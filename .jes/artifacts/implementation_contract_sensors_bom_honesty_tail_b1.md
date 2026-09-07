# Implementation Contract — Sensors BOM honesty tail (generic sensor ≠ GNSS/navigation) — copy only

**Project:** Jarvis  
**Date:** 2026-09-07  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS** · CLOSED (suite **2336**)  
**Review:** [implementation_review_sensors_bom_honesty_tail_b1.md](implementation_review_sensors_bom_honesty_tail_b1.md)  
**Report:** [implementation_report_sensors_bom_honesty_tail_b1.md](implementation_report_sensors_bom_honesty_tail_b1.md)  
**Parents:**
- [investigation_contract_minimum_sensor_know_aerial_autonomy_claim.md](investigation_contract_minimum_sensor_know_aerial_autonomy_claim.md)
- [investigation_report_minimum_sensor_know_aerial_autonomy_claim.md](investigation_report_minimum_sensor_know_aerial_autonomy_claim.md)
- [investigation_review_minimum_sensor_know_aerial_autonomy_claim.md](investigation_review_minimum_sensor_know_aerial_autonomy_claim.md) — **PASS WITH NOTES**
- [implementation_contract_control_parity.md](implementation_contract_control_parity.md) — FC BOM / Control PASS * precedent
- Geometry FC B1 CLOSED suite **2332** (orthogonal)

**Type:** Claim-language / BOM display only.  
**Not** ERF predicates. **Not** schema. **Not** catalog. **Not** geometry. **Not** Autonomous PASS.

**Baseline:** package **`0.3.8`** · suite **2332** · Control parity CLOSED

**Output:** `.jes/artifacts/implementation_report_sensors_bom_honesty_tail_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **claim-copy / honesty only** | YES |
| 2 | Ladder | Keep CONTROL DECLARED ≠ NAVIGATION-CAPABLE KNOW ≠ AUTONOMOUS FLIGHT CLAIM |
| 3 | **N1** gates | Do **not** change `_control_evidence` / Control PASS * logic; do **not** imply Control PASS requires GNSS |
| 4 | Surface | **BOM `sensors` declarative line** (extend FC honesty-tail precedent) |
| 5 | Schema / catalog | **No** new fields · **no** `library/sensors/` · **no** capability table |
| 6 | Completeness | `_sensor_completeness` **unchanged** (still never `"high"`) |
| 7 | Architecture / ERF / ASSEMBLY_READY | **Unchanged** |

---

## 1. You

- Do **not** edit `_control_evidence`, `_derive_subsystem_verdict`, `_derive_overall`, gap types.
- Do **not** change `_sensor_completeness`, `classify_component`, `_MEASURABLE`, architecture `n/4` counters.
- Do **not** add sensor/FC catalog, bind, Continuity wizard, or capability schema.
- Do **not** change Control PASS * footnote string (already correct: declaración — sin física de control).
- Do **not** add Here3 geometry / indoor vocabulary / Autonomous PASS.
- Do **not** bump package version unless Engineer asks after review.
- Full suite green. Zero weakened tests.
- Write `implementation_report_sensors_bom_honesty_tail_b1.md` when done.

---

## 2. Intent

Today:

```text
◇ sensors: Here3 (declarativo)
◇ sensors: barómetro (declarativo)   ← same shape; reader may hear “GPS/nav OK”
```

Architecture `control` treats both as non-low. BOM must not let a bare `sensor_type` look like navigation KNOW, and must not let even a GNSS declaration look like demonstrated autonomous flight.

```text
CONTROL DECLARED (unchanged mechanics)
  +
honest sensors line (this IC)
        ≠
NAVIGATION-CAPABLE KNOW (not claimed)
        ≠
