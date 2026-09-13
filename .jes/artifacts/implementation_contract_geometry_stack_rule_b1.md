# Implementation Contract — Envelope stack rule B1 (`B1-stack-rule`)

**Project:** Jarvis  
**Date:** 2026-09-13  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** READY FOR ★ — pick **Path N** (narrow, implementable now) and/or **Path F** (full stack-on-plate — **data-gated** on plate box)  
**Parents:**
- [investigation_report_board_drone_default_layout_b0.md](investigation_report_board_drone_default_layout_b0.md) §C · [review](investigation_review_board_drone_default_layout_b0.md) N5  
- [feature lock Continuity spatial](engineer_lock_continuity_spatial_assembly_feature.md) — **no silent auto-pose**  
- Pose writer CLOSED — `set_component_declared_box_pose` only writes handed Δmm  
- Mount standard assist B1 — [review](implementation_review_mount_standard_assist_b1.md)  
- Plate-box B1 — [B0 hold](implementation_report_geometry_plate_box_b1.md) · [review PASS](implementation_review_geometry_plate_box_b1.md) — full Path F waits for §0.1 plate L×W  

**Type:** Explicit, **disclosed** rule that proposes (or writes **only after confirm**) a centered/stack Δmm pose from **already-declared envelopes** — never presented as measured CAD.  
**Not** inventing envelopes. **Not** silent pose on Board load. **Not** layout pack / kit cited poses. **Not** plate L×W invent. **Not** Situar UX rewrite. **Not** Conversation Engine. **Not** version bump. **Not** `workspace/` mutation unless ★ Path apply-live.

**Output:** `.jes/artifacts/implementation_report_geometry_stack_rule_b1.md`

**Cola after:** `B1-layout-pack-cited` → silueta · plate-box re-entry when bag filled · [cola](engineer_note_board_situar_work_cola.md)

**Checkpoint:** package **`0.4.1`** · suite ≥**2763** · UI ≥**99**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-stack-rule`** — named rule + honesty copy; never silent |
| 2 | Paths (★ one or both) | **Path N — narrow:** only `propellers` posed on `motors` when both have envelopes (disk/box as already projected) and `mounted_on=motors` (or undeclared → suggest mount first via existing assist). **Path F — full:** stack subjects (`battery`/`esc`/`flight_controller`/`sensors`) centered on boxed `frame_plate` (or single clear plate) — **requires** plate `shape: box` (plate-box data). If plate absent → Path F must **no-op with honest message**, never invent plate |
| 3 | Arithmetic (locked formulas) | **N:** `x_mm=0`, `y_mm=0`, `z_mm = motor.height_mm/2 + prop_axial` — define `prop_axial` in report from existing prop geometry (disk: use documented half-height or 0 if flat disk convention already used in visor; **disclose**). **F:** `x_mm=0`, `y_mm=0`, `z_mm = plate.height_mm/2 + child.height_mm/2` (flush centered stack). No XY offset invent |
| 4 | Confirm UX | **Suggest-only by default:** IDLE phrase family (e.g. `apilar estándar` / `proponer stack`) lists proposed poses + exact Continuity pose phrase **or** applies only after explicit confirm (number / `sí` / retype) — same honesty class as mount-standard-assist. **Silent write on project open = forbidden** |
| 5 | Copy | Every proposal and every written pose path must disclose: *“regla de apilado centrado (supuesto), no medida / no VERIFIED”* (Spanish, short). Mirror screening-disclaimer tone |
| 6 | Writer | Reuse **only** `set_component_declared_box_pose` + existing Continuity pose parse. No new pose schema. Fit attestation fingerprint follows existing pose-write rules |
| 7 | Ambiguity | 2+ plates → Path F AMBIGUOUS (list keys), no guess. Missing envelope on subject or origin → skip that edge with reason |
| 8 | Out | Layout pack · arm-as-subject · invent plate/arm L×W · LLM invent Δmm · version bump · Situar interaction redesign |

**Product sentence:**

```text
Jarvis puede proponerme poses de apilado centrado usando solo las cajas
que ya declaré (hélices sobre motor; o aviónica sobre placa si hay caja
de placa), con copy de supuesto — yo confirmo. No inventa la placa ni
afirma CAD.
```

### 0.1 ★ menu (Engineer picks)

```text
path_star: N | F | N+F
confirm_mode: suggest_retype | number_confirm | (document choice)
live_projects_smoke: autonomía-de-5min | autonomía-15min | fixture-only
```

If ★ **F** while plate-box still B0 hold → Claude implements Path F as **honest skip** + tests for skip; no plate invent. Prefer ★ **N** alone until caliper.

---

## 1. You (Claude)

- Thin pure module (e.g. `stack_rule_assist.py`): given components → list of proposed `{subject, origin, x,y,z, reason, example_pose_phrase, disclaimer}`.  
- IDLE bridge after mount-standard / pose declare family; do not steal `"monta X en Y"` or pose `respecto` parses.  
- Tests: Path N with motor+prop envelopes; Path F with plate box fixture; Path F without plate → empty/skip message; confirm never writes without confirm path; disclaimer present in format string.  
- Do **not** change Scene3D layout math beyond what existing pose already does.  
- Do **not** bump version / mutate `workspace/` unless ★ says apply-live (default: no).

**STOP if** required to invent plate L×W or claim VERIFIED.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | Path N: motor H + prop geometry → proposed z matches locked formula; phrase parses / writer accepts after confirm |
| T2 | Path F + plate box fixture → centered stack z; origin=`frame_plate` |
| T3 | Path F, no plate box → no proposal (honest message), no write |
| T4 | Suggest-only trigger does not mutate state |
| T5 | Formatted output contains disclaimer (supuesto / no verificado) |
| T6 | Full pytest green; package `0.4.1` |

---

## 3. Smoke (Engineer)

**Path N:** 5min with prop+motor envelopes → trigger → confirm one → prop pose on motors; Board shows stack; copy shows supuesto.  
**Path F (only if plate boxed):** trigger → FC/ESC/battery proposals on plate → confirm one.  
Confirm no auto-pose on Board reload alone.

---

## 4. Out of scope

Plate-box data fill · layout-pack-cited · silhouette · subject-vocab · HD-005 · Situar UX

---

## 5. Done when

- [ ] ★ path chosen  
- [ ] Module + IDLE + T1–T6 + report  
- [ ] Engineer smoke ACCEPT (for ★'d paths)  

---

## 6. Handoff

```text
Engineer → ★ path N and/or F (+ confirm_mode)
Claude   → implement + report
Cursor   → review
Engineer → smoke §3
```
