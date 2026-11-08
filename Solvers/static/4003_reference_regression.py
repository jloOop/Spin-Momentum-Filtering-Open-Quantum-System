#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
00_reference_regression_solver.py
=================================
Strict zero-ambient-bath propagation and raw numerical-audit solver based on
``750.Ref.py``.

Scientific purpose
------------------
This script establishes the authoritative detector-only reference before any
open-system bath operator is introduced.  It supports one detector per run:

    --detector spinor   : the verified spin-coupled ABC, Lap_diag + C
    --detector scalar   : the componentwise scalar ABC, Lap_diag

The following numerical core is retained from ``750.Ref.py``:

* the Cartesian mesh and Gaussian reference state;
* ``L_z`` and ``L_dirichlet``;
* the Kronecker construction of ``Lap_scalar`` and ``Lap_diag``;
* the spinor roof matrix ``C`` and ``Lap_spinor = Lap_diag + C``;
* the harmonic potential;
* the Crank--Nicolson matrices;
* complex128 GMRES, the diagonal preconditioner, and all GMRES parameters;
* the post-solve Dirichlet assignments.

Only indispensable numerical diagnostics, detector selection, metadata,
checkpointing, and hashing are added around that core. No ambient bath is
present. Scientific reductions, reference comparisons, and plotting belong to
``00_reference_regression_loader.py``.

Primary step diagnostics
------------------------
For every Crank--Nicolson step n -> n+1 the script records:

1. ``step_loss_roof_midpoint``

       dt * kappa * hx * hy * sum_roof |(psi_n + psi_{n+1}^{CN})/2|^2,

   the exact Cayley midpoint roof-loss expression for the implemented ABC
   closure when the linear system is solved exactly;

2. ``step_loss_preclamp``

       S_n - ||psi_{n+1}^{cast,preclamp}||^2,

   obtained from the actual propagated state, before the explicit boundary
   cleanup;

3. ``step_loss_clamp``

   the probability present on the unique Dirichlet boundary nodes immediately
   before they are reset to zero;

4. ``step_loss_total``

       S_n - S_{n+1},

   the exact norm change of the state actually carried to the next step.

The difference between (2) and (1) is the combined finite-GMRES/cast residual.
At a configurable audit cadence it is split into a true GMRES/CN residual and
complex128->complex64 cast loss.

Typical use
-----------
Place this file beside the unmodified reference source and run, for example,

    python 00_reference_regression_solver.py \
        --detector spinor \
        --reference-source 750.Ref.py \
        --out-root runs

    python 00_reference_regression_solver.py \
        --detector scalar \
        --reference-source 750.Ref.py \
        --out-root runs

The physical and solver defaults are intentionally frozen to the uploaded
reference: omega=100 unless OMEGA is set, dt=5e-4, T_final=20, and the same
100 x 100 x 1500 grid.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import platform
import shutil
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

import numpy as np
import cupy as cp
from cupyx.scipy.sparse import diags, eye, kron, coo_matrix, csr_matrix, bmat
from cupyx.scipy.sparse.linalg import gmres, LinearOperator


EXPECTED_REFERENCE_SHA256 = (
    "815a470da8ec7664ee613f830f384050247f949dac5fa8ab4e0cfd8f331cfbfe"
)
SCRIPT_VERSION = "2026-08-01-reference-regression-solver-v1"


# -----------------------------------------------------------------------------
# General utilities
# -----------------------------------------------------------------------------
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


def sha256_json(payload: Dict[str, Any]) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
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


def to_cpu(arr: cp.ndarray) -> np.ndarray:
    return cp.asnumpy(arr)


def cp_float(value: Any) -> float:
    return float(cp.asnumpy(value))


def sanitize_label(label: str) -> str:
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.=")
    cleaned = "".join(ch if ch in allowed else "_" for ch in label.strip())
    return cleaned or "run"


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


# -----------------------------------------------------------------------------
# Diagnostic reductions.  These do not enter the propagated state.
# -----------------------------------------------------------------------------
def norm2_uniform(psi: cp.ndarray, dvol: float) -> float:
    """Return sum |psi|^2 dV with float64 accumulation."""
    density = psi.real * psi.real + psi.imag * psi.imag
    return cp_float(cp.sum(density, dtype=cp.float64)) * dvol


def _probability_and_max(arr: cp.ndarray, dvol: float) -> Tuple[float, float]:
    if arr.size == 0:
        return 0.0, 0.0
    density = arr.real * arr.real + arr.imag * arr.imag
    probability = cp_float(cp.sum(density, dtype=cp.float64)) * dvol
    maximum = cp_float(cp.max(cp.abs(arr)))
    return probability, maximum


def dirichlet_boundary_audit(
    psi_3d: cp.ndarray, dvol: float
) -> Tuple[float, float]:
    """
    Probability and maximum amplitude on the unique nodes that the reference
    solver explicitly clamps to zero.

    The partition avoids double counting edges and corners:
      * both x sidewalls, all y,z;
      * both y sidewalls with x sidewalls removed;
      * bottom plane with both sidewall sets removed.
    """
    probability = 0.0
    maximum = 0.0

    pieces = (
        psi_3d[:, 0, :, :],
        psi_3d[:, -1, :, :],
        psi_3d[:, 1:-1, 0, :],
        psi_3d[:, 1:-1, -1, :],
        psi_3d[:, 1:-1, 1:-1, 0],
    )
    for piece in pieces:
        p_piece, max_piece = _probability_and_max(piece, dvol)
        probability += p_piece
        maximum = max(maximum, max_piece)
    return probability, maximum


def enforce_dirichlet_reference(psi_3d: cp.ndarray) -> None:
    """The post-GMRES boundary assignments from 750.Ref.py, unchanged."""
    psi_up = psi_3d[0]
    psi_down = psi_3d[1]

    psi_up[[0, -1], :, :] = 0
    psi_up[:, [0, -1], :] = 0
    psi_up[:, :, 0] = 0
    psi_down[[0, -1], :, :] = 0
    psi_down[:, [0, -1], :] = 0
    psi_down[:, :, 0] = 0


