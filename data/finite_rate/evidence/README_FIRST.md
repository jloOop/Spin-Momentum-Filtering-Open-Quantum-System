# Task09 analysis collection

Created 2026-09-28T20:01:08.922614+00:00. Original source: `[ARCHIVE_PATH]`. This is a separate collection assembled from saved local evidence. No solver was run; no original was deleted, changed, renamed, linked or moved.

**Share ChatGPT_Core.zip first.** Read BRANCHES.json for exact authoritative member paths and SHA256 values. The full pi1600_raw/ collection is separate and must be retained for detailed numerical/manuscript work.

| Branch | Latest genuine local main job | Actual native history | Native arrays | Retained original payload bytes |
|---|---|---|---:|---:|
| pi1600 (lambda=pi/1600) | 3463660 | t=0–10; 20,001 nodes; step 20,000 | 27 | 4,068,647,149 |
| pi800 (lambda=pi/800) | 3465589, KL2 | t=0–3.825; 7,651 nodes; step 7,650 | 27 | 58,972,672 |
| pi3200 (lambda=pi/3200) | 3464181 | t=0–6; 12,001 nodes; step 12,000 | 27 | 185,888,833 |
| pi0 (standalone lambda=0) | 2878654 | t=0–3.6; 7,201 nodes; step 7,200 | 24 | 31,661,853 |

All main histories use dt=0.0005, Nshell=12, Nz=1500, omega=100, dimension=273000. Positive branches preserve their own paired-zero arrays; pi0 is a separately identified standalone run. Event-sector caps are 4, 6, 4 and 0, respectively. No resampling, smoothing, dtype conversion, metadata repair, history concatenation or renormalization was performed.

## Authoritative histories

- **pi1600**: `pi1600_raw/analysis_core/A136/Task09_Pi1600_S19327_To1000_PC2_H100_v1_IO200_Result_3463660/OUTPUT/block_histories.npz`
- **pi0**: `pi0_core/A100/SESSION/block_histories.npz`
- **pi3200**: `pi3200_core/A148/Task09_Pi3200_11845_To12000_v2_Result_3464181_Compact/OUTPUT/recovery/block_histories.npz`
- **pi800**: `pi800_core/A162/SESSION/block_histories.npz`

## Lineages and separate experiments

pi1600: the final job3463660 continues job2966988 at19327, which continues2894739 at12000, which continues2868412 at7200, following the historical step5600 result9451476. Older checkpoints and detailed rank/policy/audit evidence are kept in 29 byte-identical original raw containers, including nested historical dependencies. Older oracle, correction, replay and failed-attempt records are not independent extensions of the final trajectory. Their native records and statuses remain unchanged.

pi800: job2878201 stopped at3792 with the old paired-zero problem; repair2879756 restarted from3700 and continued to6230, then2965353 to7200,3057048 to7488,KL1 job3464306 to7600 and KL2 job3465589 to7650. The old unrepaired history is preserved separately at its original job/member path. KL1/KL2 bridge trial states were not adopted; committed histories preserve their parents' full prefixes exactly. t=3.825 is the saved endpoint, not t=6.

pi3200: historical half-rate prefix9423060 → bridge9452826 →9453163 →9453725 →9454535 →9455248 → PC2 parent2863111 →2895255 → candidate pilot2964954 → continuation2969484 → recovery3464181. The strict pilot is a separate trajectory. Job3466150 is an independent zero-only dt-screen over6–6.1; DT001_ZERO_SCREEN_NOT_PASSED. It does not extend the positive-rate branch. V17 pi3200 and pi0 packages targeting10 are preparation evidence, not proof of completed runs.

547 earlier history occurrences compare exactly, array by array and dtype by dtype, to subsets of the latest history. Their original file hashes and alias destinations are recorded; native arrays are never reconstructed. Nonidentical trials, smoke tests, repaired/unrepaired comparisons and fixtures retain distinct paths. PI1600_HISTORICAL_OVERLAPS.json records the earlier raw checkpoint comparisons, including any differing historical/replay fields.

## How to use this collection

SOURCE_MAP.csv maps copies and duplicate/subset references to every discovered source location. FILE_INVENTORY.csv covers all local files; ARCHIVE_INVENTORY.csv and ARCHIVE_MEMBER_INVENTORY.csv cover all archive identities and listings, including unselected older packages. EXPORT_MANIFEST.csv explicitly states what compact selections retained/omitted. Original manifests remain unedited and can refer to absent factor payloads. CHECKPOINT_INVENTORY.csv inventories all692 unique available metadata records, not692 available states. REMOTE_CHECKPOINT_PATHS.csv lists saved provenance paths whose current availability is unverified.

pi1600_raw/ retains full raw result containers, spectra, rank decisions, detector telemetry, ordered ledgers and executed source dependencies. Its analysis_core/ provides direct access to selected files. pi0_core/, pi800_core/ and pi3200_core/ retain core evidence and complete available ordered checkpoint terms while omitting bulky states, exhaustive spectra and verbose telemetry. heavy_states/ currently contains an availability notice only: no pi1600 state factor was available locally and remote SSH access failed. Local standalone-zero states at steps0,100,…,7200 exist in the originals and were inventoried but excluded by the requested core policy.

Existing reports and their scripts are in analysis_reports/. Their original dates, numerical claims, acceptance language and older endpoints were not rewritten. Treat them as historical analyses; use BRANCHES.json for the current saved endpoints. Reproduction code and machine-readable selection are included. No archived source was executed.

## Numerical limitations

Use the positive run's own paired zero for rate differences. For detector bins, delta_g=(positive_step_click-zero_step_click)/dt. C denotes summed roof clicks and differs from1-S_retained. Node times and bin midpoint times are distinct. Independent zero references are comparisons, not replacements. The pi800 direct-zero extension to6 is a reference, not a finite-rate continuation.

The raw pi1600 representation_ceiling array remains at its historical value2.25e-7; interpret the saved active H10 policy separately, with final prospective cap6.25e-7. No metadata was repaired. Ordered ledgers, error allowances and software audit PASS labels are not convergence, physical acceptance, publication acceptance or Task10 eligibility. Full-state replay and complete independent spectral reconstruction are not possible from the small ZIP or currently absent state payloads.

The local collection is verified against its saved source snapshot. The intended remote destination has NOT been created or verified. PC2 scratch is working storage, not a guaranteed permanent backup; the saved operations handoff records no scratch backups/snapshots, and current retention policy was not independently rechecked. Preserve the local originals and arrange durable backup separately.
