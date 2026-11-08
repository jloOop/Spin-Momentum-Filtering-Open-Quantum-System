"""Operational stops only. No rank approximation or mathematical-budget changes."""
from __future__ import annotations
import math, os, shutil, signal, time, subprocess
from pathlib import Path
from common import ControlledStop

class ResourceGuard:
    def __init__(self, root: Path, cfg: dict, started: float):
        self.root,self.cfg,self.started=root,cfg,started
        # Count CPU input hashing and the GPU trial inside the same Slurm allocation.
        # This is operational only; no numerical time or state is changed.
        epoch=os.environ.get('TASK09_PC2_PI800_ALLOCATION_START_EPOCH')
        self.pre_driver_seconds=0.
        if epoch is not None:
            value=float(epoch)
            if not math.isfinite(value) or value<=0 or value>time.time()+2:
                raise ValueError('Invalid allocation start epoch')
            self.pre_driver_seconds=max(0.,time.time()-value)
            self.started-=self.pre_driver_seconds
        self.step_costs=[];self.checkpoint_costs=[];self.records=[];self.stop_signal=None
        self.handlers={}
        self.last_quota_time=None;self.last_quota=None
    def install_signals(self):
        for name in ('SIGUSR1','SIGTERM','SIGINT'):
            sig=getattr(signal,name,None)
            if sig is not None:
                self.handlers[sig]=signal.getsignal(sig)
                signal.signal(sig,self._request)
    def restore_signals(self):
        for sig,handler in self.handlers.items():signal.signal(sig,handler)
    def _request(self, sig, frame):
        # No exception in the middle of a physical update. Stop at a safe boundary.
        self.stop_signal=int(sig)
    def checkpoint_bytes(self, rank: int) -> int:
        # Raw complex128 factor arrays, one zero column, headers and conservative metadata/history headroom.
        return int(self.cfg['physical']['dimension']*16*(rank+1)+16*2**20)
    def before_step(self, step: int, rank: int):
        g=self.cfg['gate'];elapsed=time.perf_counter()-self.started
        predicted_step=max(g['minimum_step_reserve_seconds'],
                           g['step_prediction_safety_factor']*max(self.step_costs[-20:],default=10.))
        predicted_checkpoint=max(g['checkpoint_prediction_floor_seconds'],
                                 2*max(self.checkpoint_costs[-5:],default=0.))
        free=shutil.disk_usage(self.root).free
        quota=None
        # Local reduced tests do not call a cluster service. In a genuine PC2
        # allocation, missing or failed quota reads are clean operational stops.
        live_pc2=(self.root==Path('[ARCHIVE_PATH]'))
        if live_pc2:
            if self.last_quota_time is None or time.monotonic()-self.last_quota_time>=g['quota_recheck_seconds']:
                try:
                    from storage_check import parse_quota
                    q=subprocess.run(['pc2status'],text=True,capture_output=True,timeout=g['quota_command_timeout_seconds'])
                    if q.returncode!=0:raise RuntimeError(q.stderr or q.stdout)
                    self.last_quota=parse_quota(q.stdout);self.last_quota_time=time.monotonic()
                except Exception as error:
                    raise ControlledStop('QUOTA_QUERY_RESOURCE_STOP',{'step':step,'error':str(error)})
            quota=self.last_quota
            free=min(free,max(0,quota['remaining_bytes']))
        disk_required=int(g['runtime_free_disk_floor_gib']*2**30+
                          g['checkpoint_headroom_count']*self.checkpoint_bytes(g['rank_guard']))
        record={'step':int(step),'rank':int(rank),'elapsed_seconds':float(elapsed),
            'pre_driver_allocation_seconds':self.pre_driver_seconds,
            'step_reserve_seconds':float(predicted_step),'checkpoint_reserve_seconds':float(predicted_checkpoint),
            'free_filesystem_bytes':int(free),'required_filesystem_bytes':disk_required,
            'signal':self.stop_signal,'wall_guard_seconds':g['wall_guard_seconds'],'quota':quota}
        # This is a conservative empirical pre-allocation screen, not a mathematical
        # GPU-memory theorem. The original measured-memory gate also remains.
        forecast=None
        if self.cfg['physical']['dimension']==273000:
            forecast=g['predictive_gpu_fixed_mib']+g['predictive_gpu_mib_per_rank']*(rank+g['predictive_gpu_rank_increment_allowance'])
            record['predicted_gpu_peak_mib']=forecast
            record['gpu_prediction_scope']='Conservative envelope of job2965353; not full-horizon certification'
        self.records.append(record)
        if forecast is not None and forecast>=g['memory_guard_mib']:
            raise ControlledStop('PREDICTIVE_GPU_MEMORY_RESOURCE_GUARD',record)
        if self.stop_signal is not None or (self.root/self.cfg['output_relative']/'STOP_REQUEST').exists():
            raise ControlledStop('USER_OR_SCHEDULER_RESOURCE_STOP',record)
        if elapsed+predicted_step+predicted_checkpoint>=g['wall_guard_seconds']:
            raise ControlledStop('PREDICTIVE_WALLTIME_RESOURCE_GUARD',record)
        if free<disk_required:
            raise ControlledStop('FILESYSTEM_RESOURCE_GUARD',record)
    def before_checkpoint(self, rank: int):
        free=shutil.disk_usage(self.root).free
        required=self.checkpoint_bytes(rank)+int(self.cfg['gate']['runtime_free_disk_floor_gib']*2**30)
        # Called after a committed state. Failure preserves the earlier immutable checkpoint.
        if free<required:
            raise ControlledStop('CHECKPOINT_FILESYSTEM_RESOURCE_GUARD',{'free_bytes':int(free),'required_bytes':required})
