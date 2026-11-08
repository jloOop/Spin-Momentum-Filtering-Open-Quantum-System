"""Small I/O and policy layer; no state equation or numerical kernel."""
from __future__ import annotations
import hashlib, importlib.util, json, math, os, sys
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any
import numpy as np
from archive_tools import require, plain_json

PACKAGE_DIR = Path(__file__).resolve().parent
BASE = 'TASK09_PC2_PI3200_8849_PILOTGATED_V1'


def config() -> dict:
    # A selector for immutable declared roles, never arbitrary numerical overrides.
    phase = os.environ.get('TASK09_PHASE', 'candidate_pilot')
    require(phase in ('strict_pilot', 'candidate_pilot', 'continuation'), 'Unknown phase')
    if phase == 'continuation':
        path = PACKAGE_DIR / 'PREPARED/PROMOTION/CONFIG.json'
        require(path.is_file() and not path.is_symlink(), 'No immutable approved-pilot continuation capsule')
    else:
        path = PACKAGE_DIR / 'CONFIGS' / (phase + '.json')
    cfg = plain_json(path.read_bytes())
    require(cfg.get('phase') == phase, 'Phase/config mismatch')
    return cfg


def utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def json_value(v: Any):
    if isinstance(v, Path): return str(v)
    if isinstance(v, np.ndarray): return v.tolist()
    if isinstance(v, np.generic): return v.item()
    raise TypeError(type(v).__name__)


def write_json(path: Path, obj: Any) -> None:
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, sort_keys=True, allow_nan=False, default=json_value)
        f.write('\n')
    os.replace(tmp, path)


def save_npz(path: Path, **arrays) -> None:
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('wb') as f: np.savez_compressed(f, **arrays)
    os.replace(tmp, path)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f'Cannot import {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def reserve_line(call: int, cfg: dict | None = None) -> float:
    cfg = config() if cfg is None else cfg
    pol = cfg['policy']
    require(isinstance(call, int), 'Compression call must be an integer')
    if pol.get('kind') == 'fixed_cap_frontloaded_remaining_allowance':
        j0 = pol['historical_segment_last_call']
        if call <= j0:
            return reserve_line(call, {'policy': pol['historical_segment']})
        require(pol['start_call'] <= call <= pol['end_call'], 'Outside prospective policy')
        with localcontext() as ctx:
            ctx.prec = 60
            c0 = Decimal(pol['start_ledger_decimal'])
            final = Decimal(pol['final_ceiling_decimal'])
            fraction = Decimal(pol['frontload_numerator']) / Decimal(pol['frontload_denominator'])
            require(Decimal(0) <= fraction < Decimal(1), 'Invalid frontloaded fraction')
            if call == pol['end_call']:
                return float(final)
            progress = Decimal(call-j0) / Decimal(pol['remaining_calls'])
            return float(c0 + (final-c0)*(fraction + (1-fraction)*progress))
    if 'historical_segment' not in pol:
        # Retained for independent reduced fixtures and the original policy comparison.
        first, last = pol['start_call'], pol['end_call']
        require(first-1 <= call <= last, 'Compression call outside policy')
        with localcontext() as ctx:
            ctx.prec = 60
            initial, final = Decimal(pol['start_ledger_decimal']), Decimal(pol['final_ceiling_decimal'])
            if call == last: return float(final)
            return float(initial + (final-initial)*Decimal(call-first+1)/Decimal(last-first+1))
    if call <= pol['historical_segment_last_call']:
        return reserve_line(call, {'policy': pol['historical_segment']})
    require(pol['start_call'] <= call <= pol['end_call'], 'Compression call outside new segment')
    with localcontext() as ctx:
        ctx.prec = 60
        return float(Decimal(pol['start_ledger_decimal']) +
            Decimal(pol['slope_numerator_decimal'])*Decimal(call-pol['start_call']+1)/
            Decimal(pol['slope_denominator_calls']))


def history_prefix_equal(old: dict, new: dict) -> bool:
    return set(old) == set(new) and all(
        new[k].dtype == old[k].dtype and new[k].shape[1:] == old[k].shape[1:]
        and new[k].shape[0] >= old[k].shape[0]
        and new[k][:old[k].shape[0]].tobytes(order='C') == old[k].tobytes(order='C') for k in old
    )


def cumulative(legacy: float, terms) -> float:
    return float(math.fsum([float(legacy), *(float(x) for x in terms)]))


class ControlledStop(RuntimeError):
    def __init__(self, classification: str, detail: dict):
        super().__init__(classification)
        self.classification = classification
        self.detail = detail


def all_true(checks: dict, context: str) -> None:
    require(bool(checks) and all(v is True for v in checks.values()), f'{context}: {checks}')
