"""Fail-closed same-parent forward-pilot comparison, never a historical replay."""
from __future__ import annotations
import argparse, hashlib, math, traceback
from pathlib import Path
import numpy as np
from archive_tools import require, plain_json, digest_file, relative_name
from common import PACKAGE_DIR, history_prefix_equal, reserve_line, utc, write_json, cumulative


def load_history(path):
    with np.load(path,allow_pickle=False) as a:return {k:np.array(a[k],copy=True) for k in a.files}


def compare_histories(a,b,scfg,ccfg,campaign,strict_resource,candidate_resource):
    start,end=campaign['source_checkpoint_step'],campaign['pilot_end_step']
    n=end-start;dt=ccfg['physical']['dt'];g=campaign['gates']
    require(n==campaign['pilot_steps'] and n>campaign['performance_tail_steps'],'Pilot length')
    require(set(a)==set(b) and all(np.all(np.isfinite(x)) for x in list(a.values())+list(b.values())),'Nonfinite/mismatched histories')
    require(a['times'].shape==b['times'].shape==(end+1,) and np.array_equal(a['times'],np.arange(end+1)*dt) and np.array_equal(a['times'],b['times']),'Pilot not complete or mismatched grid')
    # All 27 inherited arrays, including timing and historical ceiling conventions.
    for k in a:
        cut=start+1 if a[k].shape[0]==end+1 else start
        require(a[k].dtype==b[k].dtype and a[k][:cut].tobytes()==b[k][:cut].tobytes(),'Historical prefix changed: '+k)
    ds=np.abs(a['positive_survival'][start+1:]-b['positive_survival'][start+1:])
    dc=np.abs(a['cumulative_positive_click'][start+1:]-b['cumulative_positive_click'][start+1:])
    dp=np.abs(a['positive_step_click'][start:]-b['positive_step_click'][start:])
    pc_l1=math.fsum(float(x) for x in dp)
    complete_l1=math.fsum([pc_l1,float(ds[-1])])
    cr_s=np.asarray(strict_resource['step_inclusive_wall_seconds'],float)
    cr_c=np.asarray(candidate_resource['step_inclusive_wall_seconds'],float)
    require(cr_s.shape==cr_c.shape==(n,) and np.all(np.isfinite(cr_s)) and np.all(np.isfinite(cr_c)) and np.min(cr_s)>0 and np.min(cr_c)>0,'Missing/nonpositive inclusive wall-time data')
    key='step_wall_seconds'
    require(key in a and key in b,'Computation timing missing')
    tail=campaign['performance_tail_steps']
    ts=a[key][-tail:];tc=b[key][-tail:]
    require(np.min(ts)>0 and np.min(tc)>0,'Invalid step times')
    rank_s=float(np.median(a['total_rank'][-tail:]));rank_c=float(np.median(b['total_rank'][-tail:]))
    metrics={'start_step':start,'end_step':end,'pilot_steps':n,
       'maximum_survival_absolute_difference':float(np.max(ds)),
       'maximum_cumulative_click_absolute_difference':float(np.max(dc)),
       'click_probability_L1_difference':pc_l1,'complete_censored_law_L1_difference':complete_l1,
       'complete_censored_law_half_L1_difference':complete_l1/2,
       'maximum_step_click_absolute_difference':float(np.max(dp)),
       'maximum_click_density_absolute_difference':float(np.max(dp))/dt,
       'maximum_zero_survival_absolute_difference':float(np.max(np.abs(a['zero_survival'][start:]-b['zero_survival'][start:]))),
       'maximum_zero_cumulative_click_absolute_difference':float(np.max(np.abs(a['cumulative_zero_click'][start:]-b['cumulative_zero_click'][start:]))),
       'maximum_zero_step_click_absolute_difference':float(np.max(np.abs(a['zero_step_click'][start:]-b['zero_step_click'][start:]))),
       'strict_final_rank':int(a['total_rank'][-1]),'candidate_final_rank':int(b['total_rank'][-1]),
       'strict_tail_median_rank':rank_s,'candidate_tail_median_rank':rank_c,'tail_rank_ratio':rank_c/rank_s,
       'strict_tail_median_compute_seconds':float(np.median(ts)),'candidate_tail_median_compute_seconds':float(np.median(tc)),
       'tail_compute_time_ratio':float(np.median(tc)/np.median(ts)),
       'strict_tail_median_inclusive_seconds':float(np.median(cr_s[-tail:])),
       'candidate_tail_median_inclusive_seconds':float(np.median(cr_c[-tail:])),
       'tail_inclusive_time_ratio':float(np.median(cr_c[-tail:])/np.median(cr_s[-tail:])),
       'strict_new_maximum_gmres_residual':float(np.max(a['gmres_max_residual'][start:])),
       'candidate_new_maximum_gmres_residual':float(np.max(b['gmres_max_residual'][start:])),
       'strict_final_representation_ledger':float(a['representation_ledger'][-1]),
       'candidate_final_representation_ledger':float(b['representation_ledger'][-1]),
       'shared_final_cap':reserve_line(24000,scfg),
       'candidate_first_new_ceiling':reserve_line(2*start+1,ccfg),
       'strict_first_new_ceiling':reserve_line(2*start+1,scfg)}
    # Closure is computed from independent S, clicks, and *recorded* truncation/event increments.
    def closures(h):
        return h['positive_survival'][start:end]-h['positive_survival'][start+1:end+1]-h['positive_step_click'][start:end]-h['representation_increment'][start:end]-h['event_increment'][start:end]
    cs,ct=closures(a),closures(b)
    metrics.update(strict_maximum_new_step_closure=float(np.max(np.abs(cs))),candidate_maximum_new_step_closure=float(np.max(np.abs(ct))),
                   maximum_step_closure_difference=float(np.max(np.abs(cs-ct))))
    prefix_cs=a['positive_survival']+a['cumulative_positive_click']+a['representation_ledger']+a['event_first_crossing_ledger']-a['positive_survival'][0]
    prefix_ct=b['positive_survival']+b['cumulative_positive_click']+b['representation_ledger']+b['event_first_crossing_ledger']-b['positive_survival'][0]
    metrics['maximum_prefix_closure_difference']=float(np.max(np.abs(prefix_cs[start:]-prefix_ct[start:])))
    # These are diagnostic sums, not new anchors or replacement canonical ledgers.
    rs=math.fsum(map(float,a['representation_increment'][start:]));rt=math.fsum(map(float,b['representation_increment'][start:]))
    es=math.fsum(map(float,a['event_increment'][start:]));et=math.fsum(map(float,b['event_increment'][start:]))
    ledger_scale=math.fsum([rs,rt,es,et])
    operational_allowance=math.fsum([ledger_scale,math.fsum(map(float,np.abs(cs))),math.fsum(map(float,np.abs(ct))),g['operational_comparison_roundoff_allowance']])
    metrics.update(strict_new_representation_charge_sum=rs,candidate_new_representation_charge_sum=rt,
                   strict_new_event_charge_sum=es,candidate_new_event_charge_sum=et,
                   comparison_ledger_scale=ledger_scale,operational_ledger_comparison_allowance=operational_allowance)
    checks={
      'survival':metrics['maximum_survival_absolute_difference']<=g['maximum_survival_absolute_difference'],
      'cumulative_clicks':metrics['maximum_cumulative_click_absolute_difference']<=g['maximum_cumulative_click_absolute_difference'],
      'click_density':metrics['maximum_click_density_absolute_difference']<=g['maximum_click_density_absolute_difference'],
      'complete_law':complete_l1<=g['maximum_complete_law_L1_difference'],
      'ledger_scale_comparison':max(complete_l1,metrics['maximum_survival_absolute_difference'],metrics['maximum_cumulative_click_absolute_difference'])<=operational_allowance,
      'zero_survival':metrics['maximum_zero_survival_absolute_difference']<=g['maximum_zero_survival_absolute_difference'],
      'zero_cumulative':metrics['maximum_zero_cumulative_click_absolute_difference']<=g['maximum_zero_cumulative_click_absolute_difference'],
      'zero_clicks':metrics['maximum_zero_step_click_absolute_difference']<=g['maximum_zero_step_click_absolute_difference'],
      'step_closure':max(metrics['strict_maximum_new_step_closure'],metrics['candidate_maximum_new_step_closure'])<=g['maximum_new_step_closure'],
      'prefix_closure':metrics['maximum_prefix_closure_difference']<=g['maximum_prefix_closure_difference'],
      'gmres':max(metrics['strict_new_maximum_gmres_residual'],metrics['candidate_new_maximum_gmres_residual'])<=g['maximum_gmres_true_residual'],
      'same_final_cap':reserve_line(24000,scfg)==reserve_line(24000,ccfg),
      'rank_improvement':metrics['tail_rank_ratio']<=g['maximum_tail_rank_ratio'],
      'compute_time_improvement':metrics['tail_compute_time_ratio']<=g['maximum_tail_compute_time_ratio'],
      'inclusive_time_improvement':metrics['tail_inclusive_time_ratio']<=g['maximum_tail_inclusive_time_ratio'],
    }
    for cfg,h in [(scfg,a),(ccfg,b)]:
        require(all(float(h['representation_ledger'][s])<=reserve_line(2*s,cfg) for s in range(start+1,end+1)),'Pilot reserve overspent')
    numerical=all(v for k,v in checks.items() if k not in ('rank_improvement','compute_time_improvement','inclusive_time_improvement'))
    return {'passed':bool(all(checks.values())),'numerical_comparison_passed':bool(numerical),
            'performance_gate_passed':bool(all(checks[k] for k in ('rank_improvement','compute_time_improvement','inclusive_time_improvement'))),
            'checks':{k:bool(v) for k,v in checks.items()},'metrics':metrics}


