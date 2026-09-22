# Implementation Report — Fase C RC → setpoint (`B1-fase-c-rc-setpoint`)

**IC:** [`implementation_contract_fase_c_rc_setpoint_b1.md`](implementation_contract_fase_c_rc_setpoint_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-22
**Status:** ★ ACCEPT CLOSED @ **`v0.5.23`** (Cursor review PASS WITH NOTES). Package **`0.5.23`**.

---

## 0. Read this first — honesty summary

This Buy adds **no motors, no execution, no live radio**. It maps
already-decoded RC channel *units* (16 ints in `[0, 2047]`, C19's own
`CrsfRcChannels` shape, or any equivalent `>= 4`-int sequence) onto the
two arguments C24's `FlightControlLoop.step`/`ControlLoop::step` already
accept: `AttitudeSetpoint` and `collective`. No CRSF frame parsing
happens here — that stays C19's job (`crsf_stub.py`); this module only
converts integers that are already decoded.

**RC->setpoint != flying != sticks drive motors != Safety allow != yaw
lock.**

**Exists:** a documented, illustrative AETR (Aileron/Elevator/Throttle/
Rudder) map from channel units to `AttitudeSetpoint` + `collective`, in
Python and C++, plus an optional thin helper that also calls C24's own
`step`. **Impossible:** a pilot flying the craft; a motor spinning; a
failsafe; heading-hold yaw. Nothing in this Buy is any of those.

---

## 1. Package layout vs IC §1

```text
src/jarvis/flight_software/flight_control/
  rc_setpoint.py           # NEW
  loop.py                  # UNCHANGED (git diff --stat empty)

native/flight_control/
  include/jarvis/fc/rc_setpoint.hpp   # NEW
  src/rc_setpoint.cpp                  # NEW — added to jarvis_fc
  tests/test_rc_setpoint.cpp           # NEW Catch2 cases (5)

tests/
  test_fase_c_rc_setpoint_b1.py        # NEW — 18 tests
```

`rc_setpoint.py` lives under `flight_control/`, not `capabilities/` (matching C24's own `loop.py` placement, and the IC's explicit instruction not to put stick math on `radio.py`). `radio.py` was not touched at all (`git diff --stat` empty, confirmed §7).

---

## 2. Types / API implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| `RC_CH_ROLL`, `RC_CH_PITCH`, `RC_CH_THROTTLE` = `0`, `1`, `2` | §2 | ✅ both languages |
| `CRSF_CH_MIN`, `CRSF_CH_MID`, `CRSF_CH_MAX` = `172`, `992`, `1811` | §2 | ✅ Python names match the IC exactly. **C++ deviation, disclosed:** named `kRcChMin`/`kRcChMid`/`kRcChMax` instead — see §2.2 below for why. |
| `RC_MAX_TILT_RAD` = `π/6` | §2 | ✅ both languages |
| `RcLoopInputs { setpoint: AttitudeSetpoint; collective: float }` | §2 | ✅ Pydantic `BaseModel` (Python, with a defensive finite/`[0,1]` re-check field validator) / plain struct (C++) |
| `map_rc_to_loop_inputs(channels, *, t_s: float) -> RcLoopInputs` | §2 | ✅ exact Python signature; C++ signature `map_rc_to_loop_inputs(const std::vector<int>&, double t_s)` |
| Invalid length / non-int → typed error | §2 | ✅ Python: `ValueError` for `len < 4` or a non-`int`/`bool` value at indices 0-2; C++: `std::invalid_argument` for `channels.size() < 4` |

### 2.1 Explicit non-goals (IC §2.1) — confirmed absent

No plant, GPIO, DShot, failsafe timer, yaw-stick mapping, C20 policy change, Safety, Intent from sticks, `/dev` scan, live RX — confirmed by grep (§7) and by `test_t5_step_with_rc_produces_four_finite_forces_no_plant_no_gpio` / `test_t6_radio_py_still_has_no_decode_or_serial_and_c20_policy_unchanged`.

### 2.2 Naming deviation, disclosed (IC §2 is "normative intent," not letter-locked)

The IC's own §2 pseudocode names the C++ constants identically to the Python ones (`CRSF_CH_MIN`/`CRSF_CH_MID`/`CRSF_CH_MAX`). While implementing, the full-suite run surfaced a **pre-existing, established lock** from C19-C23's own test files: every one of them asserts `"crsf" not in text.lower()` and `"elrs" not in text.lower()` across **every file under `native/`**, comments included — a hard "one front" boundary keeping the C++ tree protocol-agnostic (CRSF/ELRS parsing stays a Python-only capability). Naming a C++ constant `kCrsfChMin` (or writing "CRSF" in a C++ comment) trips that lock. Since IC §2 is explicitly marked "normative intent" (same phrasing C24's own IC used for its own type names, where the report was told to "list them" rather than match verbatim), I renamed the C++-side constants to `kRcChMin`/`kRcChMid`/`kRcChMax` — same values (`172`/`992`/`1811`), same meaning, no protocol name — and rewrote every C++ comment that had named "CRSF" to describe the convention without naming the protocol. This is disclosed here per the IC's own "report must list them" pattern; the **values and behavior are identical**, only the C++-side identifier/prose changed. Confirmed via full-suite re-run after the rename: `3538 passed, 2 skipped`, and `grep -rin "crsf|elrs" native/` returns zero matches tree-wide.

---

## 3. The math (both languages, verified identical)

**Throttle → collective:** `frac = (ch - CRSF_CH_MIN) / (CRSF_CH_MAX - CRSF_CH_MIN)`, clipped to `[0, 1]`. At `172` → `0.0` exactly; at `1811` → `1.0` exactly; at mid `992` → `(992-172)/(1811-172) = 820/1639 ≈ 0.5003050640634533` — **not** `0.5`, documented rather than rounded.

**Roll/pitch → Euler angle:** deflection measured from `992`, using the *appropriate* half-span depending on side (`1811-992=819` above mid, `992-172=820` below mid — the CRSF-style convention is not perfectly symmetric), scaled to reach exactly `RC_MAX_TILT_RAD` (`π/6`) at either endpoint, clipped beyond it:

```python
if ch >= MID:
    frac = (ch - MID) / (MAX - MID)
else:
    frac = (ch - MID) / (MID - MIN)
frac_clipped = clip(frac, -1, 1)
angle = frac_clipped * RC_MAX_TILT_RAD
```

At `ch = 992` (either axis): `frac = 0` exactly → `angle = 0` exactly (verified empirically: quaternion is exactly `(1.0, 0.0, 0.0, -0.0)`). At `ch = 1811`: `frac = 1` exactly → `angle = 30°` exactly. At `ch = 172`: `frac = -1` exactly → `angle = -30°` exactly. Beyond either endpoint (e.g. `ch = 2047`, the 11-bit max), `frac` clips to `±1` — same quaternion as the endpoint, verified bit-identical in both the Python and C++ test suites.

**Euler → quaternion (yaw = 0):** standard body 3-2-1 (yaw-pitch-roll) composition, yaw fixed at identity:

```text
qw = cos(pitch/2) * cos(roll/2)
qx = cos(pitch/2) * sin(roll/2)
qy = sin(pitch/2) * cos(roll/2)
qz = -sin(pitch/2) * sin(roll/2)
```

This is the product of two unit quaternions (a pitch-only rotation about body Y, then a roll-only rotation about body X), so it is unit-norm by construction — verified empirically, no defensive re-normalization needed (matching `AttitudeSetpoint`'s own lack of a norm field-validator, unchanged since C8).

**Empirical verification (before any formal test), Python:**

```text
mid quat: (1.0, 0.0, 0.0, -0.0) collective: 0.5003050640634533
roll max quat: (0.9659258262890683, 0.25881904510252074, 0.0, -0.0) approx roll deg: 29.999999999999996
roll min quat: (0.9659258262890683, -0.25881904510252074, 0.0, 0.0)
roll beyond-max quat: (0.9659258262890683, 0.25881904510252074, 0.0, -0.0)   # clipped, identical to roll-max
throttle min collective: 0.0
throttle max collective: 1.0
yaw invariant: True True
CrsfRcChannels input ok: 0.5003050640634533
step_with_rc forces: (0.3450136370019409, 0.6555964911249658, 0.6555964911249658, 0.3450136370019409)
short-length raised: channels must have at least 4 entries (AETR-shaped), got 2
non-int raised: channels[2] must be int, got 'x'
```

All match the IC's own §0 decisions 5-7 exactly.

---

## 4. Integration rules vs IC §3

| Existing | This Buy |
|---|---|
| C24 `step` | **Called only** by the optional `step_with_rc` helper — the mapper itself (`map_rc_to_loop_inputs`) never touches `FlightControlLoop`/`ControlLoop` at all. `loop.py`/`loop.hpp`/`loop.cpp` are `git diff --stat` **empty**. |
| C19 channels | `CrsfRcChannels` (C19's own type) is accepted directly and read via its `.channels` tuple — no frame is re-parsed, no second CRC/envelope logic exists here. |
| C20 | Untouched (`crsf_dual_role.py` `git diff --stat` empty); `CrsfDualRolePolicy()` defaults re-verified unchanged (`authority_channel_index == 4`, `authority_threshold == 1500`, `authority_kind == "kill"`); this module never imports `crsf_dual_role.py`. |
| C11 smoke | Left on `level_setpoint` — not required to switch to RC this Buy, and it did not. |
| C5 `radio.py` | No stick API added — `git diff --stat` empty, confirmed by grep (no `map_rc_to_loop_inputs`, no `decode_crsf`, no `open_serial` in `radio.py`). |
| C17 | Untouched (`safety.py` `git diff --stat` empty). |

---

## 5. Tests run

### 5.1 Python — new module

`tests/test_fase_c_rc_setpoint_b1.py` — **18 tests**, covering IC §4's T1-T8 and T10-T11 (T9 is the C++ Catch2 case, T12 is this report):

| Test | Covers |
|---|---|
| `test_t1_all_mid_gives_near_zero_roll_pitch_and_finite_collective` | T1 |
| `test_t2_roll_and_pitch_max_reach_30_degrees_and_clip_beyond_range` | T2 |
| `test_t3_throttle_extremes_map_to_collective_0_and_1` | T3 |
| `test_t4_yaw_channel_does_not_change_setpoint_or_collective` | T4 |
| `test_t5_step_with_rc_produces_four_finite_forces_no_plant_no_gpio` | T5 |
| `test_t6_radio_py_still_has_no_decode_or_serial_and_c20_policy_unchanged` | T6 |
| `test_t7_radio_intent_adapter_not_implemented_and_rejectall_default` | T7 |
| `test_t8_loop_module_math_untouched_by_this_buy` | T8 |
| `test_t10_pyproject_version_is_0_5_23` | T10 |
| `test_t11_full_suite_process_gate_placeholder` | T11 marker (real gate is the full-suite run below) |
| `test_crsf_rc_channels_accepted_directly_without_reparsing` | `CrsfRcChannels` input path |
| `test_rejects_too_short_channel_sequence` | typed-error path |
| `test_rejects_non_int_channel_values` | typed-error path, incl. `bool` rejection |
| `test_t_s_is_caller_supplied_never_invented` | IC §0 decision 8 |
| `test_rc_setpoint_not_under_capabilities_and_no_cpp_or_cmake_under_flight_software` | IC §1 placement lock |
| `test_no_craft_or_core_imports_of_rc_setpoint_and_registry_still_empty` | craft/registry isolation |
| `test_no_serial_or_baud_imports_in_rc_setpoint` | no serial/baud coupling |
| `test_max_tilt_is_pi_over_6` | constant sanity |

```text
tests/test_fase_c_rc_setpoint_b1.py: 18 passed
```

### 5.2 Full Python suite

```text
3538 passed, 2 skipped in 5.60s
```

Baseline before this Buy: `3520 passed, 2 skipped`. Delta: **+18**, exactly matching the new test count — zero regressions.

### 5.3 C++ — new Catch2 cases + full host `ctest`

`native/flight_control/tests/test_rc_setpoint.cpp` — 5 new `TEST_CASE`s:

1. `map_rc_to_loop_inputs: all-mid sticks give ~level quat and finite collective` (IC T9)
2. `map_rc_to_loop_inputs: throttle extremes map to collective 0 and 1` (IC T9)
3. `map_rc_to_loop_inputs: roll max reaches +30 degrees, clips beyond range`
4. `map_rc_to_loop_inputs: yaw channel changes do not change setpoint/collective`
5. `map_rc_to_loop_inputs: rejects too-short channel lists`

```text
$ cmake -S native/flight_control -B build/flight_control
$ cmake --build build/flight_control -j4     # clean build, zero warnings
$ ctest
100% tests passed out of 36

Total Test time (real) = 0.40 sec
```

Baseline before this Buy: 31 host tests. Delta: **+5**, exactly the new `TEST_CASE` count. `fc_closed_loop_smoke` and `fc_esc_pwm_smoke` both still pass.

### 5.4 MCU cross-compile re-verification (not required by IC §4, done for completeness)

Re-verified with the same known-complete toolchain C16/C24 used (xPack `arm-none-eabi-gcc` v15.2.1-1.1, still present on this machine from the C16 Buy):

```text
$ export PATH="/private/tmp/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin:$PATH"
$ cmake -S native/flight_control -B build/flight_control_mcu \
    -DCMAKE_TOOLCHAIN_FILE=<repo>/native/flight_control/cmake/toolchains/arm-none-eabi.cmake
$ cmake --build build/flight_control_mcu -j4
[  7%] Building CXX object CMakeFiles/jarvis_fc.dir/src/filter.cpp.obj
...
[ 64%] Building CXX object CMakeFiles/jarvis_fc.dir/src/rc_setpoint.cpp.obj
[ 71%] Linking CXX static library libjarvis_fc.a
[100%] Built target fc_mcu_stub.elf
```

`rc_setpoint.cpp` compiles cleanly for the ARM cross target (Cortex-M4) alongside every other rung, and `fc_mcu_stub.elf` still links. `stub_main.cpp` was not touched (`git diff --stat` empty) and still never references `rc_setpoint`/`ControlLoop`/`step(`.

**Process note (not a source issue):** the bare Homebrew `arm-none-eabi-gcc` on this machine's default `PATH` still lacks `newlib`/`libstdc++` (the exact gap C16's report already documented) — a `-DCMAKE_TOOLCHAIN_FILE` reconfigure with only that compiler on `PATH` fails on `<optional>`, same as before. Using the previously-downloaded xPack release (still cached at `/private/tmp/xpack-arm-none-eabi-gcc-15.2.1-1.1` from C16) resolved it. This is an unchanged, pre-existing environment fact, not a regression introduced by this Buy.

---

## 6. Honesty / forbidden — confirmed

| Forbidden (IC §5) | Verified absent |
|---|---|
| "Sticks fly the craft" | Not present in `rc_setpoint.py`/`.hpp`/`.cpp`, docs, or this report |
| "Angle mode product" | Not claimed — the roll/pitch map is explicitly documented as illustrative, not a product attitude-mode |
| "ELRS connected" | Not claimed — no frame parsing, no live link, anywhere in this Buy |
| Safety allow via sticks | `rc_setpoint.py`/`.hpp`/`.cpp` never reference `SafetyGate`/`submit_command`/`propose_command` (grep + `test_t5`, `test_t7`) |
| Yaw heading lock | Yaw channel is read nowhere; `AttitudeSetpoint`'s quaternion always has yaw `= 0` fixed by construction, never claimed as heading-hold |

Honesty line, shipped verbatim in this report and in the docs updated below:

```text
RC->setpoint != flying != sticks drive motors != Safety allow != yaw lock
```

---

## 7. Module-boundary / forbidden-symbol grep (run at close of this Buy)

```text
$ git diff --stat -- src/jarvis/capabilities/ src/jarvis/flight_software/autonomy/ native/flight_control/mcu/ \
    src/jarvis/flight_software/flight_control/loop.py \
    native/flight_control/include/jarvis/fc/loop.hpp native/flight_control/src/loop.cpp
(empty)

$ grep -n "Reset_Handler\|ControlLoop\|rc_setpoint" native/flight_control/mcu/stub_main.cpp
# no match (exit 1)

$ grep -rin "crsf\|elrs" native/
# no match (exit 1) — the C21-C23 native-tree lock holds, including for this Buy's own new files
```

`git status --short` at close of this Buy shows exactly the expected file set: `rc_setpoint.py`, `rc_setpoint.hpp`, `rc_setpoint.cpp`, `test_rc_setpoint.cpp`, `test_fase_c_rc_setpoint_b1.py` (new), `CMakeLists.txt` (modified to register the two new files), plus `pyproject.toml` + version-checkpoint test re-pins + docs. No `capabilities/`, `autonomy/`, `mcu/`, or `loop.{py,hpp,cpp}` files touched.

---

## 8. Files changed

**New:**
- `src/jarvis/flight_software/flight_control/rc_setpoint.py`
- `native/flight_control/include/jarvis/fc/rc_setpoint.hpp`
- `native/flight_control/src/rc_setpoint.cpp`
- `native/flight_control/tests/test_rc_setpoint.cpp`
- `tests/test_fase_c_rc_setpoint_b1.py`
- `.jes/artifacts/implementation_report_fase_c_rc_setpoint_b1.md` (this file)

**Modified:**
- `native/flight_control/CMakeLists.txt` (`src/rc_setpoint.cpp` added to `jarvis_fc`; `tests/test_rc_setpoint.cpp` added to `fc_unit_tests`)
- `native/flight_control/README.md` (Layout + a new C25 paragraph — kept protocol-agnostic, see §2.2)
- `pyproject.toml` (`0.5.22` → `0.5.23`)
- 30 pre-existing test files re-pinned from `0.5.22` to `0.5.23` (26 via the literal `'version = "X.Y.Z"' in text` pattern; 4 via the `re.search(...); match.group(1) == "X.Y.Z"` regex-checkpoint pattern first found during C24's own re-pin sweep)
- `README.md`, `docs/ARCHITECTURE.md`, `docs/PLATFORM_CAPABILITY_VISION.md`, `docs/IMPLEMENTATION_TASKS.md` (see §9)

---

## 9. Docs updated (honesty confirmed — not claiming CLOSED/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.23 includes (working tree — not yet tagged)" section, explicitly says "no `v0.5.23` tag yet."
- `docs/ARCHITECTURE.md` §1c — new C25 paragraph after the C24 block, top banner updated to "Working tree ahead: package `0.5.23` ... awaiting Cursor review + Engineer ★ ACCEPT — no `v0.5.23` tag yet."
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C25 block, same "landed — awaiting ... no tag yet" phrasing, honesty line verbatim.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner and the C25 table row both changed to "Landed — awaiting Cursor review + ★ ACCEPT (no `v0.5.23` tag yet)."
- `native/flight_control/README.md` — Layout section + new paragraph on `rc_setpoint.hpp`/`rc_setpoint.cpp`, written without naming the radio protocol (native-tree lock).

No file in this Buy claims `v0.5.23` is tagged or ACCEPT CLOSED. Confirmed via `git tag -l | sort -V | tail -3` at close of this Buy: `v0.5.20`, `v0.5.21`, `v0.5.22` — `v0.5.23` does not exist yet.

---

## 10. Residual / next steps

- C26 (EscOutput HAL) is next in the parked queue, per the IC's own handoff — explicitly **not** started here.
- C27 (CRSF stream-timeout failsafe), C28 (MCU UART HAL stub), C29 (silicon + cited FLASH map) all remain parked, untouched.
- `run_controlled_flight_sim_smoke` (C11) was **not** switched to RC input this Buy — the IC explicitly allowed it to stay on `level_setpoint`, and it does.
- The C++-side constant naming deviation from the IC's own §2 pseudocode (§2.2 above) should be flagged to Cursor/Engineer during review — it is a disclosed, behavior-preserving rename driven by a pre-existing native-tree lock, not a silent change.

---

## 11. Acceptance self-check vs IC §7

- T1-T8, T10-T11 (Python): ✅ all pass, 18/18 new tests green.
- T9 (C++ Catch2): ✅ 5 new cases pass.
- T11 (full suite + `ctest` green): ✅ `3538 passed, 2 skipped` (Python); `36/36` (`ctest`).
- T12 (this report's honesty content): ✅ this section.
- Mapper only (no mixing/ESC inside it): ✅ grep + `test_t5`.
- C24/C20 frozen: ✅ `git diff --stat` empty on `loop.py`/`loop.hpp`/`loop.cpp`/`crsf_dual_role.py`; `CrsfDualRolePolicy()` defaults re-verified.
- No GPIO: ✅ grep clean.
- Version `0.5.23`: ✅ `pyproject.toml` + all checkpoint tests re-pinned.
- Docs honest: ✅ §9 above — no premature CLOSED/tag claim anywhere.

**PASS** against every criterion in IC §7. **FAIL conditions** (sticks claimed to fly, Safety execute, yaw sold as heading, serial in this module, `radio.py` growing decode) — none present, verified above.
