# Independent PulsePair result review and scientific synthesis

**18 September 2026 — array 3152582; first-shell preparation, omega=144, T=20.**

## Main result

The same specified unobserved transverse excitation operation, with the same positive action and initial incoherent first-shell preparation, produces an **increase** in detection by T=20 when applied at s=2.95 and a **decrease** when applied at s=17.45. Both signs occur at eta=1/256 and eta=1/512. The finite-action probability laws closely reproduce the kernel predictions frozen before these runs.

This is new forward-propagation evidence, not a replotting or reweighting of the old kernel. It validates timing control of the sign at a fixed detection deadline, within the declared finite numerical model. It is not a full finite-duration Lindblad-pulse experiment or a continuously active bath calculation.

Two qualifications are essential. The early quadratic remainder is resolved under the predeclared test; the late half-action remainder is not. Also, at the same post-operation duration u=2.55, both runs have negative cumulative changes. Thus the fixed-deadline result does not independently isolate the pre-operation state from the remaining detection duration.

## 1. Evidence and verification

Input: `Task07_Omega144_PulsePair_PC2_20260917_v1_OUTPUT.zip`, 31,609,835 bytes.
SHA-256: `843efa3b908c7bd806aa6c63b2c899f1f372162f54cb2866fdcfb1e9e638ebd7`.
The uploaded sidecar and previously printed result checksum agree.

Fresh checks:

- All 93 ZIP members passed CRC; safe paths and no duplicate member names.
- All 92 export-manifest entries verified.
- All 51 package-manifest declarations verified. All 52 package files (including that manifest) match their original pre-submission release counterparts byte-for-byte.
- Ten present native-parent manifest entries and twenty present new-run manifest entries verified. The prior native manifests also list eighteen parent products not carried here; no absent product is claimed reverified.
- Eleven NumPy containers with 138 fields loaded with `allow_pickle=False`; all numerical arrays finite. This includes original histories, parent kernels/baselines, frozen predictions, and exported analysis arrays; it is not eleven independently executed trajectories.
- Frozen pulse-probability and survival columns are exact subsets of the native mode10/mode01 kernels. Those kernels and sources match the earlier T20 mechanism upload (eight cross-upload identities). The earlier independent frozen-target JSON is byte-identical.
- Both actual CONFIGURATION files match the declared physics, mixture, pulse times, actions, and backend. Both completion records point to the present output-manifest hashes.
- Separate analysis reconstructed all midpoint probability laws without importing any supplied simulation module or invoking GPU/CPU propagation.
- The independent reduction ran twice: twelve output files were byte-identical in this runtime. Existing-output refusal was tested. Thirty-two additional configuration, omission, and small finite-operator algebra checks passed. These are not new physical propagations.

The archive intentionally omits six factor snapshots (pre-operation, post-operation, final for each case) and eighty progress snapshots. All 86 omissions match EXPORT_SCOPE and the native manifest declarations. No full-state factor hash, off-diagonal reduced density, or per-step residual vector was reconstructed when its data were absent. The reported local z/spin marginal residual is a recorded audit; the pulse population transformation was independently reconstructed from saved shell populations.

Files: `fresh/audit.json`, `fresh/array_inventory.csv`, `additional_checks.json`, `reproducibility.json`, and `history_bridge/audit.json`.

## 2. Actual computation

Initial transverse state is `(rho10+rho01)/2`, with fixed physical spin theta=pi/6, phi=0 and the original longitudinal packet. This is p=1 in the earlier ground/first-shell mixture family, not a coherent superposition and not p=0.95.

Fixed settings: omega=144, N=12 (91 oscillator modes / 182 spin-resolved channels), Nz=1500, Lz=20, dt=0.00025, T=20, z0=10, Gaussian amplitude width=0.5, k0=kappa=pi, complex128. The actual inherited grid spacing is 0.013333333656191826. The actual roof is 19.986665725708008. Fresh factor propagation uses the matched 1e-12 Krylov accuracy.

Each case has 80,001 state nodes and 80,000 midpoint probabilities, with a new zero arm and two positive-action arms. Before the operation, the common two-column state is used; afterward the zero arm has two columns and each positive arm has six, totaling fourteen. No compression, post-launch renormalization, CAP, additional detector loss, or replacement GMRES was applied.

The operation is

\[
R_\eta=(I+\eta Q)^{-1/2},\quad K_0=R_\eta,\quad K_j=\sqrt\eta L_jR_\eta,
\quad Q=\sum_jL_j^\dagger L_j,\quad L_j=a_j^{(N)\dagger}.
\]

