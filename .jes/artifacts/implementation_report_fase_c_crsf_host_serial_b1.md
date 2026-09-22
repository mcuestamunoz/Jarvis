# Implementation Report — Fase C CRSF host serial ingest (`B1-fase-c-crsf-host-serial`)

**IC:** [`implementation_contract_fase_c_crsf_host_serial_b1.md`](implementation_contract_fase_c_crsf_host_serial_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-22
**Status:** ★ ACCEPT CLOSED @ **`v0.5.20`**. See [review](implementation_review_fase_c_crsf_host_serial_b1.md).

---

## 0. Read this first — pull-based FD reader, not a link, honesty summary

This Buy adds `src/jarvis/capabilities/crsf_serial.py`: `CrsfHostSerialIngress`, a pull-based reader that reads bytes from an already-open host file descriptor (`attach_fd`) or an opt-in device path (`attach_path`), and feeds them to C21's `CrsfByteStreamAssembler` **unchanged**. `poll(...)` performs exactly one non-blocking read attempt and returns whatever new `CrsfFrame`s the assembler now has — there is no background thread, no "link up"/"connected" flag, and no auto-reconnect loop anywhere in this module.

**Host serial ingest ≠ live ELRS ≠ "RX connected" ≠ UART driver ≠ Safety allow.** Every PASS in this Buy's own test suite uses a POSIX `pty` as its loopback — **no physical receiver or USB serial adapter is required**, confirmed by running the full suite on this machine with nothing plugged in. `pyserial` was **not** added as a dependency (confirmed: absent from `pyproject.toml`). **420000 baud (the rate a real ELRS CRSF link typically runs at) is not configured anywhere** — `attach_path(...)` opens a node read-only/non-blocking and nothing else; no termios call, no `IOSSIOSPEED` ioctl, no baud-rate concept exists in this module at all. That configuration is explicitly deferred to a later, platform-specific IC (IC §0 decision 8), not attempted here.

**Module boundary preserved exactly:** `crsf_serial.py` is a **new, separate** module — not folded into `crsf_stream.py`, `crsf_dual_role.py`, `crsf_stub.py`, or `radio.py`. `git diff --stat` on all five of those modules (plus `intent.py`) is **empty**. `crsf_stream.py` stays exactly as I/O-free as C21 shipped it (T11 re-verifies this).

---

## 1. Package layout vs IC §1

```text
src/jarvis/capabilities/
  crsf_serial.py         # NEW — CrsfHostSerialIngress, CrsfHostSerialError, poll_and_ingest
  crsf_stream.py           # byte-unchanged (confirmed via git diff) — reused, not rewritten
  crsf_dual_role.py          # byte-unchanged (confirmed via git diff) — reused, not rewritten
  crsf_stub.py                 # byte-unchanged (confirmed via git diff) — reused, not rewritten
  radio.py                      # byte-unchanged (confirmed via git diff)
  intent.py / safety.py          # byte-unchanged (confirmed via git diff)
  __init__.py                     # docstring extended with a C22 pointer paragraph; no new top-level exports

tests/
  fixtures/crsf/                    # REUSED from C19 — no new binary fixture needed
  test_fase_c_crsf_host_serial_b1.py  # NEW — every test uses a real POSIX pty
```

`pyproject.toml`'s dependency list is otherwise untouched — no `pyserial` (or any new runtime dependency) was added, confirmed by T12.

---

## 2. Types / API implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| `CrsfHostSerialError` | §2.1 | ✅ a dedicated exception type for attach/read failures — never `CrsfParseError` (that stays inside `crsf_stub`/`crsf_stream`, and this module never raises it) |
| `CrsfHostSerialIngress` | §2.1 | ✅ holds an injected-or-default-constructed `CrsfByteStreamAssembler` via `.assembler` |
| `.attach_fd(fd: int) -> None` | §2.1 | ✅ attaches to a caller-owned FD; forces it non-blocking via `os.set_blocking(fd, False)` so `poll(...)` never blocks regardless of how the caller obtained the FD; `close()` never closes it |
| `.attach_path(path: str) -> None` | §2.1 | ✅ `os.open(path, O_RDONLY \| O_NOCTTY \| O_NONBLOCK)`; does **not** configure baud; ingress **owns** the resulting FD, `close()` releases it; raises `CrsfHostSerialError` (not a bare `OSError`) if the open fails |
| `.poll(*, max_bytes=64) -> list[CrsfFrame]` | §2.1 | ✅ one non-blocking `os.read`; `[]` on not-attached, `BlockingIOError`/EAGAIN, or zero-byte read; never raises `CrsfParseError` (inherited from C21's own guarantee, unchanged) |
| `.close() -> None` | §2.1 | ✅ closes the FD only if `attach_path(...)` opened it; always detaches |
| `poll_and_ingest(ingress, *, policy, ingress_radio=None, max_bytes=64) -> list[RadioDualRoleResult]` | §2.2 | ✅ calls `ingress.poll(...)` **exactly once** (confirmed by direct source inspection — no double-feed risk since C21's `ingest_stream_bytes` is not reused here, avoiding a second `feed(...)` call on the same bytes), then for each new `0x16` frame decodes and calls C20's `ingest_rc_channels(...)` unchanged; below-threshold `None` results are omitted |
| Non-goals (§2.3) | §2.3 | ✅ no `pyserial`, no baud API, no USB VID/PID scan, no MCU HAL, no mixer/ESC, no Safety calls, no Intent from sticks, no background reader thread, no "connected" boolean — confirmed absent by grep and direct module inspection in tests |

**"Poll before attach" choice (IC §2.1's "pick one, report"):** documented as **`[]`, not an error** — `poll()` on a fresh, unattached `CrsfHostSerialIngress` returns an empty list, matching "no data available" rather than treating an unattached ingress as an exceptional state. Verified by `test_poll_before_attach_gives_empty_list_not_error`.

---

## 3. A real pty gotcha, found and disclosed (not a bug in the shipped module)

While writing empirical verification for T4 (`attach_path` on the pty **slave** path, writing from the **master** side), the first attempt returned zero frames indefinitely. Root cause: POSIX pseudo-terminals default to **canonical (cooked) line-buffered mode** — bytes written to the master side are held by the kernel's tty line discipline until a line terminator (e.g. a newline byte) is seen, before becoming readable on the slave side. The CRSF fixture's binary payload has no such terminator, so the data sat buffered forever from the reader's point of view.

This is a property of **ptys specifically** (they emulate a real terminal, including line discipline), not of `crsf_serial.py`'s own logic, and not something a real serial device special file (e.g. `/dev/cu.usbserial-*`) exhibits in the same way. The fix is confined entirely to the **test fixture setup**: `tty.setraw(master)` (disabling `ICANON`/echo on the pty pair) before writing, so the loopback behaves like a raw byte pipe — exactly what this module expects to read from. `crsf_serial.py` itself was not changed to work around this; it is a pure `os.open`/`os.read` reader with no knowledge of terminal modes at all, matching IC §0 decision 8's "opening a path is 'give me bytes from this node,' not 'I configured an ELRS RX'" framing.

---

## 4. Empirical verification (before formal tests, all against a real pty)

```text
=== T1: pty, write in one shot, attach_fd master, poll ===
frames: ['0x16']
=== T2: pty, write in small chunks ===
frames: ['0x16']
=== T3: poll with no new bytes ===
poll empty: []
=== T4: attach_path on slave pty path (after tty.setraw fix) ===
frames via attach_path (raw mode): ['0x16']
=== T5: close() releases owned fd ===
attached after close: False
poll after close: []
=== poll before attach ===
poll before attach: []
=== attach_fd does not own/close ===
fd still usable after close() on attach_fd ingress: b'x'
=== poll_and_ingest end-to-end over a pty, aux channel high ===
results: [RadioDualRoleResult(..., authority=AuthoritySignal(..., kind='kill',
          payload='crsf_aux_channel=4 value=1800'))]
```

All outcomes matched hand-derived predictions before any formal test was written; the formal test suite was then run **5 consecutive times** to rule out pty-timing flakiness (§5) — all 5 runs passed identically.

---

## 5. Tests (IC §4)

| ID | Check | Result |
|---|---|---|
| T1 | PTY: write valid fixture to slave in one shot; `attach_fd` master; `poll` until 1 frame type `0x16` | ✅ `test_t1_pty_one_shot_write_gives_one_frame` |
| T2 | PTY: write same fixture in small chunks across several writes; polls reassemble to 1 frame | ✅ `test_t2_pty_chunked_writes_reassemble_to_one_frame` |
| T3 | `poll` with no new bytes → `[]`, no raise | ✅ `test_t3_poll_with_no_new_bytes_gives_empty_list_no_raise` |
| T4 | Optional `attach_path`: open pty slave path, write from other side, get ≥1 valid frame | ✅ `test_t4_attach_path_on_pty_slave_path_gives_valid_frame` |
| T5 | `close()` after `attach_path` releases the owned FD | ✅ `test_t5_close_after_attach_path_releases_owned_fd` (+ `test_attach_fd_does_not_own_or_close_the_fd` for the FD-ownership counterpart) |
| T6 | Optional helper: PTY bytes with aux ch 4 ≥ 1500 → Authority `kill`; all-992 fixture → empty result list | ✅ `test_t6_aux_channel_high_via_pty_gives_authority_kill` (+ `test_t6b_all_neutral_fixture_via_pty_gives_empty_results`) |
| T7 | C5 T5: `radio.py` has no `decode_crsf`/`decode_elrs`/`open_serial`/`write_pwm` | ✅ `test_t7_radio_py_still_has_no_public_decode_or_serial_symbols` |
| T8 | `RadioIntentAdapter` still `not_implemented` | ✅ `test_t8_radio_intent_adapter_still_raises_not_implemented` |
| T9 | No `submit_command`/autonomy import for execution in the new module | ✅ `test_t9_module_never_calls_submit_command_or_imports_autonomy` |
| T10 | `default_safety_gate()` still RejectAll | ✅ `test_t10_default_safety_gate_still_reject_all` |
| T11 | `crsf_stream.py` still has no I/O imports/device `open(` in real code | ✅ `test_t11_crsf_stream_still_has_no_io_imports_or_device_open` |
| T12 | No `pyserial` in `pyproject.toml` dependencies | ✅ `test_t12_no_pyserial_dependency_in_pyproject` |
| T13 | No glob/scan of `/dev/cu`/`/dev/ttyUSB` in the module real code | ✅ `test_t13_no_device_glob_or_scan_in_module_real_code` |
| T14 | `pyproject` `0.5.20`; re-pin `0.5.19` checkpoints | ✅ §6 below |
| T15 | Full suite green **without** a physical RX | ✅ **3485 passed, 1 skipped** (was 3465 — exact +20 delta), run on a machine with no receiver attached |
| T16 | Report: host serial ingest ≠ live ELRS ≠ RX connected ≠ Safety allow; baud 420000 deferred | ✅ §0 above |
| T17 | No CRSF/ELRS/UART **driver** tokens under `native/`; no bare `"uart"` substring check | ✅ `test_t17_no_crsf_or_elrs_under_native_no_bare_uart_substring_check` (scoped exactly like C21's own equivalent test, for the same disclosed reason) |

New Python test module `tests/test_fase_c_crsf_host_serial_b1.py` — **20 tests**, all passing, every one gated behind `pytestmark = pytest.mark.skipif(not _HAS_PTY, ...)` (skips with a clear reason on a non-POSIX platform rather than requiring hardware — IC §0 decision 11):

```text
test_t1_pty_one_shot_write_gives_one_frame PASSED
test_t2_pty_chunked_writes_reassemble_to_one_frame PASSED
test_t3_poll_with_no_new_bytes_gives_empty_list_no_raise PASSED
test_t4_attach_path_on_pty_slave_path_gives_valid_frame PASSED
test_t5_close_after_attach_path_releases_owned_fd PASSED
test_attach_fd_does_not_own_or_close_the_fd PASSED
test_t6_aux_channel_high_via_pty_gives_authority_kill PASSED
test_t6b_all_neutral_fixture_via_pty_gives_empty_results PASSED
test_t7_radio_py_still_has_no_public_decode_or_serial_symbols PASSED
test_t8_radio_intent_adapter_still_raises_not_implemented PASSED
test_t9_module_never_calls_submit_command_or_imports_autonomy PASSED
test_t10_default_safety_gate_still_reject_all PASSED
test_t11_crsf_stream_still_has_no_io_imports_or_device_open PASSED
test_t12_no_pyserial_dependency_in_pyproject PASSED
test_t13_no_device_glob_or_scan_in_module_real_code PASSED
test_t14_pyproject_version_is_0_5_20 PASSED
test_t17_no_crsf_or_elrs_under_native_no_bare_uart_substring_check PASSED
test_poll_before_attach_gives_empty_list_not_error PASSED
test_attach_path_to_nonexistent_path_raises_typed_error PASSED
test_no_native_wiring_and_registry_still_empty PASSED
```

**No honesty-test false positives this time** — the comment/docstring-stripping helper (`_strip_python_comments_and_docstrings`) and the `crsf`/`elrs`-only (not bare `"uart"`) native-tree scope were both applied from the outset, carrying forward the lessons from C19 and C21.

**Flakiness check (a pty-based test suite's own honest self-scrutiny):** ran the full 20-test module **5 consecutive times** in isolation — identical `20 passed` result every time, no timing-dependent failures observed. `_poll_until(...)`'s small bounded retry loop (≤20 attempts, 10ms apart) accounts for the fact that a pty write is not guaranteed to be instantaneously readable, without ever blocking indefinitely on a stuck test.

**T15 (full suite):** `pytest -q` — **3485 passed, 1 skipped** (baseline before this Buy was 3465 passed, 1 skipped; delta is exactly the 20 new tests, no other file's pass/fail count moved; the one skip is unrelated/pre-existing). Run with no receiver or USB serial adapter of any kind attached to the machine.

Twenty-seven pre-existing test files hardcoded the prior checkpoint version string (`"0.5.19"`) as a version-pin assertion, including C19's, C20's, and C21's own test modules. Since this IC explicitly requires the `0.5.20` bump (§0 decision 15), all twenty-seven were re-pinned to `"0.5.20"`:

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

## 6. Honesty / forbidden confirmation (IC §5)

| Forbidden | Status | Evidence |
|---|---|---|
| Pytest that needs a real ELRS RX/USB serial | ✅ absent | Full suite passed on a machine with no receiver attached (§5, T15) |
| `pyserial` dependency | ✅ absent | T12 |
| Setting 420000 baud / claiming ELRS UART timing | ✅ absent | No termios/ioctl call anywhere in `crsf_serial.py`; §0 explicitly states this is deferred |
| Auto-scan `/dev/cu.*` | ✅ absent | T13 |
| Background thread + "connected=true" | ✅ absent | `poll(...)` is a synchronous, single-shot, caller-driven read; no threading import, no "connected" attribute anywhere |
| Decode/serial APIs on `radio.py` | ✅ absent | T7 + `git diff --stat radio.py` empty |
| I/O inside `crsf_stream.py` | ✅ absent | T11 + `git diff --stat crsf_stream.py` empty |
| MCU UART under `native/` | ✅ absent | T17 |
| Authority → Safety `allow` | ✅ absent | T10; C20's own already-tested Authority-trace-only guarantee is reused unchanged via `ingest_rc_channels` |
| Auto `submit_command` | ✅ absent | T9 |
| Marking radio `available` in registry | ✅ absent | `CapabilityRegistry.load_default()` re-confirmed empty |
| Flash / craft↔FS / deepen C20 policy | ✅ absent | Not touched; `crsf_dual_role.py` byte-unchanged |

**"One front" discipline (process lock after C6):** this Buy stayed exactly within the host serial-shaped ingest scope. No MCU UART, GPIO, flash, craft↔FS wiring, Safety policy edits, mixer/ESC, C20 policy deepening, or custom-baud configuration were touched or opened.

---

## 7. Integration rules (IC §3) — confirmed unchanged

- C21 `CrsfByteStreamAssembler` — **called**, not rewritten; still no I/O inside `crsf_stream.py` (T11); `crsf_stream.py` byte-unchanged.
- C20 policy/bridge — unchanged; `poll_and_ingest` is a caller of `ingest_rc_channels`, not a reimplementation; `crsf_dual_role.py` byte-unchanged.
- C19 parse — unchanged, reached only via C21's own `feed(...)`.
- C5 `radio.py` — no `decode_*`/`open_serial`/`write_pwm`/stream types; byte-unchanged.
- C2 `RadioIntentAdapter` — still refuses.
- C4 autonomy — no serial → `submit_command` path exists anywhere.
- C17 Safety — untouched; default stays `RejectAllSafetyGate`.
- Registry — default stays empty.

---

## 8. Files changed

**New:**
- `src/jarvis/capabilities/crsf_serial.py`
- `tests/test_fase_c_crsf_host_serial_b1.py`
- `.jes/artifacts/implementation_report_fase_c_crsf_host_serial_b1.md` (this file)

**Modified:**
- `pyproject.toml` — version `0.5.19` → `0.5.20` (no new dependency)
- `src/jarvis/capabilities/__init__.py` — docstring extended with a C22 pointer paragraph; `__all__`/imports unchanged (deliberately not exported at package top level, same choice as C19/C20/C21)
- `docs/ARCHITECTURE.md`, `docs/PLATFORM_CAPABILITY_VISION.md`, `docs/IMPLEMENTATION_TASKS.md`, `README.md` — C22 sections (see §9)
- 27 test files — re-pinned stale `0.5.19` version-checkpoint assertions to `0.5.20`

**Not touched (confirmed):** `orchestrator.py`, Board (`ui/spatial-board/`), `library/`, `native/flight_control/**` (zero CRSF/ELRS references), `src/jarvis/capabilities/crsf_stream.py`, `src/jarvis/capabilities/crsf_dual_role.py`, `src/jarvis/capabilities/crsf_stub.py`, `src/jarvis/capabilities/radio.py`, `src/jarvis/capabilities/intent.py`, `src/jarvis/capabilities/safety.py`, `src/jarvis/flight_software/**`, `.jes/state/engineering_state.json`.

---

## 9. Docs honesty confirmation (IC §6)

- README header banner: "v0.5.19 tagged tip · working tree ahead toward v0.5.20 (C22 ... awaiting Cursor review + Engineer ACCEPT)" — no premature tag claim.
- `docs/IMPLEMENTATION_TASKS.md` PRIORIDAD banner and C22 row: "landed — awaiting Cursor review + ★ ACCEPT ... tag not on git yet".
- `docs/ARCHITECTURE.md` — new short note under capabilities: `crsf_serial.py` ≠ live ELRS ≠ RX connected, baud 420000 deferred.
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C22 block with the required honesty line verbatim: "Host serial ingest ≠ live ELRS ≠ RX connected ≠ UART driver ≠ Safety allow".
- Confirmed via `git tag -l | sort -V`: latest Fase C tag is `v0.5.19` (C21); no `v0.5.20` tag exists.
- Explicit **exists vs. impossible** statement, present in README/ARCHITECTURE/PLATFORM_CAPABILITY_VISION: **exists** = a pull-based host FD/path reader feeding C21's assembler, tested entirely via `pty` loopback; **impossible** = a live ExpressLRS link, a receiver "connected," configured 420000-baud UART timing, a UART/HAL driver, pilot sticks driving anything, Authority opening Safety.

---

## 10. Residual — what comes next

Per this IC's own §8 handoff: still one front at a time, Engineer-prioritized — deepening C20's policy (explicitly out of scope this Buy), actual board bring-up/flash, craft↔FS wiring, or the custom-baud (`420000`, macOS `IOSSIOSPEED` ioctl) configuration this Buy explicitly deferred. Not decided here.

---

## 11. Acceptance self-check against IC §7

- T1–T17: ✅ (see §5 table)
- pty ingest yields C19 frames via C21: ✅ (§4, T1–T2, T4, T6)
- No hardware RX required: ✅ (§0, §5, T15 — full suite ran with nothing attached)
- No `pyserial`: ✅ (§6, T12)
- No 420000 claim: ✅ (§0, §6)
- C5/C19/C20/C21 locks hold: ✅ (§0, §6, §7 — byte-diff confirmed on all five modules)
- Safety default unchanged: ✅ (§6, T10)
- Version `0.5.20`: ✅
- Docs honest: ✅ (§9)
- Not FAIL conditions: pytest does not need a dongle (§5, T15) · `pyserial` not added (§6, T12) · baud-420000 not claimed working (§0, §6) · serial not stuffed into `radio.py` (§6, T7) · no I/O added to `crsf_stream.py` (§6, T11) · no Safety allow via Authority (§6) · no "RX connected"/live ELRS claim anywhere in living docs (§9)
