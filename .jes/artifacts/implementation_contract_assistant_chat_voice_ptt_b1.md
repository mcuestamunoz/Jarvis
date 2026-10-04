# Implementation Contract — Chat voice push-to-talk (`B1-assistant-chat-voice-ptt`)

**Project:** Jarvis  
**Date:** 2026-10-04  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.7.5`**

**Status:** **IC ready** — paste to Claude = Buy. Cursor does **not** implement `src/` for this IC.  
**Parents:** [T46-DC](design_contract_assistant_chat_voice_ptt_b0.md) · [T45](implementation_review_assistant_chat_spoken_continuity_b1.md) @ `0.7.4` · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md) · tip **`0.7.4`**  
**Type:** Timed **push-to-talk** inside `--chat --voice-speak` — type `hablar`/`habla`, record externally, reuse T37 STT, feed transcript into the same `run_chat` loop (`TERMINAL` + T45 speak).  
**Opens:** **`0.7.5` / `v0.7.5`**. **Cola:** **T47**

**Not:** wake-word · always-on mic · barge-in · dual-Enter stop · PTT on `--voice` · `source=VOICE` · LLM · T40 · speech deps · ACCEPT claim · making bare `--chat` record or speak.

---

## Why this Buy

Engineer confirmed `--chat --voice-speak` talks until session end (typed input). Remaining gap: **speak into the air in that same session**. T46-DC locked PTT (not always-on). This IC implements that cut.

---

## 0. Engineer Buy (locked from T46-DC)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-chat-voice-ptt`** — PTT on the existing full-chat + speak REPL |
| 2 | **CLI** — no new flag. `--chat --voice-speak` already opted into voice; PTT is an intercept inside that session. Bare `--chat` never records |
| 3 | **Trigger** — typed line, after Continuity-style normalize (`strip` + `casefold` + NFKD accent-strip), is exactly `hablar` or `habla`. Consume it **once** at `input("User > ")`; do not put these strings in `CONTINUITY_DEFER_PHRASES` |
| 4 | **Record seam** — new thin `adapters/voice/` helper (name flexible, e.g. `record_audio_file`). Env `JARVIS_RECORD_CMD` with required `{output}` (optional `{seconds}`). Duration `JARVIS_RECORD_SECONDS` default **7**. Typed errors (`RecordConfigError` / `RecordProcessError` or equivalent). No audio decode in `capabilities/` / `intelligence/` / `core/`. No ffmpeg hardcoded in Python |
| 5 | **Cue** — print `Jarvis > Grabando {n} s…` **without TTS**. Then run record → `transcribe_audio_file`. Print `User > [voz] {transcript}`. Assign `user_input = transcript` and **fall through** the rest of `run_chat` unchanged (startup picker, `handle_user_text` **without** `source=VOICE`, T45 `spoken_text_for_wall` on walls). If STT returns `hablar`/`habla`, that is ordinary text this turn — **do not** record again |
| 6 | **Honesty** — missing/failed record or STT, empty transcript: print `Grabación no disponible: …` or `STT no disponible: …`; loop continues; no invented Skill. Ctrl-C during record/STT: `Grabación cancelada.` + continue (do not `break` the chat). Temp wav: write under tmp and unlink in `finally` |
| 7 | **Wrapper** — `scripts/voice/record_turn.sh`: `{output}` as argv or via the env template; 16 kHz mono wav; Darwin `ffmpeg -f avfoundation`; Linux ffmpeg alsa/pulse or `arecord`; `--check`; `JARVIS_RECORD_SECONDS`. Diagnostics on stderr; non-zero on every missing piece |
| 8 | **Guide + map** — `USER_GUIDE_VOICE.md`: §1 / §4.1 / cheatsheet / §8 — `--chat --voice-speak` now has `hablar` PTT; still not always-on; §5.3 stays one-shot `--voice-audio`. Living spoken-continuity map: add the new print surfaces (`Grabando…`, `User > [voz]`, record/STT honesty) as **screen-only**. PRIORIDAD · cola · short PLATFORM/CONNECTIONS (**no new C-xxx**) |
| 9 | **Version** `pyproject` → **`0.7.5`** — no speech deps |
| 10 | **Tests T1–T7** — fake RECORD + fake STT; no mic. Out: wake-word · `--voice` PTT · T40 · ACCEPT claim · changing T45 wall extract |

---

## 1. Files

| Path | Change |
|---|---|
| `src/jarvis/adapters/voice/external_record.py` | **new** `record_audio_file` + typed `RecordError` family + env names |
| `src/jarvis/adapters/voice/__init__.py` | export the record helper / errors (thin) |
| `src/jarvis/adapters/cli/main.py` | `run_chat`: PTT intercept when `speak_tts=True`; keep T42 source guard on `run_chat` (`speak_egress` / `JARVIS_TTS_CMD` / `_voice_speak_fn` / `TtsError` still absent from `run_chat` source) |
| `scripts/voice/record_turn.sh` | **new** operator wrapper (ffmpeg / arecord, `--check`) |
| `docs/USER_GUIDE_VOICE.md` | PTT as part of §4.1; honesty in §1 / §8; cheatsheet env + `hablar` |
| `.jes/artifacts/engineer_note_chat_spoken_continuity_map.md` | new print-surface rows (screen-only) |
| `tests/test_assistant_chat_voice_ptt_b1.py` | **new** T1–T7 |
| `pyproject.toml` | `0.7.4` → **`0.7.5`** |
| Docs / cola / state | T47 Implemented await review |

