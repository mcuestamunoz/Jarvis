# Implementation Contract — Fase C mag-yaw rung (`B1-fase-c-mag-yaw-rung`)

**Project:** Jarvis  
**Date:** 2026-09-26  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — ★ AUTHORIZED: **implement now**  
**Reviewer:** Cursor against this IC · Engineer spot-check (sim mag ≠ live mag · yaw unlock ≠ flying · C7 tilt path still green)

**Status:** ★ **ACCEPT CLOSED** @ tag **`v0.5.38`** (Engineer 2026-09-26) · Cursor review PASS WITH NOTES  
**Parents:**
- [C36 ★ ACCEPT](implementation_contract_fase_c_sim_6dof_plant_b1.md) — `ToyQuad6DofPlant` @ **`v0.5.37`**  
- [C7 ★ ACCEPT](implementation_contract_fase_c_attitude_estimation_rung_b1.md) — complementary attitude, **no mag**, yaw gyro-only @ **`v0.5.5`**  
- [C25 ★ ACCEPT](implementation_contract_fase_c_rc_setpoint_b1.md) — AETR map; **yaw channel unused** for lack of heading reference @ **`v0.5.23`**  
- [Month note](engineer_note_software_month_until_bench_2026_09_26.md) — C37 after C36  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — add a **simulated magnetometer** and fuse it so estimated **yaw has an absolute reference**; unlock the RC **yaw** stick into `AttitudeSetpoint` now that heading is honest.  
**Package:** bump **`0.5.37` → `0.5.38`**; git tag **`v0.5.38`** only after Engineer ACCEPT.

**Not** live mag chip · not ICM/SPI mag · not altitude/position loops (C38/C39) · not executor (C40) · not Safety deepen · not craft↔FS · not Assistant · not GPIO · not claiming heading lock on a real aircraft · not folding plant into `step`.

**Outputs (required):**
1. Python: mag sample type + `SimulatedMagHal` (or equivalent) + mag-aware attitude update path extending C7 (prefer surgical extension of `attitude.py`, not a second named AHRS)  
2. C++ twin under `native/flight_control/`  
3. Unlock `map_rc_to_loop_inputs` yaw channel (index `3`) into the setpoint quaternion’s yaw — Python + C++  
4. Tests: `tests/test_fase_c_mag_yaw_rung_b1.py` + Catch2 case(s)  
5. Thin smoke: with sim mag, estimated yaw tracks a known true heading better than gyro-only after a yaw rotation  
6. Report + docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **sim mag ≠ live mag ≠ flying**  
7. `pyproject.toml` → **`0.5.38`** (+ re-pin `0.5.37` checkpoints)

**Checkpoint:** package **`0.5.38`** · suite green · host `ctest` green · C7 level/tilt tests still pass · C11/C36 plant smokes still pass

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-mag-yaw-rung`** — sim mag + yaw reference + unlock RC yaw |
| 2 | One front | Do **not** fold altitude loop, position loop, executor, Safety policy, ICM client, craft↔FS, Assistant, silicon, Taller/standoff |
| 3 | What this Buy demonstrates | Yaw stops being “only gyro drift.” A simulated field gives an absolute heading the estimator can hold, and the yaw stick can honestly set a heading in the setpoint. **Human:** “ya hay un norte de juguete; el stick de yaw ya no finge un rumbo que no existe.” |
| 4 | Mag sample | Typed **`MagSample`** (or equivalent): at least `t_s` + body-frame mag vector (`Vec3`). Units: **µT toy numbers OK** — document defaults; not a datasheet claim |
| 5 | Sim mag HAL | **`SimulatedMagHal`** (name flexible): deterministic. Preferred: fixed world field in ENU ≈ `(B_north, 0, B_down)` (document components), rotated into body by a **caller-supplied** true `q_body_to_world` (tests/plant feed truth; HAL does not secretly own a plant). Optional noise = **off** by default |
| 6 | Estimator | **One** complementary-style path: keep accel tilt correction; **add** yaw correction from horizontal mag vs world north when a mag sample is provided. Prefer extending `ComplementaryAttitudeEstimator` with `update(sample, mag=None)` (or `update` + `update_mag`) — **not** Mahony/Madgwick/EKF by name, not a second estimator “to compare.” When `mag is None`, behavior must match pre-C37 (C7 regression green) |
| 7 | RC yaw unlock | `RC_CH_YAW` index **`3`**: same mid/endpoints as C25; deflection from mid → yaw Euler angle in the 3-2-1 setpoint quaternion (same ±`RC_MAX_TILT_RAD` scale as roll/pitch **or** a documented `RC_MAX_YAW_RAD` — pick one, document). Roll/pitch/throttle maps **unchanged**. Sign: document (increasing channel → positive yaw about body/world Z per ENU right-hand) |
| 8 | `FlightControlLoop.step` | **No plant call.** Mag is **not** required inside `step` this Buy — caller may fuse mag **before** `step` by updating the estimator externally, **or** `step` may accept an optional mag argument. Prefer **caller fuses outside `step`** (keeps tick signature stable) unless a one-optional-arg extension is cleaner — pick one, document, do not break C24/C35 tests |
| 9 | Languages | **Both** Python + C++ |
| 10 | Plants | `ToyQuadAttitudePlant` / `ToyQuad6DofPlant` untouched in dynamics. Tests may feed plant `true_attitude.q` into `SimulatedMagHal` |
| 11 | Safety / craft / registry | Untouched |
| 12 | Version | **`0.5.37` → `0.5.38`**; tag on ACCEPT only |
| 13 | Forbidden claims | “compass live” · “GPS heading” · “we fly” · “heading hold on hardware” · mag on SPI1 |

**Product sentence:**

```text
Un magnetómetro de juguete y una corrección de yaw: el rumbo deja de
ser solo integración de giro, y el stick de yaw ya puede pedir un
rumbo con referencia — sin chip real y sin volar.
```

**Defaults locked by Cursor:**
- `MagSample` + `SimulatedMagHal` (world field → body via supplied q)  
- Extend C7 complementary filter; mag optional → C7-identical when absent  
- Unlock RC yaw into setpoint quaternion yaw  
- Prefer mag fusion **outside** `step` (caller)  
- Python + C++ · package **`0.5.38`**

---

## 1. Package layout (normative intent)

```text
src/jarvis/flight_software/flight_control/
  types.py or mag.py / sim_mag_hal.py   # MagSample + SimulatedMagHal (names flexible)
  attitude.py                           # EXTEND — optional mag yaw correction
  rc_setpoint.py                        # EXTEND — use channel 3
  loop.py                               # UNCHANGED preferred

