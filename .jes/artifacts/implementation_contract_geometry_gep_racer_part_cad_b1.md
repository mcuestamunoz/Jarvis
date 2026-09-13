# Implementation Contract — #4g-A GEP-Racer part envelopes from CAD (plates / arms / standoff Ø)

**Project:** Jarvis  
**Date:** 2026-09-11  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Cursor / Claude — after Engineer ★ **and** §0.1 CAD bag filled  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** **CLOSED B0** (2026-09-11) — Phase 0 empty CAD bag · [investigation report](investigation_report_geometry_gep_racer_part_cad_b0.md) · [review](investigation_review_geometry_gep_racer_part_cad_b0.md) **PASS** · Option B caliper deferred  
**Parents:**
- [implementation_contract_geometry_sourced_frame_gep_racer_b1.md](implementation_contract_geometry_sourced_frame_gep_racer_b1.md) — **#4g P1** partial catalog seed (body 175×173 · wb 208 · thicknesses · H24) — orthogonal; may ★/land first  
- Engineer 2026-09-11 honesty lock: plate/arm L×W UNKNOWN · standoff Ø UNKNOWN · do not copy 175×173 onto plates · do not read M3×6×24 as Ø6  
- [engineer_lock_sourced_envelope_to_3d.md](engineer_lock_sourced_envelope_to_3d.md) ★ LOCKED  

**Type:** Cite authentic CAD → measure bounding L×W (and standoff OD) → **declared** project envelopes and/or catalog enrichment **only if** schema already allows.  
**Not** Yeggi/Printables random STLs as SoT. **Not** inventing L×W. **Not** `geometry_level` schema. **Not** Rooster. **Not** version bump.

**Baseline:** package **`0.4.1`** · suite **≥2718** · UI **83**

**Output:** `.jes/artifacts/implementation_report_geometry_gep_racer_part_cad_b1.md`  
**If CAD absent:** `.jes/artifacts/investigation_report_geometry_gep_racer_part_cad_b0.md` (gap holds → handoff **Option B** caliper)

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Path | **Option A** — prefer authentic CAD/STEP/STL over caliper (**B**) |
| 2 | Goal | Fill UNKNOWN: Top/Bottom/Alu plate **L×W** · Arm **L×W** · Standoff **outer Ø or section** |
| 3 | Authority | Only files Engineer accepts as **OEM / licensed / manufacturer-linked**. Community camera-mount STLs ≠ frame plates |
| 4 | Pre-check (2026-09-11) | `https://geprc.com/downloads/racer/` — **empty** (“nothing for the time being”). Product + parts pages: **no** STEP/STL download. Printables hit = camera mount only — **out** |
| 5 | Apply surface | Prefer **project declared** `length_mm`/`width_mm`/`height_mm` on `frame_plate*` / `frame_arm` / `frame_standoff` after #4g bind. **STOP** before adding `PlateSeed.length_mm` schema unless Engineer ★ a separate schema Buy |
| 6 | Bounding box honesty | CAD → AABB / engineer-stated print dims only; disclose “bounding box of QR arm, not solid rectangle” in note |
| 7 | Fallback | If §0.1 bag stays empty after search → **close A as B0 gap** · Engineer opens **Option B** (caliper) — no invent |
| 8 | Out | Scraping Yeggi as SoT · estimating from wheelbase · Ø6 invent · Conversation Engine · version bump |

**Product sentence:**

```text
Si GEPRC (u OEM) publica CAD del GEP-Racer, mido L×W de placas/brazos
y Ø de columna y lo declaro en el Board. Si no hay CAD auténtico, no invento;
paso a calibre.
```

### 0.1 CAD citation bag — **Engineer fills before implement**

