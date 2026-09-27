# Implementation Contract — Fase C ICM register client (`B1-fase-c-icm-register-client`)

**Project:** Jarvis  
**Date:** 2026-09-27  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — ★ AUTHORIZED: **implement now**  
**Reviewer:** Cursor against this IC · Engineer spot-check (datasheet client ≠ chip SPI1 ≠ gyro live ≠ IMU into `step`)

**Status:** ★ **ACCEPT CLOSED** @ tag **`v0.5.43`** (Engineer 2026-09-27) · Cursor review PASS WITH NOTES (N1 citation = PX4+search, not PDF page)  
**Parents:**
- [C41 ★ ACCEPT](implementation_contract_fase_c_safety_sim_policy_b1.md) — Safety allow-list HOLD/LAND/GO_TO @ **`v0.5.42`**  
- [C34 ★ ACCEPT](implementation_contract_fase_c_spi_scripted_gyro_probe_b1.md) — `probe_rx` client of `SpiBytePort`; fixture `0x47` was **placeholder**, not WHO_AM_I claim @ **`v0.5.32`**  
- [C33 ★ ACCEPT](implementation_contract_fase_c_spi_scripted_slave_b1.md) — `ScriptedSpi` canned RX @ **`v0.5.31`**  
- [C32 ★ ACCEPT](implementation_contract_fase_c_mcu_spi_hal_stub_b1.md) — `SpiBytePort` @ **`v0.5.30`**  
- [Month note](engineer_note_software_month_until_bench_2026_09_26.md) — C42 after C41  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — a **datasheet-cited ICM42688P register client** that talks to `SpiBytePort` (tests use `ScriptedSpi`) to read **WHO_AM_I** (and optionally one more cited register). Still **not** the chip on SPI1, still **not** live gyro samples into `step`.  
**Package:** bump **`0.5.42` → `0.5.43`**; git tag **`v0.5.43`** only after Engineer ACCEPT.

**Not** chip SPI1 · not CS GPIO · not full IMU driver · not samples into `FlightControlLoop.step` · not DShot wire · not C30 DFU · not craft↔FS (C43) · not Assistant · not claiming gyro live.

**Outputs (required):**
1. Python and/or C++ client (prefer **both** if natural; C++ under `native/flight_control/` next to `spi_probe`) that encodes a **cited** WHO_AM_I read transaction against `SpiBytePort`  
2. Datasheet citation in comments/report: part **ICM-42688-P** (or exact desk part string), register address, expected ID value — **cite source** (TDK datasheet section/table)  
3. Tests: `ScriptedSpi` scripted to return the cited WHO_AM_I byte → client reports match; wrong byte → documented fail/mismatch; `LoopbackSpi` path does not falsely claim WHO_AM_I success  
4. Tests: `tests/test_fase_c_icm_register_client_b1.py` + Catch2 if C++  
5. Report + docs honesty: **ICM client on ScriptedSpi ≠ chip SPI1 ≠ gyro live ≠ IMU in step**  
6. `pyproject.toml` → **`0.5.43`** (+ re-pin `0.5.42` checkpoints)

