# Implementation Contract — Propellers↔motors catalog-pair evidence (`B1-propellers-motors-catalog-pair`)

**Project:** Jarvis  
**Date:** 2026-09-16  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** CLOSED — Engineer smoke ACCEPT 2026-09-17  

**Parents:**
- Software closeout queue **#3** — [engineer_note_software_closeout_queue.md](engineer_note_software_closeout_queue.md)
- Disk-station investigation **CLOSED** — [report](investigation_report_disk_station_fit_attest_b0.md) §C: `propellers↔motors` needs its **own** evidence class; axial standoff facts **do not exist** live → do **not** invent reach/axial geometry this Buy
- Disk-station reach **CLOSED** — [IC](implementation_contract_disk_station_reach_b1.md): motors↔frame_arm only; propellers↔motors left `n_a_disk` (named debt)
- Fit-relations checklist — `fit_relations_assist.py` still hardcodes propellers→motors → `n_a_disk`
- Existing catalog pairing — `electrical_compatibility._prop_motor` / `library.match_motor_propeller` (compatible_prop_ids / compatible_prop_inch) already powers ERF gaps; **not** yet shown on the `relaciones` row
- HD-005 craft OP XING-E+Gemfan+4S — **parked** (bench / estimate bag); out of this Buy

**Type:** Replace the unconditional `n_a_disk` row for **`propellers` ↔ `motors`** with a **new, narrowly-named catalog-pair screening** that reuses `match_motor_propeller` / the same facts ERF already uses — with copy that affirms **pairing de catálogo**, never hub/shaft/axial/blade clearance, never exact thrust OP.  
**Not** axial reach / prop-to-motor-face offset (no facts → no invent).  
**Not** cylinder-as-box / AABB.  
**Not** Path N.  
**Not** HD-005 exact OP seed.  
**Not** SuggestionEngine N1 / Continuity mission (done).  
**Not** ASSEMBLY_READY flip.  
**Not** version bump. **Not** `workspace/` mutation (tests-only).

**Output:** `.jes/artifacts/implementation_report_propellers_motors_catalog_pair_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**2993** · UI ≥**105** (or current green at ★ time)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-propellers-motors-catalog-pair`** — catalog-pair evidence on the fit-relations `propellers`→`motors` row |
| 2 | Pair | **Only** `propellers` → `motors`. `motors`→`frame_arm` station-reach **unchanged** |
| 3 | Evidence class | **Catalog pairing only** — call existing `default_library.match_motor_propeller(motor_sku, prop_sku)` (or a thin pure wrapper that mirrors `_prop_motor` outcomes). Prefer a shared helper so ERF and `relaciones` cannot drift. **Do not** invent shaft Ø, hub bore, axial standoff, or blade–frame clearance |
| 4 | When to screen | Both components present **and** both have catalog refs with families `motor` / `propeller`. If mount missing (`propellers.mounted_on != "motors"`), keep mount_warning as today; still allow catalog-pair status if both bound (mount and pairing are independent signals — report exact choice) |
| 5 | Status vocabulary (locked semantics; exact names OK if documented) | Distinct from AABB and from `station_reach_*`. Required outcomes: **`catalog_pair_ok`** (match true) · **`catalog_pair_mismatch`** (match false) · **`catalog_pair_unverifiable`** (missing SKU / family / KeyError / unbound) — **never** silently keep `n_a_disk` when both SKUs are bound. Optional: retain `n_a_disk` **only** when the pair is not catalog-bound at all **and** you document that as “no pairing facts yet” (prefer `catalog_pair_unverifiable` for consistency) |
| 6 | Copy (Spanish) | Must say **emparejamiento de catálogo** (ids / pulgadas compatibles). Must **not** say cabe / alcance / hub / eje / clearance / “combo exacto de empuje” / VERIFIED físico. Follow [approx-until-verified](engineer_note_geometry_approx_until_verified.md) honesty |
| 7 | Wire | `fit_relations_assist._mount_only_relation_row`: special-case `child=="propellers" and origin=="motors"` → new helper (name OK, e.g. `_propellers_motors_catalog_pair_row`). `relaciones` / Continuity checklist must show the new statuses. Do **not** widen `pose_envelope_screening` |
| 8 | Human attest | **Out of this Buy** (no geometric screen to seal). Do not invent a prop↔motor attest path |
| 9 | ERF | Do **not** change gap severity / ASSEMBLY_READY. Reuse facts only; optional: assert ERF `prop_motor` outcome matches the new row when both bound (test pin) |
| 10 | Forbidden | Invent mm · axial/reach rule · Path N · HD-005 OP seed · treat cylinder as box · flip ASSEMBLY_READY · LLM · version bump · workspace mutate · SuggestionEngine edits |
| 11 | Live | Default **tests-only**. Engineer smoke on `dron-de-vigilancia-doméstico` or `10-min-autonomía` (both catalog-bound motor+prop) |

