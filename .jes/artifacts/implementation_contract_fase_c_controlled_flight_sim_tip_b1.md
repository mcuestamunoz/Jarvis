# Implementation Contract — Fase C controlled-flight sim tip (`B1-fase-c-controlled-flight-sim-tip`)

**Project:** Jarvis  
**Date:** 2026-09-20  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (sim closed-loop ≠ flying · plant ≠ physics product · no GPIO)

**Status:** ★ ACCEPT CLOSED @ tag **`v0.5.9`** · **Amendment A** included  
**Parents:**
- [C0 Design Contract ★](design_contract_fase_c_skill_capability_architecture.md) — §7 FC progression tip: `ESC → controlled flight`  
- [C10 ★ ACCEPT](implementation_contract_fase_c_esc_pwm_stub_rung_b1.md) — `encode_motor_forces` / `SimulatedEscSink` @ **`v0.5.8`**  
- Engineer strategy 2026-09-20: **finish the wooden ladder** (Python scaffold guide) before changing material to C++  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no Safety-real, C++/CMake, ELRS, craft wiring, or real peripheral I/O in this Buy  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — **C0 §7 tip only**: a **toy closed-loop sim** that feeds mixer motor forces back into a **plantita** which emits the next attitude-aware `ImuSample`, so the existing C3→C10 pipeline can run as a **closed loop** with a measurable “level recovery” criterion.  
**Package:** bump to **`0.5.9`** in this Buy; git tag **`v0.5.9`** only after Engineer ACCEPT.  
**Not** real flight · product aero/physics · GPIO/ESC hardware · rate→torque controller (honesty gap on C9 **remains**; do not silently invent one) · Safety-real · C++/CMake · craft Continuity wiring · claiming “we fly.”

**Outputs (required):**
1. Code under `src/jarvis/flight_software/flight_control/` (prefer new `plant.py` or `sim_loop.py` — **one** new module for plant + thin loop helper; do **not** fork C3–C10 modules)  
2. Tests + thin smoke (`run_controlled_flight_sim_smoke` or equivalent)  
3. `.jes/artifacts/implementation_report_fase_c_controlled_flight_sim_tip_b1.md`  
4. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **sim closed-loop ≠ flying / ≠ hardware**; C++ honesty phrase; wooden-ladder tip framing  
5. `pyproject.toml` → **`0.5.9`** (+ re-pin `0.5.8` version-checkpoint tests)

