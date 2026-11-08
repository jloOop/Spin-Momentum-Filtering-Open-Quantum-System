# Part I Open-System ABC Project  
## Authoritative Numerical Master Audit Through the Task-06 Available-Data Audit and Handoff for Task 07 and Later Response Stages

**Project:** Environmental susceptibility of the spin–momentum absorbing-boundary detector  
**Date:** 3 August 2026  
**Scope:** effective Part-I scalar/spinor ABC detector with an independent transverse trace-preserving environment  
**Current status:** Audits 00--04 are closed for their declared scopes. The required sixteen-case Task-05 baseline/scalar-control block is complete and passes. Task 06 has now been implemented and executed as an independent read-only aggregate loader. Its available-data audit validates the factorized scalar null at both confinements, the monolithic \(O(\Delta t^2)\) artifact diagnosis, spinor \(10/01\) isotropy, source activation, and the numerical integrity of the accepted H200/CuPy cases. Two additional mode-00 shell calculations at \(N=8\) and \(N=16\) are numerically healthy and show strong \(N=12\to16\) convergence. The raw Task-06 run nevertheless returned `FAIL` because the strict loader treated the separately audited \(10^{-10}\) GMRES convergence family as source drift, because four frozen convergence configurations remain absent, because one optional mode-01 case has a noncanonical prefix, and because the Stage-01 cluster archive and independent same-prefix rerun were not yet supplied. Accordingly, Task 06 receives a **qualified PASS for the available-data independent audit**, while complete Task-05/06 branch closure remains pending. Task-07 development is authorized; final production susceptibilities remain provisional until the residual closure items are completed.  
**Purpose of this file:** preserve the complete Audit-00--04 and historical Task-05 records, incorporate the completed baseline/scalar Task-05 campaign and the executed Task-06 aggregate audit, distinguish the available-data PASS from formal full-campaign closure, and provide the authoritative structured handoff for Task 07, Task 08, and the later finite-rate programme.  

---


> **Status precedence notice.** Parts XVII--XXI appended to this version are the current authority for Task 06 and the Task-07/08 handoff. Parts XV and XVI are retained unchanged as historical provenance. The phrase **Task-06 qualified PASS** means that the independent loader implementation and all available accepted numerical/scientific data pass after explicit source-family reconciliation; it does **not** mean that the originally frozen 22-case campaign, Stage-01 cluster provenance, or deterministic rerun gate has been completed.

## 0. Authority, supersession, and how to use this document

This file consolidates the following numerical records:

1. `NUM_Open_System_PartI_Numerical_Session_Handoff_2026-08-02(2).md`;
2. `NUM_Stage01_Static_Mode_Complete_Audit_and_Next_Workflow_2026-08-02(6).md`;
3. the user-supplied full review archive `Stage01_static_mode(1).zip`;
4. `NUM_Stage02_Bath_Operator_Complete_Audit_2026-08-02.md`;
5. `Stage02_Complete_Code_Audit_2026-08-02.md`;
6. `Stage02_Local_Smoke_Test_Report_2026-08-02.md`;
7. `Stage02_Fresh_Execution_Analysis_2026-08-02.md`;
8. the independently generated `Stage02_bath_operator_report.md`;
9. the audited Audit-03 solver `03_bath_only_fock_test.py` and all stable Audit-03 products;
10. `Stage03_exact_augmented_overflow_audit.json` and `Stage03_highres_population_10001point_audit.json`;
11. the independent Audit-04 loader `04_bath_only_fock_loader.py`;
12. `Stage03_loader_audit.json`, the independent case/cutoff tables, and `Stage03_bath_only_report.md`;
13. `Task04_Stage03_Independent_Loader_Verified_2026-08-03.zip`;
14. the fresh Audit-04 package re-execution performed while preparing this update.

The source files remain the archival records. This master file is the current workflow authority.

The supersession and interpretation rules are:

- Audit 01 is complete for its declared twelve zero-bath Cartesian cases. The supplied ZIP contains every scalar/spinor, mode, and confinement combination.
- The former label **Stage 01C** did not denote a missing mode or an omitted part of that ZIP. It was a proposed extra convergence/control addendum motivated by the known finite-step scalar artifact at \(\omega=100\).
- To remove the confusing parallel numbering, that extra control is no longer treated as an independent stage. It is incorporated as the mandatory first subpart of Task 05.
- Audit 02 remains fully closed at 22/22 gates.
- Audit 03 remains the authoritative detector-free projected-bath solver record at 32/32 gates.
- Audit 04 independently reconstructs and verifies Audit 03 and closes the bath branch.
- The required Task-05 baseline/scalar-control block is complete and passes; the residual mode-10 shell and spinor time-step convergence cases remain formal closure items.
- Task 06 has been implemented and executed as an independent aggregate loader. Its available-data audit receives a qualified PASS; the original complete-campaign closure remains pending.
- Task-07 weak-response development is now authorized, while final production susceptibilities remain provisional until the residual Task-05/06 closure items pass.
- No detector--bath susceptibility or finite-rate detector response has yet been calculated.

The present dependency structure is

\[
\begin{array}{ccccccccc}
\text{detector foundation:}
&\text{Audit 00}&\longrightarrow&\text{Audit 01}&\longrightarrow&\text{Task 05 solver}&\longrightarrow&\text{Task 06 loader},\\[1mm]
\text{bath foundation:}
&\text{Audit 02}&\longrightarrow&\text{Audit 03 solver}&\longrightarrow&\text{Audit 04 loader},\\[1mm]
\text{response branch:}
&&&&\text{Task 07 solver}&\longrightarrow&\text{Task 08 loader}&\longrightarrow&\text{Tasks 09--10 finite-rate validation}.
\end{array}
\]

Thus the immediate authorized step is

\[
\boxed{
\text{Task-05/06 qualified zero-bath foundation}
+
\text{Audit-02--04 bath closure}
\longrightarrow
\text{Task-07 weak environmental-response development}.
}
\]

---

# Part I — Current scientific and numerical status

## 1. Executive decision

| Audit or task | Purpose | Current result | Decision |
|---|---|---|---|
| Audit 00 | Zero-ambient-bath detector reference | Two confinement references completed and internally valid | **PASS as pilot/reference** |
| Audit 01 | Zero-bath transverse-mode library | Full 12-case archive present; all runs completed; spinor preparation response established | **COMPLETE FOR DECLARED SCOPE** |
| Audit-01 scalar control issue | Explain/remove the \(\omega=100\) monolithic-Cayley mode artifact | Extra refined/factorized runs are not in the ZIP; the issue is real but already identified | **FOLDED INTO TASK 05A** |
| Audit 02 | Transverse ladder, number, commutator, Hamiltonian, and \(K\)-operator certification | 22/22 gates passed with independent loader | **FULL PASS** |
| Audit 03 | Detector-free projected-bath solver | B0--B8 propagated; 32/32 solver gates; deterministic rerun; exact overflow refinement | **SOLVER PASS** |
| Audit 04 | Independent Audit-03 loader/auditor | 8/8 stable hashes; independent 32/32 gates; solver/loader agreement; tamper tests | **FULL PASS; BATH BRANCH CLOSED** |
| Task 05 | Oscillator-channel zero-bath detector recovery, scalar closure, and source diagnostics | Required 16-case baseline/scalar block complete; 23 valid cases discovered by Task 06; baseline physics, scalar controls, spinor isotropy, source activation, and mode-00 shell convergence established | **SOLVER/SCIENCE PASS FOR AVAILABLE DATA; FORMAL BRANCH CLOSURE PENDING** |
| Task 06 | Independent Task-05 aggregate loader | Implemented and executed; 23 valid cases discovered, no duplicate physical configurations, all load-bearing available-data numerical/scientific reductions verified; strict full-campaign verdict blocked only by residual inventory/provenance gates | **QUALIFIED PASS FOR AVAILABLE-DATA AUDIT; FULL CLOSURE PENDING** |
| Task 07 susceptibility solver | Channel-resolved weak environmental response at zero rate | Development authorized under the exact finite-model tangent theory; no production response yet | **NEXT IMPLEMENTATION; FINAL CLAIMS PROVISIONAL UNTIL FULL 05/06 CLOSURE** |
| Tasks 08--10 | Independent response loader and small-positive-rate validation | Not started | **WAIT FOR TASK-07 DEVELOPMENT AND AUDIT GATES** |

The current scientific conclusion is:

> The intended H200/CuPy backend supports stable production-scale oscillator-channel propagation. The authoritative factorized scalar map is mode-null at both \(\omega=1\) and \(100\) to approximately \(10^{-13}\) in complete censored-law total variation; the monolithic scalar artifact has the expected quadratic step-size reduction; the spinor detector preserves \(10/01\) isotropy, exhibits a confinement-enhanced first-shell timing response, and generates nonzero downward/dephasing source structure. The available mode-00 shell family shows \(N=12\to16\) complete-law convergence at \(d_{\mathrm{TV}}\simeq8.97\times10^{-8}\). Residual mode-10 shell, spinor time-step, Stage-01 cluster-provenance, and same-prefix rerun gates remain formal closure items. No ambient-bath susceptibility, temperature dependence, damping, heating, or dephasing modification of the click law has yet been calculated.

---

## 2. Scientific objective and non-negotiable model architecture

The Part-I numerical target is

\[
\text{same transverse trace-preserving operation}
\quad\Longrightarrow\quad
\begin{cases}
\text{scalar click-time law unchanged},\\[1mm]
\text{spinor click-time law potentially changed}.
\end{cases}
\]

The organizing reduced equation is

\[
\frac{d\widetilde\rho_\alpha}{dt}
=
\mathcal L^{\mathrm{nc}}_{\alpha,\mathrm{ABC}}
[\widetilde\rho_\alpha]
+
\mathcal L^{\mathrm{env}}_{\perp}
[\widetilde\rho_\alpha],
\qquad
\alpha\in\{\mathrm{sc},\mathrm{s}\}.
\]

The two terms have different operational meanings.

### 2.1 Direct ABC detector

The scalar or spin-coupled absorbing boundary is the only monitored roof detector. It is trace decreasing in the no-click sector and supplies the detector probability

\[
S_\alpha(t)=\operatorname{Tr}\widetilde\rho_\alpha(t),
\qquad
 g_\alpha(t)=-\dot S_\alpha(t).
\]

### 2.2 Ambient transverse environment

The ambient bath is unmonitored, physical-particle preserving, and trace preserving:

\[
\operatorname{Tr}\mathcal L^{\mathrm{env}}_{\perp}[X]=0.
\]

It can modify the transverse state reaching the roof, but it cannot itself create a roof click or remove permanent no-click probability.

### 2.3 Spinor detector mechanism

The spin-coupled roof entrance law is

\[
\partial_z\Psi=(i\kappa I_2-K)\Psi,
\qquad
K=\frac{\sigma_xp_y-\sigma_yp_x}{\hbar}.
\]

In tangential Fourier space the boundary branches are

\[
i\kappa+R,
\qquad
i\kappa-R,
\qquad R=|\boldsymbol\xi|.
\]

The scalar term \(i\kappa\) is absorptive. The \(\pm R\) part is reactive and coherent. It changes reflection phases, transverse mode content, spin–motion correlations, and return dynamics, but is not an additional loss channel.

### 2.4 Prohibited double counting

Throughout Part I:

- do not add a CAP behind the direct ABC;
- do not add another roof-loss Lindblad operator;
- do not impose the inverse-engineered impedance layer simultaneously with the direct ABC;
- do not count ambient jumps as detector events;
- do not omit ambient recycling terms from a deterministic bath master equation;
- do not introduce an explicit detector temperature \(T_D\).

The direct ABC is already the complete effective detector in Part I.

---

## 3. Frozen detector conventions and provenance

### 3.1 Immutable Cartesian detector core

The following established components remain intact unless a separate regression explicitly changes them:

1. Cartesian indexing and flattening order;
2. `L_z` and the roof ABC closure;
3. `L_dirichlet` in the transverse directions;
4. Kronecker construction of `Lap_scalar` and `Lap_diag`;
5. the spinor roof matrix `C` and
   \[
   \texttt{Lap\_spinor}=\texttt{Lap\_diag}+\texttt{C};
   \]
6. the harmonic transverse potential;
7. Crank–Nicolson/Cayley matrices;
8. complex128 GMRES and the diagonal preconditioner;
9. post-solve Dirichlet assignments;
10. the midpoint roof-loss probability.

### 3.2 Reference packet and detector parameters

The established development calculation uses

\[
\hbar=m=1,
\quad
\kappa=k_0=\pi,
\quad
z_0=10,
\quad
\sigma_z=0.5,
\quad
\theta=\frac{\pi}{6},
\quad
\phi=0.
\]

The longitudinal amplitude is

\[
\varphi_0(z)\propto
\exp\!\left[-\frac{(z-z_0)^2}{2\sigma_z^2}\right]
 e^{ik_0(z-z_0)}.
\]

Thus \(\sigma_z=0.5\) is an amplitude-width convention; the probability-density standard deviation is

\[
\sigma_\parallel=\frac{\sigma_z}{\sqrt2}=0.353553\ldots.
\]

The Cartesian grid uses `endpoint=False`. Therefore the actual on-grid roof is \(z[-1]\), not the nominal number \(L_z\). Scientific comparisons must read the saved configuration rather than infer parameters from folder names.

### 3.3 Primary detector probability

For every Cayley step, the detector probability is the nonnegative midpoint roof loss

\[
p_{D,n}
=
\Delta t\,\kappa h_xh_y
\sum_{x,y,\mathrm{spin}}
\left|
\frac{\psi_n+\psi_{n+1}^{\mathrm{CN}}}{2}
\right|_{z=z_{\mathrm{roof}}}^{2}.
\]

Integrated detector probabilities are formed directly from \(p_{D,n}\), never by numerically differentiating a sampled survival curve.


### 3.4 Principal provenance

| Artifact | SHA-256 / status |
|---|---|
| Frozen `750.Ref.py` source | `815a470da8ec7664ee613f830f384050247f949dac5fa8ab4e0cfd8f331cfbfe` |
| Earlier archival Stage-01 package `01_static_mode(2).zip` | `f17502b7ec643593c4690aa0c30fb868e0a9853eaca41cc94228a0e32e2379f7` |
| User-supplied Stage-01 review copy `Stage01_static_mode(1).zip` | `e9699883149c6f45732fc392e5f3f5b37ed3c79f251c98f212ba6047389cc4f2`; 75 meaningful files; 12/12 configurations present |
| Audited Stage-02 package | `30525cd27cc545941b89ad77daf4cdb904ffa51e45e0f64839951a6d834a7a8c` |
| Final Stage-02 solver | `2ed0daf88dca64d33896d42e53d93c1e57b85d7e22391498babd4f7588b273b2` |
| Final Stage-02 loader | `398a66b51c21e72216da38ef446c4e0e0012b0c23e2d6114b12b19e54e4bfc0b` |
| Final Audit-03 solver `03_bath_only_fock_test.py` | `5e621ee346604d8eef4765c07532ab3b525783af2b9a52d80fa408ef38c65bbe` |
| Audit-03 full CPU certification package | `469177671f683277ea1352d04ab476946bf249d6c4cc5308f202b445df11df0c` |
| Audit-03 acceptance record | `6d90ee8db963a189471a9c7d099648244631fcaaf7269a7735e6b3ae3bc24b9a` |
| Audit-03 stable time-series archive | `fe1a591de7c33fc8432888a4a36bb67c3798ee6328012df590628659eb8daa14` |
| Audit-04 loader `04_bath_only_fock_loader.py` | `cf0246ee8767dbb8862d637a4225952c9625392281d3856a616e69fea22c7d9c` |
| Audit-04 verified package | `0a658b07e6f32d292dce658b9288d196070c7b745db099622306fac7676e11a7` |
| Audit-04 loader audit | `d44c429c4a5fe42cfdd0c1ccd8884fb6eaf422423869ad64032171172b3df69b` |
| Audit-04 independent report | `52e73ce0c55c623091a0a96425b79d08ca0e8e3097cfc127aa2ded0d193a7e31` |
| Audit-04 independent case metrics | `ef105a722872716267d7ee8ac3c48dd70af7d3922960916fa3d603bb0d243b01` |
| Audit-04 independent cutoff metrics | `24022372f499bedc7248e93d6bd02ad01d49818f38ae1fa563d269c14feb6744` |

The two Stage-01 ZIP hashes refer to distinct archive packages. The current review copy was inspected directly and reproduces the declared twelve-case data inventory and numerical tables; its different package hash does not imply a different physical data set.

Only source and output products matching the hashes above are authoritative for the corresponding audit.

---

# Part II — Stage 00 detector-only reference

## 4. Stage 00 purpose

Stage 00 established the zero-ambient-bath detector reference before any transverse environment was introduced. The only nonunitary process was the direct roof ABC.

The principal observables are

\[
S(t),
\qquad
p_{D,n},
\qquad
g(t_{n+1/2})=\frac{p_{D,n}}{\Delta t},
\]

\[
D(T)=1-S(T),
\qquad
\mu^*(T)=\int_0^T S(t)\,dt.
\]

The prompt/late divider used in the development calculations is

\[
t_{\mathrm{cut}}=3.6.
\]

## 5. Stage 00 reference at \(\omega=1\)

Parameters:

\[
\omega=1,
\qquad
\Delta t=10^{-3},
\qquad
T=10,
\qquad
N_t=10{,}000.
\]

| Quantity | Value |
|---|---:|
| final survival \(S(10)\) | \(1.143121284532\times10^{-1}\) |
| detected fraction | \(8.856878715468\times10^{-1}\) |
| accumulated roof probability | \(8.856874940464\times10^{-1}\) |
| restricted mean \(\mu^*(10)\) | \(4.257623567375\) |
| conditional click mean before \(T\) | \(3.516478414074\) |
| early detected fraction | \(5.762347038638\times10^{-1}\) |
| late detected fraction | \(3.094527901826\times10^{-1}\) |
| late fraction among clicks | \(3.493927511258\times10^{-1}\) |
| click-density peak time | \(2.4535\) |

Numerical audit:

| Quantity | Value |
|---|---:|
| relative roof closure | \(4.262\times10^{-7}\) |
| telescoping closure | \(0\) |
| clamp loss | \(0\) |
| relative negative total-step mass | \(8.402\times10^{-8}\) |
| GMRES failures | \(0\) |
| maximum true residual | \(5.415\times10^{-10}\) |
| maximum operator residual | \(0\) |

## 6. Stage 00 reference at \(\omega=100\)

Parameters:

\[
\omega=100,
\qquad
\Delta t=5\times10^{-4},
\qquad
T=10,
\qquad
N_t=20{,}000.
\]

| Quantity | Value |
|---|---:|
| final survival \(S(10)\) | \(4.873590946645\times10^{-1}\) |
| detected fraction | \(5.126409053355\times10^{-1}\) |
| accumulated roof probability | \(5.126406843492\times10^{-1}\) |
| restricted mean \(\mu^*(10)\) | \(6.603815786852\) |
| conditional click mean before \(T\) | \(3.375120410237\) |
| early detected fraction | \(3.649141679858\times10^{-1}\) |
| late detected fraction | \(1.477265163634\times10^{-1}\) |
| late fraction among clicks | \(2.881677574048\times10^{-1}\) |
| click-density peak time | \(2.31875\) |

Numerical audit:

| Quantity | Value |
|---|---:|
| relative roof closure | \(4.311\times10^{-7}\) |
| telescoping closure | \(0\) |
| clamp loss | \(0\) |
| relative negative total-step mass | \(2.781\times10^{-7}\) |
| GMRES failures | \(0\) |
| maximum true residual | \(9.997\times10^{-9}\) |
| maximum operator residual | \(0\) |

## 7. Stage 00 decision

The strict aggregate loader flag was false only because a provisional negative-total-step-mass threshold of \(10^{-8}\) was tighter than the observed complex64 roundoff/cast diagnostic. The load-bearing checks passed:

- no GMRES failure;
- exact telescoping closure;
- zero clamp loss;
- nonnegative midpoint roof probabilities;
- roof/norm closure at approximately \(4\times10^{-7}\) relative error;
- small true linear residuals;
- zero reported operator residual.

Therefore Stage 00 is accepted as the detector reference, with the signed `step_loss_total` retained only as an error monitor. It is not clipped or substituted for the midpoint detector law.

---

# Part III — Completed Stage 01 static-mode audit

## 8. Stage 01 data set and scientific role

The completed archive contains

\[
\{\mathrm{scalar},\mathrm{spinor}\}
\times
\{|0,0\rangle,|1,0\rangle,|0,1\rangle\}
\times
\{\omega=1,100\}.
\]

All twelve propagations pass their individual solver-integrity checks.

This stage changes only the initial transverse mode. No ambient bath acts during propagation.

The first-shell combination

\[
\Delta_\uparrow X
=
X_{10}+X_{01}-2X_{00}
\]

is simultaneously

- the leading low-temperature static-preparation coefficient;
- the unit upward Lindblad direction applied at launch;
- the cheapest detector-specific environmental probe before dynamical bath propagation.

## 9. Common Stage 01 configuration

| \(\omega\) | \(\Delta t\) | \(T\) | steps | grid | \(L_x\) | \(L_y\) | \(\theta\) | \(\phi\) |
|---:|---:|---:|---:|---|---:|---:|---:|---:|
| 1 | 0.001 | 10 | 10000 | \(100\times100\times1500\) | 10 | 10 | 0.52359878 | 0 |
| 100 | \(5\times10^{-4}\) | 10 | 20000 | \(100\times100\times1500\) | 1 | 1 | 0.52359878 | 0 |

All cases use

\[
\kappa=k_0=\pi,
\quad z_0=10,
\quad \sigma_z=0.5,
\quad \theta=\pi/6,
\quad \phi=0.
\]

## 10. Stage 01 numerical integrity

| \(\omega\) | relative roof closure | maximum true residual | GMRES failures | clamp loss | negative roof steps | maximum mode overlap |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | \(4.197\times10^{-7}\)–\(4.313\times10^{-7}\) | \(5.315\times10^{-10}\)–\(5.496\times10^{-10}\) | 0 | 0 | 0 | \(1.301\times10^{-9}\) |
| 100 | \(4.173\times10^{-7}\)–\(4.414\times10^{-7}\) | \(9.742\times10^{-9}\)–\(9.997\times10^{-9}\) | 0 | 0 | 0 | \(2.918\times10^{-8}\) |

Across all twelve cases:

- every GMRES solve completed;
- all midpoint roof probabilities are nonnegative;
- cumulative clamp loss is zero;
- mode normalization and orthogonality are much more accurate than the physical spinor response;
- the ground-mode Stage-01 curves recover the Stage-00 references.

## 11. Mode-resolved detector laws

### 11.1 \(\omega=1\)

| detector | mode | \(S(T)\) | \(D_{\mathrm{roof}}(T)\) | \(\mu^*(T)\) | \(D_E\) | \(D_L\) | \(D_L/D\) | mean click \(|T\) | \(t_{\mathrm{peak}}\) | \(g_{\mathrm{peak}}\) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| scalar | 00 | 0.09311578 | 0.90688383 | 4.12727059 | 0.58759754 | 0.31928629 | 0.35206967 | 3.52427874 | 2.4585 | 0.3691129 |
| scalar | 10 | 0.09311580 | 0.90688381 | 4.12728104 | 0.58759552 | 0.31928829 | 0.35207188 | 3.52429015 | 2.4585 | 0.3691141 |
| scalar | 01 | 0.09311580 | 0.90688381 | 4.12728104 | 0.58759552 | 0.31928829 | 0.35207189 | 3.52429016 | 2.4585 | 0.36911411 |
| spinor | 00 | 0.11431213 | 0.88568749 | 4.25762357 | 0.57623470 | 0.30945279 | 0.34939275 | 3.51647841 | 2.4535 | 0.36231273 |
| spinor | 10 | 0.13410870 | 0.86589093 | 4.38165941 | 0.56534314 | 0.30054778 | 0.34709659 | 3.51149433 | 2.4495 | 0.35578737 |
| spinor | 01 | 0.13410870 | 0.86589093 | 4.38165944 | 0.56534315 | 0.30054779 | 0.34709659 | 3.51149433 | 2.4495 | 0.35578736 |

### 11.2 \(\omega=100\)

