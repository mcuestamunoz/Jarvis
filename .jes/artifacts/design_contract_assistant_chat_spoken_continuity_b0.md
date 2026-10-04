# Design Contract — Chat spoken continuity (`DC-assistant-chat-spoken-continuity`)

**Project:** Jarvis  
**Date:** 2026-10-04  
**Author:** JES / Cursor  
**Status:** **DC ready** — Engineer asked to lock the plan in the voice phase before the IC.  
**Type:** Block lock — **V7** spoken-continuity layer over T43 `--chat --voice-speak`  
**Cola:** **T44-DC**  
**Parents:** [T44-inv review](investigation_review_assistant_chat_spoken_continuity_b0.md) · [INV report](investigation_report_assistant_chat_spoken_continuity_b0.md) · [living map](engineer_note_chat_spoken_continuity_map.md) · [T43 review](implementation_review_assistant_chat_voice_speak_b1.md) · [voice channels DC ★](design_contract_assistant_chat_voice_channels_b0.md) · tip **`0.7.3`**

**Not** an Implementation Contract. **Not** permission to implement until the T45 IC is pasted. **No LLM.**

---

## Intent

T43 made `--chat --voice-speak` hear every printed `Jarvis >` string. Continuity walls (project load + `estado`) are the engineering **truth** on screen and unusable as speech.

Engineer lock (2026-10-04): two layers.

> Capa de **verdad** = el chat (Continuity completa en pantalla).  
> Capa **por encima** = extracción determinista de lo relevante para dar continuidad.  
> Entra cuando hay voz. Completo = opt-in. **Sin LLM** (el LLM entra más adelante solo como intérprete semántico de *entrada*).

This DC locks that plan so T45 stays a narrow speak-path Buy.

---

## Plan (cola V7)

| Step | Cola | Buy | Package | Scope |
|---|---|---|---|---|
| Map | **T44-inv** | `INV-assistant-chat-spoken-continuity` | `0.7.3` docs | Inventory + ranking + living map |
| **This DC** | **T44-DC** | `DC-assistant-chat-spoken-continuity` | no bump | Product locks |
| First code | **T45** | `B1-assistant-chat-spoken-continuity` | **`0.7.4`** | Walls only: print full / speak brief; full phrases this turn |
| Later | own IC | craft footer / reasoning if still too long | TBD | **Out of T45** |
| Parked | **T40** | craft/`world` voice | TBD | **Out of V7** |

Each step independently ★-able. T45 must not wait on T41/T42/T43 ACCEPT tags.

---

## Locks (block-level)

| # | Lock |
|---|---|
| 1 | **Two layers** — Layer 1 (screen) is the only engineering truth. Layer 2 never invents, never recorta the print, never becomes a second Continuity |
| 2 | **No LLM** in Layer 2. Extract existing dict fields only. LLM later = semantic *ingress* interpreter, not state rewrite |
| 3 | **Brief by default** under `--chat --voice-speak` for **Continuity-shaped walls**: (a) project-load `startup_block`, (b) `action == "project_status"` / `estado` via `CONTINUITY_DEFER_PHRASES`. Other turns (Skills, errors, wizards, craft `Acción ejecutada` bodies) stay **speak-as-printed** in T45 |
| 4 | **Brief payload (ordered, existing fields only):** `continuity["situation"]` · `continuity["next_useful_step"]` · `continuity["next_useful_why"]` (omit if empty; **same `_humanize_next_useful_why` as the wall**, not the raw footer) · one phrase from `readiness["overall"]` matching the `PROJECT STATUS:` line (`ASSEMBLY READY` / `NOT ASSEMBLY READY`) · `readiness["prioritized_gaps"][0]["title"]` if the list is non-empty. Skip missing pieces; join with newlines; skip empty result (then speak nothing extra) |
| 5 | **Explicitly not in brief:** `evidence`, BOM/`component_bom_lines`, readiness subsystem table, propulsion/hover/endurance blocks, `explain_topics`, block-closure paragraph |
| 6 | **Full this turn only** — finite phrase set, zero-LLM, same normalize/exact-match family as `CONTINUITY_DEFER_PHRASES`. Locked FULL set: `completo`, `estado completo`, `dame detalles`, `dame detalles del proyecto`, `detalles del proyecto`, `cuentame todo`, `cuentame el proyecto`, `cuenta el proyecto`, `describe el proyecto`, `explica el proyecto` (plus the same strings after the existing Continuity phrase normalizer). Screen still full. Session does **not** persist “always full” |
| 7 | **Bare `--chat`** stays text-only. `--voice` (T42) unchanged (Skills-only; no Continuity wall there) |
| 8 | **Where the extractor lives** — pure function in `adapters/voice/` (e.g. `spoken_continuity.py`). Called from the **speak** path in `run_chat` / `_chat_speak_fn` companion — **not** from `render_startup_context` / `render_response` (those stay Layer 1). No orchestrator Continuity ranking change |
| 9 | **Living map** — T45 updates [engineer_note_chat_spoken_continuity_map.md](engineer_note_chat_spoken_continuity_map.md) classifications to match shipped behavior. Future chat/Continuity/`render_*` Buys update the map in the same Buy (`CLAUDE.md` clause) |
| 10 | **Out unless a later IC ★** — LLM summary · wake-word/always-on mic · T40 world · changing default `--chat` to speak · speaking banner/welcome · Conversation Engine · recorting screen Continuity |

---

## Review notes absorbed (T44-inv Cursor N1–N4)

- **N1** — Continuity `return` is `project_continuity.py:676–682` (fix map citations in T45 docs). Keys were already correct.  
- **N2** — brief `why` = wall humanize, not raw footer.  
- **N3** — phrase split is lock 6; do not treat every `CONTINUITY_DEFER_PHRASES` member as brief or as full.  
- **N4** — reasoning-without-footer stays speak-as-printed in T45 (speak-on-request later).

---

## Opens

T45 IC: [`implementation_contract_assistant_chat_spoken_continuity_b1.md`](implementation_contract_assistant_chat_spoken_continuity_b1.md). Tip stays **`0.7.3`** until T45 opens **`0.7.4`**.

**Later (2026-10-04, does not reopen this DC):** **V8 PTT** is a sibling ingress Buy on the same `--chat --voice-speak` session — [T46-DC](design_contract_assistant_chat_voice_ptt_b0.md). V7 stays egress-only.

SoT: [phase cola](engineer_note_voice_phase_c_cola.md) · [`docs/IMPLEMENTATION_TASKS.md`](../../docs/IMPLEMENTATION_TASKS.md) PRIORIDAD
