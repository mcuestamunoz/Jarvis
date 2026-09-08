"""Conn B1 (`mounted_on` subject/target parse symmetry).

Covers implementation_contract_connect_remaining_mounted_on_b1.md §4:
  T1  "helices montadas en los motores" -> SET(propellers, motors)
  T2  "sensor montado en el esc" -> SET(sensors, esc) -- never self-mount
  T3  "monta las helices en los motores" -> SET(propellers, motors)
  T4  Non-reg: "propellers montados en motors" still SET
  T5  Non-reg: "sensor montado en la placa" still AMBIGUOUS (2+ plates)
  T6  Non-reg: CLEAR "quita el montaje del esc"
  T7  Orchestrator IDLE: T1 phrase persists propellers.mounted_on == "motors"
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.mounted_on_declare_assist import parse_mounted_on_declare
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _components_propulsion():
    return {
        "motors": ComponentSpec(suggested_key="motors", completeness="high"),
        "propellers": ComponentSpec(suggested_key="propellers", completeness="high"),
        "sensors": ComponentSpec(suggested_key="sensors", completeness="medium"),
        "esc": ComponentSpec(suggested_key="esc", completeness="high"),
    }


def _components_two_plates():
    return {
        "sensors": ComponentSpec(suggested_key="sensors", completeness="medium"),
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_plate": ComponentSpec(
            suggested_key="frame_plate", component_type="structure_part",
            parent_key="frame", completeness="medium",
            properties={"label": PropertyValue(value="Main Plate")},
        ),
        "frame_plate_2": ComponentSpec(
            suggested_key="frame_plate_2", component_type="structure_part",
            parent_key="frame", completeness="medium",
            properties={"label": PropertyValue(value="Top")},
        ),
    }


# ── T1-T3: the two reproduced collision bugs, now fixed ─────────────────────


def test_t1_helices_montadas_en_los_motores_sets_propellers_on_motors():
    result = parse_mounted_on_declare("helices montadas en los motores", _components_propulsion())
    assert result.kind == "SET"
    assert result.component_key == "propellers"
    assert result.target_key == "motors"


def test_t2_sensor_montado_en_el_esc_never_self_mounts():
    result = parse_mounted_on_declare("sensor montado en el esc", _components_propulsion())
    assert result.kind == "SET"
    assert result.component_key == "sensors"
    assert result.target_key == "esc"
    assert result.component_key != result.target_key


def test_t3_monta_las_helices_en_los_motores():
    result = parse_mounted_on_declare("monta las helices en los motores", _components_propulsion())
    assert result.kind == "SET"
    assert result.component_key == "propellers"
    assert result.target_key == "motors"


# ── T4-T6: non-regression ───────────────────────────────────────────────────


def test_t4_non_regression_literal_keys_still_set():
    result = parse_mounted_on_declare("propellers montados en motors", _components_propulsion())
    assert result.kind == "SET"
    assert result.component_key == "propellers"
    assert result.target_key == "motors"


def test_t5_non_regression_sensor_en_placa_still_ambiguous():
    result = parse_mounted_on_declare("sensor montado en la placa", _components_two_plates())
    assert result.kind == "AMBIGUOUS_TARGET"
    assert result.component_key == "sensors"
    assert set(result.candidates) == {("frame_plate", "Main Plate"), ("frame_plate_2", "Top")}


def test_t6_non_regression_clear_esc_still_works():
    result = parse_mounted_on_declare("quita el montaje del esc", _components_propulsion())
    assert result.kind == "CLEAR"
    assert result.component_key == "esc"
    assert result.target_key is None


def test_t6b_non_regression_esc_montado_en_frame_plate_subject_stays_esc():
    """The pre-existing exact-key regression (esc must never resolve as its
    own target) must still hold now that subject resolution is segment-scoped."""
    components = {
        "esc": ComponentSpec(suggested_key="esc", completeness="high"),
        "frame_plate": ComponentSpec(
            suggested_key="frame_plate", component_type="structure_part",
            parent_key="frame", completeness="medium",
        ),
    }
    result = parse_mounted_on_declare("esc montado en frame_plate", components)
    assert result.kind == "SET"
    assert result.component_key == "esc"
    assert result.target_key == "frame_plate"


def test_t6c_non_regression_arm_target_unaffected_by_alias_fallback():
    result = parse_mounted_on_declare("monta las helices en frame_arm", {
        "propellers": ComponentSpec(suggested_key="propellers", completeness="high"),
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_arm": ComponentSpec(
            suggested_key="frame_arm", parent_key="frame", completeness="medium",
        ),
    })
    assert result.kind == "SET"
    assert result.component_key == "propellers"
    assert result.target_key == "frame_arm"


def test_target_alias_never_invents_a_key_absent_from_components():
    """Component-noun alias resolution (§3.2) must never resolve to a key
    that isn't actually declared — 'los motores' with no motors component
    stays unresolved (AMBIGUOUS_TARGET, empty candidates), not a fabricated
    target."""
    result = parse_mounted_on_declare("helices montadas en los motores", {
        "propellers": ComponentSpec(suggested_key="propellers", completeness="high"),
    })
    assert result.kind == "AMBIGUOUS_TARGET"
    assert result.component_key == "propellers"
    assert result.candidates == ()


# ── T7: orchestrator IDLE persistence ───────────────────────────────────────


def _project_with_components(tmp_path: Path, components: dict) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "conn b1", "payload_kg": 1.0,
            "restrictions": "ninguna", "detail_level": "conceptual",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    updated_dp = ps.design_properties.model_copy(
        update={"components": {**ps.design_properties.components, **components}}
    )
    ps = ps.model_copy(update={"design_properties": updated_dp})
    orch.workspace_manager.save_state(ps)
    return orch


def test_t7_idle_helices_en_motores_persists_via_orchestrator(tmp_path: Path):
    orch = _project_with_components(tmp_path, _components_propulsion())
    result = orch.handle_user_text("helices montadas en los motores", _RefuseLLM())
    assert result["status"] == "ok"
    assert "Declarado" in result["message"]
    assert "propellers montado en motors" in result["message"]

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.design_properties.components["propellers"].mounted_on == "motors"


def test_t7b_idle_sensor_en_esc_persists_via_orchestrator(tmp_path: Path):
    orch = _project_with_components(tmp_path, _components_propulsion())
    result = orch.handle_user_text("sensor montado en el esc", _RefuseLLM())
    assert result["status"] == "ok"

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.design_properties.components["sensors"].mounted_on == "esc"
