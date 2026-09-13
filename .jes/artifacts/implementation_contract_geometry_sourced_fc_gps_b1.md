# Implementation Contract — #4b Sourced FC + GPS envelopes B1

**Project:** Jarvis  
**Date:** 2026-09-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Cursor / Claude — after Engineer ★ on this text  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** READY FOR ★ — SpeedyBee F405 V4 + Holybro M10 purchase bags locked  
**Parents:**
- [engineer_lock_sourced_envelope_to_3d.md](engineer_lock_sourced_envelope_to_3d.md) ★ LOCKED  
- [implementation_contract_geometry_fc_envelope_b1.md](implementation_contract_geometry_fc_envelope_b1.md) — FC = `FLIGHT_CONTROLLER_DIMENSIONS` (**no** `library/fc/`)  
- [investigation_report_geometry_for_all_b1.md](investigation_report_geometry_for_all_b1.md) — sensors had **no** dims table yet  
- Battery #4 B1 LANDING @ **2703** — [IC](implementation_contract_geometry_sourced_dims_b1.md) · [report](implementation_report_geometry_sourced_dims_b1.md) (orthogonal)

**Type:** Identity-linked sourced boxes on free-text FC/GPS recognition (FC B1 pattern).  
**Not** `library/fc/` · **not** `library/sensors/` · **not** `catalog_ref` / bind · **not** battery · **not** Rooster L×W · **not** version bump.

**Baseline:** package **`0.4.1`** · suite **2703** · UI **83**

**Output:** `.jes/artifacts/implementation_report_geometry_sourced_fc_gps_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | Seed SpeedyBee F405 V4 + Holybro M10 L×W×H from Engineer purchase pages |
| 2 | Authority | Purchase-ground-truth (real parts to order/receive) |
| 3 | FC mechanism | `FLIGHT_CONTROLLER_MAP` + `FLIGHT_CONTROLLER_DIMENSIONS` only |
| 4 | GPS mechanism | New `GPS_DIMENSIONS` beside `GPS_MAP`; attach in `extract_sensor_properties` |
| 5 | GPS identity | Canonical **`holybro_m10`** — bare `"m10"` → `ublox_m10` **without** dims |
| 6 | Mass / mount / antenna | `source_note` / card only — **no** new schema; antenna 25×25×4 ≠ envelope |
| 7 | Property source | `source="declared"` (FC B1 convention) |
| 8 | Live refresh | Re-declare on 5min (stale FC 44×84×12 · sensors 40×40×12) |
| 9 | Completeness | Unchanged — dims do not gate FC/sensor completeness |
| 10 | Out | `library/fc|sensors` · Pixhawk table rewrite · bare `ublox_m10` dims · battery · Rooster |

**Product sentence:**

```text
Si digo SpeedyBee F405 V4 y Holybro M10 (lo que compro), Jarvis pega
41.6×39.4×7.8 y 50×50×14.4 en el Board. Sin abrir catálogo FC/GPS.
```

### 0.1 Citation bags — locked (re-fetched 2026-09-10)

#### Flight controller — GetFPV live confirm

```text
### speedybee_f405_v4
source_url: https://www.getfpv.com/speedybee-f405-v4-flight-controller-30x30.html
Dimension: 41.6(L) x 39.4(W) x 7.8(H)mm → 41.6 / 39.4 / 7.8
Weight: 10.5g (note only)
Mounting: 30.5 x 30.5mm · 4mm holes (note only — NOT the box)
MAP aliases (longest first): "speedybee f405 v4", "speedybee f405", "f405 v4"
Do NOT attach dims to bare "betaflight" or bare "f405"
```

#### GPS — Engineer primary URL (Holybro store) · re-fetched 2026-09-10

```text
### holybro_m10
source_url: https://holybro.com/products/m10-gps
  (Engineer paste had ?utm_source=chatgpt.com — strip UTM for SoT; same product path)
