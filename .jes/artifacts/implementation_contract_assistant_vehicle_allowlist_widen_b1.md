# Implementation Contract — Assistant chat ArmedAllowlist widen (`B1-assistant-vehicle-allowlist-widen`)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.25`**

**Status:** ★ **AUTHORIZED** — await Claude implement → Cursor review → Engineer ★ ACCEPT → tag **`v0.6.25`**.  
**Parents:**
- [DC ★ CLOSED](design_contract_assistant_vehicle_allowlist_widen_b0.md)
- T16 [`B1-esc-fence-import-only`](implementation_review_esc_fence_import_only_b1.md) — ★ ACCEPT CLOSED @ **`v0.6.24`** (tip)
- T13 PATROL ★ @ **`v0.6.21`** · T11 arm UX ★ — shared chat latch · **no new INV**

**Type:** Safety-policy widen of `ArmedAllowlistSafetyGate._ALLOWED_VERBS` so all seven chat vehicle verbs pass when armed. No new Task kind.  
**Opens:** **`0.6.25` / `v0.6.25`** on ACCEPT.  
**Cola:** **T14**

**Not:** CHARGE · copper · sim executor tick from chat · new Task/phrase/cap/skill · route/person parse · FN-016 · mass `0.5.x` tip-pin cleanup · voice · edit prior classify bodies beyond copy/tests that this Buy owns.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-vehicle-allowlist-widen`** |
| 2 | In `src/jarvis/capabilities/safety.py`: set `ArmedAllowlistSafetyGate._ALLOWED_VERBS` to `frozenset({"HOLD","LAND","GO_TO","TAKEOFF","RETURN_HOME","FOLLOW","PATROL"})` — exactly the seven `AutonomyVerb` values with chat Tasks |
| 3 | Update class docstring to state the widen (C17 → C41 GO_TO → **T14 full chat set**). Keep: disarmed → reject; Authority unread; never coupled to `SimulatedEscSink.arm()` / `SimAutonomyExecutor.tick` |
| 4 | Latch API unchanged (`arm`/`disarm`/`armed`/`evaluate`). Shared T11 orchestrator gate unchanged in construction — only the class allow-list set changes |
| 5 | After `armar`: **every** chat vehicle fulfill (HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME/FOLLOW/PATROL) → Safety `allow` + execution `not_implemented`; never `"executed"`; honest Spanish unchanged in meaning |
| 6 | Default (disarmed): all seven still `reject`/`disarmed` |
| 7 | Update `_handle_arm_policy` message text that currently claims TAKEOFF/RETURN_HOME remain `verb_not_allowed` — after widen they do not. Keep “software Safety latch / not ESC/motors/drone” honesty |
| 8 | **No** new registry rows required. Cascade remains **10** caps / **11** skills. Bump `safety.chat_armed_allowlist` capability `version` → `0.6.25` if present |
| 9 | Tests: **new** `tests/test_assistant_vehicle_allowlist_widen_b1.py` T1–T8. Update prior arm/follow/patrol/takeoff/return_home (and any other) suites that assert armed → `verb_not_allowed` for TAKEOFF/RETURN_HOME/FOLLOW/PATROL or frozenset `{HOLD,LAND,GO_TO}` |
| 10 | Version **`0.6.25`**; docs: PRIORIDAD · PLATFORM · CONNECTIONS (**no new C-xxx**) · intelligence README one line · USER_GUIDE one line if needed |
| 11 | Out: CHARGE · copper · sim tick from chat · FN-016 · historical tip-pin mass cleanup |

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/capabilities/safety.py` | widen `_ALLOWED_VERBS` + docstring |
| `src/jarvis/core/orchestrator.py` | arm-policy UX copy only (no fulfill rewiring) |
| `src/jarvis/capabilities/data/default_registry.json` | optional version bump on `safety.chat_armed_allowlist` |
| `tests/test_assistant_vehicle_allowlist_widen_b1.py` | **new** T1–T8 |
| Prior vehicle / arm suites | armed expectations + allow-list frozenset |
| `pyproject.toml` | `0.6.25` |
| Docs | §0.10 |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | `_ALLOWED_VERBS` == seven-verb frozenset; each of HOLD…PATROL ∈ set |
| T2 | Disarmed gate: `propose_command`+`submit_command` for TAKEOFF/FOLLOW/PATROL/RETURN_HOME → `reject`/`disarmed`/`not_attempted` |
| T3 | Armed gate: same four verbs → `allow`/`not_implemented` (never `executed`) |
| T4 | `handle_user_text`: `armar` then `takeoff`/`rtl`/`follow`/`patrol` → `allow` + `not_implemented` in message; HOLD still `allow`/`not_implemented` |
| T5 | `armar` → `desarmar` → `patrol` → back to `disarmed` |
| T6 | Seed: cascade still 10 caps / 11 skills; `default_safety_gate()` still RejectAll |
| T7 | No chat path calls `SimAutonomyExecutor` / no new import of sim executor in orchestrator vehicle fulfills (AST or source scan) |
| T8 | `pyproject` `0.6.25` |

Bump stale `0.6.24` checkpoints this Buy owns.

---

## 3. Acceptance

- [ ] `_ALLOWED_VERBS` widened to seven chat AutonomyVerbs  
- [ ] Armed path: all seven → `allow`/`not_implemented`; disarmed unchanged  
- [ ] Arm UX copy honest · prior suites retargeted · cascade 10/11 · T1–T8 · docs · `0.6.25`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.25`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-vehicle-allowlist-widen (T14)

IC: .jes/artifacts/implementation_contract_assistant_vehicle_allowlist_widen_b1.md
DC: .jes/artifacts/design_contract_assistant_vehicle_allowlist_widen_b0.md (★ CLOSED)
Parent tip: T16 ESC fence ★ ACCEPT CLOSED @ v0.6.24 (shared chat ArmedAllowlist)

Widen ArmedAllowlistSafetyGate._ALLOWED_VERBS in capabilities/safety.py to:
  {HOLD, LAND, GO_TO, TAKEOFF, RETURN_HOME, FOLLOW, PATROL}
Update docstring (T14 full chat set). Latch API unchanged.
Do NOT wire SimAutonomyExecutor from chat. allow ≠ execute.
After armar: takeoff/rtl/follow/patrol → allow/not_implemented (never executed).
Disarmed path unchanged (reject/disarmed).
Update _handle_arm_policy Spanish copy that still says TAKEOFF/RH stay
verb_not_allowed — they no longer do.
No new Task/phrase/cap/skill. Cascade stays 10/11.
Optional: bump safety.chat_armed_allowlist version to 0.6.25.
New tests T1–T8. Retarget prior arm/follow/patrol/takeoff/return_home
suites that asserted verb_not_allowed or frozenset {HOLD,LAND,GO_TO}.
Bump to 0.6.25. Docs + PRIORIDAD. Report.
No ACCEPT claim. CHARGE / copper / FN-016 / mass tip-pin cleanup out.
```
