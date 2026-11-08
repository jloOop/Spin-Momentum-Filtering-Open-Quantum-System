#!/usr/bin/env python3
"""Verify the final Task-08 structural or operational aggregate."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from pathlib import Path

EXPECTED_IDS = {
    "D1", "D2", "D3", "D4", "D5", "D2-I",
    "U1", "U2", "U3", "U4", "U5", "U2-I",
    "P1", "P2", "P3", "P4", "P5", "P2-I",
}
DIRECTIONS = ("downward", "upward", "dephasing")
REQUIRED_FILES = (
    "Task08_run_status.json",
    "Task08_case_identity_table.csv",
    "Task08_case_integrity_audit.json",
    "Task08_supplemental_case_integrity.json",
    "Task08_scalar_null_audit.json",
    "Task08_downward_family_audit.json",
    "Task08_upward_family_audit.json",
    "Task08_dephasing_family_audit.json",
    "Task08_insertion_refinement.csv",
    "Task08_time_step_convergence.csv",
    "Task08_shell_convergence.csv",
    "Task08_uncertainty_budget.json",
    "Task08_evidence_classification.json",
    "Task08_output_hashes.json",
    "Task08_aggregate_report.md",
    "Task08_refinement_compact_results.npz",
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[2] not in {"structural", "final"}:
        raise SystemExit("usage: verify_task08_output.py OUTPUT_DIR structural|final")

    root = Path(sys.argv[1]).expanduser().resolve()
    mode = sys.argv[2]
    if not root.is_dir():
        raise AssertionError(f"Output directory is missing: {root}")

    for name in REQUIRED_FILES:
        path = root / name
        assert path.is_file(), f"Missing final output: {path}"

    status = load_json(root / "Task08_run_status.json")
    integrity = load_json(root / "Task08_case_integrity_audit.json")
    budget = load_json(root / "Task08_uncertainty_budget.json")
    evidence = load_json(root / "Task08_evidence_classification.json")

    cases = integrity.get("cases", {})
    assert set(cases) == EXPECTED_IDS, sorted(cases)
    inadmissible = [
        matrix_id for matrix_id, record in cases.items()
        if record.get("scientific_admissible") is not True
    ]
    assert not inadmissible, f"Scientifically inadmissible roles: {inadmissible}"

    with (root / "Task08_case_identity_table.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        identity_rows = list(csv.DictReader(handle))
    assert {row.get("matrix_id") for row in identity_rows} == EXPECTED_IDS

    with (root / "Task08_insertion_refinement.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        insertion_rows = list(csv.DictReader(handle))
    assert len(insertion_rows) == 3, len(insertion_rows)
    assert {row.get("direction") for row in insertion_rows} == set(DIRECTIONS)
    for row in insertion_rows:
        assert str(row.get("passed", "")).lower() == "true", row

    for direction in DIRECTIONS:
        family = load_json(root / f"Task08_{direction}_family_audit.json")
        insertion = family.get("insertion_grid_convergence", {})
        assert insertion.get("passed") is True, (direction, insertion)
        assert family.get("time_step_convergence", {}).get("passed") is True
        assert family.get("shell_convergence", {}).get("passed") is True

    # Verify all stable output hashes.
    manifest = load_json(root / "Task08_output_hashes.json")
    for relpath, expected in manifest.get("files", {}).items():
        path = root / relpath
        assert path.is_file(), f"Manifested file missing: {path}"
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == expected, f"Hash mismatch for {relpath}: {actual} != {expected}"

    verdict = status.get("scientific_verdict")
    gate = status.get("task08_finite_v8_zero_rate_response_gate_authorized")
    claim = status.get("physical_zero_rate_susceptibility_claim_authorized")

    if mode == "structural":
        assert int(status.get("exit_code", -1)) == 3
        assert gate is False and claim is False
        for direction in DIRECTIONS:
            record = budget["by_direction"][direction]
            missing = set(record.get("missing_required_components", []))
            assert {"epsilon_repr", "epsilon_z"} <= missing, (direction, missing)
            assert record.get("complete") is False
            assert evidence["by_direction"][direction].get("classification") == "BUDGET_INCOMPLETE"
        print("Structural verdict:", verdict)
        print("All 18 roles and all three refinement families pass; inherited budget remains intentionally incomplete.")
        print("TASK08_STRUCTURAL_OUTPUT_VERIFIED")
        return 0

    assert int(status.get("exit_code", -1)) == 0
    assert verdict in {
        "PASS_TASK08_LINEAR_RESPONSE",
        "PASS_TASK08_ALL_CHANNELS_ZERO_COMPATIBLE",
    }, verdict
    assert gate is True and claim is True

    for direction in DIRECTIONS:
        record = budget["by_direction"][direction]
        epsilon = record.get("epsilon_total_zero_rate")
        assert record.get("complete") is True, (direction, record)
        assert not record.get("missing_required_components"), (direction, record)
        assert isinstance(epsilon, (int, float)) and math.isfinite(epsilon) and epsilon >= 0.0
        classification = evidence["by_direction"][direction].get("classification")
        assert classification in {"RESOLVED_NONZERO", "CONSISTENT_WITH_ZERO"}, classification
        ratio = evidence["by_direction"][direction].get("signal_to_uncertainty_ratio")
        print(
            direction,
            "epsilon_total_zero_rate=", f"{float(epsilon):.16e}",
            "classification=", classification,
            "ratio=", ratio,
        )

    print("Scientific verdict:", verdict)
    print("Zero-rate claim authorized:", claim)
    print("Task-09 gate authorized:", gate)
    print("FINAL_TASK08_OUTPUT_AND_HASH_AUDIT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
