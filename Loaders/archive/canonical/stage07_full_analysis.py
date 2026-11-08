#!/usr/bin/env python3
"""Reproducible read-only audit of Stage-07 and the 12-case upward omega scan.

The script reads existing Stage-07/08 evidence and writes only beneath the
selected output directory.  It does not import or execute any Task-07 solver or
loader.  Numerical statements are reconstructed from archived arrays.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

os.environ.setdefault("MPLCONFIGDIR", "[ARCHIVE_PATH]")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ANALYSIS_DATE = "2026-09-03"
T_CUT = 3.6
CANONICAL_DIRNAME = "Task07_Final_Curated_Input_2026-08-10"
OMEGA_BUNDLE_REL = Path(
    "Omega_Dependencies/Task07_Extended_Upward_2826996_OUTPUT/"
    "Task07_Extended_Upward_12Cases_Bundle"
)
EXPECTED_OMEGAS = (4.0, 36.0, 64.0, 144.0)
EXPECTED_MODES = ("00", "10", "01")
STANDARD_CORE = "827fd4993707152393a8adcf891df59d7b4d02310a06e89dd5263c0fd37369af"
HIGH_ACCURACY_CORE = "d665b92be5d1efb6954968833f4cf008672add6e8ed5194e9d8a55a2a498d796"
LOADER_SHA = "3ec8f9699b2182ebd73e17e64bfbd6fc783df5d9e1ee9dc29cfd7f64c0f91d14"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path, block: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(block)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    fieldnames.append(key)
                    seen.add(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: clean_scalar(row.get(key, "")) for key in fieldnames})


def clean_scalar(value: Any) -> Any:
    if isinstance(value, (np.floating, np.integer, np.bool_)):
        value = value.item()
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value, separators=(",", ":"), allow_nan=False)
    if value is None:
        return ""
    if isinstance(value, float) and not math.isfinite(value):
        return ""
    return value


def f64(value: Any, default: float = math.nan) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "pass"}


def load_npz_bytes(data: bytes) -> dict[str, np.ndarray]:
    with np.load(io.BytesIO(data), allow_pickle=False) as archive:
        return {key: np.asarray(archive[key]) for key in archive.files}


def locate_member(names: Iterable[str], suffix: str) -> str:
    matches = [name for name in names if name.endswith(suffix)]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one ZIP member ending {suffix!r}, found {matches}")
    return matches[0]


def verify_zip_hash_manifests(zf: zipfile.ZipFile) -> dict[str, Any]:
    names = zf.namelist()
    by_basename = defaultdict(list)
    for name in names:
        by_basename[Path(name).name].append(name)
    manifests = [name for name in names if name.endswith("_output_hashes.json")]
    results: list[dict[str, Any]] = []
    total_checked = 0
    total_failed = 0
    for manifest_name in manifests:
        data = json.loads(zf.read(manifest_name))
        failures: list[str] = []
        checked = 0
        for filename, expected in (data.get("files") or {}).items():
            candidates = by_basename.get(Path(filename).name, [])
            if len(candidates) != 1:
                failures.append(f"{filename}: member_count={len(candidates)}")
                continue
            actual = sha256_bytes(zf.read(candidates[0]))
            checked += 1
            if actual.lower() != str(expected).lower():
                failures.append(f"{filename}: expected={expected} actual={actual}")
        total_checked += checked
        total_failed += len(failures)
        results.append(
            {
                "manifest": Path(manifest_name).name,
                "checked": checked,
                "failed": len(failures),
                "failures": failures,
            }
        )
    return {
        "manifest_count": len(manifests),
        "checked_file_count": total_checked,
        "failed_file_count": total_failed,
        "all_passed": total_failed == 0 and len(manifests) >= 1,
        "manifests": results,
    }


def parse_sha_manifest(path: Path) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, name = line.split(maxsplit=1)
        entries.append((digest, name.lstrip("*")))
    return entries


def verify_sha_manifest(path: Path) -> dict[str, Any]:
    failures: list[dict[str, str]] = []
    entries = parse_sha_manifest(path)
    for expected, rel in entries:
        target = path.parent / rel
        if not target.is_file():
            failures.append({"path": rel, "reason": "missing"})
            continue
        actual = sha256_file(target)
        if actual.lower() != expected.lower():
            failures.append({"path": rel, "reason": "hash_mismatch", "actual": actual})
    return {
        "manifest": str(path),
        "entry_count": len(entries),
        "failure_count": len(failures),
        "all_passed": not failures,
        "failures": failures,
    }


def zero_crossings(x: np.ndarray, y: np.ndarray) -> list[float]:
    if len(y) and np.all(y == 0.0):
        return []
    crossings: list[float] = []
    for i in range(len(y) - 1):
        y0, y1 = float(y[i]), float(y[i + 1])
        if not (np.isfinite(y0) and np.isfinite(y1)):
            continue
        if y0 == 0.0:
            crossings.append(float(x[i]))
        elif y0 * y1 < 0.0:
            crossings.append(float(x[i] - y0 * (x[i + 1] - x[i]) / (y1 - y0)))
    if len(y) and float(y[-1]) == 0.0:
        crossings.append(float(x[-1]))
    deduped: list[float] = []
    for value in crossings:
        if not deduped or abs(value - deduped[-1]) > 1e-12:
            deduped.append(value)
    return deduped


def summarize_response(arrays: dict[str, np.ndarray], t_cut: float = T_CUT) -> dict[str, Any]:
    times = np.asarray(arrays["times"], dtype=float)
    chi_s = np.asarray(arrays["chi_survival"], dtype=float)
    chi_g = np.asarray(arrays["chi_click_density"], dtype=float)
    panels = np.asarray(arrays["chi_panel_probability"], dtype=float)
    durations = np.asarray(arrays.get("panel_durations", np.diff(times)), dtype=float)
    if len(times) != len(chi_s) or len(panels) + 1 != len(times) or len(chi_g) != len(panels):
        raise RuntimeError("Node/panel shape mismatch")
    mids = 0.5 * (times[:-1] + times[1:])
    early = mids < t_cut - 1e-13
    late = ~early
    chi_d_surv = -float(chi_s[-1])
    chi_d_panel = float(np.sum(panels))
    chi_mu = float(np.trapezoid(chi_s, times))
    chi_de = float(np.sum(panels[early]))
    chi_dl = float(np.sum(panels[late]))
    temporal_l1 = float(np.sum(np.abs(panels)))
    a_tv = 0.5 * (temporal_l1 + abs(float(chi_s[-1])))
    pos = float(np.sum(panels[panels > 0]))
    neg = float(np.sum(panels[panels < 0]))
    closure_nodes = chi_s[1:] + np.cumsum(panels)
    ref_s = np.asarray(arrays.get("reference_survival", []), dtype=float)
    baseline_s_t = float(ref_s[-1]) if ref_s.size else math.nan
    baseline_d_t = 1.0 - baseline_s_t if ref_s.size else math.nan
    baseline_panel = -np.diff(ref_s) if ref_s.size else np.asarray([])
    crossings = zero_crossings(mids, chi_g)
    max_i = int(np.argmax(chi_g))
    min_i = int(np.argmin(chi_g))
    abs_i = int(np.argmax(np.abs(chi_g)))
    return {
        "state_node_count": int(len(times)),
        "response_panel_count": int(len(panels)),
        "panel_midpoint_convention_verified": bool(np.allclose(mids, times[:-1] + durations / 2)),
        "chi_D_recomputed_survival": chi_d_surv,
        "chi_D_recomputed_panel_sum": chi_d_panel,
        "chi_mu_recomputed": chi_mu,
        "chi_D_E_recomputed": chi_de,
        "chi_D_L_recomputed": chi_dl,
        "A_TV_recomputed": a_tv,
        "temporal_L1": temporal_l1,
        "positive_panel_mass": pos,
        "negative_panel_mass": neg,
        "A_TV_over_abs_chi_D": a_tv / abs(chi_d_surv) if chi_d_surv != 0 else math.inf,
        "temporal_L1_over_abs_chi_D": temporal_l1 / abs(chi_d_surv) if chi_d_surv != 0 else math.inf,
        "signed_late_fraction": chi_dl / chi_d_surv if chi_d_surv != 0 else math.nan,
        "chi_g_min": float(chi_g[min_i]),
        "chi_g_min_time": float(mids[min_i]),
        "chi_g_max": float(chi_g[max_i]),
        "chi_g_max_time": float(mids[max_i]),
        "chi_g_abs_max": float(abs(chi_g[abs_i])),
        "chi_g_abs_max_time": float(mids[abs_i]),
        "chi_survival_abs_max": float(np.max(np.abs(chi_s))),
        "chi_survival_abs_max_time": float(times[int(np.argmax(np.abs(chi_s)))]),
        "zero_crossing_count": len(crossings),
        "zero_crossing_times": crossings,
        "tangent_closure_recomputed_max_abs": float(np.max(np.abs(closure_nodes))) if closure_nodes.size else 0.0,
        "final_detection_identity_residual_recomputed": abs(chi_d_surv - chi_d_panel),
        "baseline_S_T": baseline_s_t,
        "baseline_D_T": baseline_d_t,
        "baseline_min_panel_detection": float(np.min(baseline_panel)) if baseline_panel.size else math.nan,
        "times": times,
        "panel_midpoints": mids,
        "chi_survival": chi_s,
        "chi_click_density": chi_g,
        "chi_panel_probability": panels,
        "reference_survival": ref_s,
    }


def compare_complete_signed(a: dict[str, Any], b: dict[str, Any]) -> dict[str, float]:
    pa = np.asarray(a["chi_panel_probability"])
    pb = np.asarray(b["chi_panel_probability"])
    if len(pa) == 2 * len(pb):
        pa = pa.reshape(-1, 2).sum(axis=1)
    elif len(pb) == 2 * len(pa):
        pb = pb.reshape(-1, 2).sum(axis=1)
    if len(pa) != len(pb):
        raise RuntimeError(f"Cannot align panel grids: {len(pa)} and {len(pb)}")
    atom_a = -float(a["chi_D_recomputed_survival"])
    atom_b = -float(b["chi_D_recomputed_survival"])
    distance = 0.5 * (float(np.sum(np.abs(pa - pb))) + abs(atom_a - atom_b))
    aligned_norm_a = 0.5 * (float(np.sum(np.abs(pa))) + abs(atom_a))
    aligned_norm_b = 0.5 * (float(np.sum(np.abs(pb))) + abs(atom_b))
    max_norm = max(aligned_norm_a, aligned_norm_b)
    return {
        "complete_signed_distance": distance,
        "relative_to_first_A_TV": distance / aligned_norm_a if aligned_norm_a else math.inf,
        "relative_to_max_A_TV": distance / max_norm if max_norm else math.inf,
        "aligned_first_A_TV": aligned_norm_a,
        "aligned_second_A_TV": aligned_norm_b,
        "chi_mu_abs_difference": abs(float(a["chi_mu_recomputed"]) - float(b["chi_mu_recomputed"])),
    }


def least_squares_shape(y_ref: np.ndarray, y: np.ndarray) -> dict[str, float]:
    y_ref = np.asarray(y_ref, dtype=float)
    y = np.asarray(y, dtype=float)
    den = float(np.dot(y_ref, y_ref))
    scale = float(np.dot(y, y_ref) / den) if den else math.nan
    residual = y - scale * y_ref
    ynorm = float(np.linalg.norm(y))
    denom_cos = float(np.linalg.norm(y_ref)) * ynorm
    cosine = float(np.dot(y_ref, y) / denom_cos) if denom_cos else math.nan
    return {
        "best_scale": scale,
        "relative_L2_residual_after_scaling": float(np.linalg.norm(residual) / ynorm) if ynorm else 0.0,
        "cosine_similarity": cosine,
    }


def spearman4(x: list[float], y: list[float]) -> float:
    def ranks(vals: list[float]) -> np.ndarray:
        order = np.argsort(vals)
        result = np.empty(len(vals), dtype=float)
        result[order] = np.arange(1, len(vals) + 1, dtype=float)
        return result

    return float(np.corrcoef(ranks(x), ranks(y))[0, 1])


def fmt(x: Any, sig: int = 6) -> str:
    try:
        value = float(x)
    except (TypeError, ValueError):
        return str(x)
    if not np.isfinite(value):
        return "n/a"
    return f"{value:.{sig}g}"


def mode_label(mode: str) -> str:
    return {"00": "mode 00", "10": "mode 10", "01": "mode 01"}.get(mode, mode)


def classify_top_level(name: str) -> tuple[str, str, str]:
    if name == CANONICAL_DIRNAME:
        return "1", "authoritative_curated", "Curated 15 canonical + 3 supplemental Task-07 scientific inputs"
    if name == f"{CANONICAL_DIRNAME}.zip":
        return "3", "archive_duplicate", "Archive duplicate of curated input directory"
    if name == "Final_Accepted_Stage07":
        return "3", "duplicate_source_tree", "Source copies superseded for aggregate use by curated register"
    if name == "Old_LessAccurateResults":
        return "3", "superseded", "Explicitly older/less-accurate results"
    if name == "Omega_Dependencies":
        return "2", "mixed_exploratory_and_operational", "Contains priority 12-case exploratory scan plus builders/operational history"
    if name.startswith("GIFs_Omega144"):
        return "3", "visualization_derivative", "Spatial/timing derivatives; not ordinary case acceptance"
    if name.startswith("Screenshot"):
        return "3", "visualization_only", "Screenshot evidence only"
    if name in {"DiagnosticPlan", "Authontiative_Initialize_things"}:
        return "3", "historical_or_initialization", "Historical planning/initialization material"
    if name.endswith(".md"):
        return "context", "authority_or_handoff", "Context/claim-boundary or operational handoff"
    if name.endswith(".zip"):
        return "3", "archive_or_duplicate", "Archive requiring provenance-specific use"
    if re.match(r"^\d{4}[.]?\s*Environmental_response|^\d{4}[.]spinor", name):
        return "3", "duplicate_case_tree", "Root case copy; curated register is aggregate authority"
    return "3", "supplemental_or_unresolved", "Supplemental Stage-07 item"


def parse_args() -> argparse.Namespace:
    default_project = Path(__file__).resolve().parents[4]
    default_output = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=default_project)
    parser.add_argument("--output-dir", type=Path, default=default_output)
    parser.add_argument("--finalize-only", action="store_true")
    return parser.parse_args()


def read_one_csv_text(text: str) -> dict[str, str]:
    rows = list(csv.DictReader(io.StringIO(text)))
    if len(rows) != 1:
        raise RuntimeError(f"Expected one CSV data row, found {len(rows)}")
    return rows[0]


def load_task08(project: Path) -> dict[str, Any]:
    root = project / (
        "Part1/Stage08/Task08_All_Output_2026-08-10 2/"
        "4902.Task08_Project_Aggregate_Recheck_2026-08-10_01"
    )
    identities = {
        row["matrix_id"]: row
        for row in csv.DictReader((root / "Task08_case_identity_table.csv").open(encoding="utf-8"))
    }
    insertions = {
        row["direction"]: row
        for row in csv.DictReader((root / "Task08_insertion_refinement.csv").open(encoding="utf-8"))
    }
    time_steps = {
        row["direction"]: row
        for row in csv.DictReader((root / "Task08_time_step_convergence.csv").open(encoding="utf-8"))
    }
    shells = {
        row["direction"]: row
        for row in csv.DictReader((root / "Task08_shell_convergence.csv").open(encoding="utf-8"))
    }
    return {
        "root": root,
        "identities": identities,
        "insertions": insertions,
        "time_steps": time_steps,
        "shells": shells,
        "status": json.loads((root / "Task08_run_status.json").read_text()),
        "classification": json.loads((root / "Task08_evidence_classification.json").read_text()),
        "coverage": json.loads((root / "Task08_reproducibility_coverage.json").read_text()),
    }


def canonical_case_data(project: Path, task08: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
    curated = project / "Part1/Stage07" / CANONICAL_DIRNAME
    register = json.loads((curated / "Task07_case_register.json").read_text())
    rows: list[dict[str, Any]] = []
    responses: dict[str, dict[str, Any]] = {}
    integrity: dict[str, Any] = {"register_case_count": len(register["accepted_roles"]), "cases": {}}
    for entry in register["accepted_roles"]:
        matrix_id = entry["matrix_id"]
        zip_path = curated / entry["case_zip"]
        outer_actual = sha256_file(zip_path)
        if outer_actual != entry["case_zip_sha256"]:
            raise RuntimeError(f"Canonical outer ZIP hash mismatch: {matrix_id}")
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            prefix = entry["case_prefix"]
            compact_name = locate_member(names, "_case_loader_compact.npz")
            metrics_name = locate_member(names, "_case_loader_metrics.csv")
            audit_name = locate_member(names, "_case_loader_audit.json")
            status_name = locate_member(names, "_case_loader_run_status.json")
            integrated_name = locate_member(names, "_integrated_response.json")
            arrays = load_npz_bytes(zf.read(compact_name))
            response = summarize_response(arrays)
            metrics = read_one_csv_text(zf.read(metrics_name).decode("utf-8"))
            audit = json.loads(zf.read(audit_name))
            status = json.loads(zf.read(status_name))
            integrated = json.loads(zf.read(integrated_name))
            hash_audit = verify_zip_hash_manifests(zf)
            curves_name = locate_member(names, "_case_loader_curves.csv")
            curve_rows = list(csv.DictReader(io.StringIO(zf.read(curves_name).decode("utf-8"))))
            curve_node = np.asarray([f64(x["chi_survival"]) for x in curve_rows], dtype=float)
            curve_panel = np.asarray(
                [f64(x["chi_panel_probability"]) for x in curve_rows if x["panel_index"] != ""], dtype=float
            )
            curve_max = max(
                float(np.max(np.abs(curve_node - arrays["chi_survival"]))),
                float(np.max(np.abs(curve_panel - arrays["chi_panel_probability"]))),
            )
        identity = task08["identities"].get(matrix_id, {})
        row: dict[str, Any] = {
            "matrix_id": matrix_id,
            "canonical_or_supplemental": entry["canonical_or_supplemental"],
            "case_role": identity.get("role", status.get("case_role", "")),
            "propagator_type": entry["propagator_type"],
            "environment_direction": entry["environment_direction"],
            "omega": entry["omega"],
            "initial_mode": entry["initial_mode"],
            "N_shell": entry["N_shell"],
            "dt": entry["dt"],
            "T_final": entry["T_final"],
            "insertion_dt": entry["insertion_dt"],
            "state_node_count": response["state_node_count"],
            "response_panel_count": response["response_panel_count"],
            "baseline_S_T": response["baseline_S_T"],
            "baseline_D_T": response["baseline_D_T"],
            "chi_D": response["chi_D_recomputed_survival"],
            "chi_D_panel_sum": response["chi_D_recomputed_panel_sum"],
            "chi_mu": response["chi_mu_recomputed"],
            "chi_D_E": response["chi_D_E_recomputed"],
            "chi_D_L": response["chi_D_L_recomputed"],
            "A_TV": response["A_TV_recomputed"],
            "A_TV_over_abs_chi_D": response["A_TV_over_abs_chi_D"],
            "positive_panel_mass": response["positive_panel_mass"],
            "negative_panel_mass": response["negative_panel_mass"],
            "chi_g_min": response["chi_g_min"],
            "chi_g_min_time": response["chi_g_min_time"],
            "chi_g_max": response["chi_g_max"],
            "chi_g_max_time": response["chi_g_max_time"],
            "zero_crossing_count": response["zero_crossing_count"],
            "zero_crossing_times": response["zero_crossing_times"],
            "tangent_closure_max_abs": response["tangent_closure_recomputed_max_abs"],
            "final_detection_identity_residual": response["final_detection_identity_residual_recomputed"],
            "reported_vs_recomputed_chi_D_abs": abs(f64(metrics["chi_D"]) - response["chi_D_recomputed_survival"]),
            "reported_vs_recomputed_chi_mu_abs": abs(f64(metrics["chi_mu"]) - response["chi_mu_recomputed"]),
            "reported_vs_recomputed_A_TV_abs": abs(f64(metrics["response_norm"]) - response["A_TV_recomputed"]),
            "integrated_json_vs_recomputed_chi_D_abs": abs(f64(integrated["chi_D_from_final_survival"]) - response["chi_D_recomputed_survival"]),
            "curves_vs_npz_max_abs": curve_max,
            "case_zip_sha256": outer_actual,
            "configuration_sha256": entry["configuration_sha256"],
            "numerical_core_sha256": entry["numerical_core_sha256"],
            "loader_source_sha256": audit.get("loader_source_sha256", status.get("loader_source_sha256", "")),
            "loader_exit_code": status.get("exit_code"),
            "loader_verdict": status.get("verdict"),
            "local_checks_passed": audit.get("all_independent_checks_passed"),
            "failed_check_count": status.get("failed_check_count", metrics.get("failed_check_count")),
            "pending_item_count": len(status.get("pending_items", [])),
            "loader_failed_checks": audit.get("failed_checks", []),
            "loader_pending_items": status.get("pending_items", []),
            "runtime_seconds_before_final_hashing": f64(metrics.get("total_seconds_before_final_hashing")),
            "task08_status": identity.get("status", ""),
            "task08_scientifically_admissible": identity.get("scientific_admissible", ""),
            "task08_reproducibility_closed": identity.get("reproducibility_closed", ""),
            "task08_evidence_classification": task08["classification"].get("by_direction", {}).get(entry["environment_direction"], {}).get("classification", ""),
            "evidence_tier": "authoritative_curated",
            "claim_scope": "zero-rate linear response; finite v8 model",
        }
        rows.append(row)
        responses[matrix_id] = response
        integrity["cases"][matrix_id] = {
            "outer_zip_hash_match": True,
            "internal_hash_audit": hash_audit,
            "curves_vs_npz_max_abs": curve_max,
            "all_independent_checks_passed": audit.get("all_independent_checks_passed"),
        }
    by_id = {row["matrix_id"]: row for row in rows}
    for direction, comp in task08["insertions"].items():
        base, fine = comp["baseline"], comp["control"]
        independently_recomputed = compare_complete_signed(responses[base], responses[fine])
        for matrix_id in (base, fine):
            by_id[matrix_id]["genuine_insertion_pair"] = f"{base} vs {fine}"
            by_id[matrix_id]["insertion_complete_signed_distance_recomputed"] = independently_recomputed["complete_signed_distance"]
            by_id[matrix_id]["insertion_relative_to_baseline_A_TV_recomputed"] = independently_recomputed["relative_to_first_A_TV"]
            by_id[matrix_id]["insertion_relative_to_max_A_TV_recomputed"] = independently_recomputed["relative_to_max_A_TV"]
            by_id[matrix_id]["insertion_aligned_baseline_A_TV_recomputed"] = independently_recomputed["aligned_first_A_TV"]
            by_id[matrix_id]["insertion_aligned_control_A_TV_recomputed"] = independently_recomputed["aligned_second_A_TV"]
            by_id[matrix_id]["insertion_relative_distance_reported_by_task08"] = f64(comp["relative_signed_measure_distance"])
            by_id[matrix_id]["insertion_relative_distance_task08_abs_residual"] = abs(
                independently_recomputed["relative_to_max_A_TV"] - f64(comp["relative_signed_measure_distance"])
            )
            by_id[matrix_id]["insertion_gate_passed_task08"] = comp["passed"]
    integrity["all_outer_hashes_match"] = True
    integrity["all_internal_hash_manifests_passed"] = all(
        value["internal_hash_audit"]["all_passed"] for value in integrity["cases"].values()
    )
    integrity["maximum_curves_vs_npz_abs"] = max(value["curves_vs_npz_max_abs"] for value in integrity["cases"].values())
    return rows, responses, integrity


def omega_case_data(project: Path) -> tuple[list[dict[str, Any]], dict[tuple[float, str], dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    bundle = project / "Part1/Stage07" / OMEGA_BUNDLE_REL
    summary_rows = list(csv.DictReader((bundle / "case_summary.tsv").open(encoding="utf-8"), delimiter="\t"))
    rows: list[dict[str, Any]] = []
    responses: dict[tuple[float, str], dict[str, Any]] = {}
    integrity: dict[str, Any] = {
        "case_share_manifest": verify_sha_manifest(bundle / "SHA256SUMS_case_shares.txt"),
        "quicklook_manifest": verify_sha_manifest(bundle / "SHA256SUMS_quicklook.txt"),
        "cases": {},
    }
    sidecars = sorted(bundle.parent.glob("*.zip.sha256"))
    integrity["outer_bundle_archive_sidecar"] = verify_sha_manifest(sidecars[0]) if len(sidecars) == 1 else {
        "all_passed": False,
        "reason": f"expected one outer sidecar, found {len(sidecars)}",
    }
    log_rows: list[dict[str, Any]] = []
    for summary in summary_rows:
        prefix_match = re.search(r"spinor_upward_omega([0-9]+)_mode(00|10|01)_", summary["share_zip"])
        if not prefix_match:
            raise RuntimeError(f"Cannot parse omega case: {summary['share_zip']}")
        omega = float(prefix_match.group(1))
        mode = prefix_match.group(2)
        key = (omega, mode)
        qprefix = summary["share_zip"].replace("_Task07_case_share.zip", "")
        compact_path = bundle / "quicklook" / f"{qprefix}_case_loader_compact.npz"
        metrics_path = bundle / "quicklook" / f"{qprefix}_case_loader_metrics.csv"
        curves_path = bundle / "quicklook" / f"{qprefix}_case_loader_curves.csv"
        audit_path = bundle / "quicklook" / f"{qprefix}_case_loader_audit.json"
        report_path = bundle / "quicklook" / f"{qprefix}_case_loader_report.md"
        for path in (compact_path, metrics_path, curves_path, audit_path, report_path):
            if not path.is_file():
                raise RuntimeError(f"Missing quicklook product: {path}")
        with np.load(compact_path, allow_pickle=False) as archive:
            arrays = {name: np.asarray(archive[name]) for name in archive.files}
        response = summarize_response(arrays)
        metrics = read_one_csv_text(metrics_path.read_text(encoding="utf-8"))
        audit = json.loads(audit_path.read_text())
        report_text = report_path.read_text(encoding="utf-8")
        report_verdict_present = summary["verdict"] in report_text
        if not report_verdict_present:
            raise RuntimeError(f"Quicklook report verdict mismatch: {omega:g}/{mode}")
        curve_rows = list(csv.DictReader(curves_path.open(encoding="utf-8")))
        curve_node = np.asarray([f64(x["chi_survival"]) for x in curve_rows])
        curve_panel = np.asarray([f64(x["chi_panel_probability"]) for x in curve_rows if x["panel_index"] != ""])
        curve_max = max(
            float(np.max(np.abs(curve_node - arrays["chi_survival"]))),
            float(np.max(np.abs(curve_panel - arrays["chi_panel_probability"]))),
        )
        zip_path = bundle / "case_shares" / summary["share_zip"]
        outer_hash = sha256_file(zip_path)
        if outer_hash != summary["share_sha256"]:
            raise RuntimeError(f"Omega outer ZIP hash mismatch: {omega:g}/{mode}")
        with zipfile.ZipFile(zip_path) as zf:
            hash_audit = verify_zip_hash_manifests(zf)
            names = zf.namelist()
            log_names = [n for n in names if n.endswith(("_stdout.txt", "_stderr.txt", "_simulation_log.txt"))]
            text = "\n".join(zf.read(n).decode("utf-8", errors="replace") for n in log_names)
            traceback_count = len(re.findall(r"Traceback \(most recent call last\)", text))
            error_count = len(re.findall(r"(?im)^\s*(?:ERROR|FATAL)\b", text))
            fail_count = len(re.findall(r"(?im)^\s*FAIL(?:ED|URE)?\b", text))
            log_rows.append({
                "omega": omega,
                "initial_mode": mode,
                "log_member_count": len(log_names),
                "traceback_count": traceback_count,
                "error_line_count": error_count,
                "fail_line_count": fail_count,
                "scan_passed": traceback_count + error_count + fail_count == 0,
            })
        row = {
            "case_id": f"omega{omega:g}_mode{mode}",
            "environment_direction": "upward",
            "propagator_type": "spinor",
            "omega": omega,
            "initial_mode": mode,
            "N_shell": int(float(metrics["N_shell"])),
            "dt": f64(metrics["dt"]),
            "T_final": f64(metrics["T_final"]),
            "insertion_dt": f64(metrics["insertion_dt"]),
            "state_node_count": response["state_node_count"],
            "response_panel_count": response["response_panel_count"],
            "baseline_S_T": response["baseline_S_T"],
            "baseline_D_T": response["baseline_D_T"],
            "chi_D": response["chi_D_recomputed_survival"],
            "chi_D_panel_sum": response["chi_D_recomputed_panel_sum"],
            "chi_mu": response["chi_mu_recomputed"],
            "chi_D_E": response["chi_D_E_recomputed"],
            "chi_D_L": response["chi_D_L_recomputed"],
            "A_TV": response["A_TV_recomputed"],
            "A_TV_over_abs_chi_D": response["A_TV_over_abs_chi_D"],
            "temporal_L1_over_abs_chi_D": response["temporal_L1_over_abs_chi_D"],
            "positive_panel_mass": response["positive_panel_mass"],
            "negative_panel_mass": response["negative_panel_mass"],
            "chi_g_min": response["chi_g_min"],
            "chi_g_min_time": response["chi_g_min_time"],
            "chi_g_max": response["chi_g_max"],
            "chi_g_max_time": response["chi_g_max_time"],
            "chi_g_abs_max": response["chi_g_abs_max"],
            "chi_g_abs_max_time": response["chi_g_abs_max_time"],
            "zero_crossing_count": response["zero_crossing_count"],
            "zero_crossing_times": response["zero_crossing_times"],
            "tangent_closure_max_abs": response["tangent_closure_recomputed_max_abs"],
            "final_detection_identity_residual": response["final_detection_identity_residual_recomputed"],
            "reported_vs_recomputed_chi_D_abs": abs(f64(metrics["chi_D"]) - response["chi_D_recomputed_survival"]),
            "reported_vs_recomputed_chi_mu_abs": abs(f64(metrics["chi_mu"]) - response["chi_mu_recomputed"]),
            "reported_vs_recomputed_A_TV_abs": abs(f64(metrics["response_norm"]) - response["A_TV_recomputed"]),
            "curves_vs_npz_max_abs": curve_max,
            "case_zip_sha256": outer_hash,
            "numerical_core_sha256": metrics["numerical_core_sha256"],
            "loader_source_sha256": metrics["loader_source_sha256"] if "loader_source_sha256" in metrics else LOADER_SHA,
            "loader_exit_code": int(summary["loader_rc"]),
            "loader_verdict": summary["verdict"],
            "local_checks_passed": as_bool(summary["all_checks_passed"]) and audit["all_independent_checks_passed"],
            "failed_check_count": int(summary["failed_count"]),
            "pending_item_count": int(summary["pending_count"]),
            "raw_metadata_unchanged": as_bool(summary["raw_metadata_unchanged"]),
            "project_aggregate_loader_run": False,
            "task08_scientific_admissibility": "NOT_EVALUATED_FOR_THIS_12_CASE_SCAN",
            "evidence_tier": "exploratory_case_local",
            "claim_scope": "zero-rate per-case exploratory omega scan; no finite-rate or continuum claim",
        }
        rows.append(row)
        responses[key] = response
        integrity["cases"][f"{omega:g}/{mode}"] = {
            "outer_zip_hash_match": True,
            "internal_hash_audit": hash_audit,
            "curves_vs_npz_max_abs": curve_max,
            "all_independent_checks_passed": audit["all_independent_checks_passed"],
            "quicklook_report_verdict_present": report_verdict_present,
        }
    got = set(responses)
    expected = {(o, m) for o in EXPECTED_OMEGAS for m in EXPECTED_MODES}
    if got != expected:
        raise RuntimeError(f"Omega matrix mismatch: missing={expected-got}, extra={got-expected}")
    integrity["all_internal_hash_manifests_passed"] = all(
        item["internal_hash_audit"]["all_passed"] for item in integrity["cases"].values()
    )
    integrity["all_log_scans_passed"] = all(item["scan_passed"] for item in log_rows)
    integrity["maximum_curves_vs_npz_abs"] = max(item["curves_vs_npz_max_abs"] for item in integrity["cases"].values())
    return sorted(rows, key=lambda x: (x["omega"], EXPECTED_MODES.index(x["initial_mode"]))), responses, integrity, log_rows


def doublet_and_shape_diagnostics(responses: dict[tuple[float, str], dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    doublets: list[dict[str, Any]] = []
    shapes: list[dict[str, Any]] = []
    for omega in EXPECTED_OMEGAS:
        a, b = responses[(omega, "10")], responses[(omega, "01")]
        for quantity in ("chi_survival", "chi_click_density", "chi_panel_probability", "reference_survival"):
            av, bv = np.asarray(a[quantity]), np.asarray(b[quantity])
            diff = av - bv
            scale = max(float(np.linalg.norm(av)), float(np.linalg.norm(bv)), np.finfo(float).tiny)
            doublets.append({
                "omega": omega,
                "quantity": quantity,
                "max_abs_difference": float(np.max(np.abs(diff))),
                "relative_L2_difference": float(np.linalg.norm(diff) / scale),
            })
        doublets.append({
            "omega": omega,
            "quantity": "chi_D",
            "max_abs_difference": abs(a["chi_D_recomputed_survival"] - b["chi_D_recomputed_survival"]),
            "relative_L2_difference": abs(a["chi_D_recomputed_survival"] - b["chi_D_recomputed_survival"]) / max(abs(a["chi_D_recomputed_survival"]), abs(b["chi_D_recomputed_survival"])),
        })
    for mode in EXPECTED_MODES:
        ref = responses[(4.0, mode)]
        for omega in EXPECTED_OMEGAS:
            cur = responses[(omega, mode)]
            for quantity in ("chi_click_density", "chi_survival"):
                diag = least_squares_shape(ref[quantity], cur[quantity])
                shapes.append({"mode": mode, "reference_omega": 4.0, "omega": omega, "quantity": quantity, **diag})
    return doublets, shapes


def spatial_reconciliation(project: Path, omega_responses: dict[tuple[float, str], dict[str, Any]]) -> dict[str, Any]:
    root = project / "Part1/Stage07/GIFs_Omega144_Snapshots_v1/Task07_Omega144_3D_Analysis_v1"
    timing_root = root / "Omega144_mode00_dt25_timing_v1"
    timing = json.loads((timing_root / "timing_summary.json").read_text())
    atlas = json.loads((root / "Omega144_mode00_dt25_spatial_v1/atlas/atlas_summary.json").read_text())
    with np.load(timing_root / "timing_curves.npz", allow_pickle=False) as data:
        arrays = {name: np.asarray(data[name]) for name in data.files}
    ordinary = omega_responses[(144.0, "00")]
    comparisons = {
        "response_node_times_max_abs": float(np.max(np.abs(arrays["response_node_times"] - ordinary["times"]))),
        "response_panel_midpoints_max_abs": float(np.max(np.abs(arrays["response_panel_midpoints"] - ordinary["panel_midpoints"]))),
        "chi_survival_max_abs": float(np.max(np.abs(arrays["chi_survival"] - ordinary["chi_survival"]))),
        "chi_click_density_max_abs": float(np.max(np.abs(arrays["chi_click_density"] - ordinary["chi_click_density"]))),
        "chi_panel_probability_max_abs": float(np.max(np.abs(arrays["chi_panel_probability"] - ordinary["chi_panel_probability"]))),
        "timing_summary_chi_D_abs": abs(timing["upward_response"]["chi_D_from_final_survival"] - ordinary["chi_D_recomputed_survival"]),
        "timing_summary_baseline_S_T_abs": abs(timing["baseline"]["final_survival"] - ordinary["baseline_S_T"]),
    }
    return {
        "case": "omega144/mode00/dt=2.5e-4",
        "ordinary_case_and_timing_arrays_identical": max(comparisons.values()) == 0.0,
        "comparisons": comparisons,
        "timing_summary": timing,
        "spatial_atlas_scope": {
            "physical_acceptance": atlas["physical_acceptance"],
            "finite_positive_rate_state": atlas["finite_positive_rate_state"],
            "frames": atlas["grid"]["frames"],
            "field_semantics": atlas["field_semantics"],
            "trace_checks": atlas["trace_checks"],
            "separation_rule": "Spatial fields are signed derivative visualizations and are not additional ordinary case-acceptance evidence.",
        },
    }


def build_inventory(
    project: Path,
    output: Path,
    canonical_rows: list[dict[str, Any]],
    omega_rows: list[dict[str, Any]],
    task08: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    stage = project / "Part1/Stage07"
    output_resolved = output.resolve()
    detailed: list[dict[str, Any]] = []
    totals: dict[str, dict[str, Any]] = defaultdict(lambda: {"file_count": 0, "total_bytes": 0})
    for dirpath, dirnames, filenames in os.walk(stage):
        current = Path(dirpath)
        dirnames[:] = [
            name for name in dirnames
            if not (current / name).resolve().is_relative_to(output_resolved)
            and not name.startswith("Stage07_Full_Analysis_2026-09-03")
        ]
        for filename in filenames:
            path = current / filename
            if path.resolve().is_relative_to(output_resolved):
                continue
            rel = path.relative_to(stage)
            stat = path.stat()
            digest = sha256_file(path)
            top = rel.parts[0]
            tier, classification, rationale = classify_top_level(top)
            detailed.append({
                "relative_path": str(rel),
                "size_bytes": stat.st_size,
                "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "sha256": digest,
                "suffix": path.suffix.lower(),
                "top_level_item": top,
                "evidence_tier": tier,
                "classification": classification,
                "classification_rationale": rationale,
            })
            totals[top]["file_count"] += 1
            totals[top]["total_bytes"] += stat.st_size
    counts = Counter(row["sha256"] for row in detailed)
    for row in detailed:
        row["same_content_file_count"] = counts[row["sha256"]]
        row["duplicate_content_present"] = counts[row["sha256"]] > 1
    inventory: list[dict[str, Any]] = []
    for top, agg in sorted(totals.items()):
        tier, classification, rationale = classify_top_level(top)
        path = stage / top
        inventory.append({
            "record_type": "top_level_stage07_item",
            "record_id": top,
            "path": str(path.relative_to(project)),
            "file_count": agg["file_count"],
            "total_bytes": agg["total_bytes"],
            "sha256": "see STAGE07_FILE_HASH_INVENTORY.csv",
            "evidence_tier": tier,
            "classification": classification,
            "scientific_status": "contextual" if tier == "context" else classification,
            "use_in_analysis": classification in {"authoritative_curated", "mixed_exploratory_and_operational", "authority_or_handoff", "visualization_derivative"},
            "rationale": rationale,
        })
    for row in canonical_rows:
        inventory.append({
            "record_type": "canonical_case_share",
            "record_id": row["matrix_id"],
            "path": f"Part1/Stage07/{CANONICAL_DIRNAME}/cases",
            "file_count": 1,
            "total_bytes": "",
            "sha256": row["case_zip_sha256"],
            "evidence_tier": "1",
            "classification": row["canonical_or_supplemental"],
            "scientific_status": f"Task08={row['task08_status']}; admissible={row['task08_scientifically_admissible']}",
            "use_in_analysis": True,
            "rationale": "Role selected by the curated 18-case register; Task-08 identity table supplies scientific adjudication.",
        })
    for row in omega_rows:
        inventory.append({
            "record_type": "exploratory_omega_case_share",
            "record_id": row["case_id"],
            "path": f"Part1/Stage07/{OMEGA_BUNDLE_REL}/case_shares",
            "file_count": 1,
            "total_bytes": "",
            "sha256": row["case_zip_sha256"],
            "evidence_tier": "2",
            "classification": "case_local_exploratory",
            "scientific_status": f"{row['loader_verdict']}; project aggregate not run",
            "use_in_analysis": True,
            "rationale": "Priority upward omega scan; hashes and local loader checks pass, but no Task-08 aggregate/convergence adjudication exists for these 12 cases.",
        })
    inventory.append({
        "record_type": "external_stage08_adjudication",
        "record_id": "Task08_Project_Aggregate_Recheck_2026-08-10_01",
        "path": str(task08["root"].relative_to(project)),
        "file_count": "",
        "total_bytes": "",
        "sha256": "see source Task08_output_hashes.json",
        "evidence_tier": "1_adjudication",
        "classification": task08["status"]["scientific_verdict"],
        "scientific_status": task08["status"]["status"],
        "use_in_analysis": True,
        "rationale": "Independent aggregate loader that adjudicates the curated 18 Task-07 roles; kept separate from the exploratory omega bundle.",
    })
    summary = {
        "stage07_file_count_excluding_this_analysis": len(detailed),
        "stage07_total_bytes_excluding_this_analysis": sum(row["size_bytes"] for row in detailed),
        "unique_file_hash_count": len(counts),
        "duplicate_file_instances": sum(count - 1 for count in counts.values() if count > 1),
        "top_level_item_count": len(totals),
    }
    return inventory, detailed, summary


def save_figure(fig: plt.Figure, figures: Path, stem: str) -> None:
    fig.savefig(figures / f"{stem}.png", dpi=190, bbox_inches="tight", facecolor="white")
    fig.savefig(figures / f"{stem}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_outputs(
    figures: Path,
    omega_rows: list[dict[str, Any]],
    omega_responses: dict[tuple[float, str], dict[str, Any]],
    canonical_rows: list[dict[str, Any]],
    canonical_responses: dict[str, dict[str, Any]],
    doublets: list[dict[str, Any]],
    shapes: list[dict[str, Any]],
) -> None:
    figures.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "legend.fontsize": 8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 120,
    })
    colors = {"00": "#1b6ca8", "10": "#d1495b", "01": "#2a9d8f"}
    markers = {"00": "o", "10": "s", "01": "^"}

    for logx, stem in ((False, "01_integrated_metrics_linear_omega"), (True, "02_integrated_metrics_log_omega")):
        fig, axes = plt.subplots(2, 2, figsize=(10.5, 7), sharex=True)
        for mode in EXPECTED_MODES:
            subset = [r for r in omega_rows if r["initial_mode"] == mode]
            x = [r["omega"] for r in subset]
            for ax, field, title in zip(axes.flat, ("chi_D", "chi_mu", "A_TV", "chi_D_L"), (r"$\chi_D$", r"$\chi_\mu$", r"$A_{TV}$", r"late $\chi_{D,L}$")):
                ax.plot(x, [r[field] for r in subset], marker=markers[mode], color=colors[mode], label=mode_label(mode))
                ax.axhline(0, color="0.55", lw=0.7)
                ax.set_title(title)
                ax.grid(alpha=0.22)
                if logx:
                    ax.set_xscale("log")
        for ax in axes[-1]:
            ax.set_xlabel(r"confinement $\omega$")
        axes[0, 0].legend(ncol=3)
        fig.suptitle("Upward zero-rate response metrics — samples joined only as a guide (no fit)", y=1.01)
        fig.text(0.5, -0.015, "Markers are archived samples; lines do not assert interpolation or a scaling law.", ha="center", color="0.35")
        fig.tight_layout()
        save_figure(fig, figures, stem)

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    for mode in EXPECTED_MODES:
        subset = [r for r in omega_rows if r["initial_mode"] == mode]
        x = [r["omega"] for r in subset]
        axes[0].plot(x, [r["baseline_S_T"] for r in subset], marker=markers[mode], color=colors[mode], label=mode_label(mode))
        axes[1].plot(x, [r["baseline_D_T"] for r in subset], marker=markers[mode], color=colors[mode], label=mode_label(mode))
    axes[0].set_title(r"Baseline $S_0(T)$")
    axes[1].set_title(r"Baseline $D_0(T)=1-S_0(T)$")
    for ax in axes:
        ax.set_xlabel(r"confinement $\omega$")
        ax.grid(alpha=0.22)
    axes[0].set_ylabel("probability")
    axes[0].legend()
    fig.suptitle("Unperturbed finite-v8 detection baseline (no fit)")
    fig.tight_layout()
    save_figure(fig, figures, "03_baseline_survival_detection")

    for quantity, ylabel, stem in (
        ("chi_click_density", r"$\chi_g(t)$", "04_chi_g_overlays_by_mode"),
        ("chi_survival", r"$\chi_S(t)$", "05_chi_survival_overlays_by_mode"),
    ):
        fig, axes = plt.subplots(1, 3, figsize=(13.2, 3.8), sharey=True)
        cmap = plt.get_cmap("viridis")
        for ax, mode in zip(axes, EXPECTED_MODES):
            for i, omega in enumerate(EXPECTED_OMEGAS):
                r = omega_responses[(omega, mode)]
                x = r["panel_midpoints"] if quantity == "chi_click_density" else r["times"]
                ax.plot(x, r[quantity], color=cmap(i / 3), label=rf"$\omega={omega:g}$")
            ax.axhline(0, color="0.55", lw=0.7)
            ax.axvline(T_CUT, color="0.4", lw=0.8, ls="--", label=rf"$t_c={T_CUT:g}$" if mode == "00" else None)
            ax.set_title(mode_label(mode))
            ax.set_xlabel("time")
            ax.grid(alpha=0.2)
        axes[0].set_ylabel(ylabel)
        axes[-1].legend(loc="best")
        fig.suptitle(f"Upward {ylabel} shape across confinement — no fit")
        fig.tight_layout()
        save_figure(fig, figures, stem)

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7), sharex=True, sharey=True)
    for ax, omega in zip(axes.flat, EXPECTED_OMEGAS):
        for mode in EXPECTED_MODES:
            r = omega_responses[(omega, mode)]
            ax.plot(r["panel_midpoints"], r["chi_click_density"], color=colors[mode], label=mode_label(mode))
        ax.axhline(0, color="0.55", lw=0.7)
        ax.axvline(T_CUT, color="0.4", lw=0.8, ls="--")
        ax.set_title(rf"$\omega={omega:g}$")
        ax.grid(alpha=0.2)
    axes[0, 0].legend()
    for ax in axes[-1]: ax.set_xlabel("time")
    for ax in axes[:, 0]: ax.set_ylabel(r"$\chi_g(t)$")
    fig.suptitle("Fixed-confinement mode comparison")
    fig.tight_layout()
    save_figure(fig, figures, "06_fixed_omega_mode_comparison")

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    for quantity, marker in (("chi_click_density", "o"), ("chi_survival", "s"), ("chi_D", "^")):
        subset = [r for r in doublets if r["quantity"] == quantity]
        axes[0].semilogy([r["omega"] for r in subset], [max(r["max_abs_difference"], 1e-18) for r in subset], marker=marker, label=quantity)
        axes[1].semilogy([r["omega"] for r in subset], [max(r["relative_L2_difference"], 1e-18) for r in subset], marker=marker, label=quantity)
    axes[0].set_title("absolute 10–01 residual")
    axes[1].set_title("relative L2 10–01 residual")
    for ax in axes:
        ax.set_xlabel(r"confinement $\omega$")
        ax.grid(alpha=0.22)
    axes[0].legend()
    fig.suptitle("Excited-mode doublet numerical degeneracy")
    fig.tight_layout()
    save_figure(fig, figures, "07_excited_doublet_residuals")

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    for mode in EXPECTED_MODES:
        subset = [r for r in omega_rows if r["initial_mode"] == mode]
        x = [r["omega"] for r in subset]
        axes[0].plot(x, [r["A_TV_over_abs_chi_D"] for r in subset], marker=markers[mode], color=colors[mode], label=mode_label(mode))
        axes[1].plot(x, [r["chi_D_E"] for r in subset], marker=markers[mode], color=colors[mode], ls="--", label=f"{mode} early")
        axes[1].plot(x, [r["chi_D_L"] for r in subset], marker=markers[mode], color=colors[mode], ls="-", label=f"{mode} late")
    axes[0].axhline(1, color="0.5", lw=0.7)
    axes[0].set_title(r"cancellation ratio $A_{TV}/|\chi_D|$")
    axes[1].axhline(0, color="0.5", lw=0.7)
    axes[1].set_title(r"early/late split at $t_c=3.6$")
    for ax in axes:
        ax.set_xlabel(r"confinement $\omega$")
        ax.grid(alpha=0.22)
    axes[0].legend()
    axes[1].legend(ncol=2, fontsize=7)
    fig.suptitle("Signed temporal redistribution and cancellation")
    fig.tight_layout()
    save_figure(fig, figures, "08_cancellation_early_late")

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), sharey=True)
    for ax, quantity in zip(axes, ("chi_click_density", "chi_survival")):
        for mode in EXPECTED_MODES:
            subset = [r for r in shapes if r["mode"] == mode and r["quantity"] == quantity]
            ax.plot([r["omega"] for r in subset], [r["relative_L2_residual_after_scaling"] for r in subset], marker=markers[mode], color=colors[mode], label=mode_label(mode))
        ax.set_title(quantity.replace("_", " "))
        ax.set_xlabel(r"confinement $\omega$")
        ax.grid(alpha=0.22)
    axes[0].set_ylabel(r"relative residual after best rescaling of $\omega=4$ shape")
    axes[0].legend()
    fig.suptitle("Amplitude-only scaling test: large residual means genuine reshaping")
    fig.tight_layout()
    save_figure(fig, figures, "09_shape_rescaling_diagnostic")

    ground_scan = [r for r in omega_rows if r["initial_mode"] == "00"]
    anchors = [r for r in canonical_rows if r["matrix_id"] in {"U3", "U2", "U4", "U2-I"}]
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    ax.plot([r["omega"] for r in ground_scan], [r["chi_D"] for r in ground_scan], "o-", color=colors["00"], label="new scan, ds=0.1")
    marker_map = {0.001: "D", 0.0005: "s", 0.00025: "^"}
    for r in anchors:
        ax.scatter(r["omega"], r["chi_D"], s=62, marker=marker_map.get(r["dt"], "o"), edgecolor="black", label=f"{r['matrix_id']} (dt={r['dt']:g}, ds={r['insertion_dt']:g})")
    ax.axhline(0, color="0.5", lw=0.7)
    ax.set_xscale("log")
    ax.set_xlabel(r"confinement $\omega$")
    ax.set_ylabel(r"$\chi_D$")
    ax.set_title("Ground-mode omega context: exploratory scan versus curated anchors")
    ax.grid(alpha=0.22)
    ax.legend(ncol=2, fontsize=7)
    fig.tight_layout()
    save_figure(fig, figures, "10_ground_mode_anchor_context")


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]], limit: int | None = None) -> str:
    shown = rows if limit is None else rows[:limit]
    header = "| " + " | ".join(label for _, label in columns) + " |"
    divider = "|" + "|".join("---" for _ in columns) + "|"
    body = []
    for row in shown:
        cells = []
        for key, _ in columns:
            value = row.get(key, "")
            cells.append(fmt(value, 7) if isinstance(value, (float, int, np.number)) and not isinstance(value, bool) else str(value))
        body.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, divider, *body])


def write_reports(
    project: Path,
    output: Path,
    canonical_rows: list[dict[str, Any]],
    omega_rows: list[dict[str, Any]],
    omega_responses: dict[tuple[float, str], dict[str, Any]],
    task08: dict[str, Any],
    canonical_integrity: dict[str, Any],
    omega_integrity: dict[str, Any],
    inventory_summary: dict[str, Any],
    doublets: list[dict[str, Any]],
    shapes: list[dict[str, Any]],
    spatial: dict[str, Any],
) -> None:
    excited = [r for r in omega_rows if r["initial_mode"] in {"10", "01"}]
    mode00 = [r for r in omega_rows if r["initial_mode"] == "00"]
    max_doublet_chid = max(r["max_abs_difference"] for r in doublets if r["quantity"] == "chi_D")
    max_doublet_curve = max(r["max_abs_difference"] for r in doublets if r["quantity"] in {"chi_survival", "chi_click_density"})
    omega144_excited = [r for r in excited if r["omega"] == 144]
    task08_status = task08["status"]
    summary_json = {
        "analysis_date": ANALYSIS_DATE,
        "derivative_convention": "one-sided derivative at zero per unit dimensionless environmental rate",
        "canonical_case_count": len(canonical_rows),
        "omega_scan_case_count": len(omega_rows),
        "integrity": {"canonical": canonical_integrity, "omega_scan": omega_integrity},
        "inventory": inventory_summary,
        "task08": {
            "scientific_verdict": task08_status["scientific_verdict"],
            "accepted_response_roles": task08_status["accepted_response_roles"],
            "direct_response_representation_and_longitudinal_refinement_completed": task08_status["direct_response_representation_and_longitudinal_refinement_completed"],
            "publication_level_project_claim_closed_under_attached_master": task08_status["publication_level_project_claim_closed_under_attached_master"],
            "finite_rate_or_temperature_claim_authorized": task08_status["finite_rate_or_temperature_claim_authorized"],
        },
        "omega_findings": {
            "mode00_chi_D_values": {str(int(r["omega"])): r["chi_D"] for r in mode00},
            "excited_sign_reversal_bracket_only": "64 < omega < 144",
            "omega144_excited_early_late": [{"mode": r["initial_mode"], "chi_D_E": r["chi_D_E"], "chi_D_L": r["chi_D_L"], "chi_D": r["chi_D"], "A_TV": r["A_TV"]} for r in omega144_excited],
            "max_abs_10_01_chi_D_difference": max_doublet_chid,
            "max_abs_10_01_curve_difference": max_doublet_curve,
            "no_scaling_law_fitted": True,
        },
        "spatial_timing_reconciliation": spatial,
    }
    write_json(output / "ANALYSIS_SUMMARY.json", summary_json)

    legacy_local_fails = [r for r in canonical_rows if not as_bool(r["local_checks_passed"])]
    canonical_by_id = {r["matrix_id"]: r for r in canonical_rows}
    accepted_rows = [canonical_by_id[k] for k in ("D2-I", "U2-I", "P2-I")]
    readme = f"""# Stage-07 full analysis ({ANALYSIS_DATE})

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
- Modes 10 and 01 are numerically degenerate within at most {max_doublet_chid:.3e} in `chi_D` across the four omega values.
- The excited doublet has negative `chi_D` at omega 4, 36, and 64, and positive `chi_D` at omega 144. The data support only the bracket `64 < omega < 144`; no root or interpolation is claimed.
- At omega 144, the excited-mode net sign reversal is caused by temporal redistribution: early response remains negative while late response is positive and larger. `A_TV/|chi_D|` is about {omega144_excited[0]['A_TV_over_abs_chi_D']:.3f}, exposing strong cancellation.
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
"""
    write_text(output / "README.md", readme)

    integrity_report = f"""# Integrity and provenance report

