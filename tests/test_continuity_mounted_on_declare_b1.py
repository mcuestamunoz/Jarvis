"""Continuity declare `mounted_on` B1 (CLI / IDLE).

Covers implementation_contract_continuity_mounted_on_declare_b1.md §4:
  T1  Parse SET: FC + "placa" with a single plate
  T2  Parse SET: motors -> frame_arm ("brazos")
  T3  Parse CLEAR: "quita el montaje del FC"
  T4  AMBIGUOUS: bare "placa" with 2+ plates -> no write
  T5  Unique label match: "placa principal" -> correct key
  T6  NONE: unrelated status phrase without component+target
  T7  Orchestrator IDLE: happy path persists mounted_on + honest message
  T8  Orchestrator: missing subject component -> honest error, no crash
  T9  Non-regression: idle catalog rebind ("cambiar frame") still works
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.mounted_on_declare_assist import parse_mounted_on_declare
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.workspace.spatial_board import project_spatial_nodes


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _components_one_plate():
    return {
        "flight_controller": ComponentSpec(suggested_key="flight_controller", completeness="high"),
        "esc": ComponentSpec(suggested_key="esc", completeness="high"),
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_plate": ComponentSpec(
            suggested_key="frame_plate", component_type="structure_part",
            parent_key="frame", completeness="medium",
        ),
    }


def _components_two_plates():
    return {
        "esc": ComponentSpec(suggested_key="esc", completeness="high"),
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_plate": ComponentSpec(
            suggested_key="frame_plate", component_type="structure_part",
            parent_key="frame", completeness="medium",
            properties={"label": PropertyValue(value="Principal")},
        ),
        "frame_plate_2": ComponentSpec(
            suggested_key="frame_plate_2", component_type="structure_part",
            parent_key="frame", completeness="medium",
            properties={"label": PropertyValue(value="Top")},
        ),
    }


def _components_with_arm():
    return {
        "motors": ComponentSpec(suggested_key="motors", completeness="high"),
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_arm": ComponentSpec(
            suggested_key="frame_arm", component_type="structure_part",
            parent_key="frame", completeness="medium",
        ),
    }


# ── T1-T6: pure parse ────────────────────────────────────────────────────


def test_t1_set_fc_bare_placa_single_plate():
    result = parse_mounted_on_declare("monta el fc en la placa", _components_one_plate())
    assert result.kind == "SET"
    assert result.component_key == "flight_controller"
    assert result.target_key == "frame_plate"


def test_t2_set_motors_brazos_to_frame_arm():
    result = parse_mounted_on_declare("motores montados en los brazos", _components_with_arm())
    assert result.kind == "SET"
    assert result.component_key == "motors"
    assert result.target_key == "frame_arm"


def test_t3_clear_fc():
    result = parse_mounted_on_declare("quita el montaje del fc", _components_one_plate())
    assert result.kind == "CLEAR"
    assert result.component_key == "flight_controller"
    assert result.target_key is None


def test_t4_ambiguous_bare_placa_two_plates_no_write():
    result = parse_mounted_on_declare("monta el esc en la placa", _components_two_plates())
    assert result.kind == "AMBIGUOUS_TARGET"
    assert result.component_key == "esc"
    assert set(result.candidates) == {("frame_plate", "Principal"), ("frame_plate_2", "Top")}


def test_t5_unique_label_match_placa_principal():
    result = parse_mounted_on_declare("monta el esc en la placa principal", _components_two_plates())
    assert result.kind == "SET"
    assert result.component_key == "esc"
    assert result.target_key == "frame_plate"


@pytest.mark.parametrize("phrase", [
    "por que no puedo montar",
    "no se como montar esto todavia",
    "cual es el estado del proyecto",
])
def test_t6_none_unrelated_status_phrases(phrase):
    result = parse_mounted_on_declare(phrase, _components_one_plate())
    assert result.kind == "NONE"


def test_parse_clear_without_subject_is_none():
    result = parse_mounted_on_declare("quita el montaje", _components_one_plate())
    assert result.kind == "NONE"


def test_parse_set_without_recognized_subject_is_none():
    result = parse_mounted_on_declare("monta el dron en la placa", _components_one_plate())
    assert result.kind == "NONE"


def test_exact_key_target_esc_montado_en_frame_plate():
    """Subject 'esc' must never resolve as its own target — target
    resolution only looks after the first 'en'."""
    result = parse_mounted_on_declare("esc montado en frame_plate", _components_one_plate())
    assert result.kind == "SET"
    assert result.component_key == "esc"
    assert result.target_key == "frame_plate"


# ── T7-T9: orchestrator IDLE dispatch ───────────────────────────────────────


def _project_with_components(tmp_path: Path, components: dict) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "mounted_on declare b1",
            "payload_kg": 1.0, "restrictions": "ninguna", "detail_level": "conceptual",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    updated_components = {**ps.design_properties.components, **components}
    updated_dp = ps.design_properties.model_copy(update={"components": updated_components})
    ps = ps.model_copy(update={"design_properties": updated_dp})
    orch.workspace_manager.save_state(ps)
    return orch


def test_t7_idle_happy_path_persists_and_confirms(tmp_path: Path):
    orch = _project_with_components(tmp_path, _components_one_plate())
    result = orch.handle_user_text("monta el fc en la placa", _RefuseLLM())
    assert result["status"] == "ok"
    assert "Declarado" in result["message"]
    assert "montado en" in result["message"]
    assert "ensamblado" not in result["message"].lower()
    assert "cabe" not in result["message"].lower()
    assert "verificado" not in result["message"].lower()

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.design_properties.components["flight_controller"].mounted_on == "frame_plate"

    # §3.6 smoke: the Board projector (unchanged since the prior IC) already
    # shows the declared relation with zero new code — chat -> Board is coherent.
    nodes = project_spatial_nodes(ps)
    fc_node = next(n for n in nodes if n["id"] == "flight_controller")
    assert {"label": "montado en", "value": "frame_plate"} in fc_node["fields"]


def test_t7b_idle_ambiguous_path_no_write(tmp_path: Path):
    orch = _project_with_components(tmp_path, _components_two_plates())
    result = orch.handle_user_text("monta el esc en la placa", _RefuseLLM())
    assert result["status"] == "interactive"
    assert "frame_plate" in result["message"]

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.design_properties.components["esc"].mounted_on is None


def test_t7c_idle_clear_persists(tmp_path: Path):
    orch = _project_with_components(tmp_path, _components_one_plate())
    orch.handle_user_text("monta el fc en la placa", _RefuseLLM())
    result = orch.handle_user_text("quita el montaje del fc", _RefuseLLM())
    assert result["status"] == "ok"
    assert "eliminado" in result["message"]

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.design_properties.components["flight_controller"].mounted_on is None


def test_t8_missing_subject_component_honest_error(tmp_path: Path):
    """battery is not declared at all -> honest error, no crash, no write."""
    orch = _project_with_components(tmp_path, _components_one_plate())
    result = orch.handle_user_text("monta la bateria en la placa", _RefuseLLM())
    assert result["status"] == "error"
    assert "no declarado" in result["message"].lower() or "aun no declarado" in result["message"].lower()


def test_t9_non_regression_idle_catalog_rebind_still_works(tmp_path: Path):
    """'cambiar frame' must still open the frame catalog offer — the new
    mount-declare dispatch must never intercept an unrelated IDLE phrase."""
    orch = _project_with_components(tmp_path, {})
    result = orch.handle_user_text("cambiar frame", _RefuseLLM())
    assert result["status"] in {"interactive", "ok"}
    assert "frame" in (result.get("message") or "").lower() or result.get("action") in {
        "component_description_prompt", "define_missing_params",
    }
