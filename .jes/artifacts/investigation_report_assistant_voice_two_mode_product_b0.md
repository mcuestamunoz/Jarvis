# Investigation report — Voice product surface → two modes (chat | voice-only)

**Project:** Jarvis  
**Date:** 2026-10-13  
**Author:** Cursor (JES evaluation)  
**Status:** ★ **FINDINGS ACCEPTED** (Engineer “si”, 2026-10-13) — DC ready: [`design_contract_assistant_voice_two_mode_product_b0.md`](design_contract_assistant_voice_two_mode_product_b0.md)  
**Type:** Product-surface + reuse evaluation (not an IC; no `src/` edits)  
**Tip parent:** **`v0.7.9`** (T52 ★) · PRIORIDAD = Engineer pick  
**Parents:** [voice channels DC ★](design_contract_assistant_chat_voice_channels_b0.md) · [T46-DC PTT](design_contract_assistant_chat_voice_ptt_b0.md) · [cola voz](engineer_note_voice_phase_c_cola.md) · [FN-017](engineer_note_voice_spoken_polish_field_fn017.md) · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md) · Engineer direction 2026-10-13

**Not** permission to implement. **Not** a Design Contract. **Not** T40/`world/`.

---

## 0. Engineer direction (this evaluation's brief)

Jarvis is **personal use for a long time** and will grow. Do not keep product modes the Engineer will not use.

Desired **product** end-state:

| Mode | Meaning |
|---|---|
| **Chat** | Normal `--chat` — keyboard in, text out. No mic, no TTS. |
| **Voice-only** | Well-designed full interaction — mic default, Jarvis speaks, same chat brain. |

Obsolete as a *product mode*: `--chat --voice-speak` + typed `hablar` (hybrid half-step).

Build order already agreed in chat: **voice-only with mic default + fixed-duration cut first**, silence-detection polish later.

Question this report answers: **rewrite vs reuse**, and **what to eliminate vs keep**, so the next DC is not a accidental third brain or a pile of dead flags.

---

## 1. What exists today (forensic inventory)

### 1.1 Operator entry points

| Surface | Flag / path | Brain | In | Out | Product role today |
|---|---|---|---|---|---|
| Chat silent | `--chat` | full `run_chat` `TERMINAL` | keyboard | print | **Keep forever** (mode Chat) |
| Chat + Jarvis speaks | `--chat --voice-speak` | same `run_chat` | keyboard (+ optional `hablar`) | print + TTS | **Hybrid — Engineer marks obsolete** |
| PTT trigger | type `hablar`/`habla` under speak | same loop | timed record → STT → text | same | Bridge after T47; **UX obsolete** once voice-only exists |
| Skills-only REPL | `--voice` | Skills only `source=VOICE` | keyboard | print + TTS | Demo/narrow channel — **not** full personal Jarvis |
| Batch audio | `--voice-audio PATH` | Skills `run_voice_turn` | file | optional TTS | CI / one-shot |
| Batch fixture | `--voice-fixture PATH` | Skills `run_voice` | text lines | optional TTS | CI / regression |

### 1.2 Seams under `src/jarvis/adapters/voice/` (infrastructure)

| Module | Job | Personal-product fate |
|---|---|---|
| `external_stt.py` | `JARVIS_STT_CMD` → transcript | **KEEP** — voice-only needs it |
| `external_tts.py` / `speak_egress` | `JARVIS_TTS_CMD` → speak | **KEEP** |
| `external_record.py` | `JARVIS_RECORD_CMD` timed wav + `is_ptt_trigger` | **KEEP record seam**; **retire trigger UX** (or shrink to non-product helper) |
| `speak_sanitize.py` | Layer-2 cleanup before TTS | **KEEP** |
| `spoken_continuity.py` | brief / FULL narrated Continuity | **KEEP** — voice-only Continuity walls need it |
| `fixture_loop.py` | text fixture → Skills turns | **KEEP** for CI / Skill-first proofs |

### 1.3 Operator scripts (external processes)

`scripts/voice/{piper_tts,whisper_stt,record_turn}.sh` — **KEEP**. Still the free-first operator path; no speech SDK in `pyproject`.

### 1.4 Critical loop fact (T47)

```text
hablar → tempfile wav → record N s → STT → unlink wav
      → print "User > [voz] {transcript}"
      → user_input = transcript → same run_chat body
```

