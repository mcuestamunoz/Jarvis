# Implementation Report — Cancel mid-TTS (`B1-assistant-voice-cancel-mid-tts`, T56 / V12)

**Project:** Jarvis
**Date:** 2026-10-14
**Implementer:** Claude Code (Engineer paste)
**Contract:** [IC](implementation_contract_assistant_voice_cancel_mid_tts_b1.md) · [V12-DC](design_contract_assistant_voice_cancel_mid_tts_b0.md)
**Parent:** tip `v0.8.2` (T54 ★ `v0.8.1`, T55 ★ `v0.8.2`)
**Status:** ★ **ACCEPT CLOSED** (2026-10-14) @ tip **`v0.8.3`**.
**Package:** `0.8.2` → **`0.8.3`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/adapters/voice/external_tts.py` | `speak_egress`: `subprocess.run` → `Popen(..., start_new_session=True)` + `communicate(input=…)`. On `KeyboardInterrupt`: `_stop_process_group` (SIGTERM the group → wait ≤ 2 s → SIGKILL sweep of the group → reap) then raise **`TtsCancelled`**. Sanitize-first, empty-text no-op, `TtsConfigError`/`TtsProcessError` semantics unchanged. |
| `src/jarvis/adapters/voice/__init__.py` | export `TtsCancelled` |
| `src/jarvis/adapters/cli/main.py` | `_chat_speak_fn(True)` (voice-only speaker) catches `TtsCancelled` → prints `Jarvis > Habla cancelada.` (never spoken) and returns; every speak call (replies, walls, goodbye) goes through it, so the loop continues to the next `read_line` → mic. Nothing else. |
| `tests/test_assistant_voice_cancel_mid_tts_b1.py` | **new** T1 (×2) – T6 |
| `docs/USER_GUIDE_VOICE.md` | §4 bullet: Ctrl-C while speaking → `Habla cancelada.`, mic again; Ctrl-C while recording → cancels that take; twice (while recording) exits |
| `engineer_note_chat_spoken_continuity_map.md` | new **screen-only** row `Habla cancelada (T56)`; tip line |
| `pyproject.toml` · PLATFORM · CONNECTIONS · cola · PRIORIDAD · state | `0.8.3`; short T56 notes; T56 → Implemented. No new C-xxx, no new dependency |

**Untouched:** mic reader (record cancel, double-Ctrl-C exit, config-missing end, ephemeral wav), silence cut / `record_turn.sh`, STT, Continuity, phrase tables, orchestrator, `--chat`.

**Separate commit before this one:** Cursor's uncommitted V12-DC + T56 IC + cola/PRIORIDAD/state edits, committed as found.

## 2. Judgment calls (lock 3 asks to document)

1. **Process group via `start_new_session=True`.** `piper_tts.sh` spawns `piper` and then a player (`afplay`/`aplay`/`paplay`); killing only the wrapper would leave the player talking. Running the command in its own session makes its pgid == its pid, so one `killpg` reaches wrapper + player. Side effect (intended): the terminal's Ctrl-C (SIGINT to the foreground group) reaches **only Jarvis**, which then stops the group itself — no race where the player dies but the wrapper reports a failure exit.
2. **`TtsCancelled(KeyboardInterrupt)`, not `TtsError`.** Existing `except TtsError` handlers (voice-only and the batch `_voice_speak_fn`) never print a cancel as "TTS no disponible". Callers that don't catch it — batch `--voice-fixture`/`--voice-audio` — keep plain Ctrl-C semantics (abort), now with the player actually stopped (lock 2: no new batch UX).
3. **Escalation.** SIGTERM first (lets a wrapper clean temp files), SIGKILL after 2 s if the direct child is still alive, then always one SIGKILL sweep of the group so a player that ignores SIGTERM can't keep talking. T1 covers both a TERM-respecting and a TERM-ignoring fake.
4. **Double-Ctrl-C exit counter stays record-only.** A mid-speech cancel does not count toward the T53 "second consecutive Ctrl-C while recording ends the session" rule.

## 3. Verification

- **Real player, real SIGINT (manual, no sound):** shell wrapper → `afplay -v 0` on a 20 s wav; SIGINT to the Python process → `TtsCancelled` after **0.81 s**; no `afplay` left running.
- Tests (mic/speaker-free; Ctrl-C = real SIGINT to the test process from a watcher thread once the fake TTS has started — same path as a terminal Ctrl-C):

| ID | What it proves |
|---|---|
| T1 [sigterm] / [sigkill-escalation] | `speak_egress` raises `TtsCancelled` (is `KeyboardInterrupt`, is **not** `TtsError`/`TtsProcessError`), returns long before the 30 s fake player, wrapper **and** child player pids gone — including when both ignore SIGTERM |
| T2 | `--voice-only`: reply speech cancelled → `Jarvis > Habla cancelada.`; `Sesión cerrada` exactly once (from the later spoken `salir`); a new `REC` follows the cancelled `TTS`; no "TTS no disponible"; pids gone |
| T3 | mid-record Ctrl-C → `Grabación cancelada`, session continues; two in a row end it (T53 unchanged) |
| T4 | bare `--chat` never records/speaks |
| T5 | decoration-only text → no invoke and no config error; text + no cmd → `TtsConfigError`; non-zero exit → `TtsProcessError` with stderr |
| T6 | guide mentions `Habla cancelada` + `Grabación cancelada`; map row is screen-only; deps/tip-pin/ESC/AuthoritySource guards |

```text
pytest tests/test_assistant_voice_cancel_mid_tts_b1.py -q   → 7 passed (~6 s; T1 escalation waits the 2 s grace)
pytest -q -k "voice or tts or chat" (after the seam change)  → 212 passed — existing TTS tests unaffected
pytest -q (final)                                            → 4074 passed, 9 skipped, 0 failed (T55 tip 4067 → +7)
```

## 4. Remaining risks / notes

- **Not live-tested with Piper speaking** (IC §3 smoke). The afplay check above covers the player-in-a-group case; Piper itself runs before the player and is in the same group.
- A Ctrl-C that lands **between** speech and the next record (e.g. while the brain is thinking) still propagates as before — unchanged, out of lock (T58 hotkey territory).
- Windows: `start_new_session`/`killpg` are POSIX; the voice scripts are POSIX-only already.
