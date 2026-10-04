"""Skill-first phase C — V7 (`B1-assistant-chat-spoken-continuity`, T45).

Layer 2 **speak-path** extractor over T43's `--chat --voice-speak` seam.
Layer 1 (print) stays exactly `render_startup_context`/`render_response`'s
full Continuity wall — nothing here ever formats, shortens, or
substitutes for the screen truth; this module is called only from the
*speak* side of `run_chat`'s two Continuity-wall sites (project load and
`action == "project_status"` turns, e.g. `estado`), never from the print
side.

`brief_spoken_continuity` extracts five already-computed fields
(`continuity.situation` / `next_useful_step` / `next_useful_why` /
`readiness.overall` / `readiness.prioritized_gaps[0].title`) — no LLM, no
new computation, no ranking change (`T44-DC` lock 4/5). Everything else
(`evidence`, BOM/component lines, the readiness subsystem table,
propulsion/hover/endurance blocks, `explain_topics`, the block-closure
paragraph) stays out of the brief by design.

`is_full_continuity_request` matches the same locked, finite FULL-phrase
set the Engineer gave (`completo`, `dame detalles`, …) against the same
minimal normalize `jarvis.intelligence.assistant_task.
_normalize_for_continuity_match` uses for `CONTINUITY_DEFER_PHRASES` —
reimplemented locally here (stdlib only) rather than imported, mirroring
that module's own documented reason for not importing a sibling
normalize helper across a DC/IC fence. Per-turn only: callers must never
persist a "always full" choice onto session state (T44-DC lock 6).
"""

from __future__ import annotations

import unicodedata
from typing import Any

# Locked FULL set (T44-DC lock 6 / T45 IC lock 6) — finite, zero-LLM,
# pre-normalized (already accent-free, lowercase) the same storage
# convention `CONTINUITY_DEFER_PHRASES` (jarvis/config.py) already uses.
# Seven of these ten are also members of CONTINUITY_DEFER_PHRASES
# (promoted from brief to full here, not duplicated classification);
# "completo"/"estado completo"/"cuentame todo" were newly added to that
# same frozenset by this Buy so they resolve to project_status at all.
FULL_CONTINUITY_PHRASES: frozenset[str] = frozenset({
    "completo",
    "estado completo",
    "dame detalles",
    "dame detalles del proyecto",
    "detalles del proyecto",
    "cuentame todo",
    "cuentame el proyecto",
    "cuenta el proyecto",
    "describe el proyecto",
    "explica el proyecto",
})


def _normalize(text: str) -> str:
    """Same minimal normalize as `assistant_task._normalize_for_
    continuity_match` (strip + casefold + NFKD accent-strip) —
    reimplemented locally rather than imported; see module docstring."""
    lowered = text.strip().lower()
    decomposed = unicodedata.normalize("NFKD", lowered)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def is_full_continuity_request(raw_text: str) -> bool:
    """True when `raw_text`, after the normalize above, exactly matches
    one of the locked `FULL_CONTINUITY_PHRASES`. Per-turn only — the
    caller decides what to speak for *this* turn; nothing here reads or
    writes session state."""
    return _normalize(raw_text) in FULL_CONTINUITY_PHRASES


def brief_spoken_continuity(ctx: dict[str, Any] | None) -> str:
    """Deterministic brief extract of a `build_startup_context`-shaped
    `ctx` (the same shape for a project-load `startup_ctx` and a
    `project_status` turn's `result["startup_context"]`) — situation /
    next step / humanized why / `PROJECT STATUS: …` / top gap title,
    newline-joined, each piece omitted when absent. Returns `""` when
    there is nothing to say (e.g. no active project); callers must treat
    that as "speak nothing" and never fall back to the full wall.
    """
    if not ctx or not ctx.get("has_project"):
        return ""

    from jarvis.adapters.cli.main import _humanize_next_useful_why

    continuity = ctx.get("continuity") or {}
    situation = continuity.get("situation")
    next_step = continuity.get("next_useful_step")
    next_why = continuity.get("next_useful_why")

    lines: list[str] = []
    if situation:
        lines.append(situation)
    if next_step:
        lines.append(next_step)
        if next_why:
            lines.append(_humanize_next_useful_why(next_why))

    readiness = ctx.get("readiness") or {}
    overall = readiness.get("overall")
    if overall:
        status_text = "ASSEMBLY READY" if overall == "ASSEMBLY_READY" else "NOT ASSEMBLY READY"
        lines.append(f"PROJECT STATUS: {status_text}")

    top_gaps = readiness.get("prioritized_gaps") or []
    if top_gaps:
        title = top_gaps[0].get("title")
        if title:
            lines.append(title)

    return "\n".join(lines)


def spoken_text_for_wall(raw_text: str, printed_wall: str, ctx: dict[str, Any] | None) -> str:
    """What `run_chat` should hand to `speak(...)` for a Continuity-wall
    turn: the exact `printed_wall` string when `raw_text` is a locked
    FULL request (per-turn only), else `brief_spoken_continuity(ctx)`.
    The print side is never touched either way — Layer 1 stays whatever
    `render_startup_context`/`render_response` already produced."""
    if is_full_continuity_request(raw_text):
        return printed_wall
    return brief_spoken_continuity(ctx)
