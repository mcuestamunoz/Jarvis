# Implementation Report — Structure Catalog Foundation IC-1 (schema + seed)

**Project:** Jarvis
**Date:** 2026-09-04
**Implementer:** Claude Code
**IC:** [implementation_contract_structure_catalog_foundation_ic1.md](implementation_contract_structure_catalog_foundation_ic1.md)
**Baseline:** tag `v0.3.6` + claim hygiene + control parity + Structure Foundations claim-copy · suite closed at 2171

---

## Files changed

- `src/jarvis/schemas/action_schema.py` — `CatalogRef.family` Literal extended to `["motor", "battery", "propeller", "esc", "frame"]`. No other schema change.
- `src/jarvis/knowledge/library.py` — new `FrameSpec` frozen dataclass (`name`, required `mass_g`, required `size_class_inch`, optional `manufacturer`/`model`/`material`/`part_number`/`source_url`/`identity_status`/`source_note`), mirroring `EscSpec` exactly; `ComponentLibrary._frames` cache slot; `_frame_from_raw`/`_load_frames`/`get_frame`/`has_frame`/`list_frames`, mirroring the ESC methods line-for-line (`KeyError` with an "available" list on miss, `ValueError` on a seed row missing `mass_g` or `size_class_inch`, empty dict if `library/frames/_datos.json` is absent). No `find_frames_for_*` (no consumer, per IC).
- `library/frames/_datos.json` — **new**, 4 seed rows (below).
- `docs/PHYSICAL_COMPONENT_CATALOG_V1.md` — one factual line added to the §13 status table recording IC-1 landed (schema+seed only); the "still deferred" line updated to say frame catalog **bind** (not the whole catalog) remains deferred. No doctrine rewritten.
- `tests/test_catalog_foundation_v1.py` — new tests (below).

No edits to `component_writers.py`, `catalog_bind.py`, `project_closure.py`, `engineering_readiness.py`, `project_continuity.py`, `orchestrator.py`, `render_views.py` (confirmed via `git diff` — zero diff on the first three forbidden-by-name files; the other three carry only the prior three ICs' already-landed changes, untouched this session).

## Seed rows — SKUs, sources, and exact numbers copied

| SKU (JSON key) | Manufacturer / model | `mass_g` | `size_class_inch` | `material` | Source URL | What the source states |
|---|---|---|---|---|---|---|
| `tbs_source_one_v5_5in` | Team BlackSheep / TBS Source One V5 | 123.5 | 5 | *(omitted — not stated on source page)* | https://www.racedayquads.com/products/tbs-source-one-v5-5-freestyle-long-range-frame | Frame weight 123.5g; 5″ wide-stance freestyle/long-range frame. |
| `tbs_source_one_v5_1_7in_dc` | Team BlackSheep / TBS Source One V5.1 7-inch DC | 143.5 | 7 | *(omitted — not stated on source page)* | https://www.progressiverc.com/products/tbs-source-one-v5-7-inch-dc-quad-frame | Frame weight 143.5g; 7″ deadcat (DC) configuration. |
| `iflight_xl7_v4_7in` | iFlight / XL7 V4 True-X Long Range | 119.1 | 7 | fibra de carbono | https://www.fpv24.com/en/iflight/iflight-xl7-v4-long-range-fpv-frame | Frame weight ~119.1g; 7″ True-X long-range frame; "full carbon fiber airframe made of 3K carbon fiber." |
| `armattan_rooster_5in` | Armattan Quads / Rooster 5″ | 125 | 5 | fibra de carbono | https://armattanquads.com/products/rooster-1 (manufacturer's own site) | Approx. 125g frame weight; 5″ compressed-X configuration; carbon fiber main plate/arms with titanium cage and aluminum standoffs. |

Two distinct `size_class_inch` values present (5 and 7), 4 SKUs total, 3
manufacturers, one row sourced directly from the manufacturer's own domain
(Armattan). All four have `identity_status: "verified"` and a `source_note`
stating what was read. No mass/class/material was invented — where a source
page did not state material, the field was omitted (TBS rows).

## Behavior changed

- `CatalogRef(family="frame", sku=...)` now constructs successfully (previously a `pydantic` validation error).
- `ComponentLibrary.get_frame`/`has_frame`/`list_frames` are new, working API — usable by any future IC, called by nothing in production today.
- **Not changed:** any writer, any bind path, `ComponentSpec.catalog_ref` is never set for a frame by any production code path, `_bom_sku_resolved` still has no `"frame"` branch (still returns `False` for it, per its own "no v1 resolve path for other families" docstring), `_structure_evidence`'s `catalog_bound` for frame remains `False` in every real project (schema now *permits* a frame `catalog_ref`, but nothing ever sets one), Structure A screening, BOM rendering, Continuity, `ASSEMBLY_READY` eligibility — all byte-identical.

## Tests added/updated

`tests/test_catalog_foundation_v1.py`: `test_frames_load_and_get_by_id`, `test_frames_seed_has_at_least_two_distinct_size_classes`, `test_has_frame`, `test_frame_missing_mass_raises`, `test_frame_missing_size_class_raises`, `test_catalog_ref_accepts_frame_family`; extended `test_unknown_sku_never_fabricated` to cover `has_frame`/`get_frame`.

## Tests executed

- Targeted: `pytest tests/test_catalog_foundation_v1.py -q` → 44 passed.
- Full suite: `pytest -q` → **2177 passed** (2171 baseline + 6 new tests), zero failures, zero skipped, zero weakened.

## Residual (per §7 of the IC)

- IC-2 (bind + `invalidate_diverged_catalog_refs` frame branch + `_bom_sku_resolved` frame branch) and IC-3 (assist/`ayúdame a elegir` for frame) remain **not authorized** — no code toward either was written.
- Layout params / CAD / FEA remain out, unaffected.
- `catalog_bound` for frame stays `False` in every real project after this IC — the schema now *permits* it, nothing *produces* it. This mirrors ESC's own long-standing state exactly, which is the precedent this IC was built to match.
