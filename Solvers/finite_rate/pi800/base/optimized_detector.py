"""Frozen detector arithmetic with one dead concatenation released sooner.
Installed with the spectral module globals so all existing telemetry interception
and blockwise numerical operations remain in force. No copies/reductions/solves
are removed or reordered; only the lifetime of an unused temporary is shortened.
"""
from __future__ import annotations
from typing import Any, Dict, Mapping, Tuple, List
import numpy as np
import math,traceback
from pathlib import Path

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
            if batch_index == 0:
                # bundle owns its concatenated data; the original concatenation is dead.
                # The unchanged synchronization above also completes the bundle copy.
                del positive

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
