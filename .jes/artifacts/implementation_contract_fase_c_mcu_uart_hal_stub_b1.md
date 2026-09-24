# Implementation Contract — Fase C MCU UART HAL stub (`B1-fase-c-mcu-uart-hal-stub`)

**Project:** Jarvis  
**Date:** 2026-09-24  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (byte port ≠ chip USART · ≠ Darwin `IOSSIOSPEED` · ≠ live ELRS · native tree still zero CRSF/ELRS · `stub_main` still no UART ISR · C22/C23 host serial untouched)

**Status:** READY — awaiting Engineer ★  
**Parents:**
- [C27 ★ ACCEPT](implementation_contract_fase_c_crsf_stream_timeout_failsafe_b1.md) — RC hold-timeout @ **`v0.5.25`**  
- [C23 ★ ACCEPT](implementation_contract_fase_c_crsf_host_baud_b1.md) — Darwin host baud 420000 @ **`v0.5.21`** (host Mac **only** — not this Buy)  
- [C22 ★ ACCEPT](implementation_contract_fase_c_crsf_host_serial_b1.md) — host FD/path ingest @ **`v0.5.20`**  
- [C18 ★ ACCEPT](implementation_contract_fase_c_cpp_mcu_freestanding_elf_b1.md) — `fc_mcu_stub.elf` idle `main` @ **`v0.5.16`**  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no silicon/FLASH map (C29), GPIO, Safety execute, craft↔FS, or flash  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — name the **MCU-side UART byte port** the chip will someday use: `UartBytePort`. Today the only implementation is an **in-memory loopback** (`LoopbackUart`). Same idea as C26 `EscOutput`: the plug has a shape; there is still no USART peripheral, no Darwin ioctl, no live RX.  
**Package:** bump Jarvis `pyproject.toml` to **`0.5.26`**; git tag **`v0.5.26`** only after Engineer ACCEPT.  
**Not** chip USART registers · not Darwin `IOSSIOSPEED` / C23 baud · not live ELRS · not C21 Python assembler on the MCU · not GPIO TX/RX pins · not IRQ/DMA · not `Reset_Handler` UART spin · not silicon map (C29) · not Safety execute.

**Outputs (required):**
1. C++ under `native/flight_control/` — preferred `include/jarvis/fc/uart.hpp` + `src/uart.cpp`, added to `jarvis_fc`  
2. Abstract `UartBytePort` + one implementation `LoopbackUart` (in-memory FIFO: `write` queues, `read` dequeues)  
3. Tests: `tests/test_fase_c_mcu_uart_hal_stub_b1.py` + ≥1 Catch2 case  
4. `.jes/artifacts/implementation_report_fase_c_mcu_uart_hal_stub_b1.md`  
5. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **MCU UART stub ≠ chip USART ≠ Darwin baud ≠ live ELRS**  
6. `pyproject.toml` → **`0.5.26`** (+ re-pin `0.5.25` checkpoints)

**Checkpoint:** package **`0.5.26`** · Python suite ≥ **3572** + new tests · host `ctest` still green · MCU `.elf` still links when toolchain present · C22/C23 Python serial **byte-unchanged**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-mcu-uart-hal-stub`** — named MCU-shaped UART **byte** port |
| 2 | One front | Do **not** fold silicon/FLASH map, GPIO pins, IRQ, CMSIS USART, Darwin baud, C21 Python on MCU, Safety execute, or flash |
| 3 | What this Buy demonstrates | El **chip** ya tiene un idioma de “bytes entran / bytes salen” igual que el Mac tenía C22 — pero **sin** registros USART y **sin** `IOSSIOSPEED`. **Human:** “el enchufe UART del MCU tiene forma; el único aparato enchufado es un loopback en memoria.” |
| 4 | Axis | **C++ native** (MCU board-prep). Do **not** add a Python UART driver. Do **not** import `crsf_serial.py` into C++ |
| 5 | Port API | `UartBytePort`: `read(dst, n) -> size_t` (0 if empty), `write(src, n) -> size_t` (how many accepted). Abstract base, virtual destructor |
| 6 | Only implementation | **`LoopbackUart`**: in-memory FIFO. Write then read gets the same bytes, in order. Bounded buffer OK if documented + overflow policy (drop-oldest or refuse extra — **pick one, document, test**) |
| 7 | No baud / no registers | **Forbidden:** USART `BRR`, CMSIS, `IOSSIOSPEED`, `termios`, pin AF mux, IRQ handlers, DMA |
| 8 | Native-tree lock | **Zero** `crsf`/`elrs` under `native/` (even comments), same as C25–C27 |
| 9 | `stub_main.cpp` | **Unchanged idle** after the existing one-shot `jarvis_fc` exercise. **Forbidden:** UART poll loop in `Reset_Handler`/`main` this Buy |
| 10 | C22 / C23 | `crsf_serial.py` **byte-unchanged**. Host Mac serial stays host Mac serial |
| 11 | C21 / C27 | Assembler and hold-watch **unchanged**. This Buy does **not** feed UART bytes into CRSF parse |
| 12 | Safety / radio.py | RejectAll default; `radio.py` no UART APIs |
| 13 | Version | **`0.5.25` → `0.5.26`**; tag **`v0.5.26`** on ACCEPT only |
| 14 | Forbidden claims | “USART live” · “ELRS on the MCU” · “same as Darwin 420000” · “IRQ UART driver” · motors / Safety execute |

**Product sentence:**

```text
Nombrar UartBytePort en el árbol MCU: bytes in/out vía loopback en
memoria — no USART de silicio, no IOSSIOSPEED del Mac, no ELRS.
```

**Defaults locked by Cursor (Engineer: next in board-prep cola after C27 ACCEPT):**
- `uart.hpp` / `LoopbackUart` FIFO  
- Overflow: **refuse extra write** (return short count) — simplest, testable  
- `stub_main` idle  

---

## 1. Package layout (normative intent)

```text
native/flight_control/
  include/jarvis/fc/uart.hpp
  src/uart.cpp                 # add to jarvis_fc
  tests/test_uart.cpp
  mcu/stub_main.cpp            # UNCHANGED idle

