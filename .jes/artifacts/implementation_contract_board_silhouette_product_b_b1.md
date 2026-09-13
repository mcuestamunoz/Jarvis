# Implementation Contract — Silhouette Product B B1 (`B1-silhouette-product-b`) · **Path S1**

**Project:** Jarvis  
**Date:** 2026-09-13  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** READY FOR ★ — **Path S1 locked** (Engineer: estimated = Product B\* normal; ★ = `checklist_idle`)  
**Parents:**
- [engineer_lock_geometry_3d_mapping_path.md](engineer_lock_geometry_3d_mapping_path.md) — Product **A racimo** vs **B silueta**  
- Estimated-temporary plate · Path F · layout-pack · mount-standard — **CLOSED**  
- Pattern peers: `mount_standard_assist.py` · `craft_montage_stack_assist.py` · `layout_pack_assist.py`  
- [cola](engineer_note_board_situar_work_cola.md) #5  

**Type:** Deterministic **suggest-only** IDLE checklist that answers “¿parece un dron / silueta?” from live Continuity — **read-only**, no writers, no invent mm.  
**Not** Three.js polish (S2). **Not** silent pose/mount. **Not** inventing plate L×W. **Not** claiming measured CAD when plate is estimated. **Not** version bump. **Not** `workspace/` mutation.

**Output:** `.jes/artifacts/implementation_report_board_silhouette_product_b_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**2830** · UI ≥**99**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-silhouette-product-b`** · **Path S1** only this cycle |
| 2 | Plate authority | **Estimated plate = normal Product B\* path** (OEM rarely publishes plate L×W). No plate box → **Product A (racimo)**. Declared/cited plate → Product B without \*. Estimated → always **\*** / “estimada” in checklist verdict until user replaces with measured `declared` |
| 3 | UX | IDLE triggers (Spanish, normalize accents): **`silueta`**, **`parece un dron`**, **`¿parece un dron?`**, **`product b`**. Document exact match family in report |
| 4 | Behavior | Pure module + orchestrator IDLE bridge → **checklist + verdict**. Never calls pose/mount/envelope writers. Confirm = user types phrases already suggested by siblings (`montajes estándar`, `apilar en placa`, `layout pack`, `declara … estimada`, Visor/`actualiza frame…`) — this Buy only **points**, does not re-implement those assists |
| 5 | Verdict enum (copy) | **`racimo` (A)** · **`silueta estimada (B*)`** · **`silueta (B)`** — never “VERIFICADO” / “CAD medido del kit” |
| 6 | Disclosure | Reuse existing Board ESTIMADA TEMPORAL on plate; checklist must repeat \* when any plate L/W/H is `estimated_temporary` |
| 7 | Forbidden | Invent dims · auto-write · S2 visor polish · weaken pose origin-must-be-box · claim B without \* on estimated plate |
| 8 | Version | **No** bump |

**Product sentence:**

```text
Pregunto “¿parece un dron?” y Jarvis me dice racimo / silueta* / silueta,
qué falta, y la frase o comando ya existente — sin inventar mm ni escribir solo.
Si la placa es estimada, la silueta lleva * hasta que mida el frame real.
```

### 0.1 Prerequisites bag — **FILLED** (smoke target)

```text
### silhouette target project:
project: 10-min-autonomía (7e400f0a4983)
frame_sku: hglrc_my5_5in
frame_plate_box: yes (L=120 W=55 H=2 authority=estimated_temporary) → B*
wheelbase_projected: yes
motors_props_x_visible: yes
stack_posed_to_plate: yes (Path F / layout-pack)
pose_cycle_absent: yes
optional_arm_boxes: yes (stations, not radial)
code_star: checklist_idle   # Path S1 — LOCKED
```

---

## 1. You (Claude) — after ★

### 1.1 Module (e.g. `silhouette_product_b_assist.py`)

Pure functions over `components` (and minimal project context if wheelbase already exposed the same way Visor/X uses — prefer reading existing helpers, do not duplicate X math):

```text
assess_silhouette(components) -> SilhouetteAssessment
format_silhouette_checklist(assessment) -> str
is_silhouette_assist_trigger(user_input) -> bool
```

**Checklist rows (deterministic, fixed order)** — each row is `ok` | `missing` | `estimated` | `n/a`, with optional **suggest** string (existing phrase/command only):

