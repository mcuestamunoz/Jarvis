# Implementation Review — Voice-only silence cut (`B1-assistant-voice-silence-cut`, T54 / V10)

**Project:** Jarvis  
**Date:** 2026-10-13  
**Reviewer:** Cursor (independent — not implementer)  
**Contract:** [IC](implementation_contract_assistant_voice_silence_cut_b1.md) · [V10-DC](design_contract_assistant_voice_silence_cut_b0.md) · [report](implementation_report_assistant_voice_silence_cut_b1.md)  
**Tip under review:** `9312fdd` on `cursor/chat-voice-ptt-impl-8ac5` · package **`0.8.1`**  
**Parent:** `v0.8.0` (T53 ★)

**Verdict:** **PASS WITH NOTES** → Engineer ★ **ACCEPT CLOSED** (2026-10-14) @ tip **`v0.8.1`** (`9312fdd`).

**Process note:** Independent Cursor review of record. Same-session self-PASS is not review of record. Engineer ★ ACCEPT CLOSED → tag **`v0.8.1`**. N1–N4 remain non-blocking (live mic smoke optional).

---

## 1. Scope check vs IC

| Lock / IC item | Evidence | Result |
|---|---|---|
| 1 · Buy `B1` · package `0.8.1` | `pyproject.toml` `version = "0.8.1"`; no speech SDK deps | **Pass** |
| 2 · Only `--voice-only` record path | Cue/banner in `run_voice_only`; `--chat` untouched (T4) | **Pass** |
| 3 · Silence in external recorder | `scripts/voice/record_turn.sh` ffmpeg `silencedetect` + watcher; free tools only | **Pass** |
| 4 · Python seam thin | `record_audio_file` unchanged (no `SILENCE` / `silencedetect` in source); `resolve_record_silence_seconds` cue-only | **Pass** |
| 5 · Max `JARVIS_RECORD_SECONDS` (7) | `-t "$DURATION"` always; T3 continuous tone → cap | **Pass** |
| 6 · `JARVIS_RECORD_SILENCE_SECONDS` default 1.0; `0`/empty → fixed | Script + Python resolver agree (T5); T1 fixed path | **Pass** |
| 7 · No-speech → wait max (no empty-room early cut) | T3 silent room → cap; report lavfi silence-only | **Pass** |
| 8 · Honest cue; never TTS | `_record_cue`: silence vs fixed; T1/T2/T6 never spoken | **Pass** |
| 9 · T53 exit/cancel/config-missing | T4 missing RECORD ends session; T53 suite still green | **Pass** |
| 10 · Guide | USER_GUIDE_VOICE silence envs + cue + limits | **Pass** |
| 11 · Tests T1–T6 | `test_assistant_voice_silence_cut_b1.py` (+ T2b real ffmpeg) | **Pass** |
| 12 · Out of scope | No wake-word, barge-in, Continuity rewrite, new C-xxx | **Pass** |
| Spoken-continuity map | Banner/cue rows updated; still **screen-only** | **Pass** |

**Not live-smoked** with a real mic — IC §3 remains the Engineer ACCEPT gate. Implementer verified early cut with synthetic lavfi through the real script (T2b).

---

## 2. Judgment calls (report) — **accepted**

IC allowed ffmpeg and/or sox. Cursor finds these **inside the spirit of the locks**:

| # | Choice | Review |
|---|---|---|
| 1 | ffmpeg `silencedetect` + FIFO log watcher + SIGTERM cut (not sox) | **Accept.** Free tool already in the operator story; `-t` cap kept; SIGTERM treated as success only when the script cut. |
| 2 | arecord-only hosts: fixed duration + stderr note | **Accept.** Lock 3 free-first; silence needs ffmpeg. Honest degradation, documented in guide. |
| 3 | Optional `JARVIS_RECORD_SILENCE_NOISE` (default `-35dB`) | **Accept.** Operator tune for room gain; default documented; not a new Python API. |
| 4 | Speech-first heuristic: `silence_start` stamp `> 0.05 s` without prior `silence_end` | **Accept.** Covers “speech then silence” when ffmpeg never emits `silence_end` first; still requires sound before cut (lock 7). |

---

## 3. Notes (non-blocking)

| ID | Severity | Note |
|---|---|---|
| **N1** | Info / ACCEPT gate | **No live mic smoke.** Short phrase should cut before 7 s; long phrase capped; `S=0` restores fixed. Engineer §3 before ★. |
| **N2** | Low | **Level-based, not voice.** Mid-sentence pause ≥ S ends the turn; noisy rooms may run to the cap. Guide §8 + `JARVIS_RECORD_SILENCE_NOISE` — product limit, not a fail. |
| **N3** | Low | **arecord = fixed only.** Silence cut requires ffmpeg on PATH. Documented; same as judgment call 2. |
| **N4** | Info | Suite gains ~12–37 s wall time (T1–T3 sleep through short real windows). Acceptable for this Buy. |
| **Carry** | — | T53 **N1** (PTT helper cleanup) · **N2** (FULL punctuation) still later / Parked — not T54 scope. |

---

## 4. Tests executed by reviewer

```text
pytest tests/test_assistant_voice_silence_cut_b1.py \
       tests/test_assistant_voice_only_loop_b1.py -q
→ 15 passed in 37.00s

# record_audio_file seam
resolve_record_silence_seconds() default → 1.0; "" / "0" → 0.0
inspect.getsource(record_audio_file): no silencedetect / SILENCE
```

Implementer reports full suite **4061 passed / 9 skipped / 0 failed** — not re-run in full here; focused set green.

---

## 5. Recommendation

**PASS WITH NOTES.** Engineer ★ ACCEPT CLOSED (2026-10-14) → tag **`v0.8.1`**. N1 live mic smoke remains optional operator validation.
