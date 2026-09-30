# Design Contract — Assistant vehicle LAND Task (`DC-assistant-vehicle-land-task`)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Author:** JES / Cursor  
**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-30 — ACCEPT T6 + redacta siguiente)  
**Type:** Design lock — **second** vehicle Task kind (same seam as HOLD). **Not** voice. **Not** GO_TO / `arm()` this DC.  
**Parents:** [T6 HOLD ★](implementation_review_assistant_vehicle_hold_task_b1.md) @ **`v0.6.14`** · [HOLD INV ★](investigation_report_assistant_vehicle_hold_task_b0.md) (seams already mapped — **no new INV**) · C4/C17/C41

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Kind: **`request_land`** · capability **`flight.land`** · skill **`skill.request_land`** (stub) |
| 2 | Schema: reuse `capabilities.intent.Task` — no fork |
| 3 | Classify in **`assistant_task.try_request_land_task`** · phrases in **`jarvis.config.VEHICLE_LAND_PHRASES`** (finite exact match; same normalize as HOLD/Continuity) |
| 4 | Precedence: explain → Continuity defer → HOLD → **LAND** → fallthrough |
| 5 | Registry: `flight.land` = **`not_implemented`**, provider **`kind=vehicle`**, offered `[flight.land]` · skill stub · **never** `available`. Keep HOLD rows. Prefer **separate** `provider.flight_land` (same grain as HOLD) — do not merge providers this Buy |
| 6 | Intelligence: membership only · **no** `SoftwareCapabilitySafetyGate` · **no** FS import |
| 7 | Safety: fresh **`ArmedAllowlistSafetyGate()` left disarmed** (gate **B**, same as HOLD) · `default_safety_gate()` untouched · do not `arm()` |
| 8 | Fulfill in orchestrator: `propose_command(LAND)` + `submit_command` · honest Spanish message from Safety/execution · never claim landed/executed |
| 9 | Out: GO_TO · `arm()` UX · voice · sim executor tick from chat · copper · shared multi-verb refactor beyond thin reuse |
| 10 | Next code: IC **`B1-assistant-vehicle-land-task`** (T7) → package **`0.6.15`** |

**Product sentence:** chat LAND phrase → Task(request_land) → core submits LAND through disarmed ArmedAllowlist → honest reject; never executed.

**Why no INV:** HOLD INV already locked fence, fulfill owner, gate B, registry honesty; LAND is the same path with a new verb/phrase/cap.
