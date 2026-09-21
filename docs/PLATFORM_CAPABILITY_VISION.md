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

**C++ ESC stub ≠ hardware write / ≠ ESC online / ≠ motors spinning** — this closes the C++ tree's module parity with the Python wooden ladder (filter/attitude/controller/rate_torque/mixer/esc, plus the plant tip); nothing here drives a real ESC or claims a propeller turns. **Next Engineer-prioritized front (still one at a time):** an MCU cross-compile target, deepen C++ tests, real Safety, or a real link — see the [process lock](../.jes/artifacts/engineer_note_fase_c_process_lock_after_c6_2026_09_20.md).

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