| detector | mode | \(S(T)\) | \(D_{\mathrm{roof}}(T)\) | \(\mu^*(T)\) | \(D_E\) | \(D_L\) | \(D_L/D\) | mean click \(|T\) | \(t_{\mathrm{peak}}\) | \(g_{\mathrm{peak}}\) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| scalar | 00 | 0.09313503 | 0.90686459 | 4.12942957 | 0.58709522 | 0.31976937 | 0.35260983 | 3.52652198 | 2.46025 | 0.36890492 |
| scalar | 10 | 0.09321618 | 0.90678344 | 4.13560889 | 0.58564841 | 0.32113502 | 0.35414743 | 3.53275719 | 2.46475 | 0.36825295 |
| scalar | 01 | 0.09321618 | 0.90678342 | 4.13560887 | 0.58564841 | 0.32113502 | 0.35414743 | 3.53275720 | 2.46475 | 0.36825294 |
| spinor | 00 | 0.48735909 | 0.51264068 | 6.60381579 | 0.36491417 | 0.14772652 | 0.28816776 | 3.37512041 | 2.31875 | 0.23641066 |
| spinor | 10 | 0.55697245 | 0.44302736 | 7.18379623 | 0.28223474 | 0.16079262 | 0.36294061 | 3.64327619 | 2.29475 | 0.18470219 |
| spinor | 01 | 0.55697245 | 0.44302736 | 7.18379620 | 0.28223474 | 0.16079262 | 0.36294061 | 3.64327619 | 2.29475 | 0.18470220 |

## 12. First-shell directional symmetry

| \(\omega\) | detector | \(d_{\mathrm{TV}}(10,01)\) | \(\max|S_{10}-S_{01}|\) | \(W_1\) |
|---:|---|---:|---:|---:|
| 1 | scalar | \(1.820\times10^{-8}\) | \(3.810\times10^{-9}\) | \(8.033\times10^{-9}\) |
| 1 | spinor | \(1.776\times10^{-8}\) | \(8.215\times10^{-9}\) | \(2.581\times10^{-8}\) |
| 100 | scalar | \(3.092\times10^{-8}\) | \(1.297\times10^{-8}\) | \(3.609\times10^{-8}\) |
| 100 | spinor | \(1.738\times10^{-8}\) | \(8.574\times10^{-9}\) | \(3.527\times10^{-8}\) |

Thus

\[
\nu_{\alpha,10}\simeq\nu_{\alpha,01}
\]

for the present trap, geometry, spin preparation, and click-time marginal. This is an excellent internal isotropy check.

## 13. Scalar null-control result

| \(\omega\) | comparison | \(d_{\mathrm{TV}}\) | \(\max|\Delta S|\) | \(W_1\) | \(\Delta\mu^*\) | \(\Delta D_E\) | \(\Delta D_L\) |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 10–00 | \(1.588072\times10^{-5}\) | \(4.512081\times10^{-6}\) | \(1.061672\times10^{-5}\) | \(1.044171\times10^{-5}\) | \(-2.024052\times10^{-6}\) | \(2.004892\times10^{-6}\) |
| 1 | 01–00 | \(1.588103\times10^{-5}\) | \(4.510397\times10^{-6}\) | \(1.061946\times10^{-5}\) | \(1.044411\times10^{-5}\) | \(-2.024682\times10^{-6}\) | \(2.006853\times10^{-6}\) |
| 100 | 10–00 | \(5.215853\times10^{-3}\) | \(1.865808\times10^{-3}\) | \(6.179325\times10^{-3}\) | \(6.179325\times10^{-3}\) | \(-1.446806\times10^{-3}\) | \(1.365650\times10^{-3}\) |
| 100 | 01–00 | \(5.215852\times10^{-3}\) | \(1.865801\times10^{-3}\) | \(6.179308\times10^{-3}\) | \(6.179305\times10^{-3}\) | \(-1.446815\times10^{-3}\) | \(1.365646\times10^{-3}\) |

At \(\omega=1\), the scalar residual is compatible with the current numerical floor.

At \(\omega=100\), the residual is not physical. The exact scalar evolution factorizes, but a monolithic Cayley transform of a Kronecker-sum generator does not equal the tensor product of the separate Cayley maps:

\[
C_h(H_z\otimes I+I\otimes H_\perp)
\neq
C_h(H_z)\otimes C_h(H_\perp).
\]

This finite-step nonfactorization explains the mode-dependent scalar artifact when \(h\omega\) is not very small.

## 14. Spinor static-mode response

For one first-shell direction relative to the ground mode:

| \(\omega\) | \(d_{\mathrm{TV}}(1,0)\) | \(\Delta S(T)\) | \(\Delta D\) | \(\Delta\mu^*\) | \(\Delta D_E\) | \(\Delta D_L\) | mean click \(|T\) | late fraction |
|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | 0.020166 | +0.019797 | -0.019797 | +0.124036 | -0.010892 | -0.008905 | 3.516478→3.511494 | 0.349393→0.347097 |
| 100 | 0.104751 | +0.069613 | -0.069613 | +0.579980 | -0.082679 | +0.013066 | 3.375120→3.643276 | 0.288168→0.362941 |

At \(\omega=100\), first-shell excitation:

- reduces total detection by approximately \(6.96\times10^{-2}\);
- removes approximately \(8.27\times10^{-2}\) from the prompt sector;
- adds approximately \(1.31\times10^{-2}\) to the late sector;
- moves the click-conditioned mean from \(3.3751\) to \(3.6433\);
- increases the late fraction from \(0.2882\) to \(0.3629\).

This is a genuine prompt-to-return-sector restructuring, not only a larger censored atom at \(T\).

## 15. Low-temperature first-shell coefficient

| \(\omega\) | detector | \(\Delta_\uparrow S(T)\) | \(\Delta_\uparrow D\) | \(\Delta_\uparrow\mu^*\) | \(\Delta_\uparrow D_E\) | \(\Delta_\uparrow D_L\) | \(\tfrac12\|\Delta_\uparrow\nu\|_1\) | closure |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | scalar | \(+2.814808\times10^{-8}\) | \(-3.698817\times10^{-8}\) | \(+2.088582\times10^{-5}\) | \(-4.048734\times10^{-6}\) | \(+4.011745\times10^{-6}\) | \(3.176174\times10^{-5}\) | \(-8.840\times10^{-9}\) |
| 1 | spinor | \(+3.959315\times10^{-2}\) | \(-3.959313\times10^{-2}\) | \(+2.480717\times10^{-1}\) | \(-2.178312\times10^{-2}\) | \(-1.781001\times10^{-2}\) | \(4.033287\times10^{-2}\) | \(2.086\times10^{-8}\) |
| 100 | scalar | \(+1.623019\times10^{-4}\) | \(-1.623249\times10^{-4}\) | \(+1.235863\times10^{-2}\) | \(-2.893621\times10^{-3}\) | \(+2.731296\times10^{-3}\) | \(1.043170\times10^{-2}\) | \(-2.305\times10^{-8}\) |
| 100 | spinor | \(+1.392267\times10^{-1}\) | \(-1.392266\times10^{-1}\) | \(+1.159961\) | \(-1.653589\times10^{-1}\) | \(+2.613221\times10^{-2}\) | \(2.095012\times10^{-1}\) | \(5.876\times10^{-8}\) |

The spinor first-shell response norm grows by a factor \(5.19\) between \(\omega=1\) and \(100\). Two confinement points do not establish a universal law, but they establish stronger preparation sensitivity at strong confinement.

For a Gibbs parameter \(q_{\mathrm{prep}}\ll1\),

\[
X^{\mathrm{th}}
=
X_{00}+q_{\mathrm{prep}}\Delta_\uparrow X
+O(q_{\mathrm{prep}}^2).
\]

The present first-shell coefficients are not a complete moderate-temperature Gibbs calculation.

## 16. Stage 01 decision

### Established

1. All twelve individual Cartesian runs are numerically valid.
2. Ground-mode Stage-01 curves recover Stage 00.
3. The \(10/01\) first-shell degeneracy is excellent.
4. The spinor detector is strongly sensitive to transverse preparation.
5. Strong confinement amplifies this sensitivity.
6. At \(\omega=100\), first-shell excitation suppresses prompt clicks and enhances delayed returns.

### Not yet established

1. A publication-grade scalar null at \(\omega=100\).
2. A time-step-converged numerical value for the strong-confinement spinor response.
3. A complete Gibbs preparation beyond the first-shell expansion.
4. Any dynamical damping, heating, or dephasing effect.
5. A universal \(\sqrt\omega\) law for the static response.

---


# Part IV — Full Audit-01 archive review and scalar-control clarification

## 17. Direct inspection of `Stage01_static_mode(1).zip`

The supplied ZIP is a complete Audit-01 archive for the scope that was actually run. After removing macOS metadata, it contains:

| Item | Count |
|---|---:|
| meaningful files | 75 |
| configuration JSON files | 12 |
| solver-audit JSON files | 12 |
| NumPy arrays | 36 |
| JSON files in total | 36 |
| aggregate CSV tables | 2 |
| embedded Markdown audit | 1 |

The twelve configurations cover exactly

\[
\{\mathrm{scalar},\mathrm{spinor}\}
\times
\{|00\rangle,|10\rangle,|01\rangle\}
\times
\{\omega=1,100\}.
\]

Every solver-audit record has `status = completed`, every case has zero GMRES failures, and every case has zero cumulative clamp loss. The aggregate metrics in the ZIP reproduce the Audit-01 tables already recorded in this master file.

The configuration review also shows:

| Confinement | Time step in every archived case | Horizon |
|---:|---:|---:|
| \(\omega=1\) | \(10^-3\) | \(10\) |
| \(\omega=100\) | \(5\times10^-4\) | \(10\) |

There is no missing detector/mode run in the archive.

## 18. What the former label `Stage 01C` meant

The phrase `Stage 01C` was introduced in the earlier master audit as a name for an **additional convergence and factorization control**, not for part of the twelve-case library. The archive contains neither:

- scalar or spinor \(\omega=100\) runs at \(\Delta t=2.5\times10^-4\); nor
- a separately factorized scalar finite-step propagator.

Therefore the ZIP is complete for Audit 01, but it does not contain that later proposed addendum.

The reason for the addendum remains valid. The archived scalar comparison at \(\omega=100\) gives

\[
d_{\mathrm{TV}}(\nu_{\mathrm{sc},10},\nu_{\mathrm{sc},00})
=5.215853\times10^-3,
\]

whereas exact scalar longitudinal--transverse factorization predicts a null click-time response. The embedded Audit-01 report correctly attributes this to applying one monolithic Cayley transform to a Kronecker-sum Hamiltonian at finite time step, not to physical transverse sensitivity of the scalar ABC.

To avoid a hidden or confusing extra stage, the workflow is now revised as follows:

\[
\boxed{
\text{Audit 01 is complete}
\quad\text{and}\quad
\text{its scalar/time-step closure is Task 05A}.
}
\]

Task 05A will contain both the exact factorized scalar control and the monolithic time-step-halving diagnostic in the oscillator-channel representation. This is more efficient than treating `Stage 01C` as a separate legacy task, and it resolves the issue in the same representation required for the later bath calculation.

---

# Part V — Stage 02 transverse operator certification

## 19. Scientific role and scope

Stage 02 certifies the transverse operator layer required by the later trace-preserving oscillator bath. It contains no detector–bath dynamics.

It deliberately contains:

- no scalar or spinor ABC propagation;
- no roof matrix `C` construction or modification;
- no longitudinal coordinate;
- no Cayley or Crank–Nicolson step;
- no GMRES solve;
- no Lindblad time evolution;
- no bath rates;
- no detector-time observable.

A Stage-02 PASS therefore cannot alter any Stage-00 or Stage-01 detector result.

## 20. Two representations

### 20.1 Authoritative complete-shell oscillator representation

The retained basis is

\[
\mathcal I_N
=
\{(n_x,n_y)\in\mathbb N_0^2:n_x+n_y\le N\}.
\]

For \(N=12\),

\[
M_\perp(N)
=
\frac{(N+1)(N+2)}{2}
=91.
\]

The projected operators are

\[
a_j^{(N)}=P_Na_jP_N,
\qquad
N_j^{(N)}=a_j^{(N)\dagger}a_j^{(N)}.
\]

This orthonormal complete-shell representation is the production representation for Stage 03 and later oscillator-channel work.

### 20.2 Cartesian cross-check

The Cartesian realization is only a low-mode compatibility test. It uses the Stage-01 conventions

\[
L_x=L_y=\frac{10}{\sqrt\omega},
\]

with `endpoint=False`, sidewall clamping, uniform quadrature, and the \(|00\rangle\), \(|10\rangle\), and \(|01\rangle\) mode formulas.

It must approach the ideal oscillator algebra with second-order centered-difference convergence. It is not the production bath basis.

## 21. Final Stage-02 configuration

```text
N_shell = 12
M_perp   = 91
omega cases = 1 and 100
Cartesian grids = 50, 100, 200
reference Cartesian case = omega 100, N = 100
hbar = m = 1
ell = 10
arithmetic = NumPy float64 / complex128
backend = CPU
```

The shell value \(N=12\) is a certification cutoff, not a claim of dynamical convergence for Stage 03.

## 22. Final scripts, directory, and commands

Authoritative scripts:

```text
4050_bath_operator_tests_solver.py
4051_bath_operator_tests_loader.py
```

Fixed directory:

```text
4050.Bath_operator_tests
```

Cluster execution:

```bash
OUTDIR=[ARCHIVE_PATH] \
python 4050_bath_operator_tests_solver.py

OUTDIR=[ARCHIVE_PATH] \
python 4051_bath_operator_tests_loader.py
```

Laptop execution:

```bash
python3 -m pip install numpy
python3 4050_bath_operator_tests_solver.py
python3 4051_bath_operator_tests_loader.py
```

With no `OUTDIR`, the fixed directory is created under the current working directory.

The same directory is intentionally reused. There are no timestamps and no automatically generated parameter folders.

## 23. Operator identities tested

### 23.1 Ladder actions

For every retained state,

\[
a_x|n_x,n_y\rangle
=\sqrt{n_x}|n_x-1,n_y\rangle,
\]

\[
a_y|n_x,n_y\rangle
=\sqrt{n_y}|n_x,n_y-1\rangle.
\]

Below the top shell,

\[
a_x^\dagger|n_x,n_y\rangle
=\sqrt{n_x+1}|n_x+1,n_y\rangle,
\]

and similarly for \(y\). On the top shell the projected creation operator must vanish.

The required low-mode tests are included explicitly:

\[
a_x|00\rangle=0,
\quad
a_y|00\rangle=0,
\]

\[
a_x|10\rangle=|00\rangle,
\quad
a_y|01\rangle=|00\rangle,
\]

\[
a_x^\dagger|00\rangle=|10\rangle,
\quad
a_y^\dagger|00\rangle=|01\rangle.
\]

### 23.2 Adjoint and number operators

\[
a_x^\dagger=a_x^H,
\qquad
a_y^\dagger=a_y^H,
\]

\[
N_x=a_x^\dagger a_x\ge0,
\qquad
N_y=a_y^\dagger a_y\ge0.
\]

### 23.3 Correct projected commutator

A finite-dimensional matrix pair cannot satisfy \([a,a^\dagger]=I\) on the complete finite space because the trace of a finite commutator is zero.

The Stage-02 code instead checks the exact complete-shell formulas, including the upper-shell defect and all cross-axis projected commutators. This is the mathematically correct finite projection.

### 23.4 Transverse Hamiltonian and Bohr relations

\[
H_\perp
=
\hbar\omega(N_x+N_y+I),
\]

\[
[H_\perp,a_j]
=-\hbar\omega a_j,
\qquad
[H_\perp,a_j^\dagger]
=+\hbar\omega a_j^\dagger.
\]

### 23.5 Spin–momentum operator

The oscillator-basis operator is

\[
K
=
\frac{i}{\sqrt2\,\ell_\perp}
\left[
\sigma_x(a_y^\dagger-a_y)
-
\sigma_y(a_x^\dagger-a_x)
\right].
\]

The implementation verifies:

- \(K^\dagger=K\);
- equality of the ladder and momentum formulas;
- \(K\propto\sqrt\omega\).

This certifies the oscillator representation used later. It does not modify the Cartesian roof matrix `C`.

## 24. Independent solver–loader audit design

The solver constructs and saves matrices and raw metrics. The loader does not import or trust the solver. It independently:

1. verifies all stable solver-output hashes;
2. verifies the frozen configuration and internal hashes;
3. verifies the copied solver source hash;
4. reconstructs every complete-shell metric from saved matrices;
5. rebuilds all six Cartesian cases;
6. recomputes convergence orders;
7. recomputes the \(\omega=1/100\) collapse;
8. reapplies every gate;
9. compares every solver and loader metric, threshold, relation, and PASS/FAIL decision.

Additional code-level tests passed:

- Python compilation and AST parsing;
- clean full solver/loader execution;
- repeated same-directory execution;
- stale-loader invalidation after a solver rerun;
- deliberate hash-tamper rejection;
- JSON and NPZ loading with `allow_pickle=False`;
- source-import confirmation that no CuPy, GPU, GMRES, detector solver, or detector matrix is used.

## 25. Fresh execution results

Fresh CPU execution returned

```text
solver return code = 0
loader return code = 0
solver acceptance = PASS
independent loader acceptance = PASS
solver/loader agreement = PASS
stable solver hashes = 10/10
```

### 25.1 Authoritative complete-shell results

| Check | Maximum defect |
|---|---:|
| all projected ladder actions | \(0.000000\times10^0\) |
| adjoint consistency | \(5.553085\times10^{-16}\) |
| number-operator diagonal identity | \(1.776357\times10^{-15}\) |
| exact projected commutator formulas | \(7.105427\times10^{-15}\) |
| oscillator Bohr relations | \(2.167914\times10^{-15}\) |
| transverse-Hamiltonian formula | \(0\) |
| \(K\) Hermiticity | \(0\) |
| \(K\) ladder/momentum formula | \(0\) |
| \(K/\sqrt\omega\) scale collapse | \(4.440892\times10^{-16}\) |

### 25.2 Cartesian reference case

For \(\omega=100\), \(N_x=N_y=100\):

| Quantity | Value |
|---|---:|
| maximum ladder-action residual | \(4.260196\times10^{-3}\) |
| maximum occupation error | \(2.478728\times10^{-3}\) |
| maximum low-mode CCR residual | \(9.654272\times10^{-3}\) |
| maximum cross-commutator residual | \(1.625214\times10^{-15}\) |
| maximum \(x/y\) isotropy defect | \(1.734723\times10^{-18}\) |
| maximum wall-leakage metric | \(1.482597\times10^{-10}\) |

Across the full Cartesian suite:

\[
p_{\min}=1.962974>1.9,
\]

and

\[
\max\bigl|\text{dimensionless residual}_{\omega=1}
-
\text{dimensionless residual}_{\omega=100}\bigr|
=3.747003\times10^{-14}.
\]

The nonzero Cartesian ladder and occupation residuals are controlled second-order finite-difference errors, not defects in the authoritative oscillator matrices.

### 25.3 Runtime

| Part | Runtime |
|---|---:|
| solver internal calculation | \(0.274\,\mathrm{s}\) |
| solver wall time | \(0.95\,\mathrm{s}\) |
| loader wall time | \(0.87\,\mathrm{s}\) |

Stage 02 is therefore comfortably laptop scale.

## 26. Complete Stage-02 gate table

| Gate | Status | Metric | Threshold |
|---|---|---:|---:|
| `authoritative_all_ladder_actions` | PASS | \(0.000000\times10^0\) | \(\le10^{-12}\) |
| `authoritative_adjoint` | PASS | \(5.553085\times10^{-16}\) | \(\le10^{-12}\) |
| `authoritative_number_positivity` | PASS | \(0\) | \(\ge-10^{-11}\) |
| `authoritative_number_diagonal` | PASS | \(1.776357\times10^{-15}\) | \(\le10^{-12}\) |
| `authoritative_xy_isotropy` | PASS | \(0\) | \(\le10^{-12}\) |
| `authoritative_projected_commutator_formulas` | PASS | \(7.105427\times10^{-15}\) | \(\le10^{-12}\) |
| `authoritative_bohr_relations` | PASS | \(2.167914\times10^{-15}\) | \(\le10^{-12}\) |
| `authoritative_K_hermiticity` | PASS | \(0\) | \(\le10^{-12}\) |
| `authoritative_K_formula` | PASS | \(0\) | \(\le10^{-12}\) |
| `authoritative_K_sqrtomega_scaling` | PASS | \(4.440892\times10^{-16}\) | \(\le10^{-12}\) |
| `cartesian_reference_case_present` | PASS | 1 | \(=1\) |
| `cartesian_mode_orthonormality` | PASS | \(7.552075\times10^{-11}\) | \(\le10^{-8}\) |
| `cartesian_weighted_adjoint` | PASS | \(6.502165\times10^{-15}\) | \(\le10^{-12}\) |
| `cartesian_number_positivity` | PASS | \(-3.719268\times10^{-15}\) | \(\ge-10^{-11}\) |
| `cartesian_ladder_O_eta_squared` | PASS | \(4.272001\times10^{-1}\) | \(\le7.5\times10^{-1}\) |
| `cartesian_occupation_O_eta_squared` | PASS | \(2.494656\times10^{-1}\) | \(\le5.0\times10^{-1}\) |
| `cartesian_CCR_O_eta_squared` | PASS | \(9.675411\times10^{-1}\) | \(\le1.25\) |
| `cartesian_second_order_refinement` | PASS | \(1.962974\) | \(\ge1.9\) |
| `cartesian_cross_commutators` | PASS | \(6.111750\times10^{-15}\) | \(\le10^{-12}\) |
| `cartesian_xy_isotropy` | PASS | \(9.996344\times10^{-17}\) | \(\le10^{-12}\) |
| `cartesian_omega_scale_collapse` | PASS | \(3.747003\times10^{-14}\) | \(\le10^{-12}\) |
| `cartesian_lateral_wall_leakage` | PASS | \(6.036987\times10^{-10}\) | \(\le10^{-8}\) |

## 27. Stage-02 output products

Solver products:

```text
Stage02_configuration.json
Stage02_authoritative_audit.json
Stage02_authoritative_operators.npz
Stage02_cartesian_case_metrics.csv
Stage02_cartesian_convergence_metrics.csv
Stage02_cartesian_omega_collapse_metrics.csv
Stage02_cartesian_reference_arrays.npz
Stage02_acceptance.json
Stage02_solver_audit.json
Stage02_output_hashes.json
Stage02_run_status.json
Stage02_stdout.txt
Stage02_simulation_log.txt
```

Loader products:

```text
Stage02_loader_audit.json
Stage02_loader_case_metrics.csv
Stage02_loader_convergence_metrics.csv
Stage02_loader_omega_collapse_metrics.csv
Stage02_bath_operator_report.md
Stage02_loader_output_hashes.json
```

Exit convention:

```text
0  all scientific and consistency gates pass
2  calculation completes but at least one scientific gate fails
1  execution or I/O failure
```

## 28. Stage 02 final decision

\[
\boxed{\text{Stage 02 is fully certified for its declared scope.}}
\]

The projected complete-shell ladder operators, adjoints, number operators, projected commutator structure, oscillator Hamiltonian, Bohr relations, and spin–momentum operator \(K\) are correct. The Cartesian low-mode realization converges to the same structure with controlled second-order error, negligible wall leakage, excellent isotropy, and the expected confinement scaling.

No additional \(\omega\), grid, shell, detector, or time-propagation run is required to accept Stage 02.

Stage 02 alone did **not** certify any dynamical bath property. The completed Stage-03 solver certification below now supplies that detector-free dynamical test.

---

# Part VI — Completed Stage 03 detector-free bath solver certification


## 29. Audit-03 scientific scope and exact status

Audit 03 certifies the finite projected transverse environment before it is combined with either absorbing-boundary detector. The implemented solver contains:

- no longitudinal coordinate;
- no scalar ABC;
- no spin-coupled ABC;
- no roof matrix `C`;
- no detector-loss operator or click observable;
- no Crank--Nicolson/Cayley detector step;
- no GMRES solve;
- no Monte Carlo trajectories;
- no positivity clipping;
- no trace renormalization.

The propagated equation is

\[
\mathcal L_{\perp,N}^{\mathrm{env}}[\rho]
=
-i[H_{\perp,N},\rho]
+
\Gamma_\downarrow\sum_{j=x,y}\mathcal D[a_j^{(N)}]\rho
+
\Gamma_\uparrow\sum_{j=x,y}\mathcal D[a_j^{(N)\dagger}]\rho
+
\gamma_\phi\sum_{j=x,y}\mathcal D[N_j^{(N)}]\rho,
\]

with \(\hbar=m=\omega=1\) for the certification suite and

