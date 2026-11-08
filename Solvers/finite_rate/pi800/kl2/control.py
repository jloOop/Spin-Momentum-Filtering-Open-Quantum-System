"""Strict same-parent repeatability gate for the unchanged qualified numerical method."""
from pathlib import Path
import os
import pcommon as q

def compare_trials(directory):
 import numpy as np
 base=Path(directory);start=q.Q['start_step'];end=start+1;roles=('trial_a','trial_b');hist={};meta={};factor_hash={};spectra={};peaks={};files={}
 filenames=[f'sector_{i}.npy' for i in range(7)]+['zero_state.npy']
 for role in roles:
  d=base/role;cp=d/f'checkpoint_step{end}';status=q.read(d/'run_status.json')
  q.need(status.get('status')=='completed' and status.get('passed') is True and status.get('start_step')==start and status.get('completed_step')==status.get('last_persisted_step')==end,'Trial incomplete')
  audit=q.read(d/'independent_audit.json');q.need(audit.get('passed') is True and audit.get('latest_checkpoint_manifest_sha256')==q.sha(cp/'checkpoint_manifest.json'),'Trial audit mismatch')
  scope=q.read(d/'KL2_SCOPE.json');q.need(scope.get('role')==role and scope.get('parent')==str(q.PARENT) and scope.get('wrapper_manifest_sha256')==q.sha(q.P/'SHA256SUMS.txt') and scope.get('patch_sha256')==q.Q['lifetime_patch_sha256'] and scope.get('driver_adapter_sha256')==q.Q['predecessor_driver_adapter_sha256'] and scope.get('driver_returncode')==0,'Trial runtime/source scope')
  mf=q.read(cp/'checkpoint_manifest.json');factor_hash[role]={}
  for n in filenames:
   f=cp/n;q.need(f.is_file() and not f.is_symlink(),'Missing/unsafe factor');hx=q.sha(f);q.need(hx==mf['files'][n],'Factor hash differs from checkpoint manifest');factor_hash[role][n]=hx
  meta[role]=q.read(cp/'checkpoint_metadata.json')
  with np.load(d/'block_histories.npz',allow_pickle=False) as a:hist[role]={k:a[k].copy() for k in a.files}
  with np.load(q.P/'PARENT7600/histories.npz',allow_pickle=False) as a:
   q.need(set(a.files)==set(hist[role]) and len(a.files)==27,'History fields')
   for k in a.files:
    old=a[k];v=hist[role][k];q.need(v.dtype==old.dtype and v.shape==(old.shape[0]+1,*old.shape[1:]) and np.all(np.isfinite(v)) and v[:len(old)].tobytes()==old.tobytes(),'Trial inherited history/length/finite '+k)
  spectra[role]={}
  for call,half in [(2*start+1,'first'),(2*start+2,'second')]:
   n=f'spectra/call_{call}_{half}.npz'
   with np.load(d/n,allow_pickle=False) as a:spectra[role][n]={k:a[k].copy() for k in a.files}
  memory=q.read(d/'memory_snapshots.json')['snapshots'];q.need(bool(memory),'Missing memory snapshots');peaks[role]=max(v['driver_used_bytes'] for v in memory)/2**20
  q.need(peaks[role]<=q.Q['measured_gpu_limit_mib'],'Trial memory guard')
  keep=[cp/n for n in filenames]+[d/'block_histories.npz',cp/'histories.npz',cp/'checkpoint_manifest.json',cp/'checkpoint_metadata.json',d/'run_status.json',d/'independent_audit.json',d/'KL2_SCOPE.json',d/'memory_snapshots.json']+[d/n for n in spectra[role]]
  for f in keep:q.need(f.is_file() and not f.is_symlink(),'Missing/unsafe trial evidence');files[f.relative_to(base).as_posix()]=q.sha(f)
 q.need(factor_hash[roles[0]]==factor_hash[roles[1]],'Factor bytes not identical')
 for k in hist[roles[0]]:
  if k=='step_wall_seconds':continue
  a=hist[roles[0]][k];b=hist[roles[1]][k];q.need(a.dtype==b.dtype and a.shape==b.shape and a.tobytes()==b.tobytes(),'Scientific histories differ '+k)
 for name,a in spectra[roles[0]].items():
  b=spectra[roles[1]][name];q.need(set(a)==set(b),'Spectral fields differ')
  for k in a:q.need(a[k].dtype==b[k].dtype and a[k].shape==b[k].shape and a[k].tobytes()==b[k].tobytes(),'Spectra differ '+k)
 for k in ('forward_representation_terms','forward_event_terms'):q.need(meta[roles[0]][k]==meta[roles[1]][k],'Ordered omission terms differ')
 return {'passed':True,'start_step':start,'end_step':end,'scope':'Two fresh same-parent GPU processes with identical previously qualified KL1 numerical kernels. Repeatability/admission gate, not a new performance A/B benchmark.','parent_checkpoint':str(q.PARENT),'parent_manifest_sha256':q.Q['parent_pins']['checkpoint_manifest.json'],'wrapper_manifest_sha256':q.sha(q.P/'SHA256SUMS.txt'),'replay_evidence_hashes':files,'factor_pairs':factor_hash[roles[0]],'sampled_peaks_mib':peaks,'scientific_arrays_equal':26,'both_spectra_bitwise_equal':True,'trial_states_imported_into_production':False,'full_horizon_authorized':False}

def require_replay(cfg,data):
 b=q.P/'work/bridge'/('job_'+os.environ['SLURM_JOB_ID']);p=b/'replay_report.json';q.need(p.is_file() and not p.is_symlink(),'Missing own successful repeatability report');r=q.read(p)
 q.need(r.get('passed') is True and r.get('start_step')==q.Q['start_step'] and r.get('end_step')==q.Q['start_step']+1,'Wrong replay interval')
 q.need(r.get('wrapper_manifest_sha256')==q.sha(q.P/'SHA256SUMS.txt'),'Source changed after gate')
 q.need(r.get('parent_checkpoint')==str(data['checkpoint'])==str(q.PARENT) and r.get('parent_manifest_sha256')==data['report']['origin_sha256'],'Wrong replay parent')
 q.need(r.get('scientific_arrays_equal')==26 and r.get('both_spectra_bitwise_equal') is True and r.get('trial_states_imported_into_production') is False,'Incomplete repeatability gate')
 for n,h in r['replay_evidence_hashes'].items():
  f=b/n;q.need(not Path(n).is_absolute() and '..' not in Path(n).parts and Path(n).parts[0] in ('trial_a','trial_b') and f.is_file() and not f.is_symlink() and q.sha(f)==h,'Trial evidence changed')
 q.need(len(r['replay_evidence_hashes'])==36,'Missing repeatability evidence')
 return {'passed':True,'path':str(p),'sha256':q.sha(p),'scope':r['scope'],'trial_states_imported_into_production':False}
