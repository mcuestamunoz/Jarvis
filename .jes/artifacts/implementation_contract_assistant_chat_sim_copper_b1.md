# Implementation Contract — Assistant chat → sim copper (`B1-assistant-chat-sim-copper`)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED after T19 ★  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.29`**

**Status:** ★ **AUTHORIZED — Claude implement now** (T19 ★ @ `v0.6.28`).  
**Parents:** [DC ★ CLOSED](design_contract_assistant_chat_sim_copper_b0.md) · T14 ★ · T19 ★ @ **`v0.6.28`** · C40 sim executor  
**Type:** Chat allow → **sim** tick for HOLD/LAND/GO_TO only.  
**Opens:** **`0.6.29` / `v0.6.29`**. **Cola:** **T20**

**Not:** live ESC/GPIO · TAKEOFF/RH/FOLLOW/PATROL sim support · CHARGE · Skills · tip pins · claiming flight.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-chat-sim-copper`** |
| 2 | Orchestrator owns one process-scoped `SimAutonomyExecutor` (lazy) for the chat path — **not** wired into `submit_command` unless IC choice (b) below |
| 3 | **Preferred path (a):** keep `submit_command` byte-stable (`allow` → `execution=not_implemented`). After allow for HOLD/LAND/GO_TO, orchestrator calls `sim.tick(verb, params, dt_s=…)` and includes sim tick result in the user message. Message must say **simulación** / not live copper |
| 4 | TAKEOFF/RETURN_HOME/FOLLOW/PATROL after allow: **no** tick; message remains allow + not_implemented / sim unsupported |
| 5 | Disarmed: no tick |
| 6 | Never `SimulatedEscSink` / ESC import from orchestrator chat path (T16 fence stays green) |
| 7 | Tests: armed HOLD → tick observed; armed PATROL → no tick; disarmed → no tick; ESC fence still green |
| 8 | Version **`0.6.29`**; PLATFORM + CONNECTIONS honesty (**no new C-xxx** unless a real new edge is unavoidable — prefer no new C-xxx) |
| 9 | Out: CHARGE · Skills · tip pins · live copper |

---

## 1. Files

| Path | Change |
|---|---|
| `core/orchestrator.py` | sim executor lazy + tick after allow for HOLD/LAND/GO_TO fulfills |
| `tests/test_assistant_chat_sim_copper_b1.py` | **new** |
| vehicle suites | retarget messages if they assert exact strings |
| `pyproject.toml` | `0.6.29` |
| Docs | honesty |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | `armar` + `hold` → Safety allow + sim tick side-effect (state/message) |
| T2 | `armar` + `patrol` → allow, **no** tick |
| T3 | disarmed `hold` → reject, no tick |
| T4 | ESC fence / no SimulatedEscSink import in orch still holds |
| T5 | No tip pins |

---

## 3. Acceptance

- [ ] HOLD/LAND/GO_TO sim tick after allow · others no tick · ESC fence · `0.6.29`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.29`**

---

## 4. Paste for Claude (AUTHORIZED — T19 ★ done)

```text
★ AUTHORIZED implementation — B1-assistant-chat-sim-copper (T20)
Parent tip: T19 ★ ACCEPT CLOSED @ v0.6.28. Implement now → package 0.6.29.

IC: .jes/artifacts/implementation_contract_assistant_chat_sim_copper_b1.md
DC: .jes/artifacts/design_contract_assistant_chat_sim_copper_b0.md (★ CLOSED)

After Safety allow on chat HOLD/LAND/GO_TO, run SimAutonomyExecutor.tick
(orchestrator-owned, lazy). Prefer leaving submit_command unchanged.
TAKEOFF/RH/FOLLOW/PATROL: allow but no tick. Never ESC/copper flight claim.
Bump 0.6.29. No tip pins. No ACCEPT claim. Skills out.
Not ESC live / not sim for TAKEOFF/RH/FOLLOW/PATROL (those stay parked).
```
