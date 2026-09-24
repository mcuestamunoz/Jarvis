# Implementation Contract — Fase C CRSF stream-timeout failsafe (`B1-fase-c-crsf-stream-timeout-failsafe`)

**Project:** Jarvis  
**Date:** 2026-09-24  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (stale sticks ≠ last-good forever · failsafe decision ≠ GPIO cut · ≠ Safety execute · C21 assembler math frozen · C20 kill unchanged · native tree still zero CRSF/ELRS)

**Status:** READY — awaiting Engineer ★  
**Parents:**
- [C26 ★ ACCEPT](implementation_contract_fase_c_esc_output_hal_b1.md) — `EscOutput` @ **`v0.5.24`**  
- [C25 ★ ACCEPT](implementation_contract_fase_c_rc_setpoint_b1.md) — RC → setpoint @ **`v0.5.23`**  
- [C21 ★ ACCEPT](implementation_contract_fase_c_crsf_byte_stream_b1.md) — byte-stream assembler @ **`v0.5.19`**  
- [C20 ★ ACCEPT](implementation_contract_fase_c_crsf_dual_role_bridge_b1.md) — aux → Authority `kill` only @ **`v0.5.18`**  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no MCU UART, silicon map, GPIO, Safety execute, craft↔FS, or flash  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — if a valid RC-channels frame has not been **noted** within a documented timeout, last stick values are **not** treated as live. The caller gets a typed **stale/failsafe decision** (recommended: level + `collective=0`) instead of silently remapping the last AETR tuple. Still no pin, no `step` auto-call, no Safety execute.  
**Package:** bump Jarvis `pyproject.toml` to **`0.5.25`**; git tag **`v0.5.25`** only after Engineer ACCEPT.  
**Not** flying · not “ELRS failsafe product” · not GPIO motor cut · not C20 extra kinds · not MCU UART (C28) · not silicon map (C29) · not wiring `EscOutput.apply_forces` · not changing C21 parse/resync math · not `radio.py` decode APIs.

**Outputs (required):**
1. New Python module under `src/jarvis/capabilities/` — preferred name **`crsf_failsafe.py`**. **Forbidden:** folding this into `radio.py` or rewriting C21 `feed()` hunt/resync  
2. C++ twin that is **protocol-agnostic** (native-tree lock: **zero** `crsf`/`elrs` even in comments): `native/flight_control/include/jarvis/fc/rc_hold.hpp` + `src/rc_hold.cpp`, added to `jarvis_fc`  
3. Tests: `tests/test_fase_c_crsf_stream_timeout_failsafe_b1.py` + ≥1 Catch2 case  
4. `.jes/artifacts/implementation_report_fase_c_crsf_stream_timeout_failsafe_b1.md`  
5. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **timeout failsafe ≠ motors cut ≠ live ELRS ≠ Safety allow**  
6. `pyproject.toml` → **`0.5.25`** (+ re-pin `0.5.24` checkpoints)

**Checkpoint:** package **`0.5.25`** · Python suite ≥ **3553** + new tests · host `ctest` still green · C21 assembler tests still green · C20 policy unchanged

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-crsf-stream-timeout-failsafe`** — stale RC must not keep mixing as if live |
| 2 | One front | Do **not** fold MCU UART, silicon, GPIO, DShot, Safety execute, C20 extra aux/kinds, or auto `submit_command` |
| 3 | What this Buy demonstrates | Si dejan de llegar palos válidos, el sistema **deja de tratar el último AETR como vivo**. **Human:** “si el mando se calla, no seguimos bailando la última canción.” |
| 4 | Clock | Watch takes **`now_s` as an argument** (caller’s time). Does **not** invent `time.time()` as SoT. Tests must be deterministic |
| 5 | Timeout | Named constant default **`0.5` s**. Constructor may override with a finite `timeout_s > 0`. Document: illustrative hold-loss window, not an ELRS product spec |
| 6 | Note vs evaluate | `note_rc(now_s)` when a **valid** RC-channels sample is available (Python: after a decoded `0x16` / `CrsfRcChannels`; C++: after the caller already has a channel vector — no frame parse in C++). `is_stale(now_s)` / `evaluate(now_s)`: **stale if never noted or `now_s - last_s > timeout_s`**. `now_s < last_s` → typed error |
| 7 | Failsafe inputs | When stale, a helper **`failsafe_loop_inputs(t_s) -> RcLoopInputs`** returns C8 `level_setpoint(t_s)` (or equivalent identity quat) + **`collective=0`**. Does **not** call `FlightControlLoop.step`, `EscOutput`, or Safety |
| 8 | Fresh path | When **not** stale, this module does **not** remap sticks — caller still uses C25 `map_rc_to_loop_inputs` on the last noted channels (or equivalent). Watch is age, not a second AETR map |
| 9 | C21 / C20 / C25 / C26 | `crsf_stream.py` `feed()` math **unchanged**. C20 `kill` policy **unchanged**. C25 mapper math **unchanged**. C26 `EscOutput` **unchanged**. Optional glue helper **may** call `note_rc` after a successful `0x16` — must not change C21 default `ingest_stream_bytes` behavior |
| 10 | `radio.py` | No `decode_*` / `open_serial` / failsafe APIs (C5 T5) |
| 11 | Languages | Python (CRSF-named, capabilities/) + C++ (protocol-agnostic `RcHoldWatch` — **no** CRSF/ELRS tokens under `native/`) |
| 12 | Safety / adapter | RejectAll default; `RadioIntentAdapter` still NotImplemented |
| 13 | Version | **`0.5.24` → `0.5.25`**; tag **`v0.5.25`** on ACCEPT only |
| 14 | Forbidden claims | “ELRS failsafe” · “motors cut on timeout” · Safety allow · last sticks stay live after timeout · UART driver |

**Product sentence:**

```text
Si no llega un RC válido en 0.5 s, los palos dejan de ser “vivos”:
decisión stale + consigna nivel + collective 0 — no GPIO, no Safety
execute, no re-parse CRSF.
```

**Defaults locked by Cursor (Engineer: next in board-prep cola after C26 ACCEPT):**
- New **`crsf_failsafe.py`** + C++ **`rc_hold`**  
- 0.5 s · `now_s` caller-supplied · failsafe = level + collective 0  
- C21 `feed()` frozen  

---

## 1. Package layout (normative intent)

```text
src/jarvis/capabilities/
  crsf_failsafe.py     # NEW
  crsf_stream.py       # UNCHANGED feed() math

