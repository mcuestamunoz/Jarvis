"""Tests T1-T8 for `B1-assistant-vehicle-hold-task` (T6).

The first **vehicle** Assistant Task kind: a finite HOLD phrase table
(`jarvis.config.VEHICLE_HOLD_PHRASES`) classifies to `Task(request_hold)`
requiring `flight.hold`, membership-checked the same way every other
kind is (T3-style) but deliberately **without** `SoftwareCapabilitySafetyGate`
(T4's gate only ever allows `available`+`software`; `flight.hold` is
intentionally `not_implemented`+`vehicle`). Fulfilled entirely by the
orchestrator (`_handle_vehicle_hold`) via the existing C4 autonomy
surface (`propose_command`/`submit_command`) with a **fresh, never-armed**
`ArmedAllowlistSafetyGate` — the product chat path never calls `arm()`.
Precedence: explain -> Continuity defer -> HOLD -> fallthrough.
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
    CAPABILITY_FLIGHT_HOLD,
    TASK_KIND_REQUEST_HOLD,
    try_request_hold_task,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSISTANT_TASK_PATH = REPO_ROOT / "src" / "jarvis" / "intelligence" / "assistant_task.py"


class _ExplodingLLMInterface:
    def interpret(self, *args, **kwargs):
        raise AssertionError("llm_interface.interpret must not be called for a HOLD phrase")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm_interface.analyze must not be called for a HOLD phrase")

    def complete(self, *args, **kwargs):
        raise AssertionError("LLM complete must not be called for a HOLD phrase")


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


def test_t1_hold_phrase_yields_task_with_capability():
    for raw in ("hold", "mantener", "Hold Position", "quédate", "mantener posición"):
        intent = _intent(raw)
        task = try_request_hold_task(intent)
        assert isinstance(task, Task), f"{raw!r} should classify"
        assert task.required_capability_ids == [CAPABILITY_FLIGHT_HOLD]
        assert task.intent_id == intent.id
        assert intent.metadata.get("task_kind") == TASK_KIND_REQUEST_HOLD


def test_t2_non_hold_craft_line_yields_no_task():
    for raw in (
        "quiero diseñar un dron",
        "cambia el motor a XING-E",
        "mantener el frame en la placa",
        "monta el frame en la placa",
    ):
        intent = _intent(raw)
        assert try_request_hold_task(intent) is None
        assert "task_kind" not in intent.metadata


def test_t3_explain_or_continuity_shaped_line_never_gets_hold_task():
    for raw in ("explain hold", "jarvis explain mantener", "explain c-rate"):
        intent = _intent(raw)
        assert try_request_hold_task(intent) is None

    for raw in ("estado", "resumen", "que falta"):
        intent = _intent(raw)
        assert try_request_hold_task(intent) is None


def test_t4_orchestrator_hold_phrase_is_honest_reject_no_llm():
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()

    for raw in ("hold", "mantener", "HOLD"):
        result = orch.handle_user_text(raw, exploding)
        assert result["status"] == "ok"
        assert result["action"] == "vehicle_hold"
        assert "disarmed" in result["message"]
        assert "reject" in result["message"]
        assert "ejecuta" in result["message"].lower()
        assert "executed" not in result["message"].lower()

    # Precedence still holds through the full orchestrator path.
    explain_result = orch.handle_user_text("explain imu", exploding)
    assert explain_result["action"] == "global_command"
    status_result = orch.handle_user_text("estado", exploding)
    assert status_result["action"] == "project_status"


def test_t5_seed_flight_hold_not_implemented_vehicle_provider_skill_stub():
    registry = CapabilityRegistry.load_default()

    hold_capability = registry.get_capability("flight.hold")
    assert hold_capability is not None
    assert hold_capability.availability == CapabilityAvailability.NOT_IMPLEMENTED
    assert hold_capability.provider_id == "provider.flight_hold"

    hold_provider = registry.get_provider("provider.flight_hold")
    assert hold_provider is not None
    assert hold_provider.kind == ProviderKind.VEHICLE
    assert hold_provider.offered_capability_ids == ["flight.hold"]

    skill_ids = {s.id for s in registry.skills()}
    assert "skill.request_hold" in skill_ids
    hold_skill = next(s for s in registry.skills() if s.id == "skill.request_hold")
    assert hold_skill.required_capability_ids == ["flight.hold"]
    assert hold_skill.availability == CapabilityAvailability.STUB

    # T2/T5 software rows are still present and untouched by this Buy.
    capability_ids = {c.id for c in registry.capabilities()}
    assert {"ontology.explain", "engineering.continuity"} <= capability_ids
    software_skill_ids = {"skill.explain_concept", "skill.project_status"}
    assert software_skill_ids <= skill_ids


def test_t6_fences_hold_ast():
    forbidden = (
        "jarvis.core",
        "jarvis.flight_software",
        "jarvis.vehicle_profiles",
    )
    imported = _imported_module_names(ASSISTANT_TASK_PATH)
    for module_name in imported:
        for forbidden_root in forbidden:
            assert not (
                module_name == forbidden_root or module_name.startswith(forbidden_root + ".")
            ), f"assistant_task.py imports forbidden module '{module_name}'"


def test_t7_default_safety_gate_still_reject_all_and_fulfill_uses_disarmed_armed_allowlist():
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)

    # Unit-level: the exact gate type/instance policy the orchestrator's
    # own _handle_vehicle_hold constructs — fresh, never armed.
    fresh_gate = ArmedAllowlistSafetyGate()
    assert fresh_gate.armed is False

    orch = JarvisOrchestrator()
    result = orch.handle_user_text("hold", _ExplodingLLMInterface())
    assert "disarmed" in result["message"]
    assert result["status"] == "ok"


def test_t8_pyproject_version_is_0_6_14():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.6.20"' in text
