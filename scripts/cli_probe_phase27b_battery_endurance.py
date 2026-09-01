#!/usr/bin/env python3
"""CLI probe — Phase 2.7-B Parametric / Estimative Battery Endurance Sweep.

implementation_contract_phase27b_parametric_battery_estimate.md §5.2

Deterministic, no LLM. Combo A (sunnysky_r2205_2500 + gf_5045x3 +
lipo_4s_1500mah @ 14.8V, payload_kg=1.718 -> matches Phase 2.5's own
reference case exactly).

Steps:
  1. build() with NO battery_endurance_sweep -> L1 (hover_energy_autonomy_min)
     unchanged, envelope None.
  2. Same params PLUS a caller-supplied 2-point sweep (20 mOhm / 40 mOhm,
     both pack-scope, labeled) -> one sustainable, one infeasible.
  3. Rendered estado contains "ESTIMATIVO" and "INVIABLE", never
     "autonomía real".
  4. No p_battery/P_battery field anywhere on the bundle (Phase 2.6
     regression check, still frozen).
"""
from __future__ import annotations

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
            "vehicle_type": "dron", "objective": "phase 2.7-b endurance probe",
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


_SWEEP = [
    {
        "v_oc_full_v": 16.4, "v_oc_empty_v": 13.2, "r_internal_ohm": 0.020,
        "i_load_a": 68.0, "v_cutoff_v": 14.0, "capacity_ah": 1.5,
        "r_internal_scope": "pack", "voltage_scope": "pack",
        "i_load_label": "4x motor_hover_current_a hypothesis (NOT pack draw, NOT P_battery)",
    },
    {
        "v_oc_full_v": 16.4, "v_oc_empty_v": 13.2, "r_internal_ohm": 0.040,
        "i_load_a": 68.0, "v_cutoff_v": 14.0, "capacity_ah": 1.5,
        "r_internal_scope": "pack", "voltage_scope": "pack",
        "i_load_label": "4x motor_hover_current_a hypothesis (NOT pack draw, NOT P_battery)",
    },
]


def probe_step1_no_sweep_l1_unchanged(tmp_root: Path):
    from jarvis.core.calculation_engine import CalculationEngine

    orch_module = __import__("jarvis.core.orchestrator", fromlist=["JarvisOrchestrator"])
    orch = orch_module.JarvisOrchestrator(workspace_root=tmp_root / "step1")
    ps = _bind_combo_a(orch, payload_kg=1.718)

    params = dict(ps.current_parameters)
    params.setdefault("vehicle_type", "dron")
    params.setdefault("payload_kg", 1.718)
    params.setdefault("structure_mass_factor", 0.5)
    params.setdefault("safety_factor", 1.2)
    bundle = CalculationEngine().build(params)

    _assert_close(bundle.hover_energy_autonomy_min, 1.3237, "hover_energy_autonomy_min (no sweep)", tol=0.01)
    assert bundle.battery_endurance_envelope is None
    assert bundle.battery_endurance_assumption is None
    assert not hasattr(bundle, "p_battery") and not hasattr(bundle, "P_battery")
    print(f"✓ Step 1 PASS: no sweep -> hover_energy_autonomy_min={bundle.hover_energy_autonomy_min}min, envelope None")
    return ps, params


def probe_step2_sweep_one_sustainable_one_infeasible(params: dict):
    from jarvis.core.calculation_engine import CalculationEngine

    params_with_sweep = dict(params)
    params_with_sweep["battery_endurance_sweep"] = _SWEEP
    bundle = CalculationEngine().build(params_with_sweep)

    assert bundle.battery_endurance_envelope is not None
    assert len(bundle.battery_endurance_envelope) == 2
    row_20, row_40 = bundle.battery_endurance_envelope
    assert row_20["outcome"] == "sustainable", row_20
    _assert_close(row_20["endurance_min"], 0.4301, "20 mOhm endurance_min", tol=0.001)
    assert row_40["outcome"] == "infeasible", row_40
    assert row_40["endurance_min"] is None
    assert row_20["source_type"] == "assumed"
    assert row_40["source_type"] == "assumed"

    # L1 unaffected by the sweep being present.
    _assert_close(bundle.hover_energy_autonomy_min, 1.3237, "hover_energy_autonomy_min (with sweep)", tol=0.01)

    print(f"✓ Step 2 PASS: R=20mΩ -> sustainable {row_20['endurance_min']}min; "
          f"R=40mΩ -> infeasible; L1 unchanged at {bundle.hover_energy_autonomy_min}min")
    return bundle


def probe_step3_cli_render(bundle):
    from jarvis.adapters.cli.main import render_startup_context

    ctx = {
        "has_project": True,
        "project_slug": "phase27b-probe",
        "hover_energy": None,
        "battery_endurance": {
            "envelope": bundle.battery_endurance_envelope,
            "assumption": None,
        },
        "readiness": None,
    }
    rendered = render_startup_context(ctx)
    assert "ESTIMATIVO" in rendered, rendered
    assert "INVIABLE" in rendered, rendered
    assert "autonomía real" not in rendered.lower(), rendered
    print("✓ Step 3 PASS: rendered estado contains ESTIMATIVO + INVIABLE, never 'autonomía real'")


def probe_step4_no_p_battery_field(bundle):
    dumped = bundle.model_dump()
    assert not any("p_battery" in k.lower() for k in dumped), dumped.keys()
    print("✓ Step 4 PASS: no p_battery/P_battery field anywhere on the bundle (Phase 2.6 boundary still frozen)")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="jarvis-probe-phase27b-endurance-") as tmp:
        root = Path(tmp)
        _, params = probe_step1_no_sweep_l1_unchanged(root)
        bundle = probe_step2_sweep_one_sustainable_one_infeasible(params)
        probe_step3_cli_render(bundle)
        probe_step4_no_p_battery_field(bundle)
    print("\n=== SUMMARY: 4/4 PHASE 2.7-B BATTERY ENDURANCE PROBES PASS ===")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
