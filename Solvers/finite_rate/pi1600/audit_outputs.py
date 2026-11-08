"""Independent saved-spectrum and checkpoint reconstruction; no production re-diagonalization."""
from __future__ import annotations
import argparse, math, traceback
from pathlib import Path
import numpy as np
from archive_tools import Archive, digest_file, plain_json, require
from common import BASE, PACKAGE_DIR, config, cumulative, history_prefix_equal, reserve_line, write_json, utc
from memory_components import block_trace_npy
from pool_control import PHASES

def reconstruct_spectrum(sp: dict, rr: dict, *, cfg: dict) -> dict:
    entries=[];negative=0.
    for k in range(5):
        key=f'sector_{k}_raw_eigenvalues_ascending'
        if key not in sp: continue
        raw=np.asarray(sp[key]);require(raw.ndim==1 and np.all(np.isfinite(raw)),'Invalid raw spectrum')
        require(np.all(np.diff(raw)>=0.),'Unordered raw spectrum')
        pos=np.maximum(raw,0.);negative+=float(np.sum(np.maximum(-raw,0.),dtype=np.float64))
        require(np.array_equal(pos,sp[f'sector_{k}_positive_eigenvalues_ascending']),'Raw/positive spectral mismatch')
        entries.extend((float(v),k,i) for i,v in enumerate(pos) if v>0.)
    entries.sort()
    values=np.asarray([x[0] for x in entries],dtype=np.float64)
    require(np.array_equal(values,sp['global_positive_eigenvalues_ascending']),'Saved global spectrum mismatch')
    require(np.array_equal(np.asarray([x[1] for x in entries],dtype=np.int32),sp['global_positive_eigenvalue_sectors']), 'Saved global sector order')
    require(np.array_equal(np.asarray([x[2] for x in entries],dtype=np.int32),sp['global_positive_eigenvalue_local_indices']), 'Saved local index order')
    call=rr['call_index'];line=reserve_line(call,cfg);prior=float(rr['ledger_before']);allow=line-prior
    require(allow>=0.,'Negative remaining allowance')
    minimum=rr['minimum_admissible_rank']
    require(isinstance(minimum,(int,np.integer)) and 0<=minimum<=len(values),'Invalid minimum rank')
    cut=len(values)-int(minimum)
    delta=math.fsum(float(x) for x in values[:cut])
    require(delta<=allow and (minimum==0 or math.fsum(float(x) for x in values[:cut+1])>allow),
            'Minimum-rank reconstruction failed')
    # Positivity makes the discard monotone: these adjacent inequalities prove global minimality.
    # Do not recompute every candidate sum in O(support_rank**2) during a multi-day final audit.
    ladder=np.asarray(sp['minimum_positive_trace_discard_by_target_rank'])
    require(ladder.shape==(len(values)+1,) and np.all(np.isfinite(ladder)) and np.all(np.diff(ladder)<=0.)
            and ladder[-1]==0. and ladder[0]==math.fsum(float(x) for x in values)
            and ladder[int(minimum)]==delta,'Saved ladder endpoint/selected-rank mismatch')
    if minimum>0:
        require(ladder[int(minimum)-1]==math.fsum(float(x) for x in values[:cut+1]),'Saved adjacent rank mismatch')
    require(line==rr['reserve_line'] and float(sp['ceiling'][0])==line,'Wrong prospective line')
    require(float(sp['ledger_before'][0])==prior and int(sp['call_index'][0])==call,'Spectrum ledger/index mismatch')
    require(abs(negative-rr['negative_gram_mass'])<=1e-24,'Negative Gram mass diagnostic mismatch')
    require(negative<=1e-16,'Negative Gram mass guard')
    out={'call_index':call,'minimum_rank':minimum,'negative_gram_mass':negative}
    if 'selected_rank' in rr:
        require(rr['selected_rank']==minimum,'Not minimum admissible retained rank')
        require(delta==rr['selected_discard'],'Positive production discard charge mismatch')
        kept=entries[len(entries)-minimum:]
        allocation={str(k):sum(1 for _,kk,_ in kept if kk==k) for k in range(5)}
        actual={str(k):int(v) for k,v in rr['allocation'].items()}
        require(all(actual.get(str(k),0)==allocation[str(k)] for k in range(5)), 'Sector allocation mismatch')
        require(rr['ledger_after']<=line, 'Reserve overspend')
        out['discard']=delta
    else:
        require(minimum is not None and minimum>cfg['gate']['rank_guard'],'Uncompressed stopped call is not a rank-resource stop')
    return out


