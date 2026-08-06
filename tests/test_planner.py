import pytest

from jarvis.core.planner import PlanValidationError, Planner, requires_planning
from jarvis.schemas.action_schema import ActionName


def test_requires_planning_only_for_composite_goals():
    assert requires_planning("create_and_simulate") is True
    assert requires_planning("recalculate_and_simulate") is True
    assert requires_planning(ActionName.CREATE_PROJECT) is False
    assert requires_planning("simulate") is False


def test_misrouted_action():
    planner = Planner()

    with pytest.raises(PlanValidationError, match="debe ejecutarse directamente"):
        planner.generate("create_project", {})


def test_invalid_composite_goal_fails_clearly():
    planner = Planner()

    with pytest.raises(PlanValidationError, match="Goal compuesto no soportado"):
        planner.generate("do_everything", {})


def test_plan_generation_for_sequence_keeps_correct_order():
    planner = Planner()

    plan = planner.generate("recalculate_and_simulate", {"project_id": "abc123"})

    assert plan.execution_type.value == "sequence"
    assert [step.action.value for step in plan.steps] == ["calculate", "simulate"]


def test_invalid_plan_when_simulate_has_no_project():
    planner = Planner()

    with pytest.raises(PlanValidationError):
        planner.generate("recalculate_and_simulate", {})


def test_pipeline_actions_are_not_expanded():
    planner = Planner()

    plan = planner.generate("iterate_and_validate", {"project_id": "abc123"})

    assert len(plan.steps) == 1
    assert plan.steps[0].action.value == "iterate"
