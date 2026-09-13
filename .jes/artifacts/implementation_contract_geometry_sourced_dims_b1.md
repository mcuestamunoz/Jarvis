# Implementation Contract — #4 Sourced dims B1 (5min Class A seed pack) — **BATTERY ONLY**

**Project:** Jarvis  
**Date:** 2026-09-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Cursor / Claude  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** LANDING — **IMPLEMENTED** Option A battery · suite **2703** · await review + Engineer smoke  
**Follow-on (FC + GPS):** [implementation_contract_geometry_sourced_fc_gps_b1.md](implementation_contract_geometry_sourced_fc_gps_b1.md) — separate Buy; do not fold into this closed battery scope.

**Parents:**
- [engineer_lock_sourced_envelope_to_3d.md](engineer_lock_sourced_envelope_to_3d.md) ★ LOCKED  
- Plate L×W Rooster investigation **B0** — **no** Rooster footprint  
- Battery envelope schema **CLOSED** @ **2316**  

**Type:** Catalog seed + 5min rebind — GenS Ace purchase identity.  
**Not** crawler · Rooster L×W · `#4b` · FC/GPS (see follow-on IC) · version bump.

**Baseline at implement:** package **`0.4.1`** · suite **2697** → **2703** · UI **83**

**Output:** [implementation_report_geometry_sourced_dims_b1.md](implementation_report_geometry_sourced_dims_b1.md)

---

## 0. Engineer Buy (locked — battery)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | Seed cited Class A for 5min battery gap |
| 2 | Identity | **Option A** — new SKU; generic `lipo_3s_2200mah` untouched |
| 3 | SKU | `gens_ace_2200mah_3s_35c_gtech` |
| 4 | Bag | 74.7×33.5×25.4 mm · mass 143 · C 35 · GenS Ace G-tech/Deans · URL genstattu |
| 5 | Authority | Engineer purchase-ground-truth |
| 6 | Projection | Prefer `source="catalog"`; **N1 delivered:** kept `declared` (golden precedent) |
| 7 | Out | Rooster · XT60 · FC/GPS · rewriting generic row |

### 0.1 Citation bag (battery) — locked

```text
### gens_ace_2200mah_3s_35c_gtech
source_url: https://genstattu.com/gens-ace-2200mah-3s-11-1v-35c-bashing-g-tech-lipo-battery-pack-with-deans-plug/
L×W×H: 74.7 × 33.5 × 25.4 · mass_g: 143 (±20 in note) · C: 35 · verified
```

---

## Delivered (see report)

- New Class A row + 5min rebind · tests T1–T6 · generic byte-stable · Rooster untouched.

## Handoff remaining

```text
Cursor → review battery B1
Engineer → smoke battery on autonomía-de-5min
FC + GPS → separate IC (sourced_fc_gps_b1) ★ then implement
```
