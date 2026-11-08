# Part-I Open-System ABC Project
## Authoritative Numerical Master Audit Through Task-09 v3.9 Rank-Growth Failure and the Fresh-v4 Reset Handoff

**Project:** Environmental susceptibility of the spin–momentum absorbing-boundary detector  
**Audit date:** 11 August 2026  
**Scope:** finite Part-I scalar/spinor absorbing-boundary detector with an independent transverse trace-preserving environment  
**Current computational frontier:** Task-09 deterministic positive-rate validation, U2 upward channel  
**Current decision:** **All Task-09 positive-rate v3.x pilots remain non-accepting and have failed before the required prompt-window endpoint \(t=3.6\). No further cap escalation or v3.x hot patch is authorized. Task-09 should restart as a clean v4 implementation/design generation after the exact v3.9 failure event is extracted and the deterministic representation is selected from a predeclared feasibility audit.**

---

> ## Current-status precedence notice
>
> This document supersedes, for **current Task-09 status and next actions**, the earlier file
>
> ```text
> NUM_Open_System_PartI_Authoritative_Master_Audit_Through_Task09_
> RankSpectrum_Resolution_2026-08-11.md
> ```
>
> The earlier audit remains authoritative historical evidence for:
>
> - final Task-07/08 zero-rate closure;
> - the accepted v3.4 U2-zero control;
> - the first v3.4 rank-spectrum event;
> - the physical and numerical conventions inherited into Task-09.
>
> Its previous conclusion that cap 256 was provisionally adequate after the **first** spectrum event is now superseded by later A100 evidence. The subsequent v3.5–v3.9 pilots demonstrate sustained and rapidly increasing factor rank well beyond 256, 512, and 640 before \(t=1.5\), far short of the required pilot endpoint \(t=3.6\).
>
> This audit does **not** declare a finite-positive-rate physical result. Every v3.4–v3.9 positive-rate run is diagnostic or failed evidence only.

---

# 1. Executive conclusion

The accepted zero-rate project remains intact:

1. Audits 00–04 are closed for their declared finite scopes.
2. Task-05/06 remains a qualified zero-bath detector foundation; residual historical campaign/provenance closure remains pending.
3. The complete Task-07 finite-v8 zero-rate response family is available.
4. The final Task-08 aggregate passed

   ```text
   PASS_TASK08_LINEAR_RESPONSE
   ```

5. The accepted insertion-refined spinor responses D2-I, U2-I, and P2-I remain `RESOLVED_NONZERO` under the dated Task-08 operational uncertainty policy.
6. The factorized scalar response remains null.
7. Task-09 was correctly authorized as a deterministic finite-positive-rate validation stage.

The finite-rate implementation history now establishes a different and more restrictive conclusion than the previous master:

8. v3.4 repaired the CuPy Gram-eigensolver defect by using `numpy.linalg.eigh` on CPU with GPU factor rotation.
9. The v3.4 zero-rate U2 control 4900 passed and remains valid historical evidence for that exact family.
10. The v3.4 positive-rate U2-low run failed under the old local \(10^{-14}\) discarded-trace rule; the first event showed that a global budget could fit below rank 256 **at that single early event**.
11. v3.5 implemented the remaining-global-budget equal-share rule with cap 256, but the required rank subsequently exceeded 256 near the prompt rise.
12. v3.6 raised the diagnostic cap to 512, but its monolithic CuPy factor crossed the practical 2-GiB single-array boundary and produced `cudaErrorIllegalAddress` in the high-rank regime.
13. v3.7 replaced the monolithic factor by exact contiguous column blocks, passed the previous CUDA-danger region, and then failed cleanly at an exact rank-cap event:

   \[
   k=5488,\quad n=2744,\quad t=1.372,\quad r_{\rm required}=514>512.
   \]

14. v3.8 retained cap 512 and allowed only rigorously banked **past** compression credit. It passed the v3.7 event but failed later at:

   \[
   k=5818,\quad n=2909,\quad t=1.4545,
   \]

   where the equal-share required rank was 526 and the banked-credit required rank was 516, both above 512.
15. v3.9 returned to the original remaining-budget equal-share policy and selected cap 640 from the v3.8 spectrum using a predeclared block-aligned headroom rule. Nevertheless, it failed again shortly after the reported step 2800. The last completed progress record was

   ```text
   step=2800, t=1.400000, rank=588, required=588,
   cap_margin=52, B_used=9.749e-10, calls=5600/40000
   ```

   followed by a fail-closed `required rank > 640` event before the next step-2900 progress report.
16. Therefore, cap selection from one prior failure spectrum does not predict later rank demand. The required rank is evolving rapidly with physical time.
17. The present blocker is no longer a one-off local tolerance defect or a one-off memory bug. It is the combined feasibility problem of:

   - rapid physical/numerical mixed-state rank growth;
   - detector cost approximately linear in retained rank;
   - temporary three-Kraus rank expansion;
   - dense Gram assembly and CPU eigendecomposition cost growing strongly with rank;
   - the requirement to propagate far beyond the current failures to \(t=3.6\) and eventually \(T=10\).

The current decision is therefore

\[
\boxed{
\text{Stop the v3.x escalation chain and redesign Task-09 as a clean v4 generation.}
}
\]

