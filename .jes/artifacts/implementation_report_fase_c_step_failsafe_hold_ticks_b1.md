# Implementation Report — Fase C denser `step` ticks (`B1-fase-c-step-failsafe-hold-ticks`)

**IC:** [`implementation_contract_fase_c_step_failsafe_hold_ticks_b1.md`](implementation_contract_fase_c_step_failsafe_hold_ticks_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-25
**Status:** Landed — awaiting Cursor independent review + Engineer ★ ACCEPT. **No `v0.5.33` tag yet** (confirmed via `git tag -l | sort -V | tail -3` at close of this Buy: `v0.5.30`, `v0.5.31`, `v0.5.32` — `v0.5.33` does not exist).

---

## 0. Read this first — honesty summary

This Buy is **tests only**. It locks three facts C24 and C27 already
*allow* but had never *chained*: (1) **many** `step()` ticks on a canned
IMU stay finite, (2) a **stale** hold watch feeds `failsafe_loop_inputs`
**into** that same `step()`, (3) **hold** means keep feeding
`level_setpoint` for those ticks — never `AutonomyVerb.HOLD` reaching
execution. No production module was touched: `loop.py`/`loop.hpp`/
`loop.cpp`, `rc_hold.hpp`/`rc_hold.cpp`, `crsf_failsafe.py`, and
`spi_probe.hpp`/`spi_probe.cpp` (C34) are all byte-unchanged.

**Many ticks != flying != 6-DoF. Failsafe -> step != motors cut != HOLD executed.**

**Exists:** tests that call `step()` a thousand times on canned IMU, and
tests that feed a stale-RC failsafe decision into that same `step()`.
**Impossible:** a flying plant; motors cutting on timeout; `HOLD`
reaching Safety-approved execution; IMU samples from `probe_rx`. Nothing
in this Buy is any of those.

---

## 1. Package layout vs IC §1

```text
tests/test_fase_c_step_failsafe_hold_ticks_b1.py       # NEW — 12 tests
native/flight_control/tests/test_loop.cpp                # EXTENDED — 4 new Catch2 cases
```

No production harness was added under `src/jarvis/` or
`include/jarvis/fc/` — every test calls the existing shipped APIs
directly (`FlightControlLoop.step`/`ControlLoop::step`,
`CrsfRcHoldWatch`/`RcHoldWatch`, `failsafe_loop_inputs`). The IC's own
§1 STOP condition ("a test cannot call the existing APIs") never
triggered.

---

## 2. Tests implemented vs IC §0 decisions 4-8 / §4

| Item | IC ref | Match |
|---|---|---|
| Glue lives in tests, not `ControlLoop`/`FlightControlLoop` | §0.4 | ✅ `inputs = failsafe_loop_inputs(t)` then `loop.step(sample, inputs.setpoint, inputs.collective)`, written in the test bodies only |
| N = 1000 ticks | §0.5 | ✅ `N_TICKS = 1000` (Python), `kTicks = 1000` (Catch2) |
| Canned level IMU (`accel ≈ (0,0,-9.81)`, gyro zeros) | §0.5 | ✅ matches the exact convention already used in `test_fase_c_control_loop_tick_b1.py`/`test_loop.cpp`'s own prior cases |
| `level_setpoint`, collective `0.5` | §0.5 | ✅ |
| Every tick: four forces finite in `[0, 1]` | §0.5 | ✅ asserted per-tick, not just at the end |
| No `ToyQuadAttitudePlant` on this path | §0.5 | ✅ neither the Python nor the Catch2 T1 case constructs a plant |
| Stale watch (never noted, or past 0.5 s) -> `failsafe_loop_inputs(t_s)` -> `step` | §0.6 | ✅ both "never noted" and "past timeout" cases, Python + Catch2 |
| Collective passed into `step` is `0` | §0.6 | ✅ `inputs.collective == 0.0`, asserted before the `step` call |
| No `EscOutput`/GPIO call in the new tests | §0.6 | ✅ neither `EscOutput` nor any GPIO symbol appears in either new file |
| Hold = keep passing `level_setpoint` for N ticks | §0.7 | ✅ `test_t3_hold_keeps_passing_level_setpoint...` and the Catch2 `level_setpoint throughout` case both assert the identity quaternion every tick, not just once |
| `submit_command(HOLD)` stays `not_attempted` | §0.7 | ✅ re-asserted explicitly under `default_safety_gate()` |
| `ImuSample` still a caller-filled struct, no `probe_rx` decode | §0.8 | ✅ `_level_imu_sample`/plain struct literals only; `probe_rx` never imported by these tests |

### 2.1 Non-goals (IC §2) — confirmed absent

6-DoF plant, `step` calling `plant.step`, folding `RcHoldWatch` into
`ControlLoop`, IMU from `probe_rx`, Safety execute, DShot wire, C30 DFU,
Taller CSS, standoff points — confirmed by §6's grep and by
`test_no_6dof_plant_or_step_signature_change` /
`test_t5_this_test_module_does_not_import_probe_rx_as_a_sensor`.

### 2.2 Two false-positive test bugs found and fixed during self-verification

Both `FlightControlLoop.step`'s own docstring and this test module's own
top-of-file docstring **honestly name** `probe_rx`/`plant.step` to say
they are absent — the same recurring false-positive pattern seen in
prior Buys' honesty checks (a bare substring match on a forbidden token
trips on the prose that discloses the token's absence). Fixed:

- `test_t5_...`: now scans only lines starting with `import `/`from `,
  not the whole file text, before checking for `probe_rx`/`SpiBytePort`/
  `ScriptedSpi`.
- `test_no_6dof_plant_or_step_signature_change`: now strips
  `FlightControlLoop.step.__doc__` out of the inspected source before
  checking for a `plant.` call — the docstring's own honest "Does not
  call `plant.step`" sentence was tripping the check before this fix.

Both were caught and fixed by running the new test module before
declaring it done (§5.1), not discovered later.

---

## 3. Verified — a real build, real symbols

```text
$ cmake --build build/flight_control -j
[ 91%] Building CXX object CMakeFiles/fc_unit_tests.dir/tests/test_loop.cpp.o
[100%] Built target fc_unit_tests
$ ctest --output-on-failure
100% tests passed out of 76
```

`test_loop.cpp`'s 4 new cases (`#33-36` in this build's numbering) also
run individually clean:

```text
$ ctest -I 33,36 --output-on-failure
100% tests passed out of 4
```

```text
$ export PATH="/private/tmp/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin:$PATH"
$ cmake --build build/flight_control_mcu -j
[ 75%] Built target jarvis_fc
[100%] Built target fc_mcu_stub.elf
```

The ARM cross-compile build is a no-op for this Buy (test files are
host-only, not part of the `jarvis_fc` static library or the
freestanding `.elf`) — confirmed still green regardless.

---

## 4. Integration rules vs IC §3

| Existing | This Buy |
|---|---|
| C24 `step` | **Byte-unchanged** — `git diff --stat` empty on `loop.hpp`/`loop.cpp`/`loop.py`; tests call it more, in a new combination |
| C27 failsafe | **Byte-unchanged** — `git diff --stat` empty on `rc_hold.hpp`/`rc_hold.cpp`/`crsf_failsafe.py`; tests chain it into `step` |
| C11 plant smoke | **Unchanged** — still the separate *with-plant* recovery path (`test_loop.cpp`'s own pre-existing "matches the inlined C13 smoke chain" case, untouched) |
| C34 `probe_rx` | **Unchanged** — `git diff --stat` empty on `spi_probe.hpp`/`spi_probe.cpp`; not used as an IMU source anywhere in the new tests |
| Safety RejectAll | **Unchanged** — re-verified explicitly in both the Python and the pre-existing default-gate tests |

---

## 5. Tests run

### 5.1 Python — new module

`tests/test_fase_c_step_failsafe_hold_ticks_b1.py` — **12 tests**,
covering IC §4's T1-T8, T10 in Python form (T1/T2 additionally run as
Catch2 cases below; T9 is the full-suite/ctest run in §3/§5.2):

| Test | Covers |
|---|---|
| `test_t1_1000_ticks_canned_level_imu_no_plant_forces_finite_in_0_1` | T1 |
| `test_t2_never_noted_watch_is_stale_failsafe_inputs_feed_step_collective_zero` | T2 (never-noted case) |
| `test_t2_watch_stale_past_timeout_also_feeds_step_via_failsafe_loop_inputs` | T2 (past-timeout case) |
| `test_t3_hold_keeps_passing_level_setpoint_and_autonomy_hold_stays_not_attempted` | T3 |
| `test_t4_loop_rc_hold_crsf_failsafe_spi_probe_git_unchanged` | T4 |
| `test_t5_this_test_module_does_not_import_probe_rx_as_a_sensor` | T5 |
| `test_t6_default_safety_gate_still_reject_all` | T6 |
| `test_t7_native_tree_zero_crsf_elrs_tokens` | T7 |
| `test_t8_pyproject_version_is_0_5_33` | T8 |
| `test_t9_full_suite_process_gate_placeholder` | T9 marker (real gate is the full-suite run below) |
| `test_no_6dof_plant_or_step_signature_change` | IC §2 non-goal (no plant call, frozen signature) |
| `test_no_craft_or_core_imports_reference_this_buys_glue` | craft/registry isolation |

```text
tests/test_fase_c_step_failsafe_hold_ticks_b1.py: 12 passed
```

### 5.2 Full Python suite

```text
3691 passed, 2 skipped in 8.35s
```

Baseline before this Buy: `3679 passed, 2 skipped`. Delta: **+12**,
exactly matching the new test count — zero regressions.

### 5.3 C++ — new Catch2 cases + full host `ctest`

`native/flight_control/tests/test_loop.cpp` — 4 new `TEST_CASE`s
appended, tag `[loop][c35]`:

1. `ControlLoop::step: 1000 ticks with canned level IMU, no plant, stay finite in [0,1]` (IC T1)
2. `ControlLoop::step: a never-noted RcHoldWatch is stale; failsafe_loop_inputs feeds step with collective 0` (IC T2)
3. `ControlLoop::step: a watch stale past timeout also feeds step via failsafe_loop_inputs` (IC T2)
4. `ControlLoop::step: 1000 ticks keep using level_setpoint throughout (hold-as-input, not an actuator)` (IC T3)

```text
100% tests passed out of 76
```

Baseline before this Buy: 72 host tests. Delta: **+4**, exactly the new
`TEST_CASE` count. All pre-existing `[loop]`-tagged cases (including the
C24 bit-for-bit smoke-chain regression) still pass unchanged.

---

## 6. Module-boundary / forbidden-symbol grep (run at close of this Buy)

```text
$ git diff --stat -- native/flight_control/include/jarvis/fc/loop.hpp native/flight_control/src/loop.cpp \
    native/flight_control/include/jarvis/fc/rc_hold.hpp native/flight_control/src/rc_hold.cpp \
    src/jarvis/flight_software/flight_control/loop.py src/jarvis/capabilities/crsf_failsafe.py \
    native/flight_control/include/jarvis/fc/spi_probe.hpp native/flight_control/src/spi_probe.cpp \
    native/flight_control/include/jarvis/fc/spi.hpp native/flight_control/src/spi.cpp
(empty)

$ grep -rin "crsf\|elrs" native/
# no match (exit 1) — the C21-C34 native-tree lock holds (rc_hold.hpp
# already used the protocol-agnostic RcHoldWatch/RcHoldDecision names;
# no new crsf/elrs token was introduced anywhere in native/)
```

`git status --short` at close of this Buy shows exactly the expected
file set: `test_loop.cpp` (modified),
`test_fase_c_step_failsafe_hold_ticks_b1.py` (new), plus `pyproject.toml`
+ version-checkpoint test re-pins + docs. No `loop.{hpp,cpp,py}`,
`rc_hold.{hpp,cpp}`, `crsf_failsafe.py`, `spi_probe.{hpp,cpp}`, `spi.hpp`,
or `spi.cpp` touched.

---

## 7. Files changed

**New:**
- `tests/test_fase_c_step_failsafe_hold_ticks_b1.py`
- `.jes/artifacts/implementation_report_fase_c_step_failsafe_hold_ticks_b1.md` (this file)

**Modified:**
- `native/flight_control/tests/test_loop.cpp` (4 new Catch2 cases appended; `#include "jarvis/fc/rc_hold.hpp"` / `"jarvis/fc/rc_setpoint.hpp"` added)
- `pyproject.toml` (`0.5.32` → `0.5.33`)
- 40 pre-existing test files re-pinned from `0.5.32` to `0.5.33` (literal `'version = "X.Y.Z"' in text` pattern and the `match.group(1) == "X.Y.Z"` regex pattern)
- `README.md`, `docs/ARCHITECTURE.md` (new §1c paragraph after C34), `docs/PLATFORM_CAPABILITY_VISION.md` §13, `docs/IMPLEMENTATION_TASKS.md` (see §9)

