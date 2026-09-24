# Implementation Review — Fase C DShot encode stub (`B1-fase-c-dshot-encode-stub`)

**Date:** 2026-09-24  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_fase_c_dshot_encode_stub_b1.md) · [report](implementation_report_fase_c_dshot_encode_stub_b1.md)  
**Verdict:** **PASS WITH NOTES** · ★ ACCEPT CLOSED @ **`v0.5.29`**

---

## Summary

C31 adds `encode_dshot_frame(throttle, telemetry=False) -> uint16` in Python (`dshot.py`) and C++ (`dshot.hpp` / `dshot.cpp`). Locked algorithm matches independent arithmetic: `0→0x0000`, `48→0x0606`, `2047→0xFFEE`, telemetry `48→0x0617`. Optional `encode_motor_forces_dshot` maps force `[0,1]` onto throttle **48..2047** (not the 0..47 command range). **PWM `encode_motor_forces` / `EscOutput` / `SimulatedEscSink` unchanged.** C30 LED files frozen. No GPIO/TIM/DMA.

Honesty:

```text
DShot encode ≠ pin ≠ motors ≠ flying
```

Independent suite **3635 passed, 2 skipped**. Host **ctest 55/55** (+4 Catch2). Native `crsf`/`elrs` **zero**. Frozen hello_led / stub_main / esc / mixer **empty diffs**.

---

## Locks (IC §0)

| # | Lock | Result |
|---|---|---|
| 1–4 | Frame in RAM · Python+C++ · not pin | **Pass** |
| 5 | Algorithm + vectors | **Pass** (independent hex + pytest + Catch2) |
| 6 | 0..47 documented, no command table | **Pass** (`test_no_command_table_invented`) |
| 7 | Optional force helper 48..2047 | **Pass** |
| 8 | EscOutput still PWM | **Pass** (T4 + empty esc/mixer diffs) |
| 9 | 150/300/600 names only, not timings | **Pass** (comments) |
| 10 | Native CRSF lock | **Pass** |
| 11 | C30 LED freeze | **Pass** (T5) |
| 12–13 | `0.5.29` · no live-motor / desk-LED claim | **Pass** |

---

## Cursor checks (independent)

| Check | Result |
|---|---|
| Vectors 0 / 48 / 2047 / telem 48 | `0x0` / `0x606` / `0xffee` / `0x617` |
| PWM `protocol == "pwm_us"` · sink still PWM | **Pass** |
| Frozen LED + esc + mixer | **Empty diffs** |
| Native `crsf`/`elrs` | **Zero** |
| C31 pytest | **16 passed** |
| C13 T4 after dshot exclusion | **Pass** (gpio still scanned in dshot files) |
| Full Python suite | **3635 passed, 2 skipped** |
| Host `ctest` | **55/55** |
| Tag `v0.5.29` | Engineer ACCEPT (this closeout) |

---

## Notes (not a recut)

| ID | Note |
|---|---|
| N1 | C++ takes `int throttle` (not IC’s `uint16_t`) so negatives can throw. Same algorithm. **Accept.** |
| N2 | C13 T4 no longer forbids `"dshot"` in the three C31 files. GPIO and other tokens still checked there; `"dshot"` still forbidden in mixer/hello_led/etc. Disclosed, not a weaken. **Accept.** |
| N3 | `test_t10` is `assert True`. Gate is the real suite/ctest. |

---

## Verdict

**PASS WITH NOTES** · ★ ACCEPT CLOSED @ **`v0.5.29`**.

Next software: **C32** [`B1-fase-c-mcu-spi-hal-stub`](implementation_contract_fase_c_mcu_spi_hal_stub_b1.md) READY — SPI byte port in RAM (same idea as C28 UART). Not the ICM42688P. DShot *wire*, USART, C30 DFU remain parked until bench.
