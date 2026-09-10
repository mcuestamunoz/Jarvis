# Implementation Contract — Kit SKUs D B1 (XT60 / JST-SH into existing holes)

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** CLOSED — REVIEWED PASS WITH NOTES @ **2532** + smoke **ACCEPT**  
**Parents:**
- Engineer ★ **`B1`** (2026-09-09) — “escribe IC” after D review
- [investigation_review_kit_connector_harness_skus_d.md](investigation_review_kit_connector_harness_skus_d.md) **PASS WITH NOTES** (Cursor default **B1**, not Claude’s B2)
- [investigation_report_kit_connector_harness_skus_d.md](investigation_report_kit_connector_harness_skus_d.md)
- Kit B1-min **CLOSED** — holes exist; free-text `XT60` still valid
- Prop adapter B1 **REVIEWED** @ **2523** — **out** (no adapter SKU)
- N2 connector nag mid-architecture — **out**

**Type:** Catalog v1 sixth family + bind + kit single-key help-choose.  
**Not** a new `KIT_TO` key. **Not** `BLOCK_TO`. **Not** 3D. **Not** a connector aisle.

**Baseline:** package **`0.3.8`** · suite **2523** · commit `3600b37`

**Output:** `.jes/artifacts/implementation_report_kit_connector_harness_skus_d.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Shape | **B1** — seed **1+1** + widen `CatalogRef` + `bind_*` + `"ayúdame a elegir"` on the **existing** kit single-key wizard |
| 2 | Family | **One** `kit_hardware` (not two MotorSpec-sized families). Row field `kit_key` ∈ `{power_connector, signal_harness}` **frozen** |
| 3 | Rows | Pololu XT60 pair **2175**; Pi Hut JST-SH 6-pin **CAB1009**. Re-fetch both pages. **STOP** if the cited facts below are gone or contradicted |
| 4 | Free-text | `XT60` / harness description **without** `catalog_ref` still saves (kit relabel). Catalog is an upgrade |
| 5 | Geometry | **No** L×W×H, **no** Ø, **no** mapping cable mm → `length_mm`. `_geometry_from_spec` stays `None` |
| 6 | Current | **Do not** seed `current_a` from Pololu (specs table silent; 60 A is marketing copy — review N4) |
| 7 | PASS | `BLOCK_TO` / kit timing / adapter ask / hover **unchanged** |
| 8 | Version | **No** bump |

**Product sentence:**

```text
Tras 4/4, “definir conector” + “ayúdame a elegir” lista el XT60 de catálogo.
El pick deja catalog_ref. Escribir XT60 a mano sigue valiendo.
No hay caja 3D. Hover no cambia.
```

**Not:**

```text
scrape GetFPV · XT60 vs XT30 de la batería · SKU de prop_adapter
· VTX/RX · N2 · meter keys en BLOCK_TO · Conversation Engine
```

---

## 1. You (Claude)

- Re-fetch `https://www.pololu.com/product/2175` (or `/specs`) and `https://thepihut.com/products/jst-sh-cable-6-pin-pack-of-4`. If either page is gone, or no longer matches §3.2, **STOP**.
- **STOP** if you put kit keys on `BLOCK_TO_COMPONENTS` or add `KIT_TO` keys.
- **STOP** if help-choose opens inside the energy/propulsion **composite** wizard.
- **STOP** if you project wire length / 60 A into `_geometry_from_spec` keys.
- `ComponentLibrary` is the only JSON reader. Full pytest green. Report existing-test updates (expect `_bom_sku_resolved` + suggestion-clear lists). Write the report.

---

## 2. Intent

```text
library/kit_hardware/_datos.json     2 rows, kit_key frozen
        ↓
ComponentLibrary + KitHardwareSpec
        ↓
CatalogRef.family += "kit_hardware"
bind_kit_hardware_from_catalog(sku) → ComponentSpec (suggested_key = row.kit_key)
        ↓
kit single-key wizard + ayúdame a elegir + numbered pick
        ↓
catalog_ref set · slot gone · PASS unchanged
```

---

## 3. Locked behavior

### 3.1 `CatalogRef` (`action_schema.py`)

Widen the Literal **exactly one** member:

```text
family: Literal["motor", "battery", "propeller", "esc", "frame", "kit_hardware"]
```

Do not put connector SKUs in `family="esc"` or `"frame"`.

### 3.2 Seed (`library/kit_hardware/_datos.json`)

**Exactly two** objects. Loader **rejects** any other `kit_key`.

**Row A — `power_connector`**

