#!/usr/bin/env python3
"""Independent, read-only audit of the uploaded job3463660 result.
No solver/auditor imports or execution, network, GPU, or state-factor reconstruction.
Usage: python audit_result.py --source-dir /path/to/uploads --output /new/folder
"""
from __future__ import annotations
import argparse, collections, csv, hashlib, io, json, math, re, stat, time, zipfile
from decimal import Decimal, localcontext
from pathlib import Path, PurePosixPath
import numpy as np

STEM='Task09_Pi1600_S19327_To1000_PC2_H100_v1_IO200_Result_3463660'
EXPECTED={STEM+'.zip':'a448831dcef3c4f49675cee51a02a80af554df5d8a1bc765cec0f0124434a537',
 STEM+'_evidence.md':'91aebf6b1aa937b73834e37b78403dde938f92f94dd45b53a2c71046d5f79d02',
 STEM+'.SHA256SUMS.txt':'9396daa1cf1c41266db376123d4ffd3c076b3c64351dc13279778be8f2cb290b'}
KEYS=set('''times positive_survival zero_survival cumulative_positive_click cumulative_zero_click representation_ledger representation_ceiling event_first_crossing_ledger cumulative_overflow_bound total_rank sector_traces sector_ranks analytic_event_tail_bound top_shell_population positive_step_click zero_step_click gmres_max_residual batch_sample_relative_error complete_step_ledger_closure zero_step_closure step_wall_seconds representation_increment event_increment detector_number_rhs detector_number_batches detector_maximum_actual_batch_columns detector_batch64_contract_passed'''.split())
COUNTS=collections.Counter()
def require(ok,msg,kind='assertions'):
 if not bool(ok):raise AssertionError(msg)
 COUNTS[kind]+=1

def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def js(b):return json.loads(b)
def save_json(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True,allow_nan=False)+'\n')
def npz(b):
 with np.load(io.BytesIO(b),allow_pickle=False) as a:return {k:a[k] for k in a.files}
def safe_zip(z):
 names=z.namelist(); require(len(names)==len(set(names)),'Duplicate ZIP paths')
 for i in z.infolist():
  p=PurePosixPath(i.filename)
  require(not p.is_absolute() and '..' not in p.parts and '\\' not in i.filename and '\x00' not in i.filename and not stat.S_ISLNK(i.external_attr>>16) and not i.flag_bits&1,'Unsafe/encrypted member '+i.filename,'safe_members')

def fsum_prefix(values,anchor=0.):
 """Independent nonoverlapping partial expansion, rounded with math.fsum at each prefix."""
 partials=[]; out=[float(anchor)]
 if anchor:partials.append(float(anchor))
 for value in values:
  x=float(value); new=[]
  for y in partials:
   if abs(x)<abs(y):x,y=y,x
   hi=x+y;lo=y-(hi-x)
   if lo:new.append(lo)
   x=hi
  new.append(x);partials=new
  out.append(math.fsum(partials))
 return np.asarray(out,dtype=np.float64)

def policy_line(call,cfg):
 p=cfg['policy'];basecall=p['start_call']-1
 with localcontext() as c:
  c.prec=60;b=Decimal(p['start_ledger_decimal']);e=Decimal(p['final_ceiling_decimal'])
  return float(b+(e-b)*Decimal(int(call)-basecall)/Decimal(p['end_call']-basecall))

def equal_prefix(old,new,label):
 require(set(old)==set(new),label+' keyset')
 for k,v in old.items():
  require(v.dtype==new[k].dtype and v.shape[1:]==new[k].shape[1:] and v.tobytes()==np.ascontiguousarray(new[k][:len(v)]).tobytes(),label+'/'+k,'array_prefixes')

