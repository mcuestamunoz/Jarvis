# Implementation Review — Assistant chat + spoken replies (`B1-assistant-chat-voice-speak`, T43)

**Date:** 2026-10-04  
**Reviewer:** Cursor (forensic pass — Claude paste “T43 is implemented and pushed…”)  
**Against:** [IC](implementation_contract_assistant_chat_voice_speak_b1.md) · [report](implementation_report_assistant_chat_voice_speak_b1.md) · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md) · [cola note](engineer_note_voice_phase_c_cola.md)  
**Tip reviewed:** `8719e56` on `cursor/chat-voice-speak-impl-8ac5` (parent IC `d73cf51` / tip T42 lineage)  
**Verdict:** **PASS WITH NOTES** → Engineer ★ **ACCEPT CLOSED** (2026-10-05) @ tip **`v0.7.3`**.

**Process note:** Claude Code implemented under Engineer paste (= Buy). This is the independent Cursor review of record. Same-session self-PASS is not review of record. **No ACCEPT claimed here.** **Updated:** Engineer ★ ACCEPT CLOSED (2026-10-05) → tag **`v0.7.3`** (stack close).

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| Double-print via `_voice_speak_fn` | **Clear** — new `_chat_speak_fn` is speak-only; `_say` prints once then speaks |
| Silent speak on bare `--chat` | **Clear** — default `speak_tts=False` + T2 (fake TTS file never created) |
| Forced `source=VOICE` / Skills-only brain | **Clear** — `handle_user_text(user_input, llm_interface)` unchanged; Continuity/craft stay |
| REPL crash on missing TTS | **Clear** — T3: ≥2 honest `TTS no disponible`, loop continues to exit |
| Scope creep (wake-word / mic / T40 / speech deps) | **Clear** |
| `src/` blast radius | **Clear** — only `adapters/cli/main.py` (+ guide/tests/docs) |
| Speech deps / tip pins / ESC | **Clear** — T5 |
| `--voice` (T42) regression | **Clear** — import smoke T4 + full T42 file green this pass |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.2 `--chat --voice-speak` reuses flag; bare silent | **PASS** — `main()` → `run_chat(speak_tts=args.voice_speak)` |
| §0.3 speak same printed strings (startup/wizard/errors/turns) | **PASS** — `_say` + startup_block `speak(...)` coverage |
| §0.4 no double-print; honest TTS failure | **PASS** |
| §0.5 chat brain TERMINAL / Continuity/craft | **PASS** |
| §0.6 `--voice` unchanged; both paths in guide | **PASS** — §4.1 / §4.2 |
| §0.7 guide co-primary + long Continuity honesty | **PASS** |
| §0.8 `0.7.3` · docs · no new C-xxx | **PASS** |
| §0.9 tests T1–T5 | **PASS** |
| §0.10 Out list | **PASS** |

---

## 2. Verification (this pass)

```text
PYTHONPATH=/workspace/src python3 -m pytest \
  tests/test_assistant_chat_voice_speak_b1.py \
  tests/test_assistant_voice_interactive_cli_b1.py \
  tests/test_assistant_voice_demo_ready_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py \
  tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 37 passed
```

`inspect.getsource(run_chat)` still contains none of `speak_egress` / `JARVIS_TTS_CMD` / `_voice_speak_fn` / `TtsError` (T42 T4 still green). TTS seam lives only in `_chat_speak_fn`. `--help` documents `--voice-speak` with `--chat`. Report full-suite claim (4009 / +5) not re-run here.

---

## 3. Notes

**N1 — T42 structural T4 is now a token fence, not a “no TTS path” proof.**  
`test_t4_chat_flag_alone_never_invokes_tts` still asserts `run_chat`'s source text never names the TTS seam. That remains true by design (`_chat_speak_fn` is separate), but `run_chat(speak_tts=True)` *does* speak via that helper. Behavioral silence for bare `--chat` is now T43 **T2** (fake TTS never invoked). T42 T4's docstring (“deliberately untouched… no code path”) is stale prose — not a product defect. Optional follow-up: retarget T42 T4 docstring / assert `speak_tts=False` behavior explicitly if Engineer wants the suite wording honest.

**N2 — Process.** Engineer ★ ACCEPT → tag **`v0.7.3`**. Day-to-day path after ACCEPT: Piper env + `python -m jarvis.main --chat --voice-speak`. T41 `@ 0.7.1` and T42 `@ 0.7.2` remain PASS WITH NOTES / ACCEPT deferred — Engineer may ★ close them with T43 or leave deferred.

---

## 4. Awaiting

```text
Cursor verdict: PASS WITH NOTES
Engineer ★ ACCEPT CLOSED → tag v0.7.3
Use path: export JARVIS_TTS_CMD → python -m jarvis.main --chat --voice-speak
Bare --chat stays text-only
```
