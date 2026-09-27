# Implementation Contract — Standoff cylinder visor layout B1

**Project:** Jarvis  
**Date:** 2026-09-24  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Cursor** (Engineer “procede tu” 2026-09-24)  
**Reviewer:** independent Cursor pass still owed (same-session implementer ≠ review of record) · Engineer smoke on Taller (vigilancia MY5)

**Status:** IMPLEMENTED · **COLA** — Engineer 2026-09-24: dejar para más adelante; **hay que corregir puntos** (no ACCEPT). Independent review still owed.  
**Parents:**
- Engineer 2026-09-24: `count=8` on the card, **one** yellow cylinder in Taller — “hay que ampliar”
- [Standoff visor layout N≠4 B7](implementation_contract_geometry_standoff_layout_n_ne4_b7.md) **CLOSED** — N∈{4,6,8} perimeter, **box only**
- [Corners B1](implementation_contract_geometry_frame_standoff_corners_b1.md) **CLOSED** — inset `hx = Lp/2 − Ls/2`
- MY5 caliper bag — [engineer_bag_my5_caliper_2026_09_24.md](engineer_bag_my5_caliper_2026_09_24.md) — 8 × 30 mm × **Ø6** (cylinder, not a fake 6×6 box)
- `_geometry_from_spec` — Ø + H → `cylinder`; box still wins if L×W×H all present

**Type:** Projector-only. The existing 4/6/8 Main-Plate perimeter layout also accepts a **cylinder** standoff. Inset uses Ø as both footprint axes (`Ls = Ws = diameter_mm`). Glyph stays cylinder. **One** BOM card.  
**Not** inventing `length_mm`/`width_mm` on the catalog standoff. **Not** eight `ComponentSpec`s. **Not** disk-only posts. **Not** quad-X / wheelbase. **Not** C33. **Not** version bump.

**Baseline:** package **`0.5.30`** · suite confirm in report  
**Output:** `.jes/artifacts/implementation_report_geometry_standoff_cylinder_layout_b1.md`

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-standoff-cylinder-layout`** — cylinder posts use the same 4/6/8 perimeter as box posts |
| 2 | Count source | Unchanged: `frame_standoff.properties["count"]` via `_parse_solid_copies_count`; accepted set still **{4,6,8}** |
| 3 | Box path | **Byte-identical** — existing B7 / B4-min / corners tests stay green without fixture edits |
| 4 | Cylinder footprint | **Layout math only:** `Ls = Ws = diameter_mm`. Do **not** write `length_mm`/`width_mm` onto the spec or catalog |
| 5 | Glyph | `_geometry_from_spec` remains `cylinder` (Ø×H). Taller draws **N** cylinders, not N boxes |
| 6 | Formula | Same `hx`/`hy` as B7: `hx = Lp/2 − Ø/2`, `hy = Wp/2 − Ø/2`. `hx<0` or `hy<0` → omit (fail closed) |
| 7 | N=4 / 6 / 8 | Same point sets as B7 (corners; + long-edge mids; + four edge mids). Z=0 |
| 8 | Disk | Ø **without** axial H → disk → **omit** copies (a disk is not a post) |
| 9 | Missing plate box | Unchanged: omit if literal `frame_plate` is not a box |
| 10 | Copies ↔ offsets | Lockstep: `solidCopies == len(offsets)`; never one without the other |
| 11 | BOM | **One** `frame_standoff` card forever |
| 12 | UI | No required `ui/` change — `expandSolidCopies` is already key-agnostic (motors already copy cylinders) |
| 13 | Out | Catalog L×W fake square · GEP M3×6 thread trap · C33 · version bump · silent workspace rewrite |

**Product sentence:**

```text
Con count=8 y standoff cilindro Ø×H más placa main en caja, Taller
pinta ocho postes en el perímetro (esquinas + medios). Sigue siendo
una card. El Ø no se convierte en un cuadrado en el catálogo.
```

### 0.1 MY5 fixture (live desk)

```text
frame_plate: 161 × 42 × 2  (box, assembly root)
frame_standoff: Ø6 × H30, count=8  (cylinder)
hx = 161/2 − 6/2 = 77.5
hy =  42/2 − 6/2 = 18.0
N=8 points:
  corners: (±77.5, ±18.0, 0)
  mids:    (±77.5, 0, 0) and (0, ±18.0, 0)