Prefer **not** touching `orchestrator.py`, Skills, `spoken_continuity.py` extract, or `run_voice_interactive`.

Phrase helper may live next to the record module (local normalize, same algorithm as T45 — do not import `assistant_task._normalize_for_continuity_match` across the fence).

---

## 2. Tests

Use a tiny **fake record script** that writes a placeholder wav to `{output}` (or `$1`) and a **fake STT script** that prints a known chat phrase (e.g. `armar` or `estado`) given any audio path. Wire `JARVIS_RECORD_CMD` / `JARVIS_STT_CMD`. Isolated tmp workspace. **No real mic.**

| ID | Assert |
|---|---|
| T1 | `run_chat(speak_tts=True)`, stdin `hablar` then `quit` (or equivalent), fake RECORD+STT printing `armar` → capsys contains `User > [voz] armar` **and** does **not** send `hablar` to `handle_user_text`; spy/record shows the Skill/`vehicle_arm_policy` path ran on `armar`. Fake TTS may capture the spoken Skill reply |
| T2 | Typed `armar` (no `hablar`) with speak on → never invokes record; keyboard path unchanged |
| T3 | `speak_tts=False`, typed `hablar` → record helper **not** called; no `Grabando` cue required |
| T4 | Missing `JARVIS_RECORD_CMD` or `JARVIS_STT_CMD` with speak on + `hablar` → honest printed message; loop survives (next line can `quit`); no invented Skill |
| T5 | Fake record or STT non-zero exit **or** empty STT stdout → honest printed message; loop survives |
| T6 | T42 guard still green (`run_chat` source has none of `speak_egress` / `JARVIS_TTS_CMD` / `_voice_speak_fn` / `TtsError`). `--voice` interactive import/smoke still works. T45 `test_assistant_chat_spoken_continuity_b1` still collected/green if run |
| T7 | `0.7.5` · no speech deps in `pyproject` · tip-pin + ESC green · guide mentions `hablar` / `habla` on `--chat --voice-speak` · map has the new screen-only rows · `record_turn.sh` exists and `--check` fails honestly when ffmpeg/arecord missing (or skip live `--check` if neither binary in CI; still assert the script is present and non-empty) |

If a full `run_chat` is heavy, T1 may monkeypatch `input` + isolate workspace like T43/T45 — but it must prove **trigger → transcript substitution → same chat brain**, not only the pure record helper.

Optional extra (nice, not required): fake STT prints `estado` → screen still has the Continuity wall (T45 Layer 1).

---

## 3. Acceptance

- [ ] `--chat --voice-speak`: type `hablar`, speak a Skill or `estado`, see `[voz]` transcript, hear T43/T45 reply; keyboard still works  
- [ ] Bare `--chat` does not record · `--voice` unchanged · `0.7.5` · guide + map updated  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.7.5`**

---

## 4. Paste for Claude

```text
Implementation — B1-assistant-chat-voice-ptt (T47)
Parent: T46-DC + T45 @ 0.7.4. Package → 0.7.5.

IC: .jes/artifacts/implementation_contract_assistant_chat_voice_ptt_b1.md
DC: .jes/artifacts/design_contract_assistant_chat_voice_ptt_b0.md
Guide: docs/USER_GUIDE_VOICE.md
Map: .jes/artifacts/engineer_note_chat_spoken_continuity_map.md

Push-to-talk on --chat --voice-speak. NOT always-on. NOT --voice. NOT source=VOICE.

- Intercept typed hablar / habla only (same normalize as Continuity:
  strip + casefold + NFKD accent-strip). Exact match. Once per input()
  line — do NOT re-intercept if STT returns hablar.
- speak_tts=True only. Bare --chat: hablar is ordinary text.
- Print "Jarvis > Grabando {n} s…" WITHOUT speaking (no TTS bleed).
- JARVIS_RECORD_SECONDS default 7. Timed capture, not dual-Enter.
- New adapters/voice/external_record.py: JARVIS_RECORD_CMD with
  required {output} (optional {seconds}). Typed RecordError family.
- Then existing transcribe_audio_file / JARVIS_STT_CMD.
- Print "User > [voz] {transcript}" then fall through the SAME
  run_chat loop (TERMINAL, Continuity, craft, T45 walls).
- Honesty: Grabación/STT no disponible; loop survives; no invented
  Skill. Ctrl-C during record → Grabación cancelada, continue.
- scripts/voice/record_turn.sh (ffmpeg avfoundation / alsa|pulse /
  arecord, 16kHz mono, --check). No speech deps in pyproject.
- Keep T42 run_chat source guard (no speak_egress / JARVIS_TTS_CMD /
  _voice_speak_fn / TtsError in run_chat source).
- Do NOT add hablar to CONTINUITY_DEFER_PHRASES.
- Do NOT add PTT to --voice. Do NOT use run_voice_turn for this path.
- Tests T1–T7: fake RECORD+STT, no mic. Guide + living map (new
  prints = screen-only). pyproject 0.7.5.
NO ACCEPT claim · NOT wake-word · NOT T40 · NOT LLM · NOT --voice PTT
```
