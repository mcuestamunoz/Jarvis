# Implementation Contract — Fase C control-loop tick (`B1-fase-c-control-loop-tick`)

**Project:** Jarvis  
**Date:** 2026-09-22  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (`step()` ≠ flying · plant stays outside the tick · no GPIO/DShot · no RC→setpoint · C11 recovery still holds · C++ twin is the board-shaped name, not a flash)

**Status:** ★ ACCEPT CLOSED @ **`v0.5.22`**  
**Parents:**
- [C11 ★ ACCEPT](implementation_contract_fase_c_controlled_flight_sim_tip_b1.md) — toy closed-loop smoke @ **`v0.5.9`** (loop **inlined** in `run_controlled_flight_sim_smoke`)  
- [C12 ★ ACCEPT](implementation_contract_fase_c_rate_torque_bridge_b1.md) — `LinearRateTorqueBridge` @ **`v0.5.10`**  
- [C13 ★ ACCEPT](implementation_contract_fase_c_cpp_flight_control_scaffold_b1.md) — C++ smoke **inlined** in `fc_closed_loop_smoke` @ **`v0.5.11`**  
- [C14 ★ ACCEPT](implementation_contract_fase_c_cpp_esc_pwm_stub_b1.md) — C++ ESC stub @ **`v0.5.12`**  
- [C23 ★ ACCEPT](implementation_contract_fase_c_crsf_host_baud_b1.md) — host baud @ **`v0.5.21`** (radio path **not** wired into this tick)  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no flash, craft↔FS, GPIO, Safety execute, RC mapping, MCU UART, or silicon map in this Buy  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — extract a **named one-cycle control tick** (`step`) from the inlined C11/C13 smokes: IMU sample + attitude setpoint + collective **in** → filter → estimate → PD → rate-torque → mixer → `MotorForceCommand` **out**. Plant, ESC pin, RC, and timers stay **outside**.  
**Package:** bump Jarvis `pyproject.toml` to **`0.5.22`**; git tag **`v0.5.22`** only after Engineer ACCEPT.  
**Not** flying · not hardware-verified control · not GPIO/DShot · not RC→setpoint (C25) · not EscOutput HAL swap (C26) · not CRSF failsafe (C27) · not MCU UART (C28) · not silicon/FLASH map (C29) · not calling `step` from `Reset_Handler` · not Safety `allow` → execute · not craft↔FS.

**Outputs (required):**
1. Python module `src/jarvis/flight_software/flight_control/loop.py` (preferred name) — **do not** reimplement filter/attitude/controller/bridge/mixer  
2. C++ twin `native/flight_control/include/jarvis/fc/loop.hpp` + `src/loop.cpp`, added to `jarvis_fc` — **same order**, reuse existing rung classes  
3. C11 `run_controlled_flight_sim_smoke` and C13 `fc_closed_loop_smoke` **call** this tick (plant remains the `for`-loop world). Recovery criterion **unchanged** (tilt still decreases / recovers)  
4. Tests: `tests/test_fase_c_control_loop_tick_b1.py` + at least one Catch2 case for the C++ tick  
5. `.jes/artifacts/implementation_report_fase_c_control_loop_tick_b1.md`  
6. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **named tick ≠ flying ≠ MCU ISR ≠ motors**  
7. `pyproject.toml` → **`0.5.22`** (+ re-pin `0.5.21` version-checkpoint tests)

