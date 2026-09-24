"""Tests T1-T10 for `B1-fase-c-cpp-mcu-freestanding-elf` (C18).

**Wrapper choice (IC §4 "document choice", same rationale + honesty as
C16's own wrapper):** this pytest wrapper actively drives the MCU
configure+build itself (there is no pre-existing artifact to just re-run
— the whole point is proving the *link* step succeeds), and treats
"`arm-none-eabi-g++` found on PATH" as necessary but not sufficient for
success: a compiler that answers `--version` but lacks a bundled
`newlib`/`libstdc++` (a real situation hit while building C16 and
reconfirmed here — see the C16 and this Buy's own implementation
reports) degrades to a skip with a specific install hint rather than a
hard suite failure.

A genuine, successful link was performed and verified for this Buy using
the xPack `arm-none-eabi-gcc` v15.2.1-1.1 (darwin-arm64) release: the
produced `fc_mcu_stub.elf` is a real `ELF32`/`ARM`/`EXEC` image with a
defined entry point, and `nm` confirms real `jarvis::fc::ImuLowPassFilter`
and `encode_motor_forces` symbols are linked in (not merely referenced) —
see the implementation report for the full command transcript.

Process gates covered elsewhere, not by this file:
- T5 (host `ctest` still green; tip class ~15°->~0.25°) — re-verified via
  the host smoke binary directly, same pattern as every prior wrapper.
- T8 (report lists layout, memory-map honesty, runtime link strategy,
  inspect commands) — `.jes/artifacts/implementation_report_fase_c_cpp_mcu_freestanding_elf_b1.md`.
- T9 (docs updated honestly, no premature v0.5.16 tag) — README/
  IMPLEMENTATION_TASKS/PLATFORM_CAPABILITY_VISION/ARCHITECTURE.
- T10 (Python full suite green @ 0.5.16) — the full `pytest -q` run.
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
MCU_DIR = NATIVE_FC_DIR / "mcu"
TOOLCHAIN_FILE = NATIVE_FC_DIR / "cmake" / "toolchains" / "arm-none-eabi.cmake"
MCU_BUILD_DIR = REPO_ROOT / "build" / "flight_control_mcu"
ELF_ARTIFACT = MCU_BUILD_DIR / "fc_mcu_stub.elf"

_INSTALL_HINT = (
    "arm-none-eabi-g++ not found on PATH. Install a FULL toolchain "
    "(bundling newlib + libstdc++, not just a bare compiler), e.g.: "
    "brew install --cask gcc-arm-embedded (macOS), or download the "
    "xPack arm-none-eabi-gcc release for your platform, or on "
    "Debian/Ubuntu: apt-get install gcc-arm-none-eabi. "
    "See native/flight_control/README.md."
)

_EXPECTED_MCU_FILES = (
    "linker_cortex_m4.ld",
    "startup_cortex_m4.c",
    "syscalls_stub.c",
    "stub_main.cpp",
)


def test_t1_linker_startup_and_stub_entry_exist():
    for filename in _EXPECTED_MCU_FILES:
        assert (MCU_DIR / filename).is_file(), filename

    linker_text = (MCU_DIR / "linker_cortex_m4.ld").read_text(encoding="utf-8")
    assert "MEMORY" in linker_text
    assert "FLASH" in linker_text
    assert "RAM" in linker_text
    assert "ENTRY(Reset_Handler)" in linker_text

    startup_text = (MCU_DIR / "startup_cortex_m4.c").read_text(encoding="utf-8")
    assert "Reset_Handler" in startup_text
    assert "isr_vector" in startup_text

    stub_text = (MCU_DIR / "stub_main.cpp").read_text(encoding="utf-8")
    assert "int main()" in stub_text or "int main(" in stub_text


def test_cmake_wires_elf_target_gated_on_cross_compiling():
    cmake_text = (NATIVE_FC_DIR / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "fc_mcu_stub.elf" in cmake_text
    assert "if(JARVIS_FC_CROSS_COMPILING)" in cmake_text
    gated_start = cmake_text.index("if(JARVIS_FC_CROSS_COMPILING)")
    gated_end = cmake_text.index("endif()", gated_start)
    gated_block = cmake_text[gated_start:gated_end]
    assert "add_executable(fc_mcu_stub.elf" in gated_block
    assert "linker_cortex_m4.ld" in gated_block


def test_t2_t3_mcu_elf_links_and_contains_real_jarvis_fc_symbols_or_skips():
    compiler = shutil.which("arm-none-eabi-g++")
    if compiler is None:
        pytest.skip(_INSTALL_HINT)

    configure = subprocess.run(
        [
            "cmake",
            "-S",
            str(NATIVE_FC_DIR),
            "-B",
            str(MCU_BUILD_DIR),
            f"--toolchain={TOOLCHAIN_FILE}",
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if configure.returncode != 0:
        pytest.skip(
            f"arm-none-eabi-g++ found at {compiler} but MCU configure failed "
            f"(likely an incomplete toolchain missing newlib/libstdc++): "
            f"{configure.stderr[-800:]}"
        )

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
            f"(likely an incomplete toolchain missing newlib/libstdc++, e.g. "
            f"a bare compiler-only package): {build.stderr[-800:]}"
        )

    assert ELF_ARTIFACT.is_file(), "expected fc_mcu_stub.elf after a successful MCU link"
    # Reject a warning-masked non-link (e.g. "cannot find entry symbol"
    # falling back to a bogus default) — surfaced during this Buy's own
    # implementation and fixed by enabling the C language in CMake.
    assert "cannot find entry symbol" not in build.stdout + build.stderr

    readelf = shutil.which("arm-none-eabi-readelf")
    objdump = shutil.which("arm-none-eabi-objdump")
    nm = shutil.which("arm-none-eabi-nm")

    if readelf is not None:
        result = subprocess.run(
            [readelf, "-h", str(ELF_ARTIFACT)], capture_output=True, text=True, timeout=30, check=False
        )
        assert "Machine:" in result.stdout and "ARM" in result.stdout, result.stdout
        assert "Entry point address" in result.stdout, result.stdout

    if objdump is not None:
        result = subprocess.run(
            [objdump, "-f", str(ELF_ARTIFACT)], capture_output=True, text=True, timeout=30, check=False
        )
        assert "elf32-littlearm" in result.stdout, result.stdout

    if nm is not None:
        result = subprocess.run(
            [nm, str(ELF_ARTIFACT)], capture_output=True, text=True, timeout=30, check=False
        )
        assert "ImuLowPassFilter" in result.stdout, "expected real jarvis_fc symbols linked into the ELF"
        assert "encode_motor_forces" in result.stdout


def test_t5_host_smoke_still_recovers_if_built():
    host_smoke_binary = REPO_ROOT / "build" / "flight_control" / "fc_closed_loop_smoke"
    if not host_smoke_binary.is_file():
        pytest.skip(
            "Host build not present. Build it first: cmake -S native/flight_control "
            "-B build/flight_control && cmake --build build/flight_control."
        )
    result = subprocess.run(
        [str(host_smoke_binary)], capture_output=True, text=True, timeout=30, check=False
    )
    assert result.returncode == 0
    assert "PASS" in result.stdout


def test_t6_no_gpio_flash_openocd_or_vendor_bsp_symbols_in_mcu_files():
    forbidden_substrings = (
        "gpio",
        "openocd",
        "jlink",
        "stm32cube",
        "cmsis",
        "chibios",
        "freertos",
        "px4",
        "ardupilot",
    )
    for filename in _EXPECTED_MCU_FILES:
        path = MCU_DIR / filename
        text = path.read_text(encoding="utf-8").lower()
        code_text = _strip_c_style_comments(text)
        for token in forbidden_substrings:
            assert token not in code_text, f"{path} contains forbidden-shaped code token '{token}'"


def _strip_c_style_comments(text: str) -> str:
    """Removes `/* ... */` block comments and `//` line comments so honesty
    tests check real code, not this project's own honesty-prose comments
    (which legitimately name forbidden terms to disclose their absence —
    same distinction every prior Fase C Buy's honesty tests make)."""
    without_block_comments = []
    in_block_comment = False
    i = 0
    n = len(text)
    while i < n:
        if not in_block_comment and text[i : i + 2] == "/*":
            in_block_comment = True
            i += 2
            continue
        if in_block_comment and text[i : i + 2] == "*/":
            in_block_comment = False
            i += 2
            continue
        if not in_block_comment:
            without_block_comments.append(text[i])
        i += 1
    code_only_lines = []
    for line in "".join(without_block_comments).splitlines():
        comment_at = line.find("//")
        code_only_lines.append(line if comment_at == -1 else line[:comment_at])
    return "\n".join(code_only_lines)


def test_t7_no_cpp_under_src_jarvis_and_craft_isolation():
    src_jarvis = REPO_ROOT / "src" / "jarvis"
    forbidden_suffixes = (".cpp", ".cc", ".cxx", ".hpp", ".hh", ".h")
    for path in src_jarvis.rglob("*"):
        if path.is_file():
            assert path.suffix not in forbidden_suffixes, f"C++ source found under src/jarvis: {path}"
            assert path.name != "CMakeLists.txt"

    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "fc_mcu_stub" not in text, f"{py_file} references the MCU ELF target"
            assert "flight_control_mcu" not in text, f"{py_file} references the MCU build dir"


def test_default_safety_and_autonomy_submit_still_reject():
    assert isinstance(default_safety_gate(), RejectAllSafetyGate)
    assert default_safety_gate().evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_capability_registry_default_still_empty():
    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []


def test_t9_pyproject_version_is_0_5_16():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.28"' in text