No v3.10 cap-768, cap-896, cap-1024, tolerance-relaxation, rate-change, or future-budget-borrowing run is authorized by this audit.

---

# 2. Evidence classes

| Class | Meaning | Current use |
|---|---|---|
| **A — raw and independently reconstructed** | Raw event JSON/spectrum, source identity, hashes, and independent reconstruction exist. | Final Task-07/08 family; v3.4 first event; v3.7 cap-512 event; v3.8 banked-credit failure event and decision audit. |
| **B — exact source plus cluster stdout/stderr** | Source identity and execution log are available, but the final event JSON/spectrum has not yet been independently reconstructed in this audit. | v3.9 cap-640 failure. |
| **C — historical implementation evidence** | Earlier package/source and diagnostic records remain useful but are superseded as active workflow. | v3.4–v3.6 package history and failed outputs. |
| **D — planned, not executed** | Design or case is described but has no accepted result. | Fresh Task-09 v4; Task-09 high-rate/scalar/time/shell cases; Task 10. |
| **E — failed non-accepting execution** | Solver stopped fail-closed and produced no admissible finite-rate scientific result. | All positive-rate v3.4–v3.9 attempts. |

A failed pilot may diagnose an algorithmic or representation limit. It does not establish a finite-rate detector curve or physical conclusion.

---

# 3. Current authority hierarchy

When records conflict, use this order:

1. **This master audit** — current Task-09 status, claim boundary, v4 reset, and next-session workflow.
2. **Final Task-08 aggregate products** — accepted zero-rate responses, uncertainty policy, and classifications.
3. **V7 manuscript** — physical theory, finite-map interpretation, and claim discipline.
4. **Exact Task-09 raw event JSON/spectrum reports and cluster stdout/stderr** — numerical evidence for each failed positive-rate attempt.
5. **Task-09 v3.9 source** — last diagnostic implementation, not an active production baseline.
6. **Previous 11 August Task-09 rank-spectrum master audit** — historical authority through the first v3.4 event.
7. **Task-09 v3.4 CPU-Gram-stable package** — physical finite-map baseline and accepted historical zero control.
8. **Frozen `750.Reference` source** — longitudinal grid, scalar roof closure, packet, Cayley structure, and GMRES conventions.
9. **Final Audit-02 operator source/archive** — projected oscillator operators, native ordering, and \(K_N\).
10. **Task-05/07 audited sources** — working ordering, detector implementation, and zero-rate response architecture.
11. **v3.5–v3.8 standalone sources** — diagnostic evolution only; not active production sources.

There is currently **no active Task-09 positive-rate production package**.

---

# 4. Stable scientific status before Task-09

## 4.1 Stage/task dashboard

| Stage/task | Current status | Current decision |
|---|---|---|
| Audits 00–04 | Closed for declared finite scopes | Preserve |
| Task 05/06 | Qualified zero-bath detector foundation | Preserve; historical closure pending |
| Task 07 | Complete finite-v8 zero-rate response family | Preserve |
| Task 08 | `PASS_TASK08_LINEAR_RESPONSE` | Operational PASS |
| Scalar response | Factorized null | Established finite-model control |
| Spinor D2-I | `RESOLVED_NONZERO` | Accepted zero-rate derivative |
| Spinor U2-I | `RESOLVED_NONZERO` | Accepted zero-rate derivative; Task-09 target |
| Spinor P2-I | `RESOLVED_NONZERO` | Accepted zero-rate derivative |
| Task-09 v3.4 U2 zero | `PASS_TASK09_ZERO_RATE_CONTROL` | Historical accepted result for v3.4 only |
| Task-09 positive rate | No accepted result | Paused/reset |
| Task 10 | No complete Task-09 family | Blocked |
| Task 11 | Thermal/preparation organization | Blocked by Tasks 09–10 |

## 4.2 Accepted zero-rate response summary

| Direction | \(\chi_D\) | \(\chi_{\mu^*}\) | Accepted complete signed-response norm | Classification |
|---|---:|---:|---:|---|
| downward | \(+2.80653184\times10^{-3}\) | \(-1.89238164\times10^{-2}\) | \(2.85617762\times10^{-3}\) | `RESOLVED_NONZERO` |
| upward | \(-5.27770479\times10^{-1}\) | \(+3.55724785\) | \(6.85485610\times10^{-1}\) | `RESOLVED_NONZERO` |
| dephasing | \(+4.57853178\times10^{-3}\) | \(-2.97474037\times10^{-2}\) | \(4.65731119\times10^{-3}\) | `RESOLVED_NONZERO` |

These are derivatives at zero environmental rate. They are not finite-rate percentage changes.

---

# 5. Fixed physical architecture and conventions

Nothing in the v3.4–v3.9 failures changes the Part-I physical model.

For \(\alpha\in\{\mathrm{sc},\mathrm{s}\}\),

\[
\frac{d\widetilde\rho_\alpha}{dt}
=
\mathcal L^{\mathrm{nc}}_{\alpha,\mathrm{ABC}}[\widetilde\rho_\alpha]
+
\mathcal L^\perp_{\mathrm{env}}[\widetilde\rho_\alpha].
\]

The direct ABC is the sole monitored detector. The ambient transverse environment is trace preserving and unmonitored. Thus