\[
\mathcal D[L]\rho
=L\rho L^\dagger-\frac12\{L^\dagger L,\rho\}.
\]

All ambient recycling terms are retained. Since no detector is present, the required probability law is

\[
\operatorname{Tr}\rho(t)=1.
\]

The solver-level result is

\[
\boxed{\text{Audit-03 solver: PASS, 32/32 gates.}}
\]

The independent Audit-04 loader has now also passed. Hence the complete detector-free bath branch is closed for the declared B0--B8 finite-model scope:

\[
\boxed{
\text{Audit-03 solver PASS}
+
\text{Audit-04 independent loader PASS}.
}
\]

The separate Audit-04 report below records the independent reconstruction and integrity tests.

## 30. Executed finite representation and numerical architecture

For every complete-shell cutoff,

\[
\mathcal I_N
=
\{(n_x,n_y)\in\mathbb N_0^2:n_x+n_y\le N\},
\]

the solver reconstructs independently

\[
a_j^{(N)}=P_Na_jP_N,
\qquad
N_j^{(N)}=a_j^{(N)\dagger}a_j^{(N)},
\]

\[
H_{\perp,N}=\omega\left(N_x^{(N)}+N_y^{(N)}+I\right).
\]

The frozen ordering is shell ascending with \(n_x\) descending within each shell:

\[
|0,0\rangle;
\quad
|1,0\rangle,|0,1\rangle;
\quad
|2,0\rangle,|1,1\rangle,|0,2\rangle;
\quad\ldots
\]

The tested dimensions are

| cutoff \(N\) | Hilbert dimension \(M_\perp=(N+1)(N+2)/2\) | Liouville dimension \(M_\perp^2\) | audit-Liouvillian nonzeros |
|---:|---:|---:|---:|
| 8 | 45 | 2,025 | 7,209 |
| 12 | 91 | 8,281 | 32,617 |
| 16 | 153 | 23,409 | 97,393 |

Density matrices are vectorized in column-major order,

```python
rho.reshape(-1, order="F")
```

using the frozen identity

\[
\operatorname{vec}(A\rho B)
=
(B^T\otimes A)\operatorname{vec}(\rho).
\]

Propagation uses

```python
scipy.sparse.linalg.expm_multiply
```

in `complex128`. The finite-generator exponential action is evaluated at 101 equally spaced diagnostic times over

\[
0\le t\le20.
\]

The software environment recorded in the certification package was

```text
Python 3.13.5
NumPy 2.3.5
SciPy 1.17.0
Linux x86_64
```

The fixed output directory is

```text
4060.Bath_only_tests
```

and is intentionally reused without timestamps or parameter-generated subdirectories.

## 31. Exact finite-cutoff event accounting

For projected creation operators, the untruncated formula

\[
\Gamma_\uparrow\langle N_\perp+2\rangle
\]

is not the exact finite-shell upward intensity because an attempted creation from the top shell is projected out.

Let \(\Pi_N\) project onto the top shell and

\[
p_{\mathrm{top}}(t)=\operatorname{Tr}[\Pi_N\rho(t)].
\]

The implemented exact projected upward intensity is

\[
r_\uparrow^{(N)}(t)
=
\Gamma_\uparrow
\left[
\langle N_\perp+2\rangle_t
-(N+2)p_{\mathrm{top}}(t)
\right].
\]

The complete projected amplitude-event intensity is

\[
r_{\mathrm{amp}}^{(N)}(t)
=
\Gamma_\downarrow\langle N_\perp\rangle_t
+r_\uparrow^{(N)}(t).
\]

The omitted untruncated upward intensity and accumulated overflow are

\[
r_\uparrow^{\mathrm{omit}}(t)
=
\Gamma_\uparrow(N+2)p_{\mathrm{top}}(t),
\]

\[
\epsilon_{\mathrm{overflow}}(t)
=
\int_0^t r_\uparrow^{\mathrm{omit}}(s)\,ds.
\]

The projected intensity identity was verified directly against the jump-operator expectation with maximum defect

\[
3.885781\times10^{-16}.
\]

## 32. Frozen B0--B8 suite

| Case | Cutoff and initial state | Active rates | Required result |
|---|---|---|---|
| B0 | \(N=12\), \(|00\rangle\langle00|\) | \(\Gamma_\downarrow=0.2\) | exact ground-state stationarity |
| B1x | \(N=12\), \(|10\rangle\langle10|\) | \(\Gamma_\downarrow=0.2\) | \(\langle N_\perp(t)\rangle=e^{-0.2t}\) |
| B1y | \(N=12\), \(|01\rangle\langle01|\) | \(\Gamma_\downarrow=0.2\) | same law and \(x/y\) isotropy |
| B2 | \(N=8,12,16\), \(|00\rangle\langle00|\) | \(\Gamma_\downarrow=0.25,\Gamma_\uparrow=0.05\) | thermal heating and projected-population agreement |
| B3 | \(N=8,12,16\), \(|20\rangle\langle20|\) | same thermal rates | relaxation toward total occupation \(0.5\) |
| B4 | \(N=12\), projected Gibbs state with \(q=0.2\) | same thermal rates | stationarity and projected event balance |
| B5 | \(N=12\), projected coherent state \(\alpha_x=0.4\) | same thermal rates | coherent-amplitude decay with projected residual control |
| B6 | \(N=12\), \((|00\rangle+|10\rangle)/\sqrt2\) | \(\gamma_\phi=0.2\) | population/energy invariance and coherence decay |
| B7 | \(N=12\), random Hermitian tests | unit-rate isotropic channels | invariance under five independent \(U(2)\) rotations |
| B8 | B2 and B3 at \(N=8,12,16\) | thermal rates | shell convergence, top-shell control, and overflow control |

For the thermal cases,

\[
\Gamma_\downarrow=0.25,
\qquad
\Gamma_\uparrow=0.05,
\qquad
\gamma_\perp=0.20,
\]

\[
q=\frac{\Gamma_\uparrow}{\Gamma_\downarrow}=0.2,
\qquad
\bar n_\infty=0.25
\]

per oscillator mode.

## 33. CPU execution, resource use, and deterministic reproducibility

The exact unmodified solver

```text
03_bath_only_fock_test.py
```

with SHA-256

```text
5e621ee346604d8eef4765c07532ab3b525783af2b9a52d80fa408ef38c65bbe
```

was executed twice from start to finish in the same fixed output directory.

| execution | internal solver time | wall time | peak resident memory | swap | exit code |
|---|---:|---:|---:|---:|---:|
| first complete run | 10.511 s | 12.10 s | 433,968 KiB | 0 | 0 |
| same-directory rerun | 10.317 s | 11.68 s | 433,948 KiB | 0 | 0 |

The following stable numerical outputs were bit-for-bit identical before and after the rerun:

| file | SHA-256 |
|---|---|
| `Stage03_time_series.npz` | `fe1a591de7c33fc8432888a4a36bb67c3798ee6328012df590628659eb8daa14` |
| `Stage03_case_metrics.csv` | `bbe3468f86e90c8ceee414545b3b47ad65963fba848d66ec7742cb3564ed0dba` |
| `Stage03_cutoff_metrics.csv` | `cee67aac556bfa9269ced31c3d666da66ce2d3d15fa708846adb73498742415a` |
| `Stage03_operator_audit.json` | `4fa2fd11b4587b4ec9d8fee3c7cc62fcff0d78209e3e4e9bb38b87984cd567bb` |
| `Stage03_acceptance.json` | `6d90ee8db963a189471a9c7d099648244631fcaaf7269a7735e6b3ae3bc24b9a` |
| `Stage03_configuration.json` | `b3b7752bb2e1906ddcac6bd7c25ec5611bdc50576c650188818fa1c5af493584` |

The complete CPU certification package has SHA-256

```text
469177671f683277ea1352d04ab476946bf249d6c4cc5308f202b445df11df0c
```

and contains the solver, all fixed products, both execution records, stable-hash comparisons, the exact augmented overflow audit, and the 10,001-point population-space audit.

## 34. Numerical results

### 34.1 Global algebraic and physical-state audit

| Test | Observed value | Required threshold | Result |
|---|---:|---:|---|
| maximum projected-operator identity defect | \(1.598721\times10^{-14}\) | \(\le10^{-12}\) | PASS |
| Liouvillian trace-row defect | \(4.996004\times10^{-16}\) | \(\le10^{-12}\) | PASS |
| column-major vectorization defect | \(1.884938\times10^{-16}\) | \(\le10^{-12}\) | PASS |
| generator Hermiticity-action defect | \(3.898133\times10^{-17}\) | \(\le10^{-12}\) | PASS |
| maximum propagated trace error | \(1.043610\times10^{-14}\) | \(\le10^{-12}\) | PASS |
| maximum density Hermiticity defect | \(0\) | \(\le10^{-12}\) | PASS |
| minimum density-matrix eigenvalue | \(0\) | \(\ge-10^{-11}\) | PASS |
| projected event-intensity formula defect | \(3.885781\times10^{-16}\) | \(\le10^{-12}\) | PASS |

No density matrix required clipping or renormalization.

### 34.2 B0 and B1 — exact ground and one-quantum controls

For B0,

| Quantity | Value |
|---|---:|
| maximum trace error | \(2.220446\times10^{-16}\) |
| maximum trace distance from \(|00\rangle\langle00|\) | \(1.110223\times10^{-16}\) |
| final occupation | \(0\) |
| final purity | \(1\) |

For B1x and B1y,

\[
\langle N_\perp(20)\rangle
=e^{-4}
=0.01831563888873418,
\]

while both numerical values were

\[
0.018315638888734168.
\]

The maximum occupation-law error was

\[
2.220446\times10^{-16},
\]

and the \(x/y\) difference was exactly zero in the recorded arithmetic.

### 34.3 B2 — thermal heating from the ground state

The infinite-oscillator reference is

\[
\langle N_\perp(t)\rangle
=0.5(1-e^{-0.2t}).
\]

At \(T=20\),

\[
\langle N_\perp(20)\rangle_\infty
=0.4908421805556329.
\]

For \(N=12\),

| Quantity | Value |
|---|---:|
| final projected occupation | \(0.4908421076415340\) |
| final difference from infinite reference | \(7.291410\times10^{-8}\) |
| maximum projected population-reference \(L^1\) error | \(5.820080\times10^{-15}\) |
| maximum projected occupation-reference error | \(3.663736\times10^{-15}\) |
| maximum top-shell population | \(2.888132\times10^{-8}\) |
| exact augmented-generator overflow | \(1.575638973\times10^{-7}\) |
| final purity | \(0.4499214076566432\) |

The full density-matrix propagation therefore agrees with the independently constructed projected population generator at the \(10^{-15}\) level. The remaining difference from the infinite formula is a controlled finite-shell effect.

### 34.4 B3 — thermal relaxation from \(|20\rangle\)

The infinite-oscillator law is

\[
\langle N_\perp(t)\rangle
=0.5+1.5e^{-0.2t}.
\]

At \(T=20\),

\[
\langle N_\perp(20)\rangle_\infty
=0.5274734583331012.
\]

For \(N=12\),

| Quantity | Value |
|---|---:|
| final projected occupation | \(0.5274732275613051\) |
| final difference from infinite reference | \(2.307718\times10^{-7}\) |
| maximum difference from infinite reference | \(2.773510\times10^{-7}\) |
| maximum projected population-reference \(L^1\) error | \(7.310993\times10^{-15}\) |
| maximum projected occupation-reference error | \(4.329870\times10^{-15}\) |
| high-resolution maximum top-shell population | \(1.073604689\times10^{-7}\) |
| exact augmented-generator overflow | \(8.766369799\times10^{-7}\) |
| final purity | \(0.4284806321705061\) |

This is the tightest Stage-03 cutoff gate. Its exact refined overflow obeys

\[
8.766369799\times10^{-7}<10^{-6},
\]

leaving the margin

\[
1.233630201\times10^{-7}.
\]

Thus \(N=12\) passes the frozen bath-only tolerance, but not by a large margin.

### 34.5 B4 — projected Gibbs stationarity and detailed balance

For

\[
\rho_{B,N}\propto P_Nq^{N_\perp}P_N,
\qquad q=0.2,
\]

the recorded results were

| Quantity | Value |
|---|---:|
| direct generator residual \(\|\mathcal L_N[\rho_{B,N}]\|_F\) | \(1.406763\times10^{-17}\) |
| maximum propagated trace distance | \(3.439279\times10^{-16}\) |
| initial total occupation | \(0.4999998807244785\) |
| final total occupation | \(0.4999998807244795\) |
| downward equilibrium intensity | \(0.12499997018111962\) |
| upward equilibrium intensity | \(0.12499997018111970\) |
| relative detailed-balance defect | \(6.661340\times10^{-16}\) |

The small difference between the projected occupation and the untruncated value \(0.5\) is a finite-\(N\) normalization effect; the projected state itself is stationary to machine precision.

### 34.6 B5 — coherent-amplitude decay

For \(\alpha_x=0.4\), the target law is

\[
\langle a_x(t)\rangle
\simeq
 e^{-[0.1+i]t}\langle a_x(0)\rangle.
\]

The audit gave

| Quantity | Value |
|---|---:|
| maximum absolute amplitude error | \(1.081089\times10^{-7}\) |
| declared threshold | \(10^{-6}\) |
| initial omitted coherent-state tail | \(6.234196\times10^{-21}\) |
| final projected residual-integral bound | \(2.010996\times10^{-7}\) |
| maximum excess above residual bound | \(1.285473\times10^{-16}\) |
| projected residual reconstruction error | \(1.167759\times10^{-11}\) |
| final overflow | \(1.944208\times10^{-7}\) |

The observed finite-cutoff amplitude deviation is quantitatively accounted for by the exact projected Heisenberg residual; it is not hidden as an unexplained solver error.

### 34.7 B6 and B7 — dephasing and isotropic basis invariance

For B6,

\[
|\psi_0\rangle
=\frac{|00\rangle+|10\rangle}{\sqrt2},
\qquad
\gamma_\phi=0.2,
\]

and the expected coherence envelope is

\[
|\rho_{00,10}(t)|=\frac12e^{-0.1t}.
\]

The recorded maximum errors were

| Quantity | Value |
|---|---:|
| population invariance | \(1.665335\times10^{-16}\) |
| total-occupation invariance | \(1.665335\times10^{-16}\) |
| energy invariance | \(0\) |
| coherence-law error | \(6.890150\times10^{-16}\) |

For B7, five independently generated \(U(2)\) matrices and five independent Hermitian test matrices per unitary were used. The maximum relative defects were

\[
4.419409\times10^{-16}
\]

for the annihilation dissipators and

\[
4.372485\times10^{-16}
\]

for the creation dissipators.

### 34.8 B8 — shell-cutoff convergence

Pairwise observable convergence:

| Family | cutoff comparison | max occupation difference | max purity difference | max trace distance |
|---|---:|---:|---:|---:|
| B2 heating | \(8\to12\) | \(2.585477\times10^{-5}\) | \(1.289414\times10^{-6}\) | \(3.679206\times10^{-6}\) |
| B2 heating | \(12\to16\) | \(7.274142\times10^{-8}\) | \(1.409345\times10^{-9}\) | \(7.714975\times10^{-9}\) |
| B3 relaxation | \(8\to12\) | \(8.723495\times10^{-5}\) | \(7.753737\times10^{-6}\) | \(1.340338\times10^{-5}\) |
| B3 relaxation | \(12\to16\) | \(2.766283\times10^{-7}\) | \(1.486500\times10^{-8}\) | \(2.889802\times10^{-8}\) |

High-resolution top-shell and exact augmented-generator overflow values:

| Case | \(N\) | maximum top-shell population | exact final overflow |
|---|---:|---:|---:|
| B2 heating | 8 | \(1.327311\times10^{-5}\) | \(6.168431\times10^{-5}\) |
| B2 heating | 12 | \(2.888132\times10^{-8}\) | \(1.575639\times10^{-7}\) |
| B2 heating | 16 | \(5.692853\times10^{-11}\) | \(3.485558\times10^{-10}\) |
| B3 relaxation | 8 | \(4.917239\times10^{-5}\) | \(2.923544\times10^{-4}\) |
| B3 relaxation | 12 | \(1.073605\times10^{-7}\) | \(8.766370\times10^{-7}\) |
| B3 relaxation | 16 | \(2.194929\times10^{-10}\) | \(2.212088\times10^{-9}\) |

Therefore:

- \(N=8\) is insufficient for the declared \(10^{-6}\) overflow target;
- \(N=12\) passes for the frozen bath-only cases;
- \(N=16\) is substantially safer;
- top-shell population and overflow improve monotonically.

The solver's 101-point B3, \(N=12\) overflow was

\[
8.766298721596334\times10^{-7},
\]

while the exact augmented-generator result was

\[
8.766369798855872\times10^{-7}.
\]

Their difference,

\[
7.107726\times10^{-12},
\]

shows that the PASS is not an artifact of the 101-point quadrature.

The acceptance of \(N=12\) applies only to this bath-only certification suite. It must not be inherited automatically after the spinor detector is introduced, because detector-present evolution can populate higher shells.

## 35. Complete Stage-03 solver acceptance and outputs

### 35.1 Complete 32-gate table

| Gate | Value | Criterion | Decision |
|---|---:|---|---|
| `B0_ground_stationarity` | \(1.110223e-16\) | `<= 1.000e-12` | **PASS** |
| `B1_one_quantum_decay` | \(2.220446e-16\) | `<= 1.000e-11` | **PASS** |
| `B1_xy_isotropy` | \(0.000000e+00\) | `<= 1.000e-12` | **PASS** |
| `B2_B3_infinite_law_within_declared_overflow_bound` | \(-4.999827e-11\) | `<= 0` | **PASS** |
| `B2_B3_projected_occupation_reference` | \(4.607426e-15\) | `<= 1.000e-11` | **PASS** |
| `B2_B3_projected_population_reference` | \(8.024080e-15\) | `<= 1.000e-11` | **PASS** |
| `B4_projected_detailed_balance` | \(6.661340e-16\) | `<= 1.000e-12` | **PASS** |
| `B4_projected_gibbs_generator_stationarity` | \(1.406763e-17\) | `<= 1.000e-12` | **PASS** |
| `B4_projected_gibbs_propagated_stationarity` | \(3.439279e-16\) | `<= 1.000e-12` | **PASS** |
| `B5_coherent_amplitude_absolute_error` | \(1.081089e-07\) | `<= 1.000e-06` | **PASS** |
| `B5_coherent_amplitude_within_projected_residual_bound` | \(1.285473e-16\) | `<= 5.000e-11` | **PASS** |
| `B5_coherent_projected_residual_reconstruction` | \(1.167759e-11\) | `<= 5.000e-11` | **PASS** |
| `B6_dephasing_coherence_law` | \(6.890150e-16\) | `<= 1.000e-12` | **PASS** |
| `B6_dephasing_energy_invariant` | \(0.000000e+00\) | `<= 1.000e-12` | **PASS** |
| `B6_dephasing_population_invariants` | \(1.665335e-16\) | `<= 1.000e-12` | **PASS** |
| `B7_isotropic_basis_invariance` | \(4.419409e-16\) | `<= 1.000e-12` | **PASS** |
| `B8_cutoff_occupation_N12_to_N16` | \(2.766283e-07\) | `<= 1.000e-06` | **PASS** |
| `B8_cutoff_purity_N12_to_N16` | \(1.486500e-08\) | `<= 1.000e-07` | **PASS** |
| `B8_cutoff_trace_distance_N12_to_N16` | \(2.889802e-08\) | `<= 1.000e-07` | **PASS** |
| `B8_occupation_trace_distance_consistency` | \(0.000000e+00\) | `<= 5.000e-12` | **PASS** |
| `B8_overflow_monotonic_improvement` | \(0.000000e+00\) | `<= 1.000e-13` | **PASS** |
| `B8_production_overflow` | \(8.766299e-07\) | `<= 1.000e-06` | **PASS** |
| `B8_production_top_shell` | \(1.073352e-07\) | `<= 1.000e-06` | **PASS** |
| `B8_top_shell_monotonic_improvement` | \(0.000000e+00\) | `<= 1.000e-13` | **PASS** |
| `column_major_vectorization` | \(1.884938e-16\) | `<= 1.000e-12` | **PASS** |
| `density_hermiticity` | \(0.000000e+00\) | `<= 1.000e-12` | **PASS** |
| `density_positivity` | \(0.000000e+00\) | `>= -1.000e-11` | **PASS** |
| `generator_hermiticity_preservation` | \(3.898133e-17\) | `<= 1.000e-12` | **PASS** |
| `liouvillian_trace_preserving_row` | \(4.996004e-16\) | `<= 1.000e-12` | **PASS** |
| `operator_identities` | \(1.598721e-14\) | `<= 1.000e-12` | **PASS** |
| `projected_event_intensity_formula` | \(3.885781e-16\) | `<= 1.000e-12` | **PASS** |
| `trace_preservation` | \(1.043610e-14\) | `<= 1.000e-12` | **PASS** |

Thus

\[
\boxed{
\text{Stage-03 solver acceptance}=32/32.
}
\]

### 35.2 Solver outputs

The fixed solver products are

```text
03_bath_only_fock_test.py
Stage03_configuration.json
Stage03_operator_audit.json
Stage03_case_metrics.csv
Stage03_time_series.npz
Stage03_cutoff_metrics.csv
Stage03_acceptance.json
Stage03_solver_audit.json
Stage03_output_hashes.json
Stage03_run_status.json
solver_stdout.txt
solver_log.txt
```

The two additional high-quality cutoff audits are

```text
Stage03_exact_augmented_overflow_audit.json
Stage03_highres_population_10001point_audit.json
```

The cluster/laptop command is

```bash
OUTDIR=[ARCHIVE_PATH] \
python 03_bath_only_fock_test.py
```

or equivalently

```bash
python 03_bath_only_fock_test.py \
    --out-root [ARCHIVE_PATH]
```

The fixed result directory is

```text
[ARCHIVE_PATH]
```

### 35.3 Exact scientific meaning of the PASS

Stage 03 establishes, for the declared finite projected model and frozen B0--B8 suite, that:

1. the complete-shell operators and Liouvillian use the intended ordering and vectorization;
2. the bath is trace preserving;
3. Hermiticity and positivity are preserved without clipping or renormalization;
4. zero-temperature damping leaves the transverse ground state stationary;
5. one-quantum damping follows the exact exponential law;
6. thermal heating and relaxation agree with an independent projected population generator;
7. the consistently projected Gibbs state is stationary;
8. projected equilibrium upward and downward event intensities balance;
9. coherent displacement decays with the expected damping and phase, with the finite-shell residual explicitly controlled;
10. independent number dephasing preserves populations and energy while reproducing the coherence-decay law;
11. the isotropic amplitude channel is invariant under unitary rotations of the degenerate \(x/y\) basis;
12. \(N=12\) is sufficient for these specific bath-only cases at the declared cutoff tolerance.

Stage 03 does **not** establish:

- a scalar or spinor click-time response;
- an environmental susceptibility;
- detector-generated transverse excitation;
- the sign or magnitude of any bath-induced arrival-time change;
- the adequacy of \(N=12\) after the spinor boundary is active.


### 35.4 Independent handoff status

The independent-loader condition formerly listed here as pending has been satisfied by Audit 04. Audit 03 remains the solver-level record; Audit 04 is the independent verification record. The acceptance of \(N=12\) remains restricted to the detector-free B0--B8 suite and must be reconverged in Task 05 once the spinor boundary is active.

---


# Part VII — Completed Audit 04 independent bath-only loader

## 36. Scope and final status

Audit 04 is the independent loader/auditor for Audit 03. Its source is

```text
04_bath_only_fock_loader.py
```

and it uses the same fixed directory

```text
4060.Bath_only_tests
```

The loader does not import the Audit-03 solver, does not accept the solver's PASS flag as evidence, does not rerun the full density-matrix propagation, and contains no detector, longitudinal coordinate, GMRES solve, positivity clipping, trace renormalization, or Monte Carlo simulation.

Its final decision is

\[
\boxed{\text{Audit 04: PASS — 32/32 independent refined gates.}}
\]

It also reconstructed the solver-equivalent acceptance table and obtained 32/32 PASS with complete criterion and PASS/FAIL agreement.

## 37. Independent provenance, schema, and reconstruction audit

The principal infrastructure results are:

