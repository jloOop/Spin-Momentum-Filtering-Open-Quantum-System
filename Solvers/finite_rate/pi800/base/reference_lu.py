"""Independent zero-reference only. The positive Batch-64 result is left untouched.

A and B are supplied by the frozen detector constructor. This is a change of
linear-solver accuracy, NOT of the Cayley map, grid, boundary, bath or launch.
Every correction is explicit; the unrefined bundled zero remains in the original
per-batch telemetry. No historical comparison tolerance is increased.
"""
from __future__ import annotations
import math
from pathlib import Path
import numpy as np
import scipy.sparse.linalg as sla
from archive_tools import require
from common import write_json

METHOD = 'sparse_direct_cayley_superlu_complex128'
ZERO_FIELDS = frozenset(('zero_survival','zero_step_click','cumulative_zero_click','zero_step_closure'))

class ZeroCayleyLU:
    def __init__(self, propagator, parent_config, operators, settings):
        self.a = propagator.a_cpu.tocsc(copy=True)
        self.b = propagator.b_cpu.tocsr(copy=True)
        self.hz = float(propagator.h_z)
        self.dt = float(parent_config.dt)
        self.kappa = float(parent_config.kappa)
        self.nz = int(parent_config.n_z)
        self.dc = int(operators.d_channels)
        self.settings = dict(settings)
        require(self.a.shape == self.b.shape == (self.dc*self.nz,)*2,'Zero LU matrix dimensions')
        require(self.a.dtype == self.b.dtype == np.complex128,'Zero LU precision')
        require(settings['method']==METHOD and settings['permutation']=='COLAMD','Unreviewed zero solver')
        self.lu = sla.splu(self.a, permc_spec='COLAMD')

    def advance_cpu(self, old):
        old=np.asarray(old,dtype=np.complex128).reshape(-1)
        require(old.size==self.dc*self.nz and np.all(np.isfinite(old)),'Invalid zero input')
        rhs=self.b@old
        new=self.lu.solve(rhs)
        before=old.reshape(self.dc,self.nz)
        after=new.reshape(self.dc,self.nz)
        q=.5*(before[:,-1]+after[:,-1])
        # Exactly the frozen detector's nondetecting lower-face convention.
        after[:,0]=0.
        require(np.all(np.isfinite(new)),'Nonfinite direct zero solve')
        residual=self.a@new-rhs
        rhs_norm=float(np.linalg.norm(rhs))
        absres=float(np.linalg.norm(residual))
        rel=absres/max(rhs_norm,np.finfo(float).tiny)
        sb=float(self.hz*np.sum(np.abs(old)**2,dtype=np.float64))
        sa=float(self.hz*np.sum(np.abs(new)**2,dtype=np.float64))
        click=float(self.dt*self.kappa*np.sum(np.abs(q)**2,dtype=np.float64))
        closure=float(sb-sa-click)
        require(rel<=self.settings['true_relative_residual_limit'],f'Zero LU residual {rel:.17e}')
        require(abs(closure)<=self.settings['step_closure_limit'],f'Zero LU midpoint closure {closure:.17e}')
        require(click>=0 and sa>=0,'Negative direct zero probability')
        audit={'method':METHOD,'true_relative_residual':rel,'physical_absolute_residual':math.sqrt(self.hz)*absres,
               'zero_before':sb,'zero_after':sa,'zero_click':click,'zero_midpoint_closure':closure,
               'historical_tolerance_was_increased':False,'positive_output_modified':False}
        return new[:,None],click,audit

    def advance_backend(self, old, backend):
        v,click,a=self.advance_cpu(backend.to_cpu(old))
        return backend.to_backend_array(v),click,a


def run_detector_with_refined_zero(zero_state,family,*,zero_solver,frozen,**kwargs):
    """Keep the entire positive result returned by the frozen bundled kernel.
    Recompute just the reference column with the direct finite-matrix solve.
    """
    backend=kwargs['backend'];engine=kwargs['engine'];hz=kwargs['propagator'].h_z
    raw_zero,positive,raw_click,positive_click,da=frozen(zero_state,family,**kwargs)
    exact_zero,click,ref=zero_solver.advance_backend(zero_state,backend)
    backend.synchronize()
    ref.update(raw_bundled_zero_after=float(da['zero_after']),raw_bundled_zero_click=float(raw_click),
        raw_bundled_vs_direct_physical_state_norm=float(math.sqrt(hz)*backend.norm(raw_zero-exact_zero)),
        raw_bundled_vs_direct_survival_abs=float(abs(da['zero_after']-ref['zero_after'])),
        raw_bundled_vs_direct_click_abs=float(abs(raw_click-click)))
    write_json(Path(kwargs['output_dir'])/'zero_lu_refinement.json',ref)
    # All positive outputs and their diagnostics stay exactly as returned.
    audit=dict(da)
    audit['raw_bundled_zero']={k:da[k] for k in ('zero_before','zero_after','zero_click','zero_midpoint_closure')}
    for k in ('zero_before','zero_after','zero_click','zero_midpoint_closure'):
        audit[k]=ref[k]
    audit['zero_reference_refinement']=ref
    del raw_zero
    return exact_zero,positive,click,positive_click,audit


def replace_only_zero_history(original, reference, n):
    """Explicit migration, never an unreported prefix mutation."""
    required={'times','zero_survival','zero_step_click','cumulative_zero_click','zero_step_closure'}
    require(required<=set(reference),'Incomplete independent zero replay')
    require(np.array_equal(original['times'],reference['times'][:n+1]),'Reference migration time mismatch')
    result={k:v.copy() for k,v in original.items()}
    for k in ZERO_FIELDS:
        size=n if k in ('zero_step_click','zero_step_closure') else n+1
        require(len(reference[k])>=size,'Short independent zero replay')
        result[k]=np.asarray(reference[k][:size],dtype=original[k].dtype).copy()
    unchanged=[]
    for k in original:
        if k not in ZERO_FIELDS:
            require(np.array_equal(result[k],original[k]) and result[k].dtype==original[k].dtype,
                    'Positive/protected prefix changed: '+k)
            unchanged.append(k)
    return result,sorted(unchanged)


def benchmark_for_config(cfg):
    """Pinned full-grid CPU benchmark. Reduced test geometries have no such reference."""
    import json
    from common import PACKAGE_DIR
    from archive_tools import digest_file
    original=json.loads((PACKAGE_DIR/'PROVENANCE/V1_CONFIG.json').read_text())
    if cfg['physical']!=original['physical'] or cfg['fresh_launch']!=original['fresh_launch']:
        return None
    f=PACKAGE_DIR/cfg['zero_lu_benchmark']['file']
    require(digest_file(f)==cfg['zero_lu_benchmark']['sha256'],'Zero LU benchmark SHA mismatch')
    with np.load(f,allow_pickle=False) as z: historical={k:z[k].copy() for k in z.files}
    if 'zero_extension' not in cfg: return historical
    ext=PACKAGE_DIR/cfg['zero_extension']['array_relative']
    mp=PACKAGE_DIR/cfg['zero_extension']['manifest_relative']
    if not ext.exists() and not mp.exists():return historical
    from zero_extension import verify_extension
    return verify_extension(cfg, historical=historical)
