# Implementation Report — Closure Policy + Propeller `sku_resolved` (IC 3 / Project Closure arc)

**Contract:** [`implementation_contract_closure_policy_propeller_sku_resolved.md`](implementation_contract_closure_policy_propeller_sku_resolved.md)
**Implementer:** Claude Code
**Base:** `checkpoint-battery-catalog-bind-ux` (`5581b51`)
**Status:** Complete, all slices (Pol-1 … Pol-6) implemented, full suite green (**1976 passed**, +3 new), CLI probe **4/4 PASS + 1 optional PASS**.

---

## 1. Pol-1 — Trace (confirmed live, not assumed)

`_bom_sku_resolved` (`project_closure.py:204-243` post-fix) before this IC:

```python
if family == "motor":
    return default_library.has_motor(sku)
if family == "battery":
    return default_library.has_battery(sku)
return False  # propeller falls through here
```

Reproduced the live bug exactly as the investigation described, against the real on-disk fixture `workspace/crear-un-dron-de-autonomia-con-payload-1kg-184eac8b7789`:

```text
Before fix: ✓ propellers: hq_5045_bn (SKU sin resolver) qty=4 (high)
After fix:  ✓ propellers: hq_5045_bn [hq_5045_bn] qty=4 (high)
```

**Confirmed the only user-visible path affected:** `_bom_sku_resolved` → `_entry()`'s `sku_resolved` field → `_bom_identity_suffix()` → `format_bom_lines()`. Grepped every other reader of `sku_resolved`/`catalog_bound`: zero hits outside `project_closure.py`/`format_bom_lines` and the BOM-entry dict itself — no gap builder, no `_derive_subsystem_verdict` branch, no P2-1/OP resolver code reads this field (matches the investigation's own confirmed finding, re-verified here, not re-assumed).

**`git diff --stat` for this IC** (see §6) touches exactly 5 files: `project_closure.py` (one function), `ENGINEERING_READINESS_VISION.md`, `tests/test_impl_d_sku_bom.py`, `docs/IMPLEMENTATION_TASKS.md`, `.jes/state/engineering_state.json`, plus the new probe script. **Zero** touch to `engineering_readiness.py`, `library.py`, `resolve_operating_point`, `component_writers.py`, `catalog_bind.py`, `orchestrator.py`, `battery_catalog_assist.py`, `semantic_intent_adapter.py`, `state_schema.py`, `param_definition_session.py`.

---

## 2. Files changed

| File | Slice | Change |
|---|---|---|
| `src/jarvis/core/project_closure.py` | Pol-3 | `_bom_sku_resolved`: `if family == "propeller": return default_library.has_propeller(sku)`, plus an expanded docstring explaining the omission's history and confirming the display-only scope. |
| `docs/ENGINEERING_READINESS_VISION.md` | Pol-2 | New **§11 Project Closure — Assembly Ready v1** (rollup rule reference, snapshots A/B, family policy matrix, IC 1/2 ratifications, S0→S1→S2, propeller fix note, deferred list). Header status/date line updated. |
| `tests/test_impl_d_sku_bom.py` | Pol-4 | 3 new tests (§4). |
| `scripts/cli_probe_closure_policy_propeller_sku.py` | Pol-5 | New, self-contained, 4/4 + 1 optional PASS. |
| `docs/IMPLEMENTATION_TASKS.md` | Pol-6 | Top section updated: IC 3 moved from "READY FOR CLAUDE" to "EN REVISIÓN", probe/suite numbers recorded. |
| `.jes/state/engineering_state.json` | Pol-6 | `execution_status`/`current_mode`/`movement_trigger`/`active_operation`/`authority_gates`/`arc.ic3` updated to reflect implementation-complete, awaiting review. |

---

## 3. Behavior changed

- **Display only:** a catalog-bound propeller whose SKU still resolves in `library/helices/_datos.json` now shows `[sku]` in BOM output (`estado`, `views/sistema.md`) instead of the honest-uncertainty marker `(SKU sin resolver)`.
- **Nothing else.** Confirmed via the full suite (1976/1976, including every `engineering_readiness_*`/`requirements_closure`/`battery_catalog_bind_ux`/`propeller_catalog_bind_ux`/`phase2_lookup_operating_point` test file) that no gap, verdict, rollup, or physics behavior changed. `build_engineering_readiness`'s `overall`/subsystem verdicts are byte-identical before and after this change on both investigation fixtures (spot-checked directly, §5).
- **Documentation-only, Track A:** `ENGINEERING_READINESS_VISION.md` §11 records the ratified product contract from IC 1/2/investigation — no code paths were added or changed to produce this section; it is a sync of already-shipped behavior, worded to distinguish "ratified contract" from "code changed in IC 3" per the contract's own instruction.

---

## 4. Tests added (3, `tests/test_impl_d_sku_bom.py`)

