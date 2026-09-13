# Implementation Contract — Craft montage Path F on plate B1 (`B1-craft-montage-path-f`)

**Project:** Jarvis  
**Date:** 2026-09-13  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke on **≥2** projects

**Status:** READY FOR ★  
**Parents:**
- [engineer_lock_craft_montage_honest_reproducible.md](engineer_lock_craft_montage_honest_reproducible.md) — north star  
- [implementation_contract_geometry_stack_rule_b1.md](implementation_contract_geometry_stack_rule_b1.md) · [report B0](implementation_report_geometry_stack_rule_b1.md) · [review](implementation_review_geometry_stack_rule_b1.md) — Path N **dead**; Path F was data-gated on plate box  
- [implementation_contract_geometry_estimated_temporary_plate_b1.md](implementation_contract_geometry_estimated_temporary_plate_b1.md) — plate box now obtainable without caliper (layout only)  
- [implementation_contract_mount_standard_assist_b1.md](implementation_contract_mount_standard_assist_b1.md) — mounts suggest-only (landing)  
- [implementation_contract_geometry_layout_pack_cited_b1.md](implementation_contract_geometry_layout_pack_cited_b1.md) — **next** for XY cited offsets (empty §0.1 stays hold)  
- [implementation_contract_board_silhouette_product_b_b1.md](implementation_contract_board_silhouette_product_b_b1.md) — **not** this Buy  

**Type:** Implement **stack-rule Path F only** — propose (suggest → confirm) centered flush stack poses of **box subjects** onto a **boxed** `frame_plate*` origin. Origin may be **cited/caliper** or **`estimated_temporary`** with mandatory honesty copy. Mechanism is **project-agnostic** (any craft with plate box + child boxes).  
**Not** Path N (disk origins). **Not** layout-pack table invent. **Not** Product B claim. **Not** invent plate/arm L×W. **Not** silent pose on load. **Not** kit-hardcode for MY5/10min. **Not** Conversation Engine. **Not** version bump.

**Output:** `.jes/artifacts/implementation_report_geometry_craft_montage_path_f_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**2785** · UI ≥**99**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-craft-montage-path-f`** — reopen stack-rule **Path F only** now that plate boxes exist (estimated or cited) |
| 2 | Path N | **Forbidden** this Buy (schema: disk ≠ pose origin) |
| 3 | Arithmetic (locked) | For each proposed subject with `shape: box` and boxed plate origin: `x_mm=0`, `y_mm=0`, `z_mm = plate.height_mm/2 + child.height_mm/2` (flush centered). **No XY invent** |
| 4 | Subjects in scope | `flight_controller`, `esc`, `battery`, `sensors` — only if each has a **box** envelope already projected. Skip missing/non-box with reason. Do **not** propose motors/propellers (Visor X / wheelbase — already separate) |
| 5 | Origin pick | Prefer single clear main plate: if exactly one `frame_plate` (or label Top/main) with box → that key. If multiple plate boxes and no unambiguous main → **AMBIGUOUS** list keys, no guess. Never invent a plate key |
| 6 | Estimated plate | **Allowed** as Path F origin when `source=estimated_temporary` on plate dims. Copy **must** say stack is on **geometría estimada temporal** / supuesto centrado — **not** medida, **not** VERIFIED, **not** “cabe”. Fit attestation SET remains refused (existing screening) — do **not** weaken |
| 7 | Confirm UX | Suggest-only IDLE (Spanish triggers, pick 1–2, document): e.g. `apilar en placa` / `proponer stack centrado`. List each proposal + exact Continuity pose phrase. Confirm = **retype** phrase (default, mount-assist class) **or** number→existing pose writer if thin and documented. **Silent write = forbidden** |
| 8 | Writers | Reuse **only** `set_component_declared_box_pose` + existing Continuity pose parse. No new pose schema. No writer-gate weaken for disks |
| 9 | Mounts | **Do not** auto-write `mounted_on`. Optionally one line: “si falta montaje, `montajes estándar`”. Prefer Path F proposals even if mount undeclared (pose and mount stay orthogonal — disclose). Do **not** invent mounts |
| 10 | Reproducibility | Zero SKU / project-id branches. Same module must work for fixture + any live project with plate box. Smoke **must** include **two** projects (recommend `autonomía-de-5min` + `10-min-autonomía` — both MY5 + estimated plate already smoked) |
| 11 | Out | Layout-pack §0.1 fill · silhouette Product B claim · arm-as-subject · standoff clearance invent · Continuity kit-tip G1 · HD-005 · version bump · `workspace/` mutation unless ★ apply-live (default: **no** — Engineer confirms poses in smoke) |

**Product sentence:**

```text
Con placa en caja (estimada o citada), Jarvis me propone apilar FC/ESC/
batería/GPS centrados sobre la placa (z por alturas declaradas); yo confirmo.
Sirve en cualquier proyecto con esos datos. No inventa XY ni dice CAD.
```

