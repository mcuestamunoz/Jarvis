# Engineer Lock — Realistic assembly template (novice kit vs 4-block architecture)

**Date:** 2026-09-09  
**Authority:** Engineer (after plate L×W review): the **initial** structure should be a **real assembly template** — adapters, controllers, wiring, etc. — so a user without domain knowledge sees what a build requires; Jarvis asks as those items come into play; unknown → **pending**. Prefer this over adding catalog rows “as we 3D.”  
**Status:** ★ LOCKED — B1-min **CLOSED** @ **2507**/**2508** + [smoke](engineer_smoke_assembly_kit_template_b1.md) **ACCEPT**. **No** naive `BLOCK_TO` append. Next kit row needs a new ★.  
**Parents:**
- [investigation_review_geometry_plate_lw_sourced_b1.md](investigation_review_geometry_plate_lw_sourced_b1.md) — Rooster **B0** (no sourced L×W)
- `BLOCK_TO_COMPONENTS` / Spatial Board **slots** (honest absence) — already pending for the **thin** template
- Structure B — curated frame parts as BOM `└` children; **full Included kit ingest OUT**
- Fit / Conversation Engine / GetFPV crawler / plate invention — **out**

**Not an IC. Do not implement.** Do not dump wiring into `BLOCK_TO_COMPONENTS` in the same breath as 3D.

---

## Locked reading

Two products (do not collapse):

| Product | What Jarvis is today | What Engineer named |
|---|---|---|
| **P-energy** | 4 blocks (`propulsion` / `energy` / `structure` / `control`) → keys `motors`, `propellers`, `esc`, `battery`, `frame`, `flight_controller`, `sensors`. Slots = those keys missing. Catalog fills **those** holes. | Enough for hover/autonomy *claims* |
| **P-kit** | A **build list** a novice can assemble: prop adapters / bell nuts, XT60, VTX, RX, camera, SMA, standoffs, wiring, … Unknown stays **pending**, not invented | Enough to **montar el equipo** |

Today the Board’s “all components” claim is honest **only inside P-energy**. A dashed slot for `esc` is not a dashed slot for `prop_adapter`. That is the new frontier — not a missing Rooster box (that gap is **B0**).

```text
Pending = existing slot / Continuity next-step / BOM incomplete
       — not a Conversation Engine, not LLM kit invention.
Template first, then catalog bind into named holes
       — not “seed 17 hélices then hope the architecture grows.”
```

---

## What already exists (do not rebuild)

- Architecture 4/4 + `BLOCK_TO_COMPONENTS` is the **functional** template.  
- Board `kind: "slot"` = architecture-expected, undeclared.  
- Frame **parts** (plates, arms) are **children of `frame`**, not extra architecture keys. Full kit scrape was **refused** in Structure B.  
- Continuity already asks the **next** missing expected key. It cannot ask for a part that is not in the template.

---

## Wrong next step

```text
añadir 20 keys a BLOCK_TO_COMPONENTS esta semana
· scrape GetFPV Included → componentes
· LLM “qué más lleva un FPV”
· tratar nylon standoffs como cajas 3D
· reabrir plate L×W con un L×W inventado
```

---

## Ordered work if Engineer ★

1. ~~Investigation~~ **REVIEWED** — [review](investigation_review_assembly_kit_template_b0.md) · [next steps](engineer_next_assembly_kit_template.md)  
2. ~~B1-min~~ **CLOSED** — [smoke](engineer_smoke_assembly_kit_template_b1.md) **ACCEPT**.  
3. Later ★: ~~B2 HD/VTX plate text~~ **CLOSED** + ACCEPT · ~~`prop_adapter`~~ **B1 REVIEWED** @ **2523** · kit SKUs **D OPEN** [contract](investigation_contract_kit_connector_harness_skus_d.md). Geometry L×W / GetFPV helix / `"cabe"` stay **other** queues.

---

## Explicit non-goals until later ★

In-product crawl · Conversation Engine · cylinder · STEP-in-core · inventing Rooster L×W · version bump
