# Implementation Report — Voice Continuity brief Spanish (`B1-assistant-voice-brief-spanish`, T51)

**Project:** Jarvis
**Date:** 2026-10-05
**Implementer:** Claude Code (Engineer paste)
**Contract:** [`implementation_contract_assistant_voice_brief_spanish_b1.md`](implementation_contract_assistant_voice_brief_spanish_b1.md)
**Parents:** [FN-017](engineer_note_voice_spoken_polish_field_fn017.md) · [T50 ★](implementation_review_assistant_voice_speak_sanitize_b1.md) @ `v0.7.7` · [T45 ★](implementation_review_assistant_chat_spoken_continuity_b1.md)
**Status:** **Cursor PASS WITH NOTES** — [review](implementation_review_assistant_voice_brief_spanish_b1.md) · await Engineer ACCEPT → tag **`v0.7.8`**.
**Package / tag:** `0.7.8` / pending **`v0.7.8`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/adapters/voice/spoken_continuity.py` | `brief_spoken_continuity` keeps the exact same five fields/order as T45 (`situation` · `next_useful_step` · humanized `next_useful_why` · project-status phrase · top gap title). Only the words spoken for the last two change: `readiness.overall == "ASSEMBLY_READY"` now speaks `"Estado del proyecto: listo para ensamblar"`, anything else speaks `"Estado del proyecto: no listo para ensamblar"` — the English `PROJECT STATUS:`/`ASSEMBLY READY` strings are never spoken on this path. The top gap title is looked up in a new finite dict, `_GAP_TITLE_SPEAK_MAP` (the five IC-locked pairs: `Autonomy target not met`→`Objetivo de autonomía no alcanzado`, `Mass limit exceeded`→`Límite de masa superado`, `Parameters blocking simulation`→`Parámetros bloquean la simulación`, `Simulation not PASS`→`Simulación no en PASS`, `Architecture block incomplete`→`Bloque de arquitectura incompleto`); a title not in the map is spoken unchanged — honesty over inventing a translation |
| `src/jarvis/adapters/voice/speak_sanitize.py` | T50-N1: the `C-rate`/`c-rate` glossary now resolves to `"la tasa C"` in every case. A new regex (`_C_RATE_WITH_ARTICLE_RE`) matches a preceding `El`/`La` article plus the term together and replaces both with `"la tasa C"` in one substitution, applied *before* the bare-term regex — so `"El C-rate"` becomes `"la tasa C"`, never `"El la tasa C"` or `"El tasa C"` |
| `src/jarvis/adapters/voice/external_tts.py` | T50-N2: the module docstring's "Vendor choice" paragraph no longer names `en_GB` as the default — it now says the Piper default is Spanish `es_ES-davefx-medium` (since T49), with `en_GB-alan-medium` noted as the supported legacy value |
| `tests/test_assistant_voice_brief_spanish_b1.py` | **new** T1–T6 |
| `tests/test_assistant_chat_spoken_continuity_b1.py` | **fixed** — two T45 tests' assertions updated for the locked status-phrase/gap-title change (§2) |
| `tests/test_assistant_voice_speak_sanitize_b1.py` | **fixed** — T2's glossary assertions updated from bare `"tasa C"` to `"la tasa C"`, plus two new negative assertions that `"El tasa C"`/`"el tasa C"` never appear (§2) |
| `docs/USER_GUIDE_VOICE.md` | §4.1 bullet rewritten to describe the Spanish brief status phrase and gap-title map; §8's T50 bullet updated to `"la tasa C"` and clarified that FULL/print stay English |
| `pyproject.toml` | `0.7.7` → **`0.7.8`** — no new dependency |
| `docs/PLATFORM_CAPABILITY_VISION.md` | new T51 paragraph; T50's own paragraph updated to ★ ACCEPT CLOSED wording and `"la tasa C"` (cheap, same-file fix while already here) |
| `docs/system_map/CONNECTIONS.md` | new T51 paragraph; T50's own paragraph updated the same way |
| `.jes/artifacts/engineer_note_voice_spoken_polish_field_fn017.md` | T51 row → Implemented; T50-N1/N2 rows marked **Done** |
| Docs / cola / state | `engineer_note_voice_phase_c_cola.md` T51 row · `IMPLEMENTATION_TASKS.md` PRIORIDAD/cola rows · `engineering_state.json` · this IC's status line |

**Not touched (as the IC asked):** `adapters/cli/main.py`/`run_chat` — zero edits, confirmed by T6's structural guard check. `render_startup_context`, `render_response`, and the readiness block (`_render_readiness_block`) — zero edits, confirmed by T5 against the *real* renderer (not just a source-inspection check). `engineering_readiness`'s own gap-title strings — unchanged; only what the brief *speaks* for an already-selected title changes. No `orchestrator.py` change. No LLM import anywhere.

---

## 2. Two pre-existing test files updated — intentional, locked behavior changes

**`tests/test_assistant_chat_spoken_continuity_b1.py` (T45).** Two tests asserted the brief's literal pre-T51 output:
- `test_t1_brief_spoken_continuity_excludes_wall_detail` checked `"PROJECT STATUS: NOT ASSEMBLY READY" in brief` and `"Simulation not PASS" in brief` (its synthetic fixture's gap title happens to be exactly one of the five IC-locked titles). Updated to assert `"Estado del proyecto: no listo para ensamblar" in brief`, `"PROJECT STATUS" not in brief`, and `"Simulación no en PASS" in brief`.
- `test_t2_chat_wall_prints_full_but_speaks_brief` asserted the fake-TTS captures contained `"PROJECT STATUS: NOT ASSEMBLY READY"` (both as a presence check and a `>= 2` count check across the two wall turns). Updated both to `"Estado del proyecto: no listo para ensamblar"`.

Both are exactly the behavior this Buy was asked to ship — the IC's own lock 3 requires the brief to *never* speak the English `PROJECT STATUS`/`ASSEMBLY READY` strings. Re-ran the full file after the fix: 7 passed.

**`tests/test_assistant_voice_speak_sanitize_b1.py` (T50).** `test_t2_c_rate_glossary_case_insensitive_word_bounded` asserted bare `"tasa C"` substitutions (`"El C-rate..."` → `"El tasa C..."`, etc.) — exactly the awkward shape T50-N1 flagged as a review note. Updated every assertion to the new `"la tasa C"` target, added a `"La c-rate es alta"` case and two explicit negative assertions (`"El tasa C" not in ...`, `"el tasa C" not in ...`). Re-ran the full file: 9 passed.

Both fixes are the *intended* outcome of this Buy's own locks (3 and 5), not incidental breakage — re-confirmed by grepping the rest of the test suite for any other reference to the old brief/glossary wording (`grep -rln "tasa C\|brief_spoken_continuity\|PROJECT STATUS" tests/*.py`) and checking each hit: only these two files and the two files this Buy itself added/already-fixed-in-T50 (`test_assistant_voice_v1_checkpoint_b1.py`, which already uses `sanitize_for_speech(egress)` as its own oracle and needed no change) referenced it. Two other files (`test_block_closure_prop_energy.py`, `test_engineering_readiness_cli.py`) mention `PROJECT STATUS` but only on the print/readiness-block side, confirmed unrelated by grepping for any `brief_spoken_continuity`/`sanitize_for_speech` call in them (none found).

---

## 3. Design notes

- **Why the gap-title map lives as a plain dict, not a function.** The IC's lock 4 is explicitly a *finite* map — a dict literal makes "this is the whole set" visually obvious and `dict.get(title, title)` is the simplest possible honest-passthrough shape (unknown key → the key itself, never a KeyError, never an invented string).
- **Why the article-absorption regex runs before the bare-term regex.** Applying them in the other order would let the bare-term regex fire first (turning `"El C-rate"` into `"El la tasa C"`), and the article-absorption regex would then have nothing left to match (`"la tasa C"` doesn't contain `"c-rate"` anymore). Running the more specific pattern first and the general one second is the only order that produces the locked result.
- **Why T5 renders through the real `_render_readiness_block` instead of just checking `spoken_continuity.py`'s imports.** T50's own T6 already proved the *absence* of a reference from the renderers to the sanitizer; this Buy's T5 additionally proves the *presence* of the untouched English string in what the real renderer actually produces today, so a future accidental edit to `_render_readiness_block` that happened to remove the English line would be caught here even though it wouldn't violate the "no import" check.

---

## 4. Tests executed

```text
pytest tests/test_assistant_voice_brief_spanish_b1.py -v
→ 6 passed (T1-T6)

pytest tests/test_assistant_chat_spoken_continuity_b1.py tests/test_assistant_voice_speak_sanitize_b1.py -q
→ 16 passed (7 + 9, including the two fixed assertions each)

pytest -q
→ 4045 passed, 9 skipped, 0 failed
```

Diffed against this session's pre-T51 tip (T50 ★ ACCEPT CLOSED, before this Buy's edits): baseline was `4039 passed, 9 skipped, 0 failed`. **Net delta: +6** — the 6 new T51 tests, zero regressions beyond the two documented, intentional test fixes (§2).

---

## 5. Remaining

None for this Buy. Out of scope per the IC (unchanged): T52's FULL narrated rewrite (the FULL phrase path still speaks the printed wall verbatim, pre-T52), expanding the gap-title map beyond the five locked pairs (its own future IC), rewriting `engineering_readiness`'s own title strings, any LLM involvement, wake-word/always-on, T40. The Field Note this Buy advances (FN-017) still has T52-DC/T52 queued next.
