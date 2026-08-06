"""Ground domain — component inference rules for land vehicles (rovers, cars, robots).

This module defines:
  - Property extractors for ground components (wheel actuators, passive wheels)
  - Completeness evaluators for each component type
  - A ComponentRuleRegistry pre-loaded with ground rules

Import ``ground_registry`` to use these rules in component_inference.py, or
pass it as the registry argument to ``infer_component()``.

Key difference from aerial domain:
  - Force unit is torque (Nm) at the actuator, not direct thrust (N)
  - Converting torque → traction force requires wheel_radius + gear_ratio
  - component_resolver therefore only resolves actuator_count for ground components;
    max_force_per_actuator_n must be provided explicitly in parameters
"""
from __future__ import annotations

import re

from jarvis.core.component_rules import ComponentRule, ComponentRuleRegistry
from jarvis.schemas.action_schema import PropertyValue


# ── Wheel actuator property extractor ────────────────────────────────────────

def extract_wheel_actuator_properties(normalized: str) -> dict[str, PropertyValue]:
    """Extract structured PropertyValue entries from a ground motor/actuator text."""
    props: dict[str, PropertyValue] = {}

    # motor_count: "4 motores", "4x", "2 ruedas motrices"
    count_match = re.search(
        r"\b(\d+)\s*(?:x\b|\s*motores?\b|\s*ruedas?\s+motrices?\b)",
        normalized,
    )
    if count_match:
        props["motor_count"] = PropertyValue(
            value=int(count_match.group(1)),
            unit=None,
            confidence=0.9,
            source="declared",
        )

    # torque_nm: "50Nm", "50 Nm", "50N.m"  — disjoint from aerial thrust "50N" (no trailing m)
    torque_match = re.search(r"\b(\d+(?:\.\d+)?)\s*n\.?m\b", normalized, re.IGNORECASE)
    if torque_match:
        props["torque_nm"] = PropertyValue(
            value=float(torque_match.group(1)),
            unit="Nm",
            confidence=0.9,
            source="declared",
        )

    # rpm: "1000rpm", "3000 rpm"
    rpm_match = re.search(r"\b(\d+(?:\.\d+)?)\s*rpm\b", normalized, re.IGNORECASE)
    if rpm_match:
        props["rpm"] = PropertyValue(
            value=float(rpm_match.group(1)),
            unit="rpm",
            confidence=0.9,
            source="declared",
        )

    return props


def _wheel_actuator_completeness(props: dict) -> tuple[str, list[str]]:
    has_torque = "torque_nm" in props
    has_count = "motor_count" in props
    missing: list[str] = []
    if not has_torque:
        missing.append("par motor (Nm)")
    if not has_count:
        missing.append("número de motores/ruedas motrices")
    if has_torque and has_count:
        return "high", []
    if props:
        return "medium", missing
    return "low", missing


# ── Passive wheel property extractor ─────────────────────────────────────────

def extract_wheel_properties(normalized: str) -> dict[str, PropertyValue]:
    """Extract structured PropertyValue entries from a passive wheel description."""
    props: dict[str, PropertyValue] = {}

    # wheel_count: "4 ruedas", "6 wheels"
    count_match = re.search(r"\b(\d+)\s*(?:ruedas?|wheels?)\b", normalized)
    if count_match:
        props["wheel_count"] = PropertyValue(
            value=int(count_match.group(1)),
            unit=None,
            confidence=0.85,
            source="declared",
        )

    return props


def _wheel_completeness(props: dict) -> tuple[str, list[str]]:
    if "wheel_count" not in props:
        return "low", ["número de ruedas"]
    return "medium", []


# ── Rule registry for ground domain ─────────────────────────────────────────

ground_registry = ComponentRuleRegistry([
    ComponentRule(
        keywords=("motor", "par", "torque", "traccion", "tracción", "motriz", "traction"),
        component_type="traction_active",
        suggested_key="wheel_actuators",
        inference_confidence=0.75,
        property_extractor=extract_wheel_actuator_properties,
        completeness_evaluator=_wheel_actuator_completeness,
        missing_field_hints=("Incluye cantidad y par motor (ej: 4 motores 50Nm)",),
        output_magnitude="torque_nm",
    ),
    ComponentRule(
        keywords=("rueda", "wheel", "neumático", "neumatico", "tyre", "tire"),
        component_type="rolling_passive",
        suggested_key="wheels",
        inference_confidence=0.65,
        property_extractor=extract_wheel_properties,
        completeness_evaluator=_wheel_completeness,
        missing_field_hints=("Define número de ruedas (ej: 4 ruedas)",),
    ),
])
