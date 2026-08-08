"""FN-011 — Propulsion declaration bypasses deterministic acquisition.

Regression coverage for the leak where an explicit "ayúdame a declarar/completar
Propulsión" fell through to the LLM even though the project state already knows
the real next acquisition gap for that block.
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import MISSING_PROPULSION_PARAMETERS
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue


class _RefuseLLM:
    """Stub that fails loudly if the LLM is invoked in any way."""

    def interpret(self, *args, **kwargs):
        raise AssertionError("LLM.interpret must not be called")

    def analyze(self, *args, **kwargs):
        raise AssertionError("LLM.analyze must not be called")

    def generate(self, *args, **kwargs):
        raise AssertionError("LLM.generate must not be called")


class _StubLLM:
    """Permissive stub for cases where reaching the LLM is expected/allowed."""

    def interpret(self, *args, **kwargs):
        return {"action": "iterate", "parameters": {}, "raw_user_input": None}

    def analyze(self, *args, **kwargs):
        return "respuesta genérica del LLM"

    def generate(self, *args, **kwargs):
        return {}


def _project_with_active_propulsion(
    tmp_path: Path, *, components_done: bool = False
) -> JarvisOrchestrator:
    """Aerial project with system architecture defined and Propulsión as the
    first pending block in system_priority (Phase A: components missing, or
    Phase B when components_done=True: only params missing)."""
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
    if components_done:
        components = {
            "motors": ComponentSpec(
                name="4 motores 920kv",
                component_type="propulsion_active",
                suggested_key="motors",
                completeness="high",
                source="declared",
                properties={
                    "motor_count": PropertyValue(value=4),
                    "kv_rating": PropertyValue(value=920),
                },
            ),
            "propellers": ComponentSpec(
                name="helices 10x4.5",
                component_type="propulsion_passive",
                suggested_key="propellers",
                completeness="high",
                source="declared",
                properties={"diameter_in": PropertyValue(value=10.0)},
            ),
        }
    dp = ps.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure", "control"],
        "system_priority": ["propulsion", "energy", "structure", "control"],
        "components": components,
    })
    orch.workspace_manager.save_state(ps.model_copy(update={"design_properties": dp}))
    return orch


# ── A) explicit declare request → deterministic route, 0 LLM calls ────────────

def test_declare_propulsion_routes_deterministically_no_llm(tmp_path: Path):
    """The exact field-note phrase must never reach the LLM and must open the
    deterministic component-acquisition wizard for the real Phase-A gap."""
    orch = _project_with_active_propulsion(tmp_path)
    result = orch.handle_user_text("ayúdame a declarar propulsión", _RefuseLLM())
    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert session.param_definition_reason == "missing_component_definition"
    assert session.pending_param_definitions == ["motors", "propellers"]


def test_declare_propulsion_phase_b_surfaces_real_propulsion_params_only(tmp_path: Path):
    """Once components are already defined, the same phrase must surface
    Propulsión's real remaining param gap (motor_count/per_motor_max_thrust_n)
    — never energy, torque, actuator, or any other block's parameters."""
    orch = _project_with_active_propulsion(tmp_path, components_done=True)
    result = orch.handle_user_text("ayúdame a declarar propulsión", _RefuseLLM())
    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert session.param_definition_reason == MISSING_PROPULSION_PARAMETERS
    assert set(session.pending_param_definitions) == {"motor_count", "per_motor_max_thrust_n"}
    joined = " ".join(session.pending_param_definitions).lower()
    assert "battery" not in joined
    assert "torque" not in joined
    assert "actuator" not in joined


def test_completar_propulsion_also_routes_deterministically(tmp_path: Path):
    """'completar' is an equally valid declare-verb once a block is named."""
    orch = _project_with_active_propulsion(tmp_path)
    result = orch.handle_user_text("ayúdame a completar propulsión", _RefuseLLM())
    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"


# ── B) bare "ayúdame a completar" (no block) → existing Continuity route ──────

def test_bare_ayudame_a_completar_keeps_existing_route(tmp_path: Path):
    """Regression: with no block explicitly named, behavior is unchanged —
    routes to project_status / Continuity, not the new block-declare bridge."""
    orch = _project_with_active_propulsion(tmp_path)
    result = orch.handle_user_text("ayúdame a completar", _RefuseLLM())
    assert result["status"] == "ok"
    assert result["action"] == "project_status"
    session = orch.state_manager.get_runtime_session()
    assert session.mode.value != "define_missing_params"


# ── C) "ayúdame a elegir el motor" → catalog determinista (sin cambios) ───────

def test_ayudame_a_elegir_el_motor_still_opens_catalog(tmp_path: Path):
    """Regression: the motor-catalog assisted flow (FN-005/FN-009) must be
    completely unaffected by the new block-declare intercept."""
    orch = _project_with_active_propulsion(tmp_path, components_done=True)
    result = orch.handle_user_text("ayúdame a elegir el motor", _RefuseLLM())
    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert session.param_definition_reason == MISSING_PROPULSION_PARAMETERS
    assert result.get("motor_suggestions") is not None


# ── D) ambiguous / unrelated to the active block → not auto-converted ─────────

def test_unrelated_ambiguous_phrase_not_converted_to_acquisition(tmp_path: Path):
    """A phrase with no declare-verb + block match must not open any wizard —
    it keeps falling through to its existing routing (LLM allowed here)."""
    orch = _project_with_active_propulsion(tmp_path)
    result = orch.handle_user_text("ayúdame a decidir qué colores usar", _StubLLM())
    session = orch.state_manager.get_runtime_session()
    assert session.mode.value != "define_missing_params"
    assert result.get("action") != "define_missing_params"


def test_declare_other_block_while_propulsion_is_active_not_auto_converted(tmp_path: Path):
    """'ayúdame a declarar energía' while Propulsión (not energía) is the real
    active/pending block must NOT jump to energía or invent its params —
    the named block must match the actual current gap."""
    orch = _project_with_active_propulsion(tmp_path)
    result = orch.handle_user_text("ayúdame a declarar energía", _StubLLM())
    session = orch.state_manager.get_runtime_session()
    assert session.mode.value != "define_missing_params"
    assert result.get("action") != "define_missing_params"
