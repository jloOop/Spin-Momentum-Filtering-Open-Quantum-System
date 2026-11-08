# Independent omega144 T20 mechanism review

**Scope:** saved-array CPU postprocessing and small finite-operator algebra only. **scientific_acceptance=false.** No SSH, scheduler action, propagation, solver execution, environment upgrade, clipping, renormalization or changes to originals.

## What the data establish

For this finite numerical model, the same upward trace-preserving transverse channel suppresses ground-preparation detection through T=20, but the incoherent first shell changes from suppression to enhancement between T=5.30 and 5.35 and stays positive at every later saved horizon. The preparation determines the sign of the *signed propagated insertion*, not whether upward source activity is positive. Both recycling and anticommutator terms are essential.

The T=20 first-shell source response is broadly positive for insertions from s=0 through 16.20 and negative from s=16.25 through 19.95. Its positive source integral is +0.316125236723 and negative source integral is -0.005846958801; their sum is +0.310278277922 from the roof reduction. Thus the source-time net is not a small remainder of nearly balanced positive/negative source windows at T=20, although the recycling and anticommutator components separately exhibit substantial cancellation.

Of the first-shell increase from T=10 to 20, **64.2713% is the delayed consequence of action at s<=10**, and 35.7287% comes from action after 10. Earlier action dominates but later action is material. The single-launch shell identity explains one exact column of the response kernel and supports nonmonotonic shell detectability; it does not determine the full continuously active susceptibility.

The main falsifiable prediction is an opposite-sign response for the **same first-shell preparation**: a weak operation at s=2.95 has terminal derivative +0.038596591017, whereas one at s=17.45 has -0.002813534761. These are data-derived predictions for future independent tests, not interventions performed here.

## 1. Identity, numerical authority, and verification

Primary archive: `[ARCHIVE_PATH]`.
SHA-256: `11e4dfbe72cb866c5bcd95ab222f5f9ae1047b0f2d71884424c013b459f63f4f`; agrees with the sidecar and requested identity. All 196 members pass CRC, all 195 export-manifest declarations match, and all 96 entries in the six native response/reference output manifests match. The 7-entry archived analysis manifest also matches.

T10 parent: `[ARCHIVE_PATH]`; SHA-256 `e6a64d22e9c9d81516e296484aac47b0d9686fbffdfd1c3dd42bf10da1e3d33b` agrees with its sidecar and the T20 contract. All 132 parent export entries and 84 native-manifest entries match. No duplicate copies are counted as independent runs.

The T20 result ZIP contains only 15 of the 102 launch-manifest files. This export omission is explicitly recorded. A separate bounded read-only check of the matching local launch ZIP verifies all 102 entries, with a manifest byte-identical to the executed submission pin. Fifty-one parent declarations also independently match the refined T10 evidence. The complete inventory is in [manifest_verification.csv](manifest_verification.csv); nothing was relabeled or silently filled into an original archive.

| Slurm array element | Mode / native case | Recorded native completion | Wrapper meaning |
|---|---|---|---|
| 2970583_0 | 00 / 4775 | completed_pending, exit 3 | saved T20 horizon verified, nonaccepting |
| 2970583_1 | 10 / 4776 | completed_pending, exit 3 | saved T20 horizon verified, nonaccepting |
| 2970583_2 | 01 / 4777 | completed_pending, exit 3 | saved T20 horizon verified, nonaccepting |

Submission and worker-start records establish this mapping. All native local checks passed; the pending state records the absence of an applicable same-prefix production rerun. This is not a performed rerun failure. No final Slurm accounting was inferred from these records. Scheduler status, native exit, saved-array review and scientific acceptance remain distinct. The inherited `NOT_REQUIRED_FOR_OMEGA1_CONFINEMENT_CONTROL` labels are exemptions, not omega144 refinement evidence.

