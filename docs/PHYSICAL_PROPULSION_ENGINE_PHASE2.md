# Phase 2 — Physical Propulsion Engine

**Status:** **P2-1 delivered** (`checkpoint-phase2-p2-1`); **P2-2+ open** (vision below)  
**Date:** 2026-08-19 (implementation status sync: 2026-08-31)  
**Author:** Engineer  
**Depends on:** Physical Component Catalog V1 — Impl A–D ✅ (see [`PHYSICAL_COMPONENT_CATALOG_V1.md`](./PHYSICAL_COMPONENT_CATALOG_V1.md) §13)  
**Related:** [`PHYSICAL_COMPONENT_CATALOG_V1.md`](./PHYSICAL_COMPONENT_CATALOG_V1.md), [`ENGINEERING_READINESS_VISION.md`](./ENGINEERING_READINESS_VISION.md)

> **Document role:** Forward-looking vision for Phase 2 physics (operating points, power model, real-world validation). **P2-1 lookup operating point is implemented** — see §12.1. Sections 1–11 and 14–15 remain the design target for work not yet started.

---

## 0. Relationship to Catalog V1

```text
Catalog V1 (Impl A→D)     Phase 2
─────────────────────      ───────────────────────────
Components as entities  →  Components interact physically
catalog_ref binding     →  Operating points from bound combos
SKU identity persists   →  Performance data tied to real SKUs
Compatibility checks    →  Full electro-mechanical validation
```

Catalog V1 answers: **"what components exist and how are they linked to the project?"**  
Phase 2 answers: **"what does this combination of components actually produce?"**

**Prerequisites met:** Catalog V1 Impl B+ (bind + identity persist) and Impl D (BOM SKU display) are delivered. **P2-1** (lookup operating point from bound motor + propeller + voltage) is live — see §12.1. Remaining Phase 2 scope (§14–15) is still open.

---

## 1. Objective

Evolve from a system that assigns fixed thrust/power per motor toward a **physics-based model where propulsion results emerge from real component combinations under specific operating conditions**.

The question changes from:

> "What motor gives me ≥ 8.5 N?"

to:

> "What combination of motor + propeller + battery + ESC produces ≥ 8.5 N/motor within electrical and physical limits?"

and ultimately:

> "Which physically valid configuration is best for this project's objective?"

---

## 2. Current model (as-is)

```text
Motor
├── KV
├── mass
├── thrust     ← fixed value, context-free
└── power      ← fixed value, context-free
```

Calculation:

```text
thrust_per_motor × motor_count = available_thrust
available_thrust vs required_thrust = T/W ratio
```

Useful for early architecture validation but **does not represent real motor behavior**.

---

## 3. Fundamental problem

A motor does not have a universal thrust value. Thrust depends on the full operating context:

```text
MOTOR + PROPELLER + VOLTAGE + ESC + CONDITIONS
                    ↓
            OPERATING POINT
                    ↓
    ┌───────────────┼───────────────┐
    ↓               ↓               ↓
  THRUST         CURRENT           RPM
    ↓               ↓               ↓
    └────────── POWER ──────────────┘
```

The statement `Motor X = 9.5 N` is incomplete.  
The correct statement is: `Motor X + Propeller Y + Voltage Z = 9.5 N`.

---

## 4. Target model

```text
MOTOR
  +
PROPELLER
  +
BATTERY / VOLTAGE
  +
ESC
  +
CONDITIONS
  ↓
OPERATING POINT
  ↓
PHYSICAL RESULTS
  ├── RPM
  ├── Current (A)
  ├── Voltage (V)
  ├── Electrical power (W)
  ├── Mechanical power (W)
  ├── Thrust (N)
  └── Efficiency
```

---

## 5. Component models

### 5.1 Motor (real)

Motor represents only motor-intrinsic properties:

```text
Motor
├── manufacturer
├── model
├── kv
├── mass
├── voltage_range
├── max_current
├── resistance
└── performance_tests[]
```

