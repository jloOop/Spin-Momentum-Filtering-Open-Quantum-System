# Task-08 Independent Aggregate Response Audit

**Loader version:** `2026-08-10-task08-final-refinement-aware-v3.0`  
**Generated:** `2026-08-10T14:39:10+00:00`  
**Scientific verdict:** **PASS_TASK08_LINEAR_RESPONSE**  
**Task-08 finite-v8 zero-rate response gate authorized:** **YES**
**Publication-level project closure under the attached master audit:** **NO — upstream Task-05/06 closure remains pending**

## What this run means

All mandatory available-data, family, uncertainty, and representative-rerun gates were evaluated under the stated zero-rate finite-v8 scope.

## Discovery and incremental coverage

- Task-07 candidate records discovered: `18`
- Task-05 candidate records discovered: `19`
- Scientifically admissible cases: `15/15`
- Deterministic reruns closed: `1/15`
- Status counts: `MISSING=0`, `LOCAL_PASS=0`, `RERUN_PENDING=14`, `FAILED=0`, `CLOSED=1`

**Inspected input roots**

- `[ARCHIVE_PATH]` — exists=True, candidates=18

**Mixed/legacy-core candidates isolated:** `2`

Expected numerical-core SHA-256: `827fd4993707152393a8adcf891df59d7b4d02310a06e89dd5263c0fd37369af`. These candidates remain diagnostic inventory and do not fill formal D/U/P roles.
- `[ARCHIVE_PATH]`
- `[ARCHIVE_PATH]`

## Authority contract

The numerical master audit has precedence over historical defaults. The final Task-07→08 handoff fixes the corrected v8 raw-data contract, 15-case matrix, rerun policy, family gates, uncertainty budget, and output schema. Task 08 is read-only and reconstructs numerical statements without importing or executing Task 07 or its per-case loader.

- Frozen Task-07 numerical-core SHA-256: `827fd4993707152393a8adcf891df59d7b4d02310a06e89dd5263c0fd37369af`
- Frozen Task-07 per-case-loader SHA-256: `3ec8f9699b2182ebd73e17e64bfbd6fc783df5d9e1ee9dc29cfd7f64c0f91d14`
- Explicit authority-file verification: `True`

## Frozen case matrix

| ID | Role | Detector | Direction | ω | N | Δt | Status | Scientific | Rerun |
|---|---|---|---|---:|---:|---:|---|---|---|
| D1 | scalar_exact_null | scalar_factorized | downward | 100 | 12 | 0.0005 | RERUN_PENDING | PASS | PENDING |
| D2 | principal_baseline | spinor | downward | 100 | 12 | 0.0005 | RERUN_PENDING | PASS | PENDING |
| D3 | weak_confinement_control | spinor | downward | 1 | 12 | 0.001 | CLOSED | PASS | CLOSED |
| D4 | time_step_control | spinor | downward | 100 | 12 | 0.00025 | RERUN_PENDING | PASS | PENDING |
| D5 | shell_cutoff_control | spinor | downward | 100 | 16 | 0.0005 | RERUN_PENDING | PASS | PENDING |
| U1 | scalar_exact_null | scalar_factorized | upward | 100 | 12 | 0.0005 | RERUN_PENDING | PASS | PENDING |
| U2 | principal_baseline | spinor | upward | 100 | 12 | 0.0005 | RERUN_PENDING | PASS | PENDING |
| U3 | weak_confinement_control | spinor | upward | 1 | 12 | 0.001 | RERUN_PENDING | PASS | PENDING |
| U4 | time_step_control | spinor | upward | 100 | 12 | 0.00025 | RERUN_PENDING | PASS | PENDING |
| U5 | shell_cutoff_control | spinor | upward | 100 | 16 | 0.0005 | RERUN_PENDING | PASS | PENDING |
| P1 | scalar_exact_null | scalar_factorized | dephasing | 100 | 12 | 0.0005 | RERUN_PENDING | PASS | PENDING |
| P2 | principal_baseline | spinor | dephasing | 100 | 12 | 0.0005 | RERUN_PENDING | PASS | PENDING |
| P3 | weak_confinement_control | spinor | dephasing | 1 | 12 | 0.001 | RERUN_PENDING | PASS | PENDING |
| P4 | time_step_control | spinor | dephasing | 100 | 12 | 0.00025 | RERUN_PENDING | PASS | PENDING |
| P5 | shell_cutoff_control | spinor | dephasing | 100 | 16 | 0.0005 | RERUN_PENDING | PASS | PENDING |

