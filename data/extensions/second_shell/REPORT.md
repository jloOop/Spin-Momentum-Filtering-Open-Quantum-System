# Independent review: omega144 second-shell detector library

## Executive conclusion

The three new second-shell preparations and the two first-shell diagnostic replays are complete through T=20 in the supplied native records. The independently reconstructed uniform second-shell law agrees with the pre-submission launch-kernel prediction across all common probability panels and the censoring atom, not just the endpoint. Scientific acceptance remains false; this is a verification of the declared finite implementation, not a new continuum or discretization-convergence certificate.

The most informative new physical observations are:

1. Uniform second-shell detection exceeds first-shell detection by 0.0102436471614 at T=20, but not every second-shell state is more detectable. States 20 and 02 increase the detected fraction relative to the first-shell mixture; state 11 decreases it.
2. The net gain is a small difference between a -0.157884480097 contribution in instantaneous output shells 0–3 and a +0.168128127258 contribution in shells 4–12. The initially occupied shell 2 itself contributes negatively to the contrast.
3. The bath-off second-minus-first advantage appears after initial suppression, crosses between native nodes 4.80800 and 4.80825, peaks near 9.0405, and then partially compensates. Its 10–20 contribution is negative, unlike the additional positive continuously acting first-shell susceptibility discussed previously.

The new runs complete the planned detector-only prediction test. They do not constitute a further positive-rate bath calculation, do not identify a unique coherent pathway, and should not be turned into a universal claim that more transverse energy improves detection.

## 1. Inputs, authority, and audit scope

Primary archive:
`Task07_Omega144_SecondShell_PC2_20260918_v1_OUTPUT.zip`

SHA-256:
`fb7e9dd97d1c39e1da4a59afb0889b1ecc3178f53d0820686f13bbbacae1fcd1`

The supplied sidecar agrees. All 109 ZIP members pass CRC; 108 export-manifest entries and 61 package-manifest entries verify. All 61 package-manifest members also match the original pre-submission package byte-for-byte. The 12 present new-case native-manifest entries and 10 present inherited native-manifest entries verify. These overlapping counts are declarations, not independent data sets.

All 12 NumPy containers, containing 197 fields, were loaded. Numeric arrays are finite. The three histories have 80,001 detector nodes, 80,000 midpoint-probability intervals, 401 diagnostic nodes, and 400 common output panels. Their stored tensor ordering is spin-major, complete-shell orbital order with descending nx, z-fast, with separate pure-state columns.

The original record stores 12 state snapshots and 120 progress JSON files on PC2 but omits them from this compact export. Their omission and hashes are explicit. Full wavefunction factors, missing phase information, and actual per-solve residual vectors were not reconstructed from scalar summaries. Saved true-residual arrays were checked for finiteness, bounds and identity, not recalculated by replaying the solver.

No live Slurm query or cluster change was made. Submission[ARCHIVE_PATH]er/completion records identify array 3175322, indices 0/1/2 and execution IDs 3175633/3176454/3175322. All three recorded H100 workers used gpu1008 and completed 80,000 steps. Numerical-loop durations were 16.5066, 8.6541 and 16.6948 minutes. These are recorded execution times, not new scheduler measurements.

Authoritative configuration: omega144; Ndyn12; Nz1500; Lz20; dt0.00025; T20; z0=10; Gaussian amplitude width0.5; k0=kappa=pi; physical-spin angles pi/6 and0; complex128. Actual hz=0.013333333656191826 and numerical roof=19.986665725708008 are retained. GMRES response-matched tolerance is 1e-12. The inherited insertion spacing0.05 is only an output cadence here: no environmental insertion family was propagated.

See `fresh/audit.json`, `fresh/array_inventory.csv`, `fresh/manifest_verification.csv`, and `fresh/execution_records.json`.

## 2. Native law reconstruction and fixed predictions

Each pure-state column is individually normalized at launch. Mixture weights are applied only during analysis: 1/2 for first-shell states10 and01; 1/3 for second-shell states20,11,02. This is different from PulsePair's already-weighted per-initial-state contributions, which must be summed rather than averaged again.

