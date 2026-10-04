# Investigation Contract — Chat spoken-continuity map (`INV-assistant-chat-spoken-continuity`)

**Project:** Jarvis  
**Date:** 2026-10-04  
**Author:** JES / Cursor — **INV only**  
**Investigator:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ★ on findings → then DC / IC for the spoken layer  

**Status:** **Implemented (Claude Code)** — await Cursor review → Engineer ★ on findings.  
**Type:** **Investigation** — forensic inventory of every `--chat` egress surface + Continuity fields, ranked for a **deterministic spoken-continuity layer**. **Not** an Implementation Contract. **Not** permission to change speak behavior. **No LLM.**  
**Cola:** **T44-inv**  
**Tip parent:** T43 @ **`0.7.3`** (PASS WITH NOTES — `--chat --voice-speak` speaks printed strings verbatim) · tip package stays **`0.7.3`** (docs/report only)

**Parents:**
- [T43 review](implementation_review_assistant_chat_voice_speak_b1.md) — full chat + ears; same string printed = spoken
- [T34-inv ★](investigation_review_assistant_voice_e2e_b0.md) · [voice channels DC ★](design_contract_assistant_chat_voice_channels_b0.md)
- [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md) — honesty: Continuity/`estado` blocks are long when read aloud
- Engineer lock (2026-10-04): **two layers** — (1) truth = chat Continuity on screen · (2) spoken continuity = extract of what matters for continuity; brief by default; full only when asked; **no LLM** until semantic interpreter Buy

**Why investigate (not jump to IC):** T43 proved the seam works and also proved the product failure mode — loading a project speaks the entire Continuity wall. Before coding a spoken layer, Claude must **map every chat variable / egress surface** and propose what “relevant for continuity” means from **existing structured fields**, plus a **standing norm** so future chat Buys update that map in parallel.

---

## 0. Product goal (locked for the investigation)

Design input (Engineer):  
> Capa de **verdad** = el chat (Continuity completa en pantalla).  
> Capa **por encima** = extracción determinista de lo relevante / importante para dar continuidad.  
> Entra solo cuando se pide (voz / breve). Completo = opt-in. **Sin LLM.**

This INV produces the **inventory + ranking + norm** that a later DC/IC will implement. It does **not** implement the spoken layer.

**Out of this INV forever:** `src/` behavior change · changing T43 speak wiring · LLM summarization · wake-word / mic · T40 world · ACCEPT claim · new architectural subsystem (no Conversation Engine).

---

## 1. Questions this investigation must answer

| # | Question |
|---|---|
| **Q1 — Chat egress inventory** | List **every** string/`print`/`_say`/`speak` surface reachable from `run_chat` today (banner, welcome/picker, help, exit/EOF, startup Continuity, define-wizard opener, turn `render_response` branches, errors, TTS honesty). For each: trigger · symbol (file:line) · typical length · speaks today under `--chat --voice-speak`? |
| **Q2 — Continuity field map** | From `build_project_continuity` / `build_startup_context` / `render_startup_context` / `render_response`: map **structured fields** → **printed sections** (Situación, Evidencia, Siguiente paso, Conceptos, Componentes/gaps, Readiness, TOP GAPS, propulsión, etc.). Cite symbols. Mark which are dict fields vs prose-only render. |
| **Q3 — Speak-vs-print matrix (today)** | With T43 tip: which surfaces are print-only, print+speak, speak-only honesty? Confirm bare `--chat` never calls TTS. |
| **Q4 — Relevance ranking (spoken continuity)** | Propose a **deterministic** ranking of Continuity/chat surfaces for the spoken layer: **must-speak-brief** · **speak-on-request** · **screen-only (never default-speak)**. Justify from product continuity (what lets the Engineer continue), not aesthetics. No LLM. |
| **Q5 — Brief spoken shape** | Recommend the default brief spoken payload as an ordered list of **existing fields** (e.g. situation · next_useful_step · next_useful_why · project status · top gap). State exact field names from code. Explicitly exclude BOM/readiness table unless asked. |
| **Q6 — Full-on-request** | How should “completo” be requested later (command phrase vs flag vs both)? Recommend without implementing. Must not change bare `--chat` default. |
| **Q7 — Non-Continuity turns** | For short Skill replies, craft “Acción ejecutada”, interactive wizards, errors: speak-as-printed vs brief-extract vs screen-only? Propose a simple rule per class. |
| **Q8 — Living map artifact** | Deliver (or fully draft in-report and write) a living inventory note: `.jes/artifacts/engineer_note_chat_spoken_continuity_map.md` — table of surfaces/fields + spoken-continuity class + owner symbols. This is the SoT map the norm will keep updated. |
| **Q9 — Process norm (required)** | Draft a **standing engineering norm** (proposed text) for Claude/Cursor/Engineer: whenever a Buy adds or changes a `--chat` / Continuity / `render_*` egress surface, it must **in the same Buy** (or a linked INV row) update the living map and classify the new surface (brief / on-request / screen-only). Recommend where the norm lands after ★ (e.g. short clause in `CLAUDE.md` + pointer from voice cola note). **Do not** silently edit `CLAUDE.md` in this INV unless Engineer later ★ asks — put the proposed text in the report + living map header. |
| **Q10 — Next Buy recommendation** | After INV ★: DC then IC for spoken-continuity egress, or straight tiny IC? Expected: small **DC** locking two-layer + brief fields, then IC that changes speak path only (truth print unchanged). State clearly. Tip package for code Buy TBD after ★. |
| **Q11 — T40 / craft boundary** | Confirm spoken-continuity layer is about **egress over today's Continuity**, not craft/`world` voice (T40). What craft-specific egress still must be classified in the map? |
| **Q12 — Cola / PRIORIDAD** | What PRIORIDAD wording after INV Implemented; does T40 stay Parked; any connect-plugs one-liner? |

