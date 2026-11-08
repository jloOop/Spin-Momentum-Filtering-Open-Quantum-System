"""CPU reconstruction of the 18 canonical zero-rate response records.

Adapted numerical reduction only (no solver execution) from the archived
Task07 independent case loader: prefix_trapezoid_weights and
reconstruct_response_from_kernel; and stage07_full_analysis.py:
summarize_response / compare_complete_signed. The archives retain the full
historical implementations and their attribution/status.

The independent roof and survival records are compared, never overwritten.
Tolerances below test reconstruction of saved products, not convergence.
"""
from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path

import numpy as np

ROLES = {f"{c}{n}" for c in "DUP" for n in range(1, 6)} | {"D2-I", "U2-I", "P2-I"}
ARRAY_TOL = 5e-12  # Saved-array reconstruction tolerance in the original case loader.


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _member(archive, suffix):
    names = [n for n in archive.namelist() if n.endswith(suffix)]
    _require(len(names) == 1, f"Expected one member ending {suffix}: {names}")
    return names[0]


def _npz(archive, suffix):
    with np.load(io.BytesIO(archive.read(_member(archive, suffix))), allow_pickle=False) as data:
        return {key: data[key] for key in data.files}


def _npy(archive, suffix):
    return np.load(io.BytesIO(archive.read(_member(archive, suffix))), allow_pickle=False)


def _maxabs(array):
    return float(np.max(np.abs(array))) if np.size(array) else 0.0


def _assert_near(actual, expected, label, atol=ARRAY_TOL):
    difference = _maxabs(np.asarray(actual) - np.asarray(expected))
    _require(difference <= atol, f"{label}: saved-product difference {difference:.8g} > {atol}")
    return difference


def prefix_trapezoid_weights(times, endpoint_index):
    """Original prefix quadrature; endpoint weight depends on causal support."""
    if endpoint_index == 0:
        return np.zeros(1, dtype=np.float64)
    selected = np.asarray(times[: endpoint_index + 1], dtype=np.float64)
    weights = np.zeros(selected.size, dtype=np.float64)
    weights[0] = 0.5 * (selected[1] - selected[0])
    weights[-1] = 0.5 * (selected[-1] - selected[-2])
    if selected.size > 2:
        weights[1:-1] = 0.5 * (selected[2:] - selected[:-2])
    return weights


def reconstruct_response_from_kernel(insertion_times, kernel_probability, kernel_survival):
    """Original Task07 causal orientation: [output panel/node, insertion]."""
    panels, nodes = kernel_probability.shape
    _require(nodes == panels + 1, "Kernel must have one more insertion than output panel")
    _require(kernel_survival.shape == (nodes, nodes), "Survival-kernel shape mismatch")
    chi_survival = np.zeros(nodes, dtype=np.float64)
    chi_panel_probability = np.zeros(panels, dtype=np.float64)
    for state_index in range(nodes):
        weights = prefix_trapezoid_weights(insertion_times, state_index)
        chi_survival[state_index] = float(
            np.dot(weights, kernel_survival[state_index, : state_index + 1])
        )
    for panel in range(panels):
        weights = prefix_trapezoid_weights(insertion_times, panel + 1)
        chi_panel_probability[panel] = float(
            np.dot(weights[: panel + 1], kernel_probability[panel, : panel + 1])
        )
    return chi_survival, chi_panel_probability, chi_panel_probability / np.diff(insertion_times)


