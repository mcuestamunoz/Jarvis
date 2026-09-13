# Implementation Contract — Standoff visor layout N≠4 (B7 / 6·8 perimeter)

**Project:** Jarvis  
**Date:** 2026-09-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Cursor (this chat) or Claude — Engineer picks  
**Reviewer:** Cursor against this IC after the edit · Engineer smoke

**Status:** **CLOSED** — smoke **ACCEPT** ([smoke](engineer_smoke_geometry_standoff_layout_n_ne4_b7.md)) · [review](implementation_review_geometry_standoff_layout_n_ne4_b7.md) PASS WITH NOTES · suite **2697** · Option **A**  
**Parents:**
- Work order **B7** — [engineer_next_geometry_loose_and_arms.md](engineer_next_geometry_loose_and_arms.md)
- [Standoff count gate B4-min](implementation_contract_geometry_standoff_count_gate_b4.md) **CLOSED** @ **2661** — N≠4 omit
- [Corners B1](implementation_contract_geometry_frame_standoff_corners_b1.md) **CLOSED** + ACCEPT @ **2652** — N=4 formula
- [IDLE frame-part count declare B1](implementation_contract_idle_frame_part_count_declare_b1.md) — review PASS @ **2686**; sets `count` without LLM
- Feature lock — [Continuity spatial assembly](engineer_lock_continuity_spatial_assembly_feature.md)

**Type:** Projector-only — extend `frame_standoff` `solidCopies` / `solidCopyOffsetsMm` so declared **N=6** and **N=8** place posts on the Main Plate footprint (perimeter), while **N=4** keeps today’s corners. Still **one** BOM card.  
**Not** Continuity per-post offset declare. **Not** arbitrary N row (propeller pattern). **Not** inventing Rooster `standoff_count`. **Not** quad-X / wheelbase. **Not** Conversation Engine. **Not** version bump.

**Baseline:** package **`0.4.1`** · suite **2686** → **2697** · UI **83**

**Output:** `.jes/artifacts/implementation_report_geometry_standoff_layout_n_ne4_b7.md`  
**Review:** `.jes/artifacts/implementation_review_geometry_standoff_layout_n_ne4_b7.md`  
**Smoke:** `.jes/artifacts/engineer_smoke_geometry_standoff_layout_n_ne4_b7.md`

---

## 0. Engineer Buy (proposed locks — ★ on this table)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B7-min — perimeter layout for N=6 and N=8** |
| 2 | Count source | Unchanged: only `frame_standoff.properties["count"]` via `_parse_solid_copies_count` (`[2,16]`) |
| 3 | N=4 | **Unchanged** — `_main_plate_corner_points` / current B4-min path |
| 4 | N=6 | **4 corners + 2 midpoints of the longer Main Plate edges** (see §0.1). Z=0. Same inset `hx`/`hy` as corners |
| 5 | N=8 | **4 corners + 4 mid-edge points** `(±hx,0)` and `(0,±hy)`. Z=0 |
| 6 | Other N | `count` missing / invalid / in `[2,16]` but **not** in `{4,6,8}` → **omit** copies+offsets (fail closed — same honesty as B4-min for N=3,5,7,…) |
| 7 | Geometry gates | Same as corners: standoff box + literal `frame_plate` box + `hx≥0`/`hy≥0`. Fail → omit |
| 8 | Copies ↔ offsets | Lockstep: `solidCopies == len(offsets)`; never emit one without the other |
| 9 | BOM / cards | **One** `frame_standoff` forever |
| 10 | Continuity / library / ui | No new declare grammar · no seed invent · no required `ui/` change · **no** version bump |
| 11 | Rejected alternatives (unless Engineer overrides before ★) | Plain **row** of N (propeller pattern) · Engineer-typed per-post offsets · inventing N from `motor_count` / `quad_x` |

**Product sentence:**

```text
Con count=4, seis o ocho y cajas standoff + Main Plate, el visor pinta
ese número de pilares en el perímetro del sandwich (esquinas; +medios
en lados largos para 6; +cuatro medios para 8). Una card. Otros N:
sin copias, no inventar.
```

**Not:**

```text
fila de 6 como hélices · offsets Continuity por poste · seed Rooster ·
estaciones motor 230 · Conversation Engine
```

### 0.1 Formula (Main Plate axes L→+X, W→+Y)

Reuse corner inset:

```text
hx = Lp/2 − Ls/2
hy = Wp/2 − Ws/2
if hx < 0 or hy < 0 → omit
```

**Corners (always included for N∈{4,6,8}):**

```text
(+hx,+hy), (+hx,−hy), (−hx,−hy), (−hx,+hy)
```

**N=6 midpoints** — on the **longer** plate edges (if `Lp >= Wp`, long edges are constant `±hy`; else constant `±hx`):

```text
if Lp >= Wp:  (0,+hy), (0,−hy)
else:         (+hx,0), (−hx,0)
```

**N=8 midpoints** — all four edge centers:

```text
(+hx,0), (−hx,0), (0,+hy), (0,−hy)
```

