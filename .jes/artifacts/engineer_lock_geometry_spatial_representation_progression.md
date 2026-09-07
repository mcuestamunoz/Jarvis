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

1. Investigation: [investigation_contract_geometry_board_glyph_vocabulary.md](investigation_contract_geometry_board_glyph_vocabulary.md)  
2. Report → review → Engineer ★ Buy B1 → IC → implement → Board shows glyphs  
3. **No code** until ★ Buy after investigation
