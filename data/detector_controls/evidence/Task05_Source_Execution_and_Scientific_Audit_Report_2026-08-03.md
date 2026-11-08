# Task 05 Source, Execution, and Scientific Audit Report

**Project:** Part-I open-system absorbing-boundary detector  
**Audit date:** 3 August 2026  
**Audited source:** `05_oscillator_channel_detector_test.py`  
**Audited source SHA-256:** `9cfa32559a62882961f2fab33fd50e13cf9996d5b2db992d5bb1ca93380df86a`  
**Decision:** **TASK-05 SOLVER-LEVEL FAIL / CAMPAIGN BLOCKED**  
**Branch status:** not closed; Task 06 remains pending

---

## 1. Executive decision

The source-level reconstruction of the oscillator basis, Pauli matrices, projected operators, tensor ordering, spinor roof term, detector-loss identity, midpoint probability, output management, and zero-bath scope passed. The file compiled, its AST parsed, and the reduced three-map smoke test passed, including stable same-directory replacement for a repeated spinor case.

The complete frozen Task-05 campaign was **not** executed to completion. The first source-conforming production case attempted—authoritative factorized scalar, `OMEGA=100`, mode `00`, `N_SHELL=12`, `DT=5e-4`, `T_FINAL=10`—terminated at step 105 because survival increased by

\[
2.868256743227\times10^{-9},
\]

which exceeds the source's frozen per-step guard of \(2\times10^{-9}\). A separate 500-step diagnostic that merely relaxed this guard accumulated a roof/norm closure error of \(7.6690990\times10^{-7}\), proving that the issue is not solved by weakening the monotonicity test. A non-authoritative diagnostic with the factorized-branch GMRES tolerance tightened from \(10^{-8}\) to \(10^{-10}\) reduced the 500-step closure residual to \(1.67036\times10^{-10}\) and passed all gates. That change was **not** applied to the delivered source because the frozen GMRES convention is authoritative and any change requires a new audited solver version.

The intended production backend is CuPy, but this runtime has no CUDA device and no CuPy installation. The production-dimensional SciPy spinor benchmark completed 100 steps in 9.04 s wall time with 354,068 KiB peak resident memory. Extrapolation and an attempted long diagnostic show that the complete spinor refinement/cutoff campaign is not computationally credible in this CPU-only session. No unexecuted result is inferred.

Accordingly:

- the **algebraic and structural implementation passes**;
- the **reduced smoke and reduced mechanism controls pass**;
- the **frozen production solver does not receive a PASS**;
- none of the requested Task-05 production scientific comparisons is certified;
- Task 06 cannot independently close the branch until a corrected or GPU-verified Task-05 solver produces the complete frozen output set.

---

## 2. Authority review and conflicts resolved

The source hierarchy was applied in the requested order.

### 2.1 Audit-02 ordering conflict

The literal final Audit-02 source enumerates \(n_x\) ascending within each shell and stores the native \(K_N\) in orbital-first, physical-spin-fast order. The current master handoff and the explicit Task-05 request instead require complete shells with \(n_x\) descending and full storage

\[
\operatorname{{index}}(s,\mu,k_z)=(sM_N+\mu)N_z+k_z.
\]

The solver does not silently mix these conventions. It reconstructs both representations and applies an explicit unitary permutation. At \(N=12\), \(\omega=100\), the independent permutation residuals for \(a_x\), \(a_y\), and \(K_N\), and the permutation unitarity residual, were all exactly zero.

### 2.2 Reference-source provenance

The attached `750.Ref(5).py` has actual SHA-256

`8cf2095b2d760a0b702c930fe5690fe762d08ad7c721a8c53b5ed498d1744009`,

whereas the master audit records a historical frozen-reference hash beginning `815a470...`. The Task-05 source records both the actual attached hash and the historical provenance instead of asserting that they are identical.

### 2.3 Scalar-ABC prose sign versus implemented matrix

The `L_z` docstring in the attached reference describes a Robin form with the opposite prose sign, while the implemented roof diagonal is the one associated with

\[
\partial_z\psi=i\kappa\psi.
\]

