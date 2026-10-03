# Investigation Contract — Assistant voice end-to-end (`INV-assistant-voice-e2e`)

**Project:** Jarvis  
**Date:** 2026-10-03  
**Author:** JES / Cursor — **INV only**  
**Investigator:** **Claude Code** — ★ AUTHORIZED with this delivery (read-only forensic map + phased design recommendation)  
**Reviewer:** Cursor on request · Engineer ★ on findings → then DC / phased ICs

**Status:** **Implemented** (Claude Code) — report delivered, await Cursor review → Engineer ★ on findings (no `src/` mutation).  
**Type:** **Investigation** — map seams and recommend a clean **phased** path to full voice Jarvis using **what exists today**. **Not** an Implementation Contract. **Not** permission to implement STT/TTS/voice.  
**Cola:** **T34-inv**  
**Tip parent:** T33 ★ ACCEPT CLOSED @ **`v0.6.42`** · T32 ★ @ **`v0.6.41`** (SD-GO_TO CLOSED) · Skill-first phase B ★ @ **`v0.6.40`**

**Parents:**
- [DC Skill-first ★](design_contract_assistant_chat_skill_first_b0.md) — phase **C — channels**: voz / world / CLI migrate · **same Skills; new ingress only**
- [DC placement ★](design_contract_assistant_placement_b0.md) — A4 voz/world **Parked**; Voice = Intent peer; `world/` not on disk
- [Connect-plugs map ★](engineer_note_connect_plugs_real_data_map.md) — rows `voice-intent-ingress` · `a4-voice-world` · `world-package` · `go-to-metadata-plug-for-world`
- C2 Intent stub ★ — `TerminalIntentAdapter` only producer; `VoiceIntentAdapter` always `NotImplementedError`
- Twelve chat Skills Skill-first (explain → CHARGE) · T20 sim copper · T32 GO_TO destination plug

**Why investigate (not jump to IC):** Voice is a **channel** over an already-complete Skill-first brain, but also touches audio I/O (absent), egress (TTS vs print), craft Continuity/wizards (session+LLM, not in the twelve Skills), optional `world/`, Safety/authority boundaries, and “phased CLI migrate.” Jumping to one big voice Buy would invent seams or couple STT to craft. This INV must produce a **phase plan that fits the code as-is**.

---

## 0. Product goal (locked for the investigation)

Engineer wants the option of **Jarvis completo a modo voz de principio a fin** with **Jarvis as it is today** — not a new product, not a house-automation demo, not inventing copper/flight.

**End-to-end** means: user speaks → Jarvis understands intent within today's surfaces → same brain as chat (Skills / orch fulfills / honesty) → spoken (or equivalently complete) reply — **designed in phases**, each Buy small and harmonious.

**Out of this INV's implementation scope (forever for this Buy):** writing `src/` · shipping STT/TTS · creating `world/` · flipping `flight.*` to available · live ESC · closing Roadmap debts by prose alone.

---

## 1. Questions this investigation must answer

| # | Question |
|---|---|
| **Q1 — Ingress boundary** | What is the thinnest honest voice→`Intent` seam today? Exact symbols (`VoiceIntentAdapter`, `IntentSource.VOICE`, `Intent.metadata`). What payload shape should `parse` accept (raw text after external STT vs audio bytes)? Cite file:line. |
| **Q2 — Chat brain reuse** | Map the exact `--chat` chain: CLI → `handle_user_text` → `_handle_global_commands` → `run_skill` → fulfill. Which pieces are **channel-agnostic** (Skills, classify `try_*`, orch handlers) vs **terminal-hardcoded** (`TerminalIntentAdapter.parse` call sites, CLI `render_response`)? List symbols that would need a voice peer vs reuse unchanged. |
| **Q3 — Surface inventory (today)** | For each product surface reachable from chat today, state: (a) Skill-first twelve, (b) craft Continuity/wizards/LLM fallthrough, (c) sibling CLI (`jarvis explain`, `board`). Which belong in **voice v1**, which in later phases, which never voice? Justify from code, not aspiration. |
| **Q4 — Audio I/O (STT/TTS)** | Confirm absence of speech packages/deps. Recommend ownership options **without picking a vendor**: (A) external STT → text into adapter, TTS outside; (B) in-repo adapters behind NotImplemented until wired; (C) defer audio entirely and first Buys are text-shaped voice Intent only. Pros/cons vs fences (`intelligence/` isolation, no tip pins). |
| **Q5 — Egress** | Chat returns `dict` → CLI prints. What is a clean speak path that does **not** fork domain logic? Adapter after result? Orch-agnostic renderer? Out of first phase? |
| **Q6 — GO_TO / metadata** | T32 plug `go_to_x_m`/`go_to_y_m` is ready. For voice: prove-now spoken coords vs metadata-only vs deferred. Relation to `go-to-metadata-plug-for-world` row. |
| **Q7 — `world/` and A4** | Is `world/` required for “voz de principio a fin” with Jarvis **today**, or is voice-over-chat-surfaces enough for phase C.1 and world stays a later sibling (placement DC)? Recommend explicit split. |
| **Q8 — Safety / authority** | Voice must not become a kill-switch/ESC path. Confirm locks: same ArmedAllowlist honesty as chat; C0 radio dual-role stays separate; no new Authority surface unless Engineer ★. |
| **Q9 — Phased CLI migrate** | Docs say “phased CLI migrate (phase C).” What does that mean operationally given code today? Options: voice flag beside `--chat`; shared ingress helper extracted from orch; later migrate craft CLI. Recommend order that avoids a big-bang rewrite. |
| **Q10 — Phase plan (required deliverable)** | Propose **3–7 named phases** (indicative Buy ids + package bumps TBD). Each phase: goal · in · out · depends on · primary files likely touched · risk if skipped. Phases must be **independently ★-able** and prefer reuse of `run_skill` + existing fulfills. |
| **Q11 — First Buy recommendation** | After INV ★: go to **DC** (block lock) then IC, or straight to a tiny first IC? Expected: **DC voice/channels block** then first IC (likely Intent ingress prove-now). State recommendation clearly. |
| **Q12 — Map / PRIORIDAD updates** | Which connect-plugs rows change status wording after INV ★ (still OPEN, but “INV done → DC next”)? What PRIORIDAD cola rows to add (T34 DC, T35…)? |

