# Implementation Report — Chat spoken continuity (`B1-assistant-chat-spoken-continuity`, T45)

**Project:** Jarvis
**Date:** 2026-10-04
**Implementer:** Claude Code (Engineer paste)
**Contract:** [`implementation_contract_assistant_chat_spoken_continuity_b1.md`](implementation_contract_assistant_chat_spoken_continuity_b1.md)
**Parents:** [T44-DC](design_contract_assistant_chat_spoken_continuity_b0.md) · [T44-inv review](investigation_review_assistant_chat_spoken_continuity_b0.md) · [living map](engineer_note_chat_spoken_continuity_map.md) · [T43](implementation_review_assistant_chat_voice_speak_b1.md) @ `0.7.3`
**Status:** **Implemented** (Claude Code) — await Cursor review → Engineer ACCEPT → tag **`v0.7.4`**.
**Package / tag:** `0.7.4` / pending **`v0.7.4`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/adapters/voice/spoken_continuity.py` | **new.** `brief_spoken_continuity(ctx)` — pure extract of `continuity.situation`/`next_useful_step`/humanized `next_useful_why` (reusing `main.py::_humanize_next_useful_why` via a local import)/`readiness.overall` (as a `PROJECT STATUS: …` phrase)/`readiness.prioritized_gaps[0].title`, newline-joined, each piece omitted when absent, `""` when there's no active project. `is_full_continuity_request(raw_text)` — exact match against the locked ten-phrase FULL set, using a locally reimplemented minimal normalize (same algorithm as `assistant_task._normalize_for_continuity_match`, not imported, mirroring that module's own documented reason for not crossing its DC/IC fence). `spoken_text_for_wall(raw_text, printed_wall, ctx)` — the combinator: full `printed_wall` on a FULL-phrase match, else the brief |
| `src/jarvis/adapters/voice/__init__.py` | re-exports `FULL_CONTINUITY_PHRASES`/`brief_spoken_continuity`/`is_full_continuity_request`/`spoken_text_for_wall` |
| `src/jarvis/adapters/cli/main.py` | `run_chat` now locally imports `spoken_text_for_wall` and calls it on its **two** Continuity-wall sites — the project-load `startup_block` print, and the main-turn-success branch whenever `result["action"] == "project_status"` (restructured from a single `_say(render_response(result))` into an explicit `print(...)` + a conditional `speak(...)` so the print stays identical while only the speak target can differ). Every other `_say` call site (exit, help, startup error, define-wizard opener, no-project fallback, exception handler, main-turn error, every non-`project_status` success) is untouched |
| `src/jarvis/config.py` | three new entries in `CONTINUITY_DEFER_PHRASES` — `completo`, `estado completo`, `cuentame todo` — the other seven locked FULL phrases were already members. Without this, those three phrases would never resolve to `action == "project_status"` at all (they'd fall through to classify/LLM), so "speak the wall on `completo`" would have nothing to attach to |
| `docs/USER_GUIDE_VOICE.md` | §4.1 rewritten to describe the shipped brief-vs-full split (screen always full; ear brief by default; the ten FULL phrases listed verbatim); §8's "`estado` es largo" bullet updated from "hasta entonces" framing to describe the shipped behavior |
| `.jes/artifacts/engineer_note_chat_spoken_continuity_map.md` | classifications updated from "when it ships" to shipped reality; the two wall rows in Table 1 now describe the print/speak split explicitly; added the shipped extractor's symbol citations and the three new `CONTINUITY_DEFER_PHRASES` entries |
| `tests/test_assistant_chat_spoken_continuity_b1.py` | **new** T1–T6 |
| `pyproject.toml` | `0.7.3` → **`0.7.4`** — no new dependency |
| Docs / cola / state | PRIORIDAD · cola note T45 row · PLATFORM · CONNECTIONS (no new C-xxx) · IC status line · `engineering_state.json` |

**Not touched:** `render_startup_context`/`render_response` (Layer 1 stays byte-identical — verified by `test_t2`/`test_t3` asserting the full wall is still on screen on every wall turn), `project_continuity.py`'s ranking, `orchestrator.py`'s Continuity computation, `_voice_speak_fn`/`run_voice_interactive`/`run_voice_fixture`/`run_voice_audio` (T38/T42, reused/left exactly as shipped), `AuthoritySource` (still no `"voice"`), `pyproject.toml`'s dependency lists, tip-version pins (T17 green), ESC fence (T16, re-verified including the new `spoken_continuity.py` file).

---

## 2. Why `CONTINUITY_DEFER_PHRASES` needed three new entries

The IC's locked FULL set includes `completo`, `estado completo`, and `cuentame todo` — but checking the existing `CONTINUITY_DEFER_PHRASES` frozenset (`jarvis/config.py`) before writing any code showed only seven of the ten FULL phrases were already members (`dame detalles`, `dame detalles del proyecto`, `detalles del proyecto`, `cuentame el proyecto`, `cuenta el proyecto`, `describe el proyecto`, `explica el proyecto`). The other three were not recognized as Continuity-defer phrases at all, meaning typing bare `completo` would never produce `action == "project_status"` — it would fall through to classify/LLM, and the IC's own T3 acceptance ("print still full" when the line is `completo`) would be unreachable. Added exactly those three literal strings, with a comment explaining why, verified no existing test asserts an exact size or exhaustive-membership count on that frozenset (only specific-phrase membership checks), and re-ran `tests/test_assistant_defer_continuity_b1.py` to confirm nothing broke.

---

## 3. Proving print ≠ speak on a wall (not just unit-testing the extractor)

`brief_spoken_continuity` is unit-tested directly (T1) against a synthetic "fat" `ctx`, but the IC's own T2 note flagged that proving the *real* separation needs more than that: a real `run_chat()` call must show the full wall on screen while the fake-TTS process receives only the brief. T2/T3 seed a real project via `JarvisOrchestrator.handle({"action": "create_project", ...})` (bypassing the interactive wizard), isolate the workspace by monkeypatching `jarvis.workspace.workspace_manager.DEFAULT_WORKSPACE_ROOT` (same technique T43's own test file established, since `run_chat()` takes no `workspace_root`), and then:

- T2: feed `["1", "estado", "exit"]` with a fake `JARVIS_TTS_CMD` script, `speak_tts=True`. `capsys` confirms `ENGINEERING READINESS`/`TOP GAPS` are still printed. The fake TTS's received captures (project-load + `estado`, plus the auto-define wizard opener that fires between them as a non-wall, speak-as-printed turn) **never** contain `ENGINEERING READINESS`/`Componentes / gaps`/`Evidencia:`, and at least two of them contain `PROJECT STATUS: NOT ASSEMBLY READY` (the brief's own status line).
- T3/T3b: same seed, but the second typed line is `completo` / `dame detalles`. `capsys` still shows the full wall (print is identical either way). Exactly one fake-TTS capture contains `ENGINEERING READINESS`/`TOP GAPS` — the `completo`/`dame detalles` turn, and only that turn.

Both were also run manually against the real CLI entry point (fake TTS shell script + monkeypatched stdin) before being written as pytest assertions — the same "prove it with Bash first" discipline every prior voice Buy in this chain used, which is how the auto-define-wizard interaction (an extra non-wall capture landing between the two wall captures) was caught and the tests written to assert on content rather than a fixed capture index.

---

## 4. Tests executed

```text
pytest tests/test_assistant_chat_spoken_continuity_b1.py -q
→ 7 passed (T1-T6, with T3 split into T3/T3b for the two distinct FULL phrases)

