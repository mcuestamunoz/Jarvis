# Implementation Contract — Disk-station radial reach (`B1-disk-station-reach`)

**Project:** Jarvis  
**Date:** 2026-09-15  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** CLOSED · Cursor review PASS WITH NOTES · Engineer smoke **ACCEPT** (2026-09-16)  

**Parents:**
- Investigation **CLOSED** lean **D2** — [report](investigation_report_disk_station_fit_attest_b0.md) · [review PASS WITH NOTES](investigation_review_disk_station_fit_attest_b0.md)
- Fit attestation B1 **CLOSED** — box↔box only; `screen_posed_envelope` + human seal
- Fit-relations checklist **CLOSED** — motors/props hardcoded `n_a_disk`
- Disk-axial Visor **CLOSED** — cylinder ≠ AABB envelope
- Dim honesty — [engineer_note_geometry_approx_until_verified.md](engineer_note_geometry_approx_until_verified.md)
- Dual track — [engineer_note_dual_track_plate_box_disk_station.md](engineer_note_dual_track_plate_box_disk_station.md) · plate-box still bag-gated (orthogonal)
- Path N **HOLD** — do not reopen

**Type:** Ship a **new, narrowly-named** deterministic **station-reach** screening for **`motors` ↔ `frame_arm`**, reusing the same L-vs-R math the Visor already uses for arm radial placement — as an **engineering** verdict with its **own** status names and copy. Optional human seal gated on reach-OK, with a **new** fingerprint (never box L×W×H).  
**Not** cylinder-as-box / `screen_posed_envelope` widen.  
**Not** proxy box on motors.  
**Not** propellers↔motors (named debt).  
**Not** Path N.  
**Not** invent mm.  
**Not** ASSEMBLY_READY flip.  
**Not** plate-box.  
**Not** version bump. **Not** `workspace/` mutation unless ★ Path D (default: tests-only).

**Output:** `.jes/artifacts/implementation_report_disk_station_reach_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**2945** · UI ≥**105** (or current green at ★ time)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-disk-station-reach`** — D2 radial station-reach for motors↔frame_arm |
| 2 | Pair | **Only** `motors` → `frame_arm`. `propellers` → `motors` stays **`n_a_disk`** (unchanged reason or “Buy aparte — prop axial”) |
| 3 | Helper | New pure helper (name OK, e.g. `screen_station_reach` / `station_reach_screening.py` under `jarvis.core`). **Must not** live inside / widen `pose_envelope_screening.screen_posed_envelope` |
| 4 | Inputs (approximate OK) | Require all of: `frame.configuration == "quad_x"`, positive `frame.wheelbase_mm` (or existing `_quad_x_wheelbase_mm` source of truth), `frame_arm` with positive declared/cited `length_mm` as box dim, `motors` present. Prefer `motors.mounted_on == "frame_arm"` — if mount missing, status = insufficient with honest reason (do not invent mount) |
| 5 | Math | Same as Visor `_frame_arm_radial_offsets_mm`: for each quad-X station, `R = hypot(sx, sy)` from `_quad_x_station_points(wheelbase)`; compare arm `L = length_mm` to `R`. Prefer **extract shared pure bits** (station points + L/R compare) into core so Visor and screening cannot drift — or keep Visor as-is and add an equivalence test that pins the formula. **No margin band this Buy** (`L <= R` → ok; `L > R` → over). Do not shrink L |
| 6 | Status names (locked vocabulary) | Distinct from AABB. Exact set OK if documented in report; required semantics: **`station_reach_ok`** · **`station_reach_over`** (L > R) · **`station_reach_insufficient`** (missing wheelbase / arm length / quad_x / motors / arm key) · optional **`station_reach_estimated`** if arm `length_mm` (or wheelbase fact) carries `source=estimated_temporary` — fail closed for attest. **Never** return `overlap` / `no_overlap` / `child_not_box` from this helper |
| 7 | Copy | Spanish Continuity/fit-relations lines must say this is **alcance de estación / reach screening**, approx cited dims, **not** physical VERIFIED, **not** “cabe” AABB, **not** hub/blade clearance. Follow [approx-until-verified](engineer_note_geometry_approx_until_verified.md) |
| 8 | Wire | `fit_relations_assist`: for `motors`↔`frame_arm`, stop forcing `n_a_disk`; call the new helper and map statuses into `FitRelationRow`. Keep mount_warning independent. `relaciones` IDLE output must show the new statuses |
| 9 | Human attest (in scope) | Allow Engineer seal on **motors** when helper status is **`station_reach_ok` only**. New fingerprint function over reach inputs (e.g. wheelbase, arm length_mm + source, frame configuration, mounted_on) — **never** call `compute_fit_attestation_fingerprint` (box L×W×H). Clear seal when those inputs change (mirror existing clear-on-geometry-change discipline). IDLE phrase may reuse `declaro verificado` subject resolution for `motor`/`motores` **only if** the writer path branches to station-reach gate; do not let box-overlap writer grant a seal on motors |
| 10 | Forbidden | Cylinder→box · Path N · N seals · invent arm L / wheelbase · prop↔motor rule · ASSEMBLY_READY / ERF flip · Conversation Engine · version bump · silent catalog fill |
| 11 | Live | Default **tests-only**. Optional ★ Path D: apply/read on `10-min-autonomía` or vigilancia (facts already cited) — report only if ★ |

