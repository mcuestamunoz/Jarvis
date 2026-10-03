# Jarvis — Platform Capability Vision

**Status:** Directional — not implementation authority  
**Type:** Vision / To-be  
**Date:** 2026-09-10  
**Scope:** Future Skills, Capabilities, and physical-system software architecture

---

## 1) Purpose

Preserve the long-horizon platform architecture for Jarvis so that, when that work begins, design follows a modular capability model instead of a drone-coupled monolith.

This document is a **future architecture note**. It is **not** an Implementation Contract, not an as-is map, and **must not** be used as evidence of implemented behavior.

---

## 2) Document Boundaries (anti-drift contract)

- **Current system truth (as-is):**
  - `docs/ARCHITECTURE.md`
  - `docs/system_map/*`
- **Execution queue truth (what to implement next):**
  - `docs/IMPLEMENTATION_TASKS.md`
  - `.jes/state/engineering_state.json`
- **Engineering readiness vision (separate to-be axis):**
  - `docs/ENGINEERING_READINESS_VISION.md`
- **Platform capability vision (this document):**
  - `docs/PLATFORM_CAPABILITY_VISION.md`
- **Knowledge / explain vision (separate to-be axis — epoch `0.6.x`):**
  - `docs/JARVIS_KNOWLEDGE_VISION.md` (`ontology/` — not catalog, not this file’s skills tree)

Rule: this vision evolves independently until an Engineer-approved design/implementation contract opens that work.  
Do **not** create `flight_software/`, `capabilities/`, or `vehicle_profiles/` packages from this note alone.  
Only implemented and validated behavior moves into `ARCHITECTURE.md` and `docs/system_map/*`.

When that work arrives, open a JES design/investigation artifact (e.g. Skill / Capability Architecture Contract) derived from this document — do not treat this file as the executable contract.

---

## 3) Core discovery

The vision of Jarvis should not be building **“a drone with an assistant”**, but building a **platform able to operate multiple physical systems**, reusing intelligence, skills, and capabilities across them.

The drone will be the **first complex physical system** on which this architecture is developed.

---

## 4) `flight_software/` will be independent

Flight software must exist outside any concrete `workspace`.

```text
jarvis/
├── core/
├── engineering/
├── catalog/
├── flight_software/
├── capabilities/
├── vehicle_profiles/
└── workspaces/
```

### Separation

**Workspace**

> Which system I am designing.

**Vehicle Profile**

> Which physical/hardware configuration that system needs.

**Flight Software**

> How that vehicle type is controlled.

**Capabilities / Skills**

> What capabilities Jarvis can provide.

This allows the same software/capability to be reused across many systems.

---

## 5) Flight Software ≠ Assistant

The drone software must be split conceptually.

```text
flight_software/
├── flight_control/
└── autonomy/
```

### `flight_control`

Responsible for physical behavior:

* HAL
* drivers
* sensors
* state estimation
* attitude control
* rate control
* position control
* mixer
* actuators
* safety

Its mission:

> **Keep the vehicle physically controllable.**

It does not know who Jarvis is.  
It does not know how to talk.  
It does not know what task the user wants.

### `autonomy`

Responsible for:

* missions
* navigation
* planning
* trajectories
* behaviors
* autonomous execution

Examples:

```text
TAKEOFF
HOLD
GO_TO
FOLLOW
RETURN_HOME
LAND
PATROL
```

---

## 6) Assistant as a reusable layer

The Assistant must sit above vehicles/systems.

```text
                 JARVIS
                    │
                 ASSISTANT
                    │
          ┌─────────┼─────────┐
          │         │         │
        DRONE      ROBOT     HOME
```

The Assistant does not belong to the drone.

Example:

> “Jarvis, ven a buscarme.”

The Assistant produces an **intent/task**, not motor commands.

```text
Intent
  ↓
Task
  ↓
Required capabilities
  ↓
Provider
  ↓
Execution
```

---

## 7) Central concept: `Capability`

A **Capability** is a capacity a system can provide.

Examples:

```text
navigation
localization
voice_input
speech_output
vision
object_detection
flight_control
ground_control
manipulation
engineering_calculation
simulation
home_automation
```

A drone might provide:

```text
flight_control
navigation
localization
vision
```

A ground robot might provide:

```text
ground_control
navigation
localization
vision
manipulation
```

The Assistant does not need to know the physical implementation.

---

## 8) Skills compose capabilities

Example:

```text
FOLLOW_PERSON
```

requires:

```text
perception
person_tracking
localization
navigation
```

and may run via a drone or a robot.

Another example:

```text
SEARCH_OBJECT
```

might combine:

```text
perception
mapping
navigation
object_detection
reporting
```

A skill must not be coupled to a single device.

---

## 9) Resolution system

Future architecture, conceptually:

```text
User / Event
     ↓
Intent
     ↓
Task
     ↓
Required Capabilities
     ↓
Capability Resolver
     ↓
Available Provider
     ↓
Skill Implementation
     ↓
Execution
```

Example:

```text
"Ve a la cocina"
       ↓
   navigate_to
       ↓
Who provides navigation?
       ↓
     drone_01
       ↓
 execution
```

Later it could be:

```text
navigate_to
     ↓
robot_01
```

without modifying the skill.

---

## 10) Safety between Assistant and hardware

Fundamental rule:

```text
Assistant
   ↓
Intent
   ↓
Skill
   ↓
Capability
   ↓
Safety Gate
   ↓
Flight Control
   ↓
Actuators
```

The Assistant **never** directly controls motors.

It may request:

```text
GO_TO(position)
FOLLOW(person)
LAND()
```

but the physical system may reject the operation:

```text
REJECTED
reason:
  localization_invalid
```

Safety must have authority over physical actuation.

**First concrete instance (T4, `B1-assistant-software-safety-bridge`, ★ ACCEPT CLOSED @ `v0.6.12`):** for the two software-only capabilities the Assistant already has (`ontology.explain`/`engineering.continuity`, §13 below), the Intent → Task → capability → **Safety** link in the diagram above is now real code, not just this diagram — `SoftwareCapabilitySafetyGate` must `allow` before either Task is emitted. There was still no `Flight Control`/`Actuators` step for the Assistant to reach at T4 time — no vehicle verb, no `HOLD`/`GO_TO`/`LAND`.

**First vehicle verb (T6, `B1-assistant-vehicle-hold-task`, ★ ACCEPT CLOSED @ `v0.6.14`):** HOLD is the first Task kind to reach past **Safety** toward `Flight Control` — `Intent → Task(request_hold) → flight.hold → ArmedAllowlistSafetyGate (fresh, never armed) → propose_command/submit_command`. The chain still stops at Safety in practice (disarmed → `reject`/`"disarmed"`/`"not_attempted"`) — `Flight Control`/`Actuators` are reached structurally (the same C4 autonomy surface, same types) but nothing executes and nothing arms on this path. **T7 (`B1-assistant-vehicle-land-task`, ★ ACCEPT CLOSED @ `v0.6.15`)**, **T8 (`B1-assistant-vehicle-go-to-task`, ★ ACCEPT CLOSED @ `v0.6.16`)**, **T9 (`B1-assistant-vehicle-takeoff-task`, ★ ACCEPT CLOSED @ `v0.6.17`)**, and **T10 (`B1-assistant-vehicle-return-home-task`, ★ ACCEPT CLOSED @ `v0.6.18`)** repeat the exact same chain for LAND (`flight.land`), GO_TO (`flight.go_to`), TAKEOFF (`flight.takeoff`), and RETURN_HOME (`flight.return_home`) — all four later verbs proposed with empty `params`, no coordinate/altitude/home-point parsing — each its own separate provider, same disarmed-gate honesty, same structural reach with nothing executed. Basic mando set CLOSED. T11 arm UX ★ @ `v0.6.19` and T12 FOLLOW ★ @ `v0.6.20` shipped — see §13. T13 PATROL ★ @ `v0.6.21` closes the vehicle-verb cola. T14 allow-list widen IC ★ AUTHORIZED @ `0.6.22` — CHARGE / copper remain later Buys.

---

## 11) Versioning

Do not think in monolithic versions:

```text
v1 = drone
v2 = autonomous drone
v3 = drone with voice
v4 = assistant
```

Prefer each capability evolving independently.

Example:

```text
Flight Control    1.2
Autonomy          0.8
Voice             1.1
Perception        0.4
Assistant         2.0
```

A system may combine different versions.

---

## 12) End-state sketch

```text
                         JARVIS
                           │
             ┌─────────────┼─────────────┐
             │             │             │
        ENGINEERING    INTELLIGENCE   CAPABILITIES
             │             │             │
       design/sim      assistant       voice
       validation      memory          vision
                       planning        perception
             │             │             │
             └─────────────┼─────────────┘
                           │
                    PHYSICAL SYSTEMS
                           │
              ┌────────────┼────────────┐
              │            │            │
            DRONE        ROBOT         CAR
              │            │            │
        flight_control  control      control
        autonomy        autonomy     autonomy
```

Assistant, Voice, Perception, Memory, Navigation, etc. can become reusable resources across systems.

**Placement (2026-09-30):** Ontology **CLOSED @ `v0.6.0`**. Assistant A0–A6 **★ CLOSED @ `v0.6.5`** (`jarvis explain` + maps + Continuity Conceptos). T0/T1 Assistant Task seam **★ CLOSED @ `v0.6.8`/`v0.6.9`** (`explain_concept`/`defer_to_continuity`). T2 (`B1-capability-registry-product-fill`) **★ ACCEPT CLOSED @ `v0.6.10`**: C1's `CapabilityRegistry.load_default()` is no longer empty — `ontology.explain`/`engineering.continuity`, both `available` via one `software` provider each. T3 (`B1-assistant-task-registry-coherence`) **★ ACCEPT CLOSED @ `v0.6.11`**: the Assistant soft-checks every requested capability id against that default registry before emitting a Task — membership only, still not a dispatcher. T4 (`B1-assistant-software-safety-bridge`) **★ ACCEPT CLOSED @ `v0.6.12`**: the first Assistant→Safety link — a new `SoftwareCapabilitySafetyGate` must `allow` (id known, `available`, `software`-kind provider) before a software Task is emitted; `default_safety_gate()` stays `RejectAllSafetyGate`, still no vehicle verbs. T5 (`B1-capability-skills-seed`) **★ ACCEPT CLOSED @ `v0.6.13`**: the checked-in seed's `skills` array is no longer always-empty either — two declared-only `stub` rows naming the same two capability verticals; still no Skill runtime, and the Assistant's Task classify never looks these rows up. T6 (`B1-assistant-vehicle-hold-task`) **★ ACCEPT CLOSED @ `v0.6.14`**: the **first vehicle Task kind** — a finite HOLD phrase table classifies to `Task(request_hold)` requiring the new `flight.hold` capability (seeded `not_implemented`/`vehicle`, never `available`); fulfilled entirely in `core/orchestrator.py` via the existing C4 autonomy surface with a fresh, **never-armed** `ArmedAllowlistSafetyGate` — honest reject, never a claim of flight. T7 (`B1-assistant-vehicle-land-task`) **★ ACCEPT CLOSED @ `v0.6.15`**: the **second vehicle Task kind**, same seam — a finite LAND phrase table classifies to `Task(request_land)` requiring `flight.land` (its own separate `not_implemented`/`vehicle` row); precedence extends to explain → Continuity defer → HOLD → LAND → fallthrough. T8 (`B1-assistant-vehicle-go-to-task`) **★ ACCEPT CLOSED @ `v0.6.16`**: the **third vehicle Task kind** — GO_TO, requiring `flight.go_to` (its own separate row); `propose_command`'s `params` always empty this Buy, no coordinate/waypoint parsing; precedence extends to explain → Continuity defer → HOLD → LAND → GO_TO → fallthrough. T9 (`B1-assistant-vehicle-takeoff-task`) **★ ACCEPT CLOSED @ `v0.6.17`**: the **fourth vehicle Task kind** — TAKEOFF, requiring `flight.takeoff` (its own separate row, empty `params`, no altitude parse); precedence extends to explain → Continuity defer → HOLD → LAND → GO_TO → TAKEOFF → fallthrough. T10 (`B1-assistant-vehicle-return-home-task`) **★ ACCEPT CLOSED @ `v0.6.18`**: the **fifth vehicle Task kind** — RETURN_HOME closes basic mando; precedence extends to explain → Continuity defer → HOLD → LAND → GO_TO → TAKEOFF → RETURN_HOME → fallthrough. `ArmedAllowlistSafetyGate`'s own allow-list stays unwidened (`{HOLD, LAND, GO_TO}` — TAKEOFF/RETURN_HOME/FOLLOW not included). T11 arm UX ★ @ `v0.6.19` and T12 FOLLOW ★ @ `v0.6.20` extend the chat path — see §13. T13 PATROL ★ @ `v0.6.21` closes the vehicle-verb cola. T14 allow-list ★ @ `v0.6.25` · T17 tip-pin cleanup ★ @ `v0.6.26` · T18 fulfill docstring honesty ★ @ `v0.6.27` · T19 ops CHARGE ★ @ `v0.6.28` · T20 chat sim copper ★ @ `v0.6.29` (SD-GO_TO OPEN) · T21 Skills runtime ★ @ `v0.6.30` (T18–T21 block CLOSED) · T22 Skill-first software ★ @ `v0.6.31` (phase A CLOSED). T23 vehicle HOLD Skill-first ★ @ `v0.6.32`. T24 LAND Skill-first ★ @ `v0.6.33`. Next: remaining vehicle Skill-first siblings → voz/world (phased CLI). Parked until assembly: ESC live · sim TAKEOFF/RH/FOLLOW/PATROL · real CHARGE battery. R4 LLM cite later.

---

## 13) Next work when that moment arrives

**Lectura humana (qué es “scaffold”, qué hace cada carpeta):**  
[`docs/ARCHITECTURE.md`](ARCHITECTURE.md) **§1a — Fase C en lenguaje llano**.

**Do not start by coding.**

**Design contract (★★ CLOSED 2026-09-20 with amendment):**  
[`.jes/artifacts/design_contract_fase_c_skill_capability_architecture.md`](../.jes/artifacts/design_contract_fase_c_skill_capability_architecture.md)  

**C1 (ACCEPT CLOSED, tag `v0.5.0`):**  
[`.jes/artifacts/implementation_contract_fase_c_capability_registry_scaffold_b1.md`](../.jes/artifacts/implementation_contract_fase_c_capability_registry_scaffold_b1.md) — schemas + **empty** Capability Registry stub, `src/jarvis/capabilities/` → package **`0.5.0`**. No flight runtime, no execution path. See [implementation report](../.jes/artifacts/implementation_report_fase_c_capability_registry_scaffold_b1.md).

**T2 (`B1-capability-registry-product-fill`, ★ ACCEPT CLOSED @ `v0.6.10`):** scaffold ≠ empty forever — [`.jes/artifacts/implementation_contract_capability_registry_product_fill_b1.md`](../.jes/artifacts/implementation_contract_capability_registry_product_fill_b1.md) fills C1's checked-in `data/default_registry.json` with the first honest, non-empty product seed: `ontology.explain`/`engineering.continuity` (both `CapabilityAvailability.AVAILABLE`, new this Buy) via one `ProviderKind.SOFTWARE` (new this Buy) provider each — the same two capability strings T0/T1's `jarvis.intelligence.assistant_task` already require on `Task.required_capability_ids`, id-synced by test. Still **software-only**: no flight/vehicle/device row, no dispatcher method. See [implementation report](../.jes/artifacts/implementation_report_capability_registry_product_fill_b1.md).

**T3 (`B1-assistant-task-registry-coherence`, ★ ACCEPT CLOSED @ `v0.6.11`):** [`.jes/artifacts/implementation_contract_assistant_task_registry_coherence_b1.md`](../.jes/artifacts/implementation_contract_assistant_task_registry_coherence_b1.md) — the Assistant soft-checks ids against default registry; still not a dispatcher. Before returning a `Task`, `assistant_task.py` now verifies every `required_capability_ids` entry exists in `CapabilityRegistry.load_default()` (`get_capability(id) is not None`, membership only — no `availability` read, no provider call). Unknown id → refuse (`None`), no `task_kind` written. `assistant_task.py` now imports `jarvis.capabilities.registry.CapabilityRegistry` (a new, explicitly authorized one-way edge); `registry.py` still never imports `jarvis.intelligence`. See implementation report.

**T4 (`B1-assistant-software-safety-bridge`, ★ ACCEPT CLOSED @ `v0.6.12`):** [`.jes/artifacts/implementation_contract_assistant_software_safety_bridge_b1.md`](../.jes/artifacts/implementation_contract_assistant_software_safety_bridge_b1.md) — the Assistant now soft-checks ids against default registry; still not a dispatcher. The first Assistant→Safety link: a new `SoftwareCapabilitySafetyGate` (`gate_id="software_capability"`) in `jarvis.capabilities.safety`, run immediately after T3's membership check and immediately before a Task's `task_kind` write, on both `try_explain_concept_task` and `try_defer_to_continuity_task`. `allow` iff every requested capability id is `available` and bound to a `software`-kind provider; otherwise `reject` with one of five finite reasons (`unparseable_action_id`/`empty_capabilities`/`capability_unknown`/`capability_unavailable`/`provider_not_software`). `default_safety_gate()` stays `RejectAllSafetyGate`; `ArmedAllowlistSafetyGate`'s allow-list is untouched. `safety.py` now imports `jarvis.capabilities.registry`/`schemas` but still never `jarvis.intelligence`. See implementation report.