Detector probabilities are the saved nonnegative midpoint losses. They are not manufactured by differentiating sampled survival. For each mode,

D(T_n) = sum of p_k for k<n,

with the independent closure check S(T_n)+D(T_n)=S(0). Output-shell probabilities sum to p_k; diagnostic spin/orbital populations sum to S. No clipping, renormalization, compression, added absorber, or coherent mixing is used.

The exact projected launch identity below the cutoff is

B_up[rho_bar1] = 3(rho_bar2-rho_bar1).

Consequently the unweighted launch columns predict

S2(T)=S1(T)+q1(T,0)/3,

P2,k=P1,k+P_launch1,k/3.

The predicted file matches its frozen SHA-256, and its curves were independently reconstructed from the original first-shell survival/roof kernels and matched baselines. No insertion-time weight or ds factor belongs in this identity.

Results:

| Quantity | Value |
|---|---:|
| Direct uniform shell2 D(20) | 0.5175888680759747 |
| Frozen prediction D(20) | 0.5175888680758995 |
| Endpoint difference | 7.51621e-14 |
| Complete common-panel censored-law TV discrepancy | 5.75546e-14 |
| Maximum survival discrepancy | 1.49214e-13 |
| Maximum single common-panel discrepancy | 1.40773e-15 |

The individual identities for input10 and01 were also checked against the new20/11 and02/11 trajectories. Their maximum survival residuals are 5.82312e-13 and4.00679e-13; their complete signed-law discrepancies are approximately1.65e-13 and1.62e-13.

These agreements are stringent implementation checks. Because the identity is linear and the methods share the finite detector and GMRES, the agreement is not an independent measurement of continuum error or a new physical theorem.

The first-shell replays agree with the parent laws at native complete-law distances6.96355e-14 and7.58662e-14. The maximum reconstructed cumulative probability-closure residual is1.43818e-12. The largest saved true GMRES residual is9.26378e-15. Diagnostic partition residuals are below1.7e-15 at nodes and8e-18 for output panels. Maximum sampled top-shell population among the new second-shell states is6.29336e-8; this is a diagnostic, not a truncation-error bound.

See `fresh/audit.json`, `fresh/endpoint_metrics.csv`, and `fresh/sign_and_law_metrics.json`.

## 3. Actual detection probabilities and the energy-degeneracy distinction

| Preparation | D(20) | Restricted mean integral of S through20 |
|---|---:|---:|
| ground00, existing matched parent | 0.586280242327 | 12.126115659830 |
| first-shell mixture, new replays | 0.507345220915 | 13.369751389978 |
| pure20 | 0.529543090712 | 13.033623365559 |
| pure11 | 0.493680422803 | 13.558812826633 |
| pure02 | 0.529543090713 | 13.033623365562 |
| uniform second-shell mixture | 0.517588868076 | 13.208686519251 |

The precise ground restricted mean is in `fresh/endpoint_metrics.csv`; it is inherited from the matched parent, not a sixth new propagation.

The second-shell gain over the first shell is1.02436471614 percentage points of the initial ensemble, or2.01906842504% relative to the first-shell detected fraction. It is not a rate susceptibility. Ground detection remains larger than either shell average.

More importantly,

D20-D1 = +0.022197869798,
D11-D1 = -0.013664798112,
D02-D1 = +0.022197869798.

The uniform advantage is their average, not an improvement shared by every second-shell state. The 20/02 native complete-law distance is1.29368e-13, whereas the20/11 distance is0.0458391000337.

All three target states have Hperp=3*hbar*Omega and the same initial expectation of p_x^2+p_y^2, namely3*m*hbar*Omega. They differ in their transverse wavefunctions and higher moments. Therefore total occupation, transverse energy, and RMS transverse momentum are not sufficient statistics for the full spinor detector law. This does not prove that momentum is irrelevant or that coherence is the sole cause. Equal oscillator eigenenergy is not a theorem of equal detector response.

The axis-exchange symmetry relates20 and02; it does not equate either with11. The different results are compatible with an isotropic guide.

