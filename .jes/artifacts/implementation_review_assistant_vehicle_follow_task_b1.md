# Implementation Review — Assistant vehicle FOLLOW Task (`B1-assistant-vehicle-follow-task`)

**Date:** 2026-09-30  
**Reviewer:** Cursor (independent pass — Engineer: *Review del ic*)  
**Against:** [IC](implementation_contract_assistant_vehicle_follow_task_b1.md) · [report](implementation_report_assistant_vehicle_follow_task_b1.md) · [DC ★](design_contract_assistant_vehicle_follow_task_b0.md)  
**Verdict:** **PASS WITH NOTES** — ready for Engineer ★ ACCEPT → tag **`v0.6.20`**. No ACCEPT claimed in this review.

**Process note:** Cursor implemented (Engineer “Implementa ic”). Same-session implementer green is not review of record. This pass re-audits the tip against IC §0 locks with live E2E + pytest.

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| Classify id ≠ fulfill verb / action | **Clear** — `request_follow` → `flight.follow` → `AutonomyVerb.FOLLOW` → `action=vehicle_follow` |
| SoftwareCapabilitySafetyGate on flight | **Clear** — membership only; no `_software_safety_allows` in executable body |
| Fresh gate instead of shared T11 latch | **Clear** — `_handle_vehicle_follow` uses `_vehicle_chat_safety_gate()`; only one `ArmedAllowlistSafetyGate()` construction site |
| `gate.arm()` inside FOLLOW fulfill | **Clear** — no arm call in fulfill |
| Prior fulfill bodies edited | **Clear** — orchestrator diff vs authorize tip is purely additive (0 removed lines) |
| Allow-list widen / `safety.py` touch | **Clear** — `safety.py` identical to `v0.6.19`; `_ALLOWED_VERBS` still `{HOLD,LAND,GO_TO}` |
| Intelligence → FS / core import | **Clear** — AST fence |
| Exact-match steal craft chat | **Clear** — `sigue con el frame` / `follow the board` → classify `None`; falls through to LLM |
| Accent seed (`sígueme`) | **Clear** — normalizes onto `sigueme` |
| Wire order wrong | **Clear** — … → RETURN_HOME → **FOLLOW** → `return None` |
| Cascade counts | **Clear** — **9** caps / **10** skills |
| PLATFORM tip narrative still says FOLLOW later | **Found** — remediated this pass (N1) |

---

## 1. Qué aterrizó

| Layer | What |
|---|---|
| Config | `VEHICLE_FOLLOW_PHRASES` (7 accent-free entries; IC minimum seed complete) |
| Classify | `try_request_follow_task` → `flight.follow`; FOLLOW refusals in prior try_* |
| Guards | Refuse explain · Continuity · ARM · DISARM · five prior vehicle kinds |
| Fulfill | `_handle_vehicle_follow` via shared gate; empty `params={}`; honest Spanish |
| Registry | `flight.follow` `not_implemented` + vehicle provider + `skill.request_follow` @ `0.6.20` |
| Safety | Allow-list unwidened; default `disarmed`; after ARM → `verb_not_allowed` |
| Precedence | explain → defer → ARM → DISARM → HOLD → LAND → GO_TO → TAKEOFF → RETURN_HOME → **FOLLOW** |

Package **`0.6.20`**. No new C-xxx. No person/target parse. No PATROL/CHARGE.

---

## 2. Cómo se verificó (this pass)

1. IC §0 locks vs config / classify / fulfill / registry / safety.py line-by-line.  
2. Live E2E: `follow`/`sígueme`/`follow me`/`ven conmigo` → `vehicle_follow` + `disarmed`; `armar` then `follow` → `verb_not_allowed`; HOLD still `allow`/`not_implemented`; `rtl`/`explain`/`estado` intact; craft lines not stolen.  
3. Shared gate identity with arm path; `propose_command(FOLLOW, params={})` empty.  
4. Pytest: FOLLOW + arm + five vehicle + skills — **66 passed**.  
5. Cascade: registry `9`/`10`; orchestrator additive-only vs IC-authorize tip.  
6. Docs: PRIORIDAD / PLATFORM §13 T12 / CONNECTIONS / USER_GUIDE / intelligence README / report present; tip-narrative drift fixed (N1).

---

## 3. IC checklist

| Lock / Test | Verdict |
|---|---|
| §0.2–3 ids + `try_request_follow_task` | **PASS** |
| §0.4 phrase seed + exact match + accents | **PASS** |
| §0.5 wire after RETURN_HOME | **PASS** |
| §0.6 membership only / no software Safety | **PASS** |
| §0.7 metadata after membership | **PASS** |
| §0.8 registry honesty + prior rows | **PASS** |
| §0.9 fulfill FOLLOW + shared gate + honest UX | **PASS** |
| §0.10 guards both directions | **PASS** |
| §0.11 prior bodies untouched / cascade 9/10 | **PASS** |
| §0.12 allow-list unwidened · armed → verb_not_allowed | **PASS** |
| §0.13 version `0.6.20` + docs | **PASS** (after N1) |
| §0.14 PATROL / CHARGE / widen / person-target out | **PASS** |
| T1–T9 | **PASS** |

---

## 4. Dónde nos deja

```text
Chat vehicle path:
  ARM/DISARM (software latch) · TAKEOFF · HOLD · GO_TO · RETURN_HOME · LAND · FOLLOW
Next candidates: PATROL · allow-list widen · CHARGE
```

---

## 5. Cómo suma

Expone `AutonomyVerb.FOLLOW` en el Tasker con la misma honestidad que TAKEOFF/RETURN_HOME: el latch compartido de T11 hace visible `verb_not_allowed` tras `armar`, sin ensanchar allow-list ni parsear persona/target.

---

## 6. Notes

**N1 — PLATFORM tip narrative drift (remediated).** §10 / Placement still said “FOLLOW … remain later Buys” after T12 landed. Updated to point at T12 + leave PATROL/widen/CHARGE as later. Historical T8–T10 ACCEPT blocks left as period records.

**N2 — Process.** Same-session Cursor implementer green ≠ review of record. This pass is the review of record. No ★ ACCEPT / tag without Engineer.

**N3 — Residual (informational).** Older intelligence README subsections for T8/T9 still say “no FOLLOW” in their historical “still not” bullets — period text under closed Buys; tip narrative is the T12 section at top.

---

## 7. Next

```text
Await Engineer ★ ACCEPT → tag v0.6.20
Then pick: PATROL · allow-list widen · CHARGE
```
