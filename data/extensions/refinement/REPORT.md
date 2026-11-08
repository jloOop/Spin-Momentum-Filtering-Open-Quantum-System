# P12 completed-control review and GMRES failure-path diagnosis

**Evidence date:** 12 September 2026. **Scope:** omega100, transverse mode00, zero upward/downward/dephasing rates; independent reductions of saved native arrays. No job was submitted, cancelled, restarted or modified. No installed numerical library was patched or upgraded. Full scientific acceptance remains false.

## Executive conclusion

All three completed P12 controls have now been reconstructed against their actual canonical comparison partners. The complete signed-law differences, including the terminal survival atom and using common output panels, are **0.6903% for downward insertion refinement, 1.1550% for dephasing insertion refinement, and 2.2150% for upward detector-step refinement**. All three retain their terminal susceptibility signs.

The supplied CuPy GMRES implementation also contains an unguarded Arnoldi normalization. A CPU mirror of that control flow raises the same SVD exception on an exactly solvable, finite identity-matrix system. This establishes a reproducible failure path in the supplied algorithm, but does **not** identify the actual cause of historical job2878880: its failing Hessenberg matrix and incoming branch vector were not saved.

The smallest next computation is an isolated GPU validation of a guarded solver candidate, not another metadata transfer and not immediate submission of the three omega144 production cases. A non-submitting GPU micro-validation candidate is included. It has **not** been run on a GPU and is not authorized for production.

## 1. Input identity and completeness

Input `Task0708_P12_CompletedEvidence.zip`:

```
cbe2ab1a3280377876c1c3e9d5916f5c55bb6d101d93dc3fe5b2efc6f409c291
```

This matches the uploaded sidecar. The ZIP passes CRC checks and has 68 verified export-manifest entries plus the manifest itself. All 42 native manifest entries in the three newly supplied results match their bytes. The uploaded collection helper with `(1)` in its filename is byte-identical to the previously supplied helper.

The collector snapshot was captured at **2026-09-12T12:06:41.568987+00:00**, on login5. Its input preflight fingerprint matches the actual earlier uploaded preflight ZIP. Its successful queue query has no P12 job listed. This is archived scheduler evidence, not a live query by this review.

Seven baseline cases were recovered directly from their nested `Task07.zip` case-share archives: D2, D2I, P2, P2I, U2, U2I and U4. The origin members, member hashes and extracted-file hashes are retained in `baseline_provenance.json`. All 196 extracted baseline files were checked. Across the ten reconstructed cases, **140 native manifest entries, 70 native NumPy containers and 430 array fields** were checked; all numeric fields are finite. This counts 21 new native containers plus 49 baseline containers. Auxiliary loader-derived arrays in the baseline archives were not substituted for native kernels.

The optional `_util.py` library file was absent in the collector. The supplied GMRES source contains its own `_make_system` and the relevant Arnoldi helper, so this absence does not prevent the stated source-code inspection. Compiled CUDA/BLAS binaries and the historical failing reduced matrix are not included. The current installed source snapshot is not proof of the historical node's exact library bytes.

Primary records: `input_identity.json`, `original/MANIFEST.json`, `original/COLLECTION_REPORT.json`, `fresh/audit.json`.

## 2. Reconciled operational status

| Case | Job | dt | ds | Accounting result |
|---|---:|---:|---:|---|
| P_I025 | 2867807 | 0.0005 | 0.025 | COMPLETED 0:0 |
| D_I025 | 2878878 | 0.0005 | 0.025 | COMPLETED 0:0 |
| U_DT250 | 2878879 | 0.00025 | 0.05 | COMPLETED 0:0 |
| U_DT125 | 2878880 | 0.000125 | 0.05 | FAILED 1:0 |
| D_Z2000 | 2878881 | 0.0005 | 0.05 | CANCELLED; zero runtime |
| U_Z2000 | 2878882 | 0.0005 | 0.05 | CANCELLED; zero runtime |
| P_Z2000 | 2878883 | 0.0005 | 0.05 | CANCELLED; zero runtime |

All seven are omega100/mode00 controls. The completed three have native exit3 and `PASS_CASE_LOCAL_RERUN_PENDING`. Native identical-prefix rerun checks remain pending. Their successful Slurm wrapper status does not change this.

