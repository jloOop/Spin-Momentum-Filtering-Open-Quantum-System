# Part-I Open-System ABC Project
## Authoritative Numerical Master Audit Through the Current Task-07/Task-08 Interim Results and the Frozen 4800–4807 Completion Campaign

**Project:** Environmental susceptibility of the spin–momentum absorbing-boundary detector  
**Audit date:** 8 August 2026  
**Scope:** effective Part-I scalar/spinor absorbing-boundary detector with an independent transverse trace-preserving environment  
**State of the project at this freeze:** the eight new Task-07 jobs numbered 4800–4807 have been prepared and verified but have **not yet been executed**. This document therefore records the project immediately before that completion campaign.

---

> **Current-status precedence notice.** Parts I–XIII of this document are the current workflow and interpretation authority. They supersede older status statements that Task 07 had not produced response data, that U3 was only a preflight, that the downward `FAIL` labels represented a broad solver failure, that every case required a second identical execution before scientific use, or that `4520...100_00_spinor` was the Task-05 `dt/2` reference. Historical files remain provenance records, but their obsolete workflow conclusions must not be revived.
>
> **No new scientific propagation was performed in preparing this audit.** The document consolidates the authoritative Markdown records, inspected source files, raw Task-07 case-share products, independent Task-08 products, and the frozen 4800–4807 production package already present in the project record.

## How to use this document in a new session

1. Read Parts I–III before interpreting any numerical result.
2. Treat the status table in Part II and the case register in Part VIII as the current inventory.
3. Use the frozen numerical conventions in Parts IV and VII when checking source or output drift.
4. Execute the 4800–4807 campaign exactly as specified in Part XI.
5. Run the Task-07 per-case loader after every new result, then the current Task-08 case-local audit.
6. After all canonical cases exist, run one project-wide Task-08 aggregate audit with curated Task-05 inputs and explicit supplemental insertion-refinement handling.
7. Do not begin finite-rate, thermal, broad-confinement, or microscopic-detector calculations until the zero-rate family and uncertainty gates in Part XII are closed.


# Part I — Evidence classes, authority hierarchy, and supersession rules

## 1. Evidence classes

The project record contains different depths of evidence. This audit preserves those distinctions.

| Class | Meaning | Current use |
|---|---|---|
| **A — raw and independently reconstructed** | Raw arrays, configurations, source copies, stable hashes, and independent reconstruction are available. | Audits 03–04; supplied Task-07 cases; current Task-08 case-local products; D2 insertion refinement; D4 time control; U3 full production. |
| **B — aggregate products and authoritative audit record** | Aggregate tables/reports and hash records are available, but the complete raw family was not reprocessed again in this session. | Task-05/06 campaign-level conclusions. |
| **C — documentary authority** | A higher-authority Markdown records a result or unresolved item, but the underlying complete share package is not in the immediate review set. | Residual Task-05/06 closure register, Stage-01 cluster-provenance items. |
| **D — frozen plan, not yet executed** | Source files, hashes, output paths, and run order are frozen, but no result exists yet. | Task-07 jobs 4800–4807. |

A Class-B or Class-C statement is not silently relabeled as a fresh Class-A reconstruction. A planned Class-D case is never reported as completed.

## 2. Current authority hierarchy

When sources conflict, use the following order.

1. **This 8 August 2026 master audit** — current workflow status, supersession, case inventory, accepted interpretation, and exact next actions.
2. **The 3 August 2026 numerical master audit** — authoritative historical record through Task-06 qualified PASS and the foundational gates for Task 07.
3. **Frozen `750.Reference(4).py`** — longitudinal grid, scalar roof row, Cayley/Crank–Nicolson structure, GMRES conventions, packet construction, and midpoint roof-loss primitive.
4. **Final Audit-02 solver/archive** — native complete-shell order, projected oscillator operators, physical-spin tensor order, and native finite operator \(K_N\).
5. **Accepted Stage-01 Cartesian archive** — Cartesian recovery targets and representation-comparison evidence.
6. **Representative Stage-01 script** — manual directory, replacement, atomic-write, and saving style only; it is not a source of current physics defaults.
7. **V7 manuscript** — current physical interpretation, equations, mathematical-status classification, and the genuine insertion-refinement requirement. V7 supersedes V5 wherever the older Task-07 handoff still names V5.
8. **Final Task-07 v8 numerical core and independent per-case loader** — implementation contract subordinate to items 1–7.
9. **Current Task-08 v2.6 loader** — read-only independent auditor. It is an auditing implementation, not an authority allowed to override the model, the matrix, or the declared error budget.

The previous master explicitly grants Task-05/06 a **qualified available-data PASS** while leaving full upstream campaign closure pending. A later Task-07 configuration string stating `FULL_PASS_CLOSED_BY_EXPLICIT_PROJECT_AUTHORITY_OVERRIDE` is implementation-local metadata and does not override the higher-authority master record.

## 3. Principal source and package fingerprints

| Artifact | SHA-256 | Status/role |
|---|---|---|
| Previous current master audit | `0ceecbbf22b01b0242946c75a9b18d018f248225b70e3614fe418057ba3f4b3b` | Historical workflow authority through Task 06. |
| Final Task-07 → Task-08 handoff | `d7f4a629c9b21bdf3508193a9a2c585b050c63371bcfd0aea14631f168f32536` | Final v8 operational contract and 15-case matrix. |
| Post-Task-07 analysis handoff | `a1aea6b5b1a94f1abf30ac7b4f9babf3f968fb68ff51d910956bbc60cc56088d` | Nonparametric analysis and next-stage rules. |
| V7 manuscript | `d0618e35c6b5432d8289e9feaf17206bd912fa9795e31d47ad1f96e5c520b7b7` | Current theory/interpretation authority. |
| Rigorous implementation review | `72861e45bb9ae7838ea4fec457582a346741522d80dad3574dae19d18f91d82c` | Finite-model rigor and implementation strategy. |
| Frozen `750.Reference(4).py` | `8cf2095b2d760a0b702c930fe5690fe762d08ad7c721a8c53b5ed498d1744009` | Longitudinal detector core. |
| Current Stage-01 transport ZIP | `78de3cfd545603d5247f64ac896ef206e2494388a3fef3a65f8fd5809230744d` | Repackaged wrapper; stable inner products control science. |
| Current Stage-02 transport ZIP | `95a632d00477deea4dd3fbbd6f139f7bfa0745050fc69d95811b7e411b5e6536` | Repackaged wrapper; final solver/archive identities remain authoritative. |
| Current Stage-03 transport ZIP | `573fc093ecf0519380bafa3dba05f1810e6fe80b72d74aadd6620ff8a861de19` | Raw detector-free bath certification package. |
| Current Stage-04 transport ZIP | `889a7158d63b3cb8d17ffa31b391d55d52da6d9e849ccfe276445ebfb5136649` | Independent Stage-03 loader package. |
| Current Stage-05 transport ZIP | `04be83bd79ddfbbebd61bc2a2937d5d6656bc3f484d1f08bb793fa5cb7f4203f` | Aggregate snapshot, not the complete raw cluster tree. |
| Stage-07 4736/4746 outer package | `b30abd3683d05c26f0b9b5b8130d1d5416ab9b41108088a98b574378076d60da` | Raw D2 insertion refinement and full U3 production. |
| Stage-08 4736/4746 outer package | `4c802f6b1e5076b051ac0ffe38261f9eb19c4229e9b315d8370b99aae6471536` | Case-local Task-08 products for those cases. |
| Stage-08 interim package | `94fe695aa10b5a72bb8bef46f0bcc1dd8f19990cb745590f63fe2b8070ade5e0` | Earlier case-local audit collection. |
| Corrected curated U3 Task-08 share | `38af7c888f705ea7c0e1976b1d8967f54090e817c0220d3188f89d06130162da` | U3 independently admissible with curated Task-05 inputs. |
| Final 4800–4807 Task-07 package | `eab4a7a0614c86ca8da1536d899193725ae53d658f6ad07e8abec16e29568fc9` | Frozen Class-D completion campaign. |
| Task-08 automatic recheck tool | `d95cbc3441a1bd93d3182100639e10e471cf56eb2da0b7a5aa840886c81fddf5` | Convenience wrapper around unchanged v2.6 loader. |

Outer transport ZIP hashes can change under repackaging or macOS metadata. Scientific provenance is controlled by the stable inner-file hashes, numerical-core hashes, configuration hashes, and output manifests.

## 4. Resolved contradictions and obsolete statements

