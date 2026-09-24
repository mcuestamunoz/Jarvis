# Implementation Review — Fase C EscOutput HAL (`B1-fase-c-esc-output-hal`)

**Date:** 2026-09-24  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_fase_c_esc_output_hal_b1.md) · [report](implementation_report_fase_c_esc_output_hal_b1.md)  
**Verdict:** **PASS WITH NOTES** · ★ ACCEPT CLOSED @ **`v0.5.24`**

---

## Summary

C26 names the ESC output port: Python `EscOutput` (`abc.ABC`) in `esc.py`; C++ abstract base with virtual destructor in `esc.hpp`. Both expose `apply_forces(forces) -> EscApplyResult` plus `arm`/`disarm`/`armed`. `SimulatedEscSink` is-a `EscOutput`. C10 `apply(EscPwmCommand)` and arming stay byte-identical; `apply_forces` is encode-then-apply. `esc.cpp` is purely additive (4 lines). Mixer and `loop` remain force-only / no `apply`. One implementation ships.

Honesty line present:

```text
EscOutput HAL ≠ pin ≠ motors ≠ DShot
```

Independent suite **3553 passed, 2 skipped**. Host **ctest 39/39**. Frozen mixer/loop/rc_setpoint/radio/CRSF/safety/autonomy/`stub_main` diffs **empty**. Native tree **zero** `crsf`/`elrs`.

---

## Locks (IC §0)

| # | Lock | Result |
|---|---|---|
| 1–3 | Named port · one front · mixer forces, sink encodes | **Pass** |
| 4 | Mixer force-only | **Pass** (T5 + empty diffs) |
| 5–6 | `apply_forces` · keep C10 `apply` · same arming | **Pass** |
| 7 | Only `SimulatedEscSink` | **Pass** |
| 8 | `step` does not apply | **Pass** (T6 + empty loop diffs) |
| 9–14 | C25/radio frozen · Python+C++ · native lock · RejectAll · `0.5.24` · no fly claims | **Pass** |

---

## Cursor checks (independent)

| Check | Result |
|---|---|
| `EscOutput` ABC / C++ ABC + `SimulatedEscSink` is-a | Present |
| `esc.cpp` | **Additive only** (verified `git diff`) |
| mixer / loop / rc_setpoint | **Empty diffs** |
| `radio.py` / CRSF / safety / autonomy / `stub_main` | **Empty diffs** |
| Native `crsf`/`elrs` | **Zero matches** |
| Related pytest | **89 passed** |
| Full Python suite | **3553 passed, 2 skipped** |
| Host `ctest` | **39/39** (rebuild this review) |
| Tag `v0.5.24` | Engineer ACCEPT (this closeout) |

---

## Notes (not a recut)

| ID | Note |
|---|---|
| N1 | C15 freeze test `test_t6_rung_sources_are_git_unchanged_by_this_buy` now allows additive `esc.cpp` (no `-` lines) instead of blanket zero-diff. IC ★ authorized extending `esc.cpp`. Disclosed; not a weakening of C10 `apply`. **Accept.** |
| N2 | `test_t11_full_suite_process_gate_placeholder` is `assert True`. Gate is the real suite/ctest run. |
| N3 | `fc_esc_pwm_smoke` still calls `apply(EscPwmCommand)` only. IC §3 “may”; disclosed. |
| N4 | README `## Next` still spoke as C26 READY. Closed in this ACCEPT closeout. |

---

## Verdict

**PASS WITH NOTES** · ★ ACCEPT CLOSED @ **`v0.5.24`**.

Next: **C27** CRSF stream-timeout failsafe ([IC](implementation_contract_fase_c_crsf_stream_timeout_failsafe_b1.md)).