## 4. Observation horizon and the shell-resolved probability balance

The direct gap D2(T)-D1(T) has:
- minimum -0.0105534243749 at T=3.38000;
- resolved sign bracket[4.80800,4.80825];
- maximum+0.0176384036767 at T=9.04050;
- endpoint+0.0102436471614 at T=20.

The sign screening is the package rule max(5e-10,5*sum practical numerical-L1 indicators). It is not a certified continuum zero bracket. Positivity after the crossing is a statement about the native saved horizons.

Window contributions:

| Output window | D2-D1 |
|---|---:|
| 0–3.6 | -0.009998529263 |
| 3.6–10 | +0.026301997974 |
| 10–20 | -0.006059821550 |
| 0–20 | +0.010243647161 |

Thus the preparation advantage develops in an intermediate interval and later partially compensates. There is no active environment in any of these histories. The remaining S2(20)=0.482411131923 is substantial; no asymptotic efficiency conclusion follows.

Partitioning each midpoint roof probability by instantaneous output shell ell yields:

| Output-shell group | second preparation | first preparation | difference |
|---|---:|---:|---:|
| 0–3 | 0.217424598430 | 0.375309078527 | -0.157884480097 |
| 4–12 | 0.300164269646 | 0.132036142387 | +0.168128127258 |
| All | 0.517588868076 | 0.507345220915 | +0.010243647161 |

The largest positive individual contributions are shells5(+0.06449334),6(+0.04649526), and7(+0.02516336). The initially occupied shell2 contributes negatively(-0.03278198).

Therefore the advantage is not simply more clicks carried by an unchanged initial shell2 population. The detector-present dynamics generates different roof-shell content. With no bath and diagonal bulk oscillator Hamiltonian, off-diagonal channel coupling in this finite model comes from the Hermitian spin–momentum roof term. However, a roof-shell partition does not resolve a history of transitions, count repeated encounters, or identify a unique interference pathway. These components are not additional monitored detector channels.

The complete native censored-law TV distance between the two preparation mixtures is0.0377346573341; the common0.05-panel distance is0.0375716192345. Both exceed the endpoint gap because there is temporal redistribution and cancellation. The two panel resolutions are stated explicitly.

See `fresh/time_window_contributions.csv`, `fresh/output_shell_contributions.csv`, and Figures1–4.

## 5. Relation to the continuously active bath and completed pulse experiment

The direct static comparison gives the launch derivative

I1(0;20)=3(D2-D1)=+0.0307309414843.

Its independent old launch-kernel value is+0.0307309414843. This validates a component of the causal mechanism. It must not be replaced by the continuous-rate derivative,

chi_D,up^first(20)=integral_0^20 I1(s;20)ds=+0.310278277944.

The old continuous-rate coefficient was freshly re-integrated from the inherited kernels in this upload, not generated by the new library. A static launch difference and a rate derivative are operationally different.

For the earlier PulsePair, a small context-only re-reduction of its two native probability histories confirms the high-action endpoint changes+1.48893664058e-4 early and-1.08923373756e-5 late, with eta=1/256. The PulsePair archive and those history members were checked against their hashes, but its full earlier audit was not repeated. Its per-initial entries already contain1/2 weights and were summed. Equal-post-operation-duration and late-remainder-resolution qualifications from the previous review remain unchanged.

The evidential chain is therefore:
1. signed kernels predict response to a unit operation;
2. finite positive operations confirm scheduled sign control by a fixed deadline;
3. new detector-only initial states confirm the launch-shell relation and expose mode-resolved output content.

The new library does not establish that this static shell gap explains all continuously acting response. In particular, the static gap shrinks after10 even while the older continuous-bath first-shell susceptibility grows. The previously identified state-dependent anticommutator reweighting is not removed by this result.

See `mechanism_final/context_bridge.json`.

## 6. Additional analytical benchmarks, clearly separate from new trajectories

### Monochromatic local absorption

Using V9's frozen local expression A(k,R)=4*k*kappa/((k+kappa)^2+R^2), the exact radial momentum-density polynomials for the ideal oscillator can be integrated. Set x=R^2/omega. The normalized radial densities are exp(-x)W(x), with

