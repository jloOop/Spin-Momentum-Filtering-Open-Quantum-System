# Independent review: omega144 insertion refinement, array 2892221

**Review date:** 12 September 2026  
**Project:** Environmental Susceptibility of a Spin–Momentum Absorbing-Boundary Detector, Part I  
**Review status:** RECONSTRUCTED_INSERTION_COMPARISON_ONLY_NONACCEPTING  
**Scientific acceptance:** false  
**Production calculations performed in this review:** none.

## 1. Decision

The supplied result archive supports the independent insertion-only comparison for all three omega144 modes. A separately written saved-kernel reconstruction agrees with the supplied reductions and passes the declared insertion and shared-insertion replay criteria. The fixed-preparation signs at p=0.60 and p=0.95 survive the change Delta-s=0.10 to 0.05. At the unchanged old cancellation probability, the refined terminal response is +1.80655910e-6; its full signed timing-law response remains substantial.

This closes the previously missing review of the available insertion refinement. It does not certify detector-time-step, excited-state dynamical shell, longitudinal-grid/representation, or finite-rate uncertainties. It does not certify the switching probability to six decimals. Do not submit array2892221 again. Do not rerun propagation or alter the environment merely because the native solver reports exit3.

## 2. Evidence and verification boundary

The immutable input is `Task07_Omega144_Insertion05_PC2_Launch_20260907_v1_OUTPUT.zip`, 6,002,109 bytes, with SHA-256:

```
e6a64d22e9c9d81516e296484aac47b0d9686fbffdfd1c3dd42bf10da1e3d33b
```

This matches the uploaded sidecar and the earlier terminal record. The archive was unchanged after the review. All ZIP CRCs pass. All 132 export-manifest entries match; the archive contains 133 files including its manifest. All six native stable manifests, comprising 84 entries, also match. All 43 NumPy containers, 268 array fields, and 59 JSON documents were opened. Numeric arrays are finite and were loaded without pickle.

Two calculations were executed here, neither of which propagates a physical state:

1. The original supplied `analysis_code/recheck_export.py`, after source inspection, returned success. Its output is preserved in `original_offline_recheck.json`.
2. The new `reconstruct_refinement.py` independently integrated the survival and roof kernels, reconstructed mixtures and observables, and compared them with the exported arrays and tables. It imports neither the production solver nor the supplied reduction modules. Results are in `fresh/`.

The second calculation was run twice in separate output directories. All nine output files were byte-identical in this runtime. Its existing-directory guard correctly refused an overwrite. This is reproducibility of postprocessing, not a new deterministic production rerun. See `reproducibility_test.json`.

The export does not include Slurm accounting, submission receipts, worker-completion receipts, full propagation states, the full 40,001-node Task05 histories, or per-solve residual logs. These were not independently checked. Saved operator/reference/closure reports were inspected; their original propagation was not rerun. The reduced dense-versus-low-rank benchmark arrays were re-reduced, but the dense evolution itself was not executed again.

### Native completion record

The mode mapping follows the original launch package, not an inference from the newest jobs:

| Declared array element | Mode | Native completion UTC | Native status |
| --- | --- | --- | --- |
| 2892221_0 | 00 | 2026-09-08 16:30:31 | completed_pending, exit3 |
| 2892221_1 | 10 | 2026-09-09 19:05:56 | completed_pending, exit3 |
| 2892221_2 | 01 | 2026-09-10 20:24:14 | completed_pending, exit3 |

Each native verdict is `PASS_CASE_LOCAL_RERUN_PENDING`, with local checks passed. The rerun fields state that no applicable previous same-prefix result was available. Thus `rerun passed=false` does not establish a performed rerun disagreement.

The original external comparison was created at 2026-09-10T20:24:17+00:00 and records `PASS_INDEPENDENT_INSERTION_COMPARISON_ONLY_NONACCEPTING`. The exported evidence establishes saved-case completion and numerical comparison; final Slurm `COMPLETED 0:0` accounting still requires its own record.

## 3. Source identity and numerical protocol

The new fine saved sources are byte-identical to the original staged sources for all three modes. The original launch CONTRACT and its five comparison modules match this export byte-for-byte. The earlier coarse preparation export contributes 48 native evidence files that are byte-identical to this export's baseline copies. These are cross-upload checks, not reliance on the previous assistant's summary; see `cross_upload_provenance.json`.

