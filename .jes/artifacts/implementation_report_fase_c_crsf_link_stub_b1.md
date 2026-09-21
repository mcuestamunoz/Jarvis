# Implementation Report — Fase C CRSF link stub (`B1-fase-c-crsf-link-stub`)

**IC:** [`implementation_contract_fase_c_crsf_link_stub_b1.md`](implementation_contract_fase_c_crsf_link_stub_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-21
**Status:** ★ ACCEPT CLOSED @ **`v0.5.17`**. See [review](implementation_review_fase_c_crsf_link_stub_b1.md).

---

## 0. Read this first — fixture bytes, not a link, honesty summary

This Buy adds `src/jarvis/capabilities/crsf_stub.py`: pure functions that parse **CRSF** (Crossfire) byte frames — the wire framing ExpressLRS commonly carries on the UART between a receiver and a flight controller — from **checked-in fixture bytes**. It decodes the envelope (device address, frame type, payload, CRC8) and two frame payloads: `RC_CHANNELS_PACKED` (`0x16`, required) and `LINK_STATISTICS` (`0x14`, included per the IC's own default). **There is no serial, USB, SPI, socket, or any I/O anywhere in this module** — every function takes `bytes` and returns typed data or raises `CrsfParseError`.

**Fixture CRSF parse ≠ live ELRS ≠ a pilot link.** This module does not implement the ELRS *air* protocol (RF, binding, telemetry timing), never opens a port to a real receiver, and nothing it decodes reaches `SimulatedRadioIngress`, `RadioIntentAdapter`, autonomy `submit_command`, or any `SafetyGate` — decoding a CRSF frame here produces typed data only.

**Module boundary preserved exactly (IC §0 decision 5):** `crsf_stub.py` is a **separate module** from `radio.py`, on purpose — `git diff --stat` on both `radio.py` and `intent.py` is **empty**; C5's own T5 lock ("no `decode_crsf`/`decode_elrs`/`open_serial` on `radio.py`") is untouched, not merely re-verified.

---

## 1. Package layout vs IC §1

```text
src/jarvis/capabilities/
  crsf_stub.py       # NEW — envelope parse + RC channels + link statistics, pure functions
  radio.py            # byte-unchanged (confirmed via git diff)
  __init__.py          # docstring extended to point at crsf_stub.py; no new top-level exports (see §2)

tests/
  fixtures/crsf/       # NEW — 4 checked-in .bin fixtures
    rc_channels_valid.bin
    rc_channels_bad_crc.bin
    rc_channels_truncated.bin
    link_statistics_valid.bin
  test_fase_c_crsf_link_stub_b1.py   # NEW
```

No `src/jarvis/radio/`, no `flight_software/radio/`, no `native/**/crsf*` was created — matching the IC's own explicit "do not create" list.

---

## 2. Types / API implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| `CrsfParseError` | §2.1 | ✅ a single exception type (documented choice over a `Result[...]` type — simpler, matches this project's existing `ValueError`/`NotImplementedError` idioms elsewhere in `capabilities/`) |
| `CrsfFrame` (`device_addr`, `frame_type`, `payload`, `crc`) | §2.1 | ✅ Pydantic model, `extra="forbid"` |
| `parse_crsf_frame(data: bytes) -> CrsfFrame` | §2.1 | ✅ validates length (`>= 4` bytes, `frame_len` matches actual byte count) and CRC8 (poly `0xD5`, computed over `frame_type + payload`) |
| `decode_rc_channels_packed(payload: bytes) -> CrsfRcChannels` | §2.2 | ✅ 16 × 11-bit LSB-first unpack from a 22-byte payload; rejects wrong length |
| `CrsfRcChannels.channels` | §2.2 | ✅ a fixed-length 16-`int` tuple, each in `[0, 2047]` — Pydantic validates the length itself |
| `decode_link_statistics(payload: bytes) -> CrsfLinkStatistics` | §2.3 | ✅ 10-byte struct (`uplink_rssi_1/2`, `uplink_link_quality`, `uplink_snr`, `active_antenna`, `rf_profile`, `uplink_tx_power`, `downlink_rssi`, `downlink_link_quality`, `downlink_snr` — signed `snr` fields, unsigned everything else, matching the widely-documented CRSF layout) |
| `describe_crsf_frame(frame: CrsfFrame) -> str` | §2.4 | ✅ debug string only, no Safety/autonomy call |
| Non-goals (§2.5) | §2.5 | ✅ no `open_serial`, no `ElrsLink`, no `connect()`, no background thread — confirmed absent by grep and by direct module inspection in tests |

`CRSF_FRAMETYPE_RC_CHANNELS_PACKED = 0x16` and `CRSF_FRAMETYPE_LINK_STATISTICS = 0x14` are exported as named constants (`Final[int]`) rather than bare magic numbers, for callers/tests to reference.

**Not exported at the `jarvis.capabilities` package top level, deliberately** — `crsf_stub`'s public symbols are reachable via `from jarvis.capabilities.crsf_stub import ...` (or `from jarvis.capabilities import crsf_stub`), same spirit as keeping `radio.py`'s own boundary crisp: a link-stub module earns its own namespace rather than blending into the general capabilities surface. `capabilities/__init__.py`'s own docstring was extended with a pointer paragraph (disclosed in §7 below) but `__all__` is unchanged.

---

## 3. Frame envelope + CRC8 (IC §0 decision 6)

```text
[device_addr:1][frame_len:1][frame_type:1][payload:frame_len-2][crc8:1]
```

`frame_len` covers `frame_type + payload + crc8` (i.e. total frame bytes = `frame_len + 2`). CRC8 is the standard CRSF/DVB-S2 polynomial `0xD5`, computed bitwise over `data[2:crc_index]` (`frame_type` + `payload`, excluding `device_addr`/`frame_len`/the CRC byte itself). Verified empirically against hand-computed fixture bytes (§5) before any formal test was written.

**Truncated frames and bad-CRC frames both raise `CrsfParseError`** — confirmed via the `rc_channels_truncated.bin` and `rc_channels_bad_crc.bin` fixtures (§4, T2/T3); there is no silent partial-success path anywhere in `parse_crsf_frame`.

---

## 4. Fixtures (IC §0 decision 8)

Four checked-in binary fixtures under `tests/fixtures/crsf/` (not downloaded at test time, not generated on the fly by the test module):

| File | Bytes | Content |
|---|---|---|
| `rc_channels_valid.bin` | 26 | Valid `RC_CHANNELS_PACKED` frame, all 16 channels at CRSF mid-value `992`, correct CRC8 |
| `rc_channels_bad_crc.bin` | 26 | Same frame with the final CRC byte XOR-flipped (`0xAD` → `0x52`) |
| `rc_channels_truncated.bin` | 23 | Same frame with the last 3 bytes dropped (declared `frame_len` no longer matches actual length) |
| `link_statistics_valid.bin` | 14 | Valid `LINK_STATISTICS` frame with distinguishable field values (e.g. `uplink_snr=-42`, `downlink_snr=-40`) to catch field-order bugs |

Fixture bytes were computed with a scratch script implementing the same CRC8/bit-packing algorithms independently, then verified round-trip (encode → decode → same values) before being written to disk and before any formal test was written.

---

## 5. Empirical verification (before formal tests)

```text
frame: CrsfFrame(device_addr=0xC8, frame_type=0x16, payload_len=22)
type match: True
channels: (992, 992, 992, 992, 992, 992, 992, 992, 992, 992, 992, 992, 992, 992, 992, 992)
bad crc raised OK: CRC8 mismatch: frame declares 0x52, computed 0xAD
truncated raised OK: frame length mismatch: header declares 26 total bytes (frame_len=24), got 23
ls frame: CrsfFrame(device_addr=0xC8, frame_type=0x14, payload_len=10)
ls type match: True
stats: uplink_rssi_1=80 uplink_rssi_2=0 uplink_link_quality=99 uplink_snr=-42 active_antenna=0 rf_profile=2 uplink_tx_power=20 downlink_rssi=90 downlink_link_quality=99 downlink_snr=-40

# wrong-length edge cases
short tuple raised OK: ValidationError
wrong payload len raised OK: RC_CHANNELS_PACKED payload must be 22 bytes, got 21
wrong ls payload len raised OK: LINK_STATISTICS payload must be 10 bytes, got 9
```

---

## 6. Tests (IC §4)

| ID | Check | Result |
|---|---|---|
| T1 | Valid RC_CHANNELS_PACKED fixture → 16 channel ints in documented range/shape | ✅ `test_t1_valid_rc_channels_fixture_decodes_to_16_channel_ints_in_range` |
| T2 | Truncated frame → typed parse failure | ✅ `test_t2_truncated_frame_raises_typed_parse_error` |
| T3 | Bad CRC → typed parse failure | ✅ `test_t3_bad_crc_frame_raises_typed_parse_error` |
| T4 | Valid LINK_STATISTICS fixture → typed fields populated | ✅ `test_t4_valid_link_statistics_fixture_populates_typed_fields` |
| T5 | Module under test has no `serial`/`socket`/`pty` imports and no `open(` for device paths | ✅ `test_t5_module_under_test_has_no_io_imports_or_device_open` (real-code-only, docstrings/comments stripped via `tokenize` — see honesty-test note below) |
| T6 | `RadioIntentAdapter.parse(...)` still raises `NotImplementedError` matching `not_implemented` | ✅ `test_t6_radio_intent_adapter_still_raises_not_implemented` (including with real CRSF fixture bytes as input — still refuses) |
| T7 | C5 T5 still holds: `radio.py` has no public `decode_crsf`/`decode_elrs`/`open_serial`/`write_pwm` | ✅ `test_t7_radio_py_still_has_no_public_decode_or_serial_symbols` |
| T8 | Grep: no CRSF/ELRS under `native/`; no craft imports of new symbols from `core/`/`adapters/` | ✅ `test_t8_no_crsf_or_elrs_under_native_and_no_craft_wiring` |
| T9 | `default_safety_gate()` still RejectAll; `ArmedAllowlist` behavior unchanged | ✅ `test_t9_default_safety_gate_still_reject_all_and_armed_allowlist_unchanged` |
| T10 | `pyproject` `0.5.17`; re-pin `0.5.16` version checkpoints | ✅ §7 below |
| T11 | Full suite green | ✅ **3428 passed, 1 skipped** (was 3412 — exact +16 delta) |
| T12 | Report states: fixture CRSF ≠ live ELRS ≠ pilot link; no serial product | ✅ §0 above |

New Python test module `tests/test_fase_c_crsf_link_stub_b1.py` — **16 tests**, all passing:

```text
test_t1_valid_rc_channels_fixture_decodes_to_16_channel_ints_in_range PASSED
test_t2_truncated_frame_raises_typed_parse_error PASSED
test_t3_bad_crc_frame_raises_typed_parse_error PASSED
test_t4_valid_link_statistics_fixture_populates_typed_fields PASSED
test_t5_module_under_test_has_no_io_imports_or_device_open PASSED
test_t6_radio_intent_adapter_still_raises_not_implemented PASSED
test_t7_radio_py_still_has_no_public_decode_or_serial_symbols PASSED
test_t8_no_crsf_or_elrs_under_native_and_no_craft_wiring PASSED
test_t9_default_safety_gate_still_reject_all_and_armed_allowlist_unchanged PASSED
test_capability_registry_default_still_empty PASSED
test_describe_crsf_frame_is_pure_debug_helper PASSED
test_rc_channels_wrong_payload_length_raises PASSED
test_link_statistics_wrong_payload_length_raises PASSED
test_crsf_frame_rejects_buffer_shorter_than_minimum PASSED
test_no_route_from_crsf_to_autonomy_submit_command PASSED
test_t10_pyproject_version_is_0_5_17 PASSED
```

**A false-positive honesty-test bug caught and fixed during this Buy (disclosed, matching the project's established convention):** the first draft of `test_t5_...` and `test_no_route_from_crsf_to_autonomy_submit_command` checked bare substrings (`"usb"`, `"submit_command"`) anywhere in `crsf_stub.py`'s source text — which false-failed against this module's own honesty-prose docstring (which legitimately says "does not open a serial, USB, or SPI port" and "nothing in this module feeds it... `submit_command`..." to *disclose* their absence). Fixed with a `tokenize`-based comment/docstring stripper (`_strip_python_comments_and_docstrings`) shared by both tests, rather than a naive substring check — verified against the fixed module afterward.

**T11 (full suite):** `pytest -q` — **3428 passed, 1 skipped** (baseline before this Buy was 3412 passed, 1 skipped; delta is exactly the 16 new tests, no other file's pass/fail count moved; the one skip is unrelated/pre-existing).

Twenty-four pre-existing test files hardcoded the prior checkpoint version string (`"0.5.16"`) as a version-pin assertion. Since this IC explicitly requires the `0.5.17` bump (§0 decision 14), all twenty-four were re-pinned to `"0.5.17"`:

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
| Opening USB/serial to a real RX as acceptance | ✅ absent | T5 — no `serial`/`socket`/`pty`/`subprocess`/`open(` in real code |
| Claiming "ELRS connected / on air" | ✅ absent | Module docstring + this report explicitly state the opposite throughout |
| RC channels → mixer/ESC/PWM | ✅ absent | `test_no_route_from_crsf_to_autonomy_submit_command` — module has no `submit_command`/`propose_command` attribute and no `flight_software` import |
| Making `RadioIntentAdapter` succeed on bytes | ✅ absent | T6 — still raises `NotImplementedError`, even fed real CRSF fixture bytes |
| Putting decode APIs on `radio.py` | ✅ absent | T7 + `git diff --stat radio.py` empty |
| Safety allow via CRSF / Authority | ✅ absent | T9 — `default_safety_gate()`/`ArmedAllowlistSafetyGate` untouched; nothing in `crsf_stub.py` constructs an `AuthoritySignal` or calls any `SafetyGate` |
| C++ CRSF stack in `native/` | ✅ absent | T8 — grep for "crsf"/"elrs" (case-insensitive) under `native/` returns nothing |
| Marking radio `available` in default registry | ✅ absent | `CapabilityRegistry.load_default()` re-confirmed empty (capabilities/providers/skills all `[]`) |

**"One front" discipline (process lock after C6):** this Buy stayed exactly within the CRSF byte-fixture parse scope. No serial drivers, USB RX open, GPIO, MCU radio C++, craft↔FS wiring, Safety policy changes, or flash were touched or opened.

---

## 8. Integration rules (IC §3) — confirmed unchanged

- C5 `radio.py` — byte-unchanged (`git diff --stat` empty); T5 stays green.
- C2 `RadioIntentAdapter` — still refuses, re-verified with real fixture bytes as input (T6).
- C4 autonomy — no CRSF → `submit_command` path exists anywhere.
- C17 Safety — untouched; default stays `RejectAllSafetyGate`; `ArmedAllowlistSafetyGate` behavior re-verified identical.
- Registry — default stays empty.
- C13–C18 native — untouched; grep-confirmed no CRSF/ELRS token anywhere under `native/`.

---

## 9. Files changed

**New:**
- `src/jarvis/capabilities/crsf_stub.py`
- `tests/fixtures/crsf/rc_channels_valid.bin`
- `tests/fixtures/crsf/rc_channels_bad_crc.bin`
- `tests/fixtures/crsf/rc_channels_truncated.bin`
- `tests/fixtures/crsf/link_statistics_valid.bin`
- `tests/test_fase_c_crsf_link_stub_b1.py`
- `.jes/artifacts/implementation_report_fase_c_crsf_link_stub_b1.md` (this file)

**Modified:**
- `pyproject.toml` — version `0.5.16` → `0.5.17`
- `src/jarvis/capabilities/__init__.py` — docstring extended with a C19 pointer paragraph; `__all__`/imports unchanged (see §2 — deliberately not exported at package top level)
- `docs/ARCHITECTURE.md`, `docs/PLATFORM_CAPABILITY_VISION.md`, `docs/IMPLEMENTATION_TASKS.md`, `README.md` — C19 sections (see §10)
- 24 test files — re-pinned stale `0.5.16` version-checkpoint assertions to `0.5.17`

**Not touched (confirmed):** `orchestrator.py`, Board (`ui/spatial-board/`), `library/`, `native/flight_control/**` (C++ tree, zero references to CRSF/ELRS), `src/jarvis/capabilities/radio.py`, `src/jarvis/capabilities/intent.py`, `src/jarvis/capabilities/safety.py`, `src/jarvis/flight_software/**`, `.jes/state/engineering_state.json`.

---

## 10. Docs honesty confirmation (IC §6)

- README header banner: "v0.5.16 tagged tip · working tree ahead toward v0.5.17 (C19 ... awaiting Cursor review + Engineer ACCEPT)" — no premature tag claim.
- `docs/IMPLEMENTATION_TASKS.md` PRIORIDAD banner and C19 row: "landed — awaiting Cursor review + ★ ACCEPT ... tag not on git yet".
- `docs/ARCHITECTURE.md` — new short note under capabilities: CRSF fixture stub ≠ ELRS product.
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C19 block with honesty line.
- Confirmed via `git tag -l | sort -V`: latest Fase C tag is `v0.5.16` (C18); no `v0.5.17` tag exists.
- Explicit **exists vs. impossible** statement, present in README/ARCHITECTURE/PLATFORM_CAPABILITY_VISION: **exists** = parsing documented CRSF byte fixtures into typed envelope + RC channels + link statistics; **impossible** = a live ExpressLRS link, a receiver "connected," pilot sticks driving anything, a CRSF driver product.

---

## 11. Residual — what comes next

Per this IC's own §8 handoff: still one front at a time, Engineer-prioritized — actual board bring-up/flash (separately scoped), craft↔FS wiring, or deepening the link stub itself (more CRSF frame types, a thin mapping helper into `RadioStubFrame` — explicitly optional and not built this Buy). Not decided here.

---

## 12. Acceptance self-check against IC §7

- T1–T12: ✅ (see §6 table)
- Valid RC fixture parses: ✅ (§5, T1)
- Bad frames fail typed: ✅ (§5, T2/T3)
- No I/O: ✅ (§7, T5)
- C5 radio locks hold: ✅ (§0, §7, §8 — byte-diff confirmed)
- Safety default unchanged: ✅ (§7, T9)
- Version `0.5.17`: ✅
- No craft/native coupling: ✅ (§7, T8)
- Docs honest: ✅ (§10)
- Not FAIL conditions: no serial product path (§7) · no live-ELRS claim anywhere (§0, §10) · `RadioIntentAdapter` does not succeed (§7, T6) · no CRSF→autonomy execution (§7) · decode not stuffed into `radio.py` (§7, T7) · Safety not weakened (§7, T9)
