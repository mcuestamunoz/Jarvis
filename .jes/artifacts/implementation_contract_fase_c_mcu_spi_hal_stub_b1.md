# Implementation Contract — Fase C MCU SPI HAL stub (`B1-fase-c-mcu-spi-hal-stub`)

**Project:** Jarvis  
**Date:** 2026-09-24  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (byte port ≠ chip SPI ≠ gyro)

**Status:** ★ ACCEPT CLOSED @ **`v0.5.30`**  
**Parents:**
- [C31 ★ ACCEPT](implementation_contract_fase_c_dshot_encode_stub_b1.md) — DShot frame in RAM @ **`v0.5.29`**  
- [C28 ★ ACCEPT](implementation_contract_fase_c_mcu_uart_hal_stub_b1.md) — `UartBytePort` + `LoopbackUart` @ **`v0.5.26`**  
- [C3] `SimulatedImuHal` — Python fake samples; **not** this Buy  
- Desk FC gyro (when later wired): **ICM42688P** on SPI — **name only**; no register driver this Buy  
- [bench before silicon](engineer_note_fase_c_bench_before_silicon_2026_09_24.md)  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**

**Type:** **Implementation Contract** — name the **MCU-side SPI byte port** the gyro will someday use: `SpiBytePort`. Today the only implementation is an **in-memory loopback** (`LoopbackSpi`). Same idea as C28 UART: the plug has a shape; there is still no SPI peripheral, no CS pin, no ICM42688P.  
**Package:** bump Jarvis `pyproject.toml` to **`0.5.30`**; git tag **`v0.5.30`** only after Engineer ACCEPT.  
**Not** STM32 SPI registers · not GPIO CS · not ICM42688P WHO_AM_I · not IMU into `step` · not DShot wire · not C30 DFU.

**Outputs (required):**
1. C++ `include/jarvis/fc/spi.hpp` + `src/spi.cpp` added to `jarvis_fc`  
2. Abstract `SpiBytePort` + `LoopbackSpi` (full-duplex transfer: TX bytes come back as RX, in order)  
3. Tests: `tests/test_fase_c_mcu_spi_hal_stub_b1.py` + ≥1 Catch2 case  
4. `.jes/artifacts/implementation_report_fase_c_mcu_spi_hal_stub_b1.md`  
5. Docs honesty: **MCU SPI stub ≠ chip SPI ≠ gyro live ≠ flying**  
6. `pyproject.toml` → **`0.5.30`** (+ re-pin `0.5.29`)

**Checkpoint:** package **`0.5.30`** · suite ≥ **3635** + new tests · host `ctest` green · C31 `dshot.*` and C30 `hello_led` / `stub_main` **byte-unchanged**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-mcu-spi-hal-stub`** — named MCU-shaped SPI **byte** port |
| 2 | One front | Do **not** fold ICM42688P driver, SPI registers, CS GPIO, DShot wire, USART, C30 DFU, Safety execute, or craft↔FS |
| 3 | What this Buy demonstrates | El gyro de la F405 habla SPI; hoy el chip tiene un idioma de “bytes van / bytes vuelven” **sin** el bus real. **Human:** “el enchufe SPI tiene forma; el único aparato es un loopback en memoria.” |
| 4 | Axis | **C++ native** (like C28). Do **not** add a Python SPI driver. Do **not** change `SimulatedImuHal` |
| 5 | Port API | `SpiBytePort`: `transfer(tx, rx, n) -> size_t` — copies up to `n` TX bytes, fills RX with what the device would return. Never blocks. Abstract base, virtual destructor |
| 6 | Only implementation | **`LoopbackSpi`**: RX = TX, in order. Bounded buffer OK (default 256). Overflow: **refuse extra** (return short count), same as `LoopbackUart` |
| 7 | No registers / no CS | **Forbidden:** `SPI1`, `CR1`/`DR`, CMSIS, pin AF, NSS/CS GPIO, IRQ, DMA |
| 8 | Native-tree lock | **Zero** `crsf`/`elrs` under `native/` (even comments). Gyro part name **ICM42688P** may appear in a **comment** as desk identity, not as a driver |
| 9 | Freeze | `dshot.hpp`/`.cpp`/`dshot.py`, `hello_led.*`, `stub_main.cpp`, `uart.hpp` **byte-unchanged**. **Forbidden:** SPI poll in `main` |
| 10 | Version | **`0.5.29` → `0.5.30`**; tag **`v0.5.30`** on ACCEPT only |
| 11 | Forbidden claims | “SPI live” · “gyro samples” · “WHO_AM_I” as a real read · motors / DShot wire |

**Product sentence:**

```text
Nombrar SpiBytePort en el árbol MCU: bytes de ida y vuelta vía
loopback en memoria — no SPI de silicio, no ICM42688P.
```

**Defaults locked by Cursor:**
- `transfer` full-duplex loopback  
- Overflow: refuse extra  
- `stub_main` idle stays PC13 LED, no SPI  

---

## 1. Package layout (normative intent)

```text
native/flight_control/
  include/jarvis/fc/spi.hpp
  src/spi.cpp
  tests/test_spi.cpp

