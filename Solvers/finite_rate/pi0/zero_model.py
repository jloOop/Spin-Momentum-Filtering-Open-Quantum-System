"""Exact lambda=0 specialization of the frozen Task09 detector kernel.

A pure no-click state is one *subnormalized* column. The bath is identity;
there is no compression, post-step normalization, or bath-event truncation.
"""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
from common import PACKAGE_DIR,load_module
from archive_tools import require,digest_file
import spectral_components as spec

ENGINE='PARENT_Task09_ES_G2P_prefix155_event_sectors_nonaccepting.py'

def scientific_identity(c):
    keys=('physical','fresh_launch','policy','solver','runtime_sources','required_runtime_versions')
    data={k:c[k] for k in keys}
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def static_check(c,package=PACKAGE_DIR):
    identity=json.loads((package/'SOURCE_IDENTITY.json').read_text())
    for name,want in identity['byte_identical_files'].items():
        f=package/name
        require(f.is_file() and not f.is_symlink() and digest_file(f)==want,'Frozen source changed: '+name)
    require(c['physical']['rate_lambda']==0.,'This is a strictly zero-rate package')
    require(c['physical']['max_event_sector']==c['policy']['event_sectors']==0,'No nonzero event sectors at zero rate')
    require(c['policy']['compression']=='disabled' and c['policy']['trace_restoration'] is False,'Zero control must not compress or normalize')
    require(c['solver']['gmres_rtol']==1e-10 and c['solver']['gmres_restart']==30 and c['solver']['gmres_maxiter']==1000,'Solver accuracy changed')
    p=c['physical']; require(p['d_channels']==(p['n_shell']+1)*(p['n_shell']+2) and p['dimension']==p['d_channels']*p['n_z'],'Geometry mismatch')
    require(c['fresh_launch']['initial_mode']=='00','Launch preparation changed')
    return identity

class _CPUMemoryTelemetry:
    """Zero-valued GPU telemetry stub for local SciPy tests, never GPU production."""
    def used_bytes(self):return 0
    def total_bytes(self):return 0
    def free_bytes(self):return 0
    def free_all_blocks(self):pass

def build_context(c,backend_name='cupy'):
    static_check(c)
    engine=load_module(PACKAGE_DIR/'RUNTIME_SOURCES'/ENGINE,'task09_lambda0_engine')
    parent,identity=engine.load_parent_authority(PACKAGE_DIR/'RUNTIME_SOURCES')
    b=parent.NumericalBackend(backend_name);metadata=b.metadata()
    if backend_name=='cupy':
        fields={'numpy':'numpy_version','scipy':'scipy_version','cupy':'cupy_version','cuda_runtime':'cuda_runtime_version'}
        for k,v in fields.items():require(metadata.get(v)==c['required_runtime_versions'][k],'Runtime mismatch: '+v)
        require('H100' in str(metadata.get('cuda_device_name','')).upper(),'H100 required')
        require(metadata.get('total_bytes',0)>=c['hardware']['minimum_gpu_memory_mib']*2**20,'Insufficient H100 capacity')
    else:
        require(backend_name=='scipy','Unsupported backend')
        pool=_CPUMemoryTelemetry()
        b._cp=NS(cuda=NS(Device=lambda:NS(mem_info=(0,0))),get_default_memory_pool=lambda:pool,get_default_pinned_memory_pool=lambda:pool)
        metadata['gpu_memory_telemetry']='mocked zeros for real CPU numerical tests only'
    p=c['physical'];operators=parent.build_oscillator_operators(p['n_shell'],p['omega'])
    require(operators.audit['all_checks_passed'],'Oscillator audit failed')
    z,hz,_=parent.build_reference_grid(p['n_z'],p['l_z'])
    require(float(hz)==p['h_z'],'Frozen longitudinal grid changed')
    pc=parent.RunConfig(execution_gate='ES-G2P',backend=backend_name,propagator_type='spinor',environment_direction='upward',
        n_shell=p['n_shell'],n_z=p['n_z'],l_z=p['l_z'],omega=p['omega'],dt=p['dt'],
        t_final=c['gate']['end_step']*p['dt'],stop_after_steps=c['gate']['end_step'],rate_lambda=0.,
        bath_microsteps_per_half=1,gmres_rtol=c['solver']['gmres_rtol'],detector_rhs_batch_columns=64,factor_block_columns=64,
        resume_from_checkpoint=False,representation_budget=0.,planned_compression_calls=0,**c['fresh_launch'])
    require(parent.GMRES_RESTART==30 and parent.GMRES_MAXITER==1000,'Frozen GMRES iteration settings changed')
    initial=parent.build_initial_state(pc,operators,z,hz)
    prop=parent.build_propagator_objects(pc,operators,b,initial)
    require(prop.roof_sign_audit['spinor_roof_term_sign_passed'],'Spinor roof sign audit failed')
    bath=parent.build_bath_kraus(operators,'upward',0.,b)
    k=[x.toarray() for x in bath.operators_cpu]
    require(np.array_equal(k[0],np.eye(operators.d_channels,dtype=complex)),'Zero-action K0 not exactly identity')
    require(all(np.count_nonzero(x)==0 for x in k[1:]),'Nonzero zero-action jump Kraus operator')
    refpath=PACKAGE_DIR/c['zero_reference']['file']
    require(digest_file(refpath)==c['zero_reference']['sha256'],'Historical zero-reference hash changed')
    with np.load(refpath,allow_pickle=False) as f:ref={n:f[n].copy() for n in f.files}
    end=c['zero_reference']['available_through_step']
    require(end<len(ref['times']) and end<len(ref['zero_survival']),'Reference prefix too short')
    require(np.array_equal(ref['times'][:end+1],np.arange(end+1)*p['dt']),'Reference time grid mismatch')
    return NS(engine=engine,parent=parent,backend=b,metadata=metadata,operators=operators,pc=pc,prop=prop,initial=initial,
              reference=ref,hz=hz,cfg=c,parent_identity=identity,bath=bath)

