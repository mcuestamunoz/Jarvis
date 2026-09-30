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
# B1-chat-explain-intercept (A7): prefix match only, space required after the
# prefix — deliberately narrow so a bare ontology id or an unrelated craft
# phrase starting with these words (there are none today) is never stolen.
# Longest-first order matters for a naive startswith loop (not required here
# since neither prefix is a substring-prefix of the other, but kept explicit).
CHAT_EXPLAIN_PREFIXES: tuple[str, ...] = ("jarvis explain ", "explain ")
# B1-assistant-defer-continuity (T1): finite, explicit status/continuity
# phrases — a hand-copy of `IntentResolver.STATUS_PATTERNS`' own string
# values as of tip `v0.6.8` (DC/IC lock: this module stays a leaf, so the
# values are copied here rather than importing `jarvis.core.intent_resolver`
# — that import direction is reserved to `jarvis.core` itself; `jarvis.
# intelligence.assistant_task` also must never import that module). A sync
# test (`tests/test_assistant_defer_continuity_b1.py`) asserts every
# `STATUS_PATTERNS` entry is present here so the two tables cannot silently
# drift. Matching is exact-phrase (after a minimal strip/casefold/accent-
# strip normalize — see `assistant_task._normalize_for_continuity_match`),
# not `IntentResolver`'s own broader word-boundary substring search — a
# narrower, more conservative match on purpose (DC §0 row 6: "no stealing
# arbitrary craft design chat into this Task"). A line that doesn't match
# exactly still reaches the existing, unaffected Continuity/status path
# through the normal `_handle_user_text_inner` chain — this table only adds
# an earlier, zero-LLM fast path for a strict subset, it does not narrow
# what already worked.
CONTINUITY_DEFER_PHRASES: frozenset[str] = frozenset({
    "estado del proyecto",
    "estado proyecto",
    "estado actual",
    "estado",
    "resumen del proyecto",
    "situacion actual",
    "como va el proyecto",
    "donde estamos",
    "donde estoy",
    "que falta",
    "que nos falta",
    "situacion del proyecto",
    "resumen",
    "detalles del proyecto",
    "dame detalles",
    "dame detalles del proyecto",
    "cuentame el proyecto",
    "cuenta el proyecto",
    "explica el proyecto",
    "describe el proyecto",
    "resume el diseno",
    "resume el proyecto",
    "como esta el proyecto",
    "siguiente paso",
    "que hago",
    "como sigo",
    "que puedo hacer",
    "que debo hacer",
    "por donde empiezo",
    "como continuo",
    "y ahora",
    "ahora que",
    "que sigue",
    "donde quedamos",
    "por que no puedo comprar",
    "por que no puedo montar",
    "guiame",
    "guia",
    "guiame hasta",
    "ayudame a completar",
    "como completo",
    "como termino el proyecto",
    "que me falta completar",
    "que me falta",
    "sigamos",
    "vamos con el siguiente",
    "continua",
    "continuamos",
    "siguiente bloque",
})
# B1-assistant-vehicle-hold-task (T6): finite, explicit HOLD phrases —
# same grain as CONTINUITY_DEFER_PHRASES above: exact match on the
# normalized (strip/casefold/accent-strip) form via `assistant_task.
# _normalize_for_continuity_match`, entries stored pre-normalized. A
# minimum, deliberately narrow seed (DC/IC lock — no fuzzy match, no
# stealing arbitrary craft chat): "hold", "mantener", "mantén"/"manten",
# "quédate"/"quedate", "hold position", "mantener posición"/"mantener
# posicion" — the accented originals normalize onto the same entries as
# their accent-free forms, so only the deduplicated normalized set is
# stored here (mirrors CONTINUITY_DEFER_PHRASES' own already-accent-free
# storage convention).
VEHICLE_HOLD_PHRASES: frozenset[str] = frozenset({
    "hold",
    "mantener",
    "manten",
    "quedate",
    "hold position",
    "mantener posicion",
})
# B1-assistant-vehicle-land-task (T7): second vehicle Task kind, same
# discipline as VEHICLE_HOLD_PHRASES above — finite, exact match on the
# normalized form via `assistant_task._normalize_for_continuity_match`,
# entries stored pre-normalized (already accent-free here, so no
# dedup needed). Minimum, deliberately narrow seed (DC/IC lock): "land",
# "aterrizar", "aterriza", "aterrizaje", "baja", "bajar", "descend",
# "descender".
VEHICLE_LAND_PHRASES: frozenset[str] = frozenset({
    "land",
    "aterrizar",
    "aterriza",
    "aterrizaje",
    "baja",
    "bajar",
    "descend",
    "descender",
})
# B1-assistant-vehicle-go-to-task (T8): third vehicle Task kind, same
# discipline as VEHICLE_HOLD_PHRASES/VEHICLE_LAND_PHRASES above — finite,
# exact match on the normalized form, entries stored pre-normalized
# (accented "dirígete"/"dirígete a" normalize onto the accent-free
# entries already listed here, so no separate accented duplicates are
# needed). Minimum, deliberately narrow seed (DC/IC lock): "go to",
# "goto", "go_to", "ve a", "ir a", "dirigete", "dirigete a", "navega",
# "navigate".
VEHICLE_GO_TO_PHRASES: frozenset[str] = frozenset({
    "go to",
    "goto",
    "go_to",
    "ve a",
    "ir a",
    "dirigete",
    "dirigete a",
    "navega",
    "navigate",
})
# FN-016: navigation-back words, scoped to acquisition wizards only (NOT a
# global escape — deliberately not merged into ESCAPE_WORDS/checked outside
# DEFINE_MISSING_PARAMETERS). Values are already accent-normalized; callers
# must normalize user_input the same way before comparing (see
# acquisition_target.is_navigation_back_phrase).
NAVIGATION_BACK_WORDS: frozenset[str] = frozenset({"atras", "volver", "vuelve"})