**Checkpoint:** package **`0.5.9`** · suite ≥ **3315** + new tests at ★

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-controlled-flight-sim-tip`** — C0 §7 tip: **controlled flight in sim only** (close the wooden ladder) |
| 2 | One front | Do **not** fold Safety-real, C++/CMake production tree, ELRS, craft↔FS, GPIO/DShot hardware, or a rate→torque controller into this Buy |
| 3 | What this Buy demonstrates | From a **tilted** plant initial attitude + level setpoint, run N closed-loop steps (filter → estimate → PD → mixer → **plant** → next IMU). A documented **tilt-error metric** must **decrease** (or strictly improve vs open-loop / vs no-control baseline — pick one criterion, document, test). **Human:** “en el simulador, la escalera entera se cierra sobre sí misma.” |
| 4 | Plant input (exactly one primary) | Plant advances from **`MotorForceCommand`** (C9 forces). **Not** from PWM µs as the dynamics input. Optional: smoke may still call `encode_motor_forces` / `SimulatedEscSink` for tip visibility — plant must not require PWM to step. |
| 5 | Plant honesty | Ship **one** toy plant only (name e.g. `ToyQuadAttitudePlant`). Documented first-order / linear-ish attitude dynamics — **explicitly not** product flight physics. Must emit **`ImuSample` consistent with its true attitude** (gravity rotated into body + gyro reflecting plant ω) so C7 is no longer stuck on C3’s non-attitude-aware HAL for this tip. |
| 6 | C3 HAL relationship | Do **not** break or silently rewrite `SimulatedImuHal` into a secret plant. Prefer: new plant type (+ optional thin adapter/`ImuHal` Protocol wrapper) used by the closed-loop smoke. Existing C3 tests stay green. |
| 7 | Rate≠torque | C9 mixer honesty gap **remains**. Do **not** invent a second rate→torque controller “to make the plant nice.” Document that the plant may treat differential forces with a toy map (own honesty note). Rate→torque remains a **future separate Buy** if prioritized. |
| 8 | Safety / autonomy | Do **not** weaken RejectAll. Do **not** auto-wire C4 HOLD → this loop. Closing the sim loop is still **not** live actuation. |
| 9 | Language honesty | **Python scaffold / sim only — production flight_control runtime is C++ (future IC)**. Phrase in new module docstring(s). No C++/CMake tree. |
| 10 | Registry / craft | Registry stays empty; no Continuity/Board/`library/` edits |
| 11 | Smoke | Thin helper: tilted start → N steps → returns final `AttitudeState` (and/or tilt-error series). Profile reuse `smoke_quad_hal_imu` OK if still valid; no schema change required. |
| 12 | Version | Bump **`0.5.8` → `0.5.9`**; tag **`v0.5.9`** on ACCEPT only |
| 13 | Forbidden claims | “We fly” · “controlled flight verified on hardware” · “physics-accurate sim” · “motors spinning” · marking flight capability `available` |
| 14 | **Amendment A — C7 accel-correction sign (2026-09-21)** | Empirically verified blocker: `ComplementaryAttitudeEstimator` accel correction (`_cross` argument order) converges **away** from true tilt on any non-level accel (C7 tests only exercised level accel → correction ≈ 0). **Authorized under this Buy:** (a) **one surgical sign fix** in `attitude.py` (flip cross operands **or** equivalent one-line correction sign — not a redesign / not a second estimator); (b) **regression test** in C7 test module that feeds a known small true tilt and asserts estimate moves toward it; (c) **prominent disclosure** in the C11 implementation report (pre-existing tagged defect @ `v0.5.5`, discovered while verifying C11 closed loop). **Still forbidden:** rewriting C7 algorithm, adding Mahony/Madgwick/EKF, or folding other C3–C10 “improvements” into this Buy. |

**Product sentence:**

```text
Cerrar el tip de la escalera de madera: un lazo simulado juguete donde
las fuerzas del mixer alimentan una plantita que genera el siguiente IMU,
y la actitud vuelve hacia nivel — sin GPIO, sin física de producto y sin
fingir que el dron vuela.
```

**Defaults locked by Cursor (Engineer said proceed):**
- Plant input = **forces** (not PWM)  
- Pass criterion = **tilt error decreases** after N steps from a documented tilted IC (vs initial error)  
- Rate→torque = **out of scope** (honesty note only)

---

## 1. Package layout (normative)

```text
src/jarvis/flight_software/flight_control/
  # C3–C10 unchanged in behavior
  plant.py   # NEW — ToyQuadAttitudePlant (+ optional loop helper in same module or smoke only)
  # NO: physics_engine.py product claims, gpio.py, dshot.py, rate_torque_controller.py
```

Implementer may put a tiny `step_closed_loop(...)` helper in `plant.py` **or** only in `vehicle_profiles/smoke.py` — prefer keeping orchestration thin and testable.

---

## 2. Types / APIs (normative)

### 2.1 Toy plant (normative shape — names may vary slightly if documented)

```text
ToyQuadAttitudePlant
  # true attitude state (quat + omega) in ENU / body conventions matching C7
  reset(initial_q, initial_omega=...) -> None
  step(forces: MotorForceCommand, *, dt_s: float) -> ImuSample
  # also expose true state for tests (property or last_true_attitude())
```

Locks:
- `step` consumes **`MotorForceCommand`**  
- returns **`ImuSample`** usable by C6 filter / C7 estimator  
- gravity in body frame must reflect **true** orientation (fixes the C7 known sim limitation **for this tip path only**)  
- parameters (inertia-ish scales, thrust→accel gains, noise optional) must be finite and validated; document defaults  

### 2.2 Closed-loop smoke / harness

```text
run_controlled_flight_sim_smoke(..., steps=N, initial_tilt=...) -> ...
  # wires: plant IMU → filter → estimator → level setpoint → PD → mixer → plant.step(forces)
  # returns enough to assert tilt-error decreased (list of errors or final AttitudeState + initial)
