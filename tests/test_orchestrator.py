import json
from pathlib import Path

import pytest

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import OrchestratorMode


def test_create_project_flow_creates_workspace_and_artifacts(tmp_path: Path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)

    result = orchestrator.handle(
        {
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "dron que levante 2kg",
                "payload_kg": 2.0,
                "restrictions": "sin restricciones adicionales",
                "detail_level": "conceptual",
                "motors": 4,
                "per_motor_max_thrust_n": 15.0,
                "structure_mass_factor": 0.6,
                "safety_factor": 1.2,
            },
        }
    )

    workspace_path = Path(result["workspace_path"])
    assert result["status"] == "ok"
    assert workspace_path.exists()
    assert (workspace_path / "views" / "objetivo.md").exists()
    assert (workspace_path / "views" / "sistema.md").exists()
    assert (workspace_path / "history" / "simulations" / "sim_000.json").exists()
    assert (workspace_path / "history" / "iterations" / "iter_000.json").exists()
    assert (workspace_path / "history" / "events.jsonl").exists()

    state = json.loads((workspace_path / "state.json").read_text(encoding="utf-8"))
    assert state["active_iteration"] == 1
    assert state["history"][0]["action"] == "create_project"
    assert state["latest_results"]["simulation"]["status"] == "pass"


def test_interactive_create_project_requires_confirmation_before_execution(tmp_path: Path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)

    start = orchestrator.handle({"action": "create_project", "parameters": {}})
    assert start["status"] == "interactive"
    assert start["mode"] == "create_project_interactive"
    assert start["step"] == 0
    assert "¿Qué sistema quieres diseñar?" in start["question"]
    assert list(tmp_path.iterdir()) == []

    answer_1 = orchestrator.handle({"action": "create_project", "raw_user_input": "dron"})
    assert answer_1["step"] == 1

    answer_2 = orchestrator.handle(
        {"action": "create_project", "raw_user_input": "levantar 2kg"}
    )
    assert answer_2["step"] == 2

    answer_3 = orchestrator.handle({"action": "create_project", "raw_user_input": "2"})
    assert answer_3["step"] == 3

    answer_4 = orchestrator.handle(
        {"action": "create_project", "raw_user_input": "autonomía mínima de 20 minutos"}
    )
    assert answer_4["step"] == 4

    answer_5 = orchestrator.handle({"action": "create_project", "raw_user_input": "conceptual"})
    assert answer_5["step"] == 10  # aerial motors branch
    assert "motores" in answer_5["question"].lower()

    answer_motors = orchestrator.handle({"action": "create_project", "raw_user_input": "4"})
    assert answer_motors["step"] == 11

    answer_path = orchestrator.handle({"action": "create_project", "raw_user_input": "no sé"})
    assert answer_path["step"] == 90
    assert answer_path["question"] == "¿Confirmas?"
    assert "motores=" in answer_path["message"]
    assert list(tmp_path.iterdir()) == []

    result = orchestrator.handle({"action": "create_project", "raw_user_input": "sí"})
    # After confirmation, system_definition_session is launched (interactive)
    assert result["status"] == "interactive"
    assert result["mode"] == "system_definition"
    # Project was already persisted — verify via state_manager before answering the session
    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    workspace_path = Path(saved.workspace_path)
    assert workspace_path.exists()
    assert saved.current_parameters["detail_level"] == "conceptual"
    assert saved.current_parameters["restrictions"] == "autonomía mínima de 20 minutos"
    # Skip architecture definition to close the session
    skip_result = orchestrator.system_definition_session.answer("c")
    assert skip_result["status"] == "ok"


