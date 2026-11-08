# Part I Numerical Programme  
## Completed Stage-01 Static-Mode Audit and Next-Session Workflow

**Project:** Environmental susceptibility of the spin–momentum absorbing-boundary detector  
**Dataset:** `01_static_mode(2).zip`  
**Archive SHA-256:** `f17502b7ec643593c4690aa0c30fb868e0a9853eaca41cc94228a0e32e2379f7`  
**Audit date:** 2 August 2026  
**Observation horizon:** \(T=10\)  
**Prompt/late divider:** \(t_{\mathrm{cut}}=3.6\)

---

## 1. Executive decision

The updated archive is complete. It contains the full Cartesian low-mode library

\[
\{\mathrm{scalar},\mathrm{spinor}\}
\times
\{|0,0\rangle,|1,0\rangle,|0,1\rangle\}
\times
\{\omega=1,100\}.
\]

All twelve propagations pass their individual solver-integrity checks. The spinor detector shows a large, coherent, confinement-enhanced dependence on the initial transverse shell. The two first-shell directions \( |1,0\rangle \) and \( |0,1\rangle \) agree to the numerical floor.

The scalar control has two different outcomes:

- at \(\omega=1\), its mode dependence is at the \(10^{-5}\) censored-law level and is compatible with the intended scalar null control;
- at \(\omega=100\), the monolithic three-dimensional Cayley step produces a non-negligible mode-dependent numerical response,
  \[
  d_{\mathrm{TV}}(\nu_{\mathrm{sc},10},\nu_{\mathrm{sc},00})
  =5.216\times10^{-3}.
  \]

The latter is not a physical scalar effect. It is the finite-step nonfactorization of a Cayley transform applied to a Kronecker-sum Hamiltonian. Consequently:

> **The physical spinor preparation effect is established, but Stage 01 is not yet fully certified as a publication-grade scalar-null benchmark at \(\omega=100\).**

The immediate next task is therefore a short scalar-control/time-step audit. Active bath production should begin only after that gate is resolved.

---

## 2. Data inventory

| ω | detector | 00 | 10 | 01 |
|---|---|---|---|---|
| 1 | scalar | ✓ | ✓ | ✓ |
| 1 | spinor | ✓ | ✓ | ✓ |
| 100 | scalar | ✓ | ✓ | ✓ |
| 100 | spinor | ✓ | ✓ | ✓ |

The folders named `Scalarr_Omega=100_...` contain valid scalar configurations; the directory spelling has no effect on the data.

### Common configuration

| ω | Δt | T | steps | grid | Lx | Ly | θ | φ |
|---|---|---|---|---|---|---|---|---|
| 1 | 0.001 | 10 | 10000 | 100×100×1500 | 10 | 10 | 0.52359878 | 0 |
| 100 | 5.000000e-04 | 10 | 20000 | 100×100×1500 | 1 | 1 | 0.52359878 | 0 |

All runs use

\[
\kappa=k_0=\pi,\qquad
z_0=10,\qquad
\sigma_z=0.5,\qquad
\theta=\pi/6,\qquad
\phi=0,
\]

with \(N_x=N_y=100\), \(N_z=1500\), \(L_z=20\), and the same frozen reference hash.

---

## 3. Numerical-integrity audit

| ω | relative roof closure | max true residual | GMRES failures | clamp loss | negative roof steps | max mode overlap |
|---|---|---|---|---|---|---|
| 1 | 4.197e-07–4.313e-07 | 5.315e-10–5.496e-10 | 0 | 0 | 0 | 1.301e-09 |
| 100 | 4.173e-07–4.414e-07 | 9.742e-09–9.997e-09 | 0 | 0 | 0 | 2.918e-08 |

Across all twelve cases:

- every GMRES solve completed;
- all midpoint roof probabilities are nonnegative;
- cumulative clamp loss is zero;
- roof loss closes against survival loss at approximately \(4\times10^{-7}\) relative error;
- mode normalization and orthogonality are substantially more accurate than any reported physical response.

Small negative values in `step_loss_total` are roundoff/cast diagnostics. They are not used as detector-click probabilities.

