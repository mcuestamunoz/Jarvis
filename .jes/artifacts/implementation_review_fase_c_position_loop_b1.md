# Implementation Review — Fase C position loop (`B1-fase-c-position-loop`)

**IC:** [`implementation_contract_fase_c_position_loop_b1.md`](implementation_contract_fase_c_position_loop_b1.md)  
**Report:** [`implementation_report_fase_c_position_loop_b1.md`](implementation_report_fase_c_position_loop_b1.md)  
**Reviewer:** Cursor (independent review of record — not Claude self-PASS)  
**Date:** 2026-09-26  

**Verdict:** **PASS WITH NOTES** (N1–N4 residual, accepted) — Engineer ★ **ACCEPT CLOSED** @ tag **`v0.5.40`** (2026-09-26).

---

## Debt classification (Engineer ask 2026-09-26)

| # | ¿Deuda del mes C36–C43? | ¿Deuda futura / Buy? | Anotación |
|---|---|---|---|
| **N1** nan setpoint | **No** | **No** como Buy. Higiene opcional (1–2 líneas `isfinite` en `compute`) si alguien toca el módulo | Residual higiene — **no cola** |
| **N2** z baja al chase xy | **No** (no es defecto) | **No** como Buy. Es acople físico de la planta de juguete | **Conocimiento operativo** → C40 IC debe asumirlo (HOLD/GO_TO no prometen z clavada mientras hay tilt) |
| **N3** nombre T5 | **No** | **No** | Cosmético — no anotar en cola |
| **N4** π/6 duplicado C++ | **No** | **No** | Cosmético — no anotar en cola |

**Conclusión:** nada de N1–N4 entra en la cola del mes ni abre un IC. Solo N2 se **propaga como precaución de diseño** a C40 (y siguientes lazos), no como ticket de deuda.

---

## 0. Scope check

Sim position HAL + one xy→tilt controller outside `FlightControlLoop.step`. One front: no AutonomyVerb `GO_TO` executor (C40), Safety deepen, live GPS/flow, plant folded into `step`, C38 altitude rewrite, mag/RC changes, craft↔FS, Assistant, silicon. Plants / loop / altitude / mag / RC untouched.

---

## 1. Evidence (independent)

| Gate | Result |
|---|---|
| `pyproject.toml` | **`0.5.40`** |
| New Python tests | **9 passed** (`tests/test_fase_c_position_loop_b1.py`) |
| Parent smokes (C11/C36/C37/C38 + C39) | **53 passed** |
| Full `pytest -q` (`all` perms) | **3723 passed, 9 skipped** (+9 vs C38 baseline) |
| Host `ctest` | **101/101** (+8 `[position][c39]`) |
| `loop` / `plant` / `altitude_controller` / mag / attitude / rc vs HEAD | **empty** |
| Closed-loop smoke (independent) | `d: 5.0 → ≈0.211` @ `(x_des,y_des)=(5,0)`; `xN≈5.21` (East chase proven) |
| `git tag` tip | still **`v0.5.39`** — no `v0.5.40` (`v0.5.4` is an older unrelated tag) |

---

## 2. IC §0 / §2 locks

| Lock | Verdict |
|---|---|
| `PositionSample` + `SimulatedPositionHal` (caller-supplied true xy) | **Pass** — direct ENU port; no NMEA/WGS84/flow theater; HAL does not own a plant |
| `PositionSetpoint(x_m, y_m)` typed | **Pass** — no near-homograph with `AttitudeSetpoint` |
| One PD-ish xy→roll/pitch outside `step`; yaw=0 | **Pass** — `AttitudeSetpoint` for `loop.step`; `max_tilt_rad` default = `RC_MAX_TILT_RAD` (Py) / `π/6` (C++) |
| Signs documented + proven | **Pass** — East → positive pitch (`q.y>0`); North → negative roll (`q.x<0`); Catch2+pytest T3 |
| Smoke chains C38 alt + C39 pos | **Pass** — `pos.compute` → `alt.compute` → `loop.step` → `plant.step` |
| Not `AutonomyVerb.GO_TO` | **Pass** — T7: RejectAll + `not_attempted` |
| Python + C++ twins | **Pass** |
| Version `0.5.40` + checkpoint re-pins | **Pass** |
| Forbidden claims | **Pass** — docs/report say LANDED awaiting review/ACCEPT |

---

## 3. IC §2 tests

| ID | Verdict |
|---|---|
| T1 | **Pass** — HAL known xy (+ optional `z_m` round-trip) |
| T2 | **Pass WITH NOTE** — gains / non-finite velocities / non-finite HAL inputs raise; non-finite **setpoint** coords not validated (N1) |
| T3 | **Pass** — East/North direction + tilt clip + yaw=0 |
| T4 | **Pass** — horizontal distance shrinks (`< 1.0` bound); z finite (N2) |
| T5 | **Pass WITH NOTE** — `loop` never calls plant; C11+C36 green (N3: name overclaims C37/C38) |
| T6 | **Pass** — Catch2 covers T1+T3+T4 (+ extras) |
| T7–T8 | **Pass** — craft/Safety/`GO_TO` isolation + version |
| T9 | **Pass** — report honesty locks |

---

## 4. Notes (residual, accepted)

| # | Note |
|---|---|
| **N1** | IC T2 asks non-finite **setpoints** to raise. `compute` validates `vx`/`vy` but not `PositionSetpoint.x_m`/`y_m`. A `nan` East setpoint does **not** raise and (via IEEE/`min`/`max` quirks) can collapse to a max-tilt command. Precedented class of gap (validation completeness). **Accept for this Buy** — recommend a one-line finite check in a later hygiene Buy or C40 if touched; not a freeze/scope break. |
| **N2** | Smoke z ends ≈`1.38` with `z_des=2.0` while chasing xy (coupled tilt/thrust). IC T4 only requires finite z / optional near-`z_des`. Distance shrink is the gate. **Accept.** |
| **N3** | `test_t5_…c11_c36_c37_c38…` name overclaims; body only runs C11+C36 (+ `loop` source check). Parent suites re-run green independently. Same class as C38 N4. **Accept.** |
| **N4** | C++ `max_tilt_rad` default duplicates `π/6` literal instead of including `rc_setpoint.hpp` — disclosed; numeric match. **Accept.** |

---

## 5. Honesty

```text
sim position ≠ live GPS/flow chip
xy→tilt in RAM ≠ position hold in air ≠ GO_TO executed
plant outside step ≠ MCU ISR ≠ motors
ENU point in RAM ≠ house map
```

Docs say LANDED awaiting Cursor review + Engineer ★ ACCEPT — no false CLOSED / `v0.5.40` tag claim observed.

---

## 6. Reviewer ask of Engineer

★ **ACCEPT** done (Engineer 2026-09-26) → tag **`v0.5.40`**. Next: Cursor drafts **C40** (autonomy executor) AUTHORIZED for Claude.

Debt table above: **no cola items** from N1–N4. C40 must respect N2 coupling (do not claim z locked during GO_TO tilt).

