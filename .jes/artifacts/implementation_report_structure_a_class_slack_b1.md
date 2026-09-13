# Implementation Report — Structure A LEVEL A class slack (5.x-on-5)

Status: Done — awaiting review + Engineer smoke
Parent: `implementation_contract_structure_a_class_slack_b1.md`
Baseline: package `0.4.1` (unchanged) · suite `2735` → `2742` (2735 + 6 new via `python -m pytest -q tests/test_structure_a.py`, +1 net from full-suite external state at time of run). UI `83` (unchanged — no `ui/` file touched)

## Engineer ★

Presented via `AskUserQuestion` (Option A default / Option A custom slack /
Option D hold). **The Engineer chose Option A with SLACK = 0.25 in** — the
IC's own recommended default.

## Summary

`frame_class_compatibility_state`'s LEVEL A predicate widened from strict
`D <= size_class_inch` to `D <= size_class_inch + FRAME_CLASS_SLACK_IN`
(0.25 in), a single named module-level constant. This reflects the
IC's own product framing: "frame 5\"" is a commercial FPV size class
(props commonly run 5.0–5.25in on a nominal-5" frame), not a geometric
ceiling of exactly 5.000in. This directly unblocks the live `#4*` smoke
stack — Gemfan Hurricane MCK 51466-3 (sourced `diameter_in=5.189`) on
GEPRC GEP-Racer (declared `size_class_inch=5`) — while a genuinely wrong
class (a real 6" or 7" prop on a 5" frame) still fails: still LEVEL A
convention, never a geometric fit proof, never "cabe"/VERIFIED/"misfit
geométrico".

## Files changed

- `src/jarvis/core/project_closure.py`:
  - New module-level constant `FRAME_CLASS_SLACK_IN = 0.25`, placed
    immediately above `frame_class_compatibility_state`, with a docstring
    explaining the FPV commercial-class rationale and explicitly stating
    it is NOT a clearance budget and proves nothing about physical fit.
  - `frame_class_compatibility_state`'s own docstring and final compare
    updated: `"class_compatible" if diameter_in <= size_class_inch +
    FRAME_CLASS_SLACK_IN else "class_incompatible"`. No other branch
    (`not_required`/`missing`) touched. Return token set unchanged.
  - `frame_next_missing_question`'s `class_incompatible` copy: added
    `", incluso con el margen de clase habitual ({FRAME_CLASS_SLACK_IN:g}
    in)"` — the message previously hardcoded "supera la clase declarada"
    with no acknowledgment that a margin was already applied before the
    gap fired; now honestly discloses that the excess is real even after
    slack. Never claims "cabe"/fit — unchanged wording otherwise.
- `src/jarvis/core/project_continuity.py` — `_frame_class_next_step`'s
  `GAP-FRAME-PROP-SIZE` branch: same slack-disclosure addition as above,
  now importing `FRAME_CLASS_SLACK_IN` alongside the existing
  `propeller_diameter_in` import. This is the Continuity CTA the IC's own
  §3.2 table names ("Keep LEVEL A... may say class screening uses
  commercial slack — never 'cabe'").
- `src/jarvis/core/engineering_readiness.py` — `_frame_class_gaps`:
  imported `FRAME_CLASS_SLACK_IN` alongside the existing
  `frame_class_compatibility_state` import; appended one additional
  `GapEvidence(source="project_closure.FRAME_CLASS_SLACK_IN",
  fact=f"slack_in={FRAME_CLASS_SLACK_IN}")` to the `GAP-FRAME-PROP-SIZE`
  gap's evidence list (only that gap — `GAP-FRAME-SIZE-MISSING`'s own
  evidence list is unaffected, since slack is irrelevant when no class is
  declared at all). Per the IC's own §3.2 table ("Gap evidence fact may
  include `slack_in=0.25`") — optional, implemented for full audit
  transparency of why the predicate passed/failed.
- `tests/test_structure_a.py` — added T1–T6 (six new tests) right after
  the existing `test_no_propeller_diameter_structure_still_complete_
  no_gap`, see below. Zero existing tests in this file were modified —
  the pre-existing `test_misfit_7in_prop_5in_class_gap_and_incomplete_
  thrust_unchanged` (D=7.0 vs class 5.0) already serves as the T6
  regression the IC's own §4 table asks for (7.0 > 5.25, still
  incompatible) — confirmed still green, unchanged.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD ACTUAL synced (suite `2742`,
  new 🟡 LANDING entry, queue updated).
- `.jes/state/engineering_state.json` — top-level tracking fields synced;
  `engineer_ratification` left untouched.

**Not touched**: `_bom_completeness_tail`'s frame tail (`"clase
incompatible nivel A"`, no strict-inequality claim — remains accurate
regardless of slack, no update needed), `GAP-FRAME-SIZE-MISSING`'s own
message/severity/blocks (unchanged — a missing class still gates
Structure exactly as before), gap `gap_type`/`severity`/`blocks`/
`instance_key` (all unchanged — this is a predicate change only, never a
new gap shape), any catalog seed's `diameter_in`/`size_class_inch` values
(Gemfan/GEP-Racer numbers untouched — the IC's own explicit "not changing
Gemfan/GEP catalog numbers" boundary), `PlateSeed`/`StandoffSeed`/prop
schema, `ui/spatial-board/**`, `pyproject.toml` (version still `0.4.1`).

## Behavior changed

- `frame_class_compatibility_state("class_compatible")` now includes any
  `D` up to `size_class_inch + 0.25` — previously only `D <=
  size_class_inch` exactly.
- `GAP-FRAME-PROP-SIZE` no longer fires for the Gemfan 51466-3 / GEP-Racer
  pairing (verified live on `autonomía-de-5min` below).
- Two prompt/CTA strings (`frame_next_missing_question`,
  `_frame_class_next_step`) now disclose the slack margin when a
  `class_incompatible` gap DOES fire, so the Engineer understands the
  excess survived a real margin allowance rather than being flagged on a
  razor-thin strict inequality.
- `GAP-FRAME-PROP-SIZE`'s own `GapEvidence` list gained one additional
  fact (`slack_in=0.25`) — additive, no existing evidence fact removed or
  reworded.
- Unchanged: `GAP-FRAME-SIZE-MISSING` (message, severity, blocks, and the
  condition that triggers it), gap type identifiers, `_bom_completeness_
  tail`'s frame string, every calculation-engine-facing number (thrust/
  power/RPM/Ct — `frame_class_compatibility_state` never touches those,
  confirmed by the pre-existing `test_misfit_7in_prop_5in_class_gap_
  and_incomplete_thrust_unchanged` test still passing unmodified).

