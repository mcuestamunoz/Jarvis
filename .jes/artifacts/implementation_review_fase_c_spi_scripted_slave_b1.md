# Implementation Review — Fase C SPI scripted slave (`B1-fase-c-spi-scripted-slave`)

**Date:** 2026-09-25  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_fase_c_spi_scripted_slave_b1.md) · [report](implementation_report_fase_c_spi_scripted_slave_b1.md)  
**Verdict:** **PASS WITH NOTES** (N1–N3 **folded** 2026-09-25 copy+Catch2; N4–N6 residual, accepted) — Engineer ★ ACCEPT CLOSED 2026-09-25 @ **`v0.5.31`**

---

## Summary

C33 adds **`ScriptedSpi`** next to unchanged **`LoopbackSpi`**, both `SpiBytePort`. `transfer` fills RX from a pre-loaded script, never from TX. Short count if the script is shorter than `n`; RX tail untouched. No gyro driver, no WHO_AM_I API, no chip SPI, no `step` wiring.

Honesty:

```text
scripted SPI ≠ gyro live ≠ chip SPI ≠ flying
```

Independent: Python **3667 passed, 2 skipped**. Host **ctest 66/66**. Native `crsf`/`elrs` **zero**. Freeze-list diffs **empty**. Tag **`v0.5.31`** on this ACCEPT.

---

## Locks (IC §0)

| # | Lock | Result |
|---|---|---|
| 1 | Canned-RX `SpiBytePort` in existing `spi.hpp`/`spi.cpp` | **Pass** — no new native file, no CMake change |
| 2 | No ICM42688P map · no WHO_AM_I product API · no IMU→`step` | **Pass** |
| 3 | Loopback echoes; script answers something else | **Pass** — Catch2 TX `{1,2}` + script `{9,8}` → RX `{9,8}` |
| 4 | Constructor and/or `set_next_rx` | **Pass** — both shipped |
| 5 | `LoopbackSpi` behavior-unchanged | **Pass** — `git diff v0.5.30` only appends `ScriptedSpi` (+ `#include <vector>` / `<utility>`) |
| 6 | Refuse-extra / short count | **Pass** — cap is script length (see N5) |
| 7 | Native CRSF lock · WHO_AM_I/ICM42688P comment-only | **Pass** — four hits, all `//` in `spi.hpp` |
| 8 | Freeze `stub_main` / LED / dshot / `uart.hpp` · no SPI in `main` | **Pass** — empty `git diff --stat` |
| 9 | Package **`0.5.31`** | **Pass** — `pyproject.toml` + tag **`v0.5.31`** |
| 10 | Forbidden claims | **Pass** — docs: ACCEPT CLOSED; scripted SPI ≠ gyro live |

---

## Cursor checks (independent)

| Check | Result |
|---|---|
| `ScriptedSpi` is-a `SpiBytePort*` | **Pass** (ctest #59) |
| RX from script, not TX echo | **Pass** (ctest #60) |
| Short script · tail untouched · empty script → 0 | **Pass** (ctest #61, #63) |
| `LoopbackSpi` still RX=TX | **Pass** (ctest #54–58, #64) |
| C33 pytest | **9 passed** |
| Full Python suite | **3667 passed, 2 skipped** |
| Host `ctest` | **66/66** |
| `ScriptedSpi` in `flight_software/` / `core/` / `step` | **Absent** |
| Tag `v0.5.31` | **Not present** — Engineer ACCEPT owns the tag |

---

## Design call (§2.1 of the report) — confirmed

**Fixed canned response until `set_next_rx`**, not a consuming stream. That is the right default for a slave that always answers the same bytes (the shape a later WHO_AM_I-shaped test would want). IC §0.4 left it open; Cursor **accepts** this reading. Do **not** recut to a consuming FIFO unless a later Buy needs a recorded bus trace.

---

## Notes

| ID | Status |
|---|---|
| N1 | **Folded** — file banner names `LoopbackSpi` + `ScriptedSpi` |
| N2 | **Folded** — `SpiBytePort::transfer` is implementation-defined (echo vs canned) |
| N3 | **Folded** — Catch2 now does two identical `transfer`s (`0x11`, `0x11`) then `set_next_rx` (`0x22`); report §2.1 matches |
| N4 | **Residual, accept** — `test_t9` is `assert True` (C32 pattern). Gate is the real suite/`ctest` |
| N5 | **Residual, accept** — `ScriptedSpi` cap = script length, not a separate `max_bytes` |
| N6 | **Residual, accept** — no null-check on `rx` (same as C32). Tests pass valid buffers |

Copy fold does **not** change SPI behavior except the extra identical `transfer` assertion (already the documented rule).

---

## Verdict

**PASS WITH NOTES** (N1–N3 folded; N4–N6 residual) — ★ ACCEPT CLOSED @ **`v0.5.31`**.

Do **not** claim gyro live, chip SPI, or WHO_AM_I on the ICM42688P.

Next: **C34** [`B1-fase-c-spi-scripted-gyro-probe`](implementation_contract_fase_c_spi_scripted_gyro_probe_b1.md). Real ESC/FC (DShot wire, USART, SPI1, C30 DFU, motors) stay **parked** — [bench note](engineer_note_fase_c_bench_before_silicon_2026_09_24.md).
