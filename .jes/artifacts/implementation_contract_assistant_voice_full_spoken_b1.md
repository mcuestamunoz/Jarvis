# Implementation Contract — Voice Continuity FULL narrated (`B1-assistant-voice-full-spoken`)

**Project:** Jarvis  
**Date:** 2026-10-05  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.7.9`**

**Status:** **Cursor PASS WITH NOTES** — await Engineer ★ ACCEPT → tag **`v0.7.9`**.  
**Parents:** [T52-DC](design_contract_assistant_voice_full_spoken_b0.md) · [FN-017](engineer_note_voice_spoken_polish_field_fn017.md) · [T51 ★](implementation_review_assistant_voice_brief_spanish_b1.md) @ **`v0.7.8`** · tip **`39e996c`** / package **`0.7.9`** · [review](implementation_review_assistant_voice_full_spoken_b1.md)  
**Type:** Speak-path only — replace FULL Continuity speak payload with narrated field extract. **Print / Layer 1 untouched.** Brief path untouched.  
**Opens:** **`0.7.9` / `v0.7.9`**. **Cola:** **T52**

**Not:** LLM · speaking BOM / readiness subsystem table · Conceptos affordance aloud · propulsion/hover/endurance number briefing · wake-word · T40 · changing FULL phrase triggers · changing brief default · speech deps · ACCEPT claim.

---

## Why this Buy

After T50–T51, `estado` sounds like a Spanish briefing, but `completo` (and the locked FULL set) still speaks the **printed wall** (post-sanitize). FN-017: ear-truth must be narrated detail from fields, not terminal OCR. T52-DC locks the payload; this IC implements it.

---

## 0. Engineer Buy (locked from T52-DC)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-voice-full-spoken`** — narrated FULL Layer 2 for Continuity walls |
| 2 | **Wire** — in `spoken_text_for_wall`, when `is_full_continuity_request(raw_text)`: return `full_spoken_continuity(ctx)` (new), **not** `printed_wall`. Prefer **not** editing `run_chat` / any `render_*` |
| 3 | **`full_spoken_continuity(ctx)`** — if no project / empty: `""`. Else: start with **exact** `brief_spoken_continuity(ctx)` string, then append locked body sections A–E from T52-DC (omit empty). Newline-join. Do not invent fields |
| 4 | **Body A–E** — as locked in [T52-DC](design_contract_assistant_voice_full_spoken_b0.md): Evidencia (≤6) · Huecos prioritarios (≤3, T51 title map, `Siguiente:` action only) · Arquitectura one-liner · Requisitos físicos · cierre propulsión/energía one-liner (`cerrado` / `no cerrado`) |
| 5 | **Screen-only fence** — narrated FULL must **never** contain: `PROJECT STATUS` / `ASSEMBLY READY` · subsystem table labels/verdicts as a table · BOM lines · `gap_id` / `depends_on` · Conceptos / `jarvis explain` affordance lines · box-drawing rule lines (T50 still sanitizes if any slip through) |
| 6 | **Brief unchanged** — non-FULL wall turns still `brief_spoken_continuity` only (T51). No behavior change on `estado` |
| 7 | **Print untouched** — prove with test: rendered wall still has English `PROJECT STATUS` / can still show BOM when present; FULL speak does not |
| 8 | **Sanitize** — no new wire needed if FULL still goes through `speak_egress` (it must). Do not bypass sanitize |
| 9 | **Tests T1–T7** — see §2 |
| 10 | **Docs** — guide §4.1: `completo` = narrated detail, not reading the wall; living spoken-continuity map FULL row updated; PRIORIDAD/cola/FN-017/PLATFORM/CONNECTIONS short |
| 11 | **Version** `pyproject` → **`0.7.9`** |
| 12 | **Out:** LLM · BOM/table speech · Conceptos speech · prop/hover/endurance numbers · expanding T51 gap map · T40 · ACCEPT claim |

---

## 1. Files

