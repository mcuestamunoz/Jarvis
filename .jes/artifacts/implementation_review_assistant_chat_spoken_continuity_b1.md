# Implementation Review — Chat spoken continuity (`B1-assistant-chat-spoken-continuity`, T45)

**Date:** 2026-10-04  
**Reviewer:** Cursor (forensic pass — Claude paste “T45 complete…”)  
**Against:** [IC](implementation_contract_assistant_chat_spoken_continuity_b1.md) · [DC](design_contract_assistant_chat_spoken_continuity_b0.md) · [report](implementation_report_assistant_chat_spoken_continuity_b1.md) · [living map](engineer_note_chat_spoken_continuity_map.md) · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md)  
**Tip reviewed:** `c9a1d16` on `cursor/chat-spoken-continuity-impl-9ac5` (parent plan/IC `a617438` / T44-inv review `3db4c59`)  
**Verdict:** **PASS WITH NOTES** → await Engineer ★ **ACCEPT** → tag **`v0.7.4`**.

**Process note:** Claude Code implemented under Engineer paste (= Buy). This is the independent Cursor review of record. Same-session self-PASS is not review of record. **No ACCEPT claimed here.**

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| Screen Continuity recorted | **Clear** — T2/T3: `ENGINEERING READINESS` / `TOP GAPS` still in `capsys` |
| LLM / second Continuity | **Clear** — extract of existing ctx fields only |
| Speak-all-turns as brief | **Clear** — only load + `action == "project_status"`; T4 Skill speak-as-printed |
| Double-print via `_voice_speak_fn` | **Clear** |
| FULL latch across turns | **Clear enough** — T3: load brief + `completo` full in one session (N4) |
| Bare `--chat` speaks | **Clear** — T4; `_chat_speak_fn(False)` still no-op; `inspect.getsource(run_chat)` TTS-token fence empty |
| Speech deps / tip pins / ESC | **Clear** — T6; `spoken_continuity.py` in ESC walk |
| Scope (T40 / `--voice` / orch ranking) | **Clear** — no `project_continuity` ranking change |
| `src/` blast | **Clear** — `spoken_continuity.py` + `run_chat` speak sites + 3 defer phrases |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.2 print unchanged | **PASS** |
| §0.3 speak brief on walls; empty brief skip | **PASS** (`spoken_text_for_wall` → `speak(...)`) |
| §0.4 walls = load + `project_status` | **PASS** (`main.py:1015–1017`, `:1044–1049`) |
| §0.5 brief field order + humanize helper | **PASS** (lazy import of `_humanize_next_useful_why`; unknown codes pass through — same as wall) |
| §0.6 FULL set, per-turn, no latch | **PASS WITH NOTES** — set matches DC; 3 new defer phrases (N1) |
| §0.7 extractor in `adapters/voice/` | **PASS** |
| §0.8 guide + map + docs | **PASS** — §4.1/§8 describe shipped split; map `:676-682` |
| §0.9 `0.7.4` no speech deps | **PASS** (`pyproject.toml`) |
| §0.10 tests T1–T6 | **PASS** (T3 split T3/T3b; 7 tests) |

---

## 2. Verification (this pass)

```text
PYTHONPATH=/workspace/src python3 -m pytest \
  tests/test_assistant_chat_spoken_continuity_b1.py \
  tests/test_assistant_chat_voice_speak_b1.py \
  tests/test_assistant_voice_interactive_cli_b1.py \
  tests/test_assistant_voice_demo_ready_b1.py \
  tests/test_assistant_defer_continuity_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py \
  tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 50 passed
```

`FULL_CONTINUITY_PHRASES <= CONTINUITY_DEFER_PHRASES`. Accent normalize: `cuéntame todo` matches. Report full-suite claim (4016 / +7) not re-run here.

---

## 3. Notes

**N1 — `CONTINUITY_DEFER_PHRASES` gained `completo` / `estado completo` / `cuentame todo`.**  
Required so those FULL lines reach `project_status` at all (otherwise they would fall through to classify/LLM and T3 could not speak a wall). Side effect: **bare `--chat`** (no speak) also treats exact `completo` as `estado`. Exact-match only — not a substring steal. Honest and documented in the report; Engineer should know text chat gained three Continuity aliases.

**N2 — T6 does not assert package `0.7.4` as a string.** Version is correct in `pyproject.toml`; optional follow-up.

**N3 — Extractor lazy-imports `cli.main._humanize_next_useful_why`.** Matches IC “move if cycle”; lazy import avoids import cycle. Fine for T45.

**N4 — No-latch is shown as load-brief + `completo`-full, not `completo` then `estado`.** Combinator has no session state; a follow-up `estado` cannot latch. Optional extra test.

**N5 — Guide §4.1** has a small English leak (“unless que also pidas”). Does not block ★.

---

## 4. Awaiting

```text
Cursor verdict: PASS WITH NOTES
Await Engineer ★ ACCEPT → tag v0.7.4
Use: export JARVIS_TTS_CMD → python3 -m jarvis.main --chat --voice-speak
  load / estado → brief ears, full screen
  dame detalles / completo → wall that turn
```
