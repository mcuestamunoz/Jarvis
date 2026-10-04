# Implementation Contract — Assistant voice TTS external (`B1-assistant-voice-tts-external`)

**Project:** Jarvis  
**Date:** 2026-10-03  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.46`**

**Status:** **★ ACCEPT CLOSED** (Engineer 2026-10-03) — Cursor **PASS WITH NOTES** · tip **`v0.6.46`**.  
**Parents:** [DC voice/channels ★ CLOSED](design_contract_assistant_chat_voice_channels_b0.md) · [T37 ★](implementation_review_assistant_voice_stt_external_b1.md) · [T36 ★](implementation_review_assistant_voice_fixture_loop_b1.md) · [TTS product brief](engineer_note_voice_tts_product_brief.md) · [cola note](engineer_note_voice_phase_c_cola.md) · tip **`v0.6.45`**  
**Type:** Phase **V4** — external TTS process seam on `render_response` egress.  
**Opens:** **`0.6.46` / `v0.6.46`**. **Cola:** **T38**

**Not:** Piper/cloud SDK in `pyproject` · tip-pinned speech deps · live speaker driver in core · craft/`world/` · Authority-from-voice · opening `0.7.0` (T39) · Marvel voice clone.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-voice-tts-external`** — Skill-first phase C **V4** |
| 2 | **External TTS seam** in `src/jarvis/adapters/voice/` — invoke an **external command/process** that speaks (or writes audio for) a plain `str` egress. No speech package added to `pyproject.toml`. No TTS inside `capabilities/` / `intelligence/` / `core/` |
| 3 | **Config via env** — e.g. `JARVIS_TTS_CMD` (exact name up to implementer). **Prefer stdin for the text** (Skill messages have spaces/quotes — do not smash free text into `shlex` argv). Missing/empty config → typed failure (not silent no-op success) |
| 4 | **Input = `render_response` egress string** — success: exit `0`. Non-zero exit / missing binary → typed error family parallel to T37 (`TtsConfigError` / `TtsProcessError` or equivalent). Do **not** fork fulfill logic or rewrite `render_response` |
| 5 | **Wire into T36 `speak` seam** — provide a callable usable as `run_voice(..., speak=...)` (and/or a thin `speak_egress(text)` helper). Keep `--voice-fixture` / `--voice-audio` / `--chat` working. Optional CLI flag that runs a fixture (or one turn) **with** external TTS speak is OK |
| 6 | **Prove without real Piper/vendor** — tests ship a tiny **fake TTS script** that reads stdin and records/writes the received text (e.g. to a side file); assert Skill egress reaches the fake. No speaker required |
| 7 | **Product brief (rescued)** — document pointer to [TTS product brief](engineer_note_voice_tts_product_brief.md): British / grave / short / no theater; **free-first demo = external Piper `en_GB`**, not hardcoded in this Buy. Installing Piper remains **outside** the package |
| 8 | **Vendor choice out of core** — do not tip-pin Piper/ElevenLabs/etc. in deps. Pointing `JARVIS_TTS_CMD` at a real binary = operator/demo setup (or later Engineer ★), not this IC’s code lock |
| 9 | Version **`0.6.46`**; PLATFORM · CONNECTIONS (**no new C-xxx**); PRIORIDAD T38 → Implemented await review; cola + `a4-voice-world` pointer; keep TTS brief in tip |
| 10 | Out: live mic · STT vendor ★ · craft/`world` · tip pins · ACCEPT claim · `v0.7.0` · Marvel clone |

---

## 1. Files

| Path | Change |
|---|---|
| `src/jarvis/adapters/voice/` | external TTS helper + `speak` wiring (names flexible; keep thin; mirror T37 honesty) |
| `src/jarvis/adapters/cli/main.py` | optional flag to exercise TTS on a fixture/turn; existing flags unchanged in behavior |
| `tests/test_assistant_voice_tts_external_b1.py` | **new** T1–T5 |
| `pyproject.toml` | `0.6.46` — **no** new speech dependencies |
| Docs / cola / `a4-voice-world` / TTS brief | short wire; brief file present on tip |

Prefer **not** touching `orchestrator.py` / Skill classify/fulfill / `render_response` body.

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | External TTS helper with fake cmd + egress text on stdin → fake records/receives that text; exit 0 |
| T2 | Missing/empty TTS config → typed failure |
| T3 | Non-zero exit **or** missing binary → typed failure |
| T4 | Skill turn via `run_voice`/`run_voice_turn` with `speak=` wired to external TTS → fake receives non-empty `render_response` egress |
| T5 | No tip pins · ESC fence green · no speech deps in `pyproject.toml` · no Authority `"voice"` · `--chat` / `--voice-fixture` still work without TTS env |

---

## 3. Acceptance

- [x] External TTS process seam speaks/records `render_response` egress · `0.6.46` · no vendor SDK in deps  
- [x] Cursor review (**PASS WITH NOTES**) · Engineer ACCEPT · tag **`v0.6.46`**

---

## 4. Paste for Claude

```text
Implementation — B1-assistant-voice-tts-external (T38)
Parent tip: T37 ★ ACCEPT CLOSED @ v0.6.45. Package → 0.6.46.

IC: .jes/artifacts/implementation_contract_assistant_voice_tts_external_b1.md
DC: .jes/artifacts/design_contract_assistant_chat_voice_channels_b0.md (★ CLOSED)
Cola: .jes/artifacts/engineer_note_voice_phase_c_cola.md
Brief: .jes/artifacts/engineer_note_voice_tts_product_brief.md (rescue — Piper free-first)

Phase V4 only — external TTS process seam. No vendor SDK in pyproject.
- In adapters/voice/: invoke external cmd (env e.g. JARVIS_TTS_CMD)
  Prefer stdin for egress text (spaces/quotes safe)
- speak_egress / speak callable for run_voice(..., speak=...)
  Input = render_response string; success = exit 0
- Typed failures parallel to T37 (config / process / missing binary)
- Keep --chat / --voice-fixture / --voice-audio working
- Optional CLI to run fixture+TTS OK
- Tests: fake TTS script reads stdin, records text; no speaker;
  no speech deps in pyproject
- Do NOT hardcode Piper — brief says free-first demo is external
  Piper en_GB; install stays outside the package
- pyproject 0.6.46; short PRIORIDAD/PLATFORM/CONNECTIONS; cola +
  a4-voice-world; keep TTS brief on tip
NO ACCEPT claim · NO tip pins · NOT STT vendor · NOT world
· NOT v0.7.0 (T39 later) · NOT Marvel clone
```
