# Implementation Report — Unknown nonsense → situate (`B1-llm-unknown-situate`, CI-1d)

**Project:** Jarvis
**Date:** 2026-10-18
**Implementer:** Claude Code (Engineer paste)
**Contract:** [IC](implementation_contract_llm_unknown_situate_b1.md)
**Parent:** [CI-1c review](implementation_review_llm_interpret_unknown_guard_b1.md) · [CI-0 DC](design_contract_continuity_interpreter_epoch_b0.md) locks 5–6 · tip `v0.8.6` · tree `0.8.7` untagged
**Status:** **Implemented — awaiting Cursor review / Engineer ★.** No ACCEPT claimed.
**Package:** stays **`0.8.7`** (no bump).

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/core/orchestrator.py` — IDLE residual path, right before `llm_interface.interpret` | **Lock 2 early claim:** `intent == "unknown"` and `_has_active_project()` and not `is_explain_ask(user_input)` → `_handle_project_status()` + `_track_turn`. `interpret` and `analyze` are never called on that turn. |
| same file — CI-1c guard | **Lock 4 destination:** guarded verb + active project + not explain ask → `_handle_project_status()`; otherwise (explain-shaped unknown, or no-project `iterate`) → `_handle_analyze` as before. |
| `tests/test_llm_unknown_situate_b1.py` | **new** — T1–T6 + backstop + FN-022 regression |
| `tests/test_llm_interpret_unknown_guard_b1.py` | CI-1c expectations updated (§3) |
| `.jes/artifacts/engineer_note_chat_spoken_continuity_map.md` | `project_status` row trigger cell + tip line note the new trigger — no new row, no new surface (§2.2) |
| cola CI · PRIORIDAD · `engineering_state.json` | CI-1d → Implemented / awaiting review |

**Untouched:** ActionPolicy, prompts, `DEFAULT_OLLAMA_MODEL`, Continuity builders/ranking (only the existing `_handle_project_status` is called), `is_explain_ask` list, voice adapters, `pyproject.toml`. No lead-in line added (lock 6 "prefer no extra line").

## 2. Decisions

1. **Lock 3 vs lock 4 reconciled (flag for Cursor).** Explain-shaped unknowns (`qué es el margen`) are not claimed by lock 2 and still run `interpret`; Gemma typically returns a verb, which hits the CI-1c guard. Applying lock 4 literally ("route to `project_status` when an active project is present") would send them to `project_status` too and make lock 3 / T3 ("still reaches analyze") unreachable. The guard therefore situates only when the turn is **not** an explain ask; explain-shaped turns keep analyze. With the early claim in place, the guard's situate branch is a backstop that fires only if the claim is bypassed (proven by `test_t2_backstop_situates_if_interpret_runs`).
2. **Spoken map.** No new printed surface (the turn renders and speaks exactly like `estado` — wall printed, brief spoken via `spoken_text_for_wall`). Lock 5 says no row is required; I still added the new trigger to the existing `project_status` row so the map's trigger column is not stale (CLAUDE.md norm).
3. **Scope of "unknown".** Any resolver-`unknown`, non-explain line on an active project now situates, not just nonsense words — e.g. `500`, `lipo`, `sistema` (all resolver `unknown`). The two battery tests that send `500`/`lipo` only assert "not intercepted as a component" and still pass. FN-022 phrases (`poco margen`, also resolver `unknown`) are claimed earlier by the FN-022 gate and keep their plan.

## 3. Tests

| ID | What it proves |
|---|---|
| T1 | `hablar` / `Gracias.` / `hola` (asserted resolver `unknown`) on a closed project with `_RefuseLLM` → `project_status`, `startup_context.has_project`, IDLE — any LLM call would raise |
| T2 | Stub `interpret → create_project`: never consulted (`interpret_calls == []`), no wizard copy. **Backstop:** with the early claim forced off (`is_explain_ask` patched True→False), interpret runs once and the guard still returns `project_status`, no analyze, IDLE |
| T3 | `qué es el margen` (resolver `unknown`, explain-shaped) + stub `calculate` → analyze stub text |
| T4 | `explicame el margen` (resolver `analyze`) → analyze, no `Plan estratégico`, no interpret, IDLE |
| T5 | `nuevo` / `quiero diseñar un dron` with `_RefuseLLM` → create wizard |
| T6 | No project + `hablar` + stub `create_project` → create wizard (CI-1c Engineer scope) |
| extra | `poco margen` still FN-022 (`engineering_intent`/explore), 0 LLM |

**CI-1c file updates:** T1 (`hablar`/`Gracias.`) now asserts `project_status` with interpret **not** called; T2/T3/T5 switch input to the explain-shaped unknown `qué es el margen` so they keep exercising the guard (analyze for `calculate`/`simulate`/`iterate`) and the unchanged `invalid_llm_output` path. Scope tests (no project) unchanged.

Executed: both files → 21 passed. **Full suite: 4132 passed, 10 skipped** (1:15).

## 4. Remaining risks

- **Live smoke not run** (IC §0): `hablar`/`gracias` → wall, no new `llm_logs` row; `explicame el margen` → analyze; `nuevo`/`quiero diseñar…` → create; `poco margen` → plan.
- Broad claim (§2.3): a real but unclassified request on an active project now gets the Continuity wall instead of an LLM turn. Checked resolver-`unknown` + non-explain + no FN-022 goal: `Que necesito para hacer una curva de consumo de los motores` (from live `llm_logs`), `añadir un motor` (from logs), `4x 2306 2400KV 50W` (from logs), `cuanto pesa`. Before CI-1c these reached `interpret` (Gemma mostly → `create_project`); after CI-1c → analyze; now → wall. That is the IC's intended trade (widening ingress is CI-3 / lock 8), but the Engineer should probe one of these in smoke. (Phrases with an analyze verb — `por qué…`, `hazme un informe` — resolve `analyze` and are unaffected.)
- Explain-shaped unknowns still make a (wasted) `interpret` call before analyze — unchanged behaviour, out of scope.
- G-03 still open (voice `run_chat` tests reach live Ollama on a fresh workspace with no project — not affected by this claim).
