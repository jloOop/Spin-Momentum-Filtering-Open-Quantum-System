# Auto-generated from saved Jupyter notebook: 05_single_case_independent_loader.ipynb
# Save the notebook before execution so this source snapshot matches the executed loader.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
05_single_case_independent_loader.py
====================================

Independent, cluster-side audit and compression loader for ONE completed
Task-05 oscillator-channel detector case.

This loader:

* does not import the Task-05 solver;
* does not rerun propagation;
* does not trust the solver PASS flag by itself;
* verifies the solver output-hash manifest against the raw files in the fixed
  Task-05 directory;
* independently reconstructs the complete-shell basis, projected ladders,
  number operators, H_perp, Pauli matrices, K_N, Audit-02-to-Task-05
  permutation, tensor ordering, and the positive spinor roof-term source code;
* independently recomputes probability, Krylov, shell-population, source, and
  selected-insertion-vector audits from the raw arrays;
* writes a compact, shareable report package while leaving all raw solver
  outputs untouched on the cluster.

It is a per-case screening loader.  It does NOT replace the final Task-06
aggregate loader, because scalar-null, 10/01 isotropy, Cartesian--oscillator,
time-step, monolithic-ratio, and shell-cutoff comparisons require multiple
cases simultaneously.

Directory policy
----------------
Copy this notebook directly into the completed Task-05 solver directory that
contains the raw case files.  The current Jupyter working directory is selected
automatically as both the input and output directory, and CASE_PREFIX is read
from the unique solver ``*_configuration.json`` file.  No manual case-prefix
edit and no sweep are implemented.

Outputs
-------
For CASE_PREFIX = CASE, the loader writes, in the same fixed directory,

    CASE_loader_audit.json
    CASE_loader_metrics.csv
    CASE_loader_report.md
    CASE_loader_compact.npz
    CASE_loader_output_hashes.json
    CASE_loader_run_status.json
    CASE_05_single_case_independent_loader.py
    CASE_loader_share.zip

The ZIP contains the compact loader products plus the small authoritative JSON
records and copied solver source.  It omits the large raw insertion-vector and
other redundant solver arrays, which remain on the cluster for Task 06/07.

Exit codes
----------
0 : independent per-case audit PASS
2 : raw case loaded, but at least one scientific/integrity gate failed
1 : missing/corrupt input or loader execution failure
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import math
import os
import shutil
import sys
import traceback
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import scipy.sparse as sp


# =============================================================================
# AUTOMATIC SINGLE-CASE CONFIGURATION
#
# Copy this notebook into the completed solver directory and run it there.
# The directory and CASE_PREFIX are detected from the solver's unique
# ``*_configuration.json`` file.  Nothing in this block needs manual editing.
# =============================================================================
RUN_DIRECTORY = Path.cwd().expanduser().resolve()

_CONFIGURATION_FILES = sorted(RUN_DIRECTORY.glob("*_configuration.json"))
if len(_CONFIGURATION_FILES) == 0:
    raise FileNotFoundError(
        "No solver *_configuration.json file was found in the current "
        f"Jupyter directory: {RUN_DIRECTORY}"
    )
if len(_CONFIGURATION_FILES) > 1:
    raise RuntimeError(
        "Automatic CASE_PREFIX detection requires exactly one solver "
        "*_configuration.json file in the current directory. Found: "
        + ", ".join(path.name for path in _CONFIGURATION_FILES)
    )

_CONFIGURATION_PATH = _CONFIGURATION_FILES[0]
with _CONFIGURATION_PATH.open("r", encoding="utf-8") as _configuration_handle:
    _AUTODETECTED_CONFIGURATION = json.load(_configuration_handle)

CASE_PREFIX = str(
    _AUTODETECTED_CONFIGURATION.get("case_prefix", "")
).strip()
if not CASE_PREFIX:
    raise ValueError(
        f"The solver configuration {_CONFIGURATION_PATH.name!r} contains no "
        "nonempty 'case_prefix' value."
    )

_EXPECTED_CONFIGURATION_NAME = f"{CASE_PREFIX}_configuration.json"
if _CONFIGURATION_PATH.name != _EXPECTED_CONFIGURATION_NAME:
    raise ValueError(
        "The configuration filename and its internal case_prefix disagree: "
        f"filename={_CONFIGURATION_PATH.name!r}, "
        f"expected={_EXPECTED_CONFIGURATION_NAME!r}."
    )

OUT_ROOT = RUN_DIRECTORY.parent
STAGE_DIRECTORY = RUN_DIRECTORY.name
# =============================================================================

NOTEBOOK_FILENAME = "05_single_case_independent_loader_Jupyter_auto_directory_and_prefix.ipynb"
LOADER_STAGE = "05_single_case_independent_loader"
LOADER_VERSION = "2026-08-03-task05-single-case-loader-v1"
T_CUT_DEFAULT = 3.6
OPERATOR_TOL_DEFAULT = 1.0e-12
LAUNCH_TOL_DEFAULT = 1.0e-12
TRUE_RESIDUAL_TOL_DEFAULT = 1.0e-8
SURVIVAL_INCREASE_TOL_DEFAULT = 2.0e-9
ROOF_CLOSURE_REL_TOL_DEFAULT = 1.0e-6
ROOF_CLOSURE_ABS_TOL_DEFAULT = 5.0e-9
ARRAY_REL_TOL = 5.0e-12
ARRAY_ABS_TOL = 5.0e-13


