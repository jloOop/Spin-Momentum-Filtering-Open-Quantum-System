#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_bath_only_fock_test.py
=========================
Stage-03 detector-free projected-bath certification for the Part-I
open-system absorbing-boundary project.

Scientific scope
----------------
This script certifies only the finite transverse oscillator bath. It contains:

    * no longitudinal coordinate;
    * no scalar or spin-coupled absorbing boundary;
    * no roof matrix C;
    * no detector loss or click observable;
    * no Crank--Nicolson or GMRES solve;
    * no Monte Carlo trajectories;
    * no positivity clipping;
    * no trace renormalization.

For every complete-shell cutoff n_x+n_y <= N it constructs independently

    a_j^(N) = P_N a_j P_N,
    N_j^(N) = a_j^(N)† a_j^(N),
    H_perp,N = omega (N_x^(N) + N_y^(N) + I),

in units hbar = m = 1, and propagates the detector-free GKSL equation

    d rho / dt = -i [H_perp,N, rho]
                 + Gamma_down sum_j D[a_j^(N)] rho
                 + Gamma_up   sum_j D[a_j^(N)†] rho
                 + gamma_phi  sum_j D[N_j^(N)] rho.

Density matrices are vectorized in column-major (Fortran) order. The frozen
identity is

    vec(A rho B) = (B^T kron A) vec(rho).

The script implements the authoritative Stage-03 cases B0--B8:

    B0       zero-temperature ground-state stationarity;
    B1x/B1y  one-quantum decay and x/y isotropy;
    B2       thermal heating from |00>;
    B3       thermal relaxation from |20>;
    B4       projected Gibbs stationarity and detailed balance;
    B5       coherent-amplitude decay;
    B6       independent number dephasing;
    B7       isotropic bath-basis invariance;
    B8       cutoff convergence for N = 8, 12, 16.

The finite-cutoff upward intensity is treated exactly:

    r_up^(N) = Gamma_up [<N_perp+2> - (N+2) p_top],
    r_up^omit = Gamma_up (N+2) p_top.

Directory contract
------------------
The output directory is explicit, fixed, and always reused:

    4060.Bath_only_tests

There are no timestamps and no parameter-generated subdirectories. Re-running
this solver replaces the fixed Stage-03 solver products in that same directory.
Only the root is selected by --out-root or OUTDIR.

Run
---

    python 03_bath_only_fock_test.py \
        --out-root [ARCHIVE_PATH]

The fixed output is

    [ARCHIVE_PATH]

Exit status
-----------

    0 : every declared Stage-03 solver gate passes
    2 : propagation completes, but at least one scientific gate fails
    1 : execution or I/O failure

