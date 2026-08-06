"""Tests for Fix 5 — Hybrid Goal Planner."""

from __future__ import annotations

import json

import pytest

from jarvis.core.goal_planner import (
    GOAL_STRATEGIES,
    detect_goal,
    format_goal_plan,
    get_goal_context_for_llm,
    _prioritize_strategies,
)
from jarvis.llm.prompt_builder import PromptBuilder


# ── detect_goal ───────────────────────────────────────────────────────────────

class TestDetectGoal:
    def test_payload_explicit_phrase(self):
        assert detect_goal("cómo mejoro la carga útil") == "aumentar_payload"

    def test_payload_without_tilde(self):
        assert detect_goal("mejorar carga util del dron") == "aumentar_payload"

    def test_payload_english_keyword(self):
        assert detect_goal("quiero más payload") == "aumentar_payload"

    def test_payload_weight_verb(self):
        assert detect_goal("necesito levantar mas peso") == "aumentar_payload"

    def test_autonomia_with_tilde(self):
        assert detect_goal("cómo mejorar la autonomía") == "mejorar_autonomia"

    def test_autonomia_without_tilde(self):
        assert detect_goal("quiero mas autonomia") == "mejorar_autonomia"

    def test_autonomia_flight_duration(self):
        assert detect_goal("como aumentar la duracion vuelo") == "mejorar_autonomia"

    def test_reducir_masa(self):
        assert detect_goal("quiero reducir masa del chasis") == "reducir_masa"

    def test_reducir_masa_synonym(self):
        assert detect_goal("necesito aligerar el diseño") == "reducir_masa"

    def test_estabilidad(self):
        assert detect_goal("el dron necesita mas estabilidad") == "mejorar_estabilidad"

    def test_no_match_simulation_query(self):
        assert detect_goal("cuáles son los warnings del proyecto") is None

    def test_no_match_what_if(self):
        assert detect_goal("qué pasa si aumento motores") is None

    def test_no_match_empty(self):
        assert detect_goal("") is None


# ── format_goal_plan ──────────────────────────────────────────────────────────

class TestFormatGoalPlan:
    def test_payload_plan_has_header(self):
        plan = format_goal_plan("aumentar_payload")
        assert "carga útil" in plan.lower() or "aumentar" in plan.lower()

    def test_payload_plan_numbered(self):
        plan = format_goal_plan("aumentar_payload")
        assert "1." in plan
        assert "2." in plan
        assert "3." in plan

    def test_payload_plan_contains_levers(self):
        plan = format_goal_plan("aumentar_payload")
        assert "structure_mass_factor" in plan or "per_motor_max_thrust_n" in plan

    def test_autonomia_plan_contains_battery(self):
        plan = format_goal_plan("mejorar_autonomia")
        assert "battery" in plan.lower() or "batería" in plan.lower() or "Aumentar capacidad" in plan

    def test_unknown_key_returns_empty(self):
        assert format_goal_plan("objetivo_inexistente") == ""

    def test_all_goals_have_non_empty_plan(self):
        for goal_key in GOAL_STRATEGIES:
            plan = format_goal_plan(goal_key)
            assert len(plan) > 20, f"Plan vacío para {goal_key}"


# ── get_goal_context_for_llm ──────────────────────────────────────────────────

class TestGetGoalContextForLlm:
    def test_returns_valid_json(self):
        raw = get_goal_context_for_llm("aumentar_payload")
        data = json.loads(raw)
        assert data["goal"] == "aumentar_payload"
        assert isinstance(data["strategies"], list)

    def test_strategies_have_required_fields(self):
        data = json.loads(get_goal_context_for_llm("mejorar_autonomia"))
        for s in data["strategies"]:
            assert "action" in s
            assert "description" in s
            assert "lever" in s

    def test_unknown_key_returns_empty_strategies(self):
        data = json.loads(get_goal_context_for_llm("goal_inexistente"))
        assert data["strategies"] == []


# ── prompt_builder injection ──────────────────────────────────────────────────

class TestBuildAnalysisMessagesGoalInjection:
    def setup_method(self):
        self.builder = PromptBuilder()

    def test_goal_context_appears_in_user_message(self):
        goal_ctx = get_goal_context_for_llm("aumentar_payload")
        messages = self.builder.build_analysis_messages(
            user_input="cómo mejoro la carga útil",
            context={"payload_kg": 1.0},
            analyze_type="explanation",
            goal_context=goal_ctx,
        )
        user_msg = next(m["content"] for m in messages if m["role"] == "user")
        assert "Contexto del objetivo" in user_msg
        assert "aumentar_payload" in user_msg

    def test_no_goal_context_no_injection(self):
        messages = self.builder.build_analysis_messages(
            user_input="qué pasa si aumento motores",
            context={"motor_count": 4},
            analyze_type="what_if",
            goal_context=None,
        )
        user_msg = next(m["content"] for m in messages if m["role"] == "user")
        assert "Contexto del objetivo" not in user_msg

    def test_user_question_always_at_end(self):
        goal_ctx = get_goal_context_for_llm("reducir_masa")
        messages = self.builder.build_analysis_messages(
            user_input="quiero reducir masa",
            context={},
            analyze_type="explanation",
            goal_context=goal_ctx,
        )
        user_msg = next(m["content"] for m in messages if m["role"] == "user")
        assert user_msg.endswith("quiero reducir masa")


# ── prioritization ────────────────────────────────────────────────────────────

class TestPrioritizeStrategies:
    def test_low_margin_puts_thrust_first(self):
        strategies = GOAL_STRATEGIES["aumentar_payload"]
        sim = {"safety_margin_ratio": 1.05, "warnings": []}
        ordered = _prioritize_strategies("aumentar_payload", strategies, sim)
        assert "thrust" in ordered[0]["lever"].lower() or "motor" in ordered[0]["lever"].lower()

    def test_high_margin_puts_factor_first(self):
        strategies = GOAL_STRATEGIES["aumentar_payload"]
        sim = {"safety_margin_ratio": 1.8, "warnings": []}
        ordered = _prioritize_strategies("aumentar_payload", strategies, sim)
        first_lever = ordered[0]["lever"].lower()
        assert "factor" in first_lever or "payload" in first_lever

    def test_no_sim_context_returns_default_order(self):
        strategies = GOAL_STRATEGIES["aumentar_payload"]
        ordered = _prioritize_strategies("aumentar_payload", strategies, None)
        assert ordered == strategies

    def test_autonomia_energy_warning_puts_battery_first(self):
        strategies = GOAL_STRATEGIES["mejorar_autonomia"]
        sim = {"safety_margin_ratio": 1.2, "warnings": ["missing_energy_parameters"]}
        ordered = _prioritize_strategies("mejorar_autonomia", strategies, sim)
        assert "battery" in ordered[0]["lever"].lower() or "wh" in ordered[0]["lever"].lower()

    def test_format_goal_plan_passes_sim_context(self):
        """format_goal_plan con margin bajo debe listar empuje primero."""
        sim = {"safety_margin_ratio": 1.05, "warnings": []}
        plan = format_goal_plan("aumentar_payload", sim_context=sim)
        lines = plan.splitlines()
        first_strategy_line = next(l for l in lines if l.startswith("1."))
        assert "empuje" in first_strategy_line.lower() or "motor" in first_strategy_line.lower()

    def test_format_goal_plan_no_sim_context_still_works(self):
        plan = format_goal_plan("reducir_masa")
        assert "1." in plan
        assert "Palanca:" in plan
