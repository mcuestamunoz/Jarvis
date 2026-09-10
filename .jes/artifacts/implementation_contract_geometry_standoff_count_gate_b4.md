# Implementation Contract — Standoff count gate for corner copies B4-min

**Project:** Jarvis  
**Date:** 2026-09-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTATION REVIEWED — **PASS WITH NOTES** · [review](implementation_review_geometry_standoff_count_gate_b4.md) · suite **2661**  
**Parents:**
- [Feature lock — Continuity spatial assembly](engineer_lock_continuity_spatial_assembly_feature.md)
- [Work order](engineer_next_geometry_loose_and_arms.md) — **B4** this · B3 corners **CLOSED** + ACCEPT @ **2652**
- [Corners B1 IC](implementation_contract_geometry_frame_standoff_corners_b1.md) — fixed `_STANDOFF_CORNER_COUNT = 4`; deferred declared count
- Catalog: `FrameSpec.standoff_count` → `frame_standoff.properties["count"]` via `frame_part_specs_from_catalog` (`catalog_bind.py`) when the seed sets it
- Live honesty: Rooster / most seeds leave `standoff_count` **unset** (page does not state piece count) — today B3 still paints ×4. **This Buy removes that default**

**Type:** Projector-only gate — read N from `frame_standoff.properties["count"]`; emit corner `solidCopies` / offsets **only** when N parses to **exactly 4** and existing Main Plate corner geometry gates hold.  
**Not** Continuity `declara standoff_count` grammar. **Not** N≠4 layouts (row / Engineer offsets). **Not** inventing Rooster count in library. **Not** quad-X / wheelbase. **Not** four BOM keys. **Not** Conversation Engine.

**Baseline:** package **`0.4.0`** · suite **2652** (confirm in report)

**Output:** `.jes/artifacts/implementation_report_geometry_standoff_count_gate_b4.md`

**Role lock:** **Claude implements** when Engineer ★ moves PRIORIDAD off drag investigation (or inserts this Buy).

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B4-min — standoff count gate** |
| 2 | Count source | **Only** `frame_standoff.properties["count"]` (already how catalog projects `FrameSpec.standoff_count`). Never re-open `library/` / `get_frame` inside the projector. Never `motor_count` / `quad_x` / `current_parameters` |
| 3 | Parse | Reuse `_parse_solid_copies_count` (whole number in `[2,16]`). Then require **`count == 4`**. Any other parsed N → **omit** copies+offsets |
| 4 | Missing / invalid | `count` absent, non-numeric, not in `[2,16]`, or ≠4 → **omit** (fail closed). **No default 4** — this deliberately supersedes B3’s unconditional 4 |
| 5 | Geometry / formula | Unchanged: `_frame_standoff_corner_offsets_mm` / `_main_plate_corner_points` (boxes + inset). Count gate is **additional** — helper still fails closed on mute/large standoff |
| 6 | Copies ↔ offsets | Same lockstep as B3: emit `solidCopies=4` iff corner helper returns 4 points **and** count gate passes; else both omit |
| 7 | BOM / cards | **One** `frame_standoff` forever |
| 8 | Continuity grammar | **Out** — no new `declara el standoff_count…`. Engineer / free-text / catalog bind must put `count` on the part when known |
| 9 | Library seeds | **Out** — do **not** invent `standoff_count: 4` on Rooster (page does not state it). Optional later ★ when a citation exists |
| 10 | N≠4 layouts | **Out** — separate Buy |
| 11 | `ui/` / version | No UI change required · **no** bump |

**Product sentence:**

```text
Solo si el standoff declara count=4 (catálogo o propiedad) y hay cajas
standoff + Main Plate, el visor pinta 4 pilares en esquinas. Sin count
o N≠4 → una caja (o ninguna copia), nunca inventar el 4.
```

**Not:**

```text
default 4 silencioso · declara Continuity de count · layout N=6/8 ·
seed inventado Rooster · estaciones motor 230 · Conversation Engine
```

**Live regression (named, accepted):**

```text
5min / Rooster today: frame_standoff often has material/height but NO count
→ after this Buy, corner ×4 disappears until count=4 is on the part
(e.g. free-text / future cited seed). Smoke must set count=4 explicitly.
```

---

## 1. You (Claude)

- Gate `_solid_copies` / `_frame_standoff_corner_offsets_mm` (or a thin shared reader) on `properties["count"]` → parse → `== 4`.
- Update comments that still say “fixed count of 4 this Buy” / “generalist standoff_count is a later Buy”.
- Prefer keeping `_STANDOFF_CORNER_COUNT = 4` as the **only allowed corner layout size** (not as a default when count is missing).
- Tests + report. Full pytest. Extend / replace corners suite rather than forking a second formula.
- Do **not** add Continuity declare grammar. Do **not** seed library counts. Do **not** implement N≠4 placement. Do **not** bump version / mutate `workspace/`.
- **STOP** if the only way to keep 5min green is inventing Rooster `standoff_count`.

---

## 2. Intent

```text
frame_standoff box + count=4 + frame_plate box
  → solidCopies=4 + corner offsets (same formula as B3)
frame_standoff box + count missing | count=6 | count=3
  → no solidCopies / no offsets
```

---

## 3. Tests

| ID | Behavior |
|---|---|
| P1 | Standoff box + Main Plate 100×100 + standoff 5×5 + **`count=4`** → `solidCopies==4`, offsets (±47.5, ±47.5, 0) |
| P2 | Same boxes, **`count` absent** → **no** `solidCopies` (regression vs B3 default — locked) |
| P3 | Same boxes, **`count=6`** (or 3) → no copies |
| P4 | `count=4` but missing standoff box or plate L×W → no copies |
| P5 | `count=4` but standoff larger than plate → no copies |
| P6 | Offsets still ≠ motors’ quad-X (W=230 present) |
| P7 | Exactly one `frame_standoff` node |
| P8 | Motors/props/arm/adapter copy regressions still green |

Update `tests/test_geometry_frame_standoff_corners_b1.py` **or** add `tests/test_geometry_standoff_count_gate_b4.py` that supersedes the old “no count needed” assumption — either way, B3’s P1 without `count` must **not** remain green.

---

## 4. Out of scope

Continuity declare for count · N≠4 row/offsets · invent seed counts · plate label noun · sourced #4 · Board drag→writers · Fit VERIFIED · Conversation Engine · version bump

---

## 5. Done when

- [ ] Count gate live; no default 4  
- [ ] Corner formula unchanged when gated  
- [ ] §3 tests green; full suite green  
- [ ] Report written; package still `0.4.0`  
- [ ] Engineer smoke: set `count=4` on 5min standoff (or accept single solid until then)

---

## 6. Handoff

```text
Claude  → implement + report
Cursor  → review vs this IC
Engineer → smoke (must supply count=4) / next ★
```
