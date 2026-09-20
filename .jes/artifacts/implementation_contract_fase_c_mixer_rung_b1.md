# Implementation Contract — Fase C mixer rung (`B1-fase-c-mixer-rung`)

**Project:** Jarvis  
**Date:** 2026-09-20  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (motor forces ≠ ESC/PWM · one layout · no craft wiring)

**Status:** ★ ACCEPT CLOSED @ **`v0.5.7`** (Engineer 2026-09-20)  
**Parents:**
- [C0 Design Contract ★](design_contract_fase_c_skill_capability_architecture.md) — §7 FC progression (`controller → mixer → ESC → …`) · one rung per IC  
- [C8 ★ ACCEPT](implementation_contract_fase_c_attitude_controller_rung_b1.md) — `BodyRateCommand` / PD controller @ **`v0.5.6`** (assumed landed with this Buy’s ACCEPT tip)  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no ESC, Safety-real, C++, ELRS, or craft wiring in this Buy  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — **fifth** `flight_control` rung only: **mixer / motor allocation** that turns collective thrust + body-rate (mix) channels into **per-motor force commands**.  
**Package:** bump to **`0.5.7`** in this Buy; git tag **`v0.5.7`** only after Engineer ACCEPT.  
**Not** ESC/PWM drivers · DShot/Oneshot · real ESC protocols · battery current limiting as product · Safety-real · C++/CMake tree · craft Continuity wiring · claiming motors spin.

**Outputs (required):**
1. Code under `src/jarvis/flight_software/flight_control/` (prefer new `mixer.py`)  
2. Tests + thin smoke  
3. `.jes/artifacts/implementation_report_fase_c_mixer_rung_b1.md`  
4. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE — **mixer stub ≠ ESC / ≠ flying**; C++ honesty phrase  
5. `pyproject.toml` → **`0.5.7`** (+ re-pin `0.5.6` version-checkpoint tests)

**Checkpoint:** package **`0.5.7`** · suite ≥ **3280** + new tests at ★

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-mixer-rung`** — next C0 §7 rung after controller: **mixer only** |
| 2 | One front | Do **not** fold ESC/PWM, Safety-real, C++/CMake, ELRS, or craft↔FS into this Buy |
| 3 | What this Buy demonstrates | Given a **collective thrust** (how hard to push “up”) and a **BodyRateCommand** (how to roll/pitch/yaw), compute **four motor force commands** for a fixed quad layout. **Human:** “reparte el empuje entre las 4 hélices.” |
| 4 | Layout (exactly one) | Ship **one** layout only: **quadrotor X** (motors 0..3 in a documented geometric order). **Forbidden:** shipping +/H/Y6/octo matrices “to compare” in this Buy |
| 5 | Algorithm | One **fixed linear allocation matrix** (or equivalent documented formulas) mapping `[collective, ωx, ωy, ωz]` → `[m0, m1, m2, m3]`. Document motor index order and X geometry in the module docstring |
| 6 | Scaffold honesty (important) | C8 outputs **body rates**, not true body torques. B1 mixer may treat `BodyRateCommand.omega_body_rad_s` as the **roll/pitch/yaw mix channels** (torque-like inputs) with an explicit docstring note: *production stacks often insert a rate→torque loop; this Buy teaches allocation geometry, not that rate≡torque physically.* Do **not** silently invent a second controller |
| 7 | Hard cut | Output is **`MotorForceCommand`** (4 scalars) — **no** PWM microseconds, **no** DShot, **no** ESC UART, **no** GPIO. Clamping to a documented range (e.g. ≥0) is OK; pretending hardware is armed is **not** |
| 8 | Units | Lock motor outputs as **normalized force commands in `[0, 1]`** after optional clamp (document). Collective input also normalized `[0, 1]`. Keep numbers dimensionless for B1 simplicity |
| 9 | Safety / autonomy | Do **not** weaken RejectAll. Do **not** auto-wire C4 HOLD → mixer. Mixing is still **not** actuation until ESC exists |
| 10 | Registry / craft | Registry stays empty; no Continuity/Board/`library/` edits |
| 11 | Smoke | Thin helper e.g. `run_mixer_smoke`: level collective + zero/near-zero rates → four equal-ish motors; or non-zero roll channel → documented imbalance sign |
| 12 | Version | Bump **`0.5.6` → `0.5.7`**; tag **`v0.5.7`** on ACCEPT only |
| 13 | Forbidden claims | “Motors spinning” · “armed” · “ESC online” · marking mixer/`available` flight capability |

**Product sentence:**

```text
Repartir empuje colectivo + canales roll/pitch/yaw (desde BodyRateCommand)
a 4 motores en layout quad-X — sin ESC/PWM y sin fingir que las hélices
ya giran.
```

---

## 1. Package layout (normative)

```text
src/jarvis/flight_software/flight_control/
  controller.py   # C8 — reuse BodyRateCommand
  mixer.py        # NEW — MotorForceCommand, QuadXMixer (name may vary)
  # NO: esc.py, pwm.py, dshot.py