```

Optional trailing `encode_motor_forces` + sink.apply is allowed for “full tip visibility” but **must not** be required for plant dynamics.

### 2.3 Forbidden public APIs

`write_gpio`, `open_serial`, `send_dshot`, `fly()`, `arm_motors_hardware`, product CFD/aero solvers presented as truth.

---

## 3. Integration rules

| Existing | C11 rule |
|---|---|
| C3–C10 modules | **Reuse**; do not reimplement filter/attitude/controller/mixer/esc — **except** Amendment A (§0 #14): surgical C7 accel-correction sign fix + regression test only |
| C3 `SimulatedImuHal` | Remains as-is for older smokes; closed-loop tip uses the **new plant** |
| C4 autonomy | Untouched |
| RejectAll | Untouched |
| Craft | Untouched |
| C9 rate-as-mix-channel honesty | Explicitly **still true**; do not “fix” with a hidden rate loop |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | Plant `step` returns `ImuSample`; accel gravity direction consistent with true tilt (documented check) |
| T2 | Closed loop from tilted IC + level setpoint: tilt-error metric **strictly decreases** after N steps (N and metric documented) |
| T3 | Open / no-control baseline (optional but preferred): same IC without applying corrective mixer output does **not** get the same improvement claim — or document why T2 alone is enough |
| T4 | Plant rejects non-finite / invalid dt or gains |
| T5 | No GPIO/serial/dshot-shaped public symbols; no hardware lib imports in new module |
| T6 | No new `.cpp`/CMake under `flight_software/` |
| T7 | RejectAll + autonomy submit still reject |
| T8 | Zero craft imports of new plant/loop symbols |
| T9 | Registry empty |
| T10 | `pyproject` **`0.5.9`**; re-pin `0.5.8` |
| T11 | Full suite green |
| T12 | Report: toy plant · forces input · ≠ flying · ≠ product physics · rate≠torque still open · C++ honesty · wooden ladder tip |
| T13 | Amendment A: C7 regression — known small true tilt + zero gyro → estimate moves **toward** true tilt (not away); report discloses pre-`v0.5.5` defect + one-line fix |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| Claiming real / hardware-verified flight | Scaffold tip only |
| Product-grade aero as “the” plant | Honesty |
| Silent rate→torque controller | Process / C9 honesty |
| GPIO / pigpio / real ESC | Hardware not authorized |
| Weakening RejectAll / craft wiring | Process |
| C++/CMake production FC tree | Future material change |

---

## 6. Docs

- PRIORIDAD / PLATFORM §13 / ARCHITECTURE / README “What v0.5.9 includes”  
- Explicit: **exists** = toy closed-loop sim tip closing C0 §7 wooden ladder; **impossible** = real flight, hardware ESC, physics product claim  
- Note remaining wood-adjacent honesty (rate≠torque) and next material change (C++) are **other fronts**

---

## 7. Acceptance

**PASS when:** T1–T13 · closed loop recovers toward level under documented criterion · plant is toy + force-driven · C7 sign fix + regression present and disclosed · no GPIO · RejectAll unchanged · `0.5.9` · craft isolation · C++ honesty · no fake “we fly.”

**FAIL if:** open-loop-only smoke dressed as controlled flight · hardware I/O · hidden rate controller sold as physics · craft wiring · C++ tree · C7 “fixed” by algorithm rewrite beyond Amendment A.

---

## 8. Handoff

```text
Engineer → ★ this IC (C11)
Claude   → implement plant + closed-loop smoke + tests + report + 0.5.9
Cursor   → review
Engineer → ACCEPT + tag v0.5.9
Cursor   → next Buy when prioritized
           (wooden ladder tip CLOSED after ACCEPT;
            remaining fronts still one-at-a-time:
            rate→torque honesty · Safety-real · C++ material · link · craft↔FS)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C10 CLOSED @ v0.5.8. C11 B1-fase-c-controlled-flight-sim-tip READY —
toy closed-loop tip (forces→plant→IMU); ≠ flying; rate≠torque still open.
```

---

## 10. Engineer ★ checklist

1. Tip = **sim closed-loop** (not hardware flight) OK?  
2. Plant input = **MotorForceCommand** (not PWM dynamics) OK?  
3. Pass = **tilt error decreases** from tilted IC OK?  
4. Rate→torque **out of this Buy** OK?  
5. Version **`0.5.9`** OK?  
6. **Amendment A:** surgical C7 sign fix + regression + report disclosure under this Buy (not a separate IC) OK?  
