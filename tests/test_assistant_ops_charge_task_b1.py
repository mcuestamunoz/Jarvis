"""Tests T1-T7 for `B1-assistant-ops-charge-task` (T19).

First **ops** Assistant Task kind — CHARGE is deliberately NOT an
AutonomyVerb. No ArmedAllowlist, no SoftwareCapabilitySafetyGate, no
propose_command/sim executor from this fulfill.
"""

from __future__ import annotations

import ast
from pathlib import Path

from jarvis.capabilities.intent import Task, TerminalIntentAdapter
from jarvis.capabilities.registry import CapabilityRegistry
from jarvis.capabilities.schemas import CapabilityAvailability, ProviderKind
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.intelligence.assistant_task import (
    CAPABILITY_OPS_CHARGE,
    TASK_KIND_REQUEST_CHARGE,
    try_request_arm_policy_task,
    try_request_charge_task,
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
        raise AssertionError("llm must not be called for a CHARGE phrase")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm must not be called for a CHARGE phrase")

    def complete(self, *args, **kwargs):
        raise AssertionError("llm must not be called for a CHARGE phrase")


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


def test_t1_charge_phrase_yields_task():
    for raw in (
        "charge",
        "cargar",
        "cargar bateria",
        "cargar la bateria",
        "charge battery",
        "iniciar carga",
        "CHARGE",
        "Cargar Batería",
    ):
        intent = _intent(raw)
        task = try_request_charge_task(intent)
        assert isinstance(task, Task), f"{raw!r} should classify"
        assert task.required_capability_ids == [CAPABILITY_OPS_CHARGE]
        assert intent.metadata.get("task_kind") == TASK_KIND_REQUEST_CHARGE


def test_t2_payload_mission_lines_yield_no_task():
    for raw in (
        "carga util",
        "carga útil",
        "aumentar la carga",
        "carga util kg",
        "quiero diseñar un dron",
    ):
        intent = _intent(raw)
        assert try_request_charge_task(intent) is None
        assert "task_kind" not in intent.metadata


def test_t3_prior_kinds_never_stolen_by_charge():
    for raw in ("explain charge", "estado", "resumen"):
        assert try_request_charge_task(_intent(raw)) is None

    for raw, fn in (
        ("armar", try_request_arm_policy_task),
        ("desarmar", try_request_disarm_policy_task),
        ("hold", try_request_hold_task),
        ("land", try_request_land_task),
        ("go to", try_request_go_to_task),
        ("takeoff", try_request_takeoff_task),
        ("rtl", try_request_return_home_task),
        ("follow", try_request_follow_task),
        ("patrol", try_request_patrol_task),
    ):
        assert try_request_charge_task(_intent(raw)) is None
        assert fn(_intent(raw)) is not None


def test_t4_orchestrator_charge_honest_not_implemented():
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()
    for raw in ("charge", "cargar", "cargar bateria"):
        result = orch.handle_user_text(raw, exploding)
        assert result["status"] == "ok"
        assert result["action"] == "ops_charge"
        assert "no" in result["message"].lower()
        assert "implementad" in result["message"].lower()
        assert "executed" not in result["message"].lower()
        assert "ejecutada" not in result["message"].lower()
        assert "AutonomyVerb" in result["message"]


def test_t4b_charge_unaffected_by_arm_state():
    """CHARGE is not an AutonomyVerb — never touches ArmedAllowlistSafetyGate,
    so armed vs. disarmed must not change its honest not-implemented
    message shape."""
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()
    disarmed = orch.handle_user_text("charge", exploding)
    assert disarmed["action"] == "ops_charge"

    orch.handle_user_text("armar", exploding)
    armed = orch.handle_user_text("charge", exploding)
    assert armed["action"] == "ops_charge"
    assert armed["message"] == disarmed["message"]


def test_t5_seed_honesty_device_not_implemented_cascade_11_12():
    registry = CapabilityRegistry.load_default()

    cap = registry.get_capability("ops.charge")
    assert cap is not None
    assert cap.availability == CapabilityAvailability.NOT_IMPLEMENTED
    assert cap.provider_id == "provider.ops_charge"

    provider = registry.get_provider("provider.ops_charge")
    assert provider is not None
    assert provider.kind == ProviderKind.DEVICE
    assert provider.offered_capability_ids == ["ops.charge"]

    skill_ids = {s.id for s in registry.skills()}
    assert "skill.request_charge" in skill_ids
    skill = next(s for s in registry.skills() if s.id == "skill.request_charge")
    assert skill.required_capability_ids == ["ops.charge"]
    assert skill.availability == CapabilityAvailability.STUB
    assert len(skill_ids) == 12

    cap_ids = {c.id for c in registry.capabilities()}
    assert "ops.charge" in cap_ids
    assert len(cap_ids) == 11


def test_t6_ast_fence_no_flight_software_import():
    forbidden = ("jarvis.core", "jarvis.flight_software", "jarvis.vehicle_profiles")
    imported = _imported_module_names(ASSISTANT_TASK_PATH)
    for module_name in imported:
        for forbidden_root in forbidden:
            assert not (
                module_name == forbidden_root or module_name.startswith(forbidden_root + ".")
            ), f"assistant_task.py imports forbidden module '{module_name}'"


def test_t7_precedence_patrol_then_charge():
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()
    patrol = orch.handle_user_text("patrol", exploding)
    assert patrol["action"] == "vehicle_patrol"
    charge = orch.handle_user_text("charge", exploding)
    assert charge["action"] == "ops_charge"
    # PATROL phrase must not be stolen by CHARGE
    assert try_request_charge_task(_intent("patrol")) is None
    assert try_request_patrol_task(_intent("patrol")) is not None
