# Integrity and provenance report

## Scope and non-mutation policy

The audit traversed `Part1/Stage07` while excluding this output directory. It found 5,883 files totaling 1,546,283,356 bytes. File-level SHA-256 values are recorded in `STAGE07_FILE_HASH_INVENTORY.csv`; 420 duplicate instances were identified by identical content hash. Existing files were read only.

## Evidence hierarchy

1. **Authoritative scientific inputs:** `Task07_Final_Curated_Input_2026-08-10`, whose register selects 15 canonical and 3 supplemental insertion-refinement roles.
2. **Independent scientific adjudication:** the dated Task-08 aggregate recheck. It reports `PASS_TASK08_LINEAR_RESPONSE`, 15/15 canonical and 3/3 supplemental roles scientifically admissible, and accepts D2-I, U2-I, and P2-I as the response roles.
3. **Priority exploratory extension:** the 12-case upward omega bundle. It passes hashes and case-local loader checks but has no project aggregate or matched convergence budget.
4. **Visualization derivatives and duplicates:** omega-144 timing/spatial exports, root case copies, historical folders, and archive duplicates are kept distinct from ordinary acceptance evidence.

## Hash and reconstruction results

- Curated outer ZIP hashes: 18/18 match the register.
- Curated internal manifests: `all_passed=True`.
- Curated curves-versus-NPZ maximum discrepancy: 0.000e+00.
- Omega case-share manifest: `all_passed=True` (12 entries).
- Omega quicklook manifest: `all_passed=True` (60 entries).
- Omega outer bundle archive sidecar: `all_passed=True`.
- Omega internal manifests: `all_passed=True`.
- Omega curves-versus-NPZ maximum discrepancy: 0.000e+00.
- Omega archive log scan: `all_passed=True`; the scan searched archived stdout/stderr/simulation logs for tracebacks and explicit error/fail lines.
- The omega-144/mode-00 timing arrays match the ordinary quicklook arrays exactly: `True`.

## Preserved legacy case-local failures

The curated register intentionally includes 6 archived roles whose original case-loader verdict is `FAIL`: D2, D4, D5, P2, P4, P5. Each records the same four failures: insertion-quadrature factor-two refinement, two solver JSON/local-response booleans, and the solver-local stage-manifest status. Their ZIPs and internal manifests remain intact. These records are not silently relabelled; the separate, later Task-08 aggregate independently reconstructs the families and marks all selected roles scientifically admissible. The canonical master CSV exposes both statuses side by side.

## Exit/status semantics

Exit code 3 is locally admissible under the frozen Task-07 loader contract. In these records it means `PASS_CASE_LOCAL_RERUN_PENDING`: numerical checks passed, while deterministic same-prefix rerun and/or external aggregate evidence remains pending. It is not treated as an execution failure, and it is not promoted to Task-08 acceptance.

## Scientific boundary

All response quantities are derivatives at zero environmental rate per unit dimensionless rate. No finite-positive-rate state, temperature curve, continuum limit, or publication-level direct-representation closure is produced here. Task-08 itself records that direct response representation/longitudinal refinement and publication-level closure remain incomplete.
