# Design Contract — Chat voice push-to-talk (`DC-assistant-chat-voice-ptt`)

**Project:** Jarvis  
**Date:** 2026-10-04  
**Author:** JES / Cursor  
**Status:** **DC ready** — Engineer *“dale”* after locking PTT (not always-on) on `--chat --voice-speak`.  
**Type:** Block lock — **V8** speak-into-the-air on the existing full-chat + speak path  
**Cola:** **T46-DC**  
**Parents:** [T45 review](implementation_review_assistant_chat_spoken_continuity_b1.md) @ `0.7.4` · [T44-DC](design_contract_assistant_chat_spoken_continuity_b0.md) · [T43 review](implementation_review_assistant_chat_voice_speak_b1.md) · [T37 STT ★](implementation_review_assistant_voice_stt_external_b1.md) · [voice channels DC ★](design_contract_assistant_chat_voice_channels_b0.md) · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md) §5.3 · tip **`0.7.4`**

**Not** an Implementation Contract. **Not** permission to implement until the T47 IC is pasted. **No wake-word. No always-on mic. No LLM. No new brain.**

---

## Intent

After T43 + T45, `--chat --voice-speak` is the product the Engineer uses: full Continuity / craft / LLM, typed `User > `, spoken replies (brief on Continuity walls). The remaining gap is **speak into the air inside that same session** — not `--voice` (Skills-only), not `--voice-audio` (one-shot, new process each time), not a daemon.

Engineer lock (2026-10-04):

> Push-to-talk on `--chat --voice-speak`. Not always-on. Not wake-word. Keyboard stays. Same chat brain.

This DC locks that cut so T47 stays a thin record → existing STT → existing `run_chat` loop Buy.

---

## Seams reused (inventory — Cursor, T45 tip `0.7.4`)

No separate Claude INV: the seams are already shipped. T47 wires them; it does not invent a parallel path.

| Seam | Where today | V8 reuse |
|---|---|---|
| Full-chat REPL | `run_chat` `src/jarvis/adapters/cli/main.py:949` — `input("User > ")` then `handle_user_text` default **`TERMINAL`** | **Keep.** PTT substitutes the typed line with a transcript, then falls through this same loop (startup picker, Continuity, craft, T45 walls). |
| Speak on chat | `_chat_speak_fn` + T45 `spoken_text_for_wall` on the two Continuity-wall sites | **Unchanged.** After PTT, T43/T45 speak rules still apply to the *transcript*, not to the trigger word `hablar`. |
| External STT | `transcribe_audio_file` / `JARVIS_STT_CMD` `{audio}` — `adapters/voice/external_stt.py` | **Reuse as-is.** PTT records a wav, then calls this. No second STT family. |
| One-shot audio CLI | `--voice-audio PATH` → `run_voice_audio` → `run_voice_turn` with `source=VOICE` | **Do not use for this cut.** That path is Skills-only + new orchestrator per invocation (latch does not survive). Engineer wants the **open chat session**. |
| Manual mic today | [USER_GUIDE_VOICE §5.3](../../docs/USER_GUIDE_VOICE.md): operator runs `ffmpeg`/`arecord`, then `--voice-audio` | **Replace for interactive use** with in-loop PTT. §5.3 stays valid as batch/one-shot. |
| Skills-only REPL | `--voice` / `run_voice_interactive` — `source=VOICE` | **Out of V8.** Do not add `hablar` there. |
| Bare `--chat` | `run_chat(speak_tts=False)` — T42 `inspect.getsource` guard: `run_chat` source must not mention `speak_egress` / `JARVIS_TTS_CMD` / `_voice_speak_fn` / `TtsError` | **Byte-identical.** `hablar` on bare `--chat` is ordinary text (no record). |
| Audio bytes | none in `capabilities/` / `intelligence/` / `core/` | **Keep.** Record + STT stay external processes. |

---

## Plan (cola V8)

| Step | Cola | Buy | Package | Scope |
|---|---|---|---|---|
| **This DC** | **T46-DC** | `DC-assistant-chat-voice-ptt` | no bump | Product locks |
| Code | **T47** | `B1-assistant-chat-voice-ptt` | **`0.7.5`** | Timed record seam + `hablar`/`habla` intercept on `--chat --voice-speak` |
| Later | own IC | always-on / wake-word / barge-in | TBD | **Out of V8** |
| Parked | **T40** | craft/`world` voice | TBD | **Out of V8** |

Each step independently ★-able. T47 must not wait on T41–T45 ACCEPT tags.

---

## Locks (block-level)

