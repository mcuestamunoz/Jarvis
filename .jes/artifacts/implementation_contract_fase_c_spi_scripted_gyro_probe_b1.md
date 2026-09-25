# Implementation Contract — Fase C SPI scripted gyro-shaped probe (`B1-fase-c-spi-scripted-gyro-probe`)

**Project:** Jarvis  
**Date:** 2026-09-25  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (probe ≠ gyro live ≠ chip SPI ≠ WHO_AM_I)

**Status:** **READY** — awaiting Engineer ★ (parent: C33 ★ ACCEPT CLOSED @ **`v0.5.31`**)  
**Parents:**
- [C33](implementation_contract_fase_c_spi_scripted_slave_b1.md) — `ScriptedSpi` (canned RX) · PASS WITH NOTES · tag **`v0.5.31`** on ACCEPT  
- [C32 ★ ACCEPT](implementation_contract_fase_c_mcu_spi_hal_stub_b1.md) — `SpiBytePort` + `LoopbackSpi` @ **`v0.5.30`**  
- [situation after C33](engineer_note_fase_c_situation_after_c33_2026_09_25.md) §3.1 — front **1** of the four no-pin attacks  
- [bench before silicon](engineer_note_fase_c_bench_before_silicon_2026_09_24.md)  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**

**Type:** **Implementation Contract** — a **client of `SpiBytePort`**: `probe_rx` asks the port for n bytes and copies whatever RX the **current implementation** returns. Tests load `ScriptedSpi` with a canned payload (fixture `0x47` is a **placeholder byte**, not a register claim). This is how a later SPI1 port can answer the **same call**. **Not** an ICM42688P driver, **not** WHO_AM_I, **not** a register map, **not** IMU into `step`.  
**Package:** bump to **`0.5.32`**; tag **`v0.5.32`** only after Engineer ACCEPT.  
**Not** chip SPI · not CS GPIO · not gyro samples · not DShot wire · not C30 DFU · not denser `step` (cola 2) · not Taller CSS (cola 3) · not standoff points (cola 4).

**Outputs (required):**
1. `probe_rx` in new files `spi_probe.hpp` / `spi_probe.cpp` (do **not** fold into `ScriptedSpi`)  
2. Tests: Catch2 + `tests/test_fase_c_spi_scripted_gyro_probe_b1.py`  
3. Report + docs honesty: **scripted gyro probe ≠ gyro live ≠ chip SPI ≠ WHO_AM_I**  
4. `pyproject.toml` → **`0.5.32`**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-spi-scripted-gyro-probe`** — port **client**, not a device driver |
| 2 | One front | Do **not** fold ICM42688P register map, WHO_AM_I product API, register address `0x75`, IMU→`step`, denser `step` tests, chip SPI, DShot wire, C30 DFU, Taller CSS, standoff points |
| 3 | What this Buy demonstrates | C33 can **mentir** con bytes. Hoy un **cliente** pide esos bytes al enchufe. El día del chip se cambia el enchufe (`ScriptedSpi` → puerto SPI1), no el cliente. **Human:** “preguntamos al puerto y nos contesta; todavía no es el gyro.” |
| 4 | API | `std::size_t probe_rx(SpiBytePort& port, std::uint8_t* rx, std::size_t n)` — dummy TX of **zeros** (full-duplex shape; this Buy does **not** encode a register address), then `port.transfer(tx, rx, n)`, return that count. `n==0` → `0`. Short count = whatever the port already does |
| 5 | Why a new file | `spi.hpp` stays the **port**. `spi_probe.hpp` is the first **caller**. Do **not** add methods on `LoopbackSpi` / `ScriptedSpi` |
| 6 | Fixture byte | Tests **may** load `ScriptedSpi` with `{0x47}` and assert `rx[0]==0x47`. Library code must **not** hardcode `0x47` as an expected ID. Comment OK: placeholder, not a WHO_AM_I claim |
| 7 | `LoopbackSpi` | **Behavior-unchanged**. Probe on loopback + dummy TX zeros → RX zeros (proves the client uses the port, not a hidden script) |
| 8 | Native lock | Zero `crsf`/`elrs`. Do **not** name `WHO_AM_I` / `ICM42688P` in **code** (comment OK: desk identity). Do **not** put `0x75` in code |
| 9 | Freeze | `stub_main`, `hello_led`, `dshot.*`, `uart.*`, `loop.*`, `spi.hpp`/`spi.cpp` **behavior-unchanged** (`spi.hpp` comment-only if a one-line “see spi_probe” is needed; prefer zero edit). No probe in `main` |
| 10 | Version | **`0.5.31` → `0.5.32`**. Do **not** implement until C33 is ACCEPT-tagged `v0.5.31` |
| 11 | Forbidden | “gyro live” · “WHO_AM_I passed” · “ICM42688P driver” · chip SPI · samples into `step` |

**Product sentence:**

```text
probe_rx: un cliente pide n bytes a SpiBytePort —
sigue sin ser el gyro, sigue sin ser el bus del chip.
```

**Defaults locked by Cursor:**
- dummy TX = zeros (not a register address)  
- one function, no expected-ID constant  
- C++ native only (no Python SPI port)

---

## 1. Package layout (normative intent)

```text
native/flight_control/
  include/jarvis/fc/spi_probe.hpp
  src/spi_probe.cpp          ← add to jarvis_fc in CMakeLists.txt
  tests/test_spi_probe.cpp   ← add to fc_unit_tests

