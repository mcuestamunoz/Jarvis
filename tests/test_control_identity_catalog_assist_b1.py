"""Control identity assist — FC/GPS dim-table numbered list (#4b smoke fix).

Covers:
  - free-text "SpeedyBee F405 V4" binds in the control wizard (force-bind)
  - ayúdame a elegir lists sourced FC/GPS envelopes
  - pick applies the same declare path (dims attached)
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.control_identity_catalog_assist import (
    build_flight_controller_identity_suggestions,
    build_sensor_identity_suggestions,
)
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import MISSING_COMPONENT_DEFINITION
from jarvis.core.state_manager import OrchestratorMode
from jarvis.schemas.action_schema import ComponentSpec


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


_CREATE = {
    "vehicle_type": "dron",
    "objective": "dron prueba control identity assist",
    "payload_kg": 0.5,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "structure_mass_factor": 0.6,
    "safety_factor": 1.2,
}


def _fresh(tmp_path: Path) -> JarvisOrchestrator:
    o = JarvisOrchestrator(workspace_root=tmp_path)
    o.handle({"action": "create_project", "parameters": _CREATE})
    return o


def _open_control_wizard(o: JarvisOrchestrator) -> None:
    session = o.state_manager.runtime_state.session
    o.state_manager.set_runtime_session(
        session.model_copy(
            update={
                "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
                "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
                "pending_missing_params": ["flight_controller", "sensors"],
                "pending_param_definitions": ["flight_controller", "sensors"],
                "pending_define_missing": False,
                "flight_controller_suggestions": [],
                "sensor_suggestions": [],
            }
        )
    )
    # Ensure stubs so _wants_catalog_help is true.
    state = o.state_manager.load_active_project(o.workspace_manager)
    comps = dict(state.design_properties.components)
    comps["flight_controller"] = ComponentSpec(completeness="low", source="declared")
    comps["sensors"] = ComponentSpec(completeness="low", source="declared")
    state.design_properties.components = comps
    o.workspace_manager.save_state(state)


def test_build_lists_sourced_fc_and_gps():
    fcs = build_flight_controller_identity_suggestions()
    assert any(s["model_key"] == "speedybee_f405_v4" for s in fcs)
    assert any(s["model_key"] == "pixhawk_4" for s in fcs)
    gps = build_sensor_identity_suggestions()
    assert any(s["model_key"] == "holybro_m10" for s in gps)


def test_free_text_speedybee_binds_in_wizard(tmp_path: Path):
    o = _fresh(tmp_path)
    _open_control_wizard(o)
    result = o.handle_user_text("SpeedyBee F405 V4", _RefuseLLM())
    assert result["status"] == "ok"
    fc = o.state_manager.load_active_project(o.workspace_manager).design_properties.components[
        "flight_controller"
    ]
    assert fc.completeness != "low"
    assert fc.properties["model"].value == "speedybee_f405_v4"
    assert fc.properties["length_mm"].value == 41.6


def test_help_choose_lists_and_pick_speedybee(tmp_path: Path):
    o = _fresh(tmp_path)
    _open_control_wizard(o)
    offer = o.handle_user_text("ayúdame a elegir", _RefuseLLM())
    assert "SpeedyBee F405 V4" in (offer.get("message") or "")
    suggestions = offer.get("flight_controller_suggestions") or []
    idx = next(s["idx"] for s in suggestions if s["model_key"] == "speedybee_f405_v4")
    # Numbered pick
    pick = o.handle_user_text(str(idx), _RefuseLLM())
    assert pick["status"] == "ok"
    fc = o.state_manager.load_active_project(o.workspace_manager).design_properties.components[
        "flight_controller"
    ]
    assert fc.properties["model"].value == "speedybee_f405_v4"
    assert o.state_manager.get_runtime_session().pending_missing_params == ["sensors"]


def test_label_match_after_offer(tmp_path: Path):
    """match_suggestion_by_input keys off suggestion['name'] — must equal declare label."""
    from jarvis.core.control_identity_catalog_assist import (
        build_flight_controller_identity_suggestions,
        match_suggestion_by_input,
    )

    sugs = build_flight_controller_identity_suggestions()
    picked = match_suggestion_by_input("SpeedyBee F405 V4", sugs)
    assert picked is not None
    assert picked["model_key"] == "speedybee_f405_v4"

    o = _fresh(tmp_path)
    _open_control_wizard(o)
    o.handle_user_text("ayúdame a elegir", _RefuseLLM())
    pick = o.handle_user_text("SpeedyBee F405 V4", _RefuseLLM())
    assert pick["status"] == "ok"
    fc = o.state_manager.load_active_project(o.workspace_manager).design_properties.components[
        "flight_controller"
    ]
    assert fc.properties["model"].value == "speedybee_f405_v4"


def test_help_choose_sensors_holybro(tmp_path: Path):
    o = _fresh(tmp_path)
    _open_control_wizard(o)
    # Bind FC first so head key becomes sensors.
    o.handle_user_text("ayúdame a elegir", _RefuseLLM())
    suggestions = o.state_manager.get_runtime_session().flight_controller_suggestions
    idx = next(s["idx"] for s in suggestions if s["model_key"] == "speedybee_f405_v4")
    o.handle_user_text(str(idx), _RefuseLLM())

    offer = o.handle_user_text("ayúdame a elegir", _RefuseLLM())
    assert "Holybro M10" in (offer.get("message") or "")
    sens_sug = offer.get("sensor_suggestions") or []
    sidx = next(s["idx"] for s in sens_sug if s["model_key"] == "holybro_m10")
    pick = o.handle_user_text(str(sidx), _RefuseLLM())
    assert pick["status"] == "ok"
    sensors = o.state_manager.load_active_project(o.workspace_manager).design_properties.components[
        "sensors"
    ]
    assert sensors.properties["gps_model"].value == "holybro_m10"
    assert sensors.properties["length_mm"].value == 50.0
