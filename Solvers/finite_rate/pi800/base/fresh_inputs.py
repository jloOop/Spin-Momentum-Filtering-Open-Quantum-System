"""Pinned same-rate checkpoint inputs; fresh launch is restricted to isolated smoke tests."""
from __future__ import annotations
import json, math
from dataclasses import replace
from pathlib import Path
import numpy as np
from archive_tools import require, digest_file
from common import PACKAGE_DIR, cumulative, reserve_line
from memory_components import block_trace_npy

def scientific_identity(cfg):
    import hashlib
    payload={k:cfg[k] for k in ('physical','fresh_launch','policy','runtime_sources','required_runtime_versions','zero_solver')}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def static_check(package=PACKAGE_DIR,cfg=None):
    from common import config
    cfg=config() if cfg is None else cfg
    identity=json.loads((package/'SOURCE_IDENTITY.json').read_text())
    for name,want in identity['byte_identical_files'].items():
        p=package/name;require(p.is_file() and not p.is_symlink() and digest_file(p)==want,f'Frozen source changed: {name}')
    for name,want in identity.get('additional_frozen_files',{}).items():
        require(digest_file(package/name)==want,'Additional frozen source changed: '+name)
    from diagnostic_io import verify_rank_optimization,verify_detector_optimization
    verify_rank_optimization();verify_detector_optimization()
    for name,want in cfg['runtime_sources'].items():
        require(digest_file(package/'RUNTIME_SOURCES'/name)==want,f'Runtime source changed: {name}')
    require(cfg['physical']['rate_lambda']==math.pi/800,'Not pi/800')
    require(cfg['physical']['max_event_sector']==cfg['policy']['event_sectors']==6,'Event-sector disagreement')
    require(cfg['legacy']['step']==0 and cfg['legacy']['representation_ledger']==cfg['legacy']['event_ledger']==0,'Not a from-zero ledger')
    from prospective_policy import validate_policy
    validate_policy(cfg)
    require(cfg['policy']['trace_restoration'] is False,'Trace restoration is excluded')
    require(cfg['gate']['zero_crossrun_tolerance']==cfg['zero_solver']['historical_tolerance_unchanged']==2e-9,'Historical tolerance changed')
    return identity

def initial_histories(engine,gc,state,operators,hz,backend):
    h=engine.initialize_histories(replace(gc,num_steps=0))
    engine.record_initial(h,state,config=gc,operators=operators,h_z=hz,backend=backend)
    return h

