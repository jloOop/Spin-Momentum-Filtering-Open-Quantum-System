#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_bath_only_fock_loader.py
===========================
Independent Task-04 loader/auditor for the Stage-03 detector-free transverse
bath solver ``03_bath_only_fock_test.py``.

Scientific role
---------------
This file closes the *bath-only* branch of the Part-I numerical programme.  It
is deliberately distinct from scientific Stage 04 (oscillator-channel detector
recovery and detector-generated source diagnostics).

The loader does **not** import the Stage-03 solver and does not accept the
solver's PASS flag as evidence.  It independently reconstructs the complete-
shell oscillator basis, projected operators, Liouvillian identities, analytic
controls, projected population generators, finite-shell event accounting,
coherent-amplitude residual control, dephasing laws, isotropic-basis tests, and
cutoff comparisons.  It then compares every stored solver metric, threshold,
relation, and PASS/FAIL decision with its own reconstruction.

The loader also performs a higher-resolution cutoff audit:

* 10,001-point independent population-reference curves for B2/B3;
* exact augmented-generator integration of the omitted upward intensity.

No detector, longitudinal coordinate, ABC, Crank--Nicolson step, GMRES solve,
Monte-Carlo trajectory, positivity clipping, or trace renormalization is used.

Directory contract
------------------
The directory is explicit and fixed:

    4060.Bath_only_tests

Only the root is selected by ``--out-root`` or ``OUTDIR``.  There are no
timestamps and no parameter-generated subdirectories.  Re-running this loader
reuses the same directory and replaces only the known loader products.

Run
---

    python 04_bath_only_fock_loader.py \\
        --out-root [ARCHIVE_PATH]

The audited solver products must already be present in

    [ARCHIVE_PATH]

Exit status
-----------

    0 : independent loader acceptance and solver/loader agreement PASS
    2 : files are readable, but at least one scientific/consistency gate FAILS
    1 : integrity, schema, execution, or I/O failure
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import logging
import math
import os
import platform
import shutil
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

# This is a sparse CPU audit.  Respect scheduler/user settings, otherwise avoid
# uncontrolled BLAS thread multiplication on login nodes.
for _thread_variable in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ.setdefault(_thread_variable, "1")

import numpy as np
import scipy
from scipy import linalg, sparse, special
from scipy.integrate import cumulative_trapezoid
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import expm_multiply


# =============================================================================
# Frozen Task-04 and Stage-03 contract
# =============================================================================
LOADER_STAGE_NAME = "04_bath_only_fock_loader"
LOADER_VERSION = "2026-08-03-stage03-independent-loader-v1-audited"
OUTPUT_DIRECTORY_NAME = "4060.Bath_only_tests"
LOADER_SOURCE_NAME = "04_bath_only_fock_loader.py"

SOLVER_STAGE_NAME = "03_bath_only_fock_test"
SOLVER_VERSION = "2026-08-02-stage03-bath-only-fock-v3-audited"
EXPECTED_SOLVER_SHA256 = (
    "5e621ee346604d8eef4765c07532ab3b525783af2b9a52d80fa408ef38c65bbe"
)
EXPECTED_PARENT_STAGE02_SOLVER_SHA256 = (
    "2ed0daf88dca64d33896d42e53d93c1e57b85d7e22391498babd4f7588b273b2"
)
EXPECTED_PARENT_STAGE02_LOADER_SHA256 = (
    "398a66b51c21e72216da38ef446c4e0e0012b0c23e2d6114b12b19e54e4bfc0b"
)

HBAR = 1.0
MASS = 1.0
OMEGA = 1.0
T_FINAL = 20.0
NUM_OUTPUT_TIMES = 101
HIGHRES_OUTPUT_TIMES = 10001
SHELL_CUTOFFS: Tuple[int, ...] = (8, 12, 16)
PRODUCTION_SHELL = 12
SOLVER_RNG_SEED = 20260802
LOADER_INDEPENDENT_RNG_SEED = 20260803

GAMMA_ZERO_T = 0.2
GAMMA_DOWN_THERMAL = 0.25
GAMMA_UP_THERMAL = 0.05
GAMMA_NET_THERMAL = 0.20
Q_THERMAL = 0.20
NBAR_ONE_MODE = 0.25
GAMMA_PHI = 0.20
ALPHA_X = 0.4 + 0.0j
ALPHA_Y = 0.0 + 0.0j

# The thresholds are copied as frozen numerical requirements, not imported
# from or inferred from the solver output.
ACCEPTANCE_THRESHOLDS: Dict[str, float] = {
    "operator_identity_max": 1.0e-12,
    "liouvillian_trace_row_max": 1.0e-12,
    "vectorization_action_relative_max": 1.0e-12,
    "hermiticity_action_relative_max": 1.0e-12,
    "trace_error_max": 1.0e-12,
    "hermiticity_fro_max": 1.0e-12,
    "minimum_eigenvalue_min": -1.0e-11,
    "projected_intensity_formula_max": 1.0e-12,
    "ground_stationarity_trace_distance_max": 1.0e-12,
    "one_quantum_occupation_error_max": 1.0e-11,
    "one_quantum_isotropy_max": 1.0e-12,
    "projected_population_l1_max": 1.0e-11,
    "projected_occupation_error_max": 1.0e-11,
    "infinite_law_bound_slack": 5.0e-11,
    "gibbs_generator_residual_fro_max": 1.0e-12,
    "gibbs_trace_distance_max": 1.0e-12,
    "detailed_balance_relative_max": 1.0e-12,
    "coherent_amplitude_absolute_error_max": 1.0e-6,
    "coherent_bound_excess_max": 5.0e-11,
    "coherent_residual_reconstruction_error_max": 5.0e-11,
    "dephasing_population_error_max": 1.0e-12,
    "dephasing_energy_error_max": 1.0e-12,
    "dephasing_coherence_error_max": 1.0e-12,
    "isotropic_action_relative_max": 1.0e-12,
    "production_top_shell_max": 1.0e-6,
    "production_overflow_final_max": 1.0e-6,
    "cutoff_n12_n16_occupation_max": 1.0e-6,
    "cutoff_n12_n16_purity_max": 1.0e-7,
    "cutoff_n12_n16_trace_distance_max": 1.0e-7,
    "cutoff_monotonicity_tolerance": 1.0e-13,
}

# Loader-only consistency tolerances.  They are stricter than the physical
# cutoff gates and are frozen before inspecting any desired detector effect.
SERIES_RECONSTRUCTION_ATOL = 2.0e-12
CSV_NUMERIC_COMPARISON_ATOL = 2.0e-12
ACCEPTANCE_VALUE_COMPARISON_ATOL = 2.0e-12
EXACT_OVERFLOW_VS_TRAPEZOID_ATOL = 2.0e-9
INITIAL_FINAL_DENSITY_ATOL = 2.0e-12
FRESH_RANDOM_AUDIT_MAX = 1.0e-12

REQUIRED_SOLVER_HASH_KEYS: Tuple[str, ...] = (
    "03_bath_only_fock_test.py",
    "Stage03_acceptance.json",
    "Stage03_case_metrics.csv",
    "Stage03_configuration.json",
    "Stage03_cutoff_metrics.csv",
    "Stage03_operator_audit.json",
    "Stage03_solver_audit.json",
    "Stage03_time_series.npz",
)

REQUIRED_SOLVER_FILES: Tuple[str, ...] = REQUIRED_SOLVER_HASH_KEYS + (
    "Stage03_output_hashes.json",
    "Stage03_run_status.json",
)

LOADER_PRODUCTS: Tuple[str, ...] = (
    # The source copy is not a PASS artifact.  Keeping it out of this deletion
    # list also permits the loader to be executed directly from the fixed
    # Stage-03 directory without unlinking its own running source file.  When
    # the loader is launched from elsewhere, shutil.copy2 below overwrites the
    # previous source copy with the current audited file.
    "Stage03_loader_audit.json",
    "Stage03_loader_case_metrics.csv",
    "Stage03_loader_cutoff_metrics.csv",
    "Stage03_bath_only_report.md",
    "Stage03_loader_output_hashes.json",
    "Stage03_loader_run_status.json",
    "loader_stdout.txt",
    "loader_log.txt",
    "loader_failure.json",
)

BASE_SERIES_KEYS: Tuple[str, ...] = (
    "t",
    "trace",
    "hermiticity_fro",
    "minimum_eigenvalue",
    "occupation_x",
    "occupation_y",
    "occupation_total",
    "energy",
    "purity",
    "amplitude_x",
    "amplitude_y",
    "top_shell_population",
    "downward_event_intensity",
    "upward_event_intensity_projected",
    "upward_event_intensity_formula",
    "amplitude_event_intensity_projected",
    "upward_event_intensity_omitted",
    "overflow_budget",
    "offdiagonal_fro",
    "projected_intensity_formula_error",
    "population_00",
    "population_10",
    "population_01",
    "population_20",
    "population_11",
    "coherence_00_10",
    "rho_initial",
    "rho_final",
)

CASE_SPECIFIC_SERIES_KEYS: Mapping[str, Tuple[str, ...]] = {
    "B0_N12": ("trace_distance_reference",),
    "B1x_N12": (
        "one_quantum_occupation_reference",
        "one_quantum_occupation_error",
    ),
    "B1y_N12": (
        "one_quantum_occupation_reference",
        "one_quantum_occupation_error",
    ),
    "B2_N8": (
        "population_reference_l1", "population_reference_max",
        "projected_reference_occupation", "infinite_occupation_reference",
        "infinite_occupation_error", "infinite_occupation_conservative_bound",
        "infinite_occupation_bound_excess",
    ),
    "B2_N12": (
        "population_reference_l1", "population_reference_max",
        "projected_reference_occupation", "infinite_occupation_reference",
        "infinite_occupation_error", "infinite_occupation_conservative_bound",
        "infinite_occupation_bound_excess",
    ),
    "B2_N16": (
        "population_reference_l1", "population_reference_max",
        "projected_reference_occupation", "infinite_occupation_reference",
        "infinite_occupation_error", "infinite_occupation_conservative_bound",
        "infinite_occupation_bound_excess",
    ),
    "B3_N8": (
        "population_reference_l1", "population_reference_max",
        "projected_reference_occupation", "infinite_occupation_reference",
        "infinite_occupation_error", "infinite_occupation_conservative_bound",
        "infinite_occupation_bound_excess",
    ),
    "B3_N12": (
        "population_reference_l1", "population_reference_max",
        "projected_reference_occupation", "infinite_occupation_reference",
        "infinite_occupation_error", "infinite_occupation_conservative_bound",
        "infinite_occupation_bound_excess",
    ),
    "B3_N16": (
        "population_reference_l1", "population_reference_max",
        "projected_reference_occupation", "infinite_occupation_reference",
        "infinite_occupation_error", "infinite_occupation_conservative_bound",
        "infinite_occupation_bound_excess",
    ),
    "B4_N12": ("trace_distance_reference",),
    "B5_N12": (
        "coherent_amplitude_x_reference",
        "coherent_amplitude_y_reference",
        "coherent_amplitude_x_signed_error",
        "coherent_amplitude_y_signed_error",
        "coherent_amplitude_x_error",
        "coherent_amplitude_y_error",
        "coherent_heisenberg_residual_expectation_x",
        "coherent_heisenberg_residual_expectation_y",
        "coherent_residual_absolute_integral_bound_x",
        "coherent_residual_absolute_integral_bound_y",
        "coherent_residual_reconstruction_x",
        "coherent_residual_reconstruction_y",
        "coherent_residual_reconstruction_error_x",
        "coherent_residual_reconstruction_error_y",
        "coherent_amplitude_bound_excess_x",
        "coherent_amplitude_bound_excess_y",
    ),
    "B6_N12": (
        "dephasing_population_error",
        "dephasing_occupation_error",
        "dephasing_energy_error",
        "dephasing_coherence_reference",
        "dephasing_coherence_error",
        "dephasing_rotating_coherence",
        "dephasing_rotating_reference",
    ),
}

PAIR_SERIES_KEYS: Tuple[str, ...] = (
    "t",
    "occupation_difference",
    "purity_difference",
    "trace_distance",
    "occupation_trace_distance_bound",
    "occupation_trace_distance_bound_excess",
)


@dataclass(frozen=True)
class CaseSpec:
    case_id: str
    description: str
    cutoff: int
    gamma_down: float
    gamma_up: float
    gamma_phi: float
    initial_state: str
    family: str


CASE_SPECS: Tuple[CaseSpec, ...] = (
    CaseSpec("B0_N12", "zero-temperature ground-state stationarity", 12,
             0.2, 0.0, 0.0, "|00><00|", "B0"),
    CaseSpec("B1x_N12", "one-quantum x decay", 12,
             0.2, 0.0, 0.0, "|10><10|", "B1x"),
    CaseSpec("B1y_N12", "one-quantum y decay", 12,
             0.2, 0.0, 0.0, "|01><01|", "B1y"),
    CaseSpec("B2_N12", "thermal heating from the transverse ground state", 12,
             0.25, 0.05, 0.0, "|00><00|", "B2"),
    CaseSpec("B3_N12", "thermal relaxation from the hotter state |20>", 12,
             0.25, 0.05, 0.0, "|20><20|", "B3"),
    CaseSpec("B4_N12", "projected Gibbs stationarity and detailed balance", 12,
             0.25, 0.05, 0.0, "rho_B,N proportional to q^N_perp", "B4"),
    CaseSpec("B5_N12", "coherent-amplitude decay under the thermal amplitude channel", 12,
             0.25, 0.05, 0.0,
             "projected coherent alpha_x=(0.4+0j), alpha_y=0j", "B5"),
    CaseSpec("B6_N12", "pure independent number dephasing", 12,
             0.0, 0.0, 0.2, "(|00>+|10>)(<00|+<10|)/2", "B6"),
    CaseSpec("B2_N8", "thermal heating from the transverse ground state", 8,
             0.25, 0.05, 0.0, "|00><00|", "B2"),
    CaseSpec("B3_N8", "thermal relaxation from the hotter state |20>", 8,
             0.25, 0.05, 0.0, "|20><20|", "B3"),
    CaseSpec("B2_N16", "thermal heating from the transverse ground state", 16,
             0.25, 0.05, 0.0, "|00><00|", "B2"),
    CaseSpec("B3_N16", "thermal relaxation from the hotter state |20>", 16,
             0.25, 0.05, 0.0, "|20><20|", "B3"),
)
CASE_BY_ID: Mapping[str, CaseSpec] = {spec.case_id: spec for spec in CASE_SPECS}
THERMAL_CASE_IDS: Tuple[str, ...] = (
    "B2_N8", "B2_N12", "B2_N16", "B3_N8", "B3_N12", "B3_N16"
)


# =============================================================================
# General utilities and deterministic I/O
# =============================================================================
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


