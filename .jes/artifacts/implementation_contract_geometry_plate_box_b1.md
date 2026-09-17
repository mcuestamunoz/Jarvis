# Implementation Contract — Main-plate box / assembly root (`B1-plate-box`)

**Project:** Jarvis  
**Date:** 2026-09-13  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — **only after** Engineer ★ **and** §0.1 bag filled (or Path D fixture lock)  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** B0 HOLD historically · **REOPENED awaiting bag** (Engineer dual-track 2026-09-15) — fill §0.1 + ★ path C/D/E before Claude implements. Parallel: [disk-station B0](investigation_contract_disk_station_fit_attest_b0.md). See [dual-track note](engineer_note_dual_track_plate_box_disk_station.md).  
**Parents:**
- [investigation_contract_board_drone_default_layout_b0.md](investigation_contract_board_drone_default_layout_b0.md) · [report](investigation_report_board_drone_default_layout_b0.md) · [review PASS](investigation_review_board_drone_default_layout_b0.md) — lean: plate-box **after** mount-assist  
- Mount standard assist B1 — [review PASS](implementation_review_mount_standard_assist_b1.md) · smoke may still be pending  
- Visor assembly root **already shipped:** `ASSEMBLY_ROOT_ID = "frame_plate"` when geometry is a **box** (`ui/spatial-board/src/scene3dLayout.ts`)  
- Declared plate L×W Continuity **already shipped:** [declared battery + Main Plate envelope B1](implementation_contract_geometry_declared_battery_plate_envelope_b1.md) **CLOSED** — IDLE declare merges `length_mm`/`width_mm`/`height_mm` on `frame_plate*`  
- #4g GEP-Racer body 175×173 — **not** plate L×W ([#4g IC](implementation_contract_geometry_sourced_frame_gep_racer_b1.md) photo lock)  
- #4g-A CAD — **CLOSED B0** empty OEM CAD ([report](investigation_report_geometry_gep_racer_part_cad_b0.md)) · Option B caliper deferred  

**Type:** Unlock assembly root by putting an **honest** L×W (and H) on **`frame_plate`** — prefer existing Continuity declare; optional catalog/project seed **only** if bag + ★ say so.  
**Not** inventing from body 175×173 / wheelbase 208. **Not** stack-rule Δmm. **Not** layout pack. **Not** subject-vocab widen. **Not** Situar UX. **Not** Conversation Engine. **Not** version bump. **Not** silent `workspace/` mutation unless Engineer ★ Path D apply.

**Output:** `.jes/artifacts/implementation_report_geometry_plate_box_b1.md`  
**If bag stays empty after ★ attempt:** close as **B0 hold** — report gap; no dims.

**Cola after:** `B1-stack-rule` → `B1-layout-pack-cited` → silueta · [cola](engineer_note_board_situar_work_cola.md)

**Checkpoint:** package **`0.4.1`** · suite ≥**2763** · UI ≥**99**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-plate-box`** — `frame_plate` becomes a **box** → assembly root at world 0 activates (code already there) |
| 2 | Authority | **Only** §0.1 numbers: Option B caliper · OEM/cited drawing · or Engineer-disclosed fixture for Path D tests/smoke (**label honesty** in copy) |
| 3 | Forbidden sources | Body `175×173` · wheelbase · photo pixel-scale · invent · Yeggi/random STL as SoT |
| 4 | Key | Exactly **`frame_plate`** (Main / first plate). **Not** `frame_plate_2` as root. Other plates may get boxes later under a separate ★ |
| 5 | Height | Prefer existing `thickness_mm` → `height_mm` when utterance omits H (same rule as declared-envelope B1). Do not delete thickness |
| 6 | Apply path (pick one in ★) | **Path C — Continuity live:** Engineer types existing declare phrase on 5min and/or 15min (Claude: tests + report only; **no** workspace edit). **Path D — Fixture/regression:** Claude adds/extends tests with §0.1 fixture mm proving Continuity parse → box → root gate; still no invent. **Path E — Catalog seed:** only if schema already allows plate L×W on `PlateSeed` / bind **and** bag is Class A cited — **STOP and ask** if schema add is required |
| 7 | Root claim | After apply, Board 3D: `frame_plate` box centered at world origin; posed children can use it as origin. Copy must **not** claim stack-rule or “situate by dimension” pack |
| 8 | Out | Auto-pose · stack-rule · layout pack · arm L×W (unless same bag + separate line in §0.1 and ★) · version bump · LLM invent |

**Product sentence:**

```text
Con L×W honestos de la placa main (calibre o cita), declaro la caja;
Jarvis ya sabe poner esa placa en el origen del ensamblaje. No inventa
175×173 ni apila sola el stack.
```

### 0.1 Citation / caliper bag — **Engineer fills before implement**

```text
### frame_plate (Main) L×W — EMPTY until cited / measured
authority: caliper Option B | OEM drawing | Engineer fixture (disclose)
source_url_or_method:
part: Main / Bottom / Top / Aluminum — which Continuity key? → frame_plate
measured_mm:
  length_mm: ?
  width_mm: ?
  height_mm: ?   # or “use thickness_mm already on spec”