The matrix body, the positive detector-loss identity, the master audit, and the manuscript agree. The matrix body was followed. A direct independent reconstruction of Task-05 `L_z` and the literal reference matrix gave zero matrix residual.

### 2.4 Time-step and horizon hierarchy

The V5 manuscript also discusses \(4\times10^{-4}\) and \(2\times10^{-4}\) reference/production steps at horizon 20. The current master Task-05 handoff supersedes those values for this stage and freezes the Audit-01 recovery campaign at horizon 10 with \(10^{-3}\) for \(\omega=1\) and \(5\times10^{-4}\) for \(\omega=100\), plus the stated refinements.

---

## 3. Complete source-level audit

| Item | Result |
|---|---:|
| Python compilation | PASS |
| AST parsing | PASS |
| Source size | 142,064 bytes; 3,516 lines |
| Visible manual block | PASS |
| One-case production entry point | PASS |
| Automatic production sweep | absent |
| Fixed stage directory | `4070.Oscillator_channel_detector_tests` |
| Timestamped/parameter-generated directories | absent |
| Same-prefix stale-file replacement | PASS in reduced rerun |
| Source copy and SHA-256 recording | PASS |
| Active Lindblad/bath/density-matrix/trajectory code | absent by AST executable-symbol audit |
| State and sparse matrix dtype | complex128 |
| Longitudinal grid | `endpoint=False`, \(N_z=1500\), \(L_z=20\) |
| Full production dimension at \(N=12\) | \(182\times1500=273{,}000\) complex amplitudes |

### 3.1 Oscillator and tensor audits at \(N=12\), \(\omega=100\)

| Audit | Maximum defect |
|---|---:|
| dimension formula and descending complete-shell order | 0 |
| lowering actions | 0 |
| interior raising actions | 0 |
| projected top-shell raising norm | 0 |
| adjoint identities | 0 |
| number diagonals | \(1.7763568394\times10^{-15}\) |
| minimum number-operator eigenvalue | 0 |
| exact projected commutators | \(7.1054273576\times10^{-15}\) |
| oscillator Bohr relation, relative | \(2.1679136271\times10^{-15}\) |
| \(H_{{\perp,N}}\) formula | \(2.2737367544\times10^{-13}\) absolute |
| \(K_N\) Hermiticity | 0 |
| \(K_N\) ladder/momentum agreement | 0 |
| \(K_N/\sqrt{{\omega}}\) invariance | \(4.4408920985\times10^{-16}\) |
| explicit spin-major \(K_N\) action | \(7.6016345010\times10^{-14}\) |
| Audit-02-to-Task-05 permutation | 0 |
| full-state index formula | exact |

All declared operator checks passed their source thresholds.

---

## 4. Spinor roof-term sign derivation and matrix verification

At the roof, the required entrance law is

\[
\partial_z u=(i\kappa I-K_N)u.
\]

With a centered ghost derivative,

\[
u_{{R+1}}-u_{{R-1}}=2h_z(i\kappa I-K_N)u_R.
\]

Substitution into the validated half-weight roof row of \(-\tfrac12\partial_z^2\) gives

\[
-\frac{i\kappa}{2h_z}I+\frac{1}{2h_z}K_N.
\]

Therefore the coupled-channel Hamiltonian must contain

\[
\boxed{{+\frac{1}{2h_z}K_N\otimes P_R}}.
\]

For \(N=12\), \(\omega=100\), \(h_z=0.013333333656191826\):

| Matrix check | Result |
|---|---:|
| coefficient \(1/(2h_z)\) | 37.49999909196051 |
| correct plus-sign roof-block residual | 0 |
| roof-neighbor block residual | 0 |
| random full-matrix action relative residual | \(1.4524802753\times10^{-16}\) |
| detector-loss roof identity residual | 0 |
| incorrect minus-sign candidate residual | 1,837.1172626027146 |

Since \(K_N\) is Hermitian, it contributes no anti-Hermitian detector loss. The loss remains

\[
i(H-H^\dagger)=\frac{\kappa}{h_z}I_{{d_N}}\otimes P_R.
\]