Motor does NOT contain a standalone `thrust = 9.5 N`. That thrust belongs to an operating point.

### 5.2 Propeller (independent entity)

```text
Propeller
├── manufacturer
├── model
├── diameter
├── pitch
├── blade_count
├── material
└── mass
```

Same propeller produces different results depending on motor and voltage.

### 5.3 Battery

```text
Battery
├── manufacturer
├── model
├── chemistry
├── cells
├── nominal_voltage
├── capacity
├── discharge_rating
├── mass
└── internal_resistance
```

Voltage directly affects the operating point of the propulsion system.

### 5.4 ESC

ESC controls electrical power to the motor. Primary validation:

```text
required_current ≤ ESC_continuous_current
voltage_compatibility
protocol_compatibility
```

```text
ESC
├── manufacturer
├── model
├── voltage_range
├── continuous_current
├── peak_current
├── protocol
├── mass
└── efficiency
```

---

## 6. Operating Point (central concept)

An operating point represents a concrete combination:

```text
Operating Point
├── motor_id          → catalog_ref
├── propeller_id      → catalog_ref
├── battery_id        → catalog_ref (voltage source)
├── esc_id            → catalog_ref
├── voltage (V)
├── current (A)
├── rpm
├── thrust (N)
├── electrical_power (W)    = V × I
├── mechanical_power (W)    = P_elec × η_motor
├── efficiency
└── source                  → manufacturer_test | calculated | estimated
```

### Performance data

Manufacturer/test data stored as operating points:

```text
performance_test
├── motor: EMAX RS2205 2300KV
├── propeller: Gemfan 5045 BN
├── voltage: 16.2 V
├── current: 24 A
├── thrust: 955 gf ≈ 9.37 N
└── power: ~389 W
```

---

## 7. Power model

### Electrical power

```text
P_electrical = V × I
```

### Mechanical power

```text
P_motor_input = P_battery × η_ESC
P_shaft = P_motor_input × η_motor
```

JARVIS must distinguish electrical power ≠ mechanical power.

---

## 8. Thrust and validation

### Thrust per motor

Prioritize `manufacturer_test_data` over theoretical estimates.

```text
955 gf × 0.00980665 = 9.37 N
```

### Total thrust (quadrotor)

```text
9.37 N × 4 = 37.48 N
```

### Safety margin

```text
safety_margin_ratio = available_thrust / required_thrust
```

Classification: FAIL (<1.0) · CRITICAL (≈1.0) · WARNING (1.0–1.1) · PASS (>1.1)

---

## 9. Data traceability

Every physical value must have provenance:

```text
thrust:
  value: 9.37 N
  source_type: manufacturer_test | calculated | estimated | assumed
  source_reference: ...
  conditions:
    motor: EMAX RS2205 2300KV
    propeller: Gemfan 5045 BN
    voltage: 16.2 V
  confidence: high | medium | low
```

JARVIS must never present an estimate as experimental data.

---

## 10. Data architecture

```text
Component
├── Motor
├── Propeller
├── Battery
├── ESC
└── Sensor

PerformanceData
├── motor_id
├── propeller_id
├── voltage
├── current, rpm, thrust, power, efficiency
├── source
└── conditions

OperatingPoint
├── motor, propeller, battery, esc
├── voltage, current, rpm
├── thrust
├── electrical_power, mechanical_power
└── efficiency
```

Separation between **components** and **performance data** is fundamental.

---

## 11. Evolution path

```text
Model 0 (done)          Model 1 (current)         Model 2 (Phase 2)
──────────────           ─────────────────         ──────────────────
Motor → fixed thrust     Motor + KV + estimates    Motor + Prop + Battery + ESC
       ↓                        ↓                          ↓
  thrust total             thrust estimated          Operating Point
       ↓                        ↓                          ↓
      T/W                      T/W                  Thrust + Power + Current
                                                           ↓
                                                     Full validation
```

