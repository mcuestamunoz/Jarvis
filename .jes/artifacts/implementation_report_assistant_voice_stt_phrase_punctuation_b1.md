# Implementation Report — STT phrase-match punctuation honesty (`B1-assistant-voice-stt-phrase-punctuation`, T55 / V11)

**Project:** Jarvis
**Date:** 2026-10-14
**Implementer:** Claude Code (Engineer paste)
**Contract:** [IC](implementation_contract_assistant_voice_stt_phrase_punctuation_b1.md) · [V11-DC](design_contract_assistant_voice_stt_phrase_punctuation_b0.md)
**Parent:** package `0.8.1` (T54 reviewed PASS WITH NOTES, await ★)
**Status:** ★ **ACCEPT CLOSED** (2026-10-14) @ tip **`v0.8.2`**.
**Package:** `0.8.1` → **`0.8.2`**.

---

## 0. Scope decision taken with the Engineer before implementing

Lock 2b names `assistant_task._normalize_for_continuity_match` as "used by Continuity defer". In code it is the **shared** normalize of every Skill-first kind in `assistant_task.py`: Continuity defer, ARM/DISARM (software latch), HOLD, LAND, GO_TO (incl. `parse_go_to_destination`), TAKEOFF, RETURN_HOME, FOLLOW, PATROL, CHARGE. Applying lock 2b literally therefore also makes `Armar.` / `¿Hold?` / `Go to 1 2.` match their Skills (before: LLM fallthrough). Claude stopped and asked; **Engineer chose "all matchers"** (literal lock 2b). This is an explicit behavior widening beyond the IC's stated purpose — pinned by T2. Phrase tables unchanged; still exact match.

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/adapters/voice/spoken_continuity.py` | `_normalize` (FULL detection) strips `_EDGE_PUNCTUATION = ".,;:!?¡¿"` + whitespace from **both ends** after strip/casefold/NFKD. Docstrings. |
| `src/jarvis/intelligence/assistant_task.py` | `_normalize_for_continuity_match` — same strip, same set. Comment documents the shared scope. |
| `src/jarvis/adapters/voice/external_record.py` | T53 N1: `PTT_TRIGGER_PHRASES`, `_normalize`, `is_ptt_trigger` deleted (and the now-unused `unicodedata` import); docstring notes removal. |
| `src/jarvis/adapters/voice/__init__.py` | PTT re-exports removed. |
| `src/jarvis/adapters/cli/main.py` | **Unchanged** — `_is_voice_only_exit` already strips the same set (lock 5). |
| `tests/test_assistant_voice_stt_phrase_punctuation_b1.py` | **new** T1–T6 |
| `docs/USER_GUIDE_VOICE.md` | §4.1 FULL bullet ("la puntuación de los extremos da igual"); §8 new bullet (T55) + "La transcripción decide" clarified |
| map · PLATFORM · CONNECTIONS · cola · PRIORIDAD · state · `pyproject` | tip line / short T55 notes; T55 → Implemented; `0.8.2`. No new C-xxx, no new spoken surface |

**Untouched:** phrase tables (`FULL_CONTINUITY_PHRASES`, `CONTINUITY_DEFER_PHRASES`, Skill phrase sets), `brief_/full_spoken_continuity`, `render_*`, Continuity ranking, orchestrator, Skill registry, `record_turn.sh`, two modes, silence cut.

**Separate commit before this one:** Cursor's uncommitted V11-DC + T55 IC + T54 review + cola/PRIORIDAD/state edits, committed as found.

## 2. Notes on the normalize

- **Both ends, not only trailing.** IC T1 requires `¿completo?` → True, which needs the leading `¿` removed; stripping the finite set from both ends (same as `_is_voice_only_exit`) satisfies that. Interior punctuation is untouched (`go to 1.5 2.5` keeps its decimals).
- **Whitespace re-stripped** together with the set, so `completo .` / `¿ estado ?` match too.
- Not fuzzy: `completos`, `estados`, `armado.`, `salirme` do not match (T1/T2/T4).

## 3. Tests

| ID | What it proves |
|---|---|
| T1 | `Completo.`, `completo!`, `¿completo?`, `¡Completo!`, `completo .`, `Dame detalles.` → FULL; `completos`, `completo ya`, `muy completo`, `detalles` → not |
| T2 | `Estado.`/`estado?`/`¿Estado?` → `defer_to_continuity` Task; `estados` → none. **Widening pinned:** `Armar.` → arm-policy Task, `¿Hold?` → hold Task, `armado.` → none, `Go to 1 2.` / `ir a 1.5 -2.5?` parse. E2E `--voice-only` STT `Estado.` → Continuity wall on screen + brief spoken |
| T3 | E2E `Completo.` → exactly one narrated FULL capture; `estado?` + load stay brief; no wall text ever spoken; screen still full wall |
| T4 | `_is_voice_only_exit`: `Salir.`, `salir!`, `¿Salir?`, `EXIT`, `quit.` yes; `salirme` no; voice-only `salir!` ends; bare `--chat` never records/speaks |
| T5 | `is_ptt_trigger` / `PTT_TRIGGER_PHRASES` gone from `adapters.voice` (attr + `__all__`) and `external_record`; no PTT/`"hablar"` in `run_chat` / `_run_chat_session` |
| T6 | guide mentions punctuation + `Completo.`; no speech/fuzzy deps; tip-pin, ESC, AuthoritySource guards |

```text
pytest tests/test_assistant_voice_stt_phrase_punctuation_b1.py -q   → 6 passed
pytest -q (after normalize + PTT removal, before new file)          → 4061 passed, 9 skipped — no existing test pinned punctuation sensitivity
pytest -q (final)                                                   → 4067 passed, 9 skipped, 0 failed (+6)
```

## 4. Remaining risks / notes

- **Widened Skill triggers (Engineer-confirmed).** STT `Armar.` now arms the **software** latch exactly like typed `armar` (still no ESC/motor path; Safety gate unchanged). Typed text with trailing punctuation behaves the same way in `--chat`.
- `IntentResolver._normalize_text` (core, used for non-Skill-first routing) was **not** touched — out of lock; only the two named normalizers changed.
- Not live-tested with whisper; acceptance §3 (say `completo` / `estado`) is the Engineer's smoke.