| Earlier ambiguity | Current resolution |
|---|---|
| V5 named as theory authority in the 6 August handoff | V7 supersedes V5 for equations, physical interpretation, mathematical status, and insertion-refinement requirements. |
| Final Audit-02 native order versus Task-05/07 storage | Native order is shell ascending with \(n_x\) ascending and orbital\(\otimes\)spin. Task-05/07 uses shell ascending with \(n_x\) descending, spin-major, \(z\)-fast storage. Their physical equality is accepted only through the explicit audited unitary permutation. |
| `750` prose Robin sign versus implemented matrix | The implemented roof matrix, positive-loss identity, and V7 equation are authoritative: \(\partial_z\psi=i\kappa\psi\). The inconsistent prose sign is not used. |
| `4740` U3 folder contained only two preflight files | `4740` was deliberately run in `closure_preflight` mode under an older v7 source. It passed preflight but was not production. Full formal U3 is `4746`. |
| `4741` U2 appears complete | It is a scientifically useful diagnostic with `BRANCH_GMRES_RTOL=1e-12`; its numerical-core hash differs from the frozen `1e-10` family by that line. It does not fill formal U2. |
| D2/D4/D5/P5 saved `FAIL` labels | Their primitive failure is the internal `0.1 ↔ 0.2` insertion-coarsening gate. Structural, solver, causality, trace, and low-rank checks pass. For downward, the genuine `0.1 → 0.05` refinement resolves the issue. |
| Every Task-07 case must be run twice | D3 is the representative deterministic certification. Under the adopted resource-saving default, other cases can be scientifically admissible with rerun pending when all solver and independent-loader checks pass. Rerun coverage is reported separately. |
| Running Task 08 inside different folders generated identical outputs | That was v2.5 project-root scanning with notebook-local output. v2.6 strict case-local input is the current behavior. |
| U3 Task-08 `FAIL_INPUT_INTEGRITY` | Broad Task-05 discovery mixed accepted `4520` with historical `4070`. Curated inputs resolve this; corrected U3 is `RERUN_PENDING`, scientifically admissible, with no failed checks. |
| `4520...100_00_spinor` used for the `dt/2` Task-05 reference | Incorrect. The correct \(\omega=100,N=12,dt=2.5\times10^{-4}\) mode-00 Task-05 directory is `4515...100_00_spinor`. `4520...1_00_spinor` remains the \(\omega=1,dt=10^{-3}\) reference. |
| \(N=12\) means a small 12-mode calculation | False. \(N=12\) is a complete-shell cutoff containing 91 orbital modes, 182 spin channels, and 273,000 complex amplitudes with \(N_z=1500\). |


# Part II — Current executive status and decision

## 5. Stage/task dashboard

| Stage or task | Scientific purpose | Current evidence | Current decision |
|---|---|---|---|
| Audit 00 | Detector-only Cartesian reference | Prior raw/reference audit | **Accepted for declared pilot/reference scope** |
| Audit 01 | Twelve Cartesian zero-bath mode cases | Complete archive | **Complete for declared scope** |
| Audit 02 | Complete-shell oscillator operators and \(K_N\) | Solver/loader 22/22 | **Closed** |
| Audit 03 | Detector-free projected bath solver | Raw 32/32 | **Closed** |
| Audit 04 | Independent Stage-03 loader | Independent 32/32 plus tamper tests | **Closed; bath branch certified** |
| Task 05 | Zero-bath oscillator-channel detector and source diagnostics | Required baseline/scalar science and mode-00 convergence supported; residual historical campaign items remain | **Available-data science PASS; full campaign closure pending** |
| Task 06 | Independent Task-05 aggregate audit | Available-data reconstruction PASS; original inventory/provenance closure incomplete | **Qualified PASS** |
| Task 07 | Zero-rate channel-resolved environmental response | v8 core validated; multiple raw cases complete; downward convergence diagnosed and refined | **Active; substantial results, family matrix incomplete** |
| Task 08 | Independent response audit | v2.6 case-local audit working; no final family aggregate PASS | **Incremental only; final aggregate pending** |
| Tasks 09–10 | Small positive-rate validation | No finite-rate products | **Not authorized yet** |
| Task 11 | Weak thermal combination | No completed all-channel family | **Deferred** |

## 6. Current project-level decision

The numerical backbone must **not** be restarted. There is no present evidence of a foundational error in the longitudinal ABC, Cayley map, oscillator ordering, the spinor roof term, bath dissipators, tangent equation, or low-rank insertion algebra.

The current project state is:

- the scalar factorized null is strongly supported;
- a nonzero downward spinor susceptibility is robust within the presently reconstructed Task-07 discretization family;
- the upward channel has a much larger opposite-sign candidate response, but still requires formal U2, U4, and genuine insertion refinement;
- the dephasing channel has a plausible nonzero candidate, but the principal baseline and controls are still missing;
- the final 15-role Task-08 family and full uncertainty budget are incomplete;
- eight precisely defined Task-07 runs are frozen to close the remaining canonical and insertion-refinement gaps.

The immediate authorized sequence is

\[
\boxed{
4800\text{--}4802
\;\longrightarrow\;
\text{Task-07 and Task-08 local checks}
\;\longrightarrow\;
4803\text{--}4807
\;\longrightarrow\;
\text{final project-wide Task-08 audit}
}
\]

No broad \(\omega\)-scan, finite-rate scan, temperature scan, trajectory calculation, larger-shell campaign, or microscopic detector model should begin before that sequence is closed.


# Part III — Fixed physical model, mathematical status, and claim discipline

## 7. Organizing equation and monitored record

For detector type \(\alpha\in\{\mathrm{sc},\mathrm{s}\}\), the subnormalized no-click state is organized by

\[
\frac{d\widetilde\rho_\alpha}{dt}
=
\mathcal L^{\mathrm{nc}}_{\alpha,\mathrm{ABC}}[\widetilde\rho_\alpha]
+
\mathcal L^{\perp}_{\mathrm{env}}[\widetilde\rho_\alpha].
\]

The direct scalar or spinor ABC is the **only monitored detector**. The transverse environment is unobserved and trace preserving:

\[
\operatorname{Tr}\mathcal L^{\perp}_{\mathrm{env}}[X]=0.
\]

Therefore

\[
S_\alpha(t)=\operatorname{Tr}\widetilde\rho_\alpha(t),
\qquad
 g_\alpha(t)=-\dot S_\alpha(t),
\]

and every permanent reduction of the no-click trace belongs to the roof-click sector. Ambient jumps are not detector clicks.

## 8. Scalar and spinor detector distinction

The scalar roof law is

\[
\partial_z\psi=i\kappa\psi.
\]

The spinor entrance relation is

\[
\partial_z\Psi=(i\kappa I_2-K)\Psi,
\qquad
K=\frac{\sigma_xp_y-\sigma_yp_x}{\hbar}.
\]

In tangential Fourier space the branches are \(i\kappa\pm R\). The term \(i\kappa I_2\) supplies the positive absorptive part. The \(\pm R\) term is Hermitian, reactive, and coherent. It modifies reflection, mode conversion, spin–motion correlations, and later return phases; it is **not** another probability sink.

The scalar and spinor detectors have the same local positive loss operator in the finite channel model. Their different click laws arise because the coherent spinor roof term generates a different surviving no-click state.

## 9. Environmental directions

The three unit-rate response directions are

\[
\mathcal B_\downarrow=\sum_{j=x,y}\mathcal D[a_j],
\qquad
\mathcal B_\uparrow=\sum_{j=x,y}\mathcal D[a_j^\dagger],
\qquad
\mathcal B_\phi=\sum_{j=x,y}\mathcal D[N_j].
\]

For \(\rho_{00}=|0,0\rangle\langle0,0|\),

\[
\mathcal B_\uparrow[\rho_{00}]
=
\rho_{10}+\rho_{01}-2\rho_{00},
\]

while

\[
\mathcal B_\downarrow[\rho_{00}]=0,
\qquad
\mathcal B_\phi[\rho_{\mathrm{diag}}]=0.
\]

Thus upward excitation acts at launch. Downward relaxation and number dephasing become active only after detector-present spinor evolution creates or selects the relevant excitation or number-basis coherence. These source identities do not determine the final sign, magnitude, or temporal location of the click response.

## 10. Exact scalar null theorem

Group transverse motion and physical spin into \(\mathcal H_R\). If the scalar no-click map factorizes as

\[
\mathcal M^{\mathrm{nc}}_{\mathrm{sc},t}
=
\Phi^{\mathrm{nc}}_{z,t}\otimes\Phi^{\mathrm{TP}}_{R,t},
\]

then, at fixed longitudinal marginal,

\[
S_{\mathrm{sc}}(t)
=
\operatorname{Tr}_z\!
\left[
\Phi^{\mathrm{nc}}_{z,t}
\bigl(\operatorname{Tr}_R\rho_0\bigr)
\right],
\]

so every purely transverse trace-preserving preparation or channel leaves the scalar click-time marginal invariant. Task 08 must test the scalar kernel pointwise, not only after integration.

## 11. Finite-model authority

The unrestricted spinor boundary combined with unbounded oscillator jump operators is not promoted to a proved general continuum-semigroup theorem. The authoritative rigorous object is the projected and fully discretized finite conditional channel, where ordinary matrix positivity, Hermitian adjoints in orthonormalized coordinates, complete positivity, trace preservation of the ambient part, and trace nonincrease of the detector part are explicit.

Claims in this project must be classified as one of:

- exact continuum scalar result under stated assumptions;
- exact boundary identity;
- exact projected or fully finite result;
- standard reduced GKSL/Davies model under declared approximations;
- defining model assumption;
- controlled numerical approximation;
- hypothesis requiring further numerical evidence.

A finite-model result must not be relabeled as an unrestricted continuum theorem.

## 12. Explicit exclusions

Part I does not contain:

- a CAP behind the direct ABC;
- a second roof-loss Lindblad operator;
- an explicit detector Hilbert space or detector reservoir;
- a detector temperature \(T_D\);
- finite-rate bath propagation in Task 07;
- Monte Carlo trajectories;
- direct spin relaxation/dephasing;
- longitudinal Brownian motion;
- a claim that environmental source activity equals detector susceptibility.


# Part IV — Frozen numerical conventions

## 13. Longitudinal grid and packet

