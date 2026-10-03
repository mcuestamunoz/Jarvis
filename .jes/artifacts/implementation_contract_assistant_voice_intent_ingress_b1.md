# Implementation Contract — Assistant voice Intent ingress (`B1-assistant-voice-intent-ingress`)

**Project:** Jarvis  
**Date:** 2026-10-03  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.43`**

**Status:** ★ **AUTHORIZED** — await Claude implementation (no ACCEPT claim).  
**Parents:** [DC voice/channels ★ CLOSED](design_contract_assistant_chat_voice_channels_b0.md) · [T34-inv ★](investigation_review_assistant_voice_e2e_b0.md) · [cola note](engineer_note_voice_phase_c_cola.md) · tip **`v0.6.42`**  
**Type:** Phase **V1** — fill `VoiceIntentAdapter` + thread honest `IntentSource` through orch classify sites.  
**Opens:** **`0.6.43` / `v0.6.43`**. **Cola:** **T35**

**Not:** STT/TTS · `run_voice` loop · craft wizards · `world/` · Authority-from-voice · copper · opening `0.7.0` (that is T39).

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-voice-intent-ingress`** — Skill-first phase C **V1** |
| 2 | **`VoiceIntentAdapter.parse(raw_text: str) -> Intent`**: mirror `TerminalIntentAdapter` shape; return `Intent(source=IntentSource.VOICE, raw_text=raw_text)` (metadata default `{}`). **Stop** raising `NotImplementedError` for this adapter. Keep Radio/Api still NotImplemented |
| 3 | **Source threading:** `handle_user_text` (and inner path into `_handle_global_commands`) must accept an optional channel source (name/shape up to implementer: e.g. `source: IntentSource \| None = None` or keyword-only). **Default `TERMINAL`** — CLI + MCP callers stay byte-identical without passing the arg |
| 4 | **Twelve classify sites** in `_handle_global_commands` that today call `TerminalIntentAdapter.parse(stripped)` must produce Intent with the **call’s** source (not hardcoded TERMINAL). Prefer one small helper (e.g. `_parse_intent(stripped, source)`) used by all twelve — do not leave a thirteenth hardcode |
| 5 | **Reuse brain:** no new Skill runtime, no parallel orchestrator, no Conversation Engine. Classify `try_*` + `run_skill` + `_handle_*` unchanged in behavior for `TERMINAL` |
| 6 | **Prove voice path in tests** without STT: construct via `VoiceIntentAdapter.parse` and/or `handle_user_text(..., source=VOICE)` (exact API per lock 3) so at least one Skill-first phrase (e.g. `hold` or `estado`) runs with `intent.source == VOICE` observable (unit on helper and/or orch path). CLI default path still `TERMINAL` |
| 7 | **Safety/honesty:** no Authority surface; no `"voice"` on `AuthoritySignal.source`; ArmedAllowlist path unchanged |
| 8 | Version **`0.6.43`**; PLATFORM · CONNECTIONS (**no new C-xxx**); PRIORIDAD T35 → Implemented await review; connect-plugs `voice-intent-ingress` pointer updated (row **not** CLOSED until Engineer ★ ACCEPT) |
| 9 | Out: STT/TTS · fixture voice loop (T36) · craft · world · tip pins · ACCEPT claim · `v0.7.0` |

---

## 1. Files

| Path | Change |
|---|---|
| `capabilities/intent.py` | Implement `VoiceIntentAdapter.parse` |
| `core/orchestrator.py` | Optional `source` on `handle_user_text` / global-commands path; helper + twelve sites |
| `tests/test_assistant_voice_intent_ingress_b1.py` | **new** T1–T5 |
| Existing intent/safety tests | Adjust only if they asserted Voice always NotImplemented — retarget to new honesty |
| `pyproject.toml` | `0.6.43` |
| Docs / cola note / connect-plugs row | short wire; no T39/`0.7.0` |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | `VoiceIntentAdapter.parse("hold")` → `Intent` with `source=VOICE` and `raw_text` preserved (no NotImplementedError) |
| T2 | `handle_user_text` **without** source override (CLI-shaped) still behaves as today for a Skill phrase (e.g. armed `hold` or `estado`) — regression |
| T3 | `handle_user_text(..., source=VOICE)` (or locked API) on a Skill-first phrase → fulfill succeeds / same honesty as terminal; Intent reaching classify has `source=VOICE` (spy helper or equivalent) |
| T4 | Radio/Api adapters still raise NotImplementedError; MCP/CLI call sites need no mandatory new args |
| T5 | No tip pins · ESC fence green · no Authority `"voice"` member added |

---

## 3. Acceptance

- [ ] VoiceIntentAdapter produces VOICE Intent · twelve sites honor source · default TERMINAL · `0.6.43`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.43`** · connect-plugs `voice-intent-ingress` advances on ★  

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-voice-intent-ingress (T35)
Parent tip: voice phase C docs @ v0.6.42 (T34-DC ★ CLOSED). Package → 0.6.43.

IC: .jes/artifacts/implementation_contract_assistant_voice_intent_ingress_b1.md
DC: .jes/artifacts/design_contract_assistant_chat_voice_channels_b0.md (★ CLOSED)
Cola: .jes/artifacts/engineer_note_voice_phase_c_cola.md

Phase V1 only — Intent ingress + source threading. No STT/TTS/loop.
- VoiceIntentAdapter.parse(raw_text: str) -> Intent(source=VOICE, raw_text=…)
  (mirror TerminalIntentAdapter; stop NotImplementedError for Voice only)
- Thread optional source into handle_user_text → _handle_global_commands
  Default TERMINAL — CLI/MCP byte-identical without new args
- Replace all twelve TerminalIntentAdapter.parse(stripped) sites with a
  helper that uses the call's source (no leftover hardcode TERMINAL)
- Tests: T1 Voice parse; T2 default TERMINAL regression; T3 VOICE path
  on a Skill phrase; T4 Radio/Api still NI; T5 tip-pin+ESC
- pyproject 0.6.43; short PRIORIDAD/PLATFORM/CONNECTIONS; connect-plugs
  voice-intent-ingress pointer (do NOT mark row CLOSED — only on ★ ACCEPT)
NO ACCEPT claim · NO tip pins · NOT T36 loop · NOT STT/TTS · NOT world
· NOT v0.7.0 (T39 milestone later)
```
