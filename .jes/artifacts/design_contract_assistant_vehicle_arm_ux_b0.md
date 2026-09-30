# Design Contract — Assistant vehicle Safety arm UX (`DC-assistant-vehicle-arm-ux`)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Author:** JES / Cursor  
**Status:** ★ **CLOSED** (Engineer 2026-09-30 — ACCEPT T10 + procede redactar siguiente IC)  
**Type:** Design lock — first **Safety policy** chat Buy after basic mando. **Not** a sixth AutonomyVerb. **Not** FOLLOW/PATROL/CHARGE. **Not** allow-list widen. **Not** ESC/hardware arm.  
**Parents:** [T10 RETURN_HOME ★](implementation_review_assistant_vehicle_return_home_task_b1.md) @ **`v0.6.18`** · [HOLD INV ★](investigation_report_assistant_vehicle_hold_task_b0.md) (gate **B** + “who arms” deferred) · C17/C41 `ArmedAllowlistSafetyGate`

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Kinds: **`request_arm_policy`** + **`request_disarm_policy`** · capability **`safety.chat_armed_allowlist`** · skills **`skill.request_arm_policy`** / **`skill.request_disarm_policy`** (stubs) |
| 2 | Schema: reuse `capabilities.intent.Task` — no fork · **not** an `AutonomyVerb` |
| 3 | Classify in **`assistant_task.try_request_arm_policy_task`** / **`try_request_disarm_policy_task`** · phrases in **`jarvis.config.VEHICLE_ARM_PHRASES`** / **`VEHICLE_DISARM_PHRASES`** |
| 4 | Precedence: explain → Continuity defer → **ARM** → **DISARM** → HOLD → LAND → GO_TO → TAKEOFF → RETURN_HOME → fallthrough |
| 5 | Registry: `safety.chat_armed_allowlist` = **`available`**, provider **`provider.safety_chat_armed_allowlist`** `kind=software` (arm/disarm of the software latch **is** implemented). Skills stub. Keep all prior vehicle/software rows |
| 6 | Intelligence: membership + **`SoftwareCapabilitySafetyGate`** (software+available — same T4 path as explain/defer) · **no** FS import |
| 7 | **Shared chat gate (critical):** Orchestrator owns **one** process-scoped `ArmedAllowlistSafetyGate` for the vehicle chat path (lazy-created). ARM → `gate.arm()`; DISARM → `gate.disarm()`. Starts disarmed. **Not** stored on `InteractiveSessionState` (clears would wipe the latch). **Not** `SimulatedEscSink.arm()`. **Not** `default_safety_gate()` |
| 8 | **Retarget five vehicle fulfills:** HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME must call `submit_command` with **that shared gate** (stop constructing a fresh never-armed gate per call — otherwise ARM is a no-op). Do not change propose/params/UX honesty shape beyond reading the shared gate’s outcome |
| 9 | After ARM + HOLD/LAND/GO_TO: expect Safety **`allow`** + execution **`not_implemented`** — message must say so; never claim flight/motors. After ARM + TAKEOFF/RETURN_HOME: expect **`verb_not_allowed`** (allow-list still `{HOLD,LAND,GO_TO}` — **no widen this Buy**) |
| 10 | UX honesty mandatory: “Software Safety latch” / “política Safety del chat” — never “armado el drone”, never ESC, never copper |
| 11 | Out: allow-list widen · FOLLOW/PATROL/CHARGE · sim executor tick from chat · voice · copper · persist arm across process restart · auto-arm on boot |
| 12 | Next code: IC **`B1-assistant-vehicle-arm-ux`** (T11) → package **`0.6.19`** |

**Product sentence:** chat `armar`/`arm` → Task → orchestrator arms the shared ArmedAllowlist latch; later HOLD/LAND/GO_TO on the same process get Safety `allow`/`not_implemented` (still not flight). `desarmar` clears the latch.

**Why this Buy next:** basic mando is CLOSED; every verb still dies at `disarmed` because fulfills use a fresh gate. ARM is the policy Buy that makes Safety outcomes differ without adding another verb.