The authoritative grid is the literal endpoint-excluded `float32` construction inherited from `750.Reference(4).py`:

\[
N_z=1500,
\qquad
L_z=20,
\]

\[
h_z=0.013333333656191826,
\qquad
z_{\mathrm{roof}}=19.986665725708008.
\]

The packet and detector parameters are

\[
z_0=10,
\quad
\sigma_z=0.5,
\quad
k_0=\kappa=\pi,
\quad
\theta=\frac{\pi}{6},
\quad
\phi=0,
\quad
T_{\mathrm{obs}}=10,
\quad
t_{\mathrm{cut}}=3.6.
\]

Here \(\sigma_z=0.5\) is the Gaussian **amplitude** width; the probability-density standard deviation is \(\sigma_z/\sqrt2\).

## 14. Scalar roof row and positive loss

For the last longitudinal node \(R\),

\[
(H_zu)_R
=
-\frac{1}{2h_z^2}u_{R-1}
+
\left(
\frac{1}{2h_z^2}
-
\frac{i\kappa}{2h_z}
\right)u_R.
\]

This is the implemented \(\partial_z u=i\kappa u\) law and satisfies

\[
i(H_z-H_z^\dagger)=\frac{\kappa}{h_z}P_R\ge0.
\]

The implemented matrix and loss identity take precedence over any inconsistent sign in a source docstring.

## 15. Cayley/Crank–Nicolson and GMRES

The detector step is

\[
A=I+\frac{i\Delta t}{2}H,
\qquad
B=I-\frac{i\Delta t}{2}H,
\qquad
A\psi_{n+1}=B\psi_n.
\]

Frozen conventions:

- complex128 matrix, state, and solve arithmetic;
- previous state or branch as `x0`;
- inverse diagonal of \(A\) as preconditioner;
- `atol=0`;
- restart 30;
- maximum iteration count 1000;
- post-solve bottom-Dirichlet assignment;
- Task-05 archival reference at its recorded accepted tolerance, commonly \(10^{-8}\);
- Task-07 response reference and every branch matched at \(10^{-10}\).

The two-reference architecture preserves exact Task-05 recovery while preventing the archival \(10^{-8}\) trajectory from limiting the bilinear tangent probability identity.

## 16. Midpoint detector probability

For a detector Cayley step,

\[
q_n=\frac{\psi_n+\psi_{n+1}}{2}.
\]

In the Cartesian representation,

\[
p_{D,n}
=
\Delta t\,\kappa h_xh_y
\sum_{x,y,\mathrm{spin}}|q_n(x,y,z_R)|^2.
\]

In the orthonormal oscillator-channel representation,

\[
p_{D,n}
=
\Delta t\,\kappa
\sum_{c=1}^{d_N}|q_{n,c}(z_R)|^2,
\]

with no \(h_xh_y\) factor. Integrated detector probabilities must be built from these nonnegative step effects, not from numerical differentiation of a sampled survival curve.

## 17. Complete-shell transverse representation

For cutoff \(N\),

\[
M_N=\frac{(N+1)(N+2)}2.
\]

| \(N\) | Orbital modes \(M_N\) | Spin-resolved channels \(2M_N\) | Full state entries at \(N_z=1500\) |
|---:|---:|---:|---:|
| 8 | 45 | 90 | 135,000 |
| 12 | 91 | 182 | 273,000 |
| 16 | 153 | 306 | 459,000 |

Audit-02 native order is shell ascending and \(n_x\) ascending inside each shell, with orbital\(\otimes\)physical-spin storage. Task-05/07 working storage is shell ascending, \(n_x\) descending, physical-spin major, oscillator-mode minor, and \(z\) fastest:

\[
\operatorname{index}(s,\mu,k_z)
=(sM_N+\mu)N_z+k_z.
\]

The explicit unitary permutation between the two representations is a mandatory operator audit.

## 18. Projected spin–momentum roof operator

\[
K_N
=
\frac{i}{\sqrt2\,\ell_\perp}
\left[
\sigma_x(a_y^\dagger-a_y)
-
\sigma_y(a_x^\dagger-a_x)
\right],
\qquad
K_N=K_N^\dagger.
\]

Ghost elimination produces the Hamiltonian roof block

\[
+\frac{K_N}{2h_z}.
\]

The sign is positive. Since \(K_N\) is Hermitian, it contributes no anti-Hermitian loss. The local detector-loss operator remains

\[
G_D=\frac{\kappa}{h_z}I\otimes P_R
\]

for both scalar and spinor channel models.

## 19. Task-07 response grid and observables

Canonical cases use

\[
\Delta s=0.1,
\]

giving 101 state nodes and 100 output panels. Supplemental genuine refinements use

\[
\Delta s=0.05,
\]

giving 201 nodes and 200 panels.

The response quantities are

\[
\chi_D(T)
=
\sum_p\chi_{p}
=
-\chi_S(T),
\]

\[
\chi_{\mu^*}(T)=\int_0^T\chi_S(t)\,dt,
\]

\[
\chi_{D,E}=\int_0^{3.6}\chi_g(t)\,dt,
\qquad
\chi_{D,L}=\int_{3.6}^{10}\chi_g(t)\,dt,
\]

and the complete signed censored-law norm

\[
\mathcal A_{\mathrm{TV}}^{(T)}
=
\frac12
\left[
\sum_p|\chi_p|+|\chi_S(T)|
\right].
\]

The complete-law norm and curve-level distances are primary convergence diagnostics. Agreement of one integrated scalar alone is insufficient.


# Part V — Audits 00–04: closed foundations

## 20. Audit 00 — detector-only references

The accepted Cartesian detector references use the same packet and roof detector with no ambient bath.

| \(\omega\) | \(\Delta t\) | \(S(10)\) | Detected fraction | \(\mu^*(10)\) | Peak time |
|---:|---:|---:|---:|---:|---:|
| 1 | \(10^{-3}\) | 0.1143121284532 | 0.8856878715468 | 4.257623567375 | 2.4535 |
| 100 | \(5\times10^{-4}\) | 0.4873590946645 | 0.5126409053355 | 6.603815786852 | 2.31875 |

The load-bearing checks passed: zero GMRES failures, exact telescoping probability closure, zero clamp loss, nonnegative midpoint roof probabilities, and roof/norm agreement at roughly \(4\times10^{-7}\) relative accuracy. A stricter diagnostic on signed total-step mass was not used as the detector law.

## 21. Audit 01 — complete twelve-case Cartesian static-mode library

The archive contains

\[
\{\mathrm{scalar},\mathrm{spinor}\}
\times
\{00,10,01\}
\times
\{\omega=1,100\}.
\]

| \(\omega\) | Detector | Mode | \(S(10)\) | Roof detection | \(\mu^*(10)\) |
|---:|---|---|---:|---:|---:|
| 1 | scalar | 00 | 0.093115786 | 0.906883865 | 4.127270744 |
| 1 | scalar | 10 | 0.093115800 | 0.906883845 | 4.127281186 |
| 1 | scalar | 01 | 0.093115800 | 0.906883847 | 4.127281188 |
| 1 | spinor | 00 | 0.114312133 | 0.885687526 | 4.257623723 |
| 1 | spinor | 10 | 0.134108708 | 0.865890958 | 4.381659569 |
| 1 | spinor | 01 | 0.134108708 | 0.865890965 | 4.381659595 |
| 100 | scalar | 00 | 0.093135024 | 0.906864525 | 4.129429267 |
| 100 | scalar | 10 | 0.093216174 | 0.906783365 | 4.135608573 |
| 100 | scalar | 01 | 0.093216189 | 0.906783496 | 4.135609211 |
| 100 | spinor | 00 | 0.487359059 | 0.512640647 | 6.603815304 |
| 100 | spinor | 10 | 0.556972408 | 0.443027327 | 7.183795674 |
| 100 | spinor | 01 | 0.556972491 | 0.443027396 | 7.183796787 |

The \(10/01\) degeneracy is numerical-floor accurate. The visible Cartesian scalar mode dependence at strong confinement is the known monolithic finite-step artifact; Task 05 supplies the authoritative factorized scalar null.

## 22. Audit 02 — projected operators and \(K_N\)

Audit 02 is closed at 22/22 gates. It establishes the projected ladder actions, adjoints, number operators, exact finite projected commutator, oscillator Bohr relations, transverse Hamiltonian, Pauli matrices, tensor ordering, and \(K_N\).

Selected fresh-execution metrics:

| Metric | Value |
|---|---:|
| Minimum measured Cartesian grid-convergence order | 1.962974 |
| Required minimum order | 1.9 |
| Maximum Cartesian wall-leakage metric | \(1.482597\times10^{-10}\) |
| Maximum \(\omega=1\) versus 100 scale-collapse defect | \(3.747003\times10^{-14}\) |
| Maximum complete-shell projected-identity defects | roundoff to \(\sim10^{-14}\) |

The Cartesian cross-check validates the low-mode realization with controlled second-order finite-difference error; it is not the native production representation.

## 23. Audit 03 — detector-free projected bath solver

The detector-free bath branch propagates the complete projected GKSL generator with all recycling terms. No clipping or trace renormalization is used. The solver passes 32/32 gates.

Selected numerical results:

