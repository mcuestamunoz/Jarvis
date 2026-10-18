# Implementation Report — Assistant voice interactive CLI (`B1-assistant-voice-interactive-cli`, T42)

**Project:** Jarvis  
**Date:** 2026-10-04  
**Implementer:** Claude Code (Engineer paste)  
**Contract:** [`implementation_contract_assistant_voice_interactive_cli_b1.md`](implementation_contract_assistant_voice_interactive_cli_b1.md)  
**Parents:** [T41](implementation_review_assistant_voice_demo_ready_b1.md) @ `0.7.1` (PASS WITH NOTES, live Piper fix) · [T39 ★](implementation_review_assistant_voice_v1_checkpoint_b1.md) @ `v0.7.0` · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md)  
**Status:** **Implemented** (Claude Code) — await Cursor review → Engineer ★ ACCEPT.  
**Package / tag:** `0.7.2` / pending **`v0.7.2`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/adapters/cli/main.py` | new `run_voice_interactive(*, workspace_root=None)` — a REPL: prompt → typed line → `run_voice_turn` (T36, tags `source=IntentSource.VOICE`) → `_voice_speak_fn(speak_tts=True)` (T38's existing print-then-speak helper, unchanged). `quit`/`salir`/EOF/Ctrl-C exit with a goodbye; a bad turn or a failed `speak_egress` call is caught and printed, never crashes the loop. New `--voice` boolean flag wired in `main()`, dispatched **before** `--voice-audio`/`--voice-fixture`/`--chat` |
| `docs/USER_GUIDE_VOICE.md` | restructured so **§4 leads with `--voice`** (the interactive path: install once in §2–3, then sit in the REPL) and `--voice-fixture`/`--voice-audio` move to **§5 "Modo batch / fixture — para pruebas, CI, o grabar sin estar delante"**. Section numbers 1/6/7/8 (`Qué es`/`Honestidad`/`Cheatsheet`/`Límites`) are unchanged — T41's own guide-presence test still passes unmodified |
| `tests/test_assistant_voice_interactive_cli_b1.py` | **new** T1–T5 |
| `pyproject.toml` | `0.7.1` → **`0.7.2`** — no new dependency |
| Docs / cola / state | PRIORIDAD · cola note T42 row + tip parent · PLATFORM · CONNECTIONS (no new C-xxx, plus a stale-status fix on T41's own entries — see §3) · `engineering_state.json` |

**Not touched:** `run_chat` (verified by source inspection, not just by "the flag is off by default" — see §2), `run_voice_fixture`/`run_voice_audio`/`_voice_speak_fn` (reused exactly as T38/T41 shipped), every `adapters/voice/*.py` file, `core/orchestrator.py`, `render_response`, `run_skill`, any `_handle_*` fulfill, `AuthoritySource` (still no `"voice"`), `pyproject.toml`'s dependency lists (no speech package — T5 asserts this), tip-version pins (T17 guardrail green), ESC fence (T16, re-verified on orchestrator + all voice adapters + `adapters/cli/main.py`).

---

## 2. Proving `--chat` truly never speaks

The IC's own lock 4 asks for `--chat` to stay "byte-identical" by default. Rather than only asserting the negative behaviorally (which a future refactor could silently break by, say, making `speak` a no-op default parameter instead of simply absent), T4 asserts it **structurally**: it reads `run_chat`'s own source via `inspect.getsource` and checks that none of `speak_egress`, `JARVIS_TTS_CMD`, `_voice_speak_fn`, `TtsError` appear in it at all. `run_chat` has no code path to the TTS seam — not "doesn't call it today," but "cannot call it without someone editing this exact function."

---

## 3. A stale status I fixed in passing (not part of this Buy's own scope, but adjacent)

While wiring T42's PLATFORM/CONNECTIONS entries, I found T41's own entries in both files still read "await Cursor review → Engineer ★ ACCEPT" — but the tip's own commit history (`fc1001e Record Cursor PASS WITH NOTES for T41 voice demo-ready`, then two follow-up fix/test commits) and this Buy's own IC header ("T41 … PASS WITH NOTES / live Piper") show T41 has already been reviewed, with ACCEPT explicitly deferred until this Buy lands. I corrected those two lines to say "Cursor PASS WITH NOTES @ `0.7.1`, ACCEPT deferred until T42 lands" instead of leaving a stale "await Cursor review" that no longer matched the real tip — the same kind of forensic-sync check every prior Buy in this chain has applied to the IC/paste itself, just caught here in a doc cross-reference instead.

---

## 4. Behavior

- `--voice` with a fake `JARVIS_TTS_CMD` script and piped stdin `armar\nhold\nsalir\n`: prints both Skill turns, the fake TTS script's recorded stdin contains exactly two captures (the `armar` honesty message, then the `hold` allow/sim-tick message), and the process exits after printing "Sesión de voz cerrada." — verified both via the formal test (T1) and manually from the real CLI entrypoint before writing it.
- `--voice` with no `JARVIS_TTS_CMD` configured: each turn still prints its Skill result, followed by `TTS no disponible: no external TTS command configured (…)`, and the loop continues to the next typed line rather than exiting — verified for two consecutive turns (T2), confirming the honest-failure path survives repeated use, not just once.
- Every classify call during a `--voice` session carries `source=VOICE` — confirmed by spying on `VoiceIntentAdapter.parse` across multiple turns (T3), not just the first.
- `run_chat`'s source contains no reference to the TTS seam at all (T4, §2).
- No speech package in `pyproject.toml`'s dependencies; ESC fence green on every relevant file; the guide's first bare `--voice` mention precedes its first `--voice-fixture` mention (T5) — checked with a word-boundary regex rather than a plain substring search, since `--voice` is itself a substring of `--voice-fixture`.

---

## 5. Tests executed

```text
pytest tests/test_assistant_voice_interactive_cli_b1.py tests/test_assistant_voice_demo_ready_b1.py -q
→ 13 passed (T42's own 5 tests + T41's original 8, confirming the guide rewrite broke nothing)

pytest tests/test_fase_c_esc_pwm_stub_rung_b1.py tests/test_suite_no_tip_version_pins_b1.py -q
→ 19 passed (T16 ESC fence + T17 tip-pin guardrail both still green)

pytest tests/ -q
→ 4004 passed, 9 skipped, 0 failed
```

Diffed against this branch's pre-T42 tip (stash push/pop): baseline was `3999 passed, 9 skipped, 0 failed`. **Zero regressions** — the only delta is the 5 new T42 tests passing. `git status` before committing shows exactly one `src/` file touched (`adapters/cli/main.py`), matching the IC's own file list.

---

## 6. Remaining

None for this Buy. The two follow-ups are the Engineer's, not code's: deciding whether T42's ★ ACCEPT also resolves T41's deferred one (same voice surface, no new vendor introduced between them), and picking what comes next — live mic/wake-word as its own future phase, or T40 (craft/world voice).
