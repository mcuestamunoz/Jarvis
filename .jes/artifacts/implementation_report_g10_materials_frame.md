# Implementation Report — G10 Material Catalog / Frame Acquisition

**Type:** Product behavior implementation (library-canonical material identity + frame
acquisition + list-materials).
**Contract:** [implementation_contract_g10_materials_frame.md](implementation_contract_g10_materials_frame.md)
**Design authority (CLOSED ★1–★8):** [design_g10_materials_frame.md](design_g10_materials_frame.md)
**Investigation:** [investigation_g10_materials_frame.md](investigation_g10_materials_frame.md)
**Checkpoint base:** `checkpoint-g3` (`a3b72b8`)
**Commit / tag:** none (per contract — not requested)

---

## FILES CHANGED

| File | Change |
|---|---|
| `src/jarvis/domains/materials.py` (new) | Shared `MATERIAL_ALIASES` (alias → library Spanish name, 8 materials + ES/EN variants, no `madera`), `LEGACY_MATERIAL_SLUGS` (old English slugs → library names, for ★5), `resolve_material_alias()` helper |
| `src/jarvis/domains/aerial.py` | `MATERIAL_MAP` now points at the shared `MATERIAL_ALIASES` (kept as a name for backward-compat imports); `extract_frame_properties` emits library Spanish names via `resolve_material_alias()`; frame `ComponentRule` keywords expanded to all 8 library material stems (★4) |
| `src/jarvis/core/iterate_domain.py` | `_KNOWN_MATERIALS` now points at the shared `MATERIAL_ALIASES` — single alias table, `madera` no longer present (★2, ★7) |
| `src/jarvis/core/orchestrator.py` | `_handle_component_description`: added force-frame branch mirroring the FN-019 propellers bypass (★3); added `_handle_list_materials()` and wired `intent == "list_materials"` in the IDLE dispatcher, the `ITERATE_INTERACTIVE` soft-interrupt block, and the `DEFINE_MISSING_PARAMETERS` soft-interrupt block (★8) |
| `src/jarvis/core/mutation_engine.py` | `apply_material_mutation`: `current_material` now prefers `state["material"]` (canonical, via `get_frame_material`) over the legacy `structure.material` mirror (★6) |
| `src/jarvis/utils/design_utils.py` | `get_frame_material`: read-time translation of legacy English slugs (`carbon_fiber`/`aluminum`/`plastic`) to library Spanish names (★5) |
| `src/jarvis/core/intent_resolver.py` | New `IntentType` member `"list_materials"`; `LIST_MATERIALS_PATTERNS`; checked first in `_resolve_strong_action_intent` (★8) |
| `tests/test_g10_materials_frame.py` (new) | T1–T8 acceptance tests |
| `tests/test_aerial_domain.py` | Updated material-identity assertions to library Spanish names; added a full-library coverage test |
| `tests/test_design_utils.py` | Updated `get_frame_material` assertions to library Spanish names; added the ★5 legacy-shim test |
| `tests/test_frame_component.py` | Updated 3 end-to-end assertions (`carbon_fiber`→`fibra de carbono`, `aluminum`→`aluminio`) |
| `.jes/artifacts/cli_findings_post_catalog_bind_v1.md` | G10 status row + section header updated to Fixed (pending CLI) |

`library/materiales/_datos.json` — **not touched**, per contract.

---

## BEHAVIOR CHANGED

1. **Frame acquisition now accepts all 8 library materials** (was 2/8: `aluminio`, `fibra de
   carbono`). `plastico`/`plástico`/`pvc`/`titanio`/`acero`/`kevlar`/`magnesio` are now
   recognized both as frame keywords (★4, cold start) and via the force-frame bypass (★3, scoped
   wizard).
2. **Stored frame material identity changed vocabulary**: `components["frame"].properties["material"]`
   now holds the library's own Spanish name (e.g. `"fibra de carbono"`) instead of the old
   internal English slug (`"carbon_fiber"`). Any code reading that field directly (not through
   `get_frame_material()`) sees the new vocabulary for newly-declared frames.
3. **`get_frame_material()` translates legacy English slugs on read** (★5) — projects with
   frame data saved before this fix keep working with no file migration.