| Test | Value |
|---|---:|
| Maximum propagated trace error | \(1.043610\times10^{-14}\) |
| Minimum density-matrix eigenvalue | 0 |
| One-quantum decay error | \(2.220446\times10^{-16}\) |
| Projected Gibbs generator residual | \(1.406763\times10^{-17}\) |
| Detailed-balance defect | \(6.661340\times10^{-16}\) |
| Dephasing coherence-law error | \(6.890150\times10^{-16}\) |
| B3 \(N=12\to16\) maximum trace distance | \(2.889802\times10^{-8}\) |
| Tight B3, \(N=12\), exact overflow | \(8.766369798856\times10^{-7}<10^{-6}\) |

The \(N=12\) bath-only overflow gate passes but with a modest margin; this acceptance is not automatically inherited by detector-present spinor dynamics.

Principal stable identities:

```text
Stage-03 solver:       5e621ee346604d8eef4765c07532ab3b525783af2b9a52d80fa408ef38c65bbe
Acceptance record:     6d90ee8db963a189471a9c7d099648244631fcaaf7269a7735e6b3ae3bc24b9a
Stable time series:    fe1a591de7c33fc8432888a4a36bb67c3798ee6328012df590628659eb8daa14
```

## 24. Audit 04 — independent bath-only loader

Audit 04 independently reconstructs Stage 03 and passes 32/32 refined gates. It verifies all stable hashes, reproduces solver decisions, confirms deterministic same-directory output, and detects both ordinary hash tampering and coordinated metric-plus-manifest tampering.

```text
Audit-04 loader:       cf0246ee8767dbb8862d637a4225952c9625392281d3856a616e69fea22c7d9c
Verified package:      0a658b07e6f32d292dce658b9288d196070c7b745db099622306fac7676e11a7
Loader audit:          d44c429c4a5fe42cfdd0c1ccd8884fb6eaf422423869ad64032171172b3df69b
Independent report:    52e73ce0c55c623091a0a96425b79d08ca0e8e3097cfc127aa2ded0d193a7e31
Case metrics:          ef105a722872716267d7ee8ac3c48dd70af7d3922960916fa3d603bb0d243b01
Cutoff metrics:        24022372f499bedc7248e93d6bd02ad01d49818f38ae1fa563d269c14feb6744
```

**Decision:** the detector-free bath branch is closed for its declared finite B0–B8 suite.


# Part VI — Task 05 and Task 06: qualified zero-bath detector foundation

## 25. Task-05 scope

Task 05 is strictly a **zero-ambient-bath** oscillator-channel detector calculation. It contains no active Lindblad bath, no density-matrix production propagation, no trajectories, and no finite-temperature evolution.

It implements:

1. `scalar_factorized` — authoritative scalar control;
2. `scalar_monolithic` — diagnostic finite-step nonfactorization map;
3. `spinor` — coupled-channel Cayley/GMRES propagation with \(+K_N/(2h_z)\).

## 26. Task-05/06 results supported by the authoritative aggregate record

### Factorized scalar null

```text
omega=1:   dTV(10,00) = dTV(01,00) = 1.778675745506e-13
omega=100: dTV(10,00) = dTV(01,00) = 1.109654946820e-13
```

### Monolithic scalar artifact

```text
R_h       = 5.226405658793e-03
R_h/2     = 1.312471093947e-03
ratio     = 3.982111059739
```

The ratio confirms the expected \(O(\Delta t^2)\) finite-step artifact. It is not physical scalar sensitivity.

### Spinor first-shell isotropy

```text
omega=1:   dTV(10,01) = 8.514610309610e-14
omega=100: dTV(10,01) = 3.773406682439e-14
```

### Ground-state source identities

```text
s_down(0) = 0
s_phi(0)  = 0
s_up(0)   = 2
```

### Mode-00 shell convergence

```text
N=12 -> 16 complete-law dTV = 8.965075861779e-08
survival W1                 = 4.511735678960e-07
max |Delta S|               = 7.626012227258e-08
|Delta mu*|                 = 4.437203990904e-07
```

The omitted-boundary-coupling proxy improves by roughly three orders of magnitude per shell enlargement.

## 27. Exact meaning of Task-06 status

- **Task-06A — available-data independent audit:** PASS.
- **Task-06B — original complete-campaign closure:** PENDING.

Historical discovery recorded 23 valid Task-05 configurations, 22 frozen required cases, four missing required cases, five valid extras, one invalid optional candidate, zero duplicate physical configurations, and zero GMRES failures in accepted data.

The historical missing list was:

```text
spinor, omega=100, mode=00, N=12, dt=2.5e-4, T=10
spinor, omega=100, mode=10, N=8,  dt=5e-4, T=10
spinor, omega=100, mode=10, N=12, dt=2.5e-4, T=10
spinor, omega=100, mode=10, N=16, dt=5e-4, T=10
```

The first item now exists operationally on ZIB as

```text
4515.Oscillator_channel_detector_tests_100_00_spinor
```

and is the Task-05 dependency for U4 and P4. This does **not** retroactively convert the old Task-06 record into a full PASS; the aggregate Task-06 inventory has not been re-executed here, and the mode-10 closure/provenance items remain outside the current Task-07 completion plan.

## 28. Task-05 references required by the current Task-07/08 work

| Physical reference | ZIB directory |
|---|---|
| Scalar factorized \(\omega=100\), mode 00, \(N=12\), \(dt=5\times10^{-4}\) | `4535.Oscillator_channel_detector_tests_100_00_scalar_factorized` |
| Spinor \(\omega=100\), mode 00, \(N=12\), \(dt=5\times10^{-4}\) | `4513.Oscillator_channel_detector_tests_100_00_spinor` |
| Spinor \(\omega=100\), mode 10, \(N=12\), \(dt=5\times10^{-4}\) | `4514.Oscillator_channel_detector_tests_100_10_spinor` |
| Spinor \(\omega=100\), mode 01, \(N=12\), \(dt=5\times10^{-4}\) | `4514.Oscillator_channel_detector_tests_100_01_spinor` |
| Spinor \(\omega=100\), mode 00, \(N=12\), \(dt=2.5\times10^{-4}\) | `4515.Oscillator_channel_detector_tests_100_00_spinor` |
| Spinor \(\omega=100\), mode 00, \(N=16\), \(dt=5\times10^{-4}\) | `4516.Oscillator_channel_detector_tests_100_00_spinor` |
| Spinor \(\omega=1\), mode 00, \(N=12\), \(dt=10^{-3}\) | `4520.Oscillator_channel_detector_tests_1_00_spinor` |
| Spinor \(\omega=1\), mode 01 | `4521.Oscillator_channel_detector_tests_1_01_spinor` |
| Spinor \(\omega=1\), mode 10 | `4522.Oscillator_channel_detector_tests_1_10_spinor` |

The current eight-run package also verifies the necessary manifests. No new Task-05 propagation is required before the 4800–4807 Task-07 campaign.


# Part VII — Final Task-07 v8 contract

## 29. Implementation identity

```text
Expected script version:
2026-08-05-task07-environmental-response-v8-unified-manual-full-production

Frozen numerical-core SHA-256:
827fd4993707152393a8adcf891df59d7b4d02310a06e89dd5263c0fd37369af

Final independent per-case-loader SHA-256:
3ec8f9699b2182ebd73e17e64bfbd6fc783df5d9e1ee9dc29cfd7f64c0f91d14
```

The full source hash changes when the manual case block or output folder changes. The numerical-core hash must remain fixed across the formal v8 family.

For reference:

- `4742_environmental_response_solver.py` is a genuine v8 source with core `827fd...`;
- `4741` has core `d665b9...` because its branch/reference tolerance is `1e-12`;
- `4740` and the local `4631` copy are older v7 sources with core `8625cb...`.

## 30. Exact finite-step object differentiated

Task 07 differentiates the implemented symmetric finite-step bath–detector composition:

\[
\mathcal S_{\epsilon,h}
=
\exp\!\left(\frac{\epsilon h}{2}\mathcal B_r\right)
\circ
\mathcal D_h
\circ
\exp\!\left(\frac{\epsilon h}{2}\mathcal B_r\right)
\]

at \(\epsilon=0\). It does not replace the implemented map by a different continuous-time propagator.

The tangent state satisfies, in continuous notation,

\[
\dot\sigma_{\alpha,r}
=
\mathcal L_{\alpha,0}[\sigma_{\alpha,r}]
+
\mathcal B_r[\widetilde\rho_\alpha^{(0)}],
\qquad
\sigma_{\alpha,r}(0)=0,
\]

with the exact response probability identity

\[
\chi_S(t)+\int_0^t\chi_g(u)\,du=0.
\]

## 31. Four phases per v8 invocation

1. Task-05 archival regression reference at the Task-05 case's own accepted tolerance;
2. matched Task-07 response reference at \(10^{-10}\);
3. embedded full-size selected-column closure pilot for spinor cases;
4. complete all-insertion response kernel.

The pilot ETA is only the phase-3 ETA. The complete kernel is not restart-checkpointed.

## 32. Two independent implementations

### Reduced full tangent

A deliberately small finite model propagates the explicit tangent density matrix. It certifies the algebra and is not a production physics point.

### Production low-rank insertion

For one dissipator \(\mathcal D[L]\),

\[
|u_{t,s}\rangle=W_{t-s}L|\psi(s)\rangle,
\qquad
|w_{t,s}\rangle=W_{t-s}L^\dagger L|\psi(s)\rangle,
\]

\[
K_L(t,s)
=
\langle u_{t,s}|G_D|u_{t,s}\rangle
-
\operatorname{Re}\langle\psi(t)|G_D|w_{t,s}\rangle.
\]

