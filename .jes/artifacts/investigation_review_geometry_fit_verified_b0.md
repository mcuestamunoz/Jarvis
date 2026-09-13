# Investigation Review — Fit VERIFIED (beyond AABB screening)

**Date:** 2026-09-10  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_geometry_fit_verified_b0.md](investigation_contract_geometry_fit_verified_b0.md)  
**Report:** [investigation_report_geometry_fit_verified_b0.md](investigation_report_geometry_fit_verified_b0.md)  
**Parents:** screening B1-min CLOSED + ACCEPT · Board Situar @ `v0.4.1` · ladder COMPARAR/VERIFICAR

## Verdict

**PASS WITH NOTES** · recommended Buy **`B1-attest`** (Cursor keeps Claude’s lean).

No stronger *geometric* evidence class is available without CAD/MEASURE or a large new declared concept (faces). Attestation is the only candidate whose evidence is categorically different from AABB screening — **if** copy always says Engineer-declared, never bare `VERIFIED`, and attestation is rejected unless `screen_posed_envelope(...).status == "overlap"`. **`B0` remains fully legitimate** if Engineer prefers never shipping the word.

No IC until Engineer ★.

---

## Checklist

| Criterion | Result |
|---|---|
| A–E answered | **Pass** |
| Screening as-is + forbidden tokens | **Pass** — Cursor re-read `format_screening` |
| Live census (read-only) | **Pass WITH N1** — 5min 14 complete box–box; 10min 1 |
| Menu V0…V-forbidden | **Pass** — margin/compose correctly OUT for the *word* VERIFIED |
| Single Buy + `ASSEMBLY_READY` untouched | **Pass** — `B1-attest`; readiness default yes |
| Stub filename not implemented | **Pass** |
| Report-only (no `src/`/`ui/`/`library/`) | **Pass** — `git status` clean for those |
| Incidental stale `0.4.0` test | **Pass** — confirmed `test_p6_library_and_version_untouched` |

---

## Independent checks

| Claim | Cursor |
|---|---|
| AABB rule `abs(Δ) ≤ half_c+half_o` all axes | **Confirmed** `pose_envelope_screening.py:92-96` |
| Board `sobres` + IDLE `cabe` share helper | **Confirmed** `spatial_board.py:671-674` · `orchestrator.py:2147+` |
| LEVEL A ≠ geometric fit (forbidden copy) | **Confirmed** `engineering_readiness.py:889-891` |
| `_derive_overall` ignores pose/screening | **Confirmed** `engineering_readiness.py:1199-1211` |
| Pose writer does not gate on overlap | **Confirmed** `set_component_declared_box_pose` gates only existence/box-origin |
| `catalog_bind` divergence-clear pattern exists | **Confirmed** `invalidate_diverged_catalog_refs` docstring/`catalog_bind.py:4-6` |
| 10min: 1 complete pair `esc`→FC `overlap` | **Confirmed** |
| 5min: 14 complete box–box posed | **Confirmed** (keys match report) |
| 5min overlap / no_overlap split | **N1** — Cursor now: **5 / 9** (report said 6 / 8) |
| `frame_plate_2` non-round floats (Situar) | **Confirmed** |
| Suite pin test still asserts `0.4.0` | **Confirmed** |

---

## Notes

### N1 — Census 5/9 not 6/8

Live recount with `ProjectState` + `screen_posed_envelope`:

- **overlap (5):** `esc`, `flight_controller`, `frame_cage`, `frame_standoff`, `power_connector`
- **no_overlap (9):** `battery`, `sensors`, `frame_plate_2..6`, `signal_harness`, `prop_adapter`

Qualitative claim stands: **majority `no_overlap`**, write path never blocks it, attestation **must** hard-reject `no_overlap`. Do not block Buy on the off-by-one.

### N2 — Why Cursor keeps `B1-attest`

Margin/compose stay the same evidence *class* (declared mm + AABB-shaped rule). Faces are honest engineering but not minimum. Attestation is human evidence — the only way to say a stronger word without lying about geometry — provided IC locks:

1. Gate = `overlap` only (never attest past `no_overlap`).  
2. Distinct copy: *“Declarado verificado por el Engineer…”* — never mutate `format_screening`.  
3. Fingerprint invalidation on pose/envelope change (catalog_bind pattern).  
4. `ASSEMBLY_READY` / PASS untouched this Buy.  
5. New IC filename — never `implementation_contract_geometry_assembly_fit_compare.md`.

### N3 — `B0` is not a strawman

If Engineer does not want human rubber-stamp language near “fit,” ★ **B0**: screening remains the ceiling until MEASURE. Report already frames this honestly.

### N4 — Incidental suite pin

`tests/test_geometry_prop_adapter_visor_x_b1.py` still expects `version = "0.4.0"`. Out of this investigation. Fix under the next IC that touches tests (or a one-line hygiene Buy) — not Fit VERIFIED logic.

### N5 — Bare `cabe` UX with 14 posed keys

Flagged correctly; out of Fit VERIFIED. Optional later Continuity UX, not this Buy.

---

## Buys (after review)

| ★ | Meaning |
|---|---|
| **`B1-attest`** | **Default** — Engineer attestation on one `overlap`-screened pair; human copy; auto-clear on pose/geometry drift; readiness untouched |
| **`B0`** | Park. Never ship VERIFIED. Screening forever until MEASURE/CAD |
| **`B1-margin` / `B1-compose`** | Stricter or broader **screening** only — **not** the word VERIFIED this cycle |
| **`B1-faces`** | Later rung — not minimum |
| **V-forbidden** | **Forbidden** — rename overlap→VERIFIED · ASSEMBLY_READY from AABB · visor math · invent Rooster box |

---

## Phase

Investigation **REVIEWED PASS WITH NOTES**. Engineer ★ **`B1-attest`** (2026-09-10). IC: [implementation_contract_geometry_fit_attestation_b1.md](implementation_contract_geometry_fit_attestation_b1.md). Package `0.4.1` · suite **2669** · UI **80**.
