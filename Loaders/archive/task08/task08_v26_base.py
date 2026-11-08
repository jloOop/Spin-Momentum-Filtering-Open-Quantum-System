#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
08_environmental_response_aggregate_loader.py
==============================================

Independent read-only Task-08 aggregate loader for the Part-I open-system
absorbing-boundary detector project.

Authority and scope
-------------------
This loader implements the data contract frozen by:

1. NUM_Open_System_PartI_Master_Audit_Audit00_to_Task06_Qualified_PASS_and_Task07_Handoff_2026-08-03.md
2. NUM_Task07_Final_Production_and_Task08_Independent_Aggregate_Loader_Handoff_2026-08-06.md

It audits the complete D1--D5, U1--U5, P1--P5 zero-rate response matrix. It is
read-only with respect to Task-07/Task-05 inputs, CPU-only, Jupyter-safe, and
supports incomplete/incremental data sets. A discovered folder that has not yet
written a completed production package remains MISSING/PENDING rather than being
misclassified as a completed integrity failure. It never imports or executes the
Task-07 solver or the Task-07 per-case loader, and it never accepts their PASS
flags as numerical evidence. Saved raw arrays and hashes are reconstructed
independently.

The loader deliberately separates:

* per-case scientific integrity;
* family convergence and uncertainty;
* deterministic same-prefix rerun coverage.

A case can therefore be scientifically valid while its status remains
RERUN_PENDING. No physical susceptibility claim is emitted unless every
mandatory family gate and uncertainty requirement is closed.

Exit status
-----------
0 : complete Task-08 scientific PASS (rerun coverage reported separately)
3 : scientifically incomplete/qualified; no physical claim authorized
2 : integrity or completed numerical/scientific gate failed
1 : execution or output-I/O failure

Typical terminal use
--------------------

    python 08_environmental_response_aggregate_loader.py \
        --input /path/to/task07_case_zips_or_directories \
        --task05-input /path/to/task05_or_task06_products \
        --inherited-bounds /path/to/inherited_bounds.json \
        --output-dir /path/to/Task08_Aggregate

Jupyter use
-----------

Executing the complete saved source with ``%run`` and no Task-08 arguments, or
pasting the complete source into one notebook cell, activates strict case-local
notebook defaults:

    Task-07 input:     the current Stage-07 case directory only
    Task-05 root:      the nearest common sibling-data project root
    output directory:  <current-case-directory>/4900.Task08_Independent_Aggregate

The current directory must directly contain at least one recognizable Task-07
configuration (or a Task-07 case-share ZIP containing one).  The loader never
silently climbs to the common project root for its Task-07 input.  Consequently,
copying this notebook into different Stage-07 case directories produces distinct
case-local incremental Task-08 audits.  Missing matrix roles remain explicitly
MISSING/PENDING, so a case-local run is diagnostic and does not replace the final
15-case aggregate audit.

The full aggregate behavior remains available without any numerical-core change:
set ``TASK08_INPUT_ROOT`` to the common project root, or supply normal CLI/API
arguments.  ``TASK08_TASK05_INPUT_ROOT`` and ``TASK08_OUTPUT_DIR`` remain optional
overrides.

The explicit API remains available:

    import importlib.util
    spec = importlib.util.spec_from_file_location("task08", "/path/to/08_environmental_response_aggregate_loader.py")
    task08 = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = task08
    spec.loader.exec_module(task08)
    code, summary = task08.run_task08(
        input_paths=["/path/to/cases"],
        output_dir="/path/to/Task08_Aggregate",
        task05_input_paths=["/path/to/task05"],
        inherited_bounds_path="/path/to/inherited_bounds.json",
    )

Reduced synthetic validation
----------------------------

    python 08_environmental_response_aggregate_loader.py --self-test \
        --output-dir /path/to/Task08_Synthetic_SelfTest

The self-test creates synthetic data only under its designated output tree and
runs partial-family, complete 15-case ZIP discovery, mirror deduplication,
legacy-core isolation, stable-file corruption, and coordinated non-finite-data
tests. It is not physical evidence and cannot be mixed with production inputs.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import math
import os
import platform
import shutil
import sys
import tempfile
import traceback
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

import numpy as np


# =============================================================================
# FROZEN TASK-08 AUTHORITY CONTRACT
# =============================================================================
LOADER_VERSION = "2026-08-07-task08-independent-aggregate-loader-v2.6-case-local-jupyter-input"
STAGE_NAME = "08_environmental_response_aggregate_loader"
TASK07_STAGE_NAME = "07_environmental_response_solver"
TASK05_STAGE_NAME = "05_oscillator_channel_detector_test"

MASTER_AUDIT_EXPECTED_SHA256 = (
    "0ceecbbf22b01b0242946c75a9b18d018f248225b70e3614fe418057ba3f4b3b"
)
# Hash of the exact final handoff copy attached in this session.
TASK07_TASK08_HANDOFF_EXPECTED_SHA256 = (
    "d7f4a629c9b21bdf3508193a9a2c585b050c63371bcfd0aea14631f168f32536"
)
FROZEN_TASK07_V8_NUMERICAL_CORE_SHA256 = (
    "827fd4993707152393a8adcf891df59d7b4d02310a06e89dd5263c0fd37369af"
)
FROZEN_TASK07_CASE_LOADER_SHA256 = (
    "3ec8f9699b2182ebd73e17e64bfbd6fc783df5d9e1ee9dc29cfd7f64c0f91d14"
)
EXPECTED_TASK07_SCRIPT_VERSION = (
    "2026-08-05-task07-environmental-response-v8-unified-manual-full-production"
)

# The attached master audit remains the highest workflow authority. It grants a
# qualified available-data PASS to Task 05/06 but records full upstream branch
# closure as pending. A successful Task-08 audit can therefore establish the
# frozen finite-v8 zero-rate response family while publication-level project
# closure remains provisional until an updated master audit closes those items.
ATTACHED_MASTER_TASK05_06_STATUS = "QUALIFIED_PASS_FULL_CLOSURE_PENDING"
ATTACHED_MASTER_PUBLICATION_LEVEL_STATUS = (
    "PROVISIONAL_UNTIL_RESIDUAL_TASK05_06_CLOSURE_IS_RECORDED_IN_AN_UPDATED_MASTER"
)

T_CUT_DEFAULT = 3.6
EXPECTED_T_FINAL = 10.0
EXPECTED_INSERTION_DT = 1.0e-1
EXPECTED_N_Z = 1500
EXPECTED_L_Z = 20.0
EXPECTED_RESPONSE_RTOL = 1.0e-10
EXPECTED_BRANCH_RTOL = 1.0e-10

# Local per-case gates.
OPERATOR_TOL = 1.0e-12
ARRAY_ABS_TOL = 5.0e-12
ARRAY_REL_TOL = 5.0e-12
TASK05_REFERENCE_ARRAY_ABS_TOL = 5.0e-11
TASK05_SOURCE_CURVE_ABS_TOL = 5.0e-10
TRUE_RESIDUAL_TOL = 1.0e-8
SOURCE_TRACE_ABS_TOL = 5.0e-11
LAUNCH_SOURCE_ABS_TOL = 1.0e-12
CLOSURE_PILOT_ABS_TOL = 1.0e-10
TANGENT_CLOSURE_ABS_TOL = 5.0e-10
TANGENT_CLOSURE_REL_TOL = 1.0e-7
KERNEL_CLOSURE_ABS_TOL = 5.0e-8
SCALAR_KERNEL_ABS_TOL = 5.0e-9
SCALAR_RESPONSE_ABS_TOL = 1.0e-8
BENCHMARK_ABS_TOL = 5.0e-10
BENCHMARK_REL_TOL = 1.0e-7
INSERTION_CONVERGENCE_ABS_TOL = 5.0e-9
INSERTION_CONVERGENCE_REL_TOL = 5.0e-2
FAMILY_RESPONSE_ABS_TOL = 5.0e-9
FAMILY_RESPONSE_REL_TOL = 5.0e-2
UPWARD_STATIC_KERNEL_ABS_TOL = 5.0e-8
UPWARD_STATIC_KERNEL_REL_TOL = 1.0e-6
EVIDENCE_FACTOR = 5.0

STATUS_MISSING = "MISSING"
STATUS_LOCAL_PASS = "LOCAL_PASS"
STATUS_RERUN_PENDING = "RERUN_PENDING"
STATUS_FAILED = "FAILED"
STATUS_CLOSED = "CLOSED"
ALLOWED_CASE_STATUSES = (
    STATUS_MISSING,
    STATUS_LOCAL_PASS,
    STATUS_RERUN_PENDING,
    STATUS_FAILED,
    STATUS_CLOSED,
)

SCIENTIFIC_VERDICTS = (
    "PASS_TASK08_LINEAR_RESPONSE",
    "PASS_TASK08_ALL_CHANNELS_ZERO_COMPATIBLE",
    "INCOMPLETE_REQUIRED_CASE_MATRIX",
    "FAIL_INPUT_INTEGRITY",
    "FAIL_CASE_LOCAL_NUMERICS",
    "FAIL_SCALAR_POINTWISE_NULL",
    "FAIL_TIME_STEP_CONVERGENCE",
    "FAIL_SHELL_CONVERGENCE",
    "UNRESOLVED_NUMERICAL_EVIDENCE",
    "QUALIFIED_PASS_MISSING_INDEPENDENT_TASK05_RAW_INPUT",
)

EVIDENCE_RESOLVED = "RESOLVED_NONZERO"
EVIDENCE_ZERO = "CONSISTENT_WITH_ZERO"
EVIDENCE_UNRESOLVED = "UNRESOLVED"
EVIDENCE_BUDGET_INCOMPLETE = "BUDGET_INCOMPLETE"

# Exact raw solver products. Runtime/log/status products are present but are not
# part of the deterministic scientific manifest.
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
NONDETERMINISTIC_SOLVER_SUFFIXES = {
    "run_status.json",
    "output_hashes.json",
    "runtime_metrics.json",
    "stdout.txt",
    "simulation_log.txt",
    "failure.json",
}

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

TASK08_OUTPUT_FILENAMES = (
    "Task08_configuration.json",
    "Task08_input_inventory.json",
    "Task08_case_identity_table.csv",
    "Task08_case_integrity_audit.json",
    "Task08_per_case_metrics.csv",
    "Task08_scalar_null_audit.json",
    "Task08_downward_family_audit.json",
    "Task08_upward_family_audit.json",
    "Task08_dephasing_family_audit.json",
    "Task08_time_step_convergence.csv",
    "Task08_shell_convergence.csv",
    "Task08_confinement_comparison.csv",
    "Task08_prompt_late_metrics.csv",
    "Task08_complete_response_curves.csv",
    "Task08_uncertainty_budget.json",
    "Task08_evidence_classification.json",
    "Task08_reproducibility_coverage.json",
    "Task08_channel_superposition_audit.json",
    "Task08_aggregate_report.md",
    "Task08_compact_results.npz",
    "Task08_output_hashes.json",
    "Task08_run_status.json",
    "Task08_loader.py",
    "Task08_share.zip",
    "Task08_diagnostic_share.zip",
)


# =============================================================================
# DATA CLASSES AND FROZEN MATRIX
# =============================================================================
@dataclass(frozen=True)
class MatrixCaseSpec:
    matrix_id: str
    propagator_type: str
    environment_direction: str
    omega: float
    initial_mode: str
    n_shell: int
    dt: float
    t_final: float
    insertion_dt: float
    role: str

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

    def key(self) -> Tuple[Any, ...]:
        return (
            self.propagator_type,
            self.environment_direction,
            round(self.omega, 14),
            self.initial_mode,
            self.n_shell,
            round(self.dt, 16),
            round(self.t_final, 14),
            round(self.insertion_dt, 14),
        )


@dataclass
class CandidateRecord:
    package: "PackageView"
    configuration_name: str
    prefix: str
    configuration: Dict[str, Any]
    identity: Optional[CaseIdentity] = None
    matrix_id: Optional[str] = None
    scientific_fingerprint: Optional[str] = None
    required_file_count: int = 0
    discovery_errors: List[str] = field(default_factory=list)
    discovery_warnings: List[str] = field(default_factory=list)


@dataclass
class CaseAuditResult:
    matrix_id: str
    spec: MatrixCaseSpec
    status: str
    scientific_admissible: bool
    reproducibility_closed: bool
    selected_candidate: Optional[CandidateRecord]
    mirror_origins: List[str]
    conflicting_origins: List[str]
    checks: Dict[str, bool]
    failed_checks: List[str]
    warnings: List[str]
    pending_items: List[str]
    metrics: Dict[str, Any]
    arrays: Dict[str, np.ndarray]
    configuration: Dict[str, Any]
    provenance: Dict[str, Any]


@dataclass
class Task08Options:
    input_paths: Tuple[Path, ...]
    output_dir: Path
    task05_input_paths: Tuple[Path, ...] = ()
    inherited_bounds_path: Optional[Path] = None
    master_audit_path: Optional[Path] = None
    handoff_path: Optional[Path] = None
    strict_reruns: bool = False
    allow_missing_per_case_loader: bool = False
    max_zip_member_bytes: int = 2 * 1024 * 1024 * 1024
    synthetic_mode: bool = False
    expected_numerical_core_sha256: str = FROZEN_TASK07_V8_NUMERICAL_CORE_SHA256


def frozen_matrix() -> Tuple[MatrixCaseSpec, ...]:
    rows: List[MatrixCaseSpec] = []
    family_prefix = {"downward": "D", "upward": "U", "dephasing": "P"}
    for direction in ("downward", "upward", "dephasing"):
        letter = family_prefix[direction]
        rows.extend(
            [
                MatrixCaseSpec(
                    f"{letter}1", "scalar_factorized", direction, 100.0, "00",
                    12, 5.0e-4, 10.0, 1.0e-1, "scalar_exact_null"
                ),
                MatrixCaseSpec(
                    f"{letter}2", "spinor", direction, 100.0, "00",
                    12, 5.0e-4, 10.0, 1.0e-1, "principal_baseline"
                ),
                MatrixCaseSpec(
                    f"{letter}3", "spinor", direction, 1.0, "00",
                    12, 1.0e-3, 10.0, 1.0e-1, "weak_confinement_control"
                ),
                MatrixCaseSpec(
                    f"{letter}4", "spinor", direction, 100.0, "00",
                    12, 2.5e-4, 10.0, 1.0e-1, "time_step_control"
                ),
                MatrixCaseSpec(
                    f"{letter}5", "spinor", direction, 100.0, "00",
                    16, 5.0e-4, 10.0, 1.0e-1, "shell_cutoff_control"
                ),
            ]
        )
    return tuple(rows)


FROZEN_MATRIX = frozen_matrix()
SPEC_BY_ID = {spec.matrix_id: spec for spec in FROZEN_MATRIX}
SPEC_BY_KEY = {
    CaseIdentity(
        spec.propagator_type,
        spec.environment_direction,
        spec.omega,
        spec.initial_mode,
        spec.n_shell,
        spec.dt,
        spec.t_final,
        spec.insertion_dt,
    ).key(): spec
    for spec in FROZEN_MATRIX
}


# =============================================================================
# GENERAL UTILITIES
# =============================================================================
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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


def canonical_task05_prefix(
    propagator_type: str,
    omega: float,
    initial_mode: str,
    n_shell: int,
    dt: float,
    t_final: float,
) -> str:
    return (
        f"{propagator_type}_omega{_number_token(omega)}_"
        f"mode{initial_mode}_N{int(n_shell)}_dt{_number_token(dt)}_"
        f"T{_number_token(t_final)}"
    )


