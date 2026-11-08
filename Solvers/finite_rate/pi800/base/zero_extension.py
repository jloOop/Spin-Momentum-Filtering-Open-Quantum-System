"""Read-only verification reference, continued from the corrected saved zero at7200.
This does not create positive initial data, alter inherited histories, or supply a
replacement zero state to production. Production loads its own checkpoint zero.
"""
from __future__ import annotations
import argparse,json,math,os,time
from pathlib import Path
import numpy as np
from common import PACKAGE_DIR,config,load_module,write_json,save_npz
from archive_tools import require,digest_file

def verify_extension(cfg, historical=None):
    zc=cfg['zero_extension'];f=PACKAGE_DIR/zc['array_relative'];mp=PACKAGE_DIR/zc['manifest_relative']
    require(f.is_file() and mp.is_file() and not f.is_symlink() and not mp.is_symlink(),'Missing immutable zero verification extension')
    m=json.loads(mp.read_text());require(m['passed'] is True,'Failed zero extension')
    require(m['array_sha256']==digest_file(f),'Zero extension payload changed')
    require(m['script_sha256']==digest_file(PACKAGE_DIR/'zero_extension.py'),'Zero extension code changed since construction')
    require(m['reference_solver_sha256']==digest_file(PACKAGE_DIR/'reference_lu.py'),'Zero solver changed since construction')
    require(m['anchor_manifest_sha256']==cfg['continuation']['parent_checkpoint_manifest_sha256'],'Wrong zero anchor manifest')
    require(m['anchor_zero_state_sha256']==zc['zero_state_sha256'],'Wrong corrected zero factor')
    require(m['physical']==cfg['physical'] and m['zero_solver']==cfg['zero_solver'],'Wrong zero reference model/settings')
    require(m['end_step']==12000 and m['start_step']==7200,'Reference horizon mismatch')
    with np.load(f,allow_pickle=False) as data:r={k:data[k].copy() for k in data.files}
    expected={'times','zero_survival','zero_step_click','cumulative_zero_click','gmres_max_residual','zero_step_closure'}
    require(set(r)==expected,'Reference field set')
    for k,v in r.items():
        require(np.all(np.isfinite(v)),'Nonfinite zero reference')
        require(v.shape==((12000,) if k in ('zero_step_click','zero_step_closure','gmres_max_residual') else (12001,)),'Wrong zero reference shape')
    require(np.array_equal(r['times'],np.arange(12001)*cfg['physical']['dt']),'Wrong reference time grid')
    with np.load(PACKAGE_DIR/'PARENT/block_histories.npz',allow_pickle=False) as data:
        for k in ['zero_survival','zero_step_click','cumulative_zero_click','zero_step_closure']:
            require(np.array_equal(r[k][:len(data[k])],data[k]),'Reference inherited zero prefix changed: '+k)
    if historical is not None:
        require(np.max(np.abs(r['zero_survival'][:7201]-historical['zero_survival']))<=cfg['zero_solver']['benchmark_survival_tolerance'],'Historical zero benchmark lost')
        require(np.sum(np.abs(r['zero_step_click'][:7200]-historical['zero_step_click']))<=cfg['zero_solver']['benchmark_click_l1_tolerance'],'Historical zero click benchmark lost')
    require(np.max(np.abs(r['zero_survival']+r['cumulative_zero_click']-r['zero_survival'][0]))<=cfg['zero_solver']['cumulative_closure_limit'],'Reference cumulative closure')
    return r

def advance_suffix(solver, vector, arrays, start_step, end_step, progress=None):
    """Append a zero-only verification suffix; never touch any prefix entries."""
    require(0 <= start_step < end_step, 'Invalid zero continuation interval')
    total=float(arrays['cumulative_zero_click'][start_step])
    for step in range(start_step+1,end_step+1):
        vector,click,a=solver.advance_cpu(vector)
        total=math.fsum([total,click])
        arrays['zero_survival'][step]=a['zero_after']
        arrays['zero_step_click'][step-1]=click
        arrays['cumulative_zero_click'][step]=total
        arrays['zero_step_closure'][step-1]=a['zero_midpoint_closure']
        arrays['gmres_max_residual'][step-1]=a['true_relative_residual']
        if progress is not None:progress(step)
    return vector

