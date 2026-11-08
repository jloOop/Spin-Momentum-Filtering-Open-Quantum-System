"""Continue byte-identical PoolFlushFix1 allocation operations after a certified replay.
Historical replay evidence is inherited from immutable result 9451347. No new
GPU replay or full-density comparison is claimed. The four flush operations
and their memory samples are identical to the parent implementation.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Mapping

SCHEMA = 'task09-poolflushfix1-continuation-v1'
START_STEP = 5496
END_STEP = 5600
PHASES = ('first_before_analysis','first_before_compression','second_before_analysis','second_before_compression')
INHERITED_AUTHORITY = {'schema': 'task09-poolflushfix1-inherited-replay-authority-v1', 'parent_result_sha256': '2d38f0e2f751406770d8549b16d4c149a8d65570c01dcaa2554cab644d897c5a', 'parent_pool_payload_sha256': 'd6e4297ab0016fc64d4141aed10d7a611bafe33e087c29c7a4408f8f538b782f', 'parent_independent_audit_sha256': '69af840b66616dd0e6b6d52fc96598396d56bef7e540db4c33c41cd09722d9ba', 'parent_source_sha256': '1cfc848cbfde05bbed9ed7da65d38e8f0bf229afece3c4f7ec518b2d2f29c8a5', 'persistent_step': 5496, 'validated_replay_steps': [5469, 5470, 5471, 5472], 'original_replay_reference_result_sha256': '660765ac44798ac1986bb65e9f1ff827433bfa1bf6252dda7053d8af164f1bc6', 'parent_flush_count': 112, 'parent_replay_gate_passed': True, 'parent_allocation_invariants_reconstructed': True, 'new_gpu_replay_performed': False}


def validate_inherited_authority(reference: Mapping[str, Any]) -> None:
    if dict(reference) != INHERITED_AUTHORITY:
        raise RuntimeError('PoolFlushFix1 inherited replay authority mismatch')


class Controller:
    def __init__(self, *, output: Path, backend: Any, memory: list[dict[str, Any]], snapshot: Any,
                 write_json: Any, reference: Mapping[str, Any]):
        validate_inherited_authority(reference)
        self.output, self.backend, self.memory = output, backend, memory
        self.snapshot, self.write_json, self.reference = snapshot, write_json, dict(reference)
        self.flushes: list[dict[str, Any]] = []
        self.validated_steps: list[int] = []
        self.persist()
        print('[poolflush-authority] inherited replay 5469...5472 from result 9451347: PASS', flush=True)

    def persist(self) -> None:
        self.write_json(self.output / 'poolflush_replay.json', {
            'schema':SCHEMA, 'flushes':self.flushes, 'validated_steps':self.validated_steps,
            'inherited_replay_authority':self.reference, 'replay_gate_inherited':True,
            'new_gpu_replay_performed':False, 'start_step':START_STEP, 'end_step':END_STEP,
            'all_original_memory_samples_retained':True, 'arithmetic_kernels_changed':False})

    def flush(self, step: int, phase: str) -> None:
        if phase not in PHASES: raise RuntimeError(f'Unknown pool flush phase: {phase}')
        self.backend.synchronize()
        cp = self.backend._cp
        label = f'poolflush_step{step}_{phase}'
        before = self.snapshot(label+'_before', cp)
        self.memory.append(before)
        cp.get_default_memory_pool().free_all_blocks()
        self.backend.synchronize()
        after = self.snapshot(label+'_after', cp)
        self.memory.append(after)
        checks = {'active_pool_bytes_unchanged': before['pool_used_bytes'] == after['pool_used_bytes'],
                  'reserved_pool_did_not_increase': after['pool_total_bytes'] <= before['pool_total_bytes'],
                  'only_unused_blocks_released': after['pool_total_bytes'] >= after['pool_used_bytes']}
        self.flushes.append({'step': int(step), 'phase': phase, 'before': before, 'after': after,
                             'pool_bytes_released': before['pool_total_bytes']-after['pool_total_bytes'],
                             'passed': all(checks.values()), 'checks': checks})
        self.persist()
        if not all(checks.values()): raise RuntimeError(f'PoolFlushFix1 invariant failure: {checks}')


    def verify_candidate(self, record: Mapping[str, Any], ranks: list[dict[str, Any]]) -> None:
        validate_inherited_authority(self.reference)
        step = int(record['step'])
        if step != START_STEP + len(self.validated_steps) + 1 or step > END_STEP:
            raise RuntimeError('PoolFlushFix1 continuation step order mismatch')
        actual = [(int(f['step']),f['phase']) for f in self.flushes]
        expected = [(s,p) for s in range(START_STEP+1,step+1) for p in PHASES]
        if actual != expected or not all(f['passed'] for f in self.flushes):
            raise RuntimeError('PoolFlushFix1 missing/inconsistent flush before commitment')
        self.validated_steps.append(step)
        self.persist()


def audit(output: Path, report: Mapping[str, Any], reference: Mapping[str, Any]) -> dict[str, Any]:
    validate_inherited_authority(reference)
    payload = json.loads((output/'poolflush_replay.json').read_text())
    flushes = payload.get('flushes', [])
    steps = report.get('step_records', [])
    completed = int(steps[-1]['step']) if steps else START_STEP
    attempted = int(report.get('attempted_step',completed))
    possible = [(s,p) for s in range(START_STEP+1,attempted+1) for p in PHASES]
    actual = [(int(f['step']),f['phase']) for f in flushes]
    memory = report.get('memory_snapshots', [])
    checks = {
        'schema':payload.get('schema') == SCHEMA,
        'range':payload.get('start_step') == START_STEP and payload.get('end_step') == END_STEP
            and START_STEP <= completed <= attempted <= END_STEP,
        'inherited_authority':payload.get('inherited_replay_authority') == dict(reference),
        'historical_replay_not_fabricated':payload.get('replay_gate_inherited') is True
            and payload.get('new_gpu_replay_performed') is False,
        'ordered_flush_prefix':actual == possible[:len(actual)],
        'all_committed_steps_flushed':len(flushes) >= 4*(completed-START_STEP),
        'flushes_nonempty':bool(flushes),
        'flush_invariants':all(f.get('passed') is True
            and f['before']['pool_used_bytes'] == f['after']['pool_used_bytes']
            and f['after']['pool_total_bytes'] <= f['before']['pool_total_bytes']
            and f['after']['pool_total_bytes'] >= f['after']['pool_used_bytes']
            and f['pool_bytes_released'] == f['before']['pool_total_bytes']-f['after']['pool_total_bytes']
            for f in flushes),
        'pre_and_post_samples_in_resource_evidence':all(f['before'] in memory and f['after'] in memory for f in flushes),
        'validated_committed_sequence':payload.get('validated_steps') == [s['step'] for s in steps]
            == list(range(START_STEP+1,completed+1)),
        'declarations':payload.get('all_original_memory_samples_retained') is True and payload.get('arithmetic_kernels_changed') is False,
    }
    return {'passed':all(checks.values()), 'checks':checks, 'replay_gate_inherited':True,
            'new_gpu_replay_performed':False, 'inherited_replay_authority':dict(reference),
            'number_flushes':len(flushes),
            'maximum_pool_release_mib':max((f['pool_bytes_released']/2**20 for f in flushes),default=0.0)}
