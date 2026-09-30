# Implementation Contract — Assistant vehicle Safety arm UX (`B1-assistant-vehicle-arm-ux`)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Cursor** (Engineer 2026-09-30: “implementa tú”)  
**Reviewer:** Cursor independent pass on request · Engineer ACCEPT → tag **`v0.6.19`**

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-30) — Cursor review PASS WITH NOTES; package/tag **`0.6.19` / `v0.6.19`**.  
**Parents:**
- [DC ★ CLOSED](design_contract_assistant_vehicle_arm_ux_b0.md)
- T10 [`B1-assistant-vehicle-return-home-task`](implementation_review_assistant_vehicle_return_home_task_b1.md) — ★ ACCEPT CLOSED @ **`v0.6.18`**
- HOLD INV ★ — gate **B**; “who arms” closed by this Buy · **no new INV**

**Type:** Safety-policy Assistant Tasks (arm/disarm) + shared chat `ArmedAllowlistSafetyGate` consumed by existing vehicle fulfills.  
**Closed at:** **`0.6.19` / `v0.6.19`**.  
**Cola:** **T11** ★

**Not:** allow-list widen · FOLLOW/PATROL/CHARGE · AutonomyVerb for arm · ESC/`SimulatedEscSink.arm()` · sim executor tick from chat · voice · copper · edit vehicle phrase tables · claim flight when `allow`

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-vehicle-arm-ux`** |
| 2 | `TASK_KIND_REQUEST_ARM_POLICY = "request_arm_policy"` · `TASK_KIND_REQUEST_DISARM_POLICY = "request_disarm_policy"` · `CAPABILITY_SAFETY_CHAT_ARMED_ALLOWLIST = "safety.chat_armed_allowlist"` |
| 3 | `try_request_arm_policy_task(intent) -> Task \| None` · `try_request_disarm_policy_task(intent) -> Task \| None` |
| 4 | Phrase tables (finite, pre-normalized, exact match): **`VEHICLE_ARM_PHRASES`** minimum seed: `arm`, `armar`, `arma`, `armar safety`, `armar politica`, `armar política`, `arm safety` · **`VEHICLE_DISARM_PHRASES`**: `disarm`, `desarmar`, `desarma`, `disarm safety`, `desarmar safety`. Accented forms normalize onto accent-free entries |
| 5 | Precedence wire in `_handle_global_commands`: after Continuity defer, **before** HOLD: ARM then DISARM branches |
| 6 | Classify: membership on `safety.chat_armed_allowlist` **and** `SoftwareCapabilitySafetyGate` allow (T4 path — capability is `available` + software). Refuse explain / Continuity / all five vehicle phrase tables inside each try_* |
| 7 | Metadata `task_kind` only after Safety allow |
| 8 | Seed **add**: capability `safety.chat_armed_allowlist` v`0.6.19` `availability=available` `provider_id=provider.safety_chat_armed_allowlist` · provider `kind=software` `offered_capability_ids=["safety.chat_armed_allowlist"]` · skills `skill.request_arm_policy` + `skill.request_disarm_policy` stubs requiring that id. Keep all prior rows |
| 9 | Orchestrator: private shared gate helper (e.g. `_vehicle_chat_safety_gate() -> ArmedAllowlistSafetyGate`) — lazy singleton on the orchestrator instance; starts disarmed. **`_handle_arm_policy`**: `gate.arm()`; honest Spanish message that software Safety latch is armed — never drone/ESC/motors. **`_handle_disarm_policy`**: `gate.disarm()`; symmetric honesty. `action=vehicle_arm_policy` / `vehicle_disarm_policy` |
| 10 | **Edit** `_handle_vehicle_hold` / `_land` / `_go_to` / `_takeoff` / `_return_home` to use `_vehicle_chat_safety_gate()` instead of `ArmedAllowlistSafetyGate()`. Keep propose/params/message shape; still never claim executed flight. Do **not** call `gate.arm()` inside those five methods |
| 11 | Allow-list **unchanged** `{HOLD,LAND,GO_TO}`. After ARM: HOLD/LAND/GO_TO → `allow`/`not_implemented`; TAKEOFF/RETURN_HOME → `verb_not_allowed` (or `disarmed` if not armed). Document in messages when reason is `verb_not_allowed` |
| 12 | AST fence: `assistant_task` still no `flight_software` / `vehicle_profiles` / `jarvis.core` |
| 13 | Cascade: skills **9** / caps **8** (was 7/7 — +1 cap, +2 skills). Prior vehicle + software suites green with updated expectations for shared-gate default (still starts disarmed → existing `disarmed` paths hold until an ARM turn) |
| 14 | Version **`0.6.19`**; docs: intelligence README T11 · PLATFORM §10/§12/§13 · CONNECTIONS extend (**no new C-xxx**) · PRIORIDAD · USER_GUIDE one line |
| 15 | FOLLOW / allow-list widen / sim tick / copper out |

**Phrase caution:** `arm` / `arma` are short — exact-match only. Do not steal craft lines like “arma el frame”.

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/config.py` | `VEHICLE_ARM_PHRASES` · `VEHICLE_DISARM_PHRASES` |
| `src/jarvis/intelligence/assistant_task.py` | `try_request_arm_policy_task` · `try_request_disarm_policy_task` |
| `src/jarvis/core/orchestrator.py` | shared gate helper · ARM/DISARM wire+fulfill · retarget five vehicle fulfills |
| `src/jarvis/capabilities/data/default_registry.json` | safety.chat_armed_allowlist + provider + 2 skills |
| `tests/test_assistant_vehicle_arm_ux_b1.py` | **new** T1–T10 |
| Prior vehicle / cascade / T4 software tests | counts + shared-gate regression |
| `pyproject.toml` | `0.6.19` |
| Docs | §0.14 |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | ARM phrase → Task `["safety.chat_armed_allowlist"]`, `task_kind=request_arm_policy` |
| T2 | DISARM phrase → Task `request_disarm_policy` |
| T3 | Non-arm craft line (`arma el frame`) → `None`; explain/Continuity/vehicle phrases → arm/disarm try `None` |
| T4 | `handle_user_text` `armar` → `vehicle_arm_policy`; gate reports armed; message mentions software Safety latch / not motors |
| T5 | Sequence: `armar` then `hold` → Safety `allow`, execution `not_implemented`; never `executed` |
| T6 | Sequence: `armar` then `rtl`/`takeoff` → `verb_not_allowed` (allow-list unwidened) |
| T7 | Sequence: `armar` → `desarmar` → `hold` → back to `disarmed` |
| T8 | Seed honesty: cap `available` + software provider; prior 7 vehicle/software caps still present; allow-list frozenset still `{HOLD,LAND,GO_TO}` |
| T9 | AST fence on `assistant_task`; `default_safety_gate()` still RejectAll |
| T10 | `pyproject` `0.6.19` |

