# Implementation Contract — Fase C attitude controller rung (`B1-fase-c-attitude-controller-rung`)

**Project:** Jarvis  
**Date:** 2026-09-20  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (rate cmd ≠ motors · no mixer/ESC · one controller only)

**Status:** ★ ACCEPT CLOSED @ **`v0.5.6`** (Engineer 2026-09-20)  
**Parents:**
- [C0 Design Contract ★](design_contract_fase_c_skill_capability_architecture.md) — §7 FC progression (`state estimation → controller → mixer → …`) · one rung per IC  
- [C7 ★ ACCEPT](implementation_contract_fase_c_attitude_estimation_rung_b1.md) — `AttitudeState` / complementary estimator @ **`v0.5.5`**  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no Safety-real / C++ / ELRS / craft wiring in this Buy  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — **fourth** `flight_control` rung only: **attitude controller** that turns desired attitude + estimated attitude into a **body-rate command**.  
**Package:** bump to **`0.5.6`** in this Buy; git tag **`v0.5.6`** only after Engineer ACCEPT.  
**Not** mixer · ESC/PWM · motor allocation · thrust setpoints · position/velocity control · live autonomy execution · real ELRS · craft wiring · `AllowAllSafetyGate` · production C++ FC tree · second estimator · opening another platform front.

**Outputs (required):**
1. Code under `src/jarvis/flight_software/flight_control/` (prefer new `controller.py` — **no** new top-level package)  
2. Tests (module + thin smoke path §4)  
3. `.jes/artifacts/implementation_report_fase_c_attitude_controller_rung_b1.md`  
4. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE — **controller stub ≠ flying / ≠ motor commands**; keep C++ honesty phrase  
5. `pyproject.toml` → **`0.5.6`** (+ re-pin version-checkpoint tests that assert `0.5.5`)

**Checkpoint:** package **`0.5.6`** · suite ≥ **3264** + new tests at ★

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-attitude-controller-rung`** — next C0 §7 rung after estimation: **attitude controller only** |
| 2 | One front | Do **not** fold mixer, ESC, Safety-real, C++/CMake, ELRS, or craft↔FS into this Buy |
| 3 | What this Buy demonstrates | Given a **desired** orientation and the **estimated** `AttitudeState` (C7), compute a **commanded body angular rate** that would (in a later Buy) drive the vehicle toward that orientation. **Human translation:** “quiero estar nivelado / inclinado así → el controlador pide estas velocidades de giro en el cuerpo.” |
| 4 | Algorithm (exactly one) | Ship **one** controller: a **PD attitude controller** on the orientation error (quaternion error → rotation-vector / small-angle error) producing `omega_cmd` in the **body** frame. Use estimated `omega_body_rad_s` for the D term. Document gains `kp`, `kd` with fixed defaults; reject non-finite or negative gains (lock: `kp > 0`, `kd >= 0`). **Forbidden:** cascaded rate PID as a second product, LQR, MPC, INDI, or shipping two controllers “to compare” |
| 5 | Hard cut (B1) | Output is **`BodyRateCommand` only** — **no** motor thrusts, **no** mixer matrix, **no** PWM/ESC, **no** collective thrust channel required in this Buy (hover thrust is a later / mixer concern). No position or velocity loops |
| 6 | Relationship to C4 autonomy | Do **not** auto-wire `AutonomyVerb.HOLD` → this controller. C4 remains Safety-gated and non-executing. Optional tests may *construct* a level setpoint by hand; they must not call `submit_command` as a flight path |
| 7 | Frames | Setpoints and estimates use the same world frame as C7: **`enu`**. Document body vs world in the module docstring |
| 8 | Hardware / language honesty | Still sim-only Python scaffold. Phrase: **Python scaffold / sim only — production flight_control runtime is C++ (future IC)**. No C++/CMake tree |
| 9 | Safety | Do **not** weaken RejectAll. Computing a rate command is **not** actuation (no motors yet). **Forbidden:** any `write_motor` / PWM path; any shipped `AllowAll*` |
| 10 | Registry | Default `CapabilityRegistry.load_default()` stays **empty** |
| 11 | No craft coupling | Do **not** change orchestrator Continuity, Board, or `library/` |
| 12 | Smoke | Thin helper e.g. `run_attitude_controller_smoke`: build level `AttitudeSetpoint` + a synthetic or pipeline `AttitudeState` → ≥1 `BodyRateCommand`. Prefer no new profile schema |
| 13 | Version | Bump **`0.5.5` → `0.5.6`**; tag **`v0.5.6`** on Engineer ACCEPT only |
| 14 | Forbidden claims | “Vehicle holds attitude in flight” · “motors respond” · marking control capability `available` |

**Product sentence:**

```text
Dado un setpoint de actitud y el AttitudeState de C7, calcular una
consigna de velocidad angular en el cuerpo (PD) — sin mezclador, sin
ESC y sin fingir que el dron ya se estabiliza en vuelo.
```

---

## 1. Package layout (normative)

```text
src/jarvis/flight_software/flight_control/
  attitude.py       # C7 — reuse AttitudeState
  controller.py     # NEW — AttitudeSetpoint, BodyRateCommand, PdAttitudeController
  # NO: mixer.py, esc.py, motor.py, thrust_allocator.py
