# Implementation Report — Fase C CRSF byte-stream assembler (`B1-fase-c-crsf-byte-stream`)

**IC:** [`implementation_contract_fase_c_crsf_byte_stream_b1.md`](implementation_contract_fase_c_crsf_byte_stream_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-22
**Status:** ★ ACCEPT CLOSED @ **`v0.5.19`**. See [review](implementation_review_fase_c_crsf_byte_stream_b1.md).

---

## 0. Read this first — byte buffer, not a UART, honesty summary

This Buy adds `src/jarvis/capabilities/crsf_stream.py`: `CrsfByteStreamAssembler`, a pure in-memory byte buffer that reassembles C19's typed `CrsfFrame`s from bytes delivered in **arbitrary chunks** — the shape a UART actually delivers data in — without ever opening anything. `feed(data: bytes) -> list[CrsfFrame]` appends `data` and returns every complete, CRC-valid frame now available; incomplete data waits in a bounded leftover buffer; invalid complete windows are silently dropped-and-resynced one byte at a time (never raised to the caller).

**Byte-stream assembler ≠ UART open ≠ live ELRS ≠ a pilot link ≠ Safety allow.** There is no `serial`/`socket`/`pty`/USB/subprocess/`open()` anywhere in this module, no class named like `Serial`/`UartPort`, no baud-rate concept — every input is `bytes` a caller already has in memory (in this repo, always fixture/synthetic bytes).

**CRC/envelope truth stays exactly where C19 put it (IC §0 decision 5):** the assembler never reimplements CRC8 or the frame envelope. It slices a candidate window of exactly `frame_len + 2` bytes and hands that window, byte-for-byte, to `crsf_stub.parse_crsf_frame` — confirmed by `git diff --stat crsf_stub.py` being **empty**, and by a dedicated test (T17) asserting the assembler's own source contains no `0xD5` (the CRC8 polynomial) anywhere.

**Module boundary preserved exactly:** `crsf_stream.py` is a **new, separate** module — not folded into `crsf_stub.py`, `crsf_dual_role.py`, or `radio.py`. `git diff --stat` on `crsf_stub.py`, `crsf_dual_role.py`, `radio.py`, `intent.py`, and `safety.py` is **empty** — C5's T5 lock and every prior Fase C radio/Safety contract are untouched, not merely re-verified.

---

## 1. Package layout vs IC §1

```text
src/jarvis/capabilities/
  crsf_stream.py       # NEW — CrsfByteStreamAssembler + ingest_stream_bytes
  crsf_dual_role.py      # byte-unchanged (confirmed via git diff) — reused, not rewritten
  crsf_stub.py             # byte-unchanged (confirmed via git diff) — reused, not rewritten
  radio.py                  # byte-unchanged (confirmed via git diff)
  intent.py / safety.py      # byte-unchanged (confirmed via git diff)
  __init__.py                 # docstring extended with a C21 pointer paragraph; no new top-level exports

tests/
  fixtures/crsf/                # REUSED from C19 (all 4 existing .bin fixtures) — no new binary fixture needed
  test_fase_c_crsf_byte_stream_b1.py   # NEW
```

No new binary fixture was needed — every test either reuses C19's own `rc_channels_valid.bin`/`rc_channels_truncated.bin`/`rc_channels_bad_crc.bin`/`link_statistics_valid.bin`, or (for T8's "aux channel high via stream" case) constructs a synthetic frame in-test using the same CRC8/bit-packing algorithm the IC's own examples use, matching the "mutated/synthetic concatenation is OK" note in IC §4.

---

