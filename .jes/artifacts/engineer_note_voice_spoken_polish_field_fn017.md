# Field Note — Spoken Continuity polish (FN-017)

**Date:** 2026-10-05  
**Source:** Engineer live smoke @ tip **`v0.7.6`** (`es_ES-davefx-medium` + `--chat --voice-speak`)  
**Project:** `dron-de-vigilancia-doméstico`  
**Status:** **OPEN** — **T50 ★** @ `v0.7.7` · **T51 ★** @ `v0.7.8` · **T52** Cursor **PASS WITH NOTES** @ `0.7.9` (await Engineer ACCEPT → `v0.7.9`)

**Discipline:** anything spotted in smoke/review that can hurt spoken UX or docs honesty later gets **tracked here** (or in cola) with a home Buy — fix now if cheap, else schedule. Do not drop notes.

---

## Observation

Spanish Piper works. Continuity brief is usable. Asking `completo` (FULL this turn) reads the **printed wall verbatim** — flat OCR-style speech:

- Speaks decorative ASCII (`────`, `*`, `•`) — **T50 closes decoration**
- Speaks English labels / codes as-written (`C-rate`, `PROJECT STATUS`, gap titles) — **C-rate → T50 glossary; rest → T51/T52**
- Speaks BOM / readiness tables that are screen-truth, not ear-truth — **T52**

This is **by design today** for FULL (`spoken_text_for_wall` → `printed_wall`); brief still emits some English status phrases. Not a Piper bug. Not a Layer 1 (screen) defect.

---

## Product intent

Layer 1 screen Continuity stays full truth.  
Layer 2 ear must sound like a short engineering briefing in Spanish — not a reading of the terminal buffer.

---

## Queued Buys (ordered)

| # | Buy | Intent |
|---|---|---|
| **T50** | `B1-assistant-voice-speak-sanitize` | ✅ ★ **ACCEPT CLOSED** @ **`v0.7.7`** — [review ★](implementation_review_assistant_voice_speak_sanitize_b1.md). |
| **T51** | `B1-assistant-voice-brief-spanish` | ✅ ★ **ACCEPT CLOSED** @ **`v0.7.8`** — [review ★](implementation_review_assistant_voice_brief_spanish_b1.md). |
| **T52-DC** | `DC-assistant-voice-full-spoken` | **DC ready** — [DC](design_contract_assistant_voice_full_spoken_b0.md). Amends T44-DC FULL **payload** only. |
| **T52** | `B1-assistant-voice-full-spoken` | Cursor **PASS WITH NOTES** @ `0.7.9` — [review](implementation_review_assistant_voice_full_spoken_b1.md) · [report](implementation_report_assistant_voice_full_spoken_b1.md). Await Engineer ★ ACCEPT → tag `v0.7.9`. |

**Out:** LLM summary · wake-word · T40 · changing screen Continuity · Conversation Engine.

---

## Tracked follow-ups (from T50 review — must not be lost)

| ID | Finding | Severity | Home | When |
|---|---|---|---|---|
| **T50-N1** | Glossary yields awkward “El tasa C” (locked string `"tasa C"`) | Spoken UX polish | **T51** | **Done** — glossary now resolves to `"la tasa C"` always, absorbing a preceding `El`/`La` |
| **T50-N2** | `external_tts.py` module docstring still narrates pre-T49 `en_GB` demo setup (`__init__.py` already fixed) | Docs honesty | **T51** | **Done** — docstring now names the Spanish default |
| **T50-N3** | Sibling tests updated for glossary + tip-pin policy | None — closed | — | Done |
| **T51-N1** | `brief_spoken_continuity` docstring still narrated pre-T51 `PROJECT STATUS: …` | Docs honesty | same tip | **Done** — docstring synced to Spanish status + mapped/raw gap |
| **T51-N2** | Sibling T45/T50 test assertion updates | None — informational | report §2 | **Closed** — intentional locked behavior; no further cleanup |
| **T52-N1** | Section B speaks raw `recommended_next_step.action` codes | Spoken UX polish | later IC | After T52 ★ |
| **T52-N2** | Brief may speak unmapped `next_useful_why` codes | Spoken UX polish | later IC (brief) | After T52 ★ |
| **T52-N3** | IC T7 `0.7.9` not tip-pinned in-test | None — policy | tip-pin suite | Closed (same as T51 T6) |
| **T52-N4** | Top gap title can appear in brief head and Huecos | None — by design | T52-DC | Closed |

Any new smoke finding after T50 ★ → new row here or new Field Note; do not reopen T50 scope silently.

**Next process step:** Engineer ★ ACCEPT T52 → tag `v0.7.9`.