Audio is already **ephemeral**. Chat truth is **text**. Voice-only must preserve that honesty.

Mic stop today = **fixed seconds** (`JARVIS_RECORD_SECONDS`, default 7). **No** silence VAD.

---

## 2. Verdict: do **not** greenfield-rewrite the voice stack

T35–T52 bought the hard parts:

- external STT/TTS/record process seams + honesty errors  
- spoken Continuity Layer 1/2 (no LLM)  
- speak sanitizer + Spanish brief/FULL  
- same-brain discipline (`handle_user_text`, no parallel Conversation Engine)

A rewrite of `adapters/voice/` would discard that value and reopen FN-017-class failures.

**Correct approach:**

> **Reuse infrastructure. Rewrite the product loop / surface. Delete obsolete operator modes.**

That is a **surface collapse**, not a platform rebuild.

---

## 3. Keep / kill / rewrite matrix

### 3.1 KEEP (reuse as-is or thin wrap)

| Item | Why |
|---|---|
| `--chat` silent | Mode Chat |
| `speak_egress` + sanitize + TTS scripts | Jarvis speaks in voice-only |
| `record_audio_file` + `record_turn.sh` | Mic capture |
| `transcribe_audio_file` + whisper wrapper | Speech → text |
| `spoken_text_for_wall` / brief / FULL | Continuity ears |
| Ephemeral wav + unlink | Anti-contamination (already correct) |
| Fixture / `--voice-fixture` (+ tests) | Non-product regression |
| Same-brain lock (T34-DC) | Non-negotiable |

### 3.2 KILL as **product** surfaces (after voice-only ★)

| Item | Why kill |
|---|---|
| `--chat --voice-speak` as the “daily” voice mode | Hybrid the Engineer will not use |
| Typed `hablar`/`habla` as the way to open the mic | Becomes dead UX once mic-default voice-only exists |
| Documenting three overlapping “how to talk” paths in the guide | Contaminates personal UX; one voice path only |

**Kill means:** remove from PRIORIDAD / USER_GUIDE operator path and CLI help as *supported product*. Tests that only exist to pin the hybrid flag should migrate to voice-only or shrink to seam unit tests.

### 3.3 REWRITE (small, deliberate)

| Item | What changes |
|---|---|
| Chat REPL voice branch | Today: `run_chat(speak_tts=bool)` + PTT intercept. Target: **two entry modes** — silent chat vs voice-only loop — not a bool bolted onto chat |
| Session cadence | Voice-only: mic **ready/default** (start record without typing `hablar`); still fixed-duration in V9 |
| CLI flags | Collapse to e.g. `--chat` and `--voice-only` (exact names = DC). Retire `--voice-speak` from product docs/help |
| Guide | Rewrite §4 around two modes only |

### 3.4 DEFER (explicitly later — not in first voice-only Buy)

| Item | Notes |
|---|---|
| Silence / VAD end-of-utterance | V10 polish; do not block V9 |
| Wake-word / always-on background thread | Still out unless ★ |
| T40 craft/`world/` voice | Parked |
| Replacing Piper/whisper vendors | Seam stays; vendor ★ separate |
| Skills-only `--voice` REPL | See §4 |

### 3.5 Borderline: `--voice` (Skills-only interactive)

For **personal full Jarvis**, Skills-only REPL is a second incomplete product. Recommendation:

- **Do not advertise** as a daily mode.  
- **Keep** the underlying `run_voice_turn` / fixture path for CI and Skill-first isolation tests.  
- **Optional retire** of interactive `--voice` flag in the same surface-collapse Buy *or* a tiny follow-up — Engineer ★ picks. Default recommendation: **retire interactive `--voice` from the guide and help**; keep fixtures.

`--voice-audio` can stay as power-user/CI one-shot (not a “mode”).

---

## 4. Target architecture (after collapse)

```text
┌─────────────────────────────────────────────┐
│  PRODUCT (personal)                         │
│    --chat              → run_chat silent    │
│    --voice-only        → voice loop         │
│         record → STT → text                 │
│         → same handle_user_text / Continuity│
│         → print Layer 1                     │
│         → speak Layer 2 (sanitize+TTS)      │
│         → (next) mic again                  │
└─────────────────────────────────────────────┘
              │
              ▼  (unchanged package)
┌─────────────────────────────────────────────┐
│  SEAMS  adapters/voice/* + scripts/voice/*  │
└─────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  CI / non-product                           │
│    --voice-fixture · seam unit tests        │
│    (optional --voice-audio)                 │
└─────────────────────────────────────────────┘
```

