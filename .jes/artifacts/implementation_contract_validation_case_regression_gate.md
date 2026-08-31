# Implementation Contract — Validation Case ★6 Regression Gate

**Project:** Jarvis  
**Date:** 2026-08-31  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR CLAUDE

**Type:** Regression gate — permanent end-to-end probe (and optional doc) locking the **already-shipped** ★6 operating-point dataset story. **Does not** add physics capability, new data, resolver logic, or `estado` UI. **Zero `src/` diff.**

**Investigation:** [`.jes/artifacts/investigation_report_validation_case_post_v032.md`](investigation_report_validation_case_post_v032.md) — **CLOSED**  
**Investigation review:** [`.jes/artifacts/investigation_review_validation_case_post_v032.md`](investigation_review_validation_case_post_v032.md) — **PASS WITH NOTES**  
**Data authority:** [`.jes/artifacts/phase2_star6_operating_point_validation_case.md`](phase2_star6_operating_point_validation_case.md) — ★6 APPROVED (do not re-source numbers)  
**Checkpoint base:** tag **`v0.3.2`** / **`checkpoint-deferred-queue-cd`** · commit `ca1659c`

**Arc position:** First cut after Validation Case investigation. **Independent** of H5 and G24-B (both frozen). **Not** battery/ESC data curation (Engineer ★3 — out of scope).

**Workflow:** Claude implements **VC-1 → VC-5** + report → Cursor review → probe → checkpoint if Engineer asks. **Version bump (★6) — Engineer's call**; not required in this IC alone.

---

## 0. Engineer ratification (locked)

| ★ | Decision |
|---|---|
| **★1** | **Validation Case** — next block (regression gate, not new capability). |
| **★2** | **Probe/regression gate (b)**, optionally paired with **doc (a)**. **NOT** `estado` surface (c). **NOT** data curation (d). |
| **★3** | Battery/ESC real test data — **future Engineer decision**, not this IC. |
| **★4** | **H5 defer.** |
| **★5** | **G24-B freeze** — `_score_candidate` zero diff. |
| **★6** | Version/tag timing — Engineer's call when packaging. |

**Product contract (Engineer, locked):**

> The ★6 dataset is already a **lookup**, not a derivation. This IC **must not** pretend to add "physical validation" or compute divergences that do not exist for exact matches. It **locks** the end-to-end story (bind → resolve → bridge → existing `estado` lines) as a permanent regression gate.

**Architectural boundary (Engineer matiz — locked):**

```text
❌  Do NOT add a new estado line ("Validation confidence: ...")
✅  Assert the TWO existing lines via render_startup_context / build_startup_context
    — "Propulsión (evidencia): ..." and "Propulsión (OP eléctrico): ..."
    — values must match the ★6 row for the bound combo
```

---

## 1. Problem / intent

### 1.1 Today

P2-1 + P2-2 delivered the ★6 dataset, resolver, bridge, and honest `estado` labels. Individual tests cover pieces (`tests/test_phase2_lookup_operating_point.py`, P2-2 probe). **Nothing asserts the full ★6 narrative as one coherent, reviewable gate** — a future accidental change in the resolver/bridge/render chain could regress without a single probe failing on the documented numbers.

### 1.2 Target

After this IC:

1. **Probe:** walks OP-2, OP-3, and OP-0 (fallback) through the **real production bind path** and asserts the full tuple matches ★6 doc numbers.
2. **`estado` regression:** via **existing** render only — two lines present with expected content; **no new UI**.
3. **Optional doc:** short `.jes` comparison artifact citing ★6 URLs (no new sourcing).
4. **`src/`:** **zero diff** — verified in implementation report via `git diff --stat -- src/`.

---

## 2. Locked semantics (non-negotiable)

### 2.1 ★6 reference rows (assert against doc, not re-invent)

Source of truth: [`phase2_star6_operating_point_validation_case.md`](phase2_star6_operating_point_validation_case.md).

