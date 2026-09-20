# Implementation Report — Fase C IMU filtering rung (`B1-fase-c-imu-filtering-rung`)

**IC:** [`implementation_contract_fase_c_imu_filtering_rung_b1.md`](implementation_contract_fase_c_imu_filtering_rung_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-20
**Status:** ★ ACCEPT CLOSED @ **`v0.5.4`**.

---

## 1. Package path

Extended the existing C3 `src/jarvis/flight_software/flight_control/` tree — no new top-level package (IC §1 lock):

```text
src/jarvis/flight_software/flight_control/
├── types.py          # C3 — ImuSample, unchanged
├── hal.py             # C3 — ImuHal Protocol, unchanged
├── sim_imu_hal.py      # C3 — SimulatedImuHal, unchanged
├── filter.py           # NEW — ImuLowPassFilter, read_filtered
└── __init__.py         # exports the new filter symbols
```

No `estimator.py`, `controller.py`, `mixer.py`, `esc.py`, or `attitude.py` was created. No `src/jarvis/flight_software/estimation/` was created. `hal.py`, `sim_imu_hal.py`, and `types.py` are byte-for-byte unchanged.

`vehicle_profiles/smoke.py` gained one thin new function, `run_hal_imu_filter_smoke` (IC §0 decision 11's "thin second smoke entry" option) — no new `VehicleProfile` field, no new profile JSON, no schema change.

---

## 2. Types/API implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| Reuse `ImuSample` for filtered output | §2.1 | ✅ `filter_sample` returns a plain `ImuSample` — no parallel `FilteredImuSample` type |
| `ImuLowPassFilter.__init__(alpha: float = 0.2)` | §2.2 | ✅ rejects `alpha` outside `(0, 1]` with `ValueError` (T3) |
| `.reset() -> None` | §2.2 | ✅ clears internal state; next sample seeds the filter unsmoothed |
| `.filter_sample(raw: ImuSample) -> ImuSample` | §2.2 | ✅ EMA per axis on `accel_mps2`/`gyro_rad_s`; `t_s` copied verbatim from `raw` |
| `read_filtered(hal, filt) -> ImuSample` | §2.3 | ✅ `raw = hal.read_imu(); return filt.filter_sample(raw)` — pure pipeline helper, lives in `filter.py` |
| C3 unchanged | §2.4 | ✅ confirmed — no edits to `hal.py`/`sim_imu_hal.py`/`types.py` |

**Forbidden APIs confirmed absent:** `estimate_attitude`, `get_quaternion`, `get_euler`, `update_ekf`, `write_motor`, `mix`, `set_pwm` — none exist anywhere in `filter.py` (T5).

---

## 3. Algorithm (IC §0 decision 4)

`ImuLowPassFilter` implements a first-order exponential moving average:

```text
filtered = alpha * raw + (1 - alpha) * previous_filtered
```

applied independently to each of the 3 accel axes and 3 gyro axes. This is the **only** filter shipped — no Madgwick, no Mahony, no complementary-as-attitude, no EKF. The docstring states explicitly that this is sensing post-process, not estimation, and that quaternion/Euler/attitude output belongs to a later, separate rung.

---

## 4. Integration rules (IC §3) — confirmed unchanged

- C3 HAL / `ImuSample` — reused directly; no parallel IMU type created.
- C4 autonomy (`flight_software/autonomy/`) — untouched; `default_safety_gate()` and `submit_command` behavior re-verified unchanged (T7).
- C5 radio (`capabilities/radio.py`) — untouched, not imported.
- `RejectAllSafetyGate` — untouched.
- `CapabilityRegistry.load_default()` — untouched, still empty (0/0/0) (T9).
- Craft SoT (`orchestrator.py`, Board, `library/`) — untouched; zero references to `flight_control.filter` or `ImuLowPassFilter` in `src/jarvis/core/` or `src/jarvis/adapters/` (T8).

---

## 5. Tests run + counts

New module: `tests/test_fase_c_imu_filtering_rung_b1.py` — **13 tests**, all passing, covering IC §4 T1–T10 plus three extra cases (α=1 exact-passthrough, smoke-helper sample count, explicit reset-then-reseed behavior):

```text
test_t1_constant_stream_converges_to_constant PASSED
test_t1b_alpha_one_equals_raw_every_time PASSED
test_t2_same_seed_alpha_reset_gives_identical_sequence PASSED
test_t3_invalid_alpha_rejected PASSED
test_t4_filtered_output_is_imu_sample_with_no_actuator_fields PASSED
test_t5_no_estimation_or_actuation_shaped_public_symbols_in_filter_module PASSED
test_t6_no_cpp_or_cmake_under_flight_software PASSED
test_t7_default_safety_and_autonomy_submit_still_reject PASSED
test_t8_filter_symbols_not_imported_by_orchestrator_or_craft_paths PASSED
test_t9_capability_registry_default_still_empty PASSED
test_t10_pyproject_version_is_0_5_4 PASSED
test_smoke_filter_returns_at_least_one_filtered_sample PASSED
test_reset_clears_state_so_next_sample_seeds_unfiltered PASSED
```

**T11 (full craft suite green):** `pytest -q` at repo root — **3249 passed, 1 skipped** (baseline before this Buy was 3236 passed, 1 skipped; delta is exactly the 13 new tests, no other file's pass/fail count moved).

**T12 (report confirms filter rung + no estimation/control/ESC + C++ honesty):** see §6 below.

Eleven pre-existing tests hardcoded the prior checkpoint version string (`"0.5.3"`) as a version-pin assertion. Since this IC explicitly authorizes and requires the `0.5.4` bump (§0 decision 12), those eleven assertions were re-pinned to `"0.5.4"`:

- `tests/test_mission_power_w_b1.py`
- `tests/test_catalog_camera_power_w_b1.py`
- `tests/test_library_cameras_seed_b1.py`
- `tests/test_mission_vtx_identity_b1.py`
- `tests/test_fase_c_capability_registry_scaffold_b1.py`
- `tests/test_geometry_prop_adapter_visor_x_b1.py`
- `tests/test_bom_sku_resolved_cameras_b1.py`
- `tests/test_fase_c_radio_dual_role_b1.py`
- `tests/test_fase_c_intent_safety_stub_b1.py`
- `tests/test_fase_c_autonomy_surface_b1.py`
- `tests/test_fase_c_first_fc_rung_b1.py`

---

## 6. Honesty / forbidden confirmation (IC §5)

| Forbidden | Status | Evidence |
|---|---|---|
| Shipping "attitude estimator" labeled as filter | ✅ absent | `filter.py`'s module docstring states explicitly "no quaternion, no Euler angles, no Madgwick/Mahony/EKF"; no such symbol exists (T5) |
| Mixer / ESC / PWM | ✅ absent | No `mix`/`set_pwm`/`write_motor` symbol anywhere in `filter.py` (T5) |
| Claiming controlled flight / armed | ✅ absent | Package docstring says "sensing post-process only... never estimation" |
| Weakening RejectAll / AllowAll | ✅ unchanged | `default_safety_gate()` still `RejectAllSafetyGate`, re-verified (T7); no `AllowAllSafetyGate` under `src/` (unchanged from C2) |
| Craft Continuity / Board / library edits | ✅ absent | Zero touches; T8 confirms no import from `core/`/`adapters/` |
| C++/CMake production FC tree | ✅ absent | T6 — no `.cpp`/`.hpp`/`CMakeLists.txt` under `flight_software/` or `vehicle_profiles/` |
| Auto-submit autonomy from filtered IMU | ✅ absent | `filter.py` never imports `flight_software.autonomy`; `read_filtered`/`run_hal_imu_filter_smoke` never call `submit_command` |

**C++ honesty phrase** — present verbatim ("Python scaffold / sim only — production flight_control runtime is C++ (future IC)") in `filter.py`'s module docstring, `flight_software/__init__.py`'s updated docstring, and `vehicle_profiles/smoke.py`'s updated docstring.

---

## 7. Files changed

**New:**
- `src/jarvis/flight_software/flight_control/filter.py`
- `tests/test_fase_c_imu_filtering_rung_b1.py`
- `.jes/artifacts/implementation_report_fase_c_imu_filtering_rung_b1.md` (this file)

**Modified:**
- `pyproject.toml` — version `0.5.3` → `0.5.4`
- `src/jarvis/flight_software/flight_control/__init__.py` — exports `ImuLowPassFilter`, `read_filtered`
- `src/jarvis/flight_software/__init__.py` — package docstring updated: "exactly one rung" → "exactly two rungs" (HAL+IMU sampling, EMA filtering); stale "no filtering" sentence removed
- `src/jarvis/vehicle_profiles/smoke.py` — new `run_hal_imu_filter_smoke()`; docstring updated
- `src/jarvis/vehicle_profiles/__init__.py` — exports `run_hal_imu_filter_smoke`; docstring updated
- `docs/ARCHITECTURE.md` — §1c extended with a new C6 paragraph; removed stale "no hay filtrado... ELRS/CRSF para C5" sentence (both C5 and now C6 have landed since that sentence was written)
- `docs/PLATFORM_CAPABILITY_VISION.md` — §13 gained a C6 block
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner + C6 queue row updated to "landed, awaiting Cursor review + ★ ACCEPT"
- `README.md` — header banner, new "What v0.5.4 includes (working tree — not yet tagged)" section
- 11 test files — re-pinned stale `0.5.3` version-checkpoint assertions to `0.5.4` (listed in §5 above)

**Not touched (confirmed):** `orchestrator.py`, Board (`ui/spatial-board/`), `library/`, `src/jarvis/capabilities/*`, `src/jarvis/flight_software/autonomy/*`, `.jes/state/engineering_state.json`.

---

## 8. Residual — what comes next

- State estimation rung (quaternion/Euler, Madgwick/Mahony/EKF-class) — separate future IC per C0 §7's ladder; this Buy explicitly does not touch it.
- A real (non-`RejectAll`) Safety policy remains a separate future IC.
- Native/C++ production FC tree remains a separate future IC (Engineer amendment from C3 stands unchanged).
- Engineer ACCEPT of this Buy → commit + tag `v0.5.4` still pending.

---

## 9. Acceptance self-check against IC §7

- T1–T12: ✅ (T11/T12 are process gates, both satisfied — see §5/§6 above)
- EMA/low-pass works on sim IMU: ✅ (T1, T1b, T2)
- No estimation/controller/mixer/ESC: ✅ (T5)
- RejectAll unchanged: ✅ (T7)
- Version `0.5.4`: ✅ (T10)
- No craft coupling: ✅ (T8)
- C++ honesty phrase present: ✅ (§6)
