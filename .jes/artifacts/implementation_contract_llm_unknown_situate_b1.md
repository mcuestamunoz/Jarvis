# Implementation Contract — Unknown nonsense → situate (`B1-llm-unknown-situate`)

**Project:** Jarvis  
**Date:** 2026-10-18  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.8.7`** (CI-1 + CI-1b + CI-1c + this Buy)

**Status:** **IC READY** — Engineer Intent after CI-1c smoke: nonsense must **situate**, not dump analyze.  
**Parents:** [CI-1c review](implementation_review_llm_interpret_unknown_guard_b1.md) · [CI-0 DC](design_contract_continuity_interpreter_epoch_b0.md) locks 5–6 · tip **`v0.8.6`** · package **`0.8.7`** untagged  
**Type:** Ingress product fix — unclassified / meaningless turns re-orient the user with Continuity (`project_status`), 0 LLM.  
**Opens:** cola **CI-1d**. Package stays **`0.8.7`** (no bump). Tag **`v0.8.7`** only after Engineer ★ that includes this Buy.

**Not:** CI-2 Layer-2 LLM compose · CI-3 full ingress redesign · retiring `interpret` · changing Gemma default · G-03 test-Ollama isolation · G-02 keyword hygiene · T40 · Conversation Engine · inventing a new Continuity ranking.

---

## Why this Buy

Engineer smoke (2026-10-18) after CI-1c:

```text
User > hablar   → analyze dump (mismo bloque genérico)
User > gracias  → same analyze dump
User > explicame el margen → same dump (sin plan / sin eco — OK estructural)
```

CI-1c correctly stopped the create-project wizard. Engineer Intent:

> Si el user pregunta algo que no tiene ningún tipo de sentido, Jarvis debe **situar** al user — no narrar un analyze.

“Situar” = existing Continuity wall (`_handle_project_status` / `build_startup_context`): proyecto, situación, siguiente paso, readiness — **0 LLM**, same Layer 1 as `estado`.

Maps to CI-0 locks **5** (claim-before-LLM / existing contracts) and **6** (egress from already-computed Continuity fields).

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-llm-unknown-situate`** (CI-1d). Package remains **`0.8.7`**. Tag **`v0.8.7`** only after Engineer ★ covering CI-1b + CI-1c + this Buy |
| 2 | **Claim before interpret:** in `handle_user_text` IDLE residual path (before `llm_interface.interpret`), when **all** of: (a) resolver `intent == "unknown"`, (b) `_has_active_project()`, (c) **not** `is_explain_ask(user_input)` → return **`_handle_project_status()`** (+ `_track_turn`). **Do not call** `interpret` or `analyze` on that turn |
| 3 | **Explain-shaped unknown stays analyzable:** if `is_explain_ask(user_input)` (existing finite list in `goal_planner`), do **not** take lock 2 — keep today’s residual path so e.g. `qué es el margen` can still reach analyze. (`explicame el margen` already resolves `intent == "analyze"` and is out of this branch) |
| 4 | **CI-1c destination change:** where the CI-1c guard today routes guarded verbs to `_handle_analyze`, route instead to **`_handle_project_status`** when an active project is present (belt-and-suspenders if interpret still runs). `iterate` under unknown with **no** project: keep Bug 52 → analyze (or situate only if a project appears — no project ⇒ no Continuity wall; leave Bug 52 analyze / existing no-project create behaviour untouched) |
| 5 | **Reuse** `_handle_project_status` / `action == "project_status"` / `startup_context` — no new Continuity builder, no new ActionPolicy verb, no new CLI surface. Spoken path already treats `project_status` as a wall (`spoken_text_for_wall`) — **no spoken-map row required** unless a new printed lead-in string is added |
| 6 | **Optional** one deterministic Spanish lead line only if render needs it (e.g. short “No capté una orden clara — te sitúo:” before the wall). Prefer **no** extra line in v1; if added, it must be fixed copy (0 LLM) and the spoken-continuity map updated in the **same Buy** |
| 7 | Tests T1–T6 below; update CI cola + PRIORIDAD + state; **no** package bump |
| 8 | **Out** — CI-2 compose · delete `interpret` · widen `is_explain_ask` to “por qué…” (later) · G-03 · changing `DEFAULT_OLLAMA_MODEL` · craft/`world/` |

