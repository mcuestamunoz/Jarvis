# Field Note — Spoken Continuity polish (FN-017)

**Date:** 2026-10-05  
**Source:** Engineer live smoke @ tip **`v0.7.6`** (`es_ES-davefx-medium` + `--chat --voice-speak`)  
**Project:** `dron-de-vigilancia-doméstico`  
**Status:** **OPEN** — **T50 Implemented** (await Cursor review) → T51 → T52 (see voice cola)

---

## Observation

Spanish Piper works. Continuity brief is usable. Asking `completo` (FULL this turn) reads the **printed wall verbatim** — flat OCR-style speech:

- Speaks decorative ASCII (`────`, `*`, `•`)
- Speaks English labels / codes as-written (`C-rate`, `PROJECT STATUS`, gap titles)
- Speaks BOM / readiness tables that are screen-truth, not ear-truth

This is **by design today** (`spoken_text_for_wall` → `printed_wall` on FULL; brief still emits some English status phrases). Not a Piper bug. Not a Layer 1 (screen) defect.

---

## Product intent

Layer 1 screen Continuity stays full truth.  
Layer 2 ear must sound like a short engineering briefing in Spanish — not a reading of the terminal buffer.

---

## Queued Buys (ordered)

| # | Buy | Intent |
|---|---|---|
| **T50** | `B1-assistant-voice-speak-sanitize` | **Implemented** @ `0.7.7`, await Cursor review — [report](implementation_report_assistant_voice_speak_sanitize_b1.md). Speak-path sanitizer before Piper. Print untouched. |
| **T51** | `B1-assistant-voice-brief-spanish` | Humanize brief Continuity phrases to Spanish (`PROJECT STATUS` / gap titles). Same five fields. |
| **T52-DC** → **T52** | `DC` + `B1-assistant-voice-full-spoken` | Amend what FULL means: narrated detailed Continuity (prose from fields), **not** verbatim print. Screen still full. Reopens T44-DC FULL speak payload only. |

**Out:** LLM summary · wake-word · T40 · changing screen Continuity · Conversation Engine.

**Next process step:** Cursor review of T50 → Engineer ACCEPT → tag `v0.7.7`. Then T51 IC when Engineer says proceed.
