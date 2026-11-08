#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4050_bath_operator_tests_solver.py
==================================
Stage-02 transverse ladder-operator certification for the Part-I open-system
absorbing-boundary programme.

Scope
-----
This stage certifies only the transverse operators that will later define the
trace-preserving ambient oscillator bath.  It contains:

1. an authoritative complete-shell oscillator representation

       I_N = {(n_x,n_y): n_x+n_y <= N_shell},

   with exact projected matrices P_N a_x P_N and P_N a_y P_N;

2. a Cartesian low-mode cross-check using exactly the Stage-01 box scaling,
   endpoint=False grid, sidewall clamp, and |00>, |10>, |01> formulas.

It performs no time propagation and introduces neither a detector nor a bath
master equation.  It does not import, modify, or execute the validated roof
matrix C, scalar/spinor ABC operators, Crank--Nicolson matrices, GMRES solve, or
post-solve boundary clamp.

The authoritative tests include

* all retained lowering actions and all non-top-shell raising actions;
* the projected top-shell action;
* adjoint consistency;
* N_x=a_x^dagger a_x and N_y=a_y^dagger a_y positivity and occupations;
* exact complete-shell commutator defects, including cross-axis defects;
* x/y isotropy;
* the oscillator Bohr relations [H_perp,a_j]=-hbar*omega*a_j;
* the exact ladder/momentum formula, Hermiticity, and sqrt(omega) scaling of
  the projected spin--momentum operator K.

The Cartesian tests include

* a_x|00> ~= 0 and a_y|00> ~= 0;
* a_x|10> ~= |00> and a_y|01> ~= |00>;
* a_x^dagger|00> ~= |10> and a_y^dagger|00> ~= |01>;
* weighted-adjoint consistency, number-operator positivity, occupations,
  commutator actions, x/y isotropy, and lateral-wall leakage;
* fixed N=50,100,200 refinement and omega=1/100 scale-collapse checks.

Directory contract
------------------
The output directory is explicitly fixed:

    4050.Bath_operator_tests

Only the root is selected through OUTDIR.  No timestamped directory and no
parameter-generated directory is created.  Re-running the solver intentionally
replaces only the owned Stage-02 solver products in the same directory and
invalidates stale loader reports.

Typical use
-----------

    OUTDIR=[ARCHIVE_PATH] \
        python 4050_bath_operator_tests_solver.py

