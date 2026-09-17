"""Catalog hygiene + SuggestionEngine mission gate B1
(`B1-catalog-hygiene-mission-suggestions`).

Covers implementation_contract_catalog_hygiene_mission_suggestions_b1.md §2:

Part A — bind omit-key hygiene:
  T1  bind_esc_from_catalog(new_sku_without_H, base=old_with_H) -> no height_mm
  T2  Same bind preserves mounted_on / pose fields from base
  T3  FC bind omit-key: base had H, new FC row omits H -> no leaked height_mm

Part B — IDLE FC/GPS rebind + refresh:
  T4  resolve_idle_catalog_rebind("cambiar controladora") -> flight_controller
  T5  resolve_idle_catalog_rebind("cambiar gps") -> sensors
  T6  Orchestrator IDLE: those phrases offer identity catalog (numbered options)
  T7  "actualiza el fc" / "actualiza el gps" resolve refresh keys (success path)

Part C — SuggestionEngine / action_map mission gate:
  T8  Mission active + high margin: simulate suggestions list has no increase_payload
  T9  Mission active: ReasoningLayer with injected increase_payload suggestion does
      not enrich that label (waterfall/alternate instead, or suppress)
  T10 Neutral mission + high margin: increase_payload still present (regression)
  T11 Continuity #1 tests still green unmodified (checked via full suite, not here)
  T12 Full pytest green (checked at the repo level)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.catalog_bind import (
    bind_esc_from_catalog,
    bind_flight_controller_from_catalog,
    bind_sensor_from_catalog,
)
from jarvis.core.catalog_rebind_assist import resolve_idle_catalog_rebind
from jarvis.core.catalog_refresh_assist import resolve_catalog_refresh_component
from jarvis.core.component_writers import refresh_component_from_catalog
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.reasoning_layer import ReasoningLayer, filter_mission_gated_suggestions
from jarvis.schemas.action_schema import DeclaredBoxPose


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


# ── Part A: bind omit-key hygiene ────────────────────────────────────────


def test_t1_esc_rebind_to_sku_without_height_drops_stale_height():
    speedybee = bind_esc_from_catalog("speedybee_bls_60a_30x30_4in1")
    assert speedybee.properties["height_mm"].value == pytest.approx(8.0)

    skystars = bind_esc_from_catalog("skystars_ko50a_ii_bls", base=speedybee)
    assert "height_mm" not in skystars.properties
    # length/width DO exist on the skystars row and should be freshly projected
    assert skystars.properties["length_mm"].value is not None


def test_t2_esc_rebind_preserves_mounted_on_and_pose():
    speedybee = bind_esc_from_catalog("speedybee_bls_60a_30x30_4in1")
    posed = speedybee.model_copy(update={
        "mounted_on": "frame_plate",
        "declared_box_pose": DeclaredBoxPose(origin_key="frame_plate", x_mm=1.0, y_mm=2.0, z_mm=3.0),
    })
    skystars = bind_esc_from_catalog("skystars_ko50a_ii_bls", base=posed)
    assert skystars.mounted_on == "frame_plate"
    assert skystars.declared_box_pose == DeclaredBoxPose(origin_key="frame_plate", x_mm=1.0, y_mm=2.0, z_mm=3.0)


def test_esc_same_sku_refresh_preserves_estimated_temporary_height(tmp_path: Path):
    """Regression guard (caught during implementation): a refresh onto the
    SAME sku must NEVER drop a user's own estimated_temporary value for a
    key the catalog still doesn't state — only a genuine SKU CHANGE drops
    stale catalog-owned keys."""
    from jarvis.core.component_writers import set_estimated_temporary_esc_height

    orch = _orch_with_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    skystars = bind_esc_from_catalog("skystars_ko50a_ii_bls")
    dp = ps.design_properties.model_copy(update={"components": {**ps.design_properties.components, "esc": skystars}})
    ps = ps.model_copy(update={"design_properties": dp})

    updated = set_estimated_temporary_esc_height(ps, "esc", 9.5)
    refreshed = bind_esc_from_catalog("skystars_ko50a_ii_bls", base=updated.design_properties.components["esc"])
    height = refreshed.properties["height_mm"]
    assert height.value == pytest.approx(9.5)
    assert height.source == "estimated_temporary"


def test_t3_flight_controller_rebind_to_sku_without_height_drops_stale_height():
    speedybee_fc = bind_flight_controller_from_catalog("speedybee_f405_v4")
    assert speedybee_fc.properties["height_mm"].value == pytest.approx(7.8)

    skystars_fc = bind_flight_controller_from_catalog("skystars_f4_v4", base=speedybee_fc)
    assert "height_mm" not in skystars_fc.properties


def test_sensor_bind_omit_key_mechanism_shares_esc_fc_helper():
    """Sensors family (IC lock A3 — required alongside FC): the live
    library only seeds one sensor row (`holybro_m10`) so a real cross-SKU
    mismatch can't be exercised against live data — instead confirm a
    same-sku refresh (no drop) round-trips correctly, proving the shared
    helper's sku_changed=False branch runs for this family too (the
    drop-on-change branch itself is already proven live by T1/T3)."""
    holybro = bind_sensor_from_catalog("holybro_m10")
    refreshed = bind_sensor_from_catalog("holybro_m10", base=holybro)
    assert refreshed.properties["height_mm"].value == pytest.approx(14.4)


# ── Part B: IDLE FC/GPS rebind + refresh ─────────────────────────────────


def test_t4_cambiar_controladora_resolves_flight_controller():
    assert resolve_idle_catalog_rebind("cambiar controladora") == "flight_controller"
    assert resolve_idle_catalog_rebind("cambiar fc") == "flight_controller"


def test_t5_cambiar_gps_resolves_sensors():
    assert resolve_idle_catalog_rebind("cambiar gps") == "sensors"
    assert resolve_idle_catalog_rebind("cambiar sensores") == "sensors"


def test_t4_t5_regression_existing_rebind_keys_unaffected():
    assert resolve_idle_catalog_rebind("cambiar esc") == "esc"
    assert resolve_idle_catalog_rebind("cambiar frame") == "frame"
    assert resolve_idle_catalog_rebind("ayudame a elegir") is None


def _orch_with_project(tmp_path: Path, objective: str = "10-min-autonomía") -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": objective, "payload_kg": 1.0,
            "restrictions": "no", "detail_level": "detallado",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    return orch


def _orch_with_bound_fc_and_sensor(tmp_path: Path) -> JarvisOrchestrator:
    """The IDLE rebind gate is swap/upgrade-only (never steals first-time
    acquisition when the component is absent or a low-completeness stub —
    see orchestrator.py's own comment at the rebind dispatch) — so the
    fixture must already have a real, non-stub flight_controller/sensors
    entry, mirroring test_idle_catalog_rebind_b3.py's `_closed_bound`
    pattern for the other families."""
    from jarvis.core.component_writers import set_control_component

    orch = _orch_with_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    ps = set_control_component(ps, bind_flight_controller_from_catalog("speedybee_f405_v4"))
    ps = set_control_component(ps, bind_sensor_from_catalog("holybro_m10"))
    orch.workspace_manager.save_state(ps)
    return orch


def test_t6_cambiar_controladora_offers_numbered_fc_catalog(tmp_path: Path):
    orch = _orch_with_bound_fc_and_sensor(tmp_path)
    result = orch.handle_user_text("cambiar controladora", _RefuseLLM())
    assert result["status"] == "interactive"
    assert "1." in result["message"] and "2." in result["message"]
    assert "Pixhawk" in result["message"] or "controladora" in result["message"].lower()


def test_t6_cambiar_gps_offers_numbered_sensor_catalog(tmp_path: Path):
    orch = _orch_with_bound_fc_and_sensor(tmp_path)
    result = orch.handle_user_text("cambiar gps", _RefuseLLM())
    assert result["status"] == "interactive"
    assert "1." in result["message"]
    assert "GPS" in result["message"] or "sensor" in result["message"].lower()


def test_t7_actualiza_el_fc_resolves_refresh_key():
    assert resolve_catalog_refresh_component("actualiza el fc") == "flight_controller"
    assert resolve_catalog_refresh_component("actualiza la controladora") == "flight_controller"


def test_t7_actualiza_el_gps_resolves_refresh_key():
    assert resolve_catalog_refresh_component("actualiza el gps") == "sensors"
    assert resolve_catalog_refresh_component("actualiza los sensores") == "sensors"


def test_t7_refresh_component_from_catalog_succeeds_for_flight_controller(tmp_path: Path):
    orch = _orch_with_bound_fc_and_sensor(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    refreshed = refresh_component_from_catalog(ps, "flight_controller")
    assert refreshed.design_properties.components["flight_controller"].catalog_ref.sku == "speedybee_f405_v4"


def test_t7_refresh_component_from_catalog_succeeds_for_sensors(tmp_path: Path):
    orch = _orch_with_bound_fc_and_sensor(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    refreshed = refresh_component_from_catalog(ps, "sensors")
    assert refreshed.design_properties.components["sensors"].catalog_ref.sku == "holybro_m10"


# ── Part C: SuggestionEngine / action_map mission gate ───────────────────


def _sim_context(objective, components, *, restrictions="no", margin=3.0):
    return {
        "objective": objective,
        "current_parameters": {"restrictions": restrictions},
        "design_properties": {"components": components, "structure": {}},
        "last_calculation": None, "material": None,
        "last_simulation": {"safety_margin_ratio": margin, "status": "pass"},
        "memory": {}, "last_mutation": None, "mutation_mode": None,
    }


def test_t8_filter_mission_gated_suggestions_suppresses_increase_payload():
    payload = [
        {"type": "increase_payload", "reason": "r", "expected_effect": "e", "priority": 0.9},
        {"type": "improve_efficiency", "reason": "r2", "expected_effect": "e2", "priority": 0.7},
    ]
    filtered = filter_mission_gated_suggestions(payload, "dron de vigilancia", "no", {})
    types = [s["type"] for s in filtered]
    assert "increase_payload" not in types
    assert "improve_efficiency" in types


def test_t8_filter_mission_gated_suggestions_neutral_returns_unchanged():
    payload = [{"type": "increase_payload", "reason": "r", "expected_effect": "e", "priority": 0.9}]
    filtered = filter_mission_gated_suggestions(payload, "prueba", "no", {})
    assert filtered == payload


def test_t9_action_map_loop_skips_injected_increase_payload_when_mission_active():
    context = _sim_context("dron de vigilancia doméstico", {})
    injected = [{"type": "increase_payload", "reason": "margen alto", "priority": 0.9}]
    out = ReasoningLayer().build(context, suggestions=injected)
    labels = [s.label for s in out.suggested_actions]
    assert "Aumentar carga útil" not in labels
    # Nothing else was injected -> the "if not enriched" fallback fires
    # with the mission-aware alternate (IC #1's own waterfall).
    assert out.suggested_actions[0].action_type != "increase_payload"


def test_t9_action_map_loop_suppresses_when_sibling_suggestion_also_present():
    """The other IC-sanctioned outcome (T9: "waterfall/alternate instead,
    OR suppress") — when a sibling suggestion (e.g. improve_efficiency)
    also gets enriched, increase_payload is simply dropped, not replaced."""
    context = _sim_context("dron de vigilancia doméstico", {})
    injected = [
        {"type": "increase_payload", "reason": "margen alto", "priority": 0.9},
        {"type": "improve_efficiency", "reason": "eficiencia", "priority": 0.7},
    ]
    out = ReasoningLayer().build(context, suggestions=injected)
    action_types = [s.action_type for s in out.suggested_actions]
    assert "increase_payload" not in action_types
    assert "improve_efficiency" in action_types


def test_t10_neutral_mission_regression_increase_payload_still_enriched():
    context = _sim_context("prueba", {})
    injected = [{"type": "increase_payload", "reason": "margen alto", "priority": 0.9}]
    out = ReasoningLayer().build(context, suggestions=injected)
    assert out.suggested_actions[0].label == "Aumentar carga útil"
    assert out.suggested_actions[0].action_type == "increase_payload"


def test_t10_simulate_action_raw_list_and_reasoning_both_neutral_regression():
    """End-to-end: a neutral SimulateAction run must be byte-identical to
    pre-Buy behavior — increase_payload survives in both the raw list and
    ReasoningLayer's suggested_actions."""
    import json
    from jarvis.actions.simulate import SimulateAction
    from jarvis.core.calculation_engine import CalculationEngine
    from jarvis.core.state_manager import StateManager
    from jarvis.schemas.state_schema import ProjectState
    from jarvis.simulation.simulator import FlightSimulator
    from jarvis.suggestions.suggestion_engine import SuggestionEngine
    from jarvis.workspace.workspace_manager import WorkspaceManager

    fixture_path = Path("workspace/10-min-autonomía-7e400f0a4983/state.json")
    if not fixture_path.exists():
        pytest.skip("live workspace fixture not present in this environment")
    raw = json.loads(fixture_path.read_text())
    raw["objective"] = "dron de prueba"
    raw["design_properties"]["components"].pop("cameras", None)
    raw["design_properties"]["components"].pop("radio_module", None)
    project_state = ProjectState.model_validate(raw)

    wm = WorkspaceManager()
    sm = StateManager()
    action = SimulateAction(
        calculation_engine=CalculationEngine(), simulator=FlightSimulator(),
        suggestion_engine=SuggestionEngine(), reasoning_layer=ReasoningLayer(),
        state_manager=sm, workspace_manager=wm,
    )
    sm.load_active_project = lambda *a, **k: project_state
    wm.save_state = lambda state: None
    wm.save_simulation = lambda *a, **k: "fake/path"
    wm.append_event = lambda *a, **k: None
    wm.render_views = lambda *a, **k: None
    sm.record_action = lambda state, action, latest_results, increment_iteration: state.model_copy(
        update={"latest_results": latest_results}
    )

    result = action.run({})
    assert result["simulation"]["safety_margin_ratio"] > 1.5
    assert "increase_payload" in [s["type"] for s in result["suggestions"]]
    assert result["reasoning"]["suggested_actions"][0]["label"] == "Aumentar carga útil"


def test_t8_simulate_action_mission_active_suppresses_raw_increase_payload():
    import json
    from jarvis.actions.simulate import SimulateAction
    from jarvis.core.calculation_engine import CalculationEngine
    from jarvis.core.state_manager import StateManager
    from jarvis.schemas.state_schema import ProjectState
    from jarvis.simulation.simulator import FlightSimulator
    from jarvis.suggestions.suggestion_engine import SuggestionEngine
    from jarvis.workspace.workspace_manager import WorkspaceManager

    fixture_path = Path("workspace/dron-de-vigilancia-doméstico-462d6790e5af/state.json")
    if not fixture_path.exists():
        pytest.skip("live workspace fixture not present in this environment")
    raw = json.loads(fixture_path.read_text())
    project_state = ProjectState.model_validate(raw)

    wm = WorkspaceManager()
    sm = StateManager()
    action = SimulateAction(
        calculation_engine=CalculationEngine(), simulator=FlightSimulator(),
        suggestion_engine=SuggestionEngine(), reasoning_layer=ReasoningLayer(),
        state_manager=sm, workspace_manager=wm,
    )
    sm.load_active_project = lambda *a, **k: project_state
    wm.save_state = lambda state: None
    wm.save_simulation = lambda *a, **k: "fake/path"
    wm.append_event = lambda *a, **k: None
    wm.render_views = lambda *a, **k: None
    sm.record_action = lambda state, action, latest_results, increment_iteration: state.model_copy(
        update={"latest_results": latest_results}
    )

    result = action.run({})
    assert result["simulation"]["safety_margin_ratio"] > 1.5
    assert "increase_payload" not in [s["type"] for s in result["suggestions"]]
    assert result["reasoning"]["suggested_actions"][0]["label"] != "Aumentar carga útil"
