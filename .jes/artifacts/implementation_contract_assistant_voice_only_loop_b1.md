# Implementation Contract — Voice-only loop (`B1-assistant-voice-only-loop`)

**Project:** Jarvis  
**Date:** 2026-10-13  
**Author:** JES / Cursor — **IC only** (does not implement `src/` unless Engineer says otherwise)  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.8.0`**

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-10-13) — Cursor **PASS WITH NOTES** · tip **`v0.8.0`**.  
**Parents:** [V9-DC / T53-DC](design_contract_assistant_voice_two_mode_product_b0.md) · [INV ★](investigation_report_assistant_voice_two_mode_product_b0.md) · [T52 ★](implementation_review_assistant_voice_full_spoken_b1.md) · [T47 PTT](implementation_review_assistant_chat_voice_ptt_b1.md) · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md) · tip **`v0.7.9`**  
**Type:** Product-surface collapse — **Chat** (`--chat`) + **Voice-only** (`--voice-only`); kill hybrid `--chat --voice-speak` / typed `hablar` as product UX; reuse voice seams.  
**Opens:** **`0.8.0` / `v0.8.0`**. **Cola:** **T53** / **V9**

**Not:** silence/VAD (V10) · wake-word · always-on thread · barge-in · T40/`world/` · greenfield rewrite of `external_*` / `spoken_continuity` / `speak_sanitize` · speech deps in `pyproject` · ACCEPT claim · Marvel/clone voice · reintroducing hybrid as product.

---

## Why this Buy

Engineer: Jarvis is personal long-term; do not keep modes that will not be used. Hybrid speak+PTT is obsolete. Two modes only — **chat** and a **well-designed voice-only** loop on the **same full chat brain**, reusing T37–T52 seams.

---

## 0. Engineer Buy (locked from V9-DC + this IC)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-voice-only-loop`**. Package/tag **`0.8.0` / `v0.8.0`**. No tip/version pins in tests (T17) |
| 2 | **CLI product modes** — `--chat` (silent) and **`--voice-only`** (new). `--help` / guide teach **only** these two as daily modes |
| 3 | **Voice-only brain** — full chat session (Continuity / craft / Skill-first / LLM fallthrough), same handlers as `run_chat`. **Forbidden:** routing personal voice-only through Skills-only `run_voice_turn` / `run_voice_interactive` as the main loop |
| 4 | **Reuse seams** — `record_audio_file` + `JARVIS_RECORD_CMD` · `transcribe_audio_file` + `JARVIS_STT_CMD` · speak path via existing `_chat_speak_fn`-style helper + `spoken_text_for_wall` + `sanitize_for_speech` + `speak_egress` / `JARVIS_TTS_CMD` · `scripts/voice/*`. Do **not** rewrite those modules’ contracts; thin wrap/call only |
| 5 | **Kill hybrid product UX (same Buy)** — (a) `--chat` combined with `--voice-speak` must **not** enter the old speak+PTT chat: print one honest line pointing to `--voice-only` and exit non-zero (preferred thinner) **or** treat as alias error — do not silently run hybrid. (b) Remove the typed `hablar`/`habla` PTT intercept from the chat path (dead code path once speak-on-chat is gone). (c) Guide must not teach `--chat --voice-speak` or `hablar` as current product |
| 6 | **`--voice-speak` retention** — may remain **only** as the existing batch opt-in for `--voice-fixture` / `--voice-audio` (CI). Help text must say that; not a daily chat mode |
| 7 | **Interactive `--voice`** — retire from product: remove from guide primary path; `--help` must not present it as a daily mode. Preferred thinner: if `--voice` is invoked, print one-line pointer to `--voice-only` (full chat voice) and exit non-zero **or** keep the Skills REPL reachable only for CI with help marked non-product — **prefer redirect+exit** so personal Jarvis has one voice entry. Keep `run_voice_turn` / `--voice-fixture` for tests |
| 8 | **Mic default cadence** — no typed trigger. After the session is ready for a **user turn**, and again **after each Jarvis spoken reply returns** (TTS helper is synchronous today — “after `speak(...)` returns” = TTS idle): print `Jarvis > Grabando {n} s…` **without TTS**, `record_audio_file` for `JARVIS_RECORD_SECONDS` (default **7**), STT, print `User > [voz] {transcript}`, feed transcript into the same turn handling as `run_chat`. **Never** start record while TTS is in progress |
| 9 | **Startup / project picker exception** — if `existing_projects` is non-empty, the **first** selection line may still use **keyboard** `input("User > ")` (same `_handle_startup_selection` behavior as today). After startup is done (`startup_done`), **only** the mic loop supplies user turns (plus Ctrl-C / EOF to end session). If there are **no** projects, skip picker and enter mic loop after welcome |
| 10 | **Exit** — transcript (or keyboard only during picker) matching `exit`/`quit`/`salir` (casefold) ends session with the same spoken/printed goodbye pattern as chat where speak is on. Ctrl-C during record → `Grabación cancelada.` + continue mic loop (do not exit). Ctrl-C / EOF at idle may end session like chat |
| 11 | **Ephemeral wav** — `tempfile.mkstemp(suffix=".wav")`, close fd, record, STT, **`unlink` in `finally`** (success or failure). No clips under `workspace/` |
| 12 | **Layer 1 / 2** — Continuity walls: print full wall; speak via `spoken_text_for_wall` (brief/FULL T45–T52). Non-wall turns: speak what is printed (sanitize inside `speak_egress`). Update [spoken-continuity map](engineer_note_chat_spoken_continuity_map.md) for any new voice-only print/speak surfaces in **this** Buy |
| 13 | **Honesty** — missing/failed RECORD/STT/TTS → existing message families (`Grabación no disponible` / `STT no disponible` / `TTS no disponible`); loop survives; **no** invented transcript/Skill |
| 14 | **Bare `--chat`** — no mic, no TTS (unchanged silent product mode) |
| 15 | **Out** — VAD/silence cut · wake-word · always-on thread · dual-Enter stop · T40 · speech deps · ACCEPT claim · tip-pin tests |

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/adapters/cli/main.py` | Add `--voice-only` → `run_voice_only()` (name flexible). Implement mic loop per locks 8–13. Kill chat+`--voice-speak` hybrid (lock 5). Remove PTT intercept from `run_chat`. Retire interactive `--voice` per lock 7. Keep fixture/audio + optional `--voice-speak` for batch only |
| `src/jarvis/adapters/voice/*` | Prefer **no** contract rewrite. Optional tiny helper e.g. `record_and_transcribe_turn()` if it removes duplication — not required |
| `docs/USER_GUIDE_VOICE.md` | Rewrite around **two modes** only (`--chat`, `--voice-only`). Remove hybrid/`hablar` as current path. Demote fixture/audio to batch/CI. Retire interactive `--voice` from operator § |
| `.jes/artifacts/engineer_note_chat_spoken_continuity_map.md` | Add/adjust rows for voice-only surfaces |
| `tests/test_assistant_voice_only_loop_b1.py` | **new** T1–T8 below |
| `tests/test_assistant_chat_voice_speak_b1.py` · `tests/test_assistant_chat_voice_ptt_b1.py` · related | **Update or retire** assertions that require hybrid `--chat --voice-speak` / `hablar` as product. Keep pure seam tests. Do not leave red suite |
| `tests/test_assistant_voice_interactive_cli_b1.py` | Align with lock 7 (redirect or non-product); suite green |
| `pyproject.toml` | `0.7.9` → **`0.8.0`** |
| Docs / cola / PRIORIDAD / state / PLATFORM or CONNECTIONS short note | **no new C-xxx**; T53 Implemented await review |

Prefer **not** touching `orchestrator.py` domain logic, Skills registry, or Continuity ranking — only CLI/adapters voice wiring.

---

## 2. Suggested loop shape (non-normative sketch)

Claude may structure differently if locks hold:

```text
run_voice_only():
  orch + llm + speak = _chat_speak_fn(True)   # or equivalent
  welcome / list projects
  if projects: keyboard once for picker (lock 9); speak Continuity walls via spoken_text_for_wall
  while True:
    record cue (print only) → record → STT → unlink wav
    on RecordError/SttError/empty: honesty print; continue
    print User > [voz] transcript
    if exit words: goodbye; break
    # same turn body as run_chat after user_input is known
    # (startup already done): handle_user_text → print → speak walls/non-walls
```

Anti-echo: do not call record until the previous `speak(...)` has returned.

---

## 3. Tests

Fake RECORD (writes wav bytes to `{output}`), fake STT (prints a fixed phrase), fake TTS (captures stdin or no-op exit 0). Isolated tmp workspace. **No real mic.**

| ID | Assert |
|---|---|
| T1 | `--voice-only` / `run_voice_only`: fake RECORD+STT yield `armar` → session shows `User > [voz] armar` and full-chat Skill/arm path runs (not Skills-only-only). Speak path invoked for the reply |
| T2 | After one spoken reply, a **second** record cycle runs (mic default loop) — spy/count ≥ 2 record invocations before quit transcript |
| T3 | Bare `--chat`: no record, no TTS import/call on the silent path |
| T4 | `--chat --voice-speak` → non-zero exit **or** hard error pointing at `--voice-only`; does **not** open hybrid PTT chat |
| T5 | Missing `JARVIS_RECORD_CMD` or `JARVIS_STT_CMD` in voice-only → honesty message; loop can still exit cleanly |
| T6 | Continuity wall turn (fake STT `estado` or load path): screen still full wall; speak uses Layer 2 extractor (brief unless FULL phrase) — reuse T45/T52 guarantees, don’t rewrite extractor |
| T7 | Interactive `--voice` per lock 7 (redirect/exit or explicitly non-product); `--voice-fixture` still runnable; no speech deps; `pyproject` **0.8.0**; tip-pin + ESC fences green |
| T8 | Guide teaches `--chat` + `--voice-only` as the two modes; does **not** present `--chat --voice-speak` / `hablar` / interactive `--voice` as current daily product; spoken-continuity map updated if new surfaces |

---

## 4. Acceptance

- [ ] `python -m jarvis.main --voice-only` with env RECORD/STT/TTS: mic cycles without typing `hablar`; full chat brain; Continuity ears correct  
- [ ] `python -m jarvis.main --chat` silent as today  
- [ ] Hybrid `--chat --voice-speak` rejected/redirected; guide matches two modes  
- [ ] `0.8.0` · suite green for owned tests · Cursor review · Engineer ★ ACCEPT · tag **`v0.8.0`**

---

## 5. Paste for Claude

```text
Implementation — B1-assistant-voice-only-loop (T53 / V9)
Parent: V9-DC two-mode product ★. Tip v0.7.9 → package/tag 0.8.0.

IC: .jes/artifacts/implementation_contract_assistant_voice_only_loop_b1.md
DC: .jes/artifacts/design_contract_assistant_voice_two_mode_product_b0.md
INV: .jes/artifacts/investigation_report_assistant_voice_two_mode_product_b0.md
Guide: docs/USER_GUIDE_VOICE.md
Map: .jes/artifacts/engineer_note_chat_spoken_continuity_map.md

PRODUCT: exactly two daily modes — --chat (silent) and --voice-only
(full chat brain + mic default + TTS). Personal Jarvis — no dead modes.

DO:
- Add --voice-only → voice-only session loop on the SAME full chat
  brain as run_chat (Continuity/craft/Skills/LLM). NOT run_voice_turn
  as the main loop.
- Mic default: after session ready for a user turn, and again after
  each speak() returns — print "Grabando {n} s…" WITHOUT TTS, then
  existing record_audio_file (JARVIS_RECORD_SECONDS default 7) →
  transcribe_audio_file → print "User > [voz] {transcript}" → same
  turn handling. Temp wav unlink in finally.
- Keyboard exception ONLY for initial project picker when projects
  exist (lock 9). After startup_done, mic only (+ Ctrl-C/EOF).
- Reuse external_record/stt/tts, spoken_text_for_wall, sanitize,
  scripts/voice/*. Do NOT greenfield-rewrite those modules.
- Kill hybrid: --chat --voice-speak must NOT open old speak+PTT chat
  (honest redirect to --voice-only, non-zero). Remove hablar/habla
  PTT intercept from run_chat. Guide must not teach hybrid.
- --voice-speak may remain ONLY for --voice-fixture/--voice-audio.
- Retire interactive --voice from product (prefer redirect→--voice-only);
  keep fixtures/CI.
- Update/retire tests that required hybrid chat+speak/PTT as product.
  New tests/test_assistant_voice_only_loop_b1.py T1–T8. Suite green.
- pyproject 0.8.0. PRIORIDAD/cola/PLATFORM or CONNECTIONS short note —
  no new C-xxx. Update spoken-continuity map if new surfaces.
- Layer 1/2 Continuity meaning unchanged (T45–T52).

NO: silence/VAD · wake-word · always-on · T40 · speech deps ·
ACCEPT claim · tip version pins · second brain · keeping hablar as UX
```

---

## 6. Cursor note

This IC authorizes Claude to implement the listed scope without per-edit approval. Stop for ambiguity outside locks (e.g. wanting wake-word or VAD in this Buy). Cursor reviews after code exists; same-session self-PASS is not review of record.
