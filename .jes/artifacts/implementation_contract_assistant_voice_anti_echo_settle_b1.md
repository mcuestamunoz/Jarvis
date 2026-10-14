# Implementation Contract — Anti-echo settle post-TTS (`B1-assistant-voice-anti-echo-settle`)

**Project:** Jarvis  
**Date:** 2026-10-14  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.8.4`**

**Status:** ★ **ACCEPT CLOSED** @ **`v0.8.4`** (2026-10-14).  
**Parents:** [V12-DC](design_contract_assistant_voice_cancel_mid_tts_b0.md) · [T56 review ★](implementation_review_assistant_voice_cancel_mid_tts_b1.md) @ `v0.8.3` · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md) · tip **`v0.8.3`**  
**Type:** Short **fixed settle delay** after speech returns (or mid-TTS cancel) **before** `--voice-only` opens the mic — reduce speaker bleed into the next capture.  
**Opens:** **`0.8.4` / `v0.8.4`**. **Cola:** **T57** / **V12**

**Not:** T58 Space/Esc · wake-word · always-on · voice barge-in / VAD · T40 · silence-cut redo · ACCEPT claim · speech SDK · changing Continuity.

---

## Why this Buy

TTS finishes (or is cancelled) and the mic opens immediately. Room/speaker bleed can land in the next wav. V12-DC planned a **fixed settle** Buy after T56 — no new DSP, just wait.

---

## 0. Engineer Buy (locked from V12-DC + this IC)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-voice-anti-echo-settle`**. Package/tag **`0.8.4` / `v0.8.4`** |
| 2 | **Only `--voice-only` mic path** — settle runs in the mic reader **before** `record_audio_file` (after the print-only Grabando cue is fine either before or after the cue print — prefer **after cue, before record** so the user sees Grabando then a brief quiet). `--chat` unchanged |
| 3 | **Env `JARVIS_VOICE_SETTLE_SECONDS`** — default **`0.35`**. Meaning: sleep that many seconds (wall clock) before starting the external recorder. **`0`** or empty → **no settle** (T56/T53 timing). Negative / unparseable → default. Document in guide; optional thin `resolve_voice_settle_seconds()` next to other voice env resolvers (same honesty style as silence seconds) |
| 4 | **Also after mid-TTS cancel** — when `Habla cancelada.` was just printed and the loop returns to `read_line`, the same settle applies before the next record (speaker may still be draining). No special case that skips settle after cancel |
| 5 | **No VAD / no DSP package** — only `time.sleep` (or equivalent). Do not change `record_turn.sh` silence logic |
| 6 | **Ctrl-C during settle** — treat like cancel-before-record: prefer same as mid-record first Ctrl-C (“Grabación cancelada…”) **or** a quiet skip that reopens; pick one, test it, do not end the session on a single Ctrl-C during settle. Double-exit rule stays record-path as today |
| 7 | **Cue / guide** — Grabando cue text need **not** mention settle (keep cue about max/silence). Guide § limits: one bullet that a short pause after speaking reduces echo; env to tune / `0` to disable |
| 8 | **Spoken-continuity map** — tip line only if needed; no new egress surface |
| 9 | **Tests T1–T5** — mic-free; see §2 |
| 10 | **Out** — T58 hotkey · wake-word · barge-in · T40 · rewriting Continuity · ACCEPT claim · lengthening silence cut as a substitute for settle |

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/adapters/cli/main.py` | Mic reader: settle sleep before `record_audio_file`; Ctrl-C policy lock 6 |
| `src/jarvis/adapters/voice/external_record.py` (or small voice helper) | Optional `resolve_voice_settle_seconds` + env constant — **prefer here** if it keeps `main.py` thin; else inline in main with tests |
| `src/jarvis/adapters/voice/__init__.py` | Export resolver if added |
| `docs/USER_GUIDE_VOICE.md` | Settle env + honesty |
| `tests/test_assistant_voice_anti_echo_settle_b1.py` | **new** T1–T5 |
| Adjust voice-only tests if they assert tight timing | Keep green (monkeypatch sleep / force settle `0`) |
| `pyproject.toml` | `0.8.3` → **`0.8.4`** |
| PRIORIDAD · cola · state · short PLATFORM/CONNECTIONS | **no new C-xxx** |

Do **not** touch orchestrator, Continuity, `speak_egress` kill path (except calling order after speak returns), `record_turn.sh`.

---

## 2. Tests

No real mic/speaker. Spy / monkeypatch `time.sleep`.

| ID | Assert |
|---|---|
| T1 | Default settle: voice-only path calls sleep with ~`0.35` (or resolved default) **once per recording turn** before RECORD; with env `0` / empty → **no** sleep (or sleep 0 not called meaningfully — assert RECORD not preceded by positive sleep) |
| T2 | Custom env e.g. `0.5` → sleep `0.5`; negative/unparseable → default |
| T3 | After a mid-TTS cancel turn, next mic turn still applies settle before RECORD |
| T4 | Mid-record / double Ctrl-C / silence cut / `--chat` silent still green (reuse patterns; force settle `0` in fixtures if needed) |
| T5 | Guide mentions settle env; `pyproject` **0.8.4**; tip-pin/ESC fences; no speech deps |

---

## 3. Acceptance

- [ ] Live `--voice-only`: after a spoken reply, short pause then Grabando; less speaker bleed in noisy rooms  
- [ ] `JARVIS_VOICE_SETTLE_SECONDS=0` restores immediate record  
- [ ] `0.8.4` · Cursor review · Engineer ★ · tag **`v0.8.4`**

---

## 4. Paste for Claude

```text
Implementation — B1-assistant-voice-anti-echo-settle (T57 / V12)
Parent: V12-DC + T56 ★ @ v0.8.3. Package → 0.8.4.

IC: .jes/artifacts/implementation_contract_assistant_voice_anti_echo_settle_b1.md
DC: .jes/artifacts/design_contract_assistant_voice_cancel_mid_tts_b0.md
Guide: docs/USER_GUIDE_VOICE.md

GOAL: After Jarvis finishes speaking (or Habla cancelada.), wait a short
fixed settle before opening the mic so speaker bleed is less likely.
No VAD. No new audio package.

DO:
- Env JARVIS_VOICE_SETTLE_SECONDS default 0.35; 0/empty = no settle;
  negative/unparseable → default. Prefer resolve_voice_settle_seconds().
- In --voice-only mic reader: sleep before record_audio_file (after
  Grabando cue print is fine). Same settle after mid-TTS cancel.
- Ctrl-C during settle: do not end session on first press; document choice.
- Guide bullet. Tests T1–T5. pyproject 0.8.4. PRIORIDAD/cola/state.
- No new C-xxx. No speech deps.

NO: T58 hotkey · wake-word · barge-in/VAD · T40 · silence-cut redo ·
ACCEPT claim · Continuity rewrite · changing speak_egress cancel kill
```

---

## 5. Cursor note

Claude may implement the full IC without per-edit approval. Stop if the Buy requires VAD, an always-on thread, or changing silence-detect thresholds as a substitute for settle — that is out of lock.
