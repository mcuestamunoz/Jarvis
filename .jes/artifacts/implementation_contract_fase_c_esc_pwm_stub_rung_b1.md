# Implementation Contract — Fase C ESC/PWM stub rung (`B1-fase-c-esc-pwm-stub-rung`)

**Project:** Jarvis  
**Date:** 2026-09-20  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (PWM numbers ≠ hardware write · no GPIO · no DShot bitbang)

**Status:** ★ ACCEPT CLOSED @ tag **`v0.5.8`**  
**Parents:**
- [C0 Design Contract ★](design_contract_fase_c_skill_capability_architecture.md) — §7 FC progression (`mixer → ESC → controlled flight`) · one rung per IC  
- [C9 ★ ACCEPT](implementation_contract_fase_c_mixer_rung_b1.md) — `MotorForceCommand` / `QuadXMixer` @ **`v0.5.7`**  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no Safety-real, C++/CMake production tree, ELRS, or craft wiring in this Buy  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — **sixth** `flight_control` rung only: **ESC/PWM command encoding stub** that maps normalized motor forces to **PWM pulse-width numbers** (and a simulated sink that records them).  
**Package:** bump to **`0.5.8`** in this Buy; git tag **`v0.5.8`** only after Engineer ACCEPT.  
**Not** real GPIO/PWM peripherals · DShot bit-banging · ESC UART protocols · arming that powers motors · Safety-real · C++/CMake production FC · craft Continuity wiring · claiming “motors spinning.”

**Outputs (required):**
1. Code under `src/jarvis/flight_software/flight_control/` (prefer new `esc.py`)  
2. Tests + thin smoke  
3. `.jes/artifacts/implementation_report_fase_c_esc_pwm_stub_rung_b1.md`  
4. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE — **PWM stub ≠ hardware ESC / ≠ flying**; C++ honesty phrase  
5. `pyproject.toml` → **`0.5.8`** (+ re-pin `0.5.7` version-checkpoint tests)

**Checkpoint:** package **`0.5.8`** · suite ≥ **3297** + new tests at ★

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-esc-pwm-stub-rung`** — next C0 §7 rung after mixer: **ESC/PWM encoding stub only** |
| 2 | One front | Do **not** fold Safety-real, C++/CMake production tree, ELRS, craft↔FS, or real peripheral I/O into this Buy |
| 3 | What this Buy demonstrates | Given a `MotorForceCommand` (4× `[0,1]`), produce **4 PWM pulse widths in microseconds** with a documented linear map, and accept them into a **`SimulatedEscSink`** that stores the last command. **Human:** “traduce fuerza de motor a la señal típica que un ESC esperaría — pero aún no la emite por un pin.” |
| 4 | Encoding (exactly one) | Ship **one** encoding only: classic **PWM pulse width** in **µs**, default map **`1000 + force * 1000`** → `[1000, 2000]` µs (document; allow constructor overrides for min/max µs with validation). **Forbidden:** shipping DShot/Oneshot/Multishot as product encodings “to compare” in this Buy |
| 5 | Hardware honesty | **No** `RPi.GPIO`, **no** pigpio, **no** `/dev/mem`, **no** serial/USB opens, **no** sockets for ESC. `SimulatedEscSink.apply(...)` only mutates in-memory state |
| 6 | Arming | Optional typed `armed: bool` on the sink **defaults to `False`**. Applying PWM while disarmed may either no-op (record refused) or still record widths with `applied=False` — **pick one, document, test**. **Forbidden:** any path that claims physical arm/power |
| 7 | Safety / autonomy | Do **not** weaken RejectAll. Do **not** auto-wire C4 HOLD → ESC. Computing/recording PWM is still **not** live actuation |
| 8 | Language honesty | **Python scaffold / sim only — production flight_control runtime is C++ (future IC)**. Phrase in new module docstring(s). No C++/CMake tree |
| 9 | Registry / craft | Registry stays empty; no Continuity/Board/`library/` edits |
| 10 | Smoke | Thin helper e.g. `run_esc_pwm_smoke`: mixer (or synthetic `MotorForceCommand`) → encode → simulated sink last command length 4 |
| 11 | Version | Bump **`0.5.7` → `0.5.8`**; tag **`v0.5.8`** on ACCEPT only |
| 12 | Forbidden claims | “Motors spinning” · “ESC online” · “armed and flying” · marking ESC capability `available` |

**Product sentence:**

```text
Mapear las 4 fuerzas del mixer a anchos de pulso PWM (µs) y registrarlos
en un sink simulado — sin GPIO, sin DShot real y sin fingir que los
motores giran.
```

---

## 1. Package layout (normative)

```text
src/jarvis/flight_software/flight_control/
  mixer.py   # C9 — reuse MotorForceCommand
  esc.py     # NEW — EscPwmCommand, encode_motor_forces_to_pwm, SimulatedEscSink
  # NO: dshot.py, gpio.py, hardware_pwm.py
