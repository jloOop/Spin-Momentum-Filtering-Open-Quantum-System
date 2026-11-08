"""Two same-parent repeatability trials; reload original7600 for bounded production."""
import argparse,copy,os,sys,subprocess
import pcommon as q

def prepare():
 from verify import verify
 verify();q.need(q.P==q.ROOT/q.Q['package_name'],'Wrong installation')
 q.check_dependency();q.parent_metadata();q.qualification_evidence();q.base_imports()
 from pc2_runtime import verify_overlay
 verify_overlay()
 from zero_extension import verify_extension
 from common import config
 z=verify_extension(config());q.need(len(z['zero_survival'])==12001,'Zero benchmark coverage')
 q.need(q.sha(q.BASE/'PREPARED/zero_reference_7200_to12000.npz')=='51574ec148fe582a6f028a123e51d904cdb3081f07ae013f91ef4ab56c6400e8','Zero extension pin')

def execute(role):
 prepare();cfg=q.make_config(role);job=os.environ.get('SLURM_JOB_ID','');q.need(job.isdecimal(),'Allocated H100 required')
 import block_driver as driver,checkpoints,fresh_inputs
 from resources import ResourceGuard
 from common import ControlledStop
 from checkpoint_gate import read_inputs,verify_checkpoint
 from lifetime_patch import install
 trial=role!='production';out=q.P/'work'/('bridge' if trial else 'sessions')/('job_'+job)
 if trial:out=out/role
 q.need(not out.exists(),'Output collision');holder={};call=[0];samples=[]
 def snapshot(label,backend,release):
  q.need('memory' in holder,'Missing high-water collector');backend.synchronize();cp=backend._cp
  prefix='kl2_call'+str(2*q.Q['start_step']+call[0])+'_'+label
  before=driver.mem.memory_snapshot(prefix+'_before',cp);holder['memory'].append(before);samples.append(before)
  if before['driver_used_bytes']/2**20>q.Q['measured_gpu_limit_mib']:raise ControlledStop('KL2_MEASURED_MEMORY_GUARD',before)
  if release:
   cp.get_default_memory_pool().free_all_blocks();backend.synchronize();after=driver.mem.memory_snapshot(prefix+'_after',cp)
   holder['memory'].append(after);samples.append(after)
   q.need(before['pool_used_bytes']==after['pool_used_bytes'] and after['pool_used_bytes']<=after['pool_total_bytes']<=before['pool_total_bytes'],'Pool invariant')
 controller0=driver.Controller
 def controller(**kw):holder['memory']=kw['memory'];return controller0(**kw)
 loader0=driver.load_module
 def loader(path,name):
  engine=loader0(path,name);install(engine,snapshot);fn=engine.bath_half_truncated
  def counted(*a,**kw):call[0]+=1;return fn(*a,**kw)
  engine.bath_half_truncated=counted;return engine
 class Guard(ResourceGuard):
  def before_step(self,step,rank):
   q.need(q.Q['start_step']<step<=cfg['gate']['end_step']<=q.Q['end_step'] and rank<=q.Q['qualification_rank_ceiling'],'Bounded resource scope')
   try:super().before_step(step,rank)
   finally:
    for r in self.records:r['gpu_prediction_scope']='KL2 bounded7650 only:34*(r+4)-1024MiB. Additional1024MiB empirical credit after112-step KL1 audit; unchanged measured88064MiB and original2600rank cap. Not continuous-peak or full-horizon proof.'
 driver.config=lambda:copy.deepcopy(cfg);driver.read_inputs=read_inputs;driver.load_module=loader;driver.Controller=controller;driver.ResourceGuard=Guard
 checkpoints.verify_checkpoint=verify_checkpoint;fresh_inputs.verify_checkpoint=verify_checkpoint
 os.environ.pop('TASK09_PI800_SMOKE',None);os.environ.pop('TASK09_PI800_BRIDGE',None)
 argv=['block_driver.py','--project-root',str(q.ROOT),'--output-dir',str(out),'--parent-checkpoint',str(q.PARENT),'--optimization-mode','buffered']
 if trial:os.environ['TASK09_PI800_BRIDGE']='1';argv+=['--probe-end-step',str(q.Q['start_step']+1)]
 sys.argv=argv;rc=1
 try:
  rc=driver.main()
  if rc in (0,2):
   from audit_pi800 import audit_session
   a=audit_session(out,cfg,True);q.need(a['passed'],'Native session audit failed')
  return rc
 finally:
  if out.exists():q.write(out/'KL2_SCOPE.json',{'role':role,'wrapper_manifest_sha256':q.sha(q.P/'SHA256SUMS.txt'),'patch_sha256':q.sha(q.P/'lifetime_patch.py'),'driver_adapter_sha256':q.sha(q.P/'block_driver.py'),'frozen_numerical_driver_sha256':q.Q['base_driver_sha256'],'parent':str(q.PARENT),'extra_memory_samples':samples,'numerical_policy_changed':False,'numerical_implementation_changed':False,'full_horizon_authorized':False,'trial_restart_authorized':False,'driver_returncode':rc})

def main():
 prepare();job=os.environ.get('SLURM_JOB_ID','');q.need(job.isdecimal(),'Allocation required')
 b=q.P/'work/bridge'/('job_'+job);q.need(not b.exists(),'Repeatability trials already attempted');b.mkdir(parents=True)
 runtime=q.P/'work/runtime'/('job_'+job)
 for role in ('trial_a','trial_b','production'):
  q.write(runtime/(role+'_admission.json'),q.live_storage())
  end=q.Q['end_step'] if role=='production' else q.Q['start_step']+1
  log=runtime/(role+'.log');print('KL2_START role='+role+' parent=7600 end='+str(end)+' LOG='+str(log),flush=True)
  with log.open('w') as f:rc=subprocess.run([sys.executable,'-B','-u',str(q.P/'run_block.py'),'--role',role],stdout=f,stderr=subprocess.STDOUT).returncode
  print('KL2_END role='+role+' rc='+str(rc),flush=True)
  if rc:return rc
  if role=='trial_b':
   from control import compare_trials
   r=compare_trials(b);q.write(b/'replay_report.json',r);print('PASS_KL2_SAME_PARENT_REPEATABILITY; ORIGINAL7600_RELOADED_FOR_BOUNDED_PRODUCTION',flush=True)
 print('KL2_BOUNDED_TARGET_FINISHED; no automatic further propagation',flush=True);return 0
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--role',choices=['trial_a','trial_b','production']);a=ap.parse_args()
 raise SystemExit(execute(a.role) if a.role else main())