Detailed machine-readable tables:

- `Stage01_complete_case_metrics.csv`
- `Stage01_pairwise_curve_metrics.csv`
- `Stage01_first_shell_response_metrics.csv`
- `Stage01_complete_derived.npz`

---

## 4. Mode-resolved detector laws

### 4.1 Weak confinement: \(\omega=1\)

| detector | mode | S(T) | Droof(T) | μ*(T) | DE | DL | DL/D | mean click|T | tpeak | gpeak |
|---|---|---|---|---|---|---|---|---|---|---|
| scalar | 00 | 0.09311578 | 0.90688383 | 4.12727059 | 0.58759754 | 0.31928629 | 0.35206967 | 3.52427874 | 2.4585 | 0.3691129 |
| scalar | 10 | 0.0931158 | 0.90688381 | 4.12728104 | 0.58759552 | 0.31928829 | 0.35207188 | 3.52429015 | 2.4585 | 0.3691141 |
| scalar | 01 | 0.0931158 | 0.90688381 | 4.12728104 | 0.58759552 | 0.31928829 | 0.35207189 | 3.52429016 | 2.4585 | 0.36911411 |
| spinor | 00 | 0.11431213 | 0.88568749 | 4.25762357 | 0.5762347 | 0.30945279 | 0.34939275 | 3.51647841 | 2.4535 | 0.36231273 |
| spinor | 10 | 0.1341087 | 0.86589093 | 4.38165941 | 0.56534314 | 0.30054778 | 0.34709659 | 3.51149433 | 2.4495 | 0.35578737 |
| spinor | 01 | 0.1341087 | 0.86589093 | 4.38165944 | 0.56534315 | 0.30054779 | 0.34709659 | 3.51149433 | 2.4495 | 0.35578736 |

### 4.2 Strong confinement: \(\omega=100\)

| detector | mode | S(T) | Droof(T) | μ*(T) | DE | DL | DL/D | mean click|T | tpeak | gpeak |
|---|---|---|---|---|---|---|---|---|---|---|
| scalar | 00 | 0.09313503 | 0.90686459 | 4.12942957 | 0.58709522 | 0.31976937 | 0.35260983 | 3.52652198 | 2.46025 | 0.36890492 |
| scalar | 10 | 0.09321618 | 0.90678344 | 4.13560889 | 0.58564841 | 0.32113502 | 0.35414743 | 3.53275719 | 2.46475 | 0.36825295 |
| scalar | 01 | 0.09321618 | 0.90678342 | 4.13560887 | 0.58564841 | 0.32113502 | 0.35414743 | 3.5327572 | 2.46475 | 0.36825294 |
| spinor | 00 | 0.48735909 | 0.51264068 | 6.60381579 | 0.36491417 | 0.14772652 | 0.28816776 | 3.37512041 | 2.31875 | 0.23641066 |
| spinor | 10 | 0.55697245 | 0.44302736 | 7.18379623 | 0.28223474 | 0.16079262 | 0.36294061 | 3.64327619 | 2.29475 | 0.18470219 |
| spinor | 01 | 0.55697245 | 0.44302736 | 7.1837962 | 0.28223474 | 0.16079262 | 0.36294061 | 3.64327619 | 2.29475 | 0.1847022 |

Here,

\[
D_E=\sum_{t_{n+1/2}<3.6}p_{D,n},
\qquad
D_L=\sum_{t_{n+1/2}\ge3.6}p_{D,n}.
\]

---

## 5. First-shell directional symmetry

| ω | detector | dTV(10,01) | max|S10−S01| | W1 |
|---|---|---|---|---|
| 1 | scalar | 1.820e-08 | 3.810e-09 | 8.033e-09 |
| 1 | spinor | 1.776e-08 | 8.215e-09 | 2.581e-08 |
| 100 | scalar | 3.092e-08 | 1.297e-08 | 3.609e-08 |
| 100 | spinor | 1.738e-08 | 8.574e-09 | 3.527e-08 |

Thus,

\[
\nu_{\alpha,10}\simeq\nu_{\alpha,01}
\]

