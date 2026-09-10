# Implementation Report — Live ESC visor via sourced SKU rebind B1

**IC:** [implementation_contract_geometry_esc_visor_rebind_b1.md](implementation_contract_geometry_esc_visor_rebind_b1.md)  
**Implementer:** Claude Code  
**Date:** 2026-09-09  
**Baseline:** package `0.3.8` · suite **2562** → **2573** (2562 + 11)

---

## Files changed

| File | Change |
|---|---|
| `src/jarvis/core/esc_catalog_assist.py` | **New.** Thin `list_escs()` list + format. Reuses motor assist match/help-choose. |
| `src/jarvis/core/catalog_rebind_assist.py` | `CatalogRebindKey` += `"esc"`; `\besc\b`; strip token; priority last. |
| `src/jarvis/core/orchestrator.py` | IDLE explicit `esc` branch (no battery catch-all); `_offer`/`_apply`; singleton pick `expected_keys == ["esc"]`; ★4 clears `esc_suggestions` on peer offers. |
| `src/jarvis/schemas/action_schema.py` | `esc_suggestions` runtime list. |
| `src/jarvis/core/catalog_bind.py` | Docstring: IDLE rebind + `base=` preserve pose. |
| `src/jarvis/core/state_manager.py` | Comment: `esc_suggestions` not persisted. |
| `tests/test_geometry_esc_visor_rebind_b1.py` | **New.** P1–P7. |
| `library/` | empty |
| `ui/` | empty |
| `workspace/` | empty |

No version bump.

---

## Behavior changed

IDLE `cambiar esc` / `ayúdame a elegir esc` (architecture 4/4, ESC already present and not a stub) opens the 1-row Hobbywing catalog. Pick binds `hobbywing_xrotor_40a_6s` via `bind_esc_from_catalog(sku, base=existing)` + `set_control_component`. Live `declared_box_pose` / `mounted_on` survive. Projector then has an ESC **box** 50.0 × 21.6 × 12.0 mm.

Freeform ESC without `catalog_ref` still has no geometry (dims are not copied onto the mute identity). Propulsion composite `["motors","propellers","esc"]` does not offer or apply this catalog.

Physics: catalog `current_a` 40 and `mass_g` 15 project on bind. ACCEPT per IC §0.7.

---

## Tests added / executed

`tests/test_geometry_esc_visor_rebind_b1.py` — 11 collected (P4 is 5 parametrize cases):

- P1 bind + base pose → box + pose DTO  
- P2 freeform → no `geometry`  
- P3 library 50.0 / 21.6 / 12.0; `list_escs()` length 1  
- P4 resolver family / None  
- P5 IDLE `cambiar esc` → `esc_suggestions`, not battery  
- P6 pick preserves pose + box  
- P7 composite leftover `"1"` does not bind

Full suite: `python -m pytest -q` → **2573 passed**, 0 failed.

`ui/` not touched — no npm.

---

## Non-goals honored

No `lipo_3s_2200mah` L×W×H. No Rooster L×W. No `spatial_board.py` / visor X edit. No `_wants_catalog_help` on `"esc" in expected_keys`. No version bump. No `workspace/` mutation.

---

## Remaining risks

- Live 5min smoke is the Engineer’s: `cambiar esc` → pick Hobbywing → box at existing pose vs FC; `"cabe"` may now screen.  
- Battery still has no box; frame still has no prism. Next remaining-pieces slices unchanged.  
- B3 `else: battery` catch-all is gone; unknown future `CatalogRebindKey` raises `AssertionError` instead of opening the battery list.
