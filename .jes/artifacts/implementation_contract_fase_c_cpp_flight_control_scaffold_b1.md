# Implementation Contract — Fase C C++ flight_control scaffold (`B1-fase-c-cpp-flight-control-scaffold`)

**Project:** Jarvis  
**Date:** 2026-09-21  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (C++ tree ≠ firmware on hardware · CMake builds · no GPIO · Python craft SoT unchanged)

**Status:** ★ ACCEPT CLOSED @ tag **`v0.5.11`**  
**Parents:**
- [C0 Design Contract ★](design_contract_fase_c_skill_capability_architecture.md) — production FC runtime is C++ (Engineer amendment since C3)  
- [C12 ★ ACCEPT](implementation_contract_fase_c_rate_torque_bridge_b1.md) — rate→torque honesty CLOSED @ **`v0.5.10`**; wooden Python ladder complete  
- Engineer plan 2026-09-21: **rate→torque then C++ scaffold** — this Buy is the **material change**  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no Safety-real, ELRS decode, GPIO/PWM peripherals, or craft↔FS wiring in this Buy  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged** (Python craft remains design SoT)

**Type:** **Implementation Contract** — **first C++ material scaffold** for `flight_control`: open a native tree + CMake, **mirror the wooden-ladder modules**, and ship a **host smoke binary** that runs the closed-loop tip (or an equivalent documented vertical slice) **without** hardware I/O.  
**Package:** bump Jarvis `pyproject.toml` to **`0.5.11`** in this Buy (repo tip / docs); git tag **`v0.5.11`** only after Engineer ACCEPT.  
**Not** MCU flash / RTOS board bring-up · real GPIO/PWM/DShot · PX4/ArduPilot import · Safety-real · ELRS · replacing Python craft SoT · claiming “firmware flies.”

**Outputs (required):**
1. New tree under **`native/flight_control/`** (locked path — outside `src/jarvis/` Python package)  
2. Root **`CMakeLists.txt`** for that tree (C++17, host build) + build instructions in report / README snippet  
3. C++ sources mirroring the wooden ladder (see §1–§2) + **smoke executable**  
4. Tests: (a) CMake configure+build succeeds in CI/dev; (b) smoke binary exits 0 with documented tip criterion; (c) optional thin pytest wrapper that invokes the built binary if present / skip-with-reason if toolchain missing — **document choice**  
5. `.jes/artifacts/implementation_report_fase_c_cpp_flight_control_scaffold_b1.md`  
6. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **C++ scaffold ≠ flying / ≠ hardware FC**; Python wooden ladder remains the behavioral guide and craft stays Python  
7. `pyproject.toml` → **`0.5.11`** (+ re-pin `0.5.10` version-checkpoint tests)

**Checkpoint:** package **`0.5.11`** · Python suite ≥ **3348** still green · C++ smoke builds + tip criterion at ★

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-cpp-flight-control-scaffold`** — first **C++ material** for the wooden ladder |
| 2 | One front | Do **not** fold Safety-real, ELRS, craft↔FS, GPIO/DShot/pigpio, MCU SDK, or PX4/ArduPilot vendoring into this Buy |
| 3 | What this Buy demonstrates | `cmake -S native/flight_control -B build/flight_control && cmake --build …` produces a **host** binary that runs the **closed-loop tip** (tilted start → tilt error decreases) using C++ ports of the same algorithmic shape as Python C6–C12/C11. **Human:** “cambiamos de madera a acero el plano de la escalera — aún en el banco, sin cable al pin.” |
| 4 | Path (locked) | **`native/flight_control/`** only — do **not** drop `.cpp` under `src/jarvis/` |
| 5 | Language / standard | **C++17** · CMake ≥ 3.16 · host (desktop) build; no requirement for cross-compile to MCU in this Buy |
| 6 | Mirror scope | Layout mirrors Python rungs: at least modules/files corresponding to **filter, attitude, controller, rate_torque, mixer, plant** (names may be `snake` or `Camel` but map 1:1 in report). ESC/PWM encode may be included or stubbed — if stubbed, disclose; tip smoke must not need real PWM I/O |
| 7 | Behavioral guide | Algorithms should match Python intent (same formulas / same ENU conventions / same honesty notes). Exact float bit-identity with Python is **not** required; tip criterion (tilt error decreases from documented IC) **is** required |
| 8 | Hardware honesty | **No** `RPi.GPIO`, pigpio, `/dev/mem`, serial opens, sockets for ESC, or board BSP. Smoke is pure host math + stdlib I/O (stdout OK) |
| 9 | Python relationship | Python `flight_software/` **stays**; craft SoT unchanged. Do **not** delete or “replace” the wooden ladder. Docs must say: C++ is production-runtime **scaffold start**; Python remains the guide + craft platform |
| 10 | Safety / autonomy / registry | Untouched. RejectAll still default in Python. No C++ Safety rewrite in this Buy |
| 11 | Smoke binary | e.g. `fc_closed_loop_smoke` — prints or returns enough to assert tip recovery; exit nonzero on failure |
| 12 | Version | Bump **`0.5.10` → `0.5.11`**; tag **`v0.5.11`** on ACCEPT only |
| 13 | Forbidden claims | “Flashes to FC” · “flies” · “replaces PX4” · “hardware-verified” · marking flight capability `available` |

**Product sentence:**

```text
Abrir el árbol C++/CMake de flight_control y hacer correr en host el tip
de la escalera (lazo cerrado juguete) — mismo plano que en Python, otro
material, sin GPIO y sin fingir firmware en vuelo.
```

**Defaults locked by Cursor (Engineer: ACCEPT C12 then IC C++):**
- Path = `native/flight_control/`  
- Vertical slice = **closed-loop tip smoke** (not empty hello-world)  
- No MCU cross-compile required this Buy  
- Python ladder retained  

---

## 1. Package layout (normative)

```text
native/flight_control/
  CMakeLists.txt
  README.md                 # how to configure/build/run smoke (short)
  include/jarvis/fc/        # or include/fc/ — pick one, document
    types.hpp
    filter.hpp
    attitude.hpp
    controller.hpp
    rate_torque.hpp
    mixer.hpp
    plant.hpp
    # esc.hpp optional this Buy
  src/
    *.cpp                   # implementations
  smoke/
    closed_loop_smoke.cpp   # tip harness
