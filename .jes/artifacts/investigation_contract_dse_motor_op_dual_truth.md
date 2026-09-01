# Investigation Contract — DSE ↔ `motor_op_power_w` Dual-Truth (Post-P2-2)

**Project:** Jarvis  
**Date:** 2026-08-31  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output:** `.jes/artifacts/investigation_report_dse_motor_op_dual_truth.md`

**Status:** READY FOR CLAUDE

**Type:** Investigation — state consistency + scoring honesty bug (DSE explore/apply vs P2-2 OP bridge). **Not** UX routing. **Not** catalog acquisition.

**Origin:** CLI field walk @ **`v0.3.3`** — project **`autonomía-15-min`** (`7efc98205ee6`). Manual `--chat` walk after Validation Case regression gate checkpoint.

**Checkpoint base:** tag **`v0.3.3`** / **`checkpoint-validation-case-regression-gate`** · commit `ceb44b4`

**Prior arcs (CLOSED — do not re-open without regression proof on v0.3.3):**

| Delivered @ v0.3.3 | Scope |
|---|---|
| **P2-2** | `motor_op_power_w` / `motor_op_current_a` / `motor_op_rpm` bridge; `effective_motor_power_w()` OP-first for autonomy + electrical |
| **G5** | `sync_motors_component_from_params` after DSE apply; iterate no longer reverts DSE motor_count/thrust |
| **G24-A/C** | Apply-by-index; viable-slot reservation; honest explore CTA |
| **Validation Case gate** | Probe + regression test for ★6 OP dataset |

**Relationship to G5 (explicit):**

G5 closed **params-only DSE apply → subsequent iterate** clobbering `motor_count` / `per_motor_max_thrust_n`.  
**This contract is a different dual-truth:** **DSE explore/apply** vs **`motor_op_power_w`** introduced by P2-2. Same *family* (DSE params vs component/OP truth); **different fields, different code path, different user-visible symptom** (false autonomy/margin promises, not thrust revert).

**Blocks:** Trust in `optimiza para autonomía` + `aplica la N` on any catalog-bound motor with exact OP. Do **not** extend DSE grids or product autonomy messaging until this is understood and fixed.

**Workflow:** Investigate → repro test(s) → short report → Engineer ★ → (optional) IC contract → implement → review → probe → checkpoint. **No production fix in this contract.**

---

## 0. Intent

After P2-2, live calc/sim correctly uses **`motor_op_power_w`** (resolved operating point power) for autonomy when a catalog motor + propeller combo is bound:

```text
autonomía ≈ (battery_capacity_wh / (motor_op_power_w × motor_count)) × 60
```

**Design Explorer** (`design_explorer.explore`) evaluates autonomy candidates using a **different effective power** because baseline normalization via `apply_components_delta(project_state, {})` **drops `motor_op_power_w`** and resets `motor_power_w` to the catalog rating.

User-visible cliff (reproduced live):

| Step | Command / action | DSE / CLI promise | Live result |
|---|---|---|---|
| Explore baseline | `optimiza para autonomia` | autonomía **8.325 min** | `calcular` / live: **7.7 min** (@ 432 W OP) |
| Apply #1 | `aplica la mejor` (motor_power_w 260) | explore score **12.808 min** | apply result: **7.7 min** unchanged |
| Apply #3 | `aplica la 3` (battery Wh 333) | explore score **12.488 min**, viable ✓ | apply: **11.6 min**, sim **fail**, margin **0.998** |

User loses trust in DSE numbering — explore ranks and scores candidates that **do not materialize** after apply on OP-bound projects.

**Hypothesis (strong, partially verified in Cursor pre-investigation):**

1. `DesignExplorer.explore()` normalizes via `apply_components_delta(state, {})`, which re-runs `set_motor_component` and **does not preserve** existing `motor_op_power_w` in the params dict used for candidate evaluation (or overwrites `motor_power_w` back to catalog rating while omitting OP keys).
2. `_apply_delta` changes `motor_power_w` or `battery_capacity_wh` but **never** updates or clears `motor_op_power_w` coherently.
3. `_handle_apply_exploration` merges delta onto **live** `project_state.current_parameters`, where **`motor_op_power_w` survives** → `effective_motor_power_w()` still reads OP power → autonomy unchanged or differently computed than explore preview.
4. Battery candidates add a **second divergence**: explore uses one mass model; apply runs `invalidate_diverged_catalog_refs` + heuristic `battery_mass_kg` → margin/can_fly differ (viable in explore → fail after apply).

---

## 1. Evidence (mandatory read)

