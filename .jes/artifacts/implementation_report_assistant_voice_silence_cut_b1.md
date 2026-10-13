# Implementation Report — Voice-only silence cut (`B1-assistant-voice-silence-cut`, T54 / V10)

**Project:** Jarvis
**Date:** 2026-10-13
**Implementer:** Claude Code (Engineer paste)
**Contract:** [IC](implementation_contract_assistant_voice_silence_cut_b1.md) · [V10-DC](design_contract_assistant_voice_silence_cut_b0.md)
**Parent:** tip `v0.8.0` (T53 ★)
**Status:** **Implemented** — await Cursor review → Engineer ACCEPT → tag `v0.8.1`. No ACCEPT claimed.
**Package:** `0.8.0` → **`0.8.1`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `scripts/voice/record_turn.sh` | **The silence cut.** With ffmpeg (avfoundation/pulse/alsa) and `S > 0`, ffmpeg runs in the background with its built-in `silencedetect=noise=$NOISE:d=$S` filter (`-nostdin -nostats`), its log goes to a FIFO, and the script watches it: `silence_end` ⇒ sound was heard; a `silence_start` after sound — or stamped past `0.05 s`, i.e. speech came first — means `S` seconds of continuous silence have already elapsed ⇒ `kill -TERM` ffmpeg, which finalizes the wav (exit 255 treated as success only when the script made the cut; the non-empty check still applies). `-t {seconds}` stays the hard cap; no speech ⇒ no cut ⇒ runs to the cap (lock 7). `S = 0` ⇒ the exact pre-T54 fixed command. INT/TERM trap stops ffmpeg so Ctrl-C never leaves it holding the mic. arecord-only hosts can't detect silence: fixed duration + stderr note. New envs: `JARVIS_RECORD_SILENCE_SECONDS` (unset → 1; empty/0 → fixed; negative/unparseable → 1) and `JARVIS_RECORD_SILENCE_NOISE` (default `-35dB`). `--check` reports the effective cut. |
| `src/jarvis/adapters/voice/external_record.py` | `JARVIS_RECORD_SILENCE_SECONDS_ENV`, `DEFAULT_RECORD_SILENCE_SECONDS = 1.0`, `resolve_record_silence_seconds()` (same rules as the script) — **cue only**. `record_audio_file` unchanged (lock 4). Exported from `adapters/voice`. |
| `src/jarvis/adapters/cli/main.py` | `_record_cue(max, silence)`: `Grabando (máx {M} s; corta con ~{S} s de silencio)…` when `S > 0`, `Grabando {M} s…` when `S = 0` — print-only. Voice-only banner reworded the same way (it said "graba 7 s", no longer true). `run_voice_only` docstring. Nothing else. |
| `tests/test_assistant_voice_silence_cut_b1.py` | **new** T1–T6 + T2b (see §3) |
| `tests/test_assistant_voice_only_loop_b1.py` | T2 cue count made cue-text-agnostic (`"Jarvis > Grabando"`) — one cue per recording either way |
| `docs/USER_GUIDE_VOICE.md` | §1, §4 setup/sample session/new "se cierra cuando dejas de hablar" bullet, §7 cheatsheet, §8 limits (level-based, not voice-based) |
| `engineer_note_chat_spoken_continuity_map.md` | tip; "Shipped silence cut (T54)"; banner + cue rows reworded — both still **screen-only**, no new spoken surface |
| `pyproject.toml` · PLATFORM · CONNECTIONS · cola · PRIORIDAD · state | `0.8.1`; short T54 notes; T54 → Implemented. No new C-xxx, no new dependency |

**Untouched:** STT/TTS, `spoken_continuity`, `speak_sanitize`, session brain, two modes, orchestrator, Continuity. T53 exit/cancel/config-missing/ephemeral-wav behavior unchanged (T4 + the T53 file re-run green).

**Separate commit before this one:** Cursor's uncommitted V10-DC + T54 IC + cola/PRIORIDAD/state edits, committed as found.

## 2. Verified against real ffmpeg (no mic)

A PATH shim replaced `-f avfoundation -i :0` with a real-time `lavfi` source and ran the real `record_turn.sh`:

| Source | Cap | Result |
|---|---|---|
| 1.2 s tone, then silence, `S = 1.0` | 7 s | cut at **2.22 s**, valid wav (ffprobe reads duration), exit 0 |
| silence only | 3 s | ran to **3.00 s** (no early cut) |
| continuous tone | 3 s | capped at **3.00 s** |

T2b keeps this as a test (skipped when ffmpeg isn't installed).

## 3. Tests

| ID | What it proves |
|---|---|
| T1 | `S=0` and `S=""`: real script runs ffmpeg **without** `silencedetect`, full window; voice-only with `S=0` prints `Grabando 7 s…`, `armar` → `salir` works, cue never spoken |
| T2 | real script + fake ffmpeg: speech→silence and speech-first scenarios stop **< 3 s** of a 5 s cap with a non-empty wav; args carry `silencedetect=…:d=1` and `-t 5`; default (unset) is silence mode; `run_voice_only` through the real wrapper prints the silence cue, runs `armar`, two turns finish well under two full windows |
| T2b | same early cut with **real ffmpeg** (synthetic lavfi), skip if absent |
| T3 | never-ending speech runs to the cap; silent room runs to the cap (no "empty room" early cut) |
| T4 | bare `--chat` never records; missing `JARVIS_RECORD_CMD` still ends voice-only honestly |
| T5 | Python resolver == script `--check` for unset/""/0/1.5/abc/-2; cue strings; guide tokens; no audio deps; tip-pin, ESC, AuthoritySource guards |
| T6 | default `S=1` with silence-ignoring T53 fakes: loop works, silence-style cue once per recording, never spoken |

```text
pytest tests/test_assistant_voice_silence_cut_b1.py -q   → 7 passed (~12 s; T1–T3 sleep through short real windows)
pytest -q                                                 → 4061 passed, 9 skipped, 0 failed (T53 tip: 4054 → +7 new)
```

## 4. Remaining risks / notes

- **Not live-tested on a real mic.** The real-ffmpeg check uses synthetic audio. Mic gain varies: if `-35dB` treats room noise as speech, turns run to the cap (safe failure, just slower) — `JARVIS_RECORD_SILENCE_NOISE` adjusts it. If a quiet speaker sits below the threshold, the first `silence_start` stamp > 0.05 s still requires *some* sound first; otherwise the cap applies.
- Level-based, not voice detection: a mid-sentence pause ≥ S ends the turn. Documented; tune S.
- macOS avfoundation and SIGTERM: verified with lavfi input, not with avfoundation itself. ffmpeg's SIGTERM handling is input-independent, but the live smoke (IC §3) is the real check.
- The suite gains ~12 s of wall time (T1–T3 deliberately run short real windows through the script).
