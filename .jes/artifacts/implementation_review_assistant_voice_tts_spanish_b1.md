# Implementation Review — Voice TTS Spanish default (`B1-assistant-voice-tts-spanish`, T49)

**Date:** 2026-10-05  
**Reviewer:** Cursor (forensic pass — Engineer handoff: tip on `cursor/chat-voice-ptt-impl-8ac5`)  
**Against:** [IC](implementation_contract_assistant_voice_tts_spanish_b1.md) · [report](implementation_report_assistant_voice_tts_spanish_b1.md) · [brief](engineer_note_voice_tts_product_brief.md) · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md) · [T48-inv Q8](investigation_report_assistant_voice_phase_t_review_b0.md)  
**Tip reviewed:** `8419582` on `cursor/chat-voice-ptt-impl-8ac5` (parent T48-inv `6d419e0` / T47 tip `44cb5fe`)  
**Verdict:** **PASS WITH NOTES** → Engineer ★ **ACCEPT CLOSED** (2026-10-05) @ tip **`v0.7.6`**.

**Process note:** Claude Code implemented under Engineer paste (= Buy). This is the independent Cursor review of record. Same-session self-PASS is not review of record. **No ACCEPT claimed here.** **Updated:** Engineer ★ ACCEPT CLOSED (2026-10-05) → tag **`v0.7.6`** (stack close).

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| `src/jarvis` touched | **Clear** — `git diff 6d419e0..8419582 -- src/` empty |
| Speech deps / tip-pinned `.onnx` | **Clear** — T4; `find` empty; `pyproject` `0.7.6` with no speech packages |
| Hardcoded model in `piper_tts.sh` body | **Clear** — T3; body has `JARVIS_PIPER_MODEL`, no `davefx`/`sharvard`/`alan-medium` |
| Default still `en_GB` in guide/brief | **Clear** — davefx is default; en_GB documented as legacy |
| Whisper script forced to multilingual | **Clear** — guide-only; `whisper_stt.sh` untouched |
| New C-xxx / wake-word / T40 | **Clear** — PLATFORM/CONNECTIONS short wires only |
| ACCEPT claimed | **Clear** |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.1 Brief: Accent `es_ES`; default `es_ES-davefx-medium`; alt sharvard; en_GB legacy | **PASS WITH NOTES** — table locks hold; **N1** stale historical “A/B two en_GB” recommendation sentence left in §2 |
| §0.2 Guide §2/§3/cheatsheet/§8 → davefx; HF `es/es_ES/davefx/medium/` | **PASS** |
| §0.3 `piper_tts.sh` comment examples only; body model-agnostic | **PASS** |
| §0.4 STT honesty — multilingual `ggml-base.bin` in guide; no whisper script change | **PASS** |
| §0.5 `pyproject` → `0.7.6`; no speech deps | **PASS** |
| §0.6 Tests T1–T4 | **PASS** (4/4 green this pass) |
| §0.7 Short PLATFORM/CONNECTIONS; no new C-xxx | **PASS** |
| §0.8 Prefer no `src/jarvis` | **PASS** |
| Opportunistic T45 N5 fix (`also` → `también`) | **PASS** — guide `:113` |

---

## 2. Verification (this pass)

```text
PYTHONPATH=/workspace/src python3 -m pytest \
  tests/test_assistant_voice_tts_spanish_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py \
  tests/test_fase_c_esc_pwm_stub_rung_b1.py \
  tests/test_assistant_chat_voice_ptt_b1.py -q
→ 33 passed
```

Also verified: version `0.7.6`; guide default export/`--check` examples use `es_ES-davefx-medium.onnx`; cheatsheet + §8 Spanish-default prose; brief Default/Alt/Legacy rows; `piper_tts.sh` header Spanish example; T42 `run_chat` TTS-seam source guard still `[]`. Report full-suite claim (4030 / 9 skipped) not re-run here.

---

## 3. Notes

**N1 — Brief §2 “Recommendation” still says A/B two `en_GB` voices.**  
Product table (§1) and demo checklist (§4) correctly Spanish-default. The older T38-era recommendation sentence (`A/B two en_GB male voices offline`) was left as historical residue. Cosmetic; does not undo the default flip. Optional one-line rewrite on a later docs touch.

**N2 — Live-ear judgment still open (report §4).**  
Same class as T41 N1 / T48-inv Q9: no Cursor pass substitutes for hearing `es_ES-davefx-medium` against “grave / corto / sin teatro.” Engineer after ACCEPT.

---

## 4. Awaiting

```text
Cursor verdict: PASS WITH NOTES
Engineer ★ ACCEPT CLOSED → tag v0.7.6
Operator path after ACCEPT:
  # download es_ES-davefx-medium.onnx + .onnx.json
  export JARVIS_PIPER_MODEL="$HOME/piper/es_ES-davefx-medium.onnx"
  export JARVIS_TTS_CMD="$PWD/scripts/voice/piper_tts.sh"
  # for Spanish hablar: multilingual whisper model in JARVIS_STT_CMD
  python3 -m jarvis.main --chat --voice-speak
```