| Test | Covers |
|---|---|
| `test_bound_propeller_entry_has_resolved_catalog_ref_and_quantity` | Pol-4 #1 — bound propeller → `sku_resolved=True`, `[hq_5045_bn]` in BOM line, no `(SKU sin resolver)` |
| `test_bound_propeller_sku_removed_from_library_resolves_false` | Pol-4 #2 — Scenario C mirror: `catalog_ref` survives with a SKU that no longer resolves → `sku_resolved=False`, line shows `(SKU sin resolver)`, never `[sku]` |
| `test_motor_battery_sku_resolved_unaffected_by_propeller_fix` | Pol-4 #3 — regression guard: motor/battery `sku_resolved` still `True` via their own branches, unperturbed by the new propeller branch |

**Zero weakened tests.** All 6 pre-existing tests in `test_impl_d_sku_bom.py` pass with unmodified assertions.

---

## 5. Tests executed

```text
pytest tests/test_impl_d_sku_bom.py -v      → 9 passed (6 pre-existing + 3 new)
pytest tests/ (full suite)                   → 1976 passed (1973 pre-existing + 3 new)
python scripts/cli_probe_closure_policy_propeller_sku.py → 4/4 PASS + 1 optional PASS
```

Spot-check (byte-identical rollup verdicts before/after, §1's confirmation extended to the full readiness result):

```text
workspace/crear-un-dron-de-autonomia-con-payload-1kg-184eac8b7789:
  overall: NOT_ASSEMBLY_READY (unchanged)
  gaps: same 6 MEDIUM gap IDs (unchanged)
  only the BOM display line for propellers changed: [hq_5045_bn] instead of "(SKU sin resolver)"

workspace/1-324107ef7006:
  overall: ASSEMBLY_READY (unchanged, from IC 1)
  gaps: [] (unchanged)
```

---

## 6. `git diff --stat`

```text
.jes/state/engineering_state.json    |  65 ++++++++----------
docs/ENGINEERING_READINESS_VISION.md | 129 ++++++++++++++++++++++++++++++++++-
docs/IMPLEMENTATION_TASKS.md         |  17 +++--
src/jarvis/core/project_closure.py   |  17 ++++-
tests/test_impl_d_sku_bom.py         |  79 ++++++++++++++++++++-
5 files changed, 261 insertions(+), 46 deletions(-)
```

Plus one new file: `scripts/cli_probe_closure_policy_propeller_sku.py`.

**Confirms the contract's own acceptance requirement:** no `engineering_readiness.py`, `library.py`, OP resolver, or IC 1/2 source touched.

---

## 7. Scope decisions disclosed

1. **Extended `test_impl_d_sku_bom.py` rather than creating `tests/test_closure_policy_propeller_sku.py`.** The contract listed this as "Preferred" — followed. The BOM-entry-shape tests are the natural home (identical fixture/assertion style to the existing motor/battery entries in that file).
2. **No `tests/test_closure_policy_docs.py` doc-anchor guard.** The contract marks this "optional... not required if Pol-2 is thorough." §11 is thorough (7 subsections, all contract-required content present) — a grep-based anchor test would only restate the same content as a brittle string-match; skipped.
3. **CLI probe step 5 is conditional, not hard-required.** The contract labels it "(Optional)" — implemented it to run against the real on-disk `workspace/` fixture when present, and print a clear "SKIPPED (optional)" line otherwise, since `workspace/` is an untracked scratch directory not guaranteed to exist in every environment (same discipline as the IC 1/2 probes, which never hard-depend on it).
4. **Snapshot B's probe battery SKU is `lipo_6s_10000mah`, not an arbitrary pick.** First attempt used `lipo_4s_5000mah` and hit a genuine `GAP-BATTERY-DISCHARGE-EXCEEDED` — the synthetic snapshot's motor draw (400 W × 4 motors) exceeds that pack's real 50 A continuous limit at 14.8 V nominal. This is the `electrical_compatibility` check working correctly, not a probe bug; switched to `lipo_6s_10000mah` (100 A limit, ≈72 A load at 22.2 V) so the probe demonstrates the intended "all three catalog families resolved, ASSEMBLY_READY" scenario without an unrelated discharge gap obscuring it.

---

## 8. Gate check (contract §6)

| Criterion | Result |
|---|---|
| Pol-1 trace in implementation report with file:line | **PASS** — §1 above |
| Vision doc §11 contains snapshots A/B, family matrix, IC 1/2 ratifications, deferred list | **PASS** |
| Propeller bound → `sku_resolved=True`, `[sku]` in BOM line; live bug fixed | **PASS** — reproduced before/after on the real fixture |
| Probe target met; new tests green; full suite green | **PASS** |
| `git diff` confirms no engineering_readiness/OP/IC 1–2 logic changes | **PASS** — §6 |
| No weakened tests without disclosure | **PASS** — zero existing tests modified |
| Readiness rollup/gap logic unchanged | **PASS** — spot-checked byte-identical on both fixtures |
| Vision doc doesn't claim unimplemented behavior | **PASS** — §11 explicitly distinguishes "ratified contract" from "code changed in IC 3" |

**Ready for Cursor review.**

---

## 9. Queue

```text
IC 3 PASS (pending Cursor review)
  ↓
Engineer: optional checkpoint (checkpoint-closure-policy) + version bump decision
  ↓
Project Closure arc COMPLETE
```

No tag created, no push, no version bump — all explicitly out of scope for this contract, left for Engineer.
