"""Continuity Declared Box-Local Pose B1 (CLI / IDLE).

Covers implementation_contract_continuity_declared_box_pose_b1.md §4:
  T1  Parse SET single axis
  T2  Parse SET multi-axis
  T3  Parse CLEAR
  T4  Pose NONE: mount phrase
  T5  Pose NONE: "fija" phrase (mount owns it)
  T6  Pose NONE: bare "declarar X" / status phrase
  T7  Pose NONE: mount's own clear phrase
  T8  Parse SET with a shapeless origin -> orchestrator surfaces writer error
  T9  Orchestrator IDLE happy path persists + honest message + Board fields
  T10 Orchestrator CLEAR after T9
  T11 Orchestrator: "declarar el esc" stays acquisition-shaped (no pose persist)
  T12 Non-regression: "cambiar frame" still works
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.declared_box_pose_declare_assist import parse_declared_box_pose_declare
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.workspace.spatial_board import POSE_AXES_HONESTY_LABEL, project_spatial_nodes


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _fc_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="flight_controller", completeness="high",
        properties={
            "length_mm": PropertyValue(value=44.0, unit="mm", source="declared"),
            "width_mm": PropertyValue(value=84.0, unit="mm", source="declared"),
            "height_mm": PropertyValue(value=12.0, unit="mm", source="declared"),
        },
    )


def _components_esc_fc_plate_motor():
    return {
        "esc": ComponentSpec(suggested_key="esc", completeness="high"),
        "flight_controller": _fc_spec(),
        "frame_plate": ComponentSpec(
            suggested_key="frame_plate", component_type="structure_part",
            parent_key="frame", completeness="medium",
        ),
        "motors": ComponentSpec(
            suggested_key="motors", completeness="high",
            properties={"diameter_mm": PropertyValue(value=27.9, unit="mm", source="declared")},
        ),
        "battery": ComponentSpec(suggested_key="battery", completeness="high"),
    }


# ── T1-T8: pure parse ────────────────────────────────────────────────────


def test_t1_parse_set_single_axis():
    result = parse_declared_box_pose_declare(
        "declara el esc a 5 mm en x respecto al fc", _components_esc_fc_plate_motor()
    )
    assert result.kind == "SET"
    assert result.component_key == "esc"
    assert result.origin_key == "flight_controller"
    assert result.x_mm == pytest.approx(5.0)
    assert result.y_mm is None
    assert result.z_mm is None


def test_t2_parse_set_multi_axis():
    result = parse_declared_box_pose_declare(
        "declara el esc a 5 mm en x y -2 mm en z respecto al fc",
        _components_esc_fc_plate_motor(),
    )
    assert result.kind == "SET"
    assert result.x_mm == pytest.approx(5.0)
    assert result.y_mm is None
    assert result.z_mm == pytest.approx(-2.0)


def test_t3_parse_clear():
    result = parse_declared_box_pose_declare(
        "quita la pose del esc", _components_esc_fc_plate_motor()
    )
    assert result.kind == "CLEAR"
    assert result.component_key == "esc"


@pytest.mark.parametrize("phrase", [
    "esc montado en frame_plate",       # T4
    "fija el esc en la placa",           # T5
    "declarar el esc",                   # T6
    "declarar bateria",                  # T6
    "por que no puedo montar el dron",   # T6
    "quita el montaje del esc",          # T7
])
def test_t4_t7_pose_none_for_non_pose_phrases(phrase):
    result = parse_declared_box_pose_declare(phrase, _components_esc_fc_plate_motor())
    assert result.kind == "NONE"


def test_t8_parse_set_with_shapeless_origin():
    """Parser does not pre-check box-ness — it resolves the origin noun and
    lets the writer be the honesty gate (orchestrator test below confirms
    the ValueError surfaces correctly)."""
    result = parse_declared_box_pose_declare(
        "declara los motores a 3 mm en x respecto a frame_plate",
        _components_esc_fc_plate_motor(),
    )
    assert result.kind == "SET"
    assert result.component_key == "motors"
    assert result.origin_key == "frame_plate"


def test_parse_incomplete_when_gate_fires_without_axis():
    result = parse_declared_box_pose_declare(
        "declara el esc a 5 mm respecto al fc", _components_esc_fc_plate_motor()
    )
    assert result.kind == "INCOMPLETE"


def test_parse_ambiguous_origin_when_target_not_found():
    result = parse_declared_box_pose_declare(
        "declara el esc a 5 mm en x respecto a algo_no_declarado",
        _components_esc_fc_plate_motor(),
    )
    assert result.kind == "AMBIGUOUS_ORIGIN"
    assert result.candidates == ()


def test_no_directional_synonyms_accepted_as_axes():
    """'adelante' must never resolve as an axis token — the axis-token
    alternation is closed to x/y/z/largo/ancho/alto only, so a phrase using
    a directional word in that exact grammatical slot finds zero axes."""
    result = parse_declared_box_pose_declare(
        "declara el esc a 5 mm en adelante respecto al fc",
        _components_esc_fc_plate_motor(),
    )
    assert result.kind == "INCOMPLETE"


# ── T9-T12: orchestrator IDLE ────────────────────────────────────────────


def _orch_with_components(tmp_path: Path, components: dict) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "declared box pose b1",
            "payload_kg": 1.0, "restrictions": "ninguna", "detail_level": "conceptual",
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


def test_t9_idle_happy_path_persists_and_confirms(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _components_esc_fc_plate_motor())
    result = orch.handle_user_text("declara el esc a 5 mm en x respecto al fc", _RefuseLLM())
    assert result["status"] == "ok"
    assert "Declarado" in result["message"]
    assert POSE_AXES_HONESTY_LABEL in result["message"]
    # "no morro"/"no gravedad" are the one allowed occurrence — they're part
    # of the locked, verbatim honesty label itself (already shipped by the
    # writer IC), not new invented copy — so check for the POSITIVE claim
    # forms only, never the label's own explicit negations.
    lower = result["message"].lower()
    for forbidden in ("ensamblado", "cabe", "verificado", "posición real", "adelante"):
        assert forbidden not in lower
    assert "no morro" in lower and "no gravedad" in lower

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    esc = ps.design_properties.components["esc"]
    assert esc.declared_box_pose.origin_key == "flight_controller"
    assert esc.declared_box_pose.x_mm == pytest.approx(5.0)

    nodes = project_spatial_nodes(ps)
    esc_node = next(n for n in nodes if n["id"] == "esc")
    assert {"label": "origen pose", "value": "flight_controller"} in esc_node["fields"]
    assert {"label": "Δx mm", "value": "5"} in esc_node["fields"]


def test_t9b_idle_shapeless_origin_surfaces_writer_error(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _components_esc_fc_plate_motor())
    result = orch.handle_user_text(
        "declara los motores a 3 mm en x respecto a frame_plate", _RefuseLLM()
    )
    assert result["status"] == "error"
    assert "caja" in result["message"].lower()

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.design_properties.components["motors"].declared_box_pose is None


def test_t10_idle_clear_after_set(tmp_path: Path):
    orch = _orch_with_components(tmp_path, _components_esc_fc_plate_motor())
    orch.handle_user_text("declara el esc a 5 mm en x respecto al fc", _RefuseLLM())
    result = orch.handle_user_text("quita la pose del esc", _RefuseLLM())
    assert result["status"] == "ok"
    assert "eliminada" in result["message"]

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.design_properties.components["esc"].declared_box_pose is None


def test_t11_declarar_el_esc_stays_acquisition_shaped(tmp_path: Path):
    """The pose bridge itself must not steal this phrase — it correctly
    returns None (proven directly, at the same layer InfiniteCanvas's own
    IDLE chain calls it) so downstream routing (FN-005/FN-014/LLM) is
    reached exactly as it would be without this IC's dispatch existing.
    Not routed through the full LLM-backed handle_user_text pipeline here —
    what happens after "None" is pre-existing orchestrator behavior, out of
    this IC's scope; only "does this dispatch steal the phrase" is asserted.
    """
    orch = _orch_with_components(tmp_path, _components_esc_fc_plate_motor())
    assert orch._try_handle_declared_box_pose("declarar el esc") is None
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.design_properties.components["esc"].declared_box_pose is None


def test_t12_non_regression_idle_catalog_rebind_still_works(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "non regression",
            "payload_kg": 1.0, "restrictions": "ninguna", "detail_level": "conceptual",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    result = orch.handle_user_text("cambiar frame", _RefuseLLM())
    assert result["status"] in {"interactive", "ok"}