def test_interactive_create_project_accepts_payload_with_units(tmp_path: Path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)

    start = orchestrator.handle({"action": "create_project", "parameters": {"vehicle_type": "dron"}})
    assert start["step"] == 1

    answer_1 = orchestrator.handle({"action": "create_project", "raw_user_input": "levantar 2kg"})
    assert answer_1["step"] == 2

    answer_2 = orchestrator.handle({"action": "create_project", "raw_user_input": "2 Kg"})
    assert answer_2["step"] == 3
    assert answer_2["project_draft"]["payload_kg"] == 2.0


def test_interactive_iterate_flow_is_managed_by_orchestrator(tmp_path: Path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    project = orchestrator.handle(
        {
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "dron que levante 2kg",
                "payload_kg": 2.0,
                "restrictions": "sin restricciones adicionales",
                "detail_level": "conceptual",
                "motors": 4,
                "per_motor_max_thrust_n": 15.0,
                "structure_mass_factor": 0.6,
                "safety_factor": 1.2,
            },
        }
    )

    start = orchestrator.handle(
        {
            "action": "iterate",
            "parameters": {
                "objetivo": "peso",
                "operacion": "reducir",
            },
        }
    )
    assert start["status"] == "interactive"
    assert start["mode"] == "iterate_interactive"
    assert start["step"] == 0
    assert project["project_id"] in start["message"]
    assert "Quieres reducir peso" in start["message"]

    step_1 = orchestrator.handle({"action": "iterate", "raw_user_input": "sí"})
    assert step_1["step"] == 1

    step_2 = orchestrator.handle({"action": "iterate", "raw_user_input": "material"})
    assert step_2["step"] == 2

    step_3 = orchestrator.handle({"action": "iterate", "raw_user_input": "cambiar material"})
    # Gap 1: "cambiar material" doesn't include a material name → stays at step 2
    assert step_3["step"] == 2

    step_3b = orchestrator.handle({"action": "iterate", "raw_user_input": "fibra de carbono"})
    assert step_3b["step"] == 3

    step_4 = orchestrator.handle({"action": "iterate", "raw_user_input": "ninguna"})
    assert step_4["step"] == 4
    assert "impacto en empuje: positivo" in step_4["message"]

    step_5 = orchestrator.handle({"action": "iterate", "raw_user_input": "sí"})
    assert step_5["step"] == 5
    assert step_5["question"] == "¿Confirmas la iteración?"

    result = orchestrator.handle({"action": "iterate", "raw_user_input": "sí"})
    workspace_path = Path(result["workspace_path"])
    assert result["status"] == "ok"
    assert result["action"] == "iterate"
    assert result["iteration_draft"]["variable"] == "material"
    assert result["project_id"] == project["project_id"]
    assert result["state"]["active_iteration"] == 2
    # aluminio(2700)→fibra_de_carbono(1600), structural_fraction=0.25:
    # m_new = 3.2*0.75 + 3.2*0.25*(1600/2700) = 2.8741
    assert result["mutation"]["state_patch"]["masa_total"] == 2.8741
    assert result["simulation"]["status"] == "pass"
    assert (workspace_path / "history" / "iterations" / "iter_001.json").exists()


def test_iterate_requires_existing_project_context(tmp_path: Path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)

    result = orchestrator.handle(
        {
            "action": "iterate",
            "parameters": {
                "objetivo": "peso",
                "operacion": "reducir",
            },
        }
    )

    assert result["status"] == "error"
    assert "No hay proyectos creados" in result["message"]


def test_calculate_uses_persisted_project_state(tmp_path: Path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    project = orchestrator.handle(
        {
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "dron que levante 2kg",
                "payload_kg": 2.0,
                "restrictions": "sin restricciones adicionales",
                "detail_level": "conceptual",
                "motors": 4,
                "per_motor_max_thrust_n": 15.0,
                "structure_mass_factor": 0.6,
                "safety_factor": 1.2,
            },
        }
    )

    result = orchestrator.handle({"action": "calculate", "parameters": {"project_id": project["project_id"]}})

    workspace_path = Path(result["workspace_path"])
    assert result["status"] == "ok"
    assert result["action"] == "calculate"
    assert result["project_id"] == project["project_id"]
    assert result["calculations"]["total_mass_kg"] == 3.2
    assert result["state"]["active_iteration"] == 1
    assert result["state"]["history"][-1]["action"] == "calculate"
    assert (workspace_path / "history" / "calculations" / "calc_001.json").exists()


