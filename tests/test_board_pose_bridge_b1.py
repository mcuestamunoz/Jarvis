"""Board drag → Continuity pose B1 — the Python bridge.

Covers implementation_contract_board_drag_pose_b1.md §3 (Python-side) —
`board_pose_bridge.apply_drag_pose`/`main` is the ONE entry point a Board
POST commits through: load state.json -> `set_component_declared_box_pose`
(unchanged, CLOSED writer) -> `WorkspaceManager.save_state` (same SoT the
CLI itself uses) -> reprint the same projector nodes the GET route
already returns. No LLM, no orchestrator, no second pose schema.

  P1  Valid pose write persists declared_box_pose on disk (tmp project)
  P2  Writer reject (self-origin / disk origin / missing key) -> ValueError,
      no partial save (disk state unchanged)
  P6  Existing Continuity pose CLI tests still green (checked separately,
      full suite)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.board_pose_bridge import apply_drag_pose, main


def _plate_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="frame_plate", completeness="high",
        properties={
            "length_mm": PropertyValue(value=100.0, unit="mm", source="declared"),
            "width_mm": PropertyValue(value=100.0, unit="mm", source="declared"),
            "height_mm": PropertyValue(value=4.0, unit="mm", source="declared"),
        },
    )


def _disk_motors_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="motors", completeness="high",
        properties={"diameter_mm": PropertyValue(value=27.9, unit="mm", source="declared")},
    )


def _battery_spec() -> ComponentSpec:
    return ComponentSpec(suggested_key="battery", completeness="high", properties={})


def _write_project(tmp_path: Path, components: dict) -> Path:
    workspace_path = str(tmp_path / "demo-p1")
    state = ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path=workspace_path,
        design_properties=DesignProperties(components=components),
    )
    state_path = Path(workspace_path) / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(state.model_dump_json(), encoding="utf-8")
    return state_path


def test_p1_valid_pose_write_persists_on_disk(tmp_path: Path):
    state_path = _write_project(tmp_path, {"frame_plate": _plate_spec(), "battery": _battery_spec()})

    nodes = apply_drag_pose(
        state_path, {"component_key": "battery", "origin_key": "frame_plate", "x_mm": 10.0, "y_mm": -5.0}
    )
    battery_node = next(n for n in nodes if n["id"] == "battery")
    assert battery_node["declaredBoxPose"] == {"originKey": "frame_plate", "xMm": 10.0, "yMm": -5.0}

    saved = json.loads(state_path.read_text(encoding="utf-8"))
    saved_pose = saved["design_properties"]["components"]["battery"]["declared_box_pose"]
    assert saved_pose["origin_key"] == "frame_plate"
    assert saved_pose["x_mm"] == 10.0
    assert saved_pose["y_mm"] == -5.0
    assert saved_pose["z_mm"] is None


def test_save_uses_loaded_state_path_even_if_workspace_path_stale(tmp_path: Path):
    """Hotfix: Board Vite resolves one path; stale workspace_path must not divert the write."""
    state_path = _write_project(tmp_path, {"frame_plate": _plate_spec(), "battery": _battery_spec()})
    raw = json.loads(state_path.read_text(encoding="utf-8"))
    raw["workspace_path"] = str(tmp_path / "other-folder-never-created")
    state_path.write_text(json.dumps(raw), encoding="utf-8")

    apply_drag_pose(
        state_path, {"component_key": "battery", "origin_key": "frame_plate", "x_mm": 3.0, "y_mm": 0.0, "z_mm": 1.0}
    )
    saved = json.loads(state_path.read_text(encoding="utf-8"))
    assert saved["design_properties"]["components"]["battery"]["declared_box_pose"]["x_mm"] == 3.0
    assert saved["workspace_path"] == str(state_path.parent.resolve())
    assert not (tmp_path / "other-folder-never-created").exists()


def test_p2_writer_rejects_self_origin_no_partial_save(tmp_path: Path):
    state_path = _write_project(tmp_path, {"battery": _battery_spec()})
    before = state_path.read_text(encoding="utf-8")

    with pytest.raises(ValueError, match="origen de su propia pose"):
        apply_drag_pose(state_path, {"component_key": "battery", "origin_key": "battery", "x_mm": 1.0})

    assert state_path.read_text(encoding="utf-8") == before


def test_p2_writer_rejects_disk_origin_no_partial_save(tmp_path: Path):
    state_path = _write_project(tmp_path, {"motors": _disk_motors_spec(), "battery": _battery_spec()})
    before = state_path.read_text(encoding="utf-8")

    with pytest.raises(ValueError, match="no tiene una caja declarada"):
        apply_drag_pose(state_path, {"component_key": "battery", "origin_key": "motors", "x_mm": 1.0})

    assert state_path.read_text(encoding="utf-8") == before


def test_p2_missing_component_key_or_origin_key_raises(tmp_path: Path):
    state_path = _write_project(tmp_path, {"frame_plate": _plate_spec(), "battery": _battery_spec()})

    with pytest.raises(ValueError):
        apply_drag_pose(state_path, {"origin_key": "frame_plate", "x_mm": 1.0})

    with pytest.raises(ValueError):
        apply_drag_pose(state_path, {"component_key": "battery", "x_mm": 1.0})


def test_missing_project_file_raises(tmp_path: Path):
    missing = tmp_path / "nope" / "state.json"
    with pytest.raises(FileNotFoundError):
        apply_drag_pose(missing, {"component_key": "battery", "origin_key": "frame_plate", "x_mm": 1.0})


def test_cli_main_happy_path_returns_zero_and_prints_nodes(tmp_path: Path, capsys):
    state_path = _write_project(tmp_path, {"frame_plate": _plate_spec(), "battery": _battery_spec()})
    rc = main([str(state_path), json.dumps({"component_key": "battery", "origin_key": "frame_plate", "x_mm": 5.0})])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    battery_node = next(n for n in payload["nodes"] if n["id"] == "battery")
    assert battery_node["declaredBoxPose"]["xMm"] == 5.0


def test_cli_main_writer_reject_returns_nonzero(tmp_path: Path, capsys):
    state_path = _write_project(tmp_path, {"battery": _battery_spec()})
    rc = main([str(state_path), json.dumps({"component_key": "battery", "origin_key": "battery", "x_mm": 1.0})])
    assert rc == 1
    assert "propia pose" in capsys.readouterr().err
