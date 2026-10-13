# Implementation Report — Voice-only loop (`B1-assistant-voice-only-loop`, T53 / V9)

**Project:** Jarvis
**Date:** 2026-10-13
**Implementer:** Claude Code (Engineer paste)
**Contract:** [IC](implementation_contract_assistant_voice_only_loop_b1.md) · [V9-DC](design_contract_assistant_voice_two_mode_product_b0.md) · [INV ★](investigation_report_assistant_voice_two_mode_product_b0.md)
**Parent:** tip `v0.7.9` (T52 ★)
**Status:** **Implemented** — await Cursor review → Engineer ACCEPT → tag `v0.8.0`. No ACCEPT claimed.
**Package:** `0.7.9` → **`0.8.0`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/adapters/cli/main.py` | **One brain, two modes.** The former `run_chat` body is now `_run_chat_session(*, speak_tts, read_line, is_exit)`, unchanged turn handling (startup picker, Continuity walls via `spoken_text_for_wall`, `handle_user_text` + coherence, speak-as-printed). `run_chat()` = silent keyboard session (no `speak_tts` parameter any more). New `run_voice_only()` = same session with `speak_tts=True` and `_make_mic_line_reader()`. New `_print_voice_only_banner` (print-only). **Removed:** the T47 `is_ptt_trigger` intercept, `run_voice_interactive`. **CLI:** new `--voice-only`; `--voice` → stderr pointer, exit 2 (flag hidden from `--help`); `--voice-speak` without `--voice-fixture`/`--voice-audio` (covers `--chat --voice-speak`) → pointer, exit 2; `--chat --voice-only` → "choose a mode", exit 2. Help text marks fixture/audio/`--voice-speak` as batch/CI. |
| `tests/test_assistant_voice_only_loop_b1.py` | **new** T1–T8 (IC §3, one function per row) |
| T43 / T47 / T42 / T45 / T52 test files | re-homed — see §2 |
| `docs/USER_GUIDE_VOICE.md` | §1 two-mode table; §4 rewritten as `--voice-only` (setup, sample session, cadence, picker exception, exit, ephemeral wav); §4.1 Layer 1/2 unchanged in meaning; §4.2 failures; §4.3 `--chat` silent + retired combos exit 2; §5 batch/CI framed as non-daily; §6/§7/§8 aligned. No `--chat --voice-speak`, `` `hablar` ``, or bare `--voice` remain. |
| `.jes/artifacts/engineer_note_chat_spoken_continuity_map.md` | tip/legend; "Shipped voice-only loop (T53)" replaces the PTT paragraph; Table 1 is now `_run_chat_session`'s surfaces with new rows: voice-only banner, Grabando cue, `[voz]` echo, Grabación/STT no disponible, Grabación cancelada (double Ctrl-C), retired-mode pointers — all **screen-only** |
| `scripts/voice/record_turn.sh` · `whisper_stt.sh` | usage comments only (point at `--voice-only`) — no behavior change |
| `pyproject.toml` | **`0.8.0`** — no new dependency |
| PLATFORM · CONNECTIONS · cola · PRIORIDAD · state | short T53 notes; T53 → Implemented, await Cursor review. No new C-xxx. |

**Not touched:** `adapters/voice/*` (record/STT/TTS/spoken_continuity/speak_sanitize/fixture_loop — `is_ptt_trigger` stays exported, now unused by the product), orchestrator, Skills registry, Continuity, `render_*`.

**Separate commit before this one:** Cursor's uncommitted T53-inv / V9-DC / T53 IC + cola/PRIORIDAD/state edits were committed as found (`Deliver T53-inv findings, V9-DC two-mode product, and T53 IC @ 0.8.0.`) so this Buy's diff to those files is reviewable on its own.

## 2. Pre-existing tests retired / re-homed (intentional — IC §1)

| File | Retired (behavior removed by locks 5/7) | Kept / re-homed |
|---|---|---|
| `test_assistant_chat_voice_ptt_b1.py` (T47) | T1 `hablar` records, T2 typed Skill no record, T4 missing record config under hybrid, T5c transcript "hablar" | T3 bare chat `hablar` never records; T4b/T5/T5b honesty (missing STT config, record process failure, empty transcript) now via `run_voice_only`; T6 → no PTT intercept in chat, `run_voice_interactive` gone; T7 guards (guide now asserts `` `hablar` `` absent) |
| `test_assistant_chat_voice_speak_b1.py` (T43) | T1 hybrid speaks, T3 hybrid missing TTS, T4 `run_voice_interactive` import | T2 bare chat never speaks; T5 guards (guide must **not** teach `--chat --voice-speak`) |
| `test_assistant_voice_interactive_cli_b1.py` (T42) | T1/T2 REPL turns | T1 → `--voice` exit 2 + pointer; T3 → `run_voice_turn` still tags `source=VOICE` (CI seam); T4 run_chat TTS source guard; T5 guide must **not** teach bare `--voice` |
| `test_assistant_chat_spoken_continuity_b1.py` (T45) | — | T2/T3/T3b/T4/T5 now drive `run_voice_only` (picker typed, turns from fake mic); same Layer 1/2 assertions |
| `test_assistant_voice_full_spoken_b1.py` (T52) | — | T7 e2e via `run_voice_only`; wall-site source guard moved to `_run_chat_session` |

Collected tests unchanged at 4063: −8 retired, +8 new.

## 3. Design decisions inside the locks (flag for review)

1. **Missing record/STT *config* ends the session** (honest message + `Sesión cerrada.`), while process failures / empty transcripts reopen the mic (lock 13). A missing env var can never succeed; with the mic as the only input, "loop survives" would be an endless print loop with no way to type `exit`. T5 asserts both behaviors.
2. **Second consecutive Ctrl-C while recording ends the session.** Lock 10 says Ctrl-C mid-record cancels the turn and continues; but voice-only is recording almost all the time, so without this there is no keyboard exit at all. The cancel message says so; a completed turn resets the counter.
3. **Exit words in voice-only** = `exit`/`quit`/`salir`, casefolded, **trailing punctuation ignored** (whisper usually emits `Salir.`). `--chat` keeps exactly `exit`/`quit` as before.
4. **`--chat --voice-only`** → exit 2 ("choose a mode") rather than silently picking one.
5. **`--voice` kept as a hidden flag** (`argparse.SUPPRESS`) only to print the redirect; it is no longer in `--help`.

## 4. Tests executed

```text
pytest tests/test_assistant_voice_only_loop_b1.py -q            → 8 passed
pytest <T42/T43/T45/T47/T52 re-homed files> -q                   → all passed
pytest -q                                                        → 4054 passed, 9 skipped, 0 failed
clean tip (worktree @ 6fd8f79, same 4063 collected)              → 4043 passed, 20 skipped
  (worktree lacks some gitignored data → 11 extra skips there; not a regression)
python -m jarvis.main --voice / --chat --voice-speak / --voice-speak / --chat --voice-only → exit 2 + pointer
```

## 5. Remaining risks / notes

- **Not live-tested with a real mic/whisper/Piper.** All voice-only tests use fake RECORD/STT/TTS scripts per the IC; the Engineer's live smoke is the real acceptance (§4 of the IC).
- **FULL phrase via STT:** `is_full_continuity_request` compares the exact normalized phrase; whisper punctuation (`Completo.`) would not match → brief spoken that turn. Pre-existing T45 behavior, not changed here (spoken_continuity out of scope); guide §8 notes the transcript decides.
- Ctrl-C outside the record window (while the brain or TTS runs) propagates as before in `run_chat` — unchanged behavior, not addressed.
- `is_ptt_trigger` / `PTT_TRIGGER_PHRASES` remain exported from `adapters/voice` but unused by the product (IC: don't rewrite voice modules). Candidate cleanup for a later IC.