corroboration (prior): https://www.hobbydrone.cz/gps-module-holybro-m10-gps-module-standard/
Weight: 32g (note only)
Antenna: 25×25×4 mm ceramic patch — submodule, NOT component envelope
MAP: "holybro m10", "holybro m10 gps" → holybro_m10
existing "m10" → ublox_m10 unchanged (no dims)
page note: Holybro also sells M10 V2 — this Buy is the M10 page cited, not V2
```

**GPS geometry STOP (do not average — Engineer picks before ★ / before implement):**

| Source | Quote | Implication |
|---|---|---|
| **Holybro official** (Engineer link) | **φ50 × 14.4 mm** | circular footprint Ø50 · H 14.4 |
| HobbyDrone (earlier bag) | **50 × 50 × 14,4 mm** | axis-unlabeled box L×W×H |

| Option | Meaning |
|---|---|
| **G1 (preferred if Board stays box-only)** | Bounding square box **50×50×14.4** with `source_note` disclosing Holybro’s **φ50×14.4** (cylinder inscribed in square) |
| **G2** | Seed `diameter_mm=50` + `height_mm=14.4` only if existing projector already draws **disk** for sensors — **STOP** and ask if that path does not exist (do not invent cylinder renderer) |
| **G3** | Defer GPS dims until Engineer chooses; seed FC only in this Buy |

Default if Engineer ★ without letter: **G1**.

---

## 1. You (implementer)

- Wait for ★.  
- FC: add MAP aliases + `FLIGHT_CONTROLLER_DIMENSIONS["speedybee_f405_v4"]` with urls + source_note; extractor unchanged pattern vs `pixhawk_4`.  
- GPS: add `holybro_m10` to `GPS_MAP` (aliases longer than bare `m10`); add `GPS_DIMENSIONS`; attach L×W×H when model matches.  
- Tests T5–T8 style + `pixhawk_4` regression + bare m10 no dims.  
- Full suite green. Report.  
- **STOP** if asked to open `library/fc|sensors` or put Holybro dims on `ublox_m10`.

---

## 2. Intent

```text
Engineer cites SpeedyBee + Holybro M10
        ↓
aerial.py identity tables (FC + GPS_DIMENSIONS)
        ↓
re-declare on 5min
        ↓
Board boxes via _geometry_from_spec
```

---

## 3. Tests (minimum)

| ID | Assert |
|---|---|
| T1 | `extract_flight_controller_properties("SpeedyBee F405 V4")` → model + 41.6/39.4/7.8 |
| T2 | `pixhawk_4` still 44/84/12; bare "betaflight" no dims |
| T3 | `extract_sensor_properties("Holybro M10")` → `holybro_m10` + dims per Engineer G1/G2/G3 (default **G1**: 50/50/14.4 with φ50 disclosed in note) |
| T4 | `"m10"` alone → `ublox_m10` **without** L×W×H |
| T5 | Projector emits box when those properties are on a ComponentSpec |

---

## 4. Files (expected)

| Path | Action |
|---|---|
| `src/jarvis/domains/aerial.py` | MAP + DIMENSIONS + GPS_DIMENSIONS + extractor |
| `tests/test_geometry_sourced_fc_gps_b1.py` | write |
| `docs/IMPLEMENTATION_TASKS.md` / `.jes/state/engineering_state.json` | sync after report |
| `.jes/artifacts/implementation_report_geometry_sourced_fc_gps_b1.md` | write |
| `library/**` · battery · ui · version | **no** |

---

## 5. Smoke (Engineer)

On `autonomía-de-5min`:

1. Re-declare SpeedyBee F405 V4 → **41.6×39.4×7.8** (not 44×84×12).  
2. Re-declare Holybro M10 → envelope per G1/G2 (default **50×50×14.4** bounding square of φ50; not 40×40×12; not antenna 25×25). URL on card/note = holybro.com/products/m10-gps.  
3. Battery GenS Ace / ESC / motor / Rooster unchanged.

---

## 6. Out of scope

Battery re-seed · `#4b` user catalog contribution · crawler · Rooster L×W · version bump

---

## 7. Handoff

```text
Engineer → ★ this IC
Cursor/Claude → implement + report
Cursor → review
Engineer → smoke (re-declare FC + GPS)
```
