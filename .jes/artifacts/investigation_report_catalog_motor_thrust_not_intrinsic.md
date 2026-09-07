# Investigation Report — Motor Thrust Is Not an Intrinsic Property

**IC:** [investigation_contract_catalog_motor_thrust_not_intrinsic.md](investigation_contract_catalog_motor_thrust_not_intrinsic.md)
**Investigator:** Claude Code
**Date:** 2026-09-07
**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · Engineer ★ Buy B1 → IC READY  
**Review:** [investigation_review_catalog_motor_thrust_not_intrinsic.md](investigation_review_catalog_motor_thrust_not_intrinsic.md)  
**IC:** [implementation_contract_catalog_motor_thrust_not_intrinsic_b1.md](implementation_contract_catalog_motor_thrust_not_intrinsic_b1.md)

## A. Executive answer

The Engineer's locked claim is confirmed, and the investigation surfaced something worse than a display/honesty smell: **the correctly-conditioned thrust computation the codebase already knows how to make is silently discarded by a separate, unaware resolver, on every recalculation, by design precedent (FN-007).**

Two independent consumers read a catalog motor's `thrust_n`:

1. **`resolve_operating_point`** (`library.py`) — conditioned. Given `(motor_sku, propeller_sku, voltage_v)` it returns a typed, honest resolution (`exact_operating_point` / `fallback_operating_point` / `legacy_estimate`), called once from `component_writers.set_motor_component`, written to `current_parameters["per_motor_max_thrust_n"]` + a full `propulsion_resolution` audit trail.
2. **`resolve_propulsion_parameters`** (`component_resolver.py`) — unconditioned. It reads `ComponentSpec.properties["thrust_n"]` directly (the bare catalog peak `bind_motor_from_catalog` always projects with `source="declared"`), with zero knowledge of propeller, voltage, or `resolve_operating_point`'s existence. It is called **unconditionally on every physical recalculation** (`iterate.py:197-200`, `param_definition_session.py:963-965`) and its result **unconditionally overwrites** whatever is already in `current_parameters["per_motor_max_thrust_n"]` (`PhysicalOverride.apply_to`, `component_resolver.py:62-63`).

Empirical proof (live call, this session, no fixture needed):

```
resolve_operating_point('emax_rs2205s_2300', propeller_sku='gemfan_5045_hbn', voltage_v=16.0)
  -> exact_operating_point, thrust_n=13.4841  (real, measured, condition-specific)

resolve_propulsion_parameters({'motors': <same spec>})
  -> per_motor_max_thrust_n=10.042            (bare catalog peak, unconditioned)

PhysicalOverride.apply_to({'per_motor_max_thrust_n': 13.4841, ...})
  -> {'per_motor_max_thrust_n': 10.042, ...}  # the correct value is gone
```

