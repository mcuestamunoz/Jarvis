"""Catalog camera `power_w` from cite B1 (`B1-catalog-camera-power-w`).

Covers implementation_contract_catalog_camera_power_w_b1.md §2:

  T1  get_camera("runcam_phoenix_2").power_w == 1.0
  T2  Fresh bind_camera_from_catalog -> properties.power_w == 1.0 + catalog_ref
  T3  Bind path (orchestrator) -> mission_accessory_power_w includes 1.0
      (alone or + radio if set)
  T4  Free-text / medium RunCam -> no power_w
  T5  base with manual power_w=2.0 -> rebind/refresh preserves 2.0
  T6  Continuity: bound catalog camera with power -> no camera power CTA
  T7  Radio-only missing power still CTA when camera power present
  T8  Full suite; 0.4.1
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from jarvis.core.camera_catalog_assist import build_camera_catalog_suggestions
from jarvis.core.catalog_bind import bind_camera_from_catalog
from jarvis.core.component_inference import infer_component_for_key
from jarvis.core.component_writers import (
    refresh_component_from_catalog,
    set_control_component,
)
from jarvis.core.orchestrator import MISSING_COMPONENT_DEFINITION, JarvisOrchestrator
from jarvis.core.reasoning_layer import ReasoningLayer
from jarvis.core.state_manager import OrchestratorMode
from jarvis.domains.aerial import aerial_registry
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import CatalogRef, DeclaredBoxPose, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SKU = "runcam_phoenix_2"


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _state(**components) -> ProjectState:
    return ProjectState(
        project_id="p", project_slug="p", objective="vigilancia",
        workspace_path="w", design_properties=DesignProperties(components=components),
    )


# ── T1 ────────────────────────────────────────────────────────────────────


def test_t1_seed_row_carries_locked_power_w():
    spec = default_library.get_camera(_SKU)
    assert spec.power_w == pytest.approx(1.0)


# ── T2 ────────────────────────────────────────────────────────────────────


def test_t2_fresh_bind_projects_power_w_and_catalog_ref():
    bound = bind_camera_from_catalog(_SKU)
    assert bound.properties["power_w"].value == pytest.approx(1.0)
    assert bound.properties["power_w"].unit == "W"
    assert bound.catalog_ref == CatalogRef(family="cameras", sku=_SKU)


# ── T3 ────────────────────────────────────────────────────────────────────


def _idle_orchestrator(tmp_path: Path) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "camera power w b1",
            "payload_kg": 0.3,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "structure_mass_factor": 0.3,
            "safety_factor": 1.1,
            "motors": 4,
            "per_motor_max_thrust_n": 5.0,
        },
    })
    return orch


def test_t3_orchestrator_pick_mirrors_mission_accessory_power_w(tmp_path: Path):
    orch = _idle_orchestrator(tmp_path)
    session = orch.state_manager.get_runtime_session()
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "pending_missing_params": ["cameras"],
        "pending_define_missing": False,
        "camera_suggestions": [],
    })
    orch.state_manager.set_runtime_session(updated)

    offer = orch.handle_user_text("ayúdame a elegir cámara", _RefuseLLM())
    idx = next(s["idx"] for s in offer["camera_suggestions"] if s["name"] == _SKU)
    pick = orch.handle_user_text(str(idx), _RefuseLLM())
    assert pick["status"] == "ok"

    state = orch.state_manager.load_active_project(orch.workspace_manager)
    cameras = state.design_properties.components["cameras"]
    assert cameras.properties["power_w"].value == pytest.approx(1.0)
    assert state.current_parameters.get("mission_accessory_power_w") == pytest.approx(1.0)


def test_t3_mirror_sums_camera_plus_radio():
    from jarvis.core.component_writers import set_mission_component_power
    from jarvis.schemas.action_schema import ComponentSpec

    radio = ComponentSpec(
        suggested_key="radio_module", completeness="medium",
        properties={"model": PropertyValue(value="elrs", confidence=0.8, source="declared")},
    )
    bound = bind_camera_from_catalog(_SKU)
    state = _state(cameras=bound, radio_module=radio)
    state = set_mission_component_power(state, "cameras", bound.properties["power_w"].value)
    state = set_mission_component_power(state, "radio_module", 0.5)
    assert state.current_parameters["mission_accessory_power_w"] == pytest.approx(1.5)


# ── T4 ────────────────────────────────────────────────────────────────────


def test_t4_free_text_runcam_still_no_power_w():
    spec = infer_component_for_key("cámara RunCam", "cameras", registry=aerial_registry)
    assert spec is not None
    assert spec.completeness == "medium"
    assert spec.catalog_ref is None
    assert "power_w" not in spec.properties


# ── T5 ────────────────────────────────────────────────────────────────────


def test_t5_manual_power_override_preserved_on_refresh():
    bound = bind_camera_from_catalog(_SKU)
    manual = bound.model_copy(update={
        "properties": {
            **bound.properties,
            "power_w": PropertyValue(value=2.0, unit="W", confidence=0.9, source="declared"),
        }
    })
    state = _state(cameras=manual)
    state = state.model_copy(update={
        "current_parameters": {**state.current_parameters, "mission_accessory_power_w": 2.0}
    })
    refreshed_state = refresh_component_from_catalog(state, "cameras")
    cameras = refreshed_state.design_properties.components["cameras"]
    assert cameras.properties["power_w"].value == pytest.approx(2.0)
    assert refreshed_state.current_parameters["mission_accessory_power_w"] == pytest.approx(2.0)

    # Re-picking the SAME sku (not an actual SKU change) also preserves it.
    repicked = bind_camera_from_catalog(_SKU, base=cameras)
    assert repicked.properties["power_w"].value == pytest.approx(2.0)


def test_t5_rebind_preserves_pose_and_manual_power_together():
    posed = bind_camera_from_catalog(_SKU).model_copy(update={
        "properties": {
            "power_w": PropertyValue(value=2.0, unit="W", confidence=0.9, source="declared"),
        },
        "mounted_on": "frame_plate",
        "declared_box_pose": DeclaredBoxPose(origin_key="frame_plate", x_mm=1.0, y_mm=2.0, z_mm=3.0),
    })
    refreshed = bind_camera_from_catalog(_SKU, base=posed)
    assert refreshed.properties["power_w"].value == pytest.approx(2.0)
    assert refreshed.mounted_on == "frame_plate"
    assert refreshed.declared_box_pose == DeclaredBoxPose(
        origin_key="frame_plate", x_mm=1.0, y_mm=2.0, z_mm=3.0
    )


# ── T6 ────────────────────────────────────────────────────────────────────


def _reasoning_context(margin=3.6196, parsed_constraints=None):
    return {
        "objective": "dron de vigilancia",
        "current_parameters": {"restrictions": "no", "payload_kg": 0.0, "mission_payload_mass_kg": 0.012},
        "design_properties": {"components": {}, "structure": {}},
        "last_calculation": None, "material": None,
        "last_simulation": {"safety_margin_ratio": margin, "status": "pass"},
        "memory": {}, "last_mutation": None, "mutation_mode": None,
        "parsed_constraints": parsed_constraints or {"autonomy_min": 8.0},
    }


def test_t6_bound_catalog_camera_with_power_clears_cta():
    context = _reasoning_context()
    context["design_properties"]["components"] = {
        "cameras": {
            "completeness": "high",
            "properties": {
                "model": {"value": "runcam"}, "mass_g": {"value": 9.0}, "power_w": {"value": 1.0},
            },
        },
        "radio_module": {
            "completeness": "medium",
            "properties": {"model": {"value": "elrs"}, "mass_g": {"value": 3.0}, "power_w": {"value": 0.5}},
        },
    }
    out = ReasoningLayer().build(context)
    assert out.suggested_actions[0].action_type != "declare_mission_power"
    assert out.suggested_actions[0].label != "Declara potencia de cámara (W)"


# ── T7 ────────────────────────────────────────────────────────────────────


def test_t7_radio_power_still_cta_when_camera_power_present():
    context = _reasoning_context()
    context["design_properties"]["components"] = {
        "cameras": {
            "completeness": "high",
            "properties": {
                "model": {"value": "runcam"}, "mass_g": {"value": 9.0}, "power_w": {"value": 1.0},
            },
        },
        "radio_module": {
            "completeness": "medium",
            "properties": {"model": {"value": "elrs"}, "mass_g": {"value": 3.0}},
        },
    }
    out = ReasoningLayer().build(context)
    assert out.suggested_actions[0].label == "Declara potencia de radio (W)"
    assert out.suggested_actions[0].action_type == "declare_mission_power"


# ── T8 ────────────────────────────────────────────────────────────────────


def test_t8_package_checkpoint_version():
    text = (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
    assert match is not None
    assert match.group(1) == "0.5.0"


# ── Extra: catalog list surfaces the cited watts ───────────────────────────


def test_catalog_list_shows_power_w():
    suggestions = build_camera_catalog_suggestions()
    row = next(s for s in suggestions if s["name"] == _SKU)
    assert row["power_w"] == pytest.approx(1.0)
