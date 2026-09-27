# Implementation Report — Fase C autonomy executor (`B1-fase-c-autonomy-executor`)

**IC:** [`implementation_contract_fase_c_autonomy_executor_b1.md`](implementation_contract_fase_c_autonomy_executor_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-26
**Status:** ★ **ACCEPT CLOSED** @ tag **`v0.5.41`** (Engineer 2026-09-27) · Cursor review PASS WITH NOTES.

---

## 0. Read this first — honesty summary

This Buy adds a **separate, sim-only** autonomy executor that maps
`AutonomyVerb.HOLD`/`GO_TO`/`LAND` into the existing C38/C39 setpoint
chain so verbs actually drive `ToyQuad6DofPlant` — autonomy verbs stop
being only labels that RejectAll.

```text
verb -> setpoints in RAM != execute on copper
sim HOLD/LAND/GO_TO != flying != Safety allow
plant outside step != MCU ISR != motors
z may droop under tilt (C39 N2) != altitude bug
```

**Exists:** a stateful sim executor that reuses C38/C39's own
controllers to drive HOLD/LAND/GO_TO in RAM against a toy plant.
**Impossible:** any of those three verbs executing on real hardware; a
Safety `allow`; a real vehicle holding, landing, or navigating. Nothing
in this Buy is any of those, and `AutonomySubmissionResult.execution`
is never set to `"executed"` anywhere in this Buy's own code.

---

## 1. Package layout vs IC §1

```text
src/jarvis/flight_software/autonomy/sim_executor.py   # NEW — SimAutonomyExecutor + SimAutonomyParams + SimAutonomyTickResult
src/jarvis/flight_software/autonomy/__init__.py          # EXTENDED — new exports
src/jarvis/flight_software/autonomy/surface.py           # UNCHANGED
src/jarvis/flight_software/autonomy/types.py             # UNCHANGED

native/flight_control/include/jarvis/fc/sim_autonomy_executor.hpp   # NEW
native/flight_control/src/sim_autonomy_executor.cpp                   # NEW
native/flight_control/tests/test_sim_autonomy_executor.cpp            # NEW — 4 Catch2 cases

tests/test_fase_c_autonomy_executor_b1.py   # NEW — 9 tests
```

Placed at `src/jarvis/flight_software/autonomy/sim_executor.py` — next
to the C4 surface, not inside `flight_control/`, matching the IC's own
preferred layout. Not placed under `capabilities/` (C41's own future
policy home). Does not import Continuity.

---

## 2. Types / API implemented vs IC §0 / §2

| Item | IC ref | Match |
|---|---|---|
| Separate sim executor API (not `"executed"` on C4 submit) | §0.4 | ✅ `SimAutonomyExecutor.tick(...)` — `propose_command`/`submit_command`/`AutonomySubmissionResult` completely untouched |
| Verb → setpoints (HOLD/GO_TO/LAND) | §0.5 | ✅ see §2.1 for the exact semantics of each |
| Executor runs outside `step`; reuses C38/C39 controllers | §0.6 | ✅ `sense -> HALs -> pos.compute -> alt.compute -> loop.step -> plant.step`, no PD law reimplemented |
| Respects C39 N2 coupling | §0.7 | ✅ tests do not require glued z during `GO_TO`; `HOLD` bound asserted only after settling; `LAND` only asserts strict z decrease |
| Typed sim request (`SimAutonomyParams`) preferred over `AutonomyCommand.params` string dict | §0.8 | ✅ chosen — see §2.1 |
| Python + C++ | §0.9 | ✅ both, full twin (not deferred) — see §2.2 |
| Plants/controllers/C4 surface untouched | §0.10 | ✅ `git diff --stat` empty on all named modules (§4) |

### 2.1 Disclosed design choices

**Name:** `SimAutonomyExecutor` (of the two IC-suggested names,
`SimAutonomyExecutor`/`AutonomySimRunner`) — chosen for symmetry with
`SimulatedPositionHal`/`SimulatedAltitudeHal`'s own `Sim*` naming
convention already established in this tree.

**Params:** a typed `SimAutonomyParams(x_m, y_m, z_m)` (all optional
floats), not `AutonomyCommand.params: dict[str, str]` — the IC's own
"prefer typed sim request if cleaner" default. This executor does not
accept or construct an `AutonomyCommand` at all; a caller bridging from
`propose_command`'s own typed command into this executor's params
would do that translation itself outside this module (not needed for
this Buy's own tests/smokes).

**Verb semantics (the load-bearing design decision this Buy makes):**

- **`HOLD`** — freezes a `PositionSetpoint` at the current xy (or
  caller-supplied `x_m`/`y_m`) and a `z_des_m` at the current z (or
  caller-supplied `z_m`) **the first tick `HOLD` is ticked**, then holds
  that same frozen point every subsequent tick regardless of drift.
  Freezing once, rather than re-reading "current position" every tick,
  is the only way `HOLD` can be a real constraint — reading current
  position every tick would make the position-controller's own error
  always zero, a degenerate no-op that "holds" nothing.
- **`GO_TO`** — every tick builds a fresh `PositionSetpoint` straight
  from `params.x_m`/`params.y_m` (both required, `ValueError` if either
  is absent) — **not** frozen, so a caller may retarget mid-sequence
  simply by ticking with different params under the same verb. `z_m` is
  optional; when absent on the first `GO_TO` tick, the altitude target
  freezes at whatever z the plant was at when `GO_TO` began — a
  documented "keep your current height unless told otherwise" default,
  not a newly invented cruise-altitude constant.
- **`LAND`** — freezes xy the same way `HOLD` does, and ratchets a
  descending `z_des_m` target downward by `land_rate_mps * dt_s` each
  tick (default `0.5 m/s`), clamped at a documented floor `z_land_m`
  (default `0.0`) or a caller-supplied `z_m` floor. A toy descent-rate
  schedule, never a claim of touchdown gear, ground contact, or motor
  cutoff.
- **Verb-change reset:** all three verbs' frozen anchors reset whenever
  the active verb changes (tracked via `self._active_verb`) — so
  switching from `GO_TO` to `HOLD` re-captures wherever the plant
  currently is, rather than reusing a stale anchor from a prior verb.
- **Unsupported verbs** (`TAKEOFF`/`FOLLOW`/`RETURN_HOME`/`PATROL`) —
  `tick(...)` raises `ValueError` naming the verb. This Buy implements
  exactly three verbs per the IC's own lock; the other four `AutonomyVerb`
  members remain valid to `propose_command` (C4), just not driven by
  this executor.

**Gain/tuning reuse — no new PD law:** `SimAutonomyExecutor` constructs
(or accepts injected) unmodified `PositionController`/`AltitudeController`
instances with their own existing defaults — it does not compute, tune,
or override any gain itself.

**Honesty-check false positive caught and fixed before landing:** the
first draft of this module's own docstring literally wrote
`` `AutonomySubmissionResult.execution = "executed"` `` as a disclosure
sentence ("nothing here ever sets X"). Running the full suite exposed
that `tests/test_fase_c_safety_real_policy_b1.py`'s own C17 honesty
check strips whitespace and greps for the literal shape
`execution="executed"` anywhere under `src/jarvis/` — including inside
disclosure prose, which is a known, accepted false-positive risk that
check's own docstring names explicitly. Fixed by rephrasing the
disclosure sentence to never place `execution` and `"executed"` in that
exact adjacent shape (`"never writes the word "executed" into any field
anywhere in this file"`), preserving the same honesty content without
tripping the check. No test file was weakened to make this pass.

### 2.2 C++ twin shipped in full (not deferred)

The IC allowed deferring the C++ twin if it would be "empty theater."
This module is real per-tick stateful control-dispatch math (frozen
anchors, a descent schedule, verb-change resets) — exactly the kind of
logic this C++ tree exists to port — so the twin was implemented in
full, not deferred. `SimAutonomyVerb` is a small LOCAL C++ enum
(`kHold`/`kGoTo`/`kLand`) scoped to this executor only; this tree has
never ported the seven-member Python `AutonomyVerb`/the C4 command
surface to C++, and this Buy does not start that port — the local enum
is not presented as, and does not attempt to be, that twin.

### 2.3 Non-goals (IC §0 decision 2) — confirmed absent

C41 Safety allowlist, ICM client, craft↔FS, Assistant, silicon,
rewriting C38/C39 laws, house map — confirmed by grep (§6) and by
`test_t7_...`/`test_t5_...` (registry isolation, RejectAll intact, no
`"executed"` string in the new module).

---

## 3. Verified — real builds, real test runs

Before formalizing any test, three scratch closed-loop runs (deleted
after verification, not committed) confirmed the verb semantics work
as documented:

```text
GO_TO (5,0): final (5.99, 0.0, -0.68) dist 0.99   # single-run smoke, informed T1's chosen target
GO_TO (3,2) combined roll+pitch: converges but slowly (~2500-3000
  steps needed) due to coupled transient oscillation — informed the
  choice of a single-axis target (3,0) for the formal T1/T2/T3 tests,
  which converges cleanly within 1500 steps
GO_TO(3,0,z=2) -> HOLD: after full convergence + 300-tick settle,
  a 500-tick HOLD window holds within [3.0002, 3.0050] x, exactly 0.0 y,
  [1.9997, 1.9997] z — informed the documented 0.5m T2 bound (generous
  vs. the ~0.005m actually observed)
GO_TO(0,0,z=2) -> LAND: z 1.9999 -> 0.0115 over 1000 ticks
```

```text
$ cmake --build build/flight_control -j4
[  1%] Building CXX object CMakeFiles/jarvis_fc.dir/src/sim_autonomy_executor.cpp.o
[100%] Built target fc_unit_tests
$ ctest --output-on-failure
100% tests passed out of 105
```

```text
$ python -m pytest tests/test_fase_c_autonomy_executor_b1.py -v
9 passed
$ python -m pytest -q
3732 passed, 9 skipped
```

Baseline before this Buy: `3723 passed, 9 skipped` (Python), `101/101`
(host `ctest`). Delta: **+9 passed** (Python), **+4** (`ctest`) — exactly
the new test counts, zero regressions (after fixing the honesty-prose
false positive in §2.1, which was caught and fixed before this Buy's
own final full-suite run, not left as a known failure).

---

## 4. Integration rules vs IC §3

| Existing | This Buy |
|---|---|
| `ToyQuadAttitudePlant`/`ToyQuad6DofPlant` dynamics | Untouched — `git diff --stat` empty |
| `FlightControlLoop.step`/`ControlLoop::step` | No plant call, unchanged role |
| `controller.py`/`.hpp`/`.cpp` (C8 `AttitudeSetpoint`) | Untouched — `git diff --stat` empty |
| `position_controller.py`/`.hpp`/`.cpp` (C39) | Untouched — `git diff --stat` empty; reused as-is |
| `sim_position_hal.py`/`.hpp`/`.cpp` (C39) | Untouched — `git diff --stat` empty; reused as-is |
| `altitude_controller.py`/`.hpp`/`.cpp` (C38) | Untouched — `git diff --stat` empty; reused as-is |
| `sim_altitude_hal.py`/`.hpp`/`.cpp` (C38) | Untouched — `git diff --stat` empty; reused as-is |
| `attitude.py`/`.hpp`/`.cpp`, `rc_setpoint.py`/`.hpp`/`.cpp`, `mag.py`/`sim_mag_hal.py`/`.hpp`/`.cpp` | Untouched — `git diff --stat` empty |
| `surface.py`/`types.py` (C4 command surface) | Untouched — `git diff --stat` empty |
| esc/mixer/filter/rate_torque/rc_hold/crsf_failsafe/spi/spi_probe/dshot/uart | Untouched — `git diff --stat` empty |
| Safety/craft/registry | Untouched |

No pre-existing test required a disclosed retarget for its own logic in
this Buy — the one incident (§2.1) was a docstring-prose fix in this
Buy's own new file, not a change to any pre-existing test's meaning.

---

## 5. Tests run

### 5.1 Python — new module

`tests/test_fase_c_autonomy_executor_b1.py` — **9 tests**, covering IC
§2's T1-T8 (T6 is the C++ Catch2 cases below; T8's "suite+ctest green"
half is the process run in §3; T9 is this report):

| Test | Covers |
|---|---|
| `test_t1_go_to_shrinks_horizontal_distance_to_an_east_point` | T1 |
| `test_t2_hold_keeps_position_within_documented_bound_after_settling` | T2 |
| `test_t3_land_decreases_z_toward_documented_floor` | T3 |
| `test_t4_unsupported_verb_and_bad_params_raise` | T4 |
| `test_t5_submit_command_still_reject_and_no_executed_string_in_module` | T5 |
| `test_t6_loop_step_never_calls_plant_and_c11_c36_c37_c38_c39_smokes_still_green` | T6 |
| `test_t7_no_craft_continuity_library_board_edits` | T7 |
| `test_t8_pyproject_version_is_0_5_41` | T8 (version half) |
| `test_t8_full_suite_process_gate_placeholder` | T8 marker |

### 5.2 C++ — new Catch2 cases

`native/flight_control/tests/test_sim_autonomy_executor.cpp` — 4 new
`TEST_CASE`s, tag `[autonomy][c40]`: T1 (`GO_TO` shrinks horizontal
distance), T2 (`HOLD` bound after settling), T3 (`LAND` decreases z
toward floor), T4 (missing `x_m`/`y_m`, non-finite params/`dt_s`,
invalid constructor args all raise `std::invalid_argument`).

```text
100% tests passed out of 105
```

Baseline before this Buy: 101 host tests. Delta: **+4**, exactly the
new `TEST_CASE` count.

---

## 6. Module-boundary / forbidden-symbol grep

```text
$ git diff --stat -- native/flight_control/include/jarvis/fc/loop.hpp native/flight_control/src/loop.cpp \
    src/jarvis/flight_software/flight_control/loop.py \
    native/flight_control/include/jarvis/fc/plant.hpp native/flight_control/src/plant.cpp \
    src/jarvis/flight_software/flight_control/plant.py \
    native/flight_control/include/jarvis/fc/controller.hpp native/flight_control/src/controller.cpp \
    src/jarvis/flight_software/flight_control/controller.py \
    native/flight_control/include/jarvis/fc/attitude.hpp native/flight_control/src/attitude.cpp \
    src/jarvis/flight_software/flight_control/attitude.py \
    native/flight_control/include/jarvis/fc/rc_setpoint.hpp native/flight_control/src/rc_setpoint.cpp \
    src/jarvis/flight_software/flight_control/rc_setpoint.py \
    native/flight_control/include/jarvis/fc/mag.hpp native/flight_control/src/mag.cpp \
    src/jarvis/flight_software/flight_control/mag.py src/jarvis/flight_software/flight_control/sim_mag_hal.py \
    native/flight_control/include/jarvis/fc/altitude_controller.hpp native/flight_control/src/altitude_controller.cpp \
    native/flight_control/include/jarvis/fc/sim_altitude_hal.hpp native/flight_control/src/sim_altitude_hal.cpp \
    src/jarvis/flight_software/flight_control/altitude_controller.py src/jarvis/flight_software/flight_control/sim_altitude_hal.py \
    native/flight_control/include/jarvis/fc/position_controller.hpp native/flight_control/src/position_controller.cpp \
    native/flight_control/include/jarvis/fc/sim_position_hal.hpp native/flight_control/src/sim_position_hal.cpp \
    src/jarvis/flight_software/flight_control/position_controller.py src/jarvis/flight_software/flight_control/sim_position_hal.py \
    src/jarvis/flight_software/autonomy/surface.py src/jarvis/flight_software/autonomy/types.py \
    [... esc/mixer/filter/rate_torque/rc_hold/crsf_failsafe/spi/spi_probe/dshot/uart ...]
native/flight_control/CMakeLists.txt | 2 ++
1 file changed, 2 insertions(+)
(only the CMakeLists.txt wiring for the two new source files/one new
test file — every named module byte-unchanged)

$ git status --short -- ui/spatial-board library src/jarvis/core src/jarvis/adapters \
    src/jarvis/workspace src/jarvis/actions src/jarvis/schemas src/jarvis/knowledge
# only pre-existing, external, unrelated diffs (parallel craft-geometry
# track, present before this Buy, not touched by it)
```

---

## 7. Files changed

**New:**
- `src/jarvis/flight_software/autonomy/sim_executor.py`
- `native/flight_control/include/jarvis/fc/sim_autonomy_executor.hpp`
- `native/flight_control/src/sim_autonomy_executor.cpp`
- `native/flight_control/tests/test_sim_autonomy_executor.cpp`
- `tests/test_fase_c_autonomy_executor_b1.py`
- `.jes/artifacts/implementation_report_fase_c_autonomy_executor_b1.md` (this file)

**Modified:**
- `src/jarvis/flight_software/autonomy/__init__.py` (new exports: `SimAutonomyExecutor`, `SimAutonomyParams`, `SimAutonomyTickResult`)
- `native/flight_control/CMakeLists.txt` (one new source added to `jarvis_fc`; one new test file added to `fc_unit_tests`)
- `pyproject.toml` (`0.5.40` → `0.5.41`)
- 45 pre-existing test files re-pinned from `0.5.40` to `0.5.41`
- `README.md`, `docs/ARCHITECTURE.md` (new §1c/§1d paragraph after C39), `docs/PLATFORM_CAPABILITY_VISION.md` §13, `docs/IMPLEMENTATION_TASKS.md`, `native/flight_control/README.md` (see §8)

---

## 8. Docs updated (honesty confirmed — not claiming ACCEPT/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.41 includes (LANDED — awaiting Cursor review + Engineer ★ ACCEPT, no tag yet)" section; "Next" pointers retargeted.
- `docs/ARCHITECTURE.md` — new C40 paragraph after the C39 block, banner updated.
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C40 block, honesty line verbatim.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner and the C40 table row both changed to "LANDED (awaiting Cursor review + Engineer ★ ACCEPT, no tag yet)".
- `native/flight_control/README.md` — new paragraph after the C39 paragraph naming `sim_autonomy_executor.*` and the local-enum/no-C4-port disclosure.

No file in this Buy claims `v0.5.41` is tagged, ACCEPT CLOSED,
"executed," "Safety allow," "we fly," "LAND on copper," "GO_TO in air,"
or "house map." Confirmed via `git tag -l | sort -V | tail -6` at close
of this Buy: `v0.5.34`, `v0.5.35`, `v0.5.37`, `v0.5.38`, `v0.5.39`,
`v0.5.40` — `v0.5.41` does not exist yet.

---

## 9. Residual / next steps

- C41 (safety-sim policy, allowlist for what C40 can command) is next per the IC's own handoff, after Cursor review + Engineer ★ ACCEPT + tag `v0.5.41`. Assistant/placement work stays PARKED until C43.
- The pre-existing MCU-toolchain environment issue (disclosed in C36's own report) remains unfixed, unrelated to this Buy.
- Combined-axis `GO_TO` targets (nonzero `x_m` and `y_m` simultaneously) converge correctly but slowly (~2500-3000 steps observed in scratch verification, vs. ~1500 for a single-axis target) due to coupled roll+pitch transient oscillation — not a bug, but a tuning characteristic of `PositionController`'s existing C39 gains that a future Buy tuning that controller (out of this Buy's scope) may want to revisit. This Buy's own formal tests use single-axis targets specifically to keep step counts and test runtime small, not to hide the combined-axis behavior — it is disclosed here.
- `SimAutonomyExecutor`'s frozen-anchor state is per-instance, in-memory only — no persistence, no resumption across process restarts, matching every other stateful object in this ladder.

---

## 10. Acceptance self-check vs IC §4 (Acceptance)

- T1-T9: ✅ T1-T5/T7/T8 in Python (9/9 passing), T1-T4 equivalents in C++ Catch2 (4/4 passing, matching "at least T1+T3+T4" plus the T2 HOLD case), T8's suite/ctest half in §3, T9 in this report.
- Three verbs drive plant in sim: ✅ `GO_TO`/`HOLD`/`LAND` all verified against `ToyQuad6DofPlant` in both languages.
- C4 RejectAll intact: ✅ `test_t5_...` re-verifies `propose_command`/`submit_command` through `default_safety_gate()` for all three verbs.
- Version `0.5.41`: ✅ `pyproject.toml` + all 45 checkpoint tests re-pinned.

**PASS** against every criterion in IC §4. **FAIL conditions**
(`"executed"`, Safety allowlist, plant inside `step`, craft wiring, "we
fly") — none present, verified above.
