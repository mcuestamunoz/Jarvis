# Implementation Contract — Fase C RC → setpoint (`B1-fase-c-rc-setpoint`)

**Project:** Jarvis  
**Date:** 2026-09-22  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (sticks → `step` args ≠ flying · ≠ Safety execute · C20 kill policy unchanged · C24 tick unchanged math · no failsafe timeout)

**Status:** ★ ACCEPT CLOSED @ **`v0.5.23`**  
**Parents:**
- [C24 ★ ACCEPT](implementation_contract_fase_c_control_loop_tick_b1.md) — `FlightControlLoop.step` @ **`v0.5.22`**  
- [C20 ★ ACCEPT](implementation_contract_fase_c_crsf_dual_role_bridge_b1.md) — aux → Authority `kill` only @ **`v0.5.18`**  
- [C19 ★ ACCEPT](implementation_contract_fase_c_crsf_link_stub_b1.md) — `CrsfRcChannels` 16×11-bit @ **`v0.5.17`**  
- [C8 ★ ACCEPT](implementation_contract_fase_c_attitude_controller_rung_b1.md) — `AttitudeSetpoint` quat ENU @ **`v0.5.6`**  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no Esc HAL, CRSF timeout failsafe, MCU UART, silicon map, GPIO, Safety execute, craft↔FS, or flash  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — map already-decoded **RC channel units** (CRSF 11-bit ints) onto C24’s `step` arguments: `AttitudeSetpoint` + `collective`. Still no pin, no plant inside the mapper, no execute.  
**Package:** bump Jarvis `pyproject.toml` to **`0.5.23`**; git tag **`v0.5.23`** only after Engineer ACCEPT.  
**Not** flying · not RC sticks driving motors · not Safety allow/execute · not C20 extra kinds · not CRSF failsafe (C27) · not Esc HAL (C26) · not changing `loop.py` math · not `radio.py` decode APIs (C5 T5) · not live ELRS.

**Outputs (required):**
1. New mapper under `src/jarvis/flight_software/flight_control/` — preferred name **`rc_setpoint.py`**. **Forbidden:** putting stick math on `radio.py` or rewriting C24 `loop.py`  
2. C++ twin `native/flight_control/include/jarvis/fc/rc_setpoint.hpp` + `src/rc_setpoint.cpp`, added to `jarvis_fc`  
3. Tests: `tests/test_fase_c_rc_setpoint_b1.py` + ≥1 Catch2 case  
4. `.jes/artifacts/implementation_report_fase_c_rc_setpoint_b1.md`  
5. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **RC→setpoint ≠ flying ≠ sticks drive motors ≠ Safety allow**  
6. `pyproject.toml` → **`0.5.23`** (+ re-pin `0.5.22` checkpoints)

**Checkpoint:** package **`0.5.23`** · Python suite ≥ **3520** + new tests · host `ctest` still green · C24 recovery smokes still green · C20 policy unchanged

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-rc-setpoint`** — first map from CRSF-shaped stick units to C24 tick inputs |
| 2 | One front | Do **not** fold Esc HAL, CRSF timeout failsafe, MCU UART, silicon, GPIO, Safety execute, C20 extra aux/kinds, or auto `submit_command` |
| 3 | What this Buy demonstrates | Palos ya decodificados se pueden **convertir** en la consigna y el `collective` que `step` ya acepta. **Human:** “el mando ya tiene un idioma hacia el latido; aún no mueve un motor.” |
| 4 | Input | `CrsfRcChannels.channels` (16 ints in `[0, 2047]`) **or** an equivalent sequence of ≥4 ints. Reuse C19 type; do **not** re-parse CRSF frames here |
| 5 | Channel map (illustrative, documented — not a real TX model) | **AETR:** `ch[0]` roll, `ch[1]` pitch, `ch[2]` throttle, `ch[3]` yaw **unused this Buy**. Mid **992**, min **172**, max **1811** (CRSF 11-bit convention already used around C20). Indices + endpoints must be named constants |
| 6 | Throttle → collective | Linear map `[172, 1811] → [0, 1]`, clip. Mid 992 → **not** required to be 0.5 (document the actual mid value) |
| 7 | Roll/pitch → `AttitudeSetpoint` | Stick deflection from 992 → Euler roll/pitch, **max ±30°** (`π/6`) at 1811/172. Convert to `q_body_to_world_desired` ENU. **Yaw of that quat = 0** (identity heading). C7 has no mag — yaw stick is **out** this Buy |
| 8 | `t_s` | Mapper takes `t_s` as argument (caller’s sample time); does not invent a clock |
| 9 | Optional helper | Thin `step_with_rc(loop, sample, channels) -> ControlTickResult` **may** call C24 `step` after mapping. Must not call plant, ESC sink, or Safety |
| 10 | C24 / C20 | `loop.py` / `loop.cpp` math **unchanged**. C20 `kill` policy **unchanged**. Do not mix kill into this mapper |
| 11 | `radio.py` | No `decode_*` / `open_serial` / stick APIs (C5 T5) |
| 12 | Languages | **Both** Python + C++ (board-prep axis, same as C24) |
| 13 | Safety / adapter | RejectAll default; `RadioIntentAdapter` still NotImplemented |
| 14 | Version | **`0.5.22` → `0.5.23`**; tag **`v0.5.23`** on ACCEPT only |
| 15 | Forbidden claims | “Sticks fly the craft” · “angle mode product” · “ELRS connected” · Safety allow via sticks · yaw heading lock |

**Product sentence:**

```text
Mapear canales CRSF (AETR ilustrativo) a consigna de actitud + collective
para el tick C24 — palos → args de step, no motores, no Safety execute,
yaw stick fuera (sin mag).
```

**Defaults locked by Cursor (Engineer: next in board-prep cola after C24 ACCEPT):**
- New **`rc_setpoint.py`** + C++ twin  
- AETR; yaw unused; ±30°; CRSF 172/992/1811  
- Optional `step_with_rc`; C24 math frozen  

---

## 1. Package layout (normative intent)

```text
src/jarvis/flight_software/flight_control/
  rc_setpoint.py          # NEW
  loop.py                 # UNCHANGED math

