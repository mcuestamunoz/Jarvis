"""Wizard vigilancia / mission nudge at SYSTEM_DEFINITION B1 (`B1-wizard-mission-nudge`).

Covers implementation_contract_wizard_mission_nudge_b1.md §2:

  T1  start with objective containing "vigilancia" (no cameras/radio yet)
      -> step-0 message includes the nudge line
  T2  Neutral objective -> message excludes nudge; unchanged pre-Buy shape
  T3  Objective mission-like but `cameras` already present -> no nudge
  T4  Restrictions alone contain a mission keyword (objective neutral) -> nudge present
  T5  Choosing A after nudge still applies base architecture only (no auto camera/radio)
  T6  Full pytest green (checked at the repo level)
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.system_definition_session import _MISSION_NUDGE_LINE
from jarvis.schemas.action_schema import ComponentSpec


def _create_project(orchestrator, *, objective: str, restrictions: str = "no") -> None:
    orchestrator.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": objective,
            "payload_kg": 1.0,
            "restrictions": restrictions,
            "detail_level": "detallado",
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })


def _start_message(tmp_path: Path, *, objective: str, restrictions: str = "no") -> str:
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_project(orchestrator, objective=objective, restrictions=restrictions)
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    result = orchestrator.system_definition_session.start("dron", project_state)
    return result["message"]


# ── T1 ────────────────────────────────────────────────────────────────────


def test_t1_vigilancia_objective_shows_nudge(tmp_path: Path):
    message = _start_message(tmp_path, objective="dron de vigilancia doméstico")
    assert _MISSION_NUDGE_LINE in message


def test_t1_camera_english_objective_shows_nudge(tmp_path: Path):
    message = _start_message(tmp_path, objective="home surveillance drone")
    assert _MISSION_NUDGE_LINE in message


# ── T2 ────────────────────────────────────────────────────────────────────


def test_t2_neutral_objective_excludes_nudge(tmp_path: Path):
    message = _start_message(tmp_path, objective="dron de prueba")
    assert _MISSION_NUDGE_LINE not in message
    assert message == (
        "Para un dron, la arquitectura típica incluye:\n\n"
        "  • Propulsión (motores + hélices + ESC)\n"
        "  • Energía (batería)\n"
        "  • Estructura (frame)\n"
        "  • Control (controladora + sensores)\n\n"
        "Recomendado: empieza por Propulsión (motores + hélices + ESC) — "
        "es el bloque que define el dimensionado del resto.\n\n"
        "  A — Usar esta arquitectura base\n"
        "  B — Añadir o modificar bloques\n"
        "  C — Saltar (definir después)"
    )


# ── T3 ────────────────────────────────────────────────────────────────────


def test_t3_cameras_already_declared_suppresses_nudge_despite_mission_objective(tmp_path: Path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_project(orchestrator, objective="dron de vigilancia doméstico")
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    updated_components = {
        **project_state.design_properties.components,
        "cameras": ComponentSpec(suggested_key="cameras", completeness="medium"),
    }
    updated_dp = project_state.design_properties.model_copy(update={"components": updated_components})
    project_state = project_state.model_copy(update={"design_properties": updated_dp})
    orchestrator.workspace_manager.save_state(project_state)
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)

    result = orchestrator.system_definition_session.start("dron", project_state)
    assert _MISSION_NUDGE_LINE not in result["message"]


def test_t3_radio_module_already_declared_suppresses_nudge(tmp_path: Path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_project(orchestrator, objective="dron de vigilancia doméstico")
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    updated_components = {
        **project_state.design_properties.components,
        "radio_module": ComponentSpec(suggested_key="radio_module", completeness="low"),
    }
    updated_dp = project_state.design_properties.model_copy(update={"components": updated_components})
    project_state = project_state.model_copy(update={"design_properties": updated_dp})
    orchestrator.workspace_manager.save_state(project_state)
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)

    result = orchestrator.system_definition_session.start("dron", project_state)
    assert _MISSION_NUDGE_LINE not in result["message"]


# ── T4 ────────────────────────────────────────────────────────────────────


def test_t4_restrictions_alone_carry_mission_keyword_shows_nudge(tmp_path: Path):
    message = _start_message(tmp_path, objective="dron de prueba", restrictions="necesita telemetría")
    assert _MISSION_NUDGE_LINE in message


# ── T5 ────────────────────────────────────────────────────────────────────


def test_t5_option_a_after_nudge_still_applies_base_architecture_only(tmp_path: Path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_project(orchestrator, objective="dron de vigilancia doméstico")
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    start_result = orchestrator.system_definition_session.start("dron", project_state)
    assert _MISSION_NUDGE_LINE in start_result["message"]

    result = orchestrator.system_definition_session.answer("a")
    assert result["status"] == "ok"

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert set(saved.design_properties.components.keys()) == {
        "motors", "propellers", "esc", "battery", "frame", "flight_controller", "sensors",
    }
    assert "cameras" not in saved.design_properties.components
    assert "radio_module" not in saved.design_properties.components


def test_t5_option_b_after_nudge_can_still_add_camera_identity_rules_unaffected(tmp_path: Path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_project(orchestrator, objective="dron de vigilancia doméstico")
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    orchestrator.system_definition_session.start("dron", project_state)

    orchestrator.system_definition_session.answer("b")
    result = orchestrator.system_definition_session.answer("cámara")
    assert "todavía no puedo resolver" not in result["message"].lower()
    orchestrator.system_definition_session.answer("listo")

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert "cameras" in saved.design_properties.components