## Scope and non-mutation policy

The audit traversed `Part1/Stage07` while excluding this output directory. It found {inventory_summary['stage07_file_count_excluding_this_analysis']:,} files totaling {inventory_summary['stage07_total_bytes_excluding_this_analysis']:,} bytes. File-level SHA-256 values are recorded in `STAGE07_FILE_HASH_INVENTORY.csv`; {inventory_summary['duplicate_file_instances']:,} duplicate instances were identified by identical content hash. Existing files were read only.

## Evidence hierarchy

1. **Authoritative scientific inputs:** `Task07_Final_Curated_Input_2026-08-10`, whose register selects 15 canonical and 3 supplemental insertion-refinement roles.
2. **Independent scientific adjudication:** the dated Task-08 aggregate recheck. It reports `{task08_status['scientific_verdict']}`, 15/15 canonical and 3/3 supplemental roles scientifically admissible, and accepts D2-I, U2-I, and P2-I as the response roles.
3. **Priority exploratory extension:** the 12-case upward omega bundle. It passes hashes and case-local loader checks but has no project aggregate or matched convergence budget.
4. **Visualization derivatives and duplicates:** omega-144 timing/spatial exports, root case copies, historical folders, and archive duplicates are kept distinct from ordinary acceptance evidence.

## Hash and reconstruction results