Verified family: omega=144, complete shells N=12 (91 orbital labels, 182 spin-resolved channels), Nz=1500, Lz=20, dt=0.00025, ds=0.05, T=20; z0=10, Gaussian amplitude width=0.5, k0=kappa=pi, theta=pi/6, phi=0, complex128 state/matrix arithmetic and float64 reductions. There are 80,000 detector intervals / 80,001 detector nodes and 400 response panels / 401 source-response nodes.

The literal endpoint-excluded float32 construction is preserved: h_z=0.013333333656191826 and numerical roof z=19.986665725708008. The physical inner product is h_z times the Euclidean sum. Working storage is spin-major with state index (spin*91+orbital)*Nz+z; complete shells order nx descending, while Audit-02 orders nx ascending and spin-fast. The explicit 182-channel permutation is independently checked in the finite algebra self-tests. No alternative roof, grid or ordering was substituted.

The matched bath-off reference and response branches use GMRES rtol=1e-12. Task05 regression metadata records its separate 1e-8 role; those trajectories and their large selected-state snapshots are not substituted for the matched reference. The detector roof is the sole monitored loss. The bath is unobserved and trace preserving. Oscillator labels, physical spin, evolving oscillator populations and four numerical low-rank branch columns are different objects.

Exact source identities and unchanged T20/T10 function/class ASTs are recorded in [input_verification.json](input_verification.json). Sources were inspected as text, never imported. Writer excerpts, line numbers and source hash are in [SOURCE_SEMANTICS.md](SOURCE_SEMANTICS.md). The V9 manuscript was not found in the allowed bounded search, so no claim here is attributed to its named sections. The smallest missing theory source is that PDF itself.

## 2. Independent reconstruction and full-law checks

Let q[i,j] be `kernel_survival`: output node i by insertion node j. Let P[k,j] be `kernel_total_probability`: output panel k by insertion node j. Both are unweighted in source time. The writer accumulates the roof midpoint probability including detector dt into P; `kernel_anticommutator_probability` already carries its minus sign. Neither dt nor ds is multiplied into these entries a second time.

For each output horizon, chi_S is an elementary-trapezoid sum over its causal source prefix. For output panel k, the source rule extends through node k+1, whose roof kernel is zero. The primary chi_D is -chi_S; the separate roof response is the prefix sum of reconstructed panel probabilities. I(s_j;T_i)=sum_(k<i)P[k,j] is formed before source quadrature and independently checked against -q[i,j]. No survival derivative is used to manufacture clicks.

| Mode | max absolute q+I | max source trace | max tangent closure | max saved chi_S reconstruction | baseline probability closure |
|---|---:|---:|---:|---:|---:|
| 00 | 7.667e-12 | 1.843e-14 | 2.596e-11 | 4.441e-16 | 3.598e-12 |
| 01 | 4.457e-12 | 2.875e-14 | 2.005e-11 | 1.665e-16 | 5.277e-13 |
| 10 | 4.065e-12 | 3.209e-14 | 2.435e-11 | 1.665e-16 | 6.337e-13 |

All causal forbidden entries are exactly zero. Source jump/anticommutator trace identities and activity normalization checks pass; the largest projected activity-formula residual is 3.11e-15. All loaded numeric fields are finite. Matched bath-off midpoint probabilities are nonnegative, and S0+cumulative roof equals S0(0) within the residuals above. The tiny source-trace residue is also retained explicitly when auditing q+I-source_trace; no trace correction is imposed.

Declared archived tolerances: array reconstruction 2e-13, causal 1e-14, integrated metrics 2e-12, kernel closure 5e-8, source trace 5e-11 and tangent closure 5e-10. The observed discrepancies pass their applicable gates. These are identity/closure checks, not uncertainty estimates. Global continuum, longitudinal-grid, shell, dt, ds, and finite-rate errors remain unknown.

**The full 0–10 prefixes are exactly equal (max difference 0)** for all three modes: saved survival/density, independently reconstructed survival/cumulative roof, source survival, and survival/total/jump/anticommutator kernels. Genuine ds=0.05 parent arrays from array2892221 were used. Internal coarse arrays are retained as source evidence but are not treated as an independently propagated refinement.