No `CMakeLists.txt` change was needed — `test_loop.cpp` was already
registered in `fc_unit_tests` since C24. No pre-existing test needed a
disclosed retargeting this Buy.

---

## 8. Docs updated (honesty confirmed — not claiming CLOSED/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.33 includes (landed, awaiting Cursor review + Engineer ★ ACCEPT — no `v0.5.33` tag yet)" section; the v0.5.32 section's own "Next" line and the bottom "Next" mention both updated to point at C35 LANDED.
- `docs/ARCHITECTURE.md` §1c — new C35 paragraph after the C34 block, banner updated to "C35 LANDED @ package `0.5.33` (awaiting Cursor review + Engineer ★ ACCEPT, no `v0.5.33` tag yet)."
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C35 block, same "landed — awaiting ... no tag yet" phrasing, honesty line verbatim ("Many ticks ≠ flying ≠ 6-DoF. Failsafe → step ≠ motors cut ≠ HOLD executed").
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner's "PRIORIDAD AHORA" line and the C35 table row both changed from "★ Engineer proceed" to "LANDED (awaiting Cursor review + Engineer ★ ACCEPT, no tag yet)"; suite/ctest counts updated `3679`/`72/72` → `3691`/`76/76`.

No file in this Buy claims `v0.5.33` is tagged or ACCEPT CLOSED, and none
claims a flying plant, a motor cut on timeout, or an executed
`AutonomyVerb.HOLD` exists. Confirmed via `git tag -l | sort -V | tail -3`
at close of this Buy: `v0.5.30`, `v0.5.31`, `v0.5.32` — `v0.5.33` does
not exist yet.

---

## 9. Residual / next steps

- Taller CSS cuboid faces (cola 3) and standoff perimeter points (cola 4)
  remain the two remaining no-pin fronts per the existing "situation
  after C33" engineer note — neither opened by this Buy.
- DShot *wire*, on-chip USART, C30's own desk DFU smoke, a gyro
  (ICM42688P) register driver, Safety execute, and craft↔FS all remain
  independently parked axes per the existing process lock and bench
  note — none opened by this Buy.
- The two false-positive test bugs fixed during self-verification
  (§2.2) are a pattern worth remembering for any future Buy that writes
  a grep-style check against a module whose own docstring honestly
  names a forbidden symbol to disclaim it.
- A future Buy that wires `probe_rx` into a real IMU sensing path would
  be an explicitly-scoped Buy of its own, not an extension of this one
  — this Buy's own T5/`test_t5_...` guards against silently drifting
  toward that.

---

## 10. Acceptance self-check vs IC §7

- T1-T10: ✅ all pass — T1/T2 in both Python and Catch2, T3-T8/T10 in Python, T9 via the full-suite/`ctest` runs below.
- Full suite + `ctest` green: ✅ `3691 passed, 2 skipped` (Python); `76/76` (`ctest`).
- Production loop/failsafe frozen: ✅ `git diff --stat` empty on all eight named files.
- No plant on the new path: ✅ neither the Python nor the Catch2 T1/T3 cases construct `ToyQuadAttitudePlant`.
- No 6-DoF: ✅ no simulator, no position/velocity loop added anywhere.
- `step` does not call plant: ✅ `test_no_6dof_plant_or_step_signature_change` checks the executable body (docstring excluded), no `plant.` call found.
- Failsafe not folded into `ControlLoop`/`FlightControlLoop`: ✅ glue (`failsafe_loop_inputs(t)` then `.step(...)`) lives only in test bodies.
- `probe_rx` not used as IMU: ✅ `test_t5_...` and Catch2 cases both construct plain `ImuSample`/`Vec3` literals only.
- No Safety execute: ✅ `submit_command(HOLD)` re-asserted `execution="not_attempted"` under `RejectAllSafetyGate`.
- Version `0.5.33`: ✅ `pyproject.toml` + all 41 checkpoint tests re-pinned.

**PASS** against every criterion in IC §7. **FAIL conditions** (6-DoF,
`step` calling plant, failsafe folded into `ControlLoop`, `probe_rx` as
IMU, Safety execute, `HOLD` `executed`) — none present, verified above.
