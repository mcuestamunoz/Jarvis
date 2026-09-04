# Implementation Report — Block Closure B-PROP-ENERGY

**IC:** `implementation_contract_block_closure_prop_energy.md` (★1–★6 locked)
**Status:** Implemented, full suite green, awaiting Cursor review.

---

## 1. Files changed

| File | Change |
|---|---|
| `src/jarvis/core/battery_catalog_assist.py` | New `detect_battery_sku_token(user_input, *, library=None)` — scans free text for a known battery SKU token; added to `__all__`. |
| `src/jarvis/core/param_definition_session.py` | `try_ingest` intercepts a detected SKU **before** `parse_floats_from_input`/`parse_params_bidir` run, and calls `apply_and_recalculate` with the bound `ComponentSpec` directly. `apply_and_recalculate` gained `battery_catalog_spec: Any | None = None`; when supplied it is written via `set_battery_component` instead of the synthetic `_make_battery_spec(cap)`, so `catalog_ref` survives. |
| `src/jarvis/core/project_closure.py` | New `derive_prop_energy_block_closure(project_state, *, readiness=None)` — pure derivation, `status: "closed"/"not_closed"`, `evidence_tier`, `reasons`, `facts`. No mutation, no new persisted field. |
| `src/jarvis/core/orchestrator.py` | `build_startup_context` imports `derive_prop_energy_block_closure` and attaches `ctx["prop_energy_block_closure"]`, passing the already-computed `readiness` local (avoids a second catalog resolve — see §3). |
| `src/jarvis/adapters/cli/main.py` | `render_startup_context` appends one locked line after the readiness block: `CERRADO — evidencia manufacturer_test/fallback/débil` or `NO CERRADO — descarga de batería excedida` / `... no está cerrado`. |
| `tests/test_block_closure_prop_energy.py` | **New.** 7 tests, §6.1–§6.4 plus two supporting cases (unbound propeller, bare "definir bateria" wizard-path regression guard). |
| `scripts/cli_probe_block_closure_prop_energy.py` | **New**, optional. Human-readable run of the four IC scenarios against the real orchestrator. |
| `docs/IMPLEMENTATION_TASKS.md` | Synced (this change). |
| `.jes/state/engineering_state.json` | Synced (this change). |

No file outside this list was touched. `tests/test_battery_catalog_bind_ux.py` (G27) was not modified.

## 2. Behavior changed

- **New, additive:** `ctx["prop_energy_block_closure"]` on the startup context, and one new locked line in `estado`/`calcular`/`simular` output. Absent field/empty dict on old snapshots is handled by `if block_closure:` — no crash on projects without the key.
- **Bug fix:** `definir bateria <sku>` / `cambia la bateria a <sku>` on a project with an existing catalog-bound (or freeform) battery now correctly re-binds `catalog_ref` and writes the catalog's real `battery_capacity_wh` (e.g. 222.0 Wh for `lipo_6s_10000mah`), instead of destroying `catalog_ref` and writing `6.0` (the SKU's leading digit misparsed as a bare float).
- **Unchanged:** `ASSEMBLY_READY` / `NOT_ASSEMBLY_READY` derivation (`engineering_readiness._derive_overall`), `SubsystemEvidence.validated`, ERF-2 electrical compatibility logic, thrust feasibility (`simulation.status`), all Phase 2.5–2.7-B physics, CLI feasibility semantics copy from the prior IC.

## 3. Regression found and fixed during implementation

`derive_prop_energy_block_closure` originally called `build_engineering_readiness(project_state)` unconditionally. `build_startup_context` already computes `readiness` once for `ctx["readiness"]`, so the unconditional call doubled the catalog-motor resolver invocation per turn, breaking the existing G9-A regression guard `test_startup_context_invokes_catalog_resolver_once` (`spy.call_count == 1` → got `2`). Fixed by adding an optional `readiness` kwarg (computed fresh only if not supplied) and passing the orchestrator's already-computed `readiness` at the call site. Confirmed via full-suite re-run.

## 4. Root cause of the battery re-bind bug (differs from the IC's own hypothesis)

