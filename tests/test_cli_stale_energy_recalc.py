"""CLI Continuity: recalc after watts-recovery pick.

implementation_contract_cli_stale_energy_recalc.md

Walk (2026-09-02, autonomia-15min): emax no-W -> watts recovery list -> pick
#1 sunnysky_r2305_2500 (~220 W). Before 'calcular', Continuity said "Declarar
battery_capacity_wh, motor_power_w" even though Wh and W were already in the
project (a stale `energy_status: missing_energy_parameters` from the
pre-pick simulation). The honest next step in that state is recalc, not
"declare", not watts-recovery (the SKU now declares W), not "optimizar o
simular".
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.component_writers import set_frame_material
from jarvis.core.orchestrator import JarvisOrchestrator

from tests.test_cli_catalog_assist_watts_recovery import _CREATE, _RefuseLLM, _bind, _fresh


def _bind_compatible_frame(o: JarvisOrchestrator) -> None:
    """Structure A (implementation_contract_structure_a.md §2.2): _bind's
    fixture never declares a frame. gemfan_5045_hbn is a 5in prop, so a
    compatible frame (size_class_inch=5) keeps these energy/watts-recovery
    tests from also tripping the unrelated class-compatibility gap."""
    ps = o.state_manager.load_active_project(o.workspace_manager)
    ps = set_frame_material(ps, 0.1, "fibra de carbono", 5.0)
    o.workspace_manager.save_state(ps)


def test_pick_watts_recovery_candidate_awaits_recalc_not_declare(tmp_path: Path):
    o = _fresh(tmp_path)
    _bind(o, motor_sku="emax_rs2205s_2300")
    _bind_compatible_frame(o)
    o.handle_user_text("calcular", _RefuseLLM())
    o.handle_user_text("simular", _RefuseLLM())

    listed = o.handle_user_text("ayúdame a elegir", _RefuseLLM())
    suggestions = listed.get("motor_suggestions") or []
    assert suggestions, "watts-recovery list must be non-empty for this fixture"
    idx = next(
        (i for i, s in enumerate(suggestions, start=1) if s.get("name") == "sunnysky_r2305_2500"),
        1,
    )
    picked_name = suggestions[idx - 1]["name"]

    pick = o.handle_user_text(str(idx), _RefuseLLM())
    assert pick.get("status") == "ok"
    assert "puedes optimizar o simular" not in (pick.get("message") or "")

    ps = o.state_manager.load_active_project(o.workspace_manager)
    motors = ps.design_properties.components["motors"]
    assert motors.catalog_ref.sku == picked_name
    # motor_power_w and battery Wh are both already in the project; the sim
    # has not been rerun yet, so autonomy_min is still None / energy_status
    # is still stale.
    assert ps.current_parameters.get("motor_power_w") is not None
    assert ps.current_parameters.get("battery_capacity_wh") is not None
    assert (ps.latest_results or {}).get("calculations", {}).get("autonomy_min") is None

    ctx = o.build_startup_context()
    cont = ctx.get("continuity") or {}
    step = cont.get("next_useful_step") or ""

    assert "calcular" in step
    assert "simular" in step
    assert "No declares motor_power_w a mano" in step
    assert "Declarar battery_capacity_wh" not in step
    assert "Diseño validado" not in cont.get("situation", "")


def test_emax_watts_recovery_continuity_unchanged_before_pick(tmp_path: Path):
    """Before any pick, the emax (no-W) Continuity/IDLE watts-recovery path
    must be unaffected by the new recalc rank — it fires strictly earlier in
    the elif chain."""
    o = _fresh(tmp_path)
    _bind(o, motor_sku="emax_rs2205s_2300")
    _bind_compatible_frame(o)
    o.handle_user_text("calcular", _RefuseLLM())
    o.handle_user_text("simular", _RefuseLLM())

    ctx = o.build_startup_context()
    cont = ctx.get("continuity") or {}
    step = cont.get("next_useful_step") or ""
    assert "ayúdame a elegir" in step
    assert "no declara vatios" in step
