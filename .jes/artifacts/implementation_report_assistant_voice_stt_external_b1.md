# Implementation Report — Assistant voice STT external (`B1-assistant-voice-stt-external`, T37)

**Project:** Jarvis  
**Date:** 2026-10-03  
**Implementer:** Claude Code (Engineer paste)  
**Contract:** [`implementation_contract_assistant_voice_stt_external_b1.md`](implementation_contract_assistant_voice_stt_external_b1.md)  
**Parents:** [DC voice/channels ★ CLOSED](design_contract_assistant_chat_voice_channels_b0.md) · [T36 ★ ACCEPT CLOSED](implementation_review_assistant_voice_fixture_loop_b1.md) @ `v0.6.44` · [cola note](engineer_note_voice_phase_c_cola.md)  
**Status:** **Implemented** (Claude Code) — await Cursor review → Engineer ★ ACCEPT.  
**Package / tag:** `0.6.45` / pending **`v0.6.45`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/adapters/voice/external_stt.py` | **new** — `transcribe_audio_file(audio_path, *, command_template=None, env_var="JARVIS_STT_CMD")`: resolves a command template (explicit arg, else the `JARVIS_STT_CMD` env var), substitutes `{audio}` with the path, runs it via `subprocess.run` (argv list, no shell), and returns stripped stdout. Typed failure family: `SttError` (base) → `SttConfigError` (missing/empty template), `SttProcessError` (non-zero exit **or** the binary itself not found/runnable), `SttEmptyTranscriptError` (exit `0` but blank stdout) — never a silent fixture fallback. `run_voice_turn_from_audio(orchestrator, llm, audio_path, ...)` calls `transcribe_audio_file` then hands the transcript to T36's existing `run_voice_turn` unchanged |
| `src/jarvis/adapters/voice/__init__.py` | re-exports the new STT symbols alongside T36's `FixtureSttSource`/`run_voice`/`run_voice_turn` |
| `src/jarvis/adapters/cli/main.py` | new `run_voice_audio(audio_path)` helper (constructs orchestrator/LLM, calls `run_voice_turn_from_audio`, prints the egress; catches `SttError` and prints an honest "STT no disponible: …" message instead of a raw traceback); `main()` gained an optional `--voice-audio PATH` argument, checked **before** `--voice-fixture`/`--chat` in the dispatch chain; both of those stay byte-unchanged |
| `tests/test_assistant_voice_stt_external_b1.py` | **new** T1–T5 (+ one extra class-hierarchy sanity check) |
| `pyproject.toml` | `0.6.45` — **no** new dependency added |
| Docs / cola note / connect-plugs `a4-voice-world` | PRIORIDAD · PLATFORM · CONNECTIONS (no new C-xxx); cola note's T37 row → Implemented; connect-plugs `a4-voice-world` pointer advanced to mention T37 (no row marked CLOSED) |

**Not touched:** `orchestrator.py` (not required — `run_voice_turn` from T36 already does the `source=VOICE` wiring; this Buy only produces the transcript string that feeds it), `run_skill`/`skills_runtime.py`, any `_handle_*` fulfill method, `fixture_loop.py` (untouched — `FixtureSttSource`/`--voice-fixture` still work exactly as before, regression-tested), `RadioIntentAdapter`/`ApiIntentAdapter`, `AuthoritySignal`/`AuthoritySource` (no `"voice"` literal), `capabilities/`/`intelligence/`/`core/` (no audio decode anywhere in those — the external process owns all of that), no speech package added to `pyproject.toml`'s dependencies, no vendor (Whisper/Vosk/cloud) hardcoded anywhere, tip-version pins (T17 guardrail re-verified green), ESC fence (T16, re-verified green on `orchestrator.py` and both new/changed `adapters/` files).

---

## 2. A test-fixture bug caught before it shipped (not a product regression)

My first draft of test T3's "empty stdout" fixture script used `echo -n ''` inside a `#!/bin/sh` script. On this machine's `/bin/sh`, the `echo` builtin does not support `-n` as a flag — it prints the literal string `-n ` followed by a newline instead of suppressing it, so the fixture never actually produced empty output and the test failed with "DID NOT RAISE `SttEmptyTranscriptError`". This was a bug in my own test fixture, not in `transcribe_audio_file`: fixed by using `printf ''` instead (POSIX-portable, no flag parsing ambiguity), re-verified the test raises `SttEmptyTranscriptError` correctly, and reran the full suite.

---

## 3. Behavior

- `transcribe_audio_file(path, command_template="<fake_script> {audio}")` with a script that echoes `"hold"` returns `"hold"` exactly (T1).
- No `JARVIS_STT_CMD` set and no explicit `command_template` → `SttConfigError`; an explicit empty-string template → the same (T2).
- A script that exits non-zero, a script that produces zero stdout bytes (exit `0`), and a command naming a binary that doesn't exist at all each raise a distinct typed error (`SttProcessError`/`SttEmptyTranscriptError`/`SttProcessError`) — never an invented Skill phrase, never a crash with a raw traceback (T3; the "binary doesn't exist" case was verified manually via a smoke test before formalizing, confirming `subprocess.run`'s `OSError` is caught and re-raised as `SttProcessError`).
- `run_voice_turn_from_audio` wired to the fake-STT script, on a disarmed orchestrator: `result["action"] == "vehicle_hold"`, honest `"disarmed"` reject, non-empty `egress`; spying on `VoiceIntentAdapter.parse` confirms the transcript ("hold") reached classify tagged `source=VOICE` (T4).
- `python -m jarvis.main --voice-audio <path>` works end-to-end from the real CLI entrypoint (smoke-tested manually, three scenarios: successful fake-STT transcription, missing `JARVIS_STT_CMD` → honest printed message, and `--voice-fixture` still working unchanged in the same session).
- `--chat` works with zero `JARVIS_STT_CMD` configured (it never looks at that env var at all); `FixtureSttSource`/`run_voice` (T36) are untouched and still pass their own full test suite (T5).
- No speech package appears in `pyproject.toml`; no `"voice"` member exists on `AuthoritySource`.

---

## 4. Tests executed

```text
pytest tests/test_assistant_voice_stt_external_b1.py \
  tests/test_assistant_voice_fixture_loop_b1.py \
  tests/test_assistant_voice_intent_ingress_b1.py \
  tests/test_fase_c_intent_safety_stub_b1.py \
  tests/test_fase_c_radio_dual_role_b1.py -q
→ 44 passed

pytest tests/test_suite_no_tip_version_pins_b1.py tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 19 passed (T17 guardrail + T16 ESC fence both still green)

pytest tests/ -q
→ 3980 passed, 9 skipped, 0 failed
```

Diffed against this branch's pre-T37 tip (stash push/pop): baseline was `3974 passed, 9 skipped, 0 failed`. **Zero regressions** — the only delta is the 6 new T37 tests passing.

---

## 5. Remaining

None for this Buy. Next candidate per the voice phase C cola: **T38** `B1-assistant-voice-tts-external` (V4) — wires a real external TTS process onto `render_response`'s output, independent of T37 and may land before or after it (both only depend on T36). T39 (voice v1 product milestone, opens `v0.7.0`) remains blocked on both T37 and T38 ★ ACCEPT; T40 (craft/world, explicitly out of voice v1) remains Parked. Picking a real STT vendor/binary to point `JARVIS_STT_CMD` at is explicitly a separate, later Engineer ★ — not part of this Buy.