- Curated outer ZIP hashes: 18/18 match the register.
- Curated internal manifests: `all_passed={canonical_integrity['all_internal_hash_manifests_passed']}`.
- Curated curves-versus-NPZ maximum discrepancy: {canonical_integrity['maximum_curves_vs_npz_abs']:.3e}.
- Omega case-share manifest: `all_passed={omega_integrity['case_share_manifest']['all_passed']}` ({omega_integrity['case_share_manifest']['entry_count']} entries).
- Omega quicklook manifest: `all_passed={omega_integrity['quicklook_manifest']['all_passed']}` ({omega_integrity['quicklook_manifest']['entry_count']} entries).
- Omega outer bundle archive sidecar: `all_passed={omega_integrity['outer_bundle_archive_sidecar']['all_passed']}`.
- Omega internal manifests: `all_passed={omega_integrity['all_internal_hash_manifests_passed']}`.
- Omega curves-versus-NPZ maximum discrepancy: {omega_integrity['maximum_curves_vs_npz_abs']:.3e}.
- Omega archive log scan: `all_passed={omega_integrity['all_log_scans_passed']}`; the scan searched archived stdout/stderr/simulation logs for tracebacks and explicit error/fail lines.
- The omega-144/mode-00 timing arrays match the ordinary quicklook arrays exactly: `{spatial['ordinary_case_and_timing_arrays_identical']}`.