W0=1; W1=x;
W2=(2x^2-2x+1)/3;
W20=W02=3x^2/4-x+1/2;
W11=x^2/2.

At omega144 and k=kappa=pi the local averages are approximately A1=0.177927 and A2=0.148633. This benchmark predicts initial local suppression, not the eventual static finite-guide advantage. It includes the input momentum distribution, rather than just an RMS substitution, but remains a monochromatic one-encounter approximation. It is not a full packet, roof-return calculation, or alternative validated detector law. Its failure to explain the later positive gap shows why the full propagation matters; it does not uniquely prove that bottom-wall returns are responsible.

See `mechanism_final/local_absorption_benchmark.csv` and `ANALYTICAL_NOTE.md`.

### Optional coherent radial/quadrupole inference

Under the exact finite-model parity/spin and joint rotation symmetries, the complete integrated law of Q=(20-02)/sqrt(2) equals that of11. Since radial R=(20+02)/sqrt(2) and Q span the20/02 subspace,

nu_R=nu_20+nu_02-nu_11.

This gives D_R(20)=0.565405758622. The corresponding Q value is0.493680422803. These are new derived predictions, not independently propagated coherent-state results and not information obtained from populations alone. The derivation uses detector symmetries, not a generic identification of all degenerate states. The full proof and finite-operator checks are in `ANALYTICAL_NOTE.md`.

These predictions suggest a possible future radial/angular test but no new job is proposed or submitted here.

## 7. Reliability and limitations

The independent reduction ran twice with11 byte-identical outputs. The inspected bundled offline analysis was also executed with bytecode writing disabled and a new output directory; its6 products match the recorded aggregate byte-for-byte. Ten small new bookkeeping tests passed. Finite channel algebra/rotation tests were performed at N2 andN12; no wavefunction was propagated. All four PDF figures were rendered for visual inspection.

Shared finite detector, source and GMRES identities mean that prediction agreement is an implementation/linearity test, not an independent detector model. All numerical decimals identify the saved outputs, not claimed continuum accuracy. The practical accumulated state-L1 indicators reach approximately1.04e-8 and are not formal all-source error bounds. Neither small top-shell population nor small roof mass at the cutoff certifies truncation convergence. Existing configuration-matched controls retain their own scopes and should not be rerun merely because this package completed.

The results support a finite-window and detector-specific explanation involving state structure, channel conversion, and temporally compensating detector output. They do not establish a universal benefit of increasing energy, an eventual-detection advantage, a unique interference history, a physical realization of the ABC, or an exact finite-duration bath pulse.

## 8. Completion assessment

Both planned priorities have now delivered their intended evidence. The second-shell result is worth including because it replaces an inferred probability law by an independently propagated one and gives a finer mechanistic conclusion: within one energy-degenerate shell the detector distinguishes the prepared state, and the net average advantage is supported by higher-shell roof output despite deficits in lower output shells.

This deepens the sign discussion without proving a unique microscopic explanation. No repeat of this five-trajectory library or another broad susceptibility sweep is indicated by the present checks. The next immediate task is to integrate the finite pulse validation, static mode library, and causal response analysis into one claim-matched scientific narrative, preserving their distinct protocols.

## Reproduction

From a CPU environment with NumPy, SciPy and Matplotlib (no installation or upgrade is automatically performed):

```
python scripts/reconstruct.py --archive /path/to/Task07_Omega144_SecondShell_PC2_20260918_v1_OUTPUT.zip --release /path/to/Task07_Omega144_SecondShell_PC2_20260918_v1.zip --output /new/output/fresh
```

The release argument is optional; omitting it skips the cross-release byte comparison and reports zero comparisons. The output directory must not exist. `scripts/mechanism_checks.py` expects the review layout documented in `README_REPRODUCE.md`; the source archive remains read-only.

Figures can be regenerated from the packaged compact `fresh/reconstructed.npz`; the original archive is not required just to redraw them. Full native manifest and partition reconstruction requires the original archive. No absent state snapshots are required.
