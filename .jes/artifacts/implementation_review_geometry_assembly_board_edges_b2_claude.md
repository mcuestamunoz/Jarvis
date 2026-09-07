# Implementation Review (Independent) — Geometry Assembly Board Edges B2

**Reviewer:** Claude Code — independent review, per [implementation_review_contract_geometry_assembly_board_edges_b2.md](implementation_review_contract_geometry_assembly_board_edges_b2.md)
**Date:** 2026-09-07
**Subject IC:** [implementation_contract_geometry_assembly_board_edges_b2.md](implementation_contract_geometry_assembly_board_edges_b2.md)
**Subject report (implementer, Cursor):** [implementation_report_geometry_assembly_board_edges_b2.md](implementation_report_geometry_assembly_board_edges_b2.md)
**Commit reviewed:** `b79f8197de1284fed5b719c613201554ca23faf1` — confirmed HEAD (`ae2519c`) adds only this review's own contract + doc/state bookkeeping, zero B2 code follow-ups (`git log b79f819..HEAD --stat`).

**Explicit statement (per role split):** the existing `implementation_review_geometry_assembly_board_edges_b2.md` is Cursor's own **implementer self-check** and is **not authoritative**. Everything below was independently re-derived from the shipped tree and re-run commands — nothing here is taken on the self-check's word, though where its claims happened to match what I found, that is noted.

---

## Verdict: **PASS**

No IC violation found. No fail condition from §3 of the review contract triggered. One residual is named (Engineer Board smoke, per the IC's own done-criteria — not a code gap) and one minor scope note (extra queue/bookkeeping files beyond the IC's literal §5 table — docs/state only, zero behavior).

---

## Checklist vs IC §0 / §3 / §4 / §6 / §7

| # | Lock (IC §0/§3) | Verified | Evidence |
|---|---|---|---|
| 1 | Authority: edges from projector `mountedOn`, not UI-parsed `"montado en"` text | ✅ | `mountEdgeGeometry.ts` reads only `node.mountedOn`; never references `node.fields` anywhere (grep confirmed zero hits) |
| 2 | Source: only `ComponentSpec.mounted_on`; no layout/drag/BOM inference | ✅ | `spatial_board.py`'s `place()` reads `spec.mounted_on` directly; `mountEdgeSegments` reads only `node.x/y/width/height` (post-overlay rects) and `node.mountedOn` — no BOM/completeness data touched |
| 3 | Stale target → no `mountedOn` DTO; text field may still show key | ✅ | `place()`: `mounted_dto = mounted_on if mounted_on and mounted_on in components else None`; `_fields()` still appends `{"label": "montado en", "value": spec.mounted_on}` unconditionally when `spec.mounted_on` is truthy, regardless of `mounted_dto`. Confirmed by T2, and independently re-verified by re-running it. |
| 4 | Layout: `x`/`y`/`kind` unchanged by mount relation; no auto-reposition | ✅ | `_emit()` computes `x`/`y`/`height` from lane/row logic exactly as pre-B2 (identical formula); `mountedOn` is added to the node dict only when non-`None`, never fed back into the layout computation. T4 asserts `a["x"]==b["x"]`, `a["y"]==b["y"]`, `a["kind"]==b["kind"]` between an unset/mounted twin — re-run, passes. |
| 5 | Honesty: no ensamblado/cabe/verificado/fit copy on edges | ✅ | `MountEdges.tsx` renders a bare `<line>` with no text/label/title/arrowhead at all, `aria-hidden="true"`; grep for `ensamblado\|cabe\|verificado\|correcto\|fit` across all 6 touched UI/py files returns zero hits |
| 6 | Non-goals: no pose fields, no fit, no Continuity edits, no writer/schema fork, no version bump | ✅ | `git show b79f819 --stat` touches zero of `component_writers.py`, `mounted_on_declare_assist.py`, `action_schema.py`, `library/**`; `pyproject.toml` still `0.3.8` |
| 7 | Tests: T1–T5 (pytest) + U1–U3 (vitest) exist and match IC intent | ✅ | Read both files in full — each case matches its IC row exactly, including the stale-target (T2) and layout-invariance (T4) cases; no case is thinned/renamed to something weaker than its IC description |
| 8 | Suites: re-run and report counts | ✅ | See Independent Verification table below — all green, exact counts match the IC's claimed baseline |

