# Implementation Contract — Orchestrator fulfill docstring honesty (`B1-orchestrator-fulfill-docstring-honesty`)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.27`**

**Status:** **★ ACCEPT CLOSED** (Engineer 2026-10-01) — Cursor review **PASS WITH NOTES** · tag **`v0.6.27`**.  
**Parents:** [DC ★ CLOSED](design_contract_orchestrator_fulfill_docstring_honesty_b0.md) · T14 ★ @ **`v0.6.25`** · tip **`v0.6.26`**  
**Type:** Comment/docstring honesty only.  
**Opens:** **`0.6.27` / `v0.6.27`**. **Cola:** **T18** (first in coherence order).

**Not:** behavior · CHARGE · copper · Skills · tip-version pins · phrase tables · Safety frozenset.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-orchestrator-fulfill-docstring-honesty`** |
| 2 | In `src/jarvis/core/orchestrator.py`: rewrite stale intercept comments + `_handle_vehicle_takeoff` / `_return_home` / `_follow` / `_patrol` docstrings so they state T14 truth — when armed, those verbs → Safety `allow` / execution `not_implemented` (not `verb_not_allowed`) |
| 3 | Optional: fix any one-liner in `assistant_task.py` still claiming FOLLOW/PATROL → `verb_not_allowed` after arm |
| 4 | **Zero** runtime behavior change — no logic edits beyond comments/docstrings |
| 5 | Tests: assert no stale `verb_not_allowed when armed` / `Allow-list still excludes` substrings remain in those fulfill docstrings (or a small honesty test grepping the four methods). Do **not** add tip-version pins |
| 6 | Version **`0.6.27`**; PRIORIDAD · CONNECTIONS one line if needed (**no new C-xxx**) |
| 7 | Out: CHARGE · copper · Skills runtime |

---

## 1. Files

| Path | Change |
|---|---|
| `src/jarvis/core/orchestrator.py` | docstring/comment honesty |
| `src/jarvis/intelligence/assistant_task.py` | optional stale note |
| `tests/test_orchestrator_fulfill_docstring_honesty_b1.py` | **new** |
| `pyproject.toml` | `0.6.27` |
| Docs / PRIORIDAD | short |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | Four fulfill methods' docstrings do not claim allow-list excludes TAKEOFF/RH/FOLLOW/PATROL |
| T2 | Armed E2E still `allow`/`not_implemented` for those verbs (smoke reuse or 1 short call) |
| T3 | No tip-version pin tests |

---

## 3. Acceptance

- [x] Stale comments gone · behavior unchanged · `0.6.27`  
- [x] Cursor review **PASS WITH NOTES** @ `16678d6`  
- [ ] Engineer ACCEPT · tag **`v0.6.27`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-orchestrator-fulfill-docstring-honesty (T18)

IC: .jes/artifacts/implementation_contract_orchestrator_fulfill_docstring_honesty_b1.md
DC: .jes/artifacts/design_contract_orchestrator_fulfill_docstring_honesty_b0.md (★ CLOSED)
Parent tip: T17 ★ ACCEPT CLOSED @ v0.6.26

Comment/docstring only. Fix orchestrator fulfill/intercept notes that still
say TAKEOFF/RETURN_HOME/FOLLOW/PATROL stay verb_not_allowed when armed.
T14 truth: armed → allow/not_implemented for all seven chat verbs.
Optional assistant_task one-liner. No behavior change. No tip pins.
Bump 0.6.27. Docs + PRIORIDAD. Report. No ACCEPT claim.
```
