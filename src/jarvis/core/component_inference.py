"""
Domain-agnostic component inference dispatcher.

``infer_component`` matches a freeform text description against a
``ComponentRuleRegistry`` and delegates property extraction + completeness
evaluation to the matching rule.  The default registry is ``aerial_registry``
(backward-compatible), but any registry can be injected for other domains.
"""
from __future__ import annotations

from jarvis.core.component_rules import ComponentRuleRegistry
from jarvis.domains.aerial import aerial_registry
from jarvis.schemas.action_schema import ComponentSpec


# Default registry — aerial domain for backward compatibility.
# Replace or extend by passing a custom registry to infer_component().
_DEFAULT_REGISTRY: ComponentRuleRegistry = aerial_registry


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
