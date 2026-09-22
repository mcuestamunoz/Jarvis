# Implementation Report — Fase C CRSF host baud 420000 (`B1-fase-c-crsf-host-baud`)

**IC:** [`implementation_contract_fase_c_crsf_host_baud_b1.md`](implementation_contract_fase_c_crsf_host_baud_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-22
**Status:** ★ ACCEPT CLOSED @ **`v0.5.21`**. Full suite green **without any physical receiver or USB serial adapter**. Package/tag **`v0.5.21`**.

---

## 0. Read this first — host OS configuration fact, not a link, honesty summary

This Buy extends C22's `src/jarvis/capabilities/crsf_serial.py` (no sixth capabilities module) with **opt-in** Darwin host baud configuration: `configure_host_baud(fd, baud=420000)` and `CrsfHostSerialIngress.configure_baud(baud=420000)`. On `sys.platform == "darwin"`, it applies raw 8N1 termios to the given FD, then issues the real `IOSSIOSPEED` ioctl requesting `baud` — `420000` by default, the rate a real ExpressLRS CRSF UART typically runs at. On any other platform, it **fails closed** with a typed `CrsfHostSerialError` — no Linux `TCSETS2`/`BOTHER`, no Windows serial stack was added.

**A successful ioctl is a host OS configuration fact, never proof a receiver exists.** Nothing in this module claims "ELRS connected," "RX present," or "baud 420000 works" in the sense of having talked to real hardware — there is no RF, no binding, no telemetry anywhere in this repo. `attach_fd(...)`/`attach_path(...)` **still never call baud config automatically** — C22's own "open = give me bytes" contract is unchanged; baud is a separate, explicit, caller-initiated step.

**Every PASS in this Buy's own test suite requires no physical hardware.** The Darwin success path (T2, T8) is proven entirely by mocking `fcntl.ioctl` — no dongle needed. The one **unmocked** ioctl call (T3) runs against a real POSIX `pty` and is **asserted to fail** (`CrsfHostSerialError`, wrapping `ENOTTY`/`[Errno 25] Inappropriate ioctl for device`) — a pty is not a UART, and that failure is the honest, expected outcome, not something the test suite skips around.

**Module boundary preserved exactly:** no new module was created — baud lives inside `crsf_serial.py`, per IC §0 decision 4's "baud is a property of the host serial FD, not a new capability rung." `git diff --stat` on `crsf_stream.py`, `crsf_dual_role.py`, `crsf_stub.py`, `radio.py`, and `intent.py` is **empty**.

---

## 1. Package layout vs IC §1

```text
src/jarvis/capabilities/
  crsf_serial.py         # C22 ingest UNCHANGED + NEW baud/raw-termios additions (this Buy)
  crsf_stream.py           # byte-unchanged (confirmed via git diff)
  crsf_dual_role.py          # byte-unchanged (confirmed via git diff)
  crsf_stub.py                 # byte-unchanged (confirmed via git diff)
  radio.py                      # byte-unchanged (confirmed via git diff)
  intent.py / safety.py          # byte-unchanged (confirmed via git diff)
  __init__.py                     # C22 paragraph updated: baud no longer "deferred"; still != live ELRS

tests/
  test_fase_c_crsf_host_baud_b1.py    # NEW — mocked ioctl (hardware-free) + one deliberate unmocked-pty fail-closed test
  test_fase_c_crsf_host_serial_b1.py    # UNCHANGED behavior — version re-pin only (T20 re-verifies this explicitly)
```

No `pyserial` was added to `pyproject.toml`'s dependencies (confirmed by T14).

---

## 2. Types / API implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| `CRSF_HOST_BAUD_ELRS = 420000` | §2.1 | ✅ documented default; any other positive `int` is accepted too — no ELRS rate table in this Buy |
| `configure_host_baud(fd: int, baud: int = 420000) -> None` | §2.1 | ✅ Darwin: raw 8N1 termios + `IOSSIOSPEED(baud)`; non-Darwin: raises `CrsfHostSerialError` ("Darwin-only in this Buy"); non-positive `baud`: typed error before any I/O; never opens/closes/attaches/polls; never claims a receiver is present |
| `CrsfHostSerialIngress.configure_baud(self, baud: int = 420000) -> None` | §2.1 | ✅ requires an attached FD — raises `CrsfHostSerialError` (not silent) if not attached; delegates to `configure_host_baud(self._fd, baud)` |
| `attach_fd` / `attach_path` / `poll` / `close` / `poll_and_ingest` (C22) | §2.2 | ✅ **unchanged** — `attach_path` still does not configure baud; `poll` still one non-blocking `os.read` + `feed` (T5, T20 re-verify this explicitly) |
| Non-goals (§2.3) | §2.3 | ✅ no `pyserial`, no `/dev` scan, no Linux `TCSETS2`, no Windows serial, no MCU HAL, no mixer/ESC, no Safety calls, no Intent from sticks, no background reader thread, no "connected" boolean, no auto-baud on `attach_path`, no claim that ioctl success implies RX presence — confirmed absent by grep and direct module inspection in tests |

`CrsfHostSerialError` (C22's own exception type) is reused for every baud/termios/ioctl/platform failure — no bare `OSError`/`termios.error` crosses the public boundary; each is caught and re-raised with `from exc` chaining, matching the IC's "do not raise bare `OSError`" instruction.

---

## 3. Darwin `IOSSIOSPEED` derivation (IC §0 decision 7) — computed, not copied

```python
_DARWIN_IOC_IN = 0x80000000
_DARWIN_IOCPARM_MASK = 0x1FFF
_DARWIN_IOSSIOSPEED_GROUP = ord("T")
_DARWIN_IOSSIOSPEED_NUM = 2

def _darwin_iossiospeed_request() -> int:
    speed_t_size = struct.calcsize("@L")  # Darwin speed_t is unsigned long
    return (
        _DARWIN_IOC_IN
        | ((speed_t_size & _DARWIN_IOCPARM_MASK) << 16)
        | (_DARWIN_IOSSIOSPEED_GROUP << 8)
        | _DARWIN_IOSSIOSPEED_NUM
    )
```

This implements Darwin's real `_IOW('T', 2, speed_t)` macro from `sys/ioccom.h`/`IOKit/serial/ioss.h` directly — `IOC_IN | ((len & IOCPARM_MASK) << 16) | (group << 8) | num` — **not** a copied constant from `pyserial` or any other library, per the IC's own explicit instruction. `struct.calcsize("@L")` gives the platform-native `unsigned long` size (8 bytes on 64-bit Darwin, matching `speed_t`), so the length field is derived from the actual platform, not hardcoded either.

**Verified empirically (before any formal test) to equal `0x80085402`** — the same value independently documented across multiple macOS serial-port references, confirming the derivation is correct without having consulted or copied any of them as source code.

The speed itself is packed with `struct.pack("@L", baud)` (native unsigned long, matching `speed_t`) and passed to `fcntl.ioctl(fd, request, buf)`.

---

## 4. Call order + raw 8N1 (IC §0 decisions 8, 9) — implemented exactly as locked

**Order shipped: (1) raw 8N1 termios via `tcgetattr`+`tcsetattr`, (2) `IOSSIOSPEED` ioctl.** This matches the IC's own "Apple-typical" locked order exactly.

**Raw 8N1 flags applied** (`_set_raw_8n1`, verified against a real pty in T8):
- `iflag`: clears `IGNBRK`, `BRKINT`, `PARMRK`, `ISTRIP`, `INLCR`, `IGNCR`, `ICRNL`, `IXON` — disables the CR/NL translations and flow control that would corrupt binary CRSF bytes containing `0x0D`/`0x0A`.
- `oflag`: clears `OPOST` — no output post-processing.
- `lflag`: clears `ECHO`, `ECHONL`, `ICANON`, `ISIG`, `IEXTEN` — non-canonical (raw) mode, no echo, no signal generation from input bytes (this is the exact fix for the canonical-mode gotcha C22 disclosed).
- `cflag`: clears `CSIZE`/`PARENB`/`CSTOPB`, sets `CS8 | CLOCAL | CREAD` — 8 data bits, no parity, 1 stop bit, ignore modem control lines, enable receiver.
- `cc[VMIN] = 0`, `cc[VTIME] = 0` — a read never blocks waiting for a fixed byte count; C22's own non-blocking `poll(...)` stays the actual read discipline.

**If the ioctl fails, `CrsfHostSerialError` is raised and success is never claimed.** The termios mutation from step (1) is **not** rolled back on a subsequent ioctl failure — disclosed here explicitly per the IC's own "acceptable to leave; report the order" instruction. In practice this only matters on a non-UART FD (like the pty used in T3) where the whole call was never going to represent a real configured device anyway; on a genuine serial device, step 1 succeeding and step 2 failing would leave the port in raw mode but at its previous baud, a state a caller can inspect via `termios.tcgetattr` if they need to.

---

## 5. Empirical verification (before formal tests)

```text
CRSF_HOST_BAUD_ELRS: 420000
derived request: 0x80085402

# T3-equivalent: unmocked, real pty -> fails closed
unmocked pty fail-closed OK: IOSSIOSPEED ioctl failed for fd=3 baud=420000: [Errno 25] Inappropriate ioctl for device

# non-positive baud
non-positive baud rejected OK: baud must be a positive int, got 0

# configure_baud before attach
configure_baud before attach OK: configure_baud requires an attached FD (call attach_fd/attach_path first)

# T2/T8-equivalent: mocked ioctl happy path
ioctl calls: [(3, 2148029442, b'\xa0h\x06\x00\x00\x00\x00\x00')]
fd matches: True
request matches derived: True   # 2148029442 == 0x80085402
packed speed: 420000
ICANON cleared: True
ECHO cleared: True
CS8 set: True
CLOCAL set: True
CREAD set: True
VMIN: 0 VTIME: 0
```

All outcomes matched hand-derived predictions before any formal test was written.

---

## 6. Tests (IC §4)

| ID | Check | Result |
|---|---|---|
| T1 | Constant/default `420000` is the documented ELRS-typical rate | ✅ `test_t1_default_baud_is_420000_elrs_typical_rate` |
| T2 | Darwin + mocked `fcntl.ioctl`: `configure_host_baud` returns; mock called; request = derived `IOSSIOSPEED`; packed speed = `420000` | ✅ `test_t2_darwin_mocked_ioctl_configures_420000` (uses a real pty fd as the argument — the mock is what makes it "succeed") |
| T3 | Darwin unmocked `configure_host_baud` on a pty raises `CrsfHostSerialError` | ✅ `test_t3_darwin_unmocked_ioctl_on_pty_fails_closed_not_skipped` — genuinely runs on this Darwin machine, no hardware, real `ENOTTY`-class failure |
| T4 | `ingress.configure_baud()` before attach → `CrsfHostSerialError` | ✅ `test_t4_configure_baud_before_attach_raises` |
| T5 | `attach_path`/`attach_fd` without `configure_baud` issues no ioctl | ✅ `test_t5_attach_without_configure_baud_issues_no_ioctl` (spy on `fcntl.ioctl`, asserts zero calls) |
| T6 | Non-positive `baud` → typed error; no ioctl | ✅ `test_t6_non_positive_baud_raises_no_ioctl` (0, -1, -420000; also `bool` explicitly rejected as non-`int`-shaped) |
| T7 | `sys.platform != "darwin"` → Darwin-only `CrsfHostSerialError`; skip packing assertions on that runner | ✅ `test_t7_non_darwin_raises_darwin_only_error` (skipped on this Darwin machine, by design) + `test_t7b_platform_check_happens_before_hardware_access` (patches `sys.platform` to `"linux"` to exercise the branch even when running on real Darwin) |
| T8 | Successful Darwin mock path also applies raw 8N1 | ✅ `test_t8_successful_mock_path_also_applies_raw_8n1` — asserts `ICANON`/`ECHO` cleared, `CS8`/`CLOCAL`/`CREAD` set, `VMIN=VTIME=0` on the real pty fd |
| T9 | C5 T5: `radio.py` has no `decode_crsf`/`decode_elrs`/`open_serial`/`write_pwm` (+ no `IOSSIOSPEED`/`configure_baud`) | ✅ `test_t9_radio_py_still_has_no_public_decode_or_serial_symbols` |
| T10 | `RadioIntentAdapter` still `not_implemented` | ✅ `test_t10_radio_intent_adapter_still_raises_not_implemented` |
| T11 | No `submit_command`/autonomy import in baud-related real code | ✅ `test_t11_baud_code_never_calls_submit_command_or_imports_autonomy` |
| T12 | `default_safety_gate()` still RejectAll | ✅ `test_t12_default_safety_gate_still_reject_all` |
| T13 | `crsf_stream.py` still has no I/O/`fcntl`/`termios`/device `open(` in real code | ✅ `test_t13_crsf_stream_still_has_no_io_or_termios_or_fcntl_in_real_code` |
| T14 | No `pyserial` in `pyproject.toml` | ✅ `test_t14_no_pyserial_dependency_in_pyproject` |
| T15 | No glob/scan of `/dev/cu`/`/dev/ttyUSB` in `crsf_serial.py` real code | ✅ `test_t15_no_device_glob_or_scan_in_crsf_serial_real_code` |
| T16 | `pyproject` `0.5.21`; re-pin `0.5.20` checkpoints | ✅ §7 below |
| T17 | Full suite green without a physical RX/USB-serial adapter | ✅ **3504 passed, 2 skipped** (was 3485 — exact +19 delta, 1 additional skip is T7's own by-design Darwin skip) |
| T18 | Report: host baud 420000 ≠ live ELRS ≠ RX connected ≠ UART driver ≠ Safety allow; ioctl mock is the hardware-free proof | ✅ §0 above |
| T19 | No CRSF/ELRS/UART driver tokens under `native/`; no bare `"uart"` substring check | ✅ `test_t19_no_crsf_or_elrs_under_native_no_bare_uart_substring_check` |
| T20 | C22 suite still green (pty ingest); no auto-baud on attach | ✅ `test_t20_c22_ingest_behavior_unchanged_no_auto_baud`; full `test_fase_c_crsf_host_serial_b1.py` re-run — 20/20 pass unmodified except version re-pin |

New Python test module `tests/test_fase_c_crsf_host_baud_b1.py` — **20 tests**, 19 passing + 1 by-design skip on this Darwin runner:

```text
test_t1_default_baud_is_420000_elrs_typical_rate PASSED
test_t2_darwin_mocked_ioctl_configures_420000 PASSED
test_t3_darwin_unmocked_ioctl_on_pty_fails_closed_not_skipped PASSED
test_t4_configure_baud_before_attach_raises PASSED
test_t5_attach_without_configure_baud_issues_no_ioctl PASSED
test_t6_non_positive_baud_raises_no_ioctl PASSED
test_t7_non_darwin_raises_darwin_only_error SKIPPED (this test asserts the non-Darwin fail-closed path)
test_t7b_platform_check_happens_before_hardware_access PASSED
test_t8_successful_mock_path_also_applies_raw_8n1 PASSED
test_t9_radio_py_still_has_no_public_decode_or_serial_symbols PASSED
test_t10_radio_intent_adapter_still_raises_not_implemented PASSED
test_t11_baud_code_never_calls_submit_command_or_imports_autonomy PASSED
test_t12_default_safety_gate_still_reject_all PASSED
test_t13_crsf_stream_still_has_no_io_or_termios_or_fcntl_in_real_code PASSED
test_t14_no_pyserial_dependency_in_pyproject PASSED
test_t15_no_device_glob_or_scan_in_crsf_serial_real_code PASSED
test_t16_pyproject_version_is_0_5_21 PASSED
test_t19_no_crsf_or_elrs_under_native_no_bare_uart_substring_check PASSED
test_t20_c22_ingest_behavior_unchanged_no_auto_baud PASSED
test_no_native_wiring_and_registry_still_empty PASSED
```

**Flakiness check:** ran the 20-test module **5 consecutive times** in isolation — identical `19 passed, 1 skipped` result every time.

**T17 (full suite):** `pytest -q` — **3504 passed, 2 skipped** (baseline before this Buy was 3485 passed, 1 skipped; delta is exactly the 19 new passing tests plus the 1 new by-design skip; no other file's pass/fail count moved). Run with no receiver or USB serial adapter of any kind attached.

Twenty-eight pre-existing test files hardcoded the prior checkpoint version string (`"0.5.20"`) as a version-pin assertion, including C22's own test module. Since this IC explicitly requires the `0.5.21` bump (§0 decision 18), all twenty-eight were re-pinned to `"0.5.21"`:

- `tests/test_bom_sku_resolved_cameras_b1.py`
- `tests/test_catalog_camera_power_w_b1.py`
- `tests/test_fase_c_attitude_controller_rung_b1.py`
- `tests/test_fase_c_attitude_estimation_rung_b1.py`
- `tests/test_fase_c_autonomy_surface_b1.py`
- `tests/test_fase_c_capability_registry_scaffold_b1.py`
- `tests/test_fase_c_controlled_flight_sim_tip_b1.py`
- `tests/test_fase_c_cpp_esc_pwm_stub_b1.py`
- `tests/test_fase_c_cpp_flight_control_scaffold_b1.py`
- `tests/test_fase_c_cpp_mcu_cross_compile_b1.py`
- `tests/test_fase_c_cpp_mcu_freestanding_elf_b1.py`
- `tests/test_fase_c_cpp_unit_tests_b1.py`
- `tests/test_fase_c_crsf_byte_stream_b1.py`
- `tests/test_fase_c_crsf_dual_role_bridge_b1.py`
- `tests/test_fase_c_crsf_host_serial_b1.py`
- `tests/test_fase_c_crsf_link_stub_b1.py`
- `tests/test_fase_c_esc_pwm_stub_rung_b1.py`
- `tests/test_fase_c_first_fc_rung_b1.py`
- `tests/test_fase_c_imu_filtering_rung_b1.py`
- `tests/test_fase_c_intent_safety_stub_b1.py`
- `tests/test_fase_c_mixer_rung_b1.py`
- `tests/test_fase_c_radio_dual_role_b1.py`
- `tests/test_fase_c_rate_torque_bridge_b1.py`
- `tests/test_fase_c_safety_real_policy_b1.py`
- `tests/test_geometry_prop_adapter_visor_x_b1.py`
- `tests/test_library_cameras_seed_b1.py`
- `tests/test_mission_power_w_b1.py`
- `tests/test_mission_vtx_identity_b1.py`

---

## 7. Honesty / forbidden confirmation (IC §5)

| Forbidden | Status | Evidence |
|---|---|---|
| Pytest that needs a real ELRS RX/USB serial | ✅ absent | Full suite passed with nothing attached (§6, T17) |
| `pyserial` dependency | ✅ absent | T14 |
| Claiming "baud 420000 works" as a live-RX claim | ✅ absent | §0/§4/§7 all state explicitly: ioctl success is a host OS fact, not proof of hardware |
| Treating pty success as the UART proof | ✅ absent | T3 asserts the pty case **fails**, on purpose |
| Auto-scan `/dev/cu.*` | ✅ absent | T15 |
| Auto-baud on `attach_path` | ✅ absent | T5, T20 |
| Background thread + "connected=true" | ✅ absent | No threading import; `.attached` still only means "FD present" (unchanged from C22) |
| Decode/serial/baud APIs on `radio.py` | ✅ absent | T9 + `git diff --stat radio.py` empty |
| I/O/termios inside `crsf_stream.py` | ✅ absent | T13 + `git diff --stat crsf_stream.py` empty |
| Linux `TCSETS2`/Windows serial | ✅ absent | Only Darwin path implemented; T7 confirms fail-closed elsewhere |
| MCU UART under `native/` | ✅ absent | T19 |
| Authority → Safety `allow` | ✅ absent | T12; C20's own already-tested guarantee reused unchanged (not touched this Buy) |
| Auto `submit_command` | ✅ absent | T11 |
| Marking radio `available` in registry | ✅ absent | `CapabilityRegistry.load_default()` re-confirmed empty |
| Flash / craft↔FS / deepen C20 policy | ✅ absent | Not touched |

**"One front" discipline (process lock after C6):** this Buy stayed exactly within Darwin host custom-baud configuration for an already-attached FD. No MCU UART, GPIO, flash, craft↔FS wiring, Safety policy edits, mixer/ESC, C20 policy deepening, `/dev` auto-discovery, or non-Darwin platform support were touched or opened.

---

## 8. Integration rules (IC §3) — confirmed unchanged

- C22 `CrsfHostSerialIngress` — **extended** (new `configure_baud` method); default ingest behavior (`attach_fd`/`attach_path`/`poll`/`close`/`poll_and_ingest`) unchanged, re-verified by T20 and by the full, unmodified-behavior C22 test suite passing.
- C21 `CrsfByteStreamAssembler` — unchanged; still no I/O/termios inside `crsf_stream.py` (T13).
- C20 policy/bridge — unchanged; not touched this Buy.
- C19 parse — unchanged.
- C5 `radio.py` — no `decode_*`/`open_serial`/`write_pwm`/baud/ioctl; byte-unchanged.
- C2 `RadioIntentAdapter` — still refuses.
- C4 autonomy — no baud/serial → `submit_command` path exists anywhere.
- C17 Safety — untouched; default stays `RejectAllSafetyGate`.
- Registry — default stays empty.

---

## 9. Files changed

**New:**
- `tests/test_fase_c_crsf_host_baud_b1.py`
- `.jes/artifacts/implementation_report_fase_c_crsf_host_baud_b1.md` (this file)

**Modified:**
- `src/jarvis/capabilities/crsf_serial.py` — extended (not rewritten): module docstring updated (baud no longer "deferred"); new `CRSF_HOST_BAUD_ELRS` constant, `_darwin_iossiospeed_request()`, `_set_raw_8n1()`, `configure_host_baud()` module-level function, `CrsfHostSerialIngress.configure_baud()` method; all C22 code (`CrsfHostSerialError`, `attach_fd`, `attach_path`, `poll`, `close`, `poll_and_ingest`, `_DEFAULT_MAX_BYTES`) byte-identical, just relocated around the new additions
- `pyproject.toml` — version `0.5.20` → `0.5.21` (no new dependency)
- `src/jarvis/capabilities/__init__.py` — C22 paragraph updated: baud described as no longer deferred, still opt-in, still ≠ live ELRS; new sentence on the Darwin/mock testing approach
- `docs/ARCHITECTURE.md`, `docs/PLATFORM_CAPABILITY_VISION.md`, `docs/IMPLEMENTATION_TASKS.md`, `README.md` — C23 sections (see §10)
- 28 test files — re-pinned stale `0.5.20` version-checkpoint assertions to `0.5.21`

**Not touched (confirmed):** `orchestrator.py`, Board (`ui/spatial-board/`), `library/`, `native/flight_control/**` (zero CRSF/ELRS references), `src/jarvis/capabilities/crsf_stream.py`, `src/jarvis/capabilities/crsf_dual_role.py`, `src/jarvis/capabilities/crsf_stub.py`, `src/jarvis/capabilities/radio.py`, `src/jarvis/capabilities/intent.py`, `src/jarvis/capabilities/safety.py`, `src/jarvis/flight_software/**`, `.jes/state/engineering_state.json`.

---

## 10. Docs honesty confirmation (IC §6)

- README header banner: "v0.5.20 tagged tip · working tree ahead toward v0.5.21 (C23 ... awaiting Cursor review + Engineer ACCEPT)" — no premature tag claim.
- `docs/IMPLEMENTATION_TASKS.md` PRIORIDAD banner and C23 row: "landed — awaiting Cursor review + ★ ACCEPT ... tag not on git yet".
- `docs/ARCHITECTURE.md` — new short note under capabilities: `crsf_serial.py` now opt-in baud, still ≠ live ELRS ≠ RX connected.
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C23 block with the required honesty line verbatim: "Host baud 420000 ≠ live ELRS ≠ RX connected ≠ UART driver ≠ Safety allow"; the C22 "baud deferred" next-front sentence updated to reflect this Buy closing that gap.
- Confirmed via `git tag -l | sort -V`: latest Fase C tag is `v0.5.20` (C22); no `v0.5.21` tag exists.
- Explicit **exists vs. impossible** statement, present in README/ARCHITECTURE/PLATFORM_CAPABILITY_VISION: **exists** = Darwin can be asked to set `420000` + raw 8N1 on an attached FD, proven without hardware via ioctl mock; **impossible** = a live ExpressLRS link, a receiver "connected," sticks driving craft, Authority opening Safety.

---

## 11. Residual — what comes next

Per this IC's own §8 handoff: still one front at a time, Engineer-prioritized — deepening C20's policy (out of scope this Buy), actual board bring-up/flash, craft↔FS wiring, or Linux custom-baud support (`TCSETS2`/`BOTHER`, explicitly out of scope this Buy — Darwin only). Not decided here.

---

## 12. Acceptance self-check against IC §7

- T1–T20: ✅ (see §6 table)
- Darwin ioctl mock proves 420000 `IOSSIOSPEED`: ✅ (§5, T2)
- Unmocked pty is fail-closed not skipped-suite: ✅ (§5, T3)
- No hardware RX required: ✅ (§0, §6, T17)
- No `pyserial`: ✅ (§7, T14)
- No live-ELRS/RX-connected claim: ✅ (§0, §10)
- C5/C19/C20/C21/C22 locks hold: ✅ (§0, §7, §8 — byte-diff confirmed on all five, C22 default behavior re-verified via T20 + its own unmodified test suite)
- Safety default unchanged: ✅ (§7, T12)
- Version `0.5.21`: ✅
- Docs honest: ✅ (§10)
- Not FAIL conditions: pytest does not need a dongle (§6, T17) · `pyserial` not added (§7, T14) · "baud 420000 works" not claimed as an RX claim (§0, §7) · no auto-baud on `attach_path` (§7, T5/T20) · serial/baud not stuffed into `radio.py` (§7, T9) · no termios/I/O added to `crsf_stream.py` (§7, T13) · no Safety allow via Authority (§7) · no "RX connected"/live ELRS claim anywhere in living docs (§10)
