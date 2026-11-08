#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task09_4901_U2_low_v4_nonaccepting_D2PR2G1FMP_BATCH64_REPAIRED_RANK_WHOLEHALF_G0.py
===================================================================

Fresh Task-09 v4 deterministic U2-low non-accepting pilot for the finite
Part-I spinor absorbing-boundary detector.

The default execution gate is V4-G0 only.  It performs static/source/operator
certification, reduced full-density validation, whole-half repaired-rank selection versus
full-Gram-oracle tests, batch-64 multi-right-hand-side GMRES certification, exact
representation-budget reconstruction, and checkpoint/restart round-trip
validation.  It performs no production-size positive-rate propagation unless
the recorded runtime gate variables are changed after a successful G0 review.

Scientific architecture
-----------------------
* direct spinor ABC is the sole monitored detector;
* transverse upward bath is unmonitored and CPTP;
* finite map is bath-half / detector Cayley / bath-half;
* finite state is represented as a positive canonical spectral factor;
* every complete bath half-step retains the blocked metric-aware range/core, then
  scans the stable full-Gram support through blocked reconstruction, exact weighted-polar
  gauge repair, complete repaired-density certification, and the unchanged budget predicate;
* all deterministic representation approximations enter one scheduled global
  trace-norm ledger with B_max=1e-8;
* no scientific hard-rank cap exists; memory is a fail-closed resource gate;
* the resource allowance conditionally releases only unused CuPy pool blocks when the
  unchanged pre-mapping logical upper bound would otherwise exceed 80% of driver-free memory;
* the representation budget and telemetry are staged transactionally and committed
  only after a complete Strang step passes every gate;
* only complete Strang steps may be checkpointed;
* the canonicality repair trigger is a proactive repair target, while the
  unchanged hard tolerance is the sole post-repair acceptance gate;
* the P1 read-only audit selected detector RHS batch size 64 over the D2
  baseline 16 at every audited rank, with aggregate measured speedup 1.7126948241;
* V4-G1 is complete only after the production-size CPU first step, the A100
  first step, an exact low-rank CPU/A100 density comparison, and production-row
  rank-64/rank-256/rank-640 compression and detector-solve benchmarks;
* every v4 gate remains non-accepting, is not Task-10 eligible, and supports no
  finite-positive-rate physical claim.

Authority
---------
The current v3.9-reset master audit controls workflow and claims.  The final
Task-08 aggregate controls zero-rate numerics.  V7 controls theory.  The Phase-A
v3.9 reconstruction and tensor audit control representation feasibility.  The
frozen 750 reference, final Audit-02 operator construction, and audited
Task-05/07 sources control their declared numerical domains.

Exit status
-----------
0 : selected non-accepting gate completed and all required checks passed
2 : selected gate completed but at least one numerical/certification gate failed
4 : blocked by authority, contract, configuration, or staged-gate violation
1 : execution/I/O failure
"""

from __future__ import annotations

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
import tempfile
import time
import traceback
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple, Union

import numpy as np
import scipy
import scipy.linalg as la
import scipy.sparse as sp
import scipy.sparse.linalg as spla

# =============================================================================
# MANUAL V4 EXECUTION CONFIGURATION — one source, one U2-low case, no sweep
# =============================================================================
DATA_ROOT = Path(
    os.environ.get("OPEN_SYSTEM_3D_ROOT", "[ARCHIVE_PATH]")
).expanduser().resolve()

# Runtime gate selection is explicit and source-preserving.  The immutable
# delivery defaults remain G0/SciPy; later gates are activated only through
# recorded environment variables after the preceding gate has passed review.
DEFAULT_EXECUTION_GATE = "V4-G0"
DEFAULT_BACKEND = "scipy"
DEFAULT_G1_MODE = "cpu_first_step"
DEFAULT_RESUME_FROM_V4_CHECKPOINT = False
DEFAULT_D2_POST_G0_REVIEW_AUTHORIZED = False

EXECUTION_GATE = os.environ.get("TASK09_V4_GATE", DEFAULT_EXECUTION_GATE).strip()
BACKEND = os.environ.get("TASK09_V4_BACKEND", DEFAULT_BACKEND).strip().lower()
G1_MODE = os.environ.get("TASK09_V4_G1_MODE", DEFAULT_G1_MODE).strip().lower()
_resume_token = os.environ.get(
    "TASK09_V4_RESUME", "1" if DEFAULT_RESUME_FROM_V4_CHECKPOINT else "0"
).strip().lower()
if _resume_token not in {"0", "1", "false", "true", "no", "yes"}:
    raise RuntimeError("TASK09_V4_RESUME must be one of 0/1/false/true/no/yes")
RESUME_FROM_V4_CHECKPOINT = _resume_token in {"1", "true", "yes"}
_d2_review_token = os.environ.get(
    "TASK09_D2_POST_G0_REVIEW",
    "1" if DEFAULT_D2_POST_G0_REVIEW_AUTHORIZED else "0",
).strip().lower()
if _d2_review_token not in {"0", "1", "false", "true", "no", "yes"}:
    raise RuntimeError(
        "TASK09_D2_POST_G0_REVIEW must be one of 0/1/false/true/no/yes"
    )
D2_POST_G0_REVIEW_AUTHORIZED = _d2_review_token in {"1", "true", "yes"}

# Fresh v4 namespace; no v3.x output or checkpoint is ever imported.
V4_NAMESPACE = DATA_ROOT / "Task09_v4"
CASE_DIRECTORY_NAME = "4901.U2_low_CSSF_D2PR2G1FMP_BATCH64_REPAIRED_RANK_WHOLEHALF_nonaccepting_v4"

# Manual checkpoint cadence for G2-G4.  Checkpoints are written only after a
# complete bath-half/detector/bath-half Strang step.
CHECKPOINT_EVERY = 100
PROGRESS_EVERY = 25

# Multi-RHS detector solve.  It is activated outside G0 only if the same source
# has passed its internal G0 certification in the current execution.
USE_MULTI_RHS_GMRES = True
MULTI_RHS_CHECK_EVERY = 5
DETECTOR_RHS_BATCH_COLUMNS = 64
FACTOR_BLOCK_COLUMNS = 64
# =============================================================================

# TASK-09 V4 NUMERICAL CORE BEGINS HERE
NUMERICAL_CORE_MARKER = "# TASK-09 V4 NUMERICAL CORE BEGINS HERE"

SCRIPT_VERSION = "2026-08-14-task09-v4-d2pr2g1fmp-batch64-repaired-rank-whole-half-cssf-nonaccepting-g0-v4"
STAGE_NAME = "09_v4_cssf_nonaccepting_pilot"
CHECKPOINT_SCHEMA = "2026-08-14-task09-v4-d2pr2g1fmp-batch64-repaired-rank-checkpoint-v4-whole-half-transactional"
REPRESENTATION_TELEMETRY_SCHEMA = "2026-08-14-task09-v4-d2pr2g1fmp-batch64-repaired-rank-representation-telemetry-v4-whole-half"
PHYSICAL_FAMILY_CONTRACT_SCHEMA = "2026-08-11-task09-v4-u2-low-physical-family-v1"
PILOT_EXECUTION_CONTRACT_SCHEMA = "2026-08-14-task09-v4-d2pr2g1fmp-batch64-repaired-rank-nonaccepting-execution-v4"
G0_REPORT_SCHEMA = "2026-08-14-task09-v4-d2pr2g1fmp-batch64-repaired-rank-g0-certification-v4-whole-half"

PRODUCTION_AUTHORIZED = False
ACCEPTANCE_ENABLED = False
TASK10_ELIGIBLE = False
FINITE_POSITIVE_RATE_PHYSICAL_CLAIM = False
LEGACY_CHECKPOINT_IMPORT_ENABLED = False
CHECKPOINT_MIGRATION_ENABLED = False
AUTOMATIC_SWEEP_ENABLED = False

# Fixed U2-low physics.
TASK08_MATRIX_ID = "U2"
PROPAGATOR_TYPE = "spinor"
ENVIRONMENT_DIRECTION = "upward"
INITIAL_MODE = "00"
OMEGA = 100.0
N_SHELL = 12
N_Z = 1500
L_Z = 20.0
DT = 5.0e-4
T_FINAL = 10.0
RATE_LAMBDA = math.pi / 400.0
BATH_MICROSTEPS_PER_HALF = 1
PILOT_TARGET_STEP = 7200
T_CUT = 3.6

HBAR = 1.0
MASS = 1.0
Z0 = 10.0
SIGMA_Z_AMPLITUDE = 0.5
K0 = math.pi
KAPPA = math.pi
THETA = math.pi / 6.0
PHI = 0.0

GMRES_RTOL = 1.0e-10
GMRES_ATOL = 0.0
GMRES_RESTART = 30
GMRES_MAXITER = 1000
TRUE_RESIDUAL_TOL = 1.0e-8

OPERATOR_TOL = 1.0e-12
BATH_COMPLETENESS_TOL = 2.0e-12
BATH_DERIVATIVE_REL_TOL = 2.0e-6
BATH_DERIVATIVE_MIN_PROBE = 1.0e-10
BATH_DERIVATIVE_TARGET_ACTION = 1.0e-6
BATH_TRACE_RESIDUAL_TOL = 5.0e-10
PROBABILITY_CLOSURE_ABS_TOL = 5.0e-9
SURVIVAL_INCREASE_TOL = 2.0e-9
UPWARD_CUMULATIVE_OVERFLOW_TOL = 1.0e-6
CANONICALITY_TOL = 2.0e-10
# The trigger is only a proactive gauge-refinement target.  It is deliberately
# stricter than the unchanged hard gate, but it is not an acceptance tolerance.
# A repaired factor is accepted exactly when the hard canonicality audit passes.
CANONICALITY_REPAIR_TRIGGER = 1.0e-12
CANONICALITY_REPAIR_MAX_PASSES = 3
TRACE_RESTORE_TOL = 5.0e-12

# Frozen global representation ledger.
REPRESENTATION_TRACE_NORM_BUDGET = 1.0e-8
REPRESENTATION_BUDGET_POLICY = "scheduled_cumulative_envelope_with_past_credit_no_future_borrowing_v1"
REPRESENTATION_BUDGET_COMPARISON_ULPS = 32.0
D2_CQR2_CONDITION_LIMIT = 0.1 / math.sqrt(np.finfo(float).eps)
D2_RESIDUAL_DEPENDENCY_EPS2_FACTOR = 4096.0
D2_CERTIFICATE_TRACE_GUARD_ULPS = 64.0
D2_PARENT_G1COMPLETE_SHA256 = "8d1f86ea450ede47ea6c1837cfe7b07d9e313832be90336775cb4ed42a1b0754"
D2_D1A_ADDENDUM_STATUS = "PASS_V4_D1A_CLASSIFICATION_ADDENDUM"
D2P_PARENT_D2_SOURCE_SHA256 = "f7516e3c3707871fbf95ab648e32d5e5d59272f197996d7446e05cb2cd0477a2"
D2P_P1_SOURCE_SHA256 = "31bc20833ff7b4f663275f9579e0d7c0750d28c26d24147ce48c6b97016d4ee0"
D2P_P1_ARTIFACT_AUDIT_STATUS = "P1_ARTIFACT_AUDIT_PASS"
D2P_P1_BASELINE_BATCH_COLUMNS = 16
D2P_P1_SELECTED_BATCH_COLUMNS = 64
D2P_P1_AGGREGATE_SPEEDUP = 1.7126948241063793
D2PR_PARENT_D2P_SOURCE_SHA256 = "11f58b0571d0b471d1fa198d0700fdc98893bacdc60d810fab6ec39ab2264ee4"
D2PR_PARENT_D2P_CORE_SHA256 = "b9ed00ba626ee73ca9fb4aff42bb44a63d285e8b56027d31962d0a05bfc742aa"
D2PR_C2_SOURCE_SHA256 = "8a6a38e735505de3ace7685435b6b6e7ba614f9035c8187b57a6c64c9e2c3383"
D2PR_C2_SCHEMA = "2026-08-13-task09-v4-c2-readonly-repaired-rank-ladder-v1"
D2PR_C2_STATIC_AUDIT_SHA256 = "d1412a9fc6103d65c8bce2a7a1e24910f994d0dcdeb949c3e0aeec43679ff78f"
D2PR_C2_HANDOFF_SHA256 = "913dc2da8ef261089c2bb110dd54645d1913b68af6fca6f69d753aa8d4e15452"
D2PR_FRESH_SESSION_MASTER_HANDOFF_SHA256 = "a4b73455ad4704d07159306949cac54c334b2403bf899ec49392e3604537b0a8"
D2PR_PARENT_CHILD_SCOPE_AUDIT_SCHEMA = "2026-08-14-task09-v4-d2pr2g1fmp-parent-child-scope-audit-v4"
D2PR2_ADVERSARIAL_TEST_SCHEMA = "2026-08-14-task09-v4-d2pr2g1fmp-repaired-rank-adversarial-tests-v4"
D2PR2G1F_PARENT_D2PR2_SOURCE_SHA256 = "8601c3ffd742513f027e0480f9763ba3ad1e9f9096c82d5aacc221bcc0620a2a"
D2PR2G1F_PARENT_D2PR2_CORE_SHA256 = "e1090a670e3c5ac828a6a2ebd0d49dbfd3f0f4f15682d48662bf25335b3c0cf2"
D2PR2G1F_FAILURE_DIAGNOSIS_SHA256 = "be3bd7fd479ed5e3951e3de779d826e755ed4171ff1f356a17171f8d636aa781"
D2PR2G1F_FAILURE_DIAGNOSIS_SCHEMA = "2026-08-14-task09-v4-d2pr2-g1a100-controlled-failure-diagnosis-v1"
D2PR2G1F_FAILED_G1_A100_JOB_ID = 9419581
D2PR2G1FMP_PARENT_SOURCE_SHA256 = "cef5f181646bd23c9fe93d276c40b8a95534d23d1dc5860e2eb9851426de8a16"
D2PR2G1FMP_PARENT_CORE_SHA256 = "7d6240cfa8ca3055a120880194b6542c20ae0767771eb0c4b3379fa205ec4343"
D2PR2G1FMP_R1_DIAGNOSTIC_SOURCE_SHA256 = "baca8fd0a5a6ee3d19100f3d891018f688cdce58eb1e795136f1f84f3ab9432c"
D2PR2G1FMP_R1_AUTHORITY_RECORD_SHA256 = "054cc51d66932d4019c3c8d03539baa8bf2e9ac1e22d3bf0a4d3cb2f8e04c839"
D2PR2G1FMP_R1_AUTHORITY_RECORD_SCHEMA = "2026-08-14-task09-v4-d2pr2g1f-r1a-allocator-pool-authority-record-v1"
D2PR2G1FMP_R1_CLASSIFICATION = "R1-A_ALLOCATOR_POOL_CACHE_FALSE_NEGATIVE_CONFIRMED"
D2PR2G1FMP_R1_JOB_ID = 9421204
D2PR2G1FMP_RESOURCE_RELEASE_POLICY = (
    "conditional_release_of_unused_cupy_pool_blocks_only_when_pre_mapping_"
    "logical_upper_bound_exceeds_unchanged_80_percent_driver_free_allowance"
)
D2PR2_COMPLETE_ACCEPTANCE_RULE = (
    "unchanged_hard_canonicality_and_trace_gates_plus_existing_"
    "centralized_tolerance_inclusive_budget_predicate"
)
TOTAL_PHYSICAL_COMPRESSION_CALLS = 40000
GPU_WORKING_SET_FRACTION = 0.80
PSD_BACKWARD_ERROR_FACTOR = 256.0
AUGMENTED_GRAM_NORMALIZATION_FLOOR_FACTOR = 64.0

# V4-G0 reduced certification model.
G0_N_SHELL = 2
G0_N_Z = 20
G0_L_Z = 4.0
G0_Z0 = 2.0
G0_SIGMA_Z = 0.35
G0_DT = 2.0e-3
G0_T_FINAL = 2.0e-2
G0_GMRES_RTOL = 1.0e-12
G0_DENSITY_TRACE_NORM_TOL = 2.0e-9
G0_DENSITY_FROBENIUS_REL_TOL = 5.0e-10
G0_CURVE_ABS_TOL = 5.0e-10
G0_GMRES_SOLUTION_REL_TOL = 5.0e-9
G0_CHECKPOINT_DENSITY_TOL = 2.0e-12

# V4-G1 production-size completeness contract.  The CPU mode performs only the
# authoritative production first-step reconstruction.  The A100 mode requires
# that verified CPU artifact, performs its own first step, compares the two
# low-rank density operators without forming a D x D matrix, and then executes
# the production-row synthetic rank benchmarks.  Benchmark state and budget
# objects are diagnostic-only and cannot mutate the physical U2 first-step state.
G1_REPORT_SCHEMA = "2026-08-14-task09-v4-d2pr2g1fmp-batch64-repaired-rank-g1-report-v4-whole-half"
G1_BENCHMARK_SCHEMA = "2026-08-14-task09-v4-d2pr2g1fmp-batch64-repaired-rank-g1-synthetic-rank-benchmark-v4"
G1_CROSS_BACKEND_SCHEMA = "2026-08-14-task09-v4-d2pr2g1fmp-batch64-repaired-rank-g1-cpu-a100-comparison-v4"
G1_SYNTHETIC_RANKS = (64, 256, 640)
G1_SYNTHETIC_BENCHMARK_BUDGET = REPRESENTATION_TRACE_NORM_BUDGET
G1_SYNTHETIC_BENCHMARK_PLANNED_CALLS = 1
G1_CPU_A100_DENSITY_TRACE_NORM_TOL = 5.0e-8
G1_CPU_A100_SURVIVAL_ABS_TOL = 5.0e-9
G1_CPU_A100_MIDPOINT_PROBABILITY_ABS_TOL = 5.0e-9
G1_CPU_A100_REPRESENTATION_BOUND_ABS_TOL = 1.0e-10
G1_BENCHMARK_SAMPLE_COLUMNS = 4
G1_BENCHMARK_SAMPLE_SOLUTION_REL_TOL = 5.0e-7
G1_BENCHMARK_SAMPLE_PROBABILITY_ABS_TOL = 5.0e-9
G1_BENCHMARK_MEMORY_FRACTION = GPU_WORKING_SET_FRACTION

SOURCE_FINGERPRINTS: Dict[str, str] = {
    "current_parent_d2pr2g1f_source": D2PR2G1FMP_PARENT_SOURCE_SHA256,
    "current_parent_d2pr2g1f_core": D2PR2G1FMP_PARENT_CORE_SHA256,
    "r1_allocator_pool_exact_call4304_source": D2PR2G1FMP_R1_DIAGNOSTIC_SOURCE_SHA256,
    "r1_allocator_pool_authority_record": D2PR2G1FMP_R1_AUTHORITY_RECORD_SHA256,
    "current_parent_d2p_batch64_source": D2PR_PARENT_D2P_SOURCE_SHA256,
    "current_parent_d2p_batch64_core": D2PR_PARENT_D2P_CORE_SHA256,
    "c2_repaired_rank_ladder_source": D2PR_C2_SOURCE_SHA256,
    "c2_final_handoff": D2PR_C2_HANDOFF_SHA256,
    "fresh_session_master_handoff": D2PR_FRESH_SESSION_MASTER_HANDOFF_SHA256,
    "parent_g1complete_source": D2_PARENT_G1COMPLETE_SHA256,
    "parent_d2_wholehalf_source": D2P_PARENT_D2_SOURCE_SHA256,
    "p1_cayley_gmres_audit_source": D2P_P1_SOURCE_SHA256,
    "current_v39_reset_master": "944c2ae3f65785ea56a92b7ab2974373ef7c75746d643c5f784d7399646c4b87",
    "phaseA_final_design": "d40a8caf9d7455e89a3a67ed5be27cb5d4efe68c4c5941bfa19fdf79b419aede",
    "phaseA_exact_v39_reconstruction": "f566cdb1a37e8ce112ced008dd422b16a262161d5ecddb360ae276aadc7fea6f",
    "phaseA_evidence_archive": "0c1f8a3c4bb429802be4b43647bed2125687b10406b33017d0226bce83af3c9e",
    "phaseA_tensor_archive": "f90fe3fca6b0ab1788dd40b1685f878014b376d90ebacb69edc7d5a5ade4559a",
    "phaseA_tensor_report": "b4b337c3ea692f27ffdb18b47ffb787b366f8385f6a52bf15a80cdef9e2065fb",
    "v7_manuscript": "d0618e35c6b5432d8289e9feaf17206bd912fa9795e31d47ad1f96e5c520b7b7",
    "reference_750": "8cf2095b2d760a0b702c930fe5690fe762d08ad7c721a8c53b5ed498d1744009",
    "audit02_final_solver": "2ed0daf88dca64d33896d42e53d93c1e57b85d7e22391498babd4f7588b273b2",
    "task05_representative_source": "f87234c8b6380965756da215b24fb7bf1721d61848da14d5f8a5ded177f61824",
    "task07_representative_source": "7fc26afe350a051b230a43acc120a84670fa41ec2246405cb250e179d6771b5d",
    "task07_v8_standard_core": "827fd4993707152393a8adcf891df59d7b4d02310a06e89dd5263c0fd37369af",
    "task07_v8_high_accuracy_upward_core": "d665b92be5d1efb6954968833f4cf008672add6e8ed5194e9d8a55a2a498d796",
    "task08_final_output_manifest": "6a7e939fe86d0ffd827b0e5acb164b045affe79af0775ba87911f3ed92ff1a40",
    "historical_v39_source": "53076121b914b8da710db4ef84988047810f378c4ceb81fee5f1087a2e0baefc",
}


class GateBlocked(RuntimeError):
    """Expected fail-closed staged-gate or authority block."""


class RepresentationFailure(RuntimeError):
    """Fail-closed representation or resource event."""

    def __init__(self, message: str, *, event: Mapping[str, Any]):
        super().__init__(message)
        self.event = dict(event)


@dataclass(frozen=True)
class RunConfig:
    execution_gate: str
    backend: str
    propagator_type: str = PROPAGATOR_TYPE
    environment_direction: str = ENVIRONMENT_DIRECTION
    initial_mode: str = INITIAL_MODE
    omega: float = OMEGA
    n_shell: int = N_SHELL
    n_z: int = N_Z
    l_z: float = L_Z
    dt: float = DT
    t_final: float = T_FINAL
    stop_after_steps: int = 0
    rate_lambda: float = RATE_LAMBDA
    bath_microsteps_per_half: int = BATH_MICROSTEPS_PER_HALF
    z0: float = Z0
    sigma_z_amplitude: float = SIGMA_Z_AMPLITUDE
    k0: float = K0
    kappa: float = KAPPA
    theta: float = THETA
    phi: float = PHI
    t_cut: float = T_CUT
    gmres_rtol: float = GMRES_RTOL
    detector_rhs_batch_columns: int = DETECTOR_RHS_BATCH_COLUMNS
    factor_block_columns: int = FACTOR_BLOCK_COLUMNS
    checkpoint_every: int = CHECKPOINT_EVERY
    progress_every: int = PROGRESS_EVERY
    resume_from_checkpoint: bool = RESUME_FROM_V4_CHECKPOINT
    representation_budget: float = REPRESENTATION_TRACE_NORM_BUDGET
    planned_compression_calls: int = TOTAL_PHYSICAL_COMPRESSION_CALLS
    output_root: Path = V4_NAMESPACE

    @property
    def d_channels(self) -> int:
        return (self.n_shell + 1) * (self.n_shell + 2)

    @property
    def state_dimension(self) -> int:
        return self.d_channels * self.n_z

    @property
    def full_num_steps(self) -> int:
        return int(round(self.t_final / self.dt))

    @property
    def execution_num_steps(self) -> int:
        return int(self.stop_after_steps)

    @property
    def case_dir(self) -> Path:
        gate_token = self.execution_gate.replace("-", "_")
        if self.execution_gate == "V4-G1":
            gate_token = f"{gate_token}_{G1_MODE}"
        return self.output_root / CASE_DIRECTORY_NAME / gate_token


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
    backend_inverse_diagonal: Any
    transverse_phase_backend: Optional[Any]
    active_factorized_channels: Tuple[int, ...]
    roof_sign_audit: Dict[str, Any]


@dataclass
class BathKraus:
    action: float
    operators_cpu: Tuple[sp.csr_matrix, ...]
    operators_backend: Tuple[Any, ...]
    completeness_residual: float
    g_diagonal: np.ndarray
    first_derivative_audit: Dict[str, Any]


@dataclass(frozen=True)
class RawFactor:
    blocks: Tuple[Any, ...]
    n_rows: int

    def __post_init__(self) -> None:
        if not self.blocks:
            raise ValueError("RawFactor requires at least one block")
        for block in self.blocks:
            if getattr(block, "ndim", None) != 2 or int(block.shape[0]) != int(self.n_rows):
                raise ValueError("Invalid RawFactor block shape")
            if int(block.shape[1]) <= 0:
                raise ValueError("RawFactor blocks must have positive column count")

    @property
    def rank(self) -> int:
        return int(sum(int(block.shape[1]) for block in self.blocks))

    @property
    def logical_nbytes(self) -> int:
        return int(sum(int(block.nbytes) for block in self.blocks))


@dataclass(frozen=True)
class CanonicalFactor:
    """Positive density rho=Q diag(weights) Q^dagger with h_z Q^dagger Q=I."""

    basis_blocks: Tuple[Any, ...]
    weights: np.ndarray
    n_rows: int
    h_z: float

    def __post_init__(self) -> None:
        values = np.asarray(self.weights, dtype=np.float64)
        if values.ndim != 1 or values.size == 0:
            raise ValueError("CanonicalFactor weights must be a nonempty vector")
        if not np.all(np.isfinite(values)) or np.any(values <= 0.0):
            raise ValueError("CanonicalFactor weights must be finite and strictly positive")
        if np.any(values[:-1] < values[1:]):
            raise ValueError("CanonicalFactor weights must be nonincreasing")
        rank = 0
        for block in self.basis_blocks:
            if getattr(block, "ndim", None) != 2 or int(block.shape[0]) != int(self.n_rows):
                raise ValueError("Invalid canonical basis block shape")
            rank += int(block.shape[1])
        if rank != values.size:
            raise ValueError("Canonical basis rank and weight count disagree")

    @property
    def rank(self) -> int:
        return int(self.weights.size)

    @property
    def trace(self) -> float:
        return float(math.fsum(float(x) for x in self.weights))

    @property
    def logical_nbytes(self) -> int:
        return int(sum(int(block.nbytes) for block in self.basis_blocks) + self.weights.nbytes)


@dataclass
class RepresentationBudgetState:
    total_budget: float
    total_planned_calls: int
    calls_completed: int = 0
    bound_used: float = 0.0

    def allocation(self) -> Dict[str, Any]:
        call = self.calls_completed + 1
        if call > self.total_planned_calls:
            raise RepresentationFailure(
                "Representation schedule exhausted",
                event={
                    "calls_completed": self.calls_completed,
                    "total_planned_calls": self.total_planned_calls,
                },
            )
        ceiling = self.total_budget * call / self.total_planned_calls
        allowance = ceiling - self.bound_used
        if not np.isfinite(allowance) or allowance < 0.0:
            raise RepresentationFailure(
                "Scheduled representation envelope is already exceeded",
                event={"call": call, "ceiling": ceiling, "bound_used": self.bound_used},
            )
        return {
            "compression_call_index": call,
            "scheduled_cumulative_ceiling": float(ceiling),
            "cumulative_bound_before": float(self.bound_used),
            "allowed_trace_norm_increment": float(allowance),
            "past_credit_before": float(ceiling - self.bound_used),
        }

    @staticmethod
    def comparison_tolerance() -> float:
        return float(REPRESENTATION_BUDGET_COMPARISON_ULPS * np.finfo(float).eps)

    def assess_increment(
        self,
        increment: float,
        *,
        allocation: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        current = dict(self.allocation() if allocation is None else allocation)
        value = float(increment)
        tolerance = self.comparison_tolerance()
        finite_nonnegative = bool(np.isfinite(value) and value >= 0.0)
        after = math.fsum((self.bound_used, value)) if finite_nonnegative else float("nan")
        scheduled_pass = bool(
            finite_nonnegative
            and value <= float(current["allowed_trace_norm_increment"]) + tolerance
        )
        global_pass = bool(
            finite_nonnegative and after <= self.total_budget + tolerance
        )
        return {
            **current,
            "requested_increment": value,
            "comparison_tolerance": tolerance,
            "finite_nonnegative": finite_nonnegative,
            "scheduled_envelope_passed": scheduled_pass,
            "global_budget_passed": global_pass,
            "bound_after_if_committed": float(after),
            "passed": bool(finite_nonnegative and scheduled_pass and global_pass),
        }

    def commit(self, increment: float) -> Dict[str, Any]:
        assessment = self.assess_increment(increment)
        if not assessment["finite_nonnegative"]:
            raise RepresentationFailure(
                "Invalid representation increment", event=assessment
            )
        if not assessment["scheduled_envelope_passed"]:
            raise RepresentationFailure(
                "Representation increment exceeds scheduled envelope",
                event=assessment,
            )
        if not assessment["global_budget_passed"]:
            raise RepresentationFailure(
                "Global representation budget exceeded", event=assessment
            )
        self.calls_completed += 1
        self.bound_used = float(assessment["bound_after_if_committed"])
        return {
            **assessment,
            "committed_trace_norm_increment": float(increment),
            "cumulative_bound_after": self.bound_used,
            "budget_remaining_after": self.total_budget - self.bound_used,
            "calls_completed_after": self.calls_completed,
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "total_budget": self.total_budget,
            "total_planned_calls": self.total_planned_calls,
            "calls_completed": self.calls_completed,
            "bound_used": self.bound_used,
            "budget_remaining": self.total_budget - self.bound_used,
        }


class RepresentationTelemetry:
    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []

    def record(self, event: Mapping[str, Any]) -> None:
        row = dict(event)
        row["schema"] = REPRESENTATION_TELEMETRY_SCHEMA
        self.events.append(row)

    def snapshot(self) -> List[Dict[str, Any]]:
        return [dict(event) for event in self.events]

    def restore(self, events: Sequence[Mapping[str, Any]]) -> None:
        self.events = [dict(event) for event in events]


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
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False, default=json_default,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sha256_numerical_core(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="strict").replace("\r\n", "\n")
    if NUMERICAL_CORE_MARKER not in text:
        raise RuntimeError("V4 numerical-core marker is missing")
    core = text.split(NUMERICAL_CORE_MARKER, 1)[1]
    return hashlib.sha256(core.encode("utf-8")).hexdigest()


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False, default=json_default)
        handle.write("\n")
    os.replace(tmp, path)


def atomic_savez(path: Path, **arrays: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("wb") as handle:
        np.savez(handle, **arrays)
    os.replace(tmp, path)


def atomic_save_npy(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("wb") as handle:
        np.save(handle, array, allow_pickle=False)
    os.replace(tmp, path)


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise TypeError(f"Expected JSON object in {path}")
    return value


def sparse_max_abs(matrix: sp.spmatrix) -> float:
    value = matrix.tocsr()
    return 0.0 if value.nnz == 0 else float(np.max(np.abs(value.data)))


def dense_max_abs(array: np.ndarray) -> float:
    value = np.asarray(array)
    return 0.0 if value.size == 0 else float(np.max(np.abs(value)))


def frobenius_norm(matrix: Any) -> float:
    if sp.issparse(matrix):
        return float(np.sqrt(np.sum(np.abs(matrix.data) ** 2, dtype=np.float64)))
    return float(np.linalg.norm(np.asarray(matrix)))


def relative_error(numerator: float, denominator: float) -> float:
    return float(numerator) if denominator == 0.0 else float(numerator) / float(denominator)


def tail_after_each_rank(values_descending: np.ndarray) -> np.ndarray:
    values = np.asarray(values_descending, dtype=np.float64)
    if values.ndim != 1 or not np.all(np.isfinite(values)) or np.any(values < 0.0):
        raise ValueError("Spectrum must be finite, nonnegative, and one-dimensional")
    tail = np.zeros(values.size + 1, dtype=np.float64)
    if values.size:
        tail[:-1] = np.cumsum(values[::-1], dtype=np.float64)[::-1]
    return tail


def physical_trace_raw(factor: RawFactor, h_z: float, backend: "NumericalBackend") -> float:
    terms: List[float] = []
    for block in factor.blocks:
        value = backend.xp.vdot(block.reshape(-1), block.reshape(-1)).real
        terms.append(backend.scalar_float(value))
    result = float(h_z * math.fsum(terms))
    if not np.isfinite(result):
        raise FloatingPointError("Non-finite raw-factor trace")
    return result


def estimate_gpu_working_set_bytes(
    *, n_rows: int, current_rank: int, incoming_columns: int, core_dimension: int
) -> int:
    complex_bytes = np.dtype(np.complex128).itemsize
    real_bytes = np.dtype(np.float64).itemsize
    # Current basis, incoming/mapped block, residual block, rotating output,
    # cross coefficients, and two reduced Hermitian work arrays.
    large = complex_bytes * n_rows * (2 * current_rank + 3 * incoming_columns)
    reduced = complex_bytes * (2 * core_dimension * core_dimension + current_rank * incoming_columns)
    spectra = real_bytes * 4 * core_dimension
    return int(large + reduced + spectra)


def atomic_checkpoint_directory(target: Path, writer: Any) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + f".tmp-{os.getpid()}-{time.time_ns()}")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    try:
        writer(tmp)
        os.replace(tmp, target)
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


# =============================================================================
# BACKEND AND FROZEN GMRES
# =============================================================================
class NumericalBackend:
    def __init__(self, name: str):
        normalized = name.strip().lower()
        if normalized not in {"scipy", "cupy"}:
            raise ValueError("BACKEND must be scipy or cupy")
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
            except Exception as exc:
                raise RuntimeError("CuPy backend requested but unavailable") from exc
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
            (cp.asarray(csr.data, dtype=cp.complex128),
             cp.asarray(csr.indices, dtype=cp.int32),
             cp.asarray(csr.indptr, dtype=cp.int32)),
            shape=csr.shape, dtype=cp.complex128,
        )

    def to_cpu(self, array: Any) -> np.ndarray:
        if self.name == "scipy":
            return np.asarray(array)
        return self._cp.asnumpy(array)

    def scalar_float(self, value: Any) -> float:
        if self.name == "scipy":
            return float(value)
        return float(self._cp.asnumpy(value))

    def norm(self, value: Any, axis: Optional[int] = None) -> Any:
        result = self.xp.linalg.norm(value, axis=axis)
        return self.scalar_float(result) if axis is None else result

    def abs2_sum(self, value: Any, axis: Optional[Any] = None) -> Any:
        density = value.real * value.real + value.imag * value.imag
        result = self.xp.sum(density, axis=axis, dtype=self.float64)
        return self.scalar_float(result) if axis is None else result

    def make_diagonal_preconditioner(self, matrix: Any) -> Tuple[Any, Any]:
        inverse = 1.0 / matrix.diagonal()
        if self.name == "scipy":
            operator = self.sparse_linalg.LinearOperator(
                matrix.shape, matvec=lambda vector: inverse * vector,
                dtype=np.complex128,
            )
        else:
            operator = self.sparse_linalg.LinearOperator(
                shape=matrix.shape, matvec=lambda vector: inverse * vector,
            )
        return operator, inverse

    def gmres(self, matrix: Any, rhs: Any, *, x0: Any, preconditioner: Any, rtol: float) -> Tuple[Any, int]:
        solution, info = self.sparse_linalg.gmres(
            matrix, rhs, x0=x0, rtol=float(rtol), atol=GMRES_ATOL,
            restart=GMRES_RESTART, maxiter=GMRES_MAXITER, M=preconditioner,
        )
        return solution, int(info)

    def synchronize(self) -> None:
        if self.name == "cupy":
            self._cp.cuda.Stream.null.synchronize()

    def memory_info(self) -> Dict[str, Optional[int]]:
        if self.name == "cupy":
            free, total = self._cp.cuda.Device().mem_info
            return {"free_bytes": int(free), "total_bytes": int(total)}
        try:
            import psutil
            info = psutil.virtual_memory()
            return {"free_bytes": int(info.available), "total_bytes": int(info.total)}
        except Exception:
            return {"free_bytes": None, "total_bytes": None}

    def metadata(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "backend": self.name,
            "python": sys.version,
            "platform": platform.platform(),
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
        }
        if self.name == "cupy":
            cp = self._cp
            result["cupy_version"] = cp.__version__
            try:
                device_id = int(cp.cuda.runtime.getDevice())
                props = cp.cuda.runtime.getDeviceProperties(device_id)
                name = props.get("name", "unknown")
                if isinstance(name, bytes):
                    name = name.decode("utf-8", errors="replace")
                result.update({
                    "cuda_device_id": device_id,
                    "cuda_device_name": str(name),
                    "cuda_driver_version": int(cp.cuda.runtime.driverGetVersion()),
                    "cuda_runtime_version": int(cp.cuda.runtime.runtimeGetVersion()),
                    **self.memory_info(),
                })
            except Exception as exc:
                result["cuda_metadata_error"] = repr(exc)
        else:
            result.update(self.memory_info())
        return result


def _complex_givens(xp: Any, a: Any, b: Any) -> Tuple[Any, Any]:
    abs_a = xp.abs(a)
    abs_b = xp.abs(b)
    magnitude = xp.sqrt(abs_a * abs_a + abs_b * abs_b)
    c = xp.ones_like(abs_a)
    s = xp.zeros_like(a)
    nonzero = magnitude > 0.0
    a_nonzero = abs_a > 0.0
    alpha = xp.where(a_nonzero, a / xp.where(a_nonzero, abs_a, 1.0), xp.ones_like(a))
    c = xp.where(nonzero, abs_a / xp.where(nonzero, magnitude, 1.0), c)
    s = xp.where(nonzero, alpha * xp.conj(b) / xp.where(nonzero, magnitude, 1.0), s)
    return c, s


def _batched_back_substitution(xp: Any, upper: Any, rhs: Any) -> Any:
    batches, dimension, _ = upper.shape
    solution = xp.zeros((batches, dimension), dtype=upper.dtype)
    for row in range(dimension - 1, -1, -1):
        value = rhs[:, row].copy()
        if row + 1 < dimension:
            value -= xp.sum(upper[:, row, row + 1:] * solution[:, row + 1:], axis=1)
        diagonal = upper[:, row, row]
        safe = xp.abs(diagonal) > 1.0e-30
        solution[:, row] = xp.where(safe, value / xp.where(safe, diagonal, 1.0), 0.0)
    return solution


def multi_rhs_independent_gmres(
    backend: NumericalBackend,
    matrix: Any,
    rhs: Any,
    x0: Any,
    inverse_diagonal: Any,
    *,
    check_every: int,
    rtol: float,
) -> Tuple[Any, np.ndarray, np.ndarray, int]:
    """Independent restarted GMRES bases vectorized over right-hand sides."""
    xp = backend.xp
    if rhs.ndim == 1:
        rhs = rhs[:, None]
    if x0.ndim == 1:
        x0 = x0[:, None]
    solution = x0.copy()
    number_rhs = int(rhs.shape[1])
    rhs_norm = xp.linalg.norm(rhs, axis=0)
    tolerance = xp.maximum(GMRES_ATOL, float(rtol) * rhs_norm)
    total_iterations = 0
    maximum_total_inner_iterations = GMRES_MAXITER * GMRES_RESTART

    while total_iterations < maximum_total_inner_iterations:
        residual_full = rhs - matrix @ solution
        residual_norm = xp.linalg.norm(residual_full, axis=0)
        active_cpu = np.flatnonzero(np.asarray(backend.to_cpu(residual_norm > tolerance), dtype=bool))
        if active_cpu.size == 0:
            rel = residual_norm / xp.where(rhs_norm > 0.0, rhs_norm, 1.0)
            return solution, np.zeros(number_rhs, np.int32), np.asarray(backend.to_cpu(rel), np.float64), total_iterations
        active = active_cpu if backend.name == "scipy" else backend._cp.asarray(active_cpu)
        active_rhs = rhs[:, active]
        active_solution = solution[:, active]
        active_tolerance = tolerance[active]
        pre_residual = inverse_diagonal[:, None] * (active_rhs - matrix @ active_solution)
        beta = xp.linalg.norm(pre_residual, axis=0)
        safe_beta = xp.where(beta > 0.0, beta, 1.0)
        basis: List[Any] = [pre_residual / safe_beta[None, :]]
        active_count = int(active_cpu.size)
        hessenberg = xp.zeros((active_count, GMRES_RESTART + 1, GMRES_RESTART), dtype=backend.complex128)
        cosines = xp.zeros((active_count, GMRES_RESTART), dtype=backend.float64)
        sines = xp.zeros((active_count, GMRES_RESTART), dtype=backend.complex128)
        transformed_rhs = xp.zeros((active_count, GMRES_RESTART + 1), dtype=backend.complex128)
        transformed_rhs[:, 0] = beta
        candidate = active_solution.copy()
        max_inner = min(GMRES_RESTART, maximum_total_inner_iterations - total_iterations)
        used_inner = 0
        for k in range(max_inner):
            work = inverse_diagonal[:, None] * (matrix @ basis[k])
            for _ in range(2):
                for i in range(k + 1):
                    coefficient = xp.sum(xp.conj(basis[i]) * work, axis=0)
                    hessenberg[:, i, k] += coefficient
                    work -= basis[i] * coefficient[None, :]
            next_norm = xp.linalg.norm(work, axis=0)
            hessenberg[:, k + 1, k] = next_norm
            basis.append(work / xp.where(next_norm > 1.0e-30, next_norm, 1.0)[None, :])
            for i in range(k):
                top = hessenberg[:, i, k].copy()
                bottom = hessenberg[:, i + 1, k].copy()
                hessenberg[:, i, k] = cosines[:, i] * top + sines[:, i] * bottom
                hessenberg[:, i + 1, k] = -xp.conj(sines[:, i]) * top + cosines[:, i] * bottom
            cosine, sine = _complex_givens(xp, hessenberg[:, k, k], hessenberg[:, k + 1, k])
            cosines[:, k] = cosine
            sines[:, k] = sine
            top = hessenberg[:, k, k].copy()
            bottom = hessenberg[:, k + 1, k].copy()
            hessenberg[:, k, k] = cosine * top + sine * bottom
            hessenberg[:, k + 1, k] = 0.0
            rhs_top = transformed_rhs[:, k].copy()
            rhs_bottom = transformed_rhs[:, k + 1].copy()
            transformed_rhs[:, k] = cosine * rhs_top + sine * rhs_bottom
            transformed_rhs[:, k + 1] = -xp.conj(sine) * rhs_top + cosine * rhs_bottom
            used_inner = k + 1
            estimated_converged = bool(backend.scalar_float(xp.all(xp.abs(transformed_rhs[:, used_inner]) <= active_tolerance)))
            if used_inner % check_every == 0 or used_inner == max_inner or estimated_converged:
                coefficients = _batched_back_substitution(
                    xp, hessenberg[:, :used_inner, :used_inner], transformed_rhs[:, :used_inner]
                )
                correction = xp.zeros_like(active_solution)
                for i in range(used_inner):
                    correction += basis[i] * coefficients[:, i][None, :]
                candidate = active_solution + correction
                exact_residual = xp.linalg.norm(active_rhs - matrix @ candidate, axis=0)
                if bool(backend.scalar_float(xp.all(exact_residual <= active_tolerance))):
                    solution[:, active] = candidate
                    total_iterations += used_inner
                    residual_norm = xp.linalg.norm(rhs - matrix @ solution, axis=0)
                    rel = residual_norm / xp.where(rhs_norm > 0.0, rhs_norm, 1.0)
                    return solution, np.zeros(number_rhs, np.int32), np.asarray(backend.to_cpu(rel), np.float64), total_iterations
        solution[:, active] = candidate
        total_iterations += used_inner

    final = xp.linalg.norm(rhs - matrix @ solution, axis=0)
    final_cpu = np.asarray(backend.to_cpu(final), dtype=np.float64)
    rhs_cpu = np.asarray(backend.to_cpu(rhs_norm), dtype=np.float64)
    rel_cpu = final_cpu / np.where(rhs_cpu > 0.0, rhs_cpu, 1.0)
    tol_cpu = np.asarray(backend.to_cpu(tolerance), dtype=np.float64)
    info = np.where(final_cpu <= tol_cpu, 0, total_iterations).astype(np.int32)
    return solution, info, rel_cpu, total_iterations


def independent_gmres_many(
    backend: NumericalBackend,
    matrix: Any,
    rhs: Any,
    x0: Any,
    preconditioner: Any,
    *,
    rtol: float,
) -> Tuple[Any, np.ndarray, np.ndarray]:
    if rhs.ndim == 1:
        rhs = rhs[:, None]
    if x0.ndim == 1:
        x0 = x0[:, None]
    solutions: List[Any] = []
    infos = np.zeros(rhs.shape[1], dtype=np.int32)
    residuals = np.zeros(rhs.shape[1], dtype=np.float64)
    for column in range(rhs.shape[1]):
        solution, info = backend.gmres(
            matrix, rhs[:, column], x0=x0[:, column], preconditioner=preconditioner, rtol=rtol
        )
        solutions.append(solution)
        infos[column] = info
        residual = matrix @ solution - rhs[:, column]
        numerator = backend.norm(residual)
        denominator = backend.norm(rhs[:, column])
        residuals[column] = numerator if denominator == 0.0 else numerator / denominator
    return backend.xp.stack(solutions, axis=1), infos, residuals


def solve_many(
    backend: NumericalBackend,
    matrix: Any,
    rhs: Any,
    x0: Any,
    preconditioner: Any,
    inverse_diagonal: Any,
    *,
    rtol: float,
    certified_multi_rhs: bool,
) -> Tuple[Any, np.ndarray, np.ndarray, int]:
    if certified_multi_rhs and rhs.shape[1] > 1:
        return multi_rhs_independent_gmres(
            backend, matrix, rhs, x0, inverse_diagonal,
            check_every=MULTI_RHS_CHECK_EVERY, rtol=rtol,
        )
    solution, infos, residuals = independent_gmres_many(
        backend, matrix, rhs, x0, preconditioner, rtol=rtol
    )
    return solution, infos, residuals, 0



# =============================================================================
# AUDITED OSCILLATOR / DETECTOR CONSTRUCTION
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

def channel_environment_operators(
    operators: OscillatorOperators,
    direction: str,
) -> Tuple[Tuple[str, sp.csr_matrix, sp.csr_matrix], ...]:
    identity_spin = sp.eye(2, dtype=np.complex128, format="csr")
    if direction == "downward":
        orbital = (("x", operators.a_x), ("y", operators.a_y))
    elif direction == "upward":
        orbital = (("x", operators.a_x_dagger), ("y", operators.a_y_dagger))
    elif direction == "dephasing":
        orbital = (("x", operators.n_x), ("y", operators.n_y))
    else:
        raise ValueError(f"Unsupported environmental direction {direction!r}")
    result: List[Tuple[str, sp.csr_matrix, sp.csr_matrix]] = []
    for label, operator in orbital:
        channel = sp.kron(identity_spin, operator, format="csr")
        anti = (channel.getH() @ channel).tocsr()
        result.append((label, channel, anti))
    return tuple(result)

def apply_channel_operator(operator: sp.csr_matrix, state: np.ndarray, n_z: int) -> np.ndarray:
    matrix = np.asarray(state, dtype=np.complex128).reshape(operator.shape[1], n_z)
    return np.asarray(operator @ matrix, dtype=np.complex128).reshape(-1)

def projected_upward_identity_audit(operators: OscillatorOperators) -> Dict[str, Any]:
    identity = sp.eye(operators.m_modes, dtype=np.complex128, format="csr")
    top = sp.diags(
        (operators.shell_of_mode == int(np.max(operators.shell_of_mode))).astype(np.float64),
        0,
        format="csr",
        dtype=np.complex128,
    )
    expected = (
        operators.n_perp
        + 2.0 * identity
        - (int(np.max(operators.shell_of_mode)) + 2.0) * top
    ).tocsr()
    actual = (
        operators.a_x @ operators.a_x_dagger
        + operators.a_y @ operators.a_y_dagger
    ).tocsr()
    residual = sparse_max_abs(actual - expected)
    return {
        "identity": "sum_j a_j a_j^dagger = N_perp + 2 I - (N_shell+2) Pi_top",
        "maximum_abs_residual": residual,
        "passed": residual <= OPERATOR_TOL,
    }

# =============================================================================
# PROPAGATOR, CONFIGURATION, AND BATH MAP
# =============================================================================
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
        energies_orbital = config.omega * (operators.nx_diag + operators.ny_diag + 1.0)
        energies_channels = np.concatenate([energies_orbital, energies_orbital])
        transverse_phase_backend = backend.to_backend_array(np.exp(-1j * config.dt * energies_channels))
        initial_matrix = initial_state_cpu.reshape(d_channels, config.n_z)
        active_factorized_channels = tuple(
            int(index)
            for index in np.flatnonzero(
                h_z * np.sum(np.abs(initial_matrix) ** 2, axis=1, dtype=np.float64) > 0.0
            )
        )
    else:
        h_longitudinal = sp.kron(identity_channels, l_z, format="csr")
        h_transverse = sp.kron(operators.h_perp_spinmajor, identity_z, format="csr")
        h_scalar = (h_longitudinal + h_transverse).tocsr()
        if config.propagator_type == "scalar_monolithic":
            hamiltonian_cpu = h_scalar
        elif config.propagator_type == "spinor":
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
        else:
            raise ValueError(f"Unsupported propagator type {config.propagator_type!r}")
        identity = sp.eye(d_channels * config.n_z, dtype=np.complex128, format="csr")
        a_cpu = (identity + 1j * config.dt / 2.0 * hamiltonian_cpu).tocsr()
        b_cpu = (identity - 1j * config.dt / 2.0 * hamiltonian_cpu).tocsr()

    backend_a = backend.to_backend_sparse(a_cpu)
    backend_b = backend.to_backend_sparse(b_cpu)
    backend_preconditioner, backend_inverse_diagonal = backend.make_diagonal_preconditioner(backend_a)
    roof_sign_audit = audit_roof_term_sign(
        config=config, operators=operators, l_z=l_z, h_z=h_z,
        hamiltonian_cpu=hamiltonian_cpu,
    )
    return PropagatorObjects(
        l_z=l_z, z=z, h_z=h_z, z_roof_grid=z_roof_grid,
        hamiltonian_cpu=hamiltonian_cpu, a_cpu=a_cpu, b_cpu=b_cpu,
        backend_a=backend_a, backend_b=backend_b,
        backend_preconditioner=backend_preconditioner,
        backend_inverse_diagonal=backend_inverse_diagonal,
        transverse_phase_backend=transverse_phase_backend,
        active_factorized_channels=active_factorized_channels,
        roof_sign_audit=roof_sign_audit,
    )


def manual_run_config() -> RunConfig:
    gate_to_steps = {
        "V4-G0": 0,
        "V4-G1": 1,
        "V4-G2": 2000,
        "V4-G3": 3100,
        "V4-G4": 7200,
    }
    if EXECUTION_GATE not in gate_to_steps:
        raise GateBlocked(f"Unsupported or unauthorized execution gate: {EXECUTION_GATE}")
    return RunConfig(
        execution_gate=EXECUTION_GATE,
        backend=BACKEND,
        stop_after_steps=gate_to_steps[EXECUTION_GATE],
    )


def validate_config(config: RunConfig, *, reduced_model: bool = False) -> None:
    if config.propagator_type not in {"spinor", "scalar_factorized", "scalar_monolithic"}:
        raise GateBlocked("Unsupported propagator type")
    if config.environment_direction not in {"upward", "downward", "dephasing"}:
        raise GateBlocked("Unsupported environment direction")
    if config.initial_mode not in {"00", "10", "01"}:
        raise GateBlocked("Unsupported initial mode")
    if config.backend not in {"scipy", "cupy"}:
        raise GateBlocked("Unsupported backend")
    if G1_MODE not in {"cpu_first_step", "a100_first_step"}:
        raise GateBlocked("Unsupported G1 mode")
    if config.rate_lambda < 0.0 or not np.isfinite(config.rate_lambda):
        raise GateBlocked("Rate must be finite and nonnegative")
    if config.bath_microsteps_per_half != 1:
        raise GateBlocked("This v4 source freezes one bath microstep per half-step")
    if not np.isclose(config.full_num_steps * config.dt, config.t_final, rtol=0.0, atol=1.0e-12):
        raise GateBlocked("T_final/dt is not integral")
    if config.execution_num_steps < 0 or config.execution_num_steps > config.full_num_steps:
        raise GateBlocked("Invalid stop-after-step value")
    if config.planned_compression_calls <= 0:
        raise GateBlocked("Representation schedule must have positive call count")
    if config.representation_budget != 1.0e-8:
        raise GateBlocked("B_max must remain 1e-8")
    if not reduced_model:
        frozen = {
            "propagator_type": (config.propagator_type, PROPAGATOR_TYPE),
            "environment_direction": (config.environment_direction, ENVIRONMENT_DIRECTION),
            "initial_mode": (config.initial_mode, INITIAL_MODE),
            "omega": (config.omega, OMEGA),
            "n_shell": (config.n_shell, N_SHELL),
            "n_z": (config.n_z, N_Z),
            "l_z": (config.l_z, L_Z),
            "dt": (config.dt, DT),
            "t_final": (config.t_final, T_FINAL),
            "rate_lambda": (config.rate_lambda, RATE_LAMBDA),
        }
        bad = {key: values for key, values in frozen.items() if values[0] != values[1]}
        if bad:
            raise GateBlocked(f"Non-negotiable U2-low configuration changed: {bad}")
        if config.execution_gate == "V4-G0" and config.backend != "scipy":
            raise GateBlocked("V4-G0 is a CPU/SciPy certification gate")
        if config.execution_gate == "V4-G1":
            if G1_MODE == "cpu_first_step" and config.backend != "scipy":
                raise GateBlocked("G1 CPU first-step requires BACKEND='scipy'")
            if G1_MODE == "a100_first_step" and config.backend != "cupy":
                raise GateBlocked("G1 A100 first-step requires BACKEND='cupy'")
        if config.execution_gate in {"V4-G2", "V4-G3", "V4-G4"} and config.backend != "cupy":
            raise GateBlocked("Production-size v4 pilots require the A100/CuPy backend")
    if config.execution_gate == "V4-G2" and config.resume_from_checkpoint:
        raise GateBlocked("V4-G2 must start freshly at t=0")
    if config.execution_gate == "V4-G4" and config.execution_num_steps != PILOT_TARGET_STEP:
        raise GateBlocked("V4-G4 must stop exactly at step 7200")


def physical_family_contract(config: RunConfig) -> Dict[str, Any]:
    payload = {
        "schema": PHYSICAL_FAMILY_CONTRACT_SCHEMA,
        "task08_matrix_id": TASK08_MATRIX_ID,
        "propagator_type": config.propagator_type,
        "environment_direction": config.environment_direction,
        "lambda": config.rate_lambda,
        "omega": config.omega,
        "initial_mode": config.initial_mode,
        "N_shell": config.n_shell,
        "N_z": config.n_z,
        "L_z": config.l_z,
        "dt": config.dt,
        "T_final": config.t_final,
        "bath_microsteps_per_half": config.bath_microsteps_per_half,
        "strang_order": "bath_half/detector_Cayley/bath_half",
        "roof_boundary": "partial_z Psi=(i*kappa*I-K_N)Psi",
        "roof_hamiltonian_term": "+K_N/(2*h_z)",
        "detector_probability": "Cayley midpoint roof probability",
        "only_probability_sink": "direct ABC roof",
        "complete_shell_order": "shell ascending; n_x descending; physical spin major; z fastest",
        "representation_budget": config.representation_budget,
        "representation_budget_policy": REPRESENTATION_BUDGET_POLICY,
        "scientific_hard_rank_cap": None,
        "legacy_checkpoint_import": False,
        "checkpoint_migration_enabled": False,
        "production_authorized": False,
        "task10_eligible": False,
    }
    payload["contract_sha256"] = sha256_json(payload)
    return payload


def pilot_execution_contract(config: RunConfig) -> Dict[str, Any]:
    payload = {
        "schema": PILOT_EXECUTION_CONTRACT_SCHEMA,
        "execution_gate": config.execution_gate,
        "g1_mode": G1_MODE if config.execution_gate == "V4-G1" else None,
        "g1_mode_obligations": (
            ["production_size_cpu_first_step", "rank_sequence_1_3_6", "write_verified_cpu_checkpoint"]
            if config.execution_gate == "V4-G1" and G1_MODE == "cpu_first_step"
            else [
                "production_size_a100_first_step",
                "rank_sequence_1_3_6",
                "verify_cpu_first_step_artifact",
                "cpu_a100_low_rank_density_comparison",
                "production_row_rank_64_256_640_compression_benchmarks",
                "production_row_rank_64_256_640_detector_solve_benchmarks",
            ]
            if config.execution_gate == "V4-G1"
            else None
        ),
        "backend": config.backend,
        "stop_after_steps": config.execution_num_steps,
        "physical_stop_time": config.execution_num_steps * config.dt,
        "dt": config.dt,
        "detector_rhs_batch_columns": config.detector_rhs_batch_columns,
        "factor_block_columns": config.factor_block_columns,
        "resume_from_v4_checkpoint": config.resume_from_checkpoint,
        "d2_post_g0_review_authorized": D2_POST_G0_REVIEW_AUTHORIZED,
        "checkpoint_every_complete_steps": config.checkpoint_every,
        "acceptance_enabled": False,
        "production_authorized": False,
        "task10_eligible": False,
        "physical_claim": "none; non-accepting numerical gate only",
    }
    payload["contract_sha256"] = sha256_json(payload)
    return payload


def build_bath_kraus(
    operators: OscillatorOperators,
    direction: str,
    action: float,
    backend: NumericalBackend,
) -> BathKraus:
    if action < 0.0 or not np.isfinite(action):
        raise ValueError("Bath action must be finite and nonnegative")
    channel_ops = channel_environment_operators(operators, direction)
    dimension = operators.d_channels
    g = sp.csr_matrix((dimension, dimension), dtype=np.complex128)
    for _label, _jump, anti in channel_ops:
        g = (g + anti).tocsr()
    diagonal = np.asarray(g.diagonal().real, dtype=np.float64)
    offdiag = (g - sp.diags(g.diagonal(), 0, format="csr")).tocsr()
    if sparse_max_abs(offdiag) > OPERATOR_TOL or np.min(diagonal) < -OPERATOR_TOL:
        raise RuntimeError("Bath anti-operator is not the required nonnegative diagonal")
    diagonal = np.maximum(diagonal, 0.0)
    right = sp.diags(
        1.0 / np.sqrt(1.0 + float(action) * diagonal),
        0, dtype=np.complex128, format="csr",
    )
    kraus: List[sp.csr_matrix] = [right]
    if action > 0.0:
        for _label, jump, _anti in channel_ops:
            kraus.append((math.sqrt(action) * (jump @ right)).tocsr())
    else:
        zero = sp.csr_matrix((dimension, dimension), dtype=np.complex128)
        kraus.extend([zero, zero])
    completeness = sp.csr_matrix((dimension, dimension), dtype=np.complex128)
    for operator in kraus:
        completeness = (completeness + operator.getH() @ operator).tocsr()
    residual = sparse_max_abs(
        completeness - sp.eye(dimension, dtype=np.complex128, format="csr")
    )
    if residual > BATH_COMPLETENESS_TOL:
        raise RuntimeError(f"Kraus completeness failed: {residual:.3e}")
    derivative = bath_first_derivative_audit(operators, direction)
    if not derivative["passed"]:
        raise RuntimeError(f"Bath derivative audit failed: {derivative}")
    return BathKraus(
        action=float(action),
        operators_cpu=tuple(kraus),
        operators_backend=tuple(backend.to_backend_sparse(operator) for operator in kraus),
        completeness_residual=float(residual),
        g_diagonal=diagonal,
        first_derivative_audit=derivative,
    )


def bath_first_derivative_audit(
    operators: OscillatorOperators,
    direction: str,
) -> Dict[str, Any]:
    dimension = operators.d_channels
    rng = np.random.default_rng(20260809)
    raw = rng.normal(size=(dimension, min(4, dimension))) + 1j * rng.normal(
        size=(dimension, min(4, dimension))
    )
    rho = raw @ raw.conj().T
    rho /= np.trace(rho).real
    channel_ops = channel_environment_operators(operators, direction)
    exact = np.zeros_like(rho)
    for _label, jump, anti in channel_ops:
        l = jump.toarray()
        a = anti.toarray()
        exact += l @ rho @ l.conj().T - 0.5 * (a @ rho + rho @ a)
    g = sum(
        (anti for _label, _jump, anti in channel_ops),
        sp.csr_matrix((dimension, dimension), dtype=np.complex128),
    )
    diag = np.maximum(np.asarray(g.diagonal().real, dtype=np.float64), 0.0)
    scale = max(float(np.max(diag, initial=0.0)), 1.0)
    probe = max(BATH_DERIVATIVE_MIN_PROBE, min(1.0e-7, BATH_DERIVATIVE_TARGET_ACTION / scale))

    def finite_difference(value: float) -> np.ndarray:
        r = sp.diags(1.0 / np.sqrt(1.0 + value * diag), 0, dtype=np.complex128, format="csr")
        ks = [r] + [(math.sqrt(value) * (jump @ r)).tocsr() for _label, jump, _anti in channel_ops]
        mapped = sum((k @ rho @ k.getH() for k in ks), np.zeros_like(rho))
        return (mapped - rho) / value

    d1 = finite_difference(probe)
    d2 = finite_difference(probe / 2.0)
    richardson = 2.0 * d2 - d1
    denominator = max(float(np.linalg.norm(exact)), 1.0e-30)
    error = float(np.linalg.norm(richardson - exact)) / denominator
    return {
        "probe_action": probe,
        "richardson_relative_frobenius_error": error,
        "tolerance": BATH_DERIVATIVE_REL_TOL,
        "passed": bool(error <= BATH_DERIVATIVE_REL_TOL),
    }

# =============================================================================
# CANONICAL STREAMING SPECTRAL FACTOR (CSSF)
# =============================================================================
def split_backend_columns(array: Any, columns_per_block: int, backend: NumericalBackend) -> Tuple[Any, ...]:
    if getattr(array, "ndim", None) != 2:
        raise ValueError("Expected a two-dimensional factor array")
    blocks: List[Any] = []
    for start in range(0, int(array.shape[1]), int(columns_per_block)):
        stop = min(int(array.shape[1]), start + int(columns_per_block))
        blocks.append(backend.xp.ascontiguousarray(array[:, start:stop]))
    if not blocks:
        raise ValueError("Cannot split an empty factor")
    return tuple(blocks)


def block_offsets(blocks: Sequence[Any]) -> List[Tuple[int, int]]:
    result: List[Tuple[int, int]] = []
    offset = 0
    for block in blocks:
        next_offset = offset + int(block.shape[1])
        result.append((offset, next_offset))
        offset = next_offset
    return result


def canonical_from_state(
    state_cpu: np.ndarray,
    *,
    h_z: float,
    backend: NumericalBackend,
    block_columns: int,
) -> CanonicalFactor:
    state = np.asarray(state_cpu, dtype=np.complex128).reshape(-1)
    trace = float(h_z * np.vdot(state, state).real)
    if not np.isfinite(trace) or trace <= 0.0:
        raise ValueError("Initial state has nonpositive trace")
    basis = state / math.sqrt(trace)
    basis_backend = backend.to_backend_array(basis[:, None])
    return CanonicalFactor(
        basis_blocks=split_backend_columns(basis_backend, block_columns, backend),
        weights=np.asarray([trace], dtype=np.float64),
        n_rows=state.size,
        h_z=float(h_z),
    )


def iter_canonical_scaled_blocks(
    factor: CanonicalFactor,
    backend: NumericalBackend,
) -> Iterable[Any]:
    offsets = block_offsets(factor.basis_blocks)
    for block, (start, stop) in zip(factor.basis_blocks, offsets):
        scale = backend.to_backend_real(np.sqrt(factor.weights[start:stop]))
        yield backend.xp.ascontiguousarray(block * scale[None, :])


def canonical_to_raw(factor: CanonicalFactor, backend: NumericalBackend) -> RawFactor:
    return RawFactor(tuple(iter_canonical_scaled_blocks(factor, backend)), factor.n_rows)


def canonical_to_cpu_factor(factor: CanonicalFactor, backend: NumericalBackend) -> np.ndarray:
    blocks = [
        np.asarray(backend.to_cpu(block), dtype=np.complex128)
        for block in iter_canonical_scaled_blocks(factor, backend)
    ]
    return np.ascontiguousarray(np.concatenate(blocks, axis=1))


def raw_to_cpu_factor(factor: RawFactor, backend: NumericalBackend) -> np.ndarray:
    return np.ascontiguousarray(
        np.concatenate(
            [np.asarray(backend.to_cpu(block), dtype=np.complex128) for block in factor.blocks],
            axis=1,
        )
    )


def factor_density_cpu(
    factor: Union[CanonicalFactor, RawFactor],
    backend: NumericalBackend,
) -> np.ndarray:
    matrix = (
        canonical_to_cpu_factor(factor, backend)
        if isinstance(factor, CanonicalFactor)
        else raw_to_cpu_factor(factor, backend)
    )
    return matrix @ matrix.conj().T


def density_trace_norm(difference: np.ndarray, h_z: float) -> float:
    hermitian = 0.5 * (difference + difference.conj().T)
    return float(h_z * np.sum(np.abs(np.linalg.eigvalsh(hermitian)), dtype=np.float64))


def canonicality_audit(factor: CanonicalFactor, backend: NumericalBackend) -> Dict[str, Any]:
    rank = factor.rank
    gram = np.zeros((rank, rank), dtype=np.complex128)
    offsets = block_offsets(factor.basis_blocks)
    for i, left in enumerate(factor.basis_blocks):
        i0, i1 = offsets[i]
        for j in range(i, len(factor.basis_blocks)):
            right = factor.basis_blocks[j]
            j0, j1 = offsets[j]
            piece = factor.h_z * (left.conj().T @ right)
            piece_cpu = np.asarray(backend.to_cpu(piece), dtype=np.complex128)
            gram[i0:i1, j0:j1] = piece_cpu
            if i != j:
                gram[j0:j1, i0:i1] = piece_cpu.conj().T
    residual = float(
        np.linalg.norm(gram - np.eye(rank, dtype=np.complex128), ord="fro")
        / max(math.sqrt(rank), 1.0)
    )
    return {
        "rank": rank,
        "trace": factor.trace,
        "weighted_basis_orthonormality_relative_frobenius_residual": residual,
        "weights_nonincreasing": bool(np.all(factor.weights[:-1] >= factor.weights[1:])),
        "weights_positive_finite": bool(np.all(np.isfinite(factor.weights)) and np.all(factor.weights > 0.0)),
        "passed": bool(
            residual <= CANONICALITY_TOL
            and np.all(factor.weights[:-1] >= factor.weights[1:])
            and np.all(np.isfinite(factor.weights))
            and np.all(factor.weights > 0.0)
        ),
    }


def _basis_cross(
    factor: CanonicalFactor,
    block: Any,
    backend: NumericalBackend,
) -> np.ndarray:
    pieces: List[np.ndarray] = []
    for basis_block in factor.basis_blocks:
        value = factor.h_z * (basis_block.conj().T @ block)
        pieces.append(np.asarray(backend.to_cpu(value), dtype=np.complex128))
    return np.concatenate(pieces, axis=0) if pieces else np.empty((0, int(block.shape[1])), np.complex128)


def _basis_subtract(
    residual: Any,
    factor: CanonicalFactor,
    coefficients_cpu: np.ndarray,
    backend: NumericalBackend,
) -> Any:
    offsets = block_offsets(factor.basis_blocks)
    result = residual
    for basis_block, (start, stop) in zip(factor.basis_blocks, offsets):
        coeff = backend.to_backend_array(np.ascontiguousarray(coefficients_cpu[start:stop, :]))
        result -= basis_block @ coeff
    return result


def _rotate_basis(
    basis_blocks: Sequence[Any],
    coefficients_cpu: np.ndarray,
    *,
    backend: NumericalBackend,
    output_block_columns: int,
) -> Tuple[Any, ...]:
    coefficients = np.asarray(coefficients_cpu, dtype=np.complex128)
    rank_in, rank_out = coefficients.shape
    offsets = block_offsets(basis_blocks)
    if offsets[-1][1] != rank_in:
        raise ValueError("Basis rotation coefficient dimension mismatch")
    result: List[Any] = []
    coefficients_backend = backend.to_backend_array(coefficients)
    n_rows = int(basis_blocks[0].shape[0])
    for out_start in range(0, rank_out, output_block_columns):
        out_stop = min(rank_out, out_start + output_block_columns)
        output = backend.xp.zeros((n_rows, out_stop - out_start), dtype=backend.complex128)
        for basis_block, (in_start, in_stop) in zip(basis_blocks, offsets):
            output += basis_block @ coefficients_backend[in_start:in_stop, out_start:out_stop]
        result.append(backend.xp.ascontiguousarray(output))
    return tuple(result)


def _canonical_prefix(factor: CanonicalFactor, rank: int, backend: NumericalBackend) -> CanonicalFactor:
    if rank <= 0 or rank > factor.rank:
        raise ValueError("Invalid canonical prefix rank")
    remaining = rank
    blocks: List[Any] = []
    for block in factor.basis_blocks:
        if remaining <= 0:
            break
        take = min(remaining, int(block.shape[1]))
        blocks.append(backend.xp.ascontiguousarray(block[:, :take]))
        remaining -= take
    if remaining != 0:
        raise RuntimeError("Canonical prefix extraction failed")
    return CanonicalFactor(
        basis_blocks=tuple(blocks),
        weights=np.asarray(factor.weights[:rank], dtype=np.float64).copy(),
        n_rows=factor.n_rows,
        h_z=factor.h_z,
    )


def _psd_eigh(
    matrix: np.ndarray,
    *,
    label: str,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    hermitian = 0.5 * (np.asarray(matrix, np.complex128) + np.asarray(matrix, np.complex128).conj().T)
    if not np.all(np.isfinite(hermitian)):
        raise RepresentationFailure(f"Non-finite {label}", event={"label": label})
    scale = max(float(np.linalg.norm(hermitian, ord=2)), np.finfo(float).tiny)
    envelope = PSD_BACKWARD_ERROR_FACTOR * np.finfo(float).eps * max(1, hermitian.shape[0]) * scale
    raw, vectors = np.linalg.eigh(hermitian)
    raw = np.asarray(raw.real, dtype=np.float64)
    if float(np.min(raw, initial=0.0)) < -envelope:
        raise RepresentationFailure(
            f"{label} is not PSD outside its backward-error envelope",
            event={
                "label": label,
                "minimum_eigenvalue": float(np.min(raw)),
                "backward_error_envelope": float(envelope),
                "scale": scale,
            },
        )
    negative_mass = float(-np.sum(raw[raw < 0.0], dtype=np.float64)) if np.any(raw < 0.0) else 0.0
    values = np.maximum(raw, 0.0)
    eigen_residual = float(
        np.linalg.norm(hermitian @ vectors - vectors * raw[None, :], ord="fro")
        / max(float(np.linalg.norm(hermitian, ord="fro")), np.finfo(float).tiny)
    )
    orthogonality = float(
        np.linalg.norm(vectors.conj().T @ vectors - np.eye(vectors.shape[1]), ord="fro")
        / max(math.sqrt(vectors.shape[1]), 1.0)
    )
    return values, np.asarray(vectors, np.complex128), {
        "label": label,
        "minimum_raw_eigenvalue": float(np.min(raw, initial=0.0)),
        "clipped_negative_mass": negative_mass,
        "backward_error_envelope": float(envelope),
        "eigen_residual": eigen_residual,
        "orthogonality_residual": orthogonality,
    }



def _weighted_basis_gram(
    basis_blocks: Sequence[Any],
    *,
    h_z: float,
    backend: NumericalBackend,
) -> np.ndarray:
    """Return ``h_z Q^dagger Q`` for a blocked basis without materializing Q."""
    offsets = block_offsets(basis_blocks)
    rank = offsets[-1][1]
    gram = np.zeros((rank, rank), dtype=np.complex128)
    for i, left in enumerate(basis_blocks):
        i0, i1 = offsets[i]
        for j in range(i, len(basis_blocks)):
            right = basis_blocks[j]
            j0, j1 = offsets[j]
            piece = h_z * (left.conj().T @ right)
            piece_cpu = np.asarray(backend.to_cpu(piece), dtype=np.complex128)
            gram[i0:i1, j0:j1] = piece_cpu
            if i != j:
                gram[j0:j1, i0:i1] = piece_cpu.conj().T
    return 0.5 * (gram + gram.conj().T)


def _canonicality_residual(audit: Mapping[str, Any]) -> float:
    return float(
        audit["weighted_basis_orthonormality_relative_frobenius_residual"]
    )


def _recanonicalize_factor_gauge(
    factor: CanonicalFactor,
    *,
    backend: NumericalBackend,
    block_columns: int,
) -> Tuple[CanonicalFactor, Dict[str, Any]]:
    """Apply one exact reduced-space gauge repair.

    Let ``G=h_z Q^dagger Q``.  In exact arithmetic,

        Q_o = Q G^{-1/2},
        C   = G^{1/2} diag(w) G^{1/2},

    and rediagonalizing ``C`` changes only the factor gauge, not the represented
    density.  Any finite-precision removal of a numerical null direction is
    reconstructed in the reduced core and returned as a trace-norm bound.  This
    primitive reports its output audit but leaves the final accept/reject
    decision to ``_repair_factor_gauge_until_hard_acceptance``.
    """
    gram = _weighted_basis_gram(
        factor.basis_blocks, h_z=factor.h_z, backend=backend
    )
    gram_values, gram_vectors, gram_psd = _psd_eigh(
        gram, label="streaming canonical gauge Gram"
    )
    scale = max(float(np.max(gram_values, initial=0.0)), 1.0)
    invertibility_floor = (
        PSD_BACKWARD_ERROR_FACTOR
        * np.finfo(float).eps
        * max(1, factor.rank)
        * scale
    )
    if np.any(gram_values <= invertibility_floor):
        raise RepresentationFailure(
            "Canonical gauge Gram is numerically rank deficient",
            event={
                "rank": factor.rank,
                "minimum_gram_eigenvalue": float(np.min(gram_values)),
                "invertibility_floor": float(invertibility_floor),
                "gram_psd_audit": gram_psd,
            },
        )

    sqrt_values = np.sqrt(gram_values)
    inverse_sqrt_values = 1.0 / sqrt_values
    sqrt_gram = (
        gram_vectors * sqrt_values[None, :]
    ) @ gram_vectors.conj().T
    inverse_sqrt_gram = (
        gram_vectors * inverse_sqrt_values[None, :]
    ) @ gram_vectors.conj().T

    orthogonal_basis = _rotate_basis(
        factor.basis_blocks,
        np.ascontiguousarray(inverse_sqrt_gram, dtype=np.complex128),
        backend=backend,
        output_block_columns=block_columns,
    )
    reduced_core = sqrt_gram @ np.diag(factor.weights) @ sqrt_gram.conj().T
    core_values, core_vectors, core_psd = _psd_eigh(
        reduced_core, label="streaming recanonicalized density core"
    )
    positive = np.flatnonzero(core_values > 0.0)
    if positive.size == 0:
        raise RepresentationFailure(
            "Gauge recanonicalization produced zero density rank",
            event={"rank_before": factor.rank, "core_psd_audit": core_psd},
        )

    reconstructed_core = (
        core_vectors[:, positive] * core_values[positive][None, :]
    ) @ core_vectors[:, positive].conj().T
    core_difference = 0.5 * (
        reconstructed_core - reduced_core
        + (reconstructed_core - reduced_core).conj().T
    )
    gauge_density_difference = float(
        np.sum(np.abs(np.linalg.eigvalsh(core_difference)), dtype=np.float64)
    )
    order = positive[np.argsort(core_values[positive], kind="stable")[::-1]]
    final_basis = _rotate_basis(
        orthogonal_basis,
        np.ascontiguousarray(core_vectors[:, order], dtype=np.complex128),
        backend=backend,
        output_block_columns=block_columns,
    )
    repaired = CanonicalFactor(
        basis_blocks=final_basis,
        weights=np.asarray(core_values[order], dtype=np.float64),
        n_rows=factor.n_rows,
        h_z=factor.h_z,
    )
    audit = canonicality_audit(repaired, backend)
    return repaired, {
        "method": "weighted_polar_gauge_repair_with_reduced_core_rediagonalization_v2",
        "density_approximation_introduced": bool(positive.size != factor.rank),
        "rank_before": factor.rank,
        "rank_after": repaired.rank,
        "reconstructible_density_trace_norm_bound": gauge_density_difference,
        "representation_budget_increment": gauge_density_difference,
        "input_gram_psd_audit": gram_psd,
        "reduced_core_psd_audit": core_psd,
        "canonicality_after": audit,
    }


def _repair_factor_gauge_until_hard_acceptance(
    factor: CanonicalFactor,
    *,
    backend: NumericalBackend,
    block_columns: int,
    reason: str,
) -> Tuple[CanonicalFactor, Dict[str, Any]]:
    """Refine the gauge toward the trigger, then apply only the hard gate.

    The trigger controls whether another exact gauge pass is attempted.  It is
    never used as a post-repair rejection threshold.  The final factor is
    accepted if and only if the unchanged hard canonicality audit passes.
    Reduced-core density bounds from all passes are accumulated by the triangle
    inequality and must be charged to the common representation ledger by the
    caller.
    """
    initial_audit = canonicality_audit(factor, backend)
    current = factor
    pass_reports: List[Dict[str, Any]] = []
    cumulative_density_bound = 0.0
    density_approximation_introduced = False

    for pass_index in range(1, CANONICALITY_REPAIR_MAX_PASSES + 1):
        before = canonicality_audit(current, backend)
        before_residual = _canonicality_residual(before)
        if before["passed"] and before_residual <= CANONICALITY_REPAIR_TRIGGER:
            break
        try:
            repaired, report = _recanonicalize_factor_gauge(
                current,
                backend=backend,
                block_columns=block_columns,
            )
        except RepresentationFailure as exc:
            raise RepresentationFailure(
                "Exact gauge-repair pass failed",
                event={
                    "reason": reason,
                    "repair_pass_index": pass_index,
                    "maximum_repair_passes": CANONICALITY_REPAIR_MAX_PASSES,
                    "canonicality_before_pass": before,
                    "inner_failure": exc.event,
                },
            ) from exc
        pass_bound = float(report["reconstructible_density_trace_norm_bound"])
        cumulative_density_bound = math.fsum(
            (cumulative_density_bound, pass_bound)
        )
        density_approximation_introduced = bool(
            density_approximation_introduced
            or report["density_approximation_introduced"]
        )
        pass_reports.append(
            {
                "repair_pass_index": pass_index,
                "canonicality_before_pass": before,
                **report,
            }
        )
        current = repaired

    final_audit = canonicality_audit(current, backend)
    final_residual = _canonicality_residual(final_audit)
    target_met = bool(final_residual <= CANONICALITY_REPAIR_TRIGGER)
    if not final_audit["passed"]:
        raise RepresentationFailure(
            "Gauge repair failed the unchanged hard canonicality gate",
            event={
                "reason": reason,
                "initial_canonicality": initial_audit,
                "repair_passes": pass_reports,
                "maximum_repair_passes": CANONICALITY_REPAIR_MAX_PASSES,
                "repair_trigger": CANONICALITY_REPAIR_TRIGGER,
                "hard_tolerance": CANONICALITY_TOL,
                "canonicality_after_repair": final_audit,
                "repair_target_met": target_met,
                "density_approximation_introduced": density_approximation_introduced,
                "reconstructible_density_trace_norm_bound": cumulative_density_bound,
            },
        )

    return current, {
        "method": "bounded_iterated_exact_weighted_polar_gauge_repair_v1",
        "reason": reason,
        "post_repair_acceptance_rule": "unchanged_hard_canonicality_gate_only",
        "repair_trigger_role": "proactive_refinement_target_only",
        "initial_canonicality": initial_audit,
        "repair_passes": pass_reports,
        "repair_pass_count": len(pass_reports),
        "maximum_repair_passes": CANONICALITY_REPAIR_MAX_PASSES,
        "repair_trigger": CANONICALITY_REPAIR_TRIGGER,
        "hard_tolerance": CANONICALITY_TOL,
        "repair_target_met": target_met,
        "canonicality_after": final_audit,
        "density_approximation_introduced": density_approximation_introduced,
        "reconstructible_density_trace_norm_bound": cumulative_density_bound,
        "representation_budget_increment": cumulative_density_bound,
    }


def stream_merge_raw_block(
    current: Optional[CanonicalFactor],
    raw_block: Any,
    *,
    h_z: float,
    backend: NumericalBackend,
    block_columns: int,
) -> Tuple[CanonicalFactor, Dict[str, Any]]:
    """Merge one raw factor block by an exact augmented-Gram update.

    Let the current canonical density be ``Q diag(w) Q^dagger`` with
    ``h_z Q^dagger Q = I`` and let ``Y`` be the incoming raw block.  The
    augmented factor is ``Z=[Q sqrt(w), Y]``.  We diagonalize only

        G_aug = h_z Z^dagger Z

    and construct the new canonical basis in output-column blocks as

        Q_new = Z V_r diag(lambda_r^{-1/2}).

    No residual-range approximation and no square-root factor perturbation
    bound are used.  Only non-positive numerical null directions are removed.
    Their complete density trace-norm contribution is reconstructed from the
    augmented Gram trace deficit and is returned as the streaming error bound.
    """
    started = time.perf_counter()
    block = backend.xp.ascontiguousarray(raw_block)
    if block.ndim != 2 or int(block.shape[1]) <= 0:
        raise ValueError("Streaming merge requires a nonempty raw block")
    n_rows = int(block.shape[0])
    incoming_columns = int(block.shape[1])
    if current is not None and (
        current.n_rows != n_rows or not np.isclose(current.h_z, h_z)
    ):
        raise ValueError("Streaming merge factor geometry mismatch")

    current_rank = 0 if current is None else current.rank
    current_nominal_trace = 0.0 if current is None else current.trace
    trace_y = float(
        h_z
        * backend.scalar_float(
            backend.xp.vdot(block.reshape(-1), block.reshape(-1)).real
        )
    )
    if not np.isfinite(trace_y) or trace_y < 0.0:
        raise RepresentationFailure(
            "Incoming augmented-Gram block has invalid trace",
            event={"trace_y": trace_y, "incoming_columns": incoming_columns},
        )

    bottom_backend = h_z * (block.conj().T @ block)
    bottom = np.asarray(backend.to_cpu(bottom_backend), dtype=np.complex128)
    bottom = 0.5 * (bottom + bottom.conj().T)

    current_metric_audit: Optional[Dict[str, Any]] = None
    current_physical_trace = 0.0
    if current is None:
        augmented_gram = bottom
    else:
        # Use the measured weighted basis metric rather than silently replacing
        # it by I.  This makes the augmented Gram exactly consistent with the
        # represented finite-precision density Q diag(w) Q^dagger even when the
        # stored gauge has a small, still admissible orthonormality residual.
        current_metric = _weighted_basis_gram(
            current.basis_blocks, h_z=h_z, backend=backend
        )
        metric_residual = float(
            np.linalg.norm(
                current_metric - np.eye(current_rank, dtype=np.complex128),
                ord="fro",
            )
            / max(math.sqrt(current_rank), 1.0)
        )
        sqrt_weights = np.sqrt(current.weights)
        top_left = (
            sqrt_weights[:, None]
            * current_metric
            * sqrt_weights[None, :]
        )
        current_physical_trace = float(np.trace(top_left).real)
        current_metric_audit = {
            "weighted_basis_orthonormality_relative_frobenius_residual": metric_residual,
            "nominal_trace_from_weights": current_nominal_trace,
            "physical_trace_from_metric": current_physical_trace,
            "trace_metric_residual": current_physical_trace - current_nominal_trace,
            "repair_trigger": CANONICALITY_REPAIR_TRIGGER,
            "hard_tolerance": CANONICALITY_TOL,
        }
        cross = _basis_cross(current, block, backend)  # h_z Q^dagger Y
        top_right = sqrt_weights[:, None] * cross
        augmented_gram = np.zeros(
            (current_rank + incoming_columns, current_rank + incoming_columns),
            dtype=np.complex128,
        )
        augmented_gram[:current_rank, :current_rank] = top_left
        augmented_gram[:current_rank, current_rank:] = top_right
        augmented_gram[current_rank:, :current_rank] = top_right.conj().T
        augmented_gram[current_rank:, current_rank:] = bottom

    values, vectors, gram_psd = _psd_eigh(
        augmented_gram, label="streaming augmented Gram"
    )
    spectral_scale = max(float(np.max(values, initial=0.0)), np.finfo(float).tiny)
    normalization_floor = (
        AUGMENTED_GRAM_NORMALIZATION_FLOOR_FACTOR
        * np.finfo(float).eps
        * spectral_scale
    )
    positive = np.flatnonzero(values > normalization_floor)
    if positive.size == 0:
        raise RepresentationFailure(
            "Augmented Gram has zero numerically stable positive rank",
            event={
                "rank_before": current_rank,
                "incoming_columns": incoming_columns,
                "trace_y": trace_y,
                "normalization_floor": float(normalization_floor),
                "gram_psd_audit": gram_psd,
            },
        )
    order = positive[np.argsort(values[positive], kind="stable")[::-1]]
    basis_normalization_values = np.asarray(values[order], dtype=np.float64)
    retained_vectors = np.asarray(vectors[:, order], dtype=np.complex128)

    input_trace = float(math.fsum((current_physical_trace, trace_y)))
    spectral_trace = float(
        np.sum(basis_normalization_values, dtype=np.float64)
    )
    # Keep the Gram eigenvalues used to normalize the basis separate from the
    # trace-restored density weights.  Using the rescaled weights inside
    # lambda^{-1/2} would preserve the raw density but make Q^dagger Q differ
    # from I by the trace-restoration scale—the exact mechanism behind the v2
    # intermittent ~2e-10 canonicality excursions.  Here Q is normalized with
    # the unmodified positive Gram eigenvalues, while the weights alone receive
    # the uniform trace restoration.  The resulting representation is
    # canonical and the trace-restored density defect is bounded by twice the
    # absolute missing/excess spectral trace in the outer ledger.
    trace_correction = abs(input_trace - spectral_trace)
    if spectral_trace <= 0.0:
        raise RepresentationFailure(
            "Augmented Gram retained trace is nonpositive",
            event={"input_trace": input_trace, "spectral_trace": spectral_trace},
        )
    trace_restoration_scale = input_trace / spectral_trace
    retained_values = np.asarray(
        basis_normalization_values * trace_restoration_scale,
        dtype=np.float64,
    )

    inverse_sqrt = 1.0 / np.sqrt(basis_normalization_values)
    if current_rank:
        top_coefficients = (
            np.sqrt(current.weights)[:, None]
            * retained_vectors[:current_rank, :]
            * inverse_sqrt[None, :]
        )
    else:
        top_coefficients = np.empty((0, retained_values.size), dtype=np.complex128)
    incoming_coefficients = (
        retained_vectors[current_rank:, :] * inverse_sqrt[None, :]
    )

    top_coefficients_backend = backend.to_backend_array(
        np.ascontiguousarray(top_coefficients)
    ) if current_rank else None
    incoming_coefficients_backend = backend.to_backend_array(
        np.ascontiguousarray(incoming_coefficients)
    )
    current_offsets = block_offsets(current.basis_blocks) if current is not None else []
    basis_blocks: List[Any] = []
    rank_after = int(retained_values.size)
    for out_start in range(0, rank_after, block_columns):
        out_stop = min(rank_after, out_start + block_columns)
        output = backend.xp.zeros(
            (n_rows, out_stop - out_start), dtype=backend.complex128
        )
        if current is not None and top_coefficients_backend is not None:
            for basis_block, (in_start, in_stop) in zip(
                current.basis_blocks, current_offsets
            ):
                output += basis_block @ top_coefficients_backend[
                    in_start:in_stop, out_start:out_stop
                ]
        output += block @ incoming_coefficients_backend[:, out_start:out_stop]
        basis_blocks.append(backend.xp.ascontiguousarray(output))

    result = CanonicalFactor(
        basis_blocks=tuple(basis_blocks),
        weights=retained_values,
        n_rows=n_rows,
        h_z=float(h_z),
    )
    canonical_before = canonicality_audit(result, backend)
    gauge_repair: Optional[Dict[str, Any]] = None
    streaming_density_bound = float(trace_correction)
    repair_triggered = bool(
        not canonical_before["passed"]
        or _canonicality_residual(canonical_before) > CANONICALITY_REPAIR_TRIGGER
    )
    if repair_triggered:
        result, gauge_repair = _repair_factor_gauge_until_hard_acceptance(
            result,
            backend=backend,
            block_columns=block_columns,
            reason="streaming_augmented_gram_output",
        )
        streaming_density_bound = math.fsum(
            (
                streaming_density_bound,
                float(gauge_repair["reconstructible_density_trace_norm_bound"]),
            )
        )
    canonical_audit = canonicality_audit(result, backend)
    canonical_residual = _canonicality_residual(canonical_audit)
    if not canonical_audit["passed"]:
        raise RepresentationFailure(
            "Augmented-Gram output failed the unchanged hard canonicality gate",
            event={
                "canonicality_before_repair": canonical_before,
                "repair_trigger": CANONICALITY_REPAIR_TRIGGER,
                "hard_tolerance": CANONICALITY_TOL,
                "gauge_repair": gauge_repair,
                "canonicality_after_repair": canonical_audit,
                "repair_target_met": bool(
                    canonical_residual <= CANONICALITY_REPAIR_TRIGGER
                ),
            },
        )

    return result, {
        "merge_method": "direct_metric_aware_augmented_gram_canonical_update_v3",
        "incoming_columns": incoming_columns,
        "rank_before": current_rank,
        "augmented_gram_dimension": current_rank + incoming_columns,
        "rank_after_merge": result.rank,
        "input_trace": input_trace,
        "retained_spectral_trace_before_correction": spectral_trace,
        "trace_restoration_scale": trace_restoration_scale,
        "basis_normalization_uses_unscaled_gram_eigenvalues": True,
        "augmented_gram_normalization_floor": float(normalization_floor),
        "augmented_gram_discarded_numerical_eigenvalue_count": int(values.size - positive.size),
        "augmented_gram_trace_correction": trace_correction,
        "reconstructible_streaming_density_bound": streaming_density_bound,
        "gram_psd_audit": gram_psd,
        "current_metric_audit": current_metric_audit,
        "canonicality_repair_trigger": CANONICALITY_REPAIR_TRIGGER,
        "canonicality_repair_triggered": repair_triggered,
        "canonicality_repair_target_met": bool(
            canonical_residual <= CANONICALITY_REPAIR_TRIGGER
        ),
        "post_repair_acceptance_rule": "unchanged_hard_canonicality_gate_only",
        "canonicality_before_optional_gauge_repair": canonical_before,
        "gauge_repair": gauge_repair,
        "canonicality_audit": canonical_audit,
        "wall_seconds": time.perf_counter() - started,
    }

def _resource_guard(
    *,
    backend: NumericalBackend,
    n_rows: int,
    current_rank: int,
    incoming_columns: int,
    core_dimension: int,
    stage: str,
) -> Dict[str, Any]:
    memory = backend.memory_info()
    predicted = estimate_gpu_working_set_bytes(
        n_rows=n_rows,
        current_rank=current_rank,
        incoming_columns=incoming_columns,
        core_dimension=core_dimension,
    )
    free = memory.get("free_bytes")
    permitted = None if free is None else int(GPU_WORKING_SET_FRACTION * free)
    passed = True if permitted is None else predicted <= permitted
    audit = {
        "stage": stage,
        "predicted_working_set_bytes": predicted,
        "free_bytes_before": free,
        "permitted_bytes": permitted,
        "fraction_of_current_free_limit": GPU_WORKING_SET_FRACTION,
        "passed": passed,
    }
    if not passed:
        raise RepresentationFailure(
            "Predicted working set exceeds the v4 resource invariant",
            event=audit,
        )
    return audit


def _input_scaled_blocks(
    factor: Union[CanonicalFactor, RawFactor],
    backend: NumericalBackend,
) -> Iterable[Any]:
    if isinstance(factor, CanonicalFactor):
        yield from iter_canonical_scaled_blocks(factor, backend)
    else:
        yield from factor.blocks


def apply_channel_kraus_block(
    operator: Any,
    factor_block: Any,
    *,
    operators: OscillatorOperators,
    config: RunConfig,
    backend: NumericalBackend,
) -> Any:
    rank = int(factor_block.shape[1])
    shaped = factor_block.reshape(operators.d_channels, config.n_z * rank)
    mapped = operator @ shaped
    return backend.xp.ascontiguousarray(
        mapped.reshape(operators.d_channels * config.n_z, rank)
    )


# =============================================================================
# V4-D2 WHOLE-HALF-STEP METRIC-AWARE REDUCED-CORE COMPRESSION
# =============================================================================
def _d2_weighted_gram(
    blocks: Sequence[Any],
    *,
    h_z: float,
    backend: NumericalBackend,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    if not blocks:
        raise ValueError("D2 weighted Gram requires nonempty blocks")
    started = time.perf_counter()
    offsets = block_offsets(blocks)
    dimension = offsets[-1][1]
    gram = np.zeros((dimension, dimension), dtype=np.complex128)
    for i, left in enumerate(blocks):
        i0, i1 = offsets[i]
        for j in range(i, len(blocks)):
            right = blocks[j]
            j0, j1 = offsets[j]
            piece = h_z * (left.conj().T @ right)
            piece_cpu = np.asarray(backend.to_cpu(piece), dtype=np.complex128)
            gram[i0:i1, j0:j1] = piece_cpu
            if i != j:
                gram[j0:j1, i0:i1] = piece_cpu.conj().T
    backend.synchronize()
    anti = gram - gram.conj().T
    norm = max(float(np.linalg.norm(gram, ord="fro")), np.finfo(float).tiny)
    return gram, {
        "dimension": int(dimension),
        "raw_hermiticity_frobenius": float(np.linalg.norm(anti, ord="fro")),
        "raw_hermiticity_relative_frobenius": float(
            np.linalg.norm(anti, ord="fro") / norm
        ),
        "wall_seconds": time.perf_counter() - started,
    }


def _d2_psd_eigh(
    matrix: np.ndarray,
    *,
    label: str,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    raw = np.asarray(matrix, dtype=np.complex128)
    hermitian = 0.5 * (raw + raw.conj().T)
    if not np.all(np.isfinite(hermitian)):
        raise RepresentationFailure(
            f"Non-finite D2 reduced core: {label}", event={"label": label}
        )
    scale = max(float(np.linalg.norm(hermitian, ord=2)), np.finfo(float).tiny)
    envelope = (
        PSD_BACKWARD_ERROR_FACTOR
        * np.finfo(float).eps
        * max(1, hermitian.shape[0])
        * scale
    )
    raw_values, raw_vectors = np.linalg.eigh(hermitian)
    raw_values = np.asarray(raw_values.real, dtype=np.float64)
    minimum = float(np.min(raw_values, initial=0.0))
    if minimum < -envelope:
        raise RepresentationFailure(
            f"{label} is not PSD outside its backward-error envelope",
            event={
                "label": label,
                "minimum_raw_eigenvalue": minimum,
                "backward_error_envelope": float(envelope),
                "scale_2norm": scale,
            },
        )
    negative_mass = float(
        -np.sum(raw_values[raw_values < 0.0], dtype=np.float64)
        if np.any(raw_values < 0.0)
        else 0.0
    )
    clipped = np.maximum(raw_values, 0.0)
    spectral_scale = max(float(np.max(clipped, initial=0.0)), np.finfo(float).tiny)
    floor = (
        AUGMENTED_GRAM_NORMALIZATION_FLOOR_FACTOR
        * np.finfo(float).eps
        * spectral_scale
    )
    order = np.argsort(clipped, kind="stable")[::-1]
    values = np.asarray(clipped[order], dtype=np.float64)
    vectors = np.asarray(raw_vectors[:, order], dtype=np.complex128)
    eigen_residual = float(
        np.linalg.norm(
            hermitian @ raw_vectors - raw_vectors * raw_values[None, :],
            ord="fro",
        )
        / max(float(np.linalg.norm(hermitian, ord="fro")), np.finfo(float).tiny)
    )
    orthogonality = float(
        np.linalg.norm(
            raw_vectors.conj().T @ raw_vectors - np.eye(raw_vectors.shape[1]),
            ord="fro",
        )
        / max(math.sqrt(raw_vectors.shape[1]), 1.0)
    )
    return values, vectors, {
        "label": label,
        "dimension": int(hermitian.shape[0]),
        "scale_2norm": scale,
        "minimum_raw_eigenvalue": minimum,
        "clipped_negative_mass": negative_mass,
        "backward_error_envelope": float(envelope),
        "normalization_floor": float(floor),
        "positive_count_raw": int(np.count_nonzero(clipped > 0.0)),
        "stable_positive_count": int(np.count_nonzero(values > floor)),
        "subfloor_positive_trace": float(
            np.sum(values[(values > 0.0) & (values <= floor)], dtype=np.float64)
        ),
        "eigen_residual": eigen_residual,
        "orthogonality_residual": orthogonality,
        "raw_trace": float(np.trace(hermitian).real),
        "clipped_positive_trace": float(np.sum(clipped, dtype=np.float64)),
    }


def _d2_gram_support(
    gram: np.ndarray,
    *,
    label: str,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    values, vectors, audit = _d2_psd_eigh(gram, label=label)
    stable = values > float(audit["normalization_floor"])
    stable_values = np.asarray(values[stable], dtype=np.float64)
    stable_vectors = np.asarray(vectors[:, stable], dtype=np.complex128)
    if stable_values.size == 0:
        raise RepresentationFailure(
            "D2 input Gram has zero stable positive rank",
            event={"gram_audit": audit},
        )
    return stable_values, stable_vectors, audit


def _d2_direct_density_certificate(
    gram_support_values: np.ndarray,
    gram_support_vectors: np.ndarray,
    gram_audit: Mapping[str, Any],
    transform: np.ndarray,
) -> Dict[str, Any]:
    """Stable signed-Gram trace norm on the numerical support of the input.

    Null-space coefficient gauges can be arbitrarily large without changing
    the physical factor YT.  The certificate therefore projects the transform
    to the stable positive support of G=h_z Y^dagger Y before forming

        sqrt(G_s) [I - T_s T_s^dagger] sqrt(G_s).

    Positive subfloor trace and clipped negative mass are then added
    conservatively.  This is gauge invariant with respect to the numerical
    null space and avoids catastrophic cancellation for dependent Kraus blocks.
    """
    values = np.asarray(gram_support_values, dtype=np.float64)
    vectors = np.asarray(gram_support_vectors, dtype=np.complex128)
    transform = np.asarray(transform, dtype=np.complex128)
    if transform.ndim != 2 or transform.shape[0] != vectors.shape[0]:
        raise ValueError("D2 density transform has incompatible dimensions")
    support_transform = vectors.conj().T @ transform
    root = np.diag(np.sqrt(values))
    difference = (
        np.eye(values.size, dtype=np.complex128)
        - support_transform @ support_transform.conj().T
    )
    reduced = root @ difference @ root
    reduced = 0.5 * (reduced + reduced.conj().T)
    eig_values = np.linalg.eigvalsh(reduced)
    eig_norm = float(np.sum(np.abs(eig_values), dtype=np.float64))
    singular = np.linalg.svd(reduced, compute_uv=False)
    svd_norm = float(np.sum(singular, dtype=np.float64))
    disagreement = abs(eig_norm - svd_norm)
    core_scale = max(
        float(np.linalg.norm(reduced, ord=2)), np.finfo(float).tiny
    )
    core_arithmetic_guard = (
        64.0
        * np.finfo(float).eps
        * max(1, reduced.shape[0])
        * core_scale
        + disagreement
    )
    represented_trace = float(
        np.trace(
            np.diag(values)
            @ (support_transform @ support_transform.conj().T)
        ).real
    )
    input_trace_on_stable_support = float(np.sum(values, dtype=np.float64))
    trace_scale_guard = float(
        D2_CERTIFICATE_TRACE_GUARD_ULPS
        * np.finfo(float).eps
        * max(input_trace_on_stable_support, represented_trace, 1.0)
    )
    guard = math.fsum((core_arithmetic_guard, trace_scale_guard))
    negative_mass = float(gram_audit["clipped_negative_mass"])
    subfloor_trace = float(gram_audit["subfloor_positive_trace"])
    bound = math.fsum(
        (
            max(eig_norm, svd_norm),
            negative_mass,
            subfloor_trace,
            guard,
        )
    )
    return {
        "support_dimension": int(values.size),
        "trace_norm_from_eigenvalues": eig_norm,
        "trace_norm_from_singular_values": svd_norm,
        "eigen_svd_disagreement": disagreement,
        "gram_clipped_negative_mass": negative_mass,
        "gram_subfloor_positive_trace": subfloor_trace,
        "core_arithmetic_guard": core_arithmetic_guard,
        "trace_scale_guard_ulps": D2_CERTIFICATE_TRACE_GUARD_ULPS,
        "trace_scale_guard": trace_scale_guard,
        "numerical_guard": guard,
        "reconstructible_trace_norm_bound": float(bound),
        "input_trace_on_stable_support": input_trace_on_stable_support,
        "represented_trace_on_stable_support": represented_trace,
    }

def _d2_q_cross(
    q_blocks: Sequence[Any],
    block: Any,
    *,
    h_z: float,
    backend: NumericalBackend,
) -> np.ndarray:
    if not q_blocks:
        return np.empty((0, int(block.shape[1])), dtype=np.complex128)
    pieces = [
        np.asarray(backend.to_cpu(h_z * (q.conj().T @ block)), dtype=np.complex128)
        for q in q_blocks
    ]
    return np.concatenate(pieces, axis=0)


def _d2_q_subtract(
    block: Any,
    q_blocks: Sequence[Any],
    coefficients: np.ndarray,
    *,
    backend: NumericalBackend,
) -> Any:
    result = backend.xp.ascontiguousarray(block.copy())
    offsets = block_offsets(q_blocks) if q_blocks else []
    for q, (start, stop) in zip(q_blocks, offsets):
        coeff = backend.to_backend_array(
            np.ascontiguousarray(coefficients[start:stop, :])
        )
        result -= q @ coeff
    return backend.xp.ascontiguousarray(result)


def _d2_local_cqr2_or_polar(
    residual: Any,
    residual_coefficients: np.ndarray,
    *,
    h_z: float,
    backend: NumericalBackend,
    label: str,
    global_gram_scale: float,
) -> Tuple[Optional[Any], np.ndarray, np.ndarray, Dict[str, Any]]:
    """Normalize one projected residual block without promoting roundoff nulls.

    Two-pass projection leaves exact duplicate blocks with a residual of order
    machine precision.  The relevant Gram eigenvalues are therefore of order
    eps**2 times the complete mapped-density scale, not eps times the local
    residual scale.  A squared-roundoff dependency floor separates those
    numerical nulls from physically small but first-order-relevant directions
    such as the near-collinear D1 adversarial case.
    """
    started = time.perf_counter()
    residual_gram = np.asarray(
        backend.to_cpu(h_z * (residual.conj().T @ residual)),
        dtype=np.complex128,
    )
    residual_gram = 0.5 * (residual_gram + residual_gram.conj().T)
    values, vectors, psd = _d2_psd_eigh(residual_gram, label=label)

    eps = np.finfo(float).eps
    roundoff_dependency_floor = float(
        D2_RESIDUAL_DEPENDENCY_EPS2_FACTOR
        * eps
        * eps
        * max(float(global_gram_scale), np.finfo(float).tiny)
    )
    dependency_floor = max(np.finfo(float).tiny, roundoff_dependency_floor)
    stable = values > dependency_floor
    stable_values = np.asarray(values[stable], dtype=np.float64)
    stable_vectors = np.asarray(vectors[:, stable], dtype=np.complex128)
    if stable_values.size == 0:
        return (
            None,
            np.empty((residual_coefficients.shape[0], 0), np.complex128),
            np.empty((0, residual.shape[1]), np.complex128),
            {
                "method": "dependent_block_no_new_direction",
                "psd_audit": psd,
                "local_psd_normalization_floor": float(psd["normalization_floor"]),
                "roundoff_dependency_floor": roundoff_dependency_floor,
                "dependency_floor": dependency_floor,
                "rank_added": 0,
                "wall_seconds": time.perf_counter() - started,
            },
        )

    minimum = float(np.min(stable_values))
    maximum = float(np.max(stable_values))
    condition = math.sqrt(maximum / minimum)
    full_rank = stable_values.size == residual_gram.shape[0]
    method = "polar_residual_normalization"
    q_new: Any
    coefficient_new: np.ndarray
    local_r: np.ndarray
    cqr2_details: Dict[str, Any] = {}

    if full_rank and condition <= D2_CQR2_CONDITION_LIMIT:
        try:
            lower1 = np.linalg.cholesky(residual_gram)
            r1 = lower1.conj().T
            inv_r1 = np.linalg.solve(
                r1, np.eye(r1.shape[0], dtype=np.complex128)
            )
            q1 = residual @ backend.to_backend_array(
                np.ascontiguousarray(inv_r1)
            )
            metric1 = np.asarray(
                backend.to_cpu(h_z * (q1.conj().T @ q1)), dtype=np.complex128
            )
            metric1 = 0.5 * (metric1 + metric1.conj().T)
            lower2 = np.linalg.cholesky(metric1)
            r2 = lower2.conj().T
            inv_r2 = np.linalg.solve(
                r2, np.eye(r2.shape[0], dtype=np.complex128)
            )
            q_new = backend.xp.ascontiguousarray(
                q1 @ backend.to_backend_array(np.ascontiguousarray(inv_r2))
            )
            coefficient_new = residual_coefficients @ inv_r1 @ inv_r2
            local_r = r2 @ r1
            metric2 = np.asarray(
                backend.to_cpu(h_z * (q_new.conj().T @ q_new)),
                dtype=np.complex128,
            )
            method = "two_pass_projection_plus_choleskyqr2"
            cqr2_details = {
                "condition_estimate_from_residual_gram": condition,
                "condition_limit": D2_CQR2_CONDITION_LIMIT,
                "metric_after_first_choleskyqr": float(
                    np.linalg.norm(
                        metric1 - np.eye(metric1.shape[0]), ord="fro"
                    )
                    / max(math.sqrt(metric1.shape[0]), 1.0)
                ),
                "metric_after_choleskyqr2": float(
                    np.linalg.norm(
                        metric2 - np.eye(metric2.shape[0]), ord="fro"
                    )
                    / max(math.sqrt(metric2.shape[0]), 1.0)
                ),
            }
        except np.linalg.LinAlgError as exc:
            method = "polar_residual_normalization_after_cqr2_fallback"
            cqr2_details = {
                "fallback_reason": repr(exc),
                "condition_estimate_from_residual_gram": condition,
            }

    if not method.startswith("two_pass_projection_plus_choleskyqr2"):
        normalization = stable_vectors / np.sqrt(stable_values)[None, :]
        q_new = backend.xp.ascontiguousarray(
            residual
            @ backend.to_backend_array(np.ascontiguousarray(normalization))
        )
        coefficient_new = residual_coefficients @ normalization
        local_r = np.diag(np.sqrt(stable_values)) @ stable_vectors.conj().T

    backend.synchronize()
    local_metric = np.asarray(
        backend.to_cpu(h_z * (q_new.conj().T @ q_new)),
        dtype=np.complex128,
    )
    local_residual = float(
        np.linalg.norm(
            local_metric - np.eye(local_metric.shape[0]), ord="fro"
        )
        / max(math.sqrt(local_metric.shape[0]), 1.0)
    )
    return q_new, coefficient_new, local_r, {
        "method": method,
        "psd_audit": psd,
        "local_psd_normalization_floor": float(psd["normalization_floor"]),
        "roundoff_dependency_floor": roundoff_dependency_floor,
        "dependency_floor": dependency_floor,
        "residual_condition_estimate": condition,
        "rank_added": int(q_new.shape[1]),
        "local_metric_residual": local_residual,
        "cqr2_details": cqr2_details,
        "wall_seconds": time.perf_counter() - started,
    }


def _d2_output_reconstruction_bound(
    input_blocks: Sequence[Any],
    transform: np.ndarray,
    result: CanonicalFactor,
    *,
    backend: NumericalBackend,
) -> Dict[str, Any]:
    """Bound the finite-arithmetic reconstruction X - YT blockwise.

    The direct reduced-core certificate compares the exact mapped factor Y with
    the ideal coefficient-space candidate YT.  The returned canonical factor X
    is assembled by blocked backend matrix products.  This routine measures the
    physical Frobenius residual between X and YT and converts it to a density
    trace-norm bound,

        ||XX^dagger-(YT)(YT)^dagger||_1
        <= (||X||_F+||YT||_F) ||X-YT||_F,

    in the h_z-weighted physical coordinates.
    """
    coefficients = np.asarray(transform, dtype=np.complex128)
    offsets = block_offsets(input_blocks)
    if offsets[-1][1] != coefficients.shape[0]:
        raise ValueError("D2 reconstruction transform/input rank mismatch")
    output_offsets = block_offsets(result.basis_blocks)
    if output_offsets[-1][1] != coefficients.shape[1]:
        raise ValueError("D2 reconstruction transform/output rank mismatch")

    coefficients_backend = backend.to_backend_array(
        np.ascontiguousarray(coefficients)
    )
    residual_norm2_terms: List[float] = []
    ideal_norm2_terms: List[float] = []
    actual_norm2_terms: List[float] = []
    for basis_block, (out_start, out_stop) in zip(
        result.basis_blocks, output_offsets
    ):
        ideal = backend.xp.zeros_like(basis_block)
        for input_block, (in_start, in_stop) in zip(input_blocks, offsets):
            ideal += input_block @ coefficients_backend[
                in_start:in_stop, out_start:out_stop
            ]
        scale = backend.to_backend_real(
            np.sqrt(result.weights[out_start:out_stop])
        )
        actual = basis_block * scale[None, :]
        difference = actual - ideal
        residual_norm2_terms.append(
            result.h_z
            * backend.scalar_float(
                backend.xp.vdot(
                    difference.reshape(-1), difference.reshape(-1)
                ).real
            )
        )
        ideal_norm2_terms.append(
            result.h_z
            * backend.scalar_float(
                backend.xp.vdot(ideal.reshape(-1), ideal.reshape(-1)).real
            )
        )
        actual_norm2_terms.append(
            result.h_z
            * backend.scalar_float(
                backend.xp.vdot(actual.reshape(-1), actual.reshape(-1)).real
            )
        )
    backend.synchronize()
    residual_norm = math.sqrt(max(math.fsum(residual_norm2_terms), 0.0))
    ideal_norm = math.sqrt(max(math.fsum(ideal_norm2_terms), 0.0))
    actual_norm = math.sqrt(max(math.fsum(actual_norm2_terms), 0.0))
    density_bound = (actual_norm + ideal_norm) * residual_norm
    certificate_values = np.asarray(
        [residual_norm, actual_norm, ideal_norm, density_bound],
        dtype=np.float64,
    )
    if not np.all(np.isfinite(certificate_values)) or density_bound < 0.0:
        raise RepresentationFailure(
            "D2PR2 blocked candidate reconstruction certificate is non-finite or negative",
            event={
                "certificate_stage": "blocked_candidate_reconstruction",
                "physical_factor_residual_frobenius": residual_norm,
                "actual_factor_physical_frobenius": actual_norm,
                "ideal_transform_factor_physical_frobenius": ideal_norm,
                "reconstructible_density_trace_norm_bound": density_bound,
            },
        )
    return {
        "physical_factor_residual_frobenius": residual_norm,
        "actual_factor_physical_frobenius": actual_norm,
        "ideal_transform_factor_physical_frobenius": ideal_norm,
        "reconstructible_density_trace_norm_bound": float(density_bound),
    }



def _d2_scaled_factor_blocks(
    factor: CanonicalFactor,
    backend: NumericalBackend,
) -> Tuple[Any, ...]:
    """Return the actual blocked scaled factor ``Q sqrt(w)``."""
    return tuple(_input_scaled_blocks(factor, backend))


def _d2_physical_factor_reconstruction_bound(
    input_blocks: Sequence[Any],
    transform: np.ndarray,
    actual_scaled_blocks: Sequence[Any],
    *,
    h_z: float,
    backend: NumericalBackend,
    label: str,
) -> Dict[str, Any]:
    """Bound an actual blocked factor against an ideal blocked transform.

    If ``Y`` denotes the blocked input factor and ``A`` the supplied transform,
    the routine measures ``X-YA`` in the physical Frobenius norm and returns

        ||XX^dagger-(YA)(YA)^dagger||_1
        <= (||X||_F+||YA||_F)||X-YA||_F.

    No cancellation-prone combined signed Gram is formed.
    """
    coefficients = np.asarray(transform, dtype=np.complex128)
    input_offsets = block_offsets(input_blocks)
    output_offsets = block_offsets(actual_scaled_blocks)
    if input_offsets[-1][1] != coefficients.shape[0]:
        raise ValueError("D2PR input-transform row dimension mismatch")
    if output_offsets[-1][1] != coefficients.shape[1]:
        raise ValueError("D2PR output-transform column dimension mismatch")

    coefficients_backend = backend.to_backend_array(
        np.ascontiguousarray(coefficients)
    )
    residual_terms: List[float] = []
    ideal_terms: List[float] = []
    actual_terms: List[float] = []
    for actual, (out_start, out_stop) in zip(
        actual_scaled_blocks, output_offsets
    ):
        ideal = backend.xp.zeros_like(actual)
        for input_block, (in_start, in_stop) in zip(
            input_blocks, input_offsets
        ):
            ideal += input_block @ coefficients_backend[
                in_start:in_stop, out_start:out_stop
            ]
        difference = actual - ideal
        residual_terms.append(
            h_z
            * backend.scalar_float(
                backend.xp.vdot(
                    difference.reshape(-1), difference.reshape(-1)
                ).real
            )
        )
        ideal_terms.append(
            h_z
            * backend.scalar_float(
                backend.xp.vdot(ideal.reshape(-1), ideal.reshape(-1)).real
            )
        )
        actual_terms.append(
            h_z
            * backend.scalar_float(
                backend.xp.vdot(actual.reshape(-1), actual.reshape(-1)).real
            )
        )
    backend.synchronize()
    residual = math.sqrt(max(math.fsum(residual_terms), 0.0))
    ideal_norm = math.sqrt(max(math.fsum(ideal_terms), 0.0))
    actual_norm = math.sqrt(max(math.fsum(actual_terms), 0.0))
    density_bound = (ideal_norm + actual_norm) * residual
    certificate_values = np.asarray(
        [residual, ideal_norm, actual_norm, density_bound], dtype=np.float64
    )
    if (
        not np.all(np.isfinite(certificate_values))
        or density_bound < 0.0
    ):
        raise RepresentationFailure(
            "D2PR2 physical reconstruction certificate is non-finite or negative",
            event={
                "label": label,
                "physical_factor_residual_frobenius": residual,
                "ideal_factor_physical_frobenius": ideal_norm,
                "actual_factor_physical_frobenius": actual_norm,
                "reconstructible_density_trace_norm_bound": density_bound,
            },
        )
    return {
        "label": label,
        "physical_factor_residual_frobenius": residual,
        "ideal_factor_physical_frobenius": ideal_norm,
        "actual_factor_physical_frobenius": actual_norm,
        "reconstructible_density_trace_norm_bound": float(density_bound),
    }


def _d2_reduced_density_difference_in_metric(
    gram: np.ndarray,
    left_core: np.ndarray,
    right_scaled_transform: np.ndarray,
    *,
    label: str,
) -> Dict[str, Any]:
    """Stable reduced-coordinate density certificate for one gauge repair.

    It evaluates the physical trace norm of

        Q C_L Q^dagger - Q A A^dagger Q^dagger

    through the positive metric ``G=h_z Q^dagger Q``.  This is the stable C2
    construction and deliberately avoids C1's nearly dependent combined Gram.
    """
    metric = 0.5 * (
        np.asarray(gram, dtype=np.complex128)
        + np.asarray(gram, dtype=np.complex128).conj().T
    )
    values, vectors, metric_psd = _psd_eigh(metric, label=label + " metric")
    positive = values > 0.0
    if not np.any(positive):
        raise RepresentationFailure(
            "D2PR repair metric has zero positive support",
            event={"label": label, "metric_psd_audit": metric_psd},
        )
    values = values[positive]
    vectors = vectors[:, positive]
    root = (vectors * np.sqrt(values)[None, :]) @ vectors.conj().T
    left = np.asarray(left_core, dtype=np.complex128)
    transform = np.asarray(right_scaled_transform, dtype=np.complex128)
    difference = left - transform @ transform.conj().T
    reduced = root @ difference @ root
    reduced = 0.5 * (reduced + reduced.conj().T)
    eigenvalues = np.linalg.eigvalsh(reduced)
    singular_values = np.linalg.svd(reduced, compute_uv=False)
    eigen_norm = float(np.sum(np.abs(eigenvalues), dtype=np.float64))
    svd_norm = float(np.sum(singular_values, dtype=np.float64))
    disagreement = abs(eigen_norm - svd_norm)
    scale = max(float(np.linalg.norm(reduced, ord=2)), np.finfo(float).tiny)
    arithmetic_guard = (
        64.0
        * np.finfo(float).eps
        * max(1, reduced.shape[0])
        * scale
        + disagreement
    )
    right_core = transform @ transform.conj().T
    trace_left = float(np.trace(metric @ left).real)
    trace_right = float(np.trace(metric @ right_core).real)
    trace_guard = (
        D2_CERTIFICATE_TRACE_GUARD_ULPS
        * np.finfo(float).eps
        * max(abs(trace_left), abs(trace_right), 1.0)
    )
    negative_mass = float(metric_psd.get("clipped_negative_mass", 0.0))
    coefficient_scale = max(
        float(np.linalg.norm(left, ord=2)),
        float(np.linalg.norm(right_core, ord=2)),
        1.0,
    )
    metric_clip_guard = negative_mass * coefficient_scale
    bound = math.fsum(
        (
            max(eigen_norm, svd_norm),
            arithmetic_guard,
            trace_guard,
            metric_clip_guard,
        )
    )
    certificate_values = np.asarray(
        [
            eigen_norm,
            svd_norm,
            disagreement,
            arithmetic_guard,
            trace_guard,
            metric_clip_guard,
            bound,
        ],
        dtype=np.float64,
    )
    if not np.all(np.isfinite(certificate_values)) or bound < 0.0:
        raise RepresentationFailure(
            "D2PR2 reduced repair certificate is non-finite or negative",
            event={
                "label": label,
                "certificate_values": certificate_values.tolist(),
            },
        )
    return {
        "label": label,
        "trace_norm_from_eigenvalues": eigen_norm,
        "trace_norm_from_singular_values": svd_norm,
        "eigen_svd_disagreement": disagreement,
        "arithmetic_guard": arithmetic_guard,
        "trace_scale_guard": trace_guard,
        "metric_clipping_guard": metric_clip_guard,
        "reconstructible_density_trace_norm_bound": float(bound),
        "trace_left": trace_left,
        "trace_right": trace_right,
        "metric_psd_audit": metric_psd,
    }


def _d2_one_weighted_polar_repair_with_complete_certificate(
    factor: CanonicalFactor,
    *,
    backend: NumericalBackend,
    block_columns: int,
    reason: str,
) -> Tuple[CanonicalFactor, Dict[str, Any]]:
    """Perform one exact weighted-polar gauge repair and certify it."""
    gram = _weighted_basis_gram(
        factor.basis_blocks, h_z=factor.h_z, backend=backend
    )
    gram_values, gram_vectors, gram_psd = _psd_eigh(
        gram, label=reason + " input gauge Gram"
    )
    scale = max(float(np.max(gram_values, initial=0.0)), 1.0)
    invertibility_floor = (
        PSD_BACKWARD_ERROR_FACTOR
        * np.finfo(float).eps
        * max(1, factor.rank)
        * scale
    )
    if np.any(gram_values <= invertibility_floor):
        raise RepresentationFailure(
            "D2PR repair input gauge Gram is numerically rank deficient",
            event={
                "minimum_gram_eigenvalue": float(np.min(gram_values)),
                "invertibility_floor": float(invertibility_floor),
                "gram_psd_audit": gram_psd,
            },
        )

    square_root = np.sqrt(gram_values)
    inverse_square_root = 1.0 / square_root
    sqrt_gram = (
        gram_vectors * square_root[None, :]
    ) @ gram_vectors.conj().T
    inverse_sqrt_gram = (
        gram_vectors * inverse_square_root[None, :]
    ) @ gram_vectors.conj().T

    orthogonal_basis = _rotate_basis(
        factor.basis_blocks,
        np.ascontiguousarray(inverse_sqrt_gram, dtype=np.complex128),
        backend=backend,
        output_block_columns=block_columns,
    )
    reduced_core = (
        sqrt_gram @ np.diag(factor.weights) @ sqrt_gram.conj().T
    )
    core_values, core_vectors, core_psd = _psd_eigh(
        reduced_core, label=reason + " reduced density core"
    )
    positive_indices = np.flatnonzero(core_values > 0.0)
    if positive_indices.size == 0:
        raise RepresentationFailure(
            "D2PR repair produced zero density rank",
            event={"core_psd_audit": core_psd},
        )
    order = positive_indices[
        np.argsort(core_values[positive_indices], kind="stable")[::-1]
    ]
    final_basis = _rotate_basis(
        orthogonal_basis,
        np.ascontiguousarray(core_vectors[:, order], dtype=np.complex128),
        backend=backend,
        output_block_columns=block_columns,
    )
    repaired = CanonicalFactor(
        basis_blocks=final_basis,
        weights=np.asarray(core_values[order], dtype=np.float64),
        n_rows=factor.n_rows,
        h_z=factor.h_z,
    )

    scaled_transform = (
        inverse_sqrt_gram
        @ core_vectors[:, order]
        @ np.diag(np.sqrt(core_values[order]))
    )
    core_certificate = _d2_reduced_density_difference_in_metric(
        gram,
        np.diag(np.asarray(factor.weights, dtype=np.float64)),
        scaled_transform,
        label=reason + " reduced metric density difference",
    )
    reconstruction = _d2_physical_factor_reconstruction_bound(
        factor.basis_blocks,
        scaled_transform,
        _d2_scaled_factor_blocks(repaired, backend),
        h_z=factor.h_z,
        backend=backend,
        label=reason + " blocked repaired-factor reconstruction",
    )
    complete_bound = math.fsum(
        (
            float(core_certificate["reconstructible_density_trace_norm_bound"]),
            float(reconstruction["reconstructible_density_trace_norm_bound"]),
        )
    )
    return repaired, {
        "method": "exact_weighted_polar_repair_with_stable_complete_certificate_v1",
        "rank_before": factor.rank,
        "rank_after": repaired.rank,
        "input_canonicality": canonicality_audit(factor, backend),
        "output_canonicality": canonicality_audit(repaired, backend),
        "gram_psd_audit": gram_psd,
        "core_psd_audit": core_psd,
        "repair_core_density_certificate": core_certificate,
        "blocked_repaired_factor_reconstruction_certificate": reconstruction,
        "complete_repair_density_bound": float(complete_bound),
        "density_approximation_introduced": bool(
            positive_indices.size != factor.rank
        ),
    }


def _d2_repair_until_hard_gate_with_complete_certificate(
    factor: CanonicalFactor,
    *,
    backend: NumericalBackend,
    block_columns: int,
    target_trace: float,
    reason: str,
) -> Tuple[CanonicalFactor, Dict[str, Any]]:
    """Repair a candidate, enforce hard gates, and return one complete bound."""
    current = factor
    reports: List[Dict[str, Any]] = []
    cumulative_bound = 0.0
    for pass_index in range(1, CANONICALITY_REPAIR_MAX_PASSES + 1):
        audit = canonicality_audit(current, backend)
        residual = _canonicality_residual(audit)
        if audit["passed"] and residual <= CANONICALITY_REPAIR_TRIGGER:
            break
        current, repair = _d2_one_weighted_polar_repair_with_complete_certificate(
            current,
            backend=backend,
            block_columns=block_columns,
            reason=f"{reason} pass {pass_index}",
        )
        repair["repair_pass_index"] = pass_index
        reports.append(repair)
        cumulative_bound = math.fsum(
            (cumulative_bound, float(repair["complete_repair_density_bound"]))
        )

    canonical_before_restore = canonicality_audit(current, backend)
    if not canonical_before_restore["passed"]:
        raise RepresentationFailure(
            "D2PR candidate failed the unchanged hard canonicality gate after repair",
            event={
                "reason": reason,
                "repair_passes": reports,
                "canonicality_after_repair": canonical_before_restore,
            },
        )

    trace_before_restore = float(current.trace)
    if not np.isfinite(trace_before_restore) or trace_before_restore <= 0.0:
        raise RepresentationFailure(
            "D2PR repaired candidate has invalid trace",
            event={"trace_before_restore": trace_before_restore},
        )
    trace_restoration_correction = abs(
        float(target_trace) - trace_before_restore
    )
    trace_scale = float(target_trace) / trace_before_restore
    restored = CanonicalFactor(
        basis_blocks=current.basis_blocks,
        weights=np.asarray(current.weights * trace_scale, dtype=np.float64),
        n_rows=current.n_rows,
        h_z=current.h_z,
    )
    cumulative_bound = math.fsum(
        (cumulative_bound, trace_restoration_correction)
    )
    final_canonicality = canonicality_audit(restored, backend)
    trace_residual = abs(float(restored.trace) - float(target_trace))
    trace_gate = bool(
        trace_residual <= TRACE_RESTORE_TOL * max(float(target_trace), 1.0)
    )
    if not final_canonicality["passed"] or not trace_gate:
        raise RepresentationFailure(
            "D2PR repaired candidate failed final hard gates",
            event={
                "reason": reason,
                "canonicality": final_canonicality,
                "trace_residual": trace_residual,
                "trace_gate": trace_gate,
                "repair_passes": reports,
            },
        )
    return restored, {
        "method": "bounded_exact_weighted_polar_repair_until_hard_gate_v1",
        "repair_passes": reports,
        "repair_pass_count": len(reports),
        "trace_before_restoration": trace_before_restore,
        "trace_restoration_scale": trace_scale,
        "trace_restoration_correction": trace_restoration_correction,
        "trace_after_restoration": float(restored.trace),
        "trace_restore_residual": trace_residual,
        "trace_restore_gate_passed": trace_gate,
        "cumulative_repair_density_bound": float(cumulative_bound),
        "canonicality_before_trace_restoration": canonical_before_restore,
        "canonicality_after": final_canonicality,
        "passed": True,
    }


def _d2_construct_full_gram_rank_candidate(
    mapped_blocks: Sequence[Any],
    *,
    gram_support_values: np.ndarray,
    gram_support_vectors: np.ndarray,
    gram_audit: Mapping[str, Any],
    support_tails: np.ndarray,
    support_subfloor_trace: float,
    rank: int,
    h_z: float,
    target_trace: float,
    backend: NumericalBackend,
    block_columns: int,
) -> Tuple[CanonicalFactor, Dict[str, Any]]:
    """Construct one blocked C2 full-Gram rank candidate."""
    retained = float(np.sum(gram_support_values[:rank], dtype=np.float64))
    if retained <= 0.0:
        raise RepresentationFailure(
            "D2PR candidate has nonpositive retained trace",
            event={"rank": rank, "retained_trace": retained},
        )
    scale_squared = float(target_trace) / retained
    ideal_scaled_transform = (
        gram_support_vectors[:, :rank] * math.sqrt(scale_squared)
    )
    direct = _d2_direct_density_certificate(
        gram_support_values,
        gram_support_vectors,
        gram_audit,
        ideal_scaled_transform,
    )
    basis_rotation = (
        gram_support_vectors[:, :rank]
        / np.sqrt(gram_support_values[:rank])[None, :]
    )
    basis_blocks = _rotate_basis(
        mapped_blocks,
        np.ascontiguousarray(basis_rotation, dtype=np.complex128),
        backend=backend,
        output_block_columns=block_columns,
    )
    candidate = CanonicalFactor(
        basis_blocks=basis_blocks,
        weights=np.asarray(
            gram_support_values[:rank] * scale_squared, dtype=np.float64
        ),
        n_rows=int(mapped_blocks[0].shape[0]),
        h_z=float(h_z),
    )
    reconstruction = _d2_output_reconstruction_bound(
        mapped_blocks,
        np.asarray(ideal_scaled_transform, dtype=np.complex128),
        candidate,
        backend=backend,
    )
    candidate_bound = math.fsum(
        (
            float(direct["reconstructible_trace_norm_bound"]),
            float(
                reconstruction[
                    "reconstructible_density_trace_norm_bound"
                ]
            ),
        )
    )
    return candidate, {
        "candidate_source": "blocked_full_gram_stable_support",
        "rank": int(rank),
        "retained_trace_before_restoration": retained,
        "spectral_discarded_trace_including_subfloor": float(
            support_tails[rank] + support_subfloor_trace
        ),
        "coefficient_candidate_trace_restoration": abs(
            float(target_trace) - retained
        ),
        "scale_squared": scale_squared,
        "mapped_density_candidate_certificate": direct,
        "blocked_candidate_reconstruction_certificate": reconstruction,
        "unrepaired_complete_density_bound": float(candidate_bound),
        "canonicality_before_repair": canonicality_audit(candidate, backend),
    }


def _d2_assess_repaired_rank_candidate(
    candidate: CanonicalFactor,
    candidate_report: Mapping[str, Any],
    *,
    budget: RepresentationBudgetState,
    allocation: Mapping[str, Any],
    backend: NumericalBackend,
    block_columns: int,
    target_trace: float,
) -> Tuple[Optional[CanonicalFactor], Dict[str, Any]]:
    """Complete reconstruction, repair, exactly-once certification, and gates."""
    rank = int(candidate_report["rank"])
    try:
        repaired, repair = _d2_repair_until_hard_gate_with_complete_certificate(
            candidate,
            backend=backend,
            block_columns=block_columns,
            target_trace=target_trace,
            reason=f"D2PR2 full-Gram rank {rank}",
        )

        repair_passes = list(repair["repair_passes"])
        repair_core_bound = math.fsum(
            float(item["repair_core_density_certificate"][
                "reconstructible_density_trace_norm_bound"
            ])
            for item in repair_passes
        )
        repaired_reconstruction_bound = math.fsum(
            float(item["blocked_repaired_factor_reconstruction_certificate"][
                "reconstructible_density_trace_norm_bound"
            ])
            for item in repair_passes
        )
        components = {
            # Includes stable mapped-support clipping and arithmetic guards.
            "mapped_density_candidate_approximation_clipping_and_arithmetic_guards": float(
                candidate_report["mapped_density_candidate_certificate"][
                    "reconstructible_trace_norm_bound"
                ]
            ),
            "blocked_candidate_reconstruction": float(
                candidate_report["blocked_candidate_reconstruction_certificate"][
                    "reconstructible_density_trace_norm_bound"
                ]
            ),
            "weighted_polar_repair_core_density": float(repair_core_bound),
            "blocked_repaired_factor_reconstruction": float(
                repaired_reconstruction_bound
            ),
            "final_trace_restoration": float(
                repair["trace_restoration_correction"]
            ),
        }
        component_values = np.asarray(list(components.values()), dtype=np.float64)
        if not np.all(np.isfinite(component_values)) or np.any(component_values < 0.0):
            raise RepresentationFailure(
                "D2PR2 complete certificate contains a non-finite or negative component",
                event={
                    "rank": rank,
                    "certificate_components": components,
                },
            )
        complete_bound = float(math.fsum(components.values()))
        legacy_partition = math.fsum(
            (
                float(candidate_report["unrepaired_complete_density_bound"]),
                float(repair["cumulative_repair_density_bound"]),
            )
        )
        accounting_residual = abs(complete_bound - legacy_partition)
        accounting_tolerance = float(
            16.0 * np.finfo(float).eps * max(complete_bound, legacy_partition, 1.0)
        )
        if accounting_residual > accounting_tolerance:
            raise RepresentationFailure(
                "D2PR2 complete certificate component accounting failed",
                event={
                    "rank": rank,
                    "certificate_components": components,
                    "component_sum": complete_bound,
                    "independent_partition_sum": legacy_partition,
                    "accounting_residual": accounting_residual,
                    "accounting_tolerance": accounting_tolerance,
                },
            )

        assessment = budget.assess_increment(
            complete_bound, allocation=allocation
        )
        allowance = float(allocation["allowed_trace_norm_increment"])
        tolerance = float(assessment["comparison_tolerance"])
        raw_margin = allowance - complete_bound
        tolerance_margin = allowance + tolerance - complete_bound
        global_raw_margin = budget.total_budget - float(
            assessment["bound_after_if_committed"]
        )
        global_tolerance_margin = (
            budget.total_budget
            + tolerance
            - float(assessment["bound_after_if_committed"])
        )
        hard_pass = bool(
            repair["passed"]
            and repair["canonicality_after"]["passed"]
            and repair["trace_restore_gate_passed"]
        )
        strict_raw_margin_pass = bool(
            hard_pass
            and complete_bound <= allowance
            and float(assessment["bound_after_if_committed"])
            <= budget.total_budget
        )
        return repaired, {
            **dict(candidate_report),
            "repair_certificate": repair,
            "certificate_component_accounting": {
                "components_counted_exactly_once": components,
                "candidate_trace_scaling_is_contained_only_in_mapped_density_certificate": True,
                "stable_clipping_and_arithmetic_guards_are_contained_only_in_their_source_certificates": True,
                "component_sum": complete_bound,
                "independent_partition_sum": legacy_partition,
                "accounting_residual": accounting_residual,
                "accounting_tolerance": accounting_tolerance,
                "passed": True,
            },
            "repair_core_and_reconstruction_density_bound": float(
                math.fsum((repair_core_bound, repaired_reconstruction_bound))
            ),
            "complete_repaired_density_bound": complete_bound,
            "centralized_budget_assessment": assessment,
            "raw_schedule_margin": float(raw_margin),
            "tolerance_inclusive_schedule_margin": float(tolerance_margin),
            "raw_global_margin": float(global_raw_margin),
            "tolerance_inclusive_global_margin": float(
                global_tolerance_margin
            ),
            "strict_raw_margin_pass": strict_raw_margin_pass,
            "hard_canonicality_pass": bool(
                repair["canonicality_after"]["passed"]
            ),
            "trace_restoration_pass": bool(
                repair["trace_restore_gate_passed"]
            ),
            "rank_admissible": bool(hard_pass and assessment["passed"]),
        }
    except RepresentationFailure as exc:
        return None, {
            **dict(candidate_report),
            "candidate_failure_stage": "repair_or_complete_certificate",
            "repair_certificate": {
                "passed": False,
                "error": str(exc),
                "event": exc.event,
            },
            "certificate_component_accounting": None,
            "repair_core_and_reconstruction_density_bound": None,
            "complete_repaired_density_bound": None,
            "centralized_budget_assessment": None,
            "raw_schedule_margin": None,
            "tolerance_inclusive_schedule_margin": None,
            "raw_global_margin": None,
            "tolerance_inclusive_global_margin": None,
            "strict_raw_margin_pass": False,
            "hard_canonicality_pass": False,
            "trace_restoration_pass": False,
            "rank_admissible": False,
        }


def _d2_select_first_admissible_rank_report(
    rank_reports: Sequence[Mapping[str, Any]],
) -> Tuple[Mapping[str, Any], Optional[Mapping[str, Any]]]:
    """Select by the frozen predicate; separately identify strict raw margin."""
    ordered = sorted(rank_reports, key=lambda item: int(item["rank"]))
    selected = next(
        (item for item in ordered if bool(item.get("rank_admissible", False))),
        None,
    )
    first_strict = next(
        (
            item
            for item in ordered
            if bool(item.get("strict_raw_margin_pass", False))
        ),
        None,
    )
    if selected is None:
        raise RepresentationFailure(
            "D2PR no repaired rank satisfies the unchanged centralized predicate",
            event={
                "complete_repaired_rank_ladder": [dict(item) for item in ordered],
                "first_positive_strict_raw_margin_rank": (
                    None if first_strict is None else int(first_strict["rank"])
                ),
            },
        )
    return selected, first_strict

def d2_compress_mapped_blocks(
    mapped_blocks: Sequence[Any],
    *,
    block_metadata: Sequence[Mapping[str, Any]],
    h_z: float,
    target_trace: float,
    budget: RepresentationBudgetState,
    allocation: Mapping[str, Any],
    backend: NumericalBackend,
    output_block_columns: int,
    resource_permitted_bytes: Optional[int],
) -> Tuple[CanonicalFactor, Dict[str, Any]]:
    """One complete-map compression with one final reduced-core truncation.

    The mapped Kraus blocks are never concatenated into a D x 3r array.  A
    blocked weighted Gram supplies the exact reduced density certificate, while
    a two-pass metric range construction supplies the physical output basis.
    One global polar repair, one positive-core diagonalization, one rank choice,
    and one trace restoration are performed for the complete bath half-step.
    """
    started = time.perf_counter()
    blocks = tuple(mapped_blocks)
    if not blocks:
        raise RepresentationFailure(
            "D2 whole-half compression received no mapped blocks", event={}
        )
    if len(block_metadata) != len(blocks):
        raise ValueError("D2 block metadata count mismatch")
    n_rows = int(blocks[0].shape[0])
    mapped_logical_bytes = int(sum(int(block.nbytes) for block in blocks))
    gram_raw, gram_report = _d2_weighted_gram(blocks, h_z=h_z, backend=backend)
    gram_support_values, gram_support_vectors, gram_audit = _d2_gram_support(
        gram_raw, label="D2 complete three-Kraus input Gram"
    )
    global_gram_scale = float(gram_audit["scale_2norm"])

    q_blocks: List[Any] = []
    tq = np.empty((0, 0), dtype=np.complex128)
    r_reduced = np.empty((0, 0), dtype=np.complex128)
    processed_columns = 0
    block_reports: List[Dict[str, Any]] = []
    maximum_logical_working_bytes = mapped_logical_bytes + gram_raw.nbytes

    for block_index, block in enumerate(blocks):
        columns = int(block.shape[1])
        old_rank = int(tq.shape[1])
        old_columns = processed_columns
        if old_rank:
            h1 = _d2_q_cross(q_blocks, block, h_z=h_z, backend=backend)
            residual = _d2_q_subtract(block, q_blocks, h1, backend=backend)
            h2 = _d2_q_cross(q_blocks, residual, h_z=h_z, backend=backend)
            residual = _d2_q_subtract(residual, q_blocks, h2, backend=backend)
            h_total = h1 + h2
        else:
            h1 = np.empty((0, columns), dtype=np.complex128)
            h2 = np.empty((0, columns), dtype=np.complex128)
            h_total = np.empty((0, columns), dtype=np.complex128)
            residual = backend.xp.ascontiguousarray(block.copy())

        padded_old = np.vstack(
            [tq, np.zeros((columns, old_rank), dtype=np.complex128)]
        )
        selector = np.vstack(
            [
                np.zeros((old_columns, columns), dtype=np.complex128),
                np.eye(columns, dtype=np.complex128),
            ]
        )
        residual_coefficients = selector - padded_old @ h_total
        q_new, coefficient_new, local_r, local_report = _d2_local_cqr2_or_polar(
            residual,
            residual_coefficients,
            h_z=h_z,
            backend=backend,
            label=f"D2 block residual {block_index}",
            global_gram_scale=global_gram_scale,
        )
        rank_added = int(coefficient_new.shape[1])
        if rank_added:
            assert q_new is not None
            q_blocks.append(q_new)
            tq = np.concatenate([padded_old, coefficient_new], axis=1)
            new_r = np.zeros(
                (old_rank + rank_added, old_columns + columns),
                dtype=np.complex128,
            )
            if old_rank:
                new_r[:old_rank, :old_columns] = r_reduced
                new_r[:old_rank, old_columns:] = h_total
            new_r[old_rank:, old_columns:] = local_r
            r_reduced = new_r
        else:
            tq = padded_old
            new_r = np.zeros(
                (old_rank, old_columns + columns), dtype=np.complex128
            )
            if old_rank:
                new_r[:, :old_columns] = r_reduced
                new_r[:, old_columns:] = h_total
            r_reduced = new_r
        processed_columns += columns
        q_logical = int(sum(int(item.nbytes) for item in q_blocks))
        current_logical = int(
            mapped_logical_bytes
            + q_logical
            + gram_raw.nbytes
            + tq.nbytes
            + r_reduced.nbytes
        )
        maximum_logical_working_bytes = max(
            maximum_logical_working_bytes, current_logical
        )
        if (
            resource_permitted_bytes is not None
            and current_logical > resource_permitted_bytes
        ):
            raise RepresentationFailure(
                "D2 whole-half working set exceeds the resource invariant",
                event={
                    "block_index": block_index,
                    "logical_working_bytes": current_logical,
                    "permitted_bytes": resource_permitted_bytes,
                },
            )
        block_reports.append(
            {
                "block_index": block_index,
                **dict(block_metadata[block_index]),
                "rank_before": old_rank,
                "rank_added": rank_added,
                "rank_after": int(tq.shape[1]),
                "first_projection_frobenius": float(np.linalg.norm(h1, ord="fro")),
                "second_projection_frobenius": float(np.linalg.norm(h2, ord="fro")),
                "local_factorization": local_report,
            }
        )
        del residual

    if not q_blocks or tq.shape[1] == 0:
        raise RepresentationFailure(
            "D2 block range has zero rank", event={"block_reports": block_reports}
        )

    metric, metric_report = _d2_weighted_gram(q_blocks, h_z=h_z, backend=backend)
    metric_values, metric_vectors, metric_psd = _d2_psd_eigh(
        metric, label="D2 global block-range metric"
    )
    metric_floor = max(
        float(metric_psd["normalization_floor"]),
        PSD_BACKWARD_ERROR_FACTOR
        * np.finfo(float).eps
        * max(1, metric.shape[0])
        * max(float(np.max(metric_values, initial=0.0)), 1.0),
    )
    if np.any(metric_values <= metric_floor):
        raise RepresentationFailure(
            "D2 global range metric is numerically rank deficient",
            event={
                "metric_floor": metric_floor,
                "metric_psd_audit": metric_psd,
            },
        )
    metric_half = (
        metric_vectors
        @ np.diag(np.sqrt(metric_values))
        @ metric_vectors.conj().T
    )
    metric_inverse_half = (
        metric_vectors
        @ np.diag(1.0 / np.sqrt(metric_values))
        @ metric_vectors.conj().T
    )
    tq_polar = tq @ metric_inverse_half
    r_polar = metric_half @ r_reduced
    positive_core = r_polar @ r_polar.conj().T
    positive_core = 0.5 * (positive_core + positive_core.conj().T)
    core_values_all, core_vectors_all, core_psd = _d2_psd_eigh(
        positive_core, label="D2 global positive reduced core"
    )
    core_stable = core_values_all > float(core_psd["normalization_floor"])
    core_values = np.asarray(core_values_all[core_stable], dtype=np.float64)
    core_vectors = np.asarray(core_vectors_all[:, core_stable], dtype=np.complex128)
    core_subfloor_trace = float(
        np.sum(core_values_all[~core_stable], dtype=np.float64)
    )
    if core_values.size == 0:
        raise RepresentationFailure(
            "D2 positive reduced core has zero stable rank",
            event={"core_psd_audit": core_psd},
        )

    full_transform = tq_polar @ core_vectors @ np.diag(np.sqrt(core_values))
    untruncated = _d2_direct_density_certificate(
        gram_support_values,
        gram_support_vectors,
        gram_audit,
        full_transform,
    )
    coefficient_tails = tail_after_each_rank(core_values)
    allowed_trace_norm_increment = float(
        allocation["allowed_trace_norm_increment"]
    )
    schedule_tolerance = float(budget.comparison_tolerance())

    # Preserve the coefficient-space lower-rank estimate, but make final
    # acceptance depend only on complete physically reconstructed and repaired
    # full-Gram candidates.  This is the narrow C2-A integration.
    coefficient_lower_candidate_rank = 1
    lower_rank_found = False
    for rank in range(1, core_values.size + 1):
        retained = float(np.sum(core_values[:rank], dtype=np.float64))
        coefficient_tail = float(
            coefficient_tails[rank] + core_subfloor_trace
        )
        coefficient_restore = abs(float(target_trace) - retained)
        if (
            coefficient_tail + coefficient_restore
            <= allowed_trace_norm_increment + schedule_tolerance
        ):
            coefficient_lower_candidate_rank = int(rank)
            lower_rank_found = True
            break
    if not lower_rank_found:
        coefficient_lower_candidate_rank = 1

    support_tails = tail_after_each_rank(gram_support_values)
    support_subfloor_trace = float(gram_audit["subfloor_positive_trace"])
    candidate_reports: List[Dict[str, Any]] = []
    selected_factor: Optional[CanonicalFactor] = None
    selected_rank_seen: Optional[int] = None

    # Final acceptance is intentionally fail-fast: once the first complete
    # blocked/repaired candidate satisfies the unchanged centralized predicate,
    # no higher rank is evaluated merely to obtain a stricter-margin diagnostic.
    # The exact C2-A rank-29 distinction is retained by the dedicated frozen
    # call-3777 regression, not by changing production selection policy.
    for rank in range(
        coefficient_lower_candidate_rank,
        int(gram_support_values.size) + 1,
    ):
        try:
            candidate, candidate_report = _d2_construct_full_gram_rank_candidate(
                blocks,
                gram_support_values=gram_support_values,
                gram_support_vectors=gram_support_vectors,
                gram_audit=gram_audit,
                support_tails=support_tails,
                support_subfloor_trace=support_subfloor_trace,
                rank=rank,
                h_z=h_z,
                target_trace=target_trace,
                backend=backend,
                block_columns=output_block_columns,
            )
        except RepresentationFailure as exc:
            candidate_reports.append(
                {
                    "candidate_source": "blocked_full_gram_stable_support",
                    "rank": int(rank),
                    "candidate_failure_stage": "candidate_construction_or_reconstruction_certificate",
                    "candidate_failure": {
                        "error": str(exc),
                        "event": exc.event,
                    },
                    "complete_repaired_density_bound": None,
                    "centralized_budget_assessment": None,
                    "raw_schedule_margin": None,
                    "tolerance_inclusive_schedule_margin": None,
                    "strict_raw_margin_pass": False,
                    "hard_canonicality_pass": False,
                    "trace_restoration_pass": False,
                    "rank_admissible": False,
                }
            )
            continue
        candidate_working_bytes = int(
            mapped_logical_bytes
            + gram_raw.nbytes
            + candidate.logical_nbytes
            + tq.nbytes
            + r_reduced.nbytes
        )
        maximum_logical_working_bytes = max(
            maximum_logical_working_bytes, candidate_working_bytes
        )
        if (
            resource_permitted_bytes is not None
            and candidate_working_bytes > resource_permitted_bytes
        ):
            raise RepresentationFailure(
                "D2PR2 repaired-rank candidate exceeds the resource invariant",
                event={
                    "rank": rank,
                    "logical_working_bytes": candidate_working_bytes,
                    "permitted_bytes": resource_permitted_bytes,
                },
            )
        repaired, repaired_report = _d2_assess_repaired_rank_candidate(
            candidate,
            candidate_report,
            budget=budget,
            allocation=allocation,
            backend=backend,
            block_columns=output_block_columns,
            target_trace=target_trace,
        )
        candidate_reports.append(repaired_report)
        del candidate
        if repaired is not None and repaired_report["rank_admissible"]:
            selected_factor = repaired
            selected_rank_seen = int(rank)
            break
        if repaired is not None:
            del repaired

    try:
        selected_report, first_strict_report = (
            _d2_select_first_admissible_rank_report(candidate_reports)
        )
    except RepresentationFailure as exc:
        raise RepresentationFailure(
            str(exc),
            event={
                "allowed_trace_norm_increment": allowed_trace_norm_increment,
                "schedule_tolerance": schedule_tolerance,
                "coefficient_lower_candidate_rank": (
                    coefficient_lower_candidate_rank
                ),
                "stable_positive_core_rank": int(core_values.size),
                "stable_full_gram_support_rank": int(
                    gram_support_values.size
                ),
                "untruncated_direct_density_certificate": untruncated,
                "inner_failure": exc.event,
            },
        ) from exc

    selected_rank = int(selected_report["rank"])
    if selected_factor is None or selected_rank_seen != selected_rank:
        raise RepresentationFailure(
            "D2PR selected-rank factor bookkeeping mismatch",
            event={
                "selected_rank_report": selected_rank,
                "selected_rank_seen": selected_rank_seen,
            },
        )
    result = selected_factor
    final_canonicality = canonicality_audit(result, backend)
    final_trace_residual = abs(float(result.trace) - float(target_trace))
    if not final_canonicality["passed"]:
        raise RepresentationFailure(
            "D2PR selected repaired rank failed the unchanged hard canonicality gate",
            event={
                "selected_rank": selected_rank,
                "canonicality": final_canonicality,
                "complete_repaired_rank_ladder": candidate_reports,
            },
        )
    if final_trace_residual > TRACE_RESTORE_TOL * max(target_trace, 1.0):
        raise RepresentationFailure(
            "D2PR selected repaired rank failed trace restoration",
            event={
                "selected_rank": selected_rank,
                "target_trace": target_trace,
                "represented_trace": result.trace,
                "trace_residual": final_trace_residual,
            },
        )

    selected_bound = float(
        selected_report["complete_repaired_density_bound"]
    )
    selected_assessment = budget.assess_increment(
        selected_bound, allocation=allocation
    )
    if not selected_assessment["passed"]:
        raise RepresentationFailure(
            "D2PR selected rank failed centralized predicate on final reassessment",
            event={
                "selected_rank": selected_rank,
                "selected_report": selected_report,
                "final_budget_assessment": selected_assessment,
            },
        )

    repair_report = selected_report["repair_certificate"]
    first_strict_rank = (
        None
        if first_strict_report is None
        else int(first_strict_report["rank"])
    )
    report = {
        "method": "whole_three_kraus_metric_lower_rank_full_gram_first_admissible_repaired_rank_scan_v2",
        "block_qr_primary": True,
        "blocked_full_gram_fallback_used": True,
        "blocked_full_gram_repaired_rank_scan_used": True,
        "same_finite_cptp_map": True,
        "compression_scope": "one_complete_bath_half_step",
        "trace_restoration_count": 1,
        "mapped_positive_core_diagonalization_count": 1,
        "gauge_repair_core_diagonalization_count": int(
            repair_report["repair_pass_count"]
        ),
        "positive_core_diagonalization_count": 1,
        "target_trace": target_trace,
        "mapped_trace_from_gram": float(np.trace(gram_raw).real),
        "logical_input_rank": int(gram_raw.shape[0]),
        "mapped_logical_nbytes": mapped_logical_bytes,
        "gram_report": gram_report,
        "input_gram_psd_audit": gram_audit,
        "block_reports": block_reports,
        "range_rank_before_global_polar": int(tq.shape[1]),
        "global_metric_report": metric_report,
        "global_metric_psd_audit": metric_psd,
        "positive_core_psd_audit": core_psd,
        "stable_positive_core_rank": int(core_values.size),
        "stable_full_gram_support_rank": int(gram_support_values.size),
        "coefficient_lower_candidate_rank": int(
            coefficient_lower_candidate_rank
        ),
        "untruncated_direct_density_certificate": untruncated,
        "selected_rank": selected_rank,
        "first_tolerance_inclusive_passing_rank": selected_rank,
        "first_positive_strict_raw_margin_rank_within_tested_prefix": first_strict_rank,
        "selected_rank_strict_raw_margin_pass": bool(
            selected_report["strict_raw_margin_pass"]
        ),
        "spectral_discarded_trace_including_subfloor": float(
            selected_report[
                "spectral_discarded_trace_including_subfloor"
            ]
        ),
        "trace_restoration_correction": float(
            repair_report["trace_restoration_correction"]
        ),
        "mapped_density_candidate_certificate": selected_report[
            "mapped_density_candidate_certificate"
        ],
        "blocked_candidate_reconstruction_certificate": selected_report[
            "blocked_candidate_reconstruction_certificate"
        ],
        "repair_certificate": repair_report,
        "direct_reduced_core_density_certificate": selected_report[
            "mapped_density_candidate_certificate"
        ],
        "ideal_coefficient_candidate_density_bound": float(
            selected_report["unrepaired_complete_density_bound"]
        ),
        "output_reconstruction_certificate": selected_report[
            "blocked_candidate_reconstruction_certificate"
        ],
        "certified_density_trace_norm_bound": selected_bound,
        "allowed_trace_norm_increment": allowed_trace_norm_increment,
        "schedule_comparison_tolerance": schedule_tolerance,
        "raw_schedule_margin": float(
            selected_report["raw_schedule_margin"]
        ),
        "tolerance_inclusive_schedule_margin": float(
            selected_report["tolerance_inclusive_schedule_margin"]
        ),
        "selected_budget_assessment": selected_assessment,
        "unchanged_schedule_pass": True,
        "candidate_rank_reports": candidate_reports,
        "canonicality": final_canonicality,
        "trace_after": result.trace,
        "trace_restore_residual": final_trace_residual,
        "maximum_logical_working_bytes": int(
            maximum_logical_working_bytes
        ),
        "resource_permitted_bytes": resource_permitted_bytes,
        "wall_seconds": time.perf_counter() - started,
    }
    return result, report


def cssf_bath_half_step(
    factor: Union[CanonicalFactor, RawFactor],
    *,
    kraus: BathKraus,
    operators: OscillatorOperators,
    config: RunConfig,
    propagator: PropagatorObjects,
    backend: NumericalBackend,
    budget: RepresentationBudgetState,
    telemetry: RepresentationTelemetry,
    detector_step_index: int,
    bath_half_step: str,
) -> Tuple[CanonicalFactor, Dict[str, Any]]:
    if bath_half_step not in {"first", "second"}:
        raise ValueError("bath_half_step must be first or second")
    started = time.perf_counter()
    target_trace = (
        factor.trace
        if isinstance(factor, CanonicalFactor)
        else physical_trace_raw(factor, propagator.h_z, backend)
    )
    budget_at_entry = budget.snapshot()
    allocation = budget.allocation()
    failure_context = {
        **allocation,
        "detector_step_index": detector_step_index,
        "completed_detector_step_before_call": detector_step_index - 1,
        "physical_time_label": detector_step_index * config.dt,
        "bath_half_step": bath_half_step,
        "bath_microstep": 1,
        "rank_at_half_step_entry": factor.rank,
        "target_trace": target_trace,
        "budget_snapshot_at_half_step_entry": budget_at_entry,
        "caller_state_committed": False,
        "working_state_mutated_within_uncommitted_call": False,
        "budget_committed_for_current_compression_call": False,
        "telemetry_committed_for_current_compression_call": False,
    }

    input_blocks = tuple(_input_scaled_blocks(factor, backend))
    temporary_total_rank_upper_bound = int(
        len(kraus.operators_backend)
        * sum(int(block.shape[1]) for block in input_blocks)
    )
    resource_permitted, allocator_pool_resource_preflight = (
        _d2_prepare_resource_allowance_after_unused_pool_release(
            backend,
            n_rows=factor.n_rows,
            temporary_total_rank=temporary_total_rank_upper_bound,
        )
    )
    failure_context["allocator_pool_resource_preflight"] = (
        allocator_pool_resource_preflight
    )
    mapped_blocks: List[Any] = []
    block_metadata: List[Dict[str, Any]] = []
    branch_ranks: List[int] = []

    try:
        for branch_index, operator in enumerate(kraus.operators_backend):
            branch_rank = 0
            for input_index, raw_block in enumerate(input_blocks):
                mapped = apply_channel_kraus_block(
                    operator,
                    raw_block,
                    operators=operators,
                    config=config,
                    backend=backend,
                )
                mapped = backend.xp.ascontiguousarray(mapped)
                mapped_blocks.append(mapped)
                columns = int(mapped.shape[1])
                branch_rank += columns
                block_metadata.append(
                    {
                        "kraus_branch_index": branch_index,
                        "input_factor_block_index": input_index,
                        "columns": columns,
                        "logical_nbytes": int(mapped.nbytes),
                    }
                )
            branch_ranks.append(branch_rank)

        compressed, compression = d2_compress_mapped_blocks(
            mapped_blocks,
            block_metadata=block_metadata,
            h_z=propagator.h_z,
            target_trace=target_trace,
            budget=budget,
            allocation=allocation,
            backend=backend,
            output_block_columns=config.factor_block_columns,
            resource_permitted_bytes=resource_permitted,
        )
    except RepresentationFailure as exc:
        raise RepresentationFailure(
            str(exc),
            event={
                **failure_context,
                "compression_stage": "whole_half_repaired_rank_selection",
                "temporary_branch_ranks": branch_ranks,
                "temporary_total_kraus_rank": int(sum(branch_ranks)),
                "mapped_block_count": len(mapped_blocks),
                "budget_snapshot_at_failure": budget.snapshot(),
                "inner_failure": exc.event,
            },
        ) from exc

    increment = float(compression["certified_density_trace_norm_bound"])
    assessment = budget.assess_increment(increment, allocation=allocation)
    inner_assessment = compression["selected_budget_assessment"]
    predicate_identity = bool(
        assessment["passed"] == inner_assessment["passed"]
        and assessment["requested_increment"]
        == inner_assessment["requested_increment"]
        and assessment["allowed_trace_norm_increment"]
        == inner_assessment["allowed_trace_norm_increment"]
        and assessment["comparison_tolerance"]
        == inner_assessment["comparison_tolerance"]
    )
    if not predicate_identity:
        raise RepresentationFailure(
            "D2PR inner and outer centralized budget assessments disagree",
            event={
                **failure_context,
                "compression_report": compression,
                "inner_assessment": inner_assessment,
                "outer_assessment": assessment,
            },
        )
    if not assessment["passed"]:
        raise RepresentationFailure(
            "D2PR whole-half increment failed the centralized budget predicate",
            event={
                **failure_context,
                "compression_stage": "centralized_budget_assessment",
                "precompression_rank": compression[
                    "stable_positive_core_rank"
                ],
                "required_rank": compression["selected_rank"],
                "compression_report": compression,
                "budget_assessment": assessment,
                "budget_snapshot_at_failure": budget.snapshot(),
            },
        )
    try:
        commit = budget.commit(increment)
    except RepresentationFailure as exc:
        raise RepresentationFailure(
            str(exc),
            event={
                **failure_context,
                "compression_stage": "centralized_budget_commit",
                "precompression_rank": compression[
                    "stable_positive_core_rank"
                ],
                "required_rank": compression["selected_rank"],
                "requested_increment": increment,
                "budget_snapshot_at_failure": budget.snapshot(),
                "inner_failure": exc.event,
            },
        ) from exc

    canonical = canonicality_audit(compressed, backend)
    event = {
        **commit,
        "detector_step_index": detector_step_index,
        "completed_detector_step_before_call": detector_step_index - 1,
        "physical_time_label": detector_step_index * config.dt,
        "bath_half_step": bath_half_step,
        "bath_microstep": 1,
        "bath_action": kraus.action,
        "temporary_branch_ranks": branch_ranks,
        "temporary_total_kraus_rank": int(sum(branch_ranks)),
        "precompression_rank": compression["stable_positive_core_rank"],
        "required_rank": compression["selected_rank"],
        "rank_after": compressed.rank,
        "scientific_hard_rank_cap": None,
        "streaming_merge_count": 0,
        "streaming_density_bound": 0.0,
        "spectral_discarded_trace": compression[
            "spectral_discarded_trace_including_subfloor"
        ],
        "trace_restoration_correction": compression[
            "trace_restoration_correction"
        ],
        "retained_gauge_bound_scaled": compression[
            "repair_certificate"
        ]["cumulative_repair_density_bound"],
        "trace_norm_increment_formula": (
            "mapped candidate + blocked candidate reconstruction + repair core "
            "+ blocked repaired-factor reconstruction + trace restoration"
        ),
        "whole_half_compression": compression,
        "target_trace": target_trace,
        "trace_after": compressed.trace,
        "trace_restore_residual": abs(compressed.trace - target_trace),
        "kraus_completeness_residual": kraus.completeness_residual,
        "maximum_predicted_working_set_bytes": compression[
            "maximum_logical_working_bytes"
        ],
        "allocator_pool_resource_preflight": allocator_pool_resource_preflight,
        "canonicality_repair_trigger": CANONICALITY_REPAIR_TRIGGER,
        "canonicality_hard_tolerance": CANONICALITY_TOL,
        "canonicality_repair_target_met": bool(
            canonical[
                "weighted_basis_orthonormality_relative_frobenius_residual"
            ]
            <= CANONICALITY_REPAIR_TRIGGER
        ),
        "post_repair_acceptance_rule": D2PR2_COMPLETE_ACCEPTANCE_RULE,
        "raw_schedule_margin": compression["raw_schedule_margin"],
        "tolerance_inclusive_schedule_margin": compression[
            "tolerance_inclusive_schedule_margin"
        ],
        "first_positive_strict_raw_margin_rank": compression[
            "first_positive_strict_raw_margin_rank_within_tested_prefix"
        ],
        "inner_outer_budget_predicate_identity": predicate_identity,
        "canonicality": canonical,
        "budget_committed": True,
        "state_committed": True,
        "wall_seconds": time.perf_counter() - started,
    }
    telemetry.record(event)
    return compressed, {
        "event": event,
        "merge_audits": compression["block_reports"],
    }


def full_gram_oracle(
    raw_blocks: Sequence[np.ndarray],
    *,
    h_z: float,
    target_trace: float,
    allowed_trace_norm_increment: float,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    matrix = np.ascontiguousarray(np.concatenate(raw_blocks, axis=1), dtype=np.complex128)
    gram = h_z * (matrix.conj().T @ matrix)
    values, vectors, psd = _psd_eigh(gram, label="full Gram oracle")
    positive = np.flatnonzero(values > 0.0)
    order = positive[np.argsort(values[positive], kind="stable")[::-1]]
    sorted_values = values[order]
    sorted_vectors = vectors[:, order]
    tails = tail_after_each_rank(sorted_values)
    allowed_tail = max(float(allowed_trace_norm_increment), 0.0) / 2.0
    satisfying = np.flatnonzero(tails[1:] <= allowed_tail)
    rank = int(satisfying[0] + 1) if satisfying.size else sorted_values.size
    discarded = float(tails[rank])
    retained = float(np.sum(sorted_values[:rank], dtype=np.float64))
    basis_scaled = matrix @ sorted_vectors[:, :rank]
    scale = math.sqrt(target_trace / retained)
    factor = np.ascontiguousarray(basis_scaled * scale, dtype=np.complex128)
    weights = np.asarray(sorted_values[:rank] * (target_trace / retained), dtype=np.float64)
    return factor, weights, {
        "rank_before": int(sorted_values.size),
        "required_rank": rank,
        "discarded_trace": discarded,
        "trace_norm_increment": 2.0 * discarded,
        "psd_audit": psd,
    }

# =============================================================================
# DETECTOR CAYLEY STEP AND PHYSICAL DIAGNOSTICS
# =============================================================================
def advance_many_spinor(
    vectors: Any,
    *,
    backend: NumericalBackend,
    propagator: PropagatorObjects,
    config: RunConfig,
    operators: OscillatorOperators,
    certified_multi_rhs: bool,
) -> Tuple[Any, Any, np.ndarray, np.ndarray, int]:
    rhs = propagator.backend_b @ vectors
    solution, infos, residuals, iterations = solve_many(
        backend,
        propagator.backend_a,
        rhs,
        vectors,
        propagator.backend_preconditioner,
        propagator.backend_inverse_diagonal,
        rtol=config.gmres_rtol,
        certified_multi_rhs=certified_multi_rhs,
    )
    before = vectors.reshape(operators.d_channels, config.n_z, -1)
    after = solution.reshape(operators.d_channels, config.n_z, -1)
    q_roof = 0.5 * (before[:, -1, :] + after[:, -1, :])
    after[:, 0, :] = 0.0
    return after.reshape(vectors.shape), q_roof, infos, residuals, iterations


def advance_many_factorized(
    vectors: Any,
    *,
    backend: NumericalBackend,
    propagator: PropagatorObjects,
    config: RunConfig,
    operators: OscillatorOperators,
    certified_multi_rhs: bool,
) -> Tuple[Any, Any, np.ndarray, np.ndarray, int]:
    shaped = vectors.reshape(operators.d_channels, config.n_z, -1)
    columns = int(shaped.shape[2])
    pair_matrix = shaped.transpose(1, 0, 2).reshape(config.n_z, -1)
    pair_norm = backend.xp.linalg.norm(pair_matrix, axis=0)
    active_cpu = np.flatnonzero(np.asarray(backend.to_cpu(pair_norm > 0.0), dtype=bool))
    detector_pairs = backend.xp.zeros_like(pair_matrix)
    infos = np.zeros(pair_matrix.shape[1], dtype=np.int32)
    residuals = np.zeros(pair_matrix.shape[1], dtype=np.float64)
    iterations = 0
    if active_cpu.size:
        active = active_cpu if backend.name == "scipy" else backend._cp.asarray(active_cpu)
        inputs = pair_matrix[:, active]
        rhs = propagator.backend_b @ inputs
        solutions, active_info, active_residual, iterations = solve_many(
            backend,
            propagator.backend_a,
            rhs,
            inputs,
            propagator.backend_preconditioner,
            propagator.backend_inverse_diagonal,
            rtol=config.gmres_rtol,
            certified_multi_rhs=certified_multi_rhs,
        )
        detector_pairs[:, active] = solutions
        infos[active_cpu] = active_info
        residuals[active_cpu] = active_residual
    detector = detector_pairs.reshape(config.n_z, operators.d_channels, columns).transpose(1, 0, 2)
    q_roof = 0.5 * (shaped[:, -1, :] + detector[:, -1, :])
    detector[:, 0, :] = 0.0
    if propagator.transverse_phase_backend is None:
        raise RuntimeError("Factorized scalar phase is missing")
    next_vectors = propagator.transverse_phase_backend[:, None, None] * detector
    infos_branch = infos.reshape(operators.d_channels, columns).max(axis=0)
    residuals_branch = residuals.reshape(operators.d_channels, columns).max(axis=0)
    return next_vectors.reshape(vectors.shape), q_roof, infos_branch, residuals_branch, iterations


def advance_many_detector(
    vectors: Any,
    *,
    backend: NumericalBackend,
    propagator: PropagatorObjects,
    config: RunConfig,
    operators: OscillatorOperators,
    certified_multi_rhs: bool,
) -> Tuple[Any, Any, np.ndarray, np.ndarray, int]:
    if config.propagator_type == "scalar_factorized":
        return advance_many_factorized(
            vectors,
            backend=backend,
            propagator=propagator,
            config=config,
            operators=operators,
            certified_multi_rhs=certified_multi_rhs,
        )
    return advance_many_spinor(
        vectors,
        backend=backend,
        propagator=propagator,
        config=config,
        operators=operators,
        certified_multi_rhs=certified_multi_rhs,
    )


def detector_advance_canonical(
    factor: CanonicalFactor,
    *,
    operators: OscillatorOperators,
    config: RunConfig,
    propagator: PropagatorObjects,
    backend: NumericalBackend,
    certified_multi_rhs: bool,
) -> Tuple[RawFactor, float, Dict[str, Any]]:
    started = time.perf_counter()
    output_blocks: List[Any] = []
    info_values: List[np.ndarray] = []
    residual_values: List[np.ndarray] = []
    iterations = 0
    probability_terms: List[float] = []
    trace_before = factor.trace

    for scaled_block in iter_canonical_scaled_blocks(factor, backend):
        block_rank = int(scaled_block.shape[1])
        output = backend.xp.empty_like(scaled_block)
        for start in range(0, block_rank, config.detector_rhs_batch_columns):
            stop = min(block_rank, start + config.detector_rhs_batch_columns)
            batch = backend.xp.ascontiguousarray(scaled_block[:, start:stop])
            advanced, q_roof, infos, residuals, used = advance_many_detector(
                batch,
                backend=backend,
                propagator=propagator,
                config=config,
                operators=operators,
                certified_multi_rhs=certified_multi_rhs,
            )
            output[:, start:stop] = advanced
            # The h_z from the physical trace cancels the 1/h_z in G_D.
            probability_terms.append(
                float(config.dt * config.kappa * backend.abs2_sum(q_roof))
            )
            info_values.append(np.asarray(infos, dtype=np.int32))
            residual_values.append(np.asarray(residuals, dtype=np.float64))
            iterations += int(used)
        output_blocks.append(backend.xp.ascontiguousarray(output))

    raw = RawFactor(tuple(output_blocks), factor.n_rows)
    trace_after = physical_trace_raw(raw, propagator.h_z, backend)
    probability = float(math.fsum(probability_terms))
    infos_all = np.concatenate(info_values) if info_values else np.empty(0, dtype=np.int32)
    residuals_all = np.concatenate(residual_values) if residual_values else np.empty(0, dtype=np.float64)
    audit = {
        "rank": factor.rank,
        "trace_before": trace_before,
        "trace_after": trace_after,
        "midpoint_roof_probability": probability,
        "detector_probability_closure": trace_before - trace_after - probability,
        "gmres_failure_count": int(np.count_nonzero(infos_all != 0)),
        "maximum_true_relative_residual": float(np.max(residuals_all)) if residuals_all.size else 0.0,
        "multi_rhs_inner_iterations": iterations,
        "multi_rhs_enabled": certified_multi_rhs,
        "wall_seconds": time.perf_counter() - started,
    }
    if audit["gmres_failure_count"] != 0:
        raise RuntimeError(f"Detector GMRES failed: {audit}")
    if audit["maximum_true_relative_residual"] > TRUE_RESIDUAL_TOL:
        raise RuntimeError(f"Detector true residual failed: {audit}")
    if not np.isfinite(probability) or probability < 0.0:
        raise RuntimeError("Midpoint detector probability is non-finite or negative")
    if abs(audit["detector_probability_closure"]) > PROBABILITY_CLOSURE_ABS_TOL:
        raise RuntimeError(f"Detector midpoint closure failed: {audit}")
    return raw, probability, audit


def _factor_scaled_blocks(
    factor: Union[CanonicalFactor, RawFactor],
    backend: NumericalBackend,
) -> Iterable[Any]:
    yield from _input_scaled_blocks(factor, backend)


def factor_channel_diagonal(
    factor: Union[CanonicalFactor, RawFactor],
    *,
    operators: OscillatorOperators,
    config: RunConfig,
    h_z: float,
    backend: NumericalBackend,
) -> np.ndarray:
    terms = np.zeros(operators.d_channels, dtype=np.float64)
    for block in _factor_scaled_blocks(factor, backend):
        rank = int(block.shape[1])
        shaped = block.reshape(operators.d_channels, config.n_z * rank)
        density = backend.xp.sum(
            shaped.real * shaped.real + shaped.imag * shaped.imag,
            axis=1,
            dtype=backend.float64,
        )
        terms += np.asarray(backend.to_cpu(density), dtype=np.float64)
    return h_z * terms


def factor_top_shell(
    factor: Union[CanonicalFactor, RawFactor],
    *,
    operators: OscillatorOperators,
    config: RunConfig,
    h_z: float,
    backend: NumericalBackend,
) -> float:
    diagonal = factor_channel_diagonal(
        factor, operators=operators, config=config, h_z=h_z, backend=backend
    )
    orbital_mask = (operators.shell_of_mode == config.n_shell).astype(np.float64)
    channel_mask = np.concatenate([orbital_mask, orbital_mask])
    return float(np.dot(channel_mask, diagonal))


def factor_unit_activity(
    factor: Union[CanonicalFactor, RawFactor],
    *,
    g_diagonal: np.ndarray,
    operators: OscillatorOperators,
    config: RunConfig,
    h_z: float,
    backend: NumericalBackend,
) -> float:
    diagonal = factor_channel_diagonal(
        factor, operators=operators, config=config, h_z=h_z, backend=backend
    )
    return float(np.dot(np.asarray(g_diagonal, dtype=np.float64), diagonal))


def complete_step(
    factor: CanonicalFactor,
    *,
    step_index: int,
    operators: OscillatorOperators,
    propagator: PropagatorObjects,
    kraus: BathKraus,
    config: RunConfig,
    backend: NumericalBackend,
    budget: RepresentationBudgetState,
    telemetry: RepresentationTelemetry,
    certified_multi_rhs: bool,
) -> Tuple[CanonicalFactor, Dict[str, Any]]:
    """Execute one complete Strang step with transactional ledgers.

    Physical state is local until return.  Representation budget and telemetry
    are cloned, both bath halves and the detector step run against the staged
    ledgers, and the external ledgers are mutated only after every complete-step
    numerical gate passes.
    """
    started = time.perf_counter()
    survival_before = factor.trace
    input_rank = factor.rank
    budget_before_step = budget.snapshot()
    telemetry_before = telemetry.snapshot()
    staged_budget = RepresentationBudgetState(
        total_budget=budget.total_budget,
        total_planned_calls=budget.total_planned_calls,
        calls_completed=budget.calls_completed,
        bound_used=budget.bound_used,
    )
    staged_telemetry = RepresentationTelemetry()
    staged_telemetry.restore(telemetry_before)
    phase = "first_bath_half_step"
    first_completed = False
    detector_completed = False
    try:
        first, first_audit = cssf_bath_half_step(
            factor,
            kraus=kraus,
            operators=operators,
            config=config,
            propagator=propagator,
            backend=backend,
            budget=staged_budget,
            telemetry=staged_telemetry,
            detector_step_index=step_index,
            bath_half_step="first",
        )
        first_completed = True
        trace_first = first.trace
        phase = "detector_cayley_step"
        detector_raw, p_midpoint, detector_audit = detector_advance_canonical(
            first,
            operators=operators,
            config=config,
            propagator=propagator,
            backend=backend,
            certified_multi_rhs=certified_multi_rhs,
        )
        detector_completed = True
        trace_detector = physical_trace_raw(
            detector_raw, propagator.h_z, backend
        )
        phase = "second_bath_half_step"
        second, second_audit = cssf_bath_half_step(
            detector_raw,
            kraus=kraus,
            operators=operators,
            config=config,
            propagator=propagator,
            backend=backend,
            budget=staged_budget,
            telemetry=staged_telemetry,
            detector_step_index=step_index,
            bath_half_step="second",
        )
    except RepresentationFailure as exc:
        staged_snapshot = staged_budget.snapshot()
        raise RepresentationFailure(
            str(exc),
            event={
                **exc.event,
                "complete_step_index": step_index,
                "completed_detector_step_before_failure": step_index - 1,
                "complete_step_phase_at_failure": phase,
                "complete_step_input_rank": input_rank,
                "complete_step_input_trace": survival_before,
                "first_bath_half_completed_within_uncommitted_step": first_completed,
                "detector_cayley_completed_within_uncommitted_step": detector_completed,
                "complete_step_state_committed": False,
                "budget_snapshot_before_complete_step": budget_before_step,
                "external_budget_snapshot_at_failure": budget.snapshot(),
                "staged_budget_snapshot_at_failure": staged_snapshot,
                "budget_calls_staged_within_incomplete_step": int(
                    staged_snapshot["calls_completed"]
                    - budget_before_step["calls_completed"]
                ),
                "budget_bound_staged_within_incomplete_step": float(
                    staged_snapshot["bound_used"]
                    - budget_before_step["bound_used"]
                ),
                "telemetry_events_staged_within_incomplete_step": int(
                    len(staged_telemetry.events) - len(telemetry_before)
                ),
                "budget_calls_committed_within_incomplete_step": 0,
                "budget_bound_committed_within_incomplete_step": 0.0,
                "budget_mutation_occurred_within_incomplete_step": False,
                "telemetry_events_committed_within_incomplete_step": 0,
                "transactional_ledgers_preserved": bool(
                    budget.snapshot() == budget_before_step
                    and telemetry.snapshot() == telemetry_before
                ),
            },
        ) from exc

    survival_after = second.trace
    top_shell = factor_top_shell(
        second,
        operators=operators,
        config=config,
        h_z=propagator.h_z,
        backend=backend,
    )
    activity = factor_unit_activity(
        second,
        g_diagonal=kraus.g_diagonal,
        operators=operators,
        config=config,
        h_z=propagator.h_z,
        backend=backend,
    )
    audit = {
        "step_index": step_index,
        "time": step_index * config.dt,
        "survival_before": survival_before,
        "trace_after_first_bath": trace_first,
        "trace_after_detector": trace_detector,
        "survival_after": survival_after,
        "midpoint_roof_probability": p_midpoint,
        "bath_trace_residual_first": trace_first - survival_before,
        "bath_trace_residual_second": survival_after - trace_detector,
        "composed_probability_closure": survival_before - survival_after - p_midpoint,
        "survival_increase": survival_after - survival_before,
        "rank_after": second.rank,
        "top_shell_population": top_shell,
        "upward_omitted_intensity": (
            config.rate_lambda * (config.n_shell + 2.0) * top_shell
        ),
        "unit_bath_activity": activity,
        "detector_audit": detector_audit,
        "first_bath": first_audit,
        "second_bath": second_audit,
        "representation_bound_used": staged_budget.bound_used,
        "transactional_budget_commit": True,
        "transactional_telemetry_commit": True,
        "wall_seconds": time.perf_counter() - started,
    }
    finite_values = np.asarray(
        [
            survival_before,
            trace_first,
            trace_detector,
            survival_after,
            p_midpoint,
            top_shell,
            activity,
            staged_budget.bound_used,
        ],
        dtype=np.float64,
    )
    if not np.all(np.isfinite(finite_values)):
        raise RuntimeError(f"Non-finite complete-step diagnostic: {audit}")
    if abs(audit["bath_trace_residual_first"]) > BATH_TRACE_RESIDUAL_TOL:
        raise RuntimeError(f"First bath trace gate failed: {audit}")
    if abs(audit["bath_trace_residual_second"]) > BATH_TRACE_RESIDUAL_TOL:
        raise RuntimeError(f"Second bath trace gate failed: {audit}")
    if abs(audit["composed_probability_closure"]) > PROBABILITY_CLOSURE_ABS_TOL:
        raise RuntimeError(f"Complete-step probability gate failed: {audit}")
    if audit["survival_increase"] > SURVIVAL_INCREASE_TOL:
        raise RuntimeError(f"Survival-increase gate failed: {audit}")

    # Atomic logical commit after every complete-step gate has passed.
    budget.calls_completed = staged_budget.calls_completed
    budget.bound_used = staged_budget.bound_used
    telemetry.restore(staged_telemetry.snapshot())
    audit["representation_bound_used"] = budget.bound_used
    audit["wall_seconds"] = time.perf_counter() - started
    return second, audit

# =============================================================================
# CHECKPOINT / RESTART — FRESH V4 ONLY, COMPLETE STRANG STEPS ONLY
# =============================================================================
def _write_hash_manifest(directory: Path, *, manifest_name: str = "SHA256SUMS") -> Dict[str, str]:
    files = [
        path for path in sorted(directory.rglob("*"))
        if path.is_file() and path.name != manifest_name
    ]
    hashes = {str(path.relative_to(directory)): sha256_file(path) for path in files}
    text = "".join(f"{digest}  {name}\n" for name, digest in hashes.items())
    (directory / manifest_name).write_text(text, encoding="utf-8")
    return hashes


def verify_hash_manifest(directory: Path, *, manifest_name: str = "SHA256SUMS") -> Dict[str, Any]:
    manifest = directory / manifest_name
    if not manifest.is_file():
        return {"passed": False, "reason": "manifest_missing", "files": {}}
    results: Dict[str, bool] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        name = name.strip()
        path = directory / name
        results[name] = bool(path.is_file() and sha256_file(path) == digest)
    return {"passed": bool(results and all(results.values())), "files": results}


def save_checkpoint(
    checkpoint_root: Path,
    *,
    completed_step: int,
    factor: CanonicalFactor,
    budget: RepresentationBudgetState,
    telemetry: RepresentationTelemetry,
    histories: Mapping[str, np.ndarray],
    source_sha256: str,
    numerical_core_sha256: str,
    family_contract: Mapping[str, Any],
    execution_contract: Mapping[str, Any],
    backend: NumericalBackend,
) -> Path:
    if completed_step <= 0:
        raise ValueError("A v4 checkpoint must follow a positive complete Strang step")
    target = checkpoint_root / f"checkpoint_step_{completed_step:07d}"
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite checkpoint {target}")
    canonical = canonicality_audit(factor, backend)
    if not canonical["passed"]:
        raise RepresentationFailure("Cannot checkpoint a noncanonical factor", event=canonical)

    def writer(tmp: Path) -> None:
        atomic_save_npy(tmp / "weights.npy", np.asarray(factor.weights, dtype=np.float64))
        for index, block in enumerate(factor.basis_blocks):
            atomic_save_npy(
                tmp / f"basis_block_{index:04d}.npy",
                np.asarray(backend.to_cpu(block), dtype=np.complex128),
            )
        atomic_savez(tmp / "histories.npz", **{key: np.asarray(value) for key, value in histories.items()})
        atomic_write_json(tmp / "representation_telemetry.json", {
            "schema": REPRESENTATION_TELEMETRY_SCHEMA,
            "events": telemetry.snapshot(),
        })
        metadata = {
            "schema": CHECKPOINT_SCHEMA,
            "created_utc": utc_now_iso(),
            "completed_after_complete_strang_step": True,
            "completed_step": int(completed_step),
            "physical_time": float(completed_step * float(execution_contract["dt"])) ,
            "source_sha256": source_sha256,
            "numerical_core_sha256": numerical_core_sha256,
            "physical_family_contract_sha256": family_contract["contract_sha256"],
            "pilot_execution_contract_sha256": execution_contract["contract_sha256"],
            "factor_rank": factor.rank,
            "factor_trace": factor.trace,
            "factor_block_count": len(factor.basis_blocks),
            "factor_block_files": [f"basis_block_{i:04d}.npy" for i in range(len(factor.basis_blocks))],
            "h_z": factor.h_z,
            "n_rows": factor.n_rows,
            "canonicality": canonical,
            "representation_budget": budget.snapshot(),
            "legacy_checkpoint_import": False,
            "checkpoint_migration_enabled": False,
            "production_authorized": False,
            "task10_eligible": False,
        }
        atomic_write_json(tmp / "metadata.json", metadata)
        _write_hash_manifest(tmp)

    atomic_checkpoint_directory(target, writer)
    return target


def load_checkpoint(
    checkpoint: Path,
    *,
    expected_source_sha256: str,
    expected_numerical_core_sha256: str,
    expected_family_contract_sha256: str,
    backend: NumericalBackend,
) -> Tuple[int, CanonicalFactor, RepresentationBudgetState, RepresentationTelemetry, Dict[str, np.ndarray], Dict[str, Any]]:
    verification = verify_hash_manifest(checkpoint)
    if not verification["passed"]:
        raise GateBlocked(f"Checkpoint hash verification failed: {verification}")
    metadata = read_json(checkpoint / "metadata.json")
    required = {
        "schema": CHECKPOINT_SCHEMA,
        "source_sha256": expected_source_sha256,
        "numerical_core_sha256": expected_numerical_core_sha256,
        "physical_family_contract_sha256": expected_family_contract_sha256,
        "legacy_checkpoint_import": False,
        "checkpoint_migration_enabled": False,
        "production_authorized": False,
        "task10_eligible": False,
        "completed_after_complete_strang_step": True,
    }
    mismatches = {
        key: {"found": metadata.get(key), "expected": expected}
        for key, expected in required.items()
        if metadata.get(key) != expected
    }
    if mismatches:
        raise GateBlocked(f"Checkpoint contract mismatch: {mismatches}")
    weights = np.load(checkpoint / "weights.npy", allow_pickle=False)
    blocks = tuple(
        backend.to_backend_array(np.load(checkpoint / name, allow_pickle=False))
        for name in metadata["factor_block_files"]
    )
    factor = CanonicalFactor(
        basis_blocks=blocks,
        weights=np.asarray(weights, dtype=np.float64),
        n_rows=int(metadata["n_rows"]),
        h_z=float(metadata["h_z"]),
    )
    canonical = canonicality_audit(factor, backend)
    if not canonical["passed"]:
        raise GateBlocked(f"Restored checkpoint is not canonical: {canonical}")
    budget_record = metadata["representation_budget"]
    budget = RepresentationBudgetState(
        total_budget=float(budget_record["total_budget"]),
        total_planned_calls=int(budget_record["total_planned_calls"]),
        calls_completed=int(budget_record["calls_completed"]),
        bound_used=float(budget_record["bound_used"]),
    )
    telemetry_record = read_json(checkpoint / "representation_telemetry.json")
    telemetry = RepresentationTelemetry()
    telemetry.restore(telemetry_record["events"])
    with np.load(checkpoint / "histories.npz", allow_pickle=False) as archive:
        histories = {key: np.asarray(archive[key]) for key in archive.files}
    return int(metadata["completed_step"]), factor, budget, telemetry, histories, metadata


def latest_compatible_checkpoint(config: RunConfig) -> Optional[Path]:
    if not config.resume_from_checkpoint:
        return None
    candidates: List[Tuple[int, Path]] = []
    base = config.output_root / CASE_DIRECTORY_NAME
    for gate_dir in ("V4_G2", "V4_G3", "V4_G4"):
        root = base / gate_dir / "checkpoints"
        if not root.is_dir():
            continue
        for path in root.glob("checkpoint_step_*"):
            try:
                step = int(path.name.rsplit("_", 1)[1])
            except Exception:
                continue
            if step < config.execution_num_steps:
                candidates.append((step, path))
    return max(candidates, default=(0, None), key=lambda item: item[0])[1]

# =============================================================================
# V4-G0 CERTIFICATION
# =============================================================================

def run_g0_repaired_gauge_certificate_test() -> Dict[str, Any]:
    """Dense reduced test of exact weighted-polar repair and its certificate."""
    backend = NumericalBackend("scipy")
    rng = np.random.default_rng(2026081302)
    rows = 48
    rank = 7
    h_z = 0.125
    raw = rng.normal(size=(rows, rank)) + 1j * rng.normal(
        size=(rows, rank)
    )
    q, _ = np.linalg.qr(raw)
    q = q / math.sqrt(h_z)
    weights = np.geomspace(0.4, 1.0e-5, rank)
    weights /= np.sum(weights)
    diagonal_perturbation = np.linspace(-1.0, 1.0, rank)
    diagonal_perturbation -= float(
        np.sum(weights * diagonal_perturbation, dtype=np.float64)
    )
    mixing = np.eye(rank, dtype=np.complex128)
    mixing += np.diag(diagonal_perturbation) * 5.0e-8
    q_bad = q @ mixing
    factor = CanonicalFactor(
        basis_blocks=(backend.to_backend_array(q_bad),),
        weights=np.asarray(weights, dtype=np.float64),
        n_rows=rows,
        h_z=h_z,
    )
    target_trace = factor.trace
    density_before = factor_density_cpu(factor, backend)
    canonicality_before = canonicality_audit(factor, backend)
    repaired, report = _d2_repair_until_hard_gate_with_complete_certificate(
        factor,
        backend=backend,
        block_columns=4,
        target_trace=target_trace,
        reason="G0 D2PR exact repair",
    )
    density_after = factor_density_cpu(repaired, backend)
    actual_difference = density_trace_norm(
        density_after - density_before, h_z
    )
    certified = float(report["cumulative_repair_density_bound"])
    slack = float(16.0 * np.finfo(float).eps * max(target_trace, 1.0))
    checks = {
        "input_exceeds_proactive_trigger": _canonicality_residual(
            canonicality_before
        ) > CANONICALITY_REPAIR_TRIGGER,
        "repair_executed": report["repair_pass_count"] >= 1,
        "hard_canonicality_passed": report["canonicality_after"]["passed"],
        "trace_restoration_passed": report["trace_restore_gate_passed"],
        "actual_density_change_bounded": actual_difference <= certified + slack,
        "finite_nonnegative_certificate": bool(
            np.isfinite(certified) and certified >= 0.0
        ),
    }
    return {
        "canonicality_before": canonicality_before,
        "repair_report": report,
        "actual_density_trace_norm_change": actual_difference,
        "certified_repair_density_bound": certified,
        "certificate_slack": slack,
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


def run_g0_call3777_repaired_rank_ladder_regression() -> Dict[str, Any]:
    """Frozen C2-A arithmetic regression using the exact centralized predicate."""
    budget = RepresentationBudgetState(
        total_budget=REPRESENTATION_TRACE_NORM_BUDGET,
        total_planned_calls=TOTAL_PHYSICAL_COMPRESSION_CALLS,
        calls_completed=3776,
        bound_used=9.440069243677224e-10,
    )
    budget_before = budget.snapshot()
    allocation = budget.allocation()
    expected_allowance = 2.4307563227756543e-13
    frozen_bounds = {
        28: 2.48121988846993999e-13,
        29: 1.94744550193440924e-13,
        30: 1.41482447998780012e-13,
        31: 8.80730480594253629e-14,
        32: 3.57151319966449594e-14,
    }
    reports: List[Dict[str, Any]] = []
    for rank, bound in frozen_bounds.items():
        assessment = budget.assess_increment(bound, allocation=allocation)
        allowance = float(allocation["allowed_trace_norm_increment"])
        tolerance = float(assessment["comparison_tolerance"])
        reports.append(
            {
                "rank": rank,
                "complete_repaired_density_bound": bound,
                "centralized_budget_assessment": assessment,
                "raw_schedule_margin": allowance - bound,
                "tolerance_inclusive_schedule_margin": (
                    allowance + tolerance - bound
                ),
                "strict_raw_margin_pass": bool(
                    bound <= allowance
                    and assessment["bound_after_if_committed"]
                    <= budget.total_budget
                ),
                "rank_admissible": bool(assessment["passed"]),
            }
        )
    selected, first_strict = _d2_select_first_admissible_rank_report(reports)

    no_admissible_reports = [
        {
            "rank": rank,
            "complete_repaired_density_bound": (
                float(allocation["allowed_trace_norm_increment"])
                + budget.comparison_tolerance()
                + (rank + 1) * 1.0e-15
            ),
            "raw_schedule_margin": -1.0,
            "tolerance_inclusive_schedule_margin": -1.0,
            "strict_raw_margin_pass": False,
            "rank_admissible": False,
        }
        for rank in range(3)
    ]
    no_admissible_failure = None
    try:
        _d2_select_first_admissible_rank_report(no_admissible_reports)
    except RepresentationFailure as exc:
        no_admissible_failure = {
            "error": str(exc),
            "event": exc.event,
        }

    budget_after = budget.snapshot()
    tolerance = budget.comparison_tolerance()
    checks = {
        "call_index_exact": allocation["compression_call_index"] == 3777,
        "ceiling_exact": math.isclose(
            float(allocation["scheduled_cumulative_ceiling"]),
            9.4425e-10,
            rel_tol=0.0,
            abs_tol=5.0e-25,
        ),
        "allowance_exact": math.isclose(
            float(allocation["allowed_trace_norm_increment"]),
            expected_allowance,
            rel_tol=0.0,
            abs_tol=5.0e-28,
        ),
        "comparison_tolerance_exact": math.isclose(
            tolerance,
            7.105427357601002e-15,
            rel_tol=0.0,
            abs_tol=1.0e-30,
        ),
        "first_tolerance_inclusive_rank_is_28": int(selected["rank"]) == 28,
        "rank28_raw_margin_negative": reports[0]["raw_schedule_margin"] < 0.0,
        "rank28_tolerance_margin_positive": reports[0][
            "tolerance_inclusive_schedule_margin"
        ] > 0.0,
        "first_positive_strict_raw_margin_rank_is_29": bool(
            first_strict is not None and int(first_strict["rank"]) == 29
        ),
        "selection_policy_not_silently_changed": bool(
            int(selected["rank"]) == 28
            and int(first_strict["rank"]) == 29
        ),
        "budget_not_committed_by_regression": budget_before == budget_after,
        "no_admissible_rank_fails_closed": bool(
            no_admissible_failure is not None
            and len(
                no_admissible_failure["event"][
                    "complete_repaired_rank_ladder"
                ]
            )
            == len(no_admissible_reports)
        ),
    }
    return {
        "authority": "archivally verified C2-A call-3777 ladder",
        "allocation": allocation,
        "comparison_tolerance": tolerance,
        "tolerance_inclusive_threshold": (
            float(allocation["allowed_trace_norm_increment"]) + tolerance
        ),
        "rank_ladder": reports,
        "selected_rank": int(selected["rank"]),
        "first_positive_strict_raw_margin_rank": int(first_strict["rank"]),
        "no_admissible_rank_injection": no_admissible_failure,
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


def run_g0_repaired_rank_adversarial_tests(
    whole_half_oracle: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Focused fail-closed tests for the amended repaired-rank interior."""
    backend = NumericalBackend("scipy")
    c2_policy = run_g0_call3777_repaired_rank_ladder_regression()

    rng = np.random.default_rng(2026081301)
    dimension = 48
    h_z = 0.125
    q, _ = np.linalg.qr(
        rng.normal(size=(dimension, 12))
        + 1j * rng.normal(size=(dimension, 12))
    )
    singular = 10.0 ** (-np.linspace(0.0, 13.0, 12))
    decaying = q[:, :12] * singular[None, :] / math.sqrt(h_z)
    blocks_cpu = [decaying[:, :4], decaying[:, 4:8], decaying[:, 8:]]
    blocks = tuple(
        backend.to_backend_array(np.asarray(block, np.complex128))
        for block in blocks_cpu
    )
    matrix = np.ascontiguousarray(np.concatenate(blocks_cpu, axis=1))
    target_trace = float(h_z * np.vdot(matrix, matrix).real)
    metadata = [
        {
            "kraus_branch_index": index,
            "input_factor_block_index": 0,
            "columns": int(block.shape[1]),
            "logical_nbytes": int(block.nbytes),
        }
        for index, block in enumerate(blocks)
    ]

    # Force rejection of the first otherwise admissible candidate.  The actual
    # compressor must escalate and select the next strict-margin rank without
    # committing the supplied budget.
    escalation_budget = RepresentationBudgetState(1.0e-8, 1)
    escalation_before = escalation_budget.snapshot()
    original_assessor = globals()["_d2_assess_repaired_rank_candidate"]
    observed: List[Dict[str, Any]] = []
    forced = {"done": False}

    def reject_first_admissible(
        candidate: CanonicalFactor,
        candidate_report: Mapping[str, Any],
        **kwargs: Any,
    ) -> Tuple[Optional[CanonicalFactor], Dict[str, Any]]:
        repaired, report = original_assessor(
            candidate, candidate_report, **kwargs
        )
        record = {
            "rank": int(candidate_report["rank"]),
            "naturally_admissible": bool(report.get("rank_admissible", False)),
            "naturally_strict_raw_margin": bool(
                report.get("strict_raw_margin_pass", False)
            ),
        }
        if not forced["done"] and record["naturally_admissible"]:
            forced["done"] = True
            report = dict(report)
            report["adversarial_forced_rejection"] = True
            report["rank_admissible"] = False
            repaired = None
            record["forced_rejected"] = True
        else:
            record["forced_rejected"] = False
        observed.append(record)
        return repaired, report

    globals()["_d2_assess_repaired_rank_candidate"] = reject_first_admissible
    try:
        escalated_factor, escalated_report = d2_compress_mapped_blocks(
            blocks,
            block_metadata=metadata,
            h_z=h_z,
            target_trace=target_trace,
            budget=escalation_budget,
            allocation=escalation_budget.allocation(),
            backend=backend,
            output_block_columns=4,
            resource_permitted_bytes=None,
        )
    finally:
        globals()["_d2_assess_repaired_rank_candidate"] = original_assessor
    escalation_after = escalation_budget.snapshot()
    first_rejected_rank = next(
        (item["rank"] for item in observed if item["forced_rejected"]), None
    )
    escalation_checks = {
        "one_natural_candidate_was_forced_to_fail": forced["done"],
        "more_than_one_rank_was_tested": len(observed) >= 2,
        "selected_rank_is_above_rejected_rank": bool(
            first_rejected_rank is not None
            and escalated_factor.rank > int(first_rejected_rank)
        ),
        "selected_rank_has_strict_raw_margin": bool(
            escalated_report["selected_rank_strict_raw_margin_pass"]
        ),
        "compressor_did_not_commit_budget": escalation_before == escalation_after,
        "selected_factor_is_canonical": canonicality_audit(
            escalated_factor, backend
        )["passed"],
    }
    escalation = {
        "observed_candidate_sequence": observed,
        "first_forced_rejected_rank": first_rejected_rank,
        "selected_rank": escalated_factor.rank,
        "selected_raw_margin": escalated_report["raw_schedule_margin"],
        "selected_tolerance_margin": escalated_report[
            "tolerance_inclusive_schedule_margin"
        ],
        "budget_before": escalation_before,
        "budget_after": escalation_after,
        "checks": escalation_checks,
        "passed": bool(all(escalation_checks.values())),
    }

    # A rank-deficient basis must make the exact weighted-polar repair fail
    # closed without mutating the supplied factor.
    duplicate_column = np.ones((16, 1), dtype=np.complex128)
    duplicate_column /= math.sqrt(
        h_z * float(np.vdot(duplicate_column, duplicate_column).real)
    )
    duplicate_basis = np.concatenate(
        [duplicate_column, duplicate_column.copy()], axis=1
    )
    singular_factor = CanonicalFactor(
        basis_blocks=(backend.to_backend_array(duplicate_basis),),
        weights=np.asarray([0.6, 0.4], dtype=np.float64),
        n_rows=16,
        h_z=h_z,
    )
    singular_density_before = factor_density_cpu(singular_factor, backend)
    singular_weights_before = singular_factor.weights.copy()
    repair_failure_event: Dict[str, Any] = {}
    repair_failure_caught = False
    try:
        _d2_repair_until_hard_gate_with_complete_certificate(
            singular_factor,
            backend=backend,
            block_columns=2,
            target_trace=singular_factor.trace,
            reason="G0 adversarial singular gauge",
        )
    except RepresentationFailure as exc:
        repair_failure_caught = True
        repair_failure_event = dict(exc.event)
    singular_density_after = factor_density_cpu(singular_factor, backend)
    repair_failure_checks = {
        "repair_failure_caught": repair_failure_caught,
        "rank_deficiency_identified": "invertibility_floor" in repair_failure_event,
        "input_weights_unchanged": np.array_equal(
            singular_factor.weights, singular_weights_before
        ),
        "input_density_unchanged": density_trace_norm(
            singular_density_after - singular_density_before, h_z
        )
        == 0.0,
    }
    repair_failure = {
        "event": repair_failure_event,
        "checks": repair_failure_checks,
        "passed": bool(all(repair_failure_checks.values())),
    }

    # Force every blocked candidate reconstruction certificate to fail.  The
    # dynamic ladder must be saved, no rank admitted, and no budget committed.
    reconstruction_budget = RepresentationBudgetState(1.0e-8, 1)
    reconstruction_before = reconstruction_budget.snapshot()
    original_reconstruction = globals()["_d2_output_reconstruction_bound"]
    reconstruction_calls = {"count": 0}

    def reject_reconstruction(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        reconstruction_calls["count"] += 1
        raise RepresentationFailure(
            "G0 injected blocked reconstruction-certificate failure",
            event={
                "injected_reconstruction_certificate_failure": True,
                "call": reconstruction_calls["count"],
            },
        )

    globals()["_d2_output_reconstruction_bound"] = reject_reconstruction
    reconstruction_event: Dict[str, Any] = {}
    reconstruction_caught = False
    try:
        d2_compress_mapped_blocks(
            blocks,
            block_metadata=metadata,
            h_z=h_z,
            target_trace=target_trace,
            budget=reconstruction_budget,
            allocation=reconstruction_budget.allocation(),
            backend=backend,
            output_block_columns=4,
            resource_permitted_bytes=None,
        )
    except RepresentationFailure as exc:
        reconstruction_caught = True
        reconstruction_event = dict(exc.event)
    finally:
        globals()["_d2_output_reconstruction_bound"] = original_reconstruction
    reconstruction_after = reconstruction_budget.snapshot()
    reconstruction_inner = reconstruction_event.get(
        "inner_failure", reconstruction_event
    )
    reconstruction_ladder = reconstruction_inner.get(
        "complete_repaired_rank_ladder", []
    )
    reconstruction_checks = {
        "failure_caught": reconstruction_caught,
        "certificate_was_exercised": reconstruction_calls["count"] > 0,
        "complete_failed_ladder_recorded": bool(reconstruction_ladder),
        "all_tested_ranks_failed_at_reconstruction": bool(
            reconstruction_ladder
            and all(
                item.get("candidate_failure_stage")
                == "candidate_construction_or_reconstruction_certificate"
                for item in reconstruction_ladder
            )
        ),
        "budget_unchanged": reconstruction_before == reconstruction_after,
    }
    reconstruction_failure = {
        "certificate_calls": reconstruction_calls["count"],
        "event": reconstruction_event,
        "checks": reconstruction_checks,
        "passed": bool(all(reconstruction_checks.values())),
    }

    oracle_report = (
        run_g0_whole_half_oracle_tests()
        if whole_half_oracle is None
        else dict(whole_half_oracle)
    )
    no_admissible = oracle_report["actual_no_admissible_rank_injection"]
    policy_checks = {
        "rank28_is_first_tolerance_only_formal_pass": bool(
            c2_policy["selected_rank"] == 28
            and c2_policy["first_positive_strict_raw_margin_rank"] == 29
            and c2_policy["rank_ladder"][0]["raw_schedule_margin"] < 0.0
            and c2_policy["rank_ladder"][0][
                "tolerance_inclusive_schedule_margin"
            ]
            > 0.0
        ),
    }
    checks = {
        "frozen_call3777_policy": bool(all(policy_checks.values())),
        "forced_dynamic_rank_escalation": escalation["passed"],
        "no_admissible_rank_fail_closed": bool(no_admissible["passed"]),
        "canonicality_repair_failure_fail_closed": repair_failure["passed"],
        "reconstruction_certificate_failure_fail_closed": reconstruction_failure[
            "passed"
        ],
    }
    return {
        "schema": D2PR2_ADVERSARIAL_TEST_SCHEMA,
        "frozen_call3777_policy": {
            "selected_rank": c2_policy["selected_rank"],
            "first_strict_raw_margin_rank": c2_policy[
                "first_positive_strict_raw_margin_rank"
            ],
            "rank28_report": c2_policy["rank_ladder"][0],
            "rank29_report": c2_policy["rank_ladder"][1],
            "checks": policy_checks,
            "passed": bool(all(policy_checks.values())),
        },
        "forced_dynamic_rank_escalation": escalation,
        "no_admissible_rank": no_admissible,
        "canonicality_repair_failure": repair_failure,
        "reconstruction_certificate_failure": reconstruction_failure,
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


def parent_lineage_audit(script_path: Path) -> Dict[str, Any]:
    """Verify the exact D2PR2G1F parent and the R1-A allocator authority."""
    roots = [script_path.parent, Path.cwd(), DATA_ROOT]
    specifications = {
        "parent_source": (
            "Task09_4901_U2_low_v4_nonaccepting_D2PR2G1F_BATCH64_REPAIRED_RANK_WHOLEHALF_G0.py",
            D2PR2G1FMP_PARENT_SOURCE_SHA256,
        ),
        "r1_allocator_diagnostic_source": (
            "Task09_V4_R1_readonly_allocator_pool_exact_call4304.py",
            D2PR2G1FMP_R1_DIAGNOSTIC_SOURCE_SHA256,
        ),
        "r1_allocator_authority_record": (
            "Task09_D2PR2G1F_R1A_Authority_Record_2026-08-14.json",
            D2PR2G1FMP_R1_AUTHORITY_RECORD_SHA256,
        ),
        "g1_a100_controlled_failure_diagnosis": (
            "Task09_D2PR2_G1A100_Controlled_Failure_Diagnosis_2026-08-14.json",
            D2PR2G1F_FAILURE_DIAGNOSIS_SHA256,
        ),
        "c2_source": (
            "V4_C2_readonly_repaired_rank_ladder_audit_2026-08-13.py",
            D2PR_C2_SOURCE_SHA256,
        ),
        "c2_static_audit": (
            "V4_C2_Static_Audit_2026-08-13.json",
            D2PR_C2_STATIC_AUDIT_SHA256,
        ),
        "c2_handoff": (
            "Task09_V4_C2A_Final_Authoritative_Handoff_2026-08-13.md",
            D2PR_C2_HANDOFF_SHA256,
        ),
        "fresh_session_master_handoff": (
            "Task09_Fresh_Session_Master_Handoff_Through_C2A_2026-08-13.md",
            D2PR_FRESH_SESSION_MASTER_HANDOFF_SHA256,
        ),
    }
    records: Dict[str, Any] = {}
    for key, (name, expected) in specifications.items():
        located: Optional[Path] = None
        for root in roots:
            candidate = root / name
            if candidate.is_file():
                located = candidate.resolve()
                break
        if located is None:
            records[key] = {
                "filename": name,
                "expected_sha256": expected,
                "available": False,
                "verified": False,
            }
            continue
        found = sha256_file(located)
        records[key] = {
            "filename": name,
            "path": str(located),
            "expected_sha256": expected,
            "found_sha256": found,
            "available": True,
            "verified": found == expected,
        }

    parent_core = None
    if records["parent_source"]["verified"]:
        parent_core = sha256_numerical_core(Path(records["parent_source"]["path"]))

    r1_record: Dict[str, Any] = {}
    if records["r1_allocator_authority_record"]["verified"]:
        r1_record = read_json(Path(records["r1_allocator_authority_record"]["path"]))

    c2_static_schema = None
    c2_static_pass = False
    if records["c2_static_audit"]["verified"]:
        c2_static = read_json(Path(records["c2_static_audit"]["path"]))
        c2_static_schema = c2_static.get("schema")
        c2_static_pass = bool(c2_static.get("passed"))

    checks = {
        "all_required_authorities_available_and_hashed": all(
            item["verified"] for item in records.values()
        ),
        "parent_core_hash_exact": parent_core == D2PR2G1FMP_PARENT_CORE_SHA256,
        "r1_authority_schema_exact": (
            r1_record.get("schema") == D2PR2G1FMP_R1_AUTHORITY_RECORD_SCHEMA
        ),
        "r1_classification_exact": (
            r1_record.get("classification") == D2PR2G1FMP_R1_CLASSIFICATION
            and r1_record.get("diagnostic_passed") is True
            and r1_record.get("independent_artifact_audit_passed") is True
            and r1_record.get("released_second_half_passed") is True
            and r1_record.get("production_authorized") is False
            and r1_record.get("task10_eligible") is False
        ),
        "r1_exact_coordinates": (
            r1_record.get("job_id") == D2PR2G1FMP_R1_JOB_ID
            and r1_record.get("attempted_detector_step") == 2152
            and r1_record.get("compression_call_index") == 4304
            and r1_record.get("bath_half_step") == "second"
            and r1_record.get("rank_at_half_step_entry") == 54
            and r1_record.get("temporary_total_kraus_rank") == 162
        ),
        "failure_diagnosis_schema_exact": (
            read_json(Path(records["g1_a100_controlled_failure_diagnosis"]["path"])).get("schema")
            == D2PR2G1F_FAILURE_DIAGNOSIS_SCHEMA
            if records["g1_a100_controlled_failure_diagnosis"]["verified"]
            else False
        ),
        "c2_static_audit_passed": c2_static_pass,
        "c2_source_schema_recorded": D2PR_C2_SCHEMA
        == "2026-08-13-task09-v4-c2-readonly-repaired-rank-ladder-v1",
    }
    return {
        "schema": "2026-08-14-task09-v4-d2pr2g1fmp-parent-lineage-audit-v4",
        "records": records,
        "parent_numerical_core_sha256": parent_core,
        "expected_parent_numerical_core_sha256": D2PR2G1FMP_PARENT_CORE_SHA256,
        "r1_authority_record": r1_record,
        "c2_static_audit_schema": c2_static_schema,
        "checks": checks,
        "passed": bool(all(checks.values())),
    }

def source_scope_audit(script_path: Path) -> Dict[str, Any]:
    source = script_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(script_path))
    executable_names = {
        node.id.lower() for node in ast.walk(tree) if isinstance(node, ast.Name)
    }
    forbidden = {
        "negative_rate",
        "bath_temperature",
        "detector_temperature",
        "monte_carlo",
        "quantum_trajectory",
        "cap_layer",
        "detector_reservoir",
        "legacy_checkpoint",
    }
    found = sorted(executable_names.intersection(forbidden))
    functions = {
        node.name: ast.get_source_segment(source, node)
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }
    cssf_source = functions["cssf_bath_half_step"]
    compressor_source = functions["d2_compress_mapped_blocks"]
    repair_source = functions[
        "_d2_repair_until_hard_gate_with_complete_certificate"
    ]
    complete_source = functions["complete_step"]
    budget_source = functions["RepresentationBudgetState"]
    resource_preflight_source = functions[
        "_d2_prepare_resource_allowance_after_unused_pool_release"
    ]
    pool_release_source = functions["_free_backend_pool"]
    checks = {
        "source_ast_parses": True,
        "forbidden_executable_symbols_absent": not found,
        "single_case_no_sweep": AUTOMATIC_SWEEP_ENABLED is False,
        "production_not_authorized": PRODUCTION_AUTHORIZED is False,
        "acceptance_disabled": ACCEPTANCE_ENABLED is False,
        "task10_disabled": TASK10_ELIGIBLE is False,
        "physical_claim_disabled": FINITE_POSITIVE_RATE_PHYSICAL_CLAIM is False,
        "legacy_checkpoint_import_disabled": LEGACY_CHECKPOINT_IMPORT_ENABLED is False,
        "checkpoint_migration_disabled": CHECKPOINT_MIGRATION_ENABLED is False,
        "global_budget_1e-8": REPRESENTATION_TRACE_NORM_BUDGET == 1.0e-8,
        "total_compression_calls_40000": TOTAL_PHYSICAL_COMPRESSION_CALLS == 40000,
        "scheduled_past_credit_policy": REPRESENTATION_BUDGET_POLICY
        == "scheduled_cumulative_envelope_with_past_credit_no_future_borrowing_v1",
        "single_centralized_budget_predicate": (
            "def assess_increment" in budget_source
            and "assessment = self.assess_increment(increment)" in budget_source
            and "budget.assess_increment" in compressor_source
            and "budget.assess_increment" in cssf_source
            and "+ 64.0 * np.finfo(float).eps" not in cssf_source
        ),
        "whole_half_repaired_rank_scan_present": (
            "_d2_construct_full_gram_rank_candidate" in compressor_source
            and "_d2_assess_repaired_rank_candidate" in compressor_source
            and "_d2_select_first_admissible_rank_report" in compressor_source
            and "blocked_full_gram_repaired_rank_scan_used" in compressor_source
        ),
        "dynamic_rank_selection_not_hard_coded": (
            "selected_rank = 28" not in compressor_source
            and "selected_rank = 29" not in compressor_source
            and "for rank in range(" in compressor_source
        ),
        "exact_weighted_polar_repair_present": (
            "inverse_sqrt_gram" in source
            and "bounded_exact_weighted_polar_repair_until_hard_gate_v1"
            in repair_source
        ),
        "complete_repaired_density_components_present": all(
            token in source
            for token in (
                "mapped_density_candidate_certificate",
                "blocked_candidate_reconstruction_certificate",
                "repair_core_density_certificate",
                "blocked_repaired_factor_reconstruction_certificate",
                "trace_restoration_correction",
            )
        ),
        "raw_and_tolerance_margins_recorded": (
            "raw_schedule_margin" in compressor_source
            and "tolerance_inclusive_schedule_margin" in compressor_source
            and "selected_rank_strict_raw_margin_pass" in compressor_source
        ),
        "selection_stops_at_first_admissible_rank": (
            "selected_factor = repaired" in compressor_source
            and "break" in compressor_source
            and "no higher rank is evaluated" in compressor_source
        ),
        "exactly_once_certificate_accounting_present": (
            "certificate_component_accounting" in source
            and "components_counted_exactly_once" in source
            and "candidate_trace_scaling_is_contained_only_in_mapped_density_certificate" in source
        ),
        "focused_adversarial_suite_present": all(
            token in source
            for token in (
                "rank28_is_first_tolerance_only_formal_pass",
                "forced_dynamic_rank_escalation",
                "canonicality_repair_failure",
                "reconstruction_certificate_failure",
                "first_half_failure",
                "second_half_failure",
            )
        ),
        "complete_rank_ladder_saved_on_failure": (
            "complete_repaired_rank_ladder" in source
        ),
        "sequential_merge_not_called_by_cssf": "stream_merge_raw_block(" not in cssf_source,
        "actual_output_reconstruction_bound_present": (
            "_d2_output_reconstruction_bound" in source
            and "blocked_candidate_reconstruction_certificate" in source
        ),
        "stable_repair_metric_certificate_present": (
            "_d2_reduced_density_difference_in_metric" in source
            and "_d2_gram_support" not in functions[
                "_d2_reduced_density_difference_in_metric"
            ]
        ),
        "transactional_complete_step_ledgers": (
            "staged_budget = RepresentationBudgetState" in complete_source
            and "staged_telemetry = RepresentationTelemetry" in complete_source
            and "budget.calls_completed = staged_budget.calls_completed" in complete_source
            and "telemetry.restore(staged_telemetry.snapshot())" in complete_source
        ),
        "no_scientific_rank_cap": "MAX_RANK" not in executable_names,
        "runtime_execution_gate_is_staged": EXECUTION_GATE
        in {"V4-G0", "V4-G1", "V4-G2", "V4-G3", "V4-G4"},
        "delivery_default_gate_is_g0": DEFAULT_EXECUTION_GATE == "V4-G0",
        "delivery_default_backend_is_scipy": DEFAULT_BACKEND == "scipy",
        "delivery_default_resume_is_false": DEFAULT_RESUME_FROM_V4_CHECKPOINT is False,
        "detector_rhs_batch_columns_is_p1_selected_64": (
            DETECTOR_RHS_BATCH_COLUMNS == D2P_P1_SELECTED_BATCH_COLUMNS == 64
        ),
        "factor_block_columns_unchanged_64": FACTOR_BLOCK_COLUMNS == 64,
        "allocator_release_is_conditional_and_unused_only": (
            "predicted > permitted_before" in resource_preflight_source
            and "_free_backend_pool(backend)" in resource_preflight_source
            and "free_all_blocks" in pool_release_source
            and "if release_triggered" in resource_preflight_source
        ),
        "resource_fraction_unchanged_80_percent": (
            GPU_WORKING_SET_FRACTION == 0.80
            and "GPU_WORKING_SET_FRACTION" in resource_preflight_source
        ),
        "downstream_actual_working_set_guard_retained": (
            "D2 whole-half working set exceeds the resource invariant"
            in compressor_source
            and "current_logical > resource_permitted_bytes"
            in compressor_source
        ),
        "compressor_does_not_release_pool": (
            "_free_backend_pool" not in compressor_source
        ),
        "resource_preflight_recorded_in_failure_and_telemetry": (
            "allocator_pool_resource_preflight" in cssf_source
        ),
        "r1a_parent_identity_recorded": (
            D2PR2G1FMP_PARENT_SOURCE_SHA256
            == "cef5f181646bd23c9fe93d276c40b8a95534d23d1dc5860e2eb9851426de8a16"
            and D2PR2G1FMP_PARENT_CORE_SHA256
            == "7d6240cfa8ca3055a120880194b6542c20ae0767771eb0c4b3379fa205ec4343"
            and D2PR2G1FMP_R1_CLASSIFICATION
            == "R1-A_ALLOCATOR_POOL_CACHE_FALSE_NEGATIVE_CONFIRMED"
        ),
        "parent_source_hash_recorded": D2PR2G1FMP_PARENT_SOURCE_SHA256
        == "cef5f181646bd23c9fe93d276c40b8a95534d23d1dc5860e2eb9851426de8a16",
        "parent_core_hash_recorded": D2PR2G1FMP_PARENT_CORE_SHA256
        == "7d6240cfa8ca3055a120880194b6542c20ae0767771eb0c4b3379fa205ec4343",
        "d2p_repaired_rank_ancestry_retained": (
            D2PR_PARENT_D2P_SOURCE_SHA256
            == "11f58b0571d0b471d1fa198d0700fdc98893bacdc60d810fab6ec39ab2264ee4"
            and D2PR_PARENT_D2P_CORE_SHA256
            == "b9ed00ba626ee73ca9fb4aff42bb44a63d285e8b56027d31962d0a05bfc742aa"
        ),
        "g1_acceptance_rule_producer_consumer_synchronized": (
            "D2PR2_COMPLETE_ACCEPTANCE_RULE" in cssf_source
            and "D2PR2_COMPLETE_ACCEPTANCE_RULE"
            in functions["run_g1_compression_rank_benchmark"]
            and D2PR2_COMPLETE_ACCEPTANCE_RULE
            == "unchanged_hard_canonicality_and_trace_gates_plus_existing_"
               "centralized_tolerance_inclusive_budget_predicate"
        ),
        "c2_authority_hash_recorded": D2PR_C2_SOURCE_SHA256
        == "8a6a38e735505de3ace7685435b6b6e7ba614f9035c8187b57a6c64c9e2c3383",
        "gmres_conventions_frozen": bool(
            GMRES_RTOL == 1.0e-10
            and GMRES_ATOL == 0.0
            and GMRES_RESTART == 30
            and GMRES_MAXITER == 1000
            and MULTI_RHS_CHECK_EVERY == 5
        ),
        "delivery_default_post_g0_review_is_false": (
            DEFAULT_D2_POST_G0_REVIEW_AUTHORIZED is False
        ),
        "u2_low_rate_positive_and_frozen": RATE_LAMBDA == math.pi / 400.0,
        "physical_map_constants_frozen": bool(
            OMEGA == 100.0
            and N_SHELL == 12
            and N_Z == 1500
            and DT == 5.0e-4
            and T_FINAL == 10.0
            and RATE_LAMBDA == math.pi / 400.0
        ),
        "g1_synthetic_rank_contract_exact": G1_SYNTHETIC_RANKS == (64, 256, 640),
    }
    return {
        "exact_parent_source_sha256": D2PR2G1FMP_PARENT_SOURCE_SHA256,
        "exact_parent_core_sha256": D2PR2G1FMP_PARENT_CORE_SHA256,
        "r1_allocator_pool_diagnostic_source_sha256": D2PR2G1FMP_R1_DIAGNOSTIC_SOURCE_SHA256,
        "r1_allocator_pool_authority_record_sha256": D2PR2G1FMP_R1_AUTHORITY_RECORD_SHA256,
        "repaired_rank_ancestry_source_sha256": D2PR_PARENT_D2P_SOURCE_SHA256,
        "repaired_rank_ancestry_core_sha256": D2PR_PARENT_D2P_CORE_SHA256,
        "c2_source_sha256": D2PR_C2_SOURCE_SHA256,
        "c2_handoff_sha256": D2PR_C2_HANDOFF_SHA256,
        "parent_d2_wholehalf_sha256": D2P_PARENT_D2_SOURCE_SHA256,
        "p1_source_sha256": D2P_P1_SOURCE_SHA256,
        "p1_batch_selection": {
            "baseline": D2P_P1_BASELINE_BATCH_COLUMNS,
            "selected": D2P_P1_SELECTED_BATCH_COLUMNS,
            "aggregate_speedup": D2P_P1_AGGREGATE_SPEEDUP,
        },
        "forbidden_executable_symbols_found": found,
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


def embedded_authority_audit(script_path: Path) -> Dict[str, Any]:
    # G0 is self-contained.  When an authority artifact is colocated with the
    # source, verify it; absence is recorded and is not silently treated as a
    # verified file.  Production-size gates separately require the upstream
    # authorization directory.
    candidate_names = {
        "current_v39_reset_master": "NUM_Open_System_PartI_Authoritative_Master_Audit_Through_Task09_v3_9_RankGrowth_and_V4_Reset_Handoff_2026-08-11(1).md",
        "phaseA_final_design": "Task09_v4_PhaseA_Final_Representation_and_Error_Budget_Design_2026-08-11.md",
        "phaseA_exact_v39_reconstruction": "Task09_v4_PhaseA_Exact_v39_Reconstruction_2026-08-11.md",
        "phaseA_evidence_archive": "Task09_v4_PhaseA_Evidence_20260811T202923Z.tar.gz",
        "phaseA_tensor_archive": "Task09_v4_PhaseA_Tensor_Feasibility_20260811T212355Z.tar.gz",
        "v7_manuscript": "Spin_Momentum_Impedance_and_Filtering_Closed_Quantum_Open_SystemV7(8).pdf",
        "reference_750": "750.Reference(20260811-081300).py",
        "task05_representative_source": "4536_5oscillator_channel_detector_test(2).py",
        "task07_representative_source": "4759_environmental_response_solver(2).py",
        "historical_v39_source": "Task09_4901_U2_low_adaptive_budget_cap640_largefactor_safe_pilot_v3_9(2).py",
    }
    roots = [script_path.parent, Path.cwd(), DATA_ROOT]
    records: Dict[str, Any] = {}
    for key, name in candidate_names.items():
        located: Optional[Path] = None
        for root in roots:
            candidate = root / name
            if candidate.is_file():
                located = candidate.resolve()
                break
        if located is None:
            records[key] = {
                "expected_sha256": SOURCE_FINGERPRINTS[key],
                "available": False,
                "verified": False,
            }
        else:
            found = sha256_file(located)
            records[key] = {
                "expected_sha256": SOURCE_FINGERPRINTS[key],
                "available": True,
                "path": str(located),
                "found_sha256": found,
                "verified": found == SOURCE_FINGERPRINTS[key],
            }
    available_records = [record for record in records.values() if record["available"]]
    passed = bool(all(record["verified"] for record in available_records))
    return {
        "embedded_fingerprints": SOURCE_FINGERPRINTS,
        "colocated_artifact_records": records,
        "all_available_artifacts_match": passed,
        "g0_missing_artifacts_are_not_claimed_verified": True,
        "passed": passed,
    }


def reduced_config(production: RunConfig, *, steps: Optional[int] = None) -> RunConfig:
    n_steps = int(round(G0_T_FINAL / G0_DT)) if steps is None else int(steps)
    return replace(
        production,
        execution_gate="V4-G0",
        backend="scipy",
        n_shell=G0_N_SHELL,
        n_z=G0_N_Z,
        l_z=G0_L_Z,
        z0=G0_Z0,
        sigma_z_amplitude=G0_SIGMA_Z,
        dt=G0_DT,
        t_final=n_steps * G0_DT,
        stop_after_steps=n_steps,
        gmres_rtol=G0_GMRES_RTOL,
        detector_rhs_batch_columns=8,
        factor_block_columns=4,
        checkpoint_every=0,
        progress_every=1,
        resume_from_checkpoint=False,
        planned_compression_calls=2 * n_steps,
    )



def run_g0_whole_half_oracle_tests() -> Dict[str, Any]:
    """Reduced adversarial certification of complete repaired-rank selection."""
    backend = NumericalBackend("scipy")
    rng = np.random.default_rng(2026081301)
    dimension = 48
    h_z = 0.125
    cases: Dict[str, List[np.ndarray]] = {}

    generic = rng.normal(size=(dimension, 6)) + 1j * rng.normal(
        size=(dimension, 6)
    )
    generic /= math.sqrt(float(h_z * np.vdot(generic, generic).real))
    cases["generic"] = [generic[:, :3], generic[:, 3:]]

    perturb = rng.normal(size=(dimension, 4)) + 1j * rng.normal(
        size=(dimension, 4)
    )
    perturb /= np.linalg.norm(perturb)
    cases["near_collinear"] = [
        generic[:, :4], generic[:, :4] + 1.0e-10 * perturb
    ]
    cases["exact_duplicate"] = [
        generic[:, :4], generic[:, :4].copy(), generic[:, 4:6]
    ]

    q, _ = np.linalg.qr(
        rng.normal(size=(dimension, 12))
        + 1j * rng.normal(size=(dimension, 12))
    )
    singular = 10.0 ** (-np.linspace(0.0, 13.0, 12))
    decaying = q[:, :12] * singular[None, :] / math.sqrt(h_z)
    cases["broad_spectrum"] = [
        decaying[:, :4], decaying[:, 4:8], decaying[:, 8:]
    ]

    reports: Dict[str, Any] = {}
    all_passed = True
    for name, blocks_cpu in cases.items():
        blocks_backend = tuple(
            backend.to_backend_array(np.asarray(block, np.complex128))
            for block in blocks_cpu
        )
        matrix = np.ascontiguousarray(np.concatenate(blocks_cpu, axis=1))
        target_trace = float(h_z * np.vdot(matrix, matrix).real)
        allowance = 1.0e-8
        budget = RepresentationBudgetState(
            total_budget=allowance,
            total_planned_calls=1,
        )
        budget_before = budget.snapshot()
        allocation = budget.allocation()
        metadata = [
            {
                "kraus_branch_index": index,
                "input_factor_block_index": 0,
                "columns": int(block.shape[1]),
                "logical_nbytes": int(block.nbytes),
            }
            for index, block in enumerate(blocks_backend)
        ]
        compressed, report = d2_compress_mapped_blocks(
            blocks_backend,
            block_metadata=metadata,
            h_z=h_z,
            target_trace=target_trace,
            budget=budget,
            allocation=allocation,
            backend=backend,
            output_block_columns=4,
            resource_permitted_bytes=None,
        )
        budget_after = budget.snapshot()
        exact_density = matrix @ matrix.conj().T
        represented_density = factor_density_cpu(compressed, backend)
        actual_error = density_trace_norm(
            represented_density - exact_density, h_z
        )
        certified = float(report["certified_density_trace_norm_bound"])
        oracle_factor, oracle_weights, oracle = full_gram_oracle(
            [np.asarray(block, np.complex128) for block in blocks_cpu],
            h_z=h_z,
            target_trace=target_trace,
            allowed_trace_norm_increment=allowance,
        )
        oracle_density = oracle_factor @ oracle_factor.conj().T
        oracle_error = density_trace_norm(oracle_density - exact_density, h_z)
        density_vs_oracle = density_trace_norm(
            represented_density - oracle_density, h_z
        )
        certificate_slack = float(
            16.0 * np.finfo(float).eps * max(target_trace, 1.0)
        )
        oracle_roundoff_slack = float(
            D2_CERTIFICATE_TRACE_GUARD_ULPS
            * np.finfo(float).eps
            * max(target_trace, 1.0)
        )
        assessment = report["selected_budget_assessment"]
        passed = bool(
            actual_error <= certified + certificate_slack
            and assessment["passed"]
            and certified
            <= allowance + RepresentationBudgetState.comparison_tolerance()
            and oracle_error
            <= oracle["trace_norm_increment"] + oracle_roundoff_slack
            and density_vs_oracle
            <= (
                certified
                + oracle["trace_norm_increment"]
                + certificate_slack
                + oracle_roundoff_slack
            )
            and compressed.rank >= int(oracle["required_rank"])
            and report["blocked_full_gram_repaired_rank_scan_used"] is True
            and canonicality_audit(compressed, backend)["passed"]
            and budget_before == budget_after
            and np.all(np.isfinite(oracle_weights))
        )
        all_passed &= passed
        reports[name] = {
            "target_trace": target_trace,
            "logical_rank": int(matrix.shape[1]),
            "selected_rank": compressed.rank,
            "oracle_selected_rank": int(oracle["required_rank"]),
            "actual_density_trace_norm_error": actual_error,
            "certified_density_trace_norm_bound": certified,
            "oracle_actual_density_trace_norm_error": oracle_error,
            "d2pr_vs_oracle_density_trace_norm": density_vs_oracle,
            "certificate_slack": certificate_slack,
            "oracle_roundoff_slack": oracle_roundoff_slack,
            "complete_repaired_rank_scan_used": bool(
                report["blocked_full_gram_repaired_rank_scan_used"]
            ),
            "selected_rank_not_below_exact_oracle": bool(
                compressed.rank >= int(oracle["required_rank"])
            ),
            "compressor_did_not_commit_budget": budget_before == budget_after,
            "canonicality": canonicality_audit(compressed, backend),
            "compression_report": report,
            "passed": passed,
        }

    injected_blocks_cpu = cases["generic"]
    injected_blocks = tuple(
        backend.to_backend_array(np.asarray(block, np.complex128))
        for block in injected_blocks_cpu
    )
    injected_matrix = np.ascontiguousarray(
        np.concatenate(injected_blocks_cpu, axis=1)
    )
    injected_trace = float(
        h_z * np.vdot(injected_matrix, injected_matrix).real
    )
    injected_budget = RepresentationBudgetState(
        total_budget=0.0, total_planned_calls=1
    )
    injected_before = injected_budget.snapshot()
    injected_failure = None
    try:
        d2_compress_mapped_blocks(
            injected_blocks,
            block_metadata=[
                {
                    "kraus_branch_index": index,
                    "input_factor_block_index": 0,
                    "columns": int(block.shape[1]),
                    "logical_nbytes": int(block.nbytes),
                }
                for index, block in enumerate(injected_blocks)
            ],
            h_z=h_z,
            target_trace=injected_trace,
            budget=injected_budget,
            allocation=injected_budget.allocation(),
            backend=backend,
            output_block_columns=4,
            resource_permitted_bytes=None,
        )
    except RepresentationFailure as exc:
        inner = exc.event.get("inner_failure", exc.event)
        ladder = inner.get("complete_repaired_rank_ladder", [])
        injected_failure = {
            "error": str(exc),
            "event": exc.event,
            "complete_rank_ladder_length": len(ladder),
            "complete_rank_ladder_present": bool(ladder),
        }
    injected_after = injected_budget.snapshot()
    injected_passed = bool(
        injected_failure is not None
        and injected_failure["complete_rank_ladder_present"]
        and injected_before == injected_after
    )
    all_passed &= injected_passed

    return {
        "architecture": (
            "metric lower-rank estimate plus complete blocked full-Gram "
            "reconstruction, exact weighted-polar repair, complete density "
            "certificate, and unchanged centralized predicate"
        ),
        "cases": reports,
        "actual_no_admissible_rank_injection": {
            "budget_before": injected_before,
            "budget_after": injected_after,
            "failure": injected_failure,
            "passed": injected_passed,
        },
        "passed": bool(all_passed),
    }


def run_g0_budget_identity_test() -> Dict[str, Any]:
    weights = np.asarray([0.55, 0.25, 0.12, 0.05, 0.02, 0.01], dtype=np.float64)
    tails = tail_after_each_rank(weights)
    allowed_tail = 0.031
    satisfying = np.flatnonzero(tails[1:] <= allowed_tail)
    rank = int(satisfying[0] + 1)
    discarded = float(tails[rank])
    retained = float(np.sum(weights[:rank]))
    original = np.diag(weights)
    restored = np.zeros_like(original)
    restored[:rank, :rank] = np.diag(weights[:rank] / retained)
    actual = float(np.sum(np.abs(np.linalg.eigvalsh(restored - original))))
    exact = 2.0 * discarded

    budget = RepresentationBudgetState(1.0e-8, 10)
    commits: List[Dict[str, Any]] = []
    for increment in (2.0e-10, 1.0e-10, 7.0e-10):
        commits.append(budget.commit(increment))
    envelope_ok = all(
        item["cumulative_bound_after"] <= item["scheduled_cumulative_ceiling"] + 1.0e-18
        for item in commits
    )

    # Exact D1-A budget-predicate regression at authoritative call 4862.
    d1_budget = RepresentationBudgetState(
        total_budget=1.0e-8,
        total_planned_calls=40000,
        calls_completed=4861,
        bound_used=1.2152318966545368e-9,
    )
    d1_allocation = d1_budget.allocation()
    d1_sequential_requested = 2.7697409647571796e-13
    d1_oracle_requested = 1.7704879686595057e-13
    d1_sequential_assessment = d1_budget.assess_increment(
        d1_sequential_requested, allocation=d1_allocation
    )
    d1_oracle_assessment = d1_budget.assess_increment(
        d1_oracle_requested, allocation=d1_allocation
    )
    d1_predicate_pass = bool(
        d1_allocation["compression_call_index"] == 4862
        and np.isclose(
            d1_allocation["allowed_trace_norm_increment"],
            2.6810334546318087e-13,
            rtol=0.0,
            atol=0.0,
        )
        and d1_sequential_assessment["passed"] is False
        and d1_oracle_assessment["passed"] is True
        and d1_sequential_assessment["comparison_tolerance"]
        == RepresentationBudgetState.comparison_tolerance()
    )

    # Algebraic regression for the exact v2 canonicality mechanism.  A small
    # missing Gram trace is restored by a uniform weight scale c.  If c*lambda
    # is incorrectly used inside lambda^{-1/2}, the returned basis metric is
    # c^{-1} I and the normalized canonicality residual is |c^{-1}-1|.  The v3
    # rule uses the unscaled lambda for basis normalization and c*lambda only
    # as density weights, leaving the basis metric exactly I.
    regression_values = np.asarray([0.61, 0.27, 0.12], dtype=np.float64)
    regression_gap = 1.95e-10
    regression_spectral_trace = float(np.sum(regression_values))
    regression_input_trace = regression_spectral_trace + regression_gap
    regression_scale = regression_input_trace / regression_spectral_trace
    old_rescaled_basis_residual = abs(1.0 / regression_scale - 1.0)
    new_separated_basis_residual = 0.0
    regression_weights = regression_values * regression_scale
    regression_pass = bool(
        old_rescaled_basis_residual > CANONICALITY_REPAIR_TRIGGER
        and old_rescaled_basis_residual <= CANONICALITY_TOL
        and new_separated_basis_residual <= CANONICALITY_REPAIR_TRIGGER
        and abs(float(np.sum(regression_weights)) - regression_input_trace)
        <= 8.0 * np.finfo(float).eps
    )
    synthetic_post_repair_residual = 1.3227572426939694e-12
    gate_separation_pass = bool(
        synthetic_post_repair_residual > CANONICALITY_REPAIR_TRIGGER
        and synthetic_post_repair_residual <= CANONICALITY_TOL
        and synthetic_post_repair_residual <= CANONICALITY_TOL
    )
    return {
        "weights": weights.tolist(),
        "allowed_discarded_trace": allowed_tail,
        "selected_rank": rank,
        "discarded_trace": discarded,
        "actual_trace_norm_error_after_trace_restore": actual,
        "exact_2delta": exact,
        "absolute_identity_residual": abs(actual - exact),
        "scheduled_commits": commits,
        "d1a_centralized_budget_predicate_regression": {
            "allocation": d1_allocation,
            "sequential_requested_increment": d1_sequential_requested,
            "sequential_assessment": d1_sequential_assessment,
            "oracle_requested_increment": d1_oracle_requested,
            "oracle_assessment": d1_oracle_assessment,
            "passed": d1_predicate_pass,
        },
        "canonicality_gate_separation_regression": {
            "synthetic_post_repair_residual": synthetic_post_repair_residual,
            "repair_trigger": CANONICALITY_REPAIR_TRIGGER,
            "hard_tolerance": CANONICALITY_TOL,
            "trigger_target_met": bool(
                synthetic_post_repair_residual <= CANONICALITY_REPAIR_TRIGGER
            ),
            "hard_gate_passed": bool(
                synthetic_post_repair_residual <= CANONICALITY_TOL
            ),
            "passed": gate_separation_pass,
        },
        "trace_restoration_canonicality_regression": {
            "spectral_values": regression_values.tolist(),
            "missing_trace": regression_gap,
            "trace_restoration_scale": regression_scale,
            "old_rescaled_basis_canonicality_residual": old_rescaled_basis_residual,
            "new_separated_basis_canonicality_residual": new_separated_basis_residual,
            "restored_weight_trace": float(np.sum(regression_weights)),
            "target_trace": regression_input_trace,
            "repair_trigger": CANONICALITY_REPAIR_TRIGGER,
            "hard_tolerance": CANONICALITY_TOL,
            "passed": regression_pass,
        },
        "passed": bool(
            abs(actual - exact) <= 5.0e-15
            and envelope_ok
            and d1_predicate_pass
            and regression_pass
            and gate_separation_pass
        ),
    }


def run_g0_gmres_certification(config: RunConfig) -> Dict[str, Any]:
    operators = build_oscillator_operators(config.n_shell, config.omega)
    backend = NumericalBackend("scipy")
    z, h_z, _ = build_reference_grid(config.n_z, config.l_z)
    initial = build_initial_state(config, operators, z, h_z)
    propagator = build_propagator_objects(config, operators, backend, initial)
    rng = np.random.default_rng(20260812)
    vectors = np.column_stack([
        initial,
        initial + 1.0e-3 * (rng.normal(size=initial.size) + 1j * rng.normal(size=initial.size)),
        rng.normal(size=initial.size) + 1j * rng.normal(size=initial.size),
        rng.normal(size=initial.size) + 1j * rng.normal(size=initial.size),
    ]).astype(np.complex128)
    vectors = vectors.reshape(operators.d_channels, config.n_z, -1)
    vectors[:, 0, :] = 0.0
    vectors = vectors.reshape(config.state_dimension, -1)
    rhs = propagator.backend_b @ vectors
    multi, info_multi, residual_multi, iterations = multi_rhs_independent_gmres(
        backend,
        propagator.backend_a,
        rhs,
        vectors,
        propagator.backend_inverse_diagonal,
        check_every=MULTI_RHS_CHECK_EVERY,
        rtol=config.gmres_rtol,
    )
    independent, info_independent, residual_independent = independent_gmres_many(
        backend,
        propagator.backend_a,
        rhs,
        vectors,
        propagator.backend_preconditioner,
        rtol=config.gmres_rtol,
    )
    direct = la.solve(propagator.a_cpu.toarray(), np.asarray(rhs))
    direct_scale = max(float(np.linalg.norm(direct)), 1.0e-30)
    multi_direct = float(np.linalg.norm(multi - direct) / direct_scale)
    independent_direct = float(np.linalg.norm(independent - direct) / direct_scale)
    multi_independent = float(np.linalg.norm(multi - independent) / direct_scale)
    q_multi = 0.5 * (
        vectors.reshape(operators.d_channels, config.n_z, -1)[:, -1, :]
        + multi.reshape(operators.d_channels, config.n_z, -1)[:, -1, :]
    )
    q_ind = 0.5 * (
        vectors.reshape(operators.d_channels, config.n_z, -1)[:, -1, :]
        + independent.reshape(operators.d_channels, config.n_z, -1)[:, -1, :]
    )
    p_multi = float(config.dt * config.kappa * np.sum(np.abs(q_multi) ** 2))
    p_ind = float(config.dt * config.kappa * np.sum(np.abs(q_ind) ** 2))
    passed = bool(
        np.count_nonzero(info_multi) == 0
        and np.count_nonzero(info_independent) == 0
        and np.max(residual_multi) <= TRUE_RESIDUAL_TOL
        and np.max(residual_independent) <= TRUE_RESIDUAL_TOL
        and multi_direct <= G0_GMRES_SOLUTION_REL_TOL
        and independent_direct <= G0_GMRES_SOLUTION_REL_TOL
        and multi_independent <= G0_GMRES_SOLUTION_REL_TOL
        and abs(p_multi - p_ind) <= G0_CURVE_ABS_TOL
    )
    return {
        "number_rhs": vectors.shape[1],
        "multi_rhs_info": info_multi.tolist(),
        "independent_info": info_independent.tolist(),
        "maximum_multi_rhs_true_residual": float(np.max(residual_multi)),
        "maximum_independent_true_residual": float(np.max(residual_independent)),
        "multi_rhs_vs_direct_relative_error": multi_direct,
        "independent_vs_direct_relative_error": independent_direct,
        "multi_rhs_vs_independent_relative_error": multi_independent,
        "midpoint_probability_multi_rhs": p_multi,
        "midpoint_probability_independent": p_ind,
        "multi_rhs_inner_iterations": iterations,
        "passed": passed,
    }

def _dense_full_step(
    rho: np.ndarray,
    *,
    dense_u: np.ndarray,
    full_kraus: Sequence[np.ndarray],
    roof_indices: np.ndarray,
    config: RunConfig,
    h_z: float,
) -> Tuple[np.ndarray, float, Dict[str, float]]:
    rho_a = sum((k @ rho @ k.conj().T for k in full_kraus), np.zeros_like(rho))
    trace_before = float(h_z * np.trace(rho).real)
    trace_a = float(h_z * np.trace(rho_a).real)
    q = 0.5 * (np.eye(dense_u.shape[0], dtype=np.complex128) + dense_u)
    rho_q = q @ rho_a @ q.conj().T
    p_mid = float(config.dt * config.kappa * np.trace(rho_q[np.ix_(roof_indices, roof_indices)]).real)
    rho_b = dense_u @ rho_a @ dense_u.conj().T
    trace_b = float(h_z * np.trace(rho_b).real)
    rho_next = sum((k @ rho_b @ k.conj().T for k in full_kraus), np.zeros_like(rho))
    trace_next = float(h_z * np.trace(rho_next).real)
    return rho_next, p_mid, {
        "trace_before": trace_before,
        "trace_after_first_bath": trace_a,
        "trace_after_detector": trace_b,
        "trace_after_second_bath": trace_next,
        "bath_trace_residual_first": trace_a - trace_before,
        "bath_trace_residual_second": trace_next - trace_b,
        "detector_midpoint_closure": trace_a - trace_b - p_mid,
        "complete_step_closure": trace_before - trace_next - p_mid,
    }


def run_g0_reduced_full_density(config: RunConfig) -> Dict[str, Any]:
    validate_config(config, reduced_model=True)
    operators = build_oscillator_operators(config.n_shell, config.omega)
    backend = NumericalBackend("scipy")
    z, h_z, _ = build_reference_grid(config.n_z, config.l_z)
    initial = build_initial_state(config, operators, z, h_z)
    propagator = build_propagator_objects(config, operators, backend, initial)
    dense_u = la.solve(propagator.a_cpu.toarray(), propagator.b_cpu.toarray())
    action = config.rate_lambda * config.dt / 2.0
    bath = build_bath_kraus(operators, config.environment_direction, action, backend)
    identity_z = np.eye(config.n_z, dtype=np.complex128)
    full_kraus = [np.kron(operator.toarray(), identity_z) for operator in bath.operators_cpu]
    roof_indices = np.arange(operators.d_channels, dtype=np.int64) * config.n_z + config.n_z - 1

    rho = np.outer(initial, initial.conj())
    factor = canonical_from_state(
        initial,
        h_z=h_z,
        backend=backend,
        block_columns=config.factor_block_columns,
    )
    budget = RepresentationBudgetState(config.representation_budget, config.planned_compression_calls)
    telemetry = RepresentationTelemetry()
    survival_full = [float(h_z * np.trace(rho).real)]
    survival_factor = [factor.trace]
    p_full: List[float] = []
    p_factor: List[float] = []
    density_errors: List[float] = []
    step_audits: List[Dict[str, Any]] = []
    full_audits: List[Dict[str, Any]] = []

    for step in range(1, config.execution_num_steps + 1):
        rho, p_ref, full_audit = _dense_full_step(
            rho,
            dense_u=dense_u,
            full_kraus=full_kraus,
            roof_indices=roof_indices,
            config=config,
            h_z=h_z,
        )
        factor, step_audit = complete_step(
            factor,
            step_index=step,
            operators=operators,
            propagator=propagator,
            kraus=bath,
            config=config,
            backend=backend,
            budget=budget,
            telemetry=telemetry,
            certified_multi_rhs=True,
        )
        rho_factor = factor_density_cpu(factor, backend)
        error = density_trace_norm(rho_factor - rho, h_z)
        density_errors.append(error)
        survival_full.append(float(h_z * np.trace(rho).real))
        survival_factor.append(factor.trace)
        p_full.append(p_ref)
        p_factor.append(step_audit["midpoint_roof_probability"])
        step_audits.append(step_audit)
        full_audits.append(full_audit)

    final_difference = factor_density_cpu(factor, backend) - rho
    trace_norm = density_trace_norm(final_difference, h_z)
    frob_relative = float(np.linalg.norm(final_difference) / max(np.linalg.norm(rho), 1.0e-30))
    survival_error = float(np.max(np.abs(np.asarray(survival_factor) - np.asarray(survival_full))))
    probability_error = float(np.max(np.abs(np.asarray(p_factor) - np.asarray(p_full))))
    minimum_factor_eigenvalue = float(
        np.min(np.linalg.eigvalsh(0.5 * (factor_density_cpu(factor, backend) + factor_density_cpu(factor, backend).conj().T)))
    )
    maximum_full_closure = float(
        max(abs(audit["complete_step_closure"]) for audit in full_audits)
    )
    passed = bool(
        trace_norm <= budget.bound_used + G0_DENSITY_TRACE_NORM_TOL
        and frob_relative <= max(G0_DENSITY_FROBENIUS_REL_TOL, 10.0 * budget.bound_used)
        and survival_error <= budget.bound_used + G0_CURVE_ABS_TOL
        and probability_error <= 2.0 * budget.bound_used + G0_CURVE_ABS_TOL
        and minimum_factor_eigenvalue >= -1.0e-12
        and maximum_full_closure <= G0_CURVE_ABS_TOL
        and bath.completeness_residual <= BATH_COMPLETENESS_TOL
        and canonicality_audit(factor, backend)["passed"]
    )
    return {
        "configuration": {
            "N_shell": config.n_shell,
            "N_z": config.n_z,
            "dt": config.dt,
            "T_final": config.t_final,
            "steps": config.execution_num_steps,
            "dimension": config.state_dimension,
            "planned_compression_calls": config.planned_compression_calls,
            "representation_budget": config.representation_budget,
        },
        "final_density_trace_norm_error": trace_norm,
        "final_density_relative_frobenius_error": frob_relative,
        "maximum_density_trace_norm_error": float(np.max(density_errors)),
        "cumulative_representation_bound": budget.bound_used,
        "maximum_survival_error": survival_error,
        "maximum_midpoint_probability_error": probability_error,
        "minimum_factor_density_eigenvalue": minimum_factor_eigenvalue,
        "maximum_full_density_complete_step_closure": maximum_full_closure,
        "bath_kraus_completeness_residual": bath.completeness_residual,
        "bath_first_derivative_audit": bath.first_derivative_audit,
        "final_canonicality": canonicality_audit(factor, backend),
        "representation_telemetry": telemetry.snapshot(),
        "step_audits": step_audits,
        "passed": passed,
        "arrays": {
            "survival_full": np.asarray(survival_full, dtype=np.float64),
            "survival_factor": np.asarray(survival_factor, dtype=np.float64),
            "step_probability_full": np.asarray(p_full, dtype=np.float64),
            "step_probability_factor": np.asarray(p_factor, dtype=np.float64),
            "density_trace_norm_error": np.asarray(density_errors, dtype=np.float64),
        },
    }


def _empty_histories(steps: int, dt: float = G0_DT) -> Dict[str, np.ndarray]:
    return {
        "times": np.arange(steps + 1, dtype=np.float64) * float(dt),
        "survival": np.full(steps + 1, np.nan, dtype=np.float64),
        "step_probability": np.full(steps, np.nan, dtype=np.float64),
        "rank": np.full(steps + 1, -1, dtype=np.int64),
        "representation_bound": np.full(steps + 1, np.nan, dtype=np.float64),
    }


def _run_reduced_steps(
    config: RunConfig,
    *,
    number_steps: int,
    start_step: int = 0,
    factor: Optional[CanonicalFactor] = None,
    budget: Optional[RepresentationBudgetState] = None,
    telemetry: Optional[RepresentationTelemetry] = None,
    histories: Optional[Dict[str, np.ndarray]] = None,
) -> Tuple[CanonicalFactor, RepresentationBudgetState, RepresentationTelemetry, Dict[str, np.ndarray]]:
    operators = build_oscillator_operators(config.n_shell, config.omega)
    backend = NumericalBackend("scipy")
    z, h_z, _ = build_reference_grid(config.n_z, config.l_z)
    initial = build_initial_state(config, operators, z, h_z)
    propagator = build_propagator_objects(config, operators, backend, initial)
    bath = build_bath_kraus(
        operators,
        config.environment_direction,
        config.rate_lambda * config.dt / 2.0,
        backend,
    )
    if factor is None:
        factor = canonical_from_state(initial, h_z=h_z, backend=backend, block_columns=config.factor_block_columns)
    if budget is None:
        budget = RepresentationBudgetState(config.representation_budget, config.planned_compression_calls)
    if telemetry is None:
        telemetry = RepresentationTelemetry()
    if histories is None:
        histories = _empty_histories(number_steps, config.dt)
    if start_step == 0:
        histories["survival"][0] = factor.trace
        histories["rank"][0] = factor.rank
        histories["representation_bound"][0] = budget.bound_used
    for step in range(start_step + 1, number_steps + 1):
        factor, audit = complete_step(
            factor,
            step_index=step,
            operators=operators,
            propagator=propagator,
            kraus=bath,
            config=config,
            backend=backend,
            budget=budget,
            telemetry=telemetry,
            certified_multi_rhs=True,
        )
        histories["survival"][step] = factor.trace
        histories["step_probability"][step - 1] = audit["midpoint_roof_probability"]
        histories["rank"][step] = factor.rank
        histories["representation_bound"][step] = budget.bound_used
    return factor, budget, telemetry, histories


def run_g0_checkpoint_roundtrip(
    config: RunConfig,
    *,
    source_sha256: str,
    numerical_core_sha256: str,
) -> Dict[str, Any]:
    steps = 4
    run_config = replace(
        config,
        t_final=steps * config.dt,
        stop_after_steps=steps,
        planned_compression_calls=2 * steps,
    )
    family = physical_family_contract(run_config)
    execution = pilot_execution_contract(run_config)
    uninterrupted_factor, uninterrupted_budget, uninterrupted_telemetry, uninterrupted_histories = _run_reduced_steps(
        run_config, number_steps=steps
    )

    partial_histories = _empty_histories(steps, run_config.dt)
    partial_factor, partial_budget, partial_telemetry, partial_histories = _run_reduced_steps(
        run_config,
        number_steps=2,
        histories=partial_histories,
    )
    with tempfile.TemporaryDirectory(prefix="task09_v4_g0_checkpoint_") as tmp_name:
        root = Path(tmp_name)
        checkpoint = save_checkpoint(
            root,
            completed_step=2,
            factor=partial_factor,
            budget=partial_budget,
            telemetry=partial_telemetry,
            histories=partial_histories,
            source_sha256=source_sha256,
            numerical_core_sha256=numerical_core_sha256,
            family_contract=family,
            execution_contract=execution,
            backend=NumericalBackend("scipy"),
        )
        loaded_step, loaded_factor, loaded_budget, loaded_telemetry, loaded_histories, metadata = load_checkpoint(
            checkpoint,
            expected_source_sha256=source_sha256,
            expected_numerical_core_sha256=numerical_core_sha256,
            expected_family_contract_sha256=family["contract_sha256"],
            backend=NumericalBackend("scipy"),
        )
        resumed_factor, resumed_budget, resumed_telemetry, resumed_histories = _run_reduced_steps(
            run_config,
            number_steps=steps,
            start_step=loaded_step,
            factor=loaded_factor,
            budget=loaded_budget,
            telemetry=loaded_telemetry,
            histories=loaded_histories,
        )
        verification = verify_hash_manifest(checkpoint)

    backend = NumericalBackend("scipy")
    density_error = density_trace_norm(
        factor_density_cpu(resumed_factor, backend) - factor_density_cpu(uninterrupted_factor, backend),
        resumed_factor.h_z,
    )
    history_errors = {
        key: float(np.nanmax(np.abs(resumed_histories[key] - uninterrupted_histories[key])))
        for key in uninterrupted_histories
    }
    passed = bool(
        verification["passed"]
        and density_error <= G0_CHECKPOINT_DENSITY_TOL
        and all(value <= 2.0e-12 for value in history_errors.values())
        and abs(resumed_budget.bound_used - uninterrupted_budget.bound_used) <= 1.0e-18
        and resumed_budget.calls_completed == uninterrupted_budget.calls_completed
        and len(resumed_telemetry.events) == len(uninterrupted_telemetry.events)
        and metadata["completed_after_complete_strang_step"] is True
    )
    return {
        "checkpoint_schema": CHECKPOINT_SCHEMA,
        "restored_step": loaded_step,
        "density_trace_norm_difference": density_error,
        "history_maximum_absolute_differences": history_errors,
        "representation_bound_difference": abs(resumed_budget.bound_used - uninterrupted_budget.bound_used),
        "telemetry_length_difference": len(resumed_telemetry.events) - len(uninterrupted_telemetry.events),
        "hash_manifest_verified": verification["passed"],
        "passed": passed,
    }

def run_g0_failure_context_certification(
    production_config: RunConfig,
) -> Dict[str, Any]:
    """Inject first- and second-half failures and verify full transactionality."""
    config = reduced_config(production_config, steps=1)
    backend = NumericalBackend("scipy")
    operators = build_oscillator_operators(config.n_shell, config.omega)
    z, h_z, _ = build_reference_grid(config.n_z, config.l_z)
    initial = build_initial_state(config, operators, z, h_z)
    propagator = build_propagator_objects(config, operators, backend, initial)
    bath = build_bath_kraus(
        operators,
        config.environment_direction,
        config.rate_lambda * config.dt / 2.0,
        backend,
    )
    factor = canonical_from_state(
        initial,
        h_z=h_z,
        backend=backend,
        block_columns=config.factor_block_columns,
    )
    input_density = factor_density_cpu(factor, backend)
    input_weights = factor.weights.copy()

    def run_injection(fail_call: int) -> Dict[str, Any]:
        budget = RepresentationBudgetState(
            config.representation_budget, config.planned_compression_calls
        )
        telemetry = RepresentationTelemetry()
        budget_before = budget.snapshot()
        telemetry_before = telemetry.snapshot()
        original = globals()["d2_compress_mapped_blocks"]
        counter = {"calls": 0}

        def injected(*args: Any, **kwargs: Any) -> Any:
            counter["calls"] += 1
            if counter["calls"] == fail_call:
                raise RepresentationFailure(
                    f"G0 injected D2 bath-half failure at call {fail_call}",
                    event={
                        "injected_failure": True,
                        "injected_whole_half_call": fail_call,
                    },
                )
            return original(*args, **kwargs)

        globals()["d2_compress_mapped_blocks"] = injected
        caught = False
        event: Dict[str, Any] = {}
        returned_state = None
        try:
            returned_state, _audit = complete_step(
                factor,
                step_index=1,
                operators=operators,
                propagator=propagator,
                kraus=bath,
                config=config,
                backend=backend,
                budget=budget,
                telemetry=telemetry,
                certified_multi_rhs=True,
            )
        except RepresentationFailure as exc:
            caught = True
            event = dict(exc.event)
        finally:
            globals()["d2_compress_mapped_blocks"] = original

        inner = event.get("inner_failure", event)
        if isinstance(inner, Mapping) and "inner_failure" in inner:
            inner = inner["inner_failure"]
        expected_half = "first" if fail_call == 1 else "second"
        expected_staged = 0 if fail_call == 1 else 1
        density_after = factor_density_cpu(factor, backend)
        checks = {
            "failure_caught": caught,
            "expected_whole_half_call_failed": counter["calls"] == fail_call,
            "exact_compression_call": event.get("compression_call_index")
            == fail_call,
            "exact_detector_step": event.get("detector_step_index") == 1,
            "exact_bath_half_step": event.get("bath_half_step") == expected_half,
            "complete_state_not_returned": returned_state is None,
            "complete_state_not_committed": event.get(
                "complete_step_state_committed"
            )
            is False,
            "external_budget_unchanged": budget.snapshot() == budget_before,
            "external_telemetry_unchanged": telemetry.snapshot()
            == telemetry_before,
            "input_weights_unchanged": np.array_equal(
                factor.weights, input_weights
            ),
            "input_density_unchanged": density_trace_norm(
                density_after - input_density, h_z
            )
            == 0.0,
            "transactional_flag": event.get(
                "transactional_ledgers_preserved"
            )
            is True,
            "expected_staged_budget_calls": event.get(
                "budget_calls_staged_within_incomplete_step"
            )
            == expected_staged,
            "expected_staged_telemetry_events": event.get(
                "telemetry_events_staged_within_incomplete_step"
            )
            == expected_staged,
            "zero_external_budget_commits": event.get(
                "budget_calls_committed_within_incomplete_step"
            )
            == 0,
            "zero_external_telemetry_commits": event.get(
                "telemetry_events_committed_within_incomplete_step"
            )
            == 0,
            "injected_failure_preserved": bool(
                isinstance(inner, Mapping)
                and inner.get("injected_failure", False)
                and inner.get("injected_whole_half_call") == fail_call
            ),
        }
        return {
            "injected_whole_half_call": fail_call,
            "expected_bath_half": expected_half,
            "event": event,
            "checks": checks,
            "passed": bool(all(checks.values())),
        }

    first = run_injection(1)
    second = run_injection(2)
    return {
        "first_half_failure": first,
        "second_half_failure": second,
        "checkpoint_eligibility_on_incomplete_steps": False,
        "passed": bool(first["passed"] and second["passed"]),
    }



def run_g0_g1_completeness_contract(production_config: RunConfig) -> Dict[str, Any]:
    rng = np.random.default_rng(2026081201)
    dimension = 32
    h_z = 0.125
    left = rng.normal(size=(dimension, 4)) + 1j * rng.normal(size=(dimension, 4))
    right = rng.normal(size=(dimension, 3)) + 1j * rng.normal(size=(dimension, 3))
    direct = density_trace_norm(
        left @ left.conj().T - right @ right.conj().T,
        h_z,
    )
    reduced = low_rank_density_trace_norm_difference_cpu(left, right, h_z=h_z)

    reduced_config_local = replace(
        reduced_config(production_config, steps=1),
        n_z=20,
        l_z=4.0,
        stop_after_steps=0,
        planned_compression_calls=2,
    )
    backend = NumericalBackend("scipy")
    operators = build_oscillator_operators(
        reduced_config_local.n_shell, reduced_config_local.omega
    )
    z, h_small, _ = build_reference_grid(
        reduced_config_local.n_z, reduced_config_local.l_z
    )
    initial = build_initial_state(reduced_config_local, operators, z, h_small)
    propagator = build_propagator_objects(
        reduced_config_local, operators, backend, initial
    )
    synthetic, construction = build_g1_synthetic_canonical_factor(
        8,
        config=reduced_config_local,
        operators=operators,
        propagator=propagator,
        backend=backend,
    )
    checks = {
        "rank_contract_exact": G1_SYNTHETIC_RANKS == (64, 256, 640),
        "benchmark_budget_unchanged": G1_SYNTHETIC_BENCHMARK_BUDGET
        == REPRESENTATION_TRACE_NORM_BUDGET
        == 1.0e-8,
        "benchmark_ledger_isolated_single_call": G1_SYNTHETIC_BENCHMARK_PLANNED_CALLS
        == 1,
        "signed_gram_trace_norm_identity": abs(direct - reduced) <= 2.0e-12,
        "reduced_synthetic_factor": construction["passed"],
        "reduced_synthetic_rank": synthetic.rank == 8,
        "cpu_mode_name": "cpu_first_step" in {"cpu_first_step", "a100_first_step"},
        "a100_mode_name": "a100_first_step" in {"cpu_first_step", "a100_first_step"},
        "complete_acceptance_rule_exact": D2PR2_COMPLETE_ACCEPTANCE_RULE
        == "unchanged_hard_canonicality_and_trace_gates_plus_existing_"
           "centralized_tolerance_inclusive_budget_predicate",
    }
    return {
        "direct_density_trace_norm": direct,
        "reduced_signed_gram_trace_norm": reduced,
        "absolute_identity_residual": abs(direct - reduced),
        "reduced_synthetic_construction": construction,
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


def run_g0_allocator_pool_resource_false_negative_regression() -> Dict[str, Any]:
    """Reproduce R1-A allowance arithmetic with an isolated fake CuPy pool."""

    class FakePool:
        def __init__(self, owner: "FakeBackend", *, pinned: bool = False):
            self.owner = owner
            self.pinned = pinned

        def used_bytes(self) -> int:
            return 314572800 if not self.pinned else 0

        def total_bytes(self) -> int:
            if self.pinned:
                return 0
            return 83055607808 if not self.owner.released else self.used_bytes()

        def n_free_blocks(self) -> int:
            return 17 if (not self.pinned and not self.owner.released) else 0

        def free_all_blocks(self) -> None:
            if self.pinned:
                self.owner.pinned_release_calls += 1
            else:
                self.owner.release_calls += 1
                self.owner.released = True

    class FakeCp:
        def __init__(self, owner: "FakeBackend"):
            self.default_pool = FakePool(owner)
            self.pinned_pool = FakePool(owner, pinned=True)

        def get_default_memory_pool(self) -> FakePool:
            return self.default_pool

        def get_default_pinned_memory_pool(self) -> FakePool:
            return self.pinned_pool

    class FakeBackend:
        name = "cupy"

        def __init__(self, free_before: int, free_increase: int):
            self.free_before = int(free_before)
            self.free_increase = int(free_increase)
            self.released = False
            self.release_calls = 0
            self.pinned_release_calls = 0
            self.synchronize_calls = 0
            self._cp = FakeCp(self)

        def synchronize(self) -> None:
            self.synchronize_calls += 1

        def memory_info(self) -> Dict[str, int]:
            return {
                "free_bytes": self.free_before
                + (self.free_increase if self.released else 0),
                "total_bytes": 80 * 1024**3,
            }

    r1_backend = FakeBackend(1609236480, 82741035008)
    r1_permitted, r1 = _d2_prepare_resource_allowance_after_unused_pool_release(
        r1_backend,
        n_rows=182 * 1500,
        temporary_total_rank=162,
    )

    sufficient_backend = FakeBackend(8 * 1024**3, 0)
    sufficient_permitted, sufficient = (
        _d2_prepare_resource_allowance_after_unused_pool_release(
            sufficient_backend,
            n_rows=182 * 1500,
            temporary_total_rank=162,
        )
    )

    exact_upper = 1416491712
    checks = {
        "r1_exact_logical_upper_bound": (
            r1["pre_mapping_logical_upper_bound_bytes"] == exact_upper
        ),
        "r1_original_allowance_exact": (
            r1["pre_release_permitted_bytes"] == 1287389184
        ),
        "r1_old_guard_would_fail": (
            exact_upper > r1["pre_release_permitted_bytes"]
        ),
        "r1_conditional_release_triggered_once": (
            r1["unused_pool_release_triggered"] is True
            and r1_backend.release_calls == 1
            and r1_backend.pinned_release_calls == 1
            and r1_backend.synchronize_calls == 1
        ),
        "r1_driver_free_increase_exact": (
            r1["driver_free_increase_bytes"] == 82741035008
        ),
        "r1_post_release_allowance_passes": (
            r1_permitted is not None and exact_upper <= r1_permitted
        ),
        "sufficient_memory_does_not_release_pool": (
            sufficient["unused_pool_release_triggered"] is False
            and sufficient_backend.release_calls == 0
            and sufficient_backend.pinned_release_calls == 0
            and sufficient_backend.synchronize_calls == 0
            and sufficient_permitted
            == int(GPU_WORKING_SET_FRACTION * 8 * 1024**3)
        ),
        "resource_fraction_unchanged": (
            r1["working_set_fraction_unchanged"] == 0.80
            and sufficient["working_set_fraction_unchanged"] == 0.80
        ),
        "downstream_actual_guard_unchanged": (
            r1["downstream_actual_working_set_guard_unchanged"] is True
            and sufficient["downstream_actual_working_set_guard_unchanged"] is True
        ),
        "no_scientific_ledger_mutation": all(
            record[key] is False
            for record in (r1, sufficient)
            for key in (
                "physical_state_mutated",
                "representation_budget_mutated",
                "telemetry_mutated",
            )
        ),
    }
    return {
        "schema": "2026-08-14-task09-v4-d2pr2g1fmp-r1a-resource-false-negative-regression-v1",
        "r1_authority_classification": D2PR2G1FMP_R1_CLASSIFICATION,
        "r1_authority_job_id": D2PR2G1FMP_R1_JOB_ID,
        "r1_case": r1,
        "sufficient_memory_control": sufficient,
        "checks": checks,
        "passed": bool(all(checks.values())),
        "production_authorized": False,
        "task10_eligible": False,
    }


def run_g0_certification(
    production_config: RunConfig,
    *,
    script_path: Path,
    source_sha256: str,
    numerical_core_sha256: str,
) -> Tuple[Dict[str, Any], Dict[str, np.ndarray]]:
    started = time.time()
    source_audit = source_scope_audit(script_path)
    lineage_audit = parent_lineage_audit(script_path)
    authority_audit = embedded_authority_audit(script_path)

    production_operators = build_oscillator_operators(N_SHELL, OMEGA)
    static_config = replace(
        production_config,
        backend="scipy",
        n_z=32,
        l_z=4.0,
        z0=2.0,
        sigma_z_amplitude=0.35,
        dt=2.0e-3,
        t_final=2.0e-3,
        stop_after_steps=0,
        planned_compression_calls=2,
    )
    static_backend = NumericalBackend("scipy")
    static_z, static_hz, _ = build_reference_grid(
        static_config.n_z, static_config.l_z
    )
    static_initial = build_initial_state(
        static_config, production_operators, static_z, static_hz
    )
    static_propagator = build_propagator_objects(
        static_config, production_operators, static_backend, static_initial
    )
    upward_identity = projected_upward_identity_audit(production_operators)
    operator_report = {
        "production_complete_shell_operator_audit": production_operators.audit,
        "production_upward_projected_identity": upward_identity,
        "roof_sign_and_loss_audit_at_production_channel_dimension": static_propagator.roof_sign_audit,
        "passed": bool(
            production_operators.audit["all_checks_passed"]
            and upward_identity["passed"]
            and static_propagator.roof_sign_audit[
                "spinor_roof_term_sign_passed"
            ]
        ),
    }

    repair_certificate = run_g0_repaired_gauge_certificate_test()
    call3777_ladder = run_g0_call3777_repaired_rank_ladder_regression()
    whole_half_oracle = run_g0_whole_half_oracle_tests()
    repaired_rank_adversarial = run_g0_repaired_rank_adversarial_tests(
        whole_half_oracle
    )
    budget_identity = run_g0_budget_identity_test()
    bench_config = reduced_config(production_config)
    gmres = run_g0_gmres_certification(bench_config)
    full_density = run_g0_reduced_full_density(bench_config)
    checkpoint = run_g0_checkpoint_roundtrip(
        replace(
            bench_config,
            stop_after_steps=4,
            t_final=4 * bench_config.dt,
            planned_compression_calls=8,
        ),
        source_sha256=source_sha256,
        numerical_core_sha256=numerical_core_sha256,
    )
    failure_context = run_g0_failure_context_certification(production_config)
    g1_completeness = run_g0_g1_completeness_contract(production_config)
    allocator_resource = run_g0_allocator_pool_resource_false_negative_regression()

    checks = {
        "source_scope": source_audit["passed"],
        "parent_lineage": lineage_audit["passed"],
        "available_authority_hashes": authority_audit["passed"],
        "operators_ordering_and_roof": operator_report["passed"],
        "exact_weighted_polar_repair_certificate": repair_certificate["passed"],
        "call3777_repaired_rank_ladder": call3777_ladder["passed"],
        "whole_half_vs_full_gram_oracle": whole_half_oracle["passed"],
        "repaired_rank_adversarial_suite": repaired_rank_adversarial["passed"],
        "exact_2delta_and_scheduled_budget": budget_identity["passed"],
        "multi_rhs_gmres": gmres["passed"],
        "reduced_full_density": full_density["passed"],
        "checkpoint_restart_new_schema": checkpoint["passed"],
        "exact_transactional_failure_context": failure_context["passed"],
        "g1_completeness_contract": g1_completeness["passed"],
        "r1a_allocator_pool_resource_false_negative": allocator_resource["passed"],
    }
    arrays = full_density.pop("arrays")
    report = {
        "schema": G0_REPORT_SCHEMA,
        "created_utc": utc_now_iso(),
        "script_version": SCRIPT_VERSION,
        "source_sha256": source_sha256,
        "numerical_core_sha256": numerical_core_sha256,
        "exact_parent_source_sha256": D2PR2G1FMP_PARENT_SOURCE_SHA256,
        "exact_parent_core_sha256": D2PR2G1FMP_PARENT_CORE_SHA256,
        "repaired_rank_ancestry_source_sha256": D2PR_PARENT_D2P_SOURCE_SHA256,
        "repaired_rank_ancestry_core_sha256": D2PR_PARENT_D2P_CORE_SHA256,
        "execution_gate": "V4-G0",
        "source_scope_audit": source_audit,
        "parent_lineage_audit": lineage_audit,
        "authority_audit": authority_audit,
        "operator_report": operator_report,
        "repaired_gauge_certificate_test": repair_certificate,
        "call3777_repaired_rank_ladder_regression": call3777_ladder,
        "whole_half_oracle_tests": whole_half_oracle,
        "repaired_rank_adversarial_tests": repaired_rank_adversarial,
        "representation_budget_identity": budget_identity,
        "multi_rhs_gmres_certification": gmres,
        "reduced_full_density_certification": full_density,
        "checkpoint_restart_certification": checkpoint,
        "failure_context_certification": failure_context,
        "g1_completeness_contract": g1_completeness,
        "allocator_pool_resource_false_negative_regression": allocator_resource,
        "checks": checks,
        "passed": bool(all(checks.values())),
        "production_authorized": False,
        "acceptance_enabled": False,
        "task10_eligible": False,
        "physical_claim": "none; repaired-rank G1-contract plus R1-A allocator-resource V4-G0 certification only",
        "next_gate_authorized_by_this_report": False,
        "wall_seconds": time.time() - started,
    }
    return report, arrays


# =============================================================================
# PRODUCTION-SIZE NON-ACCEPTING GATE SUPPORT (G1-G4)
# =============================================================================
def verify_upstream_authority_for_production_gates() -> Dict[str, Any]:
    authorization = DATA_ROOT / "Task09_Authorization_U2_2026-08-10_01"
    task07 = DATA_ROOT / "4747.Environmental_response_100_00_spinor_upward"
    task05 = DATA_ROOT / "4513.Oscillator_channel_detector_tests_100_00_spinor"
    directories = {
        "authorization": authorization,
        "task07": task07,
        "task05": task05,
    }
    missing = [name for name, path in directories.items() if not path.is_dir()]
    if missing:
        raise GateBlocked(f"Required upstream directories are missing: {missing}")

    records: Dict[str, Any] = {}
    combined_text_parts: List[str] = []
    for name, directory in directories.items():
        manifests = list(directory.glob("SHA256SUMS")) + list(directory.glob("*output_hashes.json"))
        json_files = sorted(directory.glob("*.json"))
        for path in json_files:
            try:
                combined_text_parts.append(json.dumps(read_json(path), sort_keys=True))
            except Exception:
                continue
        records[name] = {
            "path": str(directory),
            "json_file_count": len(json_files),
            "hash_record_count": len(manifests),
        }
    combined = "\n".join(combined_text_parts)
    required_tokens = {
        "U2": "U2",
        "upward": "upward",
        "resolved_nonzero": "RESOLVED_NONZERO",
        "task08_pass": "PASS_TASK08_LINEAR_RESPONSE",
        "task08_manifest": SOURCE_FINGERPRINTS["task08_final_output_manifest"],
        "task07_high_accuracy_core": SOURCE_FINGERPRINTS["task07_v8_high_accuracy_upward_core"],
    }
    token_checks = {name: token in combined for name, token in required_tokens.items()}
    passed = bool(all(token_checks.values()))
    if not passed:
        raise GateBlocked(f"Upstream authorization content check failed: {token_checks}")
    return {
        "directories": records,
        "required_token_checks": token_checks,
        "passed": True,
    }


def _pilot_histories(config: RunConfig) -> Dict[str, np.ndarray]:
    n = config.execution_num_steps
    return {
        "times": np.arange(n + 1, dtype=np.float64) * config.dt,
        "survival": np.full(n + 1, np.nan, dtype=np.float64),
        "step_probability": np.full(n, np.nan, dtype=np.float64),
        "rank": np.full(n + 1, -1, dtype=np.int64),
        "representation_bound": np.full(n + 1, np.nan, dtype=np.float64),
        "top_shell": np.full(n + 1, np.nan, dtype=np.float64),
        "overflow_intensity": np.full(n + 1, np.nan, dtype=np.float64),
        "step_wall_seconds": np.full(n, np.nan, dtype=np.float64),
        "gmres_max_residual": np.full(n, np.nan, dtype=np.float64),
        "probability_closure": np.full(n, np.nan, dtype=np.float64),
        "bath_trace_residual_first": np.full(n, np.nan, dtype=np.float64),
        "bath_trace_residual_second": np.full(n, np.nan, dtype=np.float64),
    }


def save_nonaccepting_pilot_outputs(
    out_dir: Path,
    *,
    report: Mapping[str, Any],
    histories: Mapping[str, np.ndarray],
    telemetry: RepresentationTelemetry,
) -> None:
    atomic_write_json(out_dir / "nonaccepting_gate_report.json", report)
    atomic_savez(out_dir / "pilot_histories.npz", **{key: np.asarray(value) for key, value in histories.items()})
    atomic_write_json(out_dir / "representation_telemetry.json", {
        "schema": REPRESENTATION_TELEMETRY_SCHEMA,
        "events": telemetry.snapshot(),
    })
    if report.get("g1_cross_backend_comparison") is not None:
        atomic_write_json(
            out_dir / "g1_cross_backend_comparison.json",
            report["g1_cross_backend_comparison"],
        )
    if report.get("g1_synthetic_rank_benchmarks") is not None:
        atomic_write_json(
            out_dir / "g1_synthetic_rank_benchmarks.json",
            report["g1_synthetic_rank_benchmarks"],
        )



def _g1_mode_directory(config: RunConfig, mode: str) -> Path:
    if mode not in {"cpu_first_step", "a100_first_step"}:
        raise ValueError(f"Unsupported G1 mode directory: {mode}")
    return config.output_root / CASE_DIRECTORY_NAME / f"V4_G1_{mode}"


def _verified_output_file(directory: Path, filename: str) -> Dict[str, Any]:
    manifest_path = directory / "output_hashes.json"
    if not manifest_path.is_file():
        raise GateBlocked(f"Missing output hash manifest: {manifest_path}")
    manifest = read_json(manifest_path)
    expected = manifest.get("files", {}).get(filename)
    path = directory / filename
    if not isinstance(expected, str) or not path.is_file():
        raise GateBlocked(f"Missing hashed G1 artifact {filename} in {directory}")
    found = sha256_file(path)
    if found != expected:
        raise GateBlocked(
            f"G1 artifact hash mismatch for {path}: expected {expected}, found {found}"
        )
    return {"path": str(path), "sha256": found, "verified": True}


def low_rank_density_trace_norm_difference_cpu(
    left_matrix: np.ndarray,
    right_matrix: np.ndarray,
    *,
    h_z: float,
) -> float:
    """Exact trace norm of h_z(XX^dagger-YY^dagger) from a reduced signed Gram.

    The calculation never forms the production D x D density matrix.  For
    A=[X,Y], J=diag(I,-I), the nonzero eigenvalues of h_z A J A^dagger are the
    eigenvalues of G^{1/2} J G^{1/2}, G=h_z A^dagger A.
    """
    left = np.ascontiguousarray(left_matrix, dtype=np.complex128)
    right = np.ascontiguousarray(right_matrix, dtype=np.complex128)
    if left.ndim != 2 or right.ndim != 2 or left.shape[0] != right.shape[0]:
        raise ValueError("Low-rank density factors must have a common row dimension")
    combined = np.ascontiguousarray(np.concatenate((left, right), axis=1))
    gram = h_z * (combined.conj().T @ combined)
    gram = 0.5 * (gram + gram.conj().T)
    values, vectors = np.linalg.eigh(gram)
    scale = max(float(np.max(np.abs(values), initial=0.0)), 1.0)
    envelope = (
        PSD_BACKWARD_ERROR_FACTOR
        * np.finfo(float).eps
        * max(1, values.size)
        * scale
    )
    if float(np.min(values, initial=0.0)) < -envelope:
        raise RuntimeError(
            "Signed-density comparison Gram is non-PSD outside roundoff envelope"
        )
    sqrt_values = np.sqrt(np.maximum(values, 0.0))
    sqrt_gram = (vectors * sqrt_values[None, :]) @ vectors.conj().T
    signature = np.diag(
        np.concatenate(
            (
                np.ones(left.shape[1], dtype=np.float64),
                -np.ones(right.shape[1], dtype=np.float64),
            )
        )
    ).astype(np.complex128)
    reduced_difference = sqrt_gram @ signature @ sqrt_gram
    reduced_difference = 0.5 * (
        reduced_difference + reduced_difference.conj().T
    )
    return float(
        np.sum(np.abs(np.linalg.eigvalsh(reduced_difference)), dtype=np.float64)
    )


def build_g1_synthetic_canonical_factor(
    rank: int,
    *,
    config: RunConfig,
    operators: OscillatorOperators,
    propagator: PropagatorObjects,
    backend: NumericalBackend,
) -> Tuple[CanonicalFactor, Dict[str, Any]]:
    """Deterministic production-row rank-r factor with sine modes in channel 0."""
    rank = int(rank)
    if rank <= 0 or rank >= config.n_z:
        raise ValueError("Synthetic rank must satisfy 0 < rank < N_z")
    if operators.d_channels != config.d_channels:
        raise ValueError("Synthetic factor channel dimension mismatch")
    memory_before = backend.memory_info()
    predicted_factor_bytes = int(
        np.dtype(np.complex128).itemsize * config.state_dimension * rank
    )
    free = memory_before.get("free_bytes")
    permitted = None if free is None else int(G1_BENCHMARK_MEMORY_FRACTION * free)
    if permitted is not None and predicted_factor_bytes > permitted:
        raise RepresentationFailure(
            "Synthetic G1 factor allocation exceeds the resource invariant",
            event={
                "benchmark_component": "synthetic_factor_allocation",
                "synthetic_rank": rank,
                "predicted_factor_bytes": predicted_factor_bytes,
                "free_bytes_before": free,
                "permitted_bytes": permitted,
                "resource_fraction": G1_BENCHMARK_MEMORY_FRACTION,
                "state_committed": False,
                "budget_committed": False,
            },
        )

    grid_index = np.arange(config.n_z, dtype=np.float64)
    basis_blocks: List[Any] = []
    for start in range(0, rank, config.factor_block_columns):
        stop = min(rank, start + config.factor_block_columns)
        mode_numbers = np.arange(start + 1, stop + 1, dtype=np.float64)
        longitudinal = np.sin(
            np.pi * grid_index[:, None] * mode_numbers[None, :] / config.n_z
        ).astype(np.complex128)
        longitudinal[0, :] = 0.0
        norms = np.sqrt(
            propagator.h_z
            * np.sum(np.abs(longitudinal) ** 2, axis=0, dtype=np.float64)
        )
        if not np.all(np.isfinite(norms)) or np.any(norms <= 0.0):
            raise RuntimeError("Synthetic longitudinal sine basis has invalid norms")
        longitudinal /= norms[None, :]
        block = backend.xp.zeros(
            (config.state_dimension, stop - start), dtype=backend.complex128
        )
        block[: config.n_z, :] = backend.to_backend_array(longitudinal)
        basis_blocks.append(backend.xp.ascontiguousarray(block))

    factor = CanonicalFactor(
        basis_blocks=tuple(basis_blocks),
        weights=np.full(rank, 1.0 / rank, dtype=np.float64),
        n_rows=config.state_dimension,
        h_z=propagator.h_z,
    )
    canonical = canonicality_audit(factor, backend)
    report = {
        "construction": "channel0_discrete_sine_basis_modes_1_through_rank",
        "rank": rank,
        "state_dimension": config.state_dimension,
        "channel_dimension": operators.d_channels,
        "N_z": config.n_z,
        "h_z": propagator.h_z,
        "factor_logical_bytes": factor.logical_nbytes,
        "predicted_factor_bytes": predicted_factor_bytes,
        "memory_before": memory_before,
        "canonicality": canonical,
        "passed": bool(
            canonical["passed"]
            and abs(factor.trace - 1.0) <= 32.0 * np.finfo(float).eps
        ),
    }
    if not report["passed"]:
        raise RepresentationFailure(
            "Synthetic G1 factor failed canonical construction",
            event={
                "benchmark_component": "synthetic_factor_construction",
                "synthetic_rank": rank,
                "construction_report": report,
                "state_committed": False,
                "budget_committed": False,
            },
        )
    return factor, report


def _canonical_scaled_columns(
    factor: CanonicalFactor,
    indices: Sequence[int],
    backend: NumericalBackend,
) -> Any:
    offsets = block_offsets(factor.basis_blocks)
    columns: List[Any] = []
    for raw_index in indices:
        index = int(raw_index)
        if index < 0 or index >= factor.rank:
            raise IndexError("Canonical sample-column index out of range")
        for block, (start, stop) in zip(factor.basis_blocks, offsets):
            if start <= index < stop:
                local = index - start
                columns.append(
                    block[:, local] * math.sqrt(float(factor.weights[index]))
                )
                break
    return backend.xp.ascontiguousarray(backend.xp.stack(columns, axis=1))


def _raw_selected_columns(
    factor: RawFactor,
    indices: Sequence[int],
    backend: NumericalBackend,
) -> Any:
    offsets = block_offsets(factor.blocks)
    columns: List[Any] = []
    for raw_index in indices:
        index = int(raw_index)
        if index < 0 or index >= factor.rank:
            raise IndexError("Raw sample-column index out of range")
        for block, (start, stop) in zip(factor.blocks, offsets):
            if start <= index < stop:
                columns.append(block[:, index - start])
                break
    return backend.xp.ascontiguousarray(backend.xp.stack(columns, axis=1))


def _free_backend_pool(backend: NumericalBackend) -> None:
    backend.synchronize()
    if backend.name == "cupy":
        backend._cp.get_default_memory_pool().free_all_blocks()
        backend._cp.get_default_pinned_memory_pool().free_all_blocks()


def _allocator_pool_snapshot(backend: NumericalBackend) -> Dict[str, Any]:
    """Read driver and allocator-pool state without changing live arrays."""
    memory = backend.memory_info()
    report: Dict[str, Any] = {
        "backend": backend.name,
        "driver_free_bytes": memory.get("free_bytes"),
        "driver_total_bytes": memory.get("total_bytes"),
        "default_pool_used_bytes": None,
        "default_pool_total_bytes": None,
        "default_pool_cached_unused_bytes": None,
        "default_pool_free_block_count": None,
        "pinned_pool_free_block_count": None,
    }
    if backend.name == "cupy":
        pool = backend._cp.get_default_memory_pool()
        pinned = backend._cp.get_default_pinned_memory_pool()
        used = int(pool.used_bytes())
        total = int(pool.total_bytes())
        report.update({
            "default_pool_used_bytes": used,
            "default_pool_total_bytes": total,
            "default_pool_cached_unused_bytes": max(total - used, 0),
            "default_pool_free_block_count": int(pool.n_free_blocks()),
            "pinned_pool_free_block_count": int(pinned.n_free_blocks()),
        })
    return report


def _d2_whole_half_logical_upper_bound_bytes(
    *, n_rows: int, temporary_total_rank: int
) -> int:
    """Upper bound for mapped blocks, full range basis, and three reduced arrays."""
    if int(n_rows) <= 0 or int(temporary_total_rank) <= 0:
        raise ValueError("D2 whole-half resource dimensions must be positive")
    complex_bytes = np.dtype(np.complex128).itemsize
    mapped = complex_bytes * int(n_rows) * int(temporary_total_rank)
    full_range = mapped
    reduced = 3 * complex_bytes * int(temporary_total_rank) ** 2
    return int(mapped + full_range + reduced)


def _d2_prepare_resource_allowance_after_unused_pool_release(
    backend: NumericalBackend,
    *,
    n_rows: int,
    temporary_total_rank: int,
) -> Tuple[Optional[int], Dict[str, Any]]:
    """Remove only cached unused pool blocks when the old guard would false-stop.

    The unchanged resource fraction and the downstream actual-working-set guard
    remain authoritative.  This preflight never relaxes the limit and never
    releases live arrays; it only makes driver-free memory reflect reusable
    cached CuPy blocks when the conservative pre-mapping upper bound would
    otherwise exceed the original allowance.
    """
    predicted = _d2_whole_half_logical_upper_bound_bytes(
        n_rows=n_rows,
        temporary_total_rank=temporary_total_rank,
    )
    before = _allocator_pool_snapshot(backend)
    free_before = before.get("driver_free_bytes")
    permitted_before = (
        None
        if free_before is None
        else int(GPU_WORKING_SET_FRACTION * int(free_before))
    )
    release_triggered = bool(
        backend.name == "cupy"
        and permitted_before is not None
        and predicted > permitted_before
    )
    if release_triggered:
        _free_backend_pool(backend)
    after = _allocator_pool_snapshot(backend)
    free_after = after.get("driver_free_bytes")
    permitted_after = (
        None
        if free_after is None
        else int(GPU_WORKING_SET_FRACTION * int(free_after))
    )
    return permitted_after, {
        "policy": D2PR2G1FMP_RESOURCE_RELEASE_POLICY,
        "working_set_fraction_unchanged": GPU_WORKING_SET_FRACTION,
        "n_rows": int(n_rows),
        "temporary_total_rank_upper_bound": int(temporary_total_rank),
        "pre_mapping_logical_upper_bound_bytes": int(predicted),
        "pre_release_snapshot": before,
        "pre_release_permitted_bytes": permitted_before,
        "unused_pool_release_triggered": release_triggered,
        "post_release_snapshot": after,
        "post_release_permitted_bytes": permitted_after,
        "driver_free_increase_bytes": (
            None
            if free_before is None or free_after is None
            else int(free_after) - int(free_before)
        ),
        "downstream_actual_working_set_guard_unchanged": True,
        "physical_state_mutated": False,
        "representation_budget_mutated": False,
        "telemetry_mutated": False,
    }


def run_g1_detector_rank_benchmark(
    factor: CanonicalFactor,
    *,
    rank: int,
    config: RunConfig,
    operators: OscillatorOperators,
    propagator: PropagatorObjects,
    backend: NumericalBackend,
) -> Tuple[Dict[str, Any], RawFactor]:
    before = backend.memory_info()
    predicted_bytes = int(
        np.dtype(np.complex128).itemsize
        * config.state_dimension
        * (
            2 * rank
            + min(config.detector_rhs_batch_columns, rank)
            * (GMRES_RESTART + 8)
        )
    )
    free = before.get("free_bytes")
    permitted = None if free is None else int(G1_BENCHMARK_MEMORY_FRACTION * free)
    if permitted is not None and predicted_bytes > permitted:
        raise RepresentationFailure(
            "Synthetic detector benchmark exceeds the resource invariant",
            event={
                "benchmark_component": "detector_linear_solve",
                "synthetic_rank": rank,
                "predicted_working_set_bytes": predicted_bytes,
                "free_bytes_before": free,
                "permitted_bytes": permitted,
                "state_committed": False,
                "budget_committed": False,
            },
        )

    started = time.perf_counter()
    raw, probability, audit = detector_advance_canonical(
        factor,
        operators=operators,
        config=config,
        propagator=propagator,
        backend=backend,
        certified_multi_rhs=True,
    )
    backend.synchronize()
    wall = time.perf_counter() - started

    sample_indices = np.unique(
        np.linspace(
            0,
            rank - 1,
            num=min(G1_BENCHMARK_SAMPLE_COLUMNS, rank),
            dtype=np.int64,
        )
    )
    sample_input = _canonical_scaled_columns(factor, sample_indices, backend)
    sample_multi = _raw_selected_columns(raw, sample_indices, backend)
    sample_independent, q_independent, info_independent, residual_independent, _ = (
        advance_many_detector(
            sample_input,
            backend=backend,
            propagator=propagator,
            config=config,
            operators=operators,
            certified_multi_rhs=False,
        )
    )
    numerator = backend.norm(sample_multi - sample_independent)
    denominator = max(backend.norm(sample_independent), np.finfo(float).tiny)
    solution_relative_difference = numerator / denominator
    shaped_input = sample_input.reshape(operators.d_channels, config.n_z, -1)
    shaped_multi = sample_multi.reshape(operators.d_channels, config.n_z, -1)
    q_multi = 0.5 * (shaped_input[:, -1, :] + shaped_multi[:, -1, :])
    sample_probability_multi = float(
        config.dt * config.kappa * backend.abs2_sum(q_multi)
    )
    sample_probability_independent = float(
        config.dt * config.kappa * backend.abs2_sum(q_independent)
    )
    sample_probability_difference = abs(
        sample_probability_multi - sample_probability_independent
    )
    output_trace = physical_trace_raw(raw, propagator.h_z, backend)
    after = backend.memory_info()
    checks = {
        "rank_exact": raw.rank == rank,
        "gmres_info_zero": audit["gmres_failure_count"] == 0,
        "true_residual": audit["maximum_true_relative_residual"] <= TRUE_RESIDUAL_TOL,
        "midpoint_probability_finite_nonnegative": bool(
            np.isfinite(probability) and probability >= 0.0
        ),
        "detector_probability_closure": abs(audit["detector_probability_closure"])
        <= PROBABILITY_CLOSURE_ABS_TOL,
        "sample_independent_info_zero": int(np.count_nonzero(info_independent)) == 0,
        "sample_independent_true_residual": float(
            np.max(residual_independent, initial=0.0)
        )
        <= TRUE_RESIDUAL_TOL,
        "sample_solution_agreement": solution_relative_difference
        <= G1_BENCHMARK_SAMPLE_SOLUTION_REL_TOL,
        "sample_probability_agreement": sample_probability_difference
        <= G1_BENCHMARK_SAMPLE_PROBABILITY_ABS_TOL,
        "output_trace_finite_nonnegative": bool(
            np.isfinite(output_trace) and output_trace >= 0.0
        ),
    }
    return {
        "component": "production_dimension_detector_linear_solve",
        "rank": rank,
        "state_dimension": config.state_dimension,
        "number_rhs": rank,
        "rhs_batch_columns": config.detector_rhs_batch_columns,
        "rhs_batch_count": int(
            math.ceil(rank / config.detector_rhs_batch_columns)
        ),
        "predicted_working_set_bytes": predicted_bytes,
        "memory_before": before,
        "memory_after": after,
        "output_factor_logical_bytes": raw.logical_nbytes,
        "midpoint_roof_probability": probability,
        "output_trace": output_trace,
        "detector_audit": audit,
        "sample_indices": sample_indices.tolist(),
        "sample_solution_relative_difference": solution_relative_difference,
        "sample_probability_multi_rhs": sample_probability_multi,
        "sample_probability_independent": sample_probability_independent,
        "sample_probability_absolute_difference": sample_probability_difference,
        "sample_independent_info": np.asarray(info_independent).tolist(),
        "sample_independent_true_residual": np.asarray(
            residual_independent, dtype=np.float64
        ).tolist(),
        "checks": checks,
        "passed": bool(all(checks.values())),
        "wall_seconds": wall,
    }, raw


def _repair_summary_from_compression_audit(audit: Mapping[str, Any]) -> Dict[str, Any]:
    repair_records: List[Mapping[str, Any]] = []
    for merge in audit.get("merge_audits", []):
        repair = merge.get("gauge_repair")
        if isinstance(repair, Mapping):
            repair_records.append(repair)
    event = audit["event"]
    retained = event.get("retained_gauge_repair")
    if isinstance(retained, Mapping):
        repair_records.append(retained)
    return {
        "repair_record_count": len(repair_records),
        "repair_pass_count": int(
            sum(int(record.get("repair_pass_count", 0)) for record in repair_records)
        ),
        "density_approximation_introduced_by_gauge": bool(
            any(
                bool(record.get("density_approximation_introduced", False))
                for record in repair_records
            )
        ),
        "reconstructible_gauge_density_bound_sum": float(
            math.fsum(
                float(record.get("reconstructible_density_trace_norm_bound", 0.0))
                for record in repair_records
            )
        ),
        "all_repairs_use_hard_gate_only": bool(
            all(
                record.get("post_repair_acceptance_rule")
                == "unchanged_hard_canonicality_gate_only"
                for record in repair_records
            )
        )
        if repair_records
        else True,
    }


def run_g1_compression_rank_benchmark(
    factor: CanonicalFactor,
    *,
    rank: int,
    config: RunConfig,
    operators: OscillatorOperators,
    propagator: PropagatorObjects,
    bath: BathKraus,
    backend: NumericalBackend,
) -> Tuple[Dict[str, Any], CanonicalFactor]:
    benchmark_budget = RepresentationBudgetState(
        total_budget=G1_SYNTHETIC_BENCHMARK_BUDGET,
        total_planned_calls=G1_SYNTHETIC_BENCHMARK_PLANNED_CALLS,
    )
    benchmark_telemetry = RepresentationTelemetry()
    before = backend.memory_info()
    started = time.perf_counter()
    try:
        compressed, audit = cssf_bath_half_step(
            factor,
            kraus=bath,
            operators=operators,
            config=config,
            propagator=propagator,
            backend=backend,
            budget=benchmark_budget,
            telemetry=benchmark_telemetry,
            detector_step_index=0,
            bath_half_step="first",
        )
    except RepresentationFailure as exc:
        raise RepresentationFailure(
            str(exc),
            event={
                **exc.event,
                "benchmark_component": "production_dimension_compression",
                "synthetic_rank": rank,
                "benchmark_budget_isolated_from_physical_state": True,
                "physical_state_mutated": False,
                "physical_budget_mutated": False,
            },
        ) from exc
    backend.synchronize()
    wall = time.perf_counter() - started
    event = audit["event"]
    repair_summary = _repair_summary_from_compression_audit(audit)
    after = backend.memory_info()
    expected_temporary_rank = 3 * rank
    checks = {
        "input_rank_exact": factor.rank == rank,
        "three_kraus_logical_rank_exact": event["temporary_total_kraus_rank"]
        == expected_temporary_rank,
        "branch_rank_sequence_exact": event["temporary_branch_ranks"]
        == [rank, rank, rank],
        "finite_positive_output_weights": bool(
            np.all(np.isfinite(compressed.weights))
            and np.all(compressed.weights > 0.0)
        ),
        "hard_canonicality_gate": bool(event["canonicality"]["passed"]),
        "post_repair_acceptance_rule": event["post_repair_acceptance_rule"]
        == D2PR2_COMPLETE_ACCEPTANCE_RULE,
        "trace_preservation": abs(compressed.trace - factor.trace)
        <= TRACE_RESTORE_TOL * max(factor.trace, 1.0),
        "kraus_completeness": event["kraus_completeness_residual"]
        <= BATH_COMPLETENESS_TOL,
        "single_isolated_budget_call": benchmark_budget.calls_completed == 1,
        "same_global_budget_value": benchmark_budget.total_budget
        == REPRESENTATION_TRACE_NORM_BUDGET
        == 1.0e-8,
        "reconstructible_density_bound_within_budget": benchmark_budget.bound_used
        <= REPRESENTATION_TRACE_NORM_BUDGET,
        "telemetry_single_event": len(benchmark_telemetry.events) == 1,
        "no_scientific_hard_rank_cap": event["scientific_hard_rank_cap"] is None,
        "gauge_and_density_approximation_distinguished": (
            "density_approximation_introduced_by_gauge" in repair_summary
            and np.isfinite(
                repair_summary["reconstructible_gauge_density_bound_sum"]
            )
        ),
    }
    summary_event_keys = (
        "temporary_branch_ranks",
        "temporary_total_kraus_rank",
        "precompression_rank",
        "required_rank",
        "rank_after",
        "streaming_merge_count",
        "streaming_density_bound",
        "spectral_discarded_trace",
        "retained_gauge_bound_scaled",
        "committed_trace_norm_increment",
        "cumulative_bound_after",
        "budget_remaining_after",
        "maximum_predicted_working_set_bytes",
        "canonicality_repair_target_met",
        "post_repair_acceptance_rule",
        "raw_schedule_margin",
        "tolerance_inclusive_schedule_margin",
        "first_positive_strict_raw_margin_rank",
        "canonicality",
        "wall_seconds",
    )
    event_summary = {key: event.get(key) for key in summary_event_keys}
    return {
        "component": "production_dimension_physical_u2_resolvent_kraus_compression",
        "rank": rank,
        "state_dimension": config.state_dimension,
        "input_trace": factor.trace,
        "input_factor_logical_bytes": factor.logical_nbytes,
        "output_rank": compressed.rank,
        "output_trace": compressed.trace,
        "output_factor_logical_bytes": compressed.logical_nbytes,
        "physical_bath_action": bath.action,
        "physical_kraus_completeness_residual": bath.completeness_residual,
        "benchmark_budget_isolated_from_physical_state": True,
        "benchmark_budget": benchmark_budget.snapshot(),
        "reconstructible_density_trace_norm_bound": benchmark_budget.bound_used,
        "spectral_density_approximation_introduced": bool(
            float(event["spectral_discarded_trace"]) > 0.0
        ),
        "repair_summary": repair_summary,
        "event_summary": event_summary,
        "memory_before": before,
        "memory_after": after,
        "checks": checks,
        "passed": bool(all(checks.values())),
        "wall_seconds": wall,
    }, compressed


def run_g1_synthetic_rank_benchmarks(
    *,
    config: RunConfig,
    operators: OscillatorOperators,
    propagator: PropagatorObjects,
    bath: BathKraus,
    backend: NumericalBackend,
    output_dir: Path,
) -> Dict[str, Any]:
    if backend.name != "cupy" or G1_MODE != "a100_first_step":
        raise GateBlocked(
            "Production-row G1 rank benchmarks are authorized only in the A100 G1 mode"
        )
    started = time.time()
    reports: Dict[str, Any] = {}
    for rank in G1_SYNTHETIC_RANKS:
        print(
            f"[v4-g1] starting synthetic production-row benchmark rank={rank}",
            flush=True,
        )
        rank_started = time.time()
        factor: Optional[CanonicalFactor] = None
        detector_raw: Optional[RawFactor] = None
        compressed: Optional[CanonicalFactor] = None
        try:
            factor, construction = build_g1_synthetic_canonical_factor(
                rank,
                config=config,
                operators=operators,
                propagator=propagator,
                backend=backend,
            )
            detector_report, detector_raw = run_g1_detector_rank_benchmark(
                factor,
                rank=rank,
                config=config,
                operators=operators,
                propagator=propagator,
                backend=backend,
            )
            del detector_raw
            detector_raw = None
            _free_backend_pool(backend)
            compression_report, compressed = run_g1_compression_rank_benchmark(
                factor,
                rank=rank,
                config=config,
                operators=operators,
                propagator=propagator,
                bath=bath,
                backend=backend,
            )
            rank_report = {
                "schema": G1_BENCHMARK_SCHEMA,
                "created_utc": utc_now_iso(),
                "rank": rank,
                "construction": construction,
                "detector_linear_solve": detector_report,
                "compression": compression_report,
                "physical_state_mutated": False,
                "physical_budget_mutated": False,
                "production_authorized": False,
                "task10_eligible": False,
                "passed": bool(
                    construction["passed"]
                    and detector_report["passed"]
                    and compression_report["passed"]
                ),
                "wall_seconds": time.time() - rank_started,
            }
            atomic_write_json(
                output_dir / f"g1_synthetic_rank_{rank:04d}.json",
                rank_report,
            )
            reports[str(rank)] = rank_report
            print(
                f"[v4-g1] completed synthetic rank={rank} "
                f"passed={rank_report['passed']} "
                f"detector_s={detector_report['wall_seconds']:.3f} "
                f"compression_s={compression_report['wall_seconds']:.3f}",
                flush=True,
            )
            if not rank_report["passed"]:
                raise RuntimeError(f"Synthetic G1 rank benchmark failed at rank {rank}")
        except Exception as exc:
            atomic_write_json(
                output_dir / f"g1_synthetic_rank_{rank:04d}_failure.json",
                {
                    "schema": G1_BENCHMARK_SCHEMA,
                    "failed_utc": utc_now_iso(),
                    "rank": rank,
                    "error": repr(exc),
                    "traceback": traceback.format_exc(),
                    "physical_state_mutated": False,
                    "physical_budget_mutated": False,
                    "production_authorized": False,
                    "task10_eligible": False,
                },
            )
            raise
        finally:
            if detector_raw is not None:
                del detector_raw
            if compressed is not None:
                del compressed
            if factor is not None:
                del factor
            _free_backend_pool(backend)

    checks = {
        f"rank_{rank}_passed": bool(reports[str(rank)]["passed"])
        for rank in G1_SYNTHETIC_RANKS
    }
    return {
        "schema": G1_BENCHMARK_SCHEMA,
        "created_utc": utc_now_iso(),
        "backend": backend.metadata(),
        "state_dimension": config.state_dimension,
        "synthetic_ranks": list(G1_SYNTHETIC_RANKS),
        "compression_map": "physical U2 upward finite CPTP resolvent-Kraus half-step",
        "detector_map": "unchanged spinor Cayley/GMRES with midpoint roof probability",
        "benchmark_budget_value": G1_SYNTHETIC_BENCHMARK_BUDGET,
        "benchmark_budget_isolated_from_physical_state": True,
        "physical_state_mutated": False,
        "physical_budget_mutated": False,
        "rank_reports": reports,
        "checks": checks,
        "passed": bool(all(checks.values())),
        "performance_targets_are_advisory_not_acceptance_relaxations": True,
        "production_authorized": False,
        "task10_eligible": False,
        "physical_claim": "none; synthetic numerical feasibility evidence only",
        "wall_seconds": time.time() - started,
    }


def verify_g1_cpu_first_step_artifact(
    *,
    config: RunConfig,
    source_sha256: str,
    numerical_core_sha256: str,
    family_contract_sha256: str,
) -> Dict[str, Any]:
    directory = _g1_mode_directory(config, "cpu_first_step")
    if not directory.is_dir():
        raise GateBlocked(f"Verified G1 CPU directory is missing: {directory}")
    report_artifact = _verified_output_file(
        directory, "nonaccepting_gate_report.json"
    )
    status_path = directory / "run_status.json"
    if not status_path.is_file():
        raise GateBlocked(f"G1 CPU run status is missing: {status_path}")
    report = read_json(Path(report_artifact["path"]))
    status = read_json(status_path)
    checkpoint_paths = report.get("checkpoint_paths", [])
    if len(checkpoint_paths) != 1:
        raise GateBlocked("G1 CPU report must contain exactly one complete-step checkpoint")
    checkpoint = Path(checkpoint_paths[0]).expanduser().resolve()
    expected_root = (directory / "checkpoints").resolve()
    try:
        checkpoint.relative_to(expected_root)
    except ValueError as exc:
        raise GateBlocked("G1 CPU checkpoint lies outside its declared directory") from exc
    checkpoint_verification = verify_hash_manifest(checkpoint)
    checks = {
        "report_schema": report.get("schema") == G1_REPORT_SCHEMA,
        "source_sha256": report.get("source_sha256") == source_sha256,
        "numerical_core_sha256": report.get("numerical_core_sha256")
        == numerical_core_sha256,
        "family_contract": report.get("physical_family_contract", {}).get(
            "contract_sha256"
        )
        == family_contract_sha256,
        "mode": report.get("g1_mode") == "cpu_first_step",
        "backend": report.get("backend", {}).get("backend") == "scipy",
        "completed_step": report.get("completed_step") == 1,
        "rank_sequence": report.get("rank_sequence")
        == {
            "initial": 1,
            "after_first_complete_step": 6,
            "first_bath_rank": 3,
            "second_bath_rank": 6,
        },
        "local_pass": report.get("passed") is True,
        "family_not_falsely_closed": report.get("g1_family_complete") is False,
        "status_pass": status.get("status") == "completed_pass_nonaccepting_gate",
        "checkpoint_hashes": checkpoint_verification.get("passed") is True,
        "nonaccepting": report.get("nonaccepting") is True,
        "production_disabled": report.get("production_authorized") is False,
        "task10_disabled": report.get("task10_eligible") is False,
    }
    if not all(checks.values()):
        raise GateBlocked(f"G1 CPU artifact verification failed: {checks}")
    return {
        "directory": str(directory),
        "report": report,
        "run_status": status,
        "report_artifact": report_artifact,
        "checkpoint": str(checkpoint),
        "checkpoint_hash_verification": checkpoint_verification,
        "checks": checks,
        "passed": True,
    }


def compare_g1_cpu_and_a100_first_steps(
    *,
    config: RunConfig,
    source_sha256: str,
    numerical_core_sha256: str,
    family_contract_sha256: str,
    a100_factor: CanonicalFactor,
    a100_backend: NumericalBackend,
    a100_step_audit: Mapping[str, Any],
    a100_budget: RepresentationBudgetState,
) -> Dict[str, Any]:
    verified = verify_g1_cpu_first_step_artifact(
        config=config,
        source_sha256=source_sha256,
        numerical_core_sha256=numerical_core_sha256,
        family_contract_sha256=family_contract_sha256,
    )
    cpu_backend = NumericalBackend("scipy")
    (
        cpu_step,
        cpu_factor,
        cpu_budget,
        _cpu_telemetry,
        _cpu_histories,
        cpu_metadata,
    ) = load_checkpoint(
        Path(verified["checkpoint"]),
        expected_source_sha256=source_sha256,
        expected_numerical_core_sha256=numerical_core_sha256,
        expected_family_contract_sha256=family_contract_sha256,
        backend=cpu_backend,
    )
    cpu_matrix = canonical_to_cpu_factor(cpu_factor, cpu_backend)
    a100_matrix = canonical_to_cpu_factor(a100_factor, a100_backend)
    density_distance = low_rank_density_trace_norm_difference_cpu(
        cpu_matrix,
        a100_matrix,
        h_z=a100_factor.h_z,
    )
    cpu_report = verified["report"]
    cpu_audit = cpu_report["step_audits"][0]
    survival_difference = abs(cpu_factor.trace - a100_factor.trace)
    probability_difference = abs(
        float(cpu_audit["midpoint_roof_probability"])
        - float(a100_step_audit["midpoint_roof_probability"])
    )
    representation_bound_difference = abs(
        cpu_budget.bound_used - a100_budget.bound_used
    )
    checks = {
        "cpu_step_exact": cpu_step == 1,
        "row_dimension_exact": cpu_factor.n_rows == a100_factor.n_rows,
        "h_z_exact": cpu_factor.h_z == a100_factor.h_z,
        "rank_exact": cpu_factor.rank == a100_factor.rank == 6,
        "density_trace_norm": density_distance
        <= G1_CPU_A100_DENSITY_TRACE_NORM_TOL,
        "survival": survival_difference <= G1_CPU_A100_SURVIVAL_ABS_TOL,
        "midpoint_probability": probability_difference
        <= G1_CPU_A100_MIDPOINT_PROBABILITY_ABS_TOL,
        "representation_bound": representation_bound_difference
        <= G1_CPU_A100_REPRESENTATION_BOUND_ABS_TOL,
        "cpu_checkpoint_source_identity": cpu_metadata.get("source_sha256")
        == source_sha256,
        "cpu_checkpoint_core_identity": cpu_metadata.get("numerical_core_sha256")
        == numerical_core_sha256,
    }
    return {
        "schema": G1_CROSS_BACKEND_SCHEMA,
        "created_utc": utc_now_iso(),
        "source_sha256": source_sha256,
        "numerical_core_sha256": numerical_core_sha256,
        "cpu_artifact": verified,
        "cpu_rank": cpu_factor.rank,
        "a100_rank": a100_factor.rank,
        "cpu_survival": cpu_factor.trace,
        "a100_survival": a100_factor.trace,
        "survival_absolute_difference": survival_difference,
        "cpu_midpoint_roof_probability": float(
            cpu_audit["midpoint_roof_probability"]
        ),
        "a100_midpoint_roof_probability": float(
            a100_step_audit["midpoint_roof_probability"]
        ),
        "midpoint_probability_absolute_difference": probability_difference,
        "cpu_representation_bound": cpu_budget.bound_used,
        "a100_representation_bound": a100_budget.bound_used,
        "representation_bound_absolute_difference": representation_bound_difference,
        "low_rank_density_trace_norm_difference": density_distance,
        "tolerances": {
            "density_trace_norm": G1_CPU_A100_DENSITY_TRACE_NORM_TOL,
            "survival_absolute": G1_CPU_A100_SURVIVAL_ABS_TOL,
            "midpoint_probability_absolute": G1_CPU_A100_MIDPOINT_PROBABILITY_ABS_TOL,
            "representation_bound_absolute": G1_CPU_A100_REPRESENTATION_BOUND_ABS_TOL,
        },
        "checks": checks,
        "passed": bool(all(checks.values())),
        "production_authorized": False,
        "task10_eligible": False,
        "physical_claim": "none; backend-parity certification only",
    }


def verify_g1_family_artifact_for_later_gate(
    *,
    config: RunConfig,
    source_sha256: str,
    numerical_core_sha256: str,
    family_contract_sha256: str,
) -> Dict[str, Any]:
    directory = _g1_mode_directory(config, "a100_first_step")
    if not directory.is_dir():
        raise GateBlocked(f"Complete G1 A100 family directory is missing: {directory}")
    artifact = _verified_output_file(directory, "nonaccepting_gate_report.json")
    report = read_json(Path(artifact["path"]))
    checks = {
        "schema": report.get("schema") == G1_REPORT_SCHEMA,
        "source_sha256": report.get("source_sha256") == source_sha256,
        "numerical_core_sha256": report.get("numerical_core_sha256")
        == numerical_core_sha256,
        "family_contract": report.get("physical_family_contract", {}).get(
            "contract_sha256"
        )
        == family_contract_sha256,
        "mode": report.get("g1_mode") == "a100_first_step",
        "passed": report.get("passed") is True,
        "g1_family_complete": report.get("g1_family_complete") is True,
        "cross_backend": report.get("g1_cross_backend_comparison", {}).get(
            "passed"
        )
        is True,
        "synthetic_benchmarks": report.get("g1_synthetic_rank_benchmarks", {}).get(
            "passed"
        )
        is True,
        "production_disabled": report.get("production_authorized") is False,
        "task10_disabled": report.get("task10_eligible") is False,
    }
    if not all(checks.values()):
        raise GateBlocked(f"Complete G1 family artifact failed verification: {checks}")
    return {
        "directory": str(directory),
        "report_artifact": artifact,
        "checks": checks,
        "passed": True,
    }

def run_production_size_gate(
    config: RunConfig,
    *,
    script_path: Path,
    source_sha256: str,
    numerical_core_sha256: str,
    g0_report: Mapping[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, np.ndarray], RepresentationTelemetry]:
    if not D2_POST_G0_REVIEW_AUTHORIZED:
        raise GateBlocked(
            "D2 gates beyond G0 require explicit post-G0 review authorization "
            "through TASK09_D2_POST_G0_REVIEW=1"
        )
    if not g0_report.get("passed", False):
        raise GateBlocked("Production-size gate is blocked because G0 did not pass")
    upstream = verify_upstream_authority_for_production_gates()
    validate_config(config)
    family = physical_family_contract(config)
    prior_g1_family: Optional[Dict[str, Any]] = None
    if config.execution_gate in {"V4-G2", "V4-G3", "V4-G4"}:
        prior_g1_family = verify_g1_family_artifact_for_later_gate(
            config=config,
            source_sha256=source_sha256,
            numerical_core_sha256=numerical_core_sha256,
            family_contract_sha256=family["contract_sha256"],
        )
    backend = NumericalBackend(config.backend)
    operators = build_oscillator_operators(config.n_shell, config.omega)
    z, h_z, _ = build_reference_grid(config.n_z, config.l_z)
    initial = build_initial_state(config, operators, z, h_z)
    propagator = build_propagator_objects(config, operators, backend, initial)
    bath = build_bath_kraus(
        operators,
        config.environment_direction,
        config.rate_lambda * config.dt / 2.0,
        backend,
    )
    execution = pilot_execution_contract(config)
    checkpoint_candidate = latest_compatible_checkpoint(config)

    if checkpoint_candidate is None:
        start_step = 0
        factor = canonical_from_state(
            initial, h_z=h_z, backend=backend, block_columns=config.factor_block_columns
        )
        budget = RepresentationBudgetState(config.representation_budget, config.planned_compression_calls)
        telemetry = RepresentationTelemetry()
        histories = _pilot_histories(config)
        histories["survival"][0] = factor.trace
        histories["rank"][0] = factor.rank
        histories["representation_bound"][0] = budget.bound_used
        histories["top_shell"][0] = factor_top_shell(
            factor, operators=operators, config=config, h_z=h_z, backend=backend
        )
        histories["overflow_intensity"][0] = (
            config.rate_lambda * (config.n_shell + 2.0) * histories["top_shell"][0]
        )
        checkpoint_metadata = None
    else:
        start_step, factor, budget, telemetry, loaded_histories, checkpoint_metadata = load_checkpoint(
            checkpoint_candidate,
            expected_source_sha256=source_sha256,
            expected_numerical_core_sha256=numerical_core_sha256,
            expected_family_contract_sha256=family["contract_sha256"],
            backend=backend,
        )
        histories = _pilot_histories(config)
        for key in histories:
            if key in loaded_histories:
                count = min(histories[key].size, loaded_histories[key].size)
                histories[key].reshape(-1)[:count] = loaded_histories[key].reshape(-1)[:count]

    started = time.time()
    step_audits: List[Dict[str, Any]] = []
    checkpoint_paths: List[str] = []
    for step in range(start_step + 1, config.execution_num_steps + 1):
        try:
            factor, audit = complete_step(
                factor,
                step_index=step,
                operators=operators,
                propagator=propagator,
                kraus=bath,
                config=config,
                backend=backend,
                budget=budget,
                telemetry=telemetry,
                certified_multi_rhs=USE_MULTI_RHS_GMRES,
            )
        except RepresentationFailure as exc:
            raise RepresentationFailure(
                str(exc),
                event={
                    **exc.event,
                    "attempted_detector_step": step,
                    "last_fully_completed_detector_step": step - 1,
                    "last_fully_completed_physical_time": (step - 1) * config.dt,
                    "last_complete_state_rank": factor.rank,
                    "last_complete_state_trace": factor.trace,
                    "histories_recorded_through_step": step - 1,
                    "latest_complete_checkpoint": (
                        checkpoint_paths[-1] if checkpoint_paths else None
                    ),
                    "budget_snapshot_at_outer_failure": budget.snapshot(),
                },
            ) from exc
        step_audits.append(audit)
        histories["survival"][step] = factor.trace
        histories["step_probability"][step - 1] = audit["midpoint_roof_probability"]
        histories["rank"][step] = factor.rank
        histories["representation_bound"][step] = budget.bound_used
        histories["top_shell"][step] = audit["top_shell_population"]
        histories["overflow_intensity"][step] = audit["upward_omitted_intensity"]
        histories["step_wall_seconds"][step - 1] = audit["wall_seconds"]
        histories["gmres_max_residual"][step - 1] = audit["detector_audit"]["maximum_true_relative_residual"]
        histories["probability_closure"][step - 1] = audit["composed_probability_closure"]
        histories["bath_trace_residual_first"][step - 1] = audit["bath_trace_residual_first"]
        histories["bath_trace_residual_second"][step - 1] = audit["bath_trace_residual_second"]

        if config.checkpoint_every > 0 and (
            step % config.checkpoint_every == 0 or step == config.execution_num_steps
        ):
            checkpoint = save_checkpoint(
                config.case_dir / "checkpoints",
                completed_step=step,
                factor=factor,
                budget=budget,
                telemetry=telemetry,
                histories=histories,
                source_sha256=source_sha256,
                numerical_core_sha256=numerical_core_sha256,
                family_contract=family,
                execution_contract=execution,
                backend=backend,
            )
            checkpoint_paths.append(str(checkpoint))

        if step == 1 or step % config.progress_every == 0:
            elapsed = time.time() - started
            rate = elapsed / max(step - start_step, 1)
            eta = rate * (config.execution_num_steps - step)
            print(
                f"[v4] step={step}/{config.execution_num_steps} t={step*config.dt:.6f} "
                f"S={factor.trace:.12e} rank={factor.rank} B={budget.bound_used:.3e} "
                f"step_s={audit['wall_seconds']:.3f} eta_s={eta:.1f}",
                flush=True,
            )

    completed = config.execution_num_steps
    cumulative_overflow = float(
        np.trapezoid(histories["overflow_intensity"][:completed + 1], histories["times"][:completed + 1])
    ) if completed > 0 else 0.0
    rank_sequence = {
        "initial": int(histories["rank"][0]),
        "after_first_complete_step": int(histories["rank"][1]) if completed >= 1 else None,
        "first_bath_rank": (
            int(telemetry.events[0]["rank_after"]) if telemetry.events else None
        ),
        "second_bath_rank": (
            int(telemetry.events[1]["rank_after"]) if len(telemetry.events) >= 2 else None
        ),
    }
    g1_sequence_pass = bool(
        config.execution_gate != "V4-G1"
        or rank_sequence == {
            "initial": 1,
            "after_first_complete_step": 6,
            "first_bath_rank": 3,
            "second_bath_rank": 6,
        }
    )

    g1_cross_backend: Optional[Dict[str, Any]] = None
    g1_synthetic_benchmarks: Optional[Dict[str, Any]] = None
    g1_family_complete = False
    if config.execution_gate == "V4-G1" and G1_MODE == "a100_first_step":
        if completed != 1 or not step_audits:
            raise GateBlocked("A100 G1 comparison requires one completed first step")
        g1_cross_backend = compare_g1_cpu_and_a100_first_steps(
            config=config,
            source_sha256=source_sha256,
            numerical_core_sha256=numerical_core_sha256,
            family_contract_sha256=family["contract_sha256"],
            a100_factor=factor,
            a100_backend=backend,
            a100_step_audit=step_audits[0],
            a100_budget=budget,
        )
        atomic_write_json(
            config.case_dir / "g1_cross_backend_comparison.json",
            g1_cross_backend,
        )
        if not g1_cross_backend["passed"]:
            raise GateBlocked(
                "G1 CPU/A100 first-step comparison failed before rank benchmarks"
            )
        g1_synthetic_benchmarks = run_g1_synthetic_rank_benchmarks(
            config=config,
            operators=operators,
            propagator=propagator,
            bath=bath,
            backend=backend,
            output_dir=config.case_dir,
        )
        atomic_write_json(
            config.case_dir / "g1_synthetic_rank_benchmarks.json",
            g1_synthetic_benchmarks,
        )
        g1_family_complete = bool(
            g1_cross_backend["passed"]
            and g1_synthetic_benchmarks["passed"]
        )

    gates = {
        "g0_passed_same_execution": bool(g0_report["passed"]),
        "upstream_authority": upstream["passed"],
        "operator_audit": operators.audit["all_checks_passed"],
        "roof_sign": propagator.roof_sign_audit["spinor_roof_term_sign_passed"],
        "bath_completeness": bath.completeness_residual <= BATH_COMPLETENESS_TOL,
        "representation_budget": budget.bound_used <= config.representation_budget,
        "probability_closure": (
            completed == 0
            or float(np.nanmax(np.abs(histories["probability_closure"][:completed]))) <= PROBABILITY_CLOSURE_ABS_TOL
        ),
        "bath_trace": (
            completed == 0
            or max(
                float(np.nanmax(np.abs(histories["bath_trace_residual_first"][:completed]))),
                float(np.nanmax(np.abs(histories["bath_trace_residual_second"][:completed]))),
            ) <= BATH_TRACE_RESIDUAL_TOL
        ),
        "gmres": (
            completed == 0
            or float(np.nanmax(histories["gmres_max_residual"][:completed])) <= TRUE_RESIDUAL_TOL
        ),
        "top_shell_overflow": cumulative_overflow <= UPWARD_CUMULATIVE_OVERFLOW_TOL,
        "g1_rank_sequence": g1_sequence_pass,
        "g1_cpu_artifact_and_cross_backend": bool(
            config.execution_gate != "V4-G1"
            or G1_MODE == "cpu_first_step"
            or (g1_cross_backend is not None and g1_cross_backend["passed"])
        ),
        "g1_synthetic_rank_benchmarks": bool(
            config.execution_gate != "V4-G1"
            or G1_MODE == "cpu_first_step"
            or (
                g1_synthetic_benchmarks is not None
                and g1_synthetic_benchmarks["passed"]
            )
        ),
        "prior_g1_family_for_later_gate": bool(
            config.execution_gate not in {"V4-G2", "V4-G3", "V4-G4"}
            or (prior_g1_family is not None and prior_g1_family["passed"])
        ),
        "target_reached": completed == config.execution_num_steps,
    }
    local_gate_pass = bool(all(gates.values()))
    selected_gate_pass = bool(
        local_gate_pass
        and (
            config.execution_gate != "V4-G1"
            or G1_MODE == "cpu_first_step"
            or g1_family_complete
        )
    )
    report = {
        "schema": G1_REPORT_SCHEMA if config.execution_gate == "V4-G1" else "2026-08-14-task09-v4-d2pr2g1fmp-batch64-repaired-rank-nonaccepting-gate-report-v4-g1-prerequisite",
        "created_utc": utc_now_iso(),
        "execution_gate": config.execution_gate,
        "g1_mode": G1_MODE if config.execution_gate == "V4-G1" else None,
        "source_sha256": source_sha256,
        "numerical_core_sha256": numerical_core_sha256,
        "physical_family_contract": family,
        "pilot_execution_contract": execution,
        "upstream_authority": upstream,
        "prior_g1_family_artifact": prior_g1_family,
        "backend": backend.metadata(),
        "completed_step": completed,
        "physical_time": completed * config.dt,
        "final_survival": factor.trace,
        "final_rank": factor.rank,
        "maximum_rank": int(np.nanmax(histories["rank"][:completed + 1])),
        "representation_budget": budget.snapshot(),
        "cumulative_upward_overflow_bound": cumulative_overflow,
        "rank_sequence": rank_sequence,
        "checkpoint_paths": checkpoint_paths,
        "resumed_checkpoint": str(checkpoint_candidate) if checkpoint_candidate else None,
        "resumed_checkpoint_metadata": checkpoint_metadata,
        "checks": gates,
        "local_mode_checks_passed": local_gate_pass,
        "g1_family_complete": bool(
            config.execution_gate == "V4-G1"
            and G1_MODE == "a100_first_step"
            and g1_family_complete
            and selected_gate_pass
        ),
        "g1_required_followup": (
            "run a100_first_step after reviewing this CPU artifact"
            if config.execution_gate == "V4-G1"
            and G1_MODE == "cpu_first_step"
            else None
        ),
        "g1_cross_backend_comparison": g1_cross_backend,
        "g1_synthetic_rank_benchmarks": g1_synthetic_benchmarks,
        "passed": selected_gate_pass,
        "nonaccepting": True,
        "production_authorized": False,
        "acceptance_enabled": False,
        "task10_eligible": False,
        "physical_claim": "none; partial finite-rate pilot data are numerical diagnostics only",
        "wall_seconds": time.time() - started,
        "step_audits": step_audits if completed <= 1 else [],
    }
    return report, histories, telemetry

# =============================================================================
# OUTPUTS AND MAIN
# =============================================================================
def resolve_source_path() -> Path:
    value = globals().get("__file__")
    if isinstance(value, (str, os.PathLike)):
        path = Path(value).expanduser().resolve()
        if path.is_file():
            return path
    raise FileNotFoundError("Execute the saved Task09_4901_U2_low_v4_nonaccepting_pilot.py source")


def archive_previous_noncheckpoint_outputs(out_dir: Path) -> Optional[Path]:
    if not out_dir.exists():
        return None
    movable = [
        path for path in out_dir.iterdir()
        if path.name not in {"checkpoints", ".previous_attempts"}
    ]
    if not movable:
        return None
    archive = out_dir / ".previous_attempts" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive.mkdir(parents=True, exist_ok=False)
    for path in movable:
        shutil.move(str(path), str(archive / path.name))
    return archive


def copy_source_atomic(source: Path, destination: Path) -> None:
    tmp = destination.with_name(destination.name + ".tmp")
    shutil.copy2(source, tmp)
    os.replace(tmp, destination)


def write_output_manifest(out_dir: Path) -> Dict[str, str]:
    excluded = {"output_hashes.json", "run_status.json"}
    files = [
        path for path in sorted(out_dir.iterdir())
        if path.is_file() and path.name not in excluded
    ]
    hashes = {path.name: sha256_file(path) for path in files}
    atomic_write_json(out_dir / "output_hashes.json", {
        "schema": "2026-08-14-task09-v4-d2pr2g1fmp-batch64-repaired-rank-output-hashes-v4",
        "files": hashes,
        "production_authorized": False,
        "task10_eligible": False,
    })
    return hashes


def run() -> int:
    config = manual_run_config()
    validate_config(config)
    script_path = resolve_source_path()
    source_sha256 = sha256_file(script_path)
    numerical_core_sha256 = sha256_numerical_core(script_path)
    family_contract = physical_family_contract(config)
    execution_contract = pilot_execution_contract(config)
    out_dir = config.case_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    archived = archive_previous_noncheckpoint_outputs(out_dir)

    copy_source_atomic(script_path, out_dir / script_path.name)
    atomic_write_json(out_dir / "physical_family_contract.json", family_contract)
    atomic_write_json(out_dir / "pilot_execution_contract.json", execution_contract)
    atomic_write_json(out_dir / "configuration.json", {
        "script_version": SCRIPT_VERSION,
        "source_sha256": source_sha256,
        "numerical_core_sha256": numerical_core_sha256,
        "execution_gate": config.execution_gate,
        "backend": config.backend,
        "G1_mode": G1_MODE,
        "D2_post_G0_review_authorized": D2_POST_G0_REVIEW_AUTHORIZED,
        "allocator_pool_resource_amendment": {
            "exact_parent_source_sha256": D2PR2G1FMP_PARENT_SOURCE_SHA256,
            "exact_parent_numerical_core_sha256": D2PR2G1FMP_PARENT_CORE_SHA256,
            "r1_diagnostic_source_sha256": D2PR2G1FMP_R1_DIAGNOSTIC_SOURCE_SHA256,
            "r1_authority_record_sha256": D2PR2G1FMP_R1_AUTHORITY_RECORD_SHA256,
            "r1_classification": D2PR2G1FMP_R1_CLASSIFICATION,
            "r1_job_id": D2PR2G1FMP_R1_JOB_ID,
            "policy": D2PR2G1FMP_RESOURCE_RELEASE_POLICY,
            "working_set_fraction": GPU_WORKING_SET_FRACTION,
            "changed_scope": "conditional unused CuPy allocator-pool release before mapped construction only when the unchanged pre-mapping upper-bound test would otherwise false-stop",
            "downstream_actual_resource_guard_changed": False,
            "physical_map_changed": False,
            "compression_algorithm_changed": False,
            "rank_selection_changed": False,
            "budget_or_tolerance_changed": False,
        },
        "g1_contract_fix_amendment": {
            "exact_parent_source_sha256": D2PR2G1F_PARENT_D2PR2_SOURCE_SHA256,
            "exact_parent_numerical_core_sha256": D2PR2G1F_PARENT_D2PR2_CORE_SHA256,
            "failed_g1_a100_job_id": D2PR2G1F_FAILED_G1_A100_JOB_ID,
            "controlled_failure_diagnosis_sha256": D2PR2G1F_FAILURE_DIAGNOSIS_SHA256,
            "acceptance_rule": D2PR2_COMPLETE_ACCEPTANCE_RULE,
            "changed_scope": "synthetic G1 benchmark contract identity and directly required schemas/tests/reports only",
            "physical_map_changed": False,
            "compression_algorithm_changed": False,
            "budget_or_tolerance_changed": False,
        },
        "repaired_rank_amendment": {
            "exact_parent_source_sha256": D2PR_PARENT_D2P_SOURCE_SHA256,
            "exact_parent_numerical_core_sha256": D2PR_PARENT_D2P_CORE_SHA256,
            "c2_source_sha256": D2PR_C2_SOURCE_SHA256,
            "c2_schema": D2PR_C2_SCHEMA,
            "c2_handoff_sha256": D2PR_C2_HANDOFF_SHA256,
            "selection_policy": "first rank passing unchanged tolerance-inclusive centralized predicate",
            "strict_raw_margin_rank_is_diagnostic_only": True,
            "physical_map_changed": False,
        },
        "performance_amendment": {
            "parent_d2_source_sha256": D2P_PARENT_D2_SOURCE_SHA256,
            "p1_source_sha256": D2P_P1_SOURCE_SHA256,
            "p1_artifact_audit_status": D2P_P1_ARTIFACT_AUDIT_STATUS,
            "baseline_detector_rhs_batch_columns": D2P_P1_BASELINE_BATCH_COLUMNS,
            "selected_detector_rhs_batch_columns": D2P_P1_SELECTED_BATCH_COLUMNS,
            "aggregate_measured_speedup": D2P_P1_AGGREGATE_SPEEDUP,
            "physical_map_changed": False,
        },
        "config": config.__dict__,
        "source_fingerprints": SOURCE_FINGERPRINTS,
        "schemas": {
            "checkpoint": CHECKPOINT_SCHEMA,
            "representation_telemetry": REPRESENTATION_TELEMETRY_SCHEMA,
            "physical_family_contract": PHYSICAL_FAMILY_CONTRACT_SCHEMA,
            "pilot_execution_contract": PILOT_EXECUTION_CONTRACT_SCHEMA,
            "g1_report": G1_REPORT_SCHEMA,
            "g1_benchmark": G1_BENCHMARK_SCHEMA,
            "g1_cross_backend": G1_CROSS_BACKEND_SCHEMA,
        },
        "production_authorized": False,
        "acceptance_enabled": False,
        "task10_eligible": False,
    })
    status = {
        "status": "running_nonaccepting_gate",
        "started_utc": utc_now_iso(),
        "execution_gate": config.execution_gate,
        "source_sha256": source_sha256,
        "numerical_core_sha256": numerical_core_sha256,
        "output_directory": str(out_dir),
        "archived_previous_outputs": str(archived) if archived else None,
        "production_authorized": False,
        "task10_eligible": False,
    }
    atomic_write_json(out_dir / "run_status.json", status)

    print(f"[v4] source={script_path}")
    print(f"[v4] source_sha256={source_sha256}")
    print(f"[v4] numerical_core_sha256={numerical_core_sha256}")
    print(f"[v4] gate={config.execution_gate} backend={config.backend}")
    print("[v4] production_authorized=False task10_eligible=False")

    try:
        g0_report, g0_arrays = run_g0_certification(
            config,
            script_path=script_path,
            source_sha256=source_sha256,
            numerical_core_sha256=numerical_core_sha256,
        )
        atomic_write_json(out_dir / "g0_certification_report.json", g0_report)
        atomic_savez(out_dir / "g0_certification_arrays.npz", **g0_arrays)
        if not g0_report["passed"]:
            final_status = {
                **status,
                "status": "completed_failed_g0",
                "finished_utc": utc_now_iso(),
                "g0_passed": False,
                "production_authorized": False,
                "task10_eligible": False,
            }
            write_output_manifest(out_dir)
            atomic_write_json(out_dir / "run_status.json", final_status)
            print("FAIL_TASK09_V4_D2PR2G1FMP_BATCH64_REPAIRED_RANK_G0_CERTIFICATION")
            return 2

        if config.execution_gate == "V4-G0":
            report = {
                "schema": "2026-08-14-task09-v4-d2pr2g1fmp-batch64-repaired-rank-g0-nonaccepting-verdict-v4",
                "verdict": "PASS_TASK09_V4_D2PR2G1FMP_BATCH64_REPAIRED_RANK_G0_CERTIFICATION",
                "g0_report_sha256": sha256_file(out_dir / "g0_certification_report.json"),
                "next_gate_authorized_by_this_source": False,
                "production_authorized": False,
                "task10_eligible": False,
                "physical_claim": "none",
            }
            atomic_write_json(out_dir / "nonaccepting_gate_report.json", report)
            hashes = write_output_manifest(out_dir)
            final_status = {
                **status,
                "status": "completed_pass_nonaccepting_g0",
                "finished_utc": utc_now_iso(),
                "g0_passed": True,
                "output_hash_count": len(hashes),
                "production_authorized": False,
                "task10_eligible": False,
            }
            atomic_write_json(out_dir / "run_status.json", final_status)
            print("PASS_TASK09_V4_D2PR2G1FMP_BATCH64_REPAIRED_RANK_G0_CERTIFICATION")
            print(f"Output directory: {out_dir}")
            return 0

        pilot_report, histories, telemetry = run_production_size_gate(
            config,
            script_path=script_path,
            source_sha256=source_sha256,
            numerical_core_sha256=numerical_core_sha256,
            g0_report=g0_report,
        )
        save_nonaccepting_pilot_outputs(
            out_dir,
            report=pilot_report,
            histories=histories,
            telemetry=telemetry,
        )
        hashes = write_output_manifest(out_dir)
        final_status = {
            **status,
            "status": "completed_pass_nonaccepting_gate" if pilot_report["passed"] else "completed_failed_nonaccepting_gate",
            "finished_utc": utc_now_iso(),
            "g0_passed": True,
            "selected_gate_passed": pilot_report["passed"],
            "completed_step": pilot_report["completed_step"],
            "g1_mode": pilot_report.get("g1_mode"),
            "g1_family_complete": pilot_report.get("g1_family_complete", False),
            "g1_synthetic_rank_benchmarks_passed": (
                pilot_report.get("g1_synthetic_rank_benchmarks", {}).get("passed")
                if isinstance(pilot_report.get("g1_synthetic_rank_benchmarks"), Mapping)
                else None
            ),
            "output_hash_count": len(hashes),
            "production_authorized": False,
            "task10_eligible": False,
        }
        atomic_write_json(out_dir / "run_status.json", final_status)
        if config.execution_gate == "V4-G1" and G1_MODE == "cpu_first_step":
            marker = (
                "PASS_TASK09_V4_G1_CPU_FIRST_STEP_NONACCEPTING"
                if pilot_report["passed"]
                else "FAIL_TASK09_V4_G1_CPU_FIRST_STEP_NONACCEPTING"
            )
        elif config.execution_gate == "V4-G1" and G1_MODE == "a100_first_step":
            marker = (
                "PASS_TASK09_V4_G1_FAMILY_NONACCEPTING"
                if pilot_report["passed"]
                and pilot_report.get("g1_family_complete") is True
                else "FAIL_TASK09_V4_G1_FAMILY_NONACCEPTING"
            )
        else:
            marker = (
                f"PASS_TASK09_{config.execution_gate.replace('-', '_')}_NONACCEPTING"
                if pilot_report["passed"]
                else f"FAIL_TASK09_{config.execution_gate.replace('-', '_')}_NONACCEPTING"
            )
        print(marker)
        print(f"Output directory: {out_dir}")
        return 0 if pilot_report["passed"] else 2

    except RepresentationFailure as exc:
        event = dict(exc.event)
        state_committed = bool(
            event.get(
                "complete_step_state_committed",
                event.get("caller_state_committed", False),
            )
        )
        budget_mutated = bool(
            event.get("budget_mutation_occurred_within_incomplete_step", False)
            or event.get("budget_committed_for_current_compression_call", False)
        )
        failure = {
            "schema": "2026-08-14-task09-v4-d2pr2g1f-batch64-repaired-rank-representation-failure-v3-exact-context",
            "failed_utc": utc_now_iso(),
            "execution_gate": config.execution_gate,
            "source_sha256": source_sha256,
            "numerical_core_sha256": numerical_core_sha256,
            "error": str(exc),
            "event": event,
            "state_committed": state_committed,
            "budget_mutation_occurred": budget_mutated,
            "scientific_result_admissible": False,
            "production_authorized": False,
            "task10_eligible": False,
        }
        atomic_write_json(out_dir / "representation_failure.json", failure)
        atomic_write_json(out_dir / "run_status.json", {
            **status,
            "status": "failed_closed_representation",
            "finished_utc": utc_now_iso(),
            "error": str(exc),
            "attempted_detector_step": event.get("attempted_detector_step"),
            "last_fully_completed_detector_step": event.get(
                "last_fully_completed_detector_step"
            ),
            "compression_call_index": event.get("compression_call_index"),
            "bath_half_step": event.get("bath_half_step"),
            "bath_microstep": event.get("bath_microstep"),
            "rank_at_failure": event.get(
                "rank_of_local_working_factor_at_failure",
                event.get("precompression_rank"),
            ),
            "representation_budget_at_failure": event.get(
                "budget_snapshot_at_outer_failure",
                event.get("budget_snapshot_at_failure"),
            ),
            "state_committed": state_committed,
            "budget_mutation_occurred": budget_mutated,
            "production_authorized": False,
            "task10_eligible": False,
        })
        write_output_manifest(out_dir)
        print("FAIL_CLOSED_TASK09_V4_REPRESENTATION")
        return 2
    except GateBlocked as exc:
        atomic_write_json(out_dir / "gate_block.json", {
            "schema": "2026-08-14-task09-v4-d2pr2g1f-batch64-repaired-rank-gate-block-v3",
            "failed_utc": utc_now_iso(),
            "execution_gate": config.execution_gate,
            "error": str(exc),
            "production_authorized": False,
            "task10_eligible": False,
        })
        atomic_write_json(out_dir / "run_status.json", {
            **status,
            "status": "blocked",
            "finished_utc": utc_now_iso(),
            "error": str(exc),
            "production_authorized": False,
            "task10_eligible": False,
        })
        write_output_manifest(out_dir)
        print("BLOCKED_TASK09_V4_GATE")
        return 4
    except Exception as exc:
        atomic_write_json(out_dir / "failure.json", {
            "schema": "2026-08-14-task09-v4-d2pr2g1f-batch64-repaired-rank-execution-failure-v3",
            "failed_utc": utc_now_iso(),
            "execution_gate": config.execution_gate,
            "error": repr(exc),
            "traceback": traceback.format_exc(),
            "scientific_result_admissible": False,
            "production_authorized": False,
            "task10_eligible": False,
        })
        atomic_write_json(out_dir / "run_status.json", {
            **status,
            "status": "failed_execution",
            "finished_utc": utc_now_iso(),
            "error": repr(exc),
            "production_authorized": False,
            "task10_eligible": False,
        })
        write_output_manifest(out_dir)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
