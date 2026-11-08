"""Read-only compact-evidence adapter for exact certified checkpoint 11845.

No parent spectra are synthesized/replayed. The recorded independent PC2 audit
is hash-bound; live factor bytes and full audit-input files are checked by inputs.
"""
from __future__ import annotations
import math
from pathlib import Path
import numpy as np
from archive_tools import digest_file, plain_json, require
from common import PACKAGE_DIR, config, cumulative, history_prefix_equal, reserve_line


def read_parent(*, cfg=None, package=PACKAGE_DIR):
    cfg = config() if cfg is None else cfg
    identity = plain_json((package/'PARENT_IDENTITY.json').read_bytes())
    source = package/'PARENT_EVIDENCE'
    require(digest_file(source/'artifact_hashes.json') == identity['parent_artifact_manifest_sha256'], 'Original compact manifest changed')
    manifest = plain_json((source/'artifact_hashes.json').read_bytes())['files']
    actual = {f.relative_to(source).as_posix() for f in source.rglob('*') if f.is_file()}
    require(actual == set(identity['retained_evidence_files']), 'Retained evidence file set changed')
    for rel in sorted(actual):
        f=source/rel;require(not f.is_symlink(),'Parent evidence symlink')
        if rel != 'artifact_hashes.json':
            require(rel in manifest and digest_file(f)==manifest[rel], 'Changed original evidence: '+rel)
    output=source/'OUTPUT/continuation';ck=output/'checkpoint_step11845'
    m=plain_json((ck/'checkpoint_metadata.json').read_bytes())
    man=plain_json((ck/'checkpoint_manifest.json').read_bytes())
    st=plain_json((output/'run_status.json').read_bytes())
    audit=plain_json((output/'independent_audit_report.json').read_bytes())
    port=plain_json((output/'phase_port_audit.json').read_bytes())
    old=plain_json((source/'PROMOTION/CONFIG.json').read_bytes())
    summary=plain_json((output/'summary_report.json').read_bytes())
    require(st['status']=='clean_nonaccepting_stop' and st['classification']=='PREDICTIVE_WALLTIME_RESOURCE_GUARD','Unexpected parent status')
    require(st['completed_step']==st['last_persisted_step']==audit['last_persisted_step']==port['last_persisted_step']==m['completed_step']==11845,'Parent restart frontier differs')
    require(audit['passed'] is True and audit['verdict']==cfg['parent_result']['recorded_audit_verdict'],'Parent independent audit')
    require(port['passed'] is True and port['job_id']=='2969484' and port['numerical_audit_sha256']==digest_file(output/'independent_audit_report.json'),'Parent phase port audit')
    require(port['phase_audit_input_manifest_sha256']==digest_file(output/'phase_audit_inputs.json'),'Parent audit manifest linkage')
    runtime=source/'RUNTIME/continuation'
    require(port['device_gate_sha256']==digest_file(runtime/'h100_device_gate.json') and port['platform_smoke_sha256']==digest_file(runtime/'platform_bridge_report.json'),'Parent device/smoke linkage')
    require(plain_json((runtime/'return_codes.json').read_bytes())=={'device':0,'preflight':0,'smoke':0,'solver':2,'audit':0,'port_audit':0},'Parent pipeline return codes')
    require(plain_json((source/'RUNTIME/submission_continuation_receipt.json').read_bytes())['job_id']=='2969484','Wrong parent job')
    require(summary['configuration']==old and summary['latest_checkpoint']['metadata']==m and summary['latest_checkpoint']['payload_hashes']==man['files'],'Parent summary identity')
    require(summary['latest_checkpoint']['manifest_sha256']==digest_file(ck/'checkpoint_manifest.json'),'Terminal manifest identity')
    require(m['source_sha256']==cfg['parent_result']['driver_sha256']==identity['parent_driver_sha256'],'Parent driver identity')
    require(m['reserve_policy']==cfg['policy']==old['policy'],'Changing the prospective schedule is prohibited')
    require(m['legacy_prefix_origin']==cfg['legacy']==old['legacy'],'No ledger rebasing')
    require(cfg['physical']==old['physical'] and m['rate_lambda']==math.pi/3200. and m['physical_time']==11845*.0005,'Physical model/time changed')
    require(m['reserve_policy_adopted_through_call']==23690 and m['reserve_policy_adopted_beyond_completed_call'] is False,'Policy-call identity')
    require(all(m[k] is False for k in ('trace_restoration_applied','future_borrowing','automatic_resume','production_authorized','physical_claim','task10_eligible')),'Prohibited parent claim')
    hashes={**man['files'],'checkpoint_manifest.json':digest_file(ck/'checkpoint_manifest.json')}
    require(hashes==cfg['checkpoint_payloads']==identity['checkpoint_payload_hashes'],'Changed restart payload pins')
    for n in ('histories.npz','checkpoint_metadata.json'):
        require(digest_file(ck/n)==man['files'][n],'Checkpoint small-file hash')
    require(digest_file(output/'block_histories.npz')==man['files']['histories.npz'],'Block history differs from persisted history')
    with np.load(ck/'histories.npz',allow_pickle=False) as a:h={k:a[k].copy() for k in a.files}
    with np.load(source/'OUTPUT/candidate_pilot/block_histories.npz',allow_pickle=False) as a:ph={k:a[k].copy() for k in a.files}
    require(len(h)==27 and h['times'].shape==(11846,) and np.array_equal(h['times'],np.arange(11846)*.0005),'Native history layout')
    require(all(np.isfinite(x).all() for x in h.values()) and history_prefix_equal(ph,h),'Nonfinite or rewritten pilot prefix')
    r=list(m['forward_representation_terms']);e=list(m['forward_event_terms'])
    require(len(r)==17490 and len(e)==8745 and all(math.isfinite(x) and x>=0 for x in r+e),'Ordered ledger dimensions/values')
    pm=plain_json((source/'OUTPUT/candidate_pilot/checkpoint_step8949/checkpoint_metadata.json').read_bytes())
    require(r[:11698]==pm['forward_representation_terms'] and e[:5849]==pm['forward_event_terms'],'Pilot terms changed')
    require(cumulative(cfg['legacy']['representation_ledger'],r)==m['representation_ledger']==cfg['start']['representation_ledger'],'Representation reset/rebase')
    require(cumulative(cfg['legacy']['event_ledger'],e)==m['event_first_crossing_ledger']==cfg['start']['event_ledger'],'Event reset/rebase')
    require(cfg['start']['inherited_representation_term_count']==len(r) and cfg['start']['inherited_event_term_count']==len(e),'Inherited term counts')
    for name,field in [('representation_ledger','representation_ledger'),('event_first_crossing_ledger','event_first_crossing_ledger'),('cumulative_click','cumulative_positive_click'),('cumulative_zero_click','cumulative_zero_click'),('cumulative_overflow_bound','cumulative_overflow_bound'),('positive_survival','positive_survival'),('zero_survival','zero_survival')]:
        require(m[name]==float(h[field][-1]),'Parent endpoint differs: '+name)
    require(cfg['start']['ranks']==[m['sector_ranks'][str(k)] for k in range(5)]==h['sector_ranks'][-1].tolist(),'Starting sector ranks')
    require(cfg['start']['step']==11845 and cfg['start']['time']==5.9225 and cfg['gate']['end_step']==12000,'Recovery horizon')
    require(reserve_line(23690,cfg)==m['reserve_line_after_completed_call'],'Historical ceiling changed')
    # Every future ceiling is evaluated at its original global call. Never restart the ramp.
    require(all(reserve_line(j,cfg)==reserve_line(j,old) for j in range(23691,24001)),'Future credit was changed')
    expected_start={'step':11845,'time':m['physical_time'],'ranks':[m['sector_ranks'][str(k)] for k in range(5)],
        'representation_ledger':m['representation_ledger'],'event_ledger':m['event_first_crossing_ledger'],
        'overflow':m['cumulative_overflow_bound'],'previous_overflow_intensity':m['previous_overflow_intensity'],
        'positive_click_sum':m['cumulative_click'],'zero_click_sum':m['cumulative_zero_click'],
        'positive_survival_history':float(h['positive_survival'][-1]),'positive_survival_metadata':m['positive_survival'],
        'zero_survival_history':float(h['zero_survival'][-1]),'zero_survival_metadata':m['zero_survival'],
        'inherited_representation_term_count':len(r),'inherited_event_term_count':len(e),
        'inherited_internal_memory_peak_mib':max(old['start']['inherited_internal_memory_peak_mib'],audit['endpoint_metrics']['maximum_internal_memory_mib_this_job'])}
    require(cfg['start']==expected_start,'Restart adapter is not the exact certified endpoint')
    bridge=plain_json((output/'inherited_implementation_bridge.json').read_bytes())
    require(digest_file(output/'inherited_implementation_bridge.json')==cfg['parent_result']['implementation_bridge_sha256'],'Bridge provenance')
    return dict(metadata=m,manifest=man,histories=h,bridge=bridge,
        inherited_representation_terms=r,inherited_event_terms=e,
        identity_checks={'passed':True,'source_job':'2969484','exact_restart_step':11845,'no_rebase':True,
          'recorded_independent_audit_passed':True,'recorded_stop_reason':st['classification'],
          'parent_full_spectra_reaudited_locally':False,'parent_heavy_factors_available_locally':False,
          'retained_evidence_members_verified':len(actual)-1,'ordered_representation_terms':len(r),
          'ordered_event_terms':len(e),'remaining_original_policy_calls_verified':310})