Both jump and anticommutator terms are mandatory. A jump-only environmental response is structurally invalid.

## 33. Required per-case outputs

```text
CASE_configuration.json
CASE_operator_audit.json
CASE_reference_audit.json
CASE_closure_pilot_audit.json
CASE_response_audit.json
CASE_times.npy
CASE_insertion_times.npy
CASE_chi_survival.npy
CASE_chi_click_density.npy
CASE_integrated_response.json
CASE_kernel_summary.npz
CASE_source_insertion_summary.npz
CASE_full_tangent_benchmark.npz
CASE_runtime_metrics.json
CASE_run_status.json
CASE_output_hashes.json
CASE_07_environmental_response_solver.py
CASE_stdout.txt
CASE_simulation_log.txt
```

The independent Task-07 per-case loader must then produce its audit JSON, metric/curve tables, compact NPZ, report, hash manifest, run status, full case-share ZIP, and diagnostic ZIP.

## 34. Rerun policy

D3 is the representative deterministic same-prefix certification for the repaired v8 implementation. Under the current resource-saving scientific policy:

- every unique case must be completed at least once;
- every local solver gate must pass;
- the independent per-case loader must have an empty failed-check list;
- a case can remain `RERUN_PENDING` when the only unresolved item is deterministic duplicate coverage or external family controls;
- reproducibility coverage is reported separately;
- one additional principal \(\omega=100\) spinor rerun is recommended after family convergence is closed, but 15/15 duplicate executions are not required for the default scientific audit.

An identical rerun tests reproducibility, not \(\Delta t\), \(N\), or \(\Delta s\) convergence.


# Part VIII — Frozen case matrix and current Task-07 result inventory

## 35. Canonical fifteen-case matrix

All canonical cases use mode 00, \(T=10\), and \(\Delta s=0.1\).

| ID | Detector | Direction | \(\omega\) | \(N\) | \(\Delta t\) | Role |
|---|---|---|---:|---:|---:|---|
| D1 | scalar factorized | downward | 100 | 12 | \(5\times10^{-4}\) | scalar exact null |
| D2 | spinor | downward | 100 | 12 | \(5\times10^{-4}\) | principal baseline |
| D3 | spinor | downward | 1 | 12 | \(10^{-3}\) | weak-confinement control |
| D4 | spinor | downward | 100 | 12 | \(2.5\times10^{-4}\) | time-step control |
| D5 | spinor | downward | 100 | 16 | \(5\times10^{-4}\) | shell control |
| U1 | scalar factorized | upward | 100 | 12 | \(5\times10^{-4}\) | nontrivial scalar null |
| U2 | spinor | upward | 100 | 12 | \(5\times10^{-4}\) | principal baseline |
| U3 | spinor | upward | 1 | 12 | \(10^{-3}\) | weak-confinement control |
| U4 | spinor | upward | 100 | 12 | \(2.5\times10^{-4}\) | time-step control |
| U5 | spinor | upward | 100 | 16 | \(5\times10^{-4}\) | shell control |
| P1 | scalar factorized | dephasing | 100 | 12 | \(5\times10^{-4}\) | scalar exact null |
| P2 | spinor | dephasing | 100 | 12 | \(5\times10^{-4}\) | principal baseline |
| P3 | spinor | dephasing | 1 | 12 | \(10^{-3}\) | weak-confinement control |
| P4 | spinor | dephasing | 100 | 12 | \(2.5\times10^{-4}\) | time-step control |
| P5 | spinor | dephasing | 100 | 16 | \(5\times10^{-4}\) | shell control |

Supplemental insertion controls D2-I, U2-I, and P2-I use the same physical/numerical baseline parameters except \(\Delta s=0.05\). They do not replace D2/U2/P2 silently.

## 36. Current inventory before the 4800–4807 campaign

| ID | Current evidence | Formal-v8 status | Local scientific interpretation | Next action |
|---|---|---|---|---|
| D1 | Legacy exact-zero package | Formal v8 missing | Useful diagnostic only | Run 4800 |
| D2 | Complete frozen-v8 canonical case | Present | Saved `FAIL` only from internal `0.1↔0.2` insertion gate | Preserve |
| D2-I | Folder 4736, frozen v8, \(\Delta s=0.05\) | Supplemental | Genuine insertion refinement PASS | Preserve and register externally |
| D3 | Complete frozen-v8 and duplicate-closed | **CLOSED** | Representative deterministic certification | No rerun |
| D4 | Complete frozen-v8 time control | Present | External time-step comparison PASS; local internal insertion gate fails | Preserve |
| D5 | Complete frozen-v8 \(N=16\) control | Present | Shell comparison PASS; local internal insertion gate fails | Preserve |
| U1 | Complete frozen-v8 scalar upward | Present | Scientific PASS, rerun pending | Preserve |
| U2 | Complete `1e-12` diagnostic | Formal v8 missing | Physics credible; not common-core family evidence | Run 4801 |
| U3 | Folder 4746 complete frozen-v8 | Present | Scientific PASS, rerun pending | Preserve |
| U4 | No formal result | Missing | Required time control | Run 4803 |
| U5 | Complete frozen-v8 \(N=16\) | Present | Scientific PASS, rerun pending | Preserve |
| P1 | Complete frozen-v8 scalar dephasing | Present | Exact zero, rerun pending | Preserve |
| P2 | No formal completed result | Missing | Principal baseline absent | Run 4802 |
| P3 | No formal result | Missing | Weak-confinement control absent | Run 4806 |
| P4 | No formal result | Missing | Time control absent | Run 4805 |
| P5 | Complete frozen-v8 \(N=16\) | Present | Candidate response; local internal insertion gate fails | Preserve pending P2 family |
| U2-I | Not yet run | Supplemental missing | Genuine upward insertion refinement required | Run 4804 |
| P2-I | Not yet run | Supplemental missing | Genuine dephasing insertion refinement required | Run 4807 |

## 37. Current reconstructed response metrics

| Case | \(\chi_D\) | \(\chi_{\mu^*}\) | Prompt \(\chi_{D,E}\) | Late \(\chi_{D,L}\) | \(\mathcal A_{\mathrm{TV}}\) | Insertion diagnostic |
|---|---:|---:|---:|---:|---:|---:|
| D2 | \(+2.80628456\times10^{-3}\) | \(-1.89322817\times10^{-2}\) | \(+1.91721801\times10^{-3}\) | \(+8.89066553\times10^{-4}\) | \(2.86558941\times10^{-3}\) | internal `0.1↔0.2`: 7.9052% |
| D2-I | \(+2.80653184\times10^{-3}\) | \(-1.89238164\times10^{-2}\) | \(+1.91375009\times10^{-3}\) | \(+8.92781750\times10^{-4}\) | \(2.85617762\times10^{-3}\) | external `0.1→0.05`: 2.6125% |
| D3 | \(+1.96390082\times10^{-3}\) | \(-7.74635883\times10^{-3}\) | \(+4.46700747\times10^{-4}\) | \(+1.51720007\times10^{-3}\) | \(3.77611979\times10^{-3}\) | internal: 0.9425% |
| D4 | \(+2.80725720\times10^{-3}\) | \(-1.89403553\times10^{-2}\) | \(+1.91793973\times10^{-3}\) | \(+8.89317469\times10^{-4}\) | \(2.86668254\times10^{-3}\) | internal: 7.8898% |
| D5 | \(+2.80623645\times10^{-3}\) | \(-1.89320395\times10^{-2}\) | \(+1.91718935\times10^{-3}\) | \(+8.89047099\times10^{-4}\) | \(2.86554597\times10^{-3}\) | internal: 7.9050% |
| U1 | \(+1.09305\times10^{-12}\) | \(+4.38640\times10^{-12}\) | numerical floor | numerical floor | \(9.05483\times10^{-13}\) | scalar null |
| U2 diagnostic | \(-5.27762984\times10^{-1}\) | \(+3.55718544\) | \(-4.19395163\times10^{-1}\) | \(-1.08367822\times10^{-1}\) | \(6.83641299\times10^{-1}\) | internal: 0.1588% |
| U3 | \(-1.62040359\times10^{-1}\) | \(+8.62262471\times10^{-1}\) | \(-5.89299941\times10^{-2}\) | \(-1.03110365\times10^{-1}\) | \(1.62249465\times10^{-1}\) | internal: 0.03820% |
| U5 | \(-5.27814570\times10^{-1}\) | \(+3.55749496\) | \(-4.19422893\times10^{-1}\) | \(-1.08391676\times10^{-1}\) | \(6.83683347\times10^{-1}\) | internal: 0.1588% |
| P1 | 0 | 0 | 0 | 0 | 0 | exact stored null |
| P5 | \(+4.57861069\times10^{-3}\) | \(-2.97437677\times10^{-2}\) | \(+2.90189544\times10^{-3}\) | \(+1.67671525\times10^{-3}\) | \(4.68533322\times10^{-3}\) | internal: 9.8075% |

These are zero-rate derivatives with respect to the corresponding rate coefficient. For example, \(\chi_D=-0.528\) does not mean a 52.8% finite-rate change; it is the linear coefficient in \(D(\Gamma)=D(0)+\Gamma\chi_D+O(\Gamma^2)\).


# Part IX — Detailed interpretation of the current response data

## 38. Structural health of the controversial cases

D2, D4, D5, and P5 each report several failed Boolean labels, but they have one primitive failed numerical condition: the response on \(\Delta s=0.1\) differs from the internally reconstructed \(0.2\) coarsening by more than 5%.

