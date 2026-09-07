# Implementation Review Contract — Geometry Assembly Board Edges B2

**Project:** Jarvis  
**Date:** 2026-09-07  
**Author:** JES / Cursor (Engineer Interface)  
**Reviewer (this contract):** **Claude Code** — independent implementation review  
**Authority after Claude’s report:** Cursor may second-check; Engineer closes on smoke + review PASS

**Status:** READY FOR REVIEW — Engineer ★ (`lanza un contract review`)  
**Why this exists:** Cursor wrote the IC **and** implemented B2 (`b79f819`) — role breach. The existing [implementation_review_geometry_assembly_board_edges_b2.md](implementation_review_geometry_assembly_board_edges_b2.md) is an **implementer self-check only** and is **not** authoritative. Claude must review the shipped code against the IC from scratch.

**Subject IC:** [implementation_contract_geometry_assembly_board_edges_b2.md](implementation_contract_geometry_assembly_board_edges_b2.md)  
**Subject report (implementer):** [implementation_report_geometry_assembly_board_edges_b2.md](implementation_report_geometry_assembly_board_edges_b2.md)  
**Commit under review:** `b79f819` (and any follow-ups on `main` that touch B2 files)

**Baseline claimed:** package **`0.3.8`** · suite **2385**

**Output (required):** `.jes/artifacts/implementation_review_geometry_assembly_board_edges_b2_claude.md`  
Verdict: **PASS** | **PASS WITH NOTES** | **FAIL** — with checklist + independent verification commands.

---

## 0. Your role

You are the **independent reviewer**, not the implementer.

- Do **not** trust the Cursor self-check or the implementer report without re-checking the tree.
- Do **not** implement new features or “improve” B2 beyond fixing a **clear IC violation** you document (prefer FAIL + stop over silent scope expansion).
- Do **not** open pose / fit / Continuity changes.
- Do **not** bump package version.
- Do **not** weaken or delete tests to make the suite pass.

---

## 1. Review scope (locked)

Verify the **shipped** B2 against every lock in the IC, especially:

| # | Lock | What to verify |
|---|---|---|
| 1 | Authority | Edges come from projector `mountedOn`, **not** from parsing `"montado en"` field text in the UI |
| 2 | Source | Only `ComponentSpec.mounted_on`; no inference from layout / drag / BOM |
| 3 | Stale target | Target missing from `components` → **no** `mountedOn` DTO; text field may still show the key |
| 4 | Layout | `x`/`y`/`kind` unchanged by mount relation; no auto-reposition |
| 5 | Honesty | No ensamblado / cabe / verificado / fit copy on edges |
| 6 | Non-goals | No pose fields, no fit, no Continuity edits, no writer/schema fork, no version bump |
| 7 | Tests | T1–T5 (pytest) + U1–U3 (vitest) exist and match IC intent |
| 8 | Suites | Re-run and report counts |

Also check:

- Diff scope matches IC §5 (no surprise files).
- `ui/spatial-board` `npm test` + `npm run typecheck`.
- Full `python -m pytest -q`.
- macOS casing note (`mountEdgeGeometry.ts` vs `MountEdges.tsx`) — confirm no broken imports.

---

## 2. Required procedure

1. Read the IC end-to-end.
2. `git show b79f819 --stat` (and `git log -1 --oneline` if HEAD moved).
3. Read the actual code: `spatial_board.py`, `types.ts`, `mountEdgeGeometry.ts`, `MountEdges.tsx`, `InfiniteCanvas.tsx`, CSS, both test files.
4. Run:
   - `python -m pytest -q tests/test_geometry_assembly_board_edges_b2.py`
   - `cd ui/spatial-board && npm test && npm run typecheck`
   - `python -m pytest -q` (full suite; report count)
5. Write `implementation_review_geometry_assembly_board_edges_b2_claude.md` with:
   - Verdict
   - Checklist vs IC §0 / §3 / §4 / §6 / §7
   - Independent verification table (commands + results)
   - Notes / residuals (including whether Engineer Board smoke is still required)
   - Explicit statement: Cursor self-check is non-authoritative

---

## 3. Fail conditions (examples)

FAIL (or PASS WITH NOTES that block close) if you find:

- UI invents edges from field labels without `mountedOn`
- `mountedOn` emitted for a target not in `components`
- Layout/`parent_key`/glyphs/Continuity/writer mutated beyond IC
- Missing required tests or weakened suite
- Honesty-theater copy on edges
- Pose/fit sneak-in

---

## 4. Explicit non-goals of this review contract

- Do not implement pose B1+ or fit stubs.
- Do not close the assembly queue item without Engineer Board smoke (name it as residual even on PASS).
- Do not rewrite the IC unless you find a contractual contradiction — if so, **STOP** and ask; do not silently reinterpret.

---

## 5. Done criteria

- [ ] Independent review artifact written at the path above
- [ ] Verdict stated
- [ ] Commands re-run; counts reported
- [ ] Residuals named (smoke, notes, any FAIL fixes needed)
- [ ] No unauthorized code changes (or only minimal IC-violation fixes documented in the review)

---

## 6. After Claude finishes

Cursor may acknowledge the Claude review. Engineer Board smoke remains the product gate for closing cola **1/3**. Pose/fit stubs stay **QUEUED — DO NOT IMPLEMENT**.
