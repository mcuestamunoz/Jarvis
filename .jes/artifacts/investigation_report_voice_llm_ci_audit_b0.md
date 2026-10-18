# Investigation Report — Voice + LLM / Continuity Interpreter audit (`INV-voice-llm-ci-audit`, CI-INV-0) — Index

**Project:** Jarvis · **Date:** 2026-10-16 · **Investigator:** Claude Code (read-only)
**Contract:** [INV IC](investigation_contract_voice_llm_continuity_interpreter_audit_b0.md)
**Status:** **PASS WITH NOTES** — [Cursor review](investigation_review_voice_llm_ci_audit_b0.md). No ACCEPT claim. No `src/` edit. Tip `v0.8.6`; tree `0.8.7` untagged. **Next:** [CI-1c IC](implementation_contract_llm_interpret_unknown_guard_b1.md).

## Next step (≤15 lines)

```text
BLOCKER found: with the CI-1 Gemma default, unclassified input ("hablar",
"Gracias.", free questions) validates as create_project and OPENS THE
CREATE WIZARD over the active project (Bug 52 guard covers iterate only).
Voice-only STT hallucinations hit it. Not covered by the CI-1/CI-1b smoke.

ONE NEXT STEP → CI-1c  B1-llm-interpret-unknown-guard  (IC) before ★ v0.8.7.
  Extend Bug 52 (orchestrator.py:2586) to wizard-opening verbs on
  intent "unknown"; stub-LLM regression tests. Locks: CI-0 #5, #9.
Engineer now: in the CI-1b re-smoke also type "hablar" and "gracias" with a
project loaded; "Vamos a definir el proyecto paso a paso." → open CI-1c.
#2 tests-only: stop run_chat tests hitting live Ollama / real llm_logs.
#3 CI-2 DC egress (answers Open #2; analyze is spoken verbatim today).
T40 stays Parked. Do not delete interpret: log corpus is test-polluted.
```

## Parts

| Part | File | Answers |
|---|---|---|
| A — Voice phase tip | [part_a_voice](investigation_report_voice_llm_ci_audit_part_a_voice_b0.md) | A1–A8 · T44-vs-CI-0 conflict table · T40 rec |
| B — LLM + CI epoch | [part_b_llm_ci](investigation_report_voice_llm_ci_audit_part_b_llm_ci_b0.md) | B1–B10 · call graph · log sample · CI-5 measurement plan |
| C — Synthesis | [part_c_synthesis](investigation_report_voice_llm_ci_audit_part_c_synthesis_b0.md) | C1 gap register (G-01…G-15) · C2 roadmap · C3 one step · C4 stops · C5 wording |

## Headline findings

1. **Voice cola truth is clean:** T35–T59 verdicts = tags `v0.6.43`…`v0.8.6`; only doc drift (consumed DCs still "DC ready"). Two product modes are exactly as T53 locked; `--voice-only` = same brain as `--chat` (`main.py:992`).
2. **LLM text already reaches TTS:** `analyze` answers are spoken verbatim on `--voice-only` and are missing from the spoken-continuity map.
3. **ActionPolicy holds the verb, not the relevance:** G-01 (above) and residual bare goal tokens (G-02) are the same "valid output, wrong turn" class as the rejected CI-1 smoke.
4. **Suite reaches live Ollama:** two pre-existing `run_chat` tests make real Gemma calls and write the real `llm_logs/` (proven: 2 calls, 28.9 s); 90/133 `interpret` log rows are that test input — CI-5 measurement is blocked until fixed.
5. **CI-0 vs tip:** locks 2/7/8/12 satisfied; 1/3/6 not started; 4 contradicted (expected, `--chat` silent); 5/9/10 partial.

## Method / side effects

Read-only over artifacts, `src/`, `docs/`, `git tag`, `runtime/llm_logs/` (158 files). Probes: `IntentResolver.resolve_intent` + `detect_goal`/`is_explain_ask` on sample phrases; one in-memory stub-LLM repro of G-01 (tmp workspace). Ran 2 existing tests to prove G-03 (+2 gitignored log files). Full suite not re-run (no code change; last run 4111 passed / 10 skipped on this tree).
