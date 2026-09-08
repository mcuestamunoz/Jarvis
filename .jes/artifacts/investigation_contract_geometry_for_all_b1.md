# Investigation Contract — Geometry for all declared components (Fase 2 / G)

**Project:** Jarvis  
**Date:** 2026-09-08  
**Author:** JES / Cursor (Engineer Interface)  
**Formulation:** Engineer ★ preferred sequence **E → G → Conn** after Board status review (plan `geometry_status_next`)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_geometry_for_all_b1.md`

**Status:** READY FOR INVESTIGATION  
**Parents:**
- Engineer sequence: Fase 1 hygiene **E** → Fase 2 geometry-all **G** → Fase 3 connect **Conn**
- [implementation_contract_catalog_bound_refresh_b1.md](implementation_contract_catalog_bound_refresh_b1.md) — **PASS WITH NOTES** @ suite **2406** (Fase 1 refresh path shipped; demo ESC smoke may still be pending)
- [engineer_lock_geometry_assembly_relation_rung_closed.md](engineer_lock_geometry_assembly_relation_rung_closed.md) — assembly **relation** CLOSED; pose DEFERRED; fit FROZEN as default-next
- [engineer_lock_geometry_spatial_representation_progression.md](engineer_lock_geometry_spatial_representation_progression.md)
- Geometry `representar` CLOSED: Battery / Motor / ESC / FC envelopes
- Board glyphs B1 CLOSED: `{box, disk}` via projector when dims exist (`test_geometry_*`)
- Structure B: arm/plate **thickness** shipped; plate **L×W** never projected; cage/standoff material-only in seeds
- Catalog item **D** (plate footprints) — historically queued; **folded into this Fase 2 G** (do not open a parallel “D” track)
- Here3 / Pixhawk identity — **FROZEN** until separate ★

**Type:** Investigation only — which declared components/parts still lack honest geometric KNOW for Board `representar`/`visualizar`, what can be sourced without invention, and the **minimum ordered Buy(s)**.  
**Not** an Implementation Contract. **Do not implement.**  
**Not** Fase 3 mount-connect (Conn). **Not** fit/pose. **Not** CAD/FEA. **Not** identity unfreeze.

**Checkpoint base:** package **`0.3.8`** · suite **2406**

**Single objective (locked):**

> Produce an evidence-backed inventory of **geometry gaps** across all live component/part families on the demo Board (and seed/bind paths), and recommend the **smallest honest next Buy** so more cards can show declared volume (text and/or glyph) — without inventing dims, without unfreezing Here3, and without opening Conn/fit/pose.

**Product sentence this must enable (after a later Buy):**

```text
Más componentes del Board tienen volumen declarado honestamente — o el sistema dice con claridad por qué no (sin inventar L×W / footprint).
```

**Live demo snapshot (Cursor triage 2026-09-08 — `workspace/autonomía-de-10min-9ada1a1b0cca`):**

| Key | Envelope / glyph-relevant dims today | Notes |
|---|---|---|
| `battery` / `esc` / `motors` / `flight_controller` | L×W×H or motor diameters | Representar CLOSED |
| `propellers` | `diameter_in` + `pitch_in` | Disk glyph path already converts `diameter_in`→mm in projector tests — confirm live Board |
| `frame` | `size_class_inch` (+ mass/material); seed also has `wheelbase_mm` | No L×W×H box; wheelbase ≠ footprint |
| `frame_arm` / `frame_plate*` | `thickness_mm` (+ material/label) | **Glyph absent** when only thickness (`test_geometry_absent_when_only_thickness_declared`) |
| `frame_cage` / `frame_standoff` | material only | No dims in seed projection |
| `sensors` (Here3) | model string only; **no** `catalog_ref` | Identity **FROZEN** |

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ Buy before any IC.

**Do not implement. Do not bump version. Do not weaken tests. Do not invent plate L×W, cage dims, or Here3 footprint. Do not open Conn Continuity mass-mount IC. Do not open fit/pose. Do not unfreeze Here3/Pixhawk in the Buy — flag collisions only.**

---

## 0. Role split

```text
Engineer  → Fase 2 G after E (refresh)
Cursor    → this contract; review; IC after ★
Claude    → investigation_report_geometry_for_all_b1.md
Engineer ★ → Buy lean / Defer / re-scope / skip to Conn
```

---

## 1. Why this investigation exists

Fase 1 restored a path to **trust catalog numbers**. The Board still shows **islands of geometry**: catalog envelopes + FC table on some cards; structure parts and sensors largely thickness/material/name only. Glyphs already know how to draw `{box, disk}` when dims exist — the gap is **data honesty + projection**, not a new glyph vocabulary (unless evidence forces a tiny additive shape — justify or reject).

Wrong next moves without evidence:

- Invent Main Plate 150×150 “because 5-inch frames look like that”
- Treat `wheelbase_mm` as a plate footprint
- Unfreeze Here3 to paste a datasheet guess
- Jump to Conn or fit because cards “look empty”

---

## 2. Locked stances

1. Declared dims only from cited seed/page/identity table — **no invention**.  
2. Thickness alone is honest Structure KNOW; it is **not** a box glyph (already tested).  
3. Board load must not invent geometry.  
4. Assembly relation rung stays CLOSED — this investigation may **name** Conn as later Fase 3, not Buy Conn.  
5. Pose DEFERRED / fit FROZEN as default-next — unchanged.  
6. Here3 / Pixhawk identity FROZEN — sensors geometry Buy only if identity already unlocked **or** dims attach to a non-identity path that does not pretend SKU certainty (likely: **out** / defer).  
7. Prefer extending existing bind/project paths over new geometric SoT.

---

## 3. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| `project_spatial_nodes` / geometry helper | Which property sets emit `box` / `disk` / absent |
| Demo `state.json` components | Gap table (extend Cursor snapshot; include propeller live glyph) |
| `library/frames/_datos.json` + `frame_part_specs_from_catalog` | What plate/arm/cage/standoff fields exist vs projected |
| Manufacturer pages cited in `source_note` (Armattan / TBS / iFlight) | Any **honest** plate L×W, standoff height, cage dims? Quote or “not stated” |
| `library/helices/_datos.json` + propeller bind | Already sufficient for disk? Any missing mass/other? |
| FC envelope table | Already done — confirm no reopen |
| Sensors / Here3 path | Confirm freeze + absence of catalog_ref / dims |
| Prior Structure B additive enrichment reports | Reuse; do not contradict closed thickness Buys |

---

## 4. Questions the report must answer

### A. Gap matrix

For each family/key class: **has representar text?** **has glyph?** **blocker** (no source / not projected / identity freeze / thickness-only by design).

### B. Source honesty

For the top gaps (plates L×W, cage, standoff, sensors, frame box, propeller if any): what does the **cited page** actually state? Paste/cite. Mark **UNSOURCED** explicitly.

### C. Minimum Buy options (must include)

| Option | Intent |
|---|---|
| **B0 — Defer geometry-all / skip to Conn** | Gaps are mostly unsourced; Conn delivers more product value now |
| **B1 — Narrow sourced projection** | Only fields with proven page evidence (e.g. standoff **height** if page states it; propeller glyph confirmation-only; etc.) |
| **B1+ — Plate footprint family** | Only if ≥1 seed page states plate L×W (or equivalent) honestly — else reject |
| **B2 — New glyph / schema shape** | Only if box/disk insufficient for an honestly sourced dim set |

Reject options that require invention or identity unfreeze unless Engineer ★ overrides.

### D. Contingency field/API sketch (not an IC)

If B1 recommends projection: name target properties, which binder/projector touches them, Board effect (text vs glyph), and refresh interaction with catalog-bound refresh B1. Explicitly **not** an Implementation Contract.

### E. Out of scope checklist

Confirm Conn / fit / pose / Here3 unfreeze / CAD untouched by the recommended Buy.

---

## 5. Report format (mandatory sections)

1. **Executive recommendation** — one lean (B0 / B1 / B1+ / B2) + one sentence.  
2. **Gap matrix** — demo + seed/bind.  
3. **Source table** — stated vs not stated (plates/cage/standoff/sensors/…).  
4. **Buy options** — costs, risks, rejection of invention paths.  
5. **Contingency sketch** (if any Buy ≠ B0).  
6. **Explicit non-goals honored.**

---

## 6. Done criteria (investigation)

- [ ] Live demo + projector rules cited  
- [ ] Plate L×W / cage / standoff / Here3 honesty settled with sources  
- [ ] Propeller glyph status confirmed (already-done vs gap)  
- [ ] Clear lean with B0 allowed  
- [ ] No code; no invented numbers presented as Buy-ready facts  

---

## 7. Stop conditions

Stop and ask before: proposing fabricated plate footprints, unfreezing Here3 inside this Buy, or bundling Conn/fit into the same IC.
