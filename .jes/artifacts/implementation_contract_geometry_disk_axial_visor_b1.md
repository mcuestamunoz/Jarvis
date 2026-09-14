# Implementation Contract — Disk axial Visor from cited dims B1 (`B1-disk-axial-visor`)

**Project:** Jarvis  
**Date:** 2026-09-14  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** READY FOR ★  
**Parents:**
- Live Board 10-min: motors/props render as **flat disks** while cards already show cited axial facts (`motors.height_mm` 33.1; `propellers.hub_thickness_mm` 6.8)
- Motor `height_mm` cited B1 **CLOSED** — [IC](implementation_contract_geometry_motor_height_cited_b1.md) · [smoke ACCEPT](engineer_smoke_geometry_motor_height_cited_b1.md) — seeded card text; **explicitly forbade cylinder** at that time
- XING-E Pro sourced B1 — `height_mm` **33.1** + `diameter_mm` **28.5** already on live 10-min
- Gemfan Hurricane 51466-3 V2 sourced B1 — `hub_thickness_mm` **6.8** + Ø via `diameter_in` already on live 10-min
- Projector `_geometry_from_spec` — box only from L×W×H; diameter → flat `disk` (ignores motor `height_mm` / prop `hub_thickness_mm` for shape)
- Fit-relations CLOSED — motors/props remain `n/a_disk` for **screening/attest** until a separate disk-station Buy
- [Fit attest all note](engineer_note_fit_attest_all_components.md) — disk-station attest = **later**, not this Buy

**Type:** Visor + projector honesty: when **both** a diameter path **and** a cited axial extent already exist on the component, emit a **`cylinder`** geometry DTO and render it with that height — **no invented mm**.  
**Not** inventing missing heights. **Not** using `stator_height_mm` as body height. **Not** inventing propeller blade / disk-of-air thickness. **Not** turning motors/props into L×W×H boxes. **Not** enabling fit AABB screening / attest for cylinders (still disk-station Buy). **Not** Situar drag for multi-copy stations. **Not** plate-box. **Not** version bump. **Not** `workspace/` mutation.

**Output:** `.jes/artifacts/implementation_report_geometry_disk_axial_visor_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**2873** · UI ≥**103**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-disk-axial-visor`** — cited axial extent → Visor cylinder |
| 2 | Supersede | Engineer ★ **lifts** the prior “no cylinder” lock from Motor height cited B1 **for this Buy only** — card-seeded `height_mm` may now drive Visor axial extent when paired with diameter |
| 3 | Shape | New geometry shape **`cylinder`**: `{ shape: "cylinder", diameter_mm, height_mm }` — both required, both from existing declared properties only |
| 4 | Motor mapping | If `diameter_mm` (or existing diameter path) **and** `properties.height_mm` present → **cylinder**; axial = `height_mm`. **Never** use `stator_height_mm` / `stator_diameter_mm` as the cylinder height or as a substitute Ø |
| 5 | Propeller mapping | If diameter path (`diameter_mm` **or** `diameter_in` → mm, same as today) **and** `properties.hub_thickness_mm` present → **cylinder**; axial DTO `height_mm` = **`hub_thickness_mm` value**. Catalog/card field name stays `hub_thickness_mm` (do not rename seeds). Copy/docs must say this axial extent is **hub / center thickness**, not full blade volume or “prop disk height” invented |
| 6 | Fallback | Diameter only → keep today’s flat **`disk`** `{ shape: "disk", diameter_mm }` (z extent 0). Axial only without diameter → **no** geometry (same as today — never invent Ø) |
| 7 | Forbidden sources | Invent mm · photo pixel-scale · `stator_height_mm` as body H · SunnySky Body Length still unseeded · invent prop blade thickness · stitch L×W from Ø to fake a box · estimate H from mass/KV |
| 8 | Screening / attest | **Out.** `screen_posed_envelope` stays box-only; fit-relations motors/props stay `n/a_disk` (or equivalent honesty) until disk-station Buy. Do **not** treat cylinder as box AABB |
| 9 | Situar / copies | Multi-copy motors/props/prop_adapter: still **not** Situar-draggable (same singleton gate as disks). Layout offsets / radial stations **unchanged** |
| 10 | Catalog | **No new catalog numbers** this Buy — only consume seeds already present. Do not add `height_mm` / `hub_thickness_mm` to SKUs that lack a cited source |
| 11 | Version | **No** bump |

**Product sentence:**

```text
Si el catálogo ya cita Ø y altura (motor) o Ø y espesor de hub (hélice),
el Visor dibuja un cilindro con esas cotas. Si falta una, sigue el disco
plano. No inventa profundidad ni abre el attest de disco.
```

### 0.1 Live facts (10-min — evidence, not to invent)

```text
motors (iflight_xing_e_pro_2207_2450):
  diameter_mm: 28.5
  height_mm: 33.1          → cylinder Ø28.5 × H33.1
  stator_height_mm: 7      → card text only; NOT cylinder H

propellers (gemfan_hurricane_mck_51466_3_v2):
  diameter_in: 5.189 (= ~131.8 mm display path)
  hub_thickness_mm: 6.8    → cylinder Ø(from diameter path) × H6.8
  (no blade thickness seeded — do not invent)
```

### 0.2 Smoke target

