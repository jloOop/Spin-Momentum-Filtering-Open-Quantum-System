"""Exact marshalling optimization only: same sorted values, fsum order, and rounding.
The original implementation remains frozen in spectral_components.py. No np.cumsum,
parallel reduction, tolerance adjustment, or changed rank decision is introduced.
"""
from __future__ import annotations
import math
import numpy as np
from typing import Any, Dict, Mapping, Sequence, Tuple

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
    scalar_values = values.tolist()  # Same binary64-to-Python-float conversion, performed once.
    cumulative = np.asarray(
        [math.fsum(scalar_values[:count]) for count in range(1, support_rank + 1)],
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
