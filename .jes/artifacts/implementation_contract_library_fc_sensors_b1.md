# Implementation Contract — Relocate FC + GPS envelopes into `library/` (`B1-library-fc-sensors`)

**Project:** Jarvis  
**Date:** 2026-09-14  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** READY FOR ★ — **P0 architecture correction**  
**Parents:**
- Engineer 2026-09-14: FC/GPS dims inside `aerial.py` = **grave failure** — physical catalog facts must live under repo-root `library/` with the other families, **not** under `src/`
- Prior IC [#4b sourced FC+GPS](implementation_contract_geometry_sourced_fc_gps_b1.md) **wrongly locked** “Not `library/fc/` · not `library/sensors/`” — **this Buy supersedes that ban**
- Working pattern to mirror: `library/esc/_datos.json` + `EscSpec` + `ComponentLibrary.get_esc` / `list_escs` + `bind_esc_from_catalog` + `esc_catalog_assist`
- Live identities in use: SpeedyBee F405 V4 · Pixhawk 4 · Holybro M10 (dims already cited; **move, do not re-invent**)

**Type:** Move **sourced physical envelopes** for flight controllers and GPS/sensors from hard-coded dicts in `src/jarvis/domains/aerial.py` into:

```text
library/fc/_datos.json
library/sensors/_datos.json
```

…loaded **only** via `ComponentLibrary` (same rule as motors/ESC/propellers/batteries/frames).  
**Not** inventing new mm. **Not** deleting identities. **Not** plate-box. **Not** disk-station attest. **Not** version bump. **Not** `workspace/` mutation unless Engineer ★ Path D apply (default: **no** workspace edit — live projects keep working via same model strings / rebind).

**Output:** `.jes/artifacts/implementation_report_library_fc_sensors_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**2892** · UI ≥**105** (or current green at ★ time)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-library-fc-sensors`** — FC + sensors/GPS catalogs under `library/` |
| 2 | Failure corrected | Physical L×W×H (+ citation metadata) **must not** live as module-level dicts inside `src/jarvis/domains/aerial.py` |
| 3 | Folders | Exactly **`library/fc/`** and **`library/sensors/`**, each with `_datos.json` (parallel to `library/esc/`, `library/motores/`, …). GPS modules are rows in **`sensors`**, not a third top-level family this Buy |
| 4 | Rows to migrate (verbatim) | **FC:** `pixhawk_4` (44×84×12), `speedybee_f405_v4` (41.6×39.4×7.8). **Sensors:** `holybro_m10` (50×50×14.4 + existing source_note honesty: φ50 bound / antenna submodule note). Copy `source_url` / `source_note` / dims **unchanged** |
| 5 | Loader authority | `ComponentLibrary` is the **only** reader of these JSON files (existing library.py contract). Add `FcSpec` / `SensorSpec` (names OK) + `get_*` / `list_*` / `has_*` |
| 6 | `aerial.py` after move | May keep **language maps** (`FLIGHT_CONTROLLER_MAP` / `GPS_MAP` / completeness) as **alias → canonical id** only. Extractors look up dims via `ComponentLibrary`, **never** from a local dimensions dict. **Delete** `FLIGHT_CONTROLLER_DIMENSIONS` and `GPS_DIMENSIONS` from `aerial.py` |
| 7 | Bind / `catalog_ref` | Add `bind_flight_controller_from_catalog` / `bind_sensor_from_catalog` (or single patterned helpers) projecting L×W×H + identity fields onto `ComponentSpec`, with `catalog_ref.family` ∈ {`fc`, `sensor`} (or `flight_controller` / `sensors` — pick one pair, document in report, stay consistent). Mirror ESC confidence/`source="declared"` convention unless an existing FC convention must be preserved byte-identical for live cards |
| 8 | Assist UX | `control_identity_catalog_assist` must list from **`list_fcs()` / `list_sensors()`** (or equivalent), **not** import dimension dicts from `aerial`. Declare/pick phrases stay the ones extractors already understand |
| 9 | Forbidden | Invent mm · merge antenna 25×25×4 into M10 box · seed bare `ublox_m10` / bare `m10` dims · leave a duplicate SoT dict in `src/` “for convenience” · new Conversation Engine |
| 10 | Version | **No** bump |

**Product sentence:**

```text
FC y GPS/sensores viven en library/fc y library/sensors como el ESC.
aerial.py solo reconoce el lenguaje; las cotas salen del catálogo.
```

### 0.1 What `aerial.py` does today (the bug)

```text
FLIGHT_CONTROLLER_DIMENSIONS / GPS_DIMENSIONS
  = hard-coded physical SoT inside domain inference code under src/

extract_flight_controller_properties / extract_sensor_properties
  = on model match, attach length_mm/width_mm/height_mm from those dicts

control_identity_catalog_assist
  = “ayúdame a elegir” lists those same dict keys

→ Result: catalog physics mixed into language/domain module;
   invisible beside library/motores|esc|helices|baterias|frames;
   violates “ComponentLibrary is the ONLY place that reads _datos.json”
   spirit by never having _datos.json for FC/GPS at all.
```

### 0.2 Target shape (illustrative — match ESC field style)

`library/fc/_datos.json`:

```json
{
  "speedybee_f405_v4": {
    "manufacturer": "SpeedyBee",
    "model": "F405 V4",
    "identity_status": "verified",
    "length_mm": 41.6,
    "width_mm": 39.4,
    "height_mm": 7.8,
    "source_url": "…",
    "source_note": "…(migrate verbatim from aerial.py)…"
  },
  "pixhawk_4": { "…": "… verbatim …" }
}
```

`library/sensors/_datos.json`:

```json
{
  "holybro_m10": {
    "manufacturer": "Holybro",
    "model": "M10 GPS",
    "identity_status": "verified",
    "length_mm": 50.0,
    "width_mm": 50.0,
    "height_mm": 14.4,
    "source_url": "…",
    "source_note": "… verbatim incl. φ50 / antenna submodule honesty …"
  }
}
```

### 0.3 Smoke target

```text
project: 10-min-autonomía (SpeedyBee F405 V4 + Holybro M10)
expect: cards still show same L×W×H; Board boxes unchanged;
        library/fc + library/sensors exist; aerial.py has no DIMENSIONS dicts;
        ayúdame a elegir controladora/GPS lists from ComponentLibrary
code_star: library_json + ComponentLibrary + bind + assist rewire + extractor lookup
```

---

## 1. You (Claude) — after ★

1. Create `library/fc/_datos.json` and `library/sensors/_datos.json` with migrated rows (verbatim dims + notes).  
2. Extend `ComponentLibrary` with specs + loaders + get/list/has.  
3. Add catalog bind helpers; wire writers/orchestrator pick paths as ESC already is (minimal surface — do not invent a new acquisition architecture).  
4. Rewire `extract_*` to resolve dims via library lookup by canonical model id.  
5. Rewire `control_identity_catalog_assist` off `aerial` dimension imports.  
6. **Delete** `FLIGHT_CONTROLLER_DIMENSIONS` and `GPS_DIMENSIONS` from `aerial.py` (aliases/maps may remain).  
7. Update tests that imported the old dicts; add loader/bind/extract regressions.  
8. Do **not** bump version. Do **not** mutate `workspace/` by default.

---

## 2. Tests

| ID | Behavior |
|---|---|
| L1 | `get_fc("speedybee_f405_v4")` → 41.6×39.4×7.8; `get_fc("pixhawk_4")` → 44×84×12 |
| L2 | `get_sensor("holybro_m10")` → 50×50×14.4 |
| L3 | `aerial` module has **no** `FLIGHT_CONTROLLER_DIMENSIONS` / `GPS_DIMENSIONS` attributes |
| L4 | `extract_flight_controller_properties("SpeedyBee F405 V4")` still yields same L×W×H |
| L5 | `extract_sensor_properties` for Holybro M10 still yields same L×W×H; bare `"m10"` still no dims |
| L6 | Identity assist lists SKUs from `list_fcs` / `list_sensors` |
| L7 | Bind projects `catalog_ref` + box props |
| L8 | Full suite green; UI unchanged expectation (backend/catalog cycle) |

---

## 3. Smoke (Engineer) — `10-min-autonomía`

1. Confirm `library/fc/_datos.json` and `library/sensors/_datos.json` on disk.  
2. Board/cards: FC 41.6×39.4×7.8 · sensors 50×50×14.4 (same as today).  
3. Optional: `ayúdame a elegir` controladora / GPS still lists the sourced identities.  
4. Grep/`__dict__`: no dimension SoT left in `aerial.py`.

---

## 4. Report must include

- Explicit supersession of #4b “no library/fc|sensors” lock.  
- File tree + SKU census.  
- Confirmation extractors no longer own physical SoT.  
- Suite counts · no version bump · `workspace/` clean.

---

## 5. Cursor review gates

- [ ] `library/fc` + `library/sensors` exist; dims match prior cited values  
- [ ] No DIMENSIONS dicts in `aerial.py`  
- [ ] ComponentLibrary-only JSON read  
- [ ] Assist/bind/extract wired to library  
- [ ] No invented mm / no antenna fold-in  
- [ ] Live 10-min envelopes unchanged  
- [ ] `0.4.1` · suite green  

---

## 6. After CLOSED

- Disk-axial Visor / fit-relations remain orthogonal.  
- Future FC/GPS SKUs are catalog rows, not patches to `aerial.py`.  
- Optional later: richer FC/sensor catalog fields (mass, mount pattern) — separate ★.
