# Implementation Review — Chat Skill-first vehicle PATROL (`B1-assistant-chat-skill-first-vehicle-patrol`)

**Date:** 2026-10-02  
**Reviewer:** Cursor (forensic pass — Claude paste “Hecho — T29 implementado…”)  
**Against:** [IC](implementation_contract_assistant_chat_skill_first_vehicle_patrol_b1.md) · [report](implementation_report_assistant_chat_skill_first_vehicle_patrol_b1.md) · [DC ★](design_contract_assistant_chat_skill_first_b0.md) · [SD-GO_TO OPEN](engineer_note_t20_goto_chat_sim_destination_debt.md)  
**Tip reviewed:** `274d3b1` on `cursor/skill-first-vehicle-patrol-impl-8ac5` (parent tip T28 ★ `v0.6.37` @ `5f742be` / `435f2ae`)  
**Verdict:** **PASS WITH NOTES** — await Engineer ★ ACCEPT → tag **`v0.6.38`**. **No ACCEPT claim in this pass.**

**Process note:** Claude Code implemented under ★ AUTHORIZED IC. This is the independent Cursor review of record. Same-session self-PASS is not review of record.

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| PATROL uses `SoftwareCapabilitySafetyGate` | **Clear** — in `_VEHICLE_GATE_SKILL_IDS` → shared `_vehicle_skill_gate` |
| Duplicate / divergent vehicle-gate implementation | **Clear** — one shared gate; finite id set now HOLD…PATROL (7) |
| `flight.patrol` flipped `available` | **Clear** — stays `not_implemented` @ `0.6.21`; provider still `vehicle` |
| Route/circuit parse / invent | **Clear** — `_handle_vehicle_patrol` byte-unchanged (`params={}`) |
| PATROL added to T20 sim copper tick set | **Clear** — handler unchanged (no sim note); T1b asserts `"Simulación" not in message` |
| CHARGE/ARM/DISARM become runnable | **Clear** — still `skill_stub` (sibling probes retargeted to CHARGE) |
| Silent Task fallback on Skill reject | **Clear** — orch `outcome != "ok"` → honest “Skill request_patrol no disponible (reason).” |
| Six prior vehicle Skill-first regress | **Clear** — T3/T4 + sibling suites green |
| Tip / package | **Clear** — `0.6.38`; tip-pin guardrail + ESC fence green |
| Seven AutonomyVerb Skill-first set closed | **Clear** — gate membership = HOLD+LAND+GO_TO+TAKEOFF+RETURN_HOME+FOLLOW+PATROL |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.2 only PATROL Skill → `available` @ `0.6.38`; `flight.patrol` stays `not_implemented` | **PASS** |
| §0.3 grow shared vehicle gate …+PATROL; no SoftwareCapabilitySafetyGate; gate-only | **PASS** |
| §0.4 chat PATROL: `run_skill` then existing `_handle_vehicle_patrol` (empty params · ArmedAllowlist · no sim tick) | **PASS** |
| §0.5 six prior vehicle Skill-first regression · FN-016 + SD-GO_TO OPEN untouched | **PASS** |
| §0.6 other paths unchanged (ARM/DISARM/CHARGE/explain/status) | **PASS** |
| §0.7 tests T1–T5 (+ T1b no-sim) · sibling stub retargets PATROL→CHARGE | **PASS** |
| §0.8 version/docs · no new C-xxx · SD-GO_TO OPEN · closes AutonomyVerb Skill-first set | **PASS** |
| §0.9 Out: sim PATROL tick · route invent · CHARGE/ARM/DISARM · inventing cap available · copper · SD-GO_TO · voice · tip pins | **PASS** |

---

## 2. Verification (this pass)

```text
PYTHONPATH=/workspace pytest \
  tests/test_assistant_chat_skill_first_vehicle_patrol_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_follow_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_return_home_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_takeoff_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_go_to_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_land_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_hold_b1.py \
  tests/test_capability_skills_runtime_software_b1.py \
  tests/test_assistant_vehicle_patrol_task_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py \
  tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 77 passed
```

Available vehicle Skills in gate: HOLD + LAND + GO_TO + TAKEOFF + RETURN_HOME + FOLLOW + PATROL.  
`_handle_vehicle_patrol` body identical to pre-T29 tip (`5f742be`).

Report’s full-suite claim (3943 passed / +6 vs 3937) not re-run in this pass; targeted + fences cover the IC surface.

---

## 3. Notes

**N1 — AutonomyVerb Skill-first set closed.** This Buy completes phase B for the seven chat AutonomyVerbs. Remaining Skill-first candidates are policy/ops (ARM/DISARM/CHARGE) — different shape; may need a non-vehicle gate later. **Not blocking.**

**N2 — Process.** Await Engineer ★ ACCEPT → tag `v0.6.38`. Cola after ★: policy/ops Skill-first or phase C (voz/world). **SD-GO_TO stays OPEN.** PATROL remains outside T20 sim tick set.

---

## 4. Next

```text
Cursor: PASS WITH NOTES @ 274d3b1 (+ review commit)
Await: Engineer ★ ACCEPT → tag v0.6.38
Skill-first phase B AutonomyVerbs: HOLD ★ … PATROL (pending ★) — set complete on ★
SD-GO_TO: still OPEN
Next after ★: policy/ops Skill-first (ARM/DISARM/CHARGE) or phase C — Engineer pick
```