tests/
  test_fase_c_mcu_spi_hal_stub_b1.py
```

Do **not** put SPI under `src/jarvis/`. Do **not** name CRSF in these files.

---

## 2. Types / APIs (normative intent)

```text
SpiBytePort
  virtual ~SpiBytePort()
  virtual size_t transfer(const uint8_t* tx, uint8_t* rx, size_t n) = 0
  // returns how many bytes moved; 0 if n==0; short if capacity exhausted

LoopbackSpi(SpiBytePort)
  constructor may take max_bytes (default 256)
  transfer: for i in 0..accepted-1: rx[i] = tx[i]
```

### 2.1 Non-goals

Chip SPI, CS pin, ICM42688P registers, IMU into `step`, DShot wire, USART, C30 DFU.

---

## 3. Integration rules

| Existing | C32 rule |
|---|---|
| C28 UART | Unchanged; SPI is a **separate** port |
| C31 DShot encode | **Byte-unchanged** |
| C30 hello_led / stub_main | **Byte-unchanged** |
| C3 `SimulatedImuHal` | **Unchanged** |
| Native CRSF lock | Holds |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | `LoopbackSpi` is-a `SpiBytePort*` |
| T2 | transfer round-trips TX→RX in order |
| T3 | n=0 returns 0 |
| T4 | transfer past capacity returns short count; no unbounded growth |
| T5 | `stub_main.cpp` has no `SpiBytePort` / poll loop |
| T6 | `dshot.hpp` / `uart.hpp` git-unchanged |
| T7 | Native grep still zero `crsf`/`elrs` |
| T8 | No `SPI1`/`CR1`/CMSIS/`GPIO` CS in `spi.hpp`/`.cpp` **code** (comments may name the future gyro) |
| T9 | Catch2 cases for T1–T4 |
| T10 | `pyproject` **`0.5.30`**; re-pin `0.5.29` |
| T11 | Full Python suite + host `ctest` green |
| T12 | Report: MCU SPI stub ≠ chip SPI ≠ gyro live |

---

## 5. Honesty / forbidden

```text
MCU SPI stub ≠ chip SPI ≠ gyro live ≠ flying
```

**Exists:** a named SPI byte port; loopback in memory implements it.  
**Impossible:** reading the ICM42688P; a chip SPI bus; DShot on a pin.

---

## 6. Docs

PRIORIDAD · PLATFORM §13 · ARCHITECTURE · README “What v0.5.30 includes”

---

## 7. Acceptance

**PASS when:** T1–T12 · loopback only · C31/C30 frozen · no CRSF in native · version `0.5.30`.  
**FAIL if:** SPI registers · gyro driver · `stub_main` SPI spin · live-IMU claim.

---

## 8. Handoff

```text
Engineer → ★ this IC (C32)
Claude   → SpiBytePort + LoopbackSpi + tests + report + 0.5.30
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.30
Cursor   → next parked: DShot wire · USART · C30 DFU · gyro driver · craft↔FS
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C31 CLOSED @ v0.5.29. C32 B1-fase-c-mcu-spi-hal-stub READY —
SpiBytePort + in-memory loopback; not chip SPI, not ICM42688P.
```

---

## 10. Engineer ★ checklist

1. Buy = **named SPI byte port** (not gyro driver) OK?  
2. Loopback transfer · refuse extra OK?  
3. DShot + LED files frozen OK?  
4. Version **`0.5.30`** OK?  