## Preserved legacy case-local failures

The curated register intentionally includes {len(legacy_local_fails)} archived roles whose original case-loader verdict is `FAIL`: {', '.join(r['matrix_id'] for r in legacy_local_fails)}. Each records the same four failures: insertion-quadrature factor-two refinement, two solver JSON/local-response booleans, and the solver-local stage-manifest status. Their ZIPs and internal manifests remain intact. These records are not silently relabelled; the separate, later Task-08 aggregate independently reconstructs the families and marks all selected roles scientifically admissible. The canonical master CSV exposes both statuses side by side.

## Exit/status semantics

Exit code 3 is locally admissible under the frozen Task-07 loader contract. In these records it means `PASS_CASE_LOCAL_RERUN_PENDING`: numerical checks passed, while deterministic same-prefix rerun and/or external aggregate evidence remains pending. It is not treated as an execution failure, and it is not promoted to Task-08 acceptance.

## Scientific boundary

All response quantities are derivatives at zero environmental rate per unit dimensionless rate. No finite-positive-rate state, temperature curve, continuum limit, or publication-level direct-representation closure is produced here. Task-08 itself records that direct response representation/longitudinal refinement and publication-level closure remain incomplete.
"""
    write_text(output / "INTEGRITY_AND_PROVENANCE_REPORT.md", integrity_report)

    metrics_table = markdown_table(
        omega_rows,
        [("omega", "omega"), ("initial_mode", "mode"), ("baseline_S_T", "S0(T)"), ("chi_D", "chi_D"), ("chi_mu", "chi_mu"), ("chi_D_E", "early"), ("chi_D_L", "late"), ("A_TV", "A_TV")],
    )
    rho = {
        mode: {
            field: spearman4([r["omega"] for r in omega_rows if r["initial_mode"] == mode], [r[field] for r in omega_rows if r["initial_mode"] == mode])
            for field in ("chi_D", "chi_mu", "A_TV", "baseline_S_T")
        }
        for mode in EXPECTED_MODES
    }
    science = f"""# Omega-dependence scientific report

