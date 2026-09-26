# Implementation Contract — Fase C sim 6-DoF plant (`B1-fase-c-sim-6dof-plant`)

**Project:** Jarvis  
**Date:** 2026-09-26  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (6-DoF toy ≠ flying ≠ product aero · plant stays **outside** `step` · C11 attitude plant still recovers)

**Status:** ★ **ACCEPT CLOSED** @ tag **`v0.5.37`** (Engineer 2026-09-26) · Cursor review PASS WITH NOTES  
**Parents:**
- [Month note](engineer_note_software_month_until_bench_2026_09_26.md) — **C36 first** after D2; finish flight-control software before Assistant  
- [C11 ★ ACCEPT](implementation_contract_fase_c_controlled_flight_sim_tip_b1.md) — `ToyQuadAttitudePlant` attitude-only @ **`v0.5.9`**  
- [C24 ★ ACCEPT](implementation_contract_fase_c_control_loop_tick_b1.md) — named `step()`; plant **outside** @ **`v0.5.22`**  
- [C35 ★ ACCEPT](implementation_contract_fase_c_step_failsafe_hold_ticks_b1.md) — many ticks without plant @ **`v0.5.33`**  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — add a **toy 6-DoF rigid-body plant**: `MotorForceCommand` → advances **attitude + position + velocity** in ENU, emits next `ImuSample` for the existing ladder. Prerequisite for later yaw/alt/pos/executor Buys.  
**Package:** bump `pyproject.toml` **`0.5.36` → `0.5.37`**; git tag **`v0.5.37`** only after Engineer ACCEPT.  
*(Package tip may already show `0.5.36` from D2 docs; tagged tip may still be `v0.5.35` until D2 ACCEPT — this Buy owns **`0.5.37` / `v0.5.37`**.)*

**Not** flying · not product aero/CFD · not mass/inertia cited from MY5 · not altitude/position **controller** (C38/C39) · not mag (C37) · not autonomy executor (C40) · not Safety deepen (C41) · not ICM client (C42) · not craft↔FS (C43) · not GPIO/DShot wire · not C30 DFU · not Assistant · not folding plant into `FlightControlLoop.step`.

**Outputs (required):**
1. Production code: extend `src/jarvis/flight_software/flight_control/plant.py` (preferred) **or** one new sibling module under the same package — **one** new 6-DoF plant type; do **not** delete or silently rewrite `ToyQuadAttitudePlant`  
2. C++ twin under `native/flight_control/` (`plant.hpp` / `plant.cpp` or adjacent files) — same behavior, host tests  
3. Tests: `tests/test_fase_c_sim_6dof_plant_b1.py` + Catch2 case(s)  
4. Thin smoke helper (Python; C++ optional mirror) that runs `loop.step` → `plant.step` and shows **pose moves** under a documented thrust+tilt case  
5. `.jes/artifacts/implementation_report_fase_c_sim_6dof_plant_b1.md`  
6. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **6-DoF toy ≠ flying ≠ product physics**  
7. `pyproject.toml` → **`0.5.37`** (+ re-pin `0.5.36` version-checkpoint tests)

