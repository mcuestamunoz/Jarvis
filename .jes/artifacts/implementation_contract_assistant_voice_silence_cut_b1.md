# Implementation Contract — Voice-only silence cut (`B1-assistant-voice-silence-cut`)

**Project:** Jarvis  
**Date:** 2026-10-13  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.8.1`**

**Status:** ★ **ACCEPT CLOSED** @ **`v0.8.1`** (2026-10-14).  
**Parents:** [V10-DC / T54-DC](design_contract_assistant_voice_silence_cut_b0.md) · [T53 review ★](implementation_review_assistant_voice_only_loop_b1.md) @ `v0.8.0` · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md) · tip **`v0.8.0`**  
**Type:** External **silence end-of-utterance** on `--voice-only` record — max duration still applies; STT/chat/TTS unchanged.  
**Opens:** **`0.8.1` / `v0.8.1`**. **Cola:** **T54** / **V10**

**Not:** wake-word · always-on · barge-in · VAD inside `src/` as a pip dependency · T40 · changing two product modes · ACCEPT claim · tip version pins · FULL-phrase punctuation (T53 N2) · mandatory PTT-helper cleanup (T53 N1).

---

## Why this Buy

T53 voice-only always records a fixed `JARVIS_RECORD_SECONDS` window. V10 stops earlier when the user finishes speaking (silence), without a new brain or speech SDK in the package.

---

## 0. Engineer Buy (locked from V10-DC + this IC)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-voice-silence-cut`**. Package/tag **`0.8.1` / `v0.8.1`** |
| 2 | **Only `--voice-only` record path** — `--chat` untouched. Session loop / speak / Continuity Layer 1–2 / STT / TTS contracts unchanged |
| 3 | **Silence lives in the external recorder** — ship an updated `scripts/voice/record_turn.sh` **or** a sibling (e.g. `record_until_silence.sh`) that `JARVIS_RECORD_CMD` can point at. Free-first tools only (ffmpeg and/or sox / arecord patterns already in the operator story). **No** new entry in `pyproject.toml` dependencies |
| 4 | **Python seam** — `record_audio_file` remains “invoke template → exit 0 + non-empty file”. Optional thin env plumbing only if needed (document new envs; do not invent a second record API in `core/`). Prefer **zero** `adapters/voice/external_record.py` behavior change if the script alone is enough |
| 5 | **Max duration** — `JARVIS_RECORD_SECONDS` (default **7**) remains hard cap |
| 6 | **Silence duration** — `JARVIS_RECORD_SILENCE_SECONDS` default **`1.0`**. Stop after ≥ this many seconds of continuous silence **once speech has been detected** in the capture. **`0`** (or empty → treat as 0 in IC tests) = **fixed-duration only** (T53 behavior) for CI/fakes |
| 7 | **No-speech window** — if no speech is detected for the whole capture, stop at **max duration** (do not invent an early “empty room” cut that surprises CI). Wav may be near-silent; STT honesty already handles empty/failed transcript |
| 8 | **Cue** — voice-only print-only line becomes honest, e.g. `Jarvis > Grabando (máx {M} s; corta con ~{S} s de silencio)…` when silence mode is on (`S>0`); when `S=0`, keep a fixed-only cue like `Jarvis > Grabando {M} s…`. Never TTS the cue |
| 9 | **T53 exit/cancel unchanged** — double Ctrl-C, config-missing ends session, process failure reopens mic, ephemeral unlink, exit words with trailing punctuation |
| 10 | **Guide** — document silence envs + cue; two modes only |
| 11 | **Tests T1–T6** — mic-free fakes; see §2 |
| 12 | **Out** — wake-word · barge-in · removing max cap · speech SDK · T40 · ACCEPT claim · rewriting `spoken_continuity` |

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `scripts/voice/record_turn.sh` and/or new sibling under `scripts/voice/` | Silence-aware capture + max cap; `--check`; env `JARVIS_RECORD_SILENCE_SECONDS` |
| `src/jarvis/adapters/cli/main.py` | Cue string(s) for voice-only mic reader only — minimal |
| `src/jarvis/adapters/voice/external_record.py` | Prefer **unchanged**; optional docstring/env name constants only if needed |
| `docs/USER_GUIDE_VOICE.md` | Silence cut + envs |
| `tests/test_assistant_voice_silence_cut_b1.py` | **new** T1–T6 |
| `tests/test_assistant_voice_only_loop_b1.py` | Adjust cue assertions if the default cue text changes; keep suite green |
| `pyproject.toml` | `0.8.0` → **`0.8.1`** |
| PRIORIDAD · cola · state · short PLATFORM/CONNECTIONS note | **no new C-xxx** |