The calculation is small and CPU-only.
"""

from __future__ import annotations

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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, Sequence, Tuple

import numpy as np


# =============================================================================
# Explicit frozen configuration -- intentionally not directory-automated
# =============================================================================
STAGE_NAME = "02_bath_operator_tests"
SCRIPT_VERSION = "2026-08-02-bath-operator-tests-solver-v3-audited"
RUN_NAME = "4050.Bath_operator_tests"
OUT_ROOT = Path(os.getenv("OUTDIR", "."))

HBAR = 1.0
MASS = 1.0
ELL = 10.0
N_SHELL = 12
OMEGA_CASES: Tuple[float, ...] = (1.0, 100.0)
CARTESIAN_GRID_SIZES: Tuple[int, ...] = (50, 100, 200)
REFERENCE_OMEGA = 100.0
REFERENCE_GRID = 100

# These fingerprints identify the exact source files reviewed when this stage
# was constructed.  They are provenance records; Stage 02 has no runtime
# dependency on, and does not import, these detector scripts.
REVIEWED_INPUT_SHA256: Dict[str, str] = {
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
STAGE01_ARCHIVE_SHA256 = (
    "f17502b7ec643593c4690aa0c30fb868e0a9853eaca41cc94228a0e32e2379f7"
)

# Exact projected-operator gates.
EXACT_TOL = 1.0e-12
ADJOINT_TOL = 1.0e-12
PSD_TOL = 1.0e-11
ISOTROPY_TOL = 1.0e-12
BOHR_RELATIVE_TOL = 1.0e-12
K_HERMITICITY_TOL = 1.0e-12
K_SCALE_COLLAPSE_TOL = 1.0e-12

# Cartesian cross-check gates.  eta=sqrt(omega)*h=ELL/N, so the centered
# derivative errors are expected to be O(eta^2).  The limits below gate the
# dimensionless coefficients of eta^2 and a directly measured refinement order.
MODE_OVERLAP_TOL = 1.0e-8
WALL_LEAKAGE_TOL = 1.0e-8
CARTESIAN_LADDER_COEFFICIENT_MAX = 0.75
CARTESIAN_OCCUPATION_COEFFICIENT_MAX = 0.50
CARTESIAN_CCR_COEFFICIENT_MAX = 1.25
MIN_SECOND_ORDER_CONVERGENCE = 1.90
OMEGA_COLLAPSE_TOL = 1.0e-12

SOLVER_OWNED_FILES: Tuple[str, ...] = (
    "Stage02_configuration.json",
    "Stage02_authoritative_audit.json",
    "Stage02_authoritative_operators.npz",
    "Stage02_cartesian_case_metrics.csv",
    "Stage02_cartesian_convergence_metrics.csv",
    "Stage02_cartesian_omega_collapse_metrics.csv",
    "Stage02_cartesian_reference_arrays.npz",
    "Stage02_acceptance.json",
    "Stage02_solver_audit.json",
    "Stage02_output_hashes.json",
    "Stage02_run_status.json",
    "Stage02_stdout.txt",
    "Stage02_simulation_log.txt",
    "Stage02_failure.json",
)

# A solver rerun makes these loader products stale; remove them explicitly but
# do not touch unrelated files in the fixed directory.
STALE_LOADER_FILES: Tuple[str, ...] = (
    "4051_bath_operator_tests_loader.py",
    "Stage02_loader_audit.json",
    "Stage02_loader_case_metrics.csv",
    "Stage02_loader_convergence_metrics.csv",
    "Stage02_loader_omega_collapse_metrics.csv",
    "Stage02_bath_operator_report.md",
    "Stage02_loader_output_hashes.json",
)


# =============================================================================
# General utilities
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


def atomic_savez(path: Path, **arrays: np.ndarray) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("wb") as handle:
        np.savez(handle, **arrays)
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
    scale = max(abs(lhs), abs(rhs), 1.0)
    return float(abs(lhs - rhs) / scale)


def relative_matrix_residual(residual: np.ndarray, reference: np.ndarray) -> float:
    denominator = max(frobenius_norm(reference), 1.0)
    return frobenius_norm(residual) / denominator


def bool_record(
    passed: bool, metric: float, threshold: float, relation: str
) -> Dict[str, Any]:
    return {
        "passed": bool(passed),
        "metric": float(metric),
        "threshold": float(threshold),
        "relation": relation,
    }


def cleanup_owned_outputs(out_dir: Path) -> None:
    for name in SOLVER_OWNED_FILES + STALE_LOADER_FILES:
        path = out_dir / name
        if path.is_file() or path.is_symlink():
            path.unlink()


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
# Authoritative complete-shell oscillator representation
# =============================================================================
def complete_shell_labels(n_shell: int) -> Tuple[Tuple[int, int], ...]:
    labels = []
    for total in range(n_shell + 1):
        for nx in range(total + 1):
            labels.append((nx, total - nx))
    return tuple(labels)


def build_projected_ladders(
    labels: Tuple[Tuple[int, int], ...]
) -> Tuple[np.ndarray, np.ndarray, Dict[Tuple[int, int], int]]:
    index = {label: position for position, label in enumerate(labels)}
    dimension = len(labels)
    a_x = np.zeros((dimension, dimension), dtype=np.complex128)
    a_y = np.zeros((dimension, dimension), dtype=np.complex128)

    for column, (nx, ny) in enumerate(labels):
        if nx > 0:
            a_x[index[(nx - 1, ny)], column] = math.sqrt(nx)
        if ny > 0:
            a_y[index[(nx, ny - 1)], column] = math.sqrt(ny)
    return a_x, a_y, index


def basis_vector(
    index: Mapping[Tuple[int, int], int], label: Tuple[int, int]
) -> np.ndarray:
    vector = np.zeros(len(index), dtype=np.complex128)
    vector[index[label]] = 1.0
    return vector


def authoritative_operator_audit() -> Tuple[Dict[str, Any], Dict[str, np.ndarray]]:
    labels = complete_shell_labels(N_SHELL)
    dimension = (N_SHELL + 1) * (N_SHELL + 2) // 2
    if len(labels) != dimension:
        raise RuntimeError("Complete-shell mode count is inconsistent")

    a_x, a_y, index = build_projected_ladders(labels)
    a_x_dagger = a_x.conj().T
    a_y_dagger = a_y.conj().T
    number_x = a_x_dagger @ a_x
    number_y = a_y_dagger @ a_y
    number_perp = number_x + number_y
    identity = np.eye(dimension, dtype=np.complex128)

    e00 = basis_vector(index, (0, 0))
    e10 = basis_vector(index, (1, 0))
    e01 = basis_vector(index, (0, 1))

    low_ladder_residuals = {
        "norm_ax_mode00": vector_norm(a_x @ e00),
        "norm_ay_mode00": vector_norm(a_y @ e00),
        "norm_ax_mode10_minus_mode00": vector_norm(a_x @ e10 - e00),
        "norm_ay_mode01_minus_mode00": vector_norm(a_y @ e01 - e00),
        "norm_ax_dagger_mode00_minus_mode10": vector_norm(
            a_x_dagger @ e00 - e10
        ),
        "norm_ay_dagger_mode00_minus_mode01": vector_norm(
            a_y_dagger @ e00 - e01
        ),
        "norm_ax_mode01": vector_norm(a_x @ e01),
        "norm_ay_mode10": vector_norm(a_y @ e10),
    }

    lowering_residuals = []
    interior_raising_residuals = []
    top_shell_projected_raising_norms = []
    for nx, ny in labels:
        source = basis_vector(index, (nx, ny))
        for axis, occupation, lowering, raising in (
            ("x", nx, a_x, a_x_dagger),
            ("y", ny, a_y, a_y_dagger),
        ):
            expected_lower = np.zeros(dimension, dtype=np.complex128)
            if occupation > 0:
                lower_label = (nx - 1, ny) if axis == "x" else (nx, ny - 1)
                expected_lower = math.sqrt(occupation) * basis_vector(
                    index, lower_label
                )
            lowering_residuals.append(
                vector_norm(lowering @ source - expected_lower)
            )

            if nx + ny < N_SHELL:
                raise_label = (nx + 1, ny) if axis == "x" else (nx, ny + 1)
                expected_raise = math.sqrt(occupation + 1) * basis_vector(
                    index, raise_label
                )
                interior_raising_residuals.append(
                    vector_norm(raising @ source - expected_raise)
                )
            else:
                top_shell_projected_raising_norms.append(
                    vector_norm(raising @ source)
                )

    nx_expected = np.asarray([nx for nx, _ in labels], dtype=np.float64)
    ny_expected = np.asarray([ny for _, ny in labels], dtype=np.float64)
    number_x_expected = np.diag(nx_expected).astype(np.complex128)
    number_y_expected = np.diag(ny_expected).astype(np.complex128)

    occupation_targets = {
        "00": (e00, 0.0, 0.0),
        "10": (e10, 1.0, 0.0),
        "01": (e01, 0.0, 1.0),
    }
    low_occupations: Dict[str, Dict[str, float]] = {}
    for label, (vector, target_x, target_y) in occupation_targets.items():
        nx_value = float(np.vdot(vector, number_x @ vector).real)
        ny_value = float(np.vdot(vector, number_y @ vector).real)
        low_occupations[label] = {
            "Nx": nx_value,
            "Ny": ny_value,
            "Nx_target": target_x,
            "Ny_target": target_y,
            "Nx_abs_error": abs(nx_value - target_x),
            "Ny_abs_error": abs(ny_value - target_y),
        }

    eig_x = np.linalg.eigvalsh(0.5 * (number_x + number_x.conj().T))
    eig_y = np.linalg.eigvalsh(0.5 * (number_y + number_y.conj().T))

    comm_x = a_x @ a_x_dagger - a_x_dagger @ a_x
    comm_y = a_y @ a_y_dagger - a_y_dagger @ a_y
    expected_comm_x = identity.copy()
    expected_comm_y = identity.copy()
    top_shell_indices = []
    interior_indices = []
    for position, (nx, ny) in enumerate(labels):
        if nx + ny == N_SHELL:
            top_shell_indices.append(position)
            expected_comm_x[position, position] -= nx + 1
            expected_comm_y[position, position] -= ny + 1
        else:
            interior_indices.append(position)

    comm_ax_ay = a_x @ a_y - a_y @ a_x
    comm_axdag_aydag = a_x_dagger @ a_y_dagger - a_y_dagger @ a_x_dagger
    comm_ax_aydag = a_x @ a_y_dagger - a_y_dagger @ a_x
    comm_ay_axdag = a_y @ a_x_dagger - a_x_dagger @ a_y
    number_ladder_commutator_residuals = {
        "Nx_ax_plus_ax": number_x @ a_x - a_x @ number_x + a_x,
        "Nx_axdag_minus_axdag": (
            number_x @ a_x_dagger - a_x_dagger @ number_x - a_x_dagger
        ),
        "Ny_ay_plus_ay": number_y @ a_y - a_y @ number_y + a_y,
        "Ny_aydag_minus_aydag": (
            number_y @ a_y_dagger - a_y_dagger @ number_y - a_y_dagger
        ),
        "Nx_ay": number_x @ a_y - a_y @ number_x,
        "Ny_ax": number_y @ a_x - a_x @ number_y,
    }

    # Exact complete-shell cross-axis defect.  It is supported on the upper
    # shell because one order attempts to raise outside P_N while the other
    # lowers first and remains inside.
    expected_comm_ax_aydag = np.zeros_like(identity)
    expected_comm_ay_axdag = np.zeros_like(identity)
    for nx, ny in labels:
        if nx + ny != N_SHELL:
            continue
        column = index[(nx, ny)]
        if nx > 0:
            row = index[(nx - 1, ny + 1)]
            expected_comm_ax_aydag[row, column] = -math.sqrt(nx * (ny + 1))
        if ny > 0:
            row = index[(nx + 1, ny - 1)]
            expected_comm_ay_axdag[row, column] = -math.sqrt(ny * (nx + 1))

    swap = np.zeros_like(identity)
    for column, (nx, ny) in enumerate(labels):
        swap[index[(ny, nx)], column] = 1.0

    rng = np.random.default_rng(20260802)
    pairing_x = []
    pairing_y = []
    for _ in range(8):
        left = rng.normal(size=dimension) + 1j * rng.normal(size=dimension)
        right = rng.normal(size=dimension) + 1j * rng.normal(size=dimension)
        pairing_x.append(
            relative_pairing_defect(
                left,
                right,
                lambda vector: a_x @ vector,
                lambda vector: a_x_dagger @ vector,
                1.0,
            )
        )
        pairing_y.append(
            relative_pairing_defect(
                left,
                right,
                lambda vector: a_y @ vector,
                lambda vector: a_y_dagger @ vector,
                1.0,
            )
        )

    sigma_x = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    sigma_y = np.asarray([[0.0, -1j], [1j, 0.0]], dtype=np.complex128)
    bohr_metrics: Dict[str, Dict[str, float]] = {}
    k_metrics: Dict[str, Dict[str, float]] = {}
    hamiltonians: Dict[str, np.ndarray] = {}
    k_operators: Dict[str, np.ndarray] = {}

    for omega in OMEGA_CASES:
        h_perp = HBAR * omega * (number_perp + identity)
        omega_key = f"omega_{omega:g}".replace(".", "p")
        hamiltonians[f"H_perp_{omega_key}"] = h_perp

        bohr_residuals = {
            "ax": h_perp @ a_x - a_x @ h_perp + HBAR * omega * a_x,
            "ay": h_perp @ a_y - a_y @ h_perp + HBAR * omega * a_y,
            "ax_dagger": (
                h_perp @ a_x_dagger
                - a_x_dagger @ h_perp
                - HBAR * omega * a_x_dagger
            ),
            "ay_dagger": (
                h_perp @ a_y_dagger
                - a_y_dagger @ h_perp
                - HBAR * omega * a_y_dagger
            ),
        }
        bohr_metrics[f"{omega:g}"] = {
            name: relative_matrix_residual(
                residual,
                HBAR
                * omega
                * (a_x if name == "ax" else a_y if name == "ay" else a_x_dagger if name == "ax_dagger" else a_y_dagger),
            )
            for name, residual in bohr_residuals.items()
        }
        bohr_metrics[f"{omega:g}"]["H_perp_formula_max_abs_residual"] = max_abs(
            h_perp - HBAR * omega * (number_x + number_y + identity)
        )

        ell_perp = math.sqrt(HBAR / (MASS * omega))
        k_operator = (
            1j
            / (math.sqrt(2.0) * ell_perp)
            * (
                np.kron(a_y_dagger - a_y, sigma_x)
                - np.kron(a_x_dagger - a_x, sigma_y)
            )
        )
        p_x = (
            1j
            * HBAR
            / (math.sqrt(2.0) * ell_perp)
            * (a_x_dagger - a_x)
        )
        p_y = (
            1j
            * HBAR
            / (math.sqrt(2.0) * ell_perp)
            * (a_y_dagger - a_y)
        )
        k_from_momentum = (
            np.kron(p_y / HBAR, sigma_x)
            - np.kron(p_x / HBAR, sigma_y)
        )
        k_operators[f"K_{omega_key}"] = k_operator
        k_metrics[f"{omega:g}"] = {
            "hermiticity_max_abs_residual": max_abs(
                k_operator - k_operator.conj().T
            ),
            "formula_max_abs_residual": max_abs(
                k_operator - k_from_momentum
            ),
            "frobenius_norm": frobenius_norm(k_operator),
            "frobenius_norm_div_sqrt_omega": (
                frobenius_norm(k_operator) / math.sqrt(omega)
            ),
        }

    base_omega = OMEGA_CASES[0]
    base_key = f"omega_{base_omega:g}".replace(".", "p")
    base_scaled_k = k_operators[f"K_{base_key}"] / math.sqrt(base_omega)
    k_scale_defects = []
    for omega in OMEGA_CASES[1:]:
        key = f"omega_{omega:g}".replace(".", "p")
        scaled = k_operators[f"K_{key}"] / math.sqrt(omega)
        k_scale_defects.append(max_abs(scaled - base_scaled_k))

    all_exact_ladder = max(
        max(low_ladder_residuals.values()),
        max(lowering_residuals, default=0.0),
        max(interior_raising_residuals, default=0.0),
        max(top_shell_projected_raising_norms, default=0.0),
    )

    audit: Dict[str, Any] = {
        "representation": "orthonormal_complete_shell_oscillator_basis",
        "authoritative_for_bath": True,
        "n_shell": N_SHELL,
        "dimension": dimension,
        "mode_order": [[nx, ny] for nx, ny in labels],
        "low_mode_ladder_action_residuals": low_ladder_residuals,
        "all_mode_ladder_actions": {
            "maximum_lowering_residual": max(lowering_residuals, default=0.0),
            "maximum_interior_raising_residual": max(
                interior_raising_residuals, default=0.0
            ),
            "maximum_top_shell_projected_raising_norm": max(
                top_shell_projected_raising_norms, default=0.0
            ),
            "maximum_combined_residual": all_exact_ladder,
        },
        "weighted_adjoint": {
            "weight_matrix": "identity",
            "max_matrix_residual_ax_dagger_minus_ax_adjoint": max_abs(
                a_x_dagger - a_x.conj().T
            ),
            "max_matrix_residual_ay_dagger_minus_ay_adjoint": max_abs(
                a_y_dagger - a_y.conj().T
            ),
            "max_random_pairing_defect_x": max(pairing_x),
            "max_random_pairing_defect_y": max(pairing_y),
        },
        "number_operators": {
            "minimum_eigenvalue_Nx": float(np.min(eig_x)),
            "minimum_eigenvalue_Ny": float(np.min(eig_y)),
            "maximum_abs_Nx_minus_exact_number_diagonal": max_abs(
                number_x - number_x_expected
            ),
            "maximum_abs_Ny_minus_exact_number_diagonal": max_abs(
                number_y - number_y_expected
            ),
            "low_mode_occupations": low_occupations,
        },
        "isotropy": {
            "swap_unitarity_max_abs_residual": max_abs(
                swap.conj().T @ swap - identity
            ),
            "max_abs_swap_ax_swap_dagger_minus_ay": max_abs(
                swap @ a_x @ swap.conj().T - a_y
            ),
            "max_abs_swap_Nx_swap_dagger_minus_Ny": max_abs(
                swap @ number_x @ swap.conj().T - number_y
            ),
        },
        "commutators": {
            "max_abs_comm_x_minus_exact_projected_formula": max_abs(
                comm_x - expected_comm_x
            ),
            "max_abs_comm_y_minus_exact_projected_formula": max_abs(
                comm_y - expected_comm_y
            ),
            "max_abs_comm_ax_ay": max_abs(comm_ax_ay),
            "max_abs_comm_axdag_aydag": max_abs(comm_axdag_aydag),
            "max_abs_comm_ax_aydag_minus_exact_projected_formula": max_abs(
                comm_ax_aydag - expected_comm_ax_aydag
            ),
            "max_abs_comm_ay_axdag_minus_exact_projected_formula": max_abs(
                comm_ay_axdag - expected_comm_ay_axdag
            ),
            "max_abs_number_ladder_commutator_residual": max(
                max_abs(residual)
                for residual in number_ladder_commutator_residuals.values()
            ),
            "trace_comm_x_real": float(np.trace(comm_x).real),
            "trace_comm_y_real": float(np.trace(comm_y).real),
            "trace_identity": float(dimension),
            "top_shell_dimension": len(top_shell_indices),
            "full_space_frobenius_norm_comm_x_minus_identity": frobenius_norm(
                comm_x - identity
            ),
            "full_space_frobenius_norm_comm_y_minus_identity": frobenius_norm(
                comm_y - identity
            ),
            "interpretation": (
                "The full finite-dimensional commutator cannot equal I because "
                "the trace of a commutator is zero.  The saved formulas are the "
                "exact complete-shell P_N a P_N defects."
            ),
        },
        "bohr_relations": bohr_metrics,
        "spin_momentum_operator_K": {
            "per_omega": k_metrics,
            "max_scaled_K_collapse_defect": max(k_scale_defects, default=0.0),
            "basis_order": "transverse complete-shell basis tensor physical spin",
        },
    }

    arrays: Dict[str, np.ndarray] = {
        "mode_labels": np.asarray(labels, dtype=np.int64),
        "a_x": a_x,
        "a_y": a_y,
        "a_x_dagger": a_x_dagger,
        "a_y_dagger": a_y_dagger,
        "N_x": number_x,
        "N_y": number_y,
        "N_perp": number_perp,
        "commutator_x": comm_x,
        "commutator_y": comm_y,
        "expected_commutator_x": expected_comm_x,
        "expected_commutator_y": expected_comm_y,
        "commutator_ax_aydagger": comm_ax_aydag,
        "expected_commutator_ax_aydagger": expected_comm_ax_aydag,
        "commutator_ay_axdagger": comm_ay_axdag,
        "expected_commutator_ay_axdagger": expected_comm_ay_axdag,
        "swap_xy": swap,
        "mode00": e00,
        "mode10": e10,
        "mode01": e01,
    }
    arrays.update(hamiltonians)
    arrays.update(k_operators)
    return audit, arrays


# =============================================================================
# Cartesian Stage-01 low-mode cross-check
# =============================================================================
def centered_dirichlet_derivative(n_interior: int, spacing: float) -> np.ndarray:
    derivative = np.zeros((n_interior, n_interior), dtype=np.float64)
    coefficient = 1.0 / (2.0 * spacing)
    for row in range(n_interior):
        if row > 0:
            derivative[row, row - 1] = -coefficient
        if row < n_interior - 1:
            derivative[row, row + 1] = coefficient
    return derivative


def unique_sidewall_probability_and_max(
    array: np.ndarray, hx: float, hy: float
) -> Tuple[float, float]:
    pieces = (
        array[0, :],
        array[-1, :],
        array[1:-1, 0],
        array[1:-1, -1],
    )
    probability = sum(float(np.sum(np.abs(piece) ** 2)) for piece in pieces)
    probability *= hx * hy
    maximum = max(float(np.max(np.abs(piece))) for piece in pieces)
    return probability, maximum


def cartesian_case(
    omega: float, n_grid: int, *, retain_arrays: bool
) -> Tuple[Dict[str, Any], Dict[str, np.ndarray]]:
    if omega <= 0.0 or not math.isfinite(omega):
        raise ValueError("omega must be finite and positive")
    if n_grid < 8:
        raise ValueError("Cartesian grid must contain at least 8 points")

    lx = ELL / math.sqrt(omega)
    ly = ELL / math.sqrt(omega)
    x = np.linspace(0.0, lx, n_grid, endpoint=False, dtype=np.float64)
    y = np.linspace(0.0, ly, n_grid, endpoint=False, dtype=np.float64)
    hx = float(x[1] - x[0])
    hy = float(y[1] - y[0])
    area_weight = hx * hy

    x_centered = x - lx / 2.0
    y_centered = y - ly / 2.0
    xx, yy = np.meshgrid(x_centered, y_centered, indexing="ij")
    gaussian = np.exp(-omega * (xx * xx + yy * yy) / 2.0)
    raw_modes = {
        "00": gaussian.copy(),
        "10": math.sqrt(2.0 * omega) * xx * gaussian,
        "01": math.sqrt(2.0 * omega) * yy * gaussian,
    }

    unclamped_norm_squared: Dict[str, float] = {}
    wall_node_probability: Dict[str, float] = {}
    wall_node_probability_fraction: Dict[str, float] = {}
    wall_node_max_amplitude_ratio: Dict[str, float] = {}
    normalized_modes: Dict[str, np.ndarray] = {}
    clamped_raw_norm_squared: Dict[str, float] = {}

    for label, raw in raw_modes.items():
        total = float(np.sum(np.abs(raw) ** 2) * area_weight)
        wall_probability, wall_max = unique_sidewall_probability_and_max(
            raw, hx, hy
        )
        unclamped_norm_squared[label] = total
        wall_node_probability[label] = wall_probability
        wall_node_probability_fraction[label] = wall_probability / total
        wall_node_max_amplitude_ratio[label] = wall_max / float(
            np.max(np.abs(raw))
        )

        clamped = raw.copy()
        clamped[[0, -1], :] = 0.0
        clamped[:, [0, -1]] = 0.0
        norm_squared = float(np.sum(np.abs(clamped) ** 2) * area_weight)
        if norm_squared <= 0.0:
            raise RuntimeError(f"Cartesian mode {label} has nonpositive norm")
        clamped_raw_norm_squared[label] = norm_squared
        normalized_modes[label] = clamped / math.sqrt(norm_squared)

    mode_order = ("00", "10", "01")
    overlap = np.empty((3, 3), dtype=np.complex128)
    for row, left in enumerate(mode_order):
        for column, right in enumerate(mode_order):
            overlap[row, column] = weighted_inner(
                normalized_modes[left], normalized_modes[right], area_weight
            )
    offdiagonal = overlap - np.diag(np.diag(overlap))

    x_interior = x_centered[1:-1]
    y_interior = y_centered[1:-1]
    n_interior = n_grid - 2
    derivative_x = centered_dirichlet_derivative(n_interior, hx)
    derivative_y = centered_dirichlet_derivative(n_interior, hy)
    position_x = np.diag(x_interior)
    position_y = np.diag(y_interior)

    alpha = math.sqrt(MASS * omega / (2.0 * HBAR))
    beta = math.sqrt(HBAR / (2.0 * MASS * omega))
    a_x_1d = alpha * position_x + beta * derivative_x
    a_y_1d = alpha * position_y + beta * derivative_y
    a_x_dagger_1d = alpha * position_x - beta * derivative_x
    a_y_dagger_1d = alpha * position_y - beta * derivative_y

    def ax(field: np.ndarray) -> np.ndarray:
        return a_x_1d @ field

    def ax_dagger(field: np.ndarray) -> np.ndarray:
        return a_x_dagger_1d @ field

    def ay(field: np.ndarray) -> np.ndarray:
        return field @ a_y_1d.T

    def ay_dagger(field: np.ndarray) -> np.ndarray:
        return field @ a_y_dagger_1d.T

    interior_modes = {
        label: mode[1:-1, 1:-1].astype(np.complex128, copy=False)
        for label, mode in normalized_modes.items()
    }
    mode00 = interior_modes["00"]
    mode10 = interior_modes["10"]
    mode01 = interior_modes["01"]

    action_fields = {
        "ax_mode00": ax(mode00),
        "ay_mode00": ay(mode00),
        "ax_mode10_minus_mode00": ax(mode10) - mode00,
        "ay_mode01_minus_mode00": ay(mode01) - mode00,
        "ax_dagger_mode00_minus_mode10": ax_dagger(mode00) - mode10,
        "ay_dagger_mode00_minus_mode01": ay_dagger(mode00) - mode01,
        "ax_mode01": ax(mode01),
        "ay_mode10": ay(mode10),
    }
    ladder_residuals = {
        name: weighted_norm(field, area_weight)
        for name, field in action_fields.items()
    }

    number_x_1d = a_x_dagger_1d @ a_x_1d
    number_y_1d = a_y_dagger_1d @ a_y_1d

    def nx_action(field: np.ndarray) -> np.ndarray:
        return number_x_1d @ field

    def ny_action(field: np.ndarray) -> np.ndarray:
        return field @ number_y_1d.T

    targets = {"00": (0.0, 0.0), "10": (1.0, 0.0), "01": (0.0, 1.0)}
    occupations: Dict[str, Dict[str, float]] = {}
    occupation_errors = []
    for label, field in interior_modes.items():
        nx_value = weighted_inner(field, nx_action(field), area_weight).real
        ny_value = weighted_inner(field, ny_action(field), area_weight).real
        error_x = abs(nx_value - targets[label][0])
        error_y = abs(ny_value - targets[label][1])
        occupation_errors.extend((error_x, error_y))
        occupations[label] = {
            "Nx": float(nx_value),
            "Ny": float(ny_value),
            "Nx_target": targets[label][0],
            "Ny_target": targets[label][1],
            "Nx_abs_error": float(error_x),
            "Ny_abs_error": float(error_y),
        }

    eig_x = np.linalg.eigvalsh(0.5 * (number_x_1d + number_x_1d.conj().T))
    eig_y = np.linalg.eigvalsh(0.5 * (number_y_1d + number_y_1d.conj().T))

    comm_x_1d = a_x_1d @ a_x_dagger_1d - a_x_dagger_1d @ a_x_1d
    comm_y_1d = a_y_1d @ a_y_dagger_1d - a_y_dagger_1d @ a_y_1d

    ccr_residuals: Dict[str, Dict[str, float]] = {}
    cross_residuals: Dict[str, Dict[str, float]] = {}
    all_ccr = []
    all_cross = []
    for label, field in interior_modes.items():
        values = {
            "comm_x_minus_I": weighted_norm(
                comm_x_1d @ field - field, area_weight
            ),
            "comm_y_minus_I": weighted_norm(
                field @ comm_y_1d.T - field, area_weight
            ),
        }
        ccr_residuals[label] = values
        all_ccr.extend(values.values())

        cross_values = {
            "comm_ax_ay": weighted_norm(ax(ay(field)) - ay(ax(field)), area_weight),
            "comm_ax_aydagger": weighted_norm(
                ax(ay_dagger(field)) - ay_dagger(ax(field)), area_weight
            ),
            "comm_axdagger_ay": weighted_norm(
                ax_dagger(ay(field)) - ay(ax_dagger(field)), area_weight
            ),
            "comm_axdagger_aydagger": weighted_norm(
                ax_dagger(ay_dagger(field))
                - ay_dagger(ax_dagger(field)),
                area_weight,
            ),
        }
        cross_residuals[label] = cross_values
        all_cross.extend(cross_values.values())

    rng = np.random.default_rng(20260802 + n_grid)
    pairing_x = []
    pairing_y = []
    for _ in range(8):
        left = rng.normal(size=(n_interior, n_interior)) + 1j * rng.normal(
            size=(n_interior, n_interior)
        )
        right = rng.normal(size=(n_interior, n_interior)) + 1j * rng.normal(
            size=(n_interior, n_interior)
        )
        pairing_x.append(
            relative_pairing_defect(left, right, ax, ax_dagger, area_weight)
        )
        pairing_y.append(
            relative_pairing_defect(left, right, ay, ay_dagger, area_weight)
        )

    # Analytic ideal-oscillator probability outside the actual rectangle whose
    # endpoint=False outer nodes are explicitly clamped.  Scaled coordinates
    # make this check directly comparable across omega.
    def ground_tail_right(u: float) -> float:
        return 0.5 * math.erfc(u)

    def first_tail_right(u: float) -> float:
        return 0.5 * math.erfc(u) + (u / math.sqrt(math.pi)) * math.exp(-u * u)

    ux_left = math.sqrt(omega) * x_centered[0]
    ux_right = math.sqrt(omega) * x_centered[-1]
    uy_left = math.sqrt(omega) * y_centered[0]
    uy_right = math.sqrt(omega) * y_centered[-1]

    ground_inside_x = 1.0 - ground_tail_right(-ux_left) - ground_tail_right(ux_right)
    ground_inside_y = 1.0 - ground_tail_right(-uy_left) - ground_tail_right(uy_right)
    first_inside_x = 1.0 - first_tail_right(-ux_left) - first_tail_right(ux_right)
    first_inside_y = 1.0 - first_tail_right(-uy_left) - first_tail_right(uy_right)
    ground_outside = 1.0 - ground_inside_x * ground_inside_y
    mode10_outside = 1.0 - first_inside_x * ground_inside_y
    mode01_outside = 1.0 - ground_inside_x * first_inside_y
    first_shell_outside = max(mode10_outside, mode01_outside)

    eta_x = math.sqrt(omega) * hx
    eta_y = math.sqrt(omega) * hy
    eta = max(eta_x, eta_y)
    eta_squared = eta * eta
    max_ladder = max(ladder_residuals.values())
    max_occupation = max(occupation_errors)
    max_ccr = max(all_ccr)
    max_cross = max(all_cross, default=0.0)
    max_overlap = max(
        float(np.max(np.abs(np.diag(overlap) - 1.0))), max_abs(offdiagonal)
    )
    max_adjoint = max(
        max_abs(a_x_dagger_1d - a_x_1d.conj().T),
        max_abs(a_y_dagger_1d - a_y_1d.conj().T),
        max(pairing_x),
        max(pairing_y),
    )
    min_number_eigenvalue = min(float(np.min(eig_x)), float(np.min(eig_y)))
    max_isotropy = max(
        max_abs(a_x_1d - a_y_1d),
        max_abs(number_x_1d - number_y_1d),
        abs(ladder_residuals["ax_mode00"] - ladder_residuals["ay_mode00"]),
        abs(
            ladder_residuals["ax_mode10_minus_mode00"]
            - ladder_residuals["ay_mode01_minus_mode00"]
        ),
        abs(
            ladder_residuals["ax_dagger_mode00_minus_mode10"]
            - ladder_residuals["ay_dagger_mode00_minus_mode01"]
        ),
    )
    max_wall_metric = max(
        max(wall_node_probability_fraction.values()), first_shell_outside
    )

    summary: Dict[str, Any] = {
        "omega": float(omega),
        "N_grid": int(n_grid),
        "Nx": int(n_grid),
        "Ny": int(n_grid),
        "Lx": float(lx),
        "Ly": float(ly),
        "hx": float(hx),
        "hy": float(hy),
        "eta_sqrtomega_h": float(eta),
        "eta_squared": float(eta_squared),
        "maximum_mode_overlap_defect": float(max_overlap),
        "maximum_weighted_adjoint_defect": float(max_adjoint),
        "minimum_number_operator_eigenvalue": float(min_number_eigenvalue),
        "maximum_ladder_action_residual": float(max_ladder),
        "ladder_error_coefficient_over_eta_squared": float(
            max_ladder / eta_squared
        ),
        "maximum_occupation_abs_error": float(max_occupation),
        "occupation_error_coefficient_over_eta_squared": float(
            max_occupation / eta_squared
        ),
        "maximum_ccr_action_residual": float(max_ccr),
        "ccr_error_coefficient_over_eta_squared": float(max_ccr / eta_squared),
        "maximum_cross_commutator_action_residual": float(max_cross),
        "maximum_xy_isotropy_defect": float(max_isotropy),
        "maximum_wall_node_probability_fraction": float(
            max(wall_node_probability_fraction.values())
        ),
        "analytic_ground_probability_outside_actual_clamped_rectangle": float(
            ground_outside
        ),
        "analytic_mode10_probability_outside_actual_clamped_rectangle": float(
            mode10_outside
        ),
        "analytic_mode01_probability_outside_actual_clamped_rectangle": float(
            mode01_outside
        ),
        "maximum_wall_leakage_metric": float(max_wall_metric),
        "trace_commutator_x": float(np.trace(comm_x_1d).real),
        "trace_commutator_y": float(np.trace(comm_y_1d).real),
        "mode00_Nx": occupations["00"]["Nx"],
        "mode00_Ny": occupations["00"]["Ny"],
        "mode10_Nx": occupations["10"]["Nx"],
        "mode10_Ny": occupations["10"]["Ny"],
        "mode01_Nx": occupations["01"]["Nx"],
        "mode01_Ny": occupations["01"]["Ny"],
    }

    detail: Dict[str, Any] = {
        "representation": "stage01_cartesian_low_mode_cross_check",
        "authoritative_for_bath": False,
        "summary": summary,
        "mode_basis": {
            "mode_order": list(mode_order),
            "unclamped_total_norm_squared": unclamped_norm_squared,
            "raw_norm_squared_after_sidewall_clamp": clamped_raw_norm_squared,
            "normalized_overlap_matrix_real": overlap.real.tolist(),
            "normalized_overlap_matrix_imag": overlap.imag.tolist(),
        },
        "ladder_action_residuals": ladder_residuals,
        "number_occupations": occupations,
        "commutator_action_residuals": ccr_residuals,
        "cross_commutator_action_residuals": cross_residuals,
        "wall_leakage": {
            "raw_boundary_probability": wall_node_probability,
            "raw_boundary_probability_fraction": wall_node_probability_fraction,
            "raw_boundary_max_amplitude_ratio": wall_node_max_amplitude_ratio,
            "scaled_clamped_x_node_coordinates": [ux_left, ux_right],
            "scaled_clamped_y_node_coordinates": [uy_left, uy_right],
            "analytic_ground_probability_outside_actual_clamped_rectangle": ground_outside,
            "analytic_mode10_probability_outside_actual_clamped_rectangle": mode10_outside,
            "analytic_mode01_probability_outside_actual_clamped_rectangle": mode01_outside,
        },
        "interpretation": (
            "The Cartesian operators are a low-mode finite-difference cross-check. "
            "Their canonical commutator is assessed on the low modes and by "
            "second-order refinement; no finite matrix is required to satisfy "
            "[a,a^dagger]=I on its full space."
        ),
    }

    arrays: Dict[str, np.ndarray] = {}
    if retain_arrays:
        arrays = {
            "x": x,
            "y": y,
            "mode00_full_clamped_normalized": normalized_modes["00"],
            "mode10_full_clamped_normalized": normalized_modes["10"],
            "mode01_full_clamped_normalized": normalized_modes["01"],
            "mode_overlap": overlap,
            "a_x_1d": a_x_1d,
            "a_y_1d": a_y_1d,
            "a_x_dagger_1d": a_x_dagger_1d,
            "a_y_dagger_1d": a_y_dagger_1d,
            "N_x_1d": number_x_1d,
            "N_y_1d": number_y_1d,
            "commutator_x_1d": comm_x_1d,
            "commutator_y_1d": comm_y_1d,
        }
        arrays.update(action_fields)
    return {"summary": summary, "detail": detail}, arrays


def convergence_rows(
    case_summaries: Sequence[Mapping[str, Any]]
) -> list[Dict[str, Any]]:
    metrics = (
        "maximum_ladder_action_residual",
        "maximum_occupation_abs_error",
        "maximum_ccr_action_residual",
    )
    rows: list[Dict[str, Any]] = []
    for omega in OMEGA_CASES:
        cases = sorted(
            (row for row in case_summaries if float(row["omega"]) == omega),
            key=lambda row: int(row["N_grid"]),
        )
        for coarse, fine in zip(cases[:-1], cases[1:]):
            h_ratio = float(coarse["eta_sqrtomega_h"]) / float(
                fine["eta_sqrtomega_h"]
            )
            for metric in metrics:
                coarse_error = float(coarse[metric])
                fine_error = float(fine[metric])
                if coarse_error <= 0.0 or fine_error <= 0.0 or h_ratio <= 1.0:
                    order = float("nan")
                else:
                    order = math.log(coarse_error / fine_error) / math.log(h_ratio)
                rows.append(
                    {
                        "omega": omega,
                        "metric": metric,
                        "N_coarse": int(coarse["N_grid"]),
                        "N_fine": int(fine["N_grid"]),
                        "eta_coarse": float(coarse["eta_sqrtomega_h"]),
                        "eta_fine": float(fine["eta_sqrtomega_h"]),
                        "error_coarse": coarse_error,
                        "error_fine": fine_error,
                        "observed_order": order,
                    }
                )
    return rows


def omega_collapse_rows(
    case_summaries: Sequence[Mapping[str, Any]]
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
    rows: list[Dict[str, Any]] = []
    base_omega = OMEGA_CASES[0]
    for n_grid in CARTESIAN_GRID_SIZES:
        by_omega = {
            float(row["omega"]): row
            for row in case_summaries
            if int(row["N_grid"]) == n_grid
        }
        base = by_omega[base_omega]
        for omega in OMEGA_CASES[1:]:
            other = by_omega[omega]
            for metric in metrics:
                base_value = float(base[metric])
                other_value = float(other[metric])
                rows.append(
                    {
                        "N_grid": n_grid,
                        "omega_reference": base_omega,
                        "omega_comparison": omega,
                        "metric": metric,
                        "reference_value": base_value,
                        "comparison_value": other_value,
                        "absolute_difference": abs(other_value - base_value),
                    }
                )
    return rows


# =============================================================================
# Acceptance gate
# =============================================================================
def build_acceptance_gate(
    authoritative: Mapping[str, Any],
    case_summaries: Sequence[Mapping[str, Any]],
    convergence: Sequence[Mapping[str, Any]],
    omega_collapse: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    adjoint = authoritative["weighted_adjoint"]
    number = authoritative["number_operators"]
    isotropy = authoritative["isotropy"]
    comm = authoritative["commutators"]

    auth_ladder = float(
        authoritative["all_mode_ladder_actions"]["maximum_combined_residual"]
    )
    auth_adjoint = max(
        float(adjoint["max_matrix_residual_ax_dagger_minus_ax_adjoint"]),
        float(adjoint["max_matrix_residual_ay_dagger_minus_ay_adjoint"]),
        float(adjoint["max_random_pairing_defect_x"]),
        float(adjoint["max_random_pairing_defect_y"]),
    )
    auth_min_eig = min(
        float(number["minimum_eigenvalue_Nx"]),
        float(number["minimum_eigenvalue_Ny"]),
    )
    auth_number_diag = max(
        float(number["maximum_abs_Nx_minus_exact_number_diagonal"]),
        float(number["maximum_abs_Ny_minus_exact_number_diagonal"]),
    )
    auth_isotropy = max(float(value) for value in isotropy.values())
    auth_comm = max(
        float(comm["max_abs_comm_x_minus_exact_projected_formula"]),
        float(comm["max_abs_comm_y_minus_exact_projected_formula"]),
        float(comm["max_abs_comm_ax_ay"]),
        float(comm["max_abs_comm_axdag_aydag"]),
        float(comm["max_abs_comm_ax_aydag_minus_exact_projected_formula"]),
        float(comm["max_abs_comm_ay_axdag_minus_exact_projected_formula"]),
        float(comm["max_abs_number_ladder_commutator_residual"]),
    )
    auth_bohr = max(
        float(value)
        for per_omega in authoritative["bohr_relations"].values()
        for value in per_omega.values()
    )
    auth_k_hermiticity = max(
        float(per_omega["hermiticity_max_abs_residual"])
        for per_omega in authoritative["spin_momentum_operator_K"][
            "per_omega"
        ].values()
    )
    auth_k_formula = max(
        float(per_omega["formula_max_abs_residual"])
        for per_omega in authoritative["spin_momentum_operator_K"][
            "per_omega"
        ].values()
    )
    auth_k_scale = float(
        authoritative["spin_momentum_operator_K"][
            "max_scaled_K_collapse_defect"
        ]
    )

    max_overlap = max(float(row["maximum_mode_overlap_defect"]) for row in case_summaries)
    max_cart_adjoint = max(
        float(row["maximum_weighted_adjoint_defect"]) for row in case_summaries
    )
    min_cart_eig = min(
        float(row["minimum_number_operator_eigenvalue"]) for row in case_summaries
    )
    max_ladder_coeff = max(
        float(row["ladder_error_coefficient_over_eta_squared"])
        for row in case_summaries
    )
    max_occupation_coeff = max(
        float(row["occupation_error_coefficient_over_eta_squared"])
        for row in case_summaries
    )
    max_ccr_coeff = max(
        float(row["ccr_error_coefficient_over_eta_squared"])
        for row in case_summaries
    )
    max_cross = max(
        float(row["maximum_cross_commutator_action_residual"])
        for row in case_summaries
    )
    max_cart_isotropy = max(
        float(row["maximum_xy_isotropy_defect"]) for row in case_summaries
    )
    max_wall = max(float(row["maximum_wall_leakage_metric"]) for row in case_summaries)
    min_order = min(float(row["observed_order"]) for row in convergence)
    max_omega_collapse = max(
        float(row["absolute_difference"]) for row in omega_collapse
    )

    reference_present = any(
        float(row["omega"]) == REFERENCE_OMEGA
        and int(row["N_grid"]) == REFERENCE_GRID
        for row in case_summaries
    )

    checks: Dict[str, Dict[str, Any]] = {
        "authoritative_all_ladder_actions": bool_record(
            auth_ladder <= EXACT_TOL, auth_ladder, EXACT_TOL, "<="
        ),
        "authoritative_adjoint": bool_record(
            auth_adjoint <= ADJOINT_TOL, auth_adjoint, ADJOINT_TOL, "<="
        ),
        "authoritative_number_positivity": bool_record(
            auth_min_eig >= -PSD_TOL, auth_min_eig, -PSD_TOL, ">="
        ),
        "authoritative_number_diagonal": bool_record(
            auth_number_diag <= EXACT_TOL,
            auth_number_diag,
            EXACT_TOL,
            "<=",
        ),
        "authoritative_xy_isotropy": bool_record(
            auth_isotropy <= ISOTROPY_TOL,
            auth_isotropy,
            ISOTROPY_TOL,
            "<=",
        ),
        "authoritative_projected_commutator_formulas": bool_record(
            auth_comm <= EXACT_TOL, auth_comm, EXACT_TOL, "<="
        ),
        "authoritative_bohr_relations": bool_record(
            auth_bohr <= BOHR_RELATIVE_TOL,
            auth_bohr,
            BOHR_RELATIVE_TOL,
            "<=",
        ),
        "authoritative_K_hermiticity": bool_record(
            auth_k_hermiticity <= K_HERMITICITY_TOL,
            auth_k_hermiticity,
            K_HERMITICITY_TOL,
            "<=",
        ),
        "authoritative_K_formula": bool_record(
            auth_k_formula <= EXACT_TOL,
            auth_k_formula,
            EXACT_TOL,
            "<=",
        ),
        "authoritative_K_sqrtomega_scaling": bool_record(
            auth_k_scale <= K_SCALE_COLLAPSE_TOL,
            auth_k_scale,
            K_SCALE_COLLAPSE_TOL,
            "<=",
        ),
        "cartesian_reference_case_present": bool_record(
            reference_present,
            1.0 if reference_present else 0.0,
            1.0,
            "==",
        ),
        "cartesian_mode_orthonormality": bool_record(
            max_overlap <= MODE_OVERLAP_TOL,
            max_overlap,
            MODE_OVERLAP_TOL,
            "<=",
        ),
        "cartesian_weighted_adjoint": bool_record(
            max_cart_adjoint <= ADJOINT_TOL,
            max_cart_adjoint,
            ADJOINT_TOL,
            "<=",
        ),
        "cartesian_number_positivity": bool_record(
            min_cart_eig >= -PSD_TOL,
            min_cart_eig,
            -PSD_TOL,
            ">=",
        ),
        "cartesian_ladder_O_eta_squared": bool_record(
            max_ladder_coeff <= CARTESIAN_LADDER_COEFFICIENT_MAX,
            max_ladder_coeff,
            CARTESIAN_LADDER_COEFFICIENT_MAX,
            "<=",
        ),
        "cartesian_occupation_O_eta_squared": bool_record(
            max_occupation_coeff <= CARTESIAN_OCCUPATION_COEFFICIENT_MAX,
            max_occupation_coeff,
            CARTESIAN_OCCUPATION_COEFFICIENT_MAX,
            "<=",
        ),
        "cartesian_CCR_O_eta_squared": bool_record(
            max_ccr_coeff <= CARTESIAN_CCR_COEFFICIENT_MAX,
            max_ccr_coeff,
            CARTESIAN_CCR_COEFFICIENT_MAX,
            "<=",
        ),
        "cartesian_second_order_refinement": bool_record(
            min_order >= MIN_SECOND_ORDER_CONVERGENCE,
            min_order,
            MIN_SECOND_ORDER_CONVERGENCE,
            ">=",
        ),
        "cartesian_cross_commutators": bool_record(
            max_cross <= EXACT_TOL, max_cross, EXACT_TOL, "<="
        ),
        "cartesian_xy_isotropy": bool_record(
            max_cart_isotropy <= ISOTROPY_TOL,
            max_cart_isotropy,
            ISOTROPY_TOL,
            "<=",
        ),
        "cartesian_omega_scale_collapse": bool_record(
            max_omega_collapse <= OMEGA_COLLAPSE_TOL,
            max_omega_collapse,
            OMEGA_COLLAPSE_TOL,
            "<=",
        ),
        "cartesian_lateral_wall_leakage": bool_record(
            max_wall <= WALL_LEAKAGE_TOL,
            max_wall,
            WALL_LEAKAGE_TOL,
            "<=",
        ),
    }
    all_passed = all(record["passed"] for record in checks.values())
    return {
        "stage": STAGE_NAME,
        "status": "PASS" if all_passed else "FAIL",
        "all_checks_passed": all_passed,
        "declared_tolerances": {
            "exact": EXACT_TOL,
            "adjoint": ADJOINT_TOL,
            "psd_negative_floor": -PSD_TOL,
            "isotropy": ISOTROPY_TOL,
            "bohr_relative": BOHR_RELATIVE_TOL,
            "K_hermiticity": K_HERMITICITY_TOL,
            "K_scaled_collapse": K_SCALE_COLLAPSE_TOL,
            "mode_overlap": MODE_OVERLAP_TOL,
            "wall_leakage": WALL_LEAKAGE_TOL,
            "cartesian_ladder_coefficient_over_eta_squared": (
                CARTESIAN_LADDER_COEFFICIENT_MAX
            ),
            "cartesian_occupation_coefficient_over_eta_squared": (
                CARTESIAN_OCCUPATION_COEFFICIENT_MAX
            ),
            "cartesian_CCR_coefficient_over_eta_squared": (
                CARTESIAN_CCR_COEFFICIENT_MAX
            ),
            "minimum_second_order_convergence": MIN_SECOND_ORDER_CONVERGENCE,
            "omega_scale_collapse": OMEGA_COLLAPSE_TOL,
        },
        "checks": checks,
        "scope_statement": (
            "A PASS certifies only the transverse ladder/operator layer.  It "
            "does not certify a detector-free Lindblad channel, detector--bath "
            "composition, scalar dynamical null, or environmental susceptibility."
        ),
    }


# =============================================================================
# Main programme
# =============================================================================
def main() -> int:
    start_time = time.time()

    if N_SHELL < 2:
        raise ValueError("N_SHELL must be at least 2")
    if REFERENCE_OMEGA not in OMEGA_CASES:
        raise ValueError("REFERENCE_OMEGA must be contained in OMEGA_CASES")
    if REFERENCE_GRID not in CARTESIAN_GRID_SIZES:
        raise ValueError("REFERENCE_GRID must be contained in CARTESIAN_GRID_SIZES")
    if tuple(sorted(CARTESIAN_GRID_SIZES)) != CARTESIAN_GRID_SIZES:
        raise ValueError("CARTESIAN_GRID_SIZES must be increasing")
    for coarse, fine in zip(CARTESIAN_GRID_SIZES[:-1], CARTESIAN_GRID_SIZES[1:]):
        if fine != 2 * coarse:
            raise ValueError("The fixed convergence suite requires successive grid doubling")

    out_dir = OUT_ROOT.expanduser().resolve() / RUN_NAME
    out_dir.mkdir(parents=True, exist_ok=True)
    cleanup_owned_outputs(out_dir)

    original_stdout = sys.stdout
    stdout_handle = (out_dir / "Stage02_stdout.txt").open("w", encoding="utf-8")
    sys.stdout = Tee(original_stdout, stdout_handle)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(out_dir / "Stage02_simulation_log.txt", mode="w"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )

    script_path = Path(__file__).resolve()
    script_sha256 = sha256_file(script_path)
    copied_script = out_dir / script_path.name
    if script_path != copied_script.resolve():
        shutil.copy2(script_path, copied_script)

    status_path = out_dir / "Stage02_run_status.json"
    status: Dict[str, Any] = {
        "status": "initializing",
        "started_utc": utc_now_iso(),
        "stage": STAGE_NAME,
        "script_version": SCRIPT_VERSION,
        "script_sha256": script_sha256,
        "output_directory": str(out_dir),
    }
    atomic_write_json(status_path, status)

    print("[info] Stage-02 transverse ladder-operator certification")
    print("[info] backend: NumPy CPU, complex128 operator arithmetic")
    print(f"[info] output directory: {out_dir}")
    print(f"[info] complete-shell cutoff: N_shell={N_SHELL}")
    print(f"[info] Cartesian omega cases: {OMEGA_CASES}")
    print(f"[info] Cartesian grids: {CARTESIAN_GRID_SIZES}")
    print(f"[info] script SHA-256: {script_sha256}")
    print("[info] detector/CN/GMRES core: not imported and not modified")

    try:
        fixed_configuration: Dict[str, Any] = {
            "stage": STAGE_NAME,
            "script_version": SCRIPT_VERSION,
            "run_name": RUN_NAME,
            "output_directory_policy": (
                "fixed directory; reused; no timestamp or parameter directory"
            ),
            "hbar": HBAR,
            "mass": MASS,
            "ell": ELL,
            "N_shell": N_SHELL,
            "complete_shell_dimension": (N_SHELL + 1) * (N_SHELL + 2) // 2,
            "omega_cases": list(OMEGA_CASES),
            "cartesian_grid_sizes": list(CARTESIAN_GRID_SIZES),
            "reference_omega": REFERENCE_OMEGA,
            "reference_grid": REFERENCE_GRID,
            "authoritative_representation": "complete_shell_oscillator_basis",
            "cartesian_role": "Stage-01 low-mode cross-check only",
            "detector_core_imported": False,
            "detector_core_modified": False,
            "bath_generator_active": False,
            "time_propagation_active": False,
            "reviewed_input_sha256": REVIEWED_INPUT_SHA256,
            "stage01_archive_sha256": STAGE01_ARCHIVE_SHA256,
            "tolerances": {
                "exact": EXACT_TOL,
                "adjoint": ADJOINT_TOL,
                "psd": PSD_TOL,
                "isotropy": ISOTROPY_TOL,
                "bohr_relative": BOHR_RELATIVE_TOL,
                "K_hermiticity": K_HERMITICITY_TOL,
                "K_scale_collapse": K_SCALE_COLLAPSE_TOL,
                "mode_overlap": MODE_OVERLAP_TOL,
                "wall_leakage": WALL_LEAKAGE_TOL,
                "ladder_coefficient": CARTESIAN_LADDER_COEFFICIENT_MAX,
                "occupation_coefficient": CARTESIAN_OCCUPATION_COEFFICIENT_MAX,
                "CCR_coefficient": CARTESIAN_CCR_COEFFICIENT_MAX,
                "minimum_refinement_order": MIN_SECOND_ORDER_CONVERGENCE,
                "omega_collapse": OMEGA_COLLAPSE_TOL,
            },
            "script_sha256": script_sha256,
        }
        fixed_configuration["physics_configuration_sha256"] = sha256_json(
            fixed_configuration
        )
        full_configuration = dict(fixed_configuration)
        full_configuration["runtime"] = {
            "generated_utc": utc_now_iso(),
            "python": sys.version,
            "platform": platform.platform(),
            "numpy_version": np.__version__,
        }
        full_configuration["configuration_sha256"] = sha256_json(full_configuration)
        atomic_write_json(out_dir / "Stage02_configuration.json", full_configuration)

        status["status"] = "running"
        atomic_write_json(status_path, status)

        authoritative_audit, authoritative_arrays = authoritative_operator_audit()
        atomic_write_json(
            out_dir / "Stage02_authoritative_audit.json", authoritative_audit
        )
        atomic_savez(
            out_dir / "Stage02_authoritative_operators.npz", **authoritative_arrays
        )

        case_summaries: list[Dict[str, Any]] = []
        reference_arrays: Dict[str, np.ndarray] = {}
        reference_detail: Dict[str, Any] | None = None
        for omega in OMEGA_CASES:
            for n_grid in CARTESIAN_GRID_SIZES:
                retain = omega == REFERENCE_OMEGA and n_grid == REFERENCE_GRID
                result, arrays = cartesian_case(omega, n_grid, retain_arrays=retain)
                case_summaries.append(dict(result["summary"]))
                if retain:
                    reference_arrays = arrays
                    reference_detail = result["detail"]

        if reference_detail is None or not reference_arrays:
            raise RuntimeError("Cartesian reference case was not retained")
        reference_arrays["reference_detail_json_utf8"] = np.frombuffer(
            json.dumps(reference_detail, sort_keys=True).encode("utf-8"),
            dtype=np.uint8,
        )
        atomic_savez(
            out_dir / "Stage02_cartesian_reference_arrays.npz", **reference_arrays
        )

        case_fields = (
            "omega",
            "N_grid",
            "Nx",
            "Ny",
            "Lx",
            "Ly",
            "hx",
            "hy",
            "eta_sqrtomega_h",
            "eta_squared",
            "maximum_mode_overlap_defect",
            "maximum_weighted_adjoint_defect",
            "minimum_number_operator_eigenvalue",
            "maximum_ladder_action_residual",
            "ladder_error_coefficient_over_eta_squared",
            "maximum_occupation_abs_error",
            "occupation_error_coefficient_over_eta_squared",
            "maximum_ccr_action_residual",
            "ccr_error_coefficient_over_eta_squared",
            "maximum_cross_commutator_action_residual",
            "maximum_xy_isotropy_defect",
            "maximum_wall_node_probability_fraction",
            "analytic_ground_probability_outside_actual_clamped_rectangle",
            "analytic_mode10_probability_outside_actual_clamped_rectangle",
            "analytic_mode01_probability_outside_actual_clamped_rectangle",
            "maximum_wall_leakage_metric",
            "trace_commutator_x",
            "trace_commutator_y",
            "mode00_Nx",
            "mode00_Ny",
            "mode10_Nx",
            "mode10_Ny",
            "mode01_Nx",
            "mode01_Ny",
        )
        atomic_write_csv(
            out_dir / "Stage02_cartesian_case_metrics.csv",
            case_summaries,
            case_fields,
        )

        convergence = convergence_rows(case_summaries)
        convergence_fields = (
            "omega",
            "metric",
            "N_coarse",
            "N_fine",
            "eta_coarse",
            "eta_fine",
            "error_coarse",
            "error_fine",
            "observed_order",
        )
        atomic_write_csv(
            out_dir / "Stage02_cartesian_convergence_metrics.csv",
            convergence,
            convergence_fields,
        )

        omega_collapse = omega_collapse_rows(case_summaries)
        omega_fields = (
            "N_grid",
            "omega_reference",
            "omega_comparison",
            "metric",
            "reference_value",
            "comparison_value",
            "absolute_difference",
        )
        atomic_write_csv(
            out_dir / "Stage02_cartesian_omega_collapse_metrics.csv",
            omega_collapse,
            omega_fields,
        )

        acceptance = build_acceptance_gate(
            authoritative_audit, case_summaries, convergence, omega_collapse
        )
        atomic_write_json(out_dir / "Stage02_acceptance.json", acceptance)

        elapsed_seconds = time.time() - start_time
        reference_summary = next(
            row
            for row in case_summaries
            if float(row["omega"]) == REFERENCE_OMEGA
            and int(row["N_grid"]) == REFERENCE_GRID
        )
        solver_audit: Dict[str, Any] = {
            "status": acceptance["status"],
            "completed_utc": utc_now_iso(),
            "elapsed_seconds": elapsed_seconds,
            "stage": STAGE_NAME,
            "N_shell": N_SHELL,
            "complete_shell_dimension": authoritative_audit["dimension"],
            "omega_cases": list(OMEGA_CASES),
            "cartesian_grid_sizes": list(CARTESIAN_GRID_SIZES),
            "reference_case": reference_summary,
            "minimum_observed_cartesian_order": min(
                float(row["observed_order"]) for row in convergence
            ),
            "maximum_omega_scale_collapse_difference": max(
                float(row["absolute_difference"]) for row in omega_collapse
            ),
            "acceptance_gate": acceptance,
            "physics_configuration_sha256": fixed_configuration[
                "physics_configuration_sha256"
            ],
            "configuration_sha256": full_configuration["configuration_sha256"],
            "script_sha256": script_sha256,
        }
        atomic_write_json(out_dir / "Stage02_solver_audit.json", solver_audit)

        stable_names = (
            script_path.name,
            "Stage02_configuration.json",
            "Stage02_authoritative_audit.json",
            "Stage02_authoritative_operators.npz",
            "Stage02_cartesian_case_metrics.csv",
            "Stage02_cartesian_convergence_metrics.csv",
            "Stage02_cartesian_omega_collapse_metrics.csv",
            "Stage02_cartesian_reference_arrays.npz",
            "Stage02_acceptance.json",
            "Stage02_solver_audit.json",
        )
        output_hashes: Dict[str, str] = {}
        for name in stable_names:
            path = out_dir / name
            if not path.is_file():
                raise FileNotFoundError(f"Missing expected stable output: {path}")
            output_hashes[name] = sha256_file(path)
        atomic_write_json(
            out_dir / "Stage02_output_hashes.json",
            {
                "generated_utc": utc_now_iso(),
                "hash_algorithm": "SHA-256",
                "stage": STAGE_NAME,
                "files": output_hashes,
            },
        )

        status.update(
            {
                "status": (
                    "completed" if acceptance["all_checks_passed"] else "failed_gate"
                ),
                "completed_utc": utc_now_iso(),
                "elapsed_seconds": elapsed_seconds,
                "all_checks_passed": acceptance["all_checks_passed"],
                "solver_audit_file": "Stage02_solver_audit.json",
                "output_hash_manifest": "Stage02_output_hashes.json",
            }
        )
        atomic_write_json(status_path, status)

        print("\n[authoritative complete-shell audit]")
        print(f"  dimension:                           {authoritative_audit['dimension']}")
        print(
            "  maximum all-mode ladder residual:    "
            f"{authoritative_audit['all_mode_ladder_actions']['maximum_combined_residual']:.3e}"
        )
        print(
            "  maximum projected commutator defect: "
            f"{max(float(acceptance['checks']['authoritative_projected_commutator_formulas']['metric']), 0.0):.3e}"
        )
        print(
            "  maximum Bohr relative residual:      "
            f"{acceptance['checks']['authoritative_bohr_relations']['metric']:.3e}"
        )
        print(
            "  K/sqrt(omega) collapse defect:       "
            f"{acceptance['checks']['authoritative_K_sqrtomega_scaling']['metric']:.3e}"
        )

        print("\n[Cartesian reference cross-check: omega=100, N=100]")
        print(
            "  maximum ladder residual:             "
            f"{float(reference_summary['maximum_ladder_action_residual']):.6e}"
        )
        print(
            "  maximum occupation error:            "
            f"{float(reference_summary['maximum_occupation_abs_error']):.6e}"
        )
        print(
            "  maximum low-mode CCR residual:       "
            f"{float(reference_summary['maximum_ccr_action_residual']):.6e}"
        )
        print(
            "  maximum wall leakage metric:         "
            f"{float(reference_summary['maximum_wall_leakage_metric']):.6e}"
        )
        print(
            "  minimum measured convergence order:  "
            f"{solver_audit['minimum_observed_cartesian_order']:.6f}"
        )
        print(
            "  maximum omega-scale difference:      "
            f"{solver_audit['maximum_omega_scale_collapse_difference']:.3e}"
        )

        print("\n[Stage-02 acceptance gate]")
        for name, record in acceptance["checks"].items():
            label = "PASS" if record["passed"] else "FAIL"
            print(
                f"  {label:4s}  {name}: metric={record['metric']:.6e} "
                f"{record['relation']} {record['threshold']:.6e}"
            )
        print(f"\n[final] Stage-02 solver status: {acceptance['status']}")
        print(f"[info] Total execution time: {elapsed_seconds:.3f} s")
        print(f"[info] All outputs are in: {out_dir}")
        return 0 if acceptance["all_checks_passed"] else 2

    except Exception as exc:
        elapsed_seconds = time.time() - start_time
        failure = {
            "status": "failed",
            "failed_utc": utc_now_iso(),
            "elapsed_seconds": elapsed_seconds,
            "stage": STAGE_NAME,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc(),
        }
        atomic_write_json(out_dir / "Stage02_failure.json", failure)
        status.update(failure)
        atomic_write_json(status_path, status)
        logging.exception("Stage-02 operator certification failed")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
