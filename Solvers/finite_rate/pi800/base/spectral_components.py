"""Exact selected-function copies from the pinned numerical sources in REFERENCE/.
No historical main(), checkpoint importer, or old compression policy is executed.
See EXTRACTION_MAP.json for the function-level byte identities.
"""
from __future__ import annotations
import hashlib, json, math, os, sys, time, traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple
import numpy as np

DETECTOR_TRACEBLOCK_TELEMETRY_SCHEMA = (
    "2026-08-25-task09-es-g5p-step5114-detector-traceblockfix1-telemetry-v1"
)


POSTDETECTOR_BATHTRACE_TELEMETRY_SCHEMA = (
    "2026-08-26-task09-es-g5p-step5114-postdetector-bathtraceblockfix2-telemetry-v1"
)


SELECTED_TARGET_RANKS = (
    128, 192, 256, 257, 258, 288, 319, 384, 512, 640, 648, 649,
    650, 651, 652, 653, 654, 656, 672, 704, 736, 758, 768, 896, 1024
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    raise TypeError(type(value).__name__)


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False, default=json_default)
        handle.write("\n")
    os.replace(tmp, path)


def memory_snapshot(label: str, cp: Any) -> Dict[str, Any]:
    free_bytes, total_bytes = cp.cuda.Device().mem_info
    pool = cp.get_default_memory_pool()
    return {
        "label": label,
        "utc": utc_now_iso(),
        "driver_free_bytes": int(free_bytes),
        "driver_total_bytes": int(total_bytes),
        "driver_used_bytes": int(total_bytes - free_bytes),
        "cupy_pool_active_bytes": int(pool.used_bytes()),
        "cupy_pool_total_bytes": int(pool.total_bytes()),
        "cupy_pool_cached_unused_bytes": int(pool.free_bytes()),
    }


