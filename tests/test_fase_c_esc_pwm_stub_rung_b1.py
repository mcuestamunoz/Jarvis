"""Tests T1-T11 for `B1-fase-c-esc-pwm-stub-rung`.

T12 (full craft suite stays green) and T13 (report confirms PWM-us only
+ sim sink + != motors spinning + C++ honesty) are process gates covered
by running the full suite and by
`.jes/artifacts/implementation_report_fase_c_esc_pwm_stub_rung_b1.md`.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command
from jarvis.flight_software.flight_control import (
    EscApplyResult,
    EscPwmCommand,
    MotorForceCommand,
    SimulatedEscSink,
    encode_motor_forces,
)
from jarvis.flight_software.flight_control import esc as esc_module
from jarvis.vehicle_profiles import run_esc_pwm_smoke

REPO_ROOT = Path(__file__).resolve().parents[1]


def _forces(values=(0.0, 0.5, 1.0, 0.25), t_s: float = 0.0) -> MotorForceCommand:
    return MotorForceCommand(t_s=t_s, motor_forces=values)


def test_t1_encoding_endpoints_and_midpoint():
    cmd = encode_motor_forces(_forces((0.0, 1.0, 0.5, 0.5)))
    assert cmd.pulse_us[0] == pytest.approx(1000.0)
    assert cmd.pulse_us[1] == pytest.approx(2000.0)
    assert cmd.pulse_us[2] == pytest.approx(1500.0)
    assert cmd.pulse_us[3] == pytest.approx(1500.0)


def test_t2_exactly_four_pulses_and_protocol():
    cmd = encode_motor_forces(_forces())
    assert isinstance(cmd, EscPwmCommand)
    assert len(cmd.pulse_us) == 4
    assert cmd.protocol == "pwm_us"


def test_t3_invalid_min_max_rejected():
    for min_us, max_us in ((1000.0, 1000.0), (1500.0, 1000.0), (float("nan"), 2000.0), (1000.0, float("inf"))):
        with pytest.raises(ValueError):
            encode_motor_forces(_forces(), min_us=min_us, max_us=max_us)


def test_t4_disarmed_apply_does_not_claim_success():
    sink = SimulatedEscSink()
    assert sink.armed is False
    cmd = encode_motor_forces(_forces())
    result = sink.apply(cmd)
    assert isinstance(result, EscApplyResult)
    assert result.applied is False
    assert result.reason == "disarmed"
    assert sink.last_command() == cmd


def test_t5_armed_apply_records_last_command():
    sink = SimulatedEscSink()
    sink.arm()
    assert sink.armed is True
    cmd = encode_motor_forces(_forces())
    result = sink.apply(cmd)
    assert result.applied is True
    assert result.reason is None
    assert sink.last_command() == cmd

    sink.disarm()
    assert sink.armed is False


def test_t6_no_gpio_serial_dshot_shaped_public_symbols():
    forbidden_substrings = (
        "write_gpio",
        "open_serial",
        "send_dshot",
        "pigpio",
        "export_pwm",
    )
    for name, obj in vars(esc_module).items():
        if name.startswith("_"):
            continue
        lowered = name.lower()
        for token in forbidden_substrings:
            assert token not in lowered, f"esc.{name} looks forbidden-shaped ('{token}')"
        if isinstance(obj, type):
            for attr_name in dir(obj):
                if attr_name.startswith("_"):
                    continue
                lowered_attr = attr_name.lower()
                for token in forbidden_substrings:
                    assert token not in lowered_attr, (
                        f"esc.{name}.{attr_name} looks forbidden-shaped ('{token}')"
                    )


def test_t6b_no_known_gpio_library_imports():
    import inspect

    source = inspect.getsource(esc_module)
    for forbidden_import in ("import RPi", "import pigpio", "import serial", "import socket"):
        assert forbidden_import not in source


def test_t7_no_cpp_or_cmake_under_flight_software():
    forbidden_suffixes = (".cpp", ".cc", ".cxx", ".hpp", ".hh", ".h")
    for package_dir in (
        REPO_ROOT / "src" / "jarvis" / "flight_software",
        REPO_ROOT / "src" / "jarvis" / "vehicle_profiles",
    ):
        for path in package_dir.rglob("*"):
            if not path.is_file():
                continue
            assert path.suffix not in forbidden_suffixes, f"C++ source found: {path}"
            assert path.name != "CMakeLists.txt", f"CMake tree found: {path}"


def test_t8_default_safety_and_autonomy_submit_still_reject():
    assert isinstance(default_safety_gate(), RejectAllSafetyGate)
    assert default_safety_gate().evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def _esc_fence_violations(source: str) -> list[str]:
    """B1-esc-fence-import-only (T16): AST-only scan — forbids a real
    `flight_control.esc` import (any module path containing that dotted
    segment, via `import`/`from ... import`) and any real binding or use
    of the name `SimulatedEscSink` (import, import-as-alias, bare name
    reference, or `.SimulatedEscSink` attribute access). `ast.parse`
    never represents comments at all, and a docstring/string literal is
    just an `ast.Constant`, which this function never inspects — so a
    comment or prose string naming `SimulatedEscSink` can never trigger a
    violation (DC §0 row 2: fence must be import-honest, not substring).
    Returns a list of human-readable violation descriptions; empty means
    the source is clean."""
    violations: list[str] = []
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if "flight_control.esc" in alias.name:
                    violations.append(f"import {alias.name}")
                if (alias.asname or alias.name.rsplit(".", 1)[-1]) == "SimulatedEscSink":
                    violations.append(f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else ""))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                full = f"{module}.{alias.name}" if module else alias.name
                if "flight_control.esc" in full:
                    violations.append(f"from {module} import {alias.name}")
                if alias.name == "SimulatedEscSink" or alias.asname == "SimulatedEscSink":
                    violations.append(f"from {module} import {alias.name}")
        elif isinstance(node, ast.Name) and node.id == "SimulatedEscSink":
            violations.append("name reference: SimulatedEscSink")
        elif isinstance(node, ast.Attribute) and node.attr == "SimulatedEscSink":
            violations.append("attribute reference: .SimulatedEscSink")
    return violations


def test_t9_esc_symbols_not_imported_by_orchestrator_or_craft_paths():
    """B1-esc-fence-import-only (T16): hardened to AST/import-only (DC
    §0 row 2) — the T11 arm-UX honesty comment ("Not
    SimulatedEscSink.arm().") names the symbol in prose to deny coupling,
    and must never trip this fence again (it previously did, under the
    old plain-substring version of this test)."""
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            source = py_file.read_text(encoding="utf-8")
            violations = _esc_fence_violations(source)
            assert not violations, f"{py_file} forbidden craft coupling: {violations}"


def test_t9b_fence_helper_is_import_honest_not_substring():
    """Negative controls proving `_esc_fence_violations` is AST/import-only,
    not a reintroduction of the old substring scan it replaces (IC §2
    T2/T3)."""
    # T3: a comment-only / prose mention must NOT fail — this is exactly
    # the T11 arm-UX false positive this Buy fixes.
    comment_only_source = (
        "# Distinct from the simulated ESC sink's own arm sequence — "
        "not SimulatedEscSink.arm(), never imported here.\n"
        "x = 1\n"
    )
    assert _esc_fence_violations(comment_only_source) == []

    docstring_source = (
        '"""This module never imports SimulatedEscSink or flight_control.esc."""\n'
        "x = 1\n"
    )
    assert _esc_fence_violations(docstring_source) == []

    # T2: a real import must still be detected.
    real_import_source = "from jarvis.flight_software.flight_control.esc import SimulatedEscSink\n"
    violations = _esc_fence_violations(real_import_source)
    assert violations, "a real SimulatedEscSink import must be flagged"

    aliased_import_source = "from jarvis.flight_software.flight_control import esc as _esc\n_esc.SimulatedEscSink()\n"
    assert _esc_fence_violations(aliased_import_source), "aliased module + attribute use must be flagged"

    bare_module_import_source = "from jarvis.flight_software.flight_control import esc\n"
    assert _esc_fence_violations(bare_module_import_source), "importing the esc submodule itself must be flagged"


def test_t10_capability_registry_default_still_empty():
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


def test_t11_pyproject_version_is_0_5_8():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.44"' in text


def test_pyproject_version_is_0_6_24():
    """B1-esc-fence-import-only (T16, IC §2 T4) — new checkpoint this Buy
    owns, distinct from `test_t11_pyproject_version_is_0_5_8` above
    (that one is a frozen, historical Fase C 0.5.x pin and stays
    untouched, per DC §0 row 5 / Engineer's explicit no-tip-pin-cleanup
    direction)."""
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.6.24"' in text


def test_smoke_esc_pwm_returns_at_least_one_result_disarmed_by_default():
    results = run_esc_pwm_smoke(samples=3)
    assert len(results) == 3
    assert all(isinstance(r, EscApplyResult) for r in results)
    assert all(r.applied is False for r in results)
    assert all(r.pulse_us is not None and len(r.pulse_us) == 4 for r in results)


def test_smoke_esc_pwm_armed_reports_applied():
    results = run_esc_pwm_smoke(samples=2, armed=True)
    assert all(r.applied is True for r in results)


def test_esc_pwm_command_rejects_wrong_length():
    with pytest.raises(Exception):
        EscPwmCommand(t_s=0.0, pulse_us=(1000.0, 1000.0, 1000.0))


def test_encode_clamps_out_of_range_force_defensively():
    cmd = encode_motor_forces(_forces((-1.0, 2.0, 0.0, 1.0)))
    assert cmd.pulse_us[0] == pytest.approx(1000.0)
    assert cmd.pulse_us[1] == pytest.approx(2000.0)


def test_custom_min_max_us_range():
    cmd = encode_motor_forces(_forces((0.0, 1.0, 0.5, 0.5)), min_us=900.0, max_us=2100.0)
    assert cmd.pulse_us[0] == pytest.approx(900.0)
    assert cmd.pulse_us[1] == pytest.approx(2100.0)
    assert cmd.pulse_us[2] == pytest.approx(1500.0)


def test_no_actuator_write_call_site_in_esc_module_source():
    """The module docstring is allowed to mention GPIO/serial/DShot in
    prose (documenting what it does not do) — this checks there is no
    actual call site."""
    import inspect

    source = inspect.getsource(esc_module)
    for forbidden_call in ("write_gpio(", "open_serial(", "send_dshot(", "pigpio.", "export_pwm("):
        assert forbidden_call not in source
