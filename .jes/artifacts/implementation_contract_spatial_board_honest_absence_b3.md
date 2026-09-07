# Implementation Contract — Spatial board honest absence (B3)

**Project:** Jarvis  
**Date:** 2026-09-05  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS WITH NOTES** · honesty slice closable  
**Review:** [implementation_review_spatial_board_honest_absence_b3.md](implementation_review_spatial_board_honest_absence_b3.md)  
**Report:** [implementation_report_spatial_board_honest_absence_b3.md](implementation_report_spatial_board_honest_absence_b3.md)  
**★:** [engineer_ratification_spatial_board_product_limits.md](engineer_ratification_spatial_board_product_limits.md)  
**Parents:** investigation report + review **PASS WITH NOTES** (product limits)

**Type:** Projector-only honesty. Display-only architecture slots.  
**Not** BOM. **Not** ERF. **Not** acquisition. **Not** layout-on-disk. **Not** a visor CSS rewrite.

**Baseline:** tag **`v0.3.8`** / `checkpoint-spatial-board-projector` (`f3deae0`)

**Buy (locked):** **B3** — missing expected keys of **declared** `system_blocks` appear as `kind: "slot"` cards.

---

## 0. You

- Edit only files in §5.
- Python projector emits slots. The visor already renders `kind: "slot"` (dashed card, muted minimap). **Do not change `ui/`** unless a test proves a type error — default is **zero frontend files**.
- Do **not** import `build_component_bom`, `engineering_readiness`, or Continuity.
- Do **not** change `BLOCK_TO_COMPONENTS`, writers, orchestrator, or `_derive_overall`.
- Do **not** add HTTP write routes or card click → `definir`.
- Do **not** bump version. Do not weaken unrelated tests. Full Python suite green. `npm test` in `ui/spatial-board` still 4/4 (no visor edits expected).

---

## 1. Intent

```text
Declared system_blocks + BLOCK_TO_COMPONENTS expected key
  not present in design_properties.components
        ↓
  SpatialNode kind="slot", id=key, display-only
        ↓
  Engineer sees "not yet declared" ≠ "does not apply to this architecture"
```

A declared empty-name `ComponentSpec` (e.g. `flight_controller` with `name=""`) stays `kind: "component"`. That is a spec, not a slot.

---

## 2. Locked behavior

### 2.1 When to emit a slot

Let `blocks = state.design_properties.system_blocks` (declared architecture).  
Let `expected` = first-seen keys walking `blocks` in order, each `BLOCK_TO_COMPONENTS.get(block, [])` — **dedupe** (`motors` in propulsion+energy once; first block wins the lane).

Emit `kind: "slot"` for each key in `expected` that is **absent from** `components` (the dict key is missing). Presence as a child (`parent_key` set) still counts as present — **no** slot.

Do **not** emit slots for:

- keys whose only owning catalog blocks are **not** in `system_blocks` (e.g. `wheels` while `actuation` undeclared) — keep today’s virtue
- extra / unknown component keys (those remain real cards)
- frame parts (`frame_arm`, …) — they are not in `BLOCK_TO_COMPONENTS`

### 2.2 Empty components (review N2)

**Forbidden** after this IC: `if not components: return []` while `system_blocks` is non-empty.

| `components` | `system_blocks` | Result |
|---|---|---|
| empty | empty / missing | `[]` (unchanged) |
| empty | 4/4 aerial | slots for every expected key of those blocks (deduped) |
| some specs | 4/4 | real cards + slots for missing expected keys |

The visor empty copy (`nodes.length === 0`) then disappears when slots exist — that is intended. No `ui/` change.

### 2.3 DTO (no ComponentSpec)

Do **not** call the current `place()` helper for slots — it does `components[key]` (review N3). Sibling helper.

```text
id            = key
title         = key
declaredName  = ""          # SpatialCard already shows “sin nombre declarado”
kind          = "slot"
fields        = [{"label": "estado", "value": "no declarado"}]
width/height  = same CARD_* defaults as a one-field card
x,y           = same lane recipe as a root in that column
```

No SKU, no properties, no completeness, no BOM bucket labels (`incomplete` / `declarative` / `✗`).

### 2.4 Lane + order

- Lane index = index of the **first** declared block that lists the key in `BLOCK_TO_COMPONENTS` (same first-match rule as `_lane_index` for roots).
- Iterate **all** declared block columns `0 .. len(blocks)-1`, not only columns that already have a real root. Otherwise battery/FC slots never appear when only `motors` exists (today `lane_count` follows occupied root lanes — **must change** for slots).
- Within a column, walk that block’s `BLOCK_TO_COMPONENTS` list: if the key is in `components` as a root, place the real card then its children; if missing, place the slot. Then place extra roots assigned to that column that were not in the catalog list (unchanged). Then orphans (unchanged).
- Extra column `len(blocks)` remains for roots that match no declared block.

### 2.5 U0 / click (★)

- 1 `ComponentSpec` = 1 `component` or `part` card. Slots are absence markers only.
- No visor handler that starts DEFINE, catalog, or any writer. Existing drag/resize overlay on a slot is allowed (layout only).

### 2.6 Docs (same PR)

- `docs/system_map/00_entry/ENTRY_MAP.md`: one row in the adapters table for `adapters/cli/board.py` (launcher) and `workspace/spatial_board.py` (read-only projector). **No new C-xxx.**
- `README.md` Pizarra blurb: one honest clause — slots are architecture gaps, not BOM/completeness. CLI still mutates.

Update `spatial_board.py` module docstring: it currently says it does not invent absent slots — that sentence becomes false.

---

## 3. Tests (mandatory)

File: `tests/test_spatial_board_projector.py` (extend; do not gut).

| Test | Assert |
|---|---|
| Replace `test_does_not_invent_missing_architecture_slots` | 4 blocks + only `motors` → **no** `wheels` slot; **has** slots `propellers`, `esc`, `battery`, `frame`, `flight_controller`, `sensors`; `motors` is `kind=component` not slot |
| No blocks, only `motors` | ids `== ["motors"]` — still invents nothing |
| Empty `components`, 4 blocks | only slots; ids = deduped expected of those blocks; all `kind=="slot"` |
| Fixture A (review) | motors/battery/frame/`frame_arm`/empty FC present; slots `propellers`,`esc`,`sensors`; FC `kind=="component"` and `declaredName==""` |
| Present key never dual | `esc` as `ComponentSpec` → that node is `component`, no second slot id `esc` |
| Slot payload | `fields == [{"label": "estado", "value": "no declarado"}]`; no `SKU` |
| Module isolation | `spatial_board.py` source does not mention `build_component_bom` / `engineering_readiness` / `project_continuity` (string/import check or grep in test) |

Existing tests that assumed “only declared specs” must be updated **only** where they used 4 `system_blocks` plus a subset of keys (they will now grow slots). Tests with `system_blocks=[]` stay card-only.

Do not commit `workspace/`.

---

## 4. Explicit non-goals

B1 `spatial_layout.json` · B2 poll/mtime · B4 `PropertyValue.source` · B5 grouping · lane labels · glyphs · Continuity/ERF on the board · catalog pick from card · edges · PRODUCT_SCOPE · version bump · new C-xxx · `ui/` restyle · ESC-only special case.

---

## 5. Files you may edit

| Path | Role |
|---|---|
| `src/jarvis/workspace/spatial_board.py` | §2 |
| `tests/test_spatial_board_projector.py` | §3 |
| `docs/system_map/00_entry/ENTRY_MAP.md` | §2.6 one table row |
| `README.md` | §2.6 one clause on Pizarra |

---

## 6. Done criteria

- Fixture A class: missing expected keys visible as slots; undeclared-block keys not invented  
- Empty components + blocks → slots, not `[]`  
- `git diff` shows **no** `project_closure` / `engineering_readiness` / `ui/spatial-board/src` (unless you were forced by types — default none)  
- Targeted projector tests + full `pytest` green  
- Report: `implementation_report_spatial_board_honest_absence_b3.md` (files, behavior, tests, residual: B1 next)

---

## 7. After implementation

Cursor reviews against this IC. On PASS, board honesty slice can close. Next product Buy remains **B1** (layout in the project tree) — separate IC, not this one.
