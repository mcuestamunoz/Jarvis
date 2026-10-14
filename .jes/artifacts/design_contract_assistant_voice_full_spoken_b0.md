# Design Contract — Voice Continuity FULL narrated (`DC-assistant-voice-full-spoken`)

**Project:** Jarvis  
**Date:** 2026-10-05  
**Author:** JES / Cursor  
**Status:** **Consumed by T52 ★** — Engineer asked for IC after locking FULL-narrado bases; this DC amends T44-DC FULL **payload** only.  
**Type:** Block lock — amend Layer 2 **FULL this turn** speak payload (FN-017)  
**Cola:** **T52-DC**  
**Parents:** [FN-017](engineer_note_voice_spoken_polish_field_fn017.md) · [T44-DC](design_contract_assistant_chat_spoken_continuity_b0.md) · [T51 ★](implementation_review_assistant_voice_brief_spanish_b1.md) @ **`v0.7.8`** · [spoken-continuity map](engineer_note_chat_spoken_continuity_map.md) · tip **`v0.7.8`**

**Not** an Implementation Contract. **Not** permission to implement until the T52 IC is pasted. **No LLM.**

---

## Intent

T44-DC lock 6 fixed **when** FULL fires (finite phrase set, this turn only). T45 implemented FULL as **verbatim `printed_wall`**. Engineer smoke (FN-017) showed that sounds like OCR of the terminal — even after T50 sanitize + T51 brief Spanish.

Product intent (FN-017):

> Layer 1 screen Continuity stays full truth.  
> Layer 2 ear must sound like a short engineering briefing in Spanish — not a reading of the terminal buffer.

**This DC amends only what FULL speaks.** Brief default (`estado` / project load) stays T51. Phrase set / trigger rules stay T44-DC lock 6. Screen stays untouched.

---

## Amendment to T44-DC

| T44-DC | Was (T45 practice) | After this DC |
|---|---|---|
| Lock 6 **trigger** | finite FULL phrase set, this turn only | **unchanged** |
| Lock 6 **payload** | speak exact `printed_wall` | speak **`full_spoken_continuity(ctx)`** — deterministic narrated extract from existing fields (ordered below). Still not a second Continuity; still no LLM |
| Locks 1–5, 7–10 | two layers, no LLM, brief fields, … | **unchanged** (brief already Spanish via T51) |

T44-DC file itself is not rewritten; this document is the SoT amendment for FULL payload. T52 IC implements it.

---

## Plan (cola)

| Step | Cola | Buy | Package | Scope |
|---|---|---|---|---|
| **This DC** | **T52-DC** | `DC-assistant-voice-full-spoken` | no bump | FULL payload locks |
| Code | **T52** | `B1-assistant-voice-full-spoken` | **`0.7.9`** | `full_spoken_continuity` + wire FULL branch |
| Later | own IC | speak propulsion/hover/endurance numbers · Conceptos aloud · expand gap map | TBD | **Out of T52** |
| Parked | **T40** | craft/`world` voice | TBD | **Out** |

---

## Locks (block-level)

| # | Lock |
|---|---|
| 1 | **FULL ≠ print** — on a locked FULL phrase, Layer 2 speaks `full_spoken_continuity(ctx)`, **never** the raw `printed_wall`. Print Layer 1 unchanged |
| 2 | **No LLM** — extract / template existing `startup_context` / continuity / readiness fields only. Honesty: omit missing pieces; do not invent gaps, numbers, or translations beyond the locked maps/templates |
| 3 | **Reuse brief head** — FULL **starts with** the exact output of `brief_spoken_continuity(ctx)` (T45 fields + T51 Spanish status/gap). No divergent brief logic |
| 4 | **Ordered FULL body (after brief head)** — each section omitted when empty; join with newlines; Spanish section headers locked below |
| 5 | **Screen-only even on FULL** — never speak: readiness **subsystems table**; **BOM** / `component_bom_lines`; raw `gap_id` / `depends_on` / severity dumps; `explain_topics` / Conceptos chat-affordance lines; propulsion_resolution / hover_energy / battery_endurance **detail blocks**; English `PROJECT STATUS:` / `ASSEMBLY READY` strings. (Those stay printable truth.) |
| 6 | **Trigger unchanged** — same `FULL_CONTINUITY_PHRASES` / `is_full_continuity_request`. Session does not persist “always full” |
| 7 | **Sanitize still applies** — narrated FULL still passes `speak_egress` → T50 `sanitize_for_speech` (decoration / `la tasa C`) |
| 8 | **Where it lives** — pure function(s) in `adapters/voice/spoken_continuity.py` (or tiny helper beside it). `spoken_text_for_wall` FULL branch returns the narrated string. Prefer **not** editing `run_chat` / `render_*` / `engineering_readiness` |
| 9 | **Living map** — T52 updates [spoken-continuity map](engineer_note_chat_spoken_continuity_map.md): FULL = narrated extract (not verbatim wall); mark T52 screen-only rows explicitly |
| 10 | **Out unless a later IC ★** — LLM summary · speaking BOM/tables · speaking Conceptos affordance · propulsion/hover/endurance number briefing · wake-word · T40 · recorting screen Continuity · Conversation Engine · changing brief default · ACCEPT claim |

---

## Locked FULL body (after brief head)

| Order | Source | Speak (locked templates / rules) |
|---|---|---|
| A | `continuity.evidence` (≤6, same cap as print) | Header `Evidencia:` then each item as its own line (item text as stored — no invent) |
| B | `readiness.prioritized_gaps[:3]` | Header `Huecos prioritarios:` then per gap: title via **same T51 gap-title speak map** (unknown → raw title); if `recommended_next_step.action` present → next line `Siguiente: {action}`. Do **not** speak `gap_id`, `blocks`, `depends_on`, or severity codes |
| C | `architecture_progress` (+ optional `next_architecture_label` / `next_block_status`) | If progress present and label present → `Arquitectura {progress}. Siguiente bloque: {label}` (+ ` en progreso` if `next_block_status == "in_progress"`). If progress present and no label → `Arquitectura {progress}. Completa.` |
| D | `physical_requirements_lines` | Header `Requisitos físicos:` then each line as stored (omit section if empty) |
| E | `prop_energy_block_closure` | One line only: if `status == "closed"` → `Bloque propulsión y energía: cerrado.`; else → `Bloque propulsión y energía: no cerrado.` (tier/facts detail stays screen-only this Buy) |

If after brief head every A–E section is empty, speak the brief head alone (still valid FULL — just no extra detail available).

---

## Operator picture (after T52)

```text
python -m jarvis.main --chat --voice-speak
User > 1
Jarvis >                        # screen: full Continuity wall (English readiness OK)
                                # ears: T51 brief Spanish
User > completo
Jarvis >                        # screen: same full wall
                                # ears: brief head + Evidencia / Huecos / Arquitectura / …
                                #        NOT ──── / BOM table / subsystem PASS rows
```

---

## Opens

T52 IC: [`implementation_contract_assistant_voice_full_spoken_b1.md`](implementation_contract_assistant_voice_full_spoken_b1.md). Tip stays **`v0.7.8`** until T52 opens **`0.7.9`**.

SoT: [FN-017](engineer_note_voice_spoken_polish_field_fn017.md) · [phase cola](engineer_note_voice_phase_c_cola.md) · [`docs/IMPLEMENTATION_TASKS.md`](../../docs/IMPLEMENTATION_TASKS.md) PRIORIDAD
