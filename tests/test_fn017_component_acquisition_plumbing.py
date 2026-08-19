"""FN-017 — Component acquisition plumbing (Step B, P0 fixes only — no Guidance).

Field-note session (propulsion / propellers pending, live CLI):
    definir propulsión → ¿Cuál es el valor de propellers?
    declarar batería / 10x4.5 / 5 / definir hélices
      → "Indica material y masa. Ej: fibra de carbono 450g"     # WRONG — frame fallback
    plastico 450g → "Generic component registrado."             # WRONG — silent junk write
    declarar motores (IDLE, motors high, propellers low)
      → wizard per_actuator_torque_nm (terrestrial)              # WRONG domain
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


def _project_with_active_propulsion(
    tmp_path: Path, *, components_done: bool = False
) -> JarvisOrchestrator:
    """Same fixture pattern as FN-011/014/016: motors declared, propellers
    pending (Phase A) by default."""
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
    propellers_spec = ComponentSpec(
        name="helices 10x4.5",
        component_type="propulsion_passive",
        suggested_key="propellers",
        completeness="high",
        source="declared",
        properties={"diameter_in": PropertyValue(value=10.0)},
    )
    # ERF-2 ★5: esc is now part of BLOCK_TO_COMPONENTS["propulsion"] — declared
    # from the start in both cases so this file's own target (propellers
    # pending) stays the only thing under test, not co-mingled with esc.
    esc_spec = ComponentSpec(
        name="ESC 30A",
        component_type="propulsion_active",
        suggested_key="esc",
        completeness="high",
        source="declared",
        properties={"current_a": PropertyValue(value=30.0)},
    )
    components = {"motors": motors_spec, "propellers": propellers_spec, "esc": esc_spec} if components_done else {
        "motors": motors_spec, "esc": esc_spec
    }
    dp = ps.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure", "control"],
        "system_priority": ["propulsion", "energy", "structure", "control"],
        "components": components,
    })
    orch.workspace_manager.save_state(ps.model_copy(update={"design_properties": dp}))
    return orch


def _open_component_acquisition(orch: JarvisOrchestrator) -> None:
    """Open DEFINE_MISSING for propulsion components (Phase A: propellers)."""
    result = orch.handle_user_text("ayúdame a declarar propulsión", _RefuseLLM())
    assert result["action"] == "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert session.pending_param_definitions == ["propellers"]


# ── A) pending_missing_params stays coherent on a live wizard ──────────────

def test_phase_a_session_has_pending_missing_params(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)
    session = orch.state_manager.get_runtime_session()
    assert session.pending_missing_params == ["propellers"]
    assert session.pending_missing_reason == "missing_component_definition"


# ── B) unclear/low input while propellers pending → propellers hint ────────

def test_unclear_input_prompts_propellers_not_frame(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)

    for phrase in ("definir hélices", "5", "declarar batería"):
        result = orch.handle_user_text(phrase, _RefuseLLM())
        message = (result.get("message") or result.get("question") or "").lower()
        assert "material y masa" not in message, f"{phrase!r} -> {message!r}"
        assert "frame" not in message, f"{phrase!r} -> {message!r}"
        assert "hélices" in message or "helices" in message, f"{phrase!r} -> {message!r}"
        # Wizard must still be open on propellers — none of these were misread
        # as navigation/escape/a value that advances the wizard.
        session = orch.state_manager.get_runtime_session()
        assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
        assert "propellers" in (session.pending_param_definitions or []) or (
            "propellers" in (session.pending_missing_params or [])
        )


# ── C) a recognized propeller phrase still saves (regression) ──────────────

def test_helices_description_saves_propellers(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)

    result = orch.handle_user_text("hélices 10x4.5", _RefuseLLM())

    assert result["status"] == "ok"
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    propellers = saved.design_properties.components.get("propellers")
    assert propellers is not None
    assert propellers.suggested_key == "propellers"
    assert propellers.completeness != "low"


# ── D) generic-only match never gets silently written ───────────────────────

def test_generic_description_does_not_write_generic_component(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)

    result = orch.handle_user_text("plastico 450g", _RefuseLLM())

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert not any(
        getattr(c, "suggested_key", None) == "generic_component"
        for c in saved.design_properties.components.values()
    )
    assert "propellers" not in saved.design_properties.components or (
        saved.design_properties.components["propellers"].completeness == "low"
        or saved.design_properties.components.get("propellers") is None
    )
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert result["status"] == "interactive"


# ── E) opening question uses the component prompt, not the generic one ─────

def test_phase_a_start_question_uses_component_prompt(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    result = orch.handle_user_text("ayúdame a declarar propulsión", _RefuseLLM())
    question = result.get("question") or ""
    assert question != "¿Cuál es el valor de propellers?"
    assert "hélices" in question.lower() or "helices" in question.lower()


# ── F) aerial "declarar motores" does not open the torque wizard ───────────

def test_declarar_motores_aerial_does_not_open_torque_wizard(tmp_path: Path):
    """motors already high, propellers still low — 'declarar motores' must
    continue propulsion's remaining gap (propellers), never open a ground
    transmission-torque wizard on an aerial project."""
    orch = _project_with_active_propulsion(tmp_path)

    result = orch.handle_user_text("declarar motores", _RefuseLLM())

    assert result is not None
    message_blob = f"{result.get('message') or ''} {result.get('question') or ''}".lower()
    assert "torque" not in message_blob
    assert "per_actuator_torque_nm" not in message_blob
    session = orch.state_manager.get_runtime_session()
    assert session.param_definition_reason != "missing_transmission_parameters"
    assert "propellers" in (session.pending_param_definitions or [])


# ── G) regressions — FN-013 / FN-015 / FN-016 ───────────────────────────────

def test_definir_propulsion_still_fn013(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)
    result = orch.handle_user_text("definir propulsión", _RefuseLLM())
    assert result.get("block_declaration_reprompt") is True


def test_ayudame_definir_still_fn015(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)
    result = orch.handle_user_text("ayudame a definir", _RefuseLLM())
    assert result["status"] == "interactive"
    session = orch.state_manager.get_runtime_session()
    assert "propellers" in (session.pending_param_definitions or [])


def test_atras_still_cancels_fn016(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)
    result = orch.handle_user_text("atrás", _RefuseLLM())
    assert result["status"] == "cancelled"
    assert orch.state_manager.get_runtime_session().mode == OrchestratorMode.IDLE


# ── H) frame acquisition is unbroken — still asks material/masa ────────────

def test_frame_pending_still_asks_material_masa(tmp_path: Path):
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

    # Partial description (material only, no mass) — frame's fine-grained
    # has_mass/has_material probe must still fire.
    result = orch.handle_user_text("fibra de carbono", _RefuseLLM())
    message = (result.get("message") or "").lower()
    assert "pesa" in message or "masa" in message
