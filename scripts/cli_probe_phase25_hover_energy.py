#!/usr/bin/env python3
"""CLI probe — Phase 2.5 Hover Flight Energy Model (P25-H4).

Reference case: implementation_contract_phase25_hover_autonomy.md /
investigation_report_phase25_hover_autonomy.md Gate A — Combo A
(sunnysky_r2205_2500 + gf_5045x3 + lipo_4s_1500mah @ 14.8V), driven through
the real orchestrator (no hand-built ProjectState), with payload_kg=1.718
so total_mass_kg lands on the investigation's own traced example (~2.88 kg,
4 motors -> T_hover_motor~=7.06N).

Checks:
  1. Combo A hover trace matches the investigation report's live numbers
     exactly: T_hover_motor~=7.063N, motor_hover_power_w~=251.6W,
     hover_energy_autonomy_min~=1.32min (up from ~0.56min bench-max,
     pre-Phase-2.5) -- interpolated, bounded, provenance to both bracketing
     rows (742A).
  2. motor_op_power_w (bind-time bench-max bridge, feasibility path) stays
     592W, unchanged -- Phase 2.5 does not touch resolve_operating_point.
  3. Combo B (emax_rs2205s_2300 + gemfan_5045_hbn, single curated row) is
     honestly UNVERIFIABLE for this fixture's hover demand -- no bench
     fallback, autonomy_min is None, not a silently-reused 485.3W figure.
  4. Extrapolation negative -- a target thrust far below the curated
     minimum (1.961N) never gets an extrapolated answer.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


def _assert_close(actual, expected, label, tol=1e-3):
    assert actual is not None, f"{label}: got None, expected {expected}"
    assert abs(float(actual) - float(expected)) <= tol, (
        f"{label}: got {actual}, expected {expected}"
    )


def _bind_combo_a(orch, *, payload_kg: float, motor_count: int = 4):
    from jarvis.core.catalog_bind import bind_battery_from_catalog, bind_motor_from_catalog, bind_propeller_from_catalog
    from jarvis.core.component_writers import set_battery_component, set_motor_component, set_propeller_component
    from jarvis.knowledge.library import default_library

    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "phase 2.5 hover energy probe",
            "payload_kg": payload_kg, "restrictions": "no", "detail_level": "conceptual",
            "motors": motor_count, "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    ps = ps.model_copy(update={
        "current_parameters": {**ps.current_parameters, "motor_count": motor_count},
    })
    ps = set_propeller_component(ps, bind_propeller_from_catalog("gf_5045x3"))
    battery_spec = bind_battery_from_catalog("lipo_4s_1500mah")
    wh = battery_spec.properties["battery_capacity_wh"].value
    ps = set_battery_component(ps, battery_spec, wh)
    m = default_library.get_motor("sunnysky_r2205_2500")
    motor_spec = bind_motor_from_catalog({
        "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
        "kv_rating": m.kv_rating, "weight_g": m.weight_g, "is_generic": m.is_generic,
    })
    ps = set_motor_component(ps, motor_spec, m.max_watts)
    orch.workspace_manager.save_state(ps)
    return orch.state_manager.load_active_project(orch.workspace_manager)


def probe_combo_a_hover_trace(tmp_root: Path) -> None:
    from jarvis.core.calculation_engine import CalculationEngine
    from jarvis.core.orchestrator import JarvisOrchestrator

    orch = JarvisOrchestrator(workspace_root=tmp_root / "combo_a_hover")
    ps = _bind_combo_a(orch, payload_kg=1.718)

    params = dict(ps.current_parameters)
    params.setdefault("vehicle_type", "dron")
    params.setdefault("payload_kg", 1.718)
    params.setdefault("structure_mass_factor", 0.5)
    params.setdefault("safety_factor", 1.2)
    bundle = CalculationEngine().build(params)

    _assert_close(bundle.total_mass_kg, 2.88, "total_mass_kg", tol=0.01)
    _assert_close(bundle.t_hover_motor_n, 7.0632, "T_hover_motor_n", tol=0.001)
    assert bundle.motor_hover_power_w is not None
    _assert_close(bundle.motor_hover_power_w, 251.559, "motor_hover_power_w", tol=0.5)
    assert bundle.hover_energy_autonomy_min is not None
    _assert_close(bundle.hover_energy_autonomy_min, 1.3237, "hover_energy_autonomy_min", tol=0.01)
    assert bundle.autonomy_min == bundle.hover_energy_autonomy_min

    resolution = json.loads(bundle.hover_energy_resolution)
    assert resolution["source_type"] == "interpolated", resolution
    assert resolution["source_points"] == [
        {"thrust_n": 6.864, "power_w": 241.0, "current_a": 16.3},
        {"thrust_n": 7.845, "power_w": 293.0, "current_a": 19.8},
    ], resolution

    # ★9 / §2.5 preserved semantics: bind-time bench-max bridge unchanged.
    _assert_close(ps.current_parameters["motor_op_power_w"], 592.0, "motor_op_power_w unchanged")
    _assert_close(ps.current_parameters["motor_power_w"], 756.0, "motor_power_w unchanged")

    print("✓ Step 1 PASS: Combo A hover trace matches investigation report exactly")
    print(f"  T_hover_motor={bundle.t_hover_motor_n}N (weight_n={bundle.weight_n}, motors=4)")
    print(f"  P_motor_input={bundle.motor_hover_power_w}W/motor (interpolated 700gf-800gf bracket)")
    print(f"  hover_energy_autonomy_min={bundle.hover_energy_autonomy_min}min "
          f"(bench-max regime would have given {(22.2 / (592.0 * 4)) * 60.0:.4f}min)")
    print("✓ Step 2 PASS: motor_op_power_w=592W / motor_power_w=756W unchanged (bind bridge, ★9)")


def probe_combo_b_unverifiable(tmp_root: Path) -> None:
    from jarvis.core.calculation_engine import CalculationEngine
    from jarvis.core.catalog_bind import bind_battery_from_catalog, bind_motor_from_catalog, bind_propeller_from_catalog
    from jarvis.core.component_writers import set_battery_component, set_motor_component, set_propeller_component
    from jarvis.core.orchestrator import JarvisOrchestrator
    from jarvis.knowledge.library import default_library

    orch = JarvisOrchestrator(workspace_root=tmp_root / "combo_b_hover")
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "phase 2.5 combo b unverifiable",
            "payload_kg": 1.0, "restrictions": "no", "detail_level": "conceptual",
            "motors": 4, "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    ps = ps.model_copy(update={
        "current_parameters": {**ps.current_parameters, "motor_count": 4, "battery_cell_count": 4.32},  # ~16V
    })
    ps = set_propeller_component(ps, bind_propeller_from_catalog("gemfan_5045_hbn"))
    m = default_library.get_motor("emax_rs2205s_2300")
    motor_spec = bind_motor_from_catalog({
        "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
        "kv_rating": m.kv_rating, "weight_g": m.weight_g, "is_generic": m.is_generic,
    })
    ps = set_motor_component(ps, motor_spec, m.max_watts)
    orch.workspace_manager.save_state(ps)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    res = json.loads(ps.current_parameters["propulsion_resolution"])
    assert res["resolution_type"] == "exact_operating_point", res  # single row, matches ~16V exactly

    params = dict(ps.current_parameters)
    params.setdefault("vehicle_type", "dron")
    params.setdefault("payload_kg", 1.0)
    params.setdefault("structure_mass_factor", 0.5)
    params.setdefault("safety_factor", 1.2)
    params["battery_capacity_wh"] = 100.0
    bundle = CalculationEngine().build(params)

    assert bundle.t_hover_motor_n is not None
    assert bundle.t_hover_motor_n < 13.4841, (
        f"precondition: this fixture's hover demand ({bundle.t_hover_motor_n}N) "
        "must fall short of the single curated row (13.4841N) to exercise UNVERIFIABLE"
    )
    assert bundle.motor_hover_power_w is None
    assert bundle.hover_energy_autonomy_min is None
    assert bundle.autonomy_min is None, (
        "single-row dataset that doesn't cover this hover demand must not silently "
        "fall back to the bench-max 485.3W bridge"
    )
    resolution = json.loads(bundle.hover_energy_resolution)
    assert resolution["source_type"] == "unverifiable", resolution
    assert resolution["selection_reason"] == "below_min", resolution

    print(f"✓ Step 3 PASS: Combo B (single row, 13.4841N) honestly UNVERIFIABLE at "
          f"T_hover_motor={bundle.t_hover_motor_n}N -- autonomy_min=None, no bench fallback")


def probe_extrapolation_negative(tmp_root: Path) -> None:
    from jarvis.knowledge.library import resolve_operating_point_at_thrust

    r = resolve_operating_point_at_thrust(
        "sunnysky_r2205_2500", propeller_sku="gf_5045x3", voltage_v=14.8,
        target_thrust_n=0.5,  # below the curated minimum (1.961N)
    )
    assert r.source_type == "unverifiable", r
    assert r.selection_reason == "below_min", r
    assert r.power_w is None and r.current_a is None, (
        "extrapolation below the curated minimum must never produce a value (★★5)"
    )
    print("✓ Step 4 PASS: target_thrust_n=0.5N (below curated min 1.961N) -> UNVERIFIABLE, no extrapolation")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="jarvis-probe-phase25-hover-") as tmp:
        root = Path(tmp)
        probe_combo_a_hover_trace(root)
        probe_combo_b_unverifiable(root)
        probe_extrapolation_negative(root)
    print("\n=== SUMMARY: 4/4 PHASE 2.5 HOVER ENERGY PROBES PASS ===")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