def verify_checkpoint(checkpoint,cfg,trace_factors=True):
    checkpoint=Path(checkpoint).resolve()
    require(checkpoint.is_dir() and not checkpoint.is_symlink(),'Missing checkpoint')
    mp=checkpoint/'checkpoint_manifest.json';require(mp.is_file() and not mp.is_symlink(),'Missing manifest')
    mf=json.loads(mp.read_text());expected={f'sector_{k}.npy' for k in range(7)}|{'zero_state.npy','histories.npz','checkpoint_metadata.json'}
    require(set(mf['files'])==expected,'Checkpoint required payload set mismatch')
    for name,want in mf['files'].items():
        require(Path(name).name==name,'Unsafe checkpoint name')
        p=checkpoint/name;require(p.is_file() and not p.is_symlink() and digest_file(p)==want,f'Checkpoint SHA mismatch: {name}')
    m=json.loads((checkpoint/'checkpoint_metadata.json').read_text())
    require(m['schema']=='task09-pi800-fromzero-checkpoint-v1','Not a pi/800 fresh-family checkpoint')
    # The pinned external parent's OLD identity is accepted only under the explicit
    # prospective-policy transition. Self-checkpoints must have the NEW identity.
    external=checkpoint==(Path(cfg['project_root'])/cfg['continuation']['parent_checkpoint_relative']).resolve()
    expected_identity=cfg['continuation']['parent_scientific_identity'] if external else scientific_identity(cfg)
    require(m['scientific_identity']==expected_identity,'Rate/model/policy/runtime mismatch')
    require(m['rate_lambda']==cfg['physical']['rate_lambda'] and m['max_event_sector']==6,'Wrong rate/cutoff')
    external=checkpoint==(Path(cfg['project_root'])/cfg['continuation']['parent_checkpoint_relative']).resolve()
    if external:
        pins=cfg['continuation']
        require(digest_file(mp)==pins['parent_checkpoint_manifest_sha256'],'Pinned parent manifest changed')
        require(digest_file(checkpoint/'checkpoint_metadata.json')==pins['parent_checkpoint_metadata_sha256'],'Pinned parent metadata changed')
        require(digest_file(checkpoint/'histories.npz')==pins['parent_checkpoint_histories_sha256'],'Pinned parent history changed')
        require(m['driver_sha256']==pins['parent_driver_sha256'],'Wrong external parent driver')
        require(m['completed_step']==cfg['continuation']['parent_step']==7200,'External parent is not step7200')
    else:
        require(m['driver_sha256']==digest_file(PACKAGE_DIR/'pi800_run.py'),'Different driver requires explicit revalidation')
    require(m['trace_restoration_applied'] is False,'Invalid trace policy')
    step=m['completed_step'];require(isinstance(step,int) and 0<=step<=12000,'Bad checkpoint step')
    require(m['physical_time']==step*cfg['physical']['dt'],'Bad checkpoint time')
    with np.load(checkpoint/'histories.npz',allow_pickle=False) as f:h={k:f[k].copy() for k in f.files}
    from audit_pi800 import audit_histories
    hist_audit=audit_histories(h,cfg,step)
    if step >= 7200 and cfg['physical']['dimension']==273000:
        from common import history_prefix_equal
        pin=PACKAGE_DIR/'PARENT/block_histories.npz'
        require(digest_file(pin)==cfg['continuation']['parent_checkpoint_histories_sha256'],'Bundled parent history pin')
        with np.load(pin,allow_pickle=False) as f: old={k:f[k].copy() for k in f.files}
        require(history_prefix_equal(old,h),'Any of the 27 inherited history arrays changed')
    reps=m['forward_representation_terms'];events=m['forward_event_terms']
    require(len(reps)==2*step and len(events)==step,'Incomplete ordered ledger')
    require(all(math.isfinite(x) and x>=0 for x in reps+events),'Invalid ledger charge')
    require(math.fsum(reps)==m['representation_ledger']==float(h['representation_ledger'][-1]),'Representation ledger reset')
    require(math.fsum(events)==m['event_first_crossing_ledger']==float(h['event_first_crossing_ledger'][-1]),'Event ledger reset')
    for i in range(step):
        require(math.fsum(reps[2*i:2*i+2])==float(h['representation_increment'][i]),'Step representation terms mismatch')
        require(events[i]==float(h['event_increment'][i]),'Step event mismatch')
    for key,hkey in [('cumulative_click','cumulative_positive_click'),('cumulative_zero_click','cumulative_zero_click'),('cumulative_overflow_bound','cumulative_overflow_bound')]:
        require(m[key]==float(h[hkey][-1]),f'Checkpoint metadata mismatch: {key}')
    require(m['previous_overflow_intensity']==cfg['physical']['rate_lambda']*(cfg['physical']['n_shell']+2.)*float(h['top_shell_population'][-1]),'Previous overflow intensity mismatch')
    traces=[];ranks=[]
    D=cfg['physical']['dimension'];hz=cfg['physical']['h_z']
    for k in range(7):
        p=checkpoint/f'sector_{k}.npy'
        a=np.load(p,mmap_mode='r',allow_pickle=False)
        require(a.dtype==np.complex128 and a.ndim==2 and a.shape[0]==D,'Invalid factor shape/dtype')
        rank=a.shape[1];del a;ranks.append(rank)
        require(rank==int(h['sector_ranks'][-1,k]),'Rank/history mismatch')
        if trace_factors:
            t=block_trace_npy(p,hz);require(t['finite'],'Nonfinite factor')
            require(abs(t['trace']-float(h['sector_traces'][-1,k]))<=5e-12,'Trace/history mismatch');traces.append(t['trace'])
    z=np.load(checkpoint/'zero_state.npy',mmap_mode='r',allow_pickle=False)
    require(z.dtype==np.complex128 and z.shape==(D,1),'Invalid zero factor');del z
    if trace_factors:
        za=block_trace_npy(checkpoint/'zero_state.npy',hz)
        require(za['finite'] and abs(za['trace']-float(h['zero_survival'][-1]))<=5e-12,'Zero/history mismatch')
    return m,h,{'passed':True,'step':step,'manifest_sha256':digest_file(mp),'factor_traces_checked':trace_factors,'history_audit':hist_audit}

def read_inputs(root,cfg,parent_checkpoint=None,trace_factors=True):
    ident=static_check(PACKAGE_DIR,cfg)
    ref=PACKAGE_DIR/cfg['zero_reference']['file']
    require(digest_file(ref)==cfg['zero_reference']['sha256'],'Zero reference SHA mismatch')
    with np.load(ref,allow_pickle=False) as f:zero={k:f[k].copy() for k in f.files}
    if parent_checkpoint is None:
        checkpoint=None;meta={};h={};rep=[];evt=[]
        cfg['start'].update(step=0,ranks=[1,0,0,0,0,0,0],inherited_internal_memory_peak_mib=0.)
        report={'passed':True,'origin':'fresh_original_launch','origin_sha256':scientific_identity(cfg),'no_other_rate_state_imported':True}
    else:
        checkpoint=Path(parent_checkpoint).resolve()
        external=checkpoint==(Path(root)/cfg['continuation']['parent_checkpoint_relative']).resolve()
        require(external or checkpoint.is_relative_to(Path(root)/cfg['package_name']/'work'),
                'Only the pinned job2965353/step7200 or this exact continuation branch may be resumed')
        if external:
            from verify_parent import verify_parent_metadata
            verify_parent_metadata(cfg)

        meta,h,a=verify_checkpoint(checkpoint,cfg,trace_factors)
        require(meta['completed_step']<cfg['gate']['end_step'],'Checkpoint already at/after requested endpoint')
        rep=meta['forward_representation_terms'];evt=meta['forward_event_terms']
        cfg['start'].update(step=meta['completed_step'],ranks=list(map(int,h['sector_ranks'][-1])),inherited_internal_memory_peak_mib=0.)
        report={'passed':True,'origin':'same_rate_verified_checkpoint','origin_sha256':digest_file(checkpoint/'checkpoint_manifest.json'),
            'checkpoint':str(checkpoint),'checkpoint_audit':a,'no_other_rate_state_imported':True}
    return {'runtime':PACKAGE_DIR/'RUNTIME_SOURCES','checkpoint':checkpoint,'metadata':meta,'histories':h,
            'inherited_representation_terms':rep,'inherited_event_terms':evt,'zero_reference_histories':zero,
            'report':report,'source_equivalence_record':ident}
