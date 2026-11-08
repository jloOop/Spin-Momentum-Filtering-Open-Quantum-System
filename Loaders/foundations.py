"""Bounded CPU reductions of bundled static, oscillator and bath-only records.

Reads saved arrays only; does not import or run any archived solver or loader.
Static finite-window statistics use native midpoint roof-bin probabilities.
Operator checks retain the recorded finite-shell commutator corrections.
Bath checks compare stored observables with archived metric tables; they are
not a new bath propagator or a rerun of all historical independent checks.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _maxabs(value):
    return float(np.max(np.abs(value))) if np.size(value) else 0.0


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _save_csv(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def _static(base, output):
    references = {(float(r["omega"]), r["detector"], r["mode"]): r
                  for r in _read_csv(base / "Stage01_complete_case_metrics.csv")}
    rows, plot_arrays = [], []
    for cfg_path in sorted(base.glob("*/*_configuration.json")):
        cfg = json.loads(cfg_path.read_text())
        prefix = cfg_path.name.removesuffix("_configuration.json")
        times = np.load(cfg_path.with_name(prefix + "_times.npy"), allow_pickle=False)
        survival = np.load(cfg_path.with_name(prefix + "_survival.npy"), allow_pickle=False)
        roof = np.load(cfg_path.with_name(prefix + "_step_loss_roof_midpoint.npy"), allow_pickle=False)
        _require(times.ndim == survival.ndim == roof.ndim == 1, "Static arrays must be vectors")
        _require(times.size == survival.size == roof.size + 1, "Static state/bin schema mismatch")
        _require(np.all(np.diff(times) > 0), "Static time grid is not increasing")
        _require(all(np.all(np.isfinite(a)) for a in (times, survival, roof)), "Nonfinite static data")
        _require(np.isclose(times[-1], cfg["T_final"], rtol=0, atol=2e-12), "Static horizon mismatch")
        _require(np.allclose(np.diff(times), cfg["dt"], rtol=0, atol=2e-12), "Static detector step mismatch")
        mode = cfg["mode_basis_audit"]["selected_mode"]
        key = (float(cfg["omega"]), cfg["detector"], mode)
        reference = references[key]
        mids = (times[1:] + times[:-1]) / 2
        detected = float(np.sum(roof, dtype=np.float64))
        row = dict(omega=key[0], detector=key[1], mode=mode, T=float(times[-1]),
                   detector_dt=float(cfg["dt"]), state_nodes=len(times), roof_bins=len(roof),
                   S_T=float(survival[-1]), D_roof=detected,
                   mu=float(np.trapezoid(survival, times)),
                   cond_mean=float(np.dot(mids, roof) / detected),
                   D_E=float(np.sum(roof[mids < 3.6])),
                   D_L=float(np.sum(roof[mids >= 3.6])),
                   roof_survival_accounting_residual=float(survival[0] - survival[-1] - detected),
                   minimum_native_roof_bin=float(np.min(roof)))
        # The historical Stage01 table normalizes by each recorded initial norm.
        # Retain raw metrics and expose normalized metrics separately; arrays are unchanged.
        row["initial_survival"] = float(survival[0])
        _require(row["initial_survival"] > 0, "Nonpositive initial survival")
        for stat_name in ("S_T", "D_roof", "mu", "D_E", "D_L"):
            row["normalized_" + stat_name] = row[stat_name] / row["initial_survival"]
        differences = [abs(row["normalized_" + k] - float(reference[k]))
                       for k in ("S_T", "D_roof", "mu", "D_E", "D_L")]
        differences.append(abs(row["cond_mean"] - float(reference["cond_mean"])))
        row["maximum_stored_metric_difference"] = max(differences)
        _require(max(differences) <= 5e-12, f"Static saved-metric mismatch: {cfg_path.parent.name}")
        rows.append(row)
        plot_arrays.append((key, times, survival, roof))
    expected = {(w, d, m) for w in (1.0, 100.0) for d in ("scalar", "spinor") for m in ("00", "10", "01")}
    _require({(r["omega"], r["detector"], r["mode"]) for r in rows} == expected, "Static 12-case cohort is incomplete")
    _save_csv(output / "static_summary.csv", rows)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(9, 6.4), sharex=True, constrained_layout=True)
    colors = {"00": "#205b8d", "10": "#bf573b", "01": "#278564"}
    for (omega, detector, mode), times, survival, roof in plot_arrays:
        row, column = (0 if detector == "scalar" else 1), (0 if omega == 1 else 1)
        axes[row, column].plot(times, survival, color=colors[mode], lw=1.3,
                               ls=":" if mode == "01" else "-", label="mode " + mode)
        axes[row, column].set_title(f"{detector}; ω={omega:g}")
    for ax in axes.flat:
        ax.grid(alpha=.2); ax.set_ylabel("Survival S(t)"); ax.set_xlim(0, 10)
    for ax in axes[-1]:
        ax.set_xlabel("Time t/t₀")
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("Static preparation records · saved survival (native roof-bin metrics in CSV)", fontsize=11)
    fig.savefig(output / "static_preparation.png", dpi=170)
    plt.close(fig)
    return rows


def _operators(base):
    with np.load(base / "Stage02_authoritative_operators.npz", allow_pickle=False) as data:
        operators = {k: data[k] for k in data.files}
    ax, ay = operators["a_x"], operators["a_y"]
    adx, ady = operators["a_x_dagger"], operators["a_y_dagger"]
    checks = {
        "a_x_adjoint": _maxabs(adx - ax.conj().T),
        "a_y_adjoint": _maxabs(ady - ay.conj().T),
        "number_x": _maxabs(operators["N_x"] - adx @ ax),
        "number_y": _maxabs(operators["N_y"] - ady @ ay),
        "number_total": _maxabs(operators["N_perp"] - operators["N_x"] - operators["N_y"]),
        "finite_shell_commutator_x": _maxabs(ax @ adx - adx @ ax - operators["expected_commutator_x"]),
        "finite_shell_commutator_y": _maxabs(ay @ ady - ady @ ay - operators["expected_commutator_y"]),
        "finite_shell_cross_commutator": _maxabs(ax @ ady - ady @ ax - operators["expected_commutator_ax_aydagger"]),
    }
    for omega in (1, 100):
        k = operators[f"K_omega_{omega}"]
        checks[f"K_omega_{omega}_hermiticity"] = _maxabs(k - k.conj().T)
    _require(max(checks.values()) <= 5e-12, "Saved finite-shell operator identity failed")
    return checks


def _bath(base, output):
    reference = {r["case_id"]: r for r in _read_csv(base / "Stage03_case_metrics.csv")}
    with np.load(base / "Stage03_time_series.npz", allow_pickle=False) as data:
        rows = []
        for key in sorted(k for k in data.files if k.endswith("__trace")):
            name = key.removesuffix("__trace")
            times = data[name + "__t"]
            trace = data[key]
            occupation = data[name + "__occupation_total"]
            purity = data[name + "__purity"]
            _require(np.all(np.diff(times) > 0), "Bath time grid is not increasing")
            _require(all(np.all(np.isfinite(a)) for a in (times, trace, occupation, purity)), "Nonfinite bath observable")
            saved = reference[name]
            row = dict(case_id=name, T=float(times[-1]), nodes=int(times.size),
                       final_occupation_total=float(occupation[-1]), final_purity=float(purity[-1]),
                       maximum_trace_error=_maxabs(trace - 1))
            for field in ("final_occupation_total", "final_purity", "maximum_trace_error"):
                _require(abs(row[field] - float(saved[field])) <= 5e-12, f"Bath saved-metric mismatch: {name}/{field}")
            rows.append(row)
    _require(len(rows) > 0, "No native bath observable records found")
    _save_csv(output / "bath_observables.csv", rows)
    return rows


def run(repo: Path, output: Path):
    repo, output = Path(repo), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    base = repo / "data/foundations"
    static = _static(base / "static", output)
    operators = _operators(base / "operators/4050.Bath_operator_tests")
    bath = _bath(base / "bath_only/4060.Bath_only_tests", output)
    result = {
        "group": "foundations", "status": "passed",
        "scope": "Saved-array reductions and selected algebra/metric regressions; no production solver or full historical independent audit executed",
        "static_cases": len(static),
        "static_maximum_saved_metric_difference": max(r["maximum_stored_metric_difference"] for r in static),
        "static_maximum_roof_survival_residual": max(abs(r["roof_survival_accounting_residual"]) for r in static),
        "operator_residuals": operators,
        "bath_observable_cases": len(bath),
        "definitions": {
            "D_roof": "sum of stored native midpoint roof-bin probabilities",
            "mu": "restricted mean: trapezoidal integral of stored survival on state-node times",
            "cond_mean": "mean of detected trials: native roof-bin midpoint-weighted sum / D_roof",
            "early_late_boundary": 3.6,
            "normalization": "Raw statistics retained; normalized_* divides by recorded S(0) solely to match historical Stage01 CSV; original arrays unchanged",
            "accounting": "independent roof and survival records preserved; no forced equality",
            "finite_shell_algebra": "truncated-basis boundary corrections retained, not replaced by infinite-dimensional identity",
        },
    }
    (output / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result
