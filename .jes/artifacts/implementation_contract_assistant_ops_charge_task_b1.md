# Implementation Contract — Assistant ops CHARGE Task (`B1-assistant-ops-charge-task`)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED after T18 ★ (implement in order)  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.28`**

**Status:** **Implemented** (Claude Code) — Cursor review **PASS WITH NOTES** → await Engineer ★ ACCEPT → tag **`v0.6.28`**.  
**Parents:** [DC ★ CLOSED](design_contract_assistant_ops_charge_task_b0.md) · T14 ★ · T18 ★ @ **`v0.6.27`**  
**Type:** First ops Task — CHARGE ≠ `AutonomyVerb`.  
**Opens:** **`0.6.28` / `v0.6.28`**. **Cola:** **T19**

**Not:** copper · AutonomyVerb.CHARGE · allow-list · Skills runtime · tip pins · payload “carga útil” · real battery charge hardware.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-ops-charge-task`** |
| 2 | `TASK_KIND_REQUEST_CHARGE = "request_charge"` · `CAPABILITY_OPS_CHARGE = "ops.charge"` |
| 3 | `try_request_charge_task(intent) -> Task \| None` |
| 4 | `OPS_CHARGE_PHRASES` — finite, pre-normalized. Min: `charge`, `cargar`, `cargar bateria` (+ accent normalize). Exact match only |
| 5 | Refuse explain / Continuity / ARM/DISARM / seven vehicle phrases / payload lines (`carga util`, `aumentar la carga`, `carga util kg`, …) |
| 6 | Membership only; **no** ArmedAllowlist; **no** SoftwareCapabilitySafetyGate |
| 7 | Registry add: `ops.charge` v`0.6.28` `not_implemented` · `provider.ops_charge` **`kind=device`** · `skill.request_charge` stub. Cascade → **11** caps / **12** skills |
| 8 | Fulfill `_handle_ops_charge`: **no** `propose_command`/`AutonomyVerb`/`SimAutonomyExecutor`. Honest Spanish — charge ops not implemented. `action=ops_charge` |
| 9 | Wire after PATROL, before `return None` |
| 10 | Retarget CHARGE probes that assumed raw `autonomy:CHARGE:…` if any product path now classifies `charge` as Task — gate tests that inject `autonomy:CHARGE:` may stay |
| 11 | Version **`0.6.28`**; docs; **no tip pins**; **no new C-xxx** (extend CONNECTIONS note) |
| 12 | Out: copper · Skills · AutonomyVerb enum edit |

---

## 1. Files

| Path | Change |
|---|---|
| `config.py` | `OPS_CHARGE_PHRASES` |
| `intelligence/assistant_task.py` | `try_request_charge_task` + refusals |
| `core/orchestrator.py` | wire + `_handle_ops_charge` |
| `capabilities/data/default_registry.json` | ops.charge row |
| `tests/test_assistant_ops_charge_task_b1.py` | **new** |
| cascade count tests | 11/12 |
| `pyproject.toml` | `0.6.28` |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | `charge`/`cargar bateria` → Task `ops.charge` |
| T2 | `carga util` / `aumentar la carga` → `None` |
| T3 | Vehicle/arm/explain phrases → charge try `None` |
| T4 | `handle_user_text("charge")` → honest not-implemented; never `executed`; never AutonomyVerb |
| T5 | Seed: `ops.charge` device+not_implemented; cascade 11/12 |
| T6 | AST: assistant_task still no FS import |
| T7 | No tip-version pins |

---

## 3. Acceptance

- [ ] Classify + fulfill honesty · no AutonomyVerb · cascade 11/12 · `0.6.28`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.28`**

---

## 4. Paste for Claude (AUTHORIZED — T18 ★ done)

```text
★ AUTHORIZED implementation — B1-assistant-ops-charge-task (T19)
Parent tip: T18 ★ ACCEPT CLOSED @ v0.6.27. Implement now → package 0.6.28.

IC: .jes/artifacts/implementation_contract_assistant_ops_charge_task_b1.md
DC: .jes/artifacts/design_contract_assistant_ops_charge_task_b0.md (★ CLOSED)

CHARGE ≠ AutonomyVerb. Add OPS_CHARGE_PHRASES + try_request_charge_task
→ Task(request_charge, ops.charge). Membership only. Provider kind=device,
availability=not_implemented. Fulfill without propose_command/sim.
Refuse payload "carga útil" lines. Wire after PATROL. Cascade 11/12.
Bump 0.6.28. No tip pins. No ACCEPT claim. Copper / Skills out.
Not real battery hardware (that stays parked until assembly).
```
