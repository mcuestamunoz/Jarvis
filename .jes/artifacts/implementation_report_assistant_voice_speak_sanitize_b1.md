# Implementation Report — Voice speak-path sanitize (`B1-assistant-voice-speak-sanitize`, T50)

**Project:** Jarvis
**Date:** 2026-10-05
**Implementer:** Claude Code (Engineer paste)
**Contract:** [`implementation_contract_assistant_voice_speak_sanitize_b1.md`](implementation_contract_assistant_voice_speak_sanitize_b1.md)
**Parents:** [Field Note FN-017](engineer_note_voice_spoken_polish_field_fn017.md) (Engineer live smoke) · [T45 ★](implementation_review_assistant_chat_spoken_continuity_b1.md) · [T49 ★](implementation_review_assistant_voice_tts_spanish_b1.md) @ `v0.7.6`
**Status:** **Implemented** — await Cursor review → Engineer ACCEPT → tag **`v0.7.7`**.
**Package / tag:** `0.7.7` / pending **`v0.7.7`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/adapters/voice/speak_sanitize.py` | **new.** `sanitize_for_speech(text: str) -> str` — a pure, no-LLM transform: drops lines made entirely of rule/separator glyphs (light/heavy box-drawing `─`/`━`, ASCII `-`, `=`, `_`, 3+ repeated); strips leading `•`/`*`/`✓`/`◇`/`└`/`├`/`│`/`─`/`━` decoration (repeated groups, each with its own trailing whitespace, so a tree combo like `├── ` or `│   └ ` strips in one pass) from the start of each line — note the **ASCII hyphen is deliberately excluded** from this leading set (only from the whole-rule-line set above), so a line starting `-5kg margen` or a markdown dash-bullet keeps its leading character untouched; strips a trailing footnote-marker asterisk run only when preceded by whitespace or when it is the whole trailing token (never an asterisk glued onto a word, e.g. `100%*` is left alone); collapses runs of blank lines to one; applies exactly one glossary substitution, `\bc-rate\b` (case-insensitive) → `"tasa C"`. Returns `""` when nothing is left to say |
| `src/jarvis/adapters/voice/external_tts.py` | `speak_egress` now calls `sanitize_for_speech(text)` first and, when the result is empty, returns immediately — no external command invoked, no `TtsConfigError`/`TtsProcessError`, no filler speech. When non-empty, the *sanitized* string (not the raw `text`) is what travels to `subprocess.run`'s stdin |
| `src/jarvis/adapters/voice/__init__.py` | re-exports `sanitize_for_speech`; also fixed a stale module-docstring line that still named Piper `en_GB` as the package's default voice (pre-dating T49) — now names the current Spanish `es_ES-davefx-medium` default with `en_GB-alan-medium` noted as the supported legacy value |
| `tests/test_assistant_voice_speak_sanitize_b1.py` | **new** T1–T6 (9 test functions — T1 split three ways for the base/footnote/heavy-rule-and-tree-glyph cases, T4 split in two for the pure-function and `speak_egress`-level empty-noop cases) |
| `tests/test_assistant_voice_v1_checkpoint_b1.py` | **fixed** — T2's assertion updated for the locked `C-rate` glossary change (§2) |
| `tests/test_assistant_voice_tts_spanish_b1.py` | **fixed** — T4's literal `0.7.6` tip-version-pin assertion removed, a pre-existing policy violation from T49 this version bump surfaced (§3b) |
| `docs/USER_GUIDE_VOICE.md` | §8 gained one bullet describing the speak-path cleanup (what gets stripped, the one glossary term, and the empty-after-sanitize honesty rule) |
| `pyproject.toml` | `0.7.6` → **`0.7.7`** — no new dependency |
| `docs/PLATFORM_CAPABILITY_VISION.md` | short T50 paragraph, no new C-xxx |
| `docs/system_map/CONNECTIONS.md` | short T50 paragraph, no new C-xxx |
| `.jes/artifacts/engineer_note_voice_spoken_polish_field_fn017.md` | status line updated to **Implemented** — this Field Note (Cursor, from Engineer live smoke on project `dron-de-vigilancia-doméstico`) already existed before this Buy; not created by this report |
| Docs / cola / state | `engineer_note_voice_phase_c_cola.md` T50 row · `IMPLEMENTATION_TASKS.md` PRIORIDAD/cola row · `engineering_state.json` |

**Not touched (as the IC asked):** `src/jarvis/adapters/cli/main.py` (zero edits — `speak_egress` is the one seam both `_chat_speak_fn` and `_voice_speak_fn` already call through, so no `main.py` change was needed to cover `--chat --voice-speak` **and** `--voice`/`--voice-fixture`/`--voice-audio`), `spoken_continuity.py`, `render_startup_context`, `render_response` — confirmed by T6's structural check that none of them reference `speak_sanitize`/`sanitize_for_speech`. No `orchestrator.py` change. No LLM import anywhere in the new module.

---

## 2. One pre-existing test updated — an intentional, locked behavior change

`tests/test_assistant_voice_v1_checkpoint_b1.py::test_t2_twelve_skills_speak_wired_fake_tts_records_every_egress` (T39) asserted, for all twelve Skill-first phrases, that the exact raw egress string appears verbatim in what the fake TTS script received — encoding the pre-T50 invariant "spoken == printed, byte for byte." The `explain c-rate-de-bateria` turn's egress contains the literal substring `C-rate` (the ontology note's title and body), so this Buy's locked glossary substitution (`C-rate` → `"tasa C"`) made that one turn's raw egress no longer appear in the sanitized TTS input — the test failed on first run after wiring the sanitizer.

This is exactly the behavior T50 was asked to ship, not a regression: the IC explicitly locks `C-rate`/`c-rate` → `"tasa C"` for the spoken side while leaving the printed side (including this same ontology note, as `jarvis explain` output) completely untouched. I updated the test's assertion from `assert egress in received` to `assert sanitize_for_speech(egress) in received`, with a comment explaining why — this is a no-op change for the other eleven Skills (none contain the glossary term or any decoration glyph) and correctly reflects the new, intended behavior for the twelfth. Full suite re-run confirmed this was the only test affected across the entire codebase.

---

## 3. Design notes

- **Footnote-asterisk precision.** The real pattern in the codebase (`_render_readiness_block`, `main.py`) is `f"{label:<14} {verdict} *"` — always preceded by a space. The regex requires that space (or line-start) before the asterisk run, so a value like `100%*` (no space) is never touched — only named here because a looser "strip any trailing `*`" rule would have been a plausible first guess and would have over-matched.
- **Why the ASCII hyphen is split across two different rules.** The IC's own decoration lock puts `-` only in the whole-rule-line set (a line of nothing but hyphens, 3+ in a row, is pure decoration) and explicitly leaves it out of the leading-marker set. Tried the more aggressive "strip a leading `-` too" version first and it broke on exactly the case the IC was guarding against: a printed line like `-5kg margen` or a plain markdown dash-bullet would lose its leading character, changing a negative number's sign or silently eating a real bullet dash. `─`/`━` (Unicode box-drawing) carry no such risk — they never appear as literal content in spoken Spanish text — so both are included in the leading-marker set, letting a tree combo like `├── ` or `│   └ ` strip in one pass via a repeated-group regex (`(?:[glyph][ \t]*)+`) rather than a single flat character class, which could only consume one glyph before being blocked by the whitespace between a tree connector and its branch character.
- **Why `speak_sanitize.py` lives as its own module rather than inside `external_tts.py`.** The sanitizer has zero dependency on the TTS process seam (no subprocess, no env var) and is independently unit-testable; `external_tts.py` imports it as a one-line dependency, matching the existing pattern where `adapters/voice/__init__.py` re-exports every seam's public symbols from its own file.
- **Glossary scope discipline.** Only `C-rate`/`c-rate` is substituted, word-bounded (`\bc-rate\b`) so it can never match inside a longer token. `PROJECT STATUS`, `PASS`, and gap titles are explicitly asserted untouched by T3 — this Buy does not open the door to a general spoken-rewrite rule.

---

## 3b. A second pre-existing test fixed — a real tip-version-pin bug uncovered by this bump

Bumping `pyproject.toml` to `0.7.7` broke `tests/test_assistant_voice_tts_spanish_b1.py::test_t4_package_version_and_no_speech_deps_or_tip_pinned_models` (from **T49**, landed earlier this session): it asserted `'version = "0.7.6"' in pyproject_text` — a literal tip-version pin, which this repo has an explicit standing policy against (`tests/test_suite_no_tip_version_pins_b1.py`'s own docstring: *"do not assert live tip / package version from the suite"*). That guard test's regex happens not to catch this exact quoting shape (a version pin wrapped in an outer single-quoted string), so it slipped through T49 unnoticed by either the automated guard or review. Fixed by removing the version assertion entirely (renamed to `test_t4_no_speech_deps_or_tip_pinned_models`) rather than bumping the expected string to `0.7.7`, which would only recreate the same break on the next voice Buy. Re-scanned every other test file for the same shape (`grep -rn 'version = "0\.' tests/*.py`) — no other offender found.

---

## 4. Tests executed

```text
pytest tests/test_assistant_voice_speak_sanitize_b1.py -v
→ 9 passed (T1, T1b, T1c, T2, T3, T4, T4b, T5, T6)

pytest tests/test_assistant_voice_v1_checkpoint_b1.py -q
→ 5 passed (T39's own suite, including the updated T2)

pytest -q
→ 4039 passed, 9 skipped, 0 failed
```

Diffed against this session's pre-T50 tip (T41–T49 ★ ACCEPT CLOSED, before this Buy's edits): baseline was `4030 passed, 9 skipped, 0 failed`. **Net delta: +9** — the 9 new T50 tests, zero regressions, one pre-existing test's assertion updated to match the Buy's own locked behavior change (documented in §2 above, not hidden), one pre-existing tip-version-pin bug fixed (§3b).

---

## 5. Remaining

None for this Buy. Out of scope per the IC (unchanged): any rewrite of `PROJECT STATUS`/`PASS`/gap titles (explicitly deferred to a future Buy, T51/T52 per the paste), any further glossary term beyond `C-rate`, any LLM involvement, wake-word/always-on, T40. The Field Note this Buy closes (FN-017) notes that any further spoken-polish observation should open its own new field note rather than reopening this Buy's locked scope.
