# Design Contract — Voice-only silence end-of-utterance (`DC-assistant-voice-silence-cut`)

**Project:** Jarvis  
**Date:** 2026-10-13  
**Author:** JES / Cursor  
**Status:** **DC ready** — next after T53 ★ @ `v0.8.0`. Engineer “siguiente ic” → this DC + T54 IC.  
**Type:** Block lock — **V10** polish on `--voice-only` record cut  
**Cola:** **V10-DC** / **T54-DC**  
**Parents:** [V9-DC ★](design_contract_assistant_voice_two_mode_product_b0.md) · [T53 review ★](implementation_review_assistant_voice_only_loop_b1.md) @ `v0.8.0` · [cola voz](engineer_note_voice_phase_c_cola.md) · tip **`v0.8.0`**

**Not** an Implementation Contract. **Not** wake-word · always-on · barge-in · T40 · greenfield voice rewrite · speech SDK in `pyproject`.

---

## Intent

After T53, `--voice-only` records a **fixed** window (`JARVIS_RECORD_SECONDS`, default 7). That works but forces the user to fill or wait out the whole window.

Engineer direction (2026-10-13, pre-V9 cola): build voice-only first with fixed cut; **then** polish with automatic stop when the user stops speaking.

This DC locks that polish so T54 stays a **record-cut** Buy — same brain, same STT/TTS, same two modes.

---

## Plan

| Step | Cola | Buy | Package | Scope |
|---|---|---|---|---|
| **This DC** | **T54-DC** | `DC-assistant-voice-silence-cut` | no bump | Locks below |
| Code | **T54** | `B1-assistant-voice-silence-cut` | **`0.8.1` / `v0.8.1`** | Silence-aware record cut for `--voice-only` |
| Later | own IC | wake-word / barge-in / FULL-phrase punctuation (T53 N2) | TBD | **Out of V10** |
| Parked | **T40** | craft/`world` | TBD | **Out** |

---

## Product picture (after V10 ★)

```text
--voice-only (unchanged cadence)
  → after Jarvis speak returns
  → start record (print-only cue)
  → stop when:
       (a) silence of S seconds after speech was heard, OR
       (b) max duration M seconds (existing JARVIS_RECORD_SECONDS)
  → STT → same chat brain → speak → repeat
```

`--chat` unchanged. No new product mode.

---

## Locks (block-level)

| # | Lock |
|---|---|
| 1 | **Scope = record cut only** — do not change Continuity Layer 1/2, STT/TTS contracts, Skill-first, or session brain. Voice-only loop cadence (mic after speak) stays T53 |
| 2 | **Silence stop is external** — detection lives in the **operator record command** (extend `scripts/voice/record_turn.sh` and/or add a sibling wrapper), **not** a new audio DSP package in `src/` / `pyproject`. Python `record_audio_file` stays “run external cmd → non-empty wav” |
| 3 | **Max duration remains** — `JARVIS_RECORD_SECONDS` (default **7**) is still a hard cap so a noisy room or mic fail cannot record forever |
| 4 | **Silence parameter** — new env e.g. `JARVIS_RECORD_SILENCE_SECONDS` (default **1.0**, positive float). Meaning: after speech energy has been detected, stop when continuous silence lasts ≥ this many seconds. If the whole window is silence (user never started), stop at max duration (or earlier only if the wrapper can honestly detect “no speech + silence” — IC may keep “always wait max when no speech” for honesty/simplicity; pick one and test it) |
| 5 | **Opt-out / fixed-only** — env e.g. `JARVIS_RECORD_SILENCE_SECONDS=0` (or unset policy locked in IC) forces **fixed-duration only** (T53 behavior) for CI/fakes that write a whole wav without real silence |
| 6 | **Cue honesty** — print-only cue must not lie. Prefer: `Grabando (máx {M} s, corta con silencio)…` or equivalent; never speak the cue. Exact string = IC |
| 7 | **Fake RECORD scripts in tests** — suite must stay mic-free. Silence path tested with a fake recorder that exits early when “silence mode” env is on, **or** tests set silence=0 and assert max-duration path; at least one test proves early-exit path when the fake simulates silence-cut |
| 8 | **Ephemeral wav + honesty** — unlink still; RecordError/SttError families unchanged in meaning. Ctrl-C cancel + double Ctrl-C exit (T53 judgment) unchanged |
| 9 | **Guide** — `USER_GUIDE_VOICE.md` documents silence cut + envs; still two modes only |
| 10 | **Package** — **`0.8.1` / `v0.8.1`**. No tip pins in tests |
| 11 | **Out of V10** — wake-word · always-on thread · barge-in (cut Jarvis mid-TTS) · dual-Enter stop · T40 · removing max duration · speech SDK in core · FULL-phrase punctuation normalize (T53 N2) · deleting unused `is_ptt_trigger` export (T53 N1) unless a one-line drive-by is free and tested — prefer **not** in this Buy |

---

## Opens

T54 IC: [`implementation_contract_assistant_voice_silence_cut_b1.md`](implementation_contract_assistant_voice_silence_cut_b1.md). Tip stays **`v0.8.0`** until T54 opens **`0.8.1`**.

SoT: [cola](engineer_note_voice_phase_c_cola.md) · [`docs/IMPLEMENTATION_TASKS.md`](../../docs/IMPLEMENTATION_TASKS.md) PRIORIDAD
