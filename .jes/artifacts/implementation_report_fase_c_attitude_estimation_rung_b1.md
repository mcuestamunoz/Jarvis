# Implementation Report — Fase C attitude estimation rung (`B1-fase-c-attitude-estimation-rung`)

**IC:** [`implementation_contract_fase_c_attitude_estimation_rung_b1.md`](implementation_contract_fase_c_attitude_estimation_rung_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-20
**Status:** ★ ACCEPT CLOSED @ **`v0.5.5`**.

---

## 1. Package path

Extended the existing C3/C6 `src/jarvis/flight_software/flight_control/` tree — no new top-level package, no `flight_software/estimation/` (IC §1 lock):

```text
src/jarvis/flight_software/flight_control/
├── types.py          # C3 — ImuSample, unchanged
├── hal.py             # C3 — ImuHal Protocol, unchanged
├── sim_imu_hal.py      # C3 — SimulatedImuHal, unchanged
├── filter.py           # C6 — ImuLowPassFilter, unchanged
├── attitude.py          # NEW — AttitudeState, ComplementaryAttitudeEstimator, read_attitude
└── __init__.py          # exports the new attitude symbols
```

`hal.py`, `sim_imu_hal.py`, `types.py`, and `filter.py` are byte-for-byte unchanged. No `controller.py`, `mixer.py`, `esc.py`, `navigation.py`, `ekf.py`, or `madgwick.py` was created.

`vehicle_profiles/smoke.py` gained one thin new function, `run_hal_imu_attitude_smoke` (IC §0 decision 13) — no new `VehicleProfile` field, no new profile JSON, no schema change; it reuses the existing `smoke_quad_hal_imu` profile id, same as C6.

---

## 2. Types/API implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| `AttitudeState` (`t_s`, `q_body_to_world`, `omega_body_rad_s`, `frame`) | §2.1 | ✅ Pydantic, `extra="forbid"`, `frame: Literal["enu"] = "enu"` (locked default per §0 decision 6). No position, velocity, motor, or PWM fields |
| `ComplementaryAttitudeEstimator.__init__(gain: float = 0.02, initial_q=identity)` | §2.2 | ✅ rejects `gain` outside `(0, 1]` with `ValueError` (T3); optional initial quaternion defaults to identity/level |
| `.reset() -> None` | §2.2 | ✅ clears internal state; next `update()` reseeds at `initial_q` |
| `.update(sample: ImuSample) -> AttitudeState` | §2.2 | ✅ accepts filtered `ImuSample` (also accepts raw for unit tests, as the IC permits); first call seeds unrotated, subsequent calls integrate gyro then apply the accel-tilt correction |
| `read_attitude(hal, filt, estimator) -> AttitudeState` | §2.3 | ✅ `filtered = filt.filter_sample(hal.read_imu()); return estimator.update(filtered)` — lives in `attitude.py` |
| Reuse C6 `ImuLowPassFilter`/`ImuSample` | §2.4 | ✅ imported directly; no EMA reimplemented inside the estimator |

**Determinism (locked in §2.2):** same HAL seed + same filter `alpha` + same estimator `gain` + `reset()` → identical `AttitudeState` sequence, confirmed by exact equality (T2) — all math here is deterministic floating-point (no randomness beyond the already-deterministic `SimulatedImuHal`).

**Forbidden public APIs confirmed absent:** `set_pwm`, `mix`, `write_motor`, `estimate_position`, `update_gps`, `update_mag`, `run_ekf`, `run_madgwick` — none exist anywhere in `attitude.py` (T5).

---

## 3. Algorithm (IC §0 decisions 4–6)

`ComplementaryAttitudeEstimator` implements a **single**, minimal, gravity-referenced complementary filter:

1. **Gyro integration:** `q_pred = normalize(q_prev ⊗ dq(omega * dt))`, where `dq` is the small-angle quaternion approximation of the body-rate rotation over the sample interval.
2. **Accel-derived tilt correction:** the predicted "down" direction (`world_down = (0, 0, -1)` in ENU, rotated into the body frame via `q_pred`'s inverse) is compared against the measured "down" direction (the normalized accelerometer reading). Their cross product gives a small-angle error vector, scaled by `gain`, which is composed onto `q_pred` as one more small rotation.
3. The result is renormalized to a unit quaternion.

This is **explicitly not** Mahony's published algorithm (no integral/bias state), **not** Madgwick (no gradient-descent objective function against an accel-error cost), and **not** an EKF/UKF/MEKF (no covariance propagation or Kalman gain) — it is a simple proportional-only tilt correction, which the accel measurement can only ever inform about roll/pitch, never yaw (yaw stays purely gyro-integrated, with no absolute reference — see `test_yaw_only_rotation_preserves_roll_pitch_when_level`, which confirms a pure-yaw gyro rotation accumulates in `z` while `x`/`y` (roll/pitch) stay exactly `0.0`).

**Hard cut (§0 decision 5) — confirmed absent:** no magnetometer, no GPS/baro, no online gyro-bias estimation, no position/velocity output anywhere in `attitude.py`.

**Frame (§0 decision 6):** `AttitudeState.frame` is locked to `"enu"` — the only valid `Literal` value in C7.

---

## 4. Known simulator limitation (honesty note)

`SimulatedImuHal` (C3) is **not attitude-aware** — it always emits a fixed-direction gravity vector (`accel_mps2 ≈ (0, 0, -9.81)` plus small noise) regardless of any "true" vehicle orientation, since C3 never modeled orientation at all. Consequently, a test that ran the estimator purely against `SimulatedImuHal` output would always converge toward "level" by construction, which would not actually exercise the tilt-correction math. To validate the estimator honestly, this Buy's tests (`test_t1_static_stream_stays_near_level`, `test_yaw_only_rotation_preserves_roll_pitch_when_level`, `test_reset_reseeds_at_initial_quaternion`, `test_zero_accel_norm_skips_correction_without_crashing`) construct synthetic in-memory `ImuSample` sequences directly, with known gyro/accel values, rather than relying solely on the shared sim HAL. `run_hal_imu_attitude_smoke()` still uses `SimulatedImuHal` (per the IC's smoke-path requirement) and is a pure "does the pipeline run end-to-end without crashing" smoke check, not a correctness proof.

---

## 5. Integration rules (IC §3) — confirmed unchanged

- C3 HAL / `ImuSample` — reused directly.
- C6 filter — required on the smoke path (`run_hal_imu_attitude_smoke` pipes through `ImuLowPassFilter` before the estimator, per §0 decision 13); the estimator itself also accepts raw samples for unit tests, as the IC explicitly permits.
- C4 autonomy / C5 radio — untouched; re-verified `default_safety_gate()` and `submit_command` behavior unchanged (T7).
- `RejectAllSafetyGate` — untouched.
- `CapabilityRegistry.load_default()` — untouched, still empty (0/0/0) (T9).
- Craft SoT (`orchestrator.py`, Board, `library/`) — untouched; zero references to `flight_control.attitude` or `ComplementaryAttitudeEstimator` in `src/jarvis/core/` or `src/jarvis/adapters/` (T8).

---

## 6. Tests run + counts

New module: `tests/test_fase_c_attitude_estimation_rung_b1.py` — **15 tests**, all passing, covering IC §4 T1–T10 plus five extra cases (near-static-with-noise, yaw-preservation-under-pure-rotation, reset-reseeding, zero-accel-norm guard, and the smoke helper's frame check):

```text
test_t1_static_stream_stays_near_level PASSED
test_t1b_near_static_with_noise_stays_near_level PASSED
test_t2_determinism_same_seed_alpha_gain_reset PASSED
test_t3_invalid_gain_rejected PASSED
test_t4_attitude_state_has_no_actuator_position_velocity_fields PASSED
test_t5_no_second_estimator_or_navigation_shaped_public_symbols PASSED
test_t6_no_cpp_or_cmake_under_flight_software PASSED
test_t7_default_safety_and_autonomy_submit_still_reject PASSED
test_t8_attitude_symbols_not_imported_by_orchestrator_or_craft_paths PASSED
test_t9_capability_registry_default_still_empty PASSED
test_t10_pyproject_version_is_0_5_5 PASSED
test_smoke_attitude_returns_at_least_one_state PASSED
test_yaw_only_rotation_preserves_roll_pitch_when_level PASSED
test_reset_reseeds_at_initial_quaternion PASSED
test_zero_accel_norm_skips_correction_without_crashing PASSED
```

**T11 (full craft suite green):** `pytest -q` at repo root — **3264 passed, 1 skipped** (baseline before this Buy was 3249 passed, 1 skipped; delta is exactly the 15 new tests, no other file's pass/fail count moved).

**T12 (report confirms complementary-only + no mag/GPS/bias learning + C++ honesty + "!= flight-verified"):** see §7 below.

Twelve pre-existing tests hardcoded the prior checkpoint version string (`"0.5.4"`) as a version-pin assertion. Since this IC explicitly authorizes and requires the `0.5.5` bump (§0 decision 14), those twelve assertions were re-pinned to `"0.5.5"`:

- `tests/test_mission_power_w_b1.py`
- `tests/test_catalog_camera_power_w_b1.py`
- `tests/test_library_cameras_seed_b1.py`
- `tests/test_mission_vtx_identity_b1.py`
- `tests/test_fase_c_capability_registry_scaffold_b1.py`
- `tests/test_geometry_prop_adapter_visor_x_b1.py`
- `tests/test_bom_sku_resolved_cameras_b1.py`
- `tests/test_fase_c_radio_dual_role_b1.py`
- `tests/test_fase_c_intent_safety_stub_b1.py`
- `tests/test_fase_c_imu_filtering_rung_b1.py`
- `tests/test_fase_c_first_fc_rung_b1.py`
- `tests/test_fase_c_autonomy_surface_b1.py`

---

## 7. Honesty / forbidden confirmation (IC §5)

| Forbidden | Status | Evidence |
|---|---|---|
| Shipping Madgwick/EKF "also" | ✅ absent | Exactly one class, `ComplementaryAttitudeEstimator`; module docstring states explicitly it is not Mahony/Madgwick/EKF/UKF/MEKF |
| Mag / GPS / baro fusion | ✅ absent | No such symbol or input anywhere in `attitude.py` |
| Online bias learning presented as product | ✅ absent | No bias state field or update anywhere; gyro reading used as-is each step |
| Controller / mixer / ESC | ✅ absent | No `mix`/`set_pwm`/`write_motor` symbol (T5) |
| Claiming flight-verified attitude | ✅ absent | Docstring and README both state "!= flight-verified attitude"; §4 above documents the sim HAL's own honesty limitation |
| Weakening RejectAll | ✅ unchanged | `default_safety_gate()` still `RejectAllSafetyGate`, re-verified (T7) |
| Craft Continuity / Board / library edits | ✅ absent | Zero touches; T8 confirms no import from `core/`/`adapters/` |
| C++/CMake production FC tree | ✅ absent | T6 — no `.cpp`/`.hpp`/`CMakeLists.txt` under `flight_software/` or `vehicle_profiles/` |
| Auto-submit autonomy from attitude | ✅ absent | `attitude.py` never imports `flight_software.autonomy`; `read_attitude`/`run_hal_imu_attitude_smoke` never call `submit_command` |

**C++ honesty phrase** — present verbatim ("Python scaffold / sim only — production flight_control runtime is C++ (future IC)") in `attitude.py`'s module docstring, and re-affirmed in `flight_software/__init__.py`'s and `vehicle_profiles/smoke.py`'s updated docstrings.

**"One front" discipline (process lock after C6):** this Buy stayed exactly within the estimation rung — no real Safety policy, no C++/CMake tree, no ELRS, no craft↔FS wiring were touched or opened.

---

## 8. Files changed

**New:**
- `src/jarvis/flight_software/flight_control/attitude.py`
- `tests/test_fase_c_attitude_estimation_rung_b1.py`
- `.jes/artifacts/implementation_report_fase_c_attitude_estimation_rung_b1.md` (this file)

**Modified:**
- `pyproject.toml` — version `0.5.4` → `0.5.5`
- `src/jarvis/flight_software/flight_control/__init__.py` — exports `AttitudeState`, `ComplementaryAttitudeEstimator`, `read_attitude`
- `src/jarvis/flight_software/__init__.py` — package docstring updated: "exactly two rungs" → "exactly three rungs" (sampling, filtering, attitude estimation)
- `src/jarvis/vehicle_profiles/smoke.py` — new `run_hal_imu_attitude_smoke()`; docstring updated
- `src/jarvis/vehicle_profiles/__init__.py` — exports `run_hal_imu_attitude_smoke`; docstring updated
- `docs/ARCHITECTURE.md` — §1c gained a C7 paragraph
- `docs/PLATFORM_CAPABILITY_VISION.md` — §13 gained a C7 block
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner + C7 queue row updated to "landed, awaiting Cursor review + ★ ACCEPT"
- `README.md` — header banner, new "What v0.5.5 includes (working tree — not yet tagged)" section
- 12 test files — re-pinned stale `0.5.4` version-checkpoint assertions to `0.5.5` (listed in §6 above)

**Not touched (confirmed):** `orchestrator.py`, Board (`ui/spatial-board/`), `library/`, `src/jarvis/capabilities/*`, `src/jarvis/flight_software/autonomy/*`, `src/jarvis/flight_software/flight_control/{types,hal,sim_imu_hal,filter}.py`, `.jes/state/engineering_state.json`.

---

## 9. Residual — what comes next

- Controller rung (attitude/rate/position control) — separate future IC per C0 §7's ladder; still "one front at a time" per the process lock.
- A real (non-`RejectAll`) Safety policy, native/C++ production FC tree, and real ELRS remain separate future fronts, explicitly not opened by this Buy.
- Engineer ACCEPT of this Buy → commit + tag `v0.5.5` still pending, along with Cursor review.

---

## 10. Acceptance self-check against IC §7

- T1–T12: ✅ (T11/T12 are process gates, both satisfied — see §6/§7 above)
- Complementary attitude works on sim filtered IMU: ✅ (T1, T1b, smoke)
- No second estimator: ✅ (§3, T5)
- No mag/GPS/bias learning: ✅ (§3, §7)
- No controller/ESC: ✅ (T5)
- RejectAll unchanged: ✅ (T7)
- Version `0.5.5`: ✅ (T10)
- No craft coupling: ✅ (T8)
- C++ honesty present: ✅ (§7)