Bump stale `0.6.18` checkpoints this Buy owns.

---

## 3. Acceptance

- [x] ARM/DISARM classify + T4 software Safety + fulfill latch  
- [x] Shared gate retargeted on five vehicle fulfills · allow-list unwidened  
- [x] Honest UX · cascade · T1–T10 · docs · `0.6.19`  
- [x] Cursor review · Engineer ACCEPT · tag **`v0.6.19`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-vehicle-arm-ux (T11)

IC: .jes/artifacts/implementation_contract_assistant_vehicle_arm_ux_b1.md
DC: .jes/artifacts/design_contract_assistant_vehicle_arm_ux_b0.md (★ CLOSED)
Parent: T10 RETURN_HOME ★ ACCEPT CLOSED @ v0.6.18

Add VEHICLE_ARM_PHRASES + VEHICLE_DISARM_PHRASES and
try_request_arm_policy_task / try_request_disarm_policy_task in assistant_task
(Task request_arm_policy|request_disarm_policy → safety.chat_armed_allowlist).
Use membership + SoftwareCapabilitySafetyGate (cap is available + software) —
NOT the vehicle membership-only path.
Refuse explain / Continuity / HOLD / LAND / GO_TO / TAKEOFF / RETURN_HOME phrases.
Exact match only — do not steal "arma el frame".
intelligence must NOT import flight_software.

Orchestrator: own ONE process-scoped ArmedAllowlistSafetyGate (lazy, starts disarmed).
Wire AFTER Continuity defer and BEFORE HOLD:
  arm → gate.arm(); disarm → gate.disarm().
Honest Spanish: software Safety latch only — NEVER claim drone/ESC/motors armed.
action=vehicle_arm_policy / vehicle_disarm_policy.

CRITICAL: retarget _handle_vehicle_hold/land/go_to/takeoff/return_home to use that
shared gate (stop `ArmedAllowlistSafetyGate()` fresh per call). Do not arm inside
those five methods. Do NOT widen _ALLOWED_VERBS (still HOLD/LAND/GO_TO).
After arm: HOLD/LAND/GO_TO → allow/not_implemented; TAKEOFF/RETURN_HOME → verb_not_allowed.

Seed registry: safety.chat_armed_allowlist available + software provider +
skill.request_arm_policy + skill.request_disarm_policy stubs. Keep all prior rows.
Cascade → 8 caps / 9 skills. Prior vehicle suites stay green (default still disarmed).
Tests T1–T10. Bump to 0.6.19. Docs + PRIORIDAD. Report.
No ACCEPT claim. FOLLOW / allow-list widen / sim tick out.
```
