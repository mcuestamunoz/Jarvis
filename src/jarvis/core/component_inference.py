"""
Domain-agnostic component inference dispatcher.

``infer_component`` matches a freeform text description against a
``ComponentRuleRegistry`` and delegates property extraction + completeness
evaluation to the matching rule.  The default registry is ``aerial_registry``
(backward-compatible), but any registry can be injected for other domains.

``infer_components`` (D7) splits mixed phrases so motors + hélices in one
message are both recovered instead of first-match-wins. Same-key segments
merge properties so ``4 motores 920KV y 15N`` keeps thrust.
"""
from __future__ import annotations

import re

from jarvis.core.component_rules import ComponentRule, ComponentRuleRegistry
from jarvis.domains.aerial import aerial_registry
from jarvis.schemas.action_schema import ComponentSpec


# Default registry — aerial domain for backward compatibility.
# Replace or extend by passing a custom registry to infer_component().
_DEFAULT_REGISTRY: ComponentRuleRegistry = aerial_registry

# Split mixed freeform descriptions: "4 motores 920KV, hélices 10x4.5"
_COMPONENT_SPLIT_RE = re.compile(
    r"\s*(?:,|;|/|\+| y |\s+e\s+)\s*",
    re.IGNORECASE,
)
_LOOKS_LIKE_MOTOR_RE = re.compile(
    r"(?:\b\d+\s*kv\b|\b\d+\s*x\s*\d{3,4}\b|\b\d+\s*n\b)",
    re.IGNORECASE,
)


def _spec_from_rule(raw_name: str, rule: ComponentRule, normalized: str) -> ComponentSpec:
    props = rule.property_extractor(normalized)
    completeness, missing_fields = rule.completeness_evaluator(props)
    hints = list(rule.missing_field_hints) if missing_fields else []
    hints += list(rule.extra_hints)
    return ComponentSpec(
        name=raw_name.strip(),
        suggested_key=rule.suggested_key,
        component_type=rule.component_type,
        inference_confidence=rule.inference_confidence,
        properties=props,
        completeness=completeness,
        missing_fields=missing_fields,
        hints=hints,
        output_magnitude=rule.output_magnitude,
    )


def infer_component(
    raw_name: str,
    raw_value: str | None = None,
    registry: ComponentRuleRegistry | None = None,
) -> ComponentSpec:
    """Infer a ComponentSpec from freeform text using the active rule registry.

    Parameters
    ----------
    raw_name  : the component name or full description (e.g. "4 motores 920KV")
    raw_value : optional separate value field (from mutation_engine callers)
    registry  : domain registry to use; defaults to aerial_registry
    """
    active_registry = registry or _DEFAULT_REGISTRY
    text = (raw_value or raw_name).strip()
    normalized = text.lower()
    name_lc = raw_name.strip().lower()

    rule = active_registry.match(normalized, name_lc)

    if rule is not None:
        return _spec_from_rule(raw_name, rule, normalized)

    # ── Generic fallback — no rule matched ───────────────────────────────────
    completeness = "medium" if len(normalized.split()) >= 2 else "low"
    return ComponentSpec(
        name=raw_name.strip(),
        suggested_key="generic_component",
        component_type="generic_component",
        inference_confidence=0.4,
        completeness=completeness,
        missing_fields=["especificación técnica medible"] if completeness == "low" else [],
        hints=["Añade modelo o parámetro técnico"] if completeness == "low" else [],
    )


def _rule_for_key(registry: ComponentRuleRegistry, suggested_key: str) -> ComponentRule | None:
    for rule in registry._rules:
        if rule.suggested_key == suggested_key:
            return rule
    return None