**Diff-scope note (not a violation):** `git show b79f819 --stat` includes 6 files beyond the IC's literal §5 table — `implementation_contract_geometry_assembly_board_edges_b2.md` (the IC itself, expected), `implementation_contract_geometry_assembly_pose_b1plus.md` and `implementation_contract_geometry_assembly_fit_compare.md` (queue placeholders 2/3, read in full — both are inert `QUEUED — DO NOT IMPLEMENT` stubs with hard gates, zero code, zero pose/fit fields), `implementation_review_geometry_assembly_board_edges_b2.md` (the self-check, expected given the review-contract's own framing), `.jes/state/engineering_state.json` and `docs/IMPLEMENTATION_TASKS.md` (bookkeeping, the same convention every prior IC in this project's history follows). None of these touch code, schema, or behavior. Flagged for completeness, not treated as a scope breach.

**macOS casing check (explicitly requested):** `git ls-tree -r HEAD --name-only -- ui/spatial-board/src` (case-sensitive, authoritative regardless of local filesystem) confirms `MountEdges.tsx`, `mountEdgeGeometry.ts`, and `mountEdgeGeometry.test.ts` are three distinct, correctly-tracked paths — no collision. Import statements match exactly: `MountEdges.tsx` imports `from "./mountEdgeGeometry"`, `InfiniteCanvas.tsx` imports `from "./MountEdges"`. `npm run typecheck` and `npm run build` both succeed (see below), which would fail on a real casing mismatch even on a case-insensitive dev machine (Vite/tsc resolve by the literal specifier). No stray untracked `mountEdges.ts` file left on disk from the implementer's own noted pre-ship rename (`git status --short` clean).

---

## Independent verification

| Command | Result |
|---|---|
| `python -m pytest -q tests/test_geometry_assembly_board_edges_b2.py -v` | **5 passed** (T1–T5) |
| `cd ui/spatial-board && npm test` | **7 passed** (3 new `mountEdgeGeometry.test.ts` U1–U3 + 4 prior `transform.test.ts`) |
| `cd ui/spatial-board && npm run typecheck` | clean, zero errors |
| `cd ui/spatial-board && npm run build` (extra smoke, not IC-required) | succeeds — `vite build`, 42 modules, no errors |
| `python -m pytest -q` (full suite) | **2385 passed**, 0 failed — matches the IC's claimed baseline exactly |
| `git log b79f819..HEAD --stat` | only this review's own contract + `implementation_review_*.md`/state/doc bookkeeping — zero B2 code follow-ups |
| `git show b79f819 --stat -- src/jarvis/core/component_writers.py src/jarvis/core/mounted_on_declare_assist.py src/jarvis/schemas/action_schema.py library/ pyproject.toml` | empty — none touched |
| `grep -rn "ensamblado\|cabe\|verificado\|correcto" ui/spatial-board/src/MountEdges.tsx ui/spatial-board/src/mountEdgeGeometry.ts` | zero hits |
| `git ls-tree -r HEAD --name-only -- ui/spatial-board/src \| grep -i mountedge` | 3 distinct correctly-cased paths, no collision |

---

## Code-level notes (read in full, not just diffed)

- `place()`'s `mounted_on in components` check is a **provably correct** proxy for "target will be emitted as a node," not a shortcut that happens to work by luck: tracing `project_spatial_nodes`'s full placement algorithm, every key in `design_properties.components` is placed exactly once — as a root (via the `expected_by_column` or lane-sort loops, mutually exclusive via the shared `emitted` set), as a child (placed alongside its root), or as an orphan (its own dedicated loop, for a `parent_key` that isn't itself a component). Slot nodes are synthetic and never share a key with a real component, so `mounted_on in components` can never accidentally match a slot. This satisfies IC §3.1's "among the nodes that will be / have been emitted in this projection" requirement precisely, not approximately.
- `.sb-mount-edges` (`z-index: 0`) vs `.sb-card` (`z-index: 1`, newly added by this same diff) confirms the edge SVG layer is genuinely under cards, not merely earlier in JSX source order (which alone wouldn't guarantee stacking without explicit z-index, since `.sb-card` already needed `position: absolute` and could otherwise stack unpredictably) — this is a correct, deliberate fix, not an accidental ordering dependency.
- `mountEdgeGeometry.ts` and `SpatialCard.tsx` share the exact same coordinate frame (`left: node.x, top: node.y` on an absolutely-positioned `.sb-world` child) — confirmed both read the same `node.x/y/width/height`, so edges track drag/overlay-updated positions correctly without any special-casing.
- Minimap is untouched (confirmed via `git show --stat` and grep) — matches the IC's explicit "optional, may omit" allowance, not a gap.

---

## Residuals (named explicitly, per this review contract's own instruction)

- **Engineer Board smoke is still required** before queue item 1 ("1 of 3") is treated as product-closed — this review verifies code/tests/types only, and cannot substitute for a human looking at the actual rendered canvas. Named per the IC's own done-criteria ("Engineer Board smoke recommended before closing queue item 1") and the review contract's §4 non-goal ("do not close the assembly queue item without Engineer Board smoke").
- Pose B1+ and fit/compare remain **QUEUED — DO NOT IMPLEMENT**, confirmed both stub files are inert placeholders with hard gates and no code — untouched by this review, as instructed.
- No code was changed by this review — no IC violation was found that would have required a minimal fix.

---

## Conclusion

Independently re-verified against the shipped tree, not the self-check's word: the projector emits `mountedOn` only when the target is genuinely a live, projectable component (provably, not just empirically); the UI draws edges exclusively from that machine field, under cards, with zero verification-adjacent copy; layout, `parent_key`, glyphs, the mount-declare writer, and the schema are all byte-identical to before this diff; both required test suites (T1–T5, U1–U3) exist, match the IC's intent, and pass; the full Python suite and the UI `test`/`typecheck`/`build` chain are all green at the counts claimed. **PASS**, with the Engineer Board smoke named as the one outstanding product-level (not code-level) gate.
