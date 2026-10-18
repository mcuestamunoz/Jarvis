# Implementation Contract — Assistant voice fixture loop (`B1-assistant-voice-fixture-loop`)

**Project:** Jarvis  
**Date:** 2026-10-03  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.44`**

**Status:** **★ ACCEPT CLOSED** (Engineer 2026-10-03) — Cursor **PASS WITH NOTES** · tip **`v0.6.44`**.  
**Parents:** [DC voice/channels ★ CLOSED](design_contract_assistant_chat_voice_channels_b0.md) · [T35 ★](implementation_review_assistant_voice_intent_ingress_b1.md) · [cola note](engineer_note_voice_phase_c_cola.md) · tip **`v0.6.43`**  
**Type:** Phase **V2** — fixture-driven voice turn loop over today’s Skill-first brain.  
**Opens:** **`0.6.44` / `v0.6.44`**. **Cola:** **T36**

**Not:** real STT/TTS · mic/speaker I/O · vendor SDK · craft wizards · `world/` · Authority-from-voice · opening `0.7.0` (T39).

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-voice-fixture-loop`** — Skill-first phase C **V2** |
| 2 | **New thin voice adapter** under `src/jarvis/adapters/voice/` (new package). Do **not** invent a second orchestrator / Skill runtime / Conversation Engine |
| 3 | **Fixture STT stand-in** — a small typed helper that yields plain `str` lines as “what STT produced” (list/iterable/file lines — shape up to implementer). **No audio bytes**, no mic, no vendor |
| 4 | **`run_voice_turn` (or equivalent)** — one coherent turn: fixture text → `orchestrator.handle_user_text(text, llm, source=IntentSource.VOICE)` → reuse existing `render_response(result) -> str` as egress text (what later TTS would speak). Return both result dict and rendered egress string (exact API up to implementer; must be testable) |
| 5 | **`run_voice` loop** — consume fixture lines until exhausted / sentinel; call the turn helper each line. Parallel in spirit to `run_chat`, but **fixture-driven**, not `input()`. Optional thin CLI flag (e.g. `--voice-fixture PATH`) that feeds file lines into this loop is OK; must not break `--chat` |
| 6 | **Reuse brain** — same `handle_user_text` / `run_skill` / `_handle_*`. Egress = adapter after result; **no fork** of fulfill logic; no voice-tuned renderer rewrite |
| 7 | **Prove e2e in tests without mic** — at least one Skill-first phrase (e.g. `hold` or `estado`) through the fixture loop with `source=VOICE` observable and non-empty rendered egress. Multi-line fixture (e.g. `armar` then `hold`) OK. CLI `--chat` / MCP remain byte-identical |
| 8 | **Safety/honesty** — no Authority `"voice"`; ArmedAllowlist unchanged; Radio/Api adapters still NI |
| 9 | Version **`0.6.44`**; PLATFORM · CONNECTIONS (**no new C-xxx**); PRIORIDAD T36 → Implemented await review; cola note + connect-plugs `a4-voice-world` pointer advance (do **not** invent new CLOSED rows) |
| 10 | Out: real STT (T37) · real TTS (T38) · craft/`world` · tip pins · ACCEPT claim · `v0.7.0` |

---

## 1. Files

| Path | Change |
|---|---|
| `src/jarvis/adapters/voice/` | **new** — fixture STT helper + `run_voice_turn` / `run_voice` (names flexible; keep thin) |
| `src/jarvis/adapters/cli/main.py` | optional `--voice-fixture` (or equivalent) wiring only; `--chat` untouched in behavior |
| `tests/test_assistant_voice_fixture_loop_b1.py` | **new** T1–T5 |
| `pyproject.toml` | `0.6.44` |
| Docs / cola note / connect-plugs `a4-voice-world` | short wire |

**Do not** change Skill classify/fulfill semantics. Touch `orchestrator.py` only if a tiny public import/export is truly required (prefer not).

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | Fixture STT helper yields the provided text line(s) unchanged (no audio path) |
| T2 | One Skill-first turn via voice loop/`run_voice_turn` with `source=VOICE` → honest Skill result (e.g. disarmed `hold` reject or `estado` ok) + non-empty `render_response` egress |
| T3 | Multi-line fixture (e.g. `armar` then `hold`) — second turn sees armed latch; VOICE source still used |
| T4 | `run_chat` / MCP path unchanged (no mandatory new args); Radio/Api still NI |
| T5 | No tip pins · ESC fence green · no Authority `"voice"` member |

---

## 3. Acceptance

- [x] Fixture-driven voice turn proves ingress→Skill→`render_response` with VOICE · `0.6.44`  
- [x] Cursor review (**PASS WITH NOTES**) · Engineer ACCEPT · tag **`v0.6.44`**

---

## 4. Paste for Claude

```text
Implementation — B1-assistant-voice-fixture-loop (T36)
Parent tip: T35 ★ ACCEPT CLOSED @ v0.6.43. Package → 0.6.44.

IC: .jes/artifacts/implementation_contract_assistant_voice_fixture_loop_b1.md
DC: .jes/artifacts/design_contract_assistant_chat_voice_channels_b0.md (★ CLOSED)
Cola: .jes/artifacts/engineer_note_voice_phase_c_cola.md

Phase V2 only — fixture-driven voice loop. No real STT/TTS/mic.
- New thin package src/jarvis/adapters/voice/
- Fixture STT stand-in: yields plain str lines (“what STT produced”)
- run_voice_turn: text → handle_user_text(..., source=VOICE)
  → reuse render_response(result) as egress string (no fulfill fork)
- run_voice: loop over fixture lines (not input()). Optional
  --voice-fixture PATH OK; --chat behavior unchanged
- Tests: T1 fixture yields text; T2 one Skill turn + egress;
  T3 multi-line armar→hold; T4 chat/MCP + Radio/Api NI; T5 tip-pin+ESC
- pyproject 0.6.44; short PRIORIDAD/PLATFORM/CONNECTIONS; cola +
  a4-voice-world pointer (no invented CLOSED rows)
NO ACCEPT claim · NO tip pins · NOT real STT/TTS · NOT world
· NOT v0.7.0 (T39 later)
```