Index order: corners first (FR/FL/RL/RR as today), then midpoints in the order written above. Document actual order in the report; tests assert set-equality of points (and `solidCopies` count), not Scene3D paint order.

---

## 1. You (implementer)

- Extend `_frame_standoff_corner_offsets_mm` **or** rename/split into a shared `_frame_standoff_layout_offsets_mm` that branches on parsed count `{4,6,8}`; keep N=4 byte-faithful to current points.
- `_solid_copies` for `frame_standoff` must return that same N when the helper succeeds (not hardcode 4).
- Update comments that still say “only N=4 / omit otherwise”.
- Prefer extending `tests/test_geometry_standoff_count_gate_b4.py` (or new `tests/test_geometry_standoff_layout_n_ne4_b7.py`) — keep P2/P3 honesty for absent/N=3; **change** former “count=6 → no copies” into “count=6 → 6 perimeter points”.
- Do **not** touch IDLE bridge / aerial extract / library seeds / version.
- **STOP** if the only way to green is inventing Rooster count or using wheelbase/quad-X math.

---

## 2. Intent

```text
count=4 + boxes → solidCopies=4 + corner offsets          (unchanged)
count=6 + boxes → solidCopies=6 + corners + 2 long-edge mids
count=8 + boxes → solidCopies=8 + corners + 4 edge mids
count missing | 3 | 5 | 7 | … → no solidCopies
```

---

## 3. Locked behavior (match / no-match)

| Input | Result |
|---|---|
| Standoff 5×5 + Main Plate 100×100 + `count=4` | 4 pts @ `(±47.5,±47.5,0)` |
| Same + `count=6` | 6 pts: those 4 + `(0,±47.5,0)` because Lp=Wp → treat as `Lp>=Wp` branch |
| Same + `count=8` | 8 pts: 4 corners + `(±47.5,0,0)` + `(0,±47.5,0)` |
| Plate 120×80 + standoff 5×5 + `count=6` | corners with hx=57.5, hy=37.5 + mids `(0,±37.5)` (Lp>Wp) |
| `count=3` or absent | no copies |
| Standoff larger than plate | omit |
| No `frame_plate` box | omit |

Tie-break when `Lp == Wp`: use the `Lp >= Wp` branch (mids on `±hy`) — locked above for the 100×100 fixture.

---

## 4. Tests (minimum)

| ID | Assert |
|---|---|
| P1 | `count=4` regression — same points as B4-min / corners |
| P2 | `count` absent → no copies |
| P3 | `count=3` → no copies |
| P4 | `count=6` + 100×100 / 5×5 → `solidCopies==6`; point set = corners ∪ `{(0,±47.5,0)}` |
| P5 | `count=8` + same → `solidCopies==8`; corners ∪ edge mids |
| P6 | `count=6` + Lp>Wp fixture → long-edge mids on `±hy` |
| P7 | `count=6` + Wp>Lp fixture → long-edge mids on `±hx` |
| P8 | Fail-closed: oversized standoff / missing plate |
| P9 | One `frame_standoff` node; motors/props/arm/adapter X regressions green |
| P10 | Offsets still ≠ quad-X stations when W=230 present |

---

## 5. Files

| Path | Action |
|---|---|
| `src/jarvis/workspace/spatial_board.py` | layout branch 6/8 + `_solid_copies` return N |
| `tests/test_geometry_standoff_layout_n_ne4_b7.py` and/or update gate suite | write / adjust |
| `docs/IMPLEMENTATION_TASKS.md` | PRIORIDAD sync after report |
| `.jes/state/engineering_state.json` | sync after report |
| `.jes/artifacts/implementation_report_geometry_standoff_layout_n_ne4_b7.md` | write |
| IDLE / aerial / library / ui / version | **no** |

---

## 6. Smoke (Engineer, ~5 min)

On `autonomía-de-5min` (Main Plate + standoff boxes):

1. IDLE `6 standoffs` → card count 6 → Board shows **6** posts on plate perimeter (not a lonely tiny box).  
2. IDLE `8 standoffs` → **8** posts (corners + mid-edges).  
3. IDLE `4 standoffs` → **4** corners only (regression).  
4. IDLE `3 standoffs` → no copies (honesty).  
5. Motors/props X unchanged.

---

## 7. Out of scope (separate ★)

- Continuity `declara offset del standoff…` / per-post Engineer offsets  
- Row fallback for arbitrary N  
- N=5/7/9… perimeter heuristics  
- Rooster / catalog `standoff_count` seed  
- Sourced dims #4 · LLM pending deactivate · C-114 · version bump  
- Platform Capability Vision packages

---

## 8. Open for Engineer before ★ (if you disagree)

Reply with one override if needed:

- **A (this draft):** perimeter 6/8 as §0  
- **B:** propeller-style **row** for any N≠4 in `[2,16]` (no plate placement)  
- **C:** N=6/8 only after you dictate a different mid-edge rule  

Default if you say `procede` / ★ without override: **A**.