\[
S_\alpha(t)=\operatorname{Tr}\widetilde\rho_\alpha(t),
\qquad
 g_\alpha(t)=-\dot S_\alpha(t),
\]

and permanent trace loss belongs only to the roof-click sector.

The detector conditions remain

\[
\partial_z\psi=i\kappa\psi,
\]

\[
\partial_z\Psi=(i\kappa I_2-K)\Psi,
\qquad
K=\frac{\sigma_xp_y-\sigma_yp_x}{\hbar}.
\]

The finite spinor roof Hamiltonian term remains

\[
+\frac{K_N}{2h_z}.
\]

The detector step remains

\[
A=I+\frac{i\Delta t}{2}H,
\qquad
B=I-\frac{i\Delta t}{2}H,
\qquad
A\psi_{n+1}=B\psi_n.
\]

The finite-rate U2-low case remains

\[
\omega=100,\quad N=12,\quad N_z=1500,\quad
\Delta t=5\times10^{-4},\quad T=10,
\]

\[
\lambda=\frac{\pi}{400},\quad m_B=1,
\quad t_{\rm pilot}=3.6.
\]

The physical full-family schedule contains

\[
N_{\rm steps}=20000,
\qquad
N_{\rm comp}=40000
\]

compression calls, while the non-accepting pilot target contains 7200 detector steps and 14400 compression calls.

The following remain excluded:

- CAP behind the direct ABC;
- a second roof-loss channel;
- negative rates;
- silent clipping or unrecorded renormalization;
- ambient jumps interpreted as clicks;
- finite-rate physical claims from partial pilots;
- Task-10 use of failed or pilot-only outputs.

---

# 6. Task-09 finite map and low-rank representation

The intended deterministic finite step is

\[
\widetilde\rho_{n+1}
=
\Phi_{\lambda r,\Delta t/2}
\circ
\mathcal T^{\mathrm{nc}}_{D,\Delta t}
\circ
\Phi_{\lambda r,\Delta t/2}
[\widetilde\rho_n].
\]

The bath half-step uses the finite CPTP resolvent-Kraus map

\[
R_s=(I+sG)^{-1/2},
\qquad
K_0=R_s,
\qquad
K_\beta=\sqrt{s}\,L_\beta R_s.
\]

The state is factorized as

\[
\widetilde\rho=XX^\dagger.
\]

For the U2 upward channel, each bath half-step expands the factor by the three Kraus branches. Compression is based on the Hermitian Gram matrix

\[
G_X=h_zX^\dagger X.
\]

The v3.4–v3.9 line used:

- CPU `numpy.linalg.eigh` for the finite Hermitian Gram matrix;
- GPU factor rotation;
- actual discarded Gram trace for the compression error;
- a cumulative trace-norm accounting bound;
- fail-closed rank-cap rejection before rotation in the later versions.

For \(N=12\), the factor row dimension is

\[
2M_{12}N_z=182\times1500=273000.
\]

A retained rank \(r\) therefore stores approximately

\[
273000\,r\times16\ \text{bytes}
\]

in complex128. A single monolithic factor crosses \(2^{31}\) bytes between ranks 491 and 492. This motivated the exact blocked-factor representation introduced in v3.7.

---

# 7. Detailed Task-09 chronology through v3.9

## 7.1 Version table

| Version/source | Source SHA-256 | Main numerical change | A100 outcome | Status |
|---|---|---|---|---|
| v3.4 U2-low | `e55f7795c4aba03307cd5df7bd76d2b597f9ab28971998c820714a2b43fc1b99` | CPU Gram eigensolver; local \(10^{-14}\) discard rule; cap 256 | First positive-rate run stopped at rank cap | Failed diagnostic |
| v3.5 AdaptiveBudget | `a47771af20e83a053715c7e471daefd72bee46b114417d3e93df28988164fe13` | Remaining-global-budget equal-share; cap 256 | Last reported step 2500 rank 244, then required rank exceeded 256 | Failed pilot |
| v3.6 Cap512 | `a4f44e8d16d57f087e8d5fcdd7883e802cbb753937f2e75b1e5f821c7a4d48df` | Equal-share; cap 512; monolithic factor | `cudaErrorIllegalAddress` after step 2700/high-rank compression | Failed implementation diagnostic |
| v3.7 Cap512 LargeFactorSafe | `a87a657ded82cbff976c75e2e5857246849400fb3c5eb7859c32a252192085e1` | Exact 128-column blocked factor; cap 512 | Clean cap failure at call 5488, required rank 514 | Failed pilot; exact event reconstructed |
| v3.8 Cap512 BankedCredit | `91f87bc93b397a55f0b0c8da6dfe6e806a48852c71e4cbfb3535bf0d19369a97` | Blocked factor; cap 512; past-credit fallback only | Clean failure at call 5818; equal-share rank 526, banked rank 516 | Failed pilot; exact event reconstructed |
| v3.9 Cap640 LargeFactorSafe | `53076121b914b8da710db4ef84988047810f378c4ceb81fee5f1087a2e0baefc` | Blocked factor; original equal-share; cap 640 selected from v3.8 spectrum | Last report step 2800 rank 588; then required rank exceeded 640 | Failed pilot; exact final event still to extract |

## 7.2 Directory and job register