# =============================================================================
# BASIC UTILITIES
# =============================================================================
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def case_file(stage_dir: Path, case_prefix: str, suffix: str) -> Path:
    return stage_dir / f"{case_prefix}_{suffix}"


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(chunk_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def sha256_json(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    os.replace(tmp, path)


def atomic_write_text(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def resolve_loader_source_path(
    stage_dir: Path,
    case_prefix: str,
) -> Tuple[Path, bool]:
    """Return a real Python source path in scripts and Jupyter notebooks.

    A normal ``.py`` execution uses ``__file__`` unchanged.  A direct Jupyter
    execution has no ``__file__``, so the saved notebook is read and its code
    cells are materialized as a temporary ``.py`` source snapshot.  The
    existing loader-source copy and SHA-256 provenance logic then operate on
    that snapshot exactly as they do for a normal script.

    Save the notebook before running it so the materialized source corresponds
    to the code being executed.
    """
    module_file = globals().get("__file__")
    if isinstance(module_file, str) and module_file:
        return Path(module_file).resolve(), False

    notebook_path = (RUN_DIRECTORY / NOTEBOOK_FILENAME).resolve()
    if not notebook_path.is_file():
        candidates = sorted(
            path.resolve()
            for path in RUN_DIRECTORY.glob("05_single_case_independent_loader*.ipynb")
            if path.is_file()
        )
        if len(candidates) == 1:
            notebook_path = candidates[0]
        else:
            candidate_text = ", ".join(path.name for path in candidates) or "none"
            raise FileNotFoundError(
                "Cannot identify the saved loader notebook. Expected "
                f"{NOTEBOOK_FILENAME!r} in {RUN_DIRECTORY}, and found matching "
                f"notebooks: {candidate_text}. Save this notebook with the "
                f"name {NOTEBOOK_FILENAME!r} before running it."
            )

    notebook_payload = json.loads(notebook_path.read_text(encoding="utf-8"))
    code_cells: List[str] = []
    for cell in notebook_payload.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(str(item) for item in source)
        if not isinstance(source, str):
            raise TypeError("Notebook code-cell source has an unsupported format")
        if source.strip():
            code_cells.append(source.rstrip() + "\n")

    if not code_cells:
        raise ValueError(f"No executable code cells found in {notebook_path}")

    snapshot_text = (
        f"# Auto-generated from saved Jupyter notebook: {notebook_path.name}\n"
        "# Save the notebook before execution so this source snapshot matches "
        "the executed loader.\n\n"
        + "\n\n".join(code_cells)
    )
    snapshot_path = stage_dir / (
        f".{case_prefix}_05_single_case_independent_loader_notebook_snapshot.py"
    )
    atomic_write_text(snapshot_path, snapshot_text)
    return snapshot_path, True


def atomic_savez_compressed(path: Path, **arrays: np.ndarray) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    os.replace(tmp, path)


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        result = json.load(handle)
    if not isinstance(result, dict):
        raise TypeError(f"Expected JSON object in {path.name}")
    return result


def require_file(path: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"Required Task-05 file is missing: {path}")
    return path


def sparse_max_abs(matrix: sp.spmatrix) -> float:
    matrix = matrix.tocsr()
    if matrix.nnz == 0:
        return 0.0
    return float(np.max(np.abs(matrix.data)))


def dense_max_abs(array: np.ndarray) -> float:
    array = np.asarray(array)
    return 0.0 if array.size == 0 else float(np.max(np.abs(array)))


def frobenius_norm(matrix: sp.spmatrix) -> float:
    matrix = matrix.tocsr()
    return float(np.sqrt(np.sum(np.abs(matrix.data) ** 2, dtype=np.float64)))


def relative_error(error: float, scale: float) -> float:
    return float(error / max(abs(scale), np.finfo(float).tiny))


def all_finite(*arrays: np.ndarray) -> bool:
    return all(np.all(np.isfinite(np.asarray(array))) for array in arrays)


def max_abs_difference(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left)
    right = np.asarray(right)
    if left.shape != right.shape:
        return float("inf")
    return dense_max_abs(left - right)


def scalar_close(left: float, right: float, *, rtol: float = ARRAY_REL_TOL, atol: float = ARRAY_ABS_TOL) -> bool:
    return bool(np.isclose(left, right, rtol=rtol, atol=atol))


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("Non-finite float cannot be written to strict JSON")
        return result
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Non-finite float cannot be written to strict JSON")
        return value
    return value


# =============================================================================
# INDEPENDENT SOURCE AND OPERATOR RECONSTRUCTION
# =============================================================================
def complete_shell_labels_descending(n_shell: int) -> Tuple[Tuple[int, int], ...]:
    return tuple(
        (nx, total - nx)
        for total in range(n_shell + 1)
        for nx in range(total, -1, -1)
    )


def complete_shell_labels_audit02_native(n_shell: int) -> Tuple[Tuple[int, int], ...]:
    return tuple(
        (nx, total - nx)
        for total in range(n_shell + 1)
        for nx in range(total + 1)
    )


def build_projected_ladders(
    labels: Sequence[Tuple[int, int]],
) -> Tuple[sp.csr_matrix, sp.csr_matrix, Dict[Tuple[int, int], int]]:
    index = {label: position for position, label in enumerate(labels)}
    rows_x: List[int] = []
    cols_x: List[int] = []
    data_x: List[complex] = []
    rows_y: List[int] = []
    cols_y: List[int] = []
    data_y: List[complex] = []

    for column, (nx, ny) in enumerate(labels):
        if nx > 0:
            rows_x.append(index[(nx - 1, ny)])
            cols_x.append(column)
            data_x.append(math.sqrt(nx))
        if ny > 0:
            rows_y.append(index[(nx, ny - 1)])
            cols_y.append(column)
            data_y.append(math.sqrt(ny))

    dimension = len(labels)
    a_x = sp.csr_matrix(
        (np.asarray(data_x, dtype=np.complex128), (rows_x, cols_x)),
        shape=(dimension, dimension),
        dtype=np.complex128,
    )
    a_y = sp.csr_matrix(
        (np.asarray(data_y, dtype=np.complex128), (rows_y, cols_y)),
        shape=(dimension, dimension),
        dtype=np.complex128,
    )
    return a_x, a_y, index


def orbital_permutation(
    source_labels: Sequence[Tuple[int, int]],
    target_labels: Sequence[Tuple[int, int]],
) -> sp.csr_matrix:
    source_index = {label: idx for idx, label in enumerate(source_labels)}
    rows = np.arange(len(target_labels), dtype=np.int32)
    cols = np.asarray([source_index[label] for label in target_labels], dtype=np.int32)
    data = np.ones(len(target_labels), dtype=np.complex128)
    return sp.csr_matrix(
        (data, (rows, cols)),
        shape=(len(target_labels), len(source_labels)),
    )


def audit02_to_task05_tensor_permutation(
    native_labels: Sequence[Tuple[int, int]],
    task_labels: Sequence[Tuple[int, int]],
) -> sp.csr_matrix:
    native_index = {label: idx for idx, label in enumerate(native_labels)}
    task_index = {label: idx for idx, label in enumerate(task_labels)}
    m_modes = len(task_labels)
    rows: List[int] = []
    cols: List[int] = []
    data: List[complex] = []
    for label in task_labels:
        mu_task = task_index[label]
        mu_native = native_index[label]
        for spin in range(2):
            rows.append(spin * m_modes + mu_task)
            cols.append(mu_native * 2 + spin)
            data.append(1.0)
    return sp.csr_matrix(
        (np.asarray(data, dtype=np.complex128), (rows, cols)),
        shape=(2 * m_modes, 2 * m_modes),
    )


def source_code_scope_audit(source_path: Path) -> Dict[str, Any]:
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(source_path))

    executable_names: set[str] = set()
    imported_modules: set[str] = set()
    callable_names: set[str] = set()
    roof_reactive_expression: Optional[str] = None

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            executable_names.add(node.id.lower())
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            callable_names.add(node.name.lower())
        elif isinstance(node, ast.Import):
            imported_modules.update(alias.name.lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.add((node.module or "").lower())
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets: List[ast.expr]
            value: Optional[ast.expr]
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
                value = node.value
            else:
                targets = [node.target]
                value = node.value
            for target in targets:
                if isinstance(target, ast.Name) and target.id == "roof_reactive" and value is not None:
                    roof_reactive_expression = ast.unparse(value)

    forbidden_exact_names = {
        "gamma_down",
        "gamma_up",
        "gamma_phi",
        "gamma_downarrow",
        "gamma_uparrow",
        "bath_temperature",
        "density_matrix",
        "lindblad_generator",
        "monte_carlo",
        "quantum_trajectory",
    }
    forbidden_callable_fragments = (
        "lindblad",
        "dissipator",
        "density_matrix",
        "monte_carlo",
        "trajectory",
        "finite_temperature",
    )
    forbidden_import_fragments = ("qutip",)

    found_names = sorted(forbidden_exact_names.intersection(executable_names))
    found_callables = sorted(
        name
        for name in callable_names
        if any(fragment in name for fragment in forbidden_callable_fragments)
    )
    found_imports = sorted(
        module
        for module in imported_modules
        if any(fragment in module for fragment in forbidden_import_fragments)
    )

    positive_roof_source = bool(
        roof_reactive_expression is not None
        and "operators.k_spinmajor" in roof_reactive_expression
        and "2.0 * h_z" in roof_reactive_expression
        and not roof_reactive_expression.lstrip().startswith("-")
    )

    return {
        "python_ast_parse_passed": True,
        "forbidden_exact_executable_names_found": found_names,
        "forbidden_callable_names_found": found_callables,
        "forbidden_imports_found": found_imports,
        "active_environmental_or_density_matrix_code_absent": bool(
            not found_names and not found_callables and not found_imports
        ),
        "roof_reactive_assignment_expression": roof_reactive_expression,
        "positive_K_over_2hz_roof_source_detected": positive_roof_source,
    }


def independent_operator_audit(
    *,
    n_shell: int,
    omega: float,
    n_z: int,
    h_z: float,
    source_path: Path,
) -> Dict[str, Any]:
    labels = complete_shell_labels_descending(n_shell)
    expected_m = (n_shell + 1) * (n_shell + 2) // 2
    a_x, a_y, index = build_projected_ladders(labels)
    a_x_d = a_x.getH().tocsr()
    a_y_d = a_y.getH().tocsr()
    n_x = (a_x_d @ a_x).tocsr()
    n_y = (a_y_d @ a_y).tocsr()
    identity_orb = sp.eye(expected_m, dtype=np.complex128, format="csr")
    nx_diag = np.asarray([nx for nx, _ in labels], dtype=np.float64)
    ny_diag = np.asarray([ny for _, ny in labels], dtype=np.float64)
    h_perp = (omega * (n_x + n_y + identity_orb)).tocsr()

    sigma_x = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    sigma_y = np.asarray([[0.0, -1j], [1j, 0.0]], dtype=np.complex128)
    sigma_z = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    sx = sp.csr_matrix(sigma_x)
    sy = sp.csr_matrix(sigma_y)

    ell_perp = 1.0 / math.sqrt(omega)
    momentum_x = (1j / (math.sqrt(2.0) * ell_perp) * (a_x_d - a_x)).tocsr()
    momentum_y = (1j / (math.sqrt(2.0) * ell_perp) * (a_y_d - a_y)).tocsr()
    k_ladder = (
        1j
        / (math.sqrt(2.0) * ell_perp)
        * (
            sp.kron(sx, a_y_d - a_y, format="csr")
            - sp.kron(sy, a_x_d - a_x, format="csr")
        )
    ).tocsr()
    k_momentum = (
        sp.kron(sx, momentum_y, format="csr")
        - sp.kron(sy, momentum_x, format="csr")
    ).tocsr()
    k_unit = (
        1j
        / math.sqrt(2.0)
        * (
            sp.kron(sx, a_y_d - a_y, format="csr")
            - sp.kron(sy, a_x_d - a_x, format="csr")
        )
    ).tocsr()

    lowering_residuals: List[float] = []
    raising_residuals: List[float] = []
    for nx_value, ny_value in labels:
        source = np.zeros(expected_m, dtype=np.complex128)
        source[index[(nx_value, ny_value)]] = 1.0
        for axis, occupation, lower, raise_op in (
            ("x", nx_value, a_x, a_x_d),
            ("y", ny_value, a_y, a_y_d),
        ):
            expected_lower = np.zeros(expected_m, dtype=np.complex128)
            if occupation > 0:
                target = (
                    (nx_value - 1, ny_value)
                    if axis == "x"
                    else (nx_value, ny_value - 1)
                )
                expected_lower[index[target]] = math.sqrt(occupation)
            lowering_residuals.append(float(np.linalg.norm(lower @ source - expected_lower)))

            expected_raise = np.zeros(expected_m, dtype=np.complex128)
            if nx_value + ny_value < n_shell:
                target = (
                    (nx_value + 1, ny_value)
                    if axis == "x"
                    else (nx_value, ny_value + 1)
                )
                expected_raise[index[target]] = math.sqrt(occupation + 1)
            raising_residuals.append(float(np.linalg.norm(raise_op @ source - expected_raise)))

    native_labels = complete_shell_labels_audit02_native(n_shell)
    native_ax, native_ay, _ = build_projected_ladders(native_labels)
    native_axd = native_ax.getH().tocsr()
    native_ayd = native_ay.getH().tocsr()
    p_orb = orbital_permutation(native_labels, labels)
    native_k = (
        1j
        / (math.sqrt(2.0) * ell_perp)
        * (
            sp.kron(native_ayd - native_ay, sx, format="csr")
            - sp.kron(native_axd - native_ax, sy, format="csr")
        )
    ).tocsr()
    p_tensor = audit02_to_task05_tensor_permutation(native_labels, labels)

    tensor_samples: List[Dict[str, int]] = []
    for spin in range(2):
        for mu in (0, expected_m // 2, expected_m - 1):
            for k_z in (0, n_z // 2, n_z - 1):
                formula = (spin * expected_m + mu) * n_z + k_z
                raveled = int(
                    np.ravel_multi_index(
                        (spin, mu, k_z),
                        (2, expected_m, n_z),
                        order="C",
                    )
                )
                tensor_samples.append(
                    {
                        "spin": spin,
                        "mu": mu,
                        "k_z": k_z,
                        "formula_index": formula,
                        "raveled_index": raveled,
                    }
                )

    source_scope = source_code_scope_audit(source_path)
    plus_roof_block = k_ladder / (2.0 * h_z)
    minus_roof_block = -k_ladder / (2.0 * h_z)
    sign_separation = sparse_max_abs(plus_roof_block - minus_roof_block)

    metrics = {
        "M_N_formula_residual": abs(len(labels) - expected_m),
        "maximum_lowering_action_residual": max(lowering_residuals, default=0.0),
        "maximum_raising_action_residual": max(raising_residuals, default=0.0),
        "adjoint_x_residual": sparse_max_abs(a_x_d - a_x.getH()),
        "adjoint_y_residual": sparse_max_abs(a_y_d - a_y.getH()),
        "number_x_diagonal_residual": sparse_max_abs(
            n_x - sp.diags(nx_diag, 0, dtype=np.complex128)
        ),
        "number_y_diagonal_residual": sparse_max_abs(
            n_y - sp.diags(ny_diag, 0, dtype=np.complex128)
        ),
        "minimum_number_diagonal": float(min(np.min(nx_diag), np.min(ny_diag))),
        "H_perp_formula_residual": sparse_max_abs(
            h_perp - omega * (n_x + n_y + identity_orb)
        ),
        "K_hermiticity_residual": sparse_max_abs(k_ladder - k_ladder.getH()),
        "K_ladder_momentum_formula_residual": sparse_max_abs(k_ladder - k_momentum),
        "K_sqrt_omega_proportionality_residual": sparse_max_abs(
            k_ladder / math.sqrt(omega) - k_unit
        ),
        "audit02_orbital_ax_permutation_residual": sparse_max_abs(
            a_x - p_orb @ native_ax @ p_orb.getH()
        ),
        "audit02_orbital_ay_permutation_residual": sparse_max_abs(
            a_y - p_orb @ native_ay @ p_orb.getH()
        ),
        "audit02_K_tensor_permutation_residual": sparse_max_abs(
            k_ladder - p_tensor @ native_k @ p_tensor.getH()
        ),
        "tensor_permutation_unitarity_residual": sparse_max_abs(
            p_tensor @ p_tensor.getH()
            - sp.eye(2 * expected_m, dtype=np.complex128, format="csr")
        ),
        "spinor_plus_minus_roof_block_separation": sign_separation,
        "Pauli_max_residual": max(
            dense_max_abs(sigma_x - sigma_x.conj().T),
            dense_max_abs(sigma_y - sigma_y.conj().T),
            dense_max_abs(sigma_z - sigma_z.conj().T),
            dense_max_abs(sigma_x @ sigma_x - np.eye(2)),
            dense_max_abs(sigma_y @ sigma_y - np.eye(2)),
            dense_max_abs(sigma_z @ sigma_z - np.eye(2)),
            dense_max_abs(sigma_x @ sigma_y - sigma_y @ sigma_x - 2j * sigma_z),
        ),
    }

    tol = OPERATOR_TOL_DEFAULT
    checks = {
        "complete_shell_dimension_and_descending_order": bool(
            metrics["M_N_formula_residual"] == 0
            and labels == complete_shell_labels_descending(n_shell)
        ),
        "ladder_actions": bool(
            max(
                metrics["maximum_lowering_action_residual"],
                metrics["maximum_raising_action_residual"],
            )
            <= tol
        ),
        "adjoint_identities": bool(
            max(metrics["adjoint_x_residual"], metrics["adjoint_y_residual"]) <= tol
        ),
        "number_operators": bool(
            metrics["minimum_number_diagonal"] >= -tol
            and max(
                metrics["number_x_diagonal_residual"],
                metrics["number_y_diagonal_residual"],
            )
            <= tol
        ),
        "H_perp_construction": bool(metrics["H_perp_formula_residual"] <= tol),
        "K_hermiticity": bool(metrics["K_hermiticity_residual"] <= tol),
        "K_ladder_momentum_formula": bool(
            metrics["K_ladder_momentum_formula_residual"] <= tol
        ),
        "K_sqrt_omega_scaling": bool(
            metrics["K_sqrt_omega_proportionality_residual"] <= tol
        ),
        "Audit02_equivalence_under_explicit_permutation": bool(
            max(
                metrics["audit02_orbital_ax_permutation_residual"],
                metrics["audit02_orbital_ay_permutation_residual"],
                metrics["audit02_K_tensor_permutation_residual"],
                metrics["tensor_permutation_unitarity_residual"],
            )
            <= tol
        ),
        "Pauli_matrices": bool(metrics["Pauli_max_residual"] <= tol),
        "tensor_ordering_z_fast_channel_then_spin": bool(
            all(item["formula_index"] == item["raveled_index"] for item in tensor_samples)
        ),
        "positive_spinor_roof_source_code": bool(
            source_scope["positive_K_over_2hz_roof_source_detected"]
        ),
        "active_bath_density_matrix_and_trajectory_code_absent": bool(
            source_scope["active_environmental_or_density_matrix_code_absent"]
        ),
    }

    return {
        "basis_labels": [[nx, ny] for nx, ny in labels],
        "M_N": expected_m,
        "d_channels": 2 * expected_m,
        "state_index_formula": "index(s,mu,k_z)=(s*M_N+mu)*N_z+k_z",
        "tensor_index_samples": tensor_samples,
        "metrics": metrics,
        "source_scope": source_scope,
        "checks": checks,
        "all_checks_passed": all(checks.values()),
    }


# =============================================================================
# RAW CASE LOADING AND AUDIT
# =============================================================================
def load_npy(path: Path) -> np.ndarray:
    return np.load(require_file(path), allow_pickle=False)


def load_npz(path: Path) -> Dict[str, np.ndarray]:
    with np.load(require_file(path), allow_pickle=False) as archive:
        return {name: np.asarray(archive[name]) for name in archive.files}


def compare_metric_dictionary(
    observed: Mapping[str, float],
    stored: Mapping[str, Any],
) -> Dict[str, Any]:
    differences: Dict[str, float] = {}
    passed = True
    for key, value in observed.items():
        if key not in stored:
            differences[key] = float("inf")
            passed = False
            continue
        stored_value = float(stored[key])
        difference = abs(value - stored_value)
        differences[key] = difference
        if not scalar_close(value, stored_value):
            passed = False
    return {"passed": passed, "absolute_differences": differences}


def write_metrics_csv(path: Path, row: Mapping[str, Any]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)
    os.replace(tmp, path)


def audit_case(stage_dir: Path, case_prefix: str, loader_source_path: Path) -> Dict[str, Any]:
    configuration_path = require_file(case_file(stage_dir, case_prefix, "configuration.json"))
    operator_audit_path = require_file(case_file(stage_dir, case_prefix, "operator_audit.json"))
    solver_audit_path = require_file(case_file(stage_dir, case_prefix, "solver_audit.json"))
    solver_status_path = require_file(case_file(stage_dir, case_prefix, "run_status.json"))
    solver_hash_path = require_file(case_file(stage_dir, case_prefix, "output_hashes.json"))

    configuration = read_json(configuration_path)
    operator_audit = read_json(operator_audit_path)
    solver_audit = read_json(solver_audit_path)
    solver_status = read_json(solver_status_path)
    solver_hashes = read_json(solver_hash_path)

    copied_source_name = str(configuration.get("copied_source_file", ""))
    copied_source_path = require_file(stage_dir / copied_source_name)

    # ------------------------------------------------------------------
    # Hash and provenance reconstruction.
    # ------------------------------------------------------------------
    manifest_files = solver_hashes.get("files", {})
    if not isinstance(manifest_files, dict) or not manifest_files:
        raise ValueError("Solver output-hash manifest is empty or malformed")
    manifest_hash_results: Dict[str, Dict[str, Any]] = {}
    all_manifest_hashes_match = True
    for filename, expected_hash in sorted(manifest_files.items()):
        raw_path = require_file(stage_dir / filename)
        actual_hash = sha256_file(raw_path)
        match = actual_hash == expected_hash
        manifest_hash_results[filename] = {
            "expected": expected_hash,
            "actual": actual_hash,
            "match": match,
        }
        all_manifest_hashes_match = all_manifest_hashes_match and match

    config_copy = dict(configuration)
    stored_configuration_hash = str(config_copy.pop("configuration_sha256"))
    reconstructed_configuration_hash = sha256_json(config_copy)
    configuration_hash_match = reconstructed_configuration_hash == stored_configuration_hash

    copied_source_hash = sha256_file(copied_source_path)
    source_hash_values = {
        "configuration_source_sha256": configuration.get("source_sha256"),
        "configuration_copied_source_sha256": configuration.get("copied_source_sha256"),
        "operator_audit_source_sha256": operator_audit.get("source_sha256"),
        "solver_audit_source_sha256": solver_audit.get("source_sha256"),
        "solver_status_source_sha256": solver_status.get("source_sha256"),
        "solver_manifest_source_sha256": solver_hashes.get("source_sha256"),
        "actual_copied_source_sha256": copied_source_hash,
    }
    source_hash_consistent = len({str(value) for value in source_hash_values.values()}) == 1

    actual_output_manifest_hash = sha256_file(solver_hash_path)
    status_manifest_hash_match = (
        solver_status.get("output_hash_manifest_sha256") == actual_output_manifest_hash
    )

    # ------------------------------------------------------------------
    # Frozen configuration and independent operator/source reconstruction.
    # ------------------------------------------------------------------
    n_shell = int(configuration["N_shell"])
    omega = float(configuration["omega"])
    n_z = int(configuration["N_z"])
    h_z = float(configuration["h_z"])
    dt = float(configuration["dt"])
    t_final = float(configuration["T_final"])
    num_steps = int(configuration["num_steps"])
    initial_mode = str(configuration["initial_mode"])
    propagator_type = str(configuration["propagator_type"])
    detector_label = str(configuration["detector_label"])
    t_cut = T_CUT_DEFAULT

    acceptance = solver_audit.get("acceptance_tolerances", {})
    operator_tol = float(acceptance.get("operator", OPERATOR_TOL_DEFAULT))
    launch_tol = float(acceptance.get("launch", LAUNCH_TOL_DEFAULT))
    residual_tol = float(
        acceptance.get("true_relative_residual", TRUE_RESIDUAL_TOL_DEFAULT)
    )
    survival_tol = float(
        acceptance.get("survival_increase", SURVIVAL_INCREASE_TOL_DEFAULT)
    )
    roof_rel_tol = float(
        acceptance.get("roof_closure_relative", ROOF_CLOSURE_REL_TOL_DEFAULT)
    )
    roof_abs_tol = float(
        acceptance.get("roof_closure_absolute", ROOF_CLOSURE_ABS_TOL_DEFAULT)
    )

    independent_operators = independent_operator_audit(
        n_shell=n_shell,
        omega=omega,
        n_z=n_z,
        h_z=h_z,
        source_path=copied_source_path,
    )

    expected_m = (n_shell + 1) * (n_shell + 2) // 2
    config_checks = {
        "case_prefix_exact": configuration.get("case_prefix") == case_prefix,
        "stage_directory_exact": configuration.get("fixed_stage_directory") == STAGE_DIRECTORY,
        "manual_single_case_policy": configuration.get("manual_single_case_policy") is True,
        "automatic_production_sweep_absent": configuration.get("automatic_production_sweep") is False,
        "zero_ambient_bath": configuration.get("zero_ambient_bath") is True,
        "endpoint_false": configuration.get("endpoint") is False,
        "complex128_state_and_matrix": (
            configuration.get("state_dtype") == "complex128"
            and configuration.get("matrix_dtype") == "complex128"
        ),
        "float64_reductions": configuration.get("reduction_dtype") == "float64",
        "complete_shell_dimension": int(configuration.get("M_N", -1)) == expected_m,
        "spin_resolved_dimension": int(configuration.get("d_channels", -1)) == 2 * expected_m,
        "tensor_index_formula": configuration.get("state_index_formula")
        == "index(s,mu,k_z)=(s*M_N+mu)*N_z+k_z",
        "integral_number_of_steps": (
            num_steps == int(round(t_final / dt))
            and np.isclose(num_steps * dt, t_final, rtol=0.0, atol=1.0e-12)
        ),
        "configuration_hash_reconstructed": configuration_hash_match,
        "source_hash_consistent": source_hash_consistent,
        "solver_output_manifest_hash_matches_status": status_manifest_hash_match,
        "all_manifest_file_hashes_match": all_manifest_hashes_match,
        "production_backend_cupy_or_declared_smoke": bool(
            configuration.get("smoke_test") is True
            or configuration.get("backend_metadata", {}).get("backend") == "cupy"
        ),
    }

    # ------------------------------------------------------------------
    # Raw arrays.
    # ------------------------------------------------------------------
    times = load_npy(case_file(stage_dir, case_prefix, "times.npy"))
    survival = load_npy(case_file(stage_dir, case_prefix, "survival.npy"))
    step_roof = load_npy(case_file(stage_dir, case_prefix, "step_loss_roof_midpoint.npy"))
    midpoint_times = load_npy(case_file(stage_dir, case_prefix, "click_midpoint_times.npy"))
    click_density = load_npy(case_file(stage_dir, case_prefix, "click_density.npy"))
    true_residual = load_npy(case_file(stage_dir, case_prefix, "true_relative_residual.npy"))
    gmres_info = load_npy(case_file(stage_dir, case_prefix, "gmres_info.npy"))
    gmres_solve_count = load_npy(case_file(stage_dir, case_prefix, "gmres_solve_count.npy"))
    step_total = load_npy(case_file(stage_dir, case_prefix, "step_loss_total.npy"))
    step_clamp = load_npy(case_file(stage_dir, case_prefix, "step_loss_bottom_clamp.npy"))
    step_flux_residual = load_npy(case_file(stage_dir, case_prefix, "step_loss_flux_residual.npy"))

    expected_times = np.arange(num_steps + 1, dtype=np.float64) * dt
    expected_midpoints = (np.arange(num_steps, dtype=np.float64) + 0.5) * dt
    expected_step_total = survival[:-1] - survival[1:]
    expected_click_density = step_roof / dt

    D_norm = float(survival[0] - survival[-1])
    D_roof = float(np.sum(step_roof, dtype=np.float64))
    closure_residual = float(survival[-1] + D_roof - survival[0])
    closure_relative = abs(closure_residual) / max(abs(D_norm), D_roof, 1.0e-15)
    telescoping_residual = float(
        survival[-1] + np.sum(step_total, dtype=np.float64) - survival[0]
    )
    decomposed_per_step = step_roof + step_flux_residual + step_clamp
    decomposed_residual = float(
        survival[-1]
        + D_roof
        + np.sum(step_flux_residual, dtype=np.float64)
        + np.sum(step_clamp, dtype=np.float64)
        - survival[0]
    )

    # Production Task 05 freezes t_cut=3.6.  The solver's internal reduced
    # smoke test uses a deliberately shorter t_cut that is not written into
    # the configuration JSON, so infer only that smoke-test split from the
    # stored D_E value.  No production result uses this inference.
    if configuration.get("smoke_test") is True:
        target_D_E = float(
            solver_audit.get("observed_detector_metrics", {}).get("D_E", 0.0)
        )
        prefix_losses = np.concatenate(
            ([0.0], np.cumsum(step_roof, dtype=np.float64))
        )
        early_count = int(np.argmin(np.abs(prefix_losses - target_D_E)))
        early_mask = np.zeros(num_steps, dtype=bool)
        early_mask[:early_count] = True
        t_cut_used = (
            float(midpoint_times[early_count])
            if early_count < num_steps
            else float(t_final)
        )
    else:
        early_mask = midpoint_times < t_cut
        t_cut_used = t_cut

    mu_restricted = float(np.trapezoid(survival, times))
    D_E = float(np.sum(step_roof[early_mask], dtype=np.float64))
    D_L = float(np.sum(step_roof[~early_mask], dtype=np.float64))
    late_fraction = D_L / D_roof if D_roof > 0.0 else 0.0
    conditional_click_mean = (
        (mu_restricted - t_final * survival[-1]) / D_roof if D_roof > 0.0 else 0.0
    )
    peak_index = int(np.argmax(click_density))
    observed_metrics = {
        "S_T": float(survival[-1]),
        "D_roof": D_roof,
        "D_norm": D_norm,
        "mu_restricted": mu_restricted,
        "D_E": D_E,
        "D_L": D_L,
        "late_fraction": late_fraction,
        "conditional_click_mean_before_horizon": conditional_click_mean,
        "peak_t": float(midpoint_times[peak_index]),
        "peak_g": float(click_density[peak_index]),
    }
    stored_metric_comparison = compare_metric_dictionary(
        observed_metrics,
        solver_audit.get("observed_detector_metrics", {}),
    )

    raw_array_checks = {
        "expected_array_shapes": bool(
            times.shape == (num_steps + 1,)
            and survival.shape == (num_steps + 1,)
            and all(
                array.shape == (num_steps,)
                for array in (
                    step_roof,
                    midpoint_times,
                    click_density,
                    true_residual,
                    gmres_info,
                    gmres_solve_count,
                    step_total,
                    step_clamp,
                    step_flux_residual,
                )
            )
        ),
        "all_raw_arrays_finite": all_finite(
            times,
            survival,
            step_roof,
            midpoint_times,
            click_density,
            true_residual,
            gmres_info,
            gmres_solve_count,
            step_total,
            step_clamp,
            step_flux_residual,
        ),
        "time_grid_exact": max_abs_difference(times, expected_times) <= 2.0e-12,
        "midpoint_grid_exact": max_abs_difference(midpoint_times, expected_midpoints) <= 2.0e-12,
        "click_density_reconstructed": max_abs_difference(
            click_density, expected_click_density
        )
        <= 5.0e-13,
        "step_loss_telescoping_reconstructed": max_abs_difference(
            step_total, expected_step_total
        )
        <= 5.0e-12,
        "step_loss_decomposition_reconstructed": max_abs_difference(
            step_total, decomposed_per_step
        )
        <= 5.0e-12,
        "gmres_return_codes_zero": bool(np.all(gmres_info == 0)),
        "gmres_solve_counts_positive": bool(np.all(gmres_solve_count > 0)),
        "true_relative_residual_within_tolerance": bool(
            np.max(true_residual) <= residual_tol
        ),
        "midpoint_roof_probabilities_nonnegative": bool(
            np.min(step_roof) >= -operator_tol
        ),
        "survival_nonincreasing_within_tolerance": bool(
            np.max(np.diff(survival), initial=-np.inf) <= survival_tol
        ),
        "bottom_clamp_loss_zero": bool(
            np.sum(step_clamp, dtype=np.float64) <= operator_tol
        ),
        "roof_norm_probability_closure": bool(
            abs(closure_residual)
            <= max(roof_abs_tol, roof_rel_tol * max(abs(D_norm), D_roof))
        ),
        "exact_telescoping_closure": abs(telescoping_residual) <= 5.0e-13,
        "exact_decomposed_closure": abs(decomposed_residual) <= 5.0e-13,
        "solver_detector_metrics_reconstructed": stored_metric_comparison["passed"],
    }

    # ------------------------------------------------------------------
    # Shell populations.
    # ------------------------------------------------------------------
    shell = load_npz(case_file(stage_dir, case_prefix, "shell_populations.npz"))
    required_shell_keys = {
        "shell_indices",
        "shell_populations_subnormalized",
        "shell_populations_normalized",
        "top_shell_population_subnormalized",
        "top_shell_population_normalized",
        "interpretation",
    }
    shell_keys_exact = set(shell) == required_shell_keys
    shell_sub = np.asarray(shell["shell_populations_subnormalized"], dtype=np.float64)
    shell_norm = np.asarray(shell["shell_populations_normalized"], dtype=np.float64)
    top_sub = np.asarray(shell["top_shell_population_subnormalized"], dtype=np.float64)
    top_norm = np.asarray(shell["top_shell_population_normalized"], dtype=np.float64)
    shell_indices = np.asarray(shell["shell_indices"], dtype=np.int64)

    shell_sub_sum_residual = float(np.max(np.abs(np.sum(shell_sub, axis=1) - survival)))
    shell_norm_sum_residual = float(np.max(np.abs(np.sum(shell_norm, axis=1) - 1.0)))
    shell_checks = {
        "schema_exact": shell_keys_exact,
        "shapes_exact": bool(
            shell_sub.shape == (num_steps + 1, n_shell + 1)
            and shell_norm.shape == shell_sub.shape
            and top_sub.shape == (num_steps + 1,)
            and top_norm.shape == (num_steps + 1,)
            and np.array_equal(shell_indices, np.arange(n_shell + 1))
        ),
        "all_shell_arrays_finite": all_finite(shell_sub, shell_norm, top_sub, top_norm),
        "subnormalized_shell_sum_equals_survival": shell_sub_sum_residual <= 5.0e-12,
        "normalized_shell_sum_equals_one": shell_norm_sum_residual <= 5.0e-12,
        "top_shell_arrays_match_last_column": bool(
            max_abs_difference(top_sub, shell_sub[:, -1]) <= 5.0e-13
            and max_abs_difference(top_norm, shell_norm[:, -1]) <= 5.0e-13
        ),
        "shell_populations_nonnegative": bool(
            np.min(shell_sub) >= -operator_tol and np.min(shell_norm) >= -operator_tol
        ),
        "top_shell_bounds": bool(
            np.min(top_sub) >= -operator_tol
            and np.max(top_sub - survival) <= operator_tol
            and np.min(top_norm) >= -operator_tol
            and np.max(top_norm) <= 1.0 + operator_tol
        ),
    }

    # ------------------------------------------------------------------
    # Source diagnostics.
    # ------------------------------------------------------------------
    source = load_npz(case_file(stage_dir, case_prefix, "source_diagnostics.npz"))
    required_source_numeric = {
        "s_down_subnormalized",
        "s_down_normalized",
        "s_up_subnormalized",
        "s_up_normalized",
        "s_phi_survival_weighted",
        "s_phi_normalized",
        "nx_mean_subnormalized",
        "ny_mean_subnormalized",
        "nx2_mean_subnormalized",
        "ny2_mean_subnormalized",
        "r_K_omit_subnormalized",
        "r_K_omit_normalized_no_click",
        "times",
        "r_K_omit_cumulative_integral",
        "launch_control_required",
        "launch_s_down_expected",
        "launch_s_phi_expected",
        "launch_s_up_expected",
        "interpretation",
    }
    source_schema_exact = set(source) == required_source_numeric
    source_numeric_names = [
        name
        for name in required_source_numeric
        if name not in {"interpretation", "launch_control_required"}
    ]
    source_shape_pass = all(
        np.asarray(source[name]).shape == (num_steps + 1,)
        for name in (
            "s_down_subnormalized",
            "s_down_normalized",
            "s_up_subnormalized",
            "s_up_normalized",
            "s_phi_survival_weighted",
            "s_phi_normalized",
            "nx_mean_subnormalized",
            "ny_mean_subnormalized",
            "nx2_mean_subnormalized",
            "ny2_mean_subnormalized",
            "r_K_omit_subnormalized",
            "r_K_omit_normalized_no_click",
            "times",
            "r_K_omit_cumulative_integral",
        )
    )
    source_numeric_finite = all_finite(
        *[np.asarray(source[name]) for name in source_numeric_names]
    )

    s_down_sub = np.asarray(source["s_down_subnormalized"], dtype=np.float64)
    s_down = np.asarray(source["s_down_normalized"], dtype=np.float64)
    s_up_sub = np.asarray(source["s_up_subnormalized"], dtype=np.float64)
    s_up = np.asarray(source["s_up_normalized"], dtype=np.float64)
    s_phi_weighted = np.asarray(source["s_phi_survival_weighted"], dtype=np.float64)
    s_phi = np.asarray(source["s_phi_normalized"], dtype=np.float64)
    nx_sub = np.asarray(source["nx_mean_subnormalized"], dtype=np.float64)
    ny_sub = np.asarray(source["ny_mean_subnormalized"], dtype=np.float64)
    nx2_sub = np.asarray(source["nx2_mean_subnormalized"], dtype=np.float64)
    ny2_sub = np.asarray(source["ny2_mean_subnormalized"], dtype=np.float64)
    r_k_sub = np.asarray(source["r_K_omit_subnormalized"], dtype=np.float64)
    r_k_norm = np.asarray(source["r_K_omit_normalized_no_click"], dtype=np.float64)
    r_k_cumulative = np.asarray(source["r_K_omit_cumulative_integral"], dtype=np.float64)

    nperp_sub = nx_sub + ny_sub
    expected_s_down = nperp_sub / survival
    expected_s_up_sub = nperp_sub + 2.0 * survival - (n_shell + 2.0) * top_sub
    expected_s_up = expected_s_up_sub / survival
    nx_norm = nx_sub / survival
    ny_norm = ny_sub / survival
    expected_s_phi = (
        nx2_sub / survival - nx_norm**2
        + ny2_sub / survival - ny_norm**2
    )
    expected_r_k_cumulative = np.zeros(num_steps + 1, dtype=np.float64)
    if num_steps:
        expected_r_k_cumulative[1:] = np.cumsum(
            0.5 * dt * (r_k_sub[:-1] + r_k_sub[1:]),
            dtype=np.float64,
        )

    launch_errors = {
        "s_down": abs(float(s_down[0]) - 0.0),
        "s_phi": abs(float(s_phi[0]) - 0.0),
        "s_up": abs(float(s_up[0]) - 2.0),
    }
    launch_required = initial_mode == "00"
    source_checks = {
        "schema_exact": source_schema_exact,
        "shapes_exact": source_shape_pass,
        "all_source_arrays_finite": source_numeric_finite,
        "source_times_match_state_times": max_abs_difference(
            np.asarray(source["times"], dtype=np.float64), times
        )
        <= 2.0e-12,
        "s_down_reconstructed": bool(
            max_abs_difference(s_down_sub, survival * s_down) <= 5.0e-12
            and max_abs_difference(s_down, expected_s_down) <= 5.0e-12
        ),
        "s_up_projected_formula_reconstructed": bool(
            max_abs_difference(s_up_sub, expected_s_up_sub) <= 5.0e-12
            and max_abs_difference(s_up, expected_s_up) <= 5.0e-12
        ),
        "s_phi_variance_reconstructed": bool(
            max_abs_difference(s_phi_weighted, survival * s_phi) <= 5.0e-12
            and max_abs_difference(s_phi, expected_s_phi) <= 5.0e-12
        ),
        "r_K_omit_normalization_reconstructed": max_abs_difference(
            r_k_sub, survival * r_k_norm
        )
        <= 5.0e-12,
        "r_K_omit_integral_reconstructed": max_abs_difference(
            r_k_cumulative, expected_r_k_cumulative
        )
        <= 5.0e-12,
        "source_diagnostics_nonnegative": bool(
            min(np.min(s_down), np.min(s_up), np.min(s_phi), np.min(r_k_sub))
            >= -operator_tol
        ),
        "mode00_launch_identities": bool(
            not launch_required or max(launch_errors.values()) <= launch_tol
        ),
        "factorized_scalar_ground_source_invariance": bool(
            not (detector_label == "scalar" and initial_mode == "00")
            or max(
                np.max(np.abs(s_down)),
                np.max(np.abs(s_phi)),
                np.max(np.abs(s_up - 2.0)),
            )
            <= 5.0e-12
        ),
    }

    # ------------------------------------------------------------------
    # Selected insertion-vector schema and norm bookkeeping.
    # ------------------------------------------------------------------
    insertion = load_npz(case_file(stage_dir, case_prefix, "selected_insertion_vectors.npz"))
    required_insertion_keys = {
        "vector_names",
        "vector_steps",
        "vector_requested_times",
        "vector_actual_times",
        "vector_survival",
        "vector_indptr",
        "channel_indices",
        "channel_values",
        "vector_total_norm2",
        "vector_omitted_norm2",
        "vector_channel_threshold_norm2",
        "alias_names",
        "alias_targets",
        "n_z",
        "d_channels",
        "h_z",
        "channel_relative_norm_tolerance",
        "interpretation",
    }
    insertion_schema_exact = set(insertion) == required_insertion_keys
    vector_steps = np.asarray(insertion["vector_steps"], dtype=np.int64)
    vector_survival = np.asarray(insertion["vector_survival"], dtype=np.float64)
    vector_indptr = np.asarray(insertion["vector_indptr"], dtype=np.int64)
    channel_indices = np.asarray(insertion["channel_indices"], dtype=np.int64)
    channel_values = np.asarray(insertion["channel_values"], dtype=np.complex128)
    vector_total_norm2 = np.asarray(insertion["vector_total_norm2"], dtype=np.float64)
    vector_omitted_norm2 = np.asarray(insertion["vector_omitted_norm2"], dtype=np.float64)
    n_vectors = int(np.asarray(insertion["vector_names"]).size)
    insertion_checks = {
        "schema_exact": insertion_schema_exact,
        "vector_metadata_lengths_consistent": bool(
            vector_steps.shape == (n_vectors,)
            and vector_survival.shape == (n_vectors,)
            and vector_total_norm2.shape == (n_vectors,)
            and vector_omitted_norm2.shape == (n_vectors,)
            and vector_indptr.shape == (n_vectors + 1,)
        ),
        "vector_steps_in_range": bool(
            np.all(vector_steps >= 0) and np.all(vector_steps <= num_steps)
        ),
        "vector_survivals_match_raw_curve": bool(
            max_abs_difference(vector_survival, survival[vector_steps]) <= 5.0e-12
        ),
        "compressed_channel_rows_consistent": bool(
            vector_indptr[0] == 0
            and vector_indptr[-1] == channel_indices.size
            and np.all(np.diff(vector_indptr) >= 0)
            and channel_values.shape == (channel_indices.size, n_z)
            and np.all(channel_indices >= 0)
            and np.all(channel_indices < 2 * expected_m)
        ),
        "all_insertion_numeric_arrays_finite": all_finite(
            vector_survival,
            vector_total_norm2,
            vector_omitted_norm2,
            channel_values.real,
            channel_values.imag,
        ),
        "omitted_norm_bookkeeping_nonnegative": bool(
            np.min(vector_total_norm2) >= -operator_tol
            and np.min(vector_omitted_norm2) >= -operator_tol
            and np.max(vector_omitted_norm2 - vector_total_norm2) <= operator_tol
        ),
        "dimensions_match_configuration": bool(
            int(np.asarray(insertion["n_z"])[0]) == n_z
            and int(np.asarray(insertion["d_channels"])[0]) == 2 * expected_m
            and scalar_close(float(np.asarray(insertion["h_z"])[0]), h_z)
        ),
    }

    # ------------------------------------------------------------------
    # Small JSON records, status, stage manifest, and solver/loader agreement.
    # ------------------------------------------------------------------
    solver_json_checks = {
        "solver_operator_audit_passed": operator_audit.get("all_checks_passed") is True,
        "solver_all_checks_passed": solver_audit.get("all_checks_passed") is True,
        "solver_status_completed": solver_status.get("status") == "completed",
        "solver_status_all_checks_passed": solver_status.get("all_solver_checks_passed") is True,
        "solver_completed_all_steps": int(solver_status.get("completed_steps", -1)) == num_steps,
        "configuration_hash_consistent_across_JSON": bool(
            operator_audit.get("configuration_sha256") == stored_configuration_hash
            and solver_audit.get("configuration_sha256") == stored_configuration_hash
            and solver_status.get("configuration_sha256") == stored_configuration_hash
            and solver_hashes.get("configuration_sha256") == stored_configuration_hash
        ),
        "source_hash_consistent_across_JSON": source_hash_consistent,
    }

    stage_manifest_path = stage_dir / "stage_manifest.json"
    stage_manifest_check: Dict[str, Any]
    if stage_manifest_path.is_file():
        stage_manifest = read_json(stage_manifest_path)
        entry = stage_manifest.get("cases", {}).get(case_prefix, {})
        stage_manifest_check = {
            "present": True,
            "case_entry_present": bool(entry),
            "status_matches": entry.get("status") == solver_status.get("status"),
            "configuration_file_matches": entry.get("configuration") == configuration_path.name,
            "solver_audit_file_matches": entry.get("solver_audit") == solver_audit_path.name,
            "output_hash_file_matches": entry.get("output_hashes") == solver_hash_path.name,
            "passed": bool(
                entry
                and entry.get("status") == solver_status.get("status")
                and entry.get("configuration") == configuration_path.name
                and entry.get("solver_audit") == solver_audit_path.name
                and entry.get("output_hashes") == solver_hash_path.name
            ),
        }
    else:
        stage_manifest_check = {
            "present": False,
            "case_entry_present": False,
            "passed": False,
        }

    all_check_groups = {
        "hash_and_configuration": config_checks,
        "independent_operator_and_source": independent_operators["checks"],
        "raw_array_probability_and_solver": raw_array_checks,
        "shell_populations": shell_checks,
        "source_diagnostics": source_checks,
        "selected_insertion_vectors": insertion_checks,
        "solver_JSON_records": solver_json_checks,
        "stage_manifest": {"stage_manifest_entry": stage_manifest_check["passed"]},
    }
    flat_checks = {
        f"{group}.{name}": bool(value)
        for group, group_checks in all_check_groups.items()
        for name, value in group_checks.items()
    }
    all_checks_passed = all(flat_checks.values())

    source_summary = {
        "launch_s_down": float(s_down[0]),
        "launch_s_phi": float(s_phi[0]),
        "launch_s_up": float(s_up[0]),
        "maximum_s_down_normalized": float(np.max(s_down)),
        "maximum_s_phi_normalized": float(np.max(s_phi)),
        "minimum_s_up_normalized": float(np.min(s_up)),
        "maximum_s_up_normalized": float(np.max(s_up)),
        "maximum_top_shell_population_normalized": float(np.max(top_norm)),
        "final_top_shell_population_normalized": float(top_norm[-1]),
        "final_r_K_omit_cumulative_integral": float(r_k_cumulative[-1]),
        "maximum_r_K_omit_subnormalized": float(np.max(r_k_sub)),
    }

    probability_summary = {
        "initial_survival": float(survival[0]),
        "final_survival": float(survival[-1]),
        "initial_minus_final_survival": D_norm,
        "cumulative_roof_midpoint_loss": D_roof,
        "roof_closure_residual": closure_residual,
        "roof_closure_relative": closure_relative,
        "telescoping_residual": telescoping_residual,
        "decomposed_residual": decomposed_residual,
        "minimum_midpoint_roof_probability": float(np.min(step_roof)),
        "minimum_total_step_loss": float(np.min(step_total)),
        "maximum_survival_increase": float(
            max(0.0, np.max(np.diff(survival), initial=-np.inf))
        ),
        "cumulative_bottom_clamp_loss": float(
            np.sum(step_clamp, dtype=np.float64)
        ),
    }

    linear_solver_summary = {
        "gmres_failure_count": int(np.count_nonzero(gmres_info != 0)),
        "maximum_true_relative_residual": float(np.max(true_residual)),
        "minimum_true_relative_residual": float(np.min(true_residual)),
        "total_gmres_solves": int(np.sum(gmres_solve_count, dtype=np.int64)),
    }

    pending_cross_case = [
        "factorized scalar mode-null comparison (00,10,01)",
        "10/01 spinor isotropy",
        "Cartesian--oscillator curve-level representation discrepancy",
        "monolithic scalar R_h/R_(h/2) convergence ratio",
        "spinor dt=5e-4 versus 2.5e-4 convergence",
        "spinor N=12 versus N=16 shell-cutoff convergence",
        "complete campaign-level stable same-prefix rerun decision",
    ]

    return {
        "loader_stage": LOADER_STAGE,
        "loader_version": LOADER_VERSION,
        "audited_utc": utc_now_iso(),
        "case_prefix": case_prefix,
        "stage_directory": str(stage_dir),
        "verdict": "PASS" if all_checks_passed else "FAIL",
        "all_checks_passed": all_checks_passed,
        "configuration": {
            "propagator_type": propagator_type,
            "detector_label": detector_label,
            "initial_mode": initial_mode,
            "omega": omega,
            "N_shell": n_shell,
            "M_N": expected_m,
            "d_channels": 2 * expected_m,
            "N_z": n_z,
            "h_z": h_z,
            "dt": dt,
            "T_final": t_final,
            "num_steps": num_steps,
            "t_cut_used": t_cut_used,
            "backend": configuration.get("backend_metadata", {}).get("backend"),
            "zero_ambient_bath": configuration.get("zero_ambient_bath"),
            "state_index_formula": configuration.get("state_index_formula"),
        },
        "hash_audit": {
            "configuration_sha256_stored": stored_configuration_hash,
            "configuration_sha256_reconstructed": reconstructed_configuration_hash,
            "configuration_hash_match": configuration_hash_match,
            "source_hash_values": source_hash_values,
            "source_hash_consistent": source_hash_consistent,
            "output_manifest_sha256": actual_output_manifest_hash,
            "status_manifest_hash_match": status_manifest_hash_match,
            "all_raw_manifest_hashes_match": all_manifest_hashes_match,
            "raw_manifest_files": manifest_hash_results,
        },
        "independent_operator_audit": independent_operators,
        "probability_summary": probability_summary,
        "linear_solver_summary": linear_solver_summary,
        "detector_metrics": observed_metrics,
        "solver_metric_reconstruction": stored_metric_comparison,
        "shell_summary": {
            "maximum_subnormalized_shell_sum_residual": shell_sub_sum_residual,
            "maximum_normalized_shell_sum_residual": shell_norm_sum_residual,
            "minimum_shell_population_subnormalized": float(np.min(shell_sub)),
            "minimum_shell_population_normalized": float(np.min(shell_norm)),
        },
        "source_summary": source_summary,
        "insertion_summary": {
            "number_of_vector_records": n_vectors,
            "number_of_retained_channel_rows": int(channel_indices.size),
            "maximum_relative_omitted_norm2": float(
                np.max(
                    np.divide(
                        vector_omitted_norm2,
                        np.maximum(vector_total_norm2, np.finfo(float).tiny),
                    )
                )
            ),
        },
        "stage_manifest_audit": stage_manifest_check,
        "solver_overwrite_and_rerun_record": solver_status.get(
            "overwrite_and_rerun_audit"
        ),
        "checks_by_group": all_check_groups,
        "checks": flat_checks,
        "pending_cross_case_Task06_checks": pending_cross_case,
        "interpretation": {
            "case_level_only": True,
            "raw_solver_outputs_must_remain_on_cluster": True,
            "Task06_still_required_for_branch_closure": True,
            "zero_bath_only": True,
            "nonzero_source_activity_is_not_detector_bath_susceptibility": True,
        },
        "compact_arrays": {
            "times": times,
            "midpoint_times": midpoint_times,
            "survival": survival,
            "step_roof": step_roof,
            "click_density": click_density,
            "true_residual": true_residual,
            "gmres_info": gmres_info,
            "gmres_solve_count": gmres_solve_count,
            "step_total": step_total,
            "step_clamp": step_clamp,
            "step_flux_residual": step_flux_residual,
            "shell_sub": shell_sub,
            "shell_norm": shell_norm,
            "top_sub": top_sub,
            "top_norm": top_norm,
            "s_down_sub": s_down_sub,
            "s_down": s_down,
            "s_up_sub": s_up_sub,
            "s_up": s_up,
            "s_phi_weighted": s_phi_weighted,
            "s_phi": s_phi,
            "r_k_sub": r_k_sub,
            "r_k_norm": r_k_norm,
            "r_k_cumulative": r_k_cumulative,
        },
        "small_input_paths": {
            "configuration": configuration_path,
            "operator_audit": operator_audit_path,
            "solver_audit": solver_audit_path,
            "solver_run_status": solver_status_path,
            "solver_output_hashes": solver_hash_path,
            "copied_solver_source": copied_source_path,
            "stage_manifest": stage_manifest_path if stage_manifest_path.is_file() else None,
        },
        "solver_elapsed_seconds": float(solver_status.get("elapsed_seconds", 0.0)),
        "loader_source_path": loader_source_path,
    }


# =============================================================================
# REPORT AND SHARE PACKAGE
# =============================================================================
def markdown_bool(value: bool) -> str:
    return "PASS" if value else "FAIL"


def build_report(audit: Mapping[str, Any]) -> str:
    config = audit["configuration"]
    p = audit["probability_summary"]
    linear = audit["linear_solver_summary"]
    metrics = audit["detector_metrics"]
    source = audit["source_summary"]
    failed = [name for name, passed in audit["checks"].items() if not passed]

    lines = [
        f"# Task-05 single-case independent audit — `{audit['case_prefix']}`",
        "",
        f"## Verdict: **{audit['verdict']}**",
        "",
        "> This is a per-case integrity and scientific screening result. It does not replace the final multi-case Task-06 loader.",
        "",
        "## Configuration",
        "",
        "| Quantity | Value |",
        "|---|---:|",
        f"| Propagator | `{config['propagator_type']}` |",
        f"| Detector label | `{config['detector_label']}` |",
        f"| Initial mode | `{config['initial_mode']}` |",
        f"| Omega | {config['omega']:.16g} |",
        f"| N shell | {config['N_shell']} |",
        f"| M_N / spin channels | {config['M_N']} / {config['d_channels']} |",
        f"| N_z | {config['N_z']} |",
        f"| dt | {config['dt']:.16g} |",
        f"| T final | {config['T_final']:.16g} |",
        f"| Backend | `{config['backend']}` |",
        "",
        "## Provenance and structural gates",
        "",
        f"- Raw output manifest: **{markdown_bool(audit['hash_audit']['all_raw_manifest_hashes_match'])}**",
        f"- Configuration hash reconstruction: **{markdown_bool(audit['hash_audit']['configuration_hash_match'])}**",
        f"- Source-hash consistency: **{markdown_bool(audit['hash_audit']['source_hash_consistent'])}**",
        f"- Independent operator/source reconstruction: **{markdown_bool(audit['independent_operator_audit']['all_checks_passed'])}**",
        f"- Zero-bath/source-scope guard: **{markdown_bool(audit['independent_operator_audit']['source_scope']['active_environmental_or_density_matrix_code_absent'])}**",
        f"- Positive `+K_N/(2 h_z)` source term found: **{markdown_bool(audit['independent_operator_audit']['source_scope']['positive_K_over_2hz_roof_source_detected'])}**",
        "",
        "## Detector and solver reductions",
        "",
        "| Quantity | Value |",
        "|---|---:|",
        f"| Final survival S(T) | {metrics['S_T']:.12e} |",
        f"| Detected fraction from midpoint loss | {metrics['D_roof']:.12e} |",
        f"| Restricted mean mu*(T) | {metrics['mu_restricted']:.12e} |",
        f"| D_E (t < 3.6) | {metrics['D_E']:.12e} |",
        f"| D_L (t >= 3.6) | {metrics['D_L']:.12e} |",
        f"| Late fraction | {metrics['late_fraction']:.12e} |",
        f"| Peak time / density | {metrics['peak_t']:.12e} / {metrics['peak_g']:.12e} |",
        f"| Roof closure residual | {p['roof_closure_residual']:.12e} |",
        f"| Roof closure relative | {p['roof_closure_relative']:.12e} |",
        f"| Minimum midpoint roof probability | {p['minimum_midpoint_roof_probability']:.12e} |",
        f"| Maximum survival increase | {p['maximum_survival_increase']:.12e} |",
        f"| GMRES failures | {linear['gmres_failure_count']} |",
        f"| Maximum true relative residual | {linear['maximum_true_relative_residual']:.12e} |",
        "",
        "## Source and cutoff diagnostics",
        "",
        "| Quantity | Value |",
        "|---|---:|",
        f"| s_down(0) | {source['launch_s_down']:.12e} |",
        f"| s_phi(0) | {source['launch_s_phi']:.12e} |",
        f"| s_up(0) | {source['launch_s_up']:.12e} |",
        f"| max s_down(t) | {source['maximum_s_down_normalized']:.12e} |",
        f"| max s_phi(t) | {source['maximum_s_phi_normalized']:.12e} |",
        f"| min s_up(t) | {source['minimum_s_up_normalized']:.12e} |",
        f"| max top-shell population | {source['maximum_top_shell_population_normalized']:.12e} |",
        f"| final omitted-K proxy integral | {source['final_r_K_omit_cumulative_integral']:.12e} |",
        "",
    ]

    if failed:
        lines.extend(
            [
                "## Failed gates",
                "",
                *[f"- `{name}`" for name in failed],
                "",
            ]
        )

    lines.extend(
        [
            "## Deliberately pending until Task 06",
            "",
            *[f"- {item}" for item in audit["pending_cross_case_Task06_checks"]],
            "",
            "The raw solver directory must remain unchanged on the cluster. The share ZIP is sufficient for remote per-case review, but it is not a substitute for the raw files required by the final aggregate Task-06 loader.",
            "",
        ]
    )
    return "\n".join(lines)


def create_share_zip(
    zip_path: Path,
    *,
    files: Sequence[Path],
) -> None:
    tmp = zip_path.with_name(zip_path.name + ".tmp")
    with zipfile.ZipFile(tmp, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            if path is not None and path.is_file():
                archive.write(path, arcname=path.name)
    os.replace(tmp, zip_path)


def write_outputs(
    stage_dir: Path,
    case_prefix: str,
    result: Dict[str, Any],
    loader_source_path: Path,
) -> Dict[str, Any]:
    loader_source_copy = case_file(
        stage_dir, case_prefix, "05_single_case_independent_loader.py"
    )
    shutil.copy2(loader_source_path, loader_source_copy)
    loader_source_sha = sha256_file(loader_source_copy)

    compact_arrays = result.pop("compact_arrays")
    small_input_paths = result.pop("small_input_paths")
    result.pop("loader_source_path", None)
    result["loader_source_sha256"] = loader_source_sha

    audit_path = case_file(stage_dir, case_prefix, "loader_audit.json")
    compact_path = case_file(stage_dir, case_prefix, "loader_compact.npz")
    metrics_path = case_file(stage_dir, case_prefix, "loader_metrics.csv")
    report_path = case_file(stage_dir, case_prefix, "loader_report.md")
    loader_hash_path = case_file(stage_dir, case_prefix, "loader_output_hashes.json")
    loader_status_path = case_file(stage_dir, case_prefix, "loader_run_status.json")
    share_zip_path = case_file(stage_dir, case_prefix, "loader_share.zip")

    atomic_write_json(audit_path, json_safe(result))
    atomic_savez_compressed(
        compact_path,
        case_prefix=np.asarray([case_prefix], dtype="U256"),
        propagator_type=np.asarray([result["configuration"]["propagator_type"]], dtype="U32"),
        initial_mode=np.asarray([result["configuration"]["initial_mode"]], dtype="U8"),
        omega=np.asarray([result["configuration"]["omega"]], dtype=np.float64),
        N_shell=np.asarray([result["configuration"]["N_shell"]], dtype=np.int64),
        dt=np.asarray([result["configuration"]["dt"]], dtype=np.float64),
        T_final=np.asarray([result["configuration"]["T_final"]], dtype=np.float64),
        source_sha256=np.asarray(
            [result["hash_audit"]["source_hash_values"]["actual_copied_source_sha256"]],
            dtype="U64",
        ),
        configuration_sha256=np.asarray(
            [result["hash_audit"]["configuration_sha256_stored"]], dtype="U64"
        ),
        **compact_arrays,
    )

    metric_row = {
        "case_prefix": case_prefix,
        "loader_verdict": result["verdict"],
        "propagator_type": result["configuration"]["propagator_type"],
        "detector_label": result["configuration"]["detector_label"],
        "initial_mode": result["configuration"]["initial_mode"],
        "omega": result["configuration"]["omega"],
        "N_shell": result["configuration"]["N_shell"],
        "M_N": result["configuration"]["M_N"],
        "d_channels": result["configuration"]["d_channels"],
        "N_z": result["configuration"]["N_z"],
        "dt": result["configuration"]["dt"],
        "T_final": result["configuration"]["T_final"],
        "backend": result["configuration"]["backend"],
        "source_sha256": result["hash_audit"]["source_hash_values"]["actual_copied_source_sha256"],
        "configuration_sha256": result["hash_audit"]["configuration_sha256_stored"],
        "S_T": result["detector_metrics"]["S_T"],
        "D_roof": result["detector_metrics"]["D_roof"],
        "mu_restricted": result["detector_metrics"]["mu_restricted"],
        "D_E": result["detector_metrics"]["D_E"],
        "D_L": result["detector_metrics"]["D_L"],
        "late_fraction": result["detector_metrics"]["late_fraction"],
        "peak_t": result["detector_metrics"]["peak_t"],
        "peak_g": result["detector_metrics"]["peak_g"],
        "roof_closure_relative": result["probability_summary"]["roof_closure_relative"],
        "minimum_midpoint_roof_probability": result["probability_summary"]["minimum_midpoint_roof_probability"],
        "maximum_survival_increase": result["probability_summary"]["maximum_survival_increase"],
        "gmres_failure_count": result["linear_solver_summary"]["gmres_failure_count"],
        "maximum_true_relative_residual": result["linear_solver_summary"]["maximum_true_relative_residual"],
        "launch_s_down": result["source_summary"]["launch_s_down"],
        "launch_s_phi": result["source_summary"]["launch_s_phi"],
        "launch_s_up": result["source_summary"]["launch_s_up"],
        "maximum_s_down": result["source_summary"]["maximum_s_down_normalized"],
        "maximum_s_phi": result["source_summary"]["maximum_s_phi_normalized"],
        "minimum_s_up": result["source_summary"]["minimum_s_up_normalized"],
        "maximum_top_shell_population": result["source_summary"]["maximum_top_shell_population_normalized"],
        "final_r_K_omit_cumulative_integral": result["source_summary"]["final_r_K_omit_cumulative_integral"],
        "solver_elapsed_seconds": result["solver_elapsed_seconds"],
    }
    write_metrics_csv(metrics_path, metric_row)
    atomic_write_text(report_path, build_report(result))

    status = {
        "loader_stage": LOADER_STAGE,
        "loader_version": LOADER_VERSION,
        "case_prefix": case_prefix,
        "status": "completed" if result["all_checks_passed"] else "completed_with_failed_gate",
        "all_checks_passed": result["all_checks_passed"],
        "completed_utc": utc_now_iso(),
        "loader_source_sha256": loader_source_sha,
        "raw_solver_outputs_retained_on_cluster": True,
        "Task06_still_required": True,
    }
    atomic_write_json(loader_status_path, status)

    share_constituents: List[Path] = [
        loader_source_copy,
        audit_path,
        compact_path,
        metrics_path,
        report_path,
        loader_status_path,
        small_input_paths["configuration"],
        small_input_paths["operator_audit"],
        small_input_paths["solver_audit"],
        small_input_paths["solver_run_status"],
        small_input_paths["solver_output_hashes"],
        small_input_paths["copied_solver_source"],
    ]
    if small_input_paths.get("stage_manifest") is not None:
        share_constituents.append(small_input_paths["stage_manifest"])

    loader_output_hashes = {
        path.name: sha256_file(path)
        for path in share_constituents
        if path is not None and path.is_file()
    }
    atomic_write_json(
        loader_hash_path,
        {
            "hash_algorithm": "SHA-256",
            "case_prefix": case_prefix,
            "loader_source_sha256": loader_source_sha,
            "files": loader_output_hashes,
        },
    )
    share_constituents.append(loader_hash_path)
    create_share_zip(share_zip_path, files=share_constituents)

    return {
        "audit_path": audit_path,
        "compact_path": compact_path,
        "metrics_path": metrics_path,
        "report_path": report_path,
        "loader_hash_path": loader_hash_path,
        "loader_status_path": loader_status_path,
        "loader_source_copy": loader_source_copy,
        "share_zip_path": share_zip_path,
        "share_zip_sha256": sha256_file(share_zip_path),
    }


# =============================================================================
# MAIN
# =============================================================================
def main() -> int:
    stage_dir = RUN_DIRECTORY
    stage_dir.mkdir(parents=True, exist_ok=True)
    loader_source_path: Optional[Path] = None
    temporary_loader_source = False

    try:
        loader_source_path, temporary_loader_source = resolve_loader_source_path(
            stage_dir, CASE_PREFIX
        )
        result = audit_case(stage_dir, CASE_PREFIX, loader_source_path)
        output_paths = write_outputs(
            stage_dir, CASE_PREFIX, result, loader_source_path
        )
        print("[Task-05 single-case loader]")
        print(f"  case:                    {CASE_PREFIX}")
        print(f"  input/output directory:  {stage_dir}")
        print(f"  verdict:                 {result['verdict']}")
        print(f"  source SHA-256:          {result['hash_audit']['source_hash_values']['actual_copied_source_sha256']}")
        print(f"  final survival:          {result['detector_metrics']['S_T']:.12e}")
        print(f"  detected fraction:       {result['detector_metrics']['D_roof']:.12e}")
        print(f"  max true residual:       {result['linear_solver_summary']['maximum_true_relative_residual']:.3e}")
        print(f"  max top-shell pop:       {result['source_summary']['maximum_top_shell_population_normalized']:.3e}")
        print(f"  share ZIP:               {output_paths['share_zip_path']}")
        print(f"  share ZIP SHA-256:       {output_paths['share_zip_sha256']}")
        print("  raw solver files remain on the cluster for Task 06/07.")
        return 0 if result["all_checks_passed"] else 2
    except Exception as exc:
        failure_path = case_file(stage_dir, CASE_PREFIX, "loader_failure.json")
        failure = {
            "loader_stage": LOADER_STAGE,
            "loader_version": LOADER_VERSION,
            "case_prefix": CASE_PREFIX,
            "status": "failed",
            "failed_utc": utc_now_iso(),
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc(),
        }
        try:
            atomic_write_json(failure_path, failure)
        except Exception:
            pass
        print(f"[Task-05 single-case loader] FAILED: {exc}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return 1
    finally:
        if temporary_loader_source and loader_source_path is not None:
            try:
                loader_source_path.unlink(missing_ok=True)
            except Exception:
                pass


if __name__ == "__main__":
    _loader_exit_code = main()
    if globals().get("__file__"):
        raise SystemExit(_loader_exit_code)
