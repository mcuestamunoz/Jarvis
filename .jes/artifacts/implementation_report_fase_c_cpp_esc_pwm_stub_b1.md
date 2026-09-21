# Implementation Report — Fase C C++ ESC/PWM stub parity (`B1-fase-c-cpp-esc-pwm-stub`)

**IC:** [`implementation_contract_fase_c_cpp_esc_pwm_stub_b1.md`](implementation_contract_fase_c_cpp_esc_pwm_stub_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-21
**Status:** ★ ACCEPT CLOSED @ tag **`v0.5.12`**. See [review](implementation_review_fase_c_cpp_esc_pwm_stub_b1.md).

---

## 0. Read this first — steel-ladder parity, honesty summary

This Buy closes the one deliberate gap C13 left open: the C++ scaffold now has the **same sixth rung** as the Python wooden ladder — force→PWM-µs encoding plus an in-memory `SimulatedEscSink`, ported from Python C10 into `native/flight_control/`. It is **not** GPIO, not a real ESC write, not DShot/Oneshot/Multishot as a product encoding, and does not claim any motor spins or that an ESC is online. The Python `esc.py` module is untouched.

`fc_closed_loop_smoke` (C13's own tip) is unaffected and re-verified green in this Buy — the plant still steps on `MotorForceCommand` directly; the ESC encoding is an optional, separate rung, never required to close the loop.

---

## 1. Package layout vs IC §1

```text
native/flight_control/
├── include/jarvis/fc/esc.hpp   # NEW
├── src/esc.cpp                  # NEW
├── smoke/esc_pwm_smoke.cpp       # NEW — separate thin smoke (18 checks)
├── CMakeLists.txt                # esc.cpp added to jarvis_fc; fc_esc_pwm_smoke target + ctest
└── (filter, attitude, controller, rate_torque, mixer, plant — unchanged in behavior)
```

Matches the IC's normative layout exactly (§1). `esc.hpp`/`esc.cpp` names match the IC's "locked preferred" naming. A **separate** `fc_esc_pwm_smoke` executable was chosen over extending `closed_loop_smoke.cpp` — matching the IC's own "Defaults locked by Cursor" note ("Separate thin `fc_esc_pwm_smoke` preferred — keep closed-loop tip smoke focused").

---

## 2. Types / APIs implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| `EscPwmCommand` (`t_s`, `pulse_us[4]`, `protocol="pwm_us"` locked) | §2 | ✅ `jarvis::fc::EscPwmCommand` struct — `protocol` is a `std::string` locked to `"pwm_us"` by construction (no other value is ever produced) |
| `encode_motor_forces(forces, min_us=1000, max_us=2000)` | §2 | ✅ same linear map `pulse = min_us + clamp01(force) * (max_us - min_us)`; rejects `min_us >= max_us` or non-finite bounds via `std::invalid_argument` |
| `SimulatedEscSink` (`arm`/`disarm`, `apply` → `EscApplyResult`, `last_command()`, starts disarmed) | §2 | ✅ `jarvis::fc::SimulatedEscSink` — `armed_` starts `false`; `apply()` always records `last_command_` regardless of arm state |
| `EscApplyResult` (`applied`, `reason`, optional `pulse_us` echo) | §2 | ✅ `applied=false, reason="disarmed", pulse_us=cmd.pulse_us` while disarmed; `applied=true, reason=nullopt, pulse_us=cmd.pulse_us` while armed — exact mirror of Python C10's own two branches |
| Forbidden APIs (`write_gpio`, `send_dshot`, `open_serial`, `export_pwm`, pigpio) | §2 | ✅ none exist anywhere in `esc.hpp`/`esc.cpp`/`esc_pwm_smoke.cpp` — confirmed by grep (T6), comment-only mentions excluded |

No behavioral deviation from Python C10 was needed for this Buy — the algorithm is a single linear map plus a two-branch record-then-report state machine, both of which port 1:1 without simplification.

---

## 3. Build + smoke results (IC §4 T1–T5, T7)

```bash
$ cmake -S native/flight_control -B build/flight_control   # reconfigure (esc.cpp + new target)
-- Configuring done
-- Generating done

$ cmake --build build/flight_control
[100%] Built target jarvis_fc            # now includes esc.cpp
[100%] Built target fc_closed_loop_smoke
[100%] Built target fc_esc_pwm_smoke      # NEW
   (zero warnings with -Wall -Wextra)

$ ./build/flight_control/fc_esc_pwm_smoke
fc_esc_pwm_smoke: host scaffold, C++ ESC/PWM stub parity (not hardware)
  ok   T1 force=0 -> 1000us
  ok   T1 force=1 -> 2000us
  ok   T1 force=0.5 -> 1500us (linear midpoint)
  ok   T1 force=0.25 -> 1250us (linear)
  ok   T2 exactly 4 pulse widths
  ok   T2 protocol locked to pwm_us
  ok   T3 min_us == max_us rejected
  ok   T3 min_us > max_us rejected
  ok   T3 non-finite min_us rejected
  ok   T4 sink starts disarmed
  ok   T4 disarmed apply -> applied=false
  ok   T4 reason=disarmed
  ok   T4 command recorded even while disarmed
  ok   T5 sink armed
  ok   T5 armed apply -> applied=true
  ok   T5 no reason when applied
  ok   T5 last command stored matches applied command
  ok   T5b disarm() flips back to refuse
PASS: all ESC/PWM stub assertions held (18 checks)
exit code: 0

$ ./build/flight_control/fc_closed_loop_smoke   # re-verify T7, unaffected by this Buy
initial tilt error: 15.000 deg
final tilt error:   0.252 deg (after 200 steps)
PASS: tilt error strictly decreased and recovered below 2.0 deg
exit code: 0

$ cd build/flight_control && ctest --output-on-failure
1/2 Test #1: fc_closed_loop_smoke .............   Passed
2/2 Test #2: fc_esc_pwm_smoke .................   Passed
100% tests passed out of 2
```

**T7 confirmed:** `fc_closed_loop_smoke` result (`15° → 0.252°`) is byte-identical to C13's own report — this Buy did not touch `plant.cpp`, `mixer.cpp`, `controller.cpp`, `rate_torque.cpp`, `attitude.cpp`, or `filter.cpp`.

---

## 4. Tests (IC §4)

| ID | Check | Result |
|---|---|---|
| T1 | force 0 → 1000µs; force 1 → 2000µs; mid linear | ✅ smoke checks (§3) |
| T2 | Exactly 4 pulses; protocol pwm_us | ✅ smoke checks |
| T3 | Invalid min/max rejected | ✅ smoke checks (equal, inverted, non-finite bounds) |
| T4 | Disarmed apply → `applied=false`, reason disarmed, command still recorded | ✅ smoke checks |
| T5 | Armed apply → `applied=true`, last command stored | ✅ smoke checks (plus disarm() flips back, T5b) |
| T6 | No GPIO/DShot/serial/socket symbols in new esc sources (grep; honesty comments OK) | ✅ `test_t6_no_gpio_or_hardware_io_symbols_in_esc_sources` |
| T7 | `fc_closed_loop_smoke` still PASS | ✅ §3, `test_t7_closed_loop_tip_smoke_still_green_if_built` |
| T8 | No `.cpp` under `src/jarvis/`; Python ladder files still present | ✅ `test_t8a/b/c_*` |
| T9 | Python full suite green @ `0.5.12` | ✅ **3368 passed, 1 skipped** (was 3358 — exact +10 delta) |
| T10 | Report: PWM-µs only · sim sink · steel parity · != motors spinning · != GPIO | ✅ this report |
| T11 | Docs honest; no premature `v0.5.12` tag | ✅ §8 below |

New Python test module `tests/test_fase_c_cpp_esc_pwm_stub_b1.py` — **10 tests**, all passing:

```text
test_t8a_esc_sources_exist_and_wired_into_cmake PASSED
test_t8b_esc_cpp_not_under_python_package PASSED
test_t1_t2_t3_t4_t5_esc_pwm_smoke_binary_if_built PASSED
test_t7_closed_loop_tip_smoke_still_green_if_built PASSED
test_t6_no_gpio_or_hardware_io_symbols_in_esc_sources PASSED
test_t8c_python_esc_module_untouched PASSED
test_no_native_esc_wiring_into_craft_or_orchestrator PASSED
test_default_safety_and_autonomy_submit_still_reject PASSED
test_capability_registry_default_still_empty PASSED
test_t9_pyproject_version_is_0_5_12 PASSED
```

**Wrapper choice (IC §4 "document choice", same rationale as C13's own wrapper):** the pytest wrapper does not invoke `cmake`/`clang++` itself — it runs the already-built `fc_esc_pwm_smoke` and `fc_closed_loop_smoke` binaries if present, asserting exit 0 and a `PASS`/no-`FAIL` marker in stdout; if a binary is absent, the relevant test skips with a reason naming the exact build command. The actual configure+build+run was performed and verified manually for this Buy (§3).

**T9 (full suite):** `pytest -q` — **3368 passed, 1 skipped** (baseline before this Buy was 3358 passed, 1 skipped; delta is exactly the 10 new tests, no other file's pass/fail count moved).

Nineteen pre-existing test files hardcoded the prior checkpoint version string (`"0.5.11"`) as a version-pin assertion, including C13's own `test_fase_c_cpp_flight_control_scaffold_b1.py`. Since this IC explicitly requires the `0.5.12` bump (§0 decision 11), all nineteen were re-pinned to `"0.5.12"`:

- `tests/test_bom_sku_resolved_cameras_b1.py`
- `tests/test_catalog_camera_power_w_b1.py`
- `tests/test_fase_c_attitude_controller_rung_b1.py`
- `tests/test_fase_c_attitude_estimation_rung_b1.py`
- `tests/test_fase_c_autonomy_surface_b1.py`
- `tests/test_fase_c_capability_registry_scaffold_b1.py`
- `tests/test_fase_c_controlled_flight_sim_tip_b1.py`
- `tests/test_fase_c_cpp_flight_control_scaffold_b1.py`
- `tests/test_fase_c_esc_pwm_stub_rung_b1.py`
- `tests/test_fase_c_first_fc_rung_b1.py`
- `tests/test_fase_c_imu_filtering_rung_b1.py`
- `tests/test_fase_c_intent_safety_stub_b1.py`
- `tests/test_fase_c_mixer_rung_b1.py`
- `tests/test_fase_c_radio_dual_role_b1.py`
- `tests/test_fase_c_rate_torque_bridge_b1.py`
- `tests/test_geometry_prop_adapter_visor_x_b1.py`
- `tests/test_library_cameras_seed_b1.py`
- `tests/test_mission_power_w_b1.py`
- `tests/test_mission_vtx_identity_b1.py`

---

## 5. Honesty / forbidden confirmation (IC §5)

| Forbidden | Status | Evidence |
|---|---|---|
| Real pin / pigpio / DShot product | ✅ absent | T6 grep — zero GPIO/pigpio/`/dev/mem`/termios/serial/socket/DShot/Oneshot/Multishot/export_pwm code tokens in the new esc sources (comment-only honesty mentions excluded) |
| Breaking C13 tip silently | ✅ absent | §3, T7 — `fc_closed_loop_smoke` re-run, byte-identical `15° → 0.252°` result |
| Deleting/replacing Python `esc.py` | ✅ absent | `test_t8c_python_esc_module_untouched` — Python `encode_motor_forces`/`SimulatedEscSink` behavior re-verified unchanged |
| MCU / Safety / craft in this Buy | ✅ absent | `RejectAllSafetyGate` unchanged; no reference to `fc_esc_pwm_smoke` or native ESC symbols anywhere under `src/jarvis/core/` or `src/jarvis/adapters/` |

**"One front" discipline (process lock after C6):** this Buy stayed exactly within the C++ ESC/PWM stub parity scope. No MCU cross-compile, GPIO, DShot product path, Safety-real, ELRS, or craft wiring were touched or opened.

---

## 6. Integration rules (IC §3) — confirmed unchanged

- C13 modules — `MotorForceCommand` reused from `mixer.hpp` (`#include "jarvis/fc/mixer.hpp"` in `esc.hpp`); the plant tip was not reimplemented.
- Python `esc.py` — untouched (behavior re-verified, §5).
- Craft / `RejectAllSafetyGate` — untouched.
- Closed-loop tip smoke — remains force-driven; confirmed still green (§3, T7).

---

## 7. Files changed

**New:**
- `native/flight_control/include/jarvis/fc/esc.hpp`
- `native/flight_control/src/esc.cpp`
- `native/flight_control/smoke/esc_pwm_smoke.cpp`
- `tests/test_fase_c_cpp_esc_pwm_stub_b1.py`
- `.jes/artifacts/implementation_report_fase_c_cpp_esc_pwm_stub_b1.md` (this file)

**Modified:**
- `pyproject.toml` — version `0.5.11` → `0.5.12`
- `native/flight_control/CMakeLists.txt` — `esc.cpp` added to `jarvis_fc`; `fc_esc_pwm_smoke` target + `add_test` registered
- `native/flight_control/README.md` — new "Run the ESC/PWM stub smoke" section, layout diagram updated
- `docs/ARCHITECTURE.md` — new C14 paragraph after the C13 block
- `docs/PLATFORM_CAPABILITY_VISION.md` — §13 gained a new C14 block
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner + C14 queue row (implementer: landed-awaiting-review; Cursor review pass later synced to PASS / awaiting ACCEPT)
- `README.md` — header banner, new "What v0.5.12 includes (working tree — not yet tagged)" section
- 19 test files — re-pinned stale `0.5.11` version-checkpoint assertions to `0.5.12`

**Not touched (confirmed):** `orchestrator.py`, Board (`ui/spatial-board/`), `library/`, `src/jarvis/capabilities/*`, `src/jarvis/flight_software/autonomy/*`, `src/jarvis/flight_software/flight_control/esc.py` (byte-unchanged, re-verified §5), all other Python rung modules, `native/flight_control/{types,quat_math,filter,attitude,controller,rate_torque,mixer,plant}.{hpp,cpp}` (byte-unchanged), `.jes/state/engineering_state.json`.

---

## 8. Docs honesty confirmation (IC §6, §4 T11)

- README header banner: "**v0.5.12** — C14 C++ ESC/PWM stub CLOSED"
- `docs/IMPLEMENTATION_TASKS.md` PRIORIDAD: C14 CLOSED @ v0.5.12; await Engineer pick C15+
- `docs/ARCHITECTURE.md` / PLATFORM §13: ★ ACCEPT CLOSED @ tag `v0.5.12`
- Tag **`v0.5.12`** applied on Engineer ACCEPT
- Explicit **exists vs. impossible** statement, present in README/ARCHITECTURE/PLATFORM_CAPABILITY_VISION: **exists** = C++ force→µs encoding + in-memory sink (steel parity with Python C10); **impossible** = hardware ESC drive, spinning propellers, an armed physical vehicle.

---

## 9. Residual — what comes next

Per this IC's own §8 handoff: steel-ladder module parity is CLOSED after ACCEPT of this Buy (the C++ tree now mirrors all six Python rungs: filter, attitude, controller, rate_torque, mixer, esc — plus the plant tip). Next Buy (likely, still one front at a time, Engineer-prioritized): MCU cross-compile target, deepen C++ tests (e.g. a proper C++ unit-test framework instead of a hand-rolled smoke-check harness), a real (non-`RejectAll`) Safety policy, or a real link (ELRS) — not decided here.

---

## 10. Acceptance self-check against IC §7

- T1–T11: ✅ (see §4 table)
- C++ encode/arm work: ✅ (§3 — 18/18 smoke checks pass)
- Tip smoke still green: ✅ (§3, T7 — byte-identical `15° → 0.252°`)
- No GPIO: ✅ (§4 T6, §5)
- Python suite green: ✅ (3368 passed, 1 skipped)
- `0.5.12`: ✅
- Steel ladder has ESC rung: ✅ (§1, §2)
- Not FAIL conditions: no GPIO/DShot product path (§5) · tip not broken (§3, T7) · Python `esc.py` not rewritten (§5, §6) · no premature "ESC online" claim anywhere (§8)