All six baseline/fine numerical cores have SHA-256:

```
d665b92be5d1efb6954968833f4cf008672add6e8ed5194e9d8a55a2a498d796
```

The stage archive SHA-256 is:

```
95b2d3e75596a4ccd49413c0240d1195550d7e7299dba71eb9f2feca47282915
```

The matched physical and detector-step configuration is omega144, N=12 complete shells, 91 orbital modes and 182 spin-resolved channels, Nz=1500, Lz=20, Delta-t=0.00025, T=10, 40,000 detector steps, z0=10, Gaussian **amplitude** width 0.5, k0=kappa=pi, theta=pi/6, phi=0, complex128 state/solve arithmetic and float64 reductions. The stored ordering is `(s*M_N+mu)*N_z+k_z` and retains the documented permutation conventions. No alternative algebra, roof sign, absorber, or bath channel was substituted.

The endpoint-excluded float32 longitudinal grid remains literal: h_z=0.013333333656191826 and last coordinate 19.986665725708008. The name “750 reference” is a source identifier, not the longitudinal point count. The scalar and spinor common positive roof-loss form and Cayley midpoint probability convention are preserved in the unchanged production core.

Only insertion spacing changes: 0.1 to 0.05, stride 400 to 200, 101 to 201 nodes and 100 to 200 response panels. The physical horizon and number of detector steps do not change. Response-reference and branch GMRES relative tolerances remain matched at 1e-12. The archived Task05 regression references retain their distinct historical 1e-8 role.

### Two authority qualifications

**Native control exemptions.** The omega-not-100 source branch bypasses refinement-family checks with `NOT_REQUIRED_FOR_OMEGA1_CONFINEMENT_CONTROL`. Those returned true flags are exemptions, not omega144 detector-step or shell evidence. The separate external comparison is used for insertion refinement only. Source audits with a ground-state launch fingerprint must also not be misapplied to first-shell preparations: upward source activity is 3 for a first-shell number state rather than 2 for the ground state.

**Loose reference fingerprint.** The currently supplied standalone `750.Reference_closeQsys.py` hashes to `ba4a6bafc85f63cf3fa20164f3b78fe63414fe0d0fb20c6e2713208d222886df`. The native configuration's historical `reference_750_attached` fingerprint is `8cf2095b2d760a0b702c930fe5690fe762d08ad7c721a8c53b5ed498d1744009`. These are not the same file identity. This does not contradict the matched executed coarse/fine sources, staged release, and normalized numerical core; it prevents treating the current loose file as the exact historically fingerprinted attachment without further provenance. No replacement or repair was performed.

The supplied V9 manuscript is used for definitions and theory. Its descriptions of older campaign and Task09 states are historical, not live-status authority. In particular the accepted omega100 U2-I coefficients remain separate: chi_D=-0.527770479, chi_mu*=3.55724785, A_TV=0.685485610.

## 4. Reconstruction and observable definitions

The initial mixture is incoherent:

    rho_perp(p) = (1-p)rho00 + (p/2)(rho10+rho01).

Only p varies. This is not a coherent superposition or a temperature scan. The propagator, detector, bath direction, physical spin, longitudinal packet and horizon stay fixed. At each p the reference is that preparation's own bath-off detector law.

Let chi_j be the derivative at lambda_up=0+ of the roof probability on output panel j, and let chi_S(t) be the survival derivative. Then:

    chi_D^(S) = -chi_S(T)
    chi_D^(roof) = sum_j chi_j
    chi_mu* = integral_0^T chi_S(t) dt
    A_TV = 0.5 [sum_j abs(chi_j) + abs(chi_S(T))].

The terminal atom is survival/right-censoring, not a click at T. The restricted mean mu*=E[min(tau_D,T)] is not the conditional mean among detected trials. The signed susceptibility is not a positive-rate probability curve.

Survival is reconstructed from `kernel_survival`, independently of roof probabilities. For each output row, the source integral is a sum of elementary trapezoids over the saved insertion nodes. The roof response is reconstructed separately from `kernel_total_probability`. Both recycling/jump and anticommutator contributions are retained and their sum is checked. Affine mixtures are taken at the array level before norms and other nonlinear functions are evaluated.

