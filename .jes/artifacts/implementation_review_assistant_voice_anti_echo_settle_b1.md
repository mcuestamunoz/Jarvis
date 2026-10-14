# Implementation Review — Anti-echo settle post-TTS (`B1-assistant-voice-anti-echo-settle`, T57 / V12)

**Project:** Jarvis  
**Date:** 2026-10-14  
**Reviewer:** Cursor (independent — not implementer)  
**Contract:** [IC](implementation_contract_assistant_voice_anti_echo_settle_b1.md) · [V12-DC](design_contract_assistant_voice_cancel_mid_tts_b0.md) · [report](implementation_report_assistant_voice_anti_echo_settle_b1.md)  
**Tip under review:** `5227eab` on `cursor/chat-voice-ptt-impl-8ac5` · package **`0.8.4`**  
**Parent:** `f07fd8d` / **`v0.8.3`** (T56 ★)

**Verdict:** **PASS WITH NOTES** → Engineer ★ **ACCEPT CLOSED** (2026-10-14) @ tip **`v0.8.4`**.

**Process note:** Independent Cursor review of record. Same-session self-PASS is not review of record. Engineer ★ ACCEPT CLOSED → tag **`v0.8.4`**. N1–N2 remain non-blocking (live settle smoke optional).

---

## 1. Scope check vs IC

| Lock / IC item | Evidence | Result |
|---|---|---|
| 1 · Buy · `0.8.4` | `pyproject.toml` `version = "0.8.4"`; no speech deps | **Pass** |
| 2 · Voice-only mic only; after cue before record | `_make_mic_line_reader` sleep after Grabando print, before `record_audio_file`; T4 `--chat` | **Pass** |
| 3 · Env default 0.35; 0/empty off | `resolve_voice_settle_seconds`; T1/T2 | **Pass** |
| 4 · After mid-TTS cancel | T3: cancel → SLEEP → REC | **Pass** |
| 5 · Sleep only; no `record_turn.sh` change | Diff; T5 | **Pass** |
| 6 · Ctrl-C during settle | Sleep inside record `try`; same Grabación cancelada / double exit; T4 | **Pass** |
| 7 · Cue unchanged; guide | Cue strings unchanged; guide §4/§8 | **Pass** |
| 8 · Map tip only | No new egress surface | **Pass** |
| 9 · Tests T1–T5 | New file + `_FakeVoice` settle=0 for older loops | **Pass** |
| 10 · Out of scope | No T58/VAD/Continuity rewrite | **Pass** |

**Not live-smoked** — whether 0.35 s cuts room bleed is Engineer IC §3.

---

## 2. Judgment calls — **accepted**

| # | Choice | Review |
|---|---|---|
| 1 | Ctrl-C during settle = mid-record cancel (same `try`) | **Accept.** One rule for the take; IC allowed this pick; T4 pins it. |
| 2 | Settle on **every** voice-only take (incl. first / no prior TTS) | **Accept.** Simplest honesty; `0` restores old timing. |
| 3 | Shared `_FakeVoice` forces settle=`0` for T53–T56 loop tests | **Accept.** Correct hygiene; T57 covers default explicitly. |

---

## 3. Notes (non-blocking)

| ID | Severity | Note |
|---|---|---|
| **N1** | Info / ACCEPT gate | **No live speaker smoke.** Tune `JARVIS_VOICE_SETTLE_SECONDS` if bleed remains or starts clip; `0` = off. |
| **N2** | Info | Default adds **~0.35 s latency** per voice turn — intentional product tradeoff. |
| **Carry** | — | **T58** in-session key · **T40** Parked. |

---

## 4. Tests executed by reviewer

```text
pytest tests/test_assistant_voice_anti_echo_settle_b1.py \
       tests/test_assistant_voice_cancel_mid_tts_b1.py \
       tests/test_assistant_voice_only_loop_b1.py -q
→ 20 passed in 35.99s
```

Implementer reports full suite **4079 passed / 9 skipped / 0 failed** — not re-run in full here; focused set green.

---

## 5. Recommendation

**PASS WITH NOTES.** Engineer ★ ACCEPT CLOSED (2026-10-14) → tag **`v0.8.4`**. N1 live settle smoke remains optional operator validation. Next comfort Buy: **T58** when wanted.
