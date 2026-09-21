# Implementation Contract — Fase C rate→torque bridge (`B1-fase-c-rate-torque-bridge`)

**Project:** Jarvis  
**Date:** 2026-09-21  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (typed bridge ≠ cascaded rate PID · mixer no longer eats rates as if torque · ≠ flying)

**Status:** ★ ACCEPT CLOSED @ tag **`v0.5.10`**  
**Parents:**
- [C0 Design Contract ★](design_contract_fase_c_skill_capability_architecture.md) — FC honesty / one front  
- [C9 ★ ACCEPT](implementation_contract_fase_c_mixer_rung_b1.md) — documented rate-as-mix-channel honesty gap @ **`v0.5.7`**  
- [C11 ★ ACCEPT](implementation_contract_fase_c_controlled_flight_sim_tip_b1.md) — wooden ladder tip CLOSED @ **`v0.5.9`**; rate≠torque left open on purpose  
- Engineer priority 2026-09-21: **close rate→torque honesty, then C++ scaffold** (this Buy is **only** the honesty bridge)  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no C++/CMake, Safety-real, ELRS, GPIO, or craft wiring in this Buy  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — **honesty bridge only**: introduce a typed **`BodyTorqueCommand`** (mix/torque-like body axes) and a **single feedforward** `rate → torque` map so `QuadXMixer` no longer consumes `BodyRateCommand` as if rate ≡ torque.  
**Package:** bump to **`0.5.10`** in this Buy; git tag **`v0.5.10`** only after Engineer ACCEPT.  
**Not** cascaded rate PID / second attitude controller · motor/prop physics · C++ scaffold · Safety-real · GPIO/ESC hardware · craft Continuity wiring · claiming physical torque (N·m) of a real airframe.

**Outputs (required):**
1. Code under `src/jarvis/flight_software/flight_control/` (prefer new `rate_torque.py`; **surgical** mixer API migration — see §2)  
2. Tests + thin smoke path update (closed-loop / mixer smokes must use the bridge)  
3. `.jes/artifacts/implementation_report_fase_c_rate_torque_bridge_b1.md`  
4. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **bridge ≠ rate loop product · ≠ physical N·m · ≠ flying**; C++ honesty phrase; note **next prioritized front = C++ scaffold**  
5. `pyproject.toml` → **`0.5.10`** (+ re-pin `0.5.9` version-checkpoint tests)

**Checkpoint:** package **`0.5.10`** · suite ≥ **3330** + new tests at ★

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-rate-torque-bridge`** — close the C9 honesty gap with a typed bridge |
| 2 | One front | Do **not** fold C++/CMake, Safety-real, ELRS, craft↔FS, GPIO/DShot, or a cascaded rate PID into this Buy |
| 3 | What this Buy demonstrates | Pipeline becomes: `BodyRateCommand` → **bridge** → `BodyTorqueCommand` → `QuadXMixer.mix(...)`. Mixer mix channels are **torque-typed**, not rates. **Human:** “ya no fingimos que una velocidad de giro *es* un par; hay un paso con nombre propio en medio.” |
| 4 | Bridge law (exactly one) | Ship **one** feedforward map only, e.g. `tau = gain * omega_cmd` per axis (gains finite, `> 0`, documented defaults; allow per-axis or scalar gain — pick one, document). **Forbidden:** cascaded rate PID (`kp*(ω_cmd−ω_meas)`), LQR, INDI, second attitude controller, or “physics inertia model” presented as truth |
| 5 | Types | New `BodyTorqueCommand` (`t_s`, `tau_body` or equivalent `Vec3`, optional `notes`, `extra="forbid"`). Units honesty: document as **normalized / dimensionless torque-like mix command** for B1 — **not** claimed Newton-metres of a real vehicle unless you introduce and validate a real unit path (do **not** claim N·m in this Buy) |
| 6 | Mixer migration | `QuadXMixer.mix` must take **`BodyTorqueCommand`** (not `BodyRateCommand`) as the attitude channel input. Update all in-tree call sites (smokes, C11 closed loop, tests). Do **not** leave a silent dual API that still lets callers pass rates as torque without going through the bridge |
| 7 | C8 / C11 | `PdAttitudeController` still emits `BodyRateCommand` only. Plant still consumes `MotorForceCommand`. Closed-loop smoke must insert the bridge between controller and mixer; C11 convergence criterion must still hold (or be re-tuned with documented gains — if retune needed, disclose in report; do not break tip without disclosure) |
| 8 | Safety / autonomy | Do **not** weaken RejectAll. Do **not** auto-wire C4 HOLD |
| 9 | Language honesty | **Python scaffold / sim only — production flight_control runtime is C++ (future IC)**. Phrase in new module docstring(s). No C++/CMake tree |
| 10 | Registry / craft | Registry stays empty; no Continuity/Board/`library/` edits |
| 11 | Smoke | Thin helper and/or update existing mixer / controlled-flight smokes so the documented happy path always goes through the bridge |
| 12 | Version | Bump **`0.5.9` → `0.5.10`**; tag **`v0.5.10`** on ACCEPT only |
| 13 | Forbidden claims | “True motor torque (N·m)” · “rate loop closed on hardware” · “physics-accurate inertia” · “we fly” · marking actuation `available` |
| 14 | After this Buy | Engineer-prioritized **next** front remains **C++ scaffold** (separate IC) — mention in PRIORIDAD / handoff only; do **not** start C++ here |

**Product sentence:**

```text
Poner un puente tipado entre la orden de tasa (C8) y el mezclador (C9)
para dejar de tratar rad/s como si fueran par — mapa lineal juguete,
sin PID de tasa en cascada y sin fingir N·m reales.
```

**Defaults locked by Cursor (Engineer said redacta):**
- Feedforward `tau = gain * omega_cmd` only (not cascaded rate PID)  
- Mixer API migrates to `BodyTorqueCommand`  
- Units = normalized torque-like (not claimed N·m)  
- Next front after ACCEPT = C++ scaffold (separate IC)

---

## 1. Package layout (normative)

```text
src/jarvis/flight_software/flight_control/
  controller.py   # C8 — BodyRateCommand unchanged as C8 output
  rate_torque.py  # NEW — BodyTorqueCommand, LinearRateTorqueBridge (name may vary)
  mixer.py        # MIGRATE mix(...) to consume BodyTorqueCommand
  plant.py        # unchanged input type (MotorForceCommand)
  # NO: rate_pid.py cascaded product loop, inertia_truth.py, cpp tree