**Source lock for voice-only (recommend in DC):** stay on the **full chat session** path (today’s PTT uses `TERMINAL` + `run_chat` body). Do **not** route personal voice-only through Skills-only `run_voice_turn` — that drops Continuity/craft. Whether metadata `source=VOICE` is threaded later is optional; product brain must remain full chat.

---

## 5. Recommended cola (refined from chat proposal)

Continuation of **voice phase** post T52 — **not** Fase C silicon, **not** T40.

| # | Buy | Scope | Package bump (indicative) |
|---|---|---|---|
| **V9-inv** | this report | Keep/kill/reuse — ★ findings | none |
| **V9-DC** | `DC-assistant-voice-two-mode-product` | Lock 2 product modes; mic-default voice-only; fixed cut; kill hybrid speak+PTT; reuse seams; out: VAD/wake/T40 | none |
| **V9** | `B1-assistant-voice-only-loop` | Implement voice-only loop + CLI; wire Continuity speak; ephemeral wav; **remove or hard-deprecate** `--voice-speak`/`hablar` product path; rewrite guide | **`0.8.0`** candidate (product surface milestone) *or* `0.7.10` if Engineer wants quieter bump — ★ pick in DC |
| **V9-retire** | (may merge into V9) | Delete dead PTT trigger path / flag tests migrate; help text | same Buy preferred |
| **V10** | silence end-of-utterance | Polish record cut only | later |
| **V11+** | anti-echo while TTS plays, cancel, hotkey | UX polish | later |

**Policy lock for growth:** every new voice feature must answer: *does this survive as one of the two modes, or is it a temporary half-mode?* Half-modes are forbidden unless explicitly time-boxed as scaffolding with a named kill date in the same DC.

---

## 6. Risks if we get this wrong

| Risk | Mitigation |
|---|---|
| Third brain (`run_voice_turn` for personal voice) | DC lock: voice-only = full `run_chat` brain |
| Keep `--voice-speak` “just in case” | Violates Engineer personal-use rule; kill in same milestone as voice-only ★ |
| Rewrite `spoken_continuity` / sanitize | Unnecessary; reuse |
| Ship VAD in V9 | Scope creep; fixed duration first |
| Always-on thread without DC | Honesty/privacy/echo; out until ★ |
| Leave `--voice` Skills REPL in the guide | Confuses “the” voice mode |

---

## 7. What the next DC must lock (checklist)

1. Exactly **two** product modes: Chat · Voice-only.  
2. Voice-only = full chat brain + Continuity Layer 1/2 + TTS.  
3. Mic **default** cadence (when record starts: session open / after Jarvis finishes speaking — pick one).  
4. V9 cut = **fixed duration** (reuse `JARVIS_RECORD_SECONDS`).  
5. Wav ephemeral (unlink) — already true; reaffirm.  
6. **Retire** `--chat --voice-speak` and typed `hablar` as product UX in the same milestone.  
7. Reuse `external_*` + sanitize + spoken_continuity + scripts — no greenfield.  
8. Out: silence VAD (V10), wake-word, T40, speech deps in `pyproject`.  
9. Guide rewritten to two modes only.  
10. Version bump policy (`0.7.10` vs `0.8.0`).

---

## 8. Recommendation (one paragraph)

**Do not rewrite the voice platform.** Collapse the product to **Chat + Voice-only**, implement voice-only as a new loop on top of the existing record/STT/TTS/spoken-continuity seams, and **delete the hybrid speak+PTT operator path** in the same milestone so it cannot linger as dead surface. Silence detection is a later polish Buy. This continues the voice phase after T52; it is the correct “last feature leaves the product clean” move for a long-lived personal Jarvis.

---

## 9. Opens for Engineer ★ — **CLOSED** (2026-10-13)

| Open | Decision |
|---|---|
| Accept findings as V9-DC basis? | **★ Yes** |
| Interactive `--voice`? | **Retire from product** (fixtures/CI may remain) |
| Package bump? | **`0.8.0` / `v0.8.0`** |
| Mic cadence? | After session ready for a user turn **and** after each spoken Jarvis reply; never during TTS |

Next: **V9-DC** ★ delivered → **V9 / T53 IC** when Engineer proceeds (no `src/` until IC pasted to Claude).
