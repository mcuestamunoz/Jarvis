# Implementation Report — Pose Continuity subject: plates B1

**IC:** [implementation_contract_continuity_pose_plate_subject_b1.md](implementation_contract_continuity_pose_plate_subject_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-09
**Baseline:** package `0.3.8` · suite 2602 → **2608** (2602 + 6 new)

---

## Files changed

| File | Change |
|---|---|
| `src/jarvis/core/declared_envelope_declare_assist.py` | Extracted a new **public** `resolve_plate_subject_noun(normalized, components)` from the body of the private `_resolve_subject` — same logic (Main Plate → Top LiPo plate → generic `resolve_declared_part_noun` filtered to `is_frame_plate_key`), zero behavior change (`_resolve_subject` now just calls it after the battery/sensors/kit checks). Verified byte-identical via the full pre-existing envelope test suites (29/29 still green, unchanged). |
| `src/jarvis/core/declared_box_pose_declare_assist.py` | New `_resolve_pose_subject(segment, components)`: tries the electronics table (`resolve_component_subject_noun`) first, unchanged precedence; only when that yields nothing does it try `resolve_plate_subject_noun` — an ambiguous plate match (2+ candidates) is treated as "no subject" (no new result kind, since no test in this IC's own list needed one). Wired into both the `CLEAR` and `SET` subject-resolution call sites. **Deviation from the IC** (documented below): also widened **origin** resolution to retry with `resolve_plate_subject_noun` whenever the existing `resolve_declared_part_noun` call returns ambiguous or `None` — required to make `"respecto a la placa principal"` resolve to Main Plate specifically instead of a spurious "which plate" ambiguity (see below). |
| `tests/test_continuity_pose_plate_subject_b1.py` | **New.** P1–P6 exactly per IC §3. |

`ui/`, `library/`, `workspace/`, `pyproject.toml`, the writer (`set_component_declared_box_pose`) — confirmed **untouched** by this cycle. Version still `0.3.8`.

---

## Deviation from the IC (origin resolution)

IC lock #4 states origin resolution is "Unchanged: `resolve_declared_part_noun` after `respecto`." Testing against the IC's own required P2 phrase and product-sentence example — both use `"respecto a la placa principal"` — showed `resolve_declared_part_noun` alone cannot resolve that phrase to Main Plate specifically: it has no "placa principal" canonical-noun awareness (that logic only ever existed in the envelope grammar's `_MAIN_PLATE_RE`), so it falls through to the generic bare-`"placa"` fallback and returns `AMBIGUOUS_TARGET` listing every declared plate — confirmed empirically before writing any test, per this session's established discipline of verifying a contract's own claims against real code rather than trusting them.

Since P2 is an explicit, required test in the IC's own §3 table and the product sentence itself relies on this exact phrasing, I extended origin resolution with a narrow, reuse-only fallback: when `resolve_declared_part_noun` returns ambiguous or `None` for the origin segment, retry with the SAME `resolve_plate_subject_noun` helper the subject side already uses (no new noun table, no new regex — literally the identical function). A genuinely ambiguous bare `"placa"` origin (no "principal"/"lipo" keyword, 2+ plates) still correctly surfaces `AMBIGUOUS_ORIGIN` — verified directly (not part of the six required tests, but checked interactively before finalizing). `"respecto a frame_plate"` (exact key, P1) and `"respecto al fc"` (component alias, P4) are unaffected, since `resolve_declared_part_noun` already resolves those directly (the fallback only fires on ambiguous/`None`).

This is the smallest change that satisfies the IC's own explicit test list and product sentence; no schema field, no writer change, no new mechanism — only a widened retry of an already-existing, already-shared resolver.

---

## Behavior changed

- A frame plate can now be the **subject** of a pose declare/clear phrase — `"declara la placa lipo a 0 mm en z respecto a frame_plate"` and `"quita la pose de la placa lipo"` both resolve `frame_plate_2` as `component_key`, using the exact same noun set (`"placa lipo"`/`"top lipo"`, `"placa principal"`/`"main plate"`, exact key, label substring, bare `"placa"`) the envelope grammar already ships — no second noun table.
- The origin side of a pose phrase now also resolves `"la placa principal"`/`"la placa lipo"` to that one specific plate instead of surfacing a spurious ambiguity when 2+ plates are declared (the Deviation above).
- Envelope and pose grammars remain mutually exclusive exactly as before: a phrase without `"respecto"` is still envelope-shaped only (`"declara la placa lipo 100 x 100 mm"` → envelope `SET`, pose parser `NONE`); electronics pose phrases (`"declara el esc a 5 mm en x respecto al fc"`) are completely unaffected — verified via regression (P4) and the full pre-existing 18-test pose suite staying green.
- The writer's honesty rule is untouched: posing a plate whose origin is still shapeless (no envelope declared) still raises `ValueError`; it succeeds once that origin has a real box — the exact same rule already proven for electronics components, now also exercised for a plate-vs-plate pose (P6).

---

## Tests added / executed

New: `tests/test_continuity_pose_plate_subject_b1.py` — 6/6 passing:
- P1: `"declara la placa lipo a 0 mm en z respecto a frame_plate"` → `SET frame_plate_2`, origin `frame_plate`, `z=0`.
- P2: `"declara frame_plate_2 a 0 mm en x y 0 mm en y y 15 mm en z respecto a la placa principal"` → `SET`, origin resolves specifically to `frame_plate` (not ambiguous).
- P3: the same envelope phrase without `"respecto"` stays envelope-shaped (`SET` on the envelope parser, `NONE` on the pose parser).
- P4: `"declara el esc a 5 mm en x respecto al fc"` still `SET esc` (electronics regression).
- P5: `"quita la pose de la placa lipo"` → `CLEAR frame_plate_2`.
- P6: writer still raises on a shapeless plate origin, succeeds once both plates have a declared box (regression of the existing rule, now also proven for a plate-vs-plate pose).

Full pre-existing pose suite (`tests/test_continuity_declared_box_pose_b1.py`) — **18/18 still green**, unchanged. Full pre-existing envelope suites (battery/plate, sensors/kit, Top LiPo noun — 29 tests total) — **all still green**, confirming the `resolve_plate_subject_noun` extraction was behavior-preserving.

Full suite: `python -m pytest -q` → **2608 passed**, 0 failed.

---

## Live verification (read-only)

Read the real `autonomía-de-5min` project (never saved back): both `frame_plate` and `frame_plate_2` already carry declared boxes and `battery` is already posed against `frame_plate_2` (from the Engineer's own prior live smoke, cited in this IC's own parents). Parsed `"declara la placa lipo a 20 mm en z respecto a la placa principal"` → resolved to `SET frame_plate_2` / origin `frame_plate` / `z=20`; applying it via the writer and re-projecting shows `frame_plate_2.declaredBoxPose == {originKey: "frame_plate", zMm: 20.0}`. No `workspace/` file was mutated by this verification.

---

## Non-goals honored

No new architectural subsystem — `resolve_plate_subject_noun` is a straight extraction of existing logic, reused (not duplicated) by both grammars. No writer change — `set_component_declared_box_pose`'s box-origin honesty rule is untouched. No `ASSEMBLY_ROOT_ID`/`scene3dLayout.ts` change — `frame_plate_2` still never becomes the Scene3D world origin (unaffected by this cycle, which made zero `ui/` edits). No auto-pose — every SET in this report comes from an explicit, Engineer-typed phrase. No sourced-dims work (#4, not started). No Conversation Engine. No version bump.

---

## Remaining risks

- The origin-resolution widening (Deviation above) is a real, if narrow, expansion beyond the IC's literal "Unchanged" instruction for that one call site. It was necessary to satisfy the IC's own explicit P2 test and product sentence, is scoped to reusing an already-shared helper, and is covered by both a positive test (P2) and a manual check that genuine ambiguity still surfaces correctly — but it is worth Cursor's explicit attention during review given the literal lock text.
- An ambiguous plate **subject** (bare `"placa"` naming 2+ plates in a pose phrase) has no dedicated result kind — it degrades to `INCOMPLETE`/`NONE` rather than an `AMBIGUOUS_SUBJECT` the Engineer could disambiguate. Not exercised by any required test; flagged as a possible follow-up if that phrasing turns out to matter in practice.
- The Engineer's live smoke (posing Top LiPo against Main and confirming the racimo joins via multi-hop, Main Plate still the assembly root) remains a separate, manual step per IC §5 — this report verifies the parse/write/project chain, not the rendered 3D result.