---

## 12. Implementation strategy

### 12.1 P2-1 — Lookup Operating Point ✅ (delivered)

> Tag: **`checkpoint-phase2-p2-1`**. Propeller catalog pick UX: **`v0.3.0`** / **`checkpoint-propeller-catalog-bind`**.

**Delivered (as-is, not re-specified here):**

- `resolve_operating_point` — exact / fallback OP from bound motor SKU + propeller SKU + voltage
- Curated seeds in `library/` (e.g. `emax_rs2205s_2300`, `sunnysky_r2305_2500` + propeller rows)
- Bridge into calc/sim via `component_writers` / propulsion resolution evidence
- Live CLI: motor bind → propeller pick → `exact_operating_point` or `fallback_operating_point` with honest thrust evidence

**Not delivered by P2-1 (still §14–15 vision):** full power model, Ct/Cp curves, Real World Validation Case, system-level OP optimization.

### 12.2 First validation: Real World Validation Case (P2-2+)

Do NOT introduce a massive component catalog immediately.

Start with a small, well-documented set:

```text
2–5 real motors
2–3 real propellers
1–2 real batteries
1–2 real ESCs
```

Build the first validation case:

```text
REAL DATA → JARVIS MODEL → CALCULATED RESULT → compare divergence
```

Correct the physical model before scaling the catalog.

### Success criteria

1. Identify a real component
2. Identify its operating conditions
3. Obtain manufacturer/test data
4. Calculate derived magnitudes correctly
5. Differentiate real data from estimates
6. Select physically compatible combinations
7. Calculate thrust per motor and total
8. Calculate electrical power
9. Estimate mechanical power
10. Calculate consumption
11. Validate ESC and battery limits
12. Calculate T/W and safety margin
13. Propagate design changes to all dependent calculations
14. Maintain full data provenance traceability

---

## 13. Infrastructure prerequisites (from Catalog V1 + readiness)

| Prerequisite | Source | Status |
|---|---|---|
| Components as typed entities with identity | Impl A | ✅ |
| catalog_ref binding (SKU ↔ project) | Impl B | ✅ |
| Electrical compatibility (ESC ↔ motor) | ERF-2 | ✅ |
| Catalog-aware DSE + thrust bridge | Impl C | ✅ (`checkpoint-impl-c`) |
| BOM consumes SKU identity (`[sku]`, `sku_resolved`) | Impl D + IC 3 | ✅ (`checkpoint-impl-d`, propeller branch `checkpoint-closure-policy`) |
| Live catalog pick UX (motor / propeller / battery) | G21, v0.3.0, IC 2 | ✅ |
| catalog_ref visible in gaps/continuity ranking | G9-A / C-108 | 🟡 partial (catalog-gap demotion only; full handoff deferred) |
| Lookup operating point from bound combo | **P2-1** | ✅ (`checkpoint-phase2-p2-1`) |

---

## 14. Guiding principle

> **A motor does not produce a fixed thrust. A propulsion system produces a physical result under specific conditions.**

```text
MOTOR ≠ THRUST

MOTOR + PROPELLER + VOLTAGE + ESC + CONDITIONS
= OPERATING POINT
= THRUST + POWER + CURRENT + RPM + EFFICIENCY
```

This conceptual shift is the foundation for connecting JARVIS's deterministic calculations with real-world component behavior.

---

## 15. Scope boundaries

**In scope (Phase 2):**
- Operating point model and data architecture
- Performance data storage and retrieval
- Power model (electrical + mechanical)
- Thrust from real component combinations
- Data provenance and confidence levels
- Real World Validation Case

**Out of scope (future):**
- Aerodynamic propeller models (Ct/Cp curves)
- Thermal modeling
- Dynamic flight simulation
- Environmental conditions (altitude, temperature)
- Fatigue / lifecycle modeling

---

**End of vision document.**
