# Investigation Report — Geometry for All Declared Components (Fase 2 / G)

**IC:** [investigation_contract_geometry_for_all_b1.md](investigation_contract_geometry_for_all_b1.md)
**Investigator:** Claude Code
**Date:** 2026-09-08
**Baseline:** package `0.3.8` · suite 2406 (unchanged — investigation only, no code/tests touched)

---

## 1. Executive recommendation

**B1 — narrow, per-SKU sourced text enrichment, tightly scoped to 3 newly-verified facts across 2 of the 4 seeded frames.** A fresh, live re-fetch of all four frame source pages (not a rubber-stamp of the existing `source_note` text) surfaced real, citable data the current seed doesn't yet carry: iFlight XL7 V4's page states **"Body dimensions: 202x202mm"** and **"Standoff height: 25mm (4 pieces), 32mm (4 pieces)"**; TBS Source One V5 5in's page states **"Standoff Height: 30mm and 22mm."** Nothing new was found on the other two pages (TBS 7in DC, Armattan Rooster). None of this closes a *glyph* gap — a footprint without a height still can't become a box, and a height without a diameter still can't become a disk — so this Buy is **text-only (`representar`), not a new glyph**. Given the payoff is three additional text lines across two of fourteen demo cards, with zero new glyphs and a real (if small) schema/projector cost, **B0 (defer, let Fase 3 Conn proceed) is an equally defensible choice** — this report names both, states the evidence precisely, and leans B1 only because it is genuinely free of invention and matches the IC's own worked example ("standoff height if page states it") almost exactly.

---

## 2. Gap matrix

Live-projected via `project_spatial_nodes` against the actual demo project `workspace/autonomía-de-10min-9ada1a1b0cca/state.json` this session (not a synthetic fixture):