| Path | Change |
|---|---|
| `src/jarvis/adapters/voice/spoken_continuity.py` | add `full_spoken_continuity`; FULL branch of `spoken_text_for_wall` uses it |
| `src/jarvis/adapters/voice/__init__.py` | export if siblings are exported |
| `tests/test_assistant_voice_full_spoken_b1.py` | **new** T1–T7 |
| `tests/test_assistant_chat_spoken_continuity_b1.py` | update any assertion that FULL speak == printed wall / contains `PROJECT STATUS` from the wall |
| `docs/USER_GUIDE_VOICE.md` | §4.1 FULL = narrated detail |
| `.jes/artifacts/engineer_note_chat_spoken_continuity_map.md` | FULL override = narrated extract; screen-only fence for T52 |
| `pyproject.toml` | `0.7.8` → **`0.7.9`** |
| FN-017 / cola / PRIORIDAD / PLATFORM / CONNECTIONS / state | T52 Implemented await review |

Prefer **not** touching `adapters/cli/main.py`, `engineering_readiness`, orchestrator, or `speak_sanitize.py` (reuse as-is).

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | FULL request (`completo`) with fixture ctx → speak text **contains** brief Spanish status (`Estado del proyecto:`) and **does not** contain `PROJECT STATUS` / `ASSEMBLY READY` |
| T2 | Same FULL path with evidence items → speaks `Evidencia:` + items; items absent → no Evidencia header |
| T3 | Gaps: mapped title for `Autonomy target not met`; unknown title raw; **no** `gap_id` like `GAP-` in speak text; `Siguiente:` present when `recommended_next_step.action` set |
| T4 | `spoken_text_for_wall("completo", printed_wall, ctx) != printed_wall` when wall is a long Continuity print; `spoken_text_for_wall("estado", …)` still equals brief (not full body) |
| T5 | Screen-only fence: even if ctx has `component_bom_lines` and readiness subsystems, FULL speak contains neither BOM line text nor a subsystem `PASS` table row pattern; real `_render_readiness_block` / wall render still shows `PROJECT STATUS` |
| T6 | Architecture + block_closure templates fire when fields present (`Arquitectura` / `Bloque propulsión y energía`) |
| T7 | `0.7.9` · no speech deps · tip-pin + ESC · `run_chat` TTS source guard still empty · guide mentions narrated `completo` |

---

## 3. Acceptance

- [ ] `completo` / FULL set: ears get brief head + narrated sections; screen still full Continuity wall  
- [ ] `estado` brief unchanged (T51) · no BOM/table OCR · no LLM  
- [ ] `0.7.9` · Cursor review · Engineer ACCEPT → tag **`v0.7.9`**

---

## 4. Paste for Claude

```text
Implementation — B1-assistant-voice-full-spoken (T52)
Parent tip: v0.7.8 (T51 ★). Package -> 0.7.9.
FN-017: .jes/artifacts/engineer_note_voice_spoken_polish_field_fn017.md
DC: .jes/artifacts/design_contract_assistant_voice_full_spoken_b0.md
IC: .jes/artifacts/implementation_contract_assistant_voice_full_spoken_b1.md
Map: .jes/artifacts/engineer_note_chat_spoken_continuity_map.md

Speak-path ONLY — FULL Continuity narrated (print/Layer 1 untouched; brief T51 untouched):
- spoken_text_for_wall: FULL phrase -> full_spoken_continuity(ctx), NEVER printed_wall
- full_spoken_continuity = brief_spoken_continuity(ctx) + body A-E (omit empty):
  A. Evidencia: continuity.evidence[:6]
  B. Huecos prioritarios: gaps[:3] — T51 title map; Siguiente: action only;
     never gap_id / depends_on / severity
  C. Arquitectura {progress}. Siguiente bloque: {label} [en progreso] | Completa.
  D. Requisitos físicos: physical_requirements_lines
  E. Bloque propulsión y energía: cerrado. | no cerrado.
- Screen-only even on FULL: BOM, subsystems table, Conceptos, prop/hover/endurance
  detail blocks, English PROJECT STATUS
- Prefer NOT editing run_chat / render_* / engineering_readiness / speak_sanitize
- Update T45 tests that asserted FULL == printed wall
- Tests T1-T7; pyproject 0.7.9; guide §4.1 + living map; PLATFORM/CONNECTIONS
NO LLM · NOT T40 · NOT wake-word · NOT speaking BOM/tables
NO ACCEPT claim
```
