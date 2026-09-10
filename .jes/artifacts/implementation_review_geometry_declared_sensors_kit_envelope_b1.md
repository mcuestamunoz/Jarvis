# Implementation Review — Declared sensors + kit envelope B1

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_geometry_declared_sensors_kit_envelope_b1.md](implementation_contract_geometry_declared_sensors_kit_envelope_b1.md)  
**Report:** [implementation_report_geometry_declared_sensors_kit_envelope_b1.md](implementation_report_geometry_declared_sensors_kit_envelope_b1.md)  
**Buy:** Engineer ★ **B1-sensors-kit-envelope** (step 2/4)  
**Role:** Claude implemented · Cursor reviews

## Verdict

**PASS**

Writer allowlist, parser subjects, no-thickness rule for sensors/kit, and P1–P10 match the IC. Suite **2593** (Cursor re-ran full pytest). Version **0.3.8**. No library dim seeds. Live Board smoke is Engineer’s (§6).

---

## Checklist

| Criterion | Result |
|---|---|
| #2 Writer allowlist + `sensors`/`power_connector`/`signal_harness` | **Pass** |
| #2 Still ValueError on esc/motors/frame | **Pass** — P3 |
| #3 Three mm required; no thickness fallback | **Pass** — P7 + `_NO_THICKNESS_FALLBACK_KEYS` |
| #4 CLEAR pops only box axes | **Pass** — P4 |
| #5 `source=declared` | **Pass** — P1 |
| #6 Identity / pin / pitch / catalog_ref untouched | **Pass** — P1/P2/P4 |
| #7 Kit nouns presence-gated | **Pass** — P6 missing → INCOMPLETE |
| #7 Sensors via existing subject noun | **Pass** — P5 |
| #8 `respecto` → NONE | **Pass** — P8 |
| #8 Battery + placa principal regression | **Pass** — P9 (+ prior battery tests) |
| #9 No auto-pose / no visor edit this Buy | **Pass** |
| #10 No library L×W×H seeds; cable length ≠ box | **Pass** — P10 + Cursor re-check |
| #11 No version bump | **Pass** — `0.3.8` |
| Orchestrator: no parallel route | **Pass** — copy-only INCOMPLETE hint |
| Full suite **2593** | **Pass** — Cursor |

---

## Independent checks

| Claim | Cursor |
|---|---|
| `"cable de señal"` normalizes → SET harness | **Confirmed** |
| Kit library rows still lack L×W×H | **Confirmed** |
| No `library/sensors` / `sensores` catalog | **Confirmed** |
| P1–P10 + battery/plate regression file | **20 passed** |

---

## Notes

### N1 — Smoke still required

Report’s live probe was read-only (no `workspace/` write). Engineer must type real mm on `autonomía-de-5min` for Board/3D (§6).

### N2 — Sensors missing-key path

Like battery: parser resolves `sensors` even if absent; orchestrator “aún no declarado” handles it. Kit missing-key is stricter (INCOMPLETE). Matches IC #7 wording and battery precedent — not a fail.

---

## Engineer smoke (next)

| Step | Expected |
|---|---|
| `declara el gps 40 x 40 x 12 mm` (or real mm) | sensors box; `gps_model` unchanged |
| Optional kit triple | box; pin/pitch untouched |
| No declare → no invented GPS/cable box | |

Record [engineer_smoke_geometry_declared_sensors_kit_envelope_b1.md](engineer_smoke_geometry_declared_sensors_kit_envelope_b1.md).
