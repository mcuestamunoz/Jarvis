# Implementation Review — Chat Skill-first vehicle GO_TO (`B1-assistant-chat-skill-first-vehicle-go-to`)

**Date:** 2026-10-02  
**Reviewer:** Cursor (forensic pass — Claude paste “Hecho — T25 implementado…”)  
**Against:** [IC](implementation_contract_assistant_chat_skill_first_vehicle_go_to_b1.md) · [report](implementation_report_assistant_chat_skill_first_vehicle_go_to_b1.md) · [DC ★](design_contract_assistant_chat_skill_first_b0.md) · [SD-GO_TO OPEN](engineer_note_t20_goto_chat_sim_destination_debt.md)  
**Tip reviewed:** `3071e5d` on `cursor/skill-first-vehicle-go-to-impl-8ac5` (parent tip T24 ★ `v0.6.33` @ `c5b6a4d` / `af71f05`)  
**Verdict:** **PASS WITH NOTES** — await Engineer ★ ACCEPT → tag **`v0.6.34`**. **No ACCEPT claim in this pass.**

**Process note:** Claude Code implemented under ★ AUTHORIZED IC. This is the independent Cursor review of record. Same-session self-PASS is not review of record.

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| GO_TO uses `SoftwareCapabilitySafetyGate` | **Clear** — in `_VEHICLE_GATE_SKILL_IDS` → shared `_vehicle_skill_gate` |
| Duplicate / divergent vehicle-gate implementation | **Clear** — one shared gate; finite id set grown to HOLD+LAND+GO_TO |
| `flight.go_to` flipped `available` | **Clear** — stays `not_implemented` @ `0.6.16`; provider still `vehicle` |
| Destination parse / invent / SD-GO_TO closed | **Clear** — `_handle_vehicle_go_to` byte-unchanged (`params={}`); T1b locks “sin destino”; debt note still **OPEN** |
| TAKEOFF…/CHARGE become runnable | **Clear** — still `skill_stub` (sibling probes retargeted to TAKEOFF) |
| Silent Task fallback on Skill reject | **Clear** — orch `outcome != "ok"` → honest “Skill request_go_to no disponible (reason).” |
| HOLD/LAND Skill-first regress | **Clear** — T3/T4 + hold/land suites green |
| Tip / package | **Clear** — `0.6.34`; tip-pin guardrail + ESC fence green |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.2 only GO_TO Skill → `available` @ `0.6.34`; `flight.go_to` stays `not_implemented` | **PASS** |
| §0.3 grow shared vehicle gate HOLD+LAND+GO_TO; no SoftwareCapabilitySafetyGate; gate-only | **PASS** |
| §0.4 chat GO_TO: `run_skill` then existing `_handle_vehicle_go_to` (empty params · ArmedAllowlist · T20 honesty · SD-GO_TO OPEN) | **PASS** |
| §0.5 HOLD/LAND Skill-first regression | **PASS** |
| §0.6 other paths unchanged (TAKEOFF…/CHARGE/explain/status) | **PASS** |
| §0.7 tests T1–T5 (+ T1b sin-destino honesty) | **PASS** |
| §0.8 version/docs · no new C-xxx · SD-GO_TO row stays OPEN | **PASS** |
| §0.9 Out: SD-GO_TO close · destination parse · siblings · inventing cap available · copper · voice · tip pins | **PASS** |

---

## 2. Verification (this pass)

```text
PYTHONPATH=/workspace pytest \
  tests/test_assistant_chat_skill_first_vehicle_go_to_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_land_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_hold_b1.py \
  tests/test_capability_skills_runtime_software_b1.py \
  tests/test_assistant_vehicle_go_to_task_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py \
  tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 49 passed
```

Available Skills: explain, project_status, request_hold, request_land, request_go_to.  
`_VEHICLE_GATE_SKILL_IDS` = HOLD + LAND + GO_TO.  
`_handle_vehicle_go_to` body identical to pre-T25 tip (`c5b6a4d`).

Report’s full-suite claim (3916 passed / +6 vs 3910) not re-run in this pass; targeted + fences cover the IC surface.

---

## 3. Notes

**N1 — PLATFORM duplicate T25 paragraphs.** `docs/PLATFORM_CAPABILITY_VISION.md` kept both the AUTHORIZED stub and the Implemented paragraph. Hygiene only — cleaned in this review commit. **Not blocking.**

**N2 — Finite id set growth (carry-forward of T24 N1).** `_VEHICLE_GATE_SKILL_IDS` remains the shared dispatch; this Buy correctly grows membership. Remaining siblings still need their own Buys. **Not blocking.**

**N3 — Process.** Await Engineer ★ ACCEPT → tag `v0.6.34`. Cola after ★: remaining vehicle Skill-first siblings (TAKEOFF…) before voz/world (phase C). **SD-GO_TO stays OPEN.**

---

## 4. Next

```text
Cursor: PASS WITH NOTES @ 3071e5d (+ review commit)
Await: Engineer ★ ACCEPT → tag v0.6.34
Skill-first phase B: HOLD ★ + LAND ★ + GO_TO (pending ★)
SD-GO_TO: still OPEN
Next after ★: vehicle Skill-first siblings (TAKEOFF…) — not voice yet
```