## Available-case response metrics

| ID | Status | χD | χμ | χD,E | χD,L | Complete norm | Tangent closure | Insertion dTV |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| D1 | RERUN_PENDING | -0.00000000e+00 | 0.00000000e+00 | 0.00000000e+00 | 0.00000000e+00 | 0.00000000e+00 | 0.00000000e+00 | 0.00000000e+00 |
| D2 | RERUN_PENDING | 2.80628454e-03 | -1.89322817e-02 | 1.91721801e-03 | 8.89066553e-04 | 2.86558941e-03 | 2.74956117e-11 | 2.29868297e-04 |
| D3 | CLOSED | 1.96390083e-03 | -7.74635883e-03 | 4.46700747e-04 | 1.51720007e-03 | 3.77611979e-03 | 1.29764261e-11 | 3.10155027e-05 |
| D4 | RERUN_PENDING | 2.80725720e-03 | -1.89403553e-02 | 1.91793973e-03 | 8.89317469e-04 | 2.86668254e-03 | 3.24960371e-12 | 2.29474317e-04 |
| D5 | RERUN_PENDING | 2.80623642e-03 | -1.89320395e-02 | 1.91718935e-03 | 8.89047099e-04 | 2.86554597e-03 | 2.75281902e-11 | 2.29860557e-04 |
| U1 | RERUN_PENDING | -7.17916698e-13 | 4.38639781e-12 | 3.39654842e-13 | 7.53392214e-13 | 9.05482814e-13 | 1.81096375e-12 | 1.82563065e-14 |
| U2 | RERUN_PENDING | -5.27762984e-01 | 3.55718544e+00 | -4.19395163e-01 | -1.08367822e-01 | 6.83641299e-01 | 1.21160859e-10 | 1.04346360e-03 |
| U3 | RERUN_PENDING | -1.62040358e-01 | 8.62262471e-01 | -5.89299941e-02 | -1.03110365e-01 | 1.62249465e-01 | 1.48589185e-09 | 6.19005845e-05 |
| U4 | RERUN_PENDING | -5.25687222e-01 | 3.54590556e+00 | -4.18064851e-01 | -1.07622371e-01 | 6.75361353e-01 | 2.15051865e-10 | 1.01771075e-03 |
| U5 | RERUN_PENDING | -5.27814570e-01 | 3.55749496e+00 | -4.19422893e-01 | -1.08391676e-01 | 6.83683347e-01 | 6.16283122e-11 | 1.04346244e-03 |
| P1 | RERUN_PENDING | -0.00000000e+00 | 0.00000000e+00 | 0.00000000e+00 | 0.00000000e+00 | 0.00000000e+00 | 0.00000000e+00 | 0.00000000e+00 |
| P2 | RERUN_PENDING | 4.57883785e-03 | -2.97449778e-02 | 2.90201849e-03 | 1.67681941e-03 | 4.68556747e-03 | 3.97713884e-11 | 4.61543122e-04 |
| P3 | RERUN_PENDING | 1.79481950e-03 | -7.59187187e-03 | 4.70950654e-04 | 1.32386884e-03 | 3.84316924e-03 | 1.03094976e-11 | 3.08459597e-05 |
| P4 | RERUN_PENDING | 4.57968016e-03 | -2.97527123e-02 | 2.90204529e-03 | 1.67763486e-03 | 4.67987457e-03 | 6.18179813e-12 | 4.65572931e-04 |
| P5 | RERUN_PENDING | 4.57861065e-03 | -2.97437677e-02 | 2.90189544e-03 | 1.67671525e-03 | 4.68533322e-03 | 3.96482612e-11 | 4.61535409e-04 |

## Scalar pointwise nulls

| Direction | Case | Pointwise kernel max | Response max | Pointwise gate | Integrated gate |
|---|---|---:|---:|---|---|
| downward | D1 | 0.00000000e+00 | 0.00000000e+00 | PASS | PASS |
| upward | U1 | 1.99146255e-13 | 7.17916698e-13 | PASS | PASS |
| dephasing | P1 | 0.00000000e+00 | 0.00000000e+00 | PASS | PASS |

## Time-step and shell convergence