---

## 5. Compilation and reduced smoke execution

The exact delivered source compiled successfully. A fresh reduced CPU smoke used \(N=2\), \(N_z=96\), \(\omega=4\), \(\Delta t=2\times10^{-3}\), five steps, and a packet deliberately placed near the roof. This is a structural smoke test, not production data.

| Propagator | Final \(S\) | \(D_{{\rm roof}}\) | max true residual | min \(p_D\) | relative closure | max top shell |
|---|---:|---:|---:|---:|---:|---:|
| scalar factorized | 0.9863754752041474 | 0.0136245280317473 | \(9.8986505\times10^{-9}\) | 0.0026956847761 | \(2.37505\times10^{-7}\) | 0 |
| scalar monolithic | 0.9863757662727263 | 0.0136242336882230 | \(1.4913808\times10^{-10}\) | 0.0026956341587 | \(2.86629\times10^{-9}\) | 0 |
| spinor | 0.9863762615359123 | 0.0136237383940870 | \(1.7914096\times10^{-10}\) | 0.0026955730845 | \(5.13816\times10^{-9}\) | \(1.08538\times10^{-7}\) |

All smoke arrays were finite; GMRES return codes were zero; midpoint losses were nonnegative; survival was monotone; launch identities passed. The complete smoke invocation used 0.89 s wall time and 144,032 KiB peak resident memory.

The spinor case was executed twice with the same prefix in the same fixed directory. The script removed every stale same-prefix product and the stable output hashes matched exactly on rerun.

---

## 6. Reduced scalar-null and monolithic-convergence controls

These controls use the reduced smoke geometry and do **not** replace the frozen \(\omega=100\), \(T=10\) campaign.

### 6.1 Authoritative factorized scalar null

| Comparison | max \(|\Delta S|\) | max \(|\Delta p_D|\) | complete censored-law \(d_{{\rm TV}}\) | \(W_1\) |
|---|---:|---:|---:|---:|
| 10 versus 00 | 3.330669073875e-16 | 2.168404344971e-18 | 1.136243876765e-16 | 1.332267629550e-18 |
| 01 versus 00 | 3.330669073875e-16 | 2.168404344971e-18 | 1.136243876765e-16 | 1.332267629550e-18 |
| 10 versus 01 | 0.000000000000e+00 | 0.000000000000e+00 | 0.000000000000e+00 | 0.000000000000e+00 |

The factorized scalar map is therefore mode invariant to floating-point precision in the reduced test.

### 6.2 Monolithic finite-step artifact

| Step | \(R_h=d_{{\rm TV}}(\nu_{{10}},\nu_{{00}})\) |
|---:|---:|
| \(h=2\times10^{-3}\) | 7.378282356136e-07 |
| \(h/2=10^{-3}\) | 1.844001322616e-07 |
| ratio \(R_h/R_{{h/2}}\) | **4.001234850346** |

The reduced ratio lies inside the required 3.5–4.5 band and confirms the expected global second-order disappearance of the monolithic scalar artifact. It is a numerical diagnostic, not a scalar physical response.

---

## 7. Reduced spinor isotropy and source diagnostics

For reduced spinor modes 10 and 01:

| Metric | Value |
|---|---:|
| maximum survival difference | 0.000000000000e+00 |
| maximum midpoint-step difference | 8.673617379884e-19 |
| complete censored-law \(d_{{\rm TV}}\) | 8.673617379884e-19 |
| \(W_1\) | 0.000000000000e+00 |

For the reduced ground-state launch, the exact source identities were

\[
s_\downarrow(0)=0,\qquad s_\phi(0)=0,\qquad s_\uparrow^{(N)}(0)=2.
\]

After near-roof spinor interaction, the smoke test generated

\[
\max_t s_\downarrow(t)=1.9512369162\times10^{-4},
\]

\[
\max_t s_\phi(t)=1.9532173194\times10^{-4},
\]

