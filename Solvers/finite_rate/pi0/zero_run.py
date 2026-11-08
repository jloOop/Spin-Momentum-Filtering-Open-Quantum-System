"""Fresh or exact-checkpoint standalone lambda=0 control; same frozen detector kernel.

Production CLI is restricted to a PC2 H100 allocation. Unit tests call run_session
with the real SciPy kernel and explicitly labelled mock GPU-memory telemetry.
"""
from __future__ import annotations
import argparse,copy,json,math,os,shutil,time,traceback
from pathlib import Path
import numpy as np
from archive_tools import require,digest_file
from common import PACKAGE_DIR,config,utc,write_json,save_npz,ControlledStop
from zero_model import build_context,advance,top_population,scientific_identity,static_check
from checkpoints import write_checkpoint,verify_checkpoint
from resources import ResourceGuard
from audit_zero import NODES,INTERVALS

def append_node(h,step,S,click,mu,top,c,ref):
    compared=step<=c['zero_reference']['available_through_step']
    difference=abs(S-float(ref['zero_survival'][step])) if compared else 0.
    require(not compared or difference<=c['gate']['zero_crossrun_tolerance'],'Historical zero-reference survival mismatch')
    node={'times':step*c['physical']['dt'],'zero_survival':S,'cumulative_zero_click':click,
        'restricted_mean_trapezoid':mu,'probability_closure':S+click-float(h['zero_survival'][0] if step else S),
        'top_shell_population':top,'total_rank':1,'representation_ledger':0.,'event_first_crossing_ledger':0.,
        'analytic_event_tail_bound':0.,'cumulative_overflow_bound':0.,'reference_compared':bool(compared),'reference_difference':difference}
    for k in NODES:h[k].append(node[k])