for both detectors and both confinements. This is an excellent internal isotropy check. It does not justify deleting one bath direction in the general theory; it only establishes degeneracy for the present trap, geometry, spin preparation, and click-time marginal.

---

## 6. Scalar null control

| ω | comparison | dTV | max|ΔS| | W1 | Δμ* | ΔDE | ΔDL |
|---|---|---|---|---|---|---|---|
| 1 | 10-00 | 1.588072e-05 | 4.512081e-06 | 1.061672e-05 | 1.044171e-05 | -2.024052e-06 | 2.004892e-06 |
| 1 | 01-00 | 1.588103e-05 | 4.510397e-06 | 1.061946e-05 | 1.044411e-05 | -2.024682e-06 | 2.006853e-06 |
| 100 | 10-00 | 5.215853e-03 | 1.865808e-03 | 6.179325e-03 | 6.179325e-03 | -1.446806e-03 | 1.365650e-03 |
| 100 | 01-00 | 5.215852e-03 | 1.865801e-03 | 6.179308e-03 | 6.179305e-03 | -1.446815e-03 | 1.365646e-03 |

### 6.1 \(\omega=1\)

The scalar mode dependence is tiny:

\[
d_{\mathrm{TV}}\simeq1.59\times10^{-5},
\qquad
\max_t|\Delta S(t)|\simeq4.51\times10^{-6}.
\]

This is consistent with the scalar preparation-invariance theorem at the present numerical floor.

### 6.2 \(\omega=100\)

The scalar first-shell curves differ from the ground-mode curve at the \(5.2\times10^{-3}\) censored-law level. The effect mainly redistributes numerical click weight:

\[
\Delta D_E\simeq-1.447\times10^{-3},
\qquad
\Delta D_L\simeq+1.366\times10^{-3},
\]

while the net detected-fraction change is only about \(-8.12\times10^{-5}\).

The exact scalar evolution factorizes for a Kronecker-sum Hamiltonian,

\[
e^{-it(H_z\otimes I+I\otimes H_\perp)}
=
e^{-itH_z}\otimes e^{-itH_\perp},
\]

but the monolithic Cayley step does not:

\[
C_h(H_z\otimes I+I\otimes H_\perp)
\neq
C_h(H_z)\otimes C_h(H_\perp).
\]

For a transverse energy \(E_n\), the implemented longitudinal contraction is effectively

\[
U_{h,n}
=
\left[I+\frac{ih}{2}(H_z+E_n)\right]^{-1}
\left[I-\frac{ih}{2}(H_z+E_n)\right],
\]

which depends on \(E_n\) at finite \(h\). The dependence grows when \(h\omega\) is no longer very small. This explains why the artifact is negligible at \(\omega=1\) but visible at \(\omega=100\).

---

## 7. Spinor static-mode response

For one first-shell direction relative to the ground mode:

| ω | dTV(1,0) | ΔS(T) | ΔD | Δμ* | ΔDE | ΔDL | mean click|T | late fraction |
|---|---|---|---|---|---|---|---|---|
| 1 | 0.020166 | +0.019797 | -0.019797 | +0.124036 | -0.010892 | -0.008905 | 3.516478→3.511494 | 0.349393→0.347097 |
| 100 | 0.104751 | +0.069613 | -0.069613 | +0.579980 | -0.082679 | +0.013066 | 3.375120→3.643276 | 0.288168→0.362941 |

### 7.1 \(\omega=1\)

The first-shell state:

- increases \(S(10)\) by \(1.98\times10^{-2}\);
- reduces detection by the same amount;
- increases \(\mu^*(10)\) by \(0.1240\);
- reduces both prompt and late detected masses.

The conditional mean among trials that click before \(T\) decreases slightly. Hence the rise in \(\mu^*\) is mainly a censoring/non-detection effect, not a shift of detected clicks to later times.

### 7.2 \(\omega=100\)

The first-shell state:

- increases \(S(10)\) by \(6.96\times10^{-2}\);
- reduces total detection by \(6.96\times10^{-2}\);
- increases \(\mu^*(10)\) by \(0.5800\);
- removes \(8.27\times10^{-2}\) from the prompt sector;
- adds \(1.31\times10^{-2}\) to the late sector.

