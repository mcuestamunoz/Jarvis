# Implementation Review — Assistant voice v1 checkpoint (`B1-assistant-voice-v1-checkpoint`, T39)

**Date:** 2026-10-03  
**Reviewer:** Cursor (forensic pass — Claude paste “Hecho — T39 implementado…”)  
**Against:** [IC](implementation_contract_assistant_voice_v1_checkpoint_b1.md) · [report](implementation_report_assistant_voice_v1_checkpoint_b1.md) · [DC ★](design_contract_assistant_chat_voice_channels_b0.md) · [TTS brief](engineer_note_voice_tts_product_brief.md) · [cola note](engineer_note_voice_phase_c_cola.md)  
**Tip reviewed:** `7579655` on `cursor/voice-v1-checkpoint-impl-8ac5` (parent IC `77a68a5` / tip `v0.6.46`)  
**Verdict:** **PASS WITH NOTES** → Engineer ★ **ACCEPT CLOSED** (2026-10-04) @ tip **`v0.7.0`**.

**Process note:** Claude Code implemented under Engineer paste (= Buy). This is the independent Cursor review of record. Same-session self-PASS is not review of record.

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| New voice seam / `src/` change | **Clear** — `git diff` IC→impl: **no** `src/` paths; only tests + `pyproject` + docs/artifacts |
| Speech SDK / Piper in `pyproject` | **Clear** — `0.7.0`; deps = `pydantic` only; `"piper"`/`whisper`/etc. absent |
| Tip-pin in new tests | **Clear** — T5 invokes T17 guardrail; Claude self-removed a forbidden `version = "0.7.0"` assert before ship |
| Twelve Skills not covered | **Clear** — T1 `EXPECTED_ACTIONS` frozenset equality (12 distinct actions) + non-empty egress |
| Craft/LLM fallthrough | **Clear** — `_ExplodingLLMInterface` on T1/T2/T3/T5 |
| Fake STT→Skill→TTS missing | **Clear** — T3 |
| Authority `"voice"` / Radio/Api | **Clear** — T4 |
| Invented CLOSED map rows | **Clear** — `a4-voice-world` voice half **Implemented pending review**; world = T40 |
| ESC fence | **Clear** — T5 |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.2 no new voice seam; reuse T35–T38 | **PASS** |
| §0.3 product picture proof (fixture → VOICE → Skill → egress → fake TTS) | **PASS** (T1/T2) |
| §0.4 twelve Skills on voice path | **PASS** (T1) |
| §0.5 combined STT→Skill→TTS | **PASS** (T3) |
| §0.6 `pyproject` → `0.7.0` (not `0.6.47`) | **PASS** |
| §0.7 docs / cola / `a4-voice-world` / brief | **PASS** |
| §0.8 safety / tip pins / ESC / no speech deps | **PASS** |
| §0.9 vendor / Piper out | **PASS** |
| §0.10 Out list | **PASS** |
| Tests T1–T5 | **PASS** |

---

## 2. Verification (this pass)

```text
PYTHONPATH=/workspace python3 -m pytest \
  tests/test_assistant_voice_v1_checkpoint_b1.py \
  tests/test_assistant_voice_tts_external_b1.py \
  tests/test_assistant_voice_stt_external_b1.py \
  tests/test_assistant_voice_fixture_loop_b1.py \
  tests/test_assistant_voice_intent_ingress_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py \
  tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 47 passed
```

Report full-suite claim (3991 / +5) not re-run here.

---

## 3. Notes

**N1 — Tip-parent lines previously said `v0.6.46` while package was already `0.7.0`.** Resolved on Engineer ★ ACCEPT → tag **`v0.7.0`**.

**N2 — Process.** Engineer ★ ACCEPT (2026-10-04) → tag **`v0.7.0`** (“Jarvis voz v1”). Voice half of `a4-voice-world` complete. Next Parked: **T40** craft/`world/` (own DC).

---

## 4. Closed

```text
Cursor verdict: PASS WITH NOTES
Engineer ★ ACCEPT CLOSED → tag v0.7.0
Next: T40 craft/world voice — Parked (own DC later)
```
