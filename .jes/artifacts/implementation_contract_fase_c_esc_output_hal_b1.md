# Implementation Contract — Fase C EscOutput HAL (`B1-fase-c-esc-output-hal`)

**Project:** Jarvis  
**Date:** 2026-09-22  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (named output port ≠ pin · mixer still force-only · no DShot packets · C24 `step` still does not `apply` · Simulated sink remains the only implementation)

**Status:** ★ ACCEPT CLOSED @ **`v0.5.24`**  
**Parents:**
- [C25 ★ ACCEPT](implementation_contract_fase_c_rc_setpoint_b1.md) — RC → setpoint @ **`v0.5.23`**  
- [C10 ★ ACCEPT](implementation_contract_fase_c_esc_pwm_stub_rung_b1.md) — `encode_motor_forces` + `SimulatedEscSink` @ **`v0.5.8`**  
- [C14 ★ ACCEPT](implementation_contract_fase_c_cpp_esc_pwm_stub_b1.md) — C++ ESC stub @ **`v0.5.12`**  
- [C24 ★ ACCEPT](implementation_contract_fase_c_control_loop_tick_b1.md) — `step` encodes PWM for visibility, never `apply` @ **`v0.5.22`**  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no GPIO, DShot product path, CRSF failsafe, MCU UART, silicon map, Safety execute, craft↔FS, or flash  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — name the **ESC output port** that C10/C14 already implemented as a concrete sink: `EscOutput`. Same contract for the in-memory simulated sink **today** and a future pin driver **later**. Mixer stays force-only. This Buy does **not** write a pin and does **not** ship DShot.  
**Package:** bump Jarvis `pyproject.toml` to **`0.5.24`**; git tag **`v0.5.24`** only after Engineer ACCEPT.  
**Not** motors spinning · not GPIO/pigpio/`/dev/mem` · not DShot/Oneshot/Multishot packets · not wiring `step` to `apply` · not CRSF failsafe (C27) · not MCU UART (C28) · not Safety execute.

**Outputs (required):**
1. `EscOutput` port in Python — **prefer extending** `src/jarvis/flight_software/flight_control/esc.py` (no new domain module unless a file split is forced and disclosed)  
2. C++ twin in `native/flight_control/include/jarvis/fc/esc.hpp` (+ `src/esc.cpp` if the interface cannot live header-only)  
3. `SimulatedEscSink` **is-a** `EscOutput`; existing C10/C14 `apply`/`arm`/`disarm` semantics **unchanged**  
4. Tests: `tests/test_fase_c_esc_output_hal_b1.py` + ≥1 Catch2 case  
5. `.jes/artifacts/implementation_report_fase_c_esc_output_hal_b1.md`  
6. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **EscOutput HAL ≠ pin ≠ motors ≠ DShot**  
7. `pyproject.toml` → **`0.5.24`** (+ re-pin `0.5.23` checkpoints)

**Checkpoint:** package **`0.5.24`** · Python suite ≥ **3538** + new tests · host `ctest` still green · C10/C14 arming tests still green · C24 `step` still does not call `apply`

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-esc-output-hal`** — name the output port; simulated sink vs future pin share one contract |
| 2 | One front | Do **not** fold GPIO, DShot product encoding, CRSF timeout failsafe, MCU UART, silicon, Safety execute, or auto `submit_command` |
| 3 | What this Buy demonstrates | El mixer sigue hablando **fuerzas**. Quien “emite” hacia un ESC habla un **puerto** (`EscOutput`). Hoy el único aparato enchufado es el sink en memoria; mañana un pin puede implementar el mismo puerto. **Human:** “el enchufe ya tiene forma; aún no hay cable.” |
| 4 | Mixer isolation | `mixer.py` / `mixer.hpp` stay **force-only**. **Forbidden:** PWM µs, DShot, pin numbers, or protocol names in the mixer |
| 5 | HAL method | `EscOutput` exposes **`apply_forces(MotorForceCommand) -> EscApplyResult`**. Encoding (today: C10 PWM-µs via existing `encode_motor_forces`) lives **inside** the sink, not the mixer. A future DShot implementation would encode **inside its own** `apply_forces` — still not in the mixer |
| 6 | Keep C10 `apply(EscPwmCommand)` | `SimulatedEscSink.apply(cmd)` remains. `apply_forces` **may** encode then call `apply`. Arming: start disarmed; record always; `applied=true` only when armed (`reason="disarmed"` otherwise) — **byte-compatible with C10/C14 tests** |
| 7 | Only one implementation this Buy | `SimulatedEscSink`. **Forbidden:** GPIO sink, dummy pin numbers, DShot bitbang, `/dev` opens. A `NotImplemented` / unimplemented pin class is also forbidden as product surface |
| 8 | C24 `step` | **Must not** call `EscOutput` / `SimulatedEscSink.apply` / `apply_forces`. PWM field on `ControlTickResult` stays visibility-only, as C24 locked |
| 9 | C25 / radio | `rc_setpoint.py` math **unchanged**. `radio.py` still no stick/ESC APIs |
| 10 | Languages | **Both** Python + C++ (board-prep axis) |
| 11 | Native-tree lock | **Zero** `crsf`/`elrs` under `native/` (even comments), same as C25 N1 |
| 12 | Safety / adapter | RejectAll default; `RadioIntentAdapter` still NotImplemented |
| 13 | Version | **`0.5.23` → `0.5.24`**; tag **`v0.5.24`** on ACCEPT only |
| 14 | Forbidden claims | “Motors spinning” · “ESC on a wire” · “DShot ready” · `step` writes a pin · mixer knows protocol |

**Product sentence:**

```text
Nombrar EscOutput: el mixer entrega fuerzas; el sink simulado (y un
futuro pin) implementan el mismo puerto. Sin GPIO, sin DShot, sin
enchufar step al apply.
```

**Defaults locked by Cursor (Engineer: next in board-prep cola after C25 ACCEPT):**
- Extend `esc.py` / `esc.hpp` — no parallel `dshot.py`  
- `apply_forces` on the port; keep C10 `apply(EscPwmCommand)`  
- `step` still does not emit  

---

## 1. Package layout (normative intent)

```text
src/jarvis/flight_software/flight_control/
  esc.py          # EXTEND — EscOutput + SimulatedEscSink is-a
  mixer.py        # UNCHANGED (force-only)
  loop.py         # UNCHANGED (no apply)

