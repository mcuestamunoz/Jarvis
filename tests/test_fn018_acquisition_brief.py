"""FN-018 — Thin Acquisition Brief + component-question harmonization (Step C).

C0 (mandatory): every path that asks about a pending component key must use
COMPONENT_PROMPTS/Brief — never "¿Cuál es el valor de propellers?". The one
remaining offender was `_try_reprompt_active_block_declaration` (FN-013).

C1: opening/re-prompting a component-definition target shows a short
deterministic Brief (what/knows/why/options), built from ProjectState facts
only — no LLM, no dialogue state.
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import ComponentSpec, OrchestratorMode, PropertyValue

_GENERIC_VALOR_PROPELLERS = "¿Cuál es el valor de propellers?"


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


def _open_component_acquisition(orch: JarvisOrchestrator) -> dict:
    result = orch.handle_user_text("ayúdame a declarar propulsión", _RefuseLLM())
    assert result["action"] == "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert session.pending_param_definitions == ["propellers"]
    return result


def _blob(result: dict) -> str:
    return f"{result.get('message') or ''} {result.get('question') or ''}"


# 1. Phase A open shows the Brief, not the generic valor-de question ────────

def test_phase_a_open_shows_brief_not_valor_de_propellers(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    result = _open_component_acquisition(orch)
    blob = _blob(result)
    assert _GENERIC_VALOR_PROPELLERS not in blob
    assert "hélices" in blob.lower() or "helices" in blob.lower()
    # Brief structure: motors already declared should surface as a known fact.
    assert "motor" in (result.get("message") or "").lower()


# 2. FN-013 reprompt — C0 mandatory ──────────────────────────────────────────

def test_fn013_reprompt_uses_component_prompt_not_generic_valor(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)

    result = orch.handle_user_text("definir propulsión", _RefuseLLM())

    assert result.get("block_declaration_reprompt") is True
    blob = _blob(result)
    assert _GENERIC_VALOR_PROPELLERS not in blob
    assert "hélices" in blob.lower() or "helices" in blob.lower()


# 3. Unclear input mid-wizard still gets the propellers Brief/prompt ────────

def test_unclear_input_still_propellers_brief(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)

    result = orch.handle_user_text("5", _RefuseLLM())

    blob = _blob(result)
    assert _GENERIC_VALOR_PROPELLERS not in blob
    assert "material y masa" not in blob.lower()
    assert "hélices" in blob.lower() or "helices" in blob.lower()


# 4. FN-015 generic help path uses the Brief/COMPONENT_PROMPTS ─────────────

def test_fn015_help_uses_brief_or_component_prompt(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)

    result = orch.handle_user_text("ayudame a definir", _RefuseLLM())

    assert result["status"] == "interactive"
    blob = _blob(result)
    assert _GENERIC_VALOR_PROPELLERS not in blob
    assert "hélices" in blob.lower() or "helices" in blob.lower()


# 5. Recognized description still saves (FN-017 regression) ────────────────

def test_helices_still_saves(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)

    result = orch.handle_user_text("hélices 10x4.5", _RefuseLLM())

    assert result["status"] == "ok"
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    propellers = saved.design_properties.components.get("propellers")
    assert propellers is not None
    assert propellers.completeness != "low"


# 6. Generic-only match still refused (FN-017 regression) ──────────────────

def test_generic_still_refused(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)

    orch.handle_user_text("plastico 450g", _RefuseLLM())

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert not any(
        getattr(c, "suggested_key", None) == "generic_component"
        for c in saved.design_properties.components.values()
    )


# 7. Frame Brief/prompt stays frame-specific, never propeller text ─────────

def test_frame_brief_or_prompt_not_propellers(tmp_path: Path):
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

    opened = orch.handle_user_text("ayúdame a declarar estructura", _RefuseLLM())
    assert opened["action"] == "define_missing_params"
    blob = _blob(opened)
    assert "hélices" not in blob.lower() and "helices" not in blob.lower()

    result = orch.handle_user_text("fibra de carbono", _RefuseLLM())
    message = (result.get("message") or "").lower()
    assert "pesa" in message or "masa" in message
    assert "hélices" not in message and "helices" not in message


# 8. FN-016 navigation regression ───────────────────────────────────────────

def test_atras_still_cancels(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)
    result = orch.handle_user_text("atrás", _RefuseLLM())
    assert result["status"] == "cancelled"
    assert orch.state_manager.get_runtime_session().mode == OrchestratorMode.IDLE
