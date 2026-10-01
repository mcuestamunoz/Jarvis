"""Tests T1-T8 for `B1-assistant-vehicle-return-home-task` (T10).

Fifth vehicle Assistant Task kind — closes basic mando set
(TAKEOFF/HOLD/GO_TO/RETURN_HOME/LAND). Same seam as prior vehicle Buys.
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
    CAPABILITY_FLIGHT_RETURN_HOME,
    TASK_KIND_REQUEST_RETURN_HOME,
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
        raise AssertionError("llm must not be called for a RETURN_HOME phrase")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm must not be called for a RETURN_HOME phrase")

    def complete(self, *args, **kwargs):
        raise AssertionError("llm must not be called for a RETURN_HOME phrase")


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


def test_t1_return_home_phrase_yields_task_with_capability():
    for raw in (
        "return home",
        "returnhome",
        "rtl",
        "rth",
        "vuelve",
        "volver",
        "vuelve a casa",
        "volver a casa",
        "casa",
        "home",
        "Return Home",
        "cáSa",
    ):
        intent = _intent(raw)
        task = try_request_return_home_task(intent)
        assert isinstance(task, Task), f"{raw!r} should classify"
        assert task.required_capability_ids == [CAPABILITY_FLIGHT_RETURN_HOME]
        assert intent.metadata.get("task_kind") == TASK_KIND_REQUEST_RETURN_HOME


def test_t2_non_rtl_craft_line_yields_no_task():
    for raw in (
        "quiero diseñar un dron",
        "volver al board",
        "casa del frame",
        "home page del catalogo",
    ):
        intent = _intent(raw)
        assert try_request_return_home_task(intent) is None
        assert "task_kind" not in intent.metadata


def test_t3_prior_kinds_never_stolen_by_return_home():
    for raw in ("explain rtl", "explain casa", "estado", "resumen"):
        assert try_request_return_home_task(_intent(raw)) is None

    for raw, fn in (
        ("hold", try_request_hold_task),
        ("land", try_request_land_task),
        ("go to", try_request_go_to_task),
        ("takeoff", try_request_takeoff_task),
    ):
        assert try_request_return_home_task(_intent(raw)) is None
        assert fn(_intent(raw)) is not None


def test_t4_orchestrator_return_home_honest_reject_precedence_intact():
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()

    for raw in ("rtl", "return home", "casa"):
        result = orch.handle_user_text(raw, exploding)
        assert result["status"] == "ok"
        assert result["action"] == "vehicle_return_home"
        assert "disarmed" in result["message"]
        assert "reject" in result["message"]
        assert "executed" not in result["message"].lower()

    assert orch.handle_user_text("explain imu", exploding)["action"] == "global_command"
    assert orch.handle_user_text("estado", exploding)["action"] == "project_status"
    assert orch.handle_user_text("hold", exploding)["action"] == "vehicle_hold"
    assert orch.handle_user_text("land", exploding)["action"] == "vehicle_land"
    assert orch.handle_user_text("go to", exploding)["action"] == "vehicle_go_to"
    assert orch.handle_user_text("takeoff", exploding)["action"] == "vehicle_takeoff"


def test_t5_seed_flight_return_home_honesty_prior_rows_and_allowlist():
    registry = CapabilityRegistry.load_default()

    cap = registry.get_capability("flight.return_home")
    assert cap is not None
    assert cap.availability == CapabilityAvailability.NOT_IMPLEMENTED
    assert cap.provider_id == "provider.flight_return_home"

    provider = registry.get_provider("provider.flight_return_home")
    assert provider is not None
    assert provider.kind == ProviderKind.VEHICLE
    assert provider.offered_capability_ids == ["flight.return_home"]

    skill_ids = {s.id for s in registry.skills()}
    assert "skill.request_return_home" in skill_ids
    skill = next(s for s in registry.skills() if s.id == "skill.request_return_home")
    assert skill.required_capability_ids == ["flight.return_home"]
    assert skill.availability == CapabilityAvailability.STUB

    assert {
        "ontology.explain",
        "engineering.continuity",
        "flight.hold",
        "flight.land",
        "flight.go_to",
        "flight.takeoff",
    } <= {c.id for c in registry.capabilities()}
    assert {
        "skill.explain_concept",
        "skill.project_status",
        "skill.request_hold",
        "skill.request_land",
        "skill.request_go_to",
        "skill.request_takeoff",
    } <= skill_ids

    # T14 (B1-assistant-vehicle-allowlist-widen): widened to the full
    # seven-verb chat set.
    assert ArmedAllowlistSafetyGate._ALLOWED_VERBS == frozenset(
        {"HOLD", "LAND", "GO_TO", "TAKEOFF", "RETURN_HOME", "FOLLOW", "PATROL"}
    )


def test_t6_fences_return_home_ast():
    forbidden = ("jarvis.core", "jarvis.flight_software", "jarvis.vehicle_profiles")
    imported = _imported_module_names(ASSISTANT_TASK_PATH)
    for module_name in imported:
        for forbidden_root in forbidden:
            assert not (
                module_name == forbidden_root or module_name.startswith(forbidden_root + ".")
            ), f"assistant_task.py imports forbidden module '{module_name}'"


def test_t7_default_safety_gate_reject_all_fulfill_disarmed_empty_params():
    assert isinstance(default_safety_gate(), RejectAllSafetyGate)
    assert ArmedAllowlistSafetyGate().armed is False

    command = propose_command(AutonomyVerb.RETURN_HOME, params={})
    assert command.params == {}
    # T14 widened the allow-list — disarmed still rejects regardless of
    # membership; membership itself is asserted in test_t5 above.
    assert "RETURN_HOME" in ArmedAllowlistSafetyGate._ALLOWED_VERBS

    orch = JarvisOrchestrator()
    result = orch.handle_user_text("rtl", _ExplodingLLMInterface())
    assert "disarmed" in result["message"]
    assert result["action"] == "vehicle_return_home"


def test_t8_pyproject_version_is_0_6_18():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.6.25"' in text