| # | Gate | ok when | if missing → suggest (examples; match live assists) |
|---|---|---|---|
| 1 | Placa con caja | `frame_plate*` (or sole boxed plate) has box L×W×H | `declara frame_plate estimada L x W mm` (or measured declare) |
| 2 | Autoridad placa | always reported | if any L/W/H `estimated_temporary` → mark **\***; if all declared/cited → no \* |
| 3 | Stack posado a placa | FC, ESC, battery, sensors that **exist** and have box: each has `declared_box_pose` with box origin (plate) | `apilar en placa` / `layout pack` / exact pose phrase from those assists — do not invent z |
| 4 | Montajes stack | those same subjects have `mounted_on` when present | `montajes estándar` or Continuity mount phrases (**prefer Spanish nouns** that parse — not raw keys `flight_controller`/`sensors` alone) |
| 5 | Visor X / wb | frame has usable wheelbase path so motors/props show on X (same honesty as today — detect via existing fields/helpers if available; if undetectable without new arch, row = `n/a` with reason, do not invent) | `actualiza frame desde catálogo` only if that is already the documented recovery |
| 6 | Pose cycle | no “only sibling cycle” as sole anchor (reuse Continuity honesty if a cheap check exists; else skip with `n/a`) | — |

Subjects absent from the project → skip that subject (do not demand FC if not declared).

**Verdict rules:**

```text
if no plate box:
  verdict = racimo (A)
elif plate box and (stack incomplete OR mounts incomplete for present boxed stack subjects):
  verdict = racimo (A)   # still “not yet a silhouette”
  # list missing rows — do NOT claim B* early
elif plate box and stack+mounts OK for present subjects:
  if plate dims estimated_temporary:
    verdict = silueta estimada (B*)
  else:
    verdict = silueta (B)
# X/wb row missing alone: warn in list but do not block B*/B if plate+stack+mounts OK
#   (Engineer: X already shipped on 10min; warn-only avoids false racimo)
```

Tune copy so a green 10min with estimated plate + full stack/mounts prints **silueta estimada (B\*)** and “nada crítico pendiente” (plus reminder: sustituir L×W al llegar el frame).

### 1.2 Orchestrator

IDLE bridge after layout-pack / craft-montage family (same suggest-only class).  
`handle_user_text` trigger → assessment → format → `action: silhouette_checklist` (or equivalent). **Never** mutate state.

### 1.3 Do not

- S2 Scene3D/Three.js work  
- New writers  
- Seed library plate L×W  
- Bump version  
- Mutate `workspace/`  

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | No plate box → verdict **racimo**; message no Product B |
| T2 | Estimated plate + all stack posed+mounted (10min-shaped fixture) → **silueta estimada (B\*)**; copy has \* / estimada; never “medido” |
| T3 | Same fixture but plate dims `declared` → **silueta (B)** without requiring \* |
| T4 | Estimated plate but ESC missing pose → **racimo**; suggests existing assist phrase, list-alone does not write |
| T5 | Trigger phrases resolve; unrelated (`montajes estándar`, `layout pack`) do not steal this bridge |
| T6 | IDLE list-alone never mutates ProjectState |
| T7 | Full pytest green; package `0.4.1` |

---

## 3. Smoke (Engineer) — `10-min-autonomía`

1. `parece un dron` / `silueta` → expect **silueta estimada (B\*)** (after remount esc if still cleared).  
2. Board: plate ESTIMADA visible; X + stack look like a drone.  
3. Optional: `quita la pose del esc` → re-trigger → racimo + suggest → retype pose → B\* again.  
4. Confirm no auto-write on trigger alone.

---

## 4. Out of scope

S2 polish · arm radial · invent plate mm · mount key-tip FN (orthogonal; prefer nouns in suggests) · HD-005

---

## 5. Done when

- [x] §0.1 + Path S1 specified  
- [ ] Engineer ★  
- [ ] Module + IDLE + T1–T7 + report  
- [ ] Engineer smoke ACCEPT  

---

## 6. Handoff

```text
Engineer → ★ Path S1 (this IC)
Claude   → implement silhouette_product_b_assist + IDLE + tests + report
Cursor   → review
Engineer → smoke §3 on 10-min-autonomía
```

### Paste for Claude (after ★)

```text
Implementá B1-silhouette-product-b Path S1 per
.jes/artifacts/implementation_contract_board_silhouette_product_b_b1.md
— checklist IDLE only; estimated plate = Product B*; no writers; no version bump;
no workspace/ mutation. Report → implementation_report_board_silhouette_product_b_b1.md
```
