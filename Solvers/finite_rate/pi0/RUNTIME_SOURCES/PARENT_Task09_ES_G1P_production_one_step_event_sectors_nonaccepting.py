#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task09_ES_G1P_production_one_step_event_sectors_nonaccepting.py
================================================================

Second gate of the Task-09 exact-event-sector lineage.

This source executes exactly one complete production-size Strang step for the
frozen U2 strong-confinement spinor model at lambda_0/4 and lambda_0/8, plus a
zero-rate detector reference. It is a non-accepting representation/backend
certification only.

The source imports an immutable copy of the terminal CSSF source only as a
read-only authority library for the already frozen oscillator, detector,
finite bath map, Batch-64 GMRES, grid, packet, and midpoint click routines. It
never calls the CSSF propagator, compression, repair, budget, checkpoint, or
continuation routines.

No production trajectory, U2-I physical comparison, Task-10 authorization, or
finite-rate physical claim is enabled.
"""

from __future__ import annotations

import argparse
import ast
import fcntl
import hashlib
import importlib.util
import json
import math
import os
import shutil
import sys
import time
import traceback
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

import numpy as np


# TASK-09 ES-G1P NUMERICAL CORE BEGINS HERE
NUMERICAL_CORE_MARKER = "# TASK-09 ES-G1P NUMERICAL CORE BEGINS HERE"

SCRIPT_VERSION = "2026-08-15-task09-es-g1p-production-one-step-event-sectors-nonaccepting-v1"
REPORT_SCHEMA = "2026-08-15-task09-es-g1p-production-one-step-report-v1"
PRODUCT_SCHEMA = "2026-08-15-task09-es-g1p-production-one-step-products-v1"
AUDIT_SCHEMA = "2026-08-15-task09-es-g1p-parent-scope-audit-v1"

PRODUCTION_AUTHORIZED = False
ACCEPTANCE_ENABLED = False
TASK10_ELIGIBLE = False
FINITE_POSITIVE_RATE_PHYSICAL_CLAIM = False
U2I_PHYSICAL_COMPARISON_PERFORMED = False
CSSF_CHECKPOINT_IMPORT_ENABLED = False
CSSF_PROPAGATION_ENABLED = False
AUTOMATIC_SWEEP_ENABLED = False

PARENT_SOURCE_NAME = (
    "Task09_4901_U2_low_v4_nonaccepting_"
    "D2PR2G1FMP_BATCH64_REPAIRED_RANK_WHOLEHALF_G0.py"
)
PARENT_SOURCE_SHA256 = "d0bcd5af9b12b4d21ec897b87151006a1d9e1a7e035172ddf73c1c41c8a111c7"
PARENT_CORE_SHA256 = "fcf82f3344cd2190efb465b82ec669c1da7270ab48e926b037f7f799bca6cc45"
PARENT_CORE_MARKER = "# TASK-09 V4 NUMERICAL CORE BEGINS HERE"
PARENT_G0R_ARCHIVE_NAME = "PARENT_Task09_ES_G0R_Reduced_Result_9422289.zip"
PARENT_G0R_ARCHIVE_SHA256 = "0216f7385f3c2b3f94f981c23a819529bf05570eb434014850145d69780c72ea"
PARENT_G0R_SOURCE_SHA256 = "cd9099053ae37b5c16aa0948b6868064fd1d3500d638a0cdcf222dbc8ab9ffc1"
PARENT_G0R_CORE_SHA256 = "0f00c20e795d9395b293a964d45e10b14b21e181471aa9aeadb3f6aec6911dee"
PARENT_G0R_VERDICT = "PASS_TASK09_ES_G0R_REDUCED_NONACCEPTING"
PARENT_G0R_AUDIT_VERDICT = "PASS_TASK09_ES_G0R_INDEPENDENT_ARTIFACT_AUDIT"
PARENT_G3_FAILURE_SHA256 = "70af5f3eca34ca15130a1d303c527b3e0cea9932ba89266a28f6c227d8bbbfa7"
PARENT_G3_FAILURE_CLASSIFICATION = "NO_ADMISSIBLE_REPAIRED_RANK"

LAMBDA_0 = math.pi / 400.0
LAMBDA_QUARTER = LAMBDA_0 / 4.0
LAMBDA_EIGHTH = LAMBDA_0 / 8.0
RATE_CASES = (
    ("zero", 0.0),
    ("lambda0_over_8", LAMBDA_EIGHTH),
    ("lambda0_over_4", LAMBDA_QUARTER),
)

# Exact production-size U2 model.
N_SHELL = 12
N_Z = 1500
L_Z = 20.0
OMEGA = 100.0
DT = 5.0e-4
Z0 = 10.0
SIGMA_Z_AMPLITUDE = 0.5
K0 = math.pi
KAPPA = math.pi
THETA = math.pi / 6.0
PHI = 0.0
DETECTOR_BATCH_COLUMNS = 64
ONE_COMPLETE_STEP = 1
MAX_EVENT_SECTOR = 2  # all events possible in one Strang step

# No intentional physical compression budget is spent in this gate. Only
# numerically null support can be removed, and every positive removed trace is
# recorded without restoration.
SUPPORT_FLOOR_FACTOR = 4096.0
MAX_REPRESENTATION_LEDGER = 1.0e-10

# Numerical gates.
PARENT_SCOPE_TOL = 0.0
OPERATOR_TOL = 2.0e-12
BATH_COMPLETENESS_TOL = 2.0e-12
TRUE_RESIDUAL_TOL = 1.0e-8
MULTI_VS_INDEPENDENT_REL_TOL = 5.0e-8
MIDPOINT_CROSSCHECK_ABS_TOL = 5.0e-10
DETECTOR_CLOSURE_ABS_TOL = 5.0e-9
BATH_TRACE_ABS_TOL = 5.0e-10
HISTORY_SECTOR_TRACE_NORM_TOL = 5.0e-10
LEDGER_TRACE_NORM_TOL = 5.0e-9
LEDGER_LAW_TOL = 5.0e-9
COMPRESSION_TRACE_IDENTITY_TOL = 5.0e-11
NEGATIVE_GRAM_GUARD_TOL = 5.0e-12
NONNEGATIVITY_TOL = 5.0e-12

ALLOWED_PARENT_SYMBOLS = {
    "RunConfig",
    "NumericalBackend",
    "build_oscillator_operators",
    "build_reference_grid",
    "build_initial_state",
    "build_propagator_objects",
    "build_bath_kraus",
    "advance_many_spinor",
}
FORBIDDEN_PARENT_CALL_FRAGMENTS = (
    "compress",
    "canonical",
    "repair",
    "budget",
    "checkpoint",
    "propagate_complete",
    "run_g",
    "run_production",
    "resume",
    "telemetry",
)


class GateBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class GateConfig:
    backend: str
    data_root: Path
    output_dir: Path
    n_shell: int = N_SHELL
    n_z: int = N_Z
    l_z: float = L_Z
    omega: float = OMEGA
    dt: float = DT
    z0: float = Z0
    sigma_z: float = SIGMA_Z_AMPLITUDE
    k0: float = K0
    kappa: float = KAPPA
    theta: float = THETA
    phi: float = PHI
    detector_batch_columns: int = DETECTOR_BATCH_COLUMNS

    @property
    def state_dimension(self) -> int:
        modes = (self.n_shell + 1) * (self.n_shell + 2) // 2
        return 2 * modes * self.n_z


@dataclass
class CompressionRecord:
    sector: int
    input_columns: int
    retained_rank: int
    input_trace: float
    output_trace: float
    discarded_positive_trace: float
    negative_eigenvalue_guard: float
    support_floor: float
    minimum_gram_eigenvalue: float
    maximum_gram_eigenvalue: float
    trace_identity_residual: float
    trace_restoration_applied: bool = False


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(chunk_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def sha256_core(path: Path, marker: str) -> str:
    text = path.read_text(encoding="utf-8", errors="strict").replace("\r\n", "\n")
    if marker not in text:
        raise GateBlocked(f"Numerical-core marker missing in {path.name}: {marker}")
    core = text.split(marker, 1)[1]
    return hashlib.sha256(core.encode("utf-8")).hexdigest()


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False, default=json_default)
        handle.write("\n")
    os.replace(tmp, path)


def atomic_savez(path: Path, **arrays: np.ndarray) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("wb") as handle:
        np.savez(handle, **arrays)
    os.replace(tmp, path)


def json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(type(value).__name__)


def verify_parent_g0r(package_dir: Path) -> Dict[str, Any]:
    archive = package_dir / PARENT_G0R_ARCHIVE_NAME
    if sha256_file(archive) != PARENT_G0R_ARCHIVE_SHA256:
        raise GateBlocked("Embedded ES-G0R result archive hash mismatch")
    with zipfile.ZipFile(archive, "r") as handle:
        bad = handle.testzip()
        if bad is not None:
            raise GateBlocked(f"Embedded ES-G0R archive CRC failure: {bad}")
        names = handle.namelist()
        gate_name = next((name for name in names if name.endswith("/gate_report.json")), None)
        audit_name = next((name for name in names if name.endswith("/independent_audit.json")), None)
        source_name = next(
            (name for name in names if name.endswith("/Task09_ES_G0R_reduced_event_sectors_nonaccepting.py")),
            None,
        )
        if not gate_name or not audit_name or not source_name:
            raise GateBlocked("Embedded ES-G0R archive is missing required evidence")
        gate = json.loads(handle.read(gate_name))
        audit = json.loads(handle.read(audit_name))
        source_hash = hashlib.sha256(handle.read(source_name)).hexdigest()
    passed = bool(
        gate.get("verdict") == PARENT_G0R_VERDICT
        and gate.get("passed") is True
        and audit.get("verdict") == PARENT_G0R_AUDIT_VERDICT
        and audit.get("passed") is True
        and source_hash == PARENT_G0R_SOURCE_SHA256
        and gate.get("numerical_core_sha256") == PARENT_G0R_CORE_SHA256
        and gate.get("claim_boundary", {}).get("production_authorized") is False
        and gate.get("claim_boundary", {}).get("task10_eligible") is False
        and gate.get("claim_boundary", {}).get("finite_positive_rate_physical_claim") is False
    )
    if not passed:
        raise GateBlocked("Embedded ES-G0R parent evidence did not pass the frozen contract")
    return {
        "archive_sha256": PARENT_G0R_ARCHIVE_SHA256,
        "solver_source_sha256": source_hash,
        "numerical_core_sha256": gate["numerical_core_sha256"],
        "solver_verdict": gate["verdict"],
        "independent_audit_verdict": audit["verdict"],
        "passed": True,
    }


def source_parent_call_audit(script_path: Path) -> Dict[str, Any]:
    tree = ast.parse(script_path.read_text(encoding="utf-8"), filename=str(script_path))
    parent_calls: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "parent":
                parent_calls.append(node.func.attr)
    forbidden = sorted(
        name for name in parent_calls
        if any(fragment in name.lower() for fragment in FORBIDDEN_PARENT_CALL_FRAGMENTS)
    )
    nonallowed = sorted(set(parent_calls) - ALLOWED_PARENT_SYMBOLS)
    passed = not forbidden and not nonallowed
    return {
        "parent_attribute_calls": sorted(set(parent_calls)),
        "allowed_parent_symbols": sorted(ALLOWED_PARENT_SYMBOLS),
        "forbidden_parent_calls": forbidden,
        "nonallowlisted_parent_calls": nonallowed,
        "cssf_propagation_compression_repair_budget_checkpoint_calls_absent": passed,
        "passed": passed,
    }


def load_parent(package_dir: Path) -> Tuple[Any, Dict[str, Any]]:
    source = package_dir / PARENT_SOURCE_NAME
    source_hash = sha256_file(source)
    core_hash = sha256_core(source, PARENT_CORE_MARKER)
    if source_hash != PARENT_SOURCE_SHA256 or core_hash != PARENT_CORE_SHA256:
        raise GateBlocked("Frozen parent source or numerical-core hash mismatch")

    safe_environment = {
        "TASK09_V4_GATE": "V4-G0",
        "TASK09_V4_BACKEND": "scipy",
        "TASK09_V4_RESUME": "0",
        "TASK09_D2_POST_G0_REVIEW": "0",
    }
    previous = {key: os.environ.get(key) for key in safe_environment}
    os.environ.update(safe_environment)
    try:
        spec = importlib.util.spec_from_file_location("task09_es_g1p_parent_authority", source)
        if spec is None or spec.loader is None:
            raise GateBlocked("Could not construct frozen parent module spec")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    frozen_flags = bool(
        module.PRODUCTION_AUTHORIZED is False
        and module.ACCEPTANCE_ENABLED is False
        and module.TASK10_ELIGIBLE is False
        and module.FINITE_POSITIVE_RATE_PHYSICAL_CLAIM is False
        and module.LEGACY_CHECKPOINT_IMPORT_ENABLED is False
        and module.CHECKPOINT_MIGRATION_ENABLED is False
        and module.AUTOMATIC_SWEEP_ENABLED is False
    )
    physical_constants = bool(
        module.PROPAGATOR_TYPE == "spinor"
        and module.ENVIRONMENT_DIRECTION == "upward"
        and module.INITIAL_MODE == "00"
        and module.N_SHELL == N_SHELL
        and module.N_Z == N_Z
        and module.L_Z == L_Z
        and module.DT == DT
        and module.OMEGA == OMEGA
        and module.GMRES_RTOL == 1.0e-10
        and module.GMRES_ATOL == 0.0
        and module.GMRES_RESTART == 30
        and module.GMRES_MAXITER == 1000
        and module.DETECTOR_RHS_BATCH_COLUMNS == DETECTOR_BATCH_COLUMNS
    )
    if not frozen_flags or not physical_constants:
        raise GateBlocked("Frozen parent authority flags or physical constants changed")
    return module, {
        "source_sha256": source_hash,
        "numerical_core_sha256": core_hash,
        "nonaccepting_flags_frozen": frozen_flags,
        "physical_and_gmres_constants_exact": physical_constants,
        "imported_as_read_only_authority_library": True,
    }


def physical_trace(factor: Any, h_z: float, backend: Any) -> float:
    value = h_z * backend.xp.sum(factor.real * factor.real + factor.imag * factor.imag)
    return backend.scalar_float(value)


def family_trace(family: Mapping[int, Any], h_z: float, backend: Any) -> float:
    return float(math.fsum(physical_trace(factor, h_z, backend) for factor in family.values()))


def combine_family(family: Mapping[int, Any], backend: Any) -> Tuple[Any, List[int], List[int]]:
    sectors = sorted(family)
    widths = [int(family[sector].shape[1]) for sector in sectors]
    if not sectors:
        raise RuntimeError("Cannot combine an empty factor family")
    return backend.xp.ascontiguousarray(
        backend.xp.concatenate([family[sector] for sector in sectors], axis=1)
    ), sectors, widths


def split_family(matrix: Any, sectors: Sequence[int], widths: Sequence[int]) -> Dict[int, Any]:
    result: Dict[int, Any] = {}
    offset = 0
    for sector, width in zip(sectors, widths):
        result[int(sector)] = matrix[:, offset : offset + width]
        offset += width
    return result


def apply_kraus(
    operator: Any, factor: Any, d_channels: int, n_z: int, backend: Any
) -> Any:
    rank = int(factor.shape[1])
    shaped = factor.reshape(d_channels, n_z * rank)
    mapped = operator @ shaped
    return backend.xp.ascontiguousarray(mapped.reshape(d_channels * n_z, rank))


def nonzero_factor(factor: Any, h_z: float, backend: Any) -> bool:
    return physical_trace(factor, h_z, backend) > np.finfo(float).tiny


def bath_half_uncompressed(
    family: Mapping[int, Any], kraus: Sequence[Any], h_z: float, backend: Any,
    d_channels: int, n_z: int
) -> Dict[int, Any]:
    k0, kx, ky = kraus
    pieces: MutableMapping[int, List[Any]] = {}
    for sector, factor in family.items():
        for increment, operator in ((0, k0), (1, kx), (1, ky)):
            mapped = apply_kraus(operator, factor, d_channels, n_z, backend)
            if nonzero_factor(mapped, h_z, backend):
                pieces.setdefault(int(sector + increment), []).append(mapped)
    return {
        sector: backend.xp.ascontiguousarray(backend.xp.concatenate(blocks, axis=1))
        for sector, blocks in pieces.items()
    }


def direct_history_second_half(
    first_labels: Sequence[Tuple[str, int]], detector_output: Any,
    kraus: Sequence[Any], h_z: float, backend: Any, d_channels: int, n_z: int
) -> Dict[int, Any]:
    kraus_labels = (("0", 0, kraus[0]), ("x", 1, kraus[1]), ("y", 1, kraus[2]))
    pieces: MutableMapping[int, List[Any]] = {}
    for column, (_first_name, first_count) in enumerate(first_labels):
        vector = detector_output[:, column : column + 1]
        for _second_name, second_count, operator in kraus_labels:
            mapped = apply_kraus(operator, vector, d_channels, n_z, backend)
            if nonzero_factor(mapped, h_z, backend):
                pieces.setdefault(first_count + second_count, []).append(mapped)
    return {
        sector: backend.xp.ascontiguousarray(backend.xp.concatenate(blocks, axis=1))
        for sector, blocks in pieces.items()
    }


def first_half_with_labels(
    psi: Any, kraus: Sequence[Any], h_z: float, backend: Any,
    d_channels: int, n_z: int
) -> Tuple[Dict[int, Any], List[Tuple[str, int]]] :
    pieces: MutableMapping[int, List[Any]] = {}
    labels: List[Tuple[str, int]] = []
    for name, count, operator in (("0", 0, kraus[0]), ("x", 1, kraus[1]), ("y", 1, kraus[2])):
        mapped = apply_kraus(operator, psi, d_channels, n_z, backend)
        if nonzero_factor(mapped, h_z, backend):
            pieces.setdefault(count, []).append(mapped)
            labels.extend([(name, count)] * int(mapped.shape[1]))
    family = {
        sector: backend.xp.ascontiguousarray(backend.xp.concatenate(blocks, axis=1))
        for sector, blocks in pieces.items()
    }
    # combine_family uses sector order; rebuild labels in that order.
    ordered_labels: List[Tuple[str, int]] = []
    for sector in sorted(family):
        ordered_labels.extend([label for label in labels if label[1] == sector])
    return family, ordered_labels


def compress_factor_no_restore(
    factor: Any, sector: int, h_z: float, backend: Any
) -> Tuple[Any, CompressionRecord]:
    columns = int(factor.shape[1])
    if columns == 0:
        raise RuntimeError("Empty factor passed to compression")
    gram_backend = h_z * (factor.conj().T @ factor)
    gram = np.asarray(backend.to_cpu(gram_backend), dtype=np.complex128)
    gram = 0.5 * (gram + gram.conj().T)
    values, vectors = np.linalg.eigh(gram)
    minimum = float(np.min(values))
    maximum = float(np.max(values))
    support_floor = float(
        SUPPORT_FLOOR_FACTOR
        * np.finfo(float).eps
        * max(1, columns)
        * max(1.0, maximum)
    )
    negative_guard = float(np.sum(np.maximum(-values, 0.0), dtype=np.float64))
    positive = np.maximum(values, 0.0)
    keep = positive > support_floor
    if not np.any(keep) and float(np.sum(positive)) > 0.0:
        keep[int(np.argmax(positive))] = True
    discard = float(np.sum(positive[~keep], dtype=np.float64))
    transform = backend.to_backend_array(np.asarray(vectors[:, keep], dtype=np.complex128))
    output = backend.xp.ascontiguousarray(factor @ transform)
    input_trace = physical_trace(factor, h_z, backend)
    output_trace = physical_trace(output, h_z, backend)
    trace_residual = float(input_trace - output_trace - discard)
    record = CompressionRecord(
        sector=int(sector),
        input_columns=columns,
        retained_rank=int(output.shape[1]),
        input_trace=input_trace,
        output_trace=output_trace,
        discarded_positive_trace=discard,
        negative_eigenvalue_guard=negative_guard,
        support_floor=support_floor,
        minimum_gram_eigenvalue=minimum,
        maximum_gram_eigenvalue=maximum,
        trace_identity_residual=trace_residual,
        trace_restoration_applied=False,
    )
    return output, record


def compress_family_no_restore(
    family: Mapping[int, Any], h_z: float, backend: Any
) -> Tuple[Dict[int, Any], float, List[CompressionRecord]]:
    output: Dict[int, Any] = {}
    ledger = 0.0
    records: List[CompressionRecord] = []
    for sector in sorted(family):
        compressed, record = compress_factor_no_restore(family[sector], sector, h_z, backend)
        output[sector] = compressed
        ledger += record.discarded_positive_trace
        records.append(record)
    return output, float(ledger), records


def family_matrix(family: Mapping[int, Any], backend: Any, n_rows: int) -> Any:
    if not family:
        return backend.xp.empty((n_rows, 0), dtype=backend.complex128)
    return backend.xp.ascontiguousarray(
        backend.xp.concatenate([family[sector] for sector in sorted(family)], axis=1)
    )


def density_trace_norm_difference(
    left: Mapping[int, Any], right: Mapping[int, Any],
    h_z: float, backend: Any, n_rows: int
) -> float:
    """Trace norm of XX^dagger-YY^dagger from a stable thin QR.

    For Z=[X,Y] and J=diag(I,-I), sqrt(h_z) Z = Q R gives
    h_z(XX^dagger-YY^dagger)=Q (R J R^dagger) Q^dagger.  The
    nonzero eigenvalues are therefore those of the small Hermitian matrix
    R J R^dagger.  No support floor is used, which is essential when the
    certified difference is much smaller than the individual factors.
    """
    x = family_matrix(left, backend, n_rows)
    y = family_matrix(right, backend, n_rows)
    z = backend.xp.ascontiguousarray(
        math.sqrt(h_z) * backend.xp.concatenate([x, y], axis=1)
    )
    _q, r = backend.xp.linalg.qr(z, mode="reduced")
    signs = backend.xp.asarray(
        np.concatenate([np.ones(x.shape[1]), -np.ones(y.shape[1])]),
        dtype=backend.xp.float64,
    )
    small = (r * signs[None, :]) @ r.conj().T
    small_cpu = np.asarray(backend.to_cpu(small), dtype=np.complex128)
    small_cpu = 0.5 * (small_cpu + small_cpu.conj().T)
    return float(np.sum(np.abs(np.linalg.eigvalsh(small_cpu)), dtype=np.float64))


def run_detector(
    family: Mapping[int, Any], *, parent: Any, operators: Any,
    config: Any, propagator: Any, backend: Any, crosscheck_independent: bool
) -> Tuple[Dict[int, Any], float, Dict[str, Any], Any]:
    combined, sectors, widths = combine_family(family, backend)
    trace_before = physical_trace(combined, propagator.h_z, backend)
    advanced, q_roof, infos, residuals, iterations = parent.advance_many_spinor(
        combined,
        backend=backend,
        propagator=propagator,
        config=config,
        operators=operators,
        certified_multi_rhs=True,
    )
    click = float(config.dt * config.kappa * backend.abs2_sum(q_roof))
    trace_after = physical_trace(advanced, propagator.h_z, backend)
    independent_relative = 0.0
    midpoint_difference = 0.0
    independent_info: List[int] = []
    independent_residuals: List[float] = []
    if crosscheck_independent:
        independent, q_ind, info_ind, residual_ind, _ = parent.advance_many_spinor(
            combined,
            backend=backend,
            propagator=propagator,
            config=config,
            operators=operators,
            certified_multi_rhs=False,
        )
        scale = max(math.sqrt(propagator.h_z) * backend.norm(independent), np.finfo(float).tiny)
        independent_relative = math.sqrt(propagator.h_z) * backend.norm(advanced - independent) / scale
        click_ind = float(config.dt * config.kappa * backend.abs2_sum(q_ind))
        midpoint_difference = abs(click - click_ind)
        independent_info = np.asarray(info_ind, dtype=np.int32).tolist()
        independent_residuals = np.asarray(residual_ind, dtype=np.float64).tolist()
    audit = {
        "number_rhs": int(combined.shape[1]),
        "batch_columns": int(config.detector_rhs_batch_columns),
        "multi_rhs_info": np.asarray(infos, dtype=np.int32).tolist(),
        "maximum_multi_rhs_true_residual": float(np.max(residuals)) if len(residuals) else 0.0,
        "multi_rhs_inner_iterations": int(iterations),
        "independent_info": independent_info,
        "maximum_independent_true_residual": max(independent_residuals, default=0.0),
        "multi_rhs_vs_independent_relative_error": float(independent_relative),
        "midpoint_probability_multi_rhs": click,
        "midpoint_probability_absolute_difference": float(midpoint_difference),
        "trace_before_detector": trace_before,
        "trace_after_detector": trace_after,
        "detector_midpoint_closure": float(trace_before - trace_after - click),
    }
    return split_family(advanced, sectors, widths), click, audit, advanced


def sector_traces_and_ranks(family: Mapping[int, Any], h_z: float, backend: Any) -> Tuple[np.ndarray, np.ndarray]:
    traces = np.zeros(MAX_EVENT_SECTOR + 1, dtype=np.float64)
    ranks = np.zeros(MAX_EVENT_SECTOR + 1, dtype=np.int64)
    for sector, factor in family.items():
        if sector > MAX_EVENT_SECTOR:
            raise RuntimeError(f"Unexpected event sector {sector} in one-step gate")
        traces[sector] = physical_trace(factor, h_z, backend)
        ranks[sector] = int(factor.shape[1])
    return traces, ranks


def top_shell_population(family: Mapping[int, Any], operators: Any, config: Any, h_z: float, backend: Any) -> float:
    total = np.zeros(operators.d_channels, dtype=np.float64)
    for factor in family.values():
        rank = int(factor.shape[1])
        shaped = factor.reshape(operators.d_channels, config.n_z * rank)
        values = h_z * backend.xp.sum(shaped.real * shaped.real + shaped.imag * shaped.imag, axis=1)
        total += np.asarray(backend.to_cpu(values), dtype=np.float64)
    mode = total.reshape(2, operators.m_modes).sum(axis=0)
    return float(np.sum(mode[operators.shell_of_mode == config.n_shell], dtype=np.float64))


def one_rate_case(
    label: str, rate: float, *, parent: Any, operators: Any, propagator: Any,
    backend: Any, gate_config: GateConfig
) -> Dict[str, Any]:
    parent_config = parent.RunConfig(
        execution_gate="ES-G1P",
        backend=gate_config.backend,
        n_shell=gate_config.n_shell,
        n_z=gate_config.n_z,
        l_z=gate_config.l_z,
        dt=gate_config.dt,
        t_final=gate_config.dt,
        stop_after_steps=1,
        rate_lambda=rate,
        z0=gate_config.z0,
        sigma_z_amplitude=gate_config.sigma_z,
        k0=gate_config.k0,
        kappa=gate_config.kappa,
        theta=gate_config.theta,
        phi=gate_config.phi,
        detector_rhs_batch_columns=gate_config.detector_batch_columns,
        factor_block_columns=gate_config.detector_batch_columns,
        resume_from_checkpoint=False,
        representation_budget=0.0,
        planned_compression_calls=2,
        output_root=gate_config.output_dir,
    )
    initial_cpu = parent.build_initial_state(parent_config, operators, propagator.z, propagator.h_z)
    initial = backend.to_backend_array(initial_cpu[:, None])
    bath = parent.build_bath_kraus(
        operators,
        "upward",
        rate * gate_config.dt / 2.0,
        backend,
    )
    kraus = bath.operators_backend

    exact_first, first_labels = first_half_with_labels(
        initial, kraus, propagator.h_z, backend, operators.d_channels, parent_config.n_z
    )
    trace_initial = physical_trace(initial, propagator.h_z, backend)
    trace_first = family_trace(exact_first, propagator.h_z, backend)
    exact_detector, click_exact, detector_audit, detector_matrix = run_detector(
        exact_first,
        parent=parent,
        operators=operators,
        config=parent_config,
        propagator=propagator,
        backend=backend,
        crosscheck_independent=True,
    )
    exact_second = bath_half_uncompressed(
        exact_detector, kraus, propagator.h_z, backend, operators.d_channels, parent_config.n_z
    )
    direct_histories = direct_history_second_half(
        first_labels, detector_matrix, kraus, propagator.h_z, backend,
        operators.d_channels, parent_config.n_z
    )
    history_sector_error = density_trace_norm_difference(
        exact_second, direct_histories, propagator.h_z, backend, gate_config.state_dimension
    )
    trace_detector = family_trace(exact_detector, propagator.h_z, backend)
    trace_final = family_trace(exact_second, propagator.h_z, backend)

    compressed_first, ledger_first, records_first = compress_family_no_restore(
        exact_first, propagator.h_z, backend
    )
    compressed_detector, click_compressed, detector_compressed_audit, _ = run_detector(
        compressed_first,
        parent=parent,
        operators=operators,
        config=parent_config,
        propagator=propagator,
        backend=backend,
        crosscheck_independent=False,
    )
    compressed_second_raw = bath_half_uncompressed(
        compressed_detector, kraus, propagator.h_z, backend,
        operators.d_channels, parent_config.n_z
    )
    compressed_second, ledger_second, records_second = compress_family_no_restore(
        compressed_second_raw, propagator.h_z, backend
    )
    representation_ledger = float(ledger_first + ledger_second)
    compressed_final_trace = family_trace(compressed_second, propagator.h_z, backend)
    density_error = density_trace_norm_difference(
        exact_second, compressed_second, propagator.h_z, backend, gate_config.state_dimension
    )
    law_l1_error = float(abs(click_exact - click_compressed) + abs(trace_final - compressed_final_trace))

    sector_traces, sector_ranks = sector_traces_and_ranks(exact_second, propagator.h_z, backend)
    compressed_sector_traces, compressed_sector_ranks = sector_traces_and_ranks(
        compressed_second, propagator.h_z, backend
    )
    compression_records = [record.__dict__ for record in records_first + records_second]
    maximum_trace_identity = max(
        (abs(record.trace_identity_residual) for record in records_first + records_second),
        default=0.0,
    )
    maximum_negative_guard = max(
        (record.negative_eigenvalue_guard for record in records_first + records_second),
        default=0.0,
    )
    any_trace_restore = any(record.trace_restoration_applied for record in records_first + records_second)
    top_shell = top_shell_population(exact_second, operators, parent_config, propagator.h_z, backend)

    checks = {
        "initial_normalization": abs(trace_initial - 1.0) <= 5.0e-13,
        "bath_completeness": bath.completeness_residual <= BATH_COMPLETENESS_TOL,
        "first_bath_trace_preservation": abs(trace_first - trace_initial) <= BATH_TRACE_ABS_TOL,
        "second_bath_trace_preservation": abs(trace_final - trace_detector) <= BATH_TRACE_ABS_TOL,
        "multi_rhs_gmres": (
            not any(detector_audit["multi_rhs_info"])
            and detector_audit["maximum_multi_rhs_true_residual"] <= TRUE_RESIDUAL_TOL
        ),
        "independent_gmres": (
            not any(detector_audit["independent_info"])
            and detector_audit["maximum_independent_true_residual"] <= TRUE_RESIDUAL_TOL
        ),
        "batch64_vs_independent": (
            detector_audit["multi_rhs_vs_independent_relative_error"] <= MULTI_VS_INDEPENDENT_REL_TOL
            and detector_audit["midpoint_probability_absolute_difference"] <= MIDPOINT_CROSSCHECK_ABS_TOL
        ),
        "detector_midpoint_closure": abs(detector_audit["detector_midpoint_closure"]) <= DETECTOR_CLOSURE_ABS_TOL,
        "complete_step_probability_closure": abs(trace_initial - trace_final - click_exact) <= DETECTOR_CLOSURE_ABS_TOL,
        "history_sector_equivalence": history_sector_error <= HISTORY_SECTOR_TRACE_NORM_TOL,
        "all_one_step_event_sectors_retained": set(exact_second).issubset({0, 1, 2}),
        "no_trace_restoration": not any_trace_restore,
        "compression_trace_identity": maximum_trace_identity <= COMPRESSION_TRACE_IDENTITY_TOL,
        "gram_negative_guard": maximum_negative_guard <= NEGATIVE_GRAM_GUARD_TOL,
        "representation_ledger": representation_ledger <= MAX_REPRESENTATION_LEDGER,
        "compressed_density_bounded": density_error <= representation_ledger + LEDGER_TRACE_NORM_TOL,
        "compressed_complete_law_bounded": law_l1_error <= representation_ledger + LEDGER_LAW_TOL,
        "click_nonnegative": min(click_exact, click_compressed) >= -NONNEGATIVITY_TOL,
        "survival_nonnegative": min(trace_final, compressed_final_trace) >= -NONNEGATIVITY_TOL,
    }
    return {
        "label": label,
        "rate": rate,
        "action_per_bath_half": rate * gate_config.dt / 2.0,
        "checks": checks,
        "passed": all(checks.values()),
        "bath_completeness_residual": bath.completeness_residual,
        "trace_initial": trace_initial,
        "trace_after_first_bath": trace_first,
        "trace_after_detector": trace_detector,
        "trace_final_exact": trace_final,
        "click_exact": click_exact,
        "complete_step_closure_exact": trace_initial - trace_final - click_exact,
        "trace_final_compressed": compressed_final_trace,
        "click_compressed": click_compressed,
        "representation_ledger": representation_ledger,
        "density_trace_norm_error": density_error,
        "complete_law_l1_error": law_l1_error,
        "history_sector_trace_norm_error": history_sector_error,
        "event_ledger": 0.0,
        "top_shell_population": top_shell,
        "upward_omitted_intensity": rate * (gate_config.n_shell + 2.0) * top_shell,
        "sector_traces": sector_traces,
        "sector_ranks": sector_ranks,
        "compressed_sector_traces": compressed_sector_traces,
        "compressed_sector_ranks": compressed_sector_ranks,
        "detector_audit": detector_audit,
        "compressed_detector_audit": detector_compressed_audit,
        "compression_records": compression_records,
        "maximum_compression_trace_identity_residual": maximum_trace_identity,
        "maximum_negative_gram_guard": maximum_negative_guard,
        "trace_restoration_applied": any_trace_restore,
    }


def run_gate(gate_config: GateConfig, package_dir: Path, require_a100: bool = True) -> Dict[str, Any]:
    started = time.perf_counter()
    parent_g0r = verify_parent_g0r(package_dir)
    parent, parent_identity = load_parent(package_dir)
    call_audit = source_parent_call_audit(Path(__file__).resolve())
    if not call_audit["passed"]:
        raise GateBlocked(f"Parent call-scope audit failed: {call_audit}")

    backend = parent.NumericalBackend(gate_config.backend)
    backend_metadata = backend.metadata()
    operators = parent.build_oscillator_operators(gate_config.n_shell, gate_config.omega)
    base_parent_config = parent.RunConfig(
        execution_gate="ES-G1P",
        backend=gate_config.backend,
        n_shell=gate_config.n_shell,
        n_z=gate_config.n_z,
        l_z=gate_config.l_z,
        dt=gate_config.dt,
        t_final=gate_config.dt,
        stop_after_steps=1,
        rate_lambda=LAMBDA_QUARTER,
        z0=gate_config.z0,
        sigma_z_amplitude=gate_config.sigma_z,
        k0=gate_config.k0,
        kappa=gate_config.kappa,
        theta=gate_config.theta,
        phi=gate_config.phi,
        detector_rhs_batch_columns=gate_config.detector_batch_columns,
        factor_block_columns=gate_config.detector_batch_columns,
        resume_from_checkpoint=False,
        representation_budget=0.0,
        planned_compression_calls=2,
        output_root=gate_config.output_dir,
    )
    z, h_z, _ = parent.build_reference_grid(gate_config.n_z, gate_config.l_z)
    initial_cpu = parent.build_initial_state(base_parent_config, operators, z, h_z)
    propagator = parent.build_propagator_objects(
        base_parent_config, operators, backend, initial_cpu
    )

    cases = [
        one_rate_case(
            label,
            rate,
            parent=parent,
            operators=operators,
            propagator=propagator,
            backend=backend,
            gate_config=gate_config,
        )
        for label, rate in RATE_CASES
    ]
    case_map = {item["label"]: item for item in cases}

    click_zero = case_map["zero"]["click_exact"]
    survival_zero = case_map["zero"]["trace_final_exact"]
    delta_click_q = case_map["lambda0_over_4"]["click_exact"] - click_zero
    delta_click_e = case_map["lambda0_over_8"]["click_exact"] - click_zero
    delta_survival_q = case_map["lambda0_over_4"]["trace_final_exact"] - survival_zero
    delta_survival_e = case_map["lambda0_over_8"]["trace_final_exact"] - survival_zero
    slope_click_q = delta_click_q / LAMBDA_QUARTER
    slope_click_e = delta_click_e / LAMBDA_EIGHTH
    slope_survival_q = delta_survival_q / LAMBDA_QUARTER
    slope_survival_e = delta_survival_e / LAMBDA_EIGHTH
    click_curvature_estimate = 4.0 * (delta_click_q - 2.0 * delta_click_e) / (LAMBDA_QUARTER**2)
    survival_curvature_estimate = 4.0 * (delta_survival_q - 2.0 * delta_survival_e) / (LAMBDA_QUARTER**2)

    device_name = str(backend_metadata.get("cuda_device_name", ""))
    a100_pass = gate_config.backend == "cupy" and "A100" in device_name.upper()
    global_checks = {
        "nonaccepting_flags_frozen": bool(
            not PRODUCTION_AUTHORIZED
            and not ACCEPTANCE_ENABLED
            and not TASK10_ELIGIBLE
            and not FINITE_POSITIVE_RATE_PHYSICAL_CLAIM
            and not U2I_PHYSICAL_COMPARISON_PERFORMED
            and not CSSF_CHECKPOINT_IMPORT_ENABLED
            and not CSSF_PROPAGATION_ENABLED
            and not AUTOMATIC_SWEEP_ENABLED
        ),
        "parent_g0r_pass": parent_g0r["passed"],
        "parent_source_and_core_exact": bool(
            parent_identity["source_sha256"] == PARENT_SOURCE_SHA256
            and parent_identity["numerical_core_sha256"] == PARENT_CORE_SHA256
        ),
        "parent_call_scope": call_audit["passed"],
        "operator_authority": bool(operators.audit["all_checks_passed"]),
        "detector_authority": bool(
            propagator.roof_sign_audit["spinor_roof_term_sign_passed"]
            and propagator.roof_sign_audit["derived_reactive_roof_sign"] == "+"
            and propagator.roof_sign_audit["K_contributes_no_antihermitian_loss"]
        ),
        "production_dimensions_exact": bool(
            gate_config.n_shell == 12
            and gate_config.n_z == 1500
            and gate_config.state_dimension == 273000
            and gate_config.dt == 5.0e-4
            and gate_config.omega == 100.0
        ),
        "all_rate_cases_pass": all(item["passed"] for item in cases),
        "required_zib_a100_backend": bool(a100_pass if require_a100 else True),
    }
    passed = all(global_checks.values())

    arrays = {
        "rates": np.asarray([item["rate"] for item in cases], dtype=np.float64),
        "exact_click": np.asarray([item["click_exact"] for item in cases], dtype=np.float64),
        "exact_survival": np.asarray([item["trace_final_exact"] for item in cases], dtype=np.float64),
        "compressed_click": np.asarray([item["click_compressed"] for item in cases], dtype=np.float64),
        "compressed_survival": np.asarray([item["trace_final_compressed"] for item in cases], dtype=np.float64),
        "representation_ledger": np.asarray([item["representation_ledger"] for item in cases], dtype=np.float64),
        "event_ledger": np.asarray([item["event_ledger"] for item in cases], dtype=np.float64),
        "sector_traces": np.stack([item["sector_traces"] for item in cases]),
        "sector_ranks": np.stack([item["sector_ranks"] for item in cases]),
        "compressed_sector_traces": np.stack([item["compressed_sector_traces"] for item in cases]),
        "compressed_sector_ranks": np.stack([item["compressed_sector_ranks"] for item in cases]),
        "top_shell_population": np.asarray([item["top_shell_population"] for item in cases], dtype=np.float64),
        "history_sector_trace_norm_error": np.asarray(
            [item["history_sector_trace_norm_error"] for item in cases], dtype=np.float64
        ),
        "density_trace_norm_error": np.asarray(
            [item["density_trace_norm_error"] for item in cases], dtype=np.float64
        ),
        "complete_law_l1_error": np.asarray(
            [item["complete_law_l1_error"] for item in cases], dtype=np.float64
        ),
    }
    scalar_metrics = {
        "schema": PRODUCT_SCHEMA,
        "rate_labels": [item["label"] for item in cases],
        "rates": {item["label"]: item["rate"] for item in cases},
        "click_slope_lambda0_over_4": slope_click_q,
        "click_slope_lambda0_over_8": slope_click_e,
        "survival_slope_lambda0_over_4": slope_survival_q,
        "survival_slope_lambda0_over_8": slope_survival_e,
        "click_slope_halving_difference": slope_click_e - slope_click_q,
        "survival_slope_halving_difference": slope_survival_e - slope_survival_q,
        "one_step_click_curvature_estimate": click_curvature_estimate,
        "one_step_survival_curvature_estimate": survival_curvature_estimate,
        "maximum_representation_ledger": max(item["representation_ledger"] for item in cases),
        "maximum_history_sector_trace_norm_error": max(
            item["history_sector_trace_norm_error"] for item in cases
        ),
        "maximum_batch64_vs_independent_relative_error": max(
            item["detector_audit"]["multi_rhs_vs_independent_relative_error"] for item in cases
        ),
        "maximum_gmres_true_relative_residual": max(
            max(
                item["detector_audit"]["maximum_multi_rhs_true_residual"],
                item["detector_audit"]["maximum_independent_true_residual"],
            )
            for item in cases
        ),
        "maximum_complete_step_closure": max(abs(item["complete_step_closure_exact"]) for item in cases),
    }

    report_cases = []
    for item in cases:
        copy = dict(item)
        for key in (
            "sector_traces",
            "sector_ranks",
            "compressed_sector_traces",
            "compressed_sector_ranks",
        ):
            copy[key] = np.asarray(copy[key]).tolist()
        report_cases.append(copy)

    report = {
        "schema": REPORT_SCHEMA,
        "script_version": SCRIPT_VERSION,
        "generated_utc": utc_now_iso(),
        "verdict": (
            "PASS_TASK09_ES_G1P_PRODUCTION_ONE_STEP_NONACCEPTING"
            if passed
            else "FAIL_TASK09_ES_G1P_PRODUCTION_ONE_STEP_NONACCEPTING"
        ),
        "passed": passed,
        "global_checks": global_checks,
        "parent_g0r": parent_g0r,
        "parent_identity": parent_identity,
        "parent_call_scope_audit": call_audit,
        "backend": backend_metadata,
        "configuration": {
            "n_shell": gate_config.n_shell,
            "n_z": gate_config.n_z,
            "state_dimension": gate_config.state_dimension,
            "l_z": gate_config.l_z,
            "omega": gate_config.omega,
            "dt": gate_config.dt,
            "steps": 1,
            "event_sectors_retained": [0, 1, 2],
            "detector_rhs_batch_columns": gate_config.detector_batch_columns,
            "strang_order": "bath-half / detector-Cayley / bath-half",
            "trace_restoration": "forbidden",
        },
        "operator_audit": operators.audit,
        "detector_audit": propagator.roof_sign_audit,
        "cases": report_cases,
        "rate_halving_diagnostics": scalar_metrics,
        "claim_boundary": {
            "interpretation": "production-size one-complete-step representation/backend certification only",
            "production_trajectory_authorized": False,
            "continuation_beyond_one_step_authorized": False,
            "U2I_comparison_performed": False,
            "finite_positive_rate_physical_claim": False,
            "task10_eligible": False,
            "cssf_branch_reactivated": False,
        },
        "authority": {
            "parent_g3_failure_archive_sha256": PARENT_G3_FAILURE_SHA256,
            "parent_g3_failure_classification": PARENT_G3_FAILURE_CLASSIFICATION,
            "does_not_supersede": [
                "the frozen detector, bath, grid, shell, midpoint, and GMRES authorities",
                "the Stage-07/08 accepted U2-I zero-rate susceptibility",
                "the terminal CSSF failure classification",
            ],
            "new_scope": "exact positive event-number sectors at one production-size Strang step",
        },
        "elapsed_seconds": time.perf_counter() - started,
    }
    return {"report": report, "arrays": arrays, "scalar_metrics": scalar_metrics}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path(os.environ.get("OPEN_SYSTEM_3D_ROOT", "[ARCHIVE_PATH]")),
    )
    parser.add_argument(
        "--backend",
        choices=("cupy", "scipy"),
        default=os.environ.get("TASK09_ES_BACKEND", "cupy"),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=os.environ.get("TASK09_ES_OVERWRITE", "0").lower() in {"1", "true", "yes"},
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    package_dir = Path(__file__).resolve().parent
    data_root = args.data_root.expanduser().resolve()
    output_dir = data_root / "Task09_ES_G1P" / "4911.ES_G1P_production_one_step_event_sectors_nonaccepting"
    output_dir.mkdir(parents=True, exist_ok=True)
    lock_path = output_dir / ".gate.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise GateBlocked("Another ES-G1P process holds the gate lock") from exc
        completed = output_dir / "gate_report.json"
        if completed.exists() and not args.overwrite:
            raise GateBlocked(f"Completed report already exists: {completed}")

        source_path = Path(__file__).resolve()
        source_hash = sha256_file(source_path)
        core_hash = sha256_core(source_path, NUMERICAL_CORE_MARKER)
        status_path = output_dir / "run_status.json"
        status: Dict[str, Any] = {
            "status": "running",
            "started_utc": utc_now_iso(),
            "script_version": SCRIPT_VERSION,
            "source_sha256": source_hash,
            "numerical_core_sha256": core_hash,
            "backend": args.backend,
            "output_directory": str(output_dir),
            "production_authorized": False,
            "continuation_beyond_one_step_authorized": False,
            "task10_eligible": False,
            "finite_positive_rate_physical_claim": False,
        }
        atomic_write_json(status_path, status)
        shutil.copy2(source_path, output_dir / source_path.name)
        config = GateConfig(
            backend=args.backend,
            data_root=data_root,
            output_dir=output_dir,
        )
        try:
            products = run_gate(config, package_dir, require_a100=True)
            report = products["report"]
            report["source_sha256"] = source_hash
            report["numerical_core_sha256"] = core_hash
            atomic_write_json(output_dir / "gate_report.json", report)
            atomic_write_json(output_dir / "operator_audit.json", report["operator_audit"])
            atomic_write_json(output_dir / "detector_audit.json", report["detector_audit"])
            atomic_write_json(
                output_dir / "bath_audit.json",
                {
                    item["label"]: {
                        "rate": item["rate"],
                        "action_per_bath_half": item["action_per_bath_half"],
                        "completeness_residual": item["bath_completeness_residual"],
                    }
                    for item in report["cases"]
                },
            )
            atomic_write_json(output_dir / "one_step_metrics.json", products["scalar_metrics"])
            atomic_savez(output_dir / "one_step_products.npz", **products["arrays"])

            exclusions = {"output_hashes.json", "run_status.json", "independent_audit.json"}
            hashes = {
                path.name: sha256_file(path)
                for path in sorted(output_dir.iterdir())
                if path.is_file() and path.name not in exclusions and not path.name.startswith(".")
            }
            atomic_write_json(output_dir / "output_hashes.json", {"algorithm": "SHA-256", "files": hashes})
            status.update(
                {
                    "status": "completed" if report["passed"] else "completed_fail",
                    "completed_utc": utc_now_iso(),
                    "verdict": report["verdict"],
                }
            )
            atomic_write_json(status_path, status)
            print(report["verdict"])
            print(f"Output directory: {output_dir}")
            return 0 if report["passed"] else 2
        except GateBlocked:
            raise
        except Exception as exc:
            failure = {
                "status": "failed",
                "failed_utc": utc_now_iso(),
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc(),
            }
            atomic_write_json(output_dir / "failure.json", failure)
            status.update(failure)
            atomic_write_json(status_path, status)
            raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GateBlocked as exc:
        print(f"BLOCKED_TASK09_ES_G1P: {exc}", file=sys.stderr)
        raise SystemExit(4)
