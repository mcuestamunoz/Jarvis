# Design Contract — Assistant chat ArmedAllowlist widen (`DC-assistant-vehicle-allowlist-widen`)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Author:** JES / Cursor  
**Status:** ★ **CLOSED** (Engineer 2026-10-01 — T13 ★ ACCEPT + procede siguiente IC)  
**Type:** Design lock — Safety **policy** widen of `ArmedAllowlistSafetyGate._ALLOWED_VERBS` for the chat vehicle path. **Not** a new Task kind. **Not** CHARGE. **Not** copper / sim tick from chat.  
**Parents:** [T13 PATROL ★](implementation_review_assistant_vehicle_patrol_task_b1.md) @ **`v0.6.21`** · [T11 arm UX ★](implementation_review_assistant_vehicle_arm_ux_b1.md) @ **`v0.6.19`** · C17/C41 `ArmedAllowlistSafetyGate` · **no new INV**

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Widen `ArmedAllowlistSafetyGate._ALLOWED_VERBS` from `{HOLD,LAND,GO_TO}` to **all seven** C4 `AutonomyVerb` values that already have a chat Task: `{HOLD,LAND,GO_TO,TAKEOFF,RETURN_HOME,FOLLOW,PATROL}` |
| 2 | Latch semantics unchanged: starts **disarmed** → all verbs `reject`/`disarmed`; after chat `armar` → listed verbs `allow`; `desarmar` clears |
| 3 | Honesty unchanged: `allow` still yields execution **`not_implemented`** on `submit_command` — never `"executed"`, never motors/ESC/copper, never claim flight |
| 4 | **Do not** wire `SimAutonomyExecutor.tick` (or any sim driver) from chat fulfills this Buy. Sim executor may remain HOLD/LAND/GO_TO-only — Safety allow-list may be **wider** than sim-supported verbs (allow ≠ execute) |
| 5 | **No** new Task kind / phrase table / capability / skill / provider. Cascade stays **10** caps / **11** skills. Optional: bump `safety.chat_armed_allowlist` seed `version` → `0.6.22` |
| 6 | Shared T11 gate remains the one chat latch — do not construct a second gate; do not call `gate.arm()` inside vehicle fulfills |
| 7 | Update arm-policy Spanish copy that still says TAKEOFF/RETURN_HOME stay `verb_not_allowed` after `armar` — after this Buy they join allow/`not_implemented` |
| 8 | Retarget prior vehicle/arm suites that asserted armed → `verb_not_allowed` for TAKEOFF/RETURN_HOME/FOLLOW/PATROL to expect `allow` + `not_implemented` instead; HOLD/LAND/GO_TO paths stay green |
| 9 | Out: CHARGE (not an `AutonomyVerb`) · copper · route/person parse · FN-016 · mass historical `0.5.x` tip-pin cleanup · voice · edit classify phrase tables |
| 10 | Next code: IC **`B1-assistant-vehicle-allowlist-widen`** (T14) → package **`0.6.22`** |

**Product sentence:** after `armar`, every chat vehicle verb (HOLD…PATROL) gets Safety `allow` / execution `not_implemented` — still not flight; `verb_not_allowed` no longer hides the four post–basic-mando verbs.

**Why this Buy next:** vehicle-verb cola is ★ CLOSED @ `v0.6.21`. The latch is armed but half the verbs still die at `verb_not_allowed`. Widen is the smallest Safety-policy step before CHARGE / copper.
