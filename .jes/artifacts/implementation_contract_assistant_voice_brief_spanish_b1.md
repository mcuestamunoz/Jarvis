# Implementation Contract — Voice Continuity brief Spanish (`B1-assistant-voice-brief-spanish`)

**Project:** Jarvis  
**Date:** 2026-10-05  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.7.8`**

**Status:** **IC ready** — paste to Claude = Buy. Cursor does **not** implement unless Engineer says so.  
**Parents:** [FN-017](engineer_note_voice_spoken_polish_field_fn017.md) · [T50 ★](implementation_review_assistant_voice_speak_sanitize_b1.md) @ **`v0.7.7`** · [T45 ★](implementation_review_assistant_chat_spoken_continuity_b1.md) · tip **`v0.7.7`**  
**Type:** Speak-path only — Spanish humanization of Continuity **brief** lines + absorb T50-N1/N2. **Print / Layer 1 untouched.** Same five brief fields.  
**Opens:** **`0.7.8` / `v0.7.8`**. **Cola:** **T51**

**Not:** T52 FULL narrated rewrite · LLM · wake-word · T40 · changing `engineering_readiness` gap title SoT · changing screen `PROJECT STATUS:` English line · speech deps.

---

## Why this Buy

After T50, decoration/`C-rate` token noise is gone, but the **brief** still speaks English engineering labels: `PROJECT STATUS: NOT ASSEMBLY READY`, gap titles like `Autonomy target not met`. Engineer smoke (FN-017) + T50-N1 (“El tasa C”) need natural Spanish on the ear for the default Continuity path (`estado` / project load).

Screen Continuity stays as today (English readiness labels allowed on Layer 1). Only Layer 2 brief changes.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-voice-brief-spanish`** — Spanish speak phrases for Continuity brief only |
| 2 | **Same five fields / order** as T45: `situation` · `next_useful_step` · humanized `next_useful_why` · project-status phrase · top gap title. No new fields. No LLM |
| 3 | **Project-status speak phrases (locked):** if `readiness.overall == "ASSEMBLY_READY"` → speak exactly `Estado del proyecto: listo para ensamblar`; else when overall present → `Estado del proyecto: no listo para ensamblar`. Do **not** speak the English `PROJECT STATUS:` / `ASSEMBLY READY` strings on the brief path |
| 4 | **Gap-title speak map (finite, speak-only):** in `spoken_continuity.py` (or a tiny helper next to it), map known `prioritized_gaps[0].title` English strings to Spanish. **Minimum locked set** (must include): `Autonomy target not met` → `Objetivo de autonomía no alcanzado`; `Mass limit exceeded` → `Límite de masa superado`; `Parameters blocking simulation` → `Parámetros bloquean la simulación`; `Simulation not PASS` → `Simulación no en PASS`; `Architecture block incomplete` → `Bloque de arquitectura incompleto`. Unknown titles: speak the raw title unchanged (honesty) — do **not** invent translations |
| 5 | **T50-N1 (locked):** in `speak_sanitize.py` glossary, replace awkward article+glossary: (a) `\b([Ee]l|[Ll]a)\s+c-rate\b` → `la tasa C` (case-insensitive on El/La/c-rate); (b) remaining `\bc-rate\b` → `la tasa C`. Result must never produce `El tasa C` / `el tasa C`. Update T50 tests that asserted bare `"tasa C"` after `El C-rate` accordingly |
| 6 | **T50-N2:** fix `external_tts.py` module docstring vendor/demo line to Spanish default `es_ES-davefx-medium` (legacy `en_GB` optional) — same honesty T50 already applied to `__init__.py` |
| 7 | **Print untouched** — `render_startup_context` / readiness block still show English `PROJECT STATUS:` / English gap titles. Prove with a test that a rendered wall still contains `PROJECT STATUS` while brief speak does not |
| 8 | **Wire** — only `brief_spoken_continuity` (and sanitize glossary) change; FULL path still verbatim print (pre-T52) then T50 sanitize. Prefer not editing `run_chat` |
| 9 | **Tests T1–T6** — status phrases · gap map · unknown title passthrough · N1 glossary · print still English · tip-pin/ESC · `0.7.8` |
| 10 | **Docs** — PRIORIDAD/cola/FN-017/PLATFORM/CONNECTIONS short; guide §4.1 one line that brief Continuity speaks Spanish status/gap labels |
| 11 | **Version** `pyproject` → **`0.7.8`** |
| 12 | **Out:** FULL narrated (T52) · expanding gap map beyond locked set without a new IC · rewriting core readiness titles · LLM |

