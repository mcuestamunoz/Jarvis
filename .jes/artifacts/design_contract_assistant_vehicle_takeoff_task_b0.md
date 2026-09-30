# Design Contract — Assistant vehicle TAKEOFF Task (`DC-assistant-vehicle-takeoff-task`)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Author:** JES / Cursor  
**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-30 — ACCEPT T8 + procede T9)  
**Type:** Design lock — **fourth** vehicle Task kind (same seam as HOLD/LAND/GO_TO). **Not** `arm()` / RETURN_HOME this DC.  
**Parents:** [T8 GO_TO ★](implementation_review_assistant_vehicle_go_to_task_b1.md) @ **`v0.6.16`** · Engineer cola lock T9 TAKEOFF → T10 RETURN_HOME · HOLD INV ★ — **no new INV**

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Kind: **`request_takeoff`** · capability **`flight.takeoff`** · skill **`skill.request_takeoff`** (stub) |
| 2 | Schema: reuse `capabilities.intent.Task` — no fork |
| 3 | Classify in **`assistant_task.try_request_takeoff_task`** · phrases in **`jarvis.config.VEHICLE_TAKEOFF_PHRASES`** |
| 4 | Precedence: explain → Continuity defer → HOLD → LAND → GO_TO → **TAKEOFF** → fallthrough |
| 5 | Registry: `flight.takeoff` = **`not_implemented`**, **separate** `provider.flight_takeoff` `kind=vehicle`, skill stub · **never** `available`. Keep prior rows |
| 6 | Intelligence: membership only · **no** `SoftwareCapabilitySafetyGate` · **no** FS import |
| 7 | Safety: fresh **`ArmedAllowlistSafetyGate()` left disarmed** (gate **B**) · do not `arm()` · `default_safety_gate()` untouched. **Note:** allow-list today is HOLD/LAND/GO_TO only — when armed, TAKEOFF would be `verb_not_allowed` until a later allow-list Buy; gate B still yields honest `disarmed` |
| 8 | Fulfill: `propose_command(TAKEOFF)` + `submit_command` · honest Spanish message · never claim airborne/executed |
| 9 | Params: `{}` (none). No altitude parse this Buy |
| 10 | Out: RETURN_HOME (T10) · `arm()` · FOLLOW/PATROL/CHARGE · shared verb framework |
| 11 | Next code: IC **`B1-assistant-vehicle-takeoff-task`** (T9) → package **`0.6.17`** |

**Product sentence:** chat TAKEOFF phrase → Task → core submits TAKEOFF through disarmed ArmedAllowlist → honest reject; never executed.