| Artifact | Location / note |
|---|---|
| Field walk project | `workspace/autonomía-15-min-7efc98205ee6/` (runtime — may be gitignored) |
| Live state (post apply #3) | `state.json` — `motor_op_power_w: 432.0`, `motor_power_w: 260.0`, `battery_capacity_wh: 333.0`, battery `catalog_ref` cleared |
| Bound combo | Motor `emax_rs2205s_2300` + prop `hq_5045_bn` → exact OP 9.7086 N, 432 W, 27 A |
| CLI transcript | Engineer field walk 2026-08-31 (this session) |
| Code anchors (Cursor pre-read) | `calculation_engine.effective_motor_power_w` · `design_explorer.explore` baseline normalize · `component_writers.apply_components_delta` empty-delta path · `orchestrator._handle_apply_exploration` params-only branch · `catalog_bind.invalidate_diverged_catalog_refs` |

### 1.1 Numeric locks (investigator must re-verify on baseline)

```text
# Live OP-bound autonomy (222 Wh, 4 motors, 432 W OP):
222 / (432 × 4) × 60 = 7.708 min  → CLI rounds 7.7

# Explore baseline without motor_op_power_w (400 W rating):
222 / (400 × 4) × 60 = 8.325 min  → matches explore "Línea base"

# Apply #3 with OP preserved (333 Wh):
333 / (432 × 4) × 60 = 11.562 min → CLI rounds 11.6

# Explore #3 promise (333 Wh, 400 W rating):
333 / (400 × 4) × 60 = 12.488 min → matches explore candidate #3 score
```

### 1.2 Secondary field notes (same walk — report may cross-reference, do not expand scope)

| ID | Symptom | Severity |
|---|---|---|
| FN-R1 | `definir battery/propellers` @ arch 4/4 → iterate wizard, not catalog re-bind | MEDIUM |
| FN-R2 | `ayúdame a elegir` noop when motor+prop+battery catalog-bound → dumps `estado` | MEDIUM |
| FN-R3 | Bare `1` after explore → LLM analyze, not `aplica la 1` | MEDIUM |
| FN-R4 | `LiPo 5000mAh` without cell count → 18.5 Wh silently | LOW |
| FN-R5 | Objective 15 min infeasible with current catalog combo — product signal gap | product |

**Primary scope of this contract:** DSE ↔ OP dual-truth (§0). FN-R* are context only unless directly caused by the same root path.

---

## 2. Investigation questions (must answer in report)

| ID | Question |
|---|---|
| Q1 | **Exact explore path:** When `apply_components_delta(state, {})` runs at explore start, which `current_parameters` keys are set/cleared for OP-bound motor+prop+battery? Trace `set_motor_component` / `set_battery_component` order. Why is `motor_op_power_w` absent in `base_params` while present in on-disk state? |
| Q2 | **Explore candidate eval:** For params-only deltas (`motor_power_w_factor`, `battery_capacity_wh_factor`), does `_evaluate(applied)` use `effective_motor_power_w()`? If `motor_op_power_w` is absent in `applied`, confirm autonomy uses rating-only — quantify error vs live. |
| Q3 | **Apply path:** In `_handle_apply_exploration` params-only branch, which keys are merged from live state vs recomputed? Why does `motor_op_power_w` persist after apply when explore assumed it absent? Is this intentional per P2-2 Option A? |
| Q4 | **Battery apply #3:** Trace `battery_capacity_wh: 222→333` + `invalidate_diverged_catalog_refs` + `battery_mass_kg` heuristic. Why explore marked candidate **viable** (margin ~1.03) but apply **fail** (margin 0.998)? Same calc engine in both paths? Same mass inputs? |
| Q5 | **G5 interaction:** Does `sync_motors_component_from_params` after DSE apply affect `motor_op_*` keys? Any revert or refresh of OP on apply? |
| Q6 | **Scope of hazard:** Besides `mejorar_autonomia`, which goals / deltas are affected when `motor_op_power_w` is set? (`reducir_masa`, `aumentar_payload`, electrical_compatibility?) |
| Q7 | **Fix options (report only — do not implement):** |
| | **A)** Explore normalization preserves `motor_op_*` when components unchanged (mirror live calc truth) |
| | **B)** Explore strips `motor_op_*` **and** apply strips/ refreshes OP when params-only delta touches power/energy fields |
| | **C)** `_apply_delta` + apply path explicitly reconcile OP vs rating (single helper, analogous to `invalidate_diverged_catalog_refs`) |
| | **D)** DSE scoring uses `effective_motor_power_w()` on both explore and apply — enforce one authority |
| | **E)** Message-only / CTA honesty (insufficient alone — document why) |
| Q8 | **Regression surface:** List tests to add/update; name probe script shape if IC follows. |
| Q9 | **Recommendation:** One primary fix direction + explicit non-goals. Does this require a P2-2 contract amendment or a new G5-style sync slice? |

