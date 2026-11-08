"""Storage and naming rules only; no changes to the numerical map or budget."""
from __future__ import annotations
import math

def required_free_gib(start: int, end: int=20000) -> int:
    # All remaining immutable stride200 checkpoints, two emergency checkpoints,
    # 16 GiB working floor and 64 GiB additional output/packaging headroom.
    scheduled = sum(s % 200 == 0 or s == end for s in range(start+1,end+1))
    maximum_checkpoint_bytes = 273000*16*(2600+1)+16*2**20
    required=(scheduled+2)*maximum_checkpoint_bytes/2**30+16+64
    return int(32*math.ceil(required/32))

def package_name(start: int) -> str:
    return f'Task09_Pi1600_{start}_To20000_PC2_H100_2026-09-12_v1_IO200'

def output_relative(start: int) -> str:
    return f'Task09_ES_G5P_PC2/4996.Pi1600_{start}_To20000_PC2_H100_RankGuard2600_NonAccepting_20260912_v1_IO200'

def result_prefix(start: int) -> str:
    token='600' if start==12000 else 'S'+str(start)
    return f'Task09_Pi1600_{token}_To1000_PC2_H100_v1_IO200_Result_'

def runtime_prefix(start: int) -> str:
    return result_prefix(start).replace('_Result_','_Run_')

def job_name(start: int) -> str:
    return 'T09P16T10I2' if start==12000 else 'T09P16I2S'+str(start)
