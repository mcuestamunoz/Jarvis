# Implementation Report — Fase C first `flight_control` rung (`B1-fase-c-first-fc-rung`)

**IC:** [`implementation_contract_fase_c_first_fc_rung_b1.md`](implementation_contract_fase_c_first_fc_rung_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-20
**Status:** **ACCEPT CLOSED** (Engineer 2026-09-20) · Cursor review PASS · tag **`v0.5.1`**

---

## 1. Package layout

Created exactly as locked in IC §1 (first authority to put these trees on disk — C0/C1/C2 all forbade this until now):

```text
src/jarvis/flight_software/
├── __init__.py                 # honest docstring: sensing-only stub, craft-FC vs FS-FC naming split
└── flight_control/
    ├── __init__.py
    ├── types.py                 # ImuSample (Vec3 = tuple[float,float,float])
    ├── hal.py                    # ImuHal Protocol — read_imu() only
    └── sim_imu_hal.py              # SimulatedImuHal — deterministic synthetic samples

src/jarvis/vehicle_profiles/
├── __init__.py
├── schemas.py                  # VehicleProfile
├── loader.py                    # load_profile() / load_smoke_profile()
├── smoke.py                      # run_hal_imu_smoke() — pytest smoke helper
└── data/
    └── smoke_quad_hal_imu.json   # the one smoke profile seed
```

No `filter.py`, `estimator.py`, `controller.py`, `mixer.py`, or `esc.py` exist under `flight_control/`. No `flight_software/autonomy/` was created (C4). The smoke helper `run_hal_imu_smoke()` was placed under `vehicle_profiles/smoke.py` (per IC §2.5's "pick one; report which") since it is profile-driven — it loads a `VehicleProfile`, then builds the HAL from it.

---

## 2. Types implemented vs IC §2

| Type | IC ref | Match |
|---|---|---|
| `ImuSample` (`t_s`, `accel_mps2`, `gyro_rad_s`) | §2.1 | ✅ Pydantic, `extra="forbid"`, no actuator field |
| `ImuHal` (Protocol, `read_imu()`) | §2.2 | ✅ `typing.Protocol`, single method. No `write_motor`/`set_pwm`/`arm`/`disarm` anywhere under `flight_software/` |
| `SimulatedImuHal` | §2.3 | ✅ implements `ImuHal`; constructor takes `seed: int = 0`; `random.Random(seed)` makes the full sample sequence deterministic; also ships `reset()` (declared optional in IC §2.2) to replay the same sequence; no network sockets, no hardware claim |
| `VehicleProfile` (`id`, `display_name`, `vehicle_class`, `rung`, `notes`) | §2.4 | ✅ Pydantic, `extra="forbid"`, `rung: Literal["hal_imu"]` (only value valid in C3) |
| `run_hal_imu_smoke()` | §2.5 | ✅ loads profile → builds `SimulatedImuHal` → reads ≥1 sample → asserts `profile.rung == "hal_imu"`. Never calls `SafetyGate.evaluate`, never touches an actuator (there is none to touch) |

---

## 3. Integration with C1/C2 (IC §3) — confirmed unchanged

- `CapabilityRegistry.load_default()` — untouched, still returns empty (0/0/0). No `imu_sampling` capability record was added to the product default, per the IC's locked preference ("keep default registry empty").
- `default_safety_gate()` — untouched, still `RejectAllSafetyGate`. Reading the IMU is sensing, not actuation, so it correctly never calls `SafetyGate.evaluate` for an `allow` decision.
- `Intent` / channel adapters — untouched; `TerminalIntentAdapter` is not wired to anything in `flight_software/`.
- Craft catalog `flight_controller` (`library/flight_controller/`) — untouched, orthogonal. The naming split is documented explicitly in `flight_software/__init__.py`'s module docstring (IC §0 decision 9).

---

## 4. Tests run + counts

New module: `tests/test_fase_c_first_fc_rung_b1.py` — **12 tests**, all passing, covering IC §4 T1–T9 plus three extra cases (reset-replay determinism, an unknown-`rung` rejection check, and a Protocol-conformance check):

```text
test_t1_simulated_imu_hal_returns_imu_sample_with_3_vectors PASSED
test_t2_same_seed_gives_identical_first_sample PASSED
test_t2b_reset_replays_same_sequence PASSED
test_t3_no_actuator_shaped_methods PASSED
test_t4_smoke_profile_declares_hal_imu_rung PASSED
test_t5_run_hal_imu_smoke_returns_at_least_one_sample PASSED
test_t6_safety_gate_unchanged_still_reject_all PASSED
test_t7_capability_registry_default_still_empty PASSED
test_t8_pyproject_version_is_0_5_1 PASSED
test_t9_flight_software_not_imported_by_orchestrator_or_craft_paths PASSED
test_vehicle_profile_rejects_unknown_rung PASSED
test_imu_hal_protocol_is_structurally_satisfied_by_simulated_imu_hal PASSED
```

**T10 (full craft suite green):** `pytest -q` at repo root — **3204 passed, 1 skipped** (baseline before this Buy was 3192 passed, 1 skipped; delta is exactly the 12 new tests, no other file's pass/fail count moved).

**T11 (report confirms H-locks + naming split):** see §5 and §3 above.

Eight pre-existing tests hardcoded the prior checkpoint version string (`"0.5.0"`) as a version-pin assertion. Since this IC explicitly authorizes and requires the `0.5.1` bump (§0 decision 10), those eight assertions were re-pinned to `"0.5.1"` — same pattern used for the 0.4.3→0.5.0 bump in C1:

- `tests/test_geometry_prop_adapter_visor_x_b1.py`
- `tests/test_catalog_camera_power_w_b1.py`
- `tests/test_mission_power_w_b1.py`
- `tests/test_library_cameras_seed_b1.py`
- `tests/test_mission_vtx_identity_b1.py`
- `tests/test_bom_sku_resolved_cameras_b1.py`
- `tests/test_fase_c_capability_registry_scaffold_b1.py`
- `tests/test_fase_c_intent_safety_stub_b1.py`

(The historical `"Scaffold @ 0.5.0 != Flight Software shipped"` sentence in `src/jarvis/capabilities/__init__.py`'s docstring was left as-is — it correctly describes when C1 landed, not a version-pin assertion.)

---

## 5. Honesty / forbidden confirmation (IC §5)

| Rule | Status | Evidence |
|---|---|---|
| No claim of controlled flight / "armed" | ✅ | `flight_software/__init__.py` docstring states explicitly "This is a sensing-only stub. It does not make any vehicle flyable" |
| No real MCU drivers presented as product-ready | ✅ | Only `SimulatedImuHal` exists; docstring states "No real MCU / I2C / SPI / UART drivers... never touches a physical bus" |
| No mixer / ESC / PWM APIs | ✅ | `test_t3_no_actuator_shaped_methods` audits `ImuHal`/`SimulatedImuHal` public attributes against `pwm`/`esc`/`motor`/`mixer`/`arm`/`actuat` |
| No autonomy verbs executing | ✅ | No `flight_software/autonomy/` created; no verb-shaped method anywhere in the new modules |
| No wiring chat Intent → HAL | ✅ | `test_t9_...` greps `src/jarvis/core/` and `src/jarvis/adapters/` for `jarvis.flight_software`/`jarvis.vehicle_profiles` imports — none found |
| No marking full `flight_control` available | ✅ | `CapabilityRegistry.load_default()` unchanged, still empty (T7); no `CapabilityRecord` was added |
| No confusing craft catalog FC with FS package | ✅ | Explicit naming-split paragraph in `flight_software/__init__.py` docstring and in `docs/ARCHITECTURE.md` §1c |
| Version `0.5.1` | ✅ | T8 |

---

## 6. Files changed

**New:**
- `src/jarvis/flight_software/__init__.py`
- `src/jarvis/flight_software/flight_control/__init__.py`
- `src/jarvis/flight_software/flight_control/types.py`
- `src/jarvis/flight_software/flight_control/hal.py`
- `src/jarvis/flight_software/flight_control/sim_imu_hal.py`
- `src/jarvis/vehicle_profiles/__init__.py`
- `src/jarvis/vehicle_profiles/schemas.py`
- `src/jarvis/vehicle_profiles/loader.py`
- `src/jarvis/vehicle_profiles/smoke.py`
- `src/jarvis/vehicle_profiles/data/smoke_quad_hal_imu.json`
- `tests/test_fase_c_first_fc_rung_b1.py`
- `.jes/artifacts/implementation_report_fase_c_first_fc_rung_b1.md` (this file)

**Modified:**
- `pyproject.toml` — version `0.5.0` → `0.5.1`
- `README.md` — header banner, new "What v0.5.1 includes" section, "Next" section reworded to C4 and corrected the stale "`flight_software/` remain[s] later Fase C Buys" claim
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner + C3 queue row updated to "landed, awaiting ★ ACCEPT"; suite count 3192 → 3204
- `docs/PLATFORM_CAPABILITY_VISION.md` — §13 gained a C3 block + corrected the "flight_software/... remain future ICs (C3+)" line (C3 has now landed)
- `docs/ARCHITECTURE.md` — new §1c describing the `flight_software/flight_control/` + `vehicle_profiles/` first rung; removed the now-false "(C3+)" qualifier from §1b's closing sentence
- 8 test files — re-pinned stale `0.5.0` version-checkpoint assertions to `0.5.1` (listed in §4 above)

**Not touched (confirmed):** `orchestrator.py`, Board (`ui/spatial-board/`), `library/`, `src/jarvis/capabilities/*`, `.jes/state/engineering_state.json`.

---

## 7. Residual — what C4 should pick up

- Autonomy command surface (`TAKEOFF`/`HOLD`/`GO_TO`/...), still gated behind Safety (`reject`-default) per IC §12/§8.
- State estimation / filtering / attitude-rate-position controller / mixer / ESC — all still absent from `flight_control/`; each is its own future rung per C0's attack order.
- ELRS/CRSF decode remains C5.
- A real (non-simulated) HAL against actual hardware needs its own bench-gated IC — not this Buy.
- Git tag: `v0.5.1` still needs to be cut on Engineer ACCEPT.

---

## 8a. Engineer amendment applied (post-landing, on top of this IC)

The Engineer issued this amendment after the initial implementation above landed. It does not replace the IC — it clarifies honesty framing and adds one guardrail:

> Todo lo que este Buy escriba bajo `src/jarvis/flight_software/` y `vehicle_profiles/` es scaffold de plataforma en Python: contratos, `SimulatedImuHal`, smoke de perfil. No es el flight controller de producción. El runtime/firmware de `flight_control` real será C++ en Buys posteriores (path/build TBD en su propio IC). Prohibido en C3: presentar el código Python como FC de producción, drivers MCU "product-ready", o loop de control real. En docstrings del paquete, report y nota ARCHITECTURE/PLATFORM: frase explícita "Python scaffold / sim only — production flight_control runtime is C++ (future IC)." No crear árbol C++ ni CMake en este Buy. No ampliar el rung más allá de HAL+IMU simulado del IC.

**Applied:**

- Added the literal phrase **"Python scaffold / sim only — production flight_control runtime is C++ (future IC)"** to every package docstring in scope: `flight_software/__init__.py`, `flight_software/flight_control/__init__.py`, `flight_software/flight_control/hal.py`, `flight_software/flight_control/sim_imu_hal.py`, `vehicle_profiles/__init__.py`, `vehicle_profiles/smoke.py`.
- Added the same phrase to this report (§8a), `docs/ARCHITECTURE.md` §1c, `docs/PLATFORM_CAPABILITY_VISION.md` §13 (C3 block), and `README.md`'s "What v0.5.1 includes" section.
- Added `test_package_docstrings_carry_python_scaffold_amendment` — asserts the exact phrase is present in the `__doc__` of `jarvis.flight_software`, `jarvis.flight_software.flight_control`, and `jarvis.vehicle_profiles`.
- Added `test_no_cpp_or_cmake_tree_created` — walks both package directories and asserts no `.cpp`/`.cc`/`.cxx`/`.hpp`/`.hh`/`.h` file and no `CMakeLists.txt` exists anywhere under them.
- **No code behavior changed** — no rung was extended, no C++/CMake tree was created (verified by the new test), no `flight_control` implementation logic was added or removed. This was a docs/docstring-only amendment plus two new regression tests.
- Full suite re-run after the amendment: **3206 passed, 1 skipped** (was 3204 before the amendment; delta is exactly the 2 new tests).

## 8. Acceptance self-check against IC §7

- T1–T11: ✅ (T10/T11 are process gates, both satisfied — see §4/§5 above)
- Trees exist: ✅ (`src/jarvis/flight_software/`, `src/jarvis/vehicle_profiles/`)
- Only HAL+IMU sim rung: ✅ (no filter/estimator/controller/mixer/esc files)
- Smoke profile works: ✅ (T4, T5)
- Safety still reject-all: ✅ (T6)
- Version `0.5.1`: ✅ (T8)
- No craft coupling: ✅ (T9)
- No actuators: ✅ (T3)
