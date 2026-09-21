# Implementation Report — Fase C rate→torque bridge (`B1-fase-c-rate-torque-bridge`)

**IC:** [`implementation_contract_fase_c_rate_torque_bridge_b1.md`](implementation_contract_fase_c_rate_torque_bridge_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-21
**Status:** ★ ACCEPT CLOSED @ **`v0.5.10`**.

---

## 1. Package path

Extended the existing C3–C11 `src/jarvis/flight_software/flight_control/` tree — no new top-level package (IC §1 lock):

```text
src/jarvis/flight_software/flight_control/
├── types.py          # C3 — ImuSample, unchanged
├── hal.py             # C3 — ImuHal Protocol, unchanged
├── sim_imu_hal.py      # C3 — SimulatedImuHal, unchanged
├── filter.py           # C6 — ImuLowPassFilter, unchanged
├── attitude.py          # C7 — unchanged (C11's own bug fix already landed; no change this Buy)
├── controller.py         # C8 — BodyRateCommand output unchanged; still C8's own type
├── rate_torque.py         # NEW — BodyTorqueCommand, LinearRateTorqueBridge
├── mixer.py                # C9 — MIGRATED: mix(...) now takes BodyTorqueCommand
├── esc.py                    # C10 — unchanged
├── plant.py                   # C11 — unchanged (still consumes MotorForceCommand)
└── __init__.py                  # exports the new rate_torque symbols
```

`types.py`, `hal.py`, `sim_imu_hal.py`, `filter.py`, `attitude.py`, `controller.py`, `esc.py`, and `plant.py` are byte-for-byte unchanged. `mixer.py` has a **surgical** migration (§3 below) — no new file, no `rate_pid.py`, no `inertia_truth.py`, no C++ tree.

`vehicle_profiles/smoke.py`'s four internal call sites that build a `MotorForceCommand` (`run_mixer_smoke`, `run_esc_pwm_smoke`, `run_controlled_flight_sim_smoke`, `run_open_loop_baseline_smoke`) were all updated to insert `LinearRateTorqueBridge().convert(...)` between the controller/rate-command step and the mixer call — no schema change to `VehicleProfile`, same `smoke_quad_hal_imu` profile id.

---

## 2. Types/API implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| `BodyTorqueCommand` (`t_s`, `tau_body`, `notes`) | §2.1 | ✅ Pydantic, `extra="forbid"`; `tau_body` validated finite (3 components) |
| `LinearRateTorqueBridge(gain=... \| gains=(gx,gy,gz))` | §2.2 | ✅ accepts either a single scalar `gain` (applied to all 3 axes) or a per-axis `gains` 3-tuple, not both (raises `ValueError` if both given); every resolved gain must be finite and `> 0` |
| `.convert(rates: BodyRateCommand) -> BodyTorqueCommand` | §2.2 | ✅ `tau_i = gain_i * omega_cmd_i` per axis — one public conversion path, confirmed by direct construction and zero/positive-input tests (T1, T2, T2b) |
| `QuadXMixer.mix(collective, torques: BodyTorqueCommand) -> MotorForceCommand` | §2.3 | ✅ **migrated**, not dual — confirmed by signature inspection (`inspect.signature` shows the sole parameter is named `torques`, annotated `BodyTorqueCommand`) and by runtime behavior (passing a `BodyRateCommand` directly raises `AttributeError` on `.tau_body`, not a silent misinterpretation) |
| Forbidden APIs (`rate_pid_step`, `compute_inertia_torque_nm`, `write_gpio`, cascaded "inner rate loop" class) | §2.4 | ✅ none exist anywhere in `rate_torque.py` — confirmed by symbol-name sweep (T7) |

---

## 3. Mixer migration (IC §0 decision 6, §2.3) — surgical, no silent dual API

`QuadXMixer.mix`'s signature changed from `mix(self, collective: float, rates: BodyRateCommand)` to `mix(self, collective: float, torques: BodyTorqueCommand)`. Internally, `roll, pitch, yaw = rates.omega_body_rad_s` became `tau_x, tau_y, tau_z = torques.tau_body` — the allocation formula itself (the quad-X geometry, motor order, clamping) is **byte-for-byte identical**, only the input variable names changed to reflect the new semantics.

**No dual API was kept.** There is exactly one `mix` method; it does not accept a `BodyRateCommand` under any parameter name, and does not duck-type-detect which type was passed. `test_no_rate_command_accepted_by_mixer_at_runtime` confirms passing a `BodyRateCommand` directly raises `AttributeError` (Pydantic's `__getattr__` fails looking up `tau_body` on a model that doesn't have it) rather than silently reinterpreting a rate as a torque.

**All in-tree call sites were updated** (grep-verified before and after):

- `vehicle_profiles/smoke.py` — 4 call sites (`run_mixer_smoke`, `run_esc_pwm_smoke`, `run_controlled_flight_sim_smoke`, `run_open_loop_baseline_smoke`), each now builds a `LinearRateTorqueBridge()` and calls `.convert(rate_cmd)` before `mixer.mix(...)`.
- `tests/test_fase_c_mixer_rung_b1.py` — C9's own 8 test call sites, updated to construct `BodyTorqueCommand` directly via a renamed `_torque_cmd()` helper (these tests exercise the mixer's own allocation geometry, not the bridge's conversion, so they bypass the bridge deliberately — documented in the file's own updated header comment).

