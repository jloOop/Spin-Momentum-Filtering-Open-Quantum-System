#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
07_environmental_response_case_loader.py
========================================

Independent read-only per-case auditor, reducer, and share-packager for one
completed Task-07 environmental-response solver case.

This is NOT the final aggregate Task-08 campaign loader.  It is the complete
per-case loader used before sharing an individual Task-07 result.  It:

* discovers one Task-07 case from its configuration JSON;
* verifies the copied solver source, deterministic configuration hash, solver
  output hashes, runtime record, run status, and shared stage manifest;
* independently reconstructs the saved low-rank response, jump and
  anticommutator kernels, causal structure, source-trace identities, reduced
  full-tangent benchmark, integrated susceptibilities, scalar-null controls,
  and insertion-grid comparison;
* distinguishes a genuine integrity/scientific failure from a deterministic
  rerun or external-family control that is merely pending;
* writes compact NumPy and CSV reductions for rapid inspection;
* creates one complete full-share ZIP and one smaller diagnostic ZIP without
  importing/rerunning the solver, copying Task-05 archives, or packaging
  temporary wave-function data.

Normal use
----------
Place this loader in the completed Task-07 case directory, start Jupyter or a
terminal in that directory, and run the saved file.  No path edit is normally
required.

The directory is expected to contain files such as

    CASE_configuration.json
    CASE_reference_audit.json
    CASE_operator_audit.json
    CASE_response_audit.json
    CASE_times.npy
    CASE_insertion_times.npy
    CASE_chi_survival.npy
    CASE_chi_click_density.npy
    CASE_integrated_response.json
    CASE_kernel_summary.npz
    CASE_source_insertion_summary.npz
    CASE_full_tangent_benchmark.npz
    CASE_runtime_metrics.json
    CASE_run_status.json
    CASE_output_hashes.json
    CASE_07_environmental_response_solver.py
    stage_manifest.json

Exit status
-----------
0 : independent per-case PASS and deterministic same-prefix rerun PASS
3 : all available local data pass, but rerun or external family controls remain pending
2 : available data contain an integrity or scientific gate failure
1 : loader execution or I/O failure
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import math
import os
import shutil
import sys
import traceback
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence, Tuple

import numpy as np


# =============================================================================
# MANUAL LOCATION CONFIGURATION
# =============================================================================
# Normal case-directory execution requires no edits.
CASE_DIRECTORY_OVERRIDE = None       # e.g. Path("[ARCHIVE_PATH]")
CASE_PREFIX_OVERRIDE = None          # e.g. "scalar_factorized_downward_omega100_..."
OUTPUT_DIRECTORY_OVERRIDE = None     # normally the same directory as the raw case
LOADER_SOURCE_PATH_OVERRIDE = None   # normally unnecessary

# Include the solver stdout/log in the full and diagnostic share ZIPs when they
# are present. They are operational rather than deterministic scientific
# products, but they are useful for diagnosing long GPU runs.
INCLUDE_STDOUT_AND_LOGS = True

# Current Task-07 solver versions write a separate runtime_metrics.json that is
# intentionally excluded from deterministic scientific hashes.  The loader
# requires and packages it whenever the solver declares it in output_contract.
REQUIRE_DECLARED_RUNTIME_METRICS = True
# =============================================================================


# =============================================================================
# FROZEN TASK-07 CASE-LOADER CONVENTIONS
# =============================================================================
LOADER_STAGE = "07_environmental_response_case_loader"
LOADER_VERSION = "2026-08-05-task07-independent-case-loader-v3-dual-reference-pilot-safe-json"
TASK07_STAGE_NAME = "07_environmental_response_solver"

T_CUT_DEFAULT = 3.6
OPERATOR_TOL = 1.0e-12
ARRAY_ABS_TOL = 5.0e-12
ARRAY_REL_TOL = 5.0e-12
TRUE_RESIDUAL_TOL = 1.0e-8
SOURCE_TRACE_ABS_TOL = 5.0e-11
LAUNCH_SOURCE_ABS_TOL = 1.0e-12
TANGENT_CLOSURE_ABS_TOL = 5.0e-10
TANGENT_CLOSURE_REL_TOL = 1.0e-7
KERNEL_CLOSURE_ABS_TOL = 5.0e-8
SCALAR_KERNEL_ABS_TOL = 5.0e-9
SCALAR_RESPONSE_ABS_TOL = 1.0e-8
BENCHMARK_ABS_TOL = 5.0e-10
BENCHMARK_REL_TOL = 1.0e-7
INSERTION_CONVERGENCE_REL_TOL = 5.0e-2
INSERTION_CONVERGENCE_ABS_TOL = 5.0e-9

CORE_REQUIRED_SOLVER_SUFFIXES = (
    "configuration.json",
    "reference_audit.json",
    "operator_audit.json",
    "response_audit.json",
    "times.npy",
    "insertion_times.npy",
    "chi_survival.npy",
    "chi_click_density.npy",
    "integrated_response.json",
    "kernel_summary.npz",
    "source_insertion_summary.npz",
    "full_tangent_benchmark.npz",
    "run_status.json",
    "output_hashes.json",
    "07_environmental_response_solver.py",
)

CURRENT_RUNTIME_SOLVER_SUFFIX = "runtime_metrics.json"
CURRENT_CLOSURE_PILOT_SUFFIX = "closure_pilot_audit.json"

OPTIONAL_SOLVER_SUFFIXES = (
    "stdout.txt",
    "simulation_log.txt",
    "failure.json",
)

KERNEL_REQUIRED_KEYS = {
    "insertion_steps",
    "insertion_times",
    "panel_durations",
    "kernel_jump_probability",
    "kernel_anticommutator_probability",
    "kernel_total_probability",
    "kernel_click_density_jump",
    "kernel_click_density_anticommutator",
    "kernel_click_density_total",
    "kernel_survival",
    "chi_panel_probability",
    "coarse_node_indices",
    "coarse_times",
    "coarse_kernel_probability",
    "coarse_kernel_survival",
    "coarse_chi_survival",
    "coarse_chi_panel_probability",
    "interpretation",
}

SOURCE_REQUIRED_KEYS = {
    "insertion_steps",
    "insertion_times",
    "jump_norm2",
    "anti_expectation",
    "trace_terms",
    "trace_total",
    "activity_total",
    "reference_survival",
    "reference_s_down",
    "reference_s_up",
    "reference_s_phi",
    "reference_top_shell",
    "branch_labels",
    "interpretation",
}

BENCHMARK_REQUIRED_KEYS = {
    "times",
    "full_chi_survival",
    "full_chi_panel_probability",
    "low_rank_chi_survival",
    "low_rank_chi_panel_probability",
    "low_rank_kernel_probability",
    "low_rank_kernel_survival",
}


# =============================================================================
# DATA CLASSES
# =============================================================================
@dataclass(frozen=True)
class CaseIdentity:
    propagator_type: str
    environment_direction: str
    omega: float
    initial_mode: str
    n_shell: int
    dt: float
    t_final: float
    insertion_dt: float

    def canonical_prefix(self) -> str:
        return canonical_task07_prefix(
            self.propagator_type,
            self.environment_direction,
            self.omega,
            self.initial_mode,
            self.n_shell,
            self.dt,
            self.t_final,
            self.insertion_dt,
        )


# =============================================================================
# BASIC UTILITIES
# =============================================================================
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _nonfinite_kind(value: float) -> str:
    if math.isnan(value):
        return "NaN"
    return "+Infinity" if value > 0.0 else "-Infinity"


def json_safe(
    value: Any,
    *,
    _path: str = "$",
    _nonfinite: Optional[List[Dict[str, Any]]] = None,
) -> Any:
    """Convert nested loader products to strict JSON-compatible objects.

    Non-finite values are never emitted as JSON numbers.  They are replaced by
    ``null`` and, when a collector is supplied, their exact paths are recorded.
    Scientific arrays are audited for finiteness independently; this conversion
    is a serialization safety net, not a numerical acceptance rule.
    """
    if isinstance(value, Mapping):
        return {
            str(key): json_safe(
                item,
                _path=f"{_path}.{key}",
                _nonfinite=_nonfinite,
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [
            json_safe(
                item,
                _path=f"{_path}[{index}]",
                _nonfinite=_nonfinite,
            )
            for index, item in enumerate(value)
        ]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist(), _path=_path, _nonfinite=_nonfinite)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, (np.floating, float)):
        result = float(value)
        if not math.isfinite(result):
            if _nonfinite is not None:
                _nonfinite.append(
                    {"path": _path, "kind": _nonfinite_kind(result)}
                )
            return None
        return result
    return value


def json_safe_with_report(value: Any) -> Tuple[Any, List[Dict[str, Any]]]:
    replacements: List[Dict[str, Any]] = []
    safe = json_safe(value, _nonfinite=replacements)
    if replacements and isinstance(safe, dict):
        safe = dict(safe)
        safe["_serialization_nonfinite_replacements"] = {
            "count": len(replacements),
            "values": replacements,
            "interpretation": (
                "Non-finite loader-derived values were replaced by JSON null. "
                "The independent finiteness check must fail for any required "
                "scientific metric or raw array that generated such a value."
            ),
        }
    return safe, replacements


def find_nonfinite_paths(
    value: Any,
    *,
    path: str = "$",
    limit: int = 256,
) -> List[Dict[str, Any]]:
    """Locate non-finite scalars without expanding large arrays elementwise."""
    records: List[Dict[str, Any]] = []

    def visit(item: Any, current: str) -> None:
        if len(records) >= limit:
            return
        if isinstance(item, Mapping):
            for key, child in item.items():
                visit(child, f"{current}.{key}")
            return
        if isinstance(item, (list, tuple)):
            for index, child in enumerate(item):
                visit(child, f"{current}[{index}]")
            return
        if isinstance(item, np.ndarray):
            array = np.asarray(item)
            if array.dtype.kind in "fc":
                mask = ~np.isfinite(array)
                count = int(np.count_nonzero(mask))
                if count:
                    first = tuple(int(i) for i in np.argwhere(mask)[0])
                    sample = float(array[first])
                    records.append(
                        {
                            "path": current,
                            "kind": _nonfinite_kind(sample),
                            "array_nonfinite_count": count,
                            "first_index": list(first),
                        }
                    )
            return
        if isinstance(item, (np.floating, float)):
            number = float(item)
            if not math.isfinite(number):
                records.append(
                    {"path": current, "kind": _nonfinite_kind(number)}
                )

    visit(value, path)
    return records


