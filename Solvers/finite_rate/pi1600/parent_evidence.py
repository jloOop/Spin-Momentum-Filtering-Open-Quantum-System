"""Read-only adapter for an immutable, audited own-branch restart.

Initial parent: job2894739, step12000. A later parent is allowed only when
prepared by the explicit manual continuation helper. No Python from an
archived result is executed. Recorded factor checks are not live checks.
"""
from __future__ import annotations
import json
import math
import numpy as np
from archive_tools import Archive, digest_file, plain_json, require
from common import PACKAGE_DIR, cumulative, history_prefix_equal


def read_parent(archive: Archive, cfg: dict) -> dict:
    pin, s, leg = cfg['parent_result'], cfg['start'], cfg['legacy']
    start = s['step']; D = cfg['physical']['dimension']; dt = cfg['physical']['dt']
    require(archive.sha256 == pin['sha256'] and archive.root == '', 'Wrong/rooted compact parent')
    count = archive.manifest('MANIFEST.json')
    require(set(archive.json('MANIFEST.json')['files']) == set(archive.members)-{'MANIFEST.json'},
            'Unmanifested compact member')
    original_hashes = archive.json('original/artifact_hashes.json')['files']
    original_verified = 0
    for name in archive.members:
        if name.startswith('original/') and name != 'original/artifact_hashes.json':
            rel = name[len('original/'):]
            require(rel in original_hashes and archive.digest(name) == original_hashes[rel],
                    'Original artifact hash mismatch: '+name)
            original_verified += 1
    for name, sha in pin['pinned_members'].items():
        require(archive.digest(name) == sha, 'Pinned parent member changed: '+name)
    status = archive.json('original/OUTPUT/run_status.json')
    report = archive.json('original/OUTPUT/summary_report.json')
    audit = archive.json('original/OUTPUT/independent_audit_report.json')
    oldcfg = archive.json('original/PACKAGE/CONFIG.json')
    port = archive.json('original/RUNTIME/pc2_port_audit.json')
    wrapper = archive.json('original/RUNTIME/wrapper_status.json')
    ckroot = f'original/OUTPUT/checkpoint_step{start}/'
    meta = archive.json(ckroot+'checkpoint_metadata.json')
    manifest = archive.json(ckroot+'checkpoint_manifest.json')
    latest = report['latest_checkpoint']
    require(latest['metadata'] == meta, 'Summary and actual checkpoint metadata differ')
    h = archive.npz('original/OUTPUT/block_histories.npz')
    ch = archive.npz(ckroot+'histories.npz')
    require(history_prefix_equal(h,ch) and h['times'].shape == ch['times'].shape,
            'Final output and checkpoint histories differ; do not advance an unpersisted frontier')
    require(status['status'] == pin['expected_status'] and status['status'] in ('completed','clean_nonaccepting_stop')
            and status['passed'] is (status['status']=='completed') and status['verdict']==pin['solver_verdict'],
            'Parent status/verdict mismatch')
    require(status['completed_step']==status['last_persisted_step']==start and
            status['start_step']==pin['expected_start_step'] and status['target_step']==pin['expected_target_step'],
            'Wrong parent frontier')
    for key in ('status','verdict','completed_step','last_persisted_step','passed'):
        require(report[key]==status[key], 'Parent summary/status mismatch: '+key)
    require(report['configuration']==oldcfg and report['persisted_checkpoints']==pin['expected_checkpoint_count']
            and report['new_committed_steps']==pin['expected_new_committed_steps']
            and report['attempted_compression_calls']==pin['expected_attempted_compression_calls'],
            'Parent counts/configuration mismatch')
    require(audit['passed'] is True and audit['verdict']==pin['audit_verdict'] and
            audit['last_persisted_step']==start and audit['reconstructed_calls']==pin['expected_attempted_compression_calls']
            and audit['reconstructed_committed_steps']==pin['expected_new_committed_steps'], 'Parent numerical audit mismatch')
    require(port['passed'] is True and str(port['job_id'])==pin['job_id'] and port['last_persisted_step']==start
            and port['verdict']==pin['port_verdict']
            and port['numerical_audit_sha256']==archive.digest('original/OUTPUT/independent_audit_report.json'),
            'Wrong parent port audit or job')
    require(str(wrapper['job_id'])==pin['job_id'] and wrapper['preflight_return_code']==0
            and wrapper['independent_audit_return_code']==0
            and wrapper['solver_return_code']==(0 if status['status']=='completed' else 2), 'Parent wrapper failure')
    require(all(meta[k] is False and status[k] is False for k in
                ('physical_claim','production_authorized','task10_eligible','automatic_resume')), 'Parent claim flags changed')
    require(oldcfg['physical']==cfg['physical'] and oldcfg['legacy']==leg
            and oldcfg['required_runtime_versions']==cfg['required_runtime_versions'], 'Physical/runtime/legacy family changed')
    require(latest['step']==meta['completed_step']==start and meta['physical_time']==s['time']==start*dt
            and meta['rate_lambda']==cfg['physical']['rate_lambda'], 'Restart time/rate mismatch')
    require(latest['path']==cfg['project_root']+'/'+cfg['checkpoint_relative']
            and latest['integrated_trace_checks_passed'] is True, 'Checkpoint path or trace check mismatch')
    require(meta['source_sha256']==pin['driver_sha256']==archive.digest('original/PACKAGE/pi1600_continue.py'),
            'Generating driver mismatch')
    require(meta['reserve_policy']==oldcfg['policy']==pin['expected_policy']
            and meta['reserve_policy_adopted_through_call']==2*start
            and meta['reserve_policy_adopted_beyond_completed_call'] is False, 'Historical reserve policy rewritten')
    if cfg['campaign']['allocation_index'] > 1:
        require(oldcfg['policy']==cfg['policy'], 'Global post600 reserve schedule rebased across allocations')
        require(oldcfg['campaign']['root_parent_compact_sha256']==cfg['campaign']['root_parent_compact_sha256']
                and oldcfg['campaign']['allocation_index']+1==cfg['campaign']['allocation_index'], 'Manual chain ancestry mismatch')
    require(meta['trace_restoration_applied'] is False and meta['future_borrowing'] is False,
            'Trace restoration/future borrowing present')
    require(latest['payload_hashes']==manifest['files']=={k:v for k,v in cfg['checkpoint_payloads'].items()
            if k!='checkpoint_manifest.json'} and latest['manifest_sha256']==cfg['checkpoint_payloads']['checkpoint_manifest.json'],
            'Checkpoint manifest pins changed')
    require(latest['payload_bytes']==sum(cfg['checkpoint_payload_sizes'].values()), 'Recorded checkpoint total-byte mismatch')
    for name in ('checkpoint_metadata.json','checkpoint_manifest.json','histories.npz'):
        require(archive.digest(ckroot+name)==cfg['checkpoint_payloads'][name]
                and digest_file(PACKAGE_DIR/'PARENT_RESULT'/name)==cfg['checkpoint_payloads'][name], 'Checkpoint evidence bytes changed: '+name)
    require(archive.digest('original/OUTPUT/block_histories.npz')==cfg['checkpoint_payloads']['histories.npz'],
            'Final NPZ is not the original checkpoint NPZ')
    require(plain_json((PACKAGE_DIR/'PARENT_RESULT/checkpoint_metadata.json').read_bytes())==meta, 'Bundled metadata differs')
    require(plain_json((PACKAGE_DIR/'PARENT_RESULT/checkpoint_manifest.json').read_bytes())==manifest, 'Bundled manifest differs')
    require(len(h)==27 and h['times'].shape==(start+1,) and h['positive_step_click'].shape==h['zero_step_click'].shape==(start,)
            and np.array_equal(h['times'],np.arange(start+1)*dt)
            and all(a.dtype.kind in 'iufb' and np.all(np.isfinite(a)) for a in h.values()), 'Invalid native history')
    require(h['sector_ranks'][-1].tolist()==s['ranks']==[meta['sector_ranks'][str(k)] for k in range(5)]
            and meta['total_rank']==sum(s['ranks']), 'Parent rank mismatch')
    meta_values={'representation_ledger':s['representation_ledger'],'event_first_crossing_ledger':s['event_ledger'],
        'cumulative_click':s['positive_click_sum'],'cumulative_zero_click':s['zero_click_sum'],
        'positive_survival':s['positive_survival_metadata'],'zero_survival':s['zero_survival_metadata'],
        'cumulative_overflow_bound':s['overflow'],'previous_overflow_intensity':s['previous_overflow_intensity']}
    for key,value in meta_values.items(): require(meta[key]==value,'Parent metadata scalar: '+key)
    history_values={'representation_ledger':s['representation_ledger'],'event_first_crossing_ledger':s['event_ledger'],
        'cumulative_positive_click':s['positive_click_sum'],'cumulative_zero_click':s['zero_click_sum'],
        'positive_survival':s['positive_survival_history'],'zero_survival':s['zero_survival_history'],
        'cumulative_overflow_bound':s['overflow']}
    for key,value in history_values.items(): require(float(h[key][-1])==value,'Parent history scalar: '+key)
    tp=PACKAGE_DIR/'PARENT_RESULT/inherited_ordered_terms.json'
    require(digest_file(tp)==pin['inherited_terms_sha256'],'Inherited ordered-term pin')
    terms=plain_json(tp.read_bytes());reps=list(meta['forward_representation_terms']);events=list(meta['forward_event_terms'])
    require(terms['forward_representation_terms']==reps and terms['forward_event_terms']==events
            and len(reps)==s['inherited_representation_term_count']==2*(start-leg['step'])
            and len(events)==s['inherited_event_term_count']==start-leg['step'], 'Ordered ledger lengths differ')
    require(all(math.isfinite(x) and x>=0 for x in reps+events),'Invalid inherited charge')
    require(meta['legacy_prefix_origin']==leg and meta['legacy_prefix_representation_ledger']==terms['legacy_representation_ledger']==leg['representation_ledger']
            and meta['legacy_event_ledger']==terms['legacy_event_ledger']==leg['event_ledger']
            and terms['legacy_step']==leg['step']==5496, 'Original ledger anchor rebased')
    original=plain_json((PACKAGE_DIR/'PROVENANCE/original_5496_to5600_ordered_terms.json').read_bytes())
    require(reps[:208]==original['forward_representation_terms'] and events[:104]==original['forward_event_terms'], 'Original5496-5600 terms altered')
    for j,step in enumerate(range(leg['step']+1,start+1),1):
        require(cumulative(leg['representation_ledger'],reps[:2*j])==float(h['representation_ledger'][step]), 'Inherited representation trajectory')
        require(cumulative(leg['event_ledger'],events[:j])==float(h['event_first_crossing_ledger'][step]), 'Inherited event trajectory')
        require(math.fsum(reps[2*j-2:2*j])==float(h['representation_increment'][step-1])
                and events[j-1]==float(h['event_increment'][step-1]), 'Inherited per-step charges')
    finals=[x for x in audit['checkpoints'] if x['step']==start]
    require(len(finals)==1 and finals[0]['passed'] is True and finals[0]['metadata_sha256']==latest['metadata_sha256'], 'No terminal checkpoint audit')
    final=finals[0]
    for k,r in enumerate(s['ranks']):
        item=final['factors'][str(k)]
        require(item['finite'] is True and item['dtype']=='complex128' and item['shape']==[D,r]
                and abs(item['trace']-meta['sector_traces'][str(k)])<=5e-12, 'Recorded factor audit mismatch')
    require(final['zero']['finite'] is True and final['zero']['dtype']=='complex128' and final['zero']['shape']==[D,1]
            and abs(final['zero']['trace']-s['zero_survival_metadata'])<=5e-12, 'Recorded zero audit mismatch')
    bridge=archive.json('original/OUTPUT/source_equivalence_record.json')
    require(archive.digest('original/OUTPUT/source_equivalence_record.json')==pin['implementation_equivalence_sha256']
            and bridge['passed'] is True and bridge['gpu_equivalence_replay_performed'] is False, 'Source-equivalence record mismatch')
    return {'metadata':meta,'manifest':manifest,'histories':h,'report':report,'recorded_audit':audit,'bridge':bridge,
        'inherited_representation_terms':reps,'inherited_event_terms':events,
        'identity_checks':{'passed':True,'parent_result_sha256':archive.sha256,'parent_evidence_kind':pin['evidence_kind'],
            'parent_job_id':pin['job_id'],'compact_hashes_verified':count,'original_artifact_subset_hashes_verified':original_verified,
            'parent_checkpoint_step':start,'parent_solver_status':status['status'],'inherited_representation_terms':len(reps),
            'inherited_event_terms':len(events),'original5496_anchor_and_ordered_sums_preserved':True,
            'inherited_step_ledgers_reconstructed':start-leg['step'],'original_full_result_freshly_audited':False,
            'old_spectra_freshly_reconstructed':False,'large_state_hashes_and_traces':'Recorded only here; live payloads checked by read_inputs.',
            'source_equivalence_scope':'Pinned numerical primitives; no new physical GPU trajectory or cross-hardware equality claim.'}}
