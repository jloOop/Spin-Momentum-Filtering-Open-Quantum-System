# Omega-dependence scientific report

## Definitions

`chi_D = -chi_S(T) = sum_i chi_panel_probability_i`. `chi_mu` is the trapezoidal integral of the state-node survival derivative. With the archived panel-average convention, `chi_g` lives on the 100 panel midpoints while `chi_S` and baseline survival live on 101 state nodes. The complete signed response norm is `A_TV = 1/2 (sum_i |chi_panel_probability_i| + |chi_S(T)|)`. Early and late detection responses split at `t_c=3.6`.

## Accepted Task-08 context

The independent aggregate accepts the insertion-refined roles D2-I, U2-I, and P2-I. Recomputed from their archived arrays:

| role | direction | chi_D | chi_mu | A_TV | Task-08 class |
|---|---|---|---|---|---|
| D2-I | downward | 0.002806532 | -0.01892382 | 0.002856178 | RESOLVED_NONZERO |
| U2-I | upward | -0.5277705 | 3.557248 | 0.6854856 | RESOLVED_NONZERO |
| P2-I | dephasing | 0.004578532 | -0.0297474 | 0.004657311 | RESOLVED_NONZERO |

All three directions are `RESOLVED_NONZERO` under the dated Task-08 zero-rate budget. This is a finite-v8, zero-rate susceptibility result; it is not a finite-positive-rate or continuum statement. Scalar-factorized D1/U1/P1 remain exact null controls. Six older curated case-loader records retain local `FAIL` status, but the later independent aggregate separately reconstructs and adjudicates the selected families; both layers are preserved in `CANONICAL_CASE_MASTER_TABLE.csv`.

## Recomputed 12-case table

| omega | mode | S0(T) | chi_D | chi_mu | early | late | A_TV |
|---|---|---|---|---|---|---|---|
| 4 | 00 | 0.1471922 | -0.4431163 | 2.430165 | -0.173443 | -0.2696733 | 0.4444288 |
| 4 | 10 | 0.2015986 | -0.544856 | 3.01989 | -0.2203603 | -0.3244957 | 0.5454603 |
| 4 | 01 | 0.2015986 | -0.544856 | 3.01989 | -0.2203603 | -0.3244957 | 0.5454603 |
| 36 | 00 | 0.2739407 | -0.8512203 | 6.128825 | -0.5766634 | -0.2745569 | 0.9838346 |
| 36 | 10 | 0.3842062 | -0.9235504 | 5.742073 | -0.5201765 | -0.4033739 | 0.9272622 |
| 36 | 01 | 0.3842062 | -0.9235504 | 5.742073 | -0.5201765 | -0.4033739 | 0.9272622 |
| 64 | 00 | 0.3786949 | -0.6881212 | 4.967542 | -0.5325998 | -0.1555215 | 0.8457214 |
| 64 | 10 | 0.4680181 | -0.8498477 | 5.366661 | -0.5178663 | -0.3319814 | 0.8985961 |
| 64 | 01 | 0.4680181 | -0.8498477 | 5.366661 | -0.5178663 | -0.3319814 | 0.8985961 |
| 144 | 00 | 0.5780903 | -0.5221895 | 3.226968 | -0.3789308 | -0.1432587 | 0.6266719 |
| 144 | 10 | 0.6433052 | 0.1221704 | -0.2539702 | -0.07145487 | 0.1936253 | 0.2585045 |
| 144 | 01 | 0.6433052 | 0.1221704 | -0.2539702 | -0.07145487 | 0.1936253 | 0.2585045 |

Every displayed metric was reconstructed from the compact NPZ arrays and checked against both CSV curves and reported metrics.

## What changes with confinement

For mode 00, `chi_D` stays negative at all four sampled omega values: 4: -0.443116, 36: -0.85122, 64: -0.688121, 144: -0.52219. Its magnitude is nonmonotonic, reaching its largest sampled value at omega 36, not at the largest omega.

For modes 10 and 01, `chi_D` is negative at omega 4, 36, and 64, but positive at omega 144. Thus the evidence supports a sampled sign change bracket only: **64 < omega < 144**. Four nonuniform points, with a dt change at omega 144, do not justify interpolation to a unique root.

At omega 144 the excited doublet has `chi_D_E ≈ -0.0714549` and `chi_D_L ≈ +0.193625`. The positive late contribution outweighs the still-negative early contribution, yielding `chi_D ≈ +0.12217`. Meanwhile `A_TV ≈ 0.258504`, so `A_TV/|chi_D| ≈ 2.116`. This is strong signed cancellation and time-shape redistribution, not a simple amplitude rescaling.

The 10/01 doublet is numerically degenerate: the largest absolute `chi_D` difference is 1.734e-10, and the largest pointwise difference over `chi_S` or `chi_g` is 1.734e-10. This supports mode-exchange symmetry at the resolution of the archived data, not a proof of exact analytic equality.

## Trend diagnostics, not laws

Spearman rank coefficients over four points are: mode 00 `{'chi_D': -0.19999999999999998, 'chi_mu': 0.19999999999999998, 'A_TV': 0.19999999999999998, 'baseline_S_T': 1.0}`, mode 10 `{'chi_D': 0.39999999999999997, 'chi_mu': -0.39999999999999997, 'A_TV': -0.39999999999999997, 'baseline_S_T': 1.0}`, mode 01 `{'chi_D': 0.39999999999999997, 'chi_mu': -0.39999999999999997, 'A_TV': -0.39999999999999997, 'baseline_S_T': 1.0}`. These ranks are descriptive only. The nonmonotonic mode-00 response, the excited-mode sign change, the large rescaling residuals in `OMEGA_SHAPE_SCALING_DIAGNOSTICS.csv`, and the omega-144 time-domain cancellation jointly rule out interpreting the scan as evidence for a universal amplitude-only scaling law.

No square-root, power, affine, monotonic, or asymptotic law was fitted. The figures connect samples only to aid reading.

## Comparison to curated omega anchors

The ground-mode scan may be compared to curated upward roles only with discretization labels retained: U3 is omega 1 at dt=1e-3; U2 is omega 100 at dt=5e-4 and insertion dt=0.1; U4 is omega 100 at dt=2.5e-4 and insertion dt=0.1; U2-I is the independently refined insertion grid at omega 100, dt=5e-4, insertion dt=0.05. Therefore omega 4/36/64 are time-step matched to U2, omega 144 is time-step matched to U4, and U2-I is the Task-08 accepted response role but is not insertion-grid matched to the scan.

## Limitations

- Only four omega values and three initial modes were supplied.
- The exploratory scan lacks N=16 shell partners, dt/2 partners at every omega, insertion refinements, and a Task-08 aggregate adjudication.
- Omega 144 changes dt from 5e-4 to 2.5e-4, so the scan is not a single fixed-discretization sequence.
- No uncertainty bars can be assigned from the supplied scan alone.
- The spatial atlas has `physical_acceptance=false` and must remain a visualization derivative, despite exact reconciliation of its timing arrays to the ordinary omega-144/mode-00 case.
