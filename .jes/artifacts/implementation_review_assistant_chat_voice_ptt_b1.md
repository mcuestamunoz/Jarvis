# Implementation Review — Chat voice push-to-talk (`B1-assistant-chat-voice-ptt`, T47)

**Date:** 2026-10-05  
**Reviewer:** Cursor (forensic pass — Engineer handoff: tip pushed to `cursor/chat-voice-ptt-impl-8ac5`)  
**Against:** [IC](implementation_contract_assistant_chat_voice_ptt_b1.md) · [DC](design_contract_assistant_chat_voice_ptt_b0.md) · [report](implementation_report_assistant_chat_voice_ptt_b1.md) · [living map](engineer_note_chat_spoken_continuity_map.md) · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md)  
**Tip reviewed:** `ba89d3e` on `cursor/chat-voice-ptt-impl-8ac5` (parent IC `611cce4` / T45 tip `2f001de`)  
**Verdict:** **PASS WITH NOTES** → await Engineer ★ **ACCEPT** → tag **`v0.7.5`**.

**Process note:** Claude Code implemented under Engineer paste (= Buy). This is the independent Cursor review of record. Same-session self-PASS is not review of record. **No ACCEPT claimed here.**

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| Always-on / wake-word / background mic | **Clear** — intercept only on typed `hablar`/`habla` when `speak_tts=True` |
| Parallel brain / `source=VOICE` / `run_voice_turn` | **Clear** — transcript → same `handle_user_text` (no `source` kwarg); `run_voice_turn` only named in docstring negation |
| Re-intercept if STT returns `hablar` | **Clear** — T5c: record ran once; `[voz] hablar` then fall-through |
| TTS during capture (bleed) | **Clear** — `Grabando` is plain `print`, not `speak()` |
| Bare `--chat` records | **Clear** — T3; gated on `speak_tts` |
| Keyboard path broken | **Clear** — T2 typed `armar` never touches record |
| `hablar` stolen into Continuity defer | **Clear** — not in `CONTINUITY_DEFER_PHRASES` |
| Invented Skill on record/STT failure | **Clear** — T4/T4b/T5/T5b honest + loop survives |
| Speech deps / tip pins / ESC | **Clear** — T7; `external_record.py` in ESC walk |
| T45 walls / T42 TTS source guard | **Clear** — T6; sibling T45/T43 suites green this pass |
| Scope (T40 / `--voice` PTT / orch) | **Clear** — no orch / spoken_continuity extract / `run_voice_interactive` edits |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.2 no new flag; bare chat never records | **PASS** |
| §0.3 trigger `hablar`/`habla` exact + Continuity normalize; not in defer | **PASS** (`is_ptt_trigger`; accent `hábla` matches; `háblame`/`hablar.` do not) |
| §0.4 `JARVIS_RECORD_CMD` `{output}` / optional `{seconds}`; typed RecordError; default 7 s | **PASS** (`external_record.py`) |
| §0.5 cue print-only → record → STT → `[voz]` → same loop | **PASS** (`main.py:1019–1039`) |
| §0.6 honesty + Ctrl-C continue + temp unlink | **PASS** (`finally: unlink`; KeyboardInterrupt → `Grabación cancelada.`) |
| §0.7 `record_turn.sh` ffmpeg/arecord + `--check` | **PASS** (T7 stripped-PATH `--check` fails with `no recorder found`) |
| §0.8 guide + map screen-only rows + docs | **PASS** — five Table 1 rows; §4.1.1 |
| §0.9 `0.7.5` no speech deps | **PASS** |
| §0.10 tests T1–T7 | **PASS** (10 functions: T4/T5 split + T5c re-intercept) |

---

## 2. Verification (this pass)

```text
PYTHONPATH=/workspace/src python3 -m pytest \
  tests/test_assistant_chat_voice_ptt_b1.py \
  tests/test_assistant_chat_spoken_continuity_b1.py \
  tests/test_assistant_chat_voice_speak_b1.py \
  tests/test_assistant_voice_interactive_cli_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py \
  tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 46 passed
```

Also verified: `hablar`/`habla` ∉ `CONTINUITY_DEFER_PHRASES`; `run_chat` source has none of `speak_egress` / `JARVIS_TTS_CMD` / `_voice_speak_fn` / `TtsError`; `pyproject` version `0.7.5`. Report full-suite claim (4026 / +10) not re-run here.

---

## 3. Notes

**N1 — `tempfile.mkstemp` leaves the file descriptor open.**  
**Remediated (Engineer “hazlo”, Cursor):** `run_chat` now does `fd, tmp_name = tempfile.mkstemp(...); os.close(fd)` before handing the path to the recorder. Path + `finally: unlink` unchanged.

**N2 — T7 does not assert package `0.7.5` as a string.** Version is correct in `pyproject.toml`; same optional gap as T45 N2.

**N3 — T1 proves fall-through via Skill egress markers, not a `handle_user_text` spy.** CapSys shows `vehicle_arm_policy`/`ARMADA` after `[voz] armar` and no `No he entendido` — enough for the IC. Optional stronger spy later.

**N4 — Living map line citations for pre-T47 surfaces still use older `main.py` line numbers.** New PTT rows cite current lines (`:1021`/`:1038`/…). Stale banner/welcome line numbers are pre-existing map drift, not introduced by this Buy.

---

## 4. Awaiting

```text
Cursor verdict: PASS WITH NOTES
Await Engineer ★ ACCEPT → tag v0.7.5
Use:
  export JARVIS_TTS_CMD=… JARVIS_STT_CMD=… \
    JARVIS_RECORD_CMD="$PWD/scripts/voice/record_turn.sh {output} {seconds}"
  ./scripts/voice/record_turn.sh --check
  python3 -m jarvis.main --chat --voice-speak
  User > hablar   # then speak a Skill / estado into the mic
```
