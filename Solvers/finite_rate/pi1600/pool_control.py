"""Unchanged PoolFlushFix1 allocator operation; new pi/1600 gate bookkeeping."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from common import config
PHASES = ('first_before_analysis','first_before_compression','second_before_analysis','second_before_compression')
class Controller:
    def __init__(self, *, output, backend, memory, snapshot, write_json):
        self.output, self.backend, self.memory = output, backend, memory
        self.snapshot, self.write_json = snapshot, write_json
        self.flushes = []
        self.persist()
    def persist(self):
        self.write_json(self.output/'pool_flush.json', {
            'schema':'pi/1600-poolflush-v1','flushes':self.flushes,
            'scope':'allocator operation unchanged; no fabricated replay of quarter-rate states',
            'all_original_memory_samples_retained':True})

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
