"""Pinned job2965353 endpoint; read-only, no state migration or factor rewriting."""
from __future__ import annotations
import argparse,json,math,re
from pathlib import Path
import numpy as np
from common import config,PACKAGE_DIR
from archive_tools import require,digest_file

def verify_parent_metadata(cfg=None):
    cfg=config() if cfg is None else cfg;pins=cfg['continuation'];root=Path(cfg['project_root'])
    old=root/pins['parent_package_name'];session=root/pins['parent_session_relative'];cp=root/pins['parent_checkpoint_relative']
    require(cp.is_dir() and not cp.is_symlink(),'Missing original job2965353 step7200 checkpoint; never substitute another state')
    pairs=[(old/'CONFIG.json','parent_config_sha256'),(old/'pi800_run.py','parent_driver_sha256'),
      (session/'run_status.json','parent_status_sha256'),(session/'independent_audit.json','parent_audit_sha256'),
      (session/'summary_report.json','parent_summary_sha256'),(cp/'checkpoint_manifest.json','parent_checkpoint_manifest_sha256'),
      (cp/'checkpoint_metadata.json','parent_checkpoint_metadata_sha256'),(cp/'histories.npz','parent_checkpoint_histories_sha256')]
    for path,key in pairs:
        require(path.is_file() and not path.is_symlink() and digest_file(path)==pins[key],'Pinned parent changed/missing: '+str(path))
    original=json.loads((old/'CONFIG.json').read_text())
    for field in ('physical','fresh_launch','legacy','runtime_sources','required_runtime_versions','zero_solver'):
        require(cfg[field]==original[field],'Frozen numerical identity changed: '+field)
    require(cfg['policy']['historical_policy']==original['policy'],'Historical policy replaced')
    from prospective_policy import validate_policy
    validate_policy(cfg)
    for name,want in cfg['runtime_sources'].items():
        require(digest_file(old/'RUNTIME_SOURCES'/name)==want,'Live parent numerical source changed: '+name)
    status=json.loads((session/'run_status.json').read_text());audit=json.loads((session/'independent_audit.json').read_text())
    require(status['status']=='completed' and status['completed_step']==status['last_persisted_step']==7200,'Parent was not the completed endpoint')
    require(audit['passed'] is True and audit['latest_checkpoint_manifest_sha256']==pins['parent_checkpoint_manifest_sha256'],'Parent audit/manifest disagreement')
    mf=json.loads((cp/'checkpoint_manifest.json').read_text());meta=json.loads((cp/'checkpoint_metadata.json').read_text())
    expected={f'sector_{i}.npy' for i in range(7)}|{'zero_state.npy','histories.npz','checkpoint_metadata.json'}
    require(set(mf['files'])==expected and mf['files']==pins['parent_factor_payload_hashes'],'Endpoint payload identity')
    for name,want in mf['files'].items():
        require(re.fullmatch(r'[0-9a-f]{64}',want) is not None,'Invalid payload hash')
        require((cp/name).is_file() and not (cp/name).is_symlink(),'Missing endpoint payload '+name)
    bundled=json.loads((PACKAGE_DIR/'PARENT/checkpoint_step7200/checkpoint_metadata.json').read_text())
    require(meta==bundled,'Endpoint metadata differs from supplied native metadata')
    require(meta['scientific_identity']==pins['parent_scientific_identity'],'Old scientific identity not pinned')
    require(meta['sector_ranks']==[1,2056,261,14,5,0,0] and meta['total_rank']==2337,'Endpoint ranks')
    require(len(meta['forward_representation_terms'])==14400 and len(meta['forward_event_terms'])==7200,'Incomplete history terms')
    require(math.fsum(meta['forward_representation_terms'])==meta['representation_ledger'],'Representation ledger closure')
    require(math.fsum(meta['forward_event_terms'])==meta['event_first_crossing_ledger'],'Event ledger closure')
    require(digest_file(cp/'histories.npz')==digest_file(PACKAGE_DIR/'PARENT/block_histories.npz'),'Native histories differ')
    return {'passed':True,'parent_job_id':'2965353','step':7200,'time':3.6,'checkpoint':str(cp),
      'manifest_sha256':pins['parent_checkpoint_manifest_sha256'],'history_arrays_matched':27,
      'past_ledgers_changed':False,'zero_reference_rebuilt':False,'factor_hashes_checked_here':False,
      'scope':'Pinned old source/status, manifest and metadata, native history bytes. All eight state-factor hashes and finite traces must be checked inside allocation before propagation.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--full',action='store_true');a=ap.parse_args();c=config()
    result=verify_parent_metadata(c)
    if a.full:
        from fresh_inputs import verify_checkpoint
        _,_,audit=verify_checkpoint(Path(c['project_root'])/c['continuation']['parent_checkpoint_relative'],c,True)
        result.update(factor_hashes_checked_here=True,full_checkpoint_audit=audit)
    print(json.dumps(result,indent=2));print('PASS_PI800_PINNED_PARENT_7200')
if __name__=='__main__':main()
