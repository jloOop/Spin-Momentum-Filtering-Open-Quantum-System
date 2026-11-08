#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task-09 ES-G2P: production-size positive-event-sector prefix to t=1.55.

This is a strictly non-accepting feasibility and numerical-integrity gate.  It
propagates the frozen U2 strong-confinement spinor detector at lambda_0/4 using
positive event-number sectors k=0,...,4, a no-trace-restoration representation
ledger, and the exact finite bath-half / detector-Cayley / bath-half map.

A fresh zero-rate rank-one detector branch is propagated with the same Cayley
and GMRES implementation.  It is compared with the accepted Stage-07 U2-I
zero-rate reference, while the finite-difference comparison to the U2-I tangent
is diagnostic only.  No finite-positive-rate physical claim is authorized.
"""
from __future__ import annotations

import argparse
import ast
import fcntl
import hashlib
import importlib.util
import io
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
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

import numpy as np
from scipy.stats import binom


# TASK-09 ES-G2P NUMERICAL CORE BEGINS HERE
NUMERICAL_CORE_MARKER = "# TASK-09 ES-G2P NUMERICAL CORE BEGINS HERE"

SCRIPT_VERSION = "2026-08-15-task09-es-g2p-prefix155-positive-event-sectors-nonaccepting-v1"
REPORT_SCHEMA = "2026-08-15-task09-es-g2p-prefix155-report-v1"
PRODUCT_SCHEMA = "2026-08-15-task09-es-g2p-prefix155-products-v1"
CHECKPOINT_SCHEMA = "2026-08-15-task09-es-g2p-prefix155-checkpoint-v1"

# Frozen non-claim boundary.
PRODUCTION_AUTHORIZED = False
ACCEPTANCE_ENABLED = False
TASK10_ELIGIBLE = False
FINITE_POSITIVE_RATE_PHYSICAL_CLAIM = False
U2I_PHYSICAL_ACCEPTANCE_PERFORMED = False
CSSF_CHECKPOINT_IMPORT_ENABLED = False
CSSF_PROPAGATION_ENABLED = False
AUTOMATIC_SWEEP_ENABLED = False
RESUME_ENABLED = False

# Parent identities.
PARENT_CSSF_SOURCE_NAME = (
    "Task09_4901_U2_low_v4_nonaccepting_"
    "D2PR2G1FMP_BATCH64_REPAIRED_RANK_WHOLEHALF_G0.py"
)
PARENT_CSSF_SOURCE_SHA256 = "d0bcd5af9b12b4d21ec897b87151006a1d9e1a7e035172ddf73c1c41c8a111c7"
PARENT_CSSF_CORE_SHA256 = "fcf82f3344cd2190efb465b82ec669c1da7270ab48e926b037f7f799bca6cc45"
PARENT_CSSF_CORE_MARKER = "# TASK-09 V4 NUMERICAL CORE BEGINS HERE"
PARENT_CSSF_FAILURE_SHA256 = "70af5f3eca34ca15130a1d303c527b3e0cea9932ba89266a28f6c227d8bbbfa7"
PARENT_CSSF_FAILURE_CLASSIFICATION = "NO_ADMISSIBLE_REPAIRED_RANK"

PARENT_G1P_SOURCE_NAME = "PARENT_Task09_ES_G1P_production_one_step_event_sectors_nonaccepting.py"
PARENT_G1P_SOURCE_SHA256 = "39f1306b371f2664a9ed89b25efc1967bae9b15c8b8dc5a3e2934815ce1a7a02"
PARENT_G1P_CORE_SHA256 = "f6c872c9f023f9ed51e0b3a90d12d93e600e349de546079fc6c44fa34adad10e"
PARENT_G1P_CORE_MARKER = "# TASK-09 ES-G1P NUMERICAL CORE BEGINS HERE"
PARENT_G1P_RESULT_NAME = "PARENT_Task09_ES_G1P_ProductionOneStep_Result_9422426.zip"
PARENT_G1P_RESULT_SHA256 = "7f909a4463d9c1a0afea0f987b5bbb4a3498a9f174b78a3b524284d7d1efe616"
PARENT_G1P_VERDICT = "PASS_TASK09_ES_G1P_PRODUCTION_ONE_STEP_NONACCEPTING"
PARENT_G1P_AUDIT_VERDICT = "PASS_TASK09_ES_G1P_INDEPENDENT_ARTIFACT_AUDIT"

U2I_ARCHIVE_NAME = "PARENT_U2I_Task07_case_share.zip"
U2I_ARCHIVE_SHA256 = "3ec8ff21a633105aa713f1eb95ebe4a104b1ae4ba5801ec8a2eee8d47188b1db"
U2I_PREFIX = "spinor_upward_omega100_mode00_N12_dt5e-4_T10_ins5e-2"
U2I_COMPACT_NAME = f"{U2I_PREFIX}_case_loader_compact.npz"
U2I_COMPACT_SHA256 = "23bbff767853695e2f217b1944511e9c445f1863fa3068685c70e40190242f8b"
U2I_INTEGRATED_NAME = f"{U2I_PREFIX}_integrated_response.json"
U2I_INTEGRATED_SHA256 = "fd57d55a9f03e9ce19c8fe58e580d0add5f0b6a1248872a0ed2293b92e6901ac"
U2I_CHI_D = -0.5277704784916021
U2I_CHI_MU = 3.5572478485472043
U2I_ATV = 0.6854856104815765

# Frozen production family.
LAMBDA_0 = math.pi / 400.0
RATE_LAMBDA = LAMBDA_0 / 4.0
N_SHELL = 12
N_Z = 1500
L_Z = 20.0
OMEGA = 100.0
DT = 5.0e-4
T_FINAL = 1.55
NUM_STEPS = 3100
Z0 = 10.0
SIGMA_Z_AMPLITUDE = 0.5
K0 = math.pi
KAPPA = math.pi
THETA = math.pi / 6.0
PHI = 0.0
DETECTOR_BATCH_COLUMNS = 64
MAX_EVENT_SECTOR = 4
OUTPUT_STRIDE_STEPS = 100       # 0.05 time units
CHECKPOINT_STEPS = (1000, 2000, 2500, 2800, 3000, 3100)
INDEPENDENT_CROSSCHECK_STEPS = (1, 1000, 2000, 2500, 2800, 3000, 3100)

# Predeclared nonuniform cumulative representation budget through t=1.55.
# This is 25% of the provisional 2e-7 prompt-window budget through t=3.6.
REPRESENTATION_BLOCKS = (
    (0.80, 5.0e-9),
    (1.10, 1.5e-8),
    (1.35, 3.0e-8),
    (1.55, 5.0e-8),
)
REPRESENTATION_BUDGET_PREFIX = 5.0e-8
REPRESENTATION_BUDGET_PROMPT_PROVISIONAL = 2.0e-7
BUDGET_COMPARISON_TOL = 128.0 * np.finfo(float).eps

# Feasibility and numerical gates.
PREFERRED_TOTAL_RANK = 128
HARD_TOTAL_RANK_STOP = 256
WALLTIME_GUARD_SECONDS = 11.75 * 3600.0
OPERATOR_TOL = 2.0e-12
BATH_COMPLETENESS_TOL = 2.0e-12
TRUE_RESIDUAL_TOL = 1.0e-8
BATCH_SAMPLE_REL_TOL = 5.0e-8
BATCH_SAMPLE_CLICK_ABS_TOL = 5.0e-10
BATH_LEDGER_CLOSURE_TOL = 5.0e-9
DETECTOR_CLOSURE_TOL = 5.0e-9
COMPLETE_STEP_LEDGER_CLOSURE_TOL = 1.0e-8
CUMULATIVE_LEDGER_CLOSURE_TOL = 5.0e-8
NEGATIVE_GRAM_GUARD_TOL = 5.0e-12
COMPRESSION_TRACE_GROWTH_TOL = 5.0e-12
COMPRESSION_TRACE_IDENTITY_TOL = 5.0e-11
SURVIVAL_INCREASE_TOL = 2.0e-9
EVENT_BOUND_TOL = 1.0e-12
TOP_SHELL_OVERFLOW_TOL = 1.0e-6
U2I_ZERO_REFERENCE_ABS_TOL = 1.0e-6
NONNEGATIVITY_TOL = 5.0e-12

ALLOWED_PARENT_CALLS = {
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
    "complete_step",
    "run_g",
    "run_production",
    "resume",
    "telemetry",
    "cssf",
)


class GateBlocked(RuntimeError):
    pass


class GateStop(RuntimeError):
    def __init__(self, classification: str, message: str, event: Mapping[str, Any]):
        super().__init__(message)
        self.classification = str(classification)
        self.event = dict(event)


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
    t_final: float = T_FINAL
    num_steps: int = NUM_STEPS
    rate_lambda: float = RATE_LAMBDA
    max_event_sector: int = MAX_EVENT_SECTOR
    z0: float = Z0
    sigma_z: float = SIGMA_Z_AMPLITUDE
    k0: float = K0
    kappa: float = KAPPA
    theta: float = THETA
    phi: float = PHI
    detector_batch_columns: int = DETECTOR_BATCH_COLUMNS
    output_stride_steps: int = OUTPUT_STRIDE_STEPS
    checkpoint_steps: Tuple[int, ...] = CHECKPOINT_STEPS
    independent_crosscheck_steps: Tuple[int, ...] = INDEPENDENT_CROSSCHECK_STEPS
    representation_blocks: Tuple[Tuple[float, float], ...] = REPRESENTATION_BLOCKS
    hard_rank_stop: int = HARD_TOTAL_RANK_STOP
    preferred_rank: int = PREFERRED_TOTAL_RANK
    walltime_guard_seconds: float = WALLTIME_GUARD_SECONDS
    require_u2i_reference: bool = True
    save_large_checkpoint: bool = True
    development_mode: bool = False

    @property
    def d_channels(self) -> int:
        return (self.n_shell + 1) * (self.n_shell + 2)

    @property
    def state_dimension(self) -> int:
        return self.d_channels * self.n_z

    @property
    def total_bath_half_calls(self) -> int:
        return 2 * self.num_steps


@dataclass
class CompressionAudit:
    call_index: int
    ceiling: float
    ledger_before: float
    allowance: float
    input_trace: float
    output_trace: float
    discarded_trace: float
    ledger_after: float
    rank_before: int
    rank_after: int
    negative_guard: float
    trace_growth_guard: float
    trace_identity_residual: float
    per_sector: List[Dict[str, Any]]
    trace_restoration_applied: bool = False


@dataclass
class PrefixState:
    family: Dict[int, Any]
    zero_state: Any
    representation_ledger: float
    event_first_crossing_ledger: float
    cumulative_click: float
    cumulative_zero_click: float
    cumulative_overflow_bound: float
    previous_overflow_intensity: float
    completed_step: int


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    raise TypeError(type(value).__name__)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


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
        raise GateBlocked(f"Numerical-core marker missing in {path.name}")
    return hashlib.sha256(text.split(marker, 1)[1].encode("utf-8")).hexdigest()


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


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise GateBlocked(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def verify_g1p_result(package_dir: Path) -> Dict[str, Any]:
    path = package_dir / PARENT_G1P_RESULT_NAME
    if sha256_file(path) != PARENT_G1P_RESULT_SHA256:
        raise GateBlocked("ES-G1P result archive SHA-256 mismatch")
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise GateBlocked(f"ES-G1P result ZIP CRC failure: {bad}")
        names = archive.namelist()
        status_name = next(name for name in names if name.endswith("/run_status.json"))
        audit_name = next(name for name in names if name.endswith("/independent_audit.json"))
        status = json.loads(archive.read(status_name))
        audit = json.loads(archive.read(audit_name))
    passed = bool(
        status.get("verdict") == PARENT_G1P_VERDICT
        and audit.get("verdict") == PARENT_G1P_AUDIT_VERDICT
        and status.get("production_authorized") is False
        and status.get("task10_eligible") is False
    )
    if not passed:
        raise GateBlocked("ES-G1P parent verdict or claim boundary failed")
    return {
        "archive_sha256": PARENT_G1P_RESULT_SHA256,
        "solver_verdict": status["verdict"],
        "independent_audit_verdict": audit["verdict"],
        "passed": True,
    }


def load_parent_authority(package_dir: Path) -> Tuple[Any, Dict[str, Any]]:
    cssf_path = package_dir / PARENT_CSSF_SOURCE_NAME
    g1p_path = package_dir / PARENT_G1P_SOURCE_NAME
    cssf_source = sha256_file(cssf_path)
    cssf_core = sha256_core(cssf_path, PARENT_CSSF_CORE_MARKER)
    g1p_source = sha256_file(g1p_path)
    g1p_core = sha256_core(g1p_path, PARENT_G1P_CORE_MARKER)
    if cssf_source != PARENT_CSSF_SOURCE_SHA256 or cssf_core != PARENT_CSSF_CORE_SHA256:
        raise GateBlocked("Frozen detector/bath parent source or core mismatch")
    if g1p_source != PARENT_G1P_SOURCE_SHA256 or g1p_core != PARENT_G1P_CORE_SHA256:
        raise GateBlocked("ES-G1P source or core mismatch")
    parent = load_module(cssf_path, "task09_es_g2p_parent_cssf_authority")
    frozen = bool(
        parent.PRODUCTION_AUTHORIZED is False
        and parent.ACCEPTANCE_ENABLED is False
        and parent.TASK10_ELIGIBLE is False
        and parent.FINITE_POSITIVE_RATE_PHYSICAL_CLAIM is False
        and parent.N_SHELL == N_SHELL
        and parent.N_Z == N_Z
        and parent.L_Z == L_Z
        and parent.OMEGA == OMEGA
        and parent.DT == DT
        and parent.GMRES_RTOL == 1.0e-10
        and parent.GMRES_ATOL == 0.0
        and parent.GMRES_RESTART == 30
        and parent.GMRES_MAXITER == 1000
        and parent.DETECTOR_RHS_BATCH_COLUMNS == DETECTOR_BATCH_COLUMNS
    )
    if not frozen:
        raise GateBlocked("Frozen parent authority constants changed")
    return parent, {
        "cssf_source_sha256": cssf_source,
        "cssf_core_sha256": cssf_core,
        "g1p_source_sha256": g1p_source,
        "g1p_core_sha256": g1p_core,
        "frozen_detector_bath_and_gmres_constants": True,
        "cssf_propagation_imported": False,
    }


def parent_call_scope_audit(script_path: Path) -> Dict[str, Any]:
    tree = ast.parse(script_path.read_text(encoding="utf-8"), filename=str(script_path))
    calls: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "parent":
                calls.append(node.func.attr)
    calls = sorted(set(calls))
    forbidden = sorted(
        name for name in calls
        if name not in ALLOWED_PARENT_CALLS
        or any(fragment in name.lower() for fragment in FORBIDDEN_PARENT_CALL_FRAGMENTS)
    )
    passed = not forbidden
    return {
        "parent_calls": calls,
        "allowed_parent_calls": sorted(ALLOWED_PARENT_CALLS),
        "forbidden_parent_calls": forbidden,
        "cssf_propagation_compression_repair_budget_checkpoint_calls_absent": passed,
        "passed": passed,
    }


def load_u2i_reference(package_dir: Path, config: GateConfig) -> Dict[str, Any]:
    path = package_dir / U2I_ARCHIVE_NAME
    if sha256_file(path) != U2I_ARCHIVE_SHA256:
        raise GateBlocked("U2-I case archive SHA-256 mismatch")
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise GateBlocked(f"U2-I ZIP CRC failure: {bad}")
        compact_bytes = archive.read(U2I_COMPACT_NAME)
        integrated_bytes = archive.read(U2I_INTEGRATED_NAME)
    if sha256_bytes(compact_bytes) != U2I_COMPACT_SHA256:
        raise GateBlocked("U2-I compact NPZ hash mismatch")
    if sha256_bytes(integrated_bytes) != U2I_INTEGRATED_SHA256:
        raise GateBlocked("U2-I integrated-response hash mismatch")
    with np.load(io.BytesIO(compact_bytes), allow_pickle=False) as data:
        times = np.asarray(data["times"], dtype=np.float64)
        reference_survival = np.asarray(data["reference_survival"], dtype=np.float64)
        chi_survival = np.asarray(data["chi_survival"], dtype=np.float64)
        chi_click_density = np.asarray(data["chi_click_density"], dtype=np.float64)
    integrated = json.loads(integrated_bytes)
    if not (
        times.shape == (201,)
        and reference_survival.shape == (201,)
        and chi_survival.shape == (201,)
        and chi_click_density.shape == (200,)
        and np.allclose(times, np.arange(201) * 0.05, rtol=0.0, atol=2.0e-15)
        and abs(integrated["chi_D_from_final_survival"] - U2I_CHI_D) <= 5.0e-15
        and abs(integrated["chi_mu_restricted"] - U2I_CHI_MU) <= 5.0e-14
        and abs(integrated["chi_complete_signed_measure_norm"] - U2I_ATV) <= 5.0e-14
    ):
        raise GateBlocked("U2-I reference content failed its frozen identity checks")
    node_times = np.arange(config.num_steps // config.output_stride_steps + 1) * (
        config.output_stride_steps * config.dt
    )
    indices = np.rint(node_times / 0.05).astype(np.int64)
    if np.max(indices) >= times.size or not np.allclose(times[indices], node_times, atol=2.0e-15, rtol=0.0):
        raise GateBlocked("ES-G2P output nodes do not align with U2-I nodes")
    return {
        "full_times": times,
        "full_reference_survival": reference_survival,
        "full_chi_survival": chi_survival,
        "full_chi_click_density": chi_click_density,
        "node_indices": indices,
        "times": times[indices],
        "reference_survival": reference_survival[indices],
        "chi_survival": chi_survival[indices],
        "chi_click_density": chi_click_density[: indices[-1]],
        "integrated": integrated,
        "archive_sha256": U2I_ARCHIVE_SHA256,
        "compact_sha256": U2I_COMPACT_SHA256,
        "claim_boundary": "diagnostic zero-rate/tangent reference only",
    }


def physical_trace(factor: Any, h_z: float, backend: Any) -> float:
    value = h_z * backend.xp.sum(factor.real * factor.real + factor.imag * factor.imag)
    return backend.scalar_float(value)


def family_trace(family: Mapping[int, Any], h_z: float, backend: Any) -> float:
    return float(math.fsum(physical_trace(factor, h_z, backend) for factor in family.values()))


def family_rank(family: Mapping[int, Any]) -> int:
    return int(sum(int(factor.shape[1]) for factor in family.values()))


def combine_family(family: Mapping[int, Any], backend: Any) -> Tuple[Any, List[int], List[int]]:
    sectors = sorted(family)
    if not sectors:
        raise GateStop("EMPTY_RETAINED_FAMILY", "No retained event-sector factor remains", {})
    widths = [int(family[sector].shape[1]) for sector in sectors]
    matrix = backend.xp.ascontiguousarray(
        backend.xp.concatenate([family[sector] for sector in sectors], axis=1)
    )
    return matrix, sectors, widths


def split_family(matrix: Any, sectors: Sequence[int], widths: Sequence[int]) -> Dict[int, Any]:
    output: Dict[int, Any] = {}
    offset = 0
    for sector, width in zip(sectors, widths):
        output[int(sector)] = matrix[:, offset : offset + int(width)]
        offset += int(width)
    return output


def apply_kraus(operator: Any, factor: Any, d_channels: int, n_z: int, backend: Any) -> Any:
    rank = int(factor.shape[1])
    shaped = factor.reshape(d_channels, n_z * rank)
    mapped = operator @ shaped
    return backend.xp.ascontiguousarray(mapped.reshape(d_channels * n_z, rank))


def representation_ceiling(call_index: int, config: GateConfig) -> float:
    if call_index < 0 or call_index > config.total_bath_half_calls:
        raise ValueError("Invalid bath-half call index")
    if call_index == 0:
        return 0.0
    previous_call = 0
    previous_budget = 0.0
    for time_end, cumulative_budget in config.representation_blocks:
        call_end = 2 * int(round(float(time_end) / config.dt))
        if call_index <= call_end:
            fraction = (call_index - previous_call) / max(call_end - previous_call, 1)
            return previous_budget + fraction * (cumulative_budget - previous_budget)
        previous_call = call_end
        previous_budget = cumulative_budget
    return float(config.representation_blocks[-1][1])


def analytic_event_tail(step: int, bath: Any, config: GateConfig) -> float:
    if step <= 0:
        return 0.0
    g_max = float(np.max(np.asarray(bath.g_diagonal, dtype=np.float64), initial=0.0))
    q_max = (bath.action * g_max) / (1.0 + bath.action * g_max)
    return float(binom.sf(config.max_event_sector, 2 * int(step), q_max))


def bath_half_truncated(
    family: Mapping[int, Any], kraus: Sequence[Any], *, config: GateConfig,
    h_z: float, backend: Any
) -> Tuple[Dict[int, Any], float, Dict[str, Any]]:
    k0, kx, ky = kraus
    pieces: MutableMapping[int, List[Any]] = {}
    event_omitted = 0.0
    trace_before = family_trace(family, h_z, backend)
    for sector, factor in sorted(family.items()):
        mapped0 = apply_kraus(k0, factor, config.d_channels, config.n_z, backend)
        if physical_trace(mapped0, h_z, backend) > 0.0:
            pieces.setdefault(int(sector), []).append(mapped0)
        for operator in (kx, ky):
            mapped = apply_kraus(operator, factor, config.d_channels, config.n_z, backend)
            mapped_trace = physical_trace(mapped, h_z, backend)
            if sector + 1 <= config.max_event_sector:
                if mapped_trace > 0.0:
                    pieces.setdefault(int(sector + 1), []).append(mapped)
            else:
                event_omitted += mapped_trace
    raw = {
        sector: backend.xp.ascontiguousarray(backend.xp.concatenate(blocks, axis=1))
        for sector, blocks in pieces.items()
    }
    trace_raw = family_trace(raw, h_z, backend)
    closure = trace_before - trace_raw - event_omitted
    return raw, float(event_omitted), {
        "trace_before": trace_before,
        "trace_raw_retained": trace_raw,
        "event_first_crossing_increment": float(event_omitted),
        "trace_closure_before_compression": float(closure),
        "rank_raw": family_rank(raw),
    }


def compress_family_global_no_restore(
    family: Mapping[int, Any], *, call_index: int, ledger_before: float,
    config: GateConfig, h_z: float, backend: Any
) -> Tuple[Dict[int, Any], float, CompressionAudit]:
    ceiling = representation_ceiling(call_index, config)
    available = max(0.0, ceiling - ledger_before)
    selection_allowance = max(0.0, available - BUDGET_COMPARISON_TOL)
    spectra: Dict[int, Tuple[np.ndarray, np.ndarray, float]] = {}
    candidates: List[Tuple[float, int, int]] = []
    negative_guard = 0.0
    rank_before = 0
    input_trace = family_trace(family, h_z, backend)
    per_sector_pre: Dict[int, Dict[str, Any]] = {}
    for sector, factor in sorted(family.items()):
        columns = int(factor.shape[1])
        rank_before += columns
        gram_backend = h_z * (factor.conj().T @ factor)
        gram = np.asarray(backend.to_cpu(gram_backend), dtype=np.complex128)
        gram = 0.5 * (gram + gram.conj().T)
        values, vectors = np.linalg.eigh(gram)
        neg = float(np.sum(np.maximum(-values, 0.0), dtype=np.float64))
        negative_guard += neg
        positive = np.maximum(values, 0.0)
        spectra[int(sector)] = (positive, vectors, physical_trace(factor, h_z, backend))
        for index, value in enumerate(positive):
            candidates.append((float(value), int(sector), int(index)))
        support_floor = float(
            4096.0 * np.finfo(float).eps * max(1, columns) * max(1.0, float(np.max(positive, initial=0.0)))
        )
        per_sector_pre[int(sector)] = {
            "input_columns": columns,
            "input_trace": spectra[int(sector)][2],
            "minimum_raw_eigenvalue": float(np.min(values, initial=0.0)),
            "maximum_positive_eigenvalue": float(np.max(positive, initial=0.0)),
            "negative_guard": neg,
            "diagnostic_support_floor": support_floor,
        }
    if negative_guard > min(NEGATIVE_GRAM_GUARD_TOL, available + NEGATIVE_GRAM_GUARD_TOL):
        raise GateStop(
            "GRAM_NEGATIVITY_STOP",
            "Sector Gram negative-mass guard exceeded tolerance",
            {"call_index": call_index, "negative_guard": negative_guard, "available": available},
        )
    positive_allowance = max(0.0, selection_allowance - negative_guard)
    candidates.sort(key=lambda item: item[0])
    discarded_keys: set[Tuple[int, int]] = set()
    estimated_discard = 0.0
    for value, sector, index in candidates:
        if estimated_discard + value <= positive_allowance:
            discarded_keys.add((sector, index))
            estimated_discard += value
        else:
            break
    positive_total = float(sum(value for value, _sector, _index in candidates))
    if positive_total > 0.0 and len(discarded_keys) == len(candidates):
        largest = max(candidates, key=lambda item: item[0])
        discarded_keys.remove((largest[1], largest[2]))
    output: Dict[int, Any] = {}
    per_sector: List[Dict[str, Any]] = []
    for sector, factor in sorted(family.items()):
        positive, vectors, sector_input_trace = spectra[int(sector)]
        keep = np.asarray(
            [value > 0.0 and (int(sector), int(index)) not in discarded_keys for index, value in enumerate(positive)],
            dtype=bool,
        )
        if np.any(keep):
            transform = backend.to_backend_array(np.asarray(vectors[:, keep], dtype=np.complex128))
            retained = backend.xp.ascontiguousarray(factor @ transform)
            sector_output_trace = physical_trace(retained, h_z, backend)
            output[int(sector)] = retained
            rank_after_sector = int(retained.shape[1])
        else:
            sector_output_trace = 0.0
            rank_after_sector = 0
        pre = per_sector_pre[int(sector)]
        per_sector.append({
            "sector": int(sector),
            **pre,
            "retained_rank": rank_after_sector,
            "output_trace": sector_output_trace,
            "direct_trace_deficit": float(sector_input_trace - sector_output_trace),
            "trace_restoration_applied": False,
        })
    output_trace = family_trace(output, h_z, backend) if output else 0.0
    trace_deficit = float(input_trace - output_trace)
    trace_growth_guard = max(0.0, -trace_deficit)
    discarded_trace = max(0.0, trace_deficit)
    trace_identity_residual = float(input_trace - output_trace - discarded_trace)
    if trace_growth_guard > COMPRESSION_TRACE_GROWTH_TOL:
        raise GateStop(
            "COMPRESSION_TRACE_GROWTH_STOP",
            "Positive-sector compression increased trace beyond tolerance",
            {"call_index": call_index, "trace_growth_guard": trace_growth_guard},
        )
    if discarded_trace > available + BUDGET_COMPARISON_TOL:
        raise GateStop(
            "REPRESENTATION_BLOCK_BUDGET_STOP",
            "Compression trace deficit exceeded the predeclared blockwise allowance",
            {
                "call_index": call_index,
                "discarded_trace": discarded_trace,
                "available": available,
                "ceiling": ceiling,
                "ledger_before": ledger_before,
            },
        )
    ledger_after = float(ledger_before + discarded_trace)
    if ledger_after > ceiling + BUDGET_COMPARISON_TOL:
        raise GateStop(
            "REPRESENTATION_CEILING_STOP",
            "Cumulative representation ledger exceeded its predeclared ceiling",
            {"call_index": call_index, "ledger_after": ledger_after, "ceiling": ceiling},
        )
    if not output:
        raise GateStop("EMPTY_RETAINED_FAMILY", "Compression removed the complete retained state", {})
    audit = CompressionAudit(
        call_index=int(call_index),
        ceiling=float(ceiling),
        ledger_before=float(ledger_before),
        allowance=float(available),
        input_trace=float(input_trace),
        output_trace=float(output_trace),
        discarded_trace=float(discarded_trace),
        ledger_after=float(ledger_after),
        rank_before=int(rank_before),
        rank_after=family_rank(output),
        negative_guard=float(negative_guard),
        trace_growth_guard=float(trace_growth_guard),
        trace_identity_residual=float(trace_identity_residual),
        per_sector=per_sector,
        trace_restoration_applied=False,
    )
    return output, ledger_after, audit


def family_sector_metrics(
    family: Mapping[int, Any], *, config: GateConfig, h_z: float, backend: Any
) -> Tuple[np.ndarray, np.ndarray]:
    traces = np.zeros(config.max_event_sector + 1, dtype=np.float64)
    ranks = np.zeros(config.max_event_sector + 1, dtype=np.int64)
    for sector, factor in family.items():
        if sector > config.max_event_sector:
            raise GateStop("EVENT_SECTOR_RANGE_STOP", "Retained sector exceeds Kmax", {"sector": sector})
        traces[int(sector)] = physical_trace(factor, h_z, backend)
        ranks[int(sector)] = int(factor.shape[1])
    return traces, ranks


def top_shell_population(
    family: Mapping[int, Any], *, operators: Any, config: GateConfig,
    h_z: float, backend: Any
) -> float:
    channel = np.zeros(operators.d_channels, dtype=np.float64)
    for factor in family.values():
        rank = int(factor.shape[1])
        shaped = factor.reshape(operators.d_channels, config.n_z * rank)
        values = h_z * backend.xp.sum(
            shaped.real * shaped.real + shaped.imag * shaped.imag,
            axis=1,
            dtype=backend.float64,
        )
        channel += np.asarray(backend.to_cpu(values), dtype=np.float64)
    orbital = channel.reshape(2, operators.m_modes).sum(axis=0)
    return float(np.sum(orbital[operators.shell_of_mode == config.n_shell], dtype=np.float64))


def run_bundled_detector(
    zero_state: Any, family: Mapping[int, Any], *, parent: Any, operators: Any,
    parent_config: Any, propagator: Any, backend: Any, crosscheck: bool
) -> Tuple[Any, Dict[int, Any], float, float, Dict[str, Any]]:
    """Advance the fresh zero-rate column and all retained positive-rate columns.

    The frozen detector contract is Batch-64.  This routine therefore partitions
    the complete bundled factor explicitly before calling the parent multi-RHS
    solver; it never relies on the current total rank being below 64.
    """
    positive, sectors, widths = combine_family(family, backend)
    bundle = backend.xp.ascontiguousarray(
        backend.xp.concatenate([zero_state, positive], axis=1)
    )
    zero_before = physical_trace(zero_state, propagator.h_z, backend)
    positive_before = physical_trace(positive, propagator.h_z, backend)

    count = int(bundle.shape[1])
    advanced = backend.xp.empty_like(bundle)
    q_roof = backend.xp.empty(
        (operators.d_channels, count), dtype=bundle.dtype
    )
    all_infos: List[np.ndarray] = []
    all_residuals: List[np.ndarray] = []
    iterations = 0
    batch_sizes: List[int] = []
    for start in range(0, count, int(parent_config.detector_rhs_batch_columns)):
        stop = min(count, start + int(parent_config.detector_rhs_batch_columns))
        batch = backend.xp.ascontiguousarray(bundle[:, start:stop])
        advanced_batch, q_batch, infos, residuals, used = parent.advance_many_spinor(
            batch,
            backend=backend,
            propagator=propagator,
            config=parent_config,
            operators=operators,
            certified_multi_rhs=True,
        )
        advanced[:, start:stop] = advanced_batch
        q_roof[:, start:stop] = q_batch
        all_infos.append(np.asarray(infos, dtype=np.int32))
        all_residuals.append(np.asarray(residuals, dtype=np.float64))
        iterations += int(used)
        batch_sizes.append(stop - start)

    infos_all = (
        np.concatenate(all_infos) if all_infos else np.empty(0, dtype=np.int32)
    )
    residuals_all = (
        np.concatenate(all_residuals)
        if all_residuals
        else np.empty(0, dtype=np.float64)
    )
    zero_next = backend.xp.ascontiguousarray(advanced[:, :1])
    positive_next_matrix = backend.xp.ascontiguousarray(advanced[:, 1:])
    zero_click = float(
        parent_config.dt * parent_config.kappa * backend.abs2_sum(q_roof[:, :1])
    )
    positive_click = float(
        parent_config.dt * parent_config.kappa * backend.abs2_sum(q_roof[:, 1:])
    )
    zero_after = physical_trace(zero_next, propagator.h_z, backend)
    positive_after = physical_trace(positive_next_matrix, propagator.h_z, backend)

    sample_relative = 0.0
    sample_click_difference = 0.0
    independent_infos: List[int] = []
    independent_residuals: List[float] = []
    sample_indices: List[int] = []
    if crosscheck:
        candidates = sorted(set([0, 1, max(0, count // 2), count - 1]))
        sample_indices = [index for index in candidates if 0 <= index < count]
        selector = (
            sample_indices
            if backend.name == "scipy"
            else backend._cp.asarray(sample_indices)
        )
        sample = backend.xp.ascontiguousarray(bundle[:, selector])
        independent, q_ind, info_ind, residual_ind, _ = parent.advance_many_spinor(
            sample,
            backend=backend,
            propagator=propagator,
            config=parent_config,
            operators=operators,
            certified_multi_rhs=False,
        )
        batch_sample = advanced[:, selector]
        scale = max(
            math.sqrt(propagator.h_z) * backend.norm(independent),
            np.finfo(float).tiny,
        )
        sample_relative = (
            math.sqrt(propagator.h_z)
            * backend.norm(batch_sample - independent)
            / scale
        )
        click_sample_batch = float(
            parent_config.dt
            * parent_config.kappa
            * backend.abs2_sum(q_roof[:, selector])
        )
        click_sample_ind = float(
            parent_config.dt * parent_config.kappa * backend.abs2_sum(q_ind)
        )
        sample_click_difference = abs(click_sample_batch - click_sample_ind)
        independent_infos = np.asarray(info_ind, dtype=np.int32).tolist()
        independent_residuals = np.asarray(
            residual_ind, dtype=np.float64
        ).tolist()

    audit = {
        "number_rhs": count,
        "batch_columns": int(parent_config.detector_rhs_batch_columns),
        "number_batches": len(batch_sizes),
        "batch_sizes": batch_sizes,
        "maximum_actual_batch_columns": max(batch_sizes, default=0),
        "batch64_contract_respected": bool(
            all(size <= int(parent_config.detector_rhs_batch_columns) for size in batch_sizes)
        ),
        "multi_rhs_info": infos_all.tolist(),
        "maximum_multi_rhs_true_residual": (
            float(np.max(residuals_all)) if residuals_all.size else 0.0
        ),
        "multi_rhs_inner_iterations": int(iterations),
        "zero_midpoint_closure": float(zero_before - zero_after - zero_click),
        "positive_midpoint_closure": float(
            positive_before - positive_after - positive_click
        ),
        "sample_indices": sample_indices,
        "sample_independent_info": independent_infos,
        "maximum_sample_independent_true_residual": max(
            independent_residuals, default=0.0
        ),
        "sample_batch_vs_independent_relative_error": float(sample_relative),
        "sample_midpoint_probability_absolute_difference": float(
            sample_click_difference
        ),
    }
    return (
        zero_next,
        split_family(positive_next_matrix, sectors, widths),
        zero_click,
        positive_click,
        audit,
    )


def complete_step_transactional(
    state: PrefixState, *, step: int, parent: Any, operators: Any,
    parent_config: Any, propagator: Any, bath: Any, config: GateConfig,
    backend: Any, crosscheck: bool
) -> Tuple[PrefixState, Dict[str, Any]]:
    started = time.perf_counter()
    survival_before = family_trace(state.family, propagator.h_z, backend)
    zero_before = physical_trace(state.zero_state, propagator.h_z, backend)
    call_first = 2 * step - 1
    raw_first, event_first, bath_first_pre = bath_half_truncated(
        state.family, bath.operators_backend, config=config, h_z=propagator.h_z, backend=backend
    )
    first, rep_after_first, compression_first = compress_family_global_no_restore(
        raw_first,
        call_index=call_first,
        ledger_before=state.representation_ledger,
        config=config,
        h_z=propagator.h_z,
        backend=backend,
    )
    rep_first = rep_after_first - state.representation_ledger
    bath_first_closure = survival_before - family_trace(first, propagator.h_z, backend) - event_first - rep_first
    if abs(bath_first_pre["trace_closure_before_compression"]) > BATH_LEDGER_CLOSURE_TOL or abs(bath_first_closure) > BATH_LEDGER_CLOSURE_TOL:
        raise GateStop(
            "FIRST_BATH_LEDGER_CLOSURE_STOP",
            "First bath-half event/representation accounting failed",
            {"step": step, "pre": bath_first_pre, "post_closure": bath_first_closure},
        )
    if family_rank(first) > config.hard_rank_stop:
        raise GateStop(
            "RANK_FEASIBILITY_STOP",
            "Retained rank exceeded the predeclared hard pilot threshold after first bath half",
            {"step": step, "phase": "first_bath", "rank": family_rank(first)},
        )
    zero_detector, detector_family, zero_click, positive_click, detector_audit = run_bundled_detector(
        state.zero_state,
        first,
        parent=parent,
        operators=operators,
        parent_config=parent_config,
        propagator=propagator,
        backend=backend,
        crosscheck=crosscheck,
    )
    if (
        not detector_audit["batch64_contract_respected"]
        or any(detector_audit["multi_rhs_info"])
        or detector_audit["maximum_multi_rhs_true_residual"] > TRUE_RESIDUAL_TOL
        or abs(detector_audit["zero_midpoint_closure"]) > DETECTOR_CLOSURE_TOL
        or abs(detector_audit["positive_midpoint_closure"]) > DETECTOR_CLOSURE_TOL
        or detector_audit["sample_batch_vs_independent_relative_error"] > BATCH_SAMPLE_REL_TOL
        or detector_audit["sample_midpoint_probability_absolute_difference"] > BATCH_SAMPLE_CLICK_ABS_TOL
        or any(detector_audit["sample_independent_info"])
        or detector_audit["maximum_sample_independent_true_residual"] > TRUE_RESIDUAL_TOL
    ):
        raise GateStop(
            "DETECTOR_GMRES_OR_MIDPOINT_STOP",
            "Detector Batch-64, independent sample, or midpoint closure gate failed",
            {"step": step, "detector_audit": detector_audit},
        )
    trace_detector = family_trace(detector_family, propagator.h_z, backend)
    call_second = 2 * step
    raw_second, event_second, bath_second_pre = bath_half_truncated(
        detector_family, bath.operators_backend, config=config, h_z=propagator.h_z, backend=backend
    )
    second, rep_after_second, compression_second = compress_family_global_no_restore(
        raw_second,
        call_index=call_second,
        ledger_before=rep_after_first,
        config=config,
        h_z=propagator.h_z,
        backend=backend,
    )
    rep_second = rep_after_second - rep_after_first
    survival_after = family_trace(second, propagator.h_z, backend)
    bath_second_closure = trace_detector - survival_after - event_second - rep_second
    if abs(bath_second_pre["trace_closure_before_compression"]) > BATH_LEDGER_CLOSURE_TOL or abs(bath_second_closure) > BATH_LEDGER_CLOSURE_TOL:
        raise GateStop(
            "SECOND_BATH_LEDGER_CLOSURE_STOP",
            "Second bath-half event/representation accounting failed",
            {"step": step, "pre": bath_second_pre, "post_closure": bath_second_closure},
        )
    total_rank = family_rank(second)
    if total_rank > config.hard_rank_stop:
        raise GateStop(
            "RANK_FEASIBILITY_STOP",
            "Retained rank exceeded the predeclared hard pilot threshold after second bath half",
            {"step": step, "phase": "second_bath", "rank": total_rank},
        )
    event_increment = event_first + event_second
    rep_increment = rep_first + rep_second
    complete_closure = survival_before - survival_after - positive_click - event_increment - rep_increment
    zero_after = physical_trace(zero_detector, propagator.h_z, backend)
    zero_closure = zero_before - zero_after - zero_click
    if abs(complete_closure) > COMPLETE_STEP_LEDGER_CLOSURE_TOL or abs(zero_closure) > DETECTOR_CLOSURE_TOL:
        raise GateStop(
            "COMPLETE_STEP_LEDGER_CLOSURE_STOP",
            "Complete-step detector/event/representation closure failed",
            {"step": step, "positive_closure": complete_closure, "zero_closure": zero_closure},
        )
    event_ledger_after = state.event_first_crossing_ledger + event_increment
    event_bound = analytic_event_tail(step, bath, config)
    if event_ledger_after > event_bound + EVENT_BOUND_TOL:
        raise GateStop(
            "EVENT_TAIL_BOUND_STOP",
            "First-crossing event ledger exceeded the analytic binomial tail bound",
            {"step": step, "event_ledger": event_ledger_after, "analytic_bound": event_bound},
        )
    top_shell = top_shell_population(
        second, operators=operators, config=config, h_z=propagator.h_z, backend=backend
    )
    overflow_intensity = config.rate_lambda * (config.n_shell + 2.0) * top_shell
    overflow_after = state.cumulative_overflow_bound + 0.5 * config.dt * (
        state.previous_overflow_intensity + overflow_intensity
    )
    if overflow_after > TOP_SHELL_OVERFLOW_TOL:
        raise GateStop(
            "TOP_SHELL_OVERFLOW_STOP",
            "Cumulative projected upward-overflow bound exceeded tolerance",
            {"step": step, "overflow_bound": overflow_after, "top_shell": top_shell},
        )
    if survival_after < -NONNEGATIVITY_TOL or zero_after < -NONNEGATIVITY_TOL:
        raise GateStop("NEGATIVE_SURVIVAL_STOP", "Retained survival became negative", {"step": step})
    if survival_after - survival_before > SURVIVAL_INCREASE_TOL or zero_after - zero_before > SURVIVAL_INCREASE_TOL:
        raise GateStop(
            "SURVIVAL_INCREASE_STOP",
            "Survival increased beyond the numerical tolerance",
            {"step": step, "positive_increase": survival_after-survival_before, "zero_increase": zero_after-zero_before},
        )
    sector_traces, sector_ranks = family_sector_metrics(
        second, config=config, h_z=propagator.h_z, backend=backend
    )
    new_state = PrefixState(
        family=second,
        zero_state=zero_detector,
        representation_ledger=rep_after_second,
        event_first_crossing_ledger=event_ledger_after,
        cumulative_click=state.cumulative_click + positive_click,
        cumulative_zero_click=state.cumulative_zero_click + zero_click,
        cumulative_overflow_bound=overflow_after,
        previous_overflow_intensity=overflow_intensity,
        completed_step=step,
    )
    audit = {
        "step": int(step),
        "time": float(step * config.dt),
        "survival_before": survival_before,
        "survival_after": survival_after,
        "zero_survival_before": zero_before,
        "zero_survival_after": zero_after,
        "positive_midpoint_click": positive_click,
        "zero_midpoint_click": zero_click,
        "event_increment": event_increment,
        "representation_increment": rep_increment,
        "event_ledger": event_ledger_after,
        "analytic_event_tail_bound": event_bound,
        "representation_ledger": rep_after_second,
        "representation_ceiling": representation_ceiling(call_second, config),
        "complete_step_ledger_closure": complete_closure,
        "zero_step_closure": zero_closure,
        "top_shell_population": top_shell,
        "overflow_intensity": overflow_intensity,
        "cumulative_overflow_bound": overflow_after,
        "total_rank": total_rank,
        "sector_traces": sector_traces,
        "sector_ranks": sector_ranks,
        "detector": detector_audit,
        "first_bath_precompression": bath_first_pre,
        "second_bath_precompression": bath_second_pre,
        "first_compression": compression_first.__dict__,
        "second_compression": compression_second.__dict__,
        "wall_seconds": time.perf_counter() - started,
        "transactional_commit": True,
        "trace_restoration_applied": False,
    }
    return new_state, audit


def initialize_histories(config: GateConfig) -> Dict[str, np.ndarray]:
    n = config.num_steps
    k = config.max_event_sector + 1
    return {
        "times": np.arange(n + 1, dtype=np.float64) * config.dt,
        "positive_survival": np.full(n + 1, np.nan, dtype=np.float64),
        "zero_survival": np.full(n + 1, np.nan, dtype=np.float64),
        "positive_step_click": np.full(n, np.nan, dtype=np.float64),
        "zero_step_click": np.full(n, np.nan, dtype=np.float64),
        "cumulative_positive_click": np.full(n + 1, np.nan, dtype=np.float64),
        "cumulative_zero_click": np.full(n + 1, np.nan, dtype=np.float64),
        "representation_ledger": np.full(n + 1, np.nan, dtype=np.float64),
        "representation_ceiling": np.full(n + 1, np.nan, dtype=np.float64),
        "event_first_crossing_ledger": np.full(n + 1, np.nan, dtype=np.float64),
        "analytic_event_tail_bound": np.full(n + 1, np.nan, dtype=np.float64),
        "cumulative_overflow_bound": np.full(n + 1, np.nan, dtype=np.float64),
        "top_shell_population": np.full(n + 1, np.nan, dtype=np.float64),
        "total_rank": np.full(n + 1, -1, dtype=np.int64),
        "sector_traces": np.full((n + 1, k), np.nan, dtype=np.float64),
        "sector_ranks": np.full((n + 1, k), -1, dtype=np.int64),
        "gmres_max_residual": np.full(n, np.nan, dtype=np.float64),
        "batch_sample_relative_error": np.full(n, np.nan, dtype=np.float64),
        "complete_step_ledger_closure": np.full(n, np.nan, dtype=np.float64),
        "zero_step_closure": np.full(n, np.nan, dtype=np.float64),
        "step_wall_seconds": np.full(n, np.nan, dtype=np.float64),
        "representation_increment": np.full(n, np.nan, dtype=np.float64),
        "event_increment": np.full(n, np.nan, dtype=np.float64),
        "detector_number_rhs": np.full(n, -1, dtype=np.int64),
        "detector_number_batches": np.full(n, -1, dtype=np.int64),
        "detector_maximum_actual_batch_columns": np.full(n, -1, dtype=np.int64),
        "detector_batch64_contract_passed": np.zeros(n, dtype=np.int8),
    }


def record_initial(
    histories: Dict[str, np.ndarray], state: PrefixState, *, config: GateConfig,
    operators: Any, h_z: float, backend: Any
) -> None:
    histories["positive_survival"][0] = family_trace(state.family, h_z, backend)
    histories["zero_survival"][0] = physical_trace(state.zero_state, h_z, backend)
    histories["cumulative_positive_click"][0] = 0.0
    histories["cumulative_zero_click"][0] = 0.0
    histories["representation_ledger"][0] = 0.0
    histories["representation_ceiling"][0] = 0.0
    histories["event_first_crossing_ledger"][0] = 0.0
    histories["analytic_event_tail_bound"][0] = 0.0
    histories["cumulative_overflow_bound"][0] = 0.0
    histories["top_shell_population"][0] = top_shell_population(
        state.family, operators=operators, config=config, h_z=h_z, backend=backend
    )
    traces, ranks = family_sector_metrics(state.family, config=config, h_z=h_z, backend=backend)
    histories["sector_traces"][0] = traces
    histories["sector_ranks"][0] = ranks
    histories["total_rank"][0] = family_rank(state.family)


def record_step(histories: Dict[str, np.ndarray], state: PrefixState, audit: Mapping[str, Any]) -> None:
    step = int(audit["step"])
    histories["positive_survival"][step] = audit["survival_after"]
    histories["zero_survival"][step] = audit["zero_survival_after"]
    histories["positive_step_click"][step - 1] = audit["positive_midpoint_click"]
    histories["zero_step_click"][step - 1] = audit["zero_midpoint_click"]
    histories["cumulative_positive_click"][step] = state.cumulative_click
    histories["cumulative_zero_click"][step] = state.cumulative_zero_click
    histories["representation_ledger"][step] = state.representation_ledger
    histories["representation_ceiling"][step] = audit["representation_ceiling"]
    histories["event_first_crossing_ledger"][step] = state.event_first_crossing_ledger
    histories["analytic_event_tail_bound"][step] = audit["analytic_event_tail_bound"]
    histories["cumulative_overflow_bound"][step] = state.cumulative_overflow_bound
    histories["top_shell_population"][step] = audit["top_shell_population"]
    histories["total_rank"][step] = audit["total_rank"]
    histories["sector_traces"][step] = audit["sector_traces"]
    histories["sector_ranks"][step] = audit["sector_ranks"]
    histories["gmres_max_residual"][step - 1] = max(
        audit["detector"]["maximum_multi_rhs_true_residual"],
        audit["detector"]["maximum_sample_independent_true_residual"],
    )
    histories["batch_sample_relative_error"][step - 1] = audit["detector"][
        "sample_batch_vs_independent_relative_error"
    ]
    histories["complete_step_ledger_closure"][step - 1] = audit["complete_step_ledger_closure"]
    histories["zero_step_closure"][step - 1] = audit["zero_step_closure"]
    histories["step_wall_seconds"][step - 1] = audit["wall_seconds"]
    histories["representation_increment"][step - 1] = audit["representation_increment"]
    histories["event_increment"][step - 1] = audit["event_increment"]
    histories["detector_number_rhs"][step - 1] = audit["detector"]["number_rhs"]
    histories["detector_number_batches"][step - 1] = audit["detector"]["number_batches"]
    histories["detector_maximum_actual_batch_columns"][step - 1] = audit["detector"][
        "maximum_actual_batch_columns"
    ]
    histories["detector_batch64_contract_passed"][step - 1] = int(
        audit["detector"]["batch64_contract_respected"]
    )


def checkpoint_payload_hashes(directory: Path) -> Dict[str, str]:
    return {
        path.name: sha256_file(path)
        for path in sorted(directory.iterdir())
        if path.is_file() and path.name != "checkpoint_manifest.json"
    }


def save_latest_checkpoint(
    output_dir: Path, *, state: PrefixState, histories: Mapping[str, np.ndarray],
    config: GateConfig, source_sha256: str, core_sha256: str, backend: Any
) -> Path:
    tmp = output_dir / ".latest_checkpoint_tmp"
    current = output_dir / "latest_checkpoint"
    old = output_dir / ".latest_checkpoint_old"
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(old, ignore_errors=True)
    tmp.mkdir(parents=True)
    for sector, factor in sorted(state.family.items()):
        np.save(tmp / f"sector_{sector}.npy", np.asarray(backend.to_cpu(factor), dtype=np.complex128), allow_pickle=False)
    np.save(tmp / "zero_state.npy", np.asarray(backend.to_cpu(state.zero_state), dtype=np.complex128), allow_pickle=False)
    completed = state.completed_step
    arrays = {}
    for key, value in histories.items():
        if value.ndim == 1:
            arrays[key] = value[: completed + 1] if value.shape[0] == config.num_steps + 1 else value[:completed]
        elif value.ndim == 2:
            arrays[key] = value[: completed + 1]
    np.savez(tmp / "histories.npz", **arrays)
    metadata = {
        "schema": CHECKPOINT_SCHEMA,
        "created_utc": utc_now_iso(),
        "completed_step": completed,
        "physical_time": completed * config.dt,
        "source_sha256": source_sha256,
        "numerical_core_sha256": core_sha256,
        "rate_lambda": config.rate_lambda,
        "max_event_sector": config.max_event_sector,
        "representation_ledger": state.representation_ledger,
        "event_first_crossing_ledger": state.event_first_crossing_ledger,
        "cumulative_click": state.cumulative_click,
        "cumulative_zero_click": state.cumulative_zero_click,
        "cumulative_overflow_bound": state.cumulative_overflow_bound,
        "previous_overflow_intensity": state.previous_overflow_intensity,
        "sector_ranks": {str(k): int(v.shape[1]) for k, v in state.family.items()},
        "resume_enabled_in_this_source": False,
        "claim_boundary": "checkpoint is numerical evidence only; no continuation is automatically authorized",
    }
    atomic_write_json(tmp / "checkpoint_metadata.json", metadata)
    manifest = {
        "algorithm": "SHA-256",
        "files": checkpoint_payload_hashes(tmp),
    }
    atomic_write_json(tmp / "checkpoint_manifest.json", manifest)
    if current.exists():
        os.replace(current, old)
    os.replace(tmp, current)
    shutil.rmtree(old, ignore_errors=True)
    return current


def save_partial_histories(output_dir: Path, histories: Mapping[str, np.ndarray], completed: int, config: GateConfig) -> None:
    arrays: Dict[str, np.ndarray] = {}
    for key, value in histories.items():
        if value.ndim == 1:
            arrays[key] = value[: completed + 1] if value.shape[0] == config.num_steps + 1 else value[:completed]
        else:
            arrays[key] = value[: completed + 1]
    atomic_savez(output_dir / "partial_step_histories.npz", **arrays)


def build_node_products(
    histories: Mapping[str, np.ndarray], *, config: GateConfig, u2i: Optional[Mapping[str, Any]]
) -> Dict[str, np.ndarray]:
    node_steps = np.arange(0, config.num_steps + 1, config.output_stride_steps, dtype=np.int64)
    if node_steps[-1] != config.num_steps:
        node_steps = np.append(node_steps, config.num_steps)
    times = histories["times"][node_steps]
    positive_survival = histories["positive_survival"][node_steps]
    zero_survival = histories["zero_survival"][node_steps]
    representation = histories["representation_ledger"][node_steps]
    event_actual = histories["event_first_crossing_ledger"][node_steps]
    event_bound = histories["analytic_event_tail_bound"][node_steps]
    total_error_bound = representation + event_bound
    slope_lower = (positive_survival - zero_survival) / config.rate_lambda
    slope_upper = (positive_survival + total_error_bound - zero_survival) / config.rate_lambda
    if u2i is None:
        u2i_reference = zero_survival.copy()
        u2i_chi = np.zeros_like(times)
    else:
        u2i_reference = np.asarray(u2i["reference_survival"], dtype=np.float64)
        u2i_chi = np.asarray(u2i["chi_survival"], dtype=np.float64)
        if u2i_chi.shape != times.shape or u2i_reference.shape != times.shape:
            raise GateBlocked("U2-I prefix shape mismatch")
    tangent_interval_distance = np.maximum(
        np.maximum(slope_lower - u2i_chi, u2i_chi - slope_upper), 0.0
    )
    return {
        "node_steps": node_steps,
        "times": times,
        "positive_survival_retained": positive_survival,
        "zero_survival_fresh": zero_survival,
        "zero_survival_u2i_reference": u2i_reference,
        "u2i_chi_survival": u2i_chi,
        "finite_difference_slope_lower": slope_lower,
        "finite_difference_slope_upper": slope_upper,
        "u2i_tangent_interval_distance_diagnostic": tangent_interval_distance,
        "cumulative_positive_click_retained": histories["cumulative_positive_click"][node_steps],
        "cumulative_zero_click": histories["cumulative_zero_click"][node_steps],
        "representation_ledger": representation,
        "event_first_crossing_ledger": event_actual,
        "analytic_event_tail_bound": event_bound,
        "total_state_and_law_error_bound": total_error_bound,
        "representation_ceiling": histories["representation_ceiling"][node_steps],
        "cumulative_overflow_bound": histories["cumulative_overflow_bound"][node_steps],
        "top_shell_population": histories["top_shell_population"][node_steps],
        "total_rank": histories["total_rank"][node_steps],
        "sector_traces": histories["sector_traces"][node_steps],
        "sector_ranks": histories["sector_ranks"][node_steps],
    }


def finite_array_checks(arrays: Mapping[str, np.ndarray]) -> bool:
    for value in arrays.values():
        if np.issubdtype(value.dtype, np.number) and not np.all(np.isfinite(value)):
            return False
    return True


def output_hash_manifest(output_dir: Path, names: Iterable[str]) -> Dict[str, Any]:
    return {
        "algorithm": "SHA-256",
        "files": {name: sha256_file(output_dir / name) for name in sorted(names)},
    }


def run_prefix(
    config: GateConfig, package_dir: Path, *, require_a100: bool = True
) -> Dict[str, Any]:
    started = time.perf_counter()
    parent_result = verify_g1p_result(package_dir)
    parent, parent_identity = load_parent_authority(package_dir)
    call_scope = parent_call_scope_audit(Path(__file__).resolve())
    if not call_scope["passed"]:
        raise GateBlocked(f"Parent call-scope audit failed: {call_scope}")
    u2i = load_u2i_reference(package_dir, config) if config.require_u2i_reference else None
    backend = parent.NumericalBackend(config.backend)
    backend_metadata = backend.metadata()
    device_name = str(backend_metadata.get("cuda_device_name", ""))
    if require_a100 and not (config.backend == "cupy" and "A100" in device_name.upper()):
        raise GateBlocked(f"ES-G2P requires a ZIB A100 CuPy backend; found {backend_metadata}")
    if not config.development_mode and not (
        config.num_steps * config.dt == config.t_final
        and config.n_shell == N_SHELL
        and config.n_z == N_Z
        and config.max_event_sector == MAX_EVENT_SECTOR
        and abs(config.rate_lambda - RATE_LAMBDA) <= 0.0
        and config.output_stride_steps * config.dt == 0.05
        and abs(config.representation_blocks[-1][1] - REPRESENTATION_BUDGET_PREFIX) <= 0.0
    ):
        raise GateBlocked("Production ES-G2P configuration changed")
    operators = parent.build_oscillator_operators(config.n_shell, config.omega)
    if not operators.audit["all_checks_passed"]:
        raise GateBlocked("Oscillator operator authority failed")
    parent_config = parent.RunConfig(
        execution_gate="ES-G2P",
        backend=config.backend,
        n_shell=config.n_shell,
        n_z=config.n_z,
        l_z=config.l_z,
        dt=config.dt,
        t_final=config.t_final,
        stop_after_steps=config.num_steps,
        rate_lambda=config.rate_lambda,
        z0=config.z0,
        sigma_z_amplitude=config.sigma_z,
        k0=config.k0,
        kappa=config.kappa,
        theta=config.theta,
        phi=config.phi,
        detector_rhs_batch_columns=config.detector_batch_columns,
        factor_block_columns=config.detector_batch_columns,
        resume_from_checkpoint=False,
        representation_budget=0.0,
        planned_compression_calls=config.total_bath_half_calls,
        output_root=config.output_dir,
    )
    z, h_z, _ = parent.build_reference_grid(config.n_z, config.l_z)
    initial_cpu = parent.build_initial_state(parent_config, operators, z, h_z)
    propagator = parent.build_propagator_objects(parent_config, operators, backend, initial_cpu)
    if not (
        propagator.roof_sign_audit["spinor_roof_term_sign_passed"]
        and propagator.roof_sign_audit["derived_reactive_roof_sign"] == "+"
        and propagator.roof_sign_audit["K_contributes_no_antihermitian_loss"]
    ):
        raise GateBlocked("Detector roof authority failed")
    bath = parent.build_bath_kraus(
        operators, "upward", config.rate_lambda * config.dt / 2.0, backend
    )
    if bath.completeness_residual > BATH_COMPLETENESS_TOL:
        raise GateBlocked("Bath Kraus completeness failed")
    initial = backend.to_backend_array(initial_cpu[:, None])
    state = PrefixState(
        family={0: initial.copy()},
        zero_state=initial.copy(),
        representation_ledger=0.0,
        event_first_crossing_ledger=0.0,
        cumulative_click=0.0,
        cumulative_zero_click=0.0,
        cumulative_overflow_bound=0.0,
        previous_overflow_intensity=0.0,
        completed_step=0,
    )
    histories = initialize_histories(config)
    record_initial(histories, state, config=config, operators=operators, h_z=h_z, backend=backend)
    compression_maxima = {
        "negative_guard": 0.0,
        "trace_growth_guard": 0.0,
        "trace_identity_residual": 0.0,
        "rank_before": 1,
        "rank_after": 1,
    }
    checkpoint_paths: List[str] = []
    wall_started = time.perf_counter()
    last_audit: Optional[Dict[str, Any]] = None
    try:
        for step in range(1, config.num_steps + 1):
            if time.perf_counter() - wall_started > config.walltime_guard_seconds:
                raise GateStop(
                    "WALLTIME_FEASIBILITY_STOP",
                    "Predeclared walltime guard reached before the target prefix",
                    {"last_complete_step": state.completed_step, "elapsed_seconds": time.perf_counter()-wall_started},
                )
            crosscheck = step in set(config.independent_crosscheck_steps)
            new_state, audit = complete_step_transactional(
                state,
                step=step,
                parent=parent,
                operators=operators,
                parent_config=parent_config,
                propagator=propagator,
                bath=bath,
                config=config,
                backend=backend,
                crosscheck=crosscheck,
            )
            state = new_state
            last_audit = audit
            record_step(histories, state, audit)
            for key in ("first_compression", "second_compression"):
                comp = audit[key]
                compression_maxima["negative_guard"] = max(compression_maxima["negative_guard"], comp["negative_guard"])
                compression_maxima["trace_growth_guard"] = max(compression_maxima["trace_growth_guard"], comp["trace_growth_guard"])
                compression_maxima["trace_identity_residual"] = max(
                    compression_maxima["trace_identity_residual"], abs(comp["trace_identity_residual"])
                )
                compression_maxima["rank_before"] = max(compression_maxima["rank_before"], comp["rank_before"])
                compression_maxima["rank_after"] = max(compression_maxima["rank_after"], comp["rank_after"])
            if step in set(config.checkpoint_steps) and config.save_large_checkpoint:
                checkpoint = save_latest_checkpoint(
                    config.output_dir,
                    state=state,
                    histories=histories,
                    config=config,
                    source_sha256=sha256_file(Path(__file__).resolve()),
                    core_sha256=sha256_core(Path(__file__).resolve(), NUMERICAL_CORE_MARKER),
                    backend=backend,
                )
                checkpoint_paths.append(str(checkpoint))
            if step == 1 or step % 100 == 0:
                elapsed = time.perf_counter() - wall_started
                recent_start = max(0, step - 100)
                recent = histories["step_wall_seconds"][recent_start:step]
                recent_mean = float(np.nanmean(recent))
                eta = recent_mean * (config.num_steps - step)
                print(
                    f"[ES-G2P] step={step}/{config.num_steps} t={step*config.dt:.4f} "
                    f"S={histories['positive_survival'][step]:.12e} "
                    f"D={state.cumulative_click:.6e} rank={histories['total_rank'][step]} "
                    f"Brep={state.representation_ledger:.3e} "
                    f"Bevent={histories['analytic_event_tail_bound'][step]:.3e} "
                    f"step_s={audit['wall_seconds']:.3f} eta_s={eta:.1f}",
                    flush=True,
                )
            if step % config.output_stride_steps == 0 or step == config.num_steps:
                save_partial_histories(config.output_dir, histories, step, config)
    except GateStop as exc:
        save_partial_histories(config.output_dir, histories, state.completed_step, config)
        failure_checkpoint = None
        if config.save_large_checkpoint:
            failure_checkpoint = save_latest_checkpoint(
                config.output_dir,
                state=state,
                histories=histories,
                config=config,
                source_sha256=sha256_file(Path(__file__).resolve()),
                core_sha256=sha256_core(Path(__file__).resolve(), NUMERICAL_CORE_MARKER),
                backend=backend,
            )
        raise GateStop(
            exc.classification,
            str(exc),
            {
                **exc.event,
                "last_complete_step": state.completed_step,
                "last_complete_time": state.completed_step * config.dt,
                "last_complete_rank": family_rank(state.family),
                "last_complete_survival": family_trace(state.family, h_z, backend),
                "representation_ledger_at_stop": state.representation_ledger,
                "event_first_crossing_ledger_at_stop": state.event_first_crossing_ledger,
                "latest_complete_checkpoint": str(failure_checkpoint) if failure_checkpoint else None,
                "incomplete_step_state_committed": False,
            },
        ) from exc
    completed = state.completed_step
    if completed != config.num_steps or last_audit is None:
        raise GateStop("TARGET_NOT_REACHED", "Prefix target was not reached", {"completed_step": completed})
    node_products = build_node_products(histories, config=config, u2i=u2i)
    zero_u2i_max = float(np.max(np.abs(
        node_products["zero_survival_fresh"] - node_products["zero_survival_u2i_reference"]
    ))) if u2i is not None else 0.0
    cumulative_closure = float(
        histories["positive_survival"][completed]
        + histories["cumulative_positive_click"][completed]
        + histories["representation_ledger"][completed]
        + histories["event_first_crossing_ledger"][completed]
        - histories["positive_survival"][0]
    )
    zero_cumulative_closure = float(
        histories["zero_survival"][completed]
        + histories["cumulative_zero_click"][completed]
        - histories["zero_survival"][0]
    )
    last_window = histories["step_wall_seconds"][max(0, completed-200):completed]
    last_mean = float(np.nanmean(last_window))
    projected_additional_to_3p6 = last_mean * max(0, int(round(3.6/config.dt)) - completed)
    projected_total_hours_to_3p6 = (time.perf_counter() - wall_started + projected_additional_to_3p6) / 3600.0
    final_rank = int(histories["total_rank"][completed])
    if final_rank <= config.preferred_rank and projected_total_hours_to_3p6 <= 30.0:
        feasibility = "GREEN_PREFIX_FEASIBLE"
    elif final_rank <= config.hard_rank_stop and projected_total_hours_to_3p6 <= 60.0:
        feasibility = "AMBER_PREFIX_MARGINAL"
    else:
        feasibility = "RED_PREFIX_NOT_COMPETITIVE"
    checks = {
        "nonaccepting_flags_frozen": bool(
            not PRODUCTION_AUTHORIZED and not ACCEPTANCE_ENABLED and not TASK10_ELIGIBLE
            and not FINITE_POSITIVE_RATE_PHYSICAL_CLAIM and not U2I_PHYSICAL_ACCEPTANCE_PERFORMED
            and not CSSF_CHECKPOINT_IMPORT_ENABLED and not CSSF_PROPAGATION_ENABLED
            and not AUTOMATIC_SWEEP_ENABLED and not RESUME_ENABLED
        ),
        "parent_g1p_pass": parent_result["passed"],
        "parent_source_and_core_exact": True,
        "parent_call_scope": call_scope["passed"],
        "operator_authority": bool(operators.audit["all_checks_passed"]),
        "detector_authority": bool(propagator.roof_sign_audit["spinor_roof_term_sign_passed"]),
        "bath_completeness": bath.completeness_residual <= BATH_COMPLETENESS_TOL,
        "required_zib_a100_backend": bool((config.backend == "cupy" and "A100" in device_name.upper()) if require_a100 else True),
        "target_reached": completed == config.num_steps,
        "all_arrays_finite": finite_array_checks({k: np.asarray(v) for k, v in node_products.items()}),
        "survival_monotonic": bool(
            np.max(np.diff(histories["positive_survival"][:completed+1])) <= SURVIVAL_INCREASE_TOL
            and np.max(np.diff(histories["zero_survival"][:completed+1])) <= SURVIVAL_INCREASE_TOL
        ),
        "cumulative_ledgers_monotonic": bool(
            np.min(np.diff(histories["cumulative_positive_click"][:completed+1])) >= -NONNEGATIVITY_TOL
            and np.min(np.diff(histories["representation_ledger"][:completed+1])) >= -NONNEGATIVITY_TOL
            and np.min(np.diff(histories["event_first_crossing_ledger"][:completed+1])) >= -NONNEGATIVITY_TOL
        ),
        "representation_budget": state.representation_ledger <= REPRESENTATION_BUDGET_PREFIX + BUDGET_COMPARISON_TOL,
        "representation_ceiling_every_step": bool(np.all(
            histories["representation_ledger"][:completed+1]
            <= histories["representation_ceiling"][:completed+1] + BUDGET_COMPARISON_TOL
        )),
        "event_tail_bound": state.event_first_crossing_ledger <= histories["analytic_event_tail_bound"][completed] + EVENT_BOUND_TOL,
        "top_shell_overflow": state.cumulative_overflow_bound <= TOP_SHELL_OVERFLOW_TOL,
        "gmres": float(np.nanmax(histories["gmres_max_residual"][:completed])) <= TRUE_RESIDUAL_TOL,
        "detector_batch64_contract": bool(
            np.all(histories["detector_batch64_contract_passed"][:completed] == 1)
            and np.max(histories["detector_maximum_actual_batch_columns"][:completed])
            <= config.detector_batch_columns
        ),
        "batch_sample_crosschecks": float(np.nanmax(histories["batch_sample_relative_error"][:completed])) <= BATCH_SAMPLE_REL_TOL,
        "step_probability_closure": float(np.nanmax(np.abs(histories["complete_step_ledger_closure"][:completed]))) <= COMPLETE_STEP_LEDGER_CLOSURE_TOL,
        "zero_step_probability_closure": float(np.nanmax(np.abs(histories["zero_step_closure"][:completed]))) <= DETECTOR_CLOSURE_TOL,
        "cumulative_probability_closure": abs(cumulative_closure) <= CUMULATIVE_LEDGER_CLOSURE_TOL,
        "zero_cumulative_probability_closure": abs(zero_cumulative_closure) <= CUMULATIVE_LEDGER_CLOSURE_TOL,
        "compression_guards": bool(
            compression_maxima["negative_guard"] <= NEGATIVE_GRAM_GUARD_TOL
            and compression_maxima["trace_growth_guard"] <= COMPRESSION_TRACE_GROWTH_TOL
            and compression_maxima["trace_identity_residual"] <= COMPRESSION_TRACE_IDENTITY_TOL
        ),
        "no_trace_restoration": True,
        "rank_hard_stop": int(np.nanmax(histories["total_rank"][:completed+1])) <= config.hard_rank_stop,
        "fresh_zero_reference_matches_u2i": (zero_u2i_max <= U2I_ZERO_REFERENCE_ABS_TOL) if u2i is not None else True,
        "checkpoint_at_target": bool(
            not config.save_large_checkpoint
            or ((config.output_dir / "latest_checkpoint" / "checkpoint_metadata.json").is_file())
        ),
    }
    passed = all(checks.values())
    output_node = config.output_dir / "prefix_products.npz"
    atomic_savez(output_node, **node_products)
    step_arrays: Dict[str, np.ndarray] = {}
    for key, value in histories.items():
        step_arrays[key] = value[:completed+1] if value.shape[0] == config.num_steps+1 else value[:completed]
    atomic_savez(config.output_dir / "step_histories.npz", **step_arrays)
    final_index = -1
    tangent_diagnostic = {
        "time": float(node_products["times"][final_index]),
        "u2i_chi_survival": float(node_products["u2i_chi_survival"][final_index]),
        "linear_predicted_survival_change": float(
            config.rate_lambda * node_products["u2i_chi_survival"][final_index]
        ),
        "retained_survival_change": float(
            node_products["positive_survival_retained"][final_index]
            - node_products["zero_survival_fresh"][final_index]
        ),
        "finite_difference_slope_interval": [
            float(node_products["finite_difference_slope_lower"][final_index]),
            float(node_products["finite_difference_slope_upper"][final_index]),
        ],
        "interval_distance_from_u2i_tangent": float(
            node_products["u2i_tangent_interval_distance_diagnostic"][final_index]
        ),
        "dispositive_gate": False,
        "reason": "lambda0/8 rate-halving and production finite-step curvature remain pending",
    }
    report = {
        "schema": REPORT_SCHEMA,
        "script_version": SCRIPT_VERSION,
        "generated_utc": utc_now_iso(),
        "verdict": (
            "PASS_TASK09_ES_G2P_PREFIX155_NONACCEPTING"
            if passed else "FAIL_TASK09_ES_G2P_PREFIX155_NONACCEPTING"
        ),
        "passed": passed,
        "checks": checks,
        "feasibility_classification": feasibility,
        "configuration": {
            "rate_lambda": config.rate_lambda,
            "rate_label": "lambda0_over_4",
            "n_shell": config.n_shell,
            "n_z": config.n_z,
            "state_dimension": config.state_dimension,
            "omega": config.omega,
            "dt": config.dt,
            "t_final": config.t_final,
            "num_steps": config.num_steps,
            "max_event_sector": config.max_event_sector,
            "strang_order": "bath-half / detector-Cayley / bath-half",
            "trace_restoration": "forbidden",
            "representation_blocks": config.representation_blocks,
            "representation_budget_prefix": REPRESENTATION_BUDGET_PREFIX,
            "provisional_prompt_budget": REPRESENTATION_BUDGET_PROMPT_PROVISIONAL,
            "hard_rank_stop": config.hard_rank_stop,
            "preferred_rank": config.preferred_rank,
        },
        "parent_g1p": parent_result,
        "parent_identity": parent_identity,
        "parent_call_scope_audit": call_scope,
        "u2i_reference": ({
            "archive_sha256": u2i["archive_sha256"],
            "compact_sha256": u2i["compact_sha256"],
            "zero_reference_max_abs_difference": zero_u2i_max,
            "chi_D": U2I_CHI_D,
            "chi_mu_restricted": U2I_CHI_MU,
            "complete_signed_law_norm": U2I_ATV,
        } if u2i is not None else {"development_mode": True}),
        "backend": backend_metadata,
        "operator_audit": operators.audit,
        "detector_audit": propagator.roof_sign_audit,
        "bath_audit": {
            "action_per_half": bath.action,
            "completeness_residual": bath.completeness_residual,
            "g_max": float(np.max(bath.g_diagonal)),
        },
        "final": {
            "completed_step": completed,
            "physical_time": completed * config.dt,
            "retained_survival": float(histories["positive_survival"][completed]),
            "zero_survival": float(histories["zero_survival"][completed]),
            "cumulative_retained_click": float(histories["cumulative_positive_click"][completed]),
            "representation_ledger": state.representation_ledger,
            "event_first_crossing_ledger": state.event_first_crossing_ledger,
            "analytic_event_tail_bound": float(histories["analytic_event_tail_bound"][completed]),
            "total_state_and_law_error_bound": float(
                state.representation_ledger + histories["analytic_event_tail_bound"][completed]
            ),
            "cumulative_overflow_bound": state.cumulative_overflow_bound,
            "final_rank": final_rank,
            "maximum_rank": int(np.nanmax(histories["total_rank"][:completed+1])),
            "sector_traces": histories["sector_traces"][completed],
            "sector_ranks": histories["sector_ranks"][completed],
            "cumulative_probability_closure": cumulative_closure,
            "zero_cumulative_probability_closure": zero_cumulative_closure,
        },
        "compression_maxima": compression_maxima,
        "detector_batch_summary": {
            "configured_batch_columns": config.detector_batch_columns,
            "maximum_actual_batch_columns": int(
                np.max(histories["detector_maximum_actual_batch_columns"][:completed])
            ),
            "maximum_number_rhs": int(np.max(histories["detector_number_rhs"][:completed])),
            "maximum_number_batches": int(
                np.max(histories["detector_number_batches"][:completed])
            ),
            "all_steps_respected_batch_contract": bool(
                np.all(histories["detector_batch64_contract_passed"][:completed] == 1)
            ),
        },
        "runtime": {
            "elapsed_seconds": time.perf_counter() - wall_started,
            "last_200_step_mean_seconds": last_mean,
            "projected_total_hours_to_t3p6_at_last_rate": projected_total_hours_to_3p6,
        },
        "checkpoint_paths": checkpoint_paths,
        "tangent_diagnostic_only": tangent_diagnostic,
        "claim_boundary": {
            "interpretation": "lambda0/4 feasibility prefix through t=1.55 only",
            "production_trajectory_authorized": False,
            "continuation_beyond_t1p55_authorized": False,
            "lambda0_over_8_rate_halving_completed": False,
            "production_finite_step_second_derivative_completed": False,
            "u2i_physical_acceptance_performed": False,
            "finite_positive_rate_physical_claim": False,
            "task10_eligible": False,
            "cssf_branch_reactivated": False,
        },
        "authority": {
            "terminal_cssf_failure_archive_sha256": PARENT_CSSF_FAILURE_SHA256,
            "terminal_cssf_failure_classification": PARENT_CSSF_FAILURE_CLASSIFICATION,
            "new_scope": "positive event-sector lambda0/4 prefix feasibility through t=1.55",
            "does_not_supersede": [
                "frozen detector, bath, grid, shell, midpoint, and GMRES authorities",
                "accepted Stage-07/08 U2-I zero-rate susceptibility",
                "terminal CSSF failure classification",
                "current manuscript claim boundary",
            ],
        },
        "elapsed_seconds_total": time.perf_counter() - started,
    }
    return {
        "report": report,
        "histories": step_arrays,
        "node_products": node_products,
    }


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
    output_dir = data_root / "Task09_ES_G2P" / "4912.ES_G2P_prefix155_event_sectors_nonaccepting"
    output_dir.mkdir(parents=True, exist_ok=True)
    lock_path = output_dir / ".gate.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise GateBlocked("Another ES-G2P process holds the gate lock") from exc
        report_path = output_dir / "gate_report.json"
        if report_path.exists() and not args.overwrite:
            raise GateBlocked(f"Completed report already exists: {report_path}")
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
            "continuation_beyond_t1p55_authorized": False,
            "task10_eligible": False,
            "finite_positive_rate_physical_claim": False,
        }
        atomic_write_json(status_path, status)
        shutil.copy2(source_path, output_dir / source_path.name)
        config = GateConfig(backend=args.backend, data_root=data_root, output_dir=output_dir)
        try:
            products = run_prefix(config, package_dir, require_a100=True)
            report = products["report"]
            report["source_sha256"] = source_hash
            report["numerical_core_sha256"] = core_hash
            atomic_write_json(report_path, report)
            atomic_write_json(output_dir / "operator_audit.json", report["operator_audit"])
            atomic_write_json(output_dir / "detector_audit.json", report["detector_audit"])
            atomic_write_json(output_dir / "bath_audit.json", report["bath_audit"])
            atomic_write_json(output_dir / "tangent_diagnostic.json", report["tangent_diagnostic_only"])
            names = [
                source_path.name,
                "gate_report.json",
                "operator_audit.json",
                "detector_audit.json",
                "bath_audit.json",
                "tangent_diagnostic.json",
                "prefix_products.npz",
                "step_histories.npz",
            ]
            manifest = output_hash_manifest(output_dir, names)
            atomic_write_json(output_dir / "output_hashes.json", manifest)
            status.update({
                "status": "completed" if report["passed"] else "completed_fail",
                "completed_utc": utc_now_iso(),
                "verdict": report["verdict"],
                "feasibility_classification": report["feasibility_classification"],
                "completed_step": report["final"]["completed_step"],
                "physical_time": report["final"]["physical_time"],
            })
            atomic_write_json(status_path, status)
            print(report["verdict"])
            print(f"Feasibility: {report['feasibility_classification']}")
            print(f"Output directory: {output_dir}")
            return 0 if report["passed"] else 2
        except GateStop as exc:
            failure = {
                "status": "failed_closed",
                "failed_utc": utc_now_iso(),
                "classification": exc.classification,
                "message": str(exc),
                "event": exc.event,
                "last_complete_step": int(exc.event.get("last_complete_step", 0)),
                "production_authorized": False,
                "task10_eligible": False,
                "finite_positive_rate_physical_claim": False,
                "traceback": traceback.format_exc(),
            }
            atomic_write_json(output_dir / "failure.json", failure)
            status.update(failure)
            atomic_write_json(status_path, status)
            print(f"STOP_TASK09_ES_G2P_PREFIX155_NONACCEPTING: {exc.classification}")
            print(str(exc))
            return 2
        except Exception as exc:
            failure = {
                "status": "execution_failure",
                "failed_utc": utc_now_iso(),
                "classification": type(exc).__name__,
                "message": str(exc),
                "production_authorized": False,
                "task10_eligible": False,
                "finite_positive_rate_physical_claim": False,
                "traceback": traceback.format_exc(),
            }
            atomic_write_json(output_dir / "failure.json", failure)
            status.update(failure)
            atomic_write_json(status_path, status)
            raise


if __name__ == "__main__":
    raise SystemExit(main())
