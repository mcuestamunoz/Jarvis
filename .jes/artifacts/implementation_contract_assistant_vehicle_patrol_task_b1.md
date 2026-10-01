# Implementation Contract — Assistant vehicle PATROL Task (`B1-assistant-vehicle-patrol-task`)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.21`**

**Status:** ★ **AUTHORIZED** — await Claude implementation → Cursor review → Engineer ★ ACCEPT → tag **`v0.6.21`**.  
**Parents:**
- [DC ★ CLOSED](design_contract_assistant_vehicle_patrol_task_b0.md)
- T12 [`B1-assistant-vehicle-follow-task`](implementation_review_assistant_vehicle_follow_task_b1.md) — ★ ACCEPT CLOSED @ **`v0.6.20`**
- HOLD INV ★ — no new INV · C4 `AutonomyVerb.PATROL` already shipped

**Type:** Seventh vehicle Assistant Task — PATROL phrase → Task → orchestrator fulfill via **shared** chat ArmedAllowlist (T11). Last C4 AutonomyVerb in the chat Tasker.  
**Opens:** **`0.6.21` / `v0.6.21`** on ACCEPT.  
**Cola:** **T13**

**Not:** allow-list widen · CHARGE · copper · waypoint/route/GPS parse · SoftwareCapabilitySafetyGate for flight · intelligence→FS import · voice · edit prior vehicle/arm fulfill bodies · sim executor PATROL tick · generic verb framework.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-vehicle-patrol-task`** |
| 2 | `TASK_KIND_REQUEST_PATROL = "request_patrol"` · `CAPABILITY_FLIGHT_PATROL = "flight.patrol"` |
| 3 | `try_request_patrol_task(intent) -> Task \| None` |
| 4 | `VEHICLE_PATROL_PHRASES` — finite frozenset, pre-normalized / accent-free. Minimum seed: `patrol`, `patrulla`, `patrullar`, `hacer patrulla`, `start patrol`, `iniciar patrulla` — accented forms normalize onto accent-free entries |
| 5 | Precedence wire: **after** FOLLOW branch, before `return None` |
| 6 | Membership only; **no** `SoftwareCapabilitySafetyGate` |
| 7 | Metadata `task_kind=request_patrol` only after membership |
| 8 | Seed **add**: capability `flight.patrol` v`0.6.21` `availability=not_implemented` `provider_id=provider.flight_patrol` · provider `kind=vehicle` `offered_capability_ids=["flight.patrol"]` · skill `skill.request_patrol` stub requires `["flight.patrol"]`. Keep all prior rows |
| 9 | Fulfill sibling `_handle_vehicle_patrol`: `propose_command(AutonomyVerb.PATROL, intent_id=..., params={})` + `submit_command` through **`self._vehicle_chat_safety_gate()`** (shared T11 latch — **not** a fresh gate; **not** `gate.arm()` here). `action=vehicle_patrol`. Honest Spanish — never claim patrol/circuit/route executed |
| 10 | Guards inside try_*: refuse explain / Continuity / ARM / DISARM / HOLD / LAND / GO_TO / TAKEOFF / RETURN_HOME / FOLLOW phrases. Prior vehicle + arm/disarm try_* must also refuse PATROL phrases |
| 11 | Do **not** edit prior `_handle_vehicle_*` / `_handle_arm_policy` / `_handle_disarm_policy` bodies beyond adding PATROL phrase refusals in classify. Cascade → **10** caps / **11** skills. Prior vehicle + arm + follow suites green |
| 12 | Allow-list **unchanged** `{HOLD,LAND,GO_TO}`. Default (disarmed): PATROL → `reject`/`disarmed`. After `armar`: PATROL → `verb_not_allowed` (same class as TAKEOFF/RETURN_HOME/FOLLOW) |
| 13 | Version **`0.6.21`**; docs: intelligence README T13 · PLATFORM · CONNECTIONS extend (**no new C-xxx**) · PRIORIDAD · USER_GUIDE one line if needed |
| 14 | CHARGE / allow-list widen / copper / route-parse out |

**Phrase caution:** `patrol` / `patrulla` are short — exact-match only. Do **not** steal craft lines like “patrulla del catalogo” or “patrol the board layout”.

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/config.py` | `VEHICLE_PATROL_PHRASES` |
| `src/jarvis/intelligence/assistant_task.py` | `try_request_patrol_task` + PATROL refusals in prior try_* |
| `src/jarvis/core/orchestrator.py` | wire after FOLLOW; `_handle_vehicle_patrol` |
| `src/jarvis/capabilities/data/default_registry.json` | patrol cap/provider/skill |
| `tests/test_assistant_vehicle_patrol_task_b1.py` | **new** T1–T9 |
| Prior vehicle / arm / follow / cascade tests | counts + PATROL refusal + tip `0.6.21` |
| `pyproject.toml` | `0.6.21` |
| Docs | §0.13 |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | PATROL phrase → Task `["flight.patrol"]`, `task_kind=request_patrol` |
| T2 | Non-patrol craft line (`patrulla del catalogo`, `patrol the board`) → `None` |
| T3 | Explain / Continuity / ARM / DISARM / six prior vehicle phrases → PATROL try `None`; prior classifiers still match |
| T4 | `handle_user_text` `patrol` → Safety reject `disarmed`; never `executed`; `action=vehicle_patrol` |
| T5 | Sequence: `armar` then `patrol` → `verb_not_allowed` (allow-list unwidened); HOLD still `allow`/`not_implemented` |
| T6 | Seed honesty: `flight.patrol` `not_implemented` + vehicle provider; prior 9 caps / 10 skills still present; allow-list still `{HOLD,LAND,GO_TO}` |
| T7 | AST fence on `assistant_task`; `default_safety_gate()` still RejectAll; fulfill uses shared gate (same instance as arm path); empty params |
| T8 | Precedence intact: FOLLOW still wins its phrases; PATROL after FOLLOW |
| T9 | `pyproject` `0.6.21` |

