"""Immutable promotion capsule: candidate pilot is continued, never replayed.

The capsule is ordinary hash-bound provenance, not a digital signature. Its gate
is recomputed from immutable pilot evidence before every continuation launch.
"""
from __future__ import annotations
import argparse, copy, json, os, shutil
from pathlib import Path
from archive_tools import require,digest_file,plain_json
from common import PACKAGE_DIR,utc,write_json


def derive_configuration(root,package=PACKAGE_DIR):
    cfg=plain_json((package/'CONFIGS/candidate_pilot.json').read_bytes());old=copy.deepcopy(cfg)
    ck=root/cfg['output_relative']/'checkpoint_step8949'
    meta=plain_json((ck/'checkpoint_metadata.json').read_bytes())
    man=plain_json((ck/'checkpoint_manifest.json').read_bytes())
    import numpy as np
    with np.load(ck/'histories.npz',allow_pickle=False) as h:
        ps=float(h['positive_survival'][-1]);zs=float(h['zero_survival'][-1])
    output=root/cfg['output_relative'];gate=root/cfg['campaign_output_relative']/'PILOT_GATE.json'
    require(meta['completed_step']==8949 and meta['reserve_policy']==cfg['policy'],'Candidate pilot checkpoint identity')
    summary=plain_json((output/'summary_report.json').read_bytes())
    cfg.update(phase='continuation',output_relative=cfg['campaign_output_relative']+'/continuation',
        checkpoint_relative=old['output_relative']+'/checkpoint_step8949',parent_output_relative=old['output_relative'],
        parent_runtime_relative='',parent_kind='approved_pilot_checkpoint',job_name='T09H8849GoV1')
    cfg['parent_result']={'job_id':'pilot:'+str(plain_json(gate.read_bytes())['job_id']),
        'name':'PILOT_GATE.json','sha256':digest_file(gate),'checkpoint_step':8949,
        'driver_sha256':digest_file(package/'half_rate_continue.py'),
        'implementation_bridge_sha256':digest_file(output/'inherited_implementation_bridge.json'),
        'audit_sha256':digest_file(output/'independent_audit_report.json'),
        'origin_job_id':'2895255','origin_checkpoint_step':8849,'origin_compact_sha256':old['parent_result']['compact_sha256']}
    cfg['checkpoint_payloads']={**man['files'],'checkpoint_manifest.json':digest_file(ck/'checkpoint_manifest.json')}
    cfg['start']={
      'step':8949,'time':8949*cfg['physical']['dt'],'ranks':[meta['sector_ranks'][str(k)] for k in range(5)],
      'representation_ledger':meta['representation_ledger'],'event_ledger':meta['event_first_crossing_ledger'],
      'inherited_representation_term_count':len(meta['forward_representation_terms']),
      'inherited_event_term_count':len(meta['forward_event_terms']),
      'inherited_internal_memory_peak_mib':max(old['start']['inherited_internal_memory_peak_mib'],summary['endpoint']['maximum_internal_driver_used_mib']),
      'overflow':meta['cumulative_overflow_bound'],'previous_overflow_intensity':meta['previous_overflow_intensity'],
      'positive_click_sum':meta['cumulative_click'],'zero_click_sum':meta['cumulative_zero_click'],
      'positive_survival_history':ps,'positive_survival_metadata':meta['positive_survival'],
      'zero_survival_history':zs,'zero_survival_metadata':meta['zero_survival']}
    cfg['gate'].update(end_step=12000,slurm_wall_seconds=518400,wall_guard_seconds=511200.,minimum_free_disk_gib=450)
    cfg['hardware'].update(max_requested_wall_seconds=518400,require_partition_max_seconds_at_least=518400)
    # Same prospective schedule, same global call numbers; no interpolation/rebase at8949.
    require(cfg['policy']==old['policy'] and cfg['legacy']==old['legacy'],'Illegal promotion rebase')
    return cfg