For comparisons, two adjacent fine roof probabilities are summed onto each coarse panel. No click-density interpolation is used. Fine survival is restricted to the shared nodes. The complete signed-law discrepancy is:

    epsilon_TV(p) = 0.5 [sum_j abs(chi_f[2j]+chi_f[2j+1]-chi_c[j])
                        + abs(chi_S,f(T)-chi_S,c(T))].

Relative discrepancy is epsilon_TV divided by max(A_TV,coarse, A_TV,fine-common,5e-9), not by the possibly vanishing terminal chi_D. The declared external insertion-only gate is epsilon_TV <= 5e-9 +0.05*max(A_TV,coarse,A_TV,fine-common). The shared-insertion replay gate is 5e-9. These gates were inspected and left unchanged; passing them does not supply a total numerical uncertainty bound.

## 5. Mode-resolved results

| Mode | Coarse chi_D | Fine chi_D | Difference | Common-law discrepancy / scale |
| --- | --- | --- | --- | --- |
| 00 | -0.5221895123634 | -0.5221922277535 | -2.715390071e-06 | 0.04520962% |
| 10 | +0.1221704399925 | +0.1221733044980 | +2.864505440e-06 | 0.06301064% |
| 01 | +0.1221704399924 | +0.1221733044980 | +2.864505575e-06 | 0.06301064% |


The fine first-shell mean is +0.12217330449799085. Its two independently saved excited-mode endpoint responses differ by approximately 3.42e-14. The refined affine relation is:

    chi_D,fine(p) = -0.5221922277535029 + 0.6443655322514938 p.

This interpolation is an exact consequence of the linear finite-model response and incoherent mixture. The dense p sweep is not a set of independently propagated preparations.

The matched bath-off survival arrays coincide at all shared output nodes in the uploaded coarse and fine evidence. This is an expected control of the unchanged detector propagation; it is not a positive-rate bath-compression test.

## 6. FIXED-preparation test and crossing shift

| Fixed p | Coarse chi_D | Fine chi_D | Fine minus coarse | Fine restricted-mean response |
| --- | --- | --- | --- | --- |
| 0.6 | -0.1355735409499 | -0.1355729084026 | +6.325472760e-07 | +1.138501868581 |
| 0.810400321209 | -0.0000000000000 | +0.0000018065591 | +1.806559098e-06 | +0.406119046068 |
| 0.95 | +0.0899524423747 | +0.0899550278854 | +2.585510728e-06 | -0.079813704355 |


Own bath-off terminal survivals at the three fixed preparations are 0.6172192082473191, 0.6309404425561631, and 0.6400444205877773 respectively. No mixture was compared with the ground baseline alone.

Independent root calculations:

| Reduction | Coarse root | Fine root | Shift |
| --- | --- | --- | --- |
| Survival kernel | 0.8104003212089723 | 0.8103975175843096 | -2.8036246628e-6 |
| Roof kernel | 0.8104003212147743 | 0.8103975175902637 | -2.8036245107e-6 |

The fine survival and roof roots differ by 5.95413e-12. This is internal probability-closure consistency, not an uncertainty on the crossing. At the **fixed old** p=0.8104003212089722, the fine survival-based result is +1.80655909796934e-6 and the independent roof sum is +1.806555261302245e-6. The approximately 3.84e-12 difference is consistent with tangent closure. Nothing was retuned to force this test to zero.

The p=0.60 negative sign and p=0.95 positive sign survive this insertion refinement with discrepancies much smaller than their magnitudes. The tiny positive value at the old root should not be presented as a certified positive sign: the common-law insertion difference is approximately 1.56e-4 and other discretization errors remain unresolved. Nor does a two-grid shift establish an asymptotic order or a rigorous continuum error bound.

## 7. Full censored-law comparison and quadrature distinction

| Fixed p | Coarse A_TV | Fine A_TV, common panels | Fine A_TV, native panels | Common-law discrepancy | Relative discrepancy |
| --- | --- | --- | --- | --- | --- |
| 0.6 | 0.288855209936 | 0.288888696713 | 0.294670520775 | 1.656885364e-04 | 0.05735376% |
| 0.810400321209 | 0.200554133262 | 0.200572950815 | 0.205364539350 | 1.555110277e-04 | 0.07753340% |
| 0.95 | 0.241592382160 | 0.241617964962 | 0.244642108708 | 1.601346786e-04 | 0.06627598% |