This is not hypothetical: it is the exact mechanism `investigation_report_g5_dse_iterate_dual_truth.md` root-caused and fixed for a *different* victim (DSE-elevated params). The G5 fix (`sync_motors_component_from_params`, tagging the synced property `source="calculated"` so the resolver's `source=="declared"` gate stops re-deriving from it) was scoped to the DSE-apply call site only. It was never applied to the catalog-motor-pick path, so `resolve_operating_point`'s conditioning has no equivalent protection and loses to the bare declared value every time.

On top of that mechanical finding, the softer honesty problem the IC named is also real and independently confirmed: every text surface that shows a motor's thrust (CLI candidate lines, CLI "motor elegido" line, BOM completeness classification, DSE ranking/filtering) shows the bare catalog peak with **zero condition annotation** — no propeller, no voltage, no "at 4S" — even in the 20/22 motor rows where no richer conditioned data exists at all, and even when it does exist and was computed (see above), the annotation is dropped before display because the underlying number itself was already overwritten.

`resolve_operating_point` itself should not be touched, and should not be removed — it is the one component of this system that already treats thrust correctly. The problem is entirely downstream: nothing yet keeps its output *durable*, and nothing yet marks the bare catalog `thrust_n` for what it is (a coarse, condition-free design-space signal, legitimate for ranking/filtering, illegitimate as a displayed "fact about the motor").

---

## B. As-is: schema, resolve ladder, surfaces

### Schema

`MotorSpec.thrust_n: float` (`library.py` ~line 41) is a **required** field, no default, no optional variant. Every one of the 22 seeded motor rows has one. It sits alongside genuinely intrinsic fields on the same dataclass (`kv_rating`, `diameter_mm`, `weight_g`) with no structural marker distinguishing "this is a fixed physical property of this part" from "this is a peak performance figure that depends on what you bolt to it and how you power it."

### Resolve ladder (`resolve_operating_point`, `library.py` ~909-1017)

Three-tier, always returns a typed `ResolvedOperatingPoint` (never a bare float) labeling its own `resolution_type`, `confidence`, `source_type`, and (post-MOP fix) voltage-validation provenance:

1. `exact_operating_point` — a real `operating_points[]` row matches the query motor+propeller(+compatible voltage).
2. `fallback_operating_point` — a row explicitly marked `fallback_only: true` (self-reported "not propeller-independent physics").
3. `legacy_estimate` — no usable `operating_points[]` row at all; falls back to the bare `MotorSpec.thrust_n`, with `source_note="Bare catalog peak thrust_n; no operating_points[] match on file."` — the resolver's own honest label for exactly the number this investigation is about.

Called from exactly one production site: `component_writers.py:475`, inside `set_motor_component`, gated on `spec.catalog_ref.family == "motor"`. Writes `current_parameters["per_motor_max_thrust_n"]` + JSON `propulsion_resolution` audit blob. This path is correct and was independently hardened by the MOP-1/2/3 fix (`investigation_report_dse_motor_op_dual_truth.md` / "Motor OP Voltage Coherence IC") against voltage-staleness across battery rebinds. Confirmed unmodified and out of scope, per the IC's own lock.

### The competing, unconditioned consumer (`resolve_propulsion_parameters`, `component_resolver.py` 73-249)

Domain-agnostic, called from two production sites — `actions/iterate.py:197-200` (every physical iterate turn) and `param_definition_session.py:963-965` (every wizard-driven recalculation) — **unconditionally, regardless of what changed that turn**. For any component with `output_magnitude == "thrust_n"` and a `properties["thrust_n"]` marked `source == "declared"`, it extracts that bare value and `PhysicalOverride.apply_to` writes it into `current_parameters["per_motor_max_thrust_n"]`, **unconditionally replacing whatever was already there** — no comparison, no "is the existing value fresher/more specific" check.

`bind_motor_from_catalog` (`catalog_bind.py` ~89-99) always sets `output_magnitude="thrust_n"` and always projects `properties["thrust_n"]` with `source="declared"` from the bare `suggestion["thrust_n"]`/`MotorSpec.thrust_n` — its own comment names this as deliberate, pre-existing design: *"FN-007 precedent: thrust_n is the resolvable magnitude for this component so component_resolver derives per_motor_max_thrust_n from it on every recalculation."* This is not an oversight — it is the documented reason `resolve_operating_point`'s conditioning cannot survive: FN-007 predates P2-1 (`resolve_operating_point`) and nothing updated FN-007's assumption once a better computation existed for the same target field.

### Precedent: this exact overwrite class was already found and fixed once (G5), for a different victim

`investigation_report_g5_dse_iterate_dual_truth.md` (CONFIRMED, fixed via `implementation_contract_g5_dse_component_sync.md`) root-caused an unrelated-looking symptom — a DSE-elevated `motor_count`/`per_motor_max_thrust_n` silently reverting on the next unrelated iterate turn — to this identical mechanism: `resolve_propulsion_parameters` always re-deriving from `design_properties.components["motors"]` and `apply_to` always winning. The fix (`component_sync.sync_motors_component_from_params`) keeps the *component* in sync with the fresher *params* value immediately, tagging the synced property `source="calculated"` — which makes the resolver's own `source == "declared"` gate skip re-deriving from it, so the fresher value survives.

**This fix was scoped to the DSE-apply orchestrator call site only** (`orchestrator.py:4332-4353`, calling `sync_motors_component_from_params` right after `invalidate_diverged_catalog_refs`). It is not called from `component_writers.set_motor_component` or from `_apply_catalog_motor_pick` (`param_definition_session.py:416-481`, the interactive catalog-pick flow). So a catalog motor pick's `resolve_operating_point` result has no equivalent protection — it is computed, written once, and then immediately exposed to the exact overwrite mechanism G5 fixed for a sibling case, on the very next recalculation (which, in `_apply_catalog_motor_pick`'s own tail call to `apply_and_recalculate`, can be the *same* wizard turn).