**T5 (`B1-capability-skills-seed`, ★ ACCEPT CLOSED @ `v0.6.13`):** [`.jes/artifacts/implementation_contract_capability_skills_seed_b1.md`](../.jes/artifacts/implementation_contract_capability_skills_seed_b1.md) — the registry declares two Skills stub that require `ontology.explain`/`engineering.continuity`; catalog honest, the Assistant still emits Tasks (T0–T4), no Skill runtime. Fills C1's checked-in `data/default_registry.json` `skills` array — always `[]` since `v0.5.0` — with `skill.explain_concept` (→ `["ontology.explain"]`) and `skill.project_status` (→ `["engineering.continuity"]`), both `availability=stub` (declared catalog rows only — marking them `available` would falsely imply a live Skill runner). Capabilities/providers rows, `assistant_task.py`, both Safety gates, the orchestrator, and Continuity ranking are all **byte-unchanged** (`git diff` confirms zero lines touched in any of them) — the Assistant's Task classify never looks up `skills()` before emitting a Task. Existing registry reject-on-load still catches a skill referencing an unknown capability id. The 39-file T2-era "Fase C isolation" cascade that still asserted `skills() == []` (plus three dedicated tests in T2's/C1's/C2's own suites) was adapted to assert the new honest two-skill shape instead, without weakening any isolation/no-dispatch check. See implementation report.

**T6 (`B1-assistant-vehicle-hold-task`, ★ ACCEPT CLOSED @ `v0.6.14`) — first vehicle Task kind:** [`.jes/artifacts/implementation_contract_assistant_vehicle_hold_task_b1.md`](../.jes/artifacts/implementation_contract_assistant_vehicle_hold_task_b1.md) — parented by [DC ★ CLOSED](../.jes/artifacts/design_contract_assistant_vehicle_hold_task_b0.md) and [INV ★ CLOSED](../.jes/artifacts/investigation_report_assistant_vehicle_hold_task_b0.md). `jarvis.intelligence.assistant_task.try_request_hold_task` classifies a finite HOLD phrase table (`jarvis.config.VEHICLE_HOLD_PHRASES`) into `Task(request_hold, required_capability_ids=["flight.hold"])`, T3-style membership-checked only (**no** `SoftwareCapabilitySafetyGate` — that gate only ever allows `available`+`software`, and `flight.hold` is intentionally neither). Registry gains a third capability/provider/skill row: `flight.hold` (`not_implemented`, `provider.flight_hold`, `kind=vehicle`) and `skill.request_hold` (`stub`). Fulfilled entirely in `core/orchestrator.py`'s new `_handle_vehicle_hold` — `propose_command(AutonomyVerb.HOLD)` + `submit_command(cmd, gate)` through the existing C4 autonomy surface, with a **fresh, never-armed** `ArmedAllowlistSafetyGate` constructed per call (`arm()` is never called on this path); `default_safety_gate()` stays `RejectAllSafetyGate`, untouched. The chat message surfaces `result.safety.outcome`/`reason`/`result.execution` verbatim (disarmed → `reject`/`"disarmed"`/`"not_attempted"`) — never a claim of executed flight. Precedence: explain → Continuity defer → HOLD → fallthrough, enforced both by orchestrator call order and by `try_request_hold_task`'s own internal guards. `assistant_task.py` still never imports `jarvis.flight_software`/`jarvis.vehicle_profiles`/`jarvis.core` — `core/orchestrator.py` is the one, newly-authorized edge into `flight_software.autonomy`. Several Fase C/T2/T5-era test-suite boundary checks ("core/adapters never reference `flight_software`/`ArmedAllowlistSafetyGate`", "seed has exactly two capabilities/providers/skills, all software") were adapted to allow-list this one new, intentional exception, without weakening any other isolation/no-dispatch check. LAND (shipped T7 below) /GO_TO, `arm()` on the product path, and voice ingress were explicitly out this Buy. See implementation report.

**T7 (`B1-assistant-vehicle-land-task`, ★ ACCEPT CLOSED @ `v0.6.15`) — second vehicle Task kind:** [`.jes/artifacts/implementation_contract_assistant_vehicle_land_task_b1.md`](../.jes/artifacts/implementation_contract_assistant_vehicle_land_task_b1.md) — parented by [DC ★ CLOSED](../.jes/artifacts/design_contract_assistant_vehicle_land_task_b0.md); reuses T6's own INV (HOLD INV ★ CLOSED — "seams already mapped, no new INV"). Same seam as T6, own verb: `jarvis.intelligence.assistant_task.try_request_land_task` classifies a finite LAND phrase table (`jarvis.config.VEHICLE_LAND_PHRASES`) into `Task(request_land, required_capability_ids=["flight.land"])`, T3-style membership-checked only (no `SoftwareCapabilitySafetyGate`, same reasoning as HOLD). Registry gains a fourth capability/provider/skill row: `flight.land` (`not_implemented`, its own **separate** `provider.flight_land`, `kind=vehicle` — DC §0 row 5 explicitly locks no provider merge) and `skill.request_land` (`stub`); all HOLD/software rows are kept, byte-unchanged. Fulfilled entirely in `core/orchestrator.py`'s new `_handle_vehicle_land` — thin duplication of `_handle_vehicle_hold`'s own shape (DC's "Not" list excludes collapsing HOLD+LAND into a generic verb framework this Buy; `_handle_vehicle_hold` itself is left byte-for-byte unchanged so HOLD cannot regress) — `propose_command(AutonomyVerb.LAND)` + `submit_command(cmd, gate)` through the same C4 surface, same fresh-never-armed `ArmedAllowlistSafetyGate` policy; `action="vehicle_land"`. Precedence extends to explain → Continuity defer → HOLD → LAND → fallthrough — `try_request_land_task` internally refuses explain-, Continuity-, *and* HOLD-shaped input, so a direct caller cannot have HOLD's own phrases stolen by LAND. `assistant_task.py` still never imports `jarvis.flight_software`/`jarvis.vehicle_profiles`/`jarvis.core`; `core/orchestrator.py` remains the one authorized edge. The same allow-listed boundary tests T6 adapted, plus the cascade's skill/capability-count assertions, were extended to a four-row shape; HOLD's own regression suite re-verified green. GO_TO (shipped T8 below) and `arm()` on the product path were out this Buy. See implementation report.

**T8 (`B1-assistant-vehicle-go-to-task`, ★ ACCEPT CLOSED @ `v0.6.16`) — third vehicle Task kind:** [`.jes/artifacts/implementation_contract_assistant_vehicle_go_to_task_b1.md`](../.jes/artifacts/implementation_contract_assistant_vehicle_go_to_task_b1.md) — parented by [DC ★ CLOSED](../.jes/artifacts/design_contract_assistant_vehicle_go_to_task_b0.md); reuses HOLD's own INV — no new INV. Same seam again: `jarvis.intelligence.assistant_task.try_request_go_to_task` classifies a finite GO_TO phrase table (`jarvis.config.VEHICLE_GO_TO_PHRASES`) into `Task(request_go_to, required_capability_ids=["flight.go_to"])`, T3-style membership-checked only. Registry gains a fifth capability/provider/skill row: `flight.go_to` (`not_implemented`, its own **separate** `provider.flight_go_to`, `kind=vehicle`) and `skill.request_go_to` (`stub`); all HOLD/LAND/software rows are kept, byte-unchanged. Fulfilled entirely in `core/orchestrator.py`'s new `_handle_vehicle_go_to` — thin sibling of `_handle_vehicle_hold`/`_handle_vehicle_land` (both left byte-for-byte unchanged, verified via `git diff` showing zero removed lines) — `propose_command(AutonomyVerb.GO_TO, params={})` (empty `params` — **no coordinate/waypoint parsing** anywhere this Buy, DC §0 row 9) + `submit_command(cmd, gate)` through the same C4 surface, same fresh-never-armed `ArmedAllowlistSafetyGate` policy; `action="vehicle_go_to"`. Precedence extends to explain → Continuity defer → HOLD → LAND → GO_TO → fallthrough — `try_request_go_to_task` internally refuses explain-, Continuity-, HOLD-, *and* LAND-shaped input. `assistant_task.py` still never imports `jarvis.flight_software`/`jarvis.vehicle_profiles`/`jarvis.core`. The same `core/orchestrator.py`-only allow-list exceptions T6 established needed no further change (they exclude the file by identity, not by verb); the cascade's skill/capability-count assertions were extended to a five-row shape. HOLD's and LAND's own regression suites both re-verified green. TAKEOFF (shipped T9 below)/FOLLOW/RETURN_HOME/PATROL were out this Buy. See implementation report.

**T9 (`B1-assistant-vehicle-takeoff-task`, ★ ACCEPT CLOSED @ `v0.6.17`) — fourth vehicle Task kind:** [`.jes/artifacts/implementation_contract_assistant_vehicle_takeoff_task_b1.md`](../.jes/artifacts/implementation_contract_assistant_vehicle_takeoff_task_b1.md) — parented by [DC ★ CLOSED](../.jes/artifacts/design_contract_assistant_vehicle_takeoff_task_b0.md); reuses HOLD's own INV — no new INV. Same seam again: `jarvis.intelligence.assistant_task.try_request_takeoff_task` classifies a finite TAKEOFF phrase table (`jarvis.config.VEHICLE_TAKEOFF_PHRASES`) into `Task(request_takeoff, required_capability_ids=["flight.takeoff"])`, T3-style membership-checked only. Registry gains a sixth capability/provider/skill row: `flight.takeoff` (`not_implemented`, its own **separate** `provider.flight_takeoff`, `kind=vehicle`) and `skill.request_takeoff` (`stub`); all HOLD/LAND/GO_TO/software rows are kept, byte-unchanged. Fulfilled entirely in `core/orchestrator.py`'s new `_handle_vehicle_takeoff` — thin sibling of the three earlier fulfill methods (all left byte-for-byte unchanged, `git diff` confirms zero removed/modified lines anywhere in the file) — `propose_command(AutonomyVerb.TAKEOFF, params={})` (empty `params`, no altitude parsing, DC §0 row 9) + `submit_command(cmd, gate)` through the same C4 surface, same fresh-never-armed `ArmedAllowlistSafetyGate` policy; `action="vehicle_takeoff"`. Precedence extends to explain → Continuity defer → HOLD → LAND → GO_TO → TAKEOFF → fallthrough — `try_request_takeoff_task` internally refuses explain-, Continuity-, HOLD-, LAND-, *and* GO_TO-shaped input. `assistant_task.py` still never imports `jarvis.flight_software`/`jarvis.vehicle_profiles`/`jarvis.core`. `ArmedAllowlistSafetyGate`'s own allow-list is unwidened (still `{HOLD, LAND, GO_TO}` — DC §0 row 7 note: TAKEOFF would get `verb_not_allowed` rather than `allow` if ever armed, though the always-disarmed product path yields `"disarmed"` either way). The same `core/orchestrator.py`-only allow-list exceptions T6 established needed no further change; the cascade's skill/capability-count assertions were extended to a six-row shape (run proactively this time, immediately after wiring the orchestrator — see T7's/T8's own reports for the cascade-timing lesson this followed). HOLD's, LAND's, and GO_TO's own regression suites all re-verified green. RETURN_HOME (T10 below)/`arm()`/FOLLOW/PATROL remain out. See implementation report.

**T10 (`B1-assistant-vehicle-return-home-task`, ★ ACCEPT CLOSED @ `v0.6.18`) — fifth vehicle Task kind (closes basic mando set):** [`.jes/artifacts/implementation_contract_assistant_vehicle_return_home_task_b1.md`](../.jes/artifacts/implementation_contract_assistant_vehicle_return_home_task_b1.md) — parented by [DC ★ CLOSED](../.jes/artifacts/design_contract_assistant_vehicle_return_home_task_b0.md); reuses HOLD's own INV — no new INV. Same seam: `try_request_return_home_task` classifies `VEHICLE_RETURN_HOME_PHRASES` into `Task(request_return_home, required_capability_ids=["flight.return_home"])`, membership only. Registry gains a seventh capability/provider/skill row: `flight.return_home` (`not_implemented`, separate `provider.flight_return_home`, `kind=vehicle`) and `skill.request_return_home` (`stub`). Fulfilled in `_handle_vehicle_return_home` — `propose_command(AutonomyVerb.RETURN_HOME, params={})` + fresh never-armed `ArmedAllowlistSafetyGate`; allow-list still `{HOLD, LAND, GO_TO}` (unwidened). Exact match only — short words (`casa`/`home`/`volver`) do not steal longer craft lines. Precedence: explain → Continuity defer → HOLD → LAND → GO_TO → TAKEOFF → RETURN_HOME → fallthrough. Prior `_handle_vehicle_*` bodies untouched vs `v0.6.17`. FOLLOW/PATROL/CHARGE remain out. See [report](../.jes/artifacts/implementation_report_assistant_vehicle_return_home_task_b1.md) · [review ★ ACCEPT CLOSED](../.jes/artifacts/implementation_review_assistant_vehicle_return_home_task_b1.md).

**T11 (`B1-assistant-vehicle-arm-ux`, ★ ACCEPT CLOSED @ `v0.6.19`) — Safety policy latch (not a sixth verb):** [`.jes/artifacts/implementation_contract_assistant_vehicle_arm_ux_b1.md`](../.jes/artifacts/implementation_contract_assistant_vehicle_arm_ux_b1.md) — parented by [DC ★ CLOSED](../.jes/artifacts/design_contract_assistant_vehicle_arm_ux_b0.md). Chat `armar`/`desarmar` → Task `request_arm_policy`/`request_disarm_policy` requiring `safety.chat_armed_allowlist` (`available`, software provider) through the T4 `SoftwareCapabilitySafetyGate`. Orchestrator owns **one** process-scoped `ArmedAllowlistSafetyGate`; ARM/DISARM toggle it; the five vehicle fulfills **retarget** to that shared gate. Allow-list stays `{HOLD, LAND, GO_TO}` — after ARM, HOLD/LAND/GO_TO become `allow`/`not_implemented`; TAKEOFF/RETURN_HOME stay `verb_not_allowed`. Honesty: software Safety latch only — never ESC/motors/flight. See [review](../.jes/artifacts/implementation_review_assistant_vehicle_arm_ux_b1.md) · [report](../.jes/artifacts/implementation_report_assistant_vehicle_arm_ux_b1.md).

**T12 (`B1-assistant-vehicle-follow-task`, ★ ACCEPT CLOSED @ `v0.6.20`) — sixth vehicle Task kind:** [`.jes/artifacts/implementation_contract_assistant_vehicle_follow_task_b1.md`](../.jes/artifacts/implementation_contract_assistant_vehicle_follow_task_b1.md) — parented by [DC ★ CLOSED](../.jes/artifacts/design_contract_assistant_vehicle_follow_task_b0.md); reuses HOLD INV — no new INV. Same seam: `try_request_follow_task` classifies `VEHICLE_FOLLOW_PHRASES` into `Task(request_follow, required_capability_ids=["flight.follow"])`, membership only. Registry adds `flight.follow` (`not_implemented`, separate `provider.flight_follow`, `kind=vehicle`) + `skill.request_follow` stub. Fulfilled in `_handle_vehicle_follow` — `propose_command(AutonomyVerb.FOLLOW, params={})` through the **shared** T11 chat ArmedAllowlist (not a fresh gate). Allow-list unwidened — default `disarmed`; after `armar` → `verb_not_allowed` (like TAKEOFF/RETURN_HOME). No person/target parse. Precedence: … → RETURN_HOME → **FOLLOW** → fallthrough. See [review ★](../.jes/artifacts/implementation_review_assistant_vehicle_follow_task_b1.md).

**T13 (`B1-assistant-vehicle-patrol-task`, ★ ACCEPT CLOSED @ `v0.6.21`) — seventh vehicle Task kind (last C4 AutonomyVerb in chat):** [`.jes/artifacts/implementation_contract_assistant_vehicle_patrol_task_b1.md`](../.jes/artifacts/implementation_contract_assistant_vehicle_patrol_task_b1.md) — parented by [DC ★ CLOSED](../.jes/artifacts/design_contract_assistant_vehicle_patrol_task_b0.md); reuses HOLD INV — no new INV. Same seam as FOLLOW: `try_request_patrol_task` classifies `VEHICLE_PATROL_PHRASES` into `Task(request_patrol, required_capability_ids=["flight.patrol"])`, membership only. Registry adds `flight.patrol` (`not_implemented`, separate `provider.flight_patrol`, `kind=vehicle`) + `skill.request_patrol` stub. Fulfilled in `_handle_vehicle_patrol` — `propose_command(AutonomyVerb.PATROL, params={})` through the **shared** T11 chat ArmedAllowlist. Allow-list unwidened — default `disarmed`; after `armar` → `verb_not_allowed`. No waypoint/route parse. Precedence: … → FOLLOW → **PATROL** → fallthrough. CHARGE / allow-list widen / copper remain later Buys. See [review ★](../.jes/artifacts/implementation_review_assistant_vehicle_patrol_task_b1.md).

**T17 (`B1-suite-tip-pin-cleanup`, ★ ACCEPT CLOSED @ `v0.6.26`) — suite honesty, not product:** retires all `pyproject.toml` tip/package version pin tests (~72 functions including the former ~52 red historical pins). Policy going forward: **do not** assert exact package tip version from the suite; guardrail `tests/test_suite_no_tip_version_pins_b1.py`. Registry capability `version` field checks remain valid product asserts. No behavior change. See [IC](../.jes/artifacts/implementation_contract_suite_tip_pin_cleanup_b1.md).

