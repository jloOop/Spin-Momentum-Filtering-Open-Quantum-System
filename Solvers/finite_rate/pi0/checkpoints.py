"""Immutable, hashed single-state checkpoints, complete histories, and node diagnostics."""
from __future__ import annotations
import json,os,shutil,tempfile
from pathlib import Path
import numpy as np
from archive_tools import require,digest_file
from common import PACKAGE_DIR,save_npz,write_json,utc
from zero_model import scientific_identity,state_diagnostics

SCHEMA='task09-lambda0-fromzero-checkpoint-v1'

def write_checkpoint(output,step,x,h,ctx,reason):
    output=Path(output);dest=output/f'checkpoint_step{step}'
    require(not dest.exists(),'Immutable checkpoint already exists')
    stage=Path(tempfile.mkdtemp(prefix='.checkpoint_',dir=output))
    try:
        a=np.asarray(ctx.backend.to_cpu(x),dtype=np.complex128)
        with (stage/'zero_state.npy').open('xb') as f:np.save(f,a,allow_pickle=False);f.flush();os.fsync(f.fileno())
        arrays={k:np.asarray(v) for k,v in h.items()};save_npz(stage/'histories.npz',**arrays)
        save_npz(stage/'state_diagnostics.npz',**state_diagnostics(ctx,x))
        c=ctx.cfg
        meta={'schema':SCHEMA,'utc':utc(),'completed_step':int(step),'physical_time':step*c['physical']['dt'],
          'rate_lambda':0.,'max_event_sector':0,'rank':1,'scientific_identity':scientific_identity(c),
          'driver_sha256':digest_file(PACKAGE_DIR/'zero_run.py'),'model_adapter_sha256':digest_file(PACKAGE_DIR/'zero_model.py'),
          'survival':float(arrays['zero_survival'][-1]),'cumulative_click':float(arrays['cumulative_zero_click'][-1]),
          'representation_ledger':0.,'event_first_crossing_ledger':0.,'trace_restoration_applied':False,'reason':reason,
          'history_node_count':step+1,'history_interval_count':step}
        write_json(stage/'checkpoint_metadata.json',meta)
        names=['zero_state.npy','histories.npz','state_diagnostics.npz','checkpoint_metadata.json']
        manifest={'schema':SCHEMA+'-manifest','files':{n:digest_file(stage/n) for n in names}}
        write_json(stage/'checkpoint_manifest.json',manifest)
        for f in stage.iterdir():
            with f.open('rb') as fd:os.fsync(fd.fileno())
        os.rename(stage,dest)
        save_npz(output/'block_histories.npz',**arrays)
        return {'step':step,'path':str(dest),'manifest_sha256':digest_file(dest/'checkpoint_manifest.json')}
    finally:
        if stage.exists():shutil.rmtree(stage)

def verify_checkpoint(path,c):
    original=Path(path);require(not original.is_symlink(),'Checkpoint may not be a symlink');path=original.resolve()
    require(path.is_dir(),'Missing checkpoint')
    m=json.loads((path/'checkpoint_manifest.json').read_text())
    expected={'zero_state.npy','histories.npz','state_diagnostics.npz','checkpoint_metadata.json'}
    require(m['schema']==SCHEMA+'-manifest' and set(m['files'])==expected,'Wrong checkpoint payload')
    for n,sha in m['files'].items():
        f=path/n;require(f.is_file() and not f.is_symlink() and digest_file(f)==sha,'Checkpoint SHA mismatch: '+n)
    meta=json.loads((path/'checkpoint_metadata.json').read_text())
    require(meta['schema']==SCHEMA and meta['scientific_identity']==scientific_identity(c),'Wrong rate/model/solver/policy checkpoint')
    require(meta['driver_sha256']==digest_file(PACKAGE_DIR/'zero_run.py') and meta['model_adapter_sha256']==digest_file(PACKAGE_DIR/'zero_model.py'),'Driver changed; explicit revalidation required')
    require(meta['rate_lambda']==0. and meta['max_event_sector']==0 and meta['rank']==1,'Not a zero control')
    require(meta['representation_ledger']==meta['event_first_crossing_ledger']==0. and meta['trace_restoration_applied'] is False,'Numerical omissions in zero control')
    step=meta['completed_step'];require(isinstance(step,int) and 0<=step<=c['gate']['end_step'],'Invalid checkpoint step')
    require(meta['physical_time']==step*c['physical']['dt'],'Checkpoint time mismatch')
    with np.load(path/'histories.npz',allow_pickle=False) as f:h={k:f[k].copy() for k in f.files}
    from audit_zero import audit_histories
    audit=audit_histories(h,c,step)
    x=np.load(path/'zero_state.npy',allow_pickle=False)
    require(x.shape==(c['physical']['dimension'],1) and x.dtype==np.complex128 and np.isfinite(x).all(),'Invalid zero state')
    S=float(c['physical']['h_z']*np.vdot(x,x).real)
    require(abs(S-meta['survival'])<=5e-12 and meta['survival']==float(h['zero_survival'][-1]),'State/history trace mismatch')
    require(meta['cumulative_click']==float(h['cumulative_zero_click'][-1]),'Metadata/click history mismatch')
    with np.load(path/'state_diagnostics.npz',allow_pickle=False) as f:
        require(abs(float(f['survival'])-S)<=5e-12,'Diagnostic trace mismatch')
        require(abs(float(f['shell_population'].sum())-S)<=5e-12,'Diagnostic shell sum mismatch')
    return meta,h,x,{'passed':True,'step':step,'manifest_sha256':digest_file(path/'checkpoint_manifest.json'),'history_audit':audit}
