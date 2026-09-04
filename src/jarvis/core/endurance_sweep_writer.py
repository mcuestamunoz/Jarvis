"""Product writer — Option A ESTIMATIVO visibility (4S, labeled, ephemeral).

P27-B already evaluates a caller-supplied ``battery_endurance_sweep``.
This module is the **product** caller: a Gate D paper grid for 4S packs,
labeled assumed, never SKU truth, never persisted on ProjectState.

``CalculationEngine.build`` stays opt-in. DSE must not import this file.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from jarvis.schemas.tool_schema import CalculationBundle

# Gate D paper hypotheses for a 4S pack — NOT SKU characterization.
_V_OC_FULL_V = 16.4
_V_OC_EMPTY_V = 13.2
_V_CUTOFF_V = 14.0
_R_PACK_OHM = (0.020, 0.040)
_I_LOAD_LABEL = (
    "n×motor_hover_current_a (hipótesis de corriente de motor — "
    "NO es I_pack, NO P_battery)"
)
_NOMINAL_V_PER_CELL = 3.7


def build_product_endurance_sweep(
    parameters: Mapping[str, Any],
    bundle: CalculationBundle,
) -> list[dict[str, Any]] | None:
    """Return a 2-point labeled sweep, or None when the 4S/hover gates fail."""
    try:
        cell_count = int(parameters.get("battery_cell_count"))
    except (TypeError, ValueError):
        return None
    if cell_count != 4:
        return None

    try:
        capacity_wh = float(parameters.get("battery_capacity_wh"))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(capacity_wh) or capacity_wh <= 0:
        return None

    current_a = bundle.motor_hover_current_a
    if current_a is None or not math.isfinite(current_a) or current_a <= 0:
        return None

    motors = bundle.motors
    if motors is None or motors < 1:
        return None

    if bundle.hover_energy_autonomy_min is None:
        return None

    i_load_a = float(motors) * float(current_a)
    capacity_ah = capacity_wh / (4 * _NOMINAL_V_PER_CELL)
    points: list[dict[str, Any]] = []
    for r_ohm in _R_PACK_OHM:
        points.append({
            "v_oc_full_v": _V_OC_FULL_V,
            "v_oc_empty_v": _V_OC_EMPTY_V,
            "v_cutoff_v": _V_CUTOFF_V,
            "r_internal_ohm": r_ohm,
            "i_load_a": i_load_a,
            "capacity_ah": capacity_ah,
            "r_internal_scope": "pack",
            "voltage_scope": "pack",
            "i_load_label": _I_LOAD_LABEL,
            "capacity_source": "catalog_nameplate",
        })
    return points


def build_with_estimative_sweep(engine: Any, parameters: Mapping[str, Any]) -> CalculationBundle:
    """Two-pass ``build``: L1 first, then optional labeled L2. Does not mutate ``parameters``."""
    params = dict(parameters)
    first = engine.build(params)
    sweep = build_product_endurance_sweep(params, first)
    if not sweep:
        return first
    second = dict(params)
    second["battery_endurance_sweep"] = sweep
    return engine.build(second)
