"""Tests for create_project interactive branching by vehicle_type domain."""
from __future__ import annotations

from pathlib import Path

from jarvis.core.interactive_session import (
    STEP_AERIAL_MOTORS,
    STEP_AERIAL_PATH,
    STEP_AERIAL_PROP_DIAMETER,
    STEP_AERIAL_PROP_RPM,
    STEP_AERIAL_THRUST,
    STEP_CONFIRM,
    STEP_GROUND_ACTUATORS,
    STEP_GROUND_FORCE,
    STEP_GROUND_PATH,
    STEP_GROUND_TORQUE,
    CreateProjectInteractiveSession,
)
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import InteractiveSessionState, OrchestratorMode, ProjectDraft


def _session(draft: ProjectDraft, step: int) -> InteractiveSessionState:
    return InteractiveSessionState(
        mode=OrchestratorMode.CREATE_PROJECT_INTERACTIVE,
        step=step,
        project_draft=draft,
    )


def _trunk_draft(**overrides) -> ProjectDraft:
    base = {
        "vehicle_type": "dron",
        "objective": "test",
        "payload_kg": 1.0,
        "restrictions": "ninguna",
        "detail_level": "conceptual",
        "structure_mass_factor": 0.6,
        "safety_factor": 1.2,
    }
    base.update(overrides)
    return ProjectDraft.model_validate(base)


def test_aerial_thrust_path_writes_per_motor_thrust():
    s = CreateProjectInteractiveSession()
    draft = _trunk_draft()
    session = _session(draft, STEP_AERIAL_MOTORS)

    r1 = s.answer(session, "4")
    assert r1["step"] == STEP_AERIAL_PATH
    assert r1["project_draft"]["motors"] == 4

    r2 = s.answer(_session(ProjectDraft.model_validate(r1["project_draft"]), r1["step"]), "empuje")
    assert r2["step"] == STEP_AERIAL_THRUST

    r3 = s.answer(_session(ProjectDraft.model_validate(r2["project_draft"]), r2["step"]), "15")
    assert r3["step"] == STEP_CONFIRM
    assert r3["project_draft"]["per_motor_max_thrust_n"] == 15.0
    payload = s.build_execution_payload(ProjectDraft.model_validate(r3["project_draft"]))
    assert payload["motors"] == 4
    assert payload["per_motor_max_thrust_n"] == 15.0
    assert payload["propeller_diameter_in"] is None


def test_aerial_propellers_path_writes_diameter_and_rpm():
    s = CreateProjectInteractiveSession()
    draft = _trunk_draft(motors=4)
    session = _session(draft, STEP_AERIAL_PATH)

    r1 = s.answer(session, "hélices")
    assert r1["step"] == STEP_AERIAL_PROP_DIAMETER

    r2 = s.answer(_session(ProjectDraft.model_validate(r1["project_draft"]), r1["step"]), "10")
    assert r2["step"] == STEP_AERIAL_PROP_RPM
    assert r2["project_draft"]["propeller_diameter_in"] == 10.0

    r3 = s.answer(_session(ProjectDraft.model_validate(r2["project_draft"]), r2["step"]), "7500")
    assert r3["step"] == STEP_CONFIRM
    assert r3["project_draft"]["propeller_rpm"] == 7500.0
    payload = s.build_execution_payload(ProjectDraft.model_validate(r3["project_draft"]))
    assert payload["propeller_diameter_in"] == 10.0
    assert payload["propeller_rpm"] == 7500.0
    assert payload["per_motor_max_thrust_n"] is None


def test_aerial_unknown_path_skips_force_params():
    s = CreateProjectInteractiveSession()
    draft = _trunk_draft(motors=4)
    r = s.answer(_session(draft, STEP_AERIAL_PATH), "no sé aún")
    assert r["step"] == STEP_CONFIRM
    assert r["project_draft"]["per_motor_max_thrust_n"] is None
    assert r["project_draft"]["propeller_diameter_in"] is None


def test_ground_torque_path():
    s = CreateProjectInteractiveSession()
    draft = _trunk_draft(vehicle_type="rover")
    r1 = s.answer(_session(draft, STEP_GROUND_ACTUATORS), "2")
    assert r1["step"] == STEP_GROUND_PATH
    assert r1["project_draft"]["motors"] == 2

    r2 = s.answer(_session(ProjectDraft.model_validate(r1["project_draft"]), r1["step"]), "torque")
    assert r2["step"] == STEP_GROUND_TORQUE

    r3 = s.answer(_session(ProjectDraft.model_validate(r2["project_draft"]), r2["step"]), "5.5")
    assert r3["step"] == STEP_CONFIRM
    assert r3["project_draft"]["per_actuator_torque_nm"] == 5.5
    payload = s.build_execution_payload(ProjectDraft.model_validate(r3["project_draft"]))
    assert payload["per_actuator_torque_nm"] == 5.5
    assert payload["max_force_per_actuator_n"] is None


def test_ground_force_path():
    s = CreateProjectInteractiveSession()
    draft = _trunk_draft(vehicle_type="robot", motors=4)
    r1 = s.answer(_session(draft, STEP_GROUND_PATH), "fuerza directa")
    assert r1["step"] == STEP_GROUND_FORCE

    r2 = s.answer(_session(ProjectDraft.model_validate(r1["project_draft"]), r1["step"]), "40")
    assert r2["step"] == STEP_CONFIRM
    assert r2["project_draft"]["max_force_per_actuator_n"] == 40.0