native/flight_control/
  include/jarvis/fc/esc.hpp   # EXTEND
  src/esc.cpp                 # EXTEND if needed
  tests/                      # ≥1 new Catch2 case

tests/
  test_fase_c_esc_output_hal_b1.py
```

Do **not** add `.cpp` under `src/jarvis/`. Do **not** put this on `radio.py`.

Python: `EscOutput` as `abc.ABC` (or `typing.Protocol` if ABC fights pydantic — disclose). C++: abstract base with virtual destructor; `SimulatedEscSink` public-inherits.

---

## 2. Types / APIs (normative intent)

```text
EscOutput
  apply_forces(forces: MotorForceCommand) -> EscApplyResult
  arm() / disarm() / armed  # same C10 semantics

SimulatedEscSink(EscOutput)
  apply(cmd: EscPwmCommand) -> EscApplyResult   # C10, keep
  apply_forces(...)                             # encode_motor_forces then apply
```

C++: same shape. No new encoding besides existing PWM-µs.

### 2.1 Non-goals

No GPIO, pigpio, DShot packets, Oneshot, Multishot, ESC UART, pin maps, `step`→`apply` wiring, failsafe timer, Safety execute.

---

## 3. Integration rules

| Existing | C26 rule |
|---|---|
| Mixer | Force-only; grep-clean of `dshot` / `gpio` / `pulse_us` in **code** (docstring hard-cut listing `dshot` as absent is OK) |
| C10 encode | Reused, not rewritten |
| C24 `step` | Still no `apply` / `apply_forces` |
| C25 mapper | Unchanged |
| C17 | Untouched |
| `fc_esc_pwm_smoke` | May keep calling `apply(EscPwmCommand)`; may also show `apply_forces` — **document** |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | `SimulatedEscSink` is instance/subclass of `EscOutput` (Python) / convertible to `EscOutput*` (C++) |
| T2 | `apply_forces` disarmed: records, `applied=False`, `reason="disarmed"` |
| T3 | `apply_forces` armed: `applied=True`; pulses match `encode_motor_forces` |
| T4 | C10 `apply(EscPwmCommand)` still record-but-refuse while disarmed |
| T5 | Mixer source has no GPIO/DShot **call** (force-only API unchanged) |
| T6 | `loop.step` source still has no `SimulatedEscSink` / `.apply(` / `apply_forces` |
| T7 | `RadioIntentAdapter` not_implemented; RejectAll default |
| T8 | No GPIO/`pigpio`/`/dev/mem` in `esc.py` / `esc.hpp` **code** |
| T9 | C++ Catch2: `apply_forces` armed/disarmed |
| T10 | `pyproject` **`0.5.24`**; re-pin `0.5.23` |
| T11 | Full Python suite + host `ctest` green |
| T12 | Report: EscOutput HAL ≠ pin ≠ motors ≠ DShot |

---

## 5. Honesty / forbidden

```text
EscOutput HAL ≠ pin ≠ motors ≠ DShot
```

**Exists:** a named port; the simulated sink implements it; mixer does not know the wire protocol.  
**Impossible:** a motor on a wire; a DShot stream; `step` actuating.

---

## 6. Docs

PRIORIDAD · PLATFORM §13 · ARCHITECTURE · README “What v0.5.24 includes”

---

## 7. Acceptance

**PASS when:** T1–T12 · one implementation (simulated) · mixer force-only · `step` does not apply · version `0.5.24`.  
**FAIL if:** GPIO shipped · DShot packets · mixer learns protocol · `step` calls the sink · motors claimed spinning.

---

## 8. Handoff

```text
Engineer → ★ this IC (C26)
Claude   → EscOutput port + SimulatedEscSink is-a + tests + report + 0.5.24
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.24
Cursor   → next: C27 CRSF stream-timeout failsafe (default on this axis)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C25 CLOSED @ v0.5.23. C26 B1-fase-c-esc-output-hal READY —
named EscOutput port; SimulatedEscSink implements it; mixer
force-only; no pin, no DShot, step still does not apply.
```

---

## 10. Engineer ★ checklist

1. Buy = **name the ESC port** (not a pin) OK?  
2. `apply_forces` on the port · keep C10 `apply` OK?  
3. Mixer force-only · no DShot this Buy OK?  
4. `step` still does not emit OK?  
5. Version **`0.5.24`** OK?  