```

Optional smoke in `vehicle_profiles/smoke.py`.

---

## 2. Types / APIs (normative)

### 2.1 `AttitudeSetpoint`

| Field | Notes |
|---|---|
| `t_s` | float |
| `q_body_to_world_desired` | unit quaternion `(w,x,y,z)` |
| `frame` | Literal `"enu"` (must match C7) |

`extra="forbid"`.

### 2.2 `BodyRateCommand`

| Field | Notes |
|---|---|
| `t_s` | float |
| `omega_body_rad_s` | 3-float commanded body rate |
| `notes` | optional honesty string |

**No** motor / PWM / thrust fields. `extra="forbid"`.

### 2.3 `PdAttitudeController`

```text
__init__(kp: float = <default>, kd: float = <default>)
  # reject invalid gains

reset() -> None   # optional; clears any D-filter state if introduced (prefer none)

compute(setpoint: AttitudeSetpoint, state: AttitudeState) -> BodyRateCommand
  # error from quaternion difference (desired vs estimated)
  # omega_cmd = kp * e_rot - kd * omega_measured   (sign convention documented)
```

Determinism: same inputs → identical `BodyRateCommand` (exact float equality or documented ≤1e-9 rel).

**Forbidden public APIs:** `mix`, `allocate`, `set_pwm`, `write_motor`, `command_esc`, `compute_thrusts`.

### 2.4 Optional helper

```text
level_setpoint(t_s: float) -> AttitudeSetpoint
  # identity quat / level hover attitude in enu — for tests/smoke only
```

---

## 3. Integration rules

| Existing | C8 rule |
|---|---|
| C7 AttitudeState | Required input |
| C6 filter / C3 HAL | Untouched (controller does not require live HAL) |
| C4 autonomy | Untouched; no auto HOLD→controller |
| RejectAll | Untouched |
| Registry / craft | Untouched |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | Level setpoint + level state (identity / near-identity) → `omega_cmd` near zero |
| T2 | Level setpoint + state with known small tilt → `omega_cmd` has corrective sign on the expected axis (documented) |
| T3 | Invalid gains → `ValueError` |
| T4 | `BodyRateCommand` has no motor/PWM/thrust fields |
| T5 | No public mixer/ESC-shaped symbols in `controller.py` |
| T6 | No new `.cpp`/CMake under `flight_software/` |
| T7 | Default Safety still reject; autonomy submit still reject |
| T8 | Zero craft imports of controller symbols from `core/` / `adapters/` |
| T9 | Registry still empty |
| T10 | `pyproject` **`0.5.6`**; re-pin `0.5.5` pins |
| T11 | Full suite green |
| T12 | Report: PD-only · rate cmd ≠ motors · C++ honesty · ≠ controlled flight |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| Mixer / motor allocation | Next ladder rung |
| ESC / PWM | Actuation |
| Claiming HOLD works in flight | C4 + this stub still non-flying |
| Second controller algorithm | One-algorithm lock |
| Weakening RejectAll | Safety |
| Craft Continuity / Board edits | Isolation |
| C++/CMake production FC | Future IC |

---

## 6. Docs

- PRIORIDAD / PLATFORM §13 / ARCHITECTURE / README “What v0.5.6 includes”  
- Explicit: **exists** = body-rate command from attitude error; **impossible** = motors move, vehicle stabilizes in air, mixer/ESC

---

## 7. Acceptance

**PASS when:** T1–T12 · PD controller works · output is body-rate only · no mixer/ESC · RejectAll unchanged · `0.5.6` · no craft coupling · C++ honesty present.

**FAIL if:** motor thrusts · mixer · ESC · Safety allow · craft wiring · fake “stabilized flight” claims.

---

## 8. Handoff

```text
Engineer → ★ this IC (C8)
Claude   → implement controller.py + tests + report + 0.5.6
Cursor   → review
Engineer → ACCEPT + tag v0.5.6
Cursor   → next Buy when prioritized (likely mixer — still one front)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C7 CLOSED @ v0.5.5. C8 B1-fase-c-attitude-controller-rung READY —
PD attitude → body-rate command; no mixer/ESC.
```

---

## 10. Engineer ★ checklist

1. Confirm **PD → BodyRateCommand** (not mixer/ESC) OK?  
2. Version **`0.5.6`** OK?  
3. No auto-wire from C4 HOLD OK?  
4. One front only (no Safety/C++/ELRS) OK?  
