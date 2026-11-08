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
BASE = 'TASK09_PC2_PI1600_12000_TO20000_V1'


def config() -> dict:
    return plain_json((PACKAGE_DIR / 'CONFIG.json').read_bytes())


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
    pol = cfg['policy']; first, last = pol['start_call'], pol['end_call']
    require(isinstance(call, int) and first-1 <= call <= last,
            f'Compression call {call} outside prospective policy [{first-1},{last}]')
    with localcontext() as ctx:
        ctx.prec = 60
        initial = Decimal(pol['start_ledger_decimal'])
        final = Decimal(pol['final_ceiling_decimal'])
        if call == last: return float(final)
        return float(initial + (final-initial)*Decimal(call-first+1)/Decimal(last-first+1))


def history_prefix_equal(old: dict, new: dict) -> bool:
    return set(old) == set(new) and all(
        new[k].dtype == old[k].dtype and new[k].shape[1:] == old[k].shape[1:]
        and new[k].shape[0] >= old[k].shape[0]
        and np.array_equal(new[k][:old[k].shape[0]], old[k]) for k in old
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
