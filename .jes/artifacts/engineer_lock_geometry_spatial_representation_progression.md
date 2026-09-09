# Engineer Lock — Geometry Progression Lock B1 (visualización declarativa)

**Date:** 2026-09-07  
**Authority:** Engineer  
**Status:** ★ LOCKED — B1 capability = **visualización declarativa only**  
**Supersedes (for next work):** informal “glyphs before assembly” chat; parent axis still [engineer_lock_geometry_physical_representation_axis.md](engineer_lock_geometry_physical_representation_axis.md)

## Locked claim

> Jarvis may evolve from declared physical KNOW toward progressive visual representation of real components.  
> The **first Geometry capability** after `representar` is exclusively **declarative visualization**: a 2D / simple-3D **glyph** derived from physical dimensions that are **already known and verified**.  
> A glyph answers: **what envelope/shape the component has** — not where it is mounted, nor whether it fits.

**Frontier (locked):**

```text
“Tiene geometría”  ≠  “está ensamblado”
```

## Progression (do not flatten)

```text
KNOW
  ↓
REPRESENTAR                 ← largely shipped (Battery/Motor/ESC/FC text dims)
  ↓
VISUALIZAR                  ← ★ B1 next capability (glyphs)
  ↓
ASSEMBLY ESPACIAL           ← later ★ (pose + mounted_on)
  ↓
COMPARAR / VERIFICAR        ← later ★
  ↓
CAD / MEASURE / FEA         ← later ★ — not early Geometry
```

Board remains a **projection of `ProjectState`**. No second geometric model of record.

## B1 does **not** introduce

- spatial position  
- orientation / pose  
- `mounted_on` / assembly relations  
- intersection detection  
- clearance / fit  
- structural validation  
- parametric CAD  
- manufacturability or mountability claims  

## Product sentence B1 must enable (honest)

> “I know what the component is, and I know what **declared physical volume** it occupies.”

Not: “this fits” / “this is assembled.”

## Relationship to shipped work (@ `0.3.8` · suite **2336**)

| Shipped | Role |
|---|---|
| Catalog/identity dims (Battery, Motor, ESC, FC) | Fuel for glyphs |
| Board + B3 slots | Canvas; cards still text `_fields` today |
| Sensors BOM honesty | Orthogonal claim ladder |

## Next

Glyphs B1 **shipped** (suite **2344**). Assembly **relation** CLOSED 2026-09-08. Visualizar-3D **CLOSED**. Declared box-local pose **writer** CLOSED @ **2438**. Continuity pose B1 **CLOSED** @ **2456** + ACCEPT.

**Product horizon (Engineer 2026-09-08):** 3D solids at declared scale → click opens today’s card → **place in space** (`mounted_on` as guide; declared box-local offsets) → later `"cabe"` vs that spatial situation.

Lock: [engineer_lock_geometry_3d_placement_horizon.md](engineer_lock_geometry_3d_placement_horizon.md). Reds **CLOSED**. Queue: [3D mapping path](engineer_lock_geometry_3d_mapping_path.md) — rung 1 Scene3D-from-pose **CLOSED**; rung 2 first cut (wheelbase on spec) **CLOSED**. Fit still QUEUED.

This B1 lock still holds: a glyph (2D or later 3D) answers **what envelope the component has**, not where it is mounted, nor whether it fits.
