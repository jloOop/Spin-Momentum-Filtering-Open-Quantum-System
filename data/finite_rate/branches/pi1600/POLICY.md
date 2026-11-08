# IO200 storage-only revision: pi/1600, t6 to t10

The submitted source log stopped BEFORE sbatch, at the old960GiB scratch gate.
It verified job2894739's nine step12000 payloads successfully. This revision
does not invalidate or repeat the completed3.6-to6 calculation.

## Only operational changes relative to the t6-to10 v1 package

Heavy restart checkpoint stride100 ->200, corresponding to0.05 ->0.1 in model
time. The initial plan is40 scheduled full-factor checkpoints, not80.
The storage formula retains the rank2600 worst case, two extra checkpoints,
16GiB working floor,64GiB output/packaging headroom, and32GiB upward rounding.
Its initial gate is544GiB, not960GiB. A live free-space and separate quota
check remain necessary; other jobs can consume this space.

All per-step history samples, midpoint roof probabilities,16000 planned new
compression decisions and spectra remain recorded. The checkpoint writer,
physical driver, detector/bath/compression primitives, GMRES settings, rank
and memory guards, step size, seven-day allocation, and independent auditor
are byte-unchanged. Only the input validator, naming/storage rule, batch job
name, manual-child path guards and configuration are operationally adapted. No existing checkpoint is
deleted, pruned, altered, replaced or renormalized.

Tradeoff: a forced ungraceful kill can lose up to199 committed but not yet
checkpointed steps instead of99. Normal controlled stops still save the
last fully committed state. The last persisted checkpoint, not the latest
console line, remains the restart authority.

## Numerical policy is UNCHANGED from the prior t6-to10 package

Immediate parent2894739 step12000; target20000; dt0.0005; lambda_up=pi/1600.
Retain original step5496 anchors,13008 representation and6504 event terms
through6, and append actual charges only. CAMPAIGN_POLICY.json is byte-identical
to v1. The same global Decimal60 allowance runs from3.749992628669547e-7
at call24000 to6.25e-7 at40000. It is not rebased between allocations.
This is still a nonaccepting feasibility budget, not a physical error estimate.
All physical_claim, production_authorized, task10_eligible, automatic_resume
flags remain false. Unchanged v1 status tokens retain their original meaning.

Later allocations use the same IO200 naming and200-step cadence. The existing
manual-next helper still accepts only an audited predictive wall-time stop,
not numerical, rank, memory, disk, or user-stop failures.

## Evidence

STORAGE_ONLY_EQUIVALENCE.json records the exact configuration/source delta.
LOCAL_VALIDATION.json records tests of this revision. PROVENANCE/IO200_BASE
contains the previous package's unaltered documents and validation: those
are historical records, not newly executed IO200 tests. No live PC2/GPU
execution occurred while preparing this package.