Their load-bearing structures pass:

- stable hashes and finite-array checks;
- Task-05 reference recovery;
- no GMRES failures and true residuals within tolerance;
- operator, ordering, and roof-sign audits;
- complete causal insertion-grid coverage;
- zero noncausal kernel entries;
- `K_total = K_jump + K_anti` at roundoff;
- source-trace cancellation around \(10^{-17}\);
- tangent probability closure around \(10^{-12}\)–\(10^{-11}\);
- independent per-insertion closure around \(10^{-12}\)–\(10^{-11}\);
- reduced full-tangent versus low-rank agreement around \(10^{-22}\) in the reduced benchmark.

The old `FAIL_CASE_LOCAL_NUMERICS` wording is technically correct under the original local gate but must not be interpreted as a broken Hamiltonian or tangent implementation.

## 39. Downward family

### Genuine insertion refinement

For D2,

\[
E_{0.2,0.1}=2.29868297\times10^{-4},
\]

whereas the genuine D2-I comparison gives

\[
E_{0.1,0.05}=7.48624816\times10^{-5},
\]

\[
\frac{E_{0.1,0.05}}{\mathcal A_{\mathrm{TV}}}=2.61246\%<5\%.
\]

The empirical order from the three levels is

\[
p_s=\log_2\!\left(\frac{E_{0.2,0.1}}{E_{0.1,0.05}}\right)=1.61849.
\]

The internally coarsened `0.1` products of the new `0.05` run reproduce the independently generated old D2 `0.1` products to approximately \(10^{-18}\). The result changed only because the insertion quadrature was refined.

### Detector time-step convergence

D2 versus D4 gives

\[
d_{\mathrm{TV}}=1.77331833\times10^{-5},
\qquad
\text{relative}=0.618596\%.
\]

The survival \(W_1\) difference is \(8.64988637\times10^{-6}\), and the integrated response scalars change by less than approximately 0.05%.

### Shell convergence

D2 versus D5 gives

\[
d_{\mathrm{TV}}=6.51474331\times10^{-8},
\qquad
\text{relative}=0.00227344\%.
\]

Thus

\[
\epsilon_N\ll\epsilon_{\Delta t}<\epsilon_{\Delta s}.
\]

Increasing beyond \(N=16\) is not a rational response to the present data.

### Downward error subtotal

Using the conservative linear sum of the currently measured complete-law distances,

\[
\epsilon_{s\text{-quad}}=7.48624816\times10^{-5},
\]

\[
\epsilon_{\Delta t}=1.77331833\times10^{-5},
\]

\[
\epsilon_N=6.51474331\times10^{-8},
\]

\[
\epsilon_{\mathrm{known}}=9.26608123\times10^{-5}.
\]

For the refined response norm \(2.85617762\times10^{-3}\),

\[
\mathcal A_{\mathrm{TV}}/\epsilon_{\mathrm{known}}\approx30.82.
\]

This is comfortably above the required evidence factor 5 **within the measured Task-07 error family**. It is not yet the publication-level total budget because inherited representation and longitudinal-grid bounds \(\epsilon_{\mathrm{repr}}\) and \(\epsilon_z\) have not been supplied to Task 08.

### Physical interpretation

The refined signs are stable:

\[
\chi_D>0,
\qquad
\chi_{\mu^*}<0.
\]

Infinitesimal downward relaxation increases detection before \(T=10\) and decreases restricted survival time in this setup. At strong confinement the net response is approximately 68.2% prompt and 31.8% late. D3 at weak confinement is approximately 77.25% late. The large shape difference shows that source activity and detector susceptibility are distinct and that confinement reorganizes the causal transfer.

**Current decision:** no further downward GPU run is scientifically mandatory before the family audit. D4-I or D5-I can be reserved for an explicitly stricter same-fine-grid policy; D2 at \(0.025\), D3 at \(0.05\), and \(N=20\) are not justified now.

## 40. Upward family

U1 is the strongest scalar control because the upward source is nonzero at launch while the factorized scalar response remains at the \(10^{-12}\) floor. The independent launch identity is

\[
K_\uparrow(p,0)=p_{10}(p)+p_{01}(p)-2p_{00}(p).
\]

For U3 it passes with maximum absolute difference \(5.25753856\times10^{-10}\) and relative difference \(3.78842255\times10^{-7}<10^{-6}\).

The current strong-confinement candidate has

\[
\chi_D\simeq-0.528,
\qquad
\chi_{\mu^*}\simeq+3.56.
\]

Thus weak upward excitation suppresses finite-window detection and increases restricted survival time.

The old `1e-12` U2 and formal-v8 U5 differ by only

\[
d_{\mathrm{TV}}=5.19353483\times10^{-5},
\qquad
\text{relative}=7.5964\times10^{-5},
\]

which strongly suggests shell stability. It is not the formal shell certificate because the numerical-core tolerance differs. Job 4801 supplies the common-core U2.

### Confinement changes temporal structure

U3 versus U5 gives

\[
d_{\mathrm{TV}}=0.56630209,
\qquad
\text{relative}=82.83\%.
\]

U3 is about 63.6% late in its net response, whereas U5 is about 79.5% prompt. The prompt magnitudes change by a factor about 7.12 from \(\omega=1\) to 100, while the signed late integrals differ by only about 5%. This does **not** mean the late dynamics are unchanged: large positive and negative late-time structures at strong confinement cancel in the signed integral.

The result is a causal/time-shape reorganization, not a single amplitude multiplied by a function of \(\omega\). Two confinement points cannot support a \(\sqrt\omega\), power-law, monotonic, or universal fit.

### Remaining upward requirements

- formal frozen-core U2: job 4801;
- U4 time control: job 4803;
- genuine U2 insertion refinement: job 4804;
- final family comparison against existing U5;
- final aggregate Task-08 budget.

## 41. Dephasing family

P1 is an exact scalar null. P5 is structurally healthy and suggests

\[
\chi_D>0,
\qquad
\chi_{\mu^*}<0,
\]

but its internal insertion coarsening difference is 9.8075%. There is no formal P2 baseline, no P3 confinement control, and no P4 time control in the current completed set.

The efficient closure sequence is therefore:

1. P2 baseline, job 4802;
2. P4 time control, job 4805;
3. P3 weak-confinement control, job 4806;
4. P2-I genuine insertion refinement, job 4807;
5. compare against existing P5 before deciding whether a fine P5 run is necessary.

A P5 `0.05` or \(N=20\) run is not justified before the P2 family comparison exists.


# Part X — Task 08: current implementation, correct interpretation, and remaining software contract

## 42. Current loader identity and scope

```text
Loader version:
2026-08-07-task08-independent-aggregate-loader-v2.6-case-local-jupyter-input

Copied-loader SHA-256:
c557cf5af72d29560397c582b81501d651709d0d60e888d0c8dc18888ef8967f
```

Task 08 is read-only, CPU/Jupyter safe, and must not import or execute Task 07 or the Task-07 per-case loader. It identifies physical cases from configuration metadata, verifies hashes, reconstructs raw arrays and response identities independently, and separates scientific validity from deterministic rerun coverage.

## 43. Case-local versus aggregate behavior

In strict case-local mode, one Stage-07 folder is the Task-07 input and the common curated Task-05 tree supplies dependencies. Fourteen roles normally remain `MISSING`. Therefore

```text
INCOMPLETE_REQUIRED_CASE_MATRIX
exit code 3
```

is the expected overall result for a healthy one-case audit.

Judge the selected row:

- `CLOSED` — scientific and deterministic closure;
- `RERUN_PENDING` with empty `failed_checks` — scientifically admissible, duplicate pending;
- `LOCAL_PASS` with empty `failed_checks` — local reconstruction passes, external controls pending;
- `FAILED` — an actual local integrity/numerical gate failed;
- current case `MISSING` — incomplete, wrong-core, or unmapped input.

## 44. Corrected U3 Task-08 result

The curated U3 run uses exact Task-05 inputs, including `4520`, `4521`, and `4522`, and yields

```text
U3 status:                 RERUN_PENDING
scientific_admissible:     True
failed_checks:             []
overall case-local result: INCOMPLETE_REQUIRED_CASE_MATRIX
```

This is the correct interpretation. The previous integrity failure was a duplicate-provenance discovery issue, not a U3 numerical failure.

A minor reporting inconsistency remains: the Markdown report says explicit authority-file verification is true while the configuration records `EMBEDDED_CONTRACT_ONLY`. This is a provenance/reporting wording issue, not a scientific-array issue.

## 45. Supplemental insertion-refinement gap

The current frozen 15-role mapper includes \(\Delta s=0.1\) in the exact role identity. Therefore D2-I at \(0.05\), and later U2-I/P2-I, can appear as `unmapped_configuration`.

A refinement-aware final audit must:

1. preserve the canonical 15 roles at \(0.1\);
2. define supplemental identities D2-I, U2-I, and P2-I;
3. match each supplemental case to its baseline using detector, direction, \(\omega\), mode, \(N\), \(\Delta t\), \(T\), and numerical core;
4. verify that the fine case's internally coarsened insertion response reproduces the independent canonical coarse case;
5. compare fine and coarse response laws on common output panels/nodes;
6. use the fine result as the preferred estimate and their complete-law distance as \(\epsilon_{s\text{-quad}}\);
7. retain the internal `0.1↔0.2` value as a diagnostic, not the final refinement gate.

