"""Finite alias seed table for `jarvis explain` — `B1-assistant-terminal-canal`.

A frozen `dict[str, str]`, not a search index: keys are exact, casefolded
alias strings; values are the target note's frontmatter `id`. Every
target below was verified `estado: solid` in `ontology/` before being
seeded (IC §1.1 — an alias pointing at a non-solid or missing note must
never be shipped). Expanding this table is a later docs/IC edit, not
fuzzy matching added here.
"""

from __future__ import annotations

EXPLAIN_ALIASES: dict[str, str] = {
    "c-rate": "c-rate-de-bateria",
    "crate": "c-rate-de-bateria",
    "op": "punto-de-operacion-vs-capacidad-intrinseca",
    "operating point": "punto-de-operacion-vs-capacidad-intrinseca",
}