```text
### CAD / STEP / STL — EMPTY until cited
source_url:
file_type: STEP | STL | DXF | …
authenticity: OEM GEPRC | distributor with Engineer ★ | other (describe)
parts covered: top_plate | bottom_plate | aluminum_plate | arm | standoff | …
measured (from CAD, mm):
  top_plate:    L=?  W=?  H=2.0 (H already catalog)
  bottom_plate: L=?  W=?  H=2.0
  aluminum:     L=?  W=?  H=2.0
  arm:          L=?  W=?  H=5.0
  standoff:     OD=? or L×W=?  H=24
method: bounding-box / sketch dims / other
re-fetch date:
```

Paste one bag. Empty after diligent search = **A fails closed** → B.

**Rejected without Engineer override:**

| Source class | Why |
|---|---|
| Yeggi / random “GEP Racer” dumps | Provenance unknown |
| Printables camera mount (Caddx Vista) | Wrong part |
| Photo pixel-scale of marketing render | Not Class A |

---

## 1. You (implementer)

### Phase 0 — find or STOP (no ★ required to *search*; ★ required to *seed from file*)

1. Re-check GEPRC downloads / product / parts / support.  
2. Ask Engineer if they hold a private OEM pack.  
3. If nothing authentic → write **investigation report B0** (gap holds) · sync PRIORIDAD to Option B · **do not invent**.  

### Phase 1 — only after §0.1 bag + ★

1. Open cited file; measure dims; disclose method.  
2. After #4g SKU exists on 5min: write **declared** envelopes on the matching children (P1 clear already done).  
3. Tests: declared L×W present; catalog `plates[]` still thickness-only unless schema Buy ★; Rooster untouched; no Ø6 invent.  
4. Full suite green. Report.

**STOP** if the only path is guessing from 175×173 or wheelbase.

---

## 2. Intent

```text
Engineer chooses CAD path (A)
        ↓
Phase 0: authentic CAD? 
   no → B0 report → Option B caliper
   yes → §0.1 bag + ★
        ↓
measure AABB L×W / OD
        ↓
declared on 5min frame children (post #4g)
        ↓
Board boxes for plates/arms/posts
```

---

## 3. Tests (minimum) — Phase 1 only

| ID | Assert |
|---|---|
| T1 | Cited CAD URL/path recorded in report + `source_note` / declare assist provenance |
| T2 | Top/Bottom (and Alu if covered) have declared L×W matching bag (±tolerance disclosed) |
| T3 | Arm has declared L×W or honest omit if CAD arm not in pack |
| T4 | Standoff OD/section only if CAD states it — never from “×6×” alone |
| T5 | Catalog `PlateSeed` still has no invented L×W fields unless separate schema Buy |
| T6 | `armattan_rooster_5in` unchanged |

---

## 4. Files (expected)

| Path | Action |
|---|---|
| Phase 0 report **or** Phase 1 report | write |
| 5min `state.json` | declared plate/arm/standoff envelopes (Phase 1) |
| `tests/test_geometry_gep_racer_part_cad_b1.py` | Phase 1 |
| `library/frames/_datos.json` | **only** if #4g already landed and a *cited* note update is needed — no fake L×W in `plates[]` |
| PlateSeed schema L×W | **no** unless Engineer ★ separate Buy |
| ui / version | **no** |

---

## 5. Smoke (Engineer) — Phase 1

On `autonomía-de-5min` after #4g + CAD declare: plate/arm solids match CAD bag; envelope 175×173 / wb 208 unchanged; no fantasy Ø6 posts.

---

## 6. Out of scope

#4g P1 seed itself (separate IC) · motor T3 · user catalog contribution · Conversation Engine

---

## 7. Handoff

```text
Engineer → ★ this IC as process lock for Option A
         → either paste CAD bag OR authorize Phase 0 search then report
Cursor/Claude → Phase 0 search / Phase 1 implement
Cursor → review
Engineer → smoke (Phase 1) or accept B0 → open Option B caliper IC
```

**Relation to #4g:** ★ and land **#4g P1** anytime (partial kit). This IC fills XY only when CAD exists.