```text
project: 10-min-autonomía
expect: motors solid = cylinder using 28.5 × 33.1; props solid = cylinder
        using prop Ø × 6.8 hub thickness; cards still show source field names;
        flat disk remains for any diameter-only SKU in tests/fixtures
code_star: projector_cylinder + Solid3D_cylinder + type/DTO tests
```

---

## 1. You (Claude) — after ★

### 1.1 Projector — `_geometry_from_spec`

Priority (fail-closed, no invent):

1. Full `length_mm` + `width_mm` + `height_mm` → **`box`** (unchanged; wins over diameter).
2. Else diameter path + motor-style `height_mm` property → **`cylinder`** `{diameter_mm, height_mm}`.
3. Else diameter path + `hub_thickness_mm` property → **`cylinder`** `{diameter_mm, height_mm: hub_thickness_mm}`.
4. Else diameter path alone → **`disk`** `{diameter_mm}` (unchanged).
5. Else → `None`.

**Hard rules:**

- Never map `stator_height_mm` into cylinder `height_mm`.
- Never invent `hub_thickness_mm` or motor `height_mm`.
- Do not emit cylinder when either Ø or axial is missing.
- Update module docstring: prior “never a cylinder” claim is **superseded** by this Buy when both cited dims exist.

### 1.2 UI types + scale + Solid3D

- Extend `SpatialGeometry` with  
  `{ shape: "cylinder"; diameter_mm: number; height_mm: number }`.
- `solidExtentPx` / wrapper: footprint = diameter on X/Y; **z = height_mm** (not forced 0).
- `Solid3D`: honest CSS 3D cylinder from Ø×H (top + bottom faces + side) — same presentation honesty class as the six-face box. **No** invented thickness when shape is still `disk`.
- Glyph / 2D card icon: may stay disk silhouette **or** show a short cylinder cue — if cheap; do not block on glyph polish. Cards must continue to list `height_mm` / `hub_thickness_mm` as today.

### 1.3 Regressions to flip / keep

- **Flip** Motor height cited T7 (and any sibling): diameter + `height_mm` → **`cylinder`**, not flat disk.
- Keep: diameter-only → disk; L×W×H → box; `stator_height_mm` alone never creates geometry; screening still refuses non-box children.

### 1.4 Out of this Buy

- Disk-station fit attest / pose Continuity for motors/props  
- Plate-box / estimated→measured plate  
- New catalog seeds  
- Version bump / `workspace/` edits  

Do **not** bump version. Do **not** mutate `workspace/`.

---

## 2. Tests

| ID | Behavior |
|---|---|
| C1 | Motors spec `{diameter_mm: 28.5, height_mm: 33.1}` → `geometry == {shape: "cylinder", diameter_mm: 28.5, height_mm: 33.1}` |
| C2 | Motors `{diameter_mm: 27.9}` only → still `{shape: "disk", diameter_mm: 27.9}` |
| C3 | Motors `{diameter_mm: 28.5, height_mm: 33.1, stator_height_mm: 7}` → cylinder H **33.1**, not 7 |
| C4 | Propellers with `diameter_in` + `hub_thickness_mm: 6.8` → cylinder; DTO `height_mm == 6.8`; diameter_mm ≈ `diameter_in * 25.4` (existing conversion) |
| C5 | Propellers diameter only (no hub_thickness) → flat disk |
| C6 | Full L×W×H still wins as **box** even if diameter also present |
| C7 | `screen_posed_envelope` on a cylinder motors child → still non-overlap path / `child_not_box` (no AABB invent) |
| C8 | UI: `solidExtentPx(cylinder)` z > 0; disk z still 0 |
| C9 | UI: Solid3D renders cylinder branch (smoke unit / rtl as existing board patterns allow) |
| T | Full pytest green; UI suite green; package `0.4.1` |

---

## 3. Smoke (Engineer) — `10-min-autonomía`

1. Open Board → motors solid has **visible axial depth** consistent with **33.1 mm** (not paper-thin); Ø still ~28.5.  
2. Propellers solid has axial depth consistent with **6.8 mm** hub thickness (thin puck, not a tall “blade drum”).  
3. Cards still show `height_mm` / `hub_thickness_mm` with those values.  
4. `relaciones` → motors/props still honest **n/a** for box screening (no false “listo para attest”).  
5. Optional: a diameter-only fixture/SKU still flat disk.

---

## 4. Report must include

- Confirmation ★ lifts prior no-cylinder lock.  
- Exact mapping table (motor `height_mm` vs prop `hub_thickness_mm` → DTO).  
- Census: which bound live SKUs become cylinders vs stay disks (no new seeds).  
- Explicit: screening/attest unchanged.  
- Suite counts · files touched · no version bump · `workspace/` clean.

---

## 5. Cursor review gates

- [ ] No invented mm / no `stator_height_mm` as H  
- [ ] Prop axial = hub thickness only, labeled honestly  
- [ ] Cylinder only when Ø **and** axial both present  
- [ ] Flat disk preserved for diameter-only  
- [ ] Box L×W×H priority unchanged  
- [ ] Screening/attest not opened for cylinders  
- [ ] T7-class regression flipped to cylinder  
- [ ] 10-min smoke depth visible for motors + thin hub puck for props  
- [ ] `0.4.1` · no `workspace/` mutation  

---

## 6. After CLOSED

- Cola: disk-station attest remains the Buy that may later screen/attest stations.  
- Plate-box remains B0 HOLD until caliper/cite bag.  
- Optional later: glyph polish; Situar for true singleton cylinder (out unless ★).
