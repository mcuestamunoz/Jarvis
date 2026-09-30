# Implementation Contract — Assistant vehicle FOLLOW Task (`B1-assistant-vehicle-follow-task`)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Cursor** (Engineer 2026-09-30: “Implementa ic”)  
**Reviewer:** Cursor independent pass on request · Engineer ACCEPT → tag **`v0.6.20`**

**Status:** **Implemented** — await review / Engineer ★ ACCEPT → tag **`v0.6.20`**.  
**Parents:**
- [DC ★ CLOSED](design_contract_assistant_vehicle_follow_task_b0.md)
- T11 [`B1-assistant-vehicle-arm-ux`](implementation_review_assistant_vehicle_arm_ux_b1.md) — ★ ACCEPT CLOSED @ **`v0.6.19`**
- HOLD INV ★ — no new INV · C4 `AutonomyVerb.FOLLOW` already shipped

**Type:** Sixth vehicle Assistant Task — FOLLOW phrase → Task → orchestrator fulfill via **shared** chat ArmedAllowlist (T11).  
**Opens:** **`0.6.20` / `v0.6.20`** on ACCEPT.  
**Cola:** **T12**

**Not:** allow-list widen · PATROL · CHARGE · person/target/GPS parse · SoftwareCapabilitySafetyGate for flight · intelligence→FS import · voice · copper · edit prior vehicle/arm fulfill bodies · sim executor FOLLOW tick · generic verb framework.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-vehicle-follow-task`** |
| 2 | `TASK_KIND_REQUEST_FOLLOW = "request_follow"` · `CAPABILITY_FLIGHT_FOLLOW = "flight.follow"` |
| 3 | `try_request_follow_task(intent) -> Task \| None` |
| 4 | `VEHICLE_FOLLOW_PHRASES` — finite frozenset, pre-normalized / accent-free. Minimum seed: `follow`, `follow me`, `seguir`, `sigue`, `sigueme`, `seguirme`, `ven conmigo` — accented forms (`sígueme`) normalize onto accent-free entries |
| 5 | Precedence wire: **after** RETURN_HOME branch, before `return None` |
| 6 | Membership only; **no** `SoftwareCapabilitySafetyGate` |
| 7 | Metadata `task_kind=request_follow` only after membership |
| 8 | Seed **add**: capability `flight.follow` v`0.6.20` `availability=not_implemented` `provider_id=provider.flight_follow` · provider `kind=vehicle` `offered_capability_ids=["flight.follow"]` · skill `skill.request_follow` stub requires `["flight.follow"]`. Keep all prior rows |
| 9 | Fulfill sibling `_handle_vehicle_follow`: `propose_command(AutonomyVerb.FOLLOW, intent_id=..., params={})` + `submit_command` through **`self._vehicle_chat_safety_gate()`** (shared T11 latch — **not** a fresh gate; **not** `gate.arm()` here). `action=vehicle_follow`. Honest Spanish — never claim following/tracking/chasing executed |
| 10 | Guards inside try_*: refuse explain / Continuity / ARM / DISARM / HOLD / LAND / GO_TO / TAKEOFF / RETURN_HOME phrases. Prior vehicle + arm/disarm try_* must also refuse FOLLOW phrases |
| 11 | Do **not** edit prior `_handle_vehicle_*` / `_handle_arm_policy` / `_handle_disarm_policy` bodies beyond adding FOLLOW phrase refusals in classify. Cascade → **9** caps / **10** skills. Prior vehicle + arm suites green |
| 12 | Allow-list **unchanged** `{HOLD,LAND,GO_TO}`. Default (disarmed): FOLLOW → `reject`/`disarmed`. After `armar`: FOLLOW → `verb_not_allowed` (same class as TAKEOFF/RETURN_HOME) |
| 13 | Version **`0.6.20`**; docs: intelligence README T12 · PLATFORM · CONNECTIONS extend (**no new C-xxx**) · PRIORIDAD · USER_GUIDE one line if needed |
| 14 | PATROL / CHARGE / allow-list widen / person-target out |

**Phrase caution:** `sigue` / `follow` are short — exact-match only. Do **not** steal craft lines like “sigue con el frame” or “follow the board layout”.

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/config.py` | `VEHICLE_FOLLOW_PHRASES` |
| `src/jarvis/intelligence/assistant_task.py` | `try_request_follow_task` + FOLLOW refusals in prior try_* |
| `src/jarvis/core/orchestrator.py` | wire after RETURN_HOME; `_handle_vehicle_follow` |
| `src/jarvis/capabilities/data/default_registry.json` | follow cap/provider/skill |
| `tests/test_assistant_vehicle_follow_task_b1.py` | **new** T1–T9 |
| Prior vehicle / arm / cascade tests | counts + FOLLOW refusal + tip `0.6.20` |
| `pyproject.toml` | `0.6.20` |
| Docs | §0.13 |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | FOLLOW phrase → Task `["flight.follow"]`, `task_kind=request_follow` (incl. `sígueme` accent) |
| T2 | Non-follow craft line (`sigue con el frame`, `follow the board`) → `None` |
| T3 | Explain / Continuity / ARM / DISARM / five prior vehicle phrases → FOLLOW try `None`; prior classifiers still match |
| T4 | `handle_user_text` `follow` → Safety reject `disarmed`; never `executed`; `action=vehicle_follow` |
| T5 | Sequence: `armar` then `follow` → `verb_not_allowed` (allow-list unwidened); HOLD still `allow`/`not_implemented` |
| T6 | Seed honesty: `flight.follow` `not_implemented` + vehicle provider; prior 8 caps / 9 skills still present; allow-list still `{HOLD,LAND,GO_TO}` |
| T7 | AST fence on `assistant_task`; `default_safety_gate()` still RejectAll; fulfill uses shared gate (same instance as arm path); empty params |
| T8 | Precedence intact: RETURN_HOME still wins over fallthrough; FOLLOW after RETURN_HOME |
| T9 | `pyproject` `0.6.20` |