| Direction | dTV(dt,dt/2) | Relative | Gate | dTV(N12,N16) | Relative | Gate |
|---|---:|---:|---|---:|---:|---|
| downward | 1.77331833e-05 | 6.18595992e-03 | PASS | 6.51474331e-08 | 2.27343921e-05 | PASS |
| upward | 1.35440735e-02 | 1.98116667e-02 | PASS | 5.19353483e-05 | 7.59640388e-05 | PASS |
| dephasing | 5.05279054e-05 | 1.07837323e-02 | PASS | 2.90809010e-07 | 6.20648431e-05 | PASS |

## Upward launch identity

| Case | Independent Task-05 raw inputs | Max absolute difference | Relative difference | Status |
|---|---|---:|---:|---|
| U1 | YES | 4.95437025e-15 | 9.90874049e-08 | PASS |
| U2 | YES | 7.13901160e-13 | 7.00379566e-11 | PASS |
| U3 | YES | 5.25753856e-10 | 3.78842255e-07 | PASS |

## Uncertainty and evidence

| Direction | Response norm | ε_total | Ratio | Classification | Missing components |
|---|---:|---:|---:|---|---|
| downward | 2.85617762e-03 | 1.71319992e-04 | 1.66715955e+01 | RESOLVED_NONZERO | none |
| upward | 6.85485610e-01 | 3.26893849e-02 | 2.09696699e+01 | RESOLVED_NONZERO | none |
| dephasing | 4.65731119e-03 | 3.61615276e-04 | 1.28791882e+01 | RESOLVED_NONZERO | none |

## Reproducibility coverage

- Representative D3 deterministic certification: `True`
- Per-case rerun coverage: `1/15`
- Coverage status: `PER_CASE_RERUN_COVERAGE_INCOMPLETE`

## Claim boundary

The mandatory Task-08 gates authorize interpretation of the independently reconstructed **zero-rate finite-v8 linear response**. Under the attached highest-authority master audit, publication-level project closure remains provisional until the residual Task-05/06 closure items are recorded in an updated master audit. This result does not authorize a finite-rate, thermal, trajectory, microscopic-detector, or continuum-semigroup claim.

## Outstanding items

- Missing cases: `[]`
- Failed cases: `[]`
- Scientifically inadmissible cases: `[]`
- Unresolved evidence directions: `[]`
- Missing independent Task-05 upward inputs: `[]`

## Principal output products

- `Task08_case_identity_table.csv` — complete D1–D5/U1–U5/P1–P5 register
- `Task08_per_case_metrics.csv` — per-case response and closure metrics
- `Task08_complete_response_curves.csv` — available reconstructed curves
- `Task08_uncertainty_budget.json` and `Task08_evidence_classification.json`
- `Task08_share.zip` and `Task08_diagnostic_share.zip`

---

# Final refinement-aware closure amendment

- Loader version: `2026-08-10-task08-final-refinement-aware-v3.0`
- Canonical cases: `15/15` required.
- Supplemental insertion refinements: `D2-I`, `U2-I`, `P2-I`.
- Internal `0.1↔0.2` coarsening is diagnostic only.
- Final insertion gate: independent `0.1→0.05` comparison.
- Upward high-accuracy core is accepted only for `U2`, `U4`, `U2-I`.

## Supplemental-case status

| Role | Status | Scientifically admissible | Rerun closed |
|---|---|---:|---:|
| D2-I | RERUN_PENDING | True | False |
| U2-I | RERUN_PENDING | True | False |
| P2-I | RERUN_PENDING | True | False |

## Genuine insertion refinement

| Direction | Complete-law distance | Relative | Gate |
|---|---:|---:|---:|
| downward | 7.48624816e-05 | 2.61246365e-02 | True |
| upward | 2.15101063e-04 | 3.14611085e-04 | True |
| dephasing | 1.82534120e-04 | 3.89566731e-02 | True |

## Final evidence budget

| Direction | Accepted response | ε_total | Signal/ε | Classification |
|---|---|---:|---:|---|
| downward | D2-I | 1.71319992e-04 | 1.66715955e+01 | RESOLVED_NONZERO |
| upward | U2-I | 3.26893849e-02 | 2.09696699e+01 | RESOLVED_NONZERO |
| dephasing | P2-I | 3.61615276e-04 | 1.28791882e+01 | RESOLVED_NONZERO |

## Final verdict

- Scientific verdict: `PASS_TASK08_LINEAR_RESPONSE`
- Zero-rate physical claim authorized: `True`
- Task-09 gate authorized: `True`
- Publication-level direct representation/longitudinal refinement remains subject to the declared inherited-bound provenance and the final Part-I audit.