**Checkpoint:** package **`0.5.37`** · Python suite green + new tests · host `ctest` green · C11 tilt-recovery smoke **still** passes on `ToyQuadAttitudePlant`

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-sim-6dof-plant`** — toy plant with **pose** (x,y,z) + velocity + attitude |
| 2 | One front | Do **not** fold mag, altitude loop, position loop, executor, Safety policy, ICM client, craft↔FS, GPIO/DShot, C30 DFU, Assistant, or Taller/standoff |
| 3 | What this Buy demonstrates | The forces that leave `step()` can move a **body in space** in RAM, not only tilt it. **Human:** “ya hay un mundo de juguete donde la nave tiene sitio; los lazos de altura y posición tendrán algo que sentir.” |
| 4 | Keep C11 plant | **`ToyQuadAttitudePlant` stays.** Behavior and C11/C13 closed-loop tilt recovery **frozen**. New type alongside (name locked below). Do **not** break existing tests by changing C11 dynamics defaults |
| 5 | New type (locked name) | **`ToyQuad6DofPlant`** — Python + C++. Tracks: `position_m` ENU `(x,y,z)`, `velocity_mps` ENU, attitude quat + `omega` (same ENU / body conventions as C7/C11) |
| 6 | Input | `step(forces: MotorForceCommand, *, dt_s: float) -> ImuSample` — **forces**, not PWM. Same C11 motor→torque-proxy signs for **attitude** part |
| 7 | Translation law (exactly one toy map) | `thrust_body = (0, 0, thrust_gain * sum(motor_forces))` in **body +Z**; `a_world = R(q) * (thrust_body / mass) + g_world` with `g_world = (0,0,-9.81)`; integrate `v += a*dt`, `p += v*dt` (semi-implicit Euler OK — document). `mass > 0`, `thrust_gain > 0`, both finite, documented defaults |
| 8 | IMU honesty (B1 lock) | **`ImuSample` stays attitude-shaped like C11:** `gyro = omega`; `accel = R^T(q) * g_world` (gravity in body from **true** attitude). Linear acceleration is **not** folded into `ImuSample` this Buy — pose truth lives on plant getters. **Why:** C7 complementary filter expects “down” from accel; injecting hover specific-force would fight it. Specific-force IMU = **later IC** if needed |
| 9 | Expose true pose | Required: `true_position_m`, `true_velocity_mps`, and existing-style `true_attitude` (or one `true_state` bundle that includes all). Tests assert against plant truth, never against estimator belief |
| 10 | `FlightControlLoop.step` | **Byte-unchanged** in role: still does **not** call the plant. Caller: `out = loop.step(...)` then `sample = plant.step(out.forces, dt=...)` |
| 11 | Languages | **Both** Python + C++ in this Buy (steel ladder). No third plant under `capabilities/` |
| 12 | Safety / autonomy / registry / craft | Untouched. No Continuity/Board/`library/` edits. No `submit_command` execute |
| 13 | Version | **`0.5.36` → `0.5.37`**; tag **`v0.5.37`** on ACCEPT only |
| 14 | Forbidden claims | “We fly” · “physics-accurate” · “6-DoF product” · “altitude hold” · “GO_TO works” · motors / GPIO · MY5 inertia cited as truth |

**Product sentence:**

```text
Una plantita 6-DoF: las fuerzas del mixer mueven actitud y posición
en RAM, el IMU sigue siendo el de actitud de C11, y step() no llama
a la planta — el suelo de juguete para los lazos que vienen, no un dron.
```

**Defaults locked by Cursor (Engineer said procede C36):**
- New **`ToyQuad6DofPlant`**; C11 plant kept  
- Translation via body-+Z thrust sum; ENU + g=(0,0,-9.81)  
- IMU = C11-style gravity+gyro (no specific-force yet)  
- Plant outside `step`  
- Python + C++  

---

## 1. Package layout (normative intent)

```text
src/jarvis/flight_software/flight_control/
  plant.py              # EXTEND — keep ToyQuadAttitudePlant; add ToyQuad6DofPlant
                        #   (or plant_6dof.py sibling — prefer same file if readable)
  loop.py               # UNCHANGED (must not grow a plant call)

native/flight_control/
  include/jarvis/fc/plant.hpp   # EXTEND — add ToyQuad6DofPlant
  src/plant.cpp                 # EXTEND
  tests/test_plant.cpp          # NEW or extend existing plant tests
  smoke/…                       # optional thin 6-DoF smoke; C11 smoke untouched

tests/test_fase_c_sim_6dof_plant_b1.py   # NEW
```

Do **not** put the plant under `capabilities/`. Do **not** import craft Continuity into `plant.py`.

---

## 2. Types / APIs (normative intent)

Exact field names may vary slightly; report must list them. Prefer:

```text
ToyQuad6DofPlant
  __init__(mass=…, thrust_gain=…, torque_gain=…, angular_damping=…)
  reset(position=…, velocity=…, initial_q=…, initial_omega=…) -> None
  sense() -> ImuSample                    # no advance; C11-shaped IMU
  step(forces, *, dt_s) -> ImuSample      # advance 6-DoF + return sense-shaped sample
  true_attitude -> AttitudeState          # or equivalent
  true_position_m -> Vec3                 # ENU metres
  true_velocity_mps -> Vec3               # ENU m/s
