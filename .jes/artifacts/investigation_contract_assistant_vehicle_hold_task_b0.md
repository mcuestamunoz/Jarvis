# Investigation Contract — Assistant vehicle HOLD Task seam (`INV-assistant-vehicle-hold-task`)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Cursor (read-only — no `src/` mutation this Buy)  
**Reviewer:** Engineer ★ on findings → then DC/IC

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-30 — ACCEPT T5 + procede IC; INV findings accepted; gate **B**)  
**Type:** **Investigation** — locate seams and recommend a clean HOLD Task design. **Not** an IC. **Not** `src/` changes.  
**Cola:** **T6-inv** — CLOSED → DC+IC HOLD same turn

**Parents:**
- T5 Skills seed — ★ ACCEPT CLOSED @ **`v0.6.13`**
- T0–T4 Assistant Task + registry + SoftwareCapabilitySafetyGate
- C4 autonomy surface: `propose_command` / `submit_command` (allow ≠ execute; `execution` never `"executed"` in shipped `src/`)
- C17/C41 `ArmedAllowlistSafetyGate` (HOLD/LAND/GO_TO; starts disarmed)
- Vision §10–§12 · Engineer order: Skills → vehicle HOLD (first of many verbs)

**Why investigate (not jump to IC):** HOLD crosses `intelligence/` (classify), `capabilities/` (registry + Safety), `flight_software/autonomy` (surface), and possibly `orchestrator` fulfill — fences and honesty (no fake flight) need an explicit map before locking code.

---

## 0. Questions this investigation must answer

| # | Question |
|---|---|
| Q1 | Exact call chain today for HOLD via `submit_command` + which gate (RejectAll vs ArmedAllowlist) and what `execution` / UX strings result |
| Q2 | Where Assistant should classify HOLD phrases (extend `assistant_task` vs new module) and phrase-table home (`config` vs module) |
| Q3 | Capability / Skill / Provider seed honesty: ids, `stub` vs `not_implemented`, never `available` for live flight |
| Q4 | Which Safety gate on the Assistant HOLD path — **must not** reuse `SoftwareCapabilitySafetyGate`; relation to `default_safety_gate()` (stays RejectAll) |
| Q5 | Who fulfills after allow/reject: orchestrator thin call to `submit_command`, or intelligence forbidden from importing FS? |
| Q6 | Precedence vs explain / Continuity defer |
| Q7 | Minimal IC scope for **first** HOLD Buy vs what stays later (LAND, GO_TO, arm UX, sim executor tick, voice) |
| Q8 | Recommended artifact sequence: DC locks → IC T6 code Buy; package bump guess |

**Out of investigation:** implementing HOLD · voice · changing Continuity ranking · copper/GPIO · marking flight `available`

---

## 1. Deliverable

1. `.jes/artifacts/investigation_report_assistant_vehicle_hold_task_b0.md` — answers Q1–Q8 with file:symbol citations  
2. Explicit **recommendation**: go to DC, or go straight to IC if seams are trivial (expected: **DC then IC**)  
3. Update PRIORIDAD / engineering_state to T6-inv delivered → await Engineer ★ on next artifact

---

## 2. Paste note

Investigation is **Cursor-owned** (read-only map). No Claude `src/` until a later IC ★ AUTHORIZED after DC.
