"""Read-only native checkpoint gate for the pinned parent and isolated trial states."""
from pathlib import Path
import math
import pcommon as q

def verify_checkpoint(checkpoint,cfg,trace_factors=True):
 import numpy as np
 from audit_pi800 import audit_histories
 from fresh_inputs import scientific_identity
 from memory_components import block_trace_npy
 supplied=Path(checkpoint);q.need(not supplied.is_symlink(),'Symlinked checkpoint rejected')
 cp=supplied.resolve();external=cp==q.PARENT.resolve()
 if not external:
  job=__import__('os').environ.get('SLURM_JOB_ID','UNSET');role=cfg['bounded_scope']['role']
  expected=q.P/'work'/('bridge' if role!='production' else 'sessions')/('job_'+job)
  if role!='production':expected=expected/role
  q.need(cp.parent==expected and (cp.name.startswith('checkpoint_step') or cp.name.startswith('.checkpoint_step')),'Checkpoint outside this allocation and role')
 q.need(cp.is_dir() and not cp.is_symlink(),'Missing or symlinked checkpoint')
 q.need((cp/'checkpoint_manifest.json').is_file() and not (cp/'checkpoint_manifest.json').is_symlink(),'Missing or symlinked manifest')
 mf=q.read(cp/'checkpoint_manifest.json');expected={f'sector_{k}.npy' for k in range(7)}|{'zero_state.npy','histories.npz','checkpoint_metadata.json'}
 q.need(set(mf['files'])==expected,'Checkpoint payload set')
 if external:q.need(q.sha(cp/'checkpoint_manifest.json')==q.Q['parent_pins']['checkpoint_manifest.json'],'Parent manifest changed')
 for name,want in mf['files'].items():
  f=cp/name;q.need(f.is_file() and not f.is_symlink() and q.sha(f)==want,'Checkpoint payload hash: '+name)
 m=q.read(cp/'checkpoint_metadata.json');step=7600 if external else int(m['completed_step'])
 q.need(external or (7600<=step<=cfg['gate']['end_step']<=q.Q['end_step']),'Checkpoint horizon')
 if not external:q.need(cp.name in (f'checkpoint_step{step}',f'.checkpoint_step{step}.tmp'),'Checkpoint directory step')
 q.need(m['schema']=='task09-pi800-fromzero-checkpoint-v1' and m['completed_step']==step and m['physical_time']==step*cfg['physical']['dt'],'Checkpoint grid')
 q.need(m['scientific_identity']==scientific_identity(cfg) and m['driver_sha256']==q.Q['base_driver_sha256'],'Model/driver identity')
 q.need(m['reserve_policy']==cfg['policy'] and m['zero_reference_solver']==cfg['zero_solver'],'Checkpoint policy or zero solver changed')
 if not external:
  origin=cp.parent/'origin.json';q.need(origin.is_file() and not origin.is_symlink(),'Missing trial origin')
  o=q.read(origin)
  q.need(m['package_name']==q.Q['package_name'] and m['session_start_step']==7600,'Wrong trial package/start')
  q.need(m['origin_record']==o and m['origin_record_sha256']==q.sha(origin),'Trial origin mismatch')
  q.need(o['bounded_continuation'] is True and o['role']==cfg['bounded_scope']['role'] and o['production_authorized'] is False and o['adapter_manifest_sha256']==q.sha(q.P/'SHA256SUMS.txt') and o['origin_sha256']==q.Q['parent_pins']['checkpoint_manifest.json'] and o['checkpoint']==str(q.PARENT),'Unpinned qualification origin')
 q.need(m['rate_lambda']==cfg['physical']['rate_lambda'] and m['max_event_sector']==6 and m['trace_restoration_applied'] is False and m['future_borrowing'] is False,'Checkpoint physics or ledger policy')
 with np.load(cp/'histories.npz',allow_pickle=False) as f:h={k:f[k] for k in f.files}
 with np.load(q.P/'PARENT7600/histories.npz',allow_pickle=False) as f:old={k:f[k] for k in f.files}
 ha=audit_histories(h,cfg,step)
 for k in old:q.need(h[k][:len(old[k])].tobytes()==old[k].tobytes(),'Inherited history changed: '+k)
 anchor=q.read(q.P/'PARENT7600/checkpoint_metadata.json');rep=m['forward_representation_terms'];ev=m['forward_event_terms']
 q.need(len(rep)==2*step and len(ev)==step and all(math.isfinite(v) and v>=0 for v in rep+ev),'Invalid ordered ledger')
 q.need(rep[:15200]==anchor['forward_representation_terms'] and ev[:7600]==anchor['forward_event_terms'],'Inherited terms changed')
 q.need(math.fsum(rep)==m['representation_ledger']==float(h['representation_ledger'][-1]),'Representation ledger mismatch')
 q.need(math.fsum(ev)==m['event_first_crossing_ledger']==float(h['event_first_crossing_ledger'][-1]),'Event ledger mismatch')
 for i in range(step):q.need(math.fsum(rep[2*i:2*i+2])==float(h['representation_increment'][i]) and ev[i]==float(h['event_increment'][i]),'Step ledger mismatch')
 for key,hkey in [('cumulative_click','cumulative_positive_click'),('cumulative_zero_click','cumulative_zero_click'),('cumulative_overflow_bound','cumulative_overflow_bound')]:q.need(m[key]==float(h[hkey][-1]),key)
 q.need(m['previous_overflow_intensity']==cfg['physical']['rate_lambda']*(cfg['physical']['n_shell']+2.)*float(h['top_shell_population'][-1]),'Overflow anchor')
 q.need(m['sector_ranks']==list(map(int,h['sector_ranks'][-1])) and m['total_rank']==int(h['total_rank'][-1]),'Rank metadata')
 for k in range(8):
  name=f'sector_{k}.npy' if k<7 else 'zero_state.npy';a=np.load(cp/name,mmap_mode='r',allow_pickle=False)
  rank=int(h['sector_ranks'][-1,k]) if k<7 else 1
  q.need(a.dtype==np.complex128 and a.shape==(cfg['physical']['dimension'],rank),'Factor shape/type '+name);del a
  if trace_factors:
   tr=block_trace_npy(cp/name,cfg['physical']['h_z']);want=float(h['sector_traces'][-1,k]) if k<7 else float(h['zero_survival'][-1])
   q.need(tr['finite'] and abs(tr['trace']-want)<=5e-12,'Factor finite/trace '+name)
 return m,h,{'passed':True,'step':step,'manifest_sha256':q.sha(cp/'checkpoint_manifest.json'),'factor_hashes_checked':True,'factor_traces_checked':trace_factors,'history_audit':ha,'trial_only':not external and cfg['bounded_scope']['role']!='production','trial_restart_authorized':False,'bounded_checkpoint':not external and cfg['bounded_scope']['role']=='production'}

