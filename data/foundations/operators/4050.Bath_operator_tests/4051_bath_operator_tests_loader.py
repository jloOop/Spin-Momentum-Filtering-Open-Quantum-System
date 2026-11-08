#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4051_bath_operator_tests_loader.py
==================================
Independent Stage-02 audit loader for ``4050_bath_operator_tests_solver.py``.

The loader does not trust the solver's PASS flag.  It:

1. verifies every solver-owned stable-file SHA-256 hash;
2. reconstructs the complete-shell ladder, number, commutator, Bohr, and K
   identities from the saved operator matrices;
3. independently rebuilds all fixed Cartesian cases at omega=1,100 and
   N=50,100,200;
4. recomputes refinement orders and omega-scale collapse;
5. recomputes every acceptance gate;
6. compares the independent result with the solver JSON/CSV products;
7. writes a human-readable Stage-02 audit report.

Directory contract
------------------
The loader reads and writes only in the explicitly fixed directory

    4050.Bath_operator_tests

under OUTDIR.  No timestamped or parameter-generated directory is created.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import platform
import shutil
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Sequence, Tuple

import numpy as np


STAGE_NAME = "02_bath_operator_tests"
SCRIPT_VERSION = "2026-08-02-bath-operator-tests-loader-v3-audited"
RUN_NAME = "4050.Bath_operator_tests"
OUT_ROOT = Path(os.getenv("OUTDIR", "."))

EXPECTED_SOLVER_VERSION = "2026-08-02-bath-operator-tests-solver-v3-audited"
EXPECTED_N_SHELL = 12
EXPECTED_OMEGA_CASES: Tuple[float, ...] = (1.0, 100.0)
EXPECTED_GRID_SIZES: Tuple[int, ...] = (50, 100, 200)
EXPECTED_REFERENCE_OMEGA = 100.0
EXPECTED_REFERENCE_GRID = 100
EXPECTED_HBAR = 1.0
EXPECTED_MASS = 1.0
EXPECTED_ELL = 10.0
EXPECTED_STAGE01_ARCHIVE_SHA256 = (
    "f17502b7ec643593c4690aa0c30fb868e0a9853eaca41cc94228a0e32e2379f7"
)
EXPECTED_REVIEWED_INPUT_SHA256: Dict[str, str] = {
    "750.Ref(3).py": (
        "8cf2095b2d760a0b702c930fe5690fe762d08ad7c721a8c53b5ed498d1744009"
    ),
    "4002_reference_regression(1).py": (
        "facecb007572b5409d9d1ddb34c874a234f0d70059780551dc2179a7d66d8b48"
    ),
    "4031_static_mode_library(2).py": (
        "eee0326442a7ddde4cc423f63c916810adec6f77202a72817db5f60f384b7dea"
    ),
    "4032_static_mode_library(1).py": (
        "11a7316ed997aa36f271ea47c2f1272dae86606053da6a84df958630e7fbf9b9"
    ),
    "NUM_Stage01_Static_Mode_Complete_Audit_and_Next_Workflow_2026-08-02(3).md": (
        "7b2444f5b10bcd3a86a2d301a40ebcaf2e88b8b28d329c8d3e069c4e97fc6f65"
    ),
}
EXPECTED_TOLERANCES: Dict[str, float] = {
    "exact": 1.0e-12,
    "adjoint": 1.0e-12,
    "psd": 1.0e-11,
    "isotropy": 1.0e-12,
    "bohr_relative": 1.0e-12,
    "K_hermiticity": 1.0e-12,
    "K_scale_collapse": 1.0e-12,
    "mode_overlap": 1.0e-8,
    "wall_leakage": 1.0e-8,
    "ladder_coefficient": 0.75,
    "occupation_coefficient": 0.50,
    "CCR_coefficient": 1.25,
    "minimum_refinement_order": 1.90,
    "omega_collapse": 1.0e-12,
}

LOADER_OWNED_FILES: Tuple[str, ...] = (
    "Stage02_loader_audit.json",
    "Stage02_loader_case_metrics.csv",
    "Stage02_loader_convergence_metrics.csv",
    "Stage02_loader_omega_collapse_metrics.csv",
    "Stage02_bath_operator_report.md",
    "Stage02_loader_output_hashes.json",
    "Stage02_loader_failure.json",
)


# =============================================================================
# Utilities
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
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    os.replace(tmp, path)


def atomic_write_text(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")
    os.replace(tmp, path)


def atomic_write_csv(
    path: Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]
) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})
    os.replace(tmp, path)


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise TypeError(f"Expected a JSON object in {path}")
    return payload


