# Implementation Review — Assistant voice Intent ingress (`B1-assistant-voice-intent-ingress`, T35)

**Date:** 2026-10-03  
**Reviewer:** Cursor (forensic pass — Claude paste “Hecho — T35 implementado…”)  
**Against:** [IC](implementation_contract_assistant_voice_intent_ingress_b1.md) · [report](implementation_report_assistant_voice_intent_ingress_b1.md) · [DC ★](design_contract_assistant_chat_voice_channels_b0.md) · [cola note](engineer_note_voice_phase_c_cola.md)  
**Tip reviewed:** `b207786` on `cursor/voice-intent-ingress-impl-8ac5` (parent authorize `d1e7def` / tip `v0.6.42`)  
**Verdict:** **PASS WITH NOTES** → Engineer ★ **ACCEPT CLOSED** (2026-10-03) @ tip **`v0.6.43`**.

**Process note:** Claude Code implemented under ★ AUTHORIZED IC. This is the independent Cursor review of record. Same-session self-PASS is not review of record.

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| Voice still raises / wrong source tag | **Clear** — `VoiceIntentAdapter.parse` → `Intent(source=VOICE, raw_text=…)` mirrors Terminal |
| Hardcoded TERMINAL left at classify sites | **Clear** — exactly **12** `self._parse_intent(...)` call sites; only helper calls `TerminalIntentAdapter.parse` |
| CLI/MCP forced new args | **Clear** — keyword-only `source=None`; CLI `run_chat` + MCP `session_manager.chat` unchanged |
| Parallel brain / new Skill runtime | **Clear** — same `try_*` / `run_skill` / `_handle_*` path; only Intent tag differs |
| Authority `"voice"` surface | **Clear** — `AuthoritySource = Literal["radio", "api", "operator"]` untouched |
| Radio/Api silently filled | **Clear** — both still `NotImplementedError` (T4 + C2 retarget) |
| Connect-plugs row CLOSED early | **Clear at impl** — row stayed Parked until this ★ ACCEPT |
| STT/TTS/loop/`world`/`v0.7.0` creep | **Clear** — out of Buy; package `0.6.43` only |
| Tip pins / ESC fence | **Clear** — T17 + T16 green on this pass |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.2 `VoiceIntentAdapter.parse` → VOICE Intent; Radio/Api NI | **PASS** |
| §0.3 optional `source` on `handle_user_text` path; default TERMINAL | **PASS** |
| §0.4 twelve sites via helper; no leftover hardcode | **PASS** (count re-verified = 12) |
| §0.5 reuse brain; TERMINAL behavior unchanged | **PASS** (T2 regression) |
| §0.6 prove VOICE path in tests without STT | **PASS** (T3 spy) |
| §0.7 no Authority voice; ArmedAllowlist unchanged | **PASS** |
| §0.8 `0.6.43` · PRIORIDAD/PLATFORM/CONNECTIONS · map pointer not CLOSED | **PASS** (see N1 cola note sync) |
| §0.9 Out list | **PASS** |
| Tests T1–T5 | **PASS** |
| C2 retarget (Voice no longer refuses) | **PASS** (`test_t2_radio_api…` + `test_t2b_…`) |

---

## 2. Verification (this pass)

```text
PYTHONPATH=/workspace python3 -m pytest \
  tests/test_assistant_voice_intent_ingress_b1.py \
  tests/test_fase_c_intent_safety_stub_b1.py \
  tests/test_assistant_chat_sim_copper_b1.py \
  tests/test_assistant_chat_go_to_destination_b1.py \
  tests/test_assistant_vehicle_arm_ux_b1.py \
  tests/test_fn016_navigation_parse_safety.py \
  tests/test_suite_no_tip_version_pins_b1.py \
  tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 69 passed
```

Spot-checks: `VoiceIntentAdapter.parse("estado")` → VOICE; Radio NI; AuthoritySource has no `"voice"`; CLI/MCP call sites omit `source`.

Report full-suite claim (3968 / +6 net) not re-run here.

---

## 3. Notes

**N1 — Cola note status drift (synced on this review tip).** IC §1 listed short wire on `engineer_note_voice_phase_c_cola.md`; Claude left T35 row as `★ AUTHORIZED · Claude` while PRIORIDAD/PLATFORM/CONNECTIONS/map already said Implemented. Review tip updates that row to **Implemented · await Cursor review → Engineer ★ ACCEPT**. Not a behavior issue.

**N2 — `_parse_intent` fallthrough honesty (V1 OK).** Helper dispatches VOICE → `VoiceIntentAdapter`, else → `TerminalIntentAdapter` (which always tags TERMINAL). Chat path only passes `VOICE` or default `TERMINAL`, so T35 locks hold. A future caller passing `RADIO`/`API`/`UI` would mislabel as TERMINAL — out of this Buy; keep in mind for later channel Buys.

**N3 — Process.** Engineer ★ ACCEPT (2026-10-03) → tag **`v0.6.43`** · connect-plugs `voice-intent-ingress` **★ CLOSED**. Next authorize when Engineer says proceed: **T36** fixture loop @ `0.6.44`. T39 product milestone **`v0.7.0`** stays locked after T37+T38.

---

## 4. Closed

```text
★ ACCEPT CLOSED @ v0.6.43
Connect-plugs voice-intent-ingress ★ CLOSED
Next authorize when Engineer says proceed: T36 B1-assistant-voice-fixture-loop @ 0.6.44
```
