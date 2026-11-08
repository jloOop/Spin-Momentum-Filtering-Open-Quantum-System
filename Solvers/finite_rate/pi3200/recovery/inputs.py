"""Immutable11845 config and read-only live source/audit/checkpoint gates."""
from __future__ import annotations
import ast, hashlib, math, shutil
from pathlib import Path
import numpy as np
from archive_tools import digest_file, plain_json, require, verify_local_package
from common import PACKAGE_DIR, config, history_prefix_equal, reserve_line
from memory_components import block_trace_npy
from parent_evidence import read_parent
from configuration_identity import configuration_identity


def validate_config(cfg):
    ident=plain_json((PACKAGE_DIR/'PARENT_IDENTITY.json').read_bytes())
    require(digest_file(PACKAGE_DIR/'CONFIG.json')==ident['new_configuration_sha256'],'Immutable config changed')
    require(cfg==plain_json((PACKAGE_DIR/'CONFIG.json').read_bytes()),'Runtime/config overrides prohibited')
    old=plain_json((PACKAGE_DIR/'SOURCE_PROVENANCE/PARENT_CONFIG.json').read_bytes())
    require(digest_file(PACKAGE_DIR/'SOURCE_PROVENANCE/PARENT_CONFIG.json')==ident['parent_configuration_sha256'],'Parent configuration changed')
    for key in ('physical','legacy','policy','runtime_sources','required_runtime_versions','zero_reference','port'):
        require(cfg[key]==old[key],'Inherited model/policy/runtime changed: '+key)
    changed_gate={'slurm_wall_seconds':86400,'wall_guard_seconds':79200.0,'minimum_free_disk_gib':96}
    require(cfg['gate']==dict(old['gate'],**changed_gate),'Unapproved solver/resource gate change')
    require(cfg['hardware']==dict(old['hardware'],max_requested_wall_seconds=86400,require_partition_max_seconds_at_least=86400),'Unapproved hardware change')
    require(cfg['phase']=='recovery' and cfg['parent_kind']=='certified_clean_stop_checkpoint','Wrong recovery role')
    require(cfg['parent_result']['job_id']=='2969484' and cfg['start']['step']==11845 and cfg['gate']['end_step']==12000,'Wrong restart/target')
    require(all(cfg['gate'][k] is False for k in ('physical_claim','production_authorized','task10_eligible','automatic_resume')),'Scientific or automatic-resume claim')
    require(cfg['physical']['dt']==.0005 and cfg['physical']['rate_lambda']==math.pi/3200. and cfg['physical']['max_event_sector']==4,'Frozen rate/step/sectors')
    require(reserve_line(24000,cfg)==reserve_line(24000,old),'Final representation cap changed')
    require(cfg['output_relative']!=cfg['parent_output_relative'] and cfg['output_relative']==cfg['campaign_output_relative']+'/recovery','Output must be separate from parent')


def check_collisions(root,cfg):
    out=root/cfg['output_relative']
    require(not out.exists() and not out.is_symlink(),'Output collision: '+str(out))
    require(shutil.disk_usage(root).free>=cfg['gate']['minimum_free_disk_gib']*2**30,
            'Need 96 GiB free filesystem space; check project/user quota independently')