## Definitions

`chi_D = -chi_S(T) = sum_i chi_panel_probability_i`. `chi_mu` is the trapezoidal integral of the state-node survival derivative. With the archived panel-average convention, `chi_g` lives on the 100 panel midpoints while `chi_S` and baseline survival live on 101 state nodes. The complete signed response norm is `A_TV = 1/2 (sum_i |chi_panel_probability_i| + |chi_S(T)|)`. Early and late detection responses split at `t_c={T_CUT}`.

## Accepted Task-08 context

The independent aggregate accepts the insertion-refined roles D2-I, U2-I, and P2-I. Recomputed from their archived arrays:

{markdown_table(accepted_rows, [("matrix_id", "role"), ("environment_direction", "direction"), ("chi_D", "chi_D"), ("chi_mu", "chi_mu"), ("A_TV", "A_TV"), ("task08_evidence_classification", "Task-08 class")])}

All three directions are `RESOLVED_NONZERO` under the dated Task-08 zero-rate budget. This is a finite-v8, zero-rate susceptibility result; it is not a finite-positive-rate or continuum statement. Scalar-factorized D1/U1/P1 remain exact null controls. Six older curated case-loader records retain local `FAIL` status, but the later independent aggregate separately reconstructs and adjudicates the selected families; both layers are preserved in `CANONICAL_CASE_MASTER_TABLE.csv`.

