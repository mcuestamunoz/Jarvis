"""Tests T1–T9 for `B1-assistant-vehicle-patrol-task` (T13).

Seventh and last vehicle Assistant Task kind — PATROL via shared chat
ArmedAllowlist. Last C4 AutonomyVerb without a chat Task.
"""

from __future__ import annotations

import ast
from pathlib import Path

from jarvis.capabilities.intent import Task, TerminalIntentAdapter
from jarvis.capabilities.registry import CapabilityRegistry
from jarvis.capabilities.safety import (
    ArmedAllowlistSafetyGate,
    RejectAllSafetyGate,
    default_safety_gate,
)
from jarvis.capabilities.schemas import CapabilityAvailability, ProviderKind
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command
from jarvis.intelligence.assistant_task import (
    CAPABILITY_FLIGHT_PATROL,
    TASK_KIND_REQUEST_PATROL,
    try_request_arm_policy_task,
    try_request_disarm_policy_task,
    try_request_follow_task,
    try_request_go_to_task,
    try_request_hold_task,
    try_request_land_task,
    try_request_patrol_task,
    try_request_return_home_task,
    try_request_takeoff_task,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSISTANT_TASK_PATH = REPO_ROOT / "src" / "jarvis" / "intelligence" / "assistant_task.py"


class _ExplodingLLMInterface:
    def interpret(self, *args, **kwargs):
        raise AssertionError("llm must not be called for a PATROL phrase")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm must not be called for a PATROL phrase")

    def complete(self, *args, **kwargs):
        raise AssertionError("llm must not be called for a PATROL phrase")


def _imported_module_names(source_path: Path) -> set[str]:
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def _intent(raw_text: str):
    return TerminalIntentAdapter.parse(raw_text)


def test_t1_patrol_phrase_yields_task():
    for raw in (
        "patrol",
        "patrulla",
        "patrullar",
        "hacer patrulla",
        "start patrol",
        "iniciar patrulla",
        "PATROL",
        "Patrulla",
    ):
        intent = _intent(raw)
        task = try_request_patrol_task(intent)
        assert isinstance(task, Task), f"{raw!r} should classify"
        assert task.required_capability_ids == [CAPABILITY_FLIGHT_PATROL]
        assert intent.metadata.get("task_kind") == TASK_KIND_REQUEST_PATROL


def test_t2_non_patrol_craft_line_yields_no_task():
    for raw in (
        "patrulla del catalogo",
        "patrol the board",
        "patrol the board layout",
        "quiero diseñar un dron",
    ):
        intent = _intent(raw)
        assert try_request_patrol_task(intent) is None
        assert "task_kind" not in intent.metadata


def test_t3_prior_kinds_never_stolen_by_patrol():
    for raw in ("explain patrol", "estado", "resumen"):
        assert try_request_patrol_task(_intent(raw)) is None

    for raw, fn in (
        ("armar", try_request_arm_policy_task),
        ("desarmar", try_request_disarm_policy_task),
        ("hold", try_request_hold_task),
        ("land", try_request_land_task),
        ("go to", try_request_go_to_task),
        ("takeoff", try_request_takeoff_task),
        ("rtl", try_request_return_home_task),
        ("follow", try_request_follow_task),
    ):
        assert try_request_patrol_task(_intent(raw)) is None
        assert fn(_intent(raw)) is not None

    # Prior classifiers refuse PATROL phrases
    for fn in (
        try_request_arm_policy_task,
        try_request_disarm_policy_task,
        try_request_hold_task,
        try_request_land_task,
        try_request_go_to_task,
        try_request_takeoff_task,
        try_request_return_home_task,
        try_request_follow_task,
    ):
        assert fn(_intent("patrol")) is None


def test_t4_orchestrator_patrol_honest_disarmed_reject():
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()
    for raw in ("patrol", "patrulla", "iniciar patrulla"):
        result = orch.handle_user_text(raw, exploding)
        assert result["status"] == "ok"
        assert result["action"] == "vehicle_patrol"
        assert "disarmed" in result["message"]
        assert "reject" in result["message"]
        assert "executed" not in result["message"].lower()
        assert "circuito" in result["message"].lower() or "patrol" in result["message"].lower()


def test_t5_armar_then_patrol_verb_not_allowed_hold_still_allow():
    """T14 (`B1-assistant-vehicle-allowlist-widen`) widened the allow-list
    to the full seven-verb chat set — PATROL now joins HOLD at
    `allow`/`not_implemented` once armed, instead of `verb_not_allowed`."""
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()
    assert orch.handle_user_text("armar", exploding)["action"] == "vehicle_arm_policy"
    patrol = orch.handle_user_text("patrol", exploding)
    assert patrol["action"] == "vehicle_patrol"
    assert "allow" in patrol["message"]
    assert "not_implemented" in patrol["message"]
    hold = orch.handle_user_text("hold", exploding)
    assert hold["action"] == "vehicle_hold"
    assert "allow" in hold["message"]
    assert "not_implemented" in hold["message"]


def test_t6_seed_honesty_prior_rows_allowlist_unwidened():
    registry = CapabilityRegistry.load_default()

    cap = registry.get_capability("flight.patrol")
    assert cap is not None
    assert cap.availability == CapabilityAvailability.NOT_IMPLEMENTED
    assert cap.provider_id == "provider.flight_patrol"
    assert cap.version == "0.6.21"

    provider = registry.get_provider("provider.flight_patrol")
    assert provider is not None
    assert provider.kind == ProviderKind.VEHICLE
    assert provider.offered_capability_ids == ["flight.patrol"]

    skill_ids = {s.id for s in registry.skills()}
    assert {
        "skill.request_patrol",
        "skill.request_follow",
        "skill.request_arm_policy",
        "skill.request_disarm_policy",
        "skill.request_return_home",
        "skill.request_hold",
        "skill.explain_concept",
        "skill.project_status",
    } <= skill_ids
    assert len(skill_ids) == 11

    cap_ids = {c.id for c in registry.capabilities()}
    assert {
        "ontology.explain",
        "engineering.continuity",
        "flight.hold",
        "flight.land",
        "flight.go_to",
        "flight.takeoff",
        "flight.return_home",
        "safety.chat_armed_allowlist",
        "flight.follow",
        "flight.patrol",
    } <= cap_ids
    assert len(cap_ids) == 10

    # T14 (B1-assistant-vehicle-allowlist-widen): widened to the full
    # seven-verb chat set.
    assert ArmedAllowlistSafetyGate._ALLOWED_VERBS == frozenset(
        {"HOLD", "LAND", "GO_TO", "TAKEOFF", "RETURN_HOME", "FOLLOW", "PATROL"}
    )


def test_t7_ast_fence_shared_gate_empty_params():
    forbidden = ("jarvis.core", "jarvis.flight_software", "jarvis.vehicle_profiles")
    imported = _imported_module_names(ASSISTANT_TASK_PATH)
    for module_name in imported:
        for forbidden_root in forbidden:
            assert not (
                module_name == forbidden_root or module_name.startswith(forbidden_root + ".")
            ), f"assistant_task.py imports forbidden module '{module_name}'"
    assert isinstance(default_safety_gate(), RejectAllSafetyGate)

    command = propose_command(AutonomyVerb.PATROL, params={})
    assert command.params == {}
    assert command.verb == AutonomyVerb.PATROL
    assert "PATROL" in ArmedAllowlistSafetyGate._ALLOWED_VERBS

    orch = JarvisOrchestrator()
    gate = orch._vehicle_chat_safety_gate()
    assert gate is orch._vehicle_chat_safety_gate()
    # Shared with arm path: arm then patrol sees allow/not_implemented on
    # the same latch (T14 widened the allow-list).
    orch.handle_user_text("armar", _ExplodingLLMInterface())
    assert gate.armed is True
    assert gate is orch._vehicle_chat_safety_gate()
    patrol = orch.handle_user_text("patrol", _ExplodingLLMInterface())
    assert "allow" in patrol["message"]
    assert "not_implemented" in patrol["message"]


def test_t8_precedence_follow_then_patrol():
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()
    follow = orch.handle_user_text("follow", exploding)
    assert follow["action"] == "vehicle_follow"
    patrol = orch.handle_user_text("patrol", exploding)
    assert patrol["action"] == "vehicle_patrol"
    # FOLLOW phrase must not be stolen by PATROL
    assert try_request_patrol_task(_intent("follow")) is None
    assert try_request_follow_task(_intent("follow")) is not None


def test_t9_pyproject_version_is_0_6_21():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.6.25"' in text
