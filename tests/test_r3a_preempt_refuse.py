"""R3a Preempt Refuse — acceptance tests.

Slice 1: ★2 refuse ported to numeric sub-mode.
Slice 2: explore_design_space as soft-interrupt in both sub-modes.
"""
from __future__ import annotations

import pytest

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import (
    MISSING_COMPONENT_DEFINITION,
    MISSING_PROPULSION_PARAMETERS,
)
from jarvis.core.state_manager import OrchestratorMode
from jarvis.schemas.action_schema import HandoffContext


class _FakeLLM:
    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called for this path")


_CREATE_PARAMS = {
    "vehicle_type": "dron",
    "objective": "dron de prueba R3a",
    "payload_kg": 1.0,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "motors": 4,
    "per_motor_max_thrust_n": 12.0,
    "structure_mass_factor": 0.5,
    "safety_factor": 1.2,
}


def _fresh(tmp_path):
    o = JarvisOrchestrator(workspace_root=tmp_path)
    o.handle({"action": "create_project", "parameters": _CREATE_PARAMS})
    return o


def _open_numeric_wizard(o, pending=None, reason=MISSING_PROPULSION_PARAMETERS):
    pending = pending or ["per_motor_max_thrust_n"]
    session = o.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "param_definition_reason": reason,
        "pending_param_definitions": pending,
    })
    o.state_manager.set_runtime_session(updated)


def _open_component_wizard(o, pending_keys):
    session = o.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "pending_missing_params": pending_keys,
        "pending_define_missing": False,
    })
    o.state_manager.set_runtime_session(updated)


# ── Slice 1: ★2 refuse ported to numeric sub-mode ───────────────────────────


def test_r3a_numeric_submode_engineering_intent_refuses_honestly(tmp_path):
    o = _fresh(tmp_path)
    _open_numeric_wizard(o)

    result = o.handle_user_text("reducir payload", _FakeLLM())

    msg = result.get("message", "")
    assert "cancelar" in msg.lower()
    assert "No reconozco" not in msg
    assert "propulsión" in msg


def test_r3a_numeric_submode_explore_refuses_honestly(tmp_path):
    o = _fresh(tmp_path)
    _open_numeric_wizard(o)

    result = o.handle_user_text("explora opciones", _FakeLLM())

    msg = result.get("message", "")
    assert "cancelar" in msg.lower()
    assert "No reconozco" not in msg


def test_r3a_numeric_submode_different_block_refuses_honestly(tmp_path):
    """'definir batería' while in a propulsion numeric wizard gets the
    different-block refusal, not the engineering-intent one — even though
    'definir batería' ALSO triggers is_engineering_intention (matches
    mejorar_autonomia's own keyword list). _maybe_refuse_numeric_submode
    checks resolve_declare_block_request FIRST, exactly matching ★2's own
    _maybe_refuse_different_target ordering (component sub-mode) — checking
    engineering-intent first would misfire here and never reach the correct
    'quieres pasar a definir la energía' message."""
    o = _fresh(tmp_path)
    _open_numeric_wizard(o)

    result = o.handle_user_text("definir batería", _FakeLLM())

    msg = result.get("message", "")
    assert "cancelar" in msg.lower()
    assert "No reconozco" not in msg
    assert "propulsión" in msg
    assert "energía" in msg
    assert "explorar" not in msg.lower()


def test_r3a_numeric_submode_pure_block_declare_refuses_honestly(tmp_path):
    """'declarar estructura' — only triggers resolve_declare_block_request,
    NOT is_engineering_intention. Exercises the block-declare branch."""
    o = _fresh(tmp_path)
    _open_numeric_wizard(o)

    result = o.handle_user_text("declarar estructura", _FakeLLM())

    msg = result.get("message", "")
    assert "cancelar" in msg.lower()
    assert "No reconozco" not in msg
    assert "estructura" in msg


