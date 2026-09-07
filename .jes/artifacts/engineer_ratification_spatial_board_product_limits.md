# Engineer Ratification — Spatial board product limits (Buy B3)

**Date:** 2026-09-05  
**Authority:** Engineer (`redacta` after review ★ lines)  
**Decision:** Lock Buy **B3 — honest absence** and authorize the Implementation Contract.

**Parents:**
- [investigation_report_spatial_board_product_limits.md](investigation_report_spatial_board_product_limits.md)
- [investigation_review_spatial_board_product_limits.md](investigation_review_spatial_board_product_limits.md) — **PASS WITH NOTES**

## Locked ★

1. **Buy = B3.** Architecture-expected keys missing from `components` render as display-only `kind: "slot"` cards. Not ESC-only: **every** missing key of `BLOCK_TO_COMPONENTS[declared system_block]`, first-block wins (dedupe `motors`).
2. **Empty `components` + declared `system_blocks` still emit slots.** Do not keep `if not components: return []` once blocks exist.
3. **U0 unchanged:** 1 `ComponentSpec` = 1 card. A slot is an absence marker, not a spec.
4. **No click → DEFINE / catalog.** Slot is display-only. Drag/resize layout overlay remains presentation.

**Out of this ★:** B1 layout-on-disk, B2 freshness, B4 source honesty, B5 grouping, Continuity/ERF chrome, PRODUCT_SCOPE rewrite.

## Authorized next

[implementation_contract_spatial_board_honest_absence_b3.md](implementation_contract_spatial_board_honest_absence_b3.md)

Claude implements from that IC only. Cursor reviews. No version bump.