**Checkpoint:** package **`0.5.43`** · suite green · host `ctest` green · C34 `probe_rx` still green · C32/C33 ports untouched in role

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-icm-register-client`** — datasheet WHO_AM_I client on `SpiBytePort` |
| 2 | One front | Do **not** fold live SPI1, CS pin, FIFO/stream samples, IMU→`step`, craft↔FS, Assistant, silicon wire, Safety changes |
| 3 | What this Buy demonstrates | The placeholder probe becomes a **named device transaction**: we ask for WHO_AM_I the way the datasheet says, against the same port abstraction. Swap `ScriptedSpi`→SPI1 later without rewriting callers. **Human:** “ya preguntamos al IMU por su ID de verdad (en papel); el bus sigue siendo mentira de laboratorio.” |
| 4 | Part / citation | Desk identity **ICM42688P** (match prior notes). Cite WHO_AM_I register address and expected response from TDK datasheet in report + code comment. Prefer constant names like `ICM42688P_REG_WHO_AM_I` / `ICM42688P_WHO_AM_I_VALUE` — **not** magic bare `0x47` without citation. Note: C34’s fixture `0x47` may equal the real ID — if so, document that coincidence; library must still cite, not inherit “placeholder” language |
| 5 | Transaction shape | Full-duplex SPI read as datasheet requires (typically write reg\|read-bit then read data). Document bit order / dummy bytes. Reuse `SpiBytePort::transfer` — do **not** bypass the port |
| 6 | API | Prefer something like `read_who_am_i(SpiBytePort&) -> uint8_t` or `WhoAmIResult` with explicit match/mismatch helpers — pick one, document. May live beside or replace thin use of `probe_rx` for this path; **do not** delete `probe_rx` |
| 7 | Optional second register | One extra cited read (e.g. device config or bank) is OK if tiny; **not** a full register map dump |
| 8 | Languages | **Prefer both** Python + C++. If Python-only would orphan the native SPI ladder, prefer C++ primary + Python smoke wrapper |
| 9 | Freeze | `LoopbackSpi` / `ScriptedSpi` / `SpiBytePort` behavior-unchanged except additive helpers if unavoidable. `loop` / plant / C40/C41 untouched |
| 10 | Version | **`0.5.42` → `0.5.43`**; tag on ACCEPT only |
| 11 | Forbidden claims | “gyro live” · “SPI1 works” · “WHO_AM_I on copper” · “IMU fused into step” · “we fly” |

**Product sentence:**

```text
Un cliente ICM42688P lee WHO_AM_I por SpiBytePort contra ScriptedSpi —
citado del datasheet, todavía sin el chip en el banco.
```

**Defaults locked by Cursor:**
- Cited WHO_AM_I read via `SpiBytePort` + `ScriptedSpi` in tests  
- Constants + datasheet cite (not anonymous `0x47`)  
- Keep `probe_rx`; add named ICM client  
- Package **`0.5.43`**

---

## 1. Package layout (normative intent)

```text
native/flight_control/
  include/jarvis/fc/icm42688p.hpp   # NEW (name flexible)
  src/icm42688p.cpp
  tests/test_icm42688p.cpp

src/jarvis/flight_software/...     # Python twin or thin wrapper if shipped

tests/test_fase_c_icm_register_client_b1.py
```

Do **not** import Continuity. Do **not** put under `capabilities/`.

---

## 2. Tests (minimum)

| ID | Check |
|---|---|
| T1 | `ScriptedSpi` returns cited WHO_AM_I → client reads matching value |
| T2 | Wrong canned byte → mismatch / documented error (not silent success) |
| T3 | Uses `SpiBytePort::transfer` (or equivalent) — not a hidden bypass |
| T4 | `probe_rx` / C34 tests still green; ports behavior-frozen |
| T5 | No craft/`library`/Board edits; no IMU into `step` |
| T6 | Catch2 T1+T2 equivalents if C++ |
| T7 | `pyproject` **`0.5.43`**; suite + `ctest` green |
| T8 | Report: **ICM on ScriptedSpi ≠ chip SPI1 ≠ gyro live** |

---

## 3. Honesty / forbidden

```text
ICM register client on ScriptedSpi ≠ chip SPI1
WHO_AM_I in RAM ≠ gyro live ≠ samples in step
datasheet cite ≠ lab measurement on copper
```

---

## 4. Acceptance

**PASS when:** T1–T8 · cited WHO_AM_I client · ScriptedSpi tests green · version `0.5.43`.  
**FAIL if:** live SPI1 · IMU into `step` · craft wiring · “gyro live” · uncited magic ID.

---

## 5. Handoff

```text
Engineer → ★ AUTHORIZED (this IC — Claude implements now)
Claude   → ICM WHO_AM_I client on SpiBytePort + tests + report + 0.5.43
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.43
Cola     → C43 craft↔FS bind
```

---

## 6. PRIORIDAD blurb (paste on landing)

```text
Fase C: ★ C42 ICM register client — WHO_AM_I on ScriptedSpi.
Package 0.5.43. ≠ chip SPI1 ≠ gyro live.
Cola after ACCEPT: C43 craft↔FS. Assistant PARKED. Silicon parked.
```

---

## 7. Engineer ★ checklist

- [x] ★ this IC (authorize Claude) — 2026-09-27 (IC passed to Claude = execute)  
- [x] After landing: Cursor review · then ACCEPT + tag `v0.5.43` — 2026-09-27  
- [x] Next = **C43**, not Assistant — C43 IC AUTHORIZED  