pytest tests/test_assistant_chat_spoken_continuity_b1.py tests/test_assistant_chat_voice_speak_b1.py \
       tests/test_assistant_voice_interactive_cli_b1.py tests/test_assistant_voice_demo_ready_b1.py \
       tests/test_assistant_defer_continuity_b1.py tests/test_project_coherence.py -q
→ 52 passed (T45's own 7 + T43's 5 + T42's 5 + T41's 8 + continuity-defer + coherence suites —
  zero retargeting needed on any sibling file, confirming the 3 new CONTINUITY_DEFER_PHRASES
  entries and the run_chat restructuring broke nothing)

pytest tests/test_fase_c_esc_pwm_stub_rung_b1.py tests/test_suite_no_tip_version_pins_b1.py -q
→ 19 passed (T16 ESC fence + T17 tip-pin guardrail both still green, including the new
  spoken_continuity.py file)

pytest tests/ -q
→ 4016 passed, 9 skipped, 0 failed
```

Diffed against this branch's pre-T45 tip (`git stash push -u` / `pop`): baseline was `4009 passed, 9 skipped, 0 failed`. **Zero regressions** — the only delta is the 7 new T45 tests passing, same skip count. `git status` before committing shows exactly the files the IC's own file list names, plus the usual docs/state.

---

## 5. Remaining

None for this Buy. Flagged (not implemented) per the IC's own "out unless a later IC ★" list: craft `coherence_footer`/reasoning-without-footer brief extraction if live use proves those too long as well — explicitly a separate future IC, not T45. Next steps are the Engineer's: Cursor review, and whether ACCEPT for T41–T45 gets bundled or tagged individually.
