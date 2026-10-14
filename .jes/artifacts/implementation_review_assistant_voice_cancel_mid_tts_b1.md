# Implementation Review — Cancel mid-TTS (`B1-assistant-voice-cancel-mid-tts`, T56 / V12)

**Project:** Jarvis  
**Date:** 2026-10-14  
**Reviewer:** Cursor (independent — not implementer)  
**Contract:** [IC](implementation_contract_assistant_voice_cancel_mid_tts_b1.md) · [V12-DC](design_contract_assistant_voice_cancel_mid_tts_b0.md) · [report](implementation_report_assistant_voice_cancel_mid_tts_b1.md)  
**Tip under review:** `913b58a` on `cursor/chat-voice-ptt-impl-8ac5` · package **`0.8.3`**  
**Parent:** `d10ff40` / tags **`v0.8.1`** · **`v0.8.2`** (T54/T55 ★)

**Verdict:** **PASS WITH NOTES** → Engineer ★ **ACCEPT CLOSED** (2026-10-14) @ tip **`v0.8.3`**.

**Process note:** Independent Cursor review of record. Same-session self-PASS is not review of record. Engineer ★ ACCEPT CLOSED → tag **`v0.8.3`**. N1–N3 remain non-blocking (live Piper smoke optional).

---

## 1. Scope check vs IC

| Lock / IC item | Evidence | Result |
|---|---|---|
| 1 · Buy · `0.8.3` | `pyproject.toml` `version = "0.8.3"`; no speech deps | **Pass** |
| 2 · Voice-only session UX; `--chat` quiet | Catch only in `_chat_speak_fn(True)`; T4 bare chat | **Pass** |
| 3 · Interruptible seam + kill + distinct cancel | `Popen(start_new_session=True)` + `_stop_process_group` + `TtsCancelled` | **Pass** |
| 4 · Session continues; exact print | `Habla cancelada.` print-only; T2 no premature `Sesión cerrada.`; REC after cancel | **Pass** |
| 5 · Record / silence cut unchanged | T3; `record_turn.sh` not in diff | **Pass** |
| 6 · Guide | Mid-speech vs mid-record Ctrl-C documented | **Pass** |
| 7 · Spoken-continuity map | New **screen-only** `Habla cancelada` row | **Pass** |
| 8 · Tests T1–T6 | New file; T1 has sigterm + sigkill-escalation | **Pass** |
| 9 · Out of scope | No T57/T58, wake-word, Continuity rewrite | **Pass** |

**Not live-smoked** with Piper speaking — IC §3 remains Engineer ACCEPT gate. Implementer verified real `afplay` under wrapper + real SIGINT (0.81 s of 20 s, no orphan player).

---

## 2. Judgment calls (report §2) — **accepted**

| # | Choice | Review |
|---|---|---|
| 1 | `start_new_session=True` so killpg hits wrapper+player; terminal SIGINT hits only Jarvis | **Accept.** Required for `piper_tts.sh` → `afplay` honesty. |
| 2 | `TtsCancelled(KeyboardInterrupt)`, not `TtsError` | **Accept.** Prevents “TTS no disponible” on cancel; batch keeps plain Ctrl-C with player stopped. |
| 3 | SIGTERM → 2 s grace → SIGKILL group sweep | **Accept.** T1 pins both TERM-respecting and TERM-ignoring fakes. |
| 4 | Mid-speech cancel does **not** count toward double-Ctrl-C exit | **Accept.** Exit counter stays record-only (T53). |

---

## 3. Notes (non-blocking)

| ID | Severity | Note |
|---|---|---|
| **N1** | Info / ACCEPT gate | **No live Piper smoke.** Ask `completo`, Ctrl-C mid-speech → silence + mic cue + session alive (IC §3). |
| **N2** | Info | Ctrl-C **between** speak and next record (brain thinking) still prior behavior — out of lock; **T58** territory. |
| **N3** | Info | POSIX-only (`killpg` / new session). Voice wrappers already POSIX. |
| **Carry** | — | **T57** anti-eco settle · **T58** in-session key · **T40** Parked. |

---

## 4. Tests executed by reviewer

```text
pytest tests/test_assistant_voice_cancel_mid_tts_b1.py \
       tests/test_assistant_voice_only_loop_b1.py \
       tests/test_assistant_voice_silence_cut_b1.py -q
→ 22 passed in 25.20s
```

Implementer reports full suite **4074 passed / 9 skipped / 0 failed** — not re-run in full here; focused set green.

---

## 5. Recommendation

**PASS WITH NOTES.** Engineer ★ ACCEPT CLOSED (2026-10-14) → tag **`v0.8.3`**. N1 live Piper smoke remains optional operator validation. Next comfort Buys: **T57** / **T58** when wanted.
