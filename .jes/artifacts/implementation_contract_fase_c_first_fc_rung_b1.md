# Implementation Contract — Fase C first `flight_control` rung (`B1-fase-c-first-fc-rung`)

**Project:** Jarvis  
**Date:** 2026-09-20  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (no fake “armed” / no ESC path / sensing ≠ flight)

**Status:** **ACCEPT CLOSED** (Engineer 2026-09-20) · package **`0.5.1`** · tag **`v0.5.1`**
**Parents:**
- [C0 Design Contract ★](design_contract_fase_c_skill_capability_architecture.md) — §7 FC progression · §10 attack order C3 · amendment (architecture ≠ implement until IC)  
- [C1 ★ ACCEPT](implementation_contract_fase_c_capability_registry_scaffold_b1.md) — empty Capability Registry @ **`v0.5.0`**  
- [C2 ★ ACCEPT](implementation_contract_fase_c_intent_safety_stub_b1.md) — Intent + `RejectAllSafetyGate` @ **`0.5.0`**  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**  

**Type:** **Implementation Contract** — **first on-disk `flight_software/` + `vehicle_profiles/`** with **one** `flight_control` rung only: **HAL + IMU sampling (simulated)**.  
**Package:** bump to **`0.5.1`** in this Buy; git tag **`v0.5.1`** only after Engineer ACCEPT.  
**Not** filtering · state estimation · attitude/rate/position controller · mixer · ESC/PWM · autonomy (`TAKEOFF`/`HOLD`/…) · ELRS · real MCU drivers · Intent→FC wiring · craft catalog `flight_controller` bind · Board chat · `AllowAllSafetyGate`.

**Outputs (required):**
1. Code under `src/jarvis/flight_software/` and `src/jarvis/vehicle_profiles/` (paths locked §0)  
2. Tests (module + smoke path §4)  
3. `.jes/artifacts/implementation_report_fase_c_first_fc_rung_b1.md`  
4. Docs honesty: PRIORIDAD · PLATFORM_CAPABILITY_VISION §13 · ARCHITECTURE — **first rung stub ≠ controlled flight**; update “no `flight_software/`” claims  
5. `pyproject.toml` → **`0.5.1`** (+ any version-pin tests that assert package version)

**Checkpoint:** package **`0.5.1`** · suite ≥ **3192** + new tests at ★

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-first-fc-rung`** — first `flight_control` rung (HAL + IMU sampling) under `vehicle_profiles` smoke |
| 2 | Authority to create trees | This IC is the **first** authority to create **`src/jarvis/flight_software/`** and **`src/jarvis/vehicle_profiles/`** on disk. C0/C1/C2 forbade them until now |
| 3 | Rung scope | **Only** MCU/HAL interface + **IMU sample acquisition**. C0 §7 ladder stops after “IMU → sampling”. **Do not** implement filtering, estimation, controller, mixer, or ESC in this Buy |
| 4 | Hardware honesty | **No real MCU / I²C / SPI / UART drivers.** Ship a **`SimulatedImuHal`** (name may vary) that produces **deterministic synthetic** IMU samples for tests/smoke. Real hardware HAL = later IC |
| 5 | Vehicle profile smoke | Ship **one** smoke profile (e.g. `smoke_quad_hal_imu`) that declares it expects this rung; a pure function / loader constructs the Sim HAL from the profile and reads ≥1 sample. **Not** Engineer Board smoke — **pytest smoke** |
| 6 | Capability registry | Product `CapabilityRegistry.load_default()` may stay **empty** **or** gain at most one **non-available** record: capability id `imu_sampling` (or `flight_control.imu_sampling`) with `availability: stub` \| `not_implemented` and `health: unknown`. **Forbidden:** `flight_control` (full stack) or any actuation capability marked live. **Lock preference:** keep **default registry empty**; tests may use **in-memory fixtures** only (same honesty pattern as C1) |
| 7 | Safety | Do **not** weaken C2. `default_safety_gate()` remains `RejectAllSafetyGate`. Sensing/read IMU does **not** require `allow` (not actuation). **Forbidden:** any new path that writes actuators, or any shipped `AllowAll*` |
| 8 | No Assistant coupling | Do **not** change `orchestrator.py` Continuity, Board, or `library/`. Do **not** wire `TerminalIntentAdapter` → FC. Craft catalog key `flight_controller` ≠ this package |
| 9 | Naming split (honesty) | Document in module docstring + report: **craft** `flight_controller` (BOM identity) vs **`flight_software.flight_control`** (vehicle-class control spine). They must not be conflated |
| 10 | Version | Bump **`0.5.0` → `0.5.1`**; tag **`v0.5.1`** on Engineer ACCEPT only |
| 11 | Vendor stacks | Betaflight / PX4 / ArduPilot **out of scope** — may appear later as Provider options inside FC, not this Buy |
| 12 | Forbidden | Autonomy command surface (C4) · ELRS (C5) · Conversation Engine · claiming “Jarvis can fly” · ESC/mixer/PWM · `available` enum value for flight |

**Product sentence:**

```text
Abrir flight_software/ y vehicle_profiles/ con el primer peldaño
honesto (HAL + IMU simulado + smoke de perfil) — sin fingir control
de actitud, mezclador ni vuelo.
```

---

## 1. Package layout (normative)

```text
src/jarvis/flight_software/
  __init__.py                 # package marker; honest docstring (stub rung ≠ flight)
  flight_control/
    __init__.py
    types.py                  # ImuSample (+ optional Vec3) — Pydantic or dataclass
    hal.py                    # Hal / ImuHal Protocol (or ABC)
    sim_imu_hal.py            # SimulatedImuHal — deterministic samples
    # NO: filter.py, estimator.py, controller.py, mixer.py, esc.py

