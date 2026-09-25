# Implementation Contract — Fase C denser `step` ticks (`B1-fase-c-step-failsafe-hold-ticks`)

**Project:** Jarvis  
**Date:** 2026-09-25  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (many ticks ≠ flying ≠ 6-DoF · failsafe→`step` ≠ motors cut)

**Status:** ★ ACCEPT CLOSED @ **`v0.5.33`**  
**Parents:**
- [C34](implementation_contract_fase_c_spi_scripted_gyro_probe_b1.md) — `probe_rx` @ **`v0.5.32`**  
- [C24 ★ ACCEPT](implementation_contract_fase_c_control_loop_tick_b1.md) — named `step()` @ **`v0.5.22`**  
- [C27 ★ ACCEPT](implementation_contract_fase_c_crsf_stream_timeout_failsafe_b1.md) — stale RC + `failsafe_loop_inputs` @ **`v0.5.25`**  
- [situation after C33](engineer_note_fase_c_situation_after_c33_2026_09_25.md) §3.1 — front **2** of the four no-pin attacks  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**

**Type:** **Implementation Contract** — **tests only**. Lock three facts C24/C27 already *allow* but do not *chain*: (1) **many** `step()` ticks on canned IMU stay finite, (2) a **stale** hold watch feeds `failsafe_loop_inputs` **into** the same `step()`, (3) **hold** means keep feeding `level_setpoint` (not AutonomyVerb execute). Plant stays outside. No new 6-DoF. No production module.  
**Package:** bump to **`0.5.33`**; tag **`v0.5.33`** only after Engineer ACCEPT.  
**Not** 6-DoF · not plant inside `step` · not Safety execute · not folding failsafe into `ControlLoop` · not `probe_rx` as an IMU · not DShot wire · not C30 DFU · not Taller CSS · not standoff points.

