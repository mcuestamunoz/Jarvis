# Engineer notes — Propose when combo doesn’t fit

**Date:** 2026-09-01  
**Trigger:** Engineer after PRODUCT_SCOPE walk: add “cuando un combo no encaja, que proponga”; evaluate whether to investigate; code scope / complexity.  
**Not an IC.** Not Catalog Foundation. Not a Conversation Engine.

Walk evidence: [engineer_cli_walk_block_closure_product_scope.md](engineer_cli_walk_block_closure_product_scope.md)

---

## Worth investigating?

**Yes.** This is the product spine of the post-walk catalog-assist investigation — not a fifth equal bullet next to the watts CTA. The walk already showed the failure: 4S 1500 + `r2305` + PVC 650 g fails; 6S 10 Ah “fixes” minutes and kills thrust; `ayúdame a elegir` reprints `estado`.

**Not worth a single mega-IC.** Three nested products live under the same sentence. The investigation must pick **one tier** before Claude implements.

---

## What already exists (do not rebuild)

| Surface | What it does on this walk | Why it didn’t help |
|---|---|---|
| `build_motor_catalog_suggestions` (G22 single search) | D8: thrust + **inherited KV + prop inch** from the *bound* combo | After `r2305` + `gf_5045x3`, filters are ~2500 KV and 5″. A motor that would actually cover ≥15 N is usually a different KV/prop band → empty or useless list. G22 **forbids** a silent KV-only fallback. |
| `_try_start_assisted_motor_help` | IDLE `ayúdame a elegir` | **Returns `None` if `catalog_ref` is set** (`orchestrator.py` ~1482 / 1498–1501). Fall-through: propeller, then battery, then Continuity/`estado`. Bound-but-underspec is treated as “motor done”. Gate E Path 2 already documented this. |
| Continuity `next_useful_step` | Rank 2 = sim fail **before** rank 3 = catalog gap | After `simular` fail, copy is “arquitectura 4/4 / sim no es PASS”, not a numbered re-offer. Rank 3 *does* mention `explora opciones`, but it never wins on this walk. |
| `SuggestionEngine` | Generic `improve_autonomy` / `reduce_weight` / `increase_thrust` | No SKU, no combo, no bind path. |
| DSE `explore()` | Read-only candidates; G24-A apply-by-index; G24-C catalog-native slot | Catalog-motor injection is only for `_CATALOG_MOTOR_GOAL_KEYS` = **`aumentar_payload`, `mejorar_estabilidad`**. Not `aumentar_empuje`, not `mejorar_autonomia`. And it **reuses the same G22 search**, so the same KV/prop trap applies. G24-B (`_score_candidate`) stays locked. |

There is **no** joint motor+prop+battery search that asks “what SKU triple would make this sim PASS and hit 5 min”. Tests close Gate A by exact bind; the CLI does not propose a replacement stack.

---

## Three tiers (investigation must recommend one)

### Tier 1 — Re-offer the same D8 list when the bound SKU no longer covers

**Product:** `estado` / post-sim / `ayúdame a elegir` prints numbered motors for the *new* thrust floor; pick re-binds.

**Code (small–medium):** `_try_start_assisted_motor_help` must not `return None` on `bound_sku_underspec`; Continuity rank 2 must not hide the catalog CTA; maybe one evidence line with names from `build_motor_catalog_suggestions`. GAP title honesty (already in evidence as `bound_sku_underspec`). Watts CTA can ride along.

**Complexity:** localized orchestrator + Continuity + tests. **Does not need** new search, DSE, or JSON.

**Limit:** if G22 filters stay, the list is often **empty** on this walk (15 N ∩ 2500 KV ∩ 5″). Honest empty + “suelta KV/hélice o cambia requisitos” is G22-consistent. It is **not** “propón un combo que encaje”.

### Tier 2 — Search that relaxes the failed combo’s KV/prop (motor family only)

**Product:** when underspec, propose motors that cover thrust **without** inheriting the failed 5″/2500 KV lock (or with an explicit “relax filters” mode).

**Code (medium):** policy fork in `build_motor_catalog_suggestions` / `derive_kv_prop_filters`. G22 lock: empty strict search must stay empty **or** a *named* second pass (not a silent fallback that disagrees with the gap). Prop compatibility may need a parallel pass. Still not a full combo.

**Risk:** offering a 900 KV / 12″ motor next to a still-bound `gf_5045x3` is a **frankenstein propose** unless propeller is in the same offer.

### Tier 3 — Propose a coherent replacement combo (motor + prop + battery) that would PASS

**Product:** “esto no cierra; prueba {SKU triple} / aplica N”. Energy vs thrust spiral (4S 1500 vs 6S 10 Ah) only dies here.

**Code (large):** new product authority or a **scoped DSE goal** (thrust+autonomy) that varies more than motors, scores with existing calc/sim, apply-by-index. Touches G24-B lock if ranking must prefer catalog rows; electrical_compatibility; L0 vs L1 autonomy; motor_count. This is the edge of a recommender. **Out of a first IC.** Investigation should say whether DSE can absorb it without a new subsystem.

---

## Recommendation to Engineer

- **Investigate:** yes. Contract title: catalog-assist + **misfit propose**, three-tier Gate.  
- **First IC (if ★ after investigation):** Tier 1 only, unless the report proves Tier 1 is empty-on-walk and Engineer ★s a named G22 second pass (Tier 2).  
- **Not this investigation’s IC:** Tier 3, H5, Option B, Catalog Foundation ESC SKUs, Structure, Conversation Engine.

Watts CTA and GAP rename are Tier 1 hygiene, not the spine.
