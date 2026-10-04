# Implementation Contract — Assistant voice interactive CLI (`B1-assistant-voice-interactive-cli`)

**Project:** Jarvis  
**Date:** 2026-10-04  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.7.2`**

**Status:** **Implemented** (Claude Code) — Cursor **PASS WITH NOTES** → await Engineer ★ ACCEPT → tag `v0.7.2`.  
**Parents:** [T41](implementation_review_assistant_voice_demo_ready_b1.md) @ `0.7.1` (PASS WITH NOTES / live Piper) · [T39 ★](implementation_review_assistant_voice_v1_checkpoint_b1.md) @ `v0.7.0` · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md) · [TTS brief](engineer_note_voice_tts_product_brief.md) · tip **`0.7.1`**  
**Type:** Interactive **use** path — Engineer sits in CLI, types (or later speaks) turns, hears replies. **Not** a fixture demo.  
**Opens:** **`0.7.2` / `v0.7.2`**. **Cola:** **T42**

**Not:** always-on wake word · craft/`world` (T40) · Piper in `pyproject` · Authority-from-voice · Marvel clone · tip pins · ACCEPT claim · replacing `--chat` byte-identical default.

---

## Why this Buy

Engineer: *“Quiero usar YO jarvis desde cli con voz, no quiero demos.”*

Today `--voice-fixture` / `--voice-audio` are **batch / one-shot**. `--chat` is interactive but **never speaks**. Missing piece: an **interactive loop** that reuses the voice brain + `JARVIS_TTS_CMD`.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-voice-interactive-cli`** — interactive CLI so the Engineer **uses** Jarvis with spoken replies |
| 2 | **New entry flag** — e.g. `--voice` (exact name flexible; must be obvious). Starts a **REPL loop**: prompt → user line → Skill-first brain with `source=VOICE` → print egress → **speak** via existing `speak_egress` / `JARVIS_TTS_CMD`. Exit on `quit`/`salir`/EOF/Ctrl-C with a clear goodbye |
| 3 | **Reuse seams** — no new STT/TTS process family. Call existing `handle_user_text(..., source=IntentSource.VOICE)` (or `run_voice_turn`) + `render_response` + T38 speak. Prefer thin code in `adapters/cli/main.py` and/or `adapters/voice/` |
| 4 | **`--chat` unchanged by default** — without the new flag, chat stays text-only (byte-identical). Do **not** force speak on every chat session unless Engineer also opts in via the new flag (do not silently change `--chat`) |
| 5 | **Typed input for this Buy** — prompt like `You > ` / `User > ` reading from stdin. **Live mic stream / wake word OUT** of this Buy (optional one-shot “press enter then record” may be documented later; not required). Fixture/audio flags stay for tests/batch |
| 6 | **TTS required honesty** — if `JARVIS_TTS_CMD` missing/fails, print honest `TTS no disponible: …` and still show text (same spirit as `_voice_speak_fn`). Do not crash the REPL |
| 7 | **Guide first** — rewrite the top of `docs/USER_GUIDE_VOICE.md` so the **primary** path is: install Piper → export env → `python -m jarvis.main --voice` (or chosen flag) → type `hold` / `armar` / `estado` and **hear** replies. Fixture demo moves to a secondary “batch / CI” section |
| 8 | **Version** `pyproject` → **`0.7.2`**; PRIORIDAD · cola T42 · short PLATFORM/CONNECTIONS (**no new C-xxx**) |
| 9 | **Tests** — interactive loop with fake stdin + fake TTS script: ≥2 typed turns → fake TTS receives ≥2 egress strings; quit exits cleanly; `--chat` without new flag still does not speak; no tip pins; no speech deps; ESC fence green |
| 10 | Out: wake-word daemon · T40 craft/world · tip-pinned SDKs · ACCEPT claim · inventing a GUI |

---

## 1. Files

| Path | Change |
|---|---|
| `src/jarvis/adapters/cli/main.py` | new `--voice` (or equiv.) interactive REPL + wire speak |
| `src/jarvis/adapters/voice/` | optional thin `run_voice_repl` helper — only if it stays small |
| `docs/USER_GUIDE_VOICE.md` | **lead with interactive use**; demote fixture to secondary |
| `tests/test_assistant_voice_interactive_cli_b1.py` | **new** T1–T5 |
| `pyproject.toml` | `0.7.1` → **`0.7.2`** — no speech deps |
| Docs / cola / state | T42 row |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | Fake stdin with 2 Skill phrases + quit → 2 non-empty egress prints; fake TTS records both (when speak wired) |
| T2 | Missing/broken `JARVIS_TTS_CMD` → honest message; REPL continues / does not crash on first turn |
| T3 | `source=VOICE` path used (spy `VoiceIntentAdapter.parse` or equivalent) |
| T4 | `--chat` alone does **not** invoke TTS |
| T5 | `0.7.2` · no speech deps · tip-pin + ESC green · guide mentions `--voice` (or chosen flag) before fixture as primary use |

---

## 3. Acceptance

- [ ] Engineer can run interactive `--voice`, type Skill phrases, see + hear replies via Piper/`JARVIS_TTS_CMD`  
- [ ] Guide leads with that path · `0.7.2` · no new vendor SDK · `--chat` default unchanged  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.7.2`**

---

## 4. Paste for Claude

```text
Implementation — B1-assistant-voice-interactive-cli (T42)
Parent tip: T41 @ 0.7.1 (demo-ready + live Piper fix). Package → 0.7.2.

IC: .jes/artifacts/implementation_contract_assistant_voice_interactive_cli_b1.md
Guide: docs/USER_GUIDE_VOICE.md (rewrite lead = interactive USE)

Engineer wants to USE Jarvis from CLI with voice — NOT fixture demos.
- Add interactive flag (e.g. --voice): REPL loop
  prompt → typed line → handle_user_text(source=VOICE)
  → render_response → print + speak_egress (JARVIS_TTS_CMD)
  quit/salir/EOF exits cleanly
- Reuse T35–T38 seams; no new STT/TTS vendor family
- --chat default stays text-only (no silent speak)
- Live mic/wake-word OUT of this Buy
- USER_GUIDE_VOICE: primary path = --voice; fixture = secondary
- pyproject 0.7.2; tests with fake stdin + fake TTS
NO ACCEPT claim · NO tip pins · NO speech deps in pyproject
· NOT T40 · NOT wake-word · NOT GUI
```
