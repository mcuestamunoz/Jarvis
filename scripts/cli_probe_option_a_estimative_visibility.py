#!/usr/bin/env python3
"""CLI probe — Option A ESTIMATIVO visibility (no hand-injected sweep).

implementation_contract_option_a_estimative_visibility.md §4.2
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
            "vehicle_type": "dron", "objective": "option a estimative probe",
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


def probe_step1_calculate_without_injected_sweep(tmp_root: Path):
    from jarvis.core.orchestrator import JarvisOrchestrator

    orch = JarvisOrchestrator(workspace_root=tmp_root / "option_a")
    _bind_combo_a(orch, payload_kg=1.718)
    result = orch.handle({"action": "calculate", "parameters": {}})
    assert result["status"] == "ok", result
    calcs = result["calculations"]
    _assert_close(calcs["hover_energy_autonomy_min"], 1.3237, "L1", tol=0.01)
    envelope = calcs["battery_endurance_envelope"]
    assert envelope is not None and len(envelope) == 2, envelope
    outcomes = {row["outcome"] for row in envelope}
    assert "sustainable" in outcomes and "infeasible" in outcomes, outcomes
    print("✓ Step 1 PASS: calculate (no injected sweep) -> L1≈1.32 + 2-point envelope")
    return orch, result


def probe_step1b_calculate_reply_shows_estimativo(result: dict):
    from jarvis.adapters.cli.main import render_response

    rendered = render_response(result)
    assert "ESTIMATIVO" in rendered, rendered
    assert "INVIABLE" in rendered, rendered
    assert "autonomía real" not in rendered.lower(), rendered
    print("✓ Step 1b PASS: calculate reply contains ESTIMATIVO + INVIABLE")


def probe_step2_estado_render(orch):
    from jarvis.adapters.cli.main import render_startup_context

    ctx = orch.build_startup_context()
    rendered = render_startup_context(ctx)
    assert "ESTIMATIVO" in rendered, rendered
    assert "INVIABLE" in rendered, rendered
    assert "autonomía real" not in rendered.lower(), rendered
    assert "hover_energy_autonomy_min≈1.32 min" in rendered, rendered
    print("✓ Step 2 PASS: estado contains ESTIMATIVO + INVIABLE + L1, never 'autonomía real'")
    return rendered


def probe_step3_sweep_not_persisted(orch):
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert "battery_endurance_sweep" not in (ps.current_parameters or {})
    print("✓ Step 3 PASS: current_parameters has no battery_endurance_sweep")


def probe_step4_p27b_probe_still_passes(tmp_root: Path):
    import runpy

    probe = Path(__file__).resolve().parent / "cli_probe_phase27b_battery_endurance.py"
    ns = runpy.run_path(str(probe), run_name="not_main")
    ns["main"]()
    print("✓ Step 4 PASS: cli_probe_phase27b_battery_endurance.py still 4/4")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="jarvis-probe-option-a-") as tmp:
        root = Path(tmp)
        orch, result = probe_step1_calculate_without_injected_sweep(root)
        probe_step1b_calculate_reply_shows_estimativo(result)
        probe_step2_estado_render(orch)
        probe_step3_sweep_not_persisted(orch)
        probe_step4_p27b_probe_still_passes(root)
    print("\n=== SUMMARY: 5/5 OPTION A ESTIMATIVE VISIBILITY PROBES PASS ===")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