The independent Stage-03 loader is intentionally a separate later script.
"""

from __future__ import annotations

import argparse
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

# Stage 03 is a small sparse-CPU certification. Prevent uncontrolled BLAS
# thread multiplication on login nodes while still respecting any thread count
# explicitly supplied by the user or scheduler.
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
# Frozen Stage-03 configuration
# =============================================================================
STAGE_NAME = "03_bath_only_fock_test"
SCRIPT_VERSION = "2026-08-02-stage03-bath-only-fock-v3-audited"
OUTPUT_DIRECTORY_NAME = "4060.Bath_only_tests"

HBAR = 1.0
MASS = 1.0
OMEGA = 1.0
T_FINAL = 20.0
NUM_OUTPUT_TIMES = 101
SHELL_CUTOFFS: Tuple[int, ...] = (8, 12, 16)
PRODUCTION_SHELL = 12
RNG_SEED = 20260802

GAMMA_ZERO_T = 0.2
GAMMA_DOWN_THERMAL = 0.25
GAMMA_UP_THERMAL = 0.05
GAMMA_NET_THERMAL = GAMMA_DOWN_THERMAL - GAMMA_UP_THERMAL
Q_THERMAL = GAMMA_UP_THERMAL / GAMMA_DOWN_THERMAL
NBAR_ONE_MODE = GAMMA_UP_THERMAL / GAMMA_NET_THERMAL
GAMMA_PHI = 0.2
ALPHA_X = 0.4 + 0.0j
ALPHA_Y = 0.0 + 0.0j

# Provenance only. Stage 03 reconstructs all operators independently and does
# not import the Stage-00/01 detector scripts or Stage-02 source at runtime.
PARENT_STAGE02_SOLVER_SHA256 = (
    "2ed0daf88dca64d33896d42e53d93c1e57b85d7e22391498babd4f7588b273b2"
)
PARENT_STAGE02_LOADER_SHA256 = (
    "398a66b51c21e72216da38ef446c4e0e0012b0c23e2d6114b12b19e54e4bfc0b"
)
REVIEWED_SOURCE_SHA256: Dict[str, str] = {
    "4022_static_mode_library(1).py": (
        "4dc7d26e891b4903c9a697018b169d08d4f3cd847f30cb9dc788dac1cbadc0f5"
    ),
    "4031_static_mode_library(1).py": (
        "eee0326442a7ddde4cc423f63c916810adec6f77202a72817db5f60f384b7dea"
    ),
    "4032_static_mode_library(1).py": (
        "11a7316ed997aa36f271ea47c2f1272dae86606053da6a84df958630e7fbf9b9"
    ),
    "750.Ref(2).py": (
        "8cf2095b2d760a0b702c930fe5690fe762d08ad7c721a8c53b5ed498d1744009"
    ),
    "4002_reference_regression(3).py": (
        "facecb007572b5409d9d1ddb34c874a234f0d70059780551dc2179a7d66d8b48"
    ),
    "NUM_Open_System_PartI_Master_Audit_Stage00_to_Stage02_and_"
    "Next_Workflow_2026-08-02.md": (
        "7bccf00d4e9189bdc8ce7a67d93a4ee6ba56c09cc46ade1ffdfced35532522dd"
    ),
}

# Thresholds are frozen for the final certification run. Values at the 1e-12
# level test algebra and deterministic propagation. The 1e-6 cutoff target is
# a separately declared dynamical-truncation tolerance, not a solver-floor
# tolerance. The coherent-amplitude test also carries an exact projected
# Heisenberg-residual audit, so its finite-cutoff deviation is not hidden by a
# merely empirical threshold.
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


# =============================================================================
# Data structures
# =============================================================================
@dataclass(frozen=True)
class ShellOperators:
    cutoff: int
    omega: float
    labels: Tuple[Tuple[int, int], ...]
    index: Mapping[Tuple[int, int], int]
    annihilation_x: csr_matrix
    annihilation_y: csr_matrix
    creation_x: csr_matrix
    creation_y: csr_matrix
    number_x: csr_matrix
    number_y: csr_matrix
    number_total: csr_matrix
    hamiltonian: csr_matrix
    identity: csr_matrix
    top_projector: csr_matrix
    n_x_values: np.ndarray
    n_y_values: np.ndarray
    shell_values: np.ndarray

    @property
    def dimension(self) -> int:
        return len(self.labels)


@dataclass
class PropagatedCase:
    case_id: str
    description: str
    cutoff: int
    gamma_down: float
    gamma_up: float
    gamma_phi: float
    initial_state_label: str
    times: np.ndarray
    vectors: np.ndarray
    initial_density: np.ndarray
    time_series: Dict[str, np.ndarray]
    metrics: Dict[str, Any]
    final_density: np.ndarray


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


def atomic_savez_compressed(path: Path, **arrays: np.ndarray) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    os.replace(tmp, path)


def output_hash_manifest(out_dir: Path, exclusions: Iterable[str]) -> Dict[str, str]:
    excluded = set(exclusions)
    hashes: Dict[str, str] = {}
    for path in sorted(out_dir.iterdir()):
        if not path.is_file() or path.name in excluded or path.name.endswith(".tmp"):
            continue
        hashes[path.name] = sha256_file(path)
    return hashes


def remove_stale_products(out_dir: Path) -> None:
    names = (
        "Stage03_configuration.json",
        "Stage03_operator_audit.json",
        "Stage03_case_metrics.csv",
        "Stage03_time_series.npz",
        "Stage03_cutoff_metrics.csv",
        "Stage03_acceptance.json",
        "Stage03_solver_audit.json",
        "Stage03_output_hashes.json",
        "Stage03_run_status.json",
        "Stage03_solver_failure.json",
        "solver_stdout.txt",
        "solver_log.txt",
        "Stage03_loader_audit.json",
        "Stage03_loader_case_metrics.csv",
        "Stage03_loader_cutoff_metrics.csv",
        "Stage03_bath_only_report.md",
        "Stage03_loader_output_hashes.json",
        "loader_stdout.txt",
        "loader_log.txt",
        "loader_failure.json",
    )
    for name in names:
        path = out_dir / name
        if path.is_file():
            path.unlink()
    figure_dir = out_dir / "figures"
    if figure_dir.is_dir():
        shutil.rmtree(figure_dir)


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


def frobenius_norm(matrix: np.ndarray) -> float:
    return float(np.linalg.norm(matrix, ord="fro"))


def hermitize(matrix: np.ndarray) -> np.ndarray:
    return 0.5 * (matrix + matrix.conjugate().T)


def trace_distance(left: np.ndarray, right: np.ndarray) -> float:
    difference = hermitize(left - right)
    eigenvalues = linalg.eigvalsh(difference, check_finite=False)
    return 0.5 * float(np.sum(np.abs(eigenvalues), dtype=np.float64))


def vec_f(matrix: np.ndarray) -> np.ndarray:
    return np.asarray(matrix, dtype=np.complex128).reshape(-1, order="F")


def unvec_f(vector: np.ndarray, dimension: int) -> np.ndarray:
    return np.asarray(vector, dtype=np.complex128).reshape(
        (dimension, dimension), order="F"
    )


def relative_norm(difference: np.ndarray, reference: np.ndarray) -> float:
    denominator = float(np.linalg.norm(reference))
    numerator = float(np.linalg.norm(difference))
    return numerator if denominator == 0.0 else numerator / denominator


def finite_float(value: Any, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise FloatingPointError(f"Non-finite value for {name}: {result!r}")
    return result


# =============================================================================
# Complete-shell oscillator operators
# =============================================================================
def complete_shell_labels(cutoff: int) -> Tuple[Tuple[int, int], ...]:
    if cutoff < 0:
        raise ValueError("cutoff must be nonnegative")
    labels: List[Tuple[int, int]] = []
    for shell in range(cutoff + 1):
        # Frozen order: |shell,0>, |shell-1,1>, ..., |0,shell>.
        for n_x in range(shell, -1, -1):
            labels.append((n_x, shell - n_x))
    return tuple(labels)


def build_shell_operators(cutoff: int, omega: float) -> ShellOperators:
    labels = complete_shell_labels(cutoff)
    index = {label: position for position, label in enumerate(labels)}
    dimension = len(labels)

    rows_x: List[int] = []
    cols_x: List[int] = []
    data_x: List[complex] = []
    rows_y: List[int] = []
    cols_y: List[int] = []
    data_y: List[complex] = []

    n_x_values = np.empty(dimension, dtype=np.float64)
    n_y_values = np.empty(dimension, dtype=np.float64)
    shell_values = np.empty(dimension, dtype=np.int64)

    for column, (n_x, n_y) in enumerate(labels):
        n_x_values[column] = float(n_x)
        n_y_values[column] = float(n_y)
        shell_values[column] = n_x + n_y
        if n_x > 0:
            rows_x.append(index[(n_x - 1, n_y)])
            cols_x.append(column)
            data_x.append(math.sqrt(n_x))
        if n_y > 0:
            rows_y.append(index[(n_x, n_y - 1)])
            cols_y.append(column)
            data_y.append(math.sqrt(n_y))

    annihilation_x = csr_matrix(
        (np.asarray(data_x, dtype=np.complex128), (rows_x, cols_x)),
        shape=(dimension, dimension),
        dtype=np.complex128,
    )
    annihilation_y = csr_matrix(
        (np.asarray(data_y, dtype=np.complex128), (rows_y, cols_y)),
        shape=(dimension, dimension),
        dtype=np.complex128,
    )
    creation_x = annihilation_x.getH().tocsr()
    creation_y = annihilation_y.getH().tocsr()
    number_x = (creation_x @ annihilation_x).tocsr()
    number_y = (creation_y @ annihilation_y).tocsr()
    number_total = (number_x + number_y).tocsr()
    identity = sparse.eye(dimension, dtype=np.complex128, format="csr")
    hamiltonian = (HBAR * omega * (number_total + identity)).tocsr()
    top_projector = sparse.diags(
        (shell_values == cutoff).astype(np.complex128), format="csr"
    )

    return ShellOperators(
        cutoff=cutoff,
        omega=omega,
        labels=labels,
        index=index,
        annihilation_x=annihilation_x,
        annihilation_y=annihilation_y,
        creation_x=creation_x,
        creation_y=creation_y,
        number_x=number_x,
        number_y=number_y,
        number_total=number_total,
        hamiltonian=hamiltonian,
        identity=identity,
        top_projector=top_projector,
        n_x_values=n_x_values,
        n_y_values=n_y_values,
        shell_values=shell_values,
    )


def dissipator_superoperator(operator: csr_matrix, identity: csr_matrix) -> csr_matrix:
    gram = (operator.getH() @ operator).tocsr()
    jump = sparse.kron(operator.conjugate(), operator, format="csr")
    left = sparse.kron(identity, gram, format="csr")
    right = sparse.kron(gram.transpose(), identity, format="csr")
    return (jump - 0.5 * left - 0.5 * right).tocsr()


def build_liouvillian(
    operators: ShellOperators,
    gamma_down: float,
    gamma_up: float,
    gamma_phi: float,
) -> csr_matrix:
    for name, value in (
        ("gamma_down", gamma_down),
        ("gamma_up", gamma_up),
        ("gamma_phi", gamma_phi),
    ):
        if not math.isfinite(value) or value < 0.0:
            raise ValueError(f"{name} must be finite and nonnegative")

    identity = operators.identity
    hamiltonian = operators.hamiltonian
    liouvillian = -1j / HBAR * (
        sparse.kron(identity, hamiltonian, format="csr")
        - sparse.kron(hamiltonian.transpose(), identity, format="csr")
    )

    if gamma_down > 0.0:
        liouvillian = liouvillian + gamma_down * (
            dissipator_superoperator(operators.annihilation_x, identity)
            + dissipator_superoperator(operators.annihilation_y, identity)
        )
    if gamma_up > 0.0:
        liouvillian = liouvillian + gamma_up * (
            dissipator_superoperator(operators.creation_x, identity)
            + dissipator_superoperator(operators.creation_y, identity)
        )
    if gamma_phi > 0.0:
        liouvillian = liouvillian + gamma_phi * (
            dissipator_superoperator(operators.number_x, identity)
            + dissipator_superoperator(operators.number_y, identity)
        )

    result = liouvillian.tocsr().astype(np.complex128)
    result.eliminate_zeros()
    return result


def direct_dissipator(operator: csr_matrix, density: np.ndarray) -> np.ndarray:
    left = operator @ density
    jump = left @ operator.getH().toarray()
    gram = (operator.getH() @ operator).toarray()
    return jump - 0.5 * (gram @ density + density @ gram)


def direct_adjoint_dissipator(
    operator: csr_matrix, observable: np.ndarray
) -> np.ndarray:
    """Hilbert--Schmidt adjoint of D[operator] acting on an observable."""
    operator_dense = operator.toarray()
    adjoint_dense = operator.getH().toarray()
    gram = adjoint_dense @ operator_dense
    return (
        adjoint_dense @ observable @ operator_dense
        - 0.5 * (gram @ observable + observable @ gram)
    )


def direct_adjoint_generator_action(
    operators: ShellOperators,
    observable: np.ndarray,
    gamma_down: float,
    gamma_up: float,
    gamma_phi: float,
) -> np.ndarray:
    """Direct Heisenberg-picture action of the projected GKSL generator."""
    hamiltonian = operators.hamiltonian.toarray()
    result = 1j / HBAR * (
        hamiltonian @ observable - observable @ hamiltonian
    )
    if gamma_down > 0.0:
        result = result + gamma_down * (
            direct_adjoint_dissipator(operators.annihilation_x, observable)
            + direct_adjoint_dissipator(operators.annihilation_y, observable)
        )
    if gamma_up > 0.0:
        result = result + gamma_up * (
            direct_adjoint_dissipator(operators.creation_x, observable)
            + direct_adjoint_dissipator(operators.creation_y, observable)
        )
    if gamma_phi > 0.0:
        result = result + gamma_phi * (
            direct_adjoint_dissipator(operators.number_x, observable)
            + direct_adjoint_dissipator(operators.number_y, observable)
        )
    return np.asarray(result, dtype=np.complex128)


def direct_generator_action(
    operators: ShellOperators,
    density: np.ndarray,
    gamma_down: float,
    gamma_up: float,
    gamma_phi: float,
) -> np.ndarray:
    hamiltonian = operators.hamiltonian.toarray()
    result = -1j / HBAR * (hamiltonian @ density - density @ hamiltonian)
    if gamma_down > 0.0:
        result = result + gamma_down * (
            direct_dissipator(operators.annihilation_x, density)
            + direct_dissipator(operators.annihilation_y, density)
        )
    if gamma_up > 0.0:
        result = result + gamma_up * (
            direct_dissipator(operators.creation_x, density)
            + direct_dissipator(operators.creation_y, density)
        )
    if gamma_phi > 0.0:
        result = result + gamma_phi * (
            direct_dissipator(operators.number_x, density)
            + direct_dissipator(operators.number_y, density)
        )
    return np.asarray(result, dtype=np.complex128)


def build_population_generator(
    operators: ShellOperators,
    gamma_down: float,
    gamma_up: float,
) -> csr_matrix:
    """Independent classical population generator for diagonal states.

    The probability vector is a column vector and obeys dp/dt = Q p.
    """
    dimension = operators.dimension
    rows: List[int] = []
    cols: List[int] = []
    data: List[float] = []

    for column, (n_x, n_y) in enumerate(operators.labels):
        total_out = 0.0
        if n_x > 0 and gamma_down > 0.0:
            rate = gamma_down * n_x
            rows.append(operators.index[(n_x - 1, n_y)])
            cols.append(column)
            data.append(rate)
            total_out += rate
        if n_y > 0 and gamma_down > 0.0:
            rate = gamma_down * n_y
            rows.append(operators.index[(n_x, n_y - 1)])
            cols.append(column)
            data.append(rate)
            total_out += rate
        if n_x + n_y < operators.cutoff and gamma_up > 0.0:
            rate_x = gamma_up * (n_x + 1)
            rate_y = gamma_up * (n_y + 1)
            rows.extend((operators.index[(n_x + 1, n_y)], operators.index[(n_x, n_y + 1)]))
            cols.extend((column, column))
            data.extend((rate_x, rate_y))
            total_out += rate_x + rate_y
        rows.append(column)
        cols.append(column)
        data.append(-total_out)

    matrix = csr_matrix(
        (np.asarray(data, dtype=np.float64), (rows, cols)),
        shape=(dimension, dimension),
        dtype=np.float64,
    )
    matrix.eliminate_zeros()
    return matrix


# =============================================================================
# Initial states
# =============================================================================
def basis_density(operators: ShellOperators, n_x: int, n_y: int) -> np.ndarray:
    index = operators.index[(n_x, n_y)]
    density = np.zeros((operators.dimension, operators.dimension), dtype=np.complex128)
    density[index, index] = 1.0
    return density


def projected_gibbs_density(operators: ShellOperators, q: float) -> np.ndarray:
    if not (0.0 <= q < 1.0):
        raise ValueError("q must satisfy 0 <= q < 1")
    weights = np.power(q, operators.shell_values, dtype=np.float64)
    weights /= np.sum(weights, dtype=np.float64)
    return np.diag(weights.astype(np.complex128))


def coherent_density(
    operators: ShellOperators,
    alpha_x: complex,
    alpha_y: complex,
) -> Tuple[np.ndarray, float]:
    coefficients = np.empty(operators.dimension, dtype=np.complex128)
    gaussian = math.exp(-0.5 * (abs(alpha_x) ** 2 + abs(alpha_y) ** 2))
    for index, (n_x, n_y) in enumerate(operators.labels):
        coefficients[index] = (
            gaussian
            * alpha_x**n_x
            * alpha_y**n_y
            / math.sqrt(math.factorial(n_x) * math.factorial(n_y))
        )
    retained_norm = float(np.vdot(coefficients, coefficients).real)
    if retained_norm <= 0.0:
        raise RuntimeError("Projected coherent state has nonpositive norm")
    coefficients /= math.sqrt(retained_norm)
    mean_total = abs(alpha_x) ** 2 + abs(alpha_y) ** 2
    omitted_tail = float(special.gammainc(operators.cutoff + 1, mean_total))
    return np.outer(coefficients, coefficients.conjugate()), omitted_tail


def dephasing_superposition_density(operators: ShellOperators) -> np.ndarray:
    vector = np.zeros(operators.dimension, dtype=np.complex128)
    vector[operators.index[(0, 0)]] = 1.0 / math.sqrt(2.0)
    vector[operators.index[(1, 0)]] = 1.0 / math.sqrt(2.0)
    return np.outer(vector, vector.conjugate())


# =============================================================================
# Propagation and diagnostics
# =============================================================================
def propagate_many(
    liouvillian: csr_matrix,
    initial_densities: Sequence[np.ndarray],
    times: np.ndarray,
) -> np.ndarray:
    if times.ndim != 1 or times.size < 2:
        raise ValueError("times must be a one-dimensional array with at least two points")
    spacing = np.diff(times)
    if not np.allclose(spacing, spacing[0], rtol=0.0, atol=1.0e-14):
        raise ValueError("expm_multiply certification grid must be equally spaced")
    columns = np.column_stack([vec_f(density) for density in initial_densities])
    propagated = expm_multiply(
        liouvillian,
        columns,
        start=float(times[0]),
        stop=float(times[-1]),
        num=int(times.size),
        endpoint=True,
    )
    propagated = np.asarray(propagated, dtype=np.complex128)
    if propagated.ndim == 2:
        propagated = propagated[:, :, np.newaxis]
    if propagated.shape != (times.size, liouvillian.shape[0], len(initial_densities)):
        raise RuntimeError(
            "Unexpected expm_multiply output shape: "
            f"{propagated.shape!r}"
        )
    return np.transpose(propagated, (2, 0, 1)).copy()


def propagate_populations(
    generator: csr_matrix,
    initial_population: np.ndarray,
    times: np.ndarray,
) -> np.ndarray:
    result = expm_multiply(
        generator,
        np.asarray(initial_population, dtype=np.float64),
        start=float(times[0]),
        stop=float(times[-1]),
        num=int(times.size),
        endpoint=True,
    )
    result = np.asarray(result, dtype=np.float64)
    if result.shape != (times.size, generator.shape[0]):
        raise RuntimeError(f"Unexpected population output shape: {result.shape!r}")
    return result


def expectation_dense(operator: np.ndarray, density: np.ndarray) -> complex:
    """Return Tr(operator @ density) without forming the dense product."""
    return complex(np.einsum("ij,ji->", operator, density, optimize=False))


def analyze_propagated_case(
    *,
    case_id: str,
    description: str,
    operators: ShellOperators,
    vectors: np.ndarray,
    times: np.ndarray,
    initial_density: np.ndarray,
    gamma_down: float,
    gamma_up: float,
    gamma_phi: float,
    initial_state_label: str,
    population_reference: np.ndarray | None = None,
    infinite_occupation_reference: np.ndarray | None = None,
    trace_distance_reference: np.ndarray | None = None,
) -> PropagatedCase:
    dimension = operators.dimension
    if vectors.shape != (times.size, dimension * dimension):
        raise ValueError(
            f"{case_id}: vectors have shape {vectors.shape}, expected "
            f"{(times.size, dimension * dimension)}"
        )

    ax = operators.annihilation_x.toarray()
    ay = operators.annihilation_y.toarray()
    nx = operators.number_x.toarray()
    ny = operators.number_y.toarray()
    ntotal = operators.number_total.toarray()
    hamiltonian = operators.hamiltonian.toarray()
    top = operators.top_projector.toarray()
    upward_gram = (
        operators.annihilation_x @ operators.creation_x
        + operators.annihilation_y @ operators.creation_y
    ).toarray()

    trace_values = np.empty(times.size, dtype=np.complex128)
    hermiticity_fro = np.empty(times.size, dtype=np.float64)
    minimum_eigenvalue = np.empty(times.size, dtype=np.float64)
    occupation_x = np.empty(times.size, dtype=np.float64)
    occupation_y = np.empty(times.size, dtype=np.float64)
    occupation_total = np.empty(times.size, dtype=np.float64)
    energy = np.empty(times.size, dtype=np.float64)
    purity = np.empty(times.size, dtype=np.float64)
    amplitude_x = np.empty(times.size, dtype=np.complex128)
    amplitude_y = np.empty(times.size, dtype=np.complex128)
    top_population = np.empty(times.size, dtype=np.float64)
    downward_intensity = np.empty(times.size, dtype=np.float64)
    upward_intensity = np.empty(times.size, dtype=np.float64)
    upward_intensity_formula = np.empty(times.size, dtype=np.float64)
    omitted_upward_intensity = np.empty(times.size, dtype=np.float64)
    offdiagonal_fro = np.empty(times.size, dtype=np.float64)

    population_reference_l1 = (
        np.empty(times.size, dtype=np.float64)
        if population_reference is not None
        else None
    )
    population_reference_max = (
        np.empty(times.size, dtype=np.float64)
        if population_reference is not None
        else None
    )
    projected_reference_occupation = (
        np.empty(times.size, dtype=np.float64)
        if population_reference is not None
        else None
    )
    reference_trace_distance = (
        np.empty(times.size, dtype=np.float64)
        if trace_distance_reference is not None
        else None
    )

    final_density = np.empty((dimension, dimension), dtype=np.complex128)
    selected_indices = {
        label: operators.index[label]
        for label in ((0, 0), (1, 0), (0, 1), (2, 0), (1, 1))
        if label in operators.index
    }
    selected_populations: Dict[Tuple[int, int], np.ndarray] = {
        label: np.empty(times.size, dtype=np.float64) for label in selected_indices
    }
    coherence_00_10 = (
        np.empty(times.size, dtype=np.complex128)
        if (0, 0) in selected_indices and (1, 0) in selected_indices
        else None
    )

    for time_index, vector in enumerate(vectors):
        density = unvec_f(vector, dimension)
        density_h = hermitize(density)
        if time_index == times.size - 1:
            final_density[:, :] = density

        trace_values[time_index] = np.trace(density)
        hermiticity_fro[time_index] = frobenius_norm(
            density - density.conjugate().T
        )
        minimum_eigenvalue[time_index] = float(
            linalg.eigvalsh(
                density_h,
                subset_by_index=(0, 0),
                check_finite=False,
            )[0]
        )
        occupation_x[time_index] = float(expectation_dense(nx, density).real)
        occupation_y[time_index] = float(expectation_dense(ny, density).real)
        occupation_total[time_index] = float(expectation_dense(ntotal, density).real)
        energy[time_index] = float(expectation_dense(hamiltonian, density).real)
        purity[time_index] = float(np.vdot(density_h, density_h).real)
        amplitude_x[time_index] = expectation_dense(ax, density)
        amplitude_y[time_index] = expectation_dense(ay, density)
        top_population[time_index] = float(expectation_dense(top, density).real)
        downward_intensity[time_index] = gamma_down * occupation_total[time_index]
        upward_intensity[time_index] = gamma_up * float(
            expectation_dense(upward_gram, density).real
        )
        upward_intensity_formula[time_index] = gamma_up * (
            occupation_total[time_index]
            + 2.0 * trace_values[time_index].real
            - (operators.cutoff + 2.0) * top_population[time_index]
        )
        omitted_upward_intensity[time_index] = (
            gamma_up * (operators.cutoff + 2.0) * top_population[time_index]
        )
        diagonal_values = np.diag(density)
        offdiagonal_squared = float(
            np.vdot(density, density).real
            - np.vdot(diagonal_values, diagonal_values).real
        )
        offdiagonal_fro[time_index] = math.sqrt(max(0.0, offdiagonal_squared))

        population = np.real(diagonal_values)
        if population_reference is not None:
            difference = population - population_reference[time_index]
            population_reference_l1[time_index] = float(
                np.sum(np.abs(difference), dtype=np.float64)
            )
            population_reference_max[time_index] = float(np.max(np.abs(difference)))
            projected_reference_occupation[time_index] = float(
                np.dot(operators.shell_values, population_reference[time_index])
            )
        if trace_distance_reference is not None:
            reference_trace_distance[time_index] = trace_distance(
                density_h, trace_distance_reference
            )
        for label, index in selected_indices.items():
            selected_populations[label][time_index] = float(density[index, index].real)
        if coherence_00_10 is not None:
            coherence_00_10[time_index] = density[
                selected_indices[(0, 0)], selected_indices[(1, 0)]
            ]

    overflow = cumulative_trapezoid(
        omitted_upward_intensity, times, initial=0.0
    ).astype(np.float64)
    amplitude_event_intensity = downward_intensity + upward_intensity
    projected_intensity_formula_error = np.abs(
        upward_intensity - upward_intensity_formula
    )

    time_series: Dict[str, np.ndarray] = {
        "t": times.copy(),
        "trace": trace_values,
        "hermiticity_fro": hermiticity_fro,
        "minimum_eigenvalue": minimum_eigenvalue,
        "occupation_x": occupation_x,
        "occupation_y": occupation_y,
        "occupation_total": occupation_total,
        "energy": energy,
        "purity": purity,
        "amplitude_x": amplitude_x,
        "amplitude_y": amplitude_y,
        "top_shell_population": top_population,
        "downward_event_intensity": downward_intensity,
        "upward_event_intensity_projected": upward_intensity,
        "upward_event_intensity_formula": upward_intensity_formula,
        "amplitude_event_intensity_projected": amplitude_event_intensity,
        "upward_event_intensity_omitted": omitted_upward_intensity,
        "overflow_budget": overflow,
        "offdiagonal_fro": offdiagonal_fro,
        "projected_intensity_formula_error": projected_intensity_formula_error,
    }
    if population_reference_l1 is not None:
        time_series["population_reference_l1"] = population_reference_l1
        time_series["population_reference_max"] = population_reference_max
        time_series["projected_reference_occupation"] = projected_reference_occupation
    if infinite_occupation_reference is not None:
        infinite_error = np.abs(occupation_total - infinite_occupation_reference)
        conservative_bound = (
            (operators.cutoff + 2.0) * overflow
            + ACCEPTANCE_THRESHOLDS["infinite_law_bound_slack"]
        )
        time_series["infinite_occupation_reference"] = (
            infinite_occupation_reference.copy()
        )
        time_series["infinite_occupation_error"] = infinite_error
        time_series["infinite_occupation_conservative_bound"] = conservative_bound
        time_series["infinite_occupation_bound_excess"] = (
            infinite_error - conservative_bound
        )
    if reference_trace_distance is not None:
        time_series["trace_distance_reference"] = reference_trace_distance
    for label, values in selected_populations.items():
        time_series[f"population_{label[0]}{label[1]}"] = values
    if coherence_00_10 is not None:
        time_series["coherence_00_10"] = coherence_00_10

    metrics: Dict[str, Any] = {
        "case_id": case_id,
        "description": description,
        "cutoff": operators.cutoff,
        "dimension": operators.dimension,
        "omega": operators.omega,
        "gamma_down": gamma_down,
        "gamma_up": gamma_up,
        "gamma_phi": gamma_phi,
        "gamma_net": gamma_down - gamma_up,
        "initial_state": initial_state_label,
        "T_final": float(times[-1]),
        "number_of_output_times": int(times.size),
        "maximum_trace_error": float(np.max(np.abs(trace_values - 1.0))),
        "maximum_trace_imaginary_part": float(np.max(np.abs(trace_values.imag))),
        "maximum_hermiticity_fro": float(np.max(hermiticity_fro)),
        "minimum_eigenvalue": float(np.min(minimum_eigenvalue)),
        "maximum_top_shell_population": float(np.max(top_population)),
        "final_top_shell_population": float(top_population[-1]),
        "maximum_omitted_upward_intensity": float(
            np.max(np.abs(omitted_upward_intensity))
        ),
        "final_overflow_budget": float(overflow[-1]),
        "maximum_projected_intensity_formula_error": float(
            np.max(projected_intensity_formula_error)
        ),
        "maximum_offdiagonal_fro": float(np.max(offdiagonal_fro)),
        "initial_occupation_total": float(occupation_total[0]),
        "final_occupation_total": float(occupation_total[-1]),
        "initial_purity": float(purity[0]),
        "final_purity": float(purity[-1]),
    }
    if population_reference_l1 is not None:
        metrics["maximum_population_reference_l1"] = float(
            np.max(population_reference_l1)
        )
        metrics["maximum_population_reference_entry_error"] = float(
            np.max(population_reference_max)
        )
        metrics["maximum_projected_occupation_reference_error"] = float(
            np.max(np.abs(occupation_total - projected_reference_occupation))
        )
    if infinite_occupation_reference is not None:
        metrics["maximum_infinite_occupation_error"] = float(
            np.max(time_series["infinite_occupation_error"])
        )
        metrics["maximum_infinite_occupation_bound_excess"] = float(
            np.max(time_series["infinite_occupation_bound_excess"])
        )
    if reference_trace_distance is not None:
        metrics["maximum_trace_distance_reference"] = float(
            np.max(reference_trace_distance)
        )

    return PropagatedCase(
        case_id=case_id,
        description=description,
        cutoff=operators.cutoff,
        gamma_down=gamma_down,
        gamma_up=gamma_up,
        gamma_phi=gamma_phi,
        initial_state_label=initial_state_label,
        times=times.copy(),
        vectors=vectors,
        initial_density=initial_density.copy(),
        time_series=time_series,
        metrics=metrics,
        final_density=final_density.copy(),
    )


# =============================================================================
# Operator certification
# =============================================================================
def random_hermitian(dimension: int, rng: np.random.Generator) -> np.ndarray:
    raw = rng.normal(size=(dimension, dimension)) + 1j * rng.normal(
        size=(dimension, dimension)
    )
    matrix = hermitize(raw)
    norm = frobenius_norm(matrix)
    if norm == 0.0:
        raise RuntimeError("Random Hermitian test matrix has zero norm")
    return matrix / norm


def certify_operators(
    operators_by_cutoff: Mapping[int, ShellOperators],
    rng: np.random.Generator,
) -> Dict[str, Any]:
    per_cutoff: Dict[str, Dict[str, Any]] = {}
    maxima: Dict[str, float] = {
        "number_diagonal_error": 0.0,
        "hamiltonian_diagonal_error": 0.0,
        "bohr_relation_error": 0.0,
        "top_shell_upward_identity_error": 0.0,
        "liouvillian_trace_row_error": 0.0,
        "vectorization_action_relative_error": 0.0,
        "hermiticity_action_relative_error": 0.0,
    }

    for cutoff, operators in operators_by_cutoff.items():
        dimension = operators.dimension
        expected_dimension = (cutoff + 1) * (cutoff + 2) // 2
        if dimension != expected_dimension:
            raise RuntimeError(
                f"N={cutoff}: dimension {dimension}, expected {expected_dimension}"
            )

        nx_dense = operators.number_x.toarray()
        ny_dense = operators.number_y.toarray()
        nt_dense = operators.number_total.toarray()
        h_dense = operators.hamiltonian.toarray()
        expected_nx = np.diag(operators.n_x_values.astype(np.complex128))
        expected_ny = np.diag(operators.n_y_values.astype(np.complex128))
        expected_h = np.diag(
            (operators.omega * (operators.shell_values + 1)).astype(np.complex128)
        )

        number_diagonal_error = max(
            float(np.max(np.abs(nx_dense - expected_nx))),
            float(np.max(np.abs(ny_dense - expected_ny))),
        )
        hamiltonian_diagonal_error = float(np.max(np.abs(h_dense - expected_h)))
        bohr_relation_error = max(
            float(
                np.max(
                    np.abs(
                        (operators.hamiltonian @ operators.annihilation_x
                         - operators.annihilation_x @ operators.hamiltonian).toarray()
                        + operators.omega * operators.annihilation_x.toarray()
                    )
                )
            ),
            float(
                np.max(
                    np.abs(
                        (operators.hamiltonian @ operators.annihilation_y
                         - operators.annihilation_y @ operators.hamiltonian).toarray()
                        + operators.omega * operators.annihilation_y.toarray()
                    )
                )
            ),
            float(
                np.max(
                    np.abs(
                        (operators.hamiltonian @ operators.creation_x
                         - operators.creation_x @ operators.hamiltonian).toarray()
                        - operators.omega * operators.creation_x.toarray()
                    )
                )
            ),
            float(
                np.max(
                    np.abs(
                        (operators.hamiltonian @ operators.creation_y
                         - operators.creation_y @ operators.hamiltonian).toarray()
                        - operators.omega * operators.creation_y.toarray()
                    )
                )
            ),
        )

        upward_gram = (
            operators.annihilation_x @ operators.creation_x
            + operators.annihilation_y @ operators.creation_y
        ).tocsr()
        expected_upward_gram = (
            operators.number_total
            + 2.0 * operators.identity
            - (cutoff + 2.0) * operators.top_projector
        ).tocsr()
        top_shell_identity_error = float(
            np.max(np.abs((upward_gram - expected_upward_gram).toarray()))
        )

        audit_rates = (0.25, 0.05, 0.2)
        liouvillian = build_liouvillian(operators, *audit_rates)
        trace_vector = vec_f(np.eye(dimension, dtype=np.complex128))
        trace_row = liouvillian.transpose() @ trace_vector
        trace_row_error = float(np.max(np.abs(trace_row)))

        test_density = random_hermitian(dimension, rng)
        direct = direct_generator_action(operators, test_density, *audit_rates)
        vectorized = unvec_f(liouvillian @ vec_f(test_density), dimension)
        vectorization_error = relative_norm(vectorized - direct, direct)
        hermiticity_action_error = relative_norm(
            vectorized - vectorized.conjugate().T,
            vectorized,
        )

        values = {
            "cutoff": cutoff,
            "dimension": dimension,
            "liouville_dimension": dimension * dimension,
            "annihilation_x_nnz": int(operators.annihilation_x.nnz),
            "annihilation_y_nnz": int(operators.annihilation_y.nnz),
            "audit_liouvillian_nnz": int(liouvillian.nnz),
            "number_diagonal_error": number_diagonal_error,
            "hamiltonian_diagonal_error": hamiltonian_diagonal_error,
            "bohr_relation_error": bohr_relation_error,
            "top_shell_upward_identity_error": top_shell_identity_error,
            "liouvillian_trace_row_error": trace_row_error,
            "vectorization_action_relative_error": vectorization_error,
            "hermiticity_action_relative_error": hermiticity_action_error,
            "basis_order": "shell ascending, n_x descending within each shell",
            "density_vectorization": "column-major order='F'",
        }
        per_cutoff[str(cutoff)] = values

        maxima["number_diagonal_error"] = max(
            maxima["number_diagonal_error"], number_diagonal_error
        )
        maxima["hamiltonian_diagonal_error"] = max(
            maxima["hamiltonian_diagonal_error"], hamiltonian_diagonal_error
        )
        maxima["bohr_relation_error"] = max(
            maxima["bohr_relation_error"], bohr_relation_error
        )
        maxima["top_shell_upward_identity_error"] = max(
            maxima["top_shell_upward_identity_error"], top_shell_identity_error
        )
        maxima["liouvillian_trace_row_error"] = max(
            maxima["liouvillian_trace_row_error"], trace_row_error
        )
        maxima["vectorization_action_relative_error"] = max(
            maxima["vectorization_action_relative_error"], vectorization_error
        )
        maxima["hermiticity_action_relative_error"] = max(
            maxima["hermiticity_action_relative_error"], hermiticity_action_error
        )

    return {
        "stage": STAGE_NAME,
        "script_version": SCRIPT_VERSION,
        "per_cutoff": per_cutoff,
        "maximum_defects": maxima,
        "scientific_scope": (
            "Independent complete-shell oscillator and Liouvillian certification; "
            "no detector operator is constructed or propagated."
        ),
    }


# =============================================================================
# Case-specific certifications
# =============================================================================
def apply_dissipator_sum(
    operators: Sequence[csr_matrix], density: np.ndarray
) -> np.ndarray:
    result = np.zeros_like(density, dtype=np.complex128)
    for operator in operators:
        result += direct_dissipator(operator, density)
    return result


def random_unitary_2(rng: np.random.Generator) -> np.ndarray:
    raw = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
    q_matrix, r_matrix = np.linalg.qr(raw)
    diagonal = np.diag(r_matrix)
    phases = np.ones(2, dtype=np.complex128)
    nonzero = np.abs(diagonal) > 0.0
    phases[nonzero] = diagonal[nonzero] / np.abs(diagonal[nonzero])
    return q_matrix @ np.diag(phases.conjugate())


def certify_isotropic_basis_invariance(
    operators: ShellOperators,
    rng: np.random.Generator,
    unitary_count: int = 5,
    matrix_count: int = 5,
) -> Dict[str, Any]:
    annihilation_reference = (
        operators.annihilation_x,
        operators.annihilation_y,
    )
    creation_reference = (
        operators.creation_x,
        operators.creation_y,
    )
    max_annihilation_relative = 0.0
    max_creation_relative = 0.0
    raw_records: List[Dict[str, Any]] = []

    for unitary_index in range(unitary_count):
        unitary = random_unitary_2(rng)
        rotated_annihilation = tuple(
            (
                unitary[row, 0] * operators.annihilation_x
                + unitary[row, 1] * operators.annihilation_y
            ).tocsr()
            for row in range(2)
        )
        rotated_creation = tuple(operator.getH().tocsr() for operator in rotated_annihilation)

        for matrix_index in range(matrix_count):
            density = random_hermitian(operators.dimension, rng)
            reference_down = apply_dissipator_sum(annihilation_reference, density)
            rotated_down = apply_dissipator_sum(rotated_annihilation, density)
            reference_up = apply_dissipator_sum(creation_reference, density)
            rotated_up = apply_dissipator_sum(rotated_creation, density)
            relative_down = relative_norm(rotated_down - reference_down, reference_down)
            relative_up = relative_norm(rotated_up - reference_up, reference_up)
            max_annihilation_relative = max(max_annihilation_relative, relative_down)
            max_creation_relative = max(max_creation_relative, relative_up)
            raw_records.append(
                {
                    "unitary_index": unitary_index,
                    "matrix_index": matrix_index,
                    "annihilation_relative_action_defect": relative_down,
                    "creation_relative_action_defect": relative_up,
                }
            )

    return {
        "case_id": "B7",
        "description": "isotropic bath-basis invariance",
        "cutoff": operators.cutoff,
        "dimension": operators.dimension,
        "unitary_count": unitary_count,
        "matrix_count_per_unitary": matrix_count,
        "maximum_annihilation_relative_action_defect": max_annihilation_relative,
        "maximum_creation_relative_action_defect": max_creation_relative,
        "raw_records": raw_records,
    }


def add_case_specific_metrics(
    case: PropagatedCase,
    operators: ShellOperators,
    *,
    kind: str,
    coherent_tail: float | None = None,
    gibbs_generator_residual: float | None = None,
    detailed_balance_relative: float | None = None,
) -> None:
    series = case.time_series
    metrics = case.metrics
    times = case.times

    if kind == "ground_stationary":
        metrics["ground_stationarity_trace_distance_max"] = float(
            np.max(series["trace_distance_reference"])
        )
    elif kind == "one_quantum":
        reference = np.exp(-GAMMA_ZERO_T * times)
        error = np.abs(series["occupation_total"] - reference)
        series["one_quantum_occupation_reference"] = reference
        series["one_quantum_occupation_error"] = error
        metrics["maximum_one_quantum_occupation_error"] = float(np.max(error))
    elif kind == "gibbs":
        if gibbs_generator_residual is None or detailed_balance_relative is None:
            raise ValueError("Gibbs metrics require generator and balance inputs")
        metrics["gibbs_generator_residual_fro"] = gibbs_generator_residual
        metrics["detailed_balance_relative_error"] = detailed_balance_relative
        metrics["gibbs_stationarity_trace_distance_max"] = float(
            np.max(series["trace_distance_reference"])
        )
    elif kind == "coherent":
        # In the infinite oscillator, L^dagger[a_j] =
        # -(gamma_net/2 + i*omega) a_j for every input state. A complete-shell
        # projection changes this identity only through an explicitly
        # computable upper-shell residual. We audit that residual directly,
        # reconstruct the observed finite-cutoff deviation, and integrate its
        # absolute expectation to obtain a conservative curve-level bound.
        decay = 0.5 * (case.gamma_down - case.gamma_up) + 1j * operators.omega
        initial_amplitude_x = complex(series["amplitude_x"][0])
        initial_amplitude_y = complex(series["amplitude_y"][0])
        reference_x = np.exp(-decay * times) * initial_amplitude_x
        reference_y = np.exp(-decay * times) * initial_amplitude_y
        signed_error_x = series["amplitude_x"] - reference_x
        signed_error_y = series["amplitude_y"] - reference_y
        error_x = np.abs(signed_error_x)
        error_y = np.abs(signed_error_y)

        ax = operators.annihilation_x.toarray()
        ay = operators.annihilation_y.toarray()
        residual_operator_x = direct_adjoint_generator_action(
            operators,
            ax,
            case.gamma_down,
            case.gamma_up,
            case.gamma_phi,
        ) + decay * ax
        residual_operator_y = direct_adjoint_generator_action(
            operators,
            ay,
            case.gamma_down,
            case.gamma_up,
            case.gamma_phi,
        ) + decay * ay

        residual_expectation_x = np.empty(times.size, dtype=np.complex128)
        residual_expectation_y = np.empty(times.size, dtype=np.complex128)
        for time_index, vector in enumerate(case.vectors):
            density = unvec_f(vector, operators.dimension)
            residual_expectation_x[time_index] = expectation_dense(
                residual_operator_x, density
            )
            residual_expectation_y[time_index] = expectation_dense(
                residual_operator_y, density
            )

        absolute_bound_x = cumulative_trapezoid(
            np.abs(residual_expectation_x), times, initial=0.0
        )
        absolute_bound_y = cumulative_trapezoid(
            np.abs(residual_expectation_y), times, initial=0.0
        )
        reconstructed_x = np.exp(-decay * times) * cumulative_trapezoid(
            np.exp(decay * times) * residual_expectation_x,
            times,
            initial=0.0,
        )
        reconstructed_y = np.exp(-decay * times) * cumulative_trapezoid(
            np.exp(decay * times) * residual_expectation_y,
            times,
            initial=0.0,
        )
        reconstruction_error_x = np.abs(signed_error_x - reconstructed_x)
        reconstruction_error_y = np.abs(signed_error_y - reconstructed_y)
        bound_excess_x = error_x - absolute_bound_x
        bound_excess_y = error_y - absolute_bound_y

        series["coherent_amplitude_x_reference"] = reference_x
        series["coherent_amplitude_y_reference"] = reference_y
        series["coherent_amplitude_x_signed_error"] = signed_error_x
        series["coherent_amplitude_y_signed_error"] = signed_error_y
        series["coherent_amplitude_x_error"] = error_x
        series["coherent_amplitude_y_error"] = error_y
        series["coherent_heisenberg_residual_expectation_x"] = (
            residual_expectation_x
        )
        series["coherent_heisenberg_residual_expectation_y"] = (
            residual_expectation_y
        )
        series["coherent_residual_absolute_integral_bound_x"] = absolute_bound_x
        series["coherent_residual_absolute_integral_bound_y"] = absolute_bound_y
        series["coherent_residual_reconstruction_x"] = reconstructed_x
        series["coherent_residual_reconstruction_y"] = reconstructed_y
        series["coherent_residual_reconstruction_error_x"] = (
            reconstruction_error_x
        )
        series["coherent_residual_reconstruction_error_y"] = (
            reconstruction_error_y
        )
        series["coherent_amplitude_bound_excess_x"] = bound_excess_x
        series["coherent_amplitude_bound_excess_y"] = bound_excess_y

        metrics["projected_coherent_initial_tail"] = float(coherent_tail or 0.0)
        metrics["coherent_residual_operator_x_fro"] = frobenius_norm(
            residual_operator_x
        )
        metrics["coherent_residual_operator_y_fro"] = frobenius_norm(
            residual_operator_y
        )
        metrics["maximum_coherent_amplitude_x_error"] = float(np.max(error_x))
        metrics["maximum_coherent_amplitude_y_error"] = float(np.max(error_y))
        metrics["maximum_coherent_amplitude_error"] = max(
            metrics["maximum_coherent_amplitude_x_error"],
            metrics["maximum_coherent_amplitude_y_error"],
        )
        metrics["maximum_coherent_amplitude_bound_excess"] = max(
            float(np.max(bound_excess_x)),
            float(np.max(bound_excess_y)),
        )
        metrics["maximum_coherent_residual_reconstruction_error"] = max(
            float(np.max(reconstruction_error_x)),
            float(np.max(reconstruction_error_y)),
        )
        metrics["final_coherent_residual_absolute_integral_bound"] = max(
            float(absolute_bound_x[-1]),
            float(absolute_bound_y[-1]),
        )
    elif kind == "dephasing":
        population_00 = series["population_00"]
        population_10 = series["population_10"]
        coherence = series["coherence_00_10"]
        population_error = np.maximum(
            np.abs(population_00 - 0.5), np.abs(population_10 - 0.5)
        )
        occupation_error = np.abs(series["occupation_total"] - 0.5)
        energy_reference = float(series["energy"][0])
        energy_error = np.abs(series["energy"] - energy_reference)
        coherence_reference = coherence[0] * np.exp(
            (1j * operators.omega - 0.5 * GAMMA_PHI) * times
        )
        coherence_error = np.abs(coherence - coherence_reference)
        rotating_coherence = coherence * np.exp(-1j * operators.omega * times)
        rotating_reference = coherence[0] * np.exp(-0.5 * GAMMA_PHI * times)
        series["dephasing_population_error"] = population_error
        series["dephasing_occupation_error"] = occupation_error
        series["dephasing_energy_error"] = energy_error
        series["dephasing_coherence_reference"] = coherence_reference
        series["dephasing_coherence_error"] = coherence_error
        series["dephasing_rotating_coherence"] = rotating_coherence
        series["dephasing_rotating_reference"] = rotating_reference
        metrics["maximum_dephasing_population_error"] = float(
            np.max(population_error)
        )
        metrics["maximum_dephasing_occupation_error"] = float(
            np.max(occupation_error)
        )
        metrics["maximum_dephasing_energy_error"] = float(np.max(energy_error))
        metrics["maximum_dephasing_coherence_error"] = float(
            np.max(coherence_error)
        )
    else:
        raise ValueError(f"Unknown case-specific kind: {kind}")


def embed_density(
    density: np.ndarray,
    small: ShellOperators,
    large: ShellOperators,
) -> np.ndarray:
    if tuple(large.labels[: small.dimension]) != tuple(small.labels):
        raise RuntimeError("Complete-shell bases are not nested prefixes")
    result = np.zeros((large.dimension, large.dimension), dtype=np.complex128)
    result[: small.dimension, : small.dimension] = density
    return result


def cutoff_pair_metrics(
    *,
    family: str,
    small_case: PropagatedCase,
    large_case: PropagatedCase,
    small_operators: ShellOperators,
    large_operators: ShellOperators,
) -> Tuple[Dict[str, Any], Dict[str, np.ndarray]]:
    if not np.array_equal(small_case.times, large_case.times):
        raise RuntimeError("Cutoff cases use different time grids")
    times = small_case.times
    occupation_difference = np.abs(
        small_case.time_series["occupation_total"]
        - large_case.time_series["occupation_total"]
    )
    purity_difference = np.abs(
        small_case.time_series["purity"] - large_case.time_series["purity"]
    )
    distance = np.empty(times.size, dtype=np.float64)

    # B2/B3 remain diagonal in the number basis. Use the exact diagonal
    # trace-distance formula when that property has itself been verified;
    # otherwise fall back to a full Hermitian eigensolve. This avoids hundreds
    # of unnecessary dense diagonalizations without weakening the audit.
    diagonal_fast_path = (
        float(small_case.metrics["maximum_offdiagonal_fro"]) <= 1.0e-13
        and float(large_case.metrics["maximum_offdiagonal_fro"]) <= 1.0e-13
    )
    for time_index in range(times.size):
        rho_small = unvec_f(
            small_case.vectors[time_index], small_operators.dimension
        )
        rho_large = unvec_f(
            large_case.vectors[time_index], large_operators.dimension
        )
        if diagonal_fast_path:
            small_diagonal = np.diag(rho_small)
            large_diagonal = np.diag(rho_large)
            embedded_diagonal = np.zeros(
                large_operators.dimension, dtype=np.complex128
            )
            embedded_diagonal[: small_operators.dimension] = small_diagonal
            distance[time_index] = 0.5 * float(
                np.sum(np.abs(embedded_diagonal - large_diagonal), dtype=np.float64)
            )
        else:
            embedded = embed_density(rho_small, small_operators, large_operators)
            distance[time_index] = trace_distance(embedded, rho_large)

    # Exact finite-dimensional consistency bound in the larger space:
    # |Tr[N_perp (rho_small-rho_large)]| <= 2 ||N_perp|| T,
    # where T is the trace distance and ||N_perp|| = large_cutoff.
    occupation_trace_distance_bound = 2.0 * large_operators.cutoff * distance
    occupation_bound_excess = (
        occupation_difference - occupation_trace_distance_bound
    )

    row = {
        "row_type": "pairwise_cutoff_comparison",
        "family": family,
        "small_cutoff": small_operators.cutoff,
        "large_cutoff": large_operators.cutoff,
        "small_dimension": small_operators.dimension,
        "large_dimension": large_operators.dimension,
        "maximum_occupation_difference": float(np.max(occupation_difference)),
        "final_occupation_difference": float(occupation_difference[-1]),
        "maximum_purity_difference": float(np.max(purity_difference)),
        "final_purity_difference": float(purity_difference[-1]),
        "maximum_trace_distance": float(np.max(distance)),
        "final_trace_distance": float(distance[-1]),
        "trace_distance_evaluation": (
            "exact diagonal L1 formula" if diagonal_fast_path
            else "full Hermitian eigenspectrum"
        ),
        "maximum_occupation_trace_distance_bound": float(
            np.max(occupation_trace_distance_bound)
        ),
        "maximum_occupation_trace_distance_bound_excess": float(
            np.max(occupation_bound_excess)
        ),
    }
    arrays = {
        "t": times.copy(),
        "occupation_difference": occupation_difference,
        "purity_difference": purity_difference,
        "trace_distance": distance,
        "occupation_trace_distance_bound": occupation_trace_distance_bound,
        "occupation_trace_distance_bound_excess": occupation_bound_excess,
    }
    return row, arrays


# =============================================================================
# Acceptance logic
# =============================================================================
def make_check(value: float, criterion: str, passed: bool) -> Dict[str, Any]:
    return {
        "value": finite_float(value, "acceptance value"),
        "criterion": criterion,
        "pass": bool(passed),
    }


def build_acceptance(
    *,
    operator_audit: Mapping[str, Any],
    propagated_cases: Mapping[str, PropagatedCase],
    b7_metrics: Mapping[str, Any],
    cutoff_rows: Sequence[Mapping[str, Any]],
    cutoff_case_rows: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    checks: Dict[str, Dict[str, Any]] = {}
    thresholds = ACCEPTANCE_THRESHOLDS

    maxima = operator_audit["maximum_defects"]
    operator_identity = max(
        float(maxima["number_diagonal_error"]),
        float(maxima["hamiltonian_diagonal_error"]),
        float(maxima["bohr_relation_error"]),
        float(maxima["top_shell_upward_identity_error"]),
    )
    checks["operator_identities"] = make_check(
        operator_identity,
        f"<= {thresholds['operator_identity_max']:.3e}",
        operator_identity <= thresholds["operator_identity_max"],
    )
    trace_row = float(maxima["liouvillian_trace_row_error"])
    checks["liouvillian_trace_preserving_row"] = make_check(
        trace_row,
        f"<= {thresholds['liouvillian_trace_row_max']:.3e}",
        trace_row <= thresholds["liouvillian_trace_row_max"],
    )
    vectorization = float(maxima["vectorization_action_relative_error"])
    checks["column_major_vectorization"] = make_check(
        vectorization,
        f"<= {thresholds['vectorization_action_relative_max']:.3e}",
        vectorization <= thresholds["vectorization_action_relative_max"],
    )
    hermiticity_action = float(maxima["hermiticity_action_relative_error"])
    checks["generator_hermiticity_preservation"] = make_check(
        hermiticity_action,
        f"<= {thresholds['hermiticity_action_relative_max']:.3e}",
        hermiticity_action <= thresholds["hermiticity_action_relative_max"],
    )

    all_cases = list(propagated_cases.values())
    maximum_trace_error = max(
        float(case.metrics["maximum_trace_error"]) for case in all_cases
    )
    maximum_hermiticity = max(
        float(case.metrics["maximum_hermiticity_fro"]) for case in all_cases
    )
    minimum_eigenvalue = min(
        float(case.metrics["minimum_eigenvalue"]) for case in all_cases
    )
    maximum_intensity_formula_error = max(
        float(case.metrics["maximum_projected_intensity_formula_error"])
        for case in all_cases
    )
    checks["trace_preservation"] = make_check(
        maximum_trace_error,
        f"<= {thresholds['trace_error_max']:.3e}",
        maximum_trace_error <= thresholds["trace_error_max"],
    )
    checks["density_hermiticity"] = make_check(
        maximum_hermiticity,
        f"<= {thresholds['hermiticity_fro_max']:.3e}",
        maximum_hermiticity <= thresholds["hermiticity_fro_max"],
    )
    checks["density_positivity"] = make_check(
        minimum_eigenvalue,
        f">= {thresholds['minimum_eigenvalue_min']:.3e}",
        minimum_eigenvalue >= thresholds["minimum_eigenvalue_min"],
    )
    checks["projected_event_intensity_formula"] = make_check(
        maximum_intensity_formula_error,
        f"<= {thresholds['projected_intensity_formula_max']:.3e}",
        maximum_intensity_formula_error
        <= thresholds["projected_intensity_formula_max"],
    )

    b0 = propagated_cases["B0_N12"]
    stationarity = float(b0.metrics["ground_stationarity_trace_distance_max"])
    checks["B0_ground_stationarity"] = make_check(
        stationarity,
        f"<= {thresholds['ground_stationarity_trace_distance_max']:.3e}",
        stationarity <= thresholds["ground_stationarity_trace_distance_max"],
    )

    b1x = propagated_cases["B1x_N12"]
    b1y = propagated_cases["B1y_N12"]
    b1_error = max(
        float(b1x.metrics["maximum_one_quantum_occupation_error"]),
        float(b1y.metrics["maximum_one_quantum_occupation_error"]),
    )
    b1_isotropy = float(
        np.max(
            np.abs(
                b1x.time_series["occupation_total"]
                - b1y.time_series["occupation_total"]
            )
        )
    )
    checks["B1_one_quantum_decay"] = make_check(
        b1_error,
        f"<= {thresholds['one_quantum_occupation_error_max']:.3e}",
        b1_error <= thresholds["one_quantum_occupation_error_max"],
    )
    checks["B1_xy_isotropy"] = make_check(
        b1_isotropy,
        f"<= {thresholds['one_quantum_isotropy_max']:.3e}",
        b1_isotropy <= thresholds["one_quantum_isotropy_max"],
    )

    thermal_keys = (
        "B2_N8", "B2_N12", "B2_N16",
        "B3_N8", "B3_N12", "B3_N16",
    )
    projected_population_l1 = max(
        float(propagated_cases[key].metrics["maximum_population_reference_l1"])
        for key in thermal_keys
    )
    projected_occupation_error = max(
        float(
            propagated_cases[key].metrics[
                "maximum_projected_occupation_reference_error"
            ]
        )
        for key in thermal_keys
    )
    infinite_bound_excess = max(
        float(
            propagated_cases[key].metrics[
                "maximum_infinite_occupation_bound_excess"
            ]
        )
        for key in thermal_keys
    )
    checks["B2_B3_projected_population_reference"] = make_check(
        projected_population_l1,
        f"<= {thresholds['projected_population_l1_max']:.3e}",
        projected_population_l1 <= thresholds["projected_population_l1_max"],
    )
    checks["B2_B3_projected_occupation_reference"] = make_check(
        projected_occupation_error,
        f"<= {thresholds['projected_occupation_error_max']:.3e}",
        projected_occupation_error
        <= thresholds["projected_occupation_error_max"],
    )
    checks["B2_B3_infinite_law_within_declared_overflow_bound"] = make_check(
        infinite_bound_excess,
        "<= 0",
        infinite_bound_excess <= 0.0,
    )

    b4 = propagated_cases["B4_N12"]
    gibbs_residual = float(b4.metrics["gibbs_generator_residual_fro"])
    gibbs_distance = float(b4.metrics["gibbs_stationarity_trace_distance_max"])
    detailed_balance = float(b4.metrics["detailed_balance_relative_error"])
    checks["B4_projected_gibbs_generator_stationarity"] = make_check(
        gibbs_residual,
        f"<= {thresholds['gibbs_generator_residual_fro_max']:.3e}",
        gibbs_residual <= thresholds["gibbs_generator_residual_fro_max"],
    )
    checks["B4_projected_gibbs_propagated_stationarity"] = make_check(
        gibbs_distance,
        f"<= {thresholds['gibbs_trace_distance_max']:.3e}",
        gibbs_distance <= thresholds["gibbs_trace_distance_max"],
    )
    checks["B4_projected_detailed_balance"] = make_check(
        detailed_balance,
        f"<= {thresholds['detailed_balance_relative_max']:.3e}",
        detailed_balance <= thresholds["detailed_balance_relative_max"],
    )

    b5 = propagated_cases["B5_N12"]
    coherent_error = float(b5.metrics["maximum_coherent_amplitude_error"])
    coherent_bound_excess = float(
        b5.metrics["maximum_coherent_amplitude_bound_excess"]
    )
    coherent_reconstruction_error = float(
        b5.metrics["maximum_coherent_residual_reconstruction_error"]
    )
    checks["B5_coherent_amplitude_absolute_error"] = make_check(
        coherent_error,
        f"<= {thresholds['coherent_amplitude_absolute_error_max']:.3e}",
        coherent_error
        <= thresholds["coherent_amplitude_absolute_error_max"],
    )
    checks["B5_coherent_amplitude_within_projected_residual_bound"] = (
        make_check(
            coherent_bound_excess,
            f"<= {thresholds['coherent_bound_excess_max']:.3e}",
            coherent_bound_excess <= thresholds["coherent_bound_excess_max"],
        )
    )
    checks["B5_coherent_projected_residual_reconstruction"] = make_check(
        coherent_reconstruction_error,
        f"<= {thresholds['coherent_residual_reconstruction_error_max']:.3e}",
        coherent_reconstruction_error
        <= thresholds["coherent_residual_reconstruction_error_max"],
    )

    b6 = propagated_cases["B6_N12"]
    dephasing_population = max(
        float(b6.metrics["maximum_dephasing_population_error"]),
        float(b6.metrics["maximum_dephasing_occupation_error"]),
    )
    dephasing_energy = float(b6.metrics["maximum_dephasing_energy_error"])
    dephasing_coherence = float(b6.metrics["maximum_dephasing_coherence_error"])
    checks["B6_dephasing_population_invariants"] = make_check(
        dephasing_population,
        f"<= {thresholds['dephasing_population_error_max']:.3e}",
        dephasing_population <= thresholds["dephasing_population_error_max"],
    )
    checks["B6_dephasing_energy_invariant"] = make_check(
        dephasing_energy,
        f"<= {thresholds['dephasing_energy_error_max']:.3e}",
        dephasing_energy <= thresholds["dephasing_energy_error_max"],
    )
    checks["B6_dephasing_coherence_law"] = make_check(
        dephasing_coherence,
        f"<= {thresholds['dephasing_coherence_error_max']:.3e}",
        dephasing_coherence <= thresholds["dephasing_coherence_error_max"],
    )

    b7_value = max(
        float(b7_metrics["maximum_annihilation_relative_action_defect"]),
        float(b7_metrics["maximum_creation_relative_action_defect"]),
    )
    checks["B7_isotropic_basis_invariance"] = make_check(
        b7_value,
        f"<= {thresholds['isotropic_action_relative_max']:.3e}",
        b7_value <= thresholds["isotropic_action_relative_max"],
    )

    n12_n16_rows = [
        row
        for row in cutoff_rows
        if int(row["small_cutoff"]) == 12 and int(row["large_cutoff"]) == 16
    ]
    cutoff_occ = max(float(row["maximum_occupation_difference"]) for row in n12_n16_rows)
    cutoff_purity = max(float(row["maximum_purity_difference"]) for row in n12_n16_rows)
    cutoff_distance = max(float(row["maximum_trace_distance"]) for row in n12_n16_rows)
    checks["B8_cutoff_occupation_N12_to_N16"] = make_check(
        cutoff_occ,
        f"<= {thresholds['cutoff_n12_n16_occupation_max']:.3e}",
        cutoff_occ <= thresholds["cutoff_n12_n16_occupation_max"],
    )
    checks["B8_cutoff_purity_N12_to_N16"] = make_check(
        cutoff_purity,
        f"<= {thresholds['cutoff_n12_n16_purity_max']:.3e}",
        cutoff_purity <= thresholds["cutoff_n12_n16_purity_max"],
    )
    checks["B8_cutoff_trace_distance_N12_to_N16"] = make_check(
        cutoff_distance,
        f"<= {thresholds['cutoff_n12_n16_trace_distance_max']:.3e}",
        cutoff_distance <= thresholds["cutoff_n12_n16_trace_distance_max"],
    )
    cutoff_occupation_bound_excess = max(
        float(row["maximum_occupation_trace_distance_bound_excess"])
        for row in n12_n16_rows
    )
    checks["B8_occupation_trace_distance_consistency"] = make_check(
        cutoff_occupation_bound_excess,
        "<= 5.000e-12",
        cutoff_occupation_bound_excess <= 5.0e-12,
    )

    production_rows = [row for row in cutoff_case_rows if int(row["cutoff"]) == 12]
    production_top = max(float(row["maximum_top_shell_population"]) for row in production_rows)
    production_overflow = max(float(row["final_overflow_budget"]) for row in production_rows)
    checks["B8_production_top_shell"] = make_check(
        production_top,
        f"<= {thresholds['production_top_shell_max']:.3e}",
        production_top <= thresholds["production_top_shell_max"],
    )
    checks["B8_production_overflow"] = make_check(
        production_overflow,
        f"<= {thresholds['production_overflow_final_max']:.3e}",
        production_overflow <= thresholds["production_overflow_final_max"],
    )

    monotonic_tolerance = thresholds["cutoff_monotonicity_tolerance"]
    top_violation = 0.0
    overflow_violation = 0.0
    for family in ("B2", "B3"):
        rows = {
            int(row["cutoff"]): row
            for row in cutoff_case_rows
            if row["family"] == family
        }
        top_violation = max(
            top_violation,
            float(rows[12]["maximum_top_shell_population"])
            - float(rows[8]["maximum_top_shell_population"]),
            float(rows[16]["maximum_top_shell_population"])
            - float(rows[12]["maximum_top_shell_population"]),
        )
        overflow_violation = max(
            overflow_violation,
            float(rows[12]["final_overflow_budget"])
            - float(rows[8]["final_overflow_budget"]),
            float(rows[16]["final_overflow_budget"])
            - float(rows[12]["final_overflow_budget"]),
        )
    checks["B8_top_shell_monotonic_improvement"] = make_check(
        top_violation,
        f"<= {monotonic_tolerance:.3e}",
        top_violation <= monotonic_tolerance,
    )
    checks["B8_overflow_monotonic_improvement"] = make_check(
        overflow_violation,
        f"<= {monotonic_tolerance:.3e}",
        overflow_violation <= monotonic_tolerance,
    )

    accepted = all(bool(result["pass"]) for result in checks.values())
    return {
        "stage": STAGE_NAME,
        "script_version": SCRIPT_VERSION,
        "accepted": accepted,
        "checks": checks,
        "thresholds": ACCEPTANCE_THRESHOLDS,
        "scope": (
            "Detector-free finite projected bath only. This PASS does not "
            "certify any detector-bath response or replace Stage 01C."
        ),
    }


# =============================================================================
# Output assembly
# =============================================================================
def store_case_arrays(
    destination: MutableMapping[str, np.ndarray],
    case: PropagatedCase,
) -> None:
    prefix = case.case_id
    for name, array in case.time_series.items():
        destination[f"{prefix}__{name}"] = np.asarray(array)
    destination[f"{prefix}__rho_initial"] = case.initial_density
    destination[f"{prefix}__rho_final"] = case.final_density


def case_metrics_row(case: PropagatedCase) -> Dict[str, Any]:
    return dict(case.metrics)


def cutoff_case_row(family: str, case: PropagatedCase) -> Dict[str, Any]:
    return {
        "row_type": "cutoff_case",
        "family": family,
        "case_id": case.case_id,
        "cutoff": case.cutoff,
        "dimension": case.metrics["dimension"],
        "maximum_top_shell_population": case.metrics[
            "maximum_top_shell_population"
        ],
        "final_top_shell_population": case.metrics[
            "final_top_shell_population"
        ],
        "maximum_omitted_upward_intensity": case.metrics[
            "maximum_omitted_upward_intensity"
        ],
        "final_overflow_budget": case.metrics["final_overflow_budget"],
        "maximum_population_reference_l1": case.metrics[
            "maximum_population_reference_l1"
        ],
        "maximum_projected_occupation_reference_error": case.metrics[
            "maximum_projected_occupation_reference_error"
        ],
        "maximum_infinite_occupation_error": case.metrics[
            "maximum_infinite_occupation_error"
        ],
        "maximum_infinite_occupation_bound_excess": case.metrics[
            "maximum_infinite_occupation_bound_excess"
        ],
        "final_occupation_total": case.metrics["final_occupation_total"],
        "final_purity": case.metrics["final_purity"],
    }


# =============================================================================
# CLI and main
# =============================================================================
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Stage-03 detector-free complete-shell bath certification. "
            f"The directory name is fixed to {OUTPUT_DIRECTORY_NAME}."
        )
    )
    parser.add_argument(
        "--out-root",
        type=Path,
        default=Path(os.getenv("OUTDIR", ".")),
        help=(
            "Root under which the fixed 4060.Bath_only_tests directory is "
            "created or reused."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = args.out_root.expanduser().resolve() / OUTPUT_DIRECTORY_NAME
    out_dir.mkdir(parents=True, exist_ok=True)
    remove_stale_products(out_dir)

    original_stdout = sys.stdout
    stdout_handle = (out_dir / "solver_stdout.txt").open("w", encoding="utf-8")
    sys.stdout = Tee(original_stdout, stdout_handle)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(out_dir / "solver_log.txt", mode="w"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )

    script_path = Path(__file__).resolve()
    script_copy = out_dir / "03_bath_only_fock_test.py"
    if script_path != script_copy:
        shutil.copy2(script_path, script_copy)
    script_sha256 = sha256_file(script_path)

    status_path = out_dir / "Stage03_run_status.json"
    status: Dict[str, Any] = {
        "status": "initializing",
        "started_utc": utc_now_iso(),
        "stage": STAGE_NAME,
        "script_version": SCRIPT_VERSION,
        "script_sha256": script_sha256,
        "output_directory": str(out_dir),
        "output_directory_contract": OUTPUT_DIRECTORY_NAME,
        "cutoffs": list(SHELL_CUTOFFS),
        "production_cutoff": PRODUCTION_SHELL,
        "omega": OMEGA,
        "T_final": T_FINAL,
        "number_of_output_times": NUM_OUTPUT_TIMES,
    }
    atomic_write_json(status_path, status)

    start_time = time.perf_counter()
    try:
        print("[info] Stage-03 detector-free Fock-space bath certification")
        print(f"[info] fixed output directory: {out_dir}")
        print(f"[info] script SHA-256: {script_sha256}")
        print(f"[info] cutoffs: {SHELL_CUTOFFS}")
        print(f"[info] omega: {OMEGA:g}")
        print(f"[info] T_final: {T_FINAL:g}")
        print(f"[info] output times: {NUM_OUTPUT_TIMES}")
        print("[info] vectorization: column-major order='F'")
        print("[info] no detector, longitudinal coordinate, clipping, or renormalization")

        times = np.linspace(0.0, T_FINAL, NUM_OUTPUT_TIMES, dtype=np.float64)
        rng = np.random.default_rng(RNG_SEED)

        operators_by_cutoff = {
            cutoff: build_shell_operators(cutoff, OMEGA)
            for cutoff in SHELL_CUTOFFS
        }
        for cutoff, operators in operators_by_cutoff.items():
            print(
                f"[operators] N={cutoff}, M={operators.dimension}, "
                f"M^2={operators.dimension**2}"
            )

        operator_audit = certify_operators(operators_by_cutoff, rng)
        atomic_write_json(out_dir / "Stage03_operator_audit.json", operator_audit)
        print("[audit] complete-shell operators and vectorization certified")

        propagated_cases: Dict[str, PropagatedCase] = {}
        time_series_output: Dict[str, np.ndarray] = {
            "global_times": times,
            "shell_cutoffs": np.asarray(SHELL_CUTOFFS, dtype=np.int64),
        }
        for cutoff, operators in operators_by_cutoff.items():
            time_series_output[f"basis_labels_N{cutoff}"] = np.asarray(
                operators.labels, dtype=np.int64
            )

        # ------------------------------------------------------------------
        # B0 and B1: zero-temperature amplitude damping at N=12.
        # ------------------------------------------------------------------
        ops12 = operators_by_cutoff[12]
        l_zero = build_liouvillian(ops12, GAMMA_ZERO_T, 0.0, 0.0)
        rho00 = basis_density(ops12, 0, 0)
        rho10 = basis_density(ops12, 1, 0)
        rho01 = basis_density(ops12, 0, 1)
        zero_vectors = propagate_many(l_zero, (rho00, rho10, rho01), times)

        b0 = analyze_propagated_case(
            case_id="B0_N12",
            description="zero-temperature ground-state stationarity",
            operators=ops12,
            vectors=zero_vectors[0],
            times=times,
            initial_density=rho00,
            gamma_down=GAMMA_ZERO_T,
            gamma_up=0.0,
            gamma_phi=0.0,
            initial_state_label="|00><00|",
            trace_distance_reference=rho00,
        )
        add_case_specific_metrics(b0, ops12, kind="ground_stationary")
        propagated_cases[b0.case_id] = b0

        b1x = analyze_propagated_case(
            case_id="B1x_N12",
            description="one-quantum x decay",
            operators=ops12,
            vectors=zero_vectors[1],
            times=times,
            initial_density=rho10,
            gamma_down=GAMMA_ZERO_T,
            gamma_up=0.0,
            gamma_phi=0.0,
            initial_state_label="|10><10|",
        )
        add_case_specific_metrics(b1x, ops12, kind="one_quantum")
        propagated_cases[b1x.case_id] = b1x

        b1y = analyze_propagated_case(
            case_id="B1y_N12",
            description="one-quantum y decay",
            operators=ops12,
            vectors=zero_vectors[2],
            times=times,
            initial_density=rho01,
            gamma_down=GAMMA_ZERO_T,
            gamma_up=0.0,
            gamma_phi=0.0,
            initial_state_label="|01><01|",
        )
        add_case_specific_metrics(b1y, ops12, kind="one_quantum")
        propagated_cases[b1y.case_id] = b1y
        print("[cases] B0, B1x, B1y completed")
        del zero_vectors

        # ------------------------------------------------------------------
        # B2--B5 at N=12: one common thermal Liouvillian.
        # ------------------------------------------------------------------
        l_thermal_12 = build_liouvillian(
            ops12, GAMMA_DOWN_THERMAL, GAMMA_UP_THERMAL, 0.0
        )
        rho20 = basis_density(ops12, 2, 0)
        rho_gibbs = projected_gibbs_density(ops12, Q_THERMAL)
        rho_coherent, coherent_tail = coherent_density(ops12, ALPHA_X, ALPHA_Y)
        thermal_vectors_12 = propagate_many(
            l_thermal_12,
            (rho00, rho20, rho_gibbs, rho_coherent),
            times,
        )

        population_generator_12 = build_population_generator(
            ops12, GAMMA_DOWN_THERMAL, GAMMA_UP_THERMAL
        )
        pop00_12 = propagate_populations(
            population_generator_12, np.real(np.diag(rho00)), times
        )
        pop20_12 = propagate_populations(
            population_generator_12, np.real(np.diag(rho20)), times
        )
        infinite_b2 = 2.0 * NBAR_ONE_MODE * (
            1.0 - np.exp(-GAMMA_NET_THERMAL * times)
        )
        infinite_b3 = 2.0 * NBAR_ONE_MODE + (
            2.0 - 2.0 * NBAR_ONE_MODE
        ) * np.exp(-GAMMA_NET_THERMAL * times)

        b2_12 = analyze_propagated_case(
            case_id="B2_N12",
            description="thermal heating from the transverse ground state",
            operators=ops12,
            vectors=thermal_vectors_12[0],
            times=times,
            initial_density=rho00,
            gamma_down=GAMMA_DOWN_THERMAL,
            gamma_up=GAMMA_UP_THERMAL,
            gamma_phi=0.0,
            initial_state_label="|00><00|",
            population_reference=pop00_12,
            infinite_occupation_reference=infinite_b2,
        )
        propagated_cases[b2_12.case_id] = b2_12

        b3_12 = analyze_propagated_case(
            case_id="B3_N12",
            description="thermal relaxation from the hotter state |20>",
            operators=ops12,
            vectors=thermal_vectors_12[1],
            times=times,
            initial_density=rho20,
            gamma_down=GAMMA_DOWN_THERMAL,
            gamma_up=GAMMA_UP_THERMAL,
            gamma_phi=0.0,
            initial_state_label="|20><20|",
            population_reference=pop20_12,
            infinite_occupation_reference=infinite_b3,
        )
        propagated_cases[b3_12.case_id] = b3_12

        gibbs_direct_residual = frobenius_norm(
            direct_generator_action(
                ops12,
                rho_gibbs,
                GAMMA_DOWN_THERMAL,
                GAMMA_UP_THERMAL,
                0.0,
            )
        )
        n_gibbs = float(
            expectation_dense(ops12.number_total.toarray(), rho_gibbs).real
        )
        ptop_gibbs = float(
            expectation_dense(ops12.top_projector.toarray(), rho_gibbs).real
        )
        equilibrium_down = GAMMA_DOWN_THERMAL * n_gibbs
        equilibrium_up = GAMMA_UP_THERMAL * (
            n_gibbs + 2.0 - (ops12.cutoff + 2.0) * ptop_gibbs
        )
        detailed_balance_relative = abs(equilibrium_down - equilibrium_up) / max(
            abs(equilibrium_down), abs(equilibrium_up), np.finfo(float).tiny
        )
        b4 = analyze_propagated_case(
            case_id="B4_N12",
            description="projected Gibbs stationarity and detailed balance",
            operators=ops12,
            vectors=thermal_vectors_12[2],
            times=times,
            initial_density=rho_gibbs,
            gamma_down=GAMMA_DOWN_THERMAL,
            gamma_up=GAMMA_UP_THERMAL,
            gamma_phi=0.0,
            initial_state_label="rho_B,N proportional to q^N_perp",
            trace_distance_reference=rho_gibbs,
        )
        add_case_specific_metrics(
            b4,
            ops12,
            kind="gibbs",
            gibbs_generator_residual=gibbs_direct_residual,
            detailed_balance_relative=detailed_balance_relative,
        )
        b4.metrics["equilibrium_downward_intensity"] = equilibrium_down
        b4.metrics["equilibrium_upward_intensity"] = equilibrium_up
        propagated_cases[b4.case_id] = b4

        b5 = analyze_propagated_case(
            case_id="B5_N12",
            description="coherent-amplitude decay under the thermal amplitude channel",
            operators=ops12,
            vectors=thermal_vectors_12[3],
            times=times,
            initial_density=rho_coherent,
            gamma_down=GAMMA_DOWN_THERMAL,
            gamma_up=GAMMA_UP_THERMAL,
            gamma_phi=0.0,
            initial_state_label=f"projected coherent alpha_x={ALPHA_X}, alpha_y={ALPHA_Y}",
        )
        add_case_specific_metrics(
            b5, ops12, kind="coherent", coherent_tail=coherent_tail
        )
        propagated_cases[b5.case_id] = b5
        print("[cases] B2, B3, B4, B5 at N=12 completed")
        del thermal_vectors_12

        # ------------------------------------------------------------------
        # B6: pure independent number dephasing.
        # ------------------------------------------------------------------
        l_dephasing = build_liouvillian(ops12, 0.0, 0.0, GAMMA_PHI)
        rho_dephasing = dephasing_superposition_density(ops12)
        dephasing_vectors = propagate_many(l_dephasing, (rho_dephasing,), times)
        b6 = analyze_propagated_case(
            case_id="B6_N12",
            description="pure independent number dephasing",
            operators=ops12,
            vectors=dephasing_vectors[0],
            times=times,
            initial_density=rho_dephasing,
            gamma_down=0.0,
            gamma_up=0.0,
            gamma_phi=GAMMA_PHI,
            initial_state_label="(|00>+|10>)(<00|+<10|)/2",
        )
        add_case_specific_metrics(b6, ops12, kind="dephasing")
        propagated_cases[b6.case_id] = b6
        print("[cases] B6 completed")
        del dephasing_vectors

        # ------------------------------------------------------------------
        # B7: isotropic basis invariance.
        # ------------------------------------------------------------------
        b7_metrics = certify_isotropic_basis_invariance(ops12, rng)
        print("[cases] B7 completed")

        # ------------------------------------------------------------------
        # B8: B2 and B3 at N=8 and N=16. N=12 results are reused.
        # ------------------------------------------------------------------
        for cutoff in (8, 16):
            operators = operators_by_cutoff[cutoff]
            liouvillian = build_liouvillian(
                operators, GAMMA_DOWN_THERMAL, GAMMA_UP_THERMAL, 0.0
            )
            rho_ground = basis_density(operators, 0, 0)
            rho_hot = basis_density(operators, 2, 0)
            vectors = propagate_many(liouvillian, (rho_ground, rho_hot), times)
            population_generator = build_population_generator(
                operators, GAMMA_DOWN_THERMAL, GAMMA_UP_THERMAL
            )
            pop_ground = propagate_populations(
                population_generator, np.real(np.diag(rho_ground)), times
            )
            pop_hot = propagate_populations(
                population_generator, np.real(np.diag(rho_hot)), times
            )

            b2 = analyze_propagated_case(
                case_id=f"B2_N{cutoff}",
                description="thermal heating from the transverse ground state",
                operators=operators,
                vectors=vectors[0],
                times=times,
                initial_density=rho_ground,
                gamma_down=GAMMA_DOWN_THERMAL,
                gamma_up=GAMMA_UP_THERMAL,
                gamma_phi=0.0,
                initial_state_label="|00><00|",
                population_reference=pop_ground,
                infinite_occupation_reference=infinite_b2,
            )
            propagated_cases[b2.case_id] = b2

            b3 = analyze_propagated_case(
                case_id=f"B3_N{cutoff}",
                description="thermal relaxation from the hotter state |20>",
                operators=operators,
                vectors=vectors[1],
                times=times,
                initial_density=rho_hot,
                gamma_down=GAMMA_DOWN_THERMAL,
                gamma_up=GAMMA_UP_THERMAL,
                gamma_phi=0.0,
                initial_state_label="|20><20|",
                population_reference=pop_hot,
                infinite_occupation_reference=infinite_b3,
            )
            propagated_cases[b3.case_id] = b3
            print(f"[cases] B8 thermal families at N={cutoff} completed")
            del vectors

        # ------------------------------------------------------------------
        # Cutoff comparisons.
        # ------------------------------------------------------------------
        cutoff_case_rows: List[Dict[str, Any]] = []
        for family in ("B2", "B3"):
            for cutoff in SHELL_CUTOFFS:
                cutoff_case_rows.append(
                    cutoff_case_row(family, propagated_cases[f"{family}_N{cutoff}"])
                )

        cutoff_pair_rows: List[Dict[str, Any]] = []
        cutoff_pair_arrays: Dict[str, np.ndarray] = {}
        for family in ("B2", "B3"):
            for small_cutoff, large_cutoff in ((8, 12), (12, 16)):
                row, arrays = cutoff_pair_metrics(
                    family=family,
                    small_case=propagated_cases[f"{family}_N{small_cutoff}"],
                    large_case=propagated_cases[f"{family}_N{large_cutoff}"],
                    small_operators=operators_by_cutoff[small_cutoff],
                    large_operators=operators_by_cutoff[large_cutoff],
                )
                cutoff_pair_rows.append(row)
                prefix = f"B8_{family}_N{small_cutoff}_to_N{large_cutoff}"
                for name, array in arrays.items():
                    cutoff_pair_arrays[f"{prefix}__{name}"] = array

        # ------------------------------------------------------------------
        # Store raw time series and case-specific final states.
        # ------------------------------------------------------------------
        for case in propagated_cases.values():
            store_case_arrays(time_series_output, case)
        time_series_output.update(cutoff_pair_arrays)
        time_series_output["B1__xy_isotropy_occupation_difference"] = np.abs(
            b1x.time_series["occupation_total"]
            - b1y.time_series["occupation_total"]
        )
        atomic_savez_compressed(
            out_dir / "Stage03_time_series.npz", **time_series_output
        )

        case_rows = [case_metrics_row(case) for case in propagated_cases.values()]
        b7_case_row = {
            key: value
            for key, value in b7_metrics.items()
            if key != "raw_records"
        }
        b7_case_row.update(
            {
                "omega": OMEGA,
                "gamma_down": "unit operator identity",
                "gamma_up": "unit operator identity",
                "gamma_phi": 0.0,
                "initial_state": "random Hermitian tests",
                "T_final": 0.0,
                "number_of_output_times": 0,
            }
        )
        case_rows.append(b7_case_row)
        atomic_write_csv(out_dir / "Stage03_case_metrics.csv", case_rows)

        cutoff_rows_all = cutoff_case_rows + cutoff_pair_rows
        atomic_write_csv(out_dir / "Stage03_cutoff_metrics.csv", cutoff_rows_all)

        acceptance = build_acceptance(
            operator_audit=operator_audit,
            propagated_cases=propagated_cases,
            b7_metrics=b7_metrics,
            cutoff_rows=cutoff_pair_rows,
            cutoff_case_rows=cutoff_case_rows,
        )
        atomic_write_json(out_dir / "Stage03_acceptance.json", acceptance)

        elapsed = time.perf_counter() - start_time
        solver_audit: Dict[str, Any] = {
            "status": "completed",
            "completed_utc": utc_now_iso(),
            "elapsed_seconds": elapsed,
            "stage": STAGE_NAME,
            "script_version": SCRIPT_VERSION,
            "script_sha256": script_sha256,
            "accepted": bool(acceptance["accepted"]),
            "propagated_case_count": len(propagated_cases),
            "cutoff_pair_count": len(cutoff_pair_rows),
            "isotropic_unitary_count": b7_metrics["unitary_count"],
            "isotropic_matrix_count_per_unitary": b7_metrics[
                "matrix_count_per_unitary"
            ],
            "maximum_trace_error": max(
                float(case.metrics["maximum_trace_error"])
                for case in propagated_cases.values()
            ),
            "maximum_hermiticity_fro": max(
                float(case.metrics["maximum_hermiticity_fro"])
                for case in propagated_cases.values()
            ),
            "minimum_eigenvalue": min(
                float(case.metrics["minimum_eigenvalue"])
                for case in propagated_cases.values()
            ),
            "maximum_projected_intensity_formula_error": max(
                float(case.metrics["maximum_projected_intensity_formula_error"])
                for case in propagated_cases.values()
            ),
            "parent_stage02_solver_sha256": PARENT_STAGE02_SOLVER_SHA256,
            "parent_stage02_loader_sha256": PARENT_STAGE02_LOADER_SHA256,
            "reviewed_source_sha256": REVIEWED_SOURCE_SHA256,
            "b7_metrics": {
                key: value
                for key, value in b7_metrics.items()
                if key != "raw_records"
            },
            "acceptance_check_count": len(acceptance["checks"]),
            "acceptance_pass_count": sum(
                bool(item["pass"]) for item in acceptance["checks"].values()
            ),
            "implementation_guards": {
                "detector_present": False,
                "longitudinal_coordinate_present": False,
                "monte_carlo_present": False,
                "positivity_clipping_present": False,
                "trace_renormalization_present": False,
                "density_dtype": "complex128",
                "operator_backend": "SciPy sparse CPU",
                "propagator": "scipy.sparse.linalg.expm_multiply",
                "density_vectorization": "column-major order='F'",
            },
        }
        atomic_write_json(out_dir / "Stage03_solver_audit.json", solver_audit)

        configuration: Dict[str, Any] = {
            "stage": STAGE_NAME,
            "script_version": SCRIPT_VERSION,
            "script_sha256": script_sha256,
            "directory_contract": {
                "fixed_directory_name": OUTPUT_DIRECTORY_NAME,
                "timestamped_directories": False,
                "parameter_generated_directories": False,
                "rerun_policy": "replace fixed Stage-03 products in the same directory",
            },
            "scientific_scope": {
                "transverse_only": True,
                "detector_present": False,
                "longitudinal_coordinate_present": False,
                "bath_only": True,
                "trace_preserving_required": True,
                "cartesian_grid_present": False,
            },
            "basis": {
                "complete_shell_cutoffs": list(SHELL_CUTOFFS),
                "production_shell_for_this_certification": PRODUCTION_SHELL,
                "ordering": "shell ascending, n_x descending within each shell",
                "orthonormal": True,
            },
            "vectorization": {
                "numpy_order": "F",
                "identity": "vec(A rho B) = (B^T kron A) vec(rho)",
                "liouvillian_hamiltonian": "-i (I kron H - H^T kron I)",
            },
            "parameters": {
                "hbar": HBAR,
                "mass": MASS,
                "omega": OMEGA,
                "T_final": T_FINAL,
                "number_of_output_times": NUM_OUTPUT_TIMES,
                "gamma_zero_temperature": GAMMA_ZERO_T,
                "gamma_down_thermal": GAMMA_DOWN_THERMAL,
                "gamma_up_thermal": GAMMA_UP_THERMAL,
                "gamma_net_thermal": GAMMA_NET_THERMAL,
                "q_thermal": Q_THERMAL,
                "nbar_one_mode": NBAR_ONE_MODE,
                "gamma_phi": GAMMA_PHI,
                "alpha_x_real": float(ALPHA_X.real),
                "alpha_x_imag": float(ALPHA_X.imag),
                "alpha_y_real": float(ALPHA_Y.real),
                "alpha_y_imag": float(ALPHA_Y.imag),
                "rng_seed": RNG_SEED,
            },
            "case_matrix": {
                "B0": "N12, |00>, gamma_down=0.2, gamma_up=gamma_phi=0",
                "B1x": "N12, |10>, gamma_down=0.2",
                "B1y": "N12, |01>, gamma_down=0.2",
                "B2": "N8/N12/N16, |00>, gamma_down=0.25, gamma_up=0.05",
                "B3": "N8/N12/N16, |20>, gamma_down=0.25, gamma_up=0.05",
                "B4": "N12 projected Gibbs q=0.2",
                "B5": (
                    "N12 projected coherent state alpha_x=0.4 with an exact "
                    "projected Heisenberg-residual audit"
                ),
                "B6": "N12 (|00>+|10>)/sqrt(2), gamma_phi=0.2",
                "B7": "N12 random U(2) isotropic dissipator-action tests",
                "B8": "pairwise N8->N12 and N12->N16 convergence for B2/B3",
            },
            "acceptance_thresholds": ACCEPTANCE_THRESHOLDS,
            "software": {
                "python": sys.version,
                "platform": platform.platform(),
                "numpy": np.__version__,
                "scipy": scipy.__version__,
            },
            "provenance": {
                "parent_stage02_solver_sha256": PARENT_STAGE02_SOLVER_SHA256,
                "parent_stage02_loader_sha256": PARENT_STAGE02_LOADER_SHA256,
                "reviewed_source_sha256": REVIEWED_SOURCE_SHA256,
            },
        }
        configuration["configuration_sha256"] = sha256_json(configuration)
        atomic_write_json(out_dir / "Stage03_configuration.json", configuration)

        status.update(
            {
                "status": "completed",
                "completed_utc": utc_now_iso(),
                "elapsed_seconds": elapsed,
                "accepted": bool(acceptance["accepted"]),
                "propagated_case_count": len(propagated_cases),
                "acceptance_check_count": len(acceptance["checks"]),
            }
        )
        atomic_write_json(status_path, status)

        hashes = output_hash_manifest(
            out_dir,
            exclusions=(
                "Stage03_output_hashes.json",
                "Stage03_run_status.json",
                "solver_stdout.txt",
                "solver_log.txt",
                "Stage03_loader_audit.json",
                "Stage03_loader_case_metrics.csv",
                "Stage03_loader_cutoff_metrics.csv",
                "Stage03_bath_only_report.md",
                "Stage03_loader_output_hashes.json",
                "loader_stdout.txt",
                "loader_log.txt",
            ),
        )
        atomic_write_json(out_dir / "Stage03_output_hashes.json", hashes)

        print("\n[acceptance]")
        for name, result in acceptance["checks"].items():
            print(
                f"  {name:52s} value={result['value']:.6e} "
                f"criterion {result['criterion']} -> "
                f"{'PASS' if result['pass'] else 'FAIL'}"
            )
        print(f"\n[decision] Stage-03 solver accepted: {acceptance['accepted']}")
        print(f"[info] elapsed seconds: {elapsed:.3f}")
        print(f"[info] outputs: {out_dir}")
        return 0 if acceptance["accepted"] else 2

    except Exception as exc:
        elapsed = time.perf_counter() - start_time
        logging.exception("Stage-03 bath-only certification failed")
        failure = {
            "status": "failed",
            "failed_utc": utc_now_iso(),
            "elapsed_seconds": elapsed,
            "stage": STAGE_NAME,
            "script_version": SCRIPT_VERSION,
            "script_sha256": script_sha256,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc(),
        }
        atomic_write_json(out_dir / "Stage03_solver_failure.json", failure)
        status.update(failure)
        atomic_write_json(status_path, status)
        return 1
    finally:
        try:
            stdout_handle.flush()
            stdout_handle.close()
        finally:
            sys.stdout = original_stdout


if __name__ == "__main__":
    raise SystemExit(main())
