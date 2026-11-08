"""Strict audited own-branch restart and read-only input validation."""
from __future__ import annotations

import ast
import hashlib
import math
import shutil
from pathlib import Path

import numpy as np

from archive_tools import Archive, digest_file, plain_json, require, verify_local_package
from common import PACKAGE_DIR, all_true, config, history_prefix_equal, reserve_line
from memory_components import block_trace_npy
from campaign_layout import required_free_gib, package_name, output_relative, result_prefix, runtime_prefix, job_name
from parent_evidence import read_parent


def validate_config(cfg: dict) -> None:
    p,s,g,pol,leg,hw=(cfg[k] for k in ('physical','start','gate','policy','legacy','hardware'))
    campaign=cfg['campaign']; start=s['step']
    all_true({
        'schema':cfg['schema']=='task09-pi1600-continuation-config-v3-to1000',
        'scope':isinstance(start,int) and 12000<=start<20000 and s['time']==start*.0005 and g['end_step']==20000,
        'campaign':campaign['root_start_step']==12000 and campaign['end_step']==20000 and campaign['root_parent_job_id']=='2894739' and campaign['root_parent_compact_sha256']=='20099017eece2749edfa705862335b69eefe13c33f0ec661b95a05ef326fc396' and campaign['root_parent_checkpoint_metadata_sha256']=='ebf68b08a99a7aea785bc12dbf1db71727abe1335ef420490906d568762e3e47',
        'manual_only':campaign['manual_next_allocation_only'] is True and campaign['global_policy_must_not_rebase'] is True and isinstance(campaign['allocation_index'],int) and campaign['allocation_index']>=1,
        'dimensions':(p['n_shell'],p['n_z'],p['d_channels'],p['dimension'])==(12,1500,182,273000),
        'model':(p['omega'],p['dt'],p['l_z'],p['max_event_sector'],p['h_z'])==(100.,.0005,20.,4,.013333333656191826),
        'rate':p['rate_lambda']==math.pi/1600. and p['rate_label']=='lambda0_over_4',
        'parent_step':cfg['parent_result']['checkpoint_step']==start,
        'unique_names':cfg['package_name']==package_name(start) and cfg['output_relative']==output_relative(start) and cfg['result_prefix']==result_prefix(start) and cfg['runtime_prefix']==runtime_prefix(start) and cfg['job_name']==job_name(start),
        'ranks':len(s['ranks'])==5 and all(isinstance(r,int) and r>=0 for r in s['ranks']) and sum(s['ranks'])>0,
        'original_anchor':leg['step']==5496 and leg['call']==10992 and leg['representation_ledger']==1.7499772167089214e-7 and leg['event_ledger']==1.6548522178802567e-11,
        'original_terms':s['inherited_representation_term_count']==2*(start-5496) and s['inherited_event_term_count']==start-5496,
        'global_policy':pol['name']=='H10_Post600_ProspectiveLinearReserveTo1000_v1' and pol['start_call']==24001 and pol['end_call']==40000 and pol['start_ledger_decimal']=='3.749992628669547e-07' and pol['final_ceiling_decimal']=='6.25e-7' and pol['previous_ceiling_decimal']=='3.75e-7',
        'resources':(g['rank_guard'],g['memory_guard_mib'],g['checkpoint_stride'])==(2600,88064.,200),
        'wall_disk':(g['slurm_wall_seconds'],g['wall_guard_seconds'],g['finalization_reserve_seconds'],g['minimum_free_disk_gib'])==(604800,597600.,7200,required_free_gib(start)),
        'platform':hw['partition']=='gpu_h100' and hw['account']=='hpc-prf-gasqd' and hw['gpu_count']==1 and hw['gpu_name_contains']=='H100' and hw['host_memory_gib']==128 and hw['cpus_per_task']==3 and hw['minimum_gpu_memory_mib']==90000 and hw['require_partition_max_seconds_at_least']==604800,
        'paths':cfg['project_root']=='[ARCHIVE_PATH]' and cfg['python']=='[ARCHIVE_PATH_794119aa1f239670]/python',
        'runtime':cfg['required_runtime_versions']=={'numpy':'2.4.2','scipy':'1.17.1','cupy':'14.0.1','cuda_runtime':12090},
        'tolerances':(g['bridge_factor_relative_tolerance'],g['bridge_scalar_absolute_tolerance'],g['zero_crossrun_tolerance'])==(5e-11,5e-12,2e-9),
        'claims':all(g[k] is False for k in ('physical_claim','production_authorized','task10_eligible','automatic_resume')),
        'accounting':pol['future_borrowing'] is False and pol['trace_restoration'] is False and pol['legacy_prefix_ledger_inherited_unchanged'] is True,
        'checkpoint_files':set(cfg['checkpoint_payloads'])==set(cfg['checkpoint_payload_sizes'])=={'checkpoint_manifest.json','checkpoint_metadata.json','histories.npz','zero_state.npy',*[f'sector_{k}.npy' for k in range(5)]},
        'zero_scope':cfg['zero_reference']['available_through_step']==7200 and cfg['zero_reference']['source_job_id']=='2878654',
    },'Frozen pi/1600 post600 continuation configuration')
    if campaign['allocation_index']==1:
        require(start==12000 and cfg['parent_result']['job_id']=='2894739' and cfg['parent_result']['sha256']==campaign['root_parent_compact_sha256'] and s['ranks']==[1,860,123,15,5] and s['representation_ledger']==3.749992628669547e-7 and s['event_ledger']==8.597403173074621e-10,'Wrong initial step12000 parent')
    else:
        require(start>12000 and cfg['parent_result']['expected_status']=='clean_nonaccepting_stop' and cfg['parent_result']['expected_policy']==pol,'Manual continuation did not preserve the global policy')
    require(pol==plain_json((PACKAGE_DIR/'CAMPAIGN_POLICY.json').read_bytes()),'Campaign allowance changed')
    require(reserve_line(24000,cfg)==3.749992628669547e-7 and reserve_line(40000,cfg)==6.25e-7 and s['representation_ledger']<=reserve_line(2*start,cfg),'Allowance continuity')
    require(g['rank_guard']>=sum(s['ranks']) and g['wall_guard_seconds']+g['finalization_reserve_seconds']==g['slurm_wall_seconds'],'Resource headroom')
    from pathlib import PurePosixPath
    for key in ('checkpoint_relative','output_relative'):
        rel=PurePosixPath(cfg[key])
        require(not rel.is_absolute() and '..' not in rel.parts and rel.parts[0]=='Task09_ES_G5P_PC2','Unsafe campaign path')
    require(cfg['checkpoint_relative']!=cfg['output_relative'],'Input/output collision')