def evaluate(root:Path,*,package=PACKAGE_DIR,check_factors=True):
    campaign=plain_json((package/'CAMPAIGN.json').read_bytes())
    cfgs=[plain_json((package/'CONFIGS'/(phase+'.json')).read_bytes()) for phase in ('strict_pilot','candidate_pilot')]
    original=load_history(package/'PARENT_EVIDENCE/OUTPUT/block_histories.npz')
    hs=[];resources=[];evidence={};checkpoints=[];job_ids=[]
    for cfg in cfgs:
        phase=cfg['phase'];out=root/cfg['output_relative'];end=campaign['pilot_end_step']
        st=plain_json((out/'run_status.json').read_bytes());au=plain_json((out/'independent_audit_report.json').read_bytes())
        port=plain_json((out/'phase_port_audit.json').read_bytes())
        require(st['status']=='completed' and st['completed_step']==st['last_persisted_step']==end,'Pilot stopped before comparison horizon: '+phase)
        require(au['passed'] is True and au['last_persisted_step']==end and au['reconstructed_committed_steps']==campaign['pilot_steps'],'Missing independent pilot audit')
        require(port['passed'] is True and port['phase']==phase and port['numerical_audit_sha256']==digest_file(out/'independent_audit_report.json'),'Missing/mismatched phase port audit')
        bm=out/'phase_audit_inputs.json'
        require(digest_file(bm)==port['phase_audit_input_manifest_sha256'],'Audit-input manifest changed')
        for rel,sha in plain_json(bm.read_bytes())['files'].items():
            f=out/relative_name(rel)
            require(f.is_file() and not f.is_symlink() and digest_file(f)==sha,'Audited phase evidence changed: '+rel)
        job_ids.append(str(port['job_id']))
        report=plain_json((out/'summary_report.json').read_bytes());require(report['configuration']==cfg,'Pilot config altered')
        h=load_history(out/'block_histories.npz');require(history_prefix_equal(original,h),'Original history modified')
        ck=out/f'checkpoint_step{end}';man=plain_json((ck/'checkpoint_manifest.json').read_bytes())
        meta=plain_json((ck/'checkpoint_metadata.json').read_bytes())
        require(digest_file(ck/'histories.npz')==digest_file(out/'block_histories.npz'),'Pilot checkpoint/history seam')
        require(meta['reserve_policy']==cfg['policy'] and meta['rate_lambda']==cfg['physical']['rate_lambda'],'Pilot checkpoint policy/rate')
        origin=plain_json((package/'PARENT_EVIDENCE/OUTPUT/checkpoint_step8849/checkpoint_metadata.json').read_bytes())
        for key,anchor in [('forward_representation_terms','representation_ledger'),('forward_event_terms','event_ledger')]:
            prior=origin[key];terms=meta[key]
            require(terms[:len(prior)]==prior,'Pilot changed ordered inherited terms')
            expected_count=len(prior)+(2 if 'representation' in key else 1)*campaign['pilot_steps']
            require(len(terms)==expected_count,'Pilot missing/duplicated ledger terms')
            target='representation_ledger' if 'representation' in key else 'event_first_crossing_ledger'
            require(cumulative(cfg['legacy'][anchor],terms)==meta[target],'Pilot ledger reset or rebase')
        require(meta['legacy_prefix_origin']==cfg['legacy'],'Pilot legacy anchor changed')
        for n,s in man['files'].items():
            f=ck/n
            if check_factors or n in ('checkpoint_metadata.json','histories.npz'):
                require(f.is_file() and not f.is_symlink() and digest_file(f)==s,'Pilot checkpoint corrupted: '+str(f))
        names=['run_status.json','independent_audit_report.json','phase_port_audit.json','summary_report.json','block_histories.npz','resource_records.json','phase_audit_inputs.json',f'checkpoint_step{end}/checkpoint_manifest.json',f'checkpoint_step{end}/checkpoint_metadata.json']
        evidence[phase]={n:digest_file(out/n) for n in names}
        # Compare the first raw spectrum, whose input is the same unmodified checkpoint.
        spath=out/f'spectra/call_{2*campaign["source_checkpoint_step"]+1}_first.npz'
        evidence[phase]['first_spectrum']=digest_file(spath)
        with np.load(spath,allow_pickle=False) as a:first={k:np.array(a[k]) for k in a.files}
        checkpoints.append({'manifest_sha256':digest_file(ck/'checkpoint_manifest.json'),'payload_hashes':man['files'],
                            'metadata':meta,'first_spectrum':first})
        hs.append(h);resources.append(plain_json((out/'resource_records.json').read_bytes()))
    require(job_ids[0]==job_ids[1] and job_ids[0].isdecimal(),'Matched pilot arms must run in the same allocation')
    first_s=checkpoints[0]['first_spectrum']['global_positive_eigenvalues_ascending']
    first_c=checkpoints[1]['first_spectrum']['global_positive_eigenvalues_ascending']
    require(first_s.shape==first_c.shape and np.allclose(first_s,first_c,rtol=1e-12,atol=1e-18),'First raw spectra differ despite identical starting factors')
    result=compare_histories(*hs,*cfgs,campaign,*resources)
    result.update(schema='task09-pi3200-forward-compression-pilot-gate-v1',source_checkpoint_step=8849,
                  pilot_end_step=campaign['pilot_end_step'],job_id=job_ids[0],evidence_hashes=evidence,
                  source_sha256=digest_file(package/'pilot_compare.py'),campaign_sha256=digest_file(package/'CAMPAIGN.json'),
                  original_checkpoint_manifest_sha256=digest_file(package/'PARENT_EVIDENCE/OUTPUT/checkpoint_step8849/checkpoint_manifest.json'),
                  historical_steps_replayed=0,heavy_pilot_factors_checked=bool(check_factors),physical_acceptance=False,
                  first_raw_spectrum_maximum_absolute_difference=float(np.max(np.abs(first_s-first_c))),
                  scope='Same-parent forward-only pilot. Operational comparison allowance is not an interval-arithmetic forward-error certificate. Actual frozen-step GMRES/sample/closure and saved-spectrum audits remain mandatory.')
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--project-root',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);a=ap.parse_args()
    require(not a.report.exists() and not a.report.is_symlink(),'Immutable pilot report exists; do not overwrite')
    try:
        result=evaluate(a.project_root);result['created_utc']=utc();rc=0 if result['passed'] else 3
    except Exception as e:
        result={'passed':False,'created_utc':utc(),'message':str(e),'traceback':traceback.format_exc(),'physical_acceptance':False};rc=1
    result['verdict']='PASS_TASK09_PI3200_FORWARD_PILOT' if rc==0 else 'STOP_TASK09_PI3200_FORWARD_PILOT_NOT_AUTHORIZED'
    write_json(a.report,result);print(result['verdict'],flush=True)
    if 'metrics' in result:
        import json;print(json.dumps(result['metrics'],indent=2,sort_keys=True))
    if rc: print(result.get('message','One or more predeclared consistency/performance gates failed.'))
    return rc

if __name__=='__main__':raise SystemExit(main())