```

Locks:
- Invalid `mass` / `thrust_gain` / `torque_gain` / `dt_s` → typed error (same spirit as C11)  
- Attitude torque proxies = **same formulas as C11** (FR/FL/RL/RR)  
- Frame locked **`enu`**

### 2.1 Forbidden public APIs

`write_gpio`, `open_serial`, `send_dshot`, `fly()`, product CFD, citing MY5 mass as plant `mass` default “because catalog”, altitude/position **controllers**, `submit_command`.

---

## 3. Integration rules

| Existing | C36 rule |
|---|---|
| `ToyQuadAttitudePlant` + C11/C13 smokes | **Keep green**; do not retune to “help” 6-DoF |
| `FlightControlLoop.step` / C++ `ControlLoop::step` | **Must not** call plant |
| C7 estimator | Unchanged; fed C11-shaped IMU from the new plant |
| C35 canned-IMU path | Unchanged (still no plant) |
| C4 / C17 Safety | Untouched |
| craft / Board / library | Untouched |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | Construct `ToyQuad6DofPlant` with defaults; `reset` at origin/level; `sense()` accel ≈ `(0,0,-9.81)`, gyro ≈ 0 |
| T2 | `step` with zero forces, small `dt`: position stays ~origin; attitude stays ~level (finite, no NaN) |
| T3 | Level + high collective (documented forces ≈ equal hover-ish sum): **altitude `z` increases** over N steps (thrust fights gravity). Document the force/collective numbers used |
| T4 | Level + pitch-tilted true attitude (or forces that create pitch) + thrust: **horizontal displacement** grows in the expected ENU direction (document sign). Pose truth from plant getters |
| T5 | `true_position_m` / `true_velocity_mps` change only via `step` (sense does not advance) |
| T6 | Invalid `mass <= 0`, `thrust_gain <= 0`, `dt_s <= 0` raise |
| T7 | C11 recovery smoke / tests for `ToyQuadAttitudePlant` still pass (tilt decreases) |
| T8 | `loop.step` source still has **no** plant call (grep / existing C24 invariant) |
| T9 | C++ Catch2: at least T1+T3 equivalent on `ToyQuad6DofPlant` |
| T10 | Thin smoke helper returns enough to see `|Δposition|` > 0 under T3 or T4 |
| T11 | No craft Continuity / `library/` / Board edits; Safety default still RejectAll |
| T12 | `pyproject` **`0.5.37`**; suite + `ctest` green |
| T13 | Report locks: **6-DoF toy ≠ flying ≠ product physics ≠ altitude hold ≠ specific-force IMU** |

---

## 5. Honesty / forbidden

```text
6-DoF toy plant ≠ flying ≠ product aero ≠ MY5 truth
pose in RAM ≠ GO_TO ≠ altitude hold ≠ house map
ImuSample C11-shaped ≠ specific-force accelerometer
plant.step outside loop.step ≠ MCU ISR ≠ motors
```

**Exists after ACCEPT:** a deterministic plant with position+velocity+attitude that consumes mixer forces and feeds the ladder.  
**Impossible:** a real vehicle; indoor navigation; claiming C38/C39 already done.

---

## 6. Docs

PRIORIDAD · PLATFORM §13 · ARCHITECTURE §1a / ladder · README “What v0.5.37 includes” · native README one-liner if it still says “attitude-only plant” as the only plant.

Cola after this: **C37** mag-yaw (sim). Assistant stays PARKED.

---

## 7. Acceptance

**PASS when:** T1–T13 · `ToyQuad6DofPlant` in Python+C++ · C11 plant recovery intact · `step` does not call plant · version `0.5.37`.  
**FAIL if:** plant folded into `ControlLoop` · C11 broken · specific-force IMU that breaks C7 without a dedicated Buy · altitude/position **controller** shipped · craft wiring · “we fly” docs · Assistant work · silicon.

---

## 8. Handoff

```text
Engineer → ★ this IC (C36)
Claude   → ToyQuad6DofPlant (Py+C++) + tests + smoke + report + 0.5.37
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.37
Cola     → C37 mag-yaw (sim)
```

---

## 9. PRIORIDAD blurb (paste on ★)

```text
Fase C: ★ C36 sim 6-DoF plant — ToyQuad6DofPlant (pose+attitude toy;
IMU C11-shaped; plant outside step). Package 0.5.37. ≠ flying.
Cola after ACCEPT: C37 mag-yaw. Assistant PARKED. Silicon parked.
```

---

## 10. Engineer ★ checklist

- [x] ★ this IC (authorize Claude) — Engineer 2026-09-26  
- [x] Confirm: C11 plant kept; IMU without specific-force this Buy — OK  
- [x] After landing: Cursor review PASS WITH NOTES — [review](implementation_review_fase_c_sim_6dof_plant_b1.md)  
- [x] Engineer ★ ACCEPT + tag `v0.5.37` — 2026-09-26  
- [ ] Next = **C37**, not Assistant  
