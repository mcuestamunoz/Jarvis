# Engineer Lock — Sourced component values → 3D envelope

**Date:** 2026-09-09  
**Authority:** Engineer (goal: *definir los valores de los componentes y usarlos para generar la geometría 3D*; GetFPV as systematic FPV retailer source)  
**Status:** ★ LOCKED — method + order. **Not** an IC. **No** `src/` until a later ★ Buy.  
**Parents:**
- [engineer_lock_geometry_3d_mapping_path.md](engineer_lock_geometry_3d_mapping_path.md) — rung **4** is the 3D-solid gap (plate L×W); `"cabe"` last
- [engineer_lock_geometry_pre_assembly_honesty.md](engineer_lock_geometry_pre_assembly_honesty.md) — envelope ≠ CAD; no STEP-in-core; no cylinder from Ø+height
- Propeller B0+B1 **CLOSED** @ **2489** · B2 **REVIEWED** @ **2497** (smoke optional)
- [engineer_validation_propeller_catalog_2026-09-09.md](engineer_validation_propeller_catalog_2026-09-09.md) — identity before fill; 40-field nested schema **out**

---

## Locked product sentence

```text
Cite a page → seed existing bag keys → bind → card text.
3D is not a second invention: it is the same Class A keys
(_geometry_from_spec already draws).
If a page does not affirm the key the glyph needs, there is no solid.
GetFPV is retailer-secondary, not a crawler and not manufacturer-primary.
```

---

## How 3D is generated today (do not rebuild)

`project_spatial_nodes` → `_geometry_from_spec`:

| Keys present | Solid |
|---|---|
| `length_mm` + `width_mm` + `height_mm` | **box** |
| `diameter_mm` **or** `diameter_in` | **disk** (inch → mm for scale only) |
| Ø + a height/hub field | **still a disk** — never a cylinder |
| anything else (mass, palas, material, hub, POPO, wheelbase, plate thickness) | **card text only** |

So: filling GetFPV hub/mass on a 5″ hélice **does not grow a new 3D primitive**. The disk was already Ø from `diameter_in`. Binding a cited 7″ / 10″ SKU **does** change disk size. That is already “using the values.”

Live 3D gap that still needs a **sourced** Class A triple (or Engineer-`declared` L×W):

- **Frame** — Rooster has `wheelbase_mm` 230, plate **thickness** 4 mm, **no** plate L×W → **no box**. Inventing 150×150 or “230×230 from wheelbase” is **forbidden**.

---

## GetFPV — how we use it

| Label | Meaning in Jarvis |
|---|---|
| GetFPV / similar shop | `AUTHORIZED_DISTRIBUTOR` / **RETAILER_SECONDARY** |
| Gemfan, EMAX, APC.com, Armattan, T-Motor | **MANUFACTURER_PRIMARY** when the page is that maker’s |

Both may appear on one row: `source_url` may stay the listing used to bind; `source_note` must say who was read and who corroborates. `identity_status: verified` is about **identity + quoted numbers**, not “we parsed GetFPV HTML in-product.”

**Extraction loop (only):** Engineer (or IC) cites **URL + bag** → Claude **re-fetches that URL** in the Buy → seed existing keys. If Cloudflare 403: independent live corroboration + disclose in `source_note` (B2 N1). Contradiction → **STOP**, do not average.

**Never:** in-product scrape, GetFPV crawler, “pasada automática de las 17 hélices” as a product feature, mixing retailer and OEM into one undifferentiated KNOW.

---

## Identity before fill (locked examples)

| Live / catalog row | GetFPV (or other) listing | Rule |
|---|---|---|
| `gemfan_5045_hbn` | Oscar Liang motor article; physical bag **UNKNOWN** | Do **not** copy Dinoblades onto HBN |
| Gemfan 5×4.5 Dinoblades Bullnose 3-blade · part **M5045BN-3BND** · GetFPV SKU 7326 · 3.6 g · hub 5 / 7 mm · PC · 3 palas | **Different identity** | New SKU only if Engineer ★ — e.g. `gemfan_5045_bn_m5045bn_3bnd`. Cursor fetched 2026-09-09: spec table matches Engineer quote. Page “Item Name” also says “5040” — quote in `source_note`, do not rename. |
| `apc_10x4_5` | 10×6EP | Already split (`apc_10x6_ep`). Do not merge. |
| `tmotor_22x6_7` | P22×6.6 | Identity debt — **do not enrich** |

Conceptual bags IDENTITY / PHYSICAL / MOUNTING / GEOMETRY / EVIDENCE stay a **wishlist**. This campaign seeds **existing** `PropellerSpec` / frame / motor keys. No nested 40-field schema in one Buy.

---

## `motor_count` vs “Rooster is 4-arm”

GetFPV/Armattan describing a 4-arm kit does **not** rewrite the project. Visor copies **N = `components.motors.motor_count`**. If the demo says 3, that is a **CLI / Continuity** correction (`declared`), same class as the 2026-09-08 R1 walk — not a catalog seed and not a default-4 in code.

---

## Two campaigns (do not collapse)

| Campaign | What it produces | 3D effect |
|---|---|---|
| **G — catalog GetFPV/OEM bags** (hélices, then other families) | Card fields on **identified** SKUs | Disk size only if `diameter_in` changes; hub/mass stay text |
| **S — Class A keys the glyph needs** | Frame L×W (and any live box still missing a triple) | **New or first solid** |

Engineer goal “usarlos para generar la geometría 3D” = **S first** for the racimo; **G** in parallel only as cited SKUs, not a 17-row blocker.

L2 retailer envelope vs L3/L4 manufacturer drawing/STEP: **holds**. STEP remains visor-only, never core SoT.

---

## Ordered next (Engineer ★ each)

1. ~~B2 Cyclone + EP seed~~ **REVIEWED** @ **2497** — smoke optional (live may stay HBN).  
2. **Investigation — plate L×W / Rooster envelope** (mapping rung 4) — [contract](investigation_contract_geometry_plate_lw_sourced_b1.md). What GetFPV vs Armattan **affirm** as footprint. No invented plate.  
3. Optional ★: new SKU Dinoblades M5045BN-3BND (GetFPV bag above) — catalog **G**, 5″ disk already.  
4. Engineer CLI (no IC): bind live SKUs that already have Ø / L×W×H so the visor **shows** cited size; set `motor_count` if the craft is four motors.  
5. IC seed plate L×W **only** after investigation + ★.  
6. `"cabe"` last. Fit QUEUED.

---

## Explicitly not this lock

In-product web crawl · Conversation Engine · cylinder · Three.js · `"cabe"` · STEP in core · version bump · dumping kit BOM (nylon standoffs, VTX plates) as fake L×W · treating ChatGPT/utm links as SoT without a live re-fetch in the Buy