| Audit | Independent result |
|---|---:|
| stable Audit-03 files verified | 8/8 |
| frozen configuration and internal configuration hash | PASS |
| copied solver source and source guards | PASS |
| forbidden CuPy/CUDA imports | none |
| GMRES call in bath-only solver | absent |
| positivity-clipping calls | absent |
| exact NPZ schema | 437 keys, PASS |
| basis labels and order | PASS |
| global time grid | PASS |
| all stored numeric arrays finite | PASS |
| case-table comparison | 13 rows, 380 nonempty fields, 0 mismatches |
| maximum case-table numerical difference | \(3.330670\times10^-16\) |
| cutoff-table comparison | 10 rows, 150 nonempty fields, 0 mismatches |
| maximum cutoff-table numerical difference | \(0\) |
| operator-JSON maximum difference | \(2.822246\times10^-18\) |
| maximum independent population-curve error | \(7.382983\times10^-15\) |
| maximum initial-density reconstruction error | \(0\) |
| maximum final-density reconstruction error | \(6.661338\times10^-16\) |
| fresh random operator/isotropy audit | PASS |
| exact augmented-overflow reconstruction | PASS |

The loader independently rebuilt the complete-shell bases, ladder and number operators, Hamiltonians, Liouvillian actions, population generators, Gibbs state, coherent-state control, dephasing control, isotropic basis rotations, cutoff comparisons, top-shell diagnostics, and overflow integrals.

## 38. Complete independent 32-gate table

| Gate | Independent value | Criterion | Decision |
|---|---:|---|---|
| `operator_identities` | \( 1.598721155460e-14 \) | `<= 1.000e-12` | **PASS** |
| `liouvillian_trace_preserving_row` | \( 4.996003610813e-16 \) | `<= 1.000e-12` | **PASS** |
| `column_major_vectorization` | \( 1.913160462302e-16 \) | `<= 1.000e-12` | **PASS** |
| `generator_hermiticity_preservation` | \( 3.908443246113e-17 \) | `<= 1.000e-12` | **PASS** |
| `trace_preservation` | \( 1.043609643148e-14 \) | `<= 1.000e-12` | **PASS** |
| `density_hermiticity` | \( 0.000000000000e+00 \) | `<= 1.000e-12` | **PASS** |
| `density_positivity` | \( 0.000000000000e+00 \) | `>= -1.000e-11` | **PASS** |
| `projected_event_intensity_formula` | \( 3.885780586188e-16 \) | `<= 1.000e-12` | **PASS** |
| `B0_ground_stationarity` | \( 1.110223024625e-16 \) | `<= 1.000e-12` | **PASS** |
| `B1_one_quantum_decay` | \( 2.220446049250e-16 \) | `<= 1.000e-11` | **PASS** |
| `B1_xy_isotropy` | \( 0.000000000000e+00 \) | `<= 1.000e-12` | **PASS** |
| `B2_B3_projected_population_reference` | \( 8.024080429950e-15 \) | `<= 1.000e-11` | **PASS** |
| `B2_B3_projected_occupation_reference` | \( 4.607425552194e-15 \) | `<= 1.000e-11` | **PASS** |
| `B2_B3_infinite_law_within_declared_overflow_bound` | \( -4.999826945336e-11 \) | `<= 0` | **PASS** |
| `B4_projected_gibbs_generator_stationarity` | \( 1.406763150647e-17 \) | `<= 1.000e-12` | **PASS** |
| `B4_projected_gibbs_propagated_stationarity` | \( 3.439278626562e-16 \) | `<= 1.000e-12` | **PASS** |
| `B4_projected_detailed_balance` | \( 3.330669868410e-16 \) | `<= 1.000e-12` | **PASS** |
| `B5_coherent_amplitude_absolute_error` | \( 1.081089232170e-07 \) | `<= 1.000e-06` | **PASS** |
| `B5_coherent_amplitude_within_projected_residual_bound` | \( 1.285472980708e-16 \) | `<= 5.000e-11` | **PASS** |
| `B5_coherent_projected_residual_reconstruction` | \( 1.167759113530e-11 \) | `<= 5.000e-11` | **PASS** |
| `B6_dephasing_population_invariants` | \( 1.665334536938e-16 \) | `<= 1.000e-12` | **PASS** |
| `B6_dephasing_energy_invariant` | \( 0.000000000000e+00 \) | `<= 1.000e-12` | **PASS** |
| `B6_dephasing_coherence_law` | \( 6.890150443143e-16 \) | `<= 1.000e-12` | **PASS** |
| `B7_isotropic_basis_invariance` | \( 4.392848978485e-16 \) | `<= 1.000e-12` | **PASS** |
| `B8_cutoff_occupation_N12_to_N16` | \( 2.766282998223e-07 \) | `<= 1.000e-06` | **PASS** |
| `B8_cutoff_purity_N12_to_N16` | \( 1.486500011971e-08 \) | `<= 1.000e-07` | **PASS** |
| `B8_cutoff_trace_distance_N12_to_N16` | \( 2.889801573192e-08 \) | `<= 1.000e-07` | **PASS** |
| `B8_occupation_trace_distance_consistency` | \( 0.000000000000e+00 \) | `<= 5.000e-12` | **PASS** |
| `B8_production_top_shell` | \( 1.073604688778e-07 \) | `<= 1.000e-06` | **PASS** |
| `B8_production_overflow` | \( 8.766369798856e-07 \) | `<= 1.000e-06` | **PASS** |
| `B8_top_shell_monotonic_improvement` | \( 0.000000000000e+00 \) | `<= 1.000e-13` | **PASS** |
| `B8_overflow_monotonic_improvement` | \( 0.000000000000e+00 \) | `<= 1.000e-13` | **PASS** |

Thus

\[
\boxed{
\text{independent refined acceptance}
=
\text{solver-equivalent acceptance}
=
32/32.
}
\]

## 39. Exact finite-shell refinement

| Case | 101-point overflow | Exact augmented overflow | High-resolution maximum top-shell population |
|---|---:|---:|---:|
| B2_N8 | \( 6.168478719806e-05 \) | \( 6.168431463015e-05 \) | \( 1.327311440532e-05 \) |
| B2_N12 | \( 1.575661560626e-07 \) | \( 1.575638973169e-07 \) | \( 2.888131964117e-08 \) |
| B2_N16 | \( 3.485636200801e-10 \) | \( 3.485558363392e-10 \) | \( 5.692853490074e-11 \) |
| B3_N8 | \( 2.923529754022e-04 \) | \( 2.923544400640e-04 \) | \( 4.917239421807e-05 \) |
| B3_N12 | \( 8.766298721596e-07 \) | \( 8.766369798856e-07 \) | \( 1.073604688778e-07 \) |
| B3_N16 | \( 2.212063755170e-09 \) | \( 2.212088468510e-09 \) | \( 2.194928752653e-10 \) |

The tightest production-shell value remains the B3, \(N=12\) relaxation case:

\[
\boxed{
\epsilon_{\mathrm{overflow}}^{\mathrm{B3},N=12}(20)
=
8.766369798855872\times10^{-7}
<10^{-6}.
}
\]

The independently refined maximum top-shell population is

\[
\max_t p_{\mathrm{top}}^{\mathrm{B3},N=12}(t)
=
1.073604688777540\times10^{-7}
<10^{-6}.
\]

The difference between the exact augmented overflow and the stored 101-point trapezoidal value is only

\[
7.107726\times10^-12
\]

for the tightest production case. The PASS is therefore not a sampling artifact.

## 40. Determinism, resource use, and adversarial tests

The verified package records two clean executions:

| Execution | Exit | Wall time | Peak resident memory |
|---|---:|---:|---:|
| clean run 1 | 0 | 15.29 s | 187,972 KiB |
| same-directory run 2 | 0 | 15.12 s | 187,436 KiB |

All stable loader products were bit-for-bit identical on the second run. The loader also executed successfully from inside the fixed result directory without deleting or altering its own source.

A fresh re-execution performed while preparing this master update returned

```text
exit = 0
independent gates = 32/32
wall time = 15.43 s
peak resident memory = 188,224 KiB
```

Two negative integrity tests also passed:

1. **Simple file tamper:** modifying `Stage03_case_metrics.csv` without updating the hash manifest caused exit status 1, stale PASS products were removed, and a failure record was written.
2. **Coordinated file-and-manifest tamper:** modifying a B0 metric and updating the manifest to hide the file hash change still caused exit status 2 because the independent numerical reconstruction detected the false metric.

The loader therefore protects against both ordinary stale-file corruption and a coordinated stored-result/manifest alteration.

## 41. Audit-04 outputs, hashes, and final decision

Authoritative source and package:

```text
04_bath_only_fock_loader.py
cf0246ee8767dbb8862d637a4225952c9625392281d3856a616e69fea22c7d9c

Task04_Stage03_Independent_Loader_Verified_2026-08-03.zip
0a658b07e6f32d292dce658b9288d196070c7b745db099622306fac7676e11a7
```

Stable loader products:

```text
Stage03_bath_only_report.md
52e73ce0c55c623091a0a96425b79d08ca0e8e3097cfc127aa2ded0d193a7e31

Stage03_loader_audit.json
d44c429c4a5fe42cfdd0c1ccd8884fb6eaf422423869ad64032171172b3df69b

Stage03_loader_case_metrics.csv
ef105a722872716267d7ee8ac3c48dd70af7d3922960916fa3d603bb0d243b01

Stage03_loader_cutoff_metrics.csv
24022372f499bedc7248e93d6bd02ad01d49818f38ae1fa563d269c14feb6744
```

Additional fixed products inside the verified package are

```text
Stage03_loader_output_hashes.json
Stage03_loader_run_status.json
loader_stdout.txt
loader_log.txt
Task04_development_verification.json
```

The exact scientific decision is

\[
\boxed{
\begin{aligned}
&\text{Audit 03 solver is closed for B0--B8.}\\
&\text{Audit 04 independently reproduces and verifies that closure.}\\
&\text{The detector-free bath branch is fully closed.}\\
&\text{The value }N=12\text{ is not inherited automatically by detector-present dynamics.}
\end{aligned}
}
\]

---


# Part VIII — Task 05 oscillator-channel detector solver and source diagnostics

## 42. Exact purpose and scope

Task 05 is the next implementation. It joins the already certified longitudinal detector core to the already certified complete-shell oscillator representation, but it remains **zero bath**. It has three purposes:

1. recover the scalar and spinor zero-bath detector laws in a coupled-channel one-dimensional representation;
2. resolve the known scalar finite-step artifact through an authoritative factorized scalar map and a separate monolithic-Cayley diagnostic;
3. determine when the detector-present spinor evolution generates the transverse excitation and number-basis structure on which the later downward and dephasing channels can act.

Task 05 does not yet propagate a Lindblad density matrix and does not yet calculate an environmental susceptibility. Its PASS is the final representation/control gate before the response phase.

The intended source is

```text
05_oscillator_channel_detector_test.py
```

with fixed output directory

```text
4070.Oscillator_channel_detector_tests
```

The script should retain the user's explicit manual configuration style: detector, mode, \(\omega\), shell cutoff, time step, horizon, and case prefix are edited in one frozen parameter block. No timestamped or automatically parameter-generated directory is permitted. Re-running one case intentionally replaces only files with that explicit case prefix.

## 43. Finite coupled-channel representation

Use the complete-shell orbital basis

\[
\mathcal I_N=\{(n_x,n_y):n_x+n_y\le N\},
\qquad
M_N=\frac{(N+1)(N+2)}2,
\]

and include physical spin explicitly. The channel dimension is

\[
d_N=2M_N.
\]

Freeze the vector ordering as

\[
\operatorname{index}(s,\mu,k_z)
=
\bigl(sM_N+\mu\bigr)N_z+k_z,
\]

so that \(z\) is the fastest index, followed by oscillator channel and then physical spin. This matches the spin-major, \(z\)-fast logic of the established Cartesian code.

The longitudinal matrix `L_z` is copied from the validated detector solver, with the same bottom Dirichlet condition and scalar roof term. The transverse Hamiltonian is

\[
H_{\perp,N}=\omega(N_x^{(N)}+N_y^{(N)}+I),
\qquad
H_{\perp,N}^{\rm spin}=I_2\otimes H_{\perp,N}.
\]

The spin--momentum matrix \(K_N\) is reconstructed from the Audit-02 complete-shell operators and checked against the frozen Audit-02 identities before propagation.

Let

\[
P_R=|z_{\rm roof}\rangle\langle z_{\rm roof}|.
\]

The scalar monolithic Hamiltonian is

\[
H_{{\rm sc},N}^{\rm mono}
=
I_{d_N}\otimes L_z
+
H_{\perp,N}^{\rm spin}\otimes I_z.
\]

The spinor Hamiltonian is

\[
H_{{\rm s},N}
=
I_{d_N}\otimes L_z
+
H_{\perp,N}^{\rm spin}\otimes I_z
+
\frac{1}{2h_z}K_N\otimes P_R.
\]

The sign of the final term is load-bearing. It follows from

\[
\partial_z u=(i\kappa I-K_N)u,
\]

because the scalar `L_z` already contributes \(-i\kappa/(2h_z)\) at the roof and the reactive correction therefore enters as \(+K_N/(2h_z)\). This is the oscillator-channel counterpart of the established Cartesian roof matrix `C`.

## 44. Three finite-step propagators and probability accounting

Task 05 must keep three logically distinct maps.

### 44.1 Authoritative factorized scalar map

Use

\[
U_{{\rm sc},h}^{\rm fact}
=
\exp[-ihH_{\perp,N}^{\rm spin}]
\otimes
U_{z,h}^{\rm nc},
\]

where \(U_{z,h}^{\rm nc}\) is the validated longitudinal scalar-ABC Cayley step. The transverse factor is exactly unitary and trace preserving. Therefore the scalar click-time marginal is exactly mode independent at finite \(h\), up to linear-solver and floating-point error.

### 44.2 Monolithic scalar diagnostic

Also propagate

\[
U_{{\rm sc},h}^{\rm mono}
=
\left(I+\frac{ih}{2}H_{{\rm sc},N}^{\rm mono}\right)^{-1}
\left(I-\frac{ih}{2}H_{{\rm sc},N}^{\rm mono}\right).
\]

This map is not the authoritative scalar control. It exists only to reproduce the known finite-step mode artifact and verify its expected \(O(h^2)\) reduction under time-step halving.

### 44.3 Spinor coupled-channel map

Use the full Cayley step

\[
U_{{\rm s},h}
=
\left(I+\frac{ih}{2}H_{{\rm s},N}\right)^{-1}
\left(I-\frac{ih}{2}H_{{\rm s},N}\right).
\]

The reference longitudinal/grid parameters are retained:

\[
N_z=1500,
\quad
L_z=20,
\quad
z_0=10,
\quad
\sigma_z=0.5,
\quad
k_0=\kappa=\pi,
\quad
\theta=\pi/6,
\quad
\phi=0.
\]

Use `complex128` for the state, sparse matrices, GMRES solve, and all reductions. No complex64 propagation is required in this reduced representation.

The norm is

\[
S_n=h_z\sum_{s,\mu,k}|\psi_{s\mu k}^{(n)}|^2.
\]

For the midpoint vector

\[
q_n=\frac{\psi_n+\psi_{n+1}^{\rm CN}}2,
\]

the roof-click probability is

\[
p_{D,n}
=
\Delta t\,\kappa
\sum_{s,\mu}|q_{n,s\mu}(z_{\rm roof})|^2.
\]

There is no \(h_xh_y\) factor because the transverse oscillator basis is orthonormal. The primary closure is

\[
S_0-S_N-\sum_{n=0}^{N-1}p_{D,n}.
\]

No detector probability may be obtained by differentiating a sampled survival curve.

## 45. Minimal required case matrix

The initial Task-05 campaign is deliberately finite and explicit.

### 45.1 Baseline recovery cases

At the Audit-01 time steps and horizon, run

\[
\omega\in\{1,100\},
\qquad
\text{modes }00,10,01,
\]

for

- authoritative factorized scalar propagation;
- spinor coupled-channel propagation;
- principal shell \(N=12\).

This gives twelve baseline recovery cases.

### 45.2 Scalar artifact diagnostic

At \(\omega=100\), modes 00 and 10, run the monolithic scalar map at

\[
\Delta t=5\times10^{-4},
\qquad
\Delta t=2.5\times10^{-4}.
\]

A third value \(1.25\times10^{-4}\) is added only if the first halving is not yet in the quadratic regime.

### 45.3 Spinor time-step refinement

At \(\omega=100\), modes 00 and 10, repeat the spinor calculation at

\[
\Delta t=2.5\times10^{-4}.
\]

### 45.4 Spinor shell convergence

At \(\omega=100\), modes 00 and 10, compare

\[
N=8,12,16
\]

at the common baseline time step. The \(N=12\) result is accepted only if the \(12\to16\) changes satisfy the declared curve and integrated-observable tolerances.

Each case is run manually with one explicit case prefix. The script must not loop over the production matrix automatically.

## 46. Scalar-control and detector-recovery gates

Task 05A passes only if all of the following hold.

### 46.1 Factorized scalar null

For each tested \(\omega\),

\[
d_{\rm TV}(\nu_{{\rm sc},10}^{\rm fact},\nu_{{\rm sc},00}^{\rm fact})
\le10^{-11},
\]

\[
d_{\rm TV}(\nu_{{\rm sc},01}^{\rm fact},\nu_{{\rm sc},00}^{\rm fact})
\le10^{-11},
\]

with corresponding survival and integrated-observable differences at the solver floor. This is the authoritative finite-step scalar null.

### 46.2 Monolithic scalar convergence

Let

\[
R_h=d_{\rm TV}(\nu_{{\rm sc},10}^{\rm mono,h},\nu_{{\rm sc},00}^{\rm mono,h}).
\]

The diagnostic should satisfy

\[
\frac{R_h}{R_{h/2}}\approx4
\]

within a predeclared practical band, initially \(3.5\le R_h/R_{h/2}\le4.5\). The monolithic residual is never interpreted as a physical scalar response.

### 46.3 Spinor recovery

For the spinor detector, compare with the Cartesian Audit-00/01 censored laws using

\[
S(t),\quad g(t),\quad D(T),\quad\mu^*(T),\quad D_E,\quad D_L,
\]

and pairwise total-variation distances. The oscillator-channel result must reproduce:

- the sign of every first-shell shift;
- the strong confinement enhancement;
- the prompt suppression and late-sector increase at \(\omega=100\);
- the \(10/01\) degeneracy at the numerical floor.

The representation discrepancy

\[
\epsilon_{\rm repr}
=
\text{Cartesian--oscillator difference at common physical inputs}
\]

must be reported separately from time-step and shell-cutoff errors. Agreement is accepted only when the observed discrepancy is bounded by the combined declared numerical error budget.

### 46.4 Core numerical integrity

For every case:

- GMRES return code is zero at every step;
- the maximum true relative residual is below the frozen tolerance;
- midpoint roof probabilities are nonnegative;
- cumulative boundary-clamp loss is zero;
- survival is nonincreasing within roundoff;
- roof/norm closure passes;
- all saved arrays are finite;
- repeated execution of one case in the same directory gives stable numerical hashes.

## 47. Shell diagnostics and direct boundary-truncation control

For the normalized surviving state

\[
\psi_{\rm nc}(t)=\frac{\psi(t)}{\sqrt{S(t)}},
\]

retain shell populations

\[
p_n^{\rm nc}(t),
\qquad
p_{\rm top}^{\rm nc}(t)=\langle\Pi_N\rangle_{\rm nc}.
\]

At minimum, require convergence of the complete censored law, \(D\), \(\mu^*\), \(D_E\), \(D_L\), and the source curves under \(N=12\to16\). A small top-shell population is necessary but not sufficient.

A useful direct omitted-boundary-coupling proxy is

\[
r_{K,\rm omit}(t)
=
\left\|Q_{N+1}K P_N\psi_\Sigma(t)\right\|^2,
\]

where \(Q_{N+1}\) selects the first omitted shell and \(\psi_\Sigma\) is the roof channel vector. Its accumulated integral should be stored as a truncation diagnostic. It is not a probability loss term and must not be added to the detector budget.

## 48. Detector-generated source diagnostics

Along \(\psi_{\rm nc}(t)\), calculate

\[
s_\downarrow(t)
=
\sum_{j=x,y}\|a_j\psi_{\rm nc}(t)\|^2
=
\langle N_\perp\rangle_{\rm nc}(t),
\]

\[
s_\uparrow^{(N)}(t)
=
\sum_{j=x,y}\|a_j^\dagger\psi_{\rm nc}(t)\|^2
=
\langle N_\perp+2\rangle_{\rm nc}
-(N+2)p_{\rm top}^{\rm nc}(t),
\]

and

\[
s_\phi(t)
=
\operatorname{Var}_{\rm nc}(N_x)
+
\operatorname{Var}_{\rm nc}(N_y).
\]

The exact launch controls for a transverse ground state are

\[
s_\downarrow(0)=0,
\qquad
s_\phi(0)=0,
\qquad
s_\uparrow(0)=2.
\]

For a factorized scalar ground-state evolution, \(s_\downarrow\) and \(s_\phi\) should remain at the solver floor. For spinor ground-state evolution, they vanish at launch but may become nonzero after the wave packet interacts with the spin--momentum boundary.

To prepare the later low-rank tangent implementation, also retain at selected insertion times the vectors

\[
a_j\psi_{\rm nc},
\quad
a_j^\dagger\psi_{\rm nc},
\quad
N_j\psi_{\rm nc},
\quad
a_j^\dagger a_j\psi_{\rm nc},
\quad
a_j a_j^\dagger\psi_{\rm nc},
\quad
N_j^2\psi_{\rm nc}.
\]

Only sparse selected-time products should be saved; full dense density matrices are prohibited.

## 49. Task-05 output contract and completion condition

For one explicit case prefix, save at minimum

```text
CASE_configuration.json
CASE_operator_audit.json
CASE_solver_audit.json
CASE_times.npy
CASE_survival.npy
CASE_step_loss_roof_midpoint.npy
CASE_shell_populations.npz
CASE_source_diagnostics.npz
CASE_run_status.json
CASE_output_hashes.json
```

The aggregate independent loader in Task 06 will write

```text
Task05_loader_audit.json
Task05_complete_case_metrics.csv
Task05_pairwise_curve_metrics.csv
Task05_cutoff_metrics.csv
Task05_detector_source_report.md
Task05_loader_output_hashes.json
```

Task 05 is not complete merely because one spinor curve looks reasonable. Its solver-level gate is

\[
\boxed{
\begin{aligned}
&\text{operator and roof-term reconstruction PASS},\\
&\text{factorized scalar null PASS},\\
&\text{monolithic scalar }O(h^2)\text{ diagnostic PASS},\\
&\text{spinor time-step and shell convergence PASS},\\
&\text{Cartesian--oscillator recovery audit PASS},\\
&\text{source launch identities and source curves PASS},\\
&\text{probability and linear-solver audits PASS}.
\end{aligned}
}
\]

Only after Task-05 solver PASS and Task-06 independent-loader PASS should the weak environmental susceptibility phase begin.

---

# Part IX — Subsequent weak environmental susceptibility phase

## 50. Tangent equation

For each environmental direction \(r\), solve

\[
\dot\sigma_{\alpha,r}
=
\mathcal L_{\alpha,0}[\sigma_{\alpha,r}]
+
\mathcal B_r[\widetilde\rho_\alpha^{(0)}(t)],
\qquad
\sigma_{\alpha,r}(0)=0.
\]

The detector responses are

\[
\chi_{S,\alpha r}(t)=\operatorname{Tr}\sigma_{\alpha,r}(t),
\]

\[
\chi_{g,\alpha r}(t)
=
\operatorname{Tr}[G_{D,\alpha}\sigma_{\alpha,r}(t)].
\]

The exact first-order probability budget is

\[
\chi_{S,\alpha r}(t)
+
\int_0^t\chi_{g,\alpha r}(u)\,du
=0.
\]

## 51. Required calculation order

\[
\text{scalar downward null}
\to
\text{spinor downward}
\to
\text{scalar upward null}
\to
\text{spinor upward}
\to
\text{independent number dephasing}.
\]

The cleanest first dynamical test is vacuum damping because

\[
\mathcal B_\downarrow[|00\rangle\langle00|]=0.
\]

Any nonzero spinor response then probes transverse structure generated or selected by detector-present evolution.

Upward excitation satisfies

\[
\mathcal B_\uparrow[|00\rangle\langle00|]
=
|10\rangle\langle10|
+
|01\rangle\langle01|
-2|00\rangle\langle00|,
\]

so it acts at launch and is directly connected to the Audit-01 first-shell coefficient.

## 52. Causal insertion kernel

Compute

\[
\chi_{g,\alpha r}(t)
=
\int_0^tK_{\alpha r}(t,s)\,ds.
\]

