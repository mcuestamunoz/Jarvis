"""FN-014 — Acquisition Target Authority: unified block ∪ component mention
resolution for the IDLE acquisition gate.

Field-note case:
    IDLE, Continuity: "Propulsión en progreso — declara componentes (propellers
    pendiente)". User: "definir propellers". Before FN-014 this opened
    ITERATE_INTERACTIVE ("propiedad declarativa..."). Target: deterministic
    component acquisition, same bridge as FN-011/Bug54, 0 LLM.
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
    """Permissive stub for cases where reaching the LLM is allowed."""

    def interpret(self, *args, **kwargs):
        return {"action": "iterate", "parameters": {}, "raw_user_input": None}

    def analyze(self, *args, **kwargs):
        return "respuesta genérica"

    def generate(self, *args, **kwargs):
        return {}


def _project_with_active_propulsion(
    tmp_path: Path, *, components_done: bool = False, propellers_done: bool = False
) -> JarvisOrchestrator:
    """Aerial project, system_defined, propulsion first in system_priority.

    - default: Phase A, motors already declared, propellers pending.
    - components_done: Phase B, both components declared, only params pending.
    - propellers_done (with motors NOT declared): motors still the Phase A gap.
    """
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
    components: dict[str, ComponentSpec] = {}
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
    elif propellers_done:
        components = {"propellers": propellers_spec}
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


# ── A) "definir propellers" — the field-note case ──────────────────────────

def test_definir_propellers_opens_component_acquisition_no_llm(tmp_path: Path):
    """The exact field-note phrase: component key (not a block alias), must
    still open deterministic acquisition, not ITERATE_INTERACTIVE, 0 LLM."""
    orch = _project_with_active_propulsion(tmp_path)
    result = orch.handle_user_text("definir propellers", _RefuseLLM())

    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert session.mode != OrchestratorMode.ITERATE_INTERACTIVE
    assert "propellers" in session.pending_param_definitions


def test_definir_helices_alias_also_resolves_to_propellers(tmp_path: Path):
    """Spanish alias for the same component key."""
    orch = _project_with_active_propulsion(tmp_path)
    result = orch.handle_user_text("definir helices", _RefuseLLM())
    assert result["action"] == "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert "propellers" in session.pending_param_definitions


def test_definir_motores_when_motors_is_the_active_gap(tmp_path: Path):
    """Symmetric case: motors pending instead of propellers."""
    orch = _project_with_active_propulsion(tmp_path, propellers_done=True)
    result = orch.handle_user_text("definir motores", _RefuseLLM())
    assert result["action"] == "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert "motors" in session.pending_param_definitions


def test_component_already_declared_does_not_reopen_its_acquisition(tmp_path: Path):
    """A component that is NOT missing/low anymore must not be treated as the
    active gap (Phase-A 'still needed' criterion, same one _set_pending_next_block
    already uses). motors is the real pending gap here; naming the
    already-declared "propellers" must not fire the acquisition gate for it."""
    orch = _project_with_active_propulsion(tmp_path, propellers_done=True)
    result = orch.handle_user_text("definir propellers", _RefuseLLM())
    session = orch.state_manager.get_runtime_session()
    if result.get("action") == "define_missing_params":
        # If something DID claim it, it must have been for the real gap (motors),
        # never for the already-declared propellers.
        assert "propellers" not in session.pending_param_definitions
    else:
        assert session.mode != OrchestratorMode.DEFINE_MISSING_PARAMETERS


# ── B) "definir propulsión" — FN-011 regression via the new shared gate ────

def test_definir_propulsion_still_opens_acquisition(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    result = orch.handle_user_text("definir propulsión", _RefuseLLM())
    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert session.param_definition_reason == "missing_component_definition"


def test_ayudame_declarar_propulsion_still_works(tmp_path: Path):
    """FN-011 regression, exact original phrase."""
    orch = _project_with_active_propulsion(tmp_path)
    result = orch.handle_user_text("ayúdame a declarar propulsión", _RefuseLLM())
    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"


# ── C) wrong-block mention — must not silently jump ─────────────────────────

def test_definir_bateria_does_not_jump_while_propulsion_pending(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    result = orch.handle_user_text("definir batería", _RefuseLLM())

    assert result is not None
    assert result["status"] == "ok"
    assert result["action"] != "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.IDLE
    assert "propulsión" in (result.get("message") or "").lower()


def test_definir_energia_component_mention_does_not_jump(tmp_path: Path):
    """Same guard via a component-level mention (battery) that only belongs
    to a non-active block."""
    orch = _project_with_active_propulsion(tmp_path)
    result = orch.handle_user_text("definir battery", _RefuseLLM())
    assert result["status"] == "ok"
    assert result["action"] != "define_missing_params"
    assert orch.state_manager.get_runtime_session().mode == OrchestratorMode.IDLE


# ── D) legitimate iterate — no gap term mentioned ───────────────────────────

def test_definir_material_still_non_acquisition(tmp_path: Path):
    """'material' names neither a block nor a component key — must not claim
    acquisition. (Falls through to iterate or whatever existing routing
    handles it; this test only asserts acquisition was NOT claimed.)"""
    orch = _project_with_active_propulsion(tmp_path)
    result = orch.handle_user_text("definir material a carbono", _RefuseLLM())
    session = orch.state_manager.get_runtime_session()
    assert result.get("action") != "define_missing_params"
    assert session.mode != OrchestratorMode.DEFINE_MISSING_PARAMETERS or (
        session.pending_param_definitions == []
    )


# ── E) no architecture / no pending block — no false acquisition ───────────

def test_no_system_defined_no_false_acquisition(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "test", "payload_kg": 1.0,
            "restrictions": "ninguna", "detail_level": "conceptual",
            "structure_mass_factor": 0.6, "safety_factor": 1.2,
        },
    })
    result = orch.handle_user_text("definir propellers", _StubLLM())
    assert result.get("action") != "define_missing_params"


# ── G) "ayúdame a elegir el motor" — FN-005 unaffected ──────────────────────

def test_ayudame_elegir_motor_unaffected(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path, components_done=True)
    result = orch.handle_user_text("ayúdame a elegir el motor", _RefuseLLM())
    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert session.param_definition_reason == MISSING_PROPULSION_PARAMETERS
    assert result.get("motor_suggestions") is not None
