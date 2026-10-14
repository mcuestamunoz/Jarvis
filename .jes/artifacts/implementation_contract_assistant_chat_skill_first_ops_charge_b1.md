# Implementation Contract — Chat Skill-first ops CHARGE (`B1-assistant-chat-skill-first-ops-charge`)

**Project:** Jarvis  
**Date:** 2026-10-03  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.40`**

**Status:** **★ ACCEPT CLOSED** (Engineer 2026-10-03) — Cursor review **PASS WITH NOTES** · tag **`v0.6.40`**.  
**Parents:** [DC ★ CLOSED](design_contract_assistant_chat_skill_first_b0.md) · T30 ★ @ **`v0.6.39`** · T19 CHARGE Task ★ @ `v0.6.28`  
**Type:** First **ops/device** Skill-first slice — **CHARGE**; closes the last chat Skill stub.  
**Opens:** **`0.6.40` / `v0.6.40`**. **Cola:** **T31**

**Not:** real battery charging · AutonomyVerb.CHARGE · ArmedAllowlist · SoftwareCapabilitySafetyGate for CHARGE · joining `_VEHICLE_GATE_SKILL_IDS` / `_POLICY_GATE_SKILL_IDS` · inventing `ops.charge=available` · payload “carga útil” steal · voice · SD-GO_TO · tip pins · live copper.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-chat-skill-first-ops-charge`** |
| 2 | Flip **only** `skill.request_charge` → `availability=available` (version `0.6.40`). **`ops.charge` stays `not_implemented`**; provider stays **`device`**. Seven vehicle Skills + two policy Skills stay `available`. After this Buy, default registry has **no remaining Skill stubs** among the twelve chat Skills |
| 3 | **Device gate — not vehicle, not policy, not software Safety:** introduce `_DEVICE_GATE_SKILL_IDS = {skill.request_charge}` and `_device_skill_gate` (membership + provider `kind==device`; reject reason `provider_not_device` / `capability_unknown`). CHARGE MUST **not** join `_VEHICLE_GATE_SKILL_IDS` or `_POLICY_GATE_SKILL_IDS`. In `run_skill`: after `available` check, vehicle-gate branch unchanged; then **device-gate branch before** `_software_safety_allows_skill` (software Safety would reject `not_implemented`+`device`). Gate-only `outcome="ok"`; no propose_command / ArmedAllowlist / sim / latch / `jarvis.core` / `flight_software` in `skills_runtime` |
| 4 | **Chat CHARGE path:** when `try_request_charge_task` matches, orch MUST call `run_skill("skill.request_charge")` first. On non-ok: honest “Skill … no disponible (reason)” — no silent Task-only fallback. On ok: existing `_handle_ops_charge` **unchanged** (honest not-implemented Spanish · `action=ops_charge` · **no** `propose_command` / AutonomyVerb / ArmedAllowlist / sim / real battery) |
| 5 | Phrase table `OPS_CHARGE_PHRASES` / payload refusals (`carga util`, …) unchanged. Precedence stays … → PATROL → CHARGE → fallthrough |
| 6 | Seven vehicle + ARM/DISARM Skill-first stay green (regression). Explain/status unchanged |
| 7 | Tests: chat CHARGE phrase (e.g. `charge` / `cargar`) → `run_skill` + `ops_charge` shape + honesty; direct `run_skill("skill.request_charge")` → ok; not in vehicle/policy gate sets; seven vehicle + both policy Skills still ok; tip-pin green. Retarget T21 CHARGE-stub probe + T23–T30 “sibling CHARGE stub” asserts → CHARGE ok / drop stub-only CHARGE assert; widen T21 available-set +1 (`skill.request_charge`); stub set among the twelve may be empty |
| 8 | Version **`0.6.40`**; PRIORIDAD · PLATFORM · CONNECTIONS (**no new C-xxx**). SD-GO_TO row stays **OPEN**. Note: this Buy closes chat Skill-first for all twelve declared Skills (software + vehicle + policy + ops); phase C (voz/world) is next horizon — **not** this Buy |
| 9 | Out: real battery · AutonomyVerb CHARGE · inventing cap `available` · copper · SD-GO_TO · voice · tip pins · software/vehicle/policy gate misuse |