AUTONOMOUS FLIGHT CLAIM (Deferred)
```

---

## 3. Locked behavior

### 3.1 BOM — `format_bom_lines` / declarative `sensors` only

In `src/jarvis/core/project_closure.py`, for entries in the **`declarative`** bucket with `key == "sensors"` only, replace the plain `(declarativo)` tail with a **discriminated** honesty tail.

When `project_state` is available, read `design_properties.components["sensors"].properties` (same duck-typing style as other helpers in this file):

| Condition | Locked tail **inside** the parentheses |
|---|---|
| `gps_model` property present | `declarativo — GNSS declarado, no vuelo demostrado` |
| else (`sensor_type` only, or empty/unknown) | `declarativo — no implica GNSS ni navegación` |

Exact line shapes:

```text
◇ sensors: {name}{sku_suffix}{qty} (declarativo — GNSS declarado, no vuelo demostrado)
◇ sensors: {name}{sku_suffix}{qty} (declarativo — no implica GNSS ni navegación)
```

If `project_state` is `None` (or sensors component/properties unavailable), use the **safer** non-GNSS tail:

```text
(declarativo — no implica GNSS ni navegación)
```

**Unchanged:** all other declarative keys; `defined` / `incomplete` / `missing` formatting; FC defined tail (`identidad, sin dato físico`); Control PASS * CLI footnote.

Prefer a tiny helper (e.g. `_bom_sensors_declarative_tail(entry, project_state)`) next to `_bom_completeness_tail` — same file only.

### 3.2 CLI readiness

**No required change** to `_render_readiness_block` / Control PASS * footnote (N1: Control PASS is sensors-blind; do not invent a second footnote that implies Control PASS needs GNSS).

BOM lines rendered wherever `format_bom_lines(..., project_state=...)` is already called with state will pick up the new tail automatically. If any call site drops `project_state` for a path that shows sensors, prefer passing it when trivially available — **do not** refactor call graphs beyond that.

### 3.3 Out of this IC

- Continuity situation / next-step copy  
- Architecture 4/4 strings  
- ERF JSON verdict values  
- Capability tables / NAVIGATION-CAPABLE display  
- Changing barometer vs Here3 architecture gate behavior  

---

## 4. Tests (required)

Extend `tests/test_project_closure_v1.py` (or adjacent BOM tests):

1. **GNSS path:** sensors with `gps_model` (e.g. Here3 / M9N) in declarative → line starts with `◇`, contains exact substring  
   `declarativo — GNSS declarado, no vuelo demostrado`  
   and does **not** contain `no implica GNSS ni navegación`.
2. **Non-GNSS path:** sensors with only `sensor_type` (e.g. barometer) → line contains exact substring  
   `declarativo — no implica GNSS ni navegación`  
   and does **not** contain `GNSS declarado`.
3. **FC regression:** `defined` flight_controller still has `identidad, sin dato físico`; motors defined line still lacks sensors/FC honesty phrases as before.
4. **Update** `test_bom_sensors_declarative_unaffected_by_control_suffix` (or replace): sensors must **not** get the FC phrase `identidad, sin dato físico`, but **must** get the new sensors honesty tail (GNSS variant for that fixture’s `gps_model`).

Do not commit `workspace/`. Run full suite; report count in implementation report.

---

## 5. Files expected to change

| File | Change |
|---|---|
| `src/jarvis/core/project_closure.py` | sensors declarative honesty tail (+ small helper) |
| `tests/test_project_closure_v1.py` (and/or adjacent) | §4 coverage |
| `.jes/artifacts/implementation_report_sensors_bom_honesty_tail_b1.md` | write |

**Do not change:** `engineering_readiness.py` control evidence, `aerial.py` completeness/maps, `adapters/cli/main.py` Control footnote (unless a one-line BOM call-site needs `project_state` passed — document if touched), catalog, Geometry, version.

---

## 6. Explicit non-goals

`_control_evidence` / Control PASS rewrite · capability schema · `library/sensors/` · Continuity sensor wizard · Here3 dims · indoor vocabulary · Autonomous PASS · ASSEMBLY_READY gating · energetic autonomy · Prop/Energy unlock · System Optimization · Conversation Engine · version bump · weakened tests

---

## 7. Done criteria

- [x] GNSS sensors BOM line uses locked GNSS honesty tail.
- [x] Non-GNSS sensors BOM line uses locked non-GNSS honesty tail.
- [x] FC / Control PASS * / architecture / completeness unchanged.
- [x] Full suite green; implementation report written.
- [x] Cursor review PASS before Engineer close.

---

## 8. Role split

```text
Engineer ★ → Buy claim-copy (this contract)
Claude     → implement exactly this IC + report
Cursor     → implementation review
Engineer   → optional CLI/BOM smoke / next focus
```