Bump stale `0.6.20` checkpoints this Buy owns.

---

## 3. Acceptance

- [ ] Classify + membership + fulfill `submit_command(PATROL)` via shared gate  
- [ ] Allow-list unwidened · honest UX · prior verbs/arm/follow unchanged  
- [ ] Registry · cascade 10/11 · T1–T9 · docs · `0.6.21`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.21`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-vehicle-patrol-task (T13)

IC: .jes/artifacts/implementation_contract_assistant_vehicle_patrol_task_b1.md
DC: .jes/artifacts/design_contract_assistant_vehicle_patrol_task_b0.md (★ CLOSED)
Parent: T12 FOLLOW ★ ACCEPT CLOSED @ v0.6.20 (shared chat ArmedAllowlist)

Add VEHICLE_PATROL_PHRASES + try_request_patrol_task in assistant_task
(Task request_patrol → flight.patrol). Membership only — NO SoftwareCapabilitySafetyGate.
Refuse explain / Continuity / ARM / DISARM / HOLD / LAND / GO_TO / TAKEOFF /
RETURN_HOME / FOLLOW phrases inside the classifier. Prior try_* must refuse PATROL phrases.
Exact match only — do not steal "patrulla del catalogo".
intelligence must NOT import flight_software.

Wire orchestrator AFTER FOLLOW branch:
  propose_command(PATROL, params={}) +
  submit_command through self._vehicle_chat_safety_gate() (shared T11 latch).
Do NOT construct a fresh ArmedAllowlistSafetyGate. Do NOT call gate.arm() here.
Do NOT widen _ALLOWED_VERBS (still HOLD/LAND/GO_TO).
Default: reject/disarmed. After armar: verb_not_allowed (like FOLLOW).
Honest Spanish — never claim patrol/circuit executed.
action=vehicle_patrol.

Do NOT edit prior _handle_vehicle_* / _handle_arm_policy / _handle_disarm_policy bodies
(except classify-side PATROL refusals in assistant_task).
Seed registry: flight.patrol not_implemented + provider.flight_patrol vehicle +
skill.request_patrol stub. Keep all prior rows.
Cascade → 10 caps / 11 skills. Prior vehicle + arm + follow suites must stay green.
Tests T1–T9. Bump to 0.6.21. Docs + PRIORIDAD. Report.
No ACCEPT claim. CHARGE / allow-list widen / copper / route-parse out.
```
