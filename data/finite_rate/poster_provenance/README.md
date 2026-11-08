# Historical poster provenance

Section 6 of `RESEARCH_REFERENCE:OpenQuantumExtension_SoFar/BeyondC_A-Jozani.pdf` shows the three rates through 5.65, 8.3 and 3.6. The original PDF remains unchanged in the local research archive; it is not duplicated here.

The source package is `TASKS:Stage09/V16_t=3.6to/Task09_Analysis_Sofat_20260917T180007Z/`. Its source selection, native roof arrays, analysis definitions, endpoint labels and unrounded statistic jointly support the association. No editable poster document or cryptographic connection from the embedded chart to its inputs was supplied, so this is a documented source association rather than proof of the poster authoring pipeline.

## Evidence and identities

- [selected_sources.json](selected_sources.json) preserves the historical archive/member selection. Its archive paths are relative to `TASKS:Stage09/`; archive hashes are **reported**, not freshly verified in this update.
- [prefix_verification.json](prefix_verification.json) records the new read-only comparison. Historical native NPZ bytes match the reported member hashes. All 27 arrays per rate (81 total), including time grids, paired zeros, survival and diagnostics, are bitwise identical to prefixes of the [bundled later histories](../branches/). Thirty derived native-bin arrays and all 22 derived doubling arrays also match the native formulas exactly. The artifact records verified source-file and later-input hashes and the exact scope of the checks.
- The JSON and CSV files in this directory, other than `prefix_verification.json`, are byte-preserving copies of the source package's `selected_sources.json` and corresponding `tables/` files. They retain historical reductions and ancestry evidence; they are not newly executed acceptance audits. Source and distributed identities are in the [release manifest](../../provenance/release_manifest.csv).
- [pi800_repaired_zero_ancestry.csv](pi800_repaired_zero_ancestry.csv) and [paired_zero_comparisons.csv](paired_zero_comparisons.csv) retain the historical scoped comparisons. The current pi800 [repair records](../branches/pi800/repair/) remain authoritative context; no alternate or standalone zero replaces its repaired paired zero.

## Historical statistic

The [unrounded source calculation](integrated_rate_doubling_T5p65_recomputed.json) sums each branch's own native roof-probability differences with `math.fsum` over 11,300 bins ending at or before 5.65. It gives

- pi/3200: ΔC = −0.000516290720464702;
- pi/1600: ΔC = −0.0010318396643455164;
- R = ΔC(pi/1600)/(2 ΔC(pi/3200)) = **0.9992816289790954**;
- Q = ΔC(pi/1600) − 2 ΔC(pi/3200) = **7.417765838875403e−7**;
- absolute deviation = **0.07183710209045513%**.

The freshly repeated native reduction agrees with that source JSON. Section 6 prints 0.9992 and 0.072%. The latter agrees with the unrounded calculation; the former is not nearest-four-decimal rounding (0.9993). Its editorial origin is unestablished. Subtracting saved cumulative arrays gives 0.999281628981739, a floating-point reduction difference far too small to explain the displayed discrepancy. Neither the historical PDF nor its reported statement has been silently corrected.

## Reproduction and limits

The [finite-rate command](../../../REPRODUCING.md#finite-rate-views-and-outputs) recreates the historical curves by cutting the bundled longer histories at the verified state nodes. It also creates the updated full-support views and [compact tables](../results/). The historical NPZ snapshots, source cache, dependency tree and large deliverable archives are unnecessary for these products and are omitted. No continuation prefix is counted as an independent run.

The results page separates [historical and extended support](../README.md) and centralizes the numerical-policy qualifications. This update verifies saved-array provenance and selected reductions; it does not establish complete finite-rate convergence or rerun the full historical audits.
