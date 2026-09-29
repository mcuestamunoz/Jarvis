"""Assistant Task seam — `B1-assistant-explain-task` (T0), extended by
`B1-assistant-defer-continuity` (T1).

First on-disk `Task` emission per `DC-assistant-first-task`
(`design_contract_assistant_first_task_b0.md`, ★ ACCEPT CLOSED):
`jarvis.intelligence` — the Assistant — classifies an `Intent` into a
`Task` (or refuses honestly), never a second task brain living in the
orchestrator. Reuses `jarvis.capabilities.intent.Task` as-is; no forked
Task type. Two kinds ship here:

- `explain_concept` (T0) — requires `ontology.explain`, fulfilled by
  A3's existing read-only cite path (`jarvis.intelligence.explain`).
- `defer_to_continuity` (T1, `design_contract_assistant_defer_continuity_b0.md`
  ★ ACCEPT CLOSED) — requires `engineering.continuity`, classified from
  a finite, explicit phrase table (`jarvis.config.CONTINUITY_DEFER_PHRASES`,
  a hand-synced copy of `IntentResolver.STATUS_PATTERNS`) and fulfilled
  entirely by `core/`'s existing `_handle_project_status()`. This module
  never formats a Continuity body itself and never imports
  `jarvis.core.intent_resolver`/`jarvis.core.project_continuity` — only
  the finite phrase *strings* are copied into `jarvis.config`, not the
  resolver class. An explain-shaped line always wins over a Continuity-
  shaped one (checked in both directions: the orchestrator's own call
  order, and `try_defer_to_continuity_task`'s own internal guard).

No LLM call anywhere in this module. No Continuity ranking read, no
`jarvis.core` import. See `tests/test_assistant_explain_task_b1.py` T6
and `tests/test_assistant_defer_continuity_b1.py` T6 for the
AST-enforced fence (also: no `jarvis.flight_software` /
`jarvis.vehicle_profiles`).
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

from jarvis.capabilities.intent import Intent, Task
from jarvis.config import CHAT_EXPLAIN_PREFIXES, CONTINUITY_DEFER_PHRASES

CAPABILITY_ONTOLOGY_EXPLAIN = "ontology.explain"
TASK_KIND_EXPLAIN_CONCEPT = "explain_concept"
CAPABILITY_ENGINEERING_CONTINUITY = "engineering.continuity"
TASK_KIND_DEFER_TO_CONTINUITY = "defer_to_continuity"

_LIST_RUNG_REDIRECT = (
    "Eso solo está disponible en terminal: "
    "`jarvis explain --list` / `jarvis explain --rung <KEY>` "
    "no funcionan dentro del chat todavía."
)


def _extract_explain_query(raw_text: str) -> str | None:
    """Same A7 grain, same table: exact `jarvis explain `/`explain `
    prefix (casefold, required trailing space) from
    `jarvis.config.CHAT_EXPLAIN_PREFIXES` — a single shared prefix
    table, not a second copy. Returns the stripped remainder, or `None`
    when `raw_text` isn't explain-shaped at all (never a bare-id or
    craft-phrase steal)."""
    stripped = raw_text.strip()
    normalized = stripped.lower()
    for prefix in CHAT_EXPLAIN_PREFIXES:
        if normalized.startswith(prefix):
            return stripped[len(prefix):].strip()
    return None


def _is_list_or_rung_flag(query: str) -> bool:
    return query.startswith("--list") or query.startswith("--rung")


def try_explain_concept_task(intent: Intent) -> Task | None:
    """Classify `intent` as an `explain_concept` Task, or refuse
    (`None`) for anything not explain-shaped — including a
    `--list`/`--rung` flag-only line, which is explain-shaped but
    deliberately does **not** get a Task (IC §0 row 6: no fake
    `ontology.explain` capability claim for a line nothing is actually
    explaining; the caller still handles it honestly via
    `fulfill_ontology_explain`/`handle_explain_intent`).

    Never calls an LLM, never reads Continuity ranking, never reads
    `ontology/` itself — resolving the query is the provider's job
    (`fulfill_ontology_explain`), not this classifier's.

    Side effect: on a real match, records `task_kind`/`explain_query`
    onto `intent.metadata` in place (IC §0 row 4) — the only state this
    function touches, and only the caller's own `Intent` object.
    """
    query = _extract_explain_query(intent.raw_text)
    if query is None or _is_list_or_rung_flag(query):
        return None
    intent.metadata["task_kind"] = TASK_KIND_EXPLAIN_CONCEPT
    intent.metadata["explain_query"] = query
    return Task(intent_id=intent.id, required_capability_ids=[CAPABILITY_ONTOLOGY_EXPLAIN])


def fulfill_ontology_explain(query: str, *, ontology_root: Path | None = None) -> str:
    """Provider for `ontology.explain`. A `--list`/`--rung` query gets
    the same honest terminal-redirect A7 already used. A resolved query
    returns the full A3 cite text (`format_explain_cite`); an
    unresolved one returns the same honest-miss wording
    `run_explain_cli`'s own stderr already uses — never a raise, never
    an invented note."""
    if _is_list_or_rung_flag(query):
        return _LIST_RUNG_REDIRECT

    from jarvis.intelligence.explain import format_explain_cite, resolve_explain_query

    cite = resolve_explain_query(query, ontology_root=ontology_root)
    if cite is None:
        return (
            f"No solid ontology note for: {query}"
            " (hint: use the note's id, its exact nombre, or a known alias"
            " such as 'c-rate')"
        )
    return format_explain_cite(cite)


def handle_explain_intent(intent: Intent, *, ontology_root: Path | None = None) -> str | None:
    """`try_explain_concept_task` + fulfill in one call — the seam the
    orchestrator's chat-explain branch calls so it never duplicates the
    resolve logic as a parallel primary brain (IC §0 row 7). Returns
    `None` when `intent.raw_text` isn't explain-shaped at all (caller
    falls through to its normal LLM/craft path unchanged). Otherwise
    always returns a message string — including for `--list`/`--rung`
    lines, which are handled here (honest redirect) without a Task ever
    being emitted for them."""
    query = _extract_explain_query(intent.raw_text)
    if query is None:
        return None
    try_explain_concept_task(intent)
    return fulfill_ontology_explain(query, ontology_root=ontology_root)


def _normalize_for_continuity_match(text: str) -> str:
    """Minimal normalize equivalent to `IntentResolver._normalize_text`'s
    accent-stripping (strip + casefold + NFKD accent-strip) — reimplemented
    locally with only the stdlib, never imported from `jarvis.core.
    intent_resolver` (T1 DC/IC fence: this module must not import that
    module or `jarvis.core.project_continuity`)."""
    lowered = text.strip().lower()
    decomposed = unicodedata.normalize("NFKD", lowered)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def try_defer_to_continuity_task(intent: Intent) -> Task | None:
    """Classify `intent` as a `defer_to_continuity` Task, or refuse
    (`None`) when `intent.raw_text` — after a minimal normalize — isn't
    an exact member of `CONTINUITY_DEFER_PHRASES`, **or** when it's
    explain-shaped (explain always wins; a line is never double-tasked).

    Exact-phrase match, deliberately narrower than `IntentResolver`'s
    own word-boundary substring search over a whole sentence (DC §0 row
    6: "no stealing arbitrary craft design chat into this Task") — a
    phrase that doesn't match exactly here still reaches the existing,
    unaffected Continuity/status path through the normal
    `_handle_user_text_inner` chain; this only adds an earlier,
    zero-LLM fast path for a strict subset, it narrows nothing that
    already worked.

    Never calls an LLM, never imports Continuity ranking modules, never
    decides what the fulfilled response looks like — that is entirely
    `core/`'s existing `_handle_project_status()` (DC §0 row 5/§2).

    Side effect: on a match, records `task_kind` onto `intent.metadata`
    in place — the only state this function touches.
    """
    if _extract_explain_query(intent.raw_text) is not None:
        return None
    normalized = _normalize_for_continuity_match(intent.raw_text)
    if normalized not in CONTINUITY_DEFER_PHRASES:
        return None
    intent.metadata["task_kind"] = TASK_KIND_DEFER_TO_CONTINUITY
    return Task(
        intent_id=intent.id,
        required_capability_ids=[CAPABILITY_ENGINEERING_CONTINUITY],
    )
