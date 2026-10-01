"""Tests T1–T10 for `B1-assistant-vehicle-arm-ux` (T11).

Safety policy latch (arm/disarm) + shared chat ArmedAllowlist consumed
by the five vehicle fulfills. Not an AutonomyVerb.
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
from jarvis.intelligence.assistant_task import (
    CAPABILITY_SAFETY_CHAT_ARMED_ALLOWLIST,
    TASK_KIND_REQUEST_ARM_POLICY,
    TASK_KIND_REQUEST_DISARM_POLICY,
    try_request_arm_policy_task,
    try_request_disarm_policy_task,
    try_request_go_to_task,
    try_request_hold_task,
    try_request_land_task,
    try_request_return_home_task,
    try_request_takeoff_task,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSISTANT_TASK_PATH = REPO_ROOT / "src" / "jarvis" / "intelligence" / "assistant_task.py"


class _ExplodingLLMInterface:
    def interpret(self, *args, **kwargs):
        raise AssertionError("llm must not be called for arm/disarm phrases")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm must not be called for arm/disarm phrases")

    def complete(self, *args, **kwargs):
        raise AssertionError("llm must not be called for arm/disarm phrases")


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


def test_t1_arm_phrase_yields_task():
    for raw in (
        "arm",
        "armar",
        "arma",
        "armar safety",
        "armar politica",
        "armar política",
        "arm safety",
        "ARMAR",
    ):
        intent = _intent(raw)
        task = try_request_arm_policy_task(intent)
        assert isinstance(task, Task), f"{raw!r} should classify"
        assert task.required_capability_ids == [CAPABILITY_SAFETY_CHAT_ARMED_ALLOWLIST]
        assert intent.metadata.get("task_kind") == TASK_KIND_REQUEST_ARM_POLICY


def test_t2_disarm_phrase_yields_task():
    for raw in ("disarm", "desarmar", "desarma", "disarm safety", "desarmar safety"):
        intent = _intent(raw)
        task = try_request_disarm_policy_task(intent)
        assert isinstance(task, Task), f"{raw!r} should classify"
        assert task.required_capability_ids == [CAPABILITY_SAFETY_CHAT_ARMED_ALLOWLIST]
        assert intent.metadata.get("task_kind") == TASK_KIND_REQUEST_DISARM_POLICY


def test_t3_non_arm_and_prior_kinds_not_stolen():
    for raw in ("arma el frame", "quiero diseñar un dron", "arm the stack"):
        assert try_request_arm_policy_task(_intent(raw)) is None
        assert try_request_disarm_policy_task(_intent(raw)) is None

    for raw in ("explain imu", "estado", "resumen"):
        assert try_request_arm_policy_task(_intent(raw)) is None
        assert try_request_disarm_policy_task(_intent(raw)) is None

    for raw, fn in (
        ("hold", try_request_hold_task),
        ("land", try_request_land_task),
        ("go to", try_request_go_to_task),
        ("takeoff", try_request_takeoff_task),
        ("rtl", try_request_return_home_task),
    ):
        assert try_request_arm_policy_task(_intent(raw)) is None
        assert try_request_disarm_policy_task(_intent(raw)) is None
        assert fn(_intent(raw)) is not None

    assert try_request_arm_policy_task(_intent("desarmar")) is None
    assert try_request_disarm_policy_task(_intent("armar")) is None


def test_t4_orchestrator_armar_honest_software_latch():
    orch = JarvisOrchestrator()
    result = orch.handle_user_text("armar", _ExplodingLLMInterface())
    assert result["status"] == "ok"
    assert result["action"] == "vehicle_arm_policy"
    lowered = result["message"].lower()
    assert "software" in lowered or "latch" in lowered or "política safety" in lowered or "politica safety" in lowered
    assert "esc" not in lowered or "no es armado de esc" in lowered
    assert orch._vehicle_chat_safety_gate().armed is True


def test_t5_armar_then_hold_allow_not_implemented():
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()
    assert orch.handle_user_text("armar", exploding)["action"] == "vehicle_arm_policy"
    hold = orch.handle_user_text("hold", exploding)
    assert hold["action"] == "vehicle_hold"
    assert "allow" in hold["message"]
    assert "not_implemented" in hold["message"]
    assert "disarmed" not in hold["message"]
    assert "executed" not in hold["message"].lower()


def test_t6_armar_then_rtl_and_takeoff_verb_not_allowed():
    """T14 (`B1-assistant-vehicle-allowlist-widen`) widened the allow-list
    to the full seven-verb chat set — RTL/TAKEOFF now join HOLD at
    `allow`/`not_implemented` once armed, instead of `verb_not_allowed`."""
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()
    orch.handle_user_text("armar", exploding)
    rtl = orch.handle_user_text("rtl", exploding)
    assert rtl["action"] == "vehicle_return_home"
    assert "allow" in rtl["message"]
    assert "not_implemented" in rtl["message"]
    takeoff = orch.handle_user_text("takeoff", exploding)
    assert takeoff["action"] == "vehicle_takeoff"
    assert "allow" in takeoff["message"]
    assert "not_implemented" in takeoff["message"]


def test_t7_armar_desarmar_hold_back_to_disarmed():
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()
    orch.handle_user_text("armar", exploding)
    disarm = orch.handle_user_text("desarmar", exploding)
    assert disarm["action"] == "vehicle_disarm_policy"
    assert orch._vehicle_chat_safety_gate().armed is False
    hold = orch.handle_user_text("hold", exploding)
    assert hold["action"] == "vehicle_hold"
    assert "disarmed" in hold["message"]


def test_t8_seed_honesty_prior_rows_allowlist_unwidened():
    registry = CapabilityRegistry.load_default()

    cap = registry.get_capability("safety.chat_armed_allowlist")
    assert cap is not None
    assert cap.availability == CapabilityAvailability.AVAILABLE
    assert cap.provider_id == "provider.safety_chat_armed_allowlist"

    provider = registry.get_provider("provider.safety_chat_armed_allowlist")
    assert provider is not None
    assert provider.kind == ProviderKind.SOFTWARE
    assert provider.offered_capability_ids == ["safety.chat_armed_allowlist"]

    skill_ids = {s.id for s in registry.skills()}
    assert {
        "skill.request_arm_policy",
        "skill.request_disarm_policy",
        "skill.request_return_home",
        "skill.request_hold",
        "skill.explain_concept",
        "skill.project_status",
    } <= skill_ids

    assert {
        "ontology.explain",
        "engineering.continuity",
        "flight.hold",
        "flight.land",
        "flight.go_to",
        "flight.takeoff",
        "flight.return_home",
        "safety.chat_armed_allowlist",
    } <= {c.id for c in registry.capabilities()}

    # T14 (B1-assistant-vehicle-allowlist-widen): widened to the full
    # seven-verb chat set.
    assert ArmedAllowlistSafetyGate._ALLOWED_VERBS == frozenset(
        {"HOLD", "LAND", "GO_TO", "TAKEOFF", "RETURN_HOME", "FOLLOW", "PATROL"}
    )


def test_t9_ast_fence_and_default_safety_gate():
    forbidden = ("jarvis.core", "jarvis.flight_software", "jarvis.vehicle_profiles")
    imported = _imported_module_names(ASSISTANT_TASK_PATH)
    for module_name in imported:
        for forbidden_root in forbidden:
            assert not (
                module_name == forbidden_root or module_name.startswith(forbidden_root + ".")
            ), f"assistant_task.py imports forbidden module '{module_name}'"
    assert isinstance(default_safety_gate(), RejectAllSafetyGate)


def test_t10_pyproject_version_is_0_6_19():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.6.25"' in text
