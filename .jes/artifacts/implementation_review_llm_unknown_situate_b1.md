# Implementation Review — Unknown nonsense → situate (`B1-llm-unknown-situate`, CI-1d)

**Project:** Jarvis  
**Date:** 2026-10-18  
**Reviewer:** Cursor (independent — not implementer)  
**Contract:** [IC](implementation_contract_llm_unknown_situate_b1.md) · [report](implementation_report_llm_unknown_situate_b1.md)  
**Package under review:** **`0.8.7`** (uncommitted / untagged)  
**Parent:** tip **`v0.8.6`** · [CI-1c review](implementation_review_llm_interpret_unknown_guard_b1.md) · [CI-0 DC](design_contract_continuity_interpreter_epoch_b0.md)

**Verdict:** **PASS WITH NOTES** (code vs IC) — **no ACCEPT**. Tag **`v0.8.7` not authorized** until Engineer live smoke ★ (CI-1b + CI-1c + CI-1d).

**Process note:** Claude implemented; Cursor did not implement this Buy.

---

## 1. Scope check vs IC

| Lock / IC item | Evidence | Result |
|---|---|---|
| 1 · Buy · `0.8.7` · no tag | `pyproject.toml` `0.8.7`; no ACCEPT | **Pass** |
| 2 · Early claim unknown + project + not explain → `project_status`, 0 LLM | `orchestrator.py:2576-2587` | **Pass** |
| 3 · Explain-shaped unknown stays analyzable | Guard keeps analyze when `is_explain_ask`; T3 | **Pass** |
| 4 · CI-1c destination → situate (active project) | `orchestrator.py:2617-2623` + not-explain gate | **Pass with N1** (§2) |
| 5 · Reuse `_handle_project_status` | same action/startup_context; no new builder | **Pass** |
| 6 · Optional lead-in | none added | **Pass** |
| 7 · Tests + status docs · no bump | new file + CI-1c file updates + cola/PRIORIDAD/state | **Pass** |
| 8 · Out of scope | ActionPolicy / DEFAULT / Continuity ranking untouched | **Pass** |
| Spoken map | existing `project_status` row trigger updated (no new surface) | **Pass** (CLAUDE.md hygiene) |
| Report honesty | lock 3↔4 + broad-claim risk disclosed | **Pass** |

---

## 2. Judgment calls — **accepted**

| # | Choice | Review |
|---|---|---|
| 1 | Guard situates only when **not** `is_explain_ask` | **Accept.** Literal lock 4 vs lock 3 conflict is real; without the gate, `qué es el margen` could never reach analyze. Preserves T3; backstop test proves situate when early claim is bypassed. |
| 2 | Spoken-map trigger cell update (no new row) | **Accept.** Same wall as `estado`; inventory honesty. |
| 3 | Broad `unknown` claim (not only nonsense words) | **Accept as IC trade** — lock 2 is written that way. Smoke should probe one real unclassified line (report §4). Ingress tightening = CI-3 later. |

---

## 3. Notes (non-blocking)

| ID | Severity | Note |
|---|---|---|
| **N1** | Info | Document the lock 3/4 reconciliation in the IC comment already in code — sufficient. |
| **N2** | Info / **ACCEPT gate** | Live smoke (IC §0): `hablar`/`gracias` → Continuity wall, **no** new `llm_logs` row; `explicame el margen` → analyze (no plan / no echo); intentional create + `poco margen` OK; optional probe `cuanto pesa` / `añadir un motor` → wall. |
| **N3** | Info | Explain-shaped unknowns still pay one `interpret` before analyze — pre-existing; out of Buy. |
| **N4** | Info | G-03 still open. |
| **N5** | Info | Full suite **4132 passed, 10 skipped** trusted from implementer. Reviewer: both test files → **21 passed**; stub repro `hablar`/`gracias`/`hola` → `project_status`. |

---

## 4. Tests executed by reviewer

```text
python -m pytest -q tests/test_llm_unknown_situate_b1.py \
  tests/test_llm_interpret_unknown_guard_b1.py
→ 21 passed in 0.23s
```

---

## 5. Engineer ACCEPT status

**Pending live smoke.** On ★: tag **`v0.8.7`** closes CI-1 + CI-1b + CI-1c + CI-1d.

```text
unset JARVIS_OLLAMA_MODEL
python -m jarvis.adapters.cli.main --chat   # project loaded
User > hablar     → Continuity wall · no analyze dump · no new llm_logs
User > gracias    → same
User > explicame el margen → analyze · no plan · no instruction echo
# optional: cuanto pesa / añadir un motor → wall
# nuevo / poco margen unchanged
```
