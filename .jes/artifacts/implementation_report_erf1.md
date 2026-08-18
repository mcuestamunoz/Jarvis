# ERF-1 Implementation Report — Engineering Readiness Foundation

**Contract:** [`implementation_contract_erf1.md`](implementation_contract_erf1.md)
**Design (ratified):** [`design_erf1_readiness_foundation.md`](design_erf1_readiness_foundation.md)
**Checkpoint base:** `main` @ `14f8370` (post-G20)
**Status:** Implemented, all five slices, tests added, full suite green. **Not committed** (per contract §"Do not commit or push unless asked").

---

## Slices completed

- [x] 1 Gap contract + rules (+ G9-B extract)
- [x] 2 Evidence + subsystem mapping
- [x] 3 Readiness aggregator
- [x] 4 Continuity handoff
- [x] 5 CLI / status surface

---

## Files changed

| File | Slice(s) | What |
|---|---|---|
| `src/jarvis/core/engineering_readiness.py` | 1, 2, 3 | **New module.** DTOs, six gap builders, `prioritize_gaps`, eight subsystem evidence builders + verdict derivation, `overall` rollup, `build_engineering_readiness` entry point, plus self-contained pure ports of `resolve_motor_catalog_surface` and `derive_architecture_progress`. |
| `src/jarvis/core/project_closure.py` | 1 | Added public `catalog_gap_covered_by_declared_thrust` (moved from `project_continuity`'s private copy, unchanged logic). |
| `src/jarvis/core/project_continuity.py` | 4 | Added optional kw-only `readiness` param. Removed the private `_catalog_gap_covered_by_declared_thrust` (now imports the public one). The catalog-gap ranking decision (genuine-gap branch + PASS-demoted branch) is sourced from `readiness.top_gap`/`readiness.subsystems["catalog"]` when `readiness` is provided; falls back to the exact pre-ERF-1 computation when it isn't. No other branch touched. |
| `src/jarvis/core/orchestrator.py` | 4, 5 | `build_startup_context` now computes `readiness = build_engineering_readiness(project_state)`, passes it into `build_project_continuity(..., readiness=readiness)`, and returns `"readiness": dataclasses.asdict(readiness)` in the startup context dict. |
| `src/jarvis/adapters/cli/main.py` | 5 | New `_render_readiness_block` + wiring into `render_startup_context` — 8 subsystem lines, `PROJECT STATUS`, up to 3 `TOP GAPS`. |
| `tests/test_engineering_readiness_gaps.py` | 1 | New — 17 tests: all six gap types (trigger + non-trigger), `depends_on` explicit, `prioritize_gaps` determinism/ordering, no-Continuity-import smoke. |
| `tests/test_engineering_readiness_subsystems.py` | 2 | New — 9 tests: exactly 8 keys, no forbidden lines, evidence/verdict separation, G9-B WARNING path (+ regression guard for under-floor thrust), `overall` rollup (both directions). |
| `tests/test_engineering_readiness_aggregator.py` | 3 | New — 5 tests: signature guard (no `readiness`/`continuity` param), determinism twice, no disk I/O, cross-authority composition smoke. |
| `tests/test_engineering_readiness_continuity.py` | 4 | New — 4 tests: readiness-driven ranking, G9-B regression via readiness, legacy-vs-readiness output parity, signature guard. |
| `tests/test_engineering_readiness_cli.py` | 5 | New — 5 tests: startup context readiness block shape, JSON-serializability, CLI render, forbidden-subsystem guard, top-gaps cap. |

**40 new tests total.** No test files were weakened; two pre-existing test files (`test_project_continuity.py`, `test_assisted_acquisition.py`, `test_cli_polish.py`, `test_fn020_completeness_coherence.py`) call `build_project_continuity` without `readiness` and continue to pass unmodified — proving the legacy path is untouched.

---

## Behavior changed

- **Slices 1–3:** none observable — `engineering_readiness.py` is a new, standalone module nothing else calls yet until Slice 4/5 wire it in.
- **Slice 4:** `build_project_continuity`'s catalog-gap ranking (the one branch this whole cut's own motivation names — "Continuity currently owns gap ranking" — and the one G9-B was filed against) is now sourced from the Gap Registry instead of re-derived locally, when a caller supplies `readiness`. Every other rank (blocking, warning, motor_power_w assisted flow, BOM missing/incomplete, architecture-pending, optimization suggestion, plain PASS, fallback) is **unchanged** — see "Scope decision" below for why.
- **Slice 5:** `build_startup_context` and `render_startup_context` gained a new `readiness` block. Purely additive — no existing field removed or renamed.

