# Investigation Contract — Assembly kit template (novice build vs 4-block architecture)

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_assembly_kit_template_b0.md`

**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · wait Engineer ★ Buy shape (`B1-min` recommended)  
**Parents:**
- [engineer_lock_assembly_kit_template.md](engineer_lock_assembly_kit_template.md)
- Plate L×W **REVIEWED B0** — [review](investigation_review_geometry_plate_lw_sourced_b1.md) — **out of this contract**
- `src/jarvis/core/system_architecture_catalog.py` — `SYSTEM_ARCHITECTURES` / `BLOCK_TO_COMPONENTS`
- Spatial Board slots — honest absence of **expected** keys
- Structure B — curated `plates[]` / arms as `parent_key=frame` BOM lines; full Included kit **out**
- Fit / Conversation Engine / GetFPV crawler / 3D cylinder — **out**

**Type:** Product-boundary investigation. **Not** an IC. **Do not implement. Do not change `BLOCK_TO_COMPONENTS`. Do not seed catalog.**

**Checkpoint:** package **`0.3.8`** · suite **2497**

**You are Claude Code.** Write the report only.

---

## 0. Role split

```text
Engineer  → novice should see a real assemble-template; unknown → pending
Cursor    → this contract; review; IC only after ★ on Buy shape
Claude    → investigation_report_assembly_kit_template_b0.md
```

---

## 1. Why this exists

Engineer: starting by growing catalog/3D **as we go** is less accurate than a **realistic initial structure** (adapters, controllers, wiring, …) that Jarvis **asks for as they become established**, leaving unknowns **pending**.

Today `dron` architecture expects seven keys: `motors`, `propellers`, `esc`, `battery`, `frame`, `flight_controller`, `sensors`. Slots only cover **that** set. A prop adapter or XT60 is invisible — not pending, **absent from the template**.

Wrong next step:

```text
volcar Included del Rooster a componentes · 20 keys en BLOCK_TO_COMPONENTS
· LLM shopping list · crawler GetFPV · cajas 3D de tornillos
```

Right question:

> What is the **minimum honest template** so a novice sees “this build still needs X” without turning Jarvis into a commercial BOM engine or a Conversation Engine — and without lying that the 4-block energy architecture is already a full kit?

---

## 2. Locked stances

1. Blocks stay **functional views**, not ownership (existing DA-MOTORS). Do not propose 1:1 “every SKU line = new block.”  
2. **Pending** must reuse slot / Continuity / BOM incomplete — not a new dialogue subsystem.  
3. Unknown ≠ invented SKU. A pending adapter is a **hole**, not a guessed part number.  
4. Frame kit extras that are **parts of the bound frame** (HD plate, VTX plate, standoffs) are Structure B **children**, not new `system_blocks`. Do not reopen plate L×W.  
5. Do not scrape. Quote live tree + existing locks.  
6. P-energy claims (hover, autonomy) must remain computable if the kit template grows; do not silently widen Structure/Propulsion PASS.

---

## 3. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| `SYSTEM_ARCHITECTURES["dron"]` + `BLOCK_TO_COMPONENTS` | Exact expected keys |
| Board slot emission | Which missing keys become `kind: "slot"` |
| Continuity next-step | What it can ask vs cannot |
| BOM `build_component_bom` | Incomplete vs not-in-template |
| Structure B children | What already hangs under `frame` |
| Create / architecture session | What the user is asked to declare **first** |

Live demo: if workspace readable, list declared keys vs slot holes. If not, say so.

---

## 4. Report sections (required)

### A. Two products

P-energy vs P-kit. What a novice **cannot** see today.

### B. Candidate Buys (ranked, one default)

At least:

| ID | Shape | Notes |
|---|---|---|
| **B0** | Keep 4-block / 7 keys; kit is a **later** product | Honesty: Board is not a build list |
| **B1** | Add a **small** named pending set to `dron` (cap N — you propose N≤8) | Keys must be **physical entities**, not verbs. Cite why each is load-bearing for “montar” |
| **B2** | Bound-frame **Included** → extra **BOM children** under `frame` (pending if not in seed) | Not new architecture keys. No L×W invention |
| **B3** | Doc-only: Continuity sentence “this architecture is not a full kit” | No schema |

Reject a 40-line FPV shopping list as one Buy.

### C. Acquisition

How Jarvis “asks as you go” using **existing** DEFINE/Continuity/IDLE — no Conversation Engine. Unknown → leave pending (slot or BOM `✗`).

### D. Out of scope

Plate L×W IC · helix GetFPV census · STEP · `"cabe"` · in-product scrape · version bump.

---

## 5. Done when

- [ ] Report written; one **default lean**  
- [ ] No `src/` / library edits  
- [ ] Explicit: what stays P-energy vs what would be P-kit

---

## Explicitly not this investigation

Implement template · change `BLOCK_TO_COMPONENTS` · seed adapters · invent Rooster millimetres
