# Implementation Review — #4d Sourced motor iFlight XING-E Pro 2207 2450KV B1

**Project:** Jarvis  
**Date:** 2026-09-10  
**Reviewer:** Cursor (Engineer Interface)  
**Against:** [IC](implementation_contract_geometry_sourced_motor_xing_e_pro_b1.md) · [report](implementation_report_geometry_sourced_motor_xing_e_pro_b1.md)  
**Verdict:** **PASS WITH NOTES** — T3 deferral correct · IC bag holdable · no code to review

---

## Scope of this review

There is **no implementation diff**. Engineer chose **T3**; report claims suite **2713** unchanged and zero `library/motores` / workspace motor edits. This review audits (1) whether T3 was the right call vs the IC, and (2) whether the parked bag is safe to reopen on T1 without re-litigating identity.

---

## Checklist

| Gate | Result |
|---|---|
| Thrust STOP honored (`MotorSpec.thrust_n` required; page silent) | **Pass** |
| Engineer T3 → no row, no invent, no T2 silent default | **Pass** |
| EMAX / `hobbywing_xrotor_2207_2450` not conflated | **Pass** (no writes) |
| 2450KV-only; 1800/2750 not seeded | **Pass** (N/A — deferred) |
| Geometry bag φ28.5×33.1 · shaft 5 · mass 33.8 cited | **Pass** (held in IC §0.1) |
| Electrical 42.63 A / 682.1 W = middle column of page triples | **Pass** (held) |
| No version bump / no `library/fc` creep | **Pass** |

---

## Notes (on reopen / IC hygiene)

| ID | Note |
|---|---|
| **N1** | **T3 > T2 for global catalog honesty** — agrees with Engineer guidance. Bare `thrust_n` still drives `find_motors_for_requirements`, BOM “measurable”, and FN-007 `resolve_propulsion_parameters` overwrite of `per_motor_max_thrust_n`. A borrowed EMAX 10.042 on an iFlight SKU would pollute sim/DSE while looking Class A. |
| **N2** | **Stator 22/7 is decode-from-“2207”**, not a labeled mm line on the page. IC already has STOP if Engineer rejects. On T1 reopen, keep that disclosure in `source_note`; do not upgrade to “page states stator 22×7” without a quote. |
| **N3** | **`compatible_prop_inch`**: page silent. Prefer `[]` until Engineer ★ affirms 5″ (craft now also moving to Gemfan 51466 ~5.1″). Do not invent `[5]` from “Adaptive Motor: 2207-2306” on a *prop* page. |
| **N4** | **Glyph**: Board disk from `diameter_mm` only; `height_mm` is card text (Motor B1). Smoke expectation “Ø28.5” is correct; do not expect a cylinder. |
| **N5** | **IC §7 handoff still says “pick T1/T2/T3 + ★”** — stale after T3. Should read: parked until T1 thrust bag + ★ reopen. Cosmetic; does not block. |
| **N6** | **Future stack coupling:** 5min is moving to **Tattu 4S** + SpeedyBee ESC while motors stay EMAX until T1. When XING seeds, rebind must refresh mass/KV/Ø and clear stale fit attest; conditioned OP path (MOP) may still lack `operating_points` → `legacy_estimate` on bare thrust — fine if T1 thrust is honest and labeled. |
| **N7** | Report filename exists for a **deferral** — good audit trail. Do not treat it as LANDING. |

---

## Reopen criteria (T1)

Minimum Engineer paste before implement:

```text
thrust: <gf or N>
prop: <model>
voltage / S: <e.g. 4S 16.0V>
source_url: <page with the table>
verbatim quote: <one line>
```

Then ★ the same IC (or a thin amend) and seed Option A SKU `iflight_xing_e_pro_2207_2450` with held geometry/electrical bag + cited thrust.

---

## Verdict

**PASS WITH NOTES** — deferral is the correct global outcome; bag is purchase-ready except thrust; reopen only on **T1**.