Bump stale `0.6.19` checkpoints this Buy owns.

---

## 3. Acceptance

- [ ] Classify + membership + fulfill `submit_command(FOLLOW)` via shared gate  
- [ ] Allow-list unwidened · honest UX · prior verbs/arm unchanged  
- [ ] Registry · cascade 9/10 · T1–T9 · docs · `0.6.20`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.20`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-vehicle-follow-task (T12)

IC: .jes/artifacts/implementation_contract_assistant_vehicle_follow_task_b1.md
DC: .jes/artifacts/design_contract_assistant_vehicle_follow_task_b0.md (★ CLOSED)
Parent: T11 arm UX ★ ACCEPT CLOSED @ v0.6.19 (shared chat ArmedAllowlist)

Add VEHICLE_FOLLOW_PHRASES + try_request_follow_task in assistant_task
(Task request_follow → flight.follow). Membership only — NO SoftwareCapabilitySafetyGate.
Refuse explain / Continuity / ARM / DISARM / HOLD / LAND / GO_TO / TAKEOFF /
RETURN_HOME phrases inside the classifier. Prior try_* must refuse FOLLOW phrases.
Exact match only — do not steal "sigue con el frame".
intelligence must NOT import flight_software.

Wire orchestrator AFTER RETURN_HOME branch:
  propose_command(FOLLOW, params={}) +
  submit_command through self._vehicle_chat_safety_gate() (shared T11 latch).
Do NOT construct a fresh ArmedAllowlistSafetyGate. Do NOT call gate.arm() here.
Do NOT widen _ALLOWED_VERBS (still HOLD/LAND/GO_TO).
Default: reject/disarmed. After armar: verb_not_allowed (like TAKEOFF/RETURN_HOME).
Honest Spanish — never claim following/tracking executed.
action=vehicle_follow.

Do NOT edit prior _handle_vehicle_* / _handle_arm_policy / _handle_disarm_policy bodies
(except classify-side FOLLOW refusals in assistant_task).
Seed registry: flight.follow not_implemented + provider.flight_follow vehicle +
skill.request_follow stub. Keep all prior rows.
Cascade → 9 caps / 10 skills. Prior vehicle + arm suites must stay green.
Tests T1–T9. Bump to 0.6.20. Docs + PRIORIDAD. Report.
No ACCEPT claim. PATROL / CHARGE / allow-list widen / person-target out.
```
