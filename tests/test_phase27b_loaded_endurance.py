"""Phase 2.7-B — Parametric / Estimative Battery Endurance Sweep.

investigation_report_phase27b_parametric_battery_estimate.md Gate D/E ·
implementation_contract_phase27b_parametric_battery_estimate.md (v0.2)

``estimate_loaded_endurance`` is a deterministic, caller-parameterized
circuit-equation evaluation — every V_oc/R/I/cutoff input is the caller's
own ASSUMED hypothesis, never a sourced SKU characterization, never
``P_battery``. Opt-in only: ``CalculationEngine.build()`` without
``parameters["battery_endurance_sweep"]`` must leave L1
(``hover_energy_autonomy_min``/``autonomy_min``) and the new bundle fields
completely unaffected.
"""
from __future__ import annotations

import json

import pytest

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.tools.electricity import estimate_loaded_endurance, estimate_loaded_endurance_sweep

# Shared labeled hypothesis bookends for the paper-exercise-style cases below
# (generic 4S LiPo chemistry rest voltage, NOT sourced, NOT SKU-specific —
# see investigation_report_phase27b_parametric_battery_estimate.md Gate D).
V_OC_FULL = 16.4
V_OC_EMPTY = 13.2
CAPACITY_AH = 1.5


def test_scope_mismatch_refused():
    r = estimate_loaded_endurance(
        v_oc_full_v=V_OC_FULL, v_oc_empty_v=V_OC_EMPTY, r_internal_ohm=0.020,
        i_load_a=68.0, v_cutoff_v=14.0, capacity_ah=CAPACITY_AH,
        r_internal_scope="pack", voltage_scope="cell",
    )
    assert r.outputs["outcome"] == "refused"
    assert r.outputs["reason"] == "scope_mismatch"
    assert r.outputs["endurance_min"] is None


def test_negative_resistance_refused():
    r = estimate_loaded_endurance(
        v_oc_full_v=V_OC_FULL, v_oc_empty_v=V_OC_EMPTY, r_internal_ohm=-0.02,
        i_load_a=68.0, v_cutoff_v=14.0, capacity_ah=CAPACITY_AH,
        r_internal_scope="pack", voltage_scope="pack",
    )
    assert r.outputs["outcome"] == "refused"
    assert r.outputs["reason"] == "invalid_input"


def test_zero_resistance_allowed():
    r = estimate_loaded_endurance(
        v_oc_full_v=V_OC_FULL, v_oc_empty_v=V_OC_EMPTY, r_internal_ohm=0.0,
        i_load_a=68.0, v_cutoff_v=14.0, capacity_ah=CAPACITY_AH,
        r_internal_scope="pack", voltage_scope="pack",
    )
    assert r.outputs["outcome"] != "refused"


def test_sustainable_voltage_cutoff_matches_investigation_numbers():
    r = estimate_loaded_endurance(
        v_oc_full_v=V_OC_FULL, v_oc_empty_v=V_OC_EMPTY, r_internal_ohm=0.020,
        i_load_a=68.0, v_cutoff_v=14.0, capacity_ah=CAPACITY_AH,
        r_internal_scope="pack", voltage_scope="pack",
    )
    assert r.outputs["outcome"] == "sustainable"
    assert r.outputs["stopping_condition"] == "voltage_cutoff"
    assert r.outputs["soc_at_cutoff"] == pytest.approx(0.675, abs=1e-4)
    assert r.outputs["endurance_min"] == pytest.approx(0.4301, abs=1e-4)


def test_higher_resistance_is_infeasible():
    r = estimate_loaded_endurance(
        v_oc_full_v=V_OC_FULL, v_oc_empty_v=V_OC_EMPTY, r_internal_ohm=0.040,
        i_load_a=68.0, v_cutoff_v=14.0, capacity_ah=CAPACITY_AH,
        r_internal_scope="pack", voltage_scope="pack",
    )
    assert r.outputs["outcome"] == "infeasible"
    assert r.outputs["endurance_min"] is None
    # Diagnostic SOC may exceed 1 — the load never clears cutoff at any charge.
    assert r.outputs["soc_at_cutoff"] > 1.0


def test_optimistic_point_matches_investigation_numbers():
    r = estimate_loaded_endurance(
        v_oc_full_v=V_OC_FULL, v_oc_empty_v=V_OC_EMPTY, r_internal_ohm=0.010,
        i_load_a=50.0, v_cutoff_v=13.2, capacity_ah=CAPACITY_AH,
        r_internal_scope="pack", voltage_scope="pack",
    )
    assert r.outputs["outcome"] == "sustainable"
    assert r.outputs["stopping_condition"] == "voltage_cutoff"
    assert r.outputs["endurance_min"] == pytest.approx(1.51875, abs=1e-4)


def test_nameplate_exhausted_never_exceeds_coulomb_budget():
    r = estimate_loaded_endurance(
        v_oc_full_v=V_OC_FULL, v_oc_empty_v=V_OC_EMPTY, r_internal_ohm=0.020,
        i_load_a=68.0, v_cutoff_v=10.0, capacity_ah=CAPACITY_AH,
        r_internal_scope="pack", voltage_scope="pack",
    )
    assert r.outputs["outcome"] == "sustainable"
    assert r.outputs["stopping_condition"] == "nameplate_exhausted"
    assert r.outputs["soc_at_cutoff"] == 0.0
    expected = CAPACITY_AH / 68.0 * 60.0
    assert r.outputs["endurance_min"] == pytest.approx(expected, abs=1e-4)
    assert r.outputs["endurance_min"] == pytest.approx(1.3235, abs=1e-3)
    # Never a super-nameplate duration.
    assert r.outputs["endurance_min"] <= expected + 1e-9