```

---

## 1. You (implementer)

- In `_frame_standoff_layout_offsets_mm`, after `_geometry_from_spec`:
  - `shape == "box"` → pass that dict to the existing corner/mid helpers (unchanged).
  - `shape == "cylinder"` → build a **local** footprint `{length_mm: diameter_mm, width_mm: diameter_mm}` and pass **that** to the same helpers. Do not mutate the spec.
  - anything else (disk / None) → `None` (omit).
- Keep `_main_plate_corner_points` / `_standoff_perimeter_midpoints_mm` box-key contracts (`length_mm`/`width_mm`). Do not teach them `diameter_mm`.
- Comments that say “standoff must be a box” → “box, or cylinder using Ø as both axes”.
- New tests: `tests/test_geometry_standoff_cylinder_layout_b1.py`. Do **not** weaken B7 box tests.
- Extend MY5 sourced test: after rebind-style project, `frame_standoff` has `geometry.shape == "cylinder"` **and** `solidCopies == 8` with the §0.1 point set.
- **STOP** if the only way to green is writing L×W onto the standoff seed.

---

## 2. Intent

```text
count=8 + cylinder Ø×H + Main Plate box → 8 cylinder copies on perimeter
count=4/6 + cylinder → same perimeter rules as box
count=8 + box → unchanged
Ø without H (disk) → no copies
Ø larger than plate → no copies
```

---

## 3. Locked behavior

| Input | Result |
|---|---|
| MY5: plate 161×42 box + standoff Ø6×30 cylinder + `count=8` | `solidCopies==8`; glyph cylinder; points §0.1 |
| Box 5×5 + plate 100×100 + `count=8` | Unchanged B7: 8 pts @ 47.5 insets |
| Cylinder Ø6 + plate 161×42 + `count=4` | 4 corners `(±77.5, ±18, 0)` |
| Cylinder Ø50 + plate 42-wide | omit (`hy < 0`) |
| Disk Ø6 (no H) + `count=8` + plate box | omit |
| No `frame_plate` box | omit |

---

## 4. Tests (minimum)

| ID | Assert |
|---|---|
| P1 | MY5 fixture §0.1 → `solidCopies==8`, shape `cylinder`, point set matches |
| P2 | B7 box `count=8` 100×100 / 5×5 still 8 pts @ 47.5 (regression; may live in existing file) |
| P3 | Cylinder `count=4` → 4 corners only |
| P4 | Oversized Ø vs plate width → no copies |
| P5 | Disk (Ø, no H) → no copies |
| P6 | Exactly one `frame_standoff` node |
| P7 | Offsets ≠ quad-X stations when wheelbase=225/230 present |
| P8 | Full suite green; B7 / B4-min / corners / MY5 bind tests unchanged except P1 addition |

---

## 5. Files

| Path | Action |
|---|---|
| `src/jarvis/workspace/spatial_board.py` | cylinder footprint branch in `_frame_standoff_layout_offsets_mm` |
| `tests/test_geometry_standoff_cylinder_layout_b1.py` | write |
| `tests/test_geometry_sourced_frame_hglrc_my5_b1.py` | add `solidCopies==8` + point set on projected MY5 |
| `docs/IMPLEMENTATION_TASKS.md` | PRIORIDAD sync after report |
| `.jes/state/engineering_state.json` | sync after report |
| `.jes/artifacts/implementation_report_geometry_standoff_cylinder_layout_b1.md` | write |
| `library/` / `ui/` / version / C33 | **no** |

---

## 6. Smoke (Engineer, ~3 min)

On **dron de vigilancia doméstico** (already rebound MY5; standoff card shows count 8, Ø6, H30):

1. Reload Taller — **eight** yellow cylinders on the Top-plate perimeter (corners + edge mids), not one pill in the spare row.
2. Inspector still **one** `frame_standoff` card, count 8.
3. Motors/props X unchanged.
4. Box-standoff projects (if any) still 4/6/8 as before.

---

## 7. Out of scope (separate ★)

- Fake 6×6×30 box in catalog  
- Per-post Continuity offsets  
- Disk posts  
- Bottom-plate L×W  
- FC estimated-H writer  
- C33 ScriptedSpi  

---

## 8. ★

Default if you say `procede` / ★ without override: **this draft** (Ø as both inset axes, box path untouched).
