# Implementation Report — Voice TTS Spanish default (`B1-assistant-voice-tts-spanish`, T49)

**Project:** Jarvis
**Date:** 2026-10-05
**Implementer:** Claude Code (Engineer paste)
**Contract:** [`implementation_contract_assistant_voice_tts_spanish_b1.md`](implementation_contract_assistant_voice_tts_spanish_b1.md)
**Parents:** [T48-inv Q8](investigation_report_assistant_voice_phase_t_review_b0.md) @ `0.7.5` · [TTS product brief](engineer_note_voice_tts_product_brief.md) · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md)
**Status:** **Implemented** — await Cursor review → Engineer ACCEPT → tag **`v0.7.6`**.
**Package / tag:** `0.7.6` / pending **`v0.7.6`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `.jes/artifacts/engineer_note_voice_tts_product_brief.md` | §1 voice-brief table: accent flipped to **Spanish `es_ES`** (default), default voice **`es_ES-davefx-medium`**, alt **`es_ES-sharvard-medium`**, `en_GB-alan-medium` demoted to documented **legacy/optional** (not deleted). Register/delivery/style rows unchanged. Cost-ladder (§2) and demo-checklist (§4) examples also flipped to the Spanish defaults, with `en_GB-alan-medium` named as the still-supported legacy path in both |
| `docs/USER_GUIDE_VOICE.md` | §2 (install): default model path/HF location flipped to `es/es_ES/davefx/medium/`, with `en_GB-alan-medium` named as a still-fully-supported alternative (just a `JARVIS_PIPER_MODEL` value change, no code). §3 (env config): all three example commands (`export JARVIS_PIPER_MODEL=...`, the `--check` success line, the "missing model" error line) flipped to the `davefx` path. §5.2 (whisper STT): example model flipped from the English-only `ggml-base.en.bin` to the multilingual `ggml-base.bin`, with a one-line honesty note on why (English-only models mistranscribe Spanish audio). §7 cheatsheet: both the Piper and Whisper example blocks flipped, with a comment naming the alt/legacy voices. §8 known-limits: the "Skills responden en español, la voz por defecto es `en_GB`" bullet rewritten to state the new default and keep `en_GB` as the documented alternative. **Opportunistic fix**: the pre-existing T45 N5 English-leak typo in §4.1 (*"a menos que also pidas"*) corrected to *"a menos que también pidas"* — found by T48-inv's N5 harvest, cheap to fix while already editing this file, zero behavior change |
| `scripts/voice/piper_tts.sh` | Header comment example env var flipped to `es_ES-davefx-medium.onnx`, with a note naming the alt/legacy voices. **Script body unchanged** — still reads `JARVIS_PIPER_MODEL` from the environment with zero hardcoded voice filename (verified by T3 below: no `davefx`/`sharvard`/`alan-medium`/`northern_english_male` literal anywhere outside the comment block) |
| `tests/test_assistant_voice_tts_spanish_b1.py` | **new** T1–T4 |
| `pyproject.toml` | `0.7.5` → **`0.7.6`** — no new dependency |
| `docs/PLATFORM_CAPABILITY_VISION.md` | short paragraph for T49 (and one for T48-inv, landed in the same session) — default-voice flip, no new C-xxx |
| `docs/system_map/CONNECTIONS.md` | short paragraph for T49 (and T48-inv) — same, no new C-xxx |
| Docs / cola / state | `IMPLEMENTATION_TASKS.md` PRIORIDAD/cola row · `engineer_note_voice_phase_c_cola.md` T49 row · `engineering_state.json` |

**Not touched (as the IC required):** zero `src/jarvis` files. `scripts/voice/whisper_stt.sh` body unchanged (already reads `JARVIS_WHISPER_MODEL` from the environment — only the guide's example path changed). No new C-xxx connect-plugs row (this is a default-value change inside the already-shipped T38 TTS seam, not a new connection). No speech dependency added to `pyproject.toml`. No `.onnx`/voice-model binary committed anywhere in the repo (verified in T4).

---

## 2. Why this needed zero `src/` changes

T48-inv's Q8 forensic read of `scripts/voice/piper_tts.sh` (before this Buy touched it) already confirmed the script is fully model-agnostic: `JARVIS_PIPER_MODEL` is a required environment variable with no hardcoded path anywhere in the executable body — only the header *comment* showed an `en_GB-alan-medium.onnx` example. The mismatch T48-inv found (Spanish Skill replies, English default demo voice) was therefore entirely a **documentation-default** problem, not a seam limitation. This Buy's only code-adjacent touch is that same comment block, which is inert (bash ignores `#` lines) — re-confirmed by T3's assertion that the script's executable body contains none of the specific voice-model names.

---

## 3. Tests executed

```text
pytest tests/test_assistant_voice_tts_spanish_b1.py -v
→ 4 passed (T1, T2, T3, T4)

pytest -q
→ 4030 passed, 9 skipped, 0 failed
```

Diffed against this session's pre-T49 tip (after T48-inv, before this Buy's edits): baseline was `4026 passed, 9 skipped, 0 failed`. **Zero regressions** — the delta is exactly the 4 new T49 tests. `git status` before committing shows exactly the files this IC's own file list names, plus the usual docs/cola/state bookkeeping.

T4 also re-confirms, live, that no `.onnx` file is committed anywhere in the repo (`find . -name "*.onnx" -not -path "*/.git/*"` returns empty) and that none of the forbidden speech-dependency package names leaked into `pyproject.toml`.

---

## 4. Remaining

None for this Buy. Out of scope per the IC (unchanged): any `src/jarvis` change, a new speech dependency, a tip-pinned voice-model file, wake-word/always-on, T40. The one genuinely open item is the same one T41's own N1 named for the original `en_GB` voice and T48-inv's Q9 re-flagged: **a live-mic, human-ear judgment of the new `es_ES-davefx-medium` default** — no amount of code/doc review substitutes for someone actually listening to it against "grave / corto / sin teatro." That is the Engineer's next step after ACCEPT, not a code gap.
