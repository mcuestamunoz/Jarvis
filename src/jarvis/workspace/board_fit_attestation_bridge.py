"""Board "Declarar verificado" / "Quitar verificación" → Fit attestation
B1 — the ONE Python entry point a Board POST commits through.

Deliberately thin, same shape as ``board_pose_bridge.py``: load
``state.json`` -> call the EXISTING ``set_component_declared_fit_
attestation`` writer (component_writers.py, CLOSED — this module adds no
attestation logic of its own, no second schema) -> save via
``write_json`` at the SAME path -> reproject the SAME projector output the
read-only GET route already returns, so the Vite plugin's response shape
for this POST and for GET stay identical.

Never touches the LLM/orchestrator — a human sign-off write is already
pure/deterministic and needs none of it, same reasoning ``board_pose_
bridge.py`` documents for its own pose write.

No partial save: ``write_json(state_path, …)`` is only reached after
``set_component_declared_fit_attestation`` returns successfully — a
``ValueError`` from the writer (e.g. screening isn't ``overlap``)
propagates untouched, before any disk write.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jarvis.core.component_writers import set_component_declared_fit_attestation
from jarvis.schemas.state_schema import ProjectState
from jarvis.workspace.file_writer import write_json
from jarvis.workspace.spatial_board import project_spatial_nodes


def apply_fit_attestation(state_path: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Load *state_path*, attest/clear the *payload* component via the
    existing writer, save to that **same path**, and return freshly
    projected nodes."""
    component_key = payload.get("component_key")
    if not component_key:
        raise ValueError("'component_key' es obligatorio para declarar o quitar una verificación.")
    attest = bool(payload.get("attest"))

    state_path = Path(state_path)
    state = ProjectState.model_validate_json(state_path.read_text(encoding="utf-8"))
    updated = set_component_declared_fit_attestation(state, component_key, attest=attest)
    # Keep workspace_path coherent with the file we actually wrote.
    if str(state_path.parent.resolve()) != str(Path(updated.workspace_path).resolve()):
        updated = updated.model_copy(update={"workspace_path": str(state_path.parent.resolve())})
    write_json(state_path, updated.model_dump())
    return project_spatial_nodes(updated)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 2:
        sys.stderr.write(
            "usage: python -m jarvis.workspace.board_fit_attestation_bridge <state.json> <json_payload>\n"
        )
        return 2
    state_path = Path(args[0])
    try:
        payload = json.loads(args[1])
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"payload JSON invalido: {exc}\n")
        return 2
    try:
        nodes = apply_fit_attestation(state_path, payload)
    except (ValueError, FileNotFoundError) as exc:
        sys.stderr.write(str(exc))
        return 1
    json.dump({"nodes": nodes}, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