**Product sentence:**

```text
Si motor y hélice están en catálogo, relaciones deja de decir “n/a disco”
y muestra si el emparejamiento de catálogo es compatible o no —
sin fingir que eso verifica el eje, el hub o el empuje del combo.
```

### 0.1 Claim ceiling

| Affirms | Does **not** affirm |
|---|---|
| Catalog `compatible_prop_ids` / `compatible_prop_inch` membership | Shaft/hub mechanical fit |
| Same pairing fact ERF already uses | Exact operating-point thrust for that combo (HD-005) |
| Honest unverifiable when unbound | Physical MEASURE / Fit VERIFIED |

### 0.2 Why not B0 again / why not axial

Disk-station B0 §C already established axial geometry needs facts that **do not exist**. This Buy is the **software-honest** closeout for the named debt: surface the pairing authority that already exists, instead of leaving a blank `n_a_disk` forever or inventing axial mm. Axial/shaft Buy stays parked until an Engineer bag exists.

---

## 1. You (Claude)

1. Add pure catalog-pair helper + status/format (own small module or next to fit_relations — report choice).  
2. Rewire `fit_relations_assist` propellers↔motors only.  
3. Tests T1–T8 + report exact status names + Continuity/`relaciones` sample lines.  
4. No version bump. No workspace write. No HD-005 seed.

**STOP if** forced to invent axial/shaft geometry or to claim thrust OP for the Gemfan+XING-E combo.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | Both catalog-bound + `match_motor_propeller` true → `catalog_pair_ok` (or locked name) on assess row |
| T2 | Both bound + match false → `catalog_pair_mismatch` |
| T3 | Motor or prop unbound / wrong family → `catalog_pair_unverifiable` (not silent `n_a_disk` if that path is retired) |
| T4 | `motors`↔`frame_arm` still uses `station_reach_*` (no regression) |
| T5 | `screen_posed_envelope` still `child_not_box` for disks — unchanged |
| T6 | Copy asserts catalog-pair honesty; forbids cabe/alcance/hub/eje/VERIFIED físico |
| T7 | When both bound, row outcome matches `evaluate_electrical_compatibility(...).prop_motor` mapping (compatible↔ok, mismatch↔mismatch, unverifiable↔unverifiable) |
| T8 | Full pytest green; package `0.4.1` |

---

## 3. Smoke (Engineer)

1. Open `dron-de-vigilancia-doméstico` (or 10min) — motor + Gemfan catalog-bound.  
2. `relaciones` (or Continuity fit checklist): propellers↔motors shows **catalog-pair** status/copy — **not** bare “n/a disco” / “Buy aparte”.  
3. Confirm motors↔frame_arm reach statuses still present.  
4. Optional: unbound prop project → unverifiable, not a fake OK.

---

## 4. Out of scope (named debt)

| Item | Note |
|---|---|
| Axial / shaft / hub clearance geometry | Needs Engineer bag — parked |
| HD-005 exact OP XING-E+51466+4S | Lab / estimate ★ |
| SuggestionEngine `increase_payload` on `simular` (N1) | Queue **#4** |
| Hygiene bind-esc / FC-GPS | #4 |
| More identity rules | #5 |
| plate-box / Path N | Parked |

---

## 5. Done when

- [x] ★  
- [x] Helper + wire + T1–T8 + report  
- [x] Cursor review PASS WITH NOTES — [review](implementation_review_propellers_motors_catalog_pair_b1.md)  
- [x] Engineer smoke ACCEPT (`relaciones`: ≈ propellers→motors catalog_pair_ok; motors→frame_arm attest intact; 0 n/a)

---

## 6. Handoff

```text
Engineer → ★ B1-propellers-motors-catalog-pair (this IC)
Claude   → implement catalog-pair row + tests + report
Cursor   → review
Engineer → smoke §3
```
