# Implementation Report — Fase C ESC/PWM stub rung (`B1-fase-c-esc-pwm-stub-rung`)

**IC:** [`implementation_contract_fase_c_esc_pwm_stub_rung_b1.md`](implementation_contract_fase_c_esc_pwm_stub_rung_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-20
**Status:** ★ ACCEPT CLOSED @ **`v0.5.8`**.

---

## 1. Package path

Extended the existing C3/C6/C7/C8/C9 `src/jarvis/flight_software/flight_control/` tree — no new top-level package (IC §1 lock):

```text
src/jarvis/flight_software/flight_control/
├── types.py          # C3 — ImuSample, unchanged
├── hal.py             # C3 — ImuHal Protocol, unchanged
├── sim_imu_hal.py      # C3 — SimulatedImuHal, unchanged
├── filter.py           # C6 — ImuLowPassFilter, unchanged
├── attitude.py          # C7 — AttitudeState, ComplementaryAttitudeEstimator, unchanged
├── controller.py         # C8 — AttitudeSetpoint, BodyRateCommand, PdAttitudeController, unchanged
├── mixer.py               # C9 — MotorForceCommand, QuadXMixer, hover_collective, unchanged
├── esc.py                  # NEW — EscPwmCommand, EscApplyResult, encode_motor_forces, SimulatedEscSink
└── __init__.py               # exports the new esc symbols
```

`hal.py`, `sim_imu_hal.py`, `types.py`, `filter.py`, `attitude.py`, `controller.py`, and `mixer.py` are byte-for-byte unchanged. No `dshot.py`, `gpio.py`, or `hardware_pwm.py` was created.

`vehicle_profiles/smoke.py` gained one thin new function, `run_esc_pwm_smoke` (IC §0 decision 10) — no new `VehicleProfile` field, no new profile JSON, no schema change; reuses the existing `smoke_quad_hal_imu` profile id, same as C6/C7/C8/C9.

---

## 2. Types/API implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| `EscPwmCommand` (`t_s`, `pulse_us`, `protocol`, `notes`) | §2.1 | ✅ Pydantic, `extra="forbid"`, `pulse_us` validated to exactly 4 finite entries; `protocol: Literal["pwm_us"] = "pwm_us"` (locked). No GPIO pin field |
| `encode_motor_forces(forces, *, min_us=1000, max_us=2000) -> EscPwmCommand` | §2.2 | ✅ free function (IC explicitly allows free function or method — one public encoding path either way); linear map, rejects `min_us >= max_us` or non-finite bounds (T3); defensively clamps each input force to `[0, 1]` before mapping, since it does not assume its input necessarily came from `QuadXMixer` |
| `SimulatedEscSink.armed` | §2.3 | ✅ property, defaults `False` |
| `.arm()` / `.disarm()` | §2.3 | ✅ flip the in-memory flag only |
| `.apply(cmd) -> EscApplyResult` | §2.3 | ✅ **locked choice documented and tested:** always records `cmd` as the sink's last command (via `last_command()`), and reports `applied=True` only while armed — `applied=False, reason="disarmed"` while disarmed. Never opens a pin (T4, T5) |
| `EscApplyResult` (`applied`, `reason`, `pulse_us`) | §2.3 | ✅ Pydantic, `extra="forbid"`, echoes `pulse_us` from the applied/attempted command |

**Locked implementer choice (IC §0 decision 6 — "pick one, document, test"):** disarmed `apply()` **still records** the command (rather than refusing to store it at all). This was chosen because it lets tests and future smoke code introspect "what was the sink about to do" even while safely reporting `applied=False` — useful for a stub whose whole purpose is teaching the shape of this interface. Documented in `esc.py`'s module docstring and confirmed by `test_t4_disarmed_apply_does_not_claim_success`.

**Forbidden public APIs confirmed absent:** `write_gpio`, `open_serial`, `send_dshot`, `pigpio_*`, `export_pwm` — none exist anywhere in `esc.py`, confirmed both by a symbol-name sweep (T6) and by a direct source-text check for any real call site or import of a known hardware library (`test_t6b_no_known_gpio_library_imports`, `test_no_actuator_write_call_site_in_esc_module_source`).

---

## 3. Encoding (IC §0 decision 4)

**Exactly one encoding — classic PWM pulse width in microseconds.** `encode_motor_forces` maps `force ∈ [0, 1]` linearly onto `[min_us, max_us]`:

```text
pulse_us = min_us + clamp01(force) * (max_us - min_us)
```

Verified directly: `force=0.0 → 1000.0 µs`, `force=1.0 → 2000.0 µs`, `force=0.5 → 1500.0 µs` (T1), and custom `min_us=900`/`max_us=2100` ranges scale correctly (`test_custom_min_max_us_range`). No DShot, Oneshot, or Multishot encoding exists anywhere in `esc.py` — only this one linear map.

---

## 4. Hardware honesty (IC §0 decisions 5, 6) — confirmed absent

- No `RPi.GPIO`, no `pigpio`, no `/dev/mem`, no serial/USB opens, no sockets — confirmed by grepping the module source for any hardware-library import (`test_t6b_no_known_gpio_library_imports`) and by a repo-wide grep during verification (`grep -rln "import RPi\|import pigpio\|import serial\|import socket" src/jarvis/flight_software/` → empty).
- `SimulatedEscSink.apply(...)` only ever mutates `self._armed`/`self._last_command` — plain Python attribute assignment, nothing else.
- `arm()`/`disarm()` flip a boolean only; the module docstring states explicitly this never claims physical power.

---

## 5. Integration rules (IC §3) — confirmed unchanged

- C9 `MotorForceCommand` — required input to the encoder, reused directly; no parallel type.
- C8/C7/C6/C3 — untouched.
- C4 autonomy — untouched; no auto-routing of `AutonomyVerb.HOLD` into `esc.py` anywhere (confirmed by craft-import isolation, T9).
- `RejectAllSafetyGate` — untouched; re-verified (T8).
- `CapabilityRegistry.load_default()` — untouched, still empty (0/0/0) (T10).
- Craft SoT (`orchestrator.py`, Board, `library/`) — untouched; zero references to `flight_control.esc` or `SimulatedEscSink` in `src/jarvis/core/` or `src/jarvis/adapters/` (T9).

---

## 6. Tests run + counts

New module: `tests/test_fase_c_esc_pwm_stub_rung_b1.py` — **18 tests**, all passing, covering IC §4 T1–T11 plus seven extra cases (armed-smoke variant, wrong-length rejection, defensive out-of-range-force clamping, custom range, and the explicit no-hardware-call-site source checks):

```text
test_t1_encoding_endpoints_and_midpoint PASSED
test_t2_exactly_four_pulses_and_protocol PASSED
test_t3_invalid_min_max_rejected PASSED
test_t4_disarmed_apply_does_not_claim_success PASSED
test_t5_armed_apply_records_last_command PASSED
test_t6_no_gpio_serial_dshot_shaped_public_symbols PASSED
test_t6b_no_known_gpio_library_imports PASSED
test_t7_no_cpp_or_cmake_under_flight_software PASSED
test_t8_default_safety_and_autonomy_submit_still_reject PASSED
test_t9_esc_symbols_not_imported_by_orchestrator_or_craft_paths PASSED
test_t10_capability_registry_default_still_empty PASSED
test_t11_pyproject_version_is_0_5_8 PASSED
test_smoke_esc_pwm_returns_at_least_one_result_disarmed_by_default PASSED
test_smoke_esc_pwm_armed_reports_applied PASSED
test_esc_pwm_command_rejects_wrong_length PASSED
test_encode_clamps_out_of_range_force_defensively PASSED
test_custom_min_max_us_range PASSED
test_no_actuator_write_call_site_in_esc_module_source PASSED
```

**T12 (full craft suite green):** `pytest -q` at repo root — **3315 passed, 1 skipped** (baseline before this Buy was 3297 passed, 1 skipped; delta is exactly the 18 new tests, no other file's pass/fail count moved).

**T13 (report confirms PWM-us only + sim sink + != motors spinning + C++ honesty):** see §3/§4/§7 below.

Fifteen pre-existing tests hardcoded the prior checkpoint version string (`"0.5.7"`) as a version-pin assertion. Since this IC explicitly authorizes and requires the `0.5.8` bump (§0 decision 11), those fifteen assertions were re-pinned to `"0.5.8"`:

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
- `tests/test_fase_c_first_fc_rung_b1.py`
- `tests/test_fase_c_autonomy_surface_b1.py`

---

## 7. Honesty / forbidden confirmation (IC §5)

| Forbidden | Status | Evidence |
|---|---|---|
| Real pin toggling / pigpio | ✅ absent | No hardware-library import anywhere (T6b); `SimulatedEscSink` only mutates in-memory attributes |
| DShot as shipped product | ✅ absent | Exactly one encoding function, `encode_motor_forces`, implementing PWM-in-µs only |
| Claiming armed flight | ✅ absent | Module docstring states explicitly `arm()` "never claims physical power"; README/ARCHITECTURE both say "!= hardware ESC / != flying" |
| Weakening RejectAll / craft wiring | ✅ unchanged | `default_safety_gate()` still `RejectAllSafetyGate`, re-verified (T8); zero craft imports (T9) |
| C++/CMake production FC tree | ✅ absent | T7 — no `.cpp`/`.hpp`/`CMakeLists.txt` under `flight_software/` or `vehicle_profiles/` |

**C++ honesty phrase** — present verbatim ("Python scaffold / sim only — production flight_control runtime is C++ (future IC)") in `esc.py`'s module docstring, and re-affirmed in `flight_software/__init__.py`'s and `vehicle_profiles/smoke.py`'s updated docstrings.

**"One front" discipline (process lock after C6):** this Buy stayed exactly within the ESC/PWM encoding rung — no real peripheral I/O, no real Safety policy, no C++/CMake tree, no ELRS, no craft↔FS wiring were touched or opened.

---

## 8. Files changed

**New:**
- `src/jarvis/flight_software/flight_control/esc.py`
- `tests/test_fase_c_esc_pwm_stub_rung_b1.py`
- `.jes/artifacts/implementation_report_fase_c_esc_pwm_stub_rung_b1.md` (this file)

**Modified:**
- `pyproject.toml` — version `0.5.7` → `0.5.8`
- `src/jarvis/flight_software/flight_control/__init__.py` — exports `EscApplyResult`, `EscPwmCommand`, `SimulatedEscSink`, `encode_motor_forces`
- `src/jarvis/flight_software/__init__.py` — package docstring updated: "exactly five rungs" → "exactly six rungs" (sampling, filtering, attitude estimation, attitude control, mixer, ESC/PWM stub)
- `src/jarvis/vehicle_profiles/smoke.py` — new `run_esc_pwm_smoke()`; docstring updated
- `src/jarvis/vehicle_profiles/__init__.py` — exports `run_esc_pwm_smoke`; docstring updated
- `docs/ARCHITECTURE.md` — §1c gained a C10 paragraph; also corrected C9's stale "sin tag v0.5.7 todavía" note (C9 is now ACCEPT CLOSED with a real tag)
- `docs/PLATFORM_CAPABILITY_VISION.md` — §13 gained a C10 block
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner + C10 queue row updated to "landed, awaiting Cursor review + ★ ACCEPT"
- `README.md` — header banner, new "What v0.5.8 includes (working tree — not yet tagged)" section
- 15 test files — re-pinned stale `0.5.7` version-checkpoint assertions to `0.5.8` (listed in §6 above)

**Not touched (confirmed):** `orchestrator.py`, Board (`ui/spatial-board/`), `library/`, `src/jarvis/capabilities/*`, `src/jarvis/flight_software/autonomy/*`, `src/jarvis/flight_software/flight_control/{types,hal,sim_imu_hal,filter,attitude,controller,mixer}.py`, `.jes/state/engineering_state.json`.

---

## 9. Residual — what comes next

Per this IC's own handoff §8, "the ladder tip 'controlled flight' is still NOT claimed" after C10 — the six rungs together (sampling → filtering → estimation → control → mixing → PWM encoding) still never touch real hardware. Likely next forks, still one front at a time:

- A rate→torque honesty bridge (if ever formalized) would be its own explicit IC, not silently folded into an existing rung.
- A real (non-`RejectAll`) Safety policy — separate future front.
- Native/C++ production FC tree — separate future front.
- Real ELRS/CRSF link — separate future front.
- Engineer ACCEPT of this Buy → commit + tag `v0.5.8` — **DONE**.

---

## 10. Acceptance self-check against IC §7

- T1–T13: ✅ (T12/T13 are process gates, both satisfied — see §6/§7 above)
- PWM-us encoding works: ✅ (T1, T2, custom-range test)
- Sim sink only: ✅ (T4, T5, §4)
- No GPIO: ✅ (T6, T6b)
- RejectAll unchanged: ✅ (T8)
- Version `0.5.8`: ✅ (T11)
- Craft isolation: ✅ (T9)
- C++ honesty present: ✅ (§7)
