# Implementation Review — In-session cancel key (`B1-assistant-voice-session-key`, T58 / V12)

**Project:** Jarvis  
**Date:** 2026-10-14  
**Reviewer:** Cursor (independent — not implementer)  
**Contract:** [IC](implementation_contract_assistant_voice_session_key_b1.md) · [V12-DC](design_contract_assistant_voice_cancel_mid_tts_b0.md) · [report](implementation_report_assistant_voice_session_key_b1.md)  
**Tip under review:** `8807bfd` on `cursor/chat-voice-ptt-impl-8ac5` · package **`0.8.5`**  
**Parent:** `904f0d5` / **`v0.8.4`** (T57 ★) · IC commit `ec73f9c`

**Verdict:** **PASS WITH NOTES** → Engineer ★ **ACCEPT CLOSED** (2026-10-14) @ tip **`v0.8.5`**.

**Process note:** Independent Cursor review of record. Same-session self-PASS is not review of record. Engineer ★ ACCEPT CLOSED → tag **`v0.8.5`**. N1–N3 remain non-blocking (live Piper/mic smoke optional).

---

## 1. Scope check vs IC

| Lock / IC item | Evidence | Result |
|---|---|---|
| 1 · Buy · `0.8.5` | `pyproject.toml` `version = "0.8.5"`; no new speech deps | **Pass** |
| 2 · `--voice-only` only | `run_voice_only` builds `SessionKeyWatcher.for_terminal()`; T5: bare `--chat` never calls it | **Pass** |
| 3 · Esc/Space mid-TTS = T56 Ctrl-C | Window around `speak_egress` → `killpg(SIGINT)` → T56 stop-group / `TtsCancelled` → `Habla cancelada.`; T1/T2 pty + T3 | **Pass** |
| 4 · Esc on settle/record; Space pick | **Pick: Space ignored** (`TAKE_CANCEL_KEYS={Esc}`); T4 Space during settle ignored; Esc cancels / double ends | **Pass** |
| 5 · No global OS hotkey | stdlib `termios`/`tty`/`select`/`threading` only; `for_terminal()` requires TTY + `tcgetpgrp == getpgrp` | **Pass** |
| 6 · Watcher during `speak_egress` | New `session_keys.py` (not `external_tts.py`) — main wraps speak; key = group SIGINT → existing T56 path; T1/T2 no orphan pids, ICANON restored | **Pass** (judgment accepted) |
| 7 · Brain gap out | Watcher only in speak / settle+record+STT windows; no session-wide thread | **Pass** |
| 8 · Banner / guide | Banner line only when watcher active; guide §4/§8 Esc/Espacio + flechas=Esc | **Pass** |
| 9 · Map · no new Habla string | Map tip + banner row wording; reuses `Habla cancelada.` / `Grabación cancelada.` | **Pass** |
| 10 · Tests T1–T6 | `test_assistant_voice_session_key_b1.py` T1/T2/T1b/T3–T6 | **Pass** |
| 11 · Out of scope | No wake-word / barge-in / global hotkey / T40 / Continuity rewrite / ACCEPT claim | **Pass** |

**Not live-smoked** — IC §3 Piper / real mic Esc/Space remains Engineer gate.

---

## 2. Judgment calls — **accepted**

| # | Choice | Review |
|---|---|---|
| 1 | Key → `os.killpg(getpgrp(), SIGINT)` instead of a second cancel path inside `external_tts` | **Accept.** Literal Ctrl-C equivalence; reuses reviewed T56/T53/T57. Group (not self-only) needed so `record_turn.sh` INT trap stops ffmpeg. |
| 2 | New `session_keys.py` + main windows; `external_tts.py` untouched | **Accept.** IC listed TTS as likely touch; wrapping at the speaker is cleaner and keeps cancel honesty in one place. |
| 3 | Space ignored during settle/record | **Accept.** IC lock 4 allowed either pick; bumped space must not trash a take; T4 pins it. |
| 4 | `KeyboardInterrupt` + `window.fired` after speak returns → same `Habla cancelada.` | **Accept.** Race at speech end still reads as user cancel, not session kill. |

---

## 3. Notes (non-blocking)

| ID | Severity | Note |
|---|---|---|
| **N1** | Info / ACCEPT gate | **No live Piper/mic smoke** (IC §3). Esc/Space mid-speech and Esc while Grabando still Operator validation. |
| **N2** | Info | Arrow keys start with Esc byte → count as Esc (guide §8). |
| **N3** | Info | Wrapper that shares Jarvis’s process group gets the same SIGINT on Esc as on real Ctrl-C — by design. |
| **Carry** | — | Brain/LLM-wait cancel (T56 N2) still out · **T40** Parked. |

---

## 4. Tests executed by reviewer

```text
# First attempt (sandbox): T1/T2 OSError: out of pty devices — env, not product.
# Outside sandbox:
pytest tests/test_assistant_voice_session_key_b1.py \
       tests/test_assistant_voice_cancel_mid_tts_b1.py -q
→ 14 passed in 12.39s
```

Implementer reports full suite **4086 passed / 9 skipped / 0 failed** (+7) and T56+T58 files 5× repeated 14/14 — not re-run in full here; focused set green.

---

## 5. Recommendation

**PASS WITH NOTES.** Engineer ★ ACCEPT CLOSED (2026-10-14) → tag **`v0.8.5`**. N1 live Esc/Space smoke remains optional operator validation. **V12 comfort** (T56–T58) ★ closed. Next: **T40** Parked, or Engineer pick.