## Tests

Added to `tests/test_structure_a.py` (6 new tests, T1–T6; the IC's own T6
regression request is already covered by the pre-existing 7in-vs-5in
test, confirmed unchanged/still green):
- T1 `D=5.189`, class `5` → `class_compatible`; `build_engineering_
  readiness` shows zero frame-class gaps; `structure` block reads
  `"complete"`.
- T2 `D=6.0`, class `5` → `class_incompatible`; `GAP-FRAME-PROP-SIZE`
  still fires (a true 6" prop on a 5" class is genuinely wrong even under
  slack).
- T3 `D=5.0`, class `5` → `class_compatible` (unchanged exact-match happy
  path).
- T4 `D=5.189`, class missing → `"missing"` (slack irrelevant when no
  class is declared — unchanged).
- T5 Live-shaped: the exact Gemfan 51466-3 (`5.189`) + GEP-Racer (`5`)
  pairing produces zero `GAP-FRAME-PROP-SIZE`.
- T6 `GAP-FRAME-PROP-SIZE`'s evidence carries `slack_in=0.25` (the exact
  `FRAME_CLASS_SLACK_IN` value, read from the module rather than
  hardcoded in the test); gap title still contains none of the forbidden
  tokens (`cabe`/`verificado`/`verified`/`does not fit`/`fits`/`misfit
  geométrico`).

Executed:
- `python -m pytest -q tests/test_structure_a.py` → **18 passed** (12
  pre-existing + 6 new).
- `python -m pytest -q` (full suite) → **2742 passed**.
- Manual smoke directly against the LIVE `autonomía-de-5min` workspace
  (which already has both GEP-Racer and Gemfan Hurricane MCK 51466-3
  bound from the prior `#4e`/`#4g` cycles): `frame_class_compatibility_
  state(state) == "class_compatible"`; `build_engineering_readiness(
  state).gaps == []` — zero gaps of ANY kind on this project, confirming
  the class gate no longer blocks Structure for this exact real stack.

## Non-goals honored

- No CAD, no clearance calculation, no plate L×W, no standoff Ø — this
  Buy is a predicate-only change, nothing geometric was added.
- `GAP-FRAME-SIZE-MISSING` untouched — a frame with no declared class
  still gates Structure exactly as before.
- No Gemfan/GEP-Racer catalog numbers changed (`diameter_in=5.189`,
  `size_class_inch=5` both untouched — the slack lives entirely in the
  predicate, never in the seed data).
- No version bump (`0.4.1` unchanged).
- No "cabe"/VERIFIED/"misfit geométrico" language introduced anywhere —
  confirmed by T6's own forbidden-token assertion and by manual review of
  both updated copy strings.

## Remaining risks

- None specific to this Buy. `FRAME_CLASS_SLACK_IN` is the single named
  constant every call site reads (`frame_class_compatibility_state`'s own
  compare, both prompt-copy sites, and the gap-evidence fact) — no
  duplicated inequality or magic `0.25` literal exists anywhere else in
  the codebase (confirmed via `grep` before finishing this cycle).
