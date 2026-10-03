# Implementation Contract — Assistant voice v1 checkpoint (`B1-assistant-voice-v1-checkpoint`)

**Project:** Jarvis  
**Date:** 2026-10-03  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.7.0`**

**Status:** **Implemented** (Claude Code) — Cursor **PASS WITH NOTES** → await Engineer ★ ACCEPT → tag `v0.7.0`.  
**Parents:** [DC voice/channels ★ CLOSED](design_contract_assistant_chat_voice_channels_b0.md) · [T38 ★](implementation_review_assistant_voice_tts_external_b1.md) · [T37 ★](implementation_review_assistant_voice_stt_external_b1.md) · [T36 ★](implementation_review_assistant_voice_fixture_loop_b1.md) · [T35 ★](implementation_review_assistant_voice_intent_ingress_b1.md) · [TTS product brief](engineer_note_voice_tts_product_brief.md) · [cola note](engineer_note_voice_phase_c_cola.md) · tip **`v0.6.46`**  
**Type:** Phase **V5** — **product milestone** “Jarvis voz v1” (integration checkpoint).  
**Opens:** **`0.7.0` / `v0.7.0`**. **Cola:** **T39**

**Not:** new STT/TTS seam · speech SDK in `pyproject` · craft/`world/` · Authority-from-voice · mic/speaker drivers in core · Marvel voice clone · tip pins · ACCEPT claim.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-voice-v1-checkpoint`** — Skill-first phase C **V5** product milestone |
| 2 | **No new voice seam** — reuse T35–T38 surface as-is (`VoiceIntentAdapter`, `run_voice` / `run_voice_turn` / `run_voice_turn_from_audio`, `speak=` / `speak_egress` / `make_speak_callable`, `JARVIS_STT_CMD` / `JARVIS_TTS_CMD`). Prefer **zero** `src/` behavior change; test-only + docs + version bump |
| 3 | **Product picture proof** — fixture (and/or fake STT) → `source=VOICE` → Skill-first brain → `render_response` → fake TTS records egress. Prove without mic / speaker / Piper |
| 4 | **Twelve Skills on voice path** — each of the twelve Skill-first Skills gets at least one fixture phrase → non-empty egress (honest allow/reject OK). Suggested phrases (reuse chat Skill-first vocabulary): `explain c-rate-de-bateria`, `estado`, `armar`, `desarmar`, `hold`, `land`, `go to`, `takeoff`, `return home` (or `rtl`), `follow`, `patrol`, `charge`. Craft/LLM fallthrough must **not** be required (`ExplodingLLM` pattern) |
| 5 | **Combined STT→Skill→TTS** — at least one turn: fake STT audio → Skill result → fake TTS stdin records that egress (closes “both seams ★” narrative for voice half of `a4-voice-world`) |
| 6 | **Version** `pyproject.toml` → **`0.7.0`**; Engineer ACCEPT → tag **`v0.7.0`**. Not `0.6.47` |
| 7 | **Docs wire** — PRIORIDAD T39 → Implemented await review; cola Estado; PLATFORM short note; CONNECTIONS (**no new C-xxx**); ARCHITECTURE tip line; TTS brief tip parent; `a4-voice-world` → voice v1 complete / world half still T40 |
| 8 | **Safety / honesty unchanged** — no Authority `"voice"`; no tip pins; ESC fence green; no speech deps in `pyproject` |
| 9 | **Vendor / Piper out** — still external demo per [TTS brief](engineer_note_voice_tts_product_brief.md); Marvel clone out; STT/TTS vendor ★ still separate |
| 10 | Out: craft/`world`/board · copper · Authority/kill · live mic/speaker drivers · tip-pinned speech SDKs · ACCEPT claim · T40 scope · new C-xxx · Conversation Engine |

---

## 1. Files

| Path | Change |
|---|---|
| `tests/test_assistant_voice_v1_checkpoint_b1.py` | **new** T1–T5 integration proofs |
| `pyproject.toml` | `0.6.46` → **`0.7.0`** — **no** new speech dependencies |
| `docs/IMPLEMENTATION_TASKS.md` | PRIORIDAD + T39 row |
| `docs/PLATFORM_CAPABILITY_VISION.md` | short T39 / voz v1 note |
| `docs/system_map/CONNECTIONS.md` | Extended-by sentence; **no new C-xxx** |
| `docs/ARCHITECTURE.md` | tip / `0.7.0` one-liner |
| `.jes/artifacts/engineer_note_voice_phase_c_cola.md` | T39 Estado; tip parent |
| `.jes/artifacts/engineer_note_connect_plugs_real_data_map.md` | `a4-voice-world` voice half complete; world = T40 |
| `.jes/artifacts/engineer_note_voice_tts_product_brief.md` | tip parent bump only |
| `.jes/state/engineering_state.json` | cycle → T39 implemented await review |
| `src/jarvis/adapters/voice/**` | **prefer untouched** |
| `src/jarvis/core/orchestrator.py` | **prefer untouched** |

Prefer **not** touching fulfill / `render_response` body / Skill classify.

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | Fixture (multiline or parametrized) covering **all twelve** Skill phrases via `run_voice` → each turn non-empty `render_response` egress; `ExplodingLLM` proves no craft/LLM fallthrough |
| T2 | Same twelve-phrase fixture with `speak=` fake TTS → fake records **every** egress (≥ twelve non-empty stdin captures) |
| T3 | Fake STT audio → `run_voice_turn_from_audio` → Skill result + egress → `speak_egress` / `make_speak_callable` records that egress (**STT→Skill→TTS**) |
| T4 | Radio/Api still `NotImplementedError`; no Authority `"voice"` literal introduced |
| T5 | `pyproject` **`0.7.0`**; no speech deps; no tip pins; ESC fence green; `--chat` / `--voice-fixture` still work without TTS/STT env |

---

## 3. Acceptance

- [ ] Product picture proven: fixture → twelve Skills → fake TTS · STT→Skill→TTS · `0.7.0` · no vendor SDK in deps · no new seam  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.7.0`**

---

## 4. Paste for Claude

```text
Implementation — B1-assistant-voice-v1-checkpoint (T39)
Parent tip: T38 ★ ACCEPT CLOSED @ v0.6.46. Package → 0.7.0 / tag v0.7.0.

IC: .jes/artifacts/implementation_contract_assistant_voice_v1_checkpoint_b1.md
DC: .jes/artifacts/design_contract_assistant_chat_voice_channels_b0.md (★ CLOSED)
Cola: .jes/artifacts/engineer_note_voice_phase_c_cola.md
Brief: .jes/artifacts/engineer_note_voice_tts_product_brief.md

Phase V5 product milestone — docs + integration proof. NO new seam code.
- Reuse T35–T38 adapters/voice surface as-is
- Prove fixture → twelve Skills → fake TTS (and STT→Skill→TTS)
  Suggested phrases: explain c-rate-de-bateria, estado, armar, desarmar,
  hold, land, go to, takeoff, return home (or rtl), follow, patrol, charge
- pyproject 0.7.0; PRIORIDAD/PLATFORM/CONNECTIONS/ARCHITECTURE; cola;
  a4-voice-world voice half complete (world stays T40); brief tip parent
NO ACCEPT claim · NO tip pins · NO speech deps · NOT world/craft
· NOT vendor ★ · NOT mic/speaker drivers · NOT Marvel clone · NOT 0.6.47
```