At the old root, the fine native A_TV is 0.20536453935048654 while the fine response rebinned to coarse panels has A_TV=0.20057295081481125. Comparing the raw native norms would partly measure the resolution of sign changes inside output bins. It is not the correct sole insertion-error estimate. The direct common-law discrepancy is 1.55511027654526e-4, only 0.0775334% of the stated response scale.

The mean-response reduction also has an output-quadrature distinction. At the fixed old root:

    native fine chi_mu* - native coarse chi_mu* = +1.04436148294085e-4
    common-node survival-response integral difference = +1.01740229497526e-4
    fine output-quadrature contribution = +2.69591879648035e-6.

Their sum closes numerically. The reported fine native chi_mu*=0.4061190460675729 is the trapezoidal integral on its 0.05 survival grid. The same distinction is supplied for every selected p in `fixed_preparations.csv`.

The terminal response can cancel even though the full timing response is nonzero. At the fixed old p, the fine prompt and late roof contributions are approximately -0.129773931187473 and +0.129775737742734. Their sum is nearly zero, but the binned response norm and restricted-mean response are not. This is a redistribution of the same roof-click law, not an additional independent detector observable.

## 8. Source-time versus output-time decomposition

The same fixed divider 3.6 is applied to source time s and output time t. A source integral is partitioned into trapezoidal **intervals**; the endpoint at 3.6 naturally contributes half weights to adjoining intervals. This avoids double counting a boundary node or introducing an arbitrary pointwise gate convention.

| Fixed p | Early source -> prompt output | Early source -> late output | Late source -> late output |
| --- | --- | --- | --- |
| 0.60 | -0.194470700719004 | +0.121014160948741 | -0.062116368632494 |
| 0.8104003212089722 | -0.129773931187473 | +0.170112299286152 | -0.040336561543418 |
| 0.95 | -0.086847911904220 | +0.202688696041424 | -0.025885756258070 |

Late source -> prompt output is exactly zero in the stored causal kernels. At p=0.95:

    late output = +0.202688696041424 -0.025885756258070
                = +0.176802939783354.

Thus the positive late output is generated predominantly by early insertions, while late insertions contribute negatively. A late detector feature does not identify a late environmental action. The refined prompt output remains negative for both endpoint preparations and hence for all p in [0,1] by affinity; the terminal sign reversal across this family is driven by the late contribution.

This strengthens the proposed causal mechanism diagnostic. It is not an independently performed gated-bath experiment. For example, at p=0.95 the stored fine kernel predicts an early-source-only terminal coefficient +0.115840784137203 and late-source-only coefficient -0.025885756258070 under the corresponding unrescaled source-window convention. These are kernel-derived predictions for a possible intervention, not new simulation results or finite-rate validations.

## 9. Closure, replay, and what was freshly checked

| Fresh reduction check, maximum over six cases | Residual |
| --- | --- |
| Tangent survival plus cumulative roof response | 1.03642e-11 |
| Independent per-insertion survival/roof closure | 4.51417e-12 |
| Environmental source trace | 3.20854e-14 |
| Noncausal kernel entries | exactly 0 |
| Reconstructed survival vs saved response | 1.66533e-16 |
| Reconstructed roof panels vs saved response | 6.93889e-18 |
| Jump plus anticommutator vs total roof kernel | 4.33681e-19 |
| Re-reduced low-rank survival vs saved dense benchmark | 2.48655e-17 |
| Re-reduced low-rank roof probabilities vs saved dense benchmark | 1.00585e-21 |

The reduced benchmark is a separate small model, N_shell=2, Nz=32, D=384, Delta-t=0.002 and T=0.02. It is not a full-density solve of the production model through T=10. Likewise, the archived full-size closure pilot is an embedded check, not independent convergence in another discretization.

Shared-insertion replay compares the old insertion columns with the matching even fine columns, summing fine output intervals. The reconstructed replay-law discrepancies are 1.40005e-16,2.03173e-16,2.19137e-16 for modes 00, 10, 01. This is useful repeat-propagation consistency of the shared insertion contributions across the archived campaigns. It does not silently mark the native same-prefix deterministic-rerun requirement as satisfied, and it is not a time-step/shell/grid control.

These small closure residuals constrain bookkeeping and internal consistency. They do not bound a common discretization bias. The external 5% criterion was a scoped acceptance rule; the measured differences are much smaller, but no total error budget was manufactured from them.

