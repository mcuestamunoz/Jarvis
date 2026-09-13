# Investigation Contract — Fit VERIFIED (beyond AABB screening)

**Project:** Jarvis  
**Date:** 2026-09-10  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_geometry_fit_verified_b0.md`

**Status:** INVESTIGATION REVIEWED — **PASS WITH NOTES** · Engineer ★ **`B1-attest`** · IC [implementation_contract_geometry_fit_attestation_b1.md](implementation_contract_geometry_fit_attestation_b1.md)  
**Report:** [investigation_report_geometry_fit_verified_b0.md](investigation_report_geometry_fit_verified_b0.md)  
**Parents:**
- Engineer ★ post-`v0.4.1` — **Fit VERIFIED** next ([IMPLEMENTATION_TASKS](../docs/IMPLEMENTATION_TASKS.md) PRIORIDAD)
- Screening **CLOSED** + smoke **ACCEPT**: [IC](implementation_contract_geometry_assembly_fit_cabe_b1.md) · [smoke](engineer_smoke_geometry_assembly_fit_cabe_b1.md) · helper `pose_envelope_screening.py`
- Ladder: [engineer_lock_geometry_spatial_representation_progression.md](engineer_lock_geometry_spatial_representation_progression.md) — **COMPARAR / VERIFICAR** after assembly espacial
- Horizon: [engineer_lock_geometry_3d_mapping_path.md](engineer_lock_geometry_3d_mapping_path.md) §5 `"cabe"` CLOSED — this investigation is the **next** compare rung, not a re-open of screening
- Historical stub: [implementation_contract_geometry_assembly_fit_compare.md](implementation_contract_geometry_assembly_fit_compare.md) — **still do not implement that file**; any READY IC must be a **new** filename after this investigation + Engineer ★
- Board Situar **CLOSED** @ `v0.4.1` (C-113) — poses may now be set from Scene3D; still not a fit proof
- Plate L×W **B0** — Rooster still no frame box
- Frame class LEVEL A (`GAP-FRAME-PROP-SIZE`) — **orthogonal**; do not merge
- **Out of this investigation:** IDLE part count · N≠4 standoffs · sourced #4 · LLM pending deactivate · HD-* · CAD/FEA/STEP-in-core · Conversation Engine · System Optimization

**Type:** Minimum honest **VERIFIED** investigation — what (if anything) may upgrade a screening fact without CAD theater.  
**Not** an IC. **Do not implement. Do not bump version. Do not invent millimetres. Do not flip `ASSEMBLY_READY` from AABB alone.**

**Checkpoint:** package **`0.4.1`** · suite **2669** · UI **80** · tag `v0.4.1` / `checkpoint-board-situar`

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ locks Buy before any IC.

---

## 0. Role split

```text
Engineer  → Fit VERIFIED as next product rung (post Board Situar)
Cursor    → this contract; review; IC only after ★ on Buy shape
Claude    → investigation_report_geometry_fit_verified_b0.md
```

---

## 1. Why this exists

Shipped (B1-min screening):

```text
declared_box_pose (complete x,y,z) + two boxes
        ↓
pose_envelope_screening  — AABB center-to-center, single-level
        ↓
Board "sobres" + IDLE "cabe"  →  "… screening, no verificado"
        ↓
