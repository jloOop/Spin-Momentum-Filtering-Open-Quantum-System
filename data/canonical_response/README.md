# Stage-07 full analysis (2026-09-03)

This directory is a read-only scientific audit of the supplied Stage-07 tree, with emphasis on the 12-case upward omega scan. The analysis code reads archived products and writes only here; it never imports or executes the Task-07 solver or loader.

## Reproduce

From the repository root:

```bash
Part1/Stage07/GIFs_Omega144_Snapshots_v1/Task07_Omega144_3D_Analysis_v1/.render_env_v2/bin/python Part1/Stage07/Stage07_Full_Analysis_2026-09-03/scripts/stage07_full_analysis.py
```

The three core CSV artifacts were also imported, inspected for spreadsheet errors, and rendered with the bundled spreadsheet artifact runtime. The verification script is `scripts/verify_csv_artifacts.mjs`.

## Outcome at a glance

- All 18 curated Task-07 case ZIP hashes match the register, and all internal solver/loader hash manifests pass.
- Six archived curated case-local loader records (D2, D4, D5, P2, P4, P5) retain four failed checks tied to the earlier insertion-quadrature test and solver-local status. This is preserved in the master table; the later independent Task-08 aggregate nevertheless marks all 18 selected roles scientifically admissible.
- All 12 omega-scan case-share hashes and all 60 quicklook hashes pass; the compact arrays, curves, metrics, audits, reports, and archive logs were independently cross-checked.
- Each omega case is `PASS_CASE_LOCAL_RERUN_PENDING` (exit 3): no failed local checks, one pending deterministic-rerun item, and no project-level aggregate/convergence adjudication. These cases are exploratory, not Task-08-accepted.
- Modes 10 and 01 are numerically degenerate within at most 1.734e-10 in `chi_D` across the four omega values.
- The excited doublet has negative `chi_D` at omega 4, 36, and 64, and positive `chi_D` at omega 144. The data support only the bracket `64 < omega < 144`; no root or interpolation is claimed.
- At omega 144, the excited-mode net sign reversal is caused by temporal redistribution: early response remains negative while late response is positive and larger. `A_TV/|chi_D|` is about 2.116, exposing strong cancellation.
- The four points do not establish a universal square-root, power, affine, or monotonic law. No fit was made.

## Deliverables

- `STAGE07_EVIDENCE_INVENTORY.csv`: evidence hierarchy and acceptance classification.
- `CANONICAL_CASE_MASTER_TABLE.csv`: 18 curated roles with recomputed response metrics and Task-08 status.
- `OMEGA_SCAN_MASTER_TABLE.csv`: 12 exploratory scan cases with recomputed metrics.
- `INTEGRITY_AND_PROVENANCE_REPORT.md`: hashes, duplicates, archive/log checks, and status semantics.
- `OMEGA_DEPENDENCE_SCIENTIFIC_REPORT.md`: scientific interpretation and limitations.
- `CLAIM_MATRIX.md`: supported, exploratory, and unsupported claims.
- `MANUSCRIPT_UPDATE_PROPOSAL.md`: conservative proposed additions to the V8 manuscript.
- `figures/`: ten figures in PNG and PDF. Lines joining omega samples are explicitly guides, not fits.
- `DELIVERABLE_MANIFEST.json` and `SHA256SUMS`: reproducibility inventory for this directory.
