# Implementation Review — Assistant voice STT external (`B1-assistant-voice-stt-external`, T37)

**Date:** 2026-10-03  
**Reviewer:** Cursor (forensic pass — Claude paste “Hecho — T37 implementado…”)  
**Against:** [IC](implementation_contract_assistant_voice_stt_external_b1.md) · [report](implementation_report_assistant_voice_stt_external_b1.md) · [DC ★](design_contract_assistant_chat_voice_channels_b0.md) · [cola note](engineer_note_voice_phase_c_cola.md)  
**Tip reviewed:** `955bb18` on `cursor/voice-stt-external-impl-8ac5` (parent IC `421a327` / tip `v0.6.44`)  
**Verdict:** **PASS WITH NOTES** → Engineer ★ **ACCEPT CLOSED** (2026-10-03) @ tip **`v0.6.45`**.

**Process note:** Claude Code implemented under Engineer paste (= Buy). This is the independent Cursor review of record. Same-session self-PASS is not review of record.

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| Speech SDK / tip-pinned vendor in deps | **Clear** — `pyproject` `0.6.45`, no whisper/vosk/… |
| Audio decode in core/capabilities/intelligence | **Clear** — only `adapters/voice/external_stt.py` + subprocess |
| Silent fixture fallback on STT failure | **Clear** — typed `SttConfigError` / `SttProcessError` / `SttEmptyTranscriptError` |
| Invented Skill phrase on empty/fail | **Clear** — T3 |
| Break `--chat` / `--voice-fixture` | **Clear** — T5 regression |
| Orchestrator / fulfill fork | **Clear** — orch diff 0; reuses `run_voice_turn` |
| Invented CLOSED map rows | **Clear** — `a4-voice-world` advanced only |
| Tip pins / ESC / Authority `"voice"` | **Clear** |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.2 external process seam, no speech deps | **PASS** |
| §0.3 `JARVIS_STT_CMD` + `{audio}`; missing → typed fail | **PASS** |
| §0.4 stdout transcript → `run_voice_turn`; fail typed | **PASS** |
| §0.5 keep fixture path; optional `--voice-audio` | **PASS** |
| §0.6 fake STT script proves e2e without mic | **PASS** (T1/T4) |
| §0.7 vendor pick out | **PASS** |
| §0.8 Safety honesty | **PASS** |
| §0.9 `0.6.45` · docs · no invented CLOSED | **PASS** |
| §0.10 Out list | **PASS** |
| Tests T1–T5 | **PASS** (+ hierarchy sanity; missing-binary → `SttProcessError`) |

---

## 2. Verification (this pass)

```text
PYTHONPATH=/workspace python3 -m pytest \
  tests/test_assistant_voice_stt_external_b1.py \
  tests/test_assistant_voice_fixture_loop_b1.py \
  tests/test_assistant_voice_intent_ingress_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py \
  tests/test_fase_c_esc_pwm_stub_rung_b1.py \
  tests/test_fase_c_radio_dual_role_b1.py -q
→ 52 passed
```

Report full-suite claim (3980 / +6) not re-run here.

---

## 3. Notes

**N1 — Welcome honesty beyond IC.** Missing binary / `OSError` from `subprocess.run` re-raised as `SttProcessError` (CLI prints typed message, no raw traceback). Keep.

**N2 — TTS product brief tip sibling.** Engineer brief (British / grave / free-first Piper) lives on `cursor/voice-tts-product-brief-8ac5` (PR #35), not stacked into this impl tip. **Rescue at T38** — do not lose. Engineer already parked that path.

**N3 — Process.** Engineer ★ ACCEPT (2026-10-03) → tag **`v0.6.45`**. Next IC when Engineer says proceed: **T38** TTS-external @ `0.6.46` — rescue TTS product brief / Piper `en_GB` (PR #35). T39 product milestone **`v0.7.0`** after T37+T38 ★.

---

## 4. Closed

```text
★ ACCEPT CLOSED @ v0.6.45
Next paste when Engineer says proceed: T38 B1-assistant-voice-tts-external @ 0.6.46
(Rescue TTS product brief / Piper en_GB)
```
