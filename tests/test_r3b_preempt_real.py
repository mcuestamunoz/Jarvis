"""R3b Real Preempt — acceptance tests.

Slice 1: preempt detector + component sub-mode clear-and-redispatch.
Slice 2: numeric sub-mode partial-apply-then-preempt.
"""
from __future__ import annotations

import pytest

from jarvis.core.design_explorer import ExplorationCandidate, ExplorationResult
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import (
    MISSING_COMPONENT_DEFINITION,
    MISSING_PROPULSION_PARAMETERS,
)
from jarvis.core.state_manager import OrchestratorMode
from jarvis.schemas.tool_schema import CalculationBundle, SimulationAnalysis, SimulationResult


class _FakeLLM:
    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called for this path")

    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called for this path")


_CREATE_PARAMS = {
    "vehicle_type": "dron",
    "objective": "dron de prueba R3b",
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


def _open_numeric_wizard(o, pending=None, reason=MISSING_PROPULSION_PARAMETERS, collected=None):
    pending = pending or ["per_motor_max_thrust_n"]
    session = o.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "param_definition_reason": reason,
        "pending_param_definitions": pending,
        "collected_params": collected or {},
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


def _make_calc(*, total_mass_kg: float = 3.5) -> CalculationBundle:
    return CalculationBundle(
        vehicle_type="dron", payload_kg=2.0, structure_mass_kg=1.5,
        total_mass_kg=total_mass_kg, weight_n=total_mass_kg * 9.81,
        required_thrust_n=total_mass_kg * 9.81 * 1.2, motors=4,
        thrust_per_motor_required_n=(total_mass_kg * 9.81 * 1.2) / 4,
        available_total_thrust_n=60.0, autonomy_min=30.0, tool_results=[],
    )


def _make_sim(*, safety_margin_ratio: float = 1.5) -> SimulationResult:
    return SimulationResult(
        can_fly=True,
        status="pass",
        safety_margin_ratio=safety_margin_ratio,
        thrust_to_weight_ratio=safety_margin_ratio,
        autonomy_min=30.0,
        quality="good",
        warnings=[],
        analysis=SimulationAnalysis(
            available_thrust_n=60.0, required_thrust_n=40.0, weight_n=34.3,
            per_motor_load_ratio=0.25,
        ),
        summary="ok",
    )


def _seed_exploration_result(o):
    """Safe params-only candidate — touches payload_kg only, never motors/energy."""
    exploration = ExplorationResult(
        goal_key="aumentar_payload",
        goal_label="maximizar carga útil",
        baseline_score=1.0,
        baseline_calculations=_make_calc(),
        baseline_simulation=_make_sim(),
        candidates=[],
        viable=[
            ExplorationCandidate(
                params_delta={"payload_kg_value": 1.2},
                components_delta={},
                calculations=_make_calc(total_mass_kg=4.0),
                simulation=_make_sim(safety_margin_ratio=1.8),
                score=2.0,
                label="payload=1.2kg",
                improvement=1.0,
            )
        ],
    )
    session = o.state_manager.get_runtime_session()
    o.state_manager.set_runtime_session(
        session.model_copy(update={"last_exploration_result": exploration})
    )


# ── Slice 1: component sub-mode clear-and-redispatch ────────────────────────


def test_r3b_component_submode_apply_exploration_preempts(tmp_path):
    o = _fresh(tmp_path)
    _open_component_wizard(o, ["motors"])
    _seed_exploration_result(o)

    result = o.handle_user_text("aplica la mejor", _FakeLLM())

    assert result.get("preempted_define_missing") is True
    assert result.get("action") == "apply_exploration_result"
    assert result.get("status") == "ok"
    assert "he cerrado la definición" in result.get("message", "").lower()


def test_r3b_component_submode_bare_iterate_preempts(tmp_path):
    o = _fresh(tmp_path)
    _open_component_wizard(o, ["motors"])

    result = o.handle_user_text("itera material del frame", _FakeLLM())

    assert result.get("preempted_define_missing") is True
    assert result.get("action") != "component_description_prompt"
    session = o.state_manager.runtime_state.session
    assert session.mode == OrchestratorMode.ITERATE_INTERACTIVE


def test_r3b_component_submode_dismiss_preempts(tmp_path):
    o = _fresh(tmp_path)
    _open_component_wizard(o, ["motors"])

    result = o.handle_user_text("descartar sugerencia", _FakeLLM())

    assert result.get("preempted_define_missing") is True
    assert result.get("action") == "project_status"
    session = o.state_manager.runtime_state.session
    assert session.mode == OrchestratorMode.IDLE


def test_r3b_component_submode_create_project_preempts(tmp_path):
    # "nuevo proyecto" (exact phrase) is caught earlier by the global "n"/"nuevo"
    # creation shortcut (_handle_global_commands, config.NEW_PROJECT_WORDS) —
    # a separate, pre-existing mechanism that already starts create_project
    # before this gate ever runs. Use a phrase that resolves to the same
    # create_project strong intent WITHOUT matching that exact-string shortcut,
    # so this test actually exercises the R3b preempt path.
    o = _fresh(tmp_path)
    _open_component_wizard(o, ["motors"])

    result = o.handle_user_text("quiero crear un proyecto nuevo", _FakeLLM())

    assert result.get("preempted_define_missing") is True
    session = o.state_manager.runtime_state.session
    assert session.mode == OrchestratorMode.CREATE_PROJECT_INTERACTIVE


def test_r3b_component_submode_real_component_description_not_preempted(tmp_path):
    o = _fresh(tmp_path)
    _open_component_wizard(o, ["motors"])

    result = o.handle_user_text("4x 2306 2400KV 50W", _FakeLLM())

    assert result.get("preempted_define_missing") is not True


# ── Slice 2: numeric sub-mode partial-apply-then-preempt ────────────────────


def test_r3b_numeric_submode_preempt_with_empty_collected_params(tmp_path):
    o = _fresh(tmp_path)
    _open_numeric_wizard(o)
    _seed_exploration_result(o)

    result = o.handle_user_text("aplica la mejor", _FakeLLM())

    assert result.get("preempted_define_missing") is True
    assert result.get("action") == "apply_exploration_result"
    assert result.get("status") == "ok"
    assert "se aplicaron los parámetros" not in result.get("message", "").lower()


def test_r3b_numeric_submode_preempt_partial_apply_then_preempt(tmp_path):
    o = _fresh(tmp_path)
    _open_numeric_wizard(
        o,
        pending=["per_motor_max_thrust_n"],
        collected={"structure_mass_factor": 0.7},
    )

    result = o.handle_user_text("itera material del frame", _FakeLLM())

    assert result.get("preempted_define_missing") is True
    assert "se aplicaron los parámetros" in result.get("message", "").lower()
    saved = o.state_manager.load_active_project(o.workspace_manager)
    assert saved.current_parameters["structure_mass_factor"] == pytest.approx(0.7)
    session = o.state_manager.runtime_state.session
    assert session.mode == OrchestratorMode.ITERATE_INTERACTIVE


def test_r3b_numeric_submode_preempt_aborts_on_structural_confirm(tmp_path):
    o = _fresh(tmp_path)
    _open_numeric_wizard(
        o,
        pending=["per_motor_max_thrust_n"],
        collected={"motor_count": 6},
    )

    result = o.handle_user_text("itera material del frame", _FakeLLM())

    assert result.get("preempted_define_missing") is not True
    assert result.get("action") == "structural_confirm"
    assert result.get("status") == "interactive"

    session = o.state_manager.runtime_state.session
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert session.pending_param_definitions == ["per_motor_max_thrust_n"]
    assert session.collected_params == {"motor_count": 6}
    assert session.pending_structural_change is not None


def test_r3b_numeric_submode_real_value_not_preempted(tmp_path):
    o = _fresh(tmp_path)
    _open_numeric_wizard(o)

    result = o.handle_user_text("12.0", _FakeLLM())

    assert result.get("preempted_define_missing") is not True
    assert result.get("status") in ("ok", "interactive")


def test_r3b_component_submode_preserves_saved_components_after_preempt(tmp_path):
    """★ contract rule: components already written to design_properties.components
    must never be reverted by a preempt. Saves 'motors' via the normal wizard
    turn, then the session's own pending list goes stale (FN-016 scenario) and
    still names it — the saved component must survive a preempt untouched."""
    o = _fresh(tmp_path)
    _open_component_wizard(o, ["motors", "propellers"])
    saved = o.handle_user_text("4x 2306 2400KV 50W", _FakeLLM())
    assert saved.get("preempted_define_missing") is not True

    before = o.state_manager.load_active_project(o.workspace_manager)
    assert before.design_properties.components.get("motors") is not None

    # Simulate FN-016 staleness: session still lists "motors" as pending.
    _open_component_wizard(o, ["motors", "propellers"])

    result = o.handle_user_text("descartar sugerencia", _FakeLLM())
    assert result.get("preempted_define_missing") is True

    after = o.state_manager.load_active_project(o.workspace_manager)
    assert after.design_properties.components.get("motors") is not None
    assert after.design_properties.components["motors"].completeness != "low"
