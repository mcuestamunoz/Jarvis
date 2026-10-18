# Investigation Review — Voice + LLM / Continuity Interpreter audit (`INV-voice-llm-ci-audit`, CI-INV-0)

**Project:** Jarvis  
**Date:** 2026-10-16  
**Reviewer:** Cursor (independent — not investigator)  
**Contract:** [INV IC](investigation_contract_voice_llm_continuity_interpreter_audit_b0.md)  
**Reports:** [index](investigation_report_voice_llm_ci_audit_b0.md) · [Part A](investigation_report_voice_llm_ci_audit_part_a_voice_b0.md) · [Part B](investigation_report_voice_llm_ci_audit_part_b_llm_ci_b0.md) · [Part C](investigation_report_voice_llm_ci_audit_part_c_synthesis_b0.md)  
**Tree:** tip **`v0.8.6`** + uncommitted CI-1/CI-1b **`0.8.7`**

**Verdict:** **PASS WITH NOTES** — findings accepted as review of record. **No ACCEPT** of product. **Endorse C3:** open **CI-1c** before ★ **`v0.8.7`**.

**Process note:** Claude investigated (read-only). Cursor did not write Parts A/B/C. Same-session self-PASS is not review of record.

---

## 1. Acceptance vs INV IC

| IC item | Result |
|---|---|
| A1–A8 answered with citations | **Pass** |
| B1–B10 answered with citations | **Pass** |
| C1 gap register + C3 one next step | **Pass** — G-01…G-15 coherent |
| T40 recommendation (Parked) | **Pass** — endorsed |
| CI-0 vs T44 “no LLM Layer 2” table | **Pass** (Part A) — latent; settle in CI-2 DC |
| Zero `src/` product edits | **Pass** (side effect: +2 gitignored `llm_logs` from G-03 proof — disclosed) |
| Index ≤15-line next-step box | **Pass** |

---

## 2. Independent verification of the blocker (G-01)

Reviewer reproduced with stub LLM on a closed project (`tests.test_fn022_engineering_intent._closed_project`):

```text
IntentResolver: hablar / Gracias. / sistema → unknown
Stub interpret → {"action": "create_project", "parameters": {"goal": "hablar"}}
handle_user_text("hablar", stub) →
  message starts "Vamos a definir el proyecto paso a paso."
  session IDLE → CREATE_PROJECT_INTERACTIVE
```

Bug 52 guard at `orchestrator.py:2586-2589` covers only `intent == "unknown" and action == "iterate"`. Claim that CI-1/CI-1b smoke criteria do not exercise this path: **confirmed**. Voice worsening (STT hallucination → same path): **accepted** (same brain as `--chat`).

---

## 3. Other headline claims — spot-check

| Claim | Review |
|---|---|
| Voice cola T35–T59 coherent with tags | Accepted (doc drift only) — not re-enumerated every tag this turn |
| `--voice-only` == `--chat` brain | Accepted (`main.py` shared `_run_chat_session`) |
| `analyze` spoken verbatim; map missing row | Accepted (A3-g1) — CI-2 inventory |
| Suite hits live Ollama on `hablar` `run_chat` tests | Accepted in principle (A6 + Part B B7); G-03 = #2 after CI-1c |
| Residual bare goal tokens (G-02) | Accepted — same class as CI-1 smoke; not blocker for ★ if CI-1c lands; fold CI-4 / F-1b later |
| CI-0 lock table | Accepted |
| T40 Parked | **Endorsed** |

---

## 4. Notes (non-blocking)

| ID | Severity | Note |
|---|---|---|
| **N1** | Gate | Engineer must add `hablar` / `gracias` to CI-1b re-smoke **with project loaded**. Wizard copy → do not tag; paste CI-1c. |
| **N2** | Info | C3 shape “extend Bug 52” is correct grain. IC should also cover `calculate`/`simulate` on `unknown` (same class) — see CI-1c IC. |
| **N3** | Info | G-03 (test→live Ollama) is real hygiene and blocks CI-5 measurement; must not displace CI-1c. |
| **N4** | Info | Open #2 (`--chat` speak?) remains Engineer input for CI-2 DC — not this Buy. |
| **N5** | Info | Full suite not re-run for INV (docs-only) — acceptable; last tree run 4111/10 skip trusted. |

---

## 5. Engineer next actions (ordered)

1. **Re-smoke CI-1b** incl. `explicame el margen` **and** `hablar` / `gracias` (project loaded).  
2. If G-01 reproduces live → paste **CI-1c** IC (Cursor-written, below). Do **not** ★ `v0.8.7` on CI-1b alone.  
3. After CI-1c ★ (+ CI-1b ★) → tag **`v0.8.7`**.  
4. Then: G-03 hygiene IC (parallel OK) · CI-2 DC (needs Open #2).

**Stop:** tag on analyze-only smoke · CI-2 before ★ · delete `interpret` · unpark T40.