tests/
  test_fase_c_mcu_uart_hal_stub_b1.py
```

Do **not** put USART code under `src/jarvis/`. Do **not** name CRSF in these files.

---

## 2. Types / APIs (normative intent)

```text
UartBytePort
  virtual ~UartBytePort()
  virtual size_t read(uint8_t* dst, size_t n) = 0
  virtual size_t write(const uint8_t* src, size_t n) = 0

LoopbackUart(UartBytePort)
  constructor may take max_bytes (default documented, e.g. 256)
  write: enqueue; if full, accept what fits, return that count
  read: dequeue; if empty, return 0
```

### 2.1 Non-goals

No USART registers, CMSIS device pack, Darwin ioctl, baud, GPIO AF, IRQ, DMA, C21 feed, C27 `note_rc`, `step`, EscOutput, Safety, flash.

---

## 3. Integration rules

| Existing | C28 rule |
|---|---|
| C22/C23 Python serial | **Unchanged** |
| C18 `stub_main` | Still idle; no UART |
| C21/C27 | Unchanged; no parse of UART bytes this Buy |
| Native CRSF lock | Holds |
| Host `ctest` | Green + new UART cases |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | `LoopbackUart` is-a `UartBytePort*` |
| T2 | write then read round-trips bytes in order |
| T3 | read on empty returns 0 |
| T4 | write past capacity returns short count (refuse extra); no unbounded growth |
| T5 | `stub_main.cpp` has no `UartBytePort` / `LoopbackUart` / poll loop |
| T6 | `crsf_serial.py` git-unchanged; `radio.py` no UART APIs |
| T7 | Native grep still zero `crsf`/`elrs` |
| T8 | No `IOSSIOSPEED` / `termios` / CMSIS USART in `uart.hpp`/`.cpp` |
| T9 | Catch2 cases for T1–T4 |
| T10 | `pyproject` **`0.5.26`**; re-pin `0.5.25` |
| T11 | Full Python suite + host `ctest` green |
| T12 | Report: MCU UART stub ≠ chip USART ≠ Darwin baud ≠ live ELRS |

---

## 5. Honesty / forbidden

```text
MCU UART stub ≠ chip USART ≠ Darwin baud ≠ live ELRS
```

**Exists:** a named byte port; loopback in memory implements it.  
**Impossible:** a USART that talks to an RX; Mac `IOSSIOSPEED` on the chip; ELRS on the MCU.

---

## 6. Docs

PRIORIDAD · PLATFORM §13 · ARCHITECTURE · README “What v0.5.26 includes”

---

## 7. Acceptance

**PASS when:** T1–T12 · loopback only · `stub_main` idle · C22/C23 frozen · no CRSF in native · version `0.5.26`.  
**FAIL if:** USART registers · Darwin ioctl copied into MCU · `stub_main` UART spin · CRSF tokens in native · live-ELRS claim.

---

## 8. Handoff

```text
Engineer → ★ this IC (C28)
Claude   → UartBytePort + LoopbackUart + tests + report + 0.5.26
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.26
Cursor   → next: C29 silicon + cited FLASH map (B0 unless Engineer upgrades)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C27 CLOSED @ v0.5.25. C28 B1-fase-c-mcu-uart-hal-stub READY —
UartBytePort + in-memory loopback; not chip USART, not Darwin
IOSSIOSPEED, not live ELRS.
```

---

## 10. Engineer ★ checklist

1. Buy = **named MCU byte port** (not USART silicon) OK?  
2. Loopback FIFO · refuse extra on full OK?  
3. `stub_main` stays idle OK?  
4. Zero CRSF in native · C22/C23 frozen OK?  
5. Version **`0.5.26`** OK?  