| Version | Stage directory | Job/evidence |
|---|---|---|
| v3.5 | `4920.Task09_v3_5_...AdaptiveBudget...` | job 9415206 log |
| v3.6 | `4921.Task09_v3_6_...Cap512...` | job 9415354; CUDA illegal-address log |
| v3.7 | `4922.Task09_v3_7_...Cap512_LargeFactorSafe...` | job 9415570; exact failure event and spectrum |
| v3.8 | `4923.Task09_v3_8_...Cap512_BankedCredit_LargeFactorSafe...` | job 9415966; exact failure event and decision report |
| v3.9 | `4924.Task09_v3_9_...Cap640_LargeFactorSafe...` | job 9416588; stdout/stderr and pending exact event extraction |

These directories must remain immutable historical evidence. None is an active v4 namespace.

---

# 8. Exact numerical evidence

## 8.1 v3.4 first rank-spectrum event

The first local-policy event was reconstructed at

```text
compression call                  4502
bath half-step                    second
estimated detector step           2251
estimated physical time           1.1255
pre-compression rank              765
local-policy required rank        257
global fixed-allocation rank      247
remaining-budget rank             246
cumulative bound before event     5.580158557449977e-11
remaining calls including event   35499
```

This correctly proved only that cap 256 was sufficient at that first event under a global allocation. It did not establish bounded rank over the later prompt interval.

## 8.2 v3.5 cap-256 equal-share pilot

The v3.5 equal-share pilot reproduced the healthy early trajectory and reached

```text
step 2500
physical time 1.25
retained rank 244
cumulative bound approximately 8.360e-10
```

before a later compression required rank above 256. No exact v3.5 failure spectrum is frozen in this audit.

Interpretation: the new global policy corrected the first v3.4 event but did not make cap 256 feasible over the evolving prompt interval.

## 8.3 v3.6 monolithic cap-512 CUDA event

The v3.6 run reached

```text
step 2700
physical time 1.35
retained rank 458
cumulative bound approximately 9.273e-10
```

and then raised

```text
cudaErrorIllegalAddress
```

inside the high-rank compression/trace path.

At 273000 rows, one complex128 factor exceeds \(2^{31}\) bytes at rank 492. The later blocked-factor run removed this CUDA failure mode and reached a clean rank-policy event. The combined evidence strongly supports a monolithic-array implementation boundary rather than a physical-map instability.

## 8.4 v3.7 exact cap-512 event

The v3.7 blocked-factor event is exact:

```text
compression_call_index                    5488
detector_step_index                       2744
physical_time                             1.372
bath_half_step                            second
remaining_compression_calls               34513
rank_before                               1536
required_rank                             514
rank_cap                                  512
allowed_discarded_trace                   1.3113871186104165e-13
discarded_trace_at_rank_cap               1.6452235431763262e-13
discarded_trace_at_required_rank          1.1878117326582647e-13
cumulative_trace_norm_bound_before        9.480192750797387e-10
factor_rotation_performed                 false
budget_committed                          false
```

Independent reconstruction gave

\[
r_{\rm required}=514,
\qquad
\frac{\delta(512)}{\delta_{\max}}=1.254567411734.
\]

Evidence hashes:

```text
failure event JSON   4c260b65d246ed8fc3c5262b5e9c3260ce04a5527814f7e3bb24703905e87695
spectrum NPZ         60243c05427bf9b3746605780fe63bda5760c80c77595d74e06ab6289bacb91d
failure JSON         72fa34c2264416fcd73df2b13f81601a3c53fe831462392ccd918afc06f0ed31
run status JSON      1b4529abbd69a16f2a9754cf33d58a81ce1f39f402ea89cca2e18d573e5adc4e
checkpoint NPZ       516a9b54f0b2ce8caea713ea1d536f0e547d9a2ca6d6c2fefa5df0735d1fe77b
rank-spectrum report ecb83416ba0c8a347f7a3f6bfee2f013bc88e6ffa346ab588adc126b7d905383
```

## 8.5 v3.8 exact banked-credit event

The v3.8 event and independent decision audit are exact:

```text
compression_call_index                          5818
detector_step_index                             2909
physical_time                                   1.4545000000000001
bath_half_step                                  second
remaining_compression_calls                     34183
rank_before                                     1536
soft/equal-share required rank                  526
banked-credit required rank                     516
rank_cap                                        512
equal_share_allowed_discarded_trace             1.2501398532060958e-13
banked_credit_allowed_discarded_trace           6.03060214396903e-13
discarded_trace_at_rank_cap                     1.7122786676060095e-12
cumulative_trace_norm_bound_before              1.453293879571206e-09
banked_trace_norm_credit_before                 1.206120428793806e-12
scheduled_cumulative_bound_after_call           1.4544999999999999e-09
factor_rotation_performed                       false
budget_committed                                false
future_budget_borrowed                          false
```

Independent ratios were

\[
\frac{\delta(512)}{\delta_{\rm equal}}=13.69669691926641,
\qquad
\frac{\delta(512)}{\delta_{\rm banked}}=2.8393162518910198.
\]

Thus the banked-credit fallback was not merely slightly insufficient at the later event; rank 512 had become clearly inadequate.

Evidence hashes frozen into v3.9:

```text
v3.8 event JSON       0fa263a81cb99a1446743499eacd81504aff4965b30a7005d8f07f65e73ded21
v3.8 spectrum NPZ     4f6575e203e8dbe094f045b9b2db78eaef969ef64795085ba6a1a464ebc8f7ca
v3.8 report TXT       09a5d5283dee3cbc0d650b011d34341a0dfc59723df88ed693571cd5e09896bb
v3.8 report JSON      777270f98cc387d7226c0808e9f4c0e504ca7ebebcaa13b67947422a37ffc771
```

## 8.6 v3.9 cap-640 pilot

The v3.9 source selected cap 640 by the frozen rule

```text
smallest 128-column block multiple above the equal-share required rank,
with selected-cap tail no larger than one quarter of the equal-share allowance
```

using the exact v3.8 required rank 526. The source remained:

- equal-share remaining-global-budget policy;
- \(B_{\max}=10^{-8}\);
- 128-column blocked factor;
- CPU Gram eigensolver;
- pilot-only, no acceptance, no Task-10 eligibility.

The A100 log reproduced the earlier trajectory:

| Step | Time | Survival | Rank | Required | Cap margin | Cumulative bound |
|---:|---:|---:|---:|---:|---:|---:|
| 2500 | 1.25 | 0.9997048476440 | 244 | 244 | 396 | \(8.360\times10^{-10}\) |
| 2600 | 1.30 | 0.9993809594655 | 344 | 344 | 296 | \(8.811\times10^{-10}\) |
| 2700 | 1.35 | 0.9988152975969 | 458 | 458 | 182 | \(9.272\times10^{-10}\) |
| 2800 | 1.40 | 0.9979031110657 | 588 | 588 | 52 | \(9.749\times10^{-10}\) |

The step-2800 survival agrees with the v3.8 value to approximately \(3.3\times10^{-12}\), supporting cross-version trajectory consistency through that point.

The run then failed fail-closed with

```text
Adaptive-budget compression requires a rank above MAX_RANK;
refusing factor rotation and silent truncation
```

before the next step-2900 progress report.

### Evidence boundary for v3.9

The exact v3.9 compression-call index, detector step, physical time, required rank, discarded tail, and full spectrum are not contained in the current attached evidence. They must be extracted from the v3.9 output directory before v4 design is frozen.

No exact value should be inferred merely from the last step-2800 progress line.

---

# 9. What the v3.x sequence has established

## 9.1 Established numerical facts

1. The v3.4 finite bath and detector map can be propagated correctly at zero rate and through the early positive-rate interval.
2. CPU `numpy.linalg.eigh` is required on the certified ZIB stack for the small Gram problem; the tested CuPy eigensolver path was not admissible.
3. The exact 128-column blocked factor is required once the logical factor approaches the 2-GiB single-array boundary.
4. Blocked storage resolves the CUDA illegal-address failure without changing the represented density operator.
5. The remaining-global-budget equal-share policy is mathematically coherent and independently reconstructible.
6. Rank demand grows rapidly during the prompt approach even at the low physical rate \(\pi/400\).
7. Rank demand did not plateau at 256, 512, or 640 within the observed interval.
8. A cap chosen with substantial headroom at one failure spectrum can fail soon afterward because the spectrum itself evolves.
9. The partial trajectories remain mutually consistent across implementation versions through common completed steps.
10. No supplied failure indicates GMRES divergence, non-finite survival, bath-trace failure, detector-probability failure, or a physical instability before the rank/representation stop.

## 9.2 Not established

The v3.x sequence does not establish:

- the rank required at \(t=3.6\);
- the rank required at \(T=10\);
- feasibility of a full deterministic low-rank U2-low run on one A100;
- an accepted finite-rate curve;
- agreement with the Task-07 tangent;
- a factor-four rate-halving result;
- finite-rate scalar null;
- finite-rate time-step or shell convergence;
- Task-10 eligibility;
- any finite-positive-rate physical claim.

---

# 10. Why a clean v4 reset is now required

The v3.5–v3.9 line accumulated successive diagnostic modifications:

- global-budget replacement of the local tolerance;
- cap 256 to 512;
- monolithic to blocked factor;
- banked-credit fallback;
- return to equal-share;
- cap 640 selected from a single event;
- legacy checkpoint imports;
- multiple incompatible contract/checkpoint/telemetry schemas.

Each modification was individually motivated, but the sequence is no longer an efficient or clean production foundation. More importantly, the cap-640 failure shows that the primary feasibility question is unresolved.

A fresh v4 generation must separate three questions that became entangled in v3.x:

1. **Physical map:** Is the finite CPTP bath–detector–bath map correct?  
   Current answer: yes for the validated finite model and reduced benchmarks.

2. **Error budget:** What compression error is scientifically required for Task-10 observable validation?  
   Current answer: \(10^{-8}\) is the existing frozen bound, but v4 must either retain it explicitly or replace it only through a predeclared claim-level derivation. No silent relaxation is permitted.

3. **Deterministic representation:** Which state representation can carry the required mixedness through \(t=3.6\) and \(T=10\) at feasible cost?  
   Current answer: not established. The present global low-rank factor with dense Gram diagonalization has not passed the pilot.

The v4 reset is therefore a **representation-and-budget design stage**, not simply a renamed cap increase.

---

# 11. Fresh Task-09 v4 design contract

## 11.1 Physics that v4 must preserve

Unless a dated authority amendment says otherwise, v4 must preserve:

- U2 upward physical direction;
- \(\lambda=\pi/400\) as the first positive rate;
- \(\omega=100\), mode 00, \(N=12\), \(N_z=1500\);
- \(\Delta t=5\times10^{-4}\), physical \(T=10\);
- the finite resolvent-Kraus CPTP bath map;
- Strang bath-half / detector / bath-half ordering;
- Task-05/07 complete-shell and spin ordering;
- \(+K_N/(2h_z)\) at the roof;
- detector Cayley/GMRES conventions;
- midpoint roof probability;
- no clipping, no unrecorded renormalization, no negative rates;
- pilot-only claim boundary until a complete family is independently audited.

## 11.2 Evidence consolidation required before coding

The first v4 action is **not** to write another propagation solver. It is to create a compact design-evidence package containing:

1. the exact v3.9 failure event JSON;
2. the v3.9 Gram spectrum NPZ;
3. an independent v3.9 spectrum report;
4. v3.9 stdout, stderr, run status, failure JSON, configuration, copied source, and hashes;
5. the complete v3.7 and v3.8 event/spectrum reports;
6. rank-versus-time and required-rank-versus-time histories from all available telemetry;
7. runtime-versus-rank and memory-versus-rank estimates;
8. checkpoint inventories for 4920–4924;
9. a statement of which checkpoints are diagnostic only and which, if any, can seed a new family.

The v4 design must not infer late-time rank from a single event.

## 11.3 Error-budget review

Before selecting a representation, v4 must freeze one of two explicit choices:

### Option A — retain the existing bound

\[
B_{\max}=10^{-8}.
\]

Then the representation must satisfy this bound through the full scheduled family without ad hoc future-budget borrowing.

### Option B — formally amend the bound

A changed bound is permitted only if a dated derivation connects density-operator trace-norm compression error to the required Task-10 censored-law and integrated-observable tolerances. The amendment must be made before viewing the final v4 production result.

No v4 source may silently reuse a looser local tolerance merely to reduce rank.

## 11.4 Deterministic representation candidates

The next session must compare at least the following design classes before selecting one:

1. **Blocked global low-rank factor with a substantially revised spectral algorithm.**  
   This retains \(\rho=XX^\dagger\), but must address both increasing retained rank and the cost of repeatedly diagonalizing the temporary three-Kraus Gram matrix. Merely changing the hard cap is not sufficient.

2. **Structured/tensorized deterministic factorization.**  
   This should exploit that the bath acts only on the finite transverse channel space while the detector propagates longitudinal factors. Any approximation must come with a reconstructible positivity, trace, and detector-observable error bound.

3. **Alternative deterministic density representation.**  
   A projected operator basis, dynamical low-rank integrator, tensor-train/MPS-like form, or another structured scheme may be considered, but only after a reduced full-density benchmark and a clear preservation/error argument.

Quantum trajectories are not the default replacement for Task-09 because Task-09/10 require deterministic finite-rate validation. They may be used later as an independent check only after a deterministic reference exists or after a formal roadmap amendment.

## 11.5 Clean v4 software architecture

The first v4 package should be simpler than the v3.x chain:

- one authoritative standalone U2-low pilot source;
- no legacy v3.6/v3.7/v3.8 checkpoint import;
- a fresh v4 output namespace;
- one checkpoint schema;
- one compression/representation telemetry schema;
- one physical-family contract;
- one pilot execution contract;
- one independent read-only pilot verifier;
- no production acceptance code in the pilot source;
- no automatic sweep;
- no active 4900/4901 production naming until the v4 pilot passes.

The existing v3.x outputs remain immutable evidence and must not be blended with the v4 family.

## 11.6 Recommended staged v4 gates

A cost-aware staged sequence is required:

### V4-G0 — static and reduced certification

- source compilation and scope audit;
- exact reduced full-density benchmark;
- positivity and trace preservation;
- detector probability closure;
- representation-error reconstruction;
- memory and runtime model.

### V4-G1 — production-size first step

- CPU reconstruction of the first finite bath/detector step;
- A100 first-step smoke;
- exact initial rank sequence and trace closure;
- no acceptance.

### V4-G2 — short production-size rank/representation pilot

- fresh v4 start from \(t=0\), not a v3 checkpoint;
- stop at a predeclared time before or near \(t=1\);
- establish telemetry and cost scaling.

### V4-G3 — event-crossing pilot

- continue natively within v4 beyond all previous failure times, at least past \(t=1.5\);
- require the representation and error budget to remain controlled;
- update the cost projection to \(t=3.6\) before spending on the full pilot.

### V4-G4 — required non-accepting prompt-window pilot

- reach \(t=3.6\), step 7200;
- pass rank/representation, error-budget, trace, probability, solver, overflow, and provenance gates;
- write only a non-accepting pilot verdict.

### V4-G5 — family regeneration

Only after V4-G4 passes:

1. freeze the v4 family;
2. regenerate U2 zero under the same v4 family;
3. run full U2 low to \(T=10\);
4. then run U2 high, bath-microstep, scalar-null, time-step, and shell controls;
5. run Task 10 only after the required family is complete.

---

# 12. Current stop/go table

