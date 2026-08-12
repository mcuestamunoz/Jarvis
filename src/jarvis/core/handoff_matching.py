"""Handoff lever matching — FN-026 (H4).

Pure helper that resolves a user-referenced ``HandoffContext`` lever to a
canonical iterate variable name. Reuses the exact same normalization /
resolution chain ``iterate_interactive_session._apply_answer`` already uses
for step-1 variable resolution — no parallel vocabulary is introduced here.
"""
from __future__ import annotations

from jarvis.core.iterate_domain import (
    _VARIABLE_NORMALIZATION,
    _fuzzy_normalize_variable,
    _is_valid_variable,
    _normalize_variable_input,
)
from jarvis.core.parameter_requirements import normalize_alias
from jarvis.schemas.action_schema import HandoffContext


def match_plan_lever(user_input: str, handoff_context: HandoffContext) -> str | None:
    """Return the canonical variable name if *user_input* names a lever
    belonging to ``handoff_context.levers``, else ``None``.

    Matching order per lever: (1) the full lever string, (2) each of its
    slash-separated tokens, stripped. A candidate only counts if it is both
    referenced (substring, normalized) in the user text AND a valid iterate
    variable per ``_is_valid_variable`` — the same closed-domain gate step 1
    of the wizard already enforces. This rejects compound-lever tokens that
    are derived/computed quantities (e.g. ``total_power_w``) while still
    accepting the settable sibling token (e.g. ``motors``).
    """
    normalized_input = _normalize_variable_input(user_input)
    for lever in handoff_context.levers:
        candidates = [lever] + [token.strip() for token in lever.split("/")]
        for candidate in candidates:
            candidate_norm = _normalize_variable_input(candidate)
            if not candidate_norm:
                continue
            if candidate_norm in normalized_input and _is_valid_variable(candidate):
                raw = normalize_alias(candidate)
                return _VARIABLE_NORMALIZATION.get(raw) or _fuzzy_normalize_variable(raw)
    return None
