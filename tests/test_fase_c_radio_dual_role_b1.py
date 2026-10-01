"""Tests T1-T10 for `B1-fase-c-radio-dual-role`.

T11 (full craft suite stays green) and T12 (report confirms dual-role +
no live ELRS + no Safety bypass) are process gates covered by running the
full suite and by
`.jes/artifacts/implementation_report_fase_c_radio_dual_role_b1.md`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from jarvis.capabilities import (
    CapabilityRegistry,
    Intent,
    IntentSource,
    RadioDualRoleResult,
    RadioIntentAdapter,
    RadioStubFrame,
    SimulatedRadioIngress,
    default_safety_gate,
    describe_dual_role,
)
from jarvis.capabilities.safety import AuthoritySignal, SafetyRequest
from jarvis.capabilities import radio as radio_module

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_t1_intent_role_frame_yields_intent_only():
    ingress = SimulatedRadioIngress()
    frame = RadioStubFrame(role="intent", intent_text="RETURN_HOME")
    result = ingress.ingest(frame)
    assert isinstance(result, RadioDualRoleResult)
    assert result.intent is not None
    assert result.intent.source == IntentSource.RADIO
    assert result.intent.raw_text == "RETURN_HOME"
    assert result.authority is None


def test_t2_authority_role_frame_yields_authority_only():
    ingress = SimulatedRadioIngress()
    frame = RadioStubFrame(role="authority", authority_kind="kill")
    result = ingress.ingest(frame)
    assert result.authority is not None
    assert isinstance(result.authority, AuthoritySignal)
    assert result.authority.source == "radio"
    assert result.authority.kind == "kill"
    assert result.intent is None


def test_t3_both_role_frame_yields_both_as_distinct_types():
    ingress = SimulatedRadioIngress()
    frame = RadioStubFrame(role="both", intent_text="HOLD", authority_kind="mode")
    result = ingress.ingest(frame)
    assert result.intent is not None and isinstance(result.intent, Intent)
    assert result.authority is not None and isinstance(result.authority, AuthoritySignal)
    assert type(result.intent) is not type(result.authority)


def test_t4_radio_intent_adapter_still_not_implemented():
    with pytest.raises(NotImplementedError, match="not_implemented"):
        RadioIntentAdapter.parse("anything")


def test_t5_no_decode_or_driver_shaped_public_methods_in_radio_module():
    forbidden_substrings = ("decode_crsf", "decode_elrs", "open_serial", "write_pwm")
    for name, obj in vars(radio_module).items():
        if name.startswith("_"):
            continue
        if isinstance(obj, type) and issubclass(obj, BaseModel):
            attr_names = list(obj.model_fields)
        elif isinstance(obj, type):
            attr_names = [n for n in dir(obj) if not n.startswith("_")]
        elif callable(obj):
            attr_names = [name]
        else:
            continue
        for attr_name in attr_names:
            lowered = attr_name.lower()
            for token in forbidden_substrings:
                assert token not in lowered, (
                    f"radio.{name}.{attr_name} looks like a driver path (matched '{token}')"
                )


def test_t6_default_safety_still_rejects_with_authority_signal_id_set():
    decision = default_safety_gate().evaluate(
        SafetyRequest(authority_signal_id="some-authority-id")
    )
    assert decision.outcome == "reject"


def test_t7_no_cpp_or_cmake_under_capabilities():
    forbidden_suffixes = (".cpp", ".cc", ".cxx", ".hpp", ".hh", ".h")
    capabilities_dir = REPO_ROOT / "src" / "jarvis" / "capabilities"
    for path in capabilities_dir.rglob("*"):
        if not path.is_file():
            continue
        assert path.suffix not in forbidden_suffixes, f"C++ source found: {path}"
        assert path.name != "CMakeLists.txt", f"CMake tree found: {path}"


def test_t8_radio_not_imported_by_orchestrator_or_craft_paths():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "capabilities.radio" not in text, (
                f"{py_file} imports capabilities.radio — forbidden craft coupling"
            )


def test_t9_capability_registry_default_still_empty():
    registry = CapabilityRegistry.load_default()
    # T2 (B1-capability-registry-product-fill): capabilities()/providers() are
    # no longer empty (ontology.explain/engineering.continuity, both software-
    # provided) — see tests/test_capability_registry_product_fill_b1.py. T5
    # (B1-capability-skills-seed): skills() is no longer empty either — two
    # declared-only stub rows — see tests/test_capability_skills_seed_b1.py.
    # T6 (B1-assistant-vehicle-hold-task): a third declared-only stub skill,
    # skill.request_hold (requires flight.hold, not_implemented/vehicle) —
    # see tests/test_assistant_vehicle_hold_task_b1.py. T7
    # (B1-assistant-vehicle-land-task): a fourth, skill.request_land
    # (requires flight.land, not_implemented/vehicle) — see
    # tests/test_assistant_vehicle_land_task_b1.py. T8
    # (B1-assistant-vehicle-go-to-task): a fifth, skill.request_go_to
    # (requires flight.go_to, not_implemented/vehicle) — see
    # tests/test_assistant_vehicle_go_to_task_b1.py. T9
    # (B1-assistant-vehicle-takeoff-task): a sixth, skill.request_takeoff
    # (requires flight.takeoff, not_implemented/vehicle) — see
    # tests/test_assistant_vehicle_takeoff_task_b1.py. T10
    # (B1-assistant-vehicle-return-home-task): a seventh, skill.request_return_home
    # (requires flight.return_home, not_implemented/vehicle) — see
    # tests/test_assistant_vehicle_return_home_task_b1.py. T11
    # (B1-assistant-vehicle-arm-ux): eighth+ninth, skill.request_arm_policy /
    # skill.request_disarm_policy (require safety.chat_armed_allowlist,
    # available/software) — see tests/test_assistant_vehicle_arm_ux_b1.py.
    # T12 (B1-assistant-vehicle-follow-task): a tenth, skill.request_follow
    # (requires flight.follow, not_implemented/vehicle) — see
    # tests/test_assistant_vehicle_follow_task_b1.py.
    # T13 (B1-assistant-vehicle-patrol-task): an eleventh, skill.request_patrol
    # (requires flight.patrol, not_implemented/vehicle) — see
    # tests/test_assistant_vehicle_patrol_task_b1.py.
    # Still zero Skill execution path anywhere; this file's own isolation
    # proof is unaffected either way.
    assert {skill.id for skill in registry.skills()} == {
        "skill.explain_concept",
        "skill.project_status",
        "skill.request_hold",
        "skill.request_land",
        "skill.request_go_to",
        "skill.request_takeoff",
        "skill.request_return_home",
        "skill.request_arm_policy",
        "skill.request_disarm_policy",
        "skill.request_follow",
        "skill.request_patrol",
    }


def test_radio_stub_frame_rejects_missing_intent_text_for_intent_role():
    with pytest.raises(ValidationError):
        RadioStubFrame(role="intent")


def test_radio_stub_frame_rejects_missing_authority_kind_for_authority_role():
    with pytest.raises(ValidationError):
        RadioStubFrame(role="authority")


def test_radio_stub_frame_rejects_intent_text_on_authority_only_role():
    with pytest.raises(ValidationError):
        RadioStubFrame(role="authority", authority_kind="mode", intent_text="leaked intent")


def test_radio_stub_frame_rejects_authority_kind_on_intent_only_role():
    with pytest.raises(ValidationError):
        RadioStubFrame(role="intent", intent_text="HOLD", authority_kind="mode")


def test_radio_stub_frame_has_no_raw_channel_map_field():
    assert "channels" not in RadioStubFrame.model_fields


def test_radio_dual_role_result_rejects_empty_result():
    with pytest.raises(ValidationError):
        RadioDualRoleResult(frame_id="x")


def test_describe_dual_role_is_pure_and_readable():
    ingress = SimulatedRadioIngress()
    frame = RadioStubFrame(role="both", intent_text="LAND", authority_kind="override")
    result = ingress.ingest(frame)
    description = describe_dual_role(result)
    assert "intent(" in description
    assert "authority(" in description
    assert result.frame_id in description