def prepare():
    c=config();p=c['physical'];z=c['zero_extension'];out=PACKAGE_DIR/z['array_relative'];mp=PACKAGE_DIR/z['manifest_relative']
    require(os.environ.get('SLURM_JOB_ID','').isdecimal(),'Construct full-size reference inside an allocated job, not the login node')
    require(PACKAGE_DIR==Path(c['project_root'])/c['package_name'],'Use installed PC2 package')
    out.parent.mkdir(exist_ok=True)
    import fcntl
    with (out.parent/'zero_reference.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if out.exists() or mp.exists():
            verify_extension(c);print('PASS_ZERO_EXTENSION_ALREADY_VERIFIED');return
        from verify_parent import verify_parent_metadata
        verify_parent_metadata(c)
        cp=Path(c['project_root'])/c['continuation']['parent_checkpoint_relative']
        require(digest_file(cp/'zero_state.npy')==z['zero_state_sha256'],'Corrected zero factor hash changed')
        v=np.load(cp/'zero_state.npy',allow_pickle=False)
        require(v.shape==(p['dimension'],1) and v.dtype==np.complex128 and np.isfinite(v).all(),'Invalid corrected zero factor')
        engine=load_module(PACKAGE_DIR/'RUNTIME_SOURCES/PARENT_Task09_ES_G2P_prefix155_event_sectors_nonaccepting.py','pi800_zero_extension_engine')
        parent,_=engine.load_parent_authority(PACKAGE_DIR/'RUNTIME_SOURCES');backend=parent.NumericalBackend('scipy')
        pc=parent.RunConfig(execution_gate='REFERENCE_ONLY',backend='scipy',propagator_type='spinor',omega=p['omega'],n_shell=p['n_shell'],n_z=p['n_z'],l_z=p['l_z'],dt=p['dt'],**c['fresh_launch'])
        operators=parent.build_oscillator_operators(p['n_shell'],p['omega'])
        grid,hz,_=parent.build_reference_grid(p['n_z'],p['l_z'])
        initial=parent.build_initial_state(pc,operators,grid,hz) # matrix/audit construction ONLY; never propagated here
        propagator=parent.build_propagator_objects(pc,operators,backend,initial)
        from reference_lu import ZeroCayleyLU
        solver=ZeroCayleyLU(propagator,pc,operators,c['zero_solver']);start=time.perf_counter()
        with np.load(PACKAGE_DIR/'PARENT/block_histories.npz',allow_pickle=False) as h:
            r={k:np.empty(12000 if k in ('zero_step_click','zero_step_closure','gmres_max_residual') else 12001,dtype=np.float64)
               for k in ('times','zero_survival','zero_step_click','cumulative_zero_click','gmres_max_residual','zero_step_closure')}
            for k in ('zero_survival','zero_step_click','cumulative_zero_click','zero_step_closure'):r[k][:len(h[k])]=h[k]
            total=float(h['cumulative_zero_click'][-1]);anchor_survival=float(h['zero_survival'][-1])
        with np.load(PACKAGE_DIR/c['zero_lu_benchmark']['file'],allow_pickle=False) as h:r['gmres_max_residual'][:7200]=h['gmres_max_residual']
        r['times']=np.arange(12001)*p['dt']
        require(abs(hz*np.vdot(v[:,0],v[:,0]).real-anchor_survival)<=5e-12,'Corrected zero anchor trace mismatch')
        def progress(step):
            if step%500==0:print(f'ZERO_REFERENCE_ONLY step={step} no state imported into production',flush=True)
        v=advance_suffix(solver,v,r,7200,12000,progress)
        require(np.max(np.abs(r['zero_survival']+r['cumulative_zero_click']-r['zero_survival'][0]))<=c['zero_solver']['cumulative_closure_limit'],'Reference cumulative closure')
        save_npz(out,**r)
        import scipy,platform
        write_json(mp,{'passed':True,'start_step':7200,'end_step':12000,'physical':p,'zero_solver':c['zero_solver'],
          'script_sha256':digest_file(PACKAGE_DIR/'zero_extension.py'),'reference_solver_sha256':digest_file(PACKAGE_DIR/'reference_lu.py'),
          'array_sha256':digest_file(out),'anchor_manifest_sha256':c['continuation']['parent_checkpoint_manifest_sha256'],
          'anchor_zero_state_sha256':z['zero_state_sha256'],'seconds':time.perf_counter()-start,
          'numpy':np.__version__,'scipy':scipy.__version__,'python':platform.python_version(),
          'positive_state_touched':False,'reference_state_imported_into_production':False,'old_prefix_rebuilt':False,
          'scope':'Same finite direct-Cayley algorithm independently continued for verification from the pinned saved corrected zero. Not an independent discretization or a new zero-rate physical solution.'})
        verify_extension(c);print('PASS_ZERO_EXTENSION_FROM_CORRECTED_STEP7200')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','verify']);a=ap.parse_args()
    if a.action=='prepare':prepare()
    else:verify_extension(config());print('PASS_ZERO_EXTENSION_HASHES_AND_PREFIX')
if __name__=='__main__':main()