PASS / ASSEMBLY_READY / hover  unchanged
```

Product copy **explicitly forbids** reading that as a fit proof. The ladder still has **COMPARAR / VERIFICAR**. Engineer named **Fit VERIFIED** as PRIORIDAD after `v0.4.1`.

Wrong next step:

```text
· Rename "screening, no verificado" → "VERIFIED" because AABB overlap exists
· Flip ASSEMBLY_READY / Structure PASS from AABB alone
· Card-lane / localStorage / Scene3D px as proof
· Multi-hop compose with yMm??0 / CSS Y↔Z (visor math)
· Invent Rooster L×W so something “fits in the frame”
· Clearance/FEA/STEP theater · Conversation Engine
· Re-open screening IC or implement the 2026-09-07 stub filename
```

Right question:

> On the **live tree + live code**, what evidence exists beyond AABB screening, and what is the **minimum honest first Buy** — including **B0 leave VERIFIED forever-pending until MEASURE** — that lets Jarvis say something is **verified** without lying?

---

## 2. Locked stances

1. **Screening stays screening.** Do not weaken or delete the “screening, no verificado” honesty on the existing AABB path unless the Buy **adds a distinct, stronger criterion** and new copy. Renaming is forbidden.  
2. **VERIFIED is a claim ladder rung**, not a synonym for overlap. Report must define what would make the claim true in Jarvis (evidence class), or recommend never using the word.  
3. **Fail closed.** Missing envelope, incomplete pose, disk-as-cylinder, mute plate origin → no VERIFIED.  
4. **Same SoT.** Any Buy writes/reads `ProjectState` / existing writers or a thin new deterministic helper — no parallel fit schema in the UI.  
5. **Not visor math.** Never import/port `scene3dLayout.ts` Y↔Z or omitted-axis→0 into an engineering verdict.  
6. **Not mount-as-fit.** `mounted_on` ≠ pose origin ≠ verified seating.  
7. **Rooster has no box.** Plate L×W B0 holds — do not invent a frame prism to verify against.  
8. **Disk stays disk.**  
9. **ASSEMBLY_READY / PASS byte-identical** unless Engineer ★ explicitly buys a Gap/readiness change — default recommendation must assume **unchanged**.  
10. **No version bump in the investigation. No Conversation Engine. No Three.js rewrite.**

---

## 3. Baseline to inventory (cite live tree · `file:line`)

| Surface | Check |
|---|---|
| `src/jarvis/core/pose_envelope_screening.py` | Status enum, AABB rule, forbidden-token copy |
| `spatial_board.py` Board `sobres` field | How screening surfaces today |
| `orchestrator._try_handle_cabe_screening` | IDLE path; what “cabe” returns (must still be screening text) |
| `project_closure.py` / `engineering_readiness.py` | Existing bans on VERIFIED / “cabe” as proof; any Gap that could honestly grow |
| Continuity / Structure A LEVEL A | Class screening ≠ geometric VERIFIED (quote) |
| Live demos (read-only `workspace/`) | Which posed **complete** box–box pairs exist on `autonomía-de-5min` / `10min` after Situar? Counts only — do not mutate |
| Board Situar / C-113 | Confirm pose can be completed from UI; still not VERIFIED fuel by itself |
| Ladder locks | Quote COMPARAR/VERIFICAR vs CAD/MEASURE placement |

Do **not** mutate `workspace/`. Read-only.

---

## 4. Report sections (required)

### A. Screening as-is (evidence)

What the helper proves and what it **explicitly does not**. Quote copy + status table.

### B. Live complete posed box–box pairs

Count on the two demos (and note Situar may have changed 5min). Incomplete vs complete. Disks out.

### C. Candidate meanings of VERIFIED (honest menu)

For **each** candidate: evidence required · what code would touch · risk of lying · lean in/out.

Minimum menu (add only if needed):

| ID | Sketch |
|---|---|
| **V0** | Never ship VERIFIED until MEASURE/CAD lab — keep screening forever |
| **V1-attest** | Engineer-attested mark on a posed pair (“declaro verificado”) — human evidence, not better geometry |
| **V1-margin** | Declared clearance / inset mm beyond AABB (still declared numbers) |
| **V1-compose** | Multi-hop AABB in declared mm (still screening unless criterion strengthens) |
| **V1-faces** | Declared mating faces / seat axes (declared, not STEP) |
| **V-forbidden** | Rename overlap→VERIFIED · ASSEMBLY_READY from AABB · visor px · invent Rooster box |

### D. Recommended Buy (one)

Exactly one of: **`B0`** | **`B1-attest`** | **`B1-margin`** | **`B1-compose`** | **`B1-faces`** | **other named ≤1 sentence**.  
If not B0: product sentence + non-goals + which modules.  
State whether `ASSEMBLY_READY` stays untouched (default **yes**).

### E. Explicitly out

CAD · FEA · STEP-in-core · Conversation Engine · System Optimization · HD-* · plate L×W invention · N≠4 / IDLE count / sourced #4 · re-implementing screening · stub filename `implementation_contract_geometry_assembly_fit_compare.md`

---

## 5. Definition of done

- Report path above exists; answers A–E; cites `file:line` / live keys.  
- Single recommended Buy.  
- No `src/` / `ui/` / `library/` edits for this investigation.  
- Cursor Investigation Review → Engineer ★ → only then a **new** IC filename.

---

## Forbidden

```text
implement · bump version · rename screening→VERIFIED · ASSEMBLY_READY from AABB
· scene3dLayout engineering · invent Rooster L×W · Conversation Engine
· implement implementation_contract_geometry_assembly_fit_compare.md
```
