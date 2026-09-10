# Implementation Report — Top LiPo plate (`frame_plate_2`) envelope noun B1

**IC:** [implementation_contract_geometry_frame_plate_2_lipo_envelope_b1.md](implementation_contract_geometry_frame_plate_2_lipo_envelope_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-09
**Baseline:** package `0.3.8` · suite 2593 → **2602** (2593 + 9 new)

---

## Files changed

| File | Change |
|---|---|
| `src/jarvis/core/declared_envelope_declare_assist.py` | Added `_TOP_LIPO_PLATE_RE` (matches `"placa lipo"`, `"placa top lipo"`, `"top lipo"`, `"top lipo plate"` after normalization) and `_resolve_top_lipo_plate` — resolves to the plate whose own `label` property normalizes to exactly `"top (lipo) plate"`, mirroring `_resolve_main_plate`. Refactored the shared single/ambiguous/none reduction (previously inlined under the main-plate check) into `_plates_by_normalized_label` (label lookup) and `_resolve_from_matches` (match-list → key / `AMBIGUOUS_TARGET` / `None`) so both nouns share one implementation instead of duplicating the same three-branch logic — `_resolve_main_plate` is now a one-line call into the shared helper, behavior byte-identical. `_resolve_subject` gained one new branch (`_TOP_LIPO_PLATE_RE` check, right after the main-plate check) using the same shared reducer. No writer change was needed — `set_component_declared_box_envelope`'s existing `is_frame_plate_key` predicate already covers `frame_plate_2`. |
| `tests/test_geometry_frame_plate_2_lipo_envelope_b1.py` | **New.** P1 (parametrized ×4) + P2–P6, exactly per IC §4. |

`orchestrator.py`, `library/`, `ui/`, `workspace/`, `pyproject.toml` — confirmed **untouched** by this cycle (`git status --short` shows no new diff on `orchestrator.py` from this cycle, `declared_envelope_declare_assist.py` is untracked so `git diff` shows nothing but the edits are present; version still `0.3.8`). The optional IDLE hint-copy touch (IC §1, "optionally improve the INCOMPLETE hint to mention `placa lipo`") was deliberately skipped — the existing generic hint (`"Indica sujeto (batería, placa, sensor o conector/harness ya declarado)..."`) already covers "placa" without enumerating every plate noun, and CLAUDE.md's discipline against opportunistic changes favored the smaller diff.

---

## Behavior changed

- Four new phrasings — `"declara la placa lipo 100 x 100 mm"`, `"declara la placa top lipo 100 x 100 mm"`, `"declara la top lipo 100 x 100 mm"`, `"declara la top lipo plate 100 x 100 mm"` — now resolve to `frame_plate_2` on the live Rooster project (label `"Top (LiPo) plate"`), the same two-number plate shape Main Plate already had (height stays `None` from the parser; the existing apply-path convention fills it from that plate's own `thickness_mm`, verified P2 against the live value `2`).
- Already-working paths (`"declara frame_plate_2 100 x 100 mm"` via exact key, `"declara la placa principal 100 x 100 mm"` via Main Plate) are unaffected — verified via regression (P3) and via the live probe cited in the IC's own parents section.
- Bare `"declara la placa 100 x 100 mm"` with both Main and Top LiPo declared still resolves `AMBIGUOUS_PLATE` with both candidates (P4) — the new noun doesn't short-circuit or interfere with the existing bare-noun ambiguity path.
- Once `frame_plate_2` has a declared box (via this noun or the exact key), the already-shipped `set_component_declared_box_pose` accepts it as an origin for the first time — verified directly (P5): `ValueError` before the SET, succeeds after. No pose-writer code was touched to achieve this, same mechanism as the Main Plate cycle.
- Assembly root is completely unaffected — `ASSEMBLY_ROOT_ID` in `scene3dLayout.ts` is still the literal string `"frame_plate"`; `frame_plate_2` was never eligible and this cycle made zero `ui/` edits to confirm that (verified by reading the file, not by adding a UI test, per the IC's stated preference to avoid touching `ui/`).

---

## Tests added / executed

New: `tests/test_geometry_frame_plate_2_lipo_envelope_b1.py` — 9/9 passing (P1 parametrized across all four required noun phrasings):
- P1 (×4): each of the four locked phrasings → `SET frame_plate_2`, `length_mm`/`width_mm` = 100/100, `height_mm=None`.
- P2: applying the parsed SET with the plate's own cited `thickness_mm` (2) yields `height_mm=2`, `thickness_mm` untouched, `frame.wheelbase_mm` untouched at 230, projector box `{100, 100, 2}`, exactly one `frame_plate_2` node.
- P3: `"placa principal"` still resolves `frame_plate` (regression).
- P4: bare `"placa"` with both plates declared → `AMBIGUOUS_PLATE`, both candidates present.
- P5: pose-origin unlock — `ValueError` before the plate SET, succeeds after (regression of the existing rule, now exercised for `frame_plate_2` specifically).
- P6: no Rooster (or any other frame) plate entry in `library/frames/_datos.json` carries `length_mm`/`width_mm` — confirms no catalog seed was added.

Full suite: `python -m pytest -q` → **2602 passed**, 0 failed.

---

## Live verification (read-only)

Ran the new parser + writer against the real `autonomía-de-5min` project's live `frame_plate_2` spec (never saved back): `"declara la placa lipo 100 x 100 mm"` resolves to `frame_plate_2`, and applying it with the live `thickness_mm=2` yields `geometry == {shape: box, 100, 100, 2}` while `frame.wheelbase_mm` stays exactly `230.0`. No `workspace/` file was written.

---

## Non-goals honored

No `length_mm`/`width_mm` seeded onto any Rooster plate row in `library/frames/_datos.json` (verified directly, P6). No `wheelbase_mm` stitched into a plate box. `ASSEMBLY_ROOT_ID`/`scene3dLayout.ts` untouched — `frame_plate_2` never becomes the Scene3D world origin. No auto-pose of battery — P5 only proves the writer *would* now accept a `respecto a frame_plate_2` pose if the Engineer types one. HD Cam / small-front / small-rear / Rear VTX plates got no new nouns this Buy. No sourced auto-fill (#4, not started). No Conversation Engine. No version bump.

---

## Remaining risks

- None identified specific to this change — the new noun resolver reuses the exact same shape (`_plates_by_normalized_label` + `_resolve_from_matches`) already proven for Main Plate, and the refactor that extracted the shared helper is behavior-preserving (verified by P3's Main Plate regression staying green).
- The Engineer's live smoke (typing real millimetres against `autonomía-de-5min`'s Top LiPo plate, optionally posing the battery `respecto a frame_plate_2`) remains a separate, manual step per IC §6 — not exercised by this report beyond the read-only verification above.