def check_collisions(root: Path, cfg: dict) -> None:
    output = root / cfg['output_relative']
    require(not output.exists() and not output.is_symlink(), f'Output collision: {output}')
    existing = list(root.glob(cfg['result_prefix'] + '*.zip'))
    require(not existing, f'Previous result with this immutable package scope: {existing}')
    free = shutil.disk_usage(root).free
    require(free >= cfg['gate']['minimum_free_disk_gib'] * 2**30,
            f'Need {cfg["gate"]["minimum_free_disk_gib"]} GiB free filesystem scratch; '
            f'available={free / 2**30:.3f} GiB; user quota is separate')


def static_check(package: Path, cfg: dict) -> dict:
    validate_config(cfg);count=verify_local_package(package)
    names={line.split(maxsplit=1)[1].lstrip('*') for line in (package/'SHA256SUMS.txt').read_text().splitlines() if line.strip()}
    actual={p.relative_to(package).as_posix() for p in package.rglob('*') if p.is_file() and not p.is_symlink() and p.name!='SHA256SUMS.txt' and 'PREPARED' not in p.relative_to(package).parts and '__pycache__' not in p.relative_to(package).parts and p.suffix!='.pyc'}
    require(names==actual,'Untracked/missing immutable files: '+str(names^actual))
    extraction=extraction_check(package)
    identities=plain_json((package/'NUMERICAL_IDENTITIES.json').read_bytes())
    require(identities['physical_map_changed'] is False and identities['compression_algorithm_changed'] is False and identities['detector_solver_changed'] is False,'Changed numerical primitives')
    require(identities['prospective_policy_changed'] is True and identities['past_ledger_changed'] is False,'Unrecorded prospective policy')
    for name,sha in identities['pinned_files'].items():require(digest_file(package/name)==sha,'Pinned file changed: '+name)
    require(digest_file(package/'pi1600_continue.py')==cfg['port']['source_driver_sha256'],'Driver hash mismatch')
    for name,sha in cfg['runtime_sources'].items():require(digest_file(package/'RUNTIME_SOURCES'/name)==sha,'Frozen runtime changed')
    for p in package.glob('*.py'):compile(p.read_text(),str(p),'exec')
    with Archive(package/cfg['parent_result']['embedded_file'],cfg['parent_result']['sha256'],rootless=True) as a:
        require(a.root==cfg['parent_result']['root'],'Wrong parent root')
    wrapper=(package/'run_gpu.sh').read_text()
    required=['#SBATCH --job-name='+cfg['job_name'],'#SBATCH --account=hpc-prf-gasqd','#SBATCH --partition=gpu_h100','#SBATCH --gres=gpu:h100:1','#SBATCH --nodes=1','#SBATCH --ntasks=1','#SBATCH --cpus-per-task=3','#SBATCH --mem=128G','#SBATCH --time=7-00:00:00','#SBATCH --signal=USR1@7200','#SBATCH --no-requeue','module load lang/Python/3.11.5-GCCcore-13.2.0','h100_device_gate.py','platform_bridge.py','pc2_port_audit.py']
    require(all(x in wrapper for x in required),'H100 wrapper contract')
    require(all(x not in wrapper for x in ('gpu-a100','bwmjozan','Pi3200','T09H5600P1','HalfRate','half_rate_continue')),'Half-rate or ZIB execution mixed into wrapper')
    tree=ast.parse((package/'pi1600_continue.py').read_text());calls={}
    for node in ast.walk(tree):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id in ('engine','parent','spec','mem'):
            calls.setdefault(node.func.value.id,set()).add(node.func.attr)
    declared=plain_json((package/'SOURCE_SCOPE.json').read_bytes())['calls']
    for k,v in calls.items():require(v<=set(declared[k]),'Out-of-scope primitive call')
    return {'passed':True,'package_hash_count':count,'extraction':extraction,'source_scope_calls':{k:sorted(v) for k,v in calls.items()},'physical_map_changed':False,'prospective_policy_changed':True,'past_ledger_changed':False,'external_runtime_source_dependency':False}