src/jarvis/vehicle_profiles/
  __init__.py
  schemas.py                  # VehicleProfile record (minimal)
  loader.py                   # load_profile(id) / load_smoke_profile()
  data/
    smoke_quad_hal_imu.json   # one smoke profile seed
```

**Do not** create `flight_software/autonomy/` in this Buy (C4).  
**Do not** put HAL under `capabilities/` — capabilities stay contracts/registry; FS is the control spine.

Optional thin re-exports from `jarvis.flight_software` / `jarvis.vehicle_profiles` public `__init__` — keep surface small.

---

## 2. Types / APIs (normative)

### 2.1 `ImuSample`

Minimal fields (names may match project style):

| Field | Notes |
|---|---|
| `t_s` | float — sample time seconds (monotonic fake clock OK) |
| `accel_mps2` | 3-float tuple/list (x,y,z) |
| `gyro_rad_s` | 3-float tuple/list (x,y,z) |

`extra="forbid"` if Pydantic. **No** actuator fields.

### 2.2 `ImuHal` (Protocol / ABC)

```text
read_imu() -> ImuSample
# optional: reset() -> None
```

No `write_motor`, `set_pwm`, `arm`, `disarm` methods anywhere under `flight_software/` in C3.

### 2.3 `SimulatedImuHal`

- Implements `ImuHal`
- **Deterministic:** same sequence of samples given the same constructor seed / config (lock: accept an optional `seed: int = 0`)
- May return constant gravity-ish accel + zero gyro, or a tiny scripted sequence — either OK if deterministic and documented
- Must **not** open network sockets or claim hardware present

### 2.4 `VehicleProfile` (minimal)

| Field | Notes |
|---|---|
| `id` | str, e.g. `smoke_quad_hal_imu` |
| `display_name` | optional str |
| `vehicle_class` | Literal or str — at least `"quadcopter_smoke"` / `"unspecified"` |
| `rung` | Literal `"hal_imu"` for this Buy (extensible later) |
| `notes` | optional honesty string |

**Not required in C3:** full BOM bind from craft workspace, geometry, or catalog SKUs.

### 2.5 Smoke helper (pure)

```text
run_hal_imu_smoke(profile_id: str = "smoke_quad_hal_imu") -> list[ImuSample]
  # load profile → build SimulatedImuHal → read N>=1 samples → return
  # MUST NOT call SafetyGate for allow, MUST NOT touch actuators
  # MAY assert profile.rung == "hal_imu"
