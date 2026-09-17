"""Extended identity rules B1 (`B1-extended-identity-rules`).

Covers implementation_contract_extended_identity_rules_b1.md §2:

  T1  Helper: payload/manipulation/actuation/transmission -> resolvable
      with live aerial_registry
  T2  Free-text/extractor: phrase -> payload_bay medium (model set)
  T3  Manipulator phrase -> arm medium; does not create/overwrite frame_arm
  T4  Wheels phrase -> wheels medium
  T5  Gearbox phrase -> gearbox medium
  T6  SYSTEM_DEFINITION B -> payload / brazo manipulador (or locked alias)
      accepts; stubs present after 'listo'
  T7  Bare frame-arm path still works ("brazo carbono" / existing Structure
      B fixtures) -- no steal
  T8  cameras/radio identity tests still green (checked via full suite)
  T9  Completeness: no model -> low; with model -> medium (not high)
  T10 Full pytest green (checked at the repo level)
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.component_inference import infer_component
from jarvis.core.system_architecture_catalog import block_components_are_resolvable
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.domains.aerial import aerial_registry


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


# ── T1 ────────────────────────────────────────────────────────────────────


def test_t1_all_four_previously_gated_blocks_now_resolvable():
    for block in ("payload", "manipulation", "actuation", "transmission"):
        assert block_components_are_resolvable(block) is True, block


# ── T2 ────────────────────────────────────────────────────────────────────


def test_t2_payload_bay_generic_phrase_reaches_medium():
    spec = infer_component("bahía de carga")
    assert spec.suggested_key == "payload_bay"
    assert spec.component_type == "payload"
    assert spec.completeness == "medium"
    assert spec.properties["model"].value == "generic_payload_bay"


def test_t2_payload_bay_gopro_descriptor_reaches_medium_with_specific_model():
    spec = infer_component("payload GoPro bay")
    assert spec.suggested_key == "payload_bay"
    assert spec.completeness == "medium"
    assert spec.properties["model"].value == "gopro_bay"


def test_t2_payload_bay_bare_via_forced_key_stays_low():
    from jarvis.core.component_inference import infer_component_for_key

    spec = infer_component_for_key("no sé qué es esto", "payload_bay", registry=aerial_registry)
    assert spec.suggested_key == "payload_bay"
    assert spec.completeness == "low"


# ── T3 ────────────────────────────────────────────────────────────────────


def test_t3_manipulator_phrase_reaches_medium():
    spec = infer_component("brazo manipulador")
    assert spec.suggested_key == "arm"
    assert spec.component_type == "manipulation"
    assert spec.completeness == "medium"
    assert spec.properties["model"].value == "robotic_arm"

    spec2 = infer_component("robotic arm 6 DOF")
    assert spec2.suggested_key == "arm"
    assert spec2.completeness == "medium"
    # DOF text never becomes a structured property
    assert "dof" not in spec2.properties
    assert set(spec2.properties) == {"model"}


def test_t3_manipulator_never_touches_frame_arm_key():
    spec = infer_component("brazo manipulador")
    assert spec.suggested_key != "frame_arm"


# ── T4 ────────────────────────────────────────────────────────────────────


def test_t4_wheels_count_phrase_reaches_medium():
    spec = infer_component("4 ruedas")
    assert spec.suggested_key == "wheels"
    assert spec.completeness == "medium"
    assert spec.properties["wheel_count"].value == 4


def test_t4_wheels_type_phrase_reaches_medium_without_count():
    spec = infer_component("wheels omni")
    assert spec.suggested_key == "wheels"
    assert spec.completeness == "medium"
    assert spec.properties["wheel_type"].value == "omni"


def test_t4_wheels_bare_stays_low():
    spec = infer_component("rueda")
    assert spec.suggested_key == "wheels"
    assert spec.completeness == "low"


# ── T5 ────────────────────────────────────────────────────────────────────


def test_t5_gearbox_ratio_reaches_medium():
    spec = infer_component("gearbox 5:1")
    assert spec.suggested_key == "gearbox"
    assert spec.component_type == "transmission"
    assert spec.completeness == "medium"
    assert spec.properties["model"].value == "gearbox_5_1"


def test_t5_gearbox_bare_stays_low():
    spec = infer_component("reductor")
    assert spec.suggested_key == "gearbox"
    assert spec.completeness == "low"


# ── T6 ────────────────────────────────────────────────────────────────────


def _orch_with_project(tmp_path: Path) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "extended identity rules b1",
            "payload_kg": 1.0, "restrictions": "no", "detail_level": "detallado",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    return orch


def test_t6_system_definition_b_payload_and_manipulador_accept_with_stubs(tmp_path: Path):
    orch = _orch_with_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    orch.system_definition_session.start("dron", ps)
    orch.system_definition_session.answer("b")

    r1 = orch.system_definition_session.answer("payload")
    assert "todavía no puedo resolver" not in r1["message"].lower()
    r2 = orch.system_definition_session.answer("brazo manipulador")
    assert "todavía no puedo resolver" not in r2["message"].lower()

    orch.system_definition_session.answer("listo")
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert "payload_bay" in saved.design_properties.components
    assert "arm" in saved.design_properties.components
    # Base architecture still applied
    assert "motors" in saved.design_properties.components


def test_t6_system_definition_b_wheels_and_gearbox_accept_with_stubs(tmp_path: Path):
    orch = _orch_with_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    orch.system_definition_session.start("dron", ps)
    orch.system_definition_session.answer("b")

    r1 = orch.system_definition_session.answer("ruedas")
    assert "actuation" in r1["message"]
    r2 = orch.system_definition_session.answer("gearbox")
    assert "transmission" in r2["message"]

    orch.system_definition_session.answer("listo")
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert "wheels" in saved.design_properties.components
    assert "gearbox" in saved.design_properties.components


# ── T7 ────────────────────────────────────────────────────────────────────


def test_t7_frame_arm_freetext_declare_not_stolen_by_manipulator_rule(tmp_path: Path):
    spec = infer_component("4 brazos carbono")
    assert spec.suggested_key == "frame"

    orch = _orch_with_project(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    orch.system_definition_session.start("dron", ps)
    orch.system_definition_session.answer("a")
    result = orch.handle_user_text("frame de fibra de carbono 450g, 4 brazos", _RefuseLLM())
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert "frame_arm" in saved.design_properties.components or "frame" in saved.design_properties.components
    assert "arm" not in saved.design_properties.components


def test_t7_wheelbase_freetext_not_stolen_by_wheels_rule():
    """Regression caught during implementation: bare 'wheel' is a substring
    of 'wheelbase' (a frame configuration term) — the rule keyword list
    excludes bare 'wheel' specifically to prevent this."""
    rule = aerial_registry.match("quad-x wheelbase 230mm", "wheelbase")
    assert rule is None or rule.suggested_key != "wheels"


# ── T9 ────────────────────────────────────────────────────────────────────


def test_t9_completeness_ladder_never_reaches_high_without_catalog():
    for phrase in ("payload GoPro bay", "brazo manipulador", "4 ruedas", "gearbox 5:1"):
        spec = infer_component(phrase)
        assert spec.completeness in ("low", "medium")
        assert spec.completeness != "high"