---

## 1. Files

| Path | Change |
|---|---|
| `capabilities/data/default_registry.json` | `skill.request_charge` → `available` @ `0.6.40` |
| `capabilities/skills_runtime.py` | `_DEVICE_GATE_SKILL_IDS` + `_device_skill_gate`; branch before software Safety |
| `core/orchestrator.py` | CHARGE intercept: `run_skill` gate then `_handle_ops_charge` |
| `tests/test_assistant_chat_skill_first_ops_charge_b1.py` | **new** |
| Retargets | T21 CHARGE-stub / available-set; T23–T30 sibling “CHARGE still stub” probes |
| `pyproject.toml` | `0.6.40` |
| Docs | short · SD-GO_TO still OPEN · Skill-first twelve closed |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | chat CHARGE phrase (e.g. `charge`) → `run_skill("skill.request_charge")`; `action=ops_charge`; honest not-implemented (no real battery / not AutonomyVerb) |
| T2 | direct `run_skill("skill.request_charge")` → `outcome=ok`; `ops.charge` still `not_implemented`; not in `_VEHICLE_GATE_SKILL_IDS` / `_POLICY_GATE_SKILL_IDS` |
| T3 | `run_skill` HOLD…PATROL + ARM/DISARM still ok |
| T4 | chat `hold` / `armar` / `desarmar` still Skill-first (regression sample) |
| T5 | No tip pins · payload phrase `carga util` still does **not** take CHARGE path |

---

## 3. Acceptance

- [x] CHARGE chat gated via `run_skill` · device gate-only · not vehicle/policy/software-Safety · `ops.charge` still `not_implemented` · `0.6.40`  
- [x] Cursor review · Engineer ACCEPT · tag **`v0.6.40`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-chat-skill-first-ops-charge (T31)
Parent tip: T30 ★ ACCEPT CLOSED @ v0.6.39. Implement now → package 0.6.40.

IC: .jes/artifacts/implementation_contract_assistant_chat_skill_first_ops_charge_b1.md
DC: .jes/artifacts/design_contract_assistant_chat_skill_first_b0.md (★ CLOSED · phase B)
T19 parent: .jes/artifacts/implementation_review_assistant_ops_charge_task_b1.md
SD-GO_TO: .jes/artifacts/engineer_note_t20_goto_chat_sim_destination_debt.md (stays OPEN)

Last chat Skill stub — ops CHARGE Skill-first (device gate; not vehicle/policy):
- Flip skill.request_charge → available (ops.charge stays not_implemented+device)
- Add _DEVICE_GATE_SKILL_IDS = {skill.request_charge} + _device_skill_gate
  (membership + provider kind==device). Do NOT add to _VEHICLE_GATE_SKILL_IDS
  or _POLICY_GATE_SKILL_IDS. Branch BEFORE SoftwareCapabilitySafetyGate
  (that gate would reject not_implemented+device). Gate-only outcome=ok.
- chat charge/cargar → run_skill("skill.request_charge") then existing
  _handle_ops_charge (unchanged honesty — no propose_command / AutonomyVerb /
  ArmedAllowlist / real battery). Hard Skill reject → no silent fallback.
- Payload refusals (carga util, …) stay. Precedence …→PATROL→CHARGE unchanged.
Seven vehicle + ARM/DISARM Skill-first stay green. Retarget T21 CHARGE-stub
probe + T23–T30 “CHARGE still stub” asserts → CHARGE ok / drop stub assert;
widen available-set +1. Closes twelve chat Skills Skill-first.
SD-GO_TO remains OPEN. No tip pins. No ACCEPT claim.
Not real battery · not voice · not inventing ops.charge=available · not ESC.
```
