# Verified finalized parent and exact11845 restart

Date: 27 September 2026. Parent: Task09 pi/3200 job2969484.

## Observed archive and scope

Actually opened `Task09_Pi3200_8849_PilotGated_v1_Continuation_Result_2969484_Compact.zip`.
Bytes: 85,867,263. SHA-256:
`6c7bab5a70c71eef5740f2213f19a8cbfdfe48e30c437735e51d98ca58aa02c0`.
All 186 compact-artifact hashes, 118 package-manifest entries and 119 package
checksums pass. All 120 original package files match the preceding frozen runnable.
The original pilot and promotion records match the previously supplied pilot archive.
The local data-only review passes 751 assertion groups; its executable and complete
machine-readable results are preserved in VALIDATION/ and NATIVE_PARENT_REVIEW.json.
No physical propagation, GPU execution, scheduler action or live PC2 connection occurred.

## Exact saved frontier and stop reason

The run status, terminal checkpoint, native history, independent audit and phase audit
agree on completed_step = last_persisted_step = 11845, t=5.9225.
This is a `clean_nonaccepting_stop` with classification
`PREDICTIVE_WALLTIME_RESOURCE_GUARD`. At the guard before attempted step11846:

- elapsed allocation time: 510617.85934446566 seconds;
- conservative next-step reservation: 603.2772790349554 seconds;
- checkpoint reservation: 120 seconds;
- guarded propagation allowance: 511200 seconds;
- recorded signal: null.

Elapsed plus both reservations exceeds the guarded allowance, so the next step was not
begun. The recorded reason is not rank, memory, disk, GMRES or a user signal.
The solver return code is 2, followed by a passing independent clean-stop audit and
passing phase-port audit. `run_status.passed=false` is retained because the declared
endpoint12000 was not reached; it is not rewritten into full-target success.

Checkpoint:
`Task09_ES_G6H_PC2/4990.Pi3200_8849_To12000_PilotGated_v1/continuation/checkpoint_step11845`.
All9 checkpoint payload identities, including the manifest, are pinned in CONFIG.json.
Heavy factor files are not supplied locally; their actual bytes and traces must pass live
read-only gates on PC2 before this new job can use them.

## Native histories and ledgers

All27 native arrays are finite. There are11846 state nodes and11845 step intervals at
exact declared dt=.0005, from0 through5.9225. Every27-array prefix through the approved
8949 pilot and through the separately uploaded11300 snapshot is byte-identical.
The chronological candidate continuation committed2896 steps,5792 compression calls,
and recorded30 new checkpoints. All17490 representation terms and8745 event terms
retain the original step3100 anchors, including every prior pilot term. The review
reconstructs8746 full-state ledger entries, every new call ceiling, cumulative clicks,
and the diagnostic closure. No prefixes are rebased or renormalized.

| Endpoint observable | Value |
|---|---:|
| Positive survival | 0.5305507673895443 |
| Paired-zero survival | 0.5300283700766036 |
| Cumulative positive roof clicks | 0.4694491528628507 |
| Cumulative zero roof clicks | 0.4699716299191712 |
| Positive minus zero cumulative clicks | -0.0005224770563204695 |
| Sector ranks | [1,1904,190,10,4] |
| Total retained rank | 2109 |
| Representation ledger | 7.9745168651101102e-8 |
| Event first-crossing ledger | 9.750692409664833e-13 |
| Maximum new ledger-accounted step closure | 9.834600097003082e-16 |
| Maximum new reported GMRES residual | 9.999825938854687e-11 |
| Last100-step median computation time | 240.72996157570742 s |

These detector-observable histories are available for preliminary plotting through5.9225;
5.9225 is not6. Use the saved midpoint probabilities, not differentiated survival. The
paired zero is the spinor detector-only reference, not the scalar control or a new
independent zero certification. Closure residuals are accounting diagnostics, not total
physical forward errors. The later rank increase does not undo the already committed
policy; no late strict counterfactual beyond8949 is present.

## Remaining interval with precisely the same policy

The first new full step is11846 and compression call23691. There are155 steps and310
calls left. Every310 future ceiling is exactly the original candidate ceiling at the same
global call; no second early-credit release occurs.

- Current ceiling at23690: 7.974544772315811e-8.
- First new ceiling at23691: 7.97473532524182e-8.
- First new call's available allowance: 2.184601317101393e-12.
- Final ceiling at24000, unchanged: 8.033616179378696e-8.
- Remaining allowance to final ceiling: 5.909931426858593e-10.

155 times the measured last100-step median is10.3647622345 hours of computation.
This is a constant-cost planning estimate, excluding preflight, checks, I/O, audits and
rank/cost changes; it is not an ETA guarantee.

## Evidence boundary

The recorded parent phase-input manifest contains8799 entries. Only11 of those files are
in this compact and locally checked;8788 are intentionally absent (full spectra,
telemetry and other detailed records). The earlier PC2 numerical audit is authenticated
via its source/hash links, not rerun over absent files. This recovery's live preflight
requires the original finalized full ZIP, all8799 phase-input files, recorded audit/device
reports and the exact9 checkpoint payloads on PC2; it hashes them without modifying them.
The locally supplied compact is not a replacement for the large state or full spectra.
All scientific nonacceptance flags remain false. Operational recovery is authorized only
by the explicit new submission and its allocated device/preflight/smoke gates.
