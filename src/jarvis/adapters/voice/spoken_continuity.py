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

T51 (`B1-assistant-voice-brief-spanish`): the project-status phrase and
the top gap title are humanized to Spanish **on this brief path only**.
`readiness.overall`/`prioritized_gaps[0].title` are read exactly as
before — no new field, no ranking change — only the *words spoken* for
those two already-selected pieces change. Screen (`render_startup_context`/
the readiness block) still prints the English `PROJECT STATUS:`/gap
titles verbatim; this module is never imported from any `render_*`
function, so Layer 1 cannot drift from this Buy. An unknown gap title
(not in `_GAP_TITLE_SPEAK_MAP`) is spoken exactly as given — honesty
over invented translation.

T52 (`B1-assistant-voice-full-spoken`): a locked FULL phrase now speaks
`full_spoken_continuity` — the brief plus a narrated body (evidence,
top-3 gaps with Spanish titles and next action, architecture progress,
physical requirements, propulsion/energy block state) — never the
printed wall verbatim. BOM, the readiness table, Conceptos and the
propulsion/hover/endurance detail blocks stay screen-only even on FULL.

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

# T51 (`B1-assistant-voice-brief-spanish`) lock 4 — finite, speak-only
# gap-title map. Keys are the exact English strings `engineering_readiness`
# produces (screen truth, never changed); values are what the brief
# speaks instead. A title not in this map is spoken unchanged (lock 4
# honesty: never invent a translation). Minimum locked set — expanding
# this map is its own future IC, not a silent edit here.
_GAP_TITLE_SPEAK_MAP: dict[str, str] = {
    "Autonomy target not met": "Objetivo de autonomía no alcanzado",
    "Mass limit exceeded": "Límite de masa superado",
    "Parameters blocking simulation": "Parámetros bloquean la simulación",
    "Simulation not PASS": "Simulación no en PASS",
    "Architecture block incomplete": "Bloque de arquitectura incompleto",
}

# T52-N1 hygiene — finite speak-only map of `recommended_next_step.action`
# codes `engineering_readiness` actually emits. Unknown actions pass through
# raw (honesty: never invent). Layer 1 still prints the code.
_ACTION_SPEAK_MAP: dict[str, str] = {
    "list_motors": "listar motores",
    "explore_design_space": "explorar el espacio de diseño",
    "continue_architecture_block": "continuar el bloque de arquitectura",
    "define_component": "definir el componente",
    "complete_component": "completar el componente",
    "fix_simulation_blocker": "resolver el bloqueo de simulación",
    "resolve_requirement": "resolver el requisito",
    "revise_esc_rating": "revisar la calificación del ESC",
    "revise_battery_or_load": "revisar la batería o la carga",
    "revise_propeller_or_motor": "revisar la hélice o el motor",
    "declare_frame_size_class": "declarar la clase de tamaño del chasis",
}


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
    next step / humanized why / Spanish project-status phrase (T51) /
    top gap title (mapped when known, else raw), newline-joined, each
    piece omitted when absent. Returns `""` when there is nothing to
    say (e.g. no active project); callers must treat that as "speak
    nothing" and never fall back to the full wall. Screen Layer 1 still
    prints English `PROJECT STATUS:` — this helper is speak-path only.
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
        if overall == "ASSEMBLY_READY":
            lines.append("Estado del proyecto: listo para ensamblar")
        else:
            lines.append("Estado del proyecto: no listo para ensamblar")

    top_gaps = readiness.get("prioritized_gaps") or []
    if top_gaps:
        title = top_gaps[0].get("title")
        if title:
            lines.append(_GAP_TITLE_SPEAK_MAP.get(title, title))

    return "\n".join(lines)


