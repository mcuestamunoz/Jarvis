# Design Contract — Two-mode voice product (`DC-assistant-voice-two-mode-product`)

**Project:** Jarvis  
**Date:** 2026-10-13  
**Author:** JES / Cursor  
**Status:** **DC ready — consumed by T53 IC** — Engineer ★ INV (“si”) + “procede” IC 2026-10-13. IC: [`implementation_contract_assistant_voice_only_loop_b1.md`](implementation_contract_assistant_voice_only_loop_b1.md).  
**Type:** Block lock — **V9** product-surface collapse: Chat | Voice-only  
**Cola:** **V9-DC** (ids **T53-DC** in PRIORIDAD)  
**Parents:** [INV two-mode ★ findings](investigation_report_assistant_voice_two_mode_product_b0.md) · [T52 review ★](implementation_review_assistant_voice_full_spoken_b1.md) @ `v0.7.9` · [cola voz](engineer_note_voice_phase_c_cola.md) · [T46-DC PTT](design_contract_assistant_chat_voice_ptt_b0.md) · [T44-DC spoken continuity](design_contract_assistant_chat_spoken_continuity_b0.md) · [T34-DC channels ★](design_contract_assistant_chat_voice_channels_b0.md) · tip **`v0.7.9`**

**Not** an Implementation Contract. **Not** permission to implement until the V9 / T53 IC is pasted. **No** silence-VAD in this DC’s first code Buy. **No** wake-word. **No** T40/`world/`. **No** greenfield rewrite of `adapters/voice/` seams.

---

## Intent

Jarvis is **personal use for a long time**. Product modes the Engineer will not use must not linger.

Engineer lock (2026-10-13):

> Two modes only: **normal chat** and a **well-designed voice-only** mode.  
> Hybrid `--chat --voice-speak` + typed `hablar` becomes **obsolete** — remove as product surface.  
> Build voice-only first (mic default, fixed-duration cut). Silence detection = later polish.  
> **Reuse** STT/TTS/record/spoken-continuity/sanitize; **rewrite** the session loop; **do not** rewrite the platform.

This DC locks that collapse so the first code Buy stays a surface + loop change on existing seams.

---

## Plan (cola V9+)

| Step | Cola | Buy id | Package | Scope |
|---|---|---|---|---|
| Map | **V9-inv / T53-inv** | `INV-assistant-voice-two-mode-product` | docs | Keep/kill/reuse — ★ findings accepted |
| **This DC** | **V9-DC / T53-DC** | `DC-assistant-voice-two-mode-product` | no bump | Product locks below |
| Code | **V9 / T53** | `B1-assistant-voice-only-loop` | **`0.8.0` / `v0.8.0`** | Voice-only loop + retire hybrid product surface + guide |
| Polish | **V10 / T54** | `B1-assistant-voice-silence-cut` (name indicative) | later | End-of-utterance by silence — **out of V9** |
| Parked | **T40** | craft/`world` voice | TBD | **Out of V9** |

Each step independently ★-able. V9 must not wait on V10.

