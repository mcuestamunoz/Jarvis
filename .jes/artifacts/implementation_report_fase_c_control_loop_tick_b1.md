# Implementation Report — Fase C control-loop tick (`B1-fase-c-control-loop-tick`)

**IC:** [`implementation_contract_fase_c_control_loop_tick_b1.md`](implementation_contract_fase_c_control_loop_tick_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-22
**Status:** ★ ACCEPT CLOSED @ **`v0.5.22`** (Cursor review PASS WITH NOTES). Package **`0.5.22`**.

---

## 0. Read this first — honesty summary

This Buy adds **no new control math**. It extracts the body that C11's
`run_controlled_flight_sim_smoke` and C13's `fc_closed_loop_smoke` already
ran **inlined**, and gives it one name in each language:

- Python: `FlightControlLoop.step(sample, setpoint, collective) -> ControlTickResult`, in `src/jarvis/flight_software/flight_control/loop.py`.
- C++: `jarvis::fc::ControlLoop::step(sample, setpoint, collective) -> ControlTickResult`, in `native/flight_control/include/jarvis/fc/loop.hpp` + `src/loop.cpp`.

Both call the **existing** rungs (`filter.py`/`filter.hpp` … `mixer.py`/`mixer.hpp`, plus C10's `encode_motor_forces` for the optional PWM field) in the exact order C11/C13 already used:
`filter_sample -> estimator.update -> controller.compute -> bridge.convert -> mixer.mix`.

**`step` does not call the plant, does not read a real IMU, and does not write a pin.** The caller (the two refactored smokes, in this Buy) still owns `plant.step(result.forces, dt)`. There is no `dt` argument, no RC decoding, no PWM actuation, no Safety call, and no `Reset_Handler` wiring anywhere in this Buy.

**Named control tick != flying != MCU ISR != motors != RC sticks.**

**Exists:** one named cycle, IMU sample + attitude setpoint + collective in, four motor forces (plus PWM-µs for visibility) out, in Python and C++, both smokes now calling it by name. **Impossible:** a running FC on a board; sticks flying the craft; an ESC on a wire. Nothing in this Buy is any of those.

---

## 1. Package layout vs IC §1

```text
src/jarvis/flight_software/flight_control/
  loop.py                 # NEW — FlightControlLoop.step
  filter.py … mixer.py    # UNCHANGED (git diff --stat empty)
  plant.py                # UNCHANGED; smoke still owns plant.step

src/jarvis/vehicle_profiles/smoke.py
  run_controlled_flight_sim_smoke  # refactored to call loop.step

native/flight_control/
  include/jarvis/fc/loop.hpp   # NEW
  src/loop.cpp                  # NEW — added to add_library(jarvis_fc ...)
  smoke/closed_loop_smoke.cpp   # refactored to call ControlLoop::step
  tests/test_loop.cpp           # NEW Catch2 cases (3)
```

`loop.py` lives under `flight_control/`, not `capabilities/` (per IC §1's explicit instruction). No CRSF/serial import anywhere in `loop.py`/`loop.hpp`/`loop.cpp` (confirmed by grep, §7 below).

`flight_control/__init__.py` now also exports `ControlTickResult`/`FlightControlLoop`, matching every sibling rung's own export (filter/attitude/controller/rate_torque/mixer/esc all already were).

---

## 2. Types / API implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| `ControlTickResult` (`t_s`, `filtered`, `state`, `rate_cmd`, `torque_cmd`, `forces`, `pwm`) | §2 | ✅ Pydantic `BaseModel` (Python), plain struct (C++) — same field names/order in both languages |
| `FlightControlLoop` / `ControlLoop` holding filter/estimator/controller/bridge/mixer, injected or default-constructed | §2 | ✅ both constructors accept `None`/default-constructed instances of each rung; smokes inject their own tuned instances (same gains they used before extraction) |
| `step(sample, setpoint, collective) -> ControlTickResult` | §2 | ✅ exact signature in both languages; no `dt` argument |
| `pwm: EscPwmCommand \| None` | §2 | Implemented as **always populated** (`EscPwmCommand`, not `Optional`) — encoded via C10's own `encode_motor_forces(forces)` every call. The IC's own wording ("optional: tick **may** also return `encode_motor_forces(forces)` for visibility") describes an optional *feature* of the API, not a sometimes-`None` field; always populating it keeps the locked 3-argument signature exactly as specified (§2, no extra flag) while still satisfying "if present, encoded from forces" — it is always present, always encoded from `forces`, never from anything else. `SimulatedEscSink.apply` is never called (verified §7). |
| `step` before construction → typed error or documented impossible | §2 | **Documented impossible**: `step` is a bound instance method — Python's own method-binding rules make an unbound call raise `TypeError` at the language level (`test_step_before_construction_is_a_language_level_typeerror`); C++ has no free-function `step` to call without an instance at all — there is nothing to construct-before-call in that language's own type system. No special-case guard code was added in either language, per the IC's own "or documented impossible" option. |

### 2.1 Explicit non-goals (IC §2.1) — confirmed absent

No plant inside `step`, no `ImuHal.read` inside `step`, no GPIO, no DShot, no `fcntl`/`termios`, no CRSF, no Safety, no Intent, no background thread, no 1 kHz claim, no `Reset_Handler` spin — confirmed by source grep (§7) and by `test_t2b_step_source_never_calls_plant_step` / `test_t5_step_imports_no_gpio_serial_submit_command_or_crsf`.

---

## 3. Integration rules vs IC §3

| Existing | This Buy |
|---|---|
| C6–C12 Python rungs | Called via `FlightControlLoop.__init__`'s stored instances, never rewritten (`git diff --stat` on `filter.py`/`attitude.py`/`controller.py`/`rate_torque.py`/`mixer.py`/`esc.py` is **empty**) |
| C11 smoke (`run_controlled_flight_sim_smoke`) | Refactored to construct a `FlightControlLoop` from the same rung instances it already built, and call `loop.step(sample, setpoint, collective)` once per iteration instead of inlining the five calls. Recovery test (`test_fase_c_controlled_flight_sim_tip_b1.py::test_t2_closed_loop_tilt_error_strictly_decreases`) stays green unmodified. |
| C13–C15 C++ | `loop.cpp` added to `add_library(jarvis_fc ...)` in `CMakeLists.txt`; `fc_closed_loop_smoke` refactored to construct a `ControlLoop` and call `.step(...)`; `ctest` green (31/31, up from 28) |
| C16/C18 MCU | `loop.cpp`/`loop.hpp` compile into `libjarvis_fc.a` on the cross-compile path too (verified — see §6) — but `mcu/stub_main.cpp` is **untouched** (`git diff --stat` empty), still no `ControlLoop`/`step(` reference anywhere in it |
| C4 / C17 | Untouched (`flight_software/autonomy/`, `safety.py` both `git diff --stat` empty) |
| C19–C23 radio/CRSF | Untouched (`radio.py`, `crsf_stub.py`, `crsf_dual_role.py`, `crsf_stream.py`, `crsf_serial.py`, `intent.py` all `git diff --stat` empty); none imported by `loop.py`/`loop.hpp`/`loop.cpp` |
| Craft | Untouched — no `core/`/`adapters/` file references `flight_control.loop` or `FlightControlLoop` (grep-verified, `test_t9`) |

---

## 4. Behavior-freeze verification (empirical, before any formal test)

Before writing `loop.py`, and again after wiring it into the smokes, I ran ad-hoc scripts comparing the refactored path against the pre-refactor inlined chain:

```text
Pre-refactor inlined chain (same construction as before this Buy):
  initial tilt error: 15.000000000000027 deg
  final tilt error:   0.2519776947664161 deg (200 steps)

Post-refactor (loop.step, same injected rung instances):
  bit-identical: True
  max diff: 0.0
```

Same result confirmed via the actual `run_controlled_flight_sim_smoke()` call after the refactor landed — `201` entries, `errors[-1] < errors[0]`, `errors[-1] < radians(2°)`, identical numeric value `0.2519776947664161` rad-equivalent-degrees to the pre-refactor run.

C++ side: `fc_closed_loop_smoke` printed, before and after the refactor:

```text
initial tilt error: 15.000 deg
final tilt error:   0.252 deg (after 200 steps)
PASS: tilt error strictly decreased and recovered below 2.0 deg
```

identical to the documented C13/C14/C15 report value — **no gain was retuned** anywhere in this Buy, satisfying IC §0 decision 7's explicit "forbidden: retuning gains 'to make extraction nicer.'"

---

## 5. Tests run

### 5.1 Python — new module

`tests/test_fase_c_control_loop_tick_b1.py` — **16 tests**, covering IC §4's T1–T5 and T7–T10 (T6 is the C++ Catch2 case, T11 is the process-gate full-suite run, T12 is this report):

| Test | Covers |
|---|---|
| `test_t1_step_returns_control_tick_result_with_four_finite_forces` | T1 |
| `test_t2_order_filter_then_estimate_then_pd_then_bridge_then_mix` | T2 (spy sequence) |
| `test_t2b_step_source_never_calls_plant_step` | T2 (no plant call inside `step`, source-level) |
| `test_t3_c11_smoke_still_strictly_decreases_and_recovers` | T3 |
| `test_t4_open_loop_baseline_still_does_not_recover` | T4 |
| `test_t5_step_imports_no_gpio_serial_submit_command_or_crsf` | T5 |
| `test_t7_refactored_smoke_matches_pre_refactor_inlined_reference` | behavior-freeze (bit-identical) |
| `test_t8_radio_intent_adapter_still_not_implemented_and_safety_default_unchanged` | T8 |
| `test_t9_registry_empty_and_no_craft_or_core_imports_of_loop` | T9 |
| `test_t10_pyproject_version_is_0_5_22` | T10 |
| `test_t11_full_suite_process_gate_placeholder` | T11 marker (real gate is the full-suite run below) |
| `test_step_before_construction_is_a_language_level_typeerror` | IC §2 "typed error or documented impossible" |
| `test_default_construction_matches_existing_rung_defaults` | default-constructed loop sanity |
| `test_pwm_field_is_populated_and_encoded_from_forces` | `pwm` field contract |
| `test_loop_py_has_no_cpp_or_cmake_and_is_not_under_capabilities` | IC §1 "do not put the tick under `capabilities/`" |
| `test_setpoint_and_collective_are_plain_arguments_no_rc_decoding` | IC §0 decision 10 (no RC) |

```text
tests/test_fase_c_control_loop_tick_b1.py: 16 passed
```

### 5.2 Full Python suite

```text
3520 passed, 2 skipped in 5.55s
```

Baseline before this Buy: `3504 passed, 2 skipped`. Delta: **+16**, exactly matching the new test count — zero regressions, zero other files' test counts changed.

### 5.3 C++ — new Catch2 cases + full host `ctest`

`native/flight_control/tests/test_loop.cpp` — 3 new `TEST_CASE`s:

1. `ControlLoop::step: one tick produces four finite motor forces` (IC T6)
2. `ControlLoop::step: does not call the plant (forces feed it, step never reads it)`
3. `ControlLoop::step: matches the inlined C13 smoke chain bit-for-bit` (`WithinAbs(..., 1e-9)`)

```text
$ cmake -S native/flight_control -B build/flight_control
$ cmake --build build/flight_control -j4     # clean build, zero warnings
$ ctest --output-on-failure
100% tests passed out of 31

Total Test time (real) = 0.64 sec
```

Baseline before this Buy: 28 host tests. Delta: **+3**, exactly the new `TEST_CASE` count. `fc_closed_loop_smoke` and `fc_esc_pwm_smoke` both still pass (tests #30, #31).

### 5.4 MCU cross-compile re-verification (not required by IC §4, done for completeness)

```text
$ cmake -S native/flight_control -B build/flight_control_mcu \
    -DCMAKE_TOOLCHAIN_FILE=native/flight_control/cmake/toolchains/arm-none-eabi.cmake
$ cmake --build build/flight_control_mcu -j4
[  7%] Building CXX object CMakeFiles/jarvis_fc.dir/src/loop.cpp.obj
[ 15%] Linking CXX static library libjarvis_fc.a
[ 69%] Built target jarvis_fc
[ 76%] Linking CXX executable fc_mcu_stub.elf
[100%] Built target fc_mcu_stub.elf
```

`loop.cpp` compiles cleanly into `libjarvis_fc.a` on the ARM cross target too (Cortex-M4, same toolchain as C16/C18), and `fc_mcu_stub.elf` still links — but `stub_main.cpp` was not touched (`git diff --stat` empty) and still never references `ControlLoop`/`step(` (grep, exit 1 = no match). The tick's C++ symbols are reachable from the MCU library the same way every other rung's symbols already were since C16 — this does not change the "no `Reset_Handler` spin" honesty line.

---

## 6. Honesty / forbidden — confirmed

| Forbidden (IC §5) | Verified absent |
|---|---|
| "Almost flies" / "board-ready FC" | Not present in `loop.py`/`loop.hpp`/`loop.cpp`, docs, or this report |
| Plant inside `step` | Grep + `test_t2b`: no `plant.step(`/`ToyQuadAttitudePlant` reference in `loop.py`'s real code |
| GPIO / DShot / pigpio | Grep clean across new/changed files (only honesty-prose mentions of their *absence*, in comments) |
| RC channel mapping | `step`'s only inputs are `sample`/`setpoint`/`collective` — plain arguments, no decode logic anywhere |
| Failsafe timeout | Not present — out of scope, not touched |
| Calling `step` from reset | `stub_main.cpp` byte-unchanged, grep confirms no `ControlLoop`/`step(` reference |
| Safety execute | `loop.py`/`loop.hpp`/`loop.cpp` never reference `SafetyGate`/`submit_command`/`propose_command` (grep + `test_t5`, `test_t8`) |
| Flash / craft↔FS | Not touched — no `core/`/`adapters/` file references the new symbols (`test_t9`) |

Honesty line, shipped verbatim in this report and in the docs updated below:

```text
Named control tick != flying != MCU ISR != motors != RC sticks
```

---

## 7. Module-boundary / forbidden-symbol grep (run at close of this Buy)

```text
$ git diff --stat -- src/jarvis/capabilities/ src/jarvis/flight_software/autonomy/ native/flight_control/mcu/
(empty)

$ grep -inE "gpio|dshot|pigpio|submit_command|crsf|elrs|reset_handler" \
    src/jarvis/flight_software/flight_control/loop.py \
    native/flight_control/include/jarvis/fc/loop.hpp \
    native/flight_control/src/loop.cpp \
    native/flight_control/smoke/closed_loop_smoke.cpp \
    src/jarvis/vehicle_profiles/smoke.py
# only honesty-prose comments disclosing their absence ("no GPIO/PWM/DShot/serial") — no real usage

$ grep -n "Reset_Handler\|ControlLoop\|step(" native/flight_control/mcu/stub_main.cpp
# no match (exit 1)
```

`git status --short` at close of this Buy shows exactly the expected file set: `loop.py`, `loop.hpp`, `loop.cpp`, `test_loop.cpp`, `test_fase_c_control_loop_tick_b1.py` (new), plus `__init__.py`/`smoke.py`/`CMakeLists.txt`/`closed_loop_smoke.cpp` (modified to wire the tick in), plus `pyproject.toml` + 29 version-checkpoint test re-pins + docs. No `capabilities/`, `autonomy/`, or `mcu/` files touched.

---

## 8. Files changed

**New:**
- `src/jarvis/flight_software/flight_control/loop.py`
- `native/flight_control/include/jarvis/fc/loop.hpp`
- `native/flight_control/src/loop.cpp`
- `native/flight_control/tests/test_loop.cpp`
- `tests/test_fase_c_control_loop_tick_b1.py`
- `.jes/artifacts/implementation_report_fase_c_control_loop_tick_b1.md` (this file)

**Modified:**
- `src/jarvis/flight_software/flight_control/__init__.py` (export `ControlTickResult`/`FlightControlLoop`)
- `src/jarvis/vehicle_profiles/smoke.py` (`run_controlled_flight_sim_smoke` now calls `loop.step`; docstring updated)
- `native/flight_control/CMakeLists.txt` (`src/loop.cpp` added to `jarvis_fc`; `tests/test_loop.cpp` added to `fc_unit_tests`)
- `native/flight_control/smoke/closed_loop_smoke.cpp` (now calls `ControlLoop::step`)
- `native/flight_control/README.md` (Layout + a new C24 paragraph)
- `pyproject.toml` (`0.5.21` → `0.5.22`)
- 29 pre-existing test files re-pinned from `0.5.21` to `0.5.22` (28 via the `'version = "X.Y.Z"' in text` literal pattern, 1 additional set of 4 files via a `re.search(...) == "X.Y.Z"` regex-checkpoint pattern found during this Buy's own re-pin sweep — see §9)
- `README.md`, `docs/ARCHITECTURE.md`, `docs/PLATFORM_CAPABILITY_VISION.md`, `docs/IMPLEMENTATION_TASKS.md` (see §10)

---

## 9. Process note — a second version-checkpoint pattern found

While re-pinning the literal `'version = "0.5.21"' in text` checkpoint tests (28 files, the pattern every prior Buy in this thread re-pinned), the full-suite run surfaced 4 additional failures using a **different** checkpoint style — `re.search(r'(?m)^version\s*=\s*"([^"]+)"', text); assert match.group(1) == "0.5.21"` — in `tests/test_catalog_camera_power_w_b1.py`, `tests/test_library_cameras_seed_b1.py`, `tests/test_mission_power_w_b1.py`, `tests/test_mission_vtx_identity_b1.py`. These are outside the Fase C CRSF/flight-control test family (Fase M mission tests) and were not part of any prior Fase C re-pin grep in this session's history. Re-pinned to `"0.5.22"` the same way; full suite confirmed green afterward (`3520 passed, 2 skipped`, zero other regressions). No production code was touched to fix this — purely a version-string checkpoint update, same category as the other 28.

---

## 10. Docs updated (honesty confirmed — not claiming CLOSED/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.22 includes (working tree — not yet tagged)" section, explicitly says "no `v0.5.22` tag yet."
- `docs/ARCHITECTURE.md` §1c — new C24 paragraph after the C23 block, top banner updated to "Working tree ahead: package `0.5.22` ... awaiting Cursor review + Engineer ★ ACCEPT — no `v0.5.22` tag yet."
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C24 block, same "landed — awaiting ... no tag yet" phrasing, honesty line verbatim.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner and the C24 table row both changed to "Landed — awaiting Cursor review + ★ ACCEPT (no `v0.5.22` tag yet)."
- `native/flight_control/README.md` — Layout section + new paragraph on `loop.hpp`/`loop.cpp`.

No file in this Buy claims `v0.5.22` is tagged or ACCEPT CLOSED. Confirmed via `git tag -l | sort -V | tail -3` at close of this Buy: `v0.5.19`, `v0.5.20`, `v0.5.21` — `v0.5.22` does not exist yet.

---

## 11. Residual / next steps

- C25 (RC → attitude/collective setpoint) is next in the parked queue, per the IC's own handoff — explicitly **not** started here; `step`'s `setpoint`/`collective` arguments stay plain, undecoded values in this Buy.
- C26 (EscOutput HAL), C27 (CRSF stream-timeout failsafe), C28 (MCU UART HAL stub), C29 (silicon + cited FLASH map) all remain parked, untouched.
- `stub_main.cpp` remains an idle one-shot exercise of two unrelated rung APIs (from C18) — this Buy did not add `ControlLoop`/`step` to it, and no future Buy should either without a dedicated, explicitly-approved IC for an actual MCU timer/ISR.

---

## 12. Acceptance self-check vs IC §7

- T1–T5, T7–T10 (Python): ✅ all pass, 16/16 new tests green.
- T6 (C++ Catch2): ✅ 3 new cases pass; `fc_closed_loop_smoke` still exits 0.
- T11 (full suite + `ctest` green): ✅ `3520 passed, 2 skipped` (Python); `31/31` (`ctest`).
- T12 (this report's honesty content): ✅ this section.
- Smokes call `step`: ✅ both `run_controlled_flight_sim_smoke` and `fc_closed_loop_smoke` refactored, no third copy of the chain left as source of truth.
- C11/C13 recovery unchanged: ✅ bit-identical (Python) / identical printed value (C++).
- No plant/GPIO/RC inside the tick: ✅ grep + tests.
- `stub_main` idle: ✅ byte-unchanged, no `ControlLoop`/`step(` reference.
- Version `0.5.22`: ✅ `pyproject.toml` + all 29 checkpoint tests re-pinned.
- Docs honest: ✅ §10 above — no premature CLOSED/tag claim anywhere.

**PASS** against every criterion in IC §7. **FAIL conditions** (third copy of the chain, plant folded into `step`, `Reset_Handler` running the loop, GPIO/DShot, RC mapping, "we fly"/"almost flies" in living docs, Safety execute) — none present, verified above.
