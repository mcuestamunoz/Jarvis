# Implementation Contract — Assistant voice STT external (`B1-assistant-voice-stt-external`)

**Project:** Jarvis  
**Date:** 2026-10-03  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.45`**

**Status:** **★ ACCEPT CLOSED** (Engineer 2026-10-03) — Cursor **PASS WITH NOTES** · tip **`v0.6.45`**.  
**Parents:** [DC voice/channels ★ CLOSED](design_contract_assistant_chat_voice_channels_b0.md) · [T36 ★](implementation_review_assistant_voice_fixture_loop_b1.md) · [cola note](engineer_note_voice_phase_c_cola.md) · tip **`v0.6.44`**  
**Type:** Phase **V3** — external STT process seam → same text ingress as T35/T36.  
**Opens:** **`0.6.45` / `v0.6.45`**. **Cola:** **T37**

**Not:** vendor SDK pick (whisper/vosk/… = **separate Engineer ★**) · tip-pinned speech deps · live mic stream · real TTS (T38) · craft/`world/` · Authority-from-voice · `v0.7.0` (T39).

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-voice-stt-external`** — Skill-first phase C **V3** |
| 2 | **External STT seam** in `src/jarvis/adapters/voice/` — invoke an **external command/process** that turns an audio **file path** into transcript `str`. No speech package added to `pyproject.toml`. No audio decode inside `capabilities/` / `intelligence/` / `core/` |
| 3 | **Config via env (or equivalent thin config)** — e.g. `JARVIS_STT_CMD` template with an `{audio}` placeholder (exact name/shape up to implementer). Missing/empty config → honest typed failure (not silent fixture fallback) |
| 4 | **Stdout = transcript** — success: strip stdout → non-empty `str` fed to existing `run_voice_turn` / `handle_user_text(..., source=VOICE)`. Non-zero exit / empty transcript → typed error, no invented Skill phrase |
| 5 | **Reuse T36 loop shape** — keep `FixtureSttSource` + `--voice-fixture` working. New path: audio file → external STT → same `run_voice_turn`. Optional CLI flag (e.g. `--voice-audio PATH`) OK; must not break `--chat` / `--voice-fixture` |
| 6 | **Prove without real vendor** — tests ship a tiny **fake STT script** (repo test helper or tmp script) that prints a Skill phrase (e.g. `hold`) given any audio path; wire env to that script; assert VOICE turn + non-empty egress. No mic required. A tiny placeholder audio file (empty/minimal bytes) is fine |
| 7 | **Vendor choice out** — do **not** tip-pin or hardcode whisper/vosk/cloud SDK. Document that picking a real STT binary is a **separate Engineer ★**. This Buy only lands the process seam |
| 8 | **Safety/honesty** — no Authority `"voice"`; Radio/Api still NI; no STT in `capabilities/` |
| 9 | Version **`0.6.45`**; PLATFORM · CONNECTIONS (**no new C-xxx**); PRIORIDAD T37 → Implemented await review; cola + `a4-voice-world` pointer advance (no invented CLOSED rows) |
| 10 | Out: real TTS (T38) · live mic capture loop · craft/`world` · tip pins · ACCEPT claim · `v0.7.0` · vendor SDK ★ |

---

## 1. Files

| Path | Change |
|---|---|
| `src/jarvis/adapters/voice/` | external STT helper + wire into turn (names flexible; keep thin) |
| `src/jarvis/adapters/cli/main.py` | optional `--voice-audio` (or equiv.); `--chat` / `--voice-fixture` behavior unchanged |
| `tests/test_assistant_voice_stt_external_b1.py` | **new** T1–T5 (+ fake STT script fixture as needed) |
| `pyproject.toml` | `0.6.45` — **no** new speech dependencies |
| Docs / cola note / connect-plugs `a4-voice-world` | short wire |

Prefer **not** touching `orchestrator.py` / Skill classify/fulfill.

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | External STT helper with fake cmd + audio path → returns expected transcript `str` (stdout) |
| T2 | Missing/empty STT config → typed failure (no silent success) |
| T3 | Non-zero exit **or** empty stdout → typed failure (no invented Skill text) |
| T4 | Fake STT → `run_voice_turn` / wired path on a Skill phrase → `source=VOICE` + honest Skill result + non-empty egress |
| T5 | No tip pins · ESC fence green · no speech deps added to `pyproject.toml` · no Authority `"voice"` · `--chat` still works without STT env |

---

## 3. Acceptance

- [x] External STT process seam feeds same VOICE ingress · `0.6.45` · no vendor SDK in deps  
- [x] Cursor review (**PASS WITH NOTES**) · Engineer ACCEPT · tag **`v0.6.45`**

---

## 4. Paste for Claude

```text
Implementation — B1-assistant-voice-stt-external (T37)
Parent tip: T36 ★ ACCEPT CLOSED @ v0.6.44. Package → 0.6.45.

IC: .jes/artifacts/implementation_contract_assistant_voice_stt_external_b1.md
DC: .jes/artifacts/design_contract_assistant_chat_voice_channels_b0.md (★ CLOSED)
Cola: .jes/artifacts/engineer_note_voice_phase_c_cola.md

Phase V3 only — external STT process seam. No vendor SDK. No TTS.
- In adapters/voice/: invoke external cmd (env e.g. JARVIS_STT_CMD with
  {audio} placeholder) on an audio file path → stdout transcript str
- Feed transcript into existing run_voice_turn (source=VOICE)
- Keep FixtureSttSource / --voice-fixture working
- Optional --voice-audio PATH OK; --chat unchanged
- Missing config / non-zero exit / empty stdout → typed failure
- Tests use a fake STT script (prints e.g. "hold"); no mic; no speech
  deps in pyproject
- Vendor pick (whisper/…) = separate Engineer ★ — do not hardcode
- pyproject 0.6.45; short PRIORIDAD/PLATFORM/CONNECTIONS; cola +
  a4-voice-world pointer (no invented CLOSED rows)
NO ACCEPT claim · NO tip pins · NOT TTS · NOT live mic stream
· NOT world · NOT v0.7.0 (T39 later)
```
