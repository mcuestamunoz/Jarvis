# Implementation Report — Declared sensors + kit envelope B1

**IC:** [implementation_contract_geometry_declared_sensors_kit_envelope_b1.md](implementation_contract_geometry_declared_sensors_kit_envelope_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-09
**Baseline:** package `0.3.8` · suite 2583 → **2593** (2583 + 10 new)

---

## Files changed

| File | Change |
|---|---|
| `src/jarvis/core/component_writers.py` | `set_component_declared_box_envelope`'s allowlist widened: added a new `_ENVELOPE_ALLOWED_LITERAL_KEYS = frozenset({"battery", "sensors", "power_connector", "signal_harness"})` (replacing the old bare `component_key != "battery"` check), still combined with the unchanged `is_frame_plate_key` predicate for plates. Docstring and `ValueError` copy updated to name all four literal keys. SET/CLEAR merge logic itself is completely unchanged — still exactly the three axis keys, still preserving every other property (kit pin/pitch fields, `catalog_ref`, `mounted_on`, etc.). |
| `src/jarvis/core/declared_envelope_declare_assist.py` | `_resolve_subject` now also accepts `"sensors"` from the existing `resolve_component_subject_noun` table (same ungated resolution as `"battery"` — presence is checked downstream by the orchestrator). New `_resolve_kit_key`/`_KIT_KEY_PATTERNS` resolve `power_connector` (conector/xt60/power_connector) and `signal_harness` (harness/"cable de señal"/signal_harness) nouns — but **only** when that exact key already exists in `components`; a matching noun with no such key falls through as "no subject" (→ `INCOMPLETE` for a SET-shaped phrase, `NONE` for CLEAR — the same fallback the existing zero-plates case already produces, no new branch needed). New `_NO_THICKNESS_FALLBACK_KEYS` set (`battery`/`sensors`/`power_connector`/`signal_harness`) replaces the old `subject == "battery"` check — all four now require the full three-number phrase (no thickness fallback, which stays plate-only). |
| `src/jarvis/core/orchestrator.py` | One-line copy touch only: the `INCOMPLETE` hint message in `_try_handle_declared_box_envelope` now also mentions sensors/conector/harness examples. No new branch, no new dispatch — the existing IDLE bridge already routes SET/CLEAR/height-fallback correctly for the new keys once the parser/writer accept them (verified directly: sensors/kit SET phrases always carry a resolved `height_mm`, so the orchestrator's thickness-fallback branch — plate-only in practice — is never triggered for them). |
| `tests/test_geometry_declared_sensors_kit_envelope_b1.py` | **New.** P1–P10 exactly per IC §4. |

`library/`, `workspace/`, `ui/`, `pyproject.toml` — confirmed **untouched** by this cycle (`git status --short` shows no new changes beyond what already existed from earlier closed cycles; version still `0.3.8`).

---

## Behavior changed

- Two new IDLE-declarable box families: `sensors` (e.g. `"declara el gps 40 x 40 x 12 mm"`) and the two kit keys `power_connector`/`signal_harness` (e.g. `"declara el conector 30 x 20 x 10 mm"`, `"declara el harness 30 x 10 x 5 mm"`, or the Spanish `"cable de señal"`/literal underscored key names). All three require the full three-number phrase — no thickness fallback exists for these families (that stays exclusive to `frame_plate*`).
- A kit noun that doesn't match a currently-declared kit key resolves to "no subject" rather than inventing a component — a phrase like `"declara el conector..."` on a project with no `power_connector` component becomes `INCOMPLETE`, never a phantom write.
- `sensors` reuses the exact same subject-noun table `battery` already used (ungated by presence — the orchestrator's existing "aún no declarado" error covers the missing-key case, same as it always has for battery).
- The writer's `ValueError` scope grew by exactly these two literal keys; `frame` root, arms, cage, standoff, motors, ESC, FC, and propellers remain rejected exactly as before (verified, P3).
- No physics/catalog impact: kit identity fields (`pin_count`, `pitch_mm`, `wire_gauge_awg`, `catalog_ref`) and sensor identity (`gps_model`, `mounted_on`) are completely untouched by a SET/CLEAR on the box triple (verified, P1/P2/P4).

---

## Tests added / executed

New: `tests/test_geometry_declared_sensors_kit_envelope_b1.py` — 10/10 passing:
- P1: writer SET on `sensors` — three props `source=declared`, `gps_model`/`mounted_on` untouched.
- P2: writer SET on `power_connector` and `signal_harness` — three props each, kit identity (`name`, `pin_count`, `pitch_mm`, `catalog_ref`) untouched.
- P3: writer still `ValueError` on `esc`/`motors`/`frame`.
- P4: writer CLEAR on `sensors` pops only the three box keys, `gps_model` survives.
- P5: parser `"declara el gps 40 x 40 x 12 mm"` → `SET sensors`.
- P6: parser resolves `power_connector` via "conector"/"xt60" and `signal_harness` via "harness"/"cable de señal", each only when that key is present; a kit noun with no matching declared key → `INCOMPLETE`.
- P7: pair-only phrase on `sensors` → `INCOMPLETE`.
- P8: a `"respecto"` phrase → parser `NONE`.
- P9: battery and `"placa principal"` phrases still resolve exactly as before this Buy (`SET battery`/`SET frame_plate`, plate's `height_mm` still `None` pre-thickness-fill).
- P10: `library/kit_hardware/_datos.json`'s two rows (Pololu XT60, Pi Hut JST-SH) still carry no `length_mm`/`width_mm`/`height_mm` — `cable_length_options_mm` stays a distinct, un-projected field; no `library/sensor(es)` catalog directory exists at all, so there is nothing there to seed.

Full suite: `python -m pytest -q` → **2593 passed**, 0 failed.

---

## Live verification (read-only)

Ran the new parser + writer against the real `autonomía-de-5min` project's live `sensors` spec (never saved back): `"declara el gps 40 x 40 x 12 mm"` resolves to `sensors`, and applying it yields `geometry == {shape: box, 40, 40, 12}` while `gps_model` stays exactly `"ublox_m9n"`. No `workspace/` file was mutated.

---

## Non-goals honored

No L×W×H seeded onto any GPS/Pololu/Pi Hut library row. `cable_length_options_mm` never becomes `length_mm`. No `set_battery_component` or kit catalog-bind writer called on this path. No auto-pose. No `scene3dLayout`/visor change. `frame_plate_2` Buy (#3) and sourced auto-fill (#4) not started. No Conversation Engine. No version bump.

---

## Remaining risks

- None identified specific to this change — the writer's allowlist and the parser's subject filter are both exercised directly by tests (P3, P6's missing-key case).
- The Engineer's live smoke (typing real GPS/connector millimetres against `autonomía-de-5min`, confirming the box appears in Board/3D and pin/pitch fields stay untouched) remains a separate, manual step per IC §6 — not exercised by this report beyond the read-only verification above.