def roof_midpoint_loss(
    psi_in64: cp.ndarray,
    psi_out64: cp.ndarray,
    *,
    nx: int,
    ny: int,
    nz: int,
    dt: float,
    k_bc: float,
    hx: float,
    hy: float,
) -> float:
    """
    Exact finite-step ABC roof loss for the Cayley midpoint, up to the GMRES
    solve residual:

        p_D,n = dt * kappa * hx * hy * sum_{x,y,spin} |q(x,y,z_top)|^2,
        q = (psi_n + psi_{n+1}^{CN})/2.
    """
    psi_in_3d = psi_in64.reshape(2, nx, ny, nz)
    psi_out_3d = psi_out64.reshape(2, nx, ny, nz)
    q_roof = 0.5 * (psi_in_3d[:, :, :, -1] + psi_out_3d[:, :, :, -1])
    density = q_roof.real * q_roof.real + q_roof.imag * q_roof.imag
    roof_sum = cp_float(cp.sum(density, dtype=cp.float64))
    return dt * k_bc * hx * hy * roof_sum


def true_relative_residual(
    a64: csr_matrix, solution64: cp.ndarray, rhs64: cp.ndarray
) -> float:
    residual = a64 @ solution64 - rhs64
    numerator = cp_float(cp.linalg.norm(residual))
    denominator = cp_float(cp.linalg.norm(rhs64))
    if denominator == 0.0:
        return numerator
    return numerator / denominator


def sparse_adjoint(matrix: csr_matrix) -> csr_matrix:
    return matrix.transpose().conj().tocsr()


def sparse_max_abs(matrix: csr_matrix) -> float:
    if matrix.nnz == 0:
        return 0.0
    return cp_float(cp.max(cp.abs(matrix.data)))


# -----------------------------------------------------------------------------
# Argument handling and provenance
# -----------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    default_reference = Path(__file__).with_name("750.Ref.py")
    if not default_reference.exists() and Path("[ARCHIVE_PATH]").exists():
        default_reference = Path("[ARCHIVE_PATH]")

    parser = argparse.ArgumentParser(
        description=(
            "Zero-bath scalar/spinor regression using the frozen 750.Ref.py "
            "Hamiltonian, ABC, CN, and GMRES implementation."
        )
    )
    parser.add_argument(
        "--detector",
        choices=("spinor", "scalar"),
        default=os.getenv("DETECTOR", "spinor").lower(),
        help="Detector to run. Use two separate runs for the scalar/spinor pair.",
    )
    parser.add_argument(
        "--reference-source",
        type=Path,
        default=default_reference,
        help="Path to the unmodified 750.Ref.py used for provenance checking.",
    )
    parser.add_argument(
        "--out-root",
        type=Path,
        default=Path(os.getenv("OUTDIR", ".")),
        help="Root directory containing the fixed omega-specific output directory.",
    )
    parser.add_argument(
        "--run-label",
        default=None,
        help="Deprecated compatibility option; ignored because the directory name depends only on OMEGA.",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=100,
        help="Console progress cadence in time steps.",
    )
    parser.add_argument(
        "--residual-every",
        type=int,
        default=100,
        help="Cadence for the expensive true GMRES residual and cast audit.",
    )
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=1000,
        help="Cadence for an atomic partial checkpoint.",
    )
    parser.add_argument(
        "--allow-reference-hash-mismatch",
        action="store_true",
        help="Permit execution when 750.Ref.py does not match the frozen hash.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Deprecated compatibility option; existing omega directories are always reused.",
    )
    args = parser.parse_args()

    if args.detector not in {"spinor", "scalar"}:
        parser.error("--detector must be either 'spinor' or 'scalar'")
    for name in ("progress_every", "residual_every", "checkpoint_every"):
        if getattr(args, name) <= 0:
            parser.error(f"--{name.replace('_', '-')} must be positive")
    return args


def gpu_metadata() -> Dict[str, Any]:
    metadata: Dict[str, Any] = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy_version": np.__version__,
        "cupy_version": cp.__version__,
    }
    try:
        device_id = int(cp.cuda.runtime.getDevice())
        properties = cp.cuda.runtime.getDeviceProperties(device_id)
        name = properties.get("name", "unknown")
        if isinstance(name, bytes):
            name = name.decode("utf-8", errors="replace")
        free_mem, total_mem = cp.cuda.Device(device_id).mem_info
        metadata.update(
            {
                "cuda_device_id": device_id,
                "cuda_device_name": str(name),
                "cuda_compute_capability": [
                    int(properties.get("major", -1)),
                    int(properties.get("minor", -1)),
                ],
                "cuda_total_memory_bytes": int(total_mem),
                "cuda_free_memory_bytes_at_start": int(free_mem),
                "cuda_driver_version": int(cp.cuda.runtime.driverGetVersion()),
                "cuda_runtime_version": int(cp.cuda.runtime.runtimeGetVersion()),
            }
        )
    except Exception as exc:  # metadata failure must not alter the calculation
        metadata["cuda_metadata_error"] = repr(exc)
    return metadata


def save_checkpoint(
    out_dir: Path,
    completed_steps: int,
    *,
    times: np.ndarray,
    survival: np.ndarray,
    step_loss_roof: np.ndarray,
    step_loss_preclamp: np.ndarray,
    step_loss_clamp: np.ndarray,
    step_loss_total: np.ndarray,
    step_loss_flux_residual: np.ndarray,
    boundary_max_preclamp: np.ndarray,
    gmres_info: np.ndarray,
    audit_steps: Iterable[int],
    audit_true_residual: Iterable[float],
    audit_solve_norm: Iterable[float],
    audit_solver_flux_residual: Iterable[float],
    audit_cast_loss: Iterable[float],
) -> None:
    k = completed_steps
    atomic_savez(
        out_dir / "4002_reference_regression_Omega=1.npz",
        completed_steps=np.asarray([k], dtype=np.int64),
        times=times[: k + 1],
        survival=survival[: k + 1],
        step_loss_roof_midpoint=step_loss_roof[:k],
        step_loss_preclamp=step_loss_preclamp[:k],
        step_loss_clamp=step_loss_clamp[:k],
        step_loss_total=step_loss_total[:k],
        step_loss_flux_residual=step_loss_flux_residual[:k],
        boundary_max_preclamp=boundary_max_preclamp[:k],
        gmres_info=gmres_info[:k],
        audit_steps=np.asarray(list(audit_steps), dtype=np.int64),
        audit_true_relative_residual=np.asarray(
            list(audit_true_residual), dtype=np.float64
        ),
        audit_solve_norm=np.asarray(list(audit_solve_norm), dtype=np.float64),
        audit_solver_flux_residual=np.asarray(
            list(audit_solver_flux_residual), dtype=np.float64
        ),
        audit_cast_loss=np.asarray(list(audit_cast_loss), dtype=np.float64),
    )