All Kraus alternatives are retained. The exact projected Q is `N_perp+2I-(N+2)Pi_N`, with maximum eigenvalue 13, not 14. The map is CPTP and its zero-action derivative is B_up; it need not equal exp(eta B_up). It is applied after the detector step reaching s and before the next detector step. The operation itself contributes no click.

Recorded identities: early is array3152582_0 / execution3152584 on gpu1018; late is array3152582_1 / execution3152582 on gpu1022. Saved numerical loop elapsed times are 5,781.27 seconds (96.35 minutes) and 1,684.10 seconds (28.07 minutes). Both reach step80,000. Final Slurm accounting is not included and is not asserted independently. The H100 reduced-oracle PASS records are inspected evidence, not rerun here.

## 3. Endpoint results: predicted versus independently propagated

The matched zero detection probability is `D0(20)=0.507345220914531` to displayed precision. Endpoint differences below are sums of native midpoint-probability differences. Subtraction of separately accumulated cumulative probabilities differs by at most about 7.6e-15. This summation-order effect is preserved and not silently fitted to the printed results.

| Time s | Action eta | Frozen linear prediction | Actual Delta D(20) | Relative change of D0 |
|---:|---:|---:|---:|---:|
| 2.95 | 1/256 | +1.50767933661e-4 | **+1.48893664058e-4** | +0.0293476% |
| 2.95 | 1/512 | +7.53839668305e-5 | **+7.49124930516e-5** | +0.0147656% |
| 17.45 | 1/256 | -1.09903701619e-5 | **-1.08923373756e-5** | -0.00214693% |
| 17.45 | 1/512 | -5.49518508093e-6 | **-5.47056447155e-6** | -0.00107827% |

The unit-action predictions were +0.0385965910172 and -0.00281353476144. The actual Delta D/eta values approach them on halving eta. Endpoint deviations from the linear prediction are 1.243% and 0.625% early, and 0.892% and 0.448% late. These should not be confused with the relative detector-probability changes in the last column.

Source: `fresh/endpoint_comparison.csv`.

## 4. Full censored-law comparison and the unresolved late remainder

The independent reduction sums the 200 native detector intervals in each 0.05 parent output panel. No click density interpolation or survival differentiation is used. For the parent unweighted insertion probability P_k(s) and survival response q(T,s),

\[
R_\eta=\tfrac12[\sum_k|\Delta P_{\eta,k}-\eta P_k(s)|+|\Delta S_\eta(T)-\eta q(T,s)|].
\]

The parent column is NOT multiplied by insertion spacing: this is one operation, not a continuous-rate quadrature.

| Case | Action | R_eta | R_eta/(eta A_TV) | R_eta / numerical TV indicator |
|---|---:|---:|---:|---:|
| Early | 1/256 | 3.4758068e-6 | 1.15671% | 339.67 |
| Early | 1/512 | 8.7403018e-7 | 0.581733% | 85.41 |
| Late | 1/256 | 1.4208064e-7 | 0.969545% | 13.88 |
| Late | 1/512 | 3.5698460e-8 | 0.487206% | 3.49 |

Early R_high/R_half = 3.97675835; both remainders exceed the frozen 10x indicator requirement, so this quadratic diagnostic passes. Late ratio = 3.98002159, but its half-action remainder falls below 10x the indicator. The late ratio is descriptive, **not resolved validation** under the predeclared rule. The local PASS deliberately covers sign and <5% normalized complete-law remainder; it is not a PASS of every possible criterion.

The four endpoint signals exceed the recorded L1 difference indicators by approximately 7275, 3660, 532 and 267, respectively. Thus the late remainder qualification is not an unresolved negative endpoint sign under those operational indicators.

Indicators are accumulated finite-matrix residual/roundoff estimates, not formal interval-arithmetic or continuum bounds. Their arithmetic was rechecked; reconstruction of every local residual vector was not possible without omitted factors. The archived tangent's observable uncertainty remains null/unknown in the package. Quadratic remainder describes the selected RK operation, not necessarily finite-duration exponential-bath curvature.

Complete-law norms at native detector resolution and common parent panels are both saved. They are not interchanged: coarse panels can hide within-panel signed cancellation.

## 5. What the time histories show