```

---

## 2. Types / APIs (normative)

### 2.1 `BodyTorqueCommand`

| Field | Notes |
|---|---|
| `t_s` | float |
| `tau_body` (name locked preferred) | `Vec3` — body-frame **torque-like mix command**, normalized/dimensionless in B1 |
| `notes` | optional honesty string |

`extra="forbid"`. Finite components required.

### 2.2 Bridge

```text
LinearRateTorqueBridge(gain=... | gains=(gx,gy,gz))
  convert(rates: BodyRateCommand) -> BodyTorqueCommand
  # tau_i = gain_i * omega_cmd_i ; reject non-finite / non-positive gains
```

One public conversion path only.

### 2.3 Mixer

```text
QuadXMixer.mix(collective: float, torques: BodyTorqueCommand) -> MotorForceCommand
  # uses torques.tau_body as roll/pitch/yaw mix channels (same X geometry as today)
```

Update docstring: remove “treats BodyRateCommand as mix channels”; state that rates must pass the bridge first.

**Forbidden:** keeping `mix(..., rates: BodyRateCommand)` as a supported public path after this Buy (migrate or delete — no silent dual).

### 2.4 Forbidden public APIs

`rate_pid_step`, `compute_inertia_torque_nm` presented as product truth, `write_gpio`, cascaded “inner rate loop” classes.

---

## 3. Integration rules

| Existing | C12 rule |
|---|---|
| C8 `BodyRateCommand` | Still the attitude-controller output |
| C9 geometry / scales | Keep Quad-X formulas; input vector is now torque-typed |
| C10 ESC | Untouched (still force→µs) |
| C11 plant / closed loop | Must call bridge; tip must remain green (disclose any gain retune) |
| C4 / RejectAll / craft | Untouched |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | Zero rate command → zero (or ~0) torque command |
| T2 | Positive roll rate cmd → positive roll torque cmd (documented sign); similarly pitch/yaw |
| T3 | Invalid / non-positive gains rejected |
| T4 | Mixer rejects / type-checks: public `mix` takes `BodyTorqueCommand` (no rates param) |
| T5 | Equal collective + zero torque → four equal motors (existing C9 behavior preserved via torques) |
| T6 | Smoke / closed-loop path uses bridge; C11-style tilt recovery still passes (or retune disclosed + still converges) |
| T7 | No cascaded rate-PID public symbols; no GPIO/C++ tree |
| T8 | RejectAll + autonomy submit still reject |
| T9 | Zero craft imports of new bridge symbols |
| T10 | Registry empty |
| T11 | `pyproject` **`0.5.10`**; re-pin `0.5.9` |
| T12 | Full suite green |
| T13 | Report: feedforward only · normalized τ · mixer migrated · ≠ N·m truth · ≠ flying · next = C++ scaffold |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| Cascaded rate PID sold as this bridge | Scope / “exactly one” law |
| Claiming real N·m | B1 normalized only |
| Silent dual mixer API (rates still accepted) | Would re-open the honesty hole |
| C++/Safety/GPIO/craft in this Buy | One front |
| Breaking C11 tip without disclosure | Process |

---

## 6. Docs

- PRIORIDAD / PLATFORM §13 / ARCHITECTURE / README “What v0.5.10 includes”  
- Explicit: **exists** = typed feedforward rate→torque-like bridge + mixer migration; **impossible** = physical torque truth, cascaded rate loop product, flying  
- PRIORIDAD after land: **next READY front = C++ scaffold** (IC not in this Buy)

---

## 7. Acceptance

**PASS when:** T1–T13 · bridge works · mixer consumes torques only · closed-loop tip still honest/green · RejectAll unchanged · `0.5.10` · craft isolation · C++ honesty · no fake N·m / no cascaded PID.

**FAIL if:** rates still fed to mixer as primary API · cascaded rate PID · C++ tree · craft wiring · tip silently broken.

---

## 8. Handoff

```text
Engineer → ★ this IC (C12)
Claude   → implement rate_torque.py + mixer migration + tests + report + 0.5.10
Cursor   → review
Engineer → ACCEPT + tag v0.5.10
Cursor   → draft C13 C++ scaffold IC when prioritized
           (Engineer plan: rate→torque THEN C++ scaffold)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C11 CLOSED @ v0.5.9. C12 B1-fase-c-rate-torque-bridge READY —
typed feedforward rate→torque-like; mixer migrates; then C++ scaffold.
```

---

## 10. Engineer ★ checklist

1. Feedforward only (not cascaded rate PID) OK?  
2. Mixer API migrates to `BodyTorqueCommand` OK?  
3. Normalized τ (not claimed N·m) OK?  
4. C11 tip must stay green / disclose retune OK?  
5. Version **`0.5.10`** OK?  
6. After ACCEPT, next IC = **C++ scaffold** OK?  
