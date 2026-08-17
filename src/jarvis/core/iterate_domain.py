"""Domain constants and pure validators for the iterate interactive session.

All symbols here are stateless (no `self` access).  They are imported by
`iterate_interactive_session.py` and may also be imported by tests directly.
"""
from __future__ import annotations

import unicodedata

from jarvis.core.parameter_requirements import (
    build_normalization_map,
    build_semantic_params,
    build_valid_domain,
)
from jarvis.domains.materials import MATERIAL_ALIASES


# Maps user-facing concept words to canonical current_parameters keys.
# Computed from the domain registry (concept_aliases on each entry).
# Distinct from build_alias_map(), which covers display-name aliases for numeric params.
_VARIABLE_NORMALIZATION: dict[str, str] = build_normalization_map()

# Canonical parameter names that must always use the semantic/strategy path at step 2.
# Computed from the domain registry (entries with variable_type=SEMANTIC_MUTATION).
_SEMANTIC_MUTATION_PARAMS: frozenset[str] = build_semantic_params()


def _normalize_variable_input(text: str) -> str:
    """Lowercase + strip diacritics for variable lookup (used for Bug 5 detection)."""
    nfkd = unicodedata.normalize("NFKD", text.lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# Fuzzy substring pairs for step-1 typo correction.
# Each tuple is (substring_keyword, canonical_variable).
# Checked in order; first match wins.
_VARIABLE_FUZZY_PAIRS: list[tuple[str, str]] = [
    ("dimens",    "dimensiones"),
    ("estructur", "estructura"),
    ("material",  "material"),
]


def _fuzzy_normalize_variable(raw: str) -> str:
    """Return the canonical variable if a known keyword is a subsequence of *raw*.

    Uses subsequence matching instead of substring so transposition typos like
    "dimesniones" (s/n swapped) still resolve to "dimensiones".

    Only fires when the exact lookup in _VARIABLE_NORMALIZATION already missed —
    the caller is responsible for trying the exact table first.
    """
    for keyword, canonical in _VARIABLE_FUZZY_PAIRS:
        iterator = iter(raw)
        if all(ch in iterator for ch in keyword):
            return canonical
    return raw


# Structural / lexical wizard terms: NOT system parameters — they activate
# declarative branches in the wizard but have no entry in the domain registry.
_STRUCTURAL_TERMS: frozenset[str] = frozenset({
    "material", "dimensiones", "dimension", "estructura",
    "componentes", "componente", "potencia", "empuje",
})

# Closed domain of valid variables for step 1.
# Computed from the domain registry (canonical names + aliases + concept aliases)
# unioned with structural / lexical wizard terms that live outside the registry.
# Derived variables (e.g. "autonomia") ARE included — they pass here and are
# redirected by get_derived_message(), not rejected outright.
_VALID_VARIABLE_DOMAIN: frozenset[str] = build_valid_domain() | _STRUCTURAL_TERMS


def _is_valid_variable(raw: str) -> bool:
    """Return True if *raw* belongs to the closed domain of modifiable variables.

    Called in step 1 BEFORE writing to the draft.
    The check runs on the normalised (lowercase, diacritics stripped) form so
    accented variants pass without needing explicit entries.
    """
    normalised = _normalize_variable_input(raw)  # lowercase + strip diacritics
    # 1. Exact match in domain
    if normalised in _VALID_VARIABLE_DOMAIN:
        return True
    # 2. After fuzzy normalisation (covers typos) — if result is in domain, accept
    fuzzy = _fuzzy_normalize_variable(normalised)
    if fuzzy != normalised and fuzzy in _VALID_VARIABLE_DOMAIN:
        return True
    # 3. Direct alias mapping (concept words like "carga util")
    if normalised in {k.lower() for k in _VARIABLE_NORMALIZATION}:
        return True
    return False


# Canonical material names recognised in freeform text.
# G10 ★2/★7: single source is jarvis.domains.materials.MATERIAL_ALIASES —
# aerial.py's frame extractor uses the same table. "madera" was removed there
# (no library entry, was an unhandled-KeyError hazard — investigation §5.3)
# and is therefore absent here too.
_KNOWN_MATERIALS: dict[str, str] = MATERIAL_ALIASES