| # | Lock |
|---|---|
| 1 | **Same session, same brain** — PTT lives inside `run_chat` under `--chat --voice-speak`. Transcript feeds the **existing** loop (`handle_user_text` default `TERMINAL`, Continuity, craft, T45). Do **not** call `run_voice_turn` / `source=VOICE` for this path |
| 2 | **Push-to-talk, not always-on** — no background mic thread, no wake-word, no barge-in. Capture starts only when the operator types a locked trigger at `User > ` |
| 3 | **Trigger set (finite, zero-LLM)** — exact match after the same normalize family as Continuity defer / T45 FULL (`strip` + `casefold` + NFKD accent-strip): **`hablar`**, **`habla`**. Nothing else (`háblame`, `quiero hablar`, `hablar.` with period) starts a capture. Do **not** add these to `CONTINUITY_DEFER_PHRASES` |
| 4 | **Intercept once** — the trigger is consumed at the typed `input()` line only. After STT, the transcript is the user line for this turn; **do not** re-intercept if STT returns `hablar`/`habla` (that text falls through as ordinary chat) |
| 5 | **Keyboard stays** — any non-trigger line is unchanged (including `estado`, Skills, craft, `exit`). Empty line still `continue` |
| 6 | **PTT only with speak on** — intercept runs iff `speak_tts=True`. Bare `--chat`: `hablar` is not a record command |
| 7 | **Record = external process** — new thin helper in `adapters/voice/` (e.g. `external_record.py`) invokes `JARVIS_RECORD_CMD` with a required `{output}` placeholder (optional `{seconds}`). No ffmpeg/arecord hardcoded in Python. No speech SDK in `pyproject.toml`. Typed `RecordError` family (config / process), never a silent skip |
| 8 | **Timed capture, not dual-Enter** — duration from `JARVIS_RECORD_SECONDS` (default **7**). Print `Jarvis > Grabando {n} s…` **without speaking** (TTS would bleed into the mic). No “press Enter to stop” |
| 9 | **Then existing STT** — wav → `transcribe_audio_file` / `JARVIS_STT_CMD`. Show what was heard: `User > [voz] {transcript}` (print only). Then fall through as if the operator had typed that transcript |
| 10 | **Honesty** — missing `JARVIS_RECORD_CMD` / `JARVIS_STT_CMD`, non-zero record/STT, empty transcript: print `Grabación no disponible: …` or `STT no disponible: …` (print-only, like T43 TTS honesty); **do not** invent a Skill phrase; **do not** crash the loop; **do not** mark startup done. Ctrl-C during record/STT → `Grabación cancelada.` and continue (do not exit the session) |
| 11 | **Operator wrapper** — `scripts/voice/record_turn.sh` (ffmpeg avfoundation on Darwin / alsa or pulse on Linux, else `arecord`; 16 kHz mono wav; `--check`; honors `JARVIS_RECORD_SECONDS`). Same honesty style as `whisper_stt.sh` / `piper_tts.sh` |
| 12 | **`--voice` unchanged** · **`--voice-audio` unchanged** · T45 Layer 1/2 unchanged · T42 `run_chat` source guard unchanged (PTT helpers may be imported; `run_chat` still must not name `speak_egress` / `JARVIS_TTS_CMD` / `_voice_speak_fn` / `TtsError`) |
| 13 | **Out unless a later IC ★** — wake-word · always-on listen · barge-in · dual-Enter stop · PTT on `--voice` · `source=VOICE` for this path · LLM rewrite · T40 world · making bare `--chat` speak or record · speech deps in `pyproject` · ACCEPT claim |

---

## Operator picture (after T47)

```text
python -m jarvis.main --chat --voice-speak
User > hablar
Jarvis > Grabando 7 s…          # print only; mic is live
User > [voz] estado             # transcript echo
Jarvis >                        # full Continuity wall on screen
                                # ears: T45 brief (or wall if transcript was a FULL phrase)
User > armar                    # keyboard still works
```

Env: existing `JARVIS_TTS_CMD` + `JARVIS_STT_CMD`, plus `JARVIS_RECORD_CMD="$PWD/scripts/voice/record_turn.sh {output}"`.

---

## Opens

T47 IC: [`implementation_contract_assistant_chat_voice_ptt_b1.md`](implementation_contract_assistant_chat_voice_ptt_b1.md). Tip stays **`0.7.4`** until T47 opens **`0.7.5`**.

SoT: [phase cola](engineer_note_voice_phase_c_cola.md) · [`docs/IMPLEMENTATION_TASKS.md`](../../docs/IMPLEMENTATION_TASKS.md) PRIORIDAD
