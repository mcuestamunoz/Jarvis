"""F-1 — Vehicle-Agnostic Payload Direction.

Root cause (.jes/artifacts/cli_findings_post_catalog_bind_v1.md, finding F-1):
`_GOAL_KEYWORDS` contained the bare, direction-less token "payload" (and
"carga util"), so `detect_goal("reducir payload")` matched it via substring
containment and returned `aumentar_payload` — a direct semantic inversion.

Fix: goal_planner.detect_goal now resolves payload as (dimension, direction)
via `_detect_payload_goal`/`_direction_of`, checked before the generic
`_GOAL_KEYWORDS` loop. A new goal, `reducir_payload`, mirrors `aumentar_payload`
using the same GOAL_STRATEGIES/EXPLORATION_GRIDS architecture — no parallel
planning system, no vehicle_type branching anywhere (detect_goal takes only
text).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.design_explorer import (
    EXPLORATION_GRIDS,
    GOAL_LABELS,
    DesignExplorer,
)
from jarvis.core.goal_planner import (
    GOAL_STRATEGIES,
    _prioritize_strategies,
    detect_goal,
    format_goal_plan,
    is_engineering_intention,
)
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.calculation_engine import CalculationEngine
from jarvis.simulation.simulator import FeasibilitySimulator

from test_design_explorer import DRONE_PARAMS, _make_project_state


class _RefuseLLM:
    def interpret(self, *a, **k):
        raise AssertionError("LLM.interpret must not be called")

    def analyze(self, *a, **k):
        raise AssertionError("LLM.analyze must not be called")

    def generate(self, *a, **k):
        raise AssertionError("LLM.generate must not be called")


# ── 1. Direction-aware detection — required outcomes table ─────────────────

@pytest.mark.parametrize("text,expected", [
    ("aumentar payload", "aumentar_payload"),
    ("aumentar carga útil", "aumentar_payload"),
    ("subir payload", "aumentar_payload"),
    ("subir carga útil", "aumentar_payload"),
    ("reducir payload", "reducir_payload"),
    ("reducir carga útil", "reducir_payload"),
    ("bajar payload", "reducir_payload"),
    ("bajar la carga útil", "reducir_payload"),
    ("transportar menos peso", "reducir_payload"),
    ("necesito transportar menos peso", "reducir_payload"),
    ("mejorar autonomia", "mejorar_autonomia"),
    ("aumentar empuje", "mejorar_estabilidad"),
])
def test_detect_goal_required_outcomes(text, expected):
    assert detect_goal(text) == expected


def test_reducir_payload_numeric_value_defers_to_iterate():
    assert is_engineering_intention("reducir payload a 2kg") is None


# ── 2. Existing positive intent stays compatible (regression) ──────────────

@pytest.mark.parametrize("text,expected", [
    ("cómo mejoro la carga útil", "aumentar_payload"),
    ("mejorar carga util del dron", "aumentar_payload"),
    ("quiero más payload", "aumentar_payload"),
    ("necesito levantar mas peso", "aumentar_payload"),
    ("quiero transportar mas peso", "aumentar_payload"),
    ("quiero reducir masa del chasis", "reducir_masa"),
    ("necesito aligerar el diseño", "reducir_masa"),
    ("el dron necesita mas estabilidad", "mejorar_estabilidad"),
])
def test_existing_positive_intent_unchanged(text, expected):
    assert detect_goal(text) == expected


# ── 3. Vehicle-agnostic detection — pure text-in/text-out ──────────────────
# detect_goal/is_engineering_intention take ONLY user_input text — there is no
# vehicle_type parameter to branch on. This parametrization documents that
# invariant directly (calling the same function signature the exact same way
# regardless of what "vehicle" the caller has in mind) rather than merely
# asserting it in prose.

@pytest.mark.parametrize("text,expected_goal", [
    ("reducir payload", "reducir_payload"),
    ("reducir carga útil", "reducir_payload"),
    ("aumentar payload", "aumentar_payload"),
])
@pytest.mark.parametrize("vehicle_type", ["dron", "robot", "ground"])
def test_payload_detection_identical_across_vehicle_types(vehicle_type, text, expected_goal):
    # vehicle_type is intentionally unused by detect_goal — its presence here
    # only proves the same call produces the same result no matter which
    # vehicle context the caller has in mind.
    del vehicle_type
    assert detect_goal(text) == expected_goal


def test_orchestrator_payload_direction_identical_dron_robot_rover(tmp_path: Path):
    """End-to-end (not just the pure function): the same phrase produces the
    same goal_key through the full orchestrator/create_project path for three
    different vehicle_type projects — dron, robot, rover ("ground")."""
    results = {}
    for vehicle_type in ("dron", "robot", "rover"):
        orch = JarvisOrchestrator(workspace_root=tmp_path / vehicle_type)
        orch.handle({
            "action": "create_project",
            "parameters": {
                "vehicle_type": vehicle_type,
                "objective": "test",
                "payload_kg": 3.0,
                "restrictions": "ninguna",
                "detail_level": "conceptual",
                "structure_mass_factor": 0.6,
                "safety_factor": 1.2,
            },
        })
        result = orch.handle_user_text("reducir payload", _RefuseLLM())
        results[vehicle_type] = result.get("goal_key")

    assert results == {"dron": "reducir_payload", "robot": "reducir_payload", "rover": "reducir_payload"}


# ── 4. reducir_payload Goal Plan — same architecture as existing goals ─────

def test_reducir_payload_in_goal_strategies():
    assert "reducir_payload" in GOAL_STRATEGIES
    strategies = GOAL_STRATEGIES["reducir_payload"]
    assert len(strategies) == 3
    for s in strategies:
        assert set(s.keys()) == {"action", "description", "lever"}


def test_reducir_payload_strategy_levers():
    levers = [s["lever"] for s in GOAL_STRATEGIES["reducir_payload"]]
    assert "payload_kg" in levers
    assert "structure_mass_factor / material" in levers
    assert "motors / motor_count" in levers


def test_reducir_payload_wording_is_vehicle_agnostic():
    """Strategy copy must describe engineering effects, not drone-specific
    concepts (no 'dron'/'drone'/'hélice'/'motor de dron' wording)."""
    forbidden = ("dron", "drone", "helice", "hélice", "propeller")
    for s in GOAL_STRATEGIES["reducir_payload"]:
        text = f"{s['action']} {s['description']}".lower()
        for term in forbidden:
            assert term not in text, f"non-vehicle-agnostic term {term!r} in: {text}"


def test_format_goal_plan_reducir_payload():
    plan = format_goal_plan("reducir_payload")
    assert "Reducir carga útil" in plan
    assert "1." in plan and "2." in plan and "3." in plan
    assert "payload_kg" in plan


def test_all_goals_still_have_non_empty_plan_including_new_one():
    for goal_key in GOAL_STRATEGIES:
        plan = format_goal_plan(goal_key)
        assert len(plan) > 20, f"Plan vacío para {goal_key}"


# ── 5. Prioritization — margin-low favors payload_kg; motor_count architecture-conditional ─

def test_reducir_payload_low_margin_puts_payload_first():
    strategies = GOAL_STRATEGIES["reducir_payload"]
    sim = {"safety_margin_ratio": 1.05, "warnings": []}
    ordered = _prioritize_strategies("reducir_payload", strategies, sim)
    assert "payload" in ordered[0]["lever"].lower()


def test_reducir_payload_motor_strategy_never_first_when_motor_count_absent():
    """Engineer lock: motor_count is architecture-conditional, never invented.
    sim_context (last_simulation-shaped) never carries motor_count today, so
    the actuator lever must never be promoted to first — regardless of margin."""
    strategies = GOAL_STRATEGIES["reducir_payload"]
    for sim in (
        {"safety_margin_ratio": 1.05, "warnings": []},
        {"safety_margin_ratio": 1.8, "warnings": []},
        {"safety_margin_ratio": None, "warnings": []},
    ):
        ordered = _prioritize_strategies("reducir_payload", strategies, sim)
        assert "motor" not in ordered[0]["lever"].lower()
        assert ordered[-1]["lever"] == "motors / motor_count"


def test_reducir_payload_motor_strategy_stays_in_catalog():
    """Deprioritized, never removed — H4/match_plan_lever may still reference
    it when the user names the lever explicitly."""
    levers = [s["lever"] for s in GOAL_STRATEGIES["reducir_payload"]]
    assert "motors / motor_count" in levers


def test_reducir_payload_no_sim_context_returns_default_order():
    strategies = GOAL_STRATEGIES["reducir_payload"]
    ordered = _prioritize_strategies("reducir_payload", strategies, None)
    assert ordered == strategies


# ── 6. DSE symmetry ──────────────────────────────────────────────────────────

@pytest.fixture
def explorer():
    return DesignExplorer(calculation_engine=CalculationEngine(), simulator=FeasibilitySimulator())


@pytest.fixture
def project_state():
    return _make_project_state(dict(DRONE_PARAMS))


def test_reducir_payload_in_exploration_grids():
    assert "reducir_payload" in EXPLORATION_GRIDS
    assert "reducir_payload" in GOAL_LABELS


def test_reducir_payload_candidates_never_exceed_baseline(explorer, project_state):
    result = explorer.explore(project_state, "reducir_payload")
    baseline_payload = result.baseline_calculations.payload_kg
    assert result.candidates, "expected at least one candidate"
    for c in result.candidates:
        assert c.calculations.payload_kg <= baseline_payload + 1e-9


def test_reducir_payload_viable_candidates_strictly_lower_payload(explorer, project_state):
    result = explorer.explore(project_state, "reducir_payload")
    baseline_payload = result.baseline_calculations.payload_kg
    assert result.viable, "expected at least one viable (can_fly) candidate"
    for c in result.viable:
        assert c.calculations.payload_kg < baseline_payload


def test_aumentar_payload_dse_still_produces_increasing_candidates(explorer, project_state):
    """Regression: F-1 must not have flipped or broken aumentar_payload's DSE."""
    result = explorer.explore(project_state, "aumentar_payload")
    baseline_payload = result.baseline_calculations.payload_kg
    increasing = [c for c in result.candidates if c.calculations.payload_kg > baseline_payload]
    assert increasing, "expected at least one candidate with higher payload than baseline"