The IC and the prior investigation report pointed at `parse_floats_from_input` (~`param_definition_session.py:1040`) as the likely culprit. Live tracing (monkeypatching `parse_floats_from_input`, `.answer()`, then `set_battery_component` with `traceback.print_stack()`) showed neither of the first two ever fire on this path; the true live route is:

```
orchestrator.py:handle_user_text → _handle_user_text_inner
  → ParamDefinitionSession.try_ingest(user_input)
    → parse_params_bidir(...)  [not parse_floats_from_input]
    → apply_and_recalculate(parsed)
      → set_battery_component(project_state, _make_battery_spec(cap), cap)   # cap = 6.0, catalog_ref lost
```

The fix intercepts at the top of `try_ingest`, exactly the fallback seam the IC anticipated ("trace the live route and patch that seam").

## 5. Tests

**New:** `tests/test_block_closure_prop_energy.py` — 7 tests, all against the real `JarvisOrchestrator` (no hand-built `simulation.status`, no LLM — `_RefuseLLM` stub):

| Test | IC ref | Result |
|---|---|---|
| `test_gate_a_compatible_block_closed_manufacturer_test` | §6.1 | closed, `manufacturer_test`, locked CLI line present |
| `test_dual_block_closed_not_assembly_ready` | §6.2 | closed **and** `NOT_ASSEMBLY_READY` in the same fixture |
| `test_gate_a_incompatible_battery_discharge_not_closed` | §6.3 | not_closed, `battery_discharge_exceeded`, locked CLI line present |
| `test_unbound_propeller_is_not_closed` | §3.2/§6.6 | not_closed, `propellers_not_catalog_bound` |
| `test_battery_rebind_definir_bateria` | §6.4 | `catalog_ref.sku == "lipo_6s_10000mah"`, Wh = 222.0 ≠ 6.0 |
| `test_battery_rebind_cambia_la_bateria_a` | §6.4 | same, alternate phrasing |
| `test_bare_definir_bateria_keeps_wizard_behavior` | regression guard | no-SKU input untouched, catalog_ref survives |

**Executed:**

```
python -m pytest -q tests/test_block_closure_prop_energy.py   → 7 passed
python -m pytest -q tests/test_battery_catalog_bind_ux.py     → 13 passed   (§6.5, G27 unaffected)
python -m pytest -q                                            → 2094 passed (2087 baseline + 7 new, 0 regressions)
```

**Optional probe:** `python scripts/cli_probe_block_closure_prop_energy.py` — confirms all four IC scenarios (compatible closed/manufacturer_test, incompatible not_closed/discharge, both re-bind phrasings) against the real orchestrator; output matches the pytest assertions.

## 6. Confirmations required by §9

- **`ASSEMBLY_READY` unchanged:** `engineering_readiness._derive_overall` and `SubsystemEvidence.validated` were not touched; `test_dual_block_closed_not_assembly_ready` and `test_gate_a_incompatible_battery_discharge_not_closed` both independently assert `readiness.overall == "NOT_ASSEMBLY_READY"` post-fix, matching pre-existing semantics.
- **Re-bind is not 6.0 Wh:** both re-bind tests assert `battery_capacity_wh == pytest.approx(222.0)` and explicitly `!= 6.0`.

## 7. Non-goals respected (§7)

Untouched: `engineering_readiness._derive_overall`/`ASSEMBLY_READY` formula, `SubsystemEvidence.validated` field, `BLOCK_STATUS` enum/10th subsystem, H5/ESC catalog/`EscSpec`, Catalog Foundation SKUs, Gate E Path 4 `define_missing_params` thrust mutation, `GAP-MOTOR-CATALOG-UNRESOLVED` rename, C-081/C-108/G24-B/Option B ERF, P26/P27-A/HD-001–003, CLI feasibility locked strings from the prior IC, invented `motor_power_w`/hover minutes, persisted fidelity ladder. `src/jarvis/core/intent_resolver.py` and `src/jarvis/actions/iterate.py` were not touched — the bug lived entirely in `try_ingest`/`apply_and_recalculate`.

## 8. Remaining risks

