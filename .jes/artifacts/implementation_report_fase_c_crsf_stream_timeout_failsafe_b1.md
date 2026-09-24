# Implementation Report — Fase C CRSF stream-timeout failsafe (`B1-fase-c-crsf-stream-timeout-failsafe`)

**IC:** [`implementation_contract_fase_c_crsf_stream_timeout_failsafe_b1.md`](implementation_contract_fase_c_crsf_stream_timeout_failsafe_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-24
**Status:** ★ ACCEPT CLOSED @ **`v0.5.25`** (Cursor review PASS WITH NOTES). Package **`0.5.25`**.

---

## 0. Read this first — honesty summary

This Buy adds **no motors cut, no live radio, no Safety execute**. It
names an **age watch**: if a valid RC-channels frame has not been
**noted** within a documented timeout (default `0.5` s), the last stick
values stop being treated as live. `CrsfRcHoldWatch` (Python,
`capabilities/crsf_failsafe.py`) and `RcHoldWatch` (protocol-agnostic
C++, `native/flight_control/`) hold **one timestamp**, nothing about
channel values — `note_rc(now_s)` records it, `evaluate(now_s)`/
`is_stale(now_s)` compare it against `timeout_s`. Nothing here parses
bytes, decodes CRSF, or reimplements C21's `feed()`; C20's `kill`
policy, C25's `map_rc_to_loop_inputs`, and C26's `EscOutput` are all
untouched.

**Timeout failsafe != motors cut != live ELRS != Safety allow.**

**Exists:** an age watch; after `0.5` s without a noted RC sample,
sticks are not "live"; the recommended inputs are level attitude plus
zero collective. **Impossible:** a radio that cuts ESCs; ExpressLRS
failsafe as a shipped product; Safety opening on timeout. Nothing in
this Buy is any of those.

---

## 1. Package layout vs IC §1

```text
src/jarvis/capabilities/
  crsf_failsafe.py     # NEW
  crsf_stream.py       # UNCHANGED (git diff --stat empty)

native/flight_control/
  include/jarvis/fc/rc_hold.hpp   # NEW — protocol-agnostic
  src/rc_hold.cpp                  # NEW — added to jarvis_fc
  tests/test_rc_hold.cpp           # NEW Catch2 cases (6)

tests/
  test_fase_c_crsf_stream_timeout_failsafe_b1.py   # NEW — 19 tests
```

`crsf_failsafe.py` lives under `capabilities/`, not folded into `radio.py` (`git diff --stat` empty, confirmed §8). The C++ twin is a new pair of files, not a rewrite of anything in C21-C26's own trees.

---

## 2. Types / API implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| `CRSF_RC_STALE_S = 0.5` (Python) / `kRcHoldTimeoutS = 0.5` (C++) | §2 | ✅ Python name matches the IC exactly (capabilities/ allowed to name the protocol); C++ name protocol-agnostic per IC §1's own lock |
| `RcHoldDecision { stale, reason, age_s }` | §2 | ✅ Pydantic `BaseModel` (Python, `reason: Literal["fresh","never","timeout"]`) / plain struct with `std::string reason` (C++, matching `EscApplyResult`'s own established `reason`-field idiom in this tree) |
| `CrsfRcHoldWatch`/`RcHoldWatch.__init__(timeout_s=0.5)` | §2 | ✅ both languages; rejects non-finite/non-positive `timeout_s` |
| `note_rc(now_s) -> None` | §2 | ✅ pure bookkeeping — records `now_s`, no parsing |
| `is_stale(now_s) -> bool` / `evaluate(now_s) -> RcHoldDecision` | §2 | ✅ stale if never noted (`"never"`) or `now_s - last_s > timeout_s` (`"timeout"`); `now_s < last_s` raises `ValueError`/`std::invalid_argument` |
| `failsafe_loop_inputs(t_s) -> RcLoopInputs` | §2 | ✅ `level_setpoint(t_s)` + `collective=0.0`, both languages |

### 2.1 Non-goals (IC §2.1) — confirmed absent

No GPIO, DShot, `EscOutput.apply`, `step` auto-call, C20 policy change, C21 resync rewrite, live RX, `time.time()` as SoT, Safety execute — confirmed by grep (§8) and by `test_t8_loop_and_esc_apply_paths_unchanged_no_timeout_wiring` / `test_crsf_failsafe_not_on_radio_py_and_no_serial_baud_imports` / `test_feed_and_note_rc_never_calls_ingest_stream_bytes`.

---

## 3. The lock boundary (`age_s <= timeout_s` is fresh) — verified empirically

```text
default timeout: 0.5
never: stale=True reason='never' age_s=None
at boundary (age==timeout): stale=False reason='fresh' age_s=0.5
just over boundary: stale=True reason='timeout' age_s=0.5000000010000001
T3: stale=True reason='timeout' age_s=0.500000001
backwards raised: now_s must not precede the last noted time
failsafe inputs: setpoint=AttitudeSetpoint(t_s=3.0, q_body_to_world_desired=(1.0, 0.0, 0.0, 0.0), frame='enu') collective=0.0
frames decoded: 1 noted: stale=False reason='fresh' age_s=0.0
zero timeout raised: timeout_s must be finite and > 0
```

Exact equality at the boundary (`age_s == timeout_s`) resolves **fresh**, matching IC T2's own explicit lock ("age <= timeout is fresh; age > timeout is stale"). Verified in both languages (Python script above; C++ Catch2 case `"RcHoldWatch: fresh at and before the timeout boundary"`).

---

## 4. A real native-tree lock violation, caught and fixed mid-Buy

My first draft of `rc_hold.hpp`'s own top comment named the Buy ID (`B1-fase-c-crsf-stream-timeout-failsafe`) and the Python module path (`capabilities/crsf_failsafe.py`) verbatim — both contain the substring "crsf", which trips the C21-C26 native-tree lock (`grep -rin "crsf|elrs" native/` must return nothing, tree-wide, even in comments). Caught by re-running that exact grep before moving on (not by a failing test — I ran the check proactively, the same habit every prior CRSF-adjacent Buy in this thread used). Fixed by rewriting the header comment to describe the Python twin generically ("a Python capability module under `capabilities/` that names the radio link protocol this stays deliberately agnostic to — see this Buy's own IC/report for that name") instead of naming the file or Buy ID. Re-verified: `grep -rin "crsf|elrs" native/` returns zero matches tree-wide after the fix, and the C++ build/tests were re-run clean afterward (§6.3).

---

## 5. Integration rules vs IC §3

| Existing | This Buy |
|---|---|
| C21 `feed()` | **Unchanged** (`crsf_stream.py` `git diff --stat` empty). The optional `feed_and_note_rc(...)` helper in the new module calls `assembler.feed(data)` — C21's own method — directly, and never calls `ingest_stream_bytes` at all, so C21's own default helper's behavior is untouched (`test_feed_and_note_rc_never_calls_ingest_stream_bytes`). |
| C25 mapper | Untouched (`rc_setpoint.py`/`.hpp`/`.cpp` all `git diff --stat` empty); used only when the watch says fresh — this module never remaps sticks itself. |
| C26 `EscOutput` | Untouched (`esc.py`/`.hpp`/`.cpp` all `git diff --stat` empty); this Buy never calls `apply`/`apply_forces`. |
| C20 | Unchanged (`crsf_dual_role.py` `git diff --stat` empty); `CrsfDualRolePolicy()` defaults re-verified (`authority_channel_index == 4`, `authority_threshold == 1500`, `authority_kind == "kill"`); `feed_and_note_rc` notes on raw `0x16` arrival, independent of C20's own aux-channel Authority threshold — these are different questions, and this Buy does not conflate them. |
| C5 `radio.py` | No failsafe API added — `git diff --stat` empty, confirmed by grep (no `CrsfRcHoldWatch`/`note_rc`/`failsafe_loop_inputs` in `radio.py`). |
| C17 | Untouched (`safety.py` `git diff --stat` empty). |

---

## 6. Tests run

### 6.1 Python — new module

`tests/test_fase_c_crsf_stream_timeout_failsafe_b1.py` — **19 tests**, covering IC §4's T1-T8 and T10-T11 (T9 is the C++ Catch2 case, T12 is this report):

| Test | Covers |
|---|---|
| `test_t1_never_noted_is_stale_with_reason_never` | T1 |
| `test_t2_fresh_at_and_before_the_timeout_boundary` | T2 |
| `test_t3_stale_with_reason_timeout_just_past_the_boundary` | T3 |
| `test_t4_failsafe_loop_inputs_near_identity_quat_and_zero_collective` | T4 |
| `test_t5_c21_feed_has_no_note_rc_coupling` | T5 (source-level half; "tests still pass" is the full-suite run below) |
| `test_t6_radio_py_still_has_no_decode_or_failsafe_and_c20_policy_unchanged` | T6 |
| `test_t7_radio_intent_adapter_not_implemented_and_rejectall_default` | T7 |
| `test_t8_loop_and_esc_apply_paths_unchanged_no_timeout_wiring` | T8 |
| `test_t10_pyproject_version_is_0_5_25` | T10 |
| `test_t11_full_suite_process_gate_placeholder` | T11 marker (real gate is the full-suite run below) |
| `test_native_tree_still_zero_crsf_elrs_tokens` | native-grep half of T9 |
| `test_now_s_before_last_noted_raises` | decision 6 typed-error path |
| `test_non_positive_timeout_rejected` | constructor validation |
| `test_feed_and_note_rc_notes_on_valid_rc_channels_frame` | glue helper, positive path |
| `test_feed_and_note_rc_does_not_note_on_non_rc_frame` | glue helper, negative path (link-stats frame) |
| `test_feed_and_note_rc_never_calls_ingest_stream_bytes` | decision 9 |
| `test_crsf_failsafe_not_on_radio_py_and_no_serial_baud_imports` | module placement + no serial/baud coupling |
| `test_no_craft_or_core_imports_and_registry_still_empty` | craft/registry isolation |
| `test_default_timeout_constant_is_half_second` | constant sanity |

```text
tests/test_fase_c_crsf_stream_timeout_failsafe_b1.py: 19 passed
```

### 6.2 Full Python suite

```text
3572 passed, 2 skipped in 6.20s
```

Baseline before this Buy: `3553 passed, 2 skipped`. Delta: **+19**, exactly matching the new test count — zero regressions, including `test_fase_c_crsf_byte_stream_b1.py` (C21's own assembler tests) which ran unmodified as part of this suite.

### 6.3 C++ — new Catch2 cases + full host `ctest`

`native/flight_control/tests/test_rc_hold.cpp` — 6 new `TEST_CASE`s:

1. `RcHoldWatch: never noted is stale with reason=never` (IC T1/T9)
2. `RcHoldWatch: fresh at and before the timeout boundary` (IC T2/T9)
3. `RcHoldWatch: stale with reason=timeout just past the boundary` (IC T3/T9)
4. `RcHoldWatch: rejects now_s before the last noted time`
5. `RcHoldWatch: rejects non-positive timeout_s`
6. `failsafe_loop_inputs: level quat and zero collective` (IC T4)

```text
$ cmake --build build/flight_control -j4     # clean build, zero warnings
$ ctest
100% tests passed out of 45

Total Test time (real) = 0.68 sec
```

Baseline before this Buy: 39 host tests. Delta: **+6**, exactly the new `TEST_CASE` count. `fc_closed_loop_smoke` and `fc_esc_pwm_smoke` both still pass.

### 6.4 MCU cross-compile re-verification (not required by IC §4, done for completeness)

```text
$ export PATH="/private/tmp/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin:$PATH"
$ cmake --build build/flight_control_mcu -j4
[  6%] Building CXX object CMakeFiles/jarvis_fc.dir/src/rc_hold.cpp.obj
[ 13%] Linking CXX static library libjarvis_fc.a
[100%] Built target fc_mcu_stub.elf
```

`rc_hold.cpp` compiles cleanly for the ARM cross target alongside every other rung. `stub_main.cpp` was not touched (`git diff --stat` empty) and still never references `RcHoldWatch`/`note_rc`/`failsafe`.

---

## 7. Honesty / forbidden — confirmed

| Forbidden (IC §5) | Verified absent |
|---|---|
| "ELRS failsafe" (as a product) | Not claimed — this module tracks age only, no link/RF concept exists here |
| "motors cut on timeout" | Not claimed — `failsafe_loop_inputs` returns argument values only, never calls `EscOutput`/`apply`/`apply_forces` |
| Safety allow | Not touched — `crsf_failsafe.py`/`rc_hold.hpp`/`.cpp` never reference `SafetyGate`/`submit_command`/`propose_command` |
| Last sticks stay live after timeout | Not the case — `evaluate`/`is_stale` correctly flip to stale past `timeout_s`, verified at and past the exact boundary |
| UART driver | Not present — no I/O, no serial, no baud anywhere in this Buy |

Honesty line, shipped verbatim in this report and in the docs updated below:

```text
timeout failsafe != motors cut != live ELRS != Safety allow
```

---

## 8. Module-boundary / forbidden-symbol grep (run at close of this Buy)

```text
$ git diff --stat -- src/jarvis/capabilities/radio.py src/jarvis/capabilities/crsf_stream.py \
    src/jarvis/capabilities/crsf_dual_role.py src/jarvis/capabilities/crsf_stub.py \
    src/jarvis/capabilities/intent.py src/jarvis/capabilities/safety.py \
    src/jarvis/flight_software/autonomy/ native/flight_control/mcu/ \
    src/jarvis/flight_software/flight_control/loop.py native/flight_control/include/jarvis/fc/loop.hpp native/flight_control/src/loop.cpp \
    src/jarvis/flight_software/flight_control/rc_setpoint.py native/flight_control/include/jarvis/fc/rc_setpoint.hpp native/flight_control/src/rc_setpoint.cpp \
    src/jarvis/flight_software/flight_control/esc.py native/flight_control/include/jarvis/fc/esc.hpp native/flight_control/src/esc.cpp
(empty)

$ grep -n "Reset_Handler\|CrsfRcHoldWatch\|RcHoldWatch\|failsafe" native/flight_control/mcu/stub_main.cpp
# no match (exit 1)

$ grep -rin "crsf\|elrs" native/
# no match (exit 1) — the C21-C26 native-tree lock holds, including for this Buy's own new files (after the §4 fix)
```

`git status --short` at close of this Buy shows exactly the expected file set: `crsf_failsafe.py`, `rc_hold.hpp`, `rc_hold.cpp`, `test_rc_hold.cpp`, `test_fase_c_crsf_stream_timeout_failsafe_b1.py` (new), `CMakeLists.txt` (modified to register the two new files), plus `pyproject.toml` + version-checkpoint test re-pins + docs. No `radio.py`, `crsf_stream.py`, `crsf_dual_role.py`, `crsf_stub.py`, `intent.py`, `safety.py`, `autonomy/`, `mcu/`, `loop.{py,hpp,cpp}`, `rc_setpoint.{py,hpp,cpp}`, or `esc.{py,hpp,cpp}` files touched.

---

## 9. Files changed

**New:**
- `src/jarvis/capabilities/crsf_failsafe.py`
- `native/flight_control/include/jarvis/fc/rc_hold.hpp`
- `native/flight_control/src/rc_hold.cpp`
- `native/flight_control/tests/test_rc_hold.cpp`
- `tests/test_fase_c_crsf_stream_timeout_failsafe_b1.py`
- `.jes/artifacts/implementation_report_fase_c_crsf_stream_timeout_failsafe_b1.md` (this file)

**Modified:**
- `native/flight_control/CMakeLists.txt` (`src/rc_hold.cpp` added to `jarvis_fc`; `tests/test_rc_hold.cpp` added to `fc_unit_tests`)
- `native/flight_control/README.md` (Layout + a new C27 paragraph, protocol-agnostic)
- `pyproject.toml` (`0.5.24` → `0.5.25`)
- ~30 pre-existing test files re-pinned from `0.5.24` to `0.5.25` (literal `'version = "X.Y.Z"' in text` pattern)
- `README.md`, `docs/ARCHITECTURE.md` (new §1j), `docs/PLATFORM_CAPABILITY_VISION.md`, `docs/IMPLEMENTATION_TASKS.md` (see §10)

---

## 10. Docs updated (honesty confirmed — not claiming CLOSED/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.25 includes (working tree — not yet tagged)" section, explicitly says "no `v0.5.25` tag yet."
- `docs/ARCHITECTURE.md` — new §1j (`capabilities/crsf_failsafe.py`), top banner updated to "Working tree ahead: package `0.5.25` ... awaiting Cursor review + Engineer ★ ACCEPT — no `v0.5.25` tag yet."
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C27 block, same "landed — awaiting ... no tag yet" phrasing, honesty line verbatim.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner and the C27 table row both changed to "Landed — awaiting Cursor review + ★ ACCEPT (no `v0.5.25` tag yet)."
- `native/flight_control/README.md` — Layout section + new paragraph on `rc_hold.hpp`/`rc_hold.cpp`, written protocol-agnostically (native-tree lock).

No file in this Buy claims `v0.5.25` is tagged or ACCEPT CLOSED. Confirmed via `git tag -l | sort -V | tail -3` at close of this Buy: `v0.5.22`, `v0.5.23`, `v0.5.24` — `v0.5.25` does not exist yet.

---

## 11. Residual / next steps

- C28 (MCU UART HAL stub) is next in the parked queue, per the IC's own handoff — explicitly **not** started here.
- C29 (silicon + cited FLASH map) remains parked, untouched.
- Neither `run_controlled_flight_sim_smoke` nor `fc_closed_loop_smoke` was wired to this watch — the IC did not ask for that, and doing so would have coupled a sim-loop smoke to a failsafe concept outside this Buy's own scope.
- The §4 native-tree lock catch (comment-only violation, fixed before any test run flagged it) should be flagged to Cursor/Engineer during review as a proactive self-check, not a test failure — disclosed here for transparency.

---

## 12. Acceptance self-check vs IC §7

- T1-T8, T10-T11 (Python): ✅ all pass, 19/19 new tests green.
- T9 (C++ Catch2 + native grep): ✅ 6 new cases pass; native-tree grep zero matches.
- T11 (full suite + `ctest` green): ✅ `3572 passed, 2 skipped` (Python); `45/45` (`ctest`).
- T12 (this report's honesty content): ✅ this section.
- Watch only (no second AETR map): ✅ `map_rc_to_loop_inputs` never called from `crsf_failsafe.py`.
- C21/C20/C25/C26 frozen: ✅ `git diff --stat` empty on all five; policy defaults re-verified.
- No GPIO: ✅ grep clean.
- Version `0.5.25`: ✅ `pyproject.toml` + all checkpoint tests re-pinned.

**PASS** against every criterion in IC §7. **FAIL conditions** (last sticks staying live after timeout, GPIO claimed, Safety execute, `time.time()` as SoT, `radio.py` growing decode, native CRSF tokens) — none present, verified above.