For eta=1/256, after a brief small positive transient, the early operation produces a substantial deficit: minimum Delta D=-5.30891746e-5 near T=5.06375. The cumulative difference crosses from negative to positive between native nodes 5.95400 and5.95425, and reaches +1.48893664e-4 at20. Half action gives the same qualitative behavior and a crossing in [5.95350,5.95375]. These are discrete brackets, not certified continuous roots. A positive early transient peaks at T=2.95425: 1.6414e-7 (high) and8.2912e-8 (half), above their respective practical L1 indicators by factors37.8 and19.1. The late positive transient is below its indicator (factors0.64 and0.32). These fine-grid transients are retained; their detailed times have no independent time-refinement certificate and are not represented on the coarser0.05 prediction grid. See short_transients.json.

The operation took place only once at2.95. Consequently, the later recovery does not require continued environmental action. This independently supports the causal-kernel interpretation that an early transverse modification can affect much later detector encounters.

The late operation remains cumulatively suppressive by20 after its initial tiny transient. It develops a negative minimum near19.24175 and then partially recovers, without reaching a positive cumulative endpoint in the saved window. This does not predict its sign beyond20.

**Qualification: operation time and remaining detection duration were not separately controlled.** At equal elapsed duration u=2.55, the high-action early run is read at T=5.5 and has Delta D=-3.95888352e-5; the late run is read at20 and has Delta D=-1.08923374e-5. Both are negative. The experiment establishes sign control at a fixed deadline; it does not yet establish an opposite-sign effect at equal post-operation duration, or prove that the pre-operation state's age alone is responsible.

Sources: `fresh/horizon_comparison.csv`, `fresh/same_delay_comparison.csv`, F01–F03.

## 6. Physical interpretation, independently reconstructed from the available arrays

For the fixed preparation and detector, define the future detector-only effect E_D(T-s). The exact operation response is

\[
\Delta D_\eta(T;s)=\mathrm{Tr}\{E_D(T-s)[\Phi_\eta-I]\widetilde\rho_0(s)\}.
\]

The original click record through s is unchanged. Local transverse trace preservation leaves the complementary marginal, total survival and instantaneous roof-loss expectation unchanged at the operation itself. Any subsequent difference is mediated by the detector-present evolution.

For the derivative, put a=Tr(Q rho_tilde), rho_hat=rho_tilde/S, rho_J=sum L rho_tilde Ldag/a, d_J=Tr(E rho_J), and d_nc=Tr(E rho_hat). Then

\[
I(s;T)=a(d_J-d_{nc})-S\,\mathrm{Cov}^{sym}_{\widehat\rho}(E,Q).
\]

The signed anticommutator is essential; deleting it would not give the prescribed unobserved trace-preserving operation. Using the saved recycling and anticommutator columns plus the fresh baseline gives:

| Operation time | a(d_J-d_nc) | -S Cov_sym | I(s;20) |
|---:|---:|---:|---:|
| 2.95 | +0.02678050324 | +0.01181608778 | +0.03859659102 |
| 17.45 | -0.00782169832 | +0.00500816356 | -0.00281353476 |

At the early time the normalized recycled state has future detection probability0.4149140 versus0.4039966 for the unperturbed survivor. At the late time these are0.0560887 versus0.0610786. All these are defined for detection by the same final T=20, so the future intervals differ. The positive covariance correction is insufficient to reverse the late negative detectability contrast. These terms provide an exact diagnostic decomposition of the predicted derivative, not independent physical probabilities for the net operation and not a unique coherence or return-path identification.

The pulse population change can be verified independently from the saved shell populations, without a full state matrix. For shell n<N, q_n=n+2, and q_N=0. The no-excitation component is p_n/(1+eta q_n), and excitation transfers eta q_(n-1) p_(n-1)/(1+eta q_(n-1)) into shell n. Agreement with the saved post-operation populations is within1.67e-16.

At high action, mean oscillator occupation conditional on survival increases by0.0114587555 early and0.0115348543 late. Both operations excite transverse motion; the opposite detector responses are not a heating-versus-cooling comparison. Unconditional probabilities of the excitation Kraus alternatives are0.00947177590 and0.00605237126 because the surviving probability and activity differ. Equal eta is not equal realized event count or energy input.

Saved maximum top-shell trace is2.7603e-9; this is a truncation diagnostic, not a substitute for a response-level cutoff test. Local complementary-marginal checks are recorded; the omitted full factors prevent a new full off-diagonal partial-trace check. Population and state-selection observations do not prove non-Markovianity, quantum backflow, a coherence witness, or a unique lower-wall-return mechanism.

Sources: `fresh/mechanism_at_pulses.csv`, `fresh/pulse_population_checks.csv`, original engine/physics code, V9 §§3.11,4.6,4.8,5.6–5.8.

## 7. Synthesis with prior project results

