# Implementation Report — Chat voice push-to-talk (`B1-assistant-chat-voice-ptt`, T47)

**Project:** Jarvis
**Date:** 2026-10-05
**Implementer:** Claude Code (Engineer paste)
**Contract:** [`implementation_contract_assistant_chat_voice_ptt_b1.md`](implementation_contract_assistant_chat_voice_ptt_b1.md)
**Parents:** [T46-DC](design_contract_assistant_chat_voice_ptt_b0.md) · [T45](implementation_report_assistant_chat_spoken_continuity_b1.md) @ `0.7.4` · [living map](engineer_note_chat_spoken_continuity_map.md) · [cola note](engineer_note_voice_phase_c_cola.md)
**Status:** **Implemented** — await Cursor review → Engineer ACCEPT → tag **`v0.7.5`**.
**Package / tag:** `0.7.5` / pending **`v0.7.5`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/adapters/voice/external_record.py` | **new.** `record_audio_file(output_path, *, seconds=None, command_template=None, env_var=JARVIS_RECORD_CMD_ENV)` — runs the external `JARVIS_RECORD_CMD` template (required `{output}`, optional `{seconds}`) via `shlex.split` + `subprocess.run` (no shell). Typed `RecordError` family: `RecordConfigError` (missing/malformed template) and `RecordProcessError` (non-zero exit, unrunnable binary, or a `0` exit with no/empty output file — never a silent "recorded nothing" success). `resolve_record_seconds()` reads `JARVIS_RECORD_SECONDS` (default `7`, falls back on an unparseable value rather than crashing). `is_ptt_trigger(raw_text)` — the locked exact-match `hablar`/`habla` trigger, using a **local** copy of the Continuity-style normalize (`strip` + `casefold` + NFKD accent-strip), not imported across the `assistant_task`/`spoken_continuity` fence, for the same DC/IC reason those modules already document |
| `src/jarvis/adapters/voice/__init__.py` | re-exports `record_audio_file`/`resolve_record_seconds`/`is_ptt_trigger`/`DEFAULT_RECORD_SECONDS`/`JARVIS_RECORD_CMD_ENV`/`JARVIS_RECORD_SECONDS_ENV`/`PTT_TRIGGER_PHRASES`/`RecordError`/`RecordConfigError`/`RecordProcessError` |
| `src/jarvis/adapters/cli/main.py` | `run_chat`: when `speak_tts=True`, each typed line is checked against `is_ptt_trigger` **once**, immediately after the blank-line guard and before the `exit`/`quit`/`help`/startup-selection checks. On a match: prints `Jarvis > Grabando {n} s…` (plain `print`, never `speak()` — no TTS bleed over the mic), records to a `tempfile.mkstemp` wav (unlinked in a `finally`), then calls the existing T37 `transcribe_audio_file`. Success prints `User > [voz] {transcript}` and reassigns `user_input = transcript`, which then falls through the rest of the loop unchanged — same `handle_user_text` call (no `source=VOICE`), same T45 wall extraction, same startup-selection/exit/help checks applied to the transcript exactly as they would to typed text. `RecordError`/`SttError` each print an honest `Grabación no disponible: …`/`STT no disponible: …` and `continue` (loop survives); `KeyboardInterrupt` during record/STT prints `Grabación cancelada.` and `continue`s rather than breaking the session. Bare `--chat` (`speak_tts=False`) never evaluates `is_ptt_trigger` — `hablar` stays ordinary text. T42's structural `inspect.getsource(run_chat)` guard (no `speak_egress`/`JARVIS_TTS_CMD`/`_voice_speak_fn`/`TtsError` literal in `run_chat`'s source) is unaffected — this PTT block only ever calls `record_audio_file`/`transcribe_audio_file`, never the TTS seam |
| `scripts/voice/record_turn.sh` | **new** operator wrapper: `record_turn.sh <output.wav> [seconds]` or `--check`. Picks a recorder per platform (`ffmpeg -f avfoundation` on Darwin; `ffmpeg -f pulse`/`-f alsa` or `arecord` on Linux), captures 16 kHz mono, and exits non-zero with a diagnostic on stderr for every missing piece (no recorder on `PATH`, the chosen tool failing, or a `0` exit producing no/empty output) — never a silent success |
| `docs/USER_GUIDE_VOICE.md` | New §4.1.1 "Hablarle de verdad — `hablar`" documents the trigger, the fixed-duration capture, the `JARVIS_RECORD_CMD`/`JARVIS_RECORD_SECONDS` env, the `--check` step, and the honesty messages. §1's "Qué no es" bullet rewritten to name the two exact moments the mic turns on (`hablar`/`habla` and `--voice-audio`). §8 gained a "No finge que grabó" honesty bullet, a cheatsheet block (`JARVIS_RECORD_CMD`/`JARVIS_RECORD_SECONDS`/`--check`/`User > hablar`), and a PTT-duration gotcha bullet; the old "ni `--voice` ni `--chat --voice-speak` son micrófono" bullet was rewritten to point at the new PTT path instead of only `--voice-audio` |
| `.jes/artifacts/engineer_note_chat_spoken_continuity_map.md` | Table 1 gained five new rows for the PTT print surfaces (`Grabando` cue, `[voz]` transcript echo, `Grabación no disponible`, `STT no disponible`, `Grabación cancelada`), all classified **screen-only** per the IC's lock 8 — none of them are spoken (the cue is deliberately print-only to avoid TTS bleeding into the recording; the honesty/cancel messages are operator diagnostics, same class as the existing TTS-honesty row) |
| `tests/test_assistant_chat_voice_ptt_b1.py` | **new** T1–T7 (10 test functions — T4/T5 each split into two to cover both the record-seam and STT-seam failure branches independently, same pattern T45 used for its FULL-phrase pair) |
| `pyproject.toml` | `0.7.4` → **`0.7.5`** — no new dependency |
| Docs / cola / state | `IMPLEMENTATION_TASKS.md` PRIORIDAD/cola/COLA header/T47 row · `PLATFORM_CAPABILITY_VISION.md` T46-DC/T47 paragraph · `CONNECTIONS.md` T46-DC/T47 paragraph (no new C-xxx) · `engineer_note_voice_phase_c_cola.md` tip-parent + T47 row · `engineering_state.json` · this IC's status line |

**Not touched:** `render_startup_context`/`render_response`/`spoken_continuity.py` (Layer 1 and the T45 extractor are both reused exactly as shipped — `spoken_text_for_wall` is still called on the same two wall sites, now possibly fed a voice-origin `user_input` for the FULL-phrase check, which is correct: a spoken "completo" should speak the full wall exactly like a typed one), `orchestrator.py`, `CONTINUITY_DEFER_PHRASES` (no entry added for `hablar`/`habla`, per lock 3), `run_voice_interactive`/`run_voice`/`run_voice_turn`/`run_voice_turn_from_audio` (T36/T38/T42, untouched — PTT never calls `run_voice_turn`), `AuthoritySource` (still no `"voice"`), `pyproject.toml`'s dependency lists (no ffmpeg/whisper/piper pin), tip-version pins (T17 green), ESC fence (T16, re-verified including the new `external_record.py` file).

---

## 2. Why the trigger lives in `external_record.py`, not a new module

The IC left the trigger-helper's home flexible ("Phrase helper may live next to the record module"). `is_ptt_trigger` was added to `external_record.py` itself rather than a third file, since both the record seam and the trigger match are small, share no other module, and `adapters/voice/__init__.py` already re-exports everything from there — splitting them would add a file with no other reason to exist. The normalize function (`_normalize`) is a private, literal duplicate of `spoken_continuity._normalize`/`assistant_task._normalize_for_continuity_match` — not imported, matching the fence those two modules already document for the same reason (DC/IC boundaries between `adapters/voice/` and `intelligence/` should not create a runtime import edge over a four-line string transform).

---

## 3. Proving "falls through the same loop", not a parallel path

The IC's own acceptance note flagged that T1 must prove *substitution into the same brain*, not just that the record helper works in isolation. `test_t1_hablar_records_transcribes_and_falls_through_same_chat` feeds `["hablar", "exit"]` as typed input with a fake record script (writes a placeholder wav) and a fake STT script (prints `armar`), then asserts the capsys output contains both `User > [voz] armar` **and** evidence that the Skill path actually ran (`vehicle_arm_policy`/`ARMADA` in the output) — i.e. the transcript was not just echoed but handed to the exact same `handle_user_text`/Skill dispatch a typed `armar` would hit. `test_t2` proves the inverse: typing a Skill phrase directly, with speak on, never touches the record seam at all (a marker file the fake record script would touch stays absent). `test_t5c` proves the "do not re-intercept" lock — a transcript that is literally `hablar` is treated as that turn's chat text and does not trigger a second recording (a counting script shows the record command ran exactly once).

---

## 4. Tests executed

```text
pytest tests/test_assistant_chat_voice_ptt_b1.py -v
→ 10 passed (T1, T2, T3, T4, T4b, T5, T5b, T5c, T6, T7)

pytest tests/ -q
→ 4026 passed, 9 skipped, 0 failed
```

Diffed against this branch's pre-T47 tip (before these edits): baseline was `4016 passed, 9 skipped, 0 failed` (T45's own reported baseline). **Zero regressions** — the delta is exactly the 10 new T47 tests. `git status` before committing shows exactly the files this IC's own file list names, plus the usual docs/cola/state bookkeeping.

The T7 test also re-verifies, live, that `record_turn.sh --check` fails loudly (non-zero exit, `"no recorder found"` on stderr) when `PATH` is stripped to a nonexistent directory — proving the honesty lock on the operator wrapper itself, not just the Python seam.

---

## 5. Remaining

None for this Buy. Out of scope per the IC (unchanged): wake-word, always-on capture, barge-in, dual-Enter stop, PTT on `--voice`, `source=VOICE`, any new Skill/intent, T40. Next steps are the Engineer's: Cursor review, and whether ACCEPT for T45/T47 gets bundled or tagged individually (T45 is still only Cursor PASS WITH NOTES, awaiting Engineer ACCEPT independently of this Buy).