def json_safe(value: Any, path: str = "root") -> Any:
    """Convert derived values to strict JSON without masking raw-array errors.

    Required raw scientific arrays are validated separately and any NaN/Inf in
    them is a hard failure. For unavailable *derived* values, callers pass None.
    This routine rejects non-finite numbers rather than converting them to zero.
    """
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError(f"Non-finite value at {path}: {numeric!r}")
        return numeric
    if isinstance(value, np.ndarray):
        if value.dtype.kind in "fc" and not np.all(np.isfinite(value)):
            raise ValueError(f"Non-finite NumPy array at {path}")
        return value.tolist()
    if isinstance(value, Mapping):
        return {
            str(key): json_safe(item, f"{path}.{key}")
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item, f"{path}[{index}]") for index, item in enumerate(value)]
    if hasattr(value, "__dict__"):
        return json_safe(vars(value), path)
    raise TypeError(f"Unsupported JSON value at {path}: {type(value).__name__}")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
    safe = json_safe(payload)
    encoded = json.dumps(
        safe,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def atomic_write_text(path: Path, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    safe = json_safe(payload)
    text = json.dumps(
        safe,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n"
    atomic_write_text(path, text)


def read_json_file(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise TypeError(f"Expected JSON object in {path}")
    return payload


def atomic_write_csv(
    path: Path,
    rows: Sequence[Mapping[str, Any]],
    fieldnames: Optional[Sequence[str]] = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        names: List[str] = []
        seen: Set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    names.append(str(key))
        fieldnames = names
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            serialized: Dict[str, Any] = {}
            for key in fieldnames:
                value = row.get(key)
                if isinstance(value, (dict, list, tuple)):
                    serialized[key] = json.dumps(json_safe(value), sort_keys=True, allow_nan=False)
                elif value is None:
                    serialized[key] = ""
                elif isinstance(value, (float, np.floating)):
                    number = float(value)
                    serialized[key] = (
                        "NONFINITE_DERIVED" if not math.isfinite(number) else repr(number)
                    )
                else:
                    serialized[key] = value
            writer.writerow(serialized)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def atomic_savez(path: Path, *, compressed: bool = True, **arrays: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("wb") as handle:
        if compressed:
            np.savez_compressed(handle, **arrays)
        else:
            np.savez(handle, **arrays)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def dense_max_abs(array: np.ndarray) -> float:
    arr = np.asarray(array)
    return 0.0 if arr.size == 0 else float(np.max(np.abs(arr)))


def trapezoid_integral(y: np.ndarray, x: np.ndarray) -> float:
    """NumPy-version-compatible trapezoidal integral."""
    function = getattr(np, "trapezoid", None)
    if function is None:  # NumPy < 2.0
        function = np.trapz
    return float(function(y, x))


def max_abs_difference(left: np.ndarray, right: np.ndarray) -> float:
    a = np.asarray(left)
    b = np.asarray(right)
    if a.shape != b.shape:
        return float("inf")
    return dense_max_abs(a - b)


def finite_float(value: Any) -> Optional[float]:
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return numeric if math.isfinite(numeric) else None


def all_finite(*arrays: np.ndarray) -> bool:
    for array in arrays:
        arr = np.asarray(array)
        if arr.dtype.kind in "fc" and not np.all(np.isfinite(arr)):
            return False
    return True


def numpy_metadata_text(value: Any) -> str:
    """Return deterministic human-readable text from a scalar/1-D NumPy field."""
    array = np.asarray(value)
    if array.size == 0:
        return ""
    flattened = array.reshape(-1)
    return " ".join(str(item) for item in flattened.tolist()).strip()


def flatten_boolean_checks(
    prefix: str,
    payload: Mapping[str, Any],
    output: MutableMapping[str, bool],
) -> None:
    for key, value in payload.items():
        name = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, Mapping):
            flatten_boolean_checks(name, value, output)
        elif isinstance(value, (bool, np.bool_)):
            output[name] = bool(value)


def nested_get(payload: Mapping[str, Any], *paths: str, default: Any = None) -> Any:
    for path in paths:
        current: Any = payload
        found = True
        for part in path.split("."):
            if not isinstance(current, Mapping) or part not in current:
                found = False
                break
            current = current[part]
        if found:
            return current
    return default


def identify_case(configuration: Mapping[str, Any]) -> CaseIdentity:
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


def matrix_spec_for_identity(identity: CaseIdentity) -> Optional[MatrixCaseSpec]:
    return SPEC_BY_KEY.get(identity.key())


def expected_insertion_grid(
    configuration: Mapping[str, Any],
) -> Tuple[np.ndarray, np.ndarray]:
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
        raise ValueError("Invalid num_steps or insertion_stride_steps")
    if not np.isclose(num_steps * dt, t_final, rtol=0.0, atol=1.0e-12):
        raise ValueError("T_final / dt is not integral")
    if not np.isclose(
        stride * dt,
        float(configuration["insertion_dt"]),
        rtol=0.0,
        atol=1.0e-12,
    ):
        raise ValueError("insertion_dt is not an integer multiple of dt")
    steps = list(range(0, num_steps + 1, stride))
    if steps[-1] != num_steps:
        steps.append(num_steps)
    step_array = np.asarray(steps, dtype=np.int64)
    return step_array, step_array.astype(np.float64) * dt


def prefix_trapezoid_weights(times: np.ndarray, final_index: int) -> np.ndarray:
    t = np.asarray(times, dtype=np.float64)
    if final_index < 0 or final_index >= t.size:
        raise IndexError("final_index outside time grid")
    result = np.zeros(final_index + 1, dtype=np.float64)
    if final_index == 0:
        return result
    intervals = np.diff(t[: final_index + 1])
    if np.any(intervals <= 0.0):
        raise ValueError("Time grid is not strictly increasing")
    result[0] = 0.5 * intervals[0]
    result[-1] = 0.5 * intervals[-1]
    if final_index > 1:
        result[1:-1] = 0.5 * (intervals[:-1] + intervals[1:])
    return result


def kernel_survival_from_panel_probability(kernel_probability: np.ndarray) -> np.ndarray:
    probability = np.asarray(kernel_probability, dtype=np.float64)
    panels, insertions = probability.shape
    result = np.zeros((panels + 1, insertions), dtype=np.float64)
    for insertion in range(insertions):
        if insertion >= panels:
            continue
        result[insertion + 1 :, insertion] = -np.cumsum(
            probability[insertion:, insertion], dtype=np.float64
        )
    return result


def reconstruct_response_from_kernel(
    insertion_times: np.ndarray,
    kernel_probability: np.ndarray,
    kernel_survival: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    times = np.asarray(insertion_times, dtype=np.float64)
    probability = np.asarray(kernel_probability, dtype=np.float64)
    survival = np.asarray(kernel_survival, dtype=np.float64)
    panels, nodes = probability.shape
    if nodes != panels + 1:
        raise ValueError("Kernel must have one more insertion node than output panels")
    if survival.shape != (nodes, nodes):
        raise ValueError("Survival kernel shape mismatch")
    chi_s = np.zeros(nodes, dtype=np.float64)
    chi_p = np.zeros(panels, dtype=np.float64)
    for state_index in range(nodes):
        weights = prefix_trapezoid_weights(times, state_index)
        chi_s[state_index] = float(
            np.dot(weights, survival[state_index, : state_index + 1])
        )
    for panel in range(panels):
        weights = prefix_trapezoid_weights(times, panel + 1)
        chi_p[panel] = float(
            np.dot(weights[: panel + 1], probability[panel, : panel + 1])
        )
    durations = np.diff(times)
    return chi_s, chi_p, chi_p / durations


def coarse_grid_indices(number_nodes: int) -> np.ndarray:
    if number_nodes < 2:
        raise ValueError("At least two nodes required")
    indices = list(range(0, number_nodes, 2))
    if indices[-1] != number_nodes - 1:
        indices.append(number_nodes - 1)
    return np.asarray(indices, dtype=np.int64)


def aggregate_kernel_to_coarse(
    fine_times: np.ndarray,
    fine_kernel_probability: np.ndarray,
    fine_kernel_survival: np.ndarray,
) -> Dict[str, np.ndarray]:
    times = np.asarray(fine_times, dtype=np.float64)
    fine_probability = np.asarray(fine_kernel_probability, dtype=np.float64)
    fine_survival = np.asarray(fine_kernel_survival, dtype=np.float64)
    node_indices = coarse_grid_indices(times.size)
    coarse_times = times[node_indices]
    coarse_panels = coarse_times.size - 1
    coarse_kernel = np.zeros((coarse_panels, coarse_times.size), dtype=np.float64)
    for coarse_panel in range(coarse_panels):
        first = int(node_indices[coarse_panel])
        last = int(node_indices[coarse_panel + 1])
        for coarse_insertion, fine_insertion in enumerate(node_indices):
            if coarse_insertion > coarse_panel:
                break
            coarse_kernel[coarse_panel, coarse_insertion] = float(
                np.sum(
                    fine_probability[first:last, int(fine_insertion)],
                    dtype=np.float64,
                )
            )
    coarse_survival_kernel = fine_survival[np.ix_(node_indices, node_indices)]
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
    times = np.asarray(fine_times, dtype=np.float64)
    fine_s = np.asarray(fine_chi_survival, dtype=np.float64)
    fine_p = np.asarray(fine_chi_panel_probability, dtype=np.float64)
    indices = np.asarray(coarse["node_indices"], dtype=np.int64)
    coarse_s = np.asarray(coarse["chi_survival"], dtype=np.float64)
    fine_s_sampled = fine_s[indices]
    fine_p_aggregated = np.zeros(indices.size - 1, dtype=np.float64)
    for panel in range(indices.size - 1):
        fine_p_aggregated[panel] = float(
            np.sum(fine_p[indices[panel] : indices[panel + 1]], dtype=np.float64)
        )
    coarse_p = np.asarray(coarse["chi_panel_probability"], dtype=np.float64)
    distance = 0.5 * (
        float(np.sum(np.abs(fine_p_aggregated - coarse_p), dtype=np.float64))
        + abs(float(fine_s_sampled[-1] - coarse_s[-1]))
    )
    fine_norm = 0.5 * (
        float(np.sum(np.abs(fine_p_aggregated), dtype=np.float64))
        + abs(float(fine_s_sampled[-1]))
    )
    coarse_norm = 0.5 * (
        float(np.sum(np.abs(coarse_p), dtype=np.float64))
        + abs(float(coarse_s[-1]))
    )
    fine_mu = trapezoid_integral(fine_s, times)
    coarse_times = np.asarray(coarse["times"], dtype=np.float64)
    coarse_mu = trapezoid_integral(coarse_s, coarse_times)
    mu_difference = abs(fine_mu - coarse_mu)
    return {
        "signed_measure_distance": distance,
        "relative_signed_measure_distance": distance
        / max(fine_norm, coarse_norm, INSERTION_CONVERGENCE_ABS_TOL),
        "maximum_abs_survival_difference": dense_max_abs(fine_s_sampled - coarse_s),
        "survival_L1_difference_on_coarse_grid": trapezoid_integral(
            np.abs(fine_s_sampled - coarse_s), coarse_times
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
    t = np.asarray(times, dtype=np.float64)
    chi_s = np.asarray(chi_survival, dtype=np.float64)
    chi_p = np.asarray(chi_panel_probability, dtype=np.float64)
    chi_g = np.asarray(chi_click_density, dtype=np.float64)
    chi_d = float(np.sum(chi_p, dtype=np.float64))
    chi_mu = trapezoid_integral(chi_s, t)
    early = 0.0
    late = 0.0
    for panel, (left, right) in enumerate(zip(t[:-1], t[1:])):
        duration = float(right - left)
        if right <= t_cut:
            early += float(chi_p[panel])
        elif left >= t_cut:
            late += float(chi_p[panel])
        else:
            fraction = (t_cut - left) / duration
            early += fraction * float(chi_p[panel])
            late += (1.0 - fraction) * float(chi_p[panel])
    complete_norm = 0.5 * (
        float(np.sum(np.abs(chi_p), dtype=np.float64))
        + abs(float(chi_s[-1]))
    )
    return {
        "chi_D_from_panel_sum": chi_d,
        "chi_D_from_final_survival": -float(chi_s[-1]),
        "chi_mu_restricted": chi_mu,
        "chi_D_E": early,
        "chi_D_L": late,
        "chi_complete_signed_measure_norm": complete_norm,
        "chi_survival_W1_norm": trapezoid_integral(np.abs(chi_s), t),
        "maximum_abs_chi_survival": dense_max_abs(chi_s),
        "maximum_abs_chi_click_density": dense_max_abs(chi_g),
        "minimum_chi_click_density": float(np.min(chi_g)),
        "maximum_chi_click_density": float(np.max(chi_g)),
    }


def signed_response_distance(
    times_a: np.ndarray,
    chi_s_a: np.ndarray,
    chi_p_a: np.ndarray,
    times_b: np.ndarray,
    chi_s_b: np.ndarray,
    chi_p_b: np.ndarray,
) -> Dict[str, float]:
    ta = np.asarray(times_a, dtype=np.float64)
    tb = np.asarray(times_b, dtype=np.float64)
    sa = np.asarray(chi_s_a, dtype=np.float64)
    sb = np.asarray(chi_s_b, dtype=np.float64)
    pa = np.asarray(chi_p_a, dtype=np.float64)
    pb = np.asarray(chi_p_b, dtype=np.float64)
    if ta.shape != tb.shape or max_abs_difference(ta, tb) > 2.0e-12:
        raise ValueError("Family response grids are not identical")
    if sa.shape != sb.shape or pa.shape != pb.shape:
        raise ValueError("Family response shapes are not identical")
    distance = 0.5 * (
        float(np.sum(np.abs(pa - pb), dtype=np.float64))
        + abs(float(sa[-1] - sb[-1]))
    )
    norm_a = 0.5 * (
        float(np.sum(np.abs(pa), dtype=np.float64)) + abs(float(sa[-1]))
    )
    norm_b = 0.5 * (
        float(np.sum(np.abs(pb), dtype=np.float64)) + abs(float(sb[-1]))
    )
    return {
        "complete_signed_measure_distance": distance,
        "relative_signed_measure_distance": distance
        / max(norm_a, norm_b, FAMILY_RESPONSE_ABS_TOL),
        "baseline_response_norm": norm_a,
        "control_response_norm": norm_b,
        "maximum_abs_survival_difference": dense_max_abs(sa - sb),
        "survival_W1_difference": trapezoid_integral(np.abs(sa - sb), ta),
        "chi_D_absolute_difference": abs(float(np.sum(pa) - np.sum(pb))),
        "chi_mu_absolute_difference": abs(
            trapezoid_integral(sa, ta) - trapezoid_integral(sb, tb)
        ),
    }


# =============================================================================
# READ-ONLY PACKAGE ABSTRACTION
# =============================================================================
class PackageView:
    """Read-only view of one candidate case directory or ZIP subtree."""

    kind: str
    origin: str
    base_label: str
    prefix: str

    def list_basenames(self) -> Tuple[str, ...]:
        raise NotImplementedError

    def exists(self, basename: str) -> bool:
        return basename in set(self.list_basenames())

    def read_bytes(self, basename: str) -> bytes:
        raise NotImplementedError

    def sha256(self, basename: str) -> str:
        return sha256_bytes(self.read_bytes(basename))

    def read_json(self, basename: str) -> Dict[str, Any]:
        payload = json.loads(self.read_bytes(basename).decode("utf-8"))
        if not isinstance(payload, dict):
            raise TypeError(f"Expected JSON object in {self.origin}:{basename}")
        return payload

    def load_npy(self, basename: str) -> np.ndarray:
        with io.BytesIO(self.read_bytes(basename)) as handle:
            return np.load(handle, allow_pickle=False)

    def load_npz(self, basename: str) -> Dict[str, np.ndarray]:
        with io.BytesIO(self.read_bytes(basename)) as handle:
            with np.load(handle, allow_pickle=False) as archive:
                return {name: np.asarray(archive[name]) for name in archive.files}

    def describe(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "origin": self.origin,
            "base_label": self.base_label,
            "prefix": self.prefix,
            "file_count": len(self.list_basenames()),
        }


class DirectoryPackage(PackageView):
    def __init__(self, directory: Path, prefix: str):
        self.kind = "directory"
        self.directory = directory.expanduser().resolve()
        self.origin = str(self.directory)
        self.base_label = self.directory.name
        self.prefix = prefix
        self._files = tuple(
            sorted(
                path.name
                for path in self.directory.iterdir()
                if path.is_file() and not path.name.endswith(".tmp")
            )
        )

    def list_basenames(self) -> Tuple[str, ...]:
        return self._files

    def read_bytes(self, basename: str) -> bytes:
        if Path(basename).name != basename:
            raise ValueError(f"Unsafe basename requested: {basename!r}")
        path = (self.directory / basename).resolve()
        if path.parent != self.directory:
            raise ValueError(f"Path escapes case directory: {basename!r}")
        return path.read_bytes()


class ZipPackage(PackageView):
    def __init__(
        self,
        zip_path: Path,
        base_member: str,
        prefix: str,
        *,
        max_member_bytes: int,
    ):
        self.kind = "zip"
        self.zip_path = zip_path.expanduser().resolve()
        self.origin = str(self.zip_path)
        self.base_member = base_member.strip("/")
        self.base_label = self.base_member or self.zip_path.stem
        self.prefix = prefix
        self.max_member_bytes = int(max_member_bytes)
        with zipfile.ZipFile(self.zip_path, "r") as archive:
            infos = archive.infolist()
        names = [info.filename for info in infos]
        self.duplicate_members = sorted(
            {name for name in names if names.count(name) > 1}
        )
        self.unsafe_members: List[str] = []
        basename_to_member: Dict[str, str] = {}
        for info in infos:
            name = info.filename
            path = PurePosixPath(name)
            unsafe = (
                path.is_absolute()
                or ".." in path.parts
                or any(part in {"", "."} for part in path.parts[:-1])
                or info.file_size > self.max_member_bytes
            )
            if unsafe:
                self.unsafe_members.append(name)
                continue
            parent = str(path.parent)
            if parent == ".":
                parent = ""
            if parent == self.base_member and not name.endswith("/"):
                basename = path.name
                if basename in basename_to_member:
                    self.duplicate_members.append(name)
                basename_to_member[basename] = name
        self._members = basename_to_member
        self._files = tuple(sorted(self._members))

    def list_basenames(self) -> Tuple[str, ...]:
        return self._files

    def read_bytes(self, basename: str) -> bytes:
        if basename not in self._members:
            raise FileNotFoundError(f"ZIP member missing: {self.origin}:{basename}")
        member = self._members[basename]
        with zipfile.ZipFile(self.zip_path, "r") as archive:
            info = archive.getinfo(member)
            if info.file_size > self.max_member_bytes:
                raise ValueError(f"ZIP member exceeds safety limit: {member}")
            return archive.read(member)

    def describe(self) -> Dict[str, Any]:
        result = super().describe()
        result.update(
            {
                "zip_sha256": sha256_file(self.zip_path),
                "base_member": self.base_member,
                "duplicate_members": sorted(set(self.duplicate_members)),
                "unsafe_members": sorted(set(self.unsafe_members)),
            }
        )
        return result


# =============================================================================
# DISCOVERY
# =============================================================================
def iter_directory_files(
    root: Path,
    *,
    excluded_roots: Sequence[Path] = (),
) -> Iterator[Path]:
    """Yield input files recursively while excluding generated/output trees.

    The exclusion is path-based rather than name-based.  This matters when the
    Task-08 output directory is intentionally created as a sibling below the
    same broad ``3D`` root used for Task-05/Task-07 discovery.
    """
    root = root.expanduser().resolve()
    excluded = tuple(
        resolved
        for resolved in (path.expanduser().resolve() for path in excluded_roots)
        if resolved == root or root in resolved.parents
    )

    def is_excluded(path: Path) -> bool:
        resolved = path.resolve()
        return any(resolved == item or item in resolved.parents for item in excluded)

    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current).resolve()
        if is_excluded(current_path):
            directories[:] = []
            continue
        retained: List[str] = []
        for name in directories:
            lowered = name.lower()
            child = current_path / name
            if (
                name.startswith(".")
                or "rollback" in lowered
                or "failed_attempt" in lowered
                or "tmp" in lowered
                or is_excluded(child)
            ):
                continue
            retained.append(name)
        directories[:] = retained
        for name in files:
            if name.endswith(".tmp"):
                continue
            yield current_path / name


def discover_zip_candidates(
    zip_path: Path,
    *,
    max_member_bytes: int,
    allow_synthetic: bool,
) -> List[CandidateRecord]:
    records: List[CandidateRecord] = []
    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            duplicate_names = {name for name in names if names.count(name) > 1}
            for info in infos:
                name = info.filename
                path = PurePosixPath(name)
                if (
                    name.endswith("/")
                    or not path.name.endswith("_configuration.json")
                    or path.is_absolute()
                    or ".." in path.parts
                    or name in duplicate_names
                    or info.file_size > max_member_bytes
                ):
                    continue
                try:
                    payload = json.loads(archive.read(name).decode("utf-8"))
                except Exception:
                    continue
                if not isinstance(payload, dict):
                    continue
                if payload.get("stage") != TASK07_STAGE_NAME:
                    continue
                if payload.get("smoke_test") is True and not allow_synthetic:
                    continue
                suffix = "_configuration.json"
                prefix = path.name[: -len(suffix)]
                base_member = str(path.parent)
                if base_member == ".":
                    base_member = ""
                package = ZipPackage(
                    zip_path,
                    base_member,
                    prefix,
                    max_member_bytes=max_member_bytes,
                )
                records.append(
                    CandidateRecord(
                        package=package,
                        configuration_name=path.name,
                        prefix=prefix,
                        configuration=payload,
                    )
                )
    except (zipfile.BadZipFile, OSError):
        return []
    return records


def discover_directory_candidate(config_path: Path, allow_synthetic: bool) -> Optional[CandidateRecord]:
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict) or payload.get("stage") != TASK07_STAGE_NAME:
        return None
    if payload.get("smoke_test") is True and not allow_synthetic:
        return None
    suffix = "_configuration.json"
    if not config_path.name.endswith(suffix):
        return None
    prefix = config_path.name[: -len(suffix)]
    return CandidateRecord(
        package=DirectoryPackage(config_path.parent, prefix),
        configuration_name=config_path.name,
        prefix=prefix,
        configuration=payload,
    )


def discover_candidates(options: Task08Options) -> Tuple[List[CandidateRecord], Dict[str, Any]]:
    records: List[CandidateRecord] = []
    inspected_paths: List[Dict[str, Any]] = []
    seen_config_locations: Set[Tuple[str, str]] = set()
    seen_zip_paths: Set[Path] = set()

    for input_path in options.input_paths:
        path = input_path.expanduser().resolve()
        if not path.exists():
            inspected_paths.append(
                {"path": str(path), "exists": False, "candidate_count": 0}
            )
            continue
        before = len(records)
        if path.is_file() and path.suffix.lower() == ".zip":
            seen_zip_paths.add(path)
            discovered = discover_zip_candidates(
                path,
                max_member_bytes=options.max_zip_member_bytes,
                allow_synthetic=options.synthetic_mode,
            )
            records.extend(discovered)
        elif path.is_file() and path.name.endswith("_configuration.json"):
            candidate = discover_directory_candidate(path, options.synthetic_mode)
            if candidate is not None:
                key = (candidate.package.origin, candidate.configuration_name)
                if key not in seen_config_locations:
                    seen_config_locations.add(key)
                    records.append(candidate)
        elif path.is_dir():
            for candidate_path in iter_directory_files(
                path, excluded_roots=(options.output_dir,)
            ):
                if candidate_path.suffix.lower() == ".zip":
                    resolved_zip = candidate_path.resolve()
                    if resolved_zip in seen_zip_paths:
                        continue
                    seen_zip_paths.add(resolved_zip)
                    records.extend(
                        discover_zip_candidates(
                            resolved_zip,
                            max_member_bytes=options.max_zip_member_bytes,
                            allow_synthetic=options.synthetic_mode,
                        )
                    )
                elif candidate_path.name.endswith("_configuration.json"):
                    candidate = discover_directory_candidate(
                        candidate_path, options.synthetic_mode
                    )
                    if candidate is None:
                        continue
                    key = (candidate.package.origin, candidate.configuration_name)
                    if key not in seen_config_locations:
                        seen_config_locations.add(key)
                        records.append(candidate)
        inspected_paths.append(
            {
                "path": str(path),
                "exists": True,
                "kind": "directory" if path.is_dir() else "file",
                "candidate_count": len(records) - before,
            }
        )

    # Annotate identity and scientific manifest fingerprint without yet trusting
    # any saved verdict.
    for record in records:
        try:
            record.identity = identify_case(record.configuration)
            spec = matrix_spec_for_identity(record.identity)
            record.matrix_id = spec.matrix_id if spec is not None else None
            output_hash_name = f"{record.prefix}_output_hashes.json"
            if record.package.exists(output_hash_name):
                manifest = record.package.read_json(output_hash_name)
                files = manifest.get("files", {})
                scientific_suffixes = (
                    "reference_audit.json",
                    "operator_audit.json",
                    "closure_pilot_audit.json",
                    "response_audit.json",
                    "times.npy",
                    "insertion_times.npy",
                    "chi_survival.npy",
                    "chi_click_density.npy",
                    "integrated_response.json",
                    "kernel_summary.npz",
                    "source_insertion_summary.npz",
                    "full_tangent_benchmark.npz",
                )
                scientific_files = {
                    str(name): digest
                    for name, digest in files.items()
                    if any(str(name).endswith("_" + suffix) for suffix in scientific_suffixes)
                } if isinstance(files, Mapping) else {}
                fingerprint_payload = {
                    "canonical_physical_identity": asdict(record.identity),
                    "numerical_core_sha256": record.configuration.get(
                        "numerical_core_sha256"
                    ),
                    "production_contract_sha256": record.configuration.get(
                        "production_contract_sha256"
                    ),
                    "scientific_files": scientific_files,
                }
                record.scientific_fingerprint = sha256_json(fingerprint_payload)
            else:
                record.scientific_fingerprint = sha256_json(
                    {
                        "configuration": record.configuration,
                        "present_files": record.package.list_basenames(),
                    }
                )
            required = required_solver_suffixes(record.configuration)
            record.required_file_count = sum(
                record.package.exists(f"{record.prefix}_{suffix}") for suffix in required
            )
        except Exception as exc:
            record.discovery_errors.append(f"identity_or_fingerprint_error: {exc}")

    inventory = {
        "inspected_paths": inspected_paths,
        "candidate_count": len(records),
        "candidates": [
            {
                **record.package.describe(),
                "configuration_name": record.configuration_name,
                "matrix_id": record.matrix_id,
                "canonical_identity": (
                    asdict(record.identity) if record.identity is not None else None
                ),
                "scientific_fingerprint": record.scientific_fingerprint,
                "required_file_count": record.required_file_count,
                "discovery_errors": record.discovery_errors,
                "discovery_warnings": record.discovery_warnings,
            }
            for record in records
        ],
    }
    return records, inventory


def required_solver_suffixes(configuration: Mapping[str, Any]) -> Tuple[str, ...]:
    raw_contract = configuration.get("output_contract", ())
    contract = tuple(str(item) for item in raw_contract) if isinstance(raw_contract, (list, tuple)) else ()
    required = list(CORE_REQUIRED_SOLVER_SUFFIXES)
    for suffix in (CURRENT_CLOSURE_PILOT_SUFFIX, CURRENT_RUNTIME_SOLVER_SUFFIX):
        if suffix in contract and suffix not in required:
            required.append(suffix)
    return tuple(required)


# =============================================================================
# CANDIDATE SELECTION AND DEDUPLICATION
# =============================================================================
def _candidate_is_complete(candidate: CandidateRecord) -> bool:
    """Return whether every required Task-07 production product is present."""
    return bool(
        not candidate.discovery_errors
        and candidate.required_file_count
        >= len(required_solver_suffixes(candidate.configuration))
    )


def _candidate_run_status(candidate: CandidateRecord) -> Dict[str, Any]:
    name = f"{candidate.prefix}_run_status.json"
    if not candidate.package.exists(name):
        return {}
    try:
        return candidate.package.read_json(name)
    except Exception:
        return {}


def _candidate_is_explicit_completed_failure(candidate: CandidateRecord) -> bool:
    """Identify an actual completed/recorded failure, not an in-progress folder.

    A partial directory is common while a long Task-07 job is running.  Such a
    directory must remain MISSING/PENDING in an incremental Task-08 audit.  It
    becomes FAILED only when the source package explicitly records failure.
    """
    failure_name = f"{candidate.prefix}_failure.json"
    if candidate.package.exists(failure_name):
        return True
    status = _candidate_run_status(candidate)
    status_name = str(status.get("status", "")).strip().lower()
    verdict = str(status.get("verdict", "")).strip().lower()
    explicit_boolean = bool(
        status.get("failed") is True
        or (
            status.get("all_case_local_checks_passed") is False
            and status_name.startswith("completed")
        )
    )
    status_failure = bool(
        status_name
        and status_name not in {"completed_incomplete", "running", "initializing"}
        and any(token in status_name for token in ("fail", "error", "abort"))
    )
    verdict_failure = bool(verdict and any(token in verdict for token in ("fail", "error")))
    response_name = f"{candidate.prefix}_response_audit.json"
    response_failure = False
    if candidate.package.exists(response_name):
        try:
            response = candidate.package.read_json(response_name)
            response_failure = response.get("all_case_local_checks_passed") is False
        except Exception:
            response_failure = False
    return bool(explicit_boolean or status_failure or verdict_failure or response_failure)


def _candidate_progress_record(
    candidate: CandidateRecord,
    *,
    expected_core_sha256: str,
) -> Dict[str, Any]:
    required = len(required_solver_suffixes(candidate.configuration))
    status = _candidate_run_status(candidate)
    return {
        "origin": candidate.package.origin,
        "kind": candidate.package.kind,
        "prefix": candidate.prefix,
        "required_file_count": candidate.required_file_count,
        "expected_required_file_count": required,
        "completion_fraction": (
            candidate.required_file_count / required if required > 0 else 0.0
        ),
        "numerical_core_sha256": candidate.configuration.get("numerical_core_sha256"),
        "uses_frozen_v8_core": str(
            candidate.configuration.get("numerical_core_sha256", "")
        ) == expected_core_sha256,
        "script_version": candidate.configuration.get("script_version"),
        "run_status": status.get("status"),
        "run_verdict": status.get("verdict"),
        "explicit_completed_failure": _candidate_is_explicit_completed_failure(candidate),
    }


def select_matrix_candidates(
    records: Sequence[CandidateRecord],
    *,
    expected_core_sha256: str,
) -> Tuple[Dict[str, Optional[CandidateRecord]], Dict[str, Dict[str, Any]]]:
    """Select at most one physical candidate per frozen matrix role.

    Byte-identical mirrors are deduplicated. Multiple complete candidates with
    different stable scientific fingerprints are treated as a physical conflict,
    rather than choosing one based on directory spelling or recency.
    """
    selected: Dict[str, Optional[CandidateRecord]] = {
        spec.matrix_id: None for spec in FROZEN_MATRIX
    }
    decisions: Dict[str, Dict[str, Any]] = {}
    by_role: Dict[str, List[CandidateRecord]] = {key: [] for key in selected}
    for record in records:
        if record.matrix_id in by_role:
            by_role[str(record.matrix_id)].append(record)

    for matrix_id, candidates in by_role.items():
        spec = SPEC_BY_ID[matrix_id]
        if not candidates:
            decisions[matrix_id] = {
                "matrix_id": matrix_id,
                "selected_origin": None,
                "mirror_origins": [],
                "conflicting_origins": [],
                "reason": "no candidate maps to the frozen configuration",
            }
            continue

        expected_required = len(required_solver_suffixes(candidates[0].configuration))
        complete = [candidate for candidate in candidates if _candidate_is_complete(candidate)]
        incomplete = [candidate for candidate in candidates if not _candidate_is_complete(candidate)]
        incomplete_records = [
            _candidate_progress_record(
                candidate,
                expected_core_sha256=expected_core_sha256,
            )
            for candidate in incomplete
        ]
        core_matched_complete = [
            candidate
            for candidate in complete
            if str(candidate.configuration.get("numerical_core_sha256", ""))
            == expected_core_sha256
        ]
        legacy_or_mixed_complete = [
            candidate
            for candidate in complete
            if str(candidate.configuration.get("numerical_core_sha256", ""))
            != expected_core_sha256
        ]

        # A complete legacy/mixed-core package is never promoted into the
        # formal v8 matrix merely because no current-v8 package has arrived.
        if complete and not core_matched_complete:
            decisions[matrix_id] = {
                "matrix_id": matrix_id,
                "expected": asdict(spec),
                "selected_origin": None,
                "mirror_origins": [],
                "conflicting_origins": [],
                "legacy_or_mixed_core_origins": sorted(
                    candidate.package.origin for candidate in legacy_or_mixed_complete
                ),
                "legacy_or_mixed_core_sha256": sorted(
                    {
                        str(candidate.configuration.get("numerical_core_sha256", ""))
                        for candidate in legacy_or_mixed_complete
                    }
                ),
                "incomplete_candidate_records": incomplete_records,
                "reason": (
                    "complete package(s) map to this physical identity but none "
                    "uses the frozen Task-07 v8 numerical core; formal role remains missing"
                ),
            }
            continue

        if core_matched_complete:
            pool = core_matched_complete
        else:
            # No completed frozen-v8 package exists.  Long production jobs leave
            # configuration/reference/pilot fragments while still running; in an
            # incremental audit those are pending inventory, not corrupted data.
            explicit_current_failures = [
                candidate
                for candidate in incomplete
                if str(candidate.configuration.get("numerical_core_sha256", ""))
                == expected_core_sha256
                and _candidate_is_explicit_completed_failure(candidate)
            ]
            if explicit_current_failures:
                pool = explicit_current_failures
            else:
                decisions[matrix_id] = {
                    "matrix_id": matrix_id,
                    "expected": asdict(spec),
                    "selected_origin": None,
                    "mirror_origins": [],
                    "conflicting_origins": [],
                    "incomplete_candidate_records": incomplete_records,
                    "legacy_or_mixed_core_origins": sorted(
                        candidate.package.origin
                        for candidate in incomplete
                        if str(candidate.configuration.get("numerical_core_sha256", ""))
                        != expected_core_sha256
                    ),
                    "reason": (
                        "matching Task-07 folder(s) were discovered, but no completed "
                        "frozen-v8 case package exists; formal role remains MISSING/PENDING"
                    ),
                }
                continue
        fingerprint_groups: Dict[str, List[CandidateRecord]] = {}
        for candidate in pool:
            fingerprint_groups.setdefault(
                candidate.scientific_fingerprint or "<none>", []
            ).append(candidate)

        # Distinct complete stable manifests for one physical identity are not
        # silently ordered. Incomplete fragments are allowed to coexist with a
        # unique complete candidate and are retained as rejected diagnostics.
        complete_fingerprints = {
            candidate.scientific_fingerprint
            for candidate in pool
            if candidate.required_file_count
            >= len(required_solver_suffixes(candidate.configuration))
            and candidate.scientific_fingerprint is not None
        }
        if len(complete_fingerprints) > 1:
            decisions[matrix_id] = {
                "matrix_id": matrix_id,
                "selected_origin": None,
                "mirror_origins": [],
                "conflicting_origins": sorted(
                    candidate.package.origin for candidate in pool
                ),
                "reason": (
                    "multiple complete packages with different stable scientific "
                    "fingerprints map to the same frozen physical identity"
                ),
                "fingerprints": {
                    fingerprint: sorted(item.package.origin for item in group)
                    for fingerprint, group in fingerprint_groups.items()
                },
            }
            continue

        # Prefer a closed deterministic record among scientifically identical
        # mirrors, then the most complete package. Directory versus ZIP is only
        # an I/O convenience and never enters physical identity.
        def selection_rank(item: CandidateRecord) -> Tuple[Any, ...]:
            rerun_closed = False
            loader_present = item.package.exists(
                f"{item.prefix}_case_loader_audit.json"
            )
            status_name = f"{item.prefix}_run_status.json"
            if item.package.exists(status_name):
                try:
                    status_record = item.package.read_json(status_name)
                    rerun_record = status_record.get(
                        "deterministic_same_prefix_rerun", {}
                    )
                    rerun_closed = bool(
                        isinstance(rerun_record, Mapping)
                        and rerun_record.get("passed") is True
                    )
                except Exception:
                    rerun_closed = False
            return (
                rerun_closed,
                loader_present,
                item.required_file_count,
                item.package.kind == "directory",
                item.package.origin,
            )

        ranked = sorted(pool, key=selection_rank, reverse=True)
        chosen = ranked[0]
        selected[matrix_id] = chosen
        mirrors = [
            item.package.origin
            for item in pool
            if item is not chosen
            and item.scientific_fingerprint == chosen.scientific_fingerprint
        ]
        rejected = [
            item.package.origin
            for item in pool
            if item is not chosen
            and item.scientific_fingerprint != chosen.scientific_fingerprint
        ]
        legacy_or_mixed_origins = [
            item.package.origin
            for item in candidates
            if str(item.configuration.get("numerical_core_sha256", ""))
            != expected_core_sha256
        ]
        incomplete_or_nonselected_origins = [
            item.package.origin
            for item in candidates
            if item is not chosen
            and item.package.origin not in mirrors
            and item.package.origin not in rejected
            and item.package.origin not in legacy_or_mixed_origins
        ]
        decisions[matrix_id] = {
            "matrix_id": matrix_id,
            "expected": asdict(spec),
            "selected_origin": chosen.package.origin,
            "selected_kind": chosen.package.kind,
            "selected_fingerprint": chosen.scientific_fingerprint,
            "mirror_origins": sorted(mirrors),
            "conflicting_origins": sorted(rejected),
            "legacy_or_mixed_core_origins": sorted(legacy_or_mixed_origins),
            "incomplete_candidate_records": incomplete_records,
            "incomplete_or_nonselected_origins": sorted(
                incomplete_or_nonselected_origins
            ),
            "required_file_count": chosen.required_file_count,
            "expected_required_file_count": expected_required,
            "reason": "unique best candidate selected by configuration and stable hashes",
        }
    return selected, decisions


# =============================================================================
# INDEPENDENT OPERATOR AND SOURCE-SCOPE RECONSTRUCTION
# =============================================================================
def complete_shell_labels_descending(n_shell: int) -> Tuple[Tuple[int, int], ...]:
    labels: List[Tuple[int, int]] = []
    for total in range(n_shell + 1):
        for nx in range(total, -1, -1):
            labels.append((nx, total - nx))
    return tuple(labels)


def build_projected_ladders(
    labels: Sequence[Tuple[int, int]],
) -> Tuple[np.ndarray, np.ndarray]:
    index = {label: position for position, label in enumerate(labels)}
    dimension = len(labels)
    a_x = np.zeros((dimension, dimension), dtype=np.complex128)
    a_y = np.zeros((dimension, dimension), dtype=np.complex128)
    for column, (nx, ny) in enumerate(labels):
        if nx > 0:
            a_x[index[(nx - 1, ny)], column] = math.sqrt(nx)
        if ny > 0:
            a_y[index[(nx, ny - 1)], column] = math.sqrt(ny)
    return a_x, a_y


def reconstruct_operator_contract(configuration: Mapping[str, Any]) -> Dict[str, Any]:
    n_shell = int(configuration["N_shell"])
    omega = float(configuration["omega"])
    labels = complete_shell_labels_descending(n_shell)
    expected_dimension = (n_shell + 1) * (n_shell + 2) // 2
    a_x, a_y = build_projected_ladders(labels)
    a_x_dagger = a_x.conj().T
    a_y_dagger = a_y.conj().T
    n_x = a_x_dagger @ a_x
    n_y = a_y_dagger @ a_y
    sigma_x = np.asarray([[0, 1], [1, 0]], dtype=np.complex128)
    sigma_y = np.asarray([[0, -1j], [1j, 0]], dtype=np.complex128)
    ell_perp = 1.0 / math.sqrt(omega)
    k_matrix = (
        1j
        / (math.sqrt(2.0) * ell_perp)
        * (
            np.kron(sigma_x, a_y_dagger - a_y)
            - np.kron(sigma_y, a_x_dagger - a_x)
        )
    )
    k_unit = (
        1j
        / math.sqrt(2.0)
        * (
            np.kron(sigma_x, a_y_dagger - a_y)
            - np.kron(sigma_y, a_x_dagger - a_x)
        )
    )
    nx_expected = np.diag(np.asarray([label[0] for label in labels], dtype=float))
    ny_expected = np.diag(np.asarray([label[1] for label in labels], dtype=float))
    metrics = {
        "complete_shell_orbital_dimension": len(labels),
        "spin_resolved_channel_dimension": 2 * len(labels),
        "number_x_residual": dense_max_abs(n_x - nx_expected),
        "number_y_residual": dense_max_abs(n_y - ny_expected),
        "K_hermiticity_residual": dense_max_abs(k_matrix - k_matrix.conj().T),
        "K_sqrt_omega_scaling_residual": dense_max_abs(
            k_matrix / math.sqrt(omega) - k_unit
        ),
        "a_x_adjoint_residual": dense_max_abs(a_x_dagger - a_x.conj().T),
        "a_y_adjoint_residual": dense_max_abs(a_y_dagger - a_y.conj().T),
    }
    checks = {
        "complete_shell_dimension": len(labels) == expected_dimension,
        "projected_number_operators": max(
            metrics["number_x_residual"], metrics["number_y_residual"]
        )
        <= OPERATOR_TOL,
        "K_is_Hermitian": metrics["K_hermiticity_residual"] <= OPERATOR_TOL,
        "K_has_sqrt_omega_scaling": metrics["K_sqrt_omega_scaling_residual"]
        <= OPERATOR_TOL,
        "physical_spin_dimension": k_matrix.shape
        == (2 * expected_dimension, 2 * expected_dimension),
    }
    return {
        "labels": [list(label) for label in labels],
        "metrics": metrics,
        "checks": checks,
    }


def source_scope_ast_audit(source_text: str) -> Dict[str, Any]:
    """Audit copied Task-07 source without importing or executing it."""
    try:
        tree = ast.parse(source_text)
    except SyntaxError as exc:
        return {"passed": False, "error": f"source syntax error: {exc}"}
    imports: List[str] = []
    call_names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)
    forbidden_runtime_calls = sorted(
        name
        for name in call_names
        if name.lower() in {"popen", "run", "system", "exec", "eval"}
    )
    solver_markers = {
        "run_reduced_full_tangent_benchmark": False,
        "compute_low_rank_kernel": False,
        "reconstruct_response_from_kernel": False,
    }
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for name in solver_markers:
        solver_markers[name] = name in defined
    return {
        "passed": all(solver_markers.values()),
        "imports": sorted(imports),
        "forbidden_runtime_call_names_for_loader_context": forbidden_runtime_calls,
        "required_solver_function_markers": solver_markers,
        "note": (
            "The copied solver is parsed only for provenance/scope; no function "
            "or module from it is imported or executed."
        ),
    }


def loader_self_scope_audit(source_path: Path) -> Dict[str, Any]:
    text = source_path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(source_path))
    imports: List[str] = []
    calls: Set[str] = set()
    forbidden_imports: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
                if "environmental_response_solver" in alias.name or "case_loader" in alias.name:
                    forbidden_imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.append(module)
            if "environmental_response_solver" in module or "case_loader" in module:
                forbidden_imports.append(module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
    forbidden_execution_calls = sorted(
        calls.intersection({"Popen", "system", "execv", "execve", "spawnv"})
    )
    return {
        "read_only_CPU_loader_without_Task07_import_or_execution": bool(
            not forbidden_imports
            and not forbidden_execution_calls
            and "cupy" not in {item.lower() for item in imports}
        ),
        "forbidden_imports": sorted(set(forbidden_imports)),
        "forbidden_execution_calls": forbidden_execution_calls,
        "imports": sorted(set(imports)),
    }


# =============================================================================
# CONFIGURATION, MANIFEST, AND AUXILIARY RECORD AUDITS
# =============================================================================
def declared_output_contract(configuration: Mapping[str, Any]) -> Tuple[str, ...]:
    raw = configuration.get("output_contract", ())
    if not isinstance(raw, (list, tuple)):
        return ()
    return tuple(str(item) for item in raw)


def audit_configuration(
    candidate: CandidateRecord,
    spec: MatrixCaseSpec,
    *,
    expected_core_sha256: str,
    synthetic_mode: bool,
) -> Dict[str, Any]:
    configuration = candidate.configuration
    checks: Dict[str, bool] = {}
    warnings: List[str] = []
    metrics: Dict[str, Any] = {}
    try:
        identity = identify_case(configuration)
        checks["physical_identity_matches_frozen_matrix"] = identity.key() == CaseIdentity(
            spec.propagator_type,
            spec.environment_direction,
            spec.omega,
            spec.initial_mode,
            spec.n_shell,
            spec.dt,
            spec.t_final,
            spec.insertion_dt,
        ).key()
    except Exception:
        identity = None
        checks["physical_identity_matches_frozen_matrix"] = False

    checks["stage_exact"] = configuration.get("stage") == TASK07_STAGE_NAME
    checks["case_prefix_matches_configuration_file"] = (
        configuration.get("case_prefix") == candidate.prefix
    )
    checks["case_prefix_is_canonical"] = candidate.prefix == spec.canonical_prefix()
    checks["manual_single_case_policy"] = (
        configuration.get("manual_single_case_policy") is True
    )
    checks["automatic_production_sweep_absent"] = (
        configuration.get("automatic_production_sweep") is False
    )
    checks["zero_environmental_rate_reference"] = (
        configuration.get("zero_environmental_rate_reference") is True
    )
    finite_rate = configuration.get(
        "finite_positive_rate_present",
        configuration.get("finite_positive_rate_used", False),
    )
    checks["finite_positive_rate_absent"] = finite_rate is False
    checks["temperature_parameter_absent"] = (
        configuration.get("temperature_parameter_present") is False
    )
    checks["trajectory_or_Monte_Carlo_absent"] = (
        configuration.get("trajectory_or_Monte_Carlo_present") is False
    )
    checks["explicit_detector_reservoir_absent"] = (
        configuration.get("explicit_detector_reservoir_present") is False
    )
    checks["CAP_or_second_roof_loss_absent"] = (
        configuration.get("CAP_or_second_roof_loss_present") is False
    )
    checks["numerical_core_matches_frozen_v8"] = (
        str(configuration.get("numerical_core_sha256", ""))
        == expected_core_sha256
    )
    checks["script_version_is_v8"] = bool(
        synthetic_mode
        or str(configuration.get("script_version", ""))
        == EXPECTED_TASK07_SCRIPT_VERSION
    )
    checks["production_backend_is_CuPy"] = bool(
        synthetic_mode or str(configuration.get("backend", "")).lower() == "cupy"
    )
    checks["complex128_state_and_matrix_dtypes"] = bool(
        str(configuration.get("state_dtype", "complex128")) == "complex128"
        and str(configuration.get("matrix_dtype", "complex128")) == "complex128"
    )
    checks["float64_reduction_dtype"] = (
        str(configuration.get("reduction_dtype", "float64")) == "float64"
    )
    checks["endpoint_false_grid"] = configuration.get("endpoint", False) is False
    gmres_block = configuration.get("gmres", {})
    checks["frozen_GMRES_atol_restart_maxiter"] = bool(
        isinstance(gmres_block, Mapping)
        and np.isclose(float(gmres_block.get("atol", 0.0)), 0.0, rtol=0.0, atol=0.0)
        and int(gmres_block.get("restart", 30)) == 30
        and int(gmres_block.get("maxiter", 1000)) == 1000
    )

    stored_hash = str(configuration.get("configuration_sha256", ""))
    deterministic = {
        key: value
        for key, value in configuration.items()
        if key not in {"configuration_sha256", "backend_metadata"}
    }
    try:
        reconstructed_hash = sha256_json(deterministic)
    except Exception:
        reconstructed_hash = None
    checks["configuration_hash_reconstructed"] = bool(
        stored_hash and reconstructed_hash == stored_hash
    )
    metrics["stored_configuration_sha256"] = stored_hash
    metrics["reconstructed_configuration_sha256"] = reconstructed_hash

    production_contract = configuration.get("production_contract")
    production_hash = configuration.get("production_contract_sha256")
    if isinstance(production_contract, Mapping) and isinstance(production_hash, str):
        try:
            checks["production_contract_hash_reconstructed"] = (
                sha256_json(production_contract) == production_hash
            )
        except Exception:
            checks["production_contract_hash_reconstructed"] = False
    else:
        checks["production_contract_hash_reconstructed"] = False

    contract = declared_output_contract(configuration)
    required = required_solver_suffixes(configuration)
    checks["output_contract_has_no_duplicates"] = len(contract) == len(set(contract))
    checks["output_contract_contains_required_products"] = all(
        suffix in contract for suffix in required
    )

    try:
        expected_steps, expected_times = expected_insertion_grid(configuration)
        complete_grid = configuration.get("complete_insertion_grid", {})
        checks["complete_insertion_grid_metadata"] = bool(
            isinstance(complete_grid, Mapping)
            and int(complete_grid.get("node_count", -1)) == expected_steps.size
            and int(complete_grid.get("panel_count", -1)) == expected_steps.size - 1
            and np.isclose(
                float(complete_grid.get("first_time", math.nan)),
                expected_times[0],
                rtol=0.0,
                atol=2.0e-12,
            )
            and np.isclose(
                float(complete_grid.get("last_time", math.nan)),
                expected_times[-1],
                rtol=0.0,
                atol=2.0e-12,
            )
        )
        checks["expected_101_node_grid"] = bool(
            expected_steps.size == 101 and expected_times.size == 101
        )
    except Exception as exc:
        checks["complete_insertion_grid_metadata"] = False
        checks["expected_101_node_grid"] = False
        warnings.append(f"cannot reconstruct insertion grid: {exc}")

    checks["frozen_T_final"] = np.isclose(
        float(configuration.get("T_final", math.nan)),
        EXPECTED_T_FINAL,
        rtol=0.0,
        atol=1.0e-12,
    )
    checks["frozen_Nz"] = int(configuration.get("N_z", configuration.get("n_z", -1))) == EXPECTED_N_Z
    checks["frozen_Lz"] = np.isclose(
        float(configuration.get("L_z", configuration.get("l_z", math.nan))),
        EXPECTED_L_Z,
        rtol=0.0,
        atol=1.0e-12,
    )

    branch_rtol = finite_float(
        nested_get(
            configuration,
            "gmres.branch_rtol",
            "branch_gmres_rtol",
            default=configuration.get("response_reference_gmres_rtol"),
        )
    )
    response_rtol = finite_float(
        configuration.get(
            "response_reference_gmres_rtol",
            nested_get(configuration, "gmres.response_reference_rtol"),
        )
    )
    checks["response_reference_rtol_1e-10"] = bool(
        response_rtol is not None
        and np.isclose(response_rtol, EXPECTED_RESPONSE_RTOL, rtol=0.0, atol=1e-18)
    )
    checks["branch_rtol_1e-10"] = bool(
        branch_rtol is not None
        and np.isclose(branch_rtol, EXPECTED_BRANCH_RTOL, rtol=0.0, atol=1e-18)
    )
    checks["response_and_branch_rtol_matched"] = bool(
        branch_rtol is not None
        and response_rtol is not None
        and np.isclose(branch_rtol, response_rtol, rtol=0.0, atol=1e-18)
    )
    metrics["branch_gmres_rtol"] = branch_rtol
    metrics["response_reference_gmres_rtol"] = response_rtol

    copied_source = str(configuration.get("copied_source_file", ""))
    source_present = bool(copied_source and candidate.package.exists(copied_source))
    checks["copied_solver_source_present"] = source_present
    source_hash = candidate.package.sha256(copied_source) if source_present else None
    checks["copied_solver_source_hash_matches_configuration"] = bool(
        source_hash
        and source_hash == configuration.get("copied_source_sha256")
        and source_hash == configuration.get("source_sha256")
    )
    metrics["copied_solver_source_sha256"] = source_hash
    source_scope: Dict[str, Any] = {}
    if source_present:
        try:
            source_scope = source_scope_ast_audit(
                candidate.package.read_bytes(copied_source).decode("utf-8")
            )
        except Exception as exc:
            source_scope = {"passed": False, "error": str(exc)}
    checks["copied_solver_source_scope_parse"] = source_scope.get("passed") is True

    # Folder numbering is storage metadata only. A mismatch is visible but is
    # never promoted to a physical-identity failure.
    fixed_dir = configuration.get("fixed_stage_directory")
    if fixed_dir and str(fixed_dir) != candidate.package.base_label:
        warnings.append(
            "saved fixed_stage_directory differs from package container; ignored "
            "for physical identity under the Task-08 handoff"
        )

    return {
        "checks": checks,
        "warnings": warnings,
        "metrics": metrics,
        "identity": asdict(identity) if identity is not None else None,
        "declared_output_contract": list(contract),
        "required_solver_suffixes": list(required),
        "copied_solver_scope_audit": source_scope,
    }


def audit_manifest_and_files(
    candidate: CandidateRecord,
) -> Dict[str, Any]:
    package = candidate.package
    prefix = candidate.prefix
    configuration = candidate.configuration
    required_suffixes = required_solver_suffixes(configuration)
    required_names = [f"{prefix}_{suffix}" for suffix in required_suffixes]
    missing = [name for name in required_names if not package.exists(name)]
    manifest_name = f"{prefix}_output_hashes.json"
    manifest: Dict[str, Any] = {}
    if package.exists(manifest_name):
        try:
            manifest = package.read_json(manifest_name)
        except Exception:
            manifest = {}
    files = manifest.get("files", {})
    rows: List[Dict[str, Any]] = []
    all_match = isinstance(files, Mapping) and bool(files)
    safe_paths = True
    if isinstance(files, Mapping):
        for filename, expected in sorted(files.items()):
            safe = isinstance(filename, str) and Path(filename).name == filename
            safe_paths = safe_paths and safe
            actual = package.sha256(filename) if safe and package.exists(filename) else None
            match = actual == expected
            all_match = all_match and match
            rows.append(
                {
                    "filename": filename,
                    "safe_basename": safe,
                    "expected_sha256": expected,
                    "actual_sha256": actual,
                    "match": match,
                }
            )
    stable_required = [
        f"{prefix}_{suffix}"
        for suffix in required_suffixes
        if suffix not in NONDETERMINISTIC_SOLVER_SUFFIXES
    ]
    missing_from_manifest = [
        name
        for name in stable_required
        if not isinstance(files, Mapping) or name not in files
    ]
    runtime_name = f"{prefix}_{CURRENT_RUNTIME_SOLVER_SUFFIX}"
    status_name = f"{prefix}_run_status.json"
    status_record: Dict[str, Any] = {}
    if package.exists(status_name):
        try:
            status_record = package.read_json(status_name)
        except Exception:
            status_record = {}
    actual_manifest_sha256 = (
        package.sha256(manifest_name) if package.exists(manifest_name) else None
    )
    status_declared_manifest_name = status_record.get("output_hash_manifest")
    status_declared_manifest_sha256 = status_record.get(
        "output_hash_manifest_sha256"
    )
    checks = {
        "all_required_solver_files_present": not missing,
        "output_manifest_present_and_nonempty": bool(files),
        "manifest_paths_are_safe_basenames": safe_paths,
        "all_manifest_hashes_match": all_match,
        "all_required_stable_products_listed": not missing_from_manifest,
        "runtime_excluded_from_stable_manifest": bool(
            not isinstance(files, Mapping) or runtime_name not in files
        ),
        "manifest_case_prefix_matches": manifest.get("case_prefix") == prefix,
        "manifest_configuration_hash_matches": manifest.get("configuration_sha256")
        == configuration.get("configuration_sha256"),
        "manifest_source_hash_matches": manifest.get("source_sha256")
        == configuration.get("source_sha256"),
        "run_status_output_manifest_name_matches": bool(
            status_record
            and status_declared_manifest_name == manifest_name
        ),
        "run_status_output_manifest_sha256_matches": bool(
            status_record
            and isinstance(status_declared_manifest_sha256, str)
            and actual_manifest_sha256 == status_declared_manifest_sha256
        ),
        "ZIP_has_no_unsafe_or_duplicate_members": bool(
            package.kind != "zip"
            or (
                not getattr(package, "unsafe_members", [])
                and not getattr(package, "duplicate_members", [])
            )
        ),
    }
    return {
        "checks": checks,
        "missing_required_files": missing,
        "missing_stable_files_from_manifest": missing_from_manifest,
        "file_hash_rows": rows,
        "manifest": manifest,
        "manifest_sha256": actual_manifest_sha256,
        "run_status_manifest_reference": {
            "output_hash_manifest": status_declared_manifest_name,
            "output_hash_manifest_sha256": status_declared_manifest_sha256,
        },
    }


def _reference_record_checks(record: Mapping[str, Any]) -> Dict[str, bool]:
    residual = finite_float(record.get("maximum_true_relative_residual"))
    minimum_probability = finite_float(record.get("minimum_midpoint_probability"))
    closure = finite_float(record.get("roof_probability_closure_residual"))
    closure_tolerance = finite_float(record.get("closure_tolerance_used"))
    return {
        "gmres_info_zero": int(record.get("maximum_gmres_info_abs", -1)) == 0,
        "true_residual_within_tolerance": bool(
            residual is not None and residual <= TRUE_RESIDUAL_TOL
        ),
        "midpoint_probability_nonnegative": bool(
            minimum_probability is not None and minimum_probability >= -OPERATOR_TOL
        ),
        "roof_probability_closure": bool(
            closure is not None
            and closure_tolerance is not None
            and abs(closure) <= closure_tolerance
        ),
        "arrays_reported_finite": record.get("all_arrays_finite") is True,
        "local_record_passed": record.get("local_numerical_passed") is True,
    }


def audit_saved_json_records(candidate: CandidateRecord) -> Dict[str, Any]:
    package = candidate.package
    prefix = candidate.prefix
    configuration = candidate.configuration
    names = {
        key: f"{prefix}_{suffix}"
        for key, suffix in {
            "reference": "reference_audit.json",
            "operator": "operator_audit.json",
            "pilot": "closure_pilot_audit.json",
            "response": "response_audit.json",
            "status": "run_status.json",
            "runtime": "runtime_metrics.json",
        }.items()
    }
    records: Dict[str, Dict[str, Any]] = {}
    for key, name in names.items():
        if package.exists(name):
            try:
                records[key] = package.read_json(name)
            except Exception as exc:
                records[key] = {"_read_error": str(exc)}
        else:
            records[key] = {}

    reference = records["reference"]
    response = records["response"]
    pilot = records["pilot"]
    status = records["status"]
    operator = records["operator"]
    architecture = str(reference.get("architecture", ""))
    task05_ref = reference.get(
        "Task05_regression_reference", reference.get("zero_rate_reference", {})
    )
    response_ref = reference.get("response_reference", {})
    if not isinstance(task05_ref, Mapping):
        task05_ref = {}
    if not isinstance(response_ref, Mapping):
        response_ref = {}

    checks: Dict[str, bool] = {}
    reference_checks = _reference_record_checks(task05_ref)
    response_reference_checks = _reference_record_checks(response_ref)
    checks.update(
        {f"Task05_reference.{name}": value for name, value in reference_checks.items()}
    )
    checks.update(
        {
            f"response_reference.{name}": value
            for name, value in response_reference_checks.items()
        }
    )
    checks["dual_reference_architecture"] = architecture == "dual_zero_rate_reference"
    checks["reference_audit_saved_pass_consistent"] = reference.get("passed") is True

    recovery = reference.get("Task05_recovery", {})
    if not isinstance(recovery, Mapping):
        recovery = {}
    # Final Task-07 v8 writes the comparison values under
    # ``comparison_metrics``.  ``metrics`` is retained only as a legacy/schema-
    # test fallback.  The real v8 key must take precedence.
    recovery_metrics = recovery.get(
        "comparison_metrics", recovery.get("metrics", {})
    )
    if not isinstance(recovery_metrics, Mapping):
        recovery_metrics = {}
    tolerance_record = recovery.get("tolerances", {})
    if not isinstance(tolerance_record, Mapping):
        tolerance_record = {}
    array_tol = finite_float(
        tolerance_record.get("reference_array_abs", TASK05_REFERENCE_ARRAY_ABS_TOL)
    )
    source_tol = finite_float(
        tolerance_record.get("reference_source_abs", TASK05_SOURCE_CURVE_ABS_TOL)
    )
    checks["Task05_recovery_shape_match"] = recovery.get("shape_match") is True
    for metric in ("survival_max_abs", "step_probability_max_abs"):
        value = finite_float(recovery_metrics.get(metric))
        checks[f"Task05_recovery_{metric}"] = bool(
            value is not None and array_tol is not None and value <= array_tol
        )
    for metric in ("s_down_max_abs", "s_up_max_abs", "s_phi_max_abs"):
        value = finite_float(recovery_metrics.get(metric))
        checks[f"Task05_recovery_{metric}"] = bool(
            value is not None and source_tol is not None and value <= source_tol
        )

    # The Task-07 case does not store the full Task-05 replay arrays, so Task 08
    # cannot recreate this comparison from the case ZIP alone without executing
    # the detector solver (which is prohibited).  It can, however, verify that
    # the saved recovery record is internally coherent and tied to the exact
    # hashed Task-05 provenance selected by Task 07.
    checks["Task05_recovery_saved_pass"] = recovery.get("passed") is True
    checks["Task05_recovery_required"] = recovery.get("required") is True
    expected_task05_prefix = str(configuration.get("task05_reference_prefix", ""))
    checks["Task05_recovery_prefix_matches_configuration"] = bool(
        expected_task05_prefix
        and recovery.get("task05_case_prefix") == expected_task05_prefix
    )
    recovery_manifest = recovery.get("task05_output_manifest", {})
    if not isinstance(recovery_manifest, Mapping):
        recovery_manifest = {}
    recovery_manifest_files = recovery_manifest.get("files", {})
    manifest_records_pass = bool(
        isinstance(recovery_manifest_files, Mapping)
        and recovery_manifest_files
        and all(
            isinstance(record, Mapping)
            and record.get("match") is True
            and record.get("expected") == record.get("actual")
            for record in recovery_manifest_files.values()
        )
    )
    checks["Task05_recovery_embedded_manifest_pass"] = bool(
        recovery_manifest.get("all_hashes_match") is True
        and manifest_records_pass
    )
    selected_mode = str(configuration.get("initial_mode", ""))
    preflight_records = configuration.get("task05_preflight_references", {})
    if not isinstance(preflight_records, Mapping):
        preflight_records = {}
    preflight_selected = preflight_records.get(selected_mode, {})
    if not isinstance(preflight_selected, Mapping):
        preflight_selected = {}
    checks["Task05_recovery_manifest_sha_matches_configuration"] = bool(
        recovery_manifest.get("manifest_sha256")
        and recovery_manifest.get("manifest_sha256")
        == preflight_selected.get("output_manifest_sha256")
    )
    recovery_gmres = recovery.get("task05_gmres_family", {})
    if not isinstance(recovery_gmres, Mapping):
        recovery_gmres = {}
    preflight_gmres = preflight_selected.get("gmres_family", {})
    if not isinstance(preflight_gmres, Mapping):
        preflight_gmres = {}
    checks["Task05_recovery_GMRES_family_coherent"] = bool(
        recovery_gmres.get("passed") is True
        and preflight_gmres.get("passed") is True
        and finite_float(recovery_gmres.get("rtol")) is not None
        and np.isclose(
            float(recovery_gmres.get("rtol")),
            float(preflight_gmres.get("rtol")),
            rtol=0.0,
            atol=1.0e-18,
        )
    )
    task05_recovery_evidence = {
        "comparison_mode": "SAVED_HASHED_TASK07_RECOVERY_RECORD",
        "exact_replay_arrays_present_in_Task07_case": False,
        "comparison_independently_recomputed_from_raw_Task05_and_Task07_replay_arrays": False,
        "embedded_Task05_manifest_verified": checks["Task05_recovery_embedded_manifest_pass"],
        "note": (
            "Task 08 independently verifies the Task-07 response arrays and the "
            "hashed Task-05 provenance record. Exact replay-array comparison remains "
            "inherited because Task-07 case packages do not contain the full replay arrays."
        ),
    }

    consistency = reference.get("cross_reference_consistency", {})
    if not isinstance(consistency, Mapping):
        consistency = {}
    checks["dual_reference_consistency_saved_pass"] = consistency.get("passed") is True
    consistency_tolerances = consistency.get("tolerances", {})
    max_abs = consistency.get("maximum_absolute_differences", {})
    if not isinstance(consistency_tolerances, Mapping):
        consistency_tolerances = {}
    if not isinstance(max_abs, Mapping):
        max_abs = {}
    consistency_pairs = (
        (
            "complete_law_total_variation",
            consistency.get("complete_censored_law_total_variation_distance"),
        ),
        ("survival_Linf", max_abs.get("survival")),
        (
            "source_diagnostic_Linf",
            consistency.get("maximum_source_diagnostic_difference"),
        ),
        (
            "phase_aligned_selected_state_relative",
            consistency.get("maximum_phase_aligned_selected_state_relative_difference"),
        ),
        (
            "phase_aligned_q_roof_relative",
            consistency.get("maximum_phase_aligned_q_roof_relative_difference"),
        ),
    )
    for tolerance_name, metric_value in consistency_pairs:
        value = finite_float(metric_value)
        tolerance = finite_float(consistency_tolerances.get(tolerance_name))
        checks[f"dual_reference_{tolerance_name}"] = bool(
            value is not None and tolerance is not None and value <= tolerance
        )

    # Recheck saved closure pilot numerically rather than accepting its PASS flag.
    pilot_tolerances = pilot.get("tolerances", {})
    if not isinstance(pilot_tolerances, Mapping):
        pilot_tolerances = {}
    pilot_max_closure = finite_float(pilot.get("maximum_closure_residual"))
    pilot_max_residual = finite_float(pilot.get("maximum_branch_true_relative_residual"))
    pilot_source_trace = finite_float(pilot.get("maximum_source_trace_residual"))
    pilot_applicable = configuration.get("propagator_type") == "spinor"
    checks["closure_pilot_record_present_or_not_applicable"] = bool(
        pilot or not pilot_applicable
    )
    checks["closure_pilot_closure"] = bool(
        not pilot_applicable
        or (
            pilot_max_closure is not None
            and pilot_max_closure
            <= finite_float(
                pilot_tolerances.get("closure_absolute", CLOSURE_PILOT_ABS_TOL)
            )
        )
    )
    checks["closure_pilot_branch_residual"] = bool(
        not pilot_applicable
        or (pilot_max_residual is not None and pilot_max_residual <= TRUE_RESIDUAL_TOL)
    )
    checks["closure_pilot_source_trace"] = bool(
        not pilot_applicable
        or (pilot_source_trace is not None and pilot_source_trace <= SOURCE_TRACE_ABS_TOL)
    )
    checks["closure_pilot_rtol_matched"] = bool(
        not pilot_applicable or pilot.get("reference_and_branch_rtol_matched") is True
    )

    flat_response_checks: Dict[str, bool] = {}
    flatten_boolean_checks("response", response.get("checks", {}), flat_response_checks)
    checks["saved_response_has_no_failed_boolean_check"] = bool(
        flat_response_checks and all(flat_response_checks.values())
    )
    checks["saved_response_local_checks_passed"] = (
        response.get("all_case_local_checks_passed") is True
    )
    checks["solver_did_not_authorize_physical_claim"] = (
        response.get("production_physical_claim_authorized") is False
        and status.get("Task08_physical_claim_authorized") is False
    )
    checks["solver_status_completed"] = str(status.get("status", "")).startswith(
        "completed_"
    )
    checks["status_configuration_hash_matches"] = (
        status.get("configuration_sha256") == configuration.get("configuration_sha256")
    )

    # Operator JSON is only a cross-check. The load-bearing operator algebra is
    # reconstructed independently by reconstruct_operator_contract().
    checks["saved_operator_audit_present"] = bool(operator)
    checks["saved_operator_audit_passed"] = operator.get("all_checks_passed") is True

    declared_tolerances = response.get("tolerances", {})
    if not isinstance(declared_tolerances, Mapping):
        declared_tolerances = {}
    expected_tolerances = {
        "source_trace_abs": SOURCE_TRACE_ABS_TOL,
        "ground_state_launch_source_abs": LAUNCH_SOURCE_ABS_TOL,
        "tangent_closure_abs": TANGENT_CLOSURE_ABS_TOL,
        "tangent_closure_rel": TANGENT_CLOSURE_REL_TOL,
        "per_insertion_kernel_closure_abs": KERNEL_CLOSURE_ABS_TOL,
        "scalar_kernel_abs": SCALAR_KERNEL_ABS_TOL,
        "scalar_response_abs": SCALAR_RESPONSE_ABS_TOL,
        "insertion_convergence_abs": INSERTION_CONVERGENCE_ABS_TOL,
        "insertion_convergence_rel": INSERTION_CONVERGENCE_REL_TOL,
        "external_time_and_shell_response_abs": FAMILY_RESPONSE_ABS_TOL,
        "external_time_and_shell_response_rel": FAMILY_RESPONSE_REL_TOL,
        "evidence_factor": EVIDENCE_FACTOR,
    }
    tolerance_checks: Dict[str, bool] = {}
    for name, expected in expected_tolerances.items():
        value = finite_float(declared_tolerances.get(name))
        # Synthetic records may omit the tolerance table; production v8 may not.
        tolerance_checks[name] = bool(
            (not declared_tolerances and candidate.configuration.get("smoke_test") is True)
            or (
                value is not None
                and np.isclose(value, expected, rtol=0.0, atol=max(1.0e-18, abs(expected) * 1.0e-14))
            )
        )
    checks.update(
        {f"declared_tolerance.{name}": passed for name, passed in tolerance_checks.items()}
    )

    rerun = status.get("deterministic_same_prefix_rerun", {})
    if not isinstance(rerun, Mapping):
        rerun = {}
    return {
        "checks": checks,
        "records": records,
        "reference_architecture": architecture,
        "Task05_recovery_evidence": task05_recovery_evidence,
        "rerun": dict(rerun),
        "solver_side_external_controls": status.get(
            "solver_side_external_controls", {}
        ),
        "failed_saved_response_checks": sorted(
            name for name, passed in flat_response_checks.items() if not passed
        ),
    }


def audit_per_case_loader(candidate: CandidateRecord, *, synthetic_mode: bool) -> Dict[str, Any]:
    package = candidate.package
    prefix = candidate.prefix
    audit_name = f"{prefix}_case_loader_audit.json"
    status_name = f"{prefix}_case_loader_run_status.json"
    manifest_name = f"{prefix}_case_loader_output_hashes.json"
    source_name = f"{prefix}_07_environmental_response_case_loader.py"
    present = package.exists(audit_name)
    checks: Dict[str, bool] = {"per_case_loader_audit_present": present}
    metrics: Dict[str, Any] = {}
    if not present:
        return {
            "present": False,
            "checks": checks,
            "metrics": metrics,
            "audit": {},
            "status": {},
        }
    try:
        audit = package.read_json(audit_name)
    except Exception as exc:
        return {
            "present": True,
            "checks": {**checks, "per_case_loader_audit_readable": False},
            "metrics": {"read_error": str(exc)},
            "audit": {},
            "status": {},
        }
    status = package.read_json(status_name) if package.exists(status_name) else {}
    manifest = package.read_json(manifest_name) if package.exists(manifest_name) else {}
    checks["per_case_loader_audit_readable"] = True
    failed = audit.get("failed_checks", [])
    checks["per_case_loader_has_no_failed_checks"] = isinstance(failed, list) and not failed
    checks["per_case_loader_all_checks_passed"] = (
        audit.get("all_independent_checks_passed") is True
        or status.get("all_independent_checks_passed") is True
    )
    checks["per_case_loader_status_consistent"] = bool(
        status
        and status.get("failed_check_count", len(failed)) == len(failed)
        and status.get("verdict") == audit.get("verdict")
    )
    checks["per_case_loader_source_present"] = package.exists(source_name)
    source_hash = package.sha256(source_name) if package.exists(source_name) else None
    checks["per_case_loader_source_hash_frozen"] = bool(
        synthetic_mode or source_hash == FROZEN_TASK07_CASE_LOADER_SHA256
    )
    checks["per_case_loader_audit_prefix_matches"] = bool(
        audit.get("case_prefix", prefix) == prefix
    )
    checks["per_case_loader_manifest_prefix_matches"] = bool(
        manifest.get("case_prefix") == prefix
    )
    checks["per_case_loader_manifest_verdict_matches"] = bool(
        manifest.get("verdict") == audit.get("verdict")
    )
    checks["per_case_loader_manifest_source_hash_matches"] = bool(
        source_hash
        and manifest.get("loader_source_sha256") == source_hash
        and manifest.get("copied_loader_source_sha256") == source_hash
    )
    checks["per_case_loader_status_source_hash_matches"] = bool(
        source_hash
        and status.get("loader_source_sha256") == source_hash
        and status.get("copied_loader_source_sha256") == source_hash
        and status.get("loader_source_copy_hash_matches") is True
    )
    actual_loader_manifest_sha256 = (
        package.sha256(manifest_name) if package.exists(manifest_name) else None
    )
    checks["per_case_loader_status_manifest_reference_matches"] = bool(
        status.get("loader_output_hash_manifest") == manifest_name
        and status.get("loader_output_hash_manifest_sha256")
        == actual_loader_manifest_sha256
    )
    files = manifest.get("files", {})
    all_hashes = isinstance(files, Mapping) and bool(files)
    if isinstance(files, Mapping):
        for filename, expected in files.items():
            all_hashes = all_hashes and bool(
                isinstance(filename, str)
                and Path(filename).name == filename
                and package.exists(filename)
                and package.sha256(filename) == expected
            )
    checks["per_case_loader_manifest_hashes_match"] = all_hashes
    metrics.update(
        {
            "loader_source_sha256": source_hash,
            "loader_verdict": audit.get("verdict", status.get("verdict")),
            "loader_exit_code": audit.get("exit_code", status.get("exit_code")),
            "loader_failed_checks": failed,
            "loader_pending_items": audit.get("pending_items", status.get("pending_items", [])),
            "loader_manifest_sha256": actual_loader_manifest_sha256,
        }
    )
    return {
        "present": True,
        "checks": checks,
        "metrics": metrics,
        "audit": audit,
        "status": status,
    }


# =============================================================================
# RAW RESPONSE/KERNEL RECONSTRUCTION
# =============================================================================
def audit_raw_response_products(candidate: CandidateRecord) -> Dict[str, Any]:
    package = candidate.package
    prefix = candidate.prefix
    configuration = candidate.configuration
    names = {
        "times": f"{prefix}_times.npy",
        "insertion_times": f"{prefix}_insertion_times.npy",
        "chi_survival": f"{prefix}_chi_survival.npy",
        "chi_click_density": f"{prefix}_chi_click_density.npy",
        "kernel": f"{prefix}_kernel_summary.npz",
        "source": f"{prefix}_source_insertion_summary.npz",
        "benchmark": f"{prefix}_full_tangent_benchmark.npz",
        "integrated": f"{prefix}_integrated_response.json",
        "response_audit": f"{prefix}_response_audit.json",
    }
    try:
        times = np.asarray(package.load_npy(names["times"]))
        insertion_times = np.asarray(package.load_npy(names["insertion_times"]))
        chi_survival = np.asarray(package.load_npy(names["chi_survival"]))
        chi_click_density = np.asarray(package.load_npy(names["chi_click_density"]))
        kernel = package.load_npz(names["kernel"])
        source = package.load_npz(names["source"])
        benchmark = package.load_npz(names["benchmark"])
        integrated_stored = package.read_json(names["integrated"])
        response_audit = package.read_json(names["response_audit"])
    except Exception as exc:
        return {
            "checks": {"raw_products_readable": False},
            "failed_checks": ["raw_products_readable"],
            "metrics": {"read_error": str(exc)},
            "arrays": {},
            "raw_invalid": True,
        }

    checks: Dict[str, bool] = {"raw_products_readable": True}
    metrics: Dict[str, Any] = {}
    arrays: Dict[str, np.ndarray] = {}

    kernel_missing = sorted(KERNEL_REQUIRED_KEYS - set(kernel))
    source_missing = sorted(SOURCE_REQUIRED_KEYS - set(source))
    benchmark_missing = sorted(BENCHMARK_REQUIRED_KEYS - set(benchmark))
    checks["kernel_schema_complete"] = not kernel_missing
    checks["source_schema_complete"] = not source_missing
    checks["benchmark_schema_complete"] = not benchmark_missing
    metrics["kernel_missing_keys"] = kernel_missing
    metrics["source_missing_keys"] = source_missing
    metrics["benchmark_missing_keys"] = benchmark_missing
    if kernel_missing or source_missing or benchmark_missing:
        failed = sorted(name for name, passed in checks.items() if not passed)
        return {
            "checks": checks,
            "failed_checks": failed,
            "metrics": metrics,
            "arrays": {},
            "raw_invalid": True,
        }

    # Numeric raw arrays. Interpretation/labels remain unmodified metadata.
    try:
        insertion_steps = np.asarray(kernel["insertion_steps"])
        kernel_insertion_times = np.asarray(kernel["insertion_times"])
        panel_durations = np.asarray(kernel["panel_durations"])
        jump = np.asarray(kernel["kernel_jump_probability"])
        anti = np.asarray(kernel["kernel_anticommutator_probability"])
        total = np.asarray(kernel["kernel_total_probability"])
        density_jump = np.asarray(kernel["kernel_click_density_jump"])
        density_anti = np.asarray(kernel["kernel_click_density_anticommutator"])
        density_total = np.asarray(kernel["kernel_click_density_total"])
        kernel_survival = np.asarray(kernel["kernel_survival"])
        chi_panel_probability = np.asarray(kernel["chi_panel_probability"])

        source_steps = np.asarray(source["insertion_steps"])
        source_times = np.asarray(source["insertion_times"])
        source_jump = np.asarray(source["jump_norm2"])
        source_anti = np.asarray(source["anti_expectation"])
        source_trace_terms = np.asarray(source["trace_terms"])
        source_trace_total = np.asarray(source["trace_total"])
        source_activity = np.asarray(source["activity_total"])
        reference_survival = np.asarray(source["reference_survival"])
        reference_s_down = np.asarray(source["reference_s_down"])
        reference_s_up = np.asarray(source["reference_s_up"])
        reference_s_phi = np.asarray(source["reference_s_phi"])
        reference_top = np.asarray(source["reference_top_shell"])
        branch_labels = np.asarray(source["branch_labels"])
        kernel_interpretation = numpy_metadata_text(kernel["interpretation"])
        source_interpretation = numpy_metadata_text(source["interpretation"])
        branch_label_list = [
            str(value) for value in branch_labels.reshape(-1).tolist()
        ]

        b_times = np.asarray(benchmark["times"])
        b_full_s = np.asarray(benchmark["full_chi_survival"])
        b_full_p = np.asarray(benchmark["full_chi_panel_probability"])
        b_low_s = np.asarray(benchmark["low_rank_chi_survival"])
        b_low_p = np.asarray(benchmark["low_rank_chi_panel_probability"])
        b_kernel_p = np.asarray(benchmark["low_rank_kernel_probability"])
        b_kernel_s = np.asarray(benchmark["low_rank_kernel_survival"])
    except Exception as exc:
        checks["raw_array_extraction"] = False
        metrics["array_extraction_error"] = str(exc)
        return {
            "checks": checks,
            "failed_checks": [name for name, passed in checks.items() if not passed],
            "metrics": metrics,
            "arrays": {},
            "raw_invalid": True,
        }
    checks["raw_array_extraction"] = True

    nodes = int(insertion_times.size)
    panels = nodes - 1
    try:
        expected_steps, expected_times = expected_insertion_grid(configuration)
    except Exception:
        expected_steps = np.empty(0, dtype=np.int64)
        expected_times = np.empty(0, dtype=np.float64)

    required_numeric = [
        times,
        insertion_times,
        chi_survival,
        chi_click_density,
        insertion_steps,
        kernel_insertion_times,
        panel_durations,
        jump,
        anti,
        total,
        density_jump,
        density_anti,
        density_total,
        kernel_survival,
        chi_panel_probability,
        source_steps,
        source_times,
        source_jump,
        source_anti,
        source_trace_terms,
        source_trace_total,
        source_activity,
        reference_survival,
        reference_s_down,
        reference_s_up,
        reference_s_phi,
        reference_top,
        b_times,
        b_full_s,
        b_full_p,
        b_low_s,
        b_low_p,
        b_kernel_p,
        b_kernel_s,
    ]
    checks["all_required_raw_numeric_arrays_finite"] = all_finite(*required_numeric)
    if not checks["all_required_raw_numeric_arrays_finite"]:
        metrics["nonfinite_raw_arrays"] = [
            label
            for label, array in zip(
                (
                    "times",
                    "insertion_times",
                    "chi_survival",
                    "chi_click_density",
                    "insertion_steps",
                    "kernel_insertion_times",
                    "panel_durations",
                    "kernel_jump_probability",
                    "kernel_anticommutator_probability",
                    "kernel_total_probability",
                    "kernel_click_density_jump",
                    "kernel_click_density_anticommutator",
                    "kernel_click_density_total",
                    "kernel_survival",
                    "chi_panel_probability",
                    "source_steps",
                    "source_times",
                    "source_jump",
                    "source_anti",
                    "source_trace_terms",
                    "source_trace_total",
                    "source_activity",
                    "reference_survival",
                    "reference_s_down",
                    "reference_s_up",
                    "reference_s_phi",
                    "reference_top_shell",
                    "benchmark_times",
                    "benchmark_full_chi_survival",
                    "benchmark_full_chi_panel_probability",
                    "benchmark_low_rank_chi_survival",
                    "benchmark_low_rank_chi_panel_probability",
                    "benchmark_kernel_probability",
                    "benchmark_kernel_survival",
                ),
                required_numeric,
            )
            if not np.all(np.isfinite(np.asarray(array)))
        ]

    checks["main_array_shapes_and_dtypes"] = bool(
        nodes == 101
        and panels == 100
        and times.shape == (nodes,)
        and insertion_times.shape == (nodes,)
        and chi_survival.shape == (nodes,)
        and chi_click_density.shape == (panels,)
        and times.dtype == np.dtype(np.float64)
        and insertion_times.dtype == np.dtype(np.float64)
        and chi_survival.dtype == np.dtype(np.float64)
        and chi_click_density.dtype == np.dtype(np.float64)
        and insertion_steps.shape == (nodes,)
        and insertion_steps.dtype == np.dtype(np.int64)
        and kernel_insertion_times.shape == (nodes,)
        and panel_durations.shape == (panels,)
        and panel_durations.dtype == np.dtype(np.float64)
        and chi_panel_probability.shape == (panels,)
        and chi_panel_probability.dtype == np.dtype(np.float64)
        and all(
            array.shape == (panels, nodes)
            and array.dtype == np.dtype(np.float64)
            for array in (
                jump,
                anti,
                total,
                density_jump,
                density_anti,
                density_total,
            )
        )
        and kernel_survival.shape == (nodes, nodes)
        and kernel_survival.dtype == np.dtype(np.float64)
    )
    checks["source_array_shapes"] = bool(
        source_steps.shape == (nodes,)
        and source_times.shape == (nodes,)
        and source_jump.shape == (nodes, 2)
        and source_anti.shape == (nodes, 2)
        and source_trace_terms.shape == (nodes, 2)
        and source_trace_total.shape == (nodes,)
        and source_activity.shape == (nodes,)
        and reference_survival.shape == (nodes,)
        and reference_s_down.shape == (nodes,)
        and reference_s_up.shape == (nodes,)
        and reference_s_phi.shape == (nodes,)
        and reference_top.shape == (nodes,)
        and branch_labels.shape == (4,)
    )
    kernel_interpretation_lower = kernel_interpretation.lower()
    source_interpretation_lower = source_interpretation.lower()
    checks["kernel_declared_orientation_consistent"] = all(
        fragment in kernel_interpretation_lower
        for fragment in (
            "rows are output panels",
            "columns are environmental insertion state nodes",
            "total equals jump plus anticommutator",
        )
    )
    checks["source_interpretation_declares_trace_preservation"] = bool(
        "trace_total" in source_interpretation_lower
        and "trace preserving" in source_interpretation_lower
    )
    checks["branch_label_order_matches_v8_contract"] = branch_label_list == [
        "jump_x",
        "anti_x",
        "jump_y",
        "anti_y",
    ]

    checks["times_equal_insertion_times"] = bool(
        times.shape == insertion_times.shape
        and max_abs_difference(times, insertion_times) <= 2.0e-12
    )
    checks["kernel_and_source_grids_equal_main_grid"] = bool(
        max_abs_difference(kernel_insertion_times, insertion_times) <= 2.0e-12
        and max_abs_difference(source_times, insertion_times) <= 2.0e-12
        and max_abs_difference(source_steps, insertion_steps) == 0.0
    )
    checks["grid_matches_configuration"] = bool(
        insertion_steps.shape == expected_steps.shape
        and max_abs_difference(insertion_steps, expected_steps) == 0.0
        and max_abs_difference(insertion_times, expected_times) <= 2.0e-12
    )
    checks["positive_panel_durations"] = bool(
        panel_durations.shape == (panels,)
        and np.all(panel_durations > 0.0)
        and max_abs_difference(panel_durations, np.diff(insertion_times)) <= 2.0e-12
    )

    decomposition_residual = max_abs_difference(total, jump + anti)
    density_residual = max(
        max_abs_difference(density_jump, jump / panel_durations[:, None]),
        max_abs_difference(density_anti, anti / panel_durations[:, None]),
        max_abs_difference(density_total, total / panel_durations[:, None]),
    )
    checks["kernel_jump_plus_anticommutator_decomposition"] = (
        decomposition_residual <= ARRAY_ABS_TOL
    )
    checks["kernel_click_density_reconstruction"] = density_residual <= ARRAY_ABS_TOL

    try:
        recomputed_s, recomputed_p, recomputed_g = reconstruct_response_from_kernel(
            insertion_times.astype(np.float64),
            total.astype(np.float64),
            kernel_survival.astype(np.float64),
        )
        response_reconstruction_residual = max(
            max_abs_difference(chi_survival, recomputed_s),
            max_abs_difference(chi_panel_probability, recomputed_p),
            max_abs_difference(chi_click_density, recomputed_g),
        )
        checks["response_reconstructed_from_kernel"] = (
            response_reconstruction_residual <= ARRAY_ABS_TOL
        )
    except Exception as exc:
        recomputed_s = np.full_like(chi_survival, np.nan, dtype=np.float64)
        recomputed_p = np.full_like(chi_panel_probability, np.nan, dtype=np.float64)
        recomputed_g = np.full_like(chi_click_density, np.nan, dtype=np.float64)
        response_reconstruction_residual = math.inf
        checks["response_reconstructed_from_kernel"] = False
        metrics["response_reconstruction_error"] = str(exc)

    probability_noncausal = np.triu(
        np.ones((panels, nodes), dtype=bool), k=1
    )
    survival_noncausal = np.triu(np.ones((nodes, nodes), dtype=bool), k=1)
    noncausal_max = max(
        dense_max_abs(total[probability_noncausal]),
        dense_max_abs(kernel_survival[survival_noncausal]),
    )
    checks["causal_kernel_triangle"] = noncausal_max <= OPERATOR_TOL
    checks["final_insertion_stub_has_no_future_panel"] = bool(
        dense_max_abs(total[:, -1]) <= OPERATOR_TOL
    )
    minimum_jump = float(np.min(jump)) if jump.size else math.nan
    checks["jump_kernel_nonnegative"] = minimum_jump >= -OPERATOR_TOL

    source_formula_residual = max(
        max_abs_difference(source_trace_terms, source_jump - source_anti),
        max_abs_difference(source_trace_total, np.sum(source_trace_terms, axis=1)),
        max_abs_difference(source_activity, np.sum(source_jump, axis=1)),
    )
    checks["source_trace_and_activity_formulas"] = (
        source_formula_residual <= ARRAY_ABS_TOL
    )
    max_source_trace = dense_max_abs(source_trace_total)
    checks["environmental_insertion_trace_preserving"] = (
        max_source_trace <= SOURCE_TRACE_ABS_TOL
    )
    launch_expected = {
        "downward": 0.0,
        "upward": 2.0,
        "dephasing": 0.0,
    }[str(configuration["environment_direction"])]
    launch_error = abs(float(source_activity[0]) - launch_expected)
    checks["ground_state_launch_source_fingerprint"] = bool(
        str(configuration.get("initial_mode")) != "00"
        or launch_error <= LAUNCH_SOURCE_ABS_TOL
    )

    causal_source_trace = np.zeros_like(kernel_survival, dtype=np.float64)
    if source_trace_total.shape == (nodes,):
        for index, value in enumerate(source_trace_total.astype(np.float64)):
            causal_source_trace[index:, index] = value
    expected_kernel_survival = (
        kernel_survival_from_panel_probability(total.astype(np.float64))
        + causal_source_trace
    )
    kernel_closure = max_abs_difference(kernel_survival, expected_kernel_survival)
    checks["per_insertion_kernel_probability_closure"] = (
        kernel_closure <= KERNEL_CLOSURE_ABS_TOL
    )

    tangent_curve = chi_survival.astype(np.float64) + np.concatenate(
        ([0.0], np.cumsum(chi_panel_probability.astype(np.float64), dtype=np.float64))
    )
    tangent_abs = dense_max_abs(tangent_curve)
    response_scale = max(
        dense_max_abs(chi_survival),
        float(np.sum(np.abs(chi_panel_probability), dtype=np.float64)),
        1.0e-15,
    )
    tangent_rel = tangent_abs / response_scale
    checks["tangent_probability_closure"] = bool(
        tangent_abs <= TANGENT_CLOSURE_ABS_TOL
        or tangent_rel <= TANGENT_CLOSURE_REL_TOL
    )
    detection_identity = abs(
        float(np.sum(chi_panel_probability, dtype=np.float64))
        + float(chi_survival[-1])
    )
    checks["final_detection_response_identity"] = bool(
        detection_identity <= TANGENT_CLOSURE_ABS_TOL
        or detection_identity / response_scale <= TANGENT_CLOSURE_REL_TOL
    )

    # Reconstruct the factor-two insertion comparison from the fine raw kernel.
    try:
        coarse = aggregate_kernel_to_coarse(
            insertion_times.astype(np.float64),
            total.astype(np.float64),
            kernel_survival.astype(np.float64),
        )
        coarse_saved_residual = max(
            max_abs_difference(kernel["coarse_node_indices"], coarse["node_indices"]),
            max_abs_difference(kernel["coarse_times"], coarse["times"]),
            max_abs_difference(
                kernel["coarse_kernel_probability"], coarse["kernel_probability"]
            ),
            max_abs_difference(
                kernel["coarse_kernel_survival"], coarse["kernel_survival"]
            ),
            max_abs_difference(kernel["coarse_chi_survival"], coarse["chi_survival"]),
            max_abs_difference(
                kernel["coarse_chi_panel_probability"],
                coarse["chi_panel_probability"],
            ),
        )
        checks["saved_coarse_products_reconstructed"] = (
            coarse_saved_residual <= ARRAY_ABS_TOL
        )
        insertion_comparison = compare_fine_and_coarse_response(
            insertion_times.astype(np.float64),
            chi_survival.astype(np.float64),
            chi_panel_probability.astype(np.float64),
            coarse,
        )
        insertion_measure_pass = bool(
            insertion_comparison["signed_measure_distance"]
            <= INSERTION_CONVERGENCE_ABS_TOL
            or insertion_comparison["relative_signed_measure_distance"]
            <= INSERTION_CONVERGENCE_REL_TOL
        )
        insertion_mu_pass = bool(
            insertion_comparison["chi_mu_absolute_difference"]
            <= INSERTION_CONVERGENCE_ABS_TOL
            * max(float(configuration["T_final"]), 1.0)
            or insertion_comparison["chi_mu_relative_difference"]
            <= INSERTION_CONVERGENCE_REL_TOL
        )
        checks["insertion_grid_factor_two_check"] = (
            insertion_measure_pass and insertion_mu_pass
        )
    except Exception as exc:
        coarse = {}
        insertion_comparison = {}
        coarse_saved_residual = math.inf
        checks["saved_coarse_products_reconstructed"] = False
        checks["insertion_grid_factor_two_check"] = False
        metrics["coarse_reconstruction_error"] = str(exc)

    integrated = integrated_response_metrics(
        insertion_times.astype(np.float64),
        chi_survival.astype(np.float64),
        chi_panel_probability.astype(np.float64),
        chi_click_density.astype(np.float64),
        float(configuration.get("t_cut", T_CUT_DEFAULT)),
    )
    integrated_differences: Dict[str, Optional[float]] = {}
    for key, value in integrated.items():
        stored_value = finite_float(integrated_stored.get(key))
        integrated_differences[key] = (
            None if stored_value is None else abs(float(value) - stored_value)
        )
    checks["integrated_observables_reconstructed"] = all(
        difference is not None
        and np.isclose(
            float(integrated[key]),
            float(integrated_stored[key]),
            rtol=ARRAY_REL_TOL,
            atol=ARRAY_ABS_TOL,
        )
        for key, difference in integrated_differences.items()
    )

    # Reduced full tangent / low-rank benchmark.
    benchmark_shapes = bool(
        b_times.ndim == 1
        and b_full_s.shape == b_times.shape
        and b_low_s.shape == b_times.shape
        and b_full_p.shape == (max(b_times.size - 1, 0),)
        and b_low_p.shape == b_full_p.shape
        and b_kernel_p.shape == (max(b_times.size - 1, 0), b_times.size)
        and b_kernel_s.shape == (b_times.size, b_times.size)
    )
    checks["benchmark_shapes"] = benchmark_shapes
    benchmark_survival_error = max_abs_difference(b_full_s, b_low_s)
    benchmark_probability_error = max_abs_difference(b_full_p, b_low_p)
    benchmark_scale = max(
        dense_max_abs(b_full_s), dense_max_abs(b_full_p), BENCHMARK_ABS_TOL
    )
    benchmark_relative = max(
        benchmark_survival_error, benchmark_probability_error
    ) / benchmark_scale
    benchmark_tangent_closure = dense_max_abs(
        b_full_s + np.concatenate(([0.0], np.cumsum(b_full_p, dtype=np.float64)))
    )
    benchmark_source_trace = np.diag(b_kernel_s) if b_kernel_s.ndim == 2 else np.asarray([])
    benchmark_causal_trace = np.zeros_like(b_kernel_s, dtype=np.float64)
    if benchmark_source_trace.size == b_times.size:
        for index, value in enumerate(benchmark_source_trace):
            benchmark_causal_trace[index:, index] = value
    benchmark_kernel_closure = max_abs_difference(
        b_kernel_s,
        kernel_survival_from_panel_probability(b_kernel_p) + benchmark_causal_trace,
    ) if benchmark_shapes else math.inf
    checks["reduced_full_tangent_low_rank_benchmark"] = bool(
        benchmark_shapes
        and max(benchmark_survival_error, benchmark_probability_error)
        <= BENCHMARK_ABS_TOL + BENCHMARK_REL_TOL * benchmark_scale
        and benchmark_tangent_closure <= BENCHMARK_ABS_TOL
        and benchmark_kernel_closure <= BENCHMARK_ABS_TOL
    )

    scalar = str(configuration["propagator_type"]) == "scalar_factorized"
    scalar_pointwise_click = dense_max_abs(density_total)
    scalar_survival_kernel = dense_max_abs(kernel_survival)
    scalar_response = max(
        dense_max_abs(chi_survival), dense_max_abs(chi_click_density)
    )
    checks["pointwise_scalar_kernel_null"] = bool(
        not scalar
        or (
            scalar_pointwise_click <= SCALAR_KERNEL_ABS_TOL
            and scalar_survival_kernel <= SCALAR_RESPONSE_ABS_TOL
        )
    )
    checks["integrated_scalar_response_null"] = bool(
        not scalar or scalar_response <= SCALAR_RESPONSE_ABS_TOL
    )

    # Saved response metrics must agree with reconstructed metrics where fields
    # are present; absent optional fields become null diagnostics, not PASS.
    saved_metrics = response_audit.get("metrics", {})
    saved_metric_comparisons: Dict[str, Any] = {}
    alias_groups = {
        "maximum_source_trace_residual": (
            ("maximum_source_trace_residual",), max_source_trace, True
        ),
        "maximum_independent_kernel_probability_closure_residual": (
            ("maximum_independent_kernel_probability_closure_residual",),
            kernel_closure,
            True,
        ),
        "maximum_tangent_probability_closure_abs": (
            (
                "maximum_tangent_probability_closure_abs",
                "maximum_tangent_probability_closure_residual",
            ),
            tangent_abs,
            True,
        ),
        "maximum_tangent_probability_closure_relative": (
            (
                "maximum_tangent_probability_closure_relative",
                "relative_tangent_probability_closure_residual",
            ),
            tangent_rel,
            True,
        ),
        "maximum_abs_noncausal_kernel_entry": (
            (
                "maximum_abs_noncausal_kernel_entry",
                "maximum_noncausal_kernel_entry",
            ),
            noncausal_max,
            True,
        ),
        "minimum_jump_kernel_probability": (
            ("minimum_jump_kernel_probability",), minimum_jump, True
        ),
        "maximum_abs_pointwise_kernel_density": (
            (
                "maximum_abs_pointwise_kernel_density",
                "maximum_abs_scalar_pointwise_click_kernel",
            ),
            scalar_pointwise_click,
            True,
        ),
        "maximum_abs_pointwise_survival_kernel": (
            ("maximum_abs_pointwise_survival_kernel",),
            scalar_survival_kernel,
            False,
        ),
        "maximum_abs_integrated_response_component": (
            ("maximum_abs_integrated_response_component",), scalar_response, False
        ),
        "final_detection_response_identity_residual": (
            ("final_detection_response_identity_residual",),
            detection_identity,
            False,
        ),
    }
    saved_metrics_consistent = isinstance(saved_metrics, Mapping)
    required_found = 0
    if isinstance(saved_metrics, Mapping):
        for canonical_name, (aliases, reconstructed, required) in alias_groups.items():
            stored = None
            selected_alias = None
            for alias in aliases:
                stored = finite_float(saved_metrics.get(alias))
                if stored is not None:
                    selected_alias = alias
                    break
            if stored is None:
                saved_metric_comparisons[canonical_name] = {
                    "saved_alias": None,
                    "absolute_difference": None,
                    "required": required,
                }
                if required:
                    saved_metrics_consistent = False
                continue
            if required:
                required_found += 1
            difference = abs(stored - reconstructed)
            match = bool(
                np.isclose(
                    stored,
                    reconstructed,
                    rtol=ARRAY_REL_TOL,
                    atol=ARRAY_ABS_TOL,
                )
            )
            saved_metric_comparisons[canonical_name] = {
                "saved_alias": selected_alias,
                "absolute_difference": difference,
                "required": required,
                "match": match,
            }
            saved_metrics_consistent = saved_metrics_consistent and match
    saved_metrics_consistent = bool(saved_metrics_consistent and required_found >= 7)
    checks["saved_response_metrics_match_raw_reconstruction"] = saved_metrics_consistent

    metrics.update(
        {
            "number_of_insertion_nodes": nodes,
            "number_of_output_panels": panels,
            "kernel_interpretation": kernel_interpretation,
            "source_interpretation": source_interpretation,
            "branch_labels": branch_label_list,
            "kernel_decomposition_max_abs_residual": decomposition_residual,
            "kernel_density_max_abs_residual": density_residual,
            "response_reconstruction_max_abs_residual": response_reconstruction_residual,
            "maximum_noncausal_kernel_entry": noncausal_max,
            "minimum_jump_kernel_probability": minimum_jump,
            "source_formula_max_abs_residual": source_formula_residual,
            "maximum_source_trace_residual": max_source_trace,
            "launch_activity": float(source_activity[0]),
            "expected_launch_activity": launch_expected,
            "launch_activity_error": launch_error,
            "maximum_independent_kernel_probability_closure_residual": kernel_closure,
            "maximum_tangent_probability_closure_residual": tangent_abs,
            "relative_tangent_probability_closure_residual": tangent_rel,
            "final_detection_response_identity_residual": detection_identity,
            "insertion_comparison": insertion_comparison,
            "coarse_saved_product_max_abs_residual": coarse_saved_residual,
            "integrated_response": integrated,
            "integrated_response_stored": integrated_stored,
            "integrated_response_absolute_differences": integrated_differences,
            "benchmark_maximum_abs_chi_survival_difference": benchmark_survival_error,
            "benchmark_maximum_abs_chi_panel_probability_difference": benchmark_probability_error,
            "benchmark_relative_difference": benchmark_relative,
            "benchmark_tangent_probability_closure": benchmark_tangent_closure,
            "benchmark_independent_kernel_closure": benchmark_kernel_closure,
            "maximum_abs_scalar_pointwise_click_kernel": scalar_pointwise_click,
            "maximum_abs_scalar_survival_kernel": scalar_survival_kernel,
            "maximum_abs_scalar_response_component": scalar_response,
            "saved_response_metric_absolute_differences": saved_metric_comparisons,
        }
    )
    arrays.update(
        {
            "times": insertion_times.astype(np.float64, copy=False),
            "insertion_steps": insertion_steps.astype(np.int64, copy=False),
            "panel_durations": panel_durations.astype(np.float64, copy=False),
            "chi_survival": chi_survival.astype(np.float64, copy=False),
            "chi_click_density": chi_click_density.astype(np.float64, copy=False),
            "chi_panel_probability": chi_panel_probability.astype(np.float64, copy=False),
            "kernel_jump_probability": jump.astype(np.float64, copy=False),
            "kernel_anticommutator_probability": anti.astype(np.float64, copy=False),
            "kernel_total_probability": total.astype(np.float64, copy=False),
            "kernel_survival": kernel_survival.astype(np.float64, copy=False),
            "source_trace_total": source_trace_total.astype(np.float64, copy=False),
            "source_activity_total": source_activity.astype(np.float64, copy=False),
            "reference_survival": reference_survival.astype(np.float64, copy=False),
            "reference_s_down": reference_s_down.astype(np.float64, copy=False),
            "reference_s_up": reference_s_up.astype(np.float64, copy=False),
            "reference_s_phi": reference_s_phi.astype(np.float64, copy=False),
            "reference_top_shell": reference_top.astype(np.float64, copy=False),
            "benchmark_times": b_times.astype(np.float64, copy=False),
            "benchmark_full_chi_survival": b_full_s.astype(np.float64, copy=False),
            "benchmark_full_chi_panel_probability": b_full_p.astype(np.float64, copy=False),
            "benchmark_low_rank_chi_survival": b_low_s.astype(np.float64, copy=False),
            "benchmark_low_rank_chi_panel_probability": b_low_p.astype(np.float64, copy=False),
        }
    )
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "checks": checks,
        "failed_checks": failed,
        "metrics": metrics,
        "arrays": arrays,
        "raw_invalid": not checks["all_required_raw_numeric_arrays_finite"],
    }


# =============================================================================
# COMPLETE PER-CASE AUDIT AND STATUS CLASSIFICATION
# =============================================================================
def missing_case_result(
    spec: MatrixCaseSpec,
    decision: Optional[Mapping[str, Any]] = None,
) -> CaseAuditResult:
    selection = dict(decision or {})
    incomplete = selection.get("incomplete_candidate_records", [])
    legacy = selection.get("legacy_or_mixed_core_origins", [])
    pending_items: List[str] = []
    if incomplete:
        pending_items.append(
            "matching Task-07 folder(s) exist, but the production package is incomplete or still in progress"
        )
    if legacy:
        pending_items.append(
            "available matching candidate(s) use a legacy or non-frozen numerical core"
        )
    if not pending_items:
        pending_items.append("required Task-07 case package is absent")
    return CaseAuditResult(
        matrix_id=spec.matrix_id,
        spec=spec,
        status=STATUS_MISSING,
        scientific_admissible=False,
        reproducibility_closed=False,
        selected_candidate=None,
        mirror_origins=list(selection.get("mirror_origins", [])),
        conflicting_origins=list(selection.get("conflicting_origins", [])),
        checks={},
        failed_checks=[],
        warnings=[],
        pending_items=pending_items,
        metrics={"selection_decision": selection} if selection else {},
        arrays={},
        configuration={},
        provenance={
            "incomplete_candidate_records": incomplete,
            "legacy_or_mixed_core_origins": legacy,
        },
    )


def conflicting_case_result(
    spec: MatrixCaseSpec,
    decision: Mapping[str, Any],
) -> CaseAuditResult:
    return CaseAuditResult(
        matrix_id=spec.matrix_id,
        spec=spec,
        status=STATUS_FAILED,
        scientific_admissible=False,
        reproducibility_closed=False,
        selected_candidate=None,
        mirror_origins=list(decision.get("mirror_origins", [])),
        conflicting_origins=list(decision.get("conflicting_origins", [])),
        checks={"unique_physical_candidate": False},
        failed_checks=["unique_physical_candidate"],
        warnings=[],
        pending_items=[],
        metrics={"selection_decision": dict(decision)},
        arrays={},
        configuration={},
        provenance={},
    )


def _rerun_status(rerun: Mapping[str, Any]) -> Tuple[bool, bool, bool]:
    passed = rerun.get("passed") is True
    pending = bool(
        rerun.get("pending") is True
        or rerun.get("comparison_applicable") is False
        or str(rerun.get("status", "")).upper().endswith("PENDING")
    )
    explicit_failure = bool(
        rerun
        and not passed
        and not pending
        and (
            rerun.get("comparison_applicable") is True
            or rerun.get("failed") is True
        )
    )
    return passed, pending, explicit_failure


def audit_one_case(
    candidate: CandidateRecord,
    spec: MatrixCaseSpec,
    decision: Mapping[str, Any],
    options: Task08Options,
) -> CaseAuditResult:
    warnings: List[str] = list(candidate.discovery_warnings)
    pending: List[str] = []
    provenance = {
        **candidate.package.describe(),
        "configuration_name": candidate.configuration_name,
        "scientific_fingerprint": candidate.scientific_fingerprint,
        "selection_decision": dict(decision),
    }
    configuration_audit = audit_configuration(
        candidate,
        spec,
        expected_core_sha256=options.expected_numerical_core_sha256,
        synthetic_mode=options.synthetic_mode,
    )
    manifest_audit = audit_manifest_and_files(candidate)
    operator_reconstruction = reconstruct_operator_contract(candidate.configuration)
    json_audit = audit_saved_json_records(candidate)
    raw_audit = audit_raw_response_products(candidate)
    loader_audit = audit_per_case_loader(
        candidate, synthetic_mode=options.synthetic_mode
    )

    checks_by_group: Dict[str, Dict[str, bool]] = {
        "configuration": configuration_audit["checks"],
        "manifest_and_files": manifest_audit["checks"],
        "independent_operator_reconstruction": operator_reconstruction["checks"],
        "saved_JSON_cross_checks": json_audit["checks"],
        "independent_raw_response_reconstruction": raw_audit["checks"],
    }
    local_flat: Dict[str, bool] = {}
    flatten_boolean_checks("", checks_by_group, local_flat)
    local_pass = bool(local_flat and all(local_flat.values()))
    loader_flat: Dict[str, bool] = {}
    flatten_boolean_checks("", loader_audit["checks"], loader_flat)
    loader_pass = bool(loader_audit["present"] and loader_flat and all(loader_flat.values()))

    rerun_record = json_audit.get("rerun", {})
    rerun_passed, rerun_pending, rerun_failed = _rerun_status(rerun_record)
    if rerun_failed:
        local_flat["deterministic_rerun_explicitly_failed"] = False
        local_pass = False
    if not loader_audit["present"]:
        pending.append("independent Task-07 per-case loader package is absent")
    elif not loader_pass:
        warnings.append("saved per-case-loader products do not pass their integrity cross-check")
    if local_pass and not rerun_passed:
        pending.append("deterministic same-prefix rerun is not closed")
    if options.strict_reruns and local_pass and not rerun_passed:
        pending.append("strict Task-08 mode requires a deterministic rerun for this case")

    scientific_admissible = bool(
        local_pass
        and loader_pass
        and (rerun_passed or not options.strict_reruns)
    )
    if not local_pass or (loader_audit["present"] and not loader_pass):
        status = STATUS_FAILED
    elif not loader_audit["present"]:
        status = STATUS_LOCAL_PASS
    elif rerun_passed:
        status = STATUS_CLOSED
    else:
        status = STATUS_RERUN_PENDING

    all_checks = dict(local_flat)
    all_checks.update(
        {f"per_case_loader.{key}": value for key, value in loader_flat.items()}
    )
    failed_checks = sorted(name for name, passed in all_checks.items() if not passed)
    # A missing loader is represented by LOCAL_PASS/pending rather than by a
    # false numerical gate, preserving the requested five-state classification.
    if not loader_audit["present"]:
        failed_checks = [
            name for name in failed_checks if not name.endswith("per_case_loader_audit_present")
        ]

    warnings.extend(configuration_audit["warnings"])
    metrics = {
        "configuration": configuration_audit["metrics"],
        "manifest": {
            key: value
            for key, value in manifest_audit.items()
            if key not in {"checks", "manifest"}
        },
        "operator_reconstruction": operator_reconstruction["metrics"],
        "saved_JSON": {
            "reference_architecture": json_audit.get("reference_architecture"),
            "Task05_recovery_evidence": json_audit.get(
                "Task05_recovery_evidence", {}
            ),
            "failed_saved_response_checks": json_audit.get(
                "failed_saved_response_checks", []
            ),
        },
        "raw": raw_audit["metrics"],
        "per_case_loader": loader_audit["metrics"],
        "rerun": dict(rerun_record),
    }
    return CaseAuditResult(
        matrix_id=spec.matrix_id,
        spec=spec,
        status=status,
        scientific_admissible=scientific_admissible,
        reproducibility_closed=rerun_passed,
        selected_candidate=candidate,
        mirror_origins=list(decision.get("mirror_origins", [])),
        conflicting_origins=list(decision.get("conflicting_origins", [])),
        checks=all_checks,
        failed_checks=failed_checks,
        warnings=sorted(set(warnings)),
        pending_items=sorted(set(pending)),
        metrics=metrics,
        arrays=raw_audit["arrays"],
        configuration=dict(candidate.configuration),
        provenance=provenance,
    )


def audit_all_cases(
    records: Sequence[CandidateRecord],
    options: Task08Options,
) -> Tuple[Dict[str, CaseAuditResult], Dict[str, Any]]:
    selected, decisions = select_matrix_candidates(
        records,
        expected_core_sha256=options.expected_numerical_core_sha256,
    )
    results: Dict[str, CaseAuditResult] = {}
    for spec in FROZEN_MATRIX:
        decision = decisions[spec.matrix_id]
        candidate = selected[spec.matrix_id]
        if candidate is None:
            if decision.get("conflicting_origins"):
                result = conflicting_case_result(spec, decision)
            else:
                result = missing_case_result(spec, decision)
        else:
            try:
                result = audit_one_case(candidate, spec, decision, options)
            except Exception as exc:
                result = CaseAuditResult(
                    matrix_id=spec.matrix_id,
                    spec=spec,
                    status=STATUS_FAILED,
                    scientific_admissible=False,
                    reproducibility_closed=False,
                    selected_candidate=candidate,
                    mirror_origins=list(decision.get("mirror_origins", [])),
                    conflicting_origins=list(decision.get("conflicting_origins", [])),
                    checks={"unhandled_case_audit_exception": False},
                    failed_checks=["unhandled_case_audit_exception"],
                    warnings=[],
                    pending_items=[],
                    metrics={
                        "exception": repr(exc),
                        "traceback": traceback.format_exc(),
                    },
                    arrays={},
                    configuration=dict(candidate.configuration),
                    provenance={
                        **candidate.package.describe(),
                        "selection_decision": dict(decision),
                    },
                )
        results[spec.matrix_id] = result
    return results, {"selection_decisions": decisions}


# =============================================================================
# OPTIONAL INDEPENDENT TASK-05 RAW-INPUT RECOVERY FOR THE UPWARD LAUNCH IDENTITY
# =============================================================================
@dataclass
class Task05Candidate:
    package: PackageView
    configuration_name: str
    prefix: str
    configuration: Dict[str, Any]
    fingerprint: Optional[str] = None
    integrity_passed: bool = False
    integrity_metrics: Dict[str, Any] = field(default_factory=dict)


def _discover_task05_zip(
    zip_path: Path,
    *,
    max_member_bytes: int,
) -> List[Task05Candidate]:
    records: List[Task05Candidate] = []
    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            for info in archive.infolist():
                path = PurePosixPath(info.filename)
                if (
                    info.filename.endswith("/")
                    or not path.name.endswith("_configuration.json")
                    or path.is_absolute()
                    or ".." in path.parts
                    or info.file_size > max_member_bytes
                ):
                    continue
                try:
                    payload = json.loads(archive.read(info.filename).decode("utf-8"))
                except Exception:
                    continue
                if not isinstance(payload, dict) or payload.get("stage") != TASK05_STAGE_NAME:
                    continue
                prefix = str(payload.get("case_prefix", ""))
                if not prefix:
                    continue
                base = str(path.parent)
                if base == ".":
                    base = ""
                package = ZipPackage(
                    zip_path,
                    base,
                    prefix,
                    max_member_bytes=max_member_bytes,
                )
                records.append(
                    Task05Candidate(package, path.name, prefix, payload)
                )
    except (OSError, zipfile.BadZipFile):
        pass
    return records


def discover_task05_candidates(options: Task08Options) -> List[Task05Candidate]:
    records: List[Task05Candidate] = []
    seen: Set[Tuple[str, str]] = set()
    for raw_path in options.task05_input_paths:
        path = raw_path.expanduser().resolve()
        if not path.exists():
            continue
        if path.is_file() and zipfile.is_zipfile(path):
            candidates = _discover_task05_zip(
                path, max_member_bytes=options.max_zip_member_bytes
            )
        elif path.is_dir():
            candidates = []
            for file_path in iter_directory_files(
                path, excluded_roots=(options.output_dir,)
            ):
                if file_path.suffix.lower() == ".zip" and zipfile.is_zipfile(file_path):
                    candidates.extend(
                        _discover_task05_zip(
                            file_path,
                            max_member_bytes=options.max_zip_member_bytes,
                        )
                    )
                elif file_path.name.endswith("_configuration.json"):
                    try:
                        payload = json.loads(file_path.read_text(encoding="utf-8"))
                    except Exception:
                        continue
                    if not isinstance(payload, dict) or payload.get("stage") != TASK05_STAGE_NAME:
                        continue
                    prefix = str(payload.get("case_prefix", ""))
                    if not prefix:
                        continue
                    candidates.append(
                        Task05Candidate(
                            DirectoryPackage(file_path.parent, prefix),
                            file_path.name,
                            prefix,
                            payload,
                        )
                    )
        else:
            candidates = []
        for candidate in candidates:
            key = (candidate.package.origin, candidate.configuration_name)
            if key in seen:
                continue
            seen.add(key)
            _audit_task05_candidate_integrity(candidate)
            records.append(candidate)
    return records


def _audit_task05_candidate_integrity(candidate: Task05Candidate) -> None:
    package = candidate.package
    prefix = candidate.prefix
    configuration = candidate.configuration
    required = (
        f"{prefix}_configuration.json",
        f"{prefix}_step_loss_roof_midpoint.npy",
        f"{prefix}_output_hashes.json",
        f"{prefix}_run_status.json",
    )
    missing = [name for name in required if not package.exists(name)]
    manifest_name = f"{prefix}_output_hashes.json"
    manifest = package.read_json(manifest_name) if package.exists(manifest_name) else {}
    files = manifest.get("files", {})
    hashes_match = isinstance(files, Mapping) and bool(files)
    if isinstance(files, Mapping):
        for filename, expected in files.items():
            hashes_match = hashes_match and bool(
                isinstance(filename, str)
                and Path(filename).name == filename
                and package.exists(filename)
                and package.sha256(filename) == expected
            )
    config_copy = dict(configuration)
    stored_config_hash = str(config_copy.pop("configuration_sha256", ""))
    # Task-05 hashes the complete configuration payload, including recorded
    # backend metadata, before appending configuration_sha256.
    deterministic = dict(config_copy)
    try:
        reconstructed = sha256_json(deterministic)
    except Exception:
        reconstructed = None
    config_hash_pass = bool(
        not stored_config_hash or reconstructed == stored_config_hash
    )
    status = package.read_json(f"{prefix}_run_status.json") if package.exists(f"{prefix}_run_status.json") else {}
    status_name = str(status.get("status", ""))
    # The authoritative final Task-05 solver writes
    #   status == "completed"
    #   all_solver_checks_passed == True.
    # Earlier synthetic/diagnostic fixtures used completed_pass-style labels.
    # Accept those only when an explicit PASS Boolean is also present; never
    # accept completed_with_failed_gate merely because it starts with
    # "completed_".
    authoritative_status_pass = bool(
        status_name == "completed"
        and status.get("all_solver_checks_passed") is True
    )
    compatible_legacy_status_pass = bool(
        status_name in {"completed_pass", "completed_pass_case_local"}
        and (
            status.get("all_solver_checks_passed") is True
            or status.get("all_case_local_checks_passed") is True
        )
    )
    task05_status_pass = bool(
        authoritative_status_pass or compatible_legacy_status_pass
    )
    candidate.integrity_passed = bool(
        not missing
        and hashes_match
        and config_hash_pass
        and task05_status_pass
    )
    candidate.integrity_metrics = {
        "missing_required_files": missing,
        "manifest_hashes_match": hashes_match,
        "run_status_name": status_name,
        "authoritative_Task05_status_pass": authoritative_status_pass,
        "compatible_legacy_status_pass": compatible_legacy_status_pass,
        "run_status_passed": task05_status_pass,
        "stored_configuration_sha256": stored_config_hash,
        "reconstructed_configuration_sha256": reconstructed,
        "status": status.get("status"),
    }
    candidate.fingerprint = sha256_json(
        {
            "configuration_sha256": configuration.get("configuration_sha256"),
            "files": files,
        }
    )


def _task05_match(
    candidate: Task05Candidate,
    *,
    propagator_type: str,
    omega: float,
    mode: str,
    n_shell: int,
    dt: float,
    t_final: float,
) -> bool:
    config = candidate.configuration
    try:
        return bool(
            candidate.integrity_passed
            and config.get("zero_ambient_bath") is True
            and config.get("propagator_type") == propagator_type
            and config.get("initial_mode") == mode
            and int(config.get("N_shell")) == int(n_shell)
            and np.isclose(float(config.get("omega")), omega, rtol=0.0, atol=1e-14)
            and np.isclose(float(config.get("dt")), dt, rtol=0.0, atol=1e-15)
            and np.isclose(float(config.get("T_final")), t_final, rtol=0.0, atol=1e-12)
        )
    except Exception:
        return False


def _select_task05_candidate(
    candidates: Sequence[Task05Candidate],
    **identity: Any,
) -> Tuple[Optional[Task05Candidate], Dict[str, Any]]:
    matches = [candidate for candidate in candidates if _task05_match(candidate, **identity)]
    if not matches:
        return None, {"status": "MISSING", "matches": []}
    fingerprints = {candidate.fingerprint for candidate in matches}
    if len(fingerprints) > 1:
        return None, {
            "status": "CONFLICT",
            "matches": [candidate.package.origin for candidate in matches],
            "fingerprints": sorted(str(value) for value in fingerprints),
        }
    selected = sorted(
        matches,
        key=lambda candidate: (
            candidate.package.kind == "directory",
            candidate.package.origin,
        ),
        reverse=True,
    )[0]
    return selected, {
        "status": "SELECTED",
        "selected": selected.package.origin,
        "mirrors": sorted(
            candidate.package.origin for candidate in matches if candidate is not selected
        ),
        "fingerprint": selected.fingerprint,
    }


def aggregate_task05_panel_probabilities(
    step_probabilities: np.ndarray,
    *,
    task05_dt: float,
    response_times: np.ndarray,
) -> np.ndarray:
    step_probabilities = np.asarray(step_probabilities, dtype=np.float64)
    if step_probabilities.ndim != 1 or not np.all(np.isfinite(step_probabilities)):
        raise ValueError("Task-05 midpoint probabilities must be a finite 1-D array")
    total_time = step_probabilities.size * task05_dt
    if not np.isclose(total_time, response_times[-1], rtol=0.0, atol=2e-12):
        raise ValueError("Task-05 horizon does not match the Task-07 response grid")
    result = np.zeros(response_times.size - 1, dtype=np.float64)
    for panel, (left, right) in enumerate(zip(response_times[:-1], response_times[1:])):
        first = int(round(left / task05_dt))
        last = int(round(right / task05_dt))
        if not (
            np.isclose(first * task05_dt, left, rtol=0.0, atol=2e-12)
            and np.isclose(last * task05_dt, right, rtol=0.0, atol=2e-12)
        ):
            raise ValueError("Task-07 response panel is not aligned with Task-05 steps")
        result[panel] = float(np.sum(step_probabilities[first:last], dtype=np.float64))
    return result


def audit_upward_launch_identities(
    case_results: Mapping[str, CaseAuditResult],
    task05_candidates: Sequence[Task05Candidate],
) -> Dict[str, Any]:
    audits: Dict[str, Any] = {}
    role_to_task05 = {
        "U1": ("scalar_factorized", 100.0, 12, 5.0e-4),
        "U2": ("spinor", 100.0, 12, 5.0e-4),
        "U3": ("spinor", 1.0, 12, 1.0e-3),
    }
    for matrix_id, (propagator, omega, n_shell, dt) in role_to_task05.items():
        result = case_results[matrix_id]
        if not result.arrays:
            audits[matrix_id] = {
                "status": "TASK07_CASE_UNAVAILABLE",
                "independently_reconstructed": False,
                "passed": False,
            }
            continue
        selected_modes: Dict[str, Task05Candidate] = {}
        selection: Dict[str, Any] = {}
        conflict = False
        for mode in ("00", "10", "01"):
            candidate, record = _select_task05_candidate(
                task05_candidates,
                propagator_type=propagator,
                omega=omega,
                mode=mode,
                n_shell=n_shell,
                dt=dt,
                t_final=10.0,
            )
            selection[mode] = record
            if candidate is not None:
                selected_modes[mode] = candidate
            if record["status"] == "CONFLICT":
                conflict = True
        if conflict:
            audits[matrix_id] = {
                "status": "TASK05_CONFLICT",
                "independently_reconstructed": False,
                "passed": False,
                "selection": selection,
            }
            continue
        if len(selected_modes) != 3:
            audits[matrix_id] = {
                "status": "TASK05_RAW_INPUT_MISSING",
                "independently_reconstructed": False,
                "passed": False,
                "selection": selection,
                "note": (
                    "The Task-07 case may remain locally admissible, but the upward "
                    "s=0 identity is inherited rather than independently reconstructed."
                ),
            }
            continue
        try:
            panels: Dict[str, np.ndarray] = {}
            for mode, candidate in selected_modes.items():
                raw = candidate.package.load_npy(
                    f"{candidate.prefix}_step_loss_roof_midpoint.npy"
                )
                panels[mode] = aggregate_task05_panel_probabilities(
                    raw,
                    task05_dt=dt,
                    response_times=result.arrays["times"],
                )
            expected = panels["10"] + panels["01"] - 2.0 * panels["00"]
            actual = result.arrays["kernel_total_probability"][:, 0]
            maximum_abs = max_abs_difference(actual, expected)
            scale = max(dense_max_abs(actual), dense_max_abs(expected), UPWARD_STATIC_KERNEL_ABS_TOL)
            relative = maximum_abs / scale
            passed = bool(
                maximum_abs <= UPWARD_STATIC_KERNEL_ABS_TOL
                or relative <= UPWARD_STATIC_KERNEL_REL_TOL
            )
            audits[matrix_id] = {
                "status": "PASS" if passed else "FAIL",
                "independently_reconstructed": True,
                "passed": passed,
                "maximum_absolute_difference": maximum_abs,
                "relative_difference": relative,
                "absolute_tolerance": UPWARD_STATIC_KERNEL_ABS_TOL,
                "relative_tolerance": UPWARD_STATIC_KERNEL_REL_TOL,
                "selection": selection,
                "Task05_panel_probabilities": panels,
                "expected_kernel_column": expected,
                "actual_kernel_column": actual,
            }
        except Exception as exc:
            audits[matrix_id] = {
                "status": "FAIL_RECONSTRUCTION",
                "independently_reconstructed": False,
                "passed": False,
                "selection": selection,
                "error": str(exc),
            }
    return audits


# =============================================================================
# FAMILY-LEVEL RESPONSE RECONSTRUCTION
# =============================================================================
def _comparison_record(
    baseline: CaseAuditResult,
    control: CaseAuditResult,
    *,
    comparison_type: str,
) -> Dict[str, Any]:
    local_available = bool(baseline.arrays and control.arrays)
    scientific_evaluable = bool(
        baseline.scientific_admissible and control.scientific_admissible
    )
    if not local_available:
        return {
            "comparison_type": comparison_type,
            "baseline": baseline.matrix_id,
            "control": control.matrix_id,
            "available": False,
            "scientific_gate_evaluable": False,
            "passed": False,
            "metrics": {},
        }
    try:
        metrics = signed_response_distance(
            baseline.arrays["times"],
            baseline.arrays["chi_survival"],
            baseline.arrays["chi_panel_probability"],
            control.arrays["times"],
            control.arrays["chi_survival"],
            control.arrays["chi_panel_probability"],
        )
        b_integrated = baseline.metrics["raw"]["integrated_response"]
        c_integrated = control.metrics["raw"]["integrated_response"]
        baseline_top_shell = np.asarray(
            baseline.arrays.get("reference_top_shell", np.asarray([])),
            dtype=np.float64,
        )
        control_top_shell = np.asarray(
            control.arrays.get("reference_top_shell", np.asarray([])),
            dtype=np.float64,
        )
        baseline_source_activity = np.asarray(
            baseline.arrays.get("source_activity_total", np.asarray([])),
            dtype=np.float64,
        )
        control_source_activity = np.asarray(
            control.arrays.get("source_activity_total", np.asarray([])),
            dtype=np.float64,
        )
        top_shell_difference = (
            max_abs_difference(baseline_top_shell, control_top_shell)
            if baseline_top_shell.shape == control_top_shell.shape
            and baseline_top_shell.size
            else None
        )
        source_activity_difference = (
            max_abs_difference(baseline_source_activity, control_source_activity)
            if baseline_source_activity.shape == control_source_activity.shape
            and baseline_source_activity.size
            else None
        )
        metrics.update(
            {
                "chi_D_E_absolute_difference": abs(
                    float(b_integrated["chi_D_E"])
                    - float(c_integrated["chi_D_E"])
                ),
                "chi_D_L_absolute_difference": abs(
                    float(b_integrated["chi_D_L"])
                    - float(c_integrated["chi_D_L"])
                ),
                "baseline_maximum_reference_top_shell": (
                    dense_max_abs(baseline_top_shell)
                    if baseline_top_shell.size
                    else None
                ),
                "control_maximum_reference_top_shell": (
                    dense_max_abs(control_top_shell)
                    if control_top_shell.size
                    else None
                ),
                "maximum_reference_top_shell_curve_difference": top_shell_difference,
                "baseline_maximum_source_activity": (
                    dense_max_abs(baseline_source_activity)
                    if baseline_source_activity.size
                    else None
                ),
                "control_maximum_source_activity": (
                    dense_max_abs(control_source_activity)
                    if control_source_activity.size
                    else None
                ),
                "maximum_source_activity_curve_difference": source_activity_difference,
                "top_shell_and_source_activity_are_diagnostics_not_substitutes_for_response_law": True,
                "complete_signed_measure_absolute_gate": FAMILY_RESPONSE_ABS_TOL,
                "complete_signed_measure_relative_gate": FAMILY_RESPONSE_REL_TOL,
            }
        )
        passed = bool(
            metrics["complete_signed_measure_distance"] <= FAMILY_RESPONSE_ABS_TOL
            or metrics["relative_signed_measure_distance"] <= FAMILY_RESPONSE_REL_TOL
        )
        return {
            "comparison_type": comparison_type,
            "baseline": baseline.matrix_id,
            "control": control.matrix_id,
            "available": True,
            "scientific_gate_evaluable": scientific_evaluable,
            "passed": passed,
            "metrics": metrics,
        }
    except Exception as exc:
        return {
            "comparison_type": comparison_type,
            "baseline": baseline.matrix_id,
            "control": control.matrix_id,
            "available": True,
            "scientific_gate_evaluable": scientific_evaluable,
            "passed": False,
            "metrics": {"error": str(exc)},
        }


def build_family_audits(
    case_results: Mapping[str, CaseAuditResult],
) -> Dict[str, Any]:
    family_letters = {"downward": "D", "upward": "U", "dephasing": "P"}
    families: Dict[str, Any] = {}
    time_rows: List[Dict[str, Any]] = []
    shell_rows: List[Dict[str, Any]] = []
    confinement_rows: List[Dict[str, Any]] = []
    for direction, letter in family_letters.items():
        scalar = case_results[f"{letter}1"]
        baseline = case_results[f"{letter}2"]
        weak = case_results[f"{letter}3"]
        time_control = case_results[f"{letter}4"]
        shell_control = case_results[f"{letter}5"]
        time_comparison = _comparison_record(
            baseline, time_control, comparison_type="baseline_vs_dt_over_2"
        )
        shell_comparison = _comparison_record(
            baseline, shell_control, comparison_type="baseline_vs_N16"
        )
        confinement_comparison = _comparison_record(
            baseline, weak, comparison_type="omega100_vs_omega1"
        )
        time_rows.append({"direction": direction, **time_comparison})
        shell_rows.append({"direction": direction, **shell_comparison})
        confinement_rows.append({"direction": direction, **confinement_comparison})
        scalar_raw = scalar.metrics.get("raw", {})
        scalar_null = {
            "matrix_id": scalar.matrix_id,
            "available": bool(scalar.arrays),
            "scientific_admissible": scalar.scientific_admissible,
            "pointwise_click_kernel_max": scalar_raw.get(
                "maximum_abs_scalar_pointwise_click_kernel"
            ),
            "survival_kernel_max": scalar_raw.get(
                "maximum_abs_scalar_survival_kernel"
            ),
            "response_component_max": scalar_raw.get(
                "maximum_abs_scalar_response_component"
            ),
            "pointwise_pass": scalar.checks.get(
                "independent_raw_response_reconstruction.pointwise_scalar_kernel_null",
                False,
            ),
            "integrated_pass": scalar.checks.get(
                "independent_raw_response_reconstruction.integrated_scalar_response_null",
                False,
            ),
        }
        families[direction] = {
            "direction": direction,
            "matrix_ids": [f"{letter}{index}" for index in range(1, 6)],
            "case_statuses": {
                f"{letter}{index}": case_results[f"{letter}{index}"].status
                for index in range(1, 6)
            },
            "scalar_null": scalar_null,
            "time_step_convergence": time_comparison,
            "shell_convergence": shell_comparison,
            "confinement_comparison": confinement_comparison,
            "all_five_cases_scientifically_admissible": all(
                case_results[f"{letter}{index}"].scientific_admissible
                for index in range(1, 6)
            ),
        }
    return {
        "families": families,
        "time_step_rows": time_rows,
        "shell_rows": shell_rows,
        "confinement_rows": confinement_rows,
    }


# =============================================================================
# UNCERTAINTY BUDGET AND FACTOR-FIVE EVIDENCE CLASSIFICATION
# =============================================================================
def load_inherited_bounds(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {}
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        return {"_error": f"inherited bounds file not found: {resolved}"}
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_error": f"cannot read inherited bounds: {exc}"}
    if not isinstance(payload, dict):
        return {"_error": "inherited bounds JSON must contain an object"}
    return payload


def inherited_bound_for(
    payload: Mapping[str, Any], direction: str, name: str
) -> Optional[float]:
    candidates: List[Any] = []
    direction_block = payload.get("by_direction", {})
    if isinstance(direction_block, Mapping):
        block = direction_block.get(direction, {})
        if isinstance(block, Mapping):
            candidates.append(block.get(name))
    global_block = payload.get("global", {})
    if isinstance(global_block, Mapping):
        candidates.append(global_block.get(name))
    candidates.append(payload.get(name))
    for candidate in candidates:
        value = finite_float(candidate)
        if value is not None and value >= 0.0:
            return value
    return None


def _recursive_numeric_values_for_key_fragment(
    payload: Any, fragment: str
) -> List[float]:
    """Legacy broad search retained for backward compatibility."""
    values: List[float] = []
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            if fragment.lower() in str(key).lower():
                numeric = finite_float(value)
                if numeric is not None:
                    values.append(abs(numeric))
            values.extend(_recursive_numeric_values_for_key_fragment(value, fragment))
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            values.extend(_recursive_numeric_values_for_key_fragment(item, fragment))
    return values


def _recursive_observed_numeric_values(
    payload: Any,
    exact_keys: Set[str],
    *,
    path: Tuple[str, ...] = (),
) -> List[float]:
    """Collect observed metrics while excluding tolerance/threshold records."""
    values: List[float] = []
    excluded_path_tokens = ("toler", "threshold", "expected", "limit", "gate")
    if any(
        any(token in component.lower() for token in excluded_path_tokens)
        for component in path
    ):
        return values
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            key_text = str(key)
            if key_text in exact_keys:
                numeric = finite_float(value)
                if numeric is not None:
                    values.append(abs(numeric))
            values.extend(
                _recursive_observed_numeric_values(
                    value,
                    exact_keys,
                    path=path + (key_text,),
                )
            )
    elif isinstance(payload, (list, tuple)):
        for index, item in enumerate(payload):
            values.extend(
                _recursive_observed_numeric_values(
                    item,
                    exact_keys,
                    path=path + (str(index),),
                )
            )
    return values


def solve_uncertainty_component(result: CaseAuditResult) -> Dict[str, Any]:
    raw = result.metrics.get("raw", {})
    response_norm = finite_float(
        nested_get(raw, "integrated_response.chi_complete_signed_measure_norm")
    ) or 0.0
    source_trace = finite_float(raw.get("maximum_source_trace_residual")) or 0.0
    tangent_closure = finite_float(
        raw.get("maximum_tangent_probability_closure_residual")
    ) or 0.0
    benchmark_s = finite_float(
        raw.get("benchmark_maximum_abs_chi_survival_difference")
    ) or 0.0
    benchmark_p = finite_float(
        raw.get("benchmark_maximum_abs_chi_panel_probability_difference")
    ) or 0.0
    branch_residual = 0.0
    reference_residual = 0.0
    if result.selected_candidate is not None:
        package = result.selected_candidate.package
        prefix = result.selected_candidate.prefix
        for suffix in ("response_audit.json", "runtime_metrics.json", "reference_audit.json"):
            name = f"{prefix}_{suffix}"
            if not package.exists(name):
                continue
            try:
                record = package.read_json(name)
            except Exception:
                continue
            branch_values = _recursive_observed_numeric_values(
                record,
                {
                    "maximum_branch_true_relative_residual",
                    "observed_maximum_branch_true_relative_residual",
                },
            )
            reference_values = _recursive_observed_numeric_values(
                record,
                {
                    "maximum_reference_true_relative_residual",
                    "observed_maximum_reference_true_relative_residual",
                    "maximum_true_relative_residual",
                },
            )
            branch_residual = max([branch_residual, *branch_values])
            reference_residual = max([reference_residual, *reference_values])
    residual_term = max(branch_residual, reference_residual) * max(
        response_norm, 1.0
    )
    source_term = EXPECTED_T_FINAL * source_trace
    benchmark_term = 0.5 * (
        100.0 * benchmark_p + benchmark_s
    ) if benchmark_p or benchmark_s else 0.0
    # The benchmark panel discrepancy is a per-panel maximum, hence the
    # conservative factor equal to the 100-panel production grid.
    total = residual_term + source_term + benchmark_term + tangent_closure
    return {
        "epsilon_solve": total,
        "components": {
            "Krylov_residual_bound": residual_term,
            "source_trace_horizon_bound": source_term,
            "reduced_benchmark_complete_measure_bound": benchmark_term,
            "final_tangent_closure_bound": tangent_closure,
        },
        "observed_maximum_branch_true_relative_residual": branch_residual,
        "observed_maximum_reference_true_relative_residual": reference_residual,
        "formula": (
            "max(Krylov residual)*max(response norm,1) + T*max source trace + "
            "conservative reduced-benchmark complete-measure discrepancy + "
            "final tangent closure"
        ),
    }


def build_uncertainty_and_evidence(
    case_results: Mapping[str, CaseAuditResult],
    family_audits: Mapping[str, Any],
    inherited_bounds: Mapping[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    letter_by_direction = {"downward": "D", "upward": "U", "dephasing": "P"}
    budgets: Dict[str, Any] = {}
    classifications: Dict[str, Any] = {}
    for direction, letter in letter_by_direction.items():
        baseline = case_results[f"{letter}2"]
        family = family_audits["families"][direction]
        raw = baseline.metrics.get("raw", {})
        insertion = raw.get("insertion_comparison", {})
        epsilon_squad = finite_float(insertion.get("signed_measure_distance"))
        epsilon_dt = finite_float(
            nested_get(
                family,
                "time_step_convergence.metrics.complete_signed_measure_distance",
            )
        )
        epsilon_n = finite_float(
            nested_get(
                family,
                "shell_convergence.metrics.complete_signed_measure_distance",
            )
        )
        solve_record = solve_uncertainty_component(baseline) if baseline.arrays else {
            "epsilon_solve": None,
            "components": {},
            "formula": "unavailable because baseline raw response is absent",
        }
        epsilon_solve = finite_float(solve_record.get("epsilon_solve"))
        epsilon_repr = inherited_bound_for(inherited_bounds, direction, "epsilon_repr")
        epsilon_z = inherited_bound_for(inherited_bounds, direction, "epsilon_z")
        epsilon_init = 0.0  # exact pure mode-00 campaign
        epsilon_mc = 0.0  # deterministic tangent calculation
        components: Dict[str, Optional[float]] = {
            "epsilon_repr": epsilon_repr,
            "epsilon_z": epsilon_z,
            "epsilon_dt": epsilon_dt,
            "epsilon_N": epsilon_n,
            "epsilon_init": epsilon_init,
            "epsilon_s_quad": epsilon_squad,
            "epsilon_solve": epsilon_solve,
            "epsilon_MC": epsilon_mc,
        }
        required_names = tuple(components)
        missing = [name for name in required_names if components[name] is None]
        epsilon_total = (
            None
            if missing
            else float(sum(float(components[name]) for name in required_names))
        )
        response_norm = finite_float(
            nested_get(raw, "integrated_response.chi_complete_signed_measure_norm")
        )
        ratio = (
            None
            if response_norm is None
            or epsilon_total is None
            or epsilon_total <= 0.0
            else response_norm / epsilon_total
        )
        if response_norm is None or epsilon_total is None:
            classification = EVIDENCE_BUDGET_INCOMPLETE
        elif epsilon_total == 0.0:
            classification = (
                EVIDENCE_ZERO if response_norm == 0.0 else EVIDENCE_RESOLVED
            )
            ratio = None if response_norm > 0.0 else 0.0
        elif ratio is not None and ratio >= EVIDENCE_FACTOR:
            classification = EVIDENCE_RESOLVED
        elif ratio is not None and ratio <= 1.0:
            classification = EVIDENCE_ZERO
        else:
            classification = EVIDENCE_UNRESOLVED
        budgets[direction] = {
            "baseline_matrix_id": f"{letter}2",
            "components": components,
            "epsilon_total_zero_rate": epsilon_total,
            "missing_required_components": missing,
            "complete": not missing,
            "epsilon_lin": {
                "value": None,
                "status": (
                    "NOT_APPLICABLE_TO_EXACT_ZERO_RATE_DERIVATIVE; required only "
                    "before finite-rate extrapolation in Tasks 09-10"
                ),
            },
            "solve_component_detail": solve_record,
            "inherited_bounds_source": dict(inherited_bounds),
            "conservative_sum_rule": True,
        }
        classifications[direction] = {
            "baseline_matrix_id": f"{letter}2",
            "response_norm": response_norm,
            "epsilon_total_zero_rate": epsilon_total,
            "signal_to_uncertainty_ratio": ratio,
            "classification": classification,
            "resolved_nonzero_factor": EVIDENCE_FACTOR,
            "physical_claim_eligible_from_evidence_alone": classification
            in {EVIDENCE_RESOLVED, EVIDENCE_ZERO},
        }
    return {"by_direction": budgets}, {"by_direction": classifications}


# =============================================================================
# OVERALL SCIENTIFIC AND REPRODUCIBILITY VERDICTS
# =============================================================================
def classify_failure_origin(result: CaseAuditResult) -> str:
    integrity_fragments = (
        "configuration",
        "manifest",
        "hash",
        "source",
        "physical_identity",
        "unique_physical_candidate",
        "required_solver_files",
        "schema",
        "dtype",
        "finite",
    )
    if any(
        any(fragment in name.lower() for fragment in integrity_fragments)
        for name in result.failed_checks
    ):
        return "integrity"
    return "local_numerics"


def build_channel_superposition_audit(
    case_results: Mapping[str, CaseAuditResult],
) -> Dict[str, Any]:
    """Audit the three validated tangent directions as a linear basis.

    This is an algebraic zero-rate linear-response record only. It does not
    propagate a finite-rate bath and does not assign a temperature.
    """
    baseline_ids = {
        "downward": "D2",
        "upward": "U2",
        "dephasing": "P2",
    }
    basis: Dict[str, Any] = {}
    available_times: List[np.ndarray] = []
    for direction, matrix_id in baseline_ids.items():
        result = case_results[matrix_id]
        available = bool(result.scientific_admissible and result.arrays)
        entry: Dict[str, Any] = {
            "matrix_id": matrix_id,
            "scientifically_admissible": result.scientific_admissible,
            "available": available,
        }
        if available:
            times = np.asarray(result.arrays["times"], dtype=np.float64)
            available_times.append(times)
            integrated = result.metrics.get("raw", {}).get(
                "integrated_response", {}
            )
            entry.update(
                {
                    "time_node_count": int(times.size),
                    "chi_D": integrated.get("chi_D_from_final_survival"),
                    "chi_mu": integrated.get("chi_mu_restricted"),
                    "chi_D_E": integrated.get("chi_D_E"),
                    "chi_D_L": integrated.get("chi_D_L"),
                }
            )
        basis[direction] = entry

    all_available = all(record["available"] for record in basis.values())
    common_grid = False
    if all_available and available_times:
        reference = available_times[0]
        common_grid = all(
            times.shape == reference.shape
            and max_abs_difference(times, reference) <= ARRAY_ABS_TOL
            for times in available_times[1:]
        )
    return {
        "status": (
            "PASS_LINEAR_BASIS_AVAILABLE"
            if all_available and common_grid
            else "PENDING_REQUIRED_BASELINE_CASES"
            if not all_available
            else "FAIL_INCOMPATIBLE_BASELINE_GRIDS"
        ),
        "passed": bool(all_available and common_grid),
        "all_three_baselines_available": all_available,
        "common_response_grid": common_grid,
        "basis": basis,
        "formal_superposition": (
            "chi[c_down,c_up,c_phi] = c_down*chi_down + "
            "c_up*chi_up + c_phi*chi_phi"
        ),
        "thermal_linear_response_example": (
            "chi_thermal(nbar) = (nbar+1)*chi_down + nbar*chi_up"
        ),
        "finite_rate_or_temperature_trajectory_simulation": False,
        "interpretation": (
            "Linearity is at the tangent-generator level. This record does not "
            "authorize a finite-rate or finite-temperature trajectory claim."
        ),
    }


def build_overall_verdict(
    case_results: Mapping[str, CaseAuditResult],
    family_audits: Mapping[str, Any],
    upward_audits: Mapping[str, Any],
    uncertainty: Mapping[str, Any],
    evidence: Mapping[str, Any],
    channel_superposition: Mapping[str, Any],
    *,
    authority_audit_passed: bool,
    self_scope_passed: bool,
) -> Dict[str, Any]:
    failed_cases = [
        result for result in case_results.values() if result.status == STATUS_FAILED
    ]
    missing_cases = [
        result.matrix_id
        for result in case_results.values()
        if result.status == STATUS_MISSING
    ]
    scientifically_inadmissible = [
        result.matrix_id
        for result in case_results.values()
        if not result.scientific_admissible
    ]
    integrity_failures = [
        result.matrix_id
        for result in failed_cases
        if classify_failure_origin(result) == "integrity"
    ]
    numerical_failures = [
        result.matrix_id
        for result in failed_cases
        if classify_failure_origin(result) == "local_numerics"
    ]

    scalar_failures: List[str] = []
    dt_failures: List[str] = []
    shell_failures: List[str] = []
    for direction, family in family_audits["families"].items():
        scalar = family["scalar_null"]
        if scalar["available"] and not (
            scalar["pointwise_pass"] and scalar["integrated_pass"]
        ):
            scalar_failures.append(direction)
        time_record = family["time_step_convergence"]
        if (
            time_record["scientific_gate_evaluable"]
            and not time_record["passed"]
        ):
            dt_failures.append(direction)
        shell_record = family["shell_convergence"]
        if (
            shell_record["scientific_gate_evaluable"]
            and not shell_record["passed"]
        ):
            shell_failures.append(direction)

    upward_failed = [
        matrix_id
        for matrix_id, record in upward_audits.items()
        if record.get("independently_reconstructed") is True
        and record.get("passed") is not True
    ]
    upward_missing = [
        matrix_id
        for matrix_id, record in upward_audits.items()
        if record.get("status") == "TASK05_RAW_INPUT_MISSING"
    ]
    upward_conflict = [
        matrix_id
        for matrix_id, record in upward_audits.items()
        if record.get("status") == "TASK05_CONFLICT"
    ]

    evidence_records = evidence.get("by_direction", {})
    evidence_classes = {
        direction: record.get("classification")
        for direction, record in evidence_records.items()
    }
    unresolved_evidence = [
        direction
        for direction, classification in evidence_classes.items()
        if classification in {EVIDENCE_UNRESOLVED, EVIDENCE_BUDGET_INCOMPLETE}
    ]
    all_zero = bool(evidence_classes) and all(
        classification == EVIDENCE_ZERO
        for classification in evidence_classes.values()
    )
    representative_deterministic_certification_pass = bool(
        case_results.get("D3") is not None
        and case_results["D3"].reproducibility_closed
    )

    if not authority_audit_passed or not self_scope_passed:
        verdict = "FAIL_INPUT_INTEGRITY"
        exit_code = 2
    elif integrity_failures or upward_conflict:
        verdict = "FAIL_INPUT_INTEGRITY"
        exit_code = 2
    elif numerical_failures or upward_failed:
        verdict = "FAIL_CASE_LOCAL_NUMERICS"
        exit_code = 2
    elif scalar_failures:
        verdict = "FAIL_SCALAR_POINTWISE_NULL"
        exit_code = 2
    elif dt_failures:
        verdict = "FAIL_TIME_STEP_CONVERGENCE"
        exit_code = 2
    elif shell_failures:
        verdict = "FAIL_SHELL_CONVERGENCE"
        exit_code = 2
    elif (
        channel_superposition.get("all_three_baselines_available") is True
        and channel_superposition.get("common_response_grid") is not True
    ):
        verdict = "FAIL_INPUT_INTEGRITY"
        exit_code = 2
    elif missing_cases or scientifically_inadmissible:
        verdict = "INCOMPLETE_REQUIRED_CASE_MATRIX"
        exit_code = 3
    elif not representative_deterministic_certification_pass:
        verdict = "INCOMPLETE_REQUIRED_CASE_MATRIX"
        exit_code = 3
    elif upward_missing:
        verdict = "QUALIFIED_PASS_MISSING_INDEPENDENT_TASK05_RAW_INPUT"
        exit_code = 3
    elif unresolved_evidence:
        verdict = "UNRESOLVED_NUMERICAL_EVIDENCE"
        exit_code = 3
    elif all_zero:
        verdict = "PASS_TASK08_ALL_CHANNELS_ZERO_COMPATIBLE"
        exit_code = 0
    else:
        verdict = "PASS_TASK08_LINEAR_RESPONSE"
        exit_code = 0

    physical_claim_authorized = verdict in {
        "PASS_TASK08_LINEAR_RESPONSE",
        "PASS_TASK08_ALL_CHANNELS_ZERO_COMPATIBLE",
    }
    return {
        "scientific_verdict": verdict,
        "exit_code": exit_code,
        "physical_zero_rate_susceptibility_claim_authorized": physical_claim_authorized,
        "task08_finite_v8_zero_rate_response_gate_authorized": physical_claim_authorized,
        "publication_level_project_claim_closed_under_attached_master": False,
        "attached_master_Task05_06_status": ATTACHED_MASTER_TASK05_06_STATUS,
        "attached_master_publication_level_status": (
            ATTACHED_MASTER_PUBLICATION_LEVEL_STATUS
        ),
        "finite_rate_or_temperature_claim_authorized": False,
        "failed_cases": [result.matrix_id for result in failed_cases],
        "missing_cases": missing_cases,
        "scientifically_inadmissible_cases": scientifically_inadmissible,
        "integrity_failure_cases": integrity_failures,
        "local_numerical_failure_cases": numerical_failures,
        "scalar_null_failure_directions": scalar_failures,
        "time_step_failure_directions": dt_failures,
        "shell_failure_directions": shell_failures,
        "upward_identity_failed_cases": upward_failed,
        "upward_identity_missing_Task05_raw_cases": upward_missing,
        "upward_identity_conflicting_Task05_cases": upward_conflict,
        "evidence_classifications": evidence_classes,
        "unresolved_evidence_directions": unresolved_evidence,
        "representative_deterministic_certification_case": "D3",
        "representative_deterministic_certification_pass": (
            representative_deterministic_certification_pass
        ),
        "channel_superposition_status": channel_superposition.get("status"),
        "channel_superposition_basis_passed": channel_superposition.get("passed"),
        "Task05_zero_rate_recovery_evidence_scope": (
            "hashed Task-07 recovery records are verified; exact replay-array "
            "comparison is inherited because replay arrays are not part of the "
            "Task-07 case-share contract"
        ),
        "claim_scope": (
            "Task-07 response kernels and zero-rate linear-response families are "
            "independently reconstructed from raw Task-07 products for the frozen "
            "finite v8 model; Task-05 replay comparison remains hashed/provenance-verified"
            if physical_claim_authorized
            else "no physical susceptibility claim"
        ),
    }


def build_reproducibility_coverage(
    case_results: Mapping[str, CaseAuditResult],
) -> Dict[str, Any]:
    closed = sorted(
        result.matrix_id
        for result in case_results.values()
        if result.reproducibility_closed
    )
    pending = sorted(
        result.matrix_id
        for result in case_results.values()
        if result.status == STATUS_RERUN_PENDING
    )
    return {
        "representative_deterministic_certification_case": "D3",
        "representative_deterministic_certification_pass": case_results[
            "D3"
        ].reproducibility_closed,
        "per_case_rerun_coverage_count": len(closed),
        "per_case_rerun_coverage_total": 15,
        "per_case_rerun_coverage_fraction": len(closed) / 15.0,
        "closed_cases": closed,
        "rerun_pending_cases": pending,
        "coverage_status": (
            "PER_CASE_RERUN_COVERAGE_COMPLETE"
            if len(closed) == 15
            else "PER_CASE_RERUN_COVERAGE_INCOMPLETE"
        ),
        "scientific_independence_policy": (
            "Default Task-08 scientific validity is independent of complete per-case "
            "rerun coverage; strict mode may require 15/15."
        ),
    }


# =============================================================================
# AUTHORITY AND SOURCE SELF-AUDITS
# =============================================================================
def resolve_loader_source_path(
    capture_directory: Optional[Path] = None,
) -> Path:
    candidates: List[Path] = []
    executing = globals().get("__file__")
    if isinstance(executing, (str, os.PathLike)):
        candidates.append(Path(executing))
    environment = os.environ.get("TASK08_LOADER_SOURCE")
    if environment:
        candidates.append(Path(environment))
    for candidate in candidates:
        try:
            resolved = candidate.expanduser().resolve()
        except Exception:
            continue
        if resolved.is_file():
            return resolved
    try:
        from IPython import get_ipython  # type: ignore

        ipython = get_ipython()
        if ipython is not None:
            history = getattr(ipython.history_manager, "input_hist_raw", ())
            for source in reversed(tuple(history)[-20:]):
                if isinstance(source, str) and "def run_task08" in source and STAGE_NAME in source:
                    target_directory = (
                        capture_directory.expanduser().resolve()
                        if capture_directory is not None
                        else Path(tempfile.gettempdir()).resolve()
                    )
                    target_directory.mkdir(parents=True, exist_ok=True)
                    path = target_directory / "Task08_loader_JUPYTER_CAPTURED.py"
                    atomic_write_text(path, source)
                    return path
    except Exception:
        pass
    raise FileNotFoundError(
        "Cannot resolve the Task-08 loader source. Run the saved .py file, set "
        "TASK08_LOADER_SOURCE, or paste the complete source in one Jupyter cell."
    )


def audit_authority_files(options: Task08Options) -> Dict[str, Any]:
    rows: Dict[str, Any] = {}
    passed = True
    for label, path, expected in (
        ("master_audit", options.master_audit_path, MASTER_AUDIT_EXPECTED_SHA256),
        ("Task07_Task08_handoff", options.handoff_path, TASK07_TASK08_HANDOFF_EXPECTED_SHA256),
    ):
        if path is None:
            rows[label] = {
                "path": None,
                "expected_sha256": expected,
                "actual_sha256": None,
                "verified": False,
                "status": "EMBEDDED_CONTRACT_ONLY",
            }
            continue
        resolved = path.expanduser().resolve()
        actual = sha256_file(resolved) if resolved.is_file() else None
        verified = actual == expected
        rows[label] = {
            "path": str(resolved),
            "expected_sha256": expected,
            "actual_sha256": actual,
            "verified": verified,
            "status": "PASS" if verified else "FAIL",
        }
        passed = passed and verified
    # Runtime copies are optional because the complete immutable contract and
    # hashes are embedded. When explicit paths are supplied, mismatches fail.
    explicit_paths_supplied = any(
        path is not None for path in (options.master_audit_path, options.handoff_path)
    )
    return {
        "files": rows,
        "explicit_authority_paths_supplied": explicit_paths_supplied,
        "passed": passed,
        "authority_precedence": [
            "current numerical master audit",
            "final Task-07 to Task-08 handoff for corrected v8 contract",
            "frozen Task-07 v8 raw products reconstructed independently",
        ],
    }


# =============================================================================
# STRICT OUTPUT SERIALIZATION AND TABLE BUILDERS
# =============================================================================
def derived_json_safe_with_report(
    value: Any, path: str = "root"
) -> Tuple[Any, List[Dict[str, str]]]:
    replacements: List[Dict[str, str]] = []

    def convert(item: Any, current: str) -> Any:
        if item is None or isinstance(item, (str, bool, int)):
            return item
        if isinstance(item, Path):
            return str(item)
        if isinstance(item, np.integer):
            return int(item)
        if isinstance(item, (float, np.floating)):
            numeric = float(item)
            if not math.isfinite(numeric):
                replacements.append(
                    {
                        "path": current,
                        "reason": f"derived non-finite value {numeric!r} replaced by JSON null",
                    }
                )
                return None
            return numeric
        if isinstance(item, np.ndarray):
            if item.dtype.kind in "fc" and not np.all(np.isfinite(item)):
                replacements.append(
                    {
                        "path": current,
                        "reason": "derived array contains non-finite values and is omitted from JSON",
                    }
                )
                return None
            return item.tolist()
        if isinstance(item, Mapping):
            return {
                str(key): convert(subitem, f"{current}.{key}")
                for key, subitem in item.items()
            }
        if isinstance(item, (list, tuple, set)):
            return [
                convert(subitem, f"{current}[{index}]")
                for index, subitem in enumerate(item)
            ]
        if hasattr(item, "__dict__"):
            return convert(vars(item), current)
        replacements.append(
            {
                "path": current,
                "reason": f"unsupported derived type {type(item).__name__} represented as text",
            }
        )
        return repr(item)

    return convert(value, path), replacements


def atomic_write_derived_json(
    path: Path, payload: Mapping[str, Any]
) -> List[Dict[str, str]]:
    safe, replacements = derived_json_safe_with_report(payload)
    if isinstance(safe, dict) and replacements:
        safe.setdefault("serialization_notes", {})
        safe["serialization_notes"]["derived_null_replacements"] = replacements
    text = json.dumps(
        safe,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n"
    atomic_write_text(path, text)
    return replacements


def case_result_json(result: CaseAuditResult) -> Dict[str, Any]:
    return {
        "matrix_id": result.matrix_id,
        "frozen_specification": asdict(result.spec),
        "status": result.status,
        "scientific_admissible": result.scientific_admissible,
        "reproducibility_closed": result.reproducibility_closed,
        "selected_candidate": (
            None
            if result.selected_candidate is None
            else {
                **result.selected_candidate.package.describe(),
                "configuration_name": result.selected_candidate.configuration_name,
                "prefix": result.selected_candidate.prefix,
                "scientific_fingerprint": result.selected_candidate.scientific_fingerprint,
            }
        ),
        "mirror_origins": result.mirror_origins,
        "conflicting_origins": result.conflicting_origins,
        "checks": result.checks,
        "failed_checks": result.failed_checks,
        "warnings": result.warnings,
        "pending_items": result.pending_items,
        "metrics": result.metrics,
        "configuration": result.configuration,
        "provenance": result.provenance,
        "array_inventory": {
            name: {
                "shape": list(array.shape),
                "dtype": str(array.dtype),
                "finite": bool(np.all(np.isfinite(array)))
                if array.dtype.kind in "fc"
                else True,
            }
            for name, array in result.arrays.items()
        },
    }


def case_identity_rows(case_results: Mapping[str, CaseAuditResult]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for spec in FROZEN_MATRIX:
        result = case_results[spec.matrix_id]
        rows.append(
            {
                "matrix_id": spec.matrix_id,
                "role": spec.role,
                "propagator_type": spec.propagator_type,
                "direction": spec.environment_direction,
                "omega": spec.omega,
                "initial_mode": spec.initial_mode,
                "N_shell": spec.n_shell,
                "dt": spec.dt,
                "T_final": spec.t_final,
                "insertion_dt": spec.insertion_dt,
                "canonical_prefix": spec.canonical_prefix(),
                "status": result.status,
                "scientific_admissible": result.scientific_admissible,
                "reproducibility_closed": result.reproducibility_closed,
                "selected_origin": (
                    result.selected_candidate.package.origin
                    if result.selected_candidate is not None
                    else None
                ),
                "selected_kind": (
                    result.selected_candidate.package.kind
                    if result.selected_candidate is not None
                    else None
                ),
                "numerical_core_sha256": result.configuration.get(
                    "numerical_core_sha256"
                ),
                "configuration_sha256": result.configuration.get(
                    "configuration_sha256"
                ),
                "scientific_fingerprint": (
                    result.selected_candidate.scientific_fingerprint
                    if result.selected_candidate is not None
                    else None
                ),
                "failed_check_count": len(result.failed_checks),
                "pending_item_count": len(result.pending_items),
            }
        )
    return rows


def per_case_metric_rows(case_results: Mapping[str, CaseAuditResult]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for spec in FROZEN_MATRIX:
        result = case_results[spec.matrix_id]
        raw = result.metrics.get("raw", {})
        integrated = raw.get("integrated_response", {})
        insertion = raw.get("insertion_comparison", {})
        rows.append(
            {
                "matrix_id": spec.matrix_id,
                "status": result.status,
                "scientific_admissible": result.scientific_admissible,
                "reproducibility_closed": result.reproducibility_closed,
                "chi_D": integrated.get("chi_D_from_panel_sum"),
                "minus_chi_S_T": integrated.get("chi_D_from_final_survival"),
                "chi_mu": integrated.get("chi_mu_restricted"),
                "chi_D_E": integrated.get("chi_D_E"),
                "chi_D_L": integrated.get("chi_D_L"),
                "complete_signed_measure_norm": integrated.get(
                    "chi_complete_signed_measure_norm"
                ),
                "survival_W1_norm": integrated.get("chi_survival_W1_norm"),
                "maximum_tangent_closure": raw.get(
                    "maximum_tangent_probability_closure_residual"
                ),
                "relative_tangent_closure": raw.get(
                    "relative_tangent_probability_closure_residual"
                ),
                "maximum_per_insertion_closure": raw.get(
                    "maximum_independent_kernel_probability_closure_residual"
                ),
                "maximum_source_trace": raw.get("maximum_source_trace_residual"),
                "maximum_noncausal_kernel": raw.get(
                    "maximum_noncausal_kernel_entry"
                ),
                "minimum_jump_kernel_probability": raw.get(
                    "minimum_jump_kernel_probability"
                ),
                "insertion_signed_measure_distance": insertion.get(
                    "signed_measure_distance"
                ),
                "insertion_relative_signed_measure_distance": insertion.get(
                    "relative_signed_measure_distance"
                ),
                "insertion_chi_mu_absolute_difference": insertion.get(
                    "chi_mu_absolute_difference"
                ),
                "benchmark_survival_difference": raw.get(
                    "benchmark_maximum_abs_chi_survival_difference"
                ),
                "benchmark_panel_difference": raw.get(
                    "benchmark_maximum_abs_chi_panel_probability_difference"
                ),
                "scalar_pointwise_kernel_max": raw.get(
                    "maximum_abs_scalar_pointwise_click_kernel"
                ),
                "scalar_response_max": raw.get(
                    "maximum_abs_scalar_response_component"
                ),
                "failed_checks": result.failed_checks,
                "pending_items": result.pending_items,
            }
        )
    return rows


def complete_response_curve_rows(
    case_results: Mapping[str, CaseAuditResult]
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for spec in FROZEN_MATRIX:
        result = case_results[spec.matrix_id]
        if not result.arrays:
            continue
        times = result.arrays["times"]
        chi_s = result.arrays["chi_survival"]
        chi_g = result.arrays["chi_click_density"]
        chi_p = result.arrays["chi_panel_probability"]
        source_activity = result.arrays["source_activity_total"]
        source_trace = result.arrays["source_trace_total"]
        for node, time_value in enumerate(times):
            panel_exists = node < chi_g.size
            rows.append(
                {
                    "matrix_id": spec.matrix_id,
                    "status": result.status,
                    "direction": spec.environment_direction,
                    "role": spec.role,
                    "node_index": node,
                    "time": float(time_value),
                    "chi_survival": float(chi_s[node]),
                    "source_activity_total": float(source_activity[node]),
                    "source_trace_total": float(source_trace[node]),
                    "panel_index": node if panel_exists else None,
                    "panel_left_time": float(time_value) if panel_exists else None,
                    "panel_right_time": (
                        float(times[node + 1]) if panel_exists else None
                    ),
                    "chi_panel_probability": (
                        float(chi_p[node]) if panel_exists else None
                    ),
                    "chi_click_density": (
                        float(chi_g[node]) if panel_exists else None
                    ),
                }
            )
    return rows


def prompt_late_rows(case_results: Mapping[str, CaseAuditResult]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for spec in FROZEN_MATRIX:
        result = case_results[spec.matrix_id]
        integrated = result.metrics.get("raw", {}).get("integrated_response", {})
        rows.append(
            {
                "matrix_id": spec.matrix_id,
                "direction": spec.environment_direction,
                "role": spec.role,
                "status": result.status,
                "chi_D_E": integrated.get("chi_D_E"),
                "chi_D_L": integrated.get("chi_D_L"),
                "chi_D": integrated.get("chi_D_from_panel_sum"),
                "late_fraction_of_net_response": (
                    None
                    if finite_float(integrated.get("chi_D_from_panel_sum")) in {None, 0.0}
                    else float(integrated["chi_D_L"])
                    / float(integrated["chi_D_from_panel_sum"])
                ),
                "t_cut": result.configuration.get("t_cut", T_CUT_DEFAULT),
            }
        )
    return rows


def family_comparison_csv_rows(records: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for record in records:
        metrics = record.get("metrics", {})
        rows.append(
            {
                "direction": record.get("direction"),
                "comparison_type": record.get("comparison_type"),
                "baseline": record.get("baseline"),
                "control": record.get("control"),
                "available": record.get("available"),
                "scientific_gate_evaluable": record.get(
                    "scientific_gate_evaluable"
                ),
                "passed": record.get("passed"),
                **(metrics if isinstance(metrics, Mapping) else {}),
            }
        )
    return rows


def build_compact_npz_arrays(
    case_results: Mapping[str, CaseAuditResult],
    family_audits: Mapping[str, Any],
    upward_audits: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> Dict[str, np.ndarray]:
    case_ids = np.asarray([spec.matrix_id for spec in FROZEN_MATRIX], dtype="U2")
    statuses = np.asarray(
        [case_results[spec.matrix_id].status for spec in FROZEN_MATRIX], dtype="U16"
    )
    times = np.arange(101, dtype=np.float64) * EXPECTED_INSERTION_DT
    chi_s = np.full((15, 101), np.nan, dtype=np.float64)
    chi_g = np.full((15, 100), np.nan, dtype=np.float64)
    chi_p = np.full((15, 100), np.nan, dtype=np.float64)
    available = np.zeros(15, dtype=np.bool_)
    admissible = np.zeros(15, dtype=np.bool_)
    closed = np.zeros(15, dtype=np.bool_)
    response_norm = np.full(15, np.nan, dtype=np.float64)
    scalar_kernel_max = np.full(15, np.nan, dtype=np.float64)
    prompt = np.full(15, np.nan, dtype=np.float64)
    late = np.full(15, np.nan, dtype=np.float64)
    for index, spec in enumerate(FROZEN_MATRIX):
        result = case_results[spec.matrix_id]
        admissible[index] = result.scientific_admissible
        closed[index] = result.reproducibility_closed
        raw = result.metrics.get("raw", {})
        integrated = raw.get("integrated_response", {})
        if result.arrays:
            available[index] = True
            if result.arrays["times"].shape == times.shape:
                times = result.arrays["times"].copy()
            chi_s[index] = result.arrays["chi_survival"]
            chi_g[index] = result.arrays["chi_click_density"]
            chi_p[index] = result.arrays["chi_panel_probability"]
        value = finite_float(integrated.get("chi_complete_signed_measure_norm"))
        if value is not None:
            response_norm[index] = value
        value = finite_float(raw.get("maximum_abs_scalar_pointwise_click_kernel"))
        if value is not None:
            scalar_kernel_max[index] = value
        value = finite_float(integrated.get("chi_D_E"))
        if value is not None:
            prompt[index] = value
        value = finite_float(integrated.get("chi_D_L"))
        if value is not None:
            late[index] = value

    directions = ("downward", "upward", "dephasing")
    dt_distance = np.full(3, np.nan, dtype=np.float64)
    shell_distance = np.full(3, np.nan, dtype=np.float64)
    confinement_distance = np.full(3, np.nan, dtype=np.float64)
    evidence_ratio = np.full(3, np.nan, dtype=np.float64)
    evidence_class = np.empty(3, dtype="U24")
    for index, direction in enumerate(directions):
        family = family_audits["families"][direction]
        for target, record_name in (
            (dt_distance, "time_step_convergence"),
            (shell_distance, "shell_convergence"),
            (confinement_distance, "confinement_comparison"),
        ):
            value = finite_float(
                nested_get(
                    family,
                    f"{record_name}.metrics.complete_signed_measure_distance",
                )
            )
            if value is not None:
                target[index] = value
        evidence_record = evidence.get("by_direction", {}).get(direction, {})
        ratio = finite_float(evidence_record.get("signal_to_uncertainty_ratio"))
        if ratio is not None:
            evidence_ratio[index] = ratio
        evidence_class[index] = str(
            evidence_record.get("classification", EVIDENCE_BUDGET_INCOMPLETE)
        )

    upward_actual = np.full((3, 100), np.nan, dtype=np.float64)
    upward_expected = np.full((3, 100), np.nan, dtype=np.float64)
    upward_available = np.zeros(3, dtype=np.bool_)
    for index, matrix_id in enumerate(("U1", "U2", "U3")):
        record = upward_audits.get(matrix_id, {})
        if record.get("independently_reconstructed") is True:
            upward_available[index] = True
            upward_actual[index] = np.asarray(record["actual_kernel_column"])
            upward_expected[index] = np.asarray(record["expected_kernel_column"])

    return {
        "matrix_ids": case_ids,
        "case_statuses": statuses,
        "response_times": times,
        "case_available_mask": available,
        "case_scientifically_admissible_mask": admissible,
        "case_rerun_closed_mask": closed,
        "chi_survival": chi_s,
        "chi_click_density": chi_g,
        "chi_panel_probability": chi_p,
        "complete_signed_measure_norm": response_norm,
        "scalar_pointwise_kernel_max": scalar_kernel_max,
        "chi_D_E": prompt,
        "chi_D_L": late,
        "family_directions": np.asarray(directions, dtype="U10"),
        "time_step_complete_measure_distance": dt_distance,
        "shell_complete_measure_distance": shell_distance,
        "confinement_complete_measure_distance": confinement_distance,
        "evidence_ratio": evidence_ratio,
        "evidence_classification": evidence_class,
        "upward_launch_matrix_ids": np.asarray(("U1", "U2", "U3"), dtype="U2"),
        "upward_launch_identity_available_mask": upward_available,
        "upward_launch_actual_kernel_column": upward_actual,
        "upward_launch_expected_kernel_column": upward_expected,
        "missing_values_are_NaN_with_explicit_masks": np.asarray([True], dtype=np.bool_),
    }


# =============================================================================
# MARKDOWN REPORT AND VERIFIED SHARE PACKAGES
# =============================================================================
def _format_value(value: Any) -> str:
    numeric = finite_float(value)
    if numeric is not None:
        return f"{numeric:.8e}"
    if value is None:
        return "—"
    return str(value)


def render_aggregate_report(
    overall: Mapping[str, Any],
    case_results: Mapping[str, CaseAuditResult],
    family_audits: Mapping[str, Any],
    upward_audits: Mapping[str, Any],
    uncertainty: Mapping[str, Any],
    evidence: Mapping[str, Any],
    reproducibility: Mapping[str, Any],
    authority_audit: Mapping[str, Any],
    discovery_inventory: Optional[Mapping[str, Any]] = None,
    task05_candidate_count: int = 0,
) -> str:
    discovery_inventory = discovery_inventory or {}

    def scientific_label(result: CaseAuditResult) -> str:
        if result.status == STATUS_FAILED:
            return "FAIL"
        if result.status == STATUS_MISSING:
            return "PENDING"
        if result.status == STATUS_LOCAL_PASS:
            return "LOCAL ONLY"
        return "PASS" if result.scientific_admissible else "PENDING"

    def gate_label(*, available: bool, passed: bool, evaluable: bool = True) -> str:
        if not available or not evaluable:
            return "PENDING"
        return "PASS" if passed else "FAIL"

    status_counts = {
        status: sum(result.status == status for result in case_results.values())
        for status in ALLOWED_CASE_STATUSES
    }
    available_results = [
        case_results[spec.matrix_id]
        for spec in FROZEN_MATRIX
        if case_results[spec.matrix_id].arrays
    ]
    candidate_categories = discovery_inventory.get("Task07_candidate_categories", {})
    mixed_core = (
        candidate_categories.get("mapped_legacy_or_mixed_core", [])
        if isinstance(candidate_categories, Mapping)
        else []
    )
    inspected_paths = discovery_inventory.get("inspected_paths", [])

    lines: List[str] = []
    lines.extend(
        [
            "# Task-08 Independent Aggregate Response Audit",
            "",
            f"**Loader version:** `{LOADER_VERSION}`  ",
            f"**Generated:** `{utc_now_iso()}`  ",
            f"**Scientific verdict:** **{overall['scientific_verdict']}**  ",
            "**Task-08 finite-v8 zero-rate response gate authorized:** "
            + ("**YES**" if overall["physical_zero_rate_susceptibility_claim_authorized"] else "**NO**"),
            "**Publication-level project closure under the attached master audit:** **NO — upstream Task-05/06 closure remains pending**",
            "",
            "## What this run means",
            "",
        ]
    )
    if overall.get("scientific_verdict") == "INCOMPLETE_REQUIRED_CASE_MATRIX":
        lines.append(
            "This is a valid **incremental** Task-08 result. Available cases were audited; "
            "unavailable matrix roles remain `MISSING/PENDING` and are not treated as numerical failures. "
            "Exit code 3 means the aggregate family is incomplete, not that the loader crashed."
        )
    elif overall.get("scientific_verdict", "").startswith("FAIL_"):
        lines.append(
            "At least one completed input failed an integrity or numerical gate. The failed case/check "
            "names below distinguish this from ordinary missing-data incompleteness."
        )
    else:
        lines.append(
            "All mandatory available-data, family, uncertainty, and representative-rerun gates were evaluated "
            "under the stated zero-rate finite-v8 scope."
        )

    lines.extend(
        [
            "",
            "## Discovery and incremental coverage",
            "",
            f"- Task-07 candidate records discovered: `{discovery_inventory.get('candidate_count', 0)}`",
            f"- Task-05 candidate records discovered: `{task05_candidate_count}`",
            f"- Scientifically admissible cases: `{sum(result.scientific_admissible for result in case_results.values())}/15`",
            f"- Deterministic reruns closed: `{sum(result.reproducibility_closed for result in case_results.values())}/15`",
            "- Status counts: " + ", ".join(f"`{key}={value}`" for key, value in status_counts.items()),
        ]
    )
    if inspected_paths:
        lines.extend(["", "**Inspected input roots**", ""])
        for record in inspected_paths:
            if isinstance(record, Mapping):
                lines.append(
                    f"- `{record.get('path')}` — exists={record.get('exists')}, "
                    f"candidates={record.get('candidate_count', 0)}"
                )
    if mixed_core:
        lines.extend(
            [
                "",
                f"**Mixed/legacy-core candidates isolated:** `{len(mixed_core)}`",
                "",
                f"Expected numerical-core SHA-256: `{FROZEN_TASK07_V8_NUMERICAL_CORE_SHA256}`. "
                "These candidates remain diagnostic inventory and do not fill formal D/U/P roles.",
            ]
        )
        for origin in mixed_core[:20]:
            lines.append(f"- `{origin}`")

    lines.extend(
        [
            "",
            "## Authority contract",
            "",
            "The numerical master audit has precedence over historical defaults. "
            "The final Task-07→08 handoff fixes the corrected v8 raw-data contract, "
            "15-case matrix, rerun policy, family gates, uncertainty budget, and "
            "output schema. Task 08 is read-only and reconstructs numerical statements "
            "without importing or executing Task 07 or its per-case loader.",
            "",
            f"- Frozen Task-07 numerical-core SHA-256: `{FROZEN_TASK07_V8_NUMERICAL_CORE_SHA256}`",
            f"- Frozen Task-07 per-case-loader SHA-256: `{FROZEN_TASK07_CASE_LOADER_SHA256}`",
            f"- Explicit authority-file verification: `{authority_audit.get('passed')}`",
            "",
            "## Frozen case matrix",
            "",
            "| ID | Role | Detector | Direction | ω | N | Δt | Status | Scientific | Rerun |",
            "|---|---|---|---|---:|---:|---:|---|---|---|",
        ]
    )
    for spec in FROZEN_MATRIX:
        result = case_results[spec.matrix_id]
        lines.append(
            f"| {spec.matrix_id} | {spec.role} | {spec.propagator_type} | "
            f"{spec.environment_direction} | {spec.omega:g} | {spec.n_shell} | "
            f"{spec.dt:.4g} | {result.status} | {scientific_label(result)} | "
            f"{'CLOSED' if result.reproducibility_closed else 'PENDING'} |"
        )

    lines.extend(["", "## Available-case response metrics", ""])
    if not available_results:
        lines.append("No complete raw Task-07 response case was available in this run.")
    else:
        lines.extend(
            [
                "| ID | Status | χD | χμ | χD,E | χD,L | Complete norm | Tangent closure | Insertion dTV |",
                "|---|---|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for result in available_results:
            raw = result.metrics.get("raw", {})
            integrated = raw.get("integrated_response", {})
            insertion = raw.get("insertion_comparison", {})
            lines.append(
                f"| {result.matrix_id} | {result.status} | "
                f"{_format_value(integrated.get('chi_D_from_final_survival'))} | "
                f"{_format_value(integrated.get('chi_mu_restricted'))} | "
                f"{_format_value(integrated.get('chi_D_E'))} | "
                f"{_format_value(integrated.get('chi_D_L'))} | "
                f"{_format_value(integrated.get('chi_complete_signed_measure_norm'))} | "
                f"{_format_value(raw.get('maximum_tangent_probability_closure_residual'))} | "
                f"{_format_value(insertion.get('signed_measure_distance'))} |"
            )

    lines.extend(["", "## Scalar pointwise nulls", ""])
    lines.extend(
        [
            "| Direction | Case | Pointwise kernel max | Response max | Pointwise gate | Integrated gate |",
            "|---|---|---:|---:|---|---|",
        ]
    )
    for direction in ("downward", "upward", "dephasing"):
        scalar = family_audits["families"][direction]["scalar_null"]
        available = bool(scalar.get("available"))
        lines.append(
            f"| {direction} | {scalar['matrix_id']} | "
            f"{_format_value(scalar['pointwise_click_kernel_max'])} | "
            f"{_format_value(scalar['response_component_max'])} | "
            f"{gate_label(available=available, passed=bool(scalar['pointwise_pass']))} | "
            f"{gate_label(available=available, passed=bool(scalar['integrated_pass']))} |"
        )

    lines.extend(["", "## Time-step and shell convergence", ""])
    lines.extend(
        [
            "| Direction | dTV(dt,dt/2) | Relative | Gate | dTV(N12,N16) | Relative | Gate |",
            "|---|---:|---:|---|---:|---:|---|",
        ]
    )
    for direction in ("downward", "upward", "dephasing"):
        family = family_audits["families"][direction]
        time_record = family["time_step_convergence"]
        shell_record = family["shell_convergence"]
        lines.append(
            f"| {direction} | "
            f"{_format_value(nested_get(time_record, 'metrics.complete_signed_measure_distance'))} | "
            f"{_format_value(nested_get(time_record, 'metrics.relative_signed_measure_distance'))} | "
            f"{gate_label(available=bool(time_record.get('available')), passed=bool(time_record.get('passed')), evaluable=bool(time_record.get('scientific_gate_evaluable')))} | "
            f"{_format_value(nested_get(shell_record, 'metrics.complete_signed_measure_distance'))} | "
            f"{_format_value(nested_get(shell_record, 'metrics.relative_signed_measure_distance'))} | "
            f"{gate_label(available=bool(shell_record.get('available')), passed=bool(shell_record.get('passed')), evaluable=bool(shell_record.get('scientific_gate_evaluable')))} |"
        )

    lines.extend(["", "## Upward launch identity", ""])
    lines.extend(
        [
            "| Case | Independent Task-05 raw inputs | Max absolute difference | Relative difference | Status |",
            "|---|---|---:|---:|---|",
        ]
    )
    for matrix_id in ("U1", "U2", "U3"):
        record = upward_audits.get(matrix_id, {})
        lines.append(
            f"| {matrix_id} | "
            f"{'YES' if record.get('independently_reconstructed') else 'NO'} | "
            f"{_format_value(record.get('maximum_absolute_difference'))} | "
            f"{_format_value(record.get('relative_difference'))} | "
            f"{record.get('status', 'UNAVAILABLE')} |"
        )

    lines.extend(["", "## Uncertainty and evidence", ""])
    lines.extend(
        [
            "| Direction | Response norm | ε_total | Ratio | Classification | Missing components |",
            "|---|---:|---:|---:|---|---|",
        ]
    )
    for direction in ("downward", "upward", "dephasing"):
        budget = uncertainty.get("by_direction", {}).get(direction, {})
        classification = evidence.get("by_direction", {}).get(direction, {})
        lines.append(
            f"| {direction} | {_format_value(classification.get('response_norm'))} | "
            f"{_format_value(budget.get('epsilon_total_zero_rate'))} | "
            f"{_format_value(classification.get('signal_to_uncertainty_ratio'))} | "
            f"{classification.get('classification', EVIDENCE_BUDGET_INCOMPLETE)} | "
            f"{', '.join(budget.get('missing_required_components', [])) or 'none'} |"
        )

    lines.extend(
        [
            "",
            "## Reproducibility coverage",
            "",
            f"- Representative D3 deterministic certification: `{reproducibility['representative_deterministic_certification_pass']}`",
            f"- Per-case rerun coverage: `{reproducibility['per_case_rerun_coverage_count']}/15`",
            f"- Coverage status: `{reproducibility['coverage_status']}`",
            "",
            "## Claim boundary",
            "",
        ]
    )
    if overall["physical_zero_rate_susceptibility_claim_authorized"]:
        lines.append(
            "The mandatory Task-08 gates authorize interpretation of the independently "
            "reconstructed **zero-rate finite-v8 linear response**. Under the attached "
            "highest-authority master audit, publication-level project closure remains "
            "provisional until the residual Task-05/06 closure items are recorded in an "
            "updated master audit. This result does not authorize a finite-rate, thermal, "
            "trajectory, microscopic-detector, or continuum-semigroup claim."
        )
    else:
        lines.append(
            "No physical detector–bath susceptibility claim is authorized. Missing roles are "
            "reported as pending; completed inputs that failed an actual gate are listed separately."
        )
    lines.extend(
        [
            "",
            "## Outstanding items",
            "",
            f"- Missing cases: `{overall.get('missing_cases', [])}`",
            f"- Failed cases: `{overall.get('failed_cases', [])}`",
            f"- Scientifically inadmissible cases: `{overall.get('scientifically_inadmissible_cases', [])}`",
            f"- Unresolved evidence directions: `{overall.get('unresolved_evidence_directions', [])}`",
            f"- Missing independent Task-05 upward inputs: `{overall.get('upward_identity_missing_Task05_raw_cases', [])}`",
            "",
            "## Principal output products",
            "",
            "- `Task08_case_identity_table.csv` — complete D1–D5/U1–U5/P1–P5 register",
            "- `Task08_per_case_metrics.csv` — per-case response and closure metrics",
            "- `Task08_complete_response_curves.csv` — available reconstructed curves",
            "- `Task08_uncertainty_budget.json` and `Task08_evidence_classification.json`",
            "- `Task08_share.zip` and `Task08_diagnostic_share.zip`",
            "",
        ]
    )
    return "\n".join(lines)

def create_verified_zip(zip_path: Path, files: Sequence[Path]) -> Dict[str, Any]:
    unique: Dict[str, Path] = {}
    for path in files:
        resolved = path.resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"Cannot package missing output: {resolved}")
        if resolved.name in unique and unique[resolved.name] != resolved:
            raise ValueError(f"Duplicate output basename for ZIP: {resolved.name}")
        unique[resolved.name] = resolved
    expected_hashes = {
        name: sha256_file(path) for name, path in sorted(unique.items())
    }
    tmp = zip_path.with_name(zip_path.name + ".tmp")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, path in sorted(unique.items()):
            info = zipfile.ZipInfo(name)
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    os.replace(tmp, zip_path)
    member_hashes: Dict[str, str] = {}
    with zipfile.ZipFile(zip_path, "r") as archive:
        names = archive.namelist()
        duplicates = sorted({name for name in names if names.count(name) > 1})
        for name in names:
            member_hashes[name] = sha256_bytes(archive.read(name))
    passed = bool(
        not duplicates
        and set(member_hashes) == set(expected_hashes)
        and all(member_hashes[name] == expected_hashes[name] for name in expected_hashes)
    )
    return {
        "path": str(zip_path),
        "sha256": sha256_file(zip_path),
        "member_count": len(expected_hashes),
        "duplicate_members": duplicates,
        "member_hashes_match_sources": passed,
    }


def task08_output_paths(output_dir: Path) -> Dict[str, Path]:
    return {
        "configuration": output_dir / "Task08_configuration.json",
        "input_inventory": output_dir / "Task08_input_inventory.json",
        "case_identity": output_dir / "Task08_case_identity_table.csv",
        "case_integrity": output_dir / "Task08_case_integrity_audit.json",
        "per_case_metrics": output_dir / "Task08_per_case_metrics.csv",
        "scalar_null": output_dir / "Task08_scalar_null_audit.json",
        "downward": output_dir / "Task08_downward_family_audit.json",
        "upward": output_dir / "Task08_upward_family_audit.json",
        "dephasing": output_dir / "Task08_dephasing_family_audit.json",
        "time_step": output_dir / "Task08_time_step_convergence.csv",
        "shell": output_dir / "Task08_shell_convergence.csv",
        "confinement": output_dir / "Task08_confinement_comparison.csv",
        "prompt_late": output_dir / "Task08_prompt_late_metrics.csv",
        "curves": output_dir / "Task08_complete_response_curves.csv",
        "uncertainty": output_dir / "Task08_uncertainty_budget.json",
        "evidence": output_dir / "Task08_evidence_classification.json",
        "reproducibility": output_dir / "Task08_reproducibility_coverage.json",
        "channel_superposition": output_dir / "Task08_channel_superposition_audit.json",
        "report": output_dir / "Task08_aggregate_report.md",
        "compact": output_dir / "Task08_compact_results.npz",
        "hashes": output_dir / "Task08_output_hashes.json",
        "status": output_dir / "Task08_run_status.json",
        "source": output_dir / "Task08_loader.py",
        "share_zip": output_dir / "Task08_share.zip",
        "diagnostic_zip": output_dir / "Task08_diagnostic_share.zip",
        "failure": output_dir / "Task08_failure.json",
    }


def _upward_json_summary(record: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        key: value
        for key, value in record.items()
        if key
        not in {
            "Task05_panel_probabilities",
            "expected_kernel_column",
            "actual_kernel_column",
        }
    }


def write_task08_outputs(
    *,
    options: Task08Options,
    loader_source: Path,
    loader_self_audit: Mapping[str, Any],
    authority_audit: Mapping[str, Any],
    discovery_inventory: Mapping[str, Any],
    candidate_records: Sequence[CandidateRecord],
    task05_candidates: Sequence[Task05Candidate],
    selection_audit: Mapping[str, Any],
    case_results: Mapping[str, CaseAuditResult],
    upward_audits: Mapping[str, Any],
    family_audits: Mapping[str, Any],
    inherited_bounds: Mapping[str, Any],
    uncertainty: Mapping[str, Any],
    evidence: Mapping[str, Any],
    reproducibility: Mapping[str, Any],
    channel_superposition: Mapping[str, Any],
    overall: Mapping[str, Any],
) -> Dict[str, Any]:
    output_dir = options.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = task08_output_paths(output_dir)
    loader_hash = sha256_file(loader_source)
    shutil.copy2(loader_source, paths["source"])
    copied_loader_hash = sha256_file(paths["source"])

    thresholds = {
        "operator": OPERATOR_TOL,
        "array_reconstruction": ARRAY_ABS_TOL,
        "Task05_reference_array": TASK05_REFERENCE_ARRAY_ABS_TOL,
        "Task05_source_curve": TASK05_SOURCE_CURVE_ABS_TOL,
        "source_trace": SOURCE_TRACE_ABS_TOL,
        "launch_source": LAUNCH_SOURCE_ABS_TOL,
        "closure_pilot": CLOSURE_PILOT_ABS_TOL,
        "tangent_closure_absolute": TANGENT_CLOSURE_ABS_TOL,
        "tangent_closure_relative": TANGENT_CLOSURE_REL_TOL,
        "kernel_closure": KERNEL_CLOSURE_ABS_TOL,
        "scalar_pointwise": SCALAR_KERNEL_ABS_TOL,
        "scalar_integrated": SCALAR_RESPONSE_ABS_TOL,
        "benchmark_absolute": BENCHMARK_ABS_TOL,
        "benchmark_relative": BENCHMARK_REL_TOL,
        "insertion_absolute": INSERTION_CONVERGENCE_ABS_TOL,
        "insertion_relative": INSERTION_CONVERGENCE_REL_TOL,
        "time_shell_absolute": FAMILY_RESPONSE_ABS_TOL,
        "time_shell_relative": FAMILY_RESPONSE_REL_TOL,
        "upward_launch_absolute": UPWARD_STATIC_KERNEL_ABS_TOL,
        "upward_launch_relative": UPWARD_STATIC_KERNEL_REL_TOL,
        "true_residual": TRUE_RESIDUAL_TOL,
        "evidence_factor": EVIDENCE_FACTOR,
    }
    task08_configuration = {
        "stage": STAGE_NAME,
        "loader_version": LOADER_VERSION,
        "created_utc": utc_now_iso(),
        "read_only_input_policy": True,
        "CPU_only": True,
        "Jupyter_safe": True,
        "imports_or_executes_Task07": False,
        "imports_or_executes_Task07_per_case_loader": False,
        "trusts_saved_PASS_flags_as_evidence": False,
        "partial_incremental_dataset_supported": True,
        "strict_reruns": options.strict_reruns,
        "allow_missing_per_case_loader": options.allow_missing_per_case_loader,
        "synthetic_mode": options.synthetic_mode,
        "input_paths": [str(path) for path in options.input_paths],
        "Task05_input_paths": [str(path) for path in options.task05_input_paths],
        "inherited_bounds_path": (
            str(options.inherited_bounds_path) if options.inherited_bounds_path else None
        ),
        "output_directory": str(output_dir),
        "loader_source_sha256": loader_hash,
        "copied_loader_source_sha256": copied_loader_hash,
        "frozen_Task07_v8_numerical_core_sha256": options.expected_numerical_core_sha256,
        "frozen_Task07_per_case_loader_sha256": FROZEN_TASK07_CASE_LOADER_SHA256,
        "expected_Task07_script_version": EXPECTED_TASK07_SCRIPT_VERSION,
        "authority_audit": authority_audit,
        "loader_self_scope_audit": loader_self_audit,
        "frozen_15_case_matrix": [asdict(spec) for spec in FROZEN_MATRIX],
        "case_status_vocabulary": list(ALLOWED_CASE_STATUSES),
        "scientific_and_rerun_status_are_orthogonal": True,
        "attached_master_Task05_06_status": ATTACHED_MASTER_TASK05_06_STATUS,
        "attached_master_publication_level_status": (
            ATTACHED_MASTER_PUBLICATION_LEVEL_STATUS
        ),
        "Task08_finite_model_verdict_is_separate_from_publication_level_project_closure": True,
        "thresholds": thresholds,
        "output_contract": list(TASK08_OUTPUT_FILENAMES),
    }
    atomic_write_derived_json(paths["configuration"], task08_configuration)

    task05_inventory = [
        {
            **candidate.package.describe(),
            "configuration_name": candidate.configuration_name,
            "prefix": candidate.prefix,
            "configuration": candidate.configuration,
            "fingerprint": candidate.fingerprint,
            "integrity_passed": candidate.integrity_passed,
            "integrity_metrics": candidate.integrity_metrics,
        }
        for candidate in task05_candidates
    ]
    task07_candidate_categories = {
        "mapped_frozen_v8": [
            record.package.origin
            for record in candidate_records
            if record.matrix_id in SPEC_BY_ID
            and str(record.configuration.get("numerical_core_sha256", ""))
            == options.expected_numerical_core_sha256
        ],
        "mapped_legacy_or_mixed_core": [
            record.package.origin
            for record in candidate_records
            if record.matrix_id in SPEC_BY_ID
            and str(record.configuration.get("numerical_core_sha256", ""))
            != options.expected_numerical_core_sha256
        ],
        "unmapped_configuration": [
            record.package.origin
            for record in candidate_records
            if record.matrix_id not in SPEC_BY_ID
        ],
        "discovery_errors": [
            {
                "origin": record.package.origin,
                "errors": list(record.discovery_errors),
            }
            for record in candidate_records
            if record.discovery_errors
        ],
        "incomplete_candidates": [
            {
                "origin": record.package.origin,
                "matrix_id": record.matrix_id,
                "required_file_count": record.required_file_count,
                "expected_required_file_count": len(
                    required_solver_suffixes(record.configuration)
                ),
            }
            for record in candidate_records
            if record.required_file_count
            < len(required_solver_suffixes(record.configuration))
        ],
    }
    inventory_payload = {
        **dict(discovery_inventory),
        "Task07_candidate_categories": task07_candidate_categories,
        "Task05_candidate_count": len(task05_candidates),
        "Task05_candidates": task05_inventory,
        "selection_audit": selection_audit,
    }
    atomic_write_derived_json(paths["input_inventory"], inventory_payload)
    atomic_write_csv(paths["case_identity"], case_identity_rows(case_results))

    case_integrity_payload = {
        "overall": dict(overall),
        "status_counts": {
            status: sum(
                result.status == status for result in case_results.values()
            )
            for status in ALLOWED_CASE_STATUSES
        },
        "cases": {
            matrix_id: case_result_json(result)
            for matrix_id, result in case_results.items()
        },
    }
    atomic_write_derived_json(paths["case_integrity"], case_integrity_payload)
    atomic_write_csv(paths["per_case_metrics"], per_case_metric_rows(case_results))

    scalar_payload = {
        "thresholds": {
            "pointwise_click_kernel": SCALAR_KERNEL_ABS_TOL,
            "survival_and_integrated_response": SCALAR_RESPONSE_ABS_TOL,
        },
        "D1": family_audits["families"]["downward"]["scalar_null"],
        "U1": family_audits["families"]["upward"]["scalar_null"],
        "P1": family_audits["families"]["dephasing"]["scalar_null"],
        "U1_is_mandatory_nontrivial_null": True,
    }
    atomic_write_derived_json(paths["scalar_null"], scalar_payload)

    for direction, path_key in (
        ("downward", "downward"),
        ("upward", "upward"),
        ("dephasing", "dephasing"),
    ):
        payload = {
            "family": family_audits["families"][direction],
            "uncertainty_budget": uncertainty.get("by_direction", {}).get(
                direction, {}
            ),
            "evidence_classification": evidence.get("by_direction", {}).get(
                direction, {}
            ),
        }
        if direction == "upward":
            payload["independent_upward_launch_identities"] = {
                matrix_id: _upward_json_summary(record)
                for matrix_id, record in upward_audits.items()
            }
        atomic_write_derived_json(paths[path_key], payload)

    atomic_write_csv(
        paths["time_step"],
        family_comparison_csv_rows(family_audits["time_step_rows"]),
    )
    atomic_write_csv(
        paths["shell"],
        family_comparison_csv_rows(family_audits["shell_rows"]),
    )
    atomic_write_csv(
        paths["confinement"],
        family_comparison_csv_rows(family_audits["confinement_rows"]),
    )
    atomic_write_csv(paths["prompt_late"], prompt_late_rows(case_results))
    atomic_write_csv(paths["curves"], complete_response_curve_rows(case_results))
    atomic_write_derived_json(
        paths["uncertainty"],
        {
            **dict(uncertainty),
            "inherited_bounds": dict(inherited_bounds),
            "unknown_inherited_terms_are_never_silently_zero": True,
        },
    )
    atomic_write_derived_json(paths["evidence"], evidence)
    atomic_write_derived_json(paths["reproducibility"], reproducibility)
    atomic_write_derived_json(paths["channel_superposition"], channel_superposition)

    report = render_aggregate_report(
        overall,
        case_results,
        family_audits,
        upward_audits,
        uncertainty,
        evidence,
        reproducibility,
        authority_audit,
        discovery_inventory=inventory_payload,
        task05_candidate_count=len(task05_candidates),
    )
    atomic_write_text(paths["report"], report)
    compact_arrays = build_compact_npz_arrays(
        case_results, family_audits, upward_audits, evidence
    )
    atomic_savez(paths["compact"], compressed=True, **compact_arrays)

    stable_keys = (
        "configuration",
        "input_inventory",
        "case_identity",
        "case_integrity",
        "per_case_metrics",
        "scalar_null",
        "downward",
        "upward",
        "dephasing",
        "time_step",
        "shell",
        "confinement",
        "prompt_late",
        "curves",
        "uncertainty",
        "evidence",
        "reproducibility",
        "channel_superposition",
        "report",
        "compact",
        "source",
    )
    stable_files = [paths[key] for key in stable_keys]
    manifest = {
        "hash_algorithm": "SHA-256",
        "stage": STAGE_NAME,
        "loader_version": LOADER_VERSION,
        "loader_source_sha256": loader_hash,
        "copied_loader_source_sha256": copied_loader_hash,
        "scientific_verdict": overall["scientific_verdict"],
        "physical_claim_authorized": overall[
            "physical_zero_rate_susceptibility_claim_authorized"
        ],
        "files": {path.name: sha256_file(path) for path in stable_files},
        "nondeterministic_or_self_referential_outputs_excluded": [
            paths["hashes"].name,
            paths["status"].name,
            paths["share_zip"].name,
            paths["diagnostic_zip"].name,
        ],
    }
    atomic_write_json(paths["hashes"], manifest)

    full_zip = create_verified_zip(
        paths["share_zip"], stable_files + [paths["hashes"]]
    )
    diagnostic_keys = (
        "configuration",
        "input_inventory",
        "case_identity",
        "case_integrity",
        "per_case_metrics",
        "scalar_null",
        "downward",
        "upward",
        "dephasing",
        "time_step",
        "shell",
        "confinement",
        "uncertainty",
        "evidence",
        "reproducibility",
        "channel_superposition",
        "report",
        "source",
    )
    diagnostic_zip = create_verified_zip(
        paths["diagnostic_zip"],
        [paths[key] for key in diagnostic_keys] + [paths["hashes"]],
    )
    if not (
        full_zip["member_hashes_match_sources"]
        and diagnostic_zip["member_hashes_match_sources"]
    ):
        raise RuntimeError("Task-08 share ZIP verification failed")

    run_status = {
        "stage": STAGE_NAME,
        "loader_version": LOADER_VERSION,
        "status": (
            "completed_pass"
            if int(overall["exit_code"]) == 0
            else "completed_incomplete"
            if int(overall["exit_code"]) == 3
            else "completed_fail"
        ),
        "completed_utc": utc_now_iso(),
        **dict(overall),
        "output_hash_manifest": paths["hashes"].name,
        "output_hash_manifest_sha256": sha256_file(paths["hashes"]),
        "share_zip": full_zip,
        "diagnostic_share_zip": diagnostic_zip,
        "output_directory": str(output_dir),
    }
    atomic_write_derived_json(paths["status"], run_status)
    return {
        "paths": {key: str(value) for key, value in paths.items()},
        "loader_source_sha256": loader_hash,
        "copied_loader_source_sha256": copied_loader_hash,
        "share_zip": full_zip,
        "diagnostic_share_zip": diagnostic_zip,
        "run_status": run_status,
    }


# =============================================================================
# TASK-08 ORCHESTRATION API
# =============================================================================
def _path_tuple(values: Optional[Sequence[Union[str, os.PathLike[str]]]]) -> Tuple[Path, ...]:
    if not values:
        return ()
    return tuple(Path(value).expanduser() for value in values)


def _default_authority_path(
    explicit: Optional[Union[str, os.PathLike[str]]],
    filenames: Sequence[str],
    loader_source: Path,
) -> Optional[Path]:
    if explicit is not None:
        return Path(explicit).expanduser()
    search_roots = (
        loader_source.parent,
        Path.cwd(),
        Path("[ARCHIVE_PATH]"),
    )
    for root in search_roots:
        for filename in filenames:
            candidate = root / filename
            if candidate.is_file():
                return candidate
    return None


def run_task08(
    *,
    input_paths: Sequence[Union[str, os.PathLike[str]]],
    output_dir: Union[str, os.PathLike[str]],
    task05_input_paths: Optional[Sequence[Union[str, os.PathLike[str]]]] = None,
    inherited_bounds_path: Optional[Union[str, os.PathLike[str]]] = None,
    master_audit_path: Optional[Union[str, os.PathLike[str]]] = None,
    handoff_path: Optional[Union[str, os.PathLike[str]]] = None,
    strict_reruns: bool = False,
    allow_missing_per_case_loader: bool = False,
    max_zip_member_bytes: int = 2 * 1024 * 1024 * 1024,
    synthetic_mode: bool = False,
    expected_numerical_core_sha256: str = FROZEN_TASK07_V8_NUMERICAL_CORE_SHA256,
) -> Tuple[int, Dict[str, Any]]:
    """Run the independent aggregate audit and return ``(exit_code, summary)``.

    No input file is opened for writing. All products are confined to
    ``output_dir``. Missing cases remain explicit MISSING rows.
    """
    output_path = Path(output_dir).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    loader_source = resolve_loader_source_path(output_path)
    master_path = _default_authority_path(
        master_audit_path,
        (
            "NUM_Open_System_PartI_Master_Audit_Audit00_to_Task06_Qualified_PASS_and_Task07_Handoff_2026-08-03(8).md",
            "NUM_Open_System_PartI_Master_Audit_Audit00_to_Task06_Qualified_PASS_and_Task07_Handoff_2026-08-03.md",
        ),
        loader_source,
    )
    handoff_resolved = _default_authority_path(
        handoff_path,
        (
            "NUM_Task07_Final_Production_and_Task08_Independent_Aggregate_Loader_Handoff_2026-08-06(1).md",
            "NUM_Task07_Final_Production_and_Task08_Independent_Aggregate_Loader_Handoff_2026-08-06.md",
        ),
        loader_source,
    )
    options = Task08Options(
        input_paths=_path_tuple(input_paths),
        output_dir=output_path,
        task05_input_paths=_path_tuple(task05_input_paths),
        inherited_bounds_path=(
            Path(inherited_bounds_path).expanduser()
            if inherited_bounds_path is not None
            else None
        ),
        master_audit_path=master_path,
        handoff_path=handoff_resolved,
        strict_reruns=bool(strict_reruns),
        allow_missing_per_case_loader=bool(allow_missing_per_case_loader),
        max_zip_member_bytes=int(max_zip_member_bytes),
        synthetic_mode=bool(synthetic_mode),
        expected_numerical_core_sha256=str(expected_numerical_core_sha256),
    )
    if not options.input_paths:
        raise ValueError("At least one Task-07 input path is required")
    if options.max_zip_member_bytes <= 0:
        raise ValueError("max_zip_member_bytes must be positive")

    output_path.mkdir(parents=True, exist_ok=True)
    try:
        loader_self_audit = loader_self_scope_audit(loader_source)
        authority_audit = audit_authority_files(options)
        records, discovery_inventory = discover_candidates(options)
        case_results, selection_audit = audit_all_cases(records, options)
        task05_candidates = discover_task05_candidates(options)
        upward_audits = audit_upward_launch_identities(
            case_results, task05_candidates
        )
        family_audits = build_family_audits(case_results)
        inherited_bounds = load_inherited_bounds(options.inherited_bounds_path)
        uncertainty, evidence = build_uncertainty_and_evidence(
            case_results, family_audits, inherited_bounds
        )
        reproducibility = build_reproducibility_coverage(case_results)
        channel_superposition = build_channel_superposition_audit(case_results)
        overall = build_overall_verdict(
            case_results,
            family_audits,
            upward_audits,
            uncertainty,
            evidence,
            channel_superposition,
            authority_audit_passed=bool(authority_audit["passed"]),
            self_scope_passed=bool(
                loader_self_audit[
                    "read_only_CPU_loader_without_Task07_import_or_execution"
                ]
            ),
        )
        outputs = write_task08_outputs(
            options=options,
            loader_source=loader_source,
            loader_self_audit=loader_self_audit,
            authority_audit=authority_audit,
            discovery_inventory=discovery_inventory,
            candidate_records=records,
            task05_candidates=task05_candidates,
            selection_audit=selection_audit,
            case_results=case_results,
            upward_audits=upward_audits,
            family_audits=family_audits,
            inherited_bounds=inherited_bounds,
            uncertainty=uncertainty,
            evidence=evidence,
            reproducibility=reproducibility,
            channel_superposition=channel_superposition,
            overall=overall,
        )
        status_counts = {
            status: sum(result.status == status for result in case_results.values())
            for status in ALLOWED_CASE_STATUSES
        }
        case_rows: List[Dict[str, Any]] = []
        for spec in FROZEN_MATRIX:
            result = case_results[spec.matrix_id]
            raw = result.metrics.get("raw", {})
            integrated = raw.get("integrated_response", {})
            insertion = raw.get("insertion_comparison", {})
            case_rows.append(
                {
                    "matrix_id": spec.matrix_id,
                    "role": spec.role,
                    "status": result.status,
                    "scientific_admissible": result.scientific_admissible,
                    "rerun_closed": result.reproducibility_closed,
                    "chi_D": integrated.get("chi_D_from_final_survival"),
                    "chi_mu": integrated.get("chi_mu_restricted"),
                    "chi_D_E": integrated.get("chi_D_E"),
                    "chi_D_L": integrated.get("chi_D_L"),
                    "complete_response_norm": integrated.get(
                        "chi_complete_signed_measure_norm"
                    ),
                    "tangent_closure": raw.get(
                        "maximum_tangent_probability_closure_residual"
                    ),
                    "insertion_signed_measure_distance": insertion.get(
                        "signed_measure_distance"
                    ),
                    "failed_checks": list(result.failed_checks),
                    "pending_items": list(result.pending_items),
                }
            )
        family_gate_summary: Dict[str, Any] = {}
        for direction in ("downward", "upward", "dephasing"):
            family = family_audits["families"][direction]
            scalar = family["scalar_null"]
            time_record = family["time_step_convergence"]
            shell_record = family["shell_convergence"]
            evidence_record = evidence.get("by_direction", {}).get(direction, {})
            family_gate_summary[direction] = {
                "scalar_null": (
                    "PENDING"
                    if not scalar.get("available")
                    else "PASS"
                    if scalar.get("pointwise_pass") and scalar.get("integrated_pass")
                    else "FAIL"
                ),
                "time_step": (
                    "PENDING"
                    if not time_record.get("scientific_gate_evaluable")
                    else "PASS" if time_record.get("passed") else "FAIL"
                ),
                "shell": (
                    "PENDING"
                    if not shell_record.get("scientific_gate_evaluable")
                    else "PASS" if shell_record.get("passed") else "FAIL"
                ),
                "evidence": evidence_record.get(
                    "classification", EVIDENCE_BUDGET_INCOMPLETE
                ),
            }
        mixed_core_origins = [
            record.package.origin
            for record in records
            if record.matrix_id in SPEC_BY_ID
            and str(record.configuration.get("numerical_core_sha256", ""))
            != options.expected_numerical_core_sha256
        ]
        selection_decisions = selection_audit.get("selection_decisions", {})
        partial_candidate_records = [
            record
            for decision in selection_decisions.values()
            if isinstance(decision, Mapping)
            for record in decision.get("incomplete_candidate_records", [])
            if isinstance(record, Mapping)
        ]
        summary = {
            **overall,
            "input_paths": [str(path) for path in options.input_paths],
            "Task05_input_paths": [str(path) for path in options.task05_input_paths],
            "Task07_candidate_count": len(records),
            "Task05_candidate_count": len(task05_candidates),
            "case_statuses": {
                matrix_id: result.status
                for matrix_id, result in case_results.items()
            },
            "status_counts": status_counts,
            "case_rows": case_rows,
            "family_gate_summary": family_gate_summary,
            "mixed_or_legacy_core_candidate_count": len(mixed_core_origins),
            "mixed_or_legacy_core_origins": mixed_core_origins,
            "partial_or_in_progress_candidate_count": len(partial_candidate_records),
            "partial_or_in_progress_candidates": partial_candidate_records,
            "completed_scientific_failure_count": status_counts.get(STATUS_FAILED, 0),
            "scientifically_admissible_case_count": sum(
                result.scientific_admissible for result in case_results.values()
            ),
            "reproducibility_closed_case_count": sum(
                result.reproducibility_closed for result in case_results.values()
            ),
            "output_directory": str(output_path),
            "aggregate_report": outputs["paths"]["report"],
            "case_identity_table": outputs["paths"]["case_identity"],
            "per_case_metrics": outputs["paths"]["per_case_metrics"],
            "share_zip": outputs["paths"]["share_zip"],
            "share_zip_sha256": outputs["share_zip"]["sha256"],
            "diagnostic_share_zip": outputs["paths"]["diagnostic_zip"],
            "diagnostic_share_zip_sha256": outputs["diagnostic_share_zip"][
                "sha256"
            ],
        }
        return int(overall["exit_code"]), summary
    except Exception as exc:
        failure = {
            "stage": STAGE_NAME,
            "loader_version": LOADER_VERSION,
            "status": "execution_or_output_failure",
            "failed_utc": utc_now_iso(),
            "error": repr(exc),
            "traceback": traceback.format_exc(),
            "input_paths": [str(path) for path in options.input_paths],
            "output_directory": str(output_path),
        }
        try:
            atomic_write_derived_json(
                task08_output_paths(output_path)["failure"], failure
            )
        except Exception:
            pass
        return 1, failure


# =============================================================================
# REDUCED SYNTHETIC SELF-TEST (NON-PHYSICAL)
# =============================================================================
def atomic_save_npy(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("wb") as handle:
        np.save(handle, np.asarray(array), allow_pickle=False)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def _synthetic_case_amplitude(spec: MatrixCaseSpec) -> float:
    if spec.propagator_type == "scalar_factorized":
        return 0.0
    base = {
        "downward": 2.0e-4,
        "upward": -3.0e-4,
        "dephasing": 0.0,
    }[spec.environment_direction]
    if spec.omega == 1.0:
        base *= 0.4
    if spec.role == "time_step_control":
        base *= 1.002
    if spec.role == "shell_cutoff_control":
        base *= 0.998
    return base


def _synthetic_kernel_products(spec: MatrixCaseSpec) -> Dict[str, Any]:
    times = np.arange(101, dtype=np.float64) * 0.1
    panels = 100
    nodes = 101
    midpoints = 0.5 * (times[:-1] + times[1:])
    amplitude = _synthetic_case_amplitude(spec)
    profile = np.exp(-((midpoints - 3.2) / 2.2) ** 2) * (
        1.0 + 0.15 * np.sin(1.3 * midpoints)
    )
    insertion_profile = np.exp(-0.02 * times)
    total = np.zeros((panels, nodes), dtype=np.float64)
    jump = np.zeros_like(total)
    for panel in range(panels):
        for insertion in range(panel + 1):
            value = amplitude * profile[panel] * insertion_profile[insertion]
            total[panel, insertion] = value
            # A nonnegative jump part with exact anticommutator cancellation.
            jump[panel, insertion] = abs(value) + (
                1.0e-6 * abs(profile[panel]) if value == 0.0 else 1.0e-7
            )
    anti = total - jump
    durations = np.diff(times)
    density_jump = jump / durations[:, None]
    density_anti = anti / durations[:, None]
    density_total = total / durations[:, None]
    kernel_survival = kernel_survival_from_panel_probability(total)
    chi_s, chi_p, chi_g = reconstruct_response_from_kernel(
        times, total, kernel_survival
    )
    coarse = aggregate_kernel_to_coarse(times, total, kernel_survival)

    if spec.environment_direction == "upward":
        source_jump = np.column_stack(
            (np.exp(-0.02 * times), np.exp(-0.02 * times))
        )
    else:
        activity_axis = 0.1 * (1.0 - np.exp(-0.5 * times))
        source_jump = np.column_stack((activity_axis, activity_axis))
    source_anti = source_jump.copy()
    source_trace_terms = source_jump - source_anti
    source_trace_total = np.sum(source_trace_terms, axis=1)
    source_activity = np.sum(source_jump, axis=1)
    reference_survival = np.exp(-0.08 * times)
    reference_s_down = 0.2 * (1.0 - np.exp(-0.3 * times))
    reference_s_up = 2.0 * np.exp(-0.02 * times)
    reference_s_phi = 0.1 * (1.0 - np.exp(-0.2 * times))
    reference_top = 1.0e-8 * (1.0 - np.exp(-times))

    benchmark_times = np.arange(11, dtype=np.float64) * 0.002
    benchmark_full_s = np.zeros(11, dtype=np.float64)
    benchmark_full_p = np.zeros(10, dtype=np.float64)
    benchmark_low_s = benchmark_full_s.copy()
    benchmark_low_p = benchmark_full_p.copy()
    benchmark_kernel_p = np.zeros((10, 11), dtype=np.float64)
    benchmark_kernel_s = np.zeros((11, 11), dtype=np.float64)
    return {
        "times": times,
        "insertion_steps": np.arange(101, dtype=np.int64)
        * int(round(0.1 / spec.dt)),
        "panel_durations": durations,
        "jump": jump,
        "anti": anti,
        "total": total,
        "density_jump": density_jump,
        "density_anti": density_anti,
        "density_total": density_total,
        "kernel_survival": kernel_survival,
        "chi_survival": chi_s,
        "chi_panel_probability": chi_p,
        "chi_click_density": chi_g,
        "coarse": coarse,
        "source_jump": source_jump,
        "source_anti": source_anti,
        "source_trace_terms": source_trace_terms,
        "source_trace_total": source_trace_total,
        "source_activity": source_activity,
        "reference_survival": reference_survival,
        "reference_s_down": reference_s_down,
        "reference_s_up": reference_s_up,
        "reference_s_phi": reference_s_phi,
        "reference_top": reference_top,
        "benchmark_times": benchmark_times,
        "benchmark_full_s": benchmark_full_s,
        "benchmark_full_p": benchmark_full_p,
        "benchmark_low_s": benchmark_low_s,
        "benchmark_low_p": benchmark_low_p,
        "benchmark_kernel_p": benchmark_kernel_p,
        "benchmark_kernel_s": benchmark_kernel_s,
    }


def _synthetic_dummy_solver_source() -> str:
    return '''#!/usr/bin/env python3
"""Synthetic Task-07 source marker. Never used as physical evidence."""
def run_reduced_full_tangent_benchmark():
    return None
def compute_low_rank_kernel():
    return None
def reconstruct_response_from_kernel():
    return None
'''


def _write_synthetic_task07_case(
    root: Path,
    spec: MatrixCaseSpec,
    *,
    synthetic_core_sha256: str,
    rerun_closed: bool,
) -> Path:
    case_dir = root / f"synthetic_{spec.matrix_id}_{spec.role}"
    case_dir.mkdir(parents=True, exist_ok=True)
    prefix = spec.canonical_prefix()
    products = _synthetic_kernel_products(spec)
    source_name = f"{prefix}_07_environmental_response_solver.py"
    atomic_write_text(case_dir / source_name, _synthetic_dummy_solver_source())
    source_hash = sha256_file(case_dir / source_name)
    output_contract = list(CORE_REQUIRED_SOLVER_SUFFIXES) + [
        CURRENT_CLOSURE_PILOT_SUFFIX,
        CURRENT_RUNTIME_SOLVER_SUFFIX,
    ]
    production_contract = {
        "propagator_type": spec.propagator_type,
        "environment_direction": spec.environment_direction,
        "omega": spec.omega,
        "N_shell": spec.n_shell,
        "dt": spec.dt,
        "T_final": spec.t_final,
        "insertion_dt": spec.insertion_dt,
        "response_reference_rtol": 1.0e-10,
        "branch_rtol": 1.0e-10,
    }
    synthetic_task05_prefix = canonical_task05_prefix(
        spec.propagator_type, spec.omega, spec.initial_mode,
        spec.n_shell, spec.dt, spec.t_final
    )
    synthetic_task05_manifest_sha = sha256_json(
        {"synthetic_Task05_prefix": synthetic_task05_prefix}
    )
    synthetic_task05_gmres = {
        "name": "baseline_rtol1e-8",
        "rtol": 1.0e-8,
        "atol": 0.0,
        "restart": 30,
        "maxiter": 1000,
        "passed": True,
    }
    config: Dict[str, Any] = {
        "stage": TASK07_STAGE_NAME,
        "script_version": EXPECTED_TASK07_SCRIPT_VERSION,
        "case_prefix": prefix,
        "propagator_type": spec.propagator_type,
        "environment_direction": spec.environment_direction,
        "initial_mode": spec.initial_mode,
        "omega": spec.omega,
        "N_shell": spec.n_shell,
        "dt": spec.dt,
        "T_final": spec.t_final,
        "insertion_dt": spec.insertion_dt,
        "num_steps": int(round(spec.t_final / spec.dt)),
        "insertion_stride_steps": int(round(spec.insertion_dt / spec.dt)),
        "N_z": EXPECTED_N_Z,
        "L_z": EXPECTED_L_Z,
        "t_cut": T_CUT_DEFAULT,
        "manual_single_case_policy": True,
        "automatic_production_sweep": False,
        "zero_environmental_rate_reference": True,
        "finite_positive_rate_present": False,
        "temperature_parameter_present": False,
        "trajectory_or_Monte_Carlo_present": False,
        "explicit_detector_reservoir_present": False,
        "CAP_or_second_roof_loss_present": False,
        "numerical_core_sha256": synthetic_core_sha256,
        "source_sha256": source_hash,
        "copied_source_sha256": source_hash,
        "copied_source_file": source_name,
        "fixed_stage_directory": case_dir.name,
        "manual_stage_folder_number": None,
        "response_reference_gmres_rtol": 1.0e-10,
        "branch_gmres_rtol": 1.0e-10,
        "gmres": {
            "response_reference_rtol": 1.0e-10,
            "branch_rtol": 1.0e-10,
        },
        "complete_insertion_grid": {
            "node_count": 101,
            "panel_count": 100,
            "first_time": 0.0,
            "last_time": 10.0,
        },
        "production_contract": production_contract,
        "production_contract_sha256": sha256_json(production_contract),
        "output_contract": output_contract,
        "task05_reference_prefix": synthetic_task05_prefix,
        "task05_reference_gmres_rtol": 1.0e-8,
        "task05_preflight_references": {
            spec.initial_mode: {
                "output_manifest_sha256": synthetic_task05_manifest_sha,
                "gmres_family": synthetic_task05_gmres,
                "stage_directory": "synthetic_Task05_directory",
            }
        },
        "backend": "synthetic_numpy",
        "backend_metadata": {"synthetic": True},
        "smoke_test": True,
    }
    deterministic = {
        key: value for key, value in config.items() if key != "backend_metadata"
    }
    config["configuration_sha256"] = sha256_json(deterministic)
    atomic_write_json(case_dir / f"{prefix}_configuration.json", config)

    atomic_save_npy(case_dir / f"{prefix}_times.npy", products["times"])
    atomic_save_npy(
        case_dir / f"{prefix}_insertion_times.npy", products["times"]
    )
    atomic_save_npy(
        case_dir / f"{prefix}_chi_survival.npy", products["chi_survival"]
    )
    atomic_save_npy(
        case_dir / f"{prefix}_chi_click_density.npy",
        products["chi_click_density"],
    )
    coarse = products["coarse"]
    atomic_savez(
        case_dir / f"{prefix}_kernel_summary.npz",
        insertion_steps=products["insertion_steps"],
        insertion_times=products["times"],
        panel_durations=products["panel_durations"],
        kernel_jump_probability=products["jump"],
        kernel_anticommutator_probability=products["anti"],
        kernel_total_probability=products["total"],
        kernel_click_density_jump=products["density_jump"],
        kernel_click_density_anticommutator=products["density_anti"],
        kernel_click_density_total=products["density_total"],
        kernel_survival=products["kernel_survival"],
        chi_panel_probability=products["chi_panel_probability"],
        coarse_node_indices=coarse["node_indices"],
        coarse_times=coarse["times"],
        coarse_kernel_probability=coarse["kernel_probability"],
        coarse_kernel_survival=coarse["kernel_survival"],
        coarse_chi_survival=coarse["chi_survival"],
        coarse_chi_panel_probability=coarse["chi_panel_probability"],
        interpretation=np.asarray(
            [
                "Rows are output panels; columns are environmental insertion state nodes. "
                "Total equals jump plus anticommutator. Entries above the causal triangle are zero."
            ],
            dtype="U512",
        ),
    )
    atomic_savez(
        case_dir / f"{prefix}_source_insertion_summary.npz",
        insertion_steps=products["insertion_steps"],
        insertion_times=products["times"],
        jump_norm2=products["source_jump"],
        anti_expectation=products["source_anti"],
        trace_terms=products["source_trace_terms"],
        trace_total=products["source_trace_total"],
        activity_total=products["source_activity"],
        reference_survival=products["reference_survival"],
        reference_s_down=products["reference_s_down"],
        reference_s_up=products["reference_s_up"],
        reference_s_phi=products["reference_s_phi"],
        reference_top_shell=products["reference_top"],
        branch_labels=np.asarray(("jump_x", "anti_x", "jump_y", "anti_y"), dtype="U8"),
        interpretation=np.asarray(
            [
                "Subnormalized zero-rate no-click source diagnostics. Trace_total must vanish "
                "because each complete dissipator is trace preserving."
            ],
            dtype="U512",
        ),
    )
    atomic_savez(
        case_dir / f"{prefix}_full_tangent_benchmark.npz",
        times=products["benchmark_times"],
        full_chi_survival=products["benchmark_full_s"],
        full_chi_panel_probability=products["benchmark_full_p"],
        low_rank_chi_survival=products["benchmark_low_s"],
        low_rank_chi_panel_probability=products["benchmark_low_p"],
        low_rank_kernel_probability=products["benchmark_kernel_p"],
        low_rank_kernel_survival=products["benchmark_kernel_s"],
    )
    integrated = integrated_response_metrics(
        products["times"],
        products["chi_survival"],
        products["chi_panel_probability"],
        products["chi_click_density"],
        T_CUT_DEFAULT,
    )
    atomic_write_json(case_dir / f"{prefix}_integrated_response.json", integrated)

    reference_record = {
        "maximum_gmres_info_abs": 0,
        "maximum_true_relative_residual": 0.0,
        "minimum_midpoint_probability": 0.0,
        "roof_probability_closure_residual": 0.0,
        "closure_tolerance_used": 1.0e-9,
        "all_arrays_finite": True,
        "local_numerical_passed": True,
        "gmres_rtol_used": 1.0e-10,
        "initial_survival": 1.0,
        "final_survival": float(products["reference_survival"][-1]),
    }
    reference_audit = {
        "architecture": "dual_zero_rate_reference",
        "Task05_regression_reference": dict(reference_record),
        "response_reference": dict(reference_record),
        "Task05_recovery": {
            "passed": True,
            "required": True,
            "shape_match": True,
            "task05_case_prefix": synthetic_task05_prefix,
            "task05_canonical_target_prefix": synthetic_task05_prefix,
            "task05_configuration_sha256": sha256_json(
                {"synthetic_Task05_configuration": synthetic_task05_prefix}
            ),
            "task05_gmres_family": synthetic_task05_gmres,
            "task05_output_manifest": {
                "all_hashes_match": True,
                "manifest_sha256": synthetic_task05_manifest_sha,
                "files": {
                    f"{synthetic_task05_prefix}_survival.npy": {
                        "expected": "synthetic-identical-hash",
                        "actual": "synthetic-identical-hash",
                        "match": True,
                    }
                },
            },
            "comparison_metrics": {
                "times_max_abs": 0.0,
                "survival_max_abs": 0.0,
                "step_probability_max_abs": 0.0,
                "s_down_max_abs": 0.0,
                "s_up_max_abs": 0.0,
                "s_phi_max_abs": 0.0,
            },
            "tolerances": {
                "reference_array_abs": TASK05_REFERENCE_ARRAY_ABS_TOL,
                "reference_source_abs": TASK05_SOURCE_CURVE_ABS_TOL,
            },
        },
        "cross_reference_consistency": {
            "passed": True,
            "shape_match": True,
            "complete_censored_law_total_variation_distance": 0.0,
            "maximum_absolute_differences": {"survival": 0.0},
            "maximum_source_diagnostic_difference": 0.0,
            "maximum_phase_aligned_selected_state_relative_difference": 0.0,
            "maximum_phase_aligned_q_roof_relative_difference": 0.0,
            "tolerances": {
                "complete_law_total_variation": 1.0e-6,
                "survival_Linf": 1.0e-6,
                "source_diagnostic_Linf": 1.0e-5,
                "phase_aligned_selected_state_relative": 2.0e-5,
                "phase_aligned_q_roof_relative": 2.0e-5,
            },
        },
        "passed": True,
    }
    atomic_write_json(case_dir / f"{prefix}_reference_audit.json", reference_audit)
    atomic_write_json(
        case_dir / f"{prefix}_operator_audit.json",
        {
            "all_checks_passed": True,
            "Task05_oscillator_operator_audit": {
                "all_checks_passed": True,
                "dimension": (spec.n_shell + 1) * (spec.n_shell + 2) // 2,
                "spin_resolved_channel_dimension": (spec.n_shell + 1) * (spec.n_shell + 2),
            },
        },
    )
    pilot = {
        "applicable": spec.propagator_type == "spinor",
        "passed": True,
        "maximum_closure_residual": 0.0,
        "maximum_branch_true_relative_residual": 0.0,
        "maximum_branch_gmres_info_abs": 0,
        "maximum_source_trace_residual": 0.0,
        "reference_and_branch_rtol_matched": True,
        "tolerances": {"closure_absolute": CLOSURE_PILOT_ABS_TOL},
    }
    atomic_write_json(case_dir / f"{prefix}_closure_pilot_audit.json", pilot)

    tangent_curve = products["chi_survival"] + np.concatenate(
        ([0.0], np.cumsum(products["chi_panel_probability"], dtype=np.float64))
    )
    tangent_abs = dense_max_abs(tangent_curve)
    response_scale = max(
        dense_max_abs(products["chi_survival"]),
        float(np.sum(np.abs(products["chi_panel_probability"]))),
        1.0e-15,
    )
    raw_metrics = {
        "maximum_source_trace_residual": 0.0,
        "maximum_independent_kernel_probability_closure_residual": 0.0,
        "maximum_tangent_probability_closure_residual": tangent_abs,
        "relative_tangent_probability_closure_residual": tangent_abs / response_scale,
        "final_detection_response_identity_residual": abs(
            float(np.sum(products["chi_panel_probability"]))
            + float(products["chi_survival"][-1])
        ),
        "maximum_noncausal_kernel_entry": 0.0,
        "minimum_jump_kernel_probability": float(np.min(products["jump"])),
        "maximum_abs_scalar_pointwise_click_kernel": dense_max_abs(
            products["density_total"]
        ),
    }
    response_audit = {
        "all_case_local_checks_passed": True,
        "production_physical_claim_authorized": False,
        "checks": {
            "kernel_decomposition": True,
            "source_trace": True,
            "tangent_closure": True,
            "scalar_null": True,
            "benchmark": True,
        },
        "metrics": raw_metrics,
        "integrated_response": integrated,
    }
    atomic_write_json(case_dir / f"{prefix}_response_audit.json", response_audit)
    atomic_write_json(
        case_dir / f"{prefix}_runtime_metrics.json",
        {
            "synthetic": True,
            "maximum_branch_true_relative_residual": 0.0,
            "maximum_reference_true_relative_residual": 0.0,
        },
    )

    stable_suffixes = [
        suffix
        for suffix in required_solver_suffixes(config)
        if suffix not in NONDETERMINISTIC_SOLVER_SUFFIXES
    ]
    stable_names = [f"{prefix}_{suffix}" for suffix in stable_suffixes]
    manifest = {
        "hash_algorithm": "SHA-256",
        "case_prefix": prefix,
        "configuration_sha256": config["configuration_sha256"],
        "source_sha256": source_hash,
        "files": {
            name: sha256_file(case_dir / name) for name in stable_names
        },
    }
    atomic_write_json(case_dir / f"{prefix}_output_hashes.json", manifest)
    manifest_hash = sha256_file(case_dir / f"{prefix}_output_hashes.json")
    rerun = {
        "passed": rerun_closed,
        "pending": not rerun_closed,
        "comparison_applicable": rerun_closed,
    }
    atomic_write_json(
        case_dir / f"{prefix}_run_status.json",
        {
            "status": "completed_pass" if rerun_closed else "completed_incomplete",
            "verdict": "PASS_CASE_LOCAL" if rerun_closed else "PASS_CASE_LOCAL_RERUN_PENDING",
            "all_case_local_checks_passed": True,
            "configuration_sha256": config["configuration_sha256"],
            "output_hash_manifest": f"{prefix}_output_hashes.json",
            "output_hash_manifest_sha256": manifest_hash,
            "Task08_physical_claim_authorized": False,
            "deterministic_same_prefix_rerun": rerun,
            "solver_side_external_controls": {
                "all_required_controls_available": False,
                "evidence_status": "PENDING",
            },
        },
    )

    # Synthetic stand-in for the independently executed per-case loader.
    loader_source_name = f"{prefix}_07_environmental_response_case_loader.py"
    atomic_write_text(
        case_dir / loader_source_name,
        '#!/usr/bin/env python3\n"""Synthetic per-case loader record."""\n',
    )
    loader_audit_name = f"{prefix}_case_loader_audit.json"
    loader_verdict = "PASS_CASE_LOCAL" if rerun_closed else "PASS_CASE_LOCAL_RERUN_PENDING"
    atomic_write_json(
        case_dir / loader_audit_name,
        {
            "case_prefix": prefix,
            "all_independent_checks_passed": True,
            "failed_checks": [],
            "pending_items": [] if rerun_closed else ["deterministic rerun"],
            "verdict": loader_verdict,
            "exit_code": 0 if rerun_closed else 3,
        },
    )
    loader_source_hash = sha256_file(case_dir / loader_source_name)
    loader_manifest_files = {
        loader_audit_name: sha256_file(case_dir / loader_audit_name),
        loader_source_name: loader_source_hash,
    }
    loader_manifest_name = f"{prefix}_case_loader_output_hashes.json"
    atomic_write_json(
        case_dir / loader_manifest_name,
        {
            "hash_algorithm": "SHA-256",
            "case_prefix": prefix,
            "loader_source_sha256": loader_source_hash,
            "copied_loader_source_sha256": loader_source_hash,
            "verdict": loader_verdict,
            "files": loader_manifest_files,
        },
    )
    loader_manifest_hash = sha256_file(case_dir / loader_manifest_name)
    atomic_write_json(
        case_dir / f"{prefix}_case_loader_run_status.json",
        {
            "all_independent_checks_passed": True,
            "failed_check_count": 0,
            "pending_items": [] if rerun_closed else ["deterministic rerun"],
            "verdict": loader_verdict,
            "exit_code": 0 if rerun_closed else 3,
            "loader_source_sha256": loader_source_hash,
            "copied_loader_source_sha256": loader_source_hash,
            "loader_source_copy_hash_matches": True,
            "loader_output_hash_manifest": loader_manifest_name,
            "loader_output_hash_manifest_sha256": loader_manifest_hash,
        },
    )
    return case_dir


def _write_synthetic_task05_case(
    root: Path,
    *,
    propagator_type: str,
    omega: float,
    mode: str,
    n_shell: int,
    dt: float,
    desired_panel_column: np.ndarray,
) -> Path:
    prefix = canonical_task05_prefix(
        propagator_type, omega, mode, n_shell, dt, 10.0
    )
    case_dir = root / f"synthetic_Task05_{propagator_type}_{omega:g}_{mode}"
    case_dir.mkdir(parents=True, exist_ok=True)
    stride = int(round(0.1 / dt))
    base_panel = np.full(100, 1.0e-3, dtype=np.float64)
    if mode == "00":
        panel = base_panel
    else:
        panel = base_panel + 0.5 * desired_panel_column
    if np.min(panel) <= 0.0:
        raise RuntimeError("Synthetic Task-05 panel probabilities became nonpositive")
    fine = np.repeat(panel / stride, stride).astype(np.float64)
    config: Dict[str, Any] = {
        "stage": TASK05_STAGE_NAME,
        "case_prefix": prefix,
        "propagator_type": propagator_type,
        "initial_mode": mode,
        "omega": omega,
        "N_shell": n_shell,
        "dt": dt,
        "T_final": 10.0,
        "zero_ambient_bath": True,
        "backend_metadata": {"synthetic": True},
    }
    deterministic = dict(config)
    config["configuration_sha256"] = sha256_json(deterministic)
    atomic_write_json(case_dir / f"{prefix}_configuration.json", config)
    atomic_save_npy(case_dir / f"{prefix}_step_loss_roof_midpoint.npy", fine)
    stable = (
        f"{prefix}_configuration.json",
        f"{prefix}_step_loss_roof_midpoint.npy",
    )
    atomic_write_json(
        case_dir / f"{prefix}_output_hashes.json",
        {
            "hash_algorithm": "SHA-256",
            "files": {name: sha256_file(case_dir / name) for name in stable},
        },
    )
    atomic_write_json(
        case_dir / f"{prefix}_run_status.json",
        {"status": "completed", "all_solver_checks_passed": True},
    )
    return case_dir


def _create_synthetic_task05_family(
    root: Path, task07_case_dirs: Mapping[str, Path]
) -> List[Path]:
    created: List[Path] = []
    for matrix_id, propagator, omega, n_shell, dt in (
        ("U1", "scalar_factorized", 100.0, 12, 5.0e-4),
        ("U2", "spinor", 100.0, 12, 5.0e-4),
        ("U3", "spinor", 1.0, 12, 1.0e-3),
    ):
        spec = SPEC_BY_ID[matrix_id]
        prefix = spec.canonical_prefix()
        with np.load(
            task07_case_dirs[matrix_id] / f"{prefix}_kernel_summary.npz",
            allow_pickle=False,
        ) as archive:
            desired = np.asarray(archive["kernel_total_probability"])[:, 0]
        for mode in ("00", "10", "01"):
            created.append(
                _write_synthetic_task05_case(
                    root,
                    propagator_type=propagator,
                    omega=omega,
                    mode=mode,
                    n_shell=n_shell,
                    dt=dt,
                    desired_panel_column=desired,
                )
            )
    return created


def _zip_synthetic_cases(zip_path: Path, case_dirs: Mapping[str, Path]) -> None:
    tmp = zip_path.with_name(zip_path.name + ".tmp")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for matrix_id, directory in sorted(case_dirs.items()):
            for path in sorted(directory.iterdir()):
                if path.is_file():
                    archive.write(path, arcname=f"{matrix_id}/{path.name}")
    os.replace(tmp, zip_path)


def run_synthetic_self_test(output_dir: Union[str, os.PathLike[str]]) -> Tuple[int, Dict[str, Any]]:
    root = Path(output_dir).expanduser().resolve()
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    sources = root / "synthetic_sources"
    case_root = sources / "Task07_cases"
    task05_root = sources / "Task05_cases"
    case_root.mkdir(parents=True)
    task05_root.mkdir(parents=True)
    synthetic_core = sha256_bytes(b"Task08 synthetic v8 core")
    case_dirs: Dict[str, Path] = {}
    for spec in FROZEN_MATRIX:
        case_dirs[spec.matrix_id] = _write_synthetic_task07_case(
            case_root,
            spec,
            synthetic_core_sha256=synthetic_core,
            rerun_closed=spec.matrix_id == "D3",
        )
    _create_synthetic_task05_family(task05_root, case_dirs)

    # Real-schema Task-05 status regression: authoritative products use
    # status="completed" with all_solver_checks_passed=True. A historical
    # completed_with_failed_gate record must never be accepted by prefix alone.
    synthetic_options = Task08Options(
        input_paths=(),
        output_dir=root,
        task05_input_paths=(task05_root,),
        inherited_bounds_path=None,
        master_audit_path=None,
        handoff_path=None,
        strict_reruns=False,
        allow_missing_per_case_loader=False,
        max_zip_member_bytes=2 * 1024 * 1024 * 1024,
        synthetic_mode=True,
        expected_numerical_core_sha256=synthetic_core,
    )
    valid_task05_candidates = discover_task05_candidates(synthetic_options)
    authoritative_task05_status_accepted = bool(
        valid_task05_candidates
        and all(candidate.integrity_passed for candidate in valid_task05_candidates)
    )
    negative_status_root = sources / "Task05_failed_status_fixture"
    source_task05_dir = next(path for path in task05_root.iterdir() if path.is_dir())
    negative_task05_dir = negative_status_root / source_task05_dir.name
    negative_status_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_task05_dir, negative_task05_dir)
    negative_config_path = next(negative_task05_dir.glob("*_configuration.json"))
    negative_config = read_json_file(negative_config_path)
    negative_prefix = str(negative_config["case_prefix"])
    atomic_write_json(
        negative_task05_dir / f"{negative_prefix}_run_status.json",
        {
            "status": "completed_with_failed_gate",
            "all_solver_checks_passed": False,
        },
    )
    negative_candidate = Task05Candidate(
        DirectoryPackage(negative_task05_dir, negative_prefix),
        negative_config_path.name,
        negative_prefix,
        negative_config,
    )
    _audit_task05_candidate_integrity(negative_candidate)
    failed_Task05_status_rejected = not negative_candidate.integrity_passed

    inherited_path = sources / "synthetic_inherited_bounds.json"
    atomic_write_json(
        inherited_path,
        {
            "global": {
                "epsilon_repr": 1.0e-6,
                "epsilon_z": 1.0e-6,
            },
            "synthetic_non_physical": True,
        },
    )
    case_zip = sources / "synthetic_Task07_full_family.zip"
    _zip_synthetic_cases(case_zip, case_dirs)

    def input_snapshot() -> Dict[str, str]:
        snapshot: Dict[str, str] = {}
        for source_root in (case_root, task05_root):
            for path in sorted(source_root.rglob("*")):
                if path.is_file():
                    snapshot[str(path.relative_to(sources))] = sha256_file(path)
        snapshot[str(case_zip.relative_to(sources))] = sha256_file(case_zip)
        snapshot[str(inherited_path.relative_to(sources))] = sha256_file(
            inherited_path
        )
        return snapshot

    pristine_inputs_before_audit = input_snapshot()

    partial_output = root / "partial_audit"
    partial_code, partial_summary = run_task08(
        input_paths=[case_dirs["D3"]],
        output_dir=partial_output,
        inherited_bounds_path=inherited_path,
        synthetic_mode=True,
        expected_numerical_core_sha256=synthetic_core,
    )
    full_output = root / "full_zip_audit"
    full_code, full_summary = run_task08(
        input_paths=[case_zip],
        task05_input_paths=[task05_root],
        output_dir=full_output,
        inherited_bounds_path=inherited_path,
        synthetic_mode=True,
        expected_numerical_core_sha256=synthetic_core,
    )
    full_case_integrity = read_json_file(
        full_output / "Task08_case_integrity_audit.json"
    )
    full_channel_superposition = read_json_file(
        full_output / "Task08_channel_superposition_audit.json"
    )
    real_schema_recovery_checks = [
        value
        for record in full_case_integrity.get("cases", {}).values()
        for name, value in record.get("checks", {}).items()
        if "Task05_recovery_" in name
    ]

    # Directory/ZIP mirrors with identical stable scientific fingerprints must
    # deduplicate without changing the physical matrix or creating a conflict.
    mirror_output = root / "mirror_dedup_audit"
    mirror_code, mirror_summary = run_task08(
        input_paths=[case_root, case_zip],
        task05_input_paths=[task05_root],
        output_dir=mirror_output,
        inherited_bounds_path=inherited_path,
        synthetic_mode=True,
        expected_numerical_core_sha256=synthetic_core,
    )
    pristine_inputs_after_audit = input_snapshot()
    mirror_inventory = read_json_file(mirror_output / "Task08_input_inventory.json")
    mirror_decisions = mirror_inventory.get("selection_audit", {}).get(
        "selection_decisions", {}
    )
    mirror_count = sum(
        bool(record.get("mirror_origins"))
        for record in mirror_decisions.values()
        if isinstance(record, Mapping)
    )

    # A complete package with the right physical configuration but a legacy or
    # mixed numerical core is inventory evidence only; it must not fill a formal
    # v8 matrix role.
    legacy_root = sources / "legacy_mixed_core_only"
    legacy_root.mkdir(parents=True)
    legacy_case = legacy_root / case_dirs["D1"].name
    shutil.copytree(case_dirs["D1"], legacy_case)
    legacy_prefix = SPEC_BY_ID["D1"].canonical_prefix()
    legacy_config_name = f"{legacy_prefix}_configuration.json"
    legacy_manifest_name = f"{legacy_prefix}_output_hashes.json"
    legacy_status_name = f"{legacy_prefix}_run_status.json"
    legacy_config = read_json_file(legacy_case / legacy_config_name)
    legacy_config["numerical_core_sha256"] = sha256_bytes(b"legacy mixed core")
    legacy_config.pop("configuration_sha256", None)
    legacy_deterministic = {
        key: value
        for key, value in legacy_config.items()
        if key != "backend_metadata"
    }
    legacy_config["configuration_sha256"] = sha256_json(legacy_deterministic)
    atomic_write_json(legacy_case / legacy_config_name, legacy_config)
    legacy_manifest = read_json_file(legacy_case / legacy_manifest_name)
    legacy_manifest["configuration_sha256"] = legacy_config[
        "configuration_sha256"
    ]
    legacy_manifest["files"][legacy_config_name] = sha256_file(
        legacy_case / legacy_config_name
    )
    atomic_write_json(legacy_case / legacy_manifest_name, legacy_manifest)
    legacy_status = read_json_file(legacy_case / legacy_status_name)
    legacy_status["configuration_sha256"] = legacy_config[
        "configuration_sha256"
    ]
    legacy_status["output_hash_manifest_sha256"] = sha256_file(
        legacy_case / legacy_manifest_name
    )
    atomic_write_json(legacy_case / legacy_status_name, legacy_status)
    legacy_output = root / "legacy_isolation_audit"
    legacy_code, legacy_summary = run_task08(
        input_paths=[legacy_root],
        output_dir=legacy_output,
        inherited_bounds_path=inherited_path,
        synthetic_mode=True,
        expected_numerical_core_sha256=synthetic_core,
    )
    legacy_integrity = read_json_file(
        legacy_output / "Task08_case_integrity_audit.json"
    )
    legacy_inventory = read_json_file(legacy_output / "Task08_input_inventory.json")

    corrupt_root = sources / "corrupted_Task07_cases"
    shutil.copytree(case_root, corrupt_root)
    corrupt_d2 = corrupt_root / case_dirs["D2"].name
    d2_prefix = SPEC_BY_ID["D2"].canonical_prefix()
    corrupted = np.load(
        corrupt_d2 / f"{d2_prefix}_chi_survival.npy", allow_pickle=False
    )
    corrupted = np.asarray(corrupted, dtype=np.float64).copy()
    corrupted[10] += 1.0e-3
    atomic_save_npy(corrupt_d2 / f"{d2_prefix}_chi_survival.npy", corrupted)
    corrupt_output = root / "corruption_audit"
    corrupt_code, corrupt_summary = run_task08(
        input_paths=[corrupt_root],
        task05_input_paths=[task05_root],
        output_dir=corrupt_output,
        inherited_bounds_path=inherited_path,
        synthetic_mode=True,
        expected_numerical_core_sha256=synthetic_core,
    )

    # A coordinated manifest update cannot launder non-finite scientific raw
    # data. Update both the stable-file hash and the run-status manifest hash,
    # then require the independent finiteness gate—not the hash gate—to fail.
    nonfinite_root = sources / "coordinated_nonfinite_Task07_cases"
    shutil.copytree(case_root, nonfinite_root)
    nonfinite_d2 = nonfinite_root / case_dirs["D2"].name
    nonfinite_prefix = SPEC_BY_ID["D2"].canonical_prefix()
    nonfinite_array_name = f"{nonfinite_prefix}_chi_survival.npy"
    nonfinite_manifest_name = f"{nonfinite_prefix}_output_hashes.json"
    nonfinite_status_name = f"{nonfinite_prefix}_run_status.json"
    nonfinite_array = np.asarray(
        np.load(nonfinite_d2 / nonfinite_array_name, allow_pickle=False),
        dtype=np.float64,
    ).copy()
    nonfinite_array[10] = np.nan
    atomic_save_npy(nonfinite_d2 / nonfinite_array_name, nonfinite_array)
    nonfinite_manifest = read_json_file(nonfinite_d2 / nonfinite_manifest_name)
    nonfinite_manifest["files"][nonfinite_array_name] = sha256_file(
        nonfinite_d2 / nonfinite_array_name
    )
    atomic_write_json(nonfinite_d2 / nonfinite_manifest_name, nonfinite_manifest)
    nonfinite_status = read_json_file(nonfinite_d2 / nonfinite_status_name)
    nonfinite_status["output_hash_manifest_sha256"] = sha256_file(
        nonfinite_d2 / nonfinite_manifest_name
    )
    atomic_write_json(nonfinite_d2 / nonfinite_status_name, nonfinite_status)
    nonfinite_output = root / "coordinated_nonfinite_audit"
    nonfinite_code, nonfinite_summary = run_task08(
        input_paths=[nonfinite_root],
        task05_input_paths=[task05_root],
        output_dir=nonfinite_output,
        inherited_bounds_path=inherited_path,
        synthetic_mode=True,
        expected_numerical_core_sha256=synthetic_core,
    )
    nonfinite_integrity = read_json_file(
        nonfinite_output / "Task08_case_integrity_audit.json"
    )
    nonfinite_d2_record = nonfinite_integrity["cases"]["D2"]

    checks = {
        "partial_dataset_returns_incomplete_exit_3": partial_code == 3,
        "partial_dataset_marks_missing_cases": bool(partial_summary.get("missing_cases")),
        "ZIP_full_family_discovery_and_audit_passes": full_code == 0,
        "real_v8_Task05_recovery_comparison_metrics_schema_is_accepted": bool(
            real_schema_recovery_checks and all(real_schema_recovery_checks)
        ),
        "authoritative_Task05_completed_status_is_accepted": (
            authoritative_task05_status_accepted
        ),
        "Task05_completed_with_failed_gate_status_is_rejected": (
            failed_Task05_status_rejected
        ),
        "channel_superposition_basis_record_is_complete": bool(
            full_channel_superposition.get("passed") is True
            and full_channel_superposition.get("common_response_grid") is True
        ),
        "full_family_authorizes_only_zero_rate_synthetic_contract": bool(
            full_summary.get("physical_zero_rate_susceptibility_claim_authorized")
        ),
        "directory_and_ZIP_mirrors_deduplicate": bool(
            mirror_code == 0 and mirror_count == 15
        ),
        "Task07_and_Task05_inputs_remain_byte_identical_after_read_only_audits": (
            pristine_inputs_before_audit == pristine_inputs_after_audit
        ),
        "legacy_mixed_core_is_isolated_as_missing_not_failed": bool(
            legacy_code == 3
            and legacy_integrity["cases"]["D1"]["status"] == STATUS_MISSING
            and legacy_inventory.get("Task07_candidate_categories", {}).get(
                "mapped_legacy_or_mixed_core"
            )
        ),
        "corrupted_stable_raw_file_is_detected": corrupt_code == 2,
        "corruption_does_not_produce_physical_claim": not bool(
            corrupt_summary.get("physical_zero_rate_susceptibility_claim_authorized")
        ),
        "coordinated_nonfinite_raw_data_is_detected_after_hash_refresh": bool(
            nonfinite_code == 2
            and nonfinite_d2_record["checks"].get(
                "manifest_and_files.all_manifest_hashes_match"
            ) is True
            and nonfinite_d2_record["checks"].get(
                "independent_raw_response_reconstruction.all_required_raw_numeric_arrays_finite"
            ) is False
        ),
        "nonfinite_case_does_not_produce_physical_claim": not bool(
            nonfinite_summary.get("physical_zero_rate_susceptibility_claim_authorized")
        ),
    }
    passed = all(checks.values())
    report = {
        "stage": "Task08_synthetic_self_test",
        "created_utc": utc_now_iso(),
        "synthetic_non_physical": True,
        "passed": passed,
        "checks": checks,
        "partial": {"exit_code": partial_code, "summary": partial_summary},
        "full": {"exit_code": full_code, "summary": full_summary},
        "mirror_deduplication": {
            "exit_code": mirror_code,
            "summary": mirror_summary,
            "matrix_roles_with_mirrors": mirror_count,
        },
        "legacy_isolation": {
            "exit_code": legacy_code,
            "summary": legacy_summary,
            "D1_status": legacy_integrity["cases"]["D1"]["status"],
        },
        "corruption": {"exit_code": corrupt_code, "summary": corrupt_summary},
        "coordinated_nonfinite": {
            "exit_code": nonfinite_code,
            "summary": nonfinite_summary,
            "D2_failed_checks": nonfinite_d2_record.get("failed_checks", []),
        },
        "source_paths": {
            "Task07_case_root": str(case_root),
            "Task07_full_zip": str(case_zip),
            "Task05_root": str(task05_root),
            "inherited_bounds": str(inherited_path),
            "legacy_mixed_core_root": str(legacy_root),
            "coordinated_nonfinite_root": str(nonfinite_root),
        },
    }
    atomic_write_derived_json(root / "Task08_synthetic_self_test_report.json", report)
    markdown = "\n".join(
        [
            "# Task-08 Synthetic Self-Test",
            "",
            "**Non-physical validation only.**",
            "",
            f"Overall: **{'PASS' if passed else 'FAIL'}**",
            "",
            *[
                f"- {'PASS' if value else 'FAIL'} — `{name}`"
                for name, value in checks.items()
            ],
            "",
            f"Partial audit: `{partial_output}`",
            f"Full ZIP audit: `{full_output}`",
            f"Mirror-deduplication audit: `{mirror_output}`",
            f"Legacy-isolation audit: `{legacy_output}`",
            f"Corruption audit: `{corrupt_output}`",
            f"Coordinated-nonfinite audit: `{nonfinite_output}`",
            "",
        ]
    )
    atomic_write_text(root / "Task08_synthetic_self_test_report.md", markdown)
    return (0 if passed else 2), report


# =============================================================================
# COMMAND-LINE / JUPYTER ENTRY POINT
# =============================================================================
JUPYTER_DEFAULT_OUTPUT_DIRECTORY_NAME = "4900.Task08_Independent_Aggregate"


def _running_under_ipykernel() -> bool:
    """Return True only for an active IPython/Jupyter kernel process."""
    if "ipykernel" in sys.modules:
        return True
    try:
        from IPython import get_ipython  # type: ignore

        shell = get_ipython()
        return bool(
            shell is not None
            and shell.__class__.__name__ == "ZMQInteractiveShell"
        )
    except Exception:
        return False


def _safe_stage_payload(path: Path) -> Optional[Dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _stage_identity_key(payload: Mapping[str, Any]) -> Optional[Tuple[Any, ...]]:
    stage = payload.get("stage")
    try:
        if stage == TASK07_STAGE_NAME:
            return (
                stage,
                str(payload["propagator_type"]),
                str(payload["environment_direction"]),
                round(float(payload["omega"]), 14),
                str(payload["initial_mode"]),
                int(payload["N_shell"]),
                round(float(payload["dt"]), 16),
                round(float(payload["T_final"]), 14),
                round(float(payload["insertion_dt"]), 14),
            )
        if stage == TASK05_STAGE_NAME:
            return (
                stage,
                str(payload["propagator_type"]),
                round(float(payload["omega"]), 14),
                str(payload["initial_mode"]),
                int(payload["N_shell"]),
                round(float(payload["dt"]), 16),
                round(float(payload["T_final"]), 14),
            )
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    return None


def _stage_identities_from_zip(zip_path: Path) -> Tuple[Set[Tuple[Any, ...]], Set[Tuple[Any, ...]]]:
    task07: Set[Tuple[Any, ...]] = set()
    task05: Set[Tuple[Any, ...]] = set()
    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            for info in archive.infolist():
                if (
                    info.is_dir()
                    or not PurePosixPath(info.filename).name.endswith("_configuration.json")
                    or info.file_size > 8 * 1024 * 1024
                ):
                    continue
                try:
                    payload = json.loads(archive.read(info.filename).decode("utf-8"))
                except Exception:
                    continue
                if not isinstance(payload, dict):
                    continue
                identity = _stage_identity_key(payload)
                if identity is None:
                    continue
                if payload.get("stage") == TASK07_STAGE_NAME:
                    task07.add(identity)
                elif payload.get("stage") == TASK05_STAGE_NAME:
                    task05.add(identity)
    except (OSError, zipfile.BadZipFile):
        pass
    return task07, task05


def _candidate_zip_may_contain_project_data(path: Path) -> bool:
    lowered = path.name.lower()
    return any(
        marker in lowered
        for marker in (
            "task07",
            "task05",
            "stage07",
            "stage05",
            "case_share",
            "diagnostic_share",
        )
    )


def _shallow_task08_project_inventory(candidate: Path) -> Dict[str, Any]:
    """Inspect only the candidate and its immediate children using stage metadata.

    The aggregate root is identified from unique physical configuration tuples,
    not from numeric folder prefixes.  ZIP mirrors of the same case are
    deduplicated at this stage so that one case folder containing its own full
    and diagnostic shares is not mistaken for the multi-case project root.
    """
    candidate = candidate.expanduser().resolve()
    direct_task07: Set[Tuple[Any, ...]] = set()
    direct_task05: Set[Tuple[Any, ...]] = set()
    child_task07: Set[Tuple[Any, ...]] = set()
    child_task05: Set[Tuple[Any, ...]] = set()
    task07_containers: Set[str] = set()
    task05_containers: Set[str] = set()
    inspected_configurations = 0
    inspected_zips = 0

    if not candidate.is_dir():
        return {
            "path": str(candidate),
            "exists": False,
            "qualifies_as_aggregate_root": False,
            "selection_reason": "candidate is not a directory",
        }

    def consume_payload(payload: Mapping[str, Any], container: str, *, child: bool) -> None:
        nonlocal inspected_configurations
        identity = _stage_identity_key(payload)
        if identity is None:
            return
        inspected_configurations += 1
        if payload.get("stage") == TASK07_STAGE_NAME:
            (child_task07 if child else direct_task07).add(identity)
            task07_containers.add(container)
        elif payload.get("stage") == TASK05_STAGE_NAME:
            (child_task05 if child else direct_task05).add(identity)
            task05_containers.add(container)

    for config_path in sorted(candidate.glob("*_configuration.json")):
        payload = _safe_stage_payload(config_path)
        if payload is not None:
            consume_payload(payload, str(candidate), child=False)

    for zip_path in sorted(candidate.glob("*.zip")):
        if not _candidate_zip_may_contain_project_data(zip_path):
            continue
        inspected_zips += 1
        zip_task07, zip_task05 = _stage_identities_from_zip(zip_path)
        direct_task07.update(zip_task07)
        direct_task05.update(zip_task05)
        if zip_task07:
            task07_containers.add(str(zip_path))
        if zip_task05:
            task05_containers.add(str(zip_path))

    excluded_names = {
        JUPYTER_DEFAULT_OUTPUT_DIRECTORY_NAME.lower(),
        "task08_aggregate",
    }
    try:
        children = sorted(candidate.iterdir(), key=lambda item: item.name)
    except OSError:
        children = []
    for child_path in children:
        if not child_path.is_dir() or child_path.name.startswith("."):
            continue
        lowered = child_path.name.lower()
        if lowered in excluded_names or "task08" in lowered and "aggregate" in lowered:
            continue
        for config_path in sorted(child_path.glob("*_configuration.json")):
            payload = _safe_stage_payload(config_path)
            if payload is not None:
                consume_payload(payload, str(child_path), child=True)
        # Some users retain only case-share ZIPs inside each numbered case
        # directory.  Inspect those shallowly without traversing deeper trees.
        for zip_path in sorted(child_path.glob("*.zip")):
            if not _candidate_zip_may_contain_project_data(zip_path):
                continue
            inspected_zips += 1
            zip_task07, zip_task05 = _stage_identities_from_zip(zip_path)
            child_task07.update(zip_task07)
            child_task05.update(zip_task05)
            if zip_task07:
                task07_containers.add(str(child_path))
            if zip_task05:
                task05_containers.add(str(child_path))

    unique_task07 = direct_task07 | child_task07
    unique_task05 = direct_task05 | child_task05
    has_authority_file = bool(
        list(candidate.glob("NUM_Task07_Final_Production_and_Task08_*Handoff*.md"))
        or list(candidate.glob("NUM_Open_System_PartI_Master_Audit_*.md"))
    )
    child_has_task07 = bool(child_task07)
    child_has_task05 = bool(child_task05)
    qualifies = bool(
        len(unique_task07) >= 2
        or (len(unique_task07) >= 1 and len(unique_task05) >= 1)
        or (child_has_task07 and has_authority_file)
    )
    if len(unique_task07) >= 2:
        reason = "contains at least two distinct Task-07 physical cases"
    elif len(unique_task07) >= 1 and len(unique_task05) >= 1:
        reason = "contains Task-07 cases and Task-05 reference cases as siblings"
    elif child_has_task07 and has_authority_file:
        reason = "contains child Task-07 data and the authoritative handoff/audit"
    elif len(unique_task07) == 1:
        reason = "contains only one unique Task-07 case; continue searching ancestors"
    else:
        reason = "no recognizable Task-07 aggregate data at this level"

    return {
        "path": str(candidate),
        "exists": True,
        "direct_Task07_unique_count": len(direct_task07),
        "child_Task07_unique_count": len(child_task07),
        "Task07_unique_count": len(unique_task07),
        "direct_Task05_unique_count": len(direct_task05),
        "child_Task05_unique_count": len(child_task05),
        "Task05_unique_count": len(unique_task05),
        "Task07_container_count": len(task07_containers),
        "Task05_container_count": len(task05_containers),
        "authority_file_present": has_authority_file,
        "inspected_configuration_count": inspected_configurations,
        "inspected_zip_count": inspected_zips,
        "qualifies_as_aggregate_root": qualifies,
        "selection_reason": reason,
    }


def _discover_task08_project_root(
    start: Optional[Path] = None,
) -> Tuple[Path, Dict[str, Any]]:
    """Return the nearest *aggregate* sibling-data root and diagnostics.

    A directory containing one completed Task-07 case is deliberately not an
    aggregate root, even when that directory also contains full/diagnostic ZIP
    mirrors.  The search therefore evaluates all ancestors until it finds a
    level containing distinct Task-07 cases, Task-05 siblings, or the authority
    files next to child Task-07 data.
    """
    origin = (Path.cwd() if start is None else Path(start)).expanduser().resolve()
    examined: List[Dict[str, Any]] = []
    direct_case_parent: Optional[Path] = None
    for distance, candidate in enumerate((origin, *origin.parents)):
        inventory = _shallow_task08_project_inventory(candidate)
        inventory["distance_from_start"] = distance
        examined.append(inventory)
        if (
            distance == 0
            and inventory.get("direct_Task07_unique_count", 0) >= 1
            and candidate.parent != candidate
        ):
            direct_case_parent = candidate.parent
        if inventory.get("qualifies_as_aggregate_root") is True:
            return candidate, {
                "start": str(origin),
                "selected_root": str(candidate),
                "selection_mode": "stage_metadata_sibling_aggregate",
                "selected_inventory": inventory,
                "examined_ancestors": examined,
            }

    # Conservative fallback for a notebook launched inside one case directory:
    # use its parent rather than trapping the aggregate audit inside that case.
    if direct_case_parent is not None and direct_case_parent.is_dir():
        fallback_inventory = _shallow_task08_project_inventory(direct_case_parent)
        return direct_case_parent, {
            "start": str(origin),
            "selected_root": str(direct_case_parent),
            "selection_mode": "single_case_parent_fallback",
            "selected_inventory": fallback_inventory,
            "examined_ancestors": examined,
        }

    return origin, {
        "start": str(origin),
        "selected_root": str(origin),
        "selection_mode": "working_directory_fallback",
        "selected_inventory": examined[0] if examined else {},
        "examined_ancestors": examined,
    }


def _nearest_task08_project_root(start: Optional[Path] = None) -> Path:
    root, _diagnostics = _discover_task08_project_root(start)
    return root

def _resolve_case_local_task07_root() -> Tuple[Path, Dict[str, Any]]:
    """Resolve a strict case-local Task-07 input directory for Jupyter.

    The previous notebook default deliberately searched ancestors until it found
    the common multi-case project root.  That behavior is correct for a final
    aggregate audit, but it makes copies launched in several case directories
    audit the same data tree.  Case-local notebook mode instead requires direct
    Task-07 evidence in the current directory and never substitutes an ancestor
    as the Task-07 input.

    Running from the already-created Task-08 output directory is also supported:
    its parent is tested as the case directory.  No other upward fallback is
    permitted, because silently accepting the project root would recreate the
    original ambiguity.
    """
    notebook_cwd = Path.cwd().expanduser().resolve()
    candidates: List[Path] = [notebook_cwd]
    if notebook_cwd.name == JUPYTER_DEFAULT_OUTPUT_DIRECTORY_NAME:
        candidates.append(notebook_cwd.parent)

    examined: List[Dict[str, Any]] = []
    for candidate in candidates:
        inventory = _shallow_task08_project_inventory(candidate)
        examined.append(inventory)
        direct_count = int(inventory.get("direct_Task07_unique_count", 0) or 0)
        if direct_count >= 1:
            return candidate, {
                "selection_mode": "strict_case_local_stage_metadata",
                "selected_root": str(candidate),
                "selected_inventory": inventory,
                "examined": examined,
            }

    raise RuntimeError(
        "Task-08 case-local Jupyter mode could not find direct Task-07 data in "
        f"the notebook working directory {notebook_cwd}. Copy/open the notebook "
        "inside the Stage-07 case directory that contains the case's "
        "*_configuration.json and raw products. The loader intentionally will "
        "not climb to the common project root for Task-07 input. To run the "
        "formal aggregate audit instead, set TASK08_INPUT_ROOT explicitly to "
        "the common project root."
    )


def _find_authority_file_by_hash(
    search_roots: Sequence[Path],
    patterns: Sequence[str],
    expected_sha256: str,
) -> Optional[Path]:
    """Return a shallow authority-file match with the exact frozen hash.

    Filenames on the cluster often acquire suffixes such as ``(2)`` or ``(9)``.
    Selection therefore uses a filename family only to enumerate candidates;
    the frozen SHA-256 decides whether a candidate is authoritative.
    """
    seen: Set[Path] = set()
    for root in search_roots:
        try:
            resolved_root = root.expanduser().resolve()
        except Exception:
            continue
        if not resolved_root.is_dir():
            continue
        for pattern in patterns:
            for candidate in sorted(resolved_root.glob(pattern)):
                try:
                    resolved = candidate.resolve()
                except Exception:
                    continue
                if resolved in seen or not resolved.is_file():
                    continue
                seen.add(resolved)
                try:
                    if sha256_file(resolved) == expected_sha256:
                        return resolved
                except OSError:
                    continue
    return None


def _jupyter_default_argv() -> List[str]:
    """Build visible case-local defaults for no-argument Jupyter execution.

    Only routing is changed.  The Task-08 discovery, hash verification, raw-array
    reconstruction, matrix-role mapping, family gates, and output schema remain
    exactly the same as in the aggregate loader.
    """
    explicit_task07_root = os.environ.get("TASK08_INPUT_ROOT")
    if explicit_task07_root:
        task07_root = Path(explicit_task07_root).expanduser().resolve()
        task07_diagnostics: Dict[str, Any] = {
            "selection_mode": "TASK08_INPUT_ROOT_environment_override",
            "selected_root": str(task07_root),
            "selected_inventory": _shallow_task08_project_inventory(task07_root),
        }
        case_root_for_output = Path.cwd().expanduser().resolve()
        if case_root_for_output.name == JUPYTER_DEFAULT_OUTPUT_DIRECTORY_NAME:
            case_root_for_output = case_root_for_output.parent
    else:
        task07_root, task07_diagnostics = _resolve_case_local_task07_root()
        case_root_for_output = task07_root

    # Task-05 references are intentionally discovered from the common sibling
    # project tree, independently of the case-local Task-07 input.
    explicit_task05_root = os.environ.get("TASK08_TASK05_INPUT_ROOT")
    if explicit_task05_root:
        task05_root = Path(explicit_task05_root).expanduser().resolve()
        task05_selection_mode = "TASK08_TASK05_INPUT_ROOT_environment_override"
        project_root = task05_root
        project_diagnostics: Dict[str, Any] = {
            "selected_root": str(project_root),
            "selection_mode": task05_selection_mode,
        }
    else:
        project_root, project_diagnostics = _discover_task08_project_root(task07_root)
        task05_root = project_root
        task05_selection_mode = str(
            project_diagnostics.get("selection_mode", "project_root_discovery")
        )

    default_output_dir = case_root_for_output / JUPYTER_DEFAULT_OUTPUT_DIRECTORY_NAME
    output_dir = Path(
        os.environ.get("TASK08_OUTPUT_DIR", str(default_output_dir))
    ).expanduser().resolve()

    argv = [
        "--input",
        str(task07_root),
        "--task05-input",
        str(task05_root),
        "--output-dir",
        str(output_dir),
    ]

    # Prefer explicit environment paths.  Otherwise, locate only exact-hash
    # authority copies at the case/project level; never select by filename alone.
    optional_environment_arguments = (
        ("TASK08_INHERITED_BOUNDS", "--inherited-bounds"),
        ("TASK08_MASTER_AUDIT", "--master-audit"),
        ("TASK08_HANDOFF", "--handoff"),
    )
    explicit_option_names: Set[str] = set()
    for environment_name, option_name in optional_environment_arguments:
        value = os.environ.get(environment_name)
        if value:
            argv.extend((option_name, str(Path(value).expanduser().resolve())))
            explicit_option_names.add(option_name)

    authority_search_roots = (task07_root, project_root, Path.cwd().resolve())
    master_path: Optional[Path] = None
    handoff_path: Optional[Path] = None
    if "--master-audit" not in explicit_option_names:
        master_path = _find_authority_file_by_hash(
            authority_search_roots,
            (
                "NUM_Open_System_PartI_Master_Audit_"
                "Audit00_to_Task06_Qualified_PASS_and_Task07_Handoff_2026-08-03*.md",
            ),
            MASTER_AUDIT_EXPECTED_SHA256,
        )
        if master_path is not None:
            argv.extend(("--master-audit", str(master_path)))
    if "--handoff" not in explicit_option_names:
        handoff_path = _find_authority_file_by_hash(
            authority_search_roots,
            (
                "NUM_Task07_Final_Production_and_Task08_"
                "Independent_Aggregate_Loader_Handoff_2026-08-06*.md",
            ),
            TASK07_TASK08_HANDOFF_EXPECTED_SHA256,
        )
        if handoff_path is not None:
            argv.extend(("--handoff", str(handoff_path)))

    inventory = task07_diagnostics.get("selected_inventory", {})
    print("[Task-08 Jupyter strict case-local selection]", flush=True)
    print(f"  notebook cwd:       {Path.cwd().resolve()}", flush=True)
    print(f"  Task-07 input:      {task07_root}", flush=True)
    print(
        f"  Task-07 selection:  {task07_diagnostics.get('selection_mode')}",
        flush=True,
    )
    print(
        "  direct case data:  "
        f"Task-07 unique={inventory.get('direct_Task07_unique_count', 0)}, "
        f"ZIPs inspected={inventory.get('inspected_zip_count', 0)}",
        flush=True,
    )
    print(f"  Task-05 input:      {task05_root}", flush=True)
    print(f"  Task-05 selection:  {task05_selection_mode}", flush=True)
    print(f"  output:             {output_dir}", flush=True)
    print(
        "  master audit:       "
        + (
            str(master_path)
            if master_path is not None
            else os.environ.get("TASK08_MASTER_AUDIT", "NOT AUTO-FOUND BY FROZEN HASH")
        ),
        flush=True,
    )
    print(
        "  Task-07/08 handoff: "
        + (
            str(handoff_path)
            if handoff_path is not None
            else os.environ.get("TASK08_HANDOFF", "NOT AUTO-FOUND BY FROZEN HASH")
        ),
        flush=True,
    )
    print(
        "  policy:             case-local incremental audit; absent matrix roles "
        "remain MISSING/PENDING; final family audit must still be run once on "
        "the common project root",
        flush=True,
    )
    return argv

def _effective_entry_argv(
    argv: Optional[Sequence[str]],
) -> Optional[List[str]]:
    """Resolve notebook kernel arguments without weakening terminal CLI rules."""
    if argv is not None:
        return list(argv)
    if not _running_under_ipykernel():
        return None

    raw = list(sys.argv[1:])
    task08_options = {
        "--input",
        "--task05-input",
        "--output-dir",
        "--inherited-bounds",
        "--master-audit",
        "--handoff",
        "--strict-reruns",
        "--allow-missing-per-case-loader",
        "--max-zip-member-bytes",
        "--self-test",
    }
    if any(item in task08_options for item in raw):
        return raw
    return _jupyter_default_argv()


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Independent read-only CPU Task-08 aggregate loader for the frozen "
            "D1-D5/U1-U5/P1-P5 Task-07 v8 response family."
        )
    )
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        help=(
            "Task-07 case directory, directory tree, or full case-share ZIP. "
            "Repeat for multiple roots."
        ),
    )
    parser.add_argument(
        "--task05-input",
        action="append",
        default=[],
        help=(
            "Optional Task-05/Task-06 directory or ZIP root for independent "
            "U1/U2/U3 launch-identity reconstruction."
        ),
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory receiving all Task-08 products.",
    )
    parser.add_argument(
        "--inherited-bounds",
        default=None,
        help=(
            "Optional JSON carrying nonzero inherited epsilon_repr and epsilon_z "
            "bounds globally or by direction."
        ),
    )
    parser.add_argument("--master-audit", default=None)
    parser.add_argument("--handoff", default=None)
    parser.add_argument(
        "--strict-reruns",
        action="store_true",
        help="Require deterministic same-prefix closure for all 15 cases.",
    )
    parser.add_argument(
        "--allow-missing-per-case-loader",
        action="store_true",
        help=(
            "Retain locally reconstructed cases as LOCAL_PASS diagnostics. This "
            "does not authorize a final physical claim without the per-case loader."
        ),
    )
    parser.add_argument(
        "--max-zip-member-bytes",
        type=int,
        default=2 * 1024 * 1024 * 1024,
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Generate and audit a reduced synthetic non-physical data family.",
    )
    args = parser.parse_args(argv)
    if not args.self_test and not args.input:
        parser.error("at least one --input is required unless --self-test is used")
    return args


def _print_task08_console_summary(summary: Mapping[str, Any]) -> None:
    """Print a compact but scientifically useful notebook/terminal report."""
    print("\n[Task-08 discovery]", flush=True)
    print(
        f"  Task-07 candidates:      {summary.get('Task07_candidate_count', 0)}",
        flush=True,
    )
    print(
        f"  Task-05 candidates:      {summary.get('Task05_candidate_count', 0)}",
        flush=True,
    )
    status_counts = summary.get("status_counts", {})
    if isinstance(status_counts, Mapping):
        print(
            "  matrix status counts:    "
            + ", ".join(
                f"{status}={status_counts.get(status, 0)}"
                for status in ALLOWED_CASE_STATUSES
            ),
            flush=True,
        )
    partial_count = int(summary.get("partial_or_in_progress_candidate_count", 0) or 0)
    if partial_count:
        print(
            f"  partial/in-progress:     {partial_count} candidate fragment(s); formal roles remain MISSING",
            flush=True,
        )
    mixed_count = int(summary.get("mixed_or_legacy_core_candidate_count", 0) or 0)
    if mixed_count:
        print(
            f"  mixed/legacy core:       {mixed_count} candidate(s) isolated",
            flush=True,
        )
        print(
            f"  required v8 core:        {FROZEN_TASK07_V8_NUMERICAL_CORE_SHA256}",
            flush=True,
        )

    print("\n[Task-08 D/U/P matrix]", flush=True)
    case_rows = summary.get("case_rows", [])
    if isinstance(case_rows, Sequence):
        for row in case_rows:
            if not isinstance(row, Mapping):
                continue
            matrix_id = str(row.get("matrix_id", "?"))
            status = str(row.get("status", "UNKNOWN"))
            scientific = "PASS" if row.get("scientific_admissible") else "PENDING"
            if status == STATUS_FAILED:
                scientific = "FAIL"
            chi_d = finite_float(row.get("chi_D"))
            norm = finite_float(row.get("complete_response_norm"))
            metric_text = ""
            if chi_d is not None or norm is not None:
                metric_text = (
                    f" | chi_D={chi_d:.6e}" if chi_d is not None else ""
                ) + (
                    f" | response_norm={norm:.6e}" if norm is not None else ""
                )
            print(
                f"  {matrix_id:>2}  {status:<14} scientific={scientific:<7}"
                f" rerun={'CLOSED' if row.get('rerun_closed') else 'PENDING'}"
                f"{metric_text}",
                flush=True,
            )
            failed = row.get("failed_checks", [])
            pending = row.get("pending_items", [])
            if status == STATUS_FAILED and failed:
                for item in list(failed)[:4]:
                    print(f"      FAIL: {item}", flush=True)
                if len(failed) > 4:
                    print(f"      ... {len(failed) - 4} additional failed checks", flush=True)
                if any("insertion_grid_factor_two_check" in str(item) for item in failed):
                    print(
                        "      action: insertion quadrature failed the frozen 5% gate; a finer insertion-grid run is required",
                        flush=True,
                    )
                if any("numerical_core_matches_frozen_v8" in str(item) for item in failed):
                    print(
                        "      action: this result cannot fill the formal matrix role without the frozen v8 numerical core",
                        flush=True,
                    )
            elif status in {STATUS_MISSING, STATUS_LOCAL_PASS, STATUS_RERUN_PENDING} and pending:
                for item in list(pending)[:2]:
                    print(f"      pending: {item}", flush=True)

    print("\n[Task-08 family gates]", flush=True)
    family_summary = summary.get("family_gate_summary", {})
    if isinstance(family_summary, Mapping):
        for direction in ("downward", "upward", "dephasing"):
            record = family_summary.get(direction, {})
            if not isinstance(record, Mapping):
                continue
            print(
                f"  {direction:<10} scalar={record.get('scalar_null', 'PENDING'):<7} "
                f"dt={record.get('time_step', 'PENDING'):<7} "
                f"shell={record.get('shell', 'PENDING'):<7} "
                f"evidence={record.get('evidence', EVIDENCE_BUDGET_INCOMPLETE)}",
                flush=True,
            )

    print("\n[Task-08 verdict]", flush=True)
    print(f"  scientific verdict:      {summary.get('scientific_verdict')}", flush=True)
    print(
        "  physical claim allowed:  "
        f"{summary.get('physical_zero_rate_susceptibility_claim_authorized')}",
        flush=True,
    )
    print(
        "  admissible cases:        "
        f"{summary.get('scientifically_admissible_case_count', 0)}/15",
        flush=True,
    )
    print(
        "  rerun coverage:          "
        f"{summary.get('reproducibility_closed_case_count', 0)}/15",
        flush=True,
    )
    if summary.get("scientific_verdict") == "INCOMPLETE_REQUIRED_CASE_MATRIX":
        print(
            "  interpretation:         incremental audit completed; exit code 3 "
            "means missing family data, not a loader failure",
            flush=True,
        )

    print("\n[Task-08 outputs]", flush=True)
    for label, key in (
        ("aggregate report", "aggregate_report"),
        ("case register", "case_identity_table"),
        ("per-case metrics", "per_case_metrics"),
        ("full share ZIP", "share_zip"),
        ("diagnostic ZIP", "diagnostic_share_zip"),
        ("output directory", "output_directory"),
    ):
        value = summary.get(key)
        if value:
            print(f"  {label:<19} {value}", flush=True)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(_effective_entry_argv(argv))
    if args.self_test:
        code, report = run_synthetic_self_test(args.output_dir)
        print("\n[Task-08 synthetic self-test]")
        print(f"  passed:          {report['passed']}")
        print(f"  output:          {Path(args.output_dir).expanduser().resolve()}")
        return int(code)
    code, summary = run_task08(
        input_paths=args.input,
        task05_input_paths=args.task05_input,
        output_dir=args.output_dir,
        inherited_bounds_path=args.inherited_bounds,
        master_audit_path=args.master_audit,
        handoff_path=args.handoff,
        strict_reruns=args.strict_reruns,
        allow_missing_per_case_loader=args.allow_missing_per_case_loader,
        max_zip_member_bytes=args.max_zip_member_bytes,
    )
    _print_task08_console_summary(summary)
    return int(code)


if __name__ == "__main__":
    _task08_exit_code = main()
    if _running_under_ipykernel():
        print(f"\nTask-08 aggregate-loader exit code: {_task08_exit_code}")
    else:
        raise SystemExit(_task08_exit_code)