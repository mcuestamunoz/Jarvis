# Investigation Review — Minimum Sensor KNOW for Aerial Autonomy Claim

**Date:** 2026-09-07  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_minimum_sensor_know_aerial_autonomy_claim.md](investigation_contract_minimum_sensor_know_aerial_autonomy_claim.md)  
**Report:** [investigation_report_minimum_sensor_know_aerial_autonomy_claim.md](investigation_report_minimum_sensor_know_aerial_autonomy_claim.md)  
**Parents:** Control parity @ **2164** · Geometry FC B1 @ **2332**

## Verdict

**PASS WITH NOTES**

Governing question answered. Three-level claim ladder held. Sharpest finding confirmed in code: **any** recognized `gps_model` **or** `sensor_type` (e.g. barometer) satisfies the architecture `control` gate the same way Here3 does — while `_control_evidence` never reads `sensors` at all. Outdoor waypoint minimum KNOW (GNSS + compass + FC-class) is scoped; indoor contrast proves non-universality. AUTONOMOUS FLIGHT CLAIM rung correctly **Deferred** as evidence-artifact, not parts list. Default lean **claim-copy / honesty only** is Buy-ready.

Engineer ★ still required before IC / code. No `src/` this investigation (FC B1 diffs pre-exist).

---

## Checklist

| Criterion | Result |
|---|---|
| A–J present | **Pass** |
| As-is Control PASS * / sensors asymmetry | **Pass** |
| Pixhawk 4 / Here3 sourced capabilities | **Pass** (PX4 + CubePilot live) |
| Outdoor waypoint minimum + indoor contrast | **Pass** |
| AUTONOMOUS FLIGHT evidence bar / Defer | **Pass** |
| Representation options without schema Buy | **Pass** |
| Honesty matrix + barometer≠GPS finding | **Pass** |
| Default lean · no catalog/CAD | **Pass** — claim-copy only |
| No `src/` this investigation | **Pass** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| `BLOCK_TO_COMPONENTS["control"]` = FC + sensors | **Confirmed** |
| `_control_evidence` reads only `flight_controller` | **Confirmed** — `engineering_readiness.py:1077-1083` |
| `_sensor_completeness`: any gps/type → `"medium"`; `"high"` unreachable | **Confirmed** + live: `"barómetro"` ≡ `"here3"` → both `medium` |
| Architecture component gate: all keys non-low | **Confirmed** — `orchestrator.py:2054-2072` |
| FC BOM tail “identidad, sin dato físico”; sensors has none | **Confirmed** — `project_closure.py:747-748` |
| Pixhawk 4: dual IMU + baro; mag on external GPS module | **Confirmed** — PX4 docs (prior session + report) |
| Here3: GNSS + IMU/compass; 2.5 m / RTK 0.025 m needs base | **Confirmed** — CubePilot Here3 manual this session |
| No optical-flow / lidar / VIO in `SENSOR_TYPE_MAP` | **Confirmed** |
| Energy path disjoint from FC/sensors | **Confirmed** (structural) |

---

## Agreement with report core

1. **Do not promote Control → Autonomous** — correct; Control PASS * already declaration-only.
2. **Barometer closes architecture `control` like Here3** — load-bearing honesty gap; confirmed.
3. **Pixhawk 4 has no on-board mag** — correct; compass KNOW must come from external module for that identity.
4. **Here3 ≠ RTK demonstrated** without correction infrastructure — correct.
5. **AUTONOMOUS FLIGHT CLAIM = flight evidence artifact** — correctly Deferred; no HD campaign.
6. **Claim-copy first; capability table / catalog late** — correct sequence.

---

## Notes (must land in IC if Engineer ★ claim-copy)

### N1 — Two gates, don’t conflate in copy

| Gate | Reads sensors? | Discriminates GNSS vs baro? |
|---|---|---|
| Architecture `control` complete | Yes (non-low required) | **No** |
| ERF `Control PASS *` | **No** (FC only) | N/A |

Honesty copy must not imply “Control PASS requires GNSS.” The live collapse is: **architecture complete + Control PASS can coexist with non-GNSS sensors**, and Control PASS can even exist with sensors unused by ERF. IC wording should target BOM/CLI honesty for the `sensors` line (and any “control declared” phrasing), **not** rewrite `_control_evidence`.

### N2 — Locked lean (await ★)

**Claim-copy / honesty only** — extend FC BOM-tail precedent to `sensors` (and/or CLI note). Suggested IC title from report is fine:

> *Sensors BOM/CLI honesty tail (generic sensor ≠ GNSS/compass) — copy only, no schema.*

Explicitly **out** of that IC: `_control_evidence` change · capability schema · `library/sensors/` · Here3 geometry · indoor vocabulary · Autonomous PASS.

### N3 — Component Validation Lead backlog (not this Buy)

Physical facts to validate later if capability KNOW is ever Bought: Pixhawk 4 internal suite; Here3 vs Here3+ IMU/mag variants; RTK infrastructure as separate KNOW; do not double-count FC-internal IMU as external `sensor_type=imu`.

### N4 — Provenance URL shape

CubePilot content matches; prefer stable path `docs.cubepilot.org/user-guides/here-3/here-3-manual` if cited in IC notes (report’s `.md` path variant is fine as long as content agrees).

---

## Buy recorded — Engineer ★ claim-copy (2026-09-07)

| Option | Outcome |
|---|---|
| Defer all code | Not bought |
| **Claim-copy / honesty only** | **★ Bought** → [IC](implementation_contract_sensors_bom_honesty_tail_b1.md) |
| Capability schema / catalog / Here3 geometry | Not now |

---

## What Engineer decides next

~~1. ★ Buy claim-copy → Cursor writes IC → Claude implements~~ **Done — IC open**  
Claude implements IC → Cursor review → optional BOM smoke.
