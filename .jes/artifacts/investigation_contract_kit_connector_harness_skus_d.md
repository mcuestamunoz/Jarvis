# Investigation Contract — Kit SKUs D (XT60 / harness into existing holes)

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_kit_connector_harness_skus_d.md`

**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · wait Engineer ★ Buy **B1** (recommended; B2 = bind-only)  
**Parents:**
- Engineer ★ **`D`** (2026-09-09) — [engineer_next_assembly_kit_template.md](engineer_next_assembly_kit_template.md) §3 D
- [engineer_lock_assembly_kit_template.md](engineer_lock_assembly_kit_template.md) — *template first, then catalog bind into named holes*
- Kit B1-min **CLOSED** — holes `power_connector`, `signal_harness` exist; free-text `XT60` / `cable JST-SH 6 pines` already saves (no `catalog_ref`)
- Prop adapter ask B1 **REVIEWED** @ **2523** — **out** (do not seed adapter SKUs; “va directa” is identity, not a connector family)
- Rooster plates B2 **CLOSED** — **out**
- Continuity N2 (`power_connector` nag mid-architecture) — **out** (later tidy, not this report’s default Buy)
- Catalog v1: `CatalogRef.family` is `Literal["motor","battery","propeller","esc","frame"]` — **no** connector family today
- ESC bind-without-wizard (`bind_esc_from_catalog`, no `_offer_component_esc_catalog`) — a pattern to compare, not to copy blindly

**Type:** Catalog identity investigation. **Not** an IC. **Do not implement. Do not seed JSON. Do not widen `CatalogRef`. Do not touch `KIT_TO` / `BLOCK_TO`.**

**Checkpoint:** package **`0.3.8`** · suite **2523**

**You are Claude Code.** Write the report only.

---

## 0. Role split

```text
Engineer  → bind real connector/harness SKUs into the holes that already exist
Cursor    → this contract; review; IC only after ★ on Buy shape
Claude    → investigation_report_kit_connector_harness_skus_d.md
```

---

## 1. Why this exists

Locked order (Engineer):

```text
Template first (holes)  →  then catalog bind into those holes
not “seed 17 hélices and hope the architecture grows.”
```

The holes are live. A novice can type `XT60` and close `power_connector` **without** SKU identity. D is whether Jarvis should also offer **curated rows** the way motors/batteries/frames do — `catalog_ref {family, sku}` — so the BOM can say which XT60, not only the word.

Wrong next step:

```text
scrape GetFPV Included → 40 connectors
· new KIT_TO keys · meter XT60 en BLOCK_TO
· caja 3D del conector · inferir XT60 vs XT30 de la batería
· SKUs de prop_adapter en el mismo Buy
· Conversation Engine · arreglar N2 en el mismo report
```

Right question:

> What is the **smallest** Catalog v1 extension that binds 1–2 honest rows into `power_connector` / `signal_harness`, keeps free-text valid, does not widen PASS, and does not invent millimetres?

---

## 2. Locked stances

1. **Holes already exist.** Do not add kit keys. Do not append `BLOCK_TO`. PASS / hover / autonomy **byte-identical**.  
2. **Free-text stays valid.** `XT60` without `catalog_ref` remains a successful declaration (kit B1-min relabel). Catalog is an **upgrade**, not a requirement. Unknown → pending still works.  
3. **Cite or don’t seed.** Each proposed row needs a manufacturer/retailer page (URL + the fields you would copy). If the page is silent on mass / L×W×H, those fields stay **absent** — not guessed. Default: **no 3D** for these SKUs (no Class A box unless the page states L×W×H unambiguously).  
4. **No compatibility engine.** Do not propose “battery is XT30-class → refuse XT60.” Honesty later may *say* two cited connector types differ; user confirms. Not the default Buy.  
5. **`ComponentLibrary` is the only JSON reader.** A new family is a new folder + dataclass + loader + `bind_*_from_catalog`, or an explicit refuse of a sixth family (see Buys). Do not read JSON from orchestrator.  
6. **`CatalogRef.family` is a core Literal.** Widening it is a contract change the IC must name. Report must not pretend a connector SKU fits in `family="esc"` or `"frame"`.  
7. **Two keys only this investigation:** `power_connector`, `signal_harness`. `prop_adapter` catalog, VTX/RX, SMA, standoffs — **out**.  
8. **N2 out.** Do not recommend reordering when Continuity asks `power_connector`.  
9. Reuse DEFINE / help-choose / numbered pick — **no** Conversation Engine.

---

## 3. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| `library/*/_datos.json` folders | Confirm **zero** connector/harness rows |
| `CatalogRef.family` Literal | Exact members; every `bind_*_from_catalog` |
| `ComponentLibrary` loaders | One loader per folder; cost of a sixth (and seventh?) family vs one `kit_hardware` bag |
| Kit DEFINE | Single-key wizard; relabel; aliases `xt60` / `harness`; **no** `_offer_component_*` for kit keys today |
| `_wants_catalog_help` | Would a free-text XT60 already `catalog_ref is None` request help-choose if a branch existed? |
| ESC pattern | `bind_esc_from_catalog` exists; **no** CLI pick — smallest bind-only precedent |
| Motor/battery/frame help-choose | File + gate; what a kit copy would duplicate |
| `_geometry_from_spec` | What happens if a future row had L×W×H — would a connector become a box? (Honesty: default Buy should **not** project geometry) |
| Live demo | If `workspace/autonomía-de-10min*` readable: `power_connector` / `signal_harness` are free-text (no `catalog_ref`) after smoke — cite. If gitignored, say so |

Do not invent product names. If you propose a seed list, each line is **page-cited** or marked “would STOP at IC if page missing.”

---

## 4. Report sections (required)

### A. What exists vs the hole

One table: families with bind+UX / bind-only / none. Explicit: kit keys have **UX without catalog**. ESC has **catalog without kit UX**.

### B. Candidate Buys (ranked, **one default**)

Must include at least:

| ID | Shape |
|---|---|
| **B0** | Park. Free-text only. No `library/` rows |
| **B2** | Seed **one** `power_connector` row + **one** `signal_harness` row + loaders + `bind_*` + widen `CatalogRef`. **No** help-choose (ESC-shaped). Free-text unchanged |
| **B1** | B2 **plus** kit single-key `"ayúdame a elegir"` / numbered pick (reuse `_wants_catalog_help`; do **not** fold into energy/propulsion composite) |
| **B-naive** | Scrape / 3D box / XT60-vs-battery inference / `prop_adapter` SKUs / `BLOCK_TO` | **Refuse** |

Name **one default**. Prefer the **smaller** hook that still lets a novice bind a named SKU into the existing hole. If B1’s extra cost is a fifth `_offer_component_*` clone, say so; B2 may then be the default. Do not recommend two new families if one `kit_connectors` folder with a `kit_key` field is smaller **and** still maps 1:1 to `power_connector` / `signal_harness` — argue, don’t invent a generic parts dump.

Seed cardinality locked for any non-B0 Buy: **≤1 row per key** this investigation (XT60-class, JST-SH-class). Not a connector aisle.

### C. Hook map

Exact functions / types: `CatalogRef`, `ComponentLibrary`, `catalog_bind.py`, kit DEFINE in `orchestrator.py`. Who must **not** gain a help-choose branch if default is B2. No patches.

### D. Twin / non-goals

PASS unchanged. Kit timing (including N2) unchanged. Adapter ask B1 unchanged. No geometry projection in the default Buy. No version bump proposed.

---

## 5. Done when

- [ ] Report written; one **default lean** (B0 / B1 / B2)  
- [ ] No `src/` / `library/` edits  
- [ ] Explicit refuse of scrape, 3D invention, compatibility inference  
- [ ] Explicit: `prop_adapter` SKUs and N2 are not this Buy  

---

## Explicitly not this investigation

Implement bind/help-choose · seed JSON · widen `CatalogRef` · `KIT_TO` / `BLOCK_TO` edits · adapter catalog · VTX/RX · N2 reorder · `"cabe"` · Conversation Engine · GetFPV crawl · version bump
