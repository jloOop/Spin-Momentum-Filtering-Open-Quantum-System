# Stage 02 — Complete Code Audit and Execution Record

**Project:** Environmental susceptibility of the spin–momentum absorbing-boundary detector  
**Stage:** 02 — transverse bath-operator tests  
**Audit date:** 2 August 2026  
**Final audited scripts:**

- `4050_bath_operator_tests_solver.py`
- `4051_bath_operator_tests_loader.py`

## 1. Scientific decision

The replacement Stage-02 implementation is accepted as a **transverse-operator certification layer**.
It passes the complete local solver/loader audit described below.

The stage deliberately contains:

- no scalar or spinor detector propagation;
- no absorbing-boundary matrix;
- no Crank–Nicolson or GMRES step;
- no Lindblad time evolution;
- no bath rates;
- no claim about trace preservation, Gibbs stationarity, detector–bath composition, or environmental susceptibility.

Its sole purpose is to certify the oscillator operators that later enter the trace-preserving transverse bath.
The authoritative representation is a projected complete-shell oscillator basis.  The Cartesian construction is retained only as a low-mode cross-check against the validated Stage-01 conventions.

## 2. Source requirements used

The Stage-01 handoff requires Stage 02 to verify

\[
a_x|00\rangle\simeq0,\qquad a_y|00\rangle\simeq0,
\]

\[
a_x|10\rangle\simeq|00\rangle,\qquad
a_y|01\rangle\simeq|00\rangle,
\]

\[
a_x^\dagger|00\rangle\simeq|10\rangle,\qquad
a_y^\dagger|00\rangle\simeq|01\rangle,
\]

as well as adjoint consistency, positivity of the number operators, number occupations, x/y isotropy, commutator defects, and lateral-wall leakage.  It also specifies that the complete-shell oscillator basis is authoritative and that the Cartesian realization is only a low-mode cross-check.

The reviewed Stage-01 scripts establish the user’s directory convention: a manually named, reusable output folder rather than timestamped or automatically parameter-generated directories.  The detector reference scripts establish the numerical core that must remain untouched.  Stage 02 records their fingerprints for provenance but neither imports nor executes them.

Reviewed source fingerprints:

| Source | SHA-256 |
|---|---|
| `750.Ref(3).py` | `8cf2095b2d760a0b702c930fe5690fe762d08ad7c721a8c53b5ed498d1744009` |
| `4002_reference_regression(1).py` | `facecb007572b5409d9d1ddb34c874a234f0d70059780551dc2179a7d66d8b48` |
| `4031_static_mode_library(2).py` | `eee0326442a7ddde4cc423f63c916810adec6f77202a72817db5f60f384b7dea` |
| `4032_static_mode_library(1).py` | `11a7316ed997aa36f271ea47c2f1272dae86606053da6a84df958630e7fbf9b9` |
| `NUM_Stage01_Static_Mode_Complete_Audit_and_Next_Workflow_2026-08-02(3).md` | `7b2444f5b10bcd3a86a2d301a40ebcaf2e88b8b28d329c8d3e069c4e97fc6f65` |

## 3. Fixed directory and file ownership

Both scripts use exactly one manually fixed directory:

```text
<OUTDIR>/4050.Bath_operator_tests
```

There are no timestamps and no folders generated from \(\omega\), grid size, cutoff, or other parameters.

A repeated solver run intentionally replaces only the files owned by Stage 02 in this same directory.  It removes stale loader products before writing new solver results, preventing an old report from being mistaken for a new run.  It does not remove unrelated files outside the Stage-02 ownership list.

## 4. Authoritative complete-shell construction

The retained transverse index set is

\[
\mathcal I_N=\{(n_x,n_y)\in\mathbb N_0^2:n_x+n_y\leq N\},
\qquad N=12.
\]

The retained dimension is

\[
M_\perp(N)=\frac{(N+1)(N+2)}{2}=91.
\]

The projected annihilation matrices are constructed directly from

\[
a_x|n_x,n_y\rangle=\sqrt{n_x}\,|n_x-1,n_y\rangle,
\qquad
a_y|n_x,n_y\rangle=\sqrt{n_y}\,|n_x,n_y-1\rangle,
\]

and

\[
a_j^{(N)}=P_Na_jP_N.
\]

The creation matrices are not independently guessed:

\[
a_x^\dagger=(a_x)^\dagger,\qquad
a_y^\dagger=(a_y)^\dagger.
\]

The number operators are

\[
N_x=a_x^\dagger a_x,\qquad
N_y=a_y^\dagger a_y,\qquad
N_\perp=N_x+N_y.
\]

