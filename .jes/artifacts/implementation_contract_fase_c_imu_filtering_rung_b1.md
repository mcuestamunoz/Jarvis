# Implementation Contract — Fase C IMU filtering rung (`B1-fase-c-imu-filtering-rung`)

**Project:** Jarvis  
**Date:** 2026-09-20  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (filter ≠ attitude · no ESC · sensing chain only)

**Status:** ★ ACCEPT CLOSED @ **`v0.5.4`** (Engineer 2026-09-20)  
**Parents:**
- [C0 Design Contract ★](design_contract_fase_c_skill_capability_architecture.md) — §7 FC progression (`sampling → filtering → state estimation → …`) · one rung per IC  
- [C3 ★ ACCEPT](implementation_contract_fase_c_first_fc_rung_b1.md) — HAL + `ImuSample` + `SimulatedImuHal` @ **`v0.5.1`** · Engineer C++ amendment  
- [C4+C5 ★ ACCEPT](implementation_contract_fase_c_autonomy_surface_b1.md) / [radio](implementation_contract_fase_c_radio_dual_role_b1.md) — autonomy + radio dual-role @ **`v0.5.3`** (unchanged by this Buy)  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — **second** `flight_control` rung only: **IMU sample filtering** on top of C3 HAL reads.  
**Package:** bump to **`0.5.4`** in this Buy; git tag **`v0.5.4`** only after Engineer ACCEPT.  
**Not** state estimation · attitude/rate/position controller · mixer · ESC/PWM · live autonomy execution · real ELRS decode · real MCU drivers · Intent→FC wiring · craft `flight_controller` bind · `AllowAllSafetyGate` · production C++ FC tree.

**Outputs (required):**
1. Code under `src/jarvis/flight_software/flight_control/` (extend C3 tree — **no** new top-level package)  
2. Tests (module + optional profile smoke extension §4)  
3. `.jes/artifacts/implementation_report_fase_c_imu_filtering_rung_b1.md`  
4. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE §1c — **filter rung ≠ attitude / ≠ controlled flight**; keep C++ honesty phrase  
5. `pyproject.toml` → **`0.5.4`** (+ re-pin version-checkpoint tests that assert `0.5.3`)

**Checkpoint:** package **`0.5.4`** · suite ≥ **3236** + new tests at ★

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-imu-filtering-rung`** — next C0 §7 rung after sampling: **filtering only** |
| 2 | Why this Buy (not Safety / C++) | After C5, PRIORIDAD options were “further FC rungs · real Safety · native stacks”. **C6 locks the FC ladder next step** (filtering). A real (non-RejectAll) Safety policy and a production C++/CMake FC tree remain **separate future ICs** — do not fold them into this Buy |
| 3 | Rung scope | Consume C3 `ImuSample` streams and emit **filtered** IMU samples. **Do not** implement state estimation, quaternion/attitude, controller, mixer, or ESC |
| 4 | Algorithm (minimal, deterministic) | Ship **one** explicit filter: a **first-order low-pass / exponential moving average (EMA)** applied independently to each accel and gyro axis. Document α (or equivalent time-constant) as a constructor parameter with a fixed default. **Forbidden:** claiming Madgwick/Mahony/EKF/complementary-as-attitude in this Buy — those are estimation-class and belong to a later rung |
| 5 | Hardware honesty | Still **no** real MCU / I²C / SPI drivers. Filter runs on samples from existing `ImuHal` (typically `SimulatedImuHal`). Real sensor fusion HW path = later IC |
| 6 | Language honesty | Same Engineer rule as C3/C4: **Python scaffold / sim only — production flight_control runtime is C++ (future IC)**. Phrase (or clear equivalent) in new module docstring(s). **No** C++/CMake tree in this Buy |
| 7 | Safety | Do **not** weaken C2/C4. `default_safety_gate()` remains `RejectAllSafetyGate`. Filtering is sensing post-process — **not** actuation; no Safety `allow` required to filter. **Forbidden:** any write to actuators; any shipped `AllowAll*` |
| 8 | Autonomy / radio | Do **not** change `flight_software/autonomy/` or `capabilities/radio.py`. Do **not** auto-wire filtered IMU → autonomy submit |
| 9 | Registry | Default `CapabilityRegistry.load_default()` stays **empty**. Tests may use in-memory fixtures only |
| 10 | No craft coupling | Do **not** change orchestrator Continuity, Board, or `library/`. Craft catalog `flight_controller` ≠ this package |
| 11 | Vehicle profile | Either extend the existing smoke helper to read ≥1 **filtered** sample, **or** add a thin second smoke entry (e.g. `smoke_quad_hal_imu_filter`) that still uses sim HAL + filter. Prefer **minimal** change — one pytest-visible smoke path is enough |
| 12 | Version | Bump **`0.5.3` → `0.5.4`**; tag **`v0.5.4`** on Engineer ACCEPT only |
| 13 | Forbidden | Estimation as “filter” · attitude angles as product output · mixer/ESC · claiming controlled flight · wiring CLI Intent→FC · marking filter capability `available` |

**Product sentence:**

```text
Añadir el peldaño de filtrado IMU (EMA/low-pass determinista) sobre el
HAL simulado de C3 — sin estimación de actitud, sin control, sin ESC
y sin fingir que el dron ya vuela.
```

---

## 1. Package layout (normative)

```text
src/jarvis/flight_software/flight_control/
  types.py          # C3 — ImuSample unchanged (may add FilteredImuSample alias OR reuse ImuSample)
  hal.py            # C3 — unchanged
  sim_imu_hal.py    # C3 — unchanged behavior
  filter.py         # NEW — ImuFilter / apply EMA (name may vary; see §2)
  # NO: estimator.py, controller.py, mixer.py, esc.py, attitude.py
