# Implementation Contract — Blank / non-speech STT take (`B1-assistant-voice-blank-stt-take`)

**Project:** Jarvis  
**Date:** 2026-10-14  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.8.6`**

**Status:** **IC ready** — Engineer “hay que corregir ese bucle” after T58 ★ @ `v0.8.5` live smoke. Paste to Claude.  
**Parents:** [T58 ★](implementation_review_assistant_voice_session_key_b1.md) @ `v0.8.5` · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md) §8 · tip **`v0.8.5`**  
**Type:** When `--voice-only` STT returns a **non-speech marker** (silence / blank take), treat it as an **empty take** — reopen the mic **without** `No se pudo interpretar la intención`.  
**Opens:** **`0.8.6` / `v0.8.6`**. **Cola:** **T59**

**Not:** wake-word · always-on · filtering arbitrary English hallucinations (“See you in the next step”) · LLM language detect · T40 · Continuity rewrite · ACCEPT claim · new speech deps.

---

## Why this Buy

Live smoke after T58: if the operator says nothing for the full record window (~7 s), whisper often returns `[BLANK_AUDIO]`, `[Music]`, or similar bracket tokens. Those are **non-empty strings**, so the mic reader echoes `User > [voz] …` and the chat brain answers **`No se pudo interpretar la intención`**, then opens the mic again — an infinite loop until `salir` / double Esc. Empty keyboard Enter already continues silently (`if not user_input: continue`). Blank STT must match that product honesty.

`-l es` (guide) reduces Spanish→English mistranslation when the user **does** speak; it does **not** fix silence → marker tokens.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-voice-blank-stt-take`**. Package/tag **`0.8.6` / `v0.8.6`** |
| 2 | **`--voice-only` mic path only** — after `transcribe_audio_file` succeeds, before echoing `User > [voz]` and before returning text to `_run_chat_session` |
| 3 | **Non-speech markers → empty take** — if the transcript (after normal whitespace collapse) is empty **or** matches a small closed set of STT non-speech markers (at least: `[BLANK_AUDIO]`, `[Music]`, `[Silence]`, case-insensitive; optional trailing punctuation strip consistent with T55 spirit), then: **do not** print `User > [voz] …`; **do not** send text to the brain; return `""` so the loop continues to the next `Grabando…` with **no** `No se pudo interpretar la intención` |
| 4 | **Real speech unchanged** — any other transcript (including wrong English like “See you…”) still echoes and goes to the brain as today. Out of this Buy to invent NLU / language filters |
| 5 | **Shared helper preferred** — e.g. `is_blank_stt_transcript(text) -> bool` in `adapters/voice/` (or next to STT), unit-tested; mic reader calls it. Optional: `whisper_stt.sh` may also refuse markers as empty (fail → existing `SttError` path that already returns `""`) — pick one primary path, document; prefer Python so any STT cmd benefits |
| 6 | **No new spoken / screen honesty string** unless needed — silent re-listen is enough (same as empty Enter). Map tip-only if no new surface |
| 7 | **Guide §8** — update the blank-loop bullet: fixed behavior + still recommend `JARVIS_WHISPER_ARGS="-l es"` for spoken Spanish |
| 8 | **Tests T1–T5** — mic-free; see §2 |
| 9 | **Out** — wake-word · barge-in · English-hallucination filter · changing silence-cut / settle defaults · T40 · ACCEPT claim |

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/adapters/voice/` (new helper or `external_stt.py`) | `is_blank_stt_transcript` + marker set |
| `src/jarvis/adapters/cli/main.py` | `_make_mic_line_reader`: after STT, if blank → return `""` without echo |
| `tests/test_assistant_voice_blank_stt_take_b1.py` | **new** T1–T5 |
| `docs/USER_GUIDE_VOICE.md` | §8 loop bullet = fixed |
| `pyproject.toml` | `0.8.5` → **`0.8.6`** |
| PRIORIDAD · cola · state · short PLATFORM/CONNECTIONS if needed | **no new C-xxx** |

Do **not** touch orchestrator intent parse, Continuity, `record_turn.sh`, TTS cancel paths.

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | `is_blank_stt_transcript("[BLANK_AUDIO]")` / `[Music]` / `[Silence]` / mixed case / surrounding spaces → True |
| T2 | Real phrases (`estado`, `salir`, `Completo.`) → False |
| T3 | Voice-only loop (fake STT returns `[BLANK_AUDIO]`): **no** `No se pudo interpretar`; **no** `User > [voz] [BLANK_AUDIO]`; next turn records again (or session continues) |
| T4 | Fake STT returns `estado` → still echoes `User > [voz] estado` and normal Skill/Continuity path (smoke with existing fakes) |
| T5 | Guide mentions blank take / no intent loop; `pyproject` **0.8.6**; tip-pin/ESC fences; no speech deps; no new C-xxx |

---

## 3. Acceptance

- [ ] Live `--voice-only`: say nothing for a full window → next `Grabando…` **without** `No se pudo interpretar la intención`  
- [ ] Say `estado` (with `-l es`) → still works  
- [ ] `0.8.6` · Cursor review · Engineer ★ · tag **`v0.8.6`**

---

## 4. Paste for Claude

```text
Implementation — B1-assistant-voice-blank-stt-take (T59)
Parent: T58 ★ @ v0.8.5 live smoke. Package → 0.8.6.

IC: .jes/artifacts/implementation_contract_assistant_voice_blank_stt_take_b1.md
Guide: docs/USER_GUIDE_VOICE.md §8

GOAL: In --voice-only, when STT returns non-speech markers
([BLANK_AUDIO], [Music], [Silence], …) or whitespace-only, treat as
empty take: no User > [voz] echo, no "No se pudo interpretar la
intención", reopen mic (return ""). Real speech unchanged.

DO:
- Helper is_blank_stt_transcript (closed marker set, case-insensitive).
- Wire in _make_mic_line_reader after transcribe, before echo/return.
- Tests T1–T5. Guide §8. pyproject 0.8.6. PRIORIDAD/cola/state.
- No new C-xxx. No ACCEPT claim.

NO: wake-word · English-hallucination NLU · T40 · Continuity rewrite ·
silence-cut/settle redo
```

---

## 5. Cursor note

Claude may implement the full IC without per-edit approval. Stop if the Buy requires filtering arbitrary English prose or a new always-on mic thread — that is out of lock.