**Smoke ACCEPT (Engineer)** — project loaded, unset `JARVIS_OLLAMA_MODEL`:

```text
python -m jarvis.adapters.cli.main --chat
User > hablar
→ Continuity / project_status wall (situación + siguiente paso…), NOT analyze Insights/Trade-offs dump
→ NO create wizard
→ prefer: no new llm_logs row for this turn (0 interpret)
User > gracias
→ same: situate, not analyze dump
User > explicame el margen
→ still analyze path (not forced into bare "estado" only); no plan wall; no instruction echo
→ (quality of margin prose may still be weak — out of this Buy)
Also: nuevo / quiero diseñar… still opens create; poco margen still FN-022 plan
```

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/core/orchestrator.py` | Lock 2 early claim; lock 4 CI-1c guard → `project_status` when active project |
| `tests/test_llm_unknown_situate_b1.py` | **new** T1–T6 |
| `tests/test_llm_interpret_unknown_guard_b1.py` | Update expectations where CI-1c tests asserted `action == "analyze"` for `hablar`/`Gracias.` — now `project_status` (same Buy) |
| CI cola · PRIORIDAD · `engineering_state.json` | CI-1d Implemented awaiting review |
| `pyproject.toml` | **no version change** |

Do **not** touch ActionPolicy, Continuity ranking/builders (beyond calling existing `_handle_project_status`), `prompt_builder`, `DEFAULT_OLLAMA_MODEL`, voice adapters (unless map update for lock 6).

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | Closed project + `_RefuseLLM`: `hablar` / `Gracias.` / `hola` → `action == "project_status"`, has `startup_context`, mode IDLE, **0** interpret/analyze calls |
| T2 | Closed project + stub that would return `create_project` from interpret: if lock 2 fires first, interpret never called; if interpret somehow runs, still `project_status` / no wizard copy |
| T3 | `is_explain_ask` unknown (e.g. `qué es el margen`) still reaches analyze (stub analyze text), **not** forced to project_status-only |
| T4 | `explicame el margen` still `intent`/routing → analyze (stub), no plan prepend (CI-1b), not wizard |
| T5 | Deterministic create (`nuevo` / `quiero diseñar un dron`) still opens create wizard with `_RefuseLLM` |
| T6 | No-project + unknown + stub `create_project` still opens create wizard (CI-1c Engineer scope) |

No live Ollama. No tip pins.

---

## 3. Acceptance

- [ ] Engineer smoke §0  
- [ ] CI-1b / CI-1c probes still hold  
- [ ] Cursor review · Engineer ★ · tag **`v0.8.7`** (closes CI-1 + CI-1b + CI-1c + CI-1d)

---

## 4. Paste for Claude

```text
Implementation — B1-llm-unknown-situate (CI-1d)
Parent: Engineer Intent after CI-1c smoke — nonsense must situate, not analyze.
Package stays 0.8.7 (no bump). Tag v0.8.7 only after Engineer ★.

IC: .jes/artifacts/implementation_contract_llm_unknown_situate_b1.md
Parents: implementation_review_llm_interpret_unknown_guard_b1.md · CI-0 DC

GOAL: With an active project, resolver intent "unknown" and NOT
is_explain_ask → _handle_project_status (0 LLM), never interpret/analyze.
Change CI-1c guard destination from analyze → project_status when a
project is active. Keep explain-shaped unknown + "explicame el margen"
on analyze. Keep no-project create + deterministic create.

DO:
- orchestrator.py: early claim (lock 2) + CI-1c→situate (lock 4)
- tests/test_llm_unknown_situate_b1.py T1–T6
- update test_llm_interpret_unknown_guard_b1.py expectations for hablar/gracias
- cola CI / PRIORIDAD / state — CI-1d implemented awaiting review
- Implementation report. No ACCEPT. No pyproject bump.

NO: CI-2 compose · delete interpret · G-03 · widen explain list ·
ActionPolicy · Continuity ranking · T40
```

---

## 5. Cursor note

Claude may implement the full IC without per-edit approval. Stop if the Buy requires Continuity ranking changes, ActionPolicy changes, or CI-2 LLM compose.
