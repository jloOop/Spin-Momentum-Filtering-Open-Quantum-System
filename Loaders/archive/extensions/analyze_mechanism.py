#!/usr/bin/env python3
"""CPU-only reductions from captured immutable arrays; never executes a solver.
python analyze_mechanism.py --inputs inputs --out /new/output
Dependencies: NumPy, Matplotlib. All numerical arrays retain native resolution.
"""
import argparse, csv, hashlib, json, os, platform, importlib.metadata
from pathlib import Path
import numpy as np
from native_io import require, maxabs, reconstruct, sha_file, write_csv, write_json

MODES=('00','10','01')
PREPS=('00','10','01','first','p060','pold','p095')
PVALUES={'00':0.,'first':1.,'p060':.6,'pold':.8104003212089722,'p095':.95}
HORIZONS=(3.6,6.,8.,9.,10.,12.,15.,20.)
PROFILE_T=(6.,10.,12.,15.,20.)
EDGES=(0.,3.6,10.,20.)
GATES=((0.,3.6),(3.6,10.),(10.,20.),(3.6,20.),(0.,20.))


def npfile(p):
    a=np.load(p,allow_pickle=False)
    if isinstance(a,np.lib.npyio.NpzFile):
        with a:a={k:a[k] for k in a.files}
    for v in (a.values() if isinstance(a,dict) else [a]):
        if v.dtype.kind in 'iufc':require(np.isfinite(v).all(),'Nonfinite native input: '+str(p))
    return a


def index(t,x):
    ids=np.flatnonzero(np.isclose(t,x,rtol=0,atol=4e-15))
    require(len(ids)==1,f'T={x} is not a unique native node')
    return int(ids[0])


def weights(t,a,b):
    """One-sided endpoint weights on [a,b]; split endpoints contribute half per side."""
    w=np.zeros(len(t))
    if b<=a:return w
    lo,hi=index(t,a),index(t,b);dt=np.diff(t[lo:hi+1])
    w[lo:hi]+=.5*dt;w[lo+1:hi+1]+=.5*dt
    return w


def cumulative_trap(v,t):return np.r_[0.,np.cumsum(.5*(v[:-1]+v[1:])*np.diff(t))]


def load(inputs,tag,m):
    folder=inputs/tag/('mode'+m)
    one=lambda suffix:next(folder.glob('*'+suffix))
    k=npfile(one('_kernel_summary.npz'));t=npfile(one('_times.npy'))
    cfg=json.loads(one('_configuration.json').read_text());src=npfile(one('_source_insertion_summary.npz'))
    s,p=reconstruct(t,k)
    return dict(t=t,k=k,cfg=cfg,src=src,s=s,p=p,d=-s,roof=np.r_[0.,np.cumsum(p)],
                saved_s=npfile(one('_chi_survival.npy')),saved_g=npfile(one('_chi_click_density.npy')),
                status=json.loads(one('_run_status.json').read_text()),prefix=str(one('_times.npy')).removesuffix('_times.npy'))


def sign_intervals(t,v,floor):
    rows=[]
    for sign in (-1,1):
        mask=sign*v>floor
        edges=np.flatnonzero(np.diff(np.r_[False,mask,False])).reshape(-1,2)
        for a,b in edges:
            rows.append(dict(sign=int(sign),first_T=float(t[a]),last_T=float(t[b-1]),
                             native_span=float(t[b-1]-t[a]),node_count=int(b-a)))
    return rows


def crossings(t,v,floor=0.):
    ids=np.flatnonzero(abs(v)>floor);rows=[]
    for left,right in zip(ids[:-1],ids[1:]):
        if v[left]*v[right]<0:
            rows.append(dict(left=float(t[left]),right=float(t[right]),left_value=float(v[left]),
                             right_value=float(v[right]),direction='negative_to_positive' if v[left]<0 else 'positive_to_negative',
                             unresolved_nodes_between=int(right-left-1)))
    return rows


