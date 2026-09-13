# Implementation Report — IDLE frame-part count declare B1

Status: Done (implementation) — awaiting review + Engineer smoke
Parent: `implementation_contract_idle_frame_part_count_declare_b1.md`
Baseline: package `0.4.1` (unchanged) · suite `2679` → `2686` (2679 + 7 new) · UI `83` (unchanged by this Buy — see note below)

## Summary

Added a new IDLE-only deterministic bridge that lets an Engineer declare
frame-part properties ("6 standoffs", "6 separadores", "standoffs
aluminio", "4 brazos fibra") outside the `DEFINE_MISSING` frame wizard,
whenever a frame is already declared with non-`low` completeness. It reuses
the EXISTING `extract_all_frame_part_properties` extractor and the EXISTING
`upsert_frame_part` writer — the same two functions G-N1's wizard-only
parts-only branch already calls — so it is the same feature, reachable
from a second entry point, never a second implementation of it.

## Files changed

- `src/jarvis/core/orchestrator.py`:
  - New method `_try_handle_idle_frame_part_declare(user_input) -> dict |
    None`. Gate, in order: (1) `extract_all_frame_part_properties` must be
    non-empty, else `None`; (2) `extract_frame_properties` must carry NONE
    of `mass_kg`/`size_class_inch`/`configuration`/`wheelbase_mm` (the same
    root guard as G-N1 — a root-shaped update is never taken by this
    bridge); (3) an active project must exist with a declared `frame`
    whose `completeness` is not `low`. On success: loops the declared
    parts through `upsert_frame_part` (unchanged writer), saves via
    `self.workspace_manager.save_state`, and returns `{"status": "ok",
    "action": "component_description_saved", "message": "Frame partes:
    ..."}` — the same message shape and `×N` count suffix G-N1's wizard
    branch already produces. Deliberately DUPLICATES that branch's
    extract+gate+upsert logic (documented in the method's own docstring)
    rather than sharing a helper with it, per the IC's own explicit
    allowance — the wizard branch also drives `still_missing`/
    `_set_pending_next_block` transitions this bridge must never touch, so
    a shared helper would have put the wizard's own tested behavior at
    risk for no benefit to this Buy.
  - Wired into the IDLE dispatch chain right after the fit-attestation
    bridge, before FN-005 — same family/order as pose / envelope / cabe /
    attest.
- `tests/test_idle_frame_part_count_declare_b1.py` (new) — T1–T6, see
  below.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD ACTUAL synced (suite `2686`,
  new 🟡 LANDING entry for this Buy, queue updated).
- `.jes/state/engineering_state.json` — top-level tracking fields
  (`cycle_intent`/`execution_status`/`current_mode`/`active_operation`/
  `movement_trigger`) synced to this cycle; `engineer_ratification` left
  untouched (Engineer-authored territory, not a mechanical status field).

**Not touched**, confirmed via `git diff --stat`: `src/jarvis/domains/
aerial.py` (zero diff — no extract change was needed, no regression
forced one), `ui/spatial-board/**`, `library/**`, `pyproject.toml`
(version still `0.4.1`).

## Behavior changed

- New: IDLE phrases matching a frame-part clause (with an existing,
  non-`low` frame and no root-shaped update in the same phrase) now upsert
  the named child(ren) directly, without opening `DEFINE_MISSING` and
  without calling the LLM.
- Unchanged: the `DEFINE_MISSING` wizard's own parts-only branch (G-N1,
  `expected_keys[0] == "frame"`) — untouched code, regression-tested
  (T5).
- Unchanged: `extract_all_frame_part_properties`, `_props_from_part_
  clause`, `upsert_frame_part`, the B4-min standoff-corner projector gate
  (`count == 4`) — none were edited; this Buy only adds a second call site
  for the first and third.

## Tests

New file `tests/test_idle_frame_part_count_declare_b1.py` (7 tests):
- T1 IDLE `"6 standoffs"` with an existing non-`low` frame → `frame_
  standoff.properties["count"] == 6`, session stays `IDLE`, `_RefuseLLM`
  used (LLM never called).
- T2 `"6 separadores"` → same.
- T3 `"standoffs aluminio"` → material set on the child only; root
  `frame.material` unchanged (`"fibra de carbono"` survives).
- T4 no `frame` declared → `_try_handle_idle_frame_part_declare` returns
  `None` directly; no `frame_standoff` key created.
- T4b (extra) a root-shaped update in the same phrase (`"6 standoffs,
  wheelbase 230mm"`) → `None` (root guard confirmed, not just documented).
- T5 regression: the `DEFINE_MISSING` wizard's own parts-only branch
  (`_open_frame_wizard` + `"4 brazos fibra de carbono"`) still upserts
  `frame_arm` with count 4 and material — unchanged behavior.
- T6 IDLE `"4 standoffs"` → `frame_standoff.properties["count"] == 4` on
  the saved spec (the B4-min projector's own corner gate is untouched
  code, not re-tested here — the IC marks this optional; asserting the
  spec-level `count == 4` was the cheap, sufficient check per the IC's own
  wording).

Executed:
- `python -m pytest -q tests/test_idle_frame_part_count_declare_b1.py` →
  7 passed.
- `python -m pytest -q tests/test_frame_parts_freetext_gn1.py` → 11 passed
  (G-N1 regression, unweakened).
- `python -m pytest -q` (full suite) → **2686 passed** (2679 baseline + 7
  new).

## Non-goals honored

- No N=6/8 station/layout formula, no Rooster/catalog `standoff_count`
  seed, no Continuity `declara el count…` grammar, no LLM pending
  deactivate map, no C-114, no version bump — none touched.
- `extract_all_frame_part_properties`/`_props_from_part_clause` in
  `aerial.py`: zero changes — no regression forced a fix, so nothing was
  edited there.
- `ui/`/`library/` untouched — no projector/visor change; B4-min corners
  still gated on `count == 4` exactly as before.
- The `DEFINE_MISSING` wizard path was not refactored — duplicated
  instead, as the IC explicitly allowed, to avoid risking its tested
  behavior.

## Baseline note (UI count)

The IC's stated baseline was "UI 80", but `npm test` in
`ui/spatial-board` currently reports **83 passing** even before this
Buy's own changes (which touch no `ui/` file at all). This reflects a
`fitAttestationUi.ts`/`fitAttestationUi.test.ts` addition and a
`Solid3D.tsx` nested-hit hotfix that landed via the prior Fit attestation
cycle's own Engineer review + smoke pass (see `docs/
IMPLEMENTATION_TASKS.md`'s "Fit attestation B1... Nested-hit Situar
hotfix ACCEPT in same walk" entry, and `implementation_review_geometry_
fit_attestation_b1.md`) — a real bug fix (the Board button's overlap
check previously used a bare `"se solapan"` substring, which
false-positived on `"no se solapan"`; `isOverlapScreeningCopy` fixes
that) that arrived between this session's last IC and this one, outside
this Buy's own scope. Recorded here for traceability, not attributed to
this Buy's diff.

## Remaining risks

- None specific to this Buy's own change. The duplicated gate logic
  (extract + root-guard + frame-completeness check) between this new IDLE
  bridge and G-N1's wizard branch is an intentional, IC-approved
  duplication — a future extractor/writer signature change would need to
  update both call sites; this is documented in both docstrings pointing
  at each other.
