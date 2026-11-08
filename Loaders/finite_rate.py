"""CPU reductions of the four native Task09 histories.

The pi1600 definitions and U2-I quadrature follow the archived A127
analyze_native.py. This portable adaptation never imports a production solver,
never executes the historical spectrum audit, and writes only to its output.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

import numpy as np


BRANCHES = ("pi1600", "pi3200", "pi800", "pi0")
TANGENT = "spinor_upward_omega100_mode00_N12_dt5e-4_T10_ins5e-2_Task07_case_share.zip"
TANGENT_PREFIX = "spinor_upward_omega100_mode00_N12_dt5e-4_T10_ins5e-2_"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def total(values):
    return math.fsum(np.asarray(values).tolist())


def read_npz(path):
    with np.load(path, allow_pickle=False) as source:
        return {name: source[name] for name in source.files}


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def table(path, rows):
    columns = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def close(actual, expected, message, atol=5e-13, rtol=1e-10):
    require(math.isclose(float(actual), float(expected), abs_tol=atol, rel_tol=rtol),
            f"{message}: reproduced {actual!r}, stored {expected!r}")


def _history(base, branch):
    folder = base / "branches" / branch
    history = read_npz(folder / "history.npz")
    meta = json.loads((folder / "checkpoint_metadata.json").read_text())
    t = history["times"]
    require(t.ndim == 1 and t.dtype == np.float64 and len(t) > 1, f"{branch}: node schema")
    require(np.isfinite(t).all() and t[0] == 0 and np.all(np.diff(t) > 0),
            f"{branch}: monotone native time grid from zero")
    dt = float(t[1] - t[0])
    require(np.max(np.abs(np.diff(t) - dt)) < 1e-12, f"{branch}: uniform detector grid")
    close(t[-1], meta["physical_time"], f"{branch}: metadata endpoint", rtol=0)
    require(len(t) - 1 == meta["completed_step"], f"{branch}: metadata step count")
    rate = float(meta["rate_lambda"])
    if branch != "pi0":
        config_path = folder / "CONFIG.json"
        if config_path.exists():
            cfg = json.loads(config_path.read_text())
        else:
            cfg = json.loads((folder / "summary_report.json").read_text())["configuration"]
        physical = cfg["physical"]
        close(dt, physical["dt"], f"{branch}: configured detector dt", rtol=0)
        close(rate, physical["rate_lambda"], f"{branch}: configured rate", rtol=0)
        require(physical["omega"] == 100 and physical["n_shell"] == 12 and physical["n_z"] == 1500,
                f"{branch}: compared physical parameters")
        p = history["positive_step_click"]
        p0 = history["zero_step_click"]
        survival = history["positive_survival"]
        cumulative = history["cumulative_positive_click"]
    else:
        cfg = json.loads((folder / "CONFIG.json").read_text())
        p = p0 = history["zero_click_probability"]
        survival = history["zero_survival"]
        cumulative = history["cumulative_zero_click"]
        require(rate == 0, "Standalone-zero rate")
    for key, arr in [("native click", p), ("paired-zero click", p0)]:
        require(arr.shape == (len(t) - 1,) and arr.dtype == np.float64 and np.isfinite(arr).all(),
                f"{branch}: {key} schema")
        require(np.all(arr >= 0), f"{branch}: nonnegative {key}")
    for key in ["zero_survival", "cumulative_zero_click", "representation_ledger", "event_first_crossing_ledger"]:
        require(history[key].shape == t.shape and np.isfinite(history[key]).all(),
                f"{branch}: {key} schema")
    for key, arr in [("survival", survival), ("cumulative", cumulative)]:
        require(arr.shape == t.shape and np.isfinite(arr).all(), f"{branch}: {key} schema")
    # This checks saved increments against saved totals, without overwriting either.
    close(total(p), cumulative[-1] - cumulative[0], f"{branch}: cumulative native clicks", atol=5e-11)
    close(total(p0), history["cumulative_zero_click"][-1] - history["cumulative_zero_click"][0],
          f"{branch}: cumulative paired-zero clicks", atol=5e-11)
    representation = history["representation_ledger"]
    event = history["event_first_crossing_ledger"]
    close(representation[-1], meta["representation_ledger"], f"{branch}: representation metadata")
    close(event[-1], meta["event_first_crossing_ledger"], f"{branch}: event metadata")
    ordered = {"scope": "terminal ordered terms and legacy anchor only; no missing spectra reconstructed"}
    if branch != "pi0":
        legacy = meta.get("legacy_prefix_origin", {"representation_ledger": 0., "event_ledger": 0.})
        rep_terms = meta["forward_representation_terms"]
        event_terms = meta["forward_event_terms"]
        close(math.fsum([legacy["representation_ledger"], *rep_terms]), representation[-1],
              f"{branch}: ordered representation sum", atol=1e-20, rtol=1e-12)
        close(math.fsum([legacy["event_ledger"], *event_terms]), event[-1],
              f"{branch}: ordered event sum", atol=1e-22, rtol=1e-12)
        ordered.update(representation_terms=len(rep_terms), event_terms=len(event_terms),
                       legacy_anchor_step=legacy.get("step", 0),
                       terminal_ordered_sums_match=True)
    mid = (t[:-1] + t[1:]) / 2
    dp = p - p0
    ds = survival - history["zero_survival"]
    dc = cumulative - history["cumulative_zero_click"]
    closure = survival + cumulative + representation + event - survival[0]
    zero_closure = history["zero_survival"] + history["cumulative_zero_click"] - history["zero_survival"][0]
    end = {
        "branch": branch, "rate_lambda": rate, "T": float(t[-1]), "step": len(t) - 1,
        "detector_dt": dt, "S_lambda": float(survival[-1]),
        "S_paired_zero": float(history["zero_survival"][-1]),
        "C_lambda_saved": float(cumulative[-1]),
        "C_paired_zero_saved": float(history["cumulative_zero_click"][-1]),
        "delta_C_saved": float(dc[-1]), "delta_C_from_fsum_differences": total(dp),
        "delta_S_retained": float(ds[-1]), "B_rep": float(representation[-1]),
        "B_event": float(event[-1]),
        "overflow_diagnostic": float(history["cumulative_overflow_bound"][-1]),
        "analytic_event_tail_diagnostic": float(history["analytic_event_tail_bound"][-1]),
        "max_positive_accounting_residual": float(np.max(np.abs(closure))),
        "max_zero_accounting_residual": float(np.max(np.abs(zero_closure))),
        "restricted_retained_survival_change_trapezoids": total(np.diff(t) * (ds[:-1] + ds[1:]) / 2),
        "click_conditional_mean_lambda": total(mid * p) / total(p),
        "click_conditional_mean_zero": total(mid * p0) / total(p0),
        "retained_signed_record_norm": .5 * (total(np.abs(dp)) + abs(float(ds[-1]))),
    }
    end["click_conditional_mean_change"] = end["click_conditional_mean_lambda"] - end["click_conditional_mean_zero"]
    end["rank"] = int(history["total_rank"][-1])
    policy = meta.get("reserve_policy", {})
    active = {
        "name": policy.get("name", "standalone zero: no compression allowance"),
        "prospective_final_ceiling": float(policy["final_ceiling_decimal"]) if policy else 0.,
        "saved_active_allowance_at_endpoint": meta.get("reserve_line_after_completed_call", 0.),
        "stored_legacy_ceiling_field": float(history["representation_ceiling"][-1]) if "representation_ceiling" in history else None,
        "scope": "policy metadata only; a numerical-loss allowance is not an error bar or convergence certificate",
    }
    return {"h": history, "meta": meta, "config": cfg, "t": t, "mid": mid, "dt": dt, "rate": rate,
            "p": p, "p0": p0, "dp": dp, "dg": dp / dt, "ds": ds, "dc": dc,
            "endpoint": end, "ordered": ordered, "policy": active}


def aggregate_native(record, edges, values):
    """Sum native probability bins whose nodes exactly align to supplied edges."""
    t = record["t"]
    indices = np.rint((edges - t[0]) / record["dt"]).astype(int)
    require(np.all(indices >= 0) and np.all(indices < len(t)), "No out-of-support panel edge")
    require(np.max(np.abs(t[indices] - edges)) < 1e-12, "No interpolated panel edge")
    require(np.all(np.diff(indices) > 0), "Panel edges must be strictly increasing")
    return np.asarray([total(values[i:j]) for i, j in zip(indices[:-1], indices[1:])]), indices


def tangent(repo, record):
    path = repo / "data" / "canonical_response" / "cases" / TANGENT
    with zipfile.ZipFile(path) as archive:
        prefix = TANGENT_PREFIX
        config = json.loads(archive.read(prefix + "configuration.json"))
        require(config["omega"] == 100 and config["N_shell"] == 12 and config["N_z"] == 1500
                and config["initial_mode"] == "00" and config["environment_direction"] == "upward",
                "Matched U2-I physical identity")
        close(config["dt"], record["dt"], "Tangent detector step", rtol=0)
        reported = json.loads(archive.read(prefix + "output_hashes.json"))["files"]
        def load(suffix):
            name = prefix + suffix
            payload = archive.read(name)
            # Text metadata may be sanitized in the release; numeric bytes must stay exact.
            if name in reported:
                require(hashlib.sha256(payload).hexdigest() == reported[name], "Native tangent array hash " + suffix)
            return np.load(io.BytesIO(payload), allow_pickle=False)
        tt = load("times.npy")
        chi_s = load("chi_survival.npy")
        chi_g = load("chi_click_density.npy")
        with load("kernel_summary.npz") as stored:
            kernel = {name: stored[name] for name in stored.files}
    total_kernel = kernel["kernel_jump_probability"] + kernel["kernel_anticommutator_probability"]
    require(np.array_equal(total_kernel, kernel["kernel_total_probability"]), "Jump plus anticommutator identity")
    rs = np.zeros(len(tt))
    rp = np.zeros(len(tt) - 1)
    # The original orientation is observation row, insertion column; half endpoint weights.
    for j in range(1, len(tt)):
        widths = np.diff(tt[:j + 1])
        weights = np.zeros(j + 1)
        weights[:-1] += widths / 2
        weights[1:] += widths / 2
        rs[j] = np.dot(weights, kernel["kernel_survival"][j, :j + 1])
        rp[j - 1] = np.dot(weights[:-1], total_kernel[j - 1, :j])
    require(np.max(np.abs(rs - chi_s)) < 1e-14, "Native causal survival quadrature")
    require(np.max(np.abs(rp - kernel["chi_panel_probability"])) < 1e-14, "Native causal roof quadrature")
    require(np.array_equal(kernel["chi_panel_probability"] / np.diff(tt), chi_g), "Native panel density convention")
    finite, _ = aggregate_native(record, tt, record["dp"])
    chi_p = chi_g * np.diff(tt)
    linear = record["rate"] * chi_p
    values = {
        "T": float(tt[-1]), "number_panels": len(tt) - 1,
        "panel_width": float(tt[1] - tt[0]), "detector_dt": record["dt"],
        "chi_D_from_panel_sum": total(chi_p), "chi_D_from_survival": -float(chi_s[-1]),
        "linear_endpoint_prediction": total(linear),
        "finite_endpoint_from_dp_sum": total(record["dp"]),
        "finite_minus_linear_endpoint": total(record["dp"]) - record["rate"] * total(chi_p),
        "endpoint_relative_departure_percent": 100 * (total(record["dp"]) / (record["rate"] * total(chi_p)) - 1),
        "complete_panel_record_residual": .5 * (total(np.abs(finite - linear))
                                                + abs(float(record["ds"][-1] - record["rate"] * chi_s[-1]))),
        "max_survival_quadrature_difference": float(np.max(np.abs(rs - chi_s))),
        "max_roof_quadrature_difference": float(np.max(np.abs(rp - kernel["chi_panel_probability"]))),
        "scope": "Single-rate matched-panel descriptive comparison; no rate-halving or complete-convergence certificate.",
    }
    return values, tt, finite, linear


def _rate_comparison(low, high):
    close(high["rate"], 2 * low["rate"], "Rate doubling", atol=1e-16, rtol=1e-12)
    endpoint = min(low["t"][-1], high["t"][-1])
    # Exact common native support, with 100-bin panels and an actual final partial panel.
    count = min(len(low["t"]), len(high["t"])) - 1
    require(np.max(np.abs(low["t"][:count + 1] - high["t"][:count + 1])) < 1e-12,
            "Compared rate histories have the same saved node grid")
    node_indices = np.unique(np.r_[np.arange(0, count + 1, 100), count]).astype(int)
    edges = low["t"][node_indices]
    small, loidx = aggregate_native(low, edges, low["dp"])
    large, hiidx = aggregate_native(high, edges, high["dp"])
    residual = large - 2 * small
    ds_residual = float(high["ds"][hiidx[-1]] - 2 * low["ds"][loidx[-1]])
    row = {
        "low_rate": low["rate"], "high_rate": high["rate"], "common_T": float(endpoint),
        "common_native_intervals": count, "panels": len(edges) - 1,
        "low_delta_click": total(small), "high_delta_click": total(large),
        "high_over_twice_low_endpoint": total(large) / (2 * total(small)),
        "complete_panel_record_scaling_residual": .5 * (total(np.abs(residual)) + abs(ds_residual)),
        "interpretation": "descriptive common-support rate scaling; not quadratic-remainder certification",
    }
    return row, edges, small, large



def _a127_tables(record, references, output):
    """Regenerate the three small A127 tables with their original definitions."""
    h, t, dt, mid = record["h"], record["t"], record["dt"], record["mid"]
    pp, pz, dp, dg, dc, ds = record["p"], record["p0"], record["dp"], record["dg"], record["dc"], record["ds"]
    endpoints = []
    for horizon in [0., 2.8, 3.6, 4.924, 6., 8., 8.3, 9., 9.6635, 10.]:
        j = int(round(horizon / dt))
        close(t[j], horizon, "A127 exact endpoint support", rtol=0)
        row = {
            "T": float(t[j]), "step": j, "S_lambda": float(h["positive_survival"][j]),
            "S_paired_zero": float(h["zero_survival"][j]),
            "C_lambda_saved": float(h["cumulative_positive_click"][j]),
            "C_paired_zero_saved": float(h["cumulative_zero_click"][j]),
            "delta_C_saved": float(dc[j]), "delta_S_retained": float(ds[j]),
            "B_rep": float(h["representation_ledger"][j]),
            "B_event": float(h["event_first_crossing_ledger"][j]),
            "rank": int(h["total_rank"][j]), "delta_C_from_fsum_differences": total(dp[:j]),
        }
        if j:
            row.update(
                delta_C_relative_percent=float(100*dc[j]/h["cumulative_zero_click"][j]),
                delta_g_last_bin=float(dg[j-1]),
                restricted_retained_survival_change_trapezoids=total(np.diff(t[:j+1])*(ds[:j]+ds[1:j+1])/2),
                click_conditional_mean_lambda=total(mid[:j]*pp[:j])/total(pp[:j]),
                click_conditional_mean_zero=total(mid[:j]*pz[:j])/total(pz[:j]))
            row["click_conditional_mean_change"] = row["click_conditional_mean_lambda"] - row["click_conditional_mean_zero"]
        endpoints.append(row)
    windows = []
    for a, b in [(0,3.6),(3.6,6),(6,8.3),(8.3,10),(6,10),(3.6,10),(9.6635,10),(0,10)]:
        i, j = int(round(a/dt)), int(round(b/dt))
        close(t[i], a, "A127 exact left window support", rtol=0)
        close(t[j], b, "A127 exact right window support", rtol=0)
        values = dp[i:j]
        windows.append({
            "start": a, "end": b, "intervals": j-i, "C_lambda_window": total(pp[i:j]),
            "C_zero_window": total(pz[i:j]), "delta_C_window": total(values),
            "positive_response_mass": total(values[values > 0]),
            "negative_response_mass": total(values[values < 0]),
            "saved_endpoint_delta_C_change": float(dc[j]-dc[i]),
        })
    signs = []
    for j in np.flatnonzero((dg[:-1]*dg[1:] < 0) & (mid[:-1] >= 1.2)):
        signs.append({
            "direction": "negative_to_positive" if dg[j] < 0 else "positive_to_negative",
            "left_midpoint": float(mid[j]), "right_midpoint": float(mid[j+1]),
            "left_bin_average_delta_g": float(dg[j]), "right_bin_average_delta_g": float(dg[j+1]),
        })
    checked = 0
    for filename, rows in [("endpoints.csv", endpoints), ("window_masses.csv", windows), ("sign_changes.csv", signs)]:
        with (references/filename).open(newline="", encoding="utf-8") as source:
            expected = list(csv.DictReader(source))
        require(len(rows) == len(expected), "A127 " + filename + " row count")
        for index, (row, stored) in enumerate(zip(rows, expected)):
            for key, value in stored.items():
                if not value:
                    require(key not in row, f"A127 {filename}/{index}/{key} empty entry")
                elif key == "direction":
                    require(row[key] == value, "A127 native sign direction")
                    checked += 1
                else:
                    close(row[key], float(value), f"A127 {filename}/{index}/{key}")
                    checked += 1
        table(output/("pi1600_"+filename if filename == "endpoints.csv" else filename), rows)
    return checked


def run(repo: Path, output: Path):
    repo, output = repo.resolve(), output.resolve()
    require(output != repo and not output.is_relative_to(repo / "data")
            and not output.is_relative_to(repo / "Solvers") and not output.is_relative_to(repo / "Loaders"),
            "Outputs must not overwrite bundled research data or code")
    output.mkdir(parents=True, exist_ok=True)
    records = {branch: _history(repo / "data" / "finite_rate", branch) for branch in BRANCHES}
    main = records["pi1600"]
    tan, tt, finite, linear = tangent(repo, main)
    target = json.loads((repo / "data" / "finite_rate" / "pi1600_analysis" / "METRICS.json").read_text())
    checks = []
    for key in ["T", "step", "S_lambda", "S_paired_zero", "C_lambda_saved", "C_paired_zero_saved",
                "delta_C_saved", "delta_C_from_fsum_differences", "delta_S_retained", "B_rep", "B_event",
                "restricted_retained_survival_change_trapezoids", "click_conditional_mean_lambda",
                "click_conditional_mean_zero", "click_conditional_mean_change", "rank"]:
        close(main["endpoint"][key], target["endpoint"][key], "Archived A127 endpoint " + key)
        checks.append("A127 endpoint " + key)
    for key in ["chi_D_from_panel_sum", "chi_D_from_survival", "linear_endpoint_prediction",
                "finite_endpoint_from_dp_sum", "finite_minus_linear_endpoint",
                "complete_panel_record_residual", "endpoint_relative_departure_percent"]:
        close(tan[key], target["tangent"][key], "Archived A127 tangent " + key)
        checks.append("A127 tangent " + key)
    close(main["endpoint"]["retained_signed_record_norm"], target["retained_signed_record_norm"], "A127 signed record norm")
    sign_indices = np.flatnonzero((main["dg"][:-1] * main["dg"][1:] < 0) & (main["mid"][:-1] >= 1.2))
    require(len(sign_indices) == target["number_post1p2_sign_changes"], "A127 adjacent-bin sign changes")
    table_cells = _a127_tables(main, repo / "data" / "finite_rate" / "pi1600_analysis", output)
    endpoints = [records[b]["endpoint"] for b in BRANCHES]
    table(output / "endpoints.csv", endpoints)
    scaling, scaling_curves = [], []
    for low, high in [("pi3200", "pi1600"), ("pi1600", "pi800")]:
        row, edges, small, large = _rate_comparison(records[low], records[high])
        row.update(low_branch=low, high_branch=high)
        scaling.append(row)
        scaling_curves.append((low, high, edges, small, large))
    table(output / "rate_scaling.csv", scaling)
    zero_checks = []
    stand = records["pi0"]
    for branch in BRANCHES[:-1]:
        record = records[branch]
        count = min(len(record["t"]), len(stand["t"])) - 1
        require(np.max(np.abs(record["t"][:count+1] - stand["t"][:count+1])) < 1e-12,
                "Standalone-zero common support")
        zero_checks.append({
            "branch": branch, "common_T": float(stand["t"][count]),
            "max_survival_difference": float(np.max(np.abs(record["h"]["zero_survival"][:count+1]
                                                           - stand["h"]["zero_survival"][:count+1]))),
            "native_click_l1_difference": total(np.abs(record["p0"][:count] - stand["p0"][:count])),
            "scope": "separate consistency comparison; standalone zero never replaces the paired zero",
        })
    table(output / "paired_zero_comparisons.csv", zero_checks)
    table(output / "tangent_panels.csv", [
        {"left": float(tt[j]), "right": float(tt[j+1]), "finite_delta_probability": float(finite[j]),
         "linear_delta_probability": float(linear[j])} for j in range(len(finite))])
    summary = {
        "check_scope": "New saved-observable/schema/metadata/reduction checks only; no simulations or spectrum/factor re-audit.",
        "source_method": "A127 analyze_native.py native-bin definitions and causal U2-I quadrature, portable adaptation.",
        "endpoints": endpoints, "tangent": tan, "common_support_rate_scaling": scaling,
        "standalone_zero_consistency": zero_checks,
        "ordered_loss_checks": {b: records[b]["ordered"] for b in BRANCHES},
        "policy_records": {b: records[b]["policy"] for b in BRANCHES},
        "schema": {b: {"array_count": len(records[b]["h"]), "node_count": len(records[b]["t"]),
                        "detector_bin_count": len(records[b]["p"])} for b in BRANCHES},
        "regression_checks": checks + ["A127 signed record norm", "A127 adjacent-bin sign changes", "A127 endpoint table", "A127 window table", "A127 sign-change table"],
        "table_regression_cells": table_cells,
        "historical_scientific_flags": {
            b: {k: records[b]["meta"][k] for k in ["physical_claim", "production_authorized", "task10_eligible"]
                if k in records[b]["meta"]} for b in BRANCHES
        },
        "not_rerun": ["production dynamics", "restart factors", "full historical compression spectra",
                      "archived VERIFICATION.json full audit"],
        "conventions": {
            "click_density": "native detector-bin probability / recorded detector dt; never differentiated survival",
            "mean": "conditional click mean uses native bin midpoints; restricted retained-survival integral is separate",
            "censoring": "unconditional finite-window record retains the no-detection atom",
            "losses": "representation and event losses are accounting terms; overflow and event-tail diagnostics are not extra sinks",
        },
    }
    dump(output / "summary.json", summary)
    np.savez_compressed(output / "finite_rate_arrays.npz", times=main["t"], midpoint_times=main["mid"],
                        delta_probability=main["dp"], delta_g=main["dg"], delta_C=main["dc"],
                        tangent_edges=tt, finite_delta_panels=finite, linear_delta_panels=linear)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    with plt.rc_context({"path.simplify": False, "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "savefig.dpi": 170}):
        fig = plt.figure(figsize=(11, 8))
        grid = fig.add_gridspec(2, 2, hspace=.4, wspace=.3)
        ax = fig.add_subplot(grid[0, :])
        ax.plot(main["mid"], main["dg"], color="#245c8d", lw=1.25)
        ax.axhline(0, color="0.45", lw=.7)
        ax.set(xlim=(0, main["t"][-1]), xlabel="Time", ylabel=r"$\Delta g_\lambda=(p_\lambda-p_0)/\Delta t$",
               title=r"Native roof-click response, $\lambda=\pi/1600$, own paired zero")
        ax.ticklabel_format(axis="y", style="sci", scilimits=(-3, 3))
        ax = fig.add_subplot(grid[1, 0])
        centers, widths = (tt[:-1]+tt[1:])/2, np.diff(tt)
        ax.plot(centers, finite/widths, color="#245c8d", label="Finite rate", lw=1.3)
        ax.plot(centers, linear/widths, color="#c25728", ls="--", label=r"$\lambda\,\chi_g$ (U2-I)", lw=1.2)
        ax.axhline(0, color="0.45", lw=.7)
        ax.set(xlim=(0, tt[-1]), xlabel="Time", ylabel="Panel-average response",
               title="Same 0.05-wide probability panels")
        ax.ticklabel_format(axis="y", style="sci", scilimits=(-3, 3))
        ax.legend(frameon=False)
        ax = fig.add_subplot(grid[1, 1])
        common_end = min(records[b]["t"][-1] for b in BRANCHES[:-1])
        count = min(len(records[b]["t"]) for b in BRANCHES[:-1])-1
        ids = np.unique(np.r_[np.arange(0, count+1, 100), count]).astype(int)
        edges = main["t"][ids]
        for b, color in [("pi3200", "#53955b"), ("pi1600", "#245c8d"), ("pi800", "#ad4b45")]:
            record = records[b]
            panels, _ = aggregate_native(record, edges, record["dp"])
            ax.plot((edges[:-1]+edges[1:])/2, panels/np.diff(edges)/record["rate"],
                    label=r"$\pi/"+b[2:]+r"$", color=color, lw=1.3)
        ax.axhline(0, color="0.45", lw=.7)
        ax.set(xlim=(0, common_end), xlabel="Time", ylabel=r"Panel response / $\lambda$",
               title=f"Three rates, common saved support to {common_end:g}")
        ax.legend(frameon=False)
        fig.text(.07, .015,
                 r"$\omega=100$, $N=12$, $N_z=1500$, mode 00, $\Delta t=0.0005$. "
                 "Native probabilities; no smoothing or extrapolation.\n"
                 "Each positive branch uses its own zero. Tangent/rate scaling is descriptive, not a convergence certificate.",
                 fontsize=8.5)
        fig.subplots_adjust(bottom=.12)
        fig.savefig(output / "finite_rate.png")
        plt.close(fig)
    return summary
