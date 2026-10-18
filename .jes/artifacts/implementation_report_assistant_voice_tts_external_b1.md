# Implementation Report — Assistant voice TTS external (`B1-assistant-voice-tts-external`, T38)

**Project:** Jarvis  
**Date:** 2026-10-03  
**Implementer:** Claude Code (Engineer paste)  
**Contract:** [`implementation_contract_assistant_voice_tts_external_b1.md`](implementation_contract_assistant_voice_tts_external_b1.md)  
**Parents:** [DC voice/channels ★ CLOSED](design_contract_assistant_chat_voice_channels_b0.md) · [T37 ★ ACCEPT CLOSED](implementation_review_assistant_voice_stt_external_b1.md) @ `v0.6.45` · [T36 ★](implementation_review_assistant_voice_fixture_loop_b1.md) · [TTS product brief](engineer_note_voice_tts_product_brief.md) · [cola note](engineer_note_voice_phase_c_cola.md)  
**Status:** **★ ACCEPT CLOSED** (Engineer 2026-10-03) — Cursor **PASS WITH NOTES**.  
**Package / tag:** `0.6.46` / **`v0.6.46`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/adapters/voice/external_tts.py` | **new** — `speak_egress(text, *, command_template=None, env_var="JARVIS_TTS_CMD")`: resolves a command template (explicit arg, else the `JARVIS_TTS_CMD` env var), splits it via `shlex.split` (no `{...}` placeholder — unlike T37's `{audio}`, there is nothing to substitute since the text always travels on **stdin**), runs it via `subprocess.run(argv, input=text, ...)`, and treats exit `0` as success. Typed failure family: `TtsError` (base) → `TtsConfigError` (missing/empty template), `TtsProcessError` (non-zero exit **or** the binary itself missing/unrunnable — `OSError` caught and re-raised) — never a silent no-op "success." `make_speak_callable(*, command_template=None, env_var=...)` returns a bound `speak(text) -> None` matching T36's `run_voice(..., speak=...)` shape exactly |
| `src/jarvis/adapters/voice/__init__.py` | re-exports the new TTS symbols alongside T36/T37's existing ones |
| `src/jarvis/adapters/cli/main.py` | new `_voice_speak_fn(speak_tts)` helper — always prints `Jarvis > {egress}`, and when `speak_tts=True` also calls `speak_egress(egress)`, catching `TtsError` and printing an honest message instead of raising. `run_voice_fixture`/`run_voice_audio` gained an optional `speak_tts: bool = False` keyword (default preserves exact prior behavior); `main()` gained a new `--voice-speak` boolean flag, combinable with `--voice-fixture`/`--voice-audio`; `--chat`'s own path is untouched |
| `tests/test_assistant_voice_tts_external_b1.py` | **new** T1–T5 (+ one extra class-hierarchy sanity check) |
| `pyproject.toml` | `0.6.46` — **no** new dependency added (confirmed: no `whisper`/`vosk`/`piper`/etc. anywhere in `dependencies`) |
| Docs / cola note / connect-plugs `a4-voice-world` / TTS brief | PRIORIDAD · PLATFORM · CONNECTIONS (no new C-xxx); cola note's T38 row → Implemented; connect-plugs `a4-voice-world` pointer advanced to mention T38 (no row marked CLOSED); the TTS product brief itself is untouched — kept on tip exactly as Cursor wrote it, per the IC's lock 7/9 |

**Not touched:** `orchestrator.py`, `run_skill`/`skills_runtime.py`, any `_handle_*` fulfill method, `render_response` (reused exactly as-is — its output is the TTS input, never rewritten for "speakability"), `fixture_loop.py`/`external_stt.py` (untouched — `FixtureSttSource`/`--voice-fixture`/`run_voice_turn_from_audio`/`--voice-audio` all still work exactly as before, regression-tested), `RadioIntentAdapter`/`ApiIntentAdapter`, `AuthoritySignal`/`AuthoritySource` (no `"voice"` literal), no speech package in `pyproject.toml`'s dependencies, no vendor (Piper or otherwise) named anywhere in code — the product brief's Piper recommendation stays a documentation/demo-setup concern, never a code dependency, tip-version pins (T17 guardrail re-verified green), ESC fence (T16, re-verified green on all four `adapters/voice/*.py` files plus `adapters/cli/main.py`).

---

## 2. Behavior

- `speak_egress('hello there, this has spaces and "quotes" — no theater', command_template="<fake_script>")` — a fake script that does `cat > file` on stdin — receives the text byte-for-byte, including spaces and quotes, because it travels on stdin rather than being shell-escaped into argv (T1, and verified manually before formalizing in tests).
- No `JARVIS_TTS_CMD` set and no explicit `command_template` → `TtsConfigError`; an explicit empty-string template → the same (T2).
- A script that exits non-zero and a command naming a binary that doesn't exist both raise `TtsProcessError` — the latter via `OSError` caught inside `speak_egress` and re-raised as a typed error, never a raw Python traceback (T3, verified manually with `/bin/false`-equivalent commands and a nonexistent binary name before formalizing).
- A Skill turn (`hold`) run through `run_voice_turn`, then spoken via a `speak` callable built by `make_speak_callable` pointed at the fake script: the exact `render_response` egress string reaches the fake script's recorded output. The same `speak` callable, passed directly as `run_voice(..., speak=speak)` (T36's own seam, unchanged), correctly receives both turns of a two-line fixture (`armar` then `hold`) in order (T4).
- `python -m jarvis.main --voice-fixture <path> --voice-speak` with `JARVIS_TTS_CMD` pointed at a fake script that appends to a log file: both fixture turns' egress strings land in the log, in order, in addition to being printed — smoke-tested manually end-to-end from the real CLI entrypoint. The same command **without** `--voice-speak` behaves byte-identically to before this Buy (also verified manually).
- `--chat` and `--voice-fixture`/`--voice-audio` (without `--voice-speak`) work with zero `JARVIS_TTS_CMD`/`JARVIS_STT_CMD` configured — neither path looks at those env vars unless explicitly asked to speak/transcribe (T5).
- No speech package appears in `pyproject.toml`; no `"voice"` member exists on `AuthoritySource`; Piper is never named anywhere in `src/jarvis/` — only in the product brief doc, as recommended demo setup.

---

## 3. Tests executed

```text
pytest tests/test_assistant_voice_tts_external_b1.py \
  tests/test_assistant_voice_stt_external_b1.py \
  tests/test_assistant_voice_fixture_loop_b1.py \
  tests/test_assistant_voice_intent_ingress_b1.py \
  tests/test_fase_c_intent_safety_stub_b1.py \
  tests/test_fase_c_radio_dual_role_b1.py -q
→ 50 passed

pytest tests/test_suite_no_tip_version_pins_b1.py tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 19 passed (T17 guardrail + T16 ESC fence both still green)

pytest tests/ -q
→ 3986 passed, 9 skipped, 0 failed
```

Diffed against this branch's pre-T38 tip (stash push/pop): baseline was `3980 passed, 9 skipped, 0 failed`. **Zero regressions** — the only delta is the 6 new T38 tests passing.

---

## 4. Remaining

None for this Buy. Next candidate per the voice phase C cola: **T39** `B1-assistant-voice-v1-checkpoint` (V5) — the product milestone (opens `v0.7.0`), blocked on both this Buy's ★ ACCEPT and T37's (already ★ ACCEPT CLOSED). T40 (craft/world, explicitly out of voice v1) remains Parked. Picking a real TTS binary (Piper `en_GB-alan-medium` per the product brief's P0 recommendation, or any other) to point `JARVIS_TTS_CMD` at is operator/demo setup, or a separate later Engineer ★ if escalating to a paid vendor — not part of this Buy.
