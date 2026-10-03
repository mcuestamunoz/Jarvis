# Implementation Report — Assistant voice Intent ingress (`B1-assistant-voice-intent-ingress`, T35)

**Project:** Jarvis  
**Date:** 2026-10-03  
**Implementer:** Claude Code (Engineer authorization paste)  
**Contract:** [`implementation_contract_assistant_voice_intent_ingress_b1.md`](implementation_contract_assistant_voice_intent_ingress_b1.md)  
**Parents:** [DC voice/channels ★ CLOSED](design_contract_assistant_chat_voice_channels_b0.md) · [T34-inv ★](investigation_review_assistant_voice_e2e_b0.md) · [cola note](engineer_note_voice_phase_c_cola.md) · tip `v0.6.42`  
**Status:** **Implemented** (Claude Code) — await Cursor review → Engineer ★ ACCEPT.  
**Package / tag:** `0.6.43` / pending **`v0.6.43`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/capabilities/intent.py` | `VoiceIntentAdapter.parse(raw_text: str) -> Intent` now mirrors `TerminalIntentAdapter.parse` exactly — `Intent(source=IntentSource.VOICE, raw_text=raw_text)`, stops raising `NotImplementedError`. `RadioIntentAdapter`/`ApiIntentAdapter` byte-unchanged — still always raise. Module + class docstrings updated to describe T35's scope |
| `src/jarvis/core/orchestrator.py` | New `_parse_intent(self, raw_text, source)` method — dispatches to `VoiceIntentAdapter.parse` when `source == IntentSource.VOICE`, else `TerminalIntentAdapter.parse` (the only two adapters that build a real `Intent`). `handle_user_text`, `_handle_user_text_inner`, and `_handle_global_commands` each gained an optional keyword-only `source: Any \| None = None`; `_handle_global_commands` resolves `effective_source = source or IntentSource.TERMINAL` once, at the top. All **twelve** `TerminalIntentAdapter.parse(stripped)` call sites (explain, Continuity-defer, ARM, DISARM, HOLD, LAND, GO_TO, TAKEOFF, RETURN_HOME, FOLLOW, PATROL, CHARGE) replaced with `self._parse_intent(stripped, effective_source)` — no hardcode left. Two now-unused local `TerminalIntentAdapter` imports removed (the import survives only inside `_parse_intent` itself) |
| `tests/test_assistant_voice_intent_ingress_b1.py` | **new** T1–T5 |
| `tests/test_fase_c_intent_safety_stub_b1.py` | `test_t2_voice_radio_api_adapters_refuse` renamed to `test_t2_radio_api_adapters_refuse` and narrowed to just Radio/Api (Voice no longer refuses); new `test_t2b_voice_adapter_now_builds_intent` added, pointing at the new T35 suite for full coverage |
| `pyproject.toml` | `0.6.43` |
| Docs | PRIORIDAD · PLATFORM · CONNECTIONS (no new C-xxx); connect-plugs map `voice-intent-ingress` row updated (status stays **Parked**, not CLOSED — per the IC, it closes only on Engineer ★ ACCEPT) |

**Not touched:** `RadioIntentAdapter`/`ApiIntentAdapter` (still `NotImplementedError`, byte-unchanged), `AuthoritySignal.source`/`AuthoritySource` (no `"voice"` literal added — verified via `typing.get_args`), the three internal `_handle_user_text_inner` re-dispatch call sites deep in wizard-preempt/resume logic (craft-path continuation, not a new Skill-first classify — left source-less/`TERMINAL` deliberately, per the IC's narrow scope), any `_handle_*` fulfill method, `run_skill`/`skills_runtime.py`, any STT/TTS code, `world/`, tip-version pins (T17 guardrail re-verified green), ESC fence (T16, re-verified green).

---

## 2. Behavior

- Every existing CLI (`run_chat`) and MCP (`JarvisSessionManager.chat`) call to `handle_user_text(user_input, llm_interface)` — no `source` kwarg — resolves to `TERMINAL` exactly as before; byte-identical messages, byte-identical classify/fulfill paths (regression-tested: T2).
- `handle_user_text(user_input, llm_interface, source=IntentSource.VOICE)` on a Skill-first phrase (e.g. `hold`) reaches `try_request_hold_task` with an `Intent` whose `source == VOICE` — verified by spying on `VoiceIntentAdapter.parse`/`TerminalIntentAdapter.parse` and confirming only the former is called (T3). Fulfill/honesty (disarmed reject, armed allow/not_implemented) is unchanged either way — only the `Intent.source` tag differs, exactly as the DC locks.
- `VoiceIntentAdapter.parse("hold")` directly returns a real `Intent(source=VOICE, raw_text="hold")`, no exception (T1).
- `RadioIntentAdapter`/`ApiIntentAdapter` still always raise `NotImplementedError("... not_implemented in C2")` (T4).
- No `"voice"` member exists on `AuthoritySource` (`Literal["radio", "api", "operator"]`) — confirmed via introspection (T5); no Authority surface was touched.

---

## 3. Tests executed

```text
pytest tests/test_assistant_voice_intent_ingress_b1.py \
  tests/test_fase_c_intent_safety_stub_b1.py \
  tests/test_assistant_chat_sim_copper_b1.py \
  tests/test_assistant_chat_go_to_destination_b1.py \
  tests/test_fn016_navigation_parse_safety.py -q
→ 41 passed

pytest tests/test_suite_no_tip_version_pins_b1.py tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 19 passed (T17 guardrail + T16 ESC fence both still green)

pytest tests/ -q
→ 3968 passed, 9 skipped, 0 failed
```

Diffed against this branch's pre-T35 tip (stash push/pop): baseline was `3962 passed, 9 skipped, 0 failed`. **Zero regressions** — the delta is the 5 new T35 tests plus the T2/T2b split in `test_fase_c_intent_safety_stub_b1.py` (net +6 test functions).

---

## 4. Remaining

None for this Buy. Next candidate per the voice phase C cola: **T36** `B1-assistant-voice-fixture-loop` (V2) — a fixture-driven `run_voice()`-style loop proving the ingress→Skill→egress chain end-to-end without a real microphone, blocked on this Buy's ★ ACCEPT. T37 (external STT)/T38 (external TTS)/T39 (voice v1 product milestone, opens `v0.7.0`)/T40 (craft/world, explicitly out of voice v1) all remain Parked per the DC's own phase table.