def advance(ctx,x,directory):
    """Call the unchanged Batch-64 wrapper with one reference column and no positive-rate columns."""
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    b=ctx.backend
    empty=b.xp.empty((ctx.cfg['physical']['dimension'],0),dtype=b.complex128)
    y,f,p,positive_click,a=spec.run_bundled_detector_traceblockfix1(x,{0:empty},parent=ctx.parent,operators=ctx.operators,
       parent_config=ctx.pc,propagator=ctx.prop,backend=b,crosscheck=True,engine=ctx.engine,output_dir=directory)
    g=ctx.cfg['gate'];e=ctx.engine
    checks={
      'one_state_column':a['number_rhs']==1 and y.shape==x.shape,
      'batch64':a['batch64_contract_respected'] is True and a['maximum_actual_batch_columns']<=64,
      'gmres':not any(a['multi_rhs_info']) and a['maximum_multi_rhs_true_residual']<=g['true_residual_tolerance'],
      'independent_gmres':not any(a['sample_independent_info']) and a['maximum_sample_independent_true_residual']<=g['true_residual_tolerance'],
      'independent_state':a['sample_batch_vs_independent_relative_error']<=e.BATCH_SAMPLE_REL_TOL,
      'independent_click':a['sample_midpoint_probability_absolute_difference']<=e.BATCH_SAMPLE_CLICK_ABS_TOL,
      'midpoint':abs(a['zero_midpoint_closure'])<=g['detector_closure_tolerance'],
      'no_other_state':positive_click==0. and all(v.shape[1]==0 for v in f.values()),
      'finite':bool(np.isfinite(p) and np.isfinite(a['zero_after']) and np.isfinite(a['zero_before'])),
      'nonnegative':p>=0. and a['zero_after']>0.,
      'survival':a['zero_after']-a['zero_before']<=g['survival_increase_tolerance'],
    }
    require(all(checks.values()),'Zero detector-step gate failed: '+repr(checks))
    a['checks']={k:bool(v) for k,v in checks.items()}
    return y,float(p),a

def top_population(ctx,x):
    b=ctx.backend;o=ctx.operators
    ix=np.flatnonzero(np.tile(o.shell_of_mode==ctx.cfg['physical']['n_shell'],2))
    if b.name!='scipy':ix=b._cp.asarray(ix)
    shaped=x.reshape(o.d_channels,ctx.cfg['physical']['n_z'])
    return float(ctx.hz*b.abs2_sum(shaped[ix,:]))

def state_diagnostics(ctx,x):
    """All quantities are computed from the saved subnormalized state at a NODE time."""
    u=np.asarray(ctx.backend.to_cpu(x)).reshape(2,ctx.operators.m_modes,ctx.cfg['physical']['n_z'])
    hz=ctx.hz;o=ctx.operators
    mode=hz*np.sum(np.abs(u)**2,axis=(0,2));S=float(np.sum(mode));require(S>0.,'Zero survival in diagnostics')
    rho=hz*np.einsum('smz,tmz->st',u,u.conj());rho_nc=rho/S
    orbital=hz*np.einsum('smz,snz->mn',u,u.conj())
    shells=np.bincount(o.shell_of_mode,weights=mode,minlength=ctx.cfg['physical']['n_shell']+1)
    spin=np.array([np.trace(rho_nc@s).real for s in [o.sigma_x,o.sigma_y,o.sigma_z]])
    return {'mode_labels':np.asarray(o.labels,dtype=np.int64),'mode_population':mode,'shell_population':shells,
      'mode_population_nc':mode/S,'shell_population_nc':shells/S,'reduced_spin':rho,'reduced_spin_nc':rho_nc,
      'reduced_orbital':orbital,'reduced_orbital_nc':orbital/S,'spin_expectations_nc':spin,
      'reduced_spin_purity':np.asarray(np.trace(rho_nc@rho_nc).real),
      'mean_nx_nc':np.asarray(np.dot(o.nx_diag,mode)/S),'mean_ny_nc':np.asarray(np.dot(o.ny_diag,mode)/S),
      'z_grid':ctx.prop.z.copy(),'longitudinal_density':np.sum(np.abs(u)**2,axis=(0,1)),
      'roof_state_amplitudes':u[:,:,-1].copy(),'survival':np.asarray(S)}