The cutoff \(N=12\) is suitable for a stringent algebraic test and is compatible with the first low-temperature preparation scale discussed in the project.  It is **not** declared to be the converged dynamical cutoff of a later bath calculation.

### 4.1 Correct projected commutator test

A finite matrix cannot satisfy \([a,a^\dagger]=I\) on its entire finite space because the trace of every commutator is zero.  Therefore the script does not impose the mathematically impossible full-space identity.

Instead it verifies the exact projected formulas.  In the interior shells, the canonical relation holds.  On the upper shell, the raising action is projected out and the corresponding diagonal and cross-axis defects are checked explicitly.  This is the correct complete-shell certification of \(P_NaP_N\).

The number-ladder relations are checked independently:

\[
[N_x,a_x]=-a_x,\qquad [N_x,a_x^\dagger]=a_x^\dagger,
\]

and analogously for the y direction, together with the vanishing cross-axis number commutators.

### 4.2 Transverse Hamiltonian and Bohr identities

For each frozen confinement \(\omega\in\{1,100\}\), the solver constructs

\[
H_\perp=\hbar\omega(N_\perp+I)
\]

and verifies

\[
[H_\perp,a_j]=-\hbar\omega a_j,
\qquad
[H_\perp,a_j^\dagger]=+\hbar\omega a_j^\dagger.
\]

The loader reconstructs these identities independently from the saved matrices.

### 4.3 Spin–momentum boundary operator consistency

Although Stage 02 contains no detector propagation, it verifies that the same oscillator graph reproduces the transverse operator entering the later spinor boundary:

\[
K=\frac{i}{\sqrt{2}\,\ell_\perp}
\left[
\sigma_x(a_y^\dagger-a_y)-
\sigma_y(a_x^\dagger-a_x)
\right].
\]

In transverse-basis-first tensor ordering, the implemented matrix is

\[
K=\frac{i}{\sqrt{2}\,\ell_\perp}
\left[
(a_y^\dagger-a_y)\otimes\sigma_x-
(a_x^\dagger-a_x)\otimes\sigma_y
\right].
\]

It is checked against

\[
K=\frac{p_y}{\hbar}\otimes\sigma_x-
\frac{p_x}{\hbar}\otimes\sigma_y,
\]

for Hermiticity and for the required \(K\propto\sqrt\omega\) scaling.

## 5. Cartesian Stage-01 cross-check

The Cartesian test reproduces the relevant Stage-01 conventions:

- \(L_x=L_y=10/\sqrt\omega\);
- `linspace(..., endpoint=False)`;
- explicit sidewall clamping;
- the same analytic low-mode formulas \(|00\rangle,|10\rangle,|01\rangle\);
- uniform quadrature \(h_xh_y\);
- centered first derivatives on the active interior nodes.

In units \(m=\hbar=1\),

\[
a_j=\sqrt{\frac{\omega}{2}}X_j+
\frac{1}{\sqrt{2\omega}}D_j,
\qquad
a_j^\dagger=\sqrt{\frac{\omega}{2}}X_j-
\frac{1}{\sqrt{2\omega}}D_j.
\]

The fixed suite is

\[
\omega\in\{1,100\},\qquad
N_x=N_y\in\{50,100,200\}.
\]

Because

\[
\eta=\sqrt\omega\,h=10/N,
\]

is independent of \(\omega\) under the Stage-01 box scaling, the \(\omega=1\) and \(100\) dimensionless residuals must collapse.  The grids 50, 100, and 200 independently establish the expected second-order centered-difference convergence rather than accepting a single-grid residual by inspection.

## 6. Solver/loader separation

### Solver: `4050_bath_operator_tests_solver.py`

The solver constructs the matrices and raw metrics, saves the authoritative matrices and Cartesian reference arrays, and writes a preliminary acceptance record.  It returns:

- `0` when all solver gates pass;
- `2` when the calculation completes but a scientific gate fails;
- a nonzero Python failure when construction or I/O fails.

### Loader: `4051_bath_operator_tests_loader.py`

The loader does not import the solver and does not trust the solver PASS flag.  It independently:

1. verifies all hashed stable solver products;
2. verifies the frozen configuration and its internal SHA-256 records;
3. verifies the copied solver source hash;
4. reconstructs every complete-shell operator metric from the saved matrices;
5. independently rebuilds all six Cartesian cases;
6. independently recomputes convergence and \(\omega\)-collapse tables;
7. independently applies all acceptance thresholds;
8. compares every solver CSV and every acceptance metric, threshold, relation, and pass/fail decision;
9. writes the final report only after these checks.