The new numbers are reconstructed in `analyze_mechanism.py`. Recorded state audits remain under `inputs/T20/state/`; recorded integrated metrics remain with the native cases. Fresh endpoint discrepancies against those records are <=4.45e-16. Existing audits are evidence to compare with, not inputs used to fit the reconstructed curves.

## 3. Cumulative signs, fixed preparations and censored laws

Pre-arrival screening uses epsilon_D=2.595613e-10 for cumulative signs/root denominators and epsilon_I=7.667089e-11 for source profiles. Each is max(1e-12,10 times the largest relevant measured closure residue). This declared screen separates numerical-floor features only; it is not a continuum error bound. Raw values and raw sign brackets are preserved in the tables, without clipping.

Ground and p=0.60 are negative at every screened node from T=0.85 to 20. Modes10/01 and their mean are negative through T=5.30 and positive from 5.35 through 20. The p=0.95 mixture crosses in [5.65,5.70] and stays positive thereafter. For the first-shell mean, the additional raw [0.25,0.30] sign change is only +6.51e-15 to -4.45e-15 and is not corroborated by a roof sign crossing. The initial exact zero is not a reversal.

The fixed old p is not sign-persistent: its meaningful brackets are [7.15,7.20], [7.20,7.25], [8.00,8.05], [10.10,10.15], [17.35,17.40], [19.30,19.35], [19.50,19.55]. It is positive at the final nodes 19.55–20. The isolated T=7.20 positive node is resolved relative to the numerical-floor rule but does not establish a broad positive interval. Every raw/screened bracket, including individual modes, is in `tables/sign_changes.csv`; intervals are only statements about saved nodes.

| Preparation | chi_D(20), survival | chi_mu*(20) | A_TV(20), with censoring | own bath-off D(20), roof |
|---|---:|---:|---:|---:|
| Ground / p=0 | -1.279406755467 | +12.309958762408 | 1.602050838746 | 0.586280242327 |
| mode10 | +0.310278277946 | -2.010736020815 | 0.667715406001 | 0.507345220914 |
| mode01 | +0.310278277942 | -2.010736020794 | 0.667715405999 | 0.507345220915 |
| First-shell / p=1 | +0.310278277944 | -2.010736020805 | 0.667715406000 | 0.507345220914 |
| p=0.60 | -0.325595735420 | +3.717541892480 | 0.734178054551 | 0.538919229480 |
| p_old=0.8104003212089722 | +0.008874506230 | +0.704463110157 | 0.510065984764 | 0.522311275620 |
| p=0.95 | +0.230794026274 | -1.294701281644 | 0.620022210704 | 0.511291971985 |

| Preparation | Native minimum (T) | Native maximum (T) |
|---|---:|---:|
| Ground / p=0 | -1.27940675547 (20.00) | +1.09523501379e-14 (0.35) |
| mode10 | -0.0771184037852 (4.10) | +0.318310635444 (19.85) |
| mode01 | -0.0771184037861 (4.10) | +0.318310635439 (19.85) |
| First-shell / p=1 | -0.0771184037856 (4.10) | +0.318310635441 (19.85) |
| p=0.60 | -0.351753882796 (16.50) | +2.14883666416e-15 (0.20) |
| p_old=0.8104003212089722 | -0.146737693822 (4.25) | +0.0437698332316 (19.00) |
| p=0.95 | -0.0951985617392 (4.15) | +0.2422552171 (19.00) |

The tiny positive maxima of ground and p=0.60 are pre-arrival numerical-floor values. The mode10–mode01 cumulative discrepancy is at most 5.5683e-12; the endpoint difference is +4.3009e-12. Additional kernel, activity and baseline symmetry residuals are in `audit.json`.

chi_mu*(T) is the trapezoidal integral of the saved chi_S nodes: the derivative of the restricted/censored mean E[min(tau_D,T)], not the conditional mean among detections. A_TV(T)=0.5*(sum|chi_P|+|chi_S(T)|) retains the no-click atom. Linear component laws and each preparation’s own baseline are mixed before absolute values or ratios. At fixed native resolution A_TV is nondecreasing within numerical closure: its worst observed single-step decrease is 1.313e-13, below the 5e-10 closure allowance.

