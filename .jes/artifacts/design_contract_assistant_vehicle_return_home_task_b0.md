# Design Contract — Assistant vehicle RETURN_HOME Task (`DC-assistant-vehicle-return-home-task`)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Author:** JES / Cursor  
**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-30 — ACCEPT T9 + redacta IC siguiente)  
**Type:** Design lock — **fifth** vehicle Task kind (cierra set mando básico). Same seam as HOLD/LAND/GO_TO/TAKEOFF. **Not** `arm()` / FOLLOW / PATROL / CHARGE this DC.  
**Parents:** [T9 TAKEOFF ★](implementation_review_assistant_vehicle_takeoff_task_b1.md) @ **`v0.6.17`** · Engineer cola lock T10 RETURN_HOME · HOLD INV ★ — **no new INV**

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Kind: **`request_return_home`** · capability **`flight.return_home`** · skill **`skill.request_return_home`** (stub) |
| 2 | Schema: reuse `capabilities.intent.Task` — no fork |
| 3 | Classify in **`assistant_task.try_request_return_home_task`** · phrases in **`jarvis.config.VEHICLE_RETURN_HOME_PHRASES`** |
| 4 | Precedence: explain → Continuity defer → HOLD → LAND → GO_TO → TAKEOFF → **RETURN_HOME** → fallthrough |
| 5 | Registry: `flight.return_home` = **`not_implemented`**, **separate** `provider.flight_return_home` `kind=vehicle`, skill stub · **never** `available`. Keep prior rows |
| 6 | Intelligence: membership only · **no** `SoftwareCapabilitySafetyGate` · **no** FS import |
| 7 | Safety: fresh **`ArmedAllowlistSafetyGate()` left disarmed** (gate **B**) · do not `arm()` · `default_safety_gate()` untouched. Allow-list today still `{HOLD,LAND,GO_TO}` — RETURN_HOME not widened this Buy (same honesty as TAKEOFF) |
| 8 | Fulfill: `propose_command(RETURN_HOME)` + `submit_command` · honest Spanish message · never claim RTL executed / returned home |
| 9 | Params: `{}`. No home-point / GPS parse this Buy |
| 10 | Out: `arm()` · allow-list widen · FOLLOW/PATROL/CHARGE · shared verb framework |
| 11 | Next code: IC **`B1-assistant-vehicle-return-home-task`** (T10) → package **`0.6.18`** |

**Product sentence:** chat RTL/home phrase → Task → core submits RETURN_HOME through disarmed ArmedAllowlist → honest reject; never executed.

**After this Buy:** basic mando set in chat = TAKEOFF · HOLD · GO_TO · RETURN_HOME · LAND.
