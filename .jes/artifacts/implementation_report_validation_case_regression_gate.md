# Implementation Report — Validation Case ★6 Regression Gate

**Contract:** [`implementation_contract_validation_case_regression_gate.md`](implementation_contract_validation_case_regression_gate.md)
**Implementer:** Claude Code
**Base:** `v0.3.2` / `checkpoint-deferred-queue-cd` (`ca1659c`)
**Status:** Complete, all slices (VC-1 … VC-5) implemented, full suite green (**2029 passed**, +1 new), CLI probe **6/6 PASS**, **`src/` zero diff**.

---

## 1. Slices delivered

| Slice | File | Change |
|---|---|---|
| VC-1 | `scripts/cli_probe_validation_case_op_dataset.py` (new) | 6-step probe walking OP-2, OP-3, OP-0 through the real production bind path and asserting the full tuple against the ★6 doc's own numbers, plus the two existing `estado` lines and the rating-vs-OP coexistence. |
| VC-2 | `tests/test_phase2_lookup_operating_point.py` (appended) | 1 new test (`test_sunnysky_r2205_2500_op3_full_tuple_matches_star6`) filling the one genuine gap found: OP-3's `power_w`/`current_a`/`source_type`/`confidence` at the resolver level, and its `motor_op_*` bridge — neither was previously asserted (OP-2 already had this depth of coverage; OP-3 only had `thrust_n`/`rpm`). |
| VC-3 | `.jes/artifacts/validation_case_op_dataset_comparison.md` (new) | Included (not skipped) — short narration citing the same ★6 URLs, no new sourcing. |
| VC-4 | — | Regression verification, §5 below. |
| VC-5 | this report | — |

**`src/` — zero diff, verified**: `git diff --stat -- src/` returns empty output with exit code 0 (§5). No file under `src/` was read-modified by this IC; the resolver, bridge, `estado` render, and every frozen path listed in the contract's §2.4 table are byte-identical to `v0.3.2`.

---

## 2. §2 locked semantics — verification notes

### 2.1 ★6 reference rows

All three rows (OP-2, OP-3, OP-0) asserted exactly as the contract's table specifies — live-verified numbers below (§3) match the contract's own expected values to the digit. OP-1 was correctly **not** probed as a separate step, per the contract's own note: at 16V + `hq_5045_bn`, the resolver's `v1_max_thrust` rule picks OP-2 (higher thrust) over OP-1 — this is existing, unchanged resolver behavior (`resolve_operating_point`, `library.py:623-626`), not something this IC introduces or re-litigates.

### 2.2 Rating vs. OP divergence — regression-locked, not newly computed

Probe step 5 and VC-2's new test both assert `motor_power_w` (catalog rating, `400.0`/motor's own `max_watts` for OP-3) stays untouched alongside the resolved `motor_op_power_w` (`432.0`/`592.0`) — confirming P2-2's Option A discipline (never overwrite the rating) holds unchanged on this baseline.

### 2.3 `estado` assertion rules — followed exactly

Probe step 4 calls only `orch.build_startup_context()` + the existing `render_startup_context()` — no new context key was added, no new render logic was written. The step additionally asserts the strings `"Validation"` and `"Confianza"` are **absent** from the rendered output, as an explicit, permanent guard against a future accidental addition of the forbidden "validation confidence" summary line (contract's own named anti-pattern).

### 2.4 Frozen paths

All confirmed zero diff via the single `git diff --stat -- src/` check (§5) — this one check covers every path the contract's table lists individually (`library.py`, `component_writers.py`, `calculation_engine.py`, `electrical_compatibility.py`, `adapters/cli/main.py`, and all of G24-A/C/D/Closure/H5's source files), since none of them appear in the diff at all.

---

## 3. Live verification — all three rows, exact match