The first-shell response averaged over the final detector panel [19.95,20] is **-0.104101405467**, despite positive cumulative chi_D(20). This panel average is not a pointwise instantaneous response. Neither sign implies eventual behavior beyond20.

| T | Ground chi_D | First-shell chi_D | p_star, survival | p_star, roof |
|---:|---:|---:|---:|---:|
| 3.6 | -0.378966910119 | -0.071473227787 | masked | masked |
| 6 | -0.468130522620 | +0.044206397652 | 0.913716158444 | 0.913716158449 |
| 8 | -0.423778655816 | +0.095375843545 | 0.816286204468 | 0.816286204473 |
| 9 | -0.460290702181 | +0.138041845663 | 0.769289091558 | 0.769289091563 |
| 10 | -0.522192227754 | +0.122173304498 | 0.810397517584 | 0.810397517590 |
| 12 | -0.699202064582 | +0.100796451315 | 0.874004202118 | 0.874004202126 |
| 15 | -0.899198213228 | +0.196623642354 | 0.820569701770 | 0.820569701778 |
| 20 | -1.279406755467 | +0.310278277944 | 0.804817764889 | 0.804817764897 |

Root formula: -chi_D,00/(chi_D,first-chi_D,00), evaluated independently from survival and roof. Denominators below epsilon_D and roots outside[0,1] are masked, with reasons saved. Resolved roots exist on native nodes 5.35–20; at T=0 every mixture has zero response and no unique ratio exists. The preparation axis is an exact affine interpolation of component arrays, not a new propagation or phase transition. The old p remains fixed at every horizon.

## 4. Source time versus detector output time

I is unweighted in insertion time. Positive/negative integrals below partition its native trapezoidal node contributions by sign, without shifting roots or altering any sample. Source-interval tables give native spans; nodal quadrature measures separately include half-weight boundaries. At fixed edges 0, 3.6, 10, 20 each window uses its own one-sided trapezoid endpoints. Adjacent half-weights add exactly; Boolean masks are not used to allocate boundary nodes.

| First-shell horizon | Positive source integral | Negative source integral | Net roof response | cancellation ratio |
|---:|---:|---:|---:|---:|
| 6 | +0.062230447421 | -0.018024049772 | +0.044206397648 | 1.815450 |
| 10 | +0.143574456028 | -0.021401151537 | +0.122173304491 | 1.350341 |
| 12 | +0.126620503882 | -0.025824052577 | +0.100796451305 | 1.512400 |
| 15 | +0.203744492116 | -0.007120849776 | +0.196623642340 | 1.072431 |
| 20 | +0.316125236723 | -0.005846958801 | +0.310278277922 | 1.037688 |

The cancellation ratio is (positive magnitude+negative magnitude)/|net|. It is 1 for a one-sign source response. At T=20 it is 1.03769 for the first shell and 1.07174 for p=0.95: broad enhancement with a smaller late suppression lobe. At T=6 it is 1.81545, showing stronger source-window cancellation. Ground I(s;20) is negative at every source node 0–19.95 and zero at20.

The SAME insertion can reverse as the observation horizon grows. For the first shell: s=0 crosses in T=[4.80,4.85]; s=2.95 in [5.95,6.00]; s=6 in [13.90,13.95]; s=10 in [14.00,14.05]. These independent roof-prefix sums show delayed consequences of fixed earlier action, not a change of preparation or pulse time. All screened early-source crossing brackets are saved in `tables/same_insertion_horizon_crossings.csv`.

The fixed source/output 3x3 block table, signed jump/anticommutator parts, and complete source-block histories are in `tables/source_output_blocks.csv` and `tables/source_block_histories.csv`. Noncausal blocks vanish exactly. Source-block sums agree with cumulative roof within 8.9e-16; integration of I agrees with survival within the existing tangent-closure residue.

