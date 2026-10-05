# Implementation Contract — Voice speak-path sanitizer (`B1-assistant-voice-speak-sanitize`)

**Project:** Jarvis  
**Date:** 2026-10-05  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.7.7`**

**Status:** **★ ACCEPT CLOSED** (Engineer 2026-10-05) — Cursor **PASS WITH NOTES** · tip **`v0.7.7`**.  
**Parents:** [FN-017](engineer_note_voice_spoken_polish_field_fn017.md) · [T45 ★](implementation_review_assistant_chat_spoken_continuity_b1.md) · [T49 ★](implementation_review_assistant_voice_tts_spanish_b1.md) · tip **`v0.7.6`** · [cola](engineer_note_voice_phase_c_cola.md)  
**Type:** Deterministic **speak-path** text sanitizer before Piper — strip terminal decoration + small locked TTS glossary. **Print / Layer 1 untouched.**  
**Opens:** **`0.7.7` / `v0.7.7`**. **Cola:** **T50**

**Not:** T51 brief-Spanish humanization · T52 FULL narrated rewrite · LLM · wake-word · T40 · changing Continuity ranking · changing `render_*` / screen walls · speech deps in `pyproject`.

---

## Why this Buy

Engineer live smoke (FN-017): Spanish Piper works, but `completo` (and any speak-as-printed wall) reads ASCII bars, bullets/asterisks, and raw codes like `C-rate` aloud. Layer 1 screen truth is fine; the ear needs a cheap, deterministic cleanup **before** `speak_egress`.

T51/T52 will go further (Spanish brief phrases; FULL = narrated fields). T50 only removes the worst “OCR of the terminal” artifacts and a minimal glossary proven in smoke.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-voice-speak-sanitize`** — sanitize text on the **speak path only** |
| 2 | **New pure helper** in `src/jarvis/adapters/voice/speak_sanitize.py`: `sanitize_for_speech(text: str) -> str` — stdlib only, no I/O, no LLM |
| 3 | **Wire once at TTS entry** — call `sanitize_for_speech` at the start of `speak_egress` (before building/running the external cmd), so `--chat --voice-speak`, `--voice`, and any `make_speak_callable` path all get it. Do **not** call it from `render_*` / print |
| 4 | **Decoration (locked):** (a) drop lines that are only box-drawing / rule characters (`─`, `━`, `─`, `-`, `=`, `_`, whitespace); (b) strip common leading markers from a line (`•`, `*`, `✓`, `◇`, `└`, `├`, `│` and similar tree junk) plus following spaces; (c) remove leftover standalone `*` used as footnote markers (e.g. `PASS *` → `PASS`); (d) collapse 3+ newlines to 2; trim |
| 5 | **Glossary (locked, finite, case-insensitive word/token replace):** exactly these pairs for T50 — expand later only via a new IC: `C-rate` / `c-rate` → `tasa C`; `C-RATE` → `tasa C`. Do **not** rewrite `PROJECT STATUS`, gap titles, `PASS`/`INCOMPLETE`, or BOM labels in T50 (those are T51/T52) |
| 6 | **Empty in → empty out** — if sanitize yields only whitespace, return `""`; callers of `speak_egress` / speak wrappers that already skip empty should keep skipping (do not invent filler speech) |
| 7 | **Honesty / fences** — T42 `run_chat` source must still have zero literal `speak_egress` / `JARVIS_TTS_CMD` / `_voice_speak_fn` / `TtsError` (sanitize lives inside `speak_egress` / voice package, not inlined into `run_chat`). No speech deps. No new C-xxx |
| 8 | **Tests T1–T6** — unit sanitize cases + prove print/render unchanged + wire via `speak_egress` (mock/subprocess or inspect) + tip-pin/ESC + `0.7.7` |
| 9 | **Docs** — short PRIORIDAD/cola/PLATFORM/CONNECTIONS; FN-017 note “T50 Implemented”; one honesty line in `USER_GUIDE_VOICE.md` §8 that speak strips terminal decoration (screen still full) |
| 10 | **Version** `pyproject` → **`0.7.7`** |
| 11 | **Out:** changing FULL from verbatim wall (T52) · Spanish-izing brief status lines (T51) · Piper SSML · tip-pin onnx |

---

## 1. Files

| Path | Change |
|---|---|
| `src/jarvis/adapters/voice/speak_sanitize.py` | **new** — `sanitize_for_speech` |
| `src/jarvis/adapters/voice/external_tts.py` | call sanitize at start of `speak_egress` |
| `src/jarvis/adapters/voice/__init__.py` | export `sanitize_for_speech`; fix stale “Piper en_GB” package docstring → Spanish default (T49 honesty) |
| `tests/test_assistant_voice_speak_sanitize_b1.py` | **new** T1–T6 |
| `pyproject.toml` | `0.7.6` → **`0.7.7`** |
| `docs/USER_GUIDE_VOICE.md` | §8 one bullet: speak sanitizes decoration; screen unchanged |
| `.jes/artifacts/engineer_note_voice_spoken_polish_field_fn017.md` | T50 Implemented await review |
| Docs / cola / PRIORIDAD / PLATFORM / CONNECTIONS / state | T50 row |

Prefer **not** editing `spoken_continuity.py` or `render_*` in this Buy.

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | Rule-only line(s) of `─` / `=` removed; surrounding prose kept |
| T2 | Leading `•` / `*` / `✓` / `◇` stripped from lines; content kept |
| T3 | `C-rate` / `c-rate` → `tasa C`; `PASS *` loses the footnote star |
| T4 | `render_startup_context` (or a golden printed wall snippet) still contains `─` / markers — print unchanged |
| T5 | `speak_egress` applies sanitize (e.g. monkeypatch subprocess / capture template input — spoken stdin must not contain a pure `────` line when fed a wall with one) |
| T6 | `0.7.7` · no speech deps · tip-pin + ESC green · `run_chat` source TTS-seam guard still empty |

---

## 3. Acceptance

- [ ] `completo` / speak-as-printed no longer reads bars/`•`/`*` aloud; `C-rate` → “tasa C”
- [ ] Screen Continuity wall byte-identical for the same turn
- [ ] `0.7.7` · Cursor review · Engineer ACCEPT → tag **`v0.7.7`**

---

## 4. Paste for Claude

```text
Implementation — B1-assistant-voice-speak-sanitize (T50)
Parent tip: v0.7.6 (T49 ★). Package -> 0.7.7.
Field Note: .jes/artifacts/engineer_note_voice_spoken_polish_field_fn017.md

IC: .jes/artifacts/implementation_contract_assistant_voice_speak_sanitize_b1.md

Speak-path ONLY sanitizer before Piper (print/Layer 1 untouched):
- NEW adapters/voice/speak_sanitize.py :: sanitize_for_speech(text) -> str
- Wire at start of speak_egress (covers --chat --voice-speak + --voice)
- Decoration: drop rule-only lines (─/=/_); strip leading • * ✓ ◇ └;
  strip footnote "*"; collapse blank lines
- Glossary ONLY: C-rate/c-rate -> "tasa C" (case-insensitive).
  Do NOT rewrite PROJECT STATUS / PASS / gap titles (those are T51/T52)
- Empty sanitize -> ""; no filler speech
- T42 run_chat TTS source guard must stay green
- Tests T1-T6; pyproject 0.7.7; short guide §8 + PLATFORM/CONNECTIONS
- Prefer NOT editing spoken_continuity.py / render_*
NO LLM · NOT T51 · NOT T52 FULL rewrite · NOT T40 · NOT wake-word
NO ACCEPT claim
```
