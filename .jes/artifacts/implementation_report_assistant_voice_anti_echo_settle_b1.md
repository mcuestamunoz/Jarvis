# Implementation Report — Anti-echo settle post-TTS (`B1-assistant-voice-anti-echo-settle`, T57 / V12)

**Project:** Jarvis
**Date:** 2026-10-14
**Implementer:** Claude Code (Engineer paste)
**Contract:** [IC](implementation_contract_assistant_voice_anti_echo_settle_b1.md) · [V12-DC](design_contract_assistant_voice_cancel_mid_tts_b0.md)
**Parent:** tip `v0.8.3` (T56 ★)
**Status:** **Implemented** — await Cursor review → Engineer ACCEPT → tag `v0.8.4`. No ACCEPT claimed.
**Package:** `0.8.3` → **`0.8.4`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/adapters/voice/external_record.py` | `JARVIS_VOICE_SETTLE_SECONDS_ENV`, `DEFAULT_VOICE_SETTLE_SECONDS = 0.35`, `resolve_voice_settle_seconds()`: unset → 0.35 · empty/`0` → 0 (no settle) · negative/unparseable → 0.35 (same style as `resolve_record_silence_seconds`). `record_audio_file` unchanged. Exported from `adapters/voice`. |
| `src/jarvis/adapters/cli/main.py` | `_make_mic_line_reader`: after the print-only `Grabando` cue, `time.sleep(settle)` (when > 0) **inside** the existing record `try`, immediately before `record_audio_file`. Module-level `import time`. Docstring. Nothing else. |
| `tests/test_assistant_voice_anti_echo_settle_b1.py` | **new** T1–T5 |
| `tests/test_assistant_voice_only_loop_b1.py` | shared `_FakeVoice` fixture sets `JARVIS_VOICE_SETTLE_SECONDS=0` so the T53–T56 loop tests keep their timing; T57 tests set the env explicitly (incl. unset = default) |
| `docs/USER_GUIDE_VOICE.md` | §4 setup env line + bullet (pause, tune, `0` disables, Ctrl-C during it); §8 limit (fixed wait, not echo detection) |
| map · PLATFORM · CONNECTIONS · cola · PRIORIDAD · state · `pyproject` | tip line only (no new surface); short T57 notes; T57 → Implemented; `0.8.4`. No new C-xxx, no new dependency |

**Untouched:** `speak_egress` / cancel kill path, `record_turn.sh` (silence cut), STT, Continuity, cue text (`_record_cue`), `--chat`, orchestrator.

**Separate commit before this one:** Cursor's uncommitted T57 IC + V12-DC sync + cola/PRIORIDAD/state edits, committed as found.

## 2. Choices (lock 6 asks to document)

1. **Ctrl-C during the settle = Ctrl-C while recording.** The sleep sits inside the same `try` as `record_audio_file`, so the existing handler applies unchanged: first press → `Grabación cancelada. (Ctrl-C otra vez para cerrar la sesión)` and the mic reopens; a second consecutive press (settle or recording) ends the session. Never ends on a single press. One rule for the whole "take" instead of a separate quiet-skip path.
2. **Placement: after the cue, before record** (IC preference): the user sees `Grabando…`, then a brief quiet, then the recorder starts. The temp wav already exists during the settle and is still unlinked in `finally`.
3. **After a mid-TTS cancel** there is no special case: every take goes through the same settle (T3 proves `TTS(cancelled) → SLEEP → REC`).
4. **Applies to every voice-only take**, including the first one of a session (no previous speech) — simplest honest rule, 0.35 s.

## 3. Tests

Sleep spy on `jarvis.adapters.cli.main.time` writes `SLEEP <s>` into the same event log the fake RECORD writes `REC` to.

| ID | What it proves |
|---|---|
| T1 | default: one `0.35` sleep per take, each `REC` immediately preceded by `SLEEP 0.35`; cue text unchanged; `0` and empty → no sleep, recordings still happen |
| T2 | resolver: unset 0.35 · "" 0 · "0" 0 · "0.5" · "1" · "-1" → 0.35 · "abc" → 0.35; session with `0.5` settles 0.5 before every `REC` |
| T3 | after a real mid-TTS cancel (T56 blocking TTS + real SIGINT): `Habla cancelada.`, then `SLEEP` → `REC` |
| T4 | Ctrl-C during settle → `Grabación cancelada`, session continues; twice → session ends with 0 recordings; bare `--chat` never sleeps/records; silence-cut cue strings unchanged |
| T5 | guide mentions the env; no audio deps; tip-pin, ESC, AuthoritySource guards; `record_turn.sh` has no settle logic |

```text
pytest tests/test_assistant_voice_anti_echo_settle_b1.py -q   → 5 passed
pytest -q (final)                                             → 4079 passed, 9 skipped, 0 failed (T56 tip 4074 → +5)
```

## 4. Remaining risks / notes

- **Not live-tested.** Whether 0.35 s is enough depends on the speaker/room; it's a fixed wait, not echo detection (guide §8). Tunable per operator.
- A settle that is too long could clip the start of a fast reply from the user; `0` restores T56 timing.
- The settle adds 0.35 s of latency to every voice-only turn by default.