def _read_case(repo, index_row, registered):
    path = repo / index_row["distributed_path"]
    _require(path.resolve().is_relative_to(repo.resolve()), "Case path leaves checkout")
    _require(index_row["original_sha256"] == registered["case_zip_sha256"],
             "Case selection identity does not match canonical register")
    with zipfile.ZipFile(path) as archive:
        configuration = json.loads(archive.read(_member(archive, "_configuration.json")))
        kernel = _npz(archive, "_kernel_summary.npz")
        compact = _npz(archive, "_case_loader_compact.npz")
        source = _npz(archive, "_source_insertion_summary.npz")
        # "_times.npy" also matches insertion_times; disambiguate explicitly.
        names = [n for n in archive.namelist() if n.endswith("_times.npy") and not n.endswith("_insertion_times.npy")]
        _require(len(names) == 1, "Ambiguous state-node times")
        times = np.load(io.BytesIO(archive.read(names[0])), allow_pickle=False)
        insertion = _npy(archive, "_insertion_times.npy")
        stored_s = _npy(archive, "_chi_survival.npy")
        stored_g = _npy(archive, "_chi_click_density.npy")
        integrated = json.loads(archive.read(_member(archive, "_integrated_response.json")))

    nodes = len(times)
    panels = nodes - 1
    durations = np.diff(times)
    _require(nodes >= 2 and np.all(np.isfinite(times)) and np.all(durations > 0), "Invalid time grid")
    _require(times.dtype == np.float64, "Unexpected time dtype")
    for name in ["kernel_jump_probability", "kernel_anticommutator_probability",
                 "kernel_total_probability", "kernel_survival", "chi_panel_probability"]:
        _require(kernel[name].dtype == np.float64, f"Unexpected dtype: {name}")
        _require(np.all(np.isfinite(kernel[name])), f"Nonfinite native kernel: {name}")
    total = kernel["kernel_total_probability"]
    jump = kernel["kernel_jump_probability"]
    anti = kernel["kernel_anticommutator_probability"]
    survival_kernel = kernel["kernel_survival"]
    _require(total.shape == (panels, nodes), "Unexpected probability kernel shape")
    _require(survival_kernel.shape == (nodes, nodes), "Unexpected survival-kernel shape")
    residuals = {
        "state_vs_insertion_time": _assert_near(times, insertion, "State and insertion grids"),
        "kernel_time": _assert_near(kernel["insertion_times"], times, "Kernel time grid"),
        "panel_width": _assert_near(kernel["panel_durations"], durations, "Response-panel duration"),
        "jump_plus_anticommutator": _assert_near(total, jump + anti, "Jump + anticommutator"),
    }
    _assert_near(times[-1], float(registered["T_final"]), "Actual horizon")
    _assert_near(float(configuration["dt"]), float(registered["dt"]), "Detector step")
    _assert_near(float(configuration["omega"]), float(registered["omega"]), "Confinement")
    _require(int(configuration["N_shell"]) == int(registered["N_shell"]), "Shell-cutoff identity")
    noncausal_p = total[np.triu(np.ones(total.shape, dtype=bool), k=1)]
    noncausal_s = survival_kernel[np.triu(np.ones(survival_kernel.shape, dtype=bool), k=1)]
    residuals["noncausal_kernel"] = max(_maxabs(noncausal_p), _maxabs(noncausal_s))
    _require(residuals["noncausal_kernel"] <= ARRAY_TOL, "Noncausal native kernel support")

    # Compare an independent kernel conservation construction including the source
    # trace, without replacing the saved survival kernel by that construction.
    constructed_s = np.zeros_like(survival_kernel)
    trace = source["trace_total"]
    for insertion_index in range(nodes):
        if insertion_index < panels:
            constructed_s[insertion_index + 1:, insertion_index] = -np.cumsum(
                total[insertion_index:, insertion_index], dtype=np.float64)
        constructed_s[insertion_index:, insertion_index] += trace[insertion_index]
    residuals["independent_kernel_closure"] = _maxabs(survival_kernel - constructed_s)
    reconstructed_s, reconstructed_p, reconstructed_g = reconstruct_response_from_kernel(
        insertion.astype(np.float64), total, survival_kernel)
    residuals["survival_reconstruction"] = _assert_near(reconstructed_s, stored_s, "Native survival susceptibility")
    residuals["roof_reconstruction"] = _assert_near(reconstructed_p, kernel["chi_panel_probability"], "Native roof-panel susceptibility")
    residuals["density_reconstruction"] = _assert_near(reconstructed_g, stored_g, "Native panel-average susceptibility")
    residuals["compact_survival"] = _assert_near(stored_s, compact["chi_survival"], "Compact survival")
    residuals["compact_roof"] = _assert_near(reconstructed_p, compact["chi_panel_probability"], "Compact roof")

    # Keep the two independently stored detection identities and their mismatch.
    chi_d_roof = float(np.sum(reconstructed_p, dtype=np.float64))
    chi_d_survival = -float(stored_s[-1])
    chi_mu = float(np.trapezoid(stored_s, times))
    censor_atom = float(stored_s[-1])
    a_tv = 0.5 * (float(np.sum(np.abs(reconstructed_p))) + abs(censor_atom))
    metrics = {
        "matrix_id": registered["matrix_id"],
        "channel": registered["environment_direction"],
        "propagator_type": registered["propagator_type"],
        "omega": float(registered["omega"]),
        "initial_mode": registered["initial_mode"],
        "N_shell": int(registered["N_shell"]),
        "Nz": int(configuration["N_z"]),
        "detector_dt": float(configuration["dt"]),
        "insertion_spacing": float(registered["insertion_dt"]),
        "panel_width_min": float(np.min(durations)),
        "panel_width_max": float(np.max(durations)),
        "T": float(times[-1]),
        "state_nodes": nodes,
        "response_panels": panels,
        "chi_D_roof": chi_d_roof,
        "chi_D_survival": chi_d_survival,
        "chi_mu_restricted": chi_mu,
        "complete_signed_measure_norm": a_tv,
        "censor_atom": censor_atom,
        "roof_survival_identity_residual": abs(chi_d_roof - chi_d_survival),
        "tangent_closure_max_abs": _maxabs(stored_s[1:] + np.cumsum(reconstructed_p)),
        "recorded_local_status": registered["loader_verdict"],
        "recorded_aggregate_status": registered["task08_status"],
    }
    for key, actual in [("chi_D", chi_d_survival), ("chi_D_panel_sum", chi_d_roof),
                        ("chi_mu", chi_mu), ("A_TV", a_tv)]:
        residuals["register_" + key] = _assert_near(actual, float(registered[key]), f"Register {key}")
    residuals["integrated_chi_D"] = _assert_near(
        chi_d_roof, integrated["chi_D_from_panel_sum"], "Integrated JSON roof")
    residuals["integrated_chi_mu"] = _assert_near(
        chi_mu, integrated["chi_mu_restricted"], "Integrated JSON restricted mean")
    curves = dict(times=times, panels=reconstructed_p, survival=stored_s, density=reconstructed_g)
    return metrics, residuals, curves


