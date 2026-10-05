# Implementation Contract — Voice TTS Spanish default (`B1-assistant-voice-tts-spanish`)

**Project:** Jarvis
**Date:** 2026-10-05
**Author:** Engineer (direct paste to Claude = Buy, no separate Cursor-authored doc)
**Implementer:** **Claude Code**
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.7.6`**

**Status:** **★ ACCEPT CLOSED** (Engineer 2026-10-05) — Cursor **PASS WITH NOTES** · tip **`v0.7.6`**.
**Parents:** [T48-inv](investigation_report_assistant_voice_phase_t_review_b0.md) Q8 @ `0.7.5` · [T41 guide](implementation_review_assistant_voice_demo_ready_b1.md) · [TTS product brief](engineer_note_voice_tts_product_brief.md) · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md)
**Type:** Flip the **default demo TTS voice** from `en_GB-alan-medium` to Spanish `es_ES-davefx-medium`, documentation/comment-level only — the Piper external seam is already model-agnostic.
**Opens:** **`0.7.6` / `v0.7.6`**. **Cola:** **T49**

**Not:** a new seam · a `src/jarvis` change · a tip-pinned onnx model file in the repo · a new speech dependency · a wake-word/always-on change · T40.

---

## Why this Buy

T48-inv Q8 confirmed: every Skill/Continuity/chat reply is Spanish prose, but the shipped default demo voice is still the British English `en_GB-alan-medium` the TTS product brief locked for "first demos." The guide itself already names this as a known limitation (§8). The Piper wrapper (`scripts/voice/piper_tts.sh`) takes its model path from `JARVIS_PIPER_MODEL` with no hardcoded path — only the *documentation defaults and comment examples* across the brief, guide, and script header need to flip. Spanish voice reading Spanish text becomes the default; `en_GB` stays available as a documented legacy/alternative choice for anyone who wants it.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | **Brief** (`engineer_note_voice_tts_product_brief.md`) — accent locks to **Spanish `es_ES`**; register/delivery/style unchanged (grave / short / sin teatro); **default** = **`es_ES-davefx-medium`**; **alt** = **`es_ES-sharvard-medium`**; `en_GB-alan-medium` demoted to **legacy optional**, not deleted from the brief |
| 2 | **Guide** (`docs/USER_GUIDE_VOICE.md`) — §2 (install/model), §3 (env config + `--check` output example), the §7 cheatsheet, and §8 (known limits) all default to `davefx` paths. Model source: Hugging Face `rhasspy/piper-voices`, path `es/es_ES/davefx/medium/` (two files: `es_ES-davefx-medium.onnx` + `.onnx.json`, same two-file pattern as every other Piper voice). §8's existing "Skills responden en español, la voz por defecto es `en_GB`" bullet gets rewritten to state the new default (Spanish voice reading Spanish is now the default) and keep `en_GB` as the documented alternative for anyone who prefers it |
| 3 | **`piper_tts.sh`** — comment examples only (header docstring env var examples) flip to the Spanish model path. **No hardcoded model path added to the script body** — `JARVIS_PIPER_MODEL` stays a required env var exactly as today; the script remains fully model-agnostic |
| 4 | **STT honesty note (guide only)** — for Spanish `hablar`/PTT transcription, the guide's whisper.cpp section (§5.2) recommends a **multilingual** model (e.g. `ggml-base.bin`) over the English-only `ggml-base.en.bin` it currently shows as the example, with a one-line honesty note on why (English-only models mistranscribe Spanish). **No `src/` or `scripts/voice/whisper_stt.sh` change** — that script is already model-path-agnostic via `JARVIS_WHISPER_MODEL`; only the guide's example path changes |
| 5 | **Version** `pyproject` → **`0.7.6`** — no speech dependency added |
| 6 | **Tests T1–T4** — assert the new defaults appear in the brief/guide/script comment, assert no `.onnx` binary or tip-pinned voice-model dependency was added to the repo or to `pyproject.toml`, assert `piper_tts.sh`'s body still reads `JARVIS_PIPER_MODEL` from the environment with no hardcoded path (model-agnostic seam preserved) |
| 7 | **Docs — short PLATFORM/CONNECTIONS** — one short paragraph each, **no new C-xxx** (this is a default-value change inside the already-shipped T38 TTS seam, not a new connection) |
| 8 | **Prefer no `src/jarvis` changes** — the seam (`scripts/voice/piper_tts.sh` reading `JARVIS_PIPER_MODEL`) is already fully model-agnostic; this Buy is documentation-default-only |

---

## 1. Files

| Path | Change |
|---|---|
| `.jes/artifacts/engineer_note_voice_tts_product_brief.md` | §1 accent/default/alt table updated to Spanish `es_ES-davefx-medium` default, `es_ES-sharvard-medium` alt, `en_GB-alan-medium` legacy |
| `docs/USER_GUIDE_VOICE.md` | §2/§3/§7 (cheatsheet)/§8 default paths + prose flipped to `davefx`; §5.2 whisper model example flipped to multilingual `ggml-base.bin` with an honesty note; opportunistic fix of the pre-existing T45 N5 English-leak typo in §4.1 (`"a menos que also pidas"` → `"a menos que también pidas"`) since this Buy is already editing the same file |
| `scripts/voice/piper_tts.sh` | header comment example env vars only (`JARVIS_PIPER_MODEL=.../es_ES-davefx-medium.onnx`) — script body unchanged, still reads the env var with no hardcoded path |
| `tests/test_assistant_voice_tts_spanish_b1.py` | **new** T1–T4 |
| `pyproject.toml` | `0.7.5` → **`0.7.6`** |
| `docs/PLATFORM_CAPABILITY_VISION.md` | short paragraph — default voice flip, no new C-xxx |
| `docs/system_map/CONNECTIONS.md` | short paragraph — default voice flip, no new C-xxx |
| Docs / cola / state | T49 Implemented await review |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | Brief (`engineer_note_voice_tts_product_brief.md`) names `es_ES-davefx-medium` as the default and `es_ES-sharvard-medium` as the alt; `en_GB-alan-medium` still present but marked legacy/optional, not deleted |
| T2 | Guide (`USER_GUIDE_VOICE.md`) §2/§3/§7 cheatsheet all reference `davefx`/`es_ES` as the default install path; `en_GB-alan-medium` no longer appears as *the* default example (may still appear as the named legacy alternative) |
| T3 | `piper_tts.sh`'s header comment mentions a Spanish model path; the script body still contains `JARVIS_PIPER_MODEL` read from the environment with **no** hardcoded `.onnx` path literal anywhere in the executable body (only inside the comment block) |
| T4 | `pyproject.toml` is `0.7.6`; no speech dependency (`piper`, `whisper`, `vosk`, `speechrecognition`, `pyttsx`, `elevenlabs`, `pyaudio`, `sounddevice`, `ffmpeg-python`) was added; no tip-pinned onnx/voice-model file exists anywhere under the repo (`find . -name "*.onnx"` empty, excluding anything under a gitignored/user-local path) |

---

## 3. Acceptance

- [ ] Guide + brief + script comment all default to `es_ES-davefx-medium`; `en_GB` stays documented as legacy
- [ ] No `src/jarvis` change; seam stays model-agnostic; `0.7.6`; no new speech dep
- [ ] Cursor review · Engineer ACCEPT → tag **`v0.7.6`**

---

## 4. Paste for Claude

```text
Implementation — B1-assistant-voice-tts-spanish (T49)
Parent: T48-inv @ 0.7.5. Package -> 0.7.6.

IC: .jes/artifacts/implementation_contract_assistant_voice_tts_spanish_b1.md
Brief: .jes/artifacts/engineer_note_voice_tts_product_brief.md

Flip DEFAULT demo TTS to Spanish (same Piper external seam):
- Brief: Accent Spanish es_ES; grave/short/sin teatro; default
  es_ES-davefx-medium; alt es_ES-sharvard-medium; en_GB = legacy optional
- USER_GUIDE_VOICE.md: section 2/3/cheatsheet/8 default to davefx paths
  (HF: es/es_ES/davefx/medium/). Spanish voice reading Spanish is default.
- piper_tts.sh: comment examples only -> Spanish model (no hardcoded path)
- STT honesty: for Spanish hablar/PTT, prefer multilingual whisper
  (e.g. ggml-base.bin) over ggml-base.en.bin -- guide only
- pyproject 0.7.6; no speech deps; tests T1-T4; short PLATFORM/CONNECTIONS
- Prefer NO src/jarvis changes (seam already model-agnostic)
NO ACCEPT claim · NOT wake-word · NOT T40 · NOT tip-pin onnx in repo
```