4. **`mutation_engine.apply_material_mutation` reads the correct current material** (★6) — this
   is a genuine bug fix: before this change, a material iterate mutation silently computed the
   wrong mass whenever the frame had been declared via the wizard after project creation
   (investigation §5.2's reproduced scenario). No user-visible interface changed; the *numeric
   result* of an iterate material mutation performed after a wizard-declared frame material is
   now different (correct) from before.
5. **New deterministic intent** `"que materiales tenemos en el catálogo?"` (and narrow variants)
   now returns the library's material list directly — 0 LLM calls — instead of falling through
   to `analyze`/LLM. Works in IDLE, inside the iterate wizard (as a soft interrupt, wizard state
   preserved), and inside `DEFINE_MISSING_PARAMETERS` (as a soft interrupt).
6. **`madera` no longer resolves as a material alias** in the iterate flow — it was previously
   recognized by name but had no library entry, causing an unhandled `KeyError` on
   `get_material()`. It now behaves like any other unrecognized material name.

Everything else (motor/propeller/battery/ESC acquisition, iterate wizard flow, Continuity,
`structure.density`/`volume` fields, `structure_mass_override_kg` physics bypass) is unchanged.

---

## TESTS ADDED/UPDATED

- **Added:** `tests/test_g10_materials_frame.py` — 24 tests (T1 parametrized ×8, T2 ×3, T3 ×2,
  T4, T5 ×3, T6, T7 ×4, T8 ×2).
- **Updated:** `tests/test_aerial_domain.py` (2 assertions + 1 new coverage test),
  `tests/test_design_utils.py` (5 assertions + 1 new shim test), `tests/test_frame_component.py`
  (3 assertions).

---

## TESTS EXECUTED

```text
pytest tests/test_g10_materials_frame.py                                    24 passed
pytest tests/test_aerial_domain.py tests/test_design_utils.py \
       tests/test_frame_component.py tests/test_mutation_engine.py         119 passed
pytest tests/test_iterate_session.py tests/test_intent_resolver.py \
       tests/test_orchestrator.py tests/test_component_inference.py \
       tests/test_motor_component.py tests/test_battery_component.py       410 passed
pytest  (full suite)                                                      1741 passed
```

No failures, no skips introduced, no tests weakened or deleted.

---

## ★1–★8 COVERAGE

| ★ | Status | Where |
|---|---|---|
| ★1 | Done | `aerial.extract_frame_properties` → `resolve_material_alias()` → library Spanish name |
| ★2 (b) | Done | `src/jarvis/domains/materials.py`; `aerial.MATERIAL_MAP` and `iterate_domain._KNOWN_MATERIALS` both point at `MATERIAL_ALIASES` |
| ★3 | Done | `orchestrator._handle_component_description`, force-frame branch mirroring FN-019 propellers |
| ★4 | Done | Frame `ComponentRule.keywords` in `aerial.py` — all 8 library stems added |
| ★5 | Done | `design_utils.get_frame_material` — `LEGACY_MATERIAL_SLUGS` translation |
| ★6 | Done | `mutation_engine.apply_material_mutation` — `state["material"]` preferred over `structure.material` |
| ★7 (a) | Done | `madera` absent from `MATERIAL_ALIASES`; no `library/` JSON edit |
| ★8 | Done | `intent_resolver.LIST_MATERIALS_PATTERNS` + `orchestrator._handle_list_materials`, wired in IDLE, iterate-wizard, and DEFINE_MISSING soft-interrupt points |

---

## RISKS / FOLLOW-UPS

- **G9** (Continuity catalog-gap blind to `catalog_ref`) — untouched, as required. No shared
  symbols were found or introduced between this cut and G9's motor catalog-gap block.
- **`madera`** — still not a library material. If Engineer later wants wood as a real material,
  it requires a `library/materiales/_datos.json` addition (out of scope here) plus re-adding it
  to `MATERIAL_ALIASES`.
- **`structure.material` (legacy mirror) still exists and is still written** by
  `create_project.py` and `actions/iterate.py:_apply_design_property_mutation`. ★6 only changed
  *what mutation_engine reads*; deleting the field entirely was explicitly optional per the
  contract (§2 "Allowed optional") and was not done — it remains a display-only value with no
  read consumers left in the material-mutation path.
- **List-materials phrasing** (★8) is intentionally narrow (4 patterns). Real CLI usage may
  surface phrasings not covered; extending `LIST_MATERIALS_PATTERNS` is a small, isolated future
  change if needed.
- **Force-frame (★3) test coverage** deliberately used a bare-mass input (`"400g"`) with zero
  keyword overlap to isolate it from ★4's keyword expansion — this is a synthetic case chosen for
  test isolation, not a phrase from the original CLI transcript.
