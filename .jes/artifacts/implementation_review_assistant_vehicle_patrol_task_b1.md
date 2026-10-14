# Implementation Review — Assistant vehicle PATROL Task (`B1-assistant-vehicle-patrol-task`)

**Date:** 2026-10-01  
**Reviewer:** Cursor (independent pass — Engineer pasted Claude T13 push summary)  
**Against:** [IC](implementation_contract_assistant_vehicle_patrol_task_b1.md) · [report](implementation_report_assistant_vehicle_patrol_task_b1.md) · [DC ★](design_contract_assistant_vehicle_patrol_task_b0.md)  
**Tip reviewed:** `7e583fb` on `cursor/assistant-patrol-impl-8ac5` (vs `origin/main` `843b77d`)  
**Verdict:** **★ ACCEPT CLOSED** (Engineer 2026-10-01) — Cursor review **PASS WITH NOTES**. Package/tag **`0.6.21` / `v0.6.21`**.

**Process note:** Claude Code implemented. Same-session implementer green is not review of record. This pass re-audits the tip against IC §0 locks with live E2E + pytest.

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| Classify id ≠ fulfill verb / action | **Clear** — `request_patrol` → `flight.patrol` → `AutonomyVerb.PATROL` → `action=vehicle_patrol` |
| SoftwareCapabilitySafetyGate on flight | **Clear** — membership only; no `_software_safety_allows` in PATROL classify body |
| Fresh gate instead of shared T11 latch | **Clear** — `_handle_vehicle_patrol` uses `_vehicle_chat_safety_gate()`; only one `ArmedAllowlistSafetyGate()` construction site |
| `gate.arm()` inside PATROL fulfill | **Clear** — no arm call in fulfill |
| Prior fulfill bodies edited | **Clear** — orchestrator diff vs `origin/main` is purely additive (wire + new handler; 0 removed fulfill lines) |
| Allow-list widen / `safety.py` touch | **Clear** — `safety.py` identical to `origin/main`; `_ALLOWED_VERBS` still `{HOLD,LAND,GO_TO}` |
| Intelligence → FS / core import | **Clear** — AST fence |
| Exact-match steal craft chat | **Clear** — `patrulla del catalogo` / `patrol the board` → classify `None`; falls through to LLM |
| Phrase seed | **Clear** — IC minimum 6 accent-free entries present |
| Wire order wrong | **Clear** — … → FOLLOW → **PATROL** → `return None` |
| Cascade counts | **Clear** — **10** caps / **11** skills; 39 Fase C isolation files gained `skill.request_patrol` |
| FN-016 / ESC comment / mass tip-pin rewrite | **Clear** — absent from commit (parked / baseline restored as Engineer reported) |
| Stale “five vehicle fulfills” docstring | **Found** — remediated this pass (N1) |

---

## 1. Qué aterrizó

| Layer | What |
|---|---|
| Config | `VEHICLE_PATROL_PHRASES` (6 accent-free entries; IC minimum seed complete) |
| Classify | `try_request_patrol_task` → `flight.patrol`; PATROL refusals in all 8 prior try_* |
| Guards | Refuse explain · Continuity · ARM · DISARM · six prior vehicle kinds |
| Fulfill | `_handle_vehicle_patrol` via shared gate; empty `params={}`; honest Spanish |
| Registry | `flight.patrol` `not_implemented` + vehicle provider + `skill.request_patrol` @ `0.6.21` |
| Safety | Allow-list unwidened; default `disarmed`; after ARM → `verb_not_allowed` |
| Precedence | explain → defer → ARM → DISARM → HOLD → LAND → GO_TO → TAKEOFF → RETURN_HOME → FOLLOW → **PATROL** |

Package **`0.6.21`**. No new C-xxx. No waypoint/route parse. No CHARGE / allow-list widen / copper.

---

## 2. Cómo se verificó (this pass)