# -----------------------------------------------------------------------------
# Main calculation
# -----------------------------------------------------------------------------
def main() -> int:
    args = parse_args()

    reference_source = args.reference_source.expanduser().resolve()
    if not reference_source.exists():
        raise FileNotFoundError(
            f"Reference source not found: {reference_source}. "
            "Pass --reference-source /path/to/750.Ref.py."
        )
    reference_sha256 = sha256_file(reference_source)
    if (
        reference_sha256 != EXPECTED_REFERENCE_SHA256
        and not args.allow_reference_hash_mismatch
    ):
        raise RuntimeError(
            "The supplied 750.Ref.py does not match the frozen authoritative hash.\n"
            f"Expected: {EXPECTED_REFERENCE_SHA256}\n"
            f"Found:    {reference_sha256}\n"
            "Use --allow-reference-hash-mismatch only after an explicit audit."
        )

    omega_env = os.getenv("OMEGA", None)
    omega = float(omega_env) if omega_env is not None else 1.0
    if not np.isfinite(omega) or omega <= 0.0:
        raise ValueError(f"OMEGA must be a finite positive number; received {omega!r}")

    # The output directory is fixed by omega only. Repeated executions for the
    # same omega reuse this exact directory, regardless of detector, run time,
    # date, or optional legacy CLI labels.
    run_name = f"4000.Reference_regrecession_{omega:g}"
    out_dir = args.out_root.expanduser().resolve() / run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    original_stdout = sys.stdout
    stdout_handle = (out_dir / "stdout.txt").open("w", encoding="utf-8")
    sys.stdout = Tee(original_stdout, stdout_handle)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(out_dir / "simulation_log.txt"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )

    script_path = Path(__file__).resolve()
    script_sha256 = sha256_file(script_path)
    shutil.copy2(script_path, out_dir / script_path.name)
    shutil.copy2(reference_source, out_dir / "750.Ref.py")

    status: Dict[str, Any] = {
        "status": "initializing",
        "started_utc": utc_now_iso(),
        "script_version": SCRIPT_VERSION,
        "detector": args.detector,
        "output_directory": str(out_dir),
        "reference_source": str(reference_source),
        "reference_sha256": reference_sha256,
        "reference_hash_expected": EXPECTED_REFERENCE_SHA256,
        "reference_hash_matches": reference_sha256 == EXPECTED_REFERENCE_SHA256,
        "script_sha256": script_sha256,
    }
    atomic_write_json(out_dir / "run_status.json", status)

    print(f"[info] backend: CuPy")
    print(f"[info] detector: {args.detector}")
    print(f"[info] reference SHA-256: {reference_sha256}")
    print(f"[info] script SHA-256:    {script_sha256}")
    print(f"[info] output directory: {out_dir}")

    # ------------------------------------------------------------------
    # Parameters from 750.Ref.py.  Frozen for this regression script.
    # ------------------------------------------------------------------
    DTYPE_R, DTYPE_C = cp.float32, cp.complex64

    Nx = 100
    Ny = 100
    Nz = 1500
    ell = 10.0

    Lx = ell / np.sqrt(omega)
    Ly = ell / np.sqrt(omega)
    Lz = 20.0

    dt = float(1e-3)
    T_final = 10.0

    Vxy0 = omega**2
    V0z = 0.0
    alpha = 0.0
    k_bc = float(cp.pi)

    z0 = 10.0
    sigma_z = 0.5
    k0 = float(cp.pi)

    theta = float(np.pi/6)
    phi = np.float32(0.0)

    gmres_rtol = 1e-7
    gmres_atol = 0.0
    gmres_maxiter = 1000
    gmres_restart = 30

    # ------------------------------------------------------------------
    # Mesh and initial state: same formulas and indexing as 750.Ref.py.
    # ------------------------------------------------------------------
    x = cp.linspace(0.0, Lx, Nx, endpoint=False, dtype=DTYPE_R)
    y = cp.linspace(0.0, Ly, Ny, endpoint=False, dtype=DTYPE_R)
    z = cp.linspace(0.0, Lz, Nz, endpoint=False, dtype=DTYPE_R)

    hx = float(x[1] - x[0])
    hy = float(y[1] - y[0])
    hz = float(z[1] - z[0])
    dvol = hx * hy * hz
    z_roof_grid = float(cp.asnumpy(z[-1]))

    X, Y, Z = cp.meshgrid(x, y, z, indexing="ij")
    Rho2 = (X - Lx / 2) ** 2 + (Y - Ly / 2) ** 2
    psi_xy = cp.exp(-omega * Rho2 / 2)
    psi_z = cp.exp(-(Z - z0) ** 2 / (2 * sigma_z**2)) * cp.exp(
        1j * k0 * (Z - z0)
    )
    psi_scalar = (psi_xy * psi_z).astype(DTYPE_C)

    c_up = cp.cos(theta / 2)
    c_down = cp.sin(theta / 2) * cp.exp(1j * phi)
    psi_up = (c_up * psi_scalar).astype(DTYPE_C)
    psi_down = (c_down * psi_scalar).astype(DTYPE_C)

    # Initial Dirichlet enforcement from the reference.
    psi_up[[0, -1], :, :] = 0
    psi_up[:, [0, -1], :] = 0
    psi_up[:, :, 0] = 0
    psi_down[[0, -1], :, :] = 0
    psi_down[:, [0, -1], :] = 0
    psi_down[:, :, 0] = 0

    def normalize_wavefunction(
        psi_up_local: cp.ndarray,
        psi_down_local: cp.ndarray,
        hx_local: float,
        hy_local: float,
        hz_local: float,
    ) -> Tuple[cp.ndarray, cp.ndarray]:
        total_prob = cp.sum(
            cp.abs(psi_up_local) ** 2 + cp.abs(psi_down_local) ** 2
        ) * (hx_local * hy_local * hz_local)
        norm = cp.sqrt(total_prob)
        psi_up_local /= norm
        psi_down_local /= norm
        return psi_up_local, psi_down_local

    psi_up, psi_down = normalize_wavefunction(psi_up, psi_down, hx, hy, hz)
    psi_flat = cp.concatenate((psi_up.ravel(), psi_down.ravel())).astype(DTYPE_C)

    rho0 = cp.abs(psi_up) ** 2 + cp.abs(psi_down) ** 2
    initial_boundary_report = {
        "rho_bottom_plane_max": cp_float(cp.max(rho0[:, :, 0])),
        "rho_sidewall_x0_max": cp_float(cp.max(rho0[0, :, :])),
        "rho_sidewall_y0_max": cp_float(cp.max(rho0[:, 0, :])),
        "rho_detector_plane_max": cp_float(cp.max(rho0[:, :, -1])),
    }
    for key, value in initial_boundary_report.items():
        print(f"[initial] {key} = {value:.16e}")

    del X, Y, Z, Rho2, psi_xy, psi_z, psi_scalar, rho0
    cp.get_default_memory_pool().free_all_blocks()

    # ------------------------------------------------------------------
    # Potential: same construction as 750.Ref.py; no absorber.
    # ------------------------------------------------------------------
    Xv = (x - Lx / 2) ** 2
    Yv = (y - Ly / 2) ** 2
    V_xy = 0.5 * Vxy0 * (Xv[:, None] + Yv[None, :])
    V_real = V_xy[:, :, None]
    V_abs = 0.0
    V = V_real.astype(DTYPE_C) + V_abs
    V_diag = cp.repeat(V_xy.ravel(), Nz).astype(DTYPE_C)
    V_full = cp.concatenate((V_diag, V_diag))

    del Xv, Yv, V_real, V_abs, V
    cp.get_default_memory_pool().free_all_blocks()

    # ------------------------------------------------------------------
    # Operators copied from 750.Ref.py.
    # ------------------------------------------------------------------
    def L_z(N_z, dz, k_bc):
        """
        Discretizes H = -(1/2) d^2/dz^2 with:
          z=0 : Dirichlet
          z=L : Robin ABC (∂z ψ + i k_bc ψ = 0)
        Returns CSR matrix.
        """
        inv = 1.0 / (dz * dz)
        data, indices, indptr = [], [], [0]
        for i in range(N_z):
            if i == 0:
                indptr.append(len(indices))
            elif i == N_z - 1:
                indices += [i - 1, i]
                data += [-0.5 * inv, 0.5 * inv - 1j * k_bc / (2.0 * dz)]
                indptr.append(len(indices))
            else:
                left = i - 1
                right = i + 1
                if left == 0:
                    indices += [i, right]
                    data += [inv, -0.5 * inv]
                    indptr.append(len(indices))
                else:
                    indices += [left, i, right]
                    data += [-0.5 * inv, inv, -0.5 * inv]
                    indptr.append(len(indices))
        data = cp.array(data, dtype=DTYPE_C)
        indices = cp.array(indices, dtype=cp.int32)
        indptr = cp.array(indptr, dtype=cp.int32)
        return csr_matrix((data, indices, indptr), shape=(N_z, N_z))

    def L_dirichlet(N, d):
        inv_d2 = 1 / d**2
        half_inv_d2 = 0.5 * inv_d2
        data, indices, indptr = [], [], [0]
        for i in range(N):
            if i == 0 or i == N - 1:
                indptr.append(indptr[-1])
            else:
                left = i-1
                right = i+1
                if left == 0:
                    indices.extend([i, right])
                    data.extend([inv_d2, -half_inv_d2])
                    indptr.append(indptr[-1] + 2)
                elif right == N-1:
                    indices.extend([left, i])
                    data.extend([-half_inv_d2, inv_d2])
                    indptr.append(indptr[-1] + 2)
                else:
                    indices.extend([left, i, right])
                    data.extend([-half_inv_d2, inv_d2, -half_inv_d2])
                    indptr.append(indptr[-1] + 3)
        data = cp.array(data, dtype=DTYPE_C)
        indices = cp.array(indices, dtype=cp.int32)
        indptr = cp.array(indptr, dtype=cp.int32)
        return csr_matrix((data, indices, indptr), shape=(N, N))

    L1 = L_z(Nz, hz, k_bc)
    L2 = L_dirichlet(Nx, hx)
    L3 = L_dirichlet(Ny, hy)

    Ix = eye(Nx, dtype=DTYPE_C, format="csr")
    Iy = eye(Ny, dtype=DTYPE_C, format="csr")
    Iz = eye(Nz, dtype=DTYPE_C, format="csr")

    Lap_scalar = (
        kron(L2, kron(Iy, Iz))
        + kron(Ix, kron(L3, Iz))
        + kron(Ix, kron(Iy, L1))
    ).tocsr()
    Lap_diag = kron(eye(2, dtype=DTYPE_C, format="csr"), Lap_scalar)

    # Spinor ABC coupling matrix C: copied from 750.Ref.py.
    rows_list, cols_list, data_list = [], [], []
    coef = 0.5 / hz
    d_coef_x = 1.0 / (2.0 * hx)
    d_coef_y = 1.0 / (2.0 * hy)
    Ngrid = Nx * Ny * Nz

    for ix in range(1, Nx - 1):
        for iy in range(1, Ny - 1):
            z_top = Nz - 1
            base = ix * Ny * Nz + iy * Nz + z_top

            # UP row
            row_up = base
            if ix > 1:
                col = Ngrid + (ix - 1) * Ny * Nz + iy * Nz + z_top
                rows_list.append(row_up)
                cols_list.append(col)
                data_list.append(coef * (-d_coef_x))
            if ix < Nx - 2:
                col = Ngrid + (ix + 1) * Ny * Nz + iy * Nz + z_top
                rows_list.append(row_up)
                cols_list.append(col)
                data_list.append(coef * (+d_coef_x))
            if iy > 1:
                col = Ngrid + ix * Ny * Nz + (iy - 1) * Nz + z_top
                rows_list.append(row_up)
                cols_list.append(col)
                data_list.append(coef * (+1j) * d_coef_y)
            if iy < Ny - 2:
                col = Ngrid + ix * Ny * Nz + (iy + 1) * Nz + z_top
                rows_list.append(row_up)
                cols_list.append(col)
                data_list.append(coef * (-1j) * d_coef_y)

            # DOWN row
            row_down = Ngrid + base
            if ix > 1:
                col = (ix - 1) * Ny * Nz + iy * Nz + z_top
                rows_list.append(row_down)
                cols_list.append(col)
                data_list.append(coef * (+d_coef_x))
            if ix < Nx - 2:
                col = (ix + 1) * Ny * Nz + iy * Nz + z_top
                rows_list.append(row_down)
                cols_list.append(col)
                data_list.append(coef * (-d_coef_x))
            if iy > 1:
                col = ix * Ny * Nz + (iy - 1) * Nz + z_top
                rows_list.append(row_down)
                cols_list.append(col)
                data_list.append(coef * (+1j) * d_coef_y)
            if iy < Ny - 2:
                col = ix * Ny * Nz + (iy + 1) * Nz + z_top
                rows_list.append(row_down)
                cols_list.append(col)
                data_list.append(coef * (-1j) * d_coef_y)

    C = coo_matrix(
        (
            cp.array(data_list, dtype=DTYPE_C),
            (cp.array(rows_list), cp.array(cols_list)),
        ),
        shape=(2 * Ngrid, 2 * Ngrid),
        dtype=DTYPE_C,
    ).tocsr()

    Lap_spinor = (Lap_diag + C).tocsr()

    # Small-operator audit.  This avoids constructing a full 3-D adjoint.
    expected_g1_diag = cp.zeros(Nz, dtype=DTYPE_C)
    expected_g1_diag[-1] = k_bc / hz
    expected_g1 = diags(expected_g1_diag, 0, format="csr")
    g1_actual = (1j * (L1 - sparse_adjoint(L1))).tocsr()

    operator_audit = {
        "L_z_loss_structure_max_abs_residual": sparse_max_abs(
            (g1_actual - expected_g1).tocsr()
        ),
        "L_x_hermiticity_max_abs_residual": sparse_max_abs(
            (L2 - sparse_adjoint(L2)).tocsr()
        ),
        "L_y_hermiticity_max_abs_residual": sparse_max_abs(
            (L3 - sparse_adjoint(L3)).tocsr()
        ),
        "C_hermiticity_max_abs_residual": sparse_max_abs(
            (C - sparse_adjoint(C)).tocsr()
        ),
        "C_nnz": int(C.nnz),
    }
    atomic_write_json(out_dir / "operator_audit.json", operator_audit)
    print("[operator audit]")
    for key, value in operator_audit.items():
        print(f"  {key}: {value}")

    # CN matrices.  The spinor branch below is literally the 750.Ref.py
    # construction.  The scalar control changes only Lap_spinor -> Lap_diag,
    # i.e. it omits the reactive spin-coupling matrix C while retaining the
    # same scalar ABC, potential, time step, and solver.
    Ntot = 2 * Nx * Ny * Nz
    Id = eye(Ntot, dtype=DTYPE_C, format="csr")
    Potential = diags(V_full, 0, format="csr")

    if args.detector == "spinor":
        A = Id + 1j * dt / 2 * (Lap_spinor + Potential).tocsr()
        B = Id - 1j * dt / 2 * (Lap_spinor + Potential).tocsr()
    else:
        A = Id + 1j * dt / 2 * (Lap_diag + Potential).tocsr()
        B = Id - 1j * dt / 2 * (Lap_diag + Potential).tocsr()

    # GMRES preconditioner and precision: unchanged.
    A64 = A.astype(cp.complex128)
    B64 = B.astype(cp.complex128)
    inv_diag64 = 1.0 / A64.diagonal()
    M64 = LinearOperator(shape=A64.shape, matvec=lambda vector: inv_diag64 * vector)

    num_steps = int(round(T_final / dt))
    times = np.arange(num_steps + 1, dtype=np.float64) * dt

    # Exact sparse probability-output cadence of 750.Ref.py: the union of
    # every 100th step and 1000 integer points generated by CuPy linspace.
    reference_prob_steps = set(
        to_cpu(cp.linspace(1, num_steps, 1000, dtype=int)).tolist()
    )
    reference_prob_steps.update(range(100, num_steps + 1, 100))
    reference_prob_indices = np.asarray(
        sorted(reference_prob_steps), dtype=np.int64
    )
    survival = np.full(num_steps + 1, np.nan, dtype=np.float64)
    step_loss_roof = np.full(num_steps, np.nan, dtype=np.float64)
    step_loss_preclamp = np.full(num_steps, np.nan, dtype=np.float64)
    step_loss_clamp = np.full(num_steps, np.nan, dtype=np.float64)
    step_loss_total = np.full(num_steps, np.nan, dtype=np.float64)
    step_loss_flux_residual = np.full(num_steps, np.nan, dtype=np.float64)
    boundary_max_preclamp = np.full(num_steps, np.nan, dtype=np.float64)
    gmres_info = np.full(num_steps, -999, dtype=np.int32)

    audit_steps: list[int] = []
    audit_true_residual: list[float] = []
    audit_solve_norm: list[float] = []
    audit_solver_flux_residual: list[float] = []
    audit_cast_loss: list[float] = []

    S_current = norm2_uniform(psi_flat, dvol)
    survival[0] = S_current

    physical_config: Dict[str, Any] = {
        "script_version": SCRIPT_VERSION,
        "detector": args.detector,
        "zero_ambient_bath": True,
        "Nx": Nx,
        "Ny": Ny,
        "Nz": Nz,
        "ell": ell,
        "Lx": float(Lx),
        "Ly": float(Ly),
        "Lz": Lz,
        "z_roof_grid": z_roof_grid,
        "hx": hx,
        "hy": hy,
        "hz": hz,
        "dt": dt,
        "T_final": T_final,
        "num_steps": num_steps,
        "omega": omega,
        "Vxy0": Vxy0,
        "V0z": V0z,
        "alpha": alpha,
        "k_bc": k_bc,
        "z0": z0,
        "sigma_z_amplitude": sigma_z,
        "sigma_parallel_probability": sigma_z / np.sqrt(2.0),
        "k0": k0,
        "theta": theta,
        "phi": float(phi),
        "DTYPE_R": "float32",
        "DTYPE_C": "complex64",
        "GMRES_internal_dtype": "complex128",
        "gmres_rtol": gmres_rtol,
        "gmres_atol": gmres_atol,
        "gmres_maxiter": gmres_maxiter,
        "gmres_restart": gmres_restart,
        "progress_every": args.progress_every,
        "residual_every": args.residual_every,
        "checkpoint_every": args.checkpoint_every,
        "reference_sha256": reference_sha256,
        "script_sha256": script_sha256,
        "initial_survival": S_current,
        "initial_boundary_report": initial_boundary_report,
        "operator_audit": operator_audit,
        "gpu_and_software": gpu_metadata(),
    }
    # A machine-independent hash of only the frozen physical and solver
    # configuration.  Runtime/GPU metadata is retained separately in the full
    # configuration record and does not alter this comparison hash.
    physics_solver_hash_payload = {
        key: physical_config[key]
        for key in (
            "script_version",
            "detector",
            "zero_ambient_bath",
            "Nx",
            "Ny",
            "Nz",
            "ell",
            "Lx",
            "Ly",
            "Lz",
            "z_roof_grid",
            "hx",
            "hy",
            "hz",
            "dt",
            "T_final",
            "num_steps",
            "omega",
            "Vxy0",
            "V0z",
            "alpha",
            "k_bc",
            "z0",
            "sigma_z_amplitude",
            "sigma_parallel_probability",
            "k0",
            "theta",
            "phi",
            "DTYPE_R",
            "DTYPE_C",
            "GMRES_internal_dtype",
            "gmres_rtol",
            "gmres_atol",
            "gmres_maxiter",
            "gmres_restart",
            "reference_sha256",
            "script_sha256",
        )
    }
    physical_config["physics_solver_configuration_sha256"] = sha256_json(
        physics_solver_hash_payload
    )
    physical_config["configuration_sha256"] = sha256_json(physical_config)
    atomic_write_json(out_dir / "configuration.json", physical_config)

    # Compatibility with the reference output convention.
    np.savez(
        out_dir / "constants.npz",
        Nx=Nx,
        Ny=Ny,
        Nz=Nz,
        Lx=float(Lx),
        Ly=float(Ly),
        Lz=Lz,
        z_roof_grid=z_roof_grid,
        hx=hx,
        hy=hy,
        hz=hz,
        dt=dt,
        T_final=T_final,
        omega=omega,
        Vxy0=Vxy0,
        V0z=V0z,
        alpha=alpha,
        k_bc=k_bc,
        theta=theta,
        phi=float(phi),
        DTYPE_R="float32",
        DTYPE_C="complex64",
        z0=z0,
        sigma_z=sigma_z,
        k0=k0,
        detector=args.detector,
        reference_sha256=reference_sha256,
        script_sha256=script_sha256,
        physics_solver_configuration_sha256=physical_config[
            "physics_solver_configuration_sha256"
        ],
        configuration_sha256=physical_config["configuration_sha256"],
    )

    print("Simulation Parameters:")
    for key in (
        "detector",
        "Nx",
        "Ny",
        "Nz",
        "theta",
        "Lx",
        "Ly",
        "Lz",
        "z_roof_grid",
        "k_bc",
        "dt",
        "T_final",
        "V0z",
        "alpha",
        "omega",
        "hx",
        "hy",
        "hz",
        "k0",
        "z0",
        "sigma_z_amplitude",
        "sigma_parallel_probability",
    ):
        print(f"{key}: {physical_config[key]}")
    print(f"out_dir: {out_dir}")
    print("-------------------------------------------")

    status.update({"status": "running", "num_steps": num_steps})
    atomic_write_json(out_dir / "run_status.json", status)

    print(f"[info] Starting time loop - {num_steps} steps")
    start_time = time.time()
    completed_steps = 0

    try:
        for n in range(1, num_steps + 1):
            if n % args.progress_every == 0 or n == 1:
                elapsed = time.time() - start_time
                eta_min = (num_steps - n) * (elapsed / max(n, 1)) / 60.0
                print(
                    f"[progress] Step {n}/{num_steps} "
                    f"(t={n * dt:.5f}) | ETA: {eta_min:.2f} min",
                    flush=True,
                )

            # ----------------------------------------------------------
            # Crank--Nicolson + GMRES advance.  Formula, precision,
            # preconditioner, tolerances, restart, and maxiter are those
            # of 750.Ref.py.
            # ----------------------------------------------------------
            psi_before = psi_flat
            rhs64 = B64 @ psi_flat.astype(cp.complex128)
            psi64, info = gmres(
                A64,
                rhs64,
                x0=psi_flat.astype(cp.complex128),
                rtol=1e-8,
                atol=0.0,
                maxiter=1000,
                M=M64,
                restart=30,
            )
            info_int = int(info)
            gmres_info[n - 1] = info_int

            do_residual_audit = (
                n == 1
                or n == num_steps
                or n % args.residual_every == 0
                or info_int != 0
            )
            if do_residual_audit:
                rel_residual = true_relative_residual(A64, psi64, rhs64)
                solve_norm = norm2_uniform(psi64, dvol)
            else:
                rel_residual = float("nan")
                solve_norm = float("nan")

            p_roof = roof_midpoint_loss(
                psi_before,
                psi64,
                nx=Nx,
                ny=Ny,
                nz=Nz,
                dt=dt,
                k_bc=k_bc,
                hx=hx,
                hy=hy,
            )
            del psi_before, rhs64

            # Reference storage precision and reference post-solve clamp.
            psi_flat = psi64.astype(cp.complex64)
            psi_3d = psi_flat.reshape(2, Nx, Ny, Nz)

            p_clamp, boundary_max = dirichlet_boundary_audit(psi_3d, dvol)
            enforce_dirichlet_reference(psi_3d)

            # One full norm reduction of the actual state carried forward.
            S_next = norm2_uniform(psi_flat, dvol)
            S_preclamp = S_next + p_clamp

            p_preclamp = S_current - S_preclamp
            p_total = S_current - S_next
            p_flux_residual = p_preclamp - p_roof

            finite_step_values = np.asarray(
                [S_next, p_roof, p_clamp, p_preclamp, p_total, p_flux_residual],
                dtype=np.float64,
            )
            if not np.all(np.isfinite(finite_step_values)):
                raise FloatingPointError(
                    f"Non-finite diagnostic at step {n}, t={n * dt:.8f}: "
                    f"{finite_step_values!r}"
                )

            survival[n] = S_next
            step_loss_roof[n - 1] = p_roof
            step_loss_preclamp[n - 1] = p_preclamp
            step_loss_clamp[n - 1] = p_clamp
            step_loss_total[n - 1] = p_total
            step_loss_flux_residual[n - 1] = p_flux_residual
            boundary_max_preclamp[n - 1] = boundary_max

            if do_residual_audit:
                solver_flux_residual = S_current - solve_norm - p_roof
                cast_loss = solve_norm - S_preclamp
                audit_steps.append(n)
                audit_true_residual.append(rel_residual)
                audit_solve_norm.append(solve_norm)
                audit_solver_flux_residual.append(solver_flux_residual)
                audit_cast_loss.append(cast_loss)

                logging.info(
                    "[audit] n=%d t=%.6f S=%.12e p_roof=%.12e "
                    "p_total=%.12e p_clamp=%.12e flux_res=%.12e "
                    "true_rel_res=%.3e info=%d",
                    n,
                    n * dt,
                    S_next,
                    p_roof,
                    p_total,
                    p_clamp,
                    p_flux_residual,
                    rel_residual,
                    info_int,
                )

            completed_steps = n
            S_current = S_next

            if info_int != 0:
                save_checkpoint(
                    out_dir,
                    completed_steps,
                    times=times,
                    survival=survival,
                    step_loss_roof=step_loss_roof,
                    step_loss_preclamp=step_loss_preclamp,
                    step_loss_clamp=step_loss_clamp,
                    step_loss_total=step_loss_total,
                    step_loss_flux_residual=step_loss_flux_residual,
                    boundary_max_preclamp=boundary_max_preclamp,
                    gmres_info=gmres_info,
                    audit_steps=audit_steps,
                    audit_true_residual=audit_true_residual,
                    audit_solve_norm=audit_solve_norm,
                    audit_solver_flux_residual=audit_solver_flux_residual,
                    audit_cast_loss=audit_cast_loss,
                )
                raise RuntimeError(
                    f"GMRES failed at step {n}, t={n * dt:.8f}, info={info_int}, "
                    f"true relative residual={rel_residual:.6e}"
                )

            if n % args.checkpoint_every == 0 or n == num_steps:
                save_checkpoint(
                    out_dir,
                    completed_steps,
                    times=times,
                    survival=survival,
                    step_loss_roof=step_loss_roof,
                    step_loss_preclamp=step_loss_preclamp,
                    step_loss_clamp=step_loss_clamp,
                    step_loss_total=step_loss_total,
                    step_loss_flux_residual=step_loss_flux_residual,
                    boundary_max_preclamp=boundary_max_preclamp,
                    gmres_info=gmres_info,
                    audit_steps=audit_steps,
                    audit_true_residual=audit_true_residual,
                    audit_solve_norm=audit_solve_norm,
                    audit_solver_flux_residual=audit_solver_flux_residual,
                    audit_cast_loss=audit_cast_loss,
                )

        elapsed_seconds = time.time() - start_time

        # ------------------------------------------------------------------
        # Final raw arrays. Scientific reductions are performed by the loader.
        # ------------------------------------------------------------------
        np.save(out_dir / "times.npy", times)
        np.save(out_dir / "survival.npy", survival)
        np.save(
            out_dir / "prob_times.npy",
            times[reference_prob_indices],
        )
        np.save(
            out_dir / "total_probs.npy",
            survival[reference_prob_indices],
        )
        np.save(
            out_dir / "reference_probability_step_indices.npy",
            reference_prob_indices,
        )
        np.save(out_dir / "step_loss_roof_midpoint.npy", step_loss_roof)
        np.save(out_dir / "step_loss_preclamp.npy", step_loss_preclamp)
        np.save(out_dir / "step_loss_clamp.npy", step_loss_clamp)
        np.save(out_dir / "step_loss_total.npy", step_loss_total)
        np.save(out_dir / "step_loss_flux_residual.npy", step_loss_flux_residual)
        np.save(out_dir / "boundary_max_preclamp.npy", boundary_max_preclamp)
        np.save(out_dir / "gmres_info.npy", gmres_info)
        np.save(out_dir / "audit_steps.npy", np.asarray(audit_steps, dtype=np.int64))
        np.save(
            out_dir / "audit_true_relative_residual.npy",
            np.asarray(audit_true_residual, dtype=np.float64),
        )
        np.save(
            out_dir / "audit_solve_norm.npy",
            np.asarray(audit_solve_norm, dtype=np.float64),
        )
        np.save(
            out_dir / "audit_solver_flux_residual.npy",
            np.asarray(audit_solver_flux_residual, dtype=np.float64),
        )
        np.save(
            out_dir / "audit_cast_loss.npy",
            np.asarray(audit_cast_loss, dtype=np.float64),
        )
        midpoint_times = (np.arange(num_steps, dtype=np.float64) + 0.5) * dt
        np.save(out_dir / "click_midpoint_times.npy", midpoint_times)

        # Solver-integrity audit only. No scientific curve reduction is done here.
        D_initial_minus_final = float(survival[0] - survival[-1])
        D_roof = float(np.sum(step_loss_roof, dtype=np.float64))
        D_preclamp = float(np.sum(step_loss_preclamp, dtype=np.float64))
        D_clamp = float(np.sum(step_loss_clamp, dtype=np.float64))
        D_total_steps = float(np.sum(step_loss_total, dtype=np.float64))
        D_flux_residual = float(np.sum(step_loss_flux_residual, dtype=np.float64))
        monotonic_tolerance = 1e-12
        negative_total_mask = step_loss_total < -monotonic_tolerance
        negative_roof_mask = step_loss_roof < -monotonic_tolerance
        gmres_failure_count = int(np.count_nonzero(gmres_info != 0))
        true_residual_array = np.asarray(audit_true_residual, dtype=np.float64)
        solver_flux_array = np.asarray(audit_solver_flux_residual, dtype=np.float64)
        cast_loss_array = np.asarray(audit_cast_loss, dtype=np.float64)

        solver_audit: Dict[str, Any] = {
            "status": "completed",
            "completed_utc": utc_now_iso(),
            "elapsed_seconds": elapsed_seconds,
            "detector": args.detector,
            "omega": omega,
            "dt": dt,
            "T_final": T_final,
            "num_steps": num_steps,
            "initial_survival": float(survival[0]),
            "final_survival": float(survival[-1]),
            "initial_minus_final_survival": D_initial_minus_final,
            "cumulative_roof_midpoint_loss": D_roof,
            "cumulative_preclamp_norm_loss": D_preclamp,
            "cumulative_clamp_loss": D_clamp,
            "cumulative_total_step_loss": D_total_steps,
            "cumulative_preclamp_minus_roof_residual": D_flux_residual,
            "telescoping_probability_closure": float(
                survival[-1] + D_total_steps - survival[0]
            ),
            "roof_probability_closure_residual": float(
                survival[-1] + D_roof - survival[0]
            ),
            "decomposed_probability_closure": float(
                survival[-1] + D_roof + D_flux_residual + D_clamp - survival[0]
            ),
            "number_of_reference_probability_samples": int(
                reference_prob_indices.size
            ),
            "minimum_total_step_loss": float(np.min(step_loss_total)),
            "minimum_roof_midpoint_step_loss": float(np.min(step_loss_roof)),
            "number_of_negative_total_steps_below_tolerance": int(
                np.count_nonzero(negative_total_mask)
            ),
            "number_of_negative_roof_steps_below_tolerance": int(
                np.count_nonzero(negative_roof_mask)
            ),
            "monotonicity_tolerance": monotonic_tolerance,
            "maximum_abs_preclamp_minus_roof_step_residual": float(
                np.max(np.abs(step_loss_flux_residual))
            ),
            "maximum_single_step_clamp_loss": float(np.max(step_loss_clamp)),
            "maximum_boundary_amplitude_before_clamp": float(
                np.max(boundary_max_preclamp)
            ),
            "gmres_failure_count": gmres_failure_count,
            "maximum_true_relative_residual_at_audit_steps": float(
                np.max(true_residual_array)
            ),
            "maximum_abs_solver_flux_residual_at_audit_steps": float(
                np.max(np.abs(solver_flux_array))
            ),
            "maximum_abs_cast_loss_at_audit_steps": float(
                np.max(np.abs(cast_loss_array))
            ),
            "number_of_residual_audit_steps": len(audit_steps),
            "physics_solver_configuration_sha256": physical_config[
                "physics_solver_configuration_sha256"
            ],
            "configuration_sha256": physical_config["configuration_sha256"],
            "reference_sha256": reference_sha256,
            "script_sha256": script_sha256,
        }
        atomic_write_json(out_dir / "solver_audit.json", solver_audit)

        # Hash all stable solver outputs except the manifest and transient files.
        hash_exclusions = {
            "output_hashes.json",
            "checkpoint.npz",
            "run_status.json",
            "stdout.txt",
            "simulation_log.txt",
        }
        output_hashes: Dict[str, str] = {}
        for path in sorted(out_dir.iterdir()):
            if path.is_file() and path.name not in hash_exclusions:
                output_hashes[path.name] = sha256_file(path)
        atomic_write_json(
            out_dir / "output_hashes.json",
            {
                "generated_utc": utc_now_iso(),
                "hash_algorithm": "SHA-256",
                "files": output_hashes,
            },
        )

        status.update(
            {
                "status": "completed",
                "completed_utc": utc_now_iso(),
                "completed_steps": completed_steps,
                "elapsed_seconds": elapsed_seconds,
                "solver_audit_file": "solver_audit.json",
                "output_hash_manifest": "output_hashes.json",
            }
        )
        atomic_write_json(out_dir / "run_status.json", status)

        print("\n[solver audit]")
        print(f"  final survival:                {survival[-1]:.12e}")
        print(f"  initial - final survival:      {D_initial_minus_final:.12e}")
        print(f"  cumulative roof midpoint loss: {D_roof:.12e}")
        print(f"  cumulative clamp loss:         {D_clamp:.12e}")
        print(
            "  roof closure residual:         "
            f"{solver_audit['roof_probability_closure_residual']:.12e}"
        )
        print(
            "  exact telescoping closure:     "
            f"{solver_audit['telescoping_probability_closure']:.12e}"
        )
        print(f"  GMRES failures:                {gmres_failure_count}")
        print(
            "  max audited true residual:     "
            f"{solver_audit['maximum_true_relative_residual_at_audit_steps']:.3e}"
        )
        print(f"  total execution time:          {elapsed_seconds:.2f} s")
        print(f"[info] All raw solver outputs are in: {out_dir}")
        return 0

    except Exception as exc:
        elapsed_seconds = time.time() - start_time
        try:
            save_checkpoint(
                out_dir,
                completed_steps,
                times=times,
                survival=survival,
                step_loss_roof=step_loss_roof,
                step_loss_preclamp=step_loss_preclamp,
                step_loss_clamp=step_loss_clamp,
                step_loss_total=step_loss_total,
                step_loss_flux_residual=step_loss_flux_residual,
                boundary_max_preclamp=boundary_max_preclamp,
                gmres_info=gmres_info,
                audit_steps=audit_steps,
                audit_true_residual=audit_true_residual,
                audit_solve_norm=audit_solve_norm,
                audit_solver_flux_residual=audit_solver_flux_residual,
                audit_cast_loss=audit_cast_loss,
            )
        except Exception:
            pass

        failure = {
            "status": "failed",
            "failed_utc": utc_now_iso(),
            "completed_steps": completed_steps,
            "elapsed_seconds": elapsed_seconds,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc(),
        }
        atomic_write_json(out_dir / "failure.json", failure)
        status.update(failure)
        atomic_write_json(out_dir / "run_status.json", status)
        logging.exception("Simulation failed after %d completed steps", completed_steps)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
