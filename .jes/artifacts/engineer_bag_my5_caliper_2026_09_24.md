# Engineer bag — HGLRC MY5 caliper (2026-09-24)

**Authority:** Engineer, frame in hand (`hglrc_my5_5in`).  
**Status:** caliper numbers **seeded** on catalog `hglrc_my5_5in` (Path E). Schema add: optional plate L×W, arm L×W, standoff Ø.  
**Not** 225×200 copied onto any plate. **Not** bottom-plate L×W invented.

## Middle plate (`frame_plate_2`) — placa base 3 mm

```text
authority: caliper
part: placa base — Engineer name. Thickness 3 mm = catalog Middle plate.
measured_mm:
  length_mm: 170
  width_mm: 45
  height_mm: 3
```

Ordinal **not** remapped. This is `frame_plate_2`, not the assembly-root key.

## Top plate (`frame_plate`)

```text
authority: caliper
part: placa de arriba — Top plate
measured_mm:
  length_mm: 161
  width_mm: 42
  height_mm: 2
```

This is the assembly-root box (first ordinal). Grosor 2 mm already matched the cited Top plate.

## Bottom plate (`frame_plate_3`)

Thickness 2 mm cited. **L×W unknown** — not invented.

## frame_arm — bounding box (option A)

```text
authority: caliper
part: one arm
measured_mm:
  length_mm: 125
  width_mm: 20
  height_mm: 5
note: curvature at the root. Straight box does not describe that flare.
```

Seeded as one 125×20×5 box. Flare stays a note. Option B (two boxes) needs its own later ★.

## frame_standoff

```text
authority: caliper / count in hand
count: 8
measured_mm:
  height_mm: 30
  diameter_mm: 6
```

**Ø 6 is outer diameter**, not the GEP `M3×6×H` thread trap. Bind glyph = **cylinder** (Ø×H). `count=8` is a card fact. Taller copies of 8 cylinders = [`B1-standoff-cylinder-layout`](implementation_contract_geometry_standoff_cylinder_layout_b1.md) **COLA** (Engineer 2026-09-24: puntos de perímetro a corregir más adelante; no ACCEPT).

## Honesty

- Root `body_length_mm`/`body_width_mm` **225×200** = assembled-craft XY envelope (retailer Dimensions). **Not a plate.** Keep as the general size the **mounted parts together** should match. No automatic AABB check yet.
- Live Board/grafo: children appear after a MY5 **rebind**. Workspace JSON is not silently rewritten.

## FC+ESC conjunto (2026-09-24)

```text
authority: caliper
part: ESC + FC as one sandwich (not each board)
measured_mm:
  length_mm: 46
  width_mm: 46
  height_mm: 18
note: Engineer wrote "18 mm de ancho" as the third number — recorded as sandwich HEIGHT. Correct if that 18 was a different axis.
```

Seeded on the MY5 **frame root** as `fc_esc_stack_*` (46×46×18). Not copied onto `flight_controller` / `esc` (would draw two sandwiches). Not `max_stack_height_mm` (that is frame clearance, Rooster 22 mm). No HGLRC FC/ESC SKU this pass — identity of the desk stack stays F460/F405 in notes until those rows exist.

## FC / ESC height topes (2026-09-24, later)

Engineer: plates have chip/standoff reliefs — a “real” PCB height is not a useful number. **Define visor topes, 23 mm each.**

```text
authority: Engineer tope (not caliper)
part: flight_controller, esc — each board's visor height cap
measured_mm:
  height_mm: 23
note: 23 = half of the conjunto's 46 mm XY, used as a round cap. NOT half of the 18 mm sandwich height. NOT Skystars/SpeedyBee catalog. Chips and posts make a single “true” H undefined; Taller draws the tope as the brick.
```

Honesty:
- **18 mm** stays `fc_esc_stack_height_mm` — caliper of the lump sandwich.
- **23 mm** is `estimated_temporary` visor H per board — a cap so Taller has a box. Not a cited thickness. Fit/`cabe`/verificado stay blocked (same gate as any estimated dim).
- 23+23 is **not** a claim that the stack is 46 mm tall.
- Catalog `library/esc/_datos.json` (Skystars still no H; SpeedyBee keeps cited 8 mm) **untouched**.
- SpeedyBee-bound 5-min project keeps catalog 8 mm — do not overwrite a cited H with this tope.
- FC has no estimated-H Continuity valve yet (envelope grammar excludes FC). Live FC boxes stay their declared H (7.8 / 12) until a twin writer exists. ESC valve already exists: `declara el esc estimado 23 mm`.
