# Implementation Review — Voice speak-path sanitize (`B1-assistant-voice-speak-sanitize`, T50)

**Date:** 2026-10-05  
**Reviewer:** Cursor (forensic pass — Engineer handoff: tip on `cursor/chat-voice-ptt-impl-8ac5`)  
**Against:** [IC](implementation_contract_assistant_voice_speak_sanitize_b1.md) · [report](implementation_report_assistant_voice_speak_sanitize_b1.md) · [FN-017](engineer_note_voice_spoken_polish_field_fn017.md) · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md)  
**Tip reviewed:** `29abdbd` on `cursor/chat-voice-ptt-impl-8ac5` (parent IC `2ee08e8` / T49 tip `d38d601`)  
**Verdict:** **PASS WITH NOTES** → Engineer ★ **ACCEPT CLOSED** (2026-10-05) @ tip **`v0.7.7`**.

**Process note:** Claude Code implemented under Engineer paste (= Buy), after reconciling onto the real tip (Field Note + IC + T41–T49 ★). This is the independent Cursor review of record. Same-session self-PASS is not review of record. **No ACCEPT claimed here.** **Updated:** Engineer ★ ACCEPT CLOSED (2026-10-05) → tag **`v0.7.7`**.

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| Print / Layer 1 mutated | **Clear** — zero edits to `main.py` / `spoken_continuity.py` / `render_*`; T6 proves no sanitizer refs there |
| Sanitize not on all speak paths | **Clear** — wired at start of `speak_egress` (covers chat + voice + fixture) |
| ASCII `-` eaten as leading marker | **Clear** — T1c: `-5kg margen` kept; rule-only `------` dropped |
| Glossary over-reach (`PROJECT STATUS` / `PASS`) | **Clear** — T3 |
| Silent TTS success on empty | **Clear** — empty after sanitize returns without invoking cmd (T4b) |
| T42 `run_chat` TTS source guard | **Clear** — empty forbidden list this pass |
| Speech deps / tip pins / ESC | **Clear** — tip-pin + ESC green; `0.7.7` |
| LLM / T40 / T51–T52 scope creep | **Clear** |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.2 `speak_sanitize.py` pure helper | **PASS** |
| §0.3 wire at `speak_egress` start | **PASS** |
| §0.4 decoration (rules / leading glyphs / footnote `*` / blank collapse) | **PASS** — includes `━`/`├`/`│`; hyphen split correct |
| §0.5 glossary only `C-rate` → `tasa C` | **PASS** |
| §0.6 empty → `""`, no filler | **PASS** |
| §0.7 honesty fences | **PASS** |
| §0.8 tests T1–T6 | **PASS** (9 functions) |
| §0.9 docs + FN-017 Implemented | **PASS** |
| §0.10 `0.7.7` | **PASS** |

---

## 2. Verification (this pass)

```text
PYTHONPATH=/workspace/src python3 -m pytest \
  tests/test_assistant_voice_speak_sanitize_b1.py \
  tests/test_assistant_voice_v1_checkpoint_b1.py \
  tests/test_assistant_voice_tts_spanish_b1.py \
  tests/test_assistant_chat_spoken_continuity_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py \
  tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 44 passed
```

Live sanitize spot-check on a Continuity-shaped fragment: bars/`•`/`PASS *` stripped; `C-rate` → `tasa C`; `-5kg margen` kept. Report full-suite claim (4039 / 9 skipped) not re-run here.

---

## 3. Notes

**N1 — Glossary yields “El tasa C” (gender awkward).**  
Locked string is `"tasa C"` per IC; Spanish article agreement is out of T50. Optional polish in T51 if Engineer wants `"la tasa C"` / rephrase.

**N2 — `external_tts.py` module docstring still narrates pre-T49 “Piper en_GB” demo setup.**  
`__init__.py` was fixed as the IC file list required. Cosmetic residue in `external_tts.py` header only — does not affect behavior. Optional one-line sync later.

**N3 — Intentional sibling-test updates are correctly documented.**  
T39 fake-TTS assertion now compares sanitized egress; T49 tip-version pin removed (policy). Not regressions — required by the locked glossary + tip-pin policy.

---

## 4. Awaiting

```text
Cursor verdict: PASS WITH NOTES
Engineer ★ ACCEPT CLOSED → tag v0.7.7
Smoke after ACCEPT:
  # same Piper env as before
  python -m jarvis.main --chat --voice-speak
  User > 1
  User > completo   # should NOT read ──── / • / * ; C-rate → "tasa C"
```
