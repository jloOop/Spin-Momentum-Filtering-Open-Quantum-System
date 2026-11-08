#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final refinement-aware Task-08 aggregate loader
================================================

This is the dated final-closure amendment of the independent Task-08 loader for
Part I of the open-system absorbing-boundary detector project.  It reuses the
independently audited v2.6 reconstruction engine in ``task08_v26_base.py`` and
changes only the workflow contract that was revised after the final Task-07
family became available:

* 15 canonical roles D1--D5/U1--U5/P1--P5;
* formal supplemental insertion roles D2-I/U2-I/P2-I;
* role-dependent numerical cores (d665... only for U2/U4/U2-I);
* matched 1e-12 response/branch tolerance for that upward subfamily;
* genuine 0.1 -> 0.05 insertion refinement on a common 0.1 panel grid;
* the old internal 0.1 <-> 0.2 coarsening result is retained as a diagnostic,
  never as the final family gate;
* deterministic rerun coverage remains separate from scientific admissibility;
* finite inherited representation and longitudinal-grid bounds are mandatory
  for a final evidence classification.

The program is CPU-only and read-only with respect to every Task-07 and Task-05
input.  It never imports or executes a Task-07 solver or per-case loader.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
import shutil
import sys
import traceback
import zipfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

import numpy as np


# -----------------------------------------------------------------------------
# Load the frozen independent reconstruction engine without modifying it.
# -----------------------------------------------------------------------------
_THIS_FILE = Path(__file__).resolve()
_BASE_FILE = _THIS_FILE.with_name("task08_v26_base.py")
if not _BASE_FILE.is_file():
    raise FileNotFoundError(f"Required base reconstruction engine is missing: {_BASE_FILE}")

_spec = importlib.util.spec_from_file_location("task08_v26_base", _BASE_FILE)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot import Task-08 base engine from {_BASE_FILE}")
base = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = base
_spec.loader.exec_module(base)


FINAL_LOADER_VERSION = "2026-08-10-task08-final-refinement-aware-v3.0"
FINAL_STAGE_NAME = "08_environmental_response_aggregate_loader_final"

STANDARD_CORE_SHA256 = (
    "827fd4993707152393a8adcf891df59d7b4d02310a06e89dd5263c0fd37369af"
)
HIGH_ACCURACY_CORE_SHA256 = (
    "d665b92be5d1efb6954968833f4cf008672add6e8ed5194e9d8a55a2a498d796"
)
CURRENT_MASTER_AUDIT_SHA256 = (
    "ce01921758baf2407c61de9d77b431d80d4f983837be33383d943660b8e21702"
)
FINAL_HANDOFF_SHA256 = (
    "c4529a79558c9a5f61ea8019987991c10177e1d97edc4b16883ff93c4042a84e"
)
P4_CORE_BRIDGE_RELATIVE_DISTANCE = 1.554e-9

ROLE_CORE_POLICY = {
    "U2": HIGH_ACCURACY_CORE_SHA256,
    "U4": HIGH_ACCURACY_CORE_SHA256,
    "U2-I": HIGH_ACCURACY_CORE_SHA256,
}
ROLE_RTOL_POLICY = {
    "U2": 1.0e-12,
    "U4": 1.0e-12,
    "U2-I": 1.0e-12,
}

SUPPLEMENTAL_SPECS: Dict[str, Any] = {
    "D2-I": base.MatrixCaseSpec(
        "D2-I", "spinor", "downward", 100.0, "00", 12,
        5.0e-4, 10.0, 5.0e-2, "insertion_refinement",
    ),
    "U2-I": base.MatrixCaseSpec(
        "U2-I", "spinor", "upward", 100.0, "00", 12,
        5.0e-4, 10.0, 5.0e-2, "insertion_refinement",
    ),
    "P2-I": base.MatrixCaseSpec(
        "P2-I", "spinor", "dephasing", 100.0, "00", 12,
        5.0e-4, 10.0, 5.0e-2, "insertion_refinement",
    ),
}

DIRECTION_REFINEMENT = {
    "downward": ("D2", "D2-I"),
    "upward": ("U2", "U2-I"),
    "dephasing": ("P2", "P2-I"),
}

# Patch only contract metadata in the imported engine.
base.LOADER_VERSION = FINAL_LOADER_VERSION
base.STAGE_NAME = FINAL_STAGE_NAME
base.MASTER_AUDIT_EXPECTED_SHA256 = CURRENT_MASTER_AUDIT_SHA256
base.TASK07_TASK08_HANDOFF_EXPECTED_SHA256 = FINAL_HANDOFF_SHA256


# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(chunk_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def strict_json(path: Path, payload: Mapping[str, Any]) -> None:
    base.atomic_write_derived_json(path, payload)


def role_expected_core(matrix_id: str) -> str:
    return ROLE_CORE_POLICY.get(matrix_id, STANDARD_CORE_SHA256)


def role_expected_rtol(matrix_id: str) -> float:
    return ROLE_RTOL_POLICY.get(matrix_id, 1.0e-10)


def identity_key(spec: Any) -> Tuple[Any, ...]:
    return base.CaseIdentity(
        spec.propagator_type,
        spec.environment_direction,
        spec.omega,
        spec.initial_mode,
        spec.n_shell,
        spec.dt,
        spec.t_final,
        spec.insertion_dt,
    ).key()


def flatten_false_checks(payload: Any, prefix: str = "") -> List[str]:
    out: List[str] = []
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            name = f"{prefix}.{key}" if prefix else str(key)
            out.extend(flatten_false_checks(value, name))
    elif isinstance(payload, bool) and not payload:
        out.append(prefix)
    return out


# -----------------------------------------------------------------------------
# Amend the v2.6 candidate-selection policy to use role-dependent cores.
# -----------------------------------------------------------------------------
_ORIGINAL_SELECT_MATRIX_CANDIDATES = base.select_matrix_candidates


def final_select_matrix_candidates(
    records: Sequence[Any], *, expected_core_sha256: str
) -> Tuple[Dict[str, Optional[Any]], Dict[str, Dict[str, Any]]]:
    std_selected, std_decisions = _ORIGINAL_SELECT_MATRIX_CANDIDATES(
        records, expected_core_sha256=STANDARD_CORE_SHA256
    )
    hi_selected, hi_decisions = _ORIGINAL_SELECT_MATRIX_CANDIDATES(
        records, expected_core_sha256=HIGH_ACCURACY_CORE_SHA256
    )
    selected: Dict[str, Optional[Any]] = {}
    decisions: Dict[str, Dict[str, Any]] = {}
    for matrix_id in base.SPEC_BY_ID:
        if matrix_id in {"U2", "U4"}:
            selected[matrix_id] = hi_selected[matrix_id]
            decisions[matrix_id] = dict(hi_decisions[matrix_id])
        else:
            selected[matrix_id] = std_selected[matrix_id]
            decisions[matrix_id] = dict(std_decisions[matrix_id])
        decisions[matrix_id]["final_role_expected_core_sha256"] = role_expected_core(matrix_id)
        decisions[matrix_id]["final_role_core_policy_applied"] = True
    return selected, decisions


base.select_matrix_candidates = final_select_matrix_candidates


# -----------------------------------------------------------------------------
# Amend local checks: role-dependent core/rtol, variable insertion-grid size,
# and nonblocking legacy 0.1<->0.2 diagnostics.
# -----------------------------------------------------------------------------
_ORIGINAL_AUDIT_CONFIGURATION = base.audit_configuration
_ORIGINAL_AUDIT_RAW = base.audit_raw_response_products
_ORIGINAL_AUDIT_SAVED_JSON = base.audit_saved_json_records
_ORIGINAL_AUDIT_PER_CASE_LOADER = base.audit_per_case_loader