def infer_component_for_key(
    raw_name: str,
    suggested_key: str,
    raw_value: str | None = None,
    registry: ComponentRuleRegistry | None = None,
) -> ComponentSpec | None:
    """FN-019: force inference against a specific suggested_key's rule,
    bypassing keyword matching entirely.

    Used only when acquisition context already names the expected component
    (e.g. propellers pending) and the input has no keyword to trigger the
    normal registry match (e.g. "10x4.5" with no "hélices" word — the
    property extractor already parses it fine, it just never runs). Reuses
    the rule's own property_extractor/completeness_evaluator unchanged — no
    second copy of the size regex. Returns None if no rule is registered for
    ``suggested_key``.
    """
    active_registry = registry or _DEFAULT_REGISTRY
    rule = _rule_for_key(active_registry, suggested_key)
    if rule is None:
        return None
    text = (raw_value or raw_name).strip()
    return _spec_from_rule(raw_name, rule, text.lower())


def _merge_same_key_specs(
    base: ComponentSpec,
    incoming: ComponentSpec,
    registry: ComponentRuleRegistry,
) -> ComponentSpec:
    """Merge two specs of the same suggested_key, re-evaluating completeness."""
    merged_props = dict(base.properties or {})
    merged_props.update(incoming.properties or {})
    rule = _rule_for_key(registry, base.suggested_key)
    name = base.name if len(base.name or "") >= len(incoming.name or "") else incoming.name
    if rule is not None:
        completeness, missing_fields = rule.completeness_evaluator(merged_props)
        hints = list(rule.missing_field_hints) if missing_fields else []
        hints += list(rule.extra_hints)
        return ComponentSpec(
            name=name,
            suggested_key=rule.suggested_key,
            component_type=rule.component_type,
            inference_confidence=max(base.inference_confidence, incoming.inference_confidence),
            properties=merged_props,
            completeness=completeness,
            missing_fields=missing_fields,
            hints=hints,
            output_magnitude=rule.output_magnitude,
        )
    rank = {"low": 0, "medium": 1, "high": 2}
    better = (
        incoming
        if rank.get(incoming.completeness, 0) > rank.get(base.completeness, 0)
        else base
    )
    return better.model_copy(update={"name": name, "properties": merged_props})


def infer_components(
    raw_name: str,
    raw_value: str | None = None,
    registry: ComponentRuleRegistry | None = None,
) -> list[ComponentSpec]:
    """Infer one or more ComponentSpecs from a possibly mixed freeform phrase (D7).

    Splits on commas / ``y`` / ``+`` and runs ``infer_component`` per segment.
    Segments that look like motors but lack the word ``motor`` are re-tried with
    a ``motores`` prefix. Same ``suggested_key`` segments **merge properties**
    (so ``4 motores 920KV y 15N`` keeps thrust). Falls back to a single full-text
    inference when splitting yields nothing useful, or when only one key remains
    and full-text recovers more properties.
    """
    active_registry = registry or _DEFAULT_REGISTRY
    text = (raw_value or raw_name).strip()
    if not text:
        return [infer_component(raw_name, raw_value, registry=active_registry)]

    segments = [s.strip() for s in _COMPONENT_SPLIT_RE.split(text) if s and s.strip()]
    if len(segments) <= 1:
        return [infer_component(raw_name, raw_value, registry=active_registry)]

    by_key: dict[str, ComponentSpec] = {}
    order: list[str] = []
    for segment in segments:
        spec = infer_component(segment, registry=active_registry)
        if (
            spec.suggested_key == "generic_component"
            and _LOOKS_LIKE_MOTOR_RE.search(segment)
        ):
            spec = infer_component(f"motores {segment}", registry=active_registry)
        if spec.suggested_key == "generic_component" and not spec.properties:
            continue
        key = spec.suggested_key
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = spec
            order.append(key)
            continue
        by_key[key] = _merge_same_key_specs(existing, spec, active_registry)

    if not by_key:
        return [infer_component(raw_name, raw_value, registry=active_registry)]

    # Single-key after split: prefer full-text if it recovers equal/more properties
    # (avoids losing fields that only parse in the combined phrase).
    if len(by_key) == 1:
        full = infer_component(raw_name, raw_value, registry=active_registry)
        only = next(iter(by_key.values()))
        if (
            full.suggested_key == only.suggested_key
            and len(full.properties or {}) >= len(only.properties or {})
        ):
            return [full]
        return [only]

    return [by_key[k] for k in order]
