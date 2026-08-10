"""FN-016 — Navigation words and unsafe parses must never be absorbed as
parameter values inside an open acquisition wizard.

Field-note cases:
  A) "atrás"/"volver" during DEFINE_MISSING (Phase A or B) → cancel, not a
     value, not the LLM.
  B) A component key (propellers/motors/battery/…) must never receive a bare
     float positionally (e.g. propellers=10.0) via ParamDefinitionSession.answer.
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import (
    MISSING_COMPONENT_DEFINITION,
    MISSING_PROPULSION_PARAMETERS,
)
from jarvis.schemas.action_schema import (
    ComponentSpec,
    InteractiveSessionState,
    OrchestratorMode,
    PropertyValue,
)


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
    """Same fixture pattern as FN-011/013/014/015: motors declared, propellers
    pending (Phase A) by default; both declared (Phase B) when
    components_done=True."""
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
    components = {"motors": motors_spec, "propellers": propellers_spec} if components_done else {
        "motors": motors_spec
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


# ── A) navigation cancels — Phase A (component-driven) ─────────────────────

def test_atras_cancels_component_acquisition_phase_a(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)

    result = orch.handle_user_text("atrás", _RefuseLLM())

    assert result["status"] == "cancelled"
    assert result["action"] == "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.IDLE
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert "propellers" not in saved.design_properties.components or (
        saved.design_properties.components["propellers"].completeness == "high"
    )


def test_atras_unaccented_also_cancels(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)
    result = orch.handle_user_text("atras", _RefuseLLM())
    assert result["status"] == "cancelled"


# ── B) navigation cancels — Phase B (numeric-driven) ────────────────────────

def test_volver_cancels_numeric_wizard_phase_b(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path, components_done=True)
    orch.start_define_missing_params(
        ["per_motor_max_thrust_n"], reason=MISSING_PROPULSION_PARAMETERS
    )
    session_before = orch.state_manager.get_runtime_session()
    collected_before = dict(session_before.collected_params)

    result = orch.handle_user_text("volver", _RefuseLLM())

    assert result["status"] == "cancelled"
    session_after = orch.state_manager.get_runtime_session()
    assert session_after.mode == OrchestratorMode.IDLE
    # No value stored for that turn.
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.current_parameters.get("per_motor_max_thrust_n") is None
    assert collected_before == {}


# ── C) numeric entry still works (regression) ───────────────────────────────

def test_numeric_value_still_accepted_phase_b(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path, components_done=True)
    orch.start_define_missing_params(
        ["per_motor_max_thrust_n"], reason=MISSING_PROPULSION_PARAMETERS
    )

    result = orch.handle_user_text("14", _RefuseLLM())

    assert result["status"] == "ok"
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.current_parameters.get("per_motor_max_thrust_n") == 14.0


# ── D) component description still works (regression) ──────────────────────

def test_propeller_description_still_works_phase_a(tmp_path: Path):
    """Uses the proven fixture phrase from test_propulsion_composite_wizard_flow.py
    (bare '10x4.5' with no 'hélices' keyword is never recognized by the aerial
    registry — that is pre-existing component-inference behavior, unrelated to
    FN-016, so this test targets the phrase the registry actually matches)."""
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)

    result = orch.handle_user_text("hélices 10x4.5", _RefuseLLM())

    assert result["status"] == "ok"
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    propellers = saved.design_properties.components.get("propellers")
    assert propellers is not None
    assert propellers.completeness != "low"


def test_component_description_works_via_original_bug54_confirmation(tmp_path: Path):
    """Discovered while implementing FN-016: pending_missing_reason (the field
    the old UX-C intercept checked) is only meaningful BEFORE
    start_define_missing_params runs — ParamDefinitionSession.start() builds a
    fresh session that never carries it forward, so it is always "" on an
    already-open wizard's own turns, regardless of which bridge opened it
    (Bug54's own "¿Definimos X ahora?" → "sí" flow included). Before the
    orchestrator fix (checking param_definition_reason too), a real component
    description right after "sí" fell through to the numeric parser and
    silently corrupted current_parameters["propellers"] = 10.0."""
    orch = _project_with_active_propulsion(tmp_path)
    session = orch.state_manager.get_runtime_session()
    orch.state_manager.set_runtime_session(session.model_copy(update={
        "pending_define_missing": True,
        "pending_missing_params": ["propellers"],
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
    }))

    opened = orch.handle_user_text("si", _RefuseLLM())
    assert opened["action"] == "define_missing_params"

    result = orch.handle_user_text("hélices 10x4.5", _RefuseLLM())

    assert result["status"] == "ok"
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    propellers = saved.design_properties.components.get("propellers")
    assert propellers is not None
    assert propellers.completeness != "low"
    assert saved.current_parameters.get("propellers") is None  # never corrupted


# ── E) bare float never lands on a component-key pending item ──────────────

def test_bare_float_not_assigned_to_component_key_pending(tmp_path: Path):
    """Defense-in-depth: force ParamDefinitionSession.answer() into a state
    where pending[0] is a component key (mis-set reason), and prove a bare
    float is never zipped onto it as a value."""
    orch = _project_with_active_propulsion(tmp_path)
    session = InteractiveSessionState(
        mode=OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        step=0,
        pending_param_definitions=["propellers"],
        collected_params={},
        param_definition_reason="missing_propulsion_parameters",  # mis-set on purpose
    )
    orch.state_manager.set_runtime_session(session)

    result = orch.param_definition_session.answer("10")

    assert result["status"] == "interactive"
    session_after = orch.state_manager.get_runtime_session()
    assert "propellers" not in session_after.collected_params
    assert session_after.pending_param_definitions == ["propellers"]
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.current_parameters.get("propellers") is None


# ── F/G) FN-013/FN-015 regressions ──────────────────────────────────────────

def test_definir_propulsion_still_fn013(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)
    result = orch.handle_user_text("definir propulsión", _RefuseLLM())
    assert result.get("block_declaration_reprompt") is True
    assert result["action"] == "define_missing_params"


def test_ayudame_definir_still_fn015(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)
    result = orch.handle_user_text("ayudame a definir", _RefuseLLM())
    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert session.pending_param_definitions == ["propellers"]


# ── H) existing ESCAPE unchanged ────────────────────────────────────────────

def test_cancelar_still_escape(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)
    result = orch.handle_user_text("cancelar", _RefuseLLM())
    assert result["status"] == "cancelled"
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.IDLE


# ── I) IDLE "atrás" is a no-op, does not open acquisition ───────────────────

def test_idle_atras_does_not_open_acquisition(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)

    class _StubLLM:
        def interpret(self, *a, **kw):
            return {"action": "iterate", "parameters": {}, "raw_user_input": None}

        def analyze(self, *a, **kw):
            return "respuesta genérica"

        def generate(self, *a, **kw):
            return {}

    result = orch.handle_user_text("atrás", _StubLLM())
    session = orch.state_manager.get_runtime_session()
    assert session.mode != OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert result is not None  # no crash