identity_status: measured | verified | fixture_disclosed
re-fetch_or_measure_date:
projects_to_apply: autonomía-de-5min | autonomía-15min | both | none (tests only)
path_star: C | D | E
```

Paste one filled bag under ★. Empty bag after search/measure attempt → **B0 hold**, no code invent.

**Rejected without override:**

| Source | Why |
|---|---|
| GEP page Dimensions 175×173 | Outer airframe envelope ≠ central plate ([#4g lock](implementation_contract_geometry_sourced_frame_gep_racer_b1.md)) |
| Wheelbase 208 | Diagonal motor–motor |
| Estimating from ESC/FC footprint | Not plate carbon |

---

## 1. You (Claude) — after ★ + filled bag

1. Confirm `parse_declared_envelope_declare` + `set_component_declared_box_envelope` still accept the §0.1 phrase shape for `frame_plate` (extend tests if a hole appears).  
2. Confirm Scene3D root gate still: `frame_plate` + `shape === "box"` → world 0 (existing `scene3dLayout` tests U10/U13 — do not weaken).  
3. Path C: write Continuity example phrases in the report; **do not** edit `workspace/` unless Engineer explicitly ★ workspace apply in this Buy.  
4. Path D: fixture mm from bag only; disclose `fixture_disclosed` in test names/comments.  
5. Path E: only if ★ and schema already supports — else STOP.  
6. Do **not** touch Situar UX, mount-standard-assist, pose auto, stack-rule.  
7. Do **not** bump version.  
8. Report out; package stays `0.4.1`.

**STOP if** the only way to get numbers is copying 175×173 or inventing.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | Phrase / writer path yields `length_mm`+`width_mm`(+H) on `frame_plate` with `source=declared` (or catalog if Path E) |
| T2 | Projector/`_geometry_from_spec` (or Board DTO) exposes `shape: box` for that plate |
| T3 | `layoutSolidsFromPose`: `frame_plate` box → origin at world 0; `frame_plate_2` box alone does **not** become root |
| T4 | Body/wheelbase values must **not** appear as plate L/W in any new seed (if Path E) |
| T5 | Full pytest green; package `0.4.1` |

---

## 3. Smoke (Engineer)

1. On target live project(s): after declare (Path C) or bind (Path E), open Board 3D — Main plate box at center / world 0.  
2. Pose one avionics box `respecto` `frame_plate` — sits relative to plate, not sibling cycle-only.  
3. Confirm copy nowhere claims auto-stack or verified CAD if authority was caliper/fixture.  
4. Re-open mount checklist — unrelated; plate box is orthogonal.

---

## 4. Out of scope

`B1-stack-rule` · `B1-layout-pack-cited` · arm/standoff envelopes · invent plate · Situar · version bump · HD-005

---

## 5. Done when

- [ ] §0.1 bag filled + ★ path chosen  
- [ ] T1–T5 (as applicable to path) + report  
- [ ] Engineer smoke ACCEPT  
- [ ] Or honest **B0 hold** report if bag empty  

---

## 6. Handoff

```text
Engineer → fill §0.1 + ★ path C/D/E (or B0 hold)
Cursor   → (this IC; review after code if any)
Claude   → implement only with bag + ★; else stop
Engineer → smoke §3
```