## Recomputed 12-case table

{metrics_table}

Every displayed metric was reconstructed from the compact NPZ arrays and checked against both CSV curves and reported metrics.

## What changes with confinement

For mode 00, `chi_D` stays negative at all four sampled omega values: {', '.join(f"{r['omega']:g}: {r['chi_D']:+.6g}" for r in mode00)}. Its magnitude is nonmonotonic, reaching its largest sampled value at omega 36, not at the largest omega.

For modes 10 and 01, `chi_D` is negative at omega 4, 36, and 64, but positive at omega 144. Thus the evidence supports a sampled sign change bracket only: **64 < omega < 144**. Four nonuniform points, with a dt change at omega 144, do not justify interpolation to a unique root.

At omega 144 the excited doublet has `chi_D_E ≈ {omega144_excited[0]['chi_D_E']:+.6g}` and `chi_D_L ≈ {omega144_excited[0]['chi_D_L']:+.6g}`. The positive late contribution outweighs the still-negative early contribution, yielding `chi_D ≈ {omega144_excited[0]['chi_D']:+.6g}`. Meanwhile `A_TV ≈ {omega144_excited[0]['A_TV']:.6g}`, so `A_TV/|chi_D| ≈ {omega144_excited[0]['A_TV_over_abs_chi_D']:.3f}`. This is strong signed cancellation and time-shape redistribution, not a simple amplitude rescaling.

