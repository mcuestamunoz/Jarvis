# Implementation Contract — Assistant voice demo ready (`B1-assistant-voice-demo-ready`)

**Project:** Jarvis  
**Date:** 2026-10-04  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.7.1`**

**Status:** **★ ACCEPT CLOSED** (Engineer 2026-10-05) — Cursor **PASS WITH NOTES** · tip **`v0.7.1`**.  
**Parents:** [T39 ★](implementation_review_assistant_voice_v1_checkpoint_b1.md) @ `v0.7.0` · [TTS product brief](engineer_note_voice_tts_product_brief.md) · [cola note](engineer_note_voice_phase_c_cola.md) · [DC voice/channels ★](design_contract_assistant_chat_voice_channels_b0.md)  
**Type:** Operator demo path — **use Jarvis with voice** on the seams already ★ (T35–T39).  
**Opens:** **`0.7.1` / `v0.7.1`**. **Cola:** **T41** (not T40)

**Not:** new STT/TTS seam in `src/` · Piper/whisper in `pyproject` · craft/`world/` (T40) · Authority-from-voice · Marvel clone · Conversation Engine · tip pins · ACCEPT claim.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-voice-demo-ready`** — post–voz-v1 **operator path** so Engineer can **use** Jarvis with spoken replies (and optional spoken ingress) |
| 2 | **No new core seam** — reuse `JARVIS_TTS_CMD` / `JARVIS_STT_CMD` / `--voice-fixture` / `--voice-audio` / `--voice-speak` exactly as T36–T38 shipped. Prefer **zero** (or docs-only) change under `src/jarvis/` |
| 3 | **`docs/USER_GUIDE_VOICE.md`** — user guide in the spirit of `USER_GUIDE_EXPLAIN.md`: real copy-paste commands; what voice is / is not; install Piper **outside** the package; set env; run fixture+speak; optional mic→STT path; honesty that vendor binaries stay external |
| 4 | **TTS wrapper script(s) under `scripts/voice/`** (or equivalent repo path **outside** `src/`) — stdin text → Piper (or documented fallback) → play and/or write wav. Config via env for model path (e.g. `JARVIS_PIPER_MODEL`). Must work when Piper + model are installed; fail with a clear message if missing (no silent success) |
| 5 | **Sample fixture** — small checked-in text fixture (e.g. `scripts/voice/fixtures/demo_skills.txt` or `examples/voice/…`) with a few Skill phrases (`armar`, `hold`, `estado`, …) for `jarvis --voice-fixture PATH --voice-speak` |
| 6 | **Optional STT helper** — thin external script or guide section: audio file path → transcript on stdout, usable as `JARVIS_STT_CMD` with `{audio}`. Prefer free/local (e.g. whisper.cpp / user-local whisper) **not** added to `pyproject`. Mic capture may be a shell one-liner (`arecord`/`ffmpeg`) documented in the guide — **not** a new loop inside `adapters/voice/` |
| 7 | **Product brief** — point at [TTS brief](engineer_note_voice_tts_product_brief.md): British / grave / short / no theater; default demo voice **Piper `en_GB-alan-medium`** (or northern_english_male if alan thin). Do not tip-pin Piper wheels in core deps |
| 8 | **Version** `pyproject.toml` → **`0.7.1`**; PRIORIDAD · cola note (new **T41** row) · short PLATFORM / CONNECTIONS (**no new C-xxx**) · ARCHITECTURE one-liner OK |
| 9 | **Tests** — minimal: guide file exists + required section headers; wrapper script(s) exist + are executable bits / shebang; sample fixture non-empty; no tip pins; no speech deps in `pyproject`; ESC fence still green. Optional: if wrapper has a `--dry-run` / missing-binary path, assert honest non-zero exit — **do not** require Piper installed in CI |
| 10 | Out: T40 craft/`world` · tip-pinned speech SDKs · live Authority/kill · inventing a second brain · ACCEPT claim · requiring paid cloud TTS |

---

## 1. Files

| Path | Change |
|---|---|
| `docs/USER_GUIDE_VOICE.md` | **new** operator guide |
| `scripts/voice/` (or `examples/voice/`) | TTS wrapper + sample fixture; optional STT helper |
| `tests/test_assistant_voice_demo_ready_b1.py` | **new** minimal presence / honesty tests |
| `pyproject.toml` | `0.7.0` → **`0.7.1`** — **no** new speech deps |
| Docs / cola / PRIORIDAD | T41 row; tip parent; brief pointer |
| `src/jarvis/**` | **prefer untouched** |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | `USER_GUIDE_VOICE.md` exists and contains headers / env names `JARVIS_TTS_CMD`, `JARVIS_STT_CMD`, `--voice-speak`, Piper |
| T2 | TTS wrapper script exists under `scripts/voice/` (or chosen path); shebang present; mentions Piper or model env |
| T3 | Sample fixture file exists and has ≥ 3 non-empty Skill lines |
| T4 | `pyproject` **`0.7.1`**; no speech deps (`piper`/`whisper`/… absent); T17 tip-pin guardrail green; ESC fence green on voice adapters (untouched) |
| T5 | (optional) wrapper invoked with missing Piper/model → non-zero exit or clear stderr — **skip if unsafe in CI**; never require a speaker |

---

## 3. Acceptance

- [ ] Operator can follow `USER_GUIDE_VOICE.md` to install Piper outside package, set `JARVIS_TTS_CMD`, run `--voice-fixture` + `--voice-speak`, and hear Skill egress  
- [ ] Optional STT/mic path documented (external) · `0.7.1` · no speech SDK in deps · no new core seam  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.7.1`**

---

## 4. Paste for Claude

```text
Implementation — B1-assistant-voice-demo-ready (T41)
Parent tip: T39 ★ ACCEPT CLOSED @ v0.7.0. Package → 0.7.1.

IC: .jes/artifacts/implementation_contract_assistant_voice_demo_ready_b1.md
Brief: .jes/artifacts/engineer_note_voice_tts_product_brief.md
Cola: .jes/artifacts/engineer_note_voice_phase_c_cola.md
Guide style: docs/USER_GUIDE_EXPLAIN.md

Operator path — USE Jarvis with voice. NO new src/ seam.
- docs/USER_GUIDE_VOICE.md — install Piper outside package; env;
  --voice-fixture + --voice-speak; optional mic/STT external
- scripts/voice/: Piper TTS wrapper (stdin → speak/wav);
  sample fixture; optional STT helper (stdout transcript)
- Fail clear if Piper/model missing — no silent success
- Default demo voice: Piper en_GB-alan-medium (brief)
- pyproject 0.7.1; NO piper/whisper in deps; prefer zero src/
- PRIORIDAD/cola T41; PLATFORM/CONNECTIONS no new C-xxx
NO ACCEPT claim · NO tip pins · NOT T40 world/craft
· NOT Marvel clone · NOT vendor SDK in core
```
