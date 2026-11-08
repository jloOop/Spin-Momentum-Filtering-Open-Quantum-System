# Task09 pi/1600: completed T=10 saved-output review

Final job3463660, exact immediate parent job2966988 at step19327.
This is an analysis deliverable, not a solver or a runnable HPC restart package.
The untouched original input archive is identified in VERIFICATION.json.

## Start here

- Task09_Pi1600_T10_Verified_Report.pdf: five-page findings and verification report.
- REPORT.md: full source/scope details, numbers and interpretation.
- figures/01_Finite_Rate_Response_0_to10.{png,svg,pdf}: priority delta_g figure.
- original/OUTPUT/block_histories.npz: byte-identical original 27-array native 0-to-10 history.
- data/Nodes_0_to10.csv and Intervals_0_to10.csv: every native sample plus labeled derived quantities.
- data/Nodes_6_to10.csv and Intervals_6_to10.csv: complete requested later interval, no renormalization.
- data/Segment_6_to10.npz: all 27 arrays sliced by their respective node/interval conventions.
- data/Plot_Data_0_to10.npz: numerical data used for the native curve figures.
- endpoints.csv, window_masses.csv, sign_changes.csv, METRICS.json: fresh detector reductions.
- VERIFICATION.json, archive_members.csv, spectrum_reconstruction.csv: fresh independent audit results.
- ARRAY_INVENTORY.json: dtype, shape and raw byte hash of every native array.
- PRESERVED_ORIGINAL_HASHES.json: identities of the unchanged original members retained here.
- reference/U2I_native_case.zip: unchanged earlier uploaded U2-I numerical tangent case.

The first four figures retain every native sample. Figure05 separately aggregates
native detector probabilities into the archived tangent's matching0.05 panels,
without interpolation. These are numerical model times, not assumed SI seconds.

## Important scientific and bookkeeping limits

The native record's representation_ceiling field remains stale at2.25e-7.
Do NOT compare the final6.249954120994585e-7 representation ledger to that field.
The activeH10 line ends at6.25e-7. The6-to10 node CSV includes separate active
policy and margin columns, reconstructed from CONFIG with Decimal precision60.
The original field is not overwritten or corrected in place.

C is recorded midpoint roof clicks, not1-S_retained. B_rep and B_event are
separate numerical losses. The analytical event envelope and overflow diagnostic
are not additional sinks. No trace restoration or normalization was performed.
The original checkpoint metadata retains tiny trace-vs-history reduction differences
(~1.11e-16); curves use history values.

This final history already contains0-to3.6,0-to6,0-to8.3, and0-to9.6635 prefixes.
Do not concatenate them again. It is NOT the independently fresh0-to3.6 rerun.
The standalone-zero input supplied with this lineage stops at3.6; the carried paired
zero continues through10. Other rates' latest endpoints are not inferred here.

24 heavy factor payloads referenced by the four new checkpoint manifests remain
absent. The stored PC2 factor audit is not a new local factor audit. Earlier full
spectra/telemetry absent from the embedded parent compact were not reconstructed.
The original pre5496 ledger qualification remains. New saved-spectrum audit covers
only the1346 compression calls of the last673steps. All later node ledger totals
since5496 were independently reconstructed from their original ordered terms.

Physical_claim, production_authorized, task10_eligible, automatic_resume remainfalse.
Small nonzero numerical response and agreement with a numerical tangent do not,
on their own, establish continuum accuracy, nonlinear curvature or rate-halving.

## Reproduce derived analysis and reports

In a Python environment with NumPy, Matplotlib and ReportLab, from this folder:

    bash scripts/rebuild_analysis.sh

This rewrites ONLY derived outputs in this extracted analysis directory; it does
not change original/ members, the included reference case, or any PC2 file.
The original verification record is not silently rewritten by this command.
The Python source files never import or execute a production solver or bundled auditor.

To repeat the independent full-archive audit, retain the user's original ZIP,
evidence Markdown and SHA256SUMS sidecar (same filenames) in SOURCE_DIR and run:

    python scripts/audit_result.py --source-dir SOURCE_DIR --output NEW_EMPTY_AUDIT_DIR

Providing the earlier uploaded compact/snapshot/source ZIPs in SOURCE_DIR also
repeats their explicit prefix/source comparisons. Missing optional prior uploads
are disclosed by absence from the new earlier_uploaded_prefixes record; the
embedded step19327 parent check is always mandatory.

Scripts are read-only with respect to inputs. audit_result.py rejects an output
folder containing an existing completed verification. No SSH, network or GPU is used.