---

## 3. IN SCOPE

| # | Work |
|---|---|
| 1 | Code trace for Q1–Q6 with file:line citations on baseline `ceb44b4` |
| 2 | **Repro test(s)** — new file e.g. `tests/test_dse_motor_op_dual_truth.py` (name at investigator discretion) |
| 3 | Short report `.jes/artifacts/investigation_report_dse_motor_op_dual_truth.md` |
| 4 | Optional: minimal CLI probe script e.g. `scripts/cli_probe_dse_motor_op_dual_truth.py` if it clarifies live story (not required for PASS) |

### Required repro test shape (minimum 3 cases)

```text
CASE A — explore vs live baseline mismatch
  1) Project: catalog motor + prop bound → exact OP → motor_op_power_w set (432 W fixture)
  2) design_explorer.explore(state, "mejorar_autonomia")
  3) ASSERT exploration.baseline_simulation.autonomy_min
       == CalculationEngine().build(live_params).autonomy_min
       (must FAIL on current main — documents explore lie)

CASE B — apply does not deliver explore autonomy promise (motor_power_w_factor)
  1) Same OP-bound project
  2) explore → take viable[0] with motor_power_w_factor delta
  3) orchestrator._handle_apply_exploration(index=1) (or handle_user_text "aplica la mejor")
  4) ASSERT post-apply autonomy_min matches explore candidate simulation autonomy_min
       OR assert documented intentional divergence with user-visible warning
       (must FAIL on current main for motor_power_w candidate)

CASE C — battery Wh delta viable → apply margin cliff
  1) Same OP-bound project, payload/mass near margin edge (field-walk-like fixture)
  2) explore → candidate with battery_capacity_wh_factor only
  3) apply that candidate by index
  4) ASSERT sim.can_fly and safety_margin_ratio consistent with explore candidate
       OR assert single mass model used in both paths
       (must FAIL on current main if explore viable → apply fail reproduced)
```

Tests may use programmatic `ExplorationResult` + `_handle_apply_exploration` (same pattern as `test_g5_dse_iterate_dual_truth.py`, `test_impl_c_catalog_aware_dse.py`). Mark **xfail** only if Engineer explicitly requests; default: **plain fail** demonstrating bug.

---

## 4. OUT OF SCOPE

- Implementing the fix (investigation only unless Engineer adds §Fix after report)
- FN-R1–R5 routing UX (separate contracts unless Engineer merges)
- H5 / ESC catalog / battery data curation
- G24-B `_score_candidate` rewrite
- Changing P2-1 matching rules or ★6 OP dataset
- Weakening tests or adjusting explore scores to match wrong apply behavior
- Version bump / checkpoint

---

## 5. Deliverables

1. **Investigation report** — answers §2 Q1–Q9; one recommended fix option; mermaid optional (explore normalize → evaluate → apply)  
2. **Failing repro test(s)** — minimum CASE A + B; CASE C if reproducible without fragile tuning  
3. **Baseline table** — suite pass count on `ceb44b4`; note if field-walk workspace unavailable  

**No production fix in this contract.**

---

## 6. Acceptance (Cursor review)

| Verdict | Criteria |
|---|---|
| **PASS** | Report identifies exact write/eval path; repro test(s) fail on current main for documented mismatch; recommendation is bounded and cites code |
| **PASS WITH NOTES** | Minor gap in CASE C tuning but A+B solid |
| **FAIL** | Inconclusive root cause; tests pass on main without explanation; fix implemented without approval |

---

## 7. Suggested queue after investigation

```text
DSE motor_op investigation PASS
  → Engineer ★ on fix option (likely A/C/D combo — investigator recommends)
  → Implementation Contract (single slice: explore+apply OP coherence)
  → Claude implements
  → Cursor review
  → Probe + checkpoint (v0.3.4 candidate)

Parallel (optional, not blocking):
  → FN-R1/R2/R3 UX investigation if Engineer wants acquisition routing arc
  → Battery/ESC data curation (Engineer/research — not IC-shaped)
```

---

## 8. Engineer decision stub (post-report)

| Option | Action |
|---|---|
| **★ Fix** | Ratify recommended option from report → IC → implement on `v0.3.3` baseline |
| **★ Defer** | Document as known limitation in `estado`/explore CTA only — **not recommended** (live walk proved user harm) |
| **★ Merge with G5 follow-up** | Only if report proves one shared reconciliation helper covers both thrust sync and OP sync |

---

*End of investigation contract.*
