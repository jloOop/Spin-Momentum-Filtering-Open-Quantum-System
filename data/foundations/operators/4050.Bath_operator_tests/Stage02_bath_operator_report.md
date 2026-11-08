# Stage 02 — Transverse Bath-Operator Complete Audit

**Status:** PASS
**Audit time:** 2026-08-02T21:08:10+00:00
**Fixed output directory:** `4050.Bath_operator_tests`

## 1. Scope

Stage 02 certifies the transverse operator layer only. The authoritative objects are the projected complete-shell oscillator matrices. The Cartesian calculation is a low-mode cross-check using the Stage-01 grid and mode conventions. No detector propagation, ABC modification, Crank–Nicolson step, GMRES solve, or Lindblad bath evolution is present.

A PASS does **not** yet certify trace preservation, Gibbs stationarity, detector–bath composition, the scalar dynamical null, or any environmental susceptibility.

## 2. Frozen configuration

- Complete-shell cutoff: `N_shell = 12`
- Retained transverse dimension: `91`
- Cartesian confinements: `(1.0, 100.0)`
- Cartesian grids: `(50, 100, 200)`
- Stage-01 box scaling: `Lx = Ly = 10/sqrt(omega)`
- Arithmetic: NumPy `float64` / `complex128`
- Directory policy: fixed directory, reused, no timestamped or parameter-generated folder

## 3. Authoritative complete-shell results

| Check | Maximum defect |
|---|---:|
| All lowering/raising actions | 0.000000e+00 |
| Adjoint consistency | 5.553085e-16 |
| Number-operator identity | 1.776357e-15 |
| Projected commutator formulas | 7.105427e-15 |
| Oscillator Bohr relations | 2.167914e-15 |
| Transverse Hamiltonian formula | 0.000000e+00 |
| K Hermiticity | 0.000000e+00 |
| K ladder-operator formula | 0.000000e+00 |
| K/sqrt(omega) scale collapse | 4.440892e-16 |

The full finite-dimensional canonical commutator is not required to equal the identity. The audit instead verifies the exact complete-shell top-shell defects and the exact cross-axis projected defects. This is the mathematically correct finite projection.

## 4. Cartesian Stage-01 cross-check

Reference case: `omega=100`, `N=100`.

| Quantity | Value |
|---|---:|
| Maximum ladder-action residual | 4.260196e-03 |
| Maximum occupation error | 2.478728e-03 |
| Maximum low-mode CCR action residual | 9.654272e-03 |
| Maximum cross-commutator action residual | 1.631912e-15 |
| Maximum x/y isotropy defect | 1.734723e-18 |
| Maximum wall-leakage metric | 1.482597e-10 |

The minimum measured refinement order over ladder actions, number occupations, and low-mode CCR actions is **1.962974**. The maximum omega=1/100 scale-collapse difference is **3.747e-14**.

## 5. Independent loader verification

- Solver stable-file hashes verified: `10`
- All solver hashes match: `True`
- Independent gates agree with solver: `True`
- Case CSV agrees: `True`
- Convergence CSV agrees: `True`
- Omega-collapse CSV agrees: `True`

## 6. Acceptance gates

| Gate | Status | Metric | Threshold |
|---|---|---:|---:|
| `authoritative_all_ladder_actions` | PASS | 0.000000e+00 | <= 1.000000e-12 |
| `authoritative_adjoint` | PASS | 5.553085e-16 | <= 1.000000e-12 |
| `authoritative_number_positivity` | PASS | 0.000000e+00 | >= -1.000000e-11 |
| `authoritative_number_diagonal` | PASS | 1.776357e-15 | <= 1.000000e-12 |
| `authoritative_xy_isotropy` | PASS | 0.000000e+00 | <= 1.000000e-12 |
| `authoritative_projected_commutator_formulas` | PASS | 7.105427e-15 | <= 1.000000e-12 |
| `authoritative_bohr_relations` | PASS | 2.167914e-15 | <= 1.000000e-12 |
| `authoritative_K_hermiticity` | PASS | 0.000000e+00 | <= 1.000000e-12 |
| `authoritative_K_formula` | PASS | 0.000000e+00 | <= 1.000000e-12 |
| `authoritative_K_sqrtomega_scaling` | PASS | 4.440892e-16 | <= 1.000000e-12 |
| `cartesian_reference_case_present` | PASS | 1.000000e+00 | == 1.000000e+00 |
| `cartesian_mode_orthonormality` | PASS | 7.552075e-11 | <= 1.000000e-08 |
| `cartesian_weighted_adjoint` | PASS | 6.502165e-15 | <= 1.000000e-12 |
| `cartesian_number_positivity` | PASS | -3.719268e-15 | >= -1.000000e-11 |
| `cartesian_ladder_O_eta_squared` | PASS | 4.272001e-01 | <= 7.500000e-01 |
| `cartesian_occupation_O_eta_squared` | PASS | 2.494656e-01 | <= 5.000000e-01 |
| `cartesian_CCR_O_eta_squared` | PASS | 9.675411e-01 | <= 1.250000e+00 |
| `cartesian_second_order_refinement` | PASS | 1.962974e+00 | >= 1.900000e+00 |
| `cartesian_cross_commutators` | PASS | 6.111750e-15 | <= 1.000000e-12 |
| `cartesian_xy_isotropy` | PASS | 9.996344e-17 | <= 1.000000e-12 |
| `cartesian_omega_scale_collapse` | PASS | 3.747003e-14 | <= 1.000000e-12 |
| `cartesian_lateral_wall_leakage` | PASS | 6.036987e-10 | <= 1.000000e-08 |

## 7. Scientific decision

Stage 02 passes. The projected complete-shell ladder operators are exact to machine precision, their number operators are positive, the finite projected commutator structure is correct, the Bohr-frequency and transverse-Hamiltonian identities hold, and the spin–momentum operator is reproduced from the same ladder graph, is Hermitian, and has the required sqrt(omega) scaling. The Cartesian low-mode residuals show controlled second-order convergence and omega=1/100 collapse under the Stage-01 scaling.

The next independent stage is detector-free bath certification: trace preservation, positivity, ground-state stationarity at zero temperature, occupation relaxation, projected Gibbs stationarity, detailed balance, coherent-amplitude decay, dephasing invariants, and shell-overflow control.

## 8. Reproducibility

- Solver SHA-256: `2ed0daf88dca64d33896d42e53d93c1e57b85d7e22391498babd4f7588b273b2`
- Loader SHA-256: `398a66b51c21e72216da38ef446c4e0e0012b0c23e2d6114b12b19e54e4bfc0b`
