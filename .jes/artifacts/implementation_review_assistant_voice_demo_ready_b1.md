# Implementation Review — Assistant voice demo ready (`B1-assistant-voice-demo-ready`, T41)

**Date:** 2026-10-04  
**Reviewer:** Cursor (forensic pass — Claude paste “Hecho — T41 implementado…”)  
**Against:** [IC](implementation_contract_assistant_voice_demo_ready_b1.md) · [report](implementation_report_assistant_voice_demo_ready_b1.md) · [TTS brief](engineer_note_voice_tts_product_brief.md) · [cola note](engineer_note_voice_phase_c_cola.md) · [T39 ★](implementation_review_assistant_voice_v1_checkpoint_b1.md)  
**Tip reviewed:** `5c61566` on `cursor/voice-demo-ready-impl-8ac5` (parent IC `af891b5` / tip `v0.7.0`)  
**Verdict:** **PASS WITH NOTES** → await Engineer ★ **ACCEPT** → tag **`v0.7.1`**.

**Process note:** Claude Code implemented under Engineer paste (= Buy). This is the independent Cursor review of record. Same-session self-PASS is not review of record. **No ACCEPT claimed here.**

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| New `src/` seam | **Clear** — IC→impl diff: **no** `src/` paths |
| Speech SDK in `pyproject` | **Clear** — `0.7.1`; deps = `pydantic` only |
| Silent success on missing Piper/whisper | **Clear** — wrappers exit ≠0 + stderr; T5/T5b/T5c |
| Egress smashed into argv | **Clear** — TTS stdin (`printf … \| piper`) |
| STT stdout polluted | **Clear** — noise → stderr; T5c |
| Tip pins / ESC | **Clear** — T4 + guardrail |
| Invented CLOSED / T40 scope creep | **Clear** — operator path only; T40 still Parked |
| Guide claims real Piper verified | **Clear** — report + brief split verified-vs-operator |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.2 no new core seam | **PASS** |
| §0.3 `USER_GUIDE_VOICE.md` | **PASS** |
| §0.4 TTS wrapper under `scripts/voice/` | **PASS** (`piper_tts.sh` + `--check`) |
| §0.5 sample fixture | **PASS** (8 Skill lines; T3/T3b) |
| §0.6 optional STT helper + mic docs | **PASS** (`whisper_stt.sh` + guide §5) |
| §0.7 brief / Piper free-first | **PASS** |
| §0.8 `0.7.1` · docs · no new C-xxx | **PASS** |
| §0.9 tests without requiring Piper in CI | **PASS** (stubs) |
| §0.10 Out list | **PASS** |
| Tests T1–T5 (+ extras) | **PASS** (8 functions) |

---

## 2. Verification (this pass)

```text
PYTHONPATH=/workspace/src python3 -m pytest \
  tests/test_assistant_voice_demo_ready_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py \
  tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 27 passed
```

Wrappers present + executable (`100755`). Report full-suite claim (3999 / +8) not re-run here.

---

## 3. Notes

**N1 — Real Piper / whisper / speaker / timbre not verified on this tip.** Honest and correct: stubs prove plumbing; Engineer listening call (`en_GB-alan-medium` grave/corto/sin teatro) remains open per brief. Not a code defect.

**N2 — Process.** Engineer ★ ACCEPT → tag **`v0.7.1`**. After that: follow `docs/USER_GUIDE_VOICE.md` §2–§4 to hear the first real demo. T40 craft/`world` stays Parked.

---

## 4. Awaiting

```text
Cursor verdict: PASS WITH NOTES
Await Engineer ★ ACCEPT → tag v0.7.1
Operator next: install Piper + run guide §4
```