The click-conditioned mean moves from \(3.3751\) to \(3.6433\), and the late fraction among detected trials rises from \(0.2882\) to \(0.3629\). This is a genuine prompt-to-return-sector restructuring, not merely a larger undetected atom at \(T\).

The spinor/scalar censored-law response ratio is approximately

\[
1.27\times10^3\quad(\omega=1),
\qquad
20.1\quad(\omega=100).
\]

The \(\omega=100\) spinor result is therefore clearly larger than the present scalar finite-step artifact, but quantitative publication values still require time-step convergence.

---

## 8. Low-temperature first-shell coefficient

Define

\[
\Delta_\uparrow X
=
X_{10}+X_{01}-2X_{00}.
\]

| ω | detector | Δ↑S(T) | Δ↑D | Δ↑μ* | Δ↑DE | Δ↑DL | ½‖Δ↑ν‖1 | closure |
|---|---|---|---|---|---|---|---|---|
| 1 | scalar | +2.814808e-08 | -3.698817e-08 | +2.088582e-05 | -4.048734e-06 | +4.011745e-06 | 3.176174e-05 | -8.840e-09 |
| 1 | spinor | +3.959315e-02 | -3.959313e-02 | +2.480717e-01 | -2.178312e-02 | -1.781001e-02 | 4.033287e-02 | 2.086e-08 |
| 100 | scalar | +1.623019e-04 | -1.623249e-04 | +1.235863e-02 | -2.893621e-03 | +2.731296e-03 | 1.043170e-02 | -2.305e-08 |
| 100 | spinor | +1.392267e-01 | -1.392266e-01 | +1.159961e+00 | -1.653589e-01 | +2.613221e-02 | 2.095012e-01 | 5.876e-08 |

The spinor response norm grows by a factor

\[
\frac{0.209501}{0.040333}=5.19
\]

between \(\omega=1\) and \(\omega=100\). The restricted-mean coefficient grows by a factor \(4.68\). Two confinement points do not establish a universal scaling law, but they clearly show stronger preparation sensitivity at strong confinement.

For a low-temperature Gibbs parameter \(q_{\mathrm{prep}}\),

\[
X^{\mathrm{th}}
=
X_{00}+q_{\mathrm{prep}}\Delta_\uparrow X+O(q_{\mathrm{prep}}^2).
\]

At \(q_{\mathrm{prep}}=0.2\), the first-order terms would be:

| ω | detector | qΔ↑D | qΔ↑μ* | qΔ↑DE | qΔ↑DL |
|---|---|---|---|---|---|
| 1 | scalar | -0.000000 | +0.000004 | -0.000001 | +0.000001 |
| 1 | spinor | -0.007919 | +0.049614 | -0.004357 | -0.003562 |
| 100 | scalar | -0.000032 | +0.002472 | -0.000579 | +0.000546 |
| 100 | spinor | -0.027845 | +0.231992 | -0.033072 | +0.005226 |

These are coefficients, not complete Gibbs predictions. Since \(q^2=0.04\), a full moderate-temperature result still requires higher shells in the later oscillator-channel implementation.

---

## 9. Scientific status after Stage 01

| item | status |
|---|---|
| All 12 individual runs numerically valid | PASS |
| Common configuration within each ω | PASS |
| Mode normalization/orthogonality | PASS |
| 10/01 first-shell degeneracy | PASS |
| Spinor static response at ω=1 | ESTABLISHED |
| Spinor static response at ω=100 | ESTABLISHED |
| Scalar null at ω=1 | PASS at current pilot tolerance |
| Scalar null at ω=100 | FAIL for monolithic finite-step map |
| Final publication-grade Stage-01 gate | PENDING scalar-control and Δt convergence |

### Established

1. The low-mode Cartesian solver is internally consistent.
2. The Stage-01 ground modes recover the Stage-00 references.
3. The first-shell directional degeneracy is numerically excellent.
4. The spinor detector is strongly sensitive to transverse preparation.
5. Strong confinement amplifies this sensitivity.
6. At \(\omega=100\), first-shell excitation suppresses prompt clicks and enhances delayed returns.