tests/
  test_fase_c_spi_scripted_gyro_probe_b1.py
```

Do **not** put the probe under `src/jarvis/`. Do **not** name CRSF in these files.

---

## 2. Types / APIs (normative intent)

```text
probe_rx(SpiBytePort& port, uint8_t* rx, size_t n) -> size_t
  // dummy_tx[0..n) = 0
  // return port.transfer(dummy_tx, rx, n)
```

Null `rx` with `n>0`: same as C32/C33 `transfer` (tests pass valid buffers; no new null-check required).

### 2.1 Non-goals

Chip SPI, CS pin, ICM42688P registers, WHO_AM_I API, IMU into `step`, denser `step` suite, DShot wire, USART, C30 DFU, Taller CSS, standoff points.

---

## 3. Integration rules

| Existing | C34 rule |
|---|---|
| C32 `LoopbackSpi` | Unchanged (echo) |
| C33 `ScriptedSpi` | Unchanged (canned RX, fixed replay until `set_next_rx`) |
| C24 `step` / `loop.*` | **Byte-unchanged** — probe does **not** feed the control tick |
| C3 `SimulatedImuHal` | **Unchanged** |
| C31 DShot / C28 UART / C30 LED | **Byte-unchanged** |
| Native CRSF lock | Holds |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | `probe_rx` takes `SpiBytePort&` (compiles / links against the abstract port) |
| T2 | `ScriptedSpi` script `{0x47}` → `probe_rx` count 1 and `rx[0]==0x47` (fixture byte, not a chip claim) |
| T3 | `LoopbackSpi` + probe → RX zeros (echo of dummy TX) — client is port-shaped, not ScriptedSpi-only |
| T4 | script shorter than n → short count; tail of RX untouched |
| T5 | `n==0` → `0` |
| T6 | `stub_main` / dshot / uart / `loop.*` git-unchanged; no probe poll in `main` |
| T7 | Native zero `crsf`/`elrs`; no SPI1/CMSIS/`0x75`/`WHO_AM_I`/`ICM42688P` in **code** of new files (comments OK) |
| T8 | Library `spi_probe.*` does **not** contain the literal `0x47` (fixture lives in tests) |
| T9 | Catch2 for T1–T5 |
| T10 | `pyproject` **`0.5.32`** |
| T11 | Full suite + `ctest` green |
| T12 | Report: scripted gyro probe ≠ gyro live ≠ chip SPI ≠ WHO_AM_I |

---

## 5. Honesty / forbidden

```text
scripted gyro probe ≠ gyro live ≠ chip SPI ≠ WHO_AM_I ≠ flying
```

**Exists:** a function that asks `SpiBytePort` for bytes; tests can preload those bytes.  
**Impossible:** reading the ICM42688P; a chip SPI bus; IMU samples from this probe.

---

## 6. Docs

PRIORIDAD · PLATFORM §13 · ARCHITECTURE · README “What v0.5.32 includes”

---

## 7. Acceptance

**PASS when:** T1–T12 · probe is a port client · no register map · `step` untouched · version `0.5.32`.  
**FAIL if:** ICM42688P driver · WHO_AM_I as shipped API · `0x75` in code · `step` reads SPI · chip registers · Python SPI port.

---

## 8. Handoff

```text
Engineer → ACCEPT C33 + tag v0.5.31  (if not already)
Engineer → ★ this IC (C34)
Claude   → probe_rx + tests + report + 0.5.32
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.32
Cola     → 2 denser step · 3 Taller CSS · 4 standoff points
```

**STOP** if C33 is not yet tagged: do not bump to `0.5.32` on top of an untagged `0.5.31`.

---

## 9. PRIORIDAD blurb (paste on ★)

```text
Fase C: C33 CLOSED @ v0.5.31. C34 B1-fase-c-spi-scripted-gyro-probe READY —
probe_rx client of SpiBytePort; not gyro live, not WHO_AM_I, not chip SPI.
```

---

## 10. Engineer ★ checklist

1. Buy = **port client** (not ICM42688P driver) OK?  
2. Dummy TX zeros · fixture `0x47` tests-only OK?  
3. `step` / loop frozen OK?  
4. Version **`0.5.32`** after C33 tag OK?  