A second, unrelated precedent — MOP-1/2/3 (`investigation_report_dse_motor_op_dual_truth.md` / "Motor OP Voltage Coherence") — fixed a *different* dual-truth failure mode entirely: `resolve_operating_point`'s own resolution going voltage-stale across battery rebinds. That fix improved the conditioned path's own correctness; it does nothing to protect that correctness once computed, from `resolve_propulsion_parameters`.

### Surfaces displaying the bare, unconditioned value

- **CLI, catalog-assisted motor pick** (`motor_catalog_assist.py`): `_format_candidate_line` (~416-425) → `"10.042N, 30g, 2300KV"`; `format_motor_chosen_line` (~428-440) → `"Motor elegido: emax_rs2205s_2300 (10.042N). Sistema recalculado."` Neither names a propeller, voltage, or condition.
- **`ComponentSpec.properties["thrust_n"]`** itself (`catalog_bind.py`), `source="declared"` — read generically by the Board's `_fields()` text renderer (any property on the spec becomes a text line on the card) and by anything else that walks `properties`.
- **BOM completeness** (`project_closure.py`): `_MEASURABLE` frozenset includes `"thrust_n"` — its mere presence (declared, bare, unconditioned) counts as "measurable engineering signal" toward `classify_component` reaching `completeness=="high"` / bucket `"defined"`. No distinction is made between "this comes from a real measured operating point" and "this is a catalog headline peak."
- **Design-space ranking/filtering** (`library.py`): `find_motors_for_requirements` (~406-431) sorts by `abs(m.thrust_n - min_thrust_n)`; `_motor_covers_requirements` gates on `m.thrust_n` against `design_space.min_thrust_n/max_thrust_n`. Both read the bare `MotorSpec.thrust_n`, never a resolved operating point (there is no fixed propeller/voltage yet at candidate-selection time — this is a legitimate, structurally different use, discussed in §D/§F).

---

## C. Seed inventory (governing question C3)

22 motor rows total in `library/motores/_datos.json`. `resolve_operating_point`-relevant data:

| Finding | Count | Detail |
|---|---|---|
| Rows with **no** `operating_points[]` at all | 20 / 22 | `resolve_operating_point` always falls to `legacy_estimate` (bare `thrust_n`) for these — not a duplication, simply no richer data exists yet. No live divergence is possible for these rows today, but also **no protection exists** if richer OP data is added to any of them later without a matching "sync to component" companion change — the same silent-overwrite mechanism would then apply. |
| Rows with `operating_points[]` present | 2 / 22 | `emax_rs2205s_2300`, `sunnysky_r2205_2500` |

