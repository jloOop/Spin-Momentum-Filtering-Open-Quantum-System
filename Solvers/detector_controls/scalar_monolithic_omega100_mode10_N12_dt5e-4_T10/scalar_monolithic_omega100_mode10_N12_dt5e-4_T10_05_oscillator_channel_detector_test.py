#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
05_oscillator_channel_detector_test.py
======================================

Task 05 of the Part-I open-system absorbing-boundary-condition programme.

This standalone solver performs a ZERO-AMBIENT-BATH oscillator-channel
calculation.  It replaces only the Cartesian transverse grid by the certified
complete-shell harmonic-oscillator representation.  It contains no active
environmental generator, no rate parameters, no density-matrix propagation,
no stochastic trajectories, and no finite-temperature propagation.

Implemented maps
----------------

``scalar_factorized``
    Authoritative scalar control.  The validated longitudinal scalar-ABC
    Cayley step is composed with the exact diagonal transverse unitary.  The
    roof probability is evaluated at the detector-Cayley midpoint, before the
    trace-preserving transverse phase is applied.

``scalar_monolithic``
    Diagnostic only.  One Cayley transform is applied to the complete scalar
    Kronecker-sum Hamiltonian.  Its finite-step mode dependence is a numerical
    nonfactorization artifact and is never interpreted as physical scalar
    transverse sensitivity.

``spinor``
    Coupled-channel Cayley/GMRES propagation with the projected
    spin-momentum roof term +K_N/(2 h_z).

Authority reconciliation
------------------------

The current master Task-05 handoff freezes shell-ascending order with n_x
DESCENDING inside each shell and state index

    index(s, mu, k_z) = (s*M_N + mu)*N_z + k_z.

The attached final Audit-02 source itself enumerates n_x ASCENDING and stores
K_N in orbital-tensor-spin order.  This script preserves the current Task-05
state convention and independently reconstructs the Audit-02-native matrices;
an explicit unitary permutation must make the two representations identical.
That equivalence is a mandatory pre-propagation audit.

Directory contract
------------------

All cases use the stage directory defined by ``STAGE_DIRECTORY`` under
``OUT_ROOT``.  No timestamp is created.  The filename prefix is generated
automatically from the manually selected propagator, confinement, initial mode,
shell cutoff, time step, and horizon.  Re-running the same physical case safely
replaces only files beginning with that generated prefix.

The production run is configured only through the clearly marked manual block
below.  There is deliberately no production parameter sweep and no production
CLI parameter interface.

