"""FN-019 — Bare propeller size ("10x4.5", no "hélices" keyword) while
propellers is the acquisition target.

Root cause: aerial_registry's propeller ComponentRule only matches on keyword
(helice/hélice/propeller/props) — extract_propeller_properties already parses
"10x4.5" fine, it just never runs without the keyword, so the user loops on
the Brief forever (FN-017/018 correctly refuse the resulting generic_component
write). COMPONENT_PROMPTS/Brief advertise '10x4.5' as the example — it must
actually work.

Fix: orchestrator._handle_component_description, gated strictly on
"propellers" in expected_keys and no other real match found — forces
inference against the propellers rule via
component_inference.infer_component_for_key (same extractor, no new regex).
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import ComponentSpec, OrchestratorMode, PropertyValue


class _RefuseLLM:
    def interpret(self, *args, **kwargs):
        raise AssertionError("LLM.interpret must not be called")

    def analyze(self, *args, **kwargs):
        raise AssertionError("LLM.analyze must not be called")

    def generate(self, *args, **kwargs):
        raise AssertionError("LLM.generate must not be called")


def _project_with_active_propulsion(tmp_path: Path) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "transporte de carga",
            "payload_kg": 2.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "structure_mass_factor": 0.6,
            "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    motors_spec = ComponentSpec(
        name="4 motores 920kv",
        component_type="propulsion_active",
        suggested_key="motors",
        completeness="high",
        source="declared",
        properties={
            "motor_count": PropertyValue(value=4),
            "kv_rating": PropertyValue(value=920),
        },
    )
    # ERF-2 ★5: esc is now part of BLOCK_TO_COMPONENTS["propulsion"] — declared
    # from the start so this file's own target (propellers pending) stays the
    # only thing under test, not co-mingled with esc.
    esc_spec = ComponentSpec(
        name="ESC 30A",
        component_type="propulsion_active",
        suggested_key="esc",
        completeness="high",
        source="declared",
        properties={"current_a": PropertyValue(value=30.0)},
    )
    dp = ps.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure", "control"],
        "system_priority": ["propulsion", "energy", "structure", "control"],
        "components": {"motors": motors_spec, "esc": esc_spec},
    })
    orch.workspace_manager.save_state(ps.model_copy(update={"design_properties": dp}))
    return orch


def _open_propellers_wizard(orch: JarvisOrchestrator) -> None:
    result = orch.handle_user_text("ayúdame a declarar propulsión", _RefuseLLM())
    assert result["action"] == "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert session.pending_param_definitions == ["propellers"]


def _project_with_frame_pending(tmp_path: Path) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "transporte de carga",
            "payload_kg": 2.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "structure_mass_factor": 0.6,
            "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    dp = ps.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["structure", "propulsion", "energy", "control"],
        "system_priority": ["structure", "propulsion", "energy", "control"],
    })
    orch.workspace_manager.save_state(ps.model_copy(update={"design_properties": dp}))
    orch.handle_user_text("ayúdame a declarar estructura", _RefuseLLM())
    return orch


# A. Bare "10x4.5" saves propellers in Phase A ──────────────────────────────

def test_bare_10x45_saves_propellers(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_propellers_wizard(orch)

    result = orch.handle_user_text("10x4.5", _RefuseLLM())

    assert result["status"] == "ok"
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    propellers = saved.design_properties.components.get("propellers")
    assert propellers is not None
    assert propellers.suggested_key == "propellers"
    assert propellers.completeness != "low"
    assert float(propellers.properties["diameter_in"].value) == 10.0
    assert float(propellers.properties["pitch_in"].value) == 4.5
    assert "count" not in (propellers.properties or {})


# B. Spaced "10 x 4.5" — same as A ──────────────────────────────────────────

def test_bare_10_x_4_5_spaced_saves_propellers(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_propellers_wizard(orch)

    result = orch.handle_user_text("10 x 4.5", _RefuseLLM())

    assert result["status"] == "ok"
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    propellers = saved.design_properties.components.get("propellers")
    assert propellers is not None
    assert propellers.completeness != "low"


# C. "hélices 10x4.5" (keyword path) still works — regression ──────────────

def test_helices_keyword_form_still_works(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_propellers_wizard(orch)

    result = orch.handle_user_text("hélices 10x4.5", _RefuseLLM())

    assert result["status"] == "ok"
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    propellers = saved.design_properties.components.get("propellers")
    assert propellers is not None
    assert propellers.completeness != "low"


# D. Bare "5" (no pitch) does not become fake propellers — re-prompts ──────

def test_bare_number_without_pitch_does_not_save(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_propellers_wizard(orch)

    result = orch.handle_user_text("5", _RefuseLLM())

    assert result["status"] == "interactive"
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.design_properties.components.get("propellers") is None
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS


# E. Frame pending — "10x4.5" must not be stolen as propellers ─────────────

def test_frame_pending_10x45_not_stolen_as_propellers(tmp_path: Path):
    orch = _project_with_frame_pending(tmp_path)

    result = orch.handle_user_text("10x4.5", _RefuseLLM())

    message = (result.get("message") or "").lower()
    assert "material y masa" in message or "pesa" in message or "material" in message
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.design_properties.components.get("propellers") is None
    assert saved.design_properties.components.get("frame") is None


# F. Brief / FN-015 help still 0 LLM (regression smoke) ─────────────────────

def test_brief_and_help_still_zero_llm(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    result = orch.handle_user_text("ayúdame a declarar propulsión", _RefuseLLM())
    assert result["action"] == "define_missing_params"

    help_result = orch.handle_user_text("ayudame a definir", _RefuseLLM())
    assert help_result["status"] == "interactive"


# G. "plastico 450g" still no generic write — regression ───────────────────

def test_generic_description_still_refused(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_propellers_wizard(orch)

    orch.handle_user_text("plastico 450g", _RefuseLLM())

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert not any(
        getattr(c, "suggested_key", None) == "generic_component"
        for c in saved.design_properties.components.values()
    )
    assert saved.design_properties.components.get("propellers") is None
