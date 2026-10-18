# Implementation Review — Gemma 4 E4B default model (`B1-llm-gemma4-default-model`, CI-1)

**Project:** Jarvis  
**Date:** 2026-10-15  
**Reviewer:** Cursor (independent — not implementer)  
**Contract:** [IC](implementation_contract_llm_gemma4_default_model_b1.md) · [report](implementation_report_llm_gemma4_default_model_b1.md)  
**Package under review:** **`0.8.7`** (uncommitted / untagged)  
**Parent:** tip **`v0.8.6`** · [CI-0 DC](design_contract_continuity_interpreter_epoch_b0.md)

**Verdict:** **PASS WITH NOTES** (code vs IC) · later smoke REJECTED → remediations CI-1b…1e · **★ ACCEPT CLOSED** (Engineer 2026-10-18) @ **`v0.8.7`**.

**CI-1b…CI-1e:** closed with package tag — see [CI-1e review](implementation_review_llm_unknown_situate_brief_b1.md).

**Process note:** Independent Cursor review of record. Claude implemented; Cursor did not implement this Buy.  
**Engineer smoke (2026-10-16):** `explicame el margen` → plan “Mejorar estabilidad” + system-prompt paraphrase + only then margin notes. Engineer: *pregunta no tiene que ver → no PASS/ACCEPT.*

---

## 1. Scope check vs IC

| Lock / IC item | Evidence | Result |
|---|---|---|
| 1 · Buy · `0.8.7` | `pyproject.toml` `version = "0.8.7"` | **Pass** |
| 2 · Default tag exact | `DEFAULT_OLLAMA_MODEL = "hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL"`; `OLLAMA_MODEL = getenv(..., DEFAULT_OLLAMA_MODEL)` | **Pass** |
| 3 · Env override | Unchanged `JARVIS_OLLAMA_MODEL`; T2 subprocess | **Pass** |
| 4 · Product docs default | `README.md` · `src/jarvis/README.md` show Gemma; no `qwen2.5:14b` as default (T4) | **Pass** |
| 5 · Tests fixtures | `test_main_cli.py` uses `DEFAULT_OLLAMA_MODEL`; no tip pins | **Pass** |
| 6 · PRIORIDAD · cola · state · lock | CI-1 Implemented awaiting review; lock “don’t change default” superseded | **Pass** |
| 7 · Out of scope | No orchestrator / ActionPolicy / Continuity / prompt / voice compose / interpret retire in diff | **Pass** |
| Tests T1–T4 | New `tests/test_llm_gemma4_default_model_b1.py` + main_cli alignment | **Pass** (see N2) |
| Report honesty | No ACCEPT claim; live smoke + egg-info disclosed | **Pass** |

---

## 2. Judgment calls — **accepted**

| # | Choice | Review |
|---|---|---|
| 1 | Named `DEFAULT_OLLAMA_MODEL` constant (not only inline getenv default) | **Accept.** Cleaner for tests/fixtures; same product default. |
| 2 | Env checks in **subprocess** | **Accept.** Avoids stale `from jarvis.config import OLLAMA_MODEL` bindings. |
| 3 | Leave historical `qwen` mentions in calibration/INV | **Accept.** IC scoped product default docs only. |
| 4 | Spoken-continuity map not updated | **Accept.** Banner string value change only; no new egress surface. |

---

## 3. Notes (non-blocking)

| ID | Severity | Note |
|---|---|---|
| **N1** | Info / **ACCEPT gate** | Live `--chat` smoke still required (IC §3): unset `JARVIS_OLLAMA_MODEL`, banner shows Gemma tag, one `estado`/status + one interpret/analyze-shaped turn, no hang. |
| **N2** | Info | IC T4 also listed pyproject/PRIORIDAD coherence in the test row; pytest T4 covers READMEs only. Package **0.8.7** and status docs verified by reviewer grep — OK. Optional later: assert `pyproject` version in the unit file. |
| **N3** | Info | `src/jarvis.egg-info/PKG-INFO` may stay stale until `pip install -e .` — disclosed; not a product gate. |
| **Carry** | — | CI-2 egress next after ★ · `interpret` quarantine unchanged · T40 Parked. |

---

## 4. Tests executed by reviewer

```text
python -m pytest -q tests/test_llm_gemma4_default_model_b1.py tests/test_main_cli.py
→ 35 passed in 0.20s
```

Full suite **4096 passed, 9 skipped** trusted from implementer report (not re-run this review turn).

---

## 5. Engineer ACCEPT status

**REJECTED** on live smoke (not a code-vs-IC fail of the default tag alone).

| Symptom | Likely root |
|---|---|
| Plan “Mejorar estabilidad” for `explicame el margen` | `detect_goal` in `_handle_analyze` matches “margen” → `mejorar_estabilidad`, then prepends `format_goal_plan` |
| “Reglas clave / Estoy listo…” | Gemma E4B paraphrases `build_analysis_messages` system + prefill `En resumen,` |

**Remediation before ★ (pick one):**

1. **CI-1b hotfix IC** (narrow): (a) do not prepend goal plan on explanatory asks / tighten `detect_goal` so bare “margen”≠estabilidad plan; (b) harden analyze prompt/prefill for Gemma so instructions are not echoed.  
2. Or fold (a)(b) into **CI-2** egress and keep CI-1 untagged until that ships.

Default tag change may stay in tree; **no tag / no ACCEPT** until Engineer re-smokes a faithful answer to `explicame el margen`.
