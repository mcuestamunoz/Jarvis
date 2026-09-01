#!/usr/bin/env python3
"""CLI probe — Minimum catalog universe end-to-end combo chain.

Verifies the curated physical-identify stack without mutating catalog data:

  Combo A: sunnysky_r2205_2500 + gf_5045x3 + lipo_4s_1500mah @ 14.8 V
  Combo B: emax_rs2205s_2300 + gemfan_5045_hbn — voltage honesty (16 V OP vs 14.8 V pack)

Checks: resolve_operating_point, motor_power_w vs motor_op_power_w separation,
electrical_compatibility (battery discharge, ESC-vs-motor), calc chain
(thrust/mass/autonomy), and that 16 V OP rows never silently match a 14.8 V
catalog battery bind.

  Combo A′: Combo A + hobbywing_xrotor_40a_6s — ESC compatible, battery gap persists.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


def _assert_close(actual, expected, label, tol=1e-4):
    assert actual is not None, f"{label}: got None, expected {expected}"
    assert abs(float(actual) - float(expected)) <= tol, (
        f"{label}: got {actual}, expected {expected}"
    )


def _bind_combo(
    orch,
    *,
    motor_sku: str,
    propeller_sku: str,
    battery_sku: str,
    motor_count: int = 4,
    esc_sku: str | None = None,
):
    from jarvis.core.catalog_bind import (
        bind_battery_from_catalog,
        bind_esc_from_catalog,
        bind_motor_from_catalog,
        bind_propeller_from_catalog,
    )
    from jarvis.core.component_writers import (
        set_battery_component,
        set_control_component,
        set_motor_component,
        set_propeller_component,
    )
    from jarvis.knowledge.library import default_library

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    ps = ps.model_copy(update={
        "current_parameters": {**ps.current_parameters, "motor_count": motor_count},
    })

    prop_spec = bind_propeller_from_catalog(propeller_sku)
    ps = set_propeller_component(ps, prop_spec)

    battery_spec = bind_battery_from_catalog(battery_sku)
    wh = battery_spec.properties["battery_capacity_wh"].value
    ps = set_battery_component(ps, battery_spec, wh)

    m = default_library.get_motor(motor_sku)
    motor_spec = bind_motor_from_catalog({
        "name": m.name,
        "max_watts": m.max_watts,
        "thrust_n": m.thrust_n,
        "kv_rating": m.kv_rating,
        "weight_g": m.weight_g,
        "is_generic": m.is_generic,
    })
    ps = set_motor_component(ps, motor_spec, m.max_watts)
    if esc_sku is not None:
        ps = set_control_component(ps, bind_esc_from_catalog(esc_sku))
    orch.workspace_manager.save_state(ps)
    return orch.state_manager.load_active_project(orch.workspace_manager)


def _fresh_orchestrator(tmp_root: Path, name: str):
    from jarvis.core.orchestrator import JarvisOrchestrator

    orch = JarvisOrchestrator(workspace_root=tmp_root / name)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": f"minimum universe combo probe {name}",
            "payload_kg": 1.0,
            "restrictions": "no",
            "detail_level": "conceptual",
            "motors": 4,
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })
    return orch


def probe_combo_a(tmp_root: Path) -> None:
    from jarvis.core.calculation_engine import CalculationEngine, effective_motor_power_w
    from jarvis.core.electrical_compatibility import evaluate_electrical_compatibility
    from jarvis.core.engineering_readiness import build_engineering_readiness
    from jarvis.knowledge.library import default_library, resolve_operating_point

    orch = _fresh_orchestrator(tmp_root, "combo_a")
    ps = _bind_combo(
        orch,
        motor_sku="sunnysky_r2205_2500",
        propeller_sku="gf_5045x3",
        battery_sku="lipo_4s_1500mah",
    )

    # ── Pure resolver (catalog voltage from battery SKU) ──
    r = resolve_operating_point(
        "sunnysky_r2205_2500",
        propeller_sku="gf_5045x3",
        voltage_v=14.8,
    )
    assert r.resolution_type == "exact_operating_point", r
    _assert_close(r.thrust_n, 12.5525, "combo_a resolver thrust_n")
    assert r.source_type == "manufacturer_test"
    _assert_close(r.current_a, 40.0, "combo_a resolver current_a")
    _assert_close(r.power_w, 592.0, "combo_a resolver power_w")

    motor = default_library.get_motor("sunnysky_r2205_2500")
    _assert_close(motor.max_watts, 756.0, "combo_a motor catalog max_watts")
    _assert_close(motor.max_current_a, 45.0, "combo_a motor catalog max_current_a")

    # ── Bind bridge ──
    res = json.loads(ps.current_parameters["propulsion_resolution"])
    assert res["resolution_type"] == "exact_operating_point", res
    assert res["source_type"] == "manufacturer_test"
    assert res["voltage_validated"] is True
    _assert_close(res["resolved_at_voltage_v"], 14.8, "combo_a resolved_at_voltage_v")
    _assert_close(ps.current_parameters["per_motor_max_thrust_n"], 12.5525, "combo_a per_motor_thrust")
    _assert_close(ps.current_parameters["motor_power_w"], 756.0, "combo_a motor_power_w (nominal)")
    _assert_close(ps.current_parameters["motor_op_power_w"], 592.0, "combo_a motor_op_power_w (OP)")
    _assert_close(ps.current_parameters["motor_op_current_a"], 40.0, "combo_a motor_op_current_a")
    assert ps.current_parameters["motor_power_w"] != ps.current_parameters["motor_op_power_w"]

    # ── Electrical compatibility ──
    compat = evaluate_electrical_compatibility(ps)
    _assert_close(compat.i_motor_a, 40.0, "combo_a i_motor_a")
    _assert_close(compat.i_total_a, 160.0, "combo_a i_total_a")
    _assert_close(compat.battery_limit_a, 150.0, "combo_a battery_limit_a")
    assert compat.battery_discharge == "exceeded", compat.battery_discharge
    assert compat.prop_motor == "compatible"

    readiness = build_engineering_readiness(ps)
    gap_ids = {g.gap_id for g in readiness.gaps}
    assert any("GAP-BATTERY-DISCHARGE-EXCEEDED" in gid for gid in gap_ids), gap_ids

    # ── Calc chain ──
    params = dict(ps.current_parameters)
    params.setdefault("vehicle_type", "dron")
    params.setdefault("payload_kg", 1.0)
    params.setdefault("structure_mass_factor", 0.5)
    params.setdefault("safety_factor", 1.2)
    bundle = CalculationEngine().build(params)
    assert bundle.available_total_thrust_n is not None
    _assert_close(bundle.available_total_thrust_n, 4 * 12.5525, "combo_a total thrust")
    assert bundle.total_mass_kg is not None and bundle.total_mass_kg > 0
    eff = effective_motor_power_w(params)
    _assert_close(eff, 592.0, "combo_a effective power for autonomy")
    assert bundle.autonomy_min is not None
    expected_autonomy = (22.2 / (592.0 * 4)) * 60.0
    _assert_close(bundle.autonomy_min, expected_autonomy, "combo_a autonomy_min", tol=0.05)

    print("✓ Combo A PASS: SunnySky + gf_5045x3 + CNHL 4S @14.8V")
    print("  OP exact manufacturer_test · motor_power_w=756 vs motor_op_power_w=592")
    print("  battery discharge exceeded: 160A > 150A · GAP-BATTERY-DISCHARGE-EXCEEDED present")


def probe_combo_a_prime(tmp_root: Path) -> None:
    from jarvis.core.electrical_compatibility import evaluate_electrical_compatibility
    from jarvis.core.engineering_readiness import build_engineering_readiness
    from jarvis.knowledge.library import default_library

    orch = _fresh_orchestrator(tmp_root, "combo_a_prime")
    ps = _bind_combo(
        orch,
        motor_sku="sunnysky_r2205_2500",
        propeller_sku="gf_5045x3",
        battery_sku="lipo_4s_1500mah",
        esc_sku="hobbywing_xrotor_40a_6s",
    )

    esc = ps.design_properties.components.get("esc")
    assert esc is not None
    assert esc.catalog_ref is not None
    assert esc.catalog_ref.family == "esc"
    assert esc.catalog_ref.sku == "hobbywing_xrotor_40a_6s"
    _assert_close(esc.properties["current_a"].value, 40.0, "combo_a_prime esc current_a")

    esc_spec = default_library.get_esc("hobbywing_xrotor_40a_6s")
    assert esc_spec.identity_status == "verified"
    assert esc_spec.manufacturer == "HOBBYWING"
    assert esc_spec.part_number == "30901001"
    assert esc_spec.esc_topology == "individual"
    assert esc_spec.channels == 1
    _assert_close(esc_spec.continuous_current_a, 40.0, "combo_a_prime catalog continuous")
    _assert_close(esc_spec.burst_current_a, 60.0, "combo_a_prime catalog burst")

    compat = evaluate_electrical_compatibility(ps)
    assert compat.esc_presence == "defined", compat.esc_presence
    assert compat.esc_vs_motor == "compatible", compat.esc_vs_motor
    _assert_close(compat.esc_current_a, 40.0, "combo_a_prime esc_current_a")
    _assert_close(compat.i_motor_a, 40.0, "combo_a_prime i_motor_a")
    assert compat.battery_discharge == "exceeded", compat.battery_discharge

    readiness = build_engineering_readiness(ps)
    gap_types = {g.gap_type for g in readiness.gaps}
    assert any("GAP-BATTERY-DISCHARGE-EXCEEDED" in gid for gid in gap_types), gap_types
    assert not any("GAP-ESC-UNDERSIZED" in gid for gid in gap_types), gap_types
    assert not any("GAP-ESC-UNDEFINED" in gid for gid in gap_types), gap_types

    print("✓ Combo A′ PASS: Combo A + HOBBYWING XRotor 40A @ catalog bind")
    print("  esc_vs_motor compatible: 40A ESC ≥ 40A motor OP")
    print("  battery discharge still exceeded: 160A > 150A")


def probe_combo_b(tmp_root: Path) -> None:
    from jarvis.knowledge.library import resolve_operating_point

    # B1 — catalog bind at real pack voltage must NOT match 16 V measured OP
    orch = _fresh_orchestrator(tmp_root, "combo_b_bind")
    ps = _bind_combo(
        orch,
        motor_sku="emax_rs2205s_2300",
        propeller_sku="gemfan_5045_hbn",
        battery_sku="lipo_4s_1500mah",
    )
    res = json.loads(ps.current_parameters["propulsion_resolution"])
    assert res["resolution_type"] != "exact_operating_point", (
        "16 V OP must not exact-match at 14.8 V catalog battery voltage"
    )
    assert res["resolution_type"] == "fallback_operating_point", res
    _assert_close(res["thrust_n"], 10.042, "combo_b bind fallback thrust")
    assert res["source_type"] == "manufacturer_test"
    assert "motor_power_w" not in ps.current_parameters, "EMAX has no nominal max_watts"
    assert "motor_op_power_w" not in ps.current_parameters, "fallback OP-0 has no electrical tuple"
    _assert_close(res["resolved_at_voltage_v"], 14.8, "combo_b bind voltage gate")

    # B2 — pure resolver: 16 V matches measured OP; 14.8 V does not
    r16 = resolve_operating_point(
        "emax_rs2205s_2300", propeller_sku="gemfan_5045_hbn", voltage_v=16.0,
    )
    assert r16.resolution_type == "exact_operating_point", r16
    assert r16.source_type == "measured_test"
    _assert_close(r16.thrust_n, 13.4841, "combo_b 16V OP thrust")
    _assert_close(r16.current_a, 30.3, "combo_b 16V OP current")
    _assert_close(r16.power_w, 485.3, "combo_b 16V OP power")

    r148 = resolve_operating_point(
        "emax_rs2205s_2300", propeller_sku="gemfan_5045_hbn", voltage_v=14.8,
    )
    assert r148.resolution_type != "exact_operating_point", r148
    assert r148.resolution_type == "fallback_operating_point", r148

    # B3 — cell_count hack at ~16 V without changing battery SKU still resolves exact
    orch16 = _fresh_orchestrator(tmp_root, "combo_b_16v_cells")
    ps16 = orch16.state_manager.load_active_project(orch16.workspace_manager)
    from jarvis.core.catalog_bind import bind_motor_from_catalog, bind_propeller_from_catalog
    from jarvis.core.component_writers import set_motor_component, set_propeller_component
    from jarvis.knowledge.library import default_library

    ps16 = set_propeller_component(ps16, bind_propeller_from_catalog("gemfan_5045_hbn"))
    ps16 = ps16.model_copy(update={
        "current_parameters": {**ps16.current_parameters, "battery_cell_count": 4.32},
    })
    m = default_library.get_motor("emax_rs2205s_2300")
    ps16 = set_motor_component(
        ps16,
        bind_motor_from_catalog({
            "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
            "kv_rating": m.kv_rating, "weight_g": m.weight_g, "is_generic": m.is_generic,
        }),
        m.max_watts,
    )
    res16 = json.loads(ps16.current_parameters["propulsion_resolution"])
    assert res16["resolution_type"] == "exact_operating_point", res16
    assert res16["source_type"] == "measured_test"
    _assert_close(ps16.current_parameters["motor_op_power_w"], 485.3, "combo_b 16V bridge power")
    assert "motor_power_w" not in ps16.current_parameters

    print("✓ Combo B PASS: EMAX + gemfan_5045_hbn voltage honesty")
    print("  14.8 V catalog bind → fallback (no silent 16 V exact match)")
    print("  16.0 V resolver / ~16 V cell_count → measured_test exact OP")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="jarvis-probe-min-universe-") as tmp:
        root = Path(tmp)
        probe_combo_a(root)
        probe_combo_a_prime(root)
        probe_combo_b(root)
    print("\n=== SUMMARY: 3/3 COMBO PROBES PASS ===")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
