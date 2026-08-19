"""CLI Routing Residuals (G17 / G14 / G13) — Implementation Contract acceptance tests.

Covers .jes/artifacts/implementation_contract_cli_routing_residuals.md:
  Slice 1 — G17: bare motor phrase at IDLE routes deterministically, 0 LLM
  Slice 2 — G14: bare propeller size at IDLE routes deterministically, 0 LLM
  Slice 3 — G13: CLI-level (orchestrator) integration test for iterate
            material compound slug ("PVC 400g")
"""
from __future__ import annotations

from jarvis.core.orchestrator import JarvisOrchestrator


class _RefuseLLM:
    """Raises if called in any way — proves a handler is 0-LLM."""

    def generate(self, *a, **kw):
        raise AssertionError("LLM.generate must not be called")

    def interpret(self, *a, **kw):
        raise AssertionError("LLM.interpret must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM.analyze must not be called")


_CREATE_PARAMS = {
    "vehicle_type": "dron",
    "objective": "dron de prueba cli routing residuals",
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


# ── Slice 1 — G17: bare motor phrase at IDLE ───────────────────────────────

def test_g17_bare_motor_idle_intercept(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)

    result = orchestrator.handle_user_text("4x 2306 1400kv", _RefuseLLM())

    assert result["status"] == "ok"
    assert result["action"] == "component_description_saved"
    assert "Motores registrados" in (result.get("message") or "")
    state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    motors = state.design_properties.components.get("motors")
    assert motors is not None
    assert motors.properties["motor_count"].value == 4
    assert motors.properties["kv_rating"].value == 1400.0


def test_g17_motors_already_defined_does_not_force_overwrite(tmp_path):
    """★5: never force-bind when the component is already fully defined."""
    orchestrator = _fresh_orchestrator(tmp_path)
    orchestrator.handle_user_text("4x 2306 1400kv", _RefuseLLM())
    state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert state.design_properties.components.get("motors") is not None

    forced = orchestrator._force_component_spec_idle("6x 2807 1900kv")
    assert forced is None


# ── Slice 2 — G14: bare propeller size at IDLE ─────────────────────────────

def test_g14_bare_propeller_idle_intercept(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)

    result = orchestrator.handle_user_text("10x4.5", _RefuseLLM())

    assert result["status"] == "ok"
    assert result["action"] == "component_description_saved"
    assert "Hélices registradas" in (result.get("message") or "")
    state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    propellers = state.design_properties.components.get("propellers")
    assert propellers is not None
    assert propellers.properties["diameter_in"].value == 10.0


def test_g14_motor_shaped_phrase_still_prefers_motors_not_propellers(tmp_path):
    """Regression guard mirroring G14's own original fix: a motor-shaped
    phrase (has a kv marker) at IDLE must never be captured by the
    propellers force, even though its "NxP"-looking substring also parses."""
    orchestrator = _fresh_orchestrator(tmp_path)

    result = orchestrator.handle_user_text("4x 2306 1400kv", _RefuseLLM())

    assert "Hélices registradas" not in (result.get("message") or "")
    state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert state.design_properties.components.get("propellers") is None
    assert state.design_properties.components.get("motors") is not None


# ── Slice 3 — G13: CLI-level iterate material compound slug ────────────────

def test_g13_iterate_material_compound_cli_path(tmp_path):
    """Full orchestrator path: IDLE -> iterate wizard -> material strategy
    step -> compound slug "PVC 400g" -> extraction + impact estimate.
    0 LLM throughout (mirrors _advance_to_material_strategy_step from
    test_continuity_hardening.py, driven via handle_user_text like a real
    CLI session)."""
    orchestrator = _fresh_orchestrator(tmp_path)
    llm = _RefuseLLM()

    start = orchestrator.handle_user_text("cambiar material", llm)
    assert start["status"] == "interactive"

    confirm = orchestrator.handle_user_text("si", llm)
    assert confirm["step"] == 1

    strategy = orchestrator.handle_user_text("material", llm)
    assert strategy["step"] == 2
    session = orchestrator.state_manager.runtime_state.session
    assert session.iteration_draft.variable == "material"
    assert session.iteration_draft.operation is None

    named = orchestrator.handle_user_text("PVC 400g", llm)
    assert named["step"] == 3
    session2 = orchestrator.state_manager.runtime_state.session
    assert session2.iteration_draft.value == "pvc"

    impact = orchestrator.handle_user_text("ninguna", llm)
    assert impact["step"] == 4
    assert "-12.2%" in impact["message"]
    assert "pvc" in impact["message"].lower()
    assert "no tengo datos físicos" not in impact["message"].lower()
