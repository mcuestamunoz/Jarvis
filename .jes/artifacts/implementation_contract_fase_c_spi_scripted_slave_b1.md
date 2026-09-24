# Implementation Contract — Fase C SPI scripted slave (`B1-fase-c-spi-scripted-slave`)

**Project:** Jarvis  
**Date:** 2026-09-24  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (canned RX ≠ gyro ≠ chip SPI)

**Status:** READY — awaiting Engineer ★  
**Parents:**
- [C32 ★ ACCEPT](implementation_contract_fase_c_mcu_spi_hal_stub_b1.md) — `SpiBytePort` + `LoopbackSpi` @ **`v0.5.30`**  
- [bench before silicon](engineer_note_fase_c_bench_before_silicon_2026_09_24.md)  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**

**Type:** **Implementation Contract** — second `SpiBytePort` implementation: **`ScriptedSpi`**. The caller supplies the RX bytes **in advance**. `transfer` copies those canned bytes into `rx` (not TX echo). This is how a test pretends “a device answered” without a chip. **Not** an ICM42688P driver, **not** WHO_AM_I as a product API, **not** IMU into `step`.  
**Package:** bump to **`0.5.31`**; tag **`v0.5.31`** only after Engineer ACCEPT.  
**Not** chip SPI · not CS GPIO · not gyro samples · not DShot wire · not C30 DFU.

**Outputs (required):**
1. `ScriptedSpi` in `spi.hpp` / `spi.cpp` (add to existing files; keep `LoopbackSpi`)  
2. Tests: extend Catch2 + `tests/test_fase_c_spi_scripted_slave_b1.py`  
3. Report + docs honesty: **scripted SPI ≠ gyro live ≠ chip SPI**  
4. `pyproject.toml` → **`0.5.31`**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-spi-scripted-slave`** — canned-RX `SpiBytePort` |
| 2 | One front | Do **not** fold ICM42688P register map, WHO_AM_I product API, IMU→`step`, chip SPI, DShot wire, C30 DFU |
| 3 | What this Buy demonstrates | El loopback solo **repite** lo que envías. Un sensor de verdad **contesta otra cosa**. Hoy podemos programar esa contestación en RAM. **Human:** “podemos hacer que el enchufe SPI mienta con bytes que nosotros escribimos.” |
| 4 | API | `ScriptedSpi(span of uint8_t canned_rx)` or `set_next_rx(...)`. `transfer`: fill `rx[0..accepted)` from the script (not from `tx`). If the script is shorter than `n`, return short count. Do **not** require TX to match anything this Buy |
| 5 | `LoopbackSpi` | **Behavior-unchanged** (still RX=TX). Both remain `SpiBytePort` |
| 6 | Overflow | Same refuse-extra / short count as C32 |
| 7 | Native lock | Zero `crsf`/`elrs`. Do **not** name WHO_AM_I / ICM42688P in **code** (comment OK: “a future gyro test could load 0x47 here”) |
| 8 | Freeze | `stub_main`, `hello_led`, `dshot.*`, `uart.hpp` **byte-unchanged**. No SPI in `main` |
| 9 | Version | **`0.5.30` → `0.5.31`** |
| 10 | Forbidden | “gyro live” · “WHO_AM_I passed on the chip” · chip SPI |

**Product sentence:**

```text
ScriptedSpi: el puerto SPI puede devolver bytes pregrabados —
sigue sin ser el gyro, sigue sin ser el bus del chip.
```

---

## 1–4. Layout / tests (minimum)

Keep code in `spi.hpp`/`spi.cpp`/`test_spi.cpp`. New pytest module `tests/test_fase_c_spi_scripted_slave_b1.py`.

| ID | Check |
|---|---|
| T1 | `ScriptedSpi` is-a `SpiBytePort*` |
| T2 | transfer fills RX from script, **not** TX echo (TX `{1,2}` + script `{9,8}` → RX `{9,8}`) |
| T3 | script shorter than n → short count; tail of RX untouched |
| T4 | `LoopbackSpi` still RX=TX (regression) |
| T5 | `stub_main` / dshot / uart git-unchanged |
| T6 | Native zero `crsf`/`elrs`; no SPI1/CMSIS in new code |
| T7 | Catch2 for T1–T4 |
| T8 | `pyproject` **`0.5.31`** |
| T9 | Full suite + `ctest` green |
| T10 | Report: scripted SPI ≠ gyro live ≠ chip SPI |

---

## 5. Honesty

```text
scripted SPI ≠ gyro live ≠ chip SPI ≠ flying
```

---

## 7. Acceptance

**PASS when:** T1–T10 · LoopbackSpi unchanged · no gyro driver.  
**FAIL if:** ICM42688P register map · WHO_AM_I as shipped API · `step` reads SPI · chip registers.

---

## 8. Handoff

```text
Engineer → ★ C33
Claude   → ScriptedSpi + tests + report + 0.5.31
Cursor   → review
Engineer → ACCEPT + tag v0.5.31
```

---

## 10. Engineer ★ checklist

1. Buy = **canned RX on SpiBytePort** (not gyro driver) OK?  
2. LoopbackSpi still echo OK?  
3. Version **`0.5.31`** OK?  
