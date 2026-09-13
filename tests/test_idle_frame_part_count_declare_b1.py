"""IDLE frame-part count declare B1.

Covers implementation_contract_idle_frame_part_count_declare_b1.md §3-3.2:
  T1  IDLE + existing non-low frame + "6 standoffs" -> count 6 on
      frame_standoff, LLM never called
  T2  "6 separadores" -> same
  T3  "standoffs aluminio" -> material on child only, frame.material
      unchanged
  T4  no frame declared -> bridge falls through (None), no upsert
  T5  G-N1 DEFINE_MISSING wizard parts-only path still works unchanged
      (regression)
  T6  after IDLE "4 standoffs", spec count == 4 (B4-min projector gate
      reuse — the projector itself is untouched by this Buy)
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import MISSING_COMPONENT_DEFINITION
from jarvis.domains.aerial import FRAME_ARM_KEY, FRAME_STANDOFF_KEY
from jarvis.schemas.action_schema import ComponentSpec, OrchestratorMode, PropertyValue

_CREATE = {
    "vehicle_type": "dron",
    "objective": "idle frame part declare test",
    "payload_kg": 1.0,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "motors": 4,
    "per_motor_max_thrust_n": 12.0,
    "structure_mass_factor": 0.5,
    "safety_factor": 1.2,
}


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _frame_spec(mass_kg: float = 0.45, material: str = "fibra de carbono") -> ComponentSpec:
    return ComponentSpec(
        suggested_key="frame", completeness="high", source="declared",
        properties={
            "mass_kg": PropertyValue(value=mass_kg, unit="kg", source="declared"),
            "material": PropertyValue(value=material, unit=None, source="declared"),
        },
    )


def _fresh_with_frame(tmp_path: Path) -> JarvisOrchestrator:
    o = JarvisOrchestrator(workspace_root=tmp_path)
    o.handle({"action": "create_project", "parameters": _CREATE})
    ps = o.state_manager.load_active_project(o.workspace_manager)
    dp = ps.design_properties.model_copy(update={"components": {"frame": _frame_spec()}})
    o.workspace_manager.save_state(ps.model_copy(update={"design_properties": dp}))
    return o


def test_t1_idle_six_standoffs_sets_count_no_llm(tmp_path: Path):
    o = _fresh_with_frame(tmp_path)
    assert o.state_manager.runtime_state.session.mode == OrchestratorMode.IDLE

    result = o.handle_user_text("6 standoffs", _RefuseLLM())
    assert result["status"] == "ok"
    assert "standoff×6" in result["message"]

    reloaded = o.state_manager.load_active_project(o.workspace_manager)
    standoff = reloaded.design_properties.components[FRAME_STANDOFF_KEY]
    assert standoff.properties["count"].value == 6
    # Session stayed IDLE — no wizard opened.
    assert o.state_manager.runtime_state.session.mode == OrchestratorMode.IDLE


def test_t2_idle_six_separadores_same(tmp_path: Path):
    o = _fresh_with_frame(tmp_path)
    result = o.handle_user_text("6 separadores", _RefuseLLM())
    assert result["status"] == "ok"
    reloaded = o.state_manager.load_active_project(o.workspace_manager)
    assert reloaded.design_properties.components[FRAME_STANDOFF_KEY].properties["count"].value == 6


def test_t3_idle_standoffs_aluminio_material_only_root_unchanged(tmp_path: Path):
    o = _fresh_with_frame(tmp_path)
    result = o.handle_user_text("standoffs aluminio", _RefuseLLM())
    assert result["status"] == "ok"
    reloaded = o.state_manager.load_active_project(o.workspace_manager)
    standoff = reloaded.design_properties.components[FRAME_STANDOFF_KEY]
    assert standoff.properties["material"].value == "aluminio"
    assert "count" not in standoff.properties
    # Root frame material untouched — never rewritten from a part clause.
    assert reloaded.design_properties.components["frame"].properties["material"].value == "fibra de carbono"


def test_t4_no_frame_falls_through_no_upsert(tmp_path: Path):
    o = JarvisOrchestrator(workspace_root=tmp_path)
    o.handle({"action": "create_project", "parameters": _CREATE})
    result = o._try_handle_idle_frame_part_declare("6 standoffs")
    assert result is None
    reloaded = o.state_manager.load_active_project(o.workspace_manager)
    assert FRAME_STANDOFF_KEY not in reloaded.design_properties.components


def test_t4b_root_update_present_is_not_this_bridge(tmp_path: Path):
    o = _fresh_with_frame(tmp_path)
    result = o._try_handle_idle_frame_part_declare("6 standoffs, wheelbase 230mm")
    assert result is None


def _open_frame_wizard(o: JarvisOrchestrator) -> None:
    session = o.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "pending_missing_params": ["frame"],
        "pending_define_missing": False,
    })
    o.state_manager.set_runtime_session(updated)


def test_t5_gn1_wizard_parts_only_path_still_works(tmp_path: Path):
    o = _fresh_with_frame(tmp_path)
    _open_frame_wizard(o)
    result = o.handle_user_text("4 brazos fibra de carbono", _RefuseLLM())
    assert result["status"] == "ok"
    assert "arm×4" in result["message"]
    reloaded = o.state_manager.load_active_project(o.workspace_manager)
    arm = reloaded.design_properties.components[FRAME_ARM_KEY]
    assert arm.properties["count"].value == 4
    assert arm.properties["material"].value == "fibra de carbono"


def test_t6_idle_four_standoffs_spec_count_four(tmp_path: Path):
    o = _fresh_with_frame(tmp_path)
    o.handle_user_text("4 standoffs", _RefuseLLM())
    reloaded = o.state_manager.load_active_project(o.workspace_manager)
    assert reloaded.design_properties.components[FRAME_STANDOFF_KEY].properties["count"].value == 4
