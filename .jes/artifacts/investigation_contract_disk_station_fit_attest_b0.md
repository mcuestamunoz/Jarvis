# Investigation Contract — Disk-station fit / attest (`B0-disk-station-fit-attest`)

**Project:** Jarvis  
**Date:** 2026-09-15  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** **Claude Code** (after Engineer ★)  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_disk_station_fit_attest_b0.md`

**Status:** INVESTIGATION REVIEWED — **PASS WITH NOTES** · await Engineer ★ Buy shape **D2** (`B1-disk-station-reach`) or park **D0**  
**Report:** [investigation_report_disk_station_fit_attest_b0.md](investigation_report_disk_station_fit_attest_b0.md)  
**Review:** [investigation_review_disk_station_fit_attest_b0.md](investigation_review_disk_station_fit_attest_b0.md)  
**Parents:**
- Fit attestation B1 **CLOSED** — box↔box only; gate `screen_posed_envelope == overlap` + human `declaro verificado`
- Fit-relations checklist **CLOSED** — motors/props stay **`n_a_disk`** by design
- Disk-axial Visor **CLOSED** — cylinder render ≠ screening box; [IC](implementation_contract_geometry_disk_axial_visor_b1.md) lock #8 forbids treating cylinder as AABB
- [engineer_note_fit_attest_all_components.md](engineer_note_fit_attest_all_components.md) — disk-station = Buy when ★
- Path N (disk-as-pose-origin) **B0 HOLD** — schema-impossible; **do not reopen** as solution here
- Plate-box **parallel track** — estimated plate still blocks stack attest; this B0 is about **motors/props stations**, not plate L×W
- Ladder: [engineer_lock_geometry_spatial_representation_progression.md](engineer_lock_geometry_spatial_representation_progression.md)

**Type:** Read-only investigation — define the **minimum honest** evidence class for screening and/or attesting **one motor station** (and optionally one prop↔motor pair) without CAD, without inventing mm, without N independent seals.  
**Not** an IC. **Do not implement.** **Do not** weaken box-only `screen_posed_envelope` by silently treating cylinders as boxes. **Do not** reopen Path N. **Do not** invent stator/blade thickness as body height.

**Checkpoint:** package **`0.4.1`** · suite ≥**2945** · UI ≥**105**

---

## 0. Role split

```text
Engineer  → ★ this B0 (and fill plate-box bag on parallel track if ready)
Cursor    → this contract; review; IC only after ★ on recommended Buy shape
Claude    → investigation_report_disk_station_fit_attest_b0.md only
```

---

## 1. Why this exists

Shipped today:

```text
box child + box origin + complete pose
        → screen_posed_envelope (AABB)
        → optional human attest

motors / propellers
        → often disk / cylinder Visor
        → fit-relations: n_a_disk
        → no cabe / no declaro verificado
```

Product want (Engineer 2026-09-15): extend the **same honesty ladder** to disk stations — one seal per station family, not four fake BOM clones.

Wrong answers:

```text
· Treat cylinder mesh as box AABB and call it screening
· Attest on Visor pixels / Situar drag of multi-copy solids
· N seals (one per motor copy)
· Path N — disk as pose origin
· Invent hub/stator height to force a box
· Rename n_a_disk → VERIFIED
```

Right question:

> On the **live code + live projects**, what declared facts (if any) would let Jarvis run a **deterministic station screen** and/or a **human attest** for `motors↔frame_arm` / `propellers↔motors` without lying — and what is the **minimum B1** (or B0 leave forever `n_a_disk`)?

---

## 2. Locked stances

1. **Box screening stays box screening.** Do not change `screen_posed_envelope` to accept disks/cylinders unless the report recommends a **new, distinctly named** helper with distinct copy.  
2. **Cylinder Visor ≠ geometry proof.** Axial cylinder is display from cited Ø + height/hub facts — not an attest envelope.  
3. **One station seal** — same spirit as Situar singleton (`solidCopies` / one fingerprint for the family), not four attestations.  
4. **Fail closed** — missing arm length, missing motor pose/station, estimated dims on either side → no screen upgrade / no attest.  
5. **`mounted_on` alone is not fit** — attachment declaration ≠ overlap/containment proof (same as box path).  
6. **ASSEMBLY_READY untouched** unless Engineer later ★ a separate Buy.  
7. **Out:** CAD/FEA/STEP · Conversation Engine · Optimization · HD-* · plate-box invent · Path N reopen · version bump · `workspace/` mutation  

---

## 3. You (Claude) — report sections

### A. As-is code map (cite file:line)

- Why motors/props get `n_a_disk` in `fit_relations_assist`
- What `screen_posed_envelope` returns for disk/cylinder children
- How Visor places motor/prop stations (arm radial / disk axial) — presentation vs engineering frame
- How fit attestation fingerprint + `solidCopies` gate work today
- Whether any Continuity pose exists on live motors/props (read-only census: 10-min, 5-min, vigilancia if present)

### B. Candidate evidence classes (menu — lean one)

| ID | Idea | Evidence class | Lean |
|---|---|---|---|
| D0 | Keep `n_a_disk` forever until MEASURE/CAD | Honest ceiling | must present |
| D1 | Declared **proxy box** at station (Engineer-declared L×W×H for motor body / prop hub only) + pose vs arm/motor origin → reuse AABB + attest | Same as box path | |
| D2 | **Radial station rule** — compare declared arm length / mount tip vs motor station offset (1D/2D), not full AABB | New deterministic rule, new copy | |
| D3 | Human attest **without** screen (“declaro estación OK”) gated only on mount+pose present | Weaker than box attest — high lie risk | default OUT unless strongly justified |
| D4 | Other (name) | … | |

Recommend **one** primary Buy shape (or D0). Do not design full IC API — name writers/phrases only.

### C. First case scope

Lock recommendation to **one** pair for a future B1:

- Prefer **`motors` ↔ `frame_arm`** (station on arm), **or**  
- **`propellers` ↔ `motors`** if motors already have stronger declared facts  

Say which, and what §0.1 bag a future IC would need (cited Ø/H already enough? need Engineer proxy box?).

### D. Interaction with plate-box / estimated

Explicitly: disk-station work **does not** unblock FC/ESC/battery attest blocked by `estimated_temporary` plate. Orthogonal.

### E. Explicitly out

Path N · invent mm · N seals · cylinder-as-box · ASSEMBLY_READY flip · plate invent

---

## 4. Done when

- [x] ★  
- [x] Report at required path · A–E answered with live citations  
- [x] Single recommended Buy **or** D0 hold — lean **D2**  
- [x] Cursor investigation review — PASS WITH NOTES  
- [x] Engineer ★ locks B1 IC shape (Cursor drafts IC) **or** parks — IC drafted: [implementation_contract_disk_station_reach_b1.md](implementation_contract_disk_station_reach_b1.md) · await ★ implement  

---

## 5. Handoff

```text
Engineer → ★ B0-disk-station-fit-attest
Claude   → investigation_report_disk_station_fit_attest_b0.md
Cursor   → review → (if Buy) IC B1-disk-station-…
Engineer → ★ implement only after IC
```