def test_explore_all_goals_smoke_includes_reducir_payload(explorer, project_state):
    for goal in EXPLORATION_GRIDS:
        result = explorer.explore(project_state, goal)
        assert result.goal_key == goal
    assert "reducir_payload" in EXPLORATION_GRIDS


# ── 7. Handoff invariant: Goal Plan → HandoffContext → explora → DSE ───────

def _closed_dron_project(orch: JarvisOrchestrator, payload_kg: float) -> None:
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


def test_reducir_payload_plan_creates_handoff_context(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _closed_dron_project(orch, payload_kg=4.0)

    result = orch.handle_user_text("reducir payload", _RefuseLLM())
    assert result["action"] == "engineering_intent"
    assert result["goal_key"] == "reducir_payload"

    session = orch.state_manager.get_runtime_session()
    hc = session.handoff_context
    assert hc is not None
    assert hc.goal_key == "reducir_payload"
    assert hc.dse_capability == "active"


def test_reducir_payload_bare_explore_binds_and_explores_lower_payload(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _closed_dron_project(orch, payload_kg=4.0)
    orch.handle_user_text("reducir payload", _RefuseLLM())

    result = orch.handle_user_text("explora opciones", _RefuseLLM())

    assert result["action"] == "explore_design_space"
    assert result["goal_key"] == "reducir_payload"
    exploration = result["exploration"]
    baseline_payload = exploration["baseline_calculations"]["payload_kg"]
    assert exploration["viable"], "expected at least one viable candidate"
    for c in exploration["viable"]:
        assert c["calculations"]["payload_kg"] < baseline_payload
    session = orch.state_manager.get_runtime_session()
    assert session.handoff_context.dse_capability == "consumed"


def test_aumentar_payload_bare_explore_unaffected_by_reducir_payload_addition(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _closed_dron_project(orch, payload_kg=2.0)
    orch.handle_user_text("aumentar payload", _RefuseLLM())

    result = orch.handle_user_text("explora opciones", _RefuseLLM())

    assert result["action"] == "explore_design_space"
    assert result["goal_key"] == "aumentar_payload"


# ── 8. Regression: FN-022 / H1-H4 smoke ─────────────────────────────────────

def test_fn022_bare_intention_other_goals_unchanged(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _closed_dron_project(orch, payload_kg=2.0)

    result = orch.handle_user_text("Aumentar el empuje", _RefuseLLM())
    assert result["action"] == "engineering_intent"
    assert result["goal_key"] == "mejorar_estabilidad"


def test_fn025_help_plus_reducir_payload_routes_to_engineering_intent(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _closed_dron_project(orch, payload_kg=4.0)

    result = orch.handle_user_text("ayudame a reducir payload", _RefuseLLM())
    assert result["action"] == "engineering_intent"
    assert result["goal_key"] == "reducir_payload"


def test_fn026_lever_preseed_reducir_payload(tmp_path: Path):
    """H4: match_plan_lever resolves reducir_payload's own levers correctly.

    Not exercised via a bare "cambia payload_kg" natural-language turn: any
    phrase containing "payload_kg" also contains the "payload" dimension
    token, so the pre-existing FN-022 goal-detection gate (checked before
    the iterate dispatch, unrelated to F-1) reclaims the turn as a new goal
    intention before it ever reaches match_plan_lever — the same known
    limitation FN-026's own report already documented for the "thrust"/
    "empuje" lever (test_dse_apply_diverging_thrust_clears_motor_catalog_ref
    used the DSE route for exactly this reason). match_plan_lever itself is
    tested directly here instead, which is what H4 preseeding actually calls."""
    from jarvis.core.handoff_matching import match_plan_lever
    from jarvis.schemas.action_schema import HandoffContext

    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _closed_dron_project(orch, payload_kg=4.0)
    orch.handle_user_text("reducir payload", _RefuseLLM())

    handoff = orch.state_manager.get_runtime_session().handoff_context
    assert handoff is not None
    assert handoff.goal_key == "reducir_payload"
    assert "payload_kg" in handoff.levers

    assert match_plan_lever("quiero cambiar payload_kg", handoff) == "payload_kg"