def _align_signed_panels(base, fine):
    """Sum native finer probabilities at common edges; no interpolation."""
    bt, ft = base["times"], fine["times"]
    indices = np.searchsorted(ft, bt)
    _require(np.all(indices < len(ft)), "Coarse support exceeds finer support")
    _require(np.allclose(ft[indices], bt, rtol=0, atol=2e-12), "Refinement nodes are not shared")
    cumulative = np.concatenate(([0.0], np.cumsum(fine["panels"], dtype=np.float64)))
    return np.diff(cumulative[indices])


def _plot(output, curves):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(3, 2, figsize=(9.4, 8.2), sharex=True, constrained_layout=True)
    colors = {"D": "#237a57", "U": "#c05636", "P": "#4353a2"}
    labels = {"D": "Downward relaxation", "U": "Upward excitation", "P": "Number dephasing"}
    for row, channel in enumerate("DUP"):
        main = curves[channel + "2-I"]
        null = curves[channel + "1"]
        left, right = axes[row]
        # Step plots explicitly show panel averages of native roof probabilities.
        left.stairs(main["density"], main["times"], color=colors[channel], lw=1.65, label="Spinor, insertion Δs=0.05")
        left.stairs(null["density"], null["times"], color="#555555", ls="--", lw=1.2, label="Factorized scalar, Δs=0.1")
        right.plot(main["times"], main["survival"], color=colors[channel], lw=1.65)
        right.plot(null["times"], null["survival"], color="#555555", ls="--", lw=1.2)
        left.set_title(labels[channel], loc="left", fontsize=11)
        left.set_ylabel(r"$\chi_g$ (panel average)")
        right.set_ylabel(r"$\chi_S(t)$")
        for ax in (left, right):
            ax.axhline(0, color="#999999", lw=.6)
            ax.grid(alpha=.2)
            ax.set_xlim(0, 10)
    axes[0, 0].legend(fontsize=8, loc="best")
    for ax in axes[-1]:
        ax.set_xlabel(r"Time $t/t_0$")
    fig.suptitle("Canonical environmental susceptibilities · ground preparation\n"
                 r"$\omega=100,\ N=12,\ N_z=1500,\ \Delta t=0.0005,\ T=10$", fontsize=12)
    fig.savefig(output / "canonical.png", dpi=180)
    plt.close(fig)


