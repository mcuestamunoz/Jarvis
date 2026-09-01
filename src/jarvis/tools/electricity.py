from __future__ import annotations

import math
from typing import Any

from jarvis.schemas.tool_schema import ToolResult


# Energy domain — battery mass estimation

# Conservative LiPo energy density (Wh/kg).
# Real range: 120–200 Wh/kg. 150 is a safe mid-range for 4S–6S packs.
LIPO_ENERGY_DENSITY_WH_KG: float = 150.0


def estimate_battery_mass_kg(capacity_wh: float) -> float:
    """Estimate battery mass from capacity using LiPo energy density.

    Returns 0.0 for non-positive capacity to avoid division errors.
    """
    if capacity_wh <= 0.0:
        return 0.0
    return round(capacity_wh / LIPO_ENERGY_DENSITY_WH_KG, 3)


# Energy domain — battery autonomy

def calculate_autonomy_min(battery_capacity_wh: float, total_power_w: float) -> ToolResult:
    """Calculate operational autonomy in minutes.

    Formula: autonomy_min = (battery_capacity_wh / total_power_w) * 60
    """
    autonomy_min = (battery_capacity_wh / total_power_w) * 60.0 if total_power_w > 0 else 0.0
    return ToolResult(
        tool_name="calculate_autonomy_min",
        inputs={
            "battery_capacity_wh": battery_capacity_wh,
            "total_power_w": total_power_w,
        },
        outputs={"autonomy_min": round(autonomy_min, 4)},
    )


# Phase 2.7-B (Parametric / Estimative Battery Endurance Sweep, ★★1-★★13
# locked) — a deterministic, caller-parameterized circuit-equation
# evaluation. Every numeric input here is an ASSUMPTION the caller supplies
# (or a nameplate passthrough) — this module invents no defaults for
# V_oc/R/I and does not characterize any real SKU. See
# investigation_report_phase27b_parametric_battery_estimate.md Gate D for
# the physics and investigation_contract_phase27b_parametric_battery_
# estimate.md §2 for the locked evaluation order (voltage-space, not a bare
# SOC>=1 branch).

_VALID_SCOPES = ("pack", "cell")


def estimate_loaded_endurance(
    *,
    v_oc_full_v: float,
    v_oc_empty_v: float,
    r_internal_ohm: float,
    i_load_a: float,
    v_cutoff_v: float,
    capacity_ah: float,
    r_internal_scope: str,
    voltage_scope: str,
) -> ToolResult:
    """Estimate loaded-battery endurance at a constant assumed load current,
    under an assumed linear V_oc(SOC) polyline and a fixed R.

    NOT P_battery, NOT a validated flight-time prediction, NOT usable Wh
    (this is a coulomb-time estimate under the caller's own hypothesis, not
    an energy integral). Outcome is one of:
      - ``refused``     — invalid or scope-mismatched inputs; no endurance
        claim of any kind.
      - ``infeasible``  — the assumed load cannot stay at/above cutoff even
        at SOC=1 (a real, honest result — not an error).
      - ``sustainable`` — endurance_min is a defined number, with
        ``stopping_condition`` distinguishing a voltage-cutoff stop from
        running out of nameplate charge first.
    """
    inputs: dict[str, Any] = {
        "v_oc_full_v": v_oc_full_v,
        "v_oc_empty_v": v_oc_empty_v,
        "r_internal_ohm": r_internal_ohm,
        "i_load_a": i_load_a,
        "v_cutoff_v": v_cutoff_v,
        "capacity_ah": capacity_ah,
        "r_internal_scope": r_internal_scope,
        "voltage_scope": voltage_scope,
    }

    def _refused(reason: str) -> ToolResult:
        return ToolResult(
            tool_name="estimate_loaded_endurance",
            inputs=inputs,
            outputs={
                "outcome": "refused",
                "reason": reason,
                "endurance_min": None,
                "soc_at_cutoff": None,
                "stopping_condition": None,
            },
        )

    numeric_fields = (v_oc_full_v, v_oc_empty_v, r_internal_ohm, i_load_a, v_cutoff_v, capacity_ah)
    if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in numeric_fields):
        return _refused("invalid_input")
    if r_internal_scope not in _VALID_SCOPES or voltage_scope not in _VALID_SCOPES:
        return _refused("scope_mismatch")
    if r_internal_scope != voltage_scope:
        return _refused("scope_mismatch")
    if i_load_a <= 0.0 or capacity_ah <= 0.0 or r_internal_ohm < 0.0 or v_oc_full_v <= v_oc_empty_v:
        return _refused("invalid_input")

    v_full_loaded = v_oc_full_v - i_load_a * r_internal_ohm
    v_empty_loaded = v_oc_empty_v - i_load_a * r_internal_ohm
    ocv_span = v_oc_full_v - v_oc_empty_v

    if v_full_loaded < v_cutoff_v:
        # Diagnostic only (may exceed 1) — the load never clears cutoff at
        # any SOC, so no endurance/coulomb figure is meaningful.
        soc_at_cutoff = (v_cutoff_v - v_oc_empty_v + i_load_a * r_internal_ohm) / ocv_span
        return ToolResult(
            tool_name="estimate_loaded_endurance",
            inputs=inputs,
            outputs={
                "outcome": "infeasible",
                "endurance_min": None,
                "soc_at_cutoff": round(soc_at_cutoff, 4),
                "stopping_condition": None,
            },
        )

    if v_empty_loaded > v_cutoff_v:
        # Cutoff is never reached inside nameplate SOC in [0, 1] — the
        # nameplate coulomb budget runs out first. Capped at capacity/I,
        # never a super-nameplate duration.
        endurance_min = capacity_ah / i_load_a * 60.0
        return ToolResult(
            tool_name="estimate_loaded_endurance",
            inputs=inputs,
            outputs={
                "outcome": "sustainable",
                "endurance_min": round(endurance_min, 4),
                "soc_at_cutoff": 0.0,
                "stopping_condition": "nameplate_exhausted",
            },
        )

    soc_at_cutoff = (v_cutoff_v - v_oc_empty_v + i_load_a * r_internal_ohm) / ocv_span
    endurance_min = capacity_ah * (1.0 - soc_at_cutoff) / i_load_a * 60.0
    return ToolResult(
        tool_name="estimate_loaded_endurance",
        inputs=inputs,
        outputs={
            "outcome": "sustainable",
            "endurance_min": round(endurance_min, 4),
            "soc_at_cutoff": round(soc_at_cutoff, 4),
            "stopping_condition": "voltage_cutoff",
        },
    )


def estimate_loaded_endurance_sweep(points: list[dict[str, Any]]) -> list[ToolResult]:
    """Run ``estimate_loaded_endurance`` once per caller-supplied point.

    No built-in grid, no default Voc/R/I — every point is exactly what the
    caller passed. A refused or infeasible point does not abort the sweep;
    each point independently yields one ToolResult, in order.
    """
    results: list[ToolResult] = []
    for point in points:
        results.append(estimate_loaded_endurance(
            v_oc_full_v=point.get("v_oc_full_v"),
            v_oc_empty_v=point.get("v_oc_empty_v"),
            r_internal_ohm=point.get("r_internal_ohm"),
            i_load_a=point.get("i_load_a"),
            v_cutoff_v=point.get("v_cutoff_v"),
            capacity_ah=point.get("capacity_ah"),
            r_internal_scope=point.get("r_internal_scope"),
            voltage_scope=point.get("voltage_scope"),
        ))
    return results
