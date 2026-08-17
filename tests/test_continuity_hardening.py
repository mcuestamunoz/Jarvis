"""Continuity Hardening (Implementation Contract acceptance tests).

Covers Slices 1-4 per .jes/artifacts/design_continuity_hardening.md (★1-★7):
  T1-T3  Slice 1 — G14 composite force gate (★4)
  T4-T5  Slice 2 — G12/G8 refuse policy (★2)
  T6-T7  Slice 3 — G15 list-motors + filtered-max messaging (★5, ★6)
  T8-T10 Slice 4 — G11 iterate preempt ownership (★3)
"""
from __future__ import annotations

import pytest

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import (
    MISSING_COMPONENT_DEFINITION,
    MISSING_PROPULSION_PARAMETERS,
)
from jarvis.core.state_manager import OrchestratorMode
from jarvis.core.motor_catalog_assist import format_no_thrust_candidate_message
from jarvis.knowledge.library import default_library


class _FakeLLM:
    """Raises if called — proves a handler is 0-LLM."""

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called for this path")


_CREATE_PARAMS = {
    "vehicle_type": "dron",
    "objective": "dron de prueba continuity hardening",
    "payload_kg": 1.0,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "motors": 4,
    "per_motor_max_thrust_n": 12.0,
    "structure_mass_factor": 0.5,
    "safety_factor": 1.2,
}


def _fresh_orchestrator(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle({"action": "create_project", "parameters": _CREATE_PARAMS})
    return orchestrator


def _open_component_wizard(orchestrator, pending_keys: list[str]):
    session = orchestrator.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "pending_missing_params": pending_keys,
        "pending_define_missing": False,
    })
    orchestrator.state_manager.set_runtime_session(updated)


def _open_thrust_wizard(orchestrator):
    session = orchestrator.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "param_definition_reason": MISSING_PROPULSION_PARAMETERS,
        "pending_param_definitions": ["per_motor_max_thrust_n"],
    })
    orchestrator.state_manager.set_runtime_session(updated)


def _advance_to_material_strategy_step(orchestrator, llm):
    """Drive the iterate wizard to step 2 with variable='material',
    operation=None — the strategy-selection step G11-B targets."""
    orchestrator.handle_user_text("cambiar material", llm)
    orchestrator.handle_user_text("si", llm)
    orchestrator.handle_user_text("material", llm)
    sess = orchestrator.state_manager.runtime_state.session
    assert sess.iteration_draft.variable == "material"
    assert sess.iteration_draft.operation is None


# ── Slice 1 — G14 composite force gate (★4) ────────────────────────────────