def test_knife_edge_zero_minutes_at_soc_one():
    v_cutoff = V_OC_FULL - 68.0 * 0.020  # constructed to land exactly on V_full_loaded
    r = estimate_loaded_endurance(
        v_oc_full_v=V_OC_FULL, v_oc_empty_v=V_OC_EMPTY, r_internal_ohm=0.020,
        i_load_a=68.0, v_cutoff_v=v_cutoff, capacity_ah=CAPACITY_AH,
        r_internal_scope="pack", voltage_scope="pack",
    )
    assert r.outputs["outcome"] == "sustainable"
    assert r.outputs["stopping_condition"] == "voltage_cutoff"
    assert r.outputs["soc_at_cutoff"] == pytest.approx(1.0, abs=1e-9)
    assert r.outputs["endurance_min"] == pytest.approx(0.0, abs=1e-9)


def test_build_without_sweep_leaves_l1_unaffected(tmp_path):
    params = {
        "vehicle_type": "dron", "payload_kg": 1.0, "structure_mass_factor": 0.5,
        "safety_factor": 1.2, "motor_count": 4, "battery_capacity_wh": 100.0,
        "motor_power_w": 220.0, "per_motor_max_thrust_n": 9.5,
    }
    control = CalculationEngine().build(params)
    test = CalculationEngine().build(dict(params))  # fresh dict, no sweep key at all

    assert test.battery_endurance_envelope is None
    assert test.battery_endurance_assumption is None
    assert test.autonomy_min == control.autonomy_min
    assert test.hover_energy_autonomy_min == control.hover_energy_autonomy_min


def test_build_with_empty_or_null_sweep_leaves_l1_unaffected():
    params = {
        "vehicle_type": "dron", "payload_kg": 1.0, "structure_mass_factor": 0.5,
        "safety_factor": 1.2, "motor_count": 4, "battery_capacity_wh": 100.0,
        "motor_power_w": 220.0, "per_motor_max_thrust_n": 9.5,
    }
    for empty_value in (None, [], "[]"):
        p = dict(params)
        p["battery_endurance_sweep"] = empty_value
        bundle = CalculationEngine().build(p)
        assert bundle.battery_endurance_envelope is None
        assert bundle.battery_endurance_assumption is None


def test_build_with_two_point_sweep_populates_envelope():
    params = {
        "vehicle_type": "dron", "payload_kg": 1.0, "structure_mass_factor": 0.5,
        "safety_factor": 1.2, "motor_count": 4, "battery_capacity_wh": 100.0,
        "motor_power_w": 220.0, "per_motor_max_thrust_n": 9.5,
        "battery_endurance_sweep": [
            {
                "v_oc_full_v": V_OC_FULL, "v_oc_empty_v": V_OC_EMPTY, "r_internal_ohm": 0.020,
                "i_load_a": 68.0, "v_cutoff_v": 14.0, "capacity_ah": CAPACITY_AH,
                "r_internal_scope": "pack", "voltage_scope": "pack",
            },
            {
                "v_oc_full_v": V_OC_FULL, "v_oc_empty_v": V_OC_EMPTY, "r_internal_ohm": 0.040,
                "i_load_a": 68.0, "v_cutoff_v": 14.0, "capacity_ah": CAPACITY_AH,
                "r_internal_scope": "pack", "voltage_scope": "pack",
            },
        ],
    }
    bundle = CalculationEngine().build(params)
    assert bundle.battery_endurance_envelope is not None
    assert len(bundle.battery_endurance_envelope) == 2
    for row in bundle.battery_endurance_envelope:
        assert row["source_type"] == "assumed"
    assert bundle.battery_endurance_envelope[0]["outcome"] == "sustainable"
    assert bundle.battery_endurance_envelope[1]["outcome"] == "infeasible"

    assumption = json.loads(bundle.battery_endurance_assumption)
    assert "ESTIMATIVE" in assumption["label"]
    assert assumption["source_type"] == "assumed"
    assert assumption["n_points"] == 2

    # L1 still computed independently (this fixture is non-aerial-hover-
    # applicable — freeform motor_power_w path — matching the no-sweep case).
    control = CalculationEngine().build({k: v for k, v in params.items() if k != "battery_endurance_sweep"})
    assert bundle.autonomy_min == control.autonomy_min


def test_sweep_does_not_abort_on_refused_point():
    points = [
        {
            "v_oc_full_v": V_OC_FULL, "v_oc_empty_v": V_OC_EMPTY, "r_internal_ohm": -1.0,
            "i_load_a": 68.0, "v_cutoff_v": 14.0, "capacity_ah": CAPACITY_AH,
            "r_internal_scope": "pack", "voltage_scope": "pack",
        },
        {
            "v_oc_full_v": V_OC_FULL, "v_oc_empty_v": V_OC_EMPTY, "r_internal_ohm": 0.020,
            "i_load_a": 68.0, "v_cutoff_v": 14.0, "capacity_ah": CAPACITY_AH,
            "r_internal_scope": "pack", "voltage_scope": "pack",
        },
    ]
    results = estimate_loaded_endurance_sweep(points)
    assert len(results) == 2
    assert results[0].outputs["outcome"] == "refused"
    assert results[1].outputs["outcome"] == "sustainable"


def test_design_explorer_never_references_battery_endurance():
    import inspect

    from jarvis.core import design_explorer

    source = inspect.getsource(design_explorer)
    assert "battery_endurance" not in source