| Key | Representar (text) | Glyph | Blocker class |
|---|---|---|---|
| `motors` | ✅ | ✅ `disk` Ø27.9mm | — (CLOSED) |
| `esc` | ✅ | ✅ `box` 50×21.6×12mm | — (CLOSED) |
| `battery` | ✅ | ✅ `box` 37×35×75mm | — (CLOSED) |
| `flight_controller` | ✅ | ✅ `box` 44×84×12mm (Pixhawk 4) | — (CLOSED) |
| `propellers` | ✅ | ✅ `disk` Ø127.0mm — **confirmed live**, `diameter_in=5.0 → 127.0mm`, exactly the documented conversion | — (CLOSED, IC's own open question resolved: yes, already correct on the live Board) |
| `frame` (root) | ✅ (`mass_kg`, `size_class_inch`, `material`) | ❌ | **Shape mismatch, not just missing data** — `wheelbase_mm` is a single motor-to-motor diagonal distance and `size_class_inch` a propeller-clearance class; neither maps to a box's L×W×H or a disk's single diameter without inventing an aspect ratio. Even a real footprint number (see §3) has no accompanying height. |
| `frame_arm` | ✅ (`thickness_mm`, `material`, `count`) | ❌ (by design) | Thickness-only is honest Structure KNOW, never glyph-worthy — matches the already-shipped `test_geometry_absent_when_only_thickness_declared` |
| `frame_plate` / `_2` / `_3` / `_4` | ✅ (`thickness_mm`, `material`, `label`) | ❌ | No L×W stated on **any** of the 4 seed pages (re-verified live, §3) — genuinely unsourced, not merely unprojected |
| `frame_cage` | ✅ (`material` only, Armattan) | ❌ | Zero dims stated on any page for any seed row |
| `frame_standoff` | ✅ (`material`, `count`) | ❌ | **Height IS sourced** for 2/4 rows (§3) but not yet in the seed/schema at all — a real, small, closeable gap |
| `sensors` (Here3) | ✅ (`gps_model` string only) | ❌ | Identity FROZEN (no `catalog_ref` family exists for sensors at all — confirmed `CatalogRef.family` has no `"sensors"`/`"flight_controller"` literal), zero dims table analogous to `FLIGHT_CONTROLLER_DIMENSIONS` exists (`extract_sensor_properties` only ever writes `gps_model`/`sensor_type` strings) |

**9 of 14 live demo cards lack a glyph.** Of those 9, 7 (arm, 4 plates, cage, sensors) are correctly, honestly blocked (thickness/material/identity-only by design or freeze) and require no action. 1 (frame root) is blocked by a genuine shape/unit mismatch even with the new data found. 1 family (standoff, ×1 node) has real sourced data not yet captured anywhere in the schema.

---

## 3. Source table (live re-fetch this session — not the archived `source_note` text)

| Seed row | Plate L×W | Cage dims | Standoff dims | New facts found today |
|---|---|---|---|---|
| `armattan_rooster_5in` | **Not stated** (confirmed live) | **Not stated** (material "titanio" only) | **Not stated** (material "aluminio" only) | Page states a 30.5mm center-stack mount and 28.5mm camera mount and a "max stack height (22mm)" — **mount-hole-pattern / payload-clearance data, not a plate footprint or standoff dimension** — flagged in §6, not actioned here |
| `tbs_source_one_v5_5in` | **Not stated** | **Not stated** | **STATED**: *"Standoff Height: 30mm and 22mm"* | ✅ new: standoff height (two lengths) |
| `tbs_source_one_v5_1_7in_dc` | **Not stated** | **Not stated** | **Not stated** | none — only wheelbase/weight/thickness, all already seeded |
| `iflight_xl7_v4_7in` | **STATED**: *"Body dimensions: 202x202mm"* | **Not stated** | **STATED**: *"Standoff height: 25mm (4 pieces), 32mm (4 pieces)"* | ✅ new: body footprint + standoff height; page also states "Mounting holes: 30.5\*30.5mm, 20\*20mm" — mount-pattern data, flagged in §6, not actioned here |

**UNSOURCED, explicitly, across all 4 rows:** plate length×width for 3/4 rows, cage dimensions for 4/4 rows, standoff dimensions for 2/4 rows. No page states a full 3-axis footprint for any plate on any frame. **Nothing here should be read as "close enough to invent the rest"** — the two facts found are exact quotes from the two pages that happen to state them; the other two pages were re-checked with the same rigor and genuinely say nothing more than what's already seeded.

---

## 4. Buy options

| Option | Assessment |
|---|---|
| **B0 — Defer geometry-for-all, let Conn proceed** | Fully defensible. The payoff of everything sourceable today is 3 text lines on 2 of 14 cards, zero new glyphs. If the Engineer weighs Fase 3 (Conn) product value higher than this, B0 costs nothing and loses nothing — the two new facts remain quoted in this report for whenever someone wants them. |
| **B1 — Narrow sourced text projection (recommended default lean)** | Add `standoff_height_mm` (a new, additive `FrameSpec` field, following the exact precedent of `wheelbase_mm`/`arm_thickness_mm`) to `tbs_source_one_v5_5in` (30mm/22mm) and `iflight_xl7_v4_7in` (25mm/32mm), threaded through `frame_part_specs_from_catalog`'s `_part()` call for `FRAME_STANDOFF_KEY` exactly the way `thickness_mm` already threads through for arms. Add a footprint fact for `iflight_xl7_v4_7in` (`body_length_mm`/`body_width_mm` = 202/202, or an equivalent honestly-named pair) — **exact target key is an open question for the IC** (frame root vs. a labeled plate-like entry; §5 flags this explicitly rather than silently picking one). **Text only — no glyph claimed or produced.** Small, additive, fully precedented schema cost; genuinely zero invention (every number is a direct quote, cited above). |
| **B1+ — Plate footprint "family"** | **Rejected as framed.** Only 1 of 4 rows (25%) has a stated body footprint — not enough to call this a family-wide capability without the other 3 rows reading as a conspicuous, explained absence on every card. If pursued, it should ship as the same per-row additive discipline as B1 above (one row gets it, three honestly don't), not a "family" feature — which is exactly what B1 already proposes. There is no separate B1+ worth buying beyond B1's own scope today. |
| **B2 — New glyph/schema shape** | **Rejected.** Nothing found today provides a complete shape input (a full box triple or a single diameter) for any currently-glyph-less node. A "footprint-only" 2D rectangle (L×W, no height) is the closest candidate a future cycle could consider *if* the Engineer wants to expand the glyph vocabulary for exactly this shape of partial data — not proposed here, since it would be a genuine new capability decision, not a data-sourcing one, and this IC's own stop condition forbids inventing a new glyph shape without dedicated justification. |

**Sensors (Here3) explicitly excluded from every option above** — per Locked Stance 6, no Buy is proposed for sensor geometry while identity stays frozen; flagged only, per §6.

---

## 5. Contingency sketch (if Engineer ★ Buys B1 — not an IC)

```text
FrameSpec (library.py): + standoff_height_mm: float | None = None   # single/first value if page lists ranges
                          (or a structured list mirroring `plates: list[PlateSeed]`,
                           if the IC wants to carry BOTH 25mm/32mm groups honestly —
                           a bare scalar would silently drop the second group)

frame_part_specs_from_catalog (catalog_bind.py):
  _part(FRAME_STANDOFF_KEY, "standoff", spec.standoff_count, spec.standoff_material,
        spec.standoff_height_mm)   # _part() already accepts a thickness_mm-shaped
                                    # positional slot; reuse or rename, IC's call

Board effect: frame_standoff's card gains a "standoff_height_mm" TEXT field
(via the existing generic `_fields()` property walk — zero Board code change).
No glyph. Refresh interaction: refresh_component_from_catalog("frame", ...)
already re-projects the WHOLE frame root via bind_frame_from_catalog(base=spec)
on the next cycle after this ships — no special-casing needed there, since a
frame refresh already picks up any newly-seeded field the same way it picked
up `wheelbase_mm`/`configuration` for the demo project during Fase 1's own
live verification.

Body footprint (iFlight only): target key is the OPEN question this sketch
deliberately does NOT resolve — attaching to `frame` root implies "the whole
frame's footprint," attaching to a labeled plate implies "just that plate's
footprint" — the page's own wording ("Body dimensions") reads more like the
former, but the IC author should confirm before locking a property name.
```

**This is illustrative only** — Cursor sizes and locks the exact field name(s), the one-vs-two-value standoff shape, and the footprint target key in a real IC.

---

## 6. Explicit non-goals honored / flags

- **Conn (Fase 3 mount-connect):** not opened, not Bought — named only as the alternative the Engineer may prefer over B1 (§4).
- **Fit / pose:** untouched. **Flag, not action:** the live re-fetch surfaced real mount-hole-pattern data for two frames (Armattan: 30.5mm center-stack + 28.5mm camera mount; iFlight XL7: 30.5×30.5mm and 20×20mm mounting holes) — this is precisely the category of evidence the earlier pose-B1+ investigation's own reversal criterion #1 named ("a manufacturer page that does publish a mounting-hole pattern... genuinely different from relative-assembly pose"). Not actioned here — flagged for whoever next revisits that Deferred investigation, since it's real, dated, sourced evidence they'll want.
- **CAD/FEA:** untouched.
- **Here3 / Pixhawk identity unfreeze:** not proposed. Sensors geometry stays entirely out of scope per Locked Stance 6 — flagged as a collision only (§4), no Buy recommended, no dims sourced or invented for Here3.
- **No number in this report is invented** — every dimension quoted in §3 is a direct, live-fetched quote from the cited manufacturer/retailer page; every "not stated" is a genuine negative finding from the same live fetch, not an assumption carried over from the archived `source_note` text.
- No code, schema, or test changed — `git status --short -- src/ tests/` is empty for this cycle.