with maximum normalized top-shell population \(1.0853847361\times10^{-7}\) and accumulated omitted-\(K\) proxy \(8.8791024551\times10^{-9}\). In the corresponding factorized scalar ground-state smoke, \(s_\downarrow\), \(s_\phi\), the top-shell population, and the omitted-\(K\) proxy remained exactly zero in recorded arithmetic, while \(s_\uparrow^{(N)}=2\) remained exact.

This establishes only detector-present source activation in a reduced zero-bath smoke calculation. It is not a damping, heating, dephasing, temperature, or detector–bath susceptibility result.

---

## 8. Production-dimensional checks and the blocking defect

### 8.1 Short spinor benchmark

A production-dimensional spinor case used

\[
N=12,\quad M_N=91,\quad d_N=182,\quad N_z=1500,
\]

for a full vector dimension of 273,000, with \(\omega=100\), mode 00, \(\Delta t=5\times10^{-4}\), and 100 steps.

| Check | Result |
|---|---:|
| operator and roof-sign gates | PASS |
| GMRES failures | 0 |
| maximum true residual | \(9.59956137\times10^{-9}\) |
| minimum midpoint probability | \(1.22640251\times10^{-176}\) |
| maximum survival increase | \(5.76316772\times10^{-12}\) |
| roof/norm closure residual | \(2.66244138\times10^{-10}\) |
| maximum top-shell population | \(5.39879403\times10^{-127}\) |
| wall time | 9.04 s |
| peak resident memory | 354,068 KiB |

The packet has not reached the roof at \(T=0.05\); detector reductions and the built-in Cartesian target difference at this horizon are scientifically meaningless and were ignored.

### 8.2 Short factorized scalar benchmark

The same production dimensions and 100 steps in the factorized scalar branch gave zero GMRES failures and a maximum true residual of \(5.34276101\times10^{-9}\), but survival drifted upward by \(9.03122419\times10^{-8}\) cumulatively while physical roof loss was only \(3.27\times10^{-112}\). The required roof/norm closure gate failed.

### 8.3 Frozen \(T=10\) campaign attempt

Exact configuration:

```text
PROPAGATOR_TYPE = scalar_factorized
INITIAL_MODE     = 00
OMEGA            = 100
N_SHELL          = 12
DT               = 5e-4
T_FINAL          = 10
full steps       = 20000
configuration SHA-256 = a6c7cf12ba7a75fa8c9be65147c08e7ea06da56ebad991822a2a46b33928fe7d
source SHA-256        = 9cfa32559a62882961f2fab33fd50e13cf9996d5b2db992d5bb1ca93380df86a
```

The case terminated at step 105 with process exit status 1:

```text
RuntimeError: Survival increased by 2.868257e-09 at step 105
```

No production output hash manifest exists because the case did not complete.

### 8.4 Defect-isolation tests

| Diagnostic | Source conforming? | Steps | max true residual | max step increase | closure residual | Verdict |
|---|---:|---:|---:|---:|---:|---|
| merely relax monotonicity guard | no | 500 | \(9.9999762\times10^{-9}\) | \(2.8682567\times10^{-9}\) | \(7.6690990\times10^{-7}\) | FAIL |
| tighten factorized GMRES rtol to \(10^{-10}\) | no | 500 | \(4.3480750\times10^{-11}\) | \(3.4061642\times10^{-13}\) | \(1.6703638\times10^{-10}\) | PASS |

The first diagnostic proves that relaxing the monotonicity gate would hide a growing closure failure. The second isolates Krylov accuracy as the proximate cause on the available SciPy backend. It does not authorize a source change by itself.

---

## 9. Frozen campaign completion table

### 9.1 Baseline recovery

| Required block | Cases | Completed production cases |
|---|---:|---:|
| \(\omega=1\), scalar factorized, modes 00/10/01, \(N=12\), \(dt=10^{-3}\), \(T=10\) | 3 | 0 |
| \(\omega=1\), spinor, modes 00/10/01 | 3 | 0 |
| \(\omega=100\), scalar factorized, modes 00/10/01, \(dt=5\times10^{-4}\) | 3 | 0; mode 00 failed at step 105 |
| \(\omega=100\), spinor, modes 00/10/01 | 3 | 0 |

### 9.2 Convergence blocks

