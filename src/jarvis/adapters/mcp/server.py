"""Jarvis MCP server.

Exposes Jarvis engineering assistant as MCP tools so that Copilot (and other
MCP clients) can chat with Jarvis, inspect project state, and reset sessions.

IMPORTANT (stdio transport):  NEVER use print() — it corrupts JSON-RPC.
All diagnostic output goes to sys.stderr via the standard logging module.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ── Logging to stderr only (stdout is reserved for JSON-RPC) ────────────────
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(levelname)s [jarvis-mcp] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Ensure project root is on sys.path ──────────────────────────────────────
# src/jarvis/adapters/mcp/server.py → 4 parents up = src/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ── Import after sys.path is set ────────────────────────────────────────────
from jarvis.adapters.mcp.session_manager import JarvisSessionManager  # noqa: E402

# ── FastMCP server instance ──────────────────────────────────────────────────
mcp = FastMCP(
    "jarvis",
    instructions=(
        "Jarvis is an engineering design assistant specialised in aerial robotics. "
        "Use jarvis_chat to send instructions in Spanish (e.g. 'quiero diseñar un dron', "
        "'itera reduciendo masa', 'calcula', 'simula'). "
        "Use jarvis_get_context to understand the current project status before sending a message. "
        "Use jarvis_get_state to inspect the raw project parameters as JSON. "
        "Use jarvis_list_projects to see existing projects. "
        "Use jarvis_reset_session to clear conversation history without losing project data."
    ),
)

# Lazy singleton — created once the server process starts
_manager: JarvisSessionManager | None = None


def _get_manager() -> JarvisSessionManager:
    global _manager
    if _manager is None:
        logger.info("Initialising JarvisSessionManager…")
        _manager = JarvisSessionManager()
        logger.info("JarvisSessionManager ready.")
    return _manager


# ── Tools ────────────────────────────────────────────────────────────────────


@mcp.tool()
def jarvis_chat(message: str) -> str:
    """Send a message to Jarvis and get its response.

    Write instructions in Spanish just as you would in the CLI:
    - "quiero diseñar un dron que levante 2 kg"
    - "itera reduciendo masa"
    - "calcula"
    - "simula"
    - "estado"
    - "explorar autonomia"

    Args:
        message: The instruction to send to Jarvis.

    Returns:
        Jarvis's formatted response.
    """
    logger.info("jarvis_chat called: %r", message[:120])
    return _get_manager().chat(message)


@mcp.tool()
def jarvis_get_state() -> str:
    """Return the active project state as a JSON string.

    The JSON contains all design parameters (mass, motors, sensors, etc.),
    iteration counter, simulation results, and project metadata.

    Returns:
        JSON string with the project state, or a message if no project exists.
    """
    logger.info("jarvis_get_state called")
    return _get_manager().get_state()


@mcp.tool()
def jarvis_get_context() -> str:
    """Return a concise summary of the current project status.

    Shows the project name, objective, design phase, simulation status,
    active variable values, and the suggested next action.

    Returns:
        Human-readable context block, or a message if no project exists.
    """
    logger.info("jarvis_get_context called")
    return _get_manager().get_context()


@mcp.tool()
def jarvis_reset_session() -> str:
    """Clear the current conversation history without deleting the project.

    Use this to start a fresh conversation turn while keeping all design
    parameters and iteration history intact.

    Returns:
        Confirmation message.
    """
    logger.info("jarvis_reset_session called")
    return _get_manager().reset_session()


@mcp.tool()
def jarvis_list_projects() -> str:
    """List all existing Jarvis projects.

    Returns:
        JSON array with project_id, project_slug, objective, and
        workspace_path for each project.
    """
    logger.info("jarvis_list_projects called")
    return _get_manager().list_projects()


# ── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("Starting Jarvis MCP server (stdio transport)…")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