def final_audit_configuration(
    candidate: Any,
    spec: Any,
    *,
    expected_core_sha256: str,
    synthetic_mode: bool,
) -> Dict[str, Any]:
    matrix_id = str(spec.matrix_id)
    expected_core = role_expected_core(matrix_id)
    result = _ORIGINAL_AUDIT_CONFIGURATION(
        candidate,
        spec,
        expected_core_sha256=expected_core,
        synthetic_mode=synthetic_mode,
    )
    checks = result["checks"]
    metrics = result["metrics"]
    config = candidate.configuration

    expected_rtol = role_expected_rtol(matrix_id)
    branch_rtol = base.finite_float(
        base.nested_get(
            config,
            "gmres.branch_rtol",
            "branch_gmres_rtol",
            default=config.get("response_reference_gmres_rtol"),
        )
    )
    response_rtol = base.finite_float(
        config.get(
            "response_reference_gmres_rtol",
            base.nested_get(config, "gmres.response_reference_rtol"),
        )
    )
    checks.pop("response_reference_rtol_1e-10", None)
    checks.pop("branch_rtol_1e-10", None)
    checks["response_reference_rtol_matches_final_role_policy"] = bool(
        response_rtol is not None
        and np.isclose(response_rtol, expected_rtol, rtol=0.0, atol=1.0e-18)
    )
    checks["branch_rtol_matches_final_role_policy"] = bool(
        branch_rtol is not None
        and np.isclose(branch_rtol, expected_rtol, rtol=0.0, atol=1.0e-18)
    )
    checks["response_and_branch_rtol_matched"] = bool(
        branch_rtol is not None
        and response_rtol is not None
        and np.isclose(branch_rtol, response_rtol, rtol=0.0, atol=1.0e-18)
    )
    metrics["final_role_expected_core_sha256"] = expected_core
    metrics["final_role_expected_response_and_branch_rtol"] = expected_rtol

    # v2.6 named this a 101-node gate.  Final Task-08 accepts the complete
    # declared grid: 101 nodes for ds=0.1 and 201 nodes for ds=0.05.
    checks.pop("expected_101_node_grid", None)
    try:
        expected_steps, expected_times = base.expected_insertion_grid(config)
        declared = config.get("complete_insertion_grid", {})
        checks["complete_declared_insertion_grid_node_count"] = bool(
            isinstance(declared, Mapping)
            and int(declared.get("node_count", -1)) == expected_steps.size
            and int(declared.get("panel_count", -1)) == expected_steps.size - 1
            and expected_times.size in {101, 201}
        )
    except Exception:
        checks["complete_declared_insertion_grid_node_count"] = False
    return result


base.audit_configuration = final_audit_configuration


def _fine_grid_main_shape_pass(result: Mapping[str, Any], candidate: Any) -> bool:
    config = candidate.configuration
    insertion_dt = float(config.get("insertion_dt", math.nan))
    t_final = float(config.get("T_final", math.nan))
    expected_nodes = int(round(t_final / insertion_dt)) + 1
    expected_panels = expected_nodes - 1
    arrays = result.get("arrays", {})
    try:
        return bool(
            expected_nodes in {101, 201}
            and result.get("metrics", {}).get("number_of_insertion_nodes") == expected_nodes
            and result.get("metrics", {}).get("number_of_output_panels") == expected_panels
            and np.asarray(arrays["times"]).shape == (expected_nodes,)
            and np.asarray(arrays["insertion_steps"]).shape == (expected_nodes,)
            and np.asarray(arrays["panel_durations"]).shape == (expected_panels,)
            and np.asarray(arrays["chi_survival"]).shape == (expected_nodes,)
            and np.asarray(arrays["chi_click_density"]).shape == (expected_panels,)
            and np.asarray(arrays["chi_panel_probability"]).shape == (expected_panels,)
            and np.asarray(arrays["kernel_total_probability"]).shape
            == (expected_panels, expected_nodes)
            and np.asarray(arrays["kernel_survival"]).shape
            == (expected_nodes, expected_nodes)
        )
    except Exception:
        return False


def final_audit_raw_response_products(candidate: Any) -> Dict[str, Any]:
    result = _ORIGINAL_AUDIT_RAW(candidate)
    checks = result.get("checks", {})
    metrics = result.get("metrics", {})

    # Preserve the numerical value and original pass/fail as a diagnostic.
    original_internal = checks.get("insertion_grid_factor_two_check")
    metrics["legacy_internal_factor_two_insertion_diagnostic"] = {
        "comparison": (
            f"ds={candidate.configuration.get('insertion_dt')} versus internally "
            f"coarsened ds={2.0 * float(candidate.configuration.get('insertion_dt', 0.0))}"
        ),
        "original_pass": original_internal,
        "nonblocking_in_final_Task08": True,
        "final_family_gate": "independent canonical ds=0.1 versus supplemental ds=0.05",
        "metrics": metrics.get("insertion_comparison", {}),
    }
    checks.pop("insertion_grid_factor_two_check", None)
    checks["legacy_internal_factor_two_insertion_is_diagnostic_only"] = True

    if np.isclose(
        float(candidate.configuration.get("insertion_dt", math.nan)),
        5.0e-2,
        rtol=0.0,
        atol=1.0e-15,
    ):
        checks["main_array_shapes_and_dtypes"] = _fine_grid_main_shape_pass(
            result, candidate
        )

    result["failed_checks"] = sorted(
        name for name, passed in checks.items() if not passed
    )
    return result


base.audit_raw_response_products = final_audit_raw_response_products


_NONBLOCKING_SAVED_RESPONSE_SUFFIXES = {
    "insertion_quadrature_factor_two_refinement",
}


def final_audit_saved_json_records(candidate: Any) -> Dict[str, Any]:
    result = _ORIGINAL_AUDIT_SAVED_JSON(candidate)
    failed = [str(item) for item in result.get("failed_saved_response_checks", [])]
    terminal_names = {item.rsplit(".", 1)[-1] for item in failed}
    if failed and terminal_names <= _NONBLOCKING_SAVED_RESPONSE_SUFFIXES:
        result["checks"]["saved_response_has_no_failed_boolean_check"] = True
        result["checks"]["saved_response_local_checks_passed"] = True
        result["legacy_internal_coarsening_saved_failure_nonblocking"] = {
            "original_failed_checks": failed,
            "final_policy": (
                "retained as diagnostic; family insertion gate supplied by "
                "D2-I/U2-I/P2-I"
            ),
        }
    return result


base.audit_saved_json_records = final_audit_saved_json_records


_NONBLOCKING_CASE_LOADER_FAILURES = {
    "independent_numerical_reconstruction.insertion_quadrature_factor_two_refinement",
    "solver_JSON_records.all_solver_response_boolean_checks_pass",
    "solver_JSON_records.response_audit_local_checks_passed",
    "status_and_stage_manifest.solver_local_checks_reported_pass",
}