## 2. Types / API implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| `CrsfByteStreamAssembler(max_buffer=256, max_frame_len=64)` | §2.1 | ✅ both defaults match the IC's own locked defaults exactly |
| `.feed(data: bytes) -> list[CrsfFrame]` | §2.1 | ✅ never raises `CrsfParseError`; `feed(b"")` is a no-op returning `[]`; concatenated complete frames in one `feed` return all of them, in order (T4) |
| `.leftover() -> bytes` | §2.1 | ✅ exposes the unconsumed buffer for tests |
| `.reset() -> None` | §2.1 | ✅ clears leftover buffer and drop counter |
| `.dropped_byte_count` | §2.1 | ✅ cumulative count across desync-resync drops and leftover-cap overflow drops |
| `ingest_stream_bytes(data, *, assembler, policy, ingress=None) -> list[RadioDualRoleResult]` | §2.2 | ✅ feeds, then for each new `0x16` frame: `decode_rc_channels_packed` → C20's `ingest_rc_channels` unchanged; below-threshold `None` results are omitted, not appended; `0x14`/unknown types skipped by this helper (still in `assembler.feed(...)`'s own return value) |
| Non-goals (§2.3) | §2.3 | ✅ no `open_serial`, no baud-rate API, no MCU HAL, no mixer/ESC, no Safety calls, no Intent from sticks, no extra Authority kinds, no address whitelist (C19's own `parse_crsf_frame` already accepts any `device_addr`) — confirmed absent by grep and direct module inspection in tests |

---

## 3. Incomplete-vs-invalid + desync policy (IC §0 decisions 6, 7, 8) — implemented exactly as locked

**Incomplete candidate (buffer shorter than the declared total) → wait.** `_try_extract_one()` returns `None` without consuming or dropping anything when `len(self._buffer) < total`; the bytes remain in `leftover()` for a future `feed(...)` call to complete. This is the deliberate inverse of C19's own `parse_crsf_frame`, which raises on a too-short buffer — the assembler is the layer that decides "not yet" vs. "never," not `parse_crsf_frame`.

**Invalid complete window → drop 1 byte, retry (never raised to caller).** When a full-length candidate fails `parse_crsf_frame` (bad CRC or, in principle, a length mismatch the assembler itself would never construct), the assembler drops exactly one byte from the front of the buffer, increments `dropped_byte_count`, and retries from the new position — looping (not recursing) until it either finds a valid frame or the buffer is exhausted.

**Plausible `frame_len` desync guard.** A declared `frame_len` outside `[2, 64]` (`_MIN_FRAME_LEN = 2`, `max_frame_len = 64` default) is treated as desync immediately — drop one byte, retry — rather than waiting for however many bytes a bogus giant length would demand. Both constants are named module-level values (`_MIN_FRAME_LEN`, `_DEFAULT_MAX_FRAME_LEN`), documented in the module's own docstring and here.

**Bounded leftover.** `_enforce_max_buffer()` runs at the end of every `feed(...)` call — if the leftover buffer exceeds `max_buffer` (default `256`), the oldest bytes are dropped down to the cap, counted in `dropped_byte_count`. Verified by `test_max_buffer_bounds_leftover_growth_on_noise` (feeding 200 bytes of noise into a `max_buffer=32` assembler; leftover never exceeds 32).

---

## 4. Empirical verification (before formal tests)

```text
=== T1: one feed of valid fixture ===
frames: 1 ['0x16'] leftover: b''
=== T2: byte-at-a-time ===
frame appeared at byte index 25 of 25
total frames: 1 leftover: b''
=== T3: mid-frame split ===
f1: [] f2 count: 1 leftover: b''
=== T4: concatenated RC + LS ===
frames: ['0x16', '0x14'] leftover: b''
=== T5: truncated ===
frames: [] leftover len: 23 dropped: 0
=== T6: garbage prefix + valid ===
frames: ['0x16'] dropped: 3 leftover: b''
=== T7: bad crc ===
frames: [] dropped: 4 leftover: b'...' (22 bytes remaining — desync stopped
                                          once the remaining window pointed
                                          past the buffer's end, correctly
                                          waiting rather than looping forever)
=== T8: aux channel threshold via stream ===
results (all-992, below threshold): []

# separately, a synthetic aux-channel-high frame:
results: [RadioDualRoleResult(..., authority=AuthoritySignal(..., source='radio', kind='kill',
          payload='crsf_aux_channel=4 value=1800'))]
```

All outcomes matched hand-derived predictions exactly before any formal test was written.

---

## 5. Tests (IC §4)

| ID | Check | Result |
|---|---|---|
| T1 | One `feed` of `rc_channels_valid.bin` → exactly 1 `CrsfFrame` type `0x16`; leftover empty | ✅ `test_t1_one_feed_of_valid_fixture_gives_exactly_one_frame` |
| T2 | Same fixture byte-at-a-time → no frame until the last byte, then 1 frame; leftover empty | ✅ `test_t2_byte_at_a_time_gives_no_frame_until_last_byte` |
| T3 | Mid-frame split → `[]` then 1 frame | ✅ `test_t3_mid_frame_split_waits_then_completes` |
| T4 | Concatenate valid RC + valid link-stats in one `feed` → 2 frames, types `0x16` then `0x14`, leftover empty | ✅ `test_t4_concatenated_rc_and_link_stats_gives_two_frames_in_order` |
| T5 | Feed `rc_channels_truncated.bin` → 0 frames, leftover kept (wait, not raise) | ✅ `test_t5_truncated_frame_gives_zero_frames_and_waits` |
| T6 | Garbage prefix + valid RC fixture → eventually 1 valid `0x16` frame; `dropped_byte_count >= 1` | ✅ `test_t6_garbage_prefix_resyncs_and_drops_at_least_one_byte` |
| T7 | One `feed` of `rc_channels_bad_crc.bin` → 0 frames; no `CrsfParseError` leaked | ✅ `test_t7_bad_crc_gives_zero_frames_no_exception_leaked` |
| T8 | Optional helper: aux ch 4 ≥ 1500 → ≥1 `RadioDualRoleResult` Authority `kill`; below-threshold → empty | ✅ `test_t8_aux_channel_high_via_stream_gives_authority_kill_result` (+ `test_t8b_below_threshold_stream_gives_empty_results`) |
| T9 | No I/O imports / device `open(` in assembler module real code | ✅ `test_t9_module_under_test_has_no_io_imports_or_device_open` |
| T10 | C5 T5: `radio.py` has no `decode_crsf`/`decode_elrs`/`open_serial`/`write_pwm` | ✅ `test_t10_radio_py_still_has_no_public_decode_or_serial_symbols` |
| T11 | `RadioIntentAdapter` still `not_implemented` | ✅ `test_t11_radio_intent_adapter_still_raises_not_implemented` (fed real assembled frames — still refuses) |
| T12 | Assembler/helper do not call `submit_command`/import autonomy surface | ✅ `test_t12_assembler_and_helper_never_call_submit_command_or_import_autonomy` |
| T13 | `default_safety_gate()` still RejectAll | ✅ `test_t13_default_safety_gate_still_reject_all` |
| T14 | `pyproject` `0.5.19`; re-pin `0.5.18` checkpoints | ✅ §6 below |
| T15 | Full suite green | ✅ **3465 passed, 1 skipped** (was 3444 — exact +21 delta) |
| T16 | Report: assembler ≠ UART open ≠ live ELRS ≠ Safety allow | ✅ §0 above |
| T17 | Assembler source calls `parse_crsf_frame` (no second CRC implementation) | ✅ `test_t17_assembler_calls_c19_parse_crsf_frame_not_a_second_crc_impl` |

New Python test module `tests/test_fase_c_crsf_byte_stream_b1.py` — **21 tests**, all passing:

```text
test_t1_one_feed_of_valid_fixture_gives_exactly_one_frame PASSED
test_t2_byte_at_a_time_gives_no_frame_until_last_byte PASSED
test_t3_mid_frame_split_waits_then_completes PASSED
test_t4_concatenated_rc_and_link_stats_gives_two_frames_in_order PASSED
test_t5_truncated_frame_gives_zero_frames_and_waits PASSED
test_t6_garbage_prefix_resyncs_and_drops_at_least_one_byte PASSED
test_t7_bad_crc_gives_zero_frames_no_exception_leaked PASSED
test_t8_aux_channel_high_via_stream_gives_authority_kill_result PASSED
test_t8b_below_threshold_stream_gives_empty_results PASSED
test_t9_module_under_test_has_no_io_imports_or_device_open PASSED
test_t10_radio_py_still_has_no_public_decode_or_serial_symbols PASSED
test_t11_radio_intent_adapter_still_raises_not_implemented PASSED
test_t12_assembler_and_helper_never_call_submit_command_or_import_autonomy PASSED
test_t13_default_safety_gate_still_reject_all PASSED
test_t14_pyproject_version_is_0_5_19 PASSED
test_t17_assembler_calls_c19_parse_crsf_frame_not_a_second_crc_impl PASSED
test_reset_clears_leftover_and_drop_counter PASSED
test_max_buffer_bounds_leftover_growth_on_noise PASSED
test_feed_empty_bytes_is_a_noop PASSED
test_no_crsf_or_elrs_under_native_and_no_craft_wiring PASSED
test_capability_registry_default_still_empty PASSED
```

**A test-scope bug caught and fixed during this Buy (disclosed, matching the project's established convention):** the first draft of the native-tree isolation test also checked for the bare substring `"uart"` (in addition to `"crsf"`/`"elrs"`) anywhere under `native/`. It false-failed against `native/flight_control/README.md`'s own **pre-existing, legitimate** C18 honesty prose ("no GPIO/UART/any real I/O"), which discloses the *absence* of UART I/O in the MCU scaffold, not a driver. Fixed by scoping the check to `crsf`/`elrs` only — matching C19's and C20's own equivalent tests — and documenting why in the test's own docstring.

**T15 (full suite):** `pytest -q` — **3465 passed, 1 skipped** (baseline before this Buy was 3444 passed, 1 skipped; delta is exactly the 21 new tests, no other file's pass/fail count moved; the one skip is unrelated/pre-existing).

Twenty-six pre-existing test files hardcoded the prior checkpoint version string (`"0.5.18"`) as a version-pin assertion, including C19's and C20's own test modules. Since this IC explicitly requires the `0.5.19` bump (§0 decision 14), all twenty-six were re-pinned to `"0.5.19"`:

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
| `serial`/USB/`/dev/tty*` as acceptance | ✅ absent | T9 — no such tokens in real code |
| Naming the module a "UART driver" in docs | ✅ absent | README/report/module docstring consistently call it a byte buffer, explicitly disclaim driver-ness |
| Claiming RX connected / live ELRS | ✅ absent | Module docstring + this report state the opposite throughout |
| Pilot sticks control craft | ✅ absent | No mixer/ESC path anywhere |
| Authority → Safety `allow` | ✅ absent | T13; C20's own already-tested Authority-trace-only guarantee is reused unchanged (`ingest_rc_channels` byte-unchanged) |
| Auto `submit_command` | ✅ absent | T12 |
| Decode/stream APIs on `radio.py` | ✅ absent | T10 + `git diff --stat radio.py` empty |
| Reimplement CRC in the assembler | ✅ absent | T17 — no `0xD5` anywhere in `crsf_stream.py`; `parse_crsf_frame` is called, not reimplemented |
| Deepen C20 policy / Intent from sticks | ✅ absent | `ingest_stream_bytes` calls C20's `ingest_rc_channels` unchanged; `crsf_dual_role.py` byte-unchanged |
| Marking radio `available` in registry | ✅ absent | `CapabilityRegistry.load_default()` re-confirmed empty |
| Flash / craft↔FS | ✅ absent | Not touched; `native/` grep-confirmed clean of `crsf`/`elrs` |

**"One front" discipline (process lock after C6):** this Buy stayed exactly within the byte-stream assembler scope. No serial/USB open, MCU UART, GPIO, flash, craft↔FS wiring, Safety policy edits, mixer/ESC, or C20 policy deepening were touched or opened.

---

## 7. Integration rules (IC §3) — confirmed unchanged

- C19 `parse_crsf_frame` — **called** on exact candidate slices, not rewritten; still raises internally on bad windows, which the assembler catches (never leaked); `crsf_stub.py` byte-unchanged.
- C19 truncated-buffer behavior — the assembler waits instead of raising when its own leftover is shorter than the declared total; this is additive behavior in a new module, not a change to `parse_crsf_frame`'s own contract (which still raises when handed a too-short buffer directly, per C19's own tests, unmodified).
- C20 policy/bridge — unchanged; `ingest_stream_bytes` is a caller of `ingest_rc_channels`, not a reimplementation; `crsf_dual_role.py` byte-unchanged.
- C5 `radio.py` — no `decode_*`/`open_serial`/`write_pwm`/stream types; byte-unchanged.
- C2 `RadioIntentAdapter` — still refuses.
- C4 autonomy — no stream → `submit_command` path exists anywhere.
- C17 Safety — untouched; default stays `RejectAllSafetyGate`.
- Registry — default stays empty.

---

## 8. Files changed

**New:**
- `src/jarvis/capabilities/crsf_stream.py`
- `tests/test_fase_c_crsf_byte_stream_b1.py`
- `.jes/artifacts/implementation_report_fase_c_crsf_byte_stream_b1.md` (this file)

**Modified:**
- `pyproject.toml` — version `0.5.18` → `0.5.19`
- `src/jarvis/capabilities/__init__.py` — docstring extended with a C21 pointer paragraph; `__all__`/imports unchanged (deliberately not exported at package top level, same choice as C19/C20)
- `docs/ARCHITECTURE.md`, `docs/PLATFORM_CAPABILITY_VISION.md`, `docs/IMPLEMENTATION_TASKS.md`, `README.md` — C21 sections (see §9)
- 26 test files — re-pinned stale `0.5.18` version-checkpoint assertions to `0.5.19`

**Not touched (confirmed):** `orchestrator.py`, Board (`ui/spatial-board/`), `library/`, `native/flight_control/**` (zero CRSF/ELRS references), `src/jarvis/capabilities/crsf_stub.py`, `src/jarvis/capabilities/crsf_dual_role.py`, `src/jarvis/capabilities/radio.py`, `src/jarvis/capabilities/intent.py`, `src/jarvis/capabilities/safety.py`, `src/jarvis/flight_software/**`, `.jes/state/engineering_state.json`.

---

## 9. Docs honesty confirmation (IC §6)

- README header banner: "v0.5.18 tagged tip · working tree ahead toward v0.5.19 (C21 ... awaiting Cursor review + Engineer ACCEPT)" — no premature tag claim.
- `docs/IMPLEMENTATION_TASKS.md` PRIORIDAD banner and C21 row: "landed — awaiting Cursor review + ★ ACCEPT ... tag not on git yet".
- `docs/ARCHITECTURE.md` — new short note under capabilities: `crsf_stream.py` ≠ UART driver ≠ live ELRS.
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C21 block with the required honesty line verbatim: "Byte-stream assembler ≠ UART open ≠ live ELRS ≠ a pilot link ≠ Safety allow".
- Confirmed via `git tag -l | sort -V`: latest Fase C tag is `v0.5.18` (C20); no `v0.5.19` tag exists.
- Explicit **exists vs. impossible** statement, present in README/ARCHITECTURE/PLATFORM_CAPABILITY_VISION: **exists** = a deterministic byte-chunk-to-frame reassembler reusing C19's parse and C20's bridge unchanged; **impossible** = an open UART/serial port, a live ExpressLRS link, a receiver "connected," pilot sticks driving anything, Authority opening Safety.

---

## 10. Residual — what comes next

Per this IC's own §8 handoff: still one front at a time, Engineer-prioritized — deepening C20's policy (more channels, configurable Authority kinds — explicitly out of scope this Buy), actual board bring-up/flash, or craft↔FS wiring. Not decided here.

---

## 11. Acceptance self-check against IC §7

- T1–T17: ✅ (see §5 table)
- Chunks reassemble to C19 frames: ✅ (§4, T1–T4)
- Wait-on-truncated: ✅ (§3, T5)
- Drop-1 on bad complete window: ✅ (§3, T6/T7)
- Optional C20 path typed: ✅ (§2, T8)
- C5/C19/C20 locks hold: ✅ (§0, §6, §7 — byte-diff confirmed on all four modules)
- Safety default unchanged: ✅ (§6, T13)
- Version `0.5.19`: ✅
- Docs honest: ✅ (§9)
- Not FAIL conditions: no serial product (§6) · no `CrsfParseError` leaked on bad-CRC feed (§5, T7) · CRC not reimplemented (§6, T17) · no Safety allow via Authority anywhere (§6) · no CRSF→autonomy execution (§6, T12) · decode/stream not stuffed into `radio.py` (§6, T10) · C19 parse behavior unchanged (§0, §7 — byte-diff confirmed)