**Checkpoint:** package **`0.5.22`** · Python suite ≥ **3504** + new tests · host `ctest` still green · C11/C13 recovery still holds · Safety default unchanged

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-control-loop-tick`** — name the one-cycle FC tick so a future MCU timer has **one function to call** |
| 2 | One front | Do **not** fold RC→setpoint, Esc HAL redesign, CRSF timeout failsafe, MCU UART, silicon/FLASH map, GPIO/DShot, Safety execute, craft↔FS, or flash into this Buy |
| 3 | What this Buy demonstrates | The C11/C13 inlined body is a **named `step`**. **Human:** “el corazón del FC ya tiene nombre; la placa no tendrá que redescubrir el orden de las piezas.” |
| 4 | Split tick vs world | **`step` does not call the plant** and does **not** read a real IMU or write a pin. Caller supplies `ImuSample`; caller consumes `MotorForceCommand`. Smoke: `out = loop.step(...)` then `plant.step(out.forces, dt)` |
| 5 | Order (locked) | `filter_sample` → `estimator.update` → `controller.compute(setpoint, state)` → `bridge.convert` → `mixer.mix(collective, torque)` — **exactly** the C11/C13 order. Do not add altitude/position/rate-PID |
| 6 | Languages | **Both** in this Buy (one concept, two trees already on disk). Python = wooden contract + pytest. C++ = what the board will eventually call. Do **not** invent a third loop in `vehicle_profiles/` that bypasses `loop.py` |
| 7 | Behavior freeze | C11 tilt-error still **strictly decreases** and recovers under the existing documented threshold after 200 steps / 15° IC. C13 smoke still exits 0. **Forbidden:** retuning gains “to make extraction nicer” |
| 8 | PWM | Optional: tick **may** also return `encode_motor_forces(forces)` for visibility. Plant dynamics **must not** require PWM (C11 lock). Do not call `SimulatedEscSink.apply` inside `step` |
| 9 | No timer | `dt` is **not** an argument of `step`. Estimator/controller keep using `ImuSample.t_s` as today. A hardware 1 kHz ISR is a later Buy |
| 10 | No RC | `AttitudeSetpoint` + `collective` are **arguments**. Smoke still uses `level_setpoint` + hover collective. Mapping sticks → those args is **C25** |
| 11 | No boot loop | `mcu/stub_main.cpp` / `Reset_Handler` **must not** start calling `step` in a spin. Symbol may exist in `jarvis_fc.a`; it is not “the FC is running on MCU” |
| 12 | Safety / autonomy | Untouched. Tick never calls `SafetyGate.evaluate` or `submit_command` |
| 13 | `RadioIntentAdapter` | Remains NotImplemented |
| 14 | Version | Bump **`0.5.21` → `0.5.22`**; tag **`v0.5.22`** on ACCEPT only |
| 15 | Forbidden claims | “We fly” · “MCU ISR” · “motors spinning” · “almost flies” · “board-ready firmware” · radio/capability `available` |

**Product sentence:**

```text
Un ciclo de control con nombre: IMU + consigna + collective → fuerzas
de motor, reutilizando C6–C12/C13, planta y pines fuera — el tick que
un timer de MCU podrá llamar, no un dron que vuele.
```

**Defaults locked by Cursor (Engineer pick 2026-09-22: step / base-for-board #1):**
- New **`loop.py`** + C++ **`loop.hpp`/`loop.cpp`**  
- `FlightControlLoop.step` / `jarvis::fc::ControlLoop::step` (names flexible; report them)  
- Plant **outside** the tick  
- Smokes **refactored to call** it; gains/recovery frozen  
- No RC, no GPIO, no `Reset_Handler` loop  

---

## 1. Package layout (normative intent)

```text
src/jarvis/flight_software/flight_control/
  loop.py                 # NEW — named tick
  filter.py … mixer.py    # UNCHANGED math
  plant.py                # UNCHANGED; smoke still owns plant.step

src/jarvis/vehicle_profiles/smoke.py
  run_controlled_flight_sim_smoke  # MUST call loop.step (not a third copy of the chain)

native/flight_control/
  include/jarvis/fc/loop.hpp
  src/loop.cpp              # add to add_library(jarvis_fc …)
  smoke/closed_loop_smoke.cpp   # MUST call ControlLoop::step
  tests/test_loop.cpp       # NEW Catch2 case(s)
```

Do **not** put the tick under `capabilities/`. Do **not** import CRSF/serial into `loop.py`.

---

## 2. Types / APIs (normative intent)

Exact names may vary; report must list them. Prefer:

```text
ControlTickResult
  t_s
  filtered: ImuSample
  state: AttitudeState
  rate_cmd: BodyRateCommand
  torque_cmd: BodyTorqueCommand
  forces: MotorForceCommand
  pwm: EscPwmCommand | None   # optional; if present, encoded from forces

FlightControlLoop
  holds: filter, estimator, controller, bridge, mixer
    (injected or default-constructed with existing defaults)

  step(sample: ImuSample, setpoint: AttitudeSetpoint, collective: float)
      -> ControlTickResult
