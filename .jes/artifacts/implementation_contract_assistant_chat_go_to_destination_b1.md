# Implementation Contract — Chat GO_TO destination (`B1-assistant-chat-go-to-destination`)

**Project:** Jarvis  
**Date:** 2026-10-03  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.41`**

**Status:** Cursor **PASS WITH NOTES** — await Engineer ★ ACCEPT → tag `v0.6.41` (closes SD-GO_TO note on ACCEPT).  
**Parents:** [DC ★ CLOSED](design_contract_assistant_chat_go_to_destination_b0.md) · [SD-GO_TO note](engineer_note_t20_goto_chat_sim_destination_debt.md) · T20 ★ @ `v0.6.29` · T25 Skill-first GO_TO ★ @ `v0.6.34`  
**Type:** Close SD-GO_TO — resolver seam + wire into existing T20 tick; bare GO_TO stays honest without inventing coords.  
**Opens:** **`0.6.41` / `v0.6.41`**. **Cola:** **T32**

**Not:** inventing default `0,0`/home · live ESC/copper · TAKEOFF/RH/FOLLOW/PATROL sim ticks · voice · GPS hardware · second sim stack · flipping `flight.go_to` to `available`.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-chat-go-to-destination`** — closes **SD-GO_TO** |
| 2 | **Resolver seam** (orch helper, e.g. `_resolve_go_to_destination(intent) -> tuple[float, float] \| None`), ordered: (a) `intent.metadata` both finite `go_to_x_m` + `go_to_y_m` → that pair (**connect plug** for later GPS/world/voice); (b) else finite prove-now parse on normalized raw text: `^(go to\|goto\|ir a\|ve a)\s+([+-]?\d+(?:\.\d+)?)\s+([+-]?\d+(?:\.\d+)?)$` → floats; (c) else `None`. **No** silent default coordinates |
| 3 | **Classify:** `try_request_go_to_task` matches bare `VEHICLE_GO_TO_PHRASES` **or** prove-now destination pattern (same normalize). Sibling try_* (HOLD/LAND/TAKEOFF/…/CHARGE/ARM/…) refuse destination-bearing GO_TO patterns so they cannot steal. Skill-first: chat still `run_skill("skill.request_go_to")` then `_handle_vehicle_go_to` |
| 4 | **`_handle_vehicle_go_to`:** resolve destination; `propose_command(..., params={})` if None else `params` with string or numeric `x_m`/`y_m` consistent with existing AutonomyCommand params typing; after Safety `allow`, call tick note **with** those coords when present |
| 5 | **`_sim_autonomy_tick_note`:** accept optional `x_m`/`y_m` (HOLD/LAND callers unchanged — omit). When GO_TO and both finite → `SimAutonomyParams(x_m=…, y_m=…)` → real sim note like HOLD/LAND. When GO_TO and missing → keep honest sin-destino note (may update wording to “sin destino / no conectado” but must not invent). Never crash |
| 6 | Bare `go to` / existing phrases after `armar` → still allow + sin-destino (T20 T1c stays or retargeted to same honesty). Armed `go to 1.0 2.0` (or equivalent prove-now) → allow + **Simulación** tick observed (not sin-destino). Metadata plug: if metadata has coords, same tick even on bare phrase text |
| 7 | HOLD/LAND/PATROL/disarmed regressions green. GO_TO Skill-first still green. ESC fence + tip-pin green |
| 8 | On ★ ACCEPT: mark [SD-GO_TO note](engineer_note_t20_goto_chat_sim_destination_debt.md) **CLOSED**; PRIORIDAD debt row closed. Version **`0.6.41`**; PLATFORM · CONNECTIONS (**no new C-xxx**) |
| 9 | Out: inventing defaults · copper · other verb sim ticks · voice · GPS driver · inventing `flight.go_to=available` |

---

## 1. Files

| Path | Change |
|---|---|
| `intelligence/assistant_task.py` | GO_TO classify accepts prove-now destination pattern; siblings refuse it |
| `core/orchestrator.py` | `_resolve_go_to_destination` · wire `_handle_vehicle_go_to` · extend `_sim_autonomy_tick_note` |
| `tests/test_assistant_chat_go_to_destination_b1.py` | **new** T1–T5 |
| `tests/test_assistant_chat_sim_copper_b1.py` | keep/adjust T1c bare sin-destino; optional pointer to new suite |
| `pyproject.toml` | `0.6.41` |
| Docs + SD-GO_TO note | short · note CLOSED only on ★ ACCEPT (this authorize leaves note “Buy AUTHORIZED”) |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | `armar` then bare `go to` → `vehicle_go_to` · allow · sin-destino / no invented tick coords |
| T2 | `armar` then `go to 1.0 2.0` (or locked prove-now form) → allow · message has `Simulación` tick · **not** sin-destino |
| T3 | metadata plug: bare phrase + `intent` path or orch-visible metadata with `go_to_x_m`/`go_to_y_m` → tick observed (prove connect seam). Prefer a unit test of `_resolve_go_to_destination` + one chat path if metadata can be injected honestly |
| T4 | HOLD/LAND still tick; PATROL no tick; disarmed GO_TO no tick; Skill-first `run_skill("skill.request_go_to")` still ok |
| T5 | No tip pins · no ESC fence break · `carga util` / other phrases unchanged |

---

## 3. Acceptance

- [x] Resolver seam + tick wire · bare honesty · prove-now tick · connect plug · `0.6.41` · SD-GO_TO closable on ★  
- [x] Cursor review (**PASS WITH NOTES** @ `1d7414f`)  
- [ ] Engineer ACCEPT · tag **`v0.6.41`** · note Status **CLOSED**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-chat-go-to-destination (T32)
Parent tip: T31 ★ ACCEPT CLOSED @ v0.6.40. Implement now → package 0.6.41.

IC: .jes/artifacts/implementation_contract_assistant_chat_go_to_destination_b1.md
DC: .jes/artifacts/design_contract_assistant_chat_go_to_destination_b0.md (★ CLOSED)
SD-GO_TO note: .jes/artifacts/engineer_note_t20_goto_chat_sim_destination_debt.md
  (mark CLOSED only on Engineer ★ ACCEPT — not in this impl commit)

Close SD-GO_TO — leave seam ready so real coords later only "connect":
- Add _resolve_go_to_destination(intent):
  1) metadata go_to_x_m + go_to_y_m if both finite (connect plug)
  2) else prove-now parse: "go to|goto|ir a|ve a" + two floats
  3) else None — NEVER invent 0,0/home
- try_request_go_to_task: bare VEHICLE_GO_TO_PHRASES OR prove-now pattern.
  Sibling try_* refuse destination-bearing GO_TO patterns.
- _handle_vehicle_go_to: resolve → propose_command params {} or {x_m,y_m};
  after allow, _sim_autonomy_tick_note(GO_TO, x_m=…, y_m=…) when present.
- _sim_autonomy_tick_note: optional x_m/y_m → SimAutonomyParams when both
  set; else keep sin-destino honesty for GO_TO. HOLD/LAND callers unchanged.
- Tests: bare go to → sin destino; "go to 1.0 2.0" armed → Simulación tick;
  metadata plug unit/chat; HOLD/LAND/PATROL/Skill-first regressions; tip-pin+ESC.
Skill-first run_skill("skill.request_go_to") stays first.
SD-GO_TO note CLOSED only at Engineer ★ ACCEPT. No tip pins. No ACCEPT claim.
Not copper · not voice · not GPS hardware · not other verb sim ticks.
```
