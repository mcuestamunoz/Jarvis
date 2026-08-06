"""
Domain-agnostic component inference rule system.

A ComponentRule describes how to recognise a component type from freeform text
and extract structured properties from it.  Domain-specific rule registries
(e.g. jarvis/domains/aerial.py) provide lists of ComponentRule objects;
component_inference.py dispatches against the active registry.

Usage
-----
>>> from jarvis.core.component_rules import ComponentRule, PropertyExtractor
>>> from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


# ── Property extraction contract ─────────────────────────────────────────────

@runtime_checkable
class PropertyExtractor(Protocol):
    """Callable that extracts structured properties from normalised input text.

    Must return a ``dict[str, PropertyValue]``.  Return an empty dict when
    nothing relevant is found — never raise.
    """
    def __call__(self, normalized: str) -> dict: ...  # dict[str, PropertyValue]


# ── Completeness evaluator contract ──────────────────────────────────────────

@runtime_checkable
class CompletenessEvaluator(Protocol):
    """Given extracted properties, return "low" | "medium" | "high" and
    a list of missing field names."""
    def __call__(self, props: dict) -> tuple[str, list[str]]: ...


# ── Rule definition ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ComponentRule:
    """Describes how to recognise one component type and extract its properties.

    Fields
    ------
    keywords        Words (lowercased) that trigger this rule in the input text.
                    Any keyword match activates the rule.
    component_type  Semantic type tag (e.g. "propulsion_active").
    suggested_key   Default key used in component_patch (e.g. "motors").
    inference_confidence  Baseline confidence when this rule fires.
    property_extractor    Callable: str → dict[str, PropertyValue].
    completeness_evaluator Callable: dict → (level, missing_fields).
    missing_field_hints   Human-readable prompt when fields are missing.
    extra_hints     Additional hints to surface regardless of completeness.
    """
    keywords: tuple[str, ...]
    component_type: str
    suggested_key: str
    inference_confidence: float
    property_extractor: PropertyExtractor
    completeness_evaluator: CompletenessEvaluator
    missing_field_hints: tuple[str, ...] = field(default_factory=tuple)
    extra_hints: tuple[str, ...] = field(default_factory=tuple)
    # output_magnitude: the property key that represents the physical output of
    # this component type (e.g. "thrust_n" for aerial motors, "torque_nm" for
    # ground actuators).  The resolver reads this to extract the relevant value
    # without hardcoding domain-specific property names.
    output_magnitude: str | None = None

    def matches(self, normalized: str, name_lc: str) -> bool:
        """Return True if any keyword appears in the normalised text or name."""
        return any(kw in normalized or kw in name_lc for kw in self.keywords)


# ── Registry ─────────────────────────────────────────────────────────────────

class ComponentRuleRegistry:
    """Ordered list of ComponentRule objects for a given domain.

    Rules are evaluated in insertion order; the first match wins.
    """

    def __init__(self, rules: list[ComponentRule] | None = None) -> None:
        self._rules: list[ComponentRule] = list(rules or [])

    def register(self, rule: ComponentRule) -> None:
        self._rules.append(rule)

    def match(self, normalized: str, name_lc: str) -> ComponentRule | None:
        """Return the first rule that matches, or None."""
        for rule in self._rules:
            if rule.matches(normalized, name_lc):
                return rule
        return None

    def __len__(self) -> int:
        return len(self._rules)
