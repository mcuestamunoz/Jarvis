# Engineer note — Voice phase C cola (Skill-first channels)

**Date:** 2026-10-03 · **updated:** 2026-10-05 (T47 Cursor PASS WITH NOTES)  
**Status:** **OPEN living cola index** — voice v1 ★ @ `v0.7.0`; operator/use path T41–T43; spoken-continuity V7 in design; **V8 PTT** Cursor **PASS WITH NOTES**  
**Authority:** Engineer — this note is how the voice phase is **designed and implemented**, not a vendor roadmap. Engineer paste of an IC to Claude = Buy (no separate AUTHORIZED stamp).  
**Tip parent:** **`0.7.5`** (T47 tip) · **T46-DC** PTT lock · **T47** Cursor **PASS WITH NOTES** @ **`0.7.5`** (await Engineer ★ ACCEPT) · T45 Cursor **PASS WITH NOTES** (await Engineer ★ ACCEPT)

**Parents:** [T34-DC ★](design_contract_assistant_chat_voice_channels_b0.md) · [T34-inv review ★](investigation_review_assistant_voice_e2e_b0.md) · [Skill-first DC ★](design_contract_assistant_chat_skill_first_b0.md) · [connect-plugs map](engineer_note_connect_plugs_real_data_map.md) · [spoken-continuity map](engineer_note_chat_spoken_continuity_map.md) · [T44-DC](design_contract_assistant_chat_spoken_continuity_b0.md)

---

## How this phase is designed (process)

```text
INV (map seams) → DC (lock product) → IC (small Buy) → Cursor review → Engineer ★
```

- **Cursor** writes INV/DC/IC and reviews after code exists. Does not implement `src/` for that IC unless Engineer says so.  
- **Claude** implements the pasted IC and writes the report.  
- **Engineer** ★ ACCEPT / tags. Same-session self-PASS is not review of record.  
- Future Buys that add/change `--chat` / Continuity / `render_*` egress update the [spoken-continuity map](engineer_note_chat_spoken_continuity_map.md) **in the same Buy** ([norm in `CLAUDE.md`](../../CLAUDE.md)).

---

## Product picture

### Voice v1 (T35–T39 ★) — same brain, new channel

```text
[fixture / mic] → STT → text → VoiceIntentAdapter(VOICE)
  → handle_user_text → run_skill → _handle_* (same as chat)
  → render_response → TTS → [speaker]
```

**In v1:** twelve Skill-first Skills.  
**Out of v1:** craft wizards/LLM, `world/`, board, Authority/kill, copper.

### Operator / use path (T41–T43)

| Path | Brain | Speaks |
|---|---|---|
| `--voice` | Skills only (`source=VOICE`) | always (via `_voice_speak_fn`) |
| `--chat` | full Continuity / craft / LLM (`TERMINAL`) | never |
| `--chat --voice-speak` | **same full chat** | T43: **verbatim printed string** (the wall) · T45: brief on walls |
| `--chat --voice-speak` + typed `hablar`/`habla` | **same full chat** (`TERMINAL`) | **T47:** timed record → existing STT → same loop (keyboard stays) |

T43 proved the seam and the failure mode: loading a project / typing `estado` **prints** Continuity (correct truth) and **speaks the entire wall** (unusable). T45 fixed the ear. Engineer then locked **V8**: speak into the air **inside that session** as push-to-talk — not `--voice`, not `--voice-audio` one-shot, not always-on.

### Spoken continuity (V7 — T44-inv → T44-DC → T45)

Two layers, no LLM:

```text
Layer 1 TRUTH (screen)     = full Continuity / chat  — never recortada
Layer 2 SPOKEN CONTINUITY  = deterministic extract   — breve by default
                            full wall only when asked
```

```text
run_chat print  → Layer 1 (unchanged)
         speak  → Layer 2 extractor (Continuity-shaped walls only)
                → speak_egress / JARVIS_TTS_CMD
```

**Not** a second Continuity. **Not** an LLM rewrite. Fields already computed by `build_project_continuity` / `build_startup_context`.

---

## Cola (ordered)

