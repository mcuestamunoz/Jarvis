# Implementation Contract — In-session cancel key (`B1-assistant-voice-session-key`)

**Project:** Jarvis  
**Date:** 2026-10-14  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.8.5`**

**Status:** **IC ready** — Engineer “procede con redactar ic” after T57 ★ @ `v0.8.4`. Paste to Claude.  
**Parents:** [V12-DC](design_contract_assistant_voice_cancel_mid_tts_b0.md) · [T56 ★](implementation_review_assistant_voice_cancel_mid_tts_b1.md) · [T57 ★](implementation_review_assistant_voice_anti_echo_settle_b1.md) · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md) · tip **`v0.8.4`**  
**Type:** In-session **Esc** / **Space** cancel speech (and Esc for take-cancel) on `--voice-only` — no global OS hotkey.  
**Opens:** **`0.8.5` / `v0.8.5`**. **Cola:** **T58** / **V12**

**Not:** wake-word · always-on · voice barge-in · global hotkey (Carbon/IOKit/etc.) · T40 · silence-cut redo · settle redo · ACCEPT claim · speech SDK · Continuity rewrite.

---

## Why this Buy

T56 made Ctrl-C cancel mid-TTS honestly. V12 still promised an in-session key (“cállate y escúchame”) for operators who prefer Esc/Space over Ctrl-C. T56 review N2 left the “Ctrl-C while thinking” gap out of that Buy — T58 does **not** have to fix the whole brain-wait window; it must make cancel-while-speaking reachable without Ctrl-C.

---

## 0. Engineer Buy (locked from V12-DC + this IC)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-voice-session-key`**. Package/tag **`0.8.5` / `v0.8.5`** |
| 2 | **`--voice-only` only** — `--chat` unchanged (no key intercept on silent chat) |
| 3 | **During TTS** — **Esc** or **Space** stops speech with the **same product outcome as T56 Ctrl-C**: kill TTS process group → print **`Jarvis > Habla cancelada.`** (never spoken) → session continues → settle (T57) → mic. Reuse `TtsCancelled` / existing speaker catch; do not invent a second honesty string |
| 4 | **During settle or record** — **Esc** behaves like Ctrl-C on that take (`Grabación cancelada.` / double-exit rule unchanged). **Space** during settle/record: same as Esc (one rule) **or** ignore Space there — pick one, document, test |
| 5 | **No global OS hotkey** — only keys read from the session’s stdin/terminal while `--voice-only` is in the foreground. No LaunchAgents, no accessibility APIs, no new deps |
| 6 | **Implementation judgment (document in report)** — while `speak_egress` blocks on `communicate`, stdin must still be watched (thread + queue, `select`, or equivalent). On Esc/Space: stop the TTS group the same way Ctrl-C does, then raise/signal `TtsCancelled`. Must not leave orphan players. POSIX terminal is enough (voice path already POSIX) |
| 7 | **Thinking / brain gap (narrow)** — Esc/Space **while** `handle_user_text` / LLM is running is **out** unless it falls out for free. Do not add a session-wide key thread that cancels mid-brain. T56 N2 remains accepted residual unless trivial |
| 8 | **Banner / guide** — voice-only banner or §4: Esc/Space corta el habla; Esc (y Space if chosen) cancela la toma al grabar; Ctrl-C sigue igual |
| 9 | **Spoken-continuity map** — tip only; `Habla cancelada.` row already screen-only (T56) — no new surface unless a new string is added (prefer none) |
| 10 | **Tests T1–T6** — mic-free; see §2 |
| 11 | **Out** — wake-word · barge-in · global hotkey · T40 · changing settle default · ACCEPT claim |

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/adapters/voice/external_tts.py` | Watch stdin (or accept a cancel event) during speak; Esc/Space → same stop-group + `TtsCancelled` as SIGINT |
| `src/jarvis/adapters/cli/main.py` | Optional: settle/record Esc(/Space) → KeyboardInterrupt path; banner line; keep speaker catch |
| `docs/USER_GUIDE_VOICE.md` | Keys documented |
| `tests/test_assistant_voice_session_key_b1.py` | **new** T1–T6 |
| Adjust cancel/settle tests if stdin watcher needs a “no key” default | Keep green |
| `pyproject.toml` | `0.8.4` → **`0.8.5`** |
| PRIORIDAD · cola · state · short PLATFORM/CONNECTIONS | **no new C-xxx** |

Do **not** touch orchestrator, Continuity extractors, `record_turn.sh`, phrase tables.

---

## 2. Tests

No real speaker. Fake TTS that blocks; inject Esc/Space into the cancel path (pipe/pty/fake stdin or test hook).

| ID | Assert |
|---|---|
| T1 | During blocking TTS, **Esc** → `TtsCancelled`; process group stopped; no orphan; not `TtsProcessError` |
| T2 | During blocking TTS, **Space** → same as T1 |
| T3 | Voice-only: Esc mid-speak → `Habla cancelada.` · no premature `Sesión cerrada.` · next turn settles + records (fake) |
| T4 | Esc during settle or record → `Grabación cancelada.`; double Esc/Ctrl-C policy still ends session (align with T53/T57) |
| T5 | Bare `--chat` never installs the watcher / never records; Ctrl-C mid-TTS path still works (regression) |
| T6 | Guide mentions Esc/Space; `pyproject` **0.8.5**; tip-pin/ESC fences; no speech deps; no new C-xxx |

---

## 3. Acceptance

- [ ] Live `--voice-only`: while Jarvis speaks, press Esc (and Space) → speech stops, `Habla cancelada.`, mic returns  
- [ ] Esc while Grabando/settle cancels the take; twice exits (same spirit as Ctrl-C)  
- [ ] `0.8.5` · Cursor review · Engineer ★ · tag **`v0.8.5`**

---

## 4. Paste for Claude

```text
Implementation — B1-assistant-voice-session-key (T58 / V12)
Parent: V12-DC + T56 ★ + T57 ★ @ v0.8.4. Package → 0.8.5.

IC: .jes/artifacts/implementation_contract_assistant_voice_session_key_b1.md
DC: .jes/artifacts/design_contract_assistant_voice_cancel_mid_tts_b0.md
Guide: docs/USER_GUIDE_VOICE.md

GOAL: In --voice-only, Esc or Space while Jarvis is speaking cancels
speech exactly like Ctrl-C (T56): kill TTS group, print Habla cancelada.,
session continues, settle + mic. No global OS hotkey. No wake-word.

DO:
- While speak_egress waits, watch session stdin for Esc/Space; stop group
  and raise TtsCancelled (reuse T56 path). Document the watcher approach.
- Esc during settle/record = take cancel like Ctrl-C; Space there: pick
  same-as-Esc or ignore — document + test.
- Brain/thinking-gap Esc is OUT unless free. Banner + guide.
- Tests T1–T6. pyproject 0.8.5. PRIORIDAD/cola/state. No new C-xxx.

NO: wake-word · always-on · voice barge-in · global hotkey · T40 ·
settle redo · ACCEPT claim · Continuity rewrite · new Habla string
```

---

## 5. Cursor note

Claude may implement the full IC without per-edit approval. Stop if the Buy requires a global OS hotkey, an always-on mic thread, or cancelling mid-`handle_user_text` with a new architecture — that is out of lock.