def audit_checkpoint(path: Path, info: dict, h: dict, cfg: dict) -> dict:
    require(digest_file(path/'checkpoint_manifest.json')==info['manifest_sha256'],'Checkpoint manifest hash')
    manifest=plain_json((path/'checkpoint_manifest.json').read_bytes())
    require(manifest['files']==info['payload_hashes'],'Checkpoint payload manifest mismatch')
    for name, sha in manifest['files'].items():
        f=path/name;require(f.is_file() and not f.is_symlink() and digest_file(f)==sha,f'Checkpoint payload altered: {f}')
    require(set(manifest['files'])=={'histories.npz','checkpoint_metadata.json','zero_state.npy',*[f'sector_{k}.npy' for k in range(5)]},'Checkpoint payload set')
    meta=plain_json((path/'checkpoint_metadata.json').read_bytes());require(meta==info['metadata'],'Checkpoint metadata record')
    require(meta['source_sha256']==digest_file(PACKAGE_DIR/'pi1600_continue.py'),'Checkpoint driver identity')
    require(meta['parent_result_sha256']==cfg['parent_result']['sha256'] and meta['parent_checkpoint_payload_hashes']==cfg['checkpoint_payloads'],'Checkpoint immediate parent identity')
    require(meta['reserve_policy']==cfg['policy'],'Checkpoint policy changed')
    step=info['step'];require(meta['completed_step']==step and meta['rate_lambda']==cfg['physical']['rate_lambda'],'Checkpoint time/rate')
    require(meta['legacy_prefix_representation_ledger']==cfg['legacy']['representation_ledger'],'Legacy ledger reset')
    require(cumulative(cfg['legacy']['representation_ledger'],meta['forward_representation_terms'])==meta['representation_ledger'],'Checkpoint total ledger')
    require(meta['reserve_line_after_completed_call']==reserve_line(2*step,cfg),'Checkpoint reserve line')
    require(meta['reserve_policy_adopted_through_call']==2*step and meta['reserve_policy_adopted_beyond_completed_call'] is False,'Future policy adoption')
    require(meta['trace_restoration_applied'] is False and meta['future_borrowing'] is False,'Trace restoration/future borrowing')
    with np.load(path/'histories.npz',allow_pickle=False) as a:
        ch={k:np.asarray(a[k]) for k in a.files}
    require(history_prefix_equal(ch,h),'Checkpoint history not trajectory prefix')
    require(ch['times'].shape==(step+1,),'Checkpoint history endpoint')
    traces=[];factors={}
    for k in range(5):
        item=block_trace_npy(path/f'sector_{k}.npy',cfg['physical']['h_z'])
        require(item['dtype']=='complex128' and item['finite'] and
                tuple(item['shape'])==(cfg['physical']['dimension'],int(ch['sector_ranks'][-1,k])), 'Checkpoint factor shape')
        require(abs(item['trace']-float(ch['sector_traces'][-1,k]))<=5e-12,'Checkpoint sector weighted trace')
        traces.append(item['trace']);factors[str(k)]=item
    zero=block_trace_npy(path/'zero_state.npy',cfg['physical']['h_z'])
    require(zero['finite'] and zero['dtype']=='complex128' and tuple(zero['shape'])==(cfg['physical']['dimension'],1),'Checkpoint zero shape')
    require(abs(zero['trace']-float(ch['zero_survival'][-1]))<=5e-12,'Checkpoint zero weighted trace')
    require(abs(math.fsum(traces)-float(ch['positive_survival'][-1]))<=5e-12,'Checkpoint family trace')
    return {'passed':True,'step':step,'factors':factors,'zero':zero,'metadata_sha256':info['metadata_sha256']}


