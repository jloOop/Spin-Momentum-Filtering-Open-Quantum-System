"""Reconstruct the standalone zero-rate law and its numerical controls. No rate division."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np
from common import PACKAGE_DIR,config,write_json
from archive_tools import require,digest_file

NODES=('times','zero_survival','cumulative_zero_click','restricted_mean_trapezoid','probability_closure',
       'top_shell_population','total_rank','representation_ledger','event_first_crossing_ledger','analytic_event_tail_bound',
       'cumulative_overflow_bound','reference_compared','reference_difference')
INTERVALS=('midpoint_times','zero_click_probability','click_density_midpoint','zero_step_closure','gmres_max_residual',
           'independent_gmres_max_residual','sample_state_relative_error','sample_click_abs_difference',
           'gmres_failure_count','independent_gmres_failure_count','step_wall_seconds')

def audit_histories(h,c,step=None):
    require(set(h)==set(NODES+INTERVALS),'Wrong zero-control history schema')
    n=len(h['zero_click_probability']) if step is None else step
    for k in NODES:require(h[k].shape==(n+1,) and np.isfinite(h[k]).all(),'Invalid node history: '+k)
    for k in INTERVALS:require(h[k].shape==(n,) and np.isfinite(h[k]).all(),'Invalid interval history: '+k)
    dt=c['physical']['dt'];g=c['gate'];S=h['zero_survival'];p=h['zero_click_probability']
    require(np.array_equal(h['times'],np.arange(n+1)*dt),'Noncontiguous time nodes')
    require(np.array_equal(h['midpoint_times'],(np.arange(n)+.5)*dt),'Wrong midpoint grid')
    require(abs(float(S[0])-1.)<5e-13,'Not the normalized original launch')
    require(np.all(S>0.) and np.all(p>=0.) and np.max(np.diff(S),initial=0.)<=g['survival_increase_tolerance'],'Invalid probability/sign')
    roof=np.r_[0.,np.cumsum(p,dtype=np.float64)]
    require(np.max(np.abs(roof-h['cumulative_zero_click']))<=5e-12,'Roof cumulative reconstruction failed')
    closure=S+roof-S[0]
    require(np.max(np.abs(closure))<=g['cumulative_closure_tolerance'],'Cumulative detector closure failed')
    require(np.max(np.abs(closure-h['probability_closure']))<=5e-12,'Saved closure mismatch')
    require(np.allclose(h['zero_step_closure'],S[:-1]-S[1:]-p,atol=5e-15,rtol=0.),'Midpoint closure reconstruction failed')
    require(np.max(np.abs(h['zero_step_closure']),initial=0.)<=g['detector_closure_tolerance'],'Step closure failed')
    require(np.array_equal(h['click_density_midpoint'],p/dt),'Click-density convention mismatch')
    mu=np.r_[0.,np.cumsum(.5*dt*(S[:-1]+S[1:]))]
    require(np.max(np.abs(mu-h['restricted_mean_trapezoid']))<=5e-12,'Restricted-mean quadrature mismatch')
    require(np.all(h['total_rank']==1),'Rank changed in a pure zero-rate control')
    for k in ['representation_ledger','event_first_crossing_ledger','analytic_event_tail_bound','cumulative_overflow_bound']:
        require(np.count_nonzero(h[k])==0,'Nonzero numerical omission: '+k)
    for k in ['gmres_max_residual','independent_gmres_max_residual']:
        require(np.max(h[k],initial=0.)<=g['true_residual_tolerance'],'GMRES residual failed: '+k)
    for k in ['gmres_failure_count','independent_gmres_failure_count']:require(np.count_nonzero(h[k])==0,'GMRES failures')
    require(np.max(h['sample_state_relative_error'],initial=0.)<=5e-8,'Independent-state crosscheck failed')
    require(np.max(h['sample_click_abs_difference'],initial=0.)<=5e-10,'Independent-click crosscheck failed')
    refpath=PACKAGE_DIR/c['zero_reference']['file'];require(digest_file(refpath)==c['zero_reference']['sha256'],'Reference hash mismatch')
    with np.load(refpath,allow_pickle=False) as f:reference=f['zero_survival']
    end=min(n,c['zero_reference']['available_through_step'])
    expected=np.arange(n+1)<=end
    require(np.array_equal(h['reference_compared'],expected),'Reference scope marker wrong')
    difference=np.abs(S[:end+1]-reference[:end+1])
    require(np.allclose(h['reference_difference'][:end+1],difference,atol=5e-15,rtol=0.),'Reference difference reconstruction failed')
    require(np.max(difference)<=g['zero_crossrun_tolerance'],'Historical zero reference mismatch')
    require(np.count_nonzero(h['reference_difference'][end+1:])==0,'Out-of-scope comparison must be marked unchecked')
    return {'passed':True,'completed_step':n,'physical_time':n*dt,'zero_survival':float(S[-1]),
        'roof_detected_fraction':float(roof[-1]),'survival_complement_diagnostic':float(1.-S[-1]),
        'restricted_mean_trapezoid':float(mu[-1]),'no_click_atom':float(S[-1]),
        'maximum_cumulative_closure':float(np.max(np.abs(closure))),
        'maximum_step_closure':float(np.max(np.abs(h['zero_step_closure']),initial=0.)),
        'maximum_true_gmres_residual':float(np.max(h['gmres_max_residual'],initial=0.)),
        'maximum_independent_gmres_residual':float(np.max(h['independent_gmres_max_residual'],initial=0.)),
        'reference_compared_through_step':end,'reference_max_survival_difference':float(np.max(difference)),
        'reference_click_curve_available':False,'compression_used':False,'bath_omission':0.,'representation_omission':0.,
        'claim_scope':'finite-grid zero-rate control; no shell/time/grid convergence or positive-rate acceptance implied'}

def audit_session(out,c=None):
    c=config() if c is None else c;out=Path(out)
    status=json.loads((out/'run_status.json').read_text())
    require(status['status'] in ['completed','clean_nonaccepting_stop'],'Session did not complete or stop cleanly')
    step=status['completed_step'];ck=out/f'checkpoint_step{step}'
    from checkpoints import verify_checkpoint
    m,h,x,ca=verify_checkpoint(ck,c)
    with np.load(out/'block_histories.npz',allow_pickle=False) as f:
        require(set(f.files)==set(h) and all(np.array_equal(f[k],h[k]) for k in h),'Session/checkpoint histories differ')
    audit=audit_histories(h,c,step)
    audit.update(latest_checkpoint=str(ck),latest_checkpoint_manifest_sha256=digest_file(ck/'checkpoint_manifest.json'),
                 start_step=status['start_step'],parent_checkpoint=status.get('parent_checkpoint'),
                 endpoint_reached=step==c['gate']['end_step'],physical_claim=False,task10_eligible=False)
    write_json(out/'independent_audit.json',audit)
    return audit

def main():
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    result=audit_session(a.output_dir);print(json.dumps(result,indent=2,sort_keys=True));print('PASS_LAMBDA0_OUTPUT_AUDIT')
if __name__=='__main__':main()