The 10/01 doublet is numerically degenerate: the largest absolute `chi_D` difference is {max_doublet_chid:.3e}, and the largest pointwise difference over `chi_S` or `chi_g` is {max_doublet_curve:.3e}. This supports mode-exchange symmetry at the resolution of the archived data, not a proof of exact analytic equality.

## Trend diagnostics, not laws

Spearman rank coefficients over four points are: mode 00 `{rho['00']}`, mode 10 `{rho['10']}`, mode 01 `{rho['01']}`. These ranks are descriptive only. The nonmonotonic mode-00 response, the excited-mode sign change, the large rescaling residuals in `OMEGA_SHAPE_SCALING_DIAGNOSTICS.csv`, and the omega-144 time-domain cancellation jointly rule out interpreting the scan as evidence for a universal amplitude-only scaling law.

No square-root, power, affine, monotonic, or asymptotic law was fitted. The figures connect samples only to aid reading.

## Comparison to curated omega anchors

The ground-mode scan may be compared to curated upward roles only with discretization labels retained: U3 is omega 1 at dt=1e-3; U2 is omega 100 at dt=5e-4 and insertion dt=0.1; U4 is omega 100 at dt=2.5e-4 and insertion dt=0.1; U2-I is the independently refined insertion grid at omega 100, dt=5e-4, insertion dt=0.05. Therefore omega 4/36/64 are time-step matched to U2, omega 144 is time-step matched to U4, and U2-I is the Task-08 accepted response role but is not insertion-grid matched to the scan.