### 0.1 ★ menu (Engineer)

```text
path_star: F                    # locked — N forbidden
confirm_mode: suggest_retype | number_confirm
live_smoke: autonomía-de-5min + 10-min-autonomía | other:
apply_live: none | engineer_confirms_in_cli
estimated_plate_ok: yes         # locked for this Buy
```

---

## 1. You (Claude) — after ★

1. Pure module (prefer `stack_rule_assist.py` or `craft_montage_stack_assist.py`):  
   `propose_path_f_stack(components) -> list[{subject, origin_key, x_mm, y_mm, z_mm, reason, example_pose_phrase, disclaimer, skip_reason?}]`  
2. Plate resolution + estimated disclosure flags as above.  
3. IDLE orchestrator bridge — do not steal `monta X en Y`, estimated-plate declare, or generic pose `respecto` parses.  
4. Format Spanish list + disclaimers.  
5. Tests §2. Full suite green. Report.  
6. **STOP if** asked to invent XY, weaken disk origin gate, claim Product B, or seed a fake layout-pack table.

**Do not** bump version. **Do not** mutate `workspace/` unless ★ `apply_live`.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | Fixture: boxed `frame_plate` (declared source) + boxed FC/ESC → proposals match locked z formula; x=y=0; origin=`frame_plate` |
| T2 | Same with `estimated_temporary` plate dims → proposals still emitted; disclaimer mentions estimada/temporal / supuesto |
| T3 | No plate box → empty proposals + honest message; no write |
| T4 | Two plate boxes, no unambiguous main → AMBIGUOUS; no guess |
| T5 | Subject missing box (e.g. identity-only) → skipped with reason; others still proposed |
| T6 | List-alone / suggest-only never mutates `ProjectState` |
| T7 | Confirm path (retype or number) calls existing writer; disk origin still rejected if somehow proposed |
| T8 | No MY5 / `10-min` / `5min` string special-cases in assist module |
| T9 | Full pytest green; package `0.4.1` |

---

## 3. Smoke (Engineer) — reproducibility gate

On **both** `autonomía-de-5min` and `10-min-autonomía` (or ★ substitutes):

1. Ensure `frame_plate` box exists (`declara frame_plate estimada 120 x 55 mm` if needed).  
2. Optional: `montajes estándar` → confirm expressible mounts.  
3. Trigger Path F phrase → see FC/ESC/battery/sensors proposals (those with boxes).  
4. Retype/confirm **one** pose → Board: child moves relative to plate root (no longer pure gallery for that part).  
5. Confirm copy does **not** say VERIFIED / cabe / CAD.  
6. Confirm second project works with **same** phrases (no project-specific tip).  
7. Motors/props may stay on Visor X / row — **OK** this Buy (not Path N).

**ACCEPT** = mechanism works on ≥2 projects. **Not** ACCEPT = “looks like a finished drone CAD”.

---

## 4. Honesty / data sufficiency (this Buy vs later)

| Need | This Buy | Later |
|---|---|---|
| Geometry box plate | estimated OK | caliper → plate-box Buy |
| Dimensions child boxes | must already exist | sourced dims Buys |
| Interfaces (holes, XT60 fit) | out | lateral |
| Mounting references | optional tip to mount-assist | pack / subject-vocab |
| XY kit layout | out | **layout-pack-cited** when §0.1 filled |
| Product B claim | out | silhouette IC when prereqs met |

---

## 5. Explicit non-goals

- Filling layout-pack §0.1 / inventing MY5 stack XY  
- Claiming Product B / “parece un dron” in Continuity  
- Path N prop→motor pose  
- Standoff gap invent (flush z is a **supuesto**)  
- Widening mount subjects (`frame_arm`, kit hardware)  
- Auto-apply on Board load  
- Fixing Continuity `power_connector` tip spam (G1)

---

## 6. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/core/stack_rule_assist.py` (or `craft_montage_stack_assist.py`) | **new** pure propose + format |
| `src/jarvis/core/orchestrator.py` | IDLE bridge |
| `tests/test_geometry_craft_montage_path_f_b1.py` | T1–T8 |
| `.jes/artifacts/implementation_report_geometry_craft_montage_path_f_b1.md` | Claude |
| Cola / PRIORIDAD | Cursor after review |

---

## 7. Done when

- [ ] ★ + Path F module + IDLE + T1–T9  
- [ ] Report lists formula, triggers, estimated disclosure  
- [ ] Cursor review PASS  
- [ ] Engineer smoke ACCEPT on **≥2** projects (§3)  
- [ ] Layout-pack / Product B remain gated (not falsely closed)

---

## 8. Handoff

```text
Engineer → ★ this IC (confirm §0.1 menu)
Claude → implement Path F only + report
Cursor → review
Engineer → smoke 5min + 10min
Next → fill layout-pack §0.1 (XY) and/or plate caliper; then silhouette when honest
```
