# Implementation Report — Fase C controlled-flight sim tip (`B1-fase-c-controlled-flight-sim-tip`)

**IC:** [`implementation_contract_fase_c_controlled_flight_sim_tip_b1.md`](implementation_contract_fase_c_controlled_flight_sim_tip_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-21
**Status:** ★ ACCEPT CLOSED @ **`v0.5.9`**.

---

## 0. Read this first — a bug in already-shipped code was found and fixed

While verifying the closed loop empirically (per this project's established "verify before writing formal tests" discipline), the C0 §7 tip's own pass criterion (tilt error must decrease) turned out to be **unachievable** using C7's `ComplementaryAttitudeEstimator` exactly as shipped at `v0.5.5` — a genuine sign bug in its accel correction caused it to converge attitude estimates **away** from the true tilt for any non-level input. This was **not** something C11 introduced; it was latent in already-ACCEPT-CLOSED, tagged code, undetected because every pre-existing C7 test only fed the estimator already-level accel readings (where the correction term is trivially zero).

Because this IC's own §3 table locks "C3–C10 modules | Reuse; do not reimplement," fixing this was outside this Buy's default scope. **I stopped and asked the Engineer how to proceed** rather than either (a) silently working around it with a cherry-picked scenario that happened to avoid triggering the bug, or (b) unilaterally patching already-tagged code without disclosure. **The Engineer's explicit answer: fix the one-line sign bug now, disclosed in this report.** §7 below is that disclosure.

---

## 1. Package path

Extended the existing C3/C6/C7/C8/C9/C10 `src/jarvis/flight_software/flight_control/` tree — no new top-level package (IC §1 lock):

```text
src/jarvis/flight_software/flight_control/
├── types.py          # C3 — ImuSample, unchanged
├── hal.py             # C3 — ImuHal Protocol, unchanged
├── sim_imu_hal.py      # C3 — SimulatedImuHal, unchanged
├── filter.py           # C6 — ImuLowPassFilter, unchanged
├── attitude.py          # C7 — ONE-LINE BUG FIX, see §7 — otherwise unchanged
├── controller.py         # C8 — AttitudeSetpoint, BodyRateCommand, PdAttitudeController, unchanged
├── mixer.py               # C9 — MotorForceCommand, QuadXMixer, hover_collective, unchanged
├── esc.py                  # C10 — EscPwmCommand, EscApplyResult, encode_motor_forces, SimulatedEscSink, unchanged
├── plant.py                 # NEW — ToyQuadAttitudePlant, tilt_angle_rad
└── __init__.py                # exports the new plant symbols
```

`hal.py`, `sim_imu_hal.py`, `types.py`, `filter.py`, `controller.py`, `mixer.py`, and `esc.py` are byte-for-byte unchanged. `attitude.py` has exactly one changed line (§7). No `physics_engine.py` product claims, `gpio.py`, `dshot.py`, or `rate_torque_controller.py` was created.

`vehicle_profiles/smoke.py` gained two thin new functions, `run_controlled_flight_sim_smoke` and `run_open_loop_baseline_smoke` (IC §0 decision 11 / §5 honesty note) — no new `VehicleProfile` field, no new profile JSON, no schema change; the closed loop does not require the shared `smoke_quad_hal_imu` profile at all (it constructs its own plant directly, per IC §0 decision 4 — the plant is driven by `MotorForceCommand`, not by any HAL).

---

## 2. Types/API implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| `ToyQuadAttitudePlant.reset(initial_q, initial_omega=...)` | §2.1 | ✅ resets true quaternion + body rate + internal clock to zero |
| `.step(forces: MotorForceCommand, *, dt_s: float) -> ImuSample` | §2.1 | ✅ consumes `MotorForceCommand` (locked — not PWM, T-confirmed via signature inspection); rejects non-finite/non-positive `dt_s` |
| Gravity in body frame reflects **true** orientation | §2.1 | ✅ `accel_mps2 = rotate(conj(q_true), world_gravity)` — verified directly: at 20° true tilt, `accel_mps2 ≈ (0, -3.355, -9.218)`, matching the analytically expected `(0, -9.81·sin(20°), -9.81·cos(20°))` to 6 significant figures (T1) |
| Exposed true state for tests | §2.1 | ✅ `true_attitude` property returns a full `AttitudeState` built from the plant's own internal quaternion/rate — never the estimator's belief |
| `run_controlled_flight_sim_smoke(..., steps=N, initial_tilt=...)` | §2.2 | ✅ wires plant → filter → estimator → level setpoint → PD → mixer → `plant.step(forces)`, returns the **true** tilt-error series (radians), one entry per step plus the initial value |
| Trailing `encode_motor_forces` + sink visibility | §2.2 | Not required by IC ("must not be required for plant dynamics") — omitted from the closed-loop path to keep it minimal; C10's own smoke already demonstrates that pairing independently |
| Forbidden APIs (`write_gpio`, `open_serial`, `send_dshot`, `fly()`, `arm_motors_hardware`) | §2.3 | ✅ none exist anywhere in `plant.py` — confirmed both by symbol-name sweep (T5) and direct source-text/import check (T5b) |

**Parameter validation:** `torque_gain` must be finite and `> 0`; `angular_damping` must be finite and `>= 0`; `dt_s` (per call) must be finite and `> 0` — all confirmed rejecting invalid inputs (T4).

---

## 3. Plant dynamics and honesty (IC §0 decisions 5–7)

**Attitude-only, explicitly not product physics.** `ToyQuadAttitudePlant` tracks quaternion + body angular rate only — no position, no velocity, no aerodynamics, no motor thrust curve, no vehicle mass/inertia from any real hardware.

**Motor→torque-proxy map** (documented in `plant.py`'s own docstring): given `MotorForceCommand.motor_forces = (m0, m1, m2, m3) = (FR, FL, RL, RR)` per `mixer.py`'s own layout,

```text
roll_proxy  = (m1 + m2) - (m0 + m3)
pitch_proxy = (m0 + m1) - (m2 + m3)
yaw_proxy   = (m1 + m3) - (m0 + m2)
```

— the algebraic inverse of `QuadXMixer.mix`'s own forward formulas, by construction of that linear system (not a new physics claim). `angular_accel = torque_gain * proxy - angular_damping * omega_true` per axis; integration is semi-implicit Euler (new rate first, then quaternion via the same body-frame right-composition convention used throughout C7/C8), matching the rest of this codebase's quaternion style.

**Rate ≠ torque remains open (IC §0 decision 7).** C9's `QuadXMixer` still treats `BodyRateCommand.omega_body_rad_s` (a rate) directly as its roll/pitch/yaw mix channels — unchanged, not "fixed" by this Buy. This plant's own force→angular-acceleration map is a **separate** toy simplification, documented on its own terms, not a physics correction for C9's honesty gap. No rate→torque controller was added anywhere.

---

## 4. Closed-loop demonstration (IC §0 decision 3, T2/T3)

**Pass criterion (locked): tilt error strictly decreases from a documented tilted initial condition.**

```text
run_controlled_flight_sim_smoke(steps=200, initial_tilt_rad=radians(15))
  initial tilt error: 15.000°
  final tilt error:   0.252°   (< 2° threshold asserted in T2)
```

**No-control baseline (T3, preferred and implemented):** `run_open_loop_baseline_smoke` runs the identical plant, seeded at the same 15° tilt, with a constant zero-rate mix applied every step (no filter/estimator/controller in the loop at all). Because the plant starts at zero body rate and a zero-rate mix produces zero net torque proxy, the angular acceleration is exactly zero for the entire run — **tilt error stays exactly constant at 15.000° for all 200 steps**, confirmed to `1e-9` tolerance. This demonstrates the closed loop is doing real corrective work, not just benefiting from passive damping or numerical decay.

---

## 5. Integration rules (IC §3) — confirmed unchanged

- C3–C10 modules — reused directly; only `attitude.py` was touched, and only for the one-line bug fix in §7 (not a reimplementation).
- C3 `SimulatedImuHal` — untouched; C3's own tests and smoke (`run_hal_imu_smoke`) still use it exactly as before; the closed-loop tip uses the new plant instead, per IC §0 decision 6.
- C4 autonomy — untouched; zero references to `flight_control.plant` or `ToyQuadAttitudePlant` in `src/jarvis/core/` or `src/jarvis/adapters/` (T8).
- `RejectAllSafetyGate` — untouched; re-verified (T7).
- `CapabilityRegistry.load_default()` — untouched, still empty (0/0/0) (T9).
- C9's rate-as-mix-channel honesty gap — explicitly still true, not silently fixed (§3 above).

---

## 6. Tests run + counts

New module: `tests/test_fase_c_controlled_flight_sim_tip_b1.py` — **14 tests**, all passing, covering IC §4 T1–T10 plus four extra cases (signature-level force-not-PWM lock, true-state exposure, reset-to-level, and the hardware-import/call-site check):

```text
test_t1_step_returns_imu_sample_with_gravity_consistent_with_true_tilt PASSED
test_t2_closed_loop_tilt_error_strictly_decreases PASSED
test_t3_open_loop_baseline_does_not_improve PASSED
test_t4_plant_rejects_invalid_dt_and_gains PASSED
test_t5_no_gpio_serial_dshot_fly_shaped_public_symbols PASSED
test_t5b_no_hardware_library_imports_or_call_sites PASSED
test_t6_no_cpp_or_cmake_under_flight_software PASSED
test_t7_default_safety_and_autonomy_submit_still_reject PASSED
test_t8_plant_symbols_not_imported_by_orchestrator_or_craft_paths PASSED
test_t9_capability_registry_default_still_empty PASSED
test_t10_pyproject_version_is_0_5_9 PASSED
test_plant_step_consumes_motor_force_command_not_pwm PASSED
test_true_attitude_property_exposes_true_state_for_tests PASSED
test_reset_defaults_to_level_and_zero_rate PASSED
```

**T11 (full craft suite green):** `pytest -q` at repo root — **3330 passed, 1 skipped** (baseline immediately before this Buy's own new tests, but *after* the C7 fix + its regression test, was 3316 passed, 1 skipped; delta is exactly the 14 new C11 tests). The C7 fix itself moved the suite from **3315 → 3316** (exactly its own one new regression test, zero other file's counts moved) — confirmed as a separate, isolated step before any C11-specific code was written.

**T12:** this report.

Sixteen pre-existing tests hardcoded the prior checkpoint version string (`"0.5.8"`) as a version-pin assertion. Since this IC explicitly authorizes and requires the `0.5.9` bump (§0 decision 12), those sixteen assertions were re-pinned to `"0.5.9"`:

- `tests/test_mission_power_w_b1.py`
- `tests/test_catalog_camera_power_w_b1.py`
- `tests/test_library_cameras_seed_b1.py`
- `tests/test_mission_vtx_identity_b1.py`
- `tests/test_fase_c_attitude_controller_rung_b1.py`
- `tests/test_fase_c_capability_registry_scaffold_b1.py`
- `tests/test_geometry_prop_adapter_visor_x_b1.py`
- `tests/test_fase_c_mixer_rung_b1.py`
- `tests/test_bom_sku_resolved_cameras_b1.py`
- `tests/test_fase_c_radio_dual_role_b1.py`
- `tests/test_fase_c_attitude_estimation_rung_b1.py`
- `tests/test_fase_c_intent_safety_stub_b1.py`
- `tests/test_fase_c_imu_filtering_rung_b1.py`
- `tests/test_fase_c_autonomy_surface_b1.py`
- `tests/test_fase_c_first_fc_rung_b1.py`
- `tests/test_fase_c_esc_pwm_stub_rung_b1.py`

---

## 7. The C7 bug: full disclosure

### 7.1 The bug

In `attitude.py`'s `ComplementaryAttitudeEstimator.update()`, the accel correction was computed as:

```python
error = _cross(predicted_down_body, accel_dir)   # WRONG order
```

Cross product is anti-commutative (`cross(a, b) = -cross(b, a)`), so this computed the **negative** of the correction needed to pull the predicted "down" direction toward the measured one — the estimator's accel feedback pushed its attitude estimate **away** from the true tilt, not toward it.

### 7.2 Proof (reproduced from the debugging session)

Seeding `ComplementaryAttitudeEstimator` with a constant accel reading corresponding to a fixed **true** tilt of `+0.1°` about the body X axis, with zero gyro, for 200 steps:

```text
Before fix: q_body_to_world converges to x ≈ -0.0016   (WRONG SIGN — true x should be ≈ +0.00087)
After fix:  q_body_to_world converges to x > 0          (correct side, matches true tilt)
```

This reproduced at every tested tilt magnitude (0.1° through 30°) — it was not a large-angle edge case, it was a systematic sign error present for any non-level input. It was undetected because every pre-existing C7 test (`test_t1_static_stream_stays_near_level`, `test_t1b_near_static_with_noise_stays_near_level`, etc.) only ever fed already-level accel, where `predicted_down_body` and `accel_dir` are already parallel and the cross-product correction is trivially `≈ 0` regardless of argument order.

### 7.3 The fix

One line, in `attitude.py`:

```python
# before
error = _cross(predicted_down_body, accel_dir)
# after
error = _cross(accel_dir, predicted_down_body)
```

Verified directly (scratch numeric check before editing the file) that this produces the correct-sign correction for a positive true tilt, then confirmed the full closed loop converges (§4 above) only after this fix — before it, the same closed-loop scenario diverged to a ~180° flip within ~80 steps.

### 7.4 What was NOT touched

- No change to the estimator's algorithm, gain semantics, API, or any other line.
- No change to `filter.py`, `controller.py`, `mixer.py`, or `esc.py`.
- All 15 pre-existing C7 tests still pass unmodified (confirmed before adding the new regression test) — this was a pure sign correction with zero behavioral change for any already-tested (near-level) scenario.

### 7.5 Regression test added to C7's own test file

`tests/test_fase_c_attitude_estimation_rung_b1.py::test_accel_correction_converges_toward_true_tilt_not_away_from_it` — feeds the estimator a constant accel reading for a fixed +5° true tilt (zero gyro) for 200 steps and asserts the converged quaternion's `x` component is positive (same side as the true tilt), with `y`/`z` staying at zero. This test would have failed before the fix and passes after it.

### 7.6 Process note

This fix was made only after explicitly stopping and asking the Engineer, since it touches a module this IC's own §3 table locks as "reuse, do not reimplement," on code already tagged `v0.5.5` and ACCEPT CLOSED. The Engineer's answer authorized fixing it now, disclosed here. No other C7 behavior, scope, or public contract was changed.

---

## 8. Honesty / forbidden confirmation (IC §5)

| Forbidden | Status | Evidence |
|---|---|---|
| Claiming real / hardware-verified flight | ✅ absent | Module docstring + README/ARCHITECTURE/PLATFORM_CAPABILITY_VISION all state "!= flying / != hardware-verified flight / != physics-accurate sim" |
| Product-grade aero as "the" plant | ✅ absent | `plant.py` docstring states explicitly "explicitly not product flight physics"; toy force→angular-acceleration map documented as such |
| Silent rate→torque controller | ✅ absent | No such controller exists anywhere in `plant.py`; §3 above documents the gap remains open |
| GPIO / pigpio / real ESC | ✅ absent | T5, T5b — no hardware-library import or call site anywhere in `plant.py` |
| Weakening RejectAll / craft wiring | ✅ unchanged | `default_safety_gate()` still `RejectAllSafetyGate`, re-verified (T7); zero craft imports (T8) |
| C++/CMake production FC tree | ✅ absent | T6 — no `.cpp`/`.hpp`/`CMakeLists.txt` under `flight_software/` or `vehicle_profiles/` |

**C++ honesty phrase** — present verbatim ("Python scaffold / sim only — production flight_control runtime is C++ (future IC)") in `plant.py`'s module docstring, and re-affirmed in `flight_software/__init__.py`'s and `vehicle_profiles/smoke.py`'s updated docstrings.

**"One front" discipline (process lock after C6):** this Buy stayed within the closed-loop-sim-tip scope, plus the one explicitly-authorized C7 fix required for that scope's own acceptance criterion. No real Safety policy, no C++/CMake production tree, no ELRS, no craft↔FS wiring, no GPIO/DShot hardware, and no rate→torque controller were touched or opened.

---

## 9. Files changed

**New:**
- `src/jarvis/flight_software/flight_control/plant.py`
- `tests/test_fase_c_controlled_flight_sim_tip_b1.py`
- `.jes/artifacts/implementation_report_fase_c_controlled_flight_sim_tip_b1.md` (this file)

**Modified:**
- `pyproject.toml` — version `0.5.8` → `0.5.9`
- `src/jarvis/flight_software/flight_control/attitude.py` — **one-line bug fix** (§7); one explanatory comment added at the fix site
- `src/jarvis/flight_software/flight_control/__init__.py` — exports `ToyQuadAttitudePlant`, `tilt_angle_rad`
- `src/jarvis/flight_software/__init__.py` — package docstring updated: "six rungs" → "six rungs plus one closed-loop sim tip"
- `src/jarvis/vehicle_profiles/smoke.py` — new `run_controlled_flight_sim_smoke()`, `run_open_loop_baseline_smoke()`; docstring updated
- `src/jarvis/vehicle_profiles/__init__.py` — exports the two new smoke functions; docstring updated
- `docs/ARCHITECTURE.md` — §1c gained a C11 paragraph (including the C7 fix disclosure)
- `docs/PLATFORM_CAPABILITY_VISION.md` — §13 gained a C11 block (including the C7 fix disclosure)
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner + C11 queue row updated to "landed, awaiting Cursor review + ★ ACCEPT," mentioning the C7 fix
- `README.md` — header banner, new "What v0.5.9 includes (working tree — not yet tagged)" section
- `tests/test_fase_c_attitude_estimation_rung_b1.py` — new regression test (§7.5)
- 16 test files — re-pinned stale `0.5.8` version-checkpoint assertions to `0.5.9` (listed in §6 above)

**Not touched (confirmed):** `orchestrator.py`, Board (`ui/spatial-board/`), `library/`, `src/jarvis/capabilities/*`, `src/jarvis/flight_software/autonomy/*`, `src/jarvis/flight_software/flight_control/{types,hal,sim_imu_hal,filter,controller,mixer,esc}.py`, `.jes/state/engineering_state.json`.

---

## 10. Residual — what comes next

Per this IC's own handoff §8, "wooden ladder tip CLOSED after ACCEPT" — the remaining fronts stay one at a time, per Engineer priority:

- A real rate→torque bridge (if ever formalized) — separate future IC.
- A real (non-`RejectAll`) Safety policy — separate future front.
- Native/C++ material change for the production FC runtime — separate future front (the "wooden ladder" is now complete; this is the next logical material change per the Engineer's own 2026-09-20 strategy note).
- Real ELRS/CRSF link — separate future front.
- Craft↔FS wiring — separate future front, not authorized by any Fase C IC so far.
- Engineer ACCEPT of this Buy → commit + tag `v0.5.9` — **DONE**.

---

## 11. Acceptance self-check against IC §7

- T1–T12: ✅ (T11/T12 are process gates, both satisfied — see §6 above)
- Closed loop recovers toward level under documented criterion: ✅ (§4, T2)
- Plant is toy + force-driven: ✅ (§3, T1)
- No GPIO: ✅ (T5, T5b)
- RejectAll unchanged: ✅ (T7)
- Version `0.5.9`: ✅ (T10)
- Craft isolation: ✅ (T8)
- C++ honesty: ✅ (§8)
- No fake "we fly": ✅ (§8)
