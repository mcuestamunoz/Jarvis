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

---

## 13) Next work when that moment arrives

**Lectura humana (qué es “scaffold”, qué hace cada carpeta):**  
[`docs/ARCHITECTURE.md`](ARCHITECTURE.md) **§1a — Fase C en lenguaje llano**.

**Do not start by coding.**

**Design contract (★★ CLOSED 2026-09-20 with amendment):**  
[`.jes/artifacts/design_contract_fase_c_skill_capability_architecture.md`](../.jes/artifacts/design_contract_fase_c_skill_capability_architecture.md)  

**C1 (ACCEPT CLOSED, tag `v0.5.0`):**  
[`.jes/artifacts/implementation_contract_fase_c_capability_registry_scaffold_b1.md`](../.jes/artifacts/implementation_contract_fase_c_capability_registry_scaffold_b1.md) — schemas + **empty** Capability Registry stub, `src/jarvis/capabilities/` → package **`0.5.0`**. No flight runtime, no execution path. See [implementation report](../.jes/artifacts/implementation_report_fase_c_capability_registry_scaffold_b1.md).

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