def test_simulate_reuses_persisted_state_and_stored_calculations(tmp_path: Path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    project = orchestrator.handle(
        {
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "dron que levante 2kg",
                "payload_kg": 2.0,
                "restrictions": "sin restricciones adicionales",
                "detail_level": "conceptual",
                "motors": 4,
                "per_motor_max_thrust_n": 15.0,
                "structure_mass_factor": 0.6,
                "safety_factor": 1.2,
            },
        }
    )

    result = orchestrator.handle({"action": "simulate", "parameters": {"project_id": project["project_id"]}})

    workspace_path = Path(result["workspace_path"])
    assert result["status"] == "ok"
    assert result["action"] == "simulate"
    assert result["project_id"] == project["project_id"]
    assert result["simulation"]["status"] == "pass"
    assert "reasoning" in result
    assert "explanation" in result["reasoning"]
    assert "suggested_actions" in result["reasoning"]
    assert result["state"]["active_iteration"] == 1
    assert result["state"]["history"][-1]["action"] == "simulate"
    assert (workspace_path / "history" / "simulations" / "sim_001.json").exists()


def test_iterate_can_define_material_without_recalculation(tmp_path: Path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    project = orchestrator.handle(
        {
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "dron que levante 2kg",
                "payload_kg": 2.0,
                "restrictions": "sin restricciones adicionales",
                "detail_level": "conceptual",
                "motors": 4,
                "per_motor_max_thrust_n": 15.0,
                "structure_mass_factor": 0.6,
                "safety_factor": 1.2,
            },
        }
    )

    start = orchestrator.handle(
        {
            "action": "iterate",
            "parameters": {
                "objetivo": "material",
                "operacion": "define",
                "variable": "material",
            },
        }
    )
    assert "Quieres define material" in start["message"]

    step_1 = orchestrator.handle({"action": "iterate", "raw_user_input": "sí"})
    assert "¿Qué material quieres usar?" in step_1["question"]

    orchestrator.handle({"action": "iterate", "raw_user_input": "fibra de carbono"})
    step_3 = orchestrator.handle({"action": "iterate", "raw_user_input": "mantener resistencia"})
    assert "No se recalcula impacto físico en esta versión" in step_3["message"]

    orchestrator.handle({"action": "iterate", "raw_user_input": "sí"})
    result = orchestrator.handle({"action": "iterate", "raw_user_input": "sí"})

    workspace_path = Path(result["workspace_path"])
    assert result["status"] == "ok"
    assert result["project_id"] == project["project_id"]
    assert result["state"]["design_properties"]["structure"]["material"] == "fibra de carbono"
    assert result["message"] == "Propiedad del diseño definida. No se recalcula impacto físico en esta versión."
    assert "reasoning" in result
    assert "explanation" in result["reasoning"]
    assert result["suggestion_context_note"] == "No se generan sugerencias físicas automáticas en iteraciones declarativas."
    assert result["suggestions"] == []
    assert (workspace_path / "history" / "iterations" / "iter_001.json").exists()


