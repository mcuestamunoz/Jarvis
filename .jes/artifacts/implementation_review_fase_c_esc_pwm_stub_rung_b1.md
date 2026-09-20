# Implementation Review — Fase C ESC/PWM stub rung (`B1-fase-c-esc-pwm-stub-rung`)

**Date:** 2026-09-20  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_fase_c_esc_pwm_stub_rung_b1.md) · [report](implementation_report_fase_c_esc_pwm_stub_rung_b1.md)  
**Verdict:** **PASS** — ★ ACCEPT CLOSED @ tag **`v0.5.8`**

---

## Summary

C10 lands `esc.py`: `encode_motor_forces` maps C9 `MotorForceCommand` → `EscPwmCommand` (4 PWM µs widths, `protocol="pwm_us"` locked) with default linear map `[1000, 2000]` µs. `SimulatedEscSink` is in-memory only; `armed` defaults `False`; disarmed `apply` **records but refuses** (`applied=False`, `reason="disarmed"`) — documented IC §0 #6 choice. Exactly one encoding (no DShot/Oneshot/Multishot product path). No GPIO/serial/socket. Not wired to C4. Package **`0.5.8`**. Suite **3315 passed, 1 skipped** (+18). Docs honest: **no `v0.5.8` git tag**; framing is “landed, awaiting review/ACCEPT.” Controlled flight still unclaimed.

---

## Locks (IC §0)

| # | Lock | Result |
|---|---|---|
| 1–3 | Buy · one front · ESC/PWM stub only | **Pass** |
| 4 | PWM-µs only · default 1000–2000 | **Pass** — T1/T2/custom range |
| 5 | No GPIO/pigpio/`/dev/mem`/serial/socket | **Pass** — T6/T6b/source sweep |
| 6 | Disarmed default · pick one refuse path | **Pass** — record-but-refuse documented + T4 |
| 7 | RejectAll · no C4 auto-wire | **Pass** — T8 |
| 8 | C++ honesty · no C++/CMake tree | **Pass** — T7 + module docstring |
| 9–10 | Registry empty · craft untouched · smoke | **Pass** — T9/T10/smoke |
| 11–12 | Version `0.5.8` · no fake motors spinning | **Pass** (tag deferred to ACCEPT) |

---

## Cursor checks (independent)

| Check | Result |
|---|---|
| Read `esc.py` vs IC §2 | Match (`EscPwmCommand`, `encode_motor_forces`, `SimulatedEscSink`, `EscApplyResult`) |
| Encoding endpoints 0→1000 / 1→2000 / 0.5→1500 | Confirmed (T1) |
| Arming: disarmed refuse vs armed apply | Confirmed (T4/T5); record-but-refuse chosen |
| Forbidden public APIs / hardware imports | Absent (T6/T6b + grep under `flight_software/`) |
| Craft imports of esc symbols | Zero in `core/` + `adapters/` (T9) |
| `pytest` C10 module | **18 passed** |
| Full suite (T12) | **3315 passed, 1 skipped** |
| Tags: no `v0.5.8` | Confirmed (`v0.5.0`…`v0.5.7` only) |
| Premature ACCEPT/tag claims in docs | None found — honest “awaiting ACCEPT” framing |
| C++ honesty phrase | Present in `esc.py` module docstring |

**Note (non-blocking):** `README.md` §Next still said “Next: ★ C10 …” while the header already reflected landed-awaiting-review — stale tip blurb only; fixed in this review pass.

---

## Verdict

**PASS** — ★ ACCEPT CLOSED @ tag **`v0.5.8`**.

Ladder tip: six rungs (sample→filter→attitude→control→mix→PWM encode) still **never touch hardware** — “controlled flight” remains unclaimed. Next Buy still one front (rate→torque honesty · Safety-real · C++ · link — Engineer prioritizes).