**Product sentence:**

```text
Jarvis puede decir si el brazo declarado alcanza el radio de estación
del quad-X (misma cuenta que el Visor), sin fingir que el motor es una
caja ni que eso verifica el ensamblaje físico.
```

### 0.1 Claim ceiling (Engineer lock)

| Affirms | Does **not** affirm |
|---|---|
| Arm `length_mm` vs wheelbase-derived station radius (L≤R / L>R) | Hub interference, blade–frame clash, vertical clearance |
| Approximate cited/declared facts usable for screening | Physical MEASURE / Fit VERIFIED without human seal |
| Human seal = Engineer judgment on already reach-ok | Auto-VERIFIED from Visor pixels or `mounted_on` alone |

No numeric §0.1 bag — live projects already have cited wheelbase + arm L + motor mount (investigation A5). Do not invent substitutes.

---

## 1. You (Claude)

1. Add core station-reach helper + status/format helpers (own module preferred).  
2. Optionally extract shared quad-X station / L–R pure functions; keep Visor behavior byte-stable or prove equivalence in tests.  
3. Rewire `fit_relations_assist` motors↔frame_arm only.  
4. Station-reach attest path + fingerprint + clear-on-change; box attest writer untouched for non-motor keys.  
5. Tests T1–T9. Report status vocabulary + example Continuity lines.  
6. No version bump. No workspace write unless ★ Path D.

**STOP if** forced to treat cylinder as box AABB, reopen Path N, or invent arm/wheelbase mm.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | Helper: fixture quad_x + wheelbase + arm L ≤ R → `station_reach_ok` |
| T2 | Helper: L > R → `station_reach_over` (never silent shrink) |
| T3 | Helper: missing wheelbase / arm length / not quad_x → `station_reach_insufficient` |
| T4 | `estimated_temporary` on arm `length_mm` → estimated/insufficient path; **attest SET raises** (fail closed) |
| T5 | `assess_fit_relations`: motors↔frame_arm uses reach statuses; propellers↔motors still `n_a_disk` |
| T6 | `screen_posed_envelope` still `child_not_box` for disk/cylinder motors — **unchanged** |
| T7 | Attest OK only on `station_reach_ok`; fingerprint ≠ box fingerprint; clear when arm L or wheelbase changes |
| T8 | Copy strings contain reach/alcance honesty; forbid claiming AABB “cabe” / bare VERIFIED from screening alone |
| T9 | Full pytest green; `0.4.1`; UI suite unchanged if no `ui/` edit (prefer no UI this Buy — Continuity/`relaciones` enough) |

---

## 3. Smoke (Engineer)

1. Project with cited wheelbase + `frame_arm.length_mm` + motors mounted on arm (e.g. 10-min or vigilancia).  
2. `relaciones` → motors↔frame_arm shows reach ok/over/insufficient — **not** old blank `n_a_disk` (unless insufficient).  
3. If reach ok → `declaro verificado` on motor (or documented phrase) seals; change arm L → seal clears.  
4. Confirm propellers row still disk honesty.  
5. Confirm no plate-box / estimated plate behavior changed.

---

## 4. Out of scope (named debt)

| Item | Note |
|---|---|
| `propellers` ↔ `motors` reach/axial | Needs its own evidence class |
| Margin band / tolerance on L vs R | Separate ★ |
| Path N / disk pose origin | HOLD |
| Plate-box / stack AABB attest | Parallel bag track |
| Visor Situar drag for multi-copy motors | Out |
| ASSEMBLY_READY coupling | Out |

---

## 5. Done when

- [x] ★  
- [x] Helper + fit_relations wire + attest path + T1–T9 + report  
- [x] Cursor review PASS WITH NOTES — [review](implementation_review_disk_station_reach_b1.md)  
- [x] Engineer smoke ACCEPT (2026-09-16) — `relaciones` reach-ok + `declaro verificado el motor`

---

## 6. Handoff

```text
Engineer → ★ B1-disk-station-reach
Claude   → implement + tests + report (no invent mm)
Cursor   → review
Engineer → smoke §3 (or waive)
```