def test_iterate_can_define_components_declaratively_without_internal_error(tmp_path: Path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    project = orchestrator.handle(
        {
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "dron que levante 2kg",
                "payload_kg": 2.0,
                "restrictions": "sin restricciones adicionales",
                "detail_level": "conceptual",
                "motors": 4,
                "per_motor_max_thrust_n": 15.0,
                "structure_mass_factor": 0.6,
                "safety_factor": 1.2,
            },
        }
    )

    start = orchestrator.handle(
        {
            "action": "iterate",
            "parameters": {
                "objetivo": "sistema de potencia",
                "operacion": "define",
                "variable": "componentes",
            },
        }
    )
    assert "Quieres define sistema de potencia" in start["message"]

    step_1 = orchestrator.handle({"action": "iterate", "raw_user_input": "sí"})
    assert "¿Qué componentes quieres usar en la unidad de potencia?" in step_1["question"]

    step_2 = orchestrator.handle({"action": "iterate", "raw_user_input": "motores brushless + esc 30a"})
    assert step_2["step"] == 3

    impact = orchestrator.handle({"action": "iterate", "raw_user_input": "no cambiar tamaño"})
    assert "No se recalcula impacto físico en esta versión" in impact["message"]

    orchestrator.handle({"action": "iterate", "raw_user_input": "sí"})
    result = orchestrator.handle({"action": "iterate", "raw_user_input": "sí"})

    workspace_path = Path(result["workspace_path"])
    assert result["status"] == "ok"
    assert result["project_id"] == project["project_id"]
    assert result["iteration_draft"]["objective"] is not None
    components = result["state"]["design_properties"]["components"]
    assert len(components) >= 1
    first_component = next(iter(components.values()))
    assert first_component["component_type"] == "propulsion_active"
    assert first_component["suggested_key"] == "motors"
    assert result["message"] == "Propiedad del diseño definida. No se recalcula impacto físico en esta versión."
    assert result["suggestion_context_note"] == "No se generan sugerencias físicas automáticas en iteraciones declarativas."
    assert result["suggestions"] == []
    assert any(
        action["label"] == "Definir empuje por motor real"
        for action in result["reasoning"]["suggested_actions"]
    )
    assert (workspace_path / "history" / "iterations" / "iter_001.json").exists()


def test_iterate_motor_suggestions_survive_orchestrator_session_rehydration(tmp_path: Path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle(
        {
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "dron que levante 2kg",
                "payload_kg": 2.0,
                "restrictions": "sin restricciones adicionales",
                "detail_level": "conceptual",
                "motors": 4,
                "per_motor_max_thrust_n": 15.0,
                "structure_mass_factor": 0.6,
                "safety_factor": 1.2,
            },
        }
    )
    orchestrator.handle(
        {
            "action": "iterate",
            "parameters": {
                "objetivo": "sistema de potencia",
                "operacion": "define",
                "variable": "componentes",
            },
        }
    )
    orchestrator.handle({"action": "iterate", "raw_user_input": "sí"})

    suggestions = orchestrator.handle({"action": "iterate", "raw_user_input": "4 motores 920KV"})
    assert suggestions["step"] == 2
    assert suggestions["motor_suggestions"]

    selected = orchestrator.handle({"action": "iterate", "raw_user_input": "1"})
    assert selected["step"] == 3
    assert selected["motor_suggestions"] == []

    component_patch = selected["iteration_draft"]["component_patch"]
    motor_spec = component_patch["motors"]
    properties = motor_spec["properties"]
    assert properties["thrust_n"]["value"] == pytest.approx(suggestions["motor_suggestions"][0]["thrust_n"])
    assert properties["weight_g"]["value"] == pytest.approx(suggestions["motor_suggestions"][0]["weight_g"])


# ── build_startup_context ─────────────────────────────────────────────────────

_AERIAL_PARAMS = {
    "vehicle_type": "dron",
    "objective": "dron de carga",
    "payload_kg": 2.0,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "motors": 4,
    "per_motor_max_thrust_n": 15.0,
    "structure_mass_factor": 0.6,
    "safety_factor": 1.2,
}


def _create_aerial_project(tmp_path: Path) -> tuple["JarvisOrchestrator", dict]:
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    result = orchestrator.handle({"action": "create_project", "parameters": _AERIAL_PARAMS})
    return orchestrator, result