```

Place under `vehicle_profiles/` or `flight_software/flight_control/smoke.py` — pick one; report which.

---

## 3. Relationship to C1 / C2 (integration rules)

| Existing | C3 rule |
|---|---|
| `capabilities/` registry | Default empty unless Engineer amends §0.6; **no** `available` flight |
| `RejectAllSafetyGate` | Unchanged; still only shipped default |
| `Intent` / adapters | Untouched; **no** Continuity/CLI rewrite |
| Craft `flight_controller` | Untouched catalog identity — **orthogonal** |

Optional (not required): a test that builds an in-memory `CapabilityRecord(id="imu_sampling", availability=stub)` and asserts it does **not** appear in `load_default()`.

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | `SimulatedImuHal(seed=0).read_imu()` returns `ImuSample` with 3-vectors |
| T2 | Same seed → identical first sample (determinism) |
| T3 | `ImuHal` / public FC modules have **no** public method whose name contains `pwm` / `esc` / `motor` / `mixer` / `arm` / `actuat` |
| T4 | `load_profile("smoke_quad_hal_imu")` (or locked id) → `rung == "hal_imu"` |
| T5 | `run_hal_imu_smoke()` returns `len >= 1` samples |
| T6 | No `AllowAllSafetyGate` under `src/`; `default_safety_gate().evaluate(...)` still `reject` |
| T7 | `CapabilityRegistry.load_default()` still empty **or** only §0.6-allowed stub ids (if amended) — default lock: **still empty** |
| T8 | `pyproject` version **`0.5.1`**; update any tests that pin `0.5.0` |
| T9 | Grep/assert: zero new imports of `jarvis.flight_software` from `orchestrator.py` / craft Continuity paths |
| T10 | Full suite green (no craft regression) |
| T11 | Report confirms H-locks + naming split craft FC vs FS |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| Claiming controlled flight / “armed” | Only sensing stub |
| Real MCU drivers presented as product-ready | No bench / no hardware Buy |
| Mixer / ESC / PWM APIs | Later rungs |
| Autonomy verbs executing | C4 |
| Wiring chat Intent → HAL | Scope; craft stays |
| Marking full `flight_control` available | C1/C2 honesty continues |
| Confusing craft catalog FC with FS package | Different SoTs |

---

## 6. Docs

- PRIORIDAD: C3 in flight / CLOSED as appropriate  
- PLATFORM_CAPABILITY_VISION §13: C3 landed — first rung; **≠** Flight Software complete  
- ARCHITECTURE: new short § for `flight_software/` + `vehicle_profiles/` (stub rung)  
- Update any “forbidden to create `flight_software/`” past-tense notes that would become false

---

## 7. Acceptance

**PASS when:** T1–T11 · trees exist · only HAL+IMU sim rung · smoke profile works · Safety still reject-all · version `0.5.1` · no craft coupling · no actuators.

**FAIL if:** mixer/ESC shipped · `allow` by default · Intent→motors · registry claims available flight · autonomy package landed “for free”.

---

## 8. Handoff

```text
Engineer → ★ this IC (C3)
Claude   → implement flight_software/ + vehicle_profiles/ + tests + report + 0.5.1
Cursor   → review
Engineer → ACCEPT + tag v0.5.1
Cursor   → C4 IC (autonomy surface behind Safety) when Engineer prioritizes
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C2 ACCEPT @ 0.5.0. C3 B1-fase-c-first-fc-rung READY —
HAL+IMU sim under vehicle_profiles smoke; opens flight_software/ @ 0.5.1.
```

---

## 10. Engineer ★ checklist (optional amendments before Claude)

Confirm or amend in ★ message if needed:

1. Version **`0.5.1`** OK? (alt: stay `0.5.0` — say so)  
2. Default registry **stays empty** OK?  
3. Smoke profile id `smoke_quad_hal_imu` OK?  
4. Simulated-only HAL OK (no hardware attempt)?  