1. IC §0 locks vs config / classify / fulfill / registry / `safety.py` line-by-line.  
2. Live E2E: `patrol`/`patrulla`/`iniciar patrulla` → `vehicle_patrol` + `disarmed`; `armar` then `patrol` → `verb_not_allowed`; HOLD still `allow`/`not_implemented`; craft lines not stolen.  
3. Shared gate identity with arm path; `propose_command(PATROL, params={})` empty.  
4. Pytest: PATROL + FOLLOW + arm + five vehicle — **68 passed**.  
5. Cascade: registry `10`/`11`; orchestrator additive-only vs authorize tip; 39 Fase C files assert `skill.request_patrol`.  
6. Docs: PRIORIDAD / PLATFORM §13 T13 / CONNECTIONS / USER_GUIDE / intelligence README / report present. Tip narrative already points PATROL landed; widen/CHARGE remain later.  
7. Cleanup honesty: no FN-016 / ESC substring edits; no mass rewrite of historical `0.5.x` tip pins — only Buy-owned checkpoints → `0.6.21` plus cascade skill/count bumps.

---

## 3. IC checklist

| Lock / Test | Verdict |
|---|---|
| §0.2–3 ids + `try_request_patrol_task` | **PASS** |
| §0.4 phrase seed + exact match | **PASS** |
| §0.5 wire after FOLLOW | **PASS** |
| §0.6 membership only / no software Safety | **PASS** |
| §0.7 metadata after membership | **PASS** |
| §0.8 registry honesty + prior rows | **PASS** |
| §0.9 fulfill PATROL + shared gate + honest UX | **PASS** |
| §0.10 guards both directions | **PASS** |
| §0.11 prior bodies untouched / cascade 10/11 | **PASS** |
| §0.12 allow-list unwidened · armed → verb_not_allowed | **PASS** |
| §0.13 version `0.6.21` + docs | **PASS** |
| §0.14 CHARGE / widen / copper / route-parse out | **PASS** |
| T1–T9 | **PASS** |

---

## 4. Dónde nos deja

```text
Chat vehicle path:
  ARM/DISARM (software latch) · TAKEOFF · HOLD · GO_TO · RETURN_HOME · LAND · FOLLOW · PATROL
Next candidates: allow-list widen · CHARGE · copper
```

Last C4 `AutonomyVerb` now has a chat Task. Vehicle-verb cola closed pending ★ ACCEPT.

---

## 5. Cómo suma

Expone `AutonomyVerb.PATROL` en el Tasker con la misma honestidad que FOLLOW/TAKEOFF/RETURN_HOME: el latch compartido de T11 hace visible `verb_not_allowed` tras `armar`, sin ensanchar allow-list ni parsear ruta/waypoint.

---

## 6. Notes

**N1 — Stale gate docstring (remediated).** `_vehicle_chat_safety_gate` still said “five vehicle fulfills” after T12/T13. Updated to “vehicle fulfills (HOLD…PATROL)”.

**N2 — Process.** Claude implementer green ≠ review of record. This Cursor pass is the review of record for IC compliance. Engineer ★ ACCEPT applied this close.

**N3 — Residual (informational).** Historical T8–T12 ACCEPT blocks in PLATFORM still say “PATROL remain later” in their period text; tip narrative is the T13 section + Placement line. T11 ARM UX Spanish message still names TAKEOFF/RETURN_HOME as the `verb_not_allowed` examples (period honesty from that Buy) — FOLLOW/PATROL share the same class by allow-list, covered by tests.

**N4 — Baseline failures.** Full-suite ~54 failures on tip match pre-existing `origin/main` historical pin/FN-016 set per implementer report; this Buy introduced zero new regressions in the vehicle/cascade suites exercised here.

---

## 7. Next

```text
★ ACCEPT CLOSED @ v0.6.21 (Engineer 2026-10-01)
Await Engineer ★ pick: allow-list widen · CHARGE · copper
(FN-016 / ESC comment: separate Buy when authorized)
```