def read_inputs(root,cfg,parent_checkpoint=None,trace_factors=True):
 import numpy as np
 from fresh_inputs import static_check
 q.need(Path(root).resolve()==q.ROOT and Path(parent_checkpoint).resolve()==q.PARENT,'Only the pinned checkpoint7600 may seed a qualification')
 q.parent_metadata();identity=static_check(q.BASE,cfg)
 m,h,a=verify_checkpoint(q.PARENT,cfg,True)
 q.need(m['total_rank']==2565,'Unexpected parent rank')
 ref=q.BASE/cfg['zero_reference']['file'];q.need(q.sha(ref)==cfg['zero_reference']['sha256'],'Historical zero reference changed')
 with np.load(ref,allow_pickle=False) as f:zero={k:f[k] for k in f.files}
 cfg['start'].update(step=7600,ranks=list(map(int,h['sector_ranks'][-1])),inherited_internal_memory_peak_mib=0.)
 report={'passed':True,'origin':'same_rate_verified_checkpoint','origin_sha256':q.sha(q.PARENT/'checkpoint_manifest.json'),'checkpoint':str(q.PARENT),'checkpoint_audit':a,'no_other_rate_state_imported':True,'bounded_continuation':True,'role':cfg['bounded_scope']['role'],'adapter_manifest_sha256':q.sha(q.P/'SHA256SUMS.txt'),'production_authorized':False}
 return {'runtime':q.BASE/'RUNTIME_SOURCES','checkpoint':q.PARENT,'metadata':m,'histories':h,'inherited_representation_terms':m['forward_representation_terms'],'inherited_event_terms':m['forward_event_terms'],'zero_reference_histories':zero,'report':report,'source_equivalence_record':identity}
