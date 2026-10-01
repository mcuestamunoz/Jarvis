# Design Contract — Assistant vehicle PATROL Task (`DC-assistant-vehicle-patrol-task`)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Author:** JES / Cursor  
**Status:** ★ **CLOSED** (Engineer 2026-10-01 — ACCEPT T12 + procede con PATROL)  
**Type:** Design lock — **seventh** vehicle Task kind (last C4 `AutonomyVerb` without a chat Task). Same seam as FOLLOW. **Not** allow-list widen. **Not** CHARGE. **Not** waypoint/route parse.  
**Parents:** [T12 FOLLOW ★](implementation_review_assistant_vehicle_follow_task_b1.md) @ **`v0.6.20`** · HOLD INV ★ — **no new INV** · C4 `AutonomyVerb.PATROL` already exists

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Kind: **`request_patrol`** · capability **`flight.patrol`** · skill **`skill.request_patrol`** (stub) |
| 2 | Schema: reuse `capabilities.intent.Task` — no fork |
| 3 | Classify in **`assistant_task.try_request_patrol_task`** · phrases in **`jarvis.config.VEHICLE_PATROL_PHRASES`** |
| 4 | Precedence: explain → Continuity defer → ARM → DISARM → HOLD → LAND → GO_TO → TAKEOFF → RETURN_HOME → FOLLOW → **PATROL** → fallthrough |
| 5 | Registry: `flight.patrol` = **`not_implemented`**, **separate** `provider.flight_patrol` `kind=vehicle`, skill stub · **never** `available`. Keep all prior rows |
| 6 | Intelligence: membership only · **no** `SoftwareCapabilitySafetyGate` · **no** FS import |
| 7 | Safety: submit through the **shared** chat `ArmedAllowlistSafetyGate` from T11 (`_vehicle_chat_safety_gate()`). Do **not** construct a fresh gate. Do **not** call `gate.arm()` inside fulfill. Allow-list stays `{HOLD,LAND,GO_TO}` — PATROL **not** widened this Buy (same honesty as FOLLOW → `verb_not_allowed` when armed; `disarmed` when not) |
| 8 | Fulfill: `propose_command(PATROL, params={})` + `submit_command` · honest Spanish message · never claim patrol / circuit / route executed |
| 9 | Params: `{}`. No waypoint / polygon / GPS / “patrulla la zona X” parse this Buy |
| 10 | Out: allow-list widen · CHARGE · copper · route parse · sim executor PATROL tick · voice · edit prior `_handle_vehicle_*` / arm-policy bodies |
| 11 | Next code: IC **`B1-assistant-vehicle-patrol-task`** (T13) → package **`0.6.21`** |

**Product sentence:** chat patrol/patrulla phrase → Task → core submits PATROL through the shared ArmedAllowlist → honest `disarmed` / `verb_not_allowed`; never executed circuit.

**Why this Buy next:** FOLLOW closed the first post–basic-mando verb; `AutonomyVerb.PATROL` is the last C4 verb still without a chat Task. Finish the intelligence vehicle-verb cola before allow-list widen / CHARGE / copper.
