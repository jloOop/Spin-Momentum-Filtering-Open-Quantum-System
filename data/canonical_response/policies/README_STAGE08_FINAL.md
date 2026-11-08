# Final Task-08 Refinement-Aware Closure Tool

**Version:** `2026-08-10-task08-final-refinement-aware-v3.0`  
**Scope:** one read-only CPU aggregate over the accepted Task-07 `15+3` family and the exact accepted Task-05 roots.

## What this package changes

This package retains the independently audited v2.6 reconstruction engine and applies the dated final-closure policy:

- canonical roles `D1-D5`, `U1-U5`, `P1-P5`;
- supplemental insertion roles `D2-I`, `U2-I`, `P2-I`;
- high-accuracy core `d665...` only for `U2`, `U4`, `U2-I`;
- standard core `827f...` for every other role;
- genuine `ds=0.10 -> 0.05` comparisons, with adjacent fine signed panels summed onto the coarse grid;
- internal `0.10 <-> 0.20` coarsening retained as a nonblocking diagnostic;
- deterministic rerun coverage kept separate from scientific admissibility;
- explicit inherited representation and longitudinal-grid bounds.

It does not execute Task-07 or Task-05, write into any input directory, require a GPU, or use `--strict-reruns`.

## Included bounds files

### Strict structural template

`Task08_Inherited_Uncertainty_STRICT_TEMPLATE_2026-08-10.json`

The representation and longitudinal bounds remain `null`. The expected outcome is an independently reconstructed structural/family pass with exit code `3`, `BUDGET_INCOMPLETE`, and no Task-09 authorization.

### Dated operational amendment

`Task08_Inherited_Uncertainty_OPERATIONAL_AMENDMENT_2026-08-10.json`

This explicitly adopts two inherited transfer envelopes:

- representation: `2.354%` of the accepted insertion-refined response norm;
- longitudinal grid: `0.4%` of the accepted insertion-refined response norm.

These are not direct response-level Cartesian or `Nz=2000` calculations. They are an explicit resource-efficient operational transfer for Task-08 and Task-09 finite-rate validation. Publication-level closure remains qualified until this transfer is retained transparently or replaced by direct response-level controls.

## Required existing ZIB inputs

Task-07 cases:

```text
[ARCHIVE_PATH]
```

Accepted Task-05 register:

```text
[ARCHIVE_PATH]
```

The runner uses the exact 11 accepted Task-05 directories and enforces:

```text
W00 = 4520, not 4070
N16 = 4516, not 4550
```

## Recommended sequence on ZIB

From this extracted tool directory:

```bash
bash run_task08_final_zib.sh structural
```

Required final line:

```text
FINAL_TASK08_STRUCTURAL_AUDIT_PASS
```

Then run the explicitly amended operational audit:

```bash
bash run_task08_final_zib.sh operational
```

Required final lines:

```text
FINAL_TASK08_OUTPUT_AND_HASH_AUDIT_PASS
FINAL_TASK08_OPERATIONAL_PASS
```

The operational output is written to:

```text
[ARCHIVE_PATH]
```

Do not launch Task-09 unless the operational run exits `0`, reports `PASS_TASK08_LINEAR_RESPONSE` or `PASS_TASK08_ALL_CHANNELS_ZERO_COMPATIBLE`, and sets both authorization flags to `true`.

## Expected operational checks

- all `18/18` roles scientifically admissible;
- scalar pointwise and integrated nulls pass;
- downward/upward/dephasing insertion refinements pass;
- all three time-step comparisons pass;
- all three shell comparisons pass;
- Task-05 upward launch identities pass;
- finite zero-rate uncertainty budgets exist for all three directions;
- output manifest hashes verify.

## Failure policy

A nonzero Stage-08 exit does not imply a need to rerun Stage-07. Preserve the new output and log, inspect the exact failed gate, and do not overwrite the directory.