---

## 1. Files

| Path | Change |
|---|---|
| `src/jarvis/adapters/voice/spoken_continuity.py` | Spanish status phrase + gap-title speak map in `brief_spoken_continuity` |
| `src/jarvis/adapters/voice/speak_sanitize.py` | T50-N1 glossary → `la tasa C` with El/La absorption |
| `src/jarvis/adapters/voice/external_tts.py` | T50-N2 docstring honesty |
| `tests/test_assistant_voice_brief_spanish_b1.py` | **new** T1–T6 |
| `tests/test_assistant_voice_speak_sanitize_b1.py` | update T2/T5 expectations for `la tasa C` / no `El tasa C` |
| `pyproject.toml` | `0.7.7` → **`0.7.8`** |
| `docs/USER_GUIDE_VOICE.md` | §4.1 brief Spanish honesty line |
| FN-017 / cola / PRIORIDAD / PLATFORM / CONNECTIONS / state | T51 Implemented await review |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | Brief with `overall=ASSEMBLY_READY` speaks `Estado del proyecto: listo para ensamblar`; never `PROJECT STATUS` / `ASSEMBLY READY` |
| T2 | Brief with non-ready overall speaks `Estado del proyecto: no listo para ensamblar` |
| T3 | Top gap title `Autonomy target not met` → Spanish locked string; an unknown title passes through unchanged |
| T4 | `sanitize_for_speech("El C-rate de la batería")` → contains `la tasa C`, never `El tasa C` / `el tasa C` |
| T5 | Rendered Continuity wall / readiness print still contains `PROJECT STATUS` (Layer 1 English unchanged) |
| T6 | `0.7.8` · no speech deps · tip-pin + ESC · `run_chat` TTS source guard still empty |

---

## 3. Acceptance

- [ ] `estado` / project load brief speaks Spanish status + mapped gap titles; screen still English readiness labels  
- [ ] No “El tasa C”; T50-N2 docstring fixed  
- [ ] `0.7.8` · Cursor review · Engineer ACCEPT → tag **`v0.7.8`**

---

## 4. Paste for Claude

```text
Implementation — B1-assistant-voice-brief-spanish (T51)
Parent tip: v0.7.7 (T50 ★). Package -> 0.7.8.
FN-017: .jes/artifacts/engineer_note_voice_spoken_polish_field_fn017.md
IC: .jes/artifacts/implementation_contract_assistant_voice_brief_spanish_b1.md

Speak-path ONLY — Continuity brief Spanish (print/Layer 1 untouched):
- brief_spoken_continuity: same 5 fields/order as T45
- PROJECT STATUS speak:
    ASSEMBLY_READY -> "Estado del proyecto: listo para ensamblar"
    else -> "Estado del proyecto: no listo para ensamblar"
  Never speak English PROJECT STATUS / ASSEMBLY READY on brief path
- Finite speak-only gap title map (min set locked in IC):
    "Autonomy target not met" -> "Objetivo de autonomía no alcanzado"
    "Mass limit exceeded" -> "Límite de masa superado"
    "Parameters blocking simulation" -> "Parámetros bloquean la simulación"
    "Simulation not PASS" -> "Simulación no en PASS"
    "Architecture block incomplete" -> "Bloque de arquitectura incompleto"
  Unknown titles: speak raw (no invent)
- T50-N1: speak_sanitize glossary -> "la tasa C"; absorb El/La before c-rate;
  never produce "El tasa C". Update T50 sanitize tests.
- T50-N2: fix external_tts.py docstring to Spanish default (en_GB legacy)
- Prefer NOT editing run_chat / render_* / engineering_readiness titles
- Tests T1-T6; pyproject 0.7.8; short guide + PLATFORM/CONNECTIONS
NO LLM · NOT T52 FULL rewrite · NOT T40 · NOT wake-word
NO ACCEPT claim
```
