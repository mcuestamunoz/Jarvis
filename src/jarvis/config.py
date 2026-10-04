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
    # T45 (`B1-assistant-chat-spoken-continuity`): three new entries, not
    # previously recognized — added so these locked FULL-speak phrases
    # (jarvis.adapters.voice.spoken_continuity.FULL_CONTINUITY_PHRASES)
    # also resolve to the same project_status handler every other
    # Continuity-defer phrase already uses, instead of falling through
    # to classify/LLM. The other seven FULL phrases were already members
    # above before T45 — only these three are additions.
    "completo",
    "estado completo",
    "cuentame todo",
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
# B1-assistant-vehicle-takeoff-task (T9): fourth vehicle Task kind, same
# discipline as VEHICLE_HOLD_PHRASES/VEHICLE_LAND_PHRASES/
# VEHICLE_GO_TO_PHRASES above — finite, exact match on the normalized
# form, entries stored pre-normalized (already accent-free here).
# Minimum, deliberately narrow seed (DC/IC lock): "takeoff", "take off",
# "despegar", "despega", "despegue", "levanta", "levantar", "sube",
# "ascender".
VEHICLE_TAKEOFF_PHRASES: frozenset[str] = frozenset({
    "takeoff",
    "take off",
    "despegar",
    "despega",
    "despegue",
    "levanta",
    "levantar",
    "sube",
    "ascender",
})
# B1-assistant-vehicle-return-home-task (T10): fifth and closing vehicle
# Task kind, same discipline as the four VEHICLE_*_PHRASES tables above
# — finite, exact match on the normalized form, entries stored
# pre-normalized (already accent-free here). Minimum, deliberately
# narrow seed (DC/IC lock): "return home", "returnhome", "rtl", "rth",
# "vuelve", "volver", "vuelve a casa", "volver a casa", "casa", "home".
# Phrase caution (IC): several of these are short single words — exact-
# match only (never substring), so a longer craft-chat line containing
# one of them (e.g. "volver al board") is never stolen; it simply
# doesn't equal any table entry after normalize. Distinct from, and
# never confused with, config.NAVIGATION_BACK_WORDS below (a separate
# table scoped to acquisition-wizard back-navigation, checked from an
# entirely different code path).
VEHICLE_RETURN_HOME_PHRASES: frozenset[str] = frozenset({
    "return home",
    "returnhome",
    "rtl",
    "rth",
    "vuelve",
    "volver",
    "vuelve a casa",
    "volver a casa",
    "casa",
    "home",
})
# B1-assistant-vehicle-arm-ux (T11): Safety *policy* latch phrases — not an
# AutonomyVerb. Same finite exact-match discipline as the VEHICLE_* tables
# above (entries pre-normalized / accent-free). Short words like "arm"/
# "arma" must not steal craft lines ("arma el frame").
VEHICLE_ARM_PHRASES: frozenset[str] = frozenset({
    "arm",
    "armar",
    "arma",
    "armar safety",
    "armar politica",
    "arm safety",
})
VEHICLE_DISARM_PHRASES: frozenset[str] = frozenset({
    "disarm",
    "desarmar",
    "desarma",
    "disarm safety",
    "desarmar safety",
})
# B1-assistant-vehicle-follow-task (T12): sixth vehicle Task phrase table.
# Exact match only — short words like "sigue"/"follow" must not steal craft
# lines ("sigue con el frame", "follow the board layout").
VEHICLE_FOLLOW_PHRASES: frozenset[str] = frozenset({
    "follow",
    "follow me",
    "seguir",
    "sigue",
    "sigueme",
    "seguirme",
    "ven conmigo",
})
# B1-assistant-vehicle-patrol-task (T13): seventh and last vehicle Task
# phrase table — last C4 AutonomyVerb without a chat Task. Exact match
# only — short words like "patrol"/"patrulla" must not steal craft lines
# ("patrulla del catalogo", "patrol the board layout").
VEHICLE_PATROL_PHRASES: frozenset[str] = frozenset({
    "patrol",
    "patrulla",
    "patrullar",
    "hacer patrulla",
    "start patrol",
    "iniciar patrulla",
})
# B1-assistant-ops-charge-task (T19): first **ops** Task phrase table —
# CHARGE is deliberately NOT an AutonomyVerb (DC §0 row 1). Exact match
# only — short words like "cargar" must not steal mission/payload lines
# ("carga util", "aumentar la carga", "carga util kg").
OPS_CHARGE_PHRASES: frozenset[str] = frozenset({
    "charge",
    "cargar",
    "cargar bateria",
    "cargar la bateria",
    "charge battery",
    "iniciar carga",
})
# FN-016: navigation-back words, scoped to acquisition wizards only (NOT a
# global escape — deliberately not merged into ESCAPE_WORDS/checked outside
# DEFINE_MISSING_PARAMETERS). Values are already accent-normalized; callers
# must normalize user_input the same way before comparing (see
# acquisition_target.is_navigation_back_phrase).
NAVIGATION_BACK_WORDS: frozenset[str] = frozenset({"atras", "volver", "vuelve"})
