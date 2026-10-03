# Implementation Report — Assistant voice fixture loop (`B1-assistant-voice-fixture-loop`, T36)

**Project:** Jarvis  
**Date:** 2026-10-03  
**Implementer:** Claude Code (Engineer paste)  
**Contract:** [`implementation_contract_assistant_voice_fixture_loop_b1.md`](implementation_contract_assistant_voice_fixture_loop_b1.md)  
**Parents:** [DC voice/channels ★ CLOSED](design_contract_assistant_chat_voice_channels_b0.md) · [T35 ★ ACCEPT CLOSED](implementation_review_assistant_voice_intent_ingress_b1.md) @ `v0.6.43` · [cola note](engineer_note_voice_phase_c_cola.md)  
**Status:** **★ ACCEPT CLOSED** (Engineer 2026-10-03) — Cursor **PASS WITH NOTES**.  
**Package / tag:** `0.6.44` / **`v0.6.44`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/adapters/voice/__init__.py` | **new** — package docstring + re-export of `FixtureSttSource`, `run_voice_turn`, `run_voice` |
| `src/jarvis/adapters/voice/fixture_loop.py` | **new** — `FixtureSttSource` (plain-text stand-in for "what STT produced," same discipline as C5's `RadioStubFrame`; `from_lines`/`from_path` constructors); `run_voice_turn(orchestrator, llm_interface, text)` (calls `orchestrator.handle_user_text(text, llm_interface, source=IntentSource.VOICE)` — T35's seam — then reuses `jarvis.adapters.cli.main.render_response` unchanged, returns `(result, egress)`); `run_voice(orchestrator, llm_interface, fixture, *, speak=None)` (loops a fixture iterable calling `run_voice_turn` per line, optional `speak` callback, returns every `(text, result, egress)` triple) |
| `src/jarvis/adapters/cli/main.py` | New `run_voice_fixture(fixture_path)` helper (constructs `JarvisOrchestrator`/`JarvisLLMInterface`, builds a `FixtureSttSource.from_path`, runs `run_voice` with `speak=lambda egress: print(f"Jarvis > {egress}")`). `main()` gained an optional `--voice-fixture PATH` argument, checked **before** `--chat` in the dispatch chain; `--chat`'s own code path is byte-unchanged |
| `tests/test_assistant_voice_fixture_loop_b1.py` | **new** T1–T5 |
| `pyproject.toml` | `0.6.44` |
| Docs / cola note / connect-plugs map | PRIORIDAD · PLATFORM · CONNECTIONS (no new C-xxx); cola note's T36 row → Implemented; connect-plugs `a4-voice-world` row pointer advanced to mention T36 (no row marked CLOSED — `voice-intent-ingress` stays as Cursor's own T35 ★ ACCEPT update left it, untouched by this Buy) |

**Not touched:** `orchestrator.py` (the IC's own preference — "touch only if a tiny public import/export is truly required (prefer not)" — T35's `handle_user_text(..., source=...)` seam was already sufficient, no change needed), `run_skill`/`skills_runtime.py`, any `_handle_*` fulfill method, `render_response`/`render_startup_context` (reused exactly as-is, no voice-tuned rewrite), `RadioIntentAdapter`/`ApiIntentAdapter` (still `NotImplementedError`), `AuthoritySignal`/`AuthoritySource` (no `"voice"` literal added), `world/` (still absent), tip-version pins (T17 guardrail re-verified green), ESC fence (T16, re-verified green on `orchestrator.py`, the new `adapters/voice/fixture_loop.py`, and `adapters/cli/main.py`).

---

## 2. A regression caught before it shipped

An existing Fase C fence test (`tests/test_fase_c_radio_dual_role_b1.py::test_t8_radio_not_imported_by_orchestrator_or_craft_paths`) does a blanket **substring** scan — not an AST/import check — over every `.py` file under `src/jarvis/core/` and `src/jarvis/adapters/`, forbidding the literal text `"capabilities.radio"` anywhere, including comments and docstrings. My first draft of `fixture_loop.py`'s module docstring referenced `` `jarvis.capabilities.radio` `` by its dotted path as a documentation analogy (comparing `FixtureSttSource` to C5's `RadioStubFrame`) — this tripped the fence even though there is no real import. Fixed by rephrasing the analogy ("C5's own `RadioStubFrame`") without spelling out the dotted module path; re-ran the fence test (green) and the full suite before proceeding.

---

## 3. Behavior

- `run_voice_turn(orch, llm, "hold")` on a disarmed orchestrator returns `(result, egress)` where `result["action"] == "vehicle_hold"`, `"disarmed"`/`"reject"` in `result["message"]`, and `egress` is the exact same non-empty string `render_response(result)` would have produced for a `TERMINAL` turn — only `Intent.source == VOICE` differs under the hood (verified via spying on `VoiceIntentAdapter.parse`/`TerminalIntentAdapter.parse`: only the former is called).
- A two-line fixture (`["armar", "hold"]`) through `run_voice` produces two turns; the second (`hold`) correctly observes the armed latch set by the first (`armar`) — same session-state behavior as `run_chat`, since both reuse the same `JarvisOrchestrator` instance and the same `handle_user_text` call.
- The optional `speak` callback receives each turn's rendered egress string, in order — the seam a later real-TTS Buy (T38) only needs to swap, not the loop or turn helper.
- `python -m jarvis.main --voice-fixture <path>` works end-to-end from the real CLI entrypoint (smoke-tested manually): prints `Jarvis > ...` for each fixture line, identical message shapes to `--chat`.
- `--chat` and MCP (`JarvisSessionManager.chat`) are unaffected — neither passes `source`, so both still default to `TERMINAL` (T35's own guarantee, re-verified here).
- `RadioIntentAdapter`/`ApiIntentAdapter` still always raise `NotImplementedError`; no `"voice"` member exists on `AuthoritySource`.

---

## 4. Tests executed

```text
pytest tests/test_assistant_voice_fixture_loop_b1.py \
  tests/test_assistant_voice_intent_ingress_b1.py \
  tests/test_fase_c_intent_safety_stub_b1.py \
  tests/test_assistant_chat_sim_copper_b1.py \
  tests/test_fase_c_radio_dual_role_b1.py -q
→ 45 passed

pytest tests/test_suite_no_tip_version_pins_b1.py tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 19 passed (T17 guardrail + T16 ESC fence both still green)

pytest tests/ -q
→ 3974 passed, 9 skipped, 0 failed
```

Diffed against this branch's pre-T36 tip (stash push/pop): baseline was `3968 passed, 9 skipped, 0 failed`. **Zero regressions** — the only delta is the 6 new T36 tests passing.

---

## 5. Remaining

None for this Buy. Next candidate per the voice phase C cola: **T37** `B1-assistant-voice-stt-external` (V3) — wires a real external STT into the same `VoiceIntentAdapter.parse(raw_text)` seam (vendor choice is its own, separate Engineer ★), blocked on this Buy's ★ ACCEPT. T38 (external TTS)/T39 (voice v1 product milestone, opens `v0.7.0`)/T40 (craft/world, explicitly out of voice v1) remain Parked.
