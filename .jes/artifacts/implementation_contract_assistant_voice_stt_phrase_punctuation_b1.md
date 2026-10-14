# Implementation Contract — STT phrase-match punctuation honesty (`B1-assistant-voice-stt-phrase-punctuation`)

**Project:** Jarvis  
**Date:** 2026-10-14  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.8.2`**

**Status:** **IC ready (amended 2026-10-14)** — lock 2b scope explicit after Claude pause. Paste / resume.  
**Parents:** [V11-DC / T55-DC](design_contract_assistant_voice_stt_phrase_punctuation_b0.md) · [T53 review ★](implementation_review_assistant_voice_only_loop_b1.md) N2 · [T54 review](implementation_review_assistant_voice_silence_cut_b1.md) · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md) · tip package **`0.8.1`**  
**Type:** Trailing-punctuation honesty on FULL + shared Skill-first normalize (STT). Optional dead PTT export cleanup.  
**Opens:** **`0.8.2` / `v0.8.2`**. **Cola:** **T55** / **V11**

**Not:** wake-word · barge-in / anti-echo · expanding phrase tables · T40 · silence-cut changes · ACCEPT claim · tip version pins · speech SDK · forking a Continuity-only normalize.

---

## Why this Buy

Whisper often returns `Completo.` / `Estado.`. Exit already strips trailing punct; FULL and Continuity defer still exact-match and miss → wrong Layer 2 (brief instead of FULL) or miss Continuity wall. T53 N2 + V10-DC lock 11 deferred this; now it is the Buy.

**Scope amend (2026-10-14):** `_normalize_for_continuity_match` is shared by **all** Skill-first matchers (ARM/DISARM/HOLD/…/GO_TO), not only Continuity defer. Cursor locks **option 1 — all matchers**: strip inside that one function; do not fork. Report must name the widening.

---

## 0. Engineer Buy (locked from V11-DC + this IC)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-voice-stt-phrase-punctuation`**. Package/tag **`0.8.2` / `v0.8.2`** |
| 2 | **Normalize** — after existing strip + lower/casefold + NFKD accent-strip, strip trailing characters from the finite set **`.,;:!?¡¿`** (same idea as `_is_voice_only_exit`). Apply in: (a) `spoken_continuity._normalize` used by `is_full_continuity_request`; (b) **`assistant_task._normalize_for_continuity_match` itself** — one strip for every caller (Continuity defer **and** ARM/DISARM/HOLD/LAND/GO_TO/FOLLOW/PATROL/CHARGE/… plus `parse_go_to_destination`). **Do not** add a Continuity-only fork. Do **not** invent fuzzy / substring matching |
| 3 | **Phrase tables unchanged** — `FULL_CONTINUITY_PHRASES`, `CONTINUITY_DEFER_PHRASES`, and all Skill-first phrase frozensets stay as locked; only the normalize step changes. **Explicit behavior widening:** STT `Armar.` / `Hold!` / `Go to 1 2.` match like typed text — flag in the implementation report |
| 4 | **Layer 1/2 payloads unchanged** — no edit to `brief_spoken_continuity` / `full_spoken_continuity` / `render_*` / Continuity ranking |
| 5 | **Exit path** — `_is_voice_only_exit` remains punct-tolerant; do not regress. Aligning its strip set with lock 2 is fine if cheaper |
| 6 | **Dead PTT (T53 N1)** — remove unused `is_ptt_trigger` / `PTT_TRIGGER_PHRASES` from `adapters/voice` public exports **and** delete the helpers if no remaining imports; update any tests that only asserted export presence. Do **not** restore hybrid `hablar` intercept. If a historical PTT test file still unit-tests the helper in isolation, either delete those unit cases or keep a private test-only shim — prefer deletion of dead product surface |
| 7 | **Two modes / silence cut** — `--chat` and `--voice-only` unchanged as products; T54 silence envs/cue untouched |
| 8 | **Guide** — short honesty note: trailing STT punctuation on Continuity/FULL **and** locked Skill-first phrases is ignored |
| 9 | **Spoken-continuity map** — tip line only if needed; no new egress surface |
| 10 | **Tests T1–T7** — mic-free; see §2 |
| 11 | **Out** — wake-word · barge-in · anti-echo · new phrases · T40 · ACCEPT claim · rewriting Continuity extractors · silence-cut redo · Continuity-only normalize fork |

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/adapters/voice/spoken_continuity.py` | `_normalize` strips trailing punct (lock 2a) |
| `src/jarvis/intelligence/assistant_task.py` | `_normalize_for_continuity_match` strips trailing punct (lock 2b) |
| `src/jarvis/adapters/voice/external_record.py` | Remove dead PTT trigger helper/phrases (lock 6) |
| `src/jarvis/adapters/voice/__init__.py` | Drop PTT re-exports |
| `src/jarvis/adapters/cli/main.py` | Only if aligning exit strip; no behavior change required |
| `docs/USER_GUIDE_VOICE.md` | Honesty line |
| `tests/test_assistant_voice_stt_phrase_punctuation_b1.py` | **new** T1–T6 |
| Adjust existing voice Continuity/FULL/PTT tests | Green under new normalize; drop dead PTT unit asserts |
| `pyproject.toml` | `0.8.1` → **`0.8.2`** |
| PRIORIDAD · cola · state · short PLATFORM/CONNECTIONS note | **no new C-xxx** |

Do **not** touch orchestrator, Skill registry, `record_turn.sh`, or Continuity builders.

---

## 2. Tests

No real mic. String-level + existing voice-only fakes.

| ID | Assert |
|---|---|
| T1 | `is_full_continuity_request("Completo.")` / `"completo!"` / `"¿completo?"` → True; `"completos"` → False; multi-word `"Dame detalles."` → True |
| T2 | Continuity defer: `"Estado."` / `"estado?"` matches the same as `"estado"` (public/testable path or `_normalize_for_continuity_match`) |
| T3 | **Skill-first widening:** at least one ARM phrase with trailing punct (e.g. `"Armar."`) classifies like bare `"armar"`; one HOLD (e.g. `"Hold!"`); one GO_TO with coords (e.g. `"Go to 1 2."` or Spanish sibling already in the table) parses/classifies like without punct. A near-miss that must **not** match still fails (e.g. `"armarlo"` / wrong shape) — no new phrases |
| T4 | Untouched payloads: a FULL turn still speaks narrated Layer 2 (not verbatim wall); brief path still brief — reuse/adapt a small existing spoken_continuity fixture assert |
| T5 | Voice-only exit still accepts `Salir.` / `salir!`; `--chat` still silent (no record) |
| T6 | `is_ptt_trigger` / `PTT_TRIGGER_PHRASES` **gone** from `jarvis.adapters.voice` public API; no `hablar` intercept restored in `run_chat` / `_run_chat_session` |
| T7 | Guide mentions trailing punctuation honesty (Continuity/FULL **and** Skill phrases); `pyproject` **0.8.2**; tip-pin/ESC fences green; no speech deps |

---

## 3. Acceptance

- [ ] Live `--voice-only`: say `completo` → FULL; STT showing `Completo.` still FULL  
- [ ] Say `estado` with trailing punct → Continuity wall (not LLM miss)  
- [ ] Optional: `armar.` still arms policy latch (same as typed)  
- [ ] `0.8.2` · Cursor review · Engineer ★ · tag **`v0.8.2`**

---

## 4. Paste for Claude

```text
Implementation — B1-assistant-voice-stt-phrase-punctuation (T55 / V11)
Parent: V11-DC + T53 N2 + T54 review @ 0.8.1. Package → 0.8.2.
AMEND 2026-10-14: lock 2b = ALL matchers (option 1). Resume.

