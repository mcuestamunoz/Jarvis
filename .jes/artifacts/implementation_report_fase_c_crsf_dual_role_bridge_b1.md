# Implementation Report — Fase C CRSF → dual-role bridge (`B1-fase-c-crsf-dual-role-bridge`)

**IC:** [`implementation_contract_fase_c_crsf_dual_role_bridge_b1.md`](implementation_contract_fase_c_crsf_dual_role_bridge_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-22
**Status:** ★ ACCEPT CLOSED @ **`v0.5.18`**. See [review](implementation_review_fase_c_crsf_dual_role_bridge_b1.md).

---

## 0. Read this first — bridge, not a link, honesty summary

This Buy adds `src/jarvis/capabilities/crsf_dual_role.py`: a small, deterministic bridge from C19's decoded `CrsfRcChannels` into C5's typed `RadioStubFrame`/`RadioDualRoleResult`, under one documented policy (`CrsfDualRolePolicy`). It is **Authority-only** — the bridge never synthesizes `Intent` text from RC channel values, never returns `role="intent"`/`"both"`, and produces `AuthorityKind="kill"` (the one locked kind this Buy supports) only when a configured aux channel's value is `>= threshold`; below threshold it returns `None`.

**Still fixture/host-only, still not a link.** Nothing in this module opens a serial/USB/SPI port, reassembles a byte stream, or claims a receiver is "connected." **Authority stays trace-only relative to Safety** — the bridge never constructs a `SafetyRequest`, never calls `SafetyGate.evaluate(...)`, and `default_safety_gate()`/`ArmedAllowlistSafetyGate` are untouched; even wiring the bridge's own `AuthoritySignal.id` into a `SafetyRequest.authority_signal_id` (tested explicitly, §6) does not flip any shipped gate's decision.

**Module boundary preserved exactly (IC §0 decision 4):** `crsf_dual_role.py` is a **new, separate** module — not folded into `crsf_stub.py` (would bloat its own C19 scope) and, critically, **not** folded into `radio.py`. `git diff --stat` on `radio.py`, `intent.py`, and `safety.py` is **empty** — C5's T5 lock and C2/C17's Safety contracts are untouched, not merely re-verified.

---

## 1. Package layout vs IC §1

```text
src/jarvis/capabilities/
  crsf_dual_role.py    # NEW — CrsfDualRolePolicy + rc_channels_to_stub_frame + ingest_rc_channels
  crsf_stub.py           # byte-unchanged (confirmed via git diff) — reused, not rewritten
  radio.py                # byte-unchanged (confirmed via git diff)
  intent.py / safety.py    # byte-unchanged (confirmed via git diff)
  __init__.py               # docstring extended with a C20 pointer paragraph; no new top-level exports

tests/
  fixtures/crsf/             # REUSED from C19 (rc_channels_valid.bin, link_statistics_valid.bin) — no new binary fixture needed
  test_fase_c_crsf_dual_role_bridge_b1.py   # NEW
```

**Module choice (IC §10 "Cursor default: new thin `crsf_dual_role.py`"):** followed exactly — a new, separate file rather than extending `crsf_stub.py`.

No new binary fixture was needed for T4's "end-to-end from a C19 valid RC fixture" requirement — the IC's own §4 T4 offered a choice ("force one channel high in a synthetic/mutated payload **or** dedicated fixture"); this report documents the choice made: the real C19 `rc_channels_valid.bin` fixture is parsed and decoded first (proving the genuine C19→C20 pipeline), then a **mutated copy** of its decoded `CrsfRcChannels.channels` tuple (aux channel forced above threshold) is fed through the bridge — avoiding a fifth checked-in binary fixture for a single-bit-of-information variant.

---

## 2. Types / API implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| `CrsfDualRolePolicy` (`authority_channel_index`, `authority_threshold`, `authority_kind`) | §2.1 | ✅ Pydantic model, `extra="forbid"`; `authority_kind: Literal["kill"]` (the one locked kind); index validated `[0, 15]`, threshold validated `[0, 2047]` via `field_validator` |
| `rc_channels_to_stub_frame(channels, *, policy, frame_id=None) -> RadioStubFrame \| None` | §2.2 | ✅ returns `None` below threshold; `RadioStubFrame(role="authority", authority_kind=..., authority_payload=..., notes=...)` at/above threshold |
| `ingest_rc_channels(channels, *, policy, ingress=None) -> RadioDualRoleResult \| None` | §2.3 | ✅ builds the stub frame then calls `SimulatedRadioIngress.ingest(...)`; returns `None` when no frame was produced; accepts an explicit `ingress` instance or constructs a fresh one |
| Optional link-statistics enrichment (IC §0 decision 7) | §2.2 (extended) | ✅ `link_stats: CrsfLinkStatistics \| None` parameter on both public functions — folded into `RadioStubFrame.notes` only (`"link: lq=... rssi1=... snr=..."`), never changes whether Authority fires, never touches Safety |
| Non-goals (§2.4) | §2.4 | ✅ no `open_serial`, no byte-stream assembler, no mixer/ESC, no Safety calls, no Intent synthesis from sticks — confirmed absent by grep and direct module inspection in tests |

`rc_channels_to_stub_frame`'s `frame_id` parameter (optional) lets a caller pin `RadioStubFrame.id` for reproducible tests; when omitted, `RadioStubFrame`'s own `default_factory=uuid4` applies, matching C5's existing behavior.

**Not exported at the `jarvis.capabilities` package top level, deliberately** — same choice as C19's own `crsf_stub.py`: reachable via `from jarvis.capabilities.crsf_dual_role import ...`. `capabilities/__init__.py`'s docstring was extended with a C20 pointer paragraph; `__all__` is unchanged.

---

## 3. Policy defaults (IC §0 decision 5) — disclosed as illustrative, not sourced from any real hardware

```python
_DEFAULT_AUTHORITY_CHANNEL_INDEX = 4   # a common AUX1/arm-switch position in the CRSF/Betaflight convention
_DEFAULT_AUTHORITY_THRESHOLD = 1500    # well above CRSF mid (992) in the typical [172, 1811] calibrated range
_DEFAULT_AUTHORITY_KIND = "kill"       # the only kind this Buy supports
```

Both defaults are explicit module-level constants (not buried in a function signature) and are named/explained in `crsf_dual_role.py`'s own docstring and in this report — matching the IC's "defaults must be explicit constants in code + report."

---

## 4. Empirical verification (before formal tests)

```text
policy: authority_channel_index=4 authority_threshold=1500 authority_kind='kill'
below threshold frame: None
above threshold frame: id='...' role='authority' intent_text='' authority_kind='kill' authority_payload='crsf_aux_channel=4 value=1800' notes=None
ingest result: frame_id='...' intent=None authority=AuthoritySignal(id='...', source='radio', kind='kill', payload='crsf_aux_channel=4 value=1800')
ingest result low: None
channel index validation OK: ValidationError
threshold validation OK: ValidationError

# real C19 fixture end-to-end
rc channels from real fixture: (992, 992, ..., 992)   # all-neutral, confirmed below threshold -> None
enriched with link stats: id='...' role='authority' authority_kind='kill' authority_payload='crsf_aux_channel=4 value=1800' notes='link: lq=99 rssi1=80 snr=-42'
```

---

## 5. Tests (IC §4)

| ID | Check | Result |
|---|---|---|
| T1 | Channel ≥ threshold → `RadioStubFrame` role=`authority`, kind=`kill` | ✅ `test_t1_channel_at_or_above_threshold_gives_authority_kill_frame` (includes exact-threshold boundary) |
| T2 | Channel < threshold → `None` (no frame) | ✅ `test_t2_channel_below_threshold_gives_none` |
| T3 | Optional ingest helper → `RadioDualRoleResult` with `AuthoritySignal` source `radio`; intent `None` | ✅ `test_t3_ingest_helper_returns_dual_role_result_with_radio_authority_and_no_intent` (+ `test_t3b_...` for the below-threshold `None` case, `test_t3c_...` for the explicit-`ingress` path) |
| T4 | End-to-end from C19 valid RC fixture: parse → decode → bridge (mutated payload) | ✅ `test_t4_end_to_end_from_c19_fixture_parse_decode_bridge` (also exercises link-statistics enrichment end-to-end from the real `link_statistics_valid.bin` fixture) |
| T5 | No I/O imports / device `open(` in bridge module real code | ✅ `test_t5_module_under_test_has_no_io_imports_or_device_open` (docstrings/comments stripped via `tokenize`, same pattern established in C19) |
| T6 | `RadioIntentAdapter` still `not_implemented` | ✅ `test_t6_radio_intent_adapter_still_raises_not_implemented` (including fed a real bridge-produced `RadioStubFrame` — still refuses) |
| T7 | C5 T5: `radio.py` has no `decode_crsf`/`decode_elrs`/`open_serial`/`write_pwm` | ✅ `test_t7_radio_py_still_has_no_public_decode_or_serial_symbols` |
| T8 | Bridge does not call `submit_command` / import autonomy surface | ✅ `test_t8_bridge_never_calls_submit_command_or_imports_autonomy` |
| T9 | `default_safety_gate()` still RejectAll; `ArmedAllowlist` unchanged | ✅ `test_t9_default_safety_gate_still_reject_all_and_armed_allowlist_unchanged` |
| T10 | `pyproject` `0.5.18`; re-pin `0.5.17` checkpoints | ✅ §6 below |
| T11 | Full suite green | ✅ **3444 passed, 1 skipped** (was 3428 — exact +16 delta) |
| T12 | Report: bridge ≠ live ELRS ≠ Safety allow | ✅ §0 above |

New Python test module `tests/test_fase_c_crsf_dual_role_bridge_b1.py` — **16 tests**, all passing:

```text
test_t1_channel_at_or_above_threshold_gives_authority_kill_frame PASSED
test_t2_channel_below_threshold_gives_none PASSED
test_t3_ingest_helper_returns_dual_role_result_with_radio_authority_and_no_intent PASSED
test_t3b_ingest_helper_returns_none_when_below_threshold PASSED
test_t3c_ingest_helper_accepts_explicit_ingress_instance PASSED
test_t4_end_to_end_from_c19_fixture_parse_decode_bridge PASSED
test_t5_module_under_test_has_no_io_imports_or_device_open PASSED
test_t6_radio_intent_adapter_still_raises_not_implemented PASSED
test_t7_radio_py_still_has_no_public_decode_or_serial_symbols PASSED
test_t8_bridge_never_calls_submit_command_or_imports_autonomy PASSED
test_t9_default_safety_gate_still_reject_all_and_armed_allowlist_unchanged PASSED
test_authority_from_bridge_never_flips_safety PASSED
test_policy_validates_channel_index_and_threshold_ranges PASSED
test_no_crsf_or_elrs_under_native_and_no_craft_wiring PASSED
test_capability_registry_default_still_empty PASSED
test_t10_pyproject_version_is_0_5_18 PASSED
```

**Honesty-test hygiene applied from the start (no false positives this time, disclosed for continuity):** the comment/docstring-stripping helper (`_strip_python_comments_and_docstrings`, `tokenize`-based) that had to be introduced reactively in C19 after two false-positive failures was written into this Buy's test module from the outset, anticipating that `crsf_dual_role.py`'s own honesty-prose docstring would otherwise trip a naive substring check (it names `submit_command`, `usb`, etc. to disclose their absence, exactly like C19's module did). Both T5 and T8 used it directly; both passed on the first run.

**T11 (full suite):** `pytest -q` — **3444 passed, 1 skipped** (baseline before this Buy was 3428 passed, 1 skipped; delta is exactly the 16 new tests, no other file's pass/fail count moved; the one skip is unrelated/pre-existing).

Twenty-five pre-existing test files hardcoded the prior checkpoint version string (`"0.5.17"`) as a version-pin assertion, including C19's own test module. Since this IC explicitly requires the `0.5.18` bump (§0 decision 13), all twenty-five were re-pinned to `"0.5.18"`:

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
| Serial/USB RX as acceptance | ✅ absent | T5 — no `serial`/`socket`/`pty`/`subprocess`/`open(` in real code |
| Claiming pilot sticks control craft | ✅ absent | No mixer/ESC path anywhere; module docstring + this report state the opposite |
| Authority → Safety `allow` | ✅ absent | `test_authority_from_bridge_never_flips_safety` — wiring the bridge's own `AuthoritySignal.id` into a `SafetyRequest` still yields `reject` on both `RejectAllSafetyGate` and armed `ArmedAllowlistSafetyGate` |
| Auto `submit_command` from bridge | ✅ absent | T8 — module has no `submit_command`/`propose_command` attribute and no `flight_software` import |
| Decode APIs on `radio.py` | ✅ absent | T7 + `git diff --stat radio.py` empty |
| Stream reassembly / UART reader | ✅ absent | No such code anywhere in `crsf_dual_role.py`; explicitly out of scope per IC §0 decision 2 |
| Marking radio `available` in registry | ✅ absent | `CapabilityRegistry.load_default()` re-confirmed empty |

**"One front" discipline (process lock after C6):** this Buy stayed exactly within the CRSF→dual-role bridge scope. No serial/UART open, stream reassembly, GPIO, flash, craft↔FS wiring, Safety policy edits, or mixer/ESC were touched or opened.

---

## 7. Integration rules (IC §3) — confirmed unchanged

- C19 `parse_crsf_frame`/decode functions — reused via import, not rewritten; `crsf_stub.py` byte-unchanged.
- C5 `radio.py` — no new `decode_*`/`open_serial`/`write_pwm`; byte-unchanged.
- C2 `RadioIntentAdapter` — still refuses, re-verified with a real bridge-produced frame as input.
- C4 autonomy — no bridge → `submit_command` path exists anywhere (T8).
- C17 Safety — untouched; default stays `RejectAllSafetyGate`; `ArmedAllowlistSafetyGate` behavior re-verified identical, including the Authority-does-not-flip-allow case explicitly for this Buy's own output.
- Registry — default stays empty.

---

## 8. Files changed

**New:**
- `src/jarvis/capabilities/crsf_dual_role.py`
- `tests/test_fase_c_crsf_dual_role_bridge_b1.py`
- `.jes/artifacts/implementation_report_fase_c_crsf_dual_role_bridge_b1.md` (this file)

**Modified:**
- `pyproject.toml` — version `0.5.17` → `0.5.18`
- `src/jarvis/capabilities/__init__.py` — docstring extended with a C20 pointer paragraph; `__all__`/imports unchanged (deliberately not exported at package top level, same choice as C19)
- `docs/ARCHITECTURE.md`, `docs/PLATFORM_CAPABILITY_VISION.md`, `docs/IMPLEMENTATION_TASKS.md`, `README.md` — C20 sections (see §9)
- 25 test files — re-pinned stale `0.5.17` version-checkpoint assertions to `0.5.18`

**Not touched (confirmed):** `orchestrator.py`, Board (`ui/spatial-board/`), `library/`, `native/flight_control/**` (zero CRSF/ELRS references), `src/jarvis/capabilities/crsf_stub.py`, `src/jarvis/capabilities/radio.py`, `src/jarvis/capabilities/intent.py`, `src/jarvis/capabilities/safety.py`, `src/jarvis/flight_software/**`, `.jes/state/engineering_state.json`.

---

## 9. Docs honesty confirmation (IC §6)

- README header banner: "v0.5.17 tagged tip · working tree ahead toward v0.5.18 (C20 ... awaiting Cursor review + Engineer ACCEPT)" — no premature tag claim.
- `docs/IMPLEMENTATION_TASKS.md` PRIORIDAD banner and C20 row: "landed — awaiting Cursor review + ★ ACCEPT ... tag not on git yet".
- `docs/ARCHITECTURE.md` — new short note under capabilities: bridge ≠ pilot link ≠ Safety allow.
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C20 block with honesty line.
- Confirmed via `git tag -l | sort -V`: latest Fase C tag is `v0.5.17` (C19); no `v0.5.18` tag exists.
- Explicit **exists vs. impossible** statement, present in README/ARCHITECTURE/PLATFORM_CAPABILITY_VISION: **exists** = a deterministic bridge from decoded CRSF RC channels into a typed dual-role Authority frame, under one documented policy; **impossible** = a live ExpressLRS link, a receiver "connected," pilot sticks driving anything, Authority opening Safety.

---

## 10. Residual — what comes next

Per this IC's own §8 handoff: still one front at a time, Engineer-prioritized — a UART byte-stream assembler (separate Buy), deepening the bridge policy (more channels, configurable Authority kinds), actual board bring-up/flash, or craft↔FS wiring. Not decided here.

---

## 11. Acceptance self-check against IC §7

- T1–T12: ✅ (see §5 table)
- Threshold policy works: ✅ (§4, T1/T2)
- Ingest optional path typed: ✅ (§4, T3)
- C5/C19 locks hold: ✅ (§0, §6, §7 — byte-diff confirmed)
- Safety default unchanged: ✅ (§6, T9, plus the explicit Authority-never-flips-allow test)
- Version `0.5.18`: ✅
- Docs honest: ✅ (§9)
- Not FAIL conditions: no serial product (§6) · no Safety allow via Authority anywhere (§6) · no CRSF→autonomy execution (§6, T8) · decode not stuffed into `radio.py` (§6, T7) · no Intent invented from sticks (§0, §2 — Authority-only, locked)
