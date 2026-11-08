"""Pinned dependency, qualification and bounded block. No unrestricted resume."""
from pathlib import Path
import hashlib,json,copy,subprocess,sys,os,shutil,re
P=Path(__file__).resolve().parent
Q=json.loads((P/'BLOCK.json').read_text())
ROOT=Path(Q['project_root']);BASE=ROOT/Q['base_package'];PARENT=ROOT/Q['parent_checkpoint_relative']
def need(ok,message):
 if not ok:raise RuntimeError(message)
def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(path):return json.loads(Path(path).read_text())
def write(path,obj):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp')
 with tmp.open('w') as f:json.dump(obj,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(tmp,path)
def command(args,timeout=120):
 r=subprocess.run(args,text=True,capture_output=True,timeout=timeout)
 need(r.returncode==0,'Command failed: '+repr(args)+'\n'+r.stdout+r.stderr)
 return r.stdout

def check_dependency(base=None):
 base=BASE if base is None else Path(base)
 need(base.is_dir() and not base.is_symlink(),'Missing frozen installed BLF1 dependency')
 for name,pin in [('SHA256SUMS.txt','base_manifest_sha256'),('verify_release.py','base_verifier_sha256'),('pi800_run.py','base_driver_sha256')]:
  need((base/name).is_file() and not (base/name).is_symlink() and sha(base/name)==Q[pin],'BLF1 dependency pin changed: '+name)
 names=set()
 for line in (P/'DEPENDENCY_SHA256SUMS.txt').read_text().splitlines():
  digest,name=line.split('  ',1);f=base/name
  need(Path(name).is_absolute() is False and '..' not in Path(name).parts and name not in names,'Unsafe dependency manifest');names.add(name)
  need(f.is_file() and not f.is_symlink() and sha(f)==digest,'BLF1 dependency changed: '+name)
 actual={str(f.relative_to(base)) for f in base.rglob('*') if f.is_file() and f.relative_to(base).parts[0] not in ('work','PREPARED','__pycache__') and '__pycache__' not in f.parts and f.suffix!='.pyc'}
 need(actual==names|{'SHA256SUMS.txt'},'Unmanifested or missing static dependency file')
 return {'passed':True,'files_verified':len(names),'source_directory':str(base),'frozen_driver_sha256':Q['base_driver_sha256']}

def base_imports(base=None):
 base=BASE if base is None else Path(base)
 if str(base) not in sys.path:sys.path.insert(1,str(base))
 return base


def make_config(role='production'):
 need(role in ('trial_a','trial_b','production'),'Unknown bounded role')
 c=copy.deepcopy(read(BASE/'CONFIG.json'));c['package_name']=Q['package_name'];c['output_relative']=Q['package_name']+'[ARCHIVE_PATH]'
 end=Q['start_step']+1 if role!='production' else Q['end_step']
 c['gate'].update(end_step=end,rank_guard=Q['qualification_rank_ceiling'],memory_guard_mib=Q['measured_gpu_limit_mib'],predictive_gpu_fixed_mib=Q['forecast_fixed_mib'],predictive_gpu_mib_per_rank=Q['forecast_mib_per_rank'],predictive_gpu_rank_increment_allowance=Q['forecast_rank_allowance'],minimum_free_disk_gib=Q['minimum_free_gib'],slurm_wall_seconds=Q['wall_seconds'],wall_guard_seconds=Q['wall_guard_seconds'],checkpoint_stride=Q['checkpoint_stride'])
 c['start'].update(step=Q['start_step'],ranks=read(P/'PARENT7600/checkpoint_metadata.json')['sector_ranks'],inherited_internal_memory_peak_mib=0.)
 c['bounded_scope']={'role':role,'end_step':end,'no_auto_resume':True,'full_horizon_authorized':False,'numerical_policy_changed':False,'resource_policy':Q['acknowledgement']}
 c['claim_boundary']='Bounded nonaccepting unchanged-KL1 continuation from original7600 after two one-step repeatability trials. Trial states not adopted; no full-t6 feasibility or physical acceptance.'
 return c

def parent_paths():
 session=PARENT.parent;pp=ROOT/Q['parent_package']
 paths={n:PARENT/n for n in ('checkpoint_manifest.json','checkpoint_metadata.json','histories.npz')}
 paths.update({n:session/n for n in ('run_status.json','independent_audit.json','summary_report.json','KL1_SCOPE.json')})
 paths['bootstrap_status.json']=pp/'work/runtime'/('job_'+Q['parent_job'])/'bootstrap_status.json'
 return paths

def validate_parent_records(status,audit,boot,scope,manifest):
 need(status.get('status')=='completed' and status.get('passed') is True and status.get('classification')=='COMPLETED_REQUESTED_PI800_GRID_PREFIX_NOT_PHYSICAL_ACCEPTANCE','Parent is not a completed nonaccepting production block')
 need(status.get('completed_step')==status.get('last_persisted_step')==Q['start_step'],'Parent endpoint not fully persisted')
 need(status.get('start_step')==7488 and status.get('target_step')==7600,'Unexpected ancestor interval')
 need(audit.get('passed') is True and audit.get('latest_checkpoint_manifest_sha256')==Q['parent_pins']['checkpoint_manifest.json'],'Parent audit mismatch')
 need(audit.get('checkpoint_audit',{}).get('trial_only') is False and audit['checkpoint_audit'].get('step')==7600,'Parent is a trial or wrong checkpoint')
 need(boot.get('job_id')==Q['parent_job'] and boot.get('returncode')==0 and boot.get('stage')=='bounded_finished','Parent batch did not finalize successfully')
 need(scope.get('role')=='production' and scope.get('driver_returncode')==0 and scope.get('wrapper_manifest_sha256')==Q['predecessor_release_sha256'],'Wrong parent runtime scope')
 need(scope.get('patch_sha256')==Q['lifetime_patch_sha256'] and scope.get('driver_adapter_sha256')==Q['predecessor_driver_adapter_sha256'],'Unqualified parent kernel')
 need(manifest==read(P/'PARENT7600/checkpoint_manifest.json'),'Parent checkpoint manifest changed')

def parent_metadata():
 paths=parent_paths()
 for n,p in paths.items():need(p.is_file() and not p.is_symlink() and sha(p)==Q['parent_pins'][n],'Parent evidence changed/missing: '+str(p))
 validate_parent_records(read(paths['run_status.json']),read(paths['independent_audit.json']),read(paths['bootstrap_status.json']),read(paths['KL1_SCOPE.json']),read(paths['checkpoint_manifest.json']))
 for name in read(paths['checkpoint_manifest.json'])['files']:need((PARENT/name).is_file() and not (PARENT/name).is_symlink(),'Missing checkpoint payload: '+name)
 return {'passed':True,'parent':str(PARENT),'step':Q['start_step'],'factor_bytes_checked':False,'scope':'Metadata and existence only; full factor bytes checked inside allocation.'}

def live_storage():
 base_imports();from storage_check import parse_quota
 quota=parse_quota(command(['pc2status'],60));fs=shutil.disk_usage(ROOT).free;req=Q['minimum_free_gib']*2**30
 need(min(fs,quota['remaining_bytes'])>=req,'Need '+str(Q['minimum_free_gib'])+' GiB live filesystem AND quota headroom; no data are deleted')
 return {'filesystem_free_bytes':fs,'quota':quota,'required_gib':Q['minimum_free_gib'],'parent_factors_copied':False,'conservative_bound_gib':Q['storage_bound_gib']}

def qualification_evidence():
 """Immediate parent is the completed, previously qualified KL1 production block."""
 import zipfile
 dep=ROOT/Q['parent_package'];listing=dep/'SHA256SUMS.txt'
 need(listing.is_file() and not listing.is_symlink() and sha(listing)==Q['predecessor_release_sha256'],'Parent release pin')
 need(listing.read_bytes()==(P/'ANCESTRY/KL1_SHA256SUMS.txt').read_bytes(),'Parent release listing differs')
 names=set()
 for line in listing.read_text().splitlines():
  digest,name=line.split('  ',1);f=dep/name
  need(not Path(name).is_absolute() and '..' not in Path(name).parts and name not in names and f.is_file() and not f.is_symlink() and sha(f)==digest,'Parent source changed: '+name);names.add(name)
 actual={str(f.relative_to(dep)) for f in dep.rglob('*') if f.is_file() and f.relative_to(dep).parts[0] not in ('work','__pycache__') and '__pycache__' not in f.parts and f.suffix!='.pyc'}
 need(actual==names|{'SHA256SUMS.txt'},'Unmanifested parent source')
 need(sha(P/'block_driver.py')==sha(dep/'block_driver.py')==Q['predecessor_driver_adapter_sha256'],'Numerical driver changed')
 need(sha(P/'lifetime_patch.py')==sha(dep/'lifetime_patch.py')==Q['lifetime_patch_sha256'],'Lifetime patch changed')
 result=dep/'work/results'/('Task09_Pi800_KL1_Result_'+Q['parent_job']+'.zip')
 need(result.is_file() and not result.is_symlink() and sha(result)==Q['input_result_sha256'],'Completed parent Result missing/changed')
 with zipfile.ZipFile(result) as z:
  need(z.read('RESULT_MANIFEST.json')==(P/'ANCESTRY/KL1_RESULT_MANIFEST.json').read_bytes(),'Parent Result manifest changed')
  mf=json.loads(z.read('RESULT_MANIFEST.json'));need(mf['wrapper_returncode']==0 and mf['job_id']==Q['parent_job'],'Wrong/failed parent Result')
 return {'passed':True,'job':Q['parent_job'],'result_sha256':Q['input_result_sha256'],'release_manifest_sha256':sha(listing),'checkpoint_manifest_sha256':Q['parent_pins']['checkpoint_manifest.json'],'qualified_numerical_driver_unchanged':True,'trial_states_not_imported':True}
