# Implementation Report — Assistant voice v1 checkpoint (`B1-assistant-voice-v1-checkpoint`, T39)

**Project:** Jarvis  
**Date:** 2026-10-03  
**Implementer:** Claude Code (Engineer paste)  
**Contract:** [`implementation_contract_assistant_voice_v1_checkpoint_b1.md`](implementation_contract_assistant_voice_v1_checkpoint_b1.md)  
**Parents:** [DC voice/channels ★ CLOSED](design_contract_assistant_chat_voice_channels_b0.md) · [T38 ★ ACCEPT CLOSED](implementation_review_assistant_voice_tts_external_b1.md) @ `v0.6.46` · T37/T36/T35 ★ · [TTS product brief](engineer_note_voice_tts_product_brief.md) · [cola note](engineer_note_voice_phase_c_cola.md)  
**Status:** **Implemented** (Claude Code) — await Cursor review → Engineer ★ ACCEPT.  
**Package / tag:** `0.7.0` / pending **`v0.7.0`**.

---

## 1. What landed

**Zero new voice seam — proof only.** This Buy touches no `src/jarvis/adapters/voice/*.py` file and no `src/jarvis/core/orchestrator.py` — confirmed via `git status` before committing: the only changes are `pyproject.toml`'s version bump, one new test file, and docs.

| Area | Change |
|---|---|
| `tests/test_assistant_voice_v1_checkpoint_b1.py` | **new** T1–T5 integration proofs, reusing T35–T38's `FixtureSttSource`, `run_voice`, `run_voice_turn_from_audio`, `make_speak_callable` exactly as shipped |
| `pyproject.toml` | `0.6.46` → **`0.7.0`** — **no** new speech dependency |
| Docs / cola / connect-plugs / brief / state | PRIORIDAD · PLATFORM · CONNECTIONS (no new C-xxx) · ARCHITECTURE tip line; cola note's T39 row + tip-parent line → Implemented; connect-plugs `a4-voice-world` row → voice half Implemented (pending T39 ★), world half unchanged at T40; TTS brief's tip-parent line bumped (brief body untouched); `.jes/state/engineering_state.json` cycle → implemented, awaiting review |

**Not touched:** `orchestrator.py`, every `adapters/voice/*.py` file (`fixture_loop.py`, `external_stt.py`, `external_tts.py`, `__init__.py`), `adapters/cli/main.py`, `render_response`, `run_skill`/`skills_runtime.py`, any `_handle_*` fulfill method, `RadioIntentAdapter`/`ApiIntentAdapter`, `AuthoritySignal`/`AuthoritySource` (no `"voice"` literal), no speech package added to `pyproject.toml` (confirmed: no `whisper`/`vosk`/`piper`/etc. anywhere in dependencies), tip-version pins (T17 guardrail re-verified green — and my own first test draft's `assert 'version = "0.7.0"' in pyproject_text` line was caught and removed before it could itself become a forbidden tip pin, see §2), ESC fence (T16, re-verified green on `orchestrator.py` and all four `adapters/voice/`/`adapters/cli/main.py` files).

---

## 2. A self-caught near-violation (not shipped)

My first draft of test T5 asserted `'version = "0.7.0"' in pyproject_text` to confirm the version bump landed. Before running it, I checked T17's own guardrail regex (`tests/test_suite_no_tip_version_pins_b1.py`) and found this exact shape — `assert\s+['"]version\s*=\s*\"[0-9.]+\"\s*in\s+\w+` — is itself one of the forbidden tip-pin patterns. Removed the assertion (the version bump is already proven by the fact that `pyproject.toml` itself was edited and the suite stays green); re-ran the guardrail test to confirm it stays green with the new test file present.

---

## 3. Behavior (the product picture, proven)

- **T1 — twelve Skills, no craft fallthrough:** a 12-line fixture (`armar`, `hold`, `land`, `go to`, `takeoff`, `return home`, `follow`, `patrol`, `charge`, `desarmar`, `explain c-rate-de-bateria`, `estado`) run through `run_voice` on a disarmed-then-armed `JarvisOrchestrator` produces exactly 12 turns, one per declared Skill, each with a distinct `result["action"]` (`vehicle_arm_policy`, `vehicle_hold`, `vehicle_land`, `vehicle_go_to`, `vehicle_takeoff`, `vehicle_return_home`, `vehicle_follow`, `vehicle_patrol`, `ops_charge`, `vehicle_disarm_policy`, `global_command`, `project_status`) and a non-empty `render_response` egress. `_ExplodingLLMInterface` (every method raises) proves the LLM/craft fallthrough is never reached for any of these twelve phrases. Spying on `VoiceIntentAdapter.parse` confirms every classify call carried `source=VOICE`.
- **T2 — twelve Skills speak to a fake TTS:** the same fixture, with `speak=make_speak_callable(command_template=<fake script>)`, results in the fake script's recorded stdin containing all 12 egress strings, each delimited and verified present verbatim.
- **T3 — combined STT→Skill→TTS:** a fake STT script (`echo 'hold'`) feeds `run_voice_turn_from_audio`, whose `(result, egress)` is then handed to a `speak_egress`/`make_speak_callable`-built TTS call — the recorded file starts with the exact egress string, and the `VoiceIntentAdapter.parse` spy confirms `source=VOICE` reached classify with the transcribed text (`"hold"`).
- **T4 — Radio/Api still refuse; no Authority voice:** unchanged (both T35–T38 already proved this; re-verified here as the checkpoint's own honesty gate).
- **T5 — version, deps, fences, regression:** `pyproject.toml` bumped (verified by editing it, not by a forbidden assertion — see §2); no speech package in dependencies; ESC fence green on every relevant file; `--chat`-equivalent (`handle_user_text` with no `source`) and `--voice-fixture`-equivalent (`run_voice` with no `speak`) both still work with zero `JARVIS_STT_CMD`/`JARVIS_TTS_CMD` configured.

---

## 4. Tests executed

```text
pytest tests/test_assistant_voice_v1_checkpoint_b1.py -q
→ 5 passed

pytest tests/test_suite_no_tip_version_pins_b1.py tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 19 passed (T17 guardrail + T16 ESC fence both still green)

pytest tests/ -q
→ 3991 passed, 9 skipped, 0 failed
```

Diffed against this branch's pre-T39 tip (stash push/pop): baseline was `3986 passed, 9 skipped, 0 failed`. **Zero regressions** — the only delta is the 5 new T39 tests passing.

---

## 5. Remaining

None for this Buy. On Engineer ★ ACCEPT: tag `v0.7.0` — the "Jarvis voz v1" product milestone. T40 (craft/world voice, its own future DC) remains the only item still Parked in the voice phase C cola; the voice *half* of the connect-plugs map's `a4-voice-world` row is now fully Implemented end-to-end (ingress, Skill-first brain, egress, combined STT→TTS), pending only this Buy's own review/ACCEPT.
