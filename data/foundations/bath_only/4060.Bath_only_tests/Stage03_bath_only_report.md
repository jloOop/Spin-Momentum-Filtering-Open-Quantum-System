# Stage-03 Independent Bath-Only Loader Report

## Decision

**PASS**

Loader source SHA-256: `cf0246ee8767dbb8862d637a4225952c9625392281d3856a616e69fea22c7d9c`

Stable Stage-03 solver files verified: 8/8.

Independent refined acceptance: 32/32 gates.

All solver/loader criteria and PASS/FAIL decisions agree: `True`.

## Scope

This report certifies only the detector-free finite projected transverse bath. No scalar/spinor ABC, longitudinal propagation, roof-click law, or environmental detector susceptibility is calculated.

## Infrastructure and independent reconstruction

| Check | Result |
|---|---:|
| `hash_validation_pass` | `True` |
| `configuration_validation_pass` | `True` |
| `source_guard_pass` | `True` |
| `npz_schema_pass` | `True` |
| `case_csv_comparison_pass` | `True` |
| `cutoff_csv_comparison_pass` | `True` |
| `operator_json_comparison_pass` | `True` |
| `independent_population_curves_pass` | `True` |
| `initial_final_density_pass` | `True` |
| `fresh_random_audit_pass` | `True` |
| `exact_overflow_refinement_pass` | `True` |

## Exact finite-shell refinement

| Case | 101-point overflow | Exact augmented overflow | High-resolution max top shell |
|---|---:|---:|---:|
| B2_N8 | 6.168478719806e-05 | 6.168431463015e-05 | 1.327311440532e-05 |
| B2_N12 | 1.575661560626e-07 | 1.575638973169e-07 | 2.888131964117e-08 |
| B2_N16 | 3.485636200801e-10 | 3.485558363392e-10 | 5.692853490074e-11 |
| B3_N8 | 2.923529754022e-04 | 2.923544400640e-04 | 4.917239421807e-05 |
| B3_N12 | 8.766298721596e-07 | 8.766369798856e-07 | 1.073604688778e-07 |
| B3_N16 | 2.212063755170e-09 | 2.212088468510e-09 | 2.194928752653e-10 |

The tightest production-shell result is

\[\epsilon_{\mathrm{overflow}}^{B3,N=12}(20)=8.766369798855872e-07<10^{-6}.\]

## Independent 32-gate table

| Gate | Loader value | Criterion | Result |
|---|---:|---:|---|
| `operator_identities` | 1.598721155460e-14 | `<= 1.000e-12` | PASS |
| `liouvillian_trace_preserving_row` | 4.996003610813e-16 | `<= 1.000e-12` | PASS |
| `column_major_vectorization` | 1.913160462302e-16 | `<= 1.000e-12` | PASS |
| `generator_hermiticity_preservation` | 3.908443246113e-17 | `<= 1.000e-12` | PASS |
| `trace_preservation` | 1.043609643148e-14 | `<= 1.000e-12` | PASS |
| `density_hermiticity` | 0.000000000000e+00 | `<= 1.000e-12` | PASS |
| `density_positivity` | 0.000000000000e+00 | `>= -1.000e-11` | PASS |
| `projected_event_intensity_formula` | 3.885780586188e-16 | `<= 1.000e-12` | PASS |
| `B0_ground_stationarity` | 1.110223024625e-16 | `<= 1.000e-12` | PASS |
| `B1_one_quantum_decay` | 2.220446049250e-16 | `<= 1.000e-11` | PASS |
| `B1_xy_isotropy` | 0.000000000000e+00 | `<= 1.000e-12` | PASS |
| `B2_B3_projected_population_reference` | 8.024080429950e-15 | `<= 1.000e-11` | PASS |
| `B2_B3_projected_occupation_reference` | 4.607425552194e-15 | `<= 1.000e-11` | PASS |
| `B2_B3_infinite_law_within_declared_overflow_bound` | -4.999826945336e-11 | `<= 0` | PASS |
| `B4_projected_gibbs_generator_stationarity` | 1.406763150647e-17 | `<= 1.000e-12` | PASS |
| `B4_projected_gibbs_propagated_stationarity` | 3.439278626562e-16 | `<= 1.000e-12` | PASS |
| `B4_projected_detailed_balance` | 3.330669868410e-16 | `<= 1.000e-12` | PASS |
| `B5_coherent_amplitude_absolute_error` | 1.081089232170e-07 | `<= 1.000e-06` | PASS |
| `B5_coherent_amplitude_within_projected_residual_bound` | 1.285472980708e-16 | `<= 5.000e-11` | PASS |
| `B5_coherent_projected_residual_reconstruction` | 1.167759113530e-11 | `<= 5.000e-11` | PASS |
| `B6_dephasing_population_invariants` | 1.665334536938e-16 | `<= 1.000e-12` | PASS |
| `B6_dephasing_energy_invariant` | 0.000000000000e+00 | `<= 1.000e-12` | PASS |
| `B6_dephasing_coherence_law` | 6.890150443143e-16 | `<= 1.000e-12` | PASS |
| `B7_isotropic_basis_invariance` | 4.392848978485e-16 | `<= 1.000e-12` | PASS |
| `B8_cutoff_occupation_N12_to_N16` | 2.766282998223e-07 | `<= 1.000e-06` | PASS |
| `B8_cutoff_purity_N12_to_N16` | 1.486500011971e-08 | `<= 1.000e-07` | PASS |
| `B8_cutoff_trace_distance_N12_to_N16` | 2.889801573192e-08 | `<= 1.000e-07` | PASS |
| `B8_occupation_trace_distance_consistency` | 0.000000000000e+00 | `<= 5.000e-12` | PASS |
| `B8_production_top_shell` | 1.073604688778e-07 | `<= 1.000e-06` | PASS |
| `B8_production_overflow` | 8.766369798856e-07 | `<= 1.000e-06` | PASS |
| `B8_top_shell_monotonic_improvement` | 0.000000000000e+00 | `<= 1.000e-13` | PASS |
| `B8_overflow_monotonic_improvement` | 0.000000000000e+00 | `<= 1.000e-13` | PASS |

## Workflow status

The Stage-03 bath branch is solver-and-loader certified for the declared B0--B8 scope. Scientific Stage 04 remains blocked until Stage 01C also passes. The N=12 result is not inherited automatically by detector-present dynamics.
