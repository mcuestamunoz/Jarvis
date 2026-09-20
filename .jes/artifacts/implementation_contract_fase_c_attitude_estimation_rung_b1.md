# Implementation Contract — Fase C attitude estimation rung (`B1-fase-c-attitude-estimation-rung`)

**Project:** Jarvis  
**Date:** 2026-09-20  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (attitude stub ≠ flight-verified · no controller/ESC · one algorithm only)

**Status:** ★ ACCEPT CLOSED @ **`v0.5.5`** (Engineer 2026-09-20)  
**Parents:**
- [C0 Design Contract ★](design_contract_fase_c_skill_capability_architecture.md) — §7 FC progression (`filtering → state estimation → controller → …`) · one rung per IC  
- [C6 ★ ACCEPT](implementation_contract_fase_c_imu_filtering_rung_b1.md) — `ImuLowPassFilter` / filtered `ImuSample` @ **`v0.5.4`**  
- [C3 ★ ACCEPT](implementation_contract_fase_c_first_fc_rung_b1.md) — HAL + `SimulatedImuHal` · Engineer C++ amendment  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no Safety-real / C++ / ELRS in this Buy  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — **third** `flight_control` rung only: **IMU-based attitude estimation** (quaternion + body rates) from filtered IMU samples.  
**Package:** bump to **`0.5.5`** in this Buy; git tag **`v0.5.5`** only after Engineer ACCEPT.  
**Not** position/velocity navigation · mag/GPS/baro fusion · gyro bias learning · controller · mixer · ESC/PWM · live autonomy execution · real ELRS · craft wiring · `AllowAllSafetyGate` · production C++ FC tree · opening a second platform front.

**Outputs (required):**
1. Code under `src/jarvis/flight_software/flight_control/` (prefer new `attitude.py` — **no** new top-level package; **no** `flight_software/estimation/` tree required)  
2. Tests (module + thin smoke path §4)  
3. `.jes/artifacts/implementation_report_fase_c_attitude_estimation_rung_b1.md`  
4. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE — **attitude stub ≠ flight-verified attitude / ≠ controlled flight**; keep C++ honesty phrase  
5. `pyproject.toml` → **`0.5.5`** (+ re-pin version-checkpoint tests that assert `0.5.4`)

**Checkpoint:** package **`0.5.5`** · suite ≥ **3249** + new tests at ★

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-attitude-estimation-rung`** — next C0 §7 rung after filtering: **attitude estimation only** |
| 2 | One front | Do **not** fold real Safety, C++/CMake FC, ELRS, or craft↔FS wiring into this Buy ([process lock](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md)) |
| 3 | Rung scope | Consume **filtered** `ImuSample` (C6) and emit a typed **attitude state**: orientation quaternion + body angular rate. **Do not** implement controller, mixer, ESC, or free navigation (position/velocity) |
| 4 | Algorithm (exactly one) | Ship **one** algorithm only: a **gravity-referenced complementary attitude filter** (gyro integration fused with accel-derived tilt). Document gain / time-constant parameter(s) with fixed defaults. **Forbidden in this Buy:** Madgwick, Mahony, EKF/UKF, MEKF, or shipping two estimators “to compare” |
| 5 | Hard cut (B1) | **No** magnetometer · **no** GPS/baro · **no** online gyro-bias estimation / learning · **no** world-frame velocity/position. Mag/GPS/bias = later ICs |
| 6 | Frames (honesty) | Document in module docstring: assumed **body frame** for IMU; attitude quaternion maps **body → a documented world/reference frame**. **Lock default: `enu`.** Implementer must set `AttitudeState.frame = "enu"` |
| 7 | Hardware honesty | Still **no** real MCU drivers. Estimator runs on samples from `ImuHal` + `ImuLowPassFilter` (sim). Real AHRS HW path = later IC |
| 8 | Language honesty | **Python scaffold / sim only — production flight_control runtime is C++ (future IC)**. Phrase in new module docstring(s). **No** C++/CMake tree |
| 9 | Safety | Do **not** weaken RejectAll. Estimation is sensing/state — **not** actuation; no Safety `allow` required to estimate. **Forbidden:** any actuator write; any shipped `AllowAll*` |
| 10 | Autonomy / radio | Do **not** change autonomy or radio packages. Do **not** auto-wire attitude → autonomy submit / HOLD |
| 11 | Registry | Default `CapabilityRegistry.load_default()` stays **empty** |
| 12 | No craft coupling | Do **not** change orchestrator Continuity, Board, or `library/` |
| 13 | Vehicle profile smoke | Thin pytest-visible helper (e.g. `run_hal_imu_attitude_smoke`) that: sim HAL → C6 filter → ≥1 attitude update. Prefer minimal schema change (reuse existing smoke profile id if possible) |
| 14 | Version | Bump **`0.5.4` → `0.5.5`**; tag **`v0.5.5`** on Engineer ACCEPT only |
| 15 | Forbidden claims | “Flight-verified attitude” · “Jarvis knows the real drone pose” · controller/ESC · marking estimation capability `available` |

**Product sentence:**

```text
Estimar actitud (cuaternión + rates de cuerpo) desde IMU filtrado con
un único complementary filter simulado — sin mag/GPS, sin bias learning,
sin control/ESC y sin fingir actitud verificada en vuelo.
```

---

## 1. Package layout (normative)

```text
src/jarvis/flight_software/flight_control/
  types.py          # may gain AttitudeState (+ Quat alias) OR keep types in attitude.py
  filter.py         # C6 — reuse; do not reimplement EMA inside estimator
  attitude.py       # NEW — ComplementaryAttitudeEstimator (name may vary; see §2)
  # NO: controller.py, mixer.py, esc.py, navigation.py, ekf.py, madgwick.py