native/flight_control/
  include/jarvis/fc/rc_setpoint.hpp
  src/rc_setpoint.cpp     # add to jarvis_fc
  tests/test_rc_setpoint.cpp

tests/
  test_fase_c_rc_setpoint_b1.py
```

Do **not** put this on `radio.py`. Do **not** import serial/baud.

---

## 2. Types / APIs (normative intent)

```text
RC_CH_ROLL, RC_CH_PITCH, RC_CH_THROTTLE   # 0,1,2
CRSF_CH_MIN, CRSF_CH_MID, CRSF_CH_MAX     # 172, 992, 1811
RC_MAX_TILT_RAD                           # π/6

RcLoopInputs
  setpoint: AttitudeSetpoint
  collective: float   # in [0, 1]

map_rc_to_loop_inputs(channels, *, t_s: float) -> RcLoopInputs
  # channels: CrsfRcChannels | sequence of ints (need ≥3 used indices)
  # invalid length / non-int → typed error
```

C++: same constants and `map_rc_to_loop_inputs`.

### 2.1 Non-goals

No plant, GPIO, DShot, failsafe timer, yaw-stick mapping, C20 policy change, Safety, Intent from sticks, `/dev` scan, live RX.

---

## 3. Integration rules

| Existing | C25 rule |
|---|---|
| C24 `step` | **Called only** by optional helper; mapper itself does not mix/ESC |
| C19 channels | Units reused; parse not rewritten |
| C20 | Unchanged |
| C11 smoke | May stay on `level_setpoint` (not required to switch to RC this Buy) |
| C5 `radio.py` | No stick APIs |
| C17 | Untouched |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | All mid (992) roll/pitch + documented throttle map → \|roll\|,\|pitch\| ≈ 0; collective finite in [0,1] |
| T2 | Roll max 1811 → +30° (documented sign); pitch max similarly; clip beyond range |
| T3 | Throttle 172 → collective ≈ 0; 1811 → ≈ 1 |
| T4 | Yaw channel changes do **not** change setpoint/collective this Buy |
| T5 | Optional helper: mapped inputs into `FlightControlLoop.step` produce four finite forces; **no** plant/GPIO |
| T6 | `radio.py` still has no `decode_crsf` / `open_serial`; C20 policy defaults unchanged |
| T7 | `RadioIntentAdapter` not_implemented; RejectAll default |
| T8 | `loop.py` / `loop.cpp` diffs empty (or smoke-only comments — math frozen) |
| T9 | C++ Catch2: mid sticks → ~level quat; throttle extremes |
| T10 | `pyproject` **`0.5.23`**; re-pin `0.5.22` |
| T11 | Full Python suite + host `ctest` green |
| T12 | Report: RC→setpoint ≠ flying ≠ sticks drive motors ≠ Safety allow |

---

## 5. Honesty / forbidden

```text
RC→setpoint ≠ flying ≠ sticks drive motors ≠ Safety allow ≠ yaw lock
```

**Exists:** documented AETR map from CRSF units to C24 args.  
**Impossible:** a pilot flying the craft; motors; failsafe; heading-hold yaw.

---

## 6. Docs

PRIORIDAD · PLATFORM §13 · ARCHITECTURE · README “What v0.5.23 includes”

---

## 7. Acceptance

**PASS when:** T1–T12 · mapper only · C24/C20 frozen · no GPIO · version `0.5.23`.  
**FAIL if:** sticks claimed to fly · Safety execute · yaw sold as heading · serial in this module · `radio.py` grows decode.

---

## 8. Handoff

```text
Engineer → ★ this IC (C25)
Claude   → mapper Python+C++ + tests + report + 0.5.23
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.23
Cursor   → next: C26 Esc HAL (default on this axis)
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C24 CLOSED @ v0.5.22. C25 B1-fase-c-rc-setpoint READY —
CRSF AETR → AttitudeSetpoint + collective for C24 step;
yaw unused; not flying; not Safety execute.
```

---

## 10. Engineer ★ checklist

1. Buy = **RC units → step args** (not motors) OK?  
2. AETR · yaw unused · ±30° · 172/992/1811 OK?  
3. Python + C++ OK?  
4. C24/C20 math/policy frozen OK?  
5. Version **`0.5.23`** OK?  
