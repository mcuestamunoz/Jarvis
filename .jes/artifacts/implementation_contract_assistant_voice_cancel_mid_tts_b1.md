# Implementation Contract — Cancel mid-TTS (`B1-assistant-voice-cancel-mid-tts`)

**Project:** Jarvis  
**Date:** 2026-10-14  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.8.3`**

**Status:** **IC ready** — Engineer “me encaja” on V12 plan @ tip **`v0.8.2`**. Paste to Claude.  
**Parents:** [V12-DC](design_contract_assistant_voice_cancel_mid_tts_b0.md) · [T53 ★](implementation_review_assistant_voice_only_loop_b1.md) · [T55 ★](implementation_review_assistant_voice_stt_phrase_punctuation_b1.md) · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md) · tip **`v0.8.2`**  
**Type:** Make `--voice-only` TTS **interruptible** with Ctrl-C → kill player → continue session → reopen mic.  
**Opens:** **`0.8.3` / `v0.8.3`**. **Cola:** **T56** / **V12**

**Not:** anti-echo settle (T57) · Space/Esc hotkey (T58) · wake-word · always-on · voice barge-in · T40 · silence-cut redo · ACCEPT claim · speech SDK.

---

## Why this Buy

`speak_egress` uses blocking `subprocess.run`. While Jarvis talks, Ctrl-C does not reliably stop the external player and can feel like a session kill. Voice-only needs: **stop talking, keep listening**.

---

## 0. Engineer Buy (locked from V12-DC + this IC)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-voice-cancel-mid-tts`**. Package/tag **`0.8.3` / `v0.8.3`** |
| 2 | **`--voice-only` only** for session behavior. `--chat` unchanged (no TTS). Batch `--voice-fixture` / `--voice-audio` may inherit interruptible `speak_egress` kill semantics; their loops need not grow new product UX |
| 3 | **Interruptible TTS seam** — change `speak_egress` (preferred) from blocking `run` to a pattern that (a) starts the external command, (b) on `KeyboardInterrupt` **terminates** the child (and process group if the wrapper spawns `afplay`/player children — document judgment), (c) surfaces cancel distinctly from `TtsProcessError` (new typed error e.g. `TtsCancelled` **or** a clear return/flag — pick one and test it). Empty sanitized text still no-ops |
| 4 | **Session continues** — in `_run_chat_session` / `_chat_speak_fn` / `_say` (voice-only path): Ctrl-C during `speak(...)` → catch cancel → print **`Jarvis > Habla cancelada.`** (exact) → **do not** break the session → **do not** speak that line → fall through so the next `read_line` opens the mic. Must not print/speak `Sesión cerrada.` for a single mid-TTS Ctrl-C |
| 5 | **Record path unchanged** — mid-record Ctrl-C still “Grabación cancelada”; second consecutive still ends session (T53). Silence cut (T54) untouched |
| 6 | **Guide** — one clear bullet: Ctrl-C while Jarvis speaks cancels speech and listens again; Ctrl-C while recording cancels that take; twice to exit |
| 7 | **Spoken-continuity map** — add `Habla cancelada.` as **screen-only** (same Buy) |
| 8 | **Tests T1–T6** — mic-free; see §2 |
| 9 | **Out** — T57 settle delay · T58 Space/Esc · wake-word · barge-in · T40 · Continuity rewrite · ACCEPT claim |

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/adapters/voice/external_tts.py` | Interruptible invoke + cancel typing; keep sanitize-first |
| `src/jarvis/adapters/voice/__init__.py` | Export new error type if public |
| `src/jarvis/adapters/cli/main.py` | Voice-only speak path catches cancel → print honesty → continue |
| `docs/USER_GUIDE_VOICE.md` | Ctrl-C mid-speech vs mid-record |
| `.jes/artifacts/engineer_note_chat_spoken_continuity_map.md` | New screen-only row |
| `tests/test_assistant_voice_cancel_mid_tts_b1.py` | **new** T1–T6 |
| Adjust voice-only / TTS tests if they assumed uninterruptible `run` | Keep green |
| `pyproject.toml` | `0.8.2` → **`0.8.3`** |
| PRIORIDAD · cola · state · short PLATFORM/CONNECTIONS | **no new C-xxx** |

Do **not** touch orchestrator, Continuity extractors, `record_turn.sh`, phrase tables.

---

## 2. Tests

No real speaker. Fake `JARVIS_TTS_CMD` that sleeps / ignores SIGTERM poorly enough to prove kill, or a Python script that writes a marker and waits.

| ID | Assert |
|---|---|
| T1 | Fake TTS started; simulate KeyboardInterrupt (or send SIGINT to the waiting parent path under test) → child **not** left running; `TtsCancelled` (or chosen signal) raised / returned; no `TtsProcessError` for clean cancel |
| T2 | Voice-only session: mid-speak cancel → stdout contains `Habla cancelada.` · does **not** contain `Sesión cerrada.` for that cancel · next turn records again (fake RECORD called after cancel) |
| T3 | Mid-record Ctrl-C still “Grabación cancelada”; double Ctrl-C still ends (reuse T53 pattern) |
| T4 | Bare `--chat` never speaks / never records; cancel path not required |
| T5 | Empty sanitize still no TTS invoke; missing `JARVIS_TTS_CMD` still honest `TtsConfigError` when there is text to speak |
| T6 | Guide mentions mid-speech cancel; map has screen-only row; `pyproject` **0.8.3**; tip-pin/ESC fences; no speech deps |

---

## 3. Acceptance

- [ ] Live `--voice-only`: ask something long (`completo`); Ctrl-C while Piper still talking → speech stops; mic cue returns; session alive  
- [ ] Ctrl-C during grabación still cancels take; twice exits  
- [ ] `0.8.3` · Cursor review · Engineer ★ · tag **`v0.8.3`**

---

## 4. Paste for Claude

```text
Implementation — B1-assistant-voice-cancel-mid-tts (T56 / V12)
Parent: V12-DC + T55 ★ @ v0.8.2. Package → 0.8.3.

IC: .jes/artifacts/implementation_contract_assistant_voice_cancel_mid_tts_b1.md
DC: .jes/artifacts/design_contract_assistant_voice_cancel_mid_tts_b0.md
Guide: docs/USER_GUIDE_VOICE.md
Map: .jes/artifacts/engineer_note_chat_spoken_continuity_map.md

GOAL: In --voice-only, Ctrl-C while Jarvis is speaking stops the
external TTS, prints "Jarvis > Habla cancelada." (never spoken), keeps
the session open, and reopens the mic. Do not end the session or speak
"Sesión cerrada." for that single Ctrl-C.

DO:
- Make speak_egress interruptible: kill the TTS child on KeyboardInterrupt;
  distinct cancel signal (e.g. TtsCancelled) vs process/config errors.
- Wire voice-only speak/_say to catch cancel → print honesty → continue.
- Leave mid-record Ctrl-C / double-exit and silence cut unchanged.
- Guide + spoken-continuity map (screen-only). Tests T1–T6. pyproject 0.8.3.
- PRIORIDAD/cola/state. No new C-xxx. No speech deps.

NO: T57 anti-echo settle · T58 Space/Esc · wake-word · always-on ·
voice barge-in · T40 · silence-cut redo · ACCEPT claim · Continuity rewrite
```

---

## 5. Cursor note

Claude may implement the full IC without per-edit approval. Stop if cancel requires a new always-on audio thread, voice barge-in, or a global OS hotkey — that is out of lock (T57/T58/later).