def test_r3a_numeric_submode_transmission_reason_has_real_label(tmp_path):
    """missing_transmission_parameters (terrestrial: torque/rueda/gear) must
    resolve to a real Spanish label, not the raw reason string leaking into
    the user-facing refusal."""
    o = _fresh(tmp_path)
    _open_numeric_wizard(
        o, pending=["per_actuator_torque_nm"], reason="missing_transmission_parameters",
    )

    result = o.handle_user_text("reducir payload", _FakeLLM())

    msg = result.get("message", "")
    assert "cancelar" in msg.lower()
    assert "missing_transmission_parameters" not in msg
    assert "transmisión" in msg


def test_r3a_numeric_submode_real_value_still_works(tmp_path):
    o = _fresh(tmp_path)
    _open_numeric_wizard(o)

    result = o.handle_user_text("12.0", _FakeLLM())

    assert result.get("status") in ("ok", "interactive")
    msg = result.get("message", "")
    assert "No reconozco" not in msg


def test_r3a_component_submode_refuse_unchanged(tmp_path):
    o = _fresh(tmp_path)
    _open_component_wizard(o, ["motors", "propellers"])

    result = o.handle_user_text("reducir payload", _FakeLLM())

    msg = result.get("message", "")
    assert "cancelar" in msg.lower()
    assert "los motores" in msg


# ── Slice 2: explore_design_space as soft-interrupt ──────────────────────────


def test_r3a_explore_soft_interrupt_component_submode(tmp_path):
    o = _fresh(tmp_path)
    _open_component_wizard(o, ["motors"])
    project = o.state_manager.load_active_project(o.workspace_manager)
    session = o.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "handoff_context": HandoffContext(
            goal_key="mejorar_autonomia",
            levers=["battery_capacity_wh"],
            dse_capability="active",
            project_id=project.project_id,
        ),
    })
    o.state_manager.set_runtime_session(updated)

    result = o.handle_user_text("explora opciones", _FakeLLM())

    assert result.get("action") == "explore_design_space"
    assert "wizard_reprompt" in result
    sess_after = o.state_manager.runtime_state.session
    assert sess_after.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS


def test_r3a_explore_soft_interrupt_numeric_submode(tmp_path):
    o = _fresh(tmp_path)
    _open_numeric_wizard(o)
    project = o.state_manager.load_active_project(o.workspace_manager)
    session = o.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "handoff_context": HandoffContext(
            goal_key="mejorar_autonomia",
            levers=["battery_capacity_wh"],
            dse_capability="active",
            project_id=project.project_id,
        ),
    })
    o.state_manager.set_runtime_session(updated)

    result = o.handle_user_text("optimiza para autonomía", _FakeLLM())

    assert result.get("action") == "explore_design_space"
    assert "wizard_reprompt" in result
    sess_after = o.state_manager.runtime_state.session
    assert sess_after.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS


def test_r3a_explore_soft_interrupt_reprompt_uses_component_prompts(tmp_path):
    """wizard_reprompt in component sub-mode must reuse the established
    _COMPONENT_PROMPTS/_component_prompt_for_first_missing text (FN-017/018
    discipline — never a hand-rolled generic string), same as ITERATE's own
    get_current_prompt reuses its wizard's real question machinery."""
    from jarvis.core.orchestrator import _COMPONENT_PROMPTS

    o = _fresh(tmp_path)
    _open_component_wizard(o, ["motors"])
    project = o.state_manager.load_active_project(o.workspace_manager)
    session = o.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "handoff_context": HandoffContext(
            goal_key="mejorar_autonomia",
            levers=["battery_capacity_wh"],
            dse_capability="active",
            project_id=project.project_id,
        ),
    })
    o.state_manager.set_runtime_session(updated)

    result = o.handle_user_text("explora opciones", _FakeLLM())

    assert result["wizard_reprompt"] == _COMPONENT_PROMPTS["motors"]


def test_r3a_explore_no_goal_falls_through(tmp_path):
    o = _fresh(tmp_path)
    _open_numeric_wizard(o)

    result = o.handle_user_text("explora opciones", _FakeLLM())

    msg = result.get("message", "")
    assert "cancelar" in msg.lower()
    assert result.get("action") != "explore_design_space"
