"""Pinned pi/800 continuation, or an isolated equivalence/smoke test.
The production propagation/compression kernels are unchanged from the audited PC2 package.
All truncation and compression omissions remain separately accounted; no trace restoration.
"""
from __future__ import annotations
import argparse, math, shutil, time, traceback, os
from dataclasses import replace
from pathlib import Path
import numpy as np
from archive_tools import require, digest_file, plain_json
from common import (BASE, PACKAGE_DIR, all_true, config, cumulative, history_prefix_equal,
                    load_module, reserve_line, save_npz, utc, write_json, ControlledStop)
from fresh_inputs import read_inputs, static_check, initial_histories
from checkpoints import write_checkpoint
from resources import ResourceGuard
from diagnostic_io import DiagnosticIO
import spectral_components as spec
import memory_components as mem
from pool_control import Controller, PHASES
from reference_lu import ZeroCayleyLU, run_detector_with_refined_zero, benchmark_for_config

def detector_checks(a: dict, engine) -> dict:
    return {
        'direct_zero_solve': a.get('zero_reference_refinement',{}).get('method') == 'sparse_direct_cayley_superlu_complex128'
            and a['zero_reference_refinement']['true_relative_residual'] <= 5e-13
            and abs(a['zero_reference_refinement']['zero_midpoint_closure']) <= 5e-12,
        'batch64': a['batch64_contract_respected'] is True and a['maximum_actual_batch_columns'] <= 64,
        'gmres': not any(a['multi_rhs_info']) and a['maximum_multi_rhs_true_residual'] <= engine.TRUE_RESIDUAL_TOL,
        'zero_midpoint': abs(a['zero_midpoint_closure']) <= engine.DETECTOR_CLOSURE_TOL,
        'positive_midpoint': abs(a['positive_midpoint_closure']) <= engine.DETECTOR_CLOSURE_TOL,
        'sample_state': a['sample_batch_vs_independent_relative_error'] <= engine.BATCH_SAMPLE_REL_TOL,
        'sample_click': a['sample_midpoint_probability_absolute_difference'] <= engine.BATCH_SAMPLE_CLICK_ABS_TOL,
        'sample_gmres': not any(a['sample_independent_info'])
              and a['maximum_sample_independent_true_residual'] <= engine.TRUE_RESIDUAL_TOL,
    }

def state_from_checkpoint(data: dict, backend, engine, cfg: dict):
    checkpoint, meta = data['checkpoint'], data['metadata']
    if checkpoint is None:
        initial = backend.to_backend_array(data['initial_cpu'][:, None])
        return engine.PrefixState(family={0:initial.copy()}, zero_state=initial.copy(),
            representation_ledger=0., event_first_crossing_ledger=0., cumulative_click=0.,
            cumulative_zero_click=0., cumulative_overflow_bound=0., previous_overflow_intensity=0., completed_step=0)
    family = {}
    for k,rank in enumerate(cfg['start']['ranks']):
        if rank:
            value = np.load(checkpoint/f'sector_{k}.npy', allow_pickle=False)
            family[k] = backend.to_backend_array(value)
    zero = backend.to_backend_array(np.load(checkpoint/'zero_state.npy',allow_pickle=False))
    return engine.PrefixState(family=family,zero_state=zero,
        representation_ledger=float(meta['representation_ledger']),
        event_first_crossing_ledger=float(meta['event_first_crossing_ledger']),
        cumulative_click=float(meta['cumulative_click']),cumulative_zero_click=float(meta['cumulative_zero_click']),
        cumulative_overflow_bound=float(meta['cumulative_overflow_bound']),
        previous_overflow_intensity=float(meta['previous_overflow_intensity']),completed_step=int(meta['completed_step']))