No other file in the repository called `.mix(` (confirmed by `grep -rn "\.mix(" src/ tests/` before starting this migration).

---

## 4. Bridge law and honesty (IC §0 decisions 4–5, 9)

**Exactly one law — feedforward only:** `tau_i = gain_i * omega_cmd_i`. No `kp * (omega_cmd - omega_measured)` term, no integral or derivative state, no measured-rate feedback anywhere in `rate_torque.py`. C8's `PdAttitudeController` already accounts for measured rate via its own `kd` term, upstream of this bridge — the bridge itself is a pure, stateless, per-axis linear scale.

**Units honesty:** `BodyTorqueCommand.tau_body` is documented in the module's own docstring as "normalized, dimensionless, torque-like" — not claimed as Newton-metres of any real vehicle. No inertia model, no unit conversion, no physical-accuracy claim exists anywhere in this module.

---

## 5. Closed-loop tip re-verification (IC §0 decision 7) — no retune needed

`run_controlled_flight_sim_smoke()`'s default `LinearRateTorqueBridge()` uses `gain=1.0` on all three axes. Since `tau_i = 1.0 * omega_cmd_i = omega_cmd_i`, this is **mathematically identical** to the mixer's pre-migration behavior (which used `omega_cmd_i` directly). Verified numerically both before and after wiring the bridge into the smoke path:

```text
Before C12 (mixer took BodyRateCommand directly):
  initial tilt error: 15.000°  final tilt error: 0.252°

After C12 (mixer takes BodyTorqueCommand via bridge, gain=1.0):
  initial tilt error: 15.000°  final tilt error: 0.252°   (identical)
```

`run_open_loop_baseline_smoke()` — now also routed through the bridge on a zero-rate command (`tau_body = (0, 0, 0)`) — remains exactly flat at 15.000° for all 200 steps, unchanged.

**No gain retune was required or performed.** This is disclosed explicitly here per IC §0 decision 7's "if retune needed, disclose in report" — none was needed.

---

## 6. Integration rules (IC §3) — confirmed unchanged

- C8 `BodyRateCommand` — still `PdAttitudeController`'s output type, unchanged.
- C9 geometry / scales — the quad-X allocation formula, motor order, and default `roll_scale`/`pitch_scale`/`yaw_scale` are unchanged; only the input vector's semantic name changed (rate → torque).
- C10 ESC — untouched; still consumes `MotorForceCommand` → PWM µs.
- C11 plant / closed loop — must (and does) call the bridge; tip remains green with zero retune (§5).
- C4 autonomy / `RejectAllSafetyGate` / craft — untouched; re-verified (T8, T9).

---

## 7. Tests run + counts

New module: `tests/test_fase_c_rate_torque_bridge_b1.py` — **18 tests**, all passing, covering IC §4 T1–T11 plus seven extra cases (per-axis gains, mixer signature lock, no-silent-rate-acceptance at runtime, smoke end-to-end, and determinism):

