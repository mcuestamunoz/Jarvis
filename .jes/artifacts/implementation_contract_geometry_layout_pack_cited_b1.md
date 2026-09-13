# Implementation Contract — Cited kit layout pack B1 (`B1-layout-pack-cited`)

**Project:** Jarvis  
**Date:** 2026-09-13  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — only after Engineer ★ **and** §0.1 table filled  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** READY FOR ★ — **§0.1 FILLED** (Engineer Path F smoke 2026-09-13 on `10-min-autonomía` + MY5). Claude may implement after ★.  
**Parents:**
- [investigation_report_board_drone_default_layout_b0.md](investigation_report_board_drone_default_layout_b0.md) §D/§E · [review](investigation_review_board_drone_default_layout_b0.md)  
- Continuity spatial ★ — [feature lock](engineer_lock_continuity_spatial_assembly_feature.md) — no silent auto-pose  
- Pose writer CLOSED — `set_component_declared_box_pose`  
- Mount-standard-assist B1 · [Path F craft montage](implementation_contract_geometry_craft_montage_path_f_b1.md) **LANDING** (flush z formula)  
- [cola](engineer_note_board_situar_work_cola.md) #4 · [montage lock](engineer_lock_craft_montage_honest_reproducible.md)  

**Type:** Named **kit layout pack** — a disclosed table of poses (and optional mounts) for a cited kit; suggest → user confirms via **existing** Continuity writers.  
**Not** inventing mm. **Not** silent apply on Board load. **Not** inventing arm radial beams / motor disk poses (Visor X owns those). **Not** plate L×W invent. **Not** silhouette polish. **Not** Conversation Engine. **Not** version bump.

**Output:** `.jes/artifacts/implementation_report_geometry_layout_pack_cited_b1.md`  

**Cola after:** Silhouette Product B · [IC](implementation_contract_board_silhouette_product_b_b1.md)

**Checkpoint:** package **`0.4.1`** · suite ≥**2813** · UI ≥**99**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-layout-pack-cited`** — pack_id **`hglrc_my5_flush_stack_b1`** (first kit; format reusable for GEP later) |
| 2 | Authority | §0.1 rows only — here: **Engineer-confirmed Path F flush** on estimated plate (not OEM CAD, not caliper XY). Disclose as supuesto flush in copy |
| 3 | Forbidden | Invent XY · invent from body 225×200 · LLM · “typical freestyle” without a row · disk origins for motors/props |
| 4 | Apply | Suggest-only IDLE: `layout pack` / `aplicar layout hglrc_my5_flush_stack_b1` (document exact triggers). Confirm = **retype** |
| 5 | Writers | Reuse only `set_component_mounted_on` / `set_component_declared_box_pose` |
| 6 | Origins | Pose origins must be **box** — here `frame_plate` only |
| 7 | Prerequisites | `requires_plate_box: yes` — skip honestly if no plate box |
| 8 | Out | Arm radial-to-plate Buy · Visor X changes · Product B claim · version bump · `workspace/` unless ★ apply-live |

**Product sentence:**

```text
Con una tabla citada o medida del kit, Jarvis me propone el pack de poses
(y montajes) con la frase exacta; yo confirmo. Sin tabla, no inventa.
```

### 0.1 Layout table — **FILLED** (2026-09-13)

```text
### pack_id: hglrc_my5_flush_stack_b1
kit_frame_sku: hglrc_my5_5in
authority: Engineer-confirmed Path F flush (supuesto) on estimated_temporary plate
source_url_or_method: >
  Same arithmetic as B1-craft-montage-path-f:
  x=0, y=0, z = H_plate/2 + H_child/2.
  Engineer smoke 2026-09-13 on project 10-min-autonomía (plate 120×55×2 estimated;
  child H from live boxes: FC 7.8, ESC 8.0, battery 29.0, sensors 14.4).
  NOT OEM drawing / NOT caliper XY / NOT “verified CAD”.
requires_plate_box: yes
rows:
  # subject_key | origin_key | x_mm | y_mm | z_mm | also_set_mounted_on? | note
  flight_controller | frame_plate | 0 | 0 | 4.9 | yes→frame_plate | Path F flush; H_fc=7.8
  esc               | frame_plate | 0 | 0 | 5.0 | yes→frame_plate | Path F flush; H_esc=8.0
  battery           | frame_plate | 0 | 0 | 15.5 | yes→frame_plate | Path F flush; H_bat=29
  sensors           | frame_plate | 0 | 0 | 8.2 | yes→frame_plate | Path F flush; H_sens=14.4
# EXPLICITLY NOT IN PACK (other mechanisms / no cited data):
# motors, propellers — Visor X from wheelbase (not Continuity disk pose)
# frame_arm — Visor X station boxes; radial-beam-to-plate = separate Buy
# frame_plate_2/3 — no L×W yet
# power_connector, signal_harness, prop_adapter — no box geometry
identity_status: fixture_disclosed
measure_or_cite_date: 2026-09-13
path_star: suggest_retype
live_apply: none
# optional Engineer smoke targets after implement: 10-min-autonomía | autonomía-de-5min
```

**Honesty lock for Claude copy:** every proposal line must say the pack is **flush supuesto / Path F formula**, not measured kit CAD. If live child heights differ from the bag, **recompute z from live envelopes with the same formula** OR skip with reason — do **not** force stale z against different H (prefer: compute z at propose-time from formula + live boxes, and treat §0.1 as the worked example / regression fixture numbers).

---

## 1. You (Claude) — after ★

1. Pure module (e.g. `layout_pack_assist.py`): register pack `hglrc_my5_flush_stack_b1` from §0.1 (code or JSON — numbers only from bag / formula).  
2. Prefer **formula-at-propose-time** for z when subject+plate boxes exist (matches Path F); use §0.1 floats as test fixture expectations for the 10min-shaped dims.  
3. IDLE trigger → list pose phrases + mount phrases (`… montado en frame_plate`); skip if plate missing / subject missing / origin not box.  
4. Confirm = retype into existing bridges (pose + mount). List-alone never writes.  
5. Tests T1–T5. Full suite green. Report.  
6. **STOP if** asked to invent XY or arm radial poses.

**Do not** bump version. **Do not** mutate `workspace/` unless ★ `apply_live`.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | Filled fixture pack → proposals match §0.1 Δmm / origins |
| T2 | List-alone never mutates ProjectState |
| T3 | Missing plate box + `requires_plate_box=yes` → honest empty/skip |
| T4 | Disk origin row rejected/skipped (no writer weaken) |
| T5 | Full pytest green; package `0.4.1` |

---

## 3. Smoke (Engineer)

1. Trigger pack on chosen project → see listed phrases.  
2. Retype one → pose (and mount if row says) set.  
3. Board matches table; copy discloses authority.  
4. Confirm no auto-apply on reload.

---

## 4. Out of scope

Silhouette Product B · plate-box fill · stack-rule Path N revive · HD-005

---

## 5. Done when

- [ ] §0.1 filled + ★  
- [ ] Module + IDLE + T1–T5 + report **or** honest B0 hold  
- [ ] Engineer smoke ACCEPT (if implemented)

---

## 6. Handoff

```text
Engineer → fill §0.1 table + ★
Claude   → implement or B0-hold report
Cursor   → review
Engineer → smoke §3
```
