# Implementation Contract — Assistant chat + spoken replies (`B1-assistant-chat-voice-speak`)

**Project:** Jarvis  
**Date:** 2026-10-04  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.7.3`**

**Status:** **IC ready for Claude** (Engineer paste = Buy).  
**Parents:** [T42](implementation_review_assistant_voice_interactive_cli_b1.md) @ `0.7.2` (PASS WITH NOTES) · [T41](implementation_review_assistant_voice_demo_ready_b1.md) · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md) · tip **`0.7.2`**  
**Type:** Wire **spoken replies into the real `--chat` CLI** (Continuity / craft / full session) — what the Engineer asked for after trying `--voice`.  
**Opens:** **`0.7.3` / `v0.7.3`**. **Cola:** **T43**

**Not:** replacing `--voice` · wake-word · mic loop · Piper in `pyproject` · Authority-from-voice · T40 world · tip pins · ACCEPT claim · silently making bare `--chat` speak.

---

## Why this Buy

Engineer ran `--voice` successfully, then: *“esto no es el cli de chat”* → *“eso es lo que quiero”*.

They want **`jarvis --chat` as today** (projects, Continuity, craft, `User >`), **plus** hearing each Jarvis reply via `JARVIS_TTS_CMD` / Piper. `--voice` stays the Skill-only channel; this Buy is **chat + speak opt-in**.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-chat-voice-speak`** — opt-in spoken egress on the **existing** `--chat` REPL |
| 2 | **CLI** — `--chat --voice-speak` (reuse the existing `--voice-speak` flag) enables speak on chat turns. Bare `--chat` remains **text-only** (no TTS call). Do not require a new flag name unless `--voice-speak` cannot be wired cleanly; prefer reuse |
| 3 | **Behavior** — every place `run_chat` today prints a Jarvis reply via `render_response` / startup context / define wizard / error messages that the user already sees as `Jarvis > …` should also be **spoken** when speak is on. Prefer speaking the **same string** that was printed (no second renderer). Skip empty strings |
| 4 | **No double print** — do **not** call `_voice_speak_fn` as-is if that would print twice. Use `speak_egress` (or a thin speak-only helper) after the existing `print`. Missing/failed TTS → print honest `TTS no disponible: …` once; **do not crash** the chat loop |
| 5 | **Chat brain unchanged** — still `handle_user_text` default `TERMINAL` (or whatever `--chat` uses today). Do **not** force `source=VOICE` for this path. Project picker, Continuity, craft/LLM fallthrough stay exactly as `--chat` |
| 6 | **`--voice` unchanged** — Skill-first interactive REPL from T42 stays; document both in the guide: `--chat --voice-speak` = full chat + ears; `--voice` = Skills-only voice channel |
| 7 | **Guide** — `USER_GUIDE_VOICE.md`: add a clear primary (or co-primary) section for **chat with voice**: `python -m jarvis.main --chat --voice-speak` after Piper env. Honesty: long Continuity / `estado` blocks will be read aloud in full |
| 8 | **Version** `pyproject` → **`0.7.3`**; PRIORIDAD · cola T43 · short PLATFORM/CONNECTIONS (**no new C-xxx**) |
| 9 | **Tests** — fake TTS + monkeypatched `input`: `--chat` path with speak on → ≥1 printed reply also reaches fake TTS stdin; bare chat / `run_chat(speak_tts=False)` never calls `speak_egress`; missing TTS honest + loop survives; tip-pin + ESC + no speech deps |
| 10 | Out: wake-word · changing default `--chat` to always speak · new STT seam · T40 · ACCEPT claim |

---

## 1. Files

| Path | Change |
|---|---|
| `src/jarvis/adapters/cli/main.py` | `run_chat(..., speak_tts=False)` + wire `main()` `--chat` + `--voice-speak`; speak-only after existing prints |
| `docs/USER_GUIDE_VOICE.md` | document `--chat --voice-speak` as the full-chat+voice path |
| `tests/test_assistant_chat_voice_speak_b1.py` | **new** T1–T5 |
| `pyproject.toml` | `0.7.2` → **`0.7.3`** — no speech deps |
| Docs / cola / state | T43 row |

Prefer **not** touching orchestrator / Skills / `adapters/voice/*` except reusing `speak_egress`.

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | Chat REPL with `speak_tts=True`, fake stdin (e.g. one Skill or status phrase + quit) → fake TTS receives the spoken egress text (≥1 capture) |
| T2 | `speak_tts=False` (default) → `speak_egress` never called (spy/mock) even if `JARVIS_TTS_CMD` set |
| T3 | Missing `JARVIS_TTS_CMD` with speak on → honest message; loop does not crash |
| T4 | `--voice` interactive path still importable/runnable (smoke or existing T42 tests still green) |
| T5 | `0.7.3` · no speech deps · tip-pin + ESC green · guide mentions `--chat --voice-speak` |

---

## 3. Acceptance

- [ ] Engineer runs `python -m jarvis.main --chat --voice-speak` with Piper env → full chat UX + spoken replies  
- [ ] Bare `--chat` still silent · `0.7.3` · guide updated  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.7.3`**

---

## 4. Paste for Claude

```text
Implementation — B1-assistant-chat-voice-speak (T43)
Parent tip: T42 @ 0.7.2 (interactive --voice). Package → 0.7.3.

IC: .jes/artifacts/implementation_contract_assistant_chat_voice_speak_b1.md
Guide: docs/USER_GUIDE_VOICE.md

Engineer wants FULL --chat CLI + spoken replies (not --voice Skills-only).
- Wire --chat --voice-speak → run_chat(speak_tts=True)
- Bare --chat stays text-only (byte-identical default)
- After each existing Jarvis print, speak the SAME string via speak_egress
  (do NOT double-print via _voice_speak_fn)
- Missing TTS → "TTS no disponible: …"; loop continues
- Keep source=TERMINAL / full Continuity+craft chat brain
- --voice (T42) unchanged; document both paths in guide
- pyproject 0.7.3; tests T1–T5; no speech deps; no tip pins
NO ACCEPT claim · NOT wake-word · NOT force speak on bare --chat
· NOT T40 · NOT new STT seam
```
