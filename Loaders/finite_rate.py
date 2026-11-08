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
    denominator = 2 * total(small)
    guard = max(1e-12, 1e-6 * float(np.max(np.abs(2 * np.cumsum(low["dp"][:count])))))
    meaningful = abs(denominator) > guard
    row = {
        "low_rate": low["rate"], "high_rate": high["rate"], "common_T": float(endpoint),
        "common_native_intervals": count, "panels": len(edges) - 1,
        "low_delta_click": total(small), "high_delta_click": total(large),
        "high_over_twice_low_endpoint": total(large) / denominator if meaningful else None,
        "absolute_endpoint_residual": abs(total(large) - denominator),
        "endpoint_ratio_denominator_guard": guard, "endpoint_denominator_meaningful": meaningful,
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


RATES = ("pi3200", "pi1600", "pi800")
POSTER_ENDS = {"pi3200": 5.65, "pi1600": 8.3, "pi800": 3.6}
COLORS = {"pi3200": "#398653", "pi1600": "#2767a1", "pi800": "#bf5045"}


def _node(record, horizon):
    index = round(horizon / record["dt"])
    require(0 <= index < len(record["t"]), "Requested horizon exceeds saved support")
    close(record["t"][index], horizon, "Exact native horizon", atol=1e-12, rtol=0)
    return index


def _native_cumulative(record):
    # Add measured roof increments, never infer roof clicks from retained survival.
    return np.r_[0., np.cumsum(record["dp"])]


def _three_rate_tables(records, output):
    matched, doubling, windows, sign_runs, changes, observations = [], [], [], [], [], {}
    horizons = (3.6, 3.825, 5.65, 6., 8.3, 10.)
    for branch in RATES:
        r = records[branch]
        dc = _native_cumulative(r)
        for horizon in horizons:
            row = {"branch": branch, "T": horizon, "saved_T": float(r["t"][-1]),
                   "supported": bool(horizon <= r["t"][-1] + 1e-12)}
            if row["supported"]:
                j = _node(r, horizon)
                row.update(C_lambda_native_fsum=total(r["p"][:j]),
                           C_paired_zero_native_fsum=total(r["p0"][:j]),
                           delta_C_native_fsum=total(r["dp"][:j]),
                           delta_C_saved=float(r["dc"][j]),
                           B_rep=float(r["h"]["representation_ledger"][j]),
                           B_event=float(r["h"]["event_first_crossing_ledger"][j]))
            matched.append(row)
        signs = np.sign(r["dg"])
        breaks = np.r_[0, np.flatnonzero(signs[1:] != signs[:-1]) + 1, len(signs)]
        runs = []
        for i, j in zip(breaks[:-1], breaks[1:]):
            run = {"branch": branch, "start": float(r["t"][i]), "end": float(r["t"][j]),
                   "first_bin": int(i), "last_bin": int(j-1), "sign": int(signs[i]),
                   "max_abs_delta_g": float(np.max(np.abs(r["dg"][i:j]))),
                   "net_response_mass": total(r["dp"][i:j])}
            run["resolves_1e_minus10_display_threshold"] = run["max_abs_delta_g"] >= 1e-10
            runs.append(run)
            sign_runs.append(run)
        for left, right in zip(runs[:-1], runs[1:]):
            if (left["sign"] * right["sign"] < 0
                    and left["resolves_1e_minus10_display_threshold"]
                    and right["resolves_1e_minus10_display_threshold"]):
                changes.append({"branch": branch,
                                "direction": "negative_to_positive" if left["sign"] < 0 else "positive_to_negative",
                                "left_midpoint": float(r["mid"][left["last_bin"]]),
                                "right_midpoint": float(r["mid"][right["first_bin"]]),
                                "display_amplitude_threshold": 1e-10,
                                "interpretation": "adjacent native-bin bracket; no interpolated root or uncertainty bound"})
        minimum = int(np.argmin(dc))
        chosen = [(0., 3.6, "launch_to_3.6"), (3.6, 6., "3.6_to_6"),
                  (6., 8.3, "6_to_8.3"), (6., 10., "6_to_10"), (8.3, 10., "8.3_to_10"),
                  (0., float(r["t"][-1]), "launch_to_saved_endpoint"),
                  (3.6, float(r["t"][-1]), "3.6_to_saved_endpoint"),
                  (float(r["t"][minimum]), float(r["t"][-1]), "cumulative_minimum_to_saved_endpoint")]
        chosen += [(run["start"], run["end"], "positive_native_sign_run") for run in runs
                   if run["sign"] > 0 and run["resolves_1e_minus10_display_threshold"]]
        for start, end, name in chosen:
            available = end > start and end <= r["t"][-1] + 1e-12
            row = {"branch": branch, "window": name, "start": start, "end": end,
                   "fully_available": bool(available)}
            if available:
                i, j = _node(r, start), _node(r, end)
                dp = r["dp"][i:j]
                row.update(positive_mass=total(dp[dp > 0]), negative_mass_signed=total(dp[dp < 0]),
                           net_mass=total(dp), delta_C_at_start=total(r["dp"][:i]),
                           delta_C_at_end=total(r["dp"][:j]))
            windows.append(row)
        observations[branch] = {
            "saved_T": float(r["t"][-1]), "minimum_delta_C": total(r["dp"][:minimum]),
            "minimum_delta_C_time": float(r["t"][minimum]), "endpoint_delta_C": total(r["dp"]),
            "change_from_minimum_to_endpoint": total(r["dp"][minimum:]),
            "final_bin_delta_g": float(r["dg"][-1]),
            "cumulative_negative_at_every_saved_node_from_t1": bool(np.all(dc[r["t"] >= 1.] < 0)),
            "resolved_positive_native_sign_runs": sum(run["sign"] > 0 and run["resolves_1e_minus10_display_threshold"] for run in runs),
            "display_threshold_scope": "Historical 1e-10 amplitude filter suppresses tiny launch sign noise; it is not a numerical error bar.",
        }
    for low, high in [("pi3200", "pi1600"), ("pi1600", "pi800")]:
        a, b = records[low], records[high]
        count = min(len(a["p"]), len(b["p"]))
        require(np.array_equal(a["t"][:count+1], b["t"][:count+1]), "Identical doubling time grid")
        threshold = max(1e-12, 1e-6 * float(np.max(np.abs(2 * _native_cumulative(a)[:count+1]))))
        common_end = float(a["t"][count])
        for horizon in horizons[:4]:
            row = {"low_branch": low, "high_branch": high, "T": horizon, "common_saved_T": common_end,
                   "supported": horizon <= common_end + 1e-12, "denominator_guard": threshold,
                   "definition": "fsum(delta_p_high)/(2*fsum(delta_p_low)); each uses own paired zero"}
            if row["supported"]:
                j = _node(a, horizon)
                low_dc, high_dc = total(a["dp"][:j]), total(b["dp"][:j])
                meaningful = abs(2 * low_dc) > threshold
                residual = high_dc - 2 * low_dc
                row.update(low_delta_C=low_dc, high_delta_C=high_dc, signed_residual_Q_C=residual,
                           absolute_residual=abs(residual), denominator_meaningful=meaningful,
                           R=high_dc / (2 * low_dc) if meaningful else None,
                           absolute_deviation_percent=100 * abs(high_dc/(2*low_dc)-1) if meaningful else None)
            doubling.append(row)
    for filename, rows in [("matched_horizons.csv", matched), ("integrated_rate_doubling.csv", doubling),
                           ("response_mass_windows.csv", windows), ("native_sign_runs.csv", sign_runs),
                           ("significant_sign_changes.csv", changes)]:
        table(output / filename, rows)
    return {"matched_horizons": matched, "integrated_rate_doubling": doubling,
            "native_sign_observations": observations,
            "sign_threshold": "Display filter inherited from Sofat; no scientific acceptance or convergence decision."}


def _poster_regression(records, references, output):
    """Historical cutoffs of verified continuation prefixes; small archived targets only."""
    target = json.loads((references / "integrated_rate_doubling_T5p65_recomputed.json").read_text())
    close(target["common_horizon"], 5.65, "Sofat target horizon", rtol=0)
    close(target["dt"], records["pi3200"]["dt"], "Sofat target detector step", rtol=0)
    require(target["native_bin_count"] == _node(records["pi3200"], 5.65), "Sofat native bin count")
    # Preserve the explicitly recomputed fsum statistic, distinct from old C-C0 arithmetic.
    fsum_values = {}
    checked = 0
    for branch in ("pi3200", "pi1600"):
        r, saved = records[branch], target["rates"][branch]
        j = _node(r, 5.65)
        values = {"positive_roof_mass_fsum": total(r["p"][:j]),
                  "paired_zero_roof_mass_fsum": total(r["p0"][:j]),
                  "delta_C_native_increment_fsum": total(r["dp"][:j]),
                  "delta_C_saved_cumulative_difference": float(r["dc"][j])}
        values["crosscheck_difference"] = values["delta_C_native_increment_fsum"] - values["delta_C_saved_cumulative_difference"]
        for key, value in values.items():
            close(value, saved[key], "Sofat fsum " + branch + "/" + key, atol=2e-14, rtol=0)
            checked += 1
        fsum_values[branch] = values
    low = fsum_values["pi3200"]["delta_C_native_increment_fsum"]
    high = fsum_values["pi1600"]["delta_C_native_increment_fsum"]
    ratio, residual = high / (2 * low), high - 2 * low
    # Field names follow the archived explicit recomputation JSON.
    for key, value in [("doubling_ratio", ratio), ("absolute_deviation_percent", 100*abs(ratio-1)),
                       ("relative_signed_deviation_percent", 100*(ratio-1)), ("high_over_low", high/low),
                       ("Q_C", residual)]:
        close(value, target[key], "Sofat unrounded " + key, atol=2e-12 if key != "Q_C" else 2e-14, rtol=0)
        checked += 1
    cells = 0
    for filename in ("endpoints.csv", "matched_horizons.csv", "response_mass_windows.csv", "rate_scaling.csv"):
        with (references / filename).open(newline="", encoding="utf-8") as source:
            stored_rows = list(csv.DictReader(source))
        for stored in stored_rows:
            branch = stored.get("rate", stored.get("low"))
            r = records[branch]
            # The source tables use separately accumulated C and C0, then subtract.
            c, c0 = np.r_[0., np.cumsum(r["p"])], np.r_[0., np.cumsum(r["p0"])]
            dc = c - c0
            if filename in ("endpoints.csv", "matched_horizons.csv"):
                horizon = float(stored["T"])
                require(horizon <= POSTER_ENDS[branch] + 1e-12, "Historical table inside declared cutoff")
                j = _node(r, horizon)
                values = {"S": r["h"]["positive_survival"][j], "S0_paired": r["h"]["zero_survival"][j],
                          "C": c[j], "C0_paired": c0[j], "delta_C": dc[j],
                          "delta_C_relative_percent": 100 * dc[j] / c0[j],
                          "B_rep": r["h"]["representation_ledger"][j], "B_event": r["h"]["event_first_crossing_ledger"][j]}
            elif filename == "response_mass_windows.csv":
                if stored["fully_available"] != "True":
                    continue
                i, j = _node(r, float(stored["start"])), _node(r, float(stored["end"]))
                require(r["t"][j] <= POSTER_ENDS[branch] + 1e-12, "Historical window cutoff")
                dp = r["dp"][i:j]
                values = {"positive_mass": total(dp[dp > 0]), "negative_mass_signed": total(dp[dp < 0]),
                          "negative_mass_magnitude": -total(dp[dp < 0]), "net_mass": total(dp),
                          "delta_C_endpoint_difference": dc[j] - dc[i]}
            else:
                high_record = records[stored["high"]]
                n = _node(r, min(POSTER_ENDS[branch], POSTER_ENDS[stored["high"]]))
                high_dc = np.r_[0., np.cumsum(high_record["p"])] - np.r_[0., np.cumsum(high_record["p0"])]
                j = _node(r, float(stored["T"]))
                require(j <= n, "Historical doubling common support")
                threshold = max(1e-12, 1e-6 * float(np.max(np.abs(2*dc[:n+1]))))
                qg = high_record["dg"][:n] - 2 * r["dg"][:n]
                values = {"Q_C": high_dc[j] - 2*dc[j], "delta_C_high_over_2low": high_dc[j]/(2*dc[j]),
                          "C_ratio_denominator_threshold": threshold,
                          "full_common_endpoint": float(r["t"][n]),
                          "max_abs_Q_g_full_common_support": float(np.max(np.abs(qg)))}
            for key, value in values.items():
                close(value, float(stored[key]), "Sofat " + filename + "/" + key, atol=2e-12, rtol=1e-10)
                cells += 1
    result = {"historical_cutoffs": POSTER_ENDS, "source": "poster_provenance/ archived Sofat targets",
              "prefix_basis": "All 27 native arrays per branch verified as exact continuation prefixes in prefix_verification.json; no independent run implied.",
              "fsum_values": fsum_values, "doubling_ratio": ratio,
              "absolute_deviation_percent": 100*abs(ratio-1), "signed_residual_Q_C": residual,
              "scalar_regressions": checked, "table_cells": cells,
              "tolerances": {"fsum_absolute": 2e-14, "ratio_absolute": 2e-12,
                             "historical_table_absolute": 2e-12, "historical_table_relative": 1e-10},
              "poster_printed_ratio": "approximately 0.9992; historical display retained, not conventional 4-decimal rounding",
              "scope": "Saved-observable regression and historical cutoff reconstruction only; no solver or complete finite-rate convergence audit."}
    dump(output / "poster_regression.json", result)
    return result


def _figures(records, tt, linear, main_rate, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    with plt.rc_context({"path.simplify": False, "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "savefig.dpi": 170}):
        def label(branch, end):
            return rf"$\lambda=\pi/{branch[2:]}$; $T={end:g}$"

        def native_figure(filename, cutoffs, title):
            fig, axes = plt.subplots(2, 1, figsize=(11, 7.2), gridspec_kw={"height_ratios": [1.25, 1.]})
            for branch in RATES:
                r, end = records[branch], cutoffs[branch]
                n = _node(r, end)
                for ax in axes:
                    ax.plot(r["mid"][:n], r["dg"][:n], color=COLORS[branch], lw=1.2, label=label(branch, end))
                    ax.plot(r["mid"][n-1], r["dg"][n-1], ".", color=COLORS[branch], ms=5)
            xmax = max(cutoffs.values())
            for ax in axes:
                ax.axhline(0, color="0.45", lw=.7)
                ax.set(xlabel="Time", ylabel=r"$\Delta g_\lambda=(p_\lambda-p_{0,\lambda})/\Delta t$")
                ax.ticklabel_format(axis="y", style="sci", scilimits=(-3, 3))
            axes[0].set(xlim=(0, xmax + .07), title=title)
            axes[0].legend(frameon=False, ncols=3, loc="lower right", fontsize=9)
            # Magnify the late native bins without discarding or smoothing samples.
            late_values = np.concatenate([records[b]["dg"][(records[b]["mid"] >= 3.4)
                              & (records[b]["mid"] < cutoffs[b])] for b in RATES])
            lo, hi = min(float(np.min(late_values)), 0.), max(float(np.max(late_values)), 0.)
            pad = .1 * (hi - lo)
            axes[1].set(xlim=(3.4, xmax+.07), ylim=(lo-pad, hi+pad), title="Late-time detail: positive density windows do not imply positive cumulative change")
            fig.text(.08, .025, r"$\omega=100$, $N=12$, $N_z=1500$, mode 00, upward bath; $\Delta t=0.0005$. "
                     "Each rate uses its own paired zero.\nEvery saved detector bin is shown; markers mark final-bin midpoints (T minus half a step). No smoothing or extrapolation.", fontsize=8.5)
            fig.subplots_adjust(hspace=.45, bottom=.15, left=.1, right=.97, top=.95)
            fig.savefig(output / filename)
            plt.close(fig)

        native_figure("finite_rate.png", {b: float(records[b]["t"][-1]) for b in RATES},
                      "Task09 finite-rate roof-click response — extended saved histories")
        native_figure("finite_rate_poster.png", POSTER_ENDS,
                      "Poster-era support — exact prefixes of the selected histories")
        fig, axes = plt.subplots(2, 1, figsize=(11, 7.2), gridspec_kw={"height_ratios": [1.3, 1.]})
        for branch in RATES:
            r, dc = records[branch], _native_cumulative(records[branch])
            for ax in axes:
                ax.plot(r["t"], dc, color=COLORS[branch], lw=1.4, label=label(branch, r["t"][-1]))
                ax.plot(r["t"][-1], dc[-1], ".", color=COLORS[branch], ms=5)
        for ax in axes:
            ax.axhline(0, color="0.45", lw=.7)
            ax.set(xlabel="Time", ylabel=r"$\Delta C_\lambda(T)=\sum_{t_{n+1}\leq T}(p_\lambda-p_{0,\lambda})$")
            ax.ticklabel_format(axis="y", style="sci", scilimits=(-3, 3))
        axes[0].set(xlim=(0, 10.07), title="Cumulative roof-click change from launch — full saved support")
        axes[0].legend(frameon=False, ncols=3, fontsize=9)
        axes[1].set(xlim=(3.4, 10.07), ylim=(-.00115, -.0003), title="Late detail for the two lower rates (high-rate curve remains below this zoom)")
        fig.text(.09, .025, "Own paired zeros; cumulative sums of native roof-probability differences. Late positive increments can reduce an earlier deficit.\n"
                 "All three cumulative changes remain negative at saved nodes from t=1. Native floating-point sums are not forced to close.", fontsize=8.5)
        fig.subplots_adjust(hspace=.45, bottom=.15, left=.1, right=.97, top=.95)
        fig.savefig(output / "finite_rate_cumulative.png")
        plt.close(fig)
        fig, axes = plt.subplots(2, 1, figsize=(11, 7.5))
        panel_rows = []
        chi_p = linear / main_rate
        for branch in RATES:
            r = records[branch]
            axes[0].plot(r["mid"], r["dg"]/r["rate"], color=COLORS[branch], lw=1.15,
                         label=label(branch, r["t"][-1]))
            axes[0].plot(r["mid"][-1], r["dg"][-1]/r["rate"], ".", color=COLORS[branch], ms=5)
            # Only whole tangent panels whose endpoints exist in the finite history.
            edge_count = int(np.count_nonzero(tt <= r["t"][-1] + 1e-12))
            edges = tt[:edge_count]
            panels, _ = aggregate_native(r, edges, r["dp"])
            widths = np.diff(edges)
            centers = (edges[:-1] + edges[1:])/2
            residual = panels/r["rate"] - chi_p[:len(panels)]
            axes[1].plot(centers, residual/widths, color=COLORS[branch], lw=1.3,
                         label=rf"$\pi/{branch[2:]}$; panels through {edges[-1]:g}")
            for j in range(len(panels)):
                panel_rows.append({"branch": branch, "left": float(edges[j]), "right": float(edges[j+1]),
                                   "finite_panel_probability": float(panels[j]),
                                   "finite_density_over_lambda": float(panels[j]/widths[j]/r["rate"]),
                                   "chi_g_panel_average": float(chi_p[j]/widths[j]),
                                   "normalized_density_residual": float(residual[j]/widths[j])})
        for ax in axes:
            ax.axhline(0, color="0.45", lw=.7)
            ax.set(xlim=(0, 10.07), xlabel="Time")
            ax.legend(frameon=False, ncols=3, fontsize=9)
        axes[0].set(ylabel=r"Native $\Delta g_\lambda/\lambda$", title="Rate-normalized response — each curve ends at its own saved endpoint")
        axes[1].set(ylabel=r"Panel $(\Delta g_\lambda/\lambda)-\chi_g$", title="Departure from U2-I tangent on matched 0.05-wide probability panels")
        axes[1].ticklabel_format(axis="y", style="sci", scilimits=(-3, 3))
        fig.text(.09, .025, "Top: every native detector bin. Bottom: sum fine probability bins before dividing by panel width and rate; tangent is per unit rate.\n"
                 "The pi/800 comparison ends at 3.8 (last complete tangent panel); its native history ends at 3.825. Descriptive, not a convergence certificate.", fontsize=8.5)
        fig.subplots_adjust(hspace=.45, bottom=.15, left=.1, right=.97, top=.95)
        fig.savefig(output / "finite_rate_normalized.png")
        plt.close(fig)
        table(output / "three_rate_tangent_panels.csv", panel_rows)


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
    three_rate = _three_rate_tables(records, output)
    poster = _poster_regression(records, repo / "data" / "finite_rate" / "poster_provenance", output)
    summary = {
        "three_rate": three_rate, "poster_regression": poster,
        "check_scope": "New saved-observable/schema/metadata/reduction checks only; no simulations or spectrum/factor re-audit.",
        "source_method": "A127 analyze_native.py native-bin definitions and causal U2-I quadrature; Sofat analyze.py historical cutoffs and native-sum comparisons, portable adaptations.",
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
    _figures(records, tt, linear, main["rate"], output)
    return summary
