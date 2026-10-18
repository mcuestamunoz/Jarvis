# Implementation Report — Interpret unknown-intent wizard guard (`B1-llm-interpret-unknown-guard`, CI-1c)

**Project:** Jarvis
**Date:** 2026-10-16
**Implementer:** Claude Code (Engineer paste)
**Contract:** [IC](implementation_contract_llm_interpret_unknown_guard_b1.md)
**Parent:** [CI-INV-0 G-01](investigation_report_voice_llm_ci_audit_part_c_synthesis_b0.md) · [CI-INV-0 review](investigation_review_voice_llm_ci_audit_b0.md) · CI-1b PASS WITH NOTES · tip `v0.8.6` · tree `0.8.7` untagged
**Status:** **Implemented — awaiting Cursor review / Engineer ★.** No ACCEPT claimed.
**Package:** stays **`0.8.7`** (no bump).

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/core/orchestrator.py` (residual `interpret` branch, Bug 52 site) | Guard extended: `intent == "unknown"` and LLM verb `iterate` (unchanged, unconditional) **or** `create_project`/`calculate`/`simulate` **with an active project** → `_handle_analyze` + `_track_turn`, never `self.handle`. Comment cites CI-1c / CI-INV-0 G-01 and the Engineer scope decision. |
| `tests/test_llm_interpret_unknown_guard_b1.py` | **new** — T1–T5 + 2 scope tests |
| `tests/test_battery_component.py` | Two stub LLMs (`test_pure_numeric_in_idle_not_intercepted`, `test_low_completeness_in_idle_not_intercepted`) gain an `analyze` method — see §2.2 |
| cola CI · PRIORIDAD · `engineering_state.json` | CI-1c → Implemented / awaiting review |

**Untouched:** ActionPolicy, prompt schemas, `interpret` JSON shape, `invalid_llm_output` path, `DEFAULT_OLLAMA_MODEL`, Continuity, voice adapters, `goal_planner`, `pyproject.toml`. No new egress surface → spoken-continuity map not updated (the guarded turn renders through the existing `analyze` branch).

## 2. Decisions

1. **Scope = active project for the three new verbs (Engineer decision, 2026-10-16).** IC lock 2 lists all four verbs unconditionally; lock 6 and G-01 are about the active project. Applying lock 2 literally broke `tests/test_llm_integration.py::test_idle_falls_back_to_llm_when_local_resolution_has_no_match`, which pins *no project + unknown phrase + LLM `create_project` → create wizard*. Asked; Engineer chose **active project only**. That test is unchanged and passes. Consequence: with **no** project, Gemma's `hablar → create_project` still opens the create wizard (nothing to hijack). Pinned by `test_no_project_unknown_create_project_still_reaches_handle`.
2. **Two battery fixtures extended, assertions untouched.** Both create a drone project, send an unknown-intent input (`500`, `lipo`), and assert the input is **not** intercepted as a component description. Their stub LLM returned `simulate` from `interpret` and had no `analyze`; the guarded turn now calls `analyze` → `AttributeError`. Added a one-line `analyze` stub; the asserted behaviour (`not in intercepted`) is unchanged.
3. **Bug 52 kept byte-compatible:** `iterate` on unknown still routes to analyze with or without a project (T3 + `test_no_project_unknown_iterate_still_routes_to_analyze`).

## 3. Tests

| ID | What it proves | Path |
|---|---|---|
| T1 | Closed project, stub `interpret → create_project`, inputs `hablar` / `Gracias.` (asserted resolver intent `unknown`): `action == "analyze"`, no "Vamos a definir el proyecto paso a paso.", not interactive, session **IDLE** | residual interpret → guard |
| T2 | Same for `calculate` / `simulate`: analyze stub text returned, analyze called once, **persisted project byte-identical** before/after (`model_dump()` equality — verified separately that a real `calculate`/`simulate` changes `latest_results` + `history`, so the check discriminates), session IDLE | guard |
| T3 | `iterate` under unknown still → analyze (Bug 52) | guard |
| T4 | `nuevo` (`_handle_global_commands` NEW_PROJECT_WORDS) and `quiero diseñar un dron` (resolver `create_project` → `resolve_action_request`) still open the create wizard with `_RefuseLLM` (0 LLM) | deterministic create |
| T5 | `invalid_llm_output` stub → exact existing error dict, analyze not called, IDLE | error path |
| scope | no project: `create_project` still reaches `handle` (wizard); `iterate` still → analyze | Engineer decision §2.1 |

Executed: new file + `test_battery_component.py` + `test_llm_integration.py` → 67 passed. **Full suite: 4121 passed, 10 skipped** (1:27).

## 4. Remaining risks

- **Live smoke not run** (Engineer ACCEPT gate, IC §0): project loaded, `hablar` / `gracias` → no create wizard; `explicame el margen` → CI-1b criteria; intentional create still works.
- Guarded turns now go to `analyze`, i.e. an LLM narration of a nonsense line (spoken on `--voice-only`). Honest and non-mutating, but Gemma may answer `hablar` with a paragraph — CI-2/CI-4 territory (G-05), not this Buy.
- No-project asymmetry (§2.1) is intentional.
- G-03 still open: `run_chat`-level voice tests reach live Ollama; with this guard, their `hablar` turn on a fresh workspace (no project) still calls `interpret` live. Separate Buy.
