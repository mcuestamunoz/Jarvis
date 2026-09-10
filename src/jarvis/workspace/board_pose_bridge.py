"""Board drag → Continuity pose B1 — the ONE Python entry point a Board
POST commits through.

Deliberately thin: load `state.json` → call the EXISTING
``set_component_declared_box_pose`` writer (component_writers.py, CLOSED —
this module adds no pose logic of its own, no second schema) → save via
the SAME ``WorkspaceManager.save_state`` the CLI itself uses → reprint the
SAME projector output the read-only GET route already returns, so the
Vite plugin's response shape for POST and GET stay identical.

Never touches the LLM/orchestrator — Continuity pose writing is already
pure/deterministic and needs none of it (mirrors the investigation
report's own finding: a full orchestrator round-trip is unnecessary
weight for a write this narrow).

No partial save: ``write_json(state_path, …)`` is only reached after
``set_component_declared_box_pose`` returns successfully — a ``ValueError``
from the writer propagates untouched, before any disk write.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jarvis.core.component_writers import set_component_declared_box_pose
from jarvis.schemas.action_schema import DeclaredBoxPose
from jarvis.schemas.state_schema import ProjectState
from jarvis.workspace.file_writer import write_json
from jarvis.workspace.spatial_board import project_spatial_nodes


def apply_drag_pose(state_path: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Load *state_path*, write the pose *payload* names via the existing
    writer, save to that **same path**, and return freshly projected nodes.

    Persist uses ``write_json(state_path, …)`` — not ``WorkspaceManager.save_state``
    alone — so a stale/mismatched ``state.workspace_path`` cannot silently
    write another folder while the Board re-GETs the file Vite resolved.
    """
    component_key = payload.get("component_key")
    if not component_key:
        raise ValueError("'component_key' es obligatorio para fijar una pose por arrastre.")
    origin_key = payload.get("origin_key")
    if not origin_key:
        raise ValueError("'origin_key' es obligatorio — el arrastre solo declara SET, nunca invento origen.")

    state_path = Path(state_path)
    state = ProjectState.model_validate_json(state_path.read_text(encoding="utf-8"))
    pose = DeclaredBoxPose(
        origin_key=origin_key,
        x_mm=payload.get("x_mm"),
        y_mm=payload.get("y_mm"),
        z_mm=payload.get("z_mm"),
    )
    updated = set_component_declared_box_pose(state, component_key, pose)
    # Keep workspace_path coherent with the file we actually wrote.
    if str(state_path.parent.resolve()) != str(Path(updated.workspace_path).resolve()):
        updated = updated.model_copy(update={"workspace_path": str(state_path.parent.resolve())})
    write_json(state_path, updated.model_dump())
    return project_spatial_nodes(updated)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 2:
        sys.stderr.write("usage: python -m jarvis.workspace.board_pose_bridge <state.json> <json_payload>\n")
        return 2
    state_path = Path(args[0])
    try:
        payload = json.loads(args[1])
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"payload JSON invalido: {exc}\n")
        return 2
    try:
        nodes = apply_drag_pose(state_path, payload)
    except (ValueError, FileNotFoundError) as exc:
        sys.stderr.write(str(exc))
        return 1
    json.dump({"nodes": nodes}, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