**Spotlight — `emax_rs2205s_2300`** (top-level `thrust_n: 10.042`):
- OP row 1: `fallback_only: true`, `thrust_n: 10.042`, `voltage_v: 16.8`, no `propeller_sku`, `source_note: "FALLBACK ONLY. EMAX official: RS2205 2300KV + HQ5045 BN + 4S = 1024 gf max. Not propeller-independent physics."` — **byte-identical to the top-level value.** `component_writers.py`'s own comment confirms this is deliberate: *"★-locked regression contract: OP-miss must reproduce today's exact numeric behavior."* This row exists specifically so `resolve_operating_point`'s fallback tier reproduces the pre-P2-1 number unchanged — it is a compatibility shim, not evidence the top-level figure is condition-free.
- OP rows 2-3: `evidence_status: "hold"` (GetFPV-reproduced table, propeller not traceable to a single SKU) — excluded from resolution entirely.
- OP row 4: real, usable, `evidence_status` clear — `thrust_n: 13.4841`, `propeller_sku: "gemfan_5045_hbn"`, `voltage_v: 16.0` (Oscar Liang thrust-stand test). **34% higher than the bare catalog peak, same motor, different propeller.** This is the row this investigation's empirical proof (§A) used to demonstrate the discard.

**`sunnysky_r2205_2500`** (top-level `thrust_n: 12.5525`): 10 real OP rows (a full voltage/current sweep at 14.8V with `gf_5045x3`), none `fallback_only`. The top-level value exactly equals the *highest* row in that sweep (40A, 1280gf, `gf_5045x3` @ 14.8V) — a legitimate "this is genuinely the same source's peak" curation, not a duplication artifact, but it means the bare `thrust_n` is silently a "best case, one specific propeller" number rather than a motor-alone fact here too. Any other propeller, or the same propeller at a different (also real, lower) point on this motor's own curated sweep, would legitimately resolve to a different, lower `exact_operating_point` value than the bare 12.5525 — and would be discarded by the same mechanism on the next recalculation.

