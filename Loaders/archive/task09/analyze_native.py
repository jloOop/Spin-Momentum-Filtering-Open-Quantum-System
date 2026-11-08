#!/usr/bin/env python3
"""Recompute pi/1600 detector observables from untouched native arrays.
Requires numpy. No solver imports, interpolation, smoothing, renormalization or GPU.
Optional: --task07-archive supplies the already uploaded original U2-I reference.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,zipfile
from pathlib import Path
import numpy as np
from audit_result import policy_line, sha, file_sha, save_json, npz, require

def exact_csv(p,columns):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='') as f:
  w=csv.writer(f);w.writerow(columns)
  for row in zip(*columns.values()):w.writerow([str(int(v)) if isinstance(v,(int,np.integer,np.bool_)) else format(float(v),'.17g') for v in row])
 with p.open(newline='') as f:rows=list(csv.DictReader(f))
 for name,v in columns.items():require(np.array_equal(np.asarray([r[name] for r in rows],dtype=v.dtype),v),'CSV roundtrip '+name)
 return {'rows':len(rows),'columns':len(columns),'exact_numeric_roundtrip':True}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,required=True);p.add_argument('--task07-archive',type=Path);args=p.parse_args();base=args.directory
 h=npz((base/'original/OUTPUT/block_histories.npz').read_bytes());cfg=json.loads((base/'original/PACKAGE/CONFIG.json').read_text());dt=cfg['physical']['dt'];lam=cfg['physical']['rate_lambda']
 t=h['times'];mid=(t[:-1]+t[1:])/2;pp=h['positive_step_click'];pz=h['zero_step_click'];dp=pp-pz;dg=dp/dt;dc=h['cumulative_positive_click']-h['cumulative_zero_click'];ds=h['positive_survival']-h['zero_survival']
 endpoints=[]
 for T in [0.,2.8,3.6,4.924,6.,8.,8.3,9.,9.6635,10.]:
  j=int(round(T/dt));r={'T':float(t[j]),'step':j,'S_lambda':float(h['positive_survival'][j]),'S_paired_zero':float(h['zero_survival'][j]),'C_lambda_saved':float(h['cumulative_positive_click'][j]),'C_paired_zero_saved':float(h['cumulative_zero_click'][j]),'delta_C_saved':float(dc[j]),'delta_S_retained':float(ds[j]),'B_rep':float(h['representation_ledger'][j]),'B_event':float(h['event_first_crossing_ledger'][j]),'rank':int(h['total_rank'][j]),'delta_C_from_fsum_differences':math.fsum(dp[:j].tolist())}
  if j:
   r.update(delta_C_relative_percent=float(100*dc[j]/h['cumulative_zero_click'][j]),delta_g_last_bin=float(dg[j-1]),restricted_retained_survival_change_trapezoids=math.fsum((np.diff(t[:j+1])*(ds[:j]+ds[1:j+1])/2).tolist()),click_conditional_mean_lambda=math.fsum((mid[:j]*pp[:j]).tolist())/math.fsum(pp[:j].tolist()),click_conditional_mean_zero=math.fsum((mid[:j]*pz[:j]).tolist())/math.fsum(pz[:j].tolist()))
   r['click_conditional_mean_change']=r['click_conditional_mean_lambda']-r['click_conditional_mean_zero']
  endpoints.append(r)
 windows=[]
 for a,b in [(0,3.6),(3.6,6),(6,8.3),(8.3,10),(6,10),(3.6,10),(9.6635,10),(0,10)]:
  i,j=int(round(a/dt)),int(round(b/dt));v=dp[i:j]
  windows.append({'start':a,'end':b,'intervals':j-i,'C_lambda_window':math.fsum(pp[i:j].tolist()),'C_zero_window':math.fsum(pz[i:j].tolist()),'delta_C_window':math.fsum(v.tolist()),'positive_response_mass':math.fsum(v[v>0].tolist()),'negative_response_mass':math.fsum(v[v<0].tolist()),'saved_endpoint_delta_C_change':float(dc[j]-dc[i])})
 signs=[]
 for j in np.flatnonzero((dg[:-1]*dg[1:]<0)&(mid[:-1]>=1.2)):
  signs.append({'direction':'negative_to_positive' if dg[j]<0 else 'positive_to_negative','left_midpoint':float(mid[j]),'right_midpoint':float(mid[j+1]),'left_bin_average_delta_g':float(dg[j]),'right_bin_average_delta_g':float(dg[j+1])})
 def tab(name,rows):
  fields=list(dict.fromkeys(k for r in rows for k in r))
  with (base/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 tab('endpoints.csv',endpoints);tab('window_masses.csv',windows);tab('sign_changes.csv',signs)
 node={'step':np.arange(len(t),dtype=np.int64)};interval={'step':np.arange(1,len(t),dtype=np.int64),'t_left':t[:-1],'t_right':t[1:],'t_midpoint':mid}
 for name,a in h.items():
  dest=node if len(a)==len(t) else interval
  if a.ndim==1:dest[name]=a
  else:
   for k in range(a.shape[1]):dest[f'{name}_sector_{k}']=a[:,k]
 node['delta_cumulative_click']=dc;node['delta_survival_retained']=ds
 node['positive_accounted_closure']=h['positive_survival']+h['cumulative_positive_click']+h['representation_ledger']+h['event_first_crossing_ledger']-h['positive_survival'][0]
 node['zero_probability_closure']=h['zero_survival']+h['cumulative_zero_click']-h['zero_survival'][0]
 interval.update(g_lambda=pp/dt,g_paired_zero=pz/dt,delta_probability=dp,delta_g=dg,delta_g_over_lambda=dg/lam)
 csvchecks={}
 csvchecks['Nodes_0_to10.csv']=exact_csv(base/'data/Nodes_0_to10.csv',node);csvchecks['Intervals_0_to10.csv']=exact_csv(base/'data/Intervals_0_to10.csv',interval)
 node6={k:v[12000:] for k,v in node.items()};int6={k:v[12000:] for k,v in interval.items()}
 node6['active_H10_prospective_ceiling']=np.array([policy_line(2*s,cfg) for s in range(12000,20001)])
 node6['active_H10_reserve_margin']=node6['active_H10_prospective_ceiling']-node6['representation_ledger']
 csvchecks['Nodes_6_to10.csv']=exact_csv(base/'data/Nodes_6_to10.csv',node6);csvchecks['Intervals_6_to10.csv']=exact_csv(base/'data/Intervals_6_to10.csv',int6)
 segment={k:v[12000:] for k,v in h.items()};np.savez_compressed(base/'data/Segment_6_to10.npz',**segment)
 np.savez_compressed(base/'data/Plot_Data_0_to10.npz',times=t,midpoint_times=mid,g_lambda=pp/dt,g_paired_zero=pz/dt,delta_probability=dp,delta_g=dg,delta_C=dc,delta_S_retained=ds)
 metrics={'source':'original/OUTPUT/block_histories.npz','definitions':{'delta_g':'(positive_step_click-zero_step_click)/dt at native interval midpoints','delta_C':'saved cumulative_positive_click minus cumulative_zero_click; independently checked by fsum of roof increments','windows':'unconditional launch-ensemble mass, not conditioned or renormalized at window start','sign_changes':'adjacent native-bin sign changes after t=1.2; no continuous-time interpolation or significance certification','signed_record_norm':'half(sum abs(dp) + abs(delta S retained)); numerical subnormalized record, not renormalized physical probability law'},'endpoint':endpoints[-1],
 'density_minimum':{'value':float(dg.min()),'midpoint':float(mid[dg.argmin()])},'density_maximum':{'value':float(dg.max()),'midpoint':float(mid[dg.argmax()])},
 'cumulative_minimum':{'value':float(dc.min()),'node':float(t[dc.argmin()])},'last_bin':{'left':float(t[-2]),'right':float(t[-1]),'midpoint':float(mid[-1]),'g_lambda':float(pp[-1]/dt),'g_paired_zero':float(pz[-1]/dt),'delta_g':float(dg[-1]),'relative_delta_g_percent':float(100*dp[-1]/pz[-1])},
 'number_post1p2_sign_changes':len(signs),'retained_signed_record_norm':.5*(math.fsum(np.abs(dp).tolist())+abs(float(ds[-1]))),
 'full_positive_response_mass':windows[-1]['positive_response_mass'],'full_negative_response_mass':windows[-1]['negative_response_mass'],
 'net_cumulative_recovery_since_minimum':float(dc[-1]-dc.min()),'early_pre1p2_positive_mass':math.fsum(dp[:2400][dp[:2400]>0].tolist()),
 'window_rows':windows,'sign_change_rows':signs,'exact_csv_roundtrips':csvchecks,'physical_acceptance':False,'tangent':None}
 if args.task07_archive or (base/'reference/U2I_native_case.zip').exists():
  if args.task07_archive:
   with zipfile.ZipFile(args.task07_archive) as z:
    members=[x for x in z.namelist() if 'U2-I' in x and 'case_share' in x and x.endswith('.zip') and not x.startswith('__MACOSX')];require(len(members)==1,'Unique U2-I case');b=z.read(members[0])
   reference_archive=args.task07_archive.name;reference_member=members[0]
  else:
   b=(base/'reference/U2I_native_case.zip').read_bytes();reference_archive='reference/U2I_native_case.zip';reference_member='included unchanged original U2-I case ZIP'
  require(sha(b)=='3ec8ff21a633105aa713f1eb95ebe4a104b1ae4ba5801ec8a2eee8d47188b1db','Exact U2-I case pin')
  case=zipfile.ZipFile(io.BytesIO(b));pre='spinor_upward_omega100_mode00_N12_dt5e-4_T10_ins5e-2_';man=json.loads(case.read(pre+'output_hashes.json'))['files']
  for rel,expected in man.items():require(sha(case.read(rel))==expected,'Tangent file hash '+rel)
  config=json.loads(case.read(pre+'configuration.json'))
  require(config['omega']==100 and config['N_shell']==12 and config['N_z']==1500 and config['dt']==dt and config['initial_mode']=='00' and config['environment_direction']=='upward','Tangent physical configuration')
  load=lambda suffix:np.load(io.BytesIO(case.read(pre+suffix)),allow_pickle=False)
  tt=load('times.npy');chiS=load('chi_survival.npy');chig=load('chi_click_density.npy');indices=np.rint(tt/dt).astype(int)
  require(np.max(np.abs(t[indices]-tt))<1e-12 and np.all(np.diff(indices)==100) and indices[-1]==20000,'Exact aligned tangent panels')
  hp=np.asarray([math.fsum(dp[i:j].tolist()) for i,j in zip(indices[:-1],indices[1:])]);chiP=chig*np.diff(tt)
  # Reconstruct the supplied kernel quadrature without importing its solver.
  kernel=load('kernel_summary.npz');ks={k:kernel[k] for k in kernel.files};kernel.close()
  total=ks['kernel_jump_probability']+ks['kernel_anticommutator_probability']
  require(np.array_equal(total,ks['kernel_total_probability']),'Tangent jump plus anticommutator')
  rs=np.zeros(len(tt));rp=np.zeros(len(tt)-1)
  for j in range(1,len(tt)):
   widths=np.diff(tt[:j+1]);w=np.zeros(j+1);w[:-1]+=widths/2;w[1:]+=widths/2
   rs[j]=np.dot(w,ks['kernel_survival'][j,:j+1])
   rp[j-1]=np.dot(w[:-1],total[j-1,:j])
  require(np.max(np.abs(rs-chiS))<1e-14 and np.max(np.abs(rp-ks['chi_panel_probability']))<1e-14,'Tangent independent kernel quadrature')
  require(np.array_equal(ks['chi_panel_probability']/np.diff(tt),chig),'Tangent density divided by panel duration')
  kernel_check={'jump_plus_anticommutator_exact':True,'max_survival_reconstruction_difference':float(np.max(np.abs(rs-chiS))),'max_panel_reconstruction_difference':float(np.max(np.abs(rp-ks['chi_panel_probability'])))}
  tangent={'reference_case_sha256':sha(b),'source_archive':reference_archive,'source_member':reference_member,'file_hashes_verified':len(man),'independent_kernel_check':kernel_check,'configuration_gmres':config['gmres'],'T':10.,'panel_width':.05,'number_panels':200,'chi_D_from_panel_sum':math.fsum(chiP.tolist()),'chi_D_from_survival':-float(chiS[-1]),'linear_endpoint_prediction':lam*math.fsum(chiP.tolist()),'finite_endpoint_from_dp_sum':math.fsum(dp.tolist()),'finite_minus_linear_endpoint':math.fsum(dp.tolist())-lam*math.fsum(chiP.tolist()),'endpoint_relative_departure_percent':100*(math.fsum(dp.tolist())/(lam*math.fsum(chiP.tolist()))-1), 'complete_panel_record_residual':.5*(math.fsum(np.abs(hp-lam*chiP).tolist())+abs(float(ds[-1]-lam*chiS[-1]))),'qualified_scope':'Single-rate, matched-panel descriptive comparison with archived numerical tangent. Different GMRES accuracies and insertion quadrature remain; no T10 rate-halving, complete convergence or curvature certificate.'}
  (base/'reference').mkdir(exist_ok=True);(base/'reference/U2I_native_case.zip').write_bytes(b)
  exact_csv(base/'data/Tangent_comparison_panels.csv',{'left':tt[:-1],'right':tt[1:],'midpoint':(tt[:-1]+tt[1:])/2,'finite_delta_probability':hp,'linear_delta_probability':lam*chiP,'finite_minus_linear':hp-lam*chiP})
  np.savez_compressed(base/'data/Tangent_Comparison.npz',times=tt,finite_delta_panels=hp,linear_delta_panels=lam*chiP,chi_survival=chiS,chi_density=chig)
  metrics['tangent']=tangent
 save_json(base/'METRICS.json',metrics)
 print(json.dumps(metrics,indent=2))

if __name__=='__main__':main()