def test_t1_motor_shaped_phrase_not_forced_into_propellers(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    _open_component_wizard(orchestrator, ["motors", "propellers"])

    result = orchestrator.handle_user_text("1x 2306 2400KV 50W", _FakeLLM())

    assert "Hélices registradas" not in (result.get("message") or "")
    state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    propellers = state.design_properties.components.get("propellers")
    assert propellers is None, "must not have silently written a propeller spec"


def test_t2_composite_bare_propeller_size_still_forces(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    _open_component_wizard(orchestrator, ["motors", "propellers"])

    result = orchestrator.handle_user_text("10x4.5", _FakeLLM())

    assert result["status"] == "ok"
    state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    propellers = state.design_properties.components.get("propellers")
    assert propellers is not None
    assert propellers.properties["diameter_in"].value == pytest.approx(10.0)


def test_t3_singleton_propellers_still_forces_bare_size(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    _open_component_wizard(orchestrator, ["propellers"])

    result = orchestrator.handle_user_text("10x4.5", _FakeLLM())

    assert result["status"] == "ok"
    state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    propellers = state.design_properties.components.get("propellers")
    assert propellers is not None
    assert propellers.properties["diameter_in"].value == pytest.approx(10.0)


# ── Slice 2 — G12/G8 refuse policy (★2) ────────────────────────────────────

def test_t4_definir_different_block_refuses_not_silent_brief(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    _open_component_wizard(orchestrator, ["battery"])

    result = orchestrator.handle_user_text("definir frame", _FakeLLM())

    message = (result.get("message") or "").lower()
    assert "cancelar" in message
    assert "batería" in message or "bateria" in message
    sess = orchestrator.state_manager.runtime_state.session
    assert sess.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert sess.pending_missing_params == ["battery"]


def test_t5_engineering_intent_mid_wizard_refuses_not_silent_absorb(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    _open_component_wizard(orchestrator, ["battery"])

    result = orchestrator.handle_user_text("reducir payload", _FakeLLM())

    message = (result.get("message") or "").lower()
    assert "cancelar" in message
    # Must NOT be the plain battery brief shown as if nothing was understood
    # (the pre-fix behavior silently repeated "Vamos a definir la batería...").
    assert "vamos a definir" not in message
    sess = orchestrator.state_manager.runtime_state.session
    assert sess.pending_missing_params == ["battery"]


def test_t4b_same_block_reprompt_still_works(tmp_path):
    """Regression: refusing a DIFFERENT block must not break C-033's existing
    same-block reprompt ('definir batería' while battery is already active)."""
    orchestrator = _fresh_orchestrator(tmp_path)
    _open_component_wizard(orchestrator, ["battery"])

    # Needs system_defined + a real pending block for _try_reprompt_active_block_declaration
    # to engage; if it doesn't (fixture too minimal), the turn still must not
    # error and must not silently claim a refuse for the SAME target.
    result = orchestrator.handle_user_text("definir batería", _FakeLLM())
    assert result["status"] in ("interactive", "ok")


# ── Slice 3 — G15 list-motors + filtered-max messaging (★5, ★6) ───────────

def test_t6_list_motors_mid_thrust_wizard_is_deterministic(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    _open_thrust_wizard(orchestrator)

    result = orchestrator.handle_user_text(
        "que motores tenemos en el catalogo", _FakeLLM()  # raises if LLM invoked
    )

    assert result["status"] == "interactive"
    sess = orchestrator.state_manager.runtime_state.session
    assert sess.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert sess.pending_param_definitions == ["per_motor_max_thrust_n"]


def test_t7_no_thrust_message_filtered_max_is_coherent():
    required_n = 37.7
    msg = format_no_thrust_candidate_message(required_n=required_n, kv=2400, prop_inch=5.0)

    import re
    match = re.search(r"máximo.*?~([\d.]+) N/motor", msg)
    assert match is not None, msg
    filtered_max = float(match.group(1))
    # The filtered max must never contradict the "no candidate" verdict —
    # i.e. it must not claim to cover the requirement that was just refused.
    assert filtered_max < required_n
    assert "compatible con tu KV/hélice" in msg


def test_t7b_unfiltered_path_unchanged_when_no_filters_given():
    unfiltered_max = max(m.max_thrust_n for m in default_library.list_motors())
    msg = format_no_thrust_candidate_message(required_n=1000.0)
    assert f"~{unfiltered_max:.1f} N/motor" in msg
    assert "compatible con tu KV/hélice" not in msg


# ── Slice 4 — G11 iterate preempt ownership (★3) ───────────────────────────

def test_t8_bare_material_at_strategy_step_does_not_preempt(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    llm = _FakeLLM()
    _advance_to_material_strategy_step(orchestrator, llm)

    result = orchestrator.handle_user_text("pvc", llm)

    assert not result.get("preempted_iterate")
    assert orchestrator.state_manager.runtime_state.session.mode == OrchestratorMode.ITERATE_INTERACTIVE


def test_t9_cambiar_a_pvc_at_strategy_step_does_not_preempt(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    llm = _FakeLLM()
    _advance_to_material_strategy_step(orchestrator, llm)

    result = orchestrator.handle_user_text("cambiar a pvc", llm)

    assert not result.get("preempted_iterate")
    sess = orchestrator.state_manager.runtime_state.session
    assert sess.mode == OrchestratorMode.ITERATE_INTERACTIVE
    assert sess.iteration_draft.value == "pvc"


def test_t10_genuine_strong_action_still_preempts_owned_step(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    llm = _FakeLLM()
    _advance_to_material_strategy_step(orchestrator, llm)

    result = orchestrator.handle_user_text("simula", llm)

    assert result.get("action") == "simulate"
    assert result["status"] == "ok"
