# Design Contract — Assistant vehicle FOLLOW Task (`DC-assistant-vehicle-follow-task`)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Author:** JES / Cursor  
**Status:** ★ **CLOSED** (Engineer 2026-09-30 — ACCEPT T11 + redacta IC siguiente)  
**Type:** Design lock — **sixth** vehicle Task kind (first post–basic-mando verb). Same seam as HOLD…RETURN_HOME. **Not** allow-list widen. **Not** PATROL/CHARGE. **Not** person/target parse.  
**Parents:** [T11 arm UX ★](implementation_review_assistant_vehicle_arm_ux_b1.md) @ **`v0.6.19`** · HOLD INV ★ — **no new INV** · C4 `AutonomyVerb.FOLLOW` already exists

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Kind: **`request_follow`** · capability **`flight.follow`** · skill **`skill.request_follow`** (stub) |
| 2 | Schema: reuse `capabilities.intent.Task` — no fork |
| 3 | Classify in **`assistant_task.try_request_follow_task`** · phrases in **`jarvis.config.VEHICLE_FOLLOW_PHRASES`** |
| 4 | Precedence: explain → Continuity defer → ARM → DISARM → HOLD → LAND → GO_TO → TAKEOFF → RETURN_HOME → **FOLLOW** → fallthrough |
| 5 | Registry: `flight.follow` = **`not_implemented`**, **separate** `provider.flight_follow` `kind=vehicle`, skill stub · **never** `available`. Keep all prior rows |
| 6 | Intelligence: membership only · **no** `SoftwareCapabilitySafetyGate` · **no** FS import |
| 7 | Safety: submit through the **shared** chat `ArmedAllowlistSafetyGate` from T11 (`_vehicle_chat_safety_gate()`). Do **not** construct a fresh gate. Do **not** call `gate.arm()` inside fulfill. Allow-list stays `{HOLD,LAND,GO_TO}` — FOLLOW **not** widened this Buy (same honesty as TAKEOFF/RETURN_HOME → `verb_not_allowed` when armed; `disarmed` when not) |
| 8 | Fulfill: `propose_command(FOLLOW, params={})` + `submit_command` · honest Spanish message · never claim following / tracking / chasing executed |
| 9 | Params: `{}`. No person / target / GPS / “sígueme a X” parse this Buy (Vision `FOLLOW(person)` stays later) |
| 10 | Out: allow-list widen · PATROL · CHARGE · person-target parse · sim executor FOLLOW tick · voice · copper · edit prior `_handle_vehicle_*` / arm-policy bodies |
| 11 | Next code: IC **`B1-assistant-vehicle-follow-task`** (T12) → package **`0.6.20`** |

**Product sentence:** chat follow/sígueme phrase → Task → core submits FOLLOW through the shared ArmedAllowlist → honest `disarmed` / `verb_not_allowed`; never executed pursuit.

**Why this Buy next:** basic mando + arm latch are CLOSED; `AutonomyVerb.FOLLOW` already exists on the C4 surface but has no chat Task path. Expose it with the same honesty as TAKEOFF/RETURN_HOME before widening the allow-list or adding PATROL/CHARGE.
