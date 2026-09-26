# Implementation Review — Fase C altitude loop (`B1-fase-c-altitude-loop`)

**IC:** [`implementation_contract_fase_c_altitude_loop_b1.md`](implementation_contract_fase_c_altitude_loop_b1.md)  
**Report:** [`implementation_report_fase_c_altitude_loop_b1.md`](implementation_report_fase_c_altitude_loop_b1.md)  
**Reviewer:** Cursor (independent review of record — not Claude self-PASS)  
**Date:** 2026-09-26  

**Verdict:** **PASS WITH NOTES** (N1–N4 residual, accepted) — Engineer ★ **ACCEPT CLOSED** @ tag **`v0.5.39`** (2026-09-26).

---

## 0. Scope check

Sim altitude HAL + one z→collective controller outside `FlightControlLoop.step`. One front: no xy position (C39), executor HOLD/LAND (C40), live baro/ToF, plant folded into `step`, mag/RC changes, craft↔FS, Assistant, silicon. Plants / loop / C37 mag / RC yaw untouched.

---

## 1. Evidence (independent)

| Gate | Result |
|---|---|
| `pyproject.toml` | **`0.5.39`** |
| New Python tests | **8 passed** (`tests/test_fase_c_altitude_loop_b1.py`) |
| Parent smokes (C11/C36/C37 + cpp unit) | **56 passed** |
| Full `pytest -q` (`all` perms) | **3714 passed, 9 skipped** (+8 vs C37 baseline) |
| Host `ctest` | **93/93** (+5 `[altitude][c38]`) |
| `loop.py` / `plant.py` / mag / attitude / rc_setpoint vs HEAD | **empty** (no freeze break) |
| Closed-loop smoke (independent) | `z0=0` → `zN≈1.933`, `|err|` `2.0` → `≈0.067` @ `z_des=2`, 500 steps |
| `git tag` tip | still **`v0.5.38`** — no `v0.5.39` |

---

## 2. IC §0 / §2 locks

| Lock | Verdict |
|---|---|
| `AltitudeSample` + `SimulatedAltitudeHal` (caller-supplied true z → `altitude_m`) | **Pass** — direct altitude port; no ISA pressure table; HAL does not own a plant |
| One PD-ish law outside `step` | **Pass** — `clip(hover_bias + kp*(z_des−z) − kd*vz, 0, 1)`; smoke does `alt.compute` → `loop.step` → `plant.step` |
| Setpoint | **Pass** — plain `float z_des_m` (IC allowed; typed wrapper declined — see N2) |
| `vz` source | **Pass** — caller-supplied; smoke uses `true_velocity_mps[2]` |
| Python + C++ twins | **Pass** — matching defaults / law / validation |
| Plants / mag / RC / Safety / craft | **Pass** — frozen modules empty vs HEAD; T7 isolation green |
| Version `0.5.39` + checkpoint re-pins | **Pass** — 44 test files on `0.5.39` |
| Forbidden claims | **Pass** — docs/report say LANDED awaiting review/ACCEPT; honesty line present |

---

## 3. IC §2 tests

| ID | Verdict |
|---|---|
| T1 | **Pass** — HAL known true z; Catch2 twin |
| T2 | **Pass** — invalid gains / non-finite inputs raise; no `dt` in this design (N3) |
| T3 | **Pass** — below → collective > hover_bias; above → lower; clip to `[0,1]` |
| T4 | **Pass** — plant climbs; `|z−z_des|` shrinks (`< 0.2` bound); Catch2 twin |
| T5 | **Pass WITH NOTE** — `loop` never calls plant; C11+C36 smokes green (N4: name claims C37 but body does not invoke mag-yaw smoke; C37 suite re-run green separately) |
| T6 | **Pass** — Catch2 covers T1+T3+T4 (+ validation extras) |
| T7–T8 | **Pass** — craft/Safety isolation + version |
| T9 | **Pass** — report honesty locks |

---

## 4. Notes (residual, accepted)

| # | Note |
|---|---|
| **N1** | **`hover_bias` default ≠ IC's suggested `hover_collective()≈0.5`.** IC said “may reuse” — optional. Empirically `0.5` mismatches `ToyQuad6DofPlant` defaults (`thrust_gain=20` → ~4× hover thrust) and never settles. Default locked to `g/(4·thrust_gain)≈0.1226` for plant defaults; documented in both languages + report. Callers with non-default mass/thrust must pass their own bias (controller stays plant-agnostic). **Accept** — correct engineering within IC latitude. |
| **N2** | Plain `z_des_m` float instead of `AltitudeSetpoint` — avoids one-letter collision with existing `AttitudeSetpoint`. IC allowed plain float. **Accept.** |
| **N3** | No `dt` on `compute` (stateless). T2 validates every arg this design has. **Accept.** |
| **N4** | `test_t5_…c11_c36_c37…` name overclaims C37; body only runs C11+C36 (+ `loop` source check). Mag-yaw suite still green independently. **Accept** — naming nit, not a freeze break. |
| *(incidental)* | `test_fase_c_cpp_unit_tests_b1.py` C37 `attitude.cpp` check rewritten from `git diff` shape → source content (necessary after `v0.5.38` landed). Precedented fragility fix; not caused by C38 product code. **Accept.** |

---

## 5. Honesty

```text
sim altitude ≠ live baro/ToF chip
z→collective in RAM ≠ altitude hold in air
plant outside step ≠ MCU ISR ≠ motors
```

Docs say LANDED awaiting Cursor review + Engineer ★ ACCEPT — no false CLOSED / `v0.5.39` tag claim observed. Independent `git tag -l` confirms tip is still `v0.5.38`.

---

## 6. Reviewer ask of Engineer

★ **ACCEPT** done (Engineer 2026-09-26) → tag **`v0.5.39`**. Next: Cursor drafts **C39** (position loop, sim) when Engineer asks.

N1 hover_bias retune accepted with the ACCEPT.