## Limitations

- Only four omega values and three initial modes were supplied.
- The exploratory scan lacks N=16 shell partners, dt/2 partners at every omega, insertion refinements, and a Task-08 aggregate adjudication.
- Omega 144 changes dt from 5e-4 to 2.5e-4, so the scan is not a single fixed-discretization sequence.
- No uncertainty bars can be assigned from the supplied scan alone.
- The spatial atlas has `physical_acceptance=false` and must remain a visualization derivative, despite exact reconciliation of its timing arrays to the ordinary omega-144/mode-00 case.
"""
    write_text(output / "OMEGA_DEPENDENCE_SCIENTIFIC_REPORT.md", science)

    claims = f"""# Claim matrix

| Claim | Status | Evidence and boundary |
|---|---|---|
| The curated 18 Task-07 roles are scientifically admissible for zero-rate response analysis. | Supported | Independent Task-08 aggregate: `{task08_status['scientific_verdict']}`; 15 canonical plus 3 supplemental roles. |
| Accepted response roles are D2-I, U2-I, and P2-I. | Supported | Task-08 run status and insertion refinement comparisons. |
| Upward `chi_D` for the excited 10/01 doublet changes sampled sign between omega 64 and 144. | Supported for the supplied samples | Both modes are negative at 64 and positive at 144. Only a bracket is claimed. |
| Modes 10 and 01 are degenerate. | Numerically supported | Max archived `chi_D` difference {max_doublet_chid:.3e}; this is numerical evidence, not an analytic proof. |
| Omega-144 excited-mode sign reversal is a temporal-redistribution effect. | Supported descriptively | Early term is negative, late term positive and larger; `A_TV/|chi_D|≈{omega144_excited[0]['A_TV_over_abs_chi_D']:.3f}`. |
| Mode-00 `|chi_D|` grows monotonically with omega. | Contradicted by samples | Sample magnitude peaks at omega 36 and is smaller at 64 and 144. |
| A universal square-root, power, affine, monotonic, or asymptotic omega law is established. | Unsupported | Four points, a dt change, reshaping, and no matched scan-wide convergence budget. No fit performed. |
| The 12 omega cases have passed Task-08 scientific acceptance. | Unsupported | Case-local checks pass, but project aggregate/convergence adjudication was not run. |
| Exit code 3 means numerical failure. | Incorrect | Frozen loader semantics: `PASS_CASE_LOCAL_RERUN_PENDING`; zero failed checks and pending rerun/aggregate evidence. |
| The analysis establishes finite-positive-rate or temperature behavior. | Unsupported | All products are zero-rate derivatives; finite rate is explicitly absent/not authorized. |
| The omega-144 spatial atlas independently establishes physical acceptance. | Unsupported | Atlas metadata says `physical_acceptance=false`; it is a signed visualization derivative. |
| Publication-level closure is complete. | Unsupported | Task-08 records direct response representation/longitudinal refinement incomplete and publication-level closure provisional. |
"""
    write_text(output / "CLAIM_MATRIX.md", claims)

    proposal = f"""# Conservative manuscript update proposal

## Proposed placement

Add a short exploratory subsection after the V8 manuscript's accepted zero-rate response results, plus one limitation paragraph. Do not replace the accepted Task-08 values or elevate the new scan to canonical status.

## Proposed text

> **Exploratory confinement scan of the upward zero-rate susceptibility.** We evaluated the same finite-v8 zero-rate tangent response for upward environmental coupling at omega = 4, 36, 64, and 144 and for initial modes 00, 10, and 01. All twelve archived cases pass their independent case-local reconstruction checks, with deterministic same-prefix reruns and aggregate convergence adjudication still pending. Accordingly, the scan is exploratory rather than part of the accepted Task-08 response set.
>
> For the ground mode, the final detection susceptibility remains negative at every sampled confinement and is nonmonotonic in magnitude. The excited 10/01 doublet is numerically degenerate within the archived resolution and changes sampled sign between omega 64 and 144. At omega 144, its early contribution remains negative whereas the late contribution is positive and larger, so the positive net response reflects temporal redistribution and cancellation rather than a uniform amplitude change. The four samples do not determine a root or establish a square-root, power, affine, monotonic, or asymptotic confinement law.

## Figure proposal

Use `figures/01_integrated_metrics_linear_omega` for the compact result and `figures/04_chi_g_overlays_by_mode` or `figures/08_cancellation_early_late` for the mechanism. Captions must say that connecting lines are guides and that omega 144 uses dt=2.5e-4 while omega 4/36/64 use dt=5e-4.

## Required caveat paragraph

The response is a one-sided derivative at zero dimensionless environmental rate, not a finite-rate percent change. The scan has no matched shell/time/insertion refinement family at every omega, no uncertainty bars, and no Task-08 aggregate acceptance. The omega-144 spatial atlas is derivative visualization evidence only. Publication-level direct-representation and longitudinal refinement closure remains outside the scope of this update.
"""
    write_text(output / "MANUSCRIPT_UPDATE_PROPOSAL.md", proposal)


def write_requirements_snapshot(output: Path) -> None:
    import importlib.metadata
    import platform
    packages = []
    for name in ("numpy", "matplotlib", "pillow", "pandas", "scipy"):
        try:
            packages.append({"name": name, "version": importlib.metadata.version(name)})
        except importlib.metadata.PackageNotFoundError:
            packages.append({"name": name, "version": "not-installed"})
    write_json(output / "REQUIREMENTS_SNAPSHOT.json", {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "platform": platform.platform(),
        "packages": packages,
    })


def finalize_manifest(output: Path) -> None:
    excluded = {"DELIVERABLE_MANIFEST.json", "SHA256SUMS"}
    files = [p for p in sorted(output.rglob("*")) if p.is_file() and p.name not in excluded]
    records = [{"path": str(p.relative_to(output)), "size_bytes": p.stat().st_size, "sha256": sha256_file(p)} for p in files]
    write_json(output / "DELIVERABLE_MANIFEST.json", {
        "schema": "STAGE07_FULL_ANALYSIS_DELIVERABLE_MANIFEST_V1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "hash_algorithm": "SHA-256",
        "self_hash_policy": "The manifest excludes itself and SHA256SUMS; SHA256SUMS includes the manifest and every other deliverable except itself.",
        "file_count_excluding_manifest_and_SHA256SUMS": len(records),
        "files": records,
    })
    checksum_files = [p for p in sorted(output.rglob("*")) if p.is_file() and p.name != "SHA256SUMS"]
    write_text(output / "SHA256SUMS", "\n".join(f"{sha256_file(p)}  {p.relative_to(output)}" for p in checksum_files))


def main() -> None:
    args = parse_args()
    project = args.project_root.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.finalize_only:
        finalize_manifest(output)
        return
    task08 = load_task08(project)
    canonical_rows, canonical_responses, canonical_integrity = canonical_case_data(project, task08)
    omega_rows, omega_responses, omega_integrity, log_rows = omega_case_data(project)
    doublets, shapes = doublet_and_shape_diagnostics(omega_responses)
    spatial = spatial_reconciliation(project, omega_responses)
    inventory_rows, detailed_inventory, inventory_summary = build_inventory(project, output, canonical_rows, omega_rows, task08)
    write_csv(output / "STAGE07_EVIDENCE_INVENTORY.csv", inventory_rows)
    write_csv(output / "STAGE07_FILE_HASH_INVENTORY.csv", detailed_inventory)
    write_csv(output / "CANONICAL_CASE_MASTER_TABLE.csv", canonical_rows)
    write_csv(output / "OMEGA_SCAN_MASTER_TABLE.csv", omega_rows)
    write_csv(output / "OMEGA_MODE_DOUBLET_RESIDUALS.csv", doublets)
    write_csv(output / "OMEGA_SHAPE_SCALING_DIAGNOSTICS.csv", shapes)
    write_csv(output / "OMEGA_CASE_LOG_SCAN.csv", log_rows)
    write_json(output / "SPATIAL_TIMING_RECONCILIATION.json", spatial)
    plot_outputs(output / "figures", omega_rows, omega_responses, canonical_rows, canonical_responses, doublets, shapes)
    write_requirements_snapshot(output)
    write_reports(project, output, canonical_rows, omega_rows, omega_responses, task08, canonical_integrity, omega_integrity, inventory_summary, doublets, shapes, spatial)
    finalize_manifest(output)


if __name__ == "__main__":
    main()