def finite_float(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def finite_nonnegative(value: Any) -> bool:
    number = finite_float(value)
    return bool(number is not None and number >= 0.0)

def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(chunk_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def sha256_json(payload: Mapping[str, Any]) -> str:
    safe, replacements = json_safe_with_report(payload)
    if replacements:
        raise ValueError(
            "Cannot construct a scientific JSON hash from non-finite values: "
            f"{replacements[:8]}"
        )
    encoded = json.dumps(
        safe,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    safe, _replacements = json_safe_with_report(payload)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(safe, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    os.replace(tmp, path)

def atomic_write_text(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def atomic_copy(source: Path, destination: Path) -> None:
    if source.resolve() == destination.resolve():
        return
    tmp = destination.with_name(destination.name + ".tmp")
    shutil.copy2(source, tmp)
    os.replace(tmp, destination)


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise TypeError(f"Expected JSON object in {path}")
    return payload


def load_npy(path: Path) -> np.ndarray:
    return np.load(require_file(path), allow_pickle=False)


def load_npz(path: Path) -> Dict[str, np.ndarray]:
    with np.load(require_file(path), allow_pickle=False) as archive:
        return {name: np.asarray(archive[name]) for name in archive.files}


def require_file(path: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"Required file is missing: {path}")
    return path


def all_finite(*arrays: np.ndarray) -> bool:
    return all(np.all(np.isfinite(np.asarray(array))) for array in arrays)


def dense_max_abs(array: np.ndarray) -> float:
    array = np.asarray(array)
    return 0.0 if array.size == 0 else float(np.max(np.abs(array)))


def max_abs_difference(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left)
    right = np.asarray(right)
    if left.shape != right.shape:
        return float("inf")
    return dense_max_abs(left - right)


def scalar_close(
    left: float,
    right: float,
    *,
    rtol: float = ARRAY_REL_TOL,
    atol: float = ARRAY_ABS_TOL,
) -> bool:
    return bool(np.isclose(float(left), float(right), rtol=rtol, atol=atol))


def case_file(stage_dir: Path, prefix: str, suffix: str) -> Path:
    return stage_dir / f"{prefix}_{suffix}"


def declared_output_contract(configuration: Mapping[str, Any]) -> Tuple[str, ...]:
    raw = configuration.get("output_contract", ())
    if not isinstance(raw, (list, tuple)):
        raise TypeError("Task-07 configuration output_contract must be a list or tuple")
    contract = tuple(str(item) for item in raw)
    if len(contract) != len(set(contract)):
        raise ValueError("Task-07 configuration output_contract contains duplicates")
    return contract


def required_solver_suffixes(configuration: Mapping[str, Any]) -> Tuple[str, ...]:
    """Return the exact required products declared by the audited solver.

    The v8 solver adds a deterministic ``closure_pilot_audit.json`` and a
    nondeterministic ``runtime_metrics.json``.  Legacy Task-07 cases remain
    readable because these files are required only when declared in the saved
    output contract.
    """
    contract = declared_output_contract(configuration)
    required = list(CORE_REQUIRED_SOLVER_SUFFIXES)
    for suffix in (CURRENT_CLOSURE_PILOT_SUFFIX, CURRENT_RUNTIME_SOLVER_SUFFIX):
        if suffix in contract and suffix not in required:
            required.append(suffix)
    return tuple(required)

def expected_insertion_grid(
    configuration: Mapping[str, Any],
) -> Tuple[np.ndarray, np.ndarray]:
    """Reconstruct the solver's exact insertion grid, including a final stub.

    The final observation time need not be an integer multiple of INSERTION_DT.
    The solver appends ``num_steps`` when the regular stride does not land on
    the final state node; the loader reproduces that rule exactly.
    """
    dt = float(configuration["dt"])
    t_final = float(configuration["T_final"])
    num_steps = int(configuration.get("num_steps", round(t_final / dt)))
    stride = int(
        configuration.get(
            "insertion_stride_steps",
            round(float(configuration["insertion_dt"]) / dt),
        )
    )
    if num_steps < 1 or stride < 1:
        raise ValueError("Invalid num_steps or insertion_stride_steps in configuration")
    if not np.isclose(num_steps * dt, t_final, rtol=0.0, atol=1.0e-12):
        raise ValueError("Configuration T_final/DT is not integral")
    if not np.isclose(
        stride * dt,
        float(configuration["insertion_dt"]),
        rtol=0.0,
        atol=1.0e-12,
    ):
        raise ValueError("Configuration INSERTION_DT is not an integer multiple of DT")
    steps = list(range(0, num_steps + 1, stride))
    if steps[-1] != num_steps:
        steps.append(num_steps)
    step_array = np.asarray(steps, dtype=np.int64)
    times = step_array.astype(np.float64) * dt
    return step_array, times


def _number_token(value: float) -> str:
    numeric = float(value)
    if numeric.is_integer():
        return str(int(numeric))
    mantissa, exponent = f"{numeric:.12e}".split("e")
    mantissa = mantissa.rstrip("0").rstrip(".").replace(".", "p")
    return f"{mantissa}e{int(exponent)}"


def canonical_task07_prefix(
    propagator_type: str,
    direction: str,
    omega: float,
    initial_mode: str,
    n_shell: int,
    dt: float,
    t_final: float,
    insertion_dt: float,
) -> str:
    return (
        f"{propagator_type}_{direction}_omega{_number_token(omega)}_"
        f"mode{initial_mode}_N{int(n_shell)}_dt{_number_token(dt)}_"
        f"T{_number_token(t_final)}_ins{_number_token(insertion_dt)}"
    )


def identity_from_configuration(configuration: Mapping[str, Any]) -> CaseIdentity:
    return CaseIdentity(
        propagator_type=str(configuration["propagator_type"]),
        environment_direction=str(configuration["environment_direction"]),
        omega=float(configuration["omega"]),
        initial_mode=str(configuration["initial_mode"]),
        n_shell=int(configuration["N_shell"]),
        dt=float(configuration["dt"]),
        t_final=float(configuration["T_final"]),
        insertion_dt=float(configuration["insertion_dt"]),
    )


def flatten_boolean_checks(prefix: str, value: Any, output: MutableMapping[str, bool]) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            flatten_boolean_checks(child, item, output)
    elif isinstance(value, (bool, np.bool_)):
        output[prefix] = bool(value)


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: json_safe(row.get(name, "")) for name in fieldnames})
    os.replace(tmp, path)


def create_zip(zip_path: Path, files: Sequence[Path]) -> Dict[str, Any]:
    """Create and verify one explicit flat share ZIP.

    Already-compressed NPZ/ZIP products are stored without a second expensive
    deflate pass.  Text, JSON, CSV, NPY, and source files are deflated.
    """
    tmp = zip_path.with_name(zip_path.name + ".tmp")
    seen: set[str] = set()
    expected: Dict[str, str] = {}
    with zipfile.ZipFile(tmp, "w") as archive:
        for path in files:
            if not path.is_file() or path.name in seen:
                continue
            seen.add(path.name)
            expected[path.name] = sha256_file(path)
            compress_type = (
                zipfile.ZIP_STORED
                if path.suffix.lower() in {".npz", ".zip"}
                else zipfile.ZIP_DEFLATED
            )
            archive.write(
                path,
                arcname=path.name,
                compress_type=compress_type,
                compresslevel=(None if compress_type == zipfile.ZIP_STORED else 6),
            )
    os.replace(tmp, zip_path)

    with zipfile.ZipFile(zip_path, "r") as archive:
        names = archive.namelist()
        duplicate_names = sorted({name for name in names if names.count(name) > 1})
        actual_names = set(names)
        expected_names = set(expected)
        member_hashes: Dict[str, str] = {}
        for name in sorted(actual_names):
            digest = hashlib.sha256()
            with archive.open(name, "r") as handle:
                while True:
                    block = handle.read(8 * 1024 * 1024)
                    if not block:
                        break
                    digest.update(block)
            member_hashes[name] = digest.hexdigest()
        hashes_match = bool(
            actual_names == expected_names
            and all(member_hashes.get(name) == digest for name, digest in expected.items())
        )
    return {
        "zip_path": str(zip_path),
        "zip_sha256": sha256_file(zip_path),
        "member_count": len(expected),
        "missing_members": sorted(expected_names - actual_names),
        "unexpected_members": sorted(actual_names - expected_names),
        "duplicate_members": duplicate_names,
        "all_member_hashes_match_sources": hashes_match,
    }


# =============================================================================
# SOURCE AND LOCATION RESOLUTION
# =============================================================================
def _current_ipython_cell_source() -> Optional[str]:
    try:
        from IPython import get_ipython as _get_ipython
    except ImportError:
        return None
    ipython = _get_ipython()
    if ipython is None:
        return None

    candidates: List[str] = []
    try:
        parent = ipython.get_parent()
        code = parent.get("content", {}).get("code", "")
        if isinstance(code, str):
            candidates.append(code)
    except Exception:
        pass
    try:
        history = getattr(ipython.history_manager, "input_hist_raw", ())
        for item in reversed(tuple(history)[-10:]):
            if isinstance(item, str):
                candidates.append(item)
    except Exception:
        pass

    markers = (
        "def run_case_loader",
        "07_environmental_response_case_loader.py",
        "Independent read-only per-case loader",
    )
    for source in candidates:
        if all(marker in source for marker in markers):
            return source
    return None


def resolve_loader_source_path() -> Path:
    candidates: List[Path] = []
    executing_file = globals().get("__file__")
    if isinstance(executing_file, (str, os.PathLike)):
        candidates.append(Path(executing_file))
    if LOADER_SOURCE_PATH_OVERRIDE is not None:
        candidates.append(Path(LOADER_SOURCE_PATH_OVERRIDE))
    for candidate in candidates:
        try:
            resolved = candidate.expanduser().resolve()
        except Exception:
            continue
        if resolved.is_file():
            return resolved

    source = _current_ipython_cell_source()
    if source is not None:
        snapshot = Path.cwd().expanduser().resolve() / "07_environmental_response_case_loader_JUPYTER_CAPTURED.py"
        tmp = snapshot.with_name(snapshot.name + ".tmp")
        tmp.write_text(source, encoding="utf-8")
        os.replace(tmp, snapshot)
        return snapshot
    raise FileNotFoundError(
        "Cannot resolve this loader source. Run the saved .py file or paste the complete loader into one Jupyter cell."
    )


def _contains_task07_configuration(directory: Path) -> bool:
    if not directory.is_dir():
        return False
    for path in directory.glob("*_configuration.json"):
        try:
            payload = read_json(path)
        except Exception:
            continue
        if payload.get("stage") == TASK07_STAGE_NAME and payload.get("smoke_test") is not True:
            return True
    return False


def resolve_case_directory(loader_source: Optional[Path] = None) -> Path:
    if CASE_DIRECTORY_OVERRIDE is not None:
        directory = Path(CASE_DIRECTORY_OVERRIDE).expanduser().resolve()
    else:
        candidates: List[Path] = [Path.cwd().expanduser().resolve()]
        if loader_source is not None:
            candidates.append(loader_source.expanduser().resolve().parent)
        unique: List[Path] = []
        for candidate in candidates:
            if candidate not in unique:
                unique.append(candidate)
        matching = [candidate for candidate in unique if _contains_task07_configuration(candidate)]
        directory = matching[0] if matching else unique[-1]
    if not directory.is_dir():
        raise NotADirectoryError(f"Task-07 case directory does not exist: {directory}")
    return directory


def _prefix_inferred_from_loader_filename(loader_source: Optional[Path]) -> Optional[str]:
    if loader_source is None:
        return None
    suffix = "_07_environmental_response_case_loader.py"
    name = loader_source.name
    if name.endswith(suffix) and len(name) > len(suffix):
        return name[: -len(suffix)]
    return None


def discover_case_configuration(
    case_dir: Path,
    loader_source: Optional[Path] = None,
) -> Tuple[Path, Dict[str, Any], str]:
    candidates: List[Tuple[Path, Dict[str, Any]]] = []
    for path in sorted(case_dir.glob("*_configuration.json")):
        try:
            payload = read_json(path)
        except Exception:
            continue
        if payload.get("stage") == TASK07_STAGE_NAME and payload.get("smoke_test") is not True:
            candidates.append((path.resolve(), payload))

    selected_prefix = (
        str(CASE_PREFIX_OVERRIDE)
        if CASE_PREFIX_OVERRIDE is not None
        else _prefix_inferred_from_loader_filename(loader_source)
    )
    if selected_prefix is not None:
        target = case_file(case_dir, selected_prefix, "configuration.json").resolve()
        for path, payload in candidates:
            if path == target:
                return path, payload, selected_prefix
        if CASE_PREFIX_OVERRIDE is not None:
            raise FileNotFoundError(
                f"CASE_PREFIX_OVERRIDE does not identify a Task-07 configuration: {target}"
            )

    if len(candidates) != 1:
        raise RuntimeError(
            f"Expected exactly one production Task-07 configuration in {case_dir}; found {len(candidates)}: "
            f"{[str(path) for path, _ in candidates]}. Set CASE_PREFIX_OVERRIDE or CASE_DIRECTORY_OVERRIDE explicitly."
        )
    path, payload = candidates[0]
    suffix = "_configuration.json"
    prefix = path.name[: -len(suffix)]
    return path, payload, prefix


def loader_self_scope_audit(loader_source: Path) -> Dict[str, Any]:
    source = loader_source.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(loader_source))
    imported: set[str] = set()
    calls: set[str] = set()
    solver_imports: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.lower())
                if "environmental_response_solver" in alias.name.lower():
                    solver_imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = (node.module or "").lower()
            imported.add(module)
            if "environmental_response_solver" in module:
                solver_imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id.lower())
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr.lower())

    forbidden_imports = sorted(
        module for module in imported if any(token in module for token in ("cupy", "cupyx", "qutip", "subprocess"))
    )
    forbidden_calls = sorted(
        call for call in calls if call in {
            "gmres", "spsolve", "splu", "spilu", "expm_multiply", "solve_ivp",
            "odeint", "popen", "system", "exec", "eval",
        }
    )
    passed = not forbidden_imports and not forbidden_calls and not solver_imports
    return {
        "method": "Python AST read-only loader audit",
        "Task07_solver_imports_found": solver_imports,
        "forbidden_GPU_or_process_imports_found": forbidden_imports,
        "propagation_or_external_execution_calls_found": forbidden_calls,
        "read_only_CPU_loader_without_solver_execution": passed,
    }



def solver_source_scope_audit(
    solver_source: Path,
    configuration: Mapping[str, Any],
) -> Dict[str, Any]:
    """Independently inspect the copied solver without importing or running it."""
    source = solver_source.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(solver_source))
    imported: set[str] = set()
    callables: set[str] = set()
    assignments: set[str] = set()
    top_level_literals: Dict[str, Any] = {}

    for node in tree.body:
        if isinstance(node, ast.Assign):
            try:
                literal = ast.literal_eval(node.value)
            except Exception:
                literal = None
            for target in node.targets:
                if isinstance(target, ast.Name) and literal is not None:
                    top_level_literals[target.id] = literal
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            try:
                top_level_literals[node.target.id] = ast.literal_eval(node.value)
            except Exception:
                pass

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").lower())
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            callables.add(node.name.lower())
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            assignments.add(node.id.lower())

    forbidden_imports = sorted(
        module for module in imported if any(token in module for token in ("qutip",))
    )
    forbidden_callables = sorted(
        name
        for name in callables
        if any(
            token in name
            for token in (
                "monte_carlo", "trajectory", "finite_rate", "temperature_sweep",
                "cap_layer", "detector_reservoir",
            )
        )
    )
    forbidden_assignments = sorted(
        name
        for name in assignments
        if name in {
            "bath_temperature", "detector_temperature", "finite_positive_rate",
            "gamma_down", "gamma_up", "gamma_phi", "cap_strength",
            "trajectory_count",
        }
    )
    required_symbols = {
        "compute_low_rank_kernel",
        "run_reduced_full_tangent_benchmark",
        "differentiate_strang_step_full_tangent",
    }
    if CURRENT_CLOSURE_PILOT_SUFFIX in declared_output_contract(configuration):
        required_symbols.add("run_selected_insertion_closure_pilot")
    required_assignments = {
        "kernel_jump_probability",
        "kernel_anticommutator_probability",
    }
    missing_required = sorted(
        (required_symbols - callables) | (required_assignments - assignments)
    )

    branch_rtol = configuration.get("gmres", {}).get("branch_rtol")
    expected_literals: Dict[str, Any] = {
        "PROPAGATOR_TYPE": configuration.get("propagator_type"),
        "ENVIRONMENT_DIRECTION": configuration.get("environment_direction"),
        "INITIAL_MODE": configuration.get("initial_mode"),
        "OMEGA": configuration.get("omega"),
        "N_SHELL": configuration.get("N_shell"),
        "DT": configuration.get("dt"),
        "T_FINAL": configuration.get("T_final"),
        "INSERTION_DT": configuration.get("insertion_dt"),
        "T_CUT": configuration.get("t_cut", T_CUT_DEFAULT),
        "BACKEND": configuration.get("backend"),
        "BRANCH_GMRES_RTOL": branch_rtol,
    }
    literal_comparisons: Dict[str, Any] = {}
    all_present_literal_matches = True
    for name, expected in expected_literals.items():
        if name not in top_level_literals or expected is None:
            continue
        actual = top_level_literals[name]
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            match = bool(
                np.isclose(float(actual), float(expected), rtol=0.0, atol=1.0e-15)
            )
        else:
            match = actual == expected
        literal_comparisons[name] = {
            "source": actual,
            "configuration": expected,
            "match": match,
        }
        all_present_literal_matches = all_present_literal_matches and match

    stage_folder_number = top_level_literals.get("STAGE_FOLDER_NUMBER")
    fixed_stage_directory = str(configuration.get("fixed_stage_directory", ""))
    folder_number_match: Optional[bool]
    if stage_folder_number is None:
        folder_number_match = None
    else:
        try:
            folder_number_match = (
                int(fixed_stage_directory.split(".", 1)[0])
                == int(stage_folder_number)
            )
        except Exception:
            folder_number_match = False

    embedded_pilot_expected = configuration.get("embedded_closure_pilot_enabled")
    embedded_pilot_source = top_level_literals.get("RUN_EMBEDDED_CLOSURE_PILOT")
    embedded_pilot_match = bool(
        embedded_pilot_expected is None
        or configuration.get("propagator_type") != "spinor"
        or embedded_pilot_source is embedded_pilot_expected
    )

    passed = bool(
        not forbidden_imports
        and not forbidden_callables
        and not forbidden_assignments
        and not missing_required
        and all_present_literal_matches
        and folder_number_match is not False
        and embedded_pilot_match
    )
    return {
        "method": "Independent Python AST audit of copied Task-07 solver; source not imported",
        "forbidden_imports": forbidden_imports,
        "forbidden_callables": forbidden_callables,
        "forbidden_assignments": forbidden_assignments,
        "missing_required_response_symbols": missing_required,
        "manual_literal_comparisons": literal_comparisons,
        "USE_BATCHED_GMRES": top_level_literals.get("USE_BATCHED_GMRES"),
        "RUN_EMBEDDED_CLOSURE_PILOT": embedded_pilot_source,
        "STAGE_FOLDER_NUMBER": stage_folder_number,
        "stage_folder_number_matches_fixed_directory": folder_number_match,
        "embedded_closure_pilot_source_matches_configuration": embedded_pilot_match,
        "source_configuration_literals_match": all_present_literal_matches,
        "finite_rate_temperature_trajectory_CAP_and_detector_reservoir_code_absent": bool(
            not forbidden_imports and not forbidden_callables and not forbidden_assignments
        ),
        "jump_and_anticommutator_implementation_symbols_present": not missing_required,
        "passed": passed,
    }

# =============================================================================
# EXACT RESPONSE RECONSTRUCTION
# =============================================================================
def prefix_trapezoid_weights(times: np.ndarray, endpoint_index: int) -> np.ndarray:
    if endpoint_index == 0:
        return np.zeros(1, dtype=np.float64)
    selected = np.asarray(times[: endpoint_index + 1], dtype=np.float64)
    weights = np.zeros(selected.size, dtype=np.float64)
    weights[0] = 0.5 * (selected[1] - selected[0])
    weights[-1] = 0.5 * (selected[-1] - selected[-2])
    if selected.size > 2:
        weights[1:-1] = 0.5 * (selected[2:] - selected[:-2])
    return weights


def kernel_survival_from_panel_probability(kernel_probability: np.ndarray) -> np.ndarray:
    panels, insertions = kernel_probability.shape
    result = np.zeros((panels + 1, insertions), dtype=np.float64)
    for insertion in range(insertions):
        if insertion >= panels:
            continue
        result[insertion + 1 :, insertion] = -np.cumsum(
            kernel_probability[insertion:, insertion], dtype=np.float64
        )
    return result


