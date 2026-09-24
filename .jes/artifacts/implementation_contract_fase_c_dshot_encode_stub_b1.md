# Implementation Contract — Fase C DShot encode stub (`B1-fase-c-dshot-encode-stub`)

**Project:** Jarvis  
**Date:** 2026-09-24  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (frame in RAM ≠ pin ≠ motors ≠ C30 DFU)

**Status:** READY — awaiting Engineer ★  
**Parents:**
- [C30 ★ ACCEPT](implementation_contract_fase_c_mcu_flash_observable_b1.md) — DFU-able LED image @ **`v0.5.28`**; **not flashed on desk**  
- [C26 ★ ACCEPT](implementation_contract_fase_c_esc_output_hal_b1.md) — `EscOutput` + `SimulatedEscSink` still PWM-µs @ **`v0.5.24`**  
- [C10/C14] PWM encode — linear force → pulse_us; **not** DShot  
- Engineer 2026-09-24: [bench before silicon](engineer_note_fase_c_bench_before_silicon_2026_09_24.md) — no GPIO/DShot *wire* until bench; software continues on the Mac  
- Desk ESC (when later wired): HGLRC 60A 6S, Bluejay, DShot150/300/600 — **protocol name only** this Buy  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**

**Type:** **Implementation Contract** — name the **DShot 16-bit frame** the desk ESC will someday want: encode throttle (+ optional telemetry request bit) + nibble-XOR checksum **in RAM**. Same idea as C10 PWM-µs: the number exists; there is still no timer, no GPIO, no motor.  
**Package:** bump Jarvis `pyproject.toml` to **`0.5.29`**; git tag **`v0.5.29`** only after Engineer ACCEPT.  
**Not** GPIO / TIM / DMA bit-bang · not DShot150 vs 300 vs 600 as a *pin period* · not `EscOutput` switching off PWM this Buy · not C30 DFU · not Safety execute · not craft↔FS.

**Outputs (required):**
1. Python `src/jarvis/flight_software/flight_control/dshot.py` + C++ `include/jarvis/fc/dshot.hpp` + `src/dshot.cpp` added to `jarvis_fc`  
2. `encode_dshot_frame(throttle_11bit, telemetry=False) -> uint16` (both languages)  
3. Tests: `tests/test_fase_c_dshot_encode_stub_b1.py` + ≥1 Catch2 case  
4. `.jes/artifacts/implementation_report_fase_c_dshot_encode_stub_b1.md`  
5. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **DShot encode ≠ pin ≠ motors ≠ flying**  
6. `pyproject.toml` → **`0.5.29`** (+ re-pin `0.5.28` checkpoints)