**T14 (`B1-assistant-vehicle-allowlist-widen`, ★ ACCEPT CLOSED @ `v0.6.25`) — Safety-policy widen, not a new Task kind:** [`.jes/artifacts/implementation_contract_assistant_vehicle_allowlist_widen_b1.md`](../.jes/artifacts/implementation_contract_assistant_vehicle_allowlist_widen_b1.md) — parented by [DC ★ CLOSED](../.jes/artifacts/design_contract_assistant_vehicle_allowlist_widen_b0.md); T13 PATROL ★ @ `v0.6.21` · T16 ESC fence ★ @ `v0.6.24`; no new INV. Widens `ArmedAllowlistSafetyGate._ALLOWED_VERBS` from `{HOLD,LAND,GO_TO}` to all seven C4 `AutonomyVerb` values with a chat Task (adds `TAKEOFF`/`RETURN_HOME`/`FOLLOW`/`PATROL`). Latch API unchanged (`arm`/`disarm`/`armed`/`evaluate`); disarmed path unchanged (`reject`/`disarmed`). After `armar`, every chat vehicle verb now resolves to Safety `allow` + execution `not_implemented` — never `"executed"`. **Allow still ≠ execute:** `SimAutonomyExecutor` remains HOLD/LAND/GO_TO-only in sim; chat fulfills never wire it. No new Task kind, phrase table, capability, or skill — cascade stays 10 caps / 11 skills. `_handle_arm_policy`'s Spanish copy updated to match (no longer claims TAKEOFF/RETURN_HOME stay `verb_not_allowed`). Report: `.jes/artifacts/implementation_report_assistant_vehicle_allowlist_widen_b1.md`.

**T18 (`B1-orchestrator-fulfill-docstring-honesty`, ★ ACCEPT CLOSED @ `v0.6.27`) — docs-only close of T14 N1:** intercept comments + four fulfill docstrings for TAKEOFF/RETURN_HOME/FOLLOW/PATROL now match the seven-verb allow-list (armed → `allow`/`not_implemented`, not `verb_not_allowed`). Zero behavior change. See [review ★](../.jes/artifacts/implementation_review_orchestrator_fulfill_docstring_honesty_b1.md).

**T19 (`B1-assistant-ops-charge-task`, ★ ACCEPT CLOSED @ `v0.6.28`) — first ops Task kind:** `try_request_charge_task` + `OPS_CHARGE_PHRASES` → `Task(request_charge, ops.charge)`. CHARGE ≠ `AutonomyVerb` — membership only, no ArmedAllowlist / SoftwareCapabilitySafetyGate; `_handle_ops_charge` never `propose_command`/sim. Registry: `ops.charge` `not_implemented` + `provider.ops_charge` `kind=device` + `skill.request_charge` stub (cascade 11/12). Exact match refuses payload lines. Not real battery hardware. See [review ★](../.jes/artifacts/implementation_review_assistant_ops_charge_task_b1.md).

**T20 (`B1-assistant-chat-sim-copper`, ★ ACCEPT CLOSED @ `v0.6.29`) — first allow → sim bridge:** after chat Safety `allow` for HOLD/LAND, `core/orchestrator.py` ticks a lazy `SimAutonomyExecutor` (C40) and reports the sim result in-message; `submit_command`'s `execution` stays `"not_implemented"` byte-unchanged. TAKEOFF/RETURN_HOME/FOLLOW/PATROL: allow, no tick. GO_TO: honest sim-unavailable-without-a-target — listed debt **SD-GO_TO** ([note](../.jes/artifacts/engineer_note_t20_goto_chat_sim_destination_debt.md)). Never live ESC/copper/motors. See [review ★](../.jes/artifacts/implementation_review_assistant_chat_sim_copper_b1.md).

**T21 (`B1-capability-skills-runtime-software`, ★ ACCEPT CLOSED @ `v0.6.30`) — first Skill runner, software only:** `jarvis.capabilities.skills_runtime.run_skill` — software Skills `skill.explain_concept` / `skill.project_status` `available`; vehicle/ops stay stub. Chat still Task-direct at ship time (Skill-first = next block T22). N1/N2 layering notes = forward friction for Skill-first. See [review ★](../.jes/artifacts/implementation_review_capability_skills_runtime_software_b1.md).

**T22 (`B1-assistant-chat-skill-first-software`, ★ ACCEPT CLOSED @ `v0.6.31`) — first Skill-first chat slice (phase A):** explain + Continuity defer go through `run_skill`; vehicle/ops still Task-direct. See [review ★](../.jes/artifacts/implementation_review_assistant_chat_skill_first_software_b1.md).

**T23 (`B1-assistant-chat-skill-first-vehicle-hold`, ★ ACCEPT CLOSED @ `v0.6.32`) — first vehicle Skill-first (phase B HOLD):** `skill.request_hold` → `available`; vehicle gate without `SoftwareCapabilitySafetyGate` (`flight.hold` stays `not_implemented`); chat `hold` → `run_skill` then `_handle_vehicle_hold`. See [review ★](../.jes/artifacts/implementation_review_assistant_chat_skill_first_vehicle_hold_b1.md).

**T24 (`B1-assistant-chat-skill-first-vehicle-land`, ★ ACCEPT CLOSED @ `v0.6.33`) — second vehicle Skill-first:** LAND + shared vehicle gate for HOLD+LAND (T23 N2). See [review ★](../.jes/artifacts/implementation_review_assistant_chat_skill_first_vehicle_land_b1.md).

**T25 (`B1-assistant-chat-skill-first-vehicle-go-to`, ★ ACCEPT CLOSED @ `v0.6.34`) — third vehicle Skill-first:** `skill.request_go_to` → `available`; HOLD/LAND/GO_TO share `_vehicle_skill_gate`; `flight.go_to` stays `not_implemented`. Chat `go to` → `run_skill` then existing `_handle_vehicle_go_to` (empty params + ArmedAllowlist + T20 sim-copper honesty). **SD-GO_TO stays OPEN** — gate only, no destination parse/invent. See [review ★](../.jes/artifacts/implementation_review_assistant_chat_skill_first_vehicle_go_to_b1.md).

**T26 (`B1-assistant-chat-skill-first-vehicle-takeoff`, ★ ACCEPT CLOSED @ `v0.6.35`) — fourth vehicle Skill-first:** `skill.request_takeoff` → `available`; HOLD/LAND/GO_TO/TAKEOFF share `_vehicle_skill_gate`; `flight.takeoff` stays `not_implemented`. Chat `takeoff` → `run_skill` then existing `_handle_vehicle_takeoff` (empty params + ArmedAllowlist + allow/`not_implemented` honesty — **no** sim tick). SD-GO_TO untouched/OPEN. See [review ★](../.jes/artifacts/implementation_review_assistant_chat_skill_first_vehicle_takeoff_b1.md).

**T27 (`B1-assistant-chat-skill-first-vehicle-return-home`, ★ ACCEPT CLOSED @ `v0.6.36`) — fifth vehicle Skill-first:** `skill.request_return_home` → `available`; HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME share `_vehicle_skill_gate`; `flight.return_home` stays `not_implemented`. Chat RTL → `run_skill` then existing `_handle_vehicle_return_home` (empty params + ArmedAllowlist + allow/`not_implemented` honesty — **no** sim tick). FN-016 wizard nav-back cancel still wins over this gate — unreordered. SD-GO_TO untouched/OPEN. See [review ★](../.jes/artifacts/implementation_review_assistant_chat_skill_first_vehicle_return_home_b1.md).

**T28 (`B1-assistant-chat-skill-first-vehicle-follow`, ★ ACCEPT CLOSED @ `v0.6.37`) — sixth vehicle Skill-first:** `skill.request_follow` → `available`; HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME/FOLLOW share `_vehicle_skill_gate`; `flight.follow` stays `not_implemented`. Chat `follow` → `run_skill` then existing `_handle_vehicle_follow` (empty params + ArmedAllowlist + allow/`not_implemented` honesty — **no** sim tick). No track/target invent. SD-GO_TO untouched/OPEN. See [review ★](../.jes/artifacts/implementation_review_assistant_chat_skill_first_vehicle_follow_b1.md).

**T29 (`B1-assistant-chat-skill-first-vehicle-patrol`, ★ ACCEPT CLOSED @ `v0.6.38`) — seventh and last vehicle Skill-first:** `skill.request_patrol` → `available`; HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME/FOLLOW/PATROL share `_vehicle_skill_gate` — **closes the full seven-verb chat AutonomyVerb Skill-first set**; `flight.patrol` stays `not_implemented`. Chat `patrol` → `run_skill` then existing `_handle_vehicle_patrol` (empty params + ArmedAllowlist + allow/`not_implemented` honesty — **no** sim tick). Remaining Skill-first candidates are policy/ops (ARM/DISARM/CHARGE). SD-GO_TO untouched/OPEN. See [review ★](../.jes/artifacts/implementation_review_assistant_chat_skill_first_vehicle_patrol_b1.md).

**T30 (`B1-assistant-chat-skill-first-policy-arm`, ★ ACCEPT CLOSED @ `v0.6.39`) — first policy Skill-first:** `skill.request_arm_policy` + `skill.request_disarm_policy` → `available`; **not** in `_VEHICLE_GATE_SKILL_IDS` — after `SoftwareCapabilitySafetyGate` allow (on `safety.chat_armed_allowlist`, available+software), `_POLICY_GATE_SKILL_IDS` returns gate-only `ok` (no latch mutate inside `skills_runtime`); chat `armar`/`desarmar` → `run_skill` then existing `_handle_arm_policy` / `_handle_disarm_policy` unchanged (software ArmedAllowlist latch — never ESC/motors/drone). Seven vehicle Skill-first (HOLD…PATROL) stay green. Remaining Skill-first candidate is ops CHARGE. SD-GO_TO untouched/OPEN. See [review ★](../.jes/artifacts/implementation_review_assistant_chat_skill_first_policy_arm_b1.md).

