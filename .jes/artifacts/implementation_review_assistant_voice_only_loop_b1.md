# Implementation Review — Voice-only loop (`B1-assistant-voice-only-loop`, T53 / V9)

**Project:** Jarvis  
**Date:** 2026-10-13  
**Reviewer:** Cursor (independent — not implementer)  
**Contract:** [IC](implementation_contract_assistant_voice_only_loop_b1.md) · [V9-DC](design_contract_assistant_voice_two_mode_product_b0.md) · [report](implementation_report_assistant_voice_only_loop_b1.md)  
**Tip under review:** `e569fdd` on `cursor/chat-voice-ptt-impl-8ac5` · package **`0.8.0`** (untagged until Engineer ★)  
**Parent:** `v0.7.9` (T52 ★)

**Verdict:** **PASS WITH NOTES** → Engineer ★ **ACCEPT CLOSED** (2026-10-13) @ tip **`v0.8.0`**.

**Process note:** Independent Cursor review of record. Same-session self-PASS is not review of record. Engineer ★ ACCEPT CLOSED → tag **`v0.8.0`**. Judgment calls 1–4 remain accepted; N1–N3 non-blocking for later.

---

## 1. Scope check vs IC

| Lock / IC item | Evidence | Result |
|---|---|---|
| Two product modes `--chat` / `--voice-only` | `main()` routing; help; guide §1 table | **Pass** |
| Same full chat brain | `_run_chat_session` shared; T1 forbids `run_voice_turn` | **Pass** |
| Reuse seams, no rewrite `adapters/voice/*` | Diff is `main.py` + docs/tests; voice package untouched | **Pass** |
| Kill hybrid `--chat --voice-speak` + PTT intercept | Reject exit 2 + pointer; `is_ptt_trigger` absent from `run_chat` / `_run_chat_session` source (T3) | **Pass** |
| `--voice-speak` batch-only | Help + reject without fixture/audio | **Pass** |
| Retire interactive `--voice` | `SUPPRESS` + redirect exit 2; guide must not teach (T7/T42 file) | **Pass** |
| Mic default after speak returns | T2: `REC` … `TTS` … `REC`; cue never spoken (T1) | **Pass** |
| Fixed duration / ephemeral wav | Default 7 s cue; unlink; no workspace wavs (T2) | **Pass** |
| Keyboard only for picker | T6: one `input` when projects exist | **Pass** |
| Layer 1/2 Continuity | T6 + re-homed T45/T52 on `run_voice_only` | **Pass** |
| Bare `--chat` silent | T3; `speak_tts` removed from `run_chat` signature | **Pass** |
| `0.8.0`, no speech deps, no new C-xxx | `pyproject.toml`; PLATFORM/CONNECTIONS short notes | **Pass** |
| Tests T1–T8 | `test_assistant_voice_only_loop_b1.py` 1:1 | **Pass** |
| Guide two-mode rewrite | No current `hablar` / hybrid daily path | **Pass** |
| Spoken-continuity map | Voice-only surfaces, screen-only | **Pass** |

**Not live-smoked** with real mic/whisper/Piper — IC allowed fake scripts; Engineer live smoke remains ACCEPT gate (§4).

---

## 2. Judgment calls (report §3) — **accepted**

IC left these underspecified. Cursor finds all four **inside the spirit of the locks**, not scope creep:

| # | Choice | Review |
|---|---|---|
| 1 | Missing `JARVIS_RECORD_CMD` / `JARVIS_STT_CMD` **ends** the session (honest once); process/empty failures **reopen** mic | **Accept.** Literal “loop survives” on missing config would spin forever with no keyboard `exit`. Distinguishing config vs process errors is honest and tested (T5). |
| 2 | Second consecutive Ctrl-C ends session | **Accept.** Lock 10’s single cancel would leave no keyboard escape while almost always recording. Banner documents it. Counter resets after a completed turn. |
| 3 | Voice-only exit words ignore trailing punctuation (`Salir.`) | **Accept.** Narrow STT honesty fix, voice-only only; `--chat` unchanged. |
| 4 | `--chat --voice-only` → “choose a mode”, exit 2 | **Accept.** Prevents silent mode preference; matches two-mode product. |

---

## 3. Notes (non-blocking)

| ID | Severity | Note |
|---|---|---|
| **N1** | Low | `is_ptt_trigger` / `PTT_TRIGGER_PHRASES` still exported, unused by product. Correct per IC “don’t rewrite voice modules.” Cleanup = later IC. |
| **N2** | Low / pre-existing | STT `Completo.` may miss exact FULL phrase match → brief that turn. Lives in `spoken_continuity` (out of T53). Guide notes transcript decides. Candidate V10/polish sibling, not a T53 fail. |
| **N3** | Info | Ctrl-C during brain/TTS (between recordings) unchanged from chat — documented in report. Fine. |

---

## 4. Tests executed by reviewer

```text
pytest tests/test_assistant_voice_only_loop_b1.py \
  tests/test_assistant_chat_voice_ptt_b1.py \
  tests/test_assistant_chat_voice_speak_b1.py \
  tests/test_assistant_voice_interactive_cli_b1.py \
  tests/test_assistant_chat_spoken_continuity_b1.py \
  tests/test_assistant_voice_full_spoken_b1.py -q
→ 34 passed
```

CLI smoke: `--voice`, `--chat --voice-speak`, `--chat --voice-only` print pointers (T4 asserts exit 2). Implementer reports full suite **4054 passed / 9 skipped / 0 failed** — not re-run in full here; focused set green.

---

## 5. Recommendation

**PASS WITH NOTES** → Engineer ★ **ACCEPT CLOSED** (2026-10-13) → tag **`v0.8.0`** ✅ done.

No rework required for the four judgment calls. Optional later: N1 dead PTT export cleanup; N2 FULL-phrase punctuation normalize (own IC). Live mic/whisper/Piper smoke remains operator validation outside the suite.