def load_restart_evidence(root: Path,cfg: dict) -> dict:
    # Read-only identity validation. Does not propagate or recursively audit old jobs.
    from parent_evidence import read_parent
    parent_path = PACKAGE_DIR / cfg['parent_result']['embedded_file']
    with Archive(parent_path,cfg['parent_result']['sha256'],rootless=True) as a:
        return read_parent(a,cfg)


def audit(output: Path, root: Path, cfg: dict) -> dict:
    report=plain_json((output/'block_report.json').read_bytes());status=plain_json((output/'run_status.json').read_bytes())
    require(status['status'] in ('completed','clean_nonaccepting_stop'),'Not a certifiable completed/clean-resource prefix')
    require(report['configuration']==cfg,'Output configuration mismatch')
    require(all(status[k] is False for k in ('production_authorized','physical_claim','task10_eligible','automatic_resume')),
            'Prohibited scientific/automatic-resume claim')
    start,end,completed=cfg['start']['step'],cfg['gate']['end_step'],status['completed_step']
    require(start<=completed<=end,'Completed step outside package scope')
    parent_data=load_restart_evidence(root,cfg)
    prefix=parent_data['histories']
    parentmeta=parent_data['metadata']
    inherited=list(parent_data['inherited_representation_terms']);inherited_event=list(parent_data['inherited_event_terms'])
    require(report['inherited_representation_terms']==inherited and report['inherited_event_terms']==inherited_event,
            'Inherited forward terms changed')
    inherited_bridge=plain_json((output/'source_equivalence_record.json').read_bytes())
    require(inherited_bridge==report['source_equivalence_record'] and inherited_bridge['passed'] is True and
            inherited_bridge['gpu_equivalence_replay_performed'] is False and inherited_bridge['physical_steps_replayed']==0 and
            inherited_bridge['parent_result_sha256']==cfg['parent_result']['sha256'] and
            inherited_bridge['parent_implementation_equivalence_sha256']==cfg['parent_result']['implementation_equivalence_sha256'],
            'Repeated/unpinned implementation bridge')
    require(inherited_bridge['source_identity_report']==parent_data['bridge'],
            'Inherited bridge body changed')
    inp=plain_json((output/'input_audit.json').read_bytes())
    require(inp['passed'] is True and inp['live_factors_hashed_now'] is True and inp['live_factors_traced_now'] is True and
            inp['checkpoint_payload_hashes']==cfg['checkpoint_payloads'],'Unverified starting factors')
    with np.load(output/'block_histories.npz',allow_pickle=False) as a:h={k:np.asarray(a[k]) for k in a.files}
    require(history_prefix_equal(prefix,h),'Inherited checkpoint history altered')
    require(h['times'].shape==(completed+1,) and h['positive_step_click'].shape==(completed,), 'History endpoint/shape')
    require(np.array_equal(h['times'],np.arange(completed+1)*cfg['physical']['dt']) and
            all(np.all(np.isfinite(x)) for x in h.values()),'History time grid/finiteness')
    steps=report['step_records'];require([x['step'] for x in steps]==list(range(start+1,completed+1)),'Committed step sequence')
    rr=report['rank_records'];require([x['call_index'] for x in rr]==list(range(2*start+1,2*start+len(rr)+1)),
                                    'Global compression sequence reset/gap')
    n=completed-start;require(2*n<=len(rr)<=2*n+2,'Unexpected number of attempted compression calls')
    charges=[];decisions=[];base=cfg['legacy']['representation_ledger'];ebase=cfg['legacy']['event_ledger']
    for row in rr:
        call=row['call_index'];require(row['step']==(call+1)//2 and row['half']==('first' if call%2 else 'second'),
                                      'Half-step/call mismatch')
        with np.load(output/row['spectrum_file'],allow_pickle=False) as a:sp={k:np.asarray(a[k]) for k in a.files}
        d=reconstruct_spectrum(sp,row,cfg=cfg);decisions.append(d)
        require(row['ledger_before']==cumulative(base,[*inherited,*charges]),'Callwise inherited+new ledger prior')
        if 'discard' in d:
            charges.append(d['discard'])
            require(row['ledger_after']==cumulative(base,[*inherited,*charges]),'Callwise inherited+new ledger after')
    require(report['new_representation_terms_committed']==charges[:2*n], 'Candidate charges committed or new charges omitted')
    require(report['all_forward_representation_terms_committed']==[*inherited,*charges[:2*n]],'Forward representation prefix reset/double count')
    event_terms=[float(h['event_increment'][s-1]) for s in range(start+1,completed+1)]
    require(report['new_event_terms_committed']==event_terms and
            report['all_forward_event_terms_committed']==[*inherited_event,*event_terms],'Forward event prefix reset/double count')
    closures=[];zeros=[];over=cfg['start']['overflow'];previous=cfg['start']['previous_overflow_intensity']
    with np.load(PACKAGE_DIR/cfg['zero_reference']['file'],allow_pickle=False) as a:q={k:np.asarray(a[k]) for k in a.files}
    zero_reference_end=cfg['zero_reference']['available_through_step']
    require(inp['zero_crossrun_reference_available_through_step']==zero_reference_end and
            inp['zero_crossrun_future_claimed'] is False,'Input zero-reference scope')
    for j,row in enumerate(steps):
        s=row['step'];ri=math.fsum(charges[2*j:2*j+2]);total=cumulative(base,[*inherited,*charges[:2*j+2]])
        require(float(h['representation_increment'][s-1])==ri==row['representation_increment'] and
                float(h['representation_ledger'][s])==total==row['representation_ledger'],'Step representation reconstruction')
        require(total<=reserve_line(2*s,cfg),'Reserve overspent')
        ev=cumulative(ebase,[*inherited_event,*event_terms[:j+1]])
        require(ev==float(h['event_first_crossing_ledger'][s])==row['event_ledger'],'Step event ledger')
        pc=float(h['positive_step_click'][s-1]);zc=float(h['zero_step_click'][s-1]);ei=event_terms[j]
        require(pc>=0 and zc>=0 and ei>=0 and pc==row['positive_click'] and zc==row['zero_click'],'Negative/mismatched click/event')
        c=float(h['positive_survival'][s-1]-h['positive_survival'][s]-pc-ei-ri)
        zz=float(h['zero_survival'][s-1]-h['zero_survival'][s]-zc)
        require(abs(c-row['full_step_closure'])<=5e-12 and abs(zz-row['zero_closure'])<=5e-12,'Closure record differs')
        require(abs(c)<=1.5e-8 and abs(zz)<=5e-9,'Probability closure')
        require(h['positive_survival'][s]>=0 and h['zero_survival'][s]>=0 and
                h['positive_survival'][s]-h['positive_survival'][s-1]<=2e-9 and
                h['zero_survival'][s]-h['zero_survival'][s-1]<=2e-9,'Survival/positivity')
        det=plain_json((output/f'detector_telemetry/step{s}/detector_traceblockfix1_telemetry.json').read_bytes())
        require(det['status']=='completed' and det['positive_click']==pc and det['zero_click']==zc,'Detector telemetry mismatch')
        require(abs(det['positive_midpoint_closure'])<=5e-9 and abs(det['zero_midpoint_closure'])<=5e-9,'Cayley midpoint closure')
        require(all(b['status']=='completed' and b['gmres_failure_count']==0 and b['batch_size']<=64 and
                    b['maximum_true_residual']<=1e-8 for b in det['batches']),'Detector GMRES/batch failure')
        require(row['gmres_max_residual']<=1e-8 and h['batch_sample_relative_error'][s-1]<=5e-8,'Krylov/sample gate')
        expected_crossrun=s<=zero_reference_end
        require(row['zero_crossrun_checked'] is expected_crossrun and
                row['zero_crossrun_reference_end_step']==zero_reference_end,'Zero cross-run scope record')
        if expected_crossrun:
            cross=abs(float(h['zero_survival'][s])-float(q['zero_survival'][s]))
            require(cross<=cfg['gate']['zero_crossrun_tolerance'] and
                    abs(cross-row['zero_crossrun_difference'])<=5e-12,
                    'Independent zero scalar-reference check')
        else:
            require(row['zero_crossrun_difference'] is None,
                    'Future zero cross-run value claimed beyond available reference')
        require(ev<=float(h['analytic_event_tail_bound'][s])+1e-12,'Event tail')
        intensity=cfg['physical']['rate_lambda']*(cfg['physical']['n_shell']+2.)*float(h['top_shell_population'][s])
        over=over+.5*cfg['physical']['dt']*(previous+intensity);previous=intensity
        require(over==float(h['cumulative_overflow_bound'][s])==row['overflow_bound'] and over<=1e-6,
                'Inherited trapezoid-overflow memory changed')
        require(abs(h['positive_survival'][s]+h['cumulative_positive_click'][s]+total+ev-h['positive_survival'][0])<=5e-8,
                'Accumulated probability closure')
        require(abs(h['zero_survival'][s]+h['cumulative_zero_click'][s]-h['zero_survival'][0])<=5e-8,'Zero accumulated closure')
        require(row['total_rank']==int(h['total_rank'][s]) and row['sector_ranks']==h['sector_ranks'][s].tolist(), 'Rank history')
        require(row['total_rank']<=cfg['gate']['rank_guard'] and row['maximum_internal_driver_used_mib']<=cfg['gate']['memory_guard_mib'],
                'Committed state exceeded resource guards')
        require(row['checks'] and all(v is True for v in row['checks'].values()),'Failed committed step gate')
        for col,cum in [('positive_step_click','cumulative_positive_click'),('zero_step_click','cumulative_zero_click')]:
            require(math.fsum([float(h[cum][s-1]),float(h[col][s-1])])==float(h[cum][s]),'Click accumulation changed/restarted')
        closures.append(abs(c));zeros.append(abs(zz))
    for col,cum in [('positive_step_click','cumulative_positive_click'),('zero_step_click','cumulative_zero_click')]:
        require(abs(math.fsum(float(x) for x in h[col])-float(h[cum][-1]))<=5e-11,'Full click-history telescoping')
    infos=report['checkpoint_records']
    expected=[s for s in range(start+1,completed+1) if s%cfg['gate']['checkpoint_stride']==0 or s==end]
    if status['status']=='clean_nonaccepting_stop' and completed>start and not status.get('terminal_checkpoint_deferred'):
        if completed not in expected:expected.append(completed)
    # A disk stop can occur while saving a cadence checkpoint; only prior directories exist.
    if status.get('terminal_checkpoint_deferred') and expected and expected[-1]==completed:
        if not (output/f'checkpoint_step{completed}').exists():expected.pop()
    require([x['step'] for x in infos]==expected,'Checkpoint cadence/terminal sequence')
    require(status['last_persisted_step']==(expected[-1] if expected else start),'Incorrect restart frontier')
    cps=[]
    for info in infos:
        s=info['step'];m=info['metadata'];length=s-start
        require(m['forward_representation_terms']==[*inherited,*charges[:2*length]] and
                m['forward_event_terms']==[*inherited_event,*event_terms[:length]],'Checkpoint ledger prefix changed')
        require(m['inherited_forward_representation_term_count']==len(inherited) and
                m['inherited_forward_event_term_count']==len(inherited_event),'Checkpoint inherited count')
        require(m['event_first_crossing_ledger']==cumulative(ebase,m['forward_event_terms']),'Checkpoint event reconstruction')
        require(m['previous_overflow_intensity']==cfg['physical']['rate_lambda']*(cfg['physical']['n_shell']+2.)*
                float(h['top_shell_population'][s]),'Checkpoint lost overflow-memory value')
        cps.append(audit_checkpoint(output/f'checkpoint_step{s}',info,h,cfg))
    pool=plain_json((output/'pool_flush.json').read_bytes());memory=plain_json((output/'memory_snapshots.json').read_bytes())['snapshots']
    actual=[(x['step'],x['phase']) for x in pool['flushes']]
    attempted=max(completed,int(status.get('attempted_step',completed)))
    possible=[(s,p) for s in range(start+1,attempted+1) for p in PHASES]
    require(actual==possible[:len(actual)] and len(actual)>=4*n,'Allocator-phase sequence')
    for f in pool['flushes']:
        a,b=f['before'],f['after']
        require(a in memory and b in memory and a['pool_used_bytes']==b['pool_used_bytes'] and
                b['pool_used_bytes']<=b['pool_total_bytes']<=a['pool_total_bytes'],'Allocator state invariant')
    require(report['kraus_block_summary']['maximum_actual_block_columns']<=64,'Kraus block size changed')
    require(report['telemetry_iofix2']['full_write_count']>=len(cps)+2,'Telemetry finalization/checkpoint writes missing')
    if status['status']=='completed':
        require(completed==end and status['last_persisted_step']==end and len(rr)==2*n,'Endpoint not fully persisted')
    peak=max((x['driver_used_bytes']/2**20 for x in memory),default=0.)
    return {'schema':'task09-pi1600-continuation-independent-audit-v1','passed':True,'completed_utc':utc(),
        'verdict':'PASS_'+BASE+('_INDEPENDENT_AUDIT' if status['status']=='completed' else '_CLEAN_STOP_INDEPENDENT_AUDIT'),
        'solver_status':status['status'],'reconstructed_calls':len(decisions),'reconstructed_committed_steps':n,
        'inherited_compression_terms_preserved':len(inherited),'inherited_event_terms_preserved':len(inherited_event),
        'last_persisted_step':status['last_persisted_step'],'checkpoints':cps,
        'endpoint_metrics':{'completed_step':completed,'last_persisted_step':status['last_persisted_step'],
            'physical_time':completed*cfg['physical']['dt'],'final_rank':int(h['total_rank'][-1]),
            'sector_ranks':h['sector_ranks'][-1].tolist(),'representation_ledger':float(h['representation_ledger'][-1]),
            'reserve_line':reserve_line(2*completed,cfg),'reserve_margin':reserve_line(2*completed,cfg)-float(h['representation_ledger'][-1]),
            'positive_survival_retained':float(h['positive_survival'][-1]),'zero_survival':float(h['zero_survival'][-1]),
            'positive_midpoint_click_sum':float(h['cumulative_positive_click'][-1]),
            'zero_midpoint_click_sum':float(h['cumulative_zero_click'][-1]),
            'event_first_crossing_ledger':float(h['event_first_crossing_ledger'][-1]),
            'projected_overflow_bound':float(h['cumulative_overflow_bound'][-1]),
            'maximum_new_step_closure':max(closures,default=0.),'maximum_new_zero_closure':max(zeros,default=0.),
            'maximum_internal_memory_mib_this_job':peak,'inherited_internal_memory_peak_mib':cfg['start']['inherited_internal_memory_peak_mib']},
        'legacy_prefix_not_spectrally_reconstructed':True,'physical_acceptance':False,
        'scope':'New saved-spectrum decisions, complete inherited ledger, nonoverlapping histories, live child checkpoint hashes/traces; no GPU replay.'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--project-root',type=Path,required=True);a=ap.parse_args()
    cfg=config();out=a.project_root/cfg['output_relative']
    try:result=audit(out,a.project_root,cfg);rc=0
    except Exception as e:
        result={'passed':False,'verdict':'FAIL_'+BASE+'_INDEPENDENT_AUDIT','message':str(e),'traceback':traceback.format_exc()};rc=1
    write_json(out/'independent_audit_report.json',result);print(result['verdict'],flush=True)
    if rc:print(result['traceback'],flush=True)
    return rc

if __name__=='__main__':raise SystemExit(main())