```

---

## 2. Types / APIs (normative)

### 2.1 `MotorForceCommand`

| Field | Notes |
|---|---|
| `t_s` | float |
| `motor_forces` | tuple/list of **exactly 4** floats (normalized `[0,1]` after clamp, or documented pre-clamp with explicit clamp helper) |
| `layout` | Literal `"quad_x"` |
| `notes` | optional honesty string |

`extra="forbid"`. **No** PWM / ESC fields.

### 2.2 `QuadXMixer`

```text
__init__(...)  # optional scale gains for roll/pitch/yaw channels; document defaults
               # reject non-finite / invalid scales

mix(collective: float, rates: BodyRateCommand) -> MotorForceCommand
  # collective in [0,1] (reject or clamp — pick one, document, test)
  # uses rates.omega_body_rad_s as mix channels (see §0 decision 6)
```

Determinism: same inputs → identical outputs.

**Forbidden public APIs:** `set_pwm`, `write_dshot`, `arm`, `disarm`, `command_esc`, `open_serial`.

### 2.3 Optional helpers

```text
hover_collective(default=0.5) -> float   # smoke/tests only
```

---

## 3. Integration rules

| Existing | C9 rule |
|---|---|
| C8 BodyRateCommand | Required mix-channel input |
| C7/C6/C3 | Untouched |
| C4 autonomy | Untouched |
| RejectAll | Untouched |
| Craft | Untouched |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | Equal collective + zero rates → four motors equal (within float tol) |
| T2 | Non-zero roll (or pitch) channel → documented motors increase/decrease with correct signs for X layout |
| T3 | Invalid collective / scales rejected or clamped per documented rule |
| T4 | `MotorForceCommand` has no PWM/ESC fields; length 4; `layout=="quad_x"` |
| T5 | No ESC/PWM-shaped public symbols in `mixer.py` |
| T6 | No new `.cpp`/CMake under `flight_software/` |
| T7 | RejectAll + autonomy submit still reject |
| T8 | Zero craft imports of mixer symbols |
| T9 | Registry empty |
| T10 | `pyproject` **`0.5.7`**; re-pin `0.5.6` |
| T11 | Full suite green |
| T12 | Report: quad-X only · rate-as-mix-channel honesty · ≠ ESC / ≠ flying |

---

## 5. Honesty / forbidden

| Forbidden | Why |
|---|---|
| ESC / PWM / DShot | Next rung |
| Multiple airframe layouts | One-layout lock |
| Claiming motors armed/spinning | Scaffold |
| Hiding rate≠torque simplification | Honesty |
| Weakening RejectAll / craft wiring | Process lock |
| C++/CMake production FC | Future IC |

---

## 6. Docs

- PRIORIDAD / PLATFORM §13 / ARCHITECTURE / README “What v0.5.7 includes”  
- Explicit: **exists** = 4 motor force numbers from mix; **impossible** = ESC signaling, spinning props, flight

---

## 7. Acceptance

**PASS when:** T1–T12 · quad-X mixer works · no ESC/PWM · RejectAll unchanged · `0.5.7` · craft isolation · C++ honesty + rate-as-channel note present.

**FAIL if:** PWM/ESC path · multiple layouts as product · fake armed motors · craft wiring.

---

## 8. Handoff

```text
Engineer → ★ this IC (C9)
Claude   → implement mixer.py + tests + report + 0.5.7
Cursor   → review
Engineer → ACCEPT + tag v0.5.7
Cursor   → next Buy (likely ESC/PWM stub — still one front)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C8 CLOSED @ v0.5.6. C9 B1-fase-c-mixer-rung READY —
quad-X allocation; no ESC/PWM.
```

---

## 10. Engineer ★ checklist

1. Quad-X only OK?  
2. Treat `BodyRateCommand` as mix channels (with honesty note) OK?  
3. Normalized `[0,1]` motor forces OK?  
4. Version **`0.5.7`** · no ESC in this Buy OK?  