def read_inputs(root: Path, cfg: dict, *, trace_factors: bool = True, package: Path = PACKAGE_DIR) -> dict:
    validate_config(cfg)
    parent_path = package / cfg['parent_result']['embedded_file']
    with Archive(parent_path, cfg['parent_result']['sha256'], rootless=True) as archive:
        parent_data = read_parent(archive, cfg)

    checkpoint = root / cfg['checkpoint_relative']
    require(checkpoint.is_dir() and not checkpoint.is_symlink(), f'Checkpoint missing/unsafe: {checkpoint}')
    require({path.name for path in checkpoint.iterdir()} == set(cfg['checkpoint_payloads']),
            'Unexpected live-checkpoint file set')
    for name, sha in cfg['checkpoint_payloads'].items():
        path = checkpoint / name
        require(path.is_file() and not path.is_symlink() and path.stat().st_size == cfg['checkpoint_payload_sizes'][name] and digest_file(path) == sha,
                f'Live checkpoint hash mismatch: {path}')

    meta = plain_json((checkpoint / 'checkpoint_metadata.json').read_bytes())
    require(meta == parent_data['metadata'], 'Live metadata differs from immutable parent result')
    require(plain_json((checkpoint / 'checkpoint_manifest.json').read_bytes()) == parent_data['manifest'],
            'Live manifest differs from immutable parent result')
    with np.load(checkpoint / 'histories.npz', allow_pickle=False) as archive:
        histories = {k: np.asarray(archive[k]) for k in archive.files}
    require(history_prefix_equal(histories, parent_data['histories']) and
            histories['times'].shape == parent_data['histories']['times'].shape,
            'Live history differs from immutable parent result')

    factor_audit: dict[str, dict] = {}
    traces: list[float] = []
    p = cfg['physical']
    for sector, rank in enumerate(cfg['start']['ranks']):
        if trace_factors:
            item = block_trace_npy(checkpoint / f'sector_{sector}.npy', p['h_z'])
            require(item['dtype'] == 'complex128' and item['finite'] and
                    tuple(item['shape']) == (p['dimension'], rank),
                    f'Factor {sector} shape/dtype/finiteness')
            require(abs(item['trace'] - float(histories['sector_traces'][-1, sector])) <= 5e-12 and
                    abs(item['trace'] - meta['sector_traces'][str(sector)]) <= 5e-12,
                    f'Factor {sector} weighted trace')
            if rank == 0:
                require(item['trace'] == 0.0, 'Empty retained sector is not zero')
            factor_audit[str(sector)] = item
            traces.append(item['trace'])

    zero_audit = block_trace_npy(checkpoint / 'zero_state.npy', p['h_z']) if trace_factors else {}
    if trace_factors:
        require(zero_audit['dtype'] == 'complex128' and zero_audit['finite'] and
                tuple(zero_audit['shape']) == (p['dimension'], 1), 'Embedded-zero state schema')
        require(abs(zero_audit['trace'] - float(histories['zero_survival'][-1])) <= 5e-12 and
                abs(math.fsum(traces) - float(histories['positive_survival'][-1])) <= 5e-12,
                'Starting weighted family/zero trace')

    runtime = package / 'RUNTIME_SOURCES'
    for name, sha in cfg['runtime_sources'].items():
        require(digest_file(runtime / name) == sha, f'Frozen runtime source changed: {name}')

    zref = cfg['zero_reference']
    zfile = package / zref['file']
    require(digest_file(zfile) == zref['sha256'], 'Zero scalar-observable reference bytes changed')
    with np.load(zfile, allow_pickle=False) as archive:
        zero_reference = {k: np.asarray(archive[k]) for k in archive.files}
    end = zref['available_through_step']
    require(end <= cfg['start']['step'] and np.array_equal(zero_reference['times'], np.arange(end + 1) * p['dt']),
            'Zero scalar-observable reference grid/scope')
    for item in zref['arrays']:
        array = zero_reference[item['name']]
        require(str(array.dtype) == item['dtype'] and list(array.shape) == item['shape'] and
                hashlib.sha256(array.tobytes(order='C')).hexdigest() == item['raw_c_order_sha256'],
                f'Zero-reference array identity: {item["name"]}')
    cross = float(np.max(np.abs(zero_reference['zero_survival'][:end+1] - histories['zero_survival'][:end+1])))
    require(cross <= cfg['gate']['zero_crossrun_tolerance'], 'Starting zero cross-run difference')

    report = {
        **parent_data['identity_checks'],
        'checkpoint_path': str(checkpoint),
        'checkpoint_payload_hashes': cfg['checkpoint_payloads'],
        'live_factors_hashed_now': True,
        'live_factors_traced_now': bool(trace_factors),
        'factor_audit': factor_audit,
        'zero_state_audit': zero_audit,
        'inherited_terms_rebased': False,
        'legacy_representation_ledger': cfg['legacy']['representation_ledger'],
        'starting_representation_ledger': meta['representation_ledger'],
        'next_global_call': 2 * cfg['start']['step'] + 1,
        'next_reserve_line': reserve_line(2 * cfg['start']['step'] + 1, cfg),
        'one_time_implementation_bridge_repeated': False,
        'zero_reference': zref,
        'zero_crossrun_maximum_difference_on_available_prefix': cross,
        'zero_crossrun_reference_available_through_step': end,
        'zero_crossrun_future_claimed': False,
        'half_rate_quantum_state_loaded': False,
        'state_modified': False,
        'physical_steps_performed': 0,
        'free_filesystem_bytes_now': shutil.disk_usage(root).free,
        'separate_user_quota_assessed': False,
    }
    return {
        'metadata': meta,
        'histories': histories,
        'quarter_histories': zero_reference,
        'checkpoint': checkpoint,
        'runtime': runtime,
        'report': report,
        'inherited_representation_terms': list(parent_data['inherited_representation_terms']),
        'inherited_event_terms': list(parent_data['inherited_event_terms']),
        'source_equivalence_record': parent_data['bridge'],
    }


