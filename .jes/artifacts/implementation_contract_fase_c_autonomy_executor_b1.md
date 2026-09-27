# Implementation Contract — Fase C autonomy executor (`B1-fase-c-autonomy-executor`)

**Project:** Jarvis  
**Date:** 2026-09-26  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — ★ AUTHORIZED: **implement now**  
**Reviewer:** Cursor against this IC · Engineer spot-check (verb→setpoints in sim ≠ execute on copper · Safety RejectAll intact · plant outside `step`)

**Status:** ★ **ACCEPT CLOSED** @ tag **`v0.5.41`** (Engineer 2026-09-27) · Cursor review PASS WITH NOTES  
**Parents:**
- [C39 ★ ACCEPT](implementation_contract_fase_c_position_loop_b1.md) — sim position + xy→tilt @ **`v0.5.40`**  
- [C38 ★ ACCEPT](implementation_contract_fase_c_altitude_loop_b1.md) — sim altitude + z→collective @ **`v0.5.39`**  
- [C4 ★ ACCEPT](implementation_contract_fase_c_autonomy_surface_b1.md) — `propose_command` / `submit_command` · RejectAll · never `"executed"`  
- [Month note](engineer_note_software_month_until_bench_2026_09_26.md) — C40 after C39 · residuals: **no cola** from C39 N1–N4; **N2 coupling** is operating knowledge  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — a **sim autonomy executor** that maps **HOLD / LAND / GO_TO** into the existing C38/C39 setpoint chain so verbs actually drive `ToyQuad6DofPlant` via `loop.step` — still **not** Safety allow on copper, still **not** `"executed"`.  
**Package:** bump **`0.5.40` → `0.5.41`**; git tag **`v0.5.41`** only after Engineer ACCEPT.

**Not** Safety allowlist (C41) · not craft↔FS · not Assistant · not live sensors · not folding plant into `step` · not claiming HOLD/LAND/GO_TO in air · not `"executed"` on `AutonomySubmissionResult` · not TAKEOFF/FOLLOW/PATROL/RETURN_HOME this Buy (may reject/unsupported).

**Outputs (required):**
1. Python: sim executor (name flexible: `SimAutonomyExecutor` / `AutonomySimRunner` — pick one, document) that, given a verb + documented params + plant/HAL/controller handles, produces per-tick **setpoint + collective** and advances `loop.step` → `plant.step`  
2. C++ twin under `native/flight_control/` **or** Python-only if C++ twin would be empty theater — **prefer both**; if C++ deferred, document why and still ship Catch2 smoke of the Python-equivalent chain via existing controllers (reviewer will judge)  
3. Verb map (locked below) for **HOLD**, **LAND**, **GO_TO** only  
4. Thin smokes: HOLD holds near a pose; GO_TO shrinks horizontal distance; LAND reduces z toward a documented floor  
5. Tests: `tests/test_fase_c_autonomy_executor_b1.py` (+ Catch2 if C++ twin)  
6. Report + docs honesty: **verb→setpoints in RAM ≠ execute on copper ≠ Safety allow ≠ flying**  
7. `pyproject.toml` → **`0.5.41`** (+ re-pin `0.5.40` checkpoints)

