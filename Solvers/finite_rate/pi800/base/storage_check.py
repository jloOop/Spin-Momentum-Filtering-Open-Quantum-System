"""Allocation-storage budget and read-only PC2 quota parsing.
QuotaFormatFix1: accept both observed Data Volume Limit/Soft Limit labels.
This continuation deliberately reduces checkpoint frequency and sizes its new storage envelope.
"""
from __future__ import annotations
from decimal import Decimal
import re


def parse_quota(text):
    """Parse one current PFS volume block; missing/ambiguous values fail closed.

    ``soft_limit_bytes`` is retained as a legacy API key for submit.py. It is
    an alias of the selected volume limit, not a claim that a field labelled
    simply ``Limit`` is a soft quota. If both labels occur, use the smaller
    numeric limit, and retain the actual labels in the returned evidence.
    """
    lines=text.splitlines()
    headings=[i for i,line in enumerate(lines) if line.strip().startswith('PFS filesystem quota')]
    if len(headings)!=1:
        raise RuntimeError('Need exactly one PFS quota section in pc2status; no quota check was completed.')
    # Stop at the next blank line after the block begins, so a missing value
    # cannot be silently borrowed from another filesystem or project section.
    section=[]
    for line in lines[headings[0]+1:]:
        if not line.strip():
            if section:break
            continue
        section.append(line)
    scales={'TiB':2**40,'GiB':2**30,'MiB':2**20,'KiB':2**10,
            'TB':10**12,'GB':10**9,'MB':10**6,'KB':10**3,'B':1}
    pattern=r'Data\s+Volume\s+(Soft\s+Limit|Limit|Used)\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*(TiB|GiB|MiB|KiB|TB|GB|MB|KB|B)'
    values={}
    for line in section:
        m=re.fullmatch(pattern,line.strip())
        if m is None:
            if re.match(r'Data\s+Volume\s+(?:Soft\s+Limit|Limit|Used)\b',line.strip()):
                raise RuntimeError('Could not parse current PC2 quota line: '+repr(line)+'. Keep the pc2status output for review.')
            continue
        label=' '.join(m.group(1).split())
        if label in values:raise RuntimeError('Duplicate current PFS quota field: '+label)
        values[label]=Decimal(m.group(2))*scales[m.group(3)]
    limits={key:value for key,value in values.items() if key in ('Soft Limit','Limit')}
    if not limits or 'Used' not in values:
        raise RuntimeError('Missing current PFS Data Volume Limit/Soft Limit or Used. Keep the pc2status output for review.')
    limit_label,limit=min(limits.items(),key=lambda item:item[1])
    if limit<=0:raise RuntimeError('Nonpositive PFS volume limit; cannot authorize storage.')
    used=values['Used'];remaining=limit-used
    return {'soft_limit_bytes':int(limit),'limit_bytes':int(limit),'limit_label':limit_label,
            'reported_limits_bytes':{key:int(value) for key,value in limits.items()},
            'used_bytes':int(used),'remaining_bytes':int(remaining),
            'remaining_gib':float(remaining/Decimal(2**30)),
            'scope':'Parsed current PFS volume quota; smaller limit used if both labels occur. Printed quantities may be rounded; not a guarantee against simultaneous-job usage.'}


def estimate_storage(cfg,start=7200):
    g=cfg['gate'];D=cfg['physical']['dimension'];end=g['end_step'];stride=g['checkpoint_stride']
    cadence=sum(i%stride==0 or i==end for i in range(start+1,end+1))
    # Preserve cadence checkpoints, one intermediate clean stop, one atomic temporary,
    # and two full-state one-step A/B trials. Existing parent files are not copied.
    slots=cadence+4
    single=D*16*(g['rank_guard']+1)+16*2**20
    telemetry_allowance=16*2**30
    total=slots*single+telemetry_allowance+g['runtime_free_disk_floor_gib']*2**30
    return {'start_step':start,'target_step':end,'cadence_checkpoint_count':cadence,'conservative_full_state_slots':slots,
      'per_checkpoint_bytes_at_rank_guard':single,'extra_required_bytes':total,'extra_required_gib':total/2**30,
      'submission_free_space_gib':g['minimum_free_disk_gib'],'parent_factors_copied':False,
      'scope':'One allocation at declared rank guard; includes two trial checkpoints, clean stop and atomic temporary, and 32 GiB diagnostics/floor. Does not reserve space against other jobs.'}