| # | Phase | Buy id | Package | Estado | Qué | Gate |
|---|---|---|---|---|---|---|
| **T34-inv** | — | `INV-assistant-voice-e2e` | — | ✅ ★ CLOSED | Forensic map + phase plan | [review ★](investigation_review_assistant_voice_e2e_b0.md) |
| **T34-DC** | V0 | `DC-assistant-chat-voice-channels` | — | ✅ ★ CLOSED | Block locks (same brain · text ingress · twelve Skills · STT/TTS external) | [DC ★](design_contract_assistant_chat_voice_channels_b0.md) |
| **T35** | V1 | `B1-assistant-voice-intent-ingress` | `0.6.43` | ✅ ★ **ACCEPT CLOSED** @ **`v0.6.43`** | `VoiceIntentAdapter` + `source` threading (12 sites) | [review ★](implementation_review_assistant_voice_intent_ingress_b1.md) |
| **T36** | V2 | `B1-assistant-voice-fixture-loop` | `0.6.44` | ✅ ★ **ACCEPT CLOSED** @ **`v0.6.44`** | New `adapters/voice/` package; fixture-driven `run_voice` loop | [review ★](implementation_review_assistant_voice_fixture_loop_b1.md) |
| **T37** | V3 | `B1-assistant-voice-stt-external` | `0.6.45` | ✅ ★ **ACCEPT CLOSED** @ **`v0.6.45`** | External STT process seam → same parse | [review ★](implementation_review_assistant_voice_stt_external_b1.md) |
| **T38** | V4 | `B1-assistant-voice-tts-external` | `0.6.46` | ✅ ★ **ACCEPT CLOSED** @ **`v0.6.46`** | External TTS process seam on `render_response` | [review ★](implementation_review_assistant_voice_tts_external_b1.md) · [brief](engineer_note_voice_tts_product_brief.md) |
| **T39** | V5 | `B1-assistant-voice-v1-checkpoint` | **`0.7.0` / `v0.7.0`** | ✅ ★ **ACCEPT CLOSED** @ **`v0.7.0`** | **Product milestone** — speak → twelve Skills → spoken reply | [review ★](implementation_review_assistant_voice_v1_checkpoint_b1.md) |
| **T41** | — | `B1-assistant-voice-demo-ready` | `0.7.1` | Implemented · Cursor **PASS WITH NOTES** (ACCEPT deferred) | Operator wrappers + guide + fixture (batch) | [review](implementation_review_assistant_voice_demo_ready_b1.md) · [guía](../../docs/USER_GUIDE_VOICE.md) |
| **T42** | — | `B1-assistant-voice-interactive-cli` | `0.7.2` | Implemented · Cursor **PASS WITH NOTES** | Skills-only `--voice` REPL | [review](implementation_review_assistant_voice_interactive_cli_b1.md) |
| **T43** | — | `B1-assistant-chat-voice-speak` | `0.7.3` | Implemented · Cursor **PASS WITH NOTES** | Full `--chat` + speak (verbatim) | [review](implementation_review_assistant_chat_voice_speak_b1.md) |
| **T44-inv** | V7 | `INV-assistant-chat-spoken-continuity` | `0.7.3` (docs) | Implemented · Cursor **PASS WITH NOTES** | Inventory of every `--chat` egress + Continuity fields | [review](investigation_review_assistant_chat_spoken_continuity_b0.md) · [map](engineer_note_chat_spoken_continuity_map.md) |
| **T44-DC** | V7 | `DC-assistant-chat-spoken-continuity` | — (no bump) | **DC ready** | Two-layer lock · brief fields · phrase split · first-slice = walls only | [DC](design_contract_assistant_chat_spoken_continuity_b0.md) |
| **T45** | V7 | `B1-assistant-chat-spoken-continuity` | **`0.7.4`** | Implemented · Cursor **PASS WITH NOTES** | Extractor on speak path; screen truth untouched | [review](implementation_review_assistant_chat_spoken_continuity_b1.md) |
| **T46-DC** | V8 | `DC-assistant-chat-voice-ptt` | — (no bump) | **DC ready** — locked, consumed by T47 | PTT lock · timed record · `hablar`/`habla` · same `run_chat` · no wake-word | [DC](design_contract_assistant_chat_voice_ptt_b0.md) |
| **T47** | V8 | `B1-assistant-chat-voice-ptt` | **`0.7.5`** | Implemented · Cursor **PASS WITH NOTES** | Record seam + intercept on `--chat --voice-speak`; reuse T37 STT | [review](implementation_review_assistant_chat_voice_ptt_b1.md) |
| **T40** | V6 | craft / `world/` voice | TBD | **Parked** — own DC | Not voice v1 · not V7 · not V8 | [placement A4](design_contract_assistant_placement_b0.md) |

