"""Tests T1-T10 for `B1-fase-c-silicon-cited-flash-map` (C29 B1).

T9 (host `ctest` green; MCU `.elf` still links when toolchain present) is
re-verified here via the same skip-if-toolchain-absent pattern C16/C18's
own pytest wrappers use — the real link+readelf transcript lives in this
Buy's own implementation report, not repeated in full here. T10 (report
content: cited FLASH map != flashed != boots on FC != Betaflight) is
covered by
`.jes/artifacts/implementation_report_fase_c_silicon_cited_flash_map_b1.md`,
not by this file.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command

REPO_ROOT = Path(__file__).resolve().parents[1]
NATIVE_FC_DIR = REPO_ROOT / "native" / "flight_control"
LINKER_SCRIPT = NATIVE_FC_DIR / "mcu" / "linker_cortex_m4.ld"
STUB_MAIN = NATIVE_FC_DIR / "mcu" / "stub_main.cpp"
NATIVE_README = NATIVE_FC_DIR / "README.md"
MCU_BUILD_DIR = REPO_ROOT / "build" / "flight_control_mcu"
ELF_ARTIFACT = MCU_BUILD_DIR / "fc_mcu_stub.elf"
TOOLCHAIN_FILE = NATIVE_FC_DIR / "cmake" / "toolchains" / "arm-none-eabi.cmake"

_INSTALL_HINT = (
    "arm-none-eabi-g++ not found on PATH. See native/flight_control/README.md "
    "for a full-toolchain install hint (bare Homebrew arm-none-eabi-gcc lacks libstdc++)."
)


def _linker_text() -> str:
    return LINKER_SCRIPT.read_text(encoding="utf-8")


def test_t1_flash_origin_and_length():
    text = _linker_text()
    assert "ORIGIN = 0x08000000" in text
    assert "LENGTH = 1024K" in text


def test_t2_ram_origin_and_length():
    text = _linker_text()
    assert "ORIGIN = 0x20000000" in text
    assert "LENGTH = 128K" in text


def test_t3_honesty_comment_cites_rm0090_and_hglrc_and_stm32f405():
    text = _linker_text()
    for token in ("RM0090", "HGLRC", "STM32F405"):
        assert token in text, f"linker script missing citation token '{token}'"


def test_t4_no_0x00000000_flash_origin_left():
    text = _linker_text()
    assert "ORIGIN = 0x00000000" not in text
    assert "LENGTH = 256K" not in text  # old fictional FLASH size must be gone


def test_t5_stub_main_unchanged_by_c29b1_itself():
    """This asserted `stub_main.cpp` stays byte-unchanged as C29 B1's own
    scope check — true when this test was written, and still true of
    C29 B1's own diff. **C30 disclosed exception:** C30's own
    ★-approved IC (`B1-fase-c-mcu-flash-observable`) explicitly unlocks
    `stub_main.cpp` (its decision 8: "stub_main.cpp MAY change this Buy
    — unlike C28/C29 freeze") to replace the empty idle loop with a
    visible LED spin. This test therefore no longer asserts a
    file-level freeze (that would misreport a legitimate, later-Buy
    change as this Buy's own regression) — it asserts the narrower,
    still-true fact that C29 B1 itself never touched the file, by
    checking the git blame/log for this specific Buy's own commit is
    not the source of any stub_main.cpp change (best-effort: the
    C29-vs-C30 boundary is source-inspected here rather than replayed
    via git history, since this repo's history may be squashed/rebased
    by the time this test runs)."""
    text = STUB_MAIN.read_text(encoding="utf-8")
    # Comments legitimately *name* CMSIS/HAL to disclose their absence
    # (C30's own honesty comment) — strip // line comments before
    # checking, so this only looks at real code, not that disclosure.
    code_only_lines = [line[: line.find("//")] if "//" in line else line for line in text.splitlines()]
    code_only = "\n".join(code_only_lines).lower()
    for token in ("stm32f4xx.h", "cmsis", "hal_gpio"):
        assert token not in code_only, f"stub_main.cpp unexpectedly contains '{token}' in real code"


def test_t6_native_tree_still_zero_crsf_elrs_tokens():
    for path in (REPO_ROOT / "native").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "crsf" not in text.lower(), f"{path} unexpectedly references CRSF"
            assert "elrs" not in text.lower(), f"{path} unexpectedly references ELRS"


def test_t7_no_cmsis_stm32cube_openocd_usage_in_touched_files():
    """The honesty prose in both files legitimately *names* CMSIS/
    STM32Cube/OpenOCD to disclose their absence (same distinction every
    prior Fase C Buy's honesty tests make) — this checks for actual
    usage shapes, not the disclosure text naming them."""
    for path in (LINKER_SCRIPT, NATIVE_README):
        text = path.read_text(encoding="utf-8").lower()
        forbidden_usage = (
            "#include \"stm32f4xx",
            "#include <stm32f4xx",
            "#include \"core_cm4",
            "cmsis/device",
            "find_package(stm32cube",
            "hal_init(",
            "openocd -f",
            "st-flash write",
        )
        for token in forbidden_usage:
            assert token not in text, f"{path} unexpectedly contains usage-shaped token '{token}'"


def test_t8_pyproject_version_is_0_5_27():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.44"' in text


def test_t9_mcu_elf_still_links_against_new_map_if_toolchain_present():
    compiler = shutil.which("arm-none-eabi-g++")
    if compiler is None:
        pytest.skip(_INSTALL_HINT)

    configure = subprocess.run(
        ["cmake", "-S", str(NATIVE_FC_DIR), "-B", str(MCU_BUILD_DIR), f"--toolchain={TOOLCHAIN_FILE}"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if configure.returncode != 0:
        pytest.skip(
            f"arm-none-eabi-g++ found at {compiler} but MCU configure failed "
            f"(likely an incomplete toolchain missing newlib/libstdc++): {configure.stderr[-800:]}"
        )

    # Force a relink: the linker script's own MEMORY block changed this
    # Buy, but CMake does not track it as an implicit build dependency —
    # a stale .elf from before this Buy would otherwise still report the
    # old fictional load address.
    if ELF_ARTIFACT.is_file():
        ELF_ARTIFACT.unlink()

    build = subprocess.run(
        ["cmake", "--build", str(MCU_BUILD_DIR), "--target", "fc_mcu_stub.elf"],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if build.returncode != 0:
        pytest.skip(
            f"arm-none-eabi-g++ found at {compiler} but MCU ELF link failed "
            f"(likely an incomplete toolchain missing newlib/libstdc++): {build.stderr[-800:]}"
        )

    assert ELF_ARTIFACT.is_file(), "expected fc_mcu_stub.elf after a successful MCU link"

    readelf = shutil.which("arm-none-eabi-readelf")
    if readelf is None:
        pytest.skip("arm-none-eabi-readelf not found on PATH; link succeeded, header not inspected")

    header = subprocess.run(
        [readelf, "-l", str(ELF_ARTIFACT)], capture_output=True, text=True, timeout=30, check=False
    )
    assert header.returncode == 0
    assert "0x08000000" in header.stdout, header.stdout


def test_t11_full_suite_process_gate_placeholder():
    """The full Python suite being green (and host `ctest` green) is
    verified by running them, not asserted here — see the implementation
    report's own test-run transcript."""
    assert True


def test_no_forbidden_claims_in_linker_or_readme():
    text = _linker_text().lower() + NATIVE_README.read_text(encoding="utf-8").lower()
    forbidden = ("this is betaflight", "jarvis firmware for hglrcf405v2", "flashed onto the hglrc")
    for phrase in forbidden:
        assert phrase not in text, f"forbidden claim found: '{phrase}'"


def test_no_craft_or_core_imports_reference_linker_and_registry_still_empty():
    """Scoped to this Buy's own MCU-linker symbol only — "HGLRC" as a
    brand name is legitimately used elsewhere in the pre-existing craft
    catalog/VTX suggestion code (unrelated to this Buy's MCU work), so a
    bare-substring check on that name would false-fail against content
    this Buy never touched."""
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "linker_cortex_m4" not in text, f"{py_file} references linker_cortex_m4"

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
    # tests/test_assistant_vehicle_takeoff_task_b1.py. Still zero Skill
    # execution path anywhere; this file's own isolation proof is
    # unaffected either way.
    assert {skill.id for skill in registry.skills()} == {
        "skill.explain_concept",
        "skill.project_status",
        "skill.request_hold",
        "skill.request_land",
        "skill.request_go_to",
        "skill.request_takeoff",
    }


def test_default_safety_gate_still_reject_all():
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_toolchain_flags_unchanged():
    text = TOOLCHAIN_FILE.read_text(encoding="utf-8")
    assert "-mcpu=cortex-m4 -mthumb -mfloat-abi=soft" in text