**Out of investigation:** implementing voice · choosing a cloud STT vendor as lock · building `world/` · rewriting Continuity · copper · claiming phase C CLOSED

---

## 2. Forensic method (required)

1. **Re-verify tip** (`v0.6.42` lineage): do not assume seed status from the connect-plugs map — confirm symbols in `src/` + tests + PRIORIDAD.
2. **Trace one happy path** in chat (e.g. `armar` → `hold` → `go to 1.0 2.0`) with file:symbol citations; then state what a voice twin would call.
3. **Trace one craft path** (e.g. Continuity `estado` or wizard) and mark whether voice v1 should include it.
4. **Grep** for `VoiceIntentAdapter`, `IntentSource.VOICE`, STT/TTS/speech deps, `world/` package — report absence with evidence.
5. **Do not invent** new architectural subsystems (no Conversation Engine, no parallel Skill runtime). Prefer seams already named in C2 / Skill-first DC / T32 metadata plug.

---

## 3. Deliverables

| # | Artifact |
|---|---|
| 1 | `.jes/artifacts/investigation_report_assistant_voice_e2e_b0.md` — answers **Q1–Q12** with file:symbol citations |
| 2 | Explicit **phase table** (Q10) + **first Buy** recommendation (Q11) |
| 3 | Short PRIORIDAD / `engineering_state` update: T34-inv **Implemented** await Cursor review → Engineer ★ (no ACCEPT claim; no `src/` change) |
| 4 | Optional one-line pointers from [connect-plugs map](engineer_note_connect_plugs_real_data_map.md) rows `voice-intent-ingress` / `a4-voice-world` → this INV (status stays OPEN/Parked until a later Buy) |

**Package:** tip stays **`0.6.42`** for this INV (docs/report only). First voice **code** Buy opens its own version after DC ★.

---

## 4. Acceptance (investigation)

- [ ] Report answers Q1–Q12 with citations; phase plan is independently ★-able  
- [ ] No `src/` behavior change; tip-pin + ESC fences untouched  
- [ ] Cursor review · Engineer ★ on findings → authorize DC / first IC  

---

## 5. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED investigation — INV-assistant-voice-e2e (T34-inv)
Parent tip: T33 ★ ACCEPT CLOSED @ v0.6.42 (stacks T32 ★ @ v0.6.41). Tip package stays 0.6.42.

INV: .jes/artifacts/investigation_contract_assistant_voice_e2e_b0.md

Read-only forensic investigation + phased design recommendation.
Goal: path to full Jarvis voice end-to-end using Jarvis as it exists today
(Skill-first twelve Skills, chat orch fulfills, T32 GO_TO metadata plug,
honesty locks) — NOT a new product, NOT house/world demo required for v1.

Must deliver:
- investigation_report_assistant_voice_e2e_b0.md answering Q1–Q12
  with file:symbol citations
- Phase table (3–7 phases), each independently ★-able; prefer
  run_skill + existing fulfills; no parallel brain
- First-Buy recommendation (expect DC then tiny Intent-ingress IC)
- PRIORIDAD / engineering_state: Implemented await Cursor review
- Optional one-line pointers on connect-plugs map voice rows
  (do NOT mark debts CLOSED)

Forensic: re-verify tip; trace chat happy path + one craft path;
confirm VoiceIntentAdapter NotImplemented + no STT/TTS deps + no world/.

NOT implementing voice/STT/TTS · NOT creating world/ · NOT src/ behavior
change · NOT picking a cloud STT vendor as architecture lock ·
NO ACCEPT claim · NO tip pins.
```
