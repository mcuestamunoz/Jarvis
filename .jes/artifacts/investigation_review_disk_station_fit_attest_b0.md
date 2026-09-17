# Investigation Review — Disk-station fit / attest (`B0-disk-station-fit-attest`)

**Date:** 2026-09-15  
**Reviewer:** Cursor (independent — not investigator)  
**Against:** [contract](investigation_contract_disk_station_fit_attest_b0.md) · [report](investigation_report_disk_station_fit_attest_b0.md)  
**Verdict:** **PASS WITH NOTES**

---

## Contract checklist

| Gate | Result |
|---|---|
| Read-only · no `src/`/`ui/`/`library/`/`tests/` | **Pass** (spot-check; report + tracking only) |
| A–E answered with live citations | **Pass** |
| Single lean (D2) + D0 as honest fallback | **Pass** |
| Box screening untouched · no cylinder-as-box | **Pass** |
| Path N not reopened | **Pass** |
| One station seal / no N seals | **Pass** — one `ComponentSpec` family |
| Orthogonal to plate-box / estimated | **Pass** |
| First case `motors ↔ frame_arm` | **Pass** — justified vs prop↔motor |
| ASSEMBLY_READY untouched | **Pass** |

## Spot-checks (code)

| Claim | Check |
|---|---|
| `_mount_only_relation_row` always `n_a_disk` | **Confirmed** `fit_relations_assist.py` ~221–237 |
| `screen_posed_envelope` box-only | **Confirmed** |
| `_frame_arm_radial_offsets_mm` uses `L` vs `R=hypot(station)` | **Confirmed** `spatial_board.py` ~682–735 |
| Fingerprint indexes child/origin L×W×H only | **Confirmed** — must not reuse for disk B1 |

## Notes

| ID | Severity | Note |
|---|---|---|
| **N1** | Soft (IC must lock) | D2 **promotes Visor presentation math** (`wheelbase` → station radius) into an **engineering** verdict. That is allowed only with new status names + copy that never says `overlap` / “cabe físico” / VERIFIED from reach alone. IC must state: inputs = cited/declared `wheelbase_mm` + `frame_arm.length_mm` (+ mount); fail-closed if missing/estimated where applicable. |
| **N2** | Soft (product lock from Engineer) | Dimensions are **approximate until verified**. Catalog-missing axes = **pending physical verify**, not invent. See [engineer_note_geometry_approx_until_verified.md](engineer_note_geometry_approx_until_verified.md). Any B1 disk-station attest must keep human seal distinct from reach screening (same spirit as box `declaro verificado`). |
| **N3** | Cosmetic | Report footer “only this report” vs also syncing `engineering_state` / PRIORIDAD — harmless. |
| **N4** | Soft | Future attest fingerprint for stations must be **new** (reach inputs), not `compute_fit_attestation_fingerprint` (box L×W×H). |

## Lean (Cursor)

Agree with report: **D2** is the only candidate that adds a deterministic check without proxy-box theater or attest-without-screen double standard. Engineering value is **thin but honest** (arm reaches wheelbase radius — not hub clearance / blade clash). Worth a **narrow B1** if Engineer ★ accepts that claim ceiling.

**D0** remains valid if Engineer parks.

## Next

```text
Engineer → ★ B1-disk-station-reach (D2 · motors↔frame_arm)  OR  park D0
Cursor   → draft IC only after ★ Buy shape
Claude   → implement only after IC ★
Parallel → plate-box still await §0.1 bag
```
