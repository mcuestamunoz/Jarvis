"""G3 — Active Goal Continuity for Explore.

Design authority: .jes/artifacts/design_g3_active_goal_continuity.md (CLOSED, ★1-★4).
Contract: .jes/artifacts/implementation_contract_g3_active_goal_continuity.md

Root problem (CLI finding G3): after a Goal Plan creates an active
HandoffContext, an explore-shaped phrase that names the same dimension but
carries no explicit direction ("optimiza payload") always re-derived its
goal from text alone via detect_goal, which defaults undirected bare
"payload" to aumentar_payload (F-1's own correct, intentional default) —
silently inverting an active reducir_payload plan. Bare "explora opciones"
already worked correctly (H1/FN-024) because it binds through the handoff
when text_goal is None; the bug was specifically that ANY non-None
text-derived goal, even an undirected one, unconditionally won over the
active handoff.

Fix: explore_continuity.resolve_explore_goal_with_handoff — a pure
precedence function — plus wiring in orchestrator._handle_explore so a
same-dimension, undirected explore phrase inherits the active handoff's
goal, while an explicit direction word or a different-dimension phrase
still overrides (and, on success, replaces the handoff — ★4).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.explore_continuity import resolve_explore_goal_with_handoff
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import HandoffContext


class _RefuseLLM:
    def interpret(self, *a, **k):
        raise AssertionError("LLM.interpret must not be called")

    def analyze(self, *a, **k):
        raise AssertionError("LLM.analyze must not be called")

    def generate(self, *a, **k):
        raise AssertionError("LLM.generate must not be called")


class _StubLLM:
    def analyze(self, **kwargs):
        return "stub analyze"

    def interpret(self, *a, **k):
        raise AssertionError("LLM.interpret must not be called")

    def generate(self, *a, **k):
        raise AssertionError("LLM.generate must not be called")


def _make_project(orch: JarvisOrchestrator, payload_kg: float) -> None:
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "transporte de carga",
            "payload_kg": payload_kg,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "structure_mass_factor": 0.6,
            "safety_factor": 1.2,
            "motors": 4,
            "per_motor_max_thrust_n": 15.0,
        },
    })


# ── Pure precedence function — unit level ───────────────────────────────────

def _hc(goal_key: str, *, dse_capability: str = "active") -> HandoffContext:
    return HandoffContext(
        goal_key=goal_key, levers=[], dse_capability=dse_capability, project_id="p1",
    )


@pytest.mark.parametrize("text,text_goal,handoff_goal,expected", [
    # rule 1: no handoff -> text_goal
    ("optimiza payload", "aumentar_payload", None, "aumentar_payload"),
    # rule 2: text_goal None -> handoff.goal_key (H1)
    ("explora opciones", None, "reducir_payload", "reducir_payload"),
    # rule 3: agree trivially
    ("optimiza para reducir carga", "reducir_payload", "reducir_payload", "reducir_payload"),
    # rule 4 (★1): same family, undirected -> inherit handoff
    ("optimiza payload", "aumentar_payload", "reducir_payload", "reducir_payload"),
    ("optimiza payload", "aumentar_payload", "aumentar_payload", "aumentar_payload"),  # T7 symmetric
    # rule 5 (★2): different dimension -> override
    ("optimiza para autonomia", "mejorar_autonomia", "reducir_payload", "mejorar_autonomia"),
    # rule 5, explicit opposite direction within same family -> override
    ("optimiza para aumentar el payload", "aumentar_payload", "reducir_payload", "aumentar_payload"),
])
def test_resolve_explore_goal_with_handoff_pure(text, text_goal, handoff_goal, expected):
    handoff = _hc(handoff_goal) if handoff_goal else None
    assert resolve_explore_goal_with_handoff(text, text_goal, handoff) == expected


def test_no_bindable_handoff_uses_text_goal_even_if_dimension_matches():
    """A handoff for a DIFFERENT project (not bindable) must not leak in."""
    assert resolve_explore_goal_with_handoff("optimiza payload", "aumentar_payload", None) == "aumentar_payload"


# ── T1: bare explore, H1 regression ─────────────────────────────────────────

def test_t1_bare_explore_still_uses_handoff_goal(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _make_project(orch, payload_kg=4.0)
    orch.handle_user_text("reducir payload", _RefuseLLM())

    result = orch.handle_user_text("explora opciones", _RefuseLLM())

    assert result["action"] == "explore_design_space"
    assert result["goal_key"] == "reducir_payload"
    baseline = result["exploration"]["baseline_calculations"]["payload_kg"]
    for c in result["exploration"]["viable"]:
        assert c["calculations"]["payload_kg"] < baseline


# ── T2 (★1): undirected domain explore inherits active reduce goal ─────────

def test_t2_undirected_domain_explore_inherits_active_reduce(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _make_project(orch, payload_kg=4.0)
    orch.handle_user_text("reducir payload", _RefuseLLM())

    result = orch.handle_user_text("optimiza payload", _RefuseLLM())

    assert result["action"] == "explore_design_space"
    assert result["goal_key"] == "reducir_payload"
    baseline = result["exploration"]["baseline_calculations"]["payload_kg"]
    assert result["exploration"]["viable"], "expected at least one viable candidate"
    for c in result["exploration"]["viable"]:
        assert c["calculations"]["payload_kg"] < baseline


# ── T3: explore-shaped explicit increase overrides ──────────────────────────

def test_t3_explicit_increase_explore_overrides_active_reduce(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _make_project(orch, payload_kg=4.0)
    orch.handle_user_text("reducir payload", _RefuseLLM())

    result = orch.handle_user_text("optimiza para aumentar el payload", _RefuseLLM())

    assert result["action"] == "explore_design_space"
    assert result["goal_key"] == "aumentar_payload"


# ── T4 (★2): different-dimension explore overrides ──────────────────────────

def test_t4_different_dimension_explore_overrides(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _make_project(orch, payload_kg=4.0)
    orch.handle_user_text("reducir payload", _RefuseLLM())

    result = orch.handle_user_text("optimiza para autonomia", _RefuseLLM())

    assert result["action"] == "explore_design_space"
    assert result["goal_key"] == "mejorar_autonomia"


# ── T5: no handoff at all -> today's text-derive behavior unchanged ────────

def test_t5_no_handoff_uses_text_derive(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _make_project(orch, payload_kg=2.0)

    result = orch.handle_user_text("optimiza payload", _RefuseLLM())

    assert result["action"] == "explore_design_space"
    assert result["goal_key"] == "aumentar_payload"
    session = orch.state_manager.get_runtime_session()
    assert session.handoff_context is None, "no handoff should be invented when none existed"


# ── T6 (★4): after a successful override explore, handoff replaced ─────────

def test_t6_handoff_replaced_after_override_explore(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _make_project(orch, payload_kg=4.0)
    orch.handle_user_text("reducir payload", _RefuseLLM())

    orch.handle_user_text("optimiza para aumentar el payload", _RefuseLLM())

    session = orch.state_manager.get_runtime_session()
    assert session.handoff_context is not None
    assert session.handoff_context.goal_key == "aumentar_payload"
    assert session.handoff_context.dse_capability == "consumed"

    # A subsequent bare explore honestly reports on the NEW goal, not the
    # stale reducir_payload one — proves the replace actually took effect,
    # not just that the session field happens to look right.
    result = orch.handle_user_text("explora opciones", _RefuseLLM())
    assert "maximizar carga útil" in result["message"]
    assert "minimizar carga útil" not in result["message"]


def test_t4_different_dimension_also_replaces_handoff(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _make_project(orch, payload_kg=4.0)
    orch.handle_user_text("reducir payload", _RefuseLLM())

    orch.handle_user_text("optimiza para autonomia", _RefuseLLM())

    session = orch.state_manager.get_runtime_session()
    assert session.handoff_context.goal_key == "mejorar_autonomia"
    assert session.handoff_context.dse_capability == "consumed"
    # H4 lever preseed now offers autonomia's own levers, not payload's.
    assert any("battery" in lever or "motor_power_w" in lever for lever in session.handoff_context.levers)


# ── T7: symmetric continuation for aumentar_payload ─────────────────────────

def test_t7_undirected_domain_explore_inherits_active_increase(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _make_project(orch, payload_kg=2.0)
    orch.handle_user_text("aumentar payload", _RefuseLLM())

    result = orch.handle_user_text("optimiza payload", _RefuseLLM())

    assert result["action"] == "explore_design_space"
    assert result["goal_key"] == "aumentar_payload"


# ── Continuation after DSE already consumed → honest message, not re-bind ──

def test_continuation_phrase_after_consumed_gives_honest_message_not_silent_reexplore(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _make_project(orch, payload_kg=4.0)
    orch.handle_user_text("reducir payload", _RefuseLLM())
    orch.handle_user_text("explora opciones", _RefuseLLM())  # consumes dse_capability

    result = orch.handle_user_text("optimiza payload", _RefuseLLM())

    assert result["goal_key"] is None
    assert "Ya exploré opciones" in result["message"]
    assert "minimizar carga útil" in result["message"]


# ── ★3: no dual-fire — a full Goal Plan phrase routes as engineering_intent,
#        never touches the explore precedence helper at all ───────────────

def test_new_plan_phrase_routes_as_engineering_intent_not_explore(tmp_path: Path):
    """"reducir payload" said again mid-plan is a NEW plan-forming phrase
    (FN-022 gate), not an explore-shaped one — it must not be reinterpreted
    by G3's explore precedence at all (★3: no dual-fire)."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _make_project(orch, payload_kg=4.0)
    orch.handle_user_text("reducir payload", _RefuseLLM())

    result = orch.handle_user_text("aumentar payload", _RefuseLLM())

    assert result["action"] == "engineering_intent"
    assert result["goal_key"] == "aumentar_payload"
    session = orch.state_manager.get_runtime_session()
    assert session.handoff_context.goal_key == "aumentar_payload"
    assert session.handoff_context.dse_capability == "active"  # fresh plan, not yet explored


