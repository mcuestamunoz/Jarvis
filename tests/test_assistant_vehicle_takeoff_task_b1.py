"""Tests T1-T8 for `B1-assistant-vehicle-takeoff-task` (T9).

The **fourth** vehicle Assistant Task kind, same seam as T6's HOLD/T7's
LAND/T8's GO_TO: a finite TAKEOFF phrase table
(`jarvis.config.VEHICLE_TAKEOFF_PHRASES`) classifies to
`Task(request_takeoff)` requiring `flight.takeoff`, membership-checked
the same way every other kind is (T3-style) but deliberately
**without** `SoftwareCapabilitySafetyGate` (T4's gate only ever allows
`available`+`software`; `flight.takeoff` is intentionally
`not_implemented`+`vehicle`). Fulfilled entirely by the orchestrator
(`_handle_vehicle_takeoff`) via the existing C4 autonomy surface
(`propose_command`/`submit_command`) with a **fresh, never-armed**
`ArmedAllowlistSafetyGate` — the product chat path never calls `arm()`.
No altitude parsing this Buy — `params` is always empty. Precedence:
explain -> Continuity defer -> HOLD -> LAND -> GO_TO -> TAKEOFF ->
fallthrough.
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
    CAPABILITY_FLIGHT_TAKEOFF,
    TASK_KIND_REQUEST_TAKEOFF,
    try_request_go_to_task,
    try_request_hold_task,
    try_request_land_task,
    try_request_takeoff_task,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSISTANT_TASK_PATH = REPO_ROOT / "src" / "jarvis" / "intelligence" / "assistant_task.py"


class _ExplodingLLMInterface:
    def interpret(self, *args, **kwargs):
        raise AssertionError("llm_interface.interpret must not be called for a TAKEOFF phrase")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm_interface.analyze must not be called for a TAKEOFF phrase")

    def complete(self, *args, **kwargs):
        raise AssertionError("LLM complete must not be called for a TAKEOFF phrase")


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


def test_t1_takeoff_phrase_yields_task_with_capability():
    for raw in (
        "takeoff",
        "take off",
        "Despegar",
        "despega",
        "despegue",
        "levanta",
        "levantar",
        "sube",
        "ascender",
    ):
        intent = _intent(raw)
        task = try_request_takeoff_task(intent)
        assert isinstance(task, Task), f"{raw!r} should classify"
        assert task.required_capability_ids == [CAPABILITY_FLIGHT_TAKEOFF]
        assert task.intent_id == intent.id
        assert intent.metadata.get("task_kind") == TASK_KIND_REQUEST_TAKEOFF


def test_t2_non_takeoff_craft_line_yields_no_task():
    for raw in (
        "quiero diseñar un dron",
        "cambia el motor a XING-E",
        "sube el volumen",
        "monta el frame en la placa",
    ):
        intent = _intent(raw)
        assert try_request_takeoff_task(intent) is None
        assert "task_kind" not in intent.metadata


def test_t3_explain_continuity_hold_land_or_go_to_shaped_line_never_gets_takeoff_task():
    for raw in ("explain takeoff", "jarvis explain despega", "explain c-rate"):
        intent = _intent(raw)
        assert try_request_takeoff_task(intent) is None

    for raw in ("estado", "resumen", "que falta"):
        intent = _intent(raw)
        assert try_request_takeoff_task(intent) is None

    for raw in ("hold", "mantener", "quédate", "hold position"):
        intent = _intent(raw)
        assert try_request_takeoff_task(intent) is None
        # HOLD's own classifier must be unaffected by TAKEOFF's guard.
        assert try_request_hold_task(_intent(raw)) is not None

    for raw in ("land", "aterrizar", "baja", "descender"):
        intent = _intent(raw)
        assert try_request_takeoff_task(intent) is None
        # LAND's own classifier must be unaffected by TAKEOFF's guard.
        assert try_request_land_task(_intent(raw)) is not None

    for raw in ("go to", "goto", "ve a", "navega"):
        intent = _intent(raw)
        assert try_request_takeoff_task(intent) is None
        # GO_TO's own classifier must be unaffected by TAKEOFF's guard.
        assert try_request_go_to_task(_intent(raw)) is not None


def test_t4_orchestrator_takeoff_phrase_is_honest_reject_no_llm_prior_precedence_intact():
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()

    for raw in ("takeoff", "despega", "TAKEOFF"):
        result = orch.handle_user_text(raw, exploding)
        assert result["status"] == "ok"
        assert result["action"] == "vehicle_takeoff"
        assert "disarmed" in result["message"]
        assert "reject" in result["message"]
        assert "ejecuta" in result["message"].lower()
        assert "executed" not in result["message"].lower()
        assert "airborne" not in result["message"].lower()

    # Precedence still holds through the full orchestrator path, HOLD/LAND/GO_TO included.
    explain_result = orch.handle_user_text("explain imu", exploding)
    assert explain_result["action"] == "global_command"
    status_result = orch.handle_user_text("estado", exploding)
    assert status_result["action"] == "project_status"
    hold_result = orch.handle_user_text("hold", exploding)
    assert hold_result["action"] == "vehicle_hold"
    assert "disarmed" in hold_result["message"]
    land_result = orch.handle_user_text("land", exploding)
    assert land_result["action"] == "vehicle_land"
    assert "disarmed" in land_result["message"]
    go_to_result = orch.handle_user_text("go to", exploding)
    assert go_to_result["action"] == "vehicle_go_to"
    assert "disarmed" in go_to_result["message"]


def test_t5_seed_flight_takeoff_not_implemented_vehicle_provider_skill_stub_prior_rows_untouched():
    registry = CapabilityRegistry.load_default()

    takeoff_capability = registry.get_capability("flight.takeoff")
    assert takeoff_capability is not None
    assert takeoff_capability.availability == CapabilityAvailability.NOT_IMPLEMENTED
    assert takeoff_capability.provider_id == "provider.flight_takeoff"

    takeoff_provider = registry.get_provider("provider.flight_takeoff")
    assert takeoff_provider is not None
    assert takeoff_provider.kind == ProviderKind.VEHICLE
    assert takeoff_provider.offered_capability_ids == ["flight.takeoff"]

    skill_ids = {s.id for s in registry.skills()}
    assert "skill.request_takeoff" in skill_ids
    takeoff_skill = next(s for s in registry.skills() if s.id == "skill.request_takeoff")
    assert takeoff_skill.required_capability_ids == ["flight.takeoff"]
    assert takeoff_skill.availability == CapabilityAvailability.STUB

    # HOLD (T6), LAND (T7), GO_TO (T8), and software (T2/T5) rows are still present.
    for capability_id in ("flight.hold", "flight.land", "flight.go_to"):
        capability = registry.get_capability(capability_id)
        assert capability is not None
        assert capability.availability == CapabilityAvailability.NOT_IMPLEMENTED
    assert {"skill.request_hold", "skill.request_land", "skill.request_go_to"} <= skill_ids

    capability_ids = {c.id for c in registry.capabilities()}
    assert {
        "ontology.explain",
        "engineering.continuity",
        "flight.hold",
        "flight.land",
        "flight.go_to",
    } <= capability_ids
    software_skill_ids = {"skill.explain_concept", "skill.project_status"}
    assert software_skill_ids <= skill_ids

    # Separate providers per DC §0 row 5 — no merge, all four vehicle rows distinct.
    vehicle_provider_ids = {
        registry.get_provider("provider.flight_hold").id,
        registry.get_provider("provider.flight_land").id,
        registry.get_provider("provider.flight_go_to").id,
        registry.get_provider("provider.flight_takeoff").id,
    }
    assert len(vehicle_provider_ids) == 4


def test_t6_fences_takeoff_ast():
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


def test_t7_default_safety_gate_reject_all_disarmed_armed_allowlist_empty_params_verb_not_on_allowlist():
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)

    # Unit-level: the exact gate type/instance policy the orchestrator's
    # own _handle_vehicle_takeoff constructs — fresh, never armed.
    fresh_gate = ArmedAllowlistSafetyGate()
    assert fresh_gate.armed is False

    from jarvis.flight_software.autonomy import AutonomyVerb, propose_command

    command = propose_command(AutonomyVerb.TAKEOFF, params={})
    assert command.params == {}

    orch = JarvisOrchestrator()
    result = orch.handle_user_text("takeoff", _ExplodingLLMInterface())
    assert "disarmed" in result["message"]
    assert result["status"] == "ok"

    # DC §0 row 7: TAKEOFF is still not on ArmedAllowlistSafetyGate's own
    # allow-list this Buy (unwidened) — irrelevant on the always-disarmed
    # product path, but documented here as the honest current shape.
    assert "TAKEOFF" not in ArmedAllowlistSafetyGate._ALLOWED_VERBS
    assert ArmedAllowlistSafetyGate._ALLOWED_VERBS == frozenset({"HOLD", "LAND", "GO_TO"})


def test_t8_pyproject_version_is_0_6_17():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.6.18"' in text