```

Optional: thin helper in `vehicle_profiles/smoke.py` (or sibling) to run sim HAL → filter → ≥1 sample.  
**Do not** create `src/jarvis/flight_software/estimation/` in this Buy.

---

## 2. Types / APIs (normative)

### 2.1 Reuse `ImuSample`

Filtered output **must** remain an `ImuSample` (same fields: `t_s`, `accel_mps2`, `gyro_rad_s`) **or** a thin `FilteredImuSample` that is field-identical / structurally interchangeable. Prefer **reuse `ImuSample`** to avoid parallel types.

### 2.2 `ImuLowPassFilter` (name may vary)

```text
__init__(alpha: float = <documented default in (0, 1]>)
  # reject alpha outside (0, 1] with ValueError

reset() -> None
  # clears internal state (next sample seeds the filter)

filter_sample(raw: ImuSample) -> ImuSample
  # EMA per axis on accel and gyro; t_s copied from raw (or documented rule)
```

Determinism lock: same seed/`SimulatedImuHal` sequence + same `alpha` + `reset()` → identical filtered sequence.

**Forbidden public APIs in this Buy:** `estimate_attitude`, `get_quaternion`, `get_euler`, `update_ekf`, `write_motor`, `mix`, `set_pwm`.

### 2.3 Optional pipeline helper (pure)

```text
read_filtered(hal: ImuHal, filt: ImuLowPassFilter) -> ImuSample
  # raw = hal.read_imu(); return filt.filter_sample(raw)
```

May live in `filter.py` or smoke helper — not required as a class.

### 2.4 C3 unchanged

`SimulatedImuHal.read_imu()` behavior stays as C3. Filter wraps reads; it does not replace the HAL.

---

## 3. Integration rules

| Existing | C6 rule |
|---|---|
| C3 HAL / ImuSample | Reuse; do not fork parallel IMU types without cause |
| C4 autonomy | Untouched |
| C5 radio | Untouched |
| RejectAll | Untouched |
| Registry | Stays empty |
| Craft SoT | Untouched |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | `filter_sample` on a constant raw stream converges toward that constant (or equals it when α=1) |
| T2 | Same HAL seed + same α + `reset()` → identical filtered sequence (determinism) |
| T3 | α ≤ 0 or α > 1 → `ValueError` (or equivalent documented rejection) |
| T4 | Filtered output has no actuator fields; type is `ImuSample` (or field-identical) |
| T5 | No public symbols named like `estimate_attitude` / `get_quaternion` / `mix` / `set_pwm` under new filter module |
| T6 | Grep: no new `.cpp`/CMake under `flight_software/` from this Buy |
| T7 | Default Safety still reject; autonomy submit still reject (smoke that C4/C5 untouched) |
| T8 | Zero craft imports of new filter symbols from `core/` / `adapters/` |
| T9 | Registry `load_default()` still empty |
| T10 | `pyproject` **`0.5.4`**; re-pin `0.5.3` pins |
| T11 | Full suite green |
| T12 | Report confirms filter rung + no estimation/control/ESC + C++ honesty retained |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| Shipping “attitude estimator” labeled as filter | Next ladder rung is estimation — separate IC |
| Mixer / ESC / PWM | Actuation not authorized |
| Claiming controlled flight / armed | Scaffold honesty |
| Weakening RejectAll / AllowAll | Safety chain |
| Craft Continuity / Board / library edits | Wrong SoT |
| C++/CMake production FC tree | Future IC (Engineer amendment stands) |
| Auto-submit autonomy from filtered IMU | C4 stays explicit + Safety-gated |

---

## 6. Docs

- PRIORIDAD: C6 in flight / CLOSED as appropriate  
- PLATFORM §13: C6 filtering rung block  
- ARCHITECTURE §1c (or short §1f): filter after IMU; still ≠ estimation/control  
- README “What v0.5.4 includes”  

---

## 7. Acceptance

**PASS when:** T1–T12 · EMA/low-pass works on sim IMU · no estimation/controller/mixer/ESC · RejectAll unchanged · version `0.5.4` · no craft coupling · C++ honesty phrase present.

**FAIL if:** attitude/EKF shipped as “filter” · ESC path · Safety allow · craft wiring · fake flight claims.

---

## 8. Handoff

```text
Engineer → ★ this IC (C6)
Claude   → implement filter.py + tests + report + 0.5.4
Cursor   → review
Engineer → ACCEPT + tag v0.5.4
Cursor   → next Buy when Engineer prioritizes
           (likely: state estimation rung · OR real Safety policy · OR native C++ FC — each its own IC)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C4+C5 CLOSED @ v0.5.3. C6 B1-fase-c-imu-filtering-rung READY —
EMA/low-pass on C3 ImuSample; no estimation/control/ESC.
```

---

## 10. Engineer ★ checklist

1. Confirm **filtering** (not real Safety / not C++ tree) as C6 OK?  
2. Version **`0.5.4`** OK?  
3. EMA/low-pass only (no Madgwick/EKF) OK?  
4. Keep default registry empty OK?  
