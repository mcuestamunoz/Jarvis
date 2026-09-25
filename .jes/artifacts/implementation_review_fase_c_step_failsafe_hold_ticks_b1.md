# Implementation Review — Fase C denser `step` ticks (`B1-fase-c-step-failsafe-hold-ticks`)

**Date:** 2026-09-25  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_fase_c_step_failsafe_hold_ticks_b1.md) · [report](implementation_report_fase_c_step_failsafe_hold_ticks_b1.md)  
**Verdict:** **PASS WITH NOTES** (N1–N2 residual, accepted) — Engineer ★ ACCEPT CLOSED 2026-09-25 @ **`v0.5.33`**

---

## Summary

C35 is **tests only**. It chains two APIs that already existed: C24 `step()` and C27 `failsafe_loop_inputs`. Production freeze-list diffs are empty. Catch2 cases were appended to `test_loop.cpp` (no new file, no CMake change). Python module is 12 tests.

Honesty:

```text
many ticks ≠ flying ≠ 6-DoF ≠ failsafe motors cut ≠ HOLD executed
```

Independent: Python **3691 passed, 2 skipped**. Host **ctest 76/76**. Native `crsf`/`elrs` **zero**. Freeze-list diffs **empty**. Tag **`v0.5.33`** on this ACCEPT.

---

## Locks (IC §0)

| # | Lock | Result |
|---|---|---|
| 1 | Denser **tests** of the existing tick | **Pass** |
| 2 | No plant / 6-DoF / IMU from `probe_rx` / failsafe-inside-`step` / Safety execute | **Pass** |
| 3 | Many canned ticks + stale RC into the same `step` | **Pass** |
| 4 | Glue in tests; freeze `loop.*` / `rc_hold.*` / `crsf_failsafe.py` / `spi_probe.*` | **Pass** — `git diff --stat` empty |
| 5 | N=1000, canned level IMU, collective 0.5, forces finite in `[0,1]`, no plant | **Pass** — Python T1 + Catch2 #33 |
| 6 | Stale watch → `failsafe_loop_inputs` → `step` with collective **0** | **Pass** — never-noted and timeout, Python + Catch2 #34/#35 |
| 7 | Hold = keep passing `level_setpoint`; `submit_command(HOLD)` stays `not_attempted` | **Pass** — Python T3/T6 + Catch2 #36 |
| 8 | `ImuSample` is a caller-filled struct; no `probe_rx` decode | **Pass** — T5 import scan; Catch2 uses `Vec3` literals |
| 9 | Native zero new `crsf`/`elrs` | **Pass** |
| 10 | Package **`0.5.33`** after C34 tag `v0.5.32` | **Pass** — `pyproject.toml`; parent tag exists |
| 11 | Forbidden claims | **Pass** — docs: landed, awaiting ACCEPT, no tag |

---

## Cursor checks (independent)

| Check | Result |
|---|---|
| T1 1000 ticks, no plant, forces in `[0,1]` | **Pass** (pytest + ctest #33) |
| T2 never-noted + timeout → collective 0 into `step` | **Pass** (pytest + ctest #34/#35) |
| T3 `level_setpoint` throughout | **Pass** (pytest + ctest #36) |
| T4 production freeze | **Pass** |
| T5 no `probe_rx` / `SpiBytePort` import as sensor | **Pass** |
| T6 RejectAll; HOLD `not_attempted` | **Pass** |
| T7 native CRSF lock | **Pass** |
| T8 `0.5.33` | **Pass** |
| T9 full suite + `ctest` | **Pass** — **3691** + **76/76** (T9 body is `assert True`; gate is this run) |
| T10 report honesty | **Pass** |
| C24 / C27 parent pytest | **Pass** (bundled with C35 module: 59 passed) |
| C34 `probe_rx` still green | **Pass** (ctest #69–#74) |
| Tag `v0.5.33` | **On ACCEPT** |

---

## Design call — confirmed

IC §1 preferred **extend** `test_loop.cpp`. Claude did that. Glue is `inputs = failsafe_loop_inputs(t)` then `loop.step(sample, inputs.setpoint, inputs.collective)` in test bodies only. `failsafe_loop_inputs` still returns `level_setpoint` + collective 0 (C27, byte-unchanged). C11 plant smoke in `test_loop.cpp` is untouched.

The two self-fixed false positives (substring hitting honesty docstrings) are the same pattern as earlier Buys. Scanning import lines / stripping `__doc__` is the right fix. Do **not** recut to nest pytest-in-pytest for T9.

---

## Notes

| ID | Status |
|---|---|
| N1 | **Residual, accept** — `test_t9` is `assert True` (C32–C34 pattern). Gate is the real suite/`ctest`. Do **not** nest pytest-in-pytest |
| N2 | **Residual, accept** — T2 Python/Catch2 iterate `motor_forces` without an explicit `len == 4`. Vacuous if the vector were empty. T1 already locks four motors on the same frozen `step()`; mixer is unchanged. Not worth recutting |

No production fold. ARM rebuild skipped: this Buy did not touch `jarvis_fc` sources.

---

## Verdict

**PASS WITH NOTES** (N1–N2 residual, accepted) — ★ ACCEPT CLOSED @ **`v0.5.33`**.

Do **not** claim flying, 6-DoF, failsafe motors cut, or HOLD executed.

Next cola: Taller CSS cuboid · standoff points. Real ESC/FC stay **parked** — [bench note](engineer_note_fase_c_bench_before_silicon_2026_09_24.md).
