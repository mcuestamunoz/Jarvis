import os
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_WORKSPACE_ROOT = Path(
    os.getenv("JARVIS_WORKSPACE_ROOT", str(PACKAGE_ROOT.parent.parent / "workspace"))
)
DEFAULT_LLM_LOG_ROOT = PACKAGE_ROOT / "runtime" / "llm_logs"
DEFAULT_SIMULATION_MARGIN = 1.2
DEFAULT_MOTOR_COUNT = 4
DEFAULT_PER_MOTOR_THRUST_N = 15.0
DEFAULT_STRUCTURE_MASS_FACTOR = 0.6
GRAVITY = 9.81
PROMPT_VERSION = "v1"
OLLAMA_BASE_URL = os.getenv("JARVIS_OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CHAT_PATH = os.getenv("JARVIS_OLLAMA_CHAT_PATH", "/api/chat")
OLLAMA_MODEL = os.getenv("JARVIS_OLLAMA_MODEL", "qwen2.5:14b")
OLLAMA_FORMAT = os.getenv("JARVIS_OLLAMA_FORMAT", "json")
OLLAMA_TEMPERATURE = float(os.getenv("JARVIS_OLLAMA_TEMPERATURE", "0"))
OLLAMA_STREAM = os.getenv("JARVIS_OLLAMA_STREAM", "false").lower() == "true"
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("JARVIS_OLLAMA_TIMEOUT_SECONDS", "60"))

# ── Global command word sets ──────────────────────────────────────────────────
# Single source of truth used by orchestrator and session handlers.
ESCAPE_WORDS: frozenset[str] = frozenset({"cancelar", "cancel", "salir", "abortar", "abort", "exit"})
NEW_PROJECT_WORDS: frozenset[str] = frozenset({"n", "nuevo", "nuevo proyecto", "crear"})
