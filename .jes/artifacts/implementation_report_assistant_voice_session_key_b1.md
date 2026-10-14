# Implementation Report — In-session cancel key (`B1-assistant-voice-session-key`, T58 / V12)

**Project:** Jarvis
**Date:** 2026-10-14
**Implementer:** Claude Code (Engineer paste)
**Contract:** [IC](implementation_contract_assistant_voice_session_key_b1.md) · [V12-DC](design_contract_assistant_voice_cancel_mid_tts_b0.md)
**Parent:** tip `v0.8.4` (T56 ★, T57 ★)
**Status:** **Implemented** — await Cursor review → Engineer ACCEPT → tag `v0.8.5`. No ACCEPT claimed.
**Package:** `0.8.4` → **`0.8.5`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/adapters/voice/session_keys.py` | **new**, stdlib only. `SessionKeyWatcher(fd, interrupt, set_cbreak=)`; `for_terminal()` → watcher on stdin **only** when it is a TTY and this process is the terminal's foreground group, else `None`; `watching(keys)` context: cbreak mode (single keys, no echo, ISIG kept so Ctrl-C still works), short-lived thread that blocks SIGINT for itself and `select`s stdin every 50 ms; a matching key → `window.fired = True` + `interrupt()`; on exit the thread is joined and the saved terminal mode restored (in its own `finally`). `SPEAK_CANCEL_KEYS = {Esc, Space}`, `TAKE_CANCEL_KEYS = {Esc}`. |
| `src/jarvis/adapters/cli/main.py` | `run_voice_only` builds `SessionKeyWatcher.for_terminal()` and passes it to `_run_chat_session(keys=)` → `_chat_speak_fn(speak_tts, keys)` and `_make_mic_line_reader(keys)`. Speaker: `speak_egress` inside `keys.watching(SPEAK_CANCEL_KEYS)`; existing `TtsCancelled` catch unchanged; plus `KeyboardInterrupt` with `window.fired` → same `Habla cancelada.` (key pressed just as speech ended on its own). Mic reader: settle + record + STT inside `keys.watching(TAKE_CANCEL_KEYS)`, inside the existing record `try`. Banner line `Esc o Espacio cortan el habla; Esc cancela la toma mientras graba.` only when a watcher exists. `from contextlib import nullcontext`. |
| `src/jarvis/adapters/voice/external_tts.py` | **unchanged** — the T56 Ctrl-C path is the cancel path |
| `tests/test_assistant_voice_session_key_b1.py` | **new** T1/T2 (real pty, Esc + Space), T1b, T3–T6 |
| `docs/USER_GUIDE_VOICE.md` | §4 sample banner + Esc/Space bullet; §8 limit (terminal-only, not while thinking, arrows start with Esc) |
| map · PLATFORM · CONNECTIONS · cola · PRIORIDAD · state · `pyproject` | banner row wording + tip; short T58 notes; T58 → Implemented; `0.8.5`. No new C-xxx, no new dependency, **no new Habla string** |

**Untouched:** `speak_egress` / TTS group stop, `record_audio_file`, `record_turn.sh`, settle default, Continuity, orchestrator, `--chat` (never builds a watcher).

**Separate commit before this one:** Cursor's uncommitted T58 IC + V12-DC sync + cola/PRIORIDAD/state edits, committed as found.

## 2. Watcher approach (lock 6 — document the judgment)

1. **A key acts as a literal Ctrl-C.** On a match the production watcher calls `os.killpg(os.getpgrp(), SIGINT)` — the signal the terminal sends on Ctrl-C to the foreground group. Everything downstream is the already-reviewed code:
   - during TTS, `speak_egress` (blocked in `communicate`) gets `KeyboardInterrupt` → stops the TTS **process group** (its own session since T56, so the group signal never reaches it directly) → `TtsCancelled` → `Habla cancelada.`;
   - during settle/record/STT, the mic reader's take-cancel runs, **and** the recorder in the foreground group gets the same SIGINT, so `record_turn.sh`'s INT trap stops ffmpeg. Signalling only Python would make `subprocess.run` SIGKILL the wrapper and orphan ffmpeg on the mic until the cap — the reason for the group signal.
2. **Only where a real Ctrl-C would land.** `for_terminal()` requires stdin to be a TTY whose foreground group is ours (`tcgetpgrp == getpgrp`). Piped stdin, a background job or CI → `None` → no keys, no banner line.
3. **Main-thread delivery.** The watcher thread blocks SIGINT (`pthread_sigmask`), so the kernel delivers it to the main thread, interrupting its blocked `select`/`wait` and raising `KeyboardInterrupt` there.
4. **Windows only.** The watcher exists only for a speech call or a settle+record+STT take; nothing reads keys during the project picker (`input()` keeps canonical mode), during the brain/LLM wait (lock 7 — T56 N2 residual stays), or in `--chat`.
5. **Space during settle/record is ignored** (lock 4 choice): a bumped space bar must never throw away a take. Esc there = Ctrl-C there (cancel take; second consecutive cancel — Esc or Ctrl-C — ends the session). Existing string `Grabación cancelada. (Ctrl-C otra vez…)` kept (lock 9: no new strings); the guide says Esc counts the same.
6. **Race:** a key pressed exactly as speech finishes by itself can surface as plain `KeyboardInterrupt` after `speak_egress` returned; the speaker treats it as the same cancel when its window fired.

## 3. Tests

| ID | What it proves |
|---|---|
| T1 / T2 | **Real pseudo-terminal** (`pty.fork`): child process owns the pty, production `for_terminal()` returns a watcher, Esc (T1) / Space (T2) typed into the master mid-speech → `TtsCancelled` with `window.fired`, not `TtsProcessError`; terminal back in canonical mode (`ICANON True`); wrapper + child "player" pids gone |
| T1b | under pytest (no owned terminal) `for_terminal()` is `None`; key sets as documented |
| T3 | `--voice-only` with an injected pipe watcher: Esc mid-speech → banner line, `Habla cancelada.`, `Sesión cerrada` once (later `salir`), a new `REC` after the cancelled `TTS`, pids gone |
| T4 | Esc during settle → `Grabación cancelada`, cancelled take never reaches the recorder, session continues; Space during settle ignored; Esc in two consecutive takes → session ends with 0 recordings |
| T5 | bare `--chat` never calls `for_terminal()` / records / speaks; with no watcher, real SIGINT mid-TTS still → `Habla cancelada.` (T56 regression), no key banner |
| T6 | guide mentions Esc/Espacio; no key/audio deps; no global-hotkey APIs in `session_keys.py`; tip-pin, ESC, AuthoritySource guards |

```text
pytest tests/test_assistant_voice_session_key_b1.py -q   → 8 passed
pytest -q -k "voice or tts or chat" (after wiring)        → 224 passed — existing tests unaffected (no TTY under pytest)
pytest -q (final)                                        → 4086 passed, 9 skipped, 0 failed (T57 tip 4079 → +7); T56+T58 files 5× repeated: 14/14 each
```

## 4. Remaining risks / notes

- **Not live-tested with Piper/a real mic** (IC §3). The pty tests exercise the real terminal path end to end with fakes.
- **Arrow keys** send `Esc [ …` and therefore count as Esc (guide §8).
- **Wrapper processes:** if Jarvis is launched through a wrapper that shares its process group, that wrapper receives the SIGINT on Esc exactly as it would on a real Ctrl-C (same equivalence, by design).
- Brain/LLM-wait cancel (T56 N2) still out of scope.
