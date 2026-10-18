# Implementation Review — Interpret unknown-intent wizard guard (`B1-llm-interpret-unknown-guard`, CI-1c)

**Project:** Jarvis  
**Date:** 2026-10-16  
**Reviewer:** Cursor (independent — not implementer)  
**Contract:** [IC](implementation_contract_llm_interpret_unknown_guard_b1.md) · [report](implementation_report_llm_interpret_unknown_guard_b1.md)  
**Package under review:** **`0.8.7`** (uncommitted / untagged)  
**Parent:** tip **`v0.8.6`** · [CI-INV-0 review](investigation_review_voice_llm_ci_audit_b0.md) · CI-1b PASS WITH NOTES

**Verdict:** **PASS WITH NOTES** (code vs IC + Engineer scope decision) — **no ACCEPT**. Tag **`v0.8.7` not authorized** until Engineer live smoke ★ (CI-1b + CI-1c probes).

**Process note:** Claude implemented; Cursor did not implement this Buy.

---

## 1. Scope check vs IC

| Lock / IC item | Evidence | Result |
|---|---|---|
| 1 · Buy · package `0.8.7` · no tag | `pyproject.toml` `0.8.7`; no ACCEPT claimed | **Pass** |
| 2 · unknown + ActionPolicy verbs → analyze, not `handle` | `orchestrator.py:2592-2606`: `iterate` always; `create_project`/`calculate`/`simulate` when `_has_active_project()` | **Pass with N1** (scoped; see §2) |
| 3 · Bug 52 iterate compatible | unconditional `iterate` branch; T3 + no-project iterate test | **Pass** |
| 4 · No ActionPolicy / prompt / interpret shape | untouched | **Pass** |
| 5 · `invalid_llm_output` unchanged | still checked before guard; T5 | **Pass** |
| 6 · Stay out of `CREATE_PROJECT_INTERACTIVE` on active project | T1; reviewer stub repro | **Pass** |
| 7 · Tests + status docs · no bump | new test file T1–T5 (+ scope); cola/PRIORIDAD/state | **Pass** |
| 8 · Out of scope | G-03 / CI-2 / keywords / DEFAULT untouched | **Pass** |
| Report honesty | §2 Engineer decision + battery stubs disclosed | **Pass** |

---

## 2. Judgment calls — **accepted**

| # | Choice | Review |
|---|---|---|
| 1 | Active-project scope for `create_project`/`calculate`/`simulate` | **Accept.** IC lock 2 was literal “all four verbs”; Engineer chose active-project-only after `test_idle_falls_back_to_llm_when_local_resolution_has_no_match` broke. Matches G-01 harm (wizard **over** active project). No-project create via interpret remains reachable — pinned. Documented. |
| 2 | Battery stubs gain `analyze` | **Accept.** Necessary consequence of the guard; assertions unchanged. |
| 3 | Extra scope tests beyond T1–T5 | **Accept.** Pins Engineer decision. |

---

## 3. Notes (non-blocking)

| ID | Severity | Note |
|---|---|---|
| **N1** | Info / product | No-project + Gemma `hablar→create_project` still opens wizard. Intentional. Daily path with a loaded project is the ★ gate. |
| **N2** | Info / **ACCEPT gate** | Live smoke (IC §0): project loaded · `hablar` / `gracias` → no wizard · `explicame el margen` (CI-1b) · intentional create still works. |
| **N3** | Info | Guarded nonsense → analyze narration (spoken on `--voice-only`) — non-mutating; CI-2/CI-4 later. |
| **N4** | Info | G-03 still open (voice `run_chat` + no project → live Ollama). Not this Buy. |
| **N5** | Info | Full suite **4121 passed, 10 skipped** trusted from implementer. Reviewer: new file + battery + llm_integration → **67 passed**; stub repro IDLE/no wizard. |

---

## 4. Tests executed by reviewer

```text
python -m pytest -q tests/test_llm_interpret_unknown_guard_b1.py \
  tests/test_battery_component.py tests/test_llm_integration.py
→ 67 passed
```

Stub repro: closed project + `interpret→create_project` on `hablar` → `action=analyze`, mode IDLE, no wizard copy.

---

## 5. Engineer ACCEPT status

**Pending live smoke.** On ★ (CI-1b + CI-1c): tag **`v0.8.7`** closes CI-1 + CI-1b + CI-1c.

```text
unset JARVIS_OLLAMA_MODEL
python -m jarvis.adapters.cli.main --chat   # project loaded
User > hablar          → no create wizard
User > gracias         → no create wizard
User > explicame el margen  → CI-1b criteria
# intentional create still works (nuevo / quiero diseñar…)
```