def full_spoken_continuity(ctx: dict[str, Any] | None) -> str:
    """T52 (`B1-assistant-voice-full-spoken`): what a locked FULL phrase
    speaks — the brief (`brief_spoken_continuity`, unchanged) followed by
    a narrated body built from already-computed `ctx` fields, each section
    omitted when empty:

    A. ``Evidencia:`` — ``continuity.evidence[:6]`` (same cap as print)
    B. ``Huecos prioritarios:`` — ``readiness.prioritized_gaps[:3]``: the
       T51 title map plus ``Siguiente: <action>`` only; never ``gap_id`` /
       ``depends_on`` / ``severity`` / ``blocks``
    C. ``Arquitectura <progress>. Siguiente bloque: <label>`` (+ `` en
       progreso`` when ``next_block_status == "in_progress"``) or
       ``Arquitectura <progress>. Completa.``
    D. ``Requisitos físicos:`` — ``physical_requirements_lines``
    E. ``Bloque propulsión y energía: cerrado.`` / ``no cerrado.``

    Screen-only even on FULL (never spoken here): BOM lines, the readiness
    subsystem table, Conceptos, propulsion/hover/endurance detail blocks,
    the English ``PROJECT STATUS`` line. No LLM, no new computation — a
    deterministic extract; Layer 1 (print) is never touched. Returns
    ``""`` when there is no active project, same as the brief.
    """
    if not ctx or not ctx.get("has_project"):
        return ""

    lines: list[str] = []
    brief = brief_spoken_continuity(ctx)
    if brief:
        lines.append(brief)

    continuity = ctx.get("continuity") or {}
    evidence = [item for item in (continuity.get("evidence") or [])[:6] if item]
    if evidence:
        lines.append("Evidencia:")
        lines.extend(evidence)

    readiness = ctx.get("readiness") or {}
    gap_lines: list[str] = []
    for gap in (readiness.get("prioritized_gaps") or [])[:3]:
        title = gap.get("title")
        if title:
            gap_lines.append(_GAP_TITLE_SPEAK_MAP.get(title, title))
        action = (gap.get("recommended_next_step") or {}).get("action")
        if action:
            gap_lines.append(f"Siguiente: {_ACTION_SPEAK_MAP.get(action, action)}")
    if gap_lines:
        lines.append("Huecos prioritarios:")
        lines.extend(gap_lines)

    arch_progress = ctx.get("architecture_progress")
    if arch_progress:
        arch_label = ctx.get("next_architecture_label")
        if arch_label:
            status_tag = " en progreso" if ctx.get("next_block_status") == "in_progress" else ""
            lines.append(f"Arquitectura {arch_progress}. Siguiente bloque: {arch_label}{status_tag}")
        else:
            lines.append(f"Arquitectura {arch_progress}. Completa.")

    req_lines = [line for line in (ctx.get("physical_requirements_lines") or []) if line]
    if req_lines:
        lines.append("Requisitos físicos:")
        lines.extend(req_lines)

    block_closure = ctx.get("prop_energy_block_closure")
    if block_closure:
        if block_closure.get("status") == "closed":
            lines.append("Bloque propulsión y energía: cerrado.")
        else:
            lines.append("Bloque propulsión y energía: no cerrado.")

    return "\n".join(lines)


def spoken_text_for_wall(raw_text: str, printed_wall: str, ctx: dict[str, Any] | None) -> str:
    """What `run_chat` should hand to `speak(...)` for a Continuity-wall
    turn: `full_spoken_continuity(ctx)` when `raw_text` is a locked FULL
    request (per-turn only), else `brief_spoken_continuity(ctx)`.

    T52: FULL no longer speaks `printed_wall` verbatim — that read the
    screen like OCR (FN-017). `printed_wall` is kept in the signature so
    the `run_chat` call sites stay untouched, but it is never spoken. The
    print side is never touched either way — Layer 1 stays whatever
    `render_startup_context`/`render_response` already produced."""
    if is_full_continuity_request(raw_text):
        return full_spoken_continuity(ctx)
    return brief_spoken_continuity(ctx)
