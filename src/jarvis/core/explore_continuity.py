"""G3 — Active Goal Continuity for Explore.

Design authority: .jes/artifacts/design_g3_active_goal_continuity.md (CLOSED, ★1-★4).

Precedence between an active HandoffContext's goal and a goal freshly
derived from a single explore-shaped message:

    explicit new goal  >  active goal (continuation)  >  inferred/default goal

Root problem this closes: `goal_planner.detect_goal` has no notion of
conversational continuity — a bare/undirected domain phrase like
"optimiza payload" always re-derives from scratch, and F-1's own bare-
dimension default (no explicit direction word → aumentar_payload) can
silently invert an active `reducir_payload` plan. This is a precedence
problem between the active HandoffContext and a freshly re-derived text
goal, not a goal_planner bug — F-1's bare default is correct and untouched.

Reuses goal_planner's own direction machinery (`_direction_of`, `_normalize`)
for override detection — no parallel synonym/NLP layer, per Design §5.
"""
from __future__ import annotations

from jarvis.core.goal_planner import _direction_of, _normalize
from jarvis.schemas.action_schema import HandoffContext

# Minimal dimension-family table — only what explore-path precedence needs
# (Design §3). Do not rebuild goal_planner's own keyword/direction tables
# here; this only groups already-resolved goal_key values.
_DIMENSION_FAMILIES: dict[str, frozenset[str]] = {
    "payload": frozenset({"aumentar_payload", "reducir_payload"}),
    "mass": frozenset({"reducir_masa"}),
    "autonomy": frozenset({"mejorar_autonomia"}),
    "stability": frozenset({"mejorar_estabilidad"}),
}


def _family_of(goal_key: str) -> str | None:
    for family, members in _DIMENSION_FAMILIES.items():
        if goal_key in members:
            return family
    return None


def _same_dimension_family(goal_a: str, goal_b: str) -> bool:
    family_a = _family_of(goal_a)
    return family_a is not None and family_a == _family_of(goal_b)


def resolve_explore_goal_with_handoff(
    user_input: str,
    text_goal: str | None,
    handoff: HandoffContext | None,
) -> str | None:
    """Resolve the goal an explore-shaped turn should use.

    Pure, testable, text-in/goal-out — no I/O, no session mutation (the
    caller, `orchestrator._handle_explore`, owns all state effects).

    Rules (Design §4):
      1. No bindable handoff -> text_goal (today's behavior unchanged).
      2. text_goal is None -> handoff.goal_key (H1, unchanged).
      3. text_goal == handoff.goal_key -> text_goal (trivially agree).
      4. Same dimension family, and the RAW TEXT carries no explicit
         increase/decrease word -> handoff.goal_key (★1: an undirected/soft
         domain phrase like "optimiza payload" is a continuation, never a
         silent inversion of the active goal).
      5. Otherwise -> text_goal (★2: different dimension always overrides;
         same-family WITH an explicit direction word is a deliberate,
         stated override, e.g. "ahora aumenta el payload").

    Note on rule 4/5: whether an explicit direction word is present in the
    text is checked directly (via goal_planner._direction_of on the raw
    input), not by comparing text_goal against handoff.goal_key as an
    "opposite pair" lookup — detect_goal's own bare-dimension default
    collapses both an undirected phrase ("optimiza payload") and an
    explicit-but-still-produces-the-same-enum-value phrase to the identical
    text_goal, so the enum value alone cannot distinguish continuation from
    override. The raw text is the only place that distinction still exists.
    """
    if handoff is None:
        return text_goal
    if text_goal is None:
        return handoff.goal_key
    if text_goal == handoff.goal_key:
        return text_goal
    if _same_dimension_family(text_goal, handoff.goal_key):
        if _direction_of(_normalize(user_input)) is None:
            return handoff.goal_key
    return text_goal