def main() -> int:
    ap=argparse.ArgumentParser();ap.add_argument('--project-root',type=Path,required=True)
    ap.add_argument('--output-dir',type=Path,required=True)
    ap.add_argument('--parent-checkpoint',type=Path)
    ap.add_argument('--smoke-end-step',type=int)
    ap.add_argument('--probe-end-step',type=int)
    ap.add_argument('--optimization-mode',choices=('baseline','buffered'),default='buffered')
    args=ap.parse_args();cfg=config();root=args.project_root.resolve()
    require(os.environ.get('SLURM_JOB_ID','').isdecimal(),'Run only in an allocated PC2 job')
    out=args.output_dir.resolve();work=root/cfg['package_name']/'work'
    require(out.is_relative_to(work) and out!=work,'Output must be a new directory beneath this package[ARCHIVE_PATH]')
    cfg['output_relative']=str(out.relative_to(root))
    if args.smoke_end_step is not None:
        require(os.environ.get('TASK09_PI800_SMOKE')=='1','Smoke endpoint override requires smoke launcher')
        require(1<=args.smoke_end_step<=8,'Smoke steps outside 1..8')
        cfg['gate']['end_step']=args.smoke_end_step
    if args.probe_end_step is not None:
        require(args.smoke_end_step is None and os.environ.get('TASK09_PI800_BRIDGE')=='1',
                'Bridge override requires the allocated one-step comparison launcher')
        require(out.is_relative_to(work/'bridge'),'Probe output must be isolated beneath work/bridge')
        cfg['gate']['end_step']=args.probe_end_step
    require(args.smoke_end_step is not None or args.parent_checkpoint is not None,
            'Production is checkpoint continuation only; fresh positive launch is not authorized')
    require(args.optimization_mode=='buffered' or args.smoke_end_step is not None or args.probe_end_step is not None,
            'Baseline mode is restricted to equivalence tests')
    log_label='pi800-smoke' if args.smoke_end_step is not None else ('pi800-bridge-'+args.optimization_mode if args.probe_end_step is not None else 'pi800-600-gated')
    data=read_inputs(root,cfg,parent_checkpoint=args.parent_checkpoint,trace_factors=True)
    if args.probe_end_step is not None:
        require(args.probe_end_step==cfg['start']['step']+1,'Bridge must advance exactly one step')
    bridge_validation=None
    if args.smoke_end_step is None and args.probe_end_step is None:
        from control import require_replay
        bridge_validation=require_replay(cfg,data)
        data['report']['optimization_equivalence_gate']=bridge_validation
    zero_benchmark=benchmark_for_config(cfg)
    require(args.smoke_end_step is not None or zero_benchmark is not None,'Production requires the pinned full-grid zero benchmark')
    require(zero_benchmark is None or len(zero_benchmark['zero_survival'])>cfg['gate']['end_step'],
            'Zero benchmark does not cover requested endpoint: run zero_extension.py prepare; never disable this gate')
    require(root==Path(cfg['project_root']),'Unexpected project root')
    output=root/cfg['output_relative'];require(not output.exists(),'Output collision');output.mkdir(parents=True)
    started=time.perf_counter();state=None;histories={};records=[];rank_records=[];comps=[];memory=[];checkpoints=[]
    new_rep=[];new_event=[];all_rep=[];all_event=[];iofix=None;kb=None;bp=None;pool=None;inherited_bridge=None;step=cfg['start']['step']
    diag=None; timing_records=[]
    guard=ResourceGuard(root,cfg,started);guard.install_signals()
    status={'schema':'task09-pi800-session-status-v1','started_utc':utc(),'status':'initializing',
        'completed_step':step,'last_persisted_step':step,'start_step':step,'target_step':cfg['gate']['end_step'],
        'production_authorized':False,'physical_claim':False,'task10_eligible':False,'automatic_resume':False}
    write_json(output/'run_status.json',status)
    def persist_checkpoint(reason):
        guard.before_checkpoint(sum(int(x.shape[1]) for x in state.family.values()))
        ck_started=time.perf_counter()
        ck=write_checkpoint(output,state,histories,backend=backend,cfg=cfg,
                            all_rep_terms=all_rep,all_event_terms=all_event,reason=reason)
        checkpoints.append(ck)
        if kb is not None: kb['flush_full']('committed_checkpoint')
        if iofix is not None: iofix['flush_full']('committed_checkpoint')
        if diag is not None: diag.flush_full('committed_checkpoint')
        guard.checkpoint_costs.append(time.perf_counter()-ck_started)
        status.update(last_persisted_step=ck['step'])
        write_json(output/'run_status.json',status)
        return ck
    try:
        static_check(PACKAGE_DIR,cfg)
        histories=data['histories'];all_rep=list(data['inherited_representation_terms']);all_event=list(data['inherited_event_terms'])
        write_json(output/'input_audit.json',data['report'])
        runtime_copy=output/'RUNTIME_SOURCES';runtime_copy.mkdir()
        for name in cfg['runtime_sources']:
            shutil.copyfile(data['runtime']/name,runtime_copy/name)
        engine_name='PARENT_Task09_ES_G2P_prefix155_event_sectors_nonaccepting.py'
        engine=load_module(data['runtime']/engine_name,'task09_g6h_engine')
        parent,parent_identity=engine.load_parent_authority(data['runtime'])
        backend=parent.NumericalBackend('cupy');bm=backend.metadata()
        require(cfg['hardware']['gpu_name_contains'].upper() in str(bm.get('cuda_device_name','')).upper(),
                f"H100 device required: {bm}")
        expected_versions=cfg['required_runtime_versions']
        for key,field in [('numpy','numpy_version'),('scipy','scipy_version'),('cupy','cupy_version'),('cuda_runtime','cuda_runtime_version')]:
            require(bm.get(field)==expected_versions[key],f'Frozen numerical runtime version mismatch: {field}: {bm.get(field)} != {expected_versions[key]}')
        require(bm.get('total_bytes',0)>=cfg['hardware']['minimum_gpu_memory_mib']*2**20,
                'Allocated H100 memory below package minimum')
        cp=backend._cp;cp.get_default_memory_pool().free_all_blocks();cp.get_default_pinned_memory_pool().free_all_blocks()
        memory.append(mem.memory_snapshot('start_empty_pools',cp))
        p=cfg['physical'];g=cfg['gate']
        operators=parent.build_oscillator_operators(p['n_shell'],p['omega'])
        require(operators.audit['all_checks_passed'],'Oscillator authority')
        z,hz,_=parent.build_reference_grid(p['n_z'],p['l_z']);require(float(hz)==p['h_z'],'Physical grid spacing')
        pcfg=parent.RunConfig(execution_gate='ES-G2P',backend='cupy',propagator_type='spinor',omega=p['omega'],n_shell=p['n_shell'],n_z=p['n_z'],l_z=p['l_z'],
            dt=p['dt'],t_final=g['end_step']*p['dt'],stop_after_steps=g['end_step'],rate_lambda=p['rate_lambda'],
            **cfg['fresh_launch'],
            detector_rhs_batch_columns=64,factor_block_columns=64,resume_from_checkpoint=False,
            representation_budget=0.,planned_compression_calls=2*g['end_step'],output_root=output)
        initial=parent.build_initial_state(pcfg,operators,z,hz)
        data['initial_cpu']=initial
        # Original physical launch. On resume this is not substituted for the saved evolved state.
        propagator=parent.build_propagator_objects(pcfg,operators,backend,initial)
        require(propagator.roof_sign_audit['spinor_roof_term_sign_passed'],'Roof sign authority')
        zero_solver=ZeroCayleyLU(propagator,pcfg,operators,cfg['zero_solver'])
        bath=parent.build_bath_kraus(operators,'upward',p['rate_lambda']*p['dt']/2.,backend)
        require(bath.completeness_residual<=engine.BATH_COMPLETENESS_TOL,'Bath completeness')
        gc=engine.GateConfig(backend='cupy',data_root=root,output_dir=output,n_shell=p['n_shell'],n_z=p['n_z'],
            l_z=p['l_z'],omega=p['omega'],dt=p['dt'],t_final=g['end_step']*p['dt'],num_steps=g['end_step'],
            rate_lambda=p['rate_lambda'],max_event_sector=p['max_event_sector'],detector_batch_columns=64,output_stride_steps=100,
            checkpoint_steps=(),independent_crosscheck_steps=(),hard_rank_stop=g['rank_guard'],preferred_rank=sum(cfg['start']['ranks']),
            walltime_guard_seconds=g['wall_guard_seconds'],require_u2i_reference=False,save_large_checkpoint=False,development_mode=False)
        write_json(output/'runtime_setup.json',{'backend':bm,'parent_identity':parent_identity,
            'operator_audit':operators.audit,'roof_audit':propagator.roof_sign_audit,
            'bath_completeness_residual':float(bath.completeness_residual),'h_z':hz,
            'source_identity_pins':cfg['runtime_sources'],'rate_lambda':p['rate_lambda'],
            'zero_reference_solver':cfg['zero_solver'],
            'positive_detector_bath_compression_arithmetic_unchanged':True,'dead_temporary_lifetime_optimized':True})
        state=state_from_checkpoint(data,backend,engine,cfg)
        if data['checkpoint'] is None:
            histories=initial_histories(engine,gc,state,operators,hz,backend)
            data['histories']={k:v.copy() for k,v in histories.items()}
        write_json(output/'origin.json',data['report'])
        iofix=mem.install_postdetector_telemetry_iofix2(spec,output_dir=output)
        diag=DiagnosticIO(output,spec,args.optimization_mode,cfg['performance']['detector_progress_seconds'])
        kb=mem.install_bath_kraus_blockfix1(engine=engine,backend=backend,output_dir=output,block_columns=64)
        bp=spec.install_postdetector_bathtraceblockfix2(engine=engine,backend=backend,output_dir=output,h_z=hz,block_columns=64)
        require(cumulative(cfg['legacy']['representation_ledger'],all_rep)==state.representation_ledger,'Inherited ordered representation sum')
        require(cumulative(cfg['legacy']['event_ledger'],all_event)==state.event_first_crossing_ledger,'Inherited ordered event sum')
        inherited_bridge={'passed':True,'source_identity_report':data['source_equivalence_record'],
            'fresh_initialization':data['checkpoint'] is None,'resume_checkpoint':str(data['checkpoint']) if data['checkpoint'] else None,
            'detector_bath_compression_cores_unchanged':True,'rank_ladder_same_ordered_fsum_inputs':True,'optimization_mode':args.optimization_mode,'gpu_equivalence_replay_performed':bridge_validation is not None,'equivalence_gate':bridge_validation}
        write_json(output/'source_equivalence_record.json',inherited_bridge)
        print(f"[pi800-start] exact checkpoint={state.completed_step}; inherited_rep_terms={len(all_rep)}; next_global_call={2*state.completed_step+1}; static primitive identity recorded; no cross-hardware replay",flush=True)
        backend.synchronize();cp.get_default_memory_pool().free_all_blocks()
        memory.append(mem.memory_snapshot('after_exact_checkpoint_load',cp))
        pool=Controller(output=output,backend=backend,memory=memory,snapshot=mem.memory_snapshot,write_json=diag.pool_writer)
        status['status']='running';write_json(output/'run_status.json',status)
        (output/'spectra').mkdir();(output/'detector_telemetry').mkdir()
        base=cfg['legacy']['representation_ledger'];ebase=cfg['legacy']['event_ledger']
        if state.completed_step==0:
            persist_checkpoint('fresh_launch_zero_ledgers')
        for step in range(cfg['start']['step']+1,g['end_step']+1):
            guard.before_step(step,sum(int(x.shape[1]) for x in state.family.values()))
            require(state.completed_step==step-1,'State continuity failed')
            timing={'step':step,'optimization_mode':args.optimization_mode}
            st=time.perf_counter();before=engine.family_trace(state.family,hz,backend);zb=engine.physical_trace(state.zero_state,hz,backend)
            lb=cumulative(base,all_rep);require(lb==state.representation_ledger,'Ordered ledger continuity')
            local_terms=[];local_comps=[];local_summaries=[];local_bath=[];local_ranks=[]
            working=state.family;zero_new=None;pc=zc=0.;da=None;trace_detector=None
            for half_index,half in enumerate(('first','second')):
                call=2*step-1+half_index;line=reserve_line(call,cfg)
                prior=cumulative(base,[*all_rep,*local_terms])
                context=f'step_{step}_{half}_bath_half';kb['set_context'](context);bp['set_context'](context)
                phase_started=time.perf_counter()
                raw,event,ba=engine.bath_half_truncated(working,bath.operators_backend,config=gc,h_z=hz,backend=backend)
                timing[half+'_bath_seconds']=time.perf_counter()-phase_started
                require(abs(ba['trace_closure_before_compression'])<=engine.BATH_LEDGER_CLOSURE_TOL,'Raw bath closure failed before rank-resource decision')
                backend.synchronize();memory.append(mem.memory_snapshot(f'step{step}_{half}_raw',cp))
                pool.flush(step,half+'_before_analysis')
                phase_started=time.perf_counter()
                su,grams,sp,internal=spec.analyze_family_spectrum(raw,h_z=hz,backend=backend,engine=engine,
                    ledger_before=prior,ceiling=line,call_index=call,step=step,half=half,half_time=(step-.5+.5*half_index)*p['dt'])
                timing[half+'_spectrum_seconds']=time.perf_counter()-phase_started
                file=f'spectra/call_{call}_{half}.npz';save_npz(output/file,**sp)
                r=su['minimum_admissible_rank_under_current_ceiling']
                rr={'step':step,'call_index':call,'half':half,'spectrum_file':file,'ledger_before':prior,
                    'reserve_line':line,'minimum_admissible_rank':r,'negative_gram_mass':su['negative_gram_mass'],
                    'support_rank':su['support_rank']}
                rank_records.append(rr)
                require(r is not None,'No rank meets the prospective line')
                require(su['negative_gram_mass']<=1e-16,'Numerical-zero/negative Gram mass guard failed')
                if r>g['rank_guard']:
                    raise ControlledStop('RANK_RESOURCE_GUARD',{'attempted_step':step,'call_index':call,'required_rank':r,'guard':g['rank_guard']})
                pool.flush(step,half+'_before_compression')
                phase_started=time.perf_counter()
                nxt,co,charge=spec.compress_from_analysis(raw,internal=internal,target_rank=r,
                    ledger_base=base,committed_terms=[*all_rep,*local_terms],ledger_before=prior,ceiling=line,
                    h_z=hz,backend=backend,engine=engine)
                backend.synchronize();memory.append(mem.memory_snapshot(f'step{step}_{half}_compression',cp))
                timing[half+'_compression_seconds']=time.perf_counter()-phase_started
                rr.update(selected_rank=r,selected_discard=charge,ledger_after=co['ledger_after'],allocation=co['sector_ranks_after'])
                comp=dict(co,step=step,half=half,call_index=call);comps.append(comp)
                local_comps.append(comp);local_terms.append(charge);local_summaries.append(su);local_ranks.append(r)
                bath_before=before if half_index==0 else trace_detector
                bath_after=engine.family_trace(nxt,hz,backend)
                bc=float(bath_before-bath_after-event-charge)
                require(abs(ba['trace_closure_before_compression'])<=engine.BATH_LEDGER_CLOSURE_TOL
                    and abs(bc)<=engine.BATH_LEDGER_CLOSURE_TOL,'Bath closure failed')
                local_bath.append({'event':float(event),'preclosure':float(ba['trace_closure_before_compression']),'postclosure':bc})
                working=nxt
                del raw,internal,grams,sp
                cp.get_default_memory_pool().free_all_blocks()
                if half_index==0:
                    detdir=output/'detector_telemetry'/f'step{step}';detdir.mkdir()
                    phase_started=time.perf_counter()
                    zero_new,working,zc,pc,da=run_detector_with_refined_zero(state.zero_state,working,
                        zero_solver=zero_solver,frozen=spec.run_bundled_detector_traceblockfix1,
                        parent=parent,operators=operators,parent_config=pcfg,propagator=propagator,
                        backend=backend,crosscheck=True,engine=engine,output_dir=detdir)
                    timing['detector_seconds']=time.perf_counter()-phase_started
                    if args.optimization_mode in ('baseline','buffered'):
                        # BLF1: production lifetimes are common to both test arms.
                        # The detector returns a new family; keep state.family for rollback,
                        # but release the now-unused first-half compressed family.
                        del nxt
                    all_true(detector_checks(da,engine),f'Detector step {step}')
                    det_telemetry=plain_json((detdir/'detector_traceblockfix1_telemetry.json').read_bytes())
                    memory.extend(item['memory_after_batch'] for item in det_telemetry['batches'] if 'memory_after_batch' in item)
                    trace_detector=engine.family_trace(working,hz,backend)
                    backend.synchronize();memory.append(mem.memory_snapshot(f'step{step}_after_detector',cp))
                    cp.get_default_memory_pool().free_all_blocks()
            after=engine.family_trace(working,hz,backend);za=engine.physical_trace(zero_new,hz,backend)
            ei=math.fsum(x['event'] for x in local_bath);ri=math.fsum(local_terms)
            fc=float(before-after-pc-ei-ri);zcres=float(zb-za-zc)
            ev=cumulative(ebase,[*all_event,ei]);bound=float(engine.analytic_event_tail(step,bath,gc))
            top=float(engine.top_shell_population(working,operators=operators,config=gc,h_z=hz,backend=backend))
            oi=gc.rate_lambda*(gc.n_shell+2.)*top
            overflow=state.cumulative_overflow_bound+.5*gc.dt*(state.previous_overflow_intensity+oi)
            traces,ranks=engine.family_sector_metrics(working,config=gc,h_z=hz,backend=backend)
            backend.synchronize();memory.append(mem.memory_snapshot(f'step{step}_completed_candidate',cp))
            maxmem=max(cfg['start']['inherited_internal_memory_peak_mib'],max(x['driver_used_bytes'] for x in memory)/2**20)
            zero_reference_end=cfg['zero_reference']['available_through_step']
            zero_crossrun_checked=step<=zero_reference_end
            zero_diff=(abs(za-float(data['zero_reference_histories']['zero_survival'][step]))
                       if zero_crossrun_checked else None)
            benchmark_diff=abs(za-float(zero_benchmark['zero_survival'][step])) if zero_benchmark is not None else None
            checks={
                'zero_direct_benchmark':benchmark_diff is None or benchmark_diff<=cfg['zero_solver']['benchmark_survival_tolerance'],
                'full_step_closure':abs(fc)<=max(1e-10,2*engine.BATH_LEDGER_CLOSURE_TOL+engine.DETECTOR_CLOSURE_TOL),
                'zero_step_closure':abs(zcres)<=engine.DETECTOR_CLOSURE_TOL,
                'event_tail':ev<=bound+engine.EVENT_BOUND_TOL,'overflow':overflow<=engine.TOP_SHELL_OVERFLOW_TOL,
                'nonnegative_clicks':pc>=0. and zc>=0.,'positive_survival':after>=0. and za>=0.,
                'survival_nonincrease':after-before<=engine.SURVIVAL_INCREASE_TOL and za-zb<=engine.SURVIVAL_INCREASE_TOL,
                'rate_unchanged':gc.rate_lambda==cfg['physical']['rate_lambda'],
                'zero_crossrun_scope':(
                    zero_crossrun_checked and zero_diff<=g['zero_crossrun_tolerance']) or (
                    not zero_crossrun_checked and step>zero_reference_end),
                'rank_resource':sum(ranks)<=g['rank_guard'],'memory_resource':maxmem<=g['memory_guard_mib'],
                'cumulative_ledger_closure':abs(after+math.fsum([state.cumulative_click,float(pc)])+cumulative(base,[*all_rep,*local_terms])+ev-float(histories['positive_survival'][0]))<=5e-8,
                'zero_cumulative_closure':abs(za+math.fsum([state.cumulative_zero_click,float(zc)])-float(histories['zero_survival'][0]))<=5e-8,
                'reserve':cumulative(base,[*all_rep,*local_terms])<=reserve_line(2*step,cfg),
            }
            checks={k:bool(v) for k,v in checks.items()}
            if not all(checks.values()):
                write_json(output/'failed_candidate.json',{'step':step,'physical_time':step*p['dt'],
                    'candidate_committed':False,'last_committed_step':state.completed_step,'checks':checks,
                    'zero_survival':float(za),'zero_crossrun_reference':float(data['zero_reference_histories']['zero_survival'][step]) if zero_crossrun_checked else None,
                    'zero_crossrun_difference':zero_diff,'zero_crossrun_tolerance':g['zero_crossrun_tolerance'],
                    'representation_ledger':cumulative(base,[*all_rep,*local_terms]),
                    'maximum_sampled_memory_mib':float(maxmem),
                    'candidate_phase_timings':dict(timing, candidate_elapsed_seconds=time.perf_counter()-st),
                    'zero_reference_refinement':da['zero_reference_refinement']})
            all_true({k:v for k,v in checks.items() if k not in ('rank_resource','memory_resource')},f'Candidate non-resource checks {step}')
            if not checks['rank_resource'] or not checks['memory_resource']:
                raise ControlledStop('COMPLETED_CANDIDATE_RESOURCE_GUARD',{'attempted_step':step,'checks':checks,'memory_mib':maxmem,'rank':int(sum(ranks))})
            all_true(checks,f'Candidate step {step}')
            require([(f['step'],f['phase']) for f in pool.flushes][-4:]==[(step,x) for x in PHASES], 'Four pool flushes missing')
            candidate=engine.PrefixState(family=working,zero_state=zero_new,representation_ledger=local_comps[-1]['ledger_after'],
                event_first_crossing_ledger=ev,cumulative_click=math.fsum([state.cumulative_click,float(pc)]),
                cumulative_zero_click=math.fsum([state.cumulative_zero_click,float(zc)]),cumulative_overflow_bound=overflow,
                previous_overflow_intensity=oi,completed_step=step)
            record={'step':step,'physical_time':step*p['dt'],'first_rank':int(local_ranks[0]),'second_rank':int(local_ranks[1]),
                'total_rank':int(sum(ranks)),'sector_ranks':[int(x) for x in ranks],
                'positive_survival':float(after),'zero_survival':float(za),'positive_click':float(pc),'zero_click':float(zc),
                'representation_ledger':candidate.representation_ledger,'representation_increment':ri,'event_increment':ei,
                'event_ledger':ev,'overflow_bound':float(overflow),'top_shell_population':top,
                'reserve_line':reserve_line(2*step,cfg),'reserve_margin':reserve_line(2*step,cfg)-candidate.representation_ledger,
                'gmres_max_residual':float(da['maximum_multi_rhs_true_residual']),
                'full_step_closure':fc,'zero_closure':zcres,
                'zero_crossrun_checked':bool(zero_crossrun_checked),
                'zero_crossrun_reference_end_step':int(zero_reference_end),
                'zero_crossrun_difference':zero_diff,
                'zero_reference_refinement':da['zero_reference_refinement'],
                'zero_direct_benchmark_checked':zero_benchmark is not None,
                'zero_direct_benchmark_difference':benchmark_diff,
                'maximum_internal_driver_used_mib':maxmem,'step_wall_seconds':time.perf_counter()-st,'checks':checks}
            new_hist=mem.append_history(histories,step=step,state=candidate,positive_survival=after,zero_survival=za,
                positive_click=pc,zero_click=zc,sector_traces=traces,sector_ranks=ranks,representation_increment=ri,
                event_increment=ei,analytic_event_bound=bound,top_shell=top,full_step_closure=fc,zero_closure=zcres,
                detector_audit=da,step_wall_seconds=record['step_wall_seconds'])
            new_hist['representation_ceiling'][-1]=reserve_line(2*step,cfg)
            # Transactional state/history commit after all candidate checks.
            state=candidate;histories=new_hist;all_rep.extend(local_terms);all_event.append(ei);new_rep.extend(local_terms);new_event.append(ei);records.append(record)
            if step%g['checkpoint_stride']==0 or step==g['end_step']:
                persist_checkpoint('endpoint' if step==g['end_step'] else 'cadence')
            timing['step_with_checkpoint_seconds']=time.perf_counter()-st
            timing['step_without_checkpoint_seconds']=record['step_wall_seconds']
            timing_records.append(timing)
            guard.step_costs.append(time.perf_counter()-st)
            status.update(completed_step=step,last_persisted_step=checkpoints[-1]['step'] if checkpoints else cfg['start']['step'])
            write_json(output/'run_status.json',status)
            print(f"[{log_label}] step={step} t={step*p['dt']:.6f} ranks={local_ranks[0]}/{local_ranks[1]} "
                  f"ledger={state.representation_ledger:.16e} reserve_margin={record['reserve_margin']:.3e} "
                  f"wall={record['step_wall_seconds']:.2f}s",flush=True)
            del working,zero_new,nxt,candidate
            backend.synchronize();cp.get_default_memory_pool().free_all_blocks()
        require(history_prefix_equal(data['histories'],histories),'Inherited pi/800 prefix altered')
        status.update(status='completed',passed=True,verdict='PASS_'+BASE+'_NONACCEPTING',classification='COMPLETED_REQUESTED_PI800_GRID_PREFIX_NOT_PHYSICAL_ACCEPTANCE')
        return_code=0
    except ControlledStop as e:
        status.update(status='clean_nonaccepting_stop',passed=False,verdict='STOP_'+BASE+'_NONACCEPTING',
                      classification=e.classification,details=e.detail,attempted_step=step)
        return_code=2
        if state is not None and state.completed_step>(checkpoints[-1]['step'] if checkpoints else cfg['start']['step']):
            try:
                persist_checkpoint('clean_resource_stop')
            except ControlledStop as persist_stop:
                status['terminal_checkpoint_deferred']={'classification':persist_stop.classification,'details':persist_stop.detail}
            except Exception as persist_error:
                status.update(status='execution_or_numerical_failure',passed=False,verdict='FAIL_'+BASE,
                    classification='TERMINAL_CHECKPOINT_FAILURE',message=str(persist_error),traceback=traceback.format_exc())
                return_code=1
    except Exception as e:
        status.update(status='execution_or_numerical_failure',passed=False,verdict='FAIL_'+BASE,
                      classification=type(e).__name__,message=str(e),traceback=traceback.format_exc(),attempted_step=step)
        return_code=1
        # Never save the rejected candidate or convert a numerical failure into a PASS.
        if type(e).__name__=='IntegrityError' and state is not None and state.completed_step>status.get('last_persisted_step',cfg['start']['step']):
            try:
                persist_checkpoint('last_committed_state_after_integrity_failure')
                status['emergency_checkpoint_saved']=True
            except Exception as checkpoint_error:
                status['emergency_checkpoint_saved']=False
                status['emergency_checkpoint_error']=str(checkpoint_error)
    finally:
        try:
            if kb is not None: kb['mark_completed']() if status['status']=='completed' else kb['mark_failed'](RuntimeError(status.get('classification','stop')))
            if bp is not None: bp['mark_completed']() if status['status']=='completed' else bp['mark_failed'](RuntimeError(status.get('classification','stop')))
            if iofix is not None: iofix['flush_full']('terminal_finalization')
        except Exception as log_error:
            status.update(status='execution_or_numerical_failure', passed=False, verdict='FAIL_'+BASE,
                          finalization_error=str(log_error), classification='TELEMETRY_FINALIZATION_FAILURE')
            return_code=1
        if diag is not None:
            try: diag.flush_full('terminal_finalization')
            except Exception as io_error:
                status.update(status='execution_or_numerical_failure',passed=False,verdict='FAIL_'+BASE,classification='OPTIMIZED_LOG_FINALIZATION_FAILURE',message=str(io_error));return_code=1
        write_json(output/'timing_records.json',{'records':timing_records,'scope':'Wall-clock phases; unchanged numerical histories and operations'})
        if histories: save_npz(output/'block_histories.npz',**histories)
        status.update(completed_utc=utc(),elapsed_seconds=time.perf_counter()-started,
            completed_step=state.completed_step if state is not None else cfg['start']['step'],
            last_persisted_step=checkpoints[-1]['step'] if checkpoints else cfg['start']['step'])
        write_json(output/'resource_records.json',{'records':guard.records,'checkpoint_wall_seconds':guard.checkpoint_costs,'step_inclusive_wall_seconds':guard.step_costs})
        write_json(output/'rank_decisions.json',{'records':rank_records})
        write_json(output/'compression_records.json',{'records':comps})
        write_json(output/'block_step_records.json',{'records':records})
        write_json(output/'checkpoint_records.json',{'records':checkpoints})
        write_json(output/'memory_snapshots.json',{'snapshots':memory})
        report={**status,'configuration':cfg,'step_records':records,'rank_records':rank_records,
            'checkpoint_records':checkpoints,'source_equivalence_record':inherited_bridge,'endpoint':records[-1] if records else None,
            'new_representation_terms_committed':new_rep,'new_event_terms_committed':new_event,
            'all_forward_representation_terms_committed':all_rep,'all_forward_event_terms_committed':all_event,
            'inherited_representation_terms':data['inherited_representation_terms'] if data else [],
            'inherited_event_terms':data['inherited_event_terms'] if data else [],
            'pool_flush_count':len(pool.flushes) if pool else 0,
            'kraus_block_summary':kb['summary']() if kb else None,'telemetry_iofix2':iofix['summary']() if iofix else None,
            'claim_boundary':cfg['claim_boundary']}
        write_json(output/'block_report.json',report);write_json(output/'run_status.json',status)
        summary={**status,'configuration':cfg,'endpoint':records[-1] if records else None,
            'new_committed_steps':len(records),'attempted_compression_calls':len(rank_records),
            'new_committed_representation_terms':len(new_rep),'total_forward_representation_terms':len(all_rep),
            'new_committed_event_terms':len(new_event),'total_forward_event_terms':len(all_event),
            'persisted_checkpoints':len(checkpoints),'latest_checkpoint':checkpoints[-1] if checkpoints else None,
            'origin_sha256':data['report']['origin_sha256'] if data else None,'gpu_equivalence_replay_performed':bridge_validation is not None,'equivalence_gate':bridge_validation,
            'detailed_records_file':'block_report.json','detailed_records_sha256':digest_file(output/'block_report.json'),
            'claim_boundary':report['claim_boundary']}
        write_json(output/'summary_report.json',summary)
        if diag is not None: diag.restore()
        if iofix is not None: iofix['restore']()
        guard.restore_signals()
    print(status['verdict'],flush=True)
    if status.get('traceback'): print(status['traceback'],flush=True)
    return return_code

if __name__=='__main__': raise SystemExit(main())