def extraction_check(package):
    mapping=plain_json((package/'EXTRACTION_MAP.json').read_bytes());reports={}
    for filename,description in mapping.items():
        text=(package/filename).read_text();nodes={n.name:n for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        require(digest_file(package/description['reference_file'])==description['reference_sha256'],'Frozen reference changed')
        for row in description['members']:
            if row['kind']=='function':
                require(row['name'] in nodes,'Missing numerical function')
                body=ast.get_source_segment(text,nodes[row['name']])+'\n'
                require(hashlib.sha256(body.encode()).hexdigest()==row['sha256'],f'Physical function changed: {filename}:{row["name"]}')
        reports[filename]={'functions_byte_exact':True,'reference_sha256':description['reference_sha256']}
    def body(path):
        text=path.read_text();ns=[n for n in ast.walk(ast.parse(text)) if isinstance(n,ast.FunctionDef) and n.name=='flush']
        require(len(ns)==1,'Ambiguous flush');return ast.get_source_segment(text,ns[0])
    require(body(package/'REFERENCE/poolflush_replay.py')==body(package/'pool_control.py'),'Allocator operation changed')
    return reports


def static_check(package,cfg):
    validate_config(cfg)
    configuration_record=configuration_identity(cfg,package=package)
    count=verify_local_package(package)
    listed={line.split(maxsplit=1)[1].lstrip('*') for line in (package/'SHA256SUMS.txt').read_text().splitlines() if line.strip()}
    # Nested original SHA256SUMS.txt is a payload too.
    actual={p.relative_to(package).as_posix() for p in package.rglob('*') if p.is_file() and not p.is_symlink()
       and p!=package/'SHA256SUMS.txt' and 'PREPARED' not in p.relative_to(package).parts and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    require(actual==listed,'Untracked/missing immutable payload')
    require(not any(p.is_symlink() for p in package.rglob('*')),'Symlink in package')
    ids=plain_json((package/'NUMERICAL_IDENTITIES.json').read_bytes())
    for n,h in ids['byte_identical_files'].items():require(digest_file(package/n)==h,'Frozen numerical/utility source changed: '+n)
    for n,h in cfg['runtime_sources'].items():require(digest_file(package/'RUNTIME_SOURCES'/n)==h,'Runtime source changed: '+n)
    source=(package/'common.py').read_text();nodes={n.name:n for n in ast.parse(source).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    for name,h in ids['common_functions_byte_identical'].items():
        require(hashlib.sha256((ast.get_source_segment(source,nodes[name])+'\n').encode()).hexdigest()==h,'Common arithmetic changed: '+name)
    require(digest_file(package/'half_rate_continue.py')==cfg['port']['source_continuation_driver_sha256'],'Byte-identical driver')
    require(digest_file(package/'WHEEL'/cfg['port']['numpy_wheel_name'])==cfg['port']['numpy_wheel_sha256'],'Pinned wheel')
    for sourcefile in package.glob('*.py'):compile(sourcefile.read_text(),str(sourcefile),'exec')
    parent=read_parent(cfg=cfg,package=package)
    return {'passed':True,'configuration_identity':configuration_record,'package_hash_count':count,'extraction':extraction_check(package),'parent_evidence':parent['identity_checks'],
            'physical_map_changed':False,'compression_policy_changed':False,'new_budget_released':False,'driver_byte_identical':True}


def verify_live_parent_evidence(root,cfg,*,package=PACKAGE_DIR):
    p=cfg['parent_result'];source=package/'PARENT_EVIDENCE'
    archive=root/p['name']
    require(archive.is_file() and not archive.is_symlink() and digest_file(archive)==p['sha256'],'Original finalized full result missing/changed: '+str(archive))
    # Authenticate the entire recorded phase audit input tree (not a rerun of its numerical audit).
    out=root/cfg['parent_output_relative'];local=source/'OUTPUT/continuation'
    for n in ('run_status.json','summary_report.json','independent_audit_report.json','phase_port_audit.json','phase_audit_inputs.json','inherited_implementation_bridge.json'):
        f=out/n;require(f.is_file() and not f.is_symlink() and digest_file(f)==digest_file(local/n),'Parent live report changed: '+str(f))
    mm=plain_json((local/'phase_audit_inputs.json').read_bytes())['files']
    for n,h in mm.items():
        q=Path(n);require(not q.is_absolute() and '..' not in q.parts,'Unsafe prior audit-input name')
        f=out/n;require(f.is_file() and not f.is_symlink() and digest_file(f)==h,'Parent live audit input changed: '+str(f))
    runtime=root/cfg['parent_runtime_relative']
    for n in ('h100_device_gate.json','platform_bridge_report.json','return_codes.json'):
        f=runtime/n;require(f.is_file() and not f.is_symlink() and digest_file(f)==digest_file(source/'RUNTIME/continuation'/n),'Live allocated-parent evidence changed: '+str(f))
    return {'parent_full_result_hashed':True,'parent_phase_inputs_hashed':len(mm),'parent_numerical_audit_rerun':False}


def read_inputs(root,cfg,*,trace_factors=True,package=PACKAGE_DIR):
    parent=read_parent(cfg=cfg,package=package)
    parent_live=verify_live_parent_evidence(root,cfg,package=package)
    checkpoint=root/cfg['checkpoint_relative'];require(checkpoint.is_dir() and not checkpoint.is_symlink(),'Exact certified checkpoint missing')
    for n,s in cfg['checkpoint_payloads'].items():
        f=checkpoint/n;require(f.is_file() and not f.is_symlink() and digest_file(f)==s,'Live checkpoint hash: '+str(f))
    meta=plain_json((checkpoint/'checkpoint_metadata.json').read_bytes())
    require(meta==parent['metadata'],'Live checkpoint metadata differs from certified record')
    with np.load(checkpoint/'histories.npz',allow_pickle=False) as a:h={k:np.array(a[k],copy=True) for k in a.files}
    require(history_prefix_equal(h,parent['histories']) and h['times'].shape==parent['histories']['times'].shape,'Live history seam')
    p=cfg['physical'];fa={};tr=[];za={}
    if trace_factors:
        for k,rank in enumerate(cfg['start']['ranks']):
            item=block_trace_npy(checkpoint/f'sector_{k}.npy',p['h_z'])
            require(item['finite'] and item['dtype']=='complex128' and tuple(item['shape'])==(p['dimension'],rank),'Live sector schema')
            require(abs(item['trace']-float(h['sector_traces'][-1,k]))<=5e-12,'Live sector weighted trace')
            fa[str(k)]=item;tr.append(item['trace'])
        za=block_trace_npy(checkpoint/'zero_state.npy',p['h_z'])
        require(za['finite'] and za['dtype']=='complex128' and tuple(za['shape'])==(p['dimension'],1),'Live zero schema')
        require(abs(za['trace']-h['zero_survival'][-1])<=5e-12 and abs(math.fsum(tr)-h['positive_survival'][-1])<=5e-12,'Live family trace')
    zr=cfg['zero_reference'];zfile=package/zr['file'];require(digest_file(zfile)==zr['sha256'],'Historical zero reference changed')
    with np.load(zfile,allow_pickle=False) as a:q={k:np.array(a[k],copy=True) for k in a.files}
    for item in zr['arrays']:
        x=q[item['name']];require(str(x.dtype)==item['dtype'] and list(x.shape)==item['shape'] and hashlib.sha256(x.tobytes(order='C')).hexdigest()==item['raw_c_order_sha256'],'Zero reference array')
    cross=float(np.max(np.abs(q['zero_survival']-h['zero_survival'][:zr['available_through_step']+1])))
    require(cross<=cfg['gate']['zero_crossrun_tolerance'],'Historical independent zero mismatch')
    nxt=2*cfg['start']['step']+1
    report={**parent['identity_checks'],'passed':True,'checkpoint_path':str(checkpoint),'checkpoint_payload_hashes':cfg['checkpoint_payloads'],
        'live_factors_hashed_now':True,'live_factors_traced_now':bool(trace_factors),'factor_audit':fa,'zero_state_audit':za,
        'next_global_call':nxt,'next_reserve_line':reserve_line(nxt,cfg),'zero_crossrun_reference_available_through_step':zr['available_through_step'],
        'zero_crossrun_future_claimed':False,'zero_crossrun_maximum_prefix_difference':cross,
        'state_modified':False,'physical_steps_performed':0,'phase':cfg['phase'],'separate_user_quota_assessed':False,**parent_live}
    return dict(metadata=meta,histories=h,quarter_histories=q,checkpoint=checkpoint,runtime=package/'RUNTIME_SOURCES',report=report,
                inherited_representation_terms=parent['inherited_representation_terms'],inherited_event_terms=parent['inherited_event_terms'],
                inherited_implementation_bridge=parent['bridge'])