| Row | Motor | Prop | Voltage | Expected (probe must assert) |
|---|---|---|---|---|
| **OP-2** | `emax_rs2205s_2300` | `hq_5045_bn` | **16.0 V** | `resolution_type=exact_operating_point`; `thrust_n=9.7086`; `power_w=432.0`; `current_a=27.0`; `rpm=23560.0`; `source_type=manufacturer_test`; `confidence=0.98` |
| **OP-3** | `sunnysky_r2205_2500` | `gf_5045x3` | **14.8 V** | `exact_operating_point`; `thrust_n=12.5525`; `power_w=592.0`; `current_a=40.0`; `rpm=27082.0`; `manufacturer_test`; `confidence=0.97` |
| **OP-0** | `emax_rs2205s_2300` | *(none)* | **16.8 V** (fallback context) | `resolution_type=fallback_operating_point`; `thrust_n=10.0420`; `power_w`/`current_a`/`rpm` absent or `None` in bridge |

**OP-1 note (informational, not a separate probe step):** at 16 V + `hq_5045_bn`, resolver v1 picks **max thrust** → **OP-2**, not OP-1. Do not assert OP-1 in the end-to-end gate unless a dedicated unit test documents why.

**Voltage setup:** use the same production pattern as `cli_probe_p2_2_operating_point_bridge.py` (`battery_cell_count` → effective voltage) — do not bypass bind path with direct `resolve_operating_point()` only in the CLI probe (unit tests may call resolver directly for isolation).

### 2.2 Rating vs OP divergence (regression lock, not new feature)

For OP-2 path, also assert:

- `motor_power_w == 400.0` (catalog rating — unchanged P2-2 Option A)
- `motor_op_power_w == 432.0` (resolved OP)

This is **already shipped**; the probe documents it persists. **Do not** add a third summary line to `estado`.

### 2.3 `estado` assertion rules (★ Engineer matiz)

| Allowed | Forbidden |
|---|---|
| `orch.build_startup_context()` + `render_startup_context(ctx)` | New keys in `orchestrator` context |
| Assert substring in rendered text for **existing** line prefixes | New `"Validation …"` / `"Confianza …"` line |
| `"Propulsión (evidencia):"` contains `exact_operating_point` + honest thrust | Changing `adapters/cli/main.py` |
| `"Propulsión (OP eléctrico):"` contains `432.0` / `27.0` / `23560.0` for OP-2 case | Any `src/` edit |

### 2.4 Frozen paths (zero diff required)

| Path | Lock |
|---|---|
| `src/jarvis/knowledge/library.py` | **Zero diff** — no seed edits |
| `resolve_operating_point` matching rules | **Zero diff** |
| `component_writers.py` P2-2 bridge | **Zero diff** |
| `calculation_engine.py` / `electrical_compatibility.py` | **Zero diff** |
| `adapters/cli/main.py` | **Zero diff** |
| G24-A/C/D, Closure, H5 surfaces | **Zero diff** |

---

## 3. Implementation slices (VC-1 … VC-5)

Execute **in order**. Suite green after each slice.

### VC-1 — CLI probe (`scripts/cli_probe_validation_case_op_dataset.py` — new)

Deterministic probe (`_RefuseLLM` where applicable). Reuse bind helpers from `cli_probe_p2_2_operating_point_bridge.py` / existing catalog_bind patterns.

| Step | Pass criterion |
|---|---|
| 1 | **OP-2 path:** bind `emax_rs2205s_2300` + `hq_5045_bn` @ ~16 V → `motor_op_*` + resolution evidence match ★6 OP-2 table (§2.1) |
| 2 | **OP-3 path:** bind `sunnysky_r2205_2500` + `gf_5045x3` @ ~14.8 V → full tuple matches ★6 OP-3 |
| 3 | **OP-0 fallback:** bind `emax_rs2205s_2300` only @ ~16.8 V context → `fallback_operating_point`, `thrust_n=10.0420`, no OP electrical tuple |
| 4 | **`estado` regression (OP-2 case):** rendered output contains the **two existing** propulsion lines with values consistent with §2.1–2.2 — **no new line added** |
| 5 | **Rating vs OP lock:** `motor_power_w=400.0` and `motor_op_power_w=432.0` coexist on OP-2 path |
| 6 | **Regression:** `cli_probe_p2_2_operating_point_bridge.py` subprocess still **6/6** |