```

C++: same fields/order in `jarvis::fc`. Collective is a `double` in `[0, 1]` as mixer already clips.

`step` before the loop object is constructed → typed error or documented impossible (report).

### 2.1 Explicit non-goals

No plant inside `step`, no `ImuHal.read` inside `step`, no GPIO, no DShot, no `fcntl`/`termios`, no CRSF, no Safety, no Intent, no background thread, no 1 kHz claim, no `Reset_Handler` spin.

---

## 3. Integration rules

| Existing | C24 rule |
|---|---|
| C6–C12 Python rungs | **Called**, not rewritten |
| C11 smoke | Uses `loop.step`; recovery tests stay green |
| C13–C15 C++ | `loop.cpp` in `jarvis_fc`; smoke uses it; `ctest` green |
| C16/C18 MCU | Library may contain the new `.o`; **no** stub_main control loop |
| C4 / C17 | Untouched |
| C19–C23 radio | Untouched; **not** imported by `loop.py` / `loop.cpp` |
| Craft | Untouched |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | `step` returns `ControlTickResult` with `forces` length 4, finite |
| T2 | Order: spy/sequence or source — filter then estimate then PD then bridge then mix (no plant call inside `step`) |
| T3 | C11 `run_controlled_flight_sim_smoke` still strictly decreases tilt error from 15° / 200 steps (existing assertion) |
| T4 | Open-loop baseline smoke still does **not** recover (existing C11 contrast) |
| T5 | `step` does not import/call `plant.step` / GPIO / serial / `submit_command` / CRSF (real code, comments stripped) |
| T6 | C++ Catch2: one tick produces four finite motor forces; `fc_closed_loop_smoke` still exits 0 |
| T7 | `stub_main.cpp` still has no `ControlLoop` / `step(` control cycle |
| T8 | `RadioIntentAdapter` still `not_implemented`; `default_safety_gate()` RejectAll |
| T9 | Registry empty; no craft/`core` imports of `loop.py` |
| T10 | `pyproject` **`0.5.22`**; re-pin `0.5.21` |
| T11 | Full Python suite green; host `ctest` green |
| T12 | Report: named tick ≠ flying ≠ MCU ISR ≠ motors; plant/RC/ESC-pin remain later cola |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| “Almost flies” / “board-ready FC” | Tick is a name, not a vehicle |
| Plant inside `step` | Would couple sim-world to the MCU-callable tick |
| GPIO / DShot / pigpio | No plate |
| RC channel mapping | C25 |
| Failsafe timeout | C27 |
| Calling `step` from reset | Fake firmware main loop |
| Safety execute | C17 allow ≠ execute |
| Flash / craft↔FS | Process lock |

Honesty line (report + living docs):

```text
Named control tick ≠ flying ≠ MCU ISR ≠ motors ≠ RC sticks
```

**Exists:** one named cycle: IMU+setpoint+collective → motor forces (Python + C++), smokes call it.  
**Impossible:** a running FC on a board; sticks flying the craft; ESC on a wire.

---

## 6. Docs

- PRIORIDAD: C24 in flight / CLOSED as appropriate  
- PLATFORM §13: C24 tick block + honesty line; C25–C29 remain parked queue  
- ARCHITECTURE: short note under `flight_control/`  
- README “What v0.5.22 includes”  
- `loop.py` / `loop.hpp` docstring: Python scaffold / C++ host; production ISR is a later IC  

---

## 7. Acceptance

**PASS when:** T1–T12 · smokes call `step` · C11/C13 recovery unchanged · no plant/GPIO/RC inside the tick · `stub_main` idle · version `0.5.22` · docs honest.

**FAIL if:** third copy of the chain left as the smoke source of truth · plant folded into `step` · `Reset_Handler` runs the loop · GPIO/DShot · RC mapping · “we fly” / “almost flies” in living docs · Safety execute.

---

## 8. Handoff

```text
Engineer → ★ this IC (C24)
Claude   → extract step Python+C++ + refactor smokes + report + 0.5.22
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.22
Cursor   → next Buy when Engineer prioritizes (C25 RC→setpoint default-next on this axis)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C23 CLOSED @ v0.5.21. C24 B1-fase-c-control-loop-tick READY —
named IMU→forces tick (Python+C++; plant outside); not flying;
not MCU ISR; not motors.
```

---

## 10. Engineer ★ checklist

1. Confirm buy = **name the control tick** (extract, don’t add physics) OK?  
2. **Python + C++** in this Buy OK?  
3. Plant / RC / ESC-pin / failsafe / UART / silicon **out** OK?  
4. Smokes must **call** `step`; recovery frozen OK?  
5. Version **`0.5.22`** OK?  
6. `Reset_Handler` stays a stub OK?  
