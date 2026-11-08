# KL1 job3464306: fresh native audit and bounded KL2 continuation

Audit date: 28 September 2026. Input archive: Task09_Pi800_KL1_Result_3464306.zip.
Input bytes: 81,617,460. SHA-256: 7b8eebff75b49c18d7b3619bdcc4034a2e88c79418fc38d0ccdc527f59dc5810.

## Native status and scope

All 583 payload hashes, exact manifest coverage, unique safe member paths, ZIP CRC and supplied SHA sidecar pass. The original KL1 release45, MQ3 release57 and BLF1 release260 hashes were reopened and verified. Embedded KL1 source bytes match its original release. The actual parent Result3057048 was reopened and all1652 payload hashes verified. Its checkpoint7488 metadata and histories agree byte for byte with the inherited parent.

Job3464306 completed the requested112-step production interval7488→7600. Status is completed, passed:true, last_persisted_step7600; this is not physical acceptance or completion to t6. The uploaded terminal log separately records COMPLETED/0:0 with09:54:42 Slurm elapsed. Production native status timestamps are2026-09-27T22:05:39+00:00 through2026-09-28T07:52:49+00:00. No interpretation of the pasted filename timestamp is used.

## Independent reconstruction

- All27 histories are finite; each inherited prefix through7488 agrees bitwise. Every saved history copy at7500,7525,7550,7575,7600 agrees with the corresponding final-history prefix.
- Calls14977–15200: all224 decisions reconstructed, including1,701,244 candidate-rank entries each recomputed with ordered math.fsum, all admissibility masks, selected minimum ranks, sector assignments, charges and ordered ledgers.
- All15,200 representation terms and7,600 event terms are preserved. Full ordered fsum reconstruction agrees exactly with saved cumulative representation entries in this fresh audit. The stock audit's different grouped accumulation reports6.35e-22; these are different summation reconstructions, not contradictory state values.
- Both sequential roof-click accumulations reproduce their native arrays exactly. No omitted trace is relabelled as roof clicks; no trace is restored.
-4,488 completed detector batches cover283,613 RHS. No recorded solver failure; maximum saved true GMRES residual in the new interval9.99871380579896e-11. These residuals were checked as recorded telemetry, not recomputed from unavailable large factors.
- The saved corrected-zero benchmark, SHA51574ec148fe582a6f028a123e51d904cdb3081f07ae013f91ef4ab56c6400e8, agrees to4.440892098500626e-16 in survival and exactly in per-step clicks. No new zero propagation was done locally.
- Same-allocation KL1 replay and first production step agree bitwise in26 scientific histories and both spectra with actual MQ1 Result3464187. The eight reported factor-hash pairs match. Heavy factor bytes are absent locally, so their hash/trace verification remains an on-PC2 reported result, not a fresh local factor audit.

### Nonzero numerical Gram negatives

Unlike the prior single-step qualification,34 of the224 new spectral decisions have a nonzero negative raw-Gram mass. The maximum is3.3908341504854556e-18; the sum of these recorded diagnostics is2.4335997526012717e-17. All are below the existing1e-16 per-call guard. The frozen implementation already records raw eigenvalues and forms their nonnegative parts for rank selection. Neither the implementation nor its guard was changed. These values are reported rather than silently set to zero. Their sum is not asserted to be a certified total numerical error bound or an environmental-loss ledger.

The inherited corrected-zero history has45 tiny positive survival increments, maximum4.440892098500626e-16 at step398, within the unchanged2e-9 history-audit tolerance. The new suffix is strictly decreasing for both survivals. This historical roundoff is preserved, not edited.

## Endpoint7600 / t3.8

| Quantity | Positive pi/800 | Corrected zero |
|---|---:|---:|
|Survival|0.6169496588862065|0.6151666236821729|
|Accumulated roof clicks|0.38305010360896136|0.3848333763166248|

Roof-click contrast: -0.0017832727076634303.
Representation ledger:2.3749965122957553e-7; ceiling2.375e-7; positive remaining margin3.487704244735264e-13 (last decimal depends on formatting).
Event-omission ledger:0; analytic event-tail bound stored in history1.7292353740919816e-9.
Rank2565 with sectors[1,2247,296,16,5,0,0].
Maximum cumulative positive closure5.1811888113206805e-12; zero closure1.2025935802739696e-12; new-interval maximum step closure1.3545083380096167e-15.

The numerical identity is S_num+C_roof+B_rep+B_event=1+epsilon. Do not replace C_roof by1-S_num: the latter includes omission losses.

The new production restart authority is:
`Task09_Pi800_7488_To7600_PC2_H100_2026-09-27_v1_KrausLifetime1[ARCHIVE_PATH]`
Checkpoint manifest SHA-256:
`50efbbd6420e9035dc1ac62e8dc7bdf7bb6d1c728fde1e0a67a99952d8fd3e83`.

## Memory and phases

11,434 native memory snapshots, including5,376 extra lifetime samples, were checked. Maximum sampled driver allocation:83,634.0625MiB at poolflush_step7599_second_before_compression_before. Headroom to the unchanged88,064MiB guard:4,429.9375MiB. This is sampled high-water evidence, not a continuous-peak bound. No earlier peak was erased after a pool flush.

