# Implementation Review — Assistant voice TTS external (`B1-assistant-voice-tts-external`, T38)

**Date:** 2026-10-03  
**Reviewer:** Cursor (forensic pass — Claude paste “Hecho — T38 implementado…”)  
**Against:** [IC](implementation_contract_assistant_voice_tts_external_b1.md) · [report](implementation_report_assistant_voice_tts_external_b1.md) · [DC ★](design_contract_assistant_chat_voice_channels_b0.md) · [TTS brief](engineer_note_voice_tts_product_brief.md) · [cola note](engineer_note_voice_phase_c_cola.md)  
**Tip reviewed:** `ba308e9` on `cursor/voice-tts-external-impl-8ac5` (parent IC `a38d134` / tip `v0.6.45`)  
**Verdict:** **PASS WITH NOTES** → await Engineer ★ **ACCEPT** → tag **`v0.6.46`**.

**Process note:** Claude Code implemented under Engineer paste (= Buy). This is the independent Cursor review of record. Same-session self-PASS is not review of record. **No ACCEPT claimed here.**

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| Speech SDK / Piper in `pyproject` | **Clear** — `0.6.46`, no speech deps; `"piper"` absent from pyproject |
| Egress text smashed into argv | **Clear** — stdin only via `subprocess.run(..., input=text)` |
| Silent no-op when TTS missing | **Clear** — typed `TtsConfigError` / `TtsProcessError` |
| Fulfill / `render_response` fork | **Clear** — orch / fixture_loop / external_stt untouched |
| Break `--chat` / fixture / audio | **Clear** — `speak_tts=False` default; T5 regression |
| Invented CLOSED map rows | **Clear** — `a4-voice-world` advanced only; brief kept |
| Authority `"voice"` / tip pins / ESC | **Clear** |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.2 external TTS process seam, no speech deps | **PASS** |
| §0.3 `JARVIS_TTS_CMD`; stdin text; missing → typed fail | **PASS** |
| §0.4 input = `render_response` egress; exit 0; typed fails | **PASS** |
| §0.5 `make_speak_callable` / `speak=` on `run_voice`; CLI `--voice-speak` | **PASS** |
| §0.6 fake TTS script proves without speaker | **PASS** (T1/T4) |
| §0.7 product brief present; Piper not hardcoded as dep | **PASS** (see N1 docstring) |
| §0.8 vendor out of core | **PASS** |
| §0.9 `0.6.46` · docs · brief on tip | **PASS** |
| §0.10 Out list | **PASS** |
| Tests T1–T5 | **PASS** (+ hierarchy sanity) |

---

## 2. Verification (this pass)

```text
PYTHONPATH=/workspace python3 -m pytest \
  tests/test_assistant_voice_tts_external_b1.py \
  tests/test_assistant_voice_stt_external_b1.py \
  tests/test_assistant_voice_fixture_loop_b1.py \
  tests/test_assistant_voice_intent_ingress_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py \
  tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 42 passed
```

Report full-suite claim (3986 / +6) not re-run here.

---

## 3. Notes

**N1 — Docstring names Piper while claiming “never names Piper in code”.** Module/`__init__` docstrings point at the product brief and mention Piper as the external free-first demo. **No import, no dep, no hardcode.** Soft honesty nit only — behavior matches the IC. Optional polish: drop the self-contradicting “never names” sentence later.

**N2 — Process.** Engineer ★ ACCEPT → tag **`v0.6.46`**. Construction V1–V4 complete. Next: **T39** voice v1 checkpoint opens product milestone **`v0.7.0`** (docs/checkpoint Buy — not more seam code unless IC says so).

---

## 4. Awaiting

```text
Cursor verdict: PASS WITH NOTES
Await Engineer ★ ACCEPT → tag v0.6.46
Next when Engineer says proceed: T39 B1-assistant-voice-v1-checkpoint @ 0.7.0
```
