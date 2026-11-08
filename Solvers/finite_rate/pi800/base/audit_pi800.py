"""Independent array/accounting audit; not an error-convergence or physics certificate."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np
from scipy.stats import binom
from archive_tools import require,digest_file
from common import config,write_json,reserve_line,PACKAGE_DIR,history_prefix_equal

STEP_KEYS={'positive_step_click','zero_step_click','gmres_max_residual','batch_sample_relative_error',
 'complete_step_ledger_closure','zero_step_closure','step_wall_seconds','representation_increment','event_increment',
 'detector_number_rhs','detector_number_batches','detector_maximum_actual_batch_columns','detector_batch64_contract_passed'}
NODE_KEYS={'times','positive_survival','zero_survival','cumulative_positive_click','cumulative_zero_click',
 'representation_ledger','representation_ceiling','event_first_crossing_ledger','analytic_event_tail_bound',
 'cumulative_overflow_bound','top_shell_population','total_rank','sector_traces','sector_ranks'}

def maxabs(a):return float(np.max(np.abs(a),initial=0.))
def audit_histories(h,cfg,n=None):
    p=cfg['physical'];dt=p['dt'];n=len(h['times'])-1 if n is None else n
    require(set(h)==STEP_KEYS|NODE_KEYS,'Missing/extra history fields')
    for k,a in h.items():
        require(isinstance(a,np.ndarray) and np.all(np.isfinite(a)),f'Nonfinite history {k}')
        shape=(n+1,7) if k in ('sector_traces','sector_ranks') else ((n,) if k in STEP_KEYS else (n+1,))
        require(a.shape==shape,f'History shape {k}: {a.shape} != {shape}')
    require(np.array_equal(h['times'],np.arange(n+1)*dt),'Time-grid discontinuity')
    require(abs(h['positive_survival'][0]-1)<5e-14 and abs(h['zero_survival'][0]-1)<5e-14,'Launch normalization')
    for k in ['cumulative_positive_click','cumulative_zero_click','representation_ledger','event_first_crossing_ledger','cumulative_overflow_bound']:
        require(h[k][0]==0,f'Nonzero initial ledger: {k}')
    for k in ['positive_survival','zero_survival','positive_step_click','zero_step_click','representation_increment','event_increment','sector_traces','sector_ranks','top_shell_population']:
        require(np.min(h[k],initial=0)>=0,f'Negative {k}')
    for k in ['positive_survival','zero_survival']:
        require(np.max(np.diff(h[k]),initial=0)<=2e-9,f'Survival increase {k}')
    require(maxabs(h['sector_traces'].sum(axis=1)-h['positive_survival'])<=5e-12,'Sector trace closure')
    require(np.array_equal(h['sector_ranks'].sum(axis=1),h['total_rank']),'Sector rank closure')
    expected_lines=np.array([reserve_line(2*i,cfg) for i in range(n+1)])
    require(np.array_equal(h['representation_ceiling'],expected_lines),'Prospective reserve schedule changed')
    require(np.all(h['representation_ledger']<=expected_lines),'Compression budget exceeded')
    for k in ['representation_ledger','event_first_crossing_ledger','cumulative_overflow_bound']:
        require(np.min(np.diff(h[k]),initial=0)>=0,f'Decreasing {k}')
    # Independently reconstruct simple sums, rather than trusting saved pass flags.
    cumchecks={}
    for stepkey,nodekey in [('positive_step_click','cumulative_positive_click'),('zero_step_click','cumulative_zero_click'),
                            ('representation_increment','representation_ledger'),('event_increment','event_first_crossing_ledger')]:
        expected=np.r_[0.,np.cumsum(h[stepkey],dtype=np.float64)]
        err=maxabs(expected-h[nodekey]);cumchecks[nodekey]=err
        require(err<=5e-12,f'Cumulative reconstruction mismatch: {nodekey}')
    closure=h['positive_survival']+h['cumulative_positive_click']+h['representation_ledger']+h['event_first_crossing_ledger']-h['positive_survival'][0]
    zeroc=h['zero_survival']+h['cumulative_zero_click']-h['zero_survival'][0]
    require(maxabs(closure)<=5e-8 and maxabs(zeroc)<=5e-8,'Cumulative probability closure')
    full=h['positive_survival'][:-1]-h['positive_survival'][1:]-h['positive_step_click']-h['representation_increment']-h['event_increment']
    require(maxabs(full-h['complete_step_ledger_closure'])<=5e-12,'Saved full-step residual not reproducible')
    zero_step=h['zero_survival'][:-1]-h['zero_survival'][1:]-h['zero_step_click']
    require(maxabs(zero_step-h['zero_step_closure'])<=5e-12,'Saved zero-step closure not reproducible')
    require(maxabs(full)<=2e-8 and maxabs(h['zero_step_closure'])<=5e-9,'Step closure gate')
    require(maxabs(h['gmres_max_residual'])<=1e-8,'GMRES true residual gate')
    require(maxabs(h['batch_sample_relative_error'])<=5e-8,'Independent-column check')
    require(np.all(h['detector_batch64_contract_passed']==1),'Batch64 contract failed')
    require(np.all(h['detector_maximum_actual_batch_columns']<=64),'Batch too large')
    q=(p['rate_lambda']*dt*(p['n_shell']+1)/2)/(1+p['rate_lambda']*dt*(p['n_shell']+1)/2)
    bound=np.array([binom.sf(6,2*i,q) if i else 0. for i in range(n+1)])
    require(maxabs(bound-h['analytic_event_tail_bound'])<=5e-20,'Event bound reconstruction')
    require(np.all(h['event_first_crossing_ledger']<=bound+1e-12),'Event truncation exceeded analytic bound')
    intensity=p['rate_lambda']*(p['n_shell']+2.)*h['top_shell_population']
    ov=np.r_[0.,np.cumsum(.5*dt*(intensity[:-1]+intensity[1:]))]
    require(maxabs(ov-h['cumulative_overflow_bound'])<=5e-12,'Overflow integral mismatch')
    require(np.max(h['cumulative_overflow_bound'],initial=0)<=1e-6,'Overflow gate')
    return {'passed':True,'steps':n,'time':n*dt,'maximum_cumulative_probability_residual':maxabs(closure),
      'maximum_zero_probability_residual':maxabs(zeroc),'maximum_gmres_residual':maxabs(h['gmres_max_residual']),
      'maximum_step_residual':maxabs(full),'cumulative_reconstruction_errors':cumchecks,
      'final_representation_ledger':float(h['representation_ledger'][-1]),'final_event_ledger':float(h['event_first_crossing_ledger'][-1]),
      'final_event_bound':float(bound[-1]),'final_rank':int(h['total_rank'][-1]),'physical_claim':False}

def audit_session(out,cfg=None,check_factor=True):
    cfg=config() if cfg is None else cfg;out=Path(out)
    status=json.loads((out/'run_status.json').read_text())
    require(status['status'] in ['completed','clean_nonaccepting_stop'],'Session failed, not eligible for automatic selection')
    with np.load(out/'block_histories.npz',allow_pickle=False) as f:h={k:f[k].copy() for k in f.files}
    a=audit_histories(h,cfg,status['completed_step'])
    report=json.loads((out/'block_report.json').read_text());n=status['completed_step'];start=status['start_step']
    records=report['step_records'];require([r['step'] for r in records]==list(range(start+1,n+1)),'Session gaps')
    require(all(all(v is True for v in r['checks'].values()) for r in records),'Failed saved step check')
    # Reconstruct the original, unchanged historical tolerance instead of trusting pass flags.
    refpath=PACKAGE_DIR/cfg['zero_reference']['file']
    require(digest_file(refpath)==cfg['zero_reference']['sha256'],'Historical reference changed')
    with np.load(refpath,allow_pickle=False) as f: ref=f['zero_survival']
    stop=min(n,cfg['zero_reference']['available_through_step'])
    historical_difference=maxabs(h['zero_survival'][:stop+1]-ref[:stop+1])
    require(historical_difference<=cfg['gate']['zero_crossrun_tolerance'],'Historical zero gate failed')
    from reference_lu import benchmark_for_config
    benchmark=benchmark_for_config(cfg)
    benchmark_difference=None
    benchmark_click_l1_difference=None
    if benchmark is not None:
        benchmark_difference=maxabs(h['zero_survival']-benchmark['zero_survival'][:n+1])
        require(benchmark_difference<=cfg['zero_solver']['benchmark_survival_tolerance'],'Full-horizon direct-zero benchmark mismatch')
        benchmark_click_l1_difference=float(np.sum(np.abs(h['zero_step_click']-benchmark['zero_step_click'][:n])))
        require(benchmark_click_l1_difference<=cfg['zero_solver']['benchmark_click_l1_tolerance'],'Full-horizon direct-zero click-L1 benchmark mismatch')
    for r in records:
        step=r['step'];zr=r['zero_reference_refinement']
        require(zr['method']==cfg['zero_solver']['method'],'Wrong zero solver')
        require(zr['true_relative_residual']<=cfg['zero_solver']['true_relative_residual_limit'],'Zero LU residual gate')
        require(abs(zr['zero_midpoint_closure'])<=cfg['zero_solver']['step_closure_limit'],'Zero LU closure gate')
        require(abs(zr['zero_after']-h['zero_survival'][step])<=5e-12,'Zero LU state/history mismatch')
        require(zr['zero_click']==float(h['zero_step_click'][step-1]),'Zero LU click/history mismatch')
        if step<=stop:
            require(r['zero_crossrun_difference']==abs(float(h['zero_survival'][step])-float(ref[step])),'Saved reference difference mismatch')
    reps=report['all_forward_representation_terms_committed'];evs=report['all_forward_event_terms_committed']
    require(len(reps)==2*n and len(evs)==n,'Full ordered ledger terms missing')
    require(math.fsum(reps)==float(h['representation_ledger'][-1]),'Full ordered representation ledger')
    require(math.fsum(evs)==float(h['event_first_crossing_ledger'][-1]),'Full ordered event ledger')
    comps=json.loads((out/'compression_records.json').read_text())['records']
    bycall={r['call_index']:r for r in json.loads((out/'rank_decisions.json').read_text())['records']}
    checked=0
    for co in comps:
        call=co['call_index']
        if call>2*n:continue # failed candidate never committed
        rr=bycall[call]
        with np.load(out/rr['spectrum_file'],allow_pickle=False) as f:
            vals=[float(v) for k in f.files if k.startswith('sector_') and k.endswith('_positive_eigenvalues_ascending') for v in f[k] if v>0]
        vals.sort();r=co['rank_after'];discard=math.fsum(vals[:len(vals)-r])
        require(discard==co['spectral_positive_discard']==reps[call-1],'Spectral charge reconstruction')
        require(co['ledger_before']==math.fsum(reps[:call-1]),'Pre-compression ledger mismatch')
        allow=reserve_line(call,cfg)-co['ledger_before']
        require(discard<=allow,'Inadmissible chosen rank')
        if r>1:require(math.fsum(vals[:len(vals)-r+1])>allow,'Chosen rank not minimal')
        require(co['trace_restoration_applied'] is False,'Trace restoration detected');checked+=1
    require(checked==2*(n-start),'Missing committed compression records')
    from fresh_inputs import verify_checkpoint
    cps=report['checkpoint_records']
    require(cps and cps[-1]['step']==n,'Last committed state is not checkpointed')
    latest=Path(cps[-1]['path'])
    m,ch,ca=verify_checkpoint(latest,cfg,trace_factors=check_factor)
    require(history_prefix_equal(ch,h) and history_prefix_equal(h,ch),'Checkpoint/final history mismatch')
    origin=json.loads((out/'origin.json').read_text())
    if origin['origin']=='same_rate_verified_checkpoint':
        parent=Path(origin['checkpoint'])
        require(digest_file(parent/'checkpoint_manifest.json')==origin['origin_sha256'],'Parent manifest changed')
        with np.load(parent/'histories.npz',allow_pickle=False) as f:ph={k:f[k].copy() for k in f.files}
        require(history_prefix_equal(ph,h),'Inherited prefix changed')
    result={'passed':True,'status':status['status'],'completed_full_target':n==cfg['gate']['end_step'],
      'history':a,'historical_zero_reference_max_difference':historical_difference,
      'historical_zero_reference_tolerance':cfg['gate']['zero_crossrun_tolerance'],
      'historical_tolerance_increased':False,'zero_direct_benchmark_max_difference':benchmark_difference,
      'zero_direct_benchmark_click_l1_difference':benchmark_click_l1_difference,
      'reconstructed_rank_decisions':checked,'latest_checkpoint':str(latest),
      'latest_checkpoint_manifest_sha256':digest_file(latest/'checkpoint_manifest.json'),
      'checkpoint_audit':ca,'physical_claim':False,'task10_eligible':False,
      'scope':'Array, checkpoint, signed probability accounting and recorded positive-spectrum decisions. Not GPU replay or convergence proof.'}
    write_json(out/'independent_audit.json',result);return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,required=True);a=ap.parse_args()
    try:r=audit_session(a.output_dir);print(json.dumps(r,indent=2));print('PASS_PI800_SESSION_AUDIT');return 0
    except Exception as e:
        import traceback
        write_json(a.output_dir/'independent_audit.json',{'passed':False,'error':str(e),'traceback':traceback.format_exc()});raise
if __name__=='__main__':raise SystemExit(main())