**Checkpoint:** package **`0.5.29`** · Python suite ≥ **3619** + new tests · host `ctest` still green · MCU `.elf` still links · C30 `hello_led` / `stub_main` **byte-unchanged** · C26 `EscOutput` default encoding still PWM-µs

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-dshot-encode-stub`** — DShot **frame encode** in RAM |
| 2 | One front | Do **not** fold GPIO, timers, DMA, C30 DFU, USART, Safety execute, or craft↔FS |
| 3 | What this Buy demonstrates | El ESC de mesa habla DShot; hoy Jarvis puede **escribir el paquete de 16 bits** que ese protocolo usa. **Human:** “ya sabemos el número; todavía no late en ningún pin.” |
| 4 | Axis | Python + C++ (parity). Do **not** put DShot code under `src/jarvis/core/` |
| 5 | Frame (locked) | 16 bits: bits 15–5 = 11-bit value, bit 4 = telemetry request, bits 3–0 = checksum. `value = (throttle << 1) \| telem`. `checksum = (value ^ (value >> 4) ^ (value >> 8)) & 0xF`. `frame = (value << 4) \| checksum`. Throttle integer `0..2047` inclusive; reject outside |
| 6 | Special range | Document: `0..47` are DShot **commands**, `48..2047` are throttle. This Buy **encodes the 11-bit field as given** — it does **not** invent a command table (beep, 3D, etc.) |
| 7 | Force map (optional helper) | If adding `encode_motor_forces_dshot(forces) -> 4× uint16`, map clamped force `[0,1]` linearly onto throttle **`48..2047`** (not 0..2047 — 0 would be a command). Document. PWM `encode_motor_forces` **unchanged** |
| 8 | `EscOutput` / `SimulatedEscSink` | **Still PWM-µs.** Do **not** switch `apply_forces` to DShot this Buy. A future pin driver encodes DShot inside its own override |
| 9 | Rates 150/300/600 | May appear in comments as **the ESC’s advertised names**, not as bit timings. **Forbidden:** claiming a timer period or GPIO toggle rate |
| 10 | Native-tree lock | **Zero** `crsf`/`elrs` under `native/` (even comments) |
| 11 | C30 freeze | `hello_led.c` / `hello_led.h` / `stub_main.cpp` **byte-unchanged**. Idle stays PC13, not DShot |
| 12 | Version | **`0.5.28` → `0.5.29`**; tag **`v0.5.29`** on ACCEPT only |
| 13 | Forbidden claims | “DShot live” · “motors spin” · “GPIO” · “this is Bluejay on the ESC” · C30 LED was seen on desk |

**Product sentence:**

```text
Codificar la trama DShot de 16 bits (throttle + checksum) en RAM —
igual que C10 hizo con µs PWM; todavía no hay pin ni motor.
```

**Defaults locked by Cursor (Engineer: software continues; bench before wire):**
- Algorithm §0.5  
- PWM sink unchanged  
- C30 LED files frozen  

**Known vectors (must pass in both languages):**

| throttle | telem | frame |
|---|---|---|
| 0 | 0 | `0x0000` |
| 48 | 0 | `0x0606` |
| 2047 | 0 | `0xFFEE` |

(Verify 48: `value=96=0x60`, checksum `0x6`, frame `0x0606`. Verify 2047: `value=0xFFE`, checksum `0xE`, frame `0xFFEE`.)

---

## 1. Package layout (normative intent)

```text
src/jarvis/flight_software/flight_control/dshot.py
native/flight_control/include/jarvis/fc/dshot.hpp
native/flight_control/src/dshot.cpp          # add to jarvis_fc
native/flight_control/tests/test_dshot.cpp   # Catch2
tests/test_fase_c_dshot_encode_stub_b1.py
```

Do **not** name CRSF in the C++ files.

---

## 2. Types / APIs (normative intent)

```text
encode_dshot_frame(throttle: int, telemetry: bool = False) -> int  # 0..65535, actually 16-bit
# C++: uint16_t encode_dshot_frame(uint16_t throttle, bool telemetry = false);
# throw / return documented error if throttle > 2047
```

### 2.1 Non-goals

GPIO, TIM, DMA, bit-bang, ESC registers, Bluejay passthrough, C30 DFU, switching `SimulatedEscSink` off PWM.

---

## 3. Integration rules

| Existing | C31 rule |
|---|---|
| C10/C14/C26 PWM encode + `EscOutput` | **Unchanged** default path |
| C30 hello_led / stub_main | **Byte-unchanged** |
| Native CRSF lock | Holds |
| Host `ctest` | Green + new DShot cases |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | Vectors §0: 0→`0x0000`, 48→`0x0606`, 2047→`0xFFEE` (Python + C++) |
| T2 | Telemetry bit set changes bit 4 of `value` before checksum (one explicit case) |
| T3 | throttle `2048` / negative (Python) rejected |
| T4 | `encode_motor_forces` PWM still `1000..2000` µs; `SimulatedEscSink` still PWM |
| T5 | C30 `stub_main.cpp` / `hello_led.c` git-unchanged |
| T6 | Native grep still zero `crsf`/`elrs` |
| T7 | No GPIO / TIM / `BSRR` / pigpio in new dshot files |
| T8 | Catch2 cases for T1–T2 |
| T9 | `pyproject` **`0.5.29`**; re-pin `0.5.28` |
| T10 | Full Python suite + host `ctest` green |
| T11 | Report: DShot encode ≠ pin ≠ motors ≠ flying |

---

## 5. Honesty / forbidden

```text
DShot encode ≠ pin ≠ motors ≠ flying
```

**Exists:** a 16-bit DShot packet computed in software.  
**Impossible:** an ESC seeing a waveform; C30 LED observed on the desk (still Engineer smoke).

---

## 6. Docs

PRIORIDAD · PLATFORM §13 · ARCHITECTURE · README “What v0.5.29 includes”

---

## 7. Acceptance

**PASS when:** T1–T11 · PWM sink unchanged · C30 LED files frozen · version `0.5.29`.  
**FAIL if:** GPIO/timer · `apply_forces` switched to DShot · command table invented as product · live-motor claim.

---

## 8. Handoff

```text
Engineer → ★ this IC (C31)
Claude   → encode_dshot_frame Python+C++ + tests + report + 0.5.29
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.29
Cursor   → next remains parked: DShot wire · USART on-chip · C30 desk DFU · craft↔FS
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C30 CLOSED @ v0.5.28 (software; LED not observed on desk).
C31 B1-fase-c-dshot-encode-stub READY — 16-bit DShot frame in RAM;
not pin, not motors. Bench still before any wire.
```

---

## 10. Engineer ★ checklist

1. Buy = **DShot frame in RAM** (not GPIO) OK?  
2. Algorithm + vectors `0x0000` / `0x0606` / `0xFFEE` OK?  
3. PWM `EscOutput` stays default OK?  
4. C30 LED files frozen · no DFU this Buy OK?  
5. Version **`0.5.29`** OK?  
