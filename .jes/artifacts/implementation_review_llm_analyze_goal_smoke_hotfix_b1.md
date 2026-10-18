# Implementation Review — Analyze / goal smoke hotfix (`B1-llm-analyze-goal-smoke-hotfix`, CI-1b)

**Project:** Jarvis  
**Date:** 2026-10-16  
**Reviewer:** Cursor (independent — not implementer)  
**Contract:** [IC](implementation_contract_llm_analyze_goal_smoke_hotfix_b1.md) · [report](implementation_report_llm_analyze_goal_smoke_hotfix_b1.md)  
**Package under review:** **`0.8.7`** (uncommitted / untagged)  
**Parent:** tip **`v0.8.6`** · [CI-1 review REJECT ACCEPT](implementation_review_llm_gemma4_default_model_b1.md) · [CI-0 DC](design_contract_continuity_interpreter_epoch_b0.md)

**Verdict:** **PASS WITH NOTES** (code vs IC) — **no ACCEPT**. Tag **`v0.8.7` not authorized** until Engineer re-smoke ★.

**Process note:** Claude implemented; Cursor did not implement this Buy. Same-session self-PASS is not review of record. Parallel **CI-INV-0** audit is out of this review’s scope.

---

## 1. Scope check vs IC

| Lock / IC item | Evidence | Result |
|---|---|---|
| 1 · Buy · package stays `0.8.7` · no tag | `pyproject.toml` `0.8.7`; no `v0.8.7` tag; report no ACCEPT | **Pass** |
| 2 · Remove bare `"margen"`; keep longer phrases | `goal_planner._GOAL_KEYWORDS` — bare gone; `margen de seguridad` / `poco margen` / `margen bajo` / `margen justo` / `safety margin` kept; **seven direction phrases added** (see §2) | **Pass** |
| 3 · Analyze plan prepend gate | `_handle_analyze`: `if goal_key and not is_explain_ask(user_input)`; finite whole-word regex on `_normalize()` | **Pass** |
| 4 · Defense in depth (2+3) | Both landed | **Pass** |
| 5 · Analyze prompt harden + drop prefill | System no-echo lines; no assistant `"En resumen,"`; interpret untouched | **Pass** |
| 6 · Optional post-filter | Not added; T6 skipped with IC-allowed reason | **Pass** |
| 7 · Tests + status docs · no bump | New `tests/test_llm_analyze_goal_smoke_hotfix_b1.py` T1–T6; cola/PRIORIDAD/state/CI-1 note/report | **Pass** |
| 8 · Out of scope | No ActionPolicy / Continuity / voice / DEFAULT change / interpret retire; FN-022 IDLE path preserved (T4) | **Pass** |
| Tests T1–T6 | Present; T6 skip documented | **Pass** |
| Report honesty | Decisions §2, risks, suite 4111/10 skip, no ACCEPT | **Pass** |

---

## 2. Judgment calls — **accepted**

| # | Choice | Review |
|---|---|---|
| 1 | Extra keywords: `mas margen`, `mejorar (el) margen`, `aumentar (el) margen`, `subir (el) margen` | **Accept.** Lock 2 removed bare `margen`; lock 8 requires FN-022 real intentions keep their plan. `"Mejorar el margen"` would otherwise fall through. Direction-bearing phrases are the right grain — not reintroducing bare `margen`. |
| 2 | Rewrite `test_goal_planner`: `"el margen es bajo"` → `None` | **Accept.** Explicit consequence of lock 2 (substring was bare `margen`). `"margen bajo"` / `"mejorar el margen"` still map. Documented residual: free word-order “el margen es bajo” goes to analyze. |
| 3 | Gate = `is_explain_ask`, not `is_engineering_intention` | **Accept.** IC lock 3 allows “or equivalent”; minimum explain-family list is met. IDLE FN-022 path correctly left ungated. |
| 4 | No post-filter | **Accept.** Lock 6 optional; T5 covers prompt-only; live Gemma echo is Engineer smoke. |

---

## 3. Notes (non-blocking)

| ID | Severity | Note |
|---|---|---|
| **N1** | Info / **ACCEPT gate** | Live smoke still required (IC §3): `unset JARVIS_OLLAMA_MODEL` · `--chat` · `explicame el margen` → no plan wall · no “Reglas clave” / instruction echo · on-topic margin answer. Also: `poco margen` / `aumentar empuje` still get FN-022 plan. |
| **N2** | Info | Bare `"empuje"` / `"thrust"` / `"estabilidad"` still make `detect_goal` hit on explain asks (e.g. `qué es el empuje`). Lock 3 gate blocks plan prepend (T3 covers). Same class as old bare `margen` — not in this Buy; optional later keyword hygiene. |
| **N3** | Info | `is_explain_ask` finite list; “por qué…” / “en qué consiste…” not gated. Only matters when a goal keyword also hits. |
| **N4** | Info | Without `"En resumen,"` prefill, Spanish relies on system + user-turn label — watch English replies in smoke. |
| **N5** | Info | Full suite **4111 passed, 10 skipped** trusted from implementer (extra skip = T6). Reviewer re-ran targeted: `test_llm_analyze_goal_smoke_hotfix_b1` + `test_goal_planner` + `test_fn022_engineering_intent` → **63 passed, 1 skipped**. |
| **Carry** | — | After ★: closes CI-1 + CI-1b · tag `v0.8.7` · then CI-2 egress (subject to CI-INV-0 findings). T40 Parked. |

---

## 4. Tests executed by reviewer

```text
python -m pytest -q tests/test_llm_analyze_goal_smoke_hotfix_b1.py \
  tests/test_goal_planner.py tests/test_fn022_engineering_intent.py
→ 63 passed, 1 skipped in 0.24s
```

Quick asserts: `detect_goal("explicame el margen") is None` · `is_explain_ask(...)` True · `detect_goal("Mejorar el margen") == mejorar_estabilidad` · `detect_goal("el margen es bajo") is None`.

---

## 5. Engineer ACCEPT status

**Pending re-smoke.** Code vs IC is PASS WITH NOTES. Pytest cannot prove Gemma stopped echoing instructions.

```text
unset JARVIS_OLLAMA_MODEL
python -m jarvis.adapters.cli.main --chat
User > explicame el margen
→ NO "Plan estratégico — Mejorar estabilidad"
→ NO instruction echo ("Reglas clave" / "Estoy listo…")
→ on-topic margin / honest "no modelado"
Also: poco margen / aumentar empuje → FN-022 plan
```

On ★: tag **`v0.8.7`** (closes CI-1 + CI-1b). If echo persists → lock 6 post-filter Buy (narrow), not CI-2.