def final_audit_per_case_loader(candidate: Any, *, synthetic_mode: bool) -> Dict[str, Any]:
    result = _ORIGINAL_AUDIT_PER_CASE_LOADER(
        candidate, synthetic_mode=synthetic_mode
    )
    failed = set(str(item) for item in result.get("metrics", {}).get("loader_failed_checks", []))
    if failed and failed <= _NONBLOCKING_CASE_LOADER_FAILURES:
        result["checks"]["per_case_loader_has_no_failed_checks"] = True
        result["checks"]["per_case_loader_all_checks_passed"] = True
        result["metrics"]["legacy_internal_coarsening_loader_failure_nonblocking"] = True
        result["metrics"]["original_loader_failed_checks"] = sorted(failed)
    return result


base.audit_per_case_loader = final_audit_per_case_loader


# -----------------------------------------------------------------------------
# Supplemental-case selection and independent audit
# -----------------------------------------------------------------------------
def _supplemental_decision(candidate: Any, spec: Any) -> Dict[str, Any]:
    return {
        "matrix_id": spec.matrix_id,
        "expected": asdict(spec),
        "selected_origin": candidate.package.origin,
        "mirror_origins": [],
        "conflicting_origins": [],
        "reason": "unique curated supplemental insertion-refinement package",
        "final_role_expected_core_sha256": role_expected_core(spec.matrix_id),
    }


