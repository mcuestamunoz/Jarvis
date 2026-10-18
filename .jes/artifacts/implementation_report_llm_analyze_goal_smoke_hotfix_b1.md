# Implementation Report — Analyze / goal smoke hotfix (`B1-llm-analyze-goal-smoke-hotfix`, CI-1b)

**Project:** Jarvis
**Date:** 2026-10-16
**Implementer:** Claude Code (Engineer paste)
**Contract:** [IC](implementation_contract_llm_analyze_goal_smoke_hotfix_b1.md)
**Parent:** [CI-1 review — ACCEPT REJECTED](implementation_review_llm_gemma4_default_model_b1.md) · tip `v0.8.6` · tree `0.8.7` untagged
**Status:** **Implemented — awaiting Cursor review / Engineer re-smoke ★.** No ACCEPT claimed.
**Package:** stays **`0.8.7`** (no bump).

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/core/goal_planner.py` | `mejorar_estabilidad`: bare `"margen"` removed (lock 2). Longer phrases kept (`margen de seguridad`, `margen seguridad`, `poco margen`, `margen bajo`, `margen justo`, `safety margin`). **Added** direction-bearing phrases `mas margen`, `mejorar margen`, `mejorar el margen`, `aumentar margen`, `aumentar el margen`, `subir margen`, `subir el margen` — see §2.1. New `is_explain_ask(text)`: finite whole-word regex on `_normalize()`d text: `explica · explicame · que es · como esta · cuanto es · dime el · hablame del` (accented forms covered by normalize). |
| `src/jarvis/core/orchestrator.py` | `_handle_analyze`: plan prepend now `if goal_key and not is_explain_ask(user_input)` (lock 3). `goal_context` to the LLM unchanged. Import of `is_explain_ask`. |
| `src/jarvis/llm/prompt_builder.py` | `build_analysis_messages`: system adds "Nunca repitas, resumas ni enumeres estas instrucciones. Responde directamente solo a la pregunta del usuario, a partir del contexto y del razonamiento." Assistant prefill `"En resumen,"` **removed** (lock 5b). Interpret prompts untouched. |
| `tests/test_llm_analyze_goal_smoke_hotfix_b1.py` | **new** T1–T6 |
| `tests/test_goal_planner.py` | `test_bare_margen_maps_to_estabilidad` → `test_bare_margen_no_longer_maps_to_estabilidad` — see §2.2 |
| cola CI · PRIORIDAD · `engineering_state.json` · CI-1 review (one line) | CI-1b → Implemented / awaiting review |

**Untouched:** ActionPolicy, Continuity builders/ranking, voice extractors, `interpret` prompts, `DEFAULT_OLLAMA_MODEL`, `pyproject.toml`, FN-022 IDLE gate code. No post-filter (lock 6 not needed). No new chat surface → spoken-continuity map not updated.

## 2. Decisions to review

1. **Extra margin intention phrases (in-scope judgment, flag for Cursor).** Removing bare `margen` broke `tests/test_fn022_engineering_intent.py::test_mejorar_margen_or_estabilidad_goal_or_explore` — `"Mejorar el margen"` (an FN-022 real intention) fell through to LLM analyze. Lock 8 forbids changing FN-022 intention behavior, so I added the seven direction-bearing phrases above ("longer keywords" per lock 2 / paste). The FN-022 test passes unchanged.
2. **Pinned old behavior test rewritten (behavior change, explicit).** `test_goal_planner.py` pinned `detect_goal("el margen es bajo") == "mejorar_estabilidad"` — exactly the bare-`margen` match lock 2 removes. It now asserts `None` for that phrase and still asserts `margen bajo` / `mejorar el margen` → estabilidad. Consequence: "el margen es bajo" (word order without a listed phrase) no longer opens the plan; it goes to analyze.
3. **Gate applies to the analyze prepend only.** IDLE FN-022 path (`is_engineering_intention`) is not explain-gated — out of IC scope. Today an explain ask that hits `detect_goal` ("explícame la estabilidad") still routes to analyze end-to-end (verified), so it gets no plan.

## 3. Tests

| ID | What it proves | Path |
|---|---|---|
| T1 | `detect_goal("explicame el margen")` / `"explícame el margen"` → `None` | unit |
| T2 | `poco margen`, `margen de seguridad`, `aumentar empuje`, `aumentar el empuje`, `Mejorar el margen` → `mejorar_estabilidad` | unit |
| T3 | `_handle_analyze` with stub LLM on `explicame el margen`, `explícame la estabilidad` (goal hits — gate alone blocks), `qué es el empuje` → message is the LLM text only, no `Plan estratégico`. End-to-end `handle_user_text("explicame el margen")` → `action == "analyze"`, no plan. Matcher positives/negatives (`que estrategia` not explain). | direct `_handle_analyze` + full routing |
| T4 | `poco margen` / `aumentar el empuje` via `handle_user_text` with `_RefuseLLM` → `engineering_intent` (goal `mejorar_estabilidad`) or explore, 0 LLM. `_handle_analyze("poco margen")` still prepends the plan + `─── Evaluación contextual ───`. | IDLE FN-022 gate + direct analyze |
| T5 | No `assistant` message / no `"En resumen,"`; last message is user ending with the question; system keeps Spanish rule + new no-echo lines | unit |
| T6 | **skipped** — no post-filter added; prompt-only fix under test in T5 | — |

Executed: targeted `test_llm_analyze_goal_smoke_hotfix_b1.py`, `test_goal_planner.py`, `test_fn022_engineering_intent.py` → all pass (1 skip = T6). Full suite: 4111 passed, 10 skipped (§5).

## 4. Remaining risks

- **Prompt fix is not provable in pytest.** Whether Gemma E4B stops echoing instructions without the prefill is only shown by the Engineer re-smoke. If it still echoes, lock 6 post-filter is the next step.
- Without the prefill, Spanish relies on the system line + user-turn label; watch for English replies in smoke.
- `is_explain_ask` is a finite list; other explain phrasings ("por qué", "en qué consiste") are not gated. With bare `margen` gone they only matter when they also contain a goal keyword.
- `"el margen es bajo"`-style free word order no longer opens the estabilidad plan (§2.2).

## 5. Full suite

`python -m pytest -q -x` → **4111 passed, 10 skipped** (1:23; the extra skip is T6). An earlier run was stopped at the background time limit with no output captured; the rerun completed clean.