def sha256_json(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    os.replace(tmp, path)


def atomic_write_csv(
    path: Path,
    rows: Sequence[Mapping[str, Any]],
    fieldnames: Sequence[str] | None = None,
) -> None:
    if fieldnames is None:
        ordered: List[str] = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    ordered.append(key)
                    seen.add(key)
        fieldnames = ordered
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
    os.replace(tmp, path)


def atomic_write_text(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")
    os.replace(tmp, path)


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise TypeError(f"Expected JSON object in {path}")
    return payload


def load_csv(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise RuntimeError(f"Missing CSV header in {path}")
        return list(reader.fieldnames), [dict(row) for row in reader]


def remove_previous_loader_products(out_dir: Path) -> None:
    # Remove every previous PASS artifact before checking the current solver.
    # This guarantees that a tampered/stale solver directory cannot retain an
    # old loader PASS record.
    for name in LOADER_PRODUCTS:
        path = out_dir / name
        if path.is_file():
            path.unlink()


def output_hash_manifest(out_dir: Path) -> Dict[str, str]:
    names = (
        LOADER_SOURCE_NAME,
        "Stage03_loader_audit.json",
        "Stage03_loader_case_metrics.csv",
        "Stage03_loader_cutoff_metrics.csv",
        "Stage03_bath_only_report.md",
    )
    return {name: sha256_file(out_dir / name) for name in names}


def finite_float(value: Any, label: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise FloatingPointError(f"Non-finite {label}: {result!r}")
    return result


def max_abs(array: np.ndarray) -> float:
    if array.size == 0:
        return 0.0
    return float(np.max(np.abs(array)))


def frobenius_norm(matrix: np.ndarray) -> float:
    return float(np.linalg.norm(matrix, ord="fro"))


def hermitize(matrix: np.ndarray) -> np.ndarray:
    return 0.5 * (matrix + matrix.conjugate().T)


def relative_norm(difference: np.ndarray, reference: np.ndarray) -> float:
    denominator = frobenius_norm(reference)
    numerator = frobenius_norm(difference)
    return numerator if denominator == 0.0 else numerator / denominator


def trace_distance(left: np.ndarray, right: np.ndarray) -> float:
    difference = hermitize(left - right)
    eigenvalues = linalg.eigvalsh(difference, check_finite=False)
    return 0.5 * float(np.sum(np.abs(eigenvalues), dtype=np.float64))


def values_close(left: float, right: float, atol: float) -> bool:
    scale = max(1.0, abs(left), abs(right))
    return abs(left - right) <= atol * scale


class Tee:
    def __init__(self, *files: Any):
        self.files = files

    def write(self, data: str) -> None:
        for file_obj in self.files:
            file_obj.write(data)
            file_obj.flush()

    def flush(self) -> None:
        for file_obj in self.files:
            file_obj.flush()


# =============================================================================
# Integrity, provenance, source, and configuration validation
# =============================================================================
def validate_solver_hashes(out_dir: Path) -> Dict[str, Any]:
    missing = [name for name in REQUIRED_SOLVER_FILES if not (out_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing required Stage-03 solver products: " + ", ".join(missing)
        )

    manifest = load_json(out_dir / "Stage03_output_hashes.json")
    if set(manifest) != set(REQUIRED_SOLVER_HASH_KEYS):
        missing_keys = sorted(set(REQUIRED_SOLVER_HASH_KEYS) - set(manifest))
        extra_keys = sorted(set(manifest) - set(REQUIRED_SOLVER_HASH_KEYS))
        raise RuntimeError(
            "Stage03_output_hashes.json key mismatch; "
            f"missing={missing_keys}, extra={extra_keys}"
        )

    records: Dict[str, Any] = {}
    all_match = True
    for name in REQUIRED_SOLVER_HASH_KEYS:
        expected = str(manifest[name])
        observed = sha256_file(out_dir / name)
        match = observed == expected
        records[name] = {
            "manifest_sha256": expected,
            "observed_sha256": observed,
            "match": match,
        }
        all_match = all_match and match
    if not all_match:
        mismatches = [name for name, item in records.items() if not item["match"]]
        raise RuntimeError(
            "Stable Stage-03 solver-output hash mismatch: " + ", ".join(mismatches)
        )

    source_hash = records["03_bath_only_fock_test.py"]["observed_sha256"]
    if source_hash != EXPECTED_SOLVER_SHA256:
        raise RuntimeError(
            "Stage-03 copied solver source is not the frozen authoritative source.\n"
            f"Expected: {EXPECTED_SOLVER_SHA256}\nObserved: {source_hash}"
        )

    return {
        "all_required_hashes_match": True,
        "stable_file_count": len(records),
        "records": records,
        "solver_fingerprint_sha256": sha256_json(manifest),
    }


def validate_solver_source_ast(source_path: Path) -> Dict[str, Any]:
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(source_path))
    imported_modules: List[str] = []
    called_names: List[str] = []
    attribute_calls: List[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                attribute_calls.append(node.func.attr)

    forbidden_imports = sorted(
        module for module in imported_modules
        if module == "cupy" or module.startswith("cupy.") or module.startswith("cupyx")
    )
    gmres_present = "gmres" in called_names or "gmres" in attribute_calls
    clipping_calls = sorted(
        name for name in set(called_names + attribute_calls)
        if name in {"clip", "clip_by_value", "maximum_eigenvalue_clipping"}
    )
    expm_present = "expm_multiply" in called_names or "expm_multiply" in source

    guards = {
        "ast_parse_pass": True,
        "imported_modules": sorted(set(imported_modules)),
        "forbidden_cupy_imports": forbidden_imports,
        "gmres_call_present": gmres_present,
        "positivity_clipping_call_names": clipping_calls,
        "expm_multiply_present": expm_present,
        "source_import_guard_pass": (
            not forbidden_imports and not gmres_present and not clipping_calls and expm_present
        ),
    }
    if not guards["source_import_guard_pass"]:
        raise RuntimeError(f"Stage-03 source implementation guard failed: {guards}")
    return guards


def validate_configuration_and_status(out_dir: Path) -> Dict[str, Any]:
    config = load_json(out_dir / "Stage03_configuration.json")
    status = load_json(out_dir / "Stage03_run_status.json")
    solver_audit = load_json(out_dir / "Stage03_solver_audit.json")
    solver_acceptance = load_json(out_dir / "Stage03_acceptance.json")

    stored_config_hash = str(config.get("configuration_sha256", ""))
    payload = dict(config)
    payload.pop("configuration_sha256", None)
    recomputed_config_hash = sha256_json(payload)
    if stored_config_hash != recomputed_config_hash:
        raise RuntimeError(
            "Stage03_configuration.json internal SHA-256 mismatch: "
            f"stored={stored_config_hash}, recomputed={recomputed_config_hash}"
        )

    expected_values: Tuple[Tuple[str, Any, Any], ...] = (
        ("stage", config.get("stage"), SOLVER_STAGE_NAME),
        ("script_version", config.get("script_version"), SOLVER_VERSION),
        ("script_sha256", config.get("script_sha256"), EXPECTED_SOLVER_SHA256),
        ("fixed directory", config.get("directory_contract", {}).get("fixed_directory_name"), OUTPUT_DIRECTORY_NAME),
        ("timestamped directories", config.get("directory_contract", {}).get("timestamped_directories"), False),
        ("parameter directories", config.get("directory_contract", {}).get("parameter_generated_directories"), False),
        ("basis cutoffs", config.get("basis", {}).get("complete_shell_cutoffs"), list(SHELL_CUTOFFS)),
        ("production shell", config.get("basis", {}).get("production_shell_for_this_certification"), PRODUCTION_SHELL),
        ("basis ordering", config.get("basis", {}).get("ordering"), "shell ascending, n_x descending within each shell"),
        ("vectorization order", config.get("vectorization", {}).get("numpy_order"), "F"),
        ("hbar", config.get("parameters", {}).get("hbar"), HBAR),
        ("mass", config.get("parameters", {}).get("mass"), MASS),
        ("omega", config.get("parameters", {}).get("omega"), OMEGA),
        ("T final", config.get("parameters", {}).get("T_final"), T_FINAL),
        ("output times", config.get("parameters", {}).get("number_of_output_times"), NUM_OUTPUT_TIMES),
        ("gamma zero T", config.get("parameters", {}).get("gamma_zero_temperature"), GAMMA_ZERO_T),
        ("gamma down", config.get("parameters", {}).get("gamma_down_thermal"), GAMMA_DOWN_THERMAL),
        ("gamma up", config.get("parameters", {}).get("gamma_up_thermal"), GAMMA_UP_THERMAL),
        ("gamma net", config.get("parameters", {}).get("gamma_net_thermal"), GAMMA_NET_THERMAL),
        ("q thermal", config.get("parameters", {}).get("q_thermal"), Q_THERMAL),
        ("nbar", config.get("parameters", {}).get("nbar_one_mode"), NBAR_ONE_MODE),
        ("gamma phi", config.get("parameters", {}).get("gamma_phi"), GAMMA_PHI),
        ("alpha x real", config.get("parameters", {}).get("alpha_x_real"), ALPHA_X.real),
        ("alpha x imag", config.get("parameters", {}).get("alpha_x_imag"), ALPHA_X.imag),
        ("alpha y real", config.get("parameters", {}).get("alpha_y_real"), ALPHA_Y.real),
        ("alpha y imag", config.get("parameters", {}).get("alpha_y_imag"), ALPHA_Y.imag),
        ("solver seed", config.get("parameters", {}).get("rng_seed"), SOLVER_RNG_SEED),
        ("thresholds", config.get("acceptance_thresholds"), ACCEPTANCE_THRESHOLDS),
        ("parent Stage02 solver", config.get("provenance", {}).get("parent_stage02_solver_sha256"), EXPECTED_PARENT_STAGE02_SOLVER_SHA256),
        ("parent Stage02 loader", config.get("provenance", {}).get("parent_stage02_loader_sha256"), EXPECTED_PARENT_STAGE02_LOADER_SHA256),
    )
    mismatches = [
        {"field": label, "observed": observed, "expected": expected}
        for label, observed, expected in expected_values
        if observed != expected
    ]
    if mismatches:
        raise RuntimeError(f"Frozen Stage-03 configuration mismatch: {mismatches}")

    if status.get("status") != "completed" or status.get("accepted") is not True:
        raise RuntimeError(f"Stage03_run_status.json is not completed/PASS: {status}")
    if solver_audit.get("status") != "completed" or solver_audit.get("accepted") is not True:
        raise RuntimeError(f"Stage03_solver_audit.json is not completed/PASS: {solver_audit}")
    if solver_acceptance.get("accepted") is not True:
        raise RuntimeError("Stage03_acceptance.json does not report solver PASS")
    if int(solver_audit.get("acceptance_check_count", -1)) != 32:
        raise RuntimeError("Stage03_solver_audit.json does not report 32 checks")
    if int(solver_audit.get("acceptance_pass_count", -1)) != 32:
        raise RuntimeError("Stage03_solver_audit.json does not report 32 passes")

    for payload_name, object_ in (
        ("run_status", status),
        ("solver_audit", solver_audit),
    ):
        if object_.get("script_sha256") != EXPECTED_SOLVER_SHA256:
            raise RuntimeError(f"{payload_name} source hash mismatch")
        if object_.get("script_version") != SOLVER_VERSION:
            raise RuntimeError(f"{payload_name} solver-version mismatch")

    guards = solver_audit.get("implementation_guards", {})
    expected_guards = {
        "detector_present": False,
        "longitudinal_coordinate_present": False,
        "monte_carlo_present": False,
        "positivity_clipping_present": False,
        "trace_renormalization_present": False,
        "density_dtype": "complex128",
        "operator_backend": "SciPy sparse CPU",
        "propagator": "scipy.sparse.linalg.expm_multiply",
        "density_vectorization": "column-major order='F'",
    }
    if guards != expected_guards:
        raise RuntimeError(
            f"Stage03_solver_audit implementation guards mismatch: {guards}"
        )

    return {
        "configuration_internal_hash_match": True,
        "configuration_sha256": stored_config_hash,
        "frozen_configuration_match": True,
        "run_status_completed": True,
        "solver_audit_completed": True,
        "solver_acceptance_record_pass": True,
        "solver_acceptance_check_count": 32,
        "implementation_guards_match": True,
        "config": config,
        "status": status,
        "solver_audit": solver_audit,
        "solver_acceptance": solver_acceptance,
    }


# =============================================================================
# Independent complete-shell oscillator and GKSL reconstruction
# =============================================================================
@dataclass(frozen=True)
class IndependentOperators:
    cutoff: int
    labels: Tuple[Tuple[int, int], ...]
    index: Mapping[Tuple[int, int], int]
    a_x: csr_matrix
    a_y: csr_matrix
    a_x_dag: csr_matrix
    a_y_dag: csr_matrix
    n_x: csr_matrix
    n_y: csr_matrix
    n_total: csr_matrix
    hamiltonian: csr_matrix
    identity: csr_matrix
    top_projector: csr_matrix
    shell_values: np.ndarray
    n_x_values: np.ndarray
    n_y_values: np.ndarray

    @property
    def dimension(self) -> int:
        return len(self.labels)


def enumerate_complete_shell(cutoff: int) -> Tuple[Tuple[int, int], ...]:
    labels: List[Tuple[int, int]] = []
    for total in range(cutoff + 1):
        labels.extend((n_x, total - n_x) for n_x in range(total, -1, -1))
    return tuple(labels)


def construct_independent_operators(cutoff: int) -> IndependentOperators:
    labels = enumerate_complete_shell(cutoff)
    index = {label: position for position, label in enumerate(labels)}
    dimension = len(labels)
    rows_x: List[int] = []
    cols_x: List[int] = []
    data_x: List[float] = []
    rows_y: List[int] = []
    cols_y: List[int] = []
    data_y: List[float] = []
    n_x_values = np.empty(dimension, dtype=np.float64)
    n_y_values = np.empty(dimension, dtype=np.float64)
    shell_values = np.empty(dimension, dtype=np.int64)

    for column, (n_x, n_y) in enumerate(labels):
        n_x_values[column] = n_x
        n_y_values[column] = n_y
        shell_values[column] = n_x + n_y
        if n_x:
            rows_x.append(index[(n_x - 1, n_y)])
            cols_x.append(column)
            data_x.append(math.sqrt(n_x))
        if n_y:
            rows_y.append(index[(n_x, n_y - 1)])
            cols_y.append(column)
            data_y.append(math.sqrt(n_y))

    a_x = csr_matrix((np.asarray(data_x, dtype=np.complex128), (rows_x, cols_x)),
                     shape=(dimension, dimension), dtype=np.complex128)
    a_y = csr_matrix((np.asarray(data_y, dtype=np.complex128), (rows_y, cols_y)),
                     shape=(dimension, dimension), dtype=np.complex128)
    a_x_dag = a_x.getH().tocsr()
    a_y_dag = a_y.getH().tocsr()
    n_x = (a_x_dag @ a_x).tocsr()
    n_y = (a_y_dag @ a_y).tocsr()
    n_total = (n_x + n_y).tocsr()
    identity = sparse.eye(dimension, format="csr", dtype=np.complex128)
    hamiltonian = (OMEGA * (n_total + identity)).tocsr()
    top_projector = sparse.diags(
        (shell_values == cutoff).astype(np.complex128), format="csr"
    )
    return IndependentOperators(
        cutoff=cutoff,
        labels=labels,
        index=index,
        a_x=a_x,
        a_y=a_y,
        a_x_dag=a_x_dag,
        a_y_dag=a_y_dag,
        n_x=n_x,
        n_y=n_y,
        n_total=n_total,
        hamiltonian=hamiltonian,
        identity=identity,
        top_projector=top_projector,
        shell_values=shell_values,
        n_x_values=n_x_values,
        n_y_values=n_y_values,
    )


def vectorize_column_major(matrix: np.ndarray) -> np.ndarray:
    return np.asarray(matrix, dtype=np.complex128).reshape(-1, order="F")


def unvectorize_column_major(vector: np.ndarray, dimension: int) -> np.ndarray:
    return np.asarray(vector, dtype=np.complex128).reshape((dimension, dimension), order="F")


def independent_dissipator_matrix(operator: csr_matrix, identity: csr_matrix) -> csr_matrix:
    gram = (operator.getH() @ operator).tocsr()
    jump = sparse.kron(operator.conjugate(), operator, format="csr")
    return (
        jump
        - 0.5 * sparse.kron(identity, gram, format="csr")
        - 0.5 * sparse.kron(gram.transpose(), identity, format="csr")
    ).tocsr()


def independent_liouvillian(
    operators: IndependentOperators,
    gamma_down: float,
    gamma_up: float,
    gamma_phi: float,
) -> csr_matrix:
    identity = operators.identity
    hamiltonian = operators.hamiltonian
    generator = -1j * (
        sparse.kron(identity, hamiltonian, format="csr")
        - sparse.kron(hamiltonian.transpose(), identity, format="csr")
    )
    if gamma_down:
        generator = generator + gamma_down * (
            independent_dissipator_matrix(operators.a_x, identity)
            + independent_dissipator_matrix(operators.a_y, identity)
        )
    if gamma_up:
        generator = generator + gamma_up * (
            independent_dissipator_matrix(operators.a_x_dag, identity)
            + independent_dissipator_matrix(operators.a_y_dag, identity)
        )
    if gamma_phi:
        generator = generator + gamma_phi * (
            independent_dissipator_matrix(operators.n_x, identity)
            + independent_dissipator_matrix(operators.n_y, identity)
        )
    result = generator.tocsr().astype(np.complex128)
    result.eliminate_zeros()
    return result


def direct_dissipator(operator: csr_matrix, density: np.ndarray) -> np.ndarray:
    op = operator.toarray()
    op_dag = op.conjugate().T
    gram = op_dag @ op
    return op @ density @ op_dag - 0.5 * (gram @ density + density @ gram)


def direct_generator_action(
    operators: IndependentOperators,
    density: np.ndarray,
    gamma_down: float,
    gamma_up: float,
    gamma_phi: float,
) -> np.ndarray:
    hamiltonian = operators.hamiltonian.toarray()
    result = -1j * (hamiltonian @ density - density @ hamiltonian)
    if gamma_down:
        result += gamma_down * (
            direct_dissipator(operators.a_x, density)
            + direct_dissipator(operators.a_y, density)
        )
    if gamma_up:
        result += gamma_up * (
            direct_dissipator(operators.a_x_dag, density)
            + direct_dissipator(operators.a_y_dag, density)
        )
    if gamma_phi:
        result += gamma_phi * (
            direct_dissipator(operators.n_x, density)
            + direct_dissipator(operators.n_y, density)
        )
    return np.asarray(result, dtype=np.complex128)


def direct_adjoint_dissipator(operator: csr_matrix, observable: np.ndarray) -> np.ndarray:
    op = operator.toarray()
    op_dag = op.conjugate().T
    gram = op_dag @ op
    return op_dag @ observable @ op - 0.5 * (gram @ observable + observable @ gram)


def direct_adjoint_generator_action(
    operators: IndependentOperators,
    observable: np.ndarray,
    gamma_down: float,
    gamma_up: float,
    gamma_phi: float,
) -> np.ndarray:
    hamiltonian = operators.hamiltonian.toarray()
    result = 1j * (hamiltonian @ observable - observable @ hamiltonian)
    if gamma_down:
        result += gamma_down * (
            direct_adjoint_dissipator(operators.a_x, observable)
            + direct_adjoint_dissipator(operators.a_y, observable)
        )
    if gamma_up:
        result += gamma_up * (
            direct_adjoint_dissipator(operators.a_x_dag, observable)
            + direct_adjoint_dissipator(operators.a_y_dag, observable)
        )
    if gamma_phi:
        result += gamma_phi * (
            direct_adjoint_dissipator(operators.n_x, observable)
            + direct_adjoint_dissipator(operators.n_y, observable)
        )
    return np.asarray(result, dtype=np.complex128)


def random_hermitian(dimension: int, rng: np.random.Generator) -> np.ndarray:
    raw = rng.normal(size=(dimension, dimension)) + 1j * rng.normal(
        size=(dimension, dimension)
    )
    matrix = hermitize(raw)
    norm = frobenius_norm(matrix)
    if norm == 0.0:
        raise RuntimeError("Random Hermitian matrix has zero norm")
    return matrix / norm


def random_unitary_2(rng: np.random.Generator) -> np.ndarray:
    raw = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
    q_matrix, r_matrix = np.linalg.qr(raw)
    diagonal = np.diag(r_matrix)
    phases = np.ones(2, dtype=np.complex128)
    nonzero = np.abs(diagonal) > 0.0
    phases[nonzero] = diagonal[nonzero] / np.abs(diagonal[nonzero])
    return q_matrix @ np.diag(phases.conjugate())


def dissipator_sum(operators: Sequence[csr_matrix], density: np.ndarray) -> np.ndarray:
    result = np.zeros_like(density, dtype=np.complex128)
    for operator in operators:
        result += direct_dissipator(operator, density)
    return result


def operator_audit_with_rng(
    operators_by_cutoff: Mapping[int, IndependentOperators],
    rng: np.random.Generator,
) -> Dict[str, Any]:
    per_cutoff: Dict[str, Dict[str, Any]] = {}
    maxima = {
        "number_diagonal_error": 0.0,
        "hamiltonian_diagonal_error": 0.0,
        "bohr_relation_error": 0.0,
        "top_shell_upward_identity_error": 0.0,
        "liouvillian_trace_row_error": 0.0,
        "vectorization_action_relative_error": 0.0,
        "hermiticity_action_relative_error": 0.0,
    }

    for cutoff in SHELL_CUTOFFS:
        operators = operators_by_cutoff[cutoff]
        dimension = operators.dimension
        nx = operators.n_x.toarray()
        ny = operators.n_y.toarray()
        h = operators.hamiltonian.toarray()
        expected_nx = np.diag(operators.n_x_values.astype(np.complex128))
        expected_ny = np.diag(operators.n_y_values.astype(np.complex128))
        expected_h = np.diag((OMEGA * (operators.shell_values + 1)).astype(np.complex128))
        number_error = max(max_abs(nx - expected_nx), max_abs(ny - expected_ny))
        h_error = max_abs(h - expected_h)

        bohr_errors = (
            max_abs((operators.hamiltonian @ operators.a_x
                     - operators.a_x @ operators.hamiltonian).toarray()
                    + OMEGA * operators.a_x.toarray()),
            max_abs((operators.hamiltonian @ operators.a_y
                     - operators.a_y @ operators.hamiltonian).toarray()
                    + OMEGA * operators.a_y.toarray()),
            max_abs((operators.hamiltonian @ operators.a_x_dag
                     - operators.a_x_dag @ operators.hamiltonian).toarray()
                    - OMEGA * operators.a_x_dag.toarray()),
            max_abs((operators.hamiltonian @ operators.a_y_dag
                     - operators.a_y_dag @ operators.hamiltonian).toarray()
                    - OMEGA * operators.a_y_dag.toarray()),
        )
        bohr_error = max(bohr_errors)

        upward_gram = (
            operators.a_x @ operators.a_x_dag
            + operators.a_y @ operators.a_y_dag
        ).tocsr()
        expected_upward = (
            operators.n_total
            + 2.0 * operators.identity
            - (cutoff + 2.0) * operators.top_projector
        ).tocsr()
        upward_error = max_abs((upward_gram - expected_upward).toarray())

        generator = independent_liouvillian(operators, 0.25, 0.05, 0.2)
        trace_vector = vectorize_column_major(np.eye(dimension, dtype=np.complex128))
        trace_row_error = max_abs(generator.transpose() @ trace_vector)
        test_density = random_hermitian(dimension, rng)
        direct = direct_generator_action(operators, test_density, 0.25, 0.05, 0.2)
        vectorized = unvectorize_column_major(
            generator @ vectorize_column_major(test_density), dimension
        )
        vectorization_error = relative_norm(vectorized - direct, direct)
        hermiticity_error = relative_norm(
            vectorized - vectorized.conjugate().T, vectorized
        )

        record = {
            "cutoff": cutoff,
            "dimension": dimension,
            "liouville_dimension": dimension * dimension,
            "annihilation_x_nnz": int(operators.a_x.nnz),
            "annihilation_y_nnz": int(operators.a_y.nnz),
            "audit_liouvillian_nnz": int(generator.nnz),
            "number_diagonal_error": number_error,
            "hamiltonian_diagonal_error": h_error,
            "bohr_relation_error": bohr_error,
            "top_shell_upward_identity_error": upward_error,
            "liouvillian_trace_row_error": trace_row_error,
            "vectorization_action_relative_error": vectorization_error,
            "hermiticity_action_relative_error": hermiticity_error,
            "basis_order": "shell ascending, n_x descending within each shell",
            "density_vectorization": "column-major order='F'",
        }
        per_cutoff[str(cutoff)] = record
        for key in maxima:
            maxima[key] = max(float(maxima[key]), float(record[key]))

    return {
        "per_cutoff": per_cutoff,
        "maximum_defects": maxima,
    }


def isotropy_audit_with_rng(
    operators: IndependentOperators,
    rng: np.random.Generator,
    unitary_count: int = 5,
    matrix_count: int = 5,
) -> Dict[str, Any]:
    max_down = 0.0
    max_up = 0.0
    reference_down_ops = (operators.a_x, operators.a_y)
    reference_up_ops = (operators.a_x_dag, operators.a_y_dag)
    for _ in range(unitary_count):
        unitary = random_unitary_2(rng)
        rotated_down = tuple(
            (unitary[row, 0] * operators.a_x
             + unitary[row, 1] * operators.a_y).tocsr()
            for row in range(2)
        )
        rotated_up = tuple(item.getH().tocsr() for item in rotated_down)
        for _ in range(matrix_count):
            density = random_hermitian(operators.dimension, rng)
            ref_down = dissipator_sum(reference_down_ops, density)
            rot_down = dissipator_sum(rotated_down, density)
            ref_up = dissipator_sum(reference_up_ops, density)
            rot_up = dissipator_sum(rotated_up, density)
            max_down = max(max_down, relative_norm(rot_down - ref_down, ref_down))
            max_up = max(max_up, relative_norm(rot_up - ref_up, ref_up))
    return {
        "unitary_count": unitary_count,
        "matrix_count_per_unitary": matrix_count,
        "maximum_annihilation_relative_action_defect": max_down,
        "maximum_creation_relative_action_defect": max_up,
    }


def replay_and_fresh_operator_audits(
    operators_by_cutoff: Mapping[int, IndependentOperators],
) -> Dict[str, Any]:
    replay_rng = np.random.default_rng(SOLVER_RNG_SEED)
    replay_operator = operator_audit_with_rng(operators_by_cutoff, replay_rng)
    replay_b7 = isotropy_audit_with_rng(operators_by_cutoff[12], replay_rng)

    fresh_rng = np.random.default_rng(LOADER_INDEPENDENT_RNG_SEED)
    fresh_operator = operator_audit_with_rng(operators_by_cutoff, fresh_rng)
    fresh_b7 = isotropy_audit_with_rng(operators_by_cutoff[12], fresh_rng)
    fresh_max = max(
        fresh_operator["maximum_defects"]["liouvillian_trace_row_error"],
        fresh_operator["maximum_defects"]["vectorization_action_relative_error"],
        fresh_operator["maximum_defects"]["hermiticity_action_relative_error"],
        fresh_b7["maximum_annihilation_relative_action_defect"],
        fresh_b7["maximum_creation_relative_action_defect"],
    )
    return {
        "replay_operator": replay_operator,
        "replay_b7": replay_b7,
        "fresh_operator": fresh_operator,
        "fresh_b7": fresh_b7,
        "fresh_random_maximum_defect": fresh_max,
        "fresh_random_audit_pass": fresh_max <= FRESH_RANDOM_AUDIT_MAX,
    }


# =============================================================================
# Independent initial states and classical population references
# =============================================================================
def basis_density(operators: IndependentOperators, n_x: int, n_y: int) -> np.ndarray:
    density = np.zeros((operators.dimension, operators.dimension), dtype=np.complex128)
    density[operators.index[(n_x, n_y)], operators.index[(n_x, n_y)]] = 1.0
    return density


def projected_gibbs_density(operators: IndependentOperators) -> np.ndarray:
    weights = np.power(Q_THERMAL, operators.shell_values, dtype=np.float64)
    weights /= np.sum(weights, dtype=np.float64)
    return np.diag(weights.astype(np.complex128))


def projected_coherent_density(
    operators: IndependentOperators,
) -> Tuple[np.ndarray, float]:
    coefficients = np.empty(operators.dimension, dtype=np.complex128)
    gaussian = math.exp(-0.5 * (abs(ALPHA_X) ** 2 + abs(ALPHA_Y) ** 2))
    for position, (n_x, n_y) in enumerate(operators.labels):
        coefficients[position] = (
            gaussian
            * ALPHA_X**n_x
            * ALPHA_Y**n_y
            / math.sqrt(math.factorial(n_x) * math.factorial(n_y))
        )
    retained = float(np.vdot(coefficients, coefficients).real)
    coefficients /= math.sqrt(retained)
    tail = float(special.gammainc(
        operators.cutoff + 1, abs(ALPHA_X) ** 2 + abs(ALPHA_Y) ** 2
    ))
    return np.outer(coefficients, coefficients.conjugate()), tail


def dephasing_initial_density(operators: IndependentOperators) -> np.ndarray:
    vector = np.zeros(operators.dimension, dtype=np.complex128)
    vector[operators.index[(0, 0)]] = 1.0 / math.sqrt(2.0)
    vector[operators.index[(1, 0)]] = 1.0 / math.sqrt(2.0)
    return np.outer(vector, vector.conjugate())


def expected_initial_density(
    spec: CaseSpec,
    operators: IndependentOperators,
) -> np.ndarray:
    if spec.family in {"B0", "B2"}:
        return basis_density(operators, 0, 0)
    if spec.family == "B1x":
        return basis_density(operators, 1, 0)
    if spec.family == "B1y":
        return basis_density(operators, 0, 1)
    if spec.family == "B3":
        return basis_density(operators, 2, 0)
    if spec.family == "B4":
        return projected_gibbs_density(operators)
    if spec.family == "B5":
        return projected_coherent_density(operators)[0]
    if spec.family == "B6":
        return dephasing_initial_density(operators)
    raise ValueError(f"Unknown case family {spec.family}")


def independent_population_generator(
    operators: IndependentOperators,
    gamma_down: float,
    gamma_up: float,
) -> csr_matrix:
    rows: List[int] = []
    cols: List[int] = []
    values: List[float] = []
    for column, (n_x, n_y) in enumerate(operators.labels):
        out_rate = 0.0
        if n_x > 0 and gamma_down:
            rate = gamma_down * n_x
            rows.append(operators.index[(n_x - 1, n_y)])
            cols.append(column)
            values.append(rate)
            out_rate += rate
        if n_y > 0 and gamma_down:
            rate = gamma_down * n_y
            rows.append(operators.index[(n_x, n_y - 1)])
            cols.append(column)
            values.append(rate)
            out_rate += rate
        if n_x + n_y < operators.cutoff and gamma_up:
            rate_x = gamma_up * (n_x + 1)
            rate_y = gamma_up * (n_y + 1)
            rows.extend((operators.index[(n_x + 1, n_y)], operators.index[(n_x, n_y + 1)]))
            cols.extend((column, column))
            values.extend((rate_x, rate_y))
            out_rate += rate_x + rate_y
        rows.append(column)
        cols.append(column)
        values.append(-out_rate)
    generator = csr_matrix(
        (np.asarray(values, dtype=np.float64), (rows, cols)),
        shape=(operators.dimension, operators.dimension),
        dtype=np.float64,
    )
    generator.eliminate_zeros()
    return generator


def population_initial_vector(spec: CaseSpec, operators: IndependentOperators) -> np.ndarray:
    vector = np.zeros(operators.dimension, dtype=np.float64)
    label = (0, 0) if spec.family == "B2" else (2, 0)
    vector[operators.index[label]] = 1.0
    return vector


def propagate_population_reference(
    generator: csr_matrix,
    initial: np.ndarray,
    number_of_times: int,
) -> np.ndarray:
    return np.asarray(
        expm_multiply(
            generator,
            initial,
            start=0.0,
            stop=T_FINAL,
            num=number_of_times,
            endpoint=True,
        ),
        dtype=np.float64,
    )


def exact_augmented_overflow(
    operators: IndependentOperators,
    generator: csr_matrix,
    initial: np.ndarray,
) -> float:
    omitted_row = (
        GAMMA_UP_THERMAL
        * (operators.cutoff + 2.0)
        * (operators.shell_values == operators.cutoff).astype(np.float64)
    )
    dimension = operators.dimension
    augmented = sparse.bmat(
        [
            [generator, sparse.csr_matrix((dimension, 1), dtype=np.float64)],
            [sparse.csr_matrix(omitted_row.reshape(1, -1)), sparse.csr_matrix((1, 1), dtype=np.float64)],
        ],
        format="csr",
        dtype=np.float64,
    )
    initial_augmented = np.concatenate((initial, np.asarray([0.0], dtype=np.float64)))
    final = expm_multiply(T_FINAL * augmented, initial_augmented)
    return float(final[-1])


# =============================================================================
# NPZ schema and raw series reconstruction
# =============================================================================
def expected_npz_keys() -> set[str]:
    keys = {
        "global_times",
        "shell_cutoffs",
        "basis_labels_N8",
        "basis_labels_N12",
        "basis_labels_N16",
        "B1__xy_isotropy_occupation_difference",
    }
    for spec in CASE_SPECS:
        for suffix in BASE_SERIES_KEYS + CASE_SPECIFIC_SERIES_KEYS.get(spec.case_id, ()):
            keys.add(f"{spec.case_id}__{suffix}")
    for family in ("B2", "B3"):
        for small, large in ((8, 12), (12, 16)):
            prefix = f"B8_{family}_N{small}_to_N{large}"
            for suffix in PAIR_SERIES_KEYS:
                keys.add(f"{prefix}__{suffix}")
    return keys


def load_and_validate_npz(
    path: Path,
    operators_by_cutoff: Mapping[int, IndependentOperators],
) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
    with np.load(path, allow_pickle=False) as archive:
        arrays = {name: np.array(archive[name], copy=True) for name in archive.files}

    expected = expected_npz_keys()
    actual = set(arrays)
    if actual != expected:
        raise RuntimeError(
            "Stage03_time_series.npz schema mismatch; "
            f"missing={sorted(expected-actual)}, extra={sorted(actual-expected)}"
        )

    for name, array in arrays.items():
        if array.dtype.kind in {"f", "c"}:
            if not np.all(np.isfinite(array.real)):
                raise FloatingPointError(f"Non-finite real values in {name}")
            if array.dtype.kind == "c" and not np.all(np.isfinite(array.imag)):
                raise FloatingPointError(f"Non-finite imaginary values in {name}")

    expected_times = np.linspace(0.0, T_FINAL, NUM_OUTPUT_TIMES, dtype=np.float64)
    if not np.array_equal(arrays["global_times"], expected_times):
        raise RuntimeError("global_times does not equal the frozen 101-point grid")
    if not np.array_equal(arrays["shell_cutoffs"], np.asarray(SHELL_CUTOFFS, dtype=np.int64)):
        raise RuntimeError("shell_cutoffs does not equal (8,12,16)")
    for cutoff in SHELL_CUTOFFS:
        expected_labels = np.asarray(operators_by_cutoff[cutoff].labels, dtype=np.int64)
        if not np.array_equal(arrays[f"basis_labels_N{cutoff}"], expected_labels):
            raise RuntimeError(f"N={cutoff} basis labels/order mismatch")

    for spec in CASE_SPECS:
        dimension = operators_by_cutoff[spec.cutoff].dimension
        if arrays[f"{spec.case_id}__t"].shape != (NUM_OUTPUT_TIMES,):
            raise RuntimeError(f"{spec.case_id}: invalid time-series shape")
        if not np.array_equal(arrays[f"{spec.case_id}__t"], expected_times):
            raise RuntimeError(f"{spec.case_id}: time grid mismatch")
        for density_name in ("rho_initial", "rho_final"):
            if arrays[f"{spec.case_id}__{density_name}"].shape != (dimension, dimension):
                raise RuntimeError(f"{spec.case_id}: invalid {density_name} shape")

    return arrays, {
        "npz_exact_key_count": len(actual),
        "npz_exact_schema_match": True,
        "npz_all_numeric_arrays_finite": True,
        "global_time_grid_match": True,
        "basis_labels_and_order_match": True,
    }


def series(arrays: Mapping[str, np.ndarray], case_id: str, suffix: str) -> np.ndarray:
    return arrays[f"{case_id}__{suffix}"]


def dense_expectation(operator: csr_matrix | np.ndarray, density: np.ndarray) -> complex:
    matrix = operator.toarray() if sparse.issparse(operator) else np.asarray(operator)
    return complex(np.trace(matrix @ density))


def reconstruct_base_case_metrics(
    spec: CaseSpec,
    arrays: Mapping[str, np.ndarray],
    operators: IndependentOperators,
) -> Dict[str, Any]:
    traces = series(arrays, spec.case_id, "trace")
    hermiticity = series(arrays, spec.case_id, "hermiticity_fro")
    min_eigen = series(arrays, spec.case_id, "minimum_eigenvalue")
    occupation = series(arrays, spec.case_id, "occupation_total")
    purity = series(arrays, spec.case_id, "purity")
    top = series(arrays, spec.case_id, "top_shell_population")
    omitted = series(arrays, spec.case_id, "upward_event_intensity_omitted")
    overflow = series(arrays, spec.case_id, "overflow_budget")
    intensity_error = series(arrays, spec.case_id, "projected_intensity_formula_error")
    offdiag = series(arrays, spec.case_id, "offdiagonal_fro")
    rho_initial = series(arrays, spec.case_id, "rho_initial")
    rho_final = series(arrays, spec.case_id, "rho_final")

    expected_initial = expected_initial_density(spec, operators)
    initial_density_error = frobenius_norm(rho_initial - expected_initial)
    if initial_density_error > INITIAL_FINAL_DENSITY_ATOL:
        raise RuntimeError(
            f"{spec.case_id}: initial density mismatch {initial_density_error:.3e}"
        )

    final_h = hermitize(rho_final)
    final_trace = np.trace(rho_final)
    final_occupation = float(dense_expectation(operators.n_total, rho_final).real)
    final_purity = float(np.vdot(final_h, final_h).real)
    final_top = float(dense_expectation(operators.top_projector, rho_final).real)
    final_hermiticity = frobenius_norm(rho_final - rho_final.conjugate().T)
    final_min_eigen = float(linalg.eigvalsh(final_h, subset_by_index=(0, 0), check_finite=False)[0])
    final_series_errors = {
        "trace": abs(final_trace - traces[-1]),
        "occupation": abs(final_occupation - occupation[-1]),
        "purity": abs(final_purity - purity[-1]),
        "top_shell": abs(final_top - top[-1]),
        "hermiticity": abs(final_hermiticity - hermiticity[-1]),
        "minimum_eigenvalue": abs(final_min_eigen - min_eigen[-1]),
    }
    if max(float(abs(value)) for value in final_series_errors.values()) > INITIAL_FINAL_DENSITY_ATOL:
        raise RuntimeError(
            f"{spec.case_id}: final-density/time-series inconsistency {final_series_errors}"
        )

    metrics: Dict[str, Any] = {
        "case_id": spec.case_id,
        "description": spec.description,
        "cutoff": spec.cutoff,
        "dimension": operators.dimension,
        "omega": OMEGA,
        "gamma_down": spec.gamma_down,
        "gamma_up": spec.gamma_up,
        "gamma_phi": spec.gamma_phi,
        "gamma_net": spec.gamma_down - spec.gamma_up,
        "initial_state": spec.initial_state,
        "T_final": T_FINAL,
        "number_of_output_times": NUM_OUTPUT_TIMES,
        "maximum_trace_error": float(np.max(np.abs(traces - 1.0))),
        "maximum_trace_imaginary_part": float(np.max(np.abs(traces.imag))),
        "maximum_hermiticity_fro": float(np.max(hermiticity)),
        "minimum_eigenvalue": float(np.min(min_eigen)),
        "maximum_top_shell_population": float(np.max(top)),
        "final_top_shell_population": float(top[-1]),
        "maximum_omitted_upward_intensity": float(np.max(np.abs(omitted))),
        "final_overflow_budget": float(overflow[-1]),
        "maximum_projected_intensity_formula_error": float(np.max(intensity_error)),
        "maximum_offdiagonal_fro": float(np.max(offdiag)),
        "initial_occupation_total": float(occupation[0]),
        "final_occupation_total": float(occupation[-1]),
        "initial_purity": float(purity[0]),
        "final_purity": float(purity[-1]),
        "loader_initial_density_fro_error": initial_density_error,
        "loader_final_density_series_max_error": max(
            float(abs(value)) for value in final_series_errors.values()
        ),
        "loader_final_density_robust_offdiagonal_fro": frobenius_norm(
            rho_final - np.diag(np.diag(rho_final))
        ),
    }

    if f"{spec.case_id}__trace_distance_reference" in arrays:
        metrics["maximum_trace_distance_reference"] = float(
            np.max(series(arrays, spec.case_id, "trace_distance_reference"))
        )
    if f"{spec.case_id}__population_reference_l1" in arrays:
        metrics["maximum_population_reference_l1"] = float(
            np.max(series(arrays, spec.case_id, "population_reference_l1"))
        )
        metrics["maximum_population_reference_entry_error"] = float(
            np.max(series(arrays, spec.case_id, "population_reference_max"))
        )
        metrics["maximum_projected_occupation_reference_error"] = float(
            np.max(np.abs(
                occupation - series(arrays, spec.case_id, "projected_reference_occupation")
            ))
        )
        metrics["maximum_infinite_occupation_error"] = float(
            np.max(series(arrays, spec.case_id, "infinite_occupation_error"))
        )
        metrics["maximum_infinite_occupation_bound_excess"] = float(
            np.max(series(arrays, spec.case_id, "infinite_occupation_bound_excess"))
        )
    return metrics


def augment_case_specific_metrics(
    metrics: MutableMapping[str, Any],
    spec: CaseSpec,
    arrays: Mapping[str, np.ndarray],
    operators: IndependentOperators,
) -> Dict[str, Any]:
    times = series(arrays, spec.case_id, "t")
    diagnostics: Dict[str, Any] = {}

    if spec.family == "B0":
        metrics["ground_stationarity_trace_distance_max"] = metrics[
            "maximum_trace_distance_reference"
        ]
    elif spec.family in {"B1x", "B1y"}:
        reference = np.exp(-GAMMA_ZERO_T * times)
        observed = series(arrays, spec.case_id, "occupation_total")
        error = np.abs(observed - reference)
        metrics["maximum_one_quantum_occupation_error"] = float(np.max(error))
        diagnostics["one_quantum_stored_reference_error"] = max_abs(
            series(arrays, spec.case_id, "one_quantum_occupation_reference") - reference
        )
        diagnostics["one_quantum_stored_error_curve_error"] = max_abs(
            series(arrays, spec.case_id, "one_quantum_occupation_error") - error
        )
    elif spec.family == "B4":
        rho_gibbs = projected_gibbs_density(operators)
        action = direct_generator_action(operators, rho_gibbs, 0.25, 0.05, 0.0)
        residual = frobenius_norm(action)
        upward_gram = (
            operators.a_x @ operators.a_x_dag
            + operators.a_y @ operators.a_y_dag
        ).tocsr()
        down = 0.25 * float(dense_expectation(operators.n_total, rho_gibbs).real)
        up = 0.05 * float(dense_expectation(upward_gram, rho_gibbs).real)
        relative = abs(down - up) / max(abs(down), abs(up), np.finfo(float).tiny)
        metrics["gibbs_generator_residual_fro"] = residual
        metrics["detailed_balance_relative_error"] = relative
        metrics["gibbs_stationarity_trace_distance_max"] = metrics[
            "maximum_trace_distance_reference"
        ]
        metrics["equilibrium_downward_intensity"] = down
        metrics["equilibrium_upward_intensity"] = up
    elif spec.family == "B5":
        amplitude_x = series(arrays, spec.case_id, "amplitude_x")
        amplitude_y = series(arrays, spec.case_id, "amplitude_y")
        decay = 0.5 * (spec.gamma_down - spec.gamma_up) + 1j * OMEGA
        reference_x = np.exp(-decay * times) * amplitude_x[0]
        reference_y = np.exp(-decay * times) * amplitude_y[0]
        signed_x = amplitude_x - reference_x
        signed_y = amplitude_y - reference_y
        error_x = np.abs(signed_x)
        error_y = np.abs(signed_y)

        ax = operators.a_x.toarray()
        ay = operators.a_y.toarray()
        residual_x = direct_adjoint_generator_action(
            operators, ax, spec.gamma_down, spec.gamma_up, spec.gamma_phi
        ) + decay * ax
        residual_y = direct_adjoint_generator_action(
            operators, ay, spec.gamma_down, spec.gamma_up, spec.gamma_phi
        ) + decay * ay
        expectation_x = series(
            arrays, spec.case_id, "coherent_heisenberg_residual_expectation_x"
        )
        expectation_y = series(
            arrays, spec.case_id, "coherent_heisenberg_residual_expectation_y"
        )
        bound_x = cumulative_trapezoid(np.abs(expectation_x), times, initial=0.0)
        bound_y = cumulative_trapezoid(np.abs(expectation_y), times, initial=0.0)
        reconstructed_x = np.exp(-decay * times) * cumulative_trapezoid(
            np.exp(decay * times) * expectation_x, times, initial=0.0
        )
        reconstructed_y = np.exp(-decay * times) * cumulative_trapezoid(
            np.exp(decay * times) * expectation_y, times, initial=0.0
        )
        reconstruction_error_x = np.abs(signed_x - reconstructed_x)
        reconstruction_error_y = np.abs(signed_y - reconstructed_y)
        bound_excess_x = error_x - bound_x
        bound_excess_y = error_y - bound_y
        rho_initial = series(arrays, spec.case_id, "rho_initial")
        rho_final = series(arrays, spec.case_id, "rho_final")
        endpoint_expectation_error = max(
            abs(dense_expectation(residual_x, rho_initial) - expectation_x[0]),
            abs(dense_expectation(residual_y, rho_initial) - expectation_y[0]),
            abs(dense_expectation(residual_x, rho_final) - expectation_x[-1]),
            abs(dense_expectation(residual_y, rho_final) - expectation_y[-1]),
        )
        coherent_tail = projected_coherent_density(operators)[1]
        metrics.update(
            {
                "projected_coherent_initial_tail": coherent_tail,
                "coherent_residual_operator_x_fro": frobenius_norm(residual_x),
                "coherent_residual_operator_y_fro": frobenius_norm(residual_y),
                "maximum_coherent_amplitude_x_error": float(np.max(error_x)),
                "maximum_coherent_amplitude_y_error": float(np.max(error_y)),
                "maximum_coherent_amplitude_error": max(
                    float(np.max(error_x)), float(np.max(error_y))
                ),
                "maximum_coherent_amplitude_bound_excess": max(
                    float(np.max(bound_excess_x)), float(np.max(bound_excess_y))
                ),
                "maximum_coherent_residual_reconstruction_error": max(
                    float(np.max(reconstruction_error_x)),
                    float(np.max(reconstruction_error_y)),
                ),
                "final_coherent_residual_absolute_integral_bound": max(
                    float(bound_x[-1]), float(bound_y[-1])
                ),
            }
        )
        stored_curve_errors = (
            max_abs(series(arrays, spec.case_id, "coherent_amplitude_x_reference") - reference_x),
            max_abs(series(arrays, spec.case_id, "coherent_amplitude_y_reference") - reference_y),
            max_abs(series(arrays, spec.case_id, "coherent_amplitude_x_signed_error") - signed_x),
            max_abs(series(arrays, spec.case_id, "coherent_amplitude_y_signed_error") - signed_y),
            max_abs(series(arrays, spec.case_id, "coherent_amplitude_x_error") - error_x),
            max_abs(series(arrays, spec.case_id, "coherent_amplitude_y_error") - error_y),
            max_abs(series(arrays, spec.case_id, "coherent_residual_absolute_integral_bound_x") - bound_x),
            max_abs(series(arrays, spec.case_id, "coherent_residual_absolute_integral_bound_y") - bound_y),
            max_abs(series(arrays, spec.case_id, "coherent_residual_reconstruction_x") - reconstructed_x),
            max_abs(series(arrays, spec.case_id, "coherent_residual_reconstruction_y") - reconstructed_y),
            max_abs(series(arrays, spec.case_id, "coherent_residual_reconstruction_error_x") - reconstruction_error_x),
            max_abs(series(arrays, spec.case_id, "coherent_residual_reconstruction_error_y") - reconstruction_error_y),
            max_abs(series(arrays, spec.case_id, "coherent_amplitude_bound_excess_x") - bound_excess_x),
            max_abs(series(arrays, spec.case_id, "coherent_amplitude_bound_excess_y") - bound_excess_y),
        )
        diagnostics["coherent_stored_derived_curve_max_error"] = max(stored_curve_errors)
        diagnostics["coherent_residual_expectation_endpoint_error"] = float(
            endpoint_expectation_error
        )
    elif spec.family == "B6":
        population_00 = series(arrays, spec.case_id, "population_00")
        population_10 = series(arrays, spec.case_id, "population_10")
        occupation = series(arrays, spec.case_id, "occupation_total")
        energy = series(arrays, spec.case_id, "energy")
        coherence = series(arrays, spec.case_id, "coherence_00_10")
        population_error = np.maximum(
            np.abs(population_00 - 0.5), np.abs(population_10 - 0.5)
        )
        occupation_error = np.abs(occupation - 0.5)
        energy_error = np.abs(energy - energy[0])
        coherence_reference = coherence[0] * np.exp(
            (1j * OMEGA - 0.5 * GAMMA_PHI) * times
        )
        coherence_error = np.abs(coherence - coherence_reference)
        rotating = coherence * np.exp(-1j * OMEGA * times)
        rotating_reference = coherence[0] * np.exp(-0.5 * GAMMA_PHI * times)
        metrics.update(
            {
                "maximum_dephasing_population_error": float(np.max(population_error)),
                "maximum_dephasing_occupation_error": float(np.max(occupation_error)),
                "maximum_dephasing_energy_error": float(np.max(energy_error)),
                "maximum_dephasing_coherence_error": float(np.max(coherence_error)),
            }
        )
        diagnostics["dephasing_stored_derived_curve_max_error"] = max(
            max_abs(series(arrays, spec.case_id, "dephasing_population_error") - population_error),
            max_abs(series(arrays, spec.case_id, "dephasing_occupation_error") - occupation_error),
            max_abs(series(arrays, spec.case_id, "dephasing_energy_error") - energy_error),
            max_abs(series(arrays, spec.case_id, "dephasing_coherence_reference") - coherence_reference),
            max_abs(series(arrays, spec.case_id, "dephasing_coherence_error") - coherence_error),
            max_abs(series(arrays, spec.case_id, "dephasing_rotating_coherence") - rotating),
            max_abs(series(arrays, spec.case_id, "dephasing_rotating_reference") - rotating_reference),
        )
    return diagnostics


# =============================================================================
# Independent B2/B3 population curves, exact overflow, and B8 convergence
# =============================================================================
def independent_thermal_references(
    arrays: Mapping[str, np.ndarray],
    operators_by_cutoff: Mapping[int, IndependentOperators],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, np.ndarray]]:
    records: Dict[str, Dict[str, Any]] = {}
    population_curves: Dict[str, np.ndarray] = {}

    for case_id in THERMAL_CASE_IDS:
        spec = CASE_BY_ID[case_id]
        operators = operators_by_cutoff[spec.cutoff]
        generator = independent_population_generator(
            operators, spec.gamma_down, spec.gamma_up
        )
        initial = population_initial_vector(spec, operators)
        reference = propagate_population_reference(generator, initial, NUM_OUTPUT_TIMES)
        highres = propagate_population_reference(generator, initial, HIGHRES_OUTPUT_TIMES)
        population_curves[case_id] = reference

        occupation = reference @ operators.shell_values.astype(np.float64)
        purity = np.sum(reference * reference, axis=1, dtype=np.float64)
        top_mask = operators.shell_values == operators.cutoff
        top = np.sum(reference[:, top_mask], axis=1, dtype=np.float64)
        highres_top = np.sum(highres[:, top_mask], axis=1, dtype=np.float64)
        omitted = GAMMA_UP_THERMAL * (operators.cutoff + 2.0) * top
        overflow_trap = cumulative_trapezoid(
            omitted,
            np.linspace(0.0, T_FINAL, NUM_OUTPUT_TIMES, dtype=np.float64),
            initial=0.0,
        )
        exact_overflow = exact_augmented_overflow(
            operators, generator, initial
        )
        selected_errors: List[float] = []
        for label in ((0, 0), (1, 0), (0, 1), (2, 0), (1, 1)):
            index = operators.index[label]
            selected_errors.append(max_abs(
                series(arrays, case_id, f"population_{label[0]}{label[1]}")
                - reference[:, index]
            ))
        final_density = series(arrays, case_id, "rho_final")
        final_population_error = max_abs(np.diag(final_density).real - reference[-1])
        final_offdiagonal = frobenius_norm(
            final_density - np.diag(np.diag(final_density))
        )
        stored_overflow = series(arrays, case_id, "overflow_budget")
        stored_reference_occupation = series(
            arrays, case_id, "projected_reference_occupation"
        )
        upward_projected = spec.gamma_up * (
            occupation + 2.0 - (operators.cutoff + 2.0) * top
        )
        downward = spec.gamma_down * occupation

        curve_error = max(
            max_abs(series(arrays, case_id, "occupation_total") - occupation),
            max_abs(series(arrays, case_id, "purity") - purity),
            max_abs(series(arrays, case_id, "top_shell_population") - top),
            max_abs(series(arrays, case_id, "upward_event_intensity_omitted") - omitted),
            max_abs(series(arrays, case_id, "overflow_budget") - overflow_trap),
            max_abs(stored_reference_occupation - occupation),
            max_abs(series(arrays, case_id, "upward_event_intensity_projected") - upward_projected),
            max_abs(series(arrays, case_id, "downward_event_intensity") - downward),
            *selected_errors,
        )
        records[case_id] = {
            "case_id": case_id,
            "family": spec.family,
            "cutoff": spec.cutoff,
            "dimension": operators.dimension,
            "independent_population_curve_max_error": curve_error,
            "independent_final_population_max_error": final_population_error,
            "independent_final_offdiagonal_fro": final_offdiagonal,
            "solver_trapezoid_overflow": float(stored_overflow[-1]),
            "independent_trapezoid_overflow": float(overflow_trap[-1]),
            "exact_augmented_overflow": exact_overflow,
            "exact_minus_solver_trapezoid_overflow": exact_overflow - float(stored_overflow[-1]),
            "highres_maximum_top_shell_population": float(np.max(highres_top)),
            "solver_101point_maximum_top_shell_population": float(
                np.max(series(arrays, case_id, "top_shell_population"))
            ),
            "final_occupation_total_independent": float(occupation[-1]),
            "final_purity_independent": float(purity[-1]),
        }

    return records, population_curves


def independent_pairwise_cutoff_metrics(
    population_curves: Mapping[str, np.ndarray],
    operators_by_cutoff: Mapping[int, IndependentOperators],
) -> Dict[str, Dict[str, Any]]:
    records: Dict[str, Dict[str, Any]] = {}
    for family in ("B2", "B3"):
        for small, large in ((8, 12), (12, 16)):
            small_ops = operators_by_cutoff[small]
            large_ops = operators_by_cutoff[large]
            p_small = population_curves[f"{family}_N{small}"]
            p_large = population_curves[f"{family}_N{large}"]
            embedded = np.zeros_like(p_large)
            embedded[:, : small_ops.dimension] = p_small
            occ_small = p_small @ small_ops.shell_values.astype(np.float64)
            occ_large = p_large @ large_ops.shell_values.astype(np.float64)
            purity_small = np.sum(p_small * p_small, axis=1, dtype=np.float64)
            purity_large = np.sum(p_large * p_large, axis=1, dtype=np.float64)
            occ_diff = np.abs(occ_small - occ_large)
            purity_diff = np.abs(purity_small - purity_large)
            distance = 0.5 * np.sum(np.abs(embedded - p_large), axis=1, dtype=np.float64)
            bound = 2.0 * large * distance
            excess = occ_diff - bound
            prefix = f"B8_{family}_N{small}_to_N{large}"
            records[prefix] = {
                "row_type": "pairwise_cutoff_comparison",
                "family": family,
                "small_cutoff": small,
                "large_cutoff": large,
                "small_dimension": small_ops.dimension,
                "large_dimension": large_ops.dimension,
                "maximum_occupation_difference": float(np.max(occ_diff)),
                "final_occupation_difference": float(occ_diff[-1]),
                "maximum_purity_difference": float(np.max(purity_diff)),
                "final_purity_difference": float(purity_diff[-1]),
                "maximum_trace_distance": float(np.max(distance)),
                "final_trace_distance": float(distance[-1]),
                "trace_distance_evaluation": "independent exact diagonal L1 formula",
                "maximum_occupation_trace_distance_bound": float(np.max(bound)),
                "maximum_occupation_trace_distance_bound_excess": float(np.max(excess)),
            }
    return records


def reconstruct_solver_pair_rows_from_npz(
    arrays: Mapping[str, np.ndarray],
    case_metrics: Mapping[str, Mapping[str, Any]],
    operators_by_cutoff: Mapping[int, IndependentOperators],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for family in ("B2", "B3"):
        for small, large in ((8, 12), (12, 16)):
            prefix = f"B8_{family}_N{small}_to_N{large}"
            occ = arrays[f"{prefix}__occupation_difference"]
            purity = arrays[f"{prefix}__purity_difference"]
            distance = arrays[f"{prefix}__trace_distance"]
            bound = arrays[f"{prefix}__occupation_trace_distance_bound"]
            excess = arrays[f"{prefix}__occupation_trace_distance_bound_excess"]
            diagonal_fast_path = (
                float(case_metrics[f"{family}_N{small}"]["maximum_offdiagonal_fro"]) <= 1.0e-13
                and float(case_metrics[f"{family}_N{large}"]["maximum_offdiagonal_fro"]) <= 1.0e-13
            )
            rows.append({
                "row_type": "pairwise_cutoff_comparison",
                "family": family,
                "small_cutoff": small,
                "large_cutoff": large,
                "small_dimension": operators_by_cutoff[small].dimension,
                "large_dimension": operators_by_cutoff[large].dimension,
                "maximum_occupation_difference": float(np.max(occ)),
                "final_occupation_difference": float(occ[-1]),
                "maximum_purity_difference": float(np.max(purity)),
                "final_purity_difference": float(purity[-1]),
                "maximum_trace_distance": float(np.max(distance)),
                "final_trace_distance": float(distance[-1]),
                "trace_distance_evaluation": (
                    "exact diagonal L1 formula" if diagonal_fast_path
                    else "full Hermitian eigenspectrum"
                ),
                "maximum_occupation_trace_distance_bound": float(np.max(bound)),
                "maximum_occupation_trace_distance_bound_excess": float(np.max(excess)),
            })
    return rows


# =============================================================================
# CSV comparison: every populated field is checked
# =============================================================================
def parse_numeric(text: str) -> float | None:
    if text == "":
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def compare_csv_rows(
    solver_fieldnames: Sequence[str],
    solver_rows: Sequence[Mapping[str, str]],
    reconstructed_rows: Sequence[Mapping[str, Any]],
    row_key: callable,
    label: str,
) -> Dict[str, Any]:
    reconstructed_index = {row_key(row): row for row in reconstructed_rows}
    maximum_numeric_difference = 0.0
    mismatches: List[Dict[str, Any]] = []
    compared_fields = 0

    for solver_row in solver_rows:
        key = row_key(solver_row)
        if key not in reconstructed_index:
            mismatches.append({"row": key, "field": "<row>", "reason": "missing"})
            continue
        reconstructed = reconstructed_index[key]
        for field in solver_fieldnames:
            solver_text = str(solver_row.get(field, ""))
            if solver_text == "":
                continue
            if field not in reconstructed:
                mismatches.append({"row": key, "field": field, "reason": "not reconstructed"})
                continue
            compared_fields += 1
            solver_numeric = parse_numeric(solver_text)
            reconstructed_value = reconstructed[field]
            if solver_numeric is not None and isinstance(
                reconstructed_value, (int, float, np.integer, np.floating)
            ):
                reconstructed_numeric = float(reconstructed_value)
                difference = abs(solver_numeric - reconstructed_numeric)
                maximum_numeric_difference = max(maximum_numeric_difference, difference)
                if not values_close(
                    solver_numeric, reconstructed_numeric, CSV_NUMERIC_COMPARISON_ATOL
                ):
                    mismatches.append({
                        "row": key,
                        "field": field,
                        "solver": solver_numeric,
                        "loader": reconstructed_numeric,
                        "absolute_difference": difference,
                    })
            else:
                if str(reconstructed_value) != solver_text:
                    mismatches.append({
                        "row": key,
                        "field": field,
                        "solver": solver_text,
                        "loader": str(reconstructed_value),
                    })

    return {
        "label": label,
        "solver_row_count": len(solver_rows),
        "loader_row_count": len(reconstructed_rows),
        "compared_nonempty_fields": compared_fields,
        "maximum_numeric_difference": maximum_numeric_difference,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "pass": len(mismatches) == 0,
    }


# =============================================================================
# Acceptance reconstruction and solver/loader comparison
# =============================================================================
def make_check(value: float, criterion: str, passed: bool) -> Dict[str, Any]:
    return {"value": finite_float(value, "acceptance value"),
            "criterion": criterion, "pass": bool(passed)}


def build_acceptance(
    operator_audit: Mapping[str, Any],
    case_metrics: Mapping[str, Mapping[str, Any]],
    b7_metrics: Mapping[str, Any],
    cutoff_case_rows: Sequence[Mapping[str, Any]],
    cutoff_pair_rows: Sequence[Mapping[str, Any]],
    refined_thermal: Mapping[str, Mapping[str, Any]] | None = None,
) -> Dict[str, Any]:
    t = ACCEPTANCE_THRESHOLDS
    checks: Dict[str, Dict[str, Any]] = {}
    maxima = operator_audit["maximum_defects"]
    operator_identity = max(
        float(maxima["number_diagonal_error"]),
        float(maxima["hamiltonian_diagonal_error"]),
        float(maxima["bohr_relation_error"]),
        float(maxima["top_shell_upward_identity_error"]),
    )
    checks["operator_identities"] = make_check(
        operator_identity, f"<= {t['operator_identity_max']:.3e}",
        operator_identity <= t["operator_identity_max"]
    )
    trace_row = float(maxima["liouvillian_trace_row_error"])
    checks["liouvillian_trace_preserving_row"] = make_check(
        trace_row, f"<= {t['liouvillian_trace_row_max']:.3e}",
        trace_row <= t["liouvillian_trace_row_max"]
    )
    vectorization = float(maxima["vectorization_action_relative_error"])
    checks["column_major_vectorization"] = make_check(
        vectorization, f"<= {t['vectorization_action_relative_max']:.3e}",
        vectorization <= t["vectorization_action_relative_max"]
    )
    herm_action = float(maxima["hermiticity_action_relative_error"])
    checks["generator_hermiticity_preservation"] = make_check(
        herm_action, f"<= {t['hermiticity_action_relative_max']:.3e}",
        herm_action <= t["hermiticity_action_relative_max"]
    )

    all_cases = list(case_metrics.values())
    max_trace = max(float(row["maximum_trace_error"]) for row in all_cases)
    max_herm = max(float(row["maximum_hermiticity_fro"]) for row in all_cases)
    min_eig = min(float(row["minimum_eigenvalue"]) for row in all_cases)
    max_intensity = max(
        float(row["maximum_projected_intensity_formula_error"]) for row in all_cases
    )
    checks["trace_preservation"] = make_check(
        max_trace, f"<= {t['trace_error_max']:.3e}", max_trace <= t["trace_error_max"]
    )
    checks["density_hermiticity"] = make_check(
        max_herm, f"<= {t['hermiticity_fro_max']:.3e}", max_herm <= t["hermiticity_fro_max"]
    )
    checks["density_positivity"] = make_check(
        min_eig, f">= {t['minimum_eigenvalue_min']:.3e}", min_eig >= t["minimum_eigenvalue_min"]
    )
    checks["projected_event_intensity_formula"] = make_check(
        max_intensity, f"<= {t['projected_intensity_formula_max']:.3e}",
        max_intensity <= t["projected_intensity_formula_max"]
    )

    b0_value = float(case_metrics["B0_N12"]["ground_stationarity_trace_distance_max"])
    checks["B0_ground_stationarity"] = make_check(
        b0_value, f"<= {t['ground_stationarity_trace_distance_max']:.3e}",
        b0_value <= t["ground_stationarity_trace_distance_max"]
    )
    b1_error = max(
        float(case_metrics["B1x_N12"]["maximum_one_quantum_occupation_error"]),
        float(case_metrics["B1y_N12"]["maximum_one_quantum_occupation_error"]),
    )
    b1_isotropy = max_abs(
        np.asarray(case_metrics["B1x_N12"]["loader_occupation_series"])
        - np.asarray(case_metrics["B1y_N12"]["loader_occupation_series"])
    )
    checks["B1_one_quantum_decay"] = make_check(
        b1_error, f"<= {t['one_quantum_occupation_error_max']:.3e}",
        b1_error <= t["one_quantum_occupation_error_max"]
    )
    checks["B1_xy_isotropy"] = make_check(
        b1_isotropy, f"<= {t['one_quantum_isotropy_max']:.3e}",
        b1_isotropy <= t["one_quantum_isotropy_max"]
    )

    pop_l1 = max(float(case_metrics[key]["maximum_population_reference_l1"])
                 for key in THERMAL_CASE_IDS)
    pop_occ = max(float(case_metrics[key]["maximum_projected_occupation_reference_error"])
                  for key in THERMAL_CASE_IDS)
    bound_excess = max(float(case_metrics[key]["maximum_infinite_occupation_bound_excess"])
                       for key in THERMAL_CASE_IDS)
    checks["B2_B3_projected_population_reference"] = make_check(
        pop_l1, f"<= {t['projected_population_l1_max']:.3e}",
        pop_l1 <= t["projected_population_l1_max"]
    )
    checks["B2_B3_projected_occupation_reference"] = make_check(
        pop_occ, f"<= {t['projected_occupation_error_max']:.3e}",
        pop_occ <= t["projected_occupation_error_max"]
    )
    checks["B2_B3_infinite_law_within_declared_overflow_bound"] = make_check(
        bound_excess, "<= 0", bound_excess <= 0.0
    )

    b4 = case_metrics["B4_N12"]
    for name, key, threshold_key in (
        ("B4_projected_gibbs_generator_stationarity", "gibbs_generator_residual_fro", "gibbs_generator_residual_fro_max"),
        ("B4_projected_gibbs_propagated_stationarity", "gibbs_stationarity_trace_distance_max", "gibbs_trace_distance_max"),
        ("B4_projected_detailed_balance", "detailed_balance_relative_error", "detailed_balance_relative_max"),
    ):
        value = float(b4[key])
        checks[name] = make_check(value, f"<= {t[threshold_key]:.3e}", value <= t[threshold_key])

    b5 = case_metrics["B5_N12"]
    b5_entries = (
        ("B5_coherent_amplitude_absolute_error", "maximum_coherent_amplitude_error", "coherent_amplitude_absolute_error_max"),
        ("B5_coherent_amplitude_within_projected_residual_bound", "maximum_coherent_amplitude_bound_excess", "coherent_bound_excess_max"),
        ("B5_coherent_projected_residual_reconstruction", "maximum_coherent_residual_reconstruction_error", "coherent_residual_reconstruction_error_max"),
    )
    for name, key, threshold_key in b5_entries:
        value = float(b5[key])
        checks[name] = make_check(value, f"<= {t[threshold_key]:.3e}", value <= t[threshold_key])

    b6 = case_metrics["B6_N12"]
    deph_pop = max(float(b6["maximum_dephasing_population_error"]),
                    float(b6["maximum_dephasing_occupation_error"]))
    checks["B6_dephasing_population_invariants"] = make_check(
        deph_pop, f"<= {t['dephasing_population_error_max']:.3e}",
        deph_pop <= t["dephasing_population_error_max"]
    )
    deph_energy = float(b6["maximum_dephasing_energy_error"])
    checks["B6_dephasing_energy_invariant"] = make_check(
        deph_energy, f"<= {t['dephasing_energy_error_max']:.3e}",
        deph_energy <= t["dephasing_energy_error_max"]
    )
    deph_coh = float(b6["maximum_dephasing_coherence_error"])
    checks["B6_dephasing_coherence_law"] = make_check(
        deph_coh, f"<= {t['dephasing_coherence_error_max']:.3e}",
        deph_coh <= t["dephasing_coherence_error_max"]
    )

    b7_value = max(
        float(b7_metrics["maximum_annihilation_relative_action_defect"]),
        float(b7_metrics["maximum_creation_relative_action_defect"]),
    )
    checks["B7_isotropic_basis_invariance"] = make_check(
        b7_value, f"<= {t['isotropic_action_relative_max']:.3e}",
        b7_value <= t["isotropic_action_relative_max"]
    )

    n12_n16 = [row for row in cutoff_pair_rows
               if int(row["small_cutoff"]) == 12 and int(row["large_cutoff"]) == 16]
    cutoff_occ = max(float(row["maximum_occupation_difference"]) for row in n12_n16)
    cutoff_purity = max(float(row["maximum_purity_difference"]) for row in n12_n16)
    cutoff_distance = max(float(row["maximum_trace_distance"]) for row in n12_n16)
    checks["B8_cutoff_occupation_N12_to_N16"] = make_check(
        cutoff_occ, f"<= {t['cutoff_n12_n16_occupation_max']:.3e}",
        cutoff_occ <= t["cutoff_n12_n16_occupation_max"]
    )
    checks["B8_cutoff_purity_N12_to_N16"] = make_check(
        cutoff_purity, f"<= {t['cutoff_n12_n16_purity_max']:.3e}",
        cutoff_purity <= t["cutoff_n12_n16_purity_max"]
    )
    checks["B8_cutoff_trace_distance_N12_to_N16"] = make_check(
        cutoff_distance, f"<= {t['cutoff_n12_n16_trace_distance_max']:.3e}",
        cutoff_distance <= t["cutoff_n12_n16_trace_distance_max"]
    )
    occ_bound_excess = max(
        float(row["maximum_occupation_trace_distance_bound_excess"]) for row in n12_n16
    )
    checks["B8_occupation_trace_distance_consistency"] = make_check(
        occ_bound_excess, "<= 5.000e-12", occ_bound_excess <= 5.0e-12
    )

    if refined_thermal is None:
        production_rows = [row for row in cutoff_case_rows if int(row["cutoff"]) == 12]
        production_top = max(float(row["maximum_top_shell_population"]) for row in production_rows)
        production_overflow = max(float(row["final_overflow_budget"]) for row in production_rows)
        top_values = {
            family: {int(row["cutoff"]): float(row["maximum_top_shell_population"])
                     for row in cutoff_case_rows if row["family"] == family}
            for family in ("B2", "B3")
        }
        overflow_values = {
            family: {int(row["cutoff"]): float(row["final_overflow_budget"])
                     for row in cutoff_case_rows if row["family"] == family}
            for family in ("B2", "B3")
        }
    else:
        production_top = max(
            float(refined_thermal["B2_N12"]["highres_maximum_top_shell_population"]),
            float(refined_thermal["B3_N12"]["highres_maximum_top_shell_population"]),
        )
        production_overflow = max(
            float(refined_thermal["B2_N12"]["exact_augmented_overflow"]),
            float(refined_thermal["B3_N12"]["exact_augmented_overflow"]),
        )
        top_values = {
            family: {
                cutoff: float(refined_thermal[f"{family}_N{cutoff}"]["highres_maximum_top_shell_population"])
                for cutoff in SHELL_CUTOFFS
            }
            for family in ("B2", "B3")
        }
        overflow_values = {
            family: {
                cutoff: float(refined_thermal[f"{family}_N{cutoff}"]["exact_augmented_overflow"])
                for cutoff in SHELL_CUTOFFS
            }
            for family in ("B2", "B3")
        }

    checks["B8_production_top_shell"] = make_check(
        production_top, f"<= {t['production_top_shell_max']:.3e}",
        production_top <= t["production_top_shell_max"]
    )
    checks["B8_production_overflow"] = make_check(
        production_overflow, f"<= {t['production_overflow_final_max']:.3e}",
        production_overflow <= t["production_overflow_final_max"]
    )
    top_violation = 0.0
    overflow_violation = 0.0
    for family in ("B2", "B3"):
        top_violation = max(
            top_violation,
            top_values[family][12] - top_values[family][8],
            top_values[family][16] - top_values[family][12],
        )
        overflow_violation = max(
            overflow_violation,
            overflow_values[family][12] - overflow_values[family][8],
            overflow_values[family][16] - overflow_values[family][12],
        )
    checks["B8_top_shell_monotonic_improvement"] = make_check(
        top_violation, f"<= {t['cutoff_monotonicity_tolerance']:.3e}",
        top_violation <= t["cutoff_monotonicity_tolerance"]
    )
    checks["B8_overflow_monotonic_improvement"] = make_check(
        overflow_violation, f"<= {t['cutoff_monotonicity_tolerance']:.3e}",
        overflow_violation <= t["cutoff_monotonicity_tolerance"]
    )

    return {
        "accepted": all(bool(item["pass"]) for item in checks.values()),
        "checks": checks,
        "thresholds": ACCEPTANCE_THRESHOLDS,
        "check_count": len(checks),
        "pass_count": sum(bool(item["pass"]) for item in checks.values()),
    }


def compare_acceptance_records(
    solver_acceptance: Mapping[str, Any],
    loader_equivalent: Mapping[str, Any],
    loader_refined: Mapping[str, Any],
) -> Dict[str, Any]:
    solver_checks = solver_acceptance.get("checks", {})
    equivalent_checks = loader_equivalent.get("checks", {})
    refined_checks = loader_refined.get("checks", {})
    if set(solver_checks) != set(equivalent_checks) or set(solver_checks) != set(refined_checks):
        raise RuntimeError("Acceptance check-name sets do not agree")
    rows: Dict[str, Any] = {}
    all_equivalent = True
    all_pass_agreement = True
    all_criteria_agreement = True
    for name in sorted(solver_checks):
        solver = solver_checks[name]
        equivalent = equivalent_checks[name]
        refined = refined_checks[name]
        value_difference = abs(float(solver["value"]) - float(equivalent["value"]))
        value_agreement = values_close(
            float(solver["value"]), float(equivalent["value"]),
            ACCEPTANCE_VALUE_COMPARISON_ATOL
        )
        pass_agreement = bool(solver["pass"]) == bool(equivalent["pass"]) == bool(refined["pass"])
        criterion_agreement = str(solver["criterion"]) == str(equivalent["criterion"]) == str(refined["criterion"])
        rows[name] = {
            "solver_value": float(solver["value"]),
            "loader_equivalent_value": float(equivalent["value"]),
            "loader_refined_value": float(refined["value"]),
            "solver_loader_equivalent_abs_difference": value_difference,
            "value_agreement": value_agreement,
            "pass_agreement": pass_agreement,
            "criterion_agreement": criterion_agreement,
            "criterion": str(solver["criterion"]),
        }
        all_equivalent = all_equivalent and value_agreement
        all_pass_agreement = all_pass_agreement and pass_agreement
        all_criteria_agreement = all_criteria_agreement and criterion_agreement
    return {
        "check_count": len(rows),
        "all_equivalent_values_agree": all_equivalent,
        "all_pass_fail_results_agree": all_pass_agreement,
        "all_criteria_agree": all_criteria_agreement,
        "checks": rows,
        "pass": all_equivalent and all_pass_agreement and all_criteria_agreement,
    }


# =============================================================================
# Loader output rows and report
# =============================================================================
def loader_case_rows(
    case_metrics: Mapping[str, Mapping[str, Any]],
    thermal_records: Mapping[str, Mapping[str, Any]],
    b7_replay: Mapping[str, Any],
    b7_fresh: Mapping[str, Any],
    case_diagnostics: Mapping[str, Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for spec in CASE_SPECS:
        row = {key: value for key, value in case_metrics[spec.case_id].items()
               if key != "loader_occupation_series"}
        row.update(case_diagnostics.get(spec.case_id, {}))
        if spec.case_id in thermal_records:
            row.update(thermal_records[spec.case_id])
        rows.append(row)
    rows.append({
        "case_id": "B7",
        "description": "isotropic bath-basis invariance",
        "cutoff": 12,
        "dimension": 91,
        "omega": OMEGA,
        "gamma_down": "unit operator identity",
        "gamma_up": "unit operator identity",
        "gamma_phi": 0.0,
        "initial_state": "random Hermitian tests",
        "T_final": 0.0,
        "number_of_output_times": 0,
        "unitary_count": b7_replay["unitary_count"],
        "matrix_count_per_unitary": b7_replay["matrix_count_per_unitary"],
        "maximum_annihilation_relative_action_defect": b7_replay[
            "maximum_annihilation_relative_action_defect"
        ],
        "maximum_creation_relative_action_defect": b7_replay[
            "maximum_creation_relative_action_defect"
        ],
        "fresh_seed": LOADER_INDEPENDENT_RNG_SEED,
        "fresh_maximum_annihilation_relative_action_defect": b7_fresh[
            "maximum_annihilation_relative_action_defect"
        ],
        "fresh_maximum_creation_relative_action_defect": b7_fresh[
            "maximum_creation_relative_action_defect"
        ],
    })
    return rows


def loader_cutoff_rows(
    case_metrics: Mapping[str, Mapping[str, Any]],
    thermal_records: Mapping[str, Mapping[str, Any]],
    solver_pair_rows: Sequence[Mapping[str, Any]],
    independent_pair_rows: Mapping[str, Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for family in ("B2", "B3"):
        for cutoff in SHELL_CUTOFFS:
            case_id = f"{family}_N{cutoff}"
            metrics = case_metrics[case_id]
            refined = thermal_records[case_id]
            rows.append({
                "row_type": "cutoff_case",
                "family": family,
                "case_id": case_id,
                "cutoff": cutoff,
                "dimension": metrics["dimension"],
                "maximum_top_shell_population": metrics["maximum_top_shell_population"],
                "highres_maximum_top_shell_population": refined[
                    "highres_maximum_top_shell_population"
                ],
                "final_top_shell_population": metrics["final_top_shell_population"],
                "maximum_omitted_upward_intensity": metrics[
                    "maximum_omitted_upward_intensity"
                ],
                "final_overflow_budget": metrics["final_overflow_budget"],
                "exact_augmented_overflow": refined["exact_augmented_overflow"],
                "exact_minus_solver_trapezoid_overflow": refined[
                    "exact_minus_solver_trapezoid_overflow"
                ],
                "maximum_population_reference_l1": metrics[
                    "maximum_population_reference_l1"
                ],
                "maximum_projected_occupation_reference_error": metrics[
                    "maximum_projected_occupation_reference_error"
                ],
                "maximum_infinite_occupation_error": metrics[
                    "maximum_infinite_occupation_error"
                ],
                "maximum_infinite_occupation_bound_excess": metrics[
                    "maximum_infinite_occupation_bound_excess"
                ],
                "final_occupation_total": metrics["final_occupation_total"],
                "final_purity": metrics["final_purity"],
                "independent_population_curve_max_error": refined[
                    "independent_population_curve_max_error"
                ],
            })
    for row in solver_pair_rows:
        key = f"B8_{row['family']}_N{row['small_cutoff']}_to_N{row['large_cutoff']}"
        merged = dict(row)
        independent = independent_pair_rows[key]
        for field in (
            "maximum_occupation_difference",
            "final_occupation_difference",
            "maximum_purity_difference",
            "final_purity_difference",
            "maximum_trace_distance",
            "final_trace_distance",
            "maximum_occupation_trace_distance_bound",
            "maximum_occupation_trace_distance_bound_excess",
        ):
            merged[f"independent_{field}"] = independent[field]
            merged[f"independent_minus_solver_{field}"] = (
                float(independent[field]) - float(row[field])
            )
        merged["independent_trace_distance_evaluation"] = independent[
            "trace_distance_evaluation"
        ]
        rows.append(merged)
    return rows


def build_report(
    accepted: bool,
    hash_audit: Mapping[str, Any],
    infrastructure: Mapping[str, Any],
    refined_acceptance: Mapping[str, Any],
    acceptance_comparison: Mapping[str, Any],
    thermal_records: Mapping[str, Mapping[str, Any]],
    loader_sha256: str,
) -> str:
    lines: List[str] = []
    lines.append("# Stage-03 Independent Bath-Only Loader Report")
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append(
        "**PASS**" if accepted else "**FAIL**"
    )
    lines.append("")
    lines.append(
        f"Loader source SHA-256: `{loader_sha256}`"
    )
    lines.append("")
    lines.append(
        f"Stable Stage-03 solver files verified: "
        f"{hash_audit['stable_file_count']}/{hash_audit['stable_file_count']}."
    )
    lines.append("")
    lines.append(
        f"Independent refined acceptance: {refined_acceptance['pass_count']}/"
        f"{refined_acceptance['check_count']} gates."
    )
    lines.append("")
    lines.append(
        "All solver/loader criteria and PASS/FAIL decisions agree: "
        f"`{acceptance_comparison['pass']}`."
    )
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append(
        "This report certifies only the detector-free finite projected transverse "
        "bath. No scalar/spinor ABC, longitudinal propagation, roof-click law, or "
        "environmental detector susceptibility is calculated."
    )
    lines.append("")
    lines.append("## Infrastructure and independent reconstruction")
    lines.append("")
    lines.append("| Check | Result |")
    lines.append("|---|---:|")
    for key in (
        "hash_validation_pass",
        "configuration_validation_pass",
        "source_guard_pass",
        "npz_schema_pass",
        "case_csv_comparison_pass",
        "cutoff_csv_comparison_pass",
        "operator_json_comparison_pass",
        "independent_population_curves_pass",
        "initial_final_density_pass",
        "fresh_random_audit_pass",
        "exact_overflow_refinement_pass",
    ):
        lines.append(f"| `{key}` | `{infrastructure[key]}` |")
    lines.append("")
    lines.append("## Exact finite-shell refinement")
    lines.append("")
    lines.append("| Case | 101-point overflow | Exact augmented overflow | High-resolution max top shell |")
    lines.append("|---|---:|---:|---:|")
    for case_id in THERMAL_CASE_IDS:
        record = thermal_records[case_id]
        lines.append(
            f"| {case_id} | {record['solver_trapezoid_overflow']:.12e} | "
            f"{record['exact_augmented_overflow']:.12e} | "
            f"{record['highres_maximum_top_shell_population']:.12e} |"
        )
    lines.append("")
    lines.append("The tightest production-shell result is")
    lines.append("")
    lines.append(
        f"\\[\\epsilon_{{\\mathrm{{overflow}}}}^{{B3,N=12}}(20)="
        f"{thermal_records['B3_N12']['exact_augmented_overflow']:.15e}<10^{{-6}}.\\]"
    )
    lines.append("")
    lines.append("## Independent 32-gate table")
    lines.append("")
    lines.append("| Gate | Loader value | Criterion | Result |")
    lines.append("|---|---:|---:|---|")
    for name, item in refined_acceptance["checks"].items():
        lines.append(
            f"| `{name}` | {item['value']:.12e} | `{item['criterion']}` | "
            f"{'PASS' if item['pass'] else 'FAIL'} |"
        )
    lines.append("")
    lines.append("## Workflow status")
    lines.append("")
    if accepted:
        lines.append(
            "The Stage-03 bath branch is solver-and-loader certified for the "
            "declared B0--B8 scope. Scientific Stage 04 remains blocked until "
            "Stage 01C also passes. The N=12 result is not inherited automatically "
            "by detector-present dynamics."
        )
    else:
        lines.append(
            "The bath branch is not closed. Scientific Stage 04 must not begin."
        )
    return "\n".join(lines) + "\n"


# =============================================================================
# Main
# =============================================================================
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Independent Task-04 audit of the Stage-03 bath-only solver products. "
            f"The directory name is fixed to {OUTPUT_DIRECTORY_NAME}."
        )
    )
    parser.add_argument(
        "--out-root",
        type=Path,
        default=Path(os.getenv("OUTDIR", ".")),
        help=(
            "Root containing the fixed 4060.Bath_only_tests directory. "
            "No timestamped or parameter-generated directory is created."
        ),
    )
    args, unknown = parser.parse_known_args()
    # IPython/Jupyter kernels inject ``-f <connection-file>``.  Ignore only
    # that exact kernel argument; every other unknown option remains an error
    # so misspelled production flags cannot pass silently.
    remaining: List[str] = []
    index = 0
    while index < len(unknown):
        token = unknown[index]
        if token == "-f" and index + 1 < len(unknown):
            index += 2
            continue
        if token.startswith("--f=") or token.startswith("-f="):
            index += 1
            continue
        remaining.append(token)
        index += 1
    if remaining:
        parser.error("unrecognized arguments: " + " ".join(remaining))
    return args


def main() -> int:
    args = parse_args()
    out_dir = args.out_root.expanduser().resolve() / OUTPUT_DIRECTORY_NAME
    if not out_dir.is_dir():
        raise FileNotFoundError(f"Stage-03 output directory not found: {out_dir}")

    remove_previous_loader_products(out_dir)
    original_stdout = sys.stdout
    stdout_handle = (out_dir / "loader_stdout.txt").open("w", encoding="utf-8")
    sys.stdout = Tee(original_stdout, stdout_handle)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(out_dir / "loader_log.txt", mode="w"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )

    start_time = time.perf_counter()
    script_path = Path(__file__).resolve()
    script_copy = out_dir / LOADER_SOURCE_NAME
    if script_path != script_copy:
        shutil.copy2(script_path, script_copy)
    loader_sha256 = sha256_file(script_copy)
    run_status_path = out_dir / "Stage03_loader_run_status.json"
    run_status: Dict[str, Any] = {
        "status": "initializing",
        "started_utc": utc_now_iso(),
        "stage": LOADER_STAGE_NAME,
        "loader_version": LOADER_VERSION,
        "loader_sha256": loader_sha256,
        "output_directory": str(out_dir),
        "fixed_directory_contract": OUTPUT_DIRECTORY_NAME,
    }
    atomic_write_json(run_status_path, run_status)

    try:
        print(f"[info] Task-04 loader: {LOADER_VERSION}")
        print(f"[info] loader SHA-256: {loader_sha256}")
        print(f"[info] fixed directory: {out_dir}")
        print("[info] solver source is not imported")

        hash_audit = validate_solver_hashes(out_dir)
        source_guard = validate_solver_source_ast(out_dir / "03_bath_only_fock_test.py")
        config_audit = validate_configuration_and_status(out_dir)
        solver_acceptance = config_audit["solver_acceptance"]
        solver_operator_audit = load_json(out_dir / "Stage03_operator_audit.json")

        operators_by_cutoff = {
            cutoff: construct_independent_operators(cutoff) for cutoff in SHELL_CUTOFFS
        }
        random_audits = replay_and_fresh_operator_audits(operators_by_cutoff)

        # Exact comparison with the solver operator-audit JSON.  The replay seed
        # is only for numerical equivalence; the fresh seed is a separate blind
        # audit and is independently gated.
        replay_operator = random_audits["replay_operator"]
        operator_json_differences: List[float] = []
        operator_json_mismatches: List[str] = []
        for cutoff in SHELL_CUTOFFS:
            solver_record = solver_operator_audit["per_cutoff"][str(cutoff)]
            loader_record = replay_operator["per_cutoff"][str(cutoff)]
            for key, solver_value in solver_record.items():
                if key not in loader_record:
                    operator_json_mismatches.append(f"N{cutoff}:{key}:missing")
                    continue
                if isinstance(solver_value, (int, float)) and isinstance(
                    loader_record[key], (int, float)
                ):
                    difference = abs(float(solver_value) - float(loader_record[key]))
                    operator_json_differences.append(difference)
                    if not values_close(
                        float(solver_value), float(loader_record[key]),
                        CSV_NUMERIC_COMPARISON_ATOL
                    ):
                        operator_json_mismatches.append(
                            f"N{cutoff}:{key}:{solver_value}!={loader_record[key]}"
                        )
                elif solver_value != loader_record[key]:
                    operator_json_mismatches.append(
                        f"N{cutoff}:{key}:{solver_value!r}!={loader_record[key]!r}"
                    )
        operator_json_pass = not operator_json_mismatches

        arrays, npz_audit = load_and_validate_npz(
            out_dir / "Stage03_time_series.npz", operators_by_cutoff
        )

        case_metrics: Dict[str, Dict[str, Any]] = {}
        case_diagnostics: Dict[str, Dict[str, Any]] = {}
        for spec in CASE_SPECS:
            operators = operators_by_cutoff[spec.cutoff]
            metrics = reconstruct_base_case_metrics(spec, arrays, operators)
            diagnostics = augment_case_specific_metrics(
                metrics, spec, arrays, operators
            )
            metrics["loader_occupation_series"] = series(
                arrays, spec.case_id, "occupation_total"
            ).copy()
            case_metrics[spec.case_id] = metrics
            case_diagnostics[spec.case_id] = diagnostics

        thermal_records, population_curves = independent_thermal_references(
            arrays, operators_by_cutoff
        )
        independent_pair_rows = independent_pairwise_cutoff_metrics(
            population_curves, operators_by_cutoff
        )
        solver_pair_rows = reconstruct_solver_pair_rows_from_npz(
            arrays, case_metrics, operators_by_cutoff
        )

        # Cutoff-case rows in the exact solver CSV schema.
        cutoff_case_rows: List[Dict[str, Any]] = []
        for family in ("B2", "B3"):
            for cutoff in SHELL_CUTOFFS:
                case_id = f"{family}_N{cutoff}"
                m = case_metrics[case_id]
                cutoff_case_rows.append({
                    "row_type": "cutoff_case",
                    "family": family,
                    "case_id": case_id,
                    "cutoff": cutoff,
                    "dimension": m["dimension"],
                    "maximum_top_shell_population": m["maximum_top_shell_population"],
                    "final_top_shell_population": m["final_top_shell_population"],
                    "maximum_omitted_upward_intensity": m["maximum_omitted_upward_intensity"],
                    "final_overflow_budget": m["final_overflow_budget"],
                    "maximum_population_reference_l1": m["maximum_population_reference_l1"],
                    "maximum_projected_occupation_reference_error": m[
                        "maximum_projected_occupation_reference_error"
                    ],
                    "maximum_infinite_occupation_error": m[
                        "maximum_infinite_occupation_error"
                    ],
                    "maximum_infinite_occupation_bound_excess": m[
                        "maximum_infinite_occupation_bound_excess"
                    ],
                    "final_occupation_total": m["final_occupation_total"],
                    "final_purity": m["final_purity"],
                })

        # B7 replay row is included in the exact solver case-CSV comparison.
        b7_replay = random_audits["replay_b7"]
        reconstructed_solver_case_rows: List[Dict[str, Any]] = []
        for spec in CASE_SPECS:
            reconstructed_solver_case_rows.append({
                key: value for key, value in case_metrics[spec.case_id].items()
                if not key.startswith("loader_")
            })
        reconstructed_solver_case_rows.append({
            "case_id": "B7",
            "description": "isotropic bath-basis invariance",
            "cutoff": 12,
            "dimension": 91,
            "omega": OMEGA,
            "gamma_down": "unit operator identity",
            "gamma_up": "unit operator identity",
            "gamma_phi": 0.0,
            "initial_state": "random Hermitian tests",
            "T_final": 0.0,
            "number_of_output_times": 0,
            **b7_replay,
        })

        case_fieldnames, solver_case_rows = load_csv(
            out_dir / "Stage03_case_metrics.csv"
        )
        cutoff_fieldnames, solver_cutoff_rows = load_csv(
            out_dir / "Stage03_cutoff_metrics.csv"
        )
        case_csv_comparison = compare_csv_rows(
            case_fieldnames,
            solver_case_rows,
            reconstructed_solver_case_rows,
            lambda row: str(row["case_id"]),
            "Stage03_case_metrics.csv",
        )
        reconstructed_solver_cutoff_rows = cutoff_case_rows + solver_pair_rows
        cutoff_csv_comparison = compare_csv_rows(
            cutoff_fieldnames,
            solver_cutoff_rows,
            reconstructed_solver_cutoff_rows,
            lambda row: (
                str(row["row_type"]), str(row["family"]),
                str(row.get("case_id", "")), str(row.get("small_cutoff", "")),
                str(row.get("large_cutoff", ""))
            ),
            "Stage03_cutoff_metrics.csv",
        )

        equivalent_acceptance = build_acceptance(
            replay_operator,
            case_metrics,
            b7_replay,
            cutoff_case_rows,
            solver_pair_rows,
            refined_thermal=None,
        )
        refined_acceptance = build_acceptance(
            replay_operator,
            case_metrics,
            b7_replay,
            cutoff_case_rows,
            solver_pair_rows,
            refined_thermal=thermal_records,
        )
        acceptance_comparison = compare_acceptance_records(
            solver_acceptance, equivalent_acceptance, refined_acceptance
        )

        max_population_curve_error = max(
            float(item["independent_population_curve_max_error"])
            for item in thermal_records.values()
        )
        max_initial_density_error = max(
            float(case_metrics[case_id]["loader_initial_density_fro_error"])
            for case_id in case_metrics
        )
        max_final_density_error = max(
            float(case_metrics[case_id]["loader_final_density_series_max_error"])
            for case_id in case_metrics
        )
        max_overflow_refinement_difference = max(
            abs(float(item["exact_minus_solver_trapezoid_overflow"]))
            for item in thermal_records.values()
        )
        case_specific_curve_error = max(
            [0.0] + [
                float(value)
                for diagnostics in case_diagnostics.values()
                for value in diagnostics.values()
                if isinstance(value, (int, float, np.integer, np.floating))
            ]
        )

        infrastructure = {
            "hash_validation_pass": hash_audit["all_required_hashes_match"],
            "configuration_validation_pass": True,
            "source_guard_pass": source_guard["source_import_guard_pass"],
            "npz_schema_pass": npz_audit["npz_exact_schema_match"],
            "case_csv_comparison_pass": case_csv_comparison["pass"],
            "cutoff_csv_comparison_pass": cutoff_csv_comparison["pass"],
            "operator_json_comparison_pass": operator_json_pass,
            "independent_population_curves_pass": (
                max_population_curve_error <= SERIES_RECONSTRUCTION_ATOL
            ),
            "initial_final_density_pass": (
                max(max_initial_density_error, max_final_density_error)
                <= INITIAL_FINAL_DENSITY_ATOL
            ),
            "fresh_random_audit_pass": random_audits["fresh_random_audit_pass"],
            "exact_overflow_refinement_pass": (
                max_overflow_refinement_difference <= EXACT_OVERFLOW_VS_TRAPEZOID_ATOL
            ),
            "case_specific_derived_curve_pass": (
                case_specific_curve_error <= SERIES_RECONSTRUCTION_ATOL
            ),
            "acceptance_comparison_pass": acceptance_comparison["pass"],
            "maximum_independent_population_curve_error": max_population_curve_error,
            "maximum_initial_density_error": max_initial_density_error,
            "maximum_final_density_series_error": max_final_density_error,
            "maximum_exact_minus_trapezoid_overflow": max_overflow_refinement_difference,
            "maximum_case_specific_derived_curve_error": case_specific_curve_error,
            "maximum_operator_json_numeric_difference": max(
                [0.0] + operator_json_differences
            ),
            "operator_json_mismatches": operator_json_mismatches,
        }
        infrastructure_pass = all(
            bool(value) for key, value in infrastructure.items()
            if key.endswith("_pass")
        )
        accepted = (
            infrastructure_pass
            and equivalent_acceptance["accepted"]
            and refined_acceptance["accepted"]
            and acceptance_comparison["pass"]
        )

        # Write deterministic loader products.
        output_case_rows = loader_case_rows(
            case_metrics,
            thermal_records,
            b7_replay,
            random_audits["fresh_b7"],
            case_diagnostics,
        )
        output_cutoff_rows = loader_cutoff_rows(
            case_metrics,
            thermal_records,
            solver_pair_rows,
            independent_pair_rows,
        )
        atomic_write_csv(
            out_dir / "Stage03_loader_case_metrics.csv", output_case_rows
        )
        atomic_write_csv(
            out_dir / "Stage03_loader_cutoff_metrics.csv", output_cutoff_rows
        )

        # Remove non-JSON arrays from the audit-facing case dictionary.
        audit_case_metrics: Dict[str, Dict[str, Any]] = {}
        for case_id, metrics in case_metrics.items():
            audit_case_metrics[case_id] = {
                key: value for key, value in metrics.items()
                if key != "loader_occupation_series"
            }

        loader_audit: Dict[str, Any] = {
            "stage": LOADER_STAGE_NAME,
            "loader_version": LOADER_VERSION,
            "loader_sha256": loader_sha256,
            "solver_stage": SOLVER_STAGE_NAME,
            "solver_version": SOLVER_VERSION,
            "solver_sha256": EXPECTED_SOLVER_SHA256,
            "accepted": accepted,
            "scope": (
                "Independent detector-free Stage-03 bath-only loader. This does "
                "not authorize scientific Stage 04 unless Stage 01C also passes."
            ),
            "directory_contract": {
                "fixed_directory_name": OUTPUT_DIRECTORY_NAME,
                "timestamped_directories": False,
                "parameter_generated_directories": False,
                "same_directory_reuse": True,
            },
            "hash_audit": hash_audit,
            "source_guard": source_guard,
            "configuration_audit": {
                key: value for key, value in config_audit.items()
                if key not in {"config", "status", "solver_audit", "solver_acceptance"}
            },
            "npz_audit": npz_audit,
            "operator_replay_audit": replay_operator,
            "operator_fresh_seed_audit": random_audits["fresh_operator"],
            "b7_replay_audit": b7_replay,
            "b7_fresh_seed_audit": random_audits["fresh_b7"],
            "case_metrics": audit_case_metrics,
            "case_specific_diagnostics": case_diagnostics,
            "thermal_reference_audit": thermal_records,
            "independent_pairwise_cutoff_audit": independent_pair_rows,
            "solver_pairwise_cutoff_reconstruction": {
                f"{row['family']}_N{row['small_cutoff']}_to_N{row['large_cutoff']}": row
                for row in solver_pair_rows
            },
            "case_csv_comparison": case_csv_comparison,
            "cutoff_csv_comparison": cutoff_csv_comparison,
            "operator_json_comparison": {
                "pass": operator_json_pass,
                "maximum_numeric_difference": max([0.0] + operator_json_differences),
                "mismatches": operator_json_mismatches,
            },
            "solver_equivalent_acceptance": equivalent_acceptance,
            "independent_refined_acceptance": refined_acceptance,
            "solver_loader_acceptance_comparison": acceptance_comparison,
            "infrastructure": infrastructure,
            "infrastructure_pass": infrastructure_pass,
            "implementation_guards": {
                "imports_solver": False,
                "detector_present": False,
                "longitudinal_coordinate_present": False,
                "density_matrix_repropagation_present": False,
                "independent_population_reference_present": True,
                "exact_augmented_overflow_present": True,
                "monte_carlo_present": False,
                "positivity_clipping_present": False,
                "trace_renormalization_present": False,
                "arithmetic": "NumPy/SciPy float64 and complex128",
            },
        }
        atomic_write_json(out_dir / "Stage03_loader_audit.json", loader_audit)

        report = build_report(
            accepted,
            hash_audit,
            infrastructure,
            refined_acceptance,
            acceptance_comparison,
            thermal_records,
            loader_sha256,
        )
        atomic_write_text(out_dir / "Stage03_bath_only_report.md", report)
        atomic_write_json(
            out_dir / "Stage03_loader_output_hashes.json",
            output_hash_manifest(out_dir),
        )

        elapsed = time.perf_counter() - start_time
        run_status.update({
            "status": "completed",
            "completed_utc": utc_now_iso(),
            "elapsed_seconds": elapsed,
            "accepted": accepted,
            "independent_acceptance_check_count": refined_acceptance["check_count"],
            "independent_acceptance_pass_count": refined_acceptance["pass_count"],
            "solver_loader_acceptance_agreement": acceptance_comparison["pass"],
            "all_required_hashes_match": hash_audit["all_required_hashes_match"],
        })
        atomic_write_json(run_status_path, run_status)

        print("\n[Task-04 independent acceptance]")
        for name, item in refined_acceptance["checks"].items():
            print(
                f"  {name:54s} value={item['value']:.12e} "
                f"criterion {item['criterion']} -> "
                f"{'PASS' if item['pass'] else 'FAIL'}"
            )
        print(f"\n[decision] independent loader accepted: {accepted}")
        print(
            "[decision] solver/loader check, criterion, and PASS/FAIL "
            f"agreement: {acceptance_comparison['pass']}"
        )
        print(
            "[refined] B3 N=12 exact overflow: "
            f"{thermal_records['B3_N12']['exact_augmented_overflow']:.15e}"
        )
        print(f"[info] elapsed seconds: {elapsed:.3f}")
        print(f"[info] outputs: {out_dir}")
        return 0 if accepted else 2

    except Exception as exc:
        elapsed = time.perf_counter() - start_time
        logging.exception("Task-04 independent Stage-03 loader failed")
        # Every previous PASS product was deleted before validation.  Only a
        # failure record is left, so stale acceptance cannot be mistaken for a
        # current result.
        failure = {
            "status": "failed",
            "failed_utc": utc_now_iso(),
            "elapsed_seconds": elapsed,
            "stage": LOADER_STAGE_NAME,
            "loader_version": LOADER_VERSION,
            "loader_sha256": loader_sha256,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc(),
            "stale_loader_pass_products_removed_before_validation": True,
        }
        atomic_write_json(out_dir / "loader_failure.json", failure)
        run_status.update(failure)
        atomic_write_json(run_status_path, run_status)
        return 1
    finally:
        try:
            stdout_handle.flush()
            stdout_handle.close()
        finally:
            sys.stdout = original_stdout


if __name__ == "__main__":
    raise SystemExit(main())