def test_ground_unknown_path():
    s = CreateProjectInteractiveSession()
    draft = _trunk_draft(vehicle_type="coche", motors=2)
    r = s.answer(_session(draft, STEP_GROUND_PATH), "no sé")
    assert r["step"] == STEP_CONFIRM
    assert r["project_draft"]["per_actuator_torque_nm"] is None
    assert r["project_draft"]["max_force_per_actuator_n"] is None


def test_detallado_applies_defaults_then_aerial_branch():
    """FN-008: 'detallado' no pregunta por factores — salta directo a la rama de
    dominio con las mismas hipótesis por defecto que 'conceptual' (0.6 / 1.2)."""
    s = CreateProjectInteractiveSession()
    draft = ProjectDraft.model_validate(
        {
            "vehicle_type": "dron",
            "objective": "test",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
        }
    )
    session = _session(draft, 4)  # STEP_DETAIL
    r = s.answer(session, "detallado")
    assert r["step"] == STEP_AERIAL_MOTORS
    assert r["project_draft"]["detail_level"] == "detallado"
    assert r["project_draft"]["structure_mass_factor"] == 0.6
    assert r["project_draft"]["safety_factor"] == 1.2


def test_detallado_ground_branch_also_gets_defaults():
    """Mismo comportamiento en la rama terrestre."""
    s = CreateProjectInteractiveSession()
    draft = ProjectDraft.model_validate(
        {
            "vehicle_type": "rover",
            "objective": "test",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
        }
    )
    r = s.answer(_session(draft, 4), "detallado")
    assert r["step"] == STEP_GROUND_ACTUATORS
    assert r["project_draft"]["structure_mass_factor"] == 0.6
    assert r["project_draft"]["safety_factor"] == 1.2


def test_confirmation_message_explains_hypotheses_not_internal_keys():
    """FN-008: el resumen explica el efecto de las hipótesis en lenguaje llano,
    sin exponer factor_estructura/factor_seguridad como protagonistas, y sin
    prometer un 'Enter' que ya no existe como pregunta."""
    s = CreateProjectInteractiveSession()
    draft = ProjectDraft.model_validate(
        {
            "vehicle_type": "dron",
            "objective": "test",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
        }
    )
    r = s.answer(_session(draft, 4), "detallado")
    r = s.answer(_session(ProjectDraft.model_validate(r["project_draft"]), r["step"]), "4")
    r = s.answer(_session(ProjectDraft.model_validate(r["project_draft"]), r["step"]), "no sé aún")
    assert r["step"] == STEP_CONFIRM

    message = s._build_confirmation_message(ProjectDraft.model_validate(r["project_draft"]))
    assert "factor_estructura" not in message
    assert "factor_seguridad" not in message
    assert "Enter para default" not in message
    assert "60%" in message  # 0.6 estructura
    assert "20%" in message  # margen de seguridad (1.2 - 1)
    assert "editable" in message.lower()


def test_conceptual_applies_defaults_then_aerial_branch():
    s = CreateProjectInteractiveSession()
    draft = ProjectDraft.model_validate(
        {
            "vehicle_type": "dron",
            "objective": "test",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
        }
    )
    r = s.answer(_session(draft, 4), "conceptual")
    assert r["step"] == STEP_AERIAL_MOTORS
    assert r["project_draft"]["structure_mass_factor"] == 0.6
    assert r["project_draft"]["safety_factor"] == 1.2


def test_unknown_vehicle_skips_domain_branch():
    s = CreateProjectInteractiveSession()
    draft = ProjectDraft.model_validate(
        {
            "vehicle_type": "satelite",
            "objective": "test",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
        }
    )
    r = s.answer(_session(draft, 4), "conceptual")
    assert r["step"] == STEP_CONFIRM


def test_direct_create_project_with_full_params_skips_wizard(tmp_path: Path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    result = orchestrator.handle(
        {
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "direct create",
                "payload_kg": 2.0,
                "restrictions": "ninguna",
                "detail_level": "conceptual",
                "motors": 4,
                "per_motor_max_thrust_n": 15.0,
                "structure_mass_factor": 0.6,
                "safety_factor": 1.2,
            },
        }
    )
    assert result["status"] == "ok"
    assert result["project_id"]
    state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert state.current_parameters["motor_count"] == 4
    assert state.current_parameters["per_motor_max_thrust_n"] == 15.0


def test_orchestrator_ground_branch_end_to_end(tmp_path: Path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    start = orchestrator.handle({"action": "create_project", "parameters": {"vehicle_type": "rover"}})
    assert start["step"] == 1

    orchestrator.handle({"action": "create_project", "raw_user_input": "explorar terreno"})
    orchestrator.handle({"action": "create_project", "raw_user_input": "5"})
    orchestrator.handle({"action": "create_project", "raw_user_input": "ninguna"})
    after_detail = orchestrator.handle({"action": "create_project", "raw_user_input": "conceptual"})
    assert after_detail["step"] == STEP_GROUND_ACTUATORS

    after_count = orchestrator.handle({"action": "create_project", "raw_user_input": "4"})
    assert after_count["step"] == STEP_GROUND_PATH

    after_path = orchestrator.handle({"action": "create_project", "raw_user_input": "fuerza"})
    assert after_path["step"] == STEP_GROUND_FORCE

    confirm = orchestrator.handle({"action": "create_project", "raw_user_input": "40"})
    assert confirm["step"] == STEP_CONFIRM
    assert "actuadores=" in confirm["message"]

    result = orchestrator.handle({"action": "create_project", "raw_user_input": "sí"})
    assert result["status"] == "interactive"
    assert result["mode"] == "system_definition"
    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert saved.current_parameters["motor_count"] == 4
    assert saved.current_parameters["max_force_per_actuator_n"] == 40.0