```

Optional thin smoke in `vehicle_profiles/smoke.py`.  
**Do not** create `src/jarvis/flight_software/estimation/` unless Engineer ★ amends this IC.

---

## 2. Types / APIs (normative)

### 2.1 `AttitudeState`

| Field | Notes |
|---|---|
| `t_s` | float — timestamp aligned with last IMU sample used |
| `q_body_to_world` | 4-float quaternion `(w, x, y, z)` unit (document normalization) |
| `omega_body_rad_s` | 3-float body angular rate (typically from filtered gyro) |
| `frame` | Literal `"enu"` (locked §0 decision 6) |

`extra="forbid"` if Pydantic. **No** position, velocity, motor, or PWM fields.

### 2.2 `ComplementaryAttitudeEstimator` (name may vary)

```text
__init__(gain: float = <documented default in (0, 1]>, ...)
  # reject invalid gain with ValueError
  # optional: initial quaternion (default identity / level)

reset() -> None

update(sample: ImuSample) -> AttitudeState
  # sample SHOULD be filtered (C6); estimator may still accept raw for unit tests
  # but smoke path MUST pipe through ImuLowPassFilter
```

Determinism lock: same HAL seed + same filter α + same estimator gain + `reset()` → identical `AttitudeState` sequence (within ordinary float equality / documented tolerance ≤ 1e-9 relative if needed).

**Forbidden public APIs:** `set_pwm`, `mix`, `write_motor`, `estimate_position`, `update_gps`, `update_mag`, `run_ekf`, `run_madgwick`.

### 2.3 Pipeline helper (required for smoke clarity)

```text
read_attitude(hal, filt, estimator) -> AttitudeState
  # filtered = filt.filter_sample(hal.read_imu()); return estimator.update(filtered)
```

May live in `attitude.py`.

### 2.4 Relationship to C6

Reuse `ImuLowPassFilter` / `ImuSample`. Do **not** duplicate EMA inside the estimator “for convenience” as a second filter product — call C6.

---

## 3. Integration rules

| Existing | C7 rule |
|---|---|
| C3 HAL / ImuSample | Reuse |
| C6 filter | Required on smoke path; estimator consumes `ImuSample` |
| C4 autonomy | Untouched |
| C5 radio | Untouched |
| RejectAll | Untouched |
| Registry | Empty |
| Craft SoT | Untouched |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | Static / near-static accel≈gravity + ~zero gyro → attitude stays near level (identity or documented level quat) within a small angle bound |
| T2 | Determinism: same seed/α/gain/`reset` → identical sequence |
| T3 | Invalid gain (≤0 or >1, or whatever range the IC documents) → `ValueError` |
| T4 | `AttitudeState` has no actuator / position / velocity fields |
| T5 | No public symbols named like `run_madgwick` / `run_ekf` / `update_gps` / `mix` / `set_pwm` in the new module |
| T6 | No new `.cpp`/CMake under `flight_software/` |
| T7 | Default Safety still reject; autonomy submit still reject |
| T8 | Zero craft imports of new attitude symbols from `core/` / `adapters/` |
| T9 | Registry `load_default()` still empty |
| T10 | `pyproject` **`0.5.5`**; re-pin `0.5.4` pins |
| T11 | Full suite green |
| T12 | Report confirms complementary-only + no mag/GPS/bias learning + C++ honesty + “≠ flight-verified” |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| Shipping Madgwick/EKF “also” | One-algorithm lock |
| Mag / GPS / baro fusion | Hard cut B1 |
| Online bias learning presented as product | Later IC |
| Controller / mixer / ESC | Next ladder rungs |
| Claiming flight-verified attitude | Sim stub only |
| Weakening RejectAll | Safety chain |
| Craft Continuity / Board / library edits | Isolation |
| C++/CMake production FC tree | Future IC |
| Auto-submit autonomy from attitude | C4 stays explicit |

---

## 6. Docs

- PRIORIDAD: C7 in flight / CLOSED as appropriate  
- PLATFORM §13: C7 attitude estimation block  
- ARCHITECTURE: short note under flight_control — estimation stub after filter  
- README “What v0.5.5 includes”  
- Explicit: **what exists** (sim attitude from filtered IMU) vs **what remains impossible** (verified flight attitude, control, ESC, real AHRS)

---

## 7. Acceptance

**PASS when:** T1–T12 · complementary attitude works on sim filtered IMU · no second estimator · no mag/GPS/bias learning · no controller/ESC · RejectAll unchanged · version `0.5.5` · no craft coupling · C++ honesty present.

**FAIL if:** Madgwick/EKF shipped · navigation pose · ESC path · Safety allow · craft wiring · fake “flight-ready AHRS” claims.

---

## 8. Handoff

```text
Engineer → ★ this IC (C7)
Claude   → implement attitude.py + tests + report + 0.5.5
Cursor   → review
Engineer → ACCEPT + tag v0.5.5
Cursor   → next Buy when Engineer prioritizes
           (likely: controller rung — still one front; Safety/C++/ELRS remain parked)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C6 CLOSED @ v0.5.4. C7 B1-fase-c-attitude-estimation-rung READY —
complementary attitude from filtered IMU; no mag/GPS/bias; no control/ESC.
```

---

## 10. Engineer ★ checklist

1. Confirm **complementary-only** (not Madgwick/EKF) OK?  
2. World frame locked **`enu`** OK?  
3. Version **`0.5.5`** OK?  
4. Keep registry empty · RejectAll · craft isolation OK?  
5. Confirm **not** opening Safety-real / C++ / ELRS in this Buy?  