```

Forbidden in this Buy: vendoring full autopilot stacks, `board/` BSP trees, `hal_gpio.cpp` that touches pins.

---

## 2. APIs / behavior (normative intent)

Mirror Python semantics (not necessarily identical API surface):

| Python guide | C++ responsibility |
|---|---|
| `ImuLowPassFilter` | EMA filter on accel/gyro |
| `ComplementaryAttitudeEstimator` | Attitude + **correct** accel-correction sign (C11 Amendment A) |
| `PdAttitudeController` | PD → body rate cmd |
| `LinearRateTorqueBridge` | Feedforward τ = g·ω |
| `QuadXMixer` | X allocation → 4 forces |
| `ToyQuadAttitudePlant` | Force-driven attitude plant → next IMU |
| C11 tip smoke | Closed loop: tilt error ↓ |

Document any intentional simplification vs Python in the report.

---

## 3. Integration rules

| Existing | C13 rule |
|---|---|
| Python `flight_software/` | Untouched except docstring/docs pointers + version pin |
| Craft / Board / library | Untouched |
| RejectAll | Untouched |
| C12 bridge honesty | Must exist in C++ path used by smoke |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | `native/flight_control/` exists with CMakeLists + smoke target |
| T2 | Configure + build succeeds on a documented host toolchain (clang++/g++) |
| T3 | Smoke: tilted IC → tilt error **strictly decreases** after N steps (N documented; may differ slightly from Python 0.252° — must still recover) |
| T4 | No GPIO/pigpio/`/dev/mem`/serial ESC symbols in new tree (grep) |
| T5 | No PX4/ArduPilot tree vendored |
| T6 | Python full suite still green @ **`0.5.11`** |
| T7 | Report: material change · host-only · ≠ flying · Python retained · C++ honesty |
| T8 | Docs PRIORIDAD / PLATFORM / ARCHITECTURE / README updated honestly (no premature `v0.5.11` tag) |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| Claiming onboard flight / flash | Scaffold host only |
| GPIO / real ESC | Hardware not authorized |
| Deleting Python ladder | Guide must remain |
| Safety-real / ELRS / craft wiring | One front |
| Silent bit-identity with Python as PASS gate | Not required; tip criterion is |

---

## 6. Docs

- PRIORIDAD / PLATFORM §13 / ARCHITECTURE / README “What v0.5.11 includes”  
- Explicit: **exists** = C++ tree + CMake + host tip smoke; **impossible** = hardware FC, flying, craft replacement  

---

## 7. Acceptance

**PASS when:** T1–T8 · C++ tip smoke builds and recovers · no GPIO · Python suite green · `0.5.11` · honesty docs.

**FAIL if:** empty hello-world only · hardware I/O · Python ladder removed · premature “we fly” · PX4 drop-in.

---

## 8. Handoff

```text
Engineer → ★ this IC (C13)
Claude   → native/flight_control + CMake + tip smoke + report + 0.5.11
Cursor   → review
Engineer → ACCEPT + tag v0.5.11
Cursor   → next Buy when prioritized
           (likely: deepen C++ parity · MCU target · Safety-real · link —
            still one front)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C12 CLOSED @ v0.5.10. C13 B1-fase-c-cpp-flight-control-scaffold READY —
native/flight_control + CMake + host tip smoke; no GPIO.
```

---

## 10. Engineer ★ checklist

1. Path **`native/flight_control/`** OK?  
2. Host CMake + **closed-loop tip smoke** (not empty hello-world) OK?  
3. No GPIO / no MCU flash this Buy OK?  
4. Python ladder **retained** OK?  
5. Version **`0.5.11`** OK?  
