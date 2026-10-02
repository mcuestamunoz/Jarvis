# Implementation Review — Chat Skill-first vehicle FOLLOW (`B1-assistant-chat-skill-first-vehicle-follow`)

**Date:** 2026-10-02  
**Reviewer:** Cursor (forensic pass — Claude paste “Hecho — T28 implementado…”)  
**Against:** [IC](implementation_contract_assistant_chat_skill_first_vehicle_follow_b1.md) · [report](implementation_report_assistant_chat_skill_first_vehicle_follow_b1.md) · [DC ★](design_contract_assistant_chat_skill_first_b0.md) · [SD-GO_TO OPEN](engineer_note_t20_goto_chat_sim_destination_debt.md)  
**Tip reviewed:** `747d472` on `cursor/skill-first-vehicle-follow-impl-8ac5` (parent tip T27 ★ `v0.6.36` @ `40902b4` / `e82b960`)  
**Verdict:** **★ ACCEPT CLOSED** (Engineer 2026-10-02) — Cursor review **PASS WITH NOTES**. Package/tag **`0.6.37` / `v0.6.37`**. Sixth vehicle Skill-first (FOLLOW) closed.

**Process note:** Claude Code implemented under ★ AUTHORIZED IC. Cursor forensic PASS WITH NOTES; Engineer ★ ACCEPT this turn (“procede”).

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| FOLLOW uses `SoftwareCapabilitySafetyGate` | **Clear** — in `_VEHICLE_GATE_SKILL_IDS` → shared `_vehicle_skill_gate` |
| Duplicate / divergent vehicle-gate implementation | **Clear** — one shared gate; finite id set grown to HOLD+LAND+GO_TO+TAKEOFF+RETURN_HOME+FOLLOW |
| `flight.follow` flipped `available` | **Clear** — stays `not_implemented` @ `0.6.20`; provider still `vehicle` |
| Track/target parse / invent | **Clear** — `_handle_vehicle_follow` byte-unchanged (`params={}`) |
| FOLLOW added to T20 sim copper tick set | **Clear** — handler unchanged (no sim note); T1b asserts `"Simulación" not in message` |
| PATROL…/CHARGE become runnable | **Clear** — still `skill_stub` (sibling probes retargeted to PATROL) |
| Silent Task fallback on Skill reject | **Clear** — orch `outcome != "ok"` → honest “Skill request_follow no disponible (reason).” |
| HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME Skill-first regress | **Clear** — T3/T4 + sibling suites green |
| Tip / package | **Clear** — `0.6.37`; tip-pin guardrail + ESC fence green |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.2 only FOLLOW Skill → `available` @ `0.6.37`; `flight.follow` stays `not_implemented` | **PASS** |
| §0.3 grow shared vehicle gate …+FOLLOW; no SoftwareCapabilitySafetyGate; gate-only | **PASS** |
| §0.4 chat FOLLOW: `run_skill` then existing `_handle_vehicle_follow` (empty params · ArmedAllowlist · no sim tick) | **PASS** |
| §0.5 HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME Skill-first regression · FN-016 + SD-GO_TO OPEN untouched | **PASS** |
| §0.6 other paths unchanged (PATROL…/CHARGE/explain/status) | **PASS** |
| §0.7 tests T1–T5 (+ T1b no-sim) · sibling stub retargets FOLLOW→PATROL | **PASS** |
| §0.8 version/docs · no new C-xxx · SD-GO_TO row stays OPEN | **PASS** |
| §0.9 Out: sim FOLLOW tick · track invent · siblings · inventing cap available · copper · SD-GO_TO · voice · tip pins | **PASS** |

---

## 2. Verification (this pass)

```text
PYTHONPATH=/workspace pytest \
  tests/test_assistant_chat_skill_first_vehicle_follow_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_return_home_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_takeoff_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_go_to_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_land_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_hold_b1.py \
  tests/test_capability_skills_runtime_software_b1.py \
  tests/test_assistant_vehicle_follow_task_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py \
  tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 71 passed
```

Available Skills: explain, project_status, request_hold, request_land, request_go_to, request_takeoff, request_return_home, request_follow.  
`_VEHICLE_GATE_SKILL_IDS` = HOLD + LAND + GO_TO + TAKEOFF + RETURN_HOME + FOLLOW.  
`_handle_vehicle_follow` body identical to pre-T28 tip (`40902b4`).

Report’s full-suite claim (3937 passed / +6 vs 3931) not re-run in this pass; targeted + fences cover the IC surface.

---

## 3. Notes

**N1 — Finite id set growth (carry-forward).** `_VEHICLE_GATE_SKILL_IDS` remains the shared dispatch; this Buy correctly grows membership. Remaining siblings (PATROL…) still need their own Buys. **Not blocking.**

**N2 — Process.** Engineer ★ ACCEPT applied → tag `v0.6.37`. Cola after ★: remaining vehicle Skill-first siblings (PATROL…) before voz/world (phase C). **SD-GO_TO stays OPEN.** FOLLOW remains outside T20 sim tick set.

---

## 4. Next

```text
★ ACCEPT CLOSED @ v0.6.37 (Engineer 2026-10-02)
Skill-first phase B: HOLD ★ + LAND ★ + GO_TO ★ + TAKEOFF ★ + RETURN_HOME ★ + FOLLOW ★
SD-GO_TO: still OPEN
Next: vehicle Skill-first siblings (PATROL…) — not voice yet
```
