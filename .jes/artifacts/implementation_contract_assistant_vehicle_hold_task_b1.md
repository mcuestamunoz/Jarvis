# Implementation Contract — Assistant vehicle HOLD Task (`B1-assistant-vehicle-hold-task`)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.14`**

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-30) — Cursor review PASS; package/tag **`0.6.14` / `v0.6.14`**.  
**Parents:**
- [DC ★ CLOSED](design_contract_assistant_vehicle_hold_task_b0.md)
- [INV ★ CLOSED](investigation_report_assistant_vehicle_hold_task_b0.md)
- T5 ★ ACCEPT CLOSED @ **`v0.6.13`**
- C4 `propose_command` / `submit_command` · C17 `ArmedAllowlistSafetyGate`

**Type:** First vehicle Assistant Task — classify HOLD phrases → Task → orchestrator fulfill via autonomy surface + disarmed ArmedAllowlist.  
**Opens:** **`0.6.14` / `v0.6.14`** on ACCEPT.  
**Cola:** **T6**

**Not:** LAND/GO_TO · `arm()` on product path · `default_safety_gate` change · SoftwareCapabilitySafetyGate for flight · intelligence→FS import · voice · copper · Continuity ranking.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-vehicle-hold-task`** |
| 2 | `TASK_KIND_REQUEST_HOLD = "request_hold"` · `CAPABILITY_FLIGHT_HOLD = "flight.hold"` |
| 3 | `try_request_hold_task(intent) -> Task \| None` in `assistant_task.py` |
| 4 | `VEHICLE_HOLD_PHRASES` in `jarvis.config` — finite frozenset; exact match after `_normalize_for_continuity_match` (reuse helper or shared normalize). Minimum seed (normative, may add clear synonyms in same table): `hold`, `mantener`, `mantén`, `manten`, `quédate`, `quedate`, `hold position`, `mantener posicion`, `mantener posición` — all stored pre-normalized (strip/casefold/accent-strip form) so match is exact on normalized input |
| 5 | Precedence in `_handle_global_commands`: after Continuity defer branch, before `return None`: build Intent → `try_request_hold_task` → if Task, fulfill HOLD (do not fall through) |
| 6 | On classify match: membership `load_default().get_capability("flight.hold") is not None`; if missing → `None`. **Do not** call `SoftwareCapabilitySafetyGate` / `_software_safety_allows` |
| 7 | Metadata: set `task_kind=request_hold` only after membership pass |
| 8 | Seed `default_registry.json` **add** (keep existing caps/skills): capability `flight.hold` version `0.6.14`, `availability=not_implemented`, `provider_id=provider.flight_hold`, `health=unknown`; provider `provider.flight_hold` `kind=vehicle` `offered_capability_ids=["flight.hold"]`; skill `skill.request_hold` version `0.6.14` `required_capability_ids=["flight.hold"]` `availability=stub` |
| 9 | Fulfill (orchestrator): `gate = ArmedAllowlistSafetyGate()` — **do not arm**; `cmd = propose_command(AutonomyVerb.HOLD, intent_id=intent.id)`; `result = submit_command(cmd, gate)`; return `status=ok` (or error if you prefer — document), `action=global_command` (or `vehicle_hold`), `message=` human-readable Spanish including `result.safety.outcome`, `result.safety.reason`, `result.execution` — must not claim executed/flight |
| 10 | Fences AST: `assistant_task` still no `flight_software`/`vehicle_profiles`/`jarvis.core`; adapt T5/T2 cascade tests that assumed only two caps / two skills / only software providers — extend honestly without weakening no-dispatch |
| 11 | Version **`0.6.14`**; docs: intelligence README T6 · PLATFORM · CONNECTIONS extend (**no new C-xxx**) · PRIORIDAD · USER_GUIDE one line if explain guide mentions chat commands |
| 12 | LAND/GO_TO out |

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/config.py` | `VEHICLE_HOLD_PHRASES` |
| `src/jarvis/intelligence/assistant_task.py` | `try_request_hold_task` + exports |
| `src/jarvis/intelligence/__init__.py` / README | export/docs |
| `src/jarvis/core/orchestrator.py` | wire after defer; fulfill HOLD |
| `src/jarvis/capabilities/data/default_registry.json` | flight.hold + provider + skill |
| `tests/test_assistant_vehicle_hold_task_b1.py` | **new** T1–T8 |
| Cascade tests | caps/skills/provider-kind counts |
| `pyproject.toml` | `0.6.14` |
| Docs | §0.11 |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | Normalized HOLD phrase → Task with `required_capability_ids == ["flight.hold"]`, `task_kind=request_hold` |
| T2 | Non-hold craft line → `None` |
| T3 | Explain-shaped / Continuity phrase → HOLD try is `None` (precedence / no steal) |
| T4 | `handle_user_text` HOLD phrase → message contains Safety reject reason (`disarmed` or equivalent); `execution` not claimed executed; LLM not required (exploding LLM ok if path is global_command) |
| T5 | Seed: `flight.hold` is `not_implemented`; provider `vehicle`; skill stub present; software caps/skills from T2/T5 still present |
| T6 | AST: `assistant_task` does not import `flight_software` / `vehicle_profiles` / `jarvis.core` |
| T7 | `default_safety_gate()` still RejectAll; product fulfill uses disarmed ArmedAllowlist (unit or orchestrator test) |
| T8 | `pyproject` reads `0.6.14` |

Bump stale `0.6.13` checkpoints.

---

## 3. Acceptance

- [ ] Classify + membership + orchestrator fulfill via submit_command  
- [ ] Disarmed ArmedAllowlist · honest UX · no FS import in intelligence  
- [ ] Registry honesty · cascade adapted · tests T1–T8 · docs · `0.6.14`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.14`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-vehicle-hold-task (T6)

IC: .jes/artifacts/implementation_contract_assistant_vehicle_hold_task_b1.md
DC: .jes/artifacts/design_contract_assistant_vehicle_hold_task_b0.md (★ CLOSED)
INV: .jes/artifacts/investigation_report_assistant_vehicle_hold_task_b0.md (★ CLOSED)

Add VEHICLE_HOLD_PHRASES + try_request_hold_task in assistant_task
(Task request_hold → flight.hold). Membership only — NO SoftwareCapabilitySafetyGate.
intelligence must NOT import flight_software.
Wire orchestrator after Continuity defer: on Task → propose_command(HOLD) +
submit_command with fresh disarmed ArmedAllowlistSafetyGate (do not arm).
Honest message from safety outcome/reason/execution — never claim executed.
Seed registry: flight.hold not_implemented + vehicle provider + skill.request_hold stub.
Precedence: explain > defer > hold. Adapt cap/skill count cascade tests.
Tests T1–T8. Bump pyproject to 0.6.14. Docs + PRIORIDAD. Report.
Parent tip v0.6.13. No ACCEPT claim.
```
