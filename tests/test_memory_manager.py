from pathlib import Path

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.state_manager import StateManager
from jarvis.memory.memory_manager import MemoryManager
from jarvis.schemas.state_schema import HistoryEntry, ProjectState
from jarvis.schemas.action_schema import ActionName


def test_memory_manager_records_conflict_resolution():
    manager = MemoryManager()
    state = ProjectState(
        project_id="abc123",
        project_slug="demo",
        objective="demo",
        workspace_path="/tmp/demo",
    )

    updated = manager.apply_conflict_resolution(
        state,
        initial_objective="peso",
        initial_operation="reducir",
        conflicting_operation="aumentar",
        resolution="keep_initial_goal",
    )

    assert updated.memory.preferences["prioritize_weight_reduction"] is True
    assert updated.memory.conflict_history[-1].resolution == "keep_initial_goal"


def test_orchestrator_persists_memory_when_conflict_is_resolved(tmp_path: Path):
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
                "objetivo": "carga",
                "operacion": "aumentar",
                "project_id": project["project_id"],
            },
        }
    )
    step_1 = orchestrator.handle({"action": "iterate", "raw_user_input": "sí"})
    step_2 = orchestrator.handle({"action": "iterate", "raw_user_input": "carga"})
    conflict = orchestrator.handle({"action": "iterate", "raw_user_input": "reducir carga"})

    assert conflict["status"] == "interactive"
    resolved = orchestrator.handle({"action": "iterate", "raw_user_input": "1"})
    assert resolved["status"] == "interactive"

    state = orchestrator.state_manager.load(Path(project["workspace_path"]) / "state.json")
    assert state.memory.conflict_history[-1].resolution == "keep_initial_goal"
    assert state.memory.conflict_history[-1].initial_objective == "carga"


def test_iterate_conflict_message_uses_memory_hint(tmp_path: Path):
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

    orchestrator.handle(
        {
            "action": "iterate",
            "parameters": {
                "objetivo": "peso",
                "operacion": "reducir",
                "project_id": project["project_id"],
            },
        }
    )
    orchestrator.handle({"action": "iterate", "raw_user_input": "sí"})
    orchestrator.handle({"action": "iterate", "raw_user_input": "carga"})
    orchestrator.handle({"action": "iterate", "raw_user_input": "aumentar carga"})
    orchestrator.handle({"action": "iterate", "raw_user_input": "1"})
    orchestrator.state_manager.clear_runtime_session()

    start = orchestrator.handle(
        {
            "action": "iterate",
            "parameters": {
                "objetivo": "peso",
                "operacion": "reducir",
                "project_id": project["project_id"],
            },
        }
    )
    step_1 = orchestrator.handle({"action": "iterate", "raw_user_input": "sí"})
    step_2 = orchestrator.handle({"action": "iterate", "raw_user_input": "carga"})
    conflict = orchestrator.handle({"action": "iterate", "raw_user_input": "aumentar carga"})

    assert "En un conflicto similar anterior elegiste mantener el objetivo inicial." in conflict["message"]


# ── Bug 19: parsed_constraints always re-derived (never stale) ────────────────

def test_parsed_constraints_derived_on_creation():
    """Bug 19: ProjectState initialised with restrictions must populate parsed_constraints."""
    state = ProjectState(
        project_id="p1", project_slug="s", objective="o", workspace_path="/tmp",
        current_parameters={"restrictions": "vuelo mínimo 20 min"},
    )
    assert state.parsed_constraints == {"autonomy_min": 20.0}, (
        f"parsed_constraints must be derived on creation, got {state.parsed_constraints}"
    )


def test_parsed_constraints_updates_when_restrictions_changes():
    """Bug 19: parsed_constraints must be re-derived after restrictions string changes.

    Old behaviour (guard 'if not self.parsed_constraints') kept stale value after
    model_copy.  New behaviour always re-derives.
    """
    state = ProjectState(
        project_id="p1", project_slug="s", objective="o", workspace_path="/tmp",
        current_parameters={"restrictions": "vuelo mínimo 20 min"},
    )
    assert state.parsed_constraints == {"autonomy_min": 20.0}

    # Simulate a restrictions update written via model_copy (as record_action does)
    updated_params = dict(state.current_parameters)
    updated_params["restrictions"] = "vuelo mínimo 45 min"
    new_state = state.model_copy(update={"current_parameters": updated_params})

    assert new_state.parsed_constraints == {"autonomy_min": 45.0}, (
        f"parsed_constraints must reflect new restrictions, got {new_state.parsed_constraints}"
    )


def test_parsed_constraints_cleared_when_restrictions_removed():
    """Bug 19: removing restrictions string must clear parsed_constraints."""
    state = ProjectState(
        project_id="p1", project_slug="s", objective="o", workspace_path="/tmp",
        current_parameters={"restrictions": "vuelo mínimo 20 min"},
    )
    new_state = state.model_copy(update={"current_parameters": {}})
    assert new_state.parsed_constraints == {}, (
        f"parsed_constraints must be empty when restrictions is removed, got {new_state.parsed_constraints}"
    )


# ── Bug 18: last_total_mass_kg decoupled from latest_results ─────────────────

def _make_base_state() -> ProjectState:
    return ProjectState(
        project_id="p1", project_slug="s", objective="o", workspace_path="/tmp",
        current_parameters={"payload_kg": 2.0},
    )


def _make_action_entry() -> HistoryEntry:
    return HistoryEntry(action=ActionName.ITERATE, summary="test")


def test_record_action_stores_total_mass_from_calculations():
    """Bug 18: record_action must extract total_mass_kg and persist it in last_total_mass_kg."""
    manager = StateManager()
    state = _make_base_state()
    latest_results = {"calculations": {"total_mass_kg": 5.5, "autonomy_min": 22.0}}
    new_state = manager.record_action(state, _make_action_entry(), latest_results)
    assert new_state.last_total_mass_kg == 5.5, (
        f"last_total_mass_kg must be 5.5 after record_action, got {new_state.last_total_mass_kg}"
    )


def test_record_action_no_calculations_keeps_previous_mass():
    """Bug 18: if calculations absent, last_total_mass_kg must keep its previous value."""
    manager = StateManager()
    state = _make_base_state().model_copy(update={"last_total_mass_kg": 4.0})
    latest_results = {"mutation": {"applied": True}}  # no "calculations" key
    new_state = manager.record_action(state, _make_action_entry(), latest_results)
    assert new_state.last_total_mass_kg == 4.0, (
        f"last_total_mass_kg should remain 4.0 when calculations absent, got {new_state.last_total_mass_kg}"
    )


def test_load_normalizes_legacy_motors_alias(tmp_path):
    """Bug 63: state.json con 'motors' en current_parameters → load() normaliza a 'motor_count'."""
    import json
    state_data = {
        "project_id": "legacy01",
        "project_slug": "test-legacy",
        "objective": "test legacy",
        "workspace_path": str(tmp_path),
        "current_parameters": {
            "motors": 4,
            "payload_kg": 2.0,
        },
    }
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps(state_data), encoding="utf-8")

    manager = StateManager()
    state = manager.load(state_path)

    assert state.current_parameters.get("motor_count") == 4, (
        "'motors' debe normalizarse a 'motor_count' al cargar estado legacy"
    )
    assert "motors" not in state.current_parameters, (
        "la clave legacy 'motors' no debe quedar en current_parameters tras load()"
    )
