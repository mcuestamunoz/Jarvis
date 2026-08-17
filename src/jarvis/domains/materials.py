"""
Shared material alias table — G10.

Single source of alias→canonical mapping for material identity. Canonical
values are the library's own Spanish names (the exact strings
``jarvis.knowledge.library.ComponentLibrary.get_material`` accepts), not a
separate internal vocabulary. Both the frame acquisition extractor
(``jarvis.domains.aerial``) and the iterate material-change flow
(``jarvis.core.iterate_domain``) resolve aliases through this table so a
library material only needs its aliases listed once.

``madera`` is deliberately absent: it has no entry in
``library/materiales/_datos.json`` (G10 investigation §5.3) and is not added
here — only ``library/`` JSON edits can introduce it as a real material.
"""
from __future__ import annotations

# Alias (lowercase, accent-stripped where relevant) → library canonical
# Spanish name. Ordered roughly by material family; lookups sort by alias
# length descending so multi-word aliases win over substrings
# ("fibra de carbono" before "carbono").
MATERIAL_ALIASES: dict[str, str] = {
    "fibra de carbono": "fibra de carbono",
    "carbon fiber": "fibra de carbono",
    "carbono": "fibra de carbono",
    "carbon": "fibra de carbono",
    "cf": "fibra de carbono",
    "aluminio": "aluminio",
    "aluminum": "aluminio",
    "aluminium": "aluminio",
    "alu": "aluminio",
    "titanio": "titanio",
    "titanium": "titanio",
    "acero": "acero",
    "steel": "acero",
    "kevlar": "kevlar",
    "magnesio": "magnesio",
    "plastico": "plástico",
    "plástico": "plástico",
    "plastic": "plástico",
    "abs": "plástico",
    "nylon": "plástico",
    "pvc": "pvc",
}

# Legacy English slugs written by the pre-G10 frame acquisition path
# (aerial.MATERIAL_MAP's old canonical output). Kept only so
# design_utils.get_frame_material can translate already-persisted
# ComponentSpec values — never used as a write target going forward.
LEGACY_MATERIAL_SLUGS: dict[str, str] = {
    "carbon_fiber": "fibra de carbono",
    "aluminum": "aluminio",
    "plastic": "plástico",
}


def resolve_material_alias(text: str) -> str | None:
    """Return the library canonical name for the longest alias found in *text*.

    Case-insensitive. Returns None when no known material alias appears.
    """
    lower = text.lower()
    found: str | None = None
    found_len = 0
    for alias, canonical in MATERIAL_ALIASES.items():
        if alias in lower and len(alias) > found_len:
            found = canonical
            found_len = len(alias)
    return found