Until this amendment exists, case-local audits of 4804 and 4807 are still useful for integrity, but `MISSING/unmapped` is not a physics failure.

## 46. Final aggregate input requirements

The final project-wide Task-08 execution must ingest:

- all fifteen canonical full Task-07 case-share packages;
- D2-I, U2-I, and P2-I supplemental packages;
- the D3 closed deterministic package;
- curated accepted Task-05 raw references, especially mode 00/10/01 upward identities;
- inherited nonnegative \(\epsilon_{\mathrm{repr}}\) and \(\epsilon_z\) bounds;
- the resource-saving rerun policy;
- explicit authority-file paths if the report is to claim runtime authority verification.

Only that aggregate can issue the finite-v8 zero-rate family verdict. Publication-level project closure remains additionally conditional on the residual upstream Task-05/06 register.


# Part XI — Frozen 4800–4807 completion campaign

## 47. Package identity

```text
Package:
Task07_Final_8_Run_Package_ZIB_4800_to_4807.zip

SHA-256:
eab4a7a0614c86ca8da1536d899193725ae53d658f6ad07e8abec16e29568fc9

Fixed output and Task-05 search root:
[ARCHIVE_PATH]
```

All eight sources compile and retain numerical-core SHA

```text
827fd4993707152393a8adcf891df59d7b4d02310a06e89dd5263c0fd37369af
```

## 48. Exact run register

| Order | Role | Script full SHA-256 | Configuration | Output directory |
|---:|---|---|---|---|
| 1 | D1 | `9a97dd8b6b3daf49b1a93c945d7c1138c50c1bd90d38d7b25a9da49e9107678f` | scalar downward, \(\omega=100,N=12,dt=5e-4,ds=0.1\) | `[ARCHIVE_PATH]` |
| 2 | U2 | `c049ef1ca6cd04289baca4d71dad23f9f52c7a3dd15391b616f6e4d30e66e1d7` | spinor upward, \(\omega=100,N=12,dt=5e-4,ds=0.1\) | `[ARCHIVE_PATH]` |
| 3 | P2 | `4e856e992ee98fb8b4468c8b412c2e6af3e28156835080050aea4217879f7d5f` | spinor dephasing, \(\omega=100,N=12,dt=5e-4,ds=0.1\) | `[ARCHIVE_PATH]` |
| 4 | U4 | `8ddbe40917e555380bab577d6ae30d484b5fb40c4ae31673e92525f70a7a4b6f` | spinor upward, \(\omega=100,N=12,dt=2.5e-4,ds=0.1\) | `[ARCHIVE_PATH]` |
| 5 | U2-I | `f2b7d5fa3419a4ccbe4509c75e5670a4d822a7c1de25f57d005edae901bfe8b2` | spinor upward, \(\omega=100,N=12,dt=5e-4,ds=0.05\) | `[ARCHIVE_PATH]` |
| 6 | P4 | `90ebba2207fefa77af363821d9489f3508758cb6bfb5fbcebf9879864024487d` | spinor dephasing, \(\omega=100,N=12,dt=2.5e-4,ds=0.1\) | `[ARCHIVE_PATH]` |
| 7 | P3 | `a9716136b9232c78e838112cd081406c8b52f9fb708f7917baf846abf944d477` | spinor dephasing, \(\omega=1,N=12,dt=1e-3,ds=0.1\) | `[ARCHIVE_PATH]` |
| 8 | P2-I | `b429edf96f3474fc1683c7bb8afc7a59889a102f421ba0d6fe23dceac2d14171` | spinor dephasing, \(\omega=100,N=12,dt=5e-4,ds=0.05\) | `[ARCHIVE_PATH]` |

## 49. Exact Task-05 overrides

| Job | Task-05 dependency |
|---|---|
| D1 | `4535...100_00_scalar_factorized` |
| U2, U2-I | `4513...100_00_spinor`, `4514...100_10_spinor`, `4514...100_01_spinor` |
| P2, P2-I | `4513...100_00_spinor` |
| U4, P4 | `4515...100_00_spinor` |
| P3 | `4520...1_00_spinor` |

All Task-05 inputs are read-only. Several GPU jobs may read the same reference concurrently.

## 50. Mandatory pre-submission checks

From the extracted package directory:

```bash
cd [ARCHIVE_PATH]

python verify_zib_task05_dependencies.py
python verify_zib_task05_manifests.py
python verify_task07_package.py
```

Required outcomes:

- Task-05 missing-directory count = 0;
- every required Task-05 output manifest matches;
- all eight Task-07 sources compile;
- all eight numerical-core hashes equal `827fd...`;
- folders 4800–4807 are unused before submission.

Do not edit any line below `# TASK-07 NUMERICAL CORE BEGINS HERE`.

## 51. Resource-efficient execution order

### Wave 1

```text
4800 D1
4801 U2
4802 P2
```

After completion, run the Task-07 per-case loader and current Task-08 case-local audit for each. Continue only if U2 and P2 have no structural failed checks. An insertion-only failure at \(\Delta s=0.1\) is not a reason to stop; U2-I/P2-I are already planned to resolve it.

### Wave 2

```text
4803 U4
4804 U2-I
4805 P4
4806 P3
4807 P2-I
```

This ordering avoids spending on family controls before the principal baselines are verified.

## 52. Stop/go logic

Proceed when Task-05 recovery, operator/permutation audits, pilot closure, source trace, causality, tangent closure, per-insertion closure, full-tangent/low-rank benchmark, and finiteness all pass.

Stop before dependent jobs if a baseline fails any structural gate. Do **not** stop solely because the baseline's internal `0.1↔0.2` insertion comparison exceeds 5%; that is precisely the role of the planned `0.05` run.

## 53. Per-case postprocessing

For every completed case:

1. verify that the log reached the complete `[kernel]` phase;
2. confirm 101/100 nodes/panels for \(ds=0.1\), or 201/200 for \(ds=0.05\);
3. run the final Task-07 per-case loader;
4. require an empty `failed_checks` list, except that an insertion-only gate can remain pending until the external fine case is compared;
5. preserve the full and diagnostic Task-07 ZIPs;
6. run Task-08 v2.6 case-locally;
7. retain exit code 3 as normal when only the family matrix is incomplete.

## 54. Task-08 automatic recheck

The automatic tool package has SHA

```text
d95cbc3441a1bd93d3182100639e10e471cf56eb2da0b7a5aa840886c81fddf5
```

It uses the unchanged v2.6 loader and curated Task-05 inputs. Case-local outputs are written to

```text
<Stage-07 folder>/4901.Task08_CaseLocal_Recheck
```

and the project aggregate to

```text
[ARCHIVE_PATH]
```

The unmodified v2.6 mapper can still leave 4804 and 4807 unmapped. Preserve those outputs; do not interpret unmapped supplemental cases as failed calculations.


# Part XII — Acceptance gates, uncertainty budget, and claim boundary

## 55. Frozen numerical gates

| Gate | Tolerance |
|---|---:|
| Operator identities and permutation | \(10^{-12}\) |
| Task-05 reference arrays | \(5\times10^{-11}\) |
| Task-05 source curves | \(5\times10^{-10}\) |
| Source trace | \(5\times10^{-11}\) |
| Launch fingerprint | \(10^{-12}\) |
| Embedded pilot closure | \(10^{-10}\) |
| Tangent closure | \(5\times10^{-10}\) absolute **or** \(10^{-7}\) relative |
| Independent per-insertion closure | \(5\times10^{-8}\) |
| Scalar pointwise kernel | \(5\times10^{-9}\) |
| Scalar integrated response | \(10^{-8}\) |
| Full tangent versus low rank | \(5\times10^{-10}\) absolute **or** \(10^{-7}\) relative |
| Insertion refinement | \(5\times10^{-9}\) absolute **or** 5% relative |
| Time-step family | \(5\times10^{-9}\) absolute **or** 5% relative |
| Shell family | \(5\times10^{-9}\) absolute **or** 5% relative |
| Upward static launch identity | \(5\times10^{-8}\) absolute **or** \(10^{-6}\) relative |
| Branch/reference true residual | \(10^{-8}\) |
| Resolved nonzero evidence | signal/error \(\ge5\) |

An OR gate passes only under the exact declared absolute/relative logic. Both raw values must be reported.

## 56. Required total error budget

For each claimed direction,

\[
\epsilon_{\mathrm{total}}
=
\epsilon_{\mathrm{repr}}
+
\epsilon_z
+
\epsilon_{\Delta t}
+
\epsilon_N
+
\epsilon_{s\text{-quad}}
+
\epsilon_{\mathrm{solve}}.
\]

Missing inherited bounds may not be set to zero. Task 08 must report `BUDGET_INCOMPLETE` until \(\epsilon_{\mathrm{repr}}\) and \(\epsilon_z\) are supplied or independently derived.

## 57. Claims currently supported

The following are supported at their stated evidence level:

