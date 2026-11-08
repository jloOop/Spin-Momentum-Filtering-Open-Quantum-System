"""Noncommitting checkpoint-based H100 smoke gate; NOT cross-hardware equivalence.

Uses the unchanged primitives on copies of the complete parent family for one
trial bath half/compression, and a small checkpoint-derived detector sample.
No production checkpoint, history, click accumulation, event term or ledger term
is written. The inherited historical implementation bridge is not executed.
"""
from __future__ import annotations
import argparse, math, os, traceback
from pathlib import Path
import numpy as np
from archive_tools import require,digest_file,plain_json
from common import BASE,PACKAGE_DIR,config,load_module,reserve_line,cumulative,write_json,save_npz,utc,all_true
from inputs import static_check,read_inputs
from configuration_identity import configuration_identity
from half_rate_continue import state_from_checkpoint,detector_checks
from audit_outputs import reconstruct_spectrum
import memory_components as mem
import spectral_components as spec


def bridge(root: Path, report_path: Path):
    cfg=config()
    configuration_record=configuration_identity(cfg,package=PACKAGE_DIR)
    p=cfg['physical'];g=cfg['gate'];work=report_path.parent/'platform_bridge'
    require(root.resolve()==Path(cfg['project_root']), 'Wrong PC2 project root')
    require(not (root/cfg['output_relative']).exists(), 'Production output exists before platform gate')
    require(not work.exists() and not work.is_symlink(), 'Platform smoke-work directory collision')
    device=plain_json((report_path.parent/'h100_device_gate.json').read_bytes())
    require(device.get('passed') is True and device['job_id']==os.environ['SLURM_JOB_ID'],'Allocated H100 gate missing/wrong job')
    static_check(PACKAGE_DIR,cfg)
    data=read_inputs(root,cfg,trace_factors=True);work.mkdir()
    engine=load_module(data['runtime']/'PARENT_Task09_ES_G2P_prefix155_event_sectors_nonaccepting.py','task09_pc2_bridge_engine')
    parent,identity=engine.load_parent_authority(data['runtime'])
    backend=parent.NumericalBackend('cupy');cp=backend._cp
    bm=backend.metadata()
    for key,field in [('numpy','numpy_version'),('scipy','scipy_version'),('cupy','cupy_version'),('cuda_runtime','cuda_runtime_version')]:
        require(bm[field]==cfg['required_runtime_versions'][key], 'Runtime changed between device and platform gates')
    require('H100' in bm['cuda_device_name'].upper(), 'Wrong bridge GPU')
    operators=parent.build_oscillator_operators(p['n_shell'],p['omega'])
    require(operators.audit['all_checks_passed'],'Oscillator audit')
    z,hz,_=parent.build_reference_grid(p['n_z'],p['l_z']);require(float(hz)==p['h_z'],'Grid audit')
    pcfg=parent.RunConfig(execution_gate='ES-G2P',backend='cupy',propagator_type='spinor',
        omega=p['omega'],n_shell=p['n_shell'],n_z=p['n_z'],l_z=p['l_z'],dt=p['dt'],
        t_final=g['end_step']*p['dt'],stop_after_steps=g['end_step'],rate_lambda=p['rate_lambda'],
        z0=10.,sigma_z_amplitude=.5,k0=math.pi,kappa=math.pi,theta=math.pi/6.,phi=0.,
        detector_rhs_batch_columns=64,factor_block_columns=64,resume_from_checkpoint=False,
        representation_budget=0.,planned_compression_calls=2*g['end_step'],output_root=work)
    initial=np.asarray(np.load(data['checkpoint']/'zero_state.npy',allow_pickle=False)).reshape(-1)
    propagator=parent.build_propagator_objects(pcfg,operators,backend,initial)
    require(propagator.roof_sign_audit['spinor_roof_term_sign_passed'],'Roof sign audit')
    bath=parent.build_bath_kraus(operators,'upward',p['rate_lambda']*p['dt']/2.,backend)
    require(bath.completeness_residual<=engine.BATH_COMPLETENESS_TOL,'Bath completeness audit')
    gc=engine.GateConfig(backend='cupy',data_root=root,output_dir=work,n_shell=p['n_shell'],n_z=p['n_z'],
        l_z=p['l_z'],omega=p['omega'],dt=p['dt'],t_final=g['end_step']*p['dt'],num_steps=g['end_step'],
        rate_lambda=p['rate_lambda'],max_event_sector=4,detector_batch_columns=64,output_stride_steps=100,
        checkpoint_steps=(),independent_crosscheck_steps=(),hard_rank_stop=g['rank_guard'],preferred_rank=sum(cfg['start']['ranks']),
        walltime_guard_seconds=g['wall_guard_seconds'],require_u2i_reference=False,save_large_checkpoint=False,development_mode=False)
    state=state_from_checkpoint(data,backend,engine,cfg)
    iofix=mem.install_postdetector_telemetry_iofix2(spec,output_dir=work)
    kb=mem.install_bath_kraus_blockfix1(engine=engine,backend=backend,output_dir=work,block_columns=64)
    bp=spec.install_postdetector_bathtraceblockfix2(engine=engine,backend=backend,output_dir=work,h_z=hz,block_columns=64)
    snapshots=[]
    def memory(label):
        backend.synchronize();snap=mem.memory_snapshot(label,cp);snapshots.append(snap)
        require(snap['driver_used_bytes']/2**20<=g['memory_guard_mib'],'Platform trial memory guard exceeded')
        return snap
    try:
        before=engine.family_trace(state.family,hz,backend);zero=engine.physical_trace(state.zero_state,hz,backend)
        require(abs(before-cfg['start']['positive_survival_metadata'])<=g['bridge_scalar_absolute_tolerance'],'GPU parent-family trace changed')
        require(abs(zero-cfg['start']['zero_survival_metadata'])<=g['bridge_scalar_absolute_tolerance'],'GPU parent-zero trace changed')
        rep_terms=list(data['inherited_representation_terms']);event_terms=list(data['inherited_event_terms'])
        require(cumulative(cfg['legacy']['representation_ledger'],rep_terms)==state.representation_ledger,'Parent ordered ledger changed')
        require(cumulative(cfg['legacy']['event_ledger'],event_terms)==state.event_first_crossing_ledger,'Parent ordered event ledger changed')
        memory('parent_loaded');step=cfg['start']['step']+1;call=2*step-1;line=reserve_line(call,cfg)
        kb['set_context']('uncommitted_pc2_platform_trial_first_bath');bp['set_context']('uncommitted_pc2_platform_trial_first_bath')
        raw,event,bath_audit=engine.bath_half_truncated(state.family,bath.operators_backend,config=gc,h_z=hz,backend=backend)
        require(abs(bath_audit['trace_closure_before_compression'])<=engine.BATH_LEDGER_CLOSURE_TOL,'Trial bath closure')
        cp.get_default_memory_pool().free_all_blocks();memory('trial_raw_bath')
        summary,grams,spectra,internal=spec.analyze_family_spectrum(raw,h_z=hz,backend=backend,engine=engine,
            ledger_before=state.representation_ledger,ceiling=line,call_index=call,step=step,half='first',half_time=(step-.5)*p['dt'])
        rank=summary['minimum_admissible_rank_under_current_ceiling']
        require(rank is not None and rank<=g['rank_guard'],'Trial first-half rank exceeds the declared resource guard')
        require(summary['negative_gram_mass']<=1e-16,'Trial negative Gram mass exceeds unchanged guard')
        cp.get_default_memory_pool().free_all_blocks();memory('trial_analysis')
        trial,comp,charge=spec.compress_from_analysis(raw,internal=internal,target_rank=rank,
            ledger_base=cfg['legacy']['representation_ledger'],committed_terms=rep_terms,
            ledger_before=state.representation_ledger,ceiling=line,h_z=hz,backend=backend,engine=engine)
        after=engine.family_trace(trial,hz,backend)
        require(abs(before-after-event-charge)<=engine.BATH_LEDGER_CLOSURE_TOL,'Trial compressed bath closure')
        rr={'call_index':call,'ledger_before':state.representation_ledger,'reserve_line':line,
            'minimum_admissible_rank':rank,'negative_gram_mass':summary['negative_gram_mass'],
            'selected_rank':rank,'selected_discard':charge,'ledger_after':comp['ledger_after'],'allocation':comp['sector_ranks_after']}
        saved_check=reconstruct_spectrum(spectra,rr,cfg=cfg)
        save_npz(work/f'trial_call{call}_spectrum.npz',**spectra)
        write_json(work/f'trial_call{call}_analysis.json',{'summary':summary,'compression':comp,'independent_saved_spectrum_check':saved_check,
            'authoritative_term_committed':False})
        memory('trial_compressed')
        take=cfg['port']['smoke_detector_columns_per_sector']
        sample={k:cp.ascontiguousarray(x[:,:min(take,x.shape[1])]) for k,x in sorted(trial.items())}
        sample_ranks={str(k):int(x.shape[1]) for k,x in sample.items()}
        del raw,trial,internal,grams,spectra
        cp.get_default_memory_pool().free_all_blocks()
        detdir=work/'sample_detector';detdir.mkdir()
        znext,fnext,zc,pc,da=spec.run_bundled_detector_traceblockfix1(state.zero_state,sample,parent=parent,operators=operators,
            parent_config=pcfg,propagator=propagator,backend=backend,crosscheck=True,engine=engine,output_dir=detdir)
        all_true(detector_checks(da,engine),'H100 checkpoint-derived detector smoke checks')
        memory('sample_detector_complete')
        # Trial charge/clicks are deliberately not added to the canonical histories or ledgers.
        require(state.completed_step==cfg['start']['step'] and state.representation_ledger==cfg['start']['representation_ledger'],
                'Platform smoke gate changed authoritative in-memory frontier')
        require(rep_terms==data['inherited_representation_terms'] and event_terms==data['inherited_event_terms'],'Trial mutated inherited terms')
        for name,expected in cfg['checkpoint_payloads'].items():
            require(digest_file(data['checkpoint']/name)==expected,'Parent file changed during platform smoke gate')
        require(not (root/cfg['output_relative']).exists(),'Platform smoke gate created production output')
        kb['mark_completed']();bp['mark_completed']();iofix['flush_full']('platform_smoke_terminal')
        require(configuration_identity(cfg,package=PACKAGE_DIR)==configuration_record,
                'Recovery configuration changed during platform smoke')
        return {'schema':'task09-pc2-checkpoint-based-platform-smoke-v1','passed':True,'completed_utc':utc(),
            'job_id':os.environ['SLURM_JOB_ID'],'parent_result_sha256':cfg['parent_result']['sha256'],
            'checkpoint_payload_hashes':cfg['checkpoint_payloads'],'start_step':cfg['start']['step'],
            'last_persisted_step':cfg['start']['step'],'next_authoritative_call':call,
            **configuration_record,
            'phase':cfg['phase'],
            'source_driver_sha256':digest_file(PACKAGE_DIR/'half_rate_continue.py'),
            'runtime_versions':device['runtime_versions'],'device_name':device['device_name'],
            'parent_identity':identity,'gpu_parent_family_trace':before,'gpu_parent_zero_trace':zero,
            'trial_first_half_rank':rank,'trial_first_half_charge_not_committed':charge,
            'trial_first_half_ledger_not_committed':comp['ledger_after'],
            'sample_detector_ranks':sample_ranks,'sample_detector_audit':da,
            'sample_detector_clicks_not_committed':{'positive':pc,'zero':zc},
            'memory_snapshots':snapshots,'full_physical_steps_performed':0,'authoritative_steps_advanced':0,
            'trial_bath_halves_performed':1,'sample_detector_substeps_performed':1,
            'authoritative_ledger_terms_added':0,'authoritative_checkpoint_changed':False,
            'historical_implementation_bridge_repeated':False,'cross_hardware_bitwise_identity_proven':False,
            'scope':cfg['port']['precontinuation_smoke_scope']}
    finally:
        iofix['restore']()

def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    try:result=bridge(a.project_root,a.report);rc=0;marker='PASS_'+BASE+'_PLATFORM_SMOKE'
    except Exception as exc:
        result={'passed':False,'message':str(exc),'traceback':traceback.format_exc(),'authoritative_steps_advanced':0}
        rc=1;marker='FAIL_'+BASE+'_PLATFORM_SMOKE'
    result['verdict']=marker;write_json(a.report,result);print(marker,flush=True)
    if rc:print(result['traceback'],flush=True)
    return rc
if __name__=='__main__':raise SystemExit(main())
