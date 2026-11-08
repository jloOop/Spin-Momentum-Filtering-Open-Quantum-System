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

N_Z = 1500


KRAUS_BLOCK_COLUMNS = 64


KRAUS_BLOCK_MAX_RESHAPED_WIDTH = N_Z * KRAUS_BLOCK_COLUMNS


KRAUS_BLOCKFIX_TELEMETRY_FILENAME = "bath_kraus_blockfix1_telemetry.json"


KRAUS_BLOCKFIX_SCHEMA = (
    "2026-08-30-task09-es-g5p-bath-kraus-blockfix1-telemetry-v1"
)


TELEMETRY_IOFIX_SCHEMA = (
    "2026-08-30-task09-es-g5p-postdetector-bathtraceblockfix2-telemetry-iofix2-v1"
)


TELEMETRY_FULL_FILENAME = "postdetector_bathtraceblockfix2_telemetry.json"


TELEMETRY_PROGRESS_FILENAME = "postdetector_bathtraceblockfix2_progress.json"


TELEMETRY_PROGRESS_MIN_INTERVAL_SECONDS = 15.0


DT = 5.0e-4


EXACT_FINAL_CEILING = 8.033616179378696e-08


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
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False, default=json_default)
        handle.write("\n")
    os.replace(tmp, path)


def memory_snapshot(label: str, cp: Any) -> Dict[str, Any]:
    free_bytes, total_bytes = cp.cuda.Device().mem_info
    return {
        "label": str(label),
        "utc": utc_now_iso(),
        "driver_used_bytes": int(total_bytes - free_bytes),
        "driver_free_bytes": int(free_bytes),
        "driver_total_bytes": int(total_bytes),
        "pool_used_bytes": int(cp.get_default_memory_pool().used_bytes()),
        "pool_total_bytes": int(cp.get_default_memory_pool().total_bytes()),
    }


def install_bath_kraus_blockfix1(
    *, engine: Any, backend: Any, output_dir: Path,
    block_columns: int = KRAUS_BLOCK_COLUMNS,
) -> Dict[str, Any]:
    """Replace one oversized Kraus SpMM by exact disjoint column-block SpMMs.

    For F with shape (d_channels*n_z, r), the frozen implementation computes
    K @ F.reshape(d_channels, n_z*r). This patch partitions only the factor
    columns. Each block is passed to the unchanged frozen implementation and
    written into the corresponding output columns. Thus the linear map is
    mathematically identical; no truncation, rescaling, or reordered summation
    enters the propagated state.
    """
    if int(block_columns) <= 0:
        raise ValueError("BathKrausBlockFix1 block_columns must be positive")
    original_apply_kraus = engine.apply_kraus
    telemetry_path = output_dir / KRAUS_BLOCKFIX_TELEMETRY_FILENAME
    telemetry: Dict[str, Any] = {
        "schema": KRAUS_BLOCKFIX_SCHEMA,
        "status": "installed",
        "started_utc": utc_now_iso(),
        "current_context": "installed",
        "block_columns": int(block_columns),
        "maximum_allowed_reshaped_rhs_width": int(N_Z * int(block_columns)),
        "map_modified": False,
        "operator_modified": False,
        "state_rescaled": False,
        "trace_restoration_applied": False,
        "logical_calls": [],
    }

    def persist(reason: str) -> None:
        telemetry["updated_utc"] = utc_now_iso()
        telemetry["write_reason"] = str(reason)
        atomic_write_json(telemetry_path, telemetry)

    def set_context(label: str) -> None:
        telemetry["current_context"] = str(label)
        if telemetry["status"] == "installed":
            telemetry["status"] = "running"

    def apply_kraus_blockwise(
        operator: Any, factor: Any, d_channels: int, n_z: int, local_backend: Any
    ) -> Any:
        if local_backend is not backend:
            raise RuntimeError("BathKrausBlockFix1 backend identity changed")
        rows = int(factor.shape[0])
        rank = int(factor.shape[1])
        if rows != int(d_channels) * int(n_z):
            raise RuntimeError(
                f"BathKrausBlockFix1 factor shape mismatch: {factor.shape}, "
                f"d_channels={d_channels}, n_z={n_z}"
            )
        record: Dict[str, Any] = {
            "call_index": len(telemetry["logical_calls"]),
            "context": telemetry["current_context"],
            "input_shape": [rows, rank],
            "d_channels": int(d_channels),
            "n_z": int(n_z),
            "block_columns": int(block_columns),
            "monolithic_reshaped_rhs_width": int(n_z) * rank,
            "blocks": [],
            "status": "running",
            "started_utc": utc_now_iso(),
        }
        telemetry["logical_calls"].append(record)
        if rank == 0:
            result = local_backend.xp.empty_like(factor)
        else:
            result = local_backend.xp.empty_like(factor)
            for block_index, start in enumerate(range(0, rank, int(block_columns))):
                stop = min(rank, start + int(block_columns))
                factor_block = local_backend.xp.ascontiguousarray(factor[:, start:stop])
                mapped_block = original_apply_kraus(
                    operator, factor_block, int(d_channels), int(n_z), local_backend
                )
                local_backend.synchronize()
                expected_shape = (rows, stop - start)
                if tuple(int(value) for value in mapped_block.shape) != expected_shape:
                    raise RuntimeError(
                        f"BathKrausBlockFix1 mapped block shape mismatch: "
                        f"{mapped_block.shape} != {expected_shape}"
                    )
                result[:, start:stop] = mapped_block
                local_backend.synchronize()
                record["blocks"].append({
                    "block_index": int(block_index),
                    "start_column": int(start),
                    "stop_column_exclusive": int(stop),
                    "block_size": int(stop - start),
                    "reshaped_rhs_width": int(n_z) * int(stop - start),
                    "synchronized": True,
                })
                record["last_completed_block"] = int(block_index)
                del factor_block, mapped_block
        result = local_backend.xp.ascontiguousarray(result)
        local_backend.synchronize()
        record.update({
            "status": "completed",
            "completed_utc": utc_now_iso(),
            "output_shape": [int(result.shape[0]), int(result.shape[1])],
            "block_count": len(record["blocks"]),
            "maximum_block_columns": max(
                (int(item["block_size"]) for item in record["blocks"]), default=0
            ),
            "maximum_reshaped_rhs_width": max(
                (int(item["reshaped_rhs_width"]) for item in record["blocks"]), default=0
            ),
        })
        return result

    engine.apply_kraus = apply_kraus_blockwise
    persist("installed")

    def flush_full(reason: str) -> None:
        persist(reason)

    def mark_completed() -> None:
        telemetry.update({
            "status": "completed",
            "completed_utc": utc_now_iso(),
            "failure_phase": None,
        })
        persist("terminal_status_completed")

    def mark_failed(exc: BaseException) -> None:
        telemetry.update({
            "status": "failed",
            "failed_utc": utc_now_iso(),
            "failure_phase": telemetry.get("current_context"),
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        })
        try:
            persist("terminal_status_failed")
        except Exception:
            pass

    def restore() -> None:
        if engine.apply_kraus is apply_kraus_blockwise:
            engine.apply_kraus = original_apply_kraus

    def summary() -> Dict[str, Any]:
        calls = telemetry.get("logical_calls", [])
        completed = [item for item in calls if item.get("status") == "completed"]
        return {
            "schema": KRAUS_BLOCKFIX_SCHEMA,
            "path": str(telemetry_path),
            "status": telemetry.get("status"),
            "block_columns": int(block_columns),
            "logical_call_count": len(calls),
            "completed_logical_call_count": len(completed),
            "maximum_input_rank": max(
                (int(item.get("input_shape", [0, 0])[1]) for item in completed), default=0
            ),
            "maximum_monolithic_reshaped_rhs_width_avoided": max(
                (int(item.get("monolithic_reshaped_rhs_width", 0)) for item in completed), default=0
            ),
            "maximum_actual_block_columns": max(
                (int(item.get("maximum_block_columns", 0)) for item in completed), default=0
            ),
            "maximum_actual_reshaped_rhs_width": max(
                (int(item.get("maximum_reshaped_rhs_width", 0)) for item in completed), default=0
            ),
            "map_modified": False,
            "operator_modified": False,
            "trace_restoration_applied": False,
        }

    return {
        "set_context": set_context,
        "flush_full": flush_full,
        "mark_completed": mark_completed,
        "mark_failed": mark_failed,
        "restore": restore,
        "summary": summary,
        "path": telemetry_path,
        "telemetry": telemetry,
    }


def _compact_telemetry_record(records: Any) -> Dict[str, Any] | None:
    if not isinstance(records, list) or not records:
        return None
    record = records[-1]
    if not isinstance(record, Mapping):
        return None
    keys = (
        "call_index", "context", "status", "shape", "input_shape", "output_shape",
        "block_count", "last_completed_block", "result", "synchronized",
        "sector", "block_index", "start_column", "stop_column_exclusive",
    )
    return {key: record[key] for key in keys if key in record}


def install_postdetector_telemetry_iofix2(
    checkpoint_parent: Any,
    *,
    output_dir: Path,
) -> Dict[str, Any]:
    """Throttle only the cumulative BathTraceBlockFix2 JSON serialization.

    The parent blockwise trace/Kraus/top-shell functions and their in-memory
    telemetry records remain untouched. Only writes targeting the single
    cumulative telemetry filename are intercepted. Other parent JSON writes,
    including per-step detector telemetry, are delegated unchanged.
    """
    original_writer = checkpoint_parent.atomic_write_json
    full_path = output_dir / TELEMETRY_FULL_FILENAME
    progress_path = output_dir / TELEMETRY_PROGRESS_FILENAME
    state: Dict[str, Any] = {
        "installed": True,
        "intercepted_write_requests": 0,
        "delegated_write_requests": 0,
        "full_write_count": 0,
        "progress_write_count": 0,
        "full_write_seconds": 0.0,
        "progress_write_seconds": 0.0,
        "last_progress_monotonic": float("-inf"),
        "last_progress_context": None,
        "last_full_reason": None,
        "latest_payload": None,
    }

    def progress_payload(payload: Mapping[str, Any], reason: str) -> Dict[str, Any]:
        return {
            "schema": TELEMETRY_IOFIX_SCHEMA,
            "status": str(payload.get("status", "unknown")),
            "reason": str(reason),
            "updated_utc": utc_now_iso(),
            "current_context": payload.get("current_context"),
            "full_telemetry_filename": TELEMETRY_FULL_FILENAME,
            "full_write_deferred_during_running_state": True,
            "counts": {
                "physical_trace_calls": len(payload.get("physical_trace_calls", [])),
                "family_trace_calls": len(payload.get("family_trace_calls", [])),
                "kraus_calls": len(payload.get("kraus_calls", [])),
                "top_shell_calls": len(payload.get("top_shell_calls", [])),
            },
            "last_records": {
                "physical_trace": _compact_telemetry_record(payload.get("physical_trace_calls")),
                "family_trace": _compact_telemetry_record(payload.get("family_trace_calls")),
                "kraus": _compact_telemetry_record(payload.get("kraus_calls")),
                "top_shell": _compact_telemetry_record(payload.get("top_shell_calls")),
            },
            "write_statistics": {
                key: value
                for key, value in state.items()
                if key not in {"latest_payload", "last_progress_monotonic"}
            },
        }

    def write_progress(payload: Mapping[str, Any], reason: str, *, force: bool) -> None:
        now = time.monotonic()
        context = str(payload.get("current_context", ""))
        if not force:
            same_context = context == state["last_progress_context"]
            if same_context and now - float(state["last_progress_monotonic"]) < TELEMETRY_PROGRESS_MIN_INTERVAL_SECONDS:
                return
        started = time.perf_counter()
        original_writer(progress_path, progress_payload(payload, reason))
        state["progress_write_seconds"] += float(time.perf_counter() - started)
        state["progress_write_count"] += 1
        state["last_progress_monotonic"] = now
        state["last_progress_context"] = context

    def write_full(payload: Mapping[str, Any], reason: str) -> None:
        started = time.perf_counter()
        original_writer(full_path, payload)
        state["full_write_seconds"] += float(time.perf_counter() - started)
        state["full_write_count"] += 1
        state["last_full_reason"] = str(reason)
        write_progress(payload, reason, force=True)

    def throttled_writer(path: Path, payload: Mapping[str, Any]) -> None:
        target = Path(path)
        if target.name != TELEMETRY_FULL_FILENAME:
            state["delegated_write_requests"] += 1
            original_writer(target, payload)
            return
        state["intercepted_write_requests"] += 1
        state["latest_payload"] = payload
        status = str(payload.get("status", ""))
        if status == "failed":
            write_full(payload, "terminal_status_failed")
        elif status == "installed" and int(state["full_write_count"]) == 0:
            write_full(payload, "terminal_status_installed")
        else:
            # Upstream logical trace/Kraus subcalls may transiently report
            # status="completed".  Treat them as progress; explicit checkpoint
            # and terminal flushes below define complete-file persistence.
            write_progress(payload, "running_progress", force=False)

    checkpoint_parent.atomic_write_json = throttled_writer

    def flush_full(reason: str) -> None:
        payload = state.get("latest_payload")
        if isinstance(payload, Mapping):
            write_full(payload, reason)

    def restore() -> None:
        checkpoint_parent.atomic_write_json = original_writer

    def summary() -> Dict[str, Any]:
        return {
            "schema": TELEMETRY_IOFIX_SCHEMA,
            "full_path": str(full_path),
            "progress_path": str(progress_path),
            "progress_interval_seconds": TELEMETRY_PROGRESS_MIN_INTERVAL_SECONDS,
            **{
                key: value
                for key, value in state.items()
                if key not in {"latest_payload", "last_progress_monotonic"}
            },
        }

    return {
        "flush_full": flush_full,
        "restore": restore,
        "summary": summary,
        "full_path": full_path,
        "progress_path": progress_path,
    }


def append_history(
    histories: Mapping[str, np.ndarray],
    *,
    step: int,
    state: Any,
    positive_survival: float,
    zero_survival: float,
    positive_click: float,
    zero_click: float,
    sector_traces: Sequence[float],
    sector_ranks: Sequence[int],
    representation_increment: float,
    event_increment: float,
    analytic_event_bound: float,
    top_shell: float,
    full_step_closure: float,
    zero_closure: float,
    detector_audit: Mapping[str, Any],
    step_wall_seconds: float,
) -> Dict[str, np.ndarray]:
    node_values = {
        "times": step * DT,
        "positive_survival": positive_survival,
        "zero_survival": zero_survival,
        "cumulative_positive_click": float(state.cumulative_click),
        "cumulative_zero_click": float(state.cumulative_zero_click),
        "representation_ledger": float(state.representation_ledger),
        "representation_ceiling": EXACT_FINAL_CEILING,
        "event_first_crossing_ledger": float(state.event_first_crossing_ledger),
        "cumulative_overflow_bound": float(state.cumulative_overflow_bound),
        "total_rank": int(sum(int(value) for value in sector_ranks)),
        "analytic_event_tail_bound": analytic_event_bound,
        "top_shell_population": top_shell,
    }
    step_values = {
        "positive_step_click": positive_click,
        "zero_step_click": zero_click,
        "gmres_max_residual": float(detector_audit["maximum_multi_rhs_true_residual"]),
        "batch_sample_relative_error": float(detector_audit["sample_batch_vs_independent_relative_error"]),
        "complete_step_ledger_closure": full_step_closure,
        "zero_step_closure": zero_closure,
        "step_wall_seconds": step_wall_seconds,
        "representation_increment": representation_increment,
        "event_increment": event_increment,
        "detector_number_rhs": int(detector_audit["number_rhs"]),
        "detector_number_batches": int(detector_audit["number_batches"]),
        "detector_maximum_actual_batch_columns": int(detector_audit["maximum_actual_batch_columns"]),
        "detector_batch64_contract_passed": 1,
    }
    combined: Dict[str, np.ndarray] = {}
    for name, old in histories.items():
        array = np.asarray(old)
        if name == "sector_traces":
            extension = np.asarray([sector_traces], dtype=array.dtype)
        elif name == "sector_ranks":
            extension = np.asarray([sector_ranks], dtype=array.dtype)
        elif name in node_values:
            extension = np.asarray([node_values[name]], dtype=array.dtype)
        elif name in step_values:
            extension = np.asarray([step_values[name]], dtype=array.dtype)
        else:
            raise RuntimeError(f"Unexpected live-history field: {name}")
        combined[name] = np.concatenate([array, extension], axis=0)
    node_names = {
        "times", "positive_survival", "zero_survival", "cumulative_positive_click",
        "cumulative_zero_click", "representation_ledger", "representation_ceiling",
        "event_first_crossing_ledger", "cumulative_overflow_bound", "total_rank",
        "sector_traces", "sector_ranks", "analytic_event_tail_bound", "top_shell_population",
    }
    for name, array in combined.items():
        expected = step + 1 if name in node_names else step
        if array.shape[0] != expected:
            raise RuntimeError(f"History length mismatch for {name}: {array.shape[0]} != {expected}")
        if not np.all(np.isfinite(array)):
            raise RuntimeError(f"History contains non-finite values: {name}")
    return combined


def block_trace_npy(path: Path, h_z: float, block_rows: int = 4096) -> Dict[str, Any]:
    array = np.load(path, mmap_mode="r", allow_pickle=False)
    if array.ndim != 2:
        raise RuntimeError(f"Checkpoint factor is not two-dimensional: {path}")
    finite = True
    terms: List[float] = []
    for start in range(0, array.shape[0], block_rows):
        block = np.asarray(array[start : start + block_rows])
        finite = finite and bool(np.all(np.isfinite(block)))
        terms.append(float(np.sum(np.abs(block) ** 2, dtype=np.float64)))
    return {
        "shape": tuple(int(value) for value in array.shape),
        "dtype": str(array.dtype),
        "finite": finite,
        "trace": float(h_z * math.fsum(terms)),
    }

