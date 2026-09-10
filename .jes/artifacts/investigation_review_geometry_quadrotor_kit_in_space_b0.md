# Investigation Review — 4 motors + 4 hélices in space (product B)

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_geometry_quadrotor_kit_in_space_b0.md](investigation_contract_geometry_quadrotor_kit_in_space_b0.md)  
**Report:** [investigation_report_geometry_quadrotor_kit_in_space_b0.md](investigation_report_geometry_quadrotor_kit_in_space_b0.md)  
**Parents:** mapping path A vs B · copies B1 @ **2473** · pose origin = box · `"cabe"` CLOSED

## Verdict

**PASS WITH NOTES** · recommended Buy **`B1-copies-prop`**.

Three walls are real: live motor SKU has no Ø; copies strip pose; writer rejects a disk origin. The **only** first Buy with live 3D today is N **propeller disks in the row**, N from the project’s `motor_count`. That is **not** millimetre stations and **not** four motors in an X.

`B1-stations` / `B1-disk-origin` stay parked. No IC until Engineer ★.

---

## Checklist

| Criterion | Result |
|---|---|
| Live motors geometry | **Pass** — both demos `emax_rs2205_2300`, `diameter_mm` absent, `geometry` None, `solidCopies` None |
| Live propellers disk Ø127 | **Pass** |
| Copies strip pose (U3 / TS) | **Pass** |
| Writer rejects disk origin | **Pass** — `set_component_declared_box_pose` |
| One `DeclaredBoxPose` per spec | **Pass** |
| Frame still no box | **Pass** |
| BOM “1 propeller per motor” | **Pass** — `_bom_quantity` |
| Single first Buy named | **Pass** — Claude **B1-copies-prop**; Cursor **keeps** it (N1) |
| Remaining pieces later ★ | **Pass** |
| Report-only | **Pass** |

---

## Independent checks

| Claim | Cursor |
|---|---|
| Library `emax_rs2205_2300` has no `diameter_mm` | **Confirmed** — old thrust/kv row |
| Sibling `emax_rs2205s_2300` has Ø 27.9 / height 31.7 | **Confirmed** — **do not copy** onto the live SKU (N3) |
| 5min `motor_count` **4**; 10min **3** | **Confirmed** (params + spec) |
| 10min “zero poses” | **Wrong** — ESC pose 5/0/0 vs FC exists (N2). Motors/hélices still none |
| `_solid_copies` SoT = spec `motor_count`, never params | **Confirmed** |

---

## Notes

### N1 — This Buy is a row of hélices, not “en el espacio”

Product sentence if ★ **B1-copies-prop**:

```text
El visor muestra N discos de hélices, N = motor_count del spec de motors
(el mismo que ya usa el BOM). Una card. Sin pose. Sin mm. Los motores
siguen invisibles (SKU sin Ø). Aún no es un quadrotor.
```

If Engineer wanted millimetre stations this week → ★ **`B0`** (park) or a later **`B1-stations`** with schema + still no live motors until Ø exists.

### N2 — 10min pose census

§A said 10min has zero poses. Live ESC is posed. Does not change motors/hélices. Remaining pieces stay later ★.

### N3 — Do not steal Ø from `emax_rs2205s_2300`

Live bind is the row **without** `s`. Seeding 27.9 onto `emax_rs2205_2300` is a **different** catalog honesty Buy, out of this IC.

### N4 — Count SoT for the IC

Motor copies B1: **spec** `motor_count`, never `current_parameters` (may drift). `_bom_quantity` prefers params. Visor propeller copies must use the **same** N as `_solid_copies` would: `components["motors"].properties["motor_count"]`. 10min → **3** disks, not 4.

### N5 — 10min is not a 4-motor kit

Do not coerce `quad_x` → 4.

---

## Buys (after review)

| ★ | Meaning |
|---|---|
| **`B1-copies-prop`** | **Default** — propeller `solidCopies` = motors spec `motor_count`; row; pose stripped; one card |
| **`B0`** | Park. Wait for Ø / stations / disk-origin as a real ★ |
| **`B1-stations`** | **Parked** — per-copy pose array; zero live motors until Ø |
| **`B1-disk-origin`** | **Parked** — reopen box-only origin; still not N stations |
| **B-naive** | **Forbidden** — default 4 · copy sibling Ø · quad-X of 230 · N BOM motors · cylinder · `"cabe"` on disks |

---

## Phase

Investigation **CLOSED**. Engineer ★ **`B1-copies-prop`** (2026-09-09). IC: [implementation_contract_geometry_propeller_visor_copies_b1.md](implementation_contract_geometry_propeller_visor_copies_b1.md). Package `0.3.8` · suite **2540**.
