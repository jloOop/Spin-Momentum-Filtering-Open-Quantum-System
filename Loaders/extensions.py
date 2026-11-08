"""CPU reductions of archived extension observables; no propagation.

The input NPZ already contains a reduction of the three native T20 kernels.
This module does not claim to repeat that omitted kernel reconstruction.
The probability panel arrays are used directly; survival is never differenced
to manufacture click probabilities.
"""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import numpy as np


def _table(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _node(times, horizon):
    found = np.flatnonzero(np.isclose(times, horizon, rtol=0, atol=4e-15))
    if len(found) != 1:
        raise ValueError(f"Horizon {horizon} is not a unique saved node")
    return int(found[0])


def _stats(times, survival_response, panel_response, horizon):
    stop = _node(times, horizon)
    s = survival_response[:stop + 1]
    p = panel_response[:stop]
    # Same trapezoidal saved-node convention as archived analyze_mechanism.py.
    mu = np.sum(0.5 * (s[:-1] + s[1:]) * np.diff(times[:stop + 1]))
    return {
        "T": float(horizon),
        "chi_D_survival": float(-s[-1]),
        "chi_D_roof": float(np.sum(p)),
        "chi_mu_restricted": float(mu),
        "A_TV_with_censoring": float(0.5 * (np.sum(np.abs(p)) + abs(s[-1]))),
        "roof_plus_survival_residual": float(np.sum(p) + s[-1]),
    }


def run(repo: Path, output: Path) -> dict:
    repo, output = Path(repo).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(output / "mplconfig"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    data = repo / "data/extensions/horizon"
    configurations = {}
    for mode in ("00", "10", "01"):
        config = json.loads((data / "configurations" / f"mode{mode}.json").read_text())
        expected = {"initial_mode": mode, "environment_direction": "upward",
                    "propagator_type": "spinor", "omega": 144.0,
                    "N_shell": 12, "N_z": 1500, "dt": 0.00025,
                    "T_final": 20.0, "insertion_dt": 0.05, "num_steps": 80000}
        for key, value in expected.items():
            if config.get(key) != value:
                raise ValueError(f"Extension configuration mismatch: mode={mode}, {key}")
        configurations[mode] = expected
    with np.load(data / "reconstructed_arrays.npz", allow_pickle=False) as archive:
        times = archive["times"].copy()
        names = archive["preparation_names"].astype(str).tolist()
        survival = archive["chi_survival"].copy()
        panel = archive["chi_panel_probability"].copy()
    if times.ndim != 1 or len(times) != 401:
        raise ValueError("Expected the archived 401-node T20 response grid")
    if survival.shape != (len(names), len(times)) or panel.shape != (len(names), len(times) - 1):
        raise ValueError("Response node/panel shape contract failed")
    if not all(np.isfinite(a).all() for a in (times, survival, panel)):
        raise ValueError("Nonfinite saved extension arrays")
    if not np.allclose(np.diff(times), 0.05, rtol=0, atol=4e-15):
        raise ValueError("Unexpected response-panel grid; do not interpolate")
    if times[0] != 0 or times[-1] != 20:
        raise ValueError("Unexpected saved extension support")
    required = {"00", "10", "01", "first"}
    if not required.issubset(names):
        raise ValueError("Missing preparation components")
    series = {name: (survival[i], panel[i]) for i, name in enumerate(names)}
    for quantity in (0, 1):
        np.testing.assert_allclose(
            series["first"][quantity],
            0.5 * (series["10"][quantity] + series["01"][quantity]),
            rtol=0, atol=2e-14,
        )

    endpoint_rows = []
    table_error = 0.0
    compared = 0
    for row in _table(data / "tables/selected_horizons.csv"):
        name, horizon = row["preparation"], float(row["T"])
        if name not in series:
            raise ValueError(f"Unknown archived table preparation: {name}")
        computed = _stats(times, *series[name], horizon)
        for key in ("chi_D_survival", "chi_D_roof", "chi_mu_restricted", "A_TV_with_censoring"):
            error = abs(computed[key] - float(row[key]))
            table_error = max(table_error, error)
            if error > 1e-10:
                raise AssertionError(f"Archived endpoint mismatch: {name}, {horizon}, {key}, {error}")
            compared += 1
        endpoint_rows.append({"preparation": name, **computed})
    roots_table = {float(r["T"]): r for r in _table(data / "tables/mixture_crossings.csv")}
    mixtures = []
    mixture_series = {}
    for horizon in (10.0, 20.0):
        stop = _node(times, horizon)
        s0, p0 = series["00"]
        s1, p1 = series["first"]
        d0, d1 = -s0[stop], -s1[stop]
        if not d0 < 0 < d1:
            raise AssertionError("The selected endpoint does not bracket a mixture root")
        weight = float(-d0 / (d1 - d0))
        s_mix, p_mix = (1 - weight) * s0 + weight * s1, (1 - weight) * p0 + weight * p1
        stats = _stats(times, s_mix, p_mix, horizon)
        reference = float(roots_table[horizon]["p_star_survival"])
        if abs(weight - reference) > 1e-12:
            raise AssertionError("Mixture root disagrees with archived crossing table")
        if abs(stats["chi_D_survival"]) > 1e-13:
            raise AssertionError("Affine survival endpoint did not cancel")
        if stats["A_TV_with_censoring"] <= 0.1 or stats["chi_mu_restricted"] <= 0.1:
            raise AssertionError("Expected nonzero retained timing response is absent")
        mixtures.append({"first_shell_weight": weight, **stats})
        mixture_series[horizon] = (s_mix, p_mix)

    # Check T10 refined component values against the separate insertion review.
    fixed_path = repo / "data/extensions/preparation/fixed_preparations.csv"
    refinement_error = 0.0
    if not fixed_path.exists():
        raise FileNotFoundError(fixed_path)
    for row in _table(fixed_path):
        weight = float(row["p"])
        s = (1 - weight) * series["00"][0] + weight * series["first"][0]
        p = (1 - weight) * series["00"][1] + weight * series["first"][1]
        stats = _stats(times, s, p, 10.0)
        for key, column in (("chi_D_survival", "fine_chi_D_survival"),
                            ("chi_D_roof", "fine_chi_D_roof"),
                            ("chi_mu_restricted", "fine_chi_mu_native"),
                            ("A_TV_with_censoring", "fine_A_TV_native")):
            error = abs(stats[key] - float(row[column]))
            refinement_error = max(refinement_error, error)
            if error > 1e-10:
                raise AssertionError(f"Separate refinement-table mismatch: p={weight}, {key}")

    # Faithful saved-grid plotting: signed roof panels are staircase averages.
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.4), layout="constrained")
    colors = {"00": "#175b91", "first": "#b84e28"}
    for name, label in (("00", "ground 00"), ("first", "equal 10/01 mixture")):
        s, p = series[name]
        roof = np.r_[0.0, np.cumsum(p)]
        axes[0].plot(times, roof, color=colors[name], label=label, lw=1.7)
        axes[0].plot([10, 20], [-s[_node(times, 10)], -s[-1]], "o",
                     color=colors[name], markersize=4)
    axes[0].set(title="Preparation changes the integrated response",
                xlabel="Saved response-node time", ylabel=r"$\chi_D(T)$ per unit $\lambda_\uparrow$")
    axes[0].axvline(10, color="0.7", lw=0.8, ls=":")
    axes[0].legend(fontsize=9, loc="lower left")
    for horizon, color in ((20.0, "#19856a"), (10.0, "#6c4c94")):
        i = _node(times, horizon)
        _, p = mixture_series[horizon]
        row = next(r for r in mixtures if r["T"] == horizon)
        axes[1].stairs(p[:i] / np.diff(times[:i + 1]), times[:i + 1],
                       color=color, lw=1.3, linestyle="--" if horizon == 10 else "-",
                       label=f"T={horizon:g}, p*={row['first_shell_weight']:.4f}, "
                             + r"$\chi_{\mu^*}$=" + f"{row['chi_mu_restricted']:.3f}")
    axes[1].set(title="Zero terminal response retains timing structure",
                xlabel="Detector time (response panels of width 0.05)",
                ylabel=r"Panel-average $\chi_g$ per unit $\lambda_\uparrow$")
    axes[1].legend(fontsize=8.5, loc="upper left")
    for ax in axes:
        ax.axhline(0, color="0.2", lw=0.7)
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_xlim(0, 20)
    fig.suptitle(r"$\omega=144$, $N=12$, $N_z=1500$; detector step $0.00025$, response panels $0.05$",
                 fontsize=11)
    fig.savefig(output / "preparation_horizon.png", dpi=170)
    plt.close(fig)
    for filename, entries in (("extension_endpoints.csv", endpoint_rows),
                              ("mixture_cancellation.csv", mixtures)):
        with (output / filename).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(entries[0]))
            writer.writeheader()
            writer.writerows(entries)
    summary = {
        "analysis_scope": "Reduction/replot of archived derived response arrays; native kernels and simulations not rerun",
        "input": "data/extensions/horizon/reconstructed_arrays.npz",
        "saved_support": [float(times[0]), float(times[-1])],
        "response_nodes": len(times),
        "response_panel_width": 0.05,
        "detector_step": configurations["00"]["dt"],
        "configuration_contracts": configurations,
        "historical_scientific_acceptance": False,
        "packaging_checks": {
            "three_native_configuration_contracts": "passed",
            "finite_arrays_and_schema": "passed",
            "saved_first_shell_mixture_identity": "passed",
            "selected_horizons_comparisons": compared,
            "max_abs_archived_table_difference": table_error,
            "max_abs_separate_refinement_table_difference": refinement_error,
            "mixture_root_comparison": "passed",
        },
        "mixtures": mixtures,
        "omitted_capabilities": [
            "Native causal-kernel reconstruction and full original review require omitted inputs",
            "Excited-state detector-step, shell and longitudinal convergence are not newly established",
            "Finite-rate continuation at omega144 was not performed",
        ],
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary
