# Implementation Report — Loose structure/kit envelopes + pose subjects B1

**IC:** [implementation_contract_geometry_loose_structure_envelope_pose_b1.md](implementation_contract_geometry_loose_structure_envelope_pose_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-10
**Baseline:** package `0.3.8` · suite 2622 → **2640** (2622 + 18 new)

---

## Files changed

| File | Change |
|---|---|
| `src/jarvis/core/component_writers.py` | `_ENVELOPE_ALLOWED_LITERAL_KEYS` grew by four literal keys: `prop_adapter`, `frame_standoff`, `frame_cage`, `frame_caps`. Docstring/`ValueError` copy updated to name all nine literal keys. No other writer logic changed. |
| `src/jarvis/core/declared_envelope_declare_assist.py` | New `_LOOSE_KEY_PATTERNS` (presence-gated, same shape as `_KIT_KEY_PATTERNS`) covering the two keys with no existing noun anywhere in the codebase: `prop_adapter` (adaptador/adapter/collet) and `frame_caps` (caps/tapas). New public `resolve_loose_structure_subject_noun(normalized, components)` — tries that pattern table first, then falls back to `resolve_declared_part_noun` filtered to `frame_cage`/`frame_standoff` (which that function's mount-declare grammar already resolves via its own jaula/cage, standoff/separador(es) nouns, itself presence-gated). Wired into `_resolve_subject` as a new tier (after `frame_arm`, before the generic plate fallback). All four keys added to `_NO_THICKNESS_FALLBACK_KEYS` — always require the full three-number phrase. |
| `src/jarvis/core/declared_box_pose_declare_assist.py` | `_resolve_pose_subject` gained a new tier — loose structure (`resolve_loose_structure_subject_noun`) — inserted after plate, before kit. No origin-side change (lock #6: "Origin rules unchanged"). |
| `tests/test_geometry_loose_structure_envelope_pose_b1.py` | **New.** P1–P7 exactly per IC §3 (several parametrized). |

`spatial_board.py`, `ui/`, `library/`, `workspace/`, `pyproject.toml` — confirmed **untouched** by this cycle (`git status --short` shows no new changes on any of them; version still `0.3.8`). No plate grammar code was touched — plates already had their own allowlist entry via `is_frame_plate_key` before this IC.

---

## Behavior changed

- Four previously-mute structure/kit holes can now be declared/cleared/posed via IDLE free text, all presence-gated (a matching noun with no such key declared is treated as "no subject," never invented — P3):
  - `"declara el adaptador 12 x 12 x 8 mm"` / `"...el collet..."` → `SET prop_adapter`.
  - `"declara el standoff 5 x 5 x 25 mm"` → `SET frame_standoff` (reuses the mount-declare grammar's existing standoff noun).
  - `"declara la jaula 40 x 40 x 30 mm"` → `SET frame_cage` (reuses the existing cage noun).
  - `"declara los caps 10 x 10 x 2 mm"` → `SET frame_caps`.
- Every one of the four always requires the full three-number phrase — a pair-only phrase is `INCOMPLETE`, never falling back to a stray `thickness_mm` (P5), same discipline as battery/sensors/kit/frame_arm.
- The identical noun set now also resolves as a **pose subject** — `"declara el adaptador a 0 mm en x y 0 mm en y y 5 mm en z respecto a frame_plate"` correctly sets `prop_adapter`'s pose against a box origin (P4). The `respecto`/envelope collision is unchanged: the same phrase without `"respecto"` stays envelope-shaped only, and CLEAR (`"quita la pose del adaptador"`) resolves the same subject.
- `frame_plate*` ordinals (HD Cam, Rear VTX, small front/rear) are completely untouched — they were already allowlisted via `is_frame_plate_key` before this IC, exactly as the parent lock states; the Engineer can already declare those with the existing plate grammar, no code change needed.
- Still exactly one `ComponentSpec` per key — never N siblings for standoffs or any other family (nothing in this cycle creates or duplicates components).

---

## Tests added / executed

New: `tests/test_geometry_loose_structure_envelope_pose_b1.py` — 18/18 passing:
- P1 (×4): writer SET on each of the four keys — three props `source=declared`.
- P2 (×5): parser nouns (adaptador, collet, standoff, jaula, caps) each resolve the expected key with the expected dims.
- P3 (×4): each noun with the key missing from `components` → `INCOMPLETE`, never invented.
- P4: pose subject resolves all four keys against a box origin; envelope/pose collision unchanged; CLEAR resolves the same subject.
- P5 (×2): pair-only phrase on adapter/standoff → `INCOMPLETE`, no thickness fallback.
- P6: battery/plate/kit/arm envelope regressions all still `SET` correctly, plate's thickness fallback stays plate-only.
- P7: no new `*_length_mm`/`*_width_mm` seed anywhere in `library/frames/_datos.json` for any of these families.

Full pre-existing regression suites — pose (18+6+7=31 across the three pose test files) and envelope (battery/plate 10, sensors/kit 10, Top LiPo 9, frame_arm 7 = 36) — **all still green**, confirming every extraction/wiring change was behavior-preserving.

Full suite: `python -m pytest -q` → **2640 passed**, 0 failed.

---

## Live verification (read-only)

Ran the extended envelope + pose parsers against the real `autonomía-de-5min` project's live `prop_adapter`/`frame_standoff`/`frame_cage` specs (never saved back): all three envelope phrases resolve correctly, applying the adapter one yields `geometry == {shape: box, 12, 12, 8}`, and `"declara el adaptador a 0 mm en x y 0 mm en y y 5 mm en z respecto a frame_plate"` resolves to `SET prop_adapter` with origin `frame_plate`. No `workspace/` file was mutated.

---

## Non-goals honored

No mm invented from Rooster marketing copy — every dimension in every test/verification came from the phrase itself. No library seed added to any frame/plate/kit SKU (verified directly, P7). No plate L×W auto-fill — plate grammar untouched. No visor copies/station math for any of these four keys (`spatial_board.py` untouched this cycle). No Conversation Engine. No sourced-dims work (#4, not started). No version bump.

---

## Remaining risks

- None identified specific to this change — every new tier reuses an already-shared, already-tested pattern (the presence-gated pattern table shape from kit, the "delegate to `resolve_declared_part_noun` and filter" shape from arm), and the fixed precedence is directly exercised by the regression tests (P6).
- As already noted in prior cycles' reports: an ambiguous plate/kit/loose-structure subject reference has no dedicated result kind in the pose grammar (degrades to `INCOMPLETE`/`NONE`) — unchanged carry-over, not introduced or worsened here.
- The Engineer's live smoke (declaring real mm for adapter/standoff/cage, posing at least one onto a plate/motor box origin, and separately declaring the mute Rooster plates' L×W with the existing plate grammar) remains a separate, manual step per IC §5 — this report verifies the parse/write/project chain, not the rendered 3D result.
