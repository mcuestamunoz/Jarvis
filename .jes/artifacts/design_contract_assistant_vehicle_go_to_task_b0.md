# Design Contract — Assistant vehicle GO_TO Task (`DC-assistant-vehicle-go-to-task`)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Author:** JES / Cursor  
**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-30 — ACCEPT T7 + procede siguiente IC)  
**Type:** Design lock — **third** vehicle Task kind (same seam as HOLD/LAND). **Not** voice. **Not** `arm()` / coordinate wizard this DC.  
**Parents:** [T7 LAND ★](implementation_review_assistant_vehicle_land_task_b1.md) @ **`v0.6.15`** · [T6 HOLD ★](implementation_review_assistant_vehicle_hold_task_b1.md) · [HOLD INV ★](investigation_report_assistant_vehicle_hold_task_b0.md) — **no new INV**

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Kind: **`request_go_to`** · capability **`flight.go_to`** · skill **`skill.request_go_to`** (stub) |
| 2 | Schema: reuse `capabilities.intent.Task` — no fork |
| 3 | Classify in **`assistant_task.try_request_go_to_task`** · phrases in **`jarvis.config.VEHICLE_GO_TO_PHRASES`** (finite exact match; same normalize) |
| 4 | Precedence: explain → Continuity defer → HOLD → LAND → **GO_TO** → fallthrough |
| 5 | Registry: `flight.go_to` = **`not_implemented`**, **separate** `provider.flight_go_to` `kind=vehicle`, skill stub · **never** `available`. Keep HOLD/LAND/software rows |
| 6 | Intelligence: membership only · **no** `SoftwareCapabilitySafetyGate` · **no** FS import |
| 7 | Safety: fresh **`ArmedAllowlistSafetyGate()` left disarmed** (gate **B**) · `default_safety_gate()` untouched · do not `arm()` |
| 8 | Fulfill in orchestrator: `propose_command(GO_TO, …)` + `submit_command` · honest Spanish message · never claim navigated/executed |
| 9 | **Params this Buy:** `params={}` (empty). **No** coordinate / waypoint parsing from chat. (Sim executor needs `x_m`/`y_m` only if a later Buy arms + ticks — out of scope here; disarmed path never executes) |
| 10 | Out: `arm()` UX · voice · sim executor tick from chat · copper · shared multi-verb framework · FOLLOW/PATROL/CHARGE · **TAKEOFF / RETURN_HOME** (queued as **T9 / T10** after this Buy — Engineer lock 2026-09-30; not this DC) |
| 11 | Next code: IC **`B1-assistant-vehicle-go-to-task`** (T8) → package **`0.6.16`**; then T9 TAKEOFF → T10 RETURN_HOME |

**Product sentence:** chat GO_TO phrase → Task(request_go_to) → core submits GO_TO through disarmed ArmedAllowlist → honest reject; never executed.
