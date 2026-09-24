# Implementation Review — Fase C MCU flash + one observable (`B1-fase-c-mcu-flash-observable`)

**Date:** 2026-09-24  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_fase_c_mcu_flash_observable_b1.md) · [report](implementation_report_fase_c_mcu_flash_observable_b1.md)  
**Verdict:** **PASS WITH NOTES** · ★ ACCEPT CLOSED @ **`v0.5.28`**

---

## Summary

C30 closes **both** C29 residuals **in code**:

1. **CMake N1** — `set_property(TARGET fc_mcu_stub.elf APPEND PROPERTY LINK_DEPENDS …/linker_cortex_m4.ld)`. Independent pytest T2: touch `.ld`, rebuild **without** deleting the elf, mtime advances.  
2. **Visible idle** — `mcu/hello_led.c` toggles **PC13** via bare MMIO (`RCC_AHB1ENR` `0x40023830` bit 2, `GPIOC_MODER`/`BSRR`). Citation: HGLRCF405V2 `resource LED 1 C13`. Not PA8 (V2 `MOTOR 6`), not PB1 (`LED_STRIP`). `stub_main` keeps the C18 one-shot then `hello_led_init` + `hello_led_spin()`.

POST_BUILD `.bin` at load **`0x08000000`**. DFU + restore **HGLRCF405V2** documented. Suite green **without** a plugged board.

Honesty line:

```text
flashed LED blink ≠ flying ≠ DShot ≠ USART live ≠ Betaflight HGLRCF405V2
```

**Not flashed on desk** (report §11). Software ACCEPT does not require the LED to have been seen (IC §8).

Independent suite **3619 passed, 2 skipped**. Host **ctest 51/51**. Independent `readelf -l`: LOAD **`0x08000000`**, entry **`0x8000045`**, `hello_led_init`/`hello_led_spin` **T** symbols. Native `crsf`/`elrs` **zero**. Frozen `uart.hpp` / `crsf_serial.py` / startup / syscalls / C16 flags **empty diffs**.

---

## Locks (IC §0)

| # | Lock | Result |
|---|---|---|
| 1–3 | Flash path + one observable + CMake dep; not DShot/USART | **Pass** |
| 4–5 | PC13 from HGLRCF405V2; not PA8/PB1 | **Pass** (source + T3/T5) |
| 6 | RM0090 MMIO + dummy-read after GPIOCEN | **Pass** (`hello_led.c`) |
| 7 | HSI 16 MHz; uncalibrated busy-wait | **Pass** |
| 8 | `stub_main` may change; one-shot kept; idle is LED spin | **Pass** (T6) |
| 9 | `hello_led.c` not under `src/jarvis/` | **Pass** |
| 10 | `LINK_DEPENDS` real, not T9-only | **Pass** (T1–T2) |
| 11–12 | `.bin` + DFU docs; pytest not a live-flash gate | **Pass** (T10/T12/T13) |
| 13–14 | Desk smoke Engineer; overwrite/restore BF | **Pass** (docs; smoke not done) |
| 15–18 | Native CRSF lock · C16 flags · uart/serial freeze · no NVIC | **Pass** |
| 19–20 | `0.5.28` · no flying/DShot/BF claim as fact | **Pass** (with N1 on README wording, closed here) |

---

## Cursor checks (independent)

| Check | Result |
|---|---|
| `LINK_DEPENDS` on `linker_cortex_m4.ld` for `fc_mcu_stub.elf` | Present |
| PC13 / `LED 1 C13` / HGLRCF405V2 in `hello_led.c` | Present |
| MMIO `0x40023830` / `0x40020800` / `0x40020818` | Present |
| `hello_led.c` code (comments stripped) has no GPIOA / `0x40020000` / `motor` | **Pass** |
| Frozen uart / crsf_serial / startup / syscalls | **Empty diffs** |
| Native `crsf`/`elrs` | **Zero matches** |
| C30 pytest | **21 passed**; C29 module still green after T5 retarget (**14** in that file as part of **35** combined) |
| Full Python suite | **3619 passed, 2 skipped** |
| Host `ctest` | **51/51** |
| Independent `readelf -l` | LOAD `0x08000000` · entry `0x8000045` · `hello_led_*` T |
| `.bin` on disk | **84424** bytes |
| Tag `v0.5.28` | Engineer ACCEPT (this closeout) |

---

## Notes (not a recut)

| ID | Note |
|---|---|
| N1 | Living README/PLATFORM used “hello-world **on this silicon**” while report §11 says **not flashed**. IC §8 calls that a docs fail. **Closed in this review** — wording is now DFU-able image / LED **not observed**. |
| N2 | C29 `test_t5_stub_main_git_unchanged` retargeted (CMSIS-in-code, not byte-freeze). IC §0.8 unlocks `stub_main`. Docstring still mentions git-blame then does a source check — messy, not a weaken. **Accept.** |
| N3 | `test_t13` / `test_t15` are `assert True`. Gate is the real suite/ctest. Same pattern as C24/C29. |
| N4 | Engineer 2026-09-24: bench + solder before mount. C30 software ACCEPT ≠ “DFU today.” Desk smoke stays parked ([bench note](engineer_note_fase_c_bench_before_silicon_2026_09_24.md)). |

---

## Verdict

**PASS WITH NOTES** · ★ ACCEPT CLOSED @ **`v0.5.28`**.

Next software: **C31** [`B1-fase-c-dshot-encode-stub`](implementation_contract_fase_c_dshot_encode_stub_b1.md) READY — DShot **frame in RAM**, not pin. C30 DFU smoke remains Engineer/bench.
