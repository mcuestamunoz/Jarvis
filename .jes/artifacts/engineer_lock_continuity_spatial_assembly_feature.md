# Engineer Lock — Continuity spatial assembly (product feature)

**Date:** 2026-09-10  
**Authority:** Engineer — “esto es una feature potente en Jarvis” + ask if correctly documented  
**Status:** ★ LOCKED as **product feature name** (not a new subsystem)  
**Parents:** [3D placement horizon](engineer_lock_geometry_3d_placement_horizon.md) · [3D mapping path](engineer_lock_geometry_3d_mapping_path.md) · situar walk 2026-09-09→10

---

## One sentence

```text
Jarvis sits declared physical boxes in a shared millimetre frame on the
Board 3D visor — Engineer-typed (or cited) envelopes + poses — without
the LLM inventing geometry and without splitting the BOM into N fake parts.
```

That stack is a **first-class product feature**: **Continuity spatial assembly** (Spanish product: *situar el mapa*).

---

## What it is (four honest layers)

| Layer | What the Engineer does / sees | SoT |
|---|---|---|
| **1. Envelope** | `declara … L x W x H mm` (or plate L×W + thickness) | `length_mm`/`width_mm`/`height_mm` `source=declared` (or `catalog` when cited) |
| **2. Relation** | `montado en` | guide only — **not** millimetres |
| **3. Pose** | `declara X a Δmm en ejes respecto a <origin caja>` | `declared_box_pose`; origin must be a **box**; multi-hop composition in the visor |
| **4. Visor multiplicity** | One BOM key → N solids at stations | `solidCopies` + `solidCopyOffsetsMm` — motors/props/arms/adapter (quad-X); standoffs ×4 (Main Plate corners) |

Assembly root: Main Plate box at world 0 so the X and the racimo share one origin.

Screening `"cabe"` / sobres = AABB honesty, **not** VERIFIED fit.

---

## Why it is powerful

1. **Global format** — same Continuity grammar and `ComponentSpec` fields work for any project, not only this quadrotor.  
2. **Honest automation ramp** — today: Engineer types when mute; later: sourced auto-fill **only** when a citation exists (cola #4). Never invent.  
3. **BOM stays clean** — four arms / four motors are **visor copies**, not four sibling specs.  
4. **LLM stays interface** — parse is deterministic; millimetres are typed or cited, not guessed.

---

## Documentation status (audit 2026-09-10)

| Surface | Status |
|---|---|
| Per-Buy ICs / reports / reviews / smokes | **Strong** — contracts are the engineering SoT for each slice |
| 3D placement horizon (2026-09-08) | **Stale wording** — still says “más tarde colocar”; pose + multi-hop + root + kit/plate subjects are already shipped |
| VISION § Geometry spatial | Points at horizon; **did not name** the feature until this lock |
| System map / ARCHITECTURE / README / VISION | **Synced @ v0.4.0** (2026-09-10 doc pass) |
| This lock | **Canonical product name** — point ICs and VISION here |

**Verdict:** the *capability* was built correctly; the *product packaging* in living docs was incomplete. This file closes that gap.

---

## In scope / out of scope (feature boundary)

**In:** declared/cited envelopes · Continuity pose · multi-hop · assembly root · visor copies/stations · kit/plate/arm subjects as shipped by ICs  

**Out (still):** Conversation Engine inventing mm · 230-as-box · disk-origin pose · `"cabe"` as VERIFIED · CAD/FEA · auto-pose without citation · N BOM clones for arms/motors

---

## Next (does not redefine the feature)

- A1–B3 arms / loose / adapter X / standoff corners — **CLOSED** path  
- Board **drag / resize → declared pose+envelope** — Engineer concept ([note](engineer_note_board_drag_place_concept.md)); investigation when ★  
- B4 `standoff_count` · plate label noun · #4 sourced dims  

Keep `declara…` grammar; UI drag is another input to the **same** writers — not a second SoT.

---

## Explicit non-goals

New architectural subsystem · moving SoT into the LLM · collapsing product A (box racimo) and B (X silhouette) without a dedicated ★
