# Next steps — Assembly kit template (after investigation review)

**Date:** 2026-09-09  
**Authority:** Cursor (JES) after reviewing Claude’s report  
**Status:** Ordered queue — kit **CLOSED**. `"cabe"` B1-min **CLOSED** + ACCEPT.  
**Parents:**
- [investigation_review_assembly_kit_template_b0.md](investigation_review_assembly_kit_template_b0.md) **PASS WITH NOTES**
- [investigation_report_assembly_kit_template_b0.md](investigation_report_assembly_kit_template_b0.md)
- [engineer_lock_assembly_kit_template.md](engineer_lock_assembly_kit_template.md)
- Plate L×W **B0** (Rooster no footprint) — [review](investigation_review_geometry_plate_lw_sourced_b1.md)

This is **not** an Implementation Contract. It is the work order so the next IC has a single shape.

---

## 0. What is now true

```text
P-energy  = 4 blocks, 7 keys, hover/autonomy/PASS.
P-kit     = “what do I still need in my hands to bolt this.”
Today P-kit is empty: adapters/connectors/harness are not pending — they
do not exist as a category. The live demo can look 4/4 complete and still
not be a build.
```

3D / GetFPV hélices / plate L×W **do not fix this**. Growing catalog into the current 7 holes never creates an eighth hole.

---

## 1. Gate — Engineer ★ one line

Reply with **one** of:

| ★ | Meaning | Then Cursor |
|---|---|---|
| **`B1-min`** (recommended) | Two pending kit entities; visibility without widening PASS | Write IC; Claude implements |
| **`B3 only`** | Continuity disclaimer, no new keys | Tiny IC / doc |
| **`B0 park`** | Keep 7-key product; kit later | PRIORIDAD returns to geometry/`cabe` |
| **`B1-naive`** | Add keys onto `propulsion`/`energy` | **Refuse** — widens composite PASS |

Do not ★ “all adapters, VTX, RX, camera, wiring this week.”

---

## 2. If ★ `B1-min` — first Implementation Contract (only this Buy)

### Product sentence

```text
Tras confirmar arquitectura dron, el Board muestra dos huecos más:
power_connector y signal_harness — slot “no declarado”.
Continuity puede pedir “Define power_connector” cuando el BOM los marca
missing. No propone XT60 ni ningún SKU. Hover / Structure / Propulsion
PASS no cambian. Architecture sigue 4/4 sobre las 7 claves de siempre.
```

### Keys (locked for this IC)

| Key | What the novice is missing | Not |
|---|---|---|
| `power_connector` | Battery ↔ ESC power path (XT60-class **as identity later**, not this IC) | Not the battery, not the ESC |
| `signal_harness` | FC ↔ ESC signal when they are separate boards | Not an AIO SKU invention |

**Out of this IC:** `prop_adapter` (conditional = later), VTX, RX, FPV camera, screws, nylon standoffs, wiring as a bag of SKUs.

### Mechanism (locked)

New data-only registry, **not** a new dialogue engine:

```text
KIT_TO_COMPONENTS = {
  "dron": ["power_connector", "signal_harness"],
  "uav":  ["power_connector", "signal_harness"],  # same aerial family
}
# robot/coche/rover: empty this Buy
```

| Consumer | Reads kit keys? |
|---|---|
| Board slots | **Yes** — extra slots on a declared `dron`/`uav` (lane: prefer **energy** for connector, **control** or propulsion for harness — IC picks one lane each, first-match dedupe) |
| `build_component_bom` `expected_keys` | **Yes** → `missing` until declared |
| Continuity rank 4 | **Yes** (via BOM) — after physics/sim ranks |
| DEFINE_MISSING / IDLE declare-component | **Yes** — orchestrator missing-key helper must union kit keys when domain is dron/uav |
| `_block_progress_status` composite/component | **No** |
| ERF propulsion / energy / structure / electronics predicates | **No** |
| Hover / `resolve_operating_point` / autonomy math | **No** |

`uav` shares the aerial template; do not silently add kit keys to `robot`.

### Completeness of a declared kit hole

When the user says they have a connector (free text, no SKU): writer creates a **root** `ComponentSpec` (`completeness` low/declarative allowed). Same as an empty FC card — **identity optional**. No catalog family required this Buy. No `_geometry_from_spec` (no L×W×H → no solid). Card text only.

