# Implementation Report — Chat Skill-first ops CHARGE (`B1-assistant-chat-skill-first-ops-charge`, T31)

**Project:** Jarvis  
**Date:** 2026-10-03  
**Implementer:** Claude Code (Engineer authorization paste)  
**Contract:** [`implementation_contract_assistant_chat_skill_first_ops_charge_b1.md`](implementation_contract_assistant_chat_skill_first_ops_charge_b1.md)  
**Parents:** [DC ★ CLOSED — phase B](design_contract_assistant_chat_skill_first_b0.md) · T30 ★ ACCEPT CLOSED @ **`v0.6.39`** · T19 CHARGE Task ★ @ `v0.6.28`  
**Status:** Cursor **PASS WITH NOTES** — await Engineer ★ ACCEPT.  
**Package / tag:** `0.6.40` / pending **`v0.6.40`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/capabilities/data/default_registry.json` | `skill.request_charge` → `availability=available`, `version` → `0.6.40`. `ops.charge` capability byte-unchanged — still `not_implemented`, provider still `device` |
| `src/jarvis/capabilities/skills_runtime.py` | New `_DEVICE_GATE_SKILL_IDS = {skill.request_charge}` + `_device_skill_gate` (membership + provider `kind==device`; reject reasons `capability_unknown`/`provider_not_device`), mirroring `_vehicle_skill_gate`'s shape. In `run_skill`, the device-gate branch runs **after** the vehicle-gate branch but **before** `_software_safety_allows_skill` — `ops.charge`'s `not_implemented`+`device` shape would otherwise be rejected outright by `SoftwareCapabilitySafetyGate`. Module + function docstrings updated to describe the new branch and that T31 closes all twelve declared Skills (no stub remains) |
| `src/jarvis/core/orchestrator.py` | CHARGE intercept: on a matched `try_request_charge_task`, calls `run_skill("skill.request_charge")` first; non-`ok` → honest `"Skill request_charge no disponible (reason)."`, no silent Task-only fallback; `ok` → existing `_handle_ops_charge` unchanged byte-for-byte (honest not-implemented Spanish, `action=ops_charge`, no `propose_command`/AutonomyVerb/ArmedAllowlist/real battery) |
| `tests/test_assistant_chat_skill_first_ops_charge_b1.py` | **new** T1–T5 |
| `tests/test_capability_skills_runtime_software_b1.py` (T21's own file) | Dropped the CHARGE-stub probe entirely (renamed `test_t3_vehicle_and_ops_skills_stay_stub` → `test_t3_charge_now_ok_no_stubs_remain`, now asserting `ok`); widened the available-set assertion by `skill.request_charge`; `stub_ids` assertion now asserts the empty set |
| `tests/test_assistant_chat_skill_first_vehicle_hold_b1.py`, `..._land_b1.py`, `..._go_to_b1.py`, `..._takeoff_b1.py`, `..._return_home_b1.py`, `..._follow_b1.py`, `..._patrol_b1.py`, `test_assistant_chat_skill_first_policy_arm_b1.py` | each had a CHARGE-stub probe (the last sibling in the retarget chain) — all eight renamed and retargeted to assert `ok` instead of `reject`/`skill_stub`, since CHARGE no longer has a further stub sibling to move to |
| `tests/test_assistant_ops_charge_task_b1.py` (T19's own file) | `test_t5_seed_honesty_device_not_implemented_cascade_11_12`'s own seed-honesty assertion (`skill.availability == STUB`) flipped to `AVAILABLE`, same pattern used for every prior Task-origin file (T10, T13, T19 itself) |
| `tests/test_assistant_chat_skill_first_software_b1.py` (T22's own file) | **Regression caught by the full-suite run, not the targeted grep**: `test_t3_hold_and_charge_still_task_direct` asserted CHARGE was never routed through `run_skill` — now stale. Renamed to `test_t3_hold_and_charge_now_both_skill_first` and rewritten to assert both `skill.request_hold` and `skill.request_charge` appear in the `run_skill` spy's call ids |
| `pyproject.toml` | `0.6.40` |
| Docs | PRIORIDAD · PLATFORM · CONNECTIONS (no new C-xxx) |

**Not touched:** `ops.charge` capability (`not_implemented`, never flipped — IC's own explicit "Not"), `_handle_ops_charge` fulfill body (same honest message as T19), `_VEHICLE_GATE_SKILL_IDS`/`_POLICY_GATE_SKILL_IDS` (unchanged — CHARGE deliberately excluded from both), `OPS_CHARGE_PHRASES`/payload-refusal phrases (`"carga util"` still does not classify to CHARGE — regression-tested: T5), precedence (`…→PATROL→CHARGE` order unchanged), `AutonomyVerb` enum (no CHARGE verb invented), SD-GO_TO (untouched, still OPEN), live ESC, voice, tip-version pins (T17 guardrail re-verified green).

---

## 2. Behavior

- `charge`/`cargar` → device Skill gate (membership + provider `kind==device`, no software Safety involved) → gate-only `ok` → `_handle_ops_charge` → honest "Carga de batería solicitada, pero esta operación aún no está implementada… No es un AutonomyVerb de vuelo."
- Armed vs. disarmed makes no difference to CHARGE's message (CHARGE never touches `ArmedAllowlistSafetyGate` — unchanged from T19).
- `"carga util"` and other payload/mission lines still do not classify as CHARGE — verified directly (T5).
- Seven vehicle Skill-first (HOLD…PATROL) and both policy Skills (ARM/DISARM) behavior is byte-identical to before (regression-tested: T3/T4).
- After this Buy, `run_skill` has **no remaining stub Skill** among the twelve declared rows — every chat vehicle/ops/policy/software Skill is Skill-first.

---

## 3. Tests executed

```text
pytest tests/test_assistant_chat_skill_first_ops_charge_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_hold_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_land_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_go_to_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_takeoff_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_return_home_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_follow_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_patrol_b1.py \
  tests/test_assistant_chat_skill_first_policy_arm_b1.py \
  tests/test_capability_skills_runtime_software_b1.py \
  tests/test_assistant_ops_charge_task_b1.py -q
→ 68 passed

pytest tests/test_suite_no_tip_version_pins_b1.py tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 19 passed (T17 guardrail + T16 ESC fence both still green)

pytest tests/ -q   (first pass)
→ 1 failed, 3952 passed — tests/test_assistant_chat_skill_first_software_b1.py::
  test_t3_hold_and_charge_still_task_direct (stale T22-era assumption that
  CHARGE never calls run_skill); fixed per "What landed" above.

pytest tests/ -q   (after fix)
→ 3953 passed, 9 skipped, 0 failed
```

Diffed against this branch's pre-T31 tip (stash push/pop): baseline was `3948 passed, 9 skipped, 0 failed`. **Zero regressions** — the only delta is the 5 new T31 tests passing.

---

## 4. Remaining

None for this Buy. Chat Skill-first (DC phase B) is now closed for all twelve declared Skills. Next horizon per the DC: phase C (voice/world, phased CLI migrate) — explicitly not immediate. SD-GO_TO still awaits its own, explicit Buy.
