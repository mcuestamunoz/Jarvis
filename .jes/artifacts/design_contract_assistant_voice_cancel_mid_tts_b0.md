# Design Contract — Voice comfort V12 (`DC-assistant-voice-cancel-mid-tts` block)

**Project:** Jarvis  
**Date:** 2026-10-14  
**Author:** JES / Cursor  
**Status:** **DC ready** — Engineer approved V12 plan after T54/T55 ★ @ `v0.8.2`.  
**Type:** Block lock — **V12** comfort on `--voice-only` (cancel / anti-echo settle / in-session key)  
**Cola:** **V12-DC** · first code Buy **T56**  
**Parents:** [INV two-mode §5](investigation_report_assistant_voice_two_mode_product_b0.md) (was “V11+”) · [T53 ★](implementation_review_assistant_voice_only_loop_b1.md) · tip **`v0.8.2`** · [cola voz](engineer_note_voice_phase_c_cola.md)

**Not** an Implementation Contract. **Not** wake-word · always-on mic · continuous barge-in by voice · T40 · speech SDK in `pyproject`.

---

## Intent

After V9–V11, voice-only works: same brain, silence cut, STT punctuation honesty. Remaining comfort gaps from the INV:

1. **Cancel while Jarvis speaks** — today Ctrl-C is honest mainly **during record**; mid-TTS the external player often keeps going or the session feels wrong.  
2. **Anti-echo settle** — speaker bleed into the next capture.  
3. **In-session key** — optional Space/Esc “cállate y escúchame” without a global OS hotkey.

This DC locks the **ordered** Buys so T56 stays small.

---

## Plan (ordered ★-able Buys)

| Step | Cola | Buy | Package | Scope |
|---|---|---|---|---|
| **This DC** | **V12-DC** | `DC-assistant-voice-v12-comfort` (file: cancel-mid-tts block) | no bump | Locks below |
| **First code** | **T56** | `B1-assistant-voice-cancel-mid-tts` | **`0.8.3` / `v0.8.3`** | Ctrl-C (primary) stops TTS → session continues → mic reopens |
| Later | **T57** | anti-echo settle post-TTS | `0.8.4` (indicative) | Short fixed delay / env before record — **out of T56** |
| Later | **T58** | in-session key (Space/Esc) | `0.8.5` or merge | Only if Ctrl-C is not enough — **out of T56** |
| Parked | **T40** | craft/`world` | TBD | **Out** |

---

## Product picture (after T56 ★)

```text
--voice-only
  → Jarvis prints + speaks reply
  → user Ctrl-C while TTS still playing
       → TTS process killed (no orphan player)
       → print-only honesty line (never spoken)
       → session continues
       → mic opens for next turn (same silence cut)
  → Ctrl-C during record: unchanged (cancel turn; double → exit)
```

`--chat` unchanged (no TTS). No new product mode.

---

## Locks (block-level)

| # | Lock |
|---|---|
| 1 | **Two modes stay** — only `--voice-only` gains cancel-mid-TTS session behavior. `--chat` silent |
| 2 | **Cancel = interrupt speak, not exit** — one Ctrl-C during TTS must **not** end the session and must **not** speak “Sesión cerrada.” Reopen mic for the next turn |
| 3 | **Kill the external TTS child** — `speak_egress` (or its caller) must stop the running `JARVIS_TTS_CMD` process on cancel so the speaker goes quiet. Prefer process-group / terminate+kill honesty; no new speech package |
| 4 | **Record cancel unchanged** — T53 double Ctrl-C during grabación stays; do not regress silence cut (T54) |
| 5 | **Print-only cue** — short screen line e.g. `Habla cancelada.` (exact string = IC). Never TTS that line. Update spoken-continuity map (**screen-only**) |
| 6 | **No wake-word / always-on / voice barge-in** — cancel is keyboard (Ctrl-C), not “speak over Jarvis” detection |
| 7 | **T57 / T58 out of T56** — post-TTS settle delay and Space/Esc hotkey are later Buys unless a one-line freebie is already required for T56 tests |
| 8 | **Guide** — document Ctrl-C mid-speech vs mid-record |
| 9 | **Package** — T56 opens **`0.8.3` / `v0.8.3`**. No tip pins. No new C-xxx |
| 10 | **Out of V12 block** — T40 · rewriting Continuity · silence-cut redo · expanding phrase tables · ACCEPT claim in IC |

---

## Opens

T56 IC: [`implementation_contract_assistant_voice_cancel_mid_tts_b1.md`](implementation_contract_assistant_voice_cancel_mid_tts_b1.md).

SoT: [cola](engineer_note_voice_phase_c_cola.md) · [`docs/IMPLEMENTATION_TASKS.md`](../../docs/IMPLEMENTATION_TASKS.md) PRIORIDAD
