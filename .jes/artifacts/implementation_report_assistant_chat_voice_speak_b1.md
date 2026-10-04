# Implementation Report — Assistant chat + spoken replies (`B1-assistant-chat-voice-speak`, T43)

**Project:** Jarvis  
**Date:** 2026-10-04  
**Implementer:** Claude Code (Engineer paste)  
**Contract:** [`implementation_contract_assistant_chat_voice_speak_b1.md`](implementation_contract_assistant_chat_voice_speak_b1.md)  
**Parents:** [T42](implementation_review_assistant_voice_interactive_cli_b1.md) @ `0.7.2` (PASS WITH NOTES) · [T41](implementation_review_assistant_voice_demo_ready_b1.md) · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md)  
**Status:** **Implemented** (Claude Code) — await Cursor review → Engineer ★ ACCEPT.  
**Package / tag:** `0.7.3` / pending **`v0.7.3`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/adapters/cli/main.py` | `run_chat()` → `run_chat(*, speak_tts: bool = False)`. New `_chat_speak_fn(speak_tts)` helper (deliberately separate from T38's `_voice_speak_fn`, which always prints internally and would double-print here) — returns a no-op when `speak_tts=False`, or a `speak(text)` callable that calls `speak_egress`/`JARVIS_TTS_CMD` and prints an honest `TTS no disponible: …` on `TtsError`. Inside `run_chat`, a local `_say(message)` closure pairs every existing `print(f"Jarvis > {message}")` with a `speak(message)` call — covering startup error, startup Continuity/context block, define-wizard proactive prompt, no-project fallback, exit/help/`Sesión cerrada`, the `Exception` handler, and the main-turn error/success branches. `main()`'s `--chat` dispatch now passes `speak_tts=args.voice_speak` (reusing the existing flag, per IC lock #2) |
| `docs/USER_GUIDE_VOICE.md` | §4 restructured into two co-primary subsections: **§4.1 `--chat --voice-speak`** (full chat + voice — projects/Continuity/craft/LLM, same brain, now also spoken) and **§4.2 `--voice`** (T42's Skills-only REPL, renamed from "la ruta principal" since it's no longer the sole primary path). §1 ("Qué no es"), §7 (cheatsheet), §8 (límites) updated to document both paths side by side. Section headers 1/6/7/8 unchanged — T41's own guide-presence test still passes unmodified; T42's bare-`--voice`-before-`--voice-fixture` ordering also still holds |
| `tests/test_assistant_chat_voice_speak_b1.py` | **new** T1–T5 |
| `pyproject.toml` | `0.7.2` → **`0.7.3`** — no new dependency |
| Docs / cola / state | PRIORIDAD · cola note T43 row · PLATFORM · CONNECTIONS (no new C-xxx) · IC status line · `engineering_state.json` |

**Not touched:** `run_voice_interactive`/`run_voice_fixture`/`run_voice_audio`/`_voice_speak_fn` (T42/T38, reused/left exactly as shipped), every `adapters/voice/*.py` file, `core/orchestrator.py` (no `source` kwarg added to any `handle_user_text` call in `run_chat` — chat brain stays `TERMINAL`-default), `render_response`, `run_skill`, any `_handle_*` fulfill, `AuthoritySource` (still no `"voice"`), `pyproject.toml`'s dependency lists (no speech package), tip-version pins (T17 guardrail green), ESC fence (T16, re-verified).

---

## 2. No double-print, and `run_chat`'s structural guard stays green

The IC's lock #4 explicitly forbids reusing `_voice_speak_fn` as-is (it always `print`s, so pairing it with `run_chat`'s own existing prints would double-print every turn). `_chat_speak_fn` is a new, separate, *speak-only* helper — it never prints; `run_chat`'s own `_say` closure does the one print, then calls `speak`.

A side effect worth flagging: T42 shipped a structural test (`test_assistant_voice_interactive_cli_b1.py::test_t4_chat_flag_alone_never_invokes_tts`) that asserts, via `inspect.getsource(run_chat)`, that `run_chat`'s own source contains **zero** literal reference to `speak_egress`, `JARVIS_TTS_CMD`, `_voice_speak_fn`, or `TtsError`. Because `_chat_speak_fn` is a separate function and `run_chat` only ever calls the local variable `speak(...)`, `run_chat`'s own source text still contains none of those four tokens — verified directly:

```text
>>> inspect.getsource(run_chat)
# contains no 'speak_egress', 'JARVIS_TTS_CMD', '_voice_speak_fn', or 'TtsError'
```

So **T42's own T4 test required no changes at all** — it passes unmodified, and still means what it meant before: `run_chat` itself never names the TTS seam, regardless of `speak_tts`. The actual seam reference lives in `_chat_speak_fn`, a new function `run_chat` calls by name only.

---

## 3. Behavior

- `--chat --voice-speak` (`run_chat(speak_tts=True)`) with a fake `JARVIS_TTS_CMD` script and piped stdin `armar\nexit\n`: prints the usual `Jarvis > Acción ejecutada: vehicle_arm_policy …` reply, and the fake TTS script's recorded stdin contains that exact same string — verified both via the formal test (T1) and manually against the real CLI entry point before writing it.
- Bare `run_chat()` (default `speak_tts=False`) with the same fake `JARVIS_TTS_CMD` configured and the same `armar`/`exit` input: the Skill reply still prints normally, but the fake TTS script's receive file is never created at all — proving the external command was never invoked (T2).
- `run_chat(speak_tts=True)` with `JARVIS_TTS_CMD` unset: each of two turns (`armar`, `hold`) prints its Skill reply followed by `Jarvis > TTS no disponible: no external TTS command configured (…)`, and the loop continues to the next turn and exits cleanly on `exit` (T3) — verified for two consecutive honest failures, not just one.
- `run_voice_interactive` (T42) remains importable/callable; the full T42 test file (5 tests) and T41's sibling file (8 tests) were re-run alongside this Buy's own 5 and all 18 pass (T4; the lightweight smoke test in the new file is a reminder of this, not the sole evidence).
- No speech package in `pyproject.toml`'s dependencies; ESC fence green on every relevant file; `docs/USER_GUIDE_VOICE.md` now contains the literal string `--chat --voice-speak` (T5).

---

## 4. Tests executed

```text
pytest tests/test_assistant_chat_voice_speak_b1.py tests/test_assistant_voice_interactive_cli_b1.py tests/test_assistant_voice_demo_ready_b1.py -q
→ 18 passed (T43's own 5 + T42's original 5 + T41's original 8 — zero retargeting needed on either sibling file)

pytest tests/test_fase_c_esc_pwm_stub_rung_b1.py tests/test_suite_no_tip_version_pins_b1.py -q
→ 19 passed (T16 ESC fence + T17 tip-pin guardrail both still green)

pytest tests/ -q
→ 4009 passed, 9 skipped, 0 failed
```

Diffed against this branch's pre-T43 tip (`git stash push -u` / `pop`): baseline was `4004 passed, 9 skipped, 0 failed`. **Zero regressions** — the only delta is the 5 new T43 tests passing, and the skip count is unchanged. `git status` before committing shows exactly the files the IC's own file list names (`adapters/cli/main.py`, `docs/USER_GUIDE_VOICE.md`, `pyproject.toml`, plus the new test file and the usual docs/state).

---

## 5. Remaining

None for this Buy. Next steps are the Engineer's: Cursor review of T43, and whether ACCEPT for T41/T42/T43 gets bundled (same voice surface, no new vendor introduced across any of the three) or tagged individually; and picking what comes after — live mic/wake-word as its own future phase, or T40 (craft/world voice, still Parked with its own DC).
