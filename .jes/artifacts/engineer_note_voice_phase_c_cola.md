# Engineer note — Voice phase C cola (Skill-first channels)

**Date:** 2026-10-03  
**Status:** **OPEN living cola index** — seeded after T34-inv ★ + T34-DC ★  
**Authority:** Engineer — update documentary system + queue ICs before first voice code Buy  
**Tip parent:** **`v0.6.44`** (T36 ★)

**Purpose:** One place to see the **ordered voice Buys** that take Jarvis from “chat-only Skill-first” to “voice end-to-end on today’s brain.” Not a vendor roadmap. Engineer paste of an IC to Claude = Buy (no separate AUTHORIZED stamp required).

**Versioning:** T35–T38 = `0.6.43`…`0.6.46` (construcción). **T39 ★** = product milestone **`0.7.0` / `v0.7.0`** (Engineer 2026-10-03).

**Parents:** [T34-DC ★](design_contract_assistant_chat_voice_channels_b0.md) · [T34-inv review ★](investigation_review_assistant_voice_e2e_b0.md) · [Skill-first DC ★](design_contract_assistant_chat_skill_first_b0.md) · [connect-plugs map](engineer_note_connect_plugs_real_data_map.md)

---

## Product picture (v1)

```text
[fixture / mic] → STT → text → VoiceIntentAdapter(VOICE)
  → handle_user_text → run_skill → _handle_* (same as chat)
  → render_response → TTS → [speaker]
```

**In v1:** twelve Skill-first Skills.  
**Out of v1:** craft wizards/LLM, `world/`, board, Authority/kill, copper.

---

## Cola (ordered)

| # | Phase | Buy id | Package | Estado | Qué | Gate |
|---|---|---|---|---|---|---|
| **T34-inv** | — | `INV-assistant-voice-e2e` | — | ✅ ★ CLOSED | Forensic map + phase plan | [review ★](investigation_review_assistant_voice_e2e_b0.md) |
| **T34-DC** | V0 | `DC-assistant-chat-voice-channels` | — | ✅ ★ CLOSED | Block locks | [DC ★](design_contract_assistant_chat_voice_channels_b0.md) |
| **T35** | V1 | `B1-assistant-voice-intent-ingress` | `0.6.43` | ✅ ★ **ACCEPT CLOSED** @ **`v0.6.43`** | `VoiceIntentAdapter` + `source` threading (12 sites) | [review ★](implementation_review_assistant_voice_intent_ingress_b1.md) |
| **T36** | V2 | `B1-assistant-voice-fixture-loop` | `0.6.44` | ✅ ★ **ACCEPT CLOSED** @ **`v0.6.44`** | New `adapters/voice/` package; fixture-driven `run_voice` loop | [review ★](implementation_review_assistant_voice_fixture_loop_b1.md) |
| **T37** | V3 | `B1-assistant-voice-stt-external` | `0.6.45` | IC ready · Claude | External STT process seam → same parse | [IC](implementation_contract_assistant_voice_stt_external_b1.md) · vendor ★ separate |
| **T38** | V4 | `B1-assistant-voice-tts-external` | `0.6.46` | Parked — after T36 ★ | External TTS on render output | may run before/after T37 · vendor ★ separate |
| **T39** | V5 | `B1-assistant-voice-v1-checkpoint` | **`0.7.0` / `v0.7.0`** | Parked — after T37+T38 ★ | **Product milestone** — voice v1 complete | opens minor `0.7` |
| **T40** | V6 | craft / `world/` voice | TBD | **Parked** — own DC | Not voice v1 | [placement A4](design_contract_assistant_placement_b0.md) |

---

## Connect-plugs rows this cola touches

| id | When it moves |
|---|---|
| `voice-intent-ingress` | **★ CLOSED** on T35 ★ @ `v0.6.43` |
| `a4-voice-world` | advances across T35–T39; world half stays until T40 |
| `go-to-metadata-plug-for-world` | stays OPEN shaped through v1; world fill = T40+ |
| `world-package` | unchanged until T40 DC |

---

## Product brief (TTS character)

Desired egress voice (not a vendor lock): **British, grave, short, no theater** — free-first via **Piper `en_GB`** external. See [`engineer_note_voice_tts_product_brief.md`](engineer_note_voice_tts_product_brief.md). Marvel exact-clone **out**.

---

## Maintenance

When a voice Buy ★ closes, that Buy’s docs pass updates this note’s Estado column and the connect-plugs map row. Do not mark rows CLOSED from prose alone.
