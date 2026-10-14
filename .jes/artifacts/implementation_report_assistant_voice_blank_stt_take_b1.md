# Implementation Report — Blank STT take (`B1-assistant-voice-blank-stt-take`, T59)

**Project:** Jarvis
**Date:** 2026-10-15
**Implementer:** Claude Code (Engineer paste)
**Contract:** [IC](implementation_contract_assistant_voice_blank_stt_take_b1.md)
**Parent:** tip `v0.8.5` (T58 ★, live smoke)
**Status:** **Implemented** — await Cursor review → Engineer ACCEPT → tag `v0.8.6`. No ACCEPT claimed.
**Package:** `0.8.5` → **`0.8.6`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/adapters/voice/external_stt.py` | `BLANK_STT_MARKERS` (closed set: `[blank_audio]`, `[silence]`, `(silence)`, `[music]`, `(music)`, `[no speech]`, `[no_speech]`) and `is_blank_stt_transcript(text)`: removes every marker (case-insensitive regex of the exact set), then the text is blank if only whitespace and T55's edge punctuation `.,;:!?¡¿` remain. `transcribe_audio_file` unchanged. Both exported from `adapters/voice`. |
| `src/jarvis/adapters/cli/main.py` | `_make_mic_line_reader`: after a successful transcribe (and the counter reset), `if is_blank_stt_transcript(transcript): return ""` — before the `User > [voz]` echo. Nothing else. |
| `tests/test_assistant_voice_blank_stt_take_b1.py` | **new** T1–T5 |
| `docs/USER_GUIDE_VOICE.md` | §8 loop bullet rewritten as fixed behavior; still recommends `JARVIS_WHISPER_ARGS="-l es"` |
| map · PLATFORM · CONNECTIONS · cola · PRIORIDAD · state · `pyproject` | tip line (no new surface); short T59 notes; T59 → Implemented; `0.8.6`. No new C-xxx, no new string, no new dependency |

**Untouched:** `whisper_stt.sh`, orchestrator/intent parse, Continuity, record/settle/silence/TTS-cancel paths, `--chat`.

**Separate commit before this one:** Cursor's uncommitted T58 live-smoke operator docs (README, guide §4/§5.2/§7/§8, `whisper_stt.sh` comments) + T59 IC + cola/PRIORIDAD/state, committed as found.

## 2. Choices (lock 5 asks for one primary path)

1. **Python, not the STT wrapper.** The check sits in the mic reader, so any `JARVIS_STT_CMD` benefits; `whisper_stt.sh` is unchanged.
2. **Silent re-listen, no new string** (lock 6) — same as an empty take; the next `Grabando…` cue is the only visible effect. Not routed through `STT no disponible` (it is not an STT failure).
3. **Whole-marker match only.** `Hola [Music]` keeps the real words (not blank); `[BLANK]` / `BLANK_AUDIO` (not in the set) are not blank; several markers in one transcript (`[BLANK_AUDIO] [BLANK_AUDIO]`, newline-separated segments) are blank.
4. **A blank take resets the double-cancel counter** — it is a completed take (cancel → blank → cancel does not end the session). Pinned in T3.

## 3. Tests

| ID | What it proves |
|---|---|
| T1 | `[BLANK_AUDIO]`, lower case, padded, `[Music]`/`[MUSIC]`/`(music)`, `[Silence]`, `[Silence].`, `(silence)`, repeated markers, marker + newline + marker, empty, spaces → blank |
| T2 | `estado`, `salir`, `Completo.`, `armar`, `See you in the next step`, `Hola [Music]`, `[BLANK]`, `BLANK_AUDIO`, `music` → not blank |
| T3 | voice-only with STT `[BLANK_AUDIO]`, `[Music]`, `salir`: no marker printed, no "No se pudo interpretar", no "STT no disponible", one `[voz]` echo (`salir`), 3 recordings/cues; cancel → blank → cancel keeps the session |
| T4 | STT `armar`, `estado`, `salir` still echo and reach the brain (arm Skill, Continuity) |
| T5 | guide mentions `[BLANK_AUDIO]`, T59 and `-l es`; no speech/lang-detect deps; tip-pin, ESC, AuthoritySource guards |

```text
pytest tests/test_assistant_voice_blank_stt_take_b1.py -q   → 5 passed
pytest -q (final)                                            → 4091 passed, 9 skipped, 0 failed (T58 tip 4086 → +5)
```

## 4. Remaining risks / notes

- whisper sometimes hallucinates real-looking text on silence (e.g. "Gracias.", "Subtítulos por…"); those are words, so they still reach the brain (lock 4 — no NLU/language filter). `-l es` reduces it.
- Marker set is closed; a new engine marker needs a one-line addition (own IC per lock 3's "closed set").
- Not live-tested with whisper (IC acceptance smoke).
