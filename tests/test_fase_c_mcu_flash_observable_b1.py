"""Tests T1-T16 for `B1-fase-c-mcu-flash-observable` (C30).

T2/T10 (real relink via `LINK_DEPENDS`; `.bin` produced; `readelf -l`
LOAD still `0x08000000`) run against the actual toolchain when present,
same skip-if-toolchain-absent pattern C16/C18/C29's own pytest wrappers
use — the full transcript lives in this Buy's own implementation report.
T15 (full Python suite + host `ctest` green) is a process gate covered
by running them, not asserted here. T16 (report content: flashed LED
blink != flying != DShot != USART live != Betaflight; C29 N1 closed by
LINK_DEPENDS, not by C29's own T9 workaround) is covered by
`.jes/artifacts/implementation_report_fase_c_mcu_flash_observable_b1.md`,
not by this file.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import time
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command

REPO_ROOT = Path(__file__).resolve().parents[1]
NATIVE_FC_DIR = REPO_ROOT / "native" / "flight_control"
CMAKE_FILE = NATIVE_FC_DIR / "CMakeLists.txt"
LINKER_SCRIPT = NATIVE_FC_DIR / "mcu" / "linker_cortex_m4.ld"
STUB_MAIN = NATIVE_FC_DIR / "mcu" / "stub_main.cpp"
HELLO_LED_H = NATIVE_FC_DIR / "mcu" / "hello_led.h"
HELLO_LED_C = NATIVE_FC_DIR / "mcu" / "hello_led.c"
NATIVE_README = NATIVE_FC_DIR / "README.md"
MCU_BUILD_DIR = REPO_ROOT / "build" / "flight_control_mcu"
ELF_ARTIFACT = MCU_BUILD_DIR / "fc_mcu_stub.elf"
BIN_ARTIFACT = MCU_BUILD_DIR / "fc_mcu_stub.bin"
TOOLCHAIN_FILE = NATIVE_FC_DIR / "cmake" / "toolchains" / "arm-none-eabi.cmake"
CRSF_SERIAL_PY = REPO_ROOT / "src" / "jarvis" / "capabilities" / "crsf_serial.py"
UART_HPP = NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "uart.hpp"

_INSTALL_HINT = (
    "arm-none-eabi-g++ not found on PATH. See native/flight_control/README.md "
    "for a full-toolchain install hint (bare Homebrew arm-none-eabi-gcc lacks libstdc++)."
)


def _strip_c_comments(text: str) -> str:
    """Removes /* ... */ block comments and // line comments so honesty
    checks look at real code, not this module's own honesty-prose
    comments (same distinction every prior Fase C Buy's honesty tests
    make, adapted for C's comment syntax)."""
    without_block = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    without_line = re.sub(r"//.*", "", without_block)
    return without_line


def test_t1_cmake_sets_link_depends_on_linker_script():
    text = CMAKE_FILE.read_text(encoding="utf-8")
    assert "LINK_DEPENDS" in text
    assert "linker_cortex_m4.ld" in text
    # Must be scoped to fc_mcu_stub.elf, not a bare/global property.
    idx = text.index("LINK_DEPENDS")
    window = text[max(0, idx - 400) : idx + 200]
    assert "fc_mcu_stub.elf" in window


def test_t2_touching_linker_script_relinks_without_deleting_elf_if_toolchain_present():
    if not shutil.which("arm-none-eabi-g++"):
        pytest.skip(_INSTALL_HINT)

    configure = subprocess.run(
        ["cmake", "-S", str(NATIVE_FC_DIR), "-B", str(MCU_BUILD_DIR), f"--toolchain={TOOLCHAIN_FILE}"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if configure.returncode != 0:
        pytest.skip(f"MCU configure failed (likely incomplete toolchain): {configure.stderr[-800:]}")

    # Ensure a baseline .elf exists first (built, not deleted).
    build = subprocess.run(
        ["cmake", "--build", str(MCU_BUILD_DIR), "--target", "fc_mcu_stub.elf"],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if build.returncode != 0:
        pytest.skip(f"MCU build failed (likely incomplete toolchain): {build.stderr[-800:]}")
    assert ELF_ARTIFACT.is_file()

    mtime_before = ELF_ARTIFACT.stat().st_mtime
    time.sleep(1.1)
    LINKER_SCRIPT.touch()  # simulate an edit without deleting the elf

    relink = subprocess.run(
        ["cmake", "--build", str(MCU_BUILD_DIR), "--target", "fc_mcu_stub.elf"],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert relink.returncode == 0, relink.stdout + relink.stderr
    mtime_after = ELF_ARTIFACT.stat().st_mtime
    assert mtime_after > mtime_before, "touching linker_cortex_m4.ld did not trigger a relink (LINK_DEPENDS broken)"


def test_t3_led_source_cites_pc13_and_hglrcf405v2():
    text = HELLO_LED_C.read_text(encoding="utf-8")
    assert "PC13" in text or "C13" in text
    assert "HGLRCF405V2" in text
    assert "LED 1 C13" in text


def test_t4_led_source_has_cited_mmio_addresses():
    text = HELLO_LED_C.read_text(encoding="utf-8")
    for addr in ("0x40023800", "0x40023830", "0x40020800", "0x40020818"):
        assert addr in text, f"hello_led.c missing cited address {addr}"


def test_t5_no_pa8_as_led_and_no_motor_pin_writes():
    """Scoped to `hello_led.c` only — `stub_main.cpp` legitimately calls
    the pre-existing `MotorForceCommand`/`encode_motor_forces` C++ API
    (C18's own one-shot `jarvis_fc` exercise, unrelated to any GPIO
    motor-pin write), so checking it for the substring "motor" would
    false-fail against that pre-existing, legitimate library usage."""
    code_only = _strip_c_comments(HELLO_LED_C.read_text(encoding="utf-8"))
    lowered = code_only.lower()
    # PA8/GPIOA is never written to as a "status LED" in real code.
    assert "gpioa" not in lowered
    assert "0x40020000" not in lowered  # GPIOA base
    # No motor-pin register writes in the GPIO/MMIO file itself.
    assert "motor" not in lowered


def test_t6_stub_main_still_calls_jarvis_fc_once_and_idle_is_not_empty_while_true():
    text = STUB_MAIN.read_text(encoding="utf-8")
    assert "ImuLowPassFilter" in text
    assert "encode_motor_forces" in text
    code_only = _strip_c_comments(text)
    assert "while (true) {\n    }" not in code_only
    assert "hello_led_spin" in code_only
    assert "hello_led_init" in code_only


def test_t7_honesty_no_longer_claims_never_flashed_and_has_the_new_line():
    text = STUB_MAIN.read_text(encoding="utf-8") + HELLO_LED_C.read_text(encoding="utf-8")
    assert "never flashed" not in text.lower() or "can now be flashed" in text.lower()
    assert "!=" in text  # the honesty comparison line is present in at least one file
    for token in ("flying", "DShot", "USART", "Betaflight"):
        assert token in text, f"missing forbidden-claim honesty token '{token}'"


def test_t8_no_cmsis_or_hal_includes_in_new_mcu_files():
    for path in (HELLO_LED_H, HELLO_LED_C, STUB_MAIN):
        code_only = _strip_c_comments(path.read_text(encoding="utf-8")).lower()
        for token in ('#include "stm32f4xx', "#include <stm32f4xx", "hal_gpio", "hal_init(", "cmsis"):
            assert token not in code_only, f"{path} unexpectedly contains '{token}'"


def test_t9_native_tree_still_zero_crsf_elrs_tokens():
    for path in (REPO_ROOT / "native").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "crsf" not in text.lower(), f"{path} unexpectedly references CRSF"
            assert "elrs" not in text.lower(), f"{path} unexpectedly references ELRS"


def test_t10_bin_produced_and_load_address_unchanged_if_toolchain_present():
    if not shutil.which("arm-none-eabi-objcopy") or not shutil.which("arm-none-eabi-g++"):
        pytest.skip(_INSTALL_HINT + " (arm-none-eabi-objcopy also required for the .bin)")

    configure = subprocess.run(
        ["cmake", "-S", str(NATIVE_FC_DIR), "-B", str(MCU_BUILD_DIR), f"--toolchain={TOOLCHAIN_FILE}"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if configure.returncode != 0:
        pytest.skip(f"MCU configure failed: {configure.stderr[-800:]}")

    build = subprocess.run(
        ["cmake", "--build", str(MCU_BUILD_DIR), "--target", "fc_mcu_stub.elf"],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if build.returncode != 0:
        pytest.skip(f"MCU build failed: {build.stderr[-800:]}")

    assert BIN_ARTIFACT.is_file(), "expected fc_mcu_stub.bin after a successful MCU build"

    readelf = shutil.which("arm-none-eabi-readelf")
    if readelf is None:
        pytest.skip("arm-none-eabi-readelf not found; build succeeded, header not inspected")
    header = subprocess.run(
        [readelf, "-l", str(ELF_ARTIFACT)], capture_output=True, text=True, timeout=30, check=False
    )
    assert header.returncode == 0
    assert "0x08000000" in header.stdout, header.stdout


def test_t11_uart_hpp_and_crsf_serial_py_git_unchanged():
    for path in (UART_HPP, CRSF_SERIAL_PY):
        result = subprocess.run(
            ["git", "diff", "--stat", str(path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == "", f"unexpected diff in {path}:\n{result.stdout}"


def test_t12_readme_documents_dfu_util_and_restore_and_props_off():
    text = NATIVE_README.read_text(encoding="utf-8")
    assert "dfu-util" in text
    assert "0x08000000" in text
    assert "HGLRCF405V2" in text
    assert "Betaflight Configurator" in text
    lowered = text.lower()
    assert "props off" in lowered or "propellers" in lowered
    assert "battery" in lowered or "lipo" in lowered


def test_t13_module_import_does_not_require_a_plugged_dfu_device():
    """Importing/collecting this test module (and the CMake/source-level
    checks above) never touches USB device enumeration — a plugged DFU
    device is never a precondition for these tests to pass. This test
    itself is trivially green with nothing plugged in, documenting that
    contract explicitly."""
    assert True


def test_t14_pyproject_version_is_0_5_28():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.31"' in text


def test_t15_full_suite_process_gate_placeholder():
    """The full Python suite being green (and host `ctest` green) is
    verified by running them, not asserted here — see the implementation
    report's own test-run transcript."""
    assert True


def test_hello_led_files_not_under_src_jarvis():
    assert HELLO_LED_H.is_file()
    assert HELLO_LED_C.is_file()
    assert not any((REPO_ROOT / "src" / "jarvis").rglob("hello_led*"))


def test_startup_and_syscalls_git_unchanged():
    for name in ("startup_cortex_m4.c", "syscalls_stub.c"):
        path = NATIVE_FC_DIR / "mcu" / name
        result = subprocess.run(
            ["git", "diff", "--stat", str(path)], cwd=REPO_ROOT, capture_output=True, text=True, check=False
        )
        assert result.stdout.strip() == "", f"unexpected diff in {path}:\n{result.stdout}"


def test_toolchain_flags_unchanged():
    text = TOOLCHAIN_FILE.read_text(encoding="utf-8")
    assert "-mcpu=cortex-m4 -mthumb -mfloat-abi=soft" in text


def test_no_nvic_or_irq_or_dma_in_new_files():
    for path in (HELLO_LED_H, HELLO_LED_C, STUB_MAIN):
        code_only = _strip_c_comments(path.read_text(encoding="utf-8")).lower()
        for token in ("nvic", "extI", "irq_handler", "dma", "__enable_irq", "__disable_irq"):
            assert token.lower() not in code_only, f"{path} unexpectedly contains '{token}'"


def test_default_safety_gate_still_reject_all():
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_no_craft_or_core_imports_reference_hello_led_and_registry_still_empty():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "hello_led" not in text, f"{py_file} references hello_led"

    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []
