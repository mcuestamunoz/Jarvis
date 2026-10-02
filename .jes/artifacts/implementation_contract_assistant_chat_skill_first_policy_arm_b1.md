# Implementation Contract — Chat Skill-first policy ARM/DISARM (`B1-assistant-chat-skill-first-policy-arm`)

**Project:** Jarvis  
**Date:** 2026-10-02  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.39`**

**Status:** ★ **AUTHORIZED — Claude implement now** (T29 ★ @ `v0.6.38`).  
**Parents:** [DC ★ CLOSED](design_contract_assistant_chat_skill_first_b0.md) · T29 ★ @ **`v0.6.38`** · T11 ARM UX ★ @ `v0.6.19` · T22 software Skill-first ★ @ `v0.6.31`  
**Type:** First **policy** Skill-first slice — **ARM + DISARM** together; software Safety gate-only (not vehicle gate).  
**Opens:** **`0.6.39` / `v0.6.39`**. **Cola:** **T30**

**Not:** flipping CHARGE · putting ARM/DISARM in `_VEHICLE_GATE_SKILL_IDS` · AutonomyVerb for arm · ESC/`SimulatedEscSink.arm()` · inventing new latch semantics · voice · SD-GO_TO · tip pins · live copper · widening allow-list further.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-chat-skill-first-policy-arm`** |
| 2 | Flip **both** `skill.request_arm_policy` and `skill.request_disarm_policy` → `availability=available` (version `0.6.39`). Required capability stays `safety.chat_armed_allowlist` (`available`+`software`). Provider stays `software`. Seven vehicle Skills (HOLD…PATROL) stay `available`. **`skill.request_charge` stays `stub`** |
| 3 | **Policy gate — not vehicle gate:** introduce `_POLICY_GATE_SKILL_IDS = {skill.request_arm_policy, skill.request_disarm_policy}`. These Skills MUST **not** join `_VEHICLE_GATE_SKILL_IDS`. Flow in `run_skill`: after `available` check, vehicle-gate branch unchanged; then existing `SoftwareCapabilitySafetyGate` check; on allow, if skill ∈ `_POLICY_GATE_SKILL_IDS` → gate-only `outcome="ok"` (no latch mutate, no message body required — orch owns fulfill). On Safety reject → `safety_reject`. **No** `propose_command` / ArmedAllowlist / sim / `jarvis.core` / `flight_software` in `skills_runtime` |
| 4 | **Chat ARM path:** when `try_request_arm_policy_task` matches, orch MUST call `run_skill("skill.request_arm_policy")` first. On non-ok: honest “Skill … no disponible (reason)” — no silent Task-only fallback. On ok: existing `_handle_arm_policy` **unchanged** (software latch `gate.arm()` + honesty message — never ESC/motors/drone) |
| 5 | **Chat DISARM path:** same shape with `skill.request_disarm_policy` → `_handle_disarm_policy` unchanged |
| 6 | Precedence / classify stay: explain → defer → ARM → DISARM → HOLD…PATROL. Phrase tables `VEHICLE_ARM_PHRASES` / `VEHICLE_DISARM_PHRASES` unchanged. Seven vehicle Skill-first paths stay green (regression) |
| 7 | CHARGE / explain / status: **unchanged** this Buy (CHARGE still Task-direct stub honesty) |
| 8 | Tests: chat ARM phrase (e.g. `armar` / known `VEHICLE_ARM_PHRASES`) → `run_skill` + `vehicle_arm_policy` shape + latch armed; chat DISARM → `run_skill` + `vehicle_disarm_policy` + latch disarmed; direct `run_skill` both → ok; seven vehicle Skills still ok; CHARGE still stub; tip-pin green. Retarget T21 `test_t3_vehicle_and_ops_skills_stay_stub` / available-set probes that still name ARM/DISARM as stub → CHARGE-only (and widen available-set to include both policy Skills) |
| 9 | Version **`0.6.39`**; PRIORIDAD · PLATFORM · CONNECTIONS (**no new C-xxx**). SD-GO_TO row stays **OPEN** |
| 10 | Out: CHARGE Skill-first · vehicle-gate membership for policy · ESC arm · voice · tip pins · inventing AutonomyVerb ARM · changing latch allow-list |

---

## 1. Files

| Path | Change |
|---|---|
| `capabilities/data/default_registry.json` | `skill.request_arm_policy` + `skill.request_disarm_policy` → `available` @ `0.6.39` |
| `capabilities/skills_runtime.py` | `_POLICY_GATE_SKILL_IDS` + gate-only ok after software Safety allow |
| `core/orchestrator.py` | ARM/DISARM intercepts: `run_skill` gate then existing `_handle_*_policy` |
| `tests/test_assistant_chat_skill_first_policy_arm_b1.py` | **new** |
| Retargets | T21 runtime tests that still assert ARM/DISARM stub → CHARGE-only; available-set membership +2 |
| `pyproject.toml` | `0.6.39` |
| Docs | short · SD-GO_TO still OPEN |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | chat ARM phrase (e.g. `armar`) → `run_skill("skill.request_arm_policy")`; `action=vehicle_arm_policy`; latch `armed=True`; honesty (software policy, not ESC) |
| T2 | chat DISARM phrase (e.g. `desarmar`) → `run_skill("skill.request_disarm_policy")`; `action=vehicle_disarm_policy`; latch `armed=False` |
| T3 | direct `run_skill` both policy Skills → `outcome=ok`; neither in `_VEHICLE_GATE_SKILL_IDS`; CHARGE still `skill_stub` |
| T4 | chat `hold` / `land` / `go to` / `takeoff` / `rtl` / `follow` / `patrol` still Skill-first vehicle (regression) |
| T5 | No tip pins |

---

## 3. Acceptance

- [ ] ARM + DISARM chat gated via `run_skill` · software Safety + policy gate-only · not vehicle gate · CHARGE still stub · `0.6.39`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.39`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-chat-skill-first-policy-arm (T30)
Parent tip: T29 ★ ACCEPT CLOSED @ v0.6.38. Implement now → package 0.6.39.

IC: .jes/artifacts/implementation_contract_assistant_chat_skill_first_policy_arm_b1.md
DC: .jes/artifacts/design_contract_assistant_chat_skill_first_b0.md (★ CLOSED · phase B)
T11 parent: .jes/artifacts/implementation_review_assistant_vehicle_arm_ux_b1.md
SD-GO_TO: .jes/artifacts/engineer_note_t20_goto_chat_sim_destination_debt.md (stays OPEN)

First policy Skill-first — ARM + DISARM together (software latch; not vehicle):
- Flip skill.request_arm_policy + skill.request_disarm_policy → available
  (safety.chat_armed_allowlist stays available+software)
- Add _POLICY_GATE_SKILL_IDS = {arm, disarm}. Do NOT add them to
  _VEHICLE_GATE_SKILL_IDS. After SoftwareCapabilitySafetyGate allow →
  gate-only outcome=ok (no latch mutate inside skills_runtime).
- chat armar → run_skill("skill.request_arm_policy") then existing
  _handle_arm_policy (unchanged latch + honesty). Hard Skill reject →
  no silent fallback.
- chat desarmar → run_skill("skill.request_disarm_policy") then existing
  _handle_disarm_policy.
Seven vehicle Skill-first (HOLD…PATROL) stay green. CHARGE stays stub.
Retarget T21 stub/available-set probes that still name ARM/DISARM as stub
→ CHARGE-only (+ both policy Skills in available set).
SD-GO_TO remains OPEN. No tip pins. No ACCEPT claim.
Not live ESC · not voice · not CHARGE Skill-first · not AutonomyVerb ARM.
```