def verify_gate(root,package=PACKAGE_DIR,check_factors=False):
    from pilot_compare import evaluate
    base=plain_json((package/'CONFIGS/candidate_pilot.json').read_bytes())
    gate_path=root/base['campaign_output_relative']/'PILOT_GATE.json'
    require(gate_path.is_file() and not gate_path.is_symlink(),'Pilot gate missing')
    saved=plain_json(gate_path.read_bytes())
    require(saved.get('passed') is True and saved.get('verdict')=='PASS_TASK09_PI3200_FORWARD_PILOT','Pilot not passed')
    current=evaluate(root,package=package,check_factors=check_factors)
    for k in ('passed','checks','metrics','evidence_hashes','source_sha256','campaign_sha256','original_checkpoint_manifest_sha256','job_id'):
        require(current[k]==saved[k],'Pilot gate evidence changed: '+k)
    return saved


def verify_promotion(root,*,package=PACKAGE_DIR,check_factors=False):
    d=package/'PREPARED/PROMOTION'
    require(d.is_dir() and not d.is_symlink(),'No approved immutable promotion capsule')
    m=plain_json((d/'MANIFEST.json').read_bytes())
    require(set(m['files'])=={'CONFIG.json','APPROVAL.json'},'Unexpected promotion capsule contents')
    for n,s in m['files'].items():require((d/n).is_file() and not (d/n).is_symlink() and digest_file(d/n)==s,'Promotion capsule corruption')
    cfg=plain_json((d/'CONFIG.json').read_bytes());approval=plain_json((d/'APPROVAL.json').read_bytes())
    gate=verify_gate(root,package=package,check_factors=check_factors)
    expected=derive_configuration(root,package)
    require(cfg==expected,'Promoted config changed or rebound')
    require(approval['gate_sha256']==digest_file(root/cfg['campaign_output_relative']/'PILOT_GATE.json'),'Approval gate hash')
    require(approval['configuration_sha256']==digest_file(d/'CONFIG.json') and approval['source_checkpoint_step']==8849 and approval['continuation_checkpoint_step']==8949,'Approval step/config mismatch')
    return {'configuration':cfg,'approval':approval,'passed':True,'gate':gate}


def create(root,*,package=PACKAGE_DIR):
    verify_gate(root,package=package,check_factors=True)
    final=package/'PREPARED/PROMOTION';tmp=package/'PREPARED/.PROMOTION.tmp'
    require(not final.exists() and not final.is_symlink() and not tmp.exists() and not tmp.is_symlink(),'Promotion capsule already exists/collision')
    cfg=derive_configuration(root,package)
    tmp.mkdir()
    try:
        write_json(tmp/'CONFIG.json',cfg)
        write_json(tmp/'APPROVAL.json',{'schema':'task09-immutable-pilot-promotion-v1','created_utc':utc(),
            'source_checkpoint_step':8849,'continuation_checkpoint_step':8949,'target_step':12000,
            'gate_sha256':digest_file(root/cfg['campaign_output_relative']/'PILOT_GATE.json'),
            'configuration_sha256':digest_file(tmp/'CONFIG.json'),
            'physical_map_changed':False,'trace_restoration':False,'ledger_rebase':False,
            'candidate_pilot_replayed':False,'historical_steps_replayed':0,'production_authorized':False,
            'operational_continuation_authorized':True,'physical_acceptance':False,
            'note':'Operational execution permission only; inherited scientific production_authorized remains false.'})
        write_json(tmp/'MANIFEST.json',{'algorithm':'SHA-256','files':{n:digest_file(tmp/n) for n in ['CONFIG.json','APPROVAL.json']}})
        for f in tmp.iterdir():
            with f.open('rb') as h:os.fsync(h.fileno())
            f.chmod(0o444)
        os.rename(tmp,final)
        fd=os.open(final.parent,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
    except Exception:
        if tmp.exists():shutil.rmtree(tmp)
        raise
    verify_promotion(root,package=package)
    print('PASS_TASK09_IMMUTABLE_PILOT_PROMOTION_NO_JOB_SUBMITTED',flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['create','verify']);ap.add_argument('--project-root',type=Path,required=True);a=ap.parse_args()
    if a.action=='create':create(a.project_root)
    else:verify_promotion(a.project_root,check_factors=True);print('PASS_TASK09_PROMOTION_VERIFIED')
    return 0
if __name__=='__main__':raise SystemExit(main())
