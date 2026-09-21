# Implementation Contract — Fase C C++ ESC/PWM stub parity (`B1-fase-c-cpp-esc-pwm-stub`)

**Project:** Jarvis  
**Date:** 2026-09-21  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (C++ PWM µs ≠ GPIO write · same honesty as Python C10 · steel-ladder parity)

**Status:** ★ ACCEPT CLOSED @ tag **`v0.5.12`**  
**Parents:**
- [C10 ★ ACCEPT](implementation_contract_fase_c_esc_pwm_stub_rung_b1.md) — Python `encode_motor_forces` / `SimulatedEscSink` @ **`v0.5.8`** (behavioral guide)  
- [C13 ★ ACCEPT](implementation_contract_fase_c_cpp_flight_control_scaffold_b1.md) — first C++ material @ **`v0.5.11`**; ESC/PWM **intentionally omitted**  
- Engineer 2026-09-21: finish **steel-ladder parity** by inertia (ESC stub next) before MCU / Safety / link  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no MCU flash, GPIO, DShot product path, Safety-real, ELRS, or craft wiring in this Buy  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged** · Python wooden ladder **retained**

**Type:** **Implementation Contract** — **C++ parity for the ESC/PWM encoding stub only**: port Python C10’s force→PWM-µs map + in-memory `SimulatedEscSink` into `native/flight_control/`, so the steel ladder has the same sixth rung as the wood.  
**Package:** bump Jarvis `pyproject.toml` to **`0.5.12`**; git tag **`v0.5.12`** only after Engineer ACCEPT.  
**Not** GPIO/pigpio · DShot/Oneshot/Multishot as product encodings · MCU target · Safety-real · rewriting Python `esc.py` · claiming motors spin / ESC online.

**Outputs (required):**
1. `native/flight_control/include/jarvis/fc/esc.hpp` + `src/esc.cpp` (names locked preferred)  
2. CMake: add `esc.cpp` to `jarvis_fc`; add a thin smoke executable (e.g. `fc_esc_pwm_smoke`) and/or extend closed-loop smoke with optional encode→sink visibility — **tip closed-loop criterion must stay green**  
3. Tests: C++ unit/smoke asserts (encode endpoints + arming) + thin pytest wrapper (run binary if built / skip-with-build-hint) + Python suite still green @ `0.5.12`  
4. `.jes/artifacts/implementation_report_fase_c_cpp_esc_pwm_stub_b1.md`  
5. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **C++ ESC stub ≠ hardware write / ≠ flying**; steel ladder parity framing  
6. `pyproject.toml` → **`0.5.12`** (+ re-pin `0.5.11` version-checkpoint tests)

**Checkpoint:** package **`0.5.12`** · Python suite ≥ **3358** + new tests · C++ encode/arm smoke green at ★

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-cpp-esc-pwm-stub`** — finish steel-ladder module parity for ESC/PWM stub |
| 2 | One front | Do **not** fold MCU cross-compile, GPIO, DShot product encodings, Safety-real, ELRS, or craft↔FS into this Buy |
| 3 | What this Buy demonstrates | Given C++ `MotorForceCommand` (4× `[0,1]`), produce **4 PWM pulse widths in µs** with the same linear map as Python C10, and apply them to an in-memory `SimulatedEscSink` (disarmed default; record-but-refuse while disarmed). **Human:** “el peldaño ESC también existe en acero — sigue sin pin.” |
| 4 | Encoding (exactly one) | Classic **PWM-µs only**. Default map **`1000 + force * 1000`** → `[1000, 2000]` µs; allow min/max overrides with `min < max` and finite validation. **Forbidden:** shipping DShot/Oneshot/Multishot as product encodings |
| 5 | Arming | `armed` defaults **`false`**. `apply` **always records** last command; `applied=true` only when armed; while disarmed `applied=false` with reason `"disarmed"` (match Python C10 locked choice) |
| 6 | Hardware honesty | **No** GPIO, pigpio, `/dev/mem`, serial/USB opens, sockets. Sink mutates in-memory state only |
| 7 | Path | Stay under **`native/flight_control/`** — do not add `.cpp` under `src/jarvis/` |
| 8 | Python relationship | Do **not** change Python `esc.py` behavior. Optional docstring cross-link only. Wooden ladder remains the guide |
| 9 | Closed-loop tip | Existing `fc_closed_loop_smoke` must remain green (15° recovery). ESC smoke is separate or additive; plant still steps on **forces**, not PWM |
| 10 | Language | C++17 · same CMake project · host-only |
| 11 | Version | Bump **`0.5.11` → `0.5.12`**; tag **`v0.5.12`** on ACCEPT only |
| 12 | Forbidden claims | “Motors spinning” · “ESC online” · “armed and flying” · hardware PWM write |

**Product sentence:**

```text
Portar a C++ el stub ESC/PWM (fuerza→µs + sink en memoria) para cerrar
la paridad de la escalera de acero con la de madera — sin GPIO y sin
fingir que los motores giran.
```

**Defaults locked by Cursor (Engineer: procede):**
- Match Python C10 semantics (map + record-but-refuse)  
- Separate thin `fc_esc_pwm_smoke` preferred (keep closed-loop tip smoke focused)  
- No DShot · no MCU  

---

## 1. Package layout (normative)

```text
native/flight_control/
  include/jarvis/fc/esc.hpp     # NEW
  src/esc.cpp                   # NEW
  smoke/esc_pwm_smoke.cpp       # NEW preferred — or documented equivalent
  CMakeLists.txt                # add esc.cpp + smoke target + ctest
  # existing filter…plant unchanged in behavior