The times have different meanings:

- \(s\): environmental insertion time;
- \(t\): later detector-response time.

Do not identify them.

For the scalar factorized control,

\[
K_{\mathrm{sc},r}(t,s)=0
\]

pointwise, not merely after temporal cancellation.

## 53. Two independent implementations

### 53.1 Full tangent density matrix

Use a small common shell cutoff as the exact finite benchmark.

### 53.2 Low-rank wave-function insertion

For one dissipator \(\mathcal D[L]\), retain both

- the propagated jump term;
- the anticommutator term.

A jump-only insertion is not trace preserving and is invalid.

The low-rank and full tangent-density results must agree before production use.

## 54. Response-phase outputs and gates

Retain

\[
\chi_S(t),
\quad
\chi_g(t),
\quad
\chi_D,
\quad
\chi_\mu,
\quad
\chi_{D_E},
\quad
\chi_{D_L},
\]

and the insertion profile \(K(t,s)\).

Required gates:

- detector-only reference recovery;
- tangent probability closure;
- scalar susceptibilities converge to zero;
- kernel integration reproduces \(\chi_g\);
- low-rank and full tangent calculations agree;
- insertion quadrature converges;
- shell cutoff converges;
- any claimed nonzero response exceeds the total numerical uncertainty.

A susceptibility consistent with zero is a valid result.

---

# Part X — Subsequent small-positive-rate validation phase

## 55. Deterministic finite-rate map

Use the symmetric composition

\[
\rho_{n+1}
=
\Phi_{B,\Delta t/2}
\circ
\mathcal T^{\mathrm{nc}}_{D,\Delta t}
\circ
\Phi_{B,\Delta t/2}
[\rho_n].
\]

The bath half-steps are CPTP. The detector step is CP and trace non-increasing. The roof probability is assigned only during the detector substep.

## 56. Initial rate pair

The packet-centre flight scale is

\[
t_{\mathrm{fp}}^{\mathrm{cl}}
=\frac{10}{\pi}
\simeq3.18310.
\]

Candidate rates satisfying

\[
\epsilon t_{\mathrm{fp}}\simeq0.02,
\qquad
\epsilon t_{\mathrm{fp}}\simeq0.05
\]

are approximately

\[
\epsilon_1\simeq0.006283,
\qquad
\epsilon_2\simeq0.015708,
\]

provided that

\[
\epsilon\ll\omega
\]

and the cutoff-dependent activity condition is satisfied.

## 57. Linearity test

For the complete censored detector law, define

\[
R_\nu(\epsilon)
=
\int_0^T
|g_\epsilon-g_0-\epsilon\chi_g|\,dt
+
|S_\epsilon(T)-S_0(T)-\epsilon\chi_S(T)|.
\]

First-order consistency requires

\[
\frac{R_\nu(\epsilon)}{R_\nu(\epsilon/2)}
\longrightarrow4.
\]

Apply the same test to

\[
D,
\quad
\mu^*,
\quad
D_E,
\quad
D_L.
\]

Do not use negative rates. Quantum trajectories are secondary and begin only after deterministic finite-rate propagation agrees with the tangent result at a common cutoff.

---

# Part XI — Common parameter campaign, observables, and evidence standard

## 58. Confinement campaign

\[
\omega\in\{1,100,300\}.
\]

Development and full audit first at \(\omega=100\), check at \(\omega=1\), and extend to \(\omega=300\) only after the mechanism is numerically stable.

## 59. Preparation campaign

Use, in order:

1. \(|00\rangle\);
2. \(|10\rangle\), \(|01\rangle\);
3. Gibbs preparation with \(\bar n_{\mathrm{prep}}=0.25\), so \(q=0.2\);
4. \(\bar n_{\mathrm{prep}}=1\) only after cutoff feasibility;
5. do not begin with \(\bar n_{\mathrm{prep}}=3\).

## 60. Observation horizons

Use

\[
T=10
\]

for implementation and mechanism development.

Use

\[
T=20
\]

for production detector statistics after the implementation is stable. Use \(T=40\) only when the delayed response remains unresolved at \(T=20\).

## 61. Required detector observables

For every detector calculation retain

\[
S(t),
\quad
p_{D,n},
\quad
g(t_{n+1/2})=p_{D,n}/\Delta t,
\]

\[
D(T)=1-S(T),
\quad
\mu^*(T)=\int_0^TS(t)\,dt,
\]

\[
D_E=\sum_{t_{n+1/2}<3.6}p_{D,n},
\quad
D_L=\sum_{t_{n+1/2}\ge3.6}p_{D,n},
\]

\[
w_L=\frac{D_L}{D_E+D_L}.
\]

For two censored laws use

\[
d_{\mathrm{TV}}^{(T)}
=
\frac12
\left[
\int_0^T|g_1-g_2|\,dt
+
|S_1(T)-S_2(T)|
\right],
\]

and

\[
W_1^{(T)}
=
\int_0^T|S_1(t)-S_2(t)|\,dt.
\]

Agreement of one integrated statistic is insufficient.

## 62. Numerical error budget

Track separately

\[
\epsilon_{\mathrm{tot}}
\le
\epsilon_{\mathrm{repr}}
+
\epsilon_z
+
\epsilon_{\Delta t}
+
\epsilon_N
+
\epsilon_{\mathrm{init}}
+
\epsilon_{s\text{-quad}}
+
\epsilon_{\mathrm{solve}}
+
\epsilon_{\mathrm{lin}}
+
\epsilon_{\mathrm{MC}}.
\]

Here:

- \(\epsilon_{\mathrm{repr}}\): Cartesian versus oscillator-channel representation;
- \(\epsilon_z\): longitudinal discretization;
- \(\epsilon_{\Delta t}\): time-step and phase-resolution error;
- \(\epsilon_N\): dynamical shell cutoff;
- \(\epsilon_{\mathrm{init}}\): initial Gibbs tail;
- \(\epsilon_{s\text{-quad}}\): insertion-time quadrature;
- \(\epsilon_{\mathrm{solve}}\): direct or Krylov solver;
- \(\epsilon_{\mathrm{lin}}\): neglected nonlinear rate terms;
- \(\epsilon_{\mathrm{MC}}\): trajectory sampling, zero for deterministic tangent calculations.

For a stable quantitative claim, use the provisional evidentiary condition

\[
|\Delta O|\ge5\epsilon_{\mathrm{tot}}.
\]

The factor five is a predeclared evidence convention, not a theorem.

---


# Part XII — File, directory, and sharing policy

## 63. Current and recommended script map

```text
Audit 00
    reference-regression Cartesian detector line

Audit 01 — complete
    static-mode Cartesian solvers and loader
    current review archive: Stage01_static_mode(1).zip

Audit 02 — complete
    4050_bath_operator_tests_solver.py
    4051_bath_operator_tests_loader.py
    fixed directory: 4050.Bath_operator_tests

Audit 03 — complete solver
    03_bath_only_fock_test.py
    fixed directory: 4060.Bath_only_tests

Audit 04 — complete independent loader
    04_bath_only_fock_loader.py
    same fixed directory: 4060.Bath_only_tests

Task 05 — immediate next solver
    05_oscillator_channel_detector_test.py
    fixed directory: 4070.Oscillator_channel_detector_tests

Task 06 — independent Task-05 loader
    06_oscillator_channel_detector_loader.py
    same fixed directory: 4070.Oscillator_channel_detector_tests

Subsequent susceptibility phase
    07_environmental_response_solver.py
    08_environmental_response_loader.py

Subsequent finite-rate phase
    09_finite_rate_validation_solver.py
    10_finite_rate_validation_loader.py
```

The former `Stage 01C` label is retired. Its scientifically necessary content is Task 05A.

## 64. Directory policy

Preserve the current explicit style:

- one manually fixed stage directory;
- no timestamps;
- no automatic parameter-generated path;
- rerunning the same stage reuses the same directory;
- one manually declared case prefix prevents different cases from overwriting one another;
- rerunning the same case intentionally replaces only that case's products;
- never infer physics from a folder name when configuration metadata exists.

## 65. Solver/loader separation

For every stage:

- the solver constructs or propagates and saves raw outputs plus indispensable numerical audits;
- the loader does not repeat the full propagation and independently verifies hashes, configurations, metrics, convergence, and acceptance;
- the loader must not trust the solver PASS flag;
- scientific reductions and plots belong to the loader;
- stale-loader products must be invalidated whenever solver products change.

## 66. Minimal sharing protocol

For one successful detector run, retain/share:

```text
CASE_configuration.json
CASE_solver_audit.json
CASE_times.npy
CASE_survival.npy
CASE_step_loss_roof_midpoint.npy
CASE_source_diagnostics.npz
```

For a completed audit, retain/share:

```text
stage summary JSON
case-metrics CSV
convergence CSV
compact derived NPZ
principal scientific plot
principal numerical-validation plot
source and output hash manifests
independent loader report
```

Do not routinely share checkpoints, full logs, or duplicate arrays unless an anomaly occurs.

---

# Part XIII — Immediate action checklist

## 67. Actions already complete

- Audit-00 reference calculations archived.
- Audit-01 full twelve-case zero-bath archive re-inspected and confirmed complete for its declared scope.
- Audit-01 scalar \(\omega=100\) finite-step artifact identified and correctly classified as numerical, not physical.
- Audit-02 solver and independent loader passed 22/22 gates.
- Audit-03 detector-free bath solver passed 32/32 gates.
- Audit-03 deterministic same-directory rerun passed with identical stable hashes.
- Audit-03 exact augmented-overflow and 10,001-point population audits passed.
- Audit-04 independent loader compiled and executed cleanly.
- Audit-04 verified 8/8 stable Audit-03 files.
- Audit-04 independently passed 32/32 refined gates.
- Audit-04 reproduced all solver criteria and PASS/FAIL decisions.
- Audit-04 simple and coordinated tamper tests passed.
- Audit-04 package re-execution during this update again returned exit 0 and 32/32.
- The detector-free bath branch is closed.

## 68. Next work — Task 05 only

1. Freeze the manual parameter block, ordering, and fixed directory in `05_oscillator_channel_detector_test.py`.
2. Reconstruct `L_z`, \(H_{\perp,N}\), and \(K_N\) independently and audit the roof-term sign.
3. Implement the authoritative factorized scalar map.
4. Implement the monolithic scalar diagnostic and time-step-halving test.
5. Implement the spinor coupled-channel Cayley/GMRES propagation.
6. Run the twelve baseline scalar-factorized/spinor recovery cases.
7. Run the scalar and spinor time-step refinements at \(\omega=100\).
8. Run \(N=8,12,16\) spinor cutoff checks for modes 00 and 10.
9. Save shell populations and detector-generated downward, upward, and dephasing source diagnostics.
10. Freeze solver outputs and hashes for the independent Task-06 loader.

No active Lindblad bath is added in Task 05.

---

# Part XIV — Current authoritative decision statement

The numerical programme now has two closed foundations and one precisely defined next implementation.

First, the full Audit-01 archive is present and complete for its twelve zero-bath Cartesian cases. It establishes the confinement-enhanced spinor preparation response and the prompt-to-return restructuring at \(\omega=100\). The archive also exhibits the known monolithic-Cayley scalar artifact. That artifact does not make the archive incomplete; it defines a control that must be resolved in the next representation.

Second, the detector-free bath branch is fully closed. Audit 02 certifies the oscillator operators and \(K\). Audit 03 certifies the finite projected GKSL solver. Audit 04 independently reconstructs the full B0--B8 audit, verifies all stable hashes, reproduces 32/32 gates, refines the tightest overflow value, and rejects both ordinary and coordinated tampering.

The tightest bath-only result is

\[
\epsilon_{\mathrm{overflow}}^{\mathrm{B3},N=12}(20)
=
8.766369798855872\times10^{-7}<10^{-6}.
\]

Therefore:

\[
\boxed{
\begin{aligned}
&\text{Audit 01 is complete for its declared twelve-case scope.}\\
&\text{The former Stage-01C label is retired; its control is Task 05A.}\\
&\text{Audit 02 is closed.}\\
&\text{Audit 03 solver is closed for B0--B8.}\\
&\text{Audit 04 independent loader is closed.}\\
&\text{The detector-free bath branch is fully certified.}\\
&\text{Task 05 is authorized and is the only immediate next implementation.}\\
&\text{No detector--bath physical response has yet been calculated.}
\end{aligned}
}
\]

The next scientifically meaningful result is not a broad finite-temperature scan. It is a controlled oscillator-channel recovery and source audit that establishes:

1. an exact finite-step scalar null;
2. controlled spinor time-step and shell convergence;
3. quantitative Cartesian--oscillator representation error;
4. when detector-present evolution activates downward and dephasing source directions;
5. the insertion-time support needed for the later susceptibility calculation.

---

## Appendix A — Stage-02 final fingerprints

```text
Stage02_bath_operator_tests_audited_2026-08-02.zip
30525cd27cc545941b89ad77daf4cdb904ffa51e45e0f64839951a6d834a7a8c

4050_bath_operator_tests_solver.py
2ed0daf88dca64d33896d42e53d93c1e57b85d7e22391498babd4f7588b273b2

4051_bath_operator_tests_loader.py
398a66b51c21e72216da38ef446c4e0e0012b0c23e2d6114b12b19e54e4bfc0b
```

## Appendix B — Stage-02 minimal confirmation command

After running the solver and loader, the decisive conditions are:

```text
solver return code = 0
loader return code = 0
Stage02_run_status.json: completed and all_checks_passed = true
Stage02_acceptance.json: PASS
Stage02_loader_audit.json: PASS
all hashes match = true
independent acceptance = PASS
solver/loader comparisons = PASS
```

No additional Stage-02 parameter sweep is required.

## Appendix C — Frozen project rules

1. Do not alter the established spinor Hamiltonian, roof matrix `C`, scalar/spinor ABC construction, CN matrices, GMRES solve, or post-solve boundary enforcement without a separate regression.
2. The direct ABC remains the only detector.
3. The ambient bath is trace preserving and cannot be inserted as another loss term.
4. Solver and loader remain separate.
5. Every detector comparison uses identical longitudinal packet, spin, geometry, and horizon.
6. Integrated detector probabilities use midpoint step losses.
7. A scalar response is numerical error until factorization and convergence prove otherwise.
8. A susceptibility consistent with zero is a valid physical result.
9. Finite-shell formulas must include the top-shell projection correction.
10. No trajectory calculation begins before the deterministic tangent and finite-rate maps pass.
11. Stage-03 acceptance of \(N=12\) is restricted to the frozen bath-only B0--B8 suite and must not be inherited automatically by detector-present calculations.
12. Audit 04 is now complete; future solver stages still require an independent loader before their branch is closed.

## Appendix D — Stage-03 final fingerprints

```text
03_bath_only_fock_test.py
5e621ee346604d8eef4765c07532ab3b525783af2b9a52d80fa408ef38c65bbe

Stage03_full_CPU_certification_results.zip
469177671f683277ea1352d04ab476946bf249d6c4cc5308f202b445df11df0c

Stage03_acceptance.json
6d90ee8db963a189471a9c7d099648244631fcaaf7269a7735e6b3ae3bc24b9a

Stage03_case_metrics.csv
bbe3468f86e90c8ceee414545b3b47ad65963fba848d66ec7742cb3564ed0dba

Stage03_cutoff_metrics.csv
cee67aac556bfa9269ced31c3d666da66ce2d3d15fa708846adb73498742415a

Stage03_time_series.npz
fe1a591de7c33fc8432888a4a36bb67c3798ee6328012df590628659eb8daa14

Stage03_exact_augmented_overflow_audit.json
e5dead4c707a4b95a34d1a4345afd8cfd41c154f7a6478def9551ac5f9a13db4

Stage03_highres_population_10001point_audit.json
e3e6b4451f4b360a3fd1be729af34fb9cd934ab1e96b40765e34403e262eef4e
```


## Appendix E — Audit-04 final fingerprints and closure condition

```text
04_bath_only_fock_loader.py
cf0246ee8767dbb8862d637a4225952c9625392281d3856a616e69fea22c7d9c

Task04_Stage03_Independent_Loader_Verified_2026-08-03.zip
0a658b07e6f32d292dce658b9288d196070c7b745db099622306fac7676e11a7

Stage03_loader_audit.json
d44c429c4a5fe42cfdd0c1ccd8884fb6eaf422423869ad64032171172b3df69b

Stage03_bath_only_report.md
52e73ce0c55c623091a0a96425b79d08ca0e8e3097cfc127aa2ded0d193a7e31

Stage03_loader_case_metrics.csv
ef105a722872716267d7ee8ac3c48dd70af7d3922960916fa3d603bb0d243b01

Stage03_loader_cutoff_metrics.csv
24022372f499bedc7248e93d6bd02ad01d49818f38ae1fa563d269c14feb6744
```

Final Audit-04 conditions:

```text
loader return code = 0
stable Audit-03 hashes = 8/8
independent refined gates = 32/32
solver-equivalent gates = 32/32
criteria and PASS/FAIL agreement = true
same-directory stable outputs = true
simple hash tamper detected = true
coordinated metric+manifest tamper detected = true
bath branch closed = true
```

## Appendix F — Stage-01 review-copy inventory

```text
Stage01_static_mode(1).zip
e9699883149c6f45732fc392e5f3f5b37ed3c79f251c98f212ba6047389cc4f2

meaningful files = 75
configuration files = 12
solver-audit files = 12
NumPy arrays = 36
aggregate CSV files = 2
embedded audit Markdown files = 1
all 12 detector/mode/confinement cases present = true
refined dt=2.5e-4 cases present = false
factorized scalar-control solver present = false
```

The last two `false` entries do not indicate a missing Audit-01 case. They identify the additional control now assigned to Task 05A.


# Part XV — Executed Task-05 audit, solver verdict, and conditional Task-06 handoff

> **Historical-status note.** This part records the original SciPy/CPU audit attempt and remains part of the provenance chain. Its `FAIL / BLOCKED` verdict is not the current H200/CuPy verdict; see Part XVI.

## 69. Scope of the executed audit

The audited source was

```text
05_oscillator_channel_detector_test.py
SHA-256: 9cfa32559a62882961f2fab33fd50e13cf9996d5b2db992d5bb1ca93380df86a
```

The source compiled and parsed. Its operator layer, explicit Audit-02 permutation, state ordering, complex128 matrices, spinor roof sign, detector-loss identity, midpoint probability, source formulas, fixed-directory policy, source copying, stale-output replacement, and zero-bath scope passed source-level reconstruction.

The reduced three-map smoke passed. A repeated same-prefix spinor smoke removed stale files and reproduced every stable output hash exactly. Reduced mode controls additionally gave:

```text
factorized scalar dTV(10,00) = 1.1362438767648086e-16
factorized scalar dTV(01,00) = 1.1362438767648086e-16
factorized scalar dTV(10,01) = 0.0000000000000000e+00
monolithic reduced R_h/R_h/2 = 4.001234850346
spinor reduced dTV(10,01) = 8.6736173798840355e-19
```

These are structural reduced tests, not the Task-05 production result.

## 70. Production-gate failure

The first frozen production campaign attempt used

```text
propagator = scalar_factorized
mode = 00
omega = 100
N_shell = 12
N_z = 1500
dt = 5e-4
T_final = 10
steps = 20000
configuration SHA-256 = a6c7cf12ba7a75fa8c9be65147c08e7ea06da56ebad991822a2a46b33928fe7d
```

It terminated at step 105:

```text
Survival increased by 2.868256743227e-09
```

The source guard is \(2\times10^{-9}\). A 500-step diagnostic with only the guard relaxed accumulated a roof/norm closure residual of \(7.6690990\times10^{-7}\), so the gate must not be weakened. A separate, explicitly non-authoritative diagnostic using factorized-channel GMRES `rtol=1e-10` reduced the 500-step closure residual to \(1.6703638\times10^{-10}\). This identifies a probable solver-accuracy correction but does not amend the frozen source or authorize a physics claim.

The available runtime had neither CUDA nor CuPy. A production-dimensional 100-step spinor benchmark required 9.04 s wall time and 354,068 KiB peak resident memory. The complete spinor baseline/refinement/cutoff matrix was therefore not executed on CPU after the scalar control failed.

## 71. Task-05 scientific verdict

\[
\boxed{{\text{{Task-05 solver-level verdict: FAIL / BLOCKED}}}}
\]

Established:

1. complete-shell and tensor implementation is correct;
2. the plus sign \(+K_N/(2h_z)\) is independently derived and verified;
3. the factorized scalar map is exactly mode-null in the reduced test;
4. the reduced monolithic artifact exhibits the expected factor-four halving ratio;
5. reduced spinor evolution generates nonzero downward and dephasing source structure after roof interaction, while the scalar ground-state source curves remain at the numerical floor;
6. no active bath is present.

Not established:

1. the twelve production recovery cases;
2. production scalar-null values at \(\omega=1,100\);
3. production monolithic quadratic ratio at \(\omega=100\);
4. production spinor time-step convergence;
5. production \(N=12\to16\) shell convergence;
6. Cartesian–oscillator representation discrepancy at common full inputs;
7. any detector–bath susceptibility or finite-temperature response.

Task 05 is not closed. The branch remains open until both the corrected/intended-backend solver and the independent Task-06 loader pass.

## 72. Exact prerequisite before Task 06

Before Task 06 is run, a new or GPU-verified Task-05 source must complete every required case with:

- status `completed` and process exit 0;
- all solver checks true;
- a copied source file and source SHA-256;
- exact configuration hash;
- stable output hash manifest;
- no stale same-prefix files;
- zero GMRES failures;
- true relative residual within the frozen or newly audited tolerance;
- nonnegative midpoint probabilities;
- monotone survival within the accepted numerical guard;
- roof/norm closure;
- finite shell and source arrays.

The corrected source must receive a new version identifier and hash if any non-manual numerical line changes.

## 73. Exact Task-06 input set

Task 06 must consume, without rerunning the solver, the following completed Task-05 products.

### 73.1 Baseline recovery: 12 cases

```text
N_shell = 12
T_final = 10
omega = 1, dt = 1e-3, modes = 00,10,01,
    propagators = scalar_factorized, spinor
omega = 100, dt = 5e-4, modes = 00,10,01,
    propagators = scalar_factorized, spinor
```

### 73.2 Monolithic scalar diagnostic

```text
omega = 100
modes = 00,10
N_shell = 12
T_final = 10
dt = 5e-4 and 2.5e-4
optional dt = 1.25e-4 only if the first ratio is outside 3.5--4.5
```

### 73.3 Spinor time-step refinement

```text
omega = 100
modes = 00,10
N_shell = 12
T_final = 10
dt = 2.5e-4
```

### 73.4 Spinor shell convergence

```text
omega = 100
modes = 00,10
dt = 5e-4
T_final = 10
N_shell = 8,12,16
```

The existing matching \(N=12\) baseline files are reused only after Task 06 verifies their source, configuration, and output hashes.

For each case Task 06 requires:

```text
CASE_configuration.json
CASE_operator_audit.json
CASE_solver_audit.json
CASE_times.npy
CASE_survival.npy
CASE_step_loss_roof_midpoint.npy
CASE_shell_populations.npz
CASE_source_diagnostics.npz
CASE_selected_insertion_vectors.npz
CASE_run_status.json
CASE_output_hashes.json
CASE_05_oscillator_channel_detector_test.py
```

## 74. Task-06 independent reconstruction checks

The loader must not import the solver and must not trust its PASS flag. It must independently:

1. verify every stable file hash and copied-source hash;
2. verify exact configuration/source coherence and reject duplicate or ambiguous case identities;
3. validate NPZ/NPY schema, shapes, dtypes, monotone time grids, and finiteness with `allow_pickle=False`;
4. reconstruct descending complete shells and the index formula \((sM_N+\mu)N_z+k_z\);
5. independently reconstruct \(a_x,a_y,N_x,N_y,H_{\perp,N}\), Pauli matrices, and \(K_N\);
6. reconstruct the literal Audit-02 native representation and verify the explicit permutation;
7. derive and verify the plus sign \(+K_N/(2h_z)\) and the anti-Hermitian roof-loss identity;
8. recompute every launch identity and source-norm formula;
9. reconstruct \(S(t)\), midpoint \(g(t)\), \(D(T)\), \(\mu^*(T)\), \(D_E\), \(D_L\), and late fraction directly from saved arrays;
10. recompute probability closure, GMRES failure counts, maximum true residual, minimum midpoint loss, survival monotonicity, top-shell population, and omitted-\(K\) proxy;
11. compare all complete censored laws using
    \[
    d_{\rm TV}^{(T)}=\frac12\left[\sum_n|p_{1,n}-p_{2,n}|+|S_1(T)-S_2(T)|\right],
    \]
    and
    \[
    W_1^{(T)}\approx\int_0^T|S_1(t)-S_2(t)|dt;
    \]
