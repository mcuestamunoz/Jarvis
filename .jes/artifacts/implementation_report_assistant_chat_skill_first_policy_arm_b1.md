# Implementation Report — Chat Skill-first policy ARM/DISARM (`B1-assistant-chat-skill-first-policy-arm`, T30)

**Project:** Jarvis  
**Date:** 2026-10-02  
**Implementer:** Claude Code (Engineer authorization paste)  
**Contract:** [`implementation_contract_assistant_chat_skill_first_policy_arm_b1.md`](implementation_contract_assistant_chat_skill_first_policy_arm_b1.md)  
**Parents:** [DC ★ CLOSED — phase B](design_contract_assistant_chat_skill_first_b0.md) · T29 ★ ACCEPT CLOSED @ **`v0.6.38`** · T11 ARM UX ★ @ `v0.6.19` · T22 software Skill-first ★ @ `v0.6.31`  
**Status:** **Implemented** (Claude Code) — await Cursor review → Engineer ★ ACCEPT.  
**Package / tag:** `0.6.39` / pending **`v0.6.39`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/capabilities/data/default_registry.json` | `skill.request_arm_policy` + `skill.request_disarm_policy` → `availability=available`, `version` → `0.6.39`. Required capability `safety.chat_armed_allowlist` byte-unchanged — still `available`+`software` |
| `src/jarvis/capabilities/skills_runtime.py` | New `_POLICY_GATE_SKILL_IDS = {skill.request_arm_policy, skill.request_disarm_policy}` — deliberately separate from `_VEHICLE_GATE_SKILL_IDS` (neither policy Skill joins it). `run_skill` flow: vehicle-gate branch unchanged → `_software_safety_allows_skill` check (same T4-shaped `SoftwareCapabilitySafetyGate` call as before) → if skill ∈ `_POLICY_GATE_SKILL_IDS`, gate-only `outcome="ok"` with no latch mutate, checked **before** the `SKILL_ID_EXPLAIN_CONCEPT`/`SKILL_ID_PROJECT_STATUS` dispatch arms. On Safety reject, unchanged `safety_reject` path. Module docstring updated to describe the new policy-gate branch |
| `src/jarvis/core/orchestrator.py` | ARM intercept: on a matched `try_request_arm_policy_task`, calls `run_skill("skill.request_arm_policy")` first; non-`ok` → honest `"Skill request_arm_policy no disponible (reason)."`, no silent Task-only fallback; `ok` → existing `_handle_arm_policy` unchanged byte-for-byte (`gate.arm()` + honesty message). DISARM intercept: identical shape with `skill.request_disarm_policy` → `_handle_disarm_policy` |
| `tests/test_assistant_chat_skill_first_policy_arm_b1.py` | **new** T1–T5 |
| `tests/test_capability_skills_runtime_software_b1.py` (T21's own file) | `test_t3_vehicle_and_ops_skills_stay_stub` collapsed to a single CHARGE-only stub check (ARM/DISARM no longer stub); `test_t4_seed_exactly_two_available_rest_stub`'s exact-set assertion extended to include both policy Skills |
| `pyproject.toml` | `0.6.39` |
| Docs | PRIORIDAD · PLATFORM · CONNECTIONS (no new C-xxx) |

**Not touched:** `safety.chat_armed_allowlist` capability (already `available`+`software`, byte-unchanged), `_handle_arm_policy`/`_handle_disarm_policy` fulfill bodies (same `gate.arm()`/`gate.disarm()` + honesty message as T11/T14), `_VEHICLE_GATE_SKILL_IDS` (unchanged — policy Skills deliberately excluded), `skill.request_charge` (still `stub`, untouched), seven vehicle Skill-first paths (HOLD…PATROL, regression-tested), `AutonomyVerb` enum (no ARM verb invented), SD-GO_TO (untouched, still OPEN), live ESC, voice, tip-version pins (T17 guardrail re-verified green). No other test file needed a retarget — a broad search of every file referencing `skill.request_arm_policy`/`skill.request_disarm_policy` found only registry-membership checks (`<=`/`==` on skill ID sets) and Task-classify function calls, never an availability equality assertion outside T21's own file.

---

## 2. Behavior

- `armar` → Skill gate (`SoftwareCapabilitySafetyGate` allow on `safety.chat_armed_allowlist`) → gate-only `ok` → `_handle_arm_policy` → latch `gate.arm()` → `armed=True`, honest "ARMADA (latch de software ArmedAllowlist). No es armado de ESC, motores ni del dron."
- `desarmar` → same shape → `_handle_disarm_policy` → latch `gate.disarm()` → `armed=False`.
- Neither Skill is a member of `_VEHICLE_GATE_SKILL_IDS` — verified directly (T3).
- HOLD, LAND, GO_TO, TAKEOFF, RETURN_HOME, FOLLOW, and PATROL Skill-first behavior is byte-identical to before (regression-tested: T4).
- CHARGE still `reject`/`skill_stub` via `run_skill`.

---

## 3. Tests executed

```text
pytest tests/test_assistant_chat_skill_first_policy_arm_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_hold_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_land_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_go_to_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_takeoff_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_return_home_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_follow_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_patrol_b1.py \
  tests/test_capability_skills_runtime_software_b1.py \
  tests/test_assistant_vehicle_arm_ux_b1.py \
  tests/test_assistant_ops_charge_task_b1.py -q
→ 72 passed

pytest tests/test_suite_no_tip_version_pins_b1.py tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 19 passed (T17 guardrail + T16 ESC fence both still green)

pytest tests/ -q
→ 3948 passed, 9 skipped, 0 failed
```

Diffed against this branch's pre-T30 tip (stash push/pop): baseline was `3943 passed, 9 skipped, 0 failed`. **Zero regressions** — the only delta is the 5 new T30 tests passing.

---

## 4. Remaining

None for this Buy. Next candidate per the DC: ops CHARGE Skill-first (the last stub Skill), then phase C (voice/world, phased CLI migrate). SD-GO_TO still awaits its own, explicit Buy.