def read_csv_rows(path: Path) -> list[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def max_abs(array: np.ndarray) -> float:
    return 0.0 if array.size == 0 else float(np.max(np.abs(array)))


def frobenius_norm(array: np.ndarray) -> float:
    return float(np.linalg.norm(array, ord="fro"))


def vector_norm(vector: np.ndarray) -> float:
    return float(np.linalg.norm(vector))


def weighted_inner(left: np.ndarray, right: np.ndarray, weight: float) -> complex:
    return complex(np.vdot(left.reshape(-1), right.reshape(-1)) * weight)


def weighted_norm(array: np.ndarray, weight: float) -> float:
    value = weighted_inner(array, array, weight).real
    return float(math.sqrt(max(value, 0.0)))


def relative_pairing_defect(
    left: np.ndarray,
    right: np.ndarray,
    apply_operator: Callable[[np.ndarray], np.ndarray],
    apply_adjoint: Callable[[np.ndarray], np.ndarray],
    weight: float,
) -> float:
    lhs = weighted_inner(left, apply_operator(right), weight)
    rhs = weighted_inner(apply_adjoint(left), right, weight)
    return float(abs(lhs - rhs) / max(abs(lhs), abs(rhs), 1.0))


def relative_matrix_residual(residual: np.ndarray, reference: np.ndarray) -> float:
    return frobenius_norm(residual) / max(frobenius_norm(reference), 1.0)


def bool_record(
    passed: bool, metric: float, threshold: float, relation: str
) -> Dict[str, Any]:
    return {
        "passed": bool(passed),
        "metric": float(metric),
        "threshold": float(threshold),
        "relation": relation,
    }


def cleanup_loader_outputs(out_dir: Path) -> None:
    for name in LOADER_OWNED_FILES:
        path = out_dir / name
        if path.is_file() or path.is_symlink():
            path.unlink()


def require_files(out_dir: Path, names: Sequence[str]) -> None:
    missing = [name for name in names if not (out_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing required Stage-02 solver outputs:\n  " + "\n  ".join(missing)
        )


def compare_float(actual: float, expected: float, tolerance: float = 5.0e-12) -> float:
    scale = max(abs(actual), abs(expected), 1.0)
    return abs(actual - expected) / scale


# =============================================================================
# Hash and solver-product verification
# =============================================================================
def verify_solver_hashes(out_dir: Path) -> Dict[str, Any]:
    manifest = load_json(out_dir / "Stage02_output_hashes.json")
    if manifest.get("hash_algorithm") != "SHA-256":
        raise ValueError("Stage02_output_hashes.json does not declare SHA-256")
    if manifest.get("stage") != STAGE_NAME:
        raise ValueError("Stage02_output_hashes.json has the wrong stage name")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("Stage02_output_hashes.json has no file dictionary")

    mismatches: Dict[str, Dict[str, str]] = {}
    verified: Dict[str, str] = {}
    for name, expected in files.items():
        path = out_dir / name
        if not path.is_file():
            mismatches[name] = {"expected": str(expected), "found": "MISSING"}
            continue
        found = sha256_file(path)
        verified[name] = found
        if found != expected:
            mismatches[name] = {"expected": str(expected), "found": found}

    return {
        "all_hashes_match": not mismatches,
        "verified_file_count": len(verified),
        "mismatches": mismatches,
        "verified": verified,
    }


def verify_configuration(
    config: Mapping[str, Any], out_dir: Path
) -> Dict[str, Any]:
    """Verify the frozen scientific configuration independently of the solver."""
    if config.get("stage") != STAGE_NAME:
        raise ValueError("Stage02 configuration has the wrong stage name")
    if config.get("script_version") != EXPECTED_SOLVER_VERSION:
        raise ValueError("Stage02 solver version differs from the audited version")
    if config.get("run_name") != RUN_NAME:
        raise ValueError("Stage02 fixed run name is inconsistent")
    if int(config.get("N_shell", -1)) != EXPECTED_N_SHELL:
        raise ValueError("Stage02 shell cutoff differs from the audited value")
    if tuple(float(value) for value in config.get("omega_cases", ())) != (
        EXPECTED_OMEGA_CASES
    ):
        raise ValueError("Stage02 omega cases differ from the audited values")
    if tuple(int(value) for value in config.get("cartesian_grid_sizes", ())) != (
        EXPECTED_GRID_SIZES
    ):
        raise ValueError("Stage02 Cartesian grids differ from the audited values")
    if not math.isclose(
        float(config.get("reference_omega", float("nan"))),
        EXPECTED_REFERENCE_OMEGA,
        rel_tol=0.0,
        abs_tol=0.0,
    ):
        raise ValueError("Stage02 reference omega is inconsistent")
    if int(config.get("reference_grid", -1)) != EXPECTED_REFERENCE_GRID:
        raise ValueError("Stage02 reference grid is inconsistent")
    for name, expected in (
        ("hbar", EXPECTED_HBAR),
        ("mass", EXPECTED_MASS),
        ("ell", EXPECTED_ELL),
    ):
        if not math.isclose(
            float(config.get(name, float("nan"))),
            expected,
            rel_tol=0.0,
            abs_tol=0.0,
        ):
            raise ValueError(f"Stage02 {name} differs from the audited value")
    expected_dimension = (EXPECTED_N_SHELL + 1) * (EXPECTED_N_SHELL + 2) // 2
    if int(config.get("complete_shell_dimension", -1)) != expected_dimension:
        raise ValueError("Stage02 complete-shell dimension is inconsistent")
    if config.get("authoritative_representation") != (
        "complete_shell_oscillator_basis"
    ):
        raise ValueError("Stage02 authoritative representation is inconsistent")
    if config.get("cartesian_role") != "Stage-01 low-mode cross-check only":
        raise ValueError("Stage02 Cartesian role is inconsistent")
    for flag in (
        "detector_core_imported",
        "detector_core_modified",
        "bath_generator_active",
        "time_propagation_active",
    ):
        if config.get(flag) is not False:
            raise ValueError(f"Stage02 scope flag {flag} must be false")

    tolerances = config.get("tolerances")
    if not isinstance(tolerances, dict) or set(tolerances) != set(
        EXPECTED_TOLERANCES
    ):
        raise ValueError("Stage02 tolerance schema differs from the audited schema")
    for name, expected in EXPECTED_TOLERANCES.items():
        if not math.isclose(
            float(tolerances[name]), expected, rel_tol=0.0, abs_tol=0.0
        ):
            raise ValueError(f"Stage02 tolerance {name} differs from the audit")

    if config.get("reviewed_input_sha256") != EXPECTED_REVIEWED_INPUT_SHA256:
        raise ValueError("Stage02 reviewed-input provenance is inconsistent")
    if config.get("stage01_archive_sha256") != EXPECTED_STAGE01_ARCHIVE_SHA256:
        raise ValueError("Stage02 Stage-01 archive provenance is inconsistent")

    supplied_full_hash = str(config.get("configuration_sha256", ""))
    full_payload = dict(config)
    full_payload.pop("configuration_sha256", None)
    recomputed_full_hash = sha256_json(full_payload)
    if supplied_full_hash != recomputed_full_hash:
        raise RuntimeError("Stage02 configuration SHA-256 is internally inconsistent")

    supplied_physics_hash = str(config.get("physics_configuration_sha256", ""))
    physics_payload = dict(config)
    physics_payload.pop("runtime", None)
    physics_payload.pop("configuration_sha256", None)
    physics_payload.pop("physics_configuration_sha256", None)
    recomputed_physics_hash = sha256_json(physics_payload)
    if supplied_physics_hash != recomputed_physics_hash:
        raise RuntimeError(
            "Stage02 physics-configuration SHA-256 is internally inconsistent"
        )

    solver_path = out_dir / "4050_bath_operator_tests_solver.py"
    actual_solver_hash = sha256_file(solver_path)
    if config.get("script_sha256") != actual_solver_hash:
        raise RuntimeError("Stage02 configuration/script SHA-256 mismatch")

    return {
        "configuration_sha256": supplied_full_hash,
        "physics_configuration_sha256": supplied_physics_hash,
        "solver_script_sha256": actual_solver_hash,
        "frozen_configuration_verified": True,
    }


# =============================================================================
# Independent authoritative-operator reconstruction
# =============================================================================
def authoritative_metrics(
    arrays: Mapping[str, np.ndarray],
    *,
    n_shell: int,
    omega_cases: Sequence[float],
    hbar: float,
    mass: float,
) -> Dict[str, float]:
    labels_array = np.asarray(arrays["mode_labels"], dtype=np.int64)
    labels = [tuple(int(value) for value in row) for row in labels_array]
    dimension = len(labels)
    expected_dimension = (n_shell + 1) * (n_shell + 2) // 2
    if dimension != expected_dimension:
        raise ValueError("Saved complete-shell dimension is inconsistent")
    expected_labels = [
        (nx, total - nx)
        for total in range(n_shell + 1)
        for nx in range(total + 1)
    ]
    if labels != expected_labels:
        raise ValueError("Saved complete-shell label ordering is inconsistent")
    index = {label: position for position, label in enumerate(labels)}

    a_x = np.asarray(arrays["a_x"], dtype=np.complex128)
    a_y = np.asarray(arrays["a_y"], dtype=np.complex128)
    a_x_dagger = np.asarray(arrays["a_x_dagger"], dtype=np.complex128)
    a_y_dagger = np.asarray(arrays["a_y_dagger"], dtype=np.complex128)
    number_x = np.asarray(arrays["N_x"], dtype=np.complex128)
    number_y = np.asarray(arrays["N_y"], dtype=np.complex128)
    number_perp = np.asarray(arrays["N_perp"], dtype=np.complex128)
    identity = np.eye(dimension, dtype=np.complex128)

    def e(label: Tuple[int, int]) -> np.ndarray:
        vector = np.zeros(dimension, dtype=np.complex128)
        vector[index[label]] = 1.0
        return vector

    all_ladder = []
    for nx, ny in labels:
        source = e((nx, ny))
        expected_x_lower = np.zeros(dimension, dtype=np.complex128)
        expected_y_lower = np.zeros(dimension, dtype=np.complex128)
        if nx > 0:
            expected_x_lower = math.sqrt(nx) * e((nx - 1, ny))
        if ny > 0:
            expected_y_lower = math.sqrt(ny) * e((nx, ny - 1))
        all_ladder.append(vector_norm(a_x @ source - expected_x_lower))
        all_ladder.append(vector_norm(a_y @ source - expected_y_lower))

        if nx + ny < n_shell:
            all_ladder.append(
                vector_norm(a_x_dagger @ source - math.sqrt(nx + 1) * e((nx + 1, ny)))
            )
            all_ladder.append(
                vector_norm(a_y_dagger @ source - math.sqrt(ny + 1) * e((nx, ny + 1)))
            )
        else:
            all_ladder.append(vector_norm(a_x_dagger @ source))
            all_ladder.append(vector_norm(a_y_dagger @ source))

    rng = np.random.default_rng(20260802)
    pairing = []
    for _ in range(8):
        left = rng.normal(size=dimension) + 1j * rng.normal(size=dimension)
        right = rng.normal(size=dimension) + 1j * rng.normal(size=dimension)
        pairing.append(
            relative_pairing_defect(
                left,
                right,
                lambda vector: a_x @ vector,
                lambda vector: a_x_dagger @ vector,
                1.0,
            )
        )
        pairing.append(
            relative_pairing_defect(
                left,
                right,
                lambda vector: a_y @ vector,
                lambda vector: a_y_dagger @ vector,
                1.0,
            )
        )

    adjoint_metric = max(
        max_abs(a_x_dagger - a_x.conj().T),
        max_abs(a_y_dagger - a_y.conj().T),
        max(pairing),
    )

    number_metric = max(
        max_abs(number_x - a_x_dagger @ a_x),
        max_abs(number_y - a_y_dagger @ a_y),
        max_abs(number_perp - number_x - number_y),
        max_abs(number_x - np.diag([nx for nx, _ in labels])),
        max_abs(number_y - np.diag([ny for _, ny in labels])),
    )
    min_number_eigenvalue = min(
        float(np.min(np.linalg.eigvalsh(0.5 * (number_x + number_x.conj().T)))),
        float(np.min(np.linalg.eigvalsh(0.5 * (number_y + number_y.conj().T)))),
    )

    comm_x = a_x @ a_x_dagger - a_x_dagger @ a_x
    comm_y = a_y @ a_y_dagger - a_y_dagger @ a_y
    expected_x = identity.copy()
    expected_y = identity.copy()
    expected_xy_dagger = np.zeros_like(identity)
    expected_yx_dagger = np.zeros_like(identity)
    for position, (nx, ny) in enumerate(labels):
        if nx + ny == n_shell:
            expected_x[position, position] -= nx + 1
            expected_y[position, position] -= ny + 1
            if nx > 0:
                expected_xy_dagger[index[(nx - 1, ny + 1)], position] = -math.sqrt(
                    nx * (ny + 1)
                )
            if ny > 0:
                expected_yx_dagger[index[(nx + 1, ny - 1)], position] = -math.sqrt(
                    ny * (nx + 1)
                )

    comm_metric = max(
        max_abs(comm_x - expected_x),
        max_abs(comm_y - expected_y),
        max_abs(a_x @ a_y - a_y @ a_x),
        max_abs(a_x_dagger @ a_y_dagger - a_y_dagger @ a_x_dagger),
        max_abs(a_x @ a_y_dagger - a_y_dagger @ a_x - expected_xy_dagger),
        max_abs(a_y @ a_x_dagger - a_x_dagger @ a_y - expected_yx_dagger),
        max_abs(number_x @ a_x - a_x @ number_x + a_x),
        max_abs(
            number_x @ a_x_dagger
            - a_x_dagger @ number_x
            - a_x_dagger
        ),
        max_abs(number_y @ a_y - a_y @ number_y + a_y),
        max_abs(
            number_y @ a_y_dagger
            - a_y_dagger @ number_y
            - a_y_dagger
        ),
        max_abs(number_x @ a_y - a_y @ number_x),
        max_abs(number_y @ a_x - a_x @ number_y),
    )

    swap = np.zeros_like(identity)
    for column, (nx, ny) in enumerate(labels):
        swap[index[(ny, nx)], column] = 1.0
    isotropy_metric = max(
        max_abs(swap.conj().T @ swap - identity),
        max_abs(swap @ a_x @ swap.conj().T - a_y),
        max_abs(swap @ number_x @ swap.conj().T - number_y),
    )

    bohr_metric = 0.0
    h_formula_metric = 0.0
    k_hermiticity = 0.0
    k_formula_metric = 0.0
    scaled_k_matrices = []
    sigma_x = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    sigma_y = np.asarray([[0.0, -1j], [1j, 0.0]], dtype=np.complex128)
    for omega in omega_cases:
        suffix = f"omega_{omega:g}".replace(".", "p")
        h_perp = np.asarray(arrays[f"H_perp_{suffix}"], dtype=np.complex128)
        h_formula_metric = max(
            h_formula_metric,
            max_abs(h_perp - hbar * omega * (number_perp + identity)),
        )
        tests = (
            (h_perp @ a_x - a_x @ h_perp + hbar * omega * a_x, hbar * omega * a_x),
            (h_perp @ a_y - a_y @ h_perp + hbar * omega * a_y, hbar * omega * a_y),
            (
                h_perp @ a_x_dagger - a_x_dagger @ h_perp - hbar * omega * a_x_dagger,
                hbar * omega * a_x_dagger,
            ),
            (
                h_perp @ a_y_dagger - a_y_dagger @ h_perp - hbar * omega * a_y_dagger,
                hbar * omega * a_y_dagger,
            ),
        )
        bohr_metric = max(
            bohr_metric,
            *(relative_matrix_residual(residual, reference) for residual, reference in tests),
        )
        k_operator = np.asarray(arrays[f"K_{suffix}"], dtype=np.complex128)
        k_hermiticity = max(
            k_hermiticity, max_abs(k_operator - k_operator.conj().T)
        )
        ell_perp = math.sqrt(hbar / (mass * omega))
        expected_k = (
            1j
            / (math.sqrt(2.0) * ell_perp)
            * (
                np.kron(a_y_dagger - a_y, sigma_x)
                - np.kron(a_x_dagger - a_x, sigma_y)
            )
        )
        k_formula_metric = max(
            k_formula_metric, max_abs(k_operator - expected_k)
        )
        scaled_k_matrices.append(k_operator / math.sqrt(omega))

    k_scale_metric = 0.0
    for matrix in scaled_k_matrices[1:]:
        k_scale_metric = max(k_scale_metric, max_abs(matrix - scaled_k_matrices[0]))

    return {
        "dimension": float(dimension),
        "maximum_all_mode_ladder_residual": max(all_ladder, default=0.0),
        "maximum_adjoint_defect": adjoint_metric,
        "minimum_number_eigenvalue": min_number_eigenvalue,
        "maximum_number_identity_defect": number_metric,
        "maximum_isotropy_defect": isotropy_metric,
        "maximum_projected_commutator_formula_defect": comm_metric,
        "maximum_bohr_relative_residual": bohr_metric,
        "maximum_H_perp_formula_defect": h_formula_metric,
        "maximum_K_hermiticity_defect": k_hermiticity,
        "maximum_K_formula_defect": k_formula_metric,
        "maximum_K_scaled_collapse_defect": k_scale_metric,
    }


# =============================================================================
# Independent Cartesian reconstruction
# =============================================================================
def centered_derivative(n_interior: int, spacing: float) -> np.ndarray:
    derivative = np.zeros((n_interior, n_interior), dtype=np.float64)
    coefficient = 1.0 / (2.0 * spacing)
    for row in range(n_interior):
        if row > 0:
            derivative[row, row - 1] = -coefficient
        if row < n_interior - 1:
            derivative[row, row + 1] = coefficient
    return derivative


def wall_probability(array: np.ndarray, hx: float, hy: float) -> float:
    pieces = (
        array[0, :],
        array[-1, :],
        array[1:-1, 0],
        array[1:-1, -1],
    )
    return sum(float(np.sum(np.abs(piece) ** 2)) for piece in pieces) * hx * hy


def independent_cartesian_metrics(
    *, omega: float, n_grid: int, ell: float, hbar: float, mass: float
) -> Dict[str, Any]:
    length = ell / math.sqrt(omega)
    x = np.linspace(0.0, length, n_grid, endpoint=False, dtype=np.float64)
    y = np.linspace(0.0, length, n_grid, endpoint=False, dtype=np.float64)
    hx = float(x[1] - x[0])
    hy = float(y[1] - y[0])
    weight = hx * hy
    xc = x - length / 2.0
    yc = y - length / 2.0
    xx, yy = np.meshgrid(xc, yc, indexing="ij")
    gaussian = np.exp(-omega * (xx * xx + yy * yy) / 2.0)
    raw = {
        "00": gaussian,
        "10": math.sqrt(2.0 * omega) * xx * gaussian,
        "01": math.sqrt(2.0 * omega) * yy * gaussian,
    }

    wall_fractions = []
    modes: Dict[str, np.ndarray] = {}
    for label, field in raw.items():
        total = float(np.sum(np.abs(field) ** 2) * weight)
        wall_fractions.append(wall_probability(field, hx, hy) / total)
        clamped = field.copy()
        clamped[[0, -1], :] = 0.0
        clamped[:, [0, -1]] = 0.0
        clamped /= math.sqrt(float(np.sum(np.abs(clamped) ** 2) * weight))
        modes[label] = clamped

    order = ("00", "10", "01")
    overlap = np.asarray(
        [
            [weighted_inner(modes[left], modes[right], weight) for right in order]
            for left in order
        ],
        dtype=np.complex128,
    )
    overlap_defect = max(
        float(np.max(np.abs(np.diag(overlap) - 1.0))),
        max_abs(overlap - np.diag(np.diag(overlap))),
    )

    n_interior = n_grid - 2
    derivative_x = centered_derivative(n_interior, hx)
    derivative_y = centered_derivative(n_interior, hy)
    position_x = np.diag(xc[1:-1])
    position_y = np.diag(yc[1:-1])
    alpha = math.sqrt(mass * omega / (2.0 * hbar))
    beta = math.sqrt(hbar / (2.0 * mass * omega))
    ax_matrix = alpha * position_x + beta * derivative_x
    ay_matrix = alpha * position_y + beta * derivative_y
    axd_matrix = alpha * position_x - beta * derivative_x
    ayd_matrix = alpha * position_y - beta * derivative_y

    def ax(field: np.ndarray) -> np.ndarray:
        return ax_matrix @ field

    def ay(field: np.ndarray) -> np.ndarray:
        return field @ ay_matrix.T

    def axd(field: np.ndarray) -> np.ndarray:
        return axd_matrix @ field

    def ayd(field: np.ndarray) -> np.ndarray:
        return field @ ayd_matrix.T

    interior = {label: field[1:-1, 1:-1] for label, field in modes.items()}
    f00 = interior["00"]
    f10 = interior["10"]
    f01 = interior["01"]
    ladder = (
        weighted_norm(ax(f00), weight),
        weighted_norm(ay(f00), weight),
        weighted_norm(ax(f10) - f00, weight),
        weighted_norm(ay(f01) - f00, weight),
        weighted_norm(axd(f00) - f10, weight),
        weighted_norm(ayd(f00) - f01, weight),
        weighted_norm(ax(f01), weight),
        weighted_norm(ay(f10), weight),
    )

    nx_matrix = axd_matrix @ ax_matrix
    ny_matrix = ayd_matrix @ ay_matrix
    targets = {"00": (0.0, 0.0), "10": (1.0, 0.0), "01": (0.0, 1.0)}
    occupation_errors = []
    occupations: Dict[str, Tuple[float, float]] = {}
    for label, field in interior.items():
        nx_value = weighted_inner(field, nx_matrix @ field, weight).real
        ny_value = weighted_inner(field, field @ ny_matrix.T, weight).real
        occupations[label] = (float(nx_value), float(ny_value))
        occupation_errors.extend(
            (abs(nx_value - targets[label][0]), abs(ny_value - targets[label][1]))
        )

    comm_x = ax_matrix @ axd_matrix - axd_matrix @ ax_matrix
    comm_y = ay_matrix @ ayd_matrix - ayd_matrix @ ay_matrix
    ccr = []
    cross = []
    for field in interior.values():
        ccr.extend(
            (
                weighted_norm(comm_x @ field - field, weight),
                weighted_norm(field @ comm_y.T - field, weight),
            )
        )
        cross.extend(
            (
                weighted_norm(ax(ay(field)) - ay(ax(field)), weight),
                weighted_norm(ax(ayd(field)) - ayd(ax(field)), weight),
                weighted_norm(axd(ay(field)) - ay(axd(field)), weight),
                weighted_norm(axd(ayd(field)) - ayd(axd(field)), weight),
            )
        )

    rng = np.random.default_rng(20260802 + n_grid)
    pairing = []
    for _ in range(8):
        left = rng.normal(size=(n_interior, n_interior)) + 1j * rng.normal(
            size=(n_interior, n_interior)
        )
        right = rng.normal(size=(n_interior, n_interior)) + 1j * rng.normal(
            size=(n_interior, n_interior)
        )
        pairing.append(relative_pairing_defect(left, right, ax, axd, weight))
        pairing.append(relative_pairing_defect(left, right, ay, ayd, weight))

    min_eig = min(
        float(np.min(np.linalg.eigvalsh(0.5 * (nx_matrix + nx_matrix.conj().T)))),
        float(np.min(np.linalg.eigvalsh(0.5 * (ny_matrix + ny_matrix.conj().T)))),
    )
    adjoint_defect = max(
        max_abs(axd_matrix - ax_matrix.conj().T),
        max_abs(ayd_matrix - ay_matrix.conj().T),
        max(pairing),
    )
    isotropy_defect = max(
        max_abs(ax_matrix - ay_matrix),
        max_abs(nx_matrix - ny_matrix),
        abs(ladder[0] - ladder[1]),
        abs(ladder[2] - ladder[3]),
        abs(ladder[4] - ladder[5]),
    )

    def ground_tail_right(u: float) -> float:
        return 0.5 * math.erfc(u)

    def first_tail_right(u: float) -> float:
        return 0.5 * math.erfc(u) + (u / math.sqrt(math.pi)) * math.exp(-u * u)

    ux_left = math.sqrt(omega) * xc[0]
    ux_right = math.sqrt(omega) * xc[-1]
    uy_left = math.sqrt(omega) * yc[0]
    uy_right = math.sqrt(omega) * yc[-1]
    ground_inside_x = 1.0 - ground_tail_right(-ux_left) - ground_tail_right(ux_right)
    ground_inside_y = 1.0 - ground_tail_right(-uy_left) - ground_tail_right(uy_right)
    first_inside_x = 1.0 - first_tail_right(-ux_left) - first_tail_right(ux_right)
    first_inside_y = 1.0 - first_tail_right(-uy_left) - first_tail_right(uy_right)
    ground_outside = 1.0 - ground_inside_x * ground_inside_y
    mode10_outside = 1.0 - first_inside_x * ground_inside_y
    mode01_outside = 1.0 - ground_inside_x * first_inside_y

    eta = max(math.sqrt(omega) * hx, math.sqrt(omega) * hy)
    eta_squared = eta * eta
    maximum_ladder = max(ladder)
    maximum_occupation = max(occupation_errors)
    maximum_ccr = max(ccr)
    maximum_wall = max(max(wall_fractions), mode10_outside, mode01_outside)

    return {
        "omega": float(omega),
        "N_grid": int(n_grid),
        "Nx": int(n_grid),
        "Ny": int(n_grid),
        "Lx": float(length),
        "Ly": float(length),
        "hx": float(hx),
        "hy": float(hy),
        "eta_sqrtomega_h": float(eta),
        "eta_squared": float(eta_squared),
        "maximum_mode_overlap_defect": float(overlap_defect),
        "maximum_weighted_adjoint_defect": float(adjoint_defect),
        "minimum_number_operator_eigenvalue": float(min_eig),
        "maximum_ladder_action_residual": float(maximum_ladder),
        "ladder_error_coefficient_over_eta_squared": float(
            maximum_ladder / eta_squared
        ),
        "maximum_occupation_abs_error": float(maximum_occupation),
        "occupation_error_coefficient_over_eta_squared": float(
            maximum_occupation / eta_squared
        ),
        "maximum_ccr_action_residual": float(maximum_ccr),
        "ccr_error_coefficient_over_eta_squared": float(maximum_ccr / eta_squared),
        "maximum_cross_commutator_action_residual": float(max(cross)),
        "maximum_xy_isotropy_defect": float(isotropy_defect),
        "maximum_wall_node_probability_fraction": float(max(wall_fractions)),
        "analytic_ground_probability_outside_actual_clamped_rectangle": float(
            ground_outside
        ),
        "analytic_mode10_probability_outside_actual_clamped_rectangle": float(
            mode10_outside
        ),
        "analytic_mode01_probability_outside_actual_clamped_rectangle": float(
            mode01_outside
        ),
        "maximum_wall_leakage_metric": float(maximum_wall),
        "trace_commutator_x": float(np.trace(comm_x).real),
        "trace_commutator_y": float(np.trace(comm_y).real),
        "mode00_Nx": occupations["00"][0],
        "mode00_Ny": occupations["00"][1],
        "mode10_Nx": occupations["10"][0],
        "mode10_Ny": occupations["10"][1],
        "mode01_Nx": occupations["01"][0],
        "mode01_Ny": occupations["01"][1],
    }


def independent_convergence_rows(
    cases: Sequence[Mapping[str, Any]], omega_cases: Sequence[float]
) -> list[Dict[str, Any]]:
    metrics = (
        "maximum_ladder_action_residual",
        "maximum_occupation_abs_error",
        "maximum_ccr_action_residual",
    )
    rows: list[Dict[str, Any]] = []
    for omega in omega_cases:
        subset = sorted(
            (case for case in cases if float(case["omega"]) == omega),
            key=lambda case: int(case["N_grid"]),
        )
        for coarse, fine in zip(subset[:-1], subset[1:]):
            ratio = float(coarse["eta_sqrtomega_h"]) / float(
                fine["eta_sqrtomega_h"]
            )
            for metric in metrics:
                e_coarse = float(coarse[metric])
                e_fine = float(fine[metric])
                order = math.log(e_coarse / e_fine) / math.log(ratio)
                rows.append(
                    {
                        "omega": omega,
                        "metric": metric,
                        "N_coarse": int(coarse["N_grid"]),
                        "N_fine": int(fine["N_grid"]),
                        "eta_coarse": float(coarse["eta_sqrtomega_h"]),
                        "eta_fine": float(fine["eta_sqrtomega_h"]),
                        "error_coarse": e_coarse,
                        "error_fine": e_fine,
                        "observed_order": order,
                    }
                )
    return rows


def independent_omega_rows(
    cases: Sequence[Mapping[str, Any]],
    omega_cases: Sequence[float],
    grid_sizes: Sequence[int],
) -> list[Dict[str, Any]]:
    metrics = (
        "eta_sqrtomega_h",
        "maximum_mode_overlap_defect",
        "maximum_weighted_adjoint_defect",
        "minimum_number_operator_eigenvalue",
        "maximum_ladder_action_residual",
        "maximum_occupation_abs_error",
        "maximum_ccr_action_residual",
        "maximum_cross_commutator_action_residual",
        "maximum_xy_isotropy_defect",
        "maximum_wall_leakage_metric",
    )
    base_omega = omega_cases[0]
    rows: list[Dict[str, Any]] = []
    for n_grid in grid_sizes:
        by_omega = {
            float(case["omega"]): case
            for case in cases
            if int(case["N_grid"]) == n_grid
        }
        for omega in omega_cases[1:]:
            for metric in metrics:
                reference = float(by_omega[base_omega][metric])
                comparison = float(by_omega[omega][metric])
                rows.append(
                    {
                        "N_grid": n_grid,
                        "omega_reference": base_omega,
                        "omega_comparison": omega,
                        "metric": metric,
                        "reference_value": reference,
                        "comparison_value": comparison,
                        "absolute_difference": abs(comparison - reference),
                    }
                )
    return rows


# =============================================================================
# Independent gate and comparison with solver products
# =============================================================================
def independent_acceptance(
    auth: Mapping[str, float],
    cases: Sequence[Mapping[str, Any]],
    convergence: Sequence[Mapping[str, Any]],
    omega_rows: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> Dict[str, Any]:
    tolerances = config["tolerances"]
    exact = float(tolerances["exact"])
    adjoint = float(tolerances["adjoint"])
    psd = float(tolerances["psd"])
    isotropy = float(tolerances["isotropy"])
    bohr = float(tolerances["bohr_relative"])
    k_hermiticity = float(tolerances["K_hermiticity"])
    k_scale = float(tolerances["K_scale_collapse"])
    mode_overlap = float(tolerances["mode_overlap"])
    wall = float(tolerances["wall_leakage"])
    ladder_coeff = float(tolerances["ladder_coefficient"])
    occupation_coeff = float(tolerances["occupation_coefficient"])
    ccr_coeff = float(tolerances["CCR_coefficient"])
    min_order_required = float(tolerances["minimum_refinement_order"])
    omega_tol = float(tolerances["omega_collapse"])

    reference_omega = float(config["reference_omega"])
    reference_grid = int(config["reference_grid"])
    reference_present = any(
        float(case["omega"]) == reference_omega
        and int(case["N_grid"]) == reference_grid
        for case in cases
    )

    checks = {
        "authoritative_all_ladder_actions": bool_record(
            auth["maximum_all_mode_ladder_residual"] <= exact,
            auth["maximum_all_mode_ladder_residual"],
            exact,
            "<=",
        ),
        "authoritative_adjoint": bool_record(
            auth["maximum_adjoint_defect"] <= adjoint,
            auth["maximum_adjoint_defect"],
            adjoint,
            "<=",
        ),
        "authoritative_number_positivity": bool_record(
            auth["minimum_number_eigenvalue"] >= -psd,
            auth["minimum_number_eigenvalue"],
            -psd,
            ">=",
        ),
        "authoritative_number_diagonal": bool_record(
            auth["maximum_number_identity_defect"] <= exact,
            auth["maximum_number_identity_defect"],
            exact,
            "<=",
        ),
        "authoritative_xy_isotropy": bool_record(
            auth["maximum_isotropy_defect"] <= isotropy,
            auth["maximum_isotropy_defect"],
            isotropy,
            "<=",
        ),
        "authoritative_projected_commutator_formulas": bool_record(
            auth["maximum_projected_commutator_formula_defect"] <= exact,
            auth["maximum_projected_commutator_formula_defect"],
            exact,
            "<=",
        ),
        "authoritative_bohr_relations": bool_record(
            max(
                auth["maximum_bohr_relative_residual"],
                auth["maximum_H_perp_formula_defect"],
            )
            <= bohr,
            max(
                auth["maximum_bohr_relative_residual"],
                auth["maximum_H_perp_formula_defect"],
            ),
            bohr,
            "<=",
        ),
        "authoritative_K_hermiticity": bool_record(
            auth["maximum_K_hermiticity_defect"] <= k_hermiticity,
            auth["maximum_K_hermiticity_defect"],
            k_hermiticity,
            "<=",
        ),
        "authoritative_K_formula": bool_record(
            auth["maximum_K_formula_defect"] <= exact,
            auth["maximum_K_formula_defect"],
            exact,
            "<=",
        ),
        "authoritative_K_sqrtomega_scaling": bool_record(
            auth["maximum_K_scaled_collapse_defect"] <= k_scale,
            auth["maximum_K_scaled_collapse_defect"],
            k_scale,
            "<=",
        ),
        "cartesian_reference_case_present": bool_record(
            reference_present,
            1.0 if reference_present else 0.0,
            1.0,
            "==",
        ),
        "cartesian_mode_orthonormality": bool_record(
            max(float(case["maximum_mode_overlap_defect"]) for case in cases)
            <= mode_overlap,
            max(float(case["maximum_mode_overlap_defect"]) for case in cases),
            mode_overlap,
            "<=",
        ),
        "cartesian_weighted_adjoint": bool_record(
            max(float(case["maximum_weighted_adjoint_defect"]) for case in cases)
            <= adjoint,
            max(float(case["maximum_weighted_adjoint_defect"]) for case in cases),
            adjoint,
            "<=",
        ),
        "cartesian_number_positivity": bool_record(
            min(float(case["minimum_number_operator_eigenvalue"]) for case in cases)
            >= -psd,
            min(float(case["minimum_number_operator_eigenvalue"]) for case in cases),
            -psd,
            ">=",
        ),
        "cartesian_ladder_O_eta_squared": bool_record(
            max(
                float(case["ladder_error_coefficient_over_eta_squared"])
                for case in cases
            )
            <= ladder_coeff,
            max(
                float(case["ladder_error_coefficient_over_eta_squared"])
                for case in cases
            ),
            ladder_coeff,
            "<=",
        ),
        "cartesian_occupation_O_eta_squared": bool_record(
            max(
                float(case["occupation_error_coefficient_over_eta_squared"])
                for case in cases
            )
            <= occupation_coeff,
            max(
                float(case["occupation_error_coefficient_over_eta_squared"])
                for case in cases
            ),
            occupation_coeff,
            "<=",
        ),
        "cartesian_CCR_O_eta_squared": bool_record(
            max(float(case["ccr_error_coefficient_over_eta_squared"]) for case in cases)
            <= ccr_coeff,
            max(float(case["ccr_error_coefficient_over_eta_squared"]) for case in cases),
            ccr_coeff,
            "<=",
        ),
        "cartesian_second_order_refinement": bool_record(
            min(float(row["observed_order"]) for row in convergence)
            >= min_order_required,
            min(float(row["observed_order"]) for row in convergence),
            min_order_required,
            ">=",
        ),
        "cartesian_cross_commutators": bool_record(
            max(
                float(case["maximum_cross_commutator_action_residual"])
                for case in cases
            )
            <= exact,
            max(
                float(case["maximum_cross_commutator_action_residual"])
                for case in cases
            ),
            exact,
            "<=",
        ),
        "cartesian_xy_isotropy": bool_record(
            max(float(case["maximum_xy_isotropy_defect"]) for case in cases)
            <= isotropy,
            max(float(case["maximum_xy_isotropy_defect"]) for case in cases),
            isotropy,
            "<=",
        ),
        "cartesian_omega_scale_collapse": bool_record(
            max(float(row["absolute_difference"]) for row in omega_rows) <= omega_tol,
            max(float(row["absolute_difference"]) for row in omega_rows),
            omega_tol,
            "<=",
        ),
        "cartesian_lateral_wall_leakage": bool_record(
            max(float(case["maximum_wall_leakage_metric"]) for case in cases) <= wall,
            max(float(case["maximum_wall_leakage_metric"]) for case in cases),
            wall,
            "<=",
        ),
    }
    all_passed = all(record["passed"] for record in checks.values())
    return {
        "stage": STAGE_NAME,
        "status": "PASS" if all_passed else "FAIL",
        "all_checks_passed": all_passed,
        "checks": checks,
    }


def compare_solver_csv(
    solver_rows: Sequence[Mapping[str, str]],
    loader_rows: Sequence[Mapping[str, Any]],
    key_fields: Sequence[str],
    numeric_fields: Sequence[str],
) -> Dict[str, Any]:
    def key_from_solver(row: Mapping[str, str]) -> Tuple[str, ...]:
        return tuple(str(row[field]) for field in key_fields)

    def normalized_key(row: Mapping[str, Any]) -> Tuple[str, ...]:
        values = []
        for field in key_fields:
            value = row[field]
            if isinstance(value, float):
                values.append(f"{value:g}")
            else:
                values.append(str(value))
        return tuple(values)

    # CSV may render 1.0 as 1.0 while loader key renders 1; compare through
    # numeric conversion for numeric key fields by falling back to row order.
    if len(solver_rows) != len(loader_rows):
        return {
            "passed": False,
            "row_count_solver": len(solver_rows),
            "row_count_loader": len(loader_rows),
            "maximum_relative_difference": float("inf"),
            "note": "row count mismatch",
        }

    maximum = 0.0
    for solver, loader in zip(solver_rows, loader_rows):
        for field in key_fields:
            try:
                key_defect = compare_float(float(solver[field]), float(loader[field]))
            except (TypeError, ValueError):
                key_defect = 0.0 if str(solver[field]) == str(loader[field]) else 1.0
            maximum = max(maximum, key_defect)
        for field in numeric_fields:
            maximum = max(
                maximum,
                compare_float(float(solver[field]), float(loader[field])),
            )
    return {
        "passed": maximum <= 5.0e-12,
        "row_count_solver": len(solver_rows),
        "row_count_loader": len(loader_rows),
        "maximum_relative_difference": maximum,
    }


def compare_acceptance(
    solver_acceptance: Mapping[str, Any], loader_acceptance: Mapping[str, Any]
) -> Dict[str, Any]:
    solver_checks = solver_acceptance.get("checks", {})
    loader_checks = loader_acceptance.get("checks", {})
    names_match = set(solver_checks) == set(loader_checks)
    maximum_metric_difference = 0.0
    maximum_threshold_difference = 0.0
    relation_mismatches = []
    pass_mismatches = []
    if names_match:
        for name in sorted(solver_checks):
            solver_record = solver_checks[name]
            loader_record = loader_checks[name]
            maximum_metric_difference = max(
                maximum_metric_difference,
                compare_float(
                    float(solver_record["metric"]), float(loader_record["metric"])
                ),
            )
            maximum_threshold_difference = max(
                maximum_threshold_difference,
                compare_float(
                    float(solver_record["threshold"]),
                    float(loader_record["threshold"]),
                ),
            )
            if solver_record.get("relation") != loader_record.get("relation"):
                relation_mismatches.append(name)
            if bool(solver_record["passed"]) != bool(loader_record["passed"]):
                pass_mismatches.append(name)
    return {
        "passed": (
            names_match
            and not pass_mismatches
            and not relation_mismatches
            and maximum_metric_difference <= 5.0e-12
            and maximum_threshold_difference <= 5.0e-12
            and solver_acceptance.get("status") == loader_acceptance.get("status")
        ),
        "check_names_match": names_match,
        "pass_mismatches": pass_mismatches,
        "relation_mismatches": relation_mismatches,
        "maximum_relative_metric_difference": maximum_metric_difference,
        "maximum_relative_threshold_difference": maximum_threshold_difference,
        "solver_status": solver_acceptance.get("status"),
        "loader_status": loader_acceptance.get("status"),
    }


# =============================================================================
# Report
# =============================================================================
def format_scientific(value: float) -> str:
    return f"{value:.6e}"


def make_report(
    *,
    config: Mapping[str, Any],
    hash_audit: Mapping[str, Any],
    auth: Mapping[str, float],
    cases: Sequence[Mapping[str, Any]],
    convergence: Sequence[Mapping[str, Any]],
    omega_rows: Sequence[Mapping[str, Any]],
    acceptance: Mapping[str, Any],
    solver_comparison: Mapping[str, Any],
    solver_script_hash: str,
    loader_script_hash: str,
) -> str:
    reference_omega = float(config["reference_omega"])
    reference_grid = int(config["reference_grid"])
    reference = next(
        case
        for case in cases
        if float(case["omega"]) == reference_omega
        and int(case["N_grid"]) == reference_grid
    )
    min_order = min(float(row["observed_order"]) for row in convergence)
    max_omega_difference = max(float(row["absolute_difference"]) for row in omega_rows)

    lines = [
        "# Stage 02 — Transverse Bath-Operator Complete Audit",
        "",
        f"**Status:** {acceptance['status']}",
        f"**Audit time:** {utc_now_iso()}",
        f"**Fixed output directory:** `{RUN_NAME}`",
        "",
        "## 1. Scope",
        "",
        "Stage 02 certifies the transverse operator layer only. The authoritative "
        "objects are the projected complete-shell oscillator matrices. The Cartesian "
        "calculation is a low-mode cross-check using the Stage-01 grid and mode conventions. "
        "No detector propagation, ABC modification, Crank–Nicolson step, GMRES solve, "
        "or Lindblad bath evolution is present.",
        "",
        "A PASS does **not** yet certify trace preservation, Gibbs stationarity, detector–bath "
        "composition, the scalar dynamical null, or any environmental susceptibility.",
        "",
        "## 2. Frozen configuration",
        "",
        f"- Complete-shell cutoff: `N_shell = {int(config['N_shell'])}`",
        f"- Retained transverse dimension: `{int(config['complete_shell_dimension'])}`",
        f"- Cartesian confinements: `{tuple(config['omega_cases'])}`",
        f"- Cartesian grids: `{tuple(config['cartesian_grid_sizes'])}`",
        f"- Stage-01 box scaling: `Lx = Ly = 10/sqrt(omega)`",
        "- Arithmetic: NumPy `float64` / `complex128`",
        "- Directory policy: fixed directory, reused, no timestamped or parameter-generated folder",
        "",
        "## 3. Authoritative complete-shell results",
        "",
        "| Check | Maximum defect |",
        "|---|---:|",
        f"| All lowering/raising actions | {format_scientific(auth['maximum_all_mode_ladder_residual'])} |",
        f"| Adjoint consistency | {format_scientific(auth['maximum_adjoint_defect'])} |",
        f"| Number-operator identity | {format_scientific(auth['maximum_number_identity_defect'])} |",
        f"| Projected commutator formulas | {format_scientific(auth['maximum_projected_commutator_formula_defect'])} |",
        f"| Oscillator Bohr relations | {format_scientific(auth['maximum_bohr_relative_residual'])} |",
        f"| Transverse Hamiltonian formula | {format_scientific(auth['maximum_H_perp_formula_defect'])} |",
        f"| K Hermiticity | {format_scientific(auth['maximum_K_hermiticity_defect'])} |",
        f"| K ladder-operator formula | {format_scientific(auth['maximum_K_formula_defect'])} |",
        f"| K/sqrt(omega) scale collapse | {format_scientific(auth['maximum_K_scaled_collapse_defect'])} |",
        "",
        "The full finite-dimensional canonical commutator is not required to equal the identity. "
        "The audit instead verifies the exact complete-shell top-shell defects and the exact "
        "cross-axis projected defects. This is the mathematically correct finite projection.",
        "",
        "## 4. Cartesian Stage-01 cross-check",
        "",
        f"Reference case: `omega={reference_omega:g}`, `N={reference_grid}`.",
        "",
        "| Quantity | Value |",
        "|---|---:|",
        f"| Maximum ladder-action residual | {format_scientific(float(reference['maximum_ladder_action_residual']))} |",
        f"| Maximum occupation error | {format_scientific(float(reference['maximum_occupation_abs_error']))} |",
        f"| Maximum low-mode CCR action residual | {format_scientific(float(reference['maximum_ccr_action_residual']))} |",
        f"| Maximum cross-commutator action residual | {format_scientific(float(reference['maximum_cross_commutator_action_residual']))} |",
        f"| Maximum x/y isotropy defect | {format_scientific(float(reference['maximum_xy_isotropy_defect']))} |",
        f"| Maximum wall-leakage metric | {format_scientific(float(reference['maximum_wall_leakage_metric']))} |",
        "",
        f"The minimum measured refinement order over ladder actions, number occupations, and "
        f"low-mode CCR actions is **{min_order:.6f}**. The maximum omega=1/100 scale-collapse "
        f"difference is **{max_omega_difference:.3e}**.",
        "",
        "## 5. Independent loader verification",
        "",
        f"- Solver stable-file hashes verified: `{hash_audit['verified_file_count']}`",
        f"- All solver hashes match: `{hash_audit['all_hashes_match']}`",
        f"- Independent gates agree with solver: `{solver_comparison['acceptance']['passed']}`",
        f"- Case CSV agrees: `{solver_comparison['case_csv']['passed']}`",
        f"- Convergence CSV agrees: `{solver_comparison['convergence_csv']['passed']}`",
        f"- Omega-collapse CSV agrees: `{solver_comparison['omega_csv']['passed']}`",
        "",
        "## 6. Acceptance gates",
        "",
        "| Gate | Status | Metric | Threshold |",
        "|---|---|---:|---:|",
    ]
    for name, record in acceptance["checks"].items():
        status = "PASS" if record["passed"] else "FAIL"
        lines.append(
            f"| `{name}` | {status} | {record['metric']:.6e} | "
            f"{record['relation']} {record['threshold']:.6e} |"
        )

    if acceptance["all_checks_passed"]:
        decision = (
            "Stage 02 passes. The projected complete-shell ladder operators are "
            "exact to machine precision, their number operators are positive, the "
            "finite projected commutator structure is correct, the Bohr-frequency "
            "and transverse-Hamiltonian identities hold, and the spin–momentum "
            "operator is reproduced from the same ladder graph, is Hermitian, and "
            "has the required sqrt(omega) scaling. The Cartesian low-mode residuals "
            "show controlled second-order convergence and omega=1/100 collapse under "
            "the Stage-01 scaling."
        )
        next_step = (
            "The next independent stage is detector-free bath certification: trace "
            "preservation, positivity, ground-state stationarity at zero temperature, "
            "occupation relaxation, projected Gibbs stationarity, detailed balance, "
            "coherent-amplitude decay, dephasing invariants, and shell-overflow control."
        )
    else:
        decision = (
            "Stage 02 fails at least one declared operator or convergence gate. "
            "No bath-channel implementation should use these operators until the "
            "failed checks are corrected and the independent loader returns PASS."
        )
        next_step = (
            "Inspect the failed acceptance rows and the solver/loader comparison "
            "before proceeding to detector-free bath certification."
        )

    lines.extend(
        [
            "",
            "## 7. Scientific decision",
            "",
            decision,
            "",
            next_step,
            "",
            "## 8. Reproducibility",
            "",
            f"- Solver SHA-256: `{solver_script_hash}`",
            f"- Loader SHA-256: `{loader_script_hash}`",
        ]
    )
    return "\n".join(lines) + "\n"


# =============================================================================
# Main
# =============================================================================
def main() -> int:
    start_time = time.time()
    out_dir = OUT_ROOT.expanduser().resolve() / RUN_NAME
    if not out_dir.is_dir():
        raise FileNotFoundError(f"Stage-02 output directory does not exist: {out_dir}")
    cleanup_loader_outputs(out_dir)

    required = (
        "Stage02_configuration.json",
        "Stage02_authoritative_operators.npz",
        "Stage02_cartesian_case_metrics.csv",
        "Stage02_cartesian_convergence_metrics.csv",
        "Stage02_cartesian_omega_collapse_metrics.csv",
        "Stage02_acceptance.json",
        "Stage02_solver_audit.json",
        "Stage02_run_status.json",
        "Stage02_output_hashes.json",
        "4050_bath_operator_tests_solver.py",
    )
    require_files(out_dir, required)

    script_path = Path(__file__).resolve()
    loader_script_hash = sha256_file(script_path)
    copied_loader = out_dir / script_path.name
    if script_path != copied_loader.resolve():
        shutil.copy2(script_path, copied_loader)

    try:
        hash_audit = verify_solver_hashes(out_dir)
        if not hash_audit["all_hashes_match"]:
            raise RuntimeError(
                "Solver output hash verification failed: "
                + json.dumps(hash_audit["mismatches"], sort_keys=True)
            )

        config = load_json(out_dir / "Stage02_configuration.json")
        configuration_audit = verify_configuration(config, out_dir)
        solver_acceptance = load_json(out_dir / "Stage02_acceptance.json")
        solver_audit = load_json(out_dir / "Stage02_solver_audit.json")
        solver_run_status = load_json(out_dir / "Stage02_run_status.json")
        if solver_run_status.get("status") not in {"completed", "failed_gate"}:
            raise RuntimeError(
                "Stage02 solver run status is incomplete: "
                f"{solver_run_status.get('status')!r}"
            )

        with np.load(
            out_dir / "Stage02_authoritative_operators.npz", allow_pickle=False
        ) as archive:
            arrays = {name: archive[name] for name in archive.files}

        omega_cases = tuple(float(value) for value in config["omega_cases"])
        grid_sizes = tuple(int(value) for value in config["cartesian_grid_sizes"])
        auth = authoritative_metrics(
            arrays,
            n_shell=int(config["N_shell"]),
            omega_cases=omega_cases,
            hbar=float(config["hbar"]),
            mass=float(config["mass"]),
        )

        cases = [
            independent_cartesian_metrics(
                omega=omega,
                n_grid=n_grid,
                ell=float(config["ell"]),
                hbar=float(config["hbar"]),
                mass=float(config["mass"]),
            )
            for omega in omega_cases
            for n_grid in grid_sizes
        ]
        convergence = independent_convergence_rows(cases, omega_cases)
        omega_rows = independent_omega_rows(cases, omega_cases, grid_sizes)
        acceptance = independent_acceptance(
            auth, cases, convergence, omega_rows, config
        )

        solver_case_rows = read_csv_rows(out_dir / "Stage02_cartesian_case_metrics.csv")
        solver_convergence_rows = read_csv_rows(
            out_dir / "Stage02_cartesian_convergence_metrics.csv"
        )
        solver_omega_rows = read_csv_rows(
            out_dir / "Stage02_cartesian_omega_collapse_metrics.csv"
        )

        case_numeric_fields = tuple(
            field for field in cases[0].keys() if field not in {"omega", "N_grid", "Nx", "Ny"}
        )
        case_csv_comparison = compare_solver_csv(
            solver_case_rows,
            cases,
            key_fields=("omega", "N_grid", "Nx", "Ny"),
            numeric_fields=case_numeric_fields,
        )
        convergence_csv_comparison = compare_solver_csv(
            solver_convergence_rows,
            convergence,
            key_fields=("omega", "metric", "N_coarse", "N_fine"),
            numeric_fields=(
                "eta_coarse",
                "eta_fine",
                "error_coarse",
                "error_fine",
                "observed_order",
            ),
        )
        omega_csv_comparison = compare_solver_csv(
            solver_omega_rows,
            omega_rows,
            key_fields=(
                "N_grid",
                "omega_reference",
                "omega_comparison",
                "metric",
            ),
            numeric_fields=(
                "reference_value",
                "comparison_value",
                "absolute_difference",
            ),
        )
        acceptance_comparison = compare_acceptance(solver_acceptance, acceptance)

        solver_comparison = {
            "acceptance": acceptance_comparison,
            "case_csv": case_csv_comparison,
            "convergence_csv": convergence_csv_comparison,
            "omega_csv": omega_csv_comparison,
            "solver_audit_status": solver_audit.get("status"),
        }
        comparisons_pass = all(
            item["passed"]
            for item in (
                acceptance_comparison,
                case_csv_comparison,
                convergence_csv_comparison,
                omega_csv_comparison,
            )
        )
        final_pass = (
            acceptance["all_checks_passed"]
            and comparisons_pass
            and solver_audit.get("status") == "PASS"
        )

        case_fields = tuple(cases[0].keys())
        atomic_write_csv(
            out_dir / "Stage02_loader_case_metrics.csv", cases, case_fields
        )
        convergence_fields = tuple(convergence[0].keys())
        atomic_write_csv(
            out_dir / "Stage02_loader_convergence_metrics.csv",
            convergence,
            convergence_fields,
        )
        omega_fields = tuple(omega_rows[0].keys())
        atomic_write_csv(
            out_dir / "Stage02_loader_omega_collapse_metrics.csv",
            omega_rows,
            omega_fields,
        )

        solver_script_hash = sha256_file(out_dir / "4050_bath_operator_tests_solver.py")
        report = make_report(
            config=config,
            hash_audit=hash_audit,
            auth=auth,
            cases=cases,
            convergence=convergence,
            omega_rows=omega_rows,
            acceptance=acceptance,
            solver_comparison=solver_comparison,
            solver_script_hash=solver_script_hash,
            loader_script_hash=loader_script_hash,
        )
        atomic_write_text(out_dir / "Stage02_bath_operator_report.md", report)

        elapsed_seconds = time.time() - start_time
        loader_audit = {
            "status": "PASS" if final_pass else "FAIL",
            "completed_utc": utc_now_iso(),
            "elapsed_seconds": elapsed_seconds,
            "stage": STAGE_NAME,
            "script_version": SCRIPT_VERSION,
            "loader_script_sha256": loader_script_hash,
            "solver_script_sha256": solver_script_hash,
            "hash_audit": hash_audit,
            "configuration_audit": configuration_audit,
            "solver_run_status": solver_run_status,
            "authoritative_metrics": auth,
            "independent_acceptance": acceptance,
            "solver_comparison": solver_comparison,
            "all_checks_passed": final_pass,
            "runtime": {
                "python": sys.version,
                "platform": platform.platform(),
                "numpy_version": np.__version__,
            },
        }
        atomic_write_json(out_dir / "Stage02_loader_audit.json", loader_audit)

        loader_stable_names = (
            script_path.name,
            "Stage02_loader_audit.json",
            "Stage02_loader_case_metrics.csv",
            "Stage02_loader_convergence_metrics.csv",
            "Stage02_loader_omega_collapse_metrics.csv",
            "Stage02_bath_operator_report.md",
        )
        hashes = {
            name: sha256_file(out_dir / name) for name in loader_stable_names
        }
        atomic_write_json(
            out_dir / "Stage02_loader_output_hashes.json",
            {
                "generated_utc": utc_now_iso(),
                "hash_algorithm": "SHA-256",
                "stage": STAGE_NAME,
                "files": hashes,
            },
        )

        reference = next(
            case
            for case in cases
            if float(case["omega"]) == float(config["reference_omega"])
            and int(case["N_grid"]) == int(config["reference_grid"])
        )
        print("[Stage-02 independent loader]")
        print(f"  solver hashes verified:              {hash_audit['verified_file_count']}")
        print(f"  authoritative max ladder residual:  {auth['maximum_all_mode_ladder_residual']:.3e}")
        print(f"  authoritative max Bohr residual:    {auth['maximum_bohr_relative_residual']:.3e}")
        print(f"  reference ladder residual:          {reference['maximum_ladder_action_residual']:.6e}")
        print(f"  reference occupation error:         {reference['maximum_occupation_abs_error']:.6e}")
        print(f"  reference CCR residual:              {reference['maximum_ccr_action_residual']:.6e}")
        print(
            "  minimum refinement order:           "
            f"{min(float(row['observed_order']) for row in convergence):.6f}"
        )
        print(
            "  maximum omega-collapse difference:  "
            f"{max(float(row['absolute_difference']) for row in omega_rows):.3e}"
        )
        print(f"  independent acceptance:             {acceptance['status']}")
        print(f"  solver/loader agreement:            {'PASS' if comparisons_pass else 'FAIL'}")
        print(f"  final Stage-02 loader status:       {'PASS' if final_pass else 'FAIL'}")
        print(f"  report:                              {out_dir / 'Stage02_bath_operator_report.md'}")
        return 0 if final_pass else 2

    except Exception as exc:
        failure = {
            "status": "failed",
            "failed_utc": utc_now_iso(),
            "elapsed_seconds": time.time() - start_time,
            "stage": STAGE_NAME,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc(),
        }
        atomic_write_json(out_dir / "Stage02_loader_failure.json", failure)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