native/flight_control/
  include/jarvis/fc/rc_hold.hpp
  src/rc_hold.cpp      # add to jarvis_fc
  tests/test_rc_hold.cpp

tests/
  test_fase_c_crsf_stream_timeout_failsafe_b1.py
```

Do **not** put this on `radio.py`. Do **not** import serial/baud.

---

## 2. Types / APIs (normative intent)

```text
CRSF_RC_STALE_S = 0.5          # Python name OK in capabilities/
kRcHoldTimeoutS = 0.5          # C++ — no protocol prefix

RcHoldDecision
  stale: bool
  reason: "fresh" | "never" | "timeout"
  age_s: float | None          # None if never noted

CrsfRcHoldWatch / RcHoldWatch
  __init__(timeout_s=0.5)
  note_rc(now_s) -> None
  is_stale(now_s) -> bool
  evaluate(now_s) -> RcHoldDecision

failsafe_loop_inputs(t_s) -> RcLoopInputs   # level + collective 0
```

C++: same behavior, protocol-agnostic identifiers.

### 2.1 Non-goals

No GPIO, DShot, EscOutput.apply, `step` auto-call, C20 policy change, C21 resync rewrite, live RX, `time.time()` as SoT, Safety execute.

---

## 3. Integration rules

| Existing | C27 rule |
|---|---|
| C21 `feed()` | **Unchanged** |
| C25 mapper | Unchanged; used only when watch says fresh |
| C26 `EscOutput` | Unchanged; this Buy does not apply |
| C20 | Unchanged (kill ≠ hold-timeout) |
| C5 `radio.py` | No failsafe APIs |
| C17 | Untouched |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | Never noted → `evaluate` stale, reason `"never"` |
| T2 | `note_rc(t)` then `evaluate(t)` / `evaluate(t + timeout)` still fresh at equality? **Lock: `age <= timeout` is fresh; `age > timeout` is stale** |
| T3 | `note_rc(0)` then `evaluate(0.5 + 1e-9)` stale, reason `"timeout"` |
| T4 | `failsafe_loop_inputs` → near-identity quat, `collective == 0` |
| T5 | C21 `feed()` source still has no `note_rc` **required** coupling; assembler tests still pass unmodified |
| T6 | `radio.py` still no `decode_crsf` / `open_serial`; C20 policy defaults unchanged |
| T7 | `RadioIntentAdapter` not_implemented; RejectAll default |
| T8 | `loop.py` / `esc.py` apply path unchanged (no timeout wiring into `step`/`apply_forces`) |
| T9 | C++ Catch2: never / fresh / timeout; native grep still zero `crsf`/`elrs` |
| T10 | `pyproject` **`0.5.25`**; re-pin `0.5.24` |
| T11 | Full Python suite + host `ctest` green |
| T12 | Report: timeout failsafe ≠ motors cut ≠ live ELRS ≠ Safety allow |

---

## 5. Honesty / forbidden

```text
timeout failsafe ≠ motors cut ≠ live ELRS ≠ Safety allow
```

**Exists:** an age watch; after 0.5 s without a noted RC sample, sticks are not “live”; recommended inputs are level + zero collective.  
**Impossible:** a radio that cuts ESCs; ExpressLRS failsafe as product; Safety opening on timeout.

---

## 6. Docs

PRIORIDAD · PLATFORM §13 · ARCHITECTURE · README “What v0.5.25 includes”

---

## 7. Acceptance

**PASS when:** T1–T12 · watch only · C21/C20/C25/C26 frozen as locked · no GPIO · version `0.5.25`.  
**FAIL if:** last sticks stay live after timeout · GPIO claimed · Safety execute · `time.time()` SoT · `radio.py` grows decode · native CRSF tokens.

---

## 8. Handoff

```text
Engineer → ★ this IC (C27)
Claude   → watch Python+C++ + tests + report + 0.5.25
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.25
Cursor   → next: C28 MCU UART HAL stub (default on this axis)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C26 CLOSED @ v0.5.24. C27 B1-fase-c-crsf-stream-timeout-failsafe
READY — 0.5 s without a noted RC sample → stale; recommended
level + collective 0; not motors, not Safety execute.
```

---

## 10. Engineer ★ checklist

1. Buy = **stale sticks are not live** (not GPIO cut) OK?  
2. 0.5 s · `now_s` caller-supplied · `age <= timeout` fresh OK?  
3. Python CRSF-named + C++ protocol-agnostic OK?  
4. C21/C20/C25/C26 frozen as locked OK?  
5. Version **`0.5.25`** OK?  