IC: .jes/artifacts/implementation_contract_assistant_voice_stt_phrase_punctuation_b1.md
DC: .jes/artifacts/design_contract_assistant_voice_stt_phrase_punctuation_b0.md
Guide: docs/USER_GUIDE_VOICE.md

GOAL: STT transcripts like "Completo." / "Estado." / "Armar." match the
same locked phrase tables as typed text. No fuzzy match. No new phrases.
Layer 1/2 payloads unchanged.

DO:
- Strip trailing .,;:!?¡¿ after existing strip/casefold/NFKD in
  spoken_continuity._normalize AND assistant_task._normalize_for_continuity_match
  (the shared helper — Continuity defer + all Skill-first callers).
  Do NOT fork a Continuity-only normalize.
- Report must flag the Skill-first behavior widening (ARM/HOLD/GO_TO/…).
- Remove dead is_ptt_trigger / PTT_TRIGGER_PHRASES from adapters/voice
  (T53 N1). Do not restore hybrid hablar.
- Guide honesty line (Continuity/FULL + Skill phrases). pyproject 0.8.2.
  Tests T1–T7. PRIORIDAD/cola/state. No new C-xxx. No speech deps.

NO: wake-word · barge-in/anti-echo · T40 · silence-cut redo · expanding
phrase tables · Continuity-only normalize fork · ACCEPT claim ·
rewriting Continuity extractors
```

---

## 5. Cursor note

Claude may implement the full IC scope without per-edit approval. Scope 2b is **resolved: all matchers**. Stop only if the Buy requires a new always-on thread, barge-in, expanding phrase tables, or a Continuity-only normalize fork — that is out of lock.