Target: **6/6 PASS**.

### VC-2 — Unit test extension (optional but recommended)

Extend `tests/test_phase2_lookup_operating_point.py` — **append only**, no weakened assertions:

- One test locking ★6 OP-3 full tuple via `resolve_operating_point` (direct unit level — complements probe).
- Optional: one test locking OP-0 fallback shape if not already fully covered.

Keep count small (1–2 tests max). Reuse existing fixtures (`_suggestion_for`, bind helpers).

### VC-3 — Optional paired doc (Engineer ★2 — optional)

If included: `.jes/artifacts/validation_case_op_dataset_comparison.md`

- For each probed row (OP-2, OP-3, OP-0): cite ★6 `source_reference` URL, state "Jarvis result = curated row (lookup, not derivation)".
- Include rating-vs-OP paragraph (400 vs 432) as **already-displayed** divergence.
- **No new sourced numbers.** Narration only.

Skipping VC-3 is **PASS** if probe + report disclose omission.

### VC-4 — Regression verification

```text
pytest tests/test_phase2_lookup_operating_point.py   → all green (+ VC-2 if added)
pytest tests/ (full suite)                         → 2028+ passed
cli_probe_validation_case_op_dataset.py              → 6/6
cli_probe_p2_2_operating_point_bridge.py             → 6/6
git diff --stat -- src/                              → (empty)
```

### VC-5 — Implementation report

`.jes/artifacts/implementation_report_validation_case_regression_gate.md`

Must include:

- Slices delivered
- Probe step results
- Explicit **`git diff --stat -- src/` empty**
- Disclosure if VC-3 skipped
- Gate check vs §6

---

## 4. Files — expected touch set

| File | Change |
|---|---|
| `scripts/cli_probe_validation_case_op_dataset.py` | VC-1 (new) |
| `tests/test_phase2_lookup_operating_point.py` | VC-2 (optional, append) |
| `.jes/artifacts/validation_case_op_dataset_comparison.md` | VC-3 (optional) |

**Must NOT change:**

- Any file under `src/`
- `library/` JSON seeds
- `pyproject.toml` version (unless Engineer separately requests)
- H5 / G24-B / G24-A/C/D / Closure code paths

---

## 5. Explicit non-goals (this IC)

- New ★6 rows or battery/ESC test data (★3)
- `estado` summary / "validation confidence" line (option c — **forbidden**)
- Divergence computation for exact OP matches (lookup — no divergence exists)
- Changing `resolve_operating_point` priority or `v1_max_thrust` rule
- H5 / ESC catalog / `CatalogRef` 1A
- G24-B `_score_candidate` rewrite
- Mega-IC bundling with unrelated work
- Version bump / tag (Engineer ★6 — separate decision)

---

## 6. Acceptance (Cursor review)

**PASS** if:

- Probe **6/6**; full suite green
- **`src/` zero diff** (hardest gate)
- OP-2, OP-3, OP-0 asserted against ★6 doc numbers via production bind path
- `estado` checked via **existing** two lines only — no new UI
- P2-2 probe **6/6** unchanged
- No invented SKUs or seed edits

**FAIL** if:

- Any `src/` or `library/` seed change
- New `estado` line or render logic change disguised as "validation"
- Probe calls only `resolve_operating_point()` without bind/bridge path (CLI probe)
- Treats this IC as closing battery/ESC §12.2 gaps
- Weakened existing tests

---

## 7. Queue after IC

```text
VC PASS + probe 6/6
  ↓
Engineer: optional checkpoint / version (★6)
  ↓
Next arc: new investigation before H5 or data curation
```

---

**End of contract.**