```

---

## 2. Types / APIs (normative)

### 2.1 `EscPwmCommand`

| Field | Notes |
|---|---|
| `t_s` | float |
| `pulse_us` | tuple of **exactly 4** floats/ints — PWM high-time in **microseconds** |
| `protocol` | Literal `"pwm_us"` (locked) |
| `notes` | optional |

`extra="forbid"`. **No** GPIO pin numbers required on the command itself.

### 2.2 Encoder

```text
encode_motor_forces(forces: MotorForceCommand, *, min_us=1000, max_us=2000) -> EscPwmCommand
  # linear map force∈[0,1] → [min_us, max_us]; reject min>=max / non-finite
```

May be a free function or method on a small `PwmEscEncoder` class — one public encoding path only.

### 2.3 `SimulatedEscSink`

```text
armed: bool = False   # property or field; default False

arm() / disarm()      # flip flag only — no hardware

apply(cmd: EscPwmCommand) -> EscApplyResult
  # if disarmed: documented refuse (applied=False) OR still store with applied=False
  # if armed: store last command, applied=True
  # NEVER opens pins
```

`EscApplyResult` minimal: `applied: bool`, `reason: str | None`, optional echo of last `pulse_us`.

**Forbidden public APIs:** `write_gpio`, `open_serial`, `send_dshot`, `pigpio_*`, `export_pwm`.

---

## 3. Integration rules

| Existing | C10 rule |
|---|---|
| C9 MotorForceCommand | Required input to encoder |
| C8/C7/… | Untouched |
| C4 autonomy | Untouched |
| RejectAll | Untouched |
| Craft | Untouched |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | force `0` → `min_us`; force `1` → `max_us`; mid maps linearly |
| T2 | Exactly 4 pulse widths; `protocol=="pwm_us"` |
| T3 | Invalid min/max rejected |
| T4 | Disarmed `apply` does not claim success as hardware write (`applied=False` or equivalent) |
| T5 | Armed `apply` records last command in memory |
| T6 | No GPIO/serial/dshot-shaped public symbols; no imports of known GPIO libs |
| T7 | No new `.cpp`/CMake under `flight_software/` |
| T8 | RejectAll + autonomy submit still reject |
| T9 | Zero craft imports of esc symbols |
| T10 | Registry empty |
| T11 | `pyproject` **`0.5.8`**; re-pin `0.5.7` |
| T12 | Full suite green |
| T13 | Report: PWM-us only · sim sink · ≠ motors spinning · C++ honesty |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| Real pin toggling / pigpio | Hardware not authorized |
| DShot as shipped product | One-encoding lock |
| Claiming armed flight | Scaffold |
| Weakening RejectAll / craft wiring | Process |
| C++/CMake production FC tree | Future IC |

---

## 6. Docs

- PRIORIDAD / PLATFORM §13 / ARCHITECTURE / README “What v0.5.8 includes”  
- Explicit: **exists** = force→µs map + sim sink; **impossible** = real ESC drive, spinning props, controlled flight

---

## 7. Acceptance

**PASS when:** T1–T13 · PWM-us encoding works · sim sink only · no GPIO · RejectAll unchanged · `0.5.8` · craft isolation · C++ honesty present.

**FAIL if:** real peripheral I/O · DShot product path · fake flying · craft wiring.

---

## 8. Handoff

```text
Engineer → ★ this IC (C10)
Claude   → implement esc.py + tests + report + 0.5.8
Cursor   → review
Engineer → ACCEPT + tag v0.5.8
Cursor   → next Buy when prioritized
           (ladder tip “controlled flight” still NOT claimed;
            likely next forks: rate→torque honesty · Safety-real · C++ · link —
            still one front)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C9 CLOSED @ v0.5.7. C10 B1-fase-c-esc-pwm-stub-rung READY —
force→PWM µs + SimulatedEscSink; no GPIO/DShot.
```

---

## 10. Engineer ★ checklist

1. PWM-µs only (not DShot) OK?  
2. Default map 1000–2000 µs OK?  
3. Disarmed default + no hardware I/O OK?  
4. Version **`0.5.8`** OK?  
