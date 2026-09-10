# Implementation Report — Frame arm envelope + visor X copies B1

**IC:** [implementation_contract_geometry_frame_arm_visor_x_b1.md](implementation_contract_geometry_frame_arm_visor_x_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-10
**Baseline:** package `0.3.8` · suite 2615 → **2622** (2615 + 7 new)

---

## Files changed

| File | Change |
|---|---|
| `src/jarvis/core/component_writers.py` | `_ENVELOPE_ALLOWED_LITERAL_KEYS` grew by one literal key: `frame_arm`. Docstring/`ValueError` copy updated to name it. No other writer logic changed — SET/CLEAR merge rules are identical for every allowed key. |
| `src/jarvis/core/declared_envelope_declare_assist.py` | New public `resolve_frame_arm_subject_noun(normalized, components)` — resolves the exact key `frame_arm`, or the bare nouns `"brazo"`/`"brazos"`/`"arm"`/`"arms"`, by delegating to the already-existing `resolve_declared_part_noun` (which already has arm-noun handling for the mount-declare grammar, itself gated on `"frame_arm" in components`) and only accepting a `"frame_arm"` result — no new regex table. Wired into `_resolve_subject` as a new tier (after kit, before the generic plate fallback). `frame_arm` added to `_NO_THICKNESS_FALLBACK_KEYS` — an arm envelope always requires the full three-number phrase, never borrowing its own `thickness_mm` (e.g. the Rooster's `arm_thickness_mm` seed) as a height fallback the way a plate can. |
| `src/jarvis/workspace/spatial_board.py` | `_solid_copies` gained a `frame_arm` branch: own geometry required, count cross-read from motors' `motor_count` (same `[2,16]` parser used by propellers) — but then, unlike propellers, an ADDITIONAL gate: the count must be exactly 4 **and** the frame's own `quad_x`+`wheelbase_mm` facts must hold (`_quad_x_wheelbase_mm`), or the whole thing omits. `_solid_copy_offsets_mm`'s allowed-key tuple widened to include `"frame_arm"` — no new station math, reuses `_quad_x_station_points` exactly as motors/propellers already do. |
| `tests/test_geometry_frame_arm_visor_x_b1.py` | **New.** P1–P6 exactly per IC §3 (P4 parametrized ×2). |

`ui/`, `library/`, `workspace/`, `pyproject.toml` — confirmed **untouched** by this cycle (`git status --short` shows no new changes beyond what already existed from earlier closed cycles this session; version still `0.3.8`).

---

## Documented choice (IC §3 P4: "document actual")

Unlike motors/propellers, a `frame_arm` copy count that isn't exactly 4-with-quad-X-stations gets **no `solidCopies` at all** — the arm renders as a single box, never a "row of N" clones. Rationale: motors/propellers are genuinely interchangeable identical parts, so a plain row is an honest (if visually plain) fallback for any N in `[2,16]`. An arm's entire reason for having N copies is standing at N specific quad-X stations — a "row of 3 arms" with no station geometry behind it would misrepresent the physical assembly far more than simply showing one arm card/box does. This mirrors the IC's own "prefer" clause in lock #3 ("prefer: same gate as station emit so N=3 stays one row solid, never fake 3-station X") — implemented as "stays a single box," the stricter and more honest of the two readings, since a plain "row" has no meaning for a part whose whole point is being at a station.

---

## Behavior changed

- `frame_arm` can now be declared via IDLE free text: `"declara el brazo 80 x 20 x 4 mm"` (or the exact key, or `"brazos"`/`"arm"`/`"arms"`) writes a real box (`source=declared`), preserving `thickness_mm`/`material`/every other property untouched. A two-number phrase is `INCOMPLETE` — arm never gets a thickness-based height fallback (unlike a plate).
- When `frame_arm` has a real box AND the sibling `motors` spec's own `motor_count` is exactly 4 AND the frame declares `configuration=="quad_x"` with a finite positive `wheelbase_mm`, the arm gets `solidCopies==4` and the exact same `solidCopyOffsetsMm` quad-X points motors/propellers already compute (verified byte-identical, P3) — the visor draws four arm boxes at the FR/FL/RL/RR stations, sharing the same silhouette.
- Any other motor count, or a missing/wrong `quad_x`/`wheelbase_mm`, leaves the arm as a single box with no `solidCopies` key at all (P4) — never a bare "row of 3."
- Still exactly **one** `frame_arm` `ComponentSpec`/BOM/card node — copies are visor-only presentation rows, the same guarantee already proven for motors/propellers.

---

## Tests added / executed

New: `tests/test_geometry_frame_arm_visor_x_b1.py` — 7/7 passing:
- P1: writer SET on `frame_arm` — three props `source=declared`, `thickness_mm`/`material` untouched.
- P2: parser `"declara el brazo 80 x 20 x 4 mm"` → `SET frame_arm`.
- P3: arm box + motors count 4 + `quad_x` + wheelbase → `solidCopies==4`, offsets length 4, identical to motors' own offsets, exactly one `frame_arm` node.
- P4 (×2): motor count 3 (with `quad_x`), and motor count 4 with `configuration=None` — both leave the arm a single box, no `solidCopies`/`solidCopyOffsetsMm` at all.
- P5: no `arm_length_mm`/`arm_width_mm` anywhere in `library/frames/_datos.json`; any existing `arm_thickness_mm` value is still just a plain number (unchanged).
- P6: battery/plate/kit envelope regressions all still `SET` correctly, and the plate's two-number thickness fallback remains plate-only (an arm two-number phrase still `INCOMPLETE`).

Full suite: `python -m pytest -q` → **2622 passed**, 0 failed.

---

## Live verification (read-only)

Ran the new parser + writer against the real `autonomía-de-5min` project's live `frame_arm` spec (never saved back): `"declara el brazo 80 x 20 x 4 mm"` resolves to `frame_arm`, and applying it yields `geometry == {shape: box, 80, 20, 4}`, `solidCopies == 4`, and `solidCopyOffsetsMm` byte-identical to the live `motors`/`propellers` stations (motor_count=4, `quad_x`+230 already declared there). `thickness_mm` stayed exactly `4.0`. No `workspace/` file was mutated.

---

## Non-goals honored

No arm length invented from `wheelbase_mm` 230 — every dimension in every test/verification came from the phrase itself. No four `frame_arm_*` BOM keys — still exactly one `ComponentSpec`, copies are presentation-only. No `prop_adapter`/caps/standoff touched. No sourced-dims work started. No cylinder, no new station formula (`_quad_x_station_points` reused verbatim, never forked). No Conversation Engine. No version bump.

---

## Remaining risks

- None identified specific to this change — the arm's copy gate reuses the exact same already-tested helpers (`_parse_solid_copies_count`, `_quad_x_wheelbase_mm`, `_quad_x_station_points`) with no new math, and the stricter "single box, never a fake row" choice is directly exercised by P4.
- The Engineer's live smoke (reloading the Board on `autonomía-de-5min` after declaring the arm's mm, confirming four arm boxes sit at the same X as motors, single `frame_arm` card) remains a separate, manual step per IC §5 — this report verifies the parse/write/project chain, not the rendered 3D result.