def run_bundled_detector_traceblockfix1(
    zero_state: Any,
    family: Mapping[int, Any],
    *,
    parent: Any,
    operators: Any,
    parent_config: Any,
    propagator: Any,
    backend: Any,
    crosscheck: bool,
    engine: Any,
    output_dir: Path,
) -> Tuple[Any, Dict[int, Any], float, float, Dict[str, Any]]:
    """Frozen Batch-64 detector with blockwise trace/click reductions.

    Job 9439432 completed every prerequisite through the rank-652 first-half
    compression, then the CUDA context reported an illegal address at the
    first host synchronization following the monolithic positive-output trace
    reduction.  This wrapper changes no state, operator, GMRES solve, batch
    size, rank, rate, roof law, or representation ledger.  It evaluates the
    mathematically identical trace and click sums over the already frozen
    disjoint Batch-64 column partition, synchronizes after each batch stage,
    and writes immutable per-batch telemetry.  The resulting scalar is an
    ordered ``math.fsum`` of float64 batch terms.
    """
    telemetry_path = output_dir / "detector_traceblockfix1_telemetry.json"
    telemetry: Dict[str, Any] = {
        "schema": DETECTOR_TRACEBLOCK_TELEMETRY_SCHEMA,
        "status": "initializing",
        "started_utc": utc_now_iso(),
        "trace_reduction_mode": "disjoint_batch64_float64_terms_then_math_fsum",
        "click_reduction_mode": "disjoint_batch64_float64_terms_then_math_fsum",
        "batch_columns": int(parent_config.detector_rhs_batch_columns),
        "state_modified_by_patch": False,
        "operator_modified_by_patch": False,
        "gmres_modified_by_patch": False,
        "rank_modified_by_patch": False,
        "batches": [],
    }
    phase = "initialize"

    def persist() -> None:
        telemetry["updated_utc"] = utc_now_iso()
        atomic_write_json(telemetry_path, telemetry)

    persist()
    try:
        phase = "combine_family"
        positive, sectors, widths = engine.combine_family(family, backend)
        bundle = backend.xp.ascontiguousarray(
            backend.xp.concatenate([zero_state, positive], axis=1)
        )
        count = int(bundle.shape[1])
        advanced = backend.xp.empty_like(bundle)
        q_roof = backend.xp.empty(
            (operators.d_channels, count), dtype=bundle.dtype
        )

        zero_before = engine.physical_trace(
            zero_state, propagator.h_z, backend
        )
        positive_before_terms: List[float] = []
        zero_after_terms: List[float] = []
        positive_after_terms: List[float] = []
        zero_click_terms: List[float] = []
        positive_click_terms: List[float] = []
        all_infos: List[np.ndarray] = []
        all_residuals: List[np.ndarray] = []
        iterations = 0
        batch_sizes: List[int] = []

        for batch_index, start in enumerate(
            range(0, count, int(parent_config.detector_rhs_batch_columns))
        ):
            stop = min(
                count,
                start + int(parent_config.detector_rhs_batch_columns),
            )
            batch_size = int(stop - start)
            record: Dict[str, Any] = {
                "batch_index": int(batch_index),
                "start_column": int(start),
                "stop_column_exclusive": int(stop),
                "batch_size": batch_size,
                "contains_zero_column": bool(start == 0),
                "status": "started",
                "started_utc": utc_now_iso(),
            }
            telemetry["batches"].append(record)
            telemetry["status"] = "running"
            telemetry["current_batch_index"] = int(batch_index)
            persist()

            phase = f"batch_{batch_index}_input_copy"
            batch = backend.xp.ascontiguousarray(bundle[:, start:stop])
            backend.synchronize()

            positive_before_term = 0.0
            if start == 0:
                if batch_size > 1:
                    positive_before_term = engine.physical_trace(
                        batch[:, 1:], propagator.h_z, backend
                    )
                    positive_before_terms.append(positive_before_term)
            else:
                positive_before_term = engine.physical_trace(
                    batch, propagator.h_z, backend
                )
                positive_before_terms.append(positive_before_term)
            record["positive_before_trace_term"] = float(
                positive_before_term
            )
            record["input_trace_reduction_completed"] = True
            persist()

            phase = f"batch_{batch_index}_advance_many_spinor"
            advanced_batch, q_batch, infos, residuals, used = (
                parent.advance_many_spinor(
                    batch,
                    backend=backend,
                    propagator=propagator,
                    config=parent_config,
                    operators=operators,
                    certified_multi_rhs=True,
                )
            )
            backend.synchronize()
            record["advance_many_spinor_completed"] = True
            record["multi_rhs_inner_iterations"] = int(used)
            record["gmres_failure_count"] = int(
                np.count_nonzero(np.asarray(infos, dtype=np.int32) != 0)
            )
            residual_array = np.asarray(residuals, dtype=np.float64)
            record["maximum_true_residual"] = (
                float(np.max(residual_array)) if residual_array.size else 0.0
            )
            persist()

            phase = f"batch_{batch_index}_blockwise_output_reductions"
            zero_after_term = 0.0
            positive_after_term = 0.0
            zero_click_term = 0.0
            positive_click_term = 0.0
            if start == 0:
                zero_after_term = engine.physical_trace(
                    advanced_batch[:, :1], propagator.h_z, backend
                )
                zero_after_terms.append(zero_after_term)
                zero_click_term = float(
                    parent_config.dt
                    * parent_config.kappa
                    * backend.abs2_sum(q_batch[:, :1])
                )
                zero_click_terms.append(zero_click_term)
                if batch_size > 1:
                    positive_after_term = engine.physical_trace(
                        advanced_batch[:, 1:],
                        propagator.h_z,
                        backend,
                    )
                    positive_after_terms.append(positive_after_term)
                    positive_click_term = float(
                        parent_config.dt
                        * parent_config.kappa
                        * backend.abs2_sum(q_batch[:, 1:])
                    )
                    positive_click_terms.append(positive_click_term)
            else:
                positive_after_term = engine.physical_trace(
                    advanced_batch, propagator.h_z, backend
                )
                positive_after_terms.append(positive_after_term)
                positive_click_term = float(
                    parent_config.dt
                    * parent_config.kappa
                    * backend.abs2_sum(q_batch)
                )
                positive_click_terms.append(positive_click_term)
            backend.synchronize()
            record.update(
                {
                    "zero_after_trace_term": float(zero_after_term),
                    "positive_after_trace_term": float(
                        positive_after_term
                    ),
                    "zero_click_term": float(zero_click_term),
                    "positive_click_term": float(positive_click_term),
                    "blockwise_trace_and_click_reductions_completed": True,
                }
            )
            persist()

            phase = f"batch_{batch_index}_destination_copy"
            advanced[:, start:stop] = advanced_batch
            q_roof[:, start:stop] = q_batch
            backend.synchronize()
            record["destination_copy_synchronized"] = True
            record["memory_after_batch"] = memory_snapshot(
                f"detector_traceblockfix1_batch_{batch_index}", backend._cp
            )
            record["status"] = "completed"
            record["completed_utc"] = utc_now_iso()
            persist()

            all_infos.append(np.asarray(infos, dtype=np.int32))
            all_residuals.append(residual_array)
            iterations += int(used)
            batch_sizes.append(batch_size)
            del batch, advanced_batch, q_batch

        phase = "assemble_blockwise_scalars"
        positive_before = float(math.fsum(positive_before_terms))
        zero_after = float(math.fsum(zero_after_terms))
        positive_after = float(math.fsum(positive_after_terms))
        zero_click = float(math.fsum(zero_click_terms))
        positive_click = float(math.fsum(positive_click_terms))
        backend.synchronize()

        zero_next = backend.xp.ascontiguousarray(advanced[:, :1])
        positive_next_matrix = backend.xp.ascontiguousarray(advanced[:, 1:])
        backend.synchronize()

        infos_all = (
            np.concatenate(all_infos)
            if all_infos
            else np.empty(0, dtype=np.int32)
        )
        residuals_all = (
            np.concatenate(all_residuals)
            if all_residuals
            else np.empty(0, dtype=np.float64)
        )

        sample_relative = 0.0
        sample_click_difference = 0.0
        independent_infos: List[int] = []
        independent_residuals: List[float] = []
        sample_indices: List[int] = []
        if crosscheck:
            phase = "independent_sample_crosscheck"
            candidates = sorted(
                set([0, 1, max(0, count // 2), count - 1])
            )
            sample_indices = [
                index for index in candidates if 0 <= index < count
            ]
            selector = (
                sample_indices
                if backend.name == "scipy"
                else backend._cp.asarray(sample_indices)
            )
            sample = backend.xp.ascontiguousarray(bundle[:, selector])
            independent, q_ind, info_ind, residual_ind, _ = (
                parent.advance_many_spinor(
                    sample,
                    backend=backend,
                    propagator=propagator,
                    config=parent_config,
                    operators=operators,
                    certified_multi_rhs=False,
                )
            )
            backend.synchronize()
            batch_sample = backend.xp.ascontiguousarray(
                advanced[:, selector]
            )
            backend.synchronize()
            scale = max(
                math.sqrt(propagator.h_z) * backend.norm(independent),
                np.finfo(float).tiny,
            )
            sample_relative = (
                math.sqrt(propagator.h_z)
                * backend.norm(batch_sample - independent)
                / scale
            )
            click_sample_batch = float(
                parent_config.dt
                * parent_config.kappa
                * backend.abs2_sum(q_roof[:, selector])
            )
            click_sample_ind = float(
                parent_config.dt
                * parent_config.kappa
                * backend.abs2_sum(q_ind)
            )
            sample_click_difference = abs(
                click_sample_batch - click_sample_ind
            )
            independent_infos = np.asarray(
                info_ind, dtype=np.int32
            ).tolist()
            independent_residuals = np.asarray(
                residual_ind, dtype=np.float64
            ).tolist()
            backend.synchronize()

        audit = {
            "number_rhs": count,
            "batch_columns": int(
                parent_config.detector_rhs_batch_columns
            ),
            "number_batches": len(batch_sizes),
            "batch_sizes": batch_sizes,
            "maximum_actual_batch_columns": max(batch_sizes, default=0),
            "batch64_contract_respected": bool(
                all(
                    size
                    <= int(parent_config.detector_rhs_batch_columns)
                    for size in batch_sizes
                )
            ),
            "multi_rhs_info": infos_all.tolist(),
            "maximum_multi_rhs_true_residual": (
                float(np.max(residuals_all))
                if residuals_all.size
                else 0.0
            ),
            "multi_rhs_inner_iterations": int(iterations),
            "zero_before": float(zero_before),
            "positive_before": float(positive_before),
            "zero_after": float(zero_after),
            "positive_after": float(positive_after),
            "zero_click": float(zero_click),
            "positive_click": float(positive_click),
            "zero_midpoint_closure": float(
                zero_before - zero_after - zero_click
            ),
            "positive_midpoint_closure": float(
                positive_before - positive_after - positive_click
            ),
            "sample_indices": sample_indices,
            "sample_independent_info": independent_infos,
            "maximum_sample_independent_true_residual": max(
                independent_residuals, default=0.0
            ),
            "sample_batch_vs_independent_relative_error": float(
                sample_relative
            ),
            "sample_midpoint_probability_absolute_difference": float(
                sample_click_difference
            ),
            "trace_reduction_mode": (
                "disjoint_batch64_float64_terms_then_math_fsum"
            ),
            "click_reduction_mode": (
                "disjoint_batch64_float64_terms_then_math_fsum"
            ),
            "positive_before_batch_terms": positive_before_terms,
            "positive_after_batch_terms": positive_after_terms,
            "positive_click_batch_terms": positive_click_terms,
            "zero_after_batch_terms": zero_after_terms,
            "zero_click_batch_terms": zero_click_terms,
            "detector_traceblockfix1_telemetry_file": telemetry_path.name,
        }

        telemetry.update(
            {
                "status": "completed",
                "completed_utc": utc_now_iso(),
                "number_rhs": count,
                "batch_sizes": batch_sizes,
                "zero_before": zero_before,
                "positive_before": positive_before,
                "zero_after": zero_after,
                "positive_after": positive_after,
                "zero_click": zero_click,
                "positive_click": positive_click,
                "zero_midpoint_closure": audit[
                    "zero_midpoint_closure"
                ],
                "positive_midpoint_closure": audit[
                    "positive_midpoint_closure"
                ],
                "failure_phase": None,
            }
        )
        persist()
        return (
            zero_next,
            engine.split_family(positive_next_matrix, sectors, widths),
            zero_click,
            positive_click,
            audit,
        )
    except Exception as exc:
        telemetry.update(
            {
                "status": "failed",
                "failed_utc": utc_now_iso(),
                "failure_phase": phase,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc(),
            }
        )
        try:
            telemetry["memory_at_failure"] = memory_snapshot(
                "detector_traceblockfix1_failure", backend._cp
            )
        except Exception as memory_exc:
            telemetry["memory_at_failure_error"] = repr(memory_exc)
        try:
            persist()
        except Exception:
            pass
        raise


def install_postdetector_bathtraceblockfix2(
    *, engine: Any, backend: Any, output_dir: Path, h_z: float,
    block_columns: int = 64,
) -> Dict[str, Any]:
    """Install diagnostic-only blockwise trace reductions after the detector.

    The state arrays, Kraus operators, Gram products, rank selection, and
    compression transforms are unchanged.  Only scalar trace and top-shell
    reductions are partitioned by columns, synchronized, and combined with
    ordered host-side summation.  Kraus applications are explicitly
    synchronized and recorded but not otherwise modified.
    """
    telemetry_path = output_dir / "postdetector_bathtraceblockfix2_telemetry.json"
    telemetry: Dict[str, Any] = {
        "schema": POSTDETECTOR_BATHTRACE_TELEMETRY_SCHEMA,
        "status": "installed",
        "started_utc": utc_now_iso(),
        "block_columns": int(block_columns),
        "trace_reduction_mode": "disjoint_column_blocks_float64_then_math_fsum",
        "state_modified_by_patch": False,
        "kraus_operator_modified_by_patch": False,
        "gram_modified_by_patch": False,
        "rank_modified_by_patch": False,
        "current_context": "installed",
        "physical_trace_calls": [],
        "family_trace_calls": [],
        "kraus_calls": [],
        "top_shell_calls": [],
    }
    original_apply_kraus = engine.apply_kraus
    original_top_shell_population = engine.top_shell_population

    def persist() -> None:
        telemetry["updated_utc"] = utc_now_iso()
        atomic_write_json(telemetry_path, telemetry)

    def set_context(label: str) -> None:
        telemetry["current_context"] = str(label)
        telemetry["status"] = "running"
        persist()

    def physical_trace_blockwise(factor: Any, local_h_z: float, local_backend: Any) -> float:
        if local_backend is not backend:
            raise RuntimeError("BathTraceBlockFix2 backend identity changed")
        if float(local_h_z) != float(h_z):
            raise RuntimeError("BathTraceBlockFix2 h_z changed")
        columns = int(factor.shape[1])
        record: Dict[str, Any] = {
            "call_index": len(telemetry["physical_trace_calls"]),
            "context": telemetry["current_context"],
            "shape": [int(factor.shape[0]), columns],
            "block_columns": int(block_columns),
            "blocks": [],
            "status": "running",
            "started_utc": utc_now_iso(),
        }
        telemetry["physical_trace_calls"].append(record)
        persist()
        terms: List[float] = []
        for block_index, start in enumerate(range(0, columns, int(block_columns))):
            stop = min(columns, start + int(block_columns))
            block = local_backend.xp.ascontiguousarray(factor[:, start:stop])
            local_backend.synchronize()
            term = float(local_h_z * local_backend.abs2_sum(block))
            local_backend.synchronize()
            terms.append(term)
            record["blocks"].append({
                "block_index": int(block_index),
                "start_column": int(start),
                "stop_column_exclusive": int(stop),
                "block_size": int(stop - start),
                "trace_term": term,
                "synchronized": True,
            })
            record["last_completed_block"] = int(block_index)
            persist()
            del block
        result = float(math.fsum(terms))
        record.update({
            "status": "completed",
            "completed_utc": utc_now_iso(),
            "result": result,
            "block_count": len(terms),
        })
        persist()
        return result

    def family_trace_blockwise(
        family: Mapping[int, Any], local_h_z: float, local_backend: Any
    ) -> float:
        record: Dict[str, Any] = {
            "call_index": len(telemetry["family_trace_calls"]),
            "context": telemetry["current_context"],
            "sector_terms": [],
            "status": "running",
            "started_utc": utc_now_iso(),
        }
        telemetry["family_trace_calls"].append(record)
        persist()
        terms: List[float] = []
        for sector, factor in sorted(family.items()):
            term = physical_trace_blockwise(factor, local_h_z, local_backend)
            terms.append(term)
            record["sector_terms"].append({
                "sector": int(sector),
                "columns": int(factor.shape[1]),
                "trace_term": float(term),
            })
            persist()
        result = float(math.fsum(terms))
        record.update({
            "status": "completed",
            "completed_utc": utc_now_iso(),
            "result": result,
        })
        persist()
        return result

    def apply_kraus_synchronized(
        operator: Any, factor: Any, d_channels: int, n_z: int, local_backend: Any
    ) -> Any:
        record: Dict[str, Any] = {
            "call_index": len(telemetry["kraus_calls"]),
            "context": telemetry["current_context"],
            "input_shape": [int(factor.shape[0]), int(factor.shape[1])],
            "status": "running",
            "started_utc": utc_now_iso(),
        }
        telemetry["kraus_calls"].append(record)
        persist()
        mapped = original_apply_kraus(
            operator, factor, d_channels, n_z, local_backend
        )
        local_backend.synchronize()
        record.update({
            "status": "completed",
            "completed_utc": utc_now_iso(),
            "output_shape": [int(mapped.shape[0]), int(mapped.shape[1])],
            "synchronized": True,
        })
        persist()
        return mapped

    def top_shell_population_blockwise(
        family: Mapping[int, Any], *, operators: Any, config: Any,
        h_z: float, backend: Any,
    ) -> float:
        record: Dict[str, Any] = {
            "call_index": len(telemetry["top_shell_calls"]),
            "context": telemetry["current_context"],
            "sector_blocks": [],
            "status": "running",
            "started_utc": utc_now_iso(),
        }
        telemetry["top_shell_calls"].append(record)
        persist()
        channel = np.zeros(operators.d_channels, dtype=np.float64)
        for sector, factor in sorted(family.items()):
            columns = int(factor.shape[1])
            for block_index, start in enumerate(range(0, columns, int(block_columns))):
                stop = min(columns, start + int(block_columns))
                block = backend.xp.ascontiguousarray(factor[:, start:stop])
                backend.synchronize()
                shaped = block.reshape(
                    operators.d_channels, config.n_z * int(stop - start)
                )
                values = h_z * backend.xp.sum(
                    shaped.real * shaped.real + shaped.imag * shaped.imag,
                    axis=1,
                    dtype=backend.float64,
                )
                channel += np.asarray(backend.to_cpu(values), dtype=np.float64)
                backend.synchronize()
                record["sector_blocks"].append({
                    "sector": int(sector),
                    "block_index": int(block_index),
                    "start_column": int(start),
                    "stop_column_exclusive": int(stop),
                    "synchronized": True,
                })
                persist()
                del block, shaped, values
        orbital = channel.reshape(2, operators.m_modes).sum(axis=0)
        result = float(
            np.sum(
                orbital[operators.shell_of_mode == config.n_shell],
                dtype=np.float64,
            )
        )
        record.update({
            "status": "completed",
            "completed_utc": utc_now_iso(),
            "result": result,
        })
        persist()
        return result

    def mark_completed() -> None:
        telemetry.update({
            "status": "completed",
            "completed_utc": utc_now_iso(),
            "failure_phase": None,
        })
        persist()

    def mark_failed(exc: BaseException) -> None:
        telemetry.update({
            "status": "failed",
            "failed_utc": utc_now_iso(),
            "failure_phase": telemetry.get("current_context"),
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc(),
        })
        try:
            telemetry["memory_at_failure"] = memory_snapshot(
                "postdetector_bathtraceblockfix2_failure", backend._cp
            )
        except Exception as memory_exc:
            telemetry["memory_at_failure_error"] = repr(memory_exc)
        try:
            persist()
        except Exception:
            pass

    engine.physical_trace = physical_trace_blockwise
    engine.family_trace = family_trace_blockwise
    engine.apply_kraus = apply_kraus_synchronized
    engine.top_shell_population = top_shell_population_blockwise
    persist()
    return {
        "path": telemetry_path,
        "telemetry": telemetry,
        "set_context": set_context,
        "mark_completed": mark_completed,
        "mark_failed": mark_failed,
    }


def build_rank_ladder(
    values: np.ndarray,
    sectors: np.ndarray,
    local_indices: np.ndarray,
    *,
    support_by_sector: Mapping[int, int],
    ledger_before: float,
    ceiling: float,
    selected_targets: Sequence[int],
) -> Tuple[Dict[str, Any], Dict[str, np.ndarray]]:
    values = np.asarray(values, dtype=np.float64)
    sectors = np.asarray(sectors, dtype=np.int32)
    local_indices = np.asarray(local_indices, dtype=np.int32)
    order = sorted(range(values.size), key=lambda i: (float(values[i]), int(sectors[i]), int(local_indices[i])))
    values = values[order]
    sectors = sectors[order]
    local_indices = local_indices[order]
    support_rank = int(values.size)
    cumulative = np.asarray(
        [math.fsum(float(value) for value in values[:count]) for count in range(1, support_rank + 1)],
        dtype=np.float64,
    )
    available = float(ceiling - ledger_before)
    target_ranks = np.arange(0, support_rank + 1, dtype=np.int64)
    discard = np.empty(support_rank + 1, dtype=np.float64)
    for target in range(support_rank + 1):
        remove_count = support_rank - target
        discard[target] = 0.0 if remove_count == 0 else float(cumulative[remove_count - 1])
    admissible = discard <= available
    admissible_targets = np.flatnonzero(admissible)
    minimum_rank = int(admissible_targets[0]) if admissible_targets.size else None
    selected: Dict[str, Any] = {}
    target_set = set(int(value) for value in selected_targets)
    target_set.add(support_rank)
    if minimum_rank is not None:
        for delta in range(-3, 4):
            target_set.add(minimum_rank + delta)
    for target in sorted(value for value in target_set if 0 <= value <= support_rank):
        remove_count = support_rank - target
        removed_sectors = sectors[:remove_count]
        removed_by_sector = {
            int(sector): int(np.count_nonzero(removed_sectors == int(sector)))
            for sector in sorted(support_by_sector)
        }
        retained_by_sector = {
            int(sector): int(support_by_sector[int(sector)] - removed_by_sector[int(sector)])
            for sector in sorted(support_by_sector)
        }
        required = float(discard[target])
        selected[str(target)] = {
            "target_total_rank": int(target),
            "number_positive_modes_to_discard": int(remove_count),
            "minimum_positive_trace_discard": required,
            "current_available": available,
            "admissible_under_current_ceiling": bool(required <= available),
            "minimum_additional_ceiling": float(max(0.0, required - available)),
            "removed_modes_by_sector": removed_by_sector,
            "retained_rank_by_sector": retained_by_sector,
            "retained_rank_sum": int(sum(retained_by_sector.values())),
            "largest_removed_positive_eigenvalue": float(values[remove_count - 1]) if remove_count > 0 else 0.0,
            "smallest_next_retained_positive_eigenvalue": float(values[remove_count]) if remove_count < support_rank else None,
        }
    summary = {
        "ledger_before": float(ledger_before),
        "ceiling": float(ceiling),
        "available": available,
        "support_rank": support_rank,
        "support_rank_by_sector": {int(key): int(value) for key, value in support_by_sector.items()},
        "minimum_admissible_rank_under_current_ceiling": minimum_rank,
        "selected_rank_ladders": selected,
    }
    arrays = {
        "global_positive_eigenvalues_ascending": values,
        "global_positive_eigenvalue_sectors": sectors,
        "global_positive_eigenvalue_local_indices": local_indices,
        "global_positive_cumulative_ascending": cumulative,
        "target_total_ranks": target_ranks,
        "minimum_positive_trace_discard_by_target_rank": discard,
        "target_rank_admissible_under_current_ceiling": admissible.astype(np.int8),
        "ledger_before": np.asarray([ledger_before], dtype=np.float64),
        "ceiling": np.asarray([ceiling], dtype=np.float64),
        "available": np.asarray([available], dtype=np.float64),
        "support_rank": np.asarray([support_rank], dtype=np.int64),
        "minimum_admissible_rank": np.asarray([-1 if minimum_rank is None else minimum_rank], dtype=np.int64),
    }
    return summary, arrays


def analyze_family_spectrum(
    family: Mapping[int, Any],
    *,
    h_z: float,
    backend: Any,
    engine: Any,
    ledger_before: float,
    ceiling: float,
    call_index: int,
    step: int,
    half: str,
    half_time: float,
) -> Tuple[Dict[str, Any], Dict[str, np.ndarray], Dict[str, np.ndarray], Dict[int, Dict[str, Any]]]:
    gram_arrays: Dict[str, np.ndarray] = {}
    spectrum_arrays: Dict[str, np.ndarray] = {}
    per_sector: Dict[str, Any] = {}
    internal: Dict[int, Dict[str, Any]] = {}
    entries: List[Tuple[float, int, int]] = []
    support_by_sector: Dict[int, int] = {}
    raw_rank = 0
    negative_mass = 0.0
    max_herm = 0.0
    total_trace_factors = 0.0
    for sector, factor in sorted(family.items()):
        raw_rank += int(factor.shape[1])
        gram_backend = h_z * (factor.conj().T @ factor)
        gram_unsym = np.asarray(backend.to_cpu(gram_backend), dtype=np.complex128)
        herm = float(np.max(np.abs(gram_unsym - gram_unsym.conj().T), initial=0.0))
        max_herm = max(max_herm, herm)
        gram = 0.5 * (gram_unsym + gram_unsym.conj().T)
        raw_values, vectors = np.linalg.eigh(gram)
        raw_values = np.asarray(raw_values, dtype=np.float64)
        positive = np.maximum(raw_values, 0.0)
        negative = float(np.sum(np.maximum(-raw_values, 0.0), dtype=np.float64))
        negative_mass += negative
        support_indices = np.flatnonzero(positive > 0.0)
        support_by_sector[int(sector)] = int(support_indices.size)
        for index in support_indices:
            entries.append((float(positive[index]), int(sector), int(index)))
        trace_factor = float(engine.physical_trace(factor, h_z, backend))
        total_trace_factors += trace_factor
        gram_arrays[f"sector_{sector}_gram"] = gram
        spectrum_arrays[f"sector_{sector}_raw_eigenvalues_ascending"] = raw_values
        spectrum_arrays[f"sector_{sector}_positive_eigenvalues_ascending"] = positive
        internal[int(sector)] = {
            "positive": positive,
            "vectors": vectors,
            "raw_values": raw_values,
            "trace_factor": trace_factor,
            "hermiticity": herm,
        }
        per_sector[str(sector)] = {
            "raw_columns": int(factor.shape[1]),
            "exact_positive_support_rank": int(support_indices.size),
            "trace_from_factor": trace_factor,
            "trace_from_gram": float(np.trace(gram).real),
            "trace_from_raw_eigenvalues": float(np.sum(raw_values, dtype=np.float64)),
            "trace_from_positive_eigenvalues": float(np.sum(positive, dtype=np.float64)),
            "minimum_raw_eigenvalue": float(raw_values[0]) if raw_values.size else 0.0,
            "maximum_raw_eigenvalue": float(raw_values[-1]) if raw_values.size else 0.0,
            "negative_gram_mass": negative,
            "gram_hermiticity_residual_before_symmetrization": herm,
        }
        del gram_backend, gram_unsym
    entries.sort(key=lambda item: (item[0], item[1], item[2]))
    values = np.asarray([item[0] for item in entries], dtype=np.float64)
    sectors = np.asarray([item[1] for item in entries], dtype=np.int32)
    local_indices = np.asarray([item[2] for item in entries], dtype=np.int32)
    ladder, ladder_arrays = build_rank_ladder(
        values, sectors, local_indices,
        support_by_sector=support_by_sector,
        ledger_before=ledger_before,
        ceiling=ceiling,
        selected_targets=SELECTED_TARGET_RANKS,
    )
    spectrum_arrays.update(ladder_arrays)
    spectrum_arrays.update({
        "call_index": np.asarray([call_index], dtype=np.int64),
        "step": np.asarray([step], dtype=np.int64),
        "half_time": np.asarray([half_time], dtype=np.float64),
        "raw_rank": np.asarray([raw_rank], dtype=np.int64),
        "negative_gram_mass": np.asarray([negative_mass], dtype=np.float64),
    })
    summary = {
        "step": int(step),
        "call_index": int(call_index),
        "half": str(half),
        "half_time": float(half_time),
        "raw_rank": int(raw_rank),
        "support_rank": int(ladder["support_rank"]),
        "support_rank_by_sector": ladder["support_rank_by_sector"],
        "negative_gram_mass": float(negative_mass),
        "maximum_gram_hermiticity_residual_before_symmetrization": float(max_herm),
        "total_trace_from_factors": float(total_trace_factors),
        "total_positive_eigenvalue_trace": float(math.fsum(float(value) for value in values)),
        "ledger_before": float(ledger_before),
        "ceiling": float(ceiling),
        "available": float(ladder["available"]),
        "minimum_admissible_rank_under_current_ceiling": ladder["minimum_admissible_rank_under_current_ceiling"],
        "selected_rank_ladders": ladder["selected_rank_ladders"],
        "per_sector": per_sector,
    }
    return summary, gram_arrays, spectrum_arrays, internal


def compress_from_analysis(
    family: Mapping[int, Any],
    *,
    internal: Mapping[int, Mapping[str, Any]],
    target_rank: int,
    ledger_base: float,
    committed_terms: Sequence[float],
    ledger_before: float,
    ceiling: float,
    h_z: float,
    backend: Any,
    engine: Any,
) -> Tuple[Dict[int, Any], Dict[str, Any], float]:
    candidates: List[Tuple[float, int, int]] = []
    for sector, data in sorted(internal.items()):
        positive = np.asarray(data["positive"], dtype=np.float64)
        for index in np.flatnonzero(positive > 0.0):
            candidates.append((float(positive[index]), int(sector), int(index)))
    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    support_rank = len(candidates)
    remove_count = max(0, support_rank - int(target_rank))
    removed = candidates[:remove_count]
    discarded_keys = {(sector, index) for _value, sector, index in removed}
    spectral_discard = float(math.fsum(value for value, _sector, _index in removed))
    available = float(ceiling - ledger_before)
    if spectral_discard > available:
        raise RuntimeError(
            f"Rank-{target_rank} compression is not admissible: "
            f"{spectral_discard} > {available}"
        )
    input_trace = float(engine.family_trace(family, h_z, backend))
    output: Dict[int, Any] = {}
    per_sector: List[Dict[str, Any]] = []
    for sector, factor in sorted(family.items()):
        data = internal[int(sector)]
        positive = np.asarray(data["positive"], dtype=np.float64)
        vectors = np.asarray(data["vectors"], dtype=np.complex128)
        keep = np.asarray(
            [
                value > 0.0 and (int(sector), int(index)) not in discarded_keys
                for index, value in enumerate(positive)
            ],
            dtype=bool,
        )
        if np.any(keep):
            transform = backend.to_backend_array(np.asarray(vectors[:, keep], dtype=np.complex128))
            retained = backend.xp.ascontiguousarray(factor @ transform)
            output[int(sector)] = retained
            output_trace_sector = float(engine.physical_trace(retained, h_z, backend))
            retained_rank = int(retained.shape[1])
        else:
            output_trace_sector = 0.0
            retained_rank = 0
        per_sector.append({
            "sector": int(sector),
            "input_columns": int(factor.shape[1]),
            "input_trace": float(data["trace_factor"]),
            "retained_rank": retained_rank,
            "output_trace": output_trace_sector,
            "direct_trace_deficit": float(data["trace_factor"] - output_trace_sector),
            "trace_restoration_applied": False,
        })
    output_trace = float(engine.family_trace(output, h_z, backend))
    direct_deficit = float(input_trace - output_trace)
    trace_residual = float(direct_deficit - spectral_discard)
    trace_growth = float(max(0.0, -direct_deficit))
    if trace_growth > engine.COMPRESSION_TRACE_GROWTH_TOL:
        raise RuntimeError(f"Rank-{target_rank} compression trace-growth guard failed")
    if abs(trace_residual) > engine.COMPRESSION_TRACE_GROWTH_TOL:
        raise RuntimeError(f"Rank-{target_rank} compression trace accounting failed: {trace_residual}")
    ledger_after = float(math.fsum([float(ledger_base), *(float(v) for v in committed_terms), spectral_discard]))
    if ledger_after > ceiling:
        raise RuntimeError(f"Rank-{target_rank} ledger exceeded exact ceiling")
    rank_after = int(engine.family_rank(output))
    if rank_after != int(target_rank):
        raise RuntimeError(f"Rank-{target_rank} compression retained {rank_after}")
    audit = {
        "target_rank": int(target_rank),
        "support_rank": int(support_rank),
        "remove_count": int(remove_count),
        "input_trace": input_trace,
        "output_trace": output_trace,
        "spectral_positive_discard": spectral_discard,
        "direct_trace_deficit": direct_deficit,
        "trace_accounting_residual": trace_residual,
        "trace_growth_guard": trace_growth,
        "ledger_before": float(ledger_before),
        "ledger_after": ledger_after,
        "available_before": available,
        "remaining_margin_after": float(ceiling - ledger_after),
        "rank_after": rank_after,
        "sector_ranks_after": {int(k): int(v.shape[1]) for k, v in sorted(output.items())},
        "per_sector": per_sector,
        "trace_restoration_applied": False,
    }
    return output, audit, spectral_discard