| Action | Status |
|---|---|
| Extract exact v3.9 event/spectrum | **GO — first next-session action** |
| Write v4 design/evidence report | **GO after extraction** |
| Implement v4 immediately from assumptions | **NO-GO** |
| Run v3.10 with cap 768/1024 | **NO-GO** |
| Change \(\lambda\) to make rank easier | **NO-GO without new scientific authorization** |
| Relax \(B_{\max}\) silently | **NO-GO** |
| Borrow future compression budget | **NO-GO** |
| Reuse failed v3.x output as Task-10 input | **NO-GO** |
| Use v3.4 4900 as matched v4 zero control | **NO-GO** |
| Preserve all 4920–4924 evidence | **GO / mandatory** |
| Continue zero-rate manuscript interpretation | **GO; independent of Task-09 failure** |

---

# 13. Current claim boundary

## Supported

1. The zero-rate Task-07/08 finite-v8 response family is operationally closed.
2. The factorized scalar click-time response is null.
3. Spinor downward, upward, and dephasing susceptibilities are resolved nonzero under the accepted operational policy.
4. The v3.4 finite-rate map passes the validated zero-rate control and early positive-rate numerical checks.
5. CPU Gram diagonalization is required on the tested ZIB stack.
6. Exact blocked-factor storage resolves the monolithic >2-GiB CUDA failure mode.
7. The U2-low deterministic factor rank grows rapidly in the prompt interval.
8. Caps 256, 512, and 640 have each failed before the required \(t=3.6\) pilot endpoint under the tested policies.
9. The positive-rate blocker is currently deterministic representation/cost feasibility, not a demonstrated physical instability.

## Not supported

Do not claim:

- an accepted U2-low finite-rate click law;
- a finite-rate change in \(D\), \(\mu^*\), prompt, or late detection;
- linear-response validation at \(\pi/400\);
- a factor-four rate-halving test;
- finite-rate scalar null;
- finite-rate time-step or shell convergence;
- a thermal finite-rate result;
- Task-09 or Task-10 PASS;
- publication-level Part-I closure.

---

# 14. Exact next-session workflow

1. Upload this audit first.
2. Upload the V7 manuscript and the previous 11 August rank-spectrum master.
3. Upload the v3.9 source and SHA sidecar.
4. From the 4924 directory, provide:

   ```text
   *_compression_failure_event.json
   *_compression_failure_spectrum.npz
   *_failure.json
   *_run_status.json
   *_configuration.json
   *_base_family_contract.json
   *_family_contract.json
   *_rate_contract.json
   *_execution_contract.json
   *_stdout.txt
   Slurm .out and .err
   copied solver source
   exact file hashes
   ```

5. Provide the v3.8 failure-spectrum TXT/JSON report and hashes.
6. Provide the v3.7 failure event/spectrum report and hashes.
7. Inventory checkpoints and source copies in 4920–4924; do not upload multi-GB checkpoints unless specifically required.
8. Independently reconstruct the exact v3.9 required rank and candidate-cap table.
9. Build a rank/time/runtime evidence table across v3.5–v3.9.
10. Write and freeze a Task-09 v4 representation-and-error-budget design document.
11. Only then implement one clean v4 pilot source.

---

# 15. New-session opening prompt

Use the following opening text in the next session:

```text
I am continuing the Part-I open-system ABC project from the fresh Task-09 v4
reset point.

Authority order:
1. NUM_Open_System_PartI_Authoritative_Master_Audit_Through_Task09_v3_9_
   RankGrowth_and_V4_Reset_Handoff_2026-08-11.md is the current workflow,
   status, claim-boundary, and stop/go authority.
2. The final Task-08 aggregate is the zero-rate numerical authority.
3. V7 is the theory authority.
4. The exact v3.7, v3.8, and v3.9 failure events/spectra and cluster logs are
   the Task-09 representation-feasibility evidence.
5. v3.4 supplies the physical finite-rate map baseline, but no v3.x positive-
   rate result is accepted and no v3.x source is active production code.

Current status:
- Audits 00-04 closed for declared scopes.
- Task-05/06 qualified zero-bath foundation.
- Task-07/08 zero-rate response operational PASS.
- Scalar response null; D2-I/U2-I/P2-I resolved nonzero.
- v3.4 U2-zero accepted historically.
- All positive-rate v3.4-v3.9 runs failed before t=3.6.
- v3.7 exact cap-512 event: call 5488, step 2744, t=1.372,
  required rank 514.
- v3.8 exact event: call 5818, step 2909, t=1.4545,
  equal-share rank 526 and banked-credit rank 516.
- v3.9 cap-640 failed after the last reported step 2800, rank 588;
  exact final event/spectrum must be reconstructed first.

Immediate task:
Do not write a new propagation solver yet. First audit the v3.9 event and all
rank-growth evidence, then freeze a clean Task-09 v4 deterministic
representation and compression-error contract. Do not authorize cap escalation,
rate changes, future-budget borrowing, Task-10 input, or a finite-positive-rate
physical claim.
```

---

# 16. Files and hashes controlling the handoff

