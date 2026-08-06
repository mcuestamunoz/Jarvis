"""Tests for workspace_path repair on StateManager.load."""
from __future__ import annotations

import json
from pathlib import Path

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.state_manager import StateManager
from jarvis.workspace.workspace_manager import WorkspaceManager


def _seed_project(tmp_path: Path, *, legacy_workspace_path: str | None) -> Path:
    """Create a minimal project folder with optional stale workspace_path."""
    project_dir = tmp_path / "demo-project-abcd1234efgh"
    (project_dir / "history" / "iterations").mkdir(parents=True)
    (project_dir / "history" / "simulations").mkdir(parents=True)
    (project_dir / "views").mkdir(parents=True)
    state = {
        "project_id": "abcd1234efgh",
        "project_slug": "demo-project",
        "objective": "demo",
        "workspace_path": legacy_workspace_path if legacy_workspace_path is not None else str(project_dir),
        "active_iteration": 0,
        "current_parameters": {
            "objective": "demo",
            "payload_kg": 1.0,
            "vehicle_type": "dron",
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "structure_mass_factor": 0.6,
            "safety_factor": 1.2,
            "motor_count": 4,
            "per_motor_max_thrust_n": 15.0,
        },
        "history": [],
        "latest_results": {},
    }
    (project_dir / "state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return project_dir


def test_load_repairs_legacy_workspace_path(tmp_path: Path):
    legacy = "/nonexistent/Ingenieria/06_Proyectos/demo-project-abcd1234efgh"
    project_dir = _seed_project(tmp_path, legacy_workspace_path=legacy)
    sm = StateManager()

    loaded = sm.load(project_dir / "state.json")

    assert Path(loaded.workspace_path).resolve() == project_dir.resolve()
    on_disk = json.loads((project_dir / "state.json").read_text(encoding="utf-8"))
    assert Path(on_disk["workspace_path"]).resolve() == project_dir.resolve()


def test_load_repairs_missing_workspace_path(tmp_path: Path):
    project_dir = _seed_project(tmp_path, legacy_workspace_path="")
    # Empty string is falsy → repair
    data = json.loads((project_dir / "state.json").read_text(encoding="utf-8"))
    data["workspace_path"] = ""
    (project_dir / "state.json").write_text(json.dumps(data), encoding="utf-8")

    loaded = StateManager().load(project_dir / "state.json")
    assert Path(loaded.workspace_path).resolve() == project_dir.resolve()


def test_load_idempotent_when_path_already_correct(tmp_path: Path):
    project_dir = _seed_project(tmp_path, legacy_workspace_path=None)
    before = (project_dir / "state.json").read_text(encoding="utf-8")
    loaded = StateManager().load(project_dir / "state.json")
    after = (project_dir / "state.json").read_text(encoding="utf-8")
    assert Path(loaded.workspace_path).resolve() == project_dir.resolve()
    assert before == after


def test_repaired_path_allows_persist(tmp_path: Path):
    legacy = str(tmp_path / "old-root" / "demo-project-abcd1234efgh")
    project_dir = _seed_project(tmp_path, legacy_workspace_path=legacy)
    sm = StateManager()
    wm = WorkspaceManager(root=tmp_path)

    state = sm.load_active_project(wm, project_id="abcd1234efgh")
    target = wm.save_simulation(Path(state.workspace_path), 0, {"status": "pass"})
    assert target.exists()
    assert project_dir in target.parents


def test_define_missing_persists_after_legacy_path_repair(tmp_path: Path):
    """Regression: param wizard complete must not fail mkdir on legacy workspace_path."""
    legacy = "/Users/fake/Ingenieria/06_Proyectos/demo-project-abcd1234efgh"
    project_dir = _seed_project(tmp_path, legacy_workspace_path=legacy)
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    # Touch mtime so load_active_project picks this project
    (project_dir / "state.json").touch()

    orch.start_define_missing_params(
        ["wheel_radius_m", "gear_ratio"],
        reason="missing_transmission_parameters",
    )
    result = orch.param_definition_session.answer("0.15 y 10")
    assert result["status"] == "ok"
    assert (project_dir / "history" / "iterations").exists()
    saved = json.loads((project_dir / "state.json").read_text(encoding="utf-8"))
    assert Path(saved["workspace_path"]).resolve() == project_dir.resolve()
    assert saved["current_parameters"]["wheel_radius_m"] == 0.15
    assert saved["current_parameters"]["gear_ratio"] == 10.0
