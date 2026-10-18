# Implementation Review — Unknown → brief situate (`B1-llm-unknown-situate-brief`, CI-1e)

**Project:** Jarvis  
**Date:** 2026-10-18  
**Reviewer:** Cursor (independent — not implementer)  
**Contract:** [IC](implementation_contract_llm_unknown_situate_brief_b1.md) · [report](implementation_report_llm_unknown_situate_brief_b1.md)  
**Package under review:** **`0.8.7`** (uncommitted / untagged)  
**Parent:** tip **`v0.8.6`** · [CI-1d review](implementation_review_llm_unknown_situate_b1.md) (egress REJECT)

**Verdict:** **PASS WITH NOTES** (code vs IC) · **★ ACCEPT CLOSED** (Engineer 2026-10-18 smoke) @ **`v0.8.7`**.

**Process note:** Claude implemented; Cursor did not implement this Buy.

---

## 1. Scope check vs IC

| Lock / IC item | Evidence | Result |
|---|---|---|
| 1 · Buy · `0.8.7` · no tag | `pyproject.toml` `0.8.7`; no ACCEPT | **Pass** |
| 2 · Keep CI-1d claim | early claim unchanged; 0 interpret/analyze (T2) | **Pass** |
| 3 · Not `project_status` | `_handle_situate` → `action == "situate"` | **Pass** |
| 4 · Action `situate` + message | `orchestrator.py:6839-6860` | **Pass** |
| 5 · Brief shape + forbidden blocks | lead + project + situation + next + readiness; no why; T1 forbids wall markers | **Pass** |
| 6 · `render_response` message only | `main.py:610-613` | **Pass** |
| 7 · `estado` full wall | T4 | **Pass** |
| 8 · Other paths unchanged | T5 / T6 | **Pass** |
| 9 · Spoken map | new situate row; CI-1d note retracted from `project_status` | **Pass** |
| 10 · Tests + status docs | new file + CI-1c/1d updates | **Pass** |
| Report honesty | decisions + risks disclosed | **Pass** |

---

## 2. Judgment calls — **accepted**

| # | Choice | Review |
|---|---|---|
| 1 | Omit `next_useful_why` | **Accept.** Lock 5d optional; avoids core→CLI humanizer import and long why sentences. |
| 2 | No `startup_context` on result | **Accept.** Prevents wall fallback; no coherence footer. |
| 3 | No Bug 54 pending-define side effect | **Accept.** Brief asks nothing; “sí” must not fire a phantom offer. |
| 4 | Project line = objective / slug | **Accept.** One short line. |

---

## 3. Notes (non-blocking)

| ID | Severity | Note |
|---|---|---|
| **N1** | Info / **ACCEPT gate** | Live smoke (IC §0): `hablar`/`gracias` → brief · no wall · no new `llm_logs`; `estado` → full wall; `explicame el margen` → analyze. |
| **N2** | Info | Broad unknown claim (CI-1d trade) remains — CI-3 later. |
| **N3** | Info | Long Continuity situation/next strings pass through untrimmed — acceptable. |
| **N4** | Info | Full suite **4144 passed, 10 skipped** trusted from implementer. Reviewer: three test files → **33 passed**. |

---

## 4. Tests executed by reviewer

```text
python -m pytest -q tests/test_llm_unknown_situate_brief_b1.py \
  tests/test_llm_unknown_situate_b1.py tests/test_llm_interpret_unknown_guard_b1.py
→ 33 passed in 0.32s
```

---

## 5. Engineer ACCEPT status

**★ ACCEPT CLOSED** (2026-10-18). Smoke: `hablar`/`gracias` → brief situate; `estado` wall unchanged; `explicame el margen` → analyze (no plan/eco). Tag **`v0.8.7`** closes CI-1 + CI-1b + CI-1c + CI-1d + CI-1e. Field note for CI-2/CI-3: `explicame como funciona la potencia de radio` still hits acquisition — ingress/explain mapping.