| Field | Value | Cite |
|---|---|---|
| JSON key / `name` | `pololu_xt60_pair` | SKU id |
| `kit_key` | `power_connector` | — |
| `manufacturer` | `Pololu` | page brand/seller |
| `model` | `XT60 Connector Male-Female Pair, Yellow` | title |
| `part_number` | `2175` | Pololu item # |
| `color` | `yellow` | specs |
| `pin_config` | `1x2` | specs Dimensions / Pins |
| `source_url` | `https://www.pololu.com/product/2175` | — |
| `identity_status` | `verified` | — |
| `source_note` | Page prose says high-current 60 A; **not** copied to `current_a` (specs table silent). No mass, no box. | review N4 |
| `current_a` / `mass_g` / `length_mm` / `width_mm` / `height_mm` / `diameter_*` | **absent** | — |

**Row B — `signal_harness`**

| Field | Value | Cite |
|---|---|---|
| JSON key / `name` | `pihut_jst_sh_6pin_cab1009` | SKU id |
| `kit_key` | `signal_harness` | — |
| `manufacturer` | `The Pi Hut` | — |
| `model` | `JST-SH Cable - 6 Pin` | title |
| `part_number` | `CAB1009` | SKU |
| `pin_count` | `6` | specs |
| `pitch_mm` | `1.0` | “1.0mm pin spacing” |
| `wire_gauge_awg` | `26` | specs |
| `connector_gender` | `female_both_ends` | page |
| `source_url` | `https://thepihut.com/products/jst-sh-cable-6-pin-pack-of-4` | — |
| `identity_status` | `verified` | — |
| `source_note` | Options 100 mm or 300 mm **cable** length — not a box; not `length_mm`. No mass. | review N5 |
| `length_mm` / `width_mm` / `height_mm` / `diameter_*` / `mass_g` | **absent** | — |

Optional catalog-only field `cable_length_options_mm: [100, 300]` is allowed on the **dataclass** if useful for the list line. Bind **must not** copy it onto `ComponentSpec.properties["length_mm"]`.

### 3.3 `ComponentLibrary`

`KitHardwareSpec` (frozen dataclass): identity + the cited electrical fields above + `kit_key`. No geometry fields on the type (do not add `length_mm` to this spec).

One loader `library/kit_hardware/_datos.json`. `get_kit_hardware` / `list_kit_hardware` / `has_kit_hardware`. `list_kit_hardware(kit_key=...)` filters. Unknown `kit_key` in JSON → load error (do not silently drop).

### 3.4 Bind (`catalog_bind.py`)

```text
bind_kit_hardware_from_catalog(sku, *, library=None, base=None) -> ComponentSpec
```

- `catalog_ref = CatalogRef(family="kit_hardware", sku=sku)`
- `suggested_key` / `component_type` = row.`kit_key`
- `completeness` at least `"medium"` (identity-only, same as kit relabel)
- Project **only** cited scalar fields that are **not** geometry keys: e.g. `pin_count`, `pitch_mm`, `wire_gauge_awg`, `color`, `pin_config`, `part_number`. **Never** `length_mm` / `width_mm` / `height_mm` / `diameter_mm` / `diameter_in`.
- `source="declared"`. No millimetres invented.

Writer on pick: existing `set_control_component` (same as kit relabel). Do not add a new physics writer.

`project_closure._bom_sku_resolved`: `family == "kit_hardware"` → `has_kit_hardware(sku)`.

### 3.5 Help-choose (kit single-key only)

New thin module `src/jarvis/core/kit_hardware_catalog_assist.py` (mirror `frame_catalog_assist.py`): reuse `is_help_choose_phrase` / `match_suggestion_by_input` from `motor_catalog_assist`. **No ranking.** Suggestions = `list_kit_hardware(kit_key=expected_keys[0])` (so the connector wizard never lists the harness).

`InteractiveSessionState.kit_hardware_suggestions` — runtime-only, same tier as `frame_suggestions` (not persisted).

Orchestrator:

1. In `_handle_component_description`, **after** adapter skip, **before** infer: if `expected_keys[0]` in `{power_connector, signal_harness}` and `_wants_catalog_help(that spec)` → help-choose / numbered pick like frame. Do **not** gate on `"esc" in expected_keys`.
2. `_offer_kit_hardware_catalog` / `_apply_kit_hardware_catalog_pick`. Apply: bind + `set_control_component` + clear suggestions + still_missing of this wizard (usually empty → `_set_pending_next_block`).
3. Every existing `_offer_component_*_catalog` that already clears peer lists must also set `kit_hardware_suggestions: []`. The new offer clears motor/propeller/battery/frame suggestions.

Do **not** add kit help-choose to `ParamDefinitionSession` numeric wizards. Do **not** fold into propulsion/energy composite Phase A.

