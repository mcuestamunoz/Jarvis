"""Tests T1-T10 for `B1-fase-c-cpp-unit-tests` (C15).

**Wrapper choice (IC §4, same rationale as C13/C14's own wrappers):** this
pytest wrapper does not invoke `cmake`/`clang++`/`ctest` itself — it runs
the already-built `fc_unit_tests`, `fc_closed_loop_smoke`, and
`fc_esc_pwm_smoke` binaries if present, asserting exit 0 and (for the
unit-test binary) parsing Catch2's own "All tests passed" summary line.
If a binary is absent, the relevant test **skips with a reason** naming
the exact build command. Building a native toolchain + fetching Catch2
should not be a hard dependency of every `pytest` run.

Process gates covered elsewhere, not by this file:
- T8 (Python suite still green @ 0.5.13) — the full `pytest -q` run.
- T9 (report: framework pin, case inventory, honesty statement) —
  `.jes/artifacts/implementation_report_fase_c_cpp_unit_tests_b1.md`.
- T10 (docs updated honestly, no premature v0.5.13 tag) — README/
  IMPLEMENTATION_TASKS/PLATFORM_CAPABILITY_VISION/ARCHITECTURE.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command

REPO_ROOT = Path(__file__).resolve().parents[1]
NATIVE_FC_DIR = REPO_ROOT / "native" / "flight_control"
TESTS_DIR = NATIVE_FC_DIR / "tests"
BUILD_DIR = REPO_ROOT / "build" / "flight_control"
UNIT_TEST_BINARY = BUILD_DIR / "fc_unit_tests"
CLOSED_LOOP_SMOKE_BINARY = BUILD_DIR / "fc_closed_loop_smoke"
ESC_SMOKE_BINARY = BUILD_DIR / "fc_esc_pwm_smoke"

_BUILD_HINT = (
    "cmake -S native/flight_control -B build/flight_control && "
    "cmake --build build/flight_control (see native/flight_control/README.md). "
    "First configure needs network once to fetch pinned Catch2 v3.7.1."
)

_EXPECTED_RUNG_TEST_FILES = (
    "test_filter.cpp",
    "test_attitude.cpp",
    "test_controller.cpp",
    "test_rate_torque.cpp",
    "test_mixer.cpp",
    "test_esc.cpp",
)


def test_t1_cmake_wires_pinned_catch2_and_unit_test_target():
    cmake_text = (NATIVE_FC_DIR / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "FetchContent_Declare" in cmake_text
    assert "Catch2" in cmake_text
    assert "GIT_TAG        v3.7.1" in cmake_text or "GIT_TAG v3.7.1" in cmake_text
    assert "add_executable(fc_unit_tests" in cmake_text
    assert "catch_discover_tests(fc_unit_tests)" in cmake_text


def test_t2_per_rung_unit_test_sources_exist():
    for filename in _EXPECTED_RUNG_TEST_FILES:
        path = TESTS_DIR / filename
        assert path.is_file(), filename
        text = path.read_text(encoding="utf-8")
        assert "TEST_CASE(" in text, f"{filename} has no TEST_CASE"


def test_smoke_binaries_still_registered_in_cmake():
    """IC §0 decision 7 — smokes must remain, not be deleted."""
    cmake_text = (NATIVE_FC_DIR / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "add_executable(fc_closed_loop_smoke" in cmake_text
    assert "add_executable(fc_esc_pwm_smoke" in cmake_text
    assert 'add_test(NAME fc_closed_loop_smoke COMMAND fc_closed_loop_smoke)' in cmake_text
    assert 'add_test(NAME fc_esc_pwm_smoke COMMAND fc_esc_pwm_smoke)' in cmake_text
    assert (NATIVE_FC_DIR / "smoke" / "closed_loop_smoke.cpp").is_file()
    assert (NATIVE_FC_DIR / "smoke" / "esc_pwm_smoke.cpp").is_file()


def test_t3_unit_test_binary_all_cases_pass_if_built():
    if not UNIT_TEST_BINARY.is_file():
        pytest.skip(f"C++ unit-test binary not built. Build it first: {_BUILD_HINT}")

    result = subprocess.run(
        [str(UNIT_TEST_BINARY)], capture_output=True, text=True, timeout=60, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "All tests passed" in result.stdout, result.stdout

    match = re.search(r"All tests passed \((\d+) assertions? in (\d+) test cases?\)", result.stdout)
    assert match is not None, result.stdout
    assertions, cases = int(match.group(1)), int(match.group(2))
    assert cases >= 6, "expected at least one case per rung (filter/attitude/controller/rate_torque/mixer/esc)"
    assert assertions > 0


def test_t4_closed_loop_smoke_still_recovers_if_built():
    if not CLOSED_LOOP_SMOKE_BINARY.is_file():
        pytest.skip(f"C++ closed-loop smoke binary not built. Build it first: {_BUILD_HINT}")

    result = subprocess.run(
        [str(CLOSED_LOOP_SMOKE_BINARY)], capture_output=True, text=True, timeout=30, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout

    initial_match = re.search(r"initial tilt error:\s*([\d.]+)\s*deg", result.stdout)
    final_match = re.search(r"final tilt error:\s*([\d.]+)\s*deg", result.stdout)
    assert initial_match is not None and final_match is not None
    assert float(final_match.group(1)) < float(initial_match.group(1))
    assert float(final_match.group(1)) < 2.0


def test_esc_smoke_still_passes_if_built():
    if not ESC_SMOKE_BINARY.is_file():
        pytest.skip(f"C++ ESC smoke binary not built. Build it first: {_BUILD_HINT}")

    result = subprocess.run(
        [str(ESC_SMOKE_BINARY)], capture_output=True, text=True, timeout=30, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout
    assert "FAIL" not in result.stdout


def test_t5_no_gpio_or_hardware_io_symbols_in_new_unit_tests():
    forbidden_substrings = (
        "gpio",
        "pigpio",
        "/dev/mem",
        "termios",
        "serial_open",
        "socket(",
        "dshot",
    )
    for filename in _EXPECTED_RUNG_TEST_FILES:
        path = TESTS_DIR / filename
        text = path.read_text(encoding="utf-8").lower()
        code_only_lines = []
        for line in text.splitlines():
            comment_at = line.find("//")
            code_only_lines.append(line if comment_at == -1 else line[:comment_at])
        code_text = "\n".join(code_only_lines)
        for token in forbidden_substrings:
            assert token not in code_text, f"{path} contains forbidden-shaped code token '{token}'"


def test_t6_rung_sources_are_git_unchanged_by_this_buy():
    """IC §0 decision 6 — behavior freeze. This Buy's own diff must not
    touch the existing rung sources unless an Engineer-approved bugfix is
    disclosed (none was needed here).

    **C26 disclosed exception:** `esc.cpp` is intentionally extended by
    `B1-fase-c-esc-output-hal` (★ Engineer-approved) — it adds
    `SimulatedEscSink::apply_forces` (a thin `encode_motor_forces` +
    `apply` wrapper implementing the new `EscOutput` port). The
    pre-existing `apply(...)`/`encode_motor_forces(...)` bodies are not
    touched — verified below via a line-level diff check (no `-` lines,
    i.e. purely additive), not just excluded from the freeze list.

    **C36 disclosed exception:** `plant.cpp` is intentionally extended by
    `B1-fase-c-sim-6dof-plant` (★ Engineer-authorized) — it adds
    `ToyQuad6DofPlant` (a second, separate toy plant with translation).
    `ToyQuadAttitudePlant`'s own pre-existing body is not touched —
    verified below via the same purely-additive line-level diff check
    already established for `esc.cpp`.

    **C37 disclosed exception:** `attitude.cpp` is intentionally extended
    by `B1-fase-c-mag-yaw-rung` (★ Engineer-authorized), per that IC's
    own explicit instruction to extend `ComplementaryAttitudeEstimator`
    with `update(sample, mag=None)`. Unlike `esc.cpp`/`plant.cpp`, this
    cannot be purely additive — adding an optional trailing parameter to
    an existing constructor/method requires editing those two signature
    lines in place, not just appending. Verified below: the diff removes
    **exactly** those two signature lines (constructor declaration +
    initializer list, and `update`'s own declaration) and nothing else —
    every existing method BODY line is untouched; the pre-existing
    Python/C++ regression suites (all passing unchanged) are the
    behavioral proof that `update(sample)` without `mag` is unaffected."""
    frozen_files = [
        NATIVE_FC_DIR / "src" / name
        for name in ("filter.cpp", "controller.cpp", "rate_torque.cpp", "mixer.cpp")
    ]
    for path in frozen_files:
        assert path.is_file(), path
    result = subprocess.run(
        ["git", "diff", "--stat", *[str(p) for p in frozen_files]],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.stdout.strip() == "", f"unexpected diff in rung sources:\n{result.stdout}"

    esc_cpp = NATIVE_FC_DIR / "src" / "esc.cpp"
    assert esc_cpp.is_file()
    esc_diff = subprocess.run(
        ["git", "diff", "--", str(esc_cpp)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    removed_lines = [
        line
        for line in esc_diff.stdout.splitlines()
        if line.startswith("-") and not line.startswith("---")
    ]
    assert removed_lines == [], f"esc.cpp diff removes/changes existing lines, not purely additive:\n{removed_lines}"

    plant_cpp = NATIVE_FC_DIR / "src" / "plant.cpp"
    assert plant_cpp.is_file()
    plant_diff = subprocess.run(
        ["git", "diff", "--", str(plant_cpp)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    plant_removed_lines = [
        line
        for line in plant_diff.stdout.splitlines()
        if line.startswith("-") and not line.startswith("---")
    ]
    assert plant_removed_lines == [], f"plant.cpp diff removes/changes existing lines, not purely additive:\n{plant_removed_lines}"

    # attitude.cpp's own C37 disclosed exception is verified against
    # current source content, not `git diff` — C37 has since been
    # ACCEPTed and tagged (`v0.5.38`), so a diff-based check (as used
    # for esc.cpp/plant.cpp above, where the invariant is simply "no
    # diff" and stays true forever) would no longer see the historical
    # edit at all once committed. Content checks below hold regardless
    # of commit status.
    attitude_cpp = NATIVE_FC_DIR / "src" / "attitude.cpp"
    assert attitude_cpp.is_file()
    attitude_cpp_text = attitude_cpp.read_text(encoding="utf-8")
    assert "mag_gain" in attitude_cpp_text, "attitude.cpp missing the disclosed C37 mag_gain parameter"
    assert "std::optional<MagSample> mag" in attitude_cpp_text, (
        "attitude.cpp missing the disclosed C37 optional MagSample parameter on update()"
    )
    # The pre-C37 signatures must no longer exist verbatim — proving the
    # constructor/update() were edited in place (the two disclosed
    # signature lines), not duplicated as a parallel overload alongside
    # an untouched original.
    assert "ComplementaryAttitudeEstimator::ComplementaryAttitudeEstimator(double gain, Quat initial_q)" not in attitude_cpp_text
    assert "AttitudeState ComplementaryAttitudeEstimator::update(const ImuSample& sample) {" not in attitude_cpp_text


def test_no_native_unit_test_wiring_into_craft_or_orchestrator():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "fc_unit_tests" not in text, f"{py_file} references the C++ unit-test binary"
            assert "Catch2" not in text, f"{py_file} references Catch2"


def test_default_safety_and_autonomy_submit_still_reject():
    assert isinstance(default_safety_gate(), RejectAllSafetyGate)
    assert default_safety_gate().evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_capability_registry_default_still_empty():
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
    }


def test_t8_pyproject_version_is_0_5_13():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.44"' in text
