# Investigation Report — Validation Case Post-v0.3.2

**Contract:** [`investigation_contract_validation_case_post_v032.md`](investigation_contract_validation_case_post_v032.md)
**Checkpoint base:** `v0.3.2` / `checkpoint-deferred-queue-cd` (`ca1659c`)
**Investigator:** Claude Code
**Status:** Complete. No `src/` changes, no test changes, no version bump — investigation only, per contract §0.4.

---

## 1. Executive summary

Baseline verified healthy (§2): 2028 suite, all 7 probes green. `git diff v0.3.1 v0.3.2 --stat` shows the entire delta between the two tags is exactly Deferred Queue C+D (`catalog_bind.py`, `design_explorer.py`, `orchestrator.py`'s CTA branch, tests, docs) — **zero lines touched** in `component_writers.py`, `calculation_engine.py`, `electrical_compatibility.py`, `library.py`, or `adapters/cli/main.py`'s propulsion-evidence rendering. This directly answers V7: **C+D changed nothing about the Validation Case calculus** — confirmed by diff, not inference.

Re-tracing V1–V11 on `v0.3.2` reproduces the prior investigation's conclusion with fresh evidence, not a citation: the ★6 dataset (2 real motor SKUs, 2 real propellers, manufacturer-sourced URLs) is fully shipped as a **lookup**, not a derivation, so there is no numeric "divergence" left to compute for an exact match — `resolve_operating_point("emax_rs2205s_2300", propeller_sku="hq_5045_bn", voltage_v=16.0)` still returns the curated row verbatim (`432.0 W`, `27.0 A`, `23560.0 RPM`, `confidence=0.98`), and the one genuine model-vs-rating divergence (`motor_power_w=400.0` vs `motor_op_power_w=432.0`) is already computed and already displayed in `estado`. No `src/` harness beyond the resolver + P2-2 bridge exists or is implied to exist.

**What remains open is narrower and more honestly scoped than "Validation Case" sounds**: (a) a documentation artifact tying the already-shipped numbers into one explicit narrative, (b) a permanent regression probe locking the ★6 story end-to-end, (c) an `estado` summary line — all three are small, additive, `src/`-light-or-free. The one item that would add genuinely *new* engineering value — real, sourced battery/ESC test data — is **data curation**, not an IC (★7): the code paths to consume such data already exist and are untouched.

**Recommendation:** a small, **probe-first IC** (option b, optionally paired with a) — lock the ★6 narrative as a permanent regression gate and, if Engineer wants it, a short `.jes` comparison doc. **No `estado` surface change** (option c) unless Engineer specifically wants the visibility — not required to close a gap, since the numbers are already shown across two existing lines. **Defer data curation** (option d) as an explicit, separate Engineer-driven decision. **H5 and G24-B remain frozen**, unchanged from the prior investigation, re-confirmed here with fresh v0.3.2 checks, not carried over from memory.

---

## 2. Baseline verification (`v0.3.2` / `ca1659c`)

| Check | Result |
|---|---|
| `pytest tests/` | **2028 passed**, 0 failed |
| `cli_probe_g24_viable_selection_honest_cta.py` | **6/6 PASS** |
| `cli_probe_frankenstein_name_clear.py` | **5/5 PASS** |
| `cli_probe_g24_apply_by_index.py` | **6/6 PASS** |
| `cli_probe_p2_2_operating_point_bridge.py` | **6/6 PASS** |
| `cli_probe_requirements_closure.py` | **5/5 PASS** |
| `cli_probe_battery_catalog_bind_ux.py` | **6/6 PASS** |
| `cli_probe_closure_policy_propeller_sku.py` | **4/4 PASS + 1 optional** |

No surprises. Proceeding to Validation Case trace.

---

## 3. Validation Case — deep trace

### 3.1 Already delivered in code (V1)

| Piece | Status | Evidence |
|---|---|---|
| ★6 curated dataset | Shipped | `library/motores/_datos.json` (`emax_rs2205s_2300`, OP-1/OP-2), `sunnysky_r2205_2500` (OP-3); `library/helices/_datos.json` (`hq_5045_bn`, `gf_5045x3`) — all with real `source_reference` URLs, `source_type="manufacturer_test"`, `confidence` |
| Lookup resolver | Shipped | `library.resolve_operating_point` (unchanged since v0.3.1, confirmed by diff §1) |
| Full electrical tuple bridge | Shipped | `component_writers.set_motor_component` writes `motor_op_power_w`/`motor_op_current_a`/`motor_op_rpm` when `resolution_type ∈ {exact, fallback}` (P2-2, unchanged) |
| Honest `estado` labeling | Shipped | Two distinct lines: `"Propulsión (evidencia): {resolution_type} · {source_type} · {thrust_n} N"` and `"Propulsión (OP eléctrico): power={W} · current={A} · rpm={rpm}"` (`adapters/cli/main.py`, unchanged) |
| Test coverage | Shipped | `tests/test_phase2_lookup_operating_point.py` (25 tests, includes the exact/fallback/legacy bridge matrix and both `estado` display cases) |

### 3.2 Any harness beyond lookup? (V2)

`grep -rln "validation.*case\|Validation Case" src/ tests/` returns exactly one hit: `tests/test_phase2_lookup_operating_point.py`'s own module docstring, which *references* the ★6 dataset by name as its data source — there is no separate comparison/divergence-computation module, script, or report generator anywhere in `src/`. Confirmed unchanged from the prior investigation.

### 3.3 Lookup vs. derivation — is there a number to diverge? (V3)

Re-verified live on `v0.3.2`, not cited: `resolve_operating_point("emax_rs2205s_2300", propeller_sku="hq_5045_bn", voltage_v=16.0)` → `resolution_type="exact_operating_point"`, `thrust_n=9.7086`, `power_w=432.0`, `current_a=27.0`, `rpm=23560.0`. These are the **same numbers as the curated ★6 row** (`_resolved_from_op_row`, `library.py`) — not derived, not estimated, a direct field copy. For an exact match, "Jarvis's result" and "the real source" are the same object by construction. There is no numeric divergence to compute here, confirmed again on the current baseline.

### 3.4 What genuine divergences exist and are already shown (V4)

The one real divergence in the system remains **catalog rating vs. resolved OP power**: `motor_power_w=400.0` (flat `MotorSpec.max_watts`) vs `motor_op_power_w=432.0` (the same motor's real draw at this specific bound combo) — an ~8% gap, live-verified unchanged, and already rendered as two separate `estado` lines (§3.1). No other divergence source exists: the ★6 rows are internally P=IV-consistent (checked previously, unchanged since no seed data changed), so there is no physics-law violation to surface either.

### 3.5 §12.2 success-criteria map (V5)

Re-verified against `v0.3.2` code, table unchanged from the prior investigation (no relevant file touched by C+D):

| §12.2 item | Status |
|---|---|
| 1–4 (identify component/conditions/source data, calc derived magnitudes) | **Done** — ★6 dataset + resolver |
| 5 (differentiate real vs. estimate) | **Done** — `resolution_type`/`source_type` + honest `estado` labels |
| 6–9 (compatible combos, thrust/power/consumption) | **Done** — resolver + P2-2 bridge |
| 10 (validate ESC limits) | **Partial** — `electrical_compatibility` checks work on a freeform-declared `current_a`; no curated *real test* ESC data exists (H5 confirmed still absent, §4) |
| 11 (validate battery limits) | **Partial** — `GAP-BATTERY-DISCHARGE-EXCEEDED` works on catalog battery spec-sheet fields (`max_continuous_current_a`/`c_rating`); no curated real-test battery data beyond spec sheets |
| 12 (T/W, safety margin) | **Done** — unaffected by this domain, pre-existing calc/sim |
| 13 (propagate design changes) | **Done** — untouched pipeline |
| 14 (provenance traceability) | **Done** — `source_type`/`confidence`/`source_reference` on every OP row |

No item moved between "done"/"open" since the prior investigation — confirmed by the empty diff on every relevant file (§1).

### 3.6 Battery / ESC domain (V6)

Unchanged: batteries are either freeform-declared or catalog-bound to library **spec-sheet** fields (`energy_wh`, `max_continuous_current_a`, `c_rating` — manufacturer datasheet numbers, not independent lab-test comparisons); ESC has zero catalog path at all (H5, §4). Neither domain has a "real measured test vs. our model" comparison the way the motor OPs do. This is the one place §12.2's vision genuinely isn't met yet — and closing it requires **new sourced data**, not new code (the consuming code — `electrical_compatibility.py`, battery bind — already works on whatever spec numbers it's given).

### 3.7 Does G24C/D change the calculus? (V7) — confirmed NO, by diff

`git diff v0.3.1 v0.3.2 --stat -- src/jarvis/core/component_writers.py src/jarvis/core/calculation_engine.py src/jarvis/core/electrical_compatibility.py src/jarvis/adapters/cli/main.py src/jarvis/knowledge/library.py` returns **empty**. This is stronger than "no interaction found" — it's proof no interaction is *possible*, since none of these files changed at all between the two tags. C+D's entire footprint is `catalog_bind.py` (G24D's `.name` fix), `design_explorer.py`/`orchestrator.py`'s explore-message branch (G24C), and their tests — none of which the Validation Case domain reads or writes.

### 3.8 IC-shaped options (V8)

| Option | Shape | Sketch |
|---|---|---|
| **(a) Documentation artifact** | Docs-only, zero `src/` touch | A `.jes/artifacts/*.md` narrating the ★6 comparison explicitly: for each real OP row, state the source, the resolved Jarvis output, and confirm they match by construction (lookup) — plus the one real divergence (rating vs. OP) with its numbers. Essentially formalizes what's already true and already displayed, into one discoverable place. |
| **(b) Probe / regression gate** | IC-shaped, small, `tests/`+`scripts/` only | A permanent CLI probe (or extended test) that walks all three ★6 exact/fallback rows end-to-end (bind → resolve → bridge → `estado`) and asserts the full tuple matches the documented ★6 values exactly — turns the "the numbers are right" claim from an implicit property of untouched code into an explicit, permanently-checked one. Protects against a future *accidental* regression in the resolver/bridge chain that today's tests would catch individually but nothing currently asserts as one coherent "story." |
| **(c) `estado`/CLI summary surface** | Small `src/` touch (`adapters/cli/main.py` + `orchestrator.py`, same shape as P2-2's own display addition) | A single "validation confidence" line summarizing resolution_type/source/confidence across the whole propulsion chain, distinct from the two existing lines. Real, but not clearly needed — the two existing lines already carry this information; a third summary line risks being redundant rather than additive. |
| **(d) New sourced data** | **Not IC-shaped — Engineer data curation** | Source 1-2 more real, cited data points (most valuably: a real battery discharge test, or a real ESC current rating) with the same ★6 discipline (real URL, `source_type="manufacturer_test"`, Engineer-approved). This is the only option that would move any §12.2 item in §3.5 from "partial" to "done" — and it cannot be done by an implementation IC at all (★2: no invented SKUs; sourcing real numbers is a research/citation task, not code). |

### 3.9 Live gap (V9) — none reproduced

No false-confidence gap exists: every OP-resolved value is labeled with its `resolution_type`/`source_type`, live-reconfirmed (§3.3-3.4). No user-visible hole beyond §3.6's data-sourcing gap, which is honestly labeled as "spec-sheet" rather than misrepresented as "manufacturer test."

### 3.10 Scope / risk / touch surfaces (V10)

| Option | Touch surface | Risk |
|---|---|---|
| (a) Docs | `.jes/artifacts/*.md` only | None |
| (b) Probe | `scripts/cli_probe_validation_case_op_dataset.py` (new), possibly 1-2 assertions added to `tests/test_phase2_lookup_operating_point.py` | Very low — read-only assertions over already-tested, already-frozen code paths |
| (c) `estado` surface | `orchestrator.py` (context key), `adapters/cli/main.py` (render) | Low-medium — same shape as P2-2's own addition, but genuinely optional value (§3.8) |
| (d) Data sourcing | `library/baterias/_datos.json` / new `library/esc/` (blocked on H5 schema anyway) | Out of IC scope entirely; Engineer/research task |

### 3.11 Reusable fixtures (V11)

`tests/test_phase2_lookup_operating_point.py`'s `_bound_exact_op_state`-style fixtures (already used by both P2-1 and P2-2 tests) are directly reusable for option (b)'s probe — no new fixture machinery needed, matching the prior investigation's own A7 finding, re-confirmed.

---

## 4. Frozen candidates — re-verified on v0.3.2

### 4.1 H5 (ESC catalog) — still no live blocker, still frozen

Re-checked live: `CatalogRef.family: Literal["motor", "battery", "propeller"]` (`action_schema.py:139`) — unchanged, no `"esc"`. `library/esc/` does not exist (`ls library/` → `baterias`, `helices`, `materiales`, `motores` only). `cli_probe_closure_policy_propeller_sku.py`'s freeform-ESC Snapshot A/B still reaches `ASSEMBLY_READY` (§2, 4/4 PASS). C+D's diff touches none of this (§3.7). **No new evidence changes the prior investigation's defer conclusion.**

### 4.2 G24-B (`_score_candidate` rewrite) — still frozen, and G24C reduced its urgency

`git diff v0.3.1 v0.3.2 -- src/jarvis/core/design_explorer.py | grep -c "_score_candidate"` → 1 hit, and it is a comment reference inside `_finalize_viable_list`'s docstring, not the function body (confirmed identically in IC C's own implementation report). G24C's viable-slot reservation already closed the practical gap the prior investigation used to justify considering G24-B (catalog candidates reliably reach `.viable` now — verified live in IC C, unaffected here). **No new evidence for reopening the ★6 scoring lock.**

---

## 5. Comparison matrix

| Criterion | Validation Case (next?) | H5 ESC | G24-B |
|---|---|---|---|
| Live gap on v0.3.2 | No (see §3.9) — only a data-sourcing gap for battery/ESC, not a code gap | No | No — G24C already closed the practical selection gap |
| Post-C+D incremental value | None from C+D itself (§3.7); the domain is simply unaffected | None | Lower than before G24C (urgency reduced) |
| IC-shaped vs research/data | Split: (a)/(b)/(c) are IC-shaped and small; (d) is research/data, not an IC | Would be IC-shaped, but blocked on an Engineer schema-lock decision first | IC-shaped but explicitly still locked |
| Architectural risk | Low across (a)/(b); low-medium for (c); n/a for (d) | Medium (schema lock reopening) | Medium (reopens a named lock) |
| Touch surface size | Short (docs/probe) to Small (estado line) | Medium-Large | Medium |
| Independent of closed arcs | Yes | Yes | Yes |
| Test/probe gate clarity | Very clear (b) — reuses existing fixtures directly | Clear but data-dependent | Clear, but explicitly not being reopened |

**Interpretation:** Validation Case is the only candidate of the three with any live, honest engineering work left at all — but that work is smaller and more narrowly IC-shaped than the vision doc's framing suggests, and its most valuable remaining piece (real battery/ESC test data) is outside an IC's authority entirely. H5 and G24-B both remain genuinely frozen with no new pressure from this cycle.

---

## 6. Recommendation

| Field | Answer |
|---|---|
| **Primary next block** | **Validation Case — option (b), probe/regression gate**, optionally paired with (a) a short documentation artifact. |
| **Rationale** | This is the smallest, lowest-risk, most honestly-scoped next step: it makes an already-true, already-tested-in-pieces property (the ★6 story resolves end-to-end exactly as documented) into one explicit, permanent, reviewable gate — protecting against future accidental regression without inventing new capability or touching any frozen/locked code path. Option (c) is real but not needed to close any gap (§3.9); option (d) is valuable but is data curation, not implementation, and shouldn't be dressed up as an IC. |
| **Deferred** | **H5** — no live blocker, no new pressure (§4.1). **G24-B** — still frozen, urgency lower than before G24C (§4.2). **Option (d) data sourcing** — explicit Engineer decision, separate from any IC, not scheduled here. |
| **Suggested IC sequence** | **1 cut only**: "Validation Case — ★6 Regression Gate" (probe + optional doc). No second cut proposed. |
| **Version note** | Docs/probe-only work is not version-bump-shaped at all in the usual sense — if bundled with anything else, `0.3.x` patch, not `0.4.0`. Recommendation only. |
| **Out of scope for the first IC** | `estado` surface changes (c), any battery/ESC data sourcing (d), any P2-1/P2-2/G24-A/C/D/Closure logic change, H5, G24-B. |

---

## 7. ★ Decisions for Engineer

**★1 — Primary next block:** ratify Validation Case option (b) [+ optional (a)]. *Recommended.*

**★2 — First-cut scope:** **(b) probe/regression gate**, optionally **(a)** a short paired doc. **(c)** `estado` surface: *not recommended* — real but not gap-closing. **(d)** data curation: *not an IC* — see ★3. *Recommended: (b), optionally + (a).*

**★3 — Data curation (d):** if Engineer wants to close the one genuine remaining §12.2 gap (real battery/ESC test data, §3.6/§3.10), that is a separate, Engineer-driven sourcing decision — not bundled into any IC from this investigation. *No recommendation on timing — Engineer's call whether/when to commission this.*

**★4 — H5:** continue defer, no schema-only spike. *Recommended.*

**★5 — G24-B:** continue freeze. *Recommended.*

**★6 — Version bump timing:** if the (b)[+a] cut ships, it's small enough to fold into whatever the *next* substantive checkpoint is (e.g., alongside a future H5 or data-curation cut) rather than warranting its own version bump — Engineer's call.

---

## 8. Suggested IC outline (bullets only — no code)

**IC "Validation Case — ★6 Regression Gate"**
- New `scripts/cli_probe_validation_case_op_dataset.py`: for each of OP-1, OP-2, OP-3 (the three non-fallback ★6 rows), bind the documented real motor+propeller+voltage combo and assert the full resolved tuple (`resolution_type`, `thrust_n`, `power_w`, `current_a`, `rpm`, `source_type`, `confidence`) matches the ★6 doc's own numbers exactly — plus one assertion for OP-0's `fallback_operating_point` shape.
- Optional: 1-2 new assertions in `tests/test_phase2_lookup_operating_point.py` locking the same tuple at the unit-test level (reuses existing fixtures, §3.11).
- Optional paired doc: a short `.jes/artifacts/validation_case_op_dataset_comparison.md` narrating the "real data → Jarvis result" match for each row plus the rating-vs-OP divergence, citing the same URLs the ★6 doc already carries — no new sourcing, purely a write-up of what's already true.
- Gate: probe green; zero `src/` changes; zero `library.py`/`resolve_operating_point`/P2-2 bridge diff (frozen per contract §3).
- Explicitly does not: touch `estado`, touch any frozen file, source new data, or reopen H5/G24-B.

---

## 9. CLI probe sketch for the recommended path

```text
1. For each of (emax_rs2205s_2300, hq_5045_bn, 16.0V) and
   (sunnysky_r2205_2500, gf_5045x3, 14.8V):
   - bind motor + propeller via real catalog_bind/component_writers path
   - assert resolution_type == exact_operating_point
   - assert thrust_n / power_w / current_a / rpm exactly match the ★6 doc's
     OP-2 / OP-3 rows
2. For emax_rs2205s_2300 with no propeller bound:
   - assert resolution_type == fallback_operating_point
   - assert thrust_n matches OP-0 (10.042), power_w/current_a/rpm are None
3. estado for each case shows the two honest lines (evidencia + OP eléctrico)
   matching the same numbers.
4. Regression: full suite + existing P2-1/P2-2 probes unaffected.
```

---

## 10. Explicit "do not implement yet" queue

- `estado` validation-summary surface (option c) — not gap-closing, deferred.
- Real battery/ESC data sourcing (option d) — Engineer data-curation decision, not an IC.
- H5 (ESC catalog) — deferred, no live blocker, no new pressure.
- G24-B (`_score_candidate` rewrite) — frozen, no new pressure, urgency reduced by G24C.
- Any change to `resolve_operating_point` matching rules, P2-2's `motor_power_w`/`motor_op_*` semantics, G24-A/C/D mechanisms, or Closure arc behavior — none found to need reopening.
- Version bump / tag creation — Engineer's call after ★ ratification.

---

**End of report.**