**T31 (`B1-assistant-chat-skill-first-ops-charge`, Implemented (Claude Code) @ `0.6.40`, await Cursor review → Engineer ★ ACCEPT) — first ops/device Skill-first; last chat Skill stub:** `skill.request_charge` → `available`; **not** in `_VEHICLE_GATE_SKILL_IDS` / `_POLICY_GATE_SKILL_IDS` — new `_DEVICE_GATE_SKILL_IDS` + `_device_skill_gate` (membership + provider `kind==device`), checked **before** the software Safety branch (that gate would reject `ops.charge`'s `not_implemented`+`device` shape outright); gate-only `ok`. Chat `charge`/`cargar` → `run_skill` then existing `_handle_ops_charge` unchanged (honest not-implemented — never AutonomyVerb / ArmedAllowlist / real battery). `ops.charge` stays `not_implemented`+`device`. Seven vehicle Skill-first + both policy Skills stay green. **Closes chat Skill-first for all twelve declared Skills** — no stub remains. SD-GO_TO untouched/OPEN. See [IC](../.jes/artifacts/implementation_contract_assistant_chat_skill_first_ops_charge_b1.md).

**C2 (ACCEPT CLOSED, package stays `0.5.0` — no new tag):**  
[`.jes/artifacts/implementation_contract_fase_c_intent_safety_stub_b1.md`](../.jes/artifacts/implementation_contract_fase_c_intent_safety_stub_b1.md) — typed Intent ingress + Safety/Authority gate **interface**, added to `src/jarvis/capabilities/` (`intent.py` + `safety.py`). Only `TerminalIntentAdapter` produces a real `Intent`; voice/radio/api always raise `NotImplementedError`. The only shipped gate factory, `default_safety_gate()`, always returns `RejectAllSafetyGate` — no `AllowAllSafetyGate` exists under `src/`. See [review](../.jes/artifacts/implementation_review_fase_c_intent_safety_stub_b1.md) · [report](../.jes/artifacts/implementation_report_fase_c_intent_safety_stub_b1.md).

**C3 (ACCEPT CLOSED, tag `v0.5.1`):**  
**Engineer amendment on the C3 IC (does not replace it): "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."** Everything landed under `flight_software/` and `vehicle_profiles/` is a Python platform scaffold — typed contracts, `SimulatedImuHal`, a profile smoke helper — not the production flight controller. The real `flight_control` runtime/firmware will be C++, built in later Buys with its own IC (path/build TBD there); this Buy creates no C++ tree and no CMake anywhere in the repo.  
[`.jes/artifacts/implementation_contract_fase_c_first_fc_rung_b1.md`](../.jes/artifacts/implementation_contract_fase_c_first_fc_rung_b1.md) — first `flight_control` rung: **HAL + simulated IMU sample acquisition only**. Opens `src/jarvis/flight_software/flight_control/` and `src/jarvis/vehicle_profiles/` **on disk for the first time** → package **`0.5.1`**. No filtering, no state estimation, no attitude/rate/position controller, no mixer, no ESC/PWM, no autonomy verbs — none of it exists yet. `SimulatedImuHal` is deterministic and never touches real hardware. Craft catalog `flight_controller` (BOM identity) and `flight_software.flight_control` (this control spine) are explicitly different systems of record — see the module docstrings. See [review](../.jes/artifacts/implementation_review_fase_c_first_fc_rung_b1.md) · [implementation report](../.jes/artifacts/implementation_report_fase_c_first_fc_rung_b1.md).

**First rung stub @ 0.5.1 != controlled flight** — estimation, control, mixer, ESC, and real ELRS/CRSF decode remain future ICs (C5 below lands the typed dual-role *model*, still simulated only).

**C4 (ACCEPT CLOSED with C5 @ tag `v0.5.3` — no `v0.5.2` tag):**  
**Same Engineer scaffold discipline continues: "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."**  
[`.jes/artifacts/implementation_contract_fase_c_autonomy_surface_b1.md`](../.jes/artifacts/implementation_contract_fase_c_autonomy_surface_b1.md) — typed **autonomy command surface**: `AutonomyVerb` (`TAKEOFF`/`HOLD`/`GO_TO`/`FOLLOW`/`RETURN_HOME`/`LAND`/`PATROL`), `propose_command()`, `submit_command()`. Opens `src/jarvis/flight_software/autonomy/`. Every `submit_command` call goes through `SafetyGate.evaluate(...)` first; with `RejectAllSafetyGate`, `HOLD`/`LAND` always `outcome=reject`/`execution="not_attempted"`. See [review PASS](../.jes/artifacts/implementation_review_fase_c_autonomy_surface_b1.md) · [report](../.jes/artifacts/implementation_report_fase_c_autonomy_surface_b1.md). Release: [docs truth-sync](../.jes/artifacts/engineer_note_docs_truth_sync_fase_c_2026_09_20.md).

**Command surface ≠ flyable autonomy** — nothing here holds, lands, takes off, navigates, or actuates.

**C5 (ACCEPT CLOSED @ tag `v0.5.3`, same block as C4):**  
**Same Engineer scaffold discipline: production radio/ELRS stack is a future IC (may be native/C++) — not this Buy.**  
[`.jes/artifacts/implementation_contract_fase_c_radio_dual_role_b1.md`](../.jes/artifacts/implementation_contract_fase_c_radio_dual_role_b1.md) — typed **radio dual-role model** in `src/jarvis/capabilities/radio.py`: `RadioStubFrame` → `SimulatedRadioIngress` → `RadioDualRoleResult` (`Intent` and/or `AuthoritySignal`). `RadioIntentAdapter.parse(...)` still raises `NotImplementedError`. Optional `SafetyRequest.authority_signal_id` for traceability — RejectAll unchanged. See [review PASS](../.jes/artifacts/implementation_review_fase_c_radio_dual_role_b1.md) · [report](../.jes/artifacts/implementation_report_fase_c_radio_dual_role_b1.md). Plain language: [`ARCHITECTURE.md` §1a](ARCHITECTURE.md).

**Dual-role stub ≠ live ELRS** — no real link is decoded and authority never implies Safety `allow`.

**C6 (ACCEPT CLOSED, tag `v0.5.4`):**  
**Same Engineer scaffold discipline continues: "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."**  
[`.jes/artifacts/implementation_contract_fase_c_imu_filtering_rung_b1.md`](../.jes/artifacts/implementation_contract_fase_c_imu_filtering_rung_b1.md) — the **second** `flight_control` rung: `ImuLowPassFilter` (deterministic first-order EMA, `alpha` constructor parameter, default `0.2`, rejects `alpha` outside `(0, 1]`) applied per-axis to `accel_mps2`/`gyro_rad_s`. `filter_sample(raw: ImuSample) -> ImuSample` — reuses C3's `ImuSample` verbatim, no parallel type. This is **sensing post-process, not estimation**: no quaternion, no Euler angles, no Madgwick/Mahony/EKF, no attitude output. `read_filtered(hal, filt)` pipes `SimulatedImuHal.read_imu()` through the filter; `vehicle_profiles.run_hal_imu_filter_smoke()` is the pytest-visible smoke path. Package/tag **`0.5.4`**. See [review PASS](../.jes/artifacts/implementation_review_fase_c_imu_filtering_rung_b1.md) · [report](../.jes/artifacts/implementation_report_fase_c_imu_filtering_rung_b1.md). After C6: [process lock](../.jes/artifacts/engineer_note_fase_c_process_lock_after_c6_2026_09_20.md).

**Filter rung ≠ attitude / ≠ controlled flight** — state estimation remains a separate future IC (decide demonstration before opening Safety-real or C++ fronts).

**C7 (ACCEPT CLOSED, tag `v0.5.5`):**  
**Same Engineer scaffold discipline continues: "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."**  
[`.jes/artifacts/implementation_contract_fase_c_attitude_estimation_rung_b1.md`](../.jes/artifacts/implementation_contract_fase_c_attitude_estimation_rung_b1.md) — the **third** `flight_control` rung: `ComplementaryAttitudeEstimator` (gyro integration fused with accel-derived tilt via a small-angle proportional correction, `gain` constructor parameter, default `0.02`, rejects `gain` outside `(0, 1]`). Exactly **one** algorithm — explicitly **not** Mahony/Madgwick/EKF/UKF/MEKF by name (no bias/integral state, no gradient descent, no covariance). `update(sample: ImuSample) -> AttitudeState` emits a unit quaternion `(w, x, y, z)` mapping body → **`enu`** world frame plus body angular rate. **Hard cut:** no magnetometer, no GPS/baro, no online gyro-bias learning, no position/velocity. Reuses C6's `ImuLowPassFilter`/`ImuSample` directly. Package/tag **`0.5.5`**. See [review PASS](../.jes/artifacts/implementation_review_fase_c_attitude_estimation_rung_b1.md) · [report](../.jes/artifacts/implementation_report_fase_c_attitude_estimation_rung_b1.md).

**Attitude stub ≠ flight-verified attitude / ≠ controlled flight** — controller, mixer, and ESC remain future ICs, each its own front.

**C8 (ACCEPT CLOSED, tag `v0.5.6`):**  
**Same Engineer scaffold discipline continues: "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."**  
[`.jes/artifacts/implementation_contract_fase_c_attitude_controller_rung_b1.md`](../.jes/artifacts/implementation_contract_fase_c_attitude_controller_rung_b1.md) — the **fourth** `flight_control` rung: `PdAttitudeController` — `omega_cmd = kp * e_rot - kd * omega_measured`, where `e_rot` is the body-frame small-angle rotation vector from the C7 estimate toward an `AttitudeSetpoint` (extracted from the shortest-path error quaternion), and `omega_measured` is `AttitudeState.omega_body_rad_s`. `kp` (default `6.0`) must be `> 0`; `kd` (default `0.6`) must be `>= 0`; both finite. Exactly **one** controller — no cascaded rate PID, LQR, MPC, or INDI. `compute(setpoint, state) -> BodyRateCommand` — the output is a **body-rate number only**: no motor thrust, no mixer matrix, no PWM/ESC, no collective-thrust channel, no position/velocity loop. Not wired to C4: `AutonomyVerb.HOLD` is never auto-routed here, and this module never calls `submit_command`. Package/tag **`0.5.6`**. See [review PASS](../.jes/artifacts/implementation_review_fase_c_attitude_controller_rung_b1.md) · [implementation report](../.jes/artifacts/implementation_report_fase_c_attitude_controller_rung_b1.md).

**Controller stub ≠ flying / ≠ motor commands** — nothing here moves a motor; mixer, ESC, and real hardware remain future fronts, one at a time per the process lock.

**C9 (ACCEPT CLOSED, tag `v0.5.7`):**  
**Same Engineer scaffold discipline continues: "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."**  
[`.jes/artifacts/implementation_contract_fase_c_mixer_rung_b1.md`](../.jes/artifacts/implementation_contract_fase_c_mixer_rung_b1.md) — the **fifth** `flight_control` rung: `QuadXMixer` — a fixed linear allocation matrix for **one documented quadrotor-X layout** (motors `0..3` = FR/FL/RL/RR, 45° off body axes). `mix(collective, rates: BodyRateCommand) -> MotorForceCommand` clamps `collective` to `[0, 1]` and emits four `[0, 1]`-clamped motor force numbers. **Honesty-critical simplification, documented explicitly:** C8's `BodyRateCommand.omega_body_rad_s` is a body *rate*, not a true body *torque* — this B1 mixer treats it directly as the roll/pitch/yaw mix channels to teach allocation geometry, without claiming rate ≡ torque physically and without inventing a second controller to bridge that gap. `roll_scale`/`pitch_scale`/`yaw_scale` (default `0.05` each) must be finite and `>= 0`. Not wired to C4: no auto-routing of `AutonomyVerb.HOLD`. Package/tag **`0.5.7`**. See [review PASS](../.jes/artifacts/implementation_review_fase_c_mixer_rung_b1.md) · [implementation report](../.jes/artifacts/implementation_report_fase_c_mixer_rung_b1.md).

**Mixer stub ≠ ESC / ≠ flying** — four numbers only; no PWM, DShot, ESC UART, or GPIO exists anywhere, and no claim that any motor spins.

**C10 (ACCEPT CLOSED, tag `v0.5.8`):**  
**Same Engineer scaffold discipline continues: "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."**  
[`.jes/artifacts/implementation_contract_fase_c_esc_pwm_stub_rung_b1.md`](../.jes/artifacts/implementation_contract_fase_c_esc_pwm_stub_rung_b1.md) — the **sixth** `flight_control` rung: `encode_motor_forces(forces, *, min_us=1000, max_us=2000) -> EscPwmCommand` linearly maps each C9 motor force onto a PWM pulse width in microseconds (`force=0 → min_us`, `force=1 → max_us`; `min_us`/`max_us` must be finite with `min_us < max_us`). **Exactly one encoding** — classic PWM-in-µs; no DShot/Oneshot/Multishot shipped alongside it. `SimulatedEscSink` records the resulting `EscPwmCommand` **in memory only** (`armed` starts `False`; `apply(cmd)` always records the command but only reports `applied=True` while armed — no `RPi.GPIO`/`pigpio`/serial/socket I/O anywhere). Not wired to C4. Package/tag **`0.5.8`**. See [review PASS](../.jes/artifacts/implementation_review_fase_c_esc_pwm_stub_rung_b1.md) · [implementation report](../.jes/artifacts/implementation_report_fase_c_esc_pwm_stub_rung_b1.md).

**ESC/PWM stub ≠ hardware ESC / ≠ flying** — arming is a plain in-memory flag; no pin, port, or socket exists anywhere, and no claim that any motor spins.

**C11 (ACCEPT CLOSED, tag `v0.5.9`):**  
**Same Engineer scaffold discipline continues: "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."**  
[`.jes/artifacts/implementation_contract_fase_c_controlled_flight_sim_tip_b1.md`](../.jes/artifacts/implementation_contract_fase_c_controlled_flight_sim_tip_b1.md) — the **C0 §7 wooden-ladder tip**: `ToyQuadAttitudePlant` advances a toy, attitude-only, explicitly-not-product-physics dynamics from **`MotorForceCommand`** (C9 forces, not PWM) and emits the next `ImuSample` **consistent with its own true attitude** — closing C3→C10 into a real closed loop. `run_controlled_flight_sim_smoke()` demonstrates measurable recovery: from a documented 15° initial tilt, the true tilt error drops below 2° within 200 steps; `run_open_loop_baseline_smoke()` shows the same plant with no correction stays at a constant 15° (no passive righting), proving the loop is doing real work. **Rate ≠ torque remains open** — C9's mixer still treats body rate as its mix channel, and this plant does not silently insert a rate→torque controller to hide that; it uses its own separately-documented toy force→angular-acceleration map.

**Also fixed, disclosed (not the primary scope of this Buy, but required for its own pass criterion to be honestly achievable):** a real sign bug in C7's `ComplementaryAttitudeEstimator` (tagged `v0.5.5`, ACCEPT CLOSED) — its accel correction had the cross-product argument order reversed, converging estimates *away* from the true tilt for any non-level input (confirmed even at 0.1°). Every pre-existing C7 test only fed already-level accel, so this was never exercised. One-line fix (swapped argument order) plus a new regression test in C7's own test file. See [implementation report](../.jes/artifacts/implementation_report_fase_c_controlled_flight_sim_tip_b1.md) for the full before/after proof.

**Sim closed-loop tip ≠ flying / ≠ hardware-verified flight / ≠ physics-accurate sim** — this is a toy demonstration that the software ladder closes on itself in simulation; no motor spins, no real vehicle exists.

**C12 (ACCEPT CLOSED, tag `v0.5.10`) — the rate≠torque gap above is now CLOSED:**  
**Same Engineer scaffold discipline continues: "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."**  
[`.jes/artifacts/implementation_contract_fase_c_rate_torque_bridge_b1.md`](../.jes/artifacts/implementation_contract_fase_c_rate_torque_bridge_b1.md) — a typed honesty bridge: `LinearRateTorqueBridge.convert(rates: BodyRateCommand) -> BodyTorqueCommand`, **one feedforward map only** (`tau_i = gain_i * omega_cmd_i` per axis, scalar or per-axis gains, each finite and `> 0`) — **not** a cascaded rate PID (no `kp * (omega_cmd - omega_measured)` term, no integral/derivative state anywhere). `BodyTorqueCommand.tau_body` is explicitly **normalized/dimensionless torque-like**, never claimed as Newton-metres of any real vehicle. `QuadXMixer.mix(collective, torques: BodyTorqueCommand)` is **migrated** — it no longer accepts a bare `BodyRateCommand` at all, no silent dual API (verified: passing a rate directly raises `AttributeError`, not a quiet misinterpretation). C11's closed-loop tip was re-verified through the bridge and is unchanged (`15° → 0.252°` in 200 steps, identical to before migration) — **no gain retune was needed**, since the bridge's default `gain=1.0` is a mathematical no-op relative to the mixer's pre-migration direct pass-through. Package file **`0.5.10`**. See [implementation report](../.jes/artifacts/implementation_report_fase_c_rate_torque_bridge_b1.md).

**Bridge ≠ rate loop product / ≠ physical N·m / ≠ flying** — a single named feedforward step exists now instead of an implicit rate-as-torque assumption; nothing here claims real torque units, a hardware-closed rate loop, or flight.

**C13 (`B1-fase-c-cpp-flight-control-scaffold`, **ACCEPT CLOSED**, tag `v0.5.11`) — the first material C++ scaffold for `flight_control`:**
[`.jes/artifacts/implementation_contract_fase_c_cpp_flight_control_scaffold_b1.md`](../.jes/artifacts/implementation_contract_fase_c_cpp_flight_control_scaffold_b1.md) opens **`native/flight_control/`** — a **host-only** C++17 tree, built with CMake ≥ 3.16, living outside `src/jarvis/` (locked path). It mirrors the Python wooden ladder's algorithmic shape module-for-module (`filter`/`attitude`/`controller`/`rate_torque`/`mixer`/`plant`), including the C11 Amendment A accel-correction sign fix from day one, and ships a `fc_closed_loop_smoke` executable that runs the same closed-loop tip: seeded at a 15° tilt, the true tilt error recovers to **0.252°** after 200 steps — the same numeric result as the Python ladder, since both port the identical formulas, though bit-identity was explicitly **not** required by the IC (only "tilt error decreases and recovers"). No GPIO/pigpio/`/dev/mem`/serial/DShot/socket anywhere in the tree (grep-verified), no PX4/ArduPilot vendored, no MCU flash or board bring-up in this Buy. The Python `flight_software/` package is **untouched except a docstring pointer** — it remains the design guide and the craft platform; nothing here replaces it. See [implementation report](../.jes/artifacts/implementation_report_fase_c_cpp_flight_control_scaffold_b1.md).

**C++ scaffold ≠ flying / ≠ hardware flight controller / ≠ firmware on any board / ≠ replacing Python craft SoT** — this is a host desktop build proving the same algorithmic ladder in a second language, nothing more.

**C14 (`B1-fase-c-cpp-esc-pwm-stub`, ★ ACCEPT CLOSED @ tag `v0.5.12`) — steel-ladder parity for the ESC/PWM encoding stub:**
[`.jes/artifacts/implementation_contract_fase_c_cpp_esc_pwm_stub_b1.md`](../.jes/artifacts/implementation_contract_fase_c_cpp_esc_pwm_stub_b1.md) ports Python C10's `encode_motor_forces`/`SimulatedEscSink` into **`native/flight_control/esc.{hpp,cpp}`** — the same linear force→PWM-µs map (`force=0 → min_us`, `force=1 → max_us`, default `1000`–`2000`, `min_us < max_us` enforced), and the same in-memory `SimulatedEscSink` (`armed` starts `false`; `apply(cmd)` always records the command but only reports `applied=true` while armed, `applied=false`/`reason="disarmed"` otherwise). A **separate** `fc_esc_pwm_smoke` executable (18 checks, all passing) keeps the C13 closed-loop tip smoke focused — `fc_closed_loop_smoke` was re-run and is **byte-identical**: `15° → 0.252°` in 200 steps, unaffected by this Buy. No GPIO/pigpio/`/dev/mem`/serial/DShot/Oneshot/Multishot/socket anywhere in the new sources (grep-verified). Python `esc.py` is untouched — re-verified with the same before/after values. See [report](../.jes/artifacts/implementation_report_fase_c_cpp_esc_pwm_stub_b1.md) · [review](../.jes/artifacts/implementation_review_fase_c_cpp_esc_pwm_stub_b1.md).

**C++ ESC stub ≠ hardware write / ≠ ESC online / ≠ motors spinning** — this closes the C++ tree's module parity with the Python wooden ladder (filter/attitude/controller/rate_torque/mixer/esc, plus the plant tip); nothing here drives a real ESC or claims a propeller turns.

**C15 (`B1-fase-c-cpp-unit-tests`, ★ ACCEPT CLOSED @ tag `v0.5.13`) — deepen host C++ verification:**
[`.jes/artifacts/implementation_contract_fase_c_cpp_unit_tests_b1.md`](../.jes/artifacts/implementation_contract_fase_c_cpp_unit_tests_b1.md) adds a real unit-test framework — **Catch2 v3, pinned to release tag `v3.7.1`** (commit `fa43b77429ba76c462b1898d6cd2f2d7a9416b14`), fetched via CMake `FetchContent` (network needed once at first configure; offline thereafter) — plus **26 `TEST_CASE`s / \~494 assertions**, at least one per steel rung (filter, attitude, controller, rate_torque, mixer, esc), under `native/flight_control/tests/`. `ctest` now runs **28 entries** total: the 26 unit cases (individually discovered via `catch_discover_tests`) plus both pre-existing smoke binaries, all green. **Behavior freeze honored exactly**: `git diff --stat` on every pre-existing rung source (`filter.cpp`…`esc.cpp`/`plant.cpp`/all headers) is empty — this Buy added coverage only, no bug was exposed, so no Engineer-call was needed. Both smoke binaries remain unmodified; `fc_closed_loop_smoke` re-verified byte-identical (`15° → 0.252°`). See [report](../.jes/artifacts/implementation_report_fase_c_cpp_unit_tests_b1.md) · [review](../.jes/artifacts/implementation_review_fase_c_cpp_unit_tests_b1.md).

**C++ unit tests ≠ flying / ≠ MCU verification / ≠ production-hardened / ≠ algorithm change** — a host desktop `ctest` run with a real framework instead of two hand-rolled smoke mains, nothing more; the rung math is unchanged.

**C16 (`B1-fase-c-cpp-mcu-cross-compile`, ★ ACCEPT CLOSED @ tag `v0.5.14`) — first MCU cross-compile scaffold:**
[`.jes/artifacts/implementation_contract_fase_c_cpp_mcu_cross_compile_b1.md`](../.jes/artifacts/implementation_contract_fase_c_cpp_mcu_cross_compile_b1.md) adds `native/flight_control/cmake/toolchains/arm-none-eabi.cmake` — `CMAKE_SYSTEM_NAME Generic`, generic **Cortex-M4** (`-mcpu=cortex-m4 -mthumb -mfloat-abi=soft`, explicitly not a claim about any specific board's silicon) — and a separate build (`build/flight_control_mcu`) that produces **only** `libjarvis_fc.a` for that triple, gated by CMake (no `#ifdef` in the rung sources) so Catch2/the unit-test binary/both smokes never build on the MCU path. A **real cross-build was performed and verified**: `arm-none-eabi-objdump` confirms `file format elf32-littlearm, architecture: armv7e-m` on the produced archive — genuine target code, not a native fallback. **A real toolchain-completeness problem was hit and disclosed**: the bare Homebrew `arm-none-eabi-gcc` formula has no bundled `newlib`/`libstdc++` and fails to compile `<optional>`; the working build used the xPack `arm-none-eabi-gcc` v15.2.1-1.1 release instead (bundles a full C++17 standard library) — both outcomes (working toolchain vs. incomplete one) are exercised by the new pytest wrapper, which skips with a specific install hint rather than hard-failing when a compiler is present but incomplete. Host build re-verified unaffected: `ctest` still 28/28 green. **Not** flash, **not** GPIO, **not** a vendor BSP/SDK (STM32Cube/CMSIS/ChibiOS/FreeRTOS/PX4/ArduPilot all absent). See [report](../.jes/artifacts/implementation_report_fase_c_cpp_mcu_cross_compile_b1.md) · [review](../.jes/artifacts/implementation_review_fase_c_cpp_mcu_cross_compile_b1.md).

**MCU cross-compile ≠ flashed / ≠ flying / ≠ firmware runs on a flight controller / ≠ GPIO-verified** — a compile-time proof the steel-ladder sources build freestanding for a Cortex-M4-class target, nothing more; no board has run this code.

**C17 (`B1-fase-c-safety-real-policy`, ★ ACCEPT CLOSED @ tag `v0.5.15`) — first real Safety policy gate:**
[`.jes/artifacts/implementation_contract_fase_c_safety_real_policy_b1.md`](../.jes/artifacts/implementation_contract_fase_c_safety_real_policy_b1.md) adds `ArmedAllowlistSafetyGate` to `src/jarvis/capabilities/safety.py` — an **opt-in** policy that starts **disarmed** (always rejects, reason `"disarmed"`) and, once explicitly `arm()`ed, `allow`s **only** `HOLD` and `LAND` (parsed from `submit_command`'s own `autonomy:{verb}:{id}` action-id shape); any other verb, or a malformed `action_id`, is rejected too (`"verb_not_allowed"` / `"unparseable_action_id"` — neither reuses `RejectAllSafetyGate`'s `"not_implemented"`). **`default_safety_gate()` is byte-unchanged** — confirmed via `git diff`, zero lines touched in `RejectAllSafetyGate` or the factory function; the shipped product default remains "reject everything." `evaluate()` never reads `authority_signal_id` at all — Authority (C5) stays trace-only and cannot flip a decision through this or any gate. `submit_command`'s `allow` branch, unreachable-in-shipped-code since C4, already resolved to `execution="not_implemented"` — this Buy needed **zero changes** to `flight_software/autonomy/surface.py`/`types.py` to satisfy "allow ≠ execute"; verified at runtime via `typing.get_args(ExecutionState) == {"not_attempted", "not_implemented"}`. A thin `smoke_policy_gate_hold_and_land()` helper demonstrates the armed allow path end-to-end. No `AllowAllSafetyGate`, no `SimulatedEscSink`/GPIO coupling, no craft/CLI wiring. See [report](../.jes/artifacts/implementation_report_fase_c_safety_real_policy_b1.md) · [review](../.jes/artifacts/implementation_review_fase_c_safety_real_policy_b1.md).

**Policy allow ≠ flying / ≠ executed autonomy / ≠ hardware Safety / ≠ "safe to fly"** — a real, opt-in, narrowly-scoped software gate now exists alongside the unchanged RejectAll default; nothing here dispatches to any actuator, and no gate shipped in `src/` can ever return `execution="executed"`.

**C18 (`B1-fase-c-cpp-mcu-freestanding-elf`, ★ ACCEPT CLOSED @ tag `v0.5.16`) — first freestanding linked MCU `.elf`:**
[`.jes/artifacts/implementation_contract_fase_c_cpp_mcu_freestanding_elf_b1.md`](../.jes/artifacts/implementation_contract_fase_c_cpp_mcu_freestanding_elf_b1.md) adds `native/flight_control/mcu/` — a generic Cortex-M4 linker script (`FLASH` at `0x00000000` / `RAM` at `0x20000000`, the ARM-architected generic Code/SRAM regions, not any vendor's remapped boot address; 256 KiB/64 KiB illustrative sizes, explicitly fictional) + a 16-entry ARMv7-M vector table + `Reset_Handler` startup + minimal newlib syscall stubs (`_sbrk`/`_write`/`_exit`/… — no semihosting, no real I/O) + a thin entry point that **links `jarvis_fc`** — reusing C16's own toolchain file unchanged — into one inspectable ARM `.elf`, `fc_mcu_stub.elf`. A **real link was performed and verified**: `readelf -h` shows `Machine: ARM`, `Type: EXEC`, a real entry point, soft-float ABI; `nm` confirms `jarvis::fc::ImuLowPassFilter::filter_sample` and `encode_motor_forces` are linked in as defined (not merely referenced) symbols. **C++ exceptions were kept enabled** (IC §0 decision 8, option (a)) — the rung sources' `throw std::invalid_argument(...)` calls are untouched; the C++ runtime resolves via the toolchain's own libstdc++/newlib plus this Buy's own syscall stubs, not by disabling exceptions. **A real build-system gap was hit and fixed, disclosed**: the `.c` startup/syscall sources were silently never compiled (CXX-only `project()`) until C was added as a project language — before the fix, the linker warned `cannot find entry symbol Reset_Handler`; after, the warning is gone and the entry point is correct. Host build re-verified unaffected: `ctest` still 28/28 green. **Not** flash, **not** a vendor BSP, **not** a claim it boots on a real FC. See [report](../.jes/artifacts/implementation_report_fase_c_cpp_mcu_freestanding_elf_b1.md) · [review](../.jes/artifacts/implementation_review_fase_c_cpp_mcu_freestanding_elf_b1.md).

**Freestanding `.elf` ≠ flashed / ≠ boots on hardware / ≠ motors / ≠ GPIO** — a linked, inspectable, host-only ARM executable proving the whole chain (startup, linker script, syscall stubs, C++ runtime, real `jarvis_fc` code) coheres, nothing more; this image has never run on any board.

**C19 (`B1-fase-c-crsf-link-stub`, ★ ACCEPT CLOSED @ tag `v0.5.17`) — first CRSF byte-fixture link stub (ELRS-shaped):**
[`.jes/artifacts/implementation_contract_fase_c_crsf_link_stub_b1.md`](../.jes/artifacts/implementation_contract_fase_c_crsf_link_stub_b1.md) adds `src/jarvis/capabilities/crsf_stub.py` — a **separate** module from C5's own `radio.py` on purpose (its no-decode-API T5 lock stays byte-unchanged, confirmed via `git diff`). Parses the CRSF envelope (`[device_addr][frame_len][type][payload][crc8]`, CRC8 poly `0xD5` over `type+payload`) from checked-in fixture bytes into `CrsfFrame`, then decodes two frame types: `0x16` `RC_CHANNELS_PACKED` (16 × 11-bit channels, LSB-first) and `0x14` `LINK_STATISTICS` (RSSI/LQ/SNR fields) — both required/recommended per this IC. Truncated frames and bad-CRC frames both raise a typed `CrsfParseError`, verified against four checked-in `.bin` fixtures. **Zero I/O anywhere in the module** — no serial/socket/pty/USB/subprocess, confirmed by inspecting real code (comments and docstrings excluded from the check). `RadioIntentAdapter.parse(...)` still raises `NotImplementedError` even when fed real CRSF fixture bytes; `default_safety_gate()` and `ArmedAllowlistSafetyGate` are untouched; nothing decoded here reaches `SimulatedRadioIngress`, autonomy `submit_command`, or any `SafetyGate`. No CRSF/ELRS token anywhere under `native/`. See [implementation report](../.jes/artifacts/implementation_report_fase_c_crsf_link_stub_b1.md) · [review](../.jes/artifacts/implementation_review_fase_c_crsf_link_stub_b1.md).

**Fixture CRSF parse ≠ live ELRS ≠ a pilot link ≠ a CRSF driver product** — this module can decode a byte sequence, nothing more: no receiver is "connected," no air protocol (RF/binding/telemetry) is implemented, and no pilot's sticks drive anything.

**C20 (`B1-fase-c-crsf-dual-role-bridge`, ★ ACCEPT CLOSED @ tag `v0.5.18`) — CRSF decode → dual-role bridge:**
[`.jes/artifacts/implementation_contract_fase_c_crsf_dual_role_bridge_b1.md`](../.jes/artifacts/implementation_contract_fase_c_crsf_dual_role_bridge_b1.md) adds `src/jarvis/capabilities/crsf_dual_role.py` — a **third separate** module (never folded into `radio.py`; `git diff` confirms `radio.py`/`intent.py`/`safety.py` all byte-unchanged) that bridges C19's decoded `CrsfRcChannels` into C5's typed `RadioStubFrame`/`RadioDualRoleResult` under one documented, deterministic policy: `CrsfDualRolePolicy` (one aux channel index + threshold, illustrative defaults channel `4`/`1500`, not sourced from any real hardware) — at/above threshold, emits `AuthorityKind="kill"` **only** (Authority-only, never Intent); below threshold, returns `None`. Optional `link_stats` enrichment folds LQ/RSSI/SNR into `RadioStubFrame.notes` without ever changing whether Authority fires. `ingest_rc_channels(...)` optionally routes a produced frame through `SimulatedRadioIngress.ingest(...)`. **Authority from this bridge stays trace-only relative to Safety** — explicitly tested: wiring the bridge's own `AuthoritySignal.id` into a `SafetyRequest.authority_signal_id` still yields `reject` on both `RejectAllSafetyGate` and an armed `ArmedAllowlistSafetyGate`; `default_safety_gate()` is unchanged. `RadioIntentAdapter.parse(...)` still raises `NotImplementedError`, even fed a real bridge-produced frame. The bridge never calls `submit_command` or imports the autonomy surface. See [implementation report](../.jes/artifacts/implementation_report_fase_c_crsf_dual_role_bridge_b1.md).

**Bridge ≠ live ELRS ≠ a pilot link ≠ Safety allow** — a deterministic, documented map from already-decoded bytes to a typed dual-role frame, nothing more; no serial/UART product, no auto-execution, Authority still cannot open Safety through any shipped gate.

**C21 (`B1-fase-c-crsf-byte-stream`, ★ ACCEPT CLOSED @ tag `v0.5.19`) — CRSF byte-stream assembler:**
[`.jes/artifacts/implementation_contract_fase_c_crsf_byte_stream_b1.md`](../.jes/artifacts/implementation_contract_fase_c_crsf_byte_stream_b1.md) adds `src/jarvis/capabilities/crsf_stream.py` — a fourth **separate** module (never folded into `radio.py`; `git diff` confirms `radio.py`/`crsf_stub.py`/`crsf_dual_role.py`/`intent.py`/`safety.py` all byte-unchanged). `CrsfByteStreamAssembler.feed(data: bytes) -> list[CrsfFrame]` reassembles frames from bytes delivered in **arbitrary chunks** (the shape a UART delivers data in) by slicing exact `frame_len + 2` candidate windows and handing them, unmodified, to C19's own `parse_crsf_frame` — no second CRC8/envelope implementation (verified: no `0xD5` anywhere in `crsf_stream.py`). **Incomplete** candidates wait in a bounded leftover buffer (default cap `256` bytes); **invalid complete** windows (bad CRC, or a declared `frame_len` outside the plausible `[2, 64]` range) are never raised to the caller — the assembler drops exactly one byte and resyncs, looping until it finds a valid frame or exhausts the buffer. An optional `ingest_stream_bytes(...)` helper reuses C20's `ingest_rc_channels(...)` **unchanged** for any completed `0x16` frames — C20's policy (one aux channel, one threshold, `AuthorityKind="kill"` only) is neither deepened nor reconfigured here. Zero I/O in the module — no `serial`/`socket`/`pty`/USB/`open()`, no class named like `Serial`/`UartPort`. See [implementation report](../.jes/artifacts/implementation_report_fase_c_crsf_byte_stream_b1.md).

**Byte-stream assembler ≠ UART open ≠ live ELRS ≠ a pilot link ≠ Safety allow** — a pure in-memory buffer proving bytes delivered in chunks reassemble into the same frames C19 already parses from a complete buffer, nothing more.

**C22 (`B1-fase-c-crsf-host-serial`, ★ ACCEPT CLOSED @ tag `v0.5.20`) — CRSF host serial ingest:**
[`.jes/artifacts/implementation_contract_fase_c_crsf_host_serial_b1.md`](../.jes/artifacts/implementation_contract_fase_c_crsf_host_serial_b1.md) adds `src/jarvis/capabilities/crsf_serial.py` — a fifth **separate** module (never folded into `radio.py`; `git diff` confirms `radio.py`/`crsf_stub.py`/`crsf_dual_role.py`/`crsf_stream.py`/`intent.py`/`safety.py` all byte-unchanged). `CrsfHostSerialIngress` pulls bytes from an already-open host FD (`attach_fd`, caller-owned, never closed by this module) or an opt-in device path (`attach_path`, ingress-owned, closed on `.close()`), and `poll(...)` performs exactly **one** non-blocking read then feeds whatever came back to C21's own `CrsfByteStreamAssembler`, unchanged — no background thread, no "connected" flag, no `/dev/cu.*` auto-scan. **Every PASS in this Buy's own test suite uses a POSIX `pty` as its loopback — no physical receiver or USB serial adapter is required**, verified by running the full suite with nothing plugged in. **No `pyserial` dependency was added**, and **420000 baud (the rate a real ELRS link runs at) is not configured anywhere** — opening a path here means "give me bytes from this node," not "I configured an ELRS receiver"; custom-baud configuration is explicitly deferred to a later, platform-specific IC. A real pty gotcha was found and disclosed while testing: POSIX ptys default to canonical (line-buffered) mode, which silently held binary CRSF bytes back from a reader until a newline appeared — fixed entirely in the test harness (`tty.setraw(...)`), not in the shipped module, which has no terminal-mode logic at all. An optional `poll_and_ingest(...)` helper reuses C20's `ingest_rc_channels(...)` unchanged for any completed `0x16` frames. See [implementation report](../.jes/artifacts/implementation_report_fase_c_crsf_host_serial_b1.md).

**Host serial ingest ≠ live ELRS ≠ RX connected ≠ UART driver ≠ Safety allow** — a pull-based FD/path reader proving bytes can be pulled from a host source and reassembled by C21's own assembler, verified entirely via `pty` loopback, nothing more.

**C23 (`B1-fase-c-crsf-host-baud`, ★ ACCEPT CLOSED @ tag `v0.5.21`) — CRSF host baud 420000:**
[`.jes/artifacts/implementation_contract_fase_c_crsf_host_baud_b1.md`](../.jes/artifacts/implementation_contract_fase_c_crsf_host_baud_b1.md) extends C22's own `src/jarvis/capabilities/crsf_serial.py` — **no sixth module** — with **opt-in** Darwin host baud configuration: `configure_host_baud(fd, baud=420000)` / `CrsfHostSerialIngress.configure_baud(...)`. On `sys.platform == "darwin"` it applies raw 8N1 termios (disabling canonical mode and the CR/NL translations that would corrupt binary CRSF) then issues the real `IOSSIOSPEED` ioctl — the request number **derived** from the `_IOW('T', 2, speed_t)` macro (`sys/ioccom.h`), not copied from `pyserial` or any library; verified independently to equal `0x80085402`. On any other platform it **fails closed** with a typed `CrsfHostSerialError` — no Linux `TCSETS2`/`BOTHER`, no Windows serial stack. `attach_fd`/`attach_path` still **never** auto-configure baud — C22's own "open = give me bytes" contract is unchanged, re-verified by re-running C22's own test suite unmodified. **Every PASS requires no hardware**: the Darwin success path is proven entirely via a mocked `fcntl.ioctl`; the one **unmocked** ioctl call runs against a real POSIX `pty` and is **asserted to fail** (a pty is not a UART) — that failure is the honest, expected outcome, not something skipped around. A successful ioctl is a host OS configuration fact, never proof a receiver exists. See [implementation report](../.jes/artifacts/implementation_report_fase_c_crsf_host_baud_b1.md).

**Host baud 420000 ≠ live ELRS ≠ RX connected ≠ UART driver ≠ Safety allow** — Darwin can be asked to clock an attached FD at an ELRS-typical rate, proven without hardware via ioctl mock, nothing more.

**C24 (`B1-fase-c-control-loop-tick`, ★ ACCEPT CLOSED @ tag `v0.5.22`) — named control tick:**
[`.jes/artifacts/implementation_contract_fase_c_control_loop_tick_b1.md`](../.jes/artifacts/implementation_contract_fase_c_control_loop_tick_b1.md) extracts the body C11/C13 already ran **inlined** into one named cycle: `src/jarvis/flight_software/flight_control/loop.py` adds `FlightControlLoop.step(sample, setpoint, collective) -> ControlTickResult` — `filter_sample -> estimator.update -> controller.compute -> bridge.convert -> mixer.mix`, exactly the C11/C13 order, calling each existing rung's own unmodified method, no new math. The C++ twin — `native/flight_control/include/jarvis/fc/loop.hpp` + `src/loop.cpp`, added to `jarvis_fc` — mirrors the same order with the same existing classes. `step` **does not** call the plant, read a real HAL, or write a pin — the caller still supplies `ImuSample` and consumes `MotorForceCommand`/`EscPwmCommand` itself; `dt` is **not** an argument (no 1 kHz ISR claim), and `AttitudeSetpoint`/`collective` are plain arguments (no RC decoding — mapping sticks to them is C25). `run_controlled_flight_sim_smoke` (Python, C11) and `fc_closed_loop_smoke` (C++, C13) are refactored to **call** `step` instead of inlining the chain — verified bit-identical to the pre-refactor behavior: `15° → 0.252°` in 200 steps, no gain retuned. `mcu/stub_main.cpp` still has no `ControlLoop`/`step(` control cycle — no `Reset_Handler` spin. `radio.py`/`crsf_*.py`/`intent.py`/`safety.py`/`autonomy/` all byte-unchanged (`git diff --stat` empty). See [implementation review](../.jes/artifacts/implementation_review_fase_c_control_loop_tick_b1.md).

**Named control tick ≠ flying ≠ MCU ISR ≠ motors ≠ RC sticks** — one named cycle, IMU+setpoint+collective in, four motor forces out, reusing C6-C12/C13 unchanged; plant, ESC pin, and RC mapping remain later cola.

**C25 (`B1-fase-c-rc-setpoint`, ★ ACCEPT CLOSED @ tag `v0.5.23`) — RC channel units → C24 tick args:**
[`.jes/artifacts/implementation_contract_fase_c_rc_setpoint_b1.md`](../.jes/artifacts/implementation_contract_fase_c_rc_setpoint_b1.md) adds `src/jarvis/flight_software/flight_control/rc_setpoint.py` — `map_rc_to_loop_inputs(channels, *, t_s) -> RcLoopInputs`, an illustrative AETR map (not a real TX model): `RC_CH_ROLL`/`RC_CH_PITCH`/`RC_CH_THROTTLE` = indices `0`/`1`/`2`; the yaw channel (index `3` conventionally) is **unused this Buy** — there is no magnetometer anywhere in this tree, so there is no absolute heading reference a yaw stick could honestly command. `CRSF_CH_MIN`/`CRSF_CH_MID`/`CRSF_CH_MAX` = `172`/`992`/`1811` (the same illustrative 11-bit convention already used around C20's policy). Throttle maps linearly onto `collective ∈ [0, 1]`, clipped — mid-stick (`992`) gives **≈0.5003, not exactly 0.5** (the endpoints are not perfectly symmetric around `992`), documented rather than rounded away. Roll/pitch deflection is measured from `992`, scaled to reach exactly `RC_MAX_TILT_RAD` (`π/6`, 30°) at either endpoint, clipped beyond it, then composed into `q_body_to_world_desired` via the standard body 3-2-1 (yaw-pitch-roll) Euler-to-quaternion formula with yaw fixed at `0`. The C++ twin — `native/flight_control/include/jarvis/fc/rc_setpoint.hpp` + `src/rc_setpoint.cpp`, added to `jarvis_fc` — mirrors the same thresholds and formula using a plain `std::vector<int>` (this tree carries no CRSF-shaped type at all; the C21-C23 lock of **zero CRSF/ELRS mentions anywhere under `native/`**, even in comments, stays intact — the C++ constants are named `kRcChMin`/`kRcChMid`/`kRcChMax`, with the protocol name dropped). An optional `step_with_rc(loop, sample, channels)` helper maps then calls C24's own `FlightControlLoop.step` unchanged — `git diff --stat` on `loop.py`/`loop.hpp`/`loop.cpp` is **empty** — and never calls a plant, `SimulatedEscSink`, or `SafetyGate.evaluate`. C20's `CrsfDualRolePolicy` (aux → Authority `kill`) is untouched and not imported here. `radio.py` still has no stick API (C5 T5 lock). See [implementation report](../.jes/artifacts/implementation_review_fase_c_rc_setpoint_b1.md).

**RC→setpoint ≠ flying ≠ sticks drive motors ≠ Safety allow ≠ yaw lock** — a deterministic, documented map from already-decoded channel units to the two arguments `step` already accepted; no pilot flies anything, no motor spins, and the yaw stick implies no heading-hold (none exists).

**C26 (`B1-fase-c-esc-output-hal`, ★ ACCEPT CLOSED @ tag `v0.5.24`) — naming the ESC output port:**
[`.jes/artifacts/implementation_contract_fase_c_esc_output_hal_b1.md`](../.jes/artifacts/implementation_contract_fase_c_esc_output_hal_b1.md) names the port C10/C14 already implemented as a concrete sink: `esc.py`/`esc.hpp` gain `EscOutput` — Python `abc.ABC`, C++ abstract base with a virtual destructor — exposing `apply_forces(forces: MotorForceCommand) -> EscApplyResult` plus `arm()`/`disarm()`/`armed` (identical semantics to C10). `SimulatedEscSink` **is-a** `EscOutput` in both languages; its C10 `apply(EscPwmCommand)` path and arming behavior stay byte-identical — `apply_forces` is a thin wrapper: `encode_motor_forces(forces)` then `apply(cmd)`. The `esc.cpp` diff is **purely additive** (verified line-by-line: zero lines removed/changed, four lines added); `esc.py`/`esc.hpp`/`esc.cpp` are the **only** rung files touched — `filter`/`attitude`/`controller`/`rate_torque`/`mixer`/`plant` stay `git diff --stat` empty. **The mixer still speaks forces only** — `mixer.py`/`mixer.hpp` gain no PWM/DShot/pin knowledge (grep-verified in real code). **`step` still never calls** `apply`/`apply_forces`/`SimulatedEscSink` — `loop.py`/`loop.hpp`/`loop.cpp` stay byte-unchanged, re-verified explicitly. **Only one implementation ships** (`SimulatedEscSink`) — no GPIO sink, no unimplemented pin class, no DShot this Buy. See [implementation report](../.jes/artifacts/implementation_review_fase_c_esc_output_hal_b1.md).

**EscOutput HAL ≠ pin ≠ motors ≠ DShot** — a named port exists; the simulated sink implements it; the mixer still does not know the wire protocol. Nothing here is a motor on a wire, a DShot stream, or `step` actuating anything.

**C27 (`B1-fase-c-crsf-stream-timeout-failsafe`, ★ ACCEPT CLOSED @ tag `v0.5.25`) — stream-timeout failsafe:**
[`.jes/artifacts/implementation_contract_fase_c_crsf_stream_timeout_failsafe_b1.md`](../.jes/artifacts/implementation_contract_fase_c_crsf_stream_timeout_failsafe_b1.md) adds `src/jarvis/capabilities/crsf_failsafe.py` — a sixth **separate** module (never folded into `radio.py`; `git diff` confirms `radio.py`/`crsf_stub.py`/`crsf_dual_role.py`/`crsf_stream.py`/`crsf_serial.py`/`intent.py`/`safety.py` all byte-unchanged). `CrsfRcHoldWatch` is an **age watch, not a parser**: `note_rc(now_s)` records the last time a valid `0x16` frame arrived; `evaluate(now_s)`/`is_stale(now_s)` compare that against `timeout_s` (default `0.5` s, illustrative, not sourced from any real ExpressLRS product spec) — `age_s <= timeout_s` is fresh, `age_s > timeout_s` is stale, never-noted is stale with `reason="never"`. Every method takes `now_s` as a caller-supplied argument — this module never calls `time.time()` as its own source of truth, keeping tests deterministic. A `now_s` earlier than the last noted time raises a typed `ValueError`. `failsafe_loop_inputs(t_s)` returns C8's own `level_setpoint(t_s)` plus `collective=0.0` — C25's own `RcLoopInputs` reused unchanged — and never calls `FlightControlLoop.step`, `EscOutput.apply_forces`, or any `SafetyGate.evaluate`. The optional `feed_and_note_rc(...)` helper calls C21's own `assembler.feed(data)` unchanged and notes only when a completed frame is `0x16` — it never calls `ingest_stream_bytes`, so C21's own default helper is untouched. The C++ twin — `native/flight_control/include/jarvis/fc/rc_hold.hpp` + `src/rc_hold.cpp`, added to `jarvis_fc` — is **deliberately protocol-agnostic**: no radio-link protocol name appears anywhere in that tree, even in comments (same C21-C26 lock, re-verified tree-wide via grep). C20's `CrsfDualRolePolicy` and C25's `map_rc_to_loop_inputs` are untouched and not imported here. See [implementation report](../.jes/artifacts/implementation_review_fase_c_crsf_stream_timeout_failsafe_b1.md).

**Timeout failsafe ≠ motors cut ≠ live ELRS ≠ Safety allow** — an age watch exists; after `0.5` s without a noted RC sample, sticks are no longer treated as live; the recommended inputs are level attitude plus zero collective. Nothing here is a radio that cuts ESCs, ExpressLRS failsafe as a shipped product, or Safety opening on timeout.

**C28 (`B1-fase-c-mcu-uart-hal-stub`, ★ ACCEPT CLOSED @ tag `v0.5.26`) — naming the MCU-side UART byte port:**
[`.jes/artifacts/implementation_contract_fase_c_mcu_uart_hal_stub_b1.md`](../.jes/artifacts/implementation_contract_fase_c_mcu_uart_hal_stub_b1.md) adds `native/flight_control/include/jarvis/fc/uart.hpp` + `src/uart.cpp` — `UartBytePort`, an abstract base with a virtual destructor exposing `read(dst, n)`/`write(src, n)` (neither blocks nor throws on a full/empty port), and `LoopbackUart`, the **only** implementation: an in-memory FIFO (default capacity `256`). A write past remaining capacity **returns a short count** (refuses the extra bytes) rather than growing unbounded or overwriting already-queued bytes — a chosen, tested overflow policy, not an accident. **Zero USART registers, zero CMSIS, zero `IOSSIOSPEED`/`termios`, zero IRQ/DMA** anywhere in either file — grep-verified in real code. `mcu/stub_main.cpp` still does **not** reference `UartBytePort`/`LoopbackUart` — no UART poll loop was added to `Reset_Handler`/`main` this Buy; the `.elf` still links against the ARM toolchain when present. `capabilities/crsf_serial.py` (Mac host serial, C22/C23) stays **byte-identical** — this Buy is C++-only on the MCU tree, no Python UART driver was added. The C21-C27 lock of **zero CRSF/ELRS mentions anywhere under `native/`**, even in comments, holds — re-verified tree-wide (proactive grep on the new header; this Buy ID contains no protocol tokens, so no rewrite was required). See [implementation review](../.jes/artifacts/implementation_review_fase_c_mcu_uart_hal_stub_b1.md).

**MCU UART stub ≠ chip USART ≠ Darwin baud ≠ live ELRS** — a named byte port exists; an in-memory loopback implements it. Nothing here is a USART talking to a receiver, the Mac's own `IOSSIOSPEED` moved onto the chip, or ExpressLRS running on the MCU.

**C29 B0 (`B0-fase-c-silicon-cited-flash-map`, investigation, ★ ACCEPT CLOSED, no tag) — park-until-named, confirmed correct:** no MCU had been named anywhere in this project, so the investigation recommended parking rather than guessing a part. On 2026-09-24 the Engineer named the desk hardware — a **HGLRC F460 6S V1** stack, FC SKU **HGLRC F405 8S V1**, MCU line **STM32F405** printed in that FC's own manual — the exact "named part" trigger the B0 report called for, opening **C29 B1**.

**C29 B1 (`B1-fase-c-silicon-cited-flash-map`, ★ ACCEPT CLOSED @ tag `v0.5.27`) — citing the desk STM32F405's own memory map:**
[`.jes/artifacts/implementation_contract_fase_c_silicon_cited_flash_map_b1.md`](../.jes/artifacts/implementation_contract_fase_c_silicon_cited_flash_map_b1.md) replaces C18's disclosed fiction in `native/flight_control/mcu/linker_cortex_m4.ld` with a **cited** map: `FLASH` `1024K` at `0x08000000`, `RAM` `128K` at `0x20000000` (SRAM1+SRAM2 contiguous) — taken from **ST RM0090 Table 3** (STM32F405xx/07xx, "Memory map"), not from the HGLRC manual (which names the MCU line but prints no ORIGIN/LENGTH numbers itself). CCM RAM (`0x10000000`, 64 KiB per RM0090) is deliberately **excluded** from this `MEMORY` block — folding it into a flat RAM region would be its own undisclosed simplification. The linker's own honesty comment names both citations (HGLRC desk identity, RM0090 map source) plus the disclosed residual: the HGLRC manual does not print the STM32F405's exact order-code suffix, but RM0090 Table 3's figures apply to the whole xx/07xx line regardless. `mcu/stub_main.cpp` was relinked (verified via `readelf -l`: `VirtAddr 0x08000000`, entry point `0x8000045`) but stays **byte-unchanged** — no new peripheral was touched. `cmake/toolchains/arm-none-eabi.cmake` (C16's own `-mfloat-abi=soft` flags) is also byte-unchanged this Buy. No CMSIS, no STM32Cube, no OpenOCD/J-Link anywhere in the touched files. See [implementation review](../.jes/artifacts/implementation_review_fase_c_silicon_cited_flash_map_b1.md).

**Cited FLASH map ≠ flashed ≠ boots on FC ≠ Betaflight HGLRCF405V2** — the linker now uses ST's own published addresses for this MCU, but that remains a compile/link-time fact on the Mac, never a claim about the HGLRC stack itself. No OpenOCD, no J-Link, no "this is Betaflight" claim anywhere.

**C30 (`B1-fase-c-mcu-flash-observable`, ★ ACCEPT CLOSED @ tag `v0.5.28`) — DFU-able PC13 image, LED not observed on desk:**
[`.jes/artifacts/implementation_contract_fase_c_mcu_flash_observable_b1.md`](../.jes/artifacts/implementation_contract_fase_c_mcu_flash_observable_b1.md) closes the two residuals C29 B1 left uncorrected in code: **(a) silent idle** — `stub_main` ran its one-shot `jarvis_fc` exercise then spun an empty `while (true)`, so a successful `Reset_Handler` looked identical to a dead board; **(b) CMake N1** — `-T<script>` is a linker flag, not an implicit CMake dependency, so editing `linker_cortex_m4.ld` never triggered a relink (C29's own T9, which deleted the `.elf` first, was a *test workaround*, not the fix). **(a)** is closed by `native/flight_control/mcu/hello_led.h`/`hello_led.c` — two functions (`hello_led_init`/`hello_led_spin`, bare `volatile` MMIO, no CMSIS, no HAL) that toggle **PC13**, cited from Betaflight's own unified target for this FC (`HGLR-HGLRCF405V2.config`, line `resource LED 1 C13`) — deliberately **not** PA8 (that same V2 target's own `resource MOTOR 6 A08`, a motor-timer pin) and **not** PB1 (`LED_STRIP`, wire LEDs, not the onboard status LED). The MMIO addresses (`RCC_AHB1ENR` `0x40023830` bit 2, `GPIOC_MODER`/`GPIOC_BSRR` at `0x40020800`/`0x40020818`) are cited from **RM0090**, transcribed by hand. The busy-wait between toggles is explicitly **uncalibrated** — a documented visible flicker at reset-default HSI 16 MHz, never a claimed millisecond period; no PLL/HSE/`SystemInit`. **(b)** is closed by `set_property(TARGET fc_mcu_stub.elf APPEND PROPERTY LINK_DEPENDS .../linker_cortex_m4.ld)` in `CMakeLists.txt` — verified by touching the `.ld` and rebuilding **without** deleting the prior `.elf`: the `.elf`'s mtime advances, confirming a genuine relink. A `POST_BUILD` step runs `arm-none-eabi-objcopy -O binary` to produce `fc_mcu_stub.bin` (load address `0x08000000`, unchanged from C29's own map) for **USB DFU** — documented in this tree's README alongside the restore procedure (reflash target **HGLRCF405V2** from Betaflight Configurator) and the props-off/battery-off warning. `uart.hpp`/`crsf_serial.py` stay **byte-identical**; `startup_cortex_m4.c`/`syscalls_stub.c`/C16's own toolchain flags too. No NVIC/EXTI/IRQ/DMA, no motor-pin write anywhere. See [implementation review](../.jes/artifacts/implementation_review_fase_c_mcu_flash_observable_b1.md).

**Flashed LED blink ≠ flying ≠ DShot ≠ USART live ≠ Betaflight HGLRCF405V2** — a DFU-able image exists; CMake will relink if the linker script changes. **Not flashed on desk.**

**C31 (`B1-fase-c-dshot-encode-stub`, ★ ACCEPT CLOSED @ tag `v0.5.29`) — the DShot 16-bit frame, in RAM:**
[`.jes/artifacts/implementation_contract_fase_c_dshot_encode_stub_b1.md`](../.jes/artifacts/implementation_contract_fase_c_dshot_encode_stub_b1.md) names the 16-bit DShot frame the desk ESC (HGLRC 60A 6S, Bluejay, DShot150/300/600) will someday want: `src/jarvis/flight_software/flight_control/dshot.py` + `native/flight_control/include/jarvis/fc/dshot.hpp`/`src/dshot.cpp` add `encode_dshot_frame(throttle, telemetry=False) -> uint16` — `value = (throttle << 1) | telemetry`, `checksum = (value ^ (value>>4) ^ (value>>8)) & 0xF`, `frame = (value << 4) | checksum`, `throttle` a required `[0, 2047]` integer (out of range raises a typed error). **Vectors verified in both languages**: `throttle=0 -> 0x0000`, `throttle=48 -> 0x0606`, `throttle=2047 -> 0xFFEE`. **Special range documented, not implemented**: DShot's own protocol reserves `0..47` as commands (beep, 3D, etc.) — this module encodes the 11-bit field as given, no command table. An optional `encode_motor_forces_dshot(forces) -> 4x uint16` helper linearly maps force `[0,1]` onto throttle **`48..2047`** (never `0..2047` — `0` would collide with the command range) — a **parallel** path that does not replace `encode_motor_forces` (PWM-µs, C10/C14) or `EscOutput`/`SimulatedEscSink` (C26), both re-verified byte-unchanged. `mcu/hello_led.h`/`hello_led.c`/`stub_main.cpp` (C30) stay **byte-identical** — idle is still PC13, not DShot. DShot150/300/600 appear only as cited protocol names in comments, never as a claimed timer period or GPIO toggle rate — no timing exists anywhere in this module. A pre-existing C13 test that used "dshot" as a blanket-forbidden token (written before any legitimate DShot code existed in this tree) was retargeted with a disclosed, narrow exclusion for only the three files C31 authorizes — every other file, and every *other* forbidden token (GPIO included) in those same three files, stays checked. See [implementation review](../.jes/artifacts/implementation_review_fase_c_dshot_encode_stub_b1.md).

**DShot encode ≠ pin ≠ motors ≠ flying** — a 16-bit DShot packet computed in software exists. Nothing here makes an ESC see a waveform.

**C32 (`B1-fase-c-mcu-spi-hal-stub`, package/tag `v0.5.30`, ★ ACCEPT CLOSED) — naming the MCU-side SPI byte port:**
[`.jes/artifacts/implementation_contract_fase_c_mcu_spi_hal_stub_b1.md`](../.jes/artifacts/implementation_contract_fase_c_mcu_spi_hal_stub_b1.md) names the SPI byte port, same pattern C28 used for UART: `native/flight_control/include/jarvis/fc/spi.hpp`/`src/spi.cpp` add `SpiBytePort` — an abstract base with a virtual destructor exposing `transfer(tx, rx, n) -> size_t` (copies up to `n` bytes from TX into RX, in order, never blocks) — and `LoopbackSpi`, the **only** implementation: RX = TX, default capacity `256`, a transfer past that capacity **returns a short count** rather than growing unbounded, the same overflow policy `LoopbackUart` (C28) already uses. Unlike `LoopbackUart`'s own persistent FIFO, `LoopbackSpi` carries **no state between calls** — a real SPI transfer is a single synchronous exchange, not an asynchronous stream, so no queue is needed. **Zero SPI registers, zero CMSIS, zero chip-select/NSS GPIO, zero IRQ/DMA** anywhere in either file — grep-verified in real code. The desk FC's own gyro (when later wired) is an **ICM42688P** on SPI — cited only as desk identity in `spi.hpp`'s own honesty comment, never in real code: no `WHO_AM_I` read, no register map, no sample anywhere in this Buy. `dshot.hpp`/`dshot.cpp`/`dshot.py` (C31), `hello_led.h`/`hello_led.c`/`stub_main.cpp` (C30), and `uart.hpp`/`uart.cpp` (C28) all stay **byte-identical** — idle is still only PC13, no SPI poll in `main`. `SimulatedImuHal` (C3, Python) is untouched too — this Buy is C++-only on the MCU tree. See [implementation review](../.jes/artifacts/implementation_review_fase_c_mcu_spi_hal_stub_b1.md).

**MCU SPI stub ≠ chip SPI ≠ gyro live ≠ flying** — a named SPI byte port exists; an in-memory loopback implements it. Nothing here reads the ICM42688P, opens a chip SPI bus, or puts DShot on a pin.

**C33 (`B1-fase-c-spi-scripted-slave`, package/tag `v0.5.31`, ★ ACCEPT CLOSED) — a second `SpiBytePort`: canned RX, not TX echo:**
[`.jes/artifacts/implementation_contract_fase_c_spi_scripted_slave_b1.md`](../.jes/artifacts/implementation_contract_fase_c_spi_scripted_slave_b1.md) adds `ScriptedSpi` to the existing `spi.hpp`/`spi.cpp` (no new file) alongside `LoopbackSpi` (C32, behavior-unchanged). `LoopbackSpi` only ever echoes what you send it; a real device answers with **its own** bytes, independent of TX — `ScriptedSpi` fills RX from a pre-loaded byte script (`canned_rx`) instead, and TX is never inspected or required to match anything. Each `transfer(...)` call fills RX from the **start** of the currently-loaded script (a fixed canned response, not a stream consumed across calls) — `set_next_rx(...)` reprograms what subsequent transfers return. A script shorter than the requested `n` **returns a short count**, same overflow policy as `LoopbackSpi`, and the untouched tail of `rx` is left exactly as the caller passed it in. **Zero SPI registers, zero CMSIS, zero chip-select/NSS GPIO, zero IRQ/DMA, zero CRSF/ELRS tokens** anywhere in `native/` — grep-verified. `WHO_AM_I`/`ICM42688P` are named only in comments (never real code) — e.g. "a future gyro test could load `0x47` here," a placeholder byte, not a claim about any real register. `stub_main.cpp`, `hello_led.h`/`hello_led.c` (C30), `dshot.hpp`/`dshot.cpp`/`dshot.py` (C31), and `uart.hpp`/`uart.cpp` (C28) all stay **byte-identical**. See [implementation review](../.jes/artifacts/implementation_review_fase_c_spi_scripted_slave_b1.md).

**Scripted SPI ≠ gyro live ≠ chip SPI ≠ flying** — a canned-RX test double exists. Nothing here reads a real device.

**C34 (`B1-fase-c-spi-scripted-gyro-probe`, package/tag `v0.5.32`, ★ ACCEPT CLOSED) — the first client of `SpiBytePort`:**
[`.jes/artifacts/implementation_contract_fase_c_spi_scripted_gyro_probe_b1.md`](../.jes/artifacts/implementation_contract_fase_c_spi_scripted_gyro_probe_b1.md) adds `probe_rx` in **new** files `native/flight_control/include/jarvis/fc/spi_probe.hpp`/`src/spi_probe.cpp` (never folded into `ScriptedSpi`) — `probe_rx(SpiBytePort& port, uint8_t* rx, size_t n) -> size_t` sends `n` dummy **all-zero** TX bytes (never a register address), calls `port.transfer(...)`, and returns that count (`n == 0` returns `0`). `spi.hpp`/`spi.cpp` (C32/C33) get **zero edits** — the port stays the port, `spi_probe.*` is the first caller. C33 gave the port a way to lie with bytes; today a **client** asks the plug for those bytes — the day a real chip exists, only the implementation behind the reference changes (`ScriptedSpi` → a SPI1 port), not this client. On `ScriptedSpi` loaded with a placeholder fixture byte, `probe_rx` returns that byte, proving the RX path end-to-end; on `LoopbackSpi`, `probe_rx` returns all-zeros (the dummy TX echoed back), proving the client is port-shaped, not tied to one implementation. Same overflow policy as the port: a script shorter than `n` **returns a short count**, untouched tail of `rx` left exactly as passed in. **Zero SPI registers, zero CMSIS, zero chip-select/NSS GPIO, zero IRQ/DMA, zero CRSF/ELRS tokens** anywhere in `native/`. `WHO_AM_I`/`ICM42688P`/register address `0x75` do not appear anywhere in `spi_probe.*`, not even in a comment — the fixture byte lives in tests only, never in library code (a stricter rule than C33's own comment-OK allowance, since this Buy's own T8 requires it). `stub_main.cpp`, `hello_led.h`/`hello_led.c` (C30), `dshot.hpp`/`dshot.cpp`/`dshot.py` (C31), `uart.hpp`/`uart.cpp` (C28), and `loop.hpp`/`loop.cpp`/`loop.py` (C3/C4) all stay **byte-identical**. See [implementation review](../.jes/artifacts/implementation_review_fase_c_spi_scripted_gyro_probe_b1.md).

**Scripted gyro probe ≠ gyro live ≠ chip SPI ≠ WHO_AM_I ≠ flying** — a function that asks the port for bytes exists; tests can preload those bytes. Nothing here reads the ICM42688P or opens a real SPI bus.

**C35 (`B1-fase-c-step-failsafe-hold-ticks`, package/tag `v0.5.33`, ★ ACCEPT CLOSED) — tests only, chaining what C24/C27 already allow:**
[`.jes/artifacts/implementation_contract_fase_c_step_failsafe_hold_ticks_b1.md`](../.jes/artifacts/implementation_contract_fase_c_step_failsafe_hold_ticks_b1.md) locks three facts C24/C27 already permit but had never chained: (1) **many** `step()` ticks on canned IMU stay finite, (2) a **stale** hold watch feeds `failsafe_loop_inputs` **into** that same `step()`, (3) **hold** means keep feeding `level_setpoint` (not `AutonomyVerb` execute). **Zero production code changed** — `loop.py`/`loop.hpp`/`loop.cpp`, `rc_hold.hpp`/`rc_hold.cpp`, `crsf_failsafe.py`, and `spi_probe.hpp`/`spi_probe.cpp` (C34) are all byte-unchanged, `git diff --stat` empty on all eight files. New tests (Python + 4 new Catch2 cases appended to the existing `test_loop.cpp`, no new Catch2 file): **1000** `step()` ticks with a canned level IMU sample (`accel ≈ (0,0,-9.81)`, gyro zeros) and no plant — every tick's four motor forces stay finite and in `[0, 1]`. A **stale** watch (never noted, or past the 0.5 s timeout) feeds `failsafe_loop_inputs(t)` into that same `step()` — `collective` passed in is `0`, forces still finite and in `[0, 1]`; no `EscOutput`/GPIO call anywhere in the new tests. `submit_command(HOLD)` is re-asserted to still return `execution="not_attempted"` under the default `RejectAllSafetyGate` — "hold" here means feeding `level_setpoint`, never `AutonomyVerb.HOLD` reaching execution. `probe_rx` (C34) is **not** used as an IMU source anywhere in these tests. See [implementation review](../.jes/artifacts/implementation_review_fase_c_step_failsafe_hold_ticks_b1.md).

**Many ticks ≠ flying ≠ 6-DoF. Failsafe → step ≠ motors cut ≠ HOLD executed** — tests that call `step()` a thousand times, and that feed failsafe inputs into that same `step()`, both exist. Nothing here is a flying plant, a motor cut, or an executed autonomy command.

**Taller CSS cuboid faces (`B1-geometry-taller-css-cuboid-faces`, package/tag `v0.5.34`, ★ ACCEPT CLOSED) — six faces stop exploding on a thin plate:**
[`.jes/artifacts/implementation_contract_geometry_taller_css_cuboid_faces_b1.md`](../.jes/artifacts/implementation_contract_geometry_taller_css_cuboid_faces_b1.md) is a **UI/CSS visor fix**, not a Fase C flight-software Buy. Root cause: each of `Solid3D`'s six box faces sat at the `.sb-solid__face` CSS default `left: 0; top: 0`, but only `front`/`back` actually match the wrapper's own `w x h` size — `left`/`right` (width `d`) and `top`/`bottom` (height `d`) do not, so with `transform-origin: 50% 50%` (never overridden) they rotate about their own off-center point instead of the cuboid's true center, most visibly on a thin plate. New pure helper `ui/spatial-board/src/cuboidFaces.ts` — `cuboidFaceLayout(w, d, h)` — centers every face first (`left: (w-fw)/2`, `top: (h-fh)/2`), then the existing rotate + `translateZ(half-extent along that face's own normal)` locked in `Solid3D.tsx`'s `box` branch, which now consumes the helper instead of hardcoding six transform strings inline. Still exactly six `.sb-solid__face` nodes, no seventh. Verified against the MY5 top-plate fixture (`161x42x2mm`, `pxPerMm 0.5` → `80.5x21x1`px): `top`/`bottom` center to `translateZ(0.5px)`, `left`/`right` to `translateZ(40.25px)`, no `translateX`/`translateY` anywhere in any transform string (centering lives entirely in `left`/`top`). Cylinder/disk branches, the projector, the `geometry` DTO, and `spatial_board.py` are all **byte-unchanged** — `git diff --stat` empty. See [implementation review](../.jes/artifacts/implementation_review_geometry_taller_css_cuboid_faces_b1.md).

**Visor cuboid ≠ CAD ≠ fit ≠ extra parts ≠ a 2D card's own origin** — six CSS faces that meet on a thin declared box exist. Nothing here is a machined plate, a fit verdict, or a seventh part.

**Taller CSS cylinder faces (`B1-geometry-taller-css-cylinder-faces`, package/tag `v0.5.35`, ★ ACCEPT CLOSED) — caps + 16 slats stop exploding on a short/tall cylinder:**
[`.jes/artifacts/implementation_contract_geometry_taller_css_cylinder_faces_b1.md`](../.jes/artifacts/implementation_contract_geometry_taller_css_cylinder_faces_b1.md) fixes the same class of bug the cuboid Buy just shipped. New pure helper `ui/spatial-board/src/cylinderFaces.ts` — `cylinderSolidLayout(diameterPx, heightPx)` — returns `{caps, slats}`: 2 caps and 16 side slats, each `{width, height, left, top, transform}`. Root cause: each `D x D` cap sat at the CSS default `left: 0; top: 0` on a `D x H` wrapper — correct only when `H == D`; with `transform-origin: 50% 50%` (never overridden), a short prop hub (`H << D`) or a tall standoff-shaped post (`H >> D`) rotates each cap about the wrong point and it swings off axis. The 16 side slats already re-centered horizontally before this Buy — reused unchanged, just relocated into the new helper. Fix: center each cap first (`left: 0`, `top: (H-D)/2` — negative when `H < D`), then rotate, then `translateZ(H/2)` — never `translateY` again after centering. `Solid3D.tsx`'s `cylinder` branch now consumes the helper; `cuboidFaces.ts`, the disk branch, `SCENE3D.pxPerMm`, the projector, the `geometry` DTO, and `spatial_board.py` all stay **byte-unchanged**. Verified against a short-hub fixture (Ø130.72 x 6.8mm -> px `65.36x3.4`, cap `top=-30.98`, `translateZ(1.7px)`) and a tall-post fixture (Ø6 x 30mm -> px `3x15`, cap `top=6`, `translateZ(7.5px)`) — both directions of the bug. Still exactly 2 caps + 16 slats, N=16 frozen, no 17th face. See [implementation review](../.jes/artifacts/implementation_review_geometry_taller_css_cylinder_faces_b1.md).

**Visor cylinder ≠ CAD ≠ fit ≠ extra parts ≠ round metal ≠ a standoff hole pattern** — 2 CSS caps + 16 CSS slats that meet on a declared Ø x H exist. Nothing here is a turned standoff, a prop hub from the mill, or a fit verdict. D2 docs review PASS WITH NOTES @ package `0.5.36` (awaiting Engineer spot-check + ★ ACCEPT, no `v0.5.36` tag yet) — [`B1-docs-truth-sync-after-c35`](../.jes/artifacts/implementation_contract_docs_truth_sync_after_c35_b1.md) · [review](../.jes/artifacts/implementation_review_docs_truth_sync_after_c35_b1.md).

**C36 (`B1-fase-c-sim-6dof-plant`, package/tag `v0.5.37`, ★ ACCEPT CLOSED) — a toy body that can move through space, not just tilt:**
[`.jes/artifacts/implementation_contract_fase_c_sim_6dof_plant_b1.md`](../.jes/artifacts/implementation_contract_fase_c_sim_6dof_plant_b1.md) adds `ToyQuad6DofPlant` (Python `plant.py` + C++ `plant.hpp`/`plant.cpp`) — a **second, separate** toy plant alongside the unchanged `ToyQuadAttitudePlant` (C11/C13), whose own body stays byte-for-byte untouched (verified purely-additive diff, same discipline C26's `esc.cpp` extension already established) — its own closed-loop tilt-recovery smoke still strictly decreases and recovers, unchanged. `ToyQuad6DofPlant` reuses the identical motor-force torque-proxy formulas for attitude, plus one new toy translation law: `thrust_body = (0, 0, thrust_gain * sum(motor_forces))` in body `+Z`, `a_world = R(q) * (thrust_body / mass_kg) + g_world` (`g_world = (0, 0, -9.81)`, ENU, semi-implicit Euler) — `mass_kg`/`thrust_gain` both toy tuning constants, never sourced from any real hardware/catalog. `ImuSample` stays exactly as C11-shaped as before — gravity rotated into body frame plus gyro, **no specific-force/linear-acceleration term** — pose truth lives only on `true_position_m`/`true_velocity_mps` getters, deliberately kept out of the IMU sample since C7's complementary filter expects "down" from the accelerometer and would fight an injected hover specific-force. `FlightControlLoop.step`/`ControlLoop::step` stay byte-unchanged in role — still never call any plant. New smoke helper `run_sim_6dof_smoke` (Python) chains `loop.step` → `plant.step` exactly like C11's own smoke, showing the resulting ENU pose actually climbs and drifts under a documented small-tilt + hover-collective case. See [implementation report](../.jes/artifacts/implementation_report_fase_c_sim_6dof_plant_b1.md) (own report — no external review yet).

**6-DoF toy plant ≠ flying ≠ product aero ≠ MY5 truth. Pose in RAM ≠ GO_TO ≠ altitude hold ≠ house map. `ImuSample` C11-shaped ≠ specific-force accelerometer** — a deterministic plant with position+velocity+attitude that consumes mixer forces exists. **★ ACCEPT CLOSED** @ **`v0.5.37`**.

**C37 (`B1-fase-c-mag-yaw-rung`, package/tag `v0.5.38`, ★ ACCEPT CLOSED) — yaw stops being only gyro drift:**
[`.jes/artifacts/implementation_contract_fase_c_mag_yaw_rung_b1.md`](../.jes/artifacts/implementation_contract_fase_c_mag_yaw_rung_b1.md) adds a simulated magnetometer and fuses it so estimated yaw finally has an absolute reference, then unlocks the RC yaw stick now that heading is honest. New `MagSample` + `SimulatedMagHal` (Python `mag.py`/`sim_mag_hal.py` + C++ `mag.hpp`/`mag.cpp`) — a deterministic HAL that rotates a fixed toy world field (`East=0, North=1.0, Up=0.0` — deliberately horizontal-only, a documented toy default, never a datasheet claim) into body frame using the caller-supplied **true** attitude; this HAL never owns or secretly consults a plant. `ComplementaryAttitudeEstimator` (C7) is **extended, not rewritten**: `update(sample, mag=None)` takes an optional `MagSample` — absent, the only path C7's own 16 pre-existing tests ever exercised, behavior is byte-for-byte identical to before this Buy (all 16 pass unchanged; the one C++ freeze-check exception is fully disclosed in the report). Present, a world-frame yaw-only correction (horizontal mag heading vs a documented world-north reference, composed on the left of the tilt-corrected estimate) pulls the estimate toward true north — verified converging from a 30-degree offset to under 5 degrees in 30 updates. Still one estimator, not a second AHRS "to compare." `map_rc_to_loop_inputs` (C25) unlocks `RC_CH_YAW` (index 3, previously present-but-unused): deflection scales to `RC_MAX_YAW_RAD` (180 degrees, a documented full-range convention distinct from roll/pitch's own 30-degree tilt limit) and composes into the setpoint quaternion's own yaw term — verified to reduce to the exact pre-C37 roll/pitch-only formula when yaw is `0`. Two pre-existing tests (Python + C++) that locked the old "yaw does nothing" decision are retargeted, disclosed, to lock the new intentional behavior instead. `FlightControlLoop.step`/`ControlLoop::step` stay byte-unchanged — mag fusion happens outside `step`, caller-driven. See [implementation report](../.jes/artifacts/implementation_report_fase_c_mag_yaw_rung_b1.md) (own report — no external review yet).

**Sim mag ≠ live mag chip ≠ ICM SPI mag. Yaw reference in RAM ≠ compass flight. RC yaw unlock ≠ motors ≠ flying** — a simulated field gives the estimator an absolute heading. **★ ACCEPT CLOSED** @ **`v0.5.38`**.

**C38 (`B1-fase-c-altitude-loop`, package `0.5.39`, ★ ACCEPT CLOSED @ `v0.5.39`) — collective stops being only the RC stick or a fixed constant:**
[`.jes/artifacts/implementation_contract_fase_c_altitude_loop_b1.md`](../.jes/artifacts/implementation_contract_fase_c_altitude_loop_b1.md) adds a simulated height sensor and a z→collective controller so `ToyQuad6DofPlant` can climb toward, or hold near, a documented height in sim. New `AltitudeSample` + `SimulatedAltitudeHal` (Python `sim_altitude_hal.py` + C++ `sim_altitude_hal.hpp`/`.cpp`) — a **direct altitude port**, not a fake ISA pressure/meteorology model: `read_altitude(true_z_m, t_s)` returns the caller-supplied true height directly; this HAL never owns or secretly consults a plant. New `AltitudeController` (Python `altitude_controller.py` + C++ `altitude_controller.hpp`/`.cpp`) — one law only, run **outside** `FlightControlLoop.step`: `collective = clip(hover_bias + kp*(z_des_m - altitude_m) - kd*vz_mps, 0, 1)`. `hover_bias` defaults to the toy hover point that actually balances `ToyQuad6DofPlant`'s own default gravity/thrust constants (`mass_kg*g/(4*thrust_gain)` ≈ `0.1226`) — **not** the IC's suggested `hover_collective()` (`0.5`), verified empirically to badly mismatch this plant's own physics (never settles near the setpoint, permanently overshoots). `vz_mps` is caller-supplied (the smoke passes `ToyQuad6DofPlant.true_velocity_mps[2]` directly), not internally integrated. Deliberately named `sim_altitude_hal.py`/`altitude_controller.py`, not `altitude.py` — this codebase already ships `attitude.py` (the C7 estimator); "altitude"/"attitude" differ by one letter, avoided the same way in file names, class names (a plain `z_des_m` float is used instead of an `AltitudeSetpoint` that would sit next to the existing `AttitudeSetpoint`), and the C++ headers. New smoke `run_altitude_loop_smoke` chains `alt.compute(...)` → `loop.step(...)` → `plant.step(...)` exactly as the IC requires — verified converging monotonically (no overshoot) to within `0.07m` of a `z_des_m=2.0` setpoint over 500 steps. See [implementation report](../.jes/artifacts/implementation_report_fase_c_altitude_loop_b1.md) · [review](../.jes/artifacts/implementation_review_fase_c_altitude_loop_b1.md).

**Sim altitude ≠ live baro/ToF chip. z→collective in RAM ≠ altitude hold in air** — a simulated height measurement drives thrust so the toy plant moves in `z`. Nothing here reads a real sensor or claims any real vehicle holds altitude. **★ ACCEPT CLOSED** @ **`v0.5.39`**.

**C39 (`B1-fase-c-position-loop`, package `0.5.40`, ★ ACCEPT CLOSED @ `v0.5.40`) — horizontal motion stops being only open-loop tilt or luck:**
[`.jes/artifacts/implementation_contract_fase_c_position_loop_b1.md`](../.jes/artifacts/implementation_contract_fase_c_position_loop_b1.md) adds a simulated horizontal position sensor and an xy→tilt controller so `ToyQuad6DofPlant` can chase a documented ENU point in sim. New `PositionSample` + `SimulatedPositionHal` (Python `sim_position_hal.py` + C++ `sim_position_hal.hpp`/`.cpp`) — a **direct ENU port**, not a NMEA/WGS84/optical-flow stack: `read_position(true_x_m, true_y_m, t_s)` returns the caller-supplied true horizontal position (East/North) directly; optional `z_m` is allowed but unused by the controller; this HAL never owns or secretly consults a plant. New `PositionSetpoint(x_m, y_m)` + `PositionController` (Python `position_controller.py` + C++ `position_controller.hpp`/`.cpp`) — one law only, run **outside** `FlightControlLoop.step`: `pitch_rad = clip(kp*(x_des-x) - kd*vx, -max_tilt_rad, max_tilt_rad)`, `roll_rad = clip(-(kp*(y_des-y) - kd*vy), -max_tilt_rad, max_tilt_rad)`, composed into an `AttitudeSetpoint` quaternion with yaw held at `0`; `max_tilt_rad` defaults to `RC_MAX_TILT_RAD` (pi/6, 30 degrees, C25) rather than duplicating that constant. Signs derived and proven: a positive pitch rotates body +Z thrust onto positive world X (East) — no sign flip on the pitch term; a positive roll rotates body +Z thrust onto negative world Y (South) — hence the sign flip on the roll term; verified with a direct closed-loop test (East-only setpoint moves `true_position_m[0]` up, North-only setpoint moves `true_position_m[1]` up, no cross-axis coupling). Unlike C38's `altitude`/`attitude` near-homograph, this Buy has no naming-collision risk, so `PositionSetpoint`/`PositionController`/`PositionSample`/`SimulatedPositionHal` are used directly, typed, per the IC's own preference. New smoke `run_position_loop_smoke` chains `pos.compute(...)` → `alt.compute(...)` (C38's own `AltitudeController`, unchanged) → `loop.step(...)` → `plant.step(...)` — starting at `(0,0,0)` with `x_des_m=5.0, y_des_m=0.0, z_des_m=2.0`, verified horizontal distance shrinking from `5.0m` to under `0.25m` over 1000 steps (10 seconds sim time). See [implementation report](../.jes/artifacts/implementation_report_fase_c_position_loop_b1.md) · [review](../.jes/artifacts/implementation_review_fase_c_position_loop_b1.md).

**Sim position ≠ live GPS/flow chip. xy→tilt in RAM ≠ position hold in air ≠ GO_TO executed. An ENU point in RAM ≠ a house map** — nothing here reads a real sensor or claims copper execute. **★ ACCEPT CLOSED** @ **`v0.5.40`**.

**C40 (`B1-fase-c-autonomy-executor`, package `0.5.41`, ★ ACCEPT CLOSED @ `v0.5.41`) — autonomy verbs stop being only labels that RejectAll:**
[`.jes/artifacts/implementation_contract_fase_c_autonomy_executor_b1.md`](../.jes/artifacts/implementation_contract_fase_c_autonomy_executor_b1.md) adds `SimAutonomyExecutor` (Python `flight_software/autonomy/sim_executor.py` + C++ `sim_autonomy_executor.hpp`/`.cpp`) — a **separate, sim-only** driver, not a change to the C4 command surface: `propose_command`/`submit_command`/`AutonomySubmissionResult` are completely untouched, and `execution` is never set to `"executed"` anywhere in this module. Every `tick(verb, params, dt_s)` call reuses, never reimplements, `PositionController.compute` (C39) → `AltitudeController.compute` (C38) → `FlightControlLoop.step` (C24) → `plant.step` (C36) — the same four-call chain `run_position_loop_smoke` already used, now wrapped as a stateful per-verb driver. **HOLD** freezes a `PositionSetpoint` at the current (or caller-supplied) xy + z the first tick it's ticked, then holds that frozen point every subsequent tick regardless of drift. **GO_TO** requires finite `x_m`/`y_m`; `z_m` is optional, defaulting to the altitude frozen at the first `GO_TO` tick (not a new invented cruise-altitude constant). **LAND** freezes xy the same way `HOLD` does and ratchets `z_des_m` downward by a documented `land_rate_mps` (default `0.5 m/s`) toward a documented floor `z_land_m` (default `0.0`) — not a claim of touchdown gear. Any other verb raises `ValueError`. Respects C39 N2 (z may droop under tilt): tests do not require altitude glued to setpoint during an aggressive `GO_TO` chase; `HOLD` asserts bounds only **after** settling; `LAND` only asserts z strictly decreases toward the floor. Verified: `GO_TO` shrinks horizontal distance to `(3.0, 0.0)` from `3.0m` to under `0.1m` over 1500 steps; `HOLD` (after that convergence) keeps a 500-tick window within `0.5m` on every axis; `LAND` (from a converged `z≈2.0`) brings z under `0.5m` over 1000 steps. See [implementation report](../.jes/artifacts/implementation_report_fase_c_autonomy_executor_b1.md).

**Verb → setpoints in RAM ≠ execute on copper. Sim HOLD/LAND/GO_TO ≠ flying ≠ Safety allow** — `propose_command`/`submit_command` through the default `RejectAllSafetyGate` still returns `reject`/`not_attempted` for all three verbs; this Buy does not touch Safety (that's C41). **★ ACCEPT CLOSED** @ **`v0.5.41`**.

**C41 (`B1-fase-c-safety-sim-policy`, package `0.5.42`, ★ ACCEPT CLOSED @ `v0.5.42`) — Safety can say yes to the same three verbs the sim executor understands:**
[`.jes/artifacts/implementation_contract_fase_c_safety_sim_policy_b1.md`](../.jes/artifacts/implementation_contract_fase_c_safety_sim_policy_b1.md) widens `ArmedAllowlistSafetyGate` (C17) rather than adding a second, competing gate class — its allow-list grows from `{HOLD, LAND}` to `{HOLD, LAND, GO_TO}`, still one opt-in gate, still starting disarmed, still parsing `autonomy:{verb}:{id}`. `default_safety_gate()` is unchanged — always `RejectAllSafetyGate`; no `AllowAllSafetyGate` exists anywhere under `src/`. **Allow still never means execute:** `submit_command`'s `allow` branch stays `execution="not_implemented"` for all three verbs — this gate is never called from `SimAutonomyExecutor.tick` (C40), and that executor is never called from `submit_command` or from `safety.py`; the two APIs stay entirely separate call paths, same as C40 left them. `AuthoritySignal` still never flips `allow`, re-verified for `GO_TO` specifically. C17's own pre-existing tests were disclosed-retargeted (not weakened): `GO_TO` moved from the "rejected" list to the "allowed" list, since the allow-list itself changed by design. See [implementation report](../.jes/artifacts/implementation_report_fase_c_safety_sim_policy_b1.md).

**allow ≠ execute ≠ flying. sim allowlist ≠ copper arm ≠ motors. GO_TO allow ≠ GO_TO in air ≠ `SimAutonomyExecutor.tick`** — nothing here dispatches to any actuator; Safety stays a verdict, not a dispatcher. **★ ACCEPT CLOSED** @ **`v0.5.42`**.

**C42 (`B1-fase-c-icm-register-client`, package `0.5.43`, ★ ACCEPT CLOSED @ `v0.5.43`) — the placeholder probe becomes a named device transaction:**
[`.jes/artifacts/implementation_contract_fase_c_icm_register_client_b1.md`](../.jes/artifacts/implementation_contract_fase_c_icm_register_client_b1.md) adds a second, named client of `SpiBytePort` beside `probe_rx` (C34, kept, unmodified): `read_who_am_i(SpiBytePort&) -> WhoAmIResult` (C++ only, `native/flight_control/include/jarvis/fc/icm42688p.hpp`/`.cpp` — same C++-native axis as C32-C34, no Python SPI port). **Datasheet citation:** TDK InvenSense ICM-42688-P (DS-000347) — `WHO_AM_I` register at address `0x75`, expected value `0x47` — verified this session via web search cross-referenced against the open-source PX4-Autopilot driver's own register header (`InvenSense_ICM42688P_registers.hpp`), since every direct datasheet PDF fetch attempted this session returned HTTP 403; that corroboration path is disclosed in the header comment rather than a fabricated page/table citation. Transaction: the standard InvenSense-family 2-byte full-duplex read — `TX[0] = 0x75 | 0x80` (read bit set), `TX[1]` = dummy, `RX[1]` = value — sent through `SpiBytePort::transfer`, no bypass (verified with a recording test double that captures the exact TX bytes, not just a real-port smoke). `WhoAmIResult{value, matches_expected, bytes_transferred}` — a short transfer (an exhausted `ScriptedSpi` fixture) is always a documented mismatch, never a silent success; `LoopbackSpi` (which only ever echoes TX) is verified to never falsely claim a match. No second register was added — a disclosed scope choice (one well-corroborated register beats a second, weakly-sourced one), not a silent omission. `spi.hpp`/`spi.cpp`/`spi_probe.hpp`/`spi_probe.cpp` get zero edits. See [implementation report](../.jes/artifacts/implementation_report_fase_c_icm_register_client_b1.md).

**ICM register client on ScriptedSpi ≠ chip SPI1. WHO_AM_I in RAM ≠ gyro live ≠ samples in step. Datasheet cite ≠ lab measurement on copper** — nothing here reads a real chip or feeds any sample into `step`. **★ ACCEPT CLOSED** @ **`v0.5.43`**.

**C43 (`B1-fase-c-craft-fs-bind`, package `0.5.44`, ★ ACCEPT CLOSED @ `v0.5.44`) — the software-month tip can finally name which craft it's about:**
[`.jes/artifacts/implementation_contract_fase_c_craft_fs_bind_b1.md`](../.jes/artifacts/implementation_contract_fase_c_craft_fs_bind_b1.md) adds a **one-way, read-only** bind: `bind_profile_to_craft_identity(profile, craft_sku, library=None) -> BoundVehicleProfile` (`src/jarvis/vehicle_profiles/bind.py`) — `vehicle_profiles` reads craft identity via `ComponentLibrary` (`jarvis.knowledge.library`, the existing sole reader of `library/` JSON); craft packages (`core`/`adapters`/Continuity/CLI/Board) still never import `jarvis.flight_software`/`jarvis.vehicle_profiles` — a directed seam, not a two-way bridge. `BoundVehicleProfile` is a small wrapper type (`profile` + `craft_sku`/`craft_manufacturer`/`craft_model`/`craft_size_class_inch`), not an extension of `VehicleProfile` itself — the C3 schema (`extra="forbid"`, pinned by 40+ Buys' own fixtures) stays completely untouched; `load_smoke_profile()`/`smoke_quad_hal_imu` are unaffected. New fixture `this_quad.json` (same C3-shaped declaration fields as `smoke_quad_hal_imu.json`, no geometry/mass of its own) binds, via the new helper, to the desk's own `hglrc_my5_5in` catalog frame (`library/frames/_datos.json`) — verified mirroring that row's `manufacturer="HGLRC"`/`model="MY5"`/`size_class_inch=5.0` verbatim. An unknown SKU raises `KeyError` — the same error `ComponentLibrary.get_frame` already raises, never a silent empty bind. Read-only, verified: the bind never writes `library/frames/_datos.json` (mtime/content unchanged across a bind call) or any craft workspace file. See [implementation report](../.jes/artifacts/implementation_report_fase_c_craft_fs_bind_b1.md).

**Profile reads craft ≠ Continuity drives firmware. Craft identity in RAM ≠ flash ≠ arm ≠ flying. Directed seam ≠ craft imports flight_software** — no Continuity turn was added that flashes, arms, or submits into `flight_software`; `submit_command`/`propose_command` are never imported by `bind.py`. **★ ACCEPT CLOSED** @ **`v0.5.44`**. Software-month C36–C43 CLOSED. After ★ ACCEPT this closes the software-month arc — Assistant DC discussion may begin (still needs its own ★ to implement). Assistant/placement **PARKED** until C43 CLOSED. Standoff = visor-break. Parked until bench: DShot *wire* · on-chip USART · C30 desk DFU — see the [process lock](../.jes/artifacts/engineer_note_fase_c_process_lock_after_c6_2026_09_20.md).

**Byte-stream assembler ≠ UART open ≠ live ELRS ≠ a pilot link ≠ Safety allow** — typed chunks only. Board flash, craft↔FS, and deepen-C20-policy remain parked — see the [process lock](../.jes/artifacts/engineer_note_fase_c_process_lock_after_c6_2026_09_20.md).

### Historical sketch (still valid as narrative)

First design:

### `Skill / Capability Architecture Contract`

Define:

```text
Skill
├── identity
├── version
├── inputs
├── outputs
├── requirements
├── preconditions
├── permissions
├── execution
├── state
└── failure_modes
```

and:

```text
Capability
├── identity
├── provider
├── version
├── availability
├── requirements
└── health
```

Then design a:

> **Capability Registry**

so Jarvis can know which capabilities exist, which provider offers them, and whether they are available.

That design now lives as the JES artifact linked above — do not silently turn **this vision file** into an IC.

---

## 14) Principle to keep

> **Jarvis must not be built around a single drone. The drone must be the first physical system that consumes a general architecture of reusable capabilities.**

The critical work will be designing **boundaries and contracts before implementation**, because that is where it is decided whether years later we have a modular platform or a tightly coupled system.
