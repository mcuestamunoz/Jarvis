# Implementation Review — Fase C RC → setpoint (`B1-fase-c-rc-setpoint`)

**Date:** 2026-09-22  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_fase_c_rc_setpoint_b1.md) · [report](implementation_report_fase_c_rc_setpoint_b1.md)  
**Verdict:** **PASS WITH NOTES** · ★ ACCEPT CLOSED @ **`v0.5.23`**

---

## Summary

C25 maps already-decoded RC channel units onto C24’s `step` arguments: Python `map_rc_to_loop_inputs` in `rc_setpoint.py`; C++ twin in `rc_setpoint.hpp`/`rc_setpoint.cpp` (in `jarvis_fc`). AETR indices 0/1/2; yaw unused; 172/992/1811; throttle linear to `[0,1]` (mid ≈ 0.5003, documented); roll/pitch ±30° at endpoints, clip beyond; yaw-fixed quat via body 3-2-1. Optional Python `step_with_rc` maps then calls C24 `step`. Plant, GPIO, Safety, C20 kill, and C24 math stay outside.

Honesty line present:

```text
RC→setpoint ≠ flying ≠ sticks drive motors ≠ Safety allow ≠ yaw lock
```

Independent suite **3538 passed, 2 skipped**. Host **ctest 36/36**. Frozen `loop.py`/`loop.hpp`/`loop.cpp` and `crsf_dual_role.py` / `radio.py` diffs **empty**. Native tree **zero** `crsf`/`elrs` matches.

---

## Locks (IC §0)

| # | Lock | Result |
|---|---|---|
| 1–3 | Mapper only · one front · sticks → `step` args | **Pass** |
| 4–5 | Decoded ints · AETR 0/1/2 · yaw unused · 172/992/1811 | **Pass** |
| 6 | Throttle linear, clip; mid not forced to 0.5 | **Pass** (T3) |
| 7 | ±30° · yaw quat = 0 | **Pass** (T2/T4) |
| 8 | `t_s` caller-supplied | **Pass** |
| 9 | Optional `step_with_rc` · no plant/ESC/Safety | **Pass** (Python; see N2) |
| 10–11 | C24/C20 frozen · `radio.py` no stick API | **Pass** |
| 12–15 | Python + C++ · RejectAll · `0.5.23` · no fly claims | **Pass** |

---

## Cursor checks (independent)

| Check | Result |
|---|---|
| `rc_setpoint.py` / `rc_setpoint.hpp`+`.cpp` / CMake | Present |
| `loop.py` / `loop.hpp` / `loop.cpp` | **Empty diffs** |
| `radio.py` / `crsf_dual_role.py` / `intent.py` / `safety.py` / `autonomy/` | **Empty diffs** |
| `stub_main.cpp` `rc_setpoint` / `map_rc` | **Absent** |
| Native `crsf`/`elrs` | **Zero matches** |
| Related pytest | **64 passed** (C25 + C24 + C20 + C11) |
| Full Python suite | **3538 passed, 2 skipped** |
| Host `ctest` | **36/36** (rebuild this review) |
| Tag `v0.5.23` | Engineer ACCEPT (this closeout) |

---

## Notes (not a recut)

| ID | Note |
|---|---|
| N1 | C++ constants are `kRcChMin`/`Mid`/`Max`, not the IC §2 names `CRSF_CH_*`. Values identical. Driven by the C19–C23 native-tree lock (even comments). Disclosed in the report. IC §2 is normative intent. **Accept.** |
| N2 | Optional `step_with_rc` shipped in Python only. C++ mapper-only is within “may”. |
| N3 | `test_t11_full_suite_process_gate_placeholder` is `assert True`. Gate is the real suite/ctest run. |
| N4 | README `## Next` still spoke as C25 READY. Closed in this ACCEPT closeout. |

---

## Verdict

**PASS WITH NOTES** · ★ ACCEPT CLOSED @ **`v0.5.23`**.

Next: **C26** EscOutput HAL ([IC](implementation_contract_fase_c_esc_output_hal_b1.md)).