def reconstruct_response_from_kernel(
    insertion_times: np.ndarray,
    kernel_probability: np.ndarray,
    kernel_survival: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    panels, nodes = kernel_probability.shape
    if nodes != panels + 1:
        raise ValueError("Kernel must have one more insertion node than output panels")
    if kernel_survival.shape != (nodes, nodes):
        raise ValueError("Survival kernel has an incompatible shape")
    chi_survival = np.zeros(nodes, dtype=np.float64)
    chi_panel_probability = np.zeros(panels, dtype=np.float64)
    for state_index in range(nodes):
        weights = prefix_trapezoid_weights(insertion_times, state_index)
        chi_survival[state_index] = float(
            np.dot(weights, kernel_survival[state_index, : state_index + 1])
        )
    for panel in range(panels):
        weights = prefix_trapezoid_weights(insertion_times, panel + 1)
        chi_panel_probability[panel] = float(
            np.dot(weights[: panel + 1], kernel_probability[panel, : panel + 1])
        )
    durations = np.diff(insertion_times)
    return chi_survival, chi_panel_probability, chi_panel_probability / durations


def coarse_grid_indices(number_nodes: int) -> np.ndarray:
    indices = list(range(0, number_nodes, 2))
    if indices[-1] != number_nodes - 1:
        indices.append(number_nodes - 1)
    return np.asarray(indices, dtype=np.int64)


def aggregate_kernel_to_coarse(
    fine_times: np.ndarray,
    fine_kernel_probability: np.ndarray,
    fine_kernel_survival: np.ndarray,
) -> Dict[str, np.ndarray]:
    node_indices = coarse_grid_indices(fine_times.size)
    coarse_times = fine_times[node_indices]
    coarse_panels = coarse_times.size - 1
    coarse_kernel = np.zeros((coarse_panels, coarse_times.size), dtype=np.float64)
    for coarse_panel in range(coarse_panels):
        first = int(node_indices[coarse_panel])
        last = int(node_indices[coarse_panel + 1])
        for coarse_insertion, fine_insertion in enumerate(node_indices):
            if coarse_insertion > coarse_panel:
                break
            coarse_kernel[coarse_panel, coarse_insertion] = float(
                np.sum(fine_kernel_probability[first:last, fine_insertion], dtype=np.float64)
            )
    coarse_survival_kernel = fine_kernel_survival[np.ix_(node_indices, node_indices)]
    chi_s, chi_p, chi_g = reconstruct_response_from_kernel(
        coarse_times, coarse_kernel, coarse_survival_kernel
    )
    return {
        "node_indices": node_indices,
        "times": coarse_times,
        "kernel_probability": coarse_kernel,
        "kernel_survival": coarse_survival_kernel,
        "chi_survival": chi_s,
        "chi_panel_probability": chi_p,
        "chi_click_density": chi_g,
    }


def compare_fine_and_coarse_response(
    fine_times: np.ndarray,
    fine_chi_survival: np.ndarray,
    fine_chi_panel_probability: np.ndarray,
    coarse: Mapping[str, np.ndarray],
) -> Dict[str, float]:
    indices = np.asarray(coarse["node_indices"], dtype=np.int64)
    coarse_survival = np.asarray(coarse["chi_survival"], dtype=np.float64)
    fine_survival_sampled = fine_chi_survival[indices]
    fine_panel_aggregated = np.zeros(indices.size - 1, dtype=np.float64)
    for panel in range(indices.size - 1):
        fine_panel_aggregated[panel] = float(
            np.sum(fine_chi_panel_probability[indices[panel] : indices[panel + 1]], dtype=np.float64)
        )
    coarse_panel = np.asarray(coarse["chi_panel_probability"], dtype=np.float64)
    signed_distance = 0.5 * (
        float(np.sum(np.abs(fine_panel_aggregated - coarse_panel), dtype=np.float64))
        + abs(float(fine_survival_sampled[-1] - coarse_survival[-1]))
    )
    fine_norm = 0.5 * (
        float(np.sum(np.abs(fine_panel_aggregated), dtype=np.float64))
        + abs(float(fine_survival_sampled[-1]))
    )
    coarse_norm = 0.5 * (
        float(np.sum(np.abs(coarse_panel), dtype=np.float64))
        + abs(float(coarse_survival[-1]))
    )
    fine_mu = float(np.trapezoid(fine_chi_survival, fine_times))
    coarse_times = np.asarray(coarse["times"], dtype=np.float64)
    coarse_mu = float(np.trapezoid(coarse_survival, coarse_times))
    mu_difference = abs(fine_mu - coarse_mu)
    return {
        "signed_measure_distance": signed_distance,
        "relative_signed_measure_distance": signed_distance
        / max(fine_norm, coarse_norm, INSERTION_CONVERGENCE_ABS_TOL),
        "maximum_abs_survival_difference": dense_max_abs(fine_survival_sampled - coarse_survival),
        "survival_L1_difference_on_coarse_grid": float(
            np.trapezoid(np.abs(fine_survival_sampled - coarse_survival), coarse_times)
        ),
        "fine_chi_mu": fine_mu,
        "coarse_chi_mu": coarse_mu,
        "chi_mu_absolute_difference": mu_difference,
        "chi_mu_relative_difference": mu_difference
        / max(abs(fine_mu), abs(coarse_mu), INSERTION_CONVERGENCE_ABS_TOL),
        "fine_response_norm": fine_norm,
        "coarse_response_norm": coarse_norm,
    }


def integrated_response_metrics(
    times: np.ndarray,
    chi_survival: np.ndarray,
    chi_panel_probability: np.ndarray,
    chi_click_density: np.ndarray,
    t_cut: float,
) -> Dict[str, float]:
    chi_d = float(np.sum(chi_panel_probability, dtype=np.float64))
    chi_mu = float(np.trapezoid(chi_survival, times))
    early = 0.0
    late = 0.0
    for panel, (left, right) in enumerate(zip(times[:-1], times[1:])):
        duration = float(right - left)
        if right <= t_cut:
            early += float(chi_panel_probability[panel])
        elif left >= t_cut:
            late += float(chi_panel_probability[panel])
        else:
            fraction = (t_cut - left) / duration
            early += fraction * float(chi_panel_probability[panel])
            late += (1.0 - fraction) * float(chi_panel_probability[panel])
    complete_norm = 0.5 * (
        float(np.sum(np.abs(chi_panel_probability), dtype=np.float64))
        + abs(float(chi_survival[-1]))
    )
    return {
        "chi_D_from_panel_sum": chi_d,
        "chi_D_from_final_survival": -float(chi_survival[-1]),
        "chi_mu_restricted": chi_mu,
        "chi_D_E": early,
        "chi_D_L": late,
        "chi_complete_signed_measure_norm": complete_norm,
        "chi_survival_W1_norm": float(np.trapezoid(np.abs(chi_survival), times)),
        "maximum_abs_chi_survival": dense_max_abs(chi_survival),
        "maximum_abs_chi_click_density": dense_max_abs(chi_click_density),
        "minimum_chi_click_density": float(np.min(chi_click_density)),
        "maximum_chi_click_density": float(np.max(chi_click_density)),
    }


# =============================================================================
# INDEPENDENT CASE AUDIT
# =============================================================================
def verify_configuration(
    case_dir: Path,
    configuration_path: Path,
    configuration: Mapping[str, Any],
    prefix: str,
) -> Dict[str, Any]:
    identity = identity_from_configuration(configuration)
    canonical_prefix = identity.canonical_prefix()
    config_copy = dict(configuration)
    stored_hash = str(config_copy.pop("configuration_sha256", ""))
    deterministic = {
        key: value for key, value in config_copy.items() if key != "backend_metadata"
    }
    reconstructed_hash = sha256_json(deterministic)
    source_name = str(configuration.get("copied_source_file", ""))
    source_path = case_dir / source_name
    source_hash = sha256_file(source_path) if source_path.is_file() else None
    declared_contract = list(declared_output_contract(configuration))
    required_contract = list(required_solver_suffixes(configuration))
    runtime_declared = CURRENT_RUNTIME_SOLVER_SUFFIX in declared_contract
    pilot_declared = CURRENT_CLOSURE_PILOT_SUFFIX in declared_contract
    finite_rate_value = configuration.get(
        "finite_positive_rate_present",
        configuration.get("finite_positive_rate_used"),
    )

    folder_number = configuration.get("manual_stage_folder_number")
    if folder_number is None:
        folder_number_matches = True
    else:
        try:
            folder_number_matches = (
                int(str(case_dir.name).split(".", 1)[0]) == int(folder_number)
            )
        except Exception:
            folder_number_matches = False

    production_contract = configuration.get("production_contract")
    production_contract_hash = configuration.get("production_contract_sha256")
    if isinstance(production_contract, Mapping) and isinstance(
        production_contract_hash, str
    ):
        production_contract_hash_matches = (
            sha256_json(production_contract) == production_contract_hash
        )
    else:
        production_contract_hash_matches = True  # legacy source

    complete_grid = configuration.get("complete_insertion_grid")
    if isinstance(complete_grid, Mapping):
        expected_steps, expected_times = expected_insertion_grid(configuration)
        complete_grid_metadata_matches = bool(
            int(complete_grid.get("node_count", -1)) == expected_steps.size
            and int(complete_grid.get("panel_count", -1)) == expected_steps.size - 1
            and np.isclose(
                float(complete_grid.get("first_time", float("nan"))),
                float(expected_times[0]),
                rtol=0.0,
                atol=2.0e-12,
            )
            and np.isclose(
                float(complete_grid.get("last_time", float("nan"))),
                float(expected_times[-1]),
                rtol=0.0,
                atol=2.0e-12,
            )
        )
    else:
        complete_grid_metadata_matches = True  # legacy source

    return {
        "identity": identity,
        "canonical_prefix": canonical_prefix,
        "checks": {
            "stage_exact": configuration.get("stage") == TASK07_STAGE_NAME,
            "case_prefix_matches_filename": configuration.get("case_prefix") == prefix,
            "case_prefix_is_canonical": prefix == canonical_prefix,
            "fixed_stage_directory_matches_actual_parent": configuration.get("fixed_stage_directory") == case_dir.name,
            "manual_stage_folder_number_matches_actual_parent": folder_number_matches,
            "manual_single_case_policy": configuration.get("manual_single_case_policy") is True,
            "automatic_production_sweep_absent": configuration.get("automatic_production_sweep") is False,
            "zero_environmental_rate_reference_exact": configuration.get("zero_environmental_rate_reference") is True,
            "finite_positive_rate_absent": finite_rate_value is False,
            "temperature_parameter_absent": configuration.get("temperature_parameter_present") is False,
            "trajectory_or_Monte_Carlo_absent": configuration.get("trajectory_or_Monte_Carlo_present") is False,
            "explicit_detector_reservoir_absent": configuration.get("explicit_detector_reservoir_present") is False,
            "CAP_or_second_roof_loss_absent": configuration.get("CAP_or_second_roof_loss_present") is False,
            "configuration_hash_reconstructed": reconstructed_hash == stored_hash,
            "production_contract_hash_reconstructed_when_declared": production_contract_hash_matches,
            "complete_insertion_grid_metadata_matches": complete_grid_metadata_matches,
            "copied_solver_source_present": source_path.is_file(),
            "copied_solver_source_hash_matches": bool(
                source_hash is not None
                and source_hash == configuration.get("copied_source_sha256")
                and source_hash == configuration.get("source_sha256")
            ),
            "output_contract_contains_required_products": all(
                suffix in declared_contract for suffix in required_contract
            ),
            "declared_runtime_metrics_policy_consistent": bool(
                (not runtime_declared)
                or CURRENT_RUNTIME_SOLVER_SUFFIX in required_contract
            ),
            "declared_closure_pilot_policy_consistent": bool(
                (not pilot_declared)
                or CURRENT_CLOSURE_PILOT_SUFFIX in required_contract
            ),
        },
        "stored_configuration_sha256": stored_hash,
        "reconstructed_configuration_sha256": reconstructed_hash,
        "source_path": source_path,
        "source_sha256": source_hash,
        "declared_output_contract": declared_contract,
        "required_solver_suffixes": required_contract,
        "runtime_metrics_declared": runtime_declared,
        "closure_pilot_declared": pilot_declared,
    }

def verify_manifest_and_files(
    case_dir: Path,
    prefix: str,
    configuration: Mapping[str, Any],
) -> Dict[str, Any]:
    required_suffixes = required_solver_suffixes(configuration)
    paths = {suffix: case_file(case_dir, prefix, suffix) for suffix in required_suffixes}
    missing = [suffix for suffix, path in paths.items() if not path.is_file()]
    manifest_path = paths["output_hashes.json"]
    manifest = read_json(manifest_path) if manifest_path.is_file() else {}
    files = manifest.get("files", {})
    hash_rows: Dict[str, Any] = {}
    all_hashes_match = bool(isinstance(files, dict) and files)
    path_safety = True
    if isinstance(files, dict):
        for filename, expected in sorted(files.items()):
            candidate = (case_dir / filename).resolve()
            safe = candidate.parent == case_dir.resolve() and Path(filename).name == filename
            path_safety = path_safety and safe
            actual = sha256_file(candidate) if safe and candidate.is_file() else None
            match = actual == expected
            all_hashes_match = all_hashes_match and match
            hash_rows[filename] = {
                "expected": expected,
                "actual": actual,
                "safe_path": safe,
                "match": match,
            }

    nondeterministic_suffixes = {
        "run_status.json",
        "output_hashes.json",
        "runtime_metrics.json",
        "stdout.txt",
        "simulation_log.txt",
        "failure.json",
    }
    stable_required = [
        paths[suffix].name
        for suffix in required_suffixes
        if suffix not in nondeterministic_suffixes
    ]
    missing_from_manifest = sorted(
        name for name in stable_required if not isinstance(files, dict) or name not in files
    )
    runtime_filename = case_file(case_dir, prefix, CURRENT_RUNTIME_SOLVER_SUFFIX).name
    runtime_excluded_from_stable_manifest = bool(
        CURRENT_RUNTIME_SOLVER_SUFFIX not in required_suffixes
        or not isinstance(files, dict)
        or runtime_filename not in files
    )
    return {
        "paths": paths,
        "manifest": manifest,
        "manifest_sha256": sha256_file(manifest_path) if manifest_path.is_file() else None,
        "missing_required_files": missing,
        "missing_required_stable_files_from_manifest": missing_from_manifest,
        "file_hash_rows": hash_rows,
        "checks": {
            "all_required_solver_files_present": not missing,
            "manifest_nonempty": bool(isinstance(files, dict) and files),
            "manifest_paths_confined_to_case_directory": path_safety,
            "all_manifest_file_hashes_match": all_hashes_match,
            "all_required_stable_products_listed_in_manifest": not missing_from_manifest,
            "runtime_metrics_excluded_from_deterministic_manifest": runtime_excluded_from_stable_manifest,
            "manifest_case_prefix_matches": manifest.get("case_prefix") == prefix,
            "manifest_configuration_hash_matches": manifest.get("configuration_sha256") == configuration.get("configuration_sha256"),
            "manifest_source_hash_matches": manifest.get("source_sha256") == configuration.get("source_sha256"),
        },
    }


def audit_runtime_metrics(
    case_dir: Path,
    prefix: str,
    configuration: Mapping[str, Any],
) -> Dict[str, Any]:
    """Audit both legacy single-reference and v8 dual-reference runtime records."""
    contract = declared_output_contract(configuration)
    declared = CURRENT_RUNTIME_SOLVER_SUFFIX in contract
    path = case_file(case_dir, prefix, CURRENT_RUNTIME_SOLVER_SUFFIX)
    if not declared:
        legacy_backend = configuration.get("backend_metadata", {})
        return {
            "applicable": False,
            "declared": False,
            "schema": "legacy_configuration_embedded_runtime",
            "path": str(path),
            "runtime_metrics": {},
            "metrics": {
                "backend": configuration.get("backend"),
                "gpu_name": (
                    legacy_backend.get("cuda_device_name")
                    if isinstance(legacy_backend, Mapping)
                    else None
                ),
            },
            "checks": {"legacy_case_runtime_record_not_declared": True},
        }

    if not path.is_file():
        return {
            "applicable": True,
            "declared": True,
            "schema": "missing",
            "path": str(path),
            "runtime_metrics": {},
            "metrics": {},
            "checks": {"declared_runtime_metrics_present": False},
        }

    payload = read_json(path)
    backend_metadata = payload.get("backend_metadata", {})
    if not isinstance(backend_metadata, Mapping):
        backend_metadata = {}

    dual = "task05_regression_reference_elapsed_seconds" in payload
    if dual:
        schema = "v8_dual_reference_with_embedded_closure_pilot"
        key_map = {
            "input_validation_seconds": "input_operator_and_benchmark_validation_seconds",
            "task05_reference_seconds": "task05_regression_reference_elapsed_seconds",
            "response_reference_seconds": "response_reference_elapsed_seconds",
            "closure_pilot_seconds": "embedded_closure_pilot_elapsed_seconds",
            "kernel_seconds": "kernel_elapsed_seconds",
            "total_seconds_before_final_hashing": "total_elapsed_seconds_before_final_hashing",
        }
    else:
        schema = "legacy_single_reference"
        key_map = {
            "input_validation_seconds": "preflight_operator_and_benchmark_seconds",
            "task05_reference_seconds": "reference_elapsed_seconds",
            "response_reference_seconds": None,
            "closure_pilot_seconds": None,
            "kernel_seconds": "kernel_elapsed_seconds",
            "total_seconds_before_final_hashing": "total_elapsed_seconds_before_final_hashing",
        }

    durations: Dict[str, Optional[float]] = {}
    required_duration_valid = True
    for normalized, source_key in key_map.items():
        if source_key is None:
            durations[normalized] = 0.0
            continue
        value = finite_float(payload.get(source_key))
        durations[normalized] = value
        required_duration_valid = bool(
            required_duration_valid and value is not None and value >= 0.0
        )

    task05_elapsed = durations["task05_reference_seconds"]
    stored_task05_rate = finite_float(
        payload.get(
            "task05_regression_reference_average_steps_per_second"
            if dual
            else "reference_average_steps_per_second"
        )
    )
    expected_task05_rate = (
        float(configuration["num_steps"]) / task05_elapsed
        if task05_elapsed is not None and task05_elapsed > 0.0
        else None
    )
    task05_rate_consistent = bool(
        stored_task05_rate is not None
        and stored_task05_rate > 0.0
        and expected_task05_rate is not None
        and np.isclose(
            stored_task05_rate,
            expected_task05_rate,
            rtol=1.0e-12,
            atol=1.0e-12,
        )
    )

    response_reused = bool(
        payload.get("response_reference_reused_Task05_trajectory", not dual)
    )
    stored_response_rate = finite_float(
        payload.get("response_reference_average_steps_per_second")
    )
    response_elapsed = durations["response_reference_seconds"]
    if not dual:
        response_rate_consistent = True
    elif response_reused:
        response_rate_consistent = bool(
            response_elapsed is not None
            and abs(response_elapsed) <= 1.0e-12
            and stored_response_rate is None
        )
    else:
        expected_response_rate = (
            float(configuration["num_steps"]) / response_elapsed
            if response_elapsed is not None and response_elapsed > 0.0
            else None
        )
        response_rate_consistent = bool(
            stored_response_rate is not None
            and stored_response_rate > 0.0
            and expected_response_rate is not None
            and np.isclose(
                stored_response_rate,
                expected_response_rate,
                rtol=1.0e-12,
                atol=1.0e-12,
            )
        )

    component_names = (
        "input_validation_seconds",
        "task05_reference_seconds",
        "response_reference_seconds",
        "closure_pilot_seconds",
        "kernel_seconds",
    )
    component_sum = sum(
        float(durations[name])
        for name in component_names
        if durations[name] is not None
    )
    total = durations["total_seconds_before_final_hashing"]
    total_covers_components = bool(
        required_duration_valid
        and total is not None
        and total + 1.0e-8 >= component_sum
    )
    backend_matches = backend_metadata.get("backend") == configuration.get("backend")
    cupy_gpu_metadata_present = bool(
        configuration.get("backend") != "cupy"
        or (
            backend_metadata.get("cupy_version")
            and backend_metadata.get("cuda_device_name")
            and backend_metadata.get("cuda_total_memory_bytes")
        )
    )

    checks = {
        "declared_runtime_metrics_present": True,
        "runtime_schema_supported": schema in {
            "legacy_single_reference",
            "v8_dual_reference_with_embedded_closure_pilot",
        },
        "runtime_case_prefix_matches": payload.get("case_prefix") == prefix,
        "runtime_record_excluded_from_deterministic_hashes": payload.get(
            "excluded_from_deterministic_scientific_hashes"
        ) is True,
        "runtime_durations_finite_and_nonnegative": required_duration_valid,
        "runtime_total_covers_all_recorded_components": total_covers_components,
        "Task05_reference_rate_reconstructed": task05_rate_consistent,
        "response_reference_rate_or_reuse_reconstructed": response_rate_consistent,
        "runtime_backend_matches_configuration": backend_matches,
        "CuPy_GPU_metadata_present_when_required": cupy_gpu_metadata_present,
    }
    return {
        "applicable": True,
        "declared": True,
        "schema": schema,
        "path": str(path),
        "runtime_metrics": payload,
        "metrics": {
            **durations,
            "task05_reference_average_steps_per_second": stored_task05_rate,
            "task05_reference_average_steps_per_second_reconstructed": expected_task05_rate,
            "response_reference_average_steps_per_second": stored_response_rate,
            "response_reference_reused_Task05_trajectory": response_reused,
            "backend": backend_metadata.get("backend"),
            "gpu_name": backend_metadata.get("cuda_device_name"),
            "cupy_version": backend_metadata.get("cupy_version"),
            "cuda_driver_version": backend_metadata.get("cuda_driver_version"),
            "cuda_runtime_version": backend_metadata.get("cuda_runtime_version"),
        },
        "checks": checks,
    }

def verify_status_and_stage_manifest(
    case_dir: Path,
    prefix: str,
    configuration: Mapping[str, Any],
    manifest_audit: Mapping[str, Any],
) -> Dict[str, Any]:
    status_path = case_file(case_dir, prefix, "run_status.json")
    status = read_json(status_path)
    rerun = status.get("deterministic_same_prefix_rerun", {})
    external = status.get("solver_side_external_controls", {})
    stage_manifest_path = case_dir / "stage_manifest.json"
    runtime_declared = CURRENT_RUNTIME_SOLVER_SUFFIX in declared_output_contract(
        configuration
    )
    if stage_manifest_path.is_file():
        stage_manifest = read_json(stage_manifest_path)
        entry = stage_manifest.get("cases", {}).get(prefix, {})
        stage_checks = {
            "stage_manifest_stage_exact": stage_manifest.get("stage") == TASK07_STAGE_NAME,
            "stage_manifest_case_entry_present": bool(entry),
            "stage_manifest_status_matches": entry.get("status") == status.get("status"),
            "stage_manifest_verdict_matches": entry.get("verdict") == status.get("verdict"),
            "stage_manifest_configuration_matches": entry.get("configuration") == case_file(case_dir, prefix, "configuration.json").name,
            "stage_manifest_reference_audit_matches": entry.get("reference_audit") == case_file(case_dir, prefix, "reference_audit.json").name,
            "stage_manifest_operator_audit_matches": entry.get("operator_audit") == case_file(case_dir, prefix, "operator_audit.json").name,
            "stage_manifest_response_audit_matches": entry.get("response_audit") == case_file(case_dir, prefix, "response_audit.json").name,
            "stage_manifest_runtime_metrics_matches_when_declared": bool(
                (not runtime_declared)
                or entry.get("runtime_metrics")
                == case_file(case_dir, prefix, CURRENT_RUNTIME_SOLVER_SUFFIX).name
            ),
            "stage_manifest_output_hashes_matches": entry.get("output_hashes") == case_file(case_dir, prefix, "output_hashes.json").name,
        }
    else:
        stage_manifest = {}
        entry = {}
        stage_checks = {
            "stage_manifest_stage_exact": False,
            "stage_manifest_case_entry_present": False,
            "stage_manifest_status_matches": False,
            "stage_manifest_verdict_matches": False,
            "stage_manifest_configuration_matches": False,
            "stage_manifest_reference_audit_matches": False,
            "stage_manifest_operator_audit_matches": False,
            "stage_manifest_response_audit_matches": False,
            "stage_manifest_runtime_metrics_matches_when_declared": False,
            "stage_manifest_output_hashes_matches": False,
        }

    completed = str(status.get("status", "")).startswith("completed_")
    return {
        "status": status,
        "deterministic_rerun": rerun,
        "external_controls": external,
        "stage_manifest": stage_manifest,
        "stage_manifest_entry": entry,
        "checks": {
            "solver_status_completed": completed,
            "solver_local_checks_reported_pass": status.get("all_case_local_checks_passed") is True,
            "configuration_hash_matches_status": status.get("configuration_sha256") == configuration.get("configuration_sha256"),
            "output_manifest_filename_matches": status.get("output_hash_manifest") == case_file(case_dir, prefix, "output_hashes.json").name,
            "output_manifest_hash_matches_status": status.get("output_hash_manifest_sha256") == manifest_audit.get("manifest_sha256"),
            "Task08_physical_claim_not_authorized_by_solver": status.get("Task08_physical_claim_authorized") is False,
            **stage_checks,
        },
    }

def audit_compact_arrays_and_kernels(
    case_dir: Path,
    prefix: str,
    configuration: Mapping[str, Any],
) -> Dict[str, Any]:
    times = np.asarray(load_npy(case_file(case_dir, prefix, "times.npy")))
    insertion_times = np.asarray(load_npy(case_file(case_dir, prefix, "insertion_times.npy")))
    chi_survival = np.asarray(load_npy(case_file(case_dir, prefix, "chi_survival.npy")))
    chi_click_density = np.asarray(load_npy(case_file(case_dir, prefix, "chi_click_density.npy")))
    kernel = load_npz(case_file(case_dir, prefix, "kernel_summary.npz"))
    source = load_npz(case_file(case_dir, prefix, "source_insertion_summary.npz"))
    benchmark = load_npz(case_file(case_dir, prefix, "full_tangent_benchmark.npz"))
    integrated_stored = read_json(case_file(case_dir, prefix, "integrated_response.json"))

    kernel_missing_keys = sorted(KERNEL_REQUIRED_KEYS - set(kernel))
    source_missing_keys = sorted(SOURCE_REQUIRED_KEYS - set(source))
    benchmark_missing_keys = sorted(BENCHMARK_REQUIRED_KEYS - set(benchmark))
    kernel_extra_keys = sorted(set(kernel) - KERNEL_REQUIRED_KEYS)
    source_extra_keys = sorted(set(source) - SOURCE_REQUIRED_KEYS)
    benchmark_extra_keys = sorted(set(benchmark) - BENCHMARK_REQUIRED_KEYS)
    kernel_schema_present = not kernel_missing_keys
    source_schema_present = not source_missing_keys
    benchmark_schema_present = not benchmark_missing_keys

    nodes = insertion_times.size
    panels = nodes - 1
    expected_steps, expected_times = expected_insertion_grid(configuration)
    expected_nodes = expected_steps.size

    insertion_steps = np.asarray(kernel["insertion_steps"])
    panel_durations = np.asarray(kernel["panel_durations"])
    jump = np.asarray(kernel["kernel_jump_probability"])
    anti = np.asarray(kernel["kernel_anticommutator_probability"])
    total = np.asarray(kernel["kernel_total_probability"])
    density_jump = np.asarray(kernel["kernel_click_density_jump"])
    density_anti = np.asarray(kernel["kernel_click_density_anticommutator"])
    density_total = np.asarray(kernel["kernel_click_density_total"])
    survival_kernel = np.asarray(kernel["kernel_survival"])
    chi_panel_probability = np.asarray(kernel["chi_panel_probability"])

    recomputed_chi_s, recomputed_chi_p, recomputed_chi_g = reconstruct_response_from_kernel(
        insertion_times.astype(np.float64),
        total.astype(np.float64),
        survival_kernel.astype(np.float64),
    )
    coarse = aggregate_kernel_to_coarse(
        insertion_times.astype(np.float64),
        total.astype(np.float64),
        survival_kernel.astype(np.float64),
    )
    coarse_comparison = compare_fine_and_coarse_response(
        insertion_times.astype(np.float64),
        chi_survival.astype(np.float64),
        chi_panel_probability.astype(np.float64),
        coarse,
    )

    source_insertion_steps = np.asarray(source["insertion_steps"])
    source_insertion_times = np.asarray(source["insertion_times"])
    source_jump = np.asarray(source["jump_norm2"])
    source_anti = np.asarray(source["anti_expectation"])
    source_trace_terms = np.asarray(source["trace_terms"])
    source_trace_total = np.asarray(source["trace_total"])
    source_activity = np.asarray(source["activity_total"])
    source_reference_survival = np.asarray(source["reference_survival"])
    source_reference_down = np.asarray(source["reference_s_down"])
    source_reference_up = np.asarray(source["reference_s_up"])
    source_reference_phi = np.asarray(source["reference_s_phi"])
    source_reference_top = np.asarray(source["reference_top_shell"])
    source_branch_labels = np.asarray(source["branch_labels"])
    causal_source_trace = np.zeros_like(survival_kernel, dtype=np.float64)
    for index, value in enumerate(source_trace_total.astype(np.float64)):
        causal_source_trace[index:, index] = value
    expected_survival_kernel = kernel_survival_from_panel_probability(total.astype(np.float64)) + causal_source_trace
    independent_kernel_closure = dense_max_abs(survival_kernel - expected_survival_kernel)

    tangent_closure_curve = chi_survival.astype(np.float64) + np.concatenate(
        ([0.0], np.cumsum(chi_panel_probability.astype(np.float64), dtype=np.float64))
    )
    tangent_closure_abs = dense_max_abs(tangent_closure_curve)
    response_scale = max(
        dense_max_abs(chi_survival),
        float(np.sum(np.abs(chi_panel_probability), dtype=np.float64)),
        1.0e-15,
    )
    tangent_closure_rel = tangent_closure_abs / response_scale

    probability_noncausal_mask = np.triu(np.ones((panels, nodes), dtype=bool), k=1)
    survival_noncausal_mask = np.triu(np.ones((nodes, nodes), dtype=bool), k=1)
    noncausal_max = max(
        dense_max_abs(total[probability_noncausal_mask]),
        dense_max_abs(survival_kernel[survival_noncausal_mask]),
    )

    t_cut = float(configuration.get("t_cut", T_CUT_DEFAULT))
    integrated = integrated_response_metrics(
        insertion_times.astype(np.float64),
        chi_survival.astype(np.float64),
        chi_panel_probability.astype(np.float64),
        chi_click_density.astype(np.float64),
        t_cut,
    )
    integrated_keys = tuple(integrated.keys())
    integrated_differences = {
        key: (
            abs(float(integrated[key]) - float(integrated_stored[key]))
            if key in integrated_stored
            else None
        )
        for key in integrated_keys
    }
    integrated_match = all(
        difference is not None
        and np.isclose(
            integrated[key],
            float(integrated_stored[key]),
            rtol=ARRAY_REL_TOL,
            atol=ARRAY_ABS_TOL,
        )
        for key, difference in integrated_differences.items()
    )

    # Reduced full-tangent benchmark reconstruction.
    b_times = np.asarray(benchmark["times"], dtype=np.float64)
    b_full_s = np.asarray(benchmark["full_chi_survival"], dtype=np.float64)
    b_full_p = np.asarray(benchmark["full_chi_panel_probability"], dtype=np.float64)
    b_low_s = np.asarray(benchmark["low_rank_chi_survival"], dtype=np.float64)
    b_low_p = np.asarray(benchmark["low_rank_chi_panel_probability"], dtype=np.float64)
    b_kernel_p = np.asarray(benchmark["low_rank_kernel_probability"], dtype=np.float64)
    b_kernel_s = np.asarray(benchmark["low_rank_kernel_survival"], dtype=np.float64)
    b_survival_error = dense_max_abs(b_full_s - b_low_s)
    b_probability_error = dense_max_abs(b_full_p - b_low_p)
    b_scale = max(dense_max_abs(b_full_s), dense_max_abs(b_full_p), BENCHMARK_ABS_TOL)
    b_relative = max(b_survival_error, b_probability_error) / b_scale
    b_closure = dense_max_abs(
        b_full_s + np.concatenate(([0.0], np.cumsum(b_full_p, dtype=np.float64)))
    )
    b_source_trace = np.diag(b_kernel_s)
    b_causal_source_trace = np.zeros_like(b_kernel_s)
    for index, value in enumerate(b_source_trace):
        b_causal_source_trace[index:, index] = value
    b_kernel_closure = dense_max_abs(
        b_kernel_s
        - (kernel_survival_from_panel_probability(b_kernel_p) + b_causal_source_trace)
    )
    benchmark_dt = float(b_times[1] - b_times[0]) if b_times.size > 1 else 1.0
    b_scalar_kernel_max = dense_max_abs(b_kernel_p / benchmark_dt)
    scalar = str(configuration["propagator_type"]) == "scalar_factorized"
    benchmark_pass = bool(
        max(b_survival_error, b_probability_error)
        <= BENCHMARK_ABS_TOL + BENCHMARK_REL_TOL * b_scale
        and b_closure <= BENCHMARK_ABS_TOL
        and b_kernel_closure <= BENCHMARK_ABS_TOL
        and ((not scalar) or b_scalar_kernel_max <= SCALAR_KERNEL_ABS_TOL)
    )

    source_shapes = bool(
        source_jump.shape == (nodes, 2)
        and source_anti.shape == (nodes, 2)
        and source_trace_terms.shape == (nodes, 2)
        and source_trace_total.shape == (nodes,)
        and source_activity.shape == (nodes,)
        and source_insertion_steps.shape == (nodes,)
        and source_insertion_times.shape == (nodes,)
        and source_reference_survival.shape == (nodes,)
        and source_reference_down.shape == (nodes,)
        and source_reference_up.shape == (nodes,)
        and source_reference_phi.shape == (nodes,)
        and source_reference_top.shape == (nodes,)
        and source_branch_labels.shape == (4,)
    )
    source_trace_formula_residual = max(
        dense_max_abs(source_trace_terms - (source_jump - source_anti)),
        dense_max_abs(source_trace_total - np.sum(source_trace_terms, axis=1)),
        dense_max_abs(source_activity - np.sum(source_jump, axis=1)),
    )
    launch_expected = {
        "downward": 0.0,
        "upward": 2.0,
        "dephasing": 0.0,
    }[str(configuration["environment_direction"])]
    launch_error = abs(float(source_activity[0]) - launch_expected)

    scalar_kernel_max = dense_max_abs(density_total)
    scalar_survival_kernel_max = dense_max_abs(survival_kernel)
    scalar_response_max = max(dense_max_abs(chi_survival), dense_max_abs(chi_click_density))
    insertion_measure_pass = bool(
        coarse_comparison["signed_measure_distance"] <= INSERTION_CONVERGENCE_ABS_TOL
        or coarse_comparison["relative_signed_measure_distance"] <= INSERTION_CONVERGENCE_REL_TOL
    )
    insertion_mu_pass = bool(
        coarse_comparison["chi_mu_absolute_difference"]
        <= INSERTION_CONVERGENCE_ABS_TOL * max(float(configuration["T_final"]), 1.0)
        or coarse_comparison["chi_mu_relative_difference"] <= INSERTION_CONVERGENCE_REL_TOL
    )
    insertion_pass = insertion_measure_pass and insertion_mu_pass
    if scalar:
        insertion_pass = insertion_pass and scalar_response_max <= SCALAR_RESPONSE_ABS_TOL

    all_numeric_arrays = [
        times, insertion_times, chi_survival, chi_click_density,
        insertion_steps, panel_durations, jump, anti, total,
        density_jump, density_anti, density_total, survival_kernel,
        chi_panel_probability,
        source_insertion_steps, source_insertion_times,
        source_jump, source_anti, source_trace_terms, source_trace_total,
        source_activity, source_reference_survival, source_reference_down,
        source_reference_up, source_reference_phi, source_reference_top,
        b_times, b_full_s, b_full_p, b_low_s, b_low_p, b_kernel_p, b_kernel_s,
    ]
    arrays_finite = all_finite(*all_numeric_arrays)

    shapes_and_dtypes = bool(
        times.shape == (nodes,)
        and insertion_times.shape == (nodes,)
        and chi_survival.shape == (nodes,)
        and chi_click_density.shape == (panels,)
        and times.dtype == np.dtype(np.float64)
        and insertion_times.dtype == np.dtype(np.float64)
        and chi_survival.dtype == np.dtype(np.float64)
        and chi_click_density.dtype == np.dtype(np.float64)
        and insertion_steps.shape == (nodes,)
        and insertion_steps.dtype == np.dtype(np.int64)
        and panel_durations.shape == (panels,)
        and panel_durations.dtype == np.dtype(np.float64)
        and all(
            array.shape == (panels, nodes) and array.dtype == np.dtype(np.float64)
            for array in (jump, anti, total, density_jump, density_anti, density_total)
        )
        and survival_kernel.shape == (nodes, nodes)
        and survival_kernel.dtype == np.dtype(np.float64)
        and chi_panel_probability.shape == (panels,)
        and chi_panel_probability.dtype == np.dtype(np.float64)
    )

    chi_d_identity_residual = abs(
        float(np.sum(chi_panel_probability, dtype=np.float64))
        + float(chi_survival[-1])
    )

    checks = {
        "kernel_NPZ_required_schema_present": kernel_schema_present,
        "source_NPZ_required_schema_present": source_schema_present,
        "benchmark_NPZ_required_schema_present": benchmark_schema_present,
        "all_declared_numeric_arrays_finite": arrays_finite,
        "declared_shapes_and_dtypes_exact": shapes_and_dtypes,
        "source_shapes_exact": source_shapes,
        "expected_insertion_node_count": nodes == expected_nodes,
        "times_equal_insertion_times": max_abs_difference(times, insertion_times) <= 2.0e-12,
        "kernel_insertion_steps_exact": max_abs_difference(insertion_steps, expected_steps) == 0.0,
        "kernel_insertion_times_match_saved_grid": max_abs_difference(
            np.asarray(kernel["insertion_times"]), insertion_times
        ) <= 2.0e-12,
        "source_insertion_grid_matches_kernel": bool(
            max_abs_difference(source_insertion_steps, insertion_steps) == 0.0
            and max_abs_difference(source_insertion_times, insertion_times) <= 2.0e-12
        ),
        "insertion_time_grid_exact_including_final_stub": max_abs_difference(
            insertion_times, expected_times
        ) <= 2.0e-12,
        "response_grid_reaches_observation_horizon": bool(
            insertion_times.size > 0
            and np.isclose(
                float(insertion_times[-1]),
                float(configuration["T_final"]),
                rtol=0.0,
                atol=2.0e-12,
            )
        ),
        "panel_durations_positive_and_reconstructed": bool(
            np.all(panel_durations > 0.0)
            and max_abs_difference(panel_durations, np.diff(insertion_times)) <= 2.0e-12
        ),
        "kernel_total_equals_jump_plus_anticommutator": max_abs_difference(total, jump + anti) <= 5.0e-12,
        "kernel_density_products_reconstructed": bool(
            max_abs_difference(density_jump, jump / panel_durations[:, None]) <= 5.0e-12
            and max_abs_difference(density_anti, anti / panel_durations[:, None]) <= 5.0e-12
            and max_abs_difference(density_total, total / panel_durations[:, None]) <= 5.0e-12
        ),
        "chi_response_reconstructed_from_kernel": bool(
            max_abs_difference(chi_survival, recomputed_chi_s) <= 5.0e-12
            and max_abs_difference(chi_panel_probability, recomputed_chi_p) <= 5.0e-12
            and max_abs_difference(chi_click_density, recomputed_chi_g) <= 5.0e-12
        ),
        "causal_kernel_triangle": noncausal_max <= OPERATOR_TOL,
        "jump_kernel_nonnegative": float(np.min(jump)) >= -OPERATOR_TOL,
        "source_trace_formulas_reconstructed": source_trace_formula_residual <= 5.0e-12,
        "trace_preserving_environmental_insertion": dense_max_abs(source_trace_total) <= SOURCE_TRACE_ABS_TOL,
        "ground_state_launch_source_fingerprint": bool(
            str(configuration["initial_mode"]) != "00" or launch_error <= LAUNCH_SOURCE_ABS_TOL
        ),
        "independent_kernel_probability_closure": independent_kernel_closure <= KERNEL_CLOSURE_ABS_TOL,
        "tangent_probability_closure": bool(
            tangent_closure_abs <= TANGENT_CLOSURE_ABS_TOL
            or tangent_closure_rel <= TANGENT_CLOSURE_REL_TOL
        ),
        "final_detection_response_identity": bool(
            chi_d_identity_residual <= TANGENT_CLOSURE_ABS_TOL
            or chi_d_identity_residual / max(response_scale, 1.0e-15)
            <= TANGENT_CLOSURE_REL_TOL
        ),
        "coarse_kernel_products_reconstructed": bool(
            max_abs_difference(kernel["coarse_node_indices"], coarse["node_indices"]) == 0.0
            and max_abs_difference(kernel["coarse_times"], coarse["times"]) <= 5.0e-12
            and max_abs_difference(kernel["coarse_kernel_probability"], coarse["kernel_probability"]) <= 5.0e-12
            and max_abs_difference(kernel["coarse_kernel_survival"], coarse["kernel_survival"]) <= 5.0e-12
            and max_abs_difference(kernel["coarse_chi_survival"], coarse["chi_survival"]) <= 5.0e-12
            and max_abs_difference(kernel["coarse_chi_panel_probability"], coarse["chi_panel_probability"]) <= 5.0e-12
        ),
        "insertion_quadrature_factor_two_refinement": insertion_pass,
        "integrated_response_reconstructed": integrated_match,
        "reduced_full_tangent_low_rank_benchmark": benchmark_pass,
        "pointwise_scalar_kernel_null": bool(
            (not scalar)
            or (
                scalar_kernel_max <= SCALAR_KERNEL_ABS_TOL
                and scalar_survival_kernel_max <= SCALAR_RESPONSE_ABS_TOL
            )
        ),
        "integrated_scalar_response_null": bool(
            (not scalar) or scalar_response_max <= SCALAR_RESPONSE_ABS_TOL
        ),
    }

    metrics = {
        "kernel_missing_keys": kernel_missing_keys,
        "kernel_extra_keys": kernel_extra_keys,
        "source_missing_keys": source_missing_keys,
        "source_extra_keys": source_extra_keys,
        "benchmark_missing_keys": benchmark_missing_keys,
        "benchmark_extra_keys": benchmark_extra_keys,
        "number_of_insertion_nodes": nodes,
        "number_of_output_panels": panels,
        "maximum_source_trace_residual": dense_max_abs(source_trace_total),
        "launch_activity": float(source_activity[0]),
        "expected_launch_activity": launch_expected,
        "launch_activity_error": launch_error,
        "maximum_independent_kernel_probability_closure_residual": independent_kernel_closure,
        "maximum_tangent_probability_closure_residual": tangent_closure_abs,
        "relative_tangent_probability_closure_residual": tangent_closure_rel,
        "final_detection_response_identity_residual": chi_d_identity_residual,
        "maximum_noncausal_kernel_entry": noncausal_max,
        "minimum_jump_kernel_probability": float(np.min(jump)),
        "maximum_abs_scalar_pointwise_click_kernel": scalar_kernel_max,
        "maximum_abs_scalar_survival_kernel": scalar_survival_kernel_max,
        "maximum_abs_response_component": scalar_response_max,
        "insertion_comparison": coarse_comparison,
        "benchmark_maximum_abs_chi_survival_difference": b_survival_error,
        "benchmark_maximum_abs_chi_panel_probability_difference": b_probability_error,
        "benchmark_relative_low_rank_full_tangent_difference": b_relative,
        "benchmark_tangent_probability_closure": b_closure,
        "benchmark_independent_kernel_closure": b_kernel_closure,
        "benchmark_maximum_abs_scalar_pointwise_kernel": b_scalar_kernel_max,
        "integrated_response_reconstructed": integrated,
        "integrated_response_stored": integrated_stored,
        "integrated_response_absolute_differences": integrated_differences,
    }
    return {
        "checks": checks,
        "metrics": metrics,
        "arrays_for_compact_loader_output": {
            "insertion_steps": insertion_steps.astype(np.int64),
            "times": insertion_times.astype(np.float64),
            "panel_durations": panel_durations.astype(np.float64),
            "chi_survival": chi_survival.astype(np.float64),
            "chi_click_density": chi_click_density.astype(np.float64),
            "chi_panel_probability": chi_panel_probability.astype(np.float64),
            "kernel_jump_probability": jump.astype(np.float64),
            "kernel_anticommutator_probability": anti.astype(np.float64),
            "kernel_total_probability": total.astype(np.float64),
            "kernel_survival": survival_kernel.astype(np.float64),
            "source_jump_norm2": source_jump.astype(np.float64),
            "source_anti_expectation": source_anti.astype(np.float64),
            "source_trace_terms": source_trace_terms.astype(np.float64),
            "source_trace_total": source_trace_total.astype(np.float64),
            "source_activity_total": source_activity.astype(np.float64),
            "reference_survival": source_reference_survival.astype(np.float64),
            "reference_s_down": source_reference_down.astype(np.float64),
            "reference_s_up": source_reference_up.astype(np.float64),
            "reference_s_phi": source_reference_phi.astype(np.float64),
            "reference_top_shell": source_reference_top.astype(np.float64),
            "branch_labels": source_branch_labels,
            "benchmark_times": b_times.astype(np.float64),
            "benchmark_full_chi_survival": b_full_s.astype(np.float64),
            "benchmark_full_chi_panel_probability": b_full_p.astype(np.float64),
            "benchmark_low_rank_chi_survival": b_low_s.astype(np.float64),
            "benchmark_low_rank_chi_panel_probability": b_low_p.astype(np.float64),
        },
    }


def audit_json_records(
    case_dir: Path,
    prefix: str,
    configuration: Mapping[str, Any],
) -> Dict[str, Any]:
    reference = read_json(case_file(case_dir, prefix, "reference_audit.json"))
    operator = read_json(case_file(case_dir, prefix, "operator_audit.json"))
    response = read_json(case_file(case_dir, prefix, "response_audit.json"))

    response_checks: Dict[str, bool] = {}
    flatten_boolean_checks("response", response.get("checks", {}), response_checks)
    failed_response_checks = sorted(
        name for name, passed in response_checks.items() if not passed
    )

    architecture = str(reference.get("architecture", "legacy_single_reference"))
    task05_zero = reference.get(
        "Task05_regression_reference",
        reference.get("zero_rate_reference", {}),
    )
    response_zero = reference.get("response_reference", task05_zero)
    recovery = reference.get("Task05_recovery", {})
    consistency = reference.get("cross_reference_consistency", {})

    def reference_record_rechecked(record: Mapping[str, Any]) -> bool:
        residual = finite_float(record.get("maximum_true_relative_residual"))
        minimum_probability = finite_float(record.get("minimum_midpoint_probability"))
        closure = finite_float(record.get("roof_probability_closure_residual"))
        closure_tolerance = finite_float(record.get("closure_tolerance_used"))
        return bool(
            int(record.get("maximum_gmres_info_abs", -1)) == 0
            and residual is not None
            and residual <= TRUE_RESIDUAL_TOL
            and minimum_probability is not None
            and minimum_probability >= -OPERATOR_TOL
            and closure is not None
            and closure_tolerance is not None
            and abs(closure) <= closure_tolerance
            and record.get("all_arrays_finite") is True
            and record.get("local_numerical_passed") is True
        )

    recovery_metrics = recovery.get("comparison_metrics", {})
    recovery_tolerances = recovery.get("tolerances", {})
    array_tol = finite_float(recovery_tolerances.get("reference_array_abs"))
    source_tol = finite_float(recovery_tolerances.get("reference_source_abs"))

    def metric_within(name: str, tolerance: Optional[float]) -> bool:
        value = finite_float(recovery_metrics.get(name))
        return bool(value is not None and tolerance is not None and value <= tolerance)

    recovery_arrays_rechecked = bool(
        recovery.get("required") is False
        or (
            recovery.get("shape_match") is True
            and metric_within("times_max_abs", 2.0e-12)
            and metric_within("survival_max_abs", array_tol)
            and metric_within("step_probability_max_abs", array_tol)
            and metric_within("s_down_max_abs", source_tol)
            and metric_within("s_up_max_abs", source_tol)
            and metric_within("s_phi_max_abs", source_tol)
        )
    )

    consistency_rechecked = True
    if architecture == "dual_zero_rate_reference":
        tolerances = consistency.get("tolerances", {})
        max_abs = consistency.get("maximum_absolute_differences", {})
        consistency_rechecked = bool(
            consistency.get("shape_match") is True
            and finite_float(
                consistency.get("complete_censored_law_total_variation_distance")
            ) is not None
            and finite_float(
                consistency.get("complete_censored_law_total_variation_distance")
            )
            <= finite_float(tolerances.get("complete_law_total_variation"))
            and finite_float(max_abs.get("survival")) is not None
            and finite_float(max_abs.get("survival"))
            <= finite_float(tolerances.get("survival_Linf"))
            and finite_float(
                consistency.get("maximum_source_diagnostic_difference")
            ) is not None
            and finite_float(
                consistency.get("maximum_source_diagnostic_difference")
            )
            <= finite_float(tolerances.get("source_diagnostic_Linf"))
            and finite_float(
                consistency.get(
                    "maximum_phase_aligned_selected_state_relative_difference"
                )
            ) is not None
            and finite_float(
                consistency.get(
                    "maximum_phase_aligned_selected_state_relative_difference"
                )
            )
            <= finite_float(
                tolerances.get("phase_aligned_selected_state_relative")
            )
            and finite_float(
                consistency.get("maximum_phase_aligned_q_roof_relative_difference")
            ) is not None
            and finite_float(
                consistency.get("maximum_phase_aligned_q_roof_relative_difference")
            )
            <= finite_float(tolerances.get("phase_aligned_q_roof_relative"))
            and consistency.get("passed") is True
        )

    branch_rtol = finite_float(
        configuration.get("gmres", {}).get(
            "branch_rtol", configuration.get("response_reference_gmres_rtol")
        )
    )
    response_rtol = finite_float(response_zero.get("gmres_rtol_used"))
    response_reference_matched = bool(
        response_rtol is not None
        and branch_rtol is not None
        and np.isclose(response_rtol, branch_rtol, rtol=0.0, atol=1.0e-18)
    )

    pilot_path = case_file(case_dir, prefix, CURRENT_CLOSURE_PILOT_SUFFIX)
    pilot_declared = CURRENT_CLOSURE_PILOT_SUFFIX in declared_output_contract(
        configuration
    )
    pilot_separate = read_json(pilot_path) if pilot_path.is_file() else {}
    pilot_embedded = response.get("embedded_full_model_closure_pilot", {})
    pilot_record = pilot_separate or pilot_embedded
    pilot_tolerances = pilot_record.get("tolerances", {})
    pilot_max_closure = finite_float(pilot_record.get("maximum_closure_residual"))
    pilot_closure_tolerance = finite_float(
        pilot_tolerances.get("closure_absolute", TANGENT_CLOSURE_ABS_TOL)
    )
    pilot_max_residual = finite_float(
        pilot_record.get("maximum_branch_true_relative_residual")
    )
    pilot_source_trace = finite_float(
        pilot_record.get("maximum_source_trace_residual")
    )
    pilot_rechecked = bool(
        (not pilot_declared and not pilot_record)
        or (
            pilot_record.get("passed") is True
            and pilot_max_closure is not None
            and pilot_closure_tolerance is not None
            and pilot_max_closure <= pilot_closure_tolerance
            and pilot_max_residual is not None
            and pilot_max_residual <= TRUE_RESIDUAL_TOL
            and int(pilot_record.get("maximum_branch_gmres_info_abs", -1)) == 0
            and pilot_source_trace is not None
            and pilot_source_trace <= SOURCE_TRACE_ABS_TOL
            and pilot_record.get("reference_and_branch_rtol_matched") is True
        )
    )
    pilot_embedded_matches = bool(
        (not pilot_declared)
        or (
            bool(pilot_separate)
            and bool(pilot_embedded)
            and json_safe(pilot_separate) == json_safe(pilot_embedded)
        )
    )

    oscillator = operator.get("Task05_oscillator_operator_audit", {})
    roof = operator.get("roof_sign_audit", {})
    upward = operator.get("projected_upward_finite_shell_identity", {})
    scope = operator.get("source_scope_audit", {})
    batched = operator.get("CuPy_batched_GMRES_certification")
    batched_pass = True if batched is None else batched.get("passed") is True
    operator_components_pass = bool(
        oscillator.get("all_checks_passed") is True
        and roof.get("spinor_roof_term_sign_passed") is True
        and upward.get("passed") is True
        and scope.get("passed") is True
        and batched_pass
    )

    return {
        "reference_audit": reference,
        "operator_audit": operator,
        "closure_pilot_audit": pilot_separate,
        "response_audit": response,
        "failed_solver_response_checks": failed_response_checks,
        "summaries": {
            "reference_architecture": architecture,
            "Task05_regression_reference": task05_zero,
            "response_reference": response_zero,
            "cross_reference_consistency": consistency,
            "Task05_recovery": recovery,
            "embedded_closure_pilot": pilot_record,
            "oscillator_dimension": oscillator.get("dimension"),
            "spin_resolved_channel_dimension": oscillator.get(
                "spin_resolved_channel_dimension"
            ),
            "oscillator_metrics": oscillator.get("metrics", {}),
            "roof_sign_audit": roof,
            "projected_upward_identity": upward,
            "CuPy_batched_GMRES_certification": batched,
            "response_metrics": response.get("metrics", {}),
            "solver_integrated_response": response.get("integrated_response", {}),
            "solver_benchmark": response.get("reduced_full_tangent_benchmark", {}),
        },
        "checks": {
            "reference_audit_passed": reference.get("passed") is True,
            "Task05_regression_reference_local_integrity_passed": task05_zero.get(
                "local_numerical_passed"
            ) is True,
            "Task05_regression_reference_numerics_independently_rechecked": reference_record_rechecked(task05_zero),
            "response_reference_local_integrity_passed": response_zero.get(
                "local_numerical_passed"
            ) is True,
            "response_reference_numerics_independently_rechecked": reference_record_rechecked(response_zero),
            "response_reference_and_branch_rtol_matched": response_reference_matched,
            "Task05_reference_recovery_passed": recovery.get("passed") is True,
            "Task05_reference_comparison_metrics_rechecked": recovery_arrays_rechecked,
            "dual_reference_consistency_passed_when_applicable": bool(
                architecture != "dual_zero_rate_reference"
                or consistency.get("passed") is True
            ),
            "dual_reference_consistency_metrics_rechecked_when_applicable": consistency_rechecked,
            "closure_pilot_file_present_when_declared": bool(
                (not pilot_declared) or pilot_path.is_file()
            ),
            "embedded_closure_pilot_passed_and_rechecked": pilot_rechecked,
            "closure_pilot_file_matches_response_embedded_copy": pilot_embedded_matches,
            "operator_audit_passed": operator.get("all_checks_passed") is True,
            "operator_component_gates_rechecked": operator_components_pass,
            "response_audit_local_checks_passed": response.get(
                "all_case_local_checks_passed"
            ) is True,
            "all_solver_response_boolean_checks_pass": not failed_response_checks,
            "solver_makes_no_production_physical_claim": response.get(
                "production_physical_claim_authorized"
            ) is False,
        },
    }

def audit_case(case_dir: Path, loader_source: Path) -> Dict[str, Any]:
    configuration_path, configuration, prefix = discover_case_configuration(
        case_dir, loader_source
    )
    configuration_audit = verify_configuration(
        case_dir, configuration_path, configuration, prefix
    )
    manifest_audit = verify_manifest_and_files(case_dir, prefix, configuration)
    runtime_audit = audit_runtime_metrics(case_dir, prefix, configuration)
    status_audit = verify_status_and_stage_manifest(
        case_dir, prefix, configuration, manifest_audit
    )
    json_audit = audit_json_records(case_dir, prefix, configuration)
    numerical_audit = audit_compact_arrays_and_kernels(
        case_dir, prefix, configuration
    )
    self_scope = loader_self_scope_audit(loader_source)
    copied_solver_source = Path(configuration_audit["source_path"])
    if copied_solver_source.is_file():
        solver_scope = solver_source_scope_audit(
            copied_solver_source, configuration
        )
    else:
        solver_scope = {
            "method": "Independent Python AST audit of copied Task-07 solver",
            "passed": False,
            "error": f"Copied solver source is missing: {copied_solver_source}",
        }

    nonfinite_scan_target = {
        "configuration_audit": {
            key: value
            for key, value in configuration_audit.items()
            if key != "identity"
        },
        "manifest_audit": manifest_audit,
        "runtime_audit": runtime_audit,
        "status_audit": status_audit,
        "solver_JSON_audit": json_audit,
        "copied_solver_source_scope_audit": solver_scope,
        "independent_numerical_metrics": numerical_audit["metrics"],
        "loader_self_scope_audit": self_scope,
    }
    nonfinite_paths = find_nonfinite_paths(nonfinite_scan_target)

    checks_by_group = {
        "loader_scope": {
            "read_only_CPU_loader": self_scope[
                "read_only_CPU_loader_without_solver_execution"
            ]
        },
        "copied_solver_source_scope": {"passed": solver_scope["passed"]},
        "configuration": configuration_audit["checks"],
        "manifest_and_files": manifest_audit["checks"],
        "runtime_metrics": runtime_audit["checks"],
        "status_and_stage_manifest": status_audit["checks"],
        "solver_JSON_records": json_audit["checks"],
        "independent_numerical_reconstruction": numerical_audit["checks"],
        "loader_derived_metric_finiteness": {
            "no_nonfinite_required_loader_metrics": not nonfinite_paths
        },
    }
    flat_checks: Dict[str, bool] = {}
    flatten_boolean_checks("", checks_by_group, flat_checks)
    all_checks_passed = all(flat_checks.values())

    rerun = status_audit["deterministic_rerun"]
    rerun_passed = rerun.get("passed") is True
    rerun_pending = bool(
        rerun.get("pending") is True
        or rerun.get("comparison_applicable") is False
    )
    external = status_audit["external_controls"]
    external_pending = bool(
        external.get("all_required_controls_available") is False
        or external.get("evidence_status") == "PENDING"
        or str(external.get("time_step_status", "")).startswith("PENDING")
        or str(external.get("shell_cutoff_status", "")).startswith("PENDING")
    )
    external_failed = bool(
        external.get("all_required_controls_available") is True
        and external.get("all_required_controls_passed") is False
        and configuration.get("propagator_type") != "scalar_factorized"
    )

    if not all_checks_passed or external_failed or (
        not rerun_passed and not rerun_pending
    ):
        verdict = "FAIL"
        exit_code = 2
    elif rerun_pending:
        verdict = "PASS_CASE_LOCAL_RERUN_PENDING"
        exit_code = 3
    elif external_pending:
        verdict = "PASS_CASE_LOCAL_EXTERNAL_CONTROLS_PENDING"
        exit_code = 3
    else:
        verdict = "PASS_CASE_LOCAL"
        exit_code = 0

    return {
        "loader_stage": LOADER_STAGE,
        "loader_version": LOADER_VERSION,
        "audited_utc": utc_now_iso(),
        "case_prefix": prefix,
        "case_directory": str(case_dir),
        "verdict": verdict,
        "exit_code": exit_code,
        "all_independent_checks_passed": all_checks_passed,
        "configuration": configuration,
        "configuration_audit": {
            key: value
            for key, value in configuration_audit.items()
            if key != "identity"
        },
        "manifest_audit": manifest_audit,
        "runtime_audit": runtime_audit,
        "status_audit": status_audit,
        "solver_JSON_audit": json_audit,
        "copied_solver_source_scope_audit": solver_scope,
        "independent_numerical_audit": {
            "checks": numerical_audit["checks"],
            "metrics": numerical_audit["metrics"],
        },
        "loader_self_scope_audit": self_scope,
        "nonfinite_loader_metric_audit": {
            "passed": not nonfinite_paths,
            "count": len(nonfinite_paths),
            "values": nonfinite_paths,
            "interpretation": (
                "Required raw numerical arrays are checked separately. This "
                "record covers derived loader metrics and prevents NaN/Infinity "
                "from being mistaken for a valid comparison or crashing JSON output."
            ),
        },
        "checks_by_group": checks_by_group,
        "checks": flat_checks,
        "failed_checks": sorted(
            name for name, passed in flat_checks.items() if not passed
        ),
        "pending_items": [
            item
            for item, pending in (
                ("deterministic same-prefix rerun", rerun_pending),
                ("external time-step/shell/evidence family", external_pending),
            )
            if pending
        ],
        "compact_arrays": numerical_audit["arrays_for_compact_loader_output"],
    }

# =============================================================================
# OUTPUTS AND SHARE PACKAGES
# =============================================================================
def loader_output_paths(output_dir: Path, prefix: str) -> Dict[str, Path]:
    return {
        "audit": case_file(output_dir, prefix, "case_loader_audit.json"),
        "metrics": case_file(output_dir, prefix, "case_loader_metrics.csv"),
        "curves": case_file(output_dir, prefix, "case_loader_curves.csv"),
        "report": case_file(output_dir, prefix, "case_loader_report.md"),
        "compact": case_file(output_dir, prefix, "case_loader_compact.npz"),
        "hashes": case_file(output_dir, prefix, "case_loader_output_hashes.json"),
        "status": case_file(output_dir, prefix, "case_loader_run_status.json"),
        "source": case_file(output_dir, prefix, "07_environmental_response_case_loader.py"),
        "full_zip": case_file(output_dir, prefix, "Task07_case_share.zip"),
        "diagnostic_zip": case_file(output_dir, prefix, "Task07_diagnostic_share.zip"),
        "failure": case_file(output_dir, prefix, "case_loader_failure.json"),
    }


def clean_previous_loader_products(output_dir: Path, prefix: str, loader_source: Path) -> None:
    for path in loader_output_paths(output_dir, prefix).values():
        if path.is_file() and path.resolve() != loader_source.resolve():
            path.unlink()


def build_curve_rows(compact_arrays: Mapping[str, np.ndarray]) -> Tuple[List[Dict[str, Any]], Tuple[str, ...]]:
    times = np.asarray(compact_arrays["times"], dtype=np.float64)
    insertion_steps = np.asarray(compact_arrays["insertion_steps"], dtype=np.int64)
    chi_s = np.asarray(compact_arrays["chi_survival"], dtype=np.float64)
    chi_g = np.asarray(compact_arrays["chi_click_density"], dtype=np.float64)
    chi_p = np.asarray(compact_arrays["chi_panel_probability"], dtype=np.float64)
    durations = np.asarray(compact_arrays["panel_durations"], dtype=np.float64)
    source_activity = np.asarray(compact_arrays["source_activity_total"], dtype=np.float64)
    source_trace = np.asarray(compact_arrays["source_trace_total"], dtype=np.float64)
    reference_survival = np.asarray(compact_arrays["reference_survival"], dtype=np.float64)
    reference_down = np.asarray(compact_arrays["reference_s_down"], dtype=np.float64)
    reference_up = np.asarray(compact_arrays["reference_s_up"], dtype=np.float64)
    reference_phi = np.asarray(compact_arrays["reference_s_phi"], dtype=np.float64)
    reference_top = np.asarray(compact_arrays["reference_top_shell"], dtype=np.float64)

    rows: List[Dict[str, Any]] = []
    for node in range(times.size):
        panel_exists = node < times.size - 1
        rows.append(
            {
                "node_index": node,
                "fine_step": int(insertion_steps[node]),
                "time": float(times[node]),
                "chi_survival": float(chi_s[node]),
                "source_activity_total": float(source_activity[node]),
                "source_trace_total": float(source_trace[node]),
                "reference_survival": float(reference_survival[node]),
                "reference_s_down": float(reference_down[node]),
                "reference_s_up": float(reference_up[node]),
                "reference_s_phi": float(reference_phi[node]),
                "reference_top_shell": float(reference_top[node]),
                "panel_index": node if panel_exists else "",
                "panel_left": float(times[node]) if panel_exists else "",
                "panel_right": float(times[node + 1]) if panel_exists else "",
                "panel_midpoint": (
                    0.5 * float(times[node] + times[node + 1])
                    if panel_exists
                    else ""
                ),
                "panel_duration": float(durations[node]) if panel_exists else "",
                "chi_panel_probability": float(chi_p[node]) if panel_exists else "",
                "chi_click_density": float(chi_g[node]) if panel_exists else "",
            }
        )
    fieldnames = tuple(rows[0].keys()) if rows else tuple()
    return rows, fieldnames


def build_metrics_row(audit: Mapping[str, Any]) -> Dict[str, Any]:
    configuration = audit["configuration"]
    metrics = audit["independent_numerical_audit"]["metrics"]
    integrated = metrics["integrated_response_reconstructed"]
    insertion = metrics["insertion_comparison"]
    status = audit["status_audit"]["status"]
    rerun = audit["status_audit"]["deterministic_rerun"]
    external = audit["status_audit"]["external_controls"]
    summaries = audit["solver_JSON_audit"]["summaries"]
    task05_zero = summaries.get("Task05_regression_reference", {})
    response_zero = summaries.get("response_reference", task05_zero)
    consistency = summaries.get("cross_reference_consistency", {})
    recovery = summaries.get("Task05_recovery", {})
    recovery_metrics = recovery.get("comparison_metrics", {})
    oscillator_metrics = summaries.get("oscillator_metrics", {})
    roof = summaries.get("roof_sign_audit", {})
    pilot = summaries.get("embedded_closure_pilot", {})
    batched = summaries.get("CuPy_batched_GMRES_certification") or {}
    runtime = audit.get("runtime_audit", {}).get("metrics", {})
    solver_scope = audit.get("copied_solver_source_scope_audit", {})
    gmres_family = recovery.get("task05_gmres_family") or {}

    return {
        "case_prefix": audit["case_prefix"],
        "case_directory": audit["case_directory"],
        "verdict": audit["verdict"],
        "all_independent_checks_passed": audit["all_independent_checks_passed"],
        "failed_check_count": len(audit["failed_checks"]),
        "pending_item_count": len(audit["pending_items"]),
        "propagator_type": configuration.get("propagator_type"),
        "environment_direction": configuration.get("environment_direction"),
        "omega": configuration.get("omega"),
        "initial_mode": configuration.get("initial_mode"),
        "N_shell": configuration.get("N_shell"),
        "M_N": configuration.get("M_N"),
        "d_channels": configuration.get("d_channels"),
        "N_z": configuration.get("N_z"),
        "dt": configuration.get("dt"),
        "T_final": configuration.get("T_final"),
        "insertion_dt": configuration.get("insertion_dt"),
        "insertion_node_count": metrics.get("number_of_insertion_nodes"),
        "backend": configuration.get("backend"),
        "use_batched_gmres": configuration.get(
            "use_batched_gmres", solver_scope.get("USE_BATCHED_GMRES")
        ),
        "stage_folder_number": configuration.get(
            "manual_stage_folder_number", solver_scope.get("STAGE_FOLDER_NUMBER")
        ),
        "solver_script_version": configuration.get("script_version"),
        "solver_source_sha256": configuration.get("source_sha256"),
        "numerical_core_sha256": configuration.get("numerical_core_sha256"),
        "gpu_name": runtime.get("gpu_name"),
        "cupy_version": runtime.get("cupy_version"),
        "input_validation_seconds": runtime.get("input_validation_seconds"),
        "task05_reference_seconds": runtime.get("task05_reference_seconds"),
        "task05_reference_steps_per_second": runtime.get(
            "task05_reference_average_steps_per_second"
        ),
        "response_reference_seconds": runtime.get("response_reference_seconds"),
        "response_reference_steps_per_second": runtime.get(
            "response_reference_average_steps_per_second"
        ),
        "response_reference_reused": runtime.get(
            "response_reference_reused_Task05_trajectory"
        ),
        "closure_pilot_seconds": runtime.get("closure_pilot_seconds"),
        "kernel_seconds": runtime.get("kernel_seconds"),
        "total_seconds_before_final_hashing": runtime.get(
            "total_seconds_before_final_hashing"
        ),
        "task05_reference_initial_survival": task05_zero.get("initial_survival"),
        "task05_reference_final_survival": task05_zero.get("final_survival"),
        "task05_reference_max_true_residual": task05_zero.get(
            "maximum_true_relative_residual"
        ),
        "response_reference_initial_survival": response_zero.get("initial_survival"),
        "response_reference_final_survival": response_zero.get("final_survival"),
        "response_reference_cumulative_roof_probability": response_zero.get(
            "cumulative_midpoint_roof_probability"
        ),
        "response_reference_roof_closure_abs": response_zero.get(
            "roof_probability_closure_residual"
        ),
        "response_reference_roof_closure_relative": response_zero.get(
            "roof_probability_closure_relative"
        ),
        "response_reference_max_true_residual": response_zero.get(
            "maximum_true_relative_residual"
        ),
        "response_reference_max_gmres_info_abs": response_zero.get(
            "maximum_gmres_info_abs"
        ),
        "response_reference_max_survival_increase": response_zero.get(
            "maximum_survival_increase"
        ),
        "dual_reference_complete_law_distance": consistency.get(
            "complete_censored_law_total_variation_distance"
        ),
        "dual_reference_max_selected_state_relative_difference": consistency.get(
            "maximum_phase_aligned_selected_state_relative_difference"
        ),
        "dual_reference_max_q_roof_relative_difference": consistency.get(
            "maximum_phase_aligned_q_roof_relative_difference"
        ),
        "closure_pilot_maximum_closure": pilot.get("maximum_closure_residual"),
        "closure_pilot_maximum_branch_residual": pilot.get(
            "maximum_branch_true_relative_residual"
        ),
        "closure_pilot_branch_steps": pilot.get("branch_steps_propagated"),
        "task05_case_prefix": recovery.get("task05_case_prefix"),
        "task05_stage_directory": recovery.get("task05_stage_directory"),
        "task05_reference_gmres_rtol": gmres_family.get("rtol"),
        "task05_survival_max_abs_difference": recovery_metrics.get("survival_max_abs"),
        "task05_step_probability_max_abs_difference": recovery_metrics.get(
            "step_probability_max_abs"
        ),
        "task05_s_down_max_abs_difference": recovery_metrics.get("s_down_max_abs"),
        "task05_s_up_max_abs_difference": recovery_metrics.get("s_up_max_abs"),
        "task05_s_phi_max_abs_difference": recovery_metrics.get("s_phi_max_abs"),
        "oscillator_dimension": summaries.get("oscillator_dimension"),
        "spin_resolved_channel_dimension": summaries.get(
            "spin_resolved_channel_dimension"
        ),
        "audit02_K_permutation_residual": oscillator_metrics.get(
            "audit02_K_tensor_permutation_residual"
        ),
        "K_hermiticity_residual": oscillator_metrics.get("K_hermiticity_residual"),
        "roof_plus_sign_residual": roof.get("plus_sign_roof_block_max_abs_residual"),
        "detector_loss_operator_residual": roof.get(
            "detector_loss_operator_roof_identity_residual"
        ),
        "batched_gmres_certification_applicable": batched.get("applicable"),
        "batched_gmres_certification_passed": batched.get("passed"),
        "solver_verdict": status.get("verdict"),
        "case_role": status.get("case_role"),
        "deterministic_rerun_passed": rerun.get("passed") is True,
        "time_step_status": external.get("time_step_status"),
        "shell_cutoff_status": external.get("shell_cutoff_status"),
        "evidence_status": external.get("evidence_status"),
        "response_classification": external.get("response_classification"),
        "chi_D": integrated["chi_D_from_final_survival"],
        "chi_D_panel_sum": integrated["chi_D_from_panel_sum"],
        "chi_mu": integrated["chi_mu_restricted"],
        "chi_D_E": integrated["chi_D_E"],
        "chi_D_L": integrated["chi_D_L"],
        "response_norm": integrated["chi_complete_signed_measure_norm"],
        "maximum_abs_chi_survival": integrated["maximum_abs_chi_survival"],
        "maximum_abs_chi_click_density": integrated[
            "maximum_abs_chi_click_density"
        ],
        "maximum_source_trace_residual": metrics["maximum_source_trace_residual"],
        "launch_activity": metrics.get("launch_activity"),
        "expected_launch_activity": metrics.get("expected_launch_activity"),
        "tangent_closure_abs": metrics[
            "maximum_tangent_probability_closure_residual"
        ],
        "kernel_closure_abs": metrics[
            "maximum_independent_kernel_probability_closure_residual"
        ],
        "final_detection_response_identity_residual": metrics.get(
            "final_detection_response_identity_residual"
        ),
        "maximum_noncausal_kernel_entry": metrics["maximum_noncausal_kernel_entry"],
        "minimum_jump_kernel_probability": metrics["minimum_jump_kernel_probability"],
        "insertion_signed_measure_difference": insertion[
            "signed_measure_distance"
        ],
        "insertion_relative_difference": insertion[
            "relative_signed_measure_distance"
        ],
        "insertion_chi_mu_absolute_difference": insertion[
            "chi_mu_absolute_difference"
        ],
        "insertion_chi_mu_relative_difference": insertion[
            "chi_mu_relative_difference"
        ],
        "benchmark_survival_difference": metrics[
            "benchmark_maximum_abs_chi_survival_difference"
        ],
        "benchmark_panel_probability_difference": metrics[
            "benchmark_maximum_abs_chi_panel_probability_difference"
        ],
    }

def build_report(audit: Mapping[str, Any], metrics_row: Mapping[str, Any]) -> str:
    checks = audit["checks"]

    def numeric(value: Any, fmt: str = ".12e") -> str:
        if value is None or value == "":
            return "not recorded"
        try:
            number = float(value)
        except Exception:
            return str(value)
        if not math.isfinite(number):
            return "undefined"
        return format(number, fmt)

    def duration(value: Any) -> str:
        if value is None or value == "":
            return "not recorded"
        try:
            seconds = float(value)
        except Exception:
            return str(value)
        if not math.isfinite(seconds):
            return "undefined"
        hours, remainder = divmod(int(round(seconds)), 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:d} h {minutes:02d} min {secs:02d} s"

    scalar = metrics_row.get("propagator_type") == "scalar_factorized"
    if scalar:
        interpretation = (
            "This case is an exact factorized-scalar null control. A PASS means "
            "the independently reconstructed pointwise kernel and integrated "
            "response remain at the declared numerical floor."
        )
    else:
        interpretation = (
            "This case contains an active spinor response kernel. The per-case "
            "loader verifies its local integrity, dual-reference construction, "
            "embedded closure guard, and full-kernel reconstruction. The response "
            "remains provisional until Task 08 closes family convergence and the "
            "combined uncertainty budget."
        )

    lines = [
        "# Task 07 — Independent per-case audit and share package",
        "",
        f"## Verdict: **{audit['verdict']}**",
        "",
        "> This is a read-only CPU audit of one completed Task-07 case. It does not import or rerun the solver and it does not itself authorize a physical susceptibility claim.",
        "",
        "## Case and provenance",
        "",
        "| Quantity | Value |",
        "|---|---|",
        f"| Prefix | `{audit['case_prefix']}` |",
        f"| Cluster case directory | `{audit['case_directory']}` |",
        f"| Stage folder number | `{metrics_row.get('stage_folder_number')}` |",
        f"| Detector map | `{metrics_row.get('propagator_type')}` |",
        f"| Environmental direction | `{metrics_row.get('environment_direction')}` |",
        f"| Confinement | {numeric(metrics_row.get('omega'), '.12g')} |",
        f"| Initial mode | `{metrics_row.get('initial_mode')}` |",
        f"| Shell cutoff | {metrics_row.get('N_shell')} |",
        f"| Oscillator modes / spin channels | {metrics_row.get('M_N')} / {metrics_row.get('d_channels')} |",
        f"| Longitudinal points | {metrics_row.get('N_z')} |",
        f"| Detector time step | {numeric(metrics_row.get('dt'), '.12g')} |",
        f"| Observation horizon | {numeric(metrics_row.get('T_final'), '.12g')} |",
        f"| Insertion spacing | {numeric(metrics_row.get('insertion_dt'), '.12g')} |",
        f"| Backend | `{metrics_row.get('backend')}` |",
        f"| Custom batched GMRES selected | `{metrics_row.get('use_batched_gmres')}` |",
        f"| GPU | `{metrics_row.get('gpu_name') or 'not recorded'}` |",
        f"| Solver version | `{metrics_row.get('solver_script_version')}` |",
        f"| Solver source SHA-256 | `{metrics_row.get('solver_source_sha256')}` |",
        f"| Numerical-core SHA-256 | `{metrics_row.get('numerical_core_sha256')}` |",
        "",
        "## Runtime record",
        "",
        "| Phase | Wall time / rate |",
        "|---|---:|",
        f"| Input, operators, and reduced benchmark | {duration(metrics_row.get('input_validation_seconds'))} |",
        f"| Task-05 archival regression reference | {duration(metrics_row.get('task05_reference_seconds'))} |",
        f"| Task-05 archival reference rate | {numeric(metrics_row.get('task05_reference_steps_per_second'), '.6g')} step/s |",
        f"| Matched Task-07 response reference | {duration(metrics_row.get('response_reference_seconds'))} |",
        f"| Response reference rate | {numeric(metrics_row.get('response_reference_steps_per_second'), '.6g')} step/s |",
        f"| Response reference reused Task-05 trajectory | `{metrics_row.get('response_reference_reused')}` |",
        f"| Embedded selected-column closure guard | {duration(metrics_row.get('closure_pilot_seconds'))} |",
        f"| Complete all-insertion kernel | {duration(metrics_row.get('kernel_seconds'))} |",
        f"| Total before final hashing | {duration(metrics_row.get('total_seconds_before_final_hashing'))} |",
        "",
        "## Dual zero-rate reference and Task-05 recovery",
        "",
        "| Quantity | Value |",
        "|---|---:|",
        f"| Task-05 reference final survival | {numeric(metrics_row.get('task05_reference_final_survival'))} |",
        f"| Task-05 reference maximum true residual | {numeric(metrics_row.get('task05_reference_max_true_residual'))} |",
        f"| Response reference final survival | {numeric(metrics_row.get('response_reference_final_survival'))} |",
        f"| Response reference cumulative roof probability | {numeric(metrics_row.get('response_reference_cumulative_roof_probability'))} |",
        f"| Response-reference roof closure residual | {numeric(metrics_row.get('response_reference_roof_closure_abs'))} |",
        f"| Response-reference relative roof closure | {numeric(metrics_row.get('response_reference_roof_closure_relative'))} |",
        f"| Response-reference maximum true residual | {numeric(metrics_row.get('response_reference_max_true_residual'))} |",
        f"| Dual-reference complete-law distance | {numeric(metrics_row.get('dual_reference_complete_law_distance'))} |",
        f"| Dual-reference maximum selected-state relative difference | {numeric(metrics_row.get('dual_reference_max_selected_state_relative_difference'))} |",
        f"| Dual-reference maximum roof-midpoint relative difference | {numeric(metrics_row.get('dual_reference_max_q_roof_relative_difference'))} |",
        f"| Embedded-pilot maximum closure | {numeric(metrics_row.get('closure_pilot_maximum_closure'))} |",
        f"| Embedded-pilot maximum branch residual | {numeric(metrics_row.get('closure_pilot_maximum_branch_residual'))} |",
        f"| Task-05 source directory | `{metrics_row.get('task05_stage_directory')}` |",
        f"| Task-05 case prefix | `{metrics_row.get('task05_case_prefix')}` |",
        f"| Maximum survival recovery difference | {numeric(metrics_row.get('task05_survival_max_abs_difference'))} |",
        f"| Maximum step-probability recovery difference | {numeric(metrics_row.get('task05_step_probability_max_abs_difference'))} |",
        "",
        "## Reconstructed environmental response",
        "",
        "| Quantity | Value |",
        "|---|---:|",
        f"| chi_D = -chi_S(T) | {numeric(metrics_row['chi_D'])} |",
        f"| chi_D from panel sum | {numeric(metrics_row['chi_D_panel_sum'])} |",
        f"| chi_mu | {numeric(metrics_row['chi_mu'])} |",
        f"| chi_D_E | {numeric(metrics_row['chi_D_E'])} |",
        f"| chi_D_L | {numeric(metrics_row['chi_D_L'])} |",
        f"| Complete signed-response norm | {numeric(metrics_row['response_norm'])} |",
        f"| Maximum |chi_S| | {numeric(metrics_row['maximum_abs_chi_survival'])} |",
        f"| Maximum |chi_g| | {numeric(metrics_row['maximum_abs_chi_click_density'])} |",
        f"| Launch activity / expected | {numeric(metrics_row.get('launch_activity'))} / {numeric(metrics_row.get('expected_launch_activity'))} |",
        "",
        "## Independent numerical controls",
        "",
        "| Audit quantity | Value |",
        "|---|---:|",
        f"| Source-trace residual | {numeric(metrics_row['maximum_source_trace_residual'])} |",
        f"| Tangent probability closure | {numeric(metrics_row['tangent_closure_abs'])} |",
        f"| Final detection-response identity residual | {numeric(metrics_row.get('final_detection_response_identity_residual'))} |",
        f"| Per-insertion kernel closure | {numeric(metrics_row['kernel_closure_abs'])} |",
        f"| Maximum noncausal kernel entry | {numeric(metrics_row['maximum_noncausal_kernel_entry'])} |",
        f"| Minimum jump-kernel probability | {numeric(metrics_row['minimum_jump_kernel_probability'])} |",
        f"| Insertion signed-measure difference | {numeric(metrics_row['insertion_signed_measure_difference'])} |",
        f"| Insertion relative difference | {numeric(metrics_row['insertion_relative_difference'])} |",
        f"| Insertion chi_mu relative difference | {numeric(metrics_row['insertion_chi_mu_relative_difference'])} |",
        f"| Full-tangent/low-rank survival difference | {numeric(metrics_row['benchmark_survival_difference'])} |",
        f"| Full-tangent/low-rank panel difference | {numeric(metrics_row['benchmark_panel_probability_difference'])} |",
        "",
        "## Operator and family status",
        "",
        "| Item | Result |",
        "|---|---|",
        f"| Audit-02 K permutation residual | {numeric(metrics_row.get('audit02_K_permutation_residual'))} |",
        f"| K Hermiticity residual | {numeric(metrics_row.get('K_hermiticity_residual'))} |",
        f"| Spinor roof +K sign residual | {numeric(metrics_row.get('roof_plus_sign_residual'))} |",
        f"| Detector-loss operator residual | {numeric(metrics_row.get('detector_loss_operator_residual'))} |",
        f"| Solver verdict | `{metrics_row.get('solver_verdict')}` |",
        f"| Case role | `{metrics_row.get('case_role')}` |",
        f"| Deterministic rerun passed | `{metrics_row.get('deterministic_rerun_passed')}` |",
        f"| Time-step control | `{metrics_row.get('time_step_status')}` |",
        f"| Shell-cutoff control | `{metrics_row.get('shell_cutoff_status')}` |",
        f"| Evidence status | `{metrics_row.get('evidence_status')}` |",
        f"| Response classification | `{metrics_row.get('response_classification')}` |",
        "",
        "## Interpretation",
        "",
        interpretation,
        "",
        "## Independent checks",
        "",
        "| Check | Verdict |",
        "|---|---|",
    ]
    for name in sorted(checks):
        lines.append(f"| `{name}` | {'PASS' if checks[name] else 'FAIL'} |")
    if audit["pending_items"]:
        lines.extend(["", "## Pending items", ""])
        lines.extend(f"- {item}" for item in audit["pending_items"])
    if audit["failed_checks"]:
        lines.extend(["", "## Failed checks", ""])
        lines.extend(f"- `{item}`" for item in audit["failed_checks"])
    lines.extend(
        [
            "",
            "## Share products",
            "",
            f"- Full raw-data package: `{audit.get('full_share_zip', 'Task07_case_share.zip')}`",
            f"- Compact diagnostic package: `{audit.get('diagnostic_share_zip', 'Task07_diagnostic_share.zip')}`",
            "- The diagnostic package includes the loader audit, metrics and curve CSVs, compact NPZ, dual-reference/closure-pilot/response audits, status/runtime records, hashes, and optional logs.",
            "- Task-05 raw archives and Task-07 temporary/rollback wave-function files are deliberately excluded.",
            "",
        ]
    )
    return "\n".join(lines)

def explicit_solver_share_files(
    case_dir: Path,
    prefix: str,
    configuration: Mapping[str, Any],
) -> List[Path]:
    files = [
        case_file(case_dir, prefix, suffix)
        for suffix in required_solver_suffixes(configuration)
    ]
    stage_manifest = case_dir / "stage_manifest.json"
    if stage_manifest.is_file():
        files.append(stage_manifest)
    if INCLUDE_STDOUT_AND_LOGS:
        for suffix in ("stdout.txt", "simulation_log.txt"):
            path = case_file(case_dir, prefix, suffix)
            if path.is_file():
                files.append(path)
    return files


def explicit_diagnostic_solver_files(
    case_dir: Path,
    prefix: str,
    configuration: Mapping[str, Any],
) -> List[Path]:
    suffixes = [
        "configuration.json",
        "reference_audit.json",
        "operator_audit.json",
        "response_audit.json",
        "integrated_response.json",
        "run_status.json",
        "output_hashes.json",
        "07_environmental_response_solver.py",
    ]
    required = required_solver_suffixes(configuration)
    for optional_current in (CURRENT_CLOSURE_PILOT_SUFFIX, CURRENT_RUNTIME_SOLVER_SUFFIX):
        if optional_current in required and optional_current not in suffixes:
            suffixes.append(optional_current)
    files = [case_file(case_dir, prefix, suffix) for suffix in suffixes]
    stage_manifest = case_dir / "stage_manifest.json"
    if stage_manifest.is_file():
        files.append(stage_manifest)
    if INCLUDE_STDOUT_AND_LOGS:
        for suffix in ("stdout.txt", "simulation_log.txt"):
            path = case_file(case_dir, prefix, suffix)
            if path.is_file():
                files.append(path)
    return files


def run_case_loader() -> Tuple[int, Dict[str, Any]]:
    loader_source = resolve_loader_source_path()
    loader_source_hash = sha256_file(loader_source)
    case_dir = resolve_case_directory(loader_source)
    configuration_path, configuration, prefix = discover_case_configuration(
        case_dir, loader_source
    )
    output_dir = (
        Path(OUTPUT_DIRECTORY_OVERRIDE).expanduser().resolve()
        if OUTPUT_DIRECTORY_OVERRIDE is not None
        else case_dir
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = loader_output_paths(output_dir, prefix)
    clean_previous_loader_products(output_dir, prefix, loader_source)

    initializing_status = {
        "status": "initializing",
        "started_utc": utc_now_iso(),
        "loader_stage": LOADER_STAGE,
        "loader_version": LOADER_VERSION,
        "loader_source_sha256": loader_source_hash,
        "case_directory": str(case_dir),
        "output_directory": str(output_dir),
        "configuration": configuration_path.name,
    }
    atomic_write_json(paths["status"], initializing_status)

    audit = audit_case(case_dir, loader_source)
    compact_arrays = audit.pop("compact_arrays")
    audit["full_share_zip"] = paths["full_zip"].name
    audit["diagnostic_share_zip"] = paths["diagnostic_zip"].name
    metrics_row = build_metrics_row(audit)
    curve_rows, curve_fieldnames = build_curve_rows(compact_arrays)

    atomic_copy(loader_source, paths["source"])
    copied_loader_hash = sha256_file(paths["source"])
    audit["loader_source_sha256"] = loader_source_hash
    audit["copied_loader_source_sha256"] = copied_loader_hash
    audit["loader_source_copy_hash_matches"] = copied_loader_hash == loader_source_hash
    report = build_report(audit, metrics_row)

    atomic_write_json(paths["audit"], audit)
    write_csv(paths["metrics"], [metrics_row], tuple(metrics_row.keys()))
    if curve_rows and curve_fieldnames:
        write_csv(paths["curves"], curve_rows, curve_fieldnames)
    else:
        atomic_write_text(paths["curves"], "")
    atomic_write_text(paths["report"], report)

    tmp_compact = paths["compact"].with_name(paths["compact"].name + ".tmp")
    with tmp_compact.open("wb") as handle:
        np.savez_compressed(handle, **compact_arrays)
    os.replace(tmp_compact, paths["compact"])

    stable_loader_files = [
        paths["audit"],
        paths["metrics"],
        paths["curves"],
        paths["report"],
        paths["compact"],
        paths["source"],
    ]
    loader_manifest = {
        "hash_algorithm": "SHA-256",
        "case_prefix": prefix,
        "loader_source_sha256": loader_source_hash,
        "copied_loader_source_sha256": copied_loader_hash,
        "verdict": audit["verdict"],
        "files": {path.name: sha256_file(path) for path in stable_loader_files},
    }
    atomic_write_json(paths["hashes"], loader_manifest)

    final_status = {
        **initializing_status,
        "status": (
            "completed_pass"
            if audit["exit_code"] == 0
            else "completed_incomplete"
            if audit["exit_code"] == 3
            else "completed_fail"
        ),
        "completed_utc": utc_now_iso(),
        "verdict": audit["verdict"],
        "exit_code": audit["exit_code"],
        "all_independent_checks_passed": audit["all_independent_checks_passed"],
        "failed_check_count": len(audit["failed_checks"]),
        "pending_items": audit["pending_items"],
        "copied_loader_source_sha256": copied_loader_hash,
        "loader_source_copy_hash_matches": copied_loader_hash == loader_source_hash,
        "loader_output_hash_manifest": paths["hashes"].name,
        "loader_output_hash_manifest_sha256": sha256_file(paths["hashes"]),
        "full_share_zip": paths["full_zip"].name,
        "diagnostic_share_zip": paths["diagnostic_zip"].name,
    }
    atomic_write_json(paths["status"], final_status)

    loader_share_files = stable_loader_files + [paths["hashes"], paths["status"]]
    full_files = (
        explicit_solver_share_files(case_dir, prefix, configuration)
        + loader_share_files
    )
    diagnostic_files = (
        explicit_diagnostic_solver_files(case_dir, prefix, configuration)
        + loader_share_files
    )
    full_zip_audit = create_zip(paths["full_zip"], full_files)
    diagnostic_zip_audit = create_zip(paths["diagnostic_zip"], diagnostic_files)
    if not (
        full_zip_audit["all_member_hashes_match_sources"]
        and diagnostic_zip_audit["all_member_hashes_match_sources"]
    ):
        raise RuntimeError(
            "ZIP member verification failed: "
            f"full={full_zip_audit}, diagnostic={diagnostic_zip_audit}"
        )

    return int(audit["exit_code"]), {
        "verdict": audit["verdict"],
        "case_prefix": prefix,
        "case_directory": str(case_dir),
        "output_directory": str(output_dir),
        "all_independent_checks_passed": audit["all_independent_checks_passed"],
        "failed_checks": audit["failed_checks"],
        "pending_items": audit["pending_items"],
        "full_share_zip": str(paths["full_zip"]),
        "diagnostic_share_zip": str(paths["diagnostic_zip"]),
        "full_share_zip_sha256": full_zip_audit["zip_sha256"],
        "diagnostic_share_zip_sha256": diagnostic_zip_audit["zip_sha256"],
        "full_share_member_count": full_zip_audit["member_count"],
        "diagnostic_share_member_count": diagnostic_zip_audit["member_count"],
    }


def main() -> int:
    try:
        exit_code, summary = run_case_loader()
        print("\n[Task-07 independent per-case loader]")
        print(f"  verdict:                     {summary['verdict']}")
        print(f"  case prefix:                 {summary['case_prefix']}")
        print(f"  independent checks passed:   {summary['all_independent_checks_passed']}")
        print(f"  failed checks:               {len(summary['failed_checks'])}")
        for name in summary["failed_checks"]:
            print(f"    FAIL: {name}")
        print(f"  pending items:               {len(summary['pending_items'])}")
        for name in summary["pending_items"]:
            print(f"    PENDING: {name}")
        print(f"  full share ZIP:              {summary['full_share_zip']}")
        print(f"  full share SHA-256:          {summary['full_share_zip_sha256']}")
        print(f"  full share members:          {summary['full_share_member_count']}")
        print(f"  diagnostic share ZIP:        {summary['diagnostic_share_zip']}")
        print(f"  diagnostic share SHA-256:    {summary['diagnostic_share_zip_sha256']}")
        print(f"  diagnostic members:          {summary['diagnostic_share_member_count']}")
        return exit_code
    except Exception as exc:
        try:
            try:
                loader_source = resolve_loader_source_path()
            except Exception:
                loader_source = None
            case_dir = resolve_case_directory(loader_source)
            try:
                _configuration_path, _configuration, prefix = discover_case_configuration(
                    case_dir, loader_source
                )
            except Exception:
                prefix = "Task07_unknown_case"
            output_dir = (
                Path(OUTPUT_DIRECTORY_OVERRIDE).expanduser().resolve()
                if OUTPUT_DIRECTORY_OVERRIDE is not None
                else case_dir
            )
            output_dir.mkdir(parents=True, exist_ok=True)
            paths = loader_output_paths(output_dir, prefix)
            failure = {
                "status": "failed",
                "failed_utc": utc_now_iso(),
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc(),
            }
            atomic_write_json(paths["failure"], failure)
            atomic_write_json(
                paths["status"],
                {**failure, "verdict": "ERROR", "exit_code": 1},
            )
            try:
                diagnostic = explicit_diagnostic_solver_files(case_dir, prefix) + [
                    paths["failure"], paths["status"]
                ]
                create_zip(paths["diagnostic_zip"], diagnostic)
                print(f"Task-07 diagnostic share ZIP: {paths['diagnostic_zip']}")
            except Exception:
                pass
        except Exception:
            pass
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    _task07_loader_exit_code = main()
    if "IPython" in sys.modules:
        print(f"\nTask-07 case-loader exit code: {_task07_loader_exit_code}")
    else:
        raise SystemExit(_task07_loader_exit_code)