Unknown → leave the slot. Never invent XT60.

### Tests the IC must name

1. Dron project, 7 keys present, kit absent → two `kind: "slot"` nodes; architecture progress **4/4 unchanged**.  
2. Same → BOM `missing` contains `power_connector` and `signal_harness`; propulsion/energy block status **byte-identical** to fixture without kit registry.  
3. Continuity: with physics not blocking, next step names one kit key (or B3 sentence + key).  
4. DEFINE/IDLE can target `power_connector` without opening a new block wizard.  
5. Twin: hover/autonomy/Structure PASS / ERF energy+propulsion **unchanged** vs pre-IC fixture.  
6. `robot` architecture: **zero** kit slots.  
7. Declaring `power_connector` (stub) removes its slot; does **not** complete propulsion.

### Files (expected)

| Path | Change |
|---|---|
| `system_architecture_catalog.py` | `KIT_TO_COMPONENTS` (+ tiny getter) |
| `spatial_board.py` | slots from union |
| `project_closure.py` | BOM expected union |
| `orchestrator.py` | DEFINE missing union (dron/uav only) |
| `project_continuity.py` | optional B3 clause in `next_why` / situation — **not** a new rank |
| `tests/test_assembly_kit_template_b1.py` | T1–T7 |
| `ui/` | **empty** if `kind: "slot"` already paints |

**No** catalog JSON, **no** `PropellerSpec` keys, **no** version bump, **no** plate L×W, **no** cylinder.

### B3 in the same IC (recommended)

One Continuity phrase when any kit key is `missing`:

```text
La arquitectura 4/4 no es la lista de montaje. Falta declarar: …
```

If Engineer ★ `B3 only`, ship **only** that sentence (weaker: still no named holes on the Board).

---

## 3. After B1-min **CLOSED** (later ★, not this IC)

Ordered, do not skip:

| # | Buy | Why later |
|---|---|---|
| A | **B2 seed** Rooster HD Cam + Rear VTX plates (Armattan Included, thickness only) | **CLOSED** [smoke](engineer_smoke_geometry_rooster_included_plates_b2.md) **ACCEPT** |
| B | `prop_adapter` ask after hélices (temporal gate; no hub/shaft inference) | **CLOSED** [smoke](engineer_smoke_kit_prop_adapter_ask_b1.md) **ACCEPT** |
| C | FPV `vtx` / `receiver` as kit keys (N+2) | Overlap with `sensors` — investigate before adding |
| D | Catalog SKUs for XT60 / harness **after** holes exist | **CLOSED** [smoke](engineer_smoke_kit_connector_harness_skus_d.md) **ACCEPT** |
| E | Engineer-**declared** Rooster plate L×W if a box is wanted | Geometry; pages have no footprint |
| F | `"cabe"` / fit | **CLOSED** [smoke](engineer_smoke_geometry_assembly_fit_cabe_b1.md) **ACCEPT** |
| G | GetFPV helix census / Dinoblades new SKU | Catalog G, not P-kit |

---

## 4. Explicitly parked (do not pull into B1-min)

- Naive append to `BLOCK_TO_COMPONENTS["propulsion"]`  
- New `assembly_hardware` **component** block on `dron` (would make architecture 5/5 and gate complete)  
- Param-type dummy block with empty `param_reason`  
- LLM shopping list / GetFPV Included scrape  
- 3D solids for connectors  
- Conversation Engine  
- Conditional slot engine  
- `motor_count` / quad-X silhouette  

---

## 5. Suggested calendar (one ★ at a time)

```text
NOW     Engineer ★ B1-min
THEN    Cursor writes implementation_contract_assembly_kit_template_b1.md
THEN    Claude implements + tests
THEN    Cursor review + Engineer Board/CLI smoke
          (4/4 still 4/4; two new dashed cards; Continuity names a kit hole)
THEN    optional B2 plates seed  OR  catalog bind into the new holes
NEVER   invent Rooster L×W to “progress 3D” instead of this
```

---

## 6. Smoke — **ACCEPT** 2026-09-09

[engineer_smoke_assembly_kit_template_b1.md](engineer_smoke_assembly_kit_template_b1.md). Live: 4/4, `XT60` + `cable JST-SH 6 pines` declarative. Leave-pending was also ACCEPT; this walk declared both. Sim FAIL on the same demo is energy detour, not kit.