1. **Finite projected-bath correctness:** Audits 02–04 close the operator and detector-free bath branches for their declared finite suites.
2. **Factorized scalar null:** nontrivial U1 confirms cancellation near the \(10^{-12}\) floor despite a nonzero upward source.
3. **Task-07 v8 structural correctness:** dual references, complete dissipators, causal kernels, trace closure, and low-rank/full-tangent agreement are healthy in audited cases.
4. **Downward zero-rate response within the current Task-07 numerical family:** the refined result has \(\chi_D>0\), \(\chi_{\mu^*}<0\), and passes insertion, time-step, and shell comparisons at the declared few-percent level.
5. **Large upward candidate with opposite sign:** \(\chi_D<0\), \(\chi_{\mu^*}>0\), strong shell-stability evidence, and a major confinement-driven time-shape change.
6. **Dephasing candidate:** P5 is structurally healthy and nonzero, but not yet family converged.
7. **Source activity is not susceptibility:** the weak-confinement downward source can be larger while producing a smaller net response; upward insertion and output times are distinct.

## 58. Claims not yet authorized

Do not claim:

- a complete Task-08 family PASS;
- publication-level Part-I numerical closure;
- a final upward response before U2/U4/U2-I are audited;
- a final dephasing response before P2/P3/P4/P2-I are audited;
- a universal, monotonic, power-law, linear, or \(\sqrt\omega\) susceptibility law;
- a finite positive-rate effect;
- bath-temperature dependence or a thermal trajectory simulation;
- that the ambient bath directly creates clicks or removes particle probability;
- that \(K_N\) is an absorber;
- that noncommutation guarantees nonzero susceptibility;
- that a nonzero source curve proves a detector response;
- a continuum semigroup theorem from the finite projected calculation;
- a microscopic detector derivation.

## 59. Gate to Tasks 09–10

Proceed to finite positive rates only after at least one direction has:

- complete canonical family coverage;
- current-v8 common-core provenance;
- scalar pointwise null PASS;
- external \(0.1\to0.05\) insertion PASS;
- time-step and shell PASS;
- independent Task-08 aggregate PASS;
- a complete error budget with signal/error \(\ge5\).

Then use at least two small positive rates and require the nonlinear residual to scale quadratically under rate halving.


# Part XIII — Exact next-session workflow and handoff

## 60. Immediate checklist

### Before submitting the first wave

- [ ] Verify package SHA `eab4a7...`.
- [ ] Confirm folders 4800–4807 are unused.
- [ ] Run Task-05 dependency and manifest verification.
- [ ] Run Task-07 package/core verification.
- [ ] Use immutable one-file-per-case Slurm submissions.
- [ ] Allocate enough wall time for the non-checkpointed complete kernel.

### First wave

- [ ] Run 4800 D1.
- [ ] Run 4801 U2.
- [ ] Run 4802 P2.
- [ ] Run Task-07 per-case loaders.
- [ ] Run Task-08 case-local audits.
- [ ] Check U2/P2 structural gates before second wave.

### Second wave

- [ ] Run 4803 U4.
- [ ] Run 4804 U2-I.
- [ ] Run 4805 P4.
- [ ] Run 4806 P3.
- [ ] Run 4807 P2-I.
- [ ] Run all per-case loaders and case-local Task-08 checks.

### Final aggregate

- [ ] Assemble all fifteen canonical full shares.
- [ ] Add D2-I, U2-I, P2-I as supplemental controls.
- [ ] Supply curated Task-05 inputs.
- [ ] Supply \(\epsilon_{\mathrm{repr}}\) and \(\epsilon_z\).
- [ ] Run one refinement-aware project-wide Task-08 audit.
- [ ] Report scientific status separately from deterministic rerun coverage.
- [ ] Select one principal \(\omega=100\) spinor case for an optional additional deterministic rerun after convergence is closed.

## 61. Files to supply to a new analysis session after the campaign

1. This master audit and its SHA sidecar.
2. Previous master audit and final Task-07→Task-08 handoff.
3. V7 manuscript.
4. Final v8 numerical-core identity and per-case-loader identity.
5. All fifteen canonical full Task-07 case-share ZIPs.
6. D2-I, U2-I, and P2-I full shares.
7. Corresponding diagnostic shares.
8. D3 closed deterministic package.
9. Curated Task-05 raw reference tree or exact accepted directories.
10. All Task-08 case-local outputs and the final aggregate share.
11. A case register mapping matrix IDs, folder numbers, hashes, run counts, and caveats.

## 62. Suggested opening prompt for the next session

> I am supplying the current master audit and the completed Task-07/Task-08 zero-rate response family for my Part-I open-system ABC project. Use the master audit as the workflow authority, V7 as the theory authority, the frozen Task-07 v8 numerical-core SHA `827fd4993707152393a8adcf891df59d7b4d02310a06e89dd5263c0fd37369af`, and the final per-case-loader SHA `3ec8f9699b2182ebd73e17e64bfbd6fc783df5d9e1ee9dc29cfd7f64c0f91d14`. First inventory all canonical D1–D5/U1–U5/P1–P5 packages and supplemental D2-I/U2-I/P2-I packages. Verify hashes and reconstruct every numerical statement independently. Do not trust solver or loader PASS flags as evidence. Keep scientific validity, deterministic rerun coverage, and publication-level upstream closure separate. Do not begin finite-rate, thermal, or broad-confinement analysis until the zero-rate family, supplemental insertion refinements, and complete uncertainty budget pass.

## 63. Final authority statement

\[
\boxed{
\begin{aligned}
&\text{Audits 00--04 are closed for their declared finite scopes.}\\
&\text{Task 05/06 provides a qualified zero-bath detector foundation; full historical closure is pending.}\\
&\text{The final Task-07 v8 numerical architecture is validated.}\\
&\text{The downward response is numerically robust within the measured Task-07 family.}\\
&\text{The upward and dephasing families remain incomplete.}\\
&\text{No final Task-08 family PASS or finite-rate/temperature claim exists yet.}\\
&\text{The 4800--4807 campaign is the exact immediate completion plan.}
\end{aligned}
}
\]


# Appendix A — Stable authoritative fingerprints

```text
Previous master audit
0ceecbbf22b01b0242946c75a9b18d018f248225b70e3614fe418057ba3f4b3b

Task-07 -> Task-08 final handoff
d7f4a629c9b21bdf3508193a9a2c585b050c63371bcfd0aea14631f168f32536

Post-Task-07 analysis handoff
a1aea6b5b1a94f1abf30ac7b4f9babf3f968fb68ff51d910956bbc60cc56088d

V7 manuscript
d0618e35c6b5432d8289e9feaf17206bd912fa9795e31d47ad1f96e5c520b7b7

Frozen 750.Reference(4).py
8cf2095b2d760a0b702c930fe5690fe762d08ad7c721a8c53b5ed498d1744009

Final Audit-02 solver
2ed0daf88dca64d33896d42e53d93c1e57b85d7e22391498babd4f7588b273b2

Stage-03 solver
5e621ee346604d8eef4765c07532ab3b525783af2b9a52d80fa408ef38c65bbe

Audit-04 loader
cf0246ee8767dbb8862d637a4225952c9625392281d3856a616e69fea22c7d9c

Task-07 v8 numerical core
827fd4993707152393a8adcf891df59d7b4d02310a06e89dd5263c0fd37369af

Task-07 independent per-case loader
3ec8f9699b2182ebd73e17e64bfbd6fc783df5d9e1ee9dc29cfd7f64c0f91d14

Task-08 v2.6 loader
c557cf5af72d29560397c582b81501d651709d0d60e888d0c8dc18888ef8967f

D3 closed full share
4f316c77206bba059dd2d052d7a1e2028780f99a1f8bf4776f0cea8dd30c5d7a

D3 closed diagnostic share
0d0b3a94dc4427392f58102a3a82fe3abc5c0c36e982b4e001e36ea8d7037ca9

D4 full case share
8b9152588c1099ba2c2b79d127e81de7fde4281ca487938926a91e2ee815b4c5

D4 diagnostic share
94acbbb22eb6751704d4dfb3c585e3719c961da5122f7bd7e254f77f0475342b

4736 full case share
d79d188923c546170b74c4d9d8ef1479f7b89ed7b0b2631f4bdf051defc9f429

4746 full case share
8241a188cbcabb2292424e2c0317d18d514febf849715be05d8d9e332669682a

Corrected curated U3 Task-08 share
38af7c888f705ea7c0e1976b1d8967f54090e817c0220d3188f89d06130162da

Final 4800–4807 package
eab4a7a0614c86ca8da1536d899193725ae53d658f6ad07e8abec16e29568fc9

Task-08 automatic recheck tool
d95cbc3441a1bd93d3182100639e10e471cf56eb2da0b7a5aa840886c81fddf5
```

# Appendix B — Status vocabulary

| Status | Meaning |
|---|---|
| `MISSING` | No acceptable formal case package is available. |
| `LOCAL_PASS` | Local reconstruction passes; external family or evidence items remain. |
| `RERUN_PENDING` | Scientifically admissible; deterministic same-prefix rerun not closed. |
| `FAILED` | A completed local integrity or numerical gate failed. The primitive failed check must be identified. |
| `CLOSED` | Local science and deterministic rerun closure are complete. |

# Appendix C — Operational distinction among the three refinements

| Symbol/code parameter | Meaning | Current downward evidence |
|---|---|---|
| `DT = Δt` | Detector/Cayley propagation step | D2→D4: 0.6186% complete-law difference |
| `N_SHELL = N` | Transverse complete-shell cutoff | D2→D5: 0.002273% |
| `INSERTION_DT = Δs` | Environmental insertion quadrature spacing | D2→D2-I: 2.6125% |

These are orthogonal numerical controls. A finer \(\Delta t\) cannot repair a coarse \(\Delta s\), and a larger \(N\) cannot repair insertion quadrature.