native/flight_control/
  include/jarvis/fc/…                   # twins
  src/…
  tests/…                               # Catch2

tests/test_fase_c_mag_yaw_rung_b1.py    # NEW
```

Do **not** put mag under `capabilities/`. Do **not** import Continuity into attitude.

---

## 2. Tests (minimum)

| ID | Check |
|---|---|
| T1 | `SimulatedMagHal` at identity q → body mag matches documented world field mapping |
| T2 | Known yaw rotation of true q → body mag rotates consistently (finite, no NaN) |
| T3 | Estimator **without** mag: C7 tilt/level regressions still pass (behavior freeze) |
| T4 | Estimator **with** mag: after a pure yaw offset IC, estimated yaw error vs true decreases over N updates (document criterion) |
| T5 | RC map: yaw mid → setpoint yaw ≈ 0; yaw max → |yaw| ≈ max scale; roll/pitch/throttle unchanged vs C25 fixtures |
| T6 | Invalid mag / gain / empty field raise or reject per documented policy |
| T7 | `loop.step` still never calls plant; C35/C36 smokes still green |
| T8 | C++ Catch2: at least T1+T4+T5 equivalents |
| T9 | No craft/`library`/Board edits; Safety RejectAll intact |
| T10 | `pyproject` **`0.5.38`**; suite + `ctest` green |
| T11 | Report: **sim mag ≠ live mag ≠ flying ≠ heading lock on hardware** |

---

## 3. Honesty / forbidden

```text
sim mag ≠ live mag chip ≠ ICM SPI mag
yaw reference in RAM ≠ compass flight
RC yaw unlock ≠ motors ≠ flying
```

---

## 4. Acceptance

**PASS when:** T1–T11 · mag optional path · RC yaw unlocked · C7-without-mag frozen · version `0.5.38`.  
**FAIL if:** live mag · second AHRS brand · altitude/position controller · plant inside `step` · craft wiring · “we fly.”

---

## 5. Handoff

```text
Engineer → ★ AUTHORIZED (this IC — Claude implements now)
Claude   → MagSample + SimulatedMagHal + C7 mag yaw + RC yaw unlock (Py+C++) + tests + report + 0.5.38
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.38
Cola     → C38 altitude loop (sim)
```

---

## 6. PRIORIDAD blurb (paste on landing)

```text
Fase C: ★ C37 mag-yaw — sim mag + yaw reference + RC yaw unlock.
Package 0.5.38. ≠ live mag ≠ flying.
Cola after ACCEPT: C38 altitude. Assistant PARKED. Silicon parked.
```

---

## 7. Engineer ★ checklist

- [x] ★ this IC (authorize Claude) — 2026-09-26 (IC passed to Claude = execute)  
- [x] After landing: Cursor review PASS WITH NOTES — [review](implementation_review_fase_c_mag_yaw_rung_b1.md)  
- [x] Engineer ★ ACCEPT + tag `v0.5.38` — 2026-09-26  
- [ ] Next = **C38**, not Assistant  
