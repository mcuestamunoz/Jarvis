# Investigation Contract — Plate L×W / Rooster envelope (sourced, GetFPV vs Armattan)

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_geometry_plate_lw_sourced_b1.md`

**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · Engineer ★ default **B0** (no IC)  
**Parents:**
- [engineer_lock_sourced_envelope_to_3d.md](engineer_lock_sourced_envelope_to_3d.md) — cite → existing keys → `_geometry_from_spec`
- [engineer_lock_geometry_3d_mapping_path.md](engineer_lock_geometry_3d_mapping_path.md) — **rung 4**
- [engineer_lock_geometry_pre_assembly_honesty.md](engineer_lock_geometry_pre_assembly_honesty.md) — Armattan seed; GetFPV kit extras not in seed; no fake drawing
- Frame seed `armattan_rooster_5in` — `wheelbase_mm` 230, plates thickness only, `source_url` Armattan
- Fit / `"cabe"` / STEP-in-core / cylinder / Conversation Engine — **out**

**Type:** Source classification + what can become a **box** without invention.  
**Not** an Implementation Contract. **Do not implement. Do not seed. Do not bump version.**

**Checkpoint base:** package **`0.3.8`** · suite **2497** · propeller B2 REVIEWED

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ locks Buy before any IC.

---

## 0. Role split

```text
Engineer  → this is the 3D gap (frame has no box); GetFPV as retailer-secondary
Cursor    → this contract; review report; IC only after ★
Claude    → investigation_report_geometry_plate_lw_sourced_b1.md
```

---

## 1. Why this exists

3D already draws **box** from `length_mm`/`width_mm`/`height_mm` and **disk** from Ø. The live **frame** has wheelbase + thicknesses and **no** footprint → `_geometry_from_spec` returns `None`. Engineer wants sourced values to generate 3D. GetFPV Rooster kit text is **richer than Armattan on extras**, but **thickness ≠ L×W**.

Wrong next step:

```text
inventar Main Plate 150×150 · usar wheelbase 230 como L y W del sólido
· scrape GetFPV in-product · volcar todo el kit (nylon, VTX plates) como cajas
· cilindro de motor · 17 hélices GetFPV como bloqueo de este rung
```

Right question:

> Which **exact strings** on Armattan vs GetFPV (re-fetch live) affirm a **footprint** (L×W or L×W×H of a named plate or of the airframe), and which only affirm thickness / wheelbase / stack / camera mount? What is the **minimum honest Buy** so a frame solid can appear — including **B0 leave the gap** or **Engineer-declared** `source=declared` L×W?

---

## 2. Locked stances

1. Sourced-only. Quote the page. No sibling frames. No ChatGPT numbers without live re-fetch in **this** report.
2. GetFPV = **RETAILER_SECONDARY**. Armattan = **MANUFACTURER_PRIMARY** for this SKU. Classify each quoted field.
3. `_geometry_from_spec` needs the **full box triple** for a solid. A lone `thickness_mm` or `wheelbase_mm` is **not** a box. Do not propose stitching 230 + 4 mm into a plate prism unless a page names that prism.
4. `configuration: quad_x` / four arms on a shop page does **not** set project `motor_count`. Note as project CLI if relevant; do not recommend a code default-4.
5. Mapping rungs 1–3 and propeller B0–B2 stay closed. Do not reopen cylinder / STEP-in-core / `"cabe"`.
6. If GetFPV 403: say so; do not invent the HTML. Engineer may paste a quote; mark `engineer_provided` vs `live_fetch`.
7. Board `_fields` already shows properties — no new UI.

---

## 3. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| `library/frames/_datos.json` → `armattan_rooster_5in` | Keys today; `plates[]`; what is missing for a box |
| Frame schema (`library.py` / bind) | Does bind already project `length_mm`/`width_mm`/`height_mm` if present? `plates[].thickness_mm`? |
| `_geometry_from_spec` | Confirm: no wheelbase path, no thickness-only path |
| Live demo frame spec (if workspace readable) | Which properties on the card; is there already a solid? |
| Armattan `source_url` | Re-fetch. Quote presence/absence of plate L×W, body dimensions, bounding box |
| GetFPV `https://www.getfpv.com/armattan-rooster-5-fpv-frame.html` | Re-fetch. Quote footprint vs thickness vs kit extras (standoffs, HD plate, VTX plates, nylon). **Do not seed.** |

Other frames in `_datos.json` that **do** have a footprint string (e.g. iFlight “Body dimensions: 202×202”) — inventory only: could that pattern apply to Rooster? **Do not copy 202×202 onto Rooster.**

---

## 4. Report sections (required)

### A. What 3D would need

One table: candidate physical referent (main plate / whole airframe AABB / compressed-X silhouette) × keys required × whether any **cited** page supplies them.

### B. Armattan live quotes

Verbatim. Footprint: yes/no.

### C. GetFPV live quotes

Verbatim or **403**. Footprint: yes/no. Kit extras: list as **card-only** vs **box-eligible**.

### D. Honest Buys (ranked)

Recommend **one** lean next IC **or** B0 (gap) **or** Engineer-declared L×W. No schema dump. No crawler.

### E. Out of scope (explicit)

17-helix GetFPV pass · Dinoblades new SKU · motor cylinder · STEP · `"cabe"` · in-product scrape.

---

## 5. Done when

- [ ] Report written with live (or explicit 403) quotes  
- [ ] No `src/` / library seed in this investigation  
- [ ] A single recommended next Buy (or B0 / declared) that can put a **sourced or declared** frame box on the Board — or an explicit “still no box”

---

## Explicitly not this investigation

Implement plate geometry · invent mm · GetFPV crawler · helix census · Conversation Engine