def run(repo: Path, output: Path):
    repo, output = Path(repo), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    base = repo / "data/canonical_response"
    register = {r["matrix_id"]: r for r in _csv(base / "CANONICAL_CASE_MASTER_TABLE.csv")}
    index = {r["matrix_id"]: r for r in _csv(base / "case_index.csv")}
    _require(set(register) == ROLES and set(index) == ROLES, "Canonical role coverage must be exactly 18")
    rows, case_checks, curves = [], {}, {}
    for role in sorted(ROLES):
        row, residuals, curve = _read_case(repo, index[role], register[role])
        rows.append(row); case_checks[role] = residuals; curves[role] = curve
    by_role = {r["matrix_id"]: r for r in rows}
    aggregate = {r["matrix_id"]: r for r in _csv(base / "aggregate/Task08_per_case_metrics.csv")}
    for role, row in by_role.items():
        historical = aggregate[role]
        for key, expected_key in [("chi_D_roof", "chi_D"), ("chi_D_survival", "minus_chi_S_T"),
                                  ("chi_mu_restricted", "chi_mu"),
                                  ("complete_signed_measure_norm", "complete_signed_measure_norm")]:
            case_checks[role]["task08_" + key] = _assert_near(
                row[key], float(historical[expected_key]), f"{role} Task08 {key}")
    scalar_nulls = {}
    for role in ("D1", "U1", "P1"):
        # The original case loader uses SCALAR_RESPONSE_ABS_TOL=1e-8.
        # U1 retains roundoff-level residuals; never replace them with zero.
        scalar_nulls[role] = {"maximum_panel": _maxabs(curves[role]["panels"]),
                              "maximum_survival": _maxabs(curves[role]["survival"]),
                              "integrated_roof": by_role[role]["chi_D_roof"]}
        _require(max(scalar_nulls[role]["maximum_panel"], scalar_nulls[role]["maximum_survival"]) <= 1e-8,
                 f"{role}: scalar response exceeds original recorded 1e-8 bound")

    refinement_rows = []
    stored_refinement = {r["baseline"]: r for r in _csv(base / "aggregate/Task08_insertion_refinement.csv")}
    for channel in "DUP":
        baseline, control = channel + "2", channel + "2-I"
        a, b = curves[baseline], curves[control]
        aligned_b = _align_signed_panels(a, b)
        atom_a, atom_b = float(a["survival"][-1]), float(b["survival"][-1])
        distance = .5 * (float(np.sum(np.abs(a["panels"] - aligned_b))) + abs(atom_a - atom_b))
        norm_a = .5 * (float(np.sum(np.abs(a["panels"]))) + abs(atom_a))
        norm_b = .5 * (float(np.sum(np.abs(aligned_b))) + abs(atom_b))
        relative = distance / max(norm_a, norm_b)
        historical = stored_refinement[baseline]
        _assert_near(distance, float(historical["complete_signed_measure_distance"]), "Insertion signed distance")
        _assert_near(relative, float(historical["relative_signed_measure_distance"]), "Insertion relative distance")
        refinement_rows.append(dict(baseline=baseline, control=control,
                                    complete_signed_distance=distance, relative_signed_distance=relative,
                                    recorded_gate=historical["passed"],
                                    check_scope="Saved-probability reduction; historical gate not rerun"))

    with (output / "canonical_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    with (output / "insertion_refinement.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(refinement_rows[0]))
        writer.writeheader(); writer.writerows(refinement_rows)
    result = {
        "group": "canonical",
        "status": "passed",
        "scope": "CPU reconstruction from bundled native kernels and regression against archived tables; no simulation or scientific acceptance rerun",
        "case_count": len(rows),
        "scalar_null_residuals": scalar_nulls,
        "checks": case_checks,
        "maximum_reconstruction_residual": max(
            value for checks in case_checks.values() for key, value in checks.items()
            if key.endswith("reconstruction")),
        "maximum_table_regression_residual": max(
            value for checks in case_checks.values() for key, value in checks.items()
            if key.startswith(("register_", "task08_", "integrated_"))),
        "maximum_independent_kernel_closure_residual": max(
            checks["independent_kernel_closure"] for checks in case_checks.values()),
        "refined_headline_coefficients": [by_role[c + "2-I"] for c in "DUP"],
        "conventions": {
            "source_rate": "dimensionless lambda_r=Gamma_r,phys*t0",
            "roof": "native signed detector-panel probabilities; never differentiated survival",
            "quadrature": "causal prefix trapezoid; total kernel = jump + anticommutator",
            "censoring": "separate survival atom chi_S(T) included in complete signed-measure norm",
            "restricted_mean": "trapezoid integral of stored chi_S on native insertion nodes",
            "historical_scope": "strict and operational uncertainty policies remain separate; no changed acceptance flags",
        },
    }
    (output / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    _plot(output, curves)
    return result