**Checkpoint:** package **`0.5.41`** · suite green · host `ctest` green · C36–C39 + C4 RejectAll still green

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-autonomy-executor`** — HOLD/LAND/GO_TO → sim setpoints |
| 2 | One front | Do **not** fold C41 Safety allowlist, ICM, craft↔FS, Assistant, silicon, rewrite C38/C39 laws, house map |
| 3 | What this Buy demonstrates | Autonomy verbs stop being “labels that RejectAll.” In **sim only**, HOLD/LAND/GO_TO become documented setpoint sequences that move the toy plant. **Human:** “el verbo ya manda consignas a la planta de juguete; sigue sin ser execute en cobre.” |
| 4 | Relationship to C4 `submit_command` | **Do not** change `AutonomySubmissionResult.execution` to `"executed"`. Prefer a **separate** sim driver API (e.g. `run_sim_command(...)` / `SimAutonomyExecutor.tick(...)`) that reuses `AutonomyVerb` + params. `submit_command` + default RejectAll must stay reject / `not_attempted`. C41 will open Safety allow for sim — not this Buy |
| 5 | Verb → setpoints (normative) | **HOLD:** freeze `PositionSetpoint` at current (or documented) xy + `z_des` at current (or documented) z — then run C39+C38 chain. **GO_TO:** `PositionSetpoint` from params (`x_m`,`y_m` required; `z_m` optional default documented) + C38 altitude to that z. **LAND:** `PositionSetpoint` hold xy + `z_des` descending toward a documented floor (prefer `0.0` or small `z_land_m`) at a documented rate or step schedule — **not** a claim of touchdown gear. Unsupported verbs: raise or return typed unsupported — document |
| 6 | Integration | Executor runs **outside** `FlightControlLoop.step` — same caller pattern as C39 smoke: sense → HALs → pos.compute → alt.compute → `loop.step` → `plant.step`. Reuse C38/C39 controllers; **do not** reimplement PD laws |
| 7 | Coupling (C39 N2 — operating knowledge, not debt) | While tilting for GO_TO, z may droop vs `z_des`. Tests must **not** require z glued to setpoint during aggressive xy chase. HOLD may assert both horizontal and vertical stay within documented bounds after settling. LAND asserts z **decreases** toward floor |
| 8 | Params | Document param keys (e.g. `x_m`,`y_m`,`z_m` as strings in `AutonomyCommand.params` **or** a typed sim request). Prefer typed sim request if cleaner; if reusing `AutonomyCommand.params`, parse finite floats and reject invalid |
| 9 | Languages | **Prefer** Python + C++. If C++ is a thin twin of the tick driver only, OK |
| 10 | Plants / controllers / C4 surface | Plant dynamics untouched. C38/C39 modules behavior-frozen except optional `isfinite` hygiene on position setpoint (**opportunistic**, not required). C4 `submit_command` path unchanged |
| 11 | Safety / craft | Untouched — RejectAll remains default |
| 12 | Version | **`0.5.40` → `0.5.41`**; tag on ACCEPT only |
| 13 | Forbidden claims | “executed” · “Safety allow” · “we fly” · “LAND on copper” · “GO_TO in air” · house map |

**Product sentence:**

```text
HOLD, LAND y GO_TO ya mandan consignas a la planta 6-DoF en sim —
sin Safety allow, sin execute en cobre y sin volar.
```

**Defaults locked by Cursor:**
- Separate sim executor API (not `"executed"` on C4 submit)  
- HOLD / LAND / GO_TO only; reuse C38+C39 outside `step`  
- Respect z↔tilt coupling (C39 N2) in acceptance bounds  
- Python (+ C++ preferred) · package **`0.5.41`**

---

## 1. Package layout (normative intent)

```text
src/jarvis/flight_software/autonomy/
  sim_executor.py          # NEW — preferred home (next to C4 surface, not inside loop/)
  # OR flight_control/sim_autonomy_executor.py — pick one tree, document

native/flight_control/
  include/jarvis/fc/sim_autonomy_executor.hpp …   # if C++ twin
  tests/test_sim_autonomy_executor.cpp

tests/test_fase_c_autonomy_executor_b1.py
```

Do **not** import Continuity. Do **not** put under `capabilities/` policy (C41).

---

## 2. Tests (minimum)

| ID | Check |
|---|---|
| T1 | GO_TO to documented East point → horizontal distance shrinks (reuse plant) |
| T2 | HOLD after a displace (or from offset) → position stays within documented bound over N ticks |
| T3 | LAND → `true_position_m[2]` decreases toward documented floor (finite; may not require exact 0) |
| T4 | Unsupported verb / bad params raise or typed reject |
| T5 | `submit_command(..., RejectAll)` still reject / `not_attempted`; no `"executed"` anywhere in new code paths |
| T6 | `loop.step` never calls plant; C36–C39 smokes still green |
| T7 | No craft/`library`/Board edits |
| T8 | `pyproject` **`0.5.41`**; suite + `ctest` green |
| T9 | Report honesty locks |

---

## 3. Honesty / forbidden

```text
verb → setpoints in RAM ≠ execute on copper
sim HOLD/LAND/GO_TO ≠ flying ≠ Safety allow
plant outside step ≠ MCU ISR ≠ motors
z may droop under tilt (C39 N2) ≠ altitude bug
```

---

## 4. Acceptance

**PASS when:** T1–T9 · three verbs drive plant in sim · C4 RejectAll intact · version `0.5.41`.  
**FAIL if:** `"executed"` · Safety allowlist · plant inside `step` · craft wiring · “we fly.”

---

## 5. Handoff

```text
Engineer → ★ AUTHORIZED (this IC — Claude implements now)
Claude   → sim executor HOLD/LAND/GO_TO + tests + smoke + report + 0.5.41
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.41
Cola     → C41 safety-sim policy (allowlist for what C40 can command)
```

---

## 6. PRIORIDAD blurb (paste on landing)

```text
Fase C: ★ C40 autonomy executor — HOLD/LAND/GO_TO → sim setpoints.
Package 0.5.41. ≠ execute on copper ≠ Safety allow.
Cola after ACCEPT: C41 safety-sim. Assistant PARKED. Silicon parked.
```

---

## 7. Engineer ★ checklist

- [x] ★ this IC (authorize Claude) — 2026-09-26 (IC passed to Claude = execute)  
- [ ] After landing: Cursor review · then ACCEPT + tag `v0.5.41`  
- [ ] Next = **C41**, not Assistant  
