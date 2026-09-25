# Implementation Review — Fase C SPI scripted gyro-shaped probe (`B1-fase-c-spi-scripted-gyro-probe`)

**Date:** 2026-09-25  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_fase_c_spi_scripted_gyro_probe_b1.md) · [report](implementation_report_fase_c_spi_scripted_gyro_probe_b1.md)  
**Verdict:** **PASS WITH NOTES** (N3–N4 folded; N1–N2 residual, accepted) — Engineer ★ ACCEPT CLOSED 2026-09-25 @ **`v0.5.32`**

---

## Summary

C34 adds **`probe_rx`**, the first **client** of `SpiBytePort`, in new files `spi_probe.hpp` / `spi_probe.cpp`. Dummy TX is all zeros; the function returns whatever `port.transfer` moved. On `ScriptedSpi` the fixture byte comes back; on `LoopbackSpi` the echo is zeros. That is the swap-the-port shape. **Not** a gyro driver, **not** WHO_AM_I, **not** a register map, **not** IMU into `step`. `spi.hpp` / `spi.cpp` are byte-unchanged.

Honesty:

```text
scripted gyro probe ≠ gyro live ≠ chip SPI ≠ WHO_AM_I ≠ flying
```

Independent: Python **3679 passed, 2 skipped**. Host **ctest 72/72**. Native `crsf`/`elrs` **zero**. Freeze-list diffs **empty**. Tag **`v0.5.32`** on this ACCEPT. ARM `spi_probe.cpp.obj` rebuilt; `fc_mcu_stub.elf` relinked (xPack).

---

## Locks (IC §0)

| # | Lock | Result |
|---|---|---|
| 1 | Port **client**, not a device driver | **Pass** — free function `probe_rx(SpiBytePort&, …)` |
| 2 | No ICM map · no WHO_AM_I API · no `0x75` · no IMU→`step` | **Pass** — those tokens only in comments (header) or tests (`0x47`) |
| 3 | Client asks the plug; silicon swaps the plug | **Pass** — T2 vs T3 |
| 4 | Dummy TX zeros → `port.transfer` → return count; `n==0` → `0` | **Pass** — stack dummy up to 256 bytes; heap only if `n>256`; `n==0` does not allocate |
| 5 | New files; no methods on `LoopbackSpi` / `ScriptedSpi` | **Pass** — `probe_rx` absent from `spi.hpp` |
| 6 / T8 | Fixture `0x47` tests-only; library must not hardcode expected ID | **Pass** — stricter T8 (no `0x47` even in library comments). See N1 |
| 7 | `LoopbackSpi` unchanged; probe → RX zeros | **Pass** (ctest #67) |
| 8 | Native CRSF lock · no `0x75` in code | **Pass** |
| 9 | Freeze `stub_main` / LED / dshot / uart / `loop.*` / `spi.*` · no probe in `main` | **Pass** — empty `git diff --stat`; `probe_rx` absent from `stub_main` |
| 10 | Package **`0.5.32`** after C33 tag | **Pass** — `pyproject.toml`; parent tag `v0.5.31` exists |
| 11 | Forbidden claims | **Pass** — docs: landed, awaiting ACCEPT, no tag |

---

## Cursor checks (independent)

| Check | Result |
|---|---|
| T1 `SpiBytePort&` | **Pass** (ctest #65) |
| T2 `ScriptedSpi` `{0x47}` → `rx[0]==0x47` | **Pass** (ctest #66) |
| T3 `LoopbackSpi` → RX zeros | **Pass** (ctest #67) |
| T4 short script · tail untouched | **Pass** (ctest #68) |
| T5 `n==0` → `0` | **Pass** (ctest #69) |
| C34 pytest | **12 passed** |
| C32/C33 SPI pytest | **23 passed** (no regression) |
| Full Python suite | **3679 passed, 2 skipped** |
| Host `ctest` | **72/72** |
| `probe_rx` / `SpiBytePort` in `flight_software/` | **Absent** |
| Tag `v0.5.32` | **On ACCEPT** |
| ARM cross-compile | **Pass** — notes-fold: `spi_probe.cpp.obj` + `fc_mcu_stub.elf` (xPack 15.2.1) |

---

## Design call (report §2.1) — confirmed

IC §0.6 allows a library **comment** that names the fixture byte; T8 forbids the literal `0x47` anywhere in `spi_probe.*`. Claude took **T8**. That is the right precedence: T8 is the testable lock; §0.6’s “comment OK” means “do not treat a comment as a WHO_AM_I product API,” not “must mention `0x47`.” Do **not** recut to put `0x47` in the header.

---

## Notes

| ID | Status |
|---|---|
| N1 | **Accepted** — T8 over §0.6 comment-mention of `0x47`. Fixture lives in tests only |
| N2 | **Residual, accept** — `test_t11` is `assert True` (C32/C33 pattern). Gate is the real suite/`ctest`. Do **not** nest pytest-in-pytest |
| N3 | **Folded** — dummy TX on the stack up to 256 bytes; heap only if `n>256`. Catch2 locks `n=257` |
| N4 | **Folded** — ARM image rebuilt this review |

N3 does **not** change the port client contract: still zeros in, whatever the port returns. A 1-byte probe (the gyro-shaped test) no longer allocates.

---

## Verdict

**PASS WITH NOTES** (N3–N4 folded; N1–N2 residual, accepted) — ★ ACCEPT CLOSED @ **`v0.5.32`**.

Do **not** claim gyro live, chip SPI, or WHO_AM_I on the ICM42688P.

Next: **C35** [`B1-fase-c-step-failsafe-hold-ticks`](implementation_contract_fase_c_step_failsafe_hold_ticks_b1.md). Real ESC/FC stay **parked** — [bench note](engineer_note_fase_c_bench_before_silicon_2026_09_24.md).