### Not yet established

1. A publication-grade scalar null at \(\omega=100\).
2. A time-step-converged numerical value for the strong-confinement spinor response.
3. A complete Gibbs preparation beyond the first-shell expansion.
4. Any dynamical bath, damping, heating, or dephasing effect.
5. A universal \(\sqrt{\omega}\) law for the static response.

---

# 10. Next-session workflow

## Stage 01C — Mandatory scalar-control and time-step closure

### Step 1: freeze the current archive

Preserve `01_static_mode(2).zip` unchanged with SHA-256

```text
f17502b7ec643593c4690aa0c30fb868e0a9853eaca41cc94228a0e32e2379f7
```

and retain this report, the three CSV files, the derived NPZ, and the response plots.

### Step 2: diagnose the \(\omega=100\) scalar artifact by time-step halving

Run, with every other parameter unchanged:

```text
detector = scalar
omega    = 100
modes    = 00 and 10
dt       = 2.5e-4
T        = 10
theta    = pi/6
phi      = 0
```

Mode \(01\) is optional for this diagnostic because \(10\) and \(01\) already agree at \(3.1\times10^{-8}\) in total variation.

Calculate

\[
R_h=d_{\mathrm{TV}}(\nu_{10}^h,\nu_{00}^h),
\quad
W_h=\int_0^T|S_{10}^h-S_{00}^h|dt.
\]

For a second-order finite-step artifact, expect approximately

\[
\frac{R_h}{R_{h/2}}\simeq4,
\qquad
\frac{W_h}{W_{h/2}}\simeq4.
\]

The current \(R_h=5.216\times10^{-3}\) predicts about \(1.30\times10^{-3}\) after one halving if clean quadratic scaling holds. This is a prediction to test, not an assumed result.

### Step 3: build the authoritative factorized scalar control

Do not modify the established spinor solver. Create a separate scalar-control implementation that uses:

- the same longitudinal matrix `L_z`;
- the same scalar ABC;
- the same longitudinal Cayley/CN step;
- a separately trace-preserving transverse step.

The finite scalar map should have the form

\[
\mathcal S_{\mathrm{sc},h}
=
\mathcal T^{\mathrm{nc}}_{z,h}
\otimes
\Phi^{\mathrm{TP}}_{\perp,h}.
\]

This implementation should reproduce scalar mode invariance at finite \(h\), rather than requiring prohibitively small time steps. It is a control solver; it does not replace or alter the verified spinor Hamiltonian/boundary/CN core.

### Step 4: spinor time-step convergence at \(\omega=100\)

Run:

```text
detector = spinor
omega    = 100
modes    = 00 and 10
dt       = 2.5e-4
T        = 10
```

Compare

\[
d_{\mathrm{TV}},
\quad
\Delta D,
\quad
\Delta\mu^*,
\quad
\Delta D_E,
\quad
\Delta D_L
\]

against the \(h=5\times10^{-4}\) results. The response must remain clearly nonzero and stable under refinement. A later production point at \(h=2\times10^{-4}\) can be selected after this audit.

### Stage-01 final gate

Proceed only when:

- scalar monolithic residual shows controlled \(O(h^2)\) decay;
- the factorized scalar control is null at the solver floor;
- the spinor response is stable under refinement;
- the physical response exceeds the complete numerical uncertainty by the predeclared evidence factor.

---

## Stage 02 — Transverse ladder-operator certification

After Stage 01C passes, implement a cheap transverse-only script. Do not add a bath to the detector propagation yet.

Required tests:

\[
a_x|00\rangle\simeq0,\qquad
a_y|00\rangle\simeq0,
\]

\[
a_x|10\rangle\simeq|00\rangle,\qquad
a_y|01\rangle\simeq|00\rangle,
\]

\[
a_x^\dagger|00\rangle\simeq|10\rangle,\qquad
a_y^\dagger|00\rangle\simeq|01\rangle.
\]

Also verify:

- weighted-adjoint consistency;
- \(N_x,N_y\ge0\);
- expected number occupations;
- \(x/y\) isotropy;
- commutator defects;
- lateral-wall leakage.