**Versioning:** T35–T38 = `0.6.43`…`0.6.46` (construcción). **T39 ★** = hito **`0.7.0`**. T41–T43 = use-path patches on `0.7.x`. **T45** opens **`0.7.4`**. **T47** opens **`0.7.5`**.

---

## V7 plan (spoken continuity) — how we implement it

Ordered, independently ★-able:

| Step | Buy | What ships | What does not |
|---|---|---|---|
| 1 | T44-inv | Map + ranking + norm draft | no `src/` |
| 2 | T44-DC | Product locks (this plan) | no `src/` |
| 3 | **T45 IC** | Layer 2 on **Continuity walls only** (project load + `estado` / `project_status`): print full, speak brief; `dame detalles` / `completo` / sibling phrases speak the wall this turn | no LLM · no change to bare `--chat` · no T40 · craft-turn bodies stay speak-as-printed |
| 4 | Later (own IC, not T45) | Craft `coherence_footer` / reasoning-without-footer if live use still too long | not in T45 |
| 5 | After Engineer ★ T44-inv/DC | Norm already pointed from `CLAUDE.md`; map stays living SoT | — |

**Default brief (existing fields, ordered):**

1. `continuity["situation"]`  
2. `continuity["next_useful_step"]`  
3. `continuity["next_useful_why"]` (omit if empty; **humanize like the wall**)  
4. Phrase from `readiness["overall"]` (`ASSEMBLY READY` / `NOT ASSEMBLY READY`)  
5. `readiness["prioritized_gaps"][0]["title"]` if present (title only)

**Phrase split (finite, zero-LLM, same intercept family as `CONTINUITY_DEFER_PHRASES`):**

- **Speak brief** (default): project load; `estado`, `resumen`, `situacion`, `donde estamos`, `que falta`, `siguiente paso`, … — screen still full.  
- **Speak full this turn:** `completo`, `estado completo`, `dame detalles`, `dame detalles del proyecto`, `detalles del proyecto`, `cuentame todo`, `cuentame el proyecto`, `cuenta el proyecto`, `describe el proyecto`, `explica el proyecto`.

---

## V8 plan (push-to-talk) — how we implement it

Engineer (2026-10-04): after T45, `--chat --voice-speak` already talks until session end. Gap = speak into the air **in that session**.

```text
User types hablar/habla
  → print Grabando Ns… (no TTS)
  → JARVIS_RECORD_CMD → wav
  → JARVIS_STT_CMD → transcript
  → print User > [voz] transcript
  → same run_chat loop (TERMINAL + T45 speak)
```

**In V8:** timed PTT (~7 s), keyboard stays, `--chat --voice-speak` only.  
**Out of V8:** wake-word, always-on, barge-in, dual-Enter stop, PTT on `--voice`, `source=VOICE`.

---

## Connect-plugs rows this cola touches

| id | When it moves |
|---|---|
| `voice-intent-ingress` | **★ CLOSED** on T35 ★ @ `v0.6.43` |
| `a4-voice-world` | voice half ★ complete on T39 ★ @ `v0.7.0`; world half stays until T40 |
| `go-to-metadata-plug-for-world` | stays OPEN shaped through v1; world fill = T40+ |
| `world-package` | unchanged until T40 DC |

Spoken-continuity is **inside** the already-★ voice-half surface (egress classification). V8 PTT is **ingress** on the same `--chat` session (external record + existing STT). No new connect-plugs debt.

---

## Product brief (TTS character)

Desired egress voice (not a vendor lock): **British, grave, short, no theater** — free-first via **Piper `en_GB`** external. See [`engineer_note_voice_tts_product_brief.md`](engineer_note_voice_tts_product_brief.md). Marvel exact-clone **out**.

V7/T45 makes "short" true for Continuity walls — the screen still shows the full wall; the ear gets the brief extract by default, full only on a locked FULL phrase for that one turn.

V8 does not change TTS character. A PTT `estado` still speaks T45 brief; a PTT FULL phrase still speaks the wall that turn.

---

## Maintenance

When a voice Buy ★ closes, update this note’s Estado column. Do not mark rows CLOSED from prose alone.  
When a Buy adds/changes chat/Continuity/`render_*` egress, update [the spoken-continuity map](engineer_note_chat_spoken_continuity_map.md) in the **same** Buy.
