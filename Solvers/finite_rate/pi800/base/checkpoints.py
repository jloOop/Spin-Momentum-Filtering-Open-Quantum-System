"""Immutable same-rate checkpoints, all seven sectors, full from-zero ledgers."""
from __future__ import annotations
import os, math, shutil
from pathlib import Path
import numpy as np
from common import PACKAGE_DIR, save_npz, write_json, reserve_line, utc
from archive_tools import require,digest_file
from fresh_inputs import scientific_identity,verify_checkpoint

def write_checkpoint(output,state,histories,*,backend,cfg,all_rep_terms,all_event_terms,reason,sector_sources=None):
    step=state.completed_step;dest=output/f'checkpoint_step{step}';tmp=output/f'.checkpoint_step{step}.tmp'
    require(not dest.exists() and not tmp.exists() and not dest.is_symlink() and not tmp.is_symlink(),'Checkpoint collision')
    require(len(all_rep_terms)==2*step and len(all_event_terms)==step,'Incomplete checkpoint ledgers')
    require(math.fsum(all_rep_terms)==state.representation_ledger,'Representation rebase')
    require(math.fsum(all_event_terms)==state.event_first_crossing_ledger,'Event rebase')
    tmp.mkdir();D=cfg['physical']['dimension']
    try:
        for k in range(cfg['physical']['max_event_sector']+1):
            if sector_sources is not None:
                source=Path(sector_sources)/f'sector_{k}.npy'
                require(source.is_file() and not source.is_symlink(),'Invalid pinned sector source')
                shutil.copyfile(source,tmp/f'sector_{k}.npy')
                with (tmp/f'sector_{k}.npy').open('rb') as f:os.fsync(f.fileno())
                continue
            x=state.family.get(k)
            a=np.empty((D,0),dtype=np.complex128) if x is None else np.asarray(backend.to_cpu(x),dtype=np.complex128)
            with (tmp/f'sector_{k}.npy').open('xb') as f:
                np.save(f,a,allow_pickle=False);f.flush();os.fsync(f.fileno())
            del a
        with (tmp/'zero_state.npy').open('xb') as f:
            np.save(f,np.asarray(backend.to_cpu(state.zero_state),dtype=np.complex128),allow_pickle=False);f.flush();os.fsync(f.fileno())
        save_npz(tmp/'histories.npz',**histories)
        m={'schema':'task09-pi800-fromzero-checkpoint-v1','created_utc':utc(),'completed_step':step,
           'physical_time':step*cfg['physical']['dt'],'rate_lambda':cfg['physical']['rate_lambda'],'max_event_sector':6,
           'scientific_identity':scientific_identity(cfg),'driver_sha256':digest_file(PACKAGE_DIR/'pi800_run.py'),
           'package_name':cfg['package_name'],'checkpoint_reason':reason,'session_start_step':cfg['start']['step'],
           'origin_record_sha256':digest_file(output/'origin.json'),'origin_record':__import__('json').loads((output/'origin.json').read_text()),
           'representation_ledger':float(state.representation_ledger),'event_first_crossing_ledger':float(state.event_first_crossing_ledger),
           'cumulative_click':float(state.cumulative_click),'cumulative_zero_click':float(state.cumulative_zero_click),
           'cumulative_overflow_bound':float(state.cumulative_overflow_bound),'previous_overflow_intensity':float(state.previous_overflow_intensity),
           'forward_representation_terms':list(all_rep_terms),'forward_event_terms':list(all_event_terms),
           'reserve_policy':cfg['policy'],'reserve_line_after_completed_call':reserve_line(2*step,cfg),
           'sector_ranks':list(map(int,histories['sector_ranks'][-1])),'total_rank':int(histories['total_rank'][-1]),
           'zero_reference_solver':cfg['zero_solver'],
           'trace_restoration_applied':False,'future_borrowing':False,'physical_claim':False,'task10_eligible':False}
        write_json(tmp/'checkpoint_metadata.json',m)
        hashes={p.name:digest_file(p) for p in sorted(tmp.iterdir()) if p.is_file()}
        write_json(tmp/'checkpoint_manifest.json',{'algorithm':'SHA-256','files':hashes})
        verify_checkpoint(tmp,cfg,True)
        for p in tmp.iterdir():
            with p.open('rb') as f:os.fsync(f.fileno())
        require(not dest.exists(),'Checkpoint appeared during write');os.rename(tmp,dest)
        fd=os.open(output,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
        return {'step':step,'path':str(dest),'reason':reason,'metadata_sha256':hashes['checkpoint_metadata.json'],
                'manifest_sha256':digest_file(dest/'checkpoint_manifest.json'),'payload_bytes':sum(p.stat().st_size for p in dest.iterdir()),'verified':True}
    except Exception:
        # Only an uncommitted temporary directory created by this function is removable.
        if tmp.exists():shutil.rmtree(tmp)
        raise