Exit status is 0 for a completed PASS, 2 for a numerically completed case with
one or more failed scientific gates, and 1 for an uncaught execution/I-O error.
"""

from __future__ import annotations

import ast
import fcntl
import hashlib
import json
import logging
import math
import os
import platform
import shutil
import sys
import tempfile
import time
import traceback
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

import numpy as np
import scipy
import scipy.sparse as sp
import scipy.sparse.linalg as spla


# =============================================================================
# MANUAL PRODUCTION CASE CONFIGURATION
# Edit this block explicitly.  One invocation runs exactly one case.
# =============================================================================
PROPAGATOR_TYPE = "scalar_monolithic"          # scalar_factorized | scalar_monolithic | spinor
INITIAL_MODE = "10"                 # 00 | 10 | 01
OMEGA = 100.0
N_SHELL = 12
DT = 5.0e-4
T_FINAL = 10.0
OUT_ROOT = Path("[ARCHIVE_PATH]")

# Production backend.  ``cupy`` is the intended cluster backend.  ``scipy`` is
# retained for reduced local certification and small debugging calculations.
BACKEND = "cupy"                    # cupy | scipy
# =============================================================================


# CASE_PREFIX is deliberately not manually editable.  It is generated from the
# selected case parameters so that filenames can never disagree with the
# configuration that was actually propagated.
def _case_number_token(value: float) -> str:
    numeric = float(value)
    if numeric.is_integer():
        return str(int(numeric))
    mantissa, exponent = f"{numeric:.12e}".split("e")
    mantissa = mantissa.rstrip("0").rstrip(".").replace(".", "p")
    return f"{mantissa}e{int(exponent)}"


CASE_PREFIX = (
    f"{PROPAGATOR_TYPE}_omega{_case_number_token(OMEGA)}_"
    f"mode{INITIAL_MODE}_N{N_SHELL}_dt{_case_number_token(DT)}_"
    f"T{_case_number_token(T_FINAL)}"
)


# =============================================================================
# FROZEN TASK-05 CONSTANTS AND NUMERICAL CONVENTIONS
# =============================================================================
SCRIPT_VERSION = "2026-08-03-task05-oscillator-channel-detector-v1"
STAGE_NAME = "05_oscillator_channel_detector_test"
STAGE_DIRECTORY = (
    f"4531.Oscillator_channel_detector_tests_"
    f"{OMEGA:g}_{INITIAL_MODE}_{PROPAGATOR_TYPE}"
)
HBAR = 1.0
MASS = 1.0
N_Z = 1500
L_Z = 20.0
Z0 = 10.0
SIGMA_Z_AMPLITUDE = 0.5
K0 = math.pi
KAPPA = math.pi
THETA = math.pi / 6.0
PHI = 0.0
T_CUT = 3.6

GMRES_RTOL = 1.0e-8
GMRES_ATOL = 0.0
GMRES_RESTART = 30
GMRES_MAXITER = 1000
TRUE_RESIDUAL_TOL = 1.0e-8
DECOMPOSED_CLOSURE_ABS_TOL = 1.0e-11

OPERATOR_TOL = 1.0e-12
LAUNCH_TOL = 1.0e-12
# The detector map is contractive analytically.  This tolerance is only a
# numerical guard for the frozen rtol=1e-8 Krylov solve; it is not interpreted
# as a physical increase of survival.
SURVIVAL_INCREASE_TOL = 2.0e-9
ROOF_CLOSURE_REL_TOL = 1.0e-6
ROOF_CLOSURE_ABS_TOL = 5.0e-9
FINITE_TOL = 0.0

PROGRESS_EVERY = 100
CHECKPOINT_EVERY = 1000

# Selected detector-only reference times for later low-rank insertion work.
# Each value is mapped to the nearest state time and deduplicated.
INSERTION_TIMES_REQUESTED = (
    0.0,
    2.0,
    10.0 / math.pi,
    3.6,
    5.0,
    7.5,
    10.0,
    15.0,
    20.0,
)
INSERTION_CHANNEL_REL_NORM_TOL = 1.0e-13
INSERTION_CHANNEL_ABS_NORM2_TOL = 1.0e-30

# Attached-source fingerprints actually present in this authoritative input set.
SOURCE_FINGERPRINTS = {
    "master_audit_attached": "86b559aa9d277c63d3b49991d0a59e75a21286808531cc9194cb3adc42bea64f",
    "reference_750_attached": "8cf2095b2d760a0b702c930fe5690fe762d08ad7c721a8c53b5ed498d1744009",
    "stage02_archive": "0840ea0daeadf0f3557af01900239ab3ba93b72a6b582427129b3e6f18202fc2",
    "audit02_final_solver": "2ed0daf88dca64d33896d42e53d93c1e57b85d7e22391498babd4f7588b273b2",
    "stage01_archive": "e9699883149c6f45732fc392e5f3f5b37ed3c79f251c98f212ba6047389cc4f2",
    "representative_stage01_script": "eee0326442a7ddde4cc423f63c916810adec6f77202a72817db5f60f384b7dea",
    "v5_manuscript": "ccb019f44c334898729ca5efb02e2b39f25021ed1ab945aed0a82044c8448e7f",
}
HISTORICAL_750_HASH_QUOTED_BY_MASTER = (
    "815a470da8ec7664ee613f830f384050247f949dac5fa8ab4e0cfd8f331cfbfe"
)

# Integrated Cartesian recovery targets reconstructed directly from the
# Stage-01 archive arrays.  Curve-level comparison remains the Task-06 loader's
# responsibility; this table supplies per-case solver-side recovery context.
STAGE01_RECOVERY_TARGETS: Dict[Tuple[float, str, str], Dict[str, float]] = {
    (1.0, "scalar", "00"): {
        "S_T": 0.0931157856628934,
        "D_roof": 0.9068838645102115,
        "mu_restricted": 4.1272707437975935,
        "D_E": 0.5875975659103185,
        "D_L": 0.31928629859989305,
        "peak_t": 2.4585,
        "peak_g": 0.3691129104239661,
    },
    (1.0, "scalar", "10"): {
        "S_T": 0.09311579995898711,
        "D_roof": 0.9068838453812411,
        "mu_restricted": 4.127281185644603,
        "D_E": 0.5875955418784362,
        "D_L": 0.319288303502805,
        "peak_t": 2.4585,
        "peak_g": 0.3691141170236713,
    },
    (1.0, "scalar", "01"): {
        "S_T": 0.09311579952117315,
        "D_roof": 0.9068838467123368,
        "mu_restricted": 4.127281188051579,
        "D_E": 0.5875955412481808,
        "D_L": 0.31928830546415604,
        "peak_t": 2.4585,
        "peak_g": 0.3691141243511513,
    },
    (1.0, "spinor", "00"): {
        "S_T": 0.1143121326199097,
        "D_roof": 0.8856875263301943,
        "mu_restricted": 4.2576237225678835,
        "D_E": 0.576234724867885,
        "D_L": 0.30945280146230947,
        "peak_t": 2.4535,
        "peak_g": 0.3623127400860847,
    },
    (1.0, "spinor", "10"): {
        "S_T": 0.1341087080116026,
        "D_roof": 0.8658909577194089,
        "mu_restricted": 4.381659569369215,
        "D_E": 0.5653431625778238,
        "D_L": 0.3005477951415852,
        "peak_t": 2.4495,
        "peak_g": 0.3557873786525027,
    },
    (1.0, "spinor", "01"): {
        "S_T": 0.13410870819184012,
        "D_roof": 0.865890964900204,
        "mu_restricted": 4.38165959512465,
        "D_E": 0.5653431661546353,
        "D_L": 0.3005477987455686,
        "peak_t": 2.4495,
        "peak_g": 0.3557873730966175,
    },
    (100.0, "scalar", "00"): {
        "S_T": 0.09313502359710689,
        "D_roof": 0.9068645247928327,
        "mu_restricted": 4.1294292666183905,
        "D_E": 0.5870951776478446,
        "D_L": 0.3197693471449882,
        "peak_t": 2.4602500000000003,
        "peak_g": 0.3689048977227025,
    },
    (100.0, "scalar", "10"): {
        "S_T": 0.09321617361180974,
        "D_roof": 0.9067833650627991,
        "mu_restricted": 4.135608572714051,
        "D_E": 0.585648369024973,
        "D_L": 0.321134996037826,
        "peak_t": 2.46475,
        "peak_g": 0.36825292176417707,
    },
    (100.0, "scalar", "01"): {
        "S_T": 0.09321618948612354,
        "D_roof": 0.906783495983936,
        "mu_restricted": 4.135609211265487,
        "D_E": 0.5856484536512948,
        "D_L": 0.32113504233264123,
        "peak_t": 2.46475,
        "peak_g": 0.36825296731692037,
    },
    (100.0, "spinor", "00"): {
        "S_T": 0.48735905901860627,
        "D_roof": 0.5126406468542095,
        "mu_restricted": 6.603815303842914,
        "D_E": 0.36491414129567207,
        "D_L": 0.1477265055585375,
        "peak_t": 2.31875,
        "peak_g": 0.2364106415185351,
    },
    (100.0, "spinor", "10"): {
        "S_T": 0.5569724077276383,
        "D_roof": 0.4430273270426192,
        "mu_restricted": 7.183795673715866,
        "D_E": 0.28223471932437033,
        "D_L": 0.1607926077182489,
        "peak_t": 2.29475,
        "peak_g": 0.18470217446189327,
    },
    (100.0, "spinor", "01"): {
        "S_T": 0.5569724906368316,
        "D_roof": 0.4430273955210401,
        "mu_restricted": 7.183796787111437,
        "D_E": 0.2822347628541849,
        "D_L": 0.16079263266685515,
        "peak_t": 2.29475,
        "peak_g": 0.18470221717557816,
    },
}


# =============================================================================
# DATA CLASSES
# =============================================================================
@dataclass(frozen=True)
class RunConfig:
    propagator_type: str
    initial_mode: str
    omega: float
    n_shell: int
    dt: float
    t_final: float
    case_prefix: str
    out_root: Path
    backend: str

    n_z: int = N_Z
    l_z: float = L_Z
    z0: float = Z0
    sigma_z_amplitude: float = SIGMA_Z_AMPLITUDE
    k0: float = K0
    kappa: float = KAPPA
    theta: float = THETA
    phi: float = PHI
    t_cut: float = T_CUT

    progress_every: int = PROGRESS_EVERY
    checkpoint_every: int = CHECKPOINT_EVERY
    smoke_test: bool = False

    @property
    def detector_label(self) -> str:
        return "spinor" if self.propagator_type == "spinor" else "scalar"

    @property
    def stage_dir(self) -> Path:
        return self.out_root.expanduser().resolve() / STAGE_DIRECTORY

    @property
    def num_steps(self) -> int:
        return int(round(self.t_final / self.dt))


@dataclass
class OscillatorOperators:
    labels: Tuple[Tuple[int, int], ...]
    index: Dict[Tuple[int, int], int]
    a_x: sp.csr_matrix
    a_y: sp.csr_matrix
    a_x_dagger: sp.csr_matrix
    a_y_dagger: sp.csr_matrix
    n_x: sp.csr_matrix
    n_y: sp.csr_matrix
    n_perp: sp.csr_matrix
    h_perp_orbital: sp.csr_matrix
    h_perp_spinmajor: sp.csr_matrix
    k_spinmajor: sp.csr_matrix
    k_omit_spinmajor: sp.csr_matrix
    sigma_x: np.ndarray
    sigma_y: np.ndarray
    sigma_z: np.ndarray
    shell_of_mode: np.ndarray
    nx_diag: np.ndarray
    ny_diag: np.ndarray
    audit: Dict[str, Any]

    @property
    def m_modes(self) -> int:
        return len(self.labels)

    @property
    def d_channels(self) -> int:
        return 2 * self.m_modes


@dataclass
class PropagatorObjects:
    l_z: sp.csr_matrix
    z: np.ndarray
    h_z: float
    z_roof_grid: float
    hamiltonian_cpu: Optional[sp.csr_matrix]
    a_cpu: sp.csr_matrix
    b_cpu: sp.csr_matrix
    backend_a: Any
    backend_b: Any
    backend_preconditioner: Any
    transverse_phase_backend: Optional[Any]
    active_factorized_channels: Tuple[int, ...]
    roof_sign_audit: Dict[str, Any]


# =============================================================================
# GENERAL UTILITIES
# =============================================================================
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
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


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
        default=json_default,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(
            payload,
            handle,
            indent=2,
            sort_keys=True,
            allow_nan=False,
            default=json_default,
        )
        handle.write("\n")
    os.replace(tmp, path)


def atomic_save_npy(path: Path, array: np.ndarray) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("wb") as handle:
        np.save(handle, array, allow_pickle=False)
    os.replace(tmp, path)


def atomic_savez(path: Path, *, compressed: bool = False, **arrays: np.ndarray) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("wb") as handle:
        if compressed:
            np.savez_compressed(handle, **arrays)
        else:
            np.savez(handle, **arrays)
    os.replace(tmp, path)


def atomic_copy(source: Path, destination: Path) -> None:
    tmp = destination.with_name(destination.name + ".tmp")
    shutil.copy2(source, tmp)
    os.replace(tmp, destination)


def case_file(stage_dir: Path, case_prefix: str, suffix: str) -> Path:
    return stage_dir / f"{case_prefix}_{suffix}"


def sparse_max_abs(matrix: sp.spmatrix) -> float:
    matrix = matrix.tocsr()
    if matrix.nnz == 0:
        return 0.0
    return float(np.max(np.abs(matrix.data)))


def dense_max_abs(array: np.ndarray) -> float:
    if array.size == 0:
        return 0.0
    return float(np.max(np.abs(array)))


def frobenius_norm(matrix: Any) -> float:
    if sp.issparse(matrix):
        return float(np.sqrt(np.sum(np.abs(matrix.data) ** 2, dtype=np.float64)))
    return float(np.linalg.norm(np.asarray(matrix)))


def relative_error(numerator: float, denominator: float) -> float:
    return numerator if denominator == 0.0 else numerator / denominator


def ensure_finite_mapping(payload: Mapping[str, Any], path: str = "root") -> None:
    for key, value in payload.items():
        current = f"{path}.{key}"
        if isinstance(value, Mapping):
            ensure_finite_mapping(value, current)
        elif isinstance(value, (list, tuple)):
            for idx, item in enumerate(value):
                if isinstance(item, Mapping):
                    ensure_finite_mapping(item, f"{current}[{idx}]")
                elif isinstance(item, (float, np.floating)) and not np.isfinite(item):
                    raise FloatingPointError(f"Non-finite value at {current}[{idx}]")
        elif isinstance(value, (float, np.floating)) and not np.isfinite(value):
            raise FloatingPointError(f"Non-finite value at {current}")


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
# BACKEND ABSTRACTION
# =============================================================================
class NumericalBackend:
    """Minimal SciPy/CuPy abstraction for complex128 sparse GMRES."""

    def __init__(self, name: str):
        normalized = name.strip().lower()
        if normalized not in {"scipy", "cupy"}:
            raise ValueError("BACKEND must be 'scipy' or 'cupy'")
        self.name = normalized

        if normalized == "scipy":
            self.xp = np
            self.sparse = sp
            self.sparse_linalg = spla
            self.complex128 = np.complex128
            self.float64 = np.float64
            self._cp = None
        else:
            try:
                import cupy as cp
                import cupyx.scipy.sparse as cpsp
                import cupyx.scipy.sparse.linalg as cpspla
            except Exception as exc:  # pragma: no cover - depends on cluster
                raise RuntimeError(
                    "CuPy backend requested but CuPy/CUDA could not be imported. "
                    "Use BACKEND='scipy' only for reduced local tests."
                ) from exc
            self.xp = cp
            self.sparse = cpsp
            self.sparse_linalg = cpspla
            self.complex128 = cp.complex128
            self.float64 = cp.float64
            self._cp = cp

    def to_backend_array(self, array: np.ndarray) -> Any:
        if self.name == "scipy":
            return np.asarray(array, dtype=np.complex128)
        return self._cp.asarray(array, dtype=self._cp.complex128)

    def to_backend_real(self, array: np.ndarray) -> Any:
        if self.name == "scipy":
            return np.asarray(array, dtype=np.float64)
        return self._cp.asarray(array, dtype=self._cp.float64)

    def to_backend_sparse(self, matrix: sp.spmatrix) -> Any:
        csr = matrix.tocsr().astype(np.complex128)
        if self.name == "scipy":
            return csr
        cp = self._cp
        return self.sparse.csr_matrix(
            (
                cp.asarray(csr.data, dtype=cp.complex128),
                cp.asarray(csr.indices, dtype=cp.int32),
                cp.asarray(csr.indptr, dtype=cp.int32),
            ),
            shape=csr.shape,
            dtype=cp.complex128,
        )

    def to_cpu(self, array: Any) -> np.ndarray:
        if self.name == "scipy":
            return np.asarray(array)
        return self._cp.asnumpy(array)

    def scalar_float(self, value: Any) -> float:
        if self.name == "scipy":
            return float(value)
        return float(self._cp.asnumpy(value))

    def norm(self, vector: Any) -> float:
        return self.scalar_float(self.xp.linalg.norm(vector))

    def abs2_sum(self, array: Any) -> float:
        density = array.real * array.real + array.imag * array.imag
        return self.scalar_float(self.xp.sum(density, dtype=self.float64))

    def make_diagonal_preconditioner(self, matrix: Any) -> Any:
        inv_diag = 1.0 / matrix.diagonal()
        if self.name == "scipy":
            return self.sparse_linalg.LinearOperator(
                matrix.shape,
                matvec=lambda vector: inv_diag * vector,
                dtype=np.complex128,
            )
        return self.sparse_linalg.LinearOperator(
            shape=matrix.shape,
            matvec=lambda vector: inv_diag * vector,
        )

    def gmres(
        self,
        matrix: Any,
        rhs: Any,
        *,
        x0: Any,
        preconditioner: Any,
    ) -> Tuple[Any, int]:
        solution, info = self.sparse_linalg.gmres(
            matrix,
            rhs,
            x0=x0,
            rtol=GMRES_RTOL,
            atol=GMRES_ATOL,
            restart=GMRES_RESTART,
            maxiter=GMRES_MAXITER,
            M=preconditioner,
        )
        return solution, int(info)

    def synchronize(self) -> None:
        if self.name == "cupy":
            self._cp.cuda.Stream.null.synchronize()

    def metadata(self) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {
            "backend": self.name,
            "python": sys.version,
            "platform": platform.platform(),
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
        }
        if self.name == "cupy":
            cp = self._cp
            metadata["cupy_version"] = cp.__version__
            try:
                device_id = int(cp.cuda.runtime.getDevice())
                props = cp.cuda.runtime.getDeviceProperties(device_id)
                name = props.get("name", "unknown")
                if isinstance(name, bytes):
                    name = name.decode("utf-8", errors="replace")
                _free_mem, total_mem = cp.cuda.Device(device_id).mem_info
                metadata.update(
                    {
                        "cuda_device_id": device_id,
                        "cuda_device_name": str(name),
                        "cuda_compute_capability": [
                            int(props.get("major", -1)),
                            int(props.get("minor", -1)),
                        ],
                        "cuda_total_memory_bytes": int(total_mem),
                        "cuda_driver_version": int(cp.cuda.runtime.driverGetVersion()),
                        "cuda_runtime_version": int(cp.cuda.runtime.runtimeGetVersion()),
                    }
                )
            except Exception as exc:  # pragma: no cover - depends on cluster
                metadata["cuda_metadata_error"] = repr(exc)
        return metadata


# =============================================================================
# CONFIGURATION AND SOURCE-GUARD AUDITS
# =============================================================================
def manual_run_config() -> RunConfig:
    return RunConfig(
        propagator_type=PROPAGATOR_TYPE,
        initial_mode=INITIAL_MODE,
        omega=float(OMEGA),
        n_shell=int(N_SHELL),
        dt=float(DT),
        t_final=float(T_FINAL),
        case_prefix=str(CASE_PREFIX),
        out_root=Path(OUT_ROOT),
        backend=str(BACKEND),
    )


def validate_config(config: RunConfig) -> None:
    if config.propagator_type not in {
        "scalar_factorized",
        "scalar_monolithic",
        "spinor",
    }:
        raise ValueError(
            "PROPAGATOR_TYPE must be scalar_factorized, scalar_monolithic, or spinor"
        )
    if config.initial_mode not in {"00", "10", "01"}:
        raise ValueError("INITIAL_MODE must be one of 00, 10, 01")
    if not np.isfinite(config.omega) or config.omega <= 0.0:
        raise ValueError("OMEGA must be finite and positive")
    if config.n_shell < 1:
        raise ValueError("N_SHELL must be at least 1 for the required mode set")
    nx0, ny0 = parse_initial_mode(config.initial_mode)
    if nx0 + ny0 > config.n_shell:
        raise ValueError("INITIAL_MODE is outside the selected complete-shell cutoff")
    if not np.isfinite(config.dt) or config.dt <= 0.0:
        raise ValueError("DT must be finite and positive")
    if not np.isfinite(config.t_final) or config.t_final <= 0.0:
        raise ValueError("T_FINAL must be finite and positive")
    if not np.isclose(config.num_steps * config.dt, config.t_final, rtol=0.0, atol=1e-12):
        raise ValueError("T_FINAL/DT must be integral within absolute tolerance 1e-12")
    if config.n_z < 4:
        raise ValueError("n_z must be at least 4")
    if not np.isfinite(config.l_z) or config.l_z <= 0.0:
        raise ValueError("l_z must be finite and positive")
    if not config.case_prefix or config.case_prefix in {".", ".."}:
        raise ValueError("CASE_PREFIX must be nonempty")
    if any(character in config.case_prefix for character in ("/", "\\", "\x00")):
        raise ValueError("CASE_PREFIX must not contain path separators or NUL")
    if config.backend not in {"scipy", "cupy"}:
        raise ValueError("BACKEND must be scipy or cupy")
    if config.progress_every <= 0 or config.checkpoint_every <= 0:
        raise ValueError("Progress and checkpoint cadences must be positive")


def audit_prohibited_dynamics_absent(script_path: Path) -> Dict[str, Any]:
    """AST audit: executable symbols for excluded dynamics must be absent.

    Comments and docstrings are intentionally ignored; only imports, assigned
    names, loaded names, and callable/function identifiers are inspected.
    """

    source = script_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(script_path))

    executable_names: set[str] = set()
    imported_modules: set[str] = set()
    callable_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            executable_names.add(node.id.lower())
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            callable_names.add(node.name.lower())
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name.lower())
        elif isinstance(node, ast.ImportFrom):
            imported_modules.add((node.module or "").lower())

    forbidden_exact_names = {
        "gamma_down",
        "gamma_up",
        "gamma_phi",
        "gamma_downarrow",
        "gamma_uparrow",
        "bath_temperature",
        "density_matrix",
        "lindblad_generator",
        "monte_carlo",
        "quantum_trajectory",
    }
    forbidden_callable_fragments = (
        "lindblad",
        "dissipator",
        "density_matrix",
        "monte_carlo",
        "trajectory",
        "finite_temperature",
    )
    forbidden_import_fragments = ("qutip",)

    found_names = sorted(forbidden_exact_names.intersection(executable_names))
    found_callables = sorted(
        name
        for name in callable_names
        if any(fragment in name for fragment in forbidden_callable_fragments)
    )
    found_imports = sorted(
        module
        for module in imported_modules
        if any(fragment in module for fragment in forbidden_import_fragments)
    )

    passed = not found_names and not found_callables and not found_imports
    return {
        "method": "Python AST executable-symbol audit; comments and docstrings excluded",
        "forbidden_exact_executable_names_found": found_names,
        "forbidden_callable_names_found": found_callables,
        "forbidden_imports_found": found_imports,
        "active_environmental_or_density_matrix_code_absent": passed,
    }


# =============================================================================
# COMPLETE-SHELL OSCILLATOR OPERATORS
# =============================================================================
def complete_shell_labels_descending(n_shell: int) -> Tuple[Tuple[int, int], ...]:
    labels: List[Tuple[int, int]] = []
    for total in range(n_shell + 1):
        for nx in range(total, -1, -1):
            labels.append((nx, total - nx))
    return tuple(labels)


def complete_shell_labels_audit02_native(n_shell: int) -> Tuple[Tuple[int, int], ...]:
    """Literal ordering in the attached final Audit-02 source."""
    labels: List[Tuple[int, int]] = []
    for total in range(n_shell + 1):
        for nx in range(total + 1):
            labels.append((nx, total - nx))
    return tuple(labels)


def build_projected_ladders(
    labels: Tuple[Tuple[int, int], ...]
) -> Tuple[sp.csr_matrix, sp.csr_matrix, Dict[Tuple[int, int], int]]:
    index = {label: position for position, label in enumerate(labels)}
    rows_x: List[int] = []
    cols_x: List[int] = []
    data_x: List[complex] = []
    rows_y: List[int] = []
    cols_y: List[int] = []
    data_y: List[complex] = []

    for column, (nx, ny) in enumerate(labels):
        if nx > 0:
            rows_x.append(index[(nx - 1, ny)])
            cols_x.append(column)
            data_x.append(math.sqrt(nx))
        if ny > 0:
            rows_y.append(index[(nx, ny - 1)])
            cols_y.append(column)
            data_y.append(math.sqrt(ny))

    dimension = len(labels)
    a_x = sp.csr_matrix(
        (np.asarray(data_x, dtype=np.complex128), (rows_x, cols_x)),
        shape=(dimension, dimension),
        dtype=np.complex128,
    )
    a_y = sp.csr_matrix(
        (np.asarray(data_y, dtype=np.complex128), (rows_y, cols_y)),
        shape=(dimension, dimension),
        dtype=np.complex128,
    )
    return a_x, a_y, index


def basis_vector(dimension: int, index: int) -> np.ndarray:
    vector = np.zeros(dimension, dtype=np.complex128)
    vector[index] = 1.0
    return vector


def orbital_permutation(
    source_labels: Sequence[Tuple[int, int]],
    target_labels: Sequence[Tuple[int, int]],
) -> sp.csr_matrix:
    """Return P such that v_target = P v_source."""
    source_index = {label: idx for idx, label in enumerate(source_labels)}
    rows = np.arange(len(target_labels), dtype=np.int32)
    cols = np.asarray([source_index[label] for label in target_labels], dtype=np.int32)
    data = np.ones(len(target_labels), dtype=np.complex128)
    return sp.csr_matrix((data, (rows, cols)), shape=(len(target_labels), len(source_labels)))


def audit02_to_task05_tensor_permutation(
    native_labels: Sequence[Tuple[int, int]],
    task05_labels: Sequence[Tuple[int, int]],
) -> sp.csr_matrix:
    """Map Audit-02 (orbital, spin-fast) to Task-05 (spin, orbital)."""
    native_index = {label: idx for idx, label in enumerate(native_labels)}
    task_index = {label: idx for idx, label in enumerate(task05_labels)}
    m_modes = len(task05_labels)
    rows: List[int] = []
    cols: List[int] = []
    data: List[complex] = []
    for label in task05_labels:
        mu_task = task_index[label]
        mu_native = native_index[label]
        for spin in range(2):
            rows.append(spin * m_modes + mu_task)
            cols.append(mu_native * 2 + spin)
            data.append(1.0)
    return sp.csr_matrix(
        (np.asarray(data, dtype=np.complex128), (rows, cols)),
        shape=(2 * m_modes, 2 * m_modes),
    )


def build_omitted_raising(
    labels: Sequence[Tuple[int, int]],
    n_shell: int,
    axis: str,
) -> sp.csr_matrix:
    """Q_{N+1} a_axis^dagger P_N from the retained space to shell N+1."""
    if axis not in {"x", "y"}:
        raise ValueError("axis must be x or y")
    retained_index = {label: idx for idx, label in enumerate(labels)}
    omitted_labels = tuple((nx, n_shell + 1 - nx) for nx in range(n_shell + 1, -1, -1))
    omitted_index = {label: idx for idx, label in enumerate(omitted_labels)}

    rows: List[int] = []
    cols: List[int] = []
    data: List[complex] = []
    for nx, ny in labels:
        if nx + ny != n_shell:
            continue
        source = retained_index[(nx, ny)]
        if axis == "x":
            target = (nx + 1, ny)
            coefficient = math.sqrt(nx + 1)
        else:
            target = (nx, ny + 1)
            coefficient = math.sqrt(ny + 1)
        rows.append(omitted_index[target])
        cols.append(source)
        data.append(coefficient)

    return sp.csr_matrix(
        (np.asarray(data, dtype=np.complex128), (rows, cols)),
        shape=(n_shell + 2, len(labels)),
        dtype=np.complex128,
    )


def explicit_spinmajor_k_action(
    vector: np.ndarray,
    *,
    a_x: sp.csr_matrix,
    a_y: sp.csr_matrix,
    omega: float,
    sigma_x: np.ndarray,
    sigma_y: np.ndarray,
) -> np.ndarray:
    """Independent array-level action for the Task-05 spin-major K matrix."""
    m_modes = a_x.shape[0]
    spin_orbital = np.asarray(vector, dtype=np.complex128).reshape(2, m_modes)
    ell_perp = math.sqrt(HBAR / (MASS * omega))
    delta_x = a_x.getH() - a_x
    delta_y = a_y.getH() - a_y

    orbital_y = np.vstack([delta_y @ spin_orbital[0], delta_y @ spin_orbital[1]])
    orbital_x = np.vstack([delta_x @ spin_orbital[0], delta_x @ spin_orbital[1]])
    result = sigma_x @ orbital_y - sigma_y @ orbital_x
    return (1j / (math.sqrt(2.0) * ell_perp) * result).reshape(-1)


def build_oscillator_operators(n_shell: int, omega: float) -> OscillatorOperators:
    labels = complete_shell_labels_descending(n_shell)
    expected_dimension = (n_shell + 1) * (n_shell + 2) // 2
    if len(labels) != expected_dimension:
        raise RuntimeError("Complete-shell dimension formula failed")

    a_x, a_y, index = build_projected_ladders(labels)
    a_x_dagger = a_x.getH().tocsr()
    a_y_dagger = a_y.getH().tocsr()
    n_x = (a_x_dagger @ a_x).tocsr()
    n_y = (a_y_dagger @ a_y).tocsr()
    n_perp = (n_x + n_y).tocsr()
    identity_orb = sp.eye(expected_dimension, dtype=np.complex128, format="csr")

    nx_diag = np.asarray([nx for nx, _ in labels], dtype=np.float64)
    ny_diag = np.asarray([ny for _, ny in labels], dtype=np.float64)
    shell_of_mode = nx_diag.astype(np.int64) + ny_diag.astype(np.int64)

    h_perp_orbital = (
        HBAR * omega * (n_x + n_y + identity_orb)
    ).tocsr()

    sigma_x = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    sigma_y = np.asarray([[0.0, -1j], [1j, 0.0]], dtype=np.complex128)
    sigma_z = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    sx = sp.csr_matrix(sigma_x)
    sy = sp.csr_matrix(sigma_y)
    identity_spin = sp.eye(2, dtype=np.complex128, format="csr")

    h_perp_spinmajor = sp.kron(identity_spin, h_perp_orbital, format="csr")
    ell_perp = math.sqrt(HBAR / (MASS * omega))
    momentum_x = (
        1j * HBAR / (math.sqrt(2.0) * ell_perp) * (a_x_dagger - a_x)
    ).tocsr()
    momentum_y = (
        1j * HBAR / (math.sqrt(2.0) * ell_perp) * (a_y_dagger - a_y)
    ).tocsr()
    k_ladder = (
        1j
        / (math.sqrt(2.0) * ell_perp)
        * (
            sp.kron(sx, a_y_dagger - a_y, format="csr")
            - sp.kron(sy, a_x_dagger - a_x, format="csr")
        )
    ).tocsr()
    k_momentum = (
        sp.kron(sx, momentum_y / HBAR, format="csr")
        - sp.kron(sy, momentum_x / HBAR, format="csr")
    ).tocsr()

    omitted_raise_x = build_omitted_raising(labels, n_shell, "x")
    omitted_raise_y = build_omitted_raising(labels, n_shell, "y")
    k_omit_spinmajor = (
        1j
        / (math.sqrt(2.0) * ell_perp)
        * (
            sp.kron(sx, omitted_raise_y, format="csr")
            - sp.kron(sy, omitted_raise_x, format="csr")
        )
    ).tocsr()

    # ------------------------------------------------------------------
    # Mandatory operator audits.
    # ------------------------------------------------------------------
    ordering_expected = []
    for total in range(n_shell + 1):
        ordering_expected.extend((nx, total - nx) for nx in range(total, -1, -1))
    ordering_pass = tuple(ordering_expected) == labels

    lowering_residuals: List[float] = []
    raising_residuals: List[float] = []
    top_raising_norms: List[float] = []
    for nx_value, ny_value in labels:
        source = basis_vector(expected_dimension, index[(nx_value, ny_value)])
        for axis, occupation, lower, raise_op in (
            ("x", nx_value, a_x, a_x_dagger),
            ("y", ny_value, a_y, a_y_dagger),
        ):
            expected_lower = np.zeros(expected_dimension, dtype=np.complex128)
            if occupation > 0:
                target = (nx_value - 1, ny_value) if axis == "x" else (nx_value, ny_value - 1)
                expected_lower[index[target]] = math.sqrt(occupation)
            lowering_residuals.append(float(np.linalg.norm(lower @ source - expected_lower)))

            if nx_value + ny_value < n_shell:
                expected_raise = np.zeros(expected_dimension, dtype=np.complex128)
                target = (nx_value + 1, ny_value) if axis == "x" else (nx_value, ny_value + 1)
                expected_raise[index[target]] = math.sqrt(occupation + 1)
                raising_residuals.append(float(np.linalg.norm(raise_op @ source - expected_raise)))
            else:
                top_raising_norms.append(float(np.linalg.norm(raise_op @ source)))

    adjoint_x = sparse_max_abs(a_x_dagger - a_x.getH())
    adjoint_y = sparse_max_abs(a_y_dagger - a_y.getH())
    number_x_exact = sp.diags(nx_diag, 0, dtype=np.complex128, format="csr")
    number_y_exact = sp.diags(ny_diag, 0, dtype=np.complex128, format="csr")
    number_x_residual = sparse_max_abs(n_x - number_x_exact)
    number_y_residual = sparse_max_abs(n_y - number_y_exact)
    minimum_number_eigenvalue = min(
        float(np.min(np.linalg.eigvalsh(n_x.toarray()))),
        float(np.min(np.linalg.eigvalsh(n_y.toarray()))),
    )
    h_perp_residual = sparse_max_abs(
        h_perp_orbital - HBAR * omega * (number_x_exact + number_y_exact + identity_orb)
    )

    # Exact complete-shell commutator defects from the final Audit-02 source.
    # A finite-dimensional projected oscillator cannot satisfy [a,a^dagger]=I
    # on the complete retained space.  The missing canonical weight is
    # supported on the upper shell and must be audited explicitly.
    comm_x = (a_x @ a_x_dagger - a_x_dagger @ a_x).tocsr()
    comm_y = (a_y @ a_y_dagger - a_y_dagger @ a_y).tocsr()
    expected_comm_x_diag = np.ones(expected_dimension, dtype=np.float64)
    expected_comm_y_diag = np.ones(expected_dimension, dtype=np.float64)
    for position, (nx_value, ny_value) in enumerate(labels):
        if nx_value + ny_value == n_shell:
            expected_comm_x_diag[position] -= nx_value + 1
            expected_comm_y_diag[position] -= ny_value + 1
    expected_comm_x = sp.diags(
        expected_comm_x_diag, 0, dtype=np.complex128, format="csr"
    )
    expected_comm_y = sp.diags(
        expected_comm_y_diag, 0, dtype=np.complex128, format="csr"
    )

    comm_ax_ay = (a_x @ a_y - a_y @ a_x).tocsr()
    comm_axdag_aydag = (
        a_x_dagger @ a_y_dagger - a_y_dagger @ a_x_dagger
    ).tocsr()
    comm_ax_aydag = (a_x @ a_y_dagger - a_y_dagger @ a_x).tocsr()
    comm_ay_axdag = (a_y @ a_x_dagger - a_x_dagger @ a_y).tocsr()

    cross_rows_xy: List[int] = []
    cross_cols_xy: List[int] = []
    cross_data_xy: List[complex] = []
    cross_rows_yx: List[int] = []
    cross_cols_yx: List[int] = []
    cross_data_yx: List[complex] = []
    for nx_value, ny_value in labels:
        if nx_value + ny_value != n_shell:
            continue
        column = index[(nx_value, ny_value)]
        if nx_value > 0:
            cross_rows_xy.append(index[(nx_value - 1, ny_value + 1)])
            cross_cols_xy.append(column)
            cross_data_xy.append(-math.sqrt(nx_value * (ny_value + 1)))
        if ny_value > 0:
            cross_rows_yx.append(index[(nx_value + 1, ny_value - 1)])
            cross_cols_yx.append(column)
            cross_data_yx.append(-math.sqrt(ny_value * (nx_value + 1)))
    expected_comm_ax_aydag = sp.csr_matrix(
        (
            np.asarray(cross_data_xy, dtype=np.complex128),
            (cross_rows_xy, cross_cols_xy),
        ),
        shape=(expected_dimension, expected_dimension),
        dtype=np.complex128,
    )
    expected_comm_ay_axdag = sp.csr_matrix(
        (
            np.asarray(cross_data_yx, dtype=np.complex128),
            (cross_rows_yx, cross_cols_yx),
        ),
        shape=(expected_dimension, expected_dimension),
        dtype=np.complex128,
    )
    number_ladder_commutator_residuals = (
        (n_x @ a_x - a_x @ n_x + a_x).tocsr(),
        (n_x @ a_x_dagger - a_x_dagger @ n_x - a_x_dagger).tocsr(),
        (n_y @ a_y - a_y @ n_y + a_y).tocsr(),
        (n_y @ a_y_dagger - a_y_dagger @ n_y - a_y_dagger).tocsr(),
        (n_x @ a_y - a_y @ n_x).tocsr(),
        (n_y @ a_x - a_x @ n_y).tocsr(),
    )
    projected_commutator_residual = max(
        sparse_max_abs(comm_x - expected_comm_x),
        sparse_max_abs(comm_y - expected_comm_y),
        sparse_max_abs(comm_ax_ay),
        sparse_max_abs(comm_axdag_aydag),
        sparse_max_abs(comm_ax_aydag - expected_comm_ax_aydag),
        sparse_max_abs(comm_ay_axdag - expected_comm_ay_axdag),
        max(
            (sparse_max_abs(residual) for residual in number_ladder_commutator_residuals),
            default=0.0,
        ),
    )

    bohr_pairs = (
        (
            h_perp_orbital @ a_x
            - a_x @ h_perp_orbital
            + HBAR * omega * a_x,
            HBAR * omega * a_x,
        ),
        (
            h_perp_orbital @ a_y
            - a_y @ h_perp_orbital
            + HBAR * omega * a_y,
            HBAR * omega * a_y,
        ),
        (
            h_perp_orbital @ a_x_dagger
            - a_x_dagger @ h_perp_orbital
            - HBAR * omega * a_x_dagger,
            HBAR * omega * a_x_dagger,
        ),
        (
            h_perp_orbital @ a_y_dagger
            - a_y_dagger @ h_perp_orbital
            - HBAR * omega * a_y_dagger,
            HBAR * omega * a_y_dagger,
        ),
    )
    bohr_absolute_residual = max(
        (sparse_max_abs(residual) for residual, _ in bohr_pairs),
        default=0.0,
    )
    bohr_relative_residual = max(
        (
            frobenius_norm(residual)
            / max(frobenius_norm(reference), 1.0)
            for residual, reference in bohr_pairs
        ),
        default=0.0,
    )

    k_hermiticity = sparse_max_abs(k_ladder - k_ladder.getH())
    k_formula = sparse_max_abs(k_ladder - k_momentum)

    ell_unit = math.sqrt(HBAR / MASS)
    k_at_unit_omega = (
        1j
        / (math.sqrt(2.0) * ell_unit)
        * (
            sp.kron(sx, a_y_dagger - a_y, format="csr")
            - sp.kron(sy, a_x_dagger - a_x, format="csr")
        )
    ).tocsr()
    k_scale = sparse_max_abs(k_ladder / math.sqrt(omega) - k_at_unit_omega)

    pauli_audits = {
        "sigma_x_hermiticity": dense_max_abs(sigma_x - sigma_x.conj().T),
        "sigma_y_hermiticity": dense_max_abs(sigma_y - sigma_y.conj().T),
        "sigma_z_hermiticity": dense_max_abs(sigma_z - sigma_z.conj().T),
        "sigma_x_squared_minus_I": dense_max_abs(sigma_x @ sigma_x - np.eye(2)),
        "sigma_y_squared_minus_I": dense_max_abs(sigma_y @ sigma_y - np.eye(2)),
        "sigma_z_squared_minus_I": dense_max_abs(sigma_z @ sigma_z - np.eye(2)),
        "sigma_x_sigma_y_commutator_minus_2i_sigma_z": dense_max_abs(
            sigma_x @ sigma_y - sigma_y @ sigma_x - 2j * sigma_z
        ),
    }

    rng = np.random.default_rng(20260803)
    random_vector = rng.normal(size=2 * expected_dimension) + 1j * rng.normal(
        size=2 * expected_dimension
    )
    explicit_k = explicit_spinmajor_k_action(
        random_vector,
        a_x=a_x,
        a_y=a_y,
        omega=omega,
        sigma_x=sigma_x,
        sigma_y=sigma_y,
    )
    k_action_residual = float(np.linalg.norm(k_ladder @ random_vector - explicit_k))

    # Reconstruct the literal Audit-02 source ordering/formula and compare by
    # explicit permutation to the current Task-05 convention.
    native_labels = complete_shell_labels_audit02_native(n_shell)
    native_ax, native_ay, _ = build_projected_ladders(native_labels)
    native_adx = native_ax.getH().tocsr()
    native_ady = native_ay.getH().tocsr()
    p_orb = orbital_permutation(native_labels, labels)
    orbital_ax_permutation_residual = sparse_max_abs(a_x - p_orb @ native_ax @ p_orb.getH())
    orbital_ay_permutation_residual = sparse_max_abs(a_y - p_orb @ native_ay @ p_orb.getH())

    native_k_orbital_spin = (
        1j
        / (math.sqrt(2.0) * ell_perp)
        * (
            sp.kron(native_ady - native_ay, sx, format="csr")
            - sp.kron(native_adx - native_ax, sy, format="csr")
        )
    ).tocsr()
    p_tensor = audit02_to_task05_tensor_permutation(native_labels, labels)
    audit02_k_permutation_residual = sparse_max_abs(
        k_ladder - p_tensor @ native_k_orbital_spin @ p_tensor.getH()
    )
    tensor_permutation_unitarity = sparse_max_abs(
        p_tensor @ p_tensor.getH()
        - sp.eye(2 * expected_dimension, dtype=np.complex128, format="csr")
    )

    tensor_index_checks: List[Dict[str, int]] = []
    for spin in range(2):
        for mu in (0, expected_dimension // 2, expected_dimension - 1):
            index_formula = spin * expected_dimension + mu
            basis = np.zeros((2, expected_dimension), dtype=np.complex128)
            basis[spin, mu] = 1.0
            raveled = int(np.argmax(np.abs(basis.reshape(-1))))
            tensor_index_checks.append(
                {
                    "spin": spin,
                    "mu": mu,
                    "formula_index": index_formula,
                    "raveled_index": raveled,
                }
            )
    tensor_order_pass = all(
        item["formula_index"] == item["raveled_index"] for item in tensor_index_checks
    )

    expected_orbital_shape = (expected_dimension, expected_dimension)
    expected_channel_shape = (2 * expected_dimension, 2 * expected_dimension)
    shape_and_dtype_pass = bool(
        all(
            matrix.shape == expected_orbital_shape
            and matrix.dtype == np.dtype(np.complex128)
            for matrix in (
                a_x,
                a_y,
                a_x_dagger,
                a_y_dagger,
                n_x,
                n_y,
                n_perp,
                h_perp_orbital,
            )
        )
        and h_perp_spinmajor.shape == expected_channel_shape
        and k_ladder.shape == expected_channel_shape
        and h_perp_spinmajor.dtype == np.dtype(np.complex128)
        and k_ladder.dtype == np.dtype(np.complex128)
    )

    # Independent finite-shell source-norm identities used later during
    # detector-only propagation.
    identity_spin_sparse = sp.eye(2, dtype=np.complex128, format="csr")
    ax_channel = sp.kron(identity_spin_sparse, a_x, format="csr")
    ay_channel = sp.kron(identity_spin_sparse, a_y, format="csr")
    axd_channel = sp.kron(identity_spin_sparse, a_x_dagger, format="csr")
    ayd_channel = sp.kron(identity_spin_sparse, a_y_dagger, format="csr")
    nperp_channel = sp.kron(identity_spin_sparse, n_perp, format="csr")
    top_projector_orbital = sp.diags(
        (shell_of_mode == n_shell).astype(np.float64),
        0,
        dtype=np.complex128,
        format="csr",
    )
    top_projector_channel = sp.kron(
        identity_spin_sparse, top_projector_orbital, format="csr"
    )
    random_source_state = random_vector / np.linalg.norm(random_vector)
    direct_down_norm = float(
        np.vdot(ax_channel @ random_source_state, ax_channel @ random_source_state).real
        + np.vdot(ay_channel @ random_source_state, ay_channel @ random_source_state).real
    )
    formula_down_norm = float(
        np.vdot(random_source_state, nperp_channel @ random_source_state).real
    )
    direct_up_norm = float(
        np.vdot(axd_channel @ random_source_state, axd_channel @ random_source_state).real
        + np.vdot(ayd_channel @ random_source_state, ayd_channel @ random_source_state).real
    )
    identity_channel_sparse = sp.eye(
        2 * expected_dimension, dtype=np.complex128, format="csr"
    )
    formula_up_operator = (
        nperp_channel
        + 2.0 * identity_channel_sparse
        - (n_shell + 2.0) * top_projector_channel
    ).tocsr()
    formula_up_norm = float(
        np.vdot(random_source_state, formula_up_operator @ random_source_state).real
    )
    source_down_formula_relative_residual = relative_error(
        abs(direct_down_norm - formula_down_norm),
        max(abs(formula_down_norm), 1.0),
    )
    source_up_formula_relative_residual = relative_error(
        abs(direct_up_norm - formula_up_norm),
        max(abs(formula_up_norm), 1.0),
    )
    probability_orbital = (
        np.abs(random_source_state.reshape(2, expected_dimension)) ** 2
    ).sum(axis=0)
    random_nx_mean = float(np.dot(probability_orbital, nx_diag))
    random_ny_mean = float(np.dot(probability_orbital, ny_diag))
    random_s_phi = float(
        np.dot(probability_orbital, nx_diag**2) - random_nx_mean**2
        + np.dot(probability_orbital, ny_diag**2) - random_ny_mean**2
    )

    exact_launch = {
        "mode00_Nx": float(nx_diag[index[(0, 0)]]),
        "mode00_Ny": float(ny_diag[index[(0, 0)]]),
        "mode10_Nx": float(nx_diag[index[(1, 0)]]),
        "mode10_Ny": float(ny_diag[index[(1, 0)]]),
        "mode01_Nx": float(nx_diag[index[(0, 1)]]),
        "mode01_Ny": float(ny_diag[index[(0, 1)]]),
    }

    metrics = {
        "dimension_formula_residual": abs(len(labels) - expected_dimension),
        "ordering_exact": ordering_pass,
        "maximum_lowering_action_residual": max(lowering_residuals, default=0.0),
        "maximum_interior_raising_action_residual": max(raising_residuals, default=0.0),
        "maximum_top_shell_projected_raising_norm": max(top_raising_norms, default=0.0),
        "adjoint_x_residual": adjoint_x,
        "adjoint_y_residual": adjoint_y,
        "number_x_diagonal_residual": number_x_residual,
        "number_y_diagonal_residual": number_y_residual,
        "minimum_number_operator_eigenvalue": minimum_number_eigenvalue,
        "H_perp_formula_residual": h_perp_residual,
        "maximum_exact_projected_commutator_residual": projected_commutator_residual,
        "maximum_oscillator_Bohr_relation_absolute_residual": bohr_absolute_residual,
        "maximum_oscillator_Bohr_relation_relative_residual": bohr_relative_residual,
        "K_hermiticity_residual": k_hermiticity,
        "K_ladder_momentum_formula_residual": k_formula,
        "K_sqrt_omega_proportionality_residual": k_scale,
        "K_explicit_spinmajor_action_residual": k_action_residual,
        "audit02_orbital_ax_permutation_residual": orbital_ax_permutation_residual,
        "audit02_orbital_ay_permutation_residual": orbital_ay_permutation_residual,
        "audit02_K_tensor_permutation_residual": audit02_k_permutation_residual,
        "audit02_to_task05_permutation_unitarity_residual": tensor_permutation_unitarity,
        "tensor_order_index_formula_exact": tensor_order_pass,
        "matrix_shapes_and_complex128_dtypes_exact": shape_and_dtype_pass,
        "source_down_norm_formula_relative_residual": source_down_formula_relative_residual,
        "source_up_norm_formula_relative_residual": source_up_formula_relative_residual,
        "random_state_s_phi": random_s_phi,
    }
    metrics.update(pauli_audits)

    checks = {
        "complete_shell_dimension_and_ordering": bool(
            metrics["dimension_formula_residual"] == 0 and ordering_pass
        ),
        "ladder_actions": bool(
            max(
                metrics["maximum_lowering_action_residual"],
                metrics["maximum_interior_raising_action_residual"],
                metrics["maximum_top_shell_projected_raising_norm"],
            )
            <= OPERATOR_TOL
        ),
        "adjoint_identities": bool(max(adjoint_x, adjoint_y) <= OPERATOR_TOL),
        "number_operator_positivity_and_diagonal": bool(
            minimum_number_eigenvalue >= -OPERATOR_TOL
            and max(number_x_residual, number_y_residual) <= OPERATOR_TOL
        ),
        "H_perp_construction": bool(h_perp_residual <= OPERATOR_TOL),
        "exact_projected_commutators_and_Bohr_relations": bool(
            projected_commutator_residual <= OPERATOR_TOL
            and bohr_relative_residual <= OPERATOR_TOL
        ),
        "K_hermiticity": bool(k_hermiticity <= OPERATOR_TOL),
        "K_ladder_momentum_formula": bool(k_formula <= OPERATOR_TOL),
        "K_sqrt_omega_proportionality": bool(k_scale <= OPERATOR_TOL),
        "Pauli_matrices": bool(max(pauli_audits.values()) <= OPERATOR_TOL),
        "tensor_ordering": bool(tensor_order_pass and k_action_residual <= OPERATOR_TOL),
        "matrix_dimensions_and_dtypes": shape_and_dtype_pass,
        "source_norm_formulas": bool(
            max(
                source_down_formula_relative_residual,
                source_up_formula_relative_residual,
            )
            <= OPERATOR_TOL
            and random_s_phi >= -OPERATOR_TOL
        ),
        "audit02_physical_equivalence_under_explicit_permutation": bool(
            max(
                orbital_ax_permutation_residual,
                orbital_ay_permutation_residual,
                audit02_k_permutation_residual,
                tensor_permutation_unitarity,
            )
            <= OPERATOR_TOL
        ),
    }
    all_checks_pass = all(checks.values())

    audit: Dict[str, Any] = {
        "representation": "orthonormal_complete_shell_oscillator_basis",
        "task05_mode_order": [[nx, ny] for nx, ny in labels],
        "task05_ordering_rule": "shell ascending; n_x descending within each shell",
        "task05_channel_order": "physical spin major, oscillator mode minor",
        "task05_full_state_order": "index(s,mu,k_z)=(s*M_N+mu)*N_z+k_z; z fastest",
        "audit02_native_mode_order": [[nx, ny] for nx, ny in native_labels],
        "audit02_native_ordering_rule": (
            "literal final Audit-02 source: shell ascending; n_x ascending within shell"
        ),
        "audit02_native_K_order": "orbital complete-shell basis tensor physical spin",
        "authority_conflict_resolution": (
            "The master Task-05 handoff and current explicit requirement freeze n_x-descending "
            "and spin-major storage.  The final Audit-02 source is reconstructed in its literal "
            "native ordering and related to the Task-05 matrices by an explicit unitary permutation."
        ),
        "dimension": expected_dimension,
        "spin_resolved_channel_dimension": 2 * expected_dimension,
        "metrics": metrics,
        "checks": checks,
        "all_checks_passed": all_checks_pass,
        "tensor_index_samples": tensor_index_checks,
        "Pauli_matrices": {
            "sigma_x": {"real": sigma_x.real.tolist(), "imag": sigma_x.imag.tolist()},
            "sigma_y": {"real": sigma_y.real.tolist(), "imag": sigma_y.imag.tolist()},
            "sigma_z": {"real": sigma_z.real.tolist(), "imag": sigma_z.imag.tolist()},
        },
        "low_mode_number_controls": exact_launch,
    }

    return OscillatorOperators(
        labels=labels,
        index=index,
        a_x=a_x,
        a_y=a_y,
        a_x_dagger=a_x_dagger,
        a_y_dagger=a_y_dagger,
        n_x=n_x,
        n_y=n_y,
        n_perp=n_perp,
        h_perp_orbital=h_perp_orbital,
        h_perp_spinmajor=h_perp_spinmajor,
        k_spinmajor=k_ladder,
        k_omit_spinmajor=k_omit_spinmajor,
        sigma_x=sigma_x,
        sigma_y=sigma_y,
        sigma_z=sigma_z,
        shell_of_mode=shell_of_mode,
        nx_diag=nx_diag,
        ny_diag=ny_diag,
        audit=audit,
    )


# =============================================================================
# LONGITUDINAL GRID, PACKET, AND DETECTOR MATRICES
# =============================================================================
def build_reference_grid(n_z: int, l_z: float) -> Tuple[np.ndarray, float, float]:
    """Literal endpoint=False float32 grid convention from the frozen reference."""
    z = np.linspace(0.0, l_z, n_z, endpoint=False, dtype=np.float32)
    h_z = float(z[1] - z[0])
    z_roof_grid = float(z[-1])
    return z, h_z, z_roof_grid


def build_l_z(n_z: int, h_z: float, kappa: float) -> sp.csr_matrix:
    """Validated 750.Ref scalar-ABC longitudinal matrix, complex128 form."""
    inv = 1.0 / (h_z * h_z)
    data: List[complex] = []
    indices: List[int] = []
    indptr: List[int] = [0]
    for i in range(n_z):
        if i == 0:
            indptr.append(len(indices))
        elif i == n_z - 1:
            indices.extend([i - 1, i])
            data.extend([-0.5 * inv, 0.5 * inv - 1j * kappa / (2.0 * h_z)])
            indptr.append(len(indices))
        else:
            left = i - 1
            right = i + 1
            if left == 0:
                indices.extend([i, right])
                data.extend([inv, -0.5 * inv])
                indptr.append(len(indices))
            else:
                indices.extend([left, i, right])
                data.extend([-0.5 * inv, inv, -0.5 * inv])
                indptr.append(len(indices))
    return sp.csr_matrix(
        (
            np.asarray(data, dtype=np.complex128),
            np.asarray(indices, dtype=np.int32),
            np.asarray(indptr, dtype=np.int32),
        ),
        shape=(n_z, n_z),
        dtype=np.complex128,
    )


def parse_initial_mode(mode: str) -> Tuple[int, int]:
    mapping = {"00": (0, 0), "10": (1, 0), "01": (0, 1)}
    try:
        return mapping[mode]
    except KeyError as exc:
        raise ValueError(f"Unsupported initial mode {mode!r}") from exc


def build_initial_state(
    config: RunConfig,
    operators: OscillatorOperators,
    z: np.ndarray,
    h_z: float,
) -> np.ndarray:
    z64 = np.asarray(z, dtype=np.float64)
    phi_z = np.exp(-((z64 - config.z0) ** 2) / (2.0 * config.sigma_z_amplitude**2))
    phi_z = phi_z.astype(np.complex128) * np.exp(
        1j * config.k0 * (z64 - config.z0)
    )
    phi_z[0] = 0.0
    norm_z = math.sqrt(float(h_z * np.sum(np.abs(phi_z) ** 2, dtype=np.float64)))
    if not np.isfinite(norm_z) or norm_z <= 0.0:
        raise RuntimeError("Longitudinal Gaussian has invalid norm")
    phi_z /= norm_z

    c_up = math.cos(config.theta / 2.0)
    c_down = math.sin(config.theta / 2.0) * np.exp(1j * config.phi)
    spinor = np.asarray([c_up, c_down], dtype=np.complex128)
    spinor /= np.linalg.norm(spinor)

    mode_label = parse_initial_mode(config.initial_mode)
    mu = operators.index[mode_label]
    psi = np.zeros((2, operators.m_modes, config.n_z), dtype=np.complex128)
    psi[0, mu, :] = spinor[0] * phi_z
    psi[1, mu, :] = spinor[1] * phi_z
    psi[:, :, 0] = 0.0

    norm = float(h_z * np.sum(np.abs(psi) ** 2, dtype=np.float64))
    if not np.isclose(norm, 1.0, rtol=0.0, atol=5e-14):
        raise RuntimeError(f"Initial state normalization failed: {norm:.17e}")
    return psi.reshape(-1)


def source_code_and_authority_inconsistencies() -> List[Dict[str, str]]:
    return [
        {
            "topic": "Audit-02 ordering",
            "finding": (
                "The attached final Audit-02 source enumerates n_x ascending within each shell "
                "and constructs K_N in orbital-tensor-spin order."
            ),
            "resolution": (
                "The higher-priority current Task-05 handoff freezes n_x descending and spin-major "
                "storage.  The script reconstructs both and requires explicit permutation equivalence."
            ),
        },
        {
            "topic": "750.Ref fingerprint",
            "finding": (
                f"The attached 750.Ref source has SHA-256 {SOURCE_FINGERPRINTS['reference_750_attached']}, "
                f"whereas the master file quotes historical hash {HISTORICAL_750_HASH_QUOTED_BY_MASTER}."
            ),
            "resolution": (
                "The attached code body is used for the longitudinal grid, L_z, packet formula, spinor "
                "initialization formula, Cayley matrices, and GMRES conventions; both hashes are recorded."
            ),
        },
        {
            "topic": "750.Ref roof-condition prose versus matrix",
            "finding": (
                "The L_z docstring writes partial_z psi + i*kappa*psi = 0, but the implemented roof "
                "diagonal -i*kappa/(2*h_z) corresponds to the physical entrance law partial_z psi = +i*kappa*psi."
            ),
            "resolution": (
                "The implemented matrix, positive outward loss identity, master handoff, and manuscript are "
                "mutually consistent; the contradictory docstring sign is treated as a prose error."
            ),
        },
        {
            "topic": "Midpoint detector audit provenance",
            "finding": (
                "The attached reflection-check 750.Ref file contains the Cayley/GMRES core but does not itself "
                "calculate or save the midpoint roof probability or probability-closure audit."
            ),
            "resolution": (
                "The exact midpoint formula is reconstructed from the same Cayley matrix and roof loss operator, "
                "and follows the higher-priority master audit, audited Stage-01 solver, and V5 equations."
            ),
        },
        {
            "topic": "Run-specific defaults",
            "finding": (
                "The attached 750.Ref uses theta=0 and T=20, while the current Task-05 recovery handoff "
                "uses theta=pi/6 and T=10 for the Stage-01 recovery campaign."
            ),
            "resolution": "The master Task-05 handoff supersedes those run-specific defaults.",
        },
        {
            "topic": "V5 time-step defaults",
            "finding": (
                "V5 discusses 4e-4 and 2e-4 for a separate Gaussian production convention, whereas "
                "Task 05 requires manually selected Audit-01 recovery steps 1e-3 or 5e-4 and refinements."
            ),
            "resolution": "The manually declared Task-05 DT is authoritative for the selected case.",
        },
        {
            "topic": "Factorized scalar midpoint",
            "finding": (
                "For a split factorized scalar map, the exact detector loss belongs to the longitudinal "
                "Cayley substep; the full-map endpoint midpoint would include an irrelevant transverse phase."
            ),
            "resolution": (
                "The saved roof probability uses the pre/post detector-substep midpoint, then applies the "
                "exact trace-preserving transverse phase.  Monolithic and spinor maps use the full Cayley midpoint."
            ),
        },
    ]


def build_propagator_objects(
    config: RunConfig,
    operators: OscillatorOperators,
    backend: NumericalBackend,
    initial_state_cpu: np.ndarray,
) -> PropagatorObjects:
    z, h_z, z_roof_grid = build_reference_grid(config.n_z, config.l_z)
    l_z = build_l_z(config.n_z, h_z, config.kappa)
    d_channels = operators.d_channels
    identity_z = sp.eye(config.n_z, dtype=np.complex128, format="csr")
    identity_channels = sp.eye(d_channels, dtype=np.complex128, format="csr")

    hamiltonian_cpu: Optional[sp.csr_matrix]
    transverse_phase_backend: Optional[Any] = None
    active_factorized_channels: Tuple[int, ...] = tuple()

    if config.propagator_type == "scalar_factorized":
        hamiltonian_cpu = None
        identity = sp.eye(config.n_z, dtype=np.complex128, format="csr")
        a_cpu = (identity + 1j * config.dt / 2.0 * l_z).tocsr()
        b_cpu = (identity - 1j * config.dt / 2.0 * l_z).tocsr()

        energies_orbital = config.omega * (
            operators.nx_diag + operators.ny_diag + 1.0
        )
        energies_channels = np.concatenate([energies_orbital, energies_orbital])
        transverse_phase_backend = backend.to_backend_array(
            np.exp(-1j * config.dt * energies_channels)
        )
        initial_matrix = initial_state_cpu.reshape(d_channels, config.n_z)
        active_factorized_channels = tuple(
            int(index)
            for index in np.flatnonzero(
                h_z * np.sum(np.abs(initial_matrix) ** 2, axis=1, dtype=np.float64)
                > 0.0
            )
        )
    else:
        h_longitudinal = sp.kron(identity_channels, l_z, format="csr")
        h_transverse = sp.kron(
            operators.h_perp_spinmajor,
            identity_z,
            format="csr",
        )
        h_scalar = (h_longitudinal + h_transverse).tocsr()
        if config.propagator_type == "scalar_monolithic":
            hamiltonian_cpu = h_scalar
        else:
            roof_projector = sp.csr_matrix(
                (
                    np.asarray([1.0], dtype=np.complex128),
                    (np.asarray([config.n_z - 1]), np.asarray([config.n_z - 1])),
                ),
                shape=(config.n_z, config.n_z),
            )
            roof_reactive = (
                (1.0 / (2.0 * h_z))
                * sp.kron(operators.k_spinmajor, roof_projector, format="csr")
            ).tocsr()
            hamiltonian_cpu = (h_scalar + roof_reactive).tocsr()

        identity = sp.eye(
            d_channels * config.n_z,
            dtype=np.complex128,
            format="csr",
        )
        a_cpu = (identity + 1j * config.dt / 2.0 * hamiltonian_cpu).tocsr()
        b_cpu = (identity - 1j * config.dt / 2.0 * hamiltonian_cpu).tocsr()

    backend_a = backend.to_backend_sparse(a_cpu)
    backend_b = backend.to_backend_sparse(b_cpu)
    backend_preconditioner = backend.make_diagonal_preconditioner(backend_a)

    roof_sign_audit = audit_roof_term_sign(
        config=config,
        operators=operators,
        l_z=l_z,
        h_z=h_z,
        hamiltonian_cpu=hamiltonian_cpu,
    )

    return PropagatorObjects(
        l_z=l_z,
        z=z,
        h_z=h_z,
        z_roof_grid=z_roof_grid,
        hamiltonian_cpu=hamiltonian_cpu,
        a_cpu=a_cpu,
        b_cpu=b_cpu,
        backend_a=backend_a,
        backend_b=backend_b,
        backend_preconditioner=backend_preconditioner,
        transverse_phase_backend=transverse_phase_backend,
        active_factorized_channels=active_factorized_channels,
        roof_sign_audit=roof_sign_audit,
    )


def audit_roof_term_sign(
    *,
    config: RunConfig,
    operators: OscillatorOperators,
    l_z: sp.csr_matrix,
    h_z: float,
    hamiltonian_cpu: Optional[sp.csr_matrix],
) -> Dict[str, Any]:
    d_channels = operators.d_channels
    inv = 1.0 / (h_z * h_z)
    identity_channels = np.eye(d_channels, dtype=np.complex128)
    h_perp_dense = operators.h_perp_spinmajor.toarray()
    k_dense = operators.k_spinmajor.toarray()

    expected_roof_roof_plus = (
        (0.5 * inv - 1j * config.kappa / (2.0 * h_z)) * identity_channels
        + h_perp_dense
        + k_dense / (2.0 * h_z)
    )
    expected_roof_roof_minus = (
        (0.5 * inv - 1j * config.kappa / (2.0 * h_z)) * identity_channels
        + h_perp_dense
        - k_dense / (2.0 * h_z)
    )
    expected_roof_neighbor = -0.5 * inv * identity_channels

    # Verify the frozen C-order vectorization independently of any matrix
    # construction: z is fastest, then oscillator channel, then physical spin.
    full_state_index_samples: List[Dict[str, int]] = []
    for spin in range(2):
        for mu in (0, operators.m_modes // 2, operators.m_modes - 1):
            for k_z in (0, config.n_z // 2, config.n_z - 1):
                formula_index = (spin * operators.m_modes + mu) * config.n_z + k_z
                raveled_index = int(
                    np.ravel_multi_index(
                        (spin, mu, k_z),
                        (2, operators.m_modes, config.n_z),
                        order="C",
                    )
                )
                full_state_index_samples.append(
                    {
                        "spin": spin,
                        "mu": mu,
                        "k_z": k_z,
                        "formula_index": formula_index,
                        "raveled_index": raveled_index,
                    }
                )
    full_state_order_pass = all(
        item["formula_index"] == item["raveled_index"]
        for item in full_state_index_samples
    )
    matrix_dtype_pass = bool(
        l_z.dtype == np.dtype(np.complex128)
        and (
            hamiltonian_cpu is None
            or hamiltonian_cpu.dtype == np.dtype(np.complex128)
        )
    )

    if config.propagator_type == "spinor":
        if hamiltonian_cpu is None:
            raise RuntimeError("Spinor roof audit requires the full Hamiltonian")
        roof_indices = np.arange(d_channels, dtype=np.int64) * config.n_z + (config.n_z - 1)
        neighbor_indices = np.arange(d_channels, dtype=np.int64) * config.n_z + (config.n_z - 2)
        actual_roof_roof = hamiltonian_cpu[roof_indices][:, roof_indices].toarray()
        actual_roof_neighbor = hamiltonian_cpu[roof_indices][:, neighbor_indices].toarray()
        plus_residual = dense_max_abs(actual_roof_roof - expected_roof_roof_plus)
        neighbor_residual = dense_max_abs(actual_roof_neighbor - expected_roof_neighbor)
        minus_candidate_residual = dense_max_abs(actual_roof_roof - expected_roof_roof_minus)

        rng = np.random.default_rng(20260803)
        random_state = rng.normal(size=d_channels * config.n_z) + 1j * rng.normal(
            size=d_channels * config.n_z
        )
        h_scalar = (
            sp.kron(sp.eye(d_channels, format="csr"), l_z, format="csr")
            + sp.kron(
                operators.h_perp_spinmajor,
                sp.eye(config.n_z, format="csr"),
                format="csr",
            )
        ).tocsr()
        difference_action = (hamiltonian_cpu - h_scalar) @ random_state
        expected_action = np.zeros_like(random_state)
        roof_vector = random_state.reshape(d_channels, config.n_z)[:, -1]
        expected_action.reshape(d_channels, config.n_z)[:, -1] = (
            operators.k_spinmajor @ roof_vector
        ) / (2.0 * h_z)
        random_action_residual = float(np.linalg.norm(difference_action - expected_action))
        random_action_scale = float(np.linalg.norm(expected_action))
        random_action_relative_residual = relative_error(
            random_action_residual, random_action_scale
        )

        loss_operator = (1j * (hamiltonian_cpu - hamiltonian_cpu.getH())).tocsr()
        roof_projector = sp.csr_matrix(
            (
                np.asarray([1.0], dtype=np.complex128),
                (np.asarray([config.n_z - 1]), np.asarray([config.n_z - 1])),
            ),
            shape=(config.n_z, config.n_z),
        )
        expected_loss = (
            (config.kappa / h_z)
            * sp.kron(
                sp.eye(d_channels, dtype=np.complex128, format="csr"),
                roof_projector,
                format="csr",
            )
        ).tocsr()
        loss_residual = sparse_max_abs(loss_operator - expected_loss)
    else:
        # The scalar maps contain no reactive K term.  We still audit the
        # independently derived sign formula at channel level.
        plus_residual = 0.0
        neighbor_residual = 0.0
        minus_candidate_residual = dense_max_abs(
            expected_roof_roof_plus - expected_roof_roof_minus
        )
        random_action_residual = 0.0
        random_action_scale = 0.0
        random_action_relative_residual = 0.0
        scalar_loss = (1j * (l_z - l_z.getH())).tocsr()
        expected_scalar_loss = sp.csr_matrix(
            (
                np.asarray([config.kappa / h_z], dtype=np.complex128),
                (np.asarray([config.n_z - 1]), np.asarray([config.n_z - 1])),
            ),
            shape=(config.n_z, config.n_z),
        )
        loss_residual = sparse_max_abs(scalar_loss - expected_scalar_loss)

    plus_pass = bool(
        max(plus_residual, neighbor_residual) <= OPERATOR_TOL
        and random_action_relative_residual <= OPERATOR_TOL
        and full_state_order_pass
        and matrix_dtype_pass
    )
    loss_pass = loss_residual <= OPERATOR_TOL
    negative_sign_rejected = bool(
        frobenius_norm(operators.k_spinmajor) == 0.0
        or minus_candidate_residual > max(100.0 * OPERATOR_TOL, plus_residual)
    )

    return {
        "boundary_relation": "partial_z u = (i*kappa*I - K_N) u",
        "ghost_elimination_derivation": (
            "Using the centered ghost derivative u_{R+1}-u_{R-1}=2*h_z*(i*kappa*I-K_N)u_R "
            "inside the validated half-weight roof row gives -i*kappa/(2*h_z)I + K_N/(2*h_z)."
        ),
        "derived_reactive_roof_sign": "+",
        "derived_reactive_roof_coefficient": 1.0 / (2.0 * h_z),
        "plus_sign_roof_block_max_abs_residual": plus_residual,
        "roof_neighbor_block_max_abs_residual": neighbor_residual,
        "random_matrix_action_absolute_residual": random_action_residual,
        "random_matrix_action_scale": random_action_scale,
        "random_matrix_action_relative_residual": random_action_relative_residual,
        "negative_sign_candidate_max_abs_residual": minus_candidate_residual,
        "negative_sign_candidate_rejected": negative_sign_rejected,
        "detector_loss_operator_roof_identity_residual": loss_residual,
        "K_contributes_no_antihermitian_loss": loss_pass,
        "full_state_index_formula_exact": full_state_order_pass,
        "full_state_index_samples": full_state_index_samples,
        "longitudinal_and_full_matrix_complex128": matrix_dtype_pass,
        "spinor_roof_term_sign_passed": bool(plus_pass and loss_pass and negative_sign_rejected),
        "midpoint_identity": (
            "dt*h_z*<q,G_D q> = dt*kappa*sum_(s,mu)|q_(s,mu)(z_roof)|^2"
        ),
    }


# =============================================================================
# STATE DIAGNOSTICS AND INSERTION-VECTOR ARCHIVE
# =============================================================================
def compute_state_diagnostics(
    state_backend: Any,
    *,
    backend: NumericalBackend,
    operators: OscillatorOperators,
    h_z: float,
    n_z: int,
) -> Dict[str, Any]:
    d_channels = operators.d_channels
    m_modes = operators.m_modes
    state = state_backend.reshape(2, m_modes, n_z)
    density = state.real * state.real + state.imag * state.imag
    mode_sub_backend = h_z * backend.xp.sum(
        density,
        axis=(0, 2),
        dtype=backend.float64,
    )
    mode_sub = np.asarray(backend.to_cpu(mode_sub_backend), dtype=np.float64)
    survival = float(np.sum(mode_sub, dtype=np.float64))
    if not np.isfinite(survival) or survival < 0.0:
        raise FloatingPointError(f"Invalid survival {survival!r}")

    shell_sub = np.bincount(
        operators.shell_of_mode,
        weights=mode_sub,
        minlength=int(np.max(operators.shell_of_mode)) + 1,
    ).astype(np.float64)
    if survival > 0.0:
        shell_norm = shell_sub / survival
        mode_norm = mode_sub / survival
    else:
        shell_norm = np.full_like(shell_sub, np.nan)
        mode_norm = np.full_like(mode_sub, np.nan)

    nx_sub = float(np.dot(mode_sub, operators.nx_diag))
    ny_sub = float(np.dot(mode_sub, operators.ny_diag))
    nx2_sub = float(np.dot(mode_sub, operators.nx_diag**2))
    ny2_sub = float(np.dot(mode_sub, operators.ny_diag**2))
    nperp_sub = nx_sub + ny_sub
    top_sub = float(shell_sub[-1])
    upward_sub = float(
        np.dot(mode_sub, operators.nx_diag + operators.ny_diag + 2.0)
        - (int(np.max(operators.shell_of_mode)) + 2) * top_sub
    )

    if survival > 0.0:
        nx_norm = nx_sub / survival
        ny_norm = ny_sub / survival
        nx2_norm = nx2_sub / survival
        ny2_norm = ny2_sub / survival
        s_down = nperp_sub / survival
        s_up = upward_sub / survival
        s_phi = (nx2_norm - nx_norm**2) + (ny2_norm - ny_norm**2)
        top_norm = top_sub / survival
    else:
        nx_norm = ny_norm = nx2_norm = ny2_norm = float("nan")
        s_down = s_up = s_phi = top_norm = float("nan")

    roof_vector = np.asarray(
        backend.to_cpu(state_backend.reshape(d_channels, n_z)[:, -1]),
        dtype=np.complex128,
    )
    omitted_vector = operators.k_omit_spinmajor @ roof_vector
    r_k_omit_sub = float(np.vdot(omitted_vector, omitted_vector).real)
    r_k_omit_norm = r_k_omit_sub / survival if survival > 0.0 else float("nan")

    return {
        "survival": survival,
        "mode_populations_subnormalized": mode_sub,
        "mode_populations_normalized": mode_norm,
        "shell_populations_subnormalized": shell_sub,
        "shell_populations_normalized": shell_norm,
        "top_shell_subnormalized": top_sub,
        "top_shell_normalized": top_norm,
        "nx_mean_subnormalized": nx_sub,
        "ny_mean_subnormalized": ny_sub,
        "nx2_mean_subnormalized": nx2_sub,
        "ny2_mean_subnormalized": ny2_sub,
        "s_down_subnormalized": nperp_sub,
        "s_down_normalized": s_down,
        "s_up_subnormalized": upward_sub,
        "s_up_normalized": s_up,
        "s_phi_survival_weighted": survival * s_phi if survival > 0.0 else float("nan"),
        "s_phi_normalized": s_phi,
        "r_K_omit_subnormalized": r_k_omit_sub,
        "r_K_omit_normalized_no_click": r_k_omit_norm,
    }


def insertion_steps(config: RunConfig) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    requested = [time_value for time_value in INSERTION_TIMES_REQUESTED if time_value <= config.t_final + 1e-12]
    requested.append(config.t_final)
    step_to_requested: Dict[int, float] = {}
    for requested_time in requested:
        step = int(round(requested_time / config.dt))
        step = min(max(step, 0), config.num_steps)
        step_to_requested.setdefault(step, requested_time)
    steps = np.asarray(sorted(step_to_requested), dtype=np.int64)
    requested_unique = np.asarray([step_to_requested[int(step)] for step in steps], dtype=np.float64)
    actual = steps.astype(np.float64) * config.dt
    return steps, requested_unique, actual


def channel_operator_dictionary(operators: OscillatorOperators) -> Dict[str, sp.csr_matrix]:
    identity_spin = sp.eye(2, dtype=np.complex128, format="csr")
    identity_channel = sp.eye(operators.d_channels, dtype=np.complex128, format="csr")
    ax = sp.kron(identity_spin, operators.a_x, format="csr")
    ay = sp.kron(identity_spin, operators.a_y, format="csr")
    axd = sp.kron(identity_spin, operators.a_x_dagger, format="csr")
    ayd = sp.kron(identity_spin, operators.a_y_dagger, format="csr")
    nx = sp.kron(identity_spin, operators.n_x, format="csr")
    ny = sp.kron(identity_spin, operators.n_y, format="csr")
    ax_axd = (ax @ axd).tocsr()
    ay_ayd = (ay @ ayd).tocsr()
    nx2 = (nx @ nx).tocsr()
    ny2 = (ny @ ny).tocsr()
    return {
        "psi_nc": identity_channel,
        "a_x_psi_nc": ax,
        "a_y_psi_nc": ay,
        "a_x_dagger_psi_nc": axd,
        "a_y_dagger_psi_nc": ayd,
        "N_x_psi_nc": nx,
        "N_y_psi_nc": ny,
        # a_j^dagger a_j psi_nc is exactly N_j psi_nc and is retained
        # through the explicit alias metadata in the archive rather than
        # duplicating large channel-row arrays.
        "a_x_a_x_dagger_psi_nc": ax_axd,
        "a_y_a_y_dagger_psi_nc": ay_ayd,
        "N_x_squared_psi_nc": nx2,
        "N_y_squared_psi_nc": ny2,
    }


def build_sparse_insertion_archive(
    selected_states: Mapping[int, np.ndarray],
    *,
    selected_survivals: Mapping[int, float],
    selected_requested_times: Mapping[int, float],
    selected_actual_times: Mapping[int, float],
    operators: OscillatorOperators,
    h_z: float,
    n_z: int,
) -> Dict[str, np.ndarray]:
    channel_ops = channel_operator_dictionary(operators)
    vector_names: List[str] = []
    vector_steps: List[int] = []
    vector_requested_times: List[float] = []
    vector_actual_times: List[float] = []
    vector_survivals: List[float] = []
    indptr: List[int] = [0]
    channel_indices: List[int] = []
    channel_value_rows: List[np.ndarray] = []
    total_norm2: List[float] = []
    omitted_norm2: List[float] = []
    threshold_norm2: List[float] = []

    for step in sorted(selected_states):
        state = np.asarray(selected_states[step], dtype=np.complex128).reshape(
            operators.d_channels, n_z
        )
        for name, operator in channel_ops.items():
            vector = np.asarray(operator @ state, dtype=np.complex128)
            per_channel_norm2 = h_z * np.sum(
                np.abs(vector) ** 2,
                axis=1,
                dtype=np.float64,
            )
            total = float(np.sum(per_channel_norm2, dtype=np.float64))
            threshold = max(
                INSERTION_CHANNEL_ABS_NORM2_TOL,
                (INSERTION_CHANNEL_REL_NORM_TOL**2) * total,
            )
            retained = np.flatnonzero(per_channel_norm2 > threshold)
            omitted = float(total - np.sum(per_channel_norm2[retained], dtype=np.float64))

            vector_names.append(name)
            vector_steps.append(int(step))
            vector_requested_times.append(float(selected_requested_times[step]))
            vector_actual_times.append(float(selected_actual_times[step]))
            vector_survivals.append(float(selected_survivals[step]))
            total_norm2.append(total)
            omitted_norm2.append(max(0.0, omitted))
            threshold_norm2.append(threshold)
            channel_indices.extend(int(index) for index in retained)
            channel_value_rows.extend(vector[index].copy() for index in retained)
            indptr.append(len(channel_indices))

    if channel_value_rows:
        values = np.stack(channel_value_rows, axis=0).astype(np.complex128, copy=False)
    else:
        values = np.empty((0, n_z), dtype=np.complex128)

    alias_keys = np.asarray(
        ["a_x_dagger_a_x_psi_nc", "a_y_dagger_a_y_psi_nc"], dtype="U64"
    )
    alias_targets = np.asarray(["N_x_psi_nc", "N_y_psi_nc"], dtype="U64")

    return {
        "vector_names": np.asarray(vector_names, dtype="U64"),
        "vector_steps": np.asarray(vector_steps, dtype=np.int64),
        "vector_requested_times": np.asarray(vector_requested_times, dtype=np.float64),
        "vector_actual_times": np.asarray(vector_actual_times, dtype=np.float64),
        "vector_survival": np.asarray(vector_survivals, dtype=np.float64),
        "vector_indptr": np.asarray(indptr, dtype=np.int64),
        "channel_indices": np.asarray(channel_indices, dtype=np.int32),
        "channel_values": values,
        "vector_total_norm2": np.asarray(total_norm2, dtype=np.float64),
        "vector_omitted_norm2": np.asarray(omitted_norm2, dtype=np.float64),
        "vector_channel_threshold_norm2": np.asarray(threshold_norm2, dtype=np.float64),
        "alias_names": alias_keys,
        "alias_targets": alias_targets,
        "n_z": np.asarray([n_z], dtype=np.int64),
        "d_channels": np.asarray([operators.d_channels], dtype=np.int64),
        "h_z": np.asarray([h_z], dtype=np.float64),
        "channel_relative_norm_tolerance": np.asarray(
            [INSERTION_CHANNEL_REL_NORM_TOL], dtype=np.float64
        ),
        "interpretation": np.asarray(
            [
                "Sparse channel-row representation of normalized no-click vectors. Reconstruct each "
                "d_channels x n_z vector by filling rows channel_indices[indptr[i]:indptr[i+1]] "
                "with channel_values; multiply by sqrt(vector_survival[i]) to recover its subnormalized form."
            ],
            dtype="U512",
        ),
    }


# =============================================================================
# PROPAGATION HELPERS
# =============================================================================
def true_relative_residual(
    backend: NumericalBackend,
    matrix: Any,
    solution: Any,
    rhs: Any,
) -> float:
    residual = matrix @ solution - rhs
    numerator = backend.norm(residual)
    denominator = backend.norm(rhs)
    return numerator if denominator == 0.0 else numerator / denominator


def midpoint_roof_probability(
    backend: NumericalBackend,
    state_before: Any,
    state_after_detector: Any,
    *,
    d_channels: int,
    n_z: int,
    dt: float,
    kappa: float,
) -> float:
    before = state_before.reshape(d_channels, n_z)
    after = state_after_detector.reshape(d_channels, n_z)
    q_roof = 0.5 * (before[:, -1] + after[:, -1])
    return dt * kappa * backend.abs2_sum(q_roof)


def norm2_state(backend: NumericalBackend, state: Any, h_z: float) -> float:
    return h_z * backend.abs2_sum(state)


def advance_factorized_scalar(
    state: Any,
    *,
    backend: NumericalBackend,
    propagator: PropagatorObjects,
    config: RunConfig,
    operators: OscillatorOperators,
) -> Tuple[Any, float, float, float, int, int, float]:
    state_matrix = state.reshape(operators.d_channels, config.n_z)
    detector_output = backend.xp.zeros_like(state_matrix)
    maximum_residual = 0.0
    maximum_info = 0
    solve_count = 0

    for channel in propagator.active_factorized_channels:
        input_channel = state_matrix[channel]
        rhs = propagator.backend_b @ input_channel
        solution, info = backend.gmres(
            propagator.backend_a,
            rhs,
            x0=input_channel,
            preconditioner=propagator.backend_preconditioner,
        )
        residual = true_relative_residual(
            backend,
            propagator.backend_a,
            solution,
            rhs,
        )
        detector_output[channel] = solution
        maximum_residual = max(maximum_residual, residual)
        maximum_info = max(maximum_info, abs(info))
        solve_count += 1

    detector_flat = detector_output.reshape(-1)
    p_roof = midpoint_roof_probability(
        backend,
        state,
        detector_flat,
        d_channels=operators.d_channels,
        n_z=config.n_z,
        dt=config.dt,
        kappa=config.kappa,
    )
    preclamp_norm = norm2_state(backend, detector_flat, propagator.h_z)
    bottom = detector_output[:, 0].copy()
    clamp_loss = propagator.h_z * backend.abs2_sum(bottom)
    detector_output[:, 0] = 0.0

    if propagator.transverse_phase_backend is None:
        raise RuntimeError("Factorized scalar phase was not constructed")
    state_next = (
        propagator.transverse_phase_backend[:, None] * detector_output
    ).reshape(-1)
    return state_next, p_roof, preclamp_norm, clamp_loss, maximum_info, solve_count, maximum_residual


def advance_monolithic(
    state: Any,
    *,
    backend: NumericalBackend,
    propagator: PropagatorObjects,
    config: RunConfig,
    operators: OscillatorOperators,
) -> Tuple[Any, float, float, float, int, int, float]:
    rhs = propagator.backend_b @ state
    solution, info = backend.gmres(
        propagator.backend_a,
        rhs,
        x0=state,
        preconditioner=propagator.backend_preconditioner,
    )
    residual = true_relative_residual(
        backend,
        propagator.backend_a,
        solution,
        rhs,
    )
    p_roof = midpoint_roof_probability(
        backend,
        state,
        solution,
        d_channels=operators.d_channels,
        n_z=config.n_z,
        dt=config.dt,
        kappa=config.kappa,
    )
    preclamp_norm = norm2_state(backend, solution, propagator.h_z)
    output = solution.reshape(operators.d_channels, config.n_z)
    bottom = output[:, 0].copy()
    clamp_loss = propagator.h_z * backend.abs2_sum(bottom)
    output[:, 0] = 0.0
    return output.reshape(-1), p_roof, preclamp_norm, clamp_loss, abs(info), 1, residual


def save_checkpoint(
    stage_dir: Path,
    case_prefix: str,
    completed_steps: int,
    *,
    times: np.ndarray,
    survival: np.ndarray,
    step_loss_roof: np.ndarray,
    step_loss_total: np.ndarray,
    step_loss_clamp: np.ndarray,
    step_flux_residual: np.ndarray,
    true_residual: np.ndarray,
    gmres_info: np.ndarray,
) -> None:
    k = completed_steps
    atomic_savez(
        case_file(stage_dir, case_prefix, "checkpoint.npz"),
        completed_steps=np.asarray([k], dtype=np.int64),
        times=times[: k + 1],
        survival=survival[: k + 1],
        step_loss_roof_midpoint=step_loss_roof[:k],
        step_loss_total=step_loss_total[:k],
        step_loss_bottom_clamp=step_loss_clamp[:k],
        step_loss_flux_residual=step_flux_residual[:k],
        true_relative_residual=true_residual[:k],
        gmres_info=gmres_info[:k],
    )


# =============================================================================
# FILE/DIRECTORY MANAGEMENT
# =============================================================================
def read_json_if_exists(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return None


def remove_stale_case_files(stage_dir: Path, case_prefix: str) -> List[str]:
    removed: List[str] = []
    for path in sorted(stage_dir.glob(f"{case_prefix}_*")):
        if path.is_file() or path.is_symlink():
            removed.append(path.name)
            path.unlink()
        elif path.is_dir():
            removed.append(path.name + "/")
            shutil.rmtree(path)
    return removed


def update_stage_manifest(
    stage_dir: Path,
    case_prefix: str,
    record: Mapping[str, Any],
) -> None:
    manifest_path = stage_dir / "stage_manifest.json"
    lock_path = stage_dir / ".stage_manifest.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        try:
            existing = read_json_if_exists(manifest_path) or {}
            existing.setdefault("stage", STAGE_NAME)
            existing.setdefault("script_version", SCRIPT_VERSION)
            existing.setdefault("cases", {})
            existing["updated_utc"] = utc_now_iso()
            existing["cases"][case_prefix] = dict(record)
            atomic_write_json(manifest_path, existing)
        finally:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def stable_output_files(stage_dir: Path, case_prefix: str) -> List[Path]:
    excluded_suffixes = {
        "output_hashes.json",
        "run_status.json",
        "stdout.txt",
        "simulation_log.txt",
        "checkpoint.npz",
        "failure.json",
    }
    paths: List[Path] = []
    for path in sorted(stage_dir.glob(f"{case_prefix}_*")):
        if not path.is_file():
            continue
        suffix = path.name[len(case_prefix) + 1 :]
        if suffix not in excluded_suffixes:
            paths.append(path)
    return paths


def compare_previous_hashes(
    previous_configuration: Optional[Mapping[str, Any]],
    previous_manifest: Optional[Mapping[str, Any]],
    current_configuration_hash: str,
    current_hashes: Mapping[str, str],
) -> Dict[str, Any]:
    if previous_configuration is None or previous_manifest is None:
        return {
            "comparison_applicable": False,
            "reason": "No previous same-prefix completed result was available.",
            "deterministic_stable_outputs_match": None,
        }
    previous_hash = previous_configuration.get("configuration_sha256")
    if previous_hash != current_configuration_hash:
        return {
            "comparison_applicable": False,
            "reason": "Previous same-prefix configuration/source differs from the current run.",
            "previous_configuration_sha256": previous_hash,
            "current_configuration_sha256": current_configuration_hash,
            "deterministic_stable_outputs_match": None,
        }
    previous_files = previous_manifest.get("files", {})
    matching = previous_files == dict(current_hashes)
    differing_names = sorted(
        set(previous_files).union(current_hashes)
        - {
            name
            for name in set(previous_files).intersection(current_hashes)
            if previous_files[name] == current_hashes[name]
        }
    )
    return {
        "comparison_applicable": True,
        "reason": "Identical configuration/source hash; stable output hashes compared.",
        "deterministic_stable_outputs_match": bool(matching),
        "differing_or_missing_files": differing_names,
    }


# =============================================================================
# MAIN SINGLE-CASE SOLVER
# =============================================================================
def run_case(config: RunConfig) -> Dict[str, Any]:
    validate_config(config)
    script_path = Path(__file__).resolve()
    script_sha256 = sha256_file(script_path)
    source_guard = audit_prohibited_dynamics_absent(script_path)
    if not source_guard["active_environmental_or_density_matrix_code_absent"]:
        raise RuntimeError(f"Prohibited executable dynamics detected: {source_guard}")

    stage_dir = config.stage_dir
    stage_dir.mkdir(parents=True, exist_ok=True)
    lock_path = stage_dir / f".{config.case_prefix}.lock"

    with lock_path.open("a+", encoding="utf-8") as case_lock:
        fcntl.flock(case_lock.fileno(), fcntl.LOCK_EX)
        previous_configuration = read_json_if_exists(
            case_file(stage_dir, config.case_prefix, "configuration.json")
        )
        previous_manifest = read_json_if_exists(
            case_file(stage_dir, config.case_prefix, "output_hashes.json")
        )
        stale_removed = remove_stale_case_files(stage_dir, config.case_prefix)

        stdout_path = case_file(stage_dir, config.case_prefix, "stdout.txt")
        log_path = case_file(stage_dir, config.case_prefix, "simulation_log.txt")
        original_stdout = sys.stdout
        stdout_handle = stdout_path.open("w", encoding="utf-8")
        sys.stdout = Tee(original_stdout, stdout_handle)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_path, mode="w"),
                logging.StreamHandler(sys.stdout),
            ],
            force=True,
        )

        status_path = case_file(stage_dir, config.case_prefix, "run_status.json")
        status: Dict[str, Any] = {
            "status": "initializing",
            "started_utc": utc_now_iso(),
            "case_prefix": config.case_prefix,
            "stage_directory": str(stage_dir),
            "stale_same_prefix_files_removed": stale_removed,
            "source_sha256": script_sha256,
        }
        atomic_write_json(status_path, status)

        try:
            backend = NumericalBackend(config.backend)
            print(f"[info] Task-05 case: {config.case_prefix}")
            print(f"[info] propagator: {config.propagator_type}")
            print(f"[info] initial mode: |{config.initial_mode[0]},{config.initial_mode[1]}>")
            print(f"[info] omega={config.omega:g}, N_shell={config.n_shell}")
            print(f"[info] dt={config.dt:.16g}, T_final={config.t_final:.16g}")
            print(f"[info] backend={backend.name}")
            print(f"[info] fixed stage directory: {stage_dir}")
            print(f"[info] source SHA-256: {script_sha256}")

            operators = build_oscillator_operators(config.n_shell, config.omega)
            z, h_z, z_roof_grid = build_reference_grid(config.n_z, config.l_z)
            initial_state_cpu = build_initial_state(config, operators, z, h_z)
            propagator = build_propagator_objects(
                config,
                operators,
                backend,
                initial_state_cpu,
            )

            # Save the complete audit record before aborting on a failed gate,
            # so a rejected construction remains independently diagnosable.
            source_copy = case_file(
                stage_dir, config.case_prefix, "05_oscillator_channel_detector_test.py"
            )
            atomic_copy(script_path, source_copy)
            copied_source_hash = sha256_file(source_copy)
            if copied_source_hash != script_sha256:
                raise RuntimeError("Copied source hash does not match executing source")

            source_inconsistencies = source_code_and_authority_inconsistencies()
            config_payload: Dict[str, Any] = {
                "stage": STAGE_NAME,
                "script_version": SCRIPT_VERSION,
                "case_prefix": config.case_prefix,
                "propagator_type": config.propagator_type,
                "propagator_interpretation": {
                    "scalar_factorized": (
                        "authoritative finite-step scalar control"
                    ),
                    "scalar_monolithic": (
                        "finite-step nonfactorization diagnostic only; any mode dependence is numerical, not physical"
                    ),
                    "spinor": (
                        "zero-bath coupled-channel spin-momentum detector map"
                    ),
                }[config.propagator_type],
                "detector_label": config.detector_label,
                "initial_mode": config.initial_mode,
                "zero_ambient_bath": True,
                "omega": config.omega,
                "N_shell": config.n_shell,
                "M_N": operators.m_modes,
                "d_channels": operators.d_channels,
                "state_index_formula": "index(s,mu,k_z)=(s*M_N+mu)*N_z+k_z",
                "N_z": config.n_z,
                "L_z": config.l_z,
                "endpoint": False,
                "grid_construction_dtype": "float32 (literal 750.Ref grid convention)",
                "h_z": propagator.h_z,
                "z_roof_grid": propagator.z_roof_grid,
                "dt": config.dt,
                "T_final": config.t_final,
                "num_steps": config.num_steps,
                "z0": config.z0,
                "sigma_z_amplitude": config.sigma_z_amplitude,
                "sigma_parallel_probability": config.sigma_z_amplitude / math.sqrt(2.0),
                "k0": config.k0,
                "kappa": config.kappa,
                "theta": config.theta,
                "phi": config.phi,
                "physical_spinor_formula": [
                    "cos(theta/2)",
                    "sin(theta/2)*exp(i*phi)",
                ],
                "state_dtype": "complex128",
                "matrix_dtype": "complex128",
                "reduction_dtype": "float64",
                "backend_metadata": backend.metadata(),
                "gmres": {
                    "rtol": GMRES_RTOL,
                    "atol": GMRES_ATOL,
                    "restart": GMRES_RESTART,
                    "maxiter": GMRES_MAXITER,
                    "preconditioner": "inverse diagonal of the Cayley left matrix",
                    "x0": "previous no-click state",
                },
                "probability_convention": {
                    "survival": "h_z*sum_(s,mu,k_z)|psi|^2",
                    "roof_step_probability": (
                        "dt*kappa*sum_(s,mu)|q(s,mu,z_roof)|^2; no h_x*h_y factor"
                    ),
                    "factorized_scalar_midpoint": (
                        "pre/post longitudinal detector-Cayley substep; transverse phase applied afterward"
                    ),
                    "monolithic_and_spinor_midpoint": "pre/post complete Cayley step",
                    "integrated_detector_probabilities": "direct sums of midpoint step probabilities",
                },
                "fixed_stage_directory": STAGE_DIRECTORY,
                "output_root": str(config.out_root.expanduser().resolve()),
                "source_sha256": script_sha256,
                "copied_source_file": source_copy.name,
                "copied_source_sha256": copied_source_hash,
                "authority_source_fingerprints": SOURCE_FINGERPRINTS,
                "historical_750_hash_quoted_by_master": HISTORICAL_750_HASH_QUOTED_BY_MASTER,
                "source_inconsistencies_and_resolutions": source_inconsistencies,
                "oscillator_channel_differences_from_cartesian_reference": [
                    "No Cartesian x/y grid and no hard lateral walls.",
                    "The transverse complete-shell basis is orthonormal; roof probability has no h_x*h_y factor.",
                    "All propagated amplitudes and sparse solves use complex128; no complex64 cast is made.",
                    "The spinor roof coupling is the projected K_N matrix acting only at the roof node.",
                    "Cartesian--oscillator representation discrepancy is retained as a separate recovery error.",
                ],
                "source_guard": source_guard,
                "manual_single_case_policy": True,
                "automatic_production_sweep": False,
                "smoke_test": config.smoke_test,
            }
            config_hash_payload = dict(config_payload)
            config_payload["configuration_sha256"] = sha256_json(config_hash_payload)
            configuration_path = case_file(
                stage_dir, config.case_prefix, "configuration.json"
            )
            atomic_write_json(configuration_path, config_payload)

            operator_audit = dict(operators.audit)
            operator_audit["source_guard"] = source_guard
            operator_audit["spinor_roof_term_sign"] = propagator.roof_sign_audit
            operator_audit["source_sha256"] = script_sha256
            operator_audit["configuration_sha256"] = config_payload[
                "configuration_sha256"
            ]
            operator_audit["all_checks_passed"] = bool(
                operators.audit["all_checks_passed"]
                and propagator.roof_sign_audit["spinor_roof_term_sign_passed"]
                and source_guard["active_environmental_or_density_matrix_code_absent"]
            )
            operator_audit_path = case_file(
                stage_dir, config.case_prefix, "operator_audit.json"
            )
            atomic_write_json(operator_audit_path, operator_audit)

            status.update(
                {
                    "status": "running",
                    "configuration_sha256": config_payload["configuration_sha256"],
                    "operator_audit_passed": operator_audit["all_checks_passed"],
                }
            )
            atomic_write_json(status_path, status)

            if not operators.audit["all_checks_passed"]:
                raise RuntimeError(
                    "Oscillator operator audit failed; inspect the saved operator audit."
                )
            if not propagator.roof_sign_audit["spinor_roof_term_sign_passed"]:
                raise RuntimeError(
                    "Spinor roof-term sign/loss audit failed; inspect the saved operator audit."
                )

            num_steps = config.num_steps
            times = np.arange(num_steps + 1, dtype=np.float64) * config.dt
            midpoint_times = (np.arange(num_steps, dtype=np.float64) + 0.5) * config.dt

            survival = np.full(num_steps + 1, np.nan, dtype=np.float64)
            step_loss_roof = np.full(num_steps, np.nan, dtype=np.float64)
            step_loss_total = np.full(num_steps, np.nan, dtype=np.float64)
            step_loss_clamp = np.full(num_steps, np.nan, dtype=np.float64)
            step_flux_residual = np.full(num_steps, np.nan, dtype=np.float64)
            true_residuals = np.full(num_steps, np.nan, dtype=np.float64)
            gmres_info = np.full(num_steps, -999, dtype=np.int32)
            gmres_solve_count = np.zeros(num_steps, dtype=np.int32)

            shell_sub = np.full(
                (num_steps + 1, config.n_shell + 1), np.nan, dtype=np.float64
            )
            shell_norm = np.full_like(shell_sub, np.nan)
            top_sub = np.full(num_steps + 1, np.nan, dtype=np.float64)
            top_norm = np.full(num_steps + 1, np.nan, dtype=np.float64)

            source_names = (
                "s_down_subnormalized",
                "s_down_normalized",
                "s_up_subnormalized",
                "s_up_normalized",
                "s_phi_survival_weighted",
                "s_phi_normalized",
                "nx_mean_subnormalized",
                "ny_mean_subnormalized",
                "nx2_mean_subnormalized",
                "ny2_mean_subnormalized",
                "r_K_omit_subnormalized",
                "r_K_omit_normalized_no_click",
            )
            source_curves = {
                name: np.full(num_steps + 1, np.nan, dtype=np.float64)
                for name in source_names
            }

            selected_steps_array, requested_times_array, actual_times_array = insertion_steps(config)
            selected_step_set = {int(step) for step in selected_steps_array}
            requested_by_step = {
                int(step): float(requested)
                for step, requested in zip(selected_steps_array, requested_times_array)
            }
            actual_by_step = {
                int(step): float(actual)
                for step, actual in zip(selected_steps_array, actual_times_array)
            }
            selected_states: Dict[int, np.ndarray] = {}
            selected_survivals: Dict[int, float] = {}

            state = backend.to_backend_array(initial_state_cpu)
            initial_diagnostics = compute_state_diagnostics(
                state,
                backend=backend,
                operators=operators,
                h_z=propagator.h_z,
                n_z=config.n_z,
            )
            survival[0] = initial_diagnostics["survival"]
            shell_sub[0] = initial_diagnostics["shell_populations_subnormalized"]
            shell_norm[0] = initial_diagnostics["shell_populations_normalized"]
            top_sub[0] = initial_diagnostics["top_shell_subnormalized"]
            top_norm[0] = initial_diagnostics["top_shell_normalized"]
            for name in source_names:
                source_curves[name][0] = initial_diagnostics[name]
            if 0 in selected_step_set:
                selected_states[0] = np.asarray(
                    backend.to_cpu(state.reshape(operators.d_channels, config.n_z)),
                    dtype=np.complex128,
                ) / math.sqrt(survival[0])
                selected_survivals[0] = float(survival[0])

            launch_expected = {
                "s_down_normalized": 0.0,
                "s_phi_normalized": 0.0,
                "s_up_normalized": 2.0,
            }
            launch_errors = {
                key: abs(float(initial_diagnostics[key]) - target)
                for key, target in launch_expected.items()
            }
            launch_control_required = config.initial_mode == "00"
            launch_control_pass = bool(
                not launch_control_required
                or max(launch_errors.values(), default=0.0) <= LAUNCH_TOL
            )
            if not launch_control_pass:
                raise RuntimeError(f"Ground-state source launch control failed: {launch_errors}")

            print("[operator audit] PASS")
            print(
                "[roof sign audit] PASS: +K_N/(2*h_z), "
                f"loss residual={propagator.roof_sign_audit['detector_loss_operator_roof_identity_residual']:.3e}"
            )
            print(
                "[launch source audit] "
                f"s_down={initial_diagnostics['s_down_normalized']:.16e}, "
                f"s_phi={initial_diagnostics['s_phi_normalized']:.16e}, "
                f"s_up={initial_diagnostics['s_up_normalized']:.16e}"
            )

            start_time = time.time()
            completed_steps = 0
            for step in range(1, num_steps + 1):
                if step == 1 or step % config.progress_every == 0:
                    elapsed = time.time() - start_time
                    eta_minutes = (
                        (num_steps - step) * elapsed / max(step, 1) / 60.0
                    )
                    print(
                        f"[progress] step {step}/{num_steps}, t={step * config.dt:.6f}, "
                        f"ETA={eta_minutes:.2f} min",
                        flush=True,
                    )

                survival_before = float(survival[step - 1])
                if config.propagator_type == "scalar_factorized":
                    (
                        state_next,
                        p_roof,
                        preclamp_norm,
                        clamp_loss,
                        info,
                        solve_count,
                        true_residual,
                    ) = advance_factorized_scalar(
                        state,
                        backend=backend,
                        propagator=propagator,
                        config=config,
                        operators=operators,
                    )
                else:
                    (
                        state_next,
                        p_roof,
                        preclamp_norm,
                        clamp_loss,
                        info,
                        solve_count,
                        true_residual,
                    ) = advance_monolithic(
                        state,
                        backend=backend,
                        propagator=propagator,
                        config=config,
                        operators=operators,
                    )

                diagnostics = compute_state_diagnostics(
                    state_next,
                    backend=backend,
                    operators=operators,
                    h_z=propagator.h_z,
                    n_z=config.n_z,
                )
                survival_after = float(diagnostics["survival"])
                total_step_loss = survival_before - survival_after
                preclamp_loss = survival_before - preclamp_norm
                flux_residual = preclamp_loss - p_roof

                step_loss_roof[step - 1] = p_roof
                step_loss_total[step - 1] = total_step_loss
                step_loss_clamp[step - 1] = clamp_loss
                step_flux_residual[step - 1] = flux_residual
                true_residuals[step - 1] = true_residual
                gmres_info[step - 1] = info
                gmres_solve_count[step - 1] = solve_count
                survival[step] = survival_after
                shell_sub[step] = diagnostics["shell_populations_subnormalized"]
                shell_norm[step] = diagnostics["shell_populations_normalized"]
                top_sub[step] = diagnostics["top_shell_subnormalized"]
                top_norm[step] = diagnostics["top_shell_normalized"]
                for name in source_names:
                    source_curves[name][step] = diagnostics[name]

                finite_values = np.asarray(
                    [
                        survival_after,
                        p_roof,
                        total_step_loss,
                        clamp_loss,
                        flux_residual,
                        true_residual,
                        diagnostics["s_down_normalized"],
                        diagnostics["s_up_normalized"],
                        diagnostics["s_phi_normalized"],
                        diagnostics["r_K_omit_subnormalized"],
                    ],
                    dtype=np.float64,
                )
                if not np.all(np.isfinite(finite_values)):
                    raise FloatingPointError(
                        f"Non-finite numerical result at step {step}: {finite_values!r}"
                    )
                if info != 0:
                    raise RuntimeError(f"GMRES returned info={info} at step {step}")
                if true_residual > TRUE_RESIDUAL_TOL:
                    raise RuntimeError(
                        f"True relative residual {true_residual:.6e} exceeds "
                        f"{TRUE_RESIDUAL_TOL:.6e} at step {step}"
                    )
                if p_roof < -OPERATOR_TOL:
                    raise RuntimeError(
                        f"Negative midpoint roof probability {p_roof:.6e} at step {step}"
                    )
                if survival_after - survival_before > SURVIVAL_INCREASE_TOL:
                    raise RuntimeError(
                        f"Survival increased by {survival_after-survival_before:.6e} "
                        f"at step {step}"
                    )

                state = state_next
                completed_steps = step
                if step in selected_step_set:
                    if survival_after <= 0.0:
                        raise RuntimeError("Cannot normalize a zero-survival selected state")
                    selected_states[step] = np.asarray(
                        backend.to_cpu(
                            state.reshape(operators.d_channels, config.n_z)
                        ),
                        dtype=np.complex128,
                    ) / math.sqrt(survival_after)
                    selected_survivals[step] = survival_after

                if step % config.checkpoint_every == 0 or step == num_steps:
                    save_checkpoint(
                        stage_dir,
                        config.case_prefix,
                        completed_steps,
                        times=times,
                        survival=survival,
                        step_loss_roof=step_loss_roof,
                        step_loss_total=step_loss_total,
                        step_loss_clamp=step_loss_clamp,
                        step_flux_residual=step_flux_residual,
                        true_residual=true_residuals,
                        gmres_info=gmres_info,
                    )

            backend.synchronize()
            elapsed_seconds = time.time() - start_time

            # Direct detector observables from the midpoint probability sequence.
            D_roof = float(np.sum(step_loss_roof, dtype=np.float64))
            D_norm = float(survival[0] - survival[-1])
            mu_restricted = float(np.trapezoid(survival, times))
            early_mask = midpoint_times < config.t_cut
            D_E = float(np.sum(step_loss_roof[early_mask], dtype=np.float64))
            D_L = float(np.sum(step_loss_roof[~early_mask], dtype=np.float64))
            late_fraction = D_L / D_roof if D_roof > 0.0 else float("nan")
            click_density = step_loss_roof / config.dt
            peak_index = int(np.argmax(click_density))
            peak_t = float(midpoint_times[peak_index])
            peak_g = float(click_density[peak_index])
            conditional_click_mean = (
                (mu_restricted - config.t_final * survival[-1]) / D_roof
                if D_roof > 0.0
                else float("nan")
            )

            closure_residual = float(survival[-1] + D_roof - survival[0])
            closure_relative = abs(closure_residual) / max(
                abs(D_norm), D_roof, 1.0e-15
            )
            telescoping_residual = float(
                survival[-1] + np.sum(step_loss_total, dtype=np.float64) - survival[0]
            )
            decomposed_residual = float(
                survival[-1]
                + D_roof
                + np.sum(step_flux_residual, dtype=np.float64)
                + np.sum(step_loss_clamp, dtype=np.float64)
                - survival[0]
            )

            r_k_omit_cumulative = np.zeros(num_steps + 1, dtype=np.float64)
            r_values = source_curves["r_K_omit_subnormalized"]
            if num_steps > 0:
                r_k_omit_cumulative[1:] = np.cumsum(
                    0.5 * config.dt * (r_values[:-1] + r_values[1:]),
                    dtype=np.float64,
                )

            all_arrays = [
                times,
                midpoint_times,
                survival,
                step_loss_roof,
                shell_sub,
                shell_norm,
                top_sub,
                top_norm,
                click_density,
                true_residuals,
            ] + list(source_curves.values())
            arrays_finite = all(np.all(np.isfinite(array)) for array in all_arrays)
            midpoint_nonnegative = bool(np.min(step_loss_roof) >= -OPERATOR_TOL)
            survival_monotone = bool(
                np.max(np.diff(survival), initial=-np.inf) <= SURVIVAL_INCREASE_TOL
            )
            gmres_all_zero = bool(np.all(gmres_info == 0))
            residual_pass = bool(np.max(true_residuals) <= TRUE_RESIDUAL_TOL)
            clamp_pass = bool(np.sum(step_loss_clamp, dtype=np.float64) <= OPERATOR_TOL)
            closure_pass = bool(
                abs(closure_residual)
                <= max(
                    ROOF_CLOSURE_ABS_TOL,
                    ROOF_CLOSURE_REL_TOL * max(abs(D_norm), D_roof),
                )
            )

            # Independent shell/source consistency checks.  These are not
            # detector probabilities; they certify the diagnostic reductions.
            shell_sub_sum_residual = float(
                np.max(np.abs(np.sum(shell_sub, axis=1) - survival))
            )
            shell_norm_sum_residual = float(
                np.max(np.abs(np.sum(shell_norm, axis=1) - 1.0))
            )
            minimum_shell_population_subnormalized = float(np.min(shell_sub))
            minimum_shell_population_normalized = float(np.min(shell_norm))
            minimum_source_value = float(
                min(
                    np.min(source_curves["s_down_normalized"]),
                    np.min(source_curves["s_up_normalized"]),
                    np.min(source_curves["s_phi_normalized"]),
                )
            )
            top_shell_bounds_pass = bool(
                np.min(top_norm) >= -OPERATOR_TOL
                and np.max(top_norm) <= 1.0 + OPERATOR_TOL
                and np.min(top_sub) >= -OPERATOR_TOL
                and np.max(top_sub - survival) <= OPERATOR_TOL
            )
            shell_population_audit_pass = bool(
                shell_sub_sum_residual <= 5.0e-12
                and shell_norm_sum_residual <= 5.0e-12
                and minimum_shell_population_subnormalized >= -OPERATOR_TOL
                and minimum_shell_population_normalized >= -OPERATOR_TOL
                and top_shell_bounds_pass
            )
            source_nonnegativity_pass = bool(minimum_source_value >= -OPERATOR_TOL)
            scalar_ground_source_invariance_applicable = bool(
                config.detector_label == "scalar" and config.initial_mode == "00"
            )
            scalar_ground_source_invariance_errors = {
                "maximum_abs_s_down": float(
                    np.max(np.abs(source_curves["s_down_normalized"]))
                ),
                "maximum_abs_s_phi": float(
                    np.max(np.abs(source_curves["s_phi_normalized"]))
                ),
                "maximum_abs_s_up_minus_2": float(
                    np.max(np.abs(source_curves["s_up_normalized"] - 2.0))
                ),
            }
            scalar_ground_source_invariance_pass = bool(
                not scalar_ground_source_invariance_applicable
                or max(scalar_ground_source_invariance_errors.values()) <= 5.0e-12
            )

            # Selected insertion vectors, compressed by active channel rows.
            if (
                set(selected_states) != selected_step_set
                or set(selected_survivals) != selected_step_set
            ):
                missing_states = sorted(selected_step_set - set(selected_states))
                missing_survivals = sorted(selected_step_set - set(selected_survivals))
                raise RuntimeError(
                    "Missing selected insertion records: "
                    f"states={missing_states}, survivals={missing_survivals}"
                )
            insertion_archive = build_sparse_insertion_archive(
                selected_states,
                selected_survivals=selected_survivals,
                selected_requested_times=requested_by_step,
                selected_actual_times=actual_by_step,
                operators=operators,
                h_z=propagator.h_z,
                n_z=config.n_z,
            )
            insertion_numeric_arrays_finite = all(
                np.all(np.isfinite(array))
                for array in insertion_archive.values()
                if isinstance(array, np.ndarray)
                and array.dtype.kind in {"b", "u", "i", "f", "c"}
            )
            arrays_finite = bool(arrays_finite and insertion_numeric_arrays_finite)

            # Save required and supporting deterministic outputs atomically.
            atomic_save_npy(
                case_file(stage_dir, config.case_prefix, "times.npy"), times
            )
            atomic_save_npy(
                case_file(stage_dir, config.case_prefix, "survival.npy"), survival
            )
            atomic_save_npy(
                case_file(
                    stage_dir,
                    config.case_prefix,
                    "step_loss_roof_midpoint.npy",
                ),
                step_loss_roof,
            )
            atomic_save_npy(
                case_file(stage_dir, config.case_prefix, "click_midpoint_times.npy"),
                midpoint_times,
            )
            atomic_save_npy(
                case_file(stage_dir, config.case_prefix, "click_density.npy"),
                click_density,
            )
            atomic_save_npy(
                case_file(stage_dir, config.case_prefix, "true_relative_residual.npy"),
                true_residuals,
            )
            atomic_save_npy(
                case_file(stage_dir, config.case_prefix, "gmres_info.npy"), gmres_info
            )
            atomic_save_npy(
                case_file(stage_dir, config.case_prefix, "gmres_solve_count.npy"),
                gmres_solve_count,
            )
            atomic_save_npy(
                case_file(stage_dir, config.case_prefix, "step_loss_total.npy"),
                step_loss_total,
            )
            atomic_save_npy(
                case_file(stage_dir, config.case_prefix, "step_loss_bottom_clamp.npy"),
                step_loss_clamp,
            )
            atomic_save_npy(
                case_file(stage_dir, config.case_prefix, "step_loss_flux_residual.npy"),
                step_flux_residual,
            )

            atomic_savez(
                case_file(stage_dir, config.case_prefix, "shell_populations.npz"),
                shell_indices=np.arange(config.n_shell + 1, dtype=np.int64),
                shell_populations_subnormalized=shell_sub,
                shell_populations_normalized=shell_norm,
                top_shell_population_subnormalized=top_sub,
                top_shell_population_normalized=top_norm,
                interpretation=np.asarray(
                    [
                        "Each row corresponds to a state time. Subnormalized shell populations sum to survival; normalized rows sum to one."
                    ],
                    dtype="U256",
                ),
            )

            source_npz_payload: Dict[str, np.ndarray] = {
                name: array for name, array in source_curves.items()
            }
            source_npz_payload.update(
                {
                    "times": times,
                    "r_K_omit_cumulative_integral": r_k_omit_cumulative,
                    "launch_control_required": np.asarray(
                        [launch_control_required], dtype=np.bool_
                    ),
                    "launch_s_down_expected": np.asarray([0.0], dtype=np.float64),
                    "launch_s_phi_expected": np.asarray([0.0], dtype=np.float64),
                    "launch_s_up_expected": np.asarray([2.0], dtype=np.float64),
                    "interpretation": np.asarray(
                        [
                            "Source norms are detector-only diagnostics. They are not active rates, probabilities, or susceptibilities. r_K_omit is a truncation proxy and is excluded from the detector probability budget."
                        ],
                        dtype="U512",
                    ),
                }
            )
            atomic_savez(
                case_file(stage_dir, config.case_prefix, "source_diagnostics.npz"),
                **source_npz_payload,
            )
            atomic_savez(
                case_file(
                    stage_dir,
                    config.case_prefix,
                    "selected_insertion_vectors.npz",
                ),
                compressed=True,
                **insertion_archive,
            )

            recovery_target = STAGE01_RECOVERY_TARGETS.get(
                (float(config.omega), config.detector_label, config.initial_mode)
            )
            observed_metrics = {
                "S_T": float(survival[-1]),
                "D_roof": D_roof,
                "D_norm": D_norm,
                "mu_restricted": mu_restricted,
                "D_E": D_E,
                "D_L": D_L,
                "late_fraction": late_fraction,
                "conditional_click_mean_before_horizon": conditional_click_mean,
                "peak_t": peak_t,
                "peak_g": peak_g,
            }
            recovery_differences = (
                {
                    key: observed_metrics[key] - recovery_target[key]
                    for key in recovery_target
                    if key in observed_metrics
                }
                if recovery_target is not None
                else None
            )

            solver_checks = {
                "operator_audit": bool(operator_audit["all_checks_passed"]),
                "source_launch_control": launch_control_pass,
                "gmres_return_codes_zero": gmres_all_zero,
                "true_relative_residual": residual_pass,
                "midpoint_roof_probabilities_nonnegative": midpoint_nonnegative,
                "survival_nonincreasing_within_tolerance": survival_monotone,
                "all_saved_numerical_arrays_finite": arrays_finite,
                "bottom_clamp_loss_zero": clamp_pass,
                "roof_norm_probability_closure": closure_pass,
                "telescoping_norm_loss_closure": abs(telescoping_residual) <= 5e-13,
                "decomposed_probability_closure": (abs(decomposed_residual) <= DECOMPOSED_CLOSURE_ABS_TOL),
                "shell_population_normalization_and_bounds": shell_population_audit_pass,
                "source_diagnostics_nonnegative": source_nonnegativity_pass,
                "scalar_ground_source_invariance": scalar_ground_source_invariance_pass,
                "selected_insertion_vectors_saved": bool(
                    insertion_archive["vector_names"].size > 0
                ),
                "fixed_directory_and_case_prefix_policy": bool(
                    stage_dir.name == STAGE_DIRECTORY
                    and all(
                        path.name.startswith(config.case_prefix + "_")
                        for path in stable_output_files(stage_dir, config.case_prefix)
                    )
                ),
            }
            all_solver_checks = all(solver_checks.values())

            solver_audit: Dict[str, Any] = {
                "stage": STAGE_NAME,
                "script_version": SCRIPT_VERSION,
                "case_prefix": config.case_prefix,
                "configuration_sha256": config_payload["configuration_sha256"],
                "source_sha256": script_sha256,
                "propagator_type": config.propagator_type,
                "detector_label": config.detector_label,
                "initial_mode": config.initial_mode,
                "omega": config.omega,
                "N_shell": config.n_shell,
                "M_N": operators.m_modes,
                "d_channels": operators.d_channels,
                "N_z": config.n_z,
                "h_z": propagator.h_z,
                "dt": config.dt,
                "T_final": config.t_final,
                "num_steps": num_steps,
                "observed_detector_metrics": observed_metrics,
                "cartesian_stage01_recovery_target": recovery_target,
                "oscillator_minus_cartesian_integrated_differences": recovery_differences,
                "probability_audit": {
                    "initial_survival": float(survival[0]),
                    "final_survival": float(survival[-1]),
                    "initial_minus_final_survival": D_norm,
                    "cumulative_roof_midpoint_loss": D_roof,
                    "roof_closure_residual": closure_residual,
                    "roof_closure_relative": closure_relative,
                    "telescoping_residual": telescoping_residual,
                    "decomposed_residual": decomposed_residual,
                    "cumulative_bottom_clamp_loss": float(
                        np.sum(step_loss_clamp, dtype=np.float64)
                    ),
                    "minimum_roof_step_probability": float(np.min(step_loss_roof)),
                    "minimum_total_step_loss": float(np.min(step_loss_total)),
                    "maximum_survival_increase": float(
                        max(0.0, np.max(np.diff(survival), initial=-np.inf))
                    ),
                },
                "linear_solver_audit": {
                    "gmres_failure_count": int(np.count_nonzero(gmres_info != 0)),
                    "maximum_true_relative_residual": float(np.max(true_residuals)),
                    "minimum_true_relative_residual": float(np.min(true_residuals)),
                    "total_gmres_solves": int(np.sum(gmres_solve_count, dtype=np.int64)),
                    "frozen_true_residual_tolerance": TRUE_RESIDUAL_TOL,
                },
                "source_launch_audit": {
                    "required_for_mode00": launch_control_required,
                    "observed": {
                        key: float(initial_diagnostics[key]) for key in launch_expected
                    },
                    "expected": launch_expected,
                    "absolute_errors": launch_errors,
                    "passed": launch_control_pass,
                },
                "shell_population_audit": {
                    "maximum_subnormalized_shell_sum_residual": shell_sub_sum_residual,
                    "maximum_normalized_shell_sum_residual": shell_norm_sum_residual,
                    "minimum_subnormalized_shell_population": (
                        minimum_shell_population_subnormalized
                    ),
                    "minimum_normalized_shell_population": (
                        minimum_shell_population_normalized
                    ),
                    "top_shell_bounds_passed": top_shell_bounds_pass,
                    "passed": shell_population_audit_pass,
                },
                "source_curve_summary": {
                    "maximum_s_down_normalized": float(
                        np.max(source_curves["s_down_normalized"])
                    ),
                    "maximum_s_phi_normalized": float(
                        np.max(source_curves["s_phi_normalized"])
                    ),
                    "minimum_s_up_normalized": float(
                        np.min(source_curves["s_up_normalized"])
                    ),
                    "minimum_of_all_normalized_source_diagnostics": (
                        minimum_source_value
                    ),
                    "all_normalized_source_diagnostics_nonnegative": (
                        source_nonnegativity_pass
                    ),
                    "scalar_ground_source_invariance": {
                        "applicable": scalar_ground_source_invariance_applicable,
                        "errors": scalar_ground_source_invariance_errors,
                        "passed": scalar_ground_source_invariance_pass,
                    },
                    "maximum_top_shell_population_normalized": float(np.max(top_norm)),
                    "final_r_K_omit_cumulative_integral": float(
                        r_k_omit_cumulative[-1]
                    ),
                },
                "insertion_vector_audit": {
                    "selected_steps": selected_steps_array.tolist(),
                    "requested_times": requested_times_array.tolist(),
                    "actual_times": actual_times_array.tolist(),
                    "number_of_unique_vector_records": int(
                        insertion_archive["vector_names"].size
                    ),
                    "number_of_retained_channel_rows": int(
                        insertion_archive["channel_indices"].size
                    ),
                    "maximum_relative_omitted_norm2": float(
                        np.max(
                            np.divide(
                                insertion_archive["vector_omitted_norm2"],
                                np.maximum(
                                    insertion_archive["vector_total_norm2"],
                                    np.finfo(float).tiny,
                                ),
                            )
                        )
                    ),
                    "a_dagger_a_aliases": {
                        "a_x_dagger_a_x_psi_nc": "N_x_psi_nc",
                        "a_y_dagger_a_y_psi_nc": "N_y_psi_nc",
                    },
                },
                "acceptance_tolerances": {
                    "operator": OPERATOR_TOL,
                    "launch": LAUNCH_TOL,
                    "true_relative_residual": TRUE_RESIDUAL_TOL,
                    "survival_increase": SURVIVAL_INCREASE_TOL,
                    "roof_closure_relative": ROOF_CLOSURE_REL_TOL,
                    "roof_closure_absolute": ROOF_CLOSURE_ABS_TOL,
                },
                "checks": solver_checks,
                "all_checks_passed": all_solver_checks,
            }
            ensure_finite_mapping(solver_audit)
            solver_audit_path = case_file(
                stage_dir, config.case_prefix, "solver_audit.json"
            )
            atomic_write_json(solver_audit_path, solver_audit)

            # Remove checkpoint only after a completed stable save.
            checkpoint_path = case_file(stage_dir, config.case_prefix, "checkpoint.npz")
            if checkpoint_path.exists():
                checkpoint_path.unlink()

            stable_paths = stable_output_files(stage_dir, config.case_prefix)
            output_hashes = {path.name: sha256_file(path) for path in stable_paths}
            output_manifest = {
                "hash_algorithm": "SHA-256",
                "case_prefix": config.case_prefix,
                "configuration_sha256": config_payload["configuration_sha256"],
                "source_sha256": script_sha256,
                "files": output_hashes,
            }
            output_hash_path = case_file(
                stage_dir, config.case_prefix, "output_hashes.json"
            )
            atomic_write_json(output_hash_path, output_manifest)

            rerun_comparison = compare_previous_hashes(
                previous_configuration,
                previous_manifest,
                config_payload["configuration_sha256"],
                output_hashes,
            )
            expected_case_files = {
                path.name for path in stage_dir.glob(f"{config.case_prefix}_*") if path.is_file()
            }
            unexpected_stale = sorted(
                name
                for name in expected_case_files
                if name.endswith(".tmp") or name.endswith(".old")
            )
            overwrite_audit = {
                "stale_same_prefix_files_removed_before_run": stale_removed,
                "temporary_or_old_files_remaining": unexpected_stale,
                "safe_replacement_passed": not unexpected_stale,
                "same_directory_rerun_comparison": rerun_comparison,
            }

            status.update(
                {
                    "status": "completed" if all_solver_checks else "completed_with_failed_gate",
                    "completed_utc": utc_now_iso(),
                    "completed_steps": completed_steps,
                    "elapsed_seconds": elapsed_seconds,
                    "all_solver_checks_passed": all_solver_checks,
                    "configuration_sha256": config_payload["configuration_sha256"],
                    "output_hash_manifest": output_hash_path.name,
                    "output_hash_manifest_sha256": sha256_file(output_hash_path),
                    "overwrite_and_rerun_audit": overwrite_audit,
                }
            )
            atomic_write_json(status_path, status)
            update_stage_manifest(
                stage_dir,
                config.case_prefix,
                {
                    "status": status["status"],
                    "propagator_type": config.propagator_type,
                    "initial_mode": config.initial_mode,
                    "omega": config.omega,
                    "N_shell": config.n_shell,
                    "dt": config.dt,
                    "T_final": config.t_final,
                    "configuration": configuration_path.name,
                    "operator_audit": operator_audit_path.name,
                    "solver_audit": solver_audit_path.name,
                    "output_hashes": output_hash_path.name,
                    "updated_utc": status["completed_utc"],
                },
            )

            print("\n[Task-05 solver verdict]")
            print(f"  all checks passed:          {all_solver_checks}")
            print(f"  final survival:            {survival[-1]:.12e}")
            print(f"  cumulative roof loss:      {D_roof:.12e}")
            print(f"  roof closure relative:     {closure_relative:.3e}")
            print(f"  maximum true residual:     {np.max(true_residuals):.3e}")
            print(f"  maximum top-shell pop nc:  {np.max(top_norm):.3e}")
            print(f"  execution time:            {elapsed_seconds:.2f} s")
            print(f"  output directory:          {stage_dir}")

            # A numerically completed case with a failed scientific gate is
            # preserved as such; ``main`` returns exit status 2 rather than
            # relabeling it as an execution/I-O failure.
            return {
                "stage_dir": stage_dir,
                "case_prefix": config.case_prefix,
                "configuration": config_payload,
                "operator_audit": operator_audit,
                "solver_audit": solver_audit,
                "run_status": status,
                "output_hashes": output_manifest,
            }

        except Exception as exc:
            failure = {
                "status": "failed",
                "failed_utc": utc_now_iso(),
                "case_prefix": config.case_prefix,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc(),
            }
            atomic_write_json(
                case_file(stage_dir, config.case_prefix, "failure.json"), failure
            )
            status.update(failure)
            atomic_write_json(status_path, status)
            update_stage_manifest(
                stage_dir,
                config.case_prefix,
                {
                    "status": "failed",
                    "failure": case_file(
                        stage_dir, config.case_prefix, "failure.json"
                    ).name,
                    "updated_utc": failure["failed_utc"],
                },
            )
            logging.exception("Task-05 case failed")
            raise
        finally:
            try:
                sys.stdout = original_stdout
                stdout_handle.close()
            except Exception:
                pass
            fcntl.flock(case_lock.fileno(), fcntl.LOCK_UN)


# =============================================================================
# REDUCED INTERNAL SMOKE TEST (NOT A PRODUCTION SWEEP)
# =============================================================================
def run_internal_smoke_test(out_root: Optional[Path] = None) -> Dict[str, Any]:
    """Execute reduced CPU checks for all three map branches.

    This function is never called by the production ``main`` path.  It exists
    solely so the delivered source can be compiled and exercised on a machine
    without CUDA.  The smoke calculation uses a reduced longitudinal grid and
    a packet closer to the roof; its numerical values are not production data.
    """

    if out_root is None:
        out_root = Path(tempfile.mkdtemp(prefix="task05_smoke_"))
    else:
        out_root = Path(out_root)
        out_root.mkdir(parents=True, exist_ok=True)

    base = RunConfig(
        propagator_type="spinor",
        initial_mode="00",
        omega=4.0,
        n_shell=2,
        dt=2.0e-3,
        t_final=1.0e-2,
        case_prefix="smoke_spinor",
        out_root=out_root,
        backend="scipy",
        n_z=96,
        l_z=20.0,
        z0=19.2,
        sigma_z_amplitude=0.7,
        k0=math.pi,
        kappa=math.pi,
        theta=math.pi / 6.0,
        phi=0.0,
        t_cut=6.0e-3,
        progress_every=1000,
        checkpoint_every=1000,
        smoke_test=True,
    )

    results: Dict[str, Any] = {}
    for propagator_type in (
        "scalar_factorized",
        "scalar_monolithic",
        "spinor",
    ):
        case = replace(
            base,
            propagator_type=propagator_type,
            case_prefix=f"smoke_{propagator_type}",
        )
        results[propagator_type] = run_case(case)

    # A second identical spinor run checks same-directory replacement and
    # deterministic stable-output hashes.
    repeated = run_case(base)
    first_spinor = results["spinor"]
    results["spinor_same_directory_repeat"] = repeated
    results["stable_hashes_match_on_repeat"] = bool(
        first_spinor["output_hashes"]["files"]
        == repeated["output_hashes"]["files"]
    )
    results["smoke_root"] = str(out_root)
    return results


def main() -> int:
    config = manual_run_config()
    result = run_case(config)
    return 0 if result["solver_audit"]["all_checks_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
