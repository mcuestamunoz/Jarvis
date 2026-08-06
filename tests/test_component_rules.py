"""Tests for ComponentRule and ComponentRuleRegistry (domain-agnostic layer)."""
from __future__ import annotations

import pytest

from jarvis.core.component_rules import ComponentRule, ComponentRuleRegistry


# ── Minimal stubs ─────────────────────────────────────────────────────────────

def _noop_extractor(normalized: str) -> dict:
    return {}


def _noop_evaluator(props: dict) -> tuple[str, list[str]]:
    return "medium", []


def _make_rule(keyword: str, component_type: str = "test_type") -> ComponentRule:
    return ComponentRule(
        keywords=(keyword,),
        component_type=component_type,
        suggested_key=keyword,
        inference_confidence=0.8,
        property_extractor=_noop_extractor,
        completeness_evaluator=_noop_evaluator,
    )


# ── ComponentRule.matches ─────────────────────────────────────────────────────

def test_matches_keyword_in_normalized():
    rule = _make_rule("motor")
    assert rule.matches("motor 920kv", "motor")


def test_matches_keyword_in_name_lc():
    rule = _make_rule("motor")
    assert rule.matches("", "motor principal")


def test_does_not_match_unrelated_text():
    rule = _make_rule("motor")
    assert not rule.matches("helice 10x4.5", "helice")


def test_multiple_keywords_any_is_sufficient():
    rule = ComponentRule(
        keywords=("helice", "propeller", "props"),
        component_type="propulsion_passive",
        suggested_key="propellers",
        inference_confidence=0.6,
        property_extractor=_noop_extractor,
        completeness_evaluator=_noop_evaluator,
    )
    assert rule.matches("propeller 10x4.5", "")
    assert rule.matches("props de carbono", "")
    assert rule.matches("", "helice principal")
    assert not rule.matches("motor 920kv", "motor")


# ── ComponentRuleRegistry construction ───────────────────────────────────────

def test_registry_starts_empty_when_no_rules():
    registry = ComponentRuleRegistry([])
    assert len(registry) == 0


def test_registry_accepts_rules_on_construction():
    rules = [_make_rule("motor"), _make_rule("esc")]
    registry = ComponentRuleRegistry(rules)
    assert len(registry) == 2


def test_register_adds_rule():
    registry = ComponentRuleRegistry([])
    registry.register(_make_rule("motor"))
    assert len(registry) == 1


# ── ComponentRuleRegistry.match ────────────────────────────────────────────────

def test_match_returns_correct_rule():
    motor_rule = _make_rule("motor", "propulsion_active")
    esc_rule = _make_rule("esc", "power_control")
    registry = ComponentRuleRegistry([motor_rule, esc_rule])

    result = registry.match("motor 920kv", "motor")
    assert result is motor_rule


def test_match_returns_none_when_no_rule_matches():
    registry = ComponentRuleRegistry([_make_rule("motor")])
    result = registry.match("bateria lipo 6s", "bateria")
    assert result is None


def test_match_empty_registry_returns_none():
    registry = ComponentRuleRegistry([])
    assert registry.match("motor 920kv", "motor") is None


# ── First-match-wins ordering ─────────────────────────────────────────────────

def test_first_match_wins_over_later_rules():
    """When two rules could match, the first registered rule takes priority."""
    first = _make_rule("motor", "first_type")
    second = ComponentRule(
        keywords=("motor", "kv"),
        component_type="second_type",
        suggested_key="motors",
        inference_confidence=0.9,
        property_extractor=_noop_extractor,
        completeness_evaluator=_noop_evaluator,
    )
    registry = ComponentRuleRegistry([first, second])

    result = registry.match("motor 920kv", "motor")
    assert result is first
    assert result.component_type == "first_type"


def test_order_matters_second_wins_when_first_does_not_match():
    first = _make_rule("esc", "power_control")
    second = _make_rule("motor", "propulsion_active")
    registry = ComponentRuleRegistry([first, second])

    result = registry.match("motor 920kv", "motor")
    assert result is second
    assert result.component_type == "propulsion_active"


# ── Registry isolation ─────────────────────────────────────────────────────────

def test_two_registries_are_independent():
    reg_a = ComponentRuleRegistry([_make_rule("motor")])
    reg_b = ComponentRuleRegistry([_make_rule("esc")])

    assert reg_a.match("motor", "") is not None
    assert reg_a.match("esc", "") is None
    assert reg_b.match("esc", "") is not None
    assert reg_b.match("motor", "") is None