**Out of investigation:** implementing brief speak · LLM rewrite of Continuity · deleting Continuity sections from screen · changing Skill-first brain · tip package bump for code

---

## 2. Forensic method (required)

1. **Re-verify tip** `0.7.3` / T43: `run_chat` / `_chat_speak_fn` / `_say` / `main()` `--voice-speak` wiring.
2. **Trace** project-load Continuity path (the failure mode Engineer hit) with file:symbol citations.
3. **Trace** one short Skill turn (`armar` / `hold`) and one `estado` / `project_status` turn.
4. **Inventory** `render_response` status branches and `render_startup_context` sections.
5. **Grep** for Continuity builders (`build_project_continuity`, `build_startup_context`) — field names, not aspiration.
6. **Do not invent** a second Continuity truth or an LLM summarizer. Prefer extract-from-existing-fields.

---

## 3. Deliverables

| # | Artifact |
|---|---|
| 1 | `.jes/artifacts/investigation_report_assistant_chat_spoken_continuity_b0.md` — answers **Q1–Q12** with file:symbol citations |
| 2 | Living map: `.jes/artifacts/engineer_note_chat_spoken_continuity_map.md` (Q8) — inventory table + proposed norm header |
| 3 | Explicit **brief field list** (Q5) + **next Buy** recommendation (Q10) |
| 4 | Short PRIORIDAD / cola note / `engineering_state`: T44-inv **Implemented** await Cursor review (no ACCEPT claim; no `src/` change) |

**Package:** tip stays **`0.7.3`** for this INV (docs/report only). Spoken-layer **code** Buy opens its own version after DC/IC ★.

---

## 4. Acceptance (investigation)

- [ ] Report answers Q1–Q12 with citations; living map lists every major chat egress + Continuity section  
- [ ] Brief spoken shape uses **existing fields only**; no LLM  
- [ ] Process norm draft is paste-ready for landing after Engineer ★  
- [ ] No `src/` behavior change; tip-pin + ESC fences untouched  
- [ ] Cursor review · Engineer ★ on findings → authorize DC / IC  

---

## 5. Paste for Claude

```text
Investigation — INV-assistant-chat-spoken-continuity (T44-inv)
Parent tip: T43 @ 0.7.3 (PASS WITH NOTES). Tip package stays 0.7.3 (docs only).

INV: .jes/artifacts/investigation_contract_assistant_chat_spoken_continuity_b0.md

Read-only forensic investigation. Engineer lock:
- Layer 1 TRUTH = full --chat / Continuity on screen (unchanged)
- Layer 2 SPOKEN CONTINUITY = deterministic extract of what matters
  for continuity; brief by default; full only when asked
- NO LLM in this layer (LLM later = semantic interpreter only)

Must deliver:
1) investigation_report_assistant_chat_spoken_continuity_b0.md
   answering Q1–Q12 with file:symbol citations
2) Living map engineer_note_chat_spoken_continuity_map.md
   — every chat egress surface + Continuity fields, classified:
   must-speak-brief / speak-on-request / screen-only
3) Default brief spoken shape = ordered EXISTING fields only
4) Draft standing NORM text: future Buys that add/change chat or
   Continuity egress must update this map in the SAME Buy
   (propose CLAUDE.md clause; do NOT silently edit CLAUDE.md here)
5) Next-Buy recommendation (expect small DC then IC for speak path only)
6) PRIORIDAD / cola / engineering_state → Implemented await Cursor review

Forensic: re-verify T43 run_chat/_chat_speak_fn; trace project-load
Continuity (the wall Engineer heard); trace short Skill + estado;
map build_project_continuity / render_startup_context fields.

NOT implementing spoken layer · NOT src/ behavior change ·
NOT LLM summarize · NOT T40 · NOT changing bare --chat ·
NO ACCEPT claim · NO tip pins · NO package bump
```