No completed U_DT125 curve or Nz2000 control was reconstructed or invented. The cancelled jobs are not successful spatial controls. The omega144 insertion array2892221 is separate, and none of its prior evidence was modified. Task09 was not analyzed or changed.

## 3. Source and numerical-protocol comparison

The physical parameters, state ordering, projected oscillator/Pauli operators, Cayley matrices, midpoint loss functional and response-integration functions match between each relevant old/new pair. The fixed physical/configuration fields were checked explicitly.

For each old/new source pair, **120 top-level functions/classes match as parsed Python**. Two differ:

* `_task05_candidate_matches` adds stricter matching of longitudinal grid, endpoint convention, packet and spin parameters.
* `run_case` adds a P12 provenance field to the configuration payload.

The manual block changes the intended dt or ds, reference/output locations and stage number. These differences are retained in `source_diffs/` and `source_lineage.json`.

Do not identify the new full source/core hashes with the old canonical hashes: metadata and validation code inside the hashed core changed. The production algebra and propagation functions nevertheless match in the explicit comparison. No source was silently replaced or rehashed as an older source.

The recorded tolerances differ by environmental family:

| Family | Response-reference/branch rtol | Old Task05 regression rtol | P12 Task05 regression rtol |
|---|---:|---:|---:|
| Downward and dephasing | 1e-10 | 1e-8 | 1e-10 |
| Upward | 1e-12 | 1e-8 | 1e-10 |

The response-generating tolerances remain matched and unchanged within each comparison. The archived-regression reference role changed and is disclosed; it is not to be conflated with response-reference accuracy. The shared-insertion replay checks below quantify resulting cross-run agreement where dt is unchanged. These P12 conventions must not be silently substituted for the omega144 campaign's protocol.

## 4. Independent kernel reductions

Each source insertion has independent survival kernel K_S(t_i,s_q) and roof-panel kernel K_j(s_q). The reconstruction integrates these separately with the declared prefix trapezoidal source weights. It never derives the survival kernel from roof closure. The complete signed-law norm is

\[
A_{TV}=\frac12\left(\sum_j|\chi_j|+|\chi_S(T)|\right).
\]

The last term is right censoring, not a detector click. All coefficients are zero-rate susceptibilities, not finite-rate probabilities. The restricted mean response is `integral chi_S(t) dt`; it is not the conditional mean among detected trials.

### New completed cases

| Case | chi_D from survival | chi_mu* | Native-panel A_TV |
|---|---:|---:|---:|
| D_I025 | +0.00280616467561345 | -0.0189053215881960 | 0.00285601682879701 |
| P_I025 | +0.00458010923088736 | -0.0297253727113180 | 0.00465243670421346 |
| U_DT250 | -0.525696822464657 | +3.54597039265926 | 0.676985076288251 |

These values are additional refinement results, not silent replacements for the frozen canonical U2-I numbers or an updated Task08 acceptance aggregate.

### Common-panel comparisons

For a finer insertion/output grid, adjacent panel probabilities are added **before** absolute values or norms are taken. No click-density interpolation is used. At fixed output spacing, the direct same-panel difference is used. Define

\[
\epsilon_{TV}=\frac12\left(\sum_j|\chi_j^{new,common}-\chi_j^{old}|+|\chi_S^{new}(T)-\chi_S^{old}(T)|\right).
\]

The relative diagnostic below is epsilon_TV divided by the larger old/new-common A_TV. It is not divided by a possibly cancelling endpoint coefficient.

| Pair | Refinement | Change in chi_D | epsilon_TV | Relative |
|---|---|---:|---:|---:|
| D2I -> D_I025 | ds 0.05 -> 0.025 | -3.6713248884e-7 | 1.9716112895e-5 | 0.690297% |
| P2I -> P_I025 | ds 0.05 -> 0.025 | +1.5774915152e-6 | 5.3793129000e-5 | 1.155025% |
| U2I -> U_DT250 | dt 0.0005 -> 0.00025 | +0.00207365602694 | 0.0151835742565 | 2.215010% |