12. reproduce the Audit-01 Cartesian target tables from the archived source arrays and calculate Cartesian–oscillator discrepancies only at common inputs;
13. verify 10/01 isotropy, factorized scalar null, monolithic halving, spinor time-step convergence, and shell convergence;
14. independently audit same-directory rerun behavior for at least one identical case;
15. verify the absence of active bath, Lindblad, density-matrix, finite-temperature, susceptibility, and trajectory code.

## 75. Task-06 acceptance gates

Task 06 passes only if:

- every required case and file is present, hashed, completed, and finite;
- all reconstructed operator, ordering, permutation, and roof-sign gates pass;
- all GMRES return codes are zero;
- the true residual satisfies the declared audited tolerance;
- every midpoint probability is nonnegative;
- survival is monotone within the audited roundoff guard;
- detector probability closure is consistent with solver accuracy;
- for mode 00, \(s_\downarrow(0)=0\), \(s_\phi(0)=0\), and \(s_\uparrow^{(N)}(0)=2\);
- the authoritative factorized scalar laws are mode invariant with
  \[
  d_{\rm TV}\le10^{-11};
  \]
- the monolithic scalar ratio lies in 3.5–4.5, or the mandatory third step is supplied and demonstrates the asymptotic regime;
- 10/01 isotropy is at the declared numerical floor;
- spinor time-step and \(N=12\to16\) shell differences are bounded by the predeclared Task-05 error budget;
- top-shell and omitted-boundary-coupling diagnostics are small and improve with shell cutoff;
- Cartesian–oscillator discrepancies are explicitly separated from time-step, shell, and solve errors;
- reduced source activity is not mislabeled as a bath response;
- every claimed nonzero scientific contrast exceeds the combined numerical uncertainty.

Task 06 must output:

```text
Task05_loader_audit.json
Task05_complete_case_metrics.csv
Task05_pairwise_curve_metrics.csv
Task05_cutoff_metrics.csv
Task05_detector_source_report.md
Task05_loader_output_hashes.json
Task05_loader_run_status.json
```

Only then may the status become

\[
\boxed{{\text{{Task-05 branch fully closed}}}}.
\]

Until that independent PASS, the environmental-susceptibility phase remains blocked.

## 76. Complete Task-05 execution registry

The registry below contains every completed, failed, or explicitly non-authoritative diagnostic execution used in this audit. The output hash is the SHA-256 of the case output-hash manifest; that manifest contains the individual stable-file hashes. A dash means no completed output manifest was produced.

| Case | Scope | Exact configuration | Status / process exit | Source SHA-256 | Configuration SHA-256 | Output-manifest SHA-256 |
|---|---|---|---|---|---|---|
| `smoke_scalar_factorized` | reduced_smoke; source-conforming | scalar_factorized; mode=00; omega=4.0; N=2; M=6; d=12; Nz=96; dt=0.002; T=0.01; steps=5 | completed / 0 | `9cfa32559a62882961f2fab33fd50e13cf9996d5b2db992d5bb1ca93380df86a` | `7f43239254e01532abdd0d260262230cca14253b18ca0d5a9782e1e001ba9fd8` | `b27fc418a7e775ed654e1236f51d08e6907af693c11420f68ef91352b8151187` |
| `smoke_scalar_monolithic` | reduced_smoke; source-conforming | scalar_monolithic; mode=00; omega=4.0; N=2; M=6; d=12; Nz=96; dt=0.002; T=0.01; steps=5 | completed / 0 | `9cfa32559a62882961f2fab33fd50e13cf9996d5b2db992d5bb1ca93380df86a` | `bdd09c292dfe182735fb01b4cf32caa30494330df6c394df4c69a45ad97bb4f9` | `6507c3c5e5bdd6b7bf3c5a9bfcdd5c8b32bc523a2a243dcc15bac3377ef08159` |
| `smoke_spinor` | reduced_smoke; source-conforming | spinor; mode=00; omega=4.0; N=2; M=6; d=12; Nz=96; dt=0.002; T=0.01; steps=5 | completed / 0 | `9cfa32559a62882961f2fab33fd50e13cf9996d5b2db992d5bb1ca93380df86a` | `b0e6f65f7dd82ef4289f8c181301e074cb855c5b8a3fd122db45caf34d047283` | `23ff1e7df5f0022f14ab40030240d5ddeca922b6756fa5693c6de9736e86aa5c` |
| `reduced_fact_mode10_dt2e-3` | reduced_scalar_null; source-conforming | scalar_factorized; mode=10; omega=4.0; N=2; M=6; d=12; Nz=96; dt=0.002; T=0.01; steps=5 | completed / 0 | `9cfa32559a62882961f2fab33fd50e13cf9996d5b2db992d5bb1ca93380df86a` | `c50d4366a28c079ad80a7c744929d7be386c564881d886e88fa991e5cf12c0bf` | `dd050c075615ab82a8c2fa99c75c0d9f7673396b6e27f756ede29e77fe9ccc55` |
| `reduced_fact_mode01_dt2e-3` | reduced_scalar_null; source-conforming | scalar_factorized; mode=01; omega=4.0; N=2; M=6; d=12; Nz=96; dt=0.002; T=0.01; steps=5 | completed / 0 | `9cfa32559a62882961f2fab33fd50e13cf9996d5b2db992d5bb1ca93380df86a` | `d9a10c674d18f55395cc52cc845ec77f3c9db345121c67a108767021b6379662` | `42385744e1698b625aecfb0cb3034c9b3d8d8885bdb125158d35d74e368d1fb0` |
| `reduced_mono_mode10_dt2e-3` | reduced_monolithic_halving; source-conforming | scalar_monolithic; mode=10; omega=4.0; N=2; M=6; d=12; Nz=96; dt=0.002; T=0.01; steps=5 | completed / 0 | `9cfa32559a62882961f2fab33fd50e13cf9996d5b2db992d5bb1ca93380df86a` | `882e48a35ed6781db9cfb6d849791e9160e6c5dcfeef3437012293a998fa1d65` | `36f795e7d1cabe2fbb921bedb5075297dc694719bc3bacc4118176b84a7326e9` |
| `reduced_mono_mode00_dt1e-3` | reduced_monolithic_halving; source-conforming | scalar_monolithic; mode=00; omega=4.0; N=2; M=6; d=12; Nz=96; dt=0.001; T=0.01; steps=10 | completed / 0 | `9cfa32559a62882961f2fab33fd50e13cf9996d5b2db992d5bb1ca93380df86a` | `a7e1a7f236a3bd24d7e0c3b558aa51c21797266380155b24dcd6b07a586c2f26` | `cc489eaa7a5187eed15f08b05fb079e5c5f23e73d49dec27a1679f8baf909a87` |
| `reduced_mono_mode10_dt1e-3` | reduced_monolithic_halving; source-conforming | scalar_monolithic; mode=10; omega=4.0; N=2; M=6; d=12; Nz=96; dt=0.001; T=0.01; steps=10 | completed / 0 | `9cfa32559a62882961f2fab33fd50e13cf9996d5b2db992d5bb1ca93380df86a` | `54b0e2a025d2606615ae36b8f922f3d2b25ae15e601ddc54380b449cfaceb55e` | `9f5ec5d36e2f42d3b16e206c1c0358d937b3ce1d85bd7448c2bba10a5f4b5b0d` |
| `reduced_spinor_mode10_dt2e-3` | reduced_spinor_isotropy; source-conforming | spinor; mode=10; omega=4.0; N=2; M=6; d=12; Nz=96; dt=0.002; T=0.01; steps=5 | completed / 0 | `9cfa32559a62882961f2fab33fd50e13cf9996d5b2db992d5bb1ca93380df86a` | `1f722933222721f2be31bc9ea5e99b518a09e0e794dc55fa68def4386e538673` | `863ad983b50eed9ee6549e6ea2a62029bb56caed7195500ba54b6f433fe07602` |
| `reduced_spinor_mode01_dt2e-3` | reduced_spinor_isotropy; source-conforming | spinor; mode=01; omega=4.0; N=2; M=6; d=12; Nz=96; dt=0.002; T=0.01; steps=5 | completed / 0 | `9cfa32559a62882961f2fab33fd50e13cf9996d5b2db992d5bb1ca93380df86a` | `34e65bec711f524a2c56092df2ca1220a72a186a8aa9ecc851500e6fce205c20` | `e027f7a50cfb23446ac369df4023f52dc930dfdaff2b7560d541fca375c2d3f7` |
| `benchmark_spinor_w100_m00_N12_dt5e-4_100steps` | production_dimension_short_benchmark; source-conforming | spinor; mode=00; omega=100.0; N=12; M=91; d=182; Nz=1500; dt=0.0005; T=0.05; steps=100 | completed / 0 | `9cfa32559a62882961f2fab33fd50e13cf9996d5b2db992d5bb1ca93380df86a` | `e311817c88d3ba44f08b8de02586163b863641bf8f6b217cfa9727692dca0820` | `e7994f4b5feb4638dee8d46e6561b494e8549d2e9185b0c453ca096248fe23bc` |
| `benchmark_fact_w100_100steps` | production_dimension_short_benchmark; source-conforming | scalar_factorized; mode=00; omega=100.0; N=12; M=91; d=182; Nz=1500; dt=0.0005; T=0.05; steps=100 | completed_with_failed_gate / 0 | `9cfa32559a62882961f2fab33fd50e13cf9996d5b2db992d5bb1ca93380df86a` | `fcd874152d2a0befa37c742ac617301728025776cbecb1b9328e8b25d778cfda` | `7f6f0b02fa9819d41b76daec11f160f5e562f3060cc78f8dddcfcb3ef4fa874d` |
| `diag_fact_w100_500steps_relaxed` | non_authoritative_defect_isolation; non-authoritative diagnostic | scalar_factorized; mode=00; omega=100.0; N=12; M=91; d=182; Nz=1500; dt=0.0005; T=0.25; steps=500 | completed_with_failed_gate / 0 | `9cfa32559a62882961f2fab33fd50e13cf9996d5b2db992d5bb1ca93380df86a` | `f474da81031e0a7ab9b5b4c318840b7273ee026490f010d35bd58f20381c1243` | `ad89a553e621df9f9f86e6578ee1d3d817db43d66ff464ec7ca40cb646a4469c` |
| `diag_fact_w100_500steps_rtol1e-10` | non_authoritative_defect_isolation; non-authoritative diagnostic | scalar_factorized; mode=00; omega=100.0; N=12; M=91; d=182; Nz=1500; dt=0.0005; T=0.25; steps=500 | completed / 0 | `9cfa32559a62882961f2fab33fd50e13cf9996d5b2db992d5bb1ca93380df86a` | `60c383a5ccfd8b146bff54ba5a76164a8cea2fdc913d57f7513a558abc850797` | `d291196ae75988fb1386a918b497138f780917165607fdf30aaa329d9a270668` |
| `diagnostic_fact_w100_m00_N12_dt5e-4` | frozen_campaign_attempt; source-conforming | scalar_factorized; mode=00; omega=100.0; N=12; M=91; d=182; Nz=1500; dt=0.0005; T=10.0; steps=20000 | failed / 1 | `9cfa32559a62882961f2fab33fd50e13cf9996d5b2db992d5bb1ca93380df86a` | `a6c7cf12ba7a75fa8c9be65147c08e7ea06da56ebad991822a2a46b33928fe7d` | `—` |


## 77. Audit artifacts for this update

```text
Task05_Source_Execution_and_Scientific_Audit_Report_2026-08-03.md
Task05_executed_case_summary_2026-08-03.csv
Task05_compact_audit_summary_2026-08-03.npz
Task05_source_audit_2026-08-03.json
```

The prior master file and audited solver source remain unchanged.

# Part XVI — H200/CuPy Task-05 first-16 production audit and current verdict

## 78. Evidence set, package integrity, and supersession of the CPU blocker

The submitted production archive is

```text
Task05_first16_loader_packages.zip
SHA-256: 5ca14feae4662bada426cdf56143a8659a4cbfc73fa48ca982ccd357c10bd6db
```

It contains 17 inner loader-share ZIP files. Direct extraction and hash verification gave:

| Item | Result |
|---|---:|
| inner loader-share ZIPs | 17 |
| current production packages | 16 |
| obsolete preliminary package | 1 |
| loader-package hash manifests verified | 17/17 |
| current solver cases with `all_checks_passed=true` | 16/16 |
| current cases using CuPy on NVIDIA H200 | 16/16 |
| active bath/Lindblad/density-matrix/trajectory code | absent in 16/16 |

The obsolete package is

```text
spinor_omega1_mode00_N12_dt1e-3_loader_share.zip
SHA-256: 6ae84c3cd8e56229e98d76b445a5844ceb3d89817aa680edda867b061b4a0fb2
```

Its filename is misleading: its stored configuration is actually
`scalar_factorized`, \(\omega=100\), mode `00`, \(N=12\), and
\(\Delta t=5\times10^{-4}\), and it belongs to the earlier failed-gate
revision. It is excluded from every current scientific comparison and must be
archived outside the Task-06 discovery path.

The 16 current solver files have different literal SHA-256 values because the
manually selected physical parameters and the user-selected stage-directory
number are embedded in each source. After normalizing only those declared
manual fields and the nonphysical stage number, all 16 files have one identical
computational-body fingerprint:

```text
normalized Task-05 computational-body SHA-256:
6ece5eac6b9be0f0d6ec93fc53d82c35cc85b9c0f867ed5a4cd22544b1be65de
```

The independent single-case loader is identical in all 16 current packages:

```text
05_single_case_independent_loader.py
SHA-256: 63e1473920ed15e480a9a3bbd9ce7168ed4bf24594eac631d8473d4923c8c61e
```

Thus the H200 results are generated by one common numerical implementation;
the differing full source hashes remain recorded case by case in Section 90.

The original SciPy/CPU production blocker in Part XV is therefore resolved at
the intended backend. It remains a valid historical backend audit, but it is no
longer the current Task-05 solver verdict.

## 79. Configuration-inventory audit: the submitted “first 16” are not the frozen first 16

The frozen first block consists of 12 baseline cases plus four \(\omega=100\)
monolithic cases. The submitted archive contains 16 current configurations, but
only 12 are members of that frozen set.

| Inventory item | Count |
|---|---:|
| frozen first-block configurations required | 16 |
| required configurations actually present | 12 |
| required configurations missing | 4 |
| extra, scientifically useful configurations present | 4 |
| obsolete preliminary package excluded | 1 |

### 79.1 Missing required configurations

```text
scalar_factorized, omega=1,   mode=00, N=12, dt=1e-3,   T=10
scalar_factorized, omega=1,   mode=10, N=12, dt=1e-3,   T=10
scalar_factorized, omega=1,   mode=01, N=12, dt=1e-3,   T=10
scalar_monolithic, omega=100, mode=10, N=12, dt=2.5e-4, T=10
```

### 79.2 Extra configurations that were executed instead

```text
scalar_monolithic, omega=1,   mode=00, N=12, dt=1e-3,   T=10
scalar_monolithic, omega=1,   mode=10, N=12, dt=1e-3,   T=10
scalar_monolithic, omega=1,   mode=01, N=12, dt=1e-3,   T=10
scalar_monolithic, omega=100, mode=01, N=12, dt=2.5e-4, T=10
```

These extra calculations are valid and informative. In particular, the
\(\omega=1\) monolithic set supplies an excellent Cartesian-recovery control,
and the refined \(|01\rangle\) case is algebraically degenerate with
\(|10\rangle\) for the scalar monolithic Hamiltonian. They do not, however,
silently replace the exact frozen configuration list.

The present data set must therefore be described as

\[
\boxed{12\ \text{required first-block cases}+4\ \text{extra controls}},
\]

not as the completed frozen first-16 campaign.

## 80. Numerical integrity of the 16 current H200 cases

Every current solver case completed all time steps and set
`all_checks_passed=true`. The aggregate numerical envelope is:

| Audit quantity | Result |
|---|---:|
| current cases | 16 |
| operator and tensor-order audits | 16/16 PASS |
| spinor roof-sign/loss audits | 16/16 PASS |
| zero-bath source guards | 16/16 PASS |
| GMRES failures | 0 |
| maximum true relative residual | 5.099925548838e-10 |
| minimum true relative residual among case maxima | 9.588681825494e-15 |
| maximum roof-closure relative residual | 3.960035852843e-10 |
| minimum roof-closure relative residual | 1.689455673259e-14 |
| largest survival increase | 4.662936703426e-15 |
| minimum midpoint roof probability | 5.438868791623e-177 |
| maximum normalized top-shell population | 1.514757866724e-08 |
| largest accumulated omitted-\(K\) proxy | 1.021440268423e-03 |
| summed solver wall time | 1405.811 s = 23.430 min |

No compact loader package contains the external H200 memory-log files, so a
campaign-wide peak-memory number is not inferred here.

### 80.1 Loader-threshold reconciliation

The raw single-case loader results are:

```text
13 direct PASS
3 FAIL
```

Across all cases the loader evaluated 1328 Boolean checks and passed 1325. The
only three failed checks are

```text
raw_array_probability_and_solver.exact_decomposed_closure
```

for the three factorized-scalar \(\omega=100\) cases. Their independently
reconstructed decomposed residuals are

| mode | decomposed residual |
|---|---:|
| 00 | 5.844214001627e-13 |
| 10 | 8.892886427248e-13 |
| 01 | 9.077183449335e-13 |

The current solver source uses

\[
\epsilon_{\mathrm{decomp}}^{\mathrm{abs}}=10^{-11},
\]

whereas the loader source still hard-codes \(5\times10^{-13}\). All three
residuals are below \(10^{-11}\), while their principal roof closure,
telescoping closure, monotonicity, midpoint positivity, and Krylov residuals
pass by large margins. Re-evaluating only this stale loader criterion gives

```text
16/16 adjusted independent single-case passes
1328/1328 adjusted checks
```

The original loader JSON files are not rewritten or relabeled. In the table
below, `PASS*` means “raw loader FAIL caused solely by the documented obsolete
decomposed-closure threshold; independently accepted at the solver’s audited
\(10^{-11}\) threshold.”

A provenance imperfection remains: the solver source contains the named
\(10^{-11}\) tolerance but does not list it in the JSON
`acceptance_tolerances` block, and the script version string remains `v1`.
The full source hashes preserve the actual revision. Task 06 must record this
tolerance explicitly.

## 81. Complete current-case detector table

| propagator | ω | mode | N | Δt | S(10) | D | μ* | D_E | D_L | w_L | max p_top | ∫r_K,omit | solver | loader† |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| scalar_factorized | 100 | 00 | 12 | 0.0005 | 0.093115503 | 0.906884497 | 4.127236412 | 0.587601468 | 0.319283029 | 0.352065815 | 0.000e+00 | 0.000e+00 | PASS | PASS* |
| scalar_factorized | 100 | 01 | 12 | 0.0005 | 0.093115503 | 0.906884497 | 4.127236412 | 0.587601468 | 0.319283029 | 0.352065815 | 0.000e+00 | 0.000e+00 | PASS | PASS* |
| scalar_factorized | 100 | 10 | 12 | 0.0005 | 0.093115503 | 0.906884497 | 4.127236412 | 0.587601468 | 0.319283029 | 0.352065815 | 0.000e+00 | 0.000e+00 | PASS | PASS* |
| scalar_monolithic | 1 | 00 | 12 | 0.001 | 0.093115781 | 0.906884219 | 4.127270921 | 0.587597718 | 0.319286502 | 0.352069751 | 0.000e+00 | 0.000e+00 | PASS | PASS |
| scalar_monolithic | 1 | 01 | 12 | 0.001 | 0.093115794 | 0.906884206 | 4.127281371 | 0.587595693 | 0.319288513 | 0.352071974 | 0.000e+00 | 0.000e+00 | PASS | PASS |
| scalar_monolithic | 1 | 10 | 12 | 0.001 | 0.093115794 | 0.906884206 | 4.127281371 | 0.587595693 | 0.319288513 | 0.352071974 | 0.000e+00 | 0.000e+00 | PASS | PASS |
| scalar_monolithic | 100 | 00 | 12 | 0.00025 | 0.093119991 | 0.906880009 | 4.127779671 | 0.587475219 | 0.319404790 | 0.352201821 | 0.000e+00 | 0.000e+00 | PASS | PASS |
| scalar_monolithic | 100 | 01 | 12 | 0.00025 | 0.093135040 | 0.906864960 | 4.129328084 | 0.587113044 | 0.319751916 | 0.352590441 | 0.000e+00 | 0.000e+00 | PASS | PASS |
| scalar_monolithic | 100 | 00 | 12 | 0.0005 | 0.093135263 | 0.906864737 | 4.129435136 | 0.587094243 | 0.319770493 | 0.352611013 | 0.000e+00 | 0.000e+00 | PASS | PASS |
| scalar_monolithic | 100 | 10 | 12 | 0.0005 | 0.093216700 | 0.906783300 | 4.135627919 | 0.585644305 | 0.321138995 | 0.354151863 | 0.000e+00 | 0.000e+00 | PASS | PASS |
| spinor | 1 | 00 | 12 | 0.001 | 0.114383672 | 0.885616328 | 4.258067789 | 0.576191196 | 0.309425132 | 0.349389597 | 8.637e-13 | 3.772e-11 | PASS | PASS |
| spinor | 1 | 01 | 12 | 0.001 | 0.134313360 | 0.865686640 | 4.382943697 | 0.565216841 | 0.300469798 | 0.347088409 | 1.874e-11 | 7.863e-10 | PASS | PASS |
| spinor | 1 | 10 | 12 | 0.001 | 0.134313360 | 0.865686640 | 4.382943697 | 0.565216841 | 0.300469798 | 0.347088409 | 1.874e-11 | 7.863e-10 | PASS | PASS |
| spinor | 100 | 00 | 12 | 0.0005 | 0.486179048 | 0.513820952 | 6.594333888 | 0.366043645 | 0.147777307 | 0.287604673 | 3.851e-10 | 2.573e-05 | PASS | PASS |
| spinor | 100 | 01 | 12 | 0.0005 | 0.551308712 | 0.448691288 | 7.150565663 | 0.285124416 | 0.163566873 | 0.364542118 | 1.515e-08 | 1.021e-03 | PASS | PASS |
| spinor | 100 | 10 | 12 | 0.0005 | 0.551308712 | 0.448691288 | 7.150565663 | 0.285124416 | 0.163566873 | 0.364542118 | 1.515e-08 | 1.021e-03 | PASS | PASS |

`† PASS*` has the precise meaning defined in Section 80.1.

All scalar cases have exactly zero top-shell population and zero omitted-\(K\)
proxy, as required. The nonzero spinor values are diagnostics of boundary-driven
channel transfer and truncation pressure, not probability loss.

## 82. Authoritative factorized scalar control

At \(\omega=100\), \(N=12\), \(\Delta t=5\times10^{-4}\), the complete
factorized scalar laws obey:

| comparison | dTV | W1 | max abs(ΔS) | Δμ* | gate ≤1e-11 |
|---|---|---|---|---|---|
| 10-00 | 1.109654946820e-13 | 5.666959887463e-13 | 8.970602038971e-14 | 4.609645998244e-13 | PASS |
| 01-00 | 1.109654946820e-13 | 5.666959887463e-13 | 8.970602038971e-14 | 4.609645998244e-13 | PASS |

Therefore,

\[
\boxed{d_{\mathrm{TV}}^{(10)}\simeq1.11\times10^{-13}<10^{-11}},
\]

for both first-shell directions. This is the authoritative finite-step scalar
null. The complete curves, terminal atom, restricted mean, prompt fraction, and
late fraction are all mode invariant at the solver floor.

The scalar source diagnostics are also exact:

- mode `00`: \(s_\downarrow=0\), \(s_\phi=0\), \(s_\uparrow=2\);
- modes `10` and `01`: \(s_\downarrow=1\), \(s_\phi=0\),
  \(s_\uparrow=3\);
- all top-shell populations and omitted-\(K\) proxies are zero.

The corresponding \(\omega=1\) factorized cases are absent, so the frozen
two-confinement scalar-null campaign is not yet complete.

## 83. Monolithic scalar finite-step artifact

The executed monolithic mode contrasts are:

| case | comparison | R_h=dTV | status |
|---|---|---|---|
| ω=1, h=1e-3 | 10-00 | 1.590123343791e-05 | extra control |
| ω=1, h=1e-3 | 01-00 | 1.590123341973e-05 | extra control |
| ω=100, h=5e-4 | 10-00 | 5.226405658793e-03 | required coarse |
| ω=100, h=2.5e-4 | 01-00 | 1.312471093973e-03 | exact-degenerate first-shell proxy; requested 10 case absent |

Using the exact first-shell degeneracy of the scalar oscillator Hamiltonian,
the refined \(|01\rangle\) case supplies the same scalar monolithic law that
\(|10\rangle\) must supply at the same \(h\). The measured halving ratio is

\[
\frac{R_{5\times10^{-4}}}{R_{2.5\times10^{-4}}}
=
\frac{5.226405658793e-03}{1.312471093973e-03}
=
3.982111059660.
\]

This lies inside the predeclared interval

\[
3.5\le R_h/R_{h/2}\le4.5.
\]

The scaled coefficients are

\[
\frac{R_h}{h^2}=20905.622635,
\qquad
\frac{R_{h/2}}{(h/2)^2}=20999.537504,
\]

which differ by only 0.449%.
The monolithic artifact therefore exhibits the expected global
\(O(h^2)\) behavior, and the optional \(1.25\times10^{-4}\) pair is not
scientifically required.

For strict configuration-level closure, the requested
`scalar_monolithic, omega=100, mode=10, dt=2.5e-4` run should still be
executed. The present ratio is a valid symmetry-based scientific result, but
the missing requested file should not be concealed.

The extra \(\omega=1\) monolithic controls give

\[
R_{10-00}=1.590123343791e-05,
\]

consistent with the much smaller weak-confinement finite-step artifact already
seen in the Cartesian solver.

## 84. Spinor isotropy and static first-shell response

### 84.1 Exact \(10/01\) isotropy

| ω | dTV(10,01) | W1 | max abs(ΔS) | verdict |
|---|---|---|---|---|
| 1 | 8.514610309610e-14 | 5.780889378304e-13 | 1.307842723008e-13 | PASS |
| 100 | 3.773406682439e-14 | 7.879523977739e-13 | 1.513233982564e-13 | PASS |

The oscillator-channel spinor solver therefore preserves directional
degeneracy at approximately \(10^{-13}\), substantially below every physical
mode contrast.

### 84.2 First-shell response relative to the ground state

Because the `10` and `01` laws are indistinguishable at the solver floor, the
table reports `10-00`; `01-00` gives the same values.

| ω | dTV(10,00) | ΔS(T) | ΔD | Δμ* | ΔD_E | ΔD_L | late fraction | mean click before T |
|---|---|---|---|---|---|---|---|---|
| 1 | 0.020305668 | +0.019929688 | -0.019929688 | +0.124875908 | -0.010974354 | -0.008955334 | 0.349390→0.347088 | 3.516456→3.511444 |
| 100 | 0.102284280 | +0.065129663 | -0.065129663 | +0.556231775 | -0.080919229 | +0.015789566 | 0.287605→0.364542 | 3.371882→3.649455 |

At \(\omega=1\), first-shell preparation reduces both prompt and late
detections, while increasing terminal survival and the restricted mean. At
\(\omega=100\), it produces the stronger and qualitatively distinctive
restructuring:

- total detection decreases by \(6.5129663\times10^{-2}\);
- prompt detection decreases by \(8.0919229\times10^{-2}\);
- late detection increases by \(1.5789566\times10^{-2}\);
- the late fraction rises from \(0.287605\) to \(0.364542\);
- the click-conditioned mean rises from \(3.371882\) to \(3.649455\).

The complete-law response grows by the factor

\[
\frac{d_{\mathrm{TV}}(\omega=100)}{d_{\mathrm{TV}}(\omega=1)}
=
5.037227995.
\]

### 84.3 First-shell upward-direction coefficient

| ω | Δ↑S(T) | Δ↑D | Δ↑μ* | Δ↑D_E | Δ↑D_L | ½||Δ↑ν||_1 | closure |
|---|---|---|---|---|---|---|---|
| 1 | +0.039859376 | -0.039859376 | +0.249751816 | -0.021948709 | -0.017910667 | 0.040611336 | -2.933e-11 |
| 100 | +0.130259326 | -0.130259326 | +1.112463550 | -0.161838458 | +0.031579132 | 0.204568561 | 2.230e-12 |

This is a zero-bath static preparation coefficient. It is also the launch-time
operator direction relevant to a later upward environmental insertion, but it
is not yet a heating susceptibility.

## 85. Cartesian--oscillator recovery and representation discrepancy

The Cartesian archive and oscillator-channel curves were compared at common
physical inputs and common time grids. The complete censored-law discrepancies
are:

| comparison | ω | mode | dTV | W1 | max abs(ΔS) | Δμ* (osc-cart) |
|---|---|---|---|---|---|---|
| spinor oscillator vs Cartesian | 1 | 00 | 7.714011300e-05 | 4.441541754e-04 | 7.178380306e-05 | +4.440662416e-04 |
| spinor oscillator vs Cartesian | 1 | 10 | 2.183116510e-04 | 1.284224822e-03 | 2.054542700e-04 | +1.284127240e-03 |
| spinor oscillator vs Cartesian | 1 | 01 | 2.183151841e-04 | 1.284207397e-03 | 2.054541858e-04 | +1.284101485e-03 |
| spinor oscillator vs Cartesian | 100 | 00 | 1.390151021e-03 | 9.481574941e-03 | 1.322976512e-03 | -9.481416009e-03 |
| spinor oscillator vs Cartesian | 100 | 10 | 9.711080590e-03 | 3.323019014e-02 | 6.047880877e-03 | -3.323001069e-02 |
| spinor oscillator vs Cartesian | 100 | 01 | 9.711098490e-03 | 3.323112409e-02 | 6.047966939e-03 | -3.323112409e-02 |
| scalar monolithic oscillator vs Cartesian | 1 | 00 | 2.677678974e-07 | 2.981987511e-07 | 7.000563973e-08 | +1.776059646e-07 |
| scalar monolithic oscillator vs Cartesian | 1 | 10 | 2.876502495e-07 | 3.135398032e-07 | 7.607271446e-08 | +1.855538478e-07 |
| scalar monolithic oscillator vs Cartesian | 1 | 01 | 2.868188183e-07 | 3.081349973e-07 | 7.388292456e-08 | +1.831467040e-07 |
| scalar monolithic oscillator vs Cartesian | 100 | 00 | 2.676874124e-06 | 5.869568958e-06 | 1.343423677e-06 | +5.869568958e-06 |
| scalar monolithic oscillator vs Cartesian | 100 | 10 | 1.328195041e-05 | 1.934605343e-05 | 5.193858678e-06 | +1.934605343e-05 |
| scalar factorized control vs Cartesian monolithic reference | 100 | 00 | 1.968396160e-03 | 2.192999104e-03 | 6.778213230e-04 | -2.192854349e-03 |
| scalar factorized control vs Cartesian monolithic reference | 100 | 10 | 7.159001413e-03 | 8.372297460e-03 | 2.542791348e-03 | -8.372160444e-03 |
| scalar factorized control vs Cartesian monolithic reference | 100 | 01 | 7.159018613e-03 | 8.372798996e-03 | 2.542890285e-03 | -8.372798996e-03 |

The interpretation is:

1. **Scalar monolithic recovery is excellent.**  
   At \(\omega=1\), all three mode discrepancies are below
   \(2.9\times10^{-7}\) in \(d_{\mathrm{TV}}\). At \(\omega=100\), the
   available common-step mode-00 and mode-10 discrepancies are
   \(2.68\times10^{-6}\) and \(1.33\times10^{-5}\). This validates the
   longitudinal core and the oscillator-channel realization independently of
   the spinor mechanism.

2. **Spinor recovery preserves every scientific sign and ordering.**  
   At \(\omega=1\), the largest individual curve discrepancy is
   \(2.18\times10^{-4}\). At \(\omega=100\), it is
   \(9.71\times10^{-3}\) for the first shell. The oscillator and Cartesian
   first-shell response contrasts agree more closely than the individual
   curves: the response \(d_{\mathrm{TV}}\) differs by only
   +0.690% at \(\omega=1\) and
   -2.354% at \(\omega=100\).

3. **The factorized scalar--Cartesian comparison is not a pure
   representation error.**  
   The Cartesian scalar archive used a monolithic Cayley map, while the
   factorized oscillator map is the authoritative scalar control. Their
   difference contains the known finite-step nonfactorization artifact and
   must not be labeled solely as \(\epsilon_{\mathrm{repr}}\).

The strong-confinement spinor representation discrepancy is not at the linear
solver floor and must remain an explicit error-budget component. Nevertheless,
the measured spinor first-shell response is over ten times larger than the
largest corresponding individual \(\omega=100\) representation discrepancy,
and its prompt/late signs agree with the Cartesian result. Time-step and shell
convergence are still required before a final quantitative uncertainty is
assigned.

## 86. Detector-generated source structure and shell diagnostics

For the spinor cases, the normalized no-click source diagnostics are:

| ω | mode | s↓(0) | max s↓ | s↓(10) | sφ(0) | max sφ | sφ(10) | s↑(0) | min s↑ | s↑(10) | max p_top | ∫r_K,omit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 00 | 0.000000 | 0.160662 | 0.160655 | 0.000000 | 0.155459 | 0.155451 | 2.000000 | 2.000000 | 2.160655 | 8.637e-13 | 3.772e-11 |
| 1 | 10 | 1.000000 | 1.126469 | 1.126469 | 0.000000 | 0.266925 | 0.266854 | 3.000000 | 3.000000 | 3.126469 | 1.874e-11 | 7.863e-10 |
| 1 | 01 | 1.000000 | 1.126469 | 1.126469 | 0.000000 | 0.266925 | 0.266854 | 3.000000 | 3.000000 | 3.126469 | 1.874e-11 | 7.863e-10 |
| 100 | 00 | 0.000000 | 0.003446 | 0.000636 | 0.000000 | 0.006692 | 0.001238 | 2.000000 | 2.000000 | 2.000636 | 3.851e-10 | 2.573e-05 |
| 100 | 10 | 1.000000 | 1.000021 | 0.992787 | 0.000000 | 0.089162 | 0.043202 | 3.000000 | 2.921448 | 2.992787 | 1.515e-08 | 1.021e-03 |
| 100 | 01 | 1.000000 | 1.000021 | 0.992787 | 0.000000 | 0.089162 | 0.043202 | 3.000000 | 2.921448 | 2.992787 | 1.515e-08 | 1.021e-03 |

The clean launch-null conclusions come from mode `00`:

\[
s_\downarrow(0)=0,\qquad s_\phi(0)=0,\qquad s_\uparrow(0)=2.
\]

After detector-present spinor evolution,

| \(\omega\) | \(\max s_\downarrow\) | peak time | \(\max s_\phi\) | peak time |
|---:|---:|---:|---:|---:|
| 1 | 0.160661707 | 9.9910 | 0.155459393 | 9.9890 |
| 100 | 0.003446303 | 2.4110 | 0.006692314 | 2.3960 |

The factorized and monolithic scalar controls retain their initial
\(s_\downarrow\), \(s_\phi\), and \(s_\uparrow\) values exactly, with maximum
deviations no larger than \(4.44\times10^{-16}\).

Therefore:

\[
\boxed{\text{the spinor detector generates nonzero downward and dephasing source structure, while the scalar detector does not}}.
\]

The temporal structure depends strongly on confinement. For the ground launch,
the \(\omega=1\) source curves build mainly through the delayed return history,
whereas the \(\omega=100\) source maxima occur near the prompt encounter and
then decrease. This is a source-level observation only; the causal
susceptibility kernel is required to determine how an actual downward or
dephasing channel changes the click law.

The top-shell populations are small at \(N=12\), but the omitted-boundary
coupling proxy is more demanding. Its largest accumulated value is

\[
\int_0^{10}r_{K,\mathrm{omit}}(t)\,dt
=
1.021440268423e-03
\]

for the \(\omega=100\) first shell. This quantity is not a probability and is
not added to the detector budget. It does show why the \(N=12\to16\) curve and
source convergence test cannot be skipped even though
\(\max p_{\mathrm{top}}\simeq1.5\times10^{-8}\).

## 87. Current Task-05 verdict

| Gate | Current decision |
|---|---|
| H200/CuPy production backend | **PASS** |
| 16 current single-case solver executions | **16/16 PASS** |
| independent single-case audit after documented threshold reconciliation | **16/16 PASS** |
| factorized scalar null at \(\omega=100\) | **PASS** |
| factorized scalar null at \(\omega=1\) | **PENDING — three cases missing** |
| monolithic \(O(h^2)\) artifact diagnosis | **SCIENTIFIC PASS** |
| exact requested fine-step `mode10` monolithic file | **PENDING — mode01 proxy present** |
| spinor baseline at \(\omega=1,100\) for `00,10,01` | **PASS** |
| spinor \(10/01\) isotropy | **PASS** |
| Cartesian--oscillator qualitative recovery | **PASS** |
| final quantitative representation/time/shell error budget | **PENDING** |
| detector-generated source activation | **PASS at source level** |
| spinor time-step refinement | **PENDING** |
| spinor \(N=12\to16\) shell convergence | **PENDING** |
| production-scale same-prefix rerun | **PENDING** |
| Task-06 aggregate independent loader | **PENDING** |

The precise overall decision is

\[
\boxed{\text{Task 05: PARTIAL SOLVER-LEVEL PASS; SCIENTIFIC FIRST-BLOCK RESULTS ESTABLISHED; BRANCH NOT CLOSED}}.
\]

No result in this section is a bath response. Task 05 remains zero ambient
bath. Nonzero \(s_\downarrow\) or \(s_\phi\) does not establish damping,
dephasing, heating, temperature dependence, or susceptibility.

## 88. Exact minimal remaining cluster campaign

The optional monolithic \(1.25\times10^{-4}\) pair is not needed because the
measured ratio is already \(3.982111\). To complete the frozen Task-05 solver
inventory, run exactly the following ten configurations.

### 88.1 Correct the four first-block omissions

```text
scalar_factorized, omega=1, mode=00, N=12, dt=1e-3,   T=10
scalar_factorized, omega=1, mode=10, N=12, dt=1e-3,   T=10
scalar_factorized, omega=1, mode=01, N=12, dt=1e-3,   T=10
scalar_monolithic, omega=100, mode=10, N=12, dt=2.5e-4, T=10
```

### 88.2 Spinor time-step refinement

```text
spinor, omega=100, mode=00, N=12, dt=2.5e-4, T=10
spinor, omega=100, mode=10, N=12, dt=2.5e-4, T=10
```

### 88.3 Spinor shell convergence

```text
spinor, omega=100, mode=00, N=8,  dt=5e-4, T=10
spinor, omega=100, mode=10, N=8,  dt=5e-4, T=10
spinor, omega=100, mode=00, N=16, dt=5e-4, T=10
spinor, omega=100, mode=10, N=16, dt=5e-4, T=10
```

After those ten runs, repeat one inexpensive factorized-scalar production case
with the identical automatically generated prefix and verify stable output
hashes. No existing valid case should be rerun unnecessarily.

Thus the remaining solver work is

\[
\boxed{10\ \text{new configurations}+1\ \text{same-prefix rerun}}.
\]

## 89. Updated Task-06 implementation and acceptance plan

Task 06 remains the next independent-loader task after Section 88 is complete.
The earlier reconstruction requirements in Sections 73--75 remain in force,
with the following updates required by the actual H200 storage layout.

1. **Recursive directory discovery.**  
   The current campaign uses separate numbered directories such as
   `4511.Oscillator_channel_detector_tests_*` rather than one `4070` directory.
   Task 06 must recursively discover candidate configuration files under
   `[ARCHIVE_PATH]`, and determine physics only from the configuration
   JSON.

2. **Strict identity and duplicate rejection.**  
   The loader must reject duplicate physical configurations, misleading
   prefixes, and the obsolete preliminary package identified in Section 78.

3. **Source-family verification.**  
   Full source hashes differ because the manual block and stage number differ.
   Task 06 must verify either exact allowed-field differences or the normalized
   computational-body fingerprint
   `6ece5eac6b9be0f0d6ec93fc53d82c35cc85b9c0f867ed5a4cd22544b1be65de`.

4. **Correct decomposed-closure gate.**  
   The independent loader must explicitly use and report
   \(10^{-11}\) for the decomposed probability closure, while retaining all
   principal roof-closure, telescoping, midpoint-positivity, monotonicity, and
   true-residual checks.

5. **Complete 22-case inventory.**  
   Task 06 must require the corrected 12 baseline cases, four monolithic cases,
   two spinor time refinements, and four new \(N=8,16\) shell cases, reusing the
   two matching \(N=12\) baselines.

6. **Cross-case gates.**  
   It must independently reconstruct the scalar nulls, the monolithic ratio,
   spinor time-step differences, \(N=12\to16\) shell differences,
   \(10/01\) isotropy, Cartesian--oscillator discrepancies, source curves,
   top-shell populations, and omitted-\(K\) proxies.

Only a complete Task-06 PASS changes the status to

\[
\boxed{\text{Task-05 branch fully closed}}.
\]

Tasks 07 and 08 must not interpret source activity as a physical environmental
response before that closure.

## 90. Current H200 case and hash registry

The table records every current case source hash, configuration hash, solver
output-manifest hash, and uploaded loader-share ZIP hash.

| case | source SHA-256 | configuration SHA-256 | solver output-manifest SHA-256 | loader-share ZIP SHA-256 |
|---|---|---|---|---|
| scalar_factorized_omega100_mode00_N12_dt5e-4_T10 | 83fc772848a565b421318a87514ee1d35a1cf53d653ac7c2435efea57f13d7b5 | 9c2836aa809d2fbfcb22fcafd638e52581b60e2eb58a0137d0e72ff7d24ac37b | 038e540df931008262504fb539aa78a4c28d61744cd7377c5d6d6bbeb7bbd993 | 091313da737a1b89b024dc8c19bb2f8d5fd61493c8b2a0f362d5cf0c10be46b7 |
| scalar_factorized_omega100_mode01_N12_dt5e-4_T10 | 57cd1775f892ee357099eab1b466f77f31b9dcb23dedcd30369a920011d842fb | 8f50b76561c5ed5418daf9ddd1e3b8f2294bb2fbc85c6de1227d63c0e8892d90 | ec218cb6709b5bbe2458118b39639b72af997a1200d1f26448e8a63db212ac0a | 7d9df8a368b9a6839349eb4b16488619643e31c78e1a4f9322ad16e5ab8920b3 |
| scalar_factorized_omega100_mode10_N12_dt5e-4_T10 | 569d1c3bc1548c4feb573bb6c5e549d5dfc6a648cedaa011a2affbc606fc7ae9 | f139bae9032e0f09d101e10beeee212fd7e1a8131c58d4c8af62fe18d8a28a0e | f8e9c7e88e465214c3ca27ebe356f0738d5bbc4115eee7e441f523c71030ab59 | 7bbcd94114e30ef99869fb15f49e2d7d94de857b5e48a770401a994b88f2529e |
| scalar_monolithic_omega100_mode00_N12_dt2p5e-4_T10 | 49d9a30e0807582c2c7de26057fcd5d08192cb32a4aa2dcf48ad688395111ca3 | c3ef7e51b148bf7a3f6c2c7c487558395819cd27aa6d807c67100482c66cb140 | ba3e167fa7d82a217c4da14a036613be7d1094ebf61f494d7c78daee549be920 | 532b1604c0a377d44b984ef4af3ae3b4572fe7f598e9eae0a6f2498c53156687 |
| scalar_monolithic_omega100_mode00_N12_dt5e-4_T10 | 5e203612a10cfce7f3b216b75adb0d7b4a114a8e292cc62b3439df90659d7c98 | cb3cbc7d11a360ede58f3a74bd998dd20f33e4d1ba8dcaccd917bfeb5376481a | 5c461d8e298ce5f5e64fe5b468c9c1b5d1011f39afec0397b57f3de9f2acd93a | f12d94efb4fef4381f95cbf55ebe5cde470625f6583df5e92c76330434e47227 |
| scalar_monolithic_omega100_mode01_N12_dt2p5e-4_T10 | a7999ef081c4ff0ff92853714fb8f7eb90747695917ec1f0fbd84fcd4883d509 | 037d53a57ca70aea3820ec6e84a7ca2ac4b4a7bae3f0ef75a38f40f67ecc8557 | 276f264985c330d8535aee00b69356b6b0cec36cbb7fc23d55ef9176e46a0a31 | 4e3f53c92d1c99271d158f62d6e47f3179f2b0448b5e9a03686e614496bbd39a |
| scalar_monolithic_omega100_mode10_N12_dt5e-4_T10 | 2120cfd425e3907f5851d372451d6f356ecaebd5c686c0619154cc3cd059a446 | ebfbc015e1372ae5ceb32ed2cbd01322b06ea32644816c195d42dec5dfa99993 | 1597b95ccbf85d25858ed20cec945536e4db72f287dea7a76f9682d5de75ee58 | c0c4829d7b520d1571cfe4aa0e3ec0798fa1f655c520fbbb64e6b414116d636c |
| scalar_monolithic_omega1_mode00_N12_dt1e-3_T10 | 1b2cc2548c93df66e084771b72bc2c61f3a4cb5df5271126a1853724b9d1f63a | 9baf630edf4a0e8643ffa71f99b86d9e9c7c71f431569d78b618fc66406eea83 | 447d2e0fcc1e4001558f52849d109afe4ae2d598fa5af1d4d1e328a67c8e8237 | 02ee947098046fe781be1f5ab4d9a7c9737b8582cc614124671bbdb722594f10 |
| scalar_monolithic_omega1_mode01_N12_dt1e-3_T10 | 7d701a0ebe5bc4e1707d50a944c7f2e12103ac95b99dc37500e916c2df0a20f7 | 30e49810677494be3d4965344fa8d8e585824f6230c65b2d06a9a4ff48c66d70 | f958851b70a7872b0a95f0ffbff3b07911dcf4ef7845af95f3c2d2ec100d4e95 | b39b7a55df9fffdc4f9f4806a01f3a610a304848c046ec6047f1c524343e617a |
| scalar_monolithic_omega1_mode10_N12_dt1e-3_T10 | 1b892cd15e62f9847993d5a19e175b5d8233f36fd08c3715462042de3ef82340 | 0ba4fc461df986106ceaeac1106656cab899d1246f86f1d2c8f8247eb7c15c66 | 58ee02e9fbd09a0fa6d01e7c425d96f0a4df93f024553ad6ec0a31dff26cb751 | 4b83099aeaa9e527a3c772de66b9b139c3236631a61e831a91c08a2947a2867d |
| spinor_omega100_mode00_N12_dt5e-4_T10 | 4e2dea899dca5f6b8a4c8be269c4c34baaf939b94690be1b734edc12937c0cc0 | 30b2b90e7142a3465622f1c38ed75e470279cbc19876f60683f235be74aa5562 | c5c08caef56f070ce85b66c82ef78c4f7c16eb2b5a925e10f1a08dfde0566633 | 1748e2558a65ed7b6d2ba9ec7393d67def996f80b3dfb0a565e93016cbe2f208 |
| spinor_omega100_mode01_N12_dt5e-4_T10 | d3ccc7657b17dd5a106e8cac6b0e131a7edb66b80ca80c23df587e8f1385a05b | 0826278b5d5350f241cb4475a048c02c8c9525a83f48ebe037410c3e7ee2d631 | a91b33d4d8b891319eff54e98a9603501bda7f014fd6639025e3f4b630ec026f | 55302d5bcd611d962103e108532cbc47c3343766e2676bd2c207c485b028f848 |
| spinor_omega100_mode10_N12_dt5e-4_T10 | f7327c640940d669ab91a5263fbd18dcc7c8364c3596f671251ee694b679de74 | adc3d0a78e34290e1f529461c90dcd76938db5800eda1b90529b81b194133841 | d41b64376d45f6e37d5291fb0c209afb9447320175d60c041c153ddb2c62087c | 3914ef2c3a01cb2a042f4d0f2961b4b3c3c8742c777dcf9540f1252e9a038642 |
| spinor_omega1_mode00_N12_dt1e-3_T10 | cff17e571467df29942da79c6f2c961d692d90ea1c7314979349208cef8bfcd4 | 7d02da64424514824970cd0bc0fe183805af177ac7cd1478380d2d52dc6a30fc | 2c152e83f35615a29e23efab33db825138c26a3c30c4546d4b7dab1f6ee647b9 | 31cde86bdd32c473ac060a56b7aeed3fb392b4738d02d37a923d9a06ea33de65 |
| spinor_omega1_mode01_N12_dt1e-3_T10 | 1e9cb7936429392d96900b95e96a33568d3a12f07bfaf1e00565baf8a9eeb8e0 | f7bbf7be7152a9810e26f733df2f83c05b38e47140428c0718fd3dae23233afe | 0bb38cecc6392cb0a3c20e0568fc5a9ecd2f8168a456e321d802a8c0fde80153 | b903d4834480973a3a547aae70af4f413e019dae6f611c97c3f082208c7d0aef |
| spinor_omega1_mode10_N12_dt1e-3_T10 | 0c23e7a2185f5f4b711d71069a79641e40a9c1c161d1d70f0f7d59ecc3272ae2 | 9767d36f5438580e0003ab29cfce56a588fb6c6cd137611eb9703a087f5eb5df | 73b44d68178aa1729eac23d5d8d48b28ad4f84b284c336d020c2dadfdcb8f0bf | 9c3f44192cddbceec2af51dcebe962dd7ff1f75a2997b08be6c1e0b82c5052f8 |