**Versioning:** V9 is a **product-surface milestone** → package/tag **`0.8.0` / `v0.8.0`** (Engineer default on INV open #3). Not a tip-pin in tests.

---

## Product picture (after V9 ★)

| Mode | CLI (locked names) | In | Out | Brain |
|---|---|---|---|---|
| **Chat** | `--chat` | keyboard | print only | full `run_chat` / Continuity / craft / LLM |
| **Voice-only** | `--voice-only` | mic default → STT → text | print Layer 1 + speak Layer 2 | **same full chat brain** (not Skills-only) |

```text
--voice-only
  → (startup / project pick: same rules as run_chat, spoken where Continuity walls apply)
  → loop:
       wait until TTS idle (no record while Jarvis speaks)
       record fixed N s (JARVIS_RECORD_SECONDS, default 7)
       STT → print "User > [voz] {transcript}" → handle_user_text (same session)
       print Layer 1 · speak Layer 2 (sanitize + spoken_continuity + TTS)
       repeat until exit
```

**Half-mode policy:** no new temporary product modes without a named kill in the same DC. V8 hybrid was scaffolding; V9 kills it.

---

## Seams reused (inventory — tip `v0.7.9`)

| Seam | Where | V9 fate |
|---|---|---|
| Full-chat session body | `run_chat` in `adapters/cli/main.py` | **Reuse brain** — extract/share loop body or call into the same handlers; do **not** invent a second orchestrator |
| Speak + Continuity Layer 2 | `_chat_speak_fn` pattern · `spoken_text_for_wall` · sanitize · `speak_egress` | **Reuse** |
| Record | `record_audio_file` / `JARVIS_RECORD_CMD` / `record_turn.sh` | **Reuse** (fixed duration) |
| STT | `transcribe_audio_file` / `JARVIS_STT_CMD` | **Reuse** |
| Ephemeral wav | `tempfile` + `unlink` in T47 path | **Reuse / reaffirm** |
| Fixtures | `--voice-fixture` · `fixture_loop` | **Keep** CI/non-product |
| Skills-only `run_voice_turn` | `--voice` interactive | **Not** the personal voice-only brain |

---

## Locks (block-level)

| # | Lock |
|---|---|
| 1 | **Exactly two product modes** after V9 ★: **Chat** (`--chat`) and **Voice-only** (`--voice-only`). No third daily mode in the guide or `--help` |
| 2 | **Same brain** — voice-only uses the **full chat** session (Continuity, craft, Skill-first, LLM fallthrough), same honesty as today’s `run_chat`. Do **not** route personal voice-only through Skills-only `run_voice_turn` / interactive `--voice` |
| 3 | **Reuse, don’t rewrite platform** — keep `external_stt` / `external_tts` / `external_record` (record helpers) / `speak_sanitize` / `spoken_continuity` / `scripts/voice/*`. No speech SDK in `pyproject`. No parallel Conversation Engine |
| 4 | **Kill hybrid product surface in the same milestone** — remove **operator** support for `--chat --voice-speak` and typed PTT triggers `hablar`/`habla` as the way to open the mic. Guide and help must not teach them. Implementation may delete the flag/intercept or hard-reject with a one-line pointer to `--voice-only` — IC picks the thinner honest option; dead UX must not remain documented as current |
| 5 | **Mic default cadence** — in voice-only, recording starts **without** typing a trigger: (a) when the session is ready for a user turn (after welcome/startup handling that needs a first line — IC may keep a minimal keyboard exception **only** for the existing project-picker if still required), and (b) **again after each Jarvis spoken reply completes**. Never start record while TTS is still playing (anti-echo) |
| 6 | **V9 cut = fixed duration** — reuse `JARVIS_RECORD_SECONDS` (default **7**). Print `Grabando {n} s…` **without speaking**. **No** silence/VAD, **no** dual-Enter stop, **no** wake-word, **no** always-on background thread in V9 |
| 7 | **Audio ephemeral** — wav in temp → STT → **unlink** (success or failure). Chat truth is the transcript text (`User > [voz] …`). Do not persist clips into `workspace/` |
| 8 | **Layer 1 / Layer 2 unchanged in meaning** — screen Continuity stays full; speak uses existing brief/FULL/`sanitize_for_speech` rules (T45–T52). Update [spoken-continuity map](engineer_note_chat_spoken_continuity_map.md) if any new egress surface appears — same Buy |
| 9 | **Interactive `--voice` (Skills-only REPL)** — **retire from product** (remove from guide primary path and operator `--help` as a daily mode). Keep fixture/`run_voice_turn` for CI. Optional: leave flag as undocumented/CI-only or remove interactive entry — IC chooses thinner; must not compete with `--voice-only` in docs |
| 10 | **`--voice-audio` / `--voice-fixture`** — non-product batch/CI; may remain. Not daily modes |
| 11 | **Honesty** — missing `JARVIS_RECORD_CMD` / `JARVIS_STT_CMD` / `JARVIS_TTS_CMD`, record/STT/TTS failure: print clear `… no disponible:` (or existing families); **do not** invent transcript; **do not** crash the session; Ctrl-C during record cancels that turn only |
| 12 | **Bare `--chat`** stays byte-silent for TTS/mic (no speak, no record) |
| 13 | **Package** — V9 opens **`0.8.0`** and tag **`v0.8.0`**. No version pins in tests (T17 policy) |
| 14 | **Out of V9 unless a later IC ★** — silence/VAD end-of-utterance (**V10**) · wake-word · barge-in · T40 world · reintroducing `--voice-speak`/`hablar` as product · Marvel/clone voice · speech deps in core · always-on daemon |

---

## Engineer defaults locked from INV opens (2026-10-13 “si”)

| Open | Lock in this DC |
|---|---|
| Accept INV findings? | **Yes** — basis for this DC |
| Interactive `--voice`? | **Retire from product** (lock 9) |
| Version bump? | **`0.8.0` / `v0.8.0`** (lock 13) |
| Mic cadence? | **After session ready for a user turn + after each spoken Jarvis reply; never during TTS** (lock 5) |

---

## Relation to prior DCs (does not reopen them)

- **T34-DC** same-brain / external STT-TTS — **affirmed**.  
- **T44/T52** spoken Continuity — **affirmed** on voice-only egress.  
- **T46-DC** PTT on `--chat --voice-speak` — **superseded as product UX** by this DC; seams it introduced (record helper, timed capture) **survive** as infrastructure for voice-only.

---

## Opens

**T53 IC ready** — [`implementation_contract_assistant_voice_only_loop_b1.md`](implementation_contract_assistant_voice_only_loop_b1.md). Paste to Claude. Tip stays **`v0.7.9`** until T53 opens **`0.8.0`**.

SoT: [INV](investigation_report_assistant_voice_two_mode_product_b0.md) · [phase cola](engineer_note_voice_phase_c_cola.md) · [`docs/IMPLEMENTATION_TASKS.md`](../../docs/IMPLEMENTATION_TASKS.md) PRIORIDAD
