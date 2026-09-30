# Design Contract — Assistant vehicle HOLD Task (`DC-assistant-vehicle-hold-task`)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Author:** JES / Cursor  
**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-30 — ACCEPT T5 + procede IC; INV ★; gate **B** locked)  
**Type:** Design lock — first vehicle Task kind. **Not** voice. **Not** LAND/GO_TO this DC.  
**Parents:** [INV report ★](investigation_report_assistant_vehicle_hold_task_b0.md) · T5 ★ @ **`v0.6.13`** · T0–T4 Assistant seam · C4/C17 autonomy+Safety

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Kind: **`request_hold`** · capability **`flight.hold`** · skill **`skill.request_hold`** (stub) |
| 2 | Schema: reuse `capabilities.intent.Task` — no fork |
| 3 | Classify in **`assistant_task.try_request_hold_task`** · phrases in **`jarvis.config.VEHICLE_HOLD_PHRASES`** (finite exact match after same normalize family as Continuity defer) |
| 4 | Precedence: explain → Continuity defer → **HOLD** → fallthrough |
| 5 | Registry: `flight.hold` = **`not_implemented`**, provider **`kind=vehicle`**, offered `[flight.hold]` · skill stub requires `[flight.hold]` · **never** `available` |
| 6 | Intelligence: may membership-check `flight.hold` exists · **must not** use `SoftwareCapabilitySafetyGate` · **must not** import `flight_software` |
| 7 | Safety at fulfill: fresh **`ArmedAllowlistSafetyGate()` left disarmed** (INV option **B**) · `default_safety_gate()` unchanged RejectAll · do not `arm()` on product chat path |
| 8 | Fulfill in **orchestrator** (or thin core helper): `propose_command(HOLD)` + `submit_command(cmd, gate)` · format honest message from `AutonomySubmissionResult` (expect reject/`disarmed` / `not_attempted`) |
| 9 | UX: no claim of flight executed · message must surface Safety reject reason |
| 10 | Out: LAND · GO_TO · voice · sim executor tick from chat · copper |
| 11 | Next code: IC **`B1-assistant-vehicle-hold-task`** (T6) → package **`0.6.14`** |

**Product sentence:** chat/CLI phrase → Task(request_hold) → core submits HOLD through disarmed ArmedAllowlist → honest reject; never executed.