| Artifact | SHA-256 / identity | Role |
|---|---|---|
| Previous Task-09 rank-spectrum master | `c063ad375efb958bfc72d9c664c59642c1ef7b30d2ca2324a7f9e2c2ac0ba67e` | Superseded Task-09 current-status record; historical authority |
| Task-09 v3.4 transport ZIP | `6c4f97efe2a1069753bc8c2ddb5fe9d6a2bd8581c0a42ddb0346f008e1b617ee` | Historical physical-map package |
| Task-09 v3.4 common core | `5b995bf91852a0849169207e5c0fda5aecac7eece5af24ac37c82990b29f6181` | Historical finite-map identity |
| v3.4 U2-zero source | `03922ac36a8e5b88fda8c2cdfaa9fc1e9a1c92674eb2b179f66c8dd4072c03ec` | Historical accepted zero control |
| v3.4 U2-low source | `e55f7795c4aba03307cd5df7bd76d2b597f9ab28971998c820714a2b43fc1b99` | Failed first positive-rate family |
| v3.5 source | `a47771af20e83a053715c7e471daefd72bee46b114417d3e93df28988164fe13` | Equal-share cap-256 diagnostic |
| v3.6 source | `a4f44e8d16d57f087e8d5fcdd7883e802cbb753937f2e75b1e5f821c7a4d48df` | Monolithic cap-512 CUDA diagnostic |
| v3.7 source | `a87a657ded82cbff976c75e2e5857246849400fb3c5eb7859c32a252192085e1` | Blocked cap-512 diagnostic |
| v3.8 source | `91f87bc93b397a55f0b0c8da6dfe6e806a48852c71e4cbfb3535bf0d19369a97` | Banked-credit cap-512 diagnostic |
| v3.9 source | `53076121b914b8da710db4ef84988047810f378c4ceb81fee5f1087a2e0baefc` | Cap-640 diagnostic; failed |
| Final Task-08 output manifest | `6a7e939fe86d0ffd827b0e5acb164b045affe79af0775ba87911f3ed92ff1a40` | Zero-rate response authority |

Scientific identity is controlled by stable source, configuration, contract, telemetry, event, spectrum, and output-manifest hashes—not by directory names alone.

---

# 17. Final authority statement

\[
\boxed{
\begin{aligned}
&\text{Audits 00--04 remain closed for their declared finite scopes.}\\
&\text{Task-05/06 remains a qualified zero-bath foundation.}\\
&\text{Task-07/08 zero-rate response remains operationally closed.}\\
&\text{Scalar response is null; D2-I, U2-I, and P2-I are resolved nonzero.}\\
&\text{The v3.4 zero-rate U2 control remains accepted historical evidence.}\\
&\text{No positive-rate v3.4--v3.9 result is admissible.}\\
&\text{Blocked-factor storage solved the monolithic CUDA failure.}\\
&\text{Caps 256, 512, and 640 failed before }t=3.6.\\
&\text{The exact v3.9 event must be reconstructed before further design.}\\
&\text{Task-09 now resets to a fresh v4 representation-and-budget design stage.}\\
&\text{No finite-positive-rate physical claim or Task-10 input is authorized.}
\end{aligned}
}
\]

---

# Appendix A — Rank-growth record at common times

| Step | Time | v3.5 equal-share cap256 | v3.7 equal-share cap512 blocked | v3.8 cap512 banked | v3.9 equal-share cap640 blocked |
|---:|---:|---:|---:|---:|---:|
| 2500 | 1.25 | rank 244 | rank 244 | rank 244/245 after resume | rank 244 |
| 2600 | 1.30 | failed before/around this region | rank 344 | rank 344 | rank 344 |
| 2700 | 1.35 | — | rank 458 | rank 458 | rank 458 |
| 2744 | 1.372 | — | required 514 > 512 | passed via later policy | passed with cap 640 |
| 2800 | 1.40 | — | — | retained 512, soft rank 519 | retained 588 |
| 2900 | 1.45 | — | — | retained 512, soft rank 526 | not reached as a reported completed progress point |
| 2909 | 1.4545 | — | — | cap-512 failure; equal rank 526, banked rank 516 | would have passed this previously known event by design |
| later than 2800 | >1.40 | — | — | — | new cap-640 failure before next report |

The table shows that the relevant object is the evolving spectrum and required-rank curve, not one isolated cap event.

# Appendix B — Approximate factor-memory scaling at \(N=12\)

| Retained rank | Logical factor memory | Three-Kraus logical expansion |
|---:|---:|---:|
| 256 | about 1.04 GiB | about 3.12 GiB |
| 512 | about 2.08 GiB | about 6.25 GiB |
| 640 | about 2.60 GiB | about 7.81 GiB |
| 768 | about 3.12 GiB | about 9.37 GiB |
| 1024 | about 4.17 GiB | about 12.50 GiB |

Blocked storage controls individual CuPy operand size but does not remove the detector-column work or dense Gram/eigensolver scaling.

# Appendix C — Mandatory preservation list

Preserve without overwriting:

```text
4900.Finite_rate_U2_100_00_spinor_upward_zero_primary_mB1
4901.Finite_rate_U2_100_00_spinor_upward_low_primary_mB1
4920.Task09_v3_5_...
4921.Task09_v3_6_...
4922.Task09_v3_7_...
4923.Task09_v3_8_...
4924.Task09_v3_9_...
```

For each failed family preserve:

- copied solver source;
- configuration and all contract JSON files;
- run-status and failure JSON;
- compression event JSON and spectrum NPZ;
- telemetry and numerical audits;
- checkpoints;
- stdout, stderr, and Slurm accounting;
- exact SHA-256 inventory.

