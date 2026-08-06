"""Session manager for the Jarvis MCP server.

Maintains a singleton JarvisOrchestrator per session so conversation state
persists across tool calls within the same MCP server process.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# ── Ensure the project root is on sys.path so that `jarvis` is importable ───
# src/jarvis/adapters/mcp/session_manager.py → 4 parents up = src/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from jarvis.config import DEFAULT_WORKSPACE_ROOT  # noqa: E402
from jarvis.core.orchestrator import JarvisOrchestrator  # noqa: E402
from jarvis.llm.llm_client import JarvisLLMInterface  # noqa: E402
from jarvis.llm.ollama_client import OllamaClient  # noqa: E402
from jarvis.adapters.cli.main import render_response, render_startup_context  # noqa: E402

logger = logging.getLogger(__name__)


class JarvisSessionManager:
    """Wraps a single JarvisOrchestrator/LLMInterface pair.

    The MCP server process is kept alive by the host, so this singleton
    persists across multiple tool calls — giving Jarvis real conversational
    memory within a session.
    """

    def __init__(self, workspace_root: Path | None = None) -> None:
        self._workspace_root = workspace_root or DEFAULT_WORKSPACE_ROOT
        self._orchestrator = JarvisOrchestrator(workspace_root=self._workspace_root)
        self._llm = JarvisLLMInterface(client=OllamaClient())
        logger.info("JarvisSessionManager ready. workspace_root=%s", self._workspace_root)

    # ── Public tools ────────────────────────────────────────────────────────

    def chat(self, message: str) -> str:
        """Send a user message to Jarvis and return the formatted response."""
        try:
            result = self._orchestrator.handle_user_text(message, self._llm)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error in handle_user_text")
            return f"Error interno de Jarvis: {exc}"

        if result.get("status") == "error":
            return result.get("message") or "No he entendido la instrucción."
        return render_response(result)

    def get_state(self) -> str:
        """Return the current project state as a JSON string.

        Returns the raw ``state.json`` fields enriched with computed fields
        derived from ``build_startup_context()``:
          - ``phase``             — lifecycle phase ("definition", "simulation", etc.)
          - ``phase_description`` — human-readable phase label
          - ``status_type``       — "blocking" | "warning" | "nominal" | "no_data"
          - ``architecture_progress`` — fraction string, e.g. "2/4" (None if not set)
          - ``suggested_action``  — top suggestion dict or None

        Returns a JSON object with a ``found`` key.  When ``found`` is
        ``false`` no active project exists yet.
        """
        try:
            state_paths = self._orchestrator.workspace_manager._list_state_paths()
            if not state_paths:
                return json.dumps({"found": False, "message": "No hay proyectos todavía."})
            # Most-recently-modified project
            latest = max(state_paths, key=lambda p: p.stat().st_mtime)
            data = json.loads(latest.read_text(encoding="utf-8"))
            data["found"] = True
            # Bug 70: enrich with computed fields from build_startup_context so callers
            # don't need a separate get_context() call just to learn the project phase.
            try:
                ctx = self._orchestrator.build_startup_context()
                if ctx.get("has_project"):
                    _COMPUTED_FIELDS = (
                        "phase",
                        "phase_description",
                        "phase_confidence",
                        "status_type",
                        "architecture_progress",
                        "suggested_action",
                        "proactive_question",
                    )
                    for field in _COMPUTED_FIELDS:
                        if field in ctx:
                            data[field] = ctx[field]
            except Exception:  # noqa: BLE001 — enrichment failure must not break raw state
                logger.warning("get_state: could not enrich with computed fields")
            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error reading state")
            return json.dumps({"found": False, "error": str(exc)})

    def get_context(self) -> str:
        """Return the startup context summary (phase, status, next actions)."""
        try:
            ctx = self._orchestrator.build_startup_context()
            if not ctx.get("has_project"):
                return "No hay proyecto activo. Usa jarvis_chat para crear uno."
            return render_startup_context(ctx)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error building startup context")
            return f"Error al leer el contexto: {exc}"

    def reset_session(self) -> str:
        """Clear conversation history without deleting the project state."""
        try:
            self._orchestrator.state_manager.clear_conversation_history()
            return "Sesión reiniciada. El proyecto sigue intacto."
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error resetting session")
            return f"Error al reiniciar la sesión: {exc}"

    def list_projects(self) -> str:
        """Return a JSON array with the existing projects."""
        try:
            state_paths = self._orchestrator.workspace_manager._list_state_paths()
            projects: list[dict] = []
            for path in sorted(state_paths, key=lambda p: p.stat().st_mtime, reverse=True):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    projects.append(
                        {
                            "project_id": data.get("project_id", "?"),
                            "project_slug": data.get("project_slug", "?"),
                            "objective": data.get("objective", ""),
                            "workspace_path": str(path.parent),
                        }
                    )
                except Exception:  # noqa: BLE001
                    continue
            return json.dumps(projects, indent=2, ensure_ascii=False)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error listing projects")
            return json.dumps({"error": str(exc)})