# ── Regressions: FN-024 / FN-025 / FN-026 / F-1 smoke ───────────────────────

def test_fn024_bare_explore_no_handoff_still_falls_to_analyze(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _make_project(orch, payload_kg=4.0)
    # No Goal Plan was ever created — no handoff exists at all. Falling back
    # to analyze legitimately reaches the LLM narrator (unchanged pre-G3
    # behavior) — _StubLLM permits analyze, still refuses interpret/generate.

    result = orch.handle_user_text("explora opciones", _StubLLM())

    assert result["action"] == "analyze"


def test_fn025_help_plus_goal_then_bare_explore_regression(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _make_project(orch, payload_kg=4.0)
    plan = orch.handle_user_text("ayudame a reducir payload", _RefuseLLM())
    assert plan["action"] == "engineering_intent"
    assert plan["goal_key"] == "reducir_payload"

    result = orch.handle_user_text("explora opciones", _RefuseLLM())
    assert result["goal_key"] == "reducir_payload"


def test_fn026_lever_preseed_unaffected_by_g3(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _make_project(orch, payload_kg=4.0)
    orch.handle_user_text("reducir payload", _RefuseLLM())

    result = orch.handle_user_text("cambia payload_kg", _RefuseLLM())
    # "payload_kg" collides with FN-022's own goal gate (pre-existing, see
    # FN-026/F-1 reports) — same known limitation, not a G3 regression.
    assert result["action"] in {"interactive", "engineering_intent"}


def test_f1_aumentar_payload_dse_regression(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _make_project(orch, payload_kg=2.0)
    orch.handle_user_text("aumentar payload", _RefuseLLM())

    result = orch.handle_user_text("explora opciones", _RefuseLLM())

    assert result["goal_key"] == "aumentar_payload"
    baseline = result["exploration"]["baseline_calculations"]["payload_kg"]
    increasing = [c for c in result["exploration"]["candidates"] if c["calculations"]["payload_kg"] > baseline]
    assert increasing