Free-text path unchanged (relabel). `"no lo sé"` on adapter is unrelated.

### 3.6 Brief / aliases

Keep existing `COMPONENT_PROMPTS` for the two keys (pending OK). You **may** append one short clause that help-choose exists (`Di 'ayúdame a elegir' para ver el catálogo.`) — do not remove the free-text example.

Aliases unchanged (`xt60` → `power_connector`, etc.).

### 3.7 Geometry / PASS / N2

`_geometry_from_spec(bound kit spec) is None`. Twin: `_block_progress_status` equal with vs without `catalog_ref` on the kit key. Continuity rank / when `power_connector` nags: **empty diff** in `project_continuity.py` unless you prove a bug.

---

## 4. Tests (new file)

`tests/test_kit_connector_harness_skus_d.py`:

| ID | Behavior |
|---|---|
| T0 | Loader: exactly two SKUs; `kit_key`s are the frozen pair; `has_kit_hardware` true; **no** `length_mm`/`height_mm` on either spec |
| T1 | `bind_kit_hardware_from_catalog("pololu_xt60_pair")` → `catalog_ref.family=="kit_hardware"`, `suggested_key=="power_connector"`, `catalog_ref.sku` set, **no** `current_a`, **no** geometry properties |
| T2 | Bind harness SKU → `suggested_key=="signal_harness"`; properties must **not** contain `length_mm` |
| T3 | `_geometry_from_spec` on both bound specs is `None` |
| T4 | `_bom_sku_resolved` true for `{family: kit_hardware, sku: pololu_xt60_pair}` |
| T5 | Orchestrator 4/4 dron, IDLE `declara el conector` then `ayúdame a elegir` → message lists `pololu_xt60_pair` (or Pololu/XT60); `kit_hardware_suggestions` non-empty; peer suggestion lists empty. Must **not** list the harness SKU |
| T6 | From T5, pick `"1"` → `components["power_connector"].catalog_ref` set; slot gone; propulsion `_block_progress_status` still `complete` |
| T7 | 4/4, `declara el conector` then `"XT60"` (no pick) → spec exists, `catalog_ref is None` (free-text regression) |
| T8 | `vehicle_type=robot` → `list_kit_hardware` may still have rows in the library, but IDLE kit wizard still does not open (existing kit T6). Do not show help-choose on a robot project |

Use `_RefuseLLM` / create_project helpers from kit B1-min tests. No network in tests (library JSON only). Do not write `workspace/`.

---

## 5. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/schemas/action_schema.py` | Literal + `kit_hardware_suggestions` |
| `library/kit_hardware/_datos.json` | two rows |
| `src/jarvis/knowledge/library.py` | spec + loader |
| `src/jarvis/core/catalog_bind.py` | `bind_kit_hardware_from_catalog` |
| `src/jarvis/core/project_closure.py` | `_bom_sku_resolved` branch |
| `src/jarvis/core/kit_hardware_catalog_assist.py` | **new** thin assist |
| `src/jarvis/core/orchestrator.py` | offer/apply + gate; peer-list clears |
| `src/jarvis/core/acquisition_target.py` | optional Brief clause |
| `tests/test_kit_connector_harness_skus_d.py` | T0–T8 |
| `ui/` | **empty** |
| `.jes/artifacts/implementation_report_kit_connector_harness_skus_d.md` | write |

`BLOCK_TO_COMPONENTS` / `KIT_TO_COMPONENTS` values **unchanged**. `engineering_readiness.py` empty unless you prove a bug.

---

## 6. Engineer smoke (after Cursor review)

Live 4/4 dron (or `autonomía-de-10min`):

- `definir conector` → `ayúdame a elegir` → list includes Pololu XT60 → `#1` → `catalog_ref` / BOM SKU.
- Typing `XT60` without pick still works.
- `estado` / Board: no new solid for the connector.
- Hover numbers **unchanged**.

Record `engineer_smoke_kit_connector_harness_skus_d.md`.

---

## 7. Done when

- [x] T0–T8 green; full pytest green (**2532**)  
- [x] `git diff` shows **no** new strings inside `BLOCK_TO_COMPONENTS` lists  
- [x] Bound specs have **no** `length_mm`/`width_mm`/`height_mm`/`diameter_*`  
- [x] No `prop_adapter` row, no version bump  
- [x] Report written  
- [x] Engineer smoke §6 **ACCEPT**  

---

## Explicitly not this IC

`prop_adapter` catalog · VTX/RX · N2 Continuity reorder · GetFPV crawl · XT60-vs-battery inference · 3D box · Conversation Engine · second connector aisle · version bump