The exact saved-grid split is chi_D^roof(20)-chi_D^roof(10) = integral_0^10[I(s;20)-I(s;10)]ds + integral_10^20 I(s;20)ds. Survival-based changes are retained alongside this roof identity:

| Preparation | Delta chi_D, survival | delayed action <=10 | newly applied action >10 | delayed fraction of roof change |
|---|---:|---:|---:|---:|
| Ground / p=0 | -0.757214527714 | -0.453730833144 | -0.303483694555 | 59.9210% |
| First-shell / p=1 | +0.188104973446 | +0.120897423604 | +0.067207549827 | 64.2713% |
| p=0.60 | -0.190022827018 | -0.108953879095 | -0.081068947926 | 57.3373% |
| p_old=0.8104003212089722 | +0.008872699671 | +0.011948090701 | -0.003075391039 | 134.6613% |
| p=0.95 | +0.140838998388 | +0.092166010767 | +0.048672987608 | 65.4407% |

The split-to-survival discrepancies are <=1.71e-11 and are not silently forced to zero. For p_old, earlier action contributes +0.011948090701 but newly applied late action contributes -0.003075391039; the >100% fraction therefore denotes cancellation, not a probability.

Integrated recycling/anticommutator roof terms at 20 are +6.427342720410 / -7.706749475851 for ground and +10.724163585698 / -10.413885307776 for the first shell. Their differences give the net signs. Neither term alone is a trace-preserving physical intervention; source-time breadth of the total must not be confused with absence of recycling/anticommutator cancellation.

The independently checked projected identity is Q_up=sum a_j a_j^dagger=N_perp+2I-14Pi_12. Saved `activity_total` is a(s)=Tr[Q_up rho_tilde0(s)], not normalized by survival. It equals sum `jump_norm2` and S0*`reference_s_up` to 3.11e-15. The latter is a conditional activity; `reference_s_down` and top-shell fraction are also conditional. At launch activity is 2 for ground and 3 for the first shell. Figure8 separates a, a/S0, I, and I/a; the ratios are diagnostics, not probabilities. Since positive activity coexists with opposite signs of I, activity magnitude alone does not determine enhancement.

## 5. Launch-shell detectability: exact identity and limited inference

The separate finite-operator self-test verifies B_up[rho_bar_n]=(n+2)(rho_bar_(n+1)-rho_bar_n) for every n=0,...,11, below the cutoff, with maximum residual 4.441e-16. It also verifies Q_up and the Audit-02 permutation. These are algebra tests, not physical evolutions.

The resulting launch relation I_0(0;T)=2[D_1^0(T)-D_0^0(T)] is checked against the actual response-matched independent bath-off ground and two-mode first-shell histories throughout 0–20: maximum roof residual 1.081e-13, survival residual 2.965e-13, and panel-law residual 7.22e-16. This validates the single-launch-operation interpretation without using printed endpoints.

D_2^0,inferred(T)=D_1^0(T)+I_1(0;T)/3 is reconstructed in two ways, from roof and survival. Its inferred panel probabilities are baselineP_first+P_first[:,0]/3, not derivatives of sampled survival. This predicts only the UNIFORM shell2 mixture (20+11+02)/3; it asserts neither equality of individual shell2 states nor an independent shell2 simulation.

| T=20 bath-off cumulative roof probability | Value |
|---|---:|
| Ground shell0, independently propagated | 0.586280242327 |
| Incoherent shell1, independently propagated components | 0.507345220914 |
| Uniform shell2, **INFERRED_FROM_LAUNCH_KERNEL** | 0.517588868076 |

The inferred shell2 roof law is nondecreasing and lies in[0,0.517589]; every inferred native panel is positive (minimum 2.23e-102). The survival form has a maximum 1.0000000000000318 and a maximum positive step 1.09e-14, both numerical residuals retained rather than clipped. Roof/survival inferred laws differ by at most 1.05e-12.