Use the Cartesian implementation only as a low-mode cross-check. The projected complete-shell oscillator basis remains the authoritative bath representation.

Suggested files:

```text
02_bath_operator_tests_solver.py
02_bath_operator_tests_loader.py
```

---

## Stage 03 — Detector-free bath certification

Construct projected complete shells \(n_x+n_y\le N\) and certify the bath before coupling it to either detector.

Mandatory tests:

1. trace preservation;
2. positivity;
3. zero-temperature ground-state stationarity;
4. mean-occupation relaxation;
5. projected Gibbs stationarity;
6. detailed balance;
7. coherent-amplitude decay;
8. pure-dephasing population/energy invariance;
9. top-shell population and overflow;
10. convergence under increasing \(N\).

No detector loss is permitted in this stage.

---

## Stage 04 — Detector-generated source diagnostics

Using the zero-bath detector evolution, calculate

\[
\langle N_\perp\rangle_{\mathrm{nc}}(t),
\]

\[
r_\downarrow(t)
=
\sum_{j=x,y}\|a_j\psi_{\mathrm{nc}}(t)\|^2,
\]

\[
r_\uparrow(t)
=
\sum_{j=x,y}\|a_j^\dagger\psi_{\mathrm{nc}}(t)\|^2,
\]

and a number-coherence/dephasing source diagnostic.

Expected control:

- scalar ground-state evolution: \(r_\downarrow\) and dephasing source remain at the numerical floor;
- spinor evolution: these sources may activate after roof interaction.

This stage determines the insertion-time grid for the response calculation.

---

## Stage 05 — Weak environmental susceptibilities

Calculation order:

\[
\text{scalar null}
\rightarrow
\text{spinor vacuum damping}
\rightarrow
\text{spinor upward excitation}
\rightarrow
\text{independent number dephasing}.
\]

For every direction, retain

\[
\chi_S(t),\quad
\chi_g(t),\quad
\chi_D,\quad
\chi_\mu,\quad
\chi_{D_E},\quad
\chi_{D_L},
\]

together with the insertion kernel \(K(t,s)\) and exact tangent probability closure.

Only after the deterministic tangent calculation passes should selected small positive rates be simulated.

---

## 11. Minimal sharing protocol for subsequent runs

For one successful run, retain/share:

```text
CASE_configuration.json
CASE_solver_audit.json
CASE_mode_basis_audit.json
CASE_times.npy
CASE_survival.npy
CASE_step_loss_roof_midpoint.npy
```

For a completed numerical stage, share:

```text
stage summary JSON
case-metrics CSV
derived NPZ
principal detector-law plot
principal response plot
numerical-validation plot
```

Do not routinely share checkpoints, stdout, full logs, or duplicate sparse probability arrays unless an anomaly occurs.

---

## 12. Frozen project rules

1. Do not alter the established spinor Hamiltonian, roof matrix \(C\), scalar/spinor ABC construction, CN matrices, GMRES solve, or post-solve boundary enforcement without a separate regression.
2. The direct ABC remains the only detector.
3. The ambient bath must be trace preserving and must not be inserted as another loss term.
4. Solver and loader remain separate.
5. Every comparison uses identical longitudinal packet, spin, geometry, and horizon.
6. Integrated detector probabilities come from midpoint step losses, not numerical differentiation of \(S(t)\).
7. A scalar response is treated as numerical error until factorization/convergence tests prove otherwise.
8. A susceptibility consistent with zero is a valid result.

---

## 13. Associated artifacts

- `Stage01_complete_case_metrics.csv`
- `Stage01_pairwise_curve_metrics.csv`
- `Stage01_first_shell_response_metrics.csv`
- `Stage01_complete_derived.npz`
- `Stage01_omega1_survival.png`
- `Stage01_omega1_click_density.png`
- `Stage01_omega100_survival.png`
- `Stage01_omega100_click_density.png`
- `Stage01_first_shell_delta_survival.png`
- `Stage01_first_shell_delta_click_density.png`
- `Stage01_response_norm_comparison.png`