def test_build_startup_context_no_project_returns_has_project_false(tmp_path: Path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    ctx = orchestrator.build_startup_context()
    assert ctx == {"has_project": False}


def test_build_startup_context_nominal_project_has_correct_structure(tmp_path: Path):
    orchestrator, result = _create_aerial_project(tmp_path)
    ctx = orchestrator.build_startup_context(workspace_path=result["workspace_path"])

    assert ctx["has_project"] is True
    assert ctx["objective"] == _AERIAL_PARAMS["objective"]
    assert ctx["status_type"] == "nominal"
    assert ctx["status_reason"] is None
    assert "project_slug" in ctx
    assert ctx["phase"] in {"optimization", "complete"}
    assert isinstance(ctx["phase_description"], str)
    assert isinstance(ctx["phase_confidence"], float)


def test_build_startup_context_nominal_active_variables_contain_payload_and_motors(tmp_path: Path):
    orchestrator, result = _create_aerial_project(tmp_path)
    ctx = orchestrator.build_startup_context(workspace_path=result["workspace_path"])

    active_vars = ctx["active_variables"]
    assert "payload_kg" in active_vars
    assert "motor_count" in active_vars
    assert len(active_vars) <= 3


def test_build_startup_context_nominal_suggested_action_is_none_or_set(tmp_path: Path):
    """Nominal project may or may not have a suggested action — structure is always correct."""
    orchestrator, result = _create_aerial_project(tmp_path)
    ctx = orchestrator.build_startup_context(workspace_path=result["workspace_path"])

    sa = ctx["suggested_action"]
    if sa is not None:
        assert "label" in sa
        assert "reason" in sa
        assert "hint" in sa


def test_build_startup_context_blocking_when_missing_transmission_params(tmp_path: Path):
    """Project with physics_status=missing_parameters → status_type=blocking."""
    orchestrator, result = _create_aerial_project(tmp_path)
    workspace_path = Path(result["workspace_path"])

    # Patch state.json: inject missing_parameters into simulation results
    state_path = workspace_path / "state.json"
    data = json.loads(state_path.read_text(encoding="utf-8"))
    data["latest_results"]["simulation"]["physics_status"] = "missing_parameters"
    data["latest_results"]["simulation"]["warnings"] = ["missing_transmission_parameters"]
    data["current_parameters"]["per_actuator_torque_nm"] = 80.0
    del data["current_parameters"]["per_motor_max_thrust_n"]
    state_path.write_text(json.dumps(data), encoding="utf-8")

    ctx = orchestrator.build_startup_context(workspace_path=str(workspace_path))

    assert ctx["status_type"] == "blocking"
    assert ctx["status_reason"] == "missing_transmission_parameters"
    assert ctx["phase"] == "definition"


def test_build_startup_context_blocking_active_variables_contain_torque(tmp_path: Path):
    """Blocking state: active_variables should surface per_actuator_torque_nm."""
    orchestrator, result = _create_aerial_project(tmp_path)
    workspace_path = Path(result["workspace_path"])

    state_path = workspace_path / "state.json"
    data = json.loads(state_path.read_text(encoding="utf-8"))
    data["latest_results"]["simulation"]["physics_status"] = "missing_parameters"
    data["latest_results"]["simulation"]["warnings"] = ["missing_transmission_parameters"]
    data["current_parameters"]["per_actuator_torque_nm"] = 80.0
    state_path.write_text(json.dumps(data), encoding="utf-8")

    ctx = orchestrator.build_startup_context(workspace_path=str(workspace_path))
    assert "per_actuator_torque_nm" in ctx["active_variables"]


def test_build_startup_context_blocking_suggested_action_has_hint(tmp_path: Path):
    """Blocking+transmission: suggested_action includes actionable hint for the user."""
    orchestrator, result = _create_aerial_project(tmp_path)
    workspace_path = Path(result["workspace_path"])

    state_path = workspace_path / "state.json"
    data = json.loads(state_path.read_text(encoding="utf-8"))
    data["latest_results"]["simulation"]["physics_status"] = "missing_parameters"
    data["latest_results"]["simulation"]["warnings"] = ["missing_transmission_parameters"]
    data["current_parameters"]["per_actuator_torque_nm"] = 80.0
    state_path.write_text(json.dumps(data), encoding="utf-8")

    ctx = orchestrator.build_startup_context(workspace_path=str(workspace_path))
    assert ctx["suggested_action"] is not None
    assert ctx["suggested_action"]["hint"] is not None
    assert "0.15" in ctx["suggested_action"]["hint"] or "10" in ctx["suggested_action"]["hint"]


# ── _handle_project_status (on-demand state) ─────────────────────────────────

def test_handle_project_status_returns_project_status_action(tmp_path: Path):
    """_handle_project_status uses build_startup_context — same data, no LLM."""
    orchestrator, result = _create_aerial_project(tmp_path)
    # Make sure state_manager knows about the project by loading it
    orchestrator.state_manager.load_active_project(
        orchestrator.workspace_manager, workspace_path=result["workspace_path"]
    )
    status_result = orchestrator._handle_project_status()

    assert status_result["status"] == "ok"
    assert status_result["action"] == "project_status"
    assert "startup_context" in status_result
    assert status_result["startup_context"]["has_project"] is True


def test_handle_project_status_no_project_has_project_false(tmp_path: Path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    status_result = orchestrator._handle_project_status()

    assert status_result["status"] == "ok"
    assert status_result["startup_context"]["has_project"] is False


# ── Bug 7: global queries during ITERATE_INTERACTIVE preserve session ─────────

def _drive_iterate_to_step4(orchestrator: JarvisOrchestrator) -> None:
    """Start an iterate wizard and advance it to step 4 (apply decision)."""
    orchestrator.handle({
        "action": "iterate",
        "parameters": {"objetivo": "peso", "operacion": "reducir"},
    })
    orchestrator.handle({"action": "iterate", "raw_user_input": "sí"})         # step 0→1
    orchestrator.handle({"action": "iterate", "raw_user_input": "componentes"}) # step 1→2
    orchestrator.handle({"action": "iterate", "raw_user_input": "optimizar estructura"})  # step 2→3
    orchestrator.handle({"action": "iterate", "raw_user_input": "sin restricciones"})     # step 3→4


def test_project_status_during_iterate_interactive_preserves_session(tmp_path: Path):
    """Bug 7: 'estado del proyecto' during an active iterate wizard must return
    project_status data without touching the session — the wizard continues from
    the same step on the next turn."""
    from unittest.mock import MagicMock

    orchestrator, _ = _create_aerial_project(tmp_path)
    _drive_iterate_to_step4(orchestrator)

    session_before = orchestrator.state_manager.runtime_state.session
    assert session_before.step == 4, "precondition: wizard must be at step 4"

    llm_interface = MagicMock()
    result = orchestrator.handle_user_text("estado del proyecto", llm_interface)

    assert result["action"] == "project_status", (
        f"Expected action='project_status', got {result.get('action')!r}"
    )
    assert result["status"] == "ok"

    session_after = orchestrator.state_manager.runtime_state.session
    assert session_after.step == 4, (
        "Session step must not change after a project_status query"
    )
    # LLM must not have been called — project_status is purely local
    llm_interface.interpret.assert_not_called()
    llm_interface.analyze.assert_not_called()


def test_analyze_during_iterate_interactive_preserves_session(tmp_path: Path):
    """Bug 7: an analysis question during an active iterate wizard must return
    an analysis response without interrupting the session."""
    from unittest.mock import MagicMock

    orchestrator, _ = _create_aerial_project(tmp_path)
    _drive_iterate_to_step4(orchestrator)

    session_before = orchestrator.state_manager.runtime_state.session
    assert session_before.step == 4, "precondition: wizard must be at step 4"

    llm_interface = MagicMock()
    llm_interface.analyze.return_value = "Análisis: el dron está bien configurado."

    result = orchestrator.handle_user_text("¿qué le pasa al dron?", llm_interface)

    assert result["action"] == "analyze", (
        f"Expected action='analyze', got {result.get('action')!r}"
    )
    assert result["status"] == "ok"

    session_after = orchestrator.state_manager.runtime_state.session
    assert session_after.step == 4, (
        "Session step must not change after an analyze query"
    )
    # LLM.analyze must have been called (analyze uses LLM), but NOT interpret
    llm_interface.analyze.assert_called_once()
    llm_interface.interpret.assert_not_called()


# ── Bug 64: component intercept helper still guarded inside ITERATE ───────────
# Calibration 2026-08-05: handle_user_text preempts (clears wizard) then intercepts.
# The helper itself must still return None during ITERATE so intercept only runs
# after clear — otherwise we'd apply the component and leave a zombie wizard.

class TestIterateInteractiveComponentGuard:
    """Bug 64: _should_intercept_component returns None while ITERATE is active."""

    def test_component_description_not_intercepted_during_iterate_wizard(self, tmp_path):
        """Helper returns None during ITERATE; preemption path clears then re-checks."""
        from jarvis.schemas.action_schema import OrchestratorMode

        orchestrator, _ = _create_aerial_project(tmp_path)

        iterate_session = orchestrator.state_manager.runtime_state.session.model_copy(
            update={"mode": OrchestratorMode.ITERATE_INTERACTIVE, "step": 1}
        )
        orchestrator.state_manager.set_runtime_session(iterate_session)
        current_session = orchestrator.state_manager.runtime_state.session

        result = orchestrator._should_intercept_component(
            "300g de fibra de carbono", current_session
        )

        assert result is None, (
            "Bug 64: _should_intercept_component must return None during ITERATE_INTERACTIVE "
            f"so preemption can clear the wizard first. Got: {result!r}"
        )


# ── Calibration 2026-08-05: hard preempt strong intents inside ITERATE ────────

class TestIterateWizardPreemption:
    """Strong intents abort ITERATE_INTERACTIVE and take over the turn."""

    def test_explore_preempts_iterate_wizard(self, tmp_path: Path):
        from unittest.mock import MagicMock

        orchestrator, _ = _create_aerial_project(tmp_path)
        _drive_iterate_to_step4(orchestrator)
        assert orchestrator.state_manager.runtime_state.session.mode == OrchestratorMode.ITERATE_INTERACTIVE

        llm = MagicMock()
        result = orchestrator.handle_user_text(
            "explora mejores configuraciones para autonomía", llm
        )

        assert result.get("preempted_iterate") is True
        assert result.get("action") == "explore_design_space"
        assert orchestrator.state_manager.runtime_state.session.mode == OrchestratorMode.IDLE
        llm.interpret.assert_not_called()

    def test_calculate_preempts_iterate_wizard(self, tmp_path: Path):
        from unittest.mock import MagicMock

        orchestrator, _ = _create_aerial_project(tmp_path)
        _drive_iterate_to_step4(orchestrator)

        result = orchestrator.handle_user_text("calcula", MagicMock())

        assert result.get("preempted_iterate") is True
        assert result.get("action") == "calculate"
        assert orchestrator.state_manager.runtime_state.session.mode == OrchestratorMode.IDLE

    def test_simulate_preempts_iterate_wizard(self, tmp_path: Path):
        from unittest.mock import MagicMock

        orchestrator, _ = _create_aerial_project(tmp_path)
        _drive_iterate_to_step4(orchestrator)

        result = orchestrator.handle_user_text("simula", MagicMock())

        assert result.get("preempted_iterate") is True
        assert result.get("action") == "simulate"
        assert orchestrator.state_manager.runtime_state.session.mode == OrchestratorMode.IDLE

    def test_new_iterate_request_preempts_old_wizard(self, tmp_path: Path):
        """A new change request must not be eaten as a step-4 wizard answer."""
        from unittest.mock import MagicMock

        orchestrator, _ = _create_aerial_project(tmp_path)
        _drive_iterate_to_step4(orchestrator)
        assert orchestrator.state_manager.runtime_state.session.step == 4

        result = orchestrator.handle_user_text("aumenta payload a 0.8", MagicMock())

        assert result.get("preempted_iterate") is True
        session = orchestrator.state_manager.runtime_state.session
        # Old step-4 draft must be gone (either idle after apply, or fresh iterate).
        assert not (
            session.mode == OrchestratorMode.ITERATE_INTERACTIVE and session.step == 4
        )
        assert result.get("action") in {
            "define_missing_params",
            "iterate",
        } or session.mode == OrchestratorMode.ITERATE_INTERACTIVE

    def test_component_preempts_iterate_wizard(self, tmp_path: Path):
        from unittest.mock import MagicMock

        orchestrator, _ = _create_aerial_project(tmp_path)
        _drive_iterate_to_step4(orchestrator)

        result = orchestrator.handle_user_text("carbono 400g", MagicMock())

        assert result.get("preempted_iterate") is True
        assert result.get("action") == "component_description_saved"
        assert orchestrator.state_manager.runtime_state.session.mode == OrchestratorMode.IDLE

    def test_define_motor_kv_does_not_preempt_and_offers_suggestions(self, tmp_path: Path):
        """DEFINE @ step 2 owns motor specs so catalog suggestions can appear."""
        from unittest.mock import MagicMock

        orchestrator, _ = _create_aerial_project(tmp_path)
        start = orchestrator.handle({
            "action": "iterate",
            "parameters": {
                "objetivo": "definición declarativa",
                "operacion": "define",
                "variable": "componentes",
                "enrich_component": "motors",
            },
        })
        assert start["step"] == 2

        result = orchestrator.handle_user_text("4 motores 920KV", MagicMock())

        assert result.get("preempted_iterate") is not True
        assert orchestrator.state_manager.runtime_state.session.mode == OrchestratorMode.ITERATE_INTERACTIVE
        suggestions = result.get("motor_suggestions") or []
        assert len(suggestions) > 0
        assert "biblioteca" in (result.get("message") or "").lower()

        pick = orchestrator.handle_user_text("1", MagicMock())
        assert pick.get("preempted_iterate") is not True
        assert orchestrator.state_manager.runtime_state.session.step == 3
        assert "empuje" in (pick.get("message") or "").lower() or "N" in (pick.get("message") or "")

    def test_wizard_step_answer_does_not_preempt(self, tmp_path: Path):
        from unittest.mock import MagicMock

        orchestrator, _ = _create_aerial_project(tmp_path)
        # Start iterate and stay at step 0 confirmation
        orchestrator.handle({
            "action": "iterate",
            "parameters": {"objetivo": "peso", "operacion": "reducir"},
        })
        assert orchestrator.state_manager.runtime_state.session.step == 0

        result = orchestrator.handle_user_text("sí", MagicMock())

        assert result.get("preempted_iterate") is not True
        assert orchestrator.state_manager.runtime_state.session.mode == OrchestratorMode.ITERATE_INTERACTIVE
        assert orchestrator.state_manager.runtime_state.session.step == 1

    def test_project_status_still_soft_interrupt(self, tmp_path: Path):
        """Bug 7 preserved: status does not clear the wizard."""
        from unittest.mock import MagicMock

        orchestrator, _ = _create_aerial_project(tmp_path)
        _drive_iterate_to_step4(orchestrator)

        result = orchestrator.handle_user_text("estado del proyecto", MagicMock())

        assert result.get("preempted_iterate") is not True
        assert result.get("action") == "project_status"
        assert orchestrator.state_manager.runtime_state.session.step == 4
