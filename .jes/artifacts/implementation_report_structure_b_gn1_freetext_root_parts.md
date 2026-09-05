# Implementation Report — Structure B G-N1 Free-text Root+Parts

**Project:** Jarvis  
**Date:** 2026-09-04  
**Implementer:** Cursor (Engineer `Procede` on Root+parts)  
**IC:** [implementation_contract_structure_b_gn1_freetext_root_parts.md](implementation_contract_structure_b_gn1_freetext_root_parts.md)  
**Baseline:** suite **2223**

## Files changed

- `src/jarvis/domains/aerial.py` — `extract_all_frame_part_properties` (clause-scoped multi-part); `extract_frame_part_properties` wraps first hit
- `src/jarvis/core/component_writers.py` — `merge_frame_root_declared_properties` (configuration / wheelbase_mm); upsert docstring
- `src/jarvis/core/orchestrator.py` — frame apply passes `source_text` → upsert parts; parts-only path when frame exists and message has no root mass/size/config/wheelbase
- `tests/test_frame_parts_freetext_gn1.py` — 6 new tests

## Behavior

- `"fibra 450g, 4 brazos carbono, jaula titanio"` → frame root + `frame_arm` + `frame_cage`
- Clause isolation: cage does not inherit root `fibra`
- Parts-only `"standoffs aluminio"` after frame exists → upsert child; root material unchanged
- Free-text now also persists `configuration` / `wheelbase_mm` on root
- PASS / `BLOCK_TO_COMPONENTS` / BOM N1 unchanged

## Tests

- Targeted G-N1: 6 passed  
- Full suite: **2229** passed (2223 + 6)

## Residual

- G-N2 / G-N3 / G-N4 still optional debt  
- G-N1 **absorbed**
