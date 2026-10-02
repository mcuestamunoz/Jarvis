# Implementation Review — Chat Skill-first policy ARM/DISARM (`B1-assistant-chat-skill-first-policy-arm`)

**Date:** 2026-10-02  
**Reviewer:** Cursor (forensic pass — Claude paste “Hecho — T30 implementado…”)  
**Against:** [IC](implementation_contract_assistant_chat_skill_first_policy_arm_b1.md) · [report](implementation_report_assistant_chat_skill_first_policy_arm_b1.md) · [DC ★](design_contract_assistant_chat_skill_first_b0.md) · [T11 ARM UX ★](implementation_review_assistant_vehicle_arm_ux_b1.md) · [SD-GO_TO OPEN](engineer_note_t20_goto_chat_sim_destination_debt.md)  
**Tip reviewed:** `d887575` on `cursor/skill-first-policy-arm-impl-8ac5` (parent tip T29 ★ `v0.6.38` @ `bba3f58` / authorize `6316df6`)  
**Verdict:** **PASS WITH NOTES** — await Engineer ★ ACCEPT → tag **`v0.6.39`**. **No ACCEPT claim in this pass.**

**Process note:** Claude Code implemented under ★ AUTHORIZED IC. This is the independent Cursor review of record. Same-session self-PASS is not review of record.

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| Policy Skills join `_VEHICLE_GATE_SKILL_IDS` | **Clear** — neither in vehicle set; both in `_POLICY_GATE_SKILL_IDS` only (T3 + direct assert) |
| Latch mutate inside `skills_runtime` | **Clear** — policy branch returns gate-only `ok`; no `gate.arm`/`disarm` / ArmedAllowlist imports |
| `_handle_arm_policy` / `_handle_disarm_policy` rewritten | **Clear** — bodies byte-identical to pre-T30 tip (`6316df6`) |
| `safety.chat_armed_allowlist` flipped / kind changed | **Clear** — still `available`+`software` @ `0.6.25` |
| CHARGE becomes runnable | **Clear** — still `skill_stub` |
| Silent Task fallback on Skill reject | **Clear** — orch non-ok → honest “Skill request_*_policy no disponible (reason).” |
| ESC / SimulatedEscSink from policy path | **Clear** — handlers unchanged honesty; ESC fence green |
| Seven vehicle Skill-first regress | **Clear** — T4 + sibling suites green |
| Tip / package | **Clear** — `0.6.39`; tip-pin guardrail + ESC fence green |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.2 both policy Skills → `available` @ `0.6.39`; cap/provider unchanged; CHARGE stub; seven vehicle Skills stay available | **PASS** |
| §0.3 `_POLICY_GATE_SKILL_IDS`; not vehicle gate; software Safety then gate-only ok; no latch in runtime | **PASS** |
| §0.4 chat ARM: `run_skill` then existing `_handle_arm_policy` | **PASS** |
| §0.5 chat DISARM: `run_skill` then existing `_handle_disarm_policy` | **PASS** |
| §0.6 precedence/classify/phrases unchanged; seven vehicle Skill-first green | **PASS** |
| §0.7 CHARGE / explain / status unchanged | **PASS** |
| §0.8 tests T1–T5 · T21 stub/available-set retarget CHARGE-only +2 available | **PASS** |
| §0.9 version/docs · no new C-xxx · SD-GO_TO OPEN | **PASS** |
| §0.10 Out: CHARGE Skill-first · vehicle-gate membership · ESC · voice · tip pins · AutonomyVerb ARM · allow-list change | **PASS** |

---

## 2. Verification (this pass)

```text
PYTHONPATH=/workspace python3 -m pytest \
  tests/test_assistant_chat_skill_first_policy_arm_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_hold_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_land_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_go_to_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_takeoff_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_return_home_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_follow_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_patrol_b1.py \
  tests/test_capability_skills_runtime_software_b1.py \
  tests/test_assistant_vehicle_arm_ux_b1.py \
  tests/test_assistant_ops_charge_task_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py \
  tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 91 passed
```

`_handle_arm_policy` / `_handle_disarm_policy` SHA256 identical to `6316df6`.  
`_VEHICLE_GATE_SKILL_IDS` size 7; `_POLICY_GATE_SKILL_IDS` size 2; no overlap.

Report’s full-suite claim (3948 passed / +5 vs 3943) not re-run in this pass; targeted + fences cover the IC surface.

---

## 3. Notes

**N1 — Last stub Skill is CHARGE.** After this Buy, only `skill.request_charge` remains stub among chat Skills. Next Skill-first candidate is ops CHARGE (device shape — different from policy/vehicle). **Not blocking.**

**N2 — Process.** Await Engineer ★ ACCEPT → tag `v0.6.39`. Cola after ★: CHARGE Skill-first or phase C (voz/world). **SD-GO_TO stays OPEN.**

---

## 4. Next

```text
Cursor: PASS WITH NOTES @ d887575 (+ review commit)
Await: Engineer ★ ACCEPT → tag v0.6.39
Skill-first: seven AutonomyVerbs ★ + policy ARM/DISARM (pending ★)
SD-GO_TO: still OPEN
Next after ★: CHARGE Skill-first (last stub) — not voice yet
```
