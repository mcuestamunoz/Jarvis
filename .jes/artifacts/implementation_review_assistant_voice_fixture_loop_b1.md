# Implementation Review — Assistant voice fixture loop (`B1-assistant-voice-fixture-loop`, T36)

**Date:** 2026-10-03  
**Reviewer:** Cursor (forensic pass — Claude paste “Hecho — T36 implementado…”)  
**Against:** [IC](implementation_contract_assistant_voice_fixture_loop_b1.md) · [report](implementation_report_assistant_voice_fixture_loop_b1.md) · [DC ★](design_contract_assistant_chat_voice_channels_b0.md) · [cola note](engineer_note_voice_phase_c_cola.md)  
**Tip reviewed:** `4bb1f19` on `cursor/voice-fixture-loop-impl-8ac5` (parent IC `8763887` / tip `v0.6.43`)  
**Verdict:** **PASS WITH NOTES** → await Engineer ★ **ACCEPT** → tag **`v0.6.44`**.

**Process note:** Claude Code implemented under Engineer paste (= Buy). This is the independent Cursor review of record. Same-session self-PASS is not review of record. **No ACCEPT claimed here.**

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| Parallel brain / Skill runtime | **Clear** — reuses `handle_user_text(..., source=VOICE)` + `render_response` |
| Audio / vendor STT/TTS creep | **Clear** — plain-text `FixtureSttSource` only; `speak` callback seam |
| Orchestrator fork / fulfill rewrite | **Clear** — `orchestrator.py` diff = 0 lines |
| `--chat` / MCP broken | **Clear** — flag additive; old call shape still works (T4) |
| Invented CLOSED map rows | **Clear** — `a4-voice-world` advanced only; `voice-intent-ingress` stays ★ CLOSED from T35 |
| Radio fence false positive | **Clear** — no `capabilities.radio` literal under adapters (report N caught) |
| Authority `"voice"` | **Clear** |
| Tip pins / ESC | **Clear** — T17 + T16 green incl. new voice files |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.2 new thin `adapters/voice/` | **PASS** |
| §0.3 Fixture STT stand-in (text lines) | **PASS** (`from_lines` / `from_path`) |
| §0.4 `run_voice_turn` → VOICE + `render_response` | **PASS** |
| §0.5 `run_voice` fixture loop; optional CLI flag | **PASS** (`--voice-fixture`) |
| §0.6 reuse brain; no fulfill fork | **PASS** |
| §0.7 e2e tests without mic | **PASS** (T2/T3/T3b) |
| §0.8 Safety honesty | **PASS** |
| §0.9 `0.6.44` · docs · no invented CLOSED | **PASS** (see N1 ARCHITECTURE sync) |
| §0.10 Out list | **PASS** |
| Tests T1–T5 | **PASS** (+ T3b speak callback — welcome) |

---

## 2. Verification (this pass)

```text
PYTHONPATH=/workspace python3 -m pytest \
  tests/test_assistant_voice_fixture_loop_b1.py \
  tests/test_assistant_voice_intent_ingress_b1.py \
  tests/test_fase_c_intent_safety_stub_b1.py \
  tests/test_fase_c_radio_dual_role_b1.py \
  tests/test_assistant_chat_sim_copper_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py \
  tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 64 passed
```

Library smoke: `run_voice(..., ["estado"])` → ok + non-empty egress.

Report full-suite claim (3974 / +6) not re-run here.

---

## 3. Notes

**N1 — ARCHITECTURE tip line (synced on this review tip).** Still said “T36 fixture-loop IC”; PRIORIDAD/PLATFORM/CONNECTIONS already Implemented. Review tip aligns ARCHITECTURE wording. Not behavior.

**N2 — Process.** Engineer ★ ACCEPT → tag **`v0.6.44`**. Next IC when Engineer says proceed: **T37** external STT @ `0.6.45` (vendor ★ separate). T39 product milestone **`v0.7.0`** stays after T37+T38.

---

## 4. Awaiting

```text
Cursor verdict: PASS WITH NOTES
Await Engineer ★ ACCEPT → tag v0.6.44
Next authorize/paste when Engineer says proceed: T37 B1-assistant-voice-stt-external @ 0.6.45
```
