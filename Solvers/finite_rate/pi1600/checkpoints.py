"""Append-only checkpoints carrying the complete original ordered ledger history."""
from __future__ import annotations
import math, os, shutil
from pathlib import Path
import numpy as np
from archive_tools import digest_file, require
from common import PACKAGE_DIR, cumulative, reserve_line, save_npz, utc, write_json
from memory_components import block_trace_npy


def write_checkpoint(output: Path, state, histories: dict, *, backend, cfg: dict,
                     all_rep_terms: list, all_event_terms: list, reason: str) -> dict:
    step=state.completed_step;dest=output/f'checkpoint_step{step}';tmp=output/f'.checkpoint_step{step}.tmp'
    require(not dest.exists() and not dest.is_symlink() and not tmp.exists() and not tmp.is_symlink(),'Checkpoint collision')
    legacy=cfg['legacy'];require(len(all_rep_terms)==2*(step-legacy['step']) and
                              len(all_event_terms)==step-legacy['step'],'Checkpoint full ledger length')
    require(cumulative(legacy['representation_ledger'],all_rep_terms)==state.representation_ledger,
            'Checkpoint representation ledger reset/rebase')
    require(cumulative(legacy['event_ledger'],all_event_terms)==state.event_first_crossing_ledger,'Checkpoint event ledger reset')
    tmp.mkdir();D=cfg['physical']['dimension'];hz=cfg['physical']['h_z'];traces=[];ranks=[]
    try:
        for k in range(5):
            x=state.family.get(k)
            cpu=np.empty((D,0),np.complex128) if x is None else np.asarray(backend.to_cpu(x),dtype=np.complex128)
            with (tmp/f'sector_{k}.npy').open('xb') as f:
                np.save(f,cpu,allow_pickle=False);f.flush();os.fsync(f.fileno())
            rank=int(cpu.shape[1]);del cpu
            item=block_trace_npy(tmp/f'sector_{k}.npy',hz)
            require(tuple(item['shape'])==(D,rank) and item['dtype']=='complex128' and item['finite'],'Written factor invalid')
            require(abs(item['trace']-float(histories['sector_traces'][-1,k]))<=5e-12,'Written sector trace mismatch')
            ranks.append(rank);traces.append(item['trace'])
        zero=np.asarray(backend.to_cpu(state.zero_state),dtype=np.complex128)
        with (tmp/'zero_state.npy').open('xb') as f:
            np.save(f,zero,allow_pickle=False);f.flush();os.fsync(f.fileno())
        del zero
        za=block_trace_npy(tmp/'zero_state.npy',hz)
        require(za['finite'] and za['dtype']=='complex128' and tuple(za['shape'])==(D,1),'Written zero state invalid')
        require(abs(math.fsum(traces)-float(histories['positive_survival'][-1]))<=5e-12 and
                abs(za['trace']-float(histories['zero_survival'][-1]))<=5e-12,'Written checkpoint trace mismatch')
        save_npz(tmp/'histories.npz',**histories)
        meta={
            'schema':'task09-pi1600-spectral-continuation-checkpoint-v1','created_utc':utc(),
            'completed_step':step,'physical_time':step*cfg['physical']['dt'],'rate_lambda':cfg['physical']['rate_lambda'],
            'max_event_sector':4,'source_sha256':digest_file(PACKAGE_DIR/'pi1600_continue.py'),
            'package_name':cfg['package_name'],'checkpoint_reason':reason,
            'continuation_start_step':cfg['start']['step'],'parent_result_sha256':cfg['parent_result']['sha256'],
            'parent_checkpoint_payload_hashes':cfg['checkpoint_payloads'],
            'parent_source_sha256':cfg['parent_result']['driver_sha256'],
            'legacy_prefix_origin':legacy,
            'representation_ledger':float(state.representation_ledger),
            'legacy_prefix_representation_ledger':legacy['representation_ledger'],
            'legacy_prefix_ledger_convention':legacy['representation_ledger_convention'],
            'legacy_event_ledger':legacy['event_ledger'],
            'forward_representation_terms':list(all_rep_terms),'forward_event_terms':list(all_event_terms),
            'inherited_forward_representation_term_count':cfg['start']['inherited_representation_term_count'],
            'inherited_forward_event_term_count':cfg['start']['inherited_event_term_count'],
            'reserve_policy':cfg['policy'],'reserve_line_after_completed_call':reserve_line(2*step,cfg),
            'reserve_policy_adopted_through_call':2*step,'reserve_policy_adopted_beyond_completed_call':False,
            'event_first_crossing_ledger':float(state.event_first_crossing_ledger),
            'cumulative_click':float(state.cumulative_click),'cumulative_zero_click':float(state.cumulative_zero_click),
            'cumulative_overflow_bound':float(state.cumulative_overflow_bound),
            'previous_overflow_intensity':float(state.previous_overflow_intensity),
            'sector_ranks':{str(k):r for k,r in enumerate(ranks)},'total_rank':sum(ranks),
            'sector_traces':{str(k):v for k,v in enumerate(traces)},
            'positive_survival':math.fsum(traces),'zero_survival':za['trace'],
            'empty_sector_encoding':'zero retained sectors stored as complex128 arrays of shape (D,0)',
            'trace_restoration_applied':False,'future_borrowing':False,'automatic_resume':False,
            'production_authorized':False,'physical_claim':False,'task10_eligible':False,
            'one_time_implementation_bridge_parent_sha256':cfg['parent_result']['implementation_equivalence_sha256'],
            'one_time_implementation_bridge_repeated':False}
        write_json(tmp/'checkpoint_metadata.json',meta)
        hashes={f.name:digest_file(f) for f in sorted(tmp.iterdir()) if f.is_file()}
        write_json(tmp/'checkpoint_manifest.json',{'algorithm':'SHA-256','files':hashes})
        for f in tmp.iterdir():
            with f.open('rb') as handle:os.fsync(handle.fileno())
        require(not dest.exists() and not dest.is_symlink(),'Checkpoint destination appeared during write')
        os.rename(tmp,dest)
        fd=os.open(output,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
        return {'step':step,'path':str(dest),'reason':reason,'metadata':meta,
                'metadata_sha256':hashes['checkpoint_metadata.json'],'manifest_sha256':digest_file(dest/'checkpoint_manifest.json'),
                'payload_hashes':hashes,'integrated_trace_checks_passed':True,
                'payload_bytes':sum(f.stat().st_size for f in dest.iterdir())}
    except Exception:
        shutil.rmtree(tmp,ignore_errors=True)
        raise