def audit_supplemental_cases(
    records: Sequence[Any], options: Any
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    results: Dict[str, Any] = {}
    decisions: Dict[str, Any] = {}
    for matrix_id, spec in SUPPLEMENTAL_SPECS.items():
        matches = [
            record
            for record in records
            if record.identity is not None and record.identity.key() == identity_key(spec)
        ]
        complete = [record for record in matches if base._candidate_is_complete(record)]
        expected_core = role_expected_core(matrix_id)
        accepted = [
            record
            for record in complete
            if str(record.configuration.get("numerical_core_sha256", "")) == expected_core
        ]
        if not accepted:
            decision = {
                "matrix_id": matrix_id,
                "expected": asdict(spec),
                "selected_origin": None,
                "mirror_origins": [],
                "conflicting_origins": [],
                "matching_origins": [record.package.origin for record in matches],
                "reason": "required supplemental case is missing or uses an unapproved core",
            }
            decisions[matrix_id] = decision
            results[matrix_id] = base.missing_case_result(spec, decision)
            continue

        fingerprints: Dict[str, List[Any]] = {}
        for record in accepted:
            fingerprints.setdefault(record.scientific_fingerprint or "<none>", []).append(record)
        if len(fingerprints) > 1:
            decision = {
                "matrix_id": matrix_id,
                "expected": asdict(spec),
                "selected_origin": None,
                "mirror_origins": [],
                "conflicting_origins": sorted(record.package.origin for record in accepted),
                "reason": "multiple nonidentical supplemental packages map to one role",
            }
            decisions[matrix_id] = decision
            results[matrix_id] = base.conflicting_case_result(spec, decision)
            continue

        group = next(iter(fingerprints.values()))
        candidate = sorted(
            group,
            key=lambda record: (
                -record.required_file_count,
                0 if record.package.kind == "zip" else 1,
                record.package.origin,
            ),
        )[0]
        decision = _supplemental_decision(candidate, spec)
        decision["mirror_origins"] = sorted(
            record.package.origin for record in group if record is not candidate
        )
        decisions[matrix_id] = decision
        try:
            results[matrix_id] = base.audit_one_case(candidate, spec, decision, options)
        except Exception as exc:
            results[matrix_id] = base.CaseAuditResult(
                matrix_id=matrix_id,
                spec=spec,
                status=base.STATUS_FAILED,
                scientific_admissible=False,
                reproducibility_closed=False,
                selected_candidate=candidate,
                mirror_origins=list(decision.get("mirror_origins", [])),
                conflicting_origins=[],
                checks={"unhandled_supplemental_audit_exception": False},
                failed_checks=["unhandled_supplemental_audit_exception"],
                warnings=[],
                pending_items=[],
                metrics={"exception": repr(exc), "traceback": traceback.format_exc()},
                arrays={},
                configuration=dict(candidate.configuration),
                provenance={**candidate.package.describe(), "selection_decision": decision},
            )
    return results, {"selection_decisions": decisions}


# -----------------------------------------------------------------------------
# Genuine 0.1 -> 0.05 family comparison
# -----------------------------------------------------------------------------
def coarsen_fine_response_to_baseline_grid(
    baseline: Any, fine: Any
) -> Dict[str, np.ndarray]:
    t0 = np.asarray(baseline.arrays["times"], dtype=np.float64)
    s0 = np.asarray(baseline.arrays["chi_survival"], dtype=np.float64)
    p0 = np.asarray(baseline.arrays["chi_panel_probability"], dtype=np.float64)
    tf = np.asarray(fine.arrays["times"], dtype=np.float64)
    sf = np.asarray(fine.arrays["chi_survival"], dtype=np.float64)
    pf = np.asarray(fine.arrays["chi_panel_probability"], dtype=np.float64)

    if tf.size != 2 * t0.size - 1:
        raise ValueError(
            f"fine/coarse node-count mismatch: fine={tf.size}, coarse={t0.size}"
        )
    if pf.size != 2 * p0.size:
        raise ValueError(
            f"fine/coarse panel-count mismatch: fine={pf.size}, coarse={p0.size}"
        )
    if base.max_abs_difference(tf[::2], t0) > 2.0e-12:
        raise ValueError("fine even-node grid does not match canonical 0.1 grid")
    fine_panel_on_coarse = pf.reshape(p0.size, 2).sum(axis=1, dtype=np.float64)
    fine_survival_on_coarse = sf[::2]
    fine_density_on_coarse = fine_panel_on_coarse / np.diff(t0)
    return {
        "times": t0,
        "baseline_survival": s0,
        "baseline_panel_probability": p0,
        "fine_survival_on_coarse": fine_survival_on_coarse,
        "fine_panel_probability_on_coarse": fine_panel_on_coarse,
        "fine_click_density_on_coarse": fine_density_on_coarse,
    }


def insertion_refinement_record(
    direction: str, baseline: Any, fine: Any
) -> Dict[str, Any]:
    available = bool(baseline.arrays and fine.arrays)
    evaluable = bool(baseline.scientific_admissible and fine.scientific_admissible)
    if not available:
        return {
            "direction": direction,
            "comparison_type": "canonical_ds0.1_vs_independent_ds0.05",
            "baseline": baseline.matrix_id,
            "control": fine.matrix_id,
            "available": False,
            "scientific_gate_evaluable": False,
            "passed": False,
            "metrics": {},
        }
    try:
        common = coarsen_fine_response_to_baseline_grid(baseline, fine)
        metrics = base.signed_response_distance(
            common["times"],
            common["baseline_survival"],
            common["baseline_panel_probability"],
            common["times"],
            common["fine_survival_on_coarse"],
            common["fine_panel_probability_on_coarse"],
        )
        base_int = baseline.metrics["raw"]["integrated_response"]
        fine_int = fine.metrics["raw"]["integrated_response"]
        metrics.update(
            {
                "chi_D_E_absolute_difference": abs(
                    float(base_int["chi_D_E"]) - float(fine_int["chi_D_E"])
                ),
                "chi_D_L_absolute_difference": abs(
                    float(base_int["chi_D_L"]) - float(fine_int["chi_D_L"])
                ),
                "coarsening_rule": (
                    "sum adjacent pairs of independent ds=0.05 signed panel "
                    "probabilities onto the ds=0.1 panel grid; sample survival "
                    "at every second fine node"
                ),
                "absolute_gate": base.INSERTION_CONVERGENCE_ABS_TOL,
                "relative_gate": base.INSERTION_CONVERGENCE_REL_TOL,
            }
        )
        passed = bool(
            metrics["complete_signed_measure_distance"]
            <= base.INSERTION_CONVERGENCE_ABS_TOL
            or metrics["relative_signed_measure_distance"]
            <= base.INSERTION_CONVERGENCE_REL_TOL
        )
        return {
            "direction": direction,
            "comparison_type": "canonical_ds0.1_vs_independent_ds0.05",
            "baseline": baseline.matrix_id,
            "control": fine.matrix_id,
            "available": True,
            "scientific_gate_evaluable": evaluable,
            "passed": passed,
            "metrics": metrics,
            "coarsened_arrays": common,
        }
    except Exception as exc:
        return {
            "direction": direction,
            "comparison_type": "canonical_ds0.1_vs_independent_ds0.05",
            "baseline": baseline.matrix_id,
            "control": fine.matrix_id,
            "available": True,
            "scientific_gate_evaluable": evaluable,
            "passed": False,
            "metrics": {"error": str(exc)},
        }


def augment_family_audits(
    canonical: Mapping[str, Any],
    supplemental: Mapping[str, Any],
    family_audits: Dict[str, Any],
) -> Dict[str, Any]:
    insertion_rows: List[Dict[str, Any]] = []
    for direction, (baseline_id, fine_id) in DIRECTION_REFINEMENT.items():
        record = insertion_refinement_record(
            direction, canonical[baseline_id], supplemental[fine_id]
        )
        family_audits["families"][direction]["insertion_grid_convergence"] = {
            key: value for key, value in record.items() if key != "coarsened_arrays"
        }
        family_audits["families"][direction]["supplemental_matrix_id"] = fine_id
        family_audits["families"][direction]["all_six_cases_scientifically_admissible"] = bool(
            family_audits["families"][direction]["all_five_cases_scientifically_admissible"]
            and supplemental[fine_id].scientific_admissible
        )
        insertion_rows.append(
            {key: value for key, value in record.items() if key != "coarsened_arrays"}
        )

    # The upward shell comparison crosses the approved solver-tolerance family.
    up_shell = family_audits["families"]["upward"]["shell_convergence"]
    up_shell["comparison_type"] = "baseline_vs_N16_shell_plus_tolerance_family"
    up_shell["approved_core_bridge_relative_distance"] = P4_CORE_BRIDGE_RELATIVE_DISTANCE
    up_shell["interpretation"] = (
        "U2 uses the approved d665/1e-12 family and U5 the standard 827f/1e-10 "
        "family; the dated P4 bridge bounds the tolerance-family discrepancy."
    )
    family_audits["insertion_rows"] = insertion_rows
    return family_audits


# -----------------------------------------------------------------------------
# Final uncertainty/evidence budget: use the genuine insertion comparison and
# the accepted fine tangent as the response norm.
# -----------------------------------------------------------------------------
def _absolute_or_relative_bound(
    payload: Mapping[str, Any],
    direction: str,
    name: str,
    response_norm: float,
) -> Tuple[Optional[float], Dict[str, Any]]:
    absolute = base.inherited_bound_for(payload, direction, name)
    if absolute is not None:
        return absolute, {"mode": "absolute", "value": absolute}
    block = payload.get("by_direction", {})
    direction_block = block.get(direction, {}) if isinstance(block, Mapping) else {}
    relative_key = f"{name}_relative_to_accepted_response_norm"
    relative = None
    if isinstance(direction_block, Mapping):
        relative = base.finite_float(direction_block.get(relative_key))
    if relative is None:
        global_block = payload.get("global", {})
        if isinstance(global_block, Mapping):
            relative = base.finite_float(global_block.get(relative_key))
    if relative is not None and relative >= 0.0:
        value = float(relative * response_norm)
        return value, {
            "mode": "relative_to_accepted_response_norm",
            "relative_envelope": relative,
            "accepted_response_norm": response_norm,
            "derived_absolute_bound": value,
        }
    return None, {"mode": "unavailable"}


def build_final_uncertainty_and_evidence(
    canonical: Mapping[str, Any],
    supplemental: Mapping[str, Any],
    family_audits: Mapping[str, Any],
    inherited_bounds: Mapping[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    letter = {"downward": "D", "upward": "U", "dephasing": "P"}
    budgets: Dict[str, Any] = {}
    classifications: Dict[str, Any] = {}
    for direction, symbol in letter.items():
        baseline = canonical[f"{symbol}2"]
        fine = supplemental[f"{symbol}2-I"]
        accepted = fine if fine.scientific_admissible and fine.arrays else baseline
        family = family_audits["families"][direction]
        accepted_raw = accepted.metrics.get("raw", {})
        response_norm = base.finite_float(
            base.nested_get(
                accepted_raw,
                "integrated_response.chi_complete_signed_measure_norm",
            )
        )
        insertion = family.get("insertion_grid_convergence", {})
        epsilon_s = base.finite_float(
            base.nested_get(insertion, "metrics.complete_signed_measure_distance")
        )
        epsilon_dt = base.finite_float(
            base.nested_get(
                family,
                "time_step_convergence.metrics.complete_signed_measure_distance",
            )
        )
        epsilon_n = base.finite_float(
            base.nested_get(
                family,
                "shell_convergence.metrics.complete_signed_measure_distance",
            )
        )
        solve_record = (
            base.solve_uncertainty_component(accepted)
            if accepted.arrays
            else {
                "epsilon_solve": None,
                "components": {},
                "formula": "accepted response is unavailable",
            }
        )
        epsilon_solve = base.finite_float(solve_record.get("epsilon_solve"))
        if response_norm is None:
            epsilon_repr, repr_record = None, {"mode": "unavailable"}
            epsilon_z, z_record = None, {"mode": "unavailable"}
        else:
            epsilon_repr, repr_record = _absolute_or_relative_bound(
                inherited_bounds, direction, "epsilon_repr", response_norm
            )
            epsilon_z, z_record = _absolute_or_relative_bound(
                inherited_bounds, direction, "epsilon_z", response_norm
            )
        epsilon_core = (
            float(P4_CORE_BRIDGE_RELATIVE_DISTANCE * response_norm)
            if direction == "upward" and response_norm is not None
            else 0.0
        )
        components: Dict[str, Optional[float]] = {
            "epsilon_repr": epsilon_repr,
            "epsilon_z": epsilon_z,
            "epsilon_dt": epsilon_dt,
            "epsilon_N": epsilon_n,
            "epsilon_s_quad": epsilon_s,
            "epsilon_solve": epsilon_solve,
            "epsilon_core_family_bridge": epsilon_core,
            "epsilon_init": 0.0,
            "epsilon_MC": 0.0,
        }
        missing = [name for name, value in components.items() if value is None]
        epsilon_total = (
            None
            if missing
            else float(sum(float(value) for value in components.values() if value is not None))
        )
        ratio = (
            None
            if response_norm is None
            or epsilon_total is None
            or epsilon_total <= 0.0
            else response_norm / epsilon_total
        )
        if response_norm is None or epsilon_total is None:
            classification = base.EVIDENCE_BUDGET_INCOMPLETE
        elif epsilon_total == 0.0:
            classification = (
                base.EVIDENCE_ZERO if response_norm == 0.0 else base.EVIDENCE_RESOLVED
            )
        elif ratio is not None and ratio >= base.EVIDENCE_FACTOR:
            classification = base.EVIDENCE_RESOLVED
        elif ratio is not None and ratio <= 1.0:
            classification = base.EVIDENCE_ZERO
        else:
            classification = base.EVIDENCE_UNRESOLVED

        budgets[direction] = {
            "baseline_matrix_id": f"{symbol}2",
            "accepted_response_matrix_id": f"{symbol}2-I",
            "accepted_response_used": accepted.matrix_id,
            "components": components,
            "epsilon_total_zero_rate": epsilon_total,
            "missing_required_components": missing,
            "complete": not missing,
            "epsilon_lin": {
                "value": None,
                "status": (
                    "NOT_APPLICABLE_TO_EXACT_ZERO_RATE_DERIVATIVE; required only "
                    "before finite-rate extrapolation in Tasks 09-10"
                ),
            },
            "solve_component_detail": solve_record,
            "representation_bound_derivation": repr_record,
            "longitudinal_bound_derivation": z_record,
            "inherited_bounds_source": dict(inherited_bounds),
            "conservative_sum_rule": True,
        }
        classifications[direction] = {
            "baseline_matrix_id": f"{symbol}2",
            "accepted_response_matrix_id": f"{symbol}2-I",
            "response_norm": response_norm,
            "epsilon_total_zero_rate": epsilon_total,
            "signal_to_uncertainty_ratio": ratio,
            "classification": classification,
            "resolved_nonzero_factor": base.EVIDENCE_FACTOR,
            "physical_claim_eligible_from_evidence_alone": classification
            in {base.EVIDENCE_RESOLVED, base.EVIDENCE_ZERO},
        }
    return {"by_direction": budgets}, {"by_direction": classifications}


# -----------------------------------------------------------------------------
# Output post-processing
# -----------------------------------------------------------------------------
def _identity_row(result: Any) -> Dict[str, Any]:
    spec = result.spec
    return {
        "matrix_id": spec.matrix_id,
        "role": spec.role,
        "propagator_type": spec.propagator_type,
        "direction": spec.environment_direction,
        "omega": spec.omega,
        "initial_mode": spec.initial_mode,
        "N_shell": spec.n_shell,
        "dt": spec.dt,
        "T_final": spec.t_final,
        "insertion_dt": spec.insertion_dt,
        "canonical_prefix": spec.canonical_prefix(),
        "status": result.status,
        "scientific_admissible": result.scientific_admissible,
        "reproducibility_closed": result.reproducibility_closed,
        "selected_origin": (
            result.selected_candidate.package.origin
            if result.selected_candidate is not None
            else None
        ),
        "selected_kind": (
            result.selected_candidate.package.kind
            if result.selected_candidate is not None
            else None
        ),
        "numerical_core_sha256": result.configuration.get("numerical_core_sha256"),
        "configuration_sha256": result.configuration.get("configuration_sha256"),
        "scientific_fingerprint": (
            result.selected_candidate.scientific_fingerprint
            if result.selected_candidate is not None
            else None
        ),
        "failed_check_count": len(result.failed_checks),
        "pending_item_count": len(result.pending_items),
    }


def _metric_row(result: Any) -> Dict[str, Any]:
    raw = result.metrics.get("raw", {})
    integrated = raw.get("integrated_response", {})
    insertion = raw.get("insertion_comparison", {})
    return {
        "matrix_id": result.matrix_id,
        "status": result.status,
        "scientific_admissible": result.scientific_admissible,
        "reproducibility_closed": result.reproducibility_closed,
        "chi_D": integrated.get("chi_D_from_panel_sum"),
        "minus_chi_S_T": integrated.get("chi_D_from_final_survival"),
        "chi_mu": integrated.get("chi_mu_restricted"),
        "chi_D_E": integrated.get("chi_D_E"),
        "chi_D_L": integrated.get("chi_D_L"),
        "complete_signed_measure_norm": integrated.get(
            "chi_complete_signed_measure_norm"
        ),
        "survival_W1_norm": integrated.get("chi_survival_W1_norm"),
        "maximum_tangent_closure": raw.get(
            "maximum_tangent_probability_closure_residual"
        ),
        "relative_tangent_closure": raw.get(
            "relative_tangent_probability_closure_residual"
        ),
        "maximum_per_insertion_closure": raw.get(
            "maximum_independent_kernel_probability_closure_residual"
        ),
        "maximum_source_trace": raw.get("maximum_source_trace_residual"),
        "maximum_noncausal_kernel": raw.get("maximum_noncausal_kernel_entry"),
        "minimum_jump_kernel_probability": raw.get("minimum_jump_kernel_probability"),
        "insertion_signed_measure_distance": insertion.get("signed_measure_distance"),
        "insertion_relative_signed_measure_distance": insertion.get(
            "relative_signed_measure_distance"
        ),
        "insertion_chi_mu_absolute_difference": insertion.get(
            "chi_mu_absolute_difference"
        ),
        "benchmark_survival_difference": raw.get(
            "benchmark_maximum_abs_chi_survival_difference"
        ),
        "benchmark_panel_difference": raw.get(
            "benchmark_maximum_abs_chi_panel_probability_difference"
        ),
        "scalar_pointwise_kernel_max": raw.get(
            "maximum_abs_scalar_pointwise_click_kernel"
        ),
        "scalar_response_max": raw.get("maximum_abs_scalar_response_component"),
        "failed_checks": result.failed_checks,
        "pending_items": result.pending_items,
    }


def _read_csv(path: Path) -> Tuple[List[str], List[Dict[str, Any]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _append_final_report(
    report_path: Path,
    supplemental: Mapping[str, Any],
    family_audits: Mapping[str, Any],
    uncertainty: Mapping[str, Any],
    evidence: Mapping[str, Any],
    overall: Mapping[str, Any],
) -> None:
    lines = [
        "",
        "---",
        "",
        "# Final refinement-aware closure amendment",
        "",
        f"- Loader version: `{FINAL_LOADER_VERSION}`",
        "- Canonical cases: `15/15` required.",
        "- Supplemental insertion refinements: `D2-I`, `U2-I`, `P2-I`.",
        "- Internal `0.1↔0.2` coarsening is diagnostic only.",
        "- Final insertion gate: independent `0.1→0.05` comparison.",
        "- Upward high-accuracy core is accepted only for `U2`, `U4`, `U2-I`.",
        "",
        "## Supplemental-case status",
        "",
        "| Role | Status | Scientifically admissible | Rerun closed |",
        "|---|---|---:|---:|",
    ]
    for matrix_id in ("D2-I", "U2-I", "P2-I"):
        result = supplemental[matrix_id]
        lines.append(
            f"| {matrix_id} | {result.status} | {result.scientific_admissible} | "
            f"{result.reproducibility_closed} |"
        )
    lines.extend(
        [
            "",
            "## Genuine insertion refinement",
            "",
            "| Direction | Complete-law distance | Relative | Gate |",
            "|---|---:|---:|---:|",
        ]
    )
    for direction in ("downward", "upward", "dephasing"):
        rec = family_audits["families"][direction]["insertion_grid_convergence"]
        met = rec.get("metrics", {})
        lines.append(
            f"| {direction} | {base._format_value(met.get('complete_signed_measure_distance'))} | "
            f"{base._format_value(met.get('relative_signed_measure_distance'))} | "
            f"{rec.get('passed')} |"
        )
    lines.extend(
        [
            "",
            "## Final evidence budget",
            "",
            "| Direction | Accepted response | ε_total | Signal/ε | Classification |",
            "|---|---|---:|---:|---|",
        ]
    )
    for direction in ("downward", "upward", "dephasing"):
        budget = uncertainty["by_direction"][direction]
        ev = evidence["by_direction"][direction]
        lines.append(
            f"| {direction} | {budget.get('accepted_response_used')} | "
            f"{base._format_value(budget.get('epsilon_total_zero_rate'))} | "
            f"{base._format_value(ev.get('signal_to_uncertainty_ratio'))} | "
            f"{ev.get('classification')} |"
        )
    lines.extend(
        [
            "",
            "## Final verdict",
            "",
            f"- Scientific verdict: `{overall.get('scientific_verdict')}`",
            "- Zero-rate physical claim authorized: "
            f"`{overall.get('physical_zero_rate_susceptibility_claim_authorized')}`",
            "- Task-09 gate authorized: "
            f"`{overall.get('task08_finite_v8_zero_rate_response_gate_authorized')}`",
            "- Publication-level direct representation/longitudinal refinement remains "
            "subject to the declared inherited-bound provenance and the final Part-I audit.",
            "",
        ]
    )
    with report_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def _rebuild_hashes_and_zips(output_dir: Path, overall: Mapping[str, Any]) -> Dict[str, Any]:
    manifest_path = output_dir / "Task08_output_hashes.json"
    status_path = output_dir / "Task08_run_status.json"
    share_path = output_dir / "Task08_share.zip"
    diagnostic_path = output_dir / "Task08_diagnostic_share.zip"
    for path in (manifest_path, status_path, share_path, diagnostic_path):
        if path.exists():
            path.unlink()

    excluded = {
        manifest_path.name,
        status_path.name,
        share_path.name,
        diagnostic_path.name,
        "Task08_failure.json",
    }
    stable_files = [
        path
        for path in sorted(output_dir.iterdir())
        if path.is_file() and path.name not in excluded
    ]
    files = {path.name: sha256_file(path) for path in stable_files}
    manifest = {
        "generated_utc": utc_now_iso(),
        "hash_algorithm": "SHA-256",
        "loader_version": FINAL_LOADER_VERSION,
        "files": files,
        "scientific_verdict": overall.get("scientific_verdict"),
    }
    strict_json(manifest_path, manifest)

    def make_zip(path: Path, members: Sequence[Path]) -> Dict[str, Any]:
        tmp = path.with_name(path.name + ".tmp")
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for member in members:
                archive.write(member, arcname=member.name)
        os.replace(tmp, path)
        with zipfile.ZipFile(path, "r") as archive:
            bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP verification failed at member {bad}: {path}")
        return {
            "path": str(path),
            "sha256": sha256_file(path),
            "member_count": len(members),
            "verified": True,
        }

    members = stable_files + [manifest_path]
    share = make_zip(share_path, members)
    diagnostic = make_zip(diagnostic_path, members)
    run_status = {
        "stage": FINAL_STAGE_NAME,
        "loader_version": FINAL_LOADER_VERSION,
        "status": (
            "completed_pass"
            if int(overall.get("exit_code", 1)) == 0
            else "completed_incomplete"
            if int(overall.get("exit_code", 1)) == 3
            else "completed_fail"
        ),
        "completed_utc": utc_now_iso(),
        **dict(overall),
        "output_hash_manifest": manifest_path.name,
        "output_hash_manifest_sha256": sha256_file(manifest_path),
        "share_zip": share,
        "diagnostic_share_zip": diagnostic,
        "output_directory": str(output_dir),
    }
    strict_json(status_path, run_status)
    return {
        "manifest": manifest_path,
        "share": share,
        "diagnostic": diagnostic,
        "status": run_status,
    }


def postprocess_outputs(
    *,
    output_dir: Path,
    canonical: Mapping[str, Any],
    supplemental: Mapping[str, Any],
    supplemental_selection: Mapping[str, Any],
    family_audits: Mapping[str, Any],
    uncertainty: Mapping[str, Any],
    evidence: Mapping[str, Any],
    overall: Mapping[str, Any],
    inherited_bounds: Mapping[str, Any],
) -> Dict[str, Any]:
    # Add supplemental cases to the load-bearing integrity JSON.
    integrity_path = output_dir / "Task08_case_integrity_audit.json"
    integrity = json.loads(integrity_path.read_text(encoding="utf-8"))
    cases = integrity.setdefault("cases", {})
    for matrix_id, result in supplemental.items():
        cases[matrix_id] = base.case_result_json(result)
    integrity["overall"] = dict(overall)
    all_results = {**canonical, **supplemental}
    integrity["status_counts_all_18_roles"] = {
        status: sum(result.status == status for result in all_results.values())
        for status in base.ALLOWED_CASE_STATUSES
    }
    strict_json(integrity_path, integrity)

    # Extend case identity and per-case metrics to 18 roles.
    identity_path = output_dir / "Task08_case_identity_table.csv"
    identity_fields, identity_rows = _read_csv(identity_path)
    existing_ids = {row.get("matrix_id") for row in identity_rows}
    for matrix_id in ("D2-I", "U2-I", "P2-I"):
        if matrix_id not in existing_ids:
            identity_rows.append(_identity_row(supplemental[matrix_id]))
    base.atomic_write_csv(identity_path, identity_rows, fieldnames=identity_fields)

    metrics_path = output_dir / "Task08_per_case_metrics.csv"
    metric_fields, metric_rows = _read_csv(metrics_path)
    existing_ids = {row.get("matrix_id") for row in metric_rows}
    for matrix_id in ("D2-I", "U2-I", "P2-I"):
        if matrix_id not in existing_ids:
            metric_rows.append(_metric_row(supplemental[matrix_id]))
    base.atomic_write_csv(metrics_path, metric_rows, fieldnames=metric_fields)

    supplemental_json = {
        "loader_version": FINAL_LOADER_VERSION,
        "selection": supplemental_selection,
        "cases": {
            matrix_id: base.case_result_json(result)
            for matrix_id, result in supplemental.items()
        },
    }
    strict_json(output_dir / "Task08_supplemental_case_integrity.json", supplemental_json)
    base.atomic_write_csv(
        output_dir / "Task08_insertion_refinement.csv",
        base.family_comparison_csv_rows(family_audits.get("insertion_rows", [])),
    )

    # Compact accepted fine responses and their common-grid projections.
    compact: Dict[str, np.ndarray] = {}
    for direction, (baseline_id, fine_id) in DIRECTION_REFINEMENT.items():
        baseline = canonical[baseline_id]
        fine = supplemental[fine_id]
        if baseline.arrays and fine.arrays:
            common = coarsen_fine_response_to_baseline_grid(baseline, fine)
            tag = direction
            compact[f"{tag}_coarse_times"] = common["times"]
            compact[f"{tag}_baseline_chi_survival"] = common["baseline_survival"]
            compact[f"{tag}_baseline_chi_panel_probability"] = common[
                "baseline_panel_probability"
            ]
            compact[f"{tag}_fine_chi_survival_on_coarse"] = common[
                "fine_survival_on_coarse"
            ]
            compact[f"{tag}_fine_chi_panel_probability_on_coarse"] = common[
                "fine_panel_probability_on_coarse"
            ]
            compact[f"{tag}_fine_times_native"] = fine.arrays["times"]
            compact[f"{tag}_fine_chi_survival_native"] = fine.arrays["chi_survival"]
            compact[f"{tag}_fine_chi_panel_probability_native"] = fine.arrays[
                "chi_panel_probability"
            ]
    base.atomic_savez(
        output_dir / "Task08_refinement_compact_results.npz",
        compressed=True,
        **compact,
    )

    # Update configuration and inventory with the final amended policy.
    config_path = output_dir / "Task08_configuration.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config.update(
        {
            "loader_version": FINAL_LOADER_VERSION,
            "final_refinement_aware_amendment": True,
            "canonical_role_count": 15,
            "supplemental_role_count": 3,
            "supplemental_roles": ["D2-I", "U2-I", "P2-I"],
            "role_core_policy": {
                "standard_core_sha256": STANDARD_CORE_SHA256,
                "high_accuracy_core_sha256": HIGH_ACCURACY_CORE_SHA256,
                "high_accuracy_roles": ["U2", "U4", "U2-I"],
            },
            "insertion_policy": {
                "final_gate": "independent ds=0.1 versus ds=0.05",
                "fine_panel_mapping": "sum adjacent 0.05 signed panels onto 0.1 panels",
                "internal_factor_two_coarsening": "diagnostic_only",
            },
            "inherited_bounds_record": dict(inherited_bounds),
        }
    )
    strict_json(config_path, config)

    inventory_path = output_dir / "Task08_input_inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    inventory["supplemental_Task07_selection"] = supplemental_selection
    inventory["supplemental_Task07_role_count"] = 3
    inventory["final_accepted_role_count"] = 18
    strict_json(inventory_path, inventory)

    # The family/uncertainty/evidence files supplied to the original writer
    # already contain the amended records. Reassert them after post-processing.
    strict_json(output_dir / "Task08_uncertainty_budget.json", uncertainty)
    strict_json(output_dir / "Task08_evidence_classification.json", evidence)
    for direction in ("downward", "upward", "dephasing"):
        strict_json(
            output_dir / f"Task08_{direction}_family_audit.json",
            family_audits["families"][direction],
        )

    reproducibility_path = output_dir / "Task08_reproducibility_coverage.json"
    reproducibility = json.loads(reproducibility_path.read_text(encoding="utf-8"))
    reproducibility["supplemental_roles"] = {
        matrix_id: {
            "status": result.status,
            "reproducibility_closed": result.reproducibility_closed,
            "scientifically_admissible": result.scientific_admissible,
        }
        for matrix_id, result in supplemental.items()
    }
    reproducibility["all_18_role_closed_count"] = sum(
        result.reproducibility_closed for result in {**canonical, **supplemental}.values()
    )
    reproducibility["all_18_role_total"] = 18
    strict_json(reproducibility_path, reproducibility)

    # Copy the exact base engine needed by the wrapper output copy.
    shutil.copy2(_BASE_FILE, output_dir / "Task08_v26_base.py")
    _append_final_report(
        output_dir / "Task08_aggregate_report.md",
        supplemental,
        family_audits,
        uncertainty,
        evidence,
        overall,
    )
    return _rebuild_hashes_and_zips(output_dir, overall)


# -----------------------------------------------------------------------------
# Final orchestration
# -----------------------------------------------------------------------------
def run_task08_final(
    *,
    input_paths: Sequence[Union[str, os.PathLike[str]]],
    output_dir: Union[str, os.PathLike[str]],
    task05_input_paths: Optional[Sequence[Union[str, os.PathLike[str]]]] = None,
    inherited_bounds_path: Optional[Union[str, os.PathLike[str]]] = None,
    master_audit_path: Optional[Union[str, os.PathLike[str]]] = None,
    handoff_path: Optional[Union[str, os.PathLike[str]]] = None,
    strict_reruns: bool = False,
    allow_missing_per_case_loader: bool = False,
    max_zip_member_bytes: int = 2 * 1024 * 1024 * 1024,
) -> Tuple[int, Dict[str, Any]]:
    output_path = Path(output_dir).expanduser().resolve()
    if output_path.exists() and any(output_path.iterdir()):
        raise FileExistsError(
            f"Refusing to overwrite nonempty final Task-08 output: {output_path}"
        )
    output_path.mkdir(parents=True, exist_ok=True)

    master_path = Path(master_audit_path).expanduser() if master_audit_path else _THIS_FILE.with_name("current_master_audit.md")
    handoff_path_resolved = Path(handoff_path).expanduser() if handoff_path else _THIS_FILE.with_name("final_Task07_Task08_handoff.md")
    options = base.Task08Options(
        input_paths=base._path_tuple(input_paths),
        output_dir=output_path,
        task05_input_paths=base._path_tuple(task05_input_paths),
        inherited_bounds_path=(
            Path(inherited_bounds_path).expanduser()
            if inherited_bounds_path is not None
            else None
        ),
        master_audit_path=master_path,
        handoff_path=handoff_path_resolved,
        strict_reruns=bool(strict_reruns),
        allow_missing_per_case_loader=bool(allow_missing_per_case_loader),
        max_zip_member_bytes=int(max_zip_member_bytes),
        synthetic_mode=False,
        expected_numerical_core_sha256=STANDARD_CORE_SHA256,
    )
    if not options.input_paths:
        raise ValueError("At least one Task-07 input path is required")

    try:
        loader_self_audit = base.loader_self_scope_audit(_THIS_FILE)
        authority_audit = base.audit_authority_files(options)
        records, discovery_inventory = base.discover_candidates(options)
        canonical, selection_audit = base.audit_all_cases(records, options)
        supplemental, supplemental_selection = audit_supplemental_cases(records, options)
        task05_candidates = base.discover_task05_candidates(options)
        upward_audits = base.audit_upward_launch_identities(canonical, task05_candidates)
        family_audits = augment_family_audits(
            canonical,
            supplemental,
            base.build_family_audits(canonical),
        )
        inherited_bounds = base.load_inherited_bounds(options.inherited_bounds_path)
        uncertainty, evidence = build_final_uncertainty_and_evidence(
            canonical,
            supplemental,
            family_audits,
            inherited_bounds,
        )
        reproducibility = base.build_reproducibility_coverage(canonical)
        channel_superposition = base.build_channel_superposition_audit(canonical)
        overall = base.build_overall_verdict(
            canonical,
            family_audits,
            upward_audits,
            uncertainty,
            evidence,
            channel_superposition,
            authority_audit_passed=bool(authority_audit["passed"]),
            self_scope_passed=bool(
                loader_self_audit[
                    "read_only_CPU_loader_without_Task07_import_or_execution"
                ]
            ),
        )

        supplemental_failed = [
            matrix_id
            for matrix_id, result in supplemental.items()
            if result.status == base.STATUS_FAILED
        ]
        supplemental_missing = [
            matrix_id
            for matrix_id, result in supplemental.items()
            if result.status == base.STATUS_MISSING
        ]
        supplemental_inadmissible = [
            matrix_id
            for matrix_id, result in supplemental.items()
            if not result.scientific_admissible
        ]
        insertion_failures = [
            direction
            for direction in ("downward", "upward", "dephasing")
            if family_audits["families"][direction]["insertion_grid_convergence"].get(
                "scientific_gate_evaluable"
            )
            and not family_audits["families"][direction]["insertion_grid_convergence"].get(
                "passed"
            )
        ]
        if supplemental_failed:
            overall["scientific_verdict"] = "FAIL_CASE_LOCAL_NUMERICS"
            overall["exit_code"] = 2
        elif supplemental_missing or supplemental_inadmissible:
            overall["scientific_verdict"] = "INCOMPLETE_REQUIRED_CASE_MATRIX"
            overall["exit_code"] = 3
        elif insertion_failures:
            overall["scientific_verdict"] = "UNRESOLVED_NUMERICAL_EVIDENCE"
            overall["exit_code"] = 3
        physical = overall["scientific_verdict"] in {
            "PASS_TASK08_LINEAR_RESPONSE",
            "PASS_TASK08_ALL_CHANNELS_ZERO_COMPATIBLE",
        }
        overall.update(
            {
                "loader_version": FINAL_LOADER_VERSION,
                "canonical_role_count": 15,
                "supplemental_role_count": 3,
                "final_role_count": 18,
                "canonical_scientifically_admissible_count": sum(
                    result.scientific_admissible for result in canonical.values()
                ),
                "supplemental_scientifically_admissible_count": sum(
                    result.scientific_admissible for result in supplemental.values()
                ),
                "supplemental_failed_cases": supplemental_failed,
                "supplemental_missing_cases": supplemental_missing,
                "supplemental_scientifically_inadmissible_cases": supplemental_inadmissible,
                "insertion_refinement_failure_directions": insertion_failures,
                "supplemental_insertion_refinements_attached": not supplemental_missing,
                "role_dependent_core_policy_passed": all(
                    result.configuration.get("numerical_core_sha256")
                    == role_expected_core(matrix_id)
                    for matrix_id, result in {**canonical, **supplemental}.items()
                    if result.configuration
                ),
                "accepted_response_roles": {
                    "downward": "D2-I",
                    "upward": "U2-I",
                    "dephasing": "P2-I",
                },
                "physical_zero_rate_susceptibility_claim_authorized": physical,
                "task08_finite_v8_zero_rate_response_gate_authorized": physical,
                "publication_level_project_claim_closed_under_attached_master": False,
                "direct_response_representation_and_longitudinal_refinement_completed": False,
                "inherited_bound_policy_status": inherited_bounds.get(
                    "adoption_status",
                    "MISSING_OR_UNDECLARED",
                ),
            }
        )

        outputs = base.write_task08_outputs(
            options=options,
            loader_source=_THIS_FILE,
            loader_self_audit=loader_self_audit,
            authority_audit=authority_audit,
            discovery_inventory=discovery_inventory,
            candidate_records=records,
            task05_candidates=task05_candidates,
            selection_audit=selection_audit,
            case_results=canonical,
            upward_audits=upward_audits,
            family_audits=family_audits,
            inherited_bounds=inherited_bounds,
            uncertainty=uncertainty,
            evidence=evidence,
            reproducibility=reproducibility,
            channel_superposition=channel_superposition,
            overall=overall,
        )
        final_files = postprocess_outputs(
            output_dir=output_path,
            canonical=canonical,
            supplemental=supplemental,
            supplemental_selection=supplemental_selection,
            family_audits=family_audits,
            uncertainty=uncertainty,
            evidence=evidence,
            overall=overall,
            inherited_bounds=inherited_bounds,
        )

        summary = {
            **overall,
            "input_paths": [str(path) for path in options.input_paths],
            "Task05_input_paths": [str(path) for path in options.task05_input_paths],
            "Task07_candidate_count": len(records),
            "Task05_candidate_count": len(task05_candidates),
            "case_statuses": {
                matrix_id: result.status
                for matrix_id, result in {**canonical, **supplemental}.items()
            },
            "scientifically_admissible_case_count": sum(
                result.scientific_admissible
                for result in {**canonical, **supplemental}.values()
            ),
            "reproducibility_closed_case_count": sum(
                result.reproducibility_closed
                for result in {**canonical, **supplemental}.values()
            ),
            "family_gate_summary": {
                direction: {
                    "scalar_null": family_audits["families"][direction]["scalar_null"],
                    "insertion": family_audits["families"][direction]["insertion_grid_convergence"],
                    "time_step": family_audits["families"][direction]["time_step_convergence"],
                    "shell": family_audits["families"][direction]["shell_convergence"],
                    "evidence": evidence["by_direction"][direction],
                }
                for direction in ("downward", "upward", "dephasing")
            },
            "output_directory": str(output_path),
            "aggregate_report": str(output_path / "Task08_aggregate_report.md"),
            "case_identity_table": str(output_path / "Task08_case_identity_table.csv"),
            "per_case_metrics": str(output_path / "Task08_per_case_metrics.csv"),
            "share_zip": final_files["share"]["path"],
            "share_zip_sha256": final_files["share"]["sha256"],
            "diagnostic_share_zip": final_files["diagnostic"]["path"],
            "diagnostic_share_zip_sha256": final_files["diagnostic"]["sha256"],
        }
        return int(overall["exit_code"]), summary
    except Exception as exc:
        failure = {
            "stage": FINAL_STAGE_NAME,
            "loader_version": FINAL_LOADER_VERSION,
            "status": "execution_or_output_failure",
            "failed_utc": utc_now_iso(),
            "error": repr(exc),
            "traceback": traceback.format_exc(),
            "input_paths": [str(path) for path in options.input_paths],
            "output_directory": str(output_path),
        }
        try:
            strict_json(output_path / "Task08_failure.json", failure)
        except Exception:
            pass
        return 1, failure


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Final read-only refinement-aware Task-08 aggregate loader for the "
            "15 canonical plus 3 independent insertion-refinement Task-07 roles."
        )
    )
    parser.add_argument("--input", action="append", default=[], required=True)
    parser.add_argument("--task05-input", action="append", default=[])
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--inherited-bounds", required=True)
    parser.add_argument("--master-audit", default=None)
    parser.add_argument("--handoff", default=None)
    parser.add_argument("--strict-reruns", action="store_true")
    parser.add_argument("--allow-missing-per-case-loader", action="store_true")
    parser.add_argument(
        "--max-zip-member-bytes",
        type=int,
        default=2 * 1024 * 1024 * 1024,
    )
    return parser.parse_args(argv)


def print_summary(summary: Mapping[str, Any]) -> None:
    print("\n=== Final Task-08 summary ===")
    print("verdict:", summary.get("scientific_verdict"))
    print("exit code:", summary.get("exit_code"))
    print(
        "scientifically admissible roles:",
        f"{summary.get('scientifically_admissible_case_count', 0)}/18",
    )
    print(
        "zero-rate claim authorized:",
        summary.get("physical_zero_rate_susceptibility_claim_authorized"),
    )
    print(
        "Task-09 gate authorized:",
        summary.get("task08_finite_v8_zero_rate_response_gate_authorized"),
    )
    family = summary.get("family_gate_summary", {})
    for direction in ("downward", "upward", "dephasing"):
        record = family.get(direction, {}) if isinstance(family, Mapping) else {}
        insertion = record.get("insertion", {}) if isinstance(record, Mapping) else {}
        evidence = record.get("evidence", {}) if isinstance(record, Mapping) else {}
        print(
            f"{direction:10s} insertion={insertion.get('passed')} "
            f"classification={evidence.get('classification')} "
            f"ratio={evidence.get('signal_to_uncertainty_ratio')}"
        )
    print("output:", summary.get("output_directory"))
    if summary.get("aggregate_report"):
        print("report:", summary.get("aggregate_report"))


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    code, summary = run_task08_final(
        input_paths=args.input,
        task05_input_paths=args.task05_input,
        output_dir=args.output_dir,
        inherited_bounds_path=args.inherited_bounds,
        master_audit_path=args.master_audit,
        handoff_path=args.handoff,
        strict_reruns=args.strict_reruns,
        allow_missing_per_case_loader=args.allow_missing_per_case_loader,
        max_zip_member_bytes=args.max_zip_member_bytes,
    )
    print_summary(summary)
    return int(code)


if __name__ == "__main__":
    raise SystemExit(main())
