# Implementation Review — Assistant voice interactive CLI (`B1-assistant-voice-interactive-cli`, T42)

**Date:** 2026-10-04  
**Reviewer:** Cursor (forensic pass — Claude paste “Hecho — T42 implementado…”)  
**Against:** [IC](implementation_contract_assistant_voice_interactive_cli_b1.md) · [report](implementation_report_assistant_voice_interactive_cli_b1.md) · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md) · [cola note](engineer_note_voice_phase_c_cola.md)  
**Tip reviewed:** `fd202e8` on `cursor/voice-interactive-cli-impl-8ac5` (parent IC `b217dd6` / tip T41 `0368952`)  
**Verdict:** **PASS WITH NOTES** → Engineer ★ **ACCEPT CLOSED** (2026-10-05) @ tip **`v0.7.2`**.

**Process note:** Claude Code implemented under Engineer paste (= Buy). This is the independent Cursor review of record. Same-session self-PASS is not review of record. **No ACCEPT claimed here.** **Updated:** Engineer ★ ACCEPT CLOSED (2026-10-05) → tag **`v0.7.2`** (stack close).

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| New STT/TTS vendor family | **Clear** — reuses `run_voice_turn` + `_voice_speak_fn` only |
| Silent change to `--chat` | **Clear** — `run_chat` untouched; T4 structural inspect |
| REPL crash on missing TTS | **Clear** — T2: honest `TTS no disponible`, loop continues |
| Fixture still primary in guide | **Clear** — §4 = `--voice`; §5 = batch |
| Speech deps / tip pins / ESC | **Clear** — T5 |
| Scope creep (wake-word / mic loop / T40) | **Clear** |
| `src/` blast radius | **Clear** — only `adapters/cli/main.py` |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.2 `--voice` REPL + speak | **PASS** |
| §0.3 reuse T35–T38 seams | **PASS** |
| §0.4 `--chat` default unchanged | **PASS** (T4 structural) |
| §0.5 typed input; mic/wake-word out | **PASS** |
| §0.6 TTS honesty, no crash | **PASS** (T2) |
| §0.7 guide leads with interactive | **PASS** |
| §0.8 `0.7.2` · docs · no new C-xxx | **PASS** |
| §0.9 tests | **PASS** (T1–T5) |
| §0.10 Out list | **PASS** |

---

## 2. Verification (this pass)

```text
PYTHONPATH=/workspace/src python3 -m pytest \
  tests/test_assistant_voice_interactive_cli_b1.py \
  tests/test_assistant_voice_demo_ready_b1.py \
  tests/test_assistant_voice_tts_external_b1.py \
  tests/test_assistant_voice_fixture_loop_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py \
  tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 44 passed
```

`--help` lists `--voice`. Report full-suite claim (4004 / +5) not re-run here.

---

## 3. Notes

**N1 — Interactive use is keyboard + spoken replies (not mic).** Matches IC lock 5 and the Engineer ask to *use* Jarvis (not fixture demos). Mic remains optional one-shot in guide §5.3. Honest product surface.

**N2 — Process.** Engineer ★ ACCEPT → tag **`v0.7.2`**. Then day-to-day: Piper env (§2–§3) + `python -m jarvis.main --voice`. Consider ★ ACCEPT of T41 `@ v0.7.1` in the same close if still deferred, or leave T41 tagged when convenient — tip already carries `0.7.2`.

---

## 4. Awaiting

```text
Cursor verdict: PASS WITH NOTES
Engineer ★ ACCEPT CLOSED → tag v0.7.2
Use path: export JARVIS_* → python -m jarvis.main --voice
```