| Required block | Status |
|---|---|
| monolithic scalar \(\omega=100\), modes 00/10, \(dt=5\times10^{-4}\) and \(2.5\times10^{-4}\) | not executed at production horizon |
| optional \(1.25\times10^{-4}\) | not triggered because production ratio was never obtained |
| spinor time-step refinement, modes 00/10, \(dt=2.5\times10^{-4}\) | not executed |
| spinor shell convergence \(N=8,12,16\), modes 00/10 | not executed |

Because the authoritative scalar control failed before the first detector encounter, proceeding to the expensive spinor campaign would violate the ordered Task-05 acceptance logic. In addition, the intended CuPy backend was unavailable and the complete CPU spinor campaign would require hours rather than a defensible audit run.

---

## 10. Requested scientific reductions: established versus pending

| Reduction | Current status |
|---|---|
| \(S(t)\), midpoint \(g(t)\), \(D(T)\), \(\mu^*(T)\), \(D_E\), \(D_L\), late fraction | calculated only for reduced smoke and short benchmarks; no production result |
| complete censored-law TV | reduced scalar null, reduced monolithic halving, and reduced spinor isotropy only |
| \(W_1\) survival distance | reduced controls only |
| 10/01 isotropy | exact/floating-point-floor in reduced controls; production pending |
| Cartesian–oscillator discrepancy | pending; short-horizon built-in comparison was rejected as incommensurate |
| production time-step differences | pending |
| \(N=12\to16\) shell differences | pending |
| shell populations/top shell | reduced and short benchmark only |
| \(s_\downarrow,s_\uparrow^{(N)},s_\phi\) | reduced source activation established; production curves pending |

No statement is made about a physical bath, temperature, damping, heating, or dephasing effect on the click law. No detector–bath susceptibility has been calculated.

---

## 11. Solver-level decision

\[
\boxed{{\text{{TASK 05: FAIL / BLOCKED AT THE PRODUCTION SOLVER GATE}}}}
\]

This is not a rejection of the oscillator-channel physics. It is a failure to certify the current source under the frozen production campaign and available backend.

The exact reasons are:

1. the first authoritative factorized scalar production case aborted at step 105;
2. weakening the monotonicity guard does not restore probability closure;
3. the intended CuPy production backend could not be executed in this environment;
4. no production baseline, time-step, shell-cutoff, or Cartesian-recovery table is therefore complete;
5. Task 06 cannot independently close an incomplete solver output set.

---

## 12. Unresolved issues and required next action

1. **Factorized scalar Krylov accuracy.** Test the unchanged source on the intended CuPy backend for at least 500–1000 pre-arrival steps at the production dimensions. If closure still fails, create a new audited solver revision using tighter factorized-channel GMRES convergence or an explicitly justified refinement strategy. Do not relax the survival or closure gates.
2. **Frozen-convention conflict.** Any tighter tolerance changes a frozen numerical convention and must be documented as a defect correction, given a new source hash, and revalidated against `750.Ref` and the three-map smoke.
3. **Production backend.** Execute the corrected/verified source on the target GPU, one manual case at a time.
4. **Representation comparison guard.** Cartesian target differences should be emitted only when horizon, mode, detector, confinement, and other common physical inputs match. The short benchmark's incommensurate built-in difference was ignored.
5. **Undefined pre-arrival conditional means.** When detected probability is numerically zero or negative because of solver drift, click-conditioned means should be reported as undefined rather than as very large signed numbers.
6. **Task 06.** Begin only after every required Task-05 case has a completed run status and a stable hash manifest.

---

## Appendix A — Complete executed-case registry

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


## 13. Files generated by this audit

- `Task05_Source_Execution_and_Scientific_Audit_Report_2026-08-03.md`
- `Task05_executed_case_summary_2026-08-03.csv`
- `Task05_compact_audit_summary_2026-08-03.npz`
- `Task05_source_audit_2026-08-03.json`
- `NUM_Open_System_PartI_Master_Audit_Audit00_to_Task05_and_Task06_Handoff_2026-08-03.md`

The original master file and the original Task-05 solver source were left unchanged.