**Outputs (required):**
1. Tests: `tests/test_fase_c_step_failsafe_hold_ticks_b1.py` + Catch2 cases in `native/flight_control/tests/test_loop.cpp` (or a new `test_loop_density.cpp` wired in CMake — prefer **extend** `test_loop.cpp`)  
2. Report + docs honesty: **many ticks ≠ flying ≠ 6-DoF ≠ failsafe motors cut**  
3. `pyproject.toml` → **`0.5.33`**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-step-failsafe-hold-ticks`** — denser **tests** of the existing tick |
| 2 | One front | Do **not** fold a plant, 6-DoF, IMU from `probe_rx`, failsafe-inside-`step`, Safety execute, DShot wire, C30 DFU, Taller CSS, standoff points |
| 3 | What this Buy demonstrates | C24 late **una vez**. C27 sabe decir “stale”. Hoy el **mismo** `step()` aguanta mil ticks de IMU de lata y, si el mando se calla, come la consigna de suelo. **Human:** “el corazón sigue latiendo sin planta; si el radio se calla, no baila la última canción.” |
| 4 | Tests only | `loop.py` / `loop.cpp` / `rc_hold.*` / `crsf_failsafe.py` / `spi_probe.*` **byte-unchanged**. Glue lives in **tests**: caller does `inputs = failsafe_loop_inputs(t)` then `loop.step(sample, inputs.setpoint, inputs.collective)` (names as already shipped) |
| 5 | Many ticks | **N = 1000**. Canned level IMU (`accel ≈ (0,0,-9.81)`, gyro zeros), `level_setpoint`, collective `0.5`. Every tick: four forces **finite** and in **`[0, 1]`**. No `ToyQuadAttitudePlant` in this path (C11’s 200-step *with* plant stays a different test) |
| 6 | Failsafe → `step` | `RcHoldWatch` / `CrsfRcHoldWatch` stale (never noted, or past 0.5 s) → `failsafe_loop_inputs(t_s)` → `step`. Forces finite in `[0, 1]`. Collective passed into `step` is **0**. Do **not** call `EscOutput` / GPIO |
| 7 | Hold | Keep passing **`level_setpoint`** for those N ticks. **Forbidden:** `submit_command(HOLD)` becoming `executed`; this is not C4/C17 execute |
| 8 | IMU | `ImuSample` is still a **struct the caller fills**. Do **not** decode SPI / `probe_rx` into accel/gyro this Buy |
| 9 | Native lock | Zero new `crsf`/`elrs` under `native/` (C++ uses `RcHoldWatch` / `failsafe_loop_inputs` already there) |
| 10 | Version | **`0.5.32` → `0.5.33`**. C34 is tagged `v0.5.32` — implement now |
| 11 | Forbidden | “we fly” · “6-DoF” · “failsafe cut motors” · “HOLD executed” · gyro live |

**Product sentence:**

```text
Mil ticks de step() con IMU de lata, y stale RC → consigna nivel +
collective 0 metidos en el mismo step — sigue sin ser volar.
```

**Defaults locked by Cursor:**
- Tests only · N=1000 · no plant on this path  
- Failsafe glue in the test, not inside `ControlLoop`  
- Python + C++ Catch2  

---

## 1. Package layout (normative intent)

```text
tests/test_fase_c_step_failsafe_hold_ticks_b1.py     # NEW
native/flight_control/tests/test_loop.cpp            # extend (or new test_loop_density.cpp + CMake)
```

Do **not** add a production harness under `src/jarvis/` or `include/jarvis/fc/` unless a test cannot call the existing APIs (then **STOP**).

---

## 2. Non-goals

6-DoF plant, `step` calling `plant.step`, folding `RcHoldWatch` into `ControlLoop`, IMU from `probe_rx`, Safety execute, DShot wire, C30 DFU, Taller CSS, standoff points.

---

## 3. Integration rules

| Existing | C35 rule |
|---|---|
| C24 `step` | **Byte-unchanged** — tests call it more |
| C27 failsafe | **Byte-unchanged** — tests chain it into `step` |
| C11 plant smoke | **Unchanged** — still the *with-plant* recovery path |
| C34 `probe_rx` | **Unchanged** — not an IMU this Buy |
| Safety RejectAll | **Unchanged** |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | 1000 ticks, canned level IMU, no plant → 4 forces finite in `[0,1]` every tick (Python + Catch2) |
| T2 | Stale watch → `failsafe_loop_inputs` → `step` with **collective 0** → 4 forces finite in `[0,1]` (Python + Catch2) |
| T3 | T1 uses `level_setpoint` throughout (hold-as-input, not Autonomy execute) |
| T4 | `loop.py` / `loop.cpp` / `loop.hpp` / `rc_hold.*` / `crsf_failsafe.py` git-unchanged |
| T5 | New tests do not import `probe_rx` / `SpiBytePort` as a sensor |
| T6 | Default Safety still RejectAll; `submit_command(HOLD)` still `not_attempted` |
| T7 | Native zero new `crsf`/`elrs` |
| T8 | `pyproject` **`0.5.33`** |
| T9 | Full suite + `ctest` green |
| T10 | Report: many ticks ≠ flying ≠ 6-DoF ≠ failsafe motors cut |

---

## 5. Honesty / forbidden

```text
many ticks ≠ flying ≠ 6-DoF ≠ failsafe motors cut ≠ HOLD executed
```

**Exists:** tests that call `step()` a thousand times and that feed failsafe inputs into it.  
**Impossible:** a flying plant; motors cutting on timeout; IMU from the ICM42688P.

---

## 6. Docs

PRIORIDAD · PLATFORM §13 · ARCHITECTURE · README “What v0.5.33 includes”

---

## 7. Acceptance

**PASS when:** T1–T10 · production loop/failsafe frozen · no plant on the new path.  
**FAIL if:** 6-DoF · `step` calls plant · failsafe folded into `ControlLoop` · `probe_rx` as IMU · Safety execute · HOLD `executed`.

---

## 8. Handoff

```text
Engineer → ACCEPT C34 + tag v0.5.32  (done)
Engineer → ★ this IC (C35)           (done)
Claude   → tests + report + 0.5.33   (done)
Cursor   → independent review        (done — PASS WITH NOTES)
Engineer → ACCEPT + tag v0.5.33      (done)
Cola     → 3 Taller CSS · 4 standoff points
```

---

## 9. PRIORIDAD blurb (paste on ★)

```text
Fase C: C35 CLOSED @ v0.5.33. Cola: Taller CSS cuboid · standoff points.
Silicon parked until bench.
```

---

## 10. Engineer ★ checklist

1. Buy = **tests only** (no new plant / no failsafe-inside-`step`) OK?  
2. N=1000 · stale → collective 0 into `step` OK?  
3. `probe_rx` stays off the IMU path OK?  
4. Version **`0.5.33`** after C34 tag OK?  