def algebra_tests():
    t=np.arange(0,21)*.05;n=len(t)
    P=np.zeros((n-1,n))
    for k in range(n-1):P[k,:k+1]=(k+1)*.0001*np.arange(1,k+2)
    q=-np.vstack([np.zeros(n),np.cumsum(P,axis=0)])
    S,p=reconstruct(t,{'kernel_survival':q,'kernel_total_probability':P})
    closure=maxabs(S+np.r_[0.,np.cumsum(p)])
    quadrature=max(abs(weights(t,0.,float(T))@np.ones(n)-T) for T in t)
    split=maxabs(weights(t,0.,.35)+weights(t,.35,.65)+weights(t,.65,1.)-weights(t,0.,1.))
    # Equal mixtures of opposite signed laws cancel before taking absolute values.
    law=np.array([.4,-.2,-.2]);mixed=.5*law+.5*(-law)
    require(.5*abs(mixed).sum()==0 and .5*(.5*abs(law).sum()+.5*abs(-law).sum())>0,'Mix-before-norm test')
    require(.5*(abs(.4)+abs(-.4))==.4,'Censoring atom test')
    N=12;labels=[(nx,n-nx) for n in range(N+1) for nx in range(n,-1,-1)];lookup={v:i for i,v in enumerate(labels)}
    ladders=[]
    for axis in (0,1):
        A=np.zeros((len(labels),len(labels)))
        for j,l in enumerate(labels):
            if l[axis]>0:
                low=list(l);low[axis]-=1;A[lookup[tuple(low)],j]=np.sqrt(l[axis])
        ladders.append(A)
    shells=np.array([sum(l) for l in labels]);Q=sum(A@A.T for A in ladders)
    projected=maxabs(Q-np.diag(shells+2-(N+2)*(shells==N)))
    shell_res=[]
    for n0 in range(N):
        rho=np.diag((shells==n0)/(n0+1));next_rho=np.diag((shells==n0+1)/(n0+2))
        B=sum(A.T@rho@A-.5*(A@A.T@rho+rho@A@A.T) for A in ladders)
        shell_res.append(maxabs(B-(n0+2)*(next_rho-rho)))
    native=[(nx,n-nx) for n in range(N+1) for nx in range(n+1)]
    perm=np.zeros((182,182))
    for mu,l in enumerate(labels):
        for spin in range(2):perm[spin*91+mu,2*native.index(l)+spin]=1.
    perm_error=maxabs(perm@perm.T-np.eye(182))
    require(max(closure,quadrature,split,projected,max(shell_res),perm_error)<1e-12,'Synthetic/algebra self-test failed')
    return dict(kind='Synthetic indexing/quadrature and 91-orbital finite algebra only; no dynamics',
                causal_reconstruction_residual=closure,quadrature_residual=quadrature,split_additivity_residual=split,
                mixing_before_norm_passed=True,censoring_atom_passed=True,projected_Q_identity_residual=projected,
                shell_ladder_identity_max_residual=max(shell_res),tested_shells=list(range(12)),
                audit02_to_working_permutation_residual=perm_error,all_passed=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--inputs',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--no-figures',action='store_true',help='Reproduce numerical reductions and self-tests only')
    args=ap.parse_args();out=args.out.resolve();inputs=args.inputs.resolve();out.mkdir(parents=True,exist_ok=True)
    require(not (out/'tables').exists(),'Existing analysis products; use a fresh destination')
    for d in ('tables','figures'): (out/d).mkdir()
    lineage=json.loads((inputs/'lineage.json').read_text())
    for r in lineage:require(sha_file(inputs.parent/r['local'])==r['member_sha256'],'Captured input hash mismatch')
    tests=algebra_tests();write_json(out/'self_tests.json',tests)
    c={};aud={};prefix=[];inventory=[]
    contract=json.loads((inputs/'T20/CONTRACT.json').read_text())
    for m in MODES:
        v=load(inputs,'T20',m);parent=load(inputs,'T10',m);c[m]=v;t=v['t'];cfg=v['cfg'];n=len(t)
        for key,val in contract['response_contract']['fixed_configuration'].items():require(cfg[key]==val,'Configuration mismatch: '+key)
        require(cfg['initial_mode']==m and n==401 and cfg['num_steps']==80000,'Mode/grid mismatch')
        actual_source=next((inputs/'T20'/('mode'+m)).glob('*_07_environmental_response_solver.py'))
        require(sha_file(actual_source)==cfg['source_sha256']==contract['response_contract']['modes'][m]['source_sha256'],'Executed source identity differs')
        completion=json.loads((inputs/f'T20/state/MODE{m}_COMPLETE.json').read_text())
        worker=json.loads((inputs/f'T20/state/WORKER_{m}_START.json').read_text())
        require(completion['mode']==m and worker['mode']==m and worker['array_job_id']=='2970583' and worker['index']==MODES.index(m),'Worker/completion identity mismatch')
        require(cfg['task05_reference_gmres_rtol']==1e-8 and cfg['gmres']['branch_rtol']==1e-12 and cfg['gmres']['response_reference_rtol']==1e-12,'Reference role mismatch')
        k=v['k'];q=k['kernel_survival'];P=k['kernel_total_probability'];src=v['src']
        I=np.vstack([np.zeros(n),np.cumsum(P,axis=0)]);v.update(I=I,q=q,P=P,J=k['kernel_jump_probability'],A=k['kernel_anticommutator_probability'])
        causaltrace=np.tril(np.ones_like(q))*src['trace_total'][None,:]
        raw=maxabs(q+I);corrected=maxabs(q+I-causaltrace)
        checks=dict(kernel_closure_to_zero=raw,kernel_closure_retaining_source_trace=corrected,
             source_trace_max=maxabs(src['trace_total']),source_jump_anti_identity=maxabs(src['trace_terms']-(src['jump_norm2']-src['anti_expectation'])),
             activity_sum_identity=maxabs(src['activity_total']-src['jump_norm2'].sum(axis=1)),
             source_trace_sum_identity=maxabs(src['trace_total']-src['trace_terms'].sum(axis=1)),
             activity_conditioning_identity=maxabs(src['activity_total']-src['reference_survival']*src['reference_s_up']),
             projected_activity_formula=maxabs(src['reference_s_up']-(src['reference_s_down']+2-14*src['reference_top_shell'])),
             causal_survival=maxabs(np.triu(q,1)),causal_roof=maxabs(np.triu(P,1)),
             jump_plus_signed_anti=maxabs(P-v['J']-v['A']),survival_reconstruction=maxabs(v['s']-v['saved_s']),
             panel_reconstruction=maxabs(v['p']-k['chi_panel_probability']),density_reconstruction=maxabs(v['p']/np.diff(t)-v['saved_g']),
             tangent_closure=maxabs(v['d']-v['roof']))
        for key in ('survival_reconstruction','panel_reconstruction','density_reconstruction','jump_plus_signed_anti'):require(checks[key]<=2e-13,key+' exceeds tolerance')
        require(raw<=5e-8 and checks['source_trace_max']<=5e-11 and checks['tangent_closure']<=5e-10,'Physical array closure tolerance failure')
        require(checks['causal_roof']==checks['causal_survival']==0.,'Noncausal values')
        bp=inputs/'T20/baselines'/m/'response_matched.npz';b=npfile(bp);meta=json.loads(bp.with_suffix('.json').read_text())
        require(meta['gmres_rtol']==1e-12 and len(b['times'])==80001 and len(b['step_probability'])==80000,'Matched baseline family wrong')
        inds=k['insertion_steps'];require(np.array_equal(b['times'][inds],t),'Baseline source times mismatch')
        R=np.r_[0.,np.cumsum(b['step_probability'])];bclosure=b['survival']+R-b['survival'][0]
        checks.update(baseline_probability_closure=maxabs(bclosure),baseline_min_midpoint_probability=float(b['step_probability'].min()),
                      baseline_source_survival=maxabs(b['survival'][inds]-src['reference_survival']),
                      baseline_activity_conditional=maxabs(b['source_up'][inds]-src['reference_s_up']))
        require(b['step_probability'].min()>=0 and maxabs(bclosure)<=5e-9,'Matched reference law failed')
        v.update(S0=b['survival'][inds],D0roof=R[inds],D0survival=b['survival'][0]-b['survival'][inds],
                 baselineP=np.array([np.sum(b['step_probability'][a:bb]) for a,bb in zip(inds[:-1],inds[1:])]),
                 activity=src['activity_total'],top=src['reference_top_shell'],down=src['reference_s_down'])
        require(np.array_equal(t[:201],parent['t']),'Parent grid mismatch')
        for key,a,bb in [('survival',v['saved_s'][:201],parent['saved_s']),('click_density',v['saved_g'][:200],parent['saved_g']),
            ('reconstructed_S',v['s'][:201],parent['s']),('reconstructed_roof',v['roof'][:201],parent['roof']),
            ('source_survival',src['reference_survival'][:201],parent['src']['reference_survival'])]:
            prefix.append(dict(mode=m,quantity=key,max_abs=maxabs(a-bb),exact_equal=bool(np.array_equal(a,bb))))
        for key in ('kernel_survival','kernel_total_probability','kernel_jump_probability','kernel_anticommutator_probability'):
            a=k[key][:201 if key=='kernel_survival' else 200,:201];bb=parent['k'][key]
            prefix.append(dict(mode=m,quantity=key,max_abs=maxabs(a-bb),exact_equal=bool(np.array_equal(a,bb))))
        require(all(r['exact_equal'] for r in prefix),'Prefix changed')
        aud[m]=checks
        inventory.append(dict(mode=m,case=cfg['manual_stage_folder_number'],native_status=v['status']['status'],native_exit=v['status']['exit_code'],
                              source_sha256=cfg['source_sha256'],numerical_core_sha256=cfg['numerical_core_sha256'],
                              initial_activity=float(v['activity'][0]),final_D_survival=float(v['d'][-1]),final_D_roof=float(v['roof'][-1])))
    t=c['00']['t'];require(all(np.array_equal(v['t'],t) for v in c.values()),'Different mode grids')
    linear=('s','p','d','roof','I','q','P','J','A','S0','D0roof','D0survival','baselineP','activity')
    c['first']={k:(c['10'][k]+c['01'][k])/2 for k in linear}
    for name in ('p060','pold','p095'):
        p=PVALUES[name];c[name]={k:(1-p)*c['00'][k]+p*c['first'][k] for k in linear}
    # Screening rules are diagnostic resolution scales, NOT discretization error bounds.
    floor_I=max(1e-12,10*max(a['kernel_closure_to_zero'] for a in aud.values()))
    floor_D=max(1e-12,10*max(a['tangent_closure'] for a in aud.values()))
    floor_ratio=1e-12
    selected=[];history=[];signs=[];extrema=[];persistence=[];tv_checks={};roots=[]
    for name in PREPS:
        v=c[name];v['mu']=cumulative_trap(v['s'],t);v['ATV']=.5*(np.r_[0.,np.cumsum(abs(v['p']))]+abs(v['s']))
        v['density']=v['p']/np.diff(t)
        v['activity_conditional']=np.divide(v['activity'],v['S0'],out=np.full_like(t,np.nan),where=abs(v['S0'])>floor_ratio)
        v['effectiveness']=np.divide(v['I'][-1],v['activity'],out=np.full_like(t,np.nan),where=abs(v['activity'])>floor_ratio)
        tv_checks[name]=float(np.min(np.diff(v['ATV'])))
        require(tv_checks[name]>=-5e-10,'A_TV decreases beyond closure allowance')
        for i,T in enumerate(t):
            row=dict(preparation=name,p=PVALUES.get(name,''),T=float(T),chi_D_survival=float(v['d'][i]),chi_D_roof=float(v['roof'][i]),
                     chi_S=float(v['s'][i]),chi_mu_restricted=float(v['mu'][i]),A_TV_with_censoring=float(v['ATV'][i]),
                     own_baseline_S=float(v['S0'][i]),own_baseline_D_roof=float(v['D0roof'][i]),own_baseline_D_survival=float(v['D0survival'][i]),
                     activity=float(v['activity'][i]),activity_per_survivor=float(v['activity_conditional'][i]))
            history.append(row)
            if any(i==index(t,x) for x in HORIZONS):selected.append(row)
        for kind,floor in [('raw',0.),('screened',floor_D)]:
            signs.extend(dict(preparation=name,quantity='cumulative_survival_response',screen=kind,**r) for r in crossings(t,v['d'],floor))
        signs.extend(dict(preparation=name,quantity='panel_average_density_response',screen='raw',**r) for r in crossings(.5*(t[:-1]+t[1:]),v['density']))
        persistence.extend(dict(preparation=name,**r) for r in sign_intervals(t,v['d'],floor_D))
        for kind,i in [('minimum',int(np.argmin(v['d']))),('maximum',int(np.argmax(v['d'])))]:extrema.append(dict(preparation=name,kind=kind,T=float(t[i]),response=float(v['d'][i])))
    for i,T in enumerate(t):
        row=dict(T=float(T))
        for kind,key in [('survival','d'),('roof','roof')]:
            a,b=c['00'][key][i],c['first'][key][i];den=b-a;r=-a/den if abs(den)>floor_D else np.nan
            valid=np.isfinite(r) and 0<=r<=1
            row['p_star_'+kind]=float(r) if valid else ''
            row['denominator_'+kind]=float(den)
            row['status_'+kind]='valid_affine_root' if valid else 'unresolved_denominator' if abs(den)<=floor_D else 'outside_unit_interval'
        roots.append(row)
    tables={'case_inventory':inventory,'prefix_comparison':prefix,'response_history':history,'selected_horizons':selected,'sign_changes':signs,'extrema':extrema,'sign_persistence':persistence,'mixture_crossings':roots}
    profiles=[];profile_stats=[];source_ranges=[];same_source=[];blocks=[];block_hist=[];late=[];additivity={};pulse_specs=[];pulseP=[];pulseS=[];gate_specs=[];gateP=[];gateS=[]
    blocks_np=np.zeros((len(PREPS),3,len(t)))
    for ni,name in enumerate(PREPS):
        v=c[name];I=v['I'];q=v['q']
        integrals=np.array([weights(t,0.,float(T))@I[i] for i,T in enumerate(t)])
        additivity[name]=dict(I_integrates_to_roof=maxabs(integrals-v['roof']),I_integrates_to_survival=maxabs(integrals-v['d']))
        require(maxabs(integrals-v['roof'])<2e-13,'I source integration mismatch')
        for T in PROFILE_T:
            i=index(t,T);vals=I[i];w=weights(t,0.,T);last=i+1;active=vals[:last]
            positive=float(w[vals>0]@vals[vals>0]);negative=float(w[vals<0]@vals[vals<0]);net=positive+negative
            profile_stats.append(dict(preparation=name,T=T,positive_integral=positive,negative_integral=negative,net=net,
                 cancellation_ratio=(positive-negative)/abs(net) if abs(net)>floor_D else '',
                 positive_nodal_measure=float(w[vals>floor_I].sum()),negative_nodal_measure=float(w[vals<-floor_I].sum()),
                 maximum=float(active.max()),maximum_s=float(t[np.argmax(active)]),minimum=float(active.min()),minimum_s=float(t[np.argmin(active)])))
            source_ranges.extend(dict(preparation=name,T=T,**r) for r in sign_intervals(t[:last],active,floor_I))
            for j in range(last):profiles.append(dict(preparation=name,T=T,s=float(t[j]),I_roof=float(vals[j]),I_survival=float(-q[i,j]),
                activity=float(v['activity'][j]),activity_per_survivor=float(v['activity_conditional'][j]),
                I_over_activity=float(vals[j]/v['activity'][j]) if abs(v['activity'][j])>floor_ratio else ''))
        for j in range(index(t,10.)+1):
            same_source.extend(dict(preparation=name,source_s=float(t[j]),**r) for r in crossings(t[j:],I[j:,j],floor_I))
        for bi,(a,b) in enumerate(zip(EDGES[:-1],EDGES[1:])):
            for i,T in enumerate(t):
                w=weights(t,a,min(b,float(T))) if T>a else np.zeros(len(t))
                value=float(w@I[i]);sv=float(-w@q[i]);blocks_np[ni,bi,i]=value
                block_hist.append(dict(preparation=name,source_start=a,source_end=b,T=float(T),chi_roof=value,chi_survival=sv,
                                       jump=float(w@np.sum(v['J'][:i],axis=0)),signed_anticommutator=float(w@np.sum(v['A'][:i],axis=0))))
        additivity[name]['source_block_history']=maxabs(blocks_np[ni].sum(axis=0)-v['roof'])
        require(additivity[name]['source_block_history']<2e-13,'Source blocks not additive')
        for oa,ob in zip(EDGES[:-1],EDGES[1:]):
            lo,hi=index(t,oa),index(t,ob)
            for sa,sb in zip(EDGES[:-1],EDGES[1:]):
                w=weights(t,sa,sb)
                vals={k:float(w@np.sum(v[k][lo:hi],axis=0)) for k in ('P','J','A')}
                if sa>=ob:require(vals['P']==0.,'Noncausal block nonzero')
                blocks.append(dict(preparation=name,output_start=oa,output_end=ob,source_start=sa,source_end=sb,
                                   total=vals['P'],jump=vals['J'],signed_anticommutator=vals['A']))
        delayed=float(weights(t,0.,10.)@(I[-1]-I[index(t,10.)]));new=float(weights(t,10.,20.)@I[-1]);delta=float(v['d'][-1]-v['d'][index(t,10.)])
        late.append(dict(preparation=name,delta_survival=delta,delta_roof=float(v['roof'][-1]-v['roof'][index(t,10.)]),delayed_earlier_action=delayed,new_action_after10=new,
                         sum=delayed+new,closure_residual=delta-delayed-new,delayed_fraction=delayed/(delayed+new) if abs(delayed+new)>floor_D else ''))
        for sign,label in ((1,'positive'),(-1,'negative')):
            eligible=[j for j in range(2,len(t)-2) if np.all(sign*I[-1,j-2:j+3]>floor_I)]
            if not eligible:continue
            j=max(eligible,key=lambda jj:sign*I[-1,jj]);a,b=float(t[j-2]),float(t[j+2]);w=weights(t,a,b)/(b-a)
            pulse_specs.append(dict(preparation=name,sign=label,s=float(t[j]),terminal_D_roof=float(I[-1,j]),terminal_D_survival=float(-q[-1,j]),
                neighborhood_start=a,neighborhood_end=b,neighbor_min=float(I[-1,j-2:j+3].min()),neighbor_max=float(I[-1,j-2:j+3].max()),
                normalized_narrow_gate_roof=float(w@I[-1]),law_closure=float(v['P'][:,j].sum()+q[-1,j]),
                label='DATA-DERIVED PREDICTION FOR FUTURE INDEPENDENT TEST'))
            pulseP.append(v['P'][:,j]);pulseS.append(q[:,j])
        for a,b in GATES:
            w=weights(t,a,b)/(b-a);pp=v['P']@w
            ss=np.array([q[i]@weights(t,a,min(b,float(T)))/(b-a) if T>a else 0. for i,T in enumerate(t)])
            gate_specs.append(dict(preparation=name,start=a,end=b,duration=b-a,terminal_D_roof=float(pp.sum()),terminal_D_survival=float(-ss[-1]),
                terminal_survival_atom=float(ss[-1]),A_TV_pulse_action=float(.5*(abs(pp).sum()+abs(ss[-1]))),
                activity_per_unit_action=float(w@v['activity']),law_closure=float(pp.sum()+ss[-1]),
                label='DATA-DERIVED PREDICTION FOR FUTURE INDEPENDENT TEST'))
            gateP.append(pp);gateS.append(ss)
    tables.update(source_profiles=profiles,source_profile_summary=profile_stats,source_sign_intervals=source_ranges,same_insertion_horizon_crossings=same_source,
                  source_output_blocks=blocks,source_block_histories=block_hist,late_change_decomposition=late,pulse_candidates=pulse_specs,gate_predictions=gate_specs)
    # Launch shell law: independent n=0 identity; n=2 is only inferred from n=1 kernel.
    zero,one=c['00'],c['first'];launch={}
    launch['ground_roof_identity']=maxabs(zero['I'][:,0]-2*(one['D0roof']-zero['D0roof']))
    launch['ground_survival_identity']=maxabs(-zero['q'][:,0]-2*(one['D0survival']-zero['D0survival']))
    launch['ground_panel_identity']=maxabs(zero['P'][:,0]-2*(one['baselineP']-zero['baselineP']))
    d2roof=one['D0roof']+one['I'][:,0]/3.;d2surv=one['D0survival']-one['q'][:,0]/3.;p2=one['baselineP']+one['P'][:,0]/3.
    s2=one['S0']+one['q'][:,0]/3.
    launch.update(inferred_shell2_roof_survival=maxabs(d2roof-d2surv),inferred_panel_min=float(p2.min()),inferred_D_min=float(d2roof.min()),
                  inferred_D_max=float(d2roof.max()),inferred_survival_min=float(s2.min()),inferred_survival_max=float(s2.max()),
                  inferred_roof_monotonic_min_increment=float(np.diff(d2roof).min()),inferred_survival_monotonic_max_increment=float(np.diff(s2).max()),
                  inferred_law_closure=maxabs(s2+d2roof-one['S0'][0]),status='INFERRED_FROM_LAUNCH_KERNEL; no independent shell2 propagation found in bounded search')
    require(max(launch[k] for k in ('ground_roof_identity','ground_survival_identity','ground_panel_identity'))<5e-10,'Launch shell0 identity failed')
    require(p2.min()>=-5e-10 and d2roof.min()>=-5e-10 and d2roof.max()<=1+5e-10 and s2.min()>=-5e-10 and s2.max()<=1+5e-10,'Inferred shell2 bounds failed')
    require(np.diff(s2).max()<=5e-10,'Inferred shell2 survival monotonicity failed')
    prediction_closure=dict(pulse_max_abs=max(abs(r['law_closure']) for r in pulse_specs),gate_max_abs=max(abs(r['law_closure']) for r in gate_specs))
    require(max(prediction_closure.values())<=5e-10,'Predicted complete law does not close')
    shellrows=[]
    for i,T in enumerate(t):shellrows.append(dict(T=float(T),D_shell0_roof=float(zero['D0roof'][i]),D_shell1_roof=float(one['D0roof'][i]),D_shell2_INFERRED_roof=float(d2roof[i]),
         D_shell0_survival=float(zero['D0survival'][i]),D_shell1_survival=float(one['D0survival'][i]),D_shell2_INFERRED_survival=float(d2surv[i]),
         launch_I0=float(zero['I'][i,0]),launch_I1=float(one['I'][i,0]),preceding_shell2_inferred_panel=float(p2[i-1]) if i else 0.))
    shellintervals=[]
    for label,v in [('D1_minus_D0',one['D0roof']-zero['D0roof']),('D2_inferred_minus_D1',d2roof-one['D0roof'])]:
        shellintervals.extend(dict(contrast=label,**r) for r in sign_intervals(t,v,floor_I))
    tables.update(shell_detectability=shellrows,shell_ordering_intervals=shellintervals)
    for name,rows in tables.items():write_csv(out/'tables'/f'{name}.csv',rows)
    np.savez_compressed(out/'pulse_gate_laws.npz',times=t,preparation_names=np.array(PREPS),
         pulse_preparations=np.array([r['preparation'] for r in pulse_specs]),pulse_source_times=np.array([r['s'] for r in pulse_specs]),
         pulse_panel_probability=np.array(pulseP),pulse_survival_history=np.array(pulseS),
         gate_preparations=np.array([r['preparation'] for r in gate_specs]),gate_windows=np.array([[r['start'],r['end']] for r in gate_specs]),
         gate_panel_probability=np.array(gateP),gate_survival_history=np.array(gateS),
         component_baseline_panel_probability=np.array([c[m]['baselineP'] for m in MODES]),
         inferred_shell2_panel_probability=p2,inferred_shell2_survival=s2)
    np.savez_compressed(out/'reconstructed_arrays.npz',times=t,preparation_names=np.array(PREPS),profile_horizons=np.array(PROFILE_T),
         chi_survival=np.array([c[m]['s'] for m in PREPS]),chi_panel_probability=np.array([c[m]['p'] for m in PREPS]),
         profiles_I_roof=np.array([[c[m]['I'][index(t,T)] for T in PROFILE_T] for m in PREPS]),
         profiles_I_survival=np.array([[-c[m]['q'][index(t,T)] for T in PROFILE_T] for m in PREPS]),source_block_roof_histories=blocks_np)
    # Cross-check existing archived endpoint/root audits, never use them to construct a curve.
    recorded_comparison={}
    for m in MODES:
        recorded=json.loads(next((inputs/'T20'/('mode'+m)).glob('*_integrated_response.json')).read_text())
        recorded_comparison[m]={'endpoint_survival_abs':abs(float(c[m]['d'][-1])-recorded['chi_D_from_final_survival']),
                                'endpoint_roof_abs':abs(float(c[m]['roof'][-1])-recorded['chi_D_from_panel_sum'])}
    symmetry={key:maxabs(c['10'][key]-c['01'][key]) for key in ('d','roof','q','P','activity','S0')}
    audit=dict(scientific_acceptance=False,new_evolution_performed=False,input_member_hashes_verified=len(lineage),native_checks=aud,
       declared_tolerances=contract['response_contract']['postprocessing_tolerances'],prefix_max_abs=max(r['max_abs'] for r in prefix),
       screening=dict(source_kernel_floor=floor_I,cumulative_response_and_root_denominator_floor=floor_D,ratio_denominator_floor=floor_ratio,
                      meaning='10 times measured closure residual, lower-bounded by 1e-12; numerical-floor screen only, not uncertainty or continuum bound'),
       source_integral_additivity=additivity,ATV_min_native_increment=tv_checks,launch_shell=launch,symmetry_max_abs=symmetry,
       recorded_audit_comparison=recorded_comparison,source_blocks=late,
       prediction_law_closure=prediction_closure,
       independent_root_max_abs_difference=max(abs(r['p_star_survival']-r['p_star_roof']) for r in roots if r['p_star_survival']!='' and r['p_star_roof']!=''),
       baseline_family='response_matched rtol=1e-12; separate Task05 regression rtol=1e-8 not substituted',
       runtime=dict(python=platform.python_version(),numpy=np.__version__,matplotlib=importlib.metadata.version('matplotlib')),script_sha256=sha_file(Path(__file__)),
       input_notes='Exact member lineage and SHA256: inputs/lineage.json. Writer meanings: SOURCE_SEMANTICS.md. Recorded audits remain under inputs/T20.',
       uncertainty_bounds=None,V9_available=False,independent_second_shell_available=False,independent_pulse_available=False)
    write_json(out/'audit.json',audit)
    if not args.no_figures:make_figures(out,t,c,roots,blocks_np,d2roof,pulse_specs,gate_specs,floor_I)
    print(json.dumps(dict(output=str(out),screening=audit['screening'],late_change=late,launch=launch,
                         priority_pulses=[r for r in pulse_specs if r['preparation'] in ('first','p095')]),indent=2))