The outer submitted package hash is

```text
5ca14feae4662bada426cdf56143a8659a4cbfc73fa48ca982ccd357c10bd6db
```

and the obsolete preliminary inner ZIP hash is

```text
6ae84c3cd8e56229e98d76b445a5844ceb3d89817aa680edda867b061b4a0fb2
```

## 91. Current authoritative decision statement

The numerical programme now has:

1. a closed Cartesian detector branch through Audit 01;
2. a closed oscillator-operator and detector-free bath branch through Audit 04;
3. a production-capable H200/CuPy oscillator-channel detector solver;
4. a verified \(\omega=100\) factorized scalar null;
5. a verified quadratic monolithic artifact;
6. complete spinor baseline laws at \(\omega=1,100\);
7. verified \(10/01\) isotropy and detector-generated source activation;
8. an explicitly measured Cartesian--oscillator representation discrepancy.

The remaining work is narrowly defined: four corrected first-block cases, six
spinor convergence cases, one deterministic rerun, and the aggregate Task-06
loader. The weak-environment susceptibility phase remains scientifically
blocked until those gates pass.

\[
\boxed{
\begin{aligned}
&\text{Audits 00--04: closed.}\\
&\text{Task-05 H200 solver and executed cases: numerically healthy.}\\
&\text{Task-05 frozen campaign: incomplete.}\\
&\text{Task-05 branch: not closed.}\\
&\text{Next action: execute the ten cases in Section 88, then Task 06.}\\
&\text{No detector--bath susceptibility has yet been calculated.}
\end{aligned}
}
\]

# Part XVII — Task-06 independent aggregate audit and qualified PASS

## 92. Exact meaning of the Task-06 decision

Task 06 is an independent aggregate loader/auditor for the Task-05 zero-bath
oscillator-channel outputs. It does not import or execute the Task-05 solver,
does not perform Cayley/GMRES propagation, and contains no bath rates,
Lindblad evolution, density-matrix propagation, trajectories, temperature, or
susceptibility. It reconstructs hashes, configurations, operators, probability
budgets, source diagnostics, and cross-case metrics directly from saved
products.

The latest compact audit package is

```text
Task06_diagnostic_share (3).zip
SHA-256: 6831034f4a90b2de3a2d99a4735af7c09262127be26c46d3c16999aedbd54705
```

The executing automatic Jupyter/cluster-safe loader is

```text
06_oscillator_channel_detector_loader_JUPYTER_SAFE_V5_AUTO.py
SHA-256: 8cef04ce37152165f54fca6e5eaaf740a2d630c22e60d8832b0dff9fcc6aa94a
```

The larger full-share archive is retained only as raw provenance:

```text
Task05_Task06_share (3).zip
SHA-256: c29ff86a4be7eba6146ab1fea55b124a533afb0fa17ea223fdcfe9035cb0532a
```

It is overinclusive and should not be used for routine sharing; the diagnostic
ZIP is the compact authority.

The Task-06 outcome is separated into two statements:


a. **Task-06A — available-data independent audit:** **PASS**.  
All load-bearing numerical and scientific conclusions supported by the
available accepted data are independently reproduced.

b. **Task-06B — original complete-campaign closure:** **PENDING**.  
The frozen 22-case inventory, Stage-01 cluster provenance, and representative
same-prefix rerun are not yet complete.

Thus this document does not relabel the raw loader exit code 2 as a full
campaign PASS. It records that the raw `FAIL` is caused by inventory and
provenance classification, not by a detected physical or numerical defect in
the accepted results.

## 93. Task-06 discovery and integrity result

The latest aggregate discovery found:

| Item | Result |
|---|---:|
| valid Task-05 configurations discovered | 23 |
| frozen required configurations | 22 |
| missing required configurations | 4 |
| valid extra configurations | 5 |
| invalid candidate configurations | 1 |
| duplicate physical configurations | 0 |
| obsolete/preliminary configurations excluded | 4 |
| baseline-family cases passing independent raw audit | all applicable cases |
| convergence-family cases numerically healthy but rejected by frozen GMRES-family gate | 3 |
| total GMRES failures in accepted numerical data | 0 |

The one invalid candidate is an optional mode-01, `N=16` case whose filename
prefix contains an extra `_N=16` suffix. It must be quarantined or regenerated
with the canonical prefix; it is not used as evidence.

The available numerical envelope is:

| Quantity | Worst available value |
|---|---:|
| maximum true relative residual | `5.120947362486e-10` |
| required true-residual tolerance | `1e-8` |
| maximum relative roof-closure residual | `4.015179382953e-10` |
| maximum absolute decomposed closure residual | `9.077183449335e-13` |
| independent decomposed-closure tolerance | `1e-11` |
| maximum survival increase | `6.715428213511e-11` |
| accepted survival guard | `2e-9` |
| minimum midpoint roof probability | `5.438868791623e-177` |
| maximum normalized top-shell population | `1.750096076849e-07` |

No accepted case shows a failed Krylov solve, negative midpoint detector
probability, probability leakage, nonfinite array, incorrect roof sign, active
bath code, or invalid source launch identity.

## 94. Reconciliation of the two solver families

The original baseline family uses

```text
GMRES_RTOL = 1e-8
```

and the later convergence family uses

```text
GMRES_RTOL = 1e-10
```

because one strong-confinement spinor convergence attempt triggered the
contractivity guard with the looser tolerance. Direct source comparison shows
that, after normalizing only

- the manual physical case assignments;
- the stage-directory assignment;
- the script-version string; and
- `GMRES_RTOL`,

all three inspected sources have one identical executable AST fingerprint:

```text
3740e983a22a65c3758b8ce071ec6d57957a1297b9edd9a11a0257f4f351d0e5
```

The source hashes are

```text
baseline N=12 source: 4e2dea899dca5f6b8a4c8be269c4c34baaf939b94690be1b734edc12937c0cc0
N=8 convergence source: 4be3c73c64e7e8d3edea1c58899a8ff721edd198943645138cac03cc20c2e8fc
N=16 convergence source: a7d9a79ae9ece5d37bd4ff3634574c01339bd1924b55a0d697671b9b1165d70f
```

No Hamiltonian, complete-shell construction, tensor ordering, `K_N`, roof
term, midpoint probability, source diagnostic, or physical convention differs.
The raw Task-06 source-family FAIL is therefore a conservative provenance gate,
not a physics failure. Future Task-06 revisions must represent these as two
explicitly audited numerical families rather than silently forcing one GMRES
value.

## 95. Scientific results independently established by Task 06

### 95.1 Factorized scalar null

At both confinements,

```text
omega=1:   dTV(10,00)=1.778675745506e-13
omega=1:   dTV(01,00)=1.778675745506e-13
omega=100: dTV(10,00)=1.109654946820e-13
omega=100: dTV(01,00)=1.109654946820e-13
```

All values satisfy the predeclared `1e-11` gate. The factorized scalar map is
the authoritative finite-step scalar control.

### 95.2 Monolithic scalar artifact

```text
R_h       = 5.226405658793e-03
R_h/2     = 1.312471093947e-03
R_h/R_h/2 = 3.982111059739
```

The ratio lies inside `[3.5,4.5]`. The monolithic response is an
`O(Delta t^2)` numerical nonfactorization artifact and is not a physical
scalar transverse response. The optional `1.25e-4` pair is not required.

### 95.3 Spinor directional isotropy

```text
omega=1:   dTV(10,01)=8.514610309610e-14
omega=100: dTV(10,01)=3.773406682439e-14
```

The `10/01` degeneracy is at the floating-point/Krylov floor.

### 95.4 Confinement-enhanced spinor preparation response

For mode `10` relative to `00`,

| Quantity | omega=1 | omega=100 |
|---|---:|---:|
| complete-law `dTV` | `2.0305668e-02` | `1.0228428e-01` |
| `Delta S(10)` | `+1.9929688e-02` | `+6.5129663e-02` |
| `Delta D(10)` | `-1.9929688e-02` | `-6.5129663e-02` |
| `Delta mu*` | `+1.24875908e-01` | `+5.56231775e-01` |
| `Delta D_E` | `-1.0974354e-02` | `-8.0919229e-02` |
| `Delta D_L` | `-8.955334e-03` | `+1.5789566e-02` |

The complete-law response is larger by a factor approximately `5.03723` at
`omega=100`. The strong-confinement result suppresses prompt clicks while
increasing the late-return sector.

### 95.5 Detector-generated source structure

For a ground-mode launch,

```text
s_down(0)=0,  s_phi(0)=0,  s_up(0)=2.
```

The factorized scalar source curves remain at the numerical floor. The spinor
curves become nonzero:

| omega | max s_down | max s_phi |
|---:|---:|---:|
| 1 | `1.606617074446e-01` | `1.554593927920e-01` |
| 100 | `3.446303075620e-03` | `6.692314341515e-03` |

This is a zero-bath source-activation result. It does not establish physical
damping, dephasing, heating, temperature dependence, or susceptibility.

## 96. Mode-00 shell-convergence result

The newly available `omega=100`, mode-00 shell cases are numerically healthy.
The independently reconstructed values are:

| N | S(10) | max top-shell population | accumulated omitted-K proxy |
|---:|---:|---:|---:|
| 8 | `0.4862772476322063` | `1.750096076849e-07` | `7.564831626975e-03` |
| 12 | `0.4861790483694784` | `3.851015726510e-10` | `2.573120697912e-05` |
| 16 | `0.4861789721099507` | `4.120675815534e-13` | `3.760486736017e-08` |

The complete-law and source differences are:

| Comparison | dTV | W1 | max abs(Delta S) | abs Delta mu* | max Delta s_down | max Delta s_phi | max Delta s_up |
|---|---:|---:|---:|---:|---:|---:|---:|
| N=8 to 12 | `1.020191456900e-04` | `6.825413307930e-04` | `1.007154029862e-04` | `6.825393284497e-04` | `3.193856029796e-06` | `2.573145252933e-05` | `4.919687825122e-06` |
| N=12 to 16 | `8.965075861779e-08` | `4.511735678960e-07` | `7.626012227258e-08` | `4.437203990904e-07` | `8.112418280973e-09` | `1.149293349430e-07` | `1.347343969726e-08` |

Thus the mode-00 detector law and source curves are extremely well converged at
`N=12`. The omitted-boundary-coupling proxy improves by about three orders of
magnitude in each shell enlargement.

The corresponding mode-10 shell family and both `dt=2.5e-4` spinor cases are
still absent. Therefore the full quantitative error budget is not yet closed.

## 97. Current authoritative gate table

| Gate | Decision |
|---|---|
| Audits 00--04 | **CLOSED** |
| Required Task-05 baseline/scalar block | **COMPLETE AND PASS** |
| Task-06 independent loader implementation | **PASS** |
| Task-06 available-data numerical/scientific audit | **QUALIFIED PASS** |
| Factorized scalar null at omega=1,100 | **PASS** |
| Monolithic quadratic artifact diagnosis | **PASS** |
| Spinor baseline and 10/01 isotropy | **PASS** |
| Detector-generated source activation | **PASS AT SOURCE LEVEL** |
| Mode-00 N=12 to 16 shell convergence | **PASS** |
| Mode-10 N=8,12,16 shell convergence | **PENDING** |
| Spinor dt=5e-4 to 2.5e-4 refinement, modes 00 and 10 | **PENDING** |
| Stage-01 cluster archive hash/reconstruction | **PENDING ADMINISTRATIVE INPUT** |
| Representative same-prefix independent rerun | **PENDING** |
| Full original 22-case Task-05/06 branch closure | **PENDING** |
| Physical detector-bath susceptibility | **NOT YET CALCULATED** |
| Task-07 development | **AUTHORIZED** |
| Final Task-07 production claim | **PROVISIONAL UNTIL FULL 05/06 CLOSURE** |

The exact residual Task-05 configurations are:

```text
spinor, omega=100, mode=00, N=12, dt=2.5e-4, T=10
spinor, omega=100, mode=10, N=8,  dt=5e-4, T=10
spinor, omega=100, mode=10, N=12, dt=2.5e-4, T=10
spinor, omega=100, mode=10, N=16, dt=5e-4, T=10
```

For a solver-family-consistent final convergence table, it is also desirable
to generate `N=12, dt=5e-4` convergence-family references at `GMRES_RTOL=1e-10`
for modes 00 and 10. No baseline scalar or omega=1 case needs repetition.

# Part XVIII — Authoritative Task-07 environmental-response handoff

## 98. Scientific scope

Task 07 is the first environmental-susceptibility solver. It computes the
linear response at **zero environmental rate**. It is not a finite-rate bath
simulation.

Task 07 must not contain:

- finite positive bath rates in the propagated reference;
- thermal occupations or a bath temperature;
- Monte Carlo trajectories;
- a second detector-loss channel;
- a CAP behind the direct ABC;
- full dense production density matrices;
- a claim that the Task-05 source curves themselves are damping or dephasing.

The reference no-click detector state remains

```text
Task-05 zero-bath factorized scalar or spinor trajectory.
```

The ambient directions enter only as first derivatives of a trace-preserving
transverse channel.

## 99. Authority order for Task 07

1. This master audit is the numerical workflow authority.
2. The accepted Task-05 source family is authoritative for the detector-only
   propagator, longitudinal grid, midpoint roof loss, oscillator ordering,
   `K_N`, and state vectorization.
3. Audit 02 is authoritative for the projected oscillator operators.
4. Audits 03--04 are authoritative for the finite projected bath dissipators,
   complete-shell correction, trace preservation, and channel conventions.
5. Task 06 is authoritative for the accepted zero-bath curves, scalar nulls,
   source activation, and current numerical error information.
6. The V5 manuscript and the rigorous implementation plan are authoritative
   for the response equations and physical interpretation.

## 100. Exact finite-dimensional response equations

For detector type `alpha` and environmental direction `r`, define

\[
\widetilde\rho_\alpha^{(0)}(t)
=e^{t\mathcal L_{\alpha,0}}\rho_0.
\]

The tangent state obeys

\[
\dot\sigma_{\alpha,r}(t)
=
\mathcal L_{\alpha,0}[\sigma_{\alpha,r}(t)]
+
\mathcal B_r[\widetilde\rho_\alpha^{(0)}(t)],
\qquad
\sigma_{\alpha,r}(0)=0.
\]

The response observables are

\[
\chi_{S,\alpha r}(t)=\operatorname{Tr}\sigma_{\alpha,r}(t),
\]

\[
\chi_{g,\alpha r}(t)
=
\operatorname{Tr}[G_{D,\alpha}\sigma_{\alpha,r}(t)].
\]

The exact first-order probability budget is

\[
\chi_{S,\alpha r}(t)
+
\int_0^t\chi_{g,\alpha r}(u)\,du
=0.
\]

The causal kernel is

\[
\chi_{g,\alpha r}(t)=\int_0^tK_{\alpha r}(t,s)\,ds.
\]

The insertion time `s` and detector-output time `t` must remain distinct.

## 101. Environmental directions and exact launch fingerprints

Use, in order,

\[
\mathcal B_\downarrow=\sum_{j=x,y}\mathcal D[a_j],
\]

\[
\mathcal B_\uparrow=\sum_{j=x,y}\mathcal D[a_j^\dagger],
\]

\[
\mathcal B_\phi=\sum_{j=x,y}\mathcal D[N_j].
\]

For a ground-state launch:

- downward source: exactly zero at launch;
- number-dephasing source: exactly zero at launch;
- upward source: nonzero at launch and linked to the first-shell coefficient.

The cleanest first new physics test is therefore

```text
factorized-scalar downward null -> spinor downward response.
```

A nonzero spinor downward response then probes detector-generated transverse
structure rather than an environmental change of the incident ground state.

## 102. Two independent numerical implementations

### 102.1 Reduced full-tangent benchmark

Use a deliberately reduced finite model, for example small `N_shell`, reduced
`N_z`, and short horizon, so that an explicit tangent density matrix is
tractable. This benchmark is for algebraic validation only and is not
production physics.

It must verify:

- trace-preserving insertion structure;
- tangent probability closure;
- scalar null response;
- Hermiticity of the tangent state;
- low-rank versus full-density agreement.

### 102.2 Production low-rank wave-function insertion

For one dissipator `D[L]`, define

\[
|u_{t,s}\rangle=W_{t-s}L|\psi(s)\rangle,
\qquad
|w_{t,s}\rangle=W_{t-s}L^\dagger L|\psi(s)\rangle.
\]

Then

\[
K_L(t,s)
=
\langle u_{t,s}|G_D|u_{t,s}\rangle
-
\operatorname{Re}
\langle\psi(t)|G_D|w_{t,s}\rangle.
\]

Both the jump and anticommutator terms are mandatory. A jump-only calculation
is not trace preserving and is invalid.

No full dense production density matrix is saved.

## 103. Insertion-grid rule

The sparse selected Task-05 insertion vectors at

```text
0, 2, 10/pi, 3.6, 5, 7.5, 10
```

are sufficient for source sanity checks and mechanism localization, but they
are not by themselves a converged quadrature for the complete susceptibility.
Task 07 must construct its own manual insertion grid and demonstrate
quadrature convergence by refinement.

The implementation should support batched/block GPU propagation and avoid
writing all intermediate branch vectors to disk. Save only:

- converged response curves;
- compact kernel slices or a compressed kernel grid;
- selected insertion vectors needed for audit;
- error and convergence summaries.

## 104. Minimal Task-07 development sequence

### T07-0 — source, ordering, and detector-reference recovery

- compile and AST-audit the source;
- reconstruct all complete-shell and roof-sign identities;
- load or reproduce the selected Task-05 zero-bath reference;
- verify identical `S(t)`, `g(t)`, and source curves before any insertion.

### T07-1 — reduced exact tangent benchmark

- small shell and longitudinal grid;
- scalar downward, spinor downward, and upward directions;
- full tangent density matrix versus low-rank insertion;
- no production claim.

### T07-2 — scalar pointwise null

For the factorized scalar detector require

\[
K_{\mathrm{sc},r}(t,s)=0
\]

at every sampled `(t,s)` within numerical tolerance, not merely after
integrating over `s`.

### T07-3 — spinor vacuum-damping susceptibility

Primary development case:

```text
omega=100, mode=00, N_shell=12, T=10.
```

Report prompt/late insertion support and the complete response law.

### T07-4 — upward susceptibility

Use the exact launch source and compare the short-time response with the
Task-05 first-shell static coefficient.

### T07-5 — number-dephasing susceptibility

Proceed only after downward and upward channels pass. Verify that the effect is
coherence sensitive and not a population-change proxy.

### T07-6 — confinement and convergence controls

- repeat the decisive directions at `omega=1`;
- refine insertion quadrature;
- compare `N=12` with `N=16` when the missing convergence-family references
  are available;
- retain solve, shell, time-step, and representation errors separately.

## 105. Minimal Task-07 case order

The efficient first sequence is

```text
1. scalar_factorized, omega=100, mode=00, downward   [exact null]
2. spinor,            omega=100, mode=00, downward   [main new result]
3. scalar_factorized, omega=100, mode=00, upward     [exact null]
4. spinor,            omega=100, mode=00, upward
5. scalar_factorized, omega=100, mode=00, dephasing  [exact null]
6. spinor,            omega=100, mode=00, dephasing
7. omega=1 controls for the informative directions
```

Do not begin with a broad temperature or rate scan.

## 106. Required Task-07 outputs

For every explicit response case, save at minimum

```text
CASE_configuration.json
CASE_reference_audit.json
CASE_operator_audit.json
CASE_response_audit.json
CASE_times.npy
CASE_insertion_times.npy
CASE_chi_survival.npy
CASE_chi_click_density.npy
CASE_integrated_response.json
CASE_kernel_summary.npz
CASE_source_insertion_summary.npz
CASE_run_status.json
CASE_output_hashes.json
CASE_07_environmental_response_solver.py
```

For reduced full-tangent benchmarks, save a compact benchmark NPZ but never a
full production dense density-matrix history.

## 107. Task-07 acceptance gates

Task 07 receives solver-level PASS only if:

1. the zero-rate detector reference reproduces Task 05;
2. every environmental insertion is trace preserving;
3. tangent probability closure holds at integration accuracy;
4. factorized scalar susceptibilities and pointwise kernels converge to zero;
5. reduced full-tangent and low-rank calculations agree;
6. jump and anticommutator terms are both present;
7. insertion-time quadrature converges;
8. shell and time-step dependence are bounded;
9. the response is finite and all arrays have declared dtypes/shapes;
10. every nonzero claimed response exceeds the combined numerical uncertainty;
11. no finite-rate bath, trajectory, temperature, or detector double counting is present.

# Part XIX — Task-08 independent response loader

Task 08 is the independent loader/auditor for Task 07. It must not import or
execute Task 07 and must not accept the Task-07 PASS flag as evidence.

It must independently reconstruct:

- response-case identities and source hashes;
- zero-rate reference recovery;
- tangent probability closure;
- scalar pointwise-null kernels;
- low-rank versus full-tangent benchmark agreement;
- insertion-grid refinement;
- shell/time-step convergence;
- channel superposition;
- prompt/late response integrals;
- complete censored-law response norms;
- the full numerical uncertainty budget.

Task 08 must distinguish:

```text
nonzero detector-generated source
```

from

```text
nonzero environmental susceptibility.
```

Only a Task-08 PASS establishes the first physical detector--bath response.

# Part XX — Tasks 09 and 10: small-positive-rate validation

After Task 07 solver PASS and Task 08 independent PASS, implement the finite
positive-rate deterministic map

\[
\rho_{n+1}
=
\Phi_{B,\Delta t/2}
\circ
\mathcal T^{\mathrm{nc}}_{D,\Delta t}
\circ
\Phi_{B,\Delta t/2}[\rho_n].
\]

Use the first candidate accumulated actions

```text
epsilon_1 approximately 0.006283
epsilon_2 approximately 0.015708
```

only after cutoff-dependent activity is checked. For the complete censored law,
require the linear-response remainder ratio to approach four under rate
halving. Do not use negative rates. Trajectories remain secondary until the
deterministic map agrees with the tangent result.

# Part XXI — Longer-term structured programme

The efficient continuation is

```text
Task 07  weak environmental-response solver
Task 08  independent response loader
Task 09  small-positive-rate deterministic solver
Task 10  independent finite-rate loader
Task 11  static Gibbs preparation and limited temperature organization
Task 12  optional trajectories/nonlinear scans only when scientifically needed
Part II  microscopic detector plus detector reservoir and detector temperature
```

The three temperatures remain distinct throughout:

- `T_prep`: initial transverse preparation;
- `T_B`: ambient propagation bath;
- `T_D`: future microscopic detector reservoir, excluded from Part I.

# Part XXII — Current final authority statement

\[
\boxed{
\begin{aligned}
&\text{Audits 00--04 are closed.}\\
&\text{The required Task-05 baseline/scalar block is complete and passes.}\\
&\text{Task-06A available-data independent audit receives a qualified PASS.}\\
&\text{Mode-00 }N=12\to16\text{ detector/source convergence is excellent.}\\
&\text{The full original Task-05/06 campaign closure remains pending.}\\
&\text{Task-07 development is authorized.}\\
&\text{No physical damping, heating, dephasing, temperature effect, or}\\
&\text{detector--bath susceptibility has yet been established.}
\end{aligned}
}
\]

The immediate scientific target is the scalar-null-controlled, channel-resolved
spinor susceptibility, beginning with vacuum damping and validated against a
reduced exact tangent calculation.