All three are below the recorded 5% single-comparison scale. This does not certify a combined uncertainty budget or establish all production acceptance requirements.

The upward endpoint changes by about 0.393% relative to the old magnitude, but its complete signed-law difference is about 2.215%. Thus endpoint agreement alone understates the curve-level detector-step sensitivity. The oscillatory late sector remains visible in both curves. This supports performing the remaining detector-step test after the execution path is validated, rather than dismissing it as unnecessary.

### Output quadrature and crossed-discretization checks

The comparison table separates changes of chi_mu* at common survival nodes from the finer output-quadrature contribution. For U4 -> U_DT250, the native change in chi_mu* is approximately 6.4833e-5, comprising a common-node difference 1.5716e-4 and an output-quadrature contribution -9.2327e-5. These should not be interpreted as the same quantity.

All four upward corners are now available at omega100/mode00:

```
(dt=.0005, ds=.1)      U2
(dt=.0005, ds=.05)     U2I
(dt=.00025, ds=.1)     U4
(dt=.00025, ds=.05)    U_DT250
```

On globally common ds=.1 output panels, the mixed finite difference

```
[U_DT250 - U2I] - [U4 - U2]
```

has complete signed-law norm **6.93365274466e-5**, with endpoint mixed difference **-2.10605350648e-6**. This is a useful observed cross-discretization diagnostic, not a continuum error bound and not validation of omega144 first-shell behavior.

### Internal consistency

| New case | Max tangent closure | Max per-insertion closure | Max source trace |
|---|---:|---:|---:|
| D_I025 | 2.7551e-11 | 1.2880e-11 | 3.8381e-17 |
| P_I025 | 3.9666e-11 | 1.8488e-11 | 7.2858e-17 |
| U_DT250 | 1.0136e-11 | 3.8402e-12 | 2.0428e-14 |

Noncausal saved kernel entries are exactly zero. Jump-plus-anticommutator kernels reproduce the total kernels. Reconstructed arrays agree with saved arrays to roundoff. The reduced tangent benchmark arrays were checked, but that check is a reduction of an archived benchmark, not another propagation.

At unchanged dt, shared-insertion replay discrepancies are 4.04e-14 for D2I/D_I025, 6.04e-14 for P2I/P_I025, and 1.13e-10 for U4/U_DT250. They support cross-run implementation consistency, not an automatic completion of the native rerun policy.

The saved source summaries provide bath-off survival nodes. They do not provide complete bath-off midpoint probability arrays, and this review did not manufacture those arrays by differentiation. The primary comparisons above are complete *susceptibility* laws, including their survival atoms.

## 5. GMRES failure-path investigation

The copied library metadata identifies CuPy 14.0.1, NumPy 2.4.3 and SciPy 1.17.1 in the collected environment snapshot. The actual historical failure source line agrees with the supplied `_iterative.py` line186. Neither matching metadata nor matching line numbers proves historical byte identity.

In the supplied implementation, each restart cycle unconditionally builds the requested Arnoldi dimension. It computes the next projected residual norm and then divides by that norm before checking for Arnoldi breakdown:

```python
cublas.nrm2(u, out=H[j+1, j])
if j+1 < restart:
    v = u / H[j+1, j]
    V[:, j+1] = v
```

The restart dimension is 30 in these runs, so the later least-squares problem normally involves a 31-by-30 Hessenberg matrix. This is not a diagonalization/compression of the full density operator.

An exactly solvable diagnostic illustrates the failure path. Set A=I and b=e1, x0=0, with identity preconditioner. After the first Arnoldi projection, u=0. The one-dimensional Krylov space already contains the solution, but the unguarded continuation divides 0 by 0. The later Hessenberg entries become nonfinite and NumPy's least-squares SVD raises `LinAlgError: SVD did not converge in Linear Least Squares`.

`diagnose_gmres.py` compiles a CPU mirror of the supplied gmres body with explicit NumPy replacements for the BLAS operations. The local numerical library was NumPy 2.3.5, not the remote NumPy 2.4.3 binary. The test therefore establishes the control-flow failure path, not a replay of GPU rounding or the original cluster state.

### Candidate safeguard, tested locally only

