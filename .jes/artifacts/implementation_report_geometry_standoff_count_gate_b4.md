# Implementation Report — Standoff count gate for corner copies B4-min

**IC:** [implementation_contract_geometry_standoff_count_gate_b4.md](implementation_contract_geometry_standoff_count_gate_b4.md)
**Implementer:** Claude Code
**Date:** 2026-09-10
**Baseline:** package `0.4.0` · suite 2652 → **2661** (2652 + 9 new; old B3 file's tests amended, not added)

---

## Files changed

| File | Change |
|---|---|
| `src/jarvis/workspace/spatial_board.py` | `_frame_standoff_corner_offsets_mm` gained a new leading gate: reads `standoff_spec.properties["count"]`, parses it via the existing `_parse_solid_copies_count` (whole number in `[2,16]`), and requires it to equal exactly `_STANDOFF_CORNER_COUNT` (4) — missing, non-numeric, out-of-range, or any N≠4 all return `None` before the existing box/plate/inset checks even run. Because both `_solid_copies`'s `frame_standoff` branch and `_solid_copy_offsets_mm`'s `frame_standoff` branch call this SAME helper, the count gate applies to both in lockstep automatically — no separate gate needed at either call site. Docstrings on `_frame_standoff_corner_offsets_mm` and the two call sites updated to describe the count gate and explicitly note it supersedes B3's unconditional default of 4. |
| `tests/test_geometry_frame_standoff_corners_b1.py` | Amended (not deleted): `_standoff_spec()` gained a `count: float | None = 4.0` parameter, defaulting to `4.0` so the existing 6 tests keep proving the **corner formula** itself (unchanged) independent of the new gate. Module docstring updated to point to the new dedicated gate-test file. |
| `tests/test_geometry_standoff_count_gate_b4.py` | **New.** P1–P8 exactly per IC §3 (P3 parametrized ×2), including the required regression: a standoff with `count` absent must **not** get `solidCopies` (B3's old default is gone). |

`ui/`, `library/`, `workspace/`, `pyproject.toml` — confirmed **untouched** by this cycle (`git status --short` shows no new changes on any of them; version still `0.4.0`).

---

## Behavior changed

- `frame_standoff` now requires a declared `properties["count"]` that parses to **exactly 4** — in addition to the unchanged box/Main-Plate/inset gates from B3 — before `solidCopies`/`solidCopyOffsetsMm` are emitted. Missing, non-numeric, out-of-range, or any N≠4 (verified for both 3 and 6) all omit both keys entirely, leaving the standoff as a single honest box.
- This is a **breaking, intentional** behavior change from B3: a standoff+plate box pair with no `count` declared no longer draws four corner posts — it draws one box. Verified live on `autonomía-de-5min`, whose `frame_standoff` has no `count` property today (`properties` keys: `material`, `length_mm`, `width_mm`, `height_mm`) — the corner ×4 correctly disappears (`solidCopies`/`solidCopyOffsetsMm` both `None`), exactly matching the IC's own named "live regression, accepted."
- The count source is exactly `frame_standoff.properties["count"]` — verified directly against `catalog_bind.py:506` (`props["count"] = PropertyValue(value=count, ...)`) and `catalog_bind.py:579` (`FRAME_STANDOFF_KEY, "standoff", spec.standoff_count, ...`), confirming this is the exact key `frame_part_specs_from_catalog` already projects a catalog `FrameSpec.standoff_count` into — no new property name invented, and no `library`/`get_frame` call was added to the projector.
- The corner formula itself (`_main_plate_corner_points`, the `hx`/`hy` inset math) is completely unchanged — verified by the amended B3 test file's 6 tests still passing byte-for-byte once `count=4` is added to the fixture.
- Setting `count=4` on the live 5min standoff (read-only, not saved) immediately restores the four `(±47.5, ±47.5, 0)` corner offsets, confirming the positive path works end to end.

---

## Tests added / executed

Amended: `tests/test_geometry_frame_standoff_corners_b1.py` — 6/6 still passing with `count=4` added to the default fixture (corner formula regression, unaffected by the new gate).

New: `tests/test_geometry_standoff_count_gate_b4.py` — 9/9 passing:
- P1: `count=4` + boxes → `solidCopies==4`, correct offsets.
- P2: `count` absent → no `solidCopies`/offsets (the required regression vs. B3's old unconditional default — confirmed this does **not** stay green without the fix).
- P3 (×2): `count=3` and `count=6` → no copies.
- P4: `count=4` but missing standoff geometry, missing plate, or plate without L×W → no copies in all three cases.
- P5: `count=4` but standoff larger than plate → fails closed.
- P6: offsets still differ from motors' quad-X points even with a `quad_x`+230mm frame present.
- P7: exactly one `frame_standoff` node.
- P8: motors/propellers/frame_arm/prop_adapter's own quad-X copy behavior unaffected.

Full suite: `python -m pytest -q` → **2661 passed**, 0 failed.

---

## Live verification (read-only)

Read the real `autonomía-de-5min` project (never saved back): `frame_standoff` has properties `material`/`length_mm`/`width_mm`/`height_mm` but **no** `count` — after this change, `solidCopies` and `solidCopyOffsetsMm` are both `None` (the corner ×4 disappears, exactly the accepted live regression the IC named). Separately, constructing an in-memory copy of the same state with `count=4` added (never written to disk) immediately restores `solidCopies==4` and the identical `(±47.5, ±47.5, 0)` corner offsets from before.

---

## Non-goals honored

No Continuity `declara standoff_count…` grammar added. No N≠4 layout (row or Engineer-typed offsets) implemented — any count other than 4 simply omits, per lock #4/#10. No `library/frames/_datos.json` seed added or changed — the Rooster row still has no `standoff_count`, confirmed unchanged. No `motor_count`/`quad_x`/`current_parameters` read anywhere in the new gate. No `ui/` change. No Conversation Engine. No version bump.

---

## Remaining risks

- None identified specific to this change — the count gate lives entirely inside the one already-shared helper both call sites use, so `solidCopies` and `solidCopyOffsetsMm` cannot drift apart, and every fail-closed path is directly exercised by tests.
- As explicitly named by the IC itself: this is a deliberate, accepted regression on any live project whose `frame_standoff` has no `count` (e.g. today's `autonomía-de-5min`) — the Engineer smoke must set `count=4` explicitly (via free text or a future cited catalog seed) to see the corner ×4 again.
- N≠4 declared layouts (row fallback, or Engineer-typed per-post offsets) remain unimplemented, as explicitly deferred by the IC (§0 lock #10) — a standoff with `count=6`, for example, currently renders as a single box with no copies at all, not a row of 6.