```text
test_t1_zero_rate_gives_zero_torque PASSED
test_t2_positive_rate_gives_positive_torque_on_each_axis PASSED
test_t2b_per_axis_gains PASSED
test_t3_invalid_gains_rejected PASSED
test_t4_mixer_public_mix_signature_takes_body_torque_command_only PASSED
test_t5_equal_collective_zero_torque_gives_four_equal_motors PASSED
test_t6_closed_loop_tilt_recovery_still_holds_with_bridge PASSED
test_t7_no_cascaded_rate_pid_or_gpio_shaped_public_symbols PASSED
test_t7b_no_cpp_or_cmake_under_flight_software PASSED
test_t8_default_safety_and_autonomy_submit_still_reject PASSED
test_t9_bridge_symbols_not_imported_by_orchestrator_or_craft_paths PASSED
test_t10_capability_registry_default_still_empty PASSED
test_t11_pyproject_version_is_0_5_10 PASSED
test_body_torque_command_rejects_non_finite PASSED
test_body_torque_command_rejects_unknown_extra_field PASSED
test_no_rate_command_accepted_by_mixer_at_runtime PASSED
test_smoke_mixer_uses_bridge_end_to_end PASSED
test_determinism_same_rate_input_gives_identical_torque PASSED
```

**T12 (full craft suite green):** `pytest -q` at repo root — **3348 passed, 1 skipped** (baseline before this Buy was 3330 passed, 1 skipped; delta is exactly the 18 new tests, no other file's pass/fail count moved — confirmed at two checkpoints: immediately after the mixer migration + smoke updates, before writing any new test, the suite was still exactly 3330 passed; only after adding the new test module did it move to 3348).

**T13 (report confirms feedforward only · normalized τ · mixer migrated · != N·m truth · != flying · next = C++ scaffold):** see §4, §8 below.

C9's own test file (`tests/test_fase_c_mixer_rung_b1.py`) was updated in place (not just re-pinned) — its 8 call sites that previously passed a `BodyRateCommand` directly to `mix()` now construct `BodyTorqueCommand` via a renamed local `_torque_cmd()` helper. This is a genuine, IC-authorized breaking-API-migration of previously-tagged (`v0.5.7`, ACCEPT CLOSED) code, explicitly locked by this IC's own §0 decision 6 and §2.3 ("Forbidden: keeping `mix(..., rates: BodyRateCommand)` as a supported public path after this Buy").

Sixteen pre-existing tests hardcoded the prior checkpoint version string (`"0.5.9"`) as a version-pin assertion. Since this IC explicitly authorizes and requires the `0.5.10` bump (§0 decision 12), those sixteen assertions were re-pinned to `"0.5.10"`:

- `tests/test_mission_power_w_b1.py`
- `tests/test_catalog_camera_power_w_b1.py`
- `tests/test_library_cameras_seed_b1.py`
- `tests/test_mission_vtx_identity_b1.py`
- `tests/test_fase_c_attitude_controller_rung_b1.py`
- `tests/test_fase_c_capability_registry_scaffold_b1.py`
- `tests/test_geometry_prop_adapter_visor_x_b1.py`
- `tests/test_fase_c_mixer_rung_b1.py`
- `tests/test_fase_c_controlled_flight_sim_tip_b1.py`
- `tests/test_bom_sku_resolved_cameras_b1.py`
- `tests/test_fase_c_radio_dual_role_b1.py`
- `tests/test_fase_c_attitude_estimation_rung_b1.py`
- `tests/test_fase_c_intent_safety_stub_b1.py`
- `tests/test_fase_c_imu_filtering_rung_b1.py`
- `tests/test_fase_c_autonomy_surface_b1.py`
- `tests/test_fase_c_esc_pwm_stub_rung_b1.py`
- `tests/test_fase_c_first_fc_rung_b1.py`

(Note: seventeen files listed — `test_fase_c_first_fc_rung_b1.py` was included in the re-pin sweep as the seventeenth. All are confirmed re-pinned to `0.5.10` in the diff.)

---

## 8. Honesty / forbidden confirmation (IC §5)

| Forbidden | Status | Evidence |
|---|---|---|
| Cascaded rate PID sold as this bridge | ✅ absent | Exactly one method, `.convert()`, implementing the single feedforward law; T7 confirms no PID-shaped symbol exists |
| Claiming real N·m | ✅ absent | Module docstring states explicitly "normalized/dimensionless torque-like," never N·m |
| Silent dual mixer API (rates still accepted) | ✅ absent | Signature-locked to `BodyTorqueCommand` only (T4); runtime confirms a rate raises `AttributeError` rather than being silently accepted (dedicated test) |
| C++/Safety/GPIO/craft in this Buy | ✅ absent | T7b — no `.cpp`/`.hpp`/`CMakeLists.txt`; T8 — RejectAll unchanged; T9 — zero craft imports |
| Breaking C11 tip without disclosure | ✅ n/a | Tip was **not** broken — re-verified identical, explicitly disclosed as needing no retune (§5) |

**C++ honesty phrase** — present verbatim ("Python scaffold / sim only — production flight_control runtime is C++ (future IC)") in `rate_torque.py`'s module docstring, and re-affirmed in `flight_software/__init__.py`'s updated docstring.

**"One front" discipline (process lock after C6):** this Buy stayed exactly within the rate→torque honesty bridge scope. No C++/CMake, no real Safety policy, no ELRS, no craft↔FS wiring, no GPIO/DShot hardware, and no cascaded rate PID were touched or opened.

---

## 9. Files changed

**New:**
- `src/jarvis/flight_software/flight_control/rate_torque.py`
- `tests/test_fase_c_rate_torque_bridge_b1.py`
- `.jes/artifacts/implementation_report_fase_c_rate_torque_bridge_b1.md` (this file)

**Modified:**
- `pyproject.toml` — version `0.5.9` → `0.5.10`
- `src/jarvis/flight_software/flight_control/mixer.py` — **migrated** `mix()` signature and internals from `BodyRateCommand`/`omega_body_rad_s` to `BodyTorqueCommand`/`tau_body`; module docstring updated to document the honesty gap as CLOSED by C12
- `src/jarvis/flight_software/flight_control/__init__.py` — exports `BodyTorqueCommand`, `LinearRateTorqueBridge`
- `src/jarvis/flight_software/__init__.py` — package docstring updated to describe the C12 bridge and the migrated C9 mixer
- `src/jarvis/vehicle_profiles/smoke.py` — all 4 internal `MotorForceCommand`-building functions now route rate commands through `LinearRateTorqueBridge` before calling `mixer.mix(...)`; docstring updated
- `docs/ARCHITECTURE.md` — §1c gained a C12 paragraph
- `docs/PLATFORM_CAPABILITY_VISION.md` — §13 gained a C12 block explicitly stating the C9/C11-documented gap is now closed
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner + C12 queue row updated to "landed, awaiting Cursor review + ★ ACCEPT"
- `README.md` — header banner, new "What v0.5.10 includes (working tree — not yet tagged)" section
- `tests/test_fase_c_mixer_rung_b1.py` — **migrated** (not just re-pinned): 8 call sites updated from `BodyRateCommand` to `BodyTorqueCommand` construction, plus version re-pin
- 16 other test files — re-pinned stale `0.5.9` version-checkpoint assertions to `0.5.10`

**Not touched (confirmed):** `orchestrator.py`, Board (`ui/spatial-board/`), `library/`, `src/jarvis/capabilities/*`, `src/jarvis/flight_software/autonomy/*`, `src/jarvis/flight_software/flight_control/{types,hal,sim_imu_hal,filter,attitude,controller,esc,plant}.py`, `.jes/state/engineering_state.json`.

---

## 10. Residual — what comes next

Per this IC's own §8 handoff and §0 decision 14: the next Engineer-prioritized front is the **C++ scaffold** (separate IC, not started here). Other still-parked fronts, one at a time:

- A real (non-`RejectAll`) Safety policy.
- Real ELRS/CRSF link.
- Craft↔FS wiring — not authorized by any Fase C IC so far.
- Engineer ACCEPT of this Buy → commit + tag `v0.5.10` — **DONE**. C13 C++ scaffold IC opened.

---

## 11. Acceptance self-check against IC §7

- T1–T13: ✅ (T12/T13 are process gates, both satisfied — see §7/§8 above)
- Bridge works: ✅ (T1, T2, T2b)
- Mixer consumes torques only: ✅ (T4, no-silent-rate-acceptance test)
- Closed-loop tip still honest/green: ✅ (§5, T6)
- RejectAll unchanged: ✅ (T8)
- Version `0.5.10`: ✅ (T11)
- Craft isolation: ✅ (T9)
- C++ honesty: ✅ (§8)
- No fake N·m / no cascaded PID: ✅ (§4, §8)