Do **not** touch orchestrator, Continuity extractors, or Skill registry.

---

## 2. Tests

No real mic. Fake RECORD that respects silence env for early exit.

| ID | Assert |
|---|---|
| T1 | `JARVIS_RECORD_SILENCE_SECONDS=0` (or fixed-only): voice-only still records up to max; cue is fixed-style; T53 loop still works (armar → salir) |
| T2 | Silence mode on (`S=1.0`): fake recorder exits **before** max seconds and still produces a non-empty wav; voice-only continues to STT + brain; event log / duration spy shows early stop |
| T3 | Max cap still enforced by the real script logic under test **or** by a fake that refuses to exceed `{seconds}` even in silence mode |
| T4 | Bare `--chat` never records; missing RECORD config still ends voice-only honestly (T53) |
| T5 | Guide mentions silence env + max cap; `pyproject` **0.8.1**; no speech deps; tip-pin/ESC fences green |
| T6 | Default path (`S` default 1.0) does not break existing voice-only unit tests when fakes ignore silence (fakes may force `S=0` in fixtures) — suite green for T53 voice-only file |

---

## 3. Acceptance

- [ ] Live `--voice-only`: speak a short phrase, silence ~1 s → turn ends before full 7 s; long phrase still capped at max  
- [ ] `JARVIS_RECORD_SILENCE_SECONDS=0` restores fixed window  
- [ ] `0.8.1` · Cursor review · Engineer ★ · tag **`v0.8.1`**

---

## 4. Paste for Claude

```text
Implementation — B1-assistant-voice-silence-cut (T54 / V10)
Parent: V10-DC + T53 ★ @ v0.8.0. Package → 0.8.1.

IC: .jes/artifacts/implementation_contract_assistant_voice_silence_cut_b1.md
DC: .jes/artifacts/design_contract_assistant_voice_silence_cut_b0.md
Guide: docs/USER_GUIDE_VOICE.md

GOAL: --voice-only stops recording early after the user stops speaking,
without a new brain or speech SDK in pyproject.

DO:
- Keep max duration JARVIS_RECORD_SECONDS (default 7).
- Add JARVIS_RECORD_SILENCE_SECONDS (default 1.0). After speech is
  detected, stop on ≥ S seconds of continuous silence. S=0 → fixed
  duration only (T53). If no speech in the window → wait until max.
- Implement silence in the EXTERNAL recorder
  (scripts/voice/record_turn.sh and/or sibling). Free tools only
  (ffmpeg/sox/arecord family). Python record_audio_file: prefer
  unchanged (still run cmd → non-empty wav).
- Update voice-only print-only cue to be honest when S>0
  (máx M s; corta con silencio). Never TTS the cue.
- Do NOT change STT/TTS/Continuity/session brain/two modes.
- T53 cancel / double Ctrl-C / config-missing end session / ephemeral
  wav unchanged.
- Tests T1–T6 mic-free. Adjust T53 cue asserts if needed. Suite green.
- pyproject 0.8.1. Guide + PRIORIDAD/cola/state. No new C-xxx.

NO: wake-word · always-on · barge-in · pip audio DSP · T40 ·
ACCEPT claim · tip pins · rewriting spoken_continuity
```

---

## 5. Cursor note

Claude may implement the full IC scope without per-edit approval. Stop if silence requires a tip-pinned audio library in `pyproject` or a new always-on thread — that is out of lock.