def make_figures(out,t,c,roots,blocks,d2,pulses,gates,floor):
    os.environ['MPLCONFIGDIR']=str(out/'.matplotlib');os.environ['XDG_CACHE_HOME']=str(out/'.cache')
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import TwoSlopeNorm,SymLogNorm
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.labelsize':11,'pdf.fonttype':42,'path.simplify':False,'savefig.facecolor':'white'})
    colors={'00':'#1f77b4','first':'#ff7f0e','p095':'#9467bd'}
    labels={'00':r'Ground $|00\rangle$','first':'Incoherent first-shell','p095':r'Mixture $p=0.95$'}
    def save(fig,name):
        fig.savefig(out/'figures'/f'{name}.png',dpi=240)
        fig.savefig(out/'figures'/f'{name}.pdf',metadata={'Creator':'analyze_mechanism.py','CreationDate':None,'ModDate':None})
        plt.close(fig)
    def clean(ax):
        ax.spines[['top','right']].set_visible(False);ax.grid(color='.92',linewidth=.5);ax.set_axisbelow(True)
    fig,ax=plt.subplots(figsize=(8.2,4.9),layout='constrained')
    ax.plot(t,c['00']['d'],color=colors['00'],lw=2,label=r'Ground preparation $|00\rangle$')
    ax.plot(t,c['first']['d'],color=colors['first'],lw=2,label='Incoherent first-shell mixture')
    ax.axhline(0,color='#2ca02c',lw=1,label='Zero response',zorder=4)
    ax.set(xlim=(0,20),ylim=(-1.37,.40),xlabel=r'Observation horizon $T$',ylabel=r'Cumulative response $\chi_{D,\uparrow}(T)$')
    ax.set_xticks(np.arange(0,21,2));ax.legend(loc='lower left');ax.set_title(r'$\omega=144$',loc='right');clean(ax);save(fig,'F01_cumulative_response_T20')
    fig,axs=plt.subplots(1,2,figsize=(12,4.6),layout='constrained');ps=np.linspace(0,1,201)
    response=(1-ps[:,None])*c['00']['d']+ps[:,None]*c['first']['d']
    mesh=axs[0].pcolormesh(t,ps,response,shading='nearest',cmap='RdBu_r',norm=TwoSlopeNorm(vmin=float(response.min()),vcenter=0,vmax=float(response.max())))
    r=np.array([np.nan if row['p_star_survival']=='' else row['p_star_survival'] for row in roots])
    axs[0].plot(t,r,color='black',lw=1.4,label=r'$p_\star(T)$, screened');axs[0].legend(loc='lower left',fontsize=9)
    axs[0].set(xlabel='Observation horizon T',ylabel='First-shell mixture fraction p',title='Affine preparation response; native T grid',xlim=(0,20),ylim=(0,1));cb=fig.colorbar(mesh,ax=axs[0],label=r'$\chi_D(p;T)$');cb.solids.set_rasterized(False)
    for name in ('00','p060','pold','p095','first'):axs[1].plot(t,c[name]['d'],lw=1.6,label=f"p={PVALUES[name]:.12g}")
    axs[1].axhline(0,color='#2ca02c',lw=.8);axs[1].set(xlabel='Observation horizon T',ylabel=r'$\chi_D(p;T)$',xlim=(0,20),title='Fixed preparations; old p is never retuned');axs[1].legend(fontsize=8);clean(axs[1]);save(fig,'F02_preparation_horizon')
    fig,axs=plt.subplots(1,3,figsize=(13,4.1),layout='constrained');palette=plt.cm.viridis(np.linspace(.05,.95,len(PROFILE_T)))
    for ax,name in zip(axs,('00','first','p095')):
        for T,col in zip(PROFILE_T,palette):
            i=index(t,T);ax.plot(t[:i+1],c[name]['I'][i,:i+1],color=col,label=f'T={T:g}',lw=1.5)
        ax.axhline(0,color='#2ca02c',lw=.8);ax.set(xlabel='Source insertion time s',ylabel='I(s;T), per unit pulse action',title=labels[name],xlim=(0,20));clean(ax)
    axs[-1].legend(fontsize=8);save(fig,'F03_source_profiles')
    fig,axs=plt.subplots(1,3,figsize=(13,4.3),layout='constrained');edge=np.r_[t[0]-.025,.5*(t[:-1]+t[1:]),t[-1]+.025]
    bound=max(float(abs(c[n]['P']/np.diff(t)[:,None]).max()) for n in ('00','first','p095'))
    norm=SymLogNorm(linthresh=bound*.002,vmin=-bound,vmax=bound,base=10)
    for ax,name in zip(axs,('00','first','p095')):
        mesh=ax.pcolormesh(edge,t,c[name]['P']/np.diff(t)[:,None],cmap='RdBu_r',norm=norm,shading='flat',rasterized=False)
        ax.plot([0,20],[0,20],color='.25',lw=.7,ls=':');ax.set(xlabel='Source insertion time s',ylabel='Detector output time t',title=labels[name],xlim=(0,20),ylim=(0,20))
    cb=fig.colorbar(mesh,ax=axs,label='Signed roof density / unit action\n(symmetric log scale)');cb.solids.set_rasterized(False);save(fig,'F04_causal_kernel_maps')
    fig,axs=plt.subplots(1,3,figsize=(13,4.1),layout='constrained')
    for ax,name in zip(axs,('00','first','p095')):
        ni=PREPS.index(name)
        for bi,(a,b) in enumerate(zip(EDGES[:-1],EDGES[1:])):ax.plot(t,blocks[ni,bi],label=f'Sources [{a:g}, {b:g}]',lw=1.6)
        ax.plot(t,c[name]['roof'],color='black',lw=1.7,ls='--',label='Sum / cumulative roof');ax.axhline(0,color='#2ca02c',lw=.8);ax.axvline(10,color='.5',lw=.8,ls=':')
        ax.set(xlabel='Observation horizon T',ylabel='Signed cumulative contribution',title=labels[name],xlim=(0,20));clean(ax)
    axs[-1].legend(fontsize=8);save(fig,'F05_source_block_histories')
    fig,axs=plt.subplots(1,3,figsize=(13,4.1),layout='constrained')
    for v,label,col,style in [(c['00']['D0roof'],'Shell 0 bath-off',colors['00'],'-'),(c['first']['D0roof'],'Shell 1 bath-off',colors['first'],'-'),(d2,'Shell 2 INFERRED','#9467bd','--')]:axs[0].plot(t,v,label=label,color=col,ls=style)
    axs[0].set(xlabel='Observation horizon T',ylabel='Bath-off cumulative detection',title='Own baseline laws');axs[0].legend(fontsize=8)
    axs[1].plot(t,c['first']['D0roof']-c['00']['D0roof'],label=r'$D_1^0-D_0^0$');axs[1].plot(t,d2-c['first']['D0roof'],label=r'$D_{2,\mathrm{inferred}}^0-D_1^0$');axs[1].set(xlabel='Observation horizon T',ylabel='Detection contrast',title='Nonmonotonic launch-shell hierarchy');axs[1].legend(fontsize=8)
    axs[2].plot(t,c['00']['I'][:,0],label='Ground launch insertion',color=colors['00']);axs[2].plot(t,c['first']['I'][:,0],label='First-shell launch insertion',color=colors['first']);axs[2].set(xlabel='Observation horizon T',ylabel='I(0;T), unit pulse action',title='Single launch operation, not active bath');axs[2].legend(fontsize=8)
    for ax in axs:ax.axhline(0,color='#2ca02c',lw=.7);ax.set_xlim(0,20);clean(ax)
    save(fig,'F06_launch_shell_detectability')
    fig,axs=plt.subplots(1,2,figsize=(12,4.7),layout='constrained')
    for name in ('first','p095'):
        axs[0].plot(t,c[name]['I'][-1],label=labels[name],color=colors[name])
        for p in [r for r in pulses if r['preparation']==name]:
            axs[0].scatter(p['s'],p['terminal_D_roof'],s=30,color=colors[name])
            if p['sign']=='positive':
                axs[0].annotate(f"s={p['s']:.2f}",(p['s'],p['terminal_D_roof']),xytext=(0,9),textcoords='offset points',ha='center',fontsize=8)
            else:
                axs[0].annotate(f"s={p['s']:.2f}",(p['s'],p['terminal_D_roof']),xytext=(19 if name=='first' else 14,-.008),ha='center',fontsize=8,arrowprops={'arrowstyle':'-','color':colors[name],'lw':.8})
    axs[0].axhline(0,color='#2ca02c',lw=.7);axs[0].legend(fontsize=9);axs[0].set(xlabel='Pulse source time s',ylabel='Predicted terminal derivative / pulse action',title='T=20: opposite-sign pulse candidates',xlim=(0,20),ylim=(-.011,.044));clean(axs[0])
    xx=np.arange(len(GATES))
    for j,name in enumerate(('00','first','p095')):
        vals=[r['terminal_D_roof'] for r in gates if r['preparation']==name];axs[1].bar(xx+(j-1)*.23,vals,width=.23,label=labels[name],color=colors[name])
    axs[1].set_xticks(xx,[f'[{a:g}, {b:g}]' for a,b in GATES],rotation=20);axs[1].axhline(0,color='#2ca02c',lw=.7);axs[1].set(xlabel='Normalized rectangular source window',ylabel='Terminal derivative / integrated rate action',title='Data-derived predictions; no intervention run');axs[1].legend(fontsize=8);clean(axs[1]);save(fig,'F07_intervention_predictions')
    fig,axs=plt.subplots(2,2,figsize=(10,7),layout='constrained')
    for name in ('00','first','p095'):
        for ax,key in zip(axs.flat,('activity','activity_conditional','I','effectiveness')):
            vals=c[name][key][-1] if key=='I' else c[name][key];ax.plot(t,vals,label=labels[name],color=colors[name])
    for ax,label in zip(axs.flat,('Unnormalized source activity a(s)','Conditional activity a(s)/S0(s)','Terminal effectiveness I(s;20)','I(s;20)/a(s), diagnostic')):
        ax.set(xlabel='Source time s',ylabel=label,xlim=(0,20));ax.axhline(0,color='#2ca02c',lw=.7);clean(ax)
    axs[0,0].legend(fontsize=9);fig.suptitle('Activity and detectability response are distinct');save(fig,'F08_activity_effectiveness')


if __name__=='__main__':main()