With the declared numerical-floor screen, D_1^0<D_0^0 at nodes 0.85–20. The inferred D_2^0 is below D_1^0 at 0.85–4.80 and above it at 4.85–20. Its launch crossing precedes the continuously active first-shell crossing [5.30,5.35]. The hierarchy therefore supplies a concrete part of the mechanism: upward redistribution at launch goes toward a less detectable shell for ground, but toward a more detectable averaged next shell for the late first-shell launch law. It does not explain later-source columns by itself; evolving coherences and correlations prevent applying the shell-mixture identity to arbitrary later states.

The bounded search covers local filenames and direct members/small configuration JSONs of 11 archives under Communication_Physics_Extension. No matching independently completed mode20/11/02 bath-off or pulse campaign was identified. Nested ZIPs were not indiscriminately unpacked. The result is an availability finding in this scope, not a whole-project or live-cluster assertion. To independently validate shell2, the minimal missing evidence is matched T20 mode20/11/02 baseline survival and midpoint probability arrays plus configurations/status/hash manifests.

## 6. Frozen predictions for future independent tests

**DATA-DERIVED PREDICTIONS FOR FUTURE INDEPENDENT TESTS.** A single weak transverse operation with derivative B_up at source time s predicts dD(20)/deta=I(s;20). The table gives both signs for the same preparation and checks two native neighbors on each side. No finite eta range is certified.

| Preparation | sign | s | terminal derivative, roof | neighbor range over s +/-0.10 | normalized narrow-window derivative |
|---|---|---:|---:|---|---:|
| First-shell / p=1 | positive | 2.95 | +0.038596591017 | [+0.037848917568, +0.038596591017] | +0.038390347365 |
| First-shell / p=1 | negative | 17.45 | -0.002813534761 | [-0.002813534761, -0.002788601621] | -0.002803706374 |
| p=0.95 | positive | 2.95 | +0.030594702367 | [+0.029984973085, +0.030594702367] | +0.030393793194 |
| p=0.95 | negative | 16.65 | -0.003684317290 | [-0.003684317290, -0.003538004593] | -0.003640017515 |

No isolated unresolved spike is selected. All candidate complete signed panel laws and survival histories are saved in `pulse_gate_laws.npz`, indexed by preparation and source time; the final survival entry is the no-click atom. Individual-mode and other-mixture candidates, where a robust sign exists, are in `tables/pulse_candidates.csv`. Ground has no robust positive T20 source time.

For lambda(t)=eta f(t), each rectangular f=1/(b-a) on[a,b] has unit integrated rate action. The following signed terminal derivatives use split-window source quadrature and preserve the terminal survival atom:

| Gate window | Ground | First shell | p=0.95 |
|---|---:|---:|---:|
| [0, 3.6] | -0.145238820316 | +0.032399288018 | +0.023517382601 |
| [3.6, 10] | -0.070791141836 | +0.019755201755 | +0.015227884575 |
| [10, 20] | -0.030348369455 | +0.006720754983 | +0.004867298761 |
| [3.6, 20] | -0.046130914775 | +0.011807368357 | +0.008910454201 |
| [0, 20] | -0.063970337772 | +0.015513913896 | +0.011539701313 |

The broad [10,20] first-shell gate is positive even though sufficiently late narrow pulses are negative; gate averaging and single-pulse timing are distinct. Equal integrated rate action is not equal expected environmental event number or equal energy input. Activity-per-unit-action is tabulated separately. No T10 timing optimum or sign was transferred without evaluating the T20 kernel.

Kernel reweighting is not independent intervention evidence. A single CPTP operation with the right zero-action derivative is not automatically an exact finite-duration Lindblad pulse. No remainder/error bounds or finite-rate percentage gains are claimed.

### At most two next experiments; not prepared or submitted

1. **Detector-only uniform shell2 validation.** Hypothesis: the independent average of 20,11,02 has the inferred complete bath-off law. Hold the same longitudinal packet, physical spin, projected ordering, roof, N/Nz/dt/T and matched rtol=1e-12; vary only the oscillator number-state preparation. The falsifiable target is the full native panel/survival history in `pulse_gate_laws.npz`, including D2(20)=0.517588868076 and the D2-D1 crossing in[4.80,4.85]. Save each component’s midpoint roof probabilities, survival, solve residuals, configuration/source/output hashes and completion record; average only afterwards. Qualitative cost: three zero-bath wavefunction references, far less work than the 401-source response campaign; no full density matrix is needed.