def main():
 pa=argparse.ArgumentParser(description=__doc__);pa.add_argument('--source-dir',type=Path,required=True);pa.add_argument('--output',type=Path,required=True);args=pa.parse_args()
 src=args.source_dir; out=args.output;out.mkdir(parents=True,exist_ok=True)
 require(not (out/'VERIFICATION.json').exists(),'Refusing existing completed verification')
 t0=time.monotonic(); external=[]
 for name,expected in EXPECTED.items():
  p=src/name;require(p.is_file(),'Missing '+name);actual=file_sha(p);require(actual==expected,'External hash '+name,'external_hashes');external.append({'name':name,'bytes':p.stat().st_size,'sha256':actual})
 side=(src/(STEM+'.SHA256SUMS.txt')).read_text().splitlines()
 require({line.split(None,1)[1]:line.split(None,1)[0] for line in side if line.strip()}=={k:v for k,v in EXPECTED.items() if not k.endswith('SHA256SUMS.txt')},'Sidecar contents')
 z=zipfile.ZipFile(src/(STEM+'.zip'));safe_zip(z);root=STEM+'/'
 require(all(i.filename.startswith(root) for i in z.infolist()),'ZIP root')
 available={i.filename[len(root):]:i for i in z.infolist() if not i.is_dir()}
 read=lambda p:z.read(root+p)
 doc=lambda p:js(read(p))
 manifest=doc('artifact_hashes.json')['files']
 require(set(manifest)==set(available)-{'artifact_hashes.json'},'Exact manifest coverage')
 hashes={}; inventory=[]
 for rel,i in available.items():
  h=hashlib.sha256()
  with z.open(i) as f:
   for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
  actual=h.hexdigest();hashes[rel]=actual
  if rel!='artifact_hashes.json':require(actual==manifest[rel],'Artifact hash '+rel,'artifact_hashes')
  inventory.append({'member':rel,'bytes':i.file_size,'compressed_bytes':i.compress_size,'sha256':actual})
 with (out/'archive_members.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(inventory[0]));w.writeheader();w.writerows(inventory)
 for line in read('PACKAGE/SHA256SUMS.txt').decode().splitlines():
  if not line.strip():continue
  h,rel=line.split(None,1);require(hashes['PACKAGE/'+rel]==h,'Package SHA '+rel,'package_checksums')
 print('HASHES',COUNTS['artifact_hashes'],COUNTS['package_checksums'],flush=True)
 cfg=doc('PACKAGE/CONFIG.json');status=doc('OUTPUT/run_status.json');audit=doc('OUTPUT/independent_audit_report.json');meta=doc('OUTPUT/checkpoint_step20000/checkpoint_metadata.json');parent_meta=doc('PACKAGE/PARENT_RESULT/checkpoint_metadata.json')
 phys=cfg['physical'];require(phys['rate_lambda']==math.pi/1600 and phys['dt']==.0005 and phys['omega']==100 and phys['n_shell']==12 and phys['n_z']==1500 and phys['dimension']==273000 and phys['max_event_sector']==4,'Physical identity')
 require(status['completed_step']==status['last_persisted_step']==status['target_step']==20000 and status['start_step']==19327 and status['status']=='completed' and status['passed'] is True,'Completion identity')
 for k in ['automatic_resume','physical_claim','production_authorized','task10_eligible']:require(status[k] is False,'Claim flag '+k)
 require(audit['passed'] is True and audit['physical_acceptance'] is False and audit['reconstructed_calls']==1346 and audit['reconstructed_committed_steps']==673,'Recorded audit scope')
 wrapper=doc('RUNTIME/wrapper_status.json');port=doc('RUNTIME/pc2_port_audit.json');require(str(wrapper['job_id'])=='3463660' and all(wrapper[k]==0 for k in ['preflight_return_code','solver_return_code','independent_audit_return_code']),'Wrapper status');require(port['passed'] is True and str(port['job_id'])=='3463660' and port['last_persisted_step']==20000 and port['numerical_audit_sha256']==hashes['OUTPUT/independent_audit_report.json'],'Port audit crosshash')
 h=npz(read('OUTPUT/block_histories.npz'));parent=npz(read('PACKAGE/PARENT_RESULT/histories.npz'))
 require(set(h)==KEYS and h['times'].shape==(20001,) and np.array_equal(h['times'],np.arange(20001)*.0005),'Native schema/grid')
 require(h['positive_step_click'].shape==(20000,) and h['zero_step_click'].shape==(20000,),'Interval grids')
 array_inventory=[]
 for k,a in h.items():
  require(a.dtype.kind in 'iufb' and np.all(np.isfinite(a)) and len(a) in [20000,20001],'Finite native '+k,'native_array_validity')
  array_inventory.append({'name':k,'shape':list(a.shape),'dtype':str(a.dtype),'c_order_sha256':sha(a.tobytes())})
 require(h['sector_ranks'].shape==h['sector_traces'].shape==(20001,5),'Sector dimensions')
 require(np.array_equal(h['total_rank'],np.sum(h['sector_ranks'],axis=1)),'Rank sums');require(np.max(np.abs(np.sum(h['sector_traces'],axis=1)-h['positive_survival']))<5e-15,'Trace sums')
 equal_prefix(parent,h,'embedded_step19327')
 require(hashes['PACKAGE/PARENT_RESULT/histories.npz']==cfg['checkpoint_payloads']['histories.npz'],'Pinned parent history')
 require(hashes['PACKAGE/PARENT_RESULT/checkpoint_metadata.json']==cfg['checkpoint_payloads']['checkpoint_metadata.json'],'Pinned parent metadata')
 pb=read('PACKAGE/'+cfg['parent_result']['embedded_file']);require(sha(pb)==cfg['parent_result']['sha256'],'Embedded parent ZIP pin')
 pz=zipfile.ZipFile(io.BytesIO(pb));safe_zip(pz);pm=js(pz.read('MANIFEST.json'))['files'];require(set(pm)==set(pz.namelist())-{'MANIFEST.json'},'Parent manifest coverage')
 for rel,expected in pm.items():require(sha(pz.read(rel))==expected,'Parent manifest '+rel,'parent_compact_hashes')
 for rel,expected in cfg['parent_result']['pinned_members'].items():require(sha(pz.read(rel))==expected,'Parent original subset '+rel,'parent_pinned_hashes')
 require(pz.read('original/OUTPUT/block_histories.npz')==read('PACKAGE/PARENT_RESULT/histories.npz'),'Parent compact/native byte identity')
 pcfg=js(pz.read('original/PACKAGE/CONFIG.json'))
 require(cfg['policy']==pcfg['policy']==meta['reserve_policy']==parent_meta['reserve_policy'],'Global policy unchanged')
 numerical_files=['pi1600_continue.py','memory_components.py','spectral_components.py','pool_control.py','checkpoints.py']
 for rel in numerical_files:require(read('PACKAGE/'+rel)==pz.read('original/PACKAGE/'+rel),'Numerical source vs parent '+rel,'parent_source_identity')
 extra_prefixes=[]
 for filename,step,member,expected in [
 ('Task09_Pi1600_2894739_Compact_Core_v1.zip',12000,'original/OUTPUT/block_histories.npz','20099017eece2749edfa705862335b69eefe13c33f0ec661b95a05ef326fc396'),
 ('Task09_Pi1600_2868412_Compact_Core(3).zip',7200,'original/OUTPUT/block_histories.npz',None)]:
  p=src/filename
  if not p.exists():continue
  digest=file_sha(p)
  if expected:require(digest==expected,'Earlier compact outer hash')
  with zipfile.ZipFile(p) as ez:
   eh=npz(ez.read(member));require(len(eh['times'])==step+1,'Earlier endpoint');equal_prefix(eh,h,filename)
  extra_prefixes.append({'file':filename,'sha256':digest,'step':step,'arrays_bitwise_equal':27,'outer_hash_pinned':bool(expected)})
 p=src/'New Folder With Items.zip'
 if p.exists():
  with zipfile.ZipFile(p) as ez:
   nm=[x for x in ez.namelist() if x.endswith('.zip') and not x.startswith('__MACOSX/')];require(len(nm)==1,'Snapshot member selection');sb=ez.read(nm[0]);require(sha(sb)=='495dcd2d9c1e8181d7b3e99c50326c951aee040bb8939264150ee0baaf0e2806','Snapshot pinned SHA')
   with zipfile.ZipFile(io.BytesIO(sb)) as sz:
    sh=npz(sz.read('original/checkpoint_step16600/histories.npz'));equal_prefix(sh,h,'snapshot16600')
  extra_prefixes.append({'file':nm[0],'sha256':sha(sb),'step':16600,'arrays_bitwise_equal':27,'outer_hash_pinned':True})
 base=src/'Task09_Pi1600_12000_To20000_PC2_H100_2026-09-12_v1_IO200.zip'
 if base.exists():
  require(file_sha(base)=='db41919ccee585fd486d7d8627f150e426dc822afd334467b09f1d74aef7a8d4','Base IO200 pin')
  with zipfile.ZipFile(base) as bz:
   br=bz.namelist()[0].split('/')[0]+'/'
   for rel in numerical_files:require(read('PACKAGE/'+rel)==bz.read(br+rel),'Base IO200 core unchanged '+rel,'base_source_identity')
 legacy=cfg['legacy'];rep=meta['forward_representation_terms'];ev=meta['forward_event_terms'];require(len(rep)==29008 and len(ev)==14504,'Final ordered term lengths')
 require(rep[:27662]==parent_meta['forward_representation_terms'] and ev[:13831]==parent_meta['forward_event_terms'],'All inherited ordered terms unchanged')
 require(meta['legacy_prefix_origin']==legacy and parent_meta['legacy_prefix_origin']==legacy,'Legacy anchor identity')
 require(all(v>=0 and math.isfinite(v) for v in rep+ev),'Valid nonnegative charges')
 reps=fsum_prefix(rep,legacy['representation_ledger']);evs=fsum_prefix(ev,legacy['event_ledger'])
 # Direct fsum cross-check every full-step ledger as well as independent streaming expansion.
 for i in range(1,14505):
  s=5496+i
  require(math.fsum([legacy['representation_ledger'],*rep[:2*i]])==reps[2*i]==float(h['representation_ledger'][s]),'Representation ledger state '+str(s),'rep_state_reconstructions')
  require(math.fsum([legacy['event_ledger'],*ev[:i]])==evs[i]==float(h['event_first_crossing_ledger'][s]),'Event ledger state '+str(s),'event_state_reconstructions')
 require(float(h['representation_ledger'][-1])==meta['representation_ledger'] and float(h['event_first_crossing_ledger'][-1])==meta['event_first_crossing_ledger'],'Metadata ledgers')
 for s in range(12001,20001):require(float(h['representation_ledger'][s])<=policy_line(2*s,cfg),'Global line at state '+str(s),'post600_node_allowances')
 decisions=doc('OUTPUT/rank_decisions.json')['records'];compression=doc('OUTPUT/compression_records.json')['records'];steps=doc('OUTPUT/block_step_records.json')['records'];require([r['call_index'] for r in decisions]==list(range(38655,40001)),'Decision sequence');require([s['step'] for s in steps]==list(range(19328,20001)),'Step sequence')
 require(len(compression)==1346,'Compression record count')
 spectrum_table=[];negative_total=0.;ladder_entries=0
 for rr,cr in zip(decisions,compression):
  call=rr['call_index'];s=(call+1)//2;which='first' if call%2 else 'second';a=npz(read('OUTPUT/'+rr['spectrum_file']))
  require(rr['step']==s and rr['half']==which and cr['call_index']==call,'Compression indices','spectrum_checks')
  entries=[];neg=0.;rawrank=0
  for k in range(5):
   raw=a[f'sector_{k}_raw_eigenvalues_ascending'];positive=a[f'sector_{k}_positive_eigenvalues_ascending'];rawrank+=len(raw)
   require(raw.dtype==np.float64 and np.all(np.isfinite(raw)) and np.all(np.diff(raw)>=0),'Raw spectral order','spectrum_checks');require(np.array_equal(positive,np.maximum(raw,0.)),'Clipped raw spectrum','spectrum_checks')
   neg+=float(np.sum(np.maximum(-raw,0.),dtype=np.float64))
   entries.extend((float(v),k,i) for i,v in enumerate(positive) if v>0)
  entries.sort();values=np.asarray([v for v,k,i in entries]);sec=np.asarray([k for v,k,i in entries],np.int32);idx=np.asarray([i for v,k,i in entries],np.int32)
  require(np.array_equal(values,a['global_positive_eigenvalues_ascending']) and np.array_equal(sec,a['global_positive_eigenvalue_sectors']) and np.array_equal(idx,a['global_positive_eigenvalue_local_indices']),'Full spectral merge','spectrum_checks')
  cumulative=fsum_prefix(values);ladder=cumulative[::-1];line=policy_line(call,cfg);prior=reps[call-10992-1];allow=line-prior
  require(np.array_equal(a['global_positive_cumulative_ascending'],cumulative[1:]),'Every cumulative spectral cutoff','full_spectral_ladders')
  require(np.array_equal(a['minimum_positive_trace_discard_by_target_rank'],ladder) and np.array_equal(a['target_total_ranks'],np.arange(len(values)+1)),'Every rank/discard ladder','spectrum_checks')
  mask=ladder<=allow;minimum=int(np.flatnonzero(mask)[0]);delta=math.fsum(values[:len(values)-minimum].tolist())
  require(np.array_equal(a['target_rank_admissible_under_current_ceiling'],mask.astype(np.int8)),'Every admissibility mask','spectrum_checks')
  require(minimum==rr['minimum_admissible_rank']==rr['selected_rank']==int(a['minimum_admissible_rank'][0])==cr['rank_after'],'Minimum rank','spectrum_checks')
  require(delta==ladder[minimum]==rr['selected_discard']==cr['spectral_positive_discard']==rep[call-10992-1],'Charge from spectrum','spectrum_checks')
  allocation={str(k):int(np.count_nonzero(sec[len(values)-minimum:]==k)) for k in range(5)}
  require(allocation==rr['allocation']==cr['sector_ranks_after'],'All sector allocations','spectrum_checks')
  require(float(a['ledger_before'][0])==rr['ledger_before']==cr['ledger_before']==prior and float(a['ceiling'][0])==rr['reserve_line']==line,'Callwise policy prior','spectrum_checks')
  require(reps[call-10992]==rr['ledger_after']==cr['ledger_after']<=line,'Ordered forward ledger call','spectrum_checks')
  require(float(a['available'][0])==allow and int(a['support_rank'][0])==len(values)==rr['support_rank'] and int(a['raw_rank'][0])==rawrank,'Spectrum auxiliary fields','spectrum_checks')
  require(neg==rr['negative_gram_mass']==float(a['negative_gram_mass'][0]) and neg<=1e-16,'Negative mass','spectrum_checks');require(cr['trace_restoration_applied'] is False,'No trace restoration','spectrum_checks')
  require(all(p['trace_restoration_applied'] is False for p in cr['per_sector']),'No sector trace restoration','spectrum_checks')
  negative_total+=neg;ladder_entries+=len(ladder)
  spectrum_table.append({'call':call,'step':s,'half':which,'support_rank':len(values),'retained_rank':minimum,'selected_discard':delta,'ledger_after':rr['ledger_after'],'active_ceiling':line,'reserve_margin':line-rr['ledger_after'],'negative_gram_mass':neg})
 print('SPECTRA',len(spectrum_table),'EXACT_LADDER_ENTRIES',ladder_entries,flush=True)
 telemetry_batches=0;maxbatchres=0.;previous=cfg['start']['previous_overflow_intensity'];over=cfg['start']['overflow']
 for row in steps:
  s=row['step'];n=s-1
  require(all(v is True for v in row['checks'].values()),'Saved step gates','saved_step_gates')
  mapping={'positive_survival':('positive_survival',s),'zero_survival':('zero_survival',s),'positive_click':('positive_step_click',n),'zero_click':('zero_step_click',n),'representation_ledger':('representation_ledger',s),'event_ledger':('event_first_crossing_ledger',s),'representation_increment':('representation_increment',n),'event_increment':('event_increment',n),'total_rank':('total_rank',s),'gmres_max_residual':('gmres_max_residual',n),'step_wall_seconds':('step_wall_seconds',n)}
  for rk,(hk,j) in mapping.items():require(row[rk]==h[hk][j],rk+' record/native','step_record_fields')
  require(row['sector_ranks']==h['sector_ranks'][s].tolist(),'Native sector ranks','step_record_fields')
  require(h['representation_increment'][n]==math.fsum(rep[2*(s-5496)-2:2*(s-5496)]) and h['event_increment'][n]==ev[s-5496-1],'New increments','step_record_fields')
  require(row['zero_crossrun_checked'] is False and row['zero_crossrun_difference'] is None and row['zero_crossrun_reference_end_step']==7200,'No invented zero comparison','step_record_fields')
  for pk,ck in [('positive_step_click','cumulative_positive_click'),('zero_step_click','cumulative_zero_click')]:require(math.fsum([float(h[ck][n]),float(h[pk][n])])==h[ck][s],'Cumulative click update','click_accumulation')
  intensity=phys['rate_lambda']*(phys['n_shell']+2)*float(h['top_shell_population'][s]);over=over+.5*phys['dt']*(previous+intensity);previous=intensity;require(over==h['cumulative_overflow_bound'][s]==row['overflow_bound'],'Overflow trapezoid','step_record_fields')
  d=doc(f'OUTPUT/detector_telemetry/step{s}/detector_traceblockfix1_telemetry.json');require(d['status']=='completed' and d['failure_phase'] is None,'Detector completion','detector_checks');require(d['batch_columns']==64 and d['number_rhs']==h['detector_number_rhs'][n],'Detector RHS','detector_checks')
  batches=d['batches'];require(len(batches)==h['detector_number_batches'][n] and sum(b['batch_size'] for b in batches)==d['number_rhs'],'Batch partition','detector_checks')
  last=0
  for j,b in enumerate(batches):
   require(b['batch_index']==j and b['start_column']==last and b['stop_column_exclusive']-last==b['batch_size'] and b['batch_size']<=64 and b['status']=='completed' and b['gmres_failure_count']==0,'Batch completion/partition','detector_batches');last=b['stop_column_exclusive'];maxbatchres=max(maxbatchres,b['maximum_true_residual'])
   require(b['maximum_true_residual']<=1e-8,'Batch true residual','detector_checks')
  telemetry_batches+=len(batches)
  for key,prefix,history in [('positive_click','positive_click_term','positive_step_click'),('zero_click','zero_click_term','zero_step_click')]:require(math.fsum(b[prefix] for b in batches)==d[key]==h[history][n],'Batch click sum','detector_checks')
  require(d['zero_before']==h['zero_survival'][n] and d['zero_after']==h['zero_survival'][s],'Embedded zero endpoints','detector_checks')
  require(abs(d['positive_midpoint_closure'])<=5e-9 and abs(d['zero_midpoint_closure'])<=5e-9,'Midpoint closure','detector_checks')
 checkpoints=doc('OUTPUT/checkpoint_records.json')['records'];require([x['step'] for x in checkpoints]==[19400,19600,19800,20000],'Checkpoint sequence')
 omitted=[];checkpoint_summary=[]
 for c in checkpoints:
  s=c['step'];cp=f'OUTPUT/checkpoint_step{s}/';cm=doc(cp+'checkpoint_manifest.json')['files'];m=doc(cp+'checkpoint_metadata.json');ch=npz(read(cp+'histories.npz'))
  require(sha(read(cp+'checkpoint_manifest.json'))==c['manifest_sha256'] and m==c['metadata'],'Checkpoint record identity','checkpoint_checks')
  for rel,expected in cm.items():
   if cp+rel in hashes:require(hashes[cp+rel]==expected,'Checkpoint payload '+rel,'checkpoint_payloads_present')
   else:omitted.append(cp+rel)
  equal_prefix(ch,h,'checkpoint'+str(s))
  require(m['completed_step']==s and len(ch['times'])==s+1 and m['physical_time']==s*.0005,'Checkpoint endpoint','checkpoint_checks')
  require(m['forward_representation_terms']==rep[:2*(s-5496)] and m['forward_event_terms']==ev[:s-5496],'Checkpoint all ordered prefixes','checkpoint_checks')
  require(m['reserve_policy']==cfg['policy'] and m['source_sha256']==hashes['PACKAGE/pi1600_continue.py'],'Checkpoint source/policy','checkpoint_checks')
  checkpoint_summary.append({'step':s,'time':s*.0005,'metadata_sha256':hashes[cp+'checkpoint_metadata.json'],'native_arrays_bitwise_prefix':27,'factor_hashes_recorded_only':6,'positive_trace_minus_history':m['positive_survival']-float(h['positive_survival'][s]),'zero_trace_minus_history':m['zero_survival']-float(h['zero_survival'][s])})
 require(read('OUTPUT/checkpoint_step20000/histories.npz')==read('OUTPUT/block_histories.npz'),'Terminal/output NPZ bytes identical')
 require(len(omitted)==24,'Four checkpoints omit six heavy factors each')
 b=h['representation_ledger'];e=h['event_first_crossing_ledger'];s=h['positive_survival'];s0=h['zero_survival'];cp=h['cumulative_positive_click'];c0=h['cumulative_zero_click'];p=h['positive_step_click'];p0=h['zero_step_click']
 require(np.all(p>=0) and np.all(p0>=0) and np.all(s>=0) and np.all(s0>=0),'Nonnegative probabilities')
 require(np.max(np.diff(s))<=2e-9 and np.max(np.diff(s0))<=2e-9,'Survival nonincrease tolerance')
 closure=s+cp+b+e-s[0];zclosure=s0+c0-s0[0]
 require(np.max(np.abs(closure))<5e-8 and np.max(np.abs(zclosure))<5e-8,'Accumulated closures')
 for k,v in [('positive_survival_retained',s[-1]),('zero_survival',s0[-1]),('positive_midpoint_click_sum',cp[-1]),('zero_midpoint_click_sum',c0[-1]),('event_first_crossing_ledger',e[-1]),('representation_ledger',b[-1])]:require(audit['endpoint_metrics'][k]==v,'Reported endpoint vs native '+k)
 zero=npz(read('PACKAGE/REFERENCE_DATA/standalone_zero_2878654_to360.npz'));require(len(zero['times'])==7201,'Independent zero reference coverage');zdiff=float(np.max(np.abs(s0[:7201]-zero['zero_survival'])));require(zdiff<=2e-9,'Available independent zero comparison')
 summary={'scope':'Fresh read-only artifact, history, provenance, ordered-ledger, saved-spectrum and detector-telemetry reconstruction. No production or bundled audit code executed; no heavy factors supplied.',
 'job_id':3463660,'passed':True,'source_files':external,'artifact_manifest_hashes_verified':len(manifest),'package_checksums_verified':COUNTS['package_checksums'],
 'embedded_parent_hashes_verified':COUNTS['parent_compact_hashes'],'embedded_parent_pinned_subset_hashes_verified':COUNTS['parent_pinned_hashes'],
 'node_count':20001,'interval_count':20000,'array_count':27,'time_end':10.,'dt':.0005,'continuation_start_step':19327,'new_full_steps':673,'new_compression_calls':1346,
 'all_27_immediate_parent_prefixes_bitwise_unchanged':True,'earlier_uploaded_prefixes':extra_prefixes,'checkpoint_summaries':checkpoint_summary,
 'representation_terms':len(rep),'event_terms':len(ev),'all_full_step_ledgers_reconstructed_since_step':5497,
 'all_saved_spectral_rank_ladders_reconstructed':1346,'exact_rank_ladder_entries':ladder_entries,'total_negative_gram_mass_new_calls':negative_total,
 'detector_telemetry_steps':len(steps),'detector_batches':telemetry_batches,'maximum_new_batch_true_residual':maxbatchres,
 'maximum_abs_accumulated_positive_closure':float(np.max(np.abs(closure))),'maximum_abs_accumulated_zero_closure':float(np.max(np.abs(zclosure))),
 'endpoint_positive_closure':float(closure[-1]),'endpoint_zero_closure':float(zclosure[-1]),
 'maximum_positive_survival_increment':float(np.max(np.diff(s))),'maximum_zero_survival_increment':float(np.max(np.diff(s0))),
 'maximum_sector_trace_closure':float(np.max(np.abs(np.sum(h['sector_traces'],axis=1)-s))),
 'max_all_history_gmres_residual':float(np.max(h['gmres_max_residual'])),'positive_roof_fsum_minus_saved':math.fsum(p.tolist())-float(cp[-1]),'zero_roof_fsum_minus_saved':math.fsum(p0.tolist())-float(c0[-1]),
 'independent_zero_available_to_time':3.6,'independent_zero_max_survival_difference_on_overlap':zdiff,
 'active_policy':cfg['policy'],'legacy_history_representation_ceiling_at_T10':float(h['representation_ceiling'][-1]),
 'heavy_factor_paths_absent':omitted,'heavy_factors_freshly_hashed_or_traced':False,'historical_full_job2966988_archive_freshly_audited':False,
 'earlier_than_step5496_ledger_ancestry':'preserved with original qualification, not reconstructed from missing spectral data',
 'physical_claim':False,'production_authorized':False,'task10_eligible':False,'automatic_resume':False,
 'check_counts':dict(COUNTS),'elapsed_seconds':time.monotonic()-t0,'software':{'numpy':np.__version__}}
 save_json(out/'VERIFICATION.json',summary);save_json(out/'ARRAY_INVENTORY.json',array_inventory)
 with (out/'spectrum_reconstruction.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(spectrum_table[0]));w.writeheader();w.writerows(spectrum_table)
 keep=['OUTPUT/block_histories.npz','OUTPUT/run_status.json','OUTPUT/independent_audit_report.json','OUTPUT/input_audit.json','OUTPUT/resource_summary.json','OUTPUT/runtime_setup.json','OUTPUT/source_equivalence_record.json','OUTPUT/checkpoint_step20000/checkpoint_manifest.json','OUTPUT/checkpoint_step20000/checkpoint_metadata.json','PACKAGE/CONFIG.json','PACKAGE/CAMPAIGN_POLICY.json','PACKAGE/PARENT_RESULT/checkpoint_manifest.json','PACKAGE/PARENT_RESULT/checkpoint_metadata.json','PACKAGE/PARENT_RESULT/histories.npz','RUNTIME/pc2_port_audit.json','RUNTIME/wrapper_status.json','artifact_hashes.json']
 for rel in keep:
  dest=out/'original'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(read(rel))
 save_json(out/'PRESERVED_ORIGINAL_HASHES.json',{rel:hashes[rel] for rel in keep})
 print(json.dumps({k:v for k,v in summary.items() if k not in ['heavy_factor_paths_absent','checkpoint_summaries','active_policy']},indent=2))

if __name__=='__main__':main()
