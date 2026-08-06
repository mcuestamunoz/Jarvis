from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from jarvis.config import DEFAULT_WORKSPACE_ROOT
from jarvis.schemas.action_schema import CreateProjectParams
from jarvis.schemas.state_schema import ProjectState
from jarvis.workspace.file_writer import append_jsonl, write_json, write_text
from jarvis.workspace.render_views import (
    render_estado_actual,
    render_objetivo,
    render_reasoning,
    render_sistema,
)


class WorkspaceManager:
    """Gestiona el workspace de un proyecto.

    Estructura del workspace:
        project/
        ├── state.json                ← ÚNICA fuente de verdad
        ├── views/                    ← representaciones read-only (generadas)
        │   ├── objetivo.md
        │   ├── sistema.md
        │   ├── estado_actual.md
        │   └── reasoning.md
        ├── history/                  ← trazabilidad append-only
        │   ├── events.jsonl          ← log de eventos del sistema
        │   ├── iterations/           ← snapshots de iteraciones (JSON)
        │   ├── simulations/          ← resultados de simulación (JSON)
        │   └── calculations/         ← resultados de cálculo standalone (JSON)
        └── meta/
            └── project_config.json
    """

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or DEFAULT_WORKSPACE_ROOT

    # ── Creación ──────────────────────────────────────────────────────────────

    def create_project_workspace(self, params: CreateProjectParams) -> tuple[Path, ProjectState]:
        slug = params.project_slug or self._slugify(params.objective)
        project_id = uuid4().hex[:12]
        project_path = self.root / f"{slug}-{project_id}"

        for relative in (
            "views",
            "history/iterations",
            "history/simulations",
            "history/calculations",
            "meta",
        ):
            (project_path / relative).mkdir(parents=True, exist_ok=True)

        # Exclude project_slug from current_parameters: it is always None here (slug is
        # derived from objective by _slugify) and already lives on ProjectState.project_slug.
        # Remap API-facing key 'motors' (motor count integer) to canonical internal key
        # 'motor_count', avoiding collision with components["motors"] (ComponentSpec).
        _PARAMS_NOT_CALC_INPUTS = frozenset({"project_slug"})
        _params_dict = params.model_dump()
        if "motors" in _params_dict:
            _params_dict["motor_count"] = _params_dict.pop("motors")
        state = ProjectState(
            project_id=project_id,
            project_slug=slug,
            objective=params.objective,
            workspace_path=str(project_path),
            current_parameters={k: v for k, v in _params_dict.items() if k not in _PARAMS_NOT_CALC_INPUTS},
        )
        write_json(
            project_path / "meta" / "project_config.json",
            {"project_id": project_id, "slug": slug, "objective": params.objective},
        )
        self.save_state(state)
        return project_path, state

    # ── Estado ────────────────────────────────────────────────────────────────

    def save_state(self, state: ProjectState) -> None:
        write_json(Path(state.workspace_path) / "state.json", state.model_dump())

    # ── Historial ─────────────────────────────────────────────────────────────

    def save_simulation(self, workspace_path: Path, sim_id: int, payload: dict) -> Path:
        """Guarda un resultado de simulación en history/simulations/sim_NNN.json."""
        target = workspace_path / "history" / "simulations" / f"sim_{sim_id:03d}.json"
        write_json(target, payload)
        return target

    def save_iteration_snapshot(self, workspace_path: Path, iteration_id: int, payload: dict) -> Path:
        """Guarda un snapshot de iteración en history/iterations/iter_NNN.json.

        El payload es libre; convencionalmente incluye:
          iteration_id, event, change, mutation, impact, calculations, simulation.
        """
        target = workspace_path / "history" / "iterations" / f"iter_{iteration_id:03d}.json"
        write_json(target, payload)
        return target

    def save_calculation(self, workspace_path: Path, calc_id: int, payload: dict) -> Path:
        """Guarda un resultado de cálculo standalone en history/calculations/calc_NNN.json."""
        target = workspace_path / "history" / "calculations" / f"calc_{calc_id:03d}.json"
        write_json(target, payload)
        return target

    def append_event(self, workspace_path: Path, event_type: str, data: dict) -> None:
        """Añade un evento al log append-only history/events.jsonl."""
        append_jsonl(workspace_path / "history" / "events.jsonl", {"type": event_type, **data})

    # ── Vistas ────────────────────────────────────────────────────────────────

    def render_views(
        self,
        workspace_path: Path,
        state: ProjectState,
        reasoning_dict: dict | None = None,
    ) -> None:
        """Regenera todas las vistas derivadas del estado actual.

        Las vistas son siempre derivadas — nunca se editan manualmente.
        """
        views = workspace_path / "views"
        write_text(views / "objetivo.md", render_objetivo(state))
        write_text(views / "sistema.md", render_sistema(state))
        write_text(views / "estado_actual.md", render_estado_actual(state))
        if reasoning_dict is not None:
            write_text(views / "reasoning.md", render_reasoning(reasoning_dict))

    # ── Resolución de rutas ───────────────────────────────────────────────────

    def resolve_state_path(
        self,
        project_id: str | None = None,
        workspace_path: str | None = None,
        project_slug: str | None = None,
    ) -> Path:
        if workspace_path:
            state_path = Path(workspace_path) / "state.json"
            if not state_path.exists():
                raise FileNotFoundError(f"No existe state.json en {workspace_path}")
            return state_path

        candidates = self._list_state_paths()
        if not candidates:
            raise FileNotFoundError("No hay proyectos creados en el workspace.")

        if project_id:
            for candidate in candidates:
                if candidate.parent.name.endswith(f"-{project_id}"):
                    return candidate
            raise FileNotFoundError(f"No se encontró proyecto con id {project_id}")

        if project_slug:
            for candidate in candidates:
                if candidate.parent.name.startswith(f"{project_slug}-"):
                    return candidate
            raise FileNotFoundError(f"No se encontró proyecto con slug {project_slug}")

        return max(candidates, key=lambda candidate: candidate.stat().st_mtime)

    def _list_state_paths(self) -> list[Path]:
        if not self.root.exists():
            return []
        return [
            path / "state.json"
            for path in self.root.iterdir()
            if path.is_dir() and (path / "state.json").exists()
        ]

    # ── Runtime snapshot (U4) ─────────────────────────────────────────────────

    _MAX_CONVERSATION_SNAPSHOT = 50

    def save_runtime_snapshot(
        self,
        workspace_path: Path,
        history: list[dict],
        session_snapshot: dict,
    ) -> None:
        """U4: persiste historial + estado de sesión mínimo en history/runtime_snapshot.json."""
        write_json(
            workspace_path / "history" / "runtime_snapshot.json",
            {
                "conversation_history": history[-self._MAX_CONVERSATION_SNAPSHOT :],
                "session": session_snapshot,
            },
        )

    def load_runtime_snapshot(self, workspace_path: Path) -> dict | None:
        """U4: retorna snapshot desde disco, o None si no existe o está corrupto."""
        path = workspace_path / "history" / "runtime_snapshot.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _slugify(self, text: str) -> str:
        normalized = "".join(char.lower() if char.isalnum() else "-" for char in text.strip())
        collapsed = "-".join(part for part in normalized.split("-") if part)
        return collapsed or "proyecto"