**Conclusion for C3**: the duplication the Engineer's contract named is currently observable in exactly 1 row (`emax_rs2205s_2300`'s fallback tier, by deliberate construction) plus 1 near-duplication (`sunnysky_r2205_2500`'s peak-of-sweep coincidence). The mechanical discard problem (§A) is broader — it applies to **both** rows with real conditioned data today, and silently to any future row the moment richer `operating_points[]` are added, unless a fix addresses the resolver interaction, not just these two seeds' numbers.

---

## D. Honesty options (H0-H3) + phrase matrix

| Option | Description | Assessment |
|---|---|---|
| **H0 — Doc-only** | Leave schema/resolvers untouched; add a code comment/doc note near `MotorSpec.thrust_n` and `bind_motor_from_catalog` stating explicitly "this is a coarse catalog peak, not a motor-alone fact; `resolve_operating_point` is the conditioned source of truth for display/physics." | Costs nothing, fixes nothing. Does not address the mechanical discard (§A) at all — that is a live correctness gap, not a documentation gap. Insufficient alone, same as G5's own "D — narration only" option was judged insufficient there for the identical reason (a bad write already happened; narration doesn't prevent it). |
| **H1 — Keep required; forbid unconditioned presentation; sync/copy hygiene** | `MotorSpec.thrust_n` stays required (still needed for design-space filtering/ranking, §F). Two changes: (a) apply the **already-built G5 tool** (`sync_motors_component_from_params`, or an equivalent motor-specific sync called from `set_motor_component` itself) so a computed `resolve_operating_point` result is written back into the component as `source="calculated"`, closing the resolver's `source=="declared"` gate and making the conditioned value durable across recalculations — exactly as G5 did for DSE; (b) every *display* surface (CLI candidate/chosen lines, BOM `_MEASURABLE` treatment) is required to name the condition (propeller/voltage) whenever `resolution_type != "legacy_estimate"`, and to say "no operating data, catalog peak only" when it is. | **Closest to a minimal, in-precedent fix.** Reuses an already-shipped mechanism instead of inventing a new one. Narrow blast radius (component_writers + a handful of copy strings) if scoped tightly. Still requires a real decision on exactly which surfaces must change vs which can defer — sizing that belongs in an Implementation Contract, not this report. |
| **H2 — Make optional; derive exclusively from `operating_points[]`** | Drop `thrust_n` as a required top-level field; require an `operating_points[]` array (even single-row) for every motor row; `resolve_operating_point` becomes the *only* path, with no `legacy_estimate` bare-field fallback. | Most architecturally "correct" long-term, but the largest blast radius by far: touches the schema (required→optional, a "changes to core contracts" item under CLAUDE.md's forbidden-without-approval list), invalidates `find_motors_for_requirements`/`_motor_covers_requirements`'s ranking/filtering signal (§F), and would require backfilling `operating_points[]` for 20/22 seed rows that currently have none — real, live-sourced data that does not exist yet and cannot be invented. Not a "next IC" scope; a multi-cycle program if ever pursued. |
| **H3 — Vocabulary split** (e.g. `catalog_peak_thrust_n` vs `thrust_n`) | Rename the bare catalog field to something self-describing as a peak/reference figure, reserving an unqualified `thrust_n` (or none) for genuinely conditioned values only. | Solves the *naming* honesty problem cleanly (a field called `catalog_peak_thrust_n` cannot be mistaken for an intrinsic fact), but is a schema/vocabulary change touching every consumer named in §B (12+ call sites across `library.py`, `catalog_bind.py`, `motor_catalog_assist.py`, `project_closure.py`, tests) for a rename alone — before even addressing the mechanical discard. Doesn't fix §A by itself; would need to be paired with H1's sync mechanism regardless. |

**Phrase matrix (current vs. honest, by surface)** — illustrative, not a locked copy deck:

| Surface | Current | Honest (if H1 adopted) |
|---|---|---|
| CLI candidate line | `"10.042N, 30g, 2300KV"` | `"~10.0N (catálogo, sin operating point), 30g, 2300KV"` or, when resolved: `"13.5N a 5045 HBN/4S (medido), 30g, 2300KV"` |
| CLI chosen line | `"Motor elegido: ... (10.042N)."` | `"Motor elegido: ... (10.042N catálogo — se refinará con hélice/batería)."` |
| BOM classification | Silent `_MEASURABLE` credit for bare `thrust_n` | Credit only when `resolution_type != "legacy_estimate"` for the currently-bound configuration, else tail-annotate like the existing `_bom_completeness_tail`/`_bom_sensors_declarative_tail` precedents already do for FC/sensors |

**Default lean (not a Buy — Engineer's call):** H1. It is the only option that (a) fixes the proven mechanical discard using a tool the codebase already built and validated for the sibling case, (b) does not touch required-ness of a field two live consumers (§F) still legitimately need, and (c) scopes to copy + one sync call rather than a schema program.

---

## E. Blast radius if `thrust_n` changes

**If H1 (sync mechanism) is adopted:**
- `component_writers.set_motor_component` gains a call analogous to `sync_motors_component_from_params`, or the existing helper is reused/generalized — the exact shape is an Implementation Contract decision, not this report's.
- `resolve_propulsion_parameters`'s behavior for a catalog-bound motor changes the instant a real `exact_operating_point`/`fallback_operating_point` resolution differs numerically from the bare seed value — for today's seeds, this is observable only for `emax_rs2205s_2300` bound with `gemfan_5045_hbn` at ~16V (10.042 → 13.4841) and `sunnysky_r2205_2500` bound with any propeller/voltage off its own peak-of-sweep point. Every other seed/config is numerically unaffected (no OP data to diverge from).
- **13 test-line hits for the literal `10.042` figure**, across 5 files: `tests/test_assisted_acquisition.py`, `tests/test_catalog_bind_v1.py`, `tests/test_dse_motor_op_dual_truth.py`, `tests/test_phase2_lookup_operating_point.py`, `tests/test_propeller_catalog_bind_ux.py`. Any of these asserting `per_motor_max_thrust_n == 10.042` *after* a propeller/voltage bind that would now resolve to `13.4841` would need to be inspected and, per CLAUDE.md's "retarget, don't delete coverage" pattern already used repeatedly this session (ESC mass hygiene B1), updated to assert the newly-correct conditioned value rather than weakened. This inspection was not performed in this report (would require reading each assertion's exact fixture state) — it is the correct first task of any H1 Implementation Contract, not something to pre-judge here.
- `find_motors_for_requirements`/`_motor_covers_requirements` are explicitly **not** touched by H1 — they keep reading `MotorSpec.thrust_n` directly (a library-level catalog field, not a `ComponentSpec` property), which is unaffected by anything `resolve_propulsion_parameters`/`sync_*` does to a bound project's own component.

**If H0 (doc-only)**: zero test/behavior blast radius — no code changes at all.

**If H2/H3**: blast radius spans schema, 20 seed rows needing backfill or an explicit "no OP data" marker, every §B call site, and an unknown number of tests beyond the 13 `10.042` hits (any test asserting `MotorSpec.thrust_n` presence/shape at all). Sizing this precisely was out of this report's evidence-gathering scope given the IC's explicit non-goal on schema Buy.

---

## F. Buy options + default lean

- **B0 — Defer.** Take no action this cycle; the mechanical discard (§A) remains live but latent (only 2/22 seeds can currently expose it, and only under a specific propeller+voltage combination neither current test suite nor any shipped UI currently drives to that state). Valid if the Engineer judges this not urgent relative to the Geometry/catalog-hygiene axis in flight.
- **B1 — H1, copy + sync hygiene (recommended default lean).** A single Implementation Contract: (1) apply the G5-precedented sync so `resolve_operating_point`'s result survives recalculation, scoped to `set_motor_component`'s existing call site only; (2) update the CLI/BOM phrase surfaces named in §D to name the condition when one exists; (3) triage and retarget (not weaken) the 13 `10.042`-pinning test lines identified in §E. Smallest change that closes the proven correctness gap.
- **B2 — H1's sync only, defer the copy hygiene.** Narrower still: fix the mechanical discard first (a correctness bug, arguably independent of the "is this display honest" question), leave phrase-matrix work for a follow-on IC. Reduces this cycle's surface area if the Engineer wants the bug fixed fastest with the smallest diff.
- **Defer H2/H3 entirely** — both require a schema-level decision (forbidden without explicit approval per CLAUDE.md) and, for H2, a live-sourcing program for 20 seed rows that does not currently exist. Not proposed as this cycle's Buy.

Default lean: **B1**, packaged tightly enough to stay inside "localized extraction / shared helper" (CLAUDE.md's preferred refactor order) — reusing `sync_motors_component_from_params` rather than inventing a second mechanism.

---

## G. Non-goals (confirmed honored by this investigation)

- No code changed. `git status --short -- src/ tests/` is empty for this cycle (confirmed).
- No test changed or added.
- No package version bump.
- `resolve_operating_point` was read, traced, and empirically exercised (live call, not a committed test) — never modified, never proposed for removal.
- No Phase 2.5 hover-energy rewrite re-litigated — `sunnysky_r2205_2500`'s OP rows were read only as seed-inventory evidence for §C, not re-evaluated.
- No ESC/FC/Sensors/Here3/Pixhawk file touched or re-opened — confirmed via `git status`.
- No pose/`mounted_on`/fit/CAD/FEA/MEASURE concept introduced or referenced beyond this report's own citations of prior, already-closed investigations.
- No new architectural subsystem proposed — H1's default lean explicitly reuses an existing, already-shipped helper (`sync_motors_component_from_params`) rather than introducing a new one.
- No invented `operating_points[]` condition, source, or numeric value anywhere in this report — every number in §A/§C is quoted verbatim from the live seed file or from a live `resolve_operating_point`/`resolve_propulsion_parameters` call made this session.
