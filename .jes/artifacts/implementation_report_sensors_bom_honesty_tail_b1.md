# Implementation Report — Sensors BOM Honesty Tail (generic sensor ≠ GNSS/navigation) — copy only (B1)

**IC:** [implementation_contract_sensors_bom_honesty_tail_b1.md](implementation_contract_sensors_bom_honesty_tail_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-07
**Baseline:** package `0.3.8` · suite 2332 · Control parity CLOSED

---

## Files changed

- `src/jarvis/core/project_closure.py`:
  - New `_bom_sensors_declarative_tail(entry, project_state=None)` next to `_bom_completeness_tail`. For any declarative entry with `key != "sensors"`, returns the plain `"declarativo"` string unchanged. For `key == "sensors"`, reads `design_properties.components["sensors"].properties` (same duck-typed, `getattr`-based style as every other helper in this file) and returns:
    - `"declarativo — GNSS declarado, no vuelo demostrado"` when a `gps_model` property is present (any value — Here3, a bare M9N, or even `generic_gps` all count as "a GNSS fact was declared," per the IC's own locked table, §3.1).
    - `"declarativo — no implica GNSS ni navegación"` otherwise — covering a bare `sensor_type` (barometer/IMU/compass), an empty/unknown sensors component, a missing `sensors` key, or `project_state=None` altogether. This is the single safe default the IC calls for; no separate "unavailable" branch was needed since the same `getattr(..., None) or {}` chain naturally degrades to it in every one of those cases.
  - `format_bom_lines`'s `declarative` bucket loop now calls `_bom_sensors_declarative_tail(entry, project_state)` instead of the hardcoded `"(declarativo)"` string. Every other bucket (`defined`/`incomplete`/`missing`) and every other declarative key's rendering is byte-identical to before this IC.
- `tests/test_project_closure_v1.py`:
  - Updated `test_bom_sensors_declarative_unaffected_by_control_suffix` (per the IC's own instruction) — its fixture already declares `gps_model="ublox_m9n"`, so once `format_bom_lines` is called *with* `project_state` (it previously wasn't), the line now correctly carries the GNSS tail instead of the old plain `"(declarativo)"` string. Updated the assertion accordingly rather than leaving a now-incorrect expectation in place.
  - `test_bom_sensors_declarative_gnss_here3_tail` — a Here3 (`gps_model`) declaration gets the GNSS tail, never the non-GNSS phrasing.
  - `test_bom_sensors_declarative_non_gnss_tail` — a bare `sensor_type="barometer"` declaration gets the non-GNSS tail, never `"GNSS declarado"` — the exact conflation the investigation found (`_sensor_completeness` grading both identically) is now visibly distinguished in the BOM copy.
  - `test_bom_sensors_declarative_tail_safe_default_without_project_state` — even a Here3-declaring project falls back to the **safer** non-GNSS phrasing when `format_bom_lines` is called without `project_state`, per the IC's explicit safety rule.
  - `test_bom_other_declarative_keys_keep_plain_tail` — a direct unit check that any non-`sensors` key (`battery` used as the example) still returns the plain `"declarativo"` string from the new helper.

## Behavior changed

- The BOM's `declarative` bucket line for `sensors` now reads one of two honest tails instead of a flat `"(declarativo)"`, depending on whether a `gps_model` was declared — making the exact gap the investigation found (a barometer and a Here3 grading identically everywhere else in the system) visible in the one place a reader actually looks at what was declared.
- **No other line, bucket, or component key changed.** `flight_controller`'s `"identidad, sin dato físico"` tail (`_bom_completeness_tail`, untouched), `frame`'s class-compatibility tail (untouched), every `defined`/`incomplete`/`missing` line, and every other `declarative` key (e.g. `battery` if it were ever declarative) are byte-identical to before this IC — confirmed both by reading the unmodified code paths and by the new `test_bom_other_declarative_keys_keep_plain_tail` regression.
- **No change to any gate, verdict, or completeness function.** `_control_evidence`, `_derive_subsystem_verdict`, `_derive_overall`, `_sensor_completeness`, `classify_component`, `_MEASURABLE`, and the Control PASS `*` CLI footnote string are all untouched — confirmed via `git diff --stat` showing zero lines changed in `engineering_readiness.py`, `aerial.py` (this session), or `adapters/cli/main.py`. Control PASS remains exactly as sensors-blind as the investigation found it, and this IC does not change that — it only changes what the BOM's own display says about what was declared.
- No call site needed a `project_state` argument added or refactored — every production caller of `format_bom_lines` that renders the `sensors` line already had `project_state` available and passed it (confirmed by inspection; no call-graph changes were required, matching the IC's "prefer, do not refactor beyond that" instruction — there was nothing to change).

## Tests

Executed: `python -m pytest -q` → **2336 passed**, 0 failed (baseline 2332 + 4 new + 1 updated in place, not counted as new since it already existed). Ran `tests/test_project_closure_v1.py` alone first (22 passed — 17 pre-existing/1 updated + 4 new) before the full run. The one pre-existing test whose assertion needed updating was updated per the IC's own explicit instruction (§4.4) — not weakened: it now asserts the more specific, more honest GNSS-tail text instead of the generic `"(declarativo)"` substring it previously checked for, and the update was necessary only because the test itself hadn't been passing `project_state` into `format_bom_lines`, not because its fixture or intent changed.

## Non-goals honored

No edits to `_control_evidence`, `_derive_subsystem_verdict`, `_derive_overall`, gap types, `_sensor_completeness`, `classify_component`, `_MEASURABLE`, architecture progress counters, the Control PASS `*` footnote string, or any catalog/schema/capability-table code (confirmed via `git diff --stat`: only `project_closure.py` and its test file changed). No sensor/FC catalog, bind, or Continuity wizard added. No Here3 geometry, indoor-sensing vocabulary, or Autonomous PASS concept introduced. No version bump.

## Remaining risk / notes for review

- The GNSS tail fires on **any** `gps_model` presence, including the bare `generic_gps` bucket (a plain "gps" keyword with no specific model) — per the IC's own locked table (§3.1: "gps_model property present," no further qualification). This means a very low-confidence, unspecific "gps" declaration gets the same GNSS-declared phrasing as a specific "Here3" one. This is exactly what the IC locked (not a decision made here), and the investigation's own §D already noted the `generic_gps` bucket exists precisely to *not* claim Here3-tier precision — this IC's tail correctly says "GNSS declarado, no vuelo demostrado" either way, which remains true for both cases; it does not claim precision, only that some GNSS fact was declared. Flagging only so a future reader isn't surprised that "gps" and "Here3" produce the same tail text.