Fresh integration of the older native T20 kernels again gives ground chi_D(20)=-1.279406755467 and first-shell chi_D(20)=+0.310278277944. Fixed mixtures p=.6 and.95 have -0.325595735420 and+0.230794026274. Those are derivatives with respect to a continuously active rate. The new pulse coefficients and finite differences concern a single action eta; they must not be substituted into each other's formula.

The combined evidence supports four distinct layers:

1. Under the specified factorization, the scalar time marginal is exactly invariant under transverse TP operations. This is a theorem and earlier control result, not a freshly executed full-size scalar PulsePair run.
2. Canonical Task07/08 zero-rate channel responses identify spinor environmental sensitivity. The omega100 accepted U2-I reference is not overwritten by the omega144 results.
3. The omega144 T20 family demonstrates preparation-dependent opposite cumulative rate-response signs across later observation windows.
4. The new forward-propagated positive-factor operation independently confirms two preselected causal-kernel predictions: scheduling the same finite positive operation changes the sign of its effect on detection by T=20.

Task09's finite continuously active omega100 trajectories remain a separate validation family. The new experiment does not validate continuous finite-rate preparation reversal at omega144, nor does it extend Task09 through20.

## 8. Novelty assessment and completion decision

This changes the evidential status from a descriptive sign reversal plus a prospective intervention to a model-based quantitative prediction tested by new positive-state propagation. The full time law, not only the endpoint, agrees at the stated finite actions. It is a substantive improvement in predictive support.

It is not a new discovery that noise can assist transport, that a noncommuting local operation can change a later readout, or that finite-window response can be signed. Relevant primary precedents include Yearsley (2010) on open-system arrival time; Plenio–Huelga (2008) on dephasing-assisted network transport; Kassal–Aspuru-Guzik (2012) on ordered-system environmental assistance; Li et al. (2015) on momentum rejuvenation and targeted noise. These precedents limit the breadth of the novelty claim, without duplicating the particular spin–momentum ABC + transverse TP operation + exact scalar-null architecture investigated here.

The defensible advance is detector-specific: preparation- and schedule-dependent signed response under a fixed detector and a particle-preserving, unobserved transverse operation, predicted through its complete causal detector effect and independently tested with positive-state evolution. An exhaustive priority claim has not been established. The covariance split is useful explanatory analysis, not itself a newly discovered general Lindblad identity or proof of uniquely quantum assistance.

For Communications Physics, this is a stronger theory-and-numerics case than the earlier cumulative plots alone. That is an editorial judgment, not an acceptance probability. The paper must make the detector-specific conceptual advance explicit and keep the ideal ABC/finite-model qualifications visible.

The first-priority question is now answered within its declared scope. Do not repeat this pair merely because the late quadratic ratio is unresolved. Do not claim it resolved or relax the frozen rule. The second priority remains the independently propagated detector-only 20/11/02 shell library with shell-resolved roof diagnostics. It addresses the nonmonotonic shell-detectability hypothesis; it has not been completed by these first-shell pulse runs. A finite-duration or alternate-CPTP implementation check is needed only to support a broader physical-pulse claim beyond the specified operation. No broader sweep or new submission was made in this review.

Suggested result sentence:

> In the specified finite spin–momentum absorbing-boundary model, an unobserved transverse excitation operation of fixed positive action enhances detection by T=20 when applied at s=2.95, but suppresses it when applied at s=17.45, for the same incoherent first-shell preparation. Independently propagated censored click laws agree with precomputed unit-insertion predictions; the corresponding factorized scalar timing law is invariant. The sign is a property of the operation schedule and observation horizon, not a universal benefit or cost of excitation.

## Primary literature checked for external context

- J. M. Yearsley, *Quantum Arrival Time For Open Systems*, PRA82,012116(2010), arXiv:1003.6079. https://arxiv.org/abs/1003.6079
- M. B. Plenio and S. F. Huelga, *Dephasing assisted transport: Quantum networks and biomolecules*, NJP10,113019(2008), arXiv:0807.4902. https://arxiv.org/abs/0807.4902
- I. Kassal and A. Aspuru-Guzik, *Environment-assisted quantum transport in ordered systems*, NJP14,053041(2012), arXiv:1201.5202. https://arxiv.org/abs/1201.5202
- Y. Li, F. Caruso, E. Gauger and S. C. Benjamin, *Classical noise assists the flow of quantum energy by momentum rejuvenation*, NJP17,013057(2015), arXiv:1405.7914. https://arxiv.org/abs/1405.7914

This targeted comparison is not a comprehensive literature-priority proof. Manuscript V9 is the supplied theory reference; obsolete workflow statements there are not treated as current data status.