## 10. Inventory before another computation

`existing_controls_inventory.csv` records native configurations, hashes and historical native statuses found in the additional project archives. This is an inventory, not a fresh re-analysis of every control's arrays.

- The descriptive upward sweep has exactly 30 cases: omega={1,4,10,25,36,64,100,144,169,200} times modes{00,10,01}. Actual per-case time steps are retained. No omega0 or16 data are introduced.
- Canonical Task07 material contributes 19 distinct source-version records for 18 case prefixes, including an explicitly retained duplicate-prefix version. It includes omega100 ground-state detector-step and N12-to16 shell controls, scalar nulls and the three-channel insertion family. N=16 is a shell cutoff, not a claimed omega16 sweep point. Historical local FAIL labels must be read with their original audits and the authoritative canonical aggregate; they are not automatically failures of the accepted U2-I family.
- Nine omega100 spin-angle controls were reconstructed in the previous review. Their result is not newly re-certified here and is not omega144 first-shell convergence evidence.
- This export contains no completed omega144 first-shell detector-step, excited-state dynamical-shell, or longitudinal-grid/representation family.
- Previously mentioned job IDs 2878878–2878883 still require accounting and exact configuration mapping before they can be counted as relevant controls. Their presence in earlier conversation is not current scheduler evidence.

The smallest operational next step is the supplied read-only monitor/accounting/receipt check, not another propagation campaign. The small missing records concern administrative lineage and whether useful controls already exist; the numerical kernels needed for this insertion review are now present. A larger copy of the same numerical archive is unnecessary.

If the inventory establishes that relevant controls do not exist, a focused proposal would next assess detector-step and excited-state shell stability at omega144 through T=10, followed by the required longitudinal-grid/representation assessment. No such proposal is authorized or submitted here, and an omega100 ground-state control is not substituted for it.

Task09 is kept separate. This export contains no new state or cumulative histories for continuation jobs 2894739 and 2895255. Their live status and positive-rate compression are not verified by this review. They were not touched, concatenated, resubmitted, or used to support a finite-rate claim.

## 11. Communication_Physics_Extension assessment

The present refinement supports three linked features within the frozen finite model: preparation-controlled endpoint signs, nonzero timing-law response at terminal cancellation, and delayed detector output generated by early environmental insertions. The affine zero by itself is not a new dynamical phase transition. Dense interpolation in p is not simulation volume that increases independent evidence.

The result removes an important insertion-discretization concern from this proposed extension. It does not, by itself, warrant changing the previously discussed PRA-first plan or asserting publication readiness for Communications Physics. That is a project-planning judgment, not a prediction of editorial outcome. The substantive remaining tasks are robust signs under the relevant remaining discretizations, a predictive intervention test, and selected physical robustness—not more unstructured omega or p sampling. No journal-policy research was undertaken in this numerical review.

A defensible current statement is: “At fixed confinement and detector settings, changing only an incoherent transverse preparation reverses the zero-rate upward-environment response of finite-window detection. The sign contrast, near-cancellation preparation, and source/output decomposition survive the tested insertion refinement; full convergence and intervention validation remain separate requirements.”

## 12. Files and reproducibility

See README.md for exact local reconstruction commands. The review ZIP includes the unchanged original result and checksum, the new reconstruction script, its nine fresh data files, the original offline-recheck result, cross-upload provenance, controls inventory, reproducibility test and six new figures in PNG/SVG/vector PDF. Original eight figures remain in the immutable original ZIP. All new figures use reconstructed arrays and are labelled as response or response differences, never finite-rate click probabilities. The final PNG figures were visually inspected and the six vector PDFs were rendered with MuPDF; no production source was edited.

**Relevant supplied theory:** V9, Sections 0.6 and 5 for zero-rate tangents and complete signed censored laws; Sections 2.2–2.3 for mixture linearity; Sections 1.5 and 4.6 for Cayley midpoint roof probabilities; Chapter 6 for the canonical-family versus remaining representation/grid qualifications. Numerical campaign status in V9 is historical. Actual archive kernels and pinned sources, rather than old prose, are the authority for the numbers above.

**End status:** insertion comparison reconstructed; scientific_acceptance=false; no job submitted, cancelled, modified, restarted or overwritten.
