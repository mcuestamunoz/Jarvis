# Implementation Review — Chat Skill-first vehicle RETURN_HOME (`B1-assistant-chat-skill-first-vehicle-return-home`)

**Date:** 2026-10-02  
**Reviewer:** Cursor (forensic pass — Claude paste “Hecho — T27 implementado…”)  
**Against:** [IC](implementation_contract_assistant_chat_skill_first_vehicle_return_home_b1.md) · [report](implementation_report_assistant_chat_skill_first_vehicle_return_home_b1.md) · [DC ★](design_contract_assistant_chat_skill_first_b0.md) · [SD-GO_TO OPEN](engineer_note_t20_goto_chat_sim_destination_debt.md)  
**Tip reviewed:** `722efb1` on `cursor/skill-first-vehicle-return-home-impl-8ac5` (parent tip T26 ★ `v0.6.35` @ `b1a4e37` / `9e086d2`)  
**Verdict:** **PASS WITH NOTES** — await Engineer ★ ACCEPT → tag **`v0.6.36`**. **No ACCEPT claim in this pass.**

**Process note:** Claude Code implemented under ★ AUTHORIZED IC. This is the independent Cursor review of record. Same-session self-PASS is not review of record.

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| RETURN_HOME uses `SoftwareCapabilitySafetyGate` | **Clear** — in `_VEHICLE_GATE_SKILL_IDS` → shared `_vehicle_skill_gate` |
| Duplicate / divergent vehicle-gate implementation | **Clear** — one shared gate; finite id set grown to HOLD+LAND+GO_TO+TAKEOFF+RETURN_HOME |
| `flight.return_home` flipped `available` | **Clear** — stays `not_implemented` @ `0.6.18`; provider still `vehicle` |
| Home/waypoint parse / invent | **Clear** — `_handle_vehicle_return_home` byte-unchanged (`params={}`) |
| RETURN_HOME added to T20 sim copper tick set | **Clear** — handler unchanged (no sim note); T1b asserts `"Simulación" not in message` |
| FN-016 wizard cancel reordered / stolen by RETURN_HOME | **Clear** — FN-016 block untouched in diff; still ~line 530 before RETURN_HOME ~696; T4b locks wizard `"volver"` → `cancelled`/`define_missing_params` |
| IDLE `"volver"` still RETURN_HOME via Skill-first | **Clear** — T4c |
| FOLLOW…/CHARGE become runnable | **Clear** — still `skill_stub` (sibling probes retargeted to FOLLOW) |
| Silent Task fallback on Skill reject | **Clear** — orch `outcome != "ok"` → honest “Skill request_return_home no disponible (reason).” |
| HOLD/LAND/GO_TO/TAKEOFF Skill-first regress | **Clear** — T3/T4 + sibling suites green |
| Tip / package | **Clear** — `0.6.36`; tip-pin guardrail + ESC fence green |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.2 only RETURN_HOME Skill → `available` @ `0.6.36`; `flight.return_home` stays `not_implemented` | **PASS** |
| §0.3 grow shared vehicle gate …+RETURN_HOME; no SoftwareCapabilitySafetyGate; gate-only | **PASS** |
| §0.4 chat RETURN_HOME: `run_skill` then existing `_handle_vehicle_return_home` (empty params · ArmedAllowlist · no sim tick) | **PASS** |
| §0.5 FN-016 precedence stays (nav-back cancel before RETURN_HOME); classify unchanged | **PASS** |
| §0.6 HOLD/LAND/GO_TO/TAKEOFF Skill-first regression · SD-GO_TO OPEN untouched | **PASS** |
| §0.7 other paths unchanged (FOLLOW…/CHARGE/explain/status) | **PASS** |
| §0.8 tests T1–T5 (+ T1b no-sim · T4b FN-016 · T4c IDLE volver) · sibling stub retargets | **PASS** |
| §0.9 version/docs · no new C-xxx · SD-GO_TO row stays OPEN | **PASS** |
| §0.10 Out: sim RTL tick · home invent · FN-016 reorder · siblings · inventing cap available · copper · SD-GO_TO · voice · tip pins | **PASS** |

---

## 2. Verification (this pass)

```text
PYTHONPATH=/workspace pytest \
  tests/test_assistant_chat_skill_first_vehicle_return_home_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_takeoff_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_go_to_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_land_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_hold_b1.py \
  tests/test_capability_skills_runtime_software_b1.py \
  tests/test_assistant_vehicle_return_home_task_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py \
  tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 64 passed
```

Available Skills: explain, project_status, request_hold, request_land, request_go_to, request_takeoff, request_return_home.  
`_VEHICLE_GATE_SKILL_IDS` = HOLD + LAND + GO_TO + TAKEOFF + RETURN_HOME.  
`_handle_vehicle_return_home` body identical to pre-T27 tip (`b1a4e37`).  
Orch diff touches only the RETURN_HOME Skill-first gate block — FN-016 early-cancel lines unchanged.

Report’s full-suite claim (3931 passed / +8 vs 3923) not re-run in this pass; targeted + fences cover the IC surface.

---

## 3. Notes

**N1 — PLATFORM duplicate T27 paragraphs.** `docs/PLATFORM_CAPABILITY_VISION.md` kept both the AUTHORIZED stub and the Implemented paragraph (same hygiene as T25/T26 N1). Cleaned in this review commit. **Not blocking.**

**N2 — Finite id set growth (carry-forward).** `_VEHICLE_GATE_SKILL_IDS` remains the shared dispatch; this Buy correctly grows membership. Remaining siblings (FOLLOW…) still need their own Buys. **Not blocking.**

**N3 — Process.** Await Engineer ★ ACCEPT → tag `v0.6.36`. Cola after ★: remaining vehicle Skill-first siblings (FOLLOW…) before voz/world (phase C). **SD-GO_TO stays OPEN.** RETURN_HOME remains outside T20 sim tick set. FN-016 precedence locked by T4b.

---

## 4. Next

```text
Cursor: PASS WITH NOTES @ 722efb1 (+ review commit)
Await: Engineer ★ ACCEPT → tag v0.6.36
Skill-first phase B: HOLD ★ + LAND ★ + GO_TO ★ + TAKEOFF ★ + RETURN_HOME (pending ★)
SD-GO_TO: still OPEN
Next after ★: vehicle Skill-first siblings (FOLLOW…) — not voice yet
```