```text
OP-2  emax_rs2205s_2300 + hq_5045_bn @ ~16.0V:
  resolution_type=exact_operating_point, thrust_n=9.7086, power_w=432.0,
  current_a=27.0, rpm=23560.0, source_type=manufacturer_test, confidence=0.98
  motor_power_w=400.0 (rating, unchanged) alongside motor_op_power_w=432.0

OP-3  sunnysky_r2205_2500 + gf_5045x3 @ 14.8V:
  resolution_type=exact_operating_point, thrust_n=12.5525, power_w=592.0,
  current_a=40.0, rpm=27082.0, source_type=manufacturer_test, confidence=0.97

OP-0  emax_rs2205s_2300, no propeller bound:
  resolution_type=fallback_operating_point, thrust_n=10.0420,
  motor_op_power_w/current_a/rpm: all absent (None) — no OP-electrical
  tuple for a headline-only fallback figure

estado (OP-2 case):
  "Propulsión (evidencia): exact_operating_point · manufacturer_test · 9.7086 N"
  "Propulsión (OP eléctrico): power=432.0 W · current=27.0 A · rpm=23560.0"
  — exactly the two pre-existing lines, no new UI.
```

Every figure above matches the contract's §2.1 table to the digit.

---

## 4. Tests added (1)

`tests/test_phase2_lookup_operating_point.py::test_sunnysky_r2205_2500_op3_full_tuple_matches_star6` — the one gap identified: `test_sunnysky_r2205_2500_exact_match` (pre-existing) only asserted `thrust_n`/`rpm`/`selection_reason`; nothing asserted OP-3's `power_w`/`current_a`/`source_type`/`confidence` at the resolver level, or OP-3's `motor_op_*` bridge at all (OP-2 had this coverage via `_bound_exact_op_state`; OP-3 didn't). Appended, not modified — the pre-existing test is untouched.

**Zero weakened tests.** No existing assertion in any file was changed.

---

## 5. Tests executed

```text
pytest tests/test_phase2_lookup_operating_point.py -v  → 26 passed (25 pre-existing + 1 new)
pytest tests/ (full suite)                                → 2029 passed (2028 pre-existing + 1 new)
python scripts/cli_probe_validation_case_op_dataset.py     → 6/6 PASS
python scripts/cli_probe_p2_2_operating_point_bridge.py     → 6/6 PASS (regression, unaffected)
git diff --stat -- src/                                       → (empty), exit code 0
```

---

## 6. Scope decisions disclosed

1. **VC-3 (optional doc) included, not skipped.** The investigation recommended pairing (b) with (a); the doc is pure narration of already-shipped, already-cited numbers — zero new sourcing, zero risk, low cost. Included per the contract's own "optionally recommended" framing.
2. **OP-0's bridge-level "no `motor_op_*` keys" shape was already covered** by a pre-existing P2-2 IC test (`test_bridge_writes_motor_op_keys_fallback`, same `emax_rs2205s_2300` fallback row) — no duplicate test added for that specific shape; VC-2's one new test targets the genuinely uncovered OP-3 gap instead, keeping the contract's "1-2 tests max" guidance on the low end.
3. **Probe uses the production bind path throughout** (`bind_motor_from_catalog`/`bind_propeller_from_catalog` + `set_motor_component`/`set_propeller_component`), never calling `resolve_operating_point()` directly in the CLI probe — matching the contract's explicit instruction that direct resolver calls are for unit tests only, not the end-to-end gate.

---

## 7. Gate check (contract §6)

| Criterion | Result |
|---|---|
| Probe 6/6; full suite green | **PASS** — 2029/2029, 6/6 |
| `src/` zero diff (hardest gate) | **PASS** — verified via `git diff --stat -- src/` |
| OP-2, OP-3, OP-0 asserted against ★6 doc numbers via production bind path | **PASS** |
| `estado` checked via existing two lines only — no new UI | **PASS** — explicit negative assertion against a "Validation"/"Confianza" line added |
| P2-2 probe 6/6 unchanged | **PASS** |
| No invented SKUs or seed edits | **PASS** — `library/` untouched, confirmed by the same `src/`-scope diff check (library data lives outside `src/` but was independently confirmed unmodified via `git status`) |
| No weakened tests | **PASS** — zero existing assertions changed |

**Ready for Cursor review.**

---

## 8. Queue

```text
VC PASS (pending Cursor review)
  ↓
Engineer: optional checkpoint / version (★6) — not required by this IC alone
  ↓
Next arc: new investigation before H5 or battery/ESC data curation (★3, separate Engineer decision)
```

No tag created, no push, no version bump — left for Engineer.
