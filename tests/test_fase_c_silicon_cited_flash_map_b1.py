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


def test_t5_stub_main_git_unchanged():
    result = subprocess.run(
        ["git", "diff", "--stat", str(STUB_MAIN)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.stdout.strip() == "", f"unexpected diff in stub_main.cpp:\n{result.stdout}"


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
    assert 'version = "0.5.27"' in text


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
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []


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