The isolated candidate checks the Arnoldi data before division. At exact/near breakdown, it solves the reduced least-squares problem and accepts a result only after the **true residual** satisfies the original target. Otherwise it raises an explicit diagnostic failure. It also rejects nonfinite input and does not report success on unconverged iteration exhaustion.

The candidate uses a test-only breakdown threshold of 64 machine epsilons times the current operator-vector norm. This is a criterion for stopping basis construction, **not** an enlarged solve tolerance. The true residual remains subject to rtol=1e-12 and atol=0. It is not an approved production policy yet.

Local results:

* The unguarded finite identity test reproduces the SVD exception and a nonfinite Hessenberg matrix.
* The guarded identity test returns the exact solution with zero residual.
* A regular finite nonsymmetric test returns bitwise-identical vectors on guarded and unguarded CPU paths, with residual below 1e-12.
* An inconsistent singular test and a nonfinite-input test are rejected, not accepted as convergence.
* Twelve one-step checks on reduced 96-dimensional Cayley matrices built from the exact submitted source pass. They use N=2, Nz=8, omega100/144, both detector steps and deterministic roof-probing vectors. These vectors are not the production packet and these are not three new preparation evolutions.
* The largest reduced relative residual is 1.7725e-16; relative difference from sparse direct solution is 2.3102e-16; midpoint-loss identity residual is 2.3161e-16.

The original failing H/e and incoming branch vector remain unavailable. Therefore **the historical cause is still unproven, and the production solver is not declared repaired**.

## 6. Implemented next validation and authorization boundary

`GPU_GMRES_Validation_Only.py` is a standalone **non-submitting** micro-validation candidate. It requires an allocated Slurm H100, explicit diagnostic acknowledgement and a new output directory. It pins the installed library source and submitted solver source hashes. It creates an isolated function namespace; it does not modify site-packages or rebind functions in a running production process. It compares native and candidate behavior on a synthetic breakdown case and twelve reduced one-step Cayley probes. It never calls `run_case` or a full insertion campaign.

The GPU script passed syntax and no-allocation refusal checks locally. It has **not run on a GPU**. A GPU PASS would certify only these microtests, not the historical failure mechanism or production convergence. No sbatch wrapper, automatic submission or reference-job chain is included in this review.

The next reviewed sequence should be:

1. Authorize one isolated GPU micro-validation gate.
2. If it passes, prepare a separate full-size selected-insertion diagnostic, preserving matched reference/branch tolerances and capturing any failure data. The failed third batch corresponds to source nodes8..11, or s={0.40,0.45,0.50,0.55}; these must be propagated through the declared horizon rather than stopped at a short startup test. This is derived from the saved case grid/batch size, not an identification of the exact failing column.
3. Capture H/e, residual/finite flags, the incoming vector/RHS and exact source/configuration identity on failure. A targeted linear-system replay need not rerun the whole insertion campaign, but it is not a restart of the frozen production kernel.
4. After that gate is reviewed, choose the necessary omega100 completion and omega144 detector-step tasks. The cancelled Nz2000 jobs require a new authorized scheduling decision; old cancelled dependencies will not run themselves.

A solver-method change must receive its own disclosed code/runtime identity. Keeping the original source file unchanged is not sufficient to claim an unchanged implementation when its GMRES function is substituted in an isolated namespace.

No additional copy of the completed P12 arrays or the omega144 insertion outputs is needed. Further bulk collection cannot recover the deleted historical failing matrices.

## 7. Reproducibility and limitations

`reconstruct_p12.py` was executed twice; all **17 outputs match byte-for-byte** in this local runtime. Its existing-output guard refused overwrite. Seven reduction tests passed, including source-weight partition, censoring and sum-before-norm rebinning. This is postprocessing reproducibility, not another full simulation.

Five figures were generated from reconstructed CSVs as PNG, SVG and vector PDF. All five PDFs were rendered with MuPDF and visually checked. The initial output-directory permission problem was corrected before successful figure generation.

The primary scientific limitations remain: finite representation, unresolved longitudinal-grid/representation closure, pending native rerun requirements, uncompleted DT125, and no omega144 excited-state detector-step/shell validation supplied here. Task09 compression and positive-rate validation are outside this review. No acceptance field was promoted.
