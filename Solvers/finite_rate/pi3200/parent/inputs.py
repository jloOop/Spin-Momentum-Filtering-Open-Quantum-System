"""Immutable role config, exact parent identity, and live checkpoint gates."""
from __future__ import annotations
import ast, hashlib, math, shutil, zipfile
from pathlib import Path
import numpy as np
from archive_tools import digest_file, plain_json, require, verify_local_package
from common import PACKAGE_DIR, all_true, config, history_prefix_equal, reserve_line
from memory_components import block_trace_npy
from parent_evidence import read_parent


def validate_config(cfg):
    phase=cfg.get('phase')
    require(phase in ('strict_pilot','candidate_pilot','continuation'),'Unknown immutable role')
    if phase=='continuation':
        from promotion import verify_promotion
        verified=verify_promotion(Path(cfg['project_root']),package=PACKAGE_DIR,check_factors=False)
        require(cfg==verified['configuration'],'Production capsule mismatch')
    else:
        expected=plain_json((PACKAGE_DIR/'CONFIGS'/(phase+'.json')).read_bytes())
        require(cfg==expected,'Numerical/runtime overrides forbidden')
    orig=plain_json((PACKAGE_DIR/'SOURCE_PROVENANCE/PARENT_CONFIG.json').read_bytes())
    require(cfg['physical']==orig['physical'] and cfg['physical']['rate_lambda']==math.pi/3200.,'Frozen physical model changed')
    require(cfg['legacy']==orig['legacy'],'Legacy ledger anchor changed')
    require(cfg['runtime_sources']==orig['runtime_sources'] and cfg['required_runtime_versions']==orig['required_runtime_versions'],'Frozen sources/runtime changed')
    require(cfg['zero_reference']==orig['zero_reference'],'Independent-zero scope changed')
    for k in ('physical_claim','production_authorized','task10_eligible','automatic_resume'):
        require(cfg['gate'][k] is False,'Prohibited acceptance/automatic resume')
    for k in ('bridge_factor_relative_tolerance','bridge_scalar_absolute_tolerance','zero_crossrun_tolerance','step_prediction_safety_factor','checkpoint_prediction_floor_seconds','terminal_checkpoint_on_clean_stop'):
        require(cfg['gate'][k]==orig['gate'][k],'Inherited guard changed: '+k)
    require((cfg['gate']['rank_guard'],cfg['gate']['memory_guard_mib'],cfg['gate']['checkpoint_stride'])==(2600,88064.,100),'Resource settings changed')
    require(cfg['gate']['wall_guard_seconds']+cfg['gate']['finalization_reserve_seconds']==cfg['gate']['slurm_wall_seconds'],'Wall reserve mismatch')
    require(cfg['physical']['dt']==.0005 and cfg['physical']['max_event_sector']==4,'Step/event structure')
    require(reserve_line(24000,cfg)==reserve_line(24000,orig),'Final representation cap increased')
    if phase!='continuation':
        require((cfg['start']['step'],cfg['gate']['end_step'])==(8849,8949),'Pilot step range')
        require(cfg['parent_result']['job_id']=='2895255','Wrong parent job')


def check_collisions(root,cfg):
    out=root/cfg['output_relative']
    require(not out.exists() and not out.is_symlink(),'Output collision: '+str(out))
    require(shutil.disk_usage(root).free>=cfg['gate']['minimum_free_disk_gib']*2**30,
            f'Need {cfg["gate"]["minimum_free_disk_gib"]} GiB free scratch; verify applicable quota separately')


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
    validate_config(cfg);count=verify_local_package(package)
    listed={line.split(maxsplit=1)[1].lstrip('*') for line in (package/'SHA256SUMS.txt').read_text().splitlines() if line.strip()}
    actual={p.relative_to(package).as_posix() for p in package.rglob('*') if p.is_file() and not p.is_symlink()
            and p.name!='SHA256SUMS.txt' and 'PREPARED' not in p.relative_to(package).parts and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    require(actual==listed,'Untracked/missing immutable file')
    require(not any(p.is_symlink() for p in package.rglob('*')),'Symlink in package')
    ids=plain_json((package/'NUMERICAL_IDENTITIES.json').read_bytes())
    for n,s in ids['byte_identical_numerical_files'].items():require(digest_file(package/n)==s,'Changed physical file: '+n)
    require(digest_file(package/'half_rate_continue.py')==cfg['port']['source_continuation_driver_sha256']==ids['continuation_driver_sha256'],'Driver identity')
    require(digest_file(package/'WHEEL'/cfg['port']['numpy_wheel_name'])==cfg['port']['numpy_wheel_sha256'],'Wheel identity')
    # Full supplied compact archive is checked here; absent parent spectra are not fabricated.
    basecfg=plain_json((package/'CONFIGS/candidate_pilot.json').read_bytes());pr=basecfg['parent_result']
    archive=package/pr['compact_file'];require(digest_file(archive)==pr['compact_sha256'],'Uploaded parent compact changed')
    with zipfile.ZipFile(archive) as z:
        require(z.testzip() is None,'Parent archive CRC')
        top=pr['compact_top']+'/'
        am=plain_json(z.read(top+'artifact_hashes.json'))['files']
        for n,s in am.items():require(hashlib.sha256(z.read(top+n)).hexdigest()==s,'Parent compact member: '+n)
        pm=plain_json(z.read(top+'PACKAGE/PACKAGE_MANIFEST.json'))['files']
        for n,s in pm.items():require(hashlib.sha256(z.read(top+'PACKAGE/'+n)).hexdigest()==s,'Parent package member: '+n)
    for source in package.glob('*.py'):compile(source.read_text(),str(source),'exec')
    parent=read_parent(cfg=cfg,package=package)
    return {'passed':True,'package_hash_count':count,'extraction':extraction_check(package),'parent_evidence':parent['identity_checks'],
            'physical_map_changed':False,'compression_primitive_changed':False,'prospective_policy_only':cfg['phase']!='strict_pilot',
            'parent_compact_manifest_files_checked':len(am),'parent_package_manifest_files_checked':len(pm),
            'H100_pilot_executed_locally':False}


def read_inputs(root,cfg,*,trace_factors=True,package=PACKAGE_DIR):
    parent=read_parent(cfg=cfg,package=package);pr=cfg['parent_result']
    if cfg['phase']!='continuation':
        arc=root/pr['name']
        require(arc.is_file() and not arc.is_symlink() and digest_file(arc)==pr['sha256'],'Original strict full-result ZIP missing/changed: '+str(arc))
        for prefix,directory in [('OUTPUT',root/cfg['parent_output_relative']),('RUNTIME',root/cfg['parent_runtime_relative'])]:
            names=['independent_audit_report.json','run_status.json'] if prefix=='OUTPUT' else ['pc2_port_audit.json','wrapper_status.json']
            for name in names:
                f=directory/name;require(f.is_file() and not f.is_symlink() and digest_file(f)==pr['evidence_member_hashes'][prefix+'/'+name],'Prior live audit changed: '+str(f))
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
        'state_modified':False,'physical_steps_performed':0,'phase':cfg['phase'],'separate_user_quota_assessed':False}
    return dict(metadata=meta,histories=h,quarter_histories=q,checkpoint=checkpoint,runtime=package/'RUNTIME_SOURCES',report=report,
                inherited_representation_terms=parent['inherited_representation_terms'],inherited_event_terms=parent['inherited_event_terms'],
                inherited_implementation_bridge=parent['bridge'])