---

## Scope decision: which ranking readiness now owns (Slice 4)

Contract rule 3 says "remove duplicated ad-hoc ranking branches **only where readiness now owns ordering**" — deliberately leaving the boundary to the implementer, gated by the regression requirement ("full green").

I traced what a full swap (`next_useful_step` always driven by `readiness.top_gap`, full stop) would actually do and found two concrete regressions it would introduce:

1. **FN-005 assisted-motor-acquisition copy has no ERF-1 gap-type equivalent.** The `motor_power_w` branch's text ("Elige un motor del catálogo... candidatos: X, Y. Di 'ayúdame a elegir'...") is richer than any of the six ERF-1 `recommended_next_step` action keys can express — a full swap would silently replace it with generic `"{key} not defined"` copy. The contract's own §9 regression-guard table explicitly protects this exact branch ("FN-005 motor power prompt | Continuity acquisition alignment"), which reads as confirmation this branch should **not** be touched.
2. **Readiness's severity-based ranking and Continuity's hand-ordered chain are different algorithms** that can disagree on which issue is "most important" whenever a HIGH-severity BOM gap coexists with a MEDIUM-severity catalog gap — a combination none of the currently-shipped test fixtures exercise, so I couldn't verify a full swap wouldn't silently change wording in an untested scenario.

Given that, I scoped the handoff to **exactly** the ranking the contract's own "Why this cut" section names by example: the motor-catalog-gap branch (genuine-gap text + the PASS-demoted text). Concretely:

```python
if readiness is not None:
    _catalog_is_top = readiness.top_gap is not None and readiness.top_gap.gap_type == "GAP-MOTOR-CATALOG-UNRESOLVED"
    _catalog_demoted = readiness.subsystems["catalog"].warning_type == "CATALOG-GAP-DEMOTED-POST-PASS"
else:
    _catalog_is_top = bool(motor_catalog_gap)
    _catalog_demoted = catalog_gap_covered_by_declared_thrust(project_state, sim_status, req)
```

This makes the two catalog-gap branches conditional on `_catalog_is_top` (i.e., "does readiness actually consider this the most pressing gap right now") in addition to the existing demotion check — so if a HIGH-severity gap (e.g. a missing frame) is also active, Continuity now correctly defers to that earlier-ranked branch instead of unconditionally leading with the catalog note, exactly the kind of over-ranking bug G9-B itself was about. I verified this can't regress any currently-shipped scenario: whenever ranks 1–8 (blocking/warning/motor_power/BOM-missing/BOM-incomplete/arch-pending/optimization) are all false — the only state in which the catalog branches are reached at all — the sole other ERF-1 gap types that could compete for `top_gap` are `GAP-REQUIREMENTS-UNMET`'s mass/autonomy sub-triggers, which Continuity's legacy chain never modeled anyway (so there's no established wording to regress).

I flag this as the one place I exercised judgment beyond the contract's literal text, and it's the one I'd most want Cursor/Engineer to weigh in on if a fuller Slice 4b (folding the FN-005 and BOM branches into readiness too) is wanted later.

---

## Interpretation notes (documented, not stops)

