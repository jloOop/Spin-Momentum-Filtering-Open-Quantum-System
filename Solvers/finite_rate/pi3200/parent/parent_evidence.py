"""Read-only authentication of exact job2895255/step8849 or a gated pilot child.

Recorded independent audit is authenticated, not rerun on absent parent spectra.
Large factors are checked separately on PC2 by inputs.read_inputs.
"""
from __future__ import annotations
import hashlib, io, math, zipfile
from pathlib import Path
import numpy as np
from archive_tools import require, digest_file, plain_json
from common import PACKAGE_DIR, config, cumulative, history_prefix_equal, reserve_line

def read_parent(*, cfg=None, package=PACKAGE_DIR):
    cfg = config() if cfg is None else cfg
    if cfg['phase'] == 'continuation':
        from promotion import verify_promotion
        verify_promotion(Path(cfg['project_root']), package=package, check_factors=False)
        ck = Path(cfg['project_root']) / cfg['checkpoint_relative']
        m = plain_json((ck/'checkpoint_metadata.json').read_bytes())
        man = plain_json((ck/'checkpoint_manifest.json').read_bytes())
        with np.load(ck/'histories.npz', allow_pickle=False) as a:
            h = {k: np.array(a[k], copy=True) for k in a.files}
        b = plain_json((Path(cfg['project_root'])/cfg['parent_output_relative']/'inherited_implementation_bridge.json').read_bytes())
        return dict(metadata=m, manifest=man, histories=h, bridge=b,
                    inherited_representation_terms=list(m['forward_representation_terms']),
                    inherited_event_terms=list(m['forward_event_terms']),
                    identity_checks={'passed':True, 'source':'immutable approved candidate pilot',
                                     'exact_restart_step':8949, 'no_rebase':True})
    source = package/'PARENT_EVIDENCE'
    p = cfg['parent_result']
    ident = plain_json((package/'PARENT_IDENTITY.json').read_bytes())
    require(p['job_id']=='2895255' and cfg['start']['step']==8849, 'Wrong parent or restart')
    require(p['compact_sha256']==ident['compact_sha256'] and p['sha256']==ident['full_result_sha256'], 'Parent identity pin')
    amap = plain_json((source/'artifact_hashes.json').read_bytes())['files']
    # Verify every directly retained evidence member against the original compact manifest.
    checked=0
    for f in source.rglob('*'):
        if not f.is_file(): continue
        rel=f.relative_to(source).as_posix()
        require(not f.is_symlink(), 'Evidence symlink')
        if rel=='artifact_hashes.json': continue
        require(rel in amap and digest_file(f)==amap[rel], 'Evidence member changed: '+rel)
        checked+=1
    ck=source/'OUTPUT/checkpoint_step8849'
    m=plain_json((ck/'checkpoint_metadata.json').read_bytes())
    man=plain_json((ck/'checkpoint_manifest.json').read_bytes())
    st=plain_json((source/'OUTPUT/run_status.json').read_bytes())
    au=plain_json((source/'OUTPUT/independent_audit_report.json').read_bytes())
    port=plain_json((source/'RUNTIME/pc2_port_audit.json').read_bytes())
    wr=plain_json((source/'RUNTIME/wrapper_status.json').read_bytes())
    require(st['status']=='clean_nonaccepting_stop' and st['completed_step']==st['last_persisted_step']==8849, 'Uncertified parent frontier')
    require(au['passed'] is True and au['last_persisted_step']==8849 and au['verdict']==p['recorded_audit_verdict'], 'Parent clean-stop audit')
    require(port['passed'] is True and port['last_persisted_step']==8849 and port['job_id']=='2895255', 'Parent port audit')
    require(port['numerical_audit_sha256']==digest_file(source/'OUTPUT/independent_audit_report.json'), 'Port audit linkage')
    require((wr['preflight_return_code'],wr['solver_return_code'],wr['independent_audit_return_code'])==(0,2,0), 'Parent wrapper return codes')
    require(m['source_sha256']==p['driver_sha256']==ident['parent_driver_sha256'], 'Parent source hash')
    require(m['legacy_prefix_origin']==cfg['legacy']==ident['original_legacy'], 'Legacy anchor changed')
    require(cfg['physical']==ident['original_physical'] and m['rate_lambda']==math.pi/3200., 'Rate/model changed')
    require(all(m[k] is False for k in ('trace_restoration_applied','future_borrowing','automatic_resume','production_authorized','physical_claim','task10_eligible')), 'Prohibited parent claim')
    require(m['completed_step']==8849 and m['physical_time']==8849*.0005 and m['reserve_policy_adopted_through_call']==17698, 'Parent call/time identity')
    hashes={**man['files'], 'checkpoint_manifest.json':digest_file(ck/'checkpoint_manifest.json')}
    require(hashes==cfg['checkpoint_payloads'], 'Checkpoint payload pins changed')
    for name in ('checkpoint_metadata.json','histories.npz'):
        require(digest_file(ck/name)==man['files'][name], 'Checkpoint metadata/history digest')
    require(digest_file(source/'OUTPUT/block_histories.npz')==digest_file(ck/'histories.npz'), 'Terminal history is not exact checkpoint history')
    with np.load(ck/'histories.npz',allow_pickle=False) as a:
        h={k:np.array(a[k],copy=True) for k in a.files}
    require(len(h)==27 and h['times'].shape==(8850,) and np.array_equal(h['times'],np.arange(8850)*.0005), 'Native history schema/time grid')
    require(all(np.all(np.isfinite(x)) for x in h.values()), 'Nonfinite native history')
    r,e=list(m['forward_representation_terms']),list(m['forward_event_terms'])
    require(len(r)==11498 and len(e)==5749 and all(math.isfinite(x) and x>=0 for x in r+e), 'Ordered ledger lengths/values')
    require(cumulative(cfg['legacy']['representation_ledger'],r)==m['representation_ledger']==cfg['start']['representation_ledger'], 'Representation ledger rebase/reset')
    require(cumulative(cfg['legacy']['event_ledger'],e)==m['event_first_crossing_ledger']==cfg['start']['event_ledger'], 'Event ledger reset')
    require([m['sector_ranks'][str(k)] for k in range(5)]==cfg['start']['ranks']==h['sector_ranks'][-1].tolist(), 'Starting rank changed')
    for key,field in [('representation_ledger','representation_ledger'),('event_first_crossing_ledger','event_first_crossing_ledger'),
                      ('cumulative_click','cumulative_positive_click'),('cumulative_zero_click','cumulative_zero_click'),('cumulative_overflow_bound','cumulative_overflow_bound')]:
        require(m[key]==float(h[field][-1]), 'Parent endpoint '+key)
    require(abs(m['positive_survival']-float(h['positive_survival'][-1]))<=5e-12, 'Parent trace mismatch')
    original_policy=plain_json((package/'SOURCE_PROVENANCE/PARENT_CONFIG.json').read_bytes())['policy']
    require(m['reserve_policy']==original_policy, 'Original strict policy altered')
    # Only the certified future policy changes; all old callwise values are identical.
    require(reserve_line(17698,cfg)==m['reserve_line_after_completed_call'], 'Historical reserve seam')
    b=plain_json((source/'OUTPUT/inherited_implementation_bridge.json').read_bytes())
    return dict(metadata=m,manifest=man,histories=h,bridge=b,inherited_representation_terms=r,inherited_event_terms=e,
                identity_checks={'passed':True,'exact_restart_step':8849,'source_job':'2895255','evidence_members_verified':checked,
                                 'ordered_representation_terms':len(r),'ordered_event_terms':len(e),
                                 'recorded_independent_audit_passed':True,'parent_full_spectra_reaudited_locally':False,
                                 'parent_heavy_factors_available_locally':False,'no_rebase':True})