2. **Independent bounded-rank single-operation test, first shell.** Hypothesis: operation timing alone switches the terminal derivative. Hold the same preparation and detector family, and compare separately implemented weak CPTP transverse operations at s=2.95 and17.45, with matched no-operation baselines. The action-derivative targets are +0.038596591017 and -0.002813534761; compare the complete predicted signed panel law and survival atom, not only the endpoints. Save the pre-operation state or adequate low-rank factors with ordering/normalization metadata, operation definition and action, post-operation trace, panel probabilities, survival, numerical residuals and provenance. A shrinking-action derivative check is needed to separate numerical and finite-action error; no action interval is endorsed here. Qualitative cost: a few pulse times and rank-limited branches instead of all 401 insertion columns, though the CPTP construction/rank and derivative estimation have to be specified independently. The p=0.95 predictions provide an optional mixture cross-check using the same component results.

## 7. What remains underdetermined

The kernels establish causal timing and preparation sensitivity, not a unique microscopic pathway. Scalar activity/top-shell/source summaries do not identify coherences, purity, spin-orbital correlations, phase-resolved interference, or shell-resolved click output. The delayed sign flips are compatible with several return/interference mechanisms; they do not isolate a lower-wall return. The saved large Task05 selected states belong to the separate regression-reference role and were not substituted as matched states or unpacked to imply that missing diagnostics exist.

Upward susceptibility is a derivative at zero bath rate, not a detection probability or a finite-rate percentage. A coefficient below -1 is not a probability-bound violation. First-shell enhancement is relative to its own baseline and does not make its absolute bath-off detection efficiency exceed ground. No eventual improvement after 20, finite-rate performance, continuum convergence, or journal acceptance follows.

The scalar null retains its factorization assumptions: a factorized longitudinal/transverse detector law with an unobserved trace-preserving transverse bath and preserved factorization leaves the longitudinal detection law unchanged. This conditional statement cannot be transferred to the spinor coupled-boundary problem. Omega100 Task09 results are separate evidence and are not used here.

## 8. Deliverables, reproducibility and provenance

Figures 1–8 have both native-grid PNG and vector PDF versions: cumulative response; preparation–horizon map/fixed-p curves; source profiles; signed causal roof-kernel maps; source-block histories; launch-shell detectability; frozen intervention predictions; activity/effectiveness. Heatmap colors use a symmetric-log scale without altering or discarding kernel values. The preparation map samples p affinely while retaining all 401 native T nodes; the zero curve is the independently computed masked p_star rather than a fitted time contour.

All continuous-source curves are at ds=.05. Native full 80001-node matched baselines and all saved component/parent kernels are retained in compact inputs. No full-system density matrix was constructed and no essential kernel axis was downsampled. Float64 CSVs use round-trip representations. Compact NPZ laws include censoring. [DATA_DICTIONARY.md](DATA_DICTIONARY.md) describes axes, units, reductions and table fields.

Input member paths and hashes are in `inputs/lineage.json`; array keys/shapes/dtypes/axes/units are in `input_array_inventory.csv`; source code meanings are in `SOURCE_SEMANTICS.md`; fresh checks are in `audit.json`; synthetic/operator tests are separately in `self_tests.json`. The original recorded audits remain explicitly under `inputs/T20`. Reproduction commands are in [EXECUTION.md](EXECUTION.md). Archive verification/capture is separate from `analyze_mechanism.py`, which can reproduce the reductions from the compact inputs without the original ~1GB ZIP.

The compact review excludes original archives, duplicate large raw states, unrelated logs, caches and environment files. Its SHA-256 sidecar and manifest are generated after all final checks. No production jobs were prepared or submitted.
