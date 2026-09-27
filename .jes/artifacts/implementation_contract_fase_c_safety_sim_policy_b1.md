# Implementation Contract — Fase C safety-sim policy (`B1-fase-c-safety-sim-policy`)

**Project:** Jarvis  
**Date:** 2026-09-27  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — ★ AUTHORIZED: **implement now**  
**Reviewer:** Cursor against this IC · Engineer spot-check (allow ≠ execute · allowlist = C40 verbs · RejectAll stays default · no copper)

**Status:** ★ **AUTHORIZED** (Engineer 2026-09-27 — IC passed to Claude = execute directly)  
**Parents:**
- [C40 ★ ACCEPT](implementation_contract_fase_c_autonomy_executor_b1.md) — `SimAutonomyExecutor` HOLD/LAND/GO_TO @ **`v0.5.41`**  
- [C17 ★ ACCEPT](implementation_contract_fase_c_safety_real_policy_b1.md) — `ArmedAllowlistSafetyGate` HOLD/LAND only @ **`v0.5.15`**  
- [C4 ★ ACCEPT](implementation_contract_fase_c_autonomy_surface_b1.md) — allow → still `execution="not_implemented"`  
- [Month note](engineer_note_software_month_until_bench_2026_09_26.md) — C41 after C40  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — Safety allow-list **aligned to what C40 can command in sim** (`HOLD` / `LAND` / `GO_TO`), still **allow ≠ execute**, still **RejectAll as shipped default**.  
**Package:** bump **`0.5.41` → `0.5.42`**; git tag **`v0.5.42`** only after Engineer ACCEPT.

**Not** `"executed"` · not wiring `submit_command` into `SimAutonomyExecutor` as copper/sim “execution” · not flipping default to permissive · not AllowAll · not craft↔FS · not Assistant · not silicon · not claiming safe to fly.

**Outputs (required):**
1. Safety policy that can `allow` **HOLD, LAND, and GO_TO** when explicitly armed (opt-in) — either surgically extend `ArmedAllowlistSafetyGate` **or** add a distinct `SimAutonomyAllowlistSafetyGate` (pick one, document; prefer **one** clear gate story)  
2. Tests: disarmed reject · armed allow for those three · armed reject for other verbs · `submit_command` allow path still `execution="not_implemented"` · `default_safety_gate()` still RejectAll  
3. Thin smoke optional: armed gate allows GO_TO (and HOLD/LAND); default still rejects  
4. Report + docs honesty: **allow ≠ execute ≠ flying ≠ C40 tick**  
5. `pyproject.toml` → **`0.5.42`** (+ re-pin `0.5.41` checkpoints)

**Checkpoint:** package **`0.5.42`** · suite green · C17 RejectAll/default regressions green · C40 executor unchanged in role

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-safety-sim-policy`** — allow-list matches C40 verbs |
| 2 | One front | Do **not** fold ICM, craft↔FS, Assistant, silicon, executor rewrite, `"executed"`, house map |
| 3 | What this Buy demonstrates | Safety can say **yes** to the same three verbs the sim executor understands — still nobody “executes” through `submit_command`. **Human:** “el portero ya conoce GO_TO además de HOLD/LAND; allow sigue sin ser execute.” |
| 4 | Allow-list | When armed: **`HOLD`, `LAND`, `GO_TO`** only (parse `autonomy:{verb}:{id}` as C17). Other verbs → reject with clear reason ≠ `"not_implemented"` |
| 5 | RejectAll default | **`default_safety_gate()` → `RejectAllSafetyGate` unchanged** |
| 6 | No AllowAll | Forbidden under `src/` |
| 7 | Allow ≠ execute | `submit_command` on allow remains **`execution="not_implemented"`**. Do **not** call `SimAutonomyExecutor` from `submit_command` / Safety. Callers may still use C40 tick **separately** (outside Safety) as today |
| 8 | C17 relationship | If extending `ArmedAllowlistSafetyGate`, update its allow-list + tests/docs. If new gate, leave C17 HOLD/LAND gate intact and document when to use which |
| 9 | Authority ≠ allow | Unchanged — Authority must not flip allow |
| 10 | ESC arm ≠ Safety arm | Unchanged |
| 11 | C40 / plants / loop | Untouched |
| 12 | Version | **`0.5.41` → `0.5.42`**; tag on ACCEPT only |
| 13 | Forbidden claims | “executed” · “safe to fly” · “GO_TO in air” · “Safety certified” |

**Product sentence:**

```text
El portero de sim ya puede permitir HOLD, LAND y GO_TO cuando lo armas —
RejectAll sigue de default, y allow sigue sin ejecutar nada.
```

**Defaults locked by Cursor:**
- Armed allow-list = C40’s three verbs  
- RejectAll remains shipped default  
- allow ≠ execute (no submit→executor bridge)  
- Package **`0.5.42`**

---

## 1. Package layout (normative intent)

```text
src/jarvis/capabilities/safety.py     # EXTEND or NEW gate
src/jarvis/capabilities/__init__.py   # exports if new

tests/test_fase_c_safety_sim_policy_b1.py   # NEW
# may extend tests/test_fase_c_safety_real_policy_b1.py if C17 gate extended
```

Prefer Python-only (Safety is Python orchestration). C++ twin **not** required unless a natural host twin already exists (it does not for Safety).

---

## 2. Tests (minimum)

| ID | Check |
|---|---|
| T1 | Disarmed → reject (reason ≠ `"not_implemented"`) |
| T2 | Armed → allow HOLD, LAND, GO_TO |
| T3 | Armed → reject TAKEOFF/FOLLOW/… with clear reason |
| T4 | `submit_command` + armed gate allow → `execution="not_implemented"` (never `"executed"`) |
| T5 | `default_safety_gate()` still RejectAll; C17/C4 regressions green |
| T6 | Authority signal does not flip allow |
| T7 | No craft/`library`/Board edits; C40 modules untouched |
| T8 | `pyproject` **`0.5.42`**; suite green |
| T9 | Report: **allow ≠ execute ≠ flying ≠ C40 tick** |

---

## 3. Honesty / forbidden

```text
allow ≠ execute ≠ flying
sim allowlist ≠ copper arm ≠ motors
GO_TO allow ≠ GO_TO in air ≠ SimAutonomyExecutor.tick
```

---

## 4. Acceptance

**PASS when:** T1–T9 · allow-list includes GO_TO · RejectAll default · allow ≠ execute · version `0.5.42`.  
**FAIL if:** `"executed"` · default flipped permissive · AllowAll · craft wiring · “we fly.”

---

## 5. Handoff

```text
Engineer → ★ AUTHORIZED (this IC — Claude implements now)
Claude   → sim-aligned Safety allow-list + tests + report + 0.5.42
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.42
Cola     → C42 ICM register client (ScriptedSpi)
```

---

## 6. PRIORIDAD blurb (paste on landing)

```text
Fase C: ★ C41 safety-sim policy — allowlist HOLD/LAND/GO_TO.
Package 0.5.42. allow ≠ execute. RejectAll stays default.
Cola after ACCEPT: C42 ICM client. Assistant PARKED. Silicon parked.
```

---

## 7. Engineer ★ checklist

- [x] ★ this IC (authorize Claude) — 2026-09-27 (IC passed to Claude = execute)  
- [ ] After landing: Cursor review · then ACCEPT + tag `v0.5.42`  
- [ ] Next = **C42**, not Assistant  
