# Implementation Report — Fase C mixer rung (`B1-fase-c-mixer-rung`)

**IC:** [`implementation_contract_fase_c_mixer_rung_b1.md`](implementation_contract_fase_c_mixer_rung_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-20
**Status:** ★ ACCEPT CLOSED @ **`v0.5.7`**.

---

## 1. Package path

Extended the existing C3/C6/C7/C8 `src/jarvis/flight_software/flight_control/` tree — no new top-level package (IC §1 lock):

```text
src/jarvis/flight_software/flight_control/
├── types.py          # C3 — ImuSample, unchanged
├── hal.py             # C3 — ImuHal Protocol, unchanged
├── sim_imu_hal.py      # C3 — SimulatedImuHal, unchanged
├── filter.py           # C6 — ImuLowPassFilter, unchanged
├── attitude.py          # C7 — AttitudeState, ComplementaryAttitudeEstimator, unchanged
├── controller.py         # C8 — AttitudeSetpoint, BodyRateCommand, PdAttitudeController, unchanged
├── mixer.py               # NEW — MotorForceCommand, QuadXMixer, hover_collective
└── __init__.py             # exports the new mixer symbols
```

`hal.py`, `sim_imu_hal.py`, `types.py`, `filter.py`, `attitude.py`, and `controller.py` are byte-for-byte unchanged. No `esc.py`, `pwm.py`, or `dshot.py` was created.

`vehicle_profiles/smoke.py` gained one thin new function, `run_mixer_smoke` (IC §0 decision 11) — no new `VehicleProfile` field, no new profile JSON, no schema change; reuses the existing `smoke_quad_hal_imu` profile id, same as C6/C7/C8.

---

## 2. Types/API implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| `MotorForceCommand` (`t_s`, `motor_forces`, `layout`, `notes`) | §2.1 | ✅ Pydantic, `extra="forbid"`, `motor_forces` validated to exactly 4 finite entries; `layout: Literal["quad_x"] = "quad_x"`. No PWM/ESC field |
| `QuadXMixer.__init__(roll_scale, pitch_scale, yaw_scale)` | §2.2 | ✅ each defaults to `0.05`; all three validated `isfinite` and `>= 0`, else `ValueError` (T3) |
| `.mix(collective, rates) -> MotorForceCommand` | §2.2 | ✅ `collective` **clamped** (not rejected) to `[0, 1]` — the IC left this as an explicit implementer choice ("reject or clamp — pick one, document, test"); documented in the module docstring and tested (T3) |
| `hover_collective(default=0.5) -> float` | §2.3 | ✅ identity-style helper, tests/smoke only |

**Determinism:** confirmed by exact equality — same `collective`/`rates`/scales → identical `MotorForceCommand` (`test_determinism_same_inputs_give_identical_command`); all math is deterministic floating-point.

**Forbidden public APIs confirmed absent:** `set_pwm`, `write_dshot`, `arm`, `disarm`, `command_esc`, `open_serial` — none exist anywhere in `mixer.py`, confirmed both by a symbol-name sweep (T5) and by a direct source-text check for any actual call site (`test_no_esc_call_site_in_mixer_module_source`, which distinguishes the docstring's prose mention of these names from a real `(`-terminated call).

---

## 3. Layout and algorithm (IC §0 decisions 4–6)

**Exactly one airframe — quadrotor X.** Motor order and geometry are documented in `mixer.py`'s own module docstring with an ASCII diagram: `m0`=Front-Right, `m1`=Front-Left, `m2`=Rear-Left, `m3`=Rear-Right, at 45° off the body X/Y axes. No `+`/H/Y6/octo matrix exists anywhere.

**Allocation formula** (before per-motor clamp):

```text
m0 (FR) = collective - roll_scale*roll + pitch_scale*pitch - yaw_scale*yaw
m1 (FL) = collective + roll_scale*roll + pitch_scale*pitch + yaw_scale*yaw
m2 (RL) = collective + roll_scale*roll - pitch_scale*pitch - yaw_scale*yaw
m3 (RR) = collective - roll_scale*roll - pitch_scale*pitch + yaw_scale*yaw
```

**Signs verified directly** (T2/T2b/T2c): a positive roll channel decreases FR/RR and increases FL/RL symmetrically; a positive pitch channel increases FR/FL and decreases RL/RR; a positive yaw channel decreases FR/RL and increases FL/RR — each isolated single-channel test confirms the documented geometry with the other two channels held at zero.

**Scaffold honesty (IC §0 decision 6, verbatim in the module docstring):** `BodyRateCommand.omega_body_rad_s` (C8) is a body **rate**, not a true body **torque**. This B1 mixer treats `(roll, pitch, yaw) = omega_body_rad_s` directly as the mix channels to teach allocation geometry — it does not claim rate is physically equivalent to torque, and it does not silently insert a second (undocumented) rate→torque controller to paper over that gap. This is stated in three places: `mixer.py`'s docstring, this report, and the `PLATFORM_CAPABILITY_VISION.md`/`ARCHITECTURE.md` entries for C9.

---

## 4. Hard cut (IC §0 decision 7) — confirmed absent

- No PWM microseconds, no DShot, no ESC UART, no GPIO.
- No claim that hardware is armed or that any motor spins.
- Clamping (not pretending-armed) is the only range-enforcement mechanism: both `collective` and each output `motor_force` are clamped into `[0, 1]` — confirmed by `test_t3_invalid_scales_rejected_collective_clamped`, which drives `collective=-5.0`/`5.0` and checks the clamped extremes.

---

## 5. Integration rules (IC §3) — confirmed unchanged

- C8 `BodyRateCommand` — required mix-channel input, reused directly; no parallel type.
- C7/C6/C3 — untouched; the mixer itself doesn't require live HAL (accepts any `BodyRateCommand`, synthetic or pipeline-derived).
- C4 autonomy — untouched; no auto-routing of `AutonomyVerb.HOLD`, no call to `submit_command` anywhere in `mixer.py` (confirmed by craft-import isolation, T8).
- `RejectAllSafetyGate` — untouched; re-verified (T7).
- `CapabilityRegistry.load_default()` — untouched, still empty (0/0/0) (T9).
- Craft SoT (`orchestrator.py`, Board, `library/`) — untouched; zero references to `flight_control.mixer` or `QuadXMixer` in `src/jarvis/core/` or `src/jarvis/adapters/` (T8).

---

## 6. Tests run + counts

New module: `tests/test_fase_c_mixer_rung_b1.py` — **17 tests**, all passing, covering IC §4 T1–T10 plus seven extra cases (separate pitch/yaw sign checks, wrong-length rejection, zero-scale channel disable, determinism, and the explicit no-ESC-call-site source check):

```text
test_t1_equal_collective_zero_rates_gives_four_equal_motors PASSED
test_t2_roll_channel_signs_match_documented_x_layout PASSED
test_t2b_pitch_channel_signs_match_documented_x_layout PASSED
test_t2c_yaw_channel_signs_match_documented_x_layout PASSED
test_t3_invalid_scales_rejected_collective_clamped PASSED
test_t4_motor_force_command_shape PASSED
test_t5_no_esc_pwm_shaped_public_symbols_in_mixer_module PASSED
test_t6_no_cpp_or_cmake_under_flight_software PASSED
test_t7_default_safety_and_autonomy_submit_still_reject PASSED
test_t8_mixer_symbols_not_imported_by_orchestrator_or_craft_paths PASSED
test_t9_capability_registry_default_still_empty PASSED
test_t10_pyproject_version_is_0_5_7 PASSED
test_smoke_mixer_returns_at_least_one_command PASSED
test_motor_force_command_rejects_wrong_length PASSED
test_zero_scale_disables_channel PASSED
test_determinism_same_inputs_give_identical_command PASSED
test_no_esc_call_site_in_mixer_module_source PASSED
```

**T11 (full craft suite green):** `pytest -q` at repo root — **3297 passed, 1 skipped** (baseline before this Buy was 3280 passed, 1 skipped; delta is exactly the 17 new tests, no other file's pass/fail count moved).

**T12 (report confirms quad-X only + rate-as-mix-channel honesty + != ESC / != flying):** see §3/§7 below.

Fourteen pre-existing tests hardcoded the prior checkpoint version string (`"0.5.6"`) as a version-pin assertion. Since this IC explicitly authorizes and requires the `0.5.7` bump (§0 decision 12), those fourteen assertions were re-pinned to `"0.5.7"`:

- `tests/test_mission_power_w_b1.py`
- `tests/test_catalog_camera_power_w_b1.py`
- `tests/test_library_cameras_seed_b1.py`
- `tests/test_mission_vtx_identity_b1.py`
- `tests/test_fase_c_attitude_controller_rung_b1.py`
- `tests/test_fase_c_capability_registry_scaffold_b1.py`
- `tests/test_geometry_prop_adapter_visor_x_b1.py`
- `tests/test_bom_sku_resolved_cameras_b1.py`
- `tests/test_fase_c_attitude_estimation_rung_b1.py`
- `tests/test_fase_c_radio_dual_role_b1.py`
- `tests/test_fase_c_intent_safety_stub_b1.py`
- `tests/test_fase_c_imu_filtering_rung_b1.py`
- `tests/test_fase_c_first_fc_rung_b1.py`
- `tests/test_fase_c_autonomy_surface_b1.py`

---

## 7. Honesty / forbidden confirmation (IC §5)

| Forbidden | Status | Evidence |
|---|---|---|
| ESC / PWM / DShot | ✅ absent | No such symbol or call site anywhere in `mixer.py` (T5, source-text check) |
| Multiple airframe layouts | ✅ absent | `layout: Literal["quad_x"]` — the only value; one class, `QuadXMixer` |
| Claiming motors armed/spinning | ✅ absent | Module docstring states explicitly "it does not answer 'así es como enciendo un ESC'"; README/ARCHITECTURE both say "!= ESC / != flying" |
| Hiding rate≠torque simplification | ✅ stated explicitly | §3 above; same language in the module docstring, this report, PLATFORM_CAPABILITY_VISION.md, and ARCHITECTURE.md |
| Weakening RejectAll / craft wiring | ✅ unchanged | `default_safety_gate()` still `RejectAllSafetyGate`, re-verified (T7); zero craft imports (T8) |
| C++/CMake production FC | ✅ absent | T6 — no `.cpp`/`.hpp`/`CMakeLists.txt` under `flight_software/` or `vehicle_profiles/` |

**C++ honesty phrase** — present verbatim ("Python scaffold / sim only — production flight_control runtime is C++ (future IC)") in `mixer.py`'s module docstring, and re-affirmed in `flight_software/__init__.py`'s and `vehicle_profiles/smoke.py`'s updated docstrings.

**"One front" discipline (process lock after C6):** this Buy stayed exactly within the mixer rung — no ESC/PWM, no real Safety policy, no C++/CMake tree, no ELRS, no craft↔FS wiring were touched or opened.

---

## 8. Files changed

**New:**
- `src/jarvis/flight_software/flight_control/mixer.py`
- `tests/test_fase_c_mixer_rung_b1.py`
- `.jes/artifacts/implementation_report_fase_c_mixer_rung_b1.md` (this file)

**Modified:**
- `pyproject.toml` — version `0.5.6` → `0.5.7`
- `src/jarvis/flight_software/flight_control/__init__.py` — exports `MotorForceCommand`, `QuadXMixer`, `hover_collective`
- `src/jarvis/flight_software/__init__.py` — package docstring updated: "exactly four rungs" → "exactly five rungs" (sampling, filtering, attitude estimation, attitude control, mixer)
- `src/jarvis/vehicle_profiles/smoke.py` — new `run_mixer_smoke()`; docstring updated
- `src/jarvis/vehicle_profiles/__init__.py` — exports `run_mixer_smoke`; docstring updated
- `docs/ARCHITECTURE.md` — §1c gained a C9 paragraph; also corrected C8's stale "sin tag v0.5.6 todavía" note (C8 is now ACCEPT CLOSED with a real tag)
- `docs/PLATFORM_CAPABILITY_VISION.md` — §13 gained a C9 block
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner + C9 queue row updated to "landed, awaiting Cursor review + ★ ACCEPT"
- `README.md` — header banner, new "What v0.5.7 includes (working tree — not yet tagged)" section
- 14 test files — re-pinned stale `0.5.6` version-checkpoint assertions to `0.5.7` (listed in §6 above)

**Not touched (confirmed):** `orchestrator.py`, Board (`ui/spatial-board/`), `library/`, `src/jarvis/capabilities/*`, `src/jarvis/flight_software/autonomy/*`, `src/jarvis/flight_software/flight_control/{types,hal,sim_imu_hal,filter,attitude,controller}.py`, `.jes/state/engineering_state.json`.

---

## 9. Residual — what comes next

- ESC/PWM stub rung — separate future IC per C0 §7's ladder; still "one front at a time" per the process lock (next likely Buy per the IC's own handoff §8).
- A rate→torque bridge (if ever formalized as its own concept) would be a separate, explicit IC — not silently folded into a future mixer revision.
- A real (non-`RejectAll`) Safety policy, native/C++ production FC tree, and real ELRS remain separate future fronts, explicitly not opened by this Buy.
- Engineer ACCEPT of this Buy → commit + tag `v0.5.7` still pending, along with Cursor review.

---

## 10. Acceptance self-check against IC §7

- T1–T12: ✅ (T11/T12 are process gates, both satisfied — see §6/§7 above)
- Quad-X mixer works: ✅ (T1, T2, T2b, T2c)
- No ESC/PWM: ✅ (T5)
- RejectAll unchanged: ✅ (T7)
- Version `0.5.7`: ✅ (T10)
- Craft isolation: ✅ (T8)
- C++ honesty + rate-as-channel note present: ✅ (§3, §7)