def run_session(out,c=None,parent_checkpoint=None,end_step=None,backend_name='cupy'):
    c=copy.deepcopy(config() if c is None else c);out=Path(out).resolve();root=Path(c['project_root']).resolve()
    work=root/c['package_name']/'work'
    require(out.is_relative_to(work) and out!=work and not out.exists(),'Output must be a new directory inside this package[ARCHIVE_PATH]')
    require(not any(p.is_symlink() for p in [out,*out.parents] if p.exists()),'Symlink output ancestry is not allowed')
    target=c['gate']['end_step'] if end_step is None else end_step
    require(isinstance(target,int) and 1<=target<=c['gate']['end_step'],'Invalid requested endpoint')
    c['output_relative']=str(out.relative_to(root));out.mkdir(parents=True)
    started=time.perf_counter();guard=ResourceGuard(root,c,started);guard.install_signals()
    h={k:[] for k in NODES+INTERVALS};step=0;ctx=None;x=None;checkpoints=[]
    status={'schema':'task09-lambda0-session-status-v1','status':'initializing','started_utc':utc(),
        'completed_step':0,'last_persisted_step':None,'start_step':0,'target_step':target,'rate_lambda':0.,
        'parent_checkpoint':str(Path(parent_checkpoint).resolve()) if parent_checkpoint else None,
        'backend_requested':backend_name,'physical_claim':False,'task10_eligible':False,'automatic_resume':False}
    write_json(out/'run_status.json',status)
    def checkpoint(reason):
        guard.before_checkpoint(1);t=time.perf_counter()
        dest=out/f'checkpoint_step{step}'
        if not dest.exists():
            record=write_checkpoint(out,step,x,h,ctx,reason);checkpoints.append(record)
            guard.checkpoint_costs.append(time.perf_counter()-t)
        status['last_persisted_step']=step;write_json(out/'run_status.json',status)
    rc=1
    try:
        ctx=build_context(c,backend_name)
        write_json(out/'runtime_setup.json',{'backend':ctx.metadata,'source_identity':static_check(c),
          'scientific_identity':scientific_identity(c),'parent_identity':ctx.parent_identity,
          'physical':c['physical'],'fresh_launch':c['fresh_launch'],'solver':c['solver'],
          'roof_sign_audit':ctx.prop.roof_sign_audit,'zero_bath_completeness':ctx.bath.completeness_residual,
          'bath_applied':'identity skipped exactly','compression_applied':False,'checkpoint_stride':c['gate']['checkpoint_stride']})
        shutil.copyfile(PACKAGE_DIR/'CONFIG.json',out/'RELEASE_CONFIG.json')
        if parent_checkpoint is not None:
            cp=Path(parent_checkpoint).resolve()
            require(cp.is_relative_to(work),'Checkpoint outside this branch')
            meta,old,x_cpu,ca=verify_checkpoint(cp,c)
            step=meta['completed_step'];require(step<target,'Checkpoint already at or beyond target')
            h={k:v.tolist() for k,v in old.items()};x=ctx.backend.to_backend_array(x_cpu)
            status.update(start_step=step,completed_step=step)
            write_json(out/'input_audit.json',{'origin':'verified_same_zero_rate_checkpoint','checkpoint':str(cp),'audit':ca})
        else:
            x=ctx.backend.to_backend_array(ctx.initial[:,None].copy())
            S=ctx.engine.physical_trace(x,ctx.hz,ctx.backend)
            append_node(h,0,S,0.,0.,top_population(ctx,x),c,ctx.reference)
            write_json(out/'input_audit.json',{'origin':'original_frozen_launch','scientific_identity':scientific_identity(c),'past_data_imported':False})
        status['status']='running';write_json(out/'run_status.json',status)
        checkpoint('fresh_launch' if parent_checkpoint is None else 'verified_resume_seam')
        label='lambda0-360' if target==c['gate']['end_step'] else 'lambda0-smoke'
        print(f'[{label}] start_step={step} target_step={target} lambda=0 rank=1 bath=identity compression=disabled',flush=True)
        while step<target:
            guard.before_step(step+1,1);start=time.perf_counter()
            next_step=step+1;before=float(h['zero_survival'][-1])
            y,p,a=advance(ctx,x,out/'detector_telemetry'/f'step{next_step}')
            S=float(a['zero_after']);cum=math.fsum([h['cumulative_zero_click'][-1],p]);dt=c['physical']['dt']
            mu=math.fsum([h['restricted_mean_trapezoid'][-1],.5*dt*(before+S)])
            require(abs(S+cum-h['zero_survival'][0])<=c['gate']['cumulative_closure_tolerance'],'Cumulative probability closure failed')
            top=top_population(ctx,y);require(np.isfinite(top) and top>=0. and top<=S+5e-12,'Invalid top-shell population')
            if backend_name=='cupy':
                free,total=ctx.backend._cp.cuda.Device().mem_info
                if (total-free)/2**20>c['gate']['memory_guard_mib']:
                    raise ControlledStop('MEMORY_RESOURCE_GUARD',{'attempted_step':next_step,'used_mib':(total-free)/2**20})
            # Reference validation happens before committing the candidate state.
            if next_step<=c['zero_reference']['available_through_step']:
                require(abs(S-float(ctx.reference['zero_survival'][next_step]))<=c['gate']['zero_crossrun_tolerance'],'Historical zero-reference mismatch')
            elapsed=time.perf_counter()-start
            interval={'midpoint_times':(next_step-.5)*dt,'zero_click_probability':p,'click_density_midpoint':p/dt,
                'zero_step_closure':before-S-p,'gmres_max_residual':a['maximum_multi_rhs_true_residual'],
                'independent_gmres_max_residual':a['maximum_sample_independent_true_residual'],
                'sample_state_relative_error':a['sample_batch_vs_independent_relative_error'],
                'sample_click_abs_difference':a['sample_midpoint_probability_absolute_difference'],
                'gmres_failure_count':sum(v!=0 for v in a['multi_rhs_info']),
                'independent_gmres_failure_count':sum(v!=0 for v in a['sample_independent_info']),'step_wall_seconds':elapsed}
            append_node(h,next_step,S,cum,mu,top,c,ctx.reference)
            for k in INTERVALS:h[k].append(interval[k])
            x=y;step=next_step;guard.step_costs.append(elapsed);status['completed_step']=step
            with (out/'step_audits.jsonl').open('a') as f:
                f.write(json.dumps({'step':step,'detector_audit':a,'cumulative_closure':h['probability_closure'][-1]},sort_keys=True,allow_nan=False)+'\n')
            if step%c['gate']['checkpoint_stride']==0 or step==target:checkpoint('periodic' if step!=target else 'requested_endpoint')
            if step<=5 or step%c['gate']['progress_stride']==0 or step==target:
                write_json(out/'run_status.json',status)
                print(f'[{label}] step={step} t={step*dt:.6f} rank=1 S={S:.12e} click_sum={cum:.12e} closure={h["probability_closure"][-1]:.3e} gmres={a["maximum_multi_rhs_true_residual"]:.3e} wall={elapsed:.3f}s',flush=True)
        status['status']='completed';rc=0
    except ControlledStop as ex:
        status.update(status='clean_nonaccepting_stop',classification=ex.classification,detail=ex.detail)
        try:
            require(ctx is not None and x is not None,'Stop before state initialization');checkpoint('clean_resource_stop');rc=2
        except Exception as failure:
            status.update(status='failed',checkpoint_error=str(failure),traceback=traceback.format_exc());rc=1
    except Exception as ex:
        status.update(status='failed',error=str(ex),traceback=traceback.format_exc());rc=1
        print(status['traceback'],flush=True)
    finally:
        guard.restore_signals();status.update(completed_step=step,finished_utc=utc(),elapsed_seconds=time.perf_counter()-started)
        write_json(out/'run_status.json',status);write_json(out/'checkpoint_index.json',checkpoints)
        write_json(out/'resource_guard_records.json',guard.records)
    return rc

def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--parent-checkpoint',type=Path);p.add_argument('--smoke-end-step',type=int);a=p.parse_args();c=config()
    require(os.environ.get('SLURM_JOB_ID','').isdecimal(),'Run production only in an allocated PC2 job')
    require(os.environ.get('SLURM_JOB_PARTITION')==c['hardware']['partition'],'Wrong Slurm partition')
    require(a.project_root.resolve()==Path(c['project_root']),'Wrong project root')
    if a.smoke_end_step is not None:
        require(os.environ.get('TASK09_LAMBDA0_SMOKE')=='1' and 1<=a.smoke_end_step<=8,'Unapproved smoke endpoint')
    return run_session(a.output_dir,c,a.parent_checkpoint,a.smoke_end_step,'cupy')
if __name__=='__main__':raise SystemExit(main())