- `derive_prop_energy_block_closure`'s catalog-identity checks (`{motors,propellers,battery}_not_catalog_bound`) require `catalog_ref.family` to exactly match `"motor"/"propeller"/"battery"` — any future catalog family renaming needs to update this function in lockstep (no dynamic lookup table exists yet; out of scope per §7).
- `evidence_tier` reads `current_parameters["propulsion_resolution"]` as an opaque JSON string; if that field's shape changes elsewhere, this function's `json.loads`/`.get()` chain degrades silently to `"none"` rather than erroring — matches the "fail to none, never invent a tier" intent, flagged here for visibility.
- No new persisted state — `prop_energy_block_closure` is recomputed every turn from existing readiness/compatibility/sim data; no migration or schema concern.

**Cursor reviews against `implementation_contract_block_closure_prop_energy.md`.**

---

## N1 patch (2026-09-01) — `implementation_review_block_closure_prop_energy.md`, PASS WITH NOTES

**Bug:** `render_startup_context` printed the locked `"NO CERRADO — descarga de batería excedida"` sentence whenever `"battery_discharge_exceeded"` was in `reasons`, but that reason token fires whenever `compat.battery_discharge != "within_limit"` — which includes `"unverifiable"` (no ESC declared), not only an actually-exceeded discharge. On the CLI feasibility fixture (`emax_rs2205s_2300` + `hq_5045_bn` + `lipo_4s_10000mah`, no ESC, `motor_count=4`) discharge is unverifiable, not exceeded, so the rendered `estado` made a false specific claim — the same class of lie the prior IC eliminated for "sin hélice de catálogo".

**Fix (`src/jarvis/adapters/cli/main.py`, `render_startup_context`):** the discharge sentence now gates on `block_closure["facts"]["battery_discharge"] == "exceeded"` (a fact, not a reason token) instead of `"battery_discharge_exceeded" in reasons`. Every other `not_closed` case — including unverifiable discharge — falls through to the generic `"el stack de propulsión/energía no está cerrado"` line. No change to `derive_prop_energy_block_closure`'s rollup logic, reason tokens, `_derive_overall`, or any closed-path/CLI-feasibility copy (per instruction, the optional reason-token rename was skipped since the (1)+(2) copy fix alone is correct and sufficient).

**Optional hygiene applied:** `ParamDefinitionSession.answer()` — a live library battery SKU typed while the wizard is pending `battery_capacity_wh` (wizard-then-SKU path) now catalog-binds via the same `detect_battery_sku_token` + `bind_battery_from_catalog` seam as the IDLE `try_ingest` path, instead of falling through to `parse_floats_from_input` and scraping `6.0` out of `lipo_6s_10000mah`. Live-verified: wizard pending `["battery_capacity_wh"]` + input `"lipo_6s_10000mah"` → `battery_capacity_wh=222.0`, `catalog_ref.sku="lipo_6s_10000mah"` (not 6.0, `catalog_ref` preserved). G27 untouched — this is a distinct seam from the wizard/human-readable phrasing G27 already hardened.

**Test added:** `tests/test_block_closure_prop_energy.py::test_unverifiable_discharge_does_not_claim_exceeded` — drives the real orchestrator on the exact `emax`+`hq_5045_bn`+`lipo_4s_10000mah` (no ESC) fixture; asserts `facts["battery_discharge"] != "exceeded"` and `"descarga de batería excedida"` is absent from rendered `estado`, while the generic not-closed sentence is present. Existing `test_gate_a_incompatible_battery_discharge_not_closed` (Gate A, motor_count=4, actual exceeded case) re-asserted green — still shows the locked discharge sentence.

**Tests executed:**
```
python -m pytest -q tests/test_block_closure_prop_energy.py tests/test_battery_catalog_bind_ux.py tests/test_cli_feasibility_semantics.py
  → 22 passed (8 Block Closure incl. new N1 test, 13 G27, 1 CLI feasibility)
python -m pytest -q
  → 2095 passed (2094 + 1 new N1 test, zero regressions)
```

**Not touched (per instruction):** `_derive_overall`, `SubsystemEvidence.validated=`, electrical compatibility formulas, catalog JSON, closed-path copy, CLI feasibility locked strings, version. `derive_prop_energy_block_closure`'s reason tokens are unchanged (`battery_discharge_exceeded` still means "not within_limit" internally — only the CLI's *use* of that token was narrowed to the `facts`-checked case).

Cursor re-checks only this path. No CLI walk until this is green.
