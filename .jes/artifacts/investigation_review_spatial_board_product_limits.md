# Investigation Review — Spatial board product limits

**Date:** 2026-09-05  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_spatial_board_product_limits.md](investigation_contract_spatial_board_product_limits.md)  
**Report:** [investigation_report_spatial_board_product_limits.md](investigation_report_spatial_board_product_limits.md)  
**Base:** tag **`v0.3.8`** / `f3deae0`

## Verdict

**PASS WITH NOTES**

Primary Buy **B3 (honest absence / architecture slots)** accepted. Tie-break vs B1/B2 is correct: the board currently **omits** expected undeclared keys while BOM already prints `✗ …: no definido`. Cosmetic Buys rejected. **Not** for silent implementation — Engineer ★ on Buy, then IC.

No `src/` / `ui/` / `tests/` from this investigation (report-only). Confirmed.

---

## Checklist

| Criterion | Result |
|---|---|
| A–H shape | **Pass** |
| Authority thesis holds (read-only projector, CLI mutates) | **Pass** — two GET routes only (`vite-plugin-jarvis-projects.ts:131-159`); two `fetch()` in UI (`projects.ts:15,23`); no writers imported |
| One real over-claim (missing architecture keys silent) | **Pass** — independent Fixture A (below) |
| Slot kind already in visor | **Pass** — `types.ts:21`, `.sb-card--slot` dashed (`spatial-board.css:128-131`), minimap `sb-minimap__dot--${n.kind}` (`Minimap.tsx:46`), fixture `esc` slot (`fixtures.ts:33-42`) |
| B3 does not duplicate BOM/ERF | **Pass** — skeleton uses `BLOCK_TO_COMPONENTS` + `system_blocks`, not `build_component_bom` |
| B5 grain rejected without drowning proof | **Pass** — children stack (`spatial_board.py:83-86`; existing test) |
| Cosmetic / CAD / Conversation Engine / card writers out | **Pass** |
| PRODUCT_SCOPE not rewritten; README visor copy honest | **Pass** — `README.md:29` “el CLI sigue mutando el diseño” |
| No `src/` from investigation | **Pass** |

---

## Independent verification

### Fixture A (Cursor, this review — `tmp_path` equivalent)

4/4 blocks; `motors`+SKU, `battery`, `frame`+`frame_arm`, empty-name `flight_controller`; **no** `esc` / `propellers` / `sensors`.

| Surface | Result |
|---|---|
| Board ids | `motors`, `battery`, `frame`, `frame_arm`, `flight_controller` — **no** `esc` |
| Empty FC | `kind=component`, `declaredName=""` |
| BOM `missing` | `['propellers', 'esc', 'sensors']` |
| BOM lines | `✗ propellers / esc / sensors: no definido` |

Lie confirmed: **three** architecture holes, not ESC-only. B3 must emit a slot per missing **expected** key of **declared** `system_blocks`, deduped (motors in propulsion+energy once).

Empty `components={}` + same four blocks → projector returns `[]` (`spatial_board.py:33-34`). Same silent-complete class at project scale (N2).

### Other claims

| Claim | Cursor check |
|---|---|
| Projector never invents slots today | **Confirmed** — `test_does_not_invent_missing_architecture_slots`; `place()` only keys in `components` |
| `_format_property` ignores `.source` | **Confirmed** — `spatial_board.py:138-148` |
| `source="calculated"` is a live writer | **Confirmed** — `component_sync.py:67-69` (`motor_count`), not only the docstring at `:49` |
| Fetch effect depends only on `projectId` | **Confirmed** — `useBoardNodes.ts:40-66` |
| Layout key outside workspace | **Confirmed** — `useBoardNodes.ts:8-9,23-29` |
| `kind` unused in gestures | **Confirmed** — CSS/minimap class only |
| ENTRY_MAP has no board adapter row | **Confirmed** — CLI + MCP only (`ENTRY_MAP.md:9-13`) |

---

## Notes

### N1 — B3 is the missing-key **class**, not an ESC special case

Report’s narrative leads with ESC (design U6). Fixture A BOM missing is `propellers`, `esc`, `sensors`. IC must not ship “ghost ESC only.”

### N2 — `if not components: return []` would skip slots on an architecture-only project

IC must emit slots from `system_blocks` **even when** `components` is empty, or the empty-state copy (“Sin componentes declarados”) still hides the same holes. Today that early return is correct for “no specs”; after B3 it is a hole.

### N3 — Cannot reuse `place()` for slots

`place()` does `spec = components[key]` (`spatial_board.py:60-61`). Slot emission needs a sibling helper (fixed `kind="slot"`, no `ComponentSpec`). Naive `place("esc", col)` KeyErrors.

### N4 — Keep the old test’s **other** half

`test_does_not_invent_missing_architecture_slots` must be **replaced**, not deleted without a successor: still **no** slots for keys whose block is **not** in `system_blocks` (e.g. `wheels` while actuation undeclared). That half remains a virtue.

### N5 — Display-only: slot click must not start DEFINE

Locked stance #1. IC: no acquisition/catalog from the dashed card. Same drag/resize as any card is fine (layout overlay only).

### N6 — Continuity stays CLI (contract §3.11)

Report has no dedicated §3.11 paragraph (points at “§H11”, which does not exist). Substance is still **inspect-only**; Continuity/ERF chrome correctly forbidden. IC must not sneak a next-step line onto the toolbar.

### N7 — U0 vs slots (Engineer ★ one-liner)

A slot is **not** a `ComponentSpec`. That does not violate “1 spec = 1 card”; it adds a second presentation kind the visor already typed. ★ should lock: **U0 unchanged for declared specs; slots are absence markers only.**

### N8 — Field reconstructions not dumped in the report

Contract §6 asked for Fixture A/B/C records. A is implied, not tabulated; B/C are code-reasoned (allowed for B). Cursor re-ran A. Does not change Buy.

---

## Engineer ★ decisions needed

1. **Buy = B3?** (Cursor recommends **yes** — removes the omission lie; B1 layout-on-disk next, not this IC.)  
2. **Slot set = all missing `BLOCK_TO_COMPONENTS[declared block]` keys, deduped** — not ESC-only (N1)?  
3. **Empty `components` + declared blocks still emit slots** (N2)?  
4. **U0 one-liner** (N7)?  
5. **No click → DEFINE** (N5)?

After ★, Cursor writes the Implementation Contract. Claude implements from that IC only.