|Window|Detector s|Both spectrum phases s|Step without checkpoint s|
|---|---:|---:|---:|
|112 new steps|216.7357|93.9594|313.5485|
|Last50|218.5517|95.1432|316.5243|
|Last25|218.5478|98.5670|320.0082|

Five production checkpoints were written. The full native metadata and individual checkpoint durations are in EVIDENCE/native_audit.json. No checkpoint pruning is performed.

Native resource records now report a3TiB quota limit rather than the old September14 snapshot's2TiB. The final recorded quota headroom was1073.152GiB and filesystem free bytes1,105,031,331,840. These are dated run observations, not a promise of current free space. The launcher checks both again live.

## Next block: KL2, same qualified numerical code

KL2 is not a second numerical optimization. The complete block_driver.py (SHA66f411ee455b2c14b846278b97fc65f16273bb1e16451e996fe0468c31305789), lifetime_patch.py (SHAf419d640cbc7f4c1e2a879ca70fae5bcc6454b35d7b5133dda4352d141909569), and all frozen BLF1 numerical dependencies are unchanged. DRIVER_GATE_DELTA.json still documents the original operational gate substitution only; no finite-map body edit is introduced.

This release permits7600→7650 only (50 new full steps; t3.8→3.825), retaining measured-memory limit88,064MiB, Batch64, complex128, dt0.0005, lambda pi/800, all physical cutoffs, solver tolerances, event sectors and the numerical omission policy.

The operational rank limit is2600:35 above the parent rank and30 above KL1's narrower2570 cap, but not above the inherited original BLF1 limit2600. It is a stop threshold, never an instruction to keep fewer than the minimum admissible spectral rank.

The resource screen is explicitly prospective:
M_forecast(r)=34(r+4)-1024 MiB.
This credits another1024MiB after the112-step production audit, for a total2560MiB credit relative to the original MQ1 baseline envelope. That remains smaller than the observed3304MiB paired saving. It lies at least2455.9375MiB above each recorded KL1 step high-water, evaluated against the pre-step rank. It gives86,322MiB at2565 and87,512MiB at2600. This is an empirical bounded admission policy, not a theorem or a guarantee of all subsequent peaks. Exact replay/measurement gates remain mandatory. No historical policy decision is relabelled.

The numerical policy Pi800_Post7200_SamePerCallReserveTo600_J6_v1 is untouched, including the3.75e-7 horizon ceiling. There is no additional omission allowance, ledger reset, retrospective borrowing, reference-prefix rebuild or compression trace restoration. Next production call15201; block final call15300.

Runtime sequence: verify actual parent factor hashes/traces on PC2; run two independent one-step trials7600→7601 with the same qualified numerical implementation; compare all8 actual factor files,26 scientific arrays, both complete spectra and all ordered omission terms bitwise; require both native audits and both sampled-memory guards; then reload the original7600 checkpoint for production. These are repeatability/admission trials, not a new performance A/B benchmark. Neither trial checkpoint is adopted.

The checkpoint cadence is25 steps, yielding7625 and7650 plus a controlled-stop checkpoint. Seven state slots at rank2600 plus16GiB for diagnostics/floor give a90.17576062679291GiB envelope. Live admission remains128GiB in BOTH filesystem and quota. Parent factors are not copied; no previous checkpoints are deleted. Request:1H100,3CPUs,128GiB host RAM,8hours,nocont. There is no automatic resume or propagation beyond7650, even after PASS.

## Local validation and remaining gates

44 frozen BLF1 tests and38 new tests pass (82 total). Reduced finite-map and split-restart calculations are real; factor bytes and scientific histories agree with the original reduced calculation. Parent-promotion, wrong/unsaved/trial-parent rejection, same-parent comparator with real small test-file hashes, history/spectral/ledger/factor tamper rejection, measured-memory failure, nonempty-queue submission, duplicate/ambiguous submission, and source-change checks are covered.

Local runtime:Python3.13.5,NumPy2.3.5,SciPy1.17.0. GPU, Slurm, service and heavy-parent-factor checks are mocked where necessary in local operational tests. Full-size H100 execution remains required. The package repeats the test suites in the pinned PC2 runtime before the two trials.

No remote job or positive production step was submitted/performed here. No fullt6 memory feasibility, full convergence proof, physical acceptance, or Task10 eligibility is claimed. The exact limits and the final integrity/installation/startup tests are recorded separately in the final validation artifact.

The exact unedited batch script was executed from a separate local simulated Slurm spool directory. The real Bash launcher, Python submission/binding, two-trial comparator, three-role dispatch and stdlib exporter ran with mocked Slurm/GPU/private-runtime/heavy-factor services. Exactly one mock submission after a durable intent, duplicate submission/compute rejection, correct monitoring of all logs, and all exported payload hashes passed. An injected module failure stopped at environment setup and the actual early finalizer exported stderr and failure status without starting a trial. These are local operational tests, not real PC2 qualification results.
