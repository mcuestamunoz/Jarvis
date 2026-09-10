# Implementation Report — Pose Continuity subject: kit keys B1

**IC:** [implementation_contract_continuity_pose_kit_subject_b1.md](implementation_contract_continuity_pose_kit_subject_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-10
**Baseline:** package `0.3.8` · suite 2608 → **2615** (2608 + 7 new)

---

## Files changed

| File | Change |
|---|---|
| `src/jarvis/core/declared_envelope_declare_assist.py` | Renamed the private `_resolve_kit_key` to a new **public** `resolve_kit_subject_noun(normalized, components)` — same logic, same presence-gated behavior (a matching noun with no declared key resolves to `None`), only the name and visibility changed, plus an expanded docstring. `_resolve_subject`'s one call site updated to the new name. Zero behavior change — verified via the full pre-existing envelope test suites (29/29 still green). |
| `src/jarvis/core/declared_box_pose_declare_assist.py` | `_resolve_pose_subject` gained a third tier, fixed precedence per lock #2: (1) electronics (`resolve_component_subject_noun`, unchanged), (2) plate (`resolve_plate_subject_noun`, unchanged from the prior cycle), (3) **new** — kit (`resolve_kit_subject_noun`) tried only when neither of the first two resolved anything. Wired automatically into both the `CLEAR` and `SET` call sites, since both already route through `_resolve_pose_subject`. Module docstring updated to describe all three tiers. Origin resolution (`resolve_declared_part_noun` + the plate-noun fallback) is completely untouched — kit keys are never a pose origin in this Buy, matching lock #4 ("Unchanged"). |
| `tests/test_continuity_pose_kit_subject_b1.py` | **New.** P1–P6 exactly per IC §3 (P3 parametrized ×2). |

`component_writers.py`, `orchestrator.py`, `ui/`, `library/`, `workspace/`, `pyproject.toml` — confirmed **untouched** by this cycle (`git status --short` shows no new diff on any of them from this cycle; version still `0.3.8`).

---

## Behavior changed

- A kit component (`power_connector`/`signal_harness`) can now be the **subject** of a pose declare/clear phrase — `"declara el conector a 0 mm en x y 0 mm en y y 5 mm en z respecto a frame_plate"` and `"declara el harness ..."` both resolve correctly, using the exact same noun set (conector/xt60/power_connector, harness/"cable de señal"/signal_harness) the envelope grammar already ships.
- Resolution is presence-gated exactly like envelope: a kit noun with no matching declared component resolves to "no subject" (`INCOMPLETE` for a SET-shaped phrase), never inventing a component (P4).
- Fixed precedence (electronics → plate → kit) means no existing behavior can be shadowed: an electronics noun still wins outright, a plate noun still wins over a kit noun (they're lexically disjoint anyway, so this never actually collides in practice, but the order is explicit and tested).
- Envelope and pose grammars remain mutually exclusive exactly as before: a kit envelope phrase without `"respecto"` is still envelope-shaped only (P6).
- `quita la pose del conector` clears `power_connector`'s pose the same way `quita la pose del esc` already cleared ESC's.

---

## Tests added / executed

New: `tests/test_continuity_pose_kit_subject_b1.py` — 7/7 passing:
- P1: conector phrase → `SET power_connector`, origin `frame_plate`, all three axes.
- P2: harness phrase → `SET signal_harness`, origin `frame_plate`, all three axes.
- P3 (×2): `"xt60"` and `"cable de señal"` alternate nouns resolve `power_connector`/`signal_harness` respectively.
- P4: a kit noun with no matching declared component → `INCOMPLETE`, never invented.
- P5: electronics (`esc`/`fc`) and plate (`frame_plate_2`) pose regressions still `SET` exactly as before.
- P6: the kit envelope phrase (no `"respecto"`) stays envelope-`SET`; the pose parser returns `NONE` for the identical text.

Full pre-existing regression suites — `test_continuity_declared_box_pose_b1.py` (18), `test_continuity_pose_plate_subject_b1.py` (6), and all three envelope suites (29) — **all still green**, confirming the `resolve_kit_subject_noun` rename/extraction was behavior-preserving.

Full suite: `python -m pytest -q` → **2615 passed**, 0 failed.

---

## Live verification (read-only)

Ran the extended pose parser against the real `autonomía-de-5min` project's live `power_connector`/`signal_harness` specs (never saved back): both `"declara el conector a 0 mm en x y 0 mm en y y 5 mm en z respecto a frame_plate"` and `"declara el harness ..."` resolve to `SET power_connector`/`SET signal_harness` respectively, origin `frame_plate`, all three axes correctly parsed. No `workspace/` file was mutated.

---

## Non-goals honored

No mm invented anywhere — every axis value in every test/verification came from the phrase itself. No auto-pose — the writer is never called by this parser; every SET requires an explicit Engineer-typed phrase. No assembly-root change — `ASSEMBLY_ROOT_ID`/`scene3dLayout.ts` untouched (no `ui/` edit made this cycle). No sourced-dims work started. No writer change — `set_component_declared_box_pose`'s existing box-origin honesty rule is exercised as-is, unmodified. No Conversation Engine. No version bump.

---

## Remaining risks

- None identified specific to this change — the third tier reuses an already-shared, already-tested helper (`resolve_kit_subject_noun`, previously `_resolve_kit_key`), and the fixed precedence is directly exercised by P5's regression checks.
- As already noted in the parent plates cycle's report: an ambiguous plate/kit subject reference has no dedicated result kind in this grammar (degrades to `INCOMPLETE`/`NONE`) — unchanged carry-over, not introduced or worsened by this cycle.
- The Engineer's live smoke (posing the connector/harness against `frame_plate` and confirming they land near the plate center in the visor) remains a separate, manual step per IC §5 — this report verifies the parse/resolve chain, not the rendered 3D result.
