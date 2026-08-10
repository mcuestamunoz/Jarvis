"""FN-015 — Generic "help me define the current pending value" phrases.

Field-note case: DEFINE_MISSING with pending=["propellers"] (or motors then
propellers), "ayudame a definir el valor" / "ayudame a definir" today resolve
to intent "analyze" (\\bayudame\\b) and reach the LLM, which invents energy
talk (battery_capacity_wh) unrelated to the real pending item. Target: 0 LLM,
deterministic help for pending[0] only, no session restart.
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import MISSING_PROPULSION_PARAMETERS
from jarvis.schemas.action_schema import ComponentSpec, OrchestratorMode, PropertyValue


class _RefuseLLM:
    def interpret(self, *args, **kwargs):
        raise AssertionError("LLM.interpret must not be called")

    def analyze(self, *args, **kwargs):
        raise AssertionError("LLM.analyze must not be called")

    def generate(self, *args, **kwargs):
        raise AssertionError("LLM.generate must not be called")


class _StubLLM:
    """Permissive stub for the one case where reaching the LLM is expected."""

    def interpret(self, *args, **kwargs):
        return {"action": "iterate", "parameters": {}, "raw_user_input": None}

    def analyze(self, *args, **kwargs):
        return "respuesta genérica del LLM"

    def generate(self, *args, **kwargs):
        return {}


def _project_with_active_propulsion(
    tmp_path: Path, *, components_done: bool = False
) -> JarvisOrchestrator:
    """Same fixture pattern as FN-011/013/014: motors declared, propellers
    pending (Phase A) by default; both declared (Phase B, params pending)
    when components_done=True."""
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
    components = {}
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
    if components_done:
        components = {"motors": motors_spec, "propellers": propellers_spec}
    else:
        components = {"motors": motors_spec}
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


# ── A/B) generic help-define inside DEFINE_MISSING ─────────────────────────

def test_ayudame_definir_el_valor_helps_propellers_no_llm(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)

    result = orch.handle_user_text("ayudame a definir el valor", _RefuseLLM())

    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"
    assert result.get("question")
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert session.pending_param_definitions == ["propellers"]


def test_ayudame_definir_bare_helps_propellers_no_llm(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)

    result = orch.handle_user_text("ayudame a definir", _RefuseLLM())

    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert session.pending_param_definitions == ["propellers"]


# ── proof: battery/energy never suggested when pending is propellers ───────

def test_help_does_not_mention_battery_when_pending_propellers(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)

    result = orch.handle_user_text("ayudame a definir el valor", _RefuseLLM())

    blob = f"{result.get('message') or ''} {result.get('question') or ''}".lower()
    assert "battery_capacity_wh" not in blob
    assert "batería" not in blob
    assert "bateria" not in blob
    assert "energía" not in blob
    assert "energia" not in blob


# ── C) assisted motor param pending → catalog help family ──────────────────

def test_ayudame_definir_with_assisted_param_pending_uses_catalog_help(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path, components_done=True)
    # Start the wizard directly with only the assisted param pending
    # (per_motor_max_thrust_n) — same pattern as test_assisted_acquisition.py's
    # _energy_project fixture, where pending[0] is genuinely an assisted param.
    orch.start_define_missing_params(
        ["per_motor_max_thrust_n"], reason=MISSING_PROPULSION_PARAMETERS
    )
    session = orch.state_manager.get_runtime_session()
    assert session.pending_param_definitions == ["per_motor_max_thrust_n"]

    result = orch.handle_user_text("ayudame a definir", _RefuseLLM())

    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"
    # Catalog-help family response shape (FN-005/FN-006's offer_catalog_help).
    assert "motor_suggestions" in result


# ── D) FN-005 regression — motor catalog help unaffected ───────────────────

def test_ayudame_elegir_motor_still_catalog(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path, components_done=True)
    orch.start_define_missing_params(
        ["per_motor_max_thrust_n"], reason=MISSING_PROPULSION_PARAMETERS
    )

    result = orch.handle_user_text("ayúdame a elegir el motor", _RefuseLLM())

    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"
    assert result.get("motor_suggestions") is not None


# ── E) FN-013 regression — named block re-prompt unaffected ────────────────

def test_definir_propulsion_still_fn013(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)

    result = orch.handle_user_text("definir propulsión", _RefuseLLM())

    assert result.get("block_declaration_reprompt") is True
    assert result["action"] == "define_missing_params"


# ── F) real analyze phrase still may reach the LLM ──────────────────────────

def test_real_analyze_phrase_still_may_use_llm(tmp_path: Path):
    """Proves FN-015 does not swallow every 'ayudame*'/analyze-shaped input —
    a genuine analysis question must still be allowed to reach the LLM."""
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)

    result = orch.handle_user_text("analiza el margen de seguridad", _StubLLM())

    assert result.get("action") != "define_missing_params" or result.get("status") == "ok"
    # The defining proof: this specific phrase is NOT claimed as pending-help.
    assert result.get("pending_help") is not True
    assert result.get("block_declaration_reprompt") is not True


# ── H) collected_params preserved across help (no session restart) ─────────

def test_collected_params_preserved_on_help(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)
    session = orch.state_manager.get_runtime_session()
    orch.state_manager.set_runtime_session(
        session.model_copy(update={"collected_params": {"motor_count": 4.0}})
    )

    orch.handle_user_text("ayudame a definir el valor", _RefuseLLM())

    after = orch.state_manager.get_runtime_session()
    assert after.collected_params == {"motor_count": 4.0}
    assert after.pending_param_definitions == ["propellers"]


# ── G) IDLE bare help-define opens acquisition + help, not iterate ─────────

def test_idle_ayudame_definir_opens_acquisition_help(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)

    result = orch.handle_user_text("ayudame a definir", _RefuseLLM())

    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert session.mode != OrchestratorMode.ITERATE_INTERACTIVE
    assert "propellers" in session.pending_param_definitions