This avoids circular validation in which a solver simply confirms numbers generated by its own formulas.

## 7. Static and execution audits performed

### 7.1 Source-level audit

- Python compilation: PASS
- Python AST parsing: PASS
- only standard-library modules plus NumPy are imported
- no CuPy/CuPyX import
- no GMRES call
- no Crank–Nicolson matrix
- no detector matrix or detector propagation
- no runtime import of the Stage-00 or Stage-01 detector scripts

References to the detector scripts occur only in comments and frozen provenance fingerprints.

### 7.2 Clean full execution

A clean solver/loader run completed with

```text
solver return code = 0
loader return code = 0
```

### 7.3 Fixed-directory reuse

The complete solver/loader chain was executed again in the same existing directory.  It completed with return code zero for both scripts and reproduced a PASS result.  This verifies the intended non-timestamped reuse behavior.

### 7.4 Tamper detection

A copy of one hashed solver CSV was deliberately modified.  The independent loader rejected the dataset and wrote `Stage02_loader_failure.json`, reporting the expected and observed SHA-256 values.  The loader returned nonzero.  This verifies stale/corrupted-result detection.

## 8. Numerical audit results

### 8.1 Authoritative complete-shell layer

| Check | Maximum defect |
|---|---:|
| all projected lowering/raising actions | `0.000000e+00` |
| adjoint consistency | `5.553085e-16` |
| number-operator identity | `1.776357e-15` |
| exact projected commutator formulas | `7.105427e-15` |
| Bohr relations | `2.167914e-15` |
| transverse-Hamiltonian formula | `0.000000e+00` |
| K Hermiticity | `0.000000e+00` |
| K ladder/momentum formula | `0.000000e+00` |
| K/\(\sqrt\omega\) scale collapse | `4.440892e-16` |

### 8.2 Cartesian reference case

For \(\omega=100\) and \(N_x=N_y=100\):

| Quantity | Value |
|---|---:|
| maximum ladder-action residual | `4.260196e-03` |
| maximum number-occupation error | `2.478728e-03` |
| maximum low-mode CCR action residual | `9.654272e-03` |
| maximum cross-commutator action residual | `1.631912e-15` |
| maximum x/y isotropy defect | `1.734723e-18` |
| maximum wall-leakage metric | `1.482597e-10` |

Across the full refinement suite:

- minimum measured convergence order: `1.962974`;
- maximum \(\omega=1/100\) scale-collapse difference: `3.747003e-14`.

All 22 declared acceptance gates passed.  The loader verified ten stable solver hashes and independently reproduced the solver decision.

## 9. Output products

The solver writes, among other products:

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
```

The loader writes:

```text
Stage02_loader_audit.json
Stage02_loader_case_metrics.csv
Stage02_loader_convergence_metrics.csv
Stage02_loader_omega_collapse_metrics.csv
Stage02_bath_operator_report.md
Stage02_loader_output_hashes.json
```

## 10. Exact cluster commands

```bash
OUTDIR=[ARCHIVE_PATH] \
python 4050_bath_operator_tests_solver.py
```

Then:

```bash
OUTDIR=[ARCHIVE_PATH] \
python 4051_bath_operator_tests_loader.py
```

Both commands use

```text
[ARCHIVE_PATH]
```

and intentionally reuse it.

## 11. Scope boundary and next gate

A Stage-02 PASS establishes the transverse operator layer only.  It does not yet establish:

- a CPTP detector-free bath evolution;
- trace preservation during time propagation;
- positivity of propagated density matrices;
- zero-temperature ground-state stationarity;
- analytical occupation relaxation;
- projected Gibbs stationarity or detailed balance;
- coherent-amplitude decay;
- pure-dephasing invariants;
- shell-overflow control under dynamics;
- detector–bath composition;
- the scalar dynamical null;
- any spinor environmental susceptibility.

Those are Stage 03 and later tests.  In addition, the unresolved Stage-01C scalar finite-step control remains a separate prerequisite before combined detector–bath production.  Stage 02 can be certified independently because it contains no detector propagation.

## 12. Final script fingerprints

| File | SHA-256 |
|---|---|
| `4050_bath_operator_tests_solver.py` | `2ed0daf88dca64d33896d42e53d93c1e57b85d7e22391498babd4f7588b273b2` |
| `4051_bath_operator_tests_loader.py` | `398a66b51c21e72216da38ef446c4e0e0012b0c23e2d6114b12b19e54e4bfc0b` |

These two scripts replace the earlier provisional Stage-02 files.