def extraction_check(package: Path) -> dict:
    mapping = plain_json((package / 'EXTRACTION_MAP.json').read_bytes())
    reports: dict[str, dict] = {}
    for filename, description in mapping.items():
        target = (package / filename).read_text()
        tree = ast.parse(target)
        actual = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        reference = package / description['reference_file']
        require(digest_file(reference) == description['reference_sha256'], f'Reference changed: {reference}')
        for row in description['members']:
            if row['kind'] == 'function':
                require(row['name'] in actual, f'Missing extracted function: {row["name"]}')
                text = ast.get_source_segment(target, actual[row['name']]) + '\n'
                require(hashlib.sha256(text.encode()).hexdigest() == row['sha256'],
                        f'Numerical function changed: {filename}:{row["name"]}')
        reports[filename] = {'reference_sha256': description['reference_sha256'], 'functions_byte_exact': True}

    pool_reference = package / 'REFERENCE/poolflush_replay.py'
    require(digest_file(pool_reference) == config()['reference_source_sha256']['pool'], 'Pool reference source changed')

    def flush_segment(path: Path) -> str:
        source = path.read_text()
        found = [node for node in ast.walk(ast.parse(source))
                 if isinstance(node, ast.FunctionDef) and node.name == 'flush']
        require(len(found) == 1, 'Ambiguous allocator flush method')
        return ast.get_source_segment(source, found[0])

    require(flush_segment(pool_reference) == flush_segment(package / 'pool_control.py'), 'Allocator operation changed')
    reports['pool_control.py'] = {'allocator_flush_method_byte_exact': True}
    return reports