```

---

## 2. Types / APIs (normative intent — mirror Python C10)

| Item | Notes |
|---|---|
| `EscPwmCommand` | `t_s`, `pulse_us[4]`, protocol locked `"pwm_us"` (string or enum), optional notes |
| `encode_motor_forces(forces, min_us=1000, max_us=2000)` | linear; clamp force to `[0,1]`; reject bad bounds |
| `SimulatedEscSink` | `arm`/`disarm`; `apply` → `EscApplyResult`; `last_command()`; starts disarmed |
| `EscApplyResult` | `applied`, `reason`, optional `pulse_us` echo |

Forbidden: `write_gpio`, `send_dshot`, `open_serial`, `export_pwm`, pigpio APIs.

---

## 3. Integration rules

| Existing | C14 rule |
|---|---|
| C13 modules | Reuse `MotorForceCommand` from mixer; do not reimplement plant tip |
| Python `esc.py` | Untouched (behavior) |
| Craft / RejectAll | Untouched |
| Closed-loop tip smoke | Remains force-driven; must stay green |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | force 0 → 1000 µs; force 1 → 2000 µs; mid linear (C++ smoke or gtest-style asserts in smoke) |
| T2 | Exactly 4 pulses; protocol pwm_us |
| T3 | Invalid min/max rejected |
| T4 | Disarmed apply → `applied=false`, reason disarmed, command still recorded |
| T5 | Armed apply → `applied=true`, last command stored |
| T6 | No GPIO/DShot/serial/socket symbols in new esc sources (grep; honesty comments OK) |
| T7 | `fc_closed_loop_smoke` still PASS |
| T8 | No `.cpp` under `src/jarvis/`; Python ladder files still present |
| T9 | Python full suite green @ **`0.5.12`** |
| T10 | Report: PWM-us only · sim sink · steel parity · ≠ motors spinning · ≠ GPIO |
| T11 | Docs honest; no premature `v0.5.12` tag |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| Real pin / pigpio / DShot product | Hardware / one-encoding |
| Breaking C13 tip silently | Process |
| Deleting/replacing Python esc | Guide retained |
| MCU / Safety / craft in this Buy | One front |

---

## 6. Docs

- PRIORIDAD / PLATFORM §13 / ARCHITECTURE / README “What v0.5.12 includes”  
- Explicit: **exists** = C++ force→µs + sim sink (steel parity with C10); **impossible** = hardware ESC drive, spinning props  

---

## 7. Acceptance

**PASS when:** T1–T11 · C++ encode/arm work · tip smoke still green · no GPIO · Python suite green · `0.5.12` · steel ladder has ESC rung.

**FAIL if:** GPIO/DShot product · tip broken · Python esc rewritten · premature “ESC online.”

---

## 8. Handoff

```text
Engineer → ★ this IC (C14)
Claude   → esc.hpp/cpp + smoke + CMake + tests + report + 0.5.12
Cursor   → review
Engineer → ACCEPT + tag v0.5.12
Cursor   → next Buy when prioritized
           (steel ladder module parity CLOSED after ACCEPT;
            next forks: MCU cross-compile · deepen tests · Safety-real · link —
            still one front)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C13 CLOSED @ v0.5.11. C14 B1-fase-c-cpp-esc-pwm-stub READY —
C++ force→PWM µs + SimulatedEscSink; steel-ladder parity; no GPIO.
```

---

## 10. Engineer ★ checklist

1. C++ port of Python C10 semantics OK?  
2. PWM-µs only (not DShot) OK?  
3. Disarmed record-but-refuse OK?  
4. Tip smoke must stay green OK?  
5. Version **`0.5.12`** OK?  