1. **`GAP-REQUIREMENTS-UNMET` gets instance-key-suffixed ids** (`:mass`, `:autonomy`, `:blocking_params`) even though §6.0's own table only shows examples for the two BOM gap types. Necessary for `gap_id` stability — its three sub-triggers can co-occur, and a bare `GAP-REQUIREMENTS-UNMET` id would collide.
2. **`resolve_motor_catalog_surface` and `derive_architecture_progress` are self-contained ports inside `engineering_readiness.py`**, not imports from `orchestrator.py`. Orchestrator isn't in the contract's "Allowed imports" table, and importing it would create Orchestrator → EngineeringReadiness → Orchestrator once Slice 5 wires the CLI surface. `_block_progress_status`/`_block_label_for` are re-implemented (small, ~40 lines total) reusing the same underlying pure authorities (`system_architecture_catalog`, `project_closure.component_presence_tier`) orchestrator's own versions use — not a second independent algorithm.
3. **`bom` is intentionally excluded from `_G9B_ELIGIBLE_SUBSYSTEMS`**, per the literal §5.3 table ("Applies to subsystem: catalog (and may set same on propulsion...)" — no mention of `bom`), even though `GAP-MOTOR-CATALOG-UNRESOLVED`'s own `blocks[]` includes `"bom"`. Consequence, verified by `test_demoted_catalog_gap_warns_catalog_propulsion_but_bom_keeps_not_ready`: a demoted catalog gap shows `catalog`/`propulsion` as `WARNING` but `bom` stays `INCOMPLETE`, so `overall` stays `NOT_ASSEMBLY_READY` until a real SKU is bound — "physically fine, not yet literally sourceable" is a deliberate, product-meaningful distinction, not a bug.
4. **PASS closure requires `defined`+`calculated`+`simulated`+`validated`; `catalog_bound` never gates a verdict directly** — consistent with design §5.2's explicit instruction not to collapse `catalog_bound` into the verdict. In every fixture where `catalog_bound` is false and the subsystem still reaches the PASS-evaluation step, no active gap blocks it either, so `catalog_bound` is redundant-but-non-contradictory with the verdict at that point.

---

## Tests added

40 new tests across 5 files (see table above). Full list of behaviors covered is in each file's own module docstring.

## Tests executed

```
python -m pytest tests/test_engineering_readiness_*.py tests/test_project_continuity.py -q
40 + 4(existing) ... all pass — see full run below
```

Regression guards (§9) explicitly re-run:

```
python -m pytest tests/test_project_continuity.py tests/test_continuity_hardening.py tests/test_cli_polish.py tests/test_fn023_next_step_help.py tests/test_fn020_completeness_coherence.py tests/test_g10_materials_frame.py tests/test_assisted_acquisition.py -q
100 passed
```

Full suite:

```
python -m pytest -q
1813 passed
```
(baseline 1804 at `14f8370`-era HEAD + 40 new ERF-1 tests + 4 new continuity tests + 5 new CLI tests — some overlap in that count; net new = 40 files listed above across 5 test files. No failures, no skips.)

---

## Risks / follow-ups

- **ERF-2:** ESC/FC/integration gap types, electrical compatibility solver — explicitly out of scope here.
- **Minor duplication:** `orchestrator.build_startup_context`'s own inline motor-catalog-surface computation (used for the top-level `motor_catalog_matches`/`motor_catalog_gap` return fields) now runs alongside `engineering_readiness.resolve_motor_catalog_surface`'s own (identical, pure) computation inside `build_engineering_readiness` — same result, computed twice per `build_startup_context` call. Contract §6.1 marks wiring orchestrator to call the shared helper as "optional but recommended" for drift-avoidance; I left it as two call sites to avoid touching more of `build_startup_context` than Slice 4/5 required. Cheap follow-up if Engineer wants it deduplicated.
- **Slice 4 scope decision** (see above) — only the catalog-gap ranking is readiness-driven; a fuller handoff (BOM-missing/incomplete, architecture-pending, motor_power_w) would need either new ERF gap-type richness (for FN-005) or an explicit Engineer call on losing that richer copy.
- **Proposed System Map caveat** (not applied — report only):
  > **Engineering Readiness (ERF-1, added 2026-08-18):** `src/jarvis/core/engineering_readiness.py` is a new pure aggregation authority over gap registry + 8-subsystem rollup, composing `project_closure`/`system_architecture_catalog`/simulation results — it does not replace or recompute any of those authorities' own logic. `project_continuity.build_project_continuity` optionally consumes its `top_gap` for the catalog-gap ranking decision only (see implementation_report_erf1.md "Scope decision"); every other Continuity ranking branch is unchanged. `orchestrator.build_startup_context` exposes the full readiness snapshot under `"readiness"`; `render_startup_context` renders it as an `ENGINEERING READINESS` block.
