# Design Contract — Assistant chat voice / channels (`DC-assistant-chat-voice-channels`)

**Project:** Jarvis  
**Date:** 2026-10-03  
**Author:** JES / Cursor  
**Status:** ★ **CLOSED** (Engineer 2026-10-03 — cola voice phase C + docs sync; findings T34-inv accepted)  
**Type:** Block lock — Skill-first **phase C** voice path, phased ICs  
**Cola:** **T34-DC**  
**Parents:** [INV ★](investigation_review_assistant_voice_e2e_b0.md) · [INV report](investigation_report_assistant_voice_e2e_b0.md) · [Skill-first DC ★](design_contract_assistant_chat_skill_first_b0.md) phase C · [placement DC ★](design_contract_assistant_placement_b0.md) A4 · [connect-plugs map](engineer_note_connect_plugs_real_data_map.md) · tip **`v0.6.42`**

**Not** an Implementation Contract. **Not** permission to ship STT/TTS vendors. **Not** `world/` scaffold.

---

## Intent

Jarvis today has a complete **Skill-first chat brain** (twelve Skills) and a channel-agnostic entry `handle_user_text(str) -> dict` (CLI + MCP already share it). Voice is the next **ingress/egress**, not a second product. This DC locks the design so each voice IC stays small, reuses `run_skill` + existing fulfills, and does not invent a parallel brain.

---

## Block phases (cola)

| Phase | Cola | Buy (indicative) | Package (indicative) | Scope |
|---|---|---|---|---|
| **V0** | **T34-DC** ★ | this DC | — (no bump) | Design lock |
| **V1** | **T35** | `B1-assistant-voice-intent-ingress` | `0.6.43` | Fill `VoiceIntentAdapter`; thread `source` (12 parse sites); default `TERMINAL` |
| **V2** | **T36** | `B1-assistant-voice-fixture-loop` | `0.6.44` | `run_voice()`-style loop + text fixture STT; prove e2e turn |
| **V3** | **T37** | `B1-assistant-voice-stt-external` | `0.6.45` | Wire real external STT → same `parse(raw_text)` (vendor ★ later) |
| **V4** | **T38** | `B1-assistant-voice-tts-external` | `0.6.46` | Wire real external TTS on `render_response` output (vendor ★ later) |
| **V5** | **T39** | `B1-assistant-voice-v1-checkpoint` | `0.6.47` | Docs/ACCEPT checkpoint: speak → Skills → spoken reply |
| **V6** | **T40** | craft / `world/` (own DC later) | TBD | Explicitly **out** of voice v1 |

Each phase is independently ★-able. V3 and V4 may swap order after V2 ★.

---

## Locks (block-level)

| # | Lock |
|---|---|
| 1 | **Same brain** — voice uses `handle_user_text` → `_handle_global_commands` → `run_skill` → existing `_handle_*`. No parallel Skill runtime / Conversation Engine |
| 2 | **Ingress = text** — `VoiceIntentAdapter.parse(raw_text: str) -> Intent(source=VOICE)`. No audio bytes inside `capabilities/` / `intelligence/` |
| 3 | **Source threading** — optional `source` (or helper) through orch; **twelve** `TerminalIntentAdapter.parse` sites generalized; default `TERMINAL` keeps CLI/MCP byte-identical |
| 4 | **v1 surface = Skill-first twelve only** — explain, project_status, ARM/DISARM, HOLD…PATROL, CHARGE. Craft wizards / LLM fallthrough **out**. `jarvis board` never. Standalone `jarvis explain` not the voice path (use chat intercept) |
| 5 | **STT/TTS external** — fixture-first (V2), then real processes; no tip-pinned vendor SDK in core Buys |
| 6 | **Egress** — adapter after result dict; v1 may reuse `render_response`; no fork of fulfill logic |
| 7 | **Safety** — same `ArmedAllowlistSafetyGate`; no `"voice"` on `AuthoritySignal.source`; no kill-switch by voice |
| 8 | **GO_TO** — T32 metadata plug ready; v1 may bare `go to` (sin destino); spoken decimals / world names later (V6) |
| 9 | **`world/`** — not required for V1–V5; sibling later under placement A4 |
| 10 | **Out unless ★** — copper/ESC · inventing flight `available` · craft voice UX · house graph · Authority-from-voice |

---

## Opens

T34-inv ★ ACCEPT CLOSED (findings). This DC ★ CLOSED. Next: authorize **T35** IC when Engineer says proceed. Tip package stays **`0.6.42`** until T35 opens **`0.6.43`**.

SoT cola: [`docs/IMPLEMENTATION_TASKS.md`](../../docs/IMPLEMENTATION_TASKS.md) PRIORIDAD · [phase note](engineer_note_voice_phase_c_cola.md)
