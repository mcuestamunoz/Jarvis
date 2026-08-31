# Implementation Contract — Closure Policy + Propeller `sku_resolved` (IC 3 / Project Closure arc)

**Project:** Jarvis  
**Date:** 2026-08-31  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR CLAUDE

**Type:** Final cut of the Project Closure arc — **(A)** ratify assembly-ready policy in vision docs (family matrix, snapshots A/B, IC 1/2 decisions); **(B)** one-line display fix so catalog-bound propellers show `[sku]` instead of `(SKU sin resolver)`. **No readiness rollup changes.** **G24 out of scope.**

**Investigation:** [`.jes/artifacts/investigation_report_project_closure_assembly_ready.md`](investigation_report_project_closure_assembly_ready.md) — §6.1, §7, §9, §11 Cut 4, §12 probes #6–#7  
**Prior IC:** [`.jes/artifacts/implementation_contract_battery_catalog_bind_ux_g27.md`](implementation_contract_battery_catalog_bind_ux_g27.md) — **CLOSED** (`checkpoint-battery-catalog-bind-ux`)  
**Checkpoint base:** tag **`checkpoint-battery-catalog-bind-ux`** · commit `5581b51`  
**Product base:** **`v0.3.0`** (unchanged until Engineer decides bump)

**Arc position:** IC **3 of 3** (Option D). After PASS → Project Closure arc complete; optional checkpoint + version bump = Engineer decision.

**Workflow:** Claude implements **Pol-1 trace → Pol-2…Pol-6** + implementation report → Cursor review → CLI probe → commit/tag if Engineer asks.

---

## 0. Engineer ratification (locked)

| ★ | Decision |
|---|---|
| **★1 (arc)** | Option D sequence — IC 3 is the **final** implementation cut before arc closure. |
| **★3 (IC 1)** | Explicit `"no"` / `"ninguna"` → `requirements.defined=True` without fake `parsed_constraints`. |
| **★6 (investigation)** | Propeller `sku_resolved`: add `has_propeller` branch in `_bom_sku_resolved` — **display-only**, bundled here. |
| **★7 (investigation)** | Family policy matrix ratified — motors/propellers/battery **catalog-evidence-strong optional**; ESC/frame/FC/sensors **freeform_ok only**. Battery bind is **not** required for ASSEMBLY READY in snapshot A. |
| **★8 (investigation)** | `ACCEPTED_WARNING_TYPES` unchanged — single type `CATALOG-GAP-DEMOTED-POST-PASS`, catalog/propulsion only. |
| **★9 (investigation)** | G24 deferred — not a closure prerequisite. |
| **IC 2 ratification** | Battery bind must **not** re-call `set_motor_component` (OP exact→fallback downgrade risk) — document as ratified UX, do not change. |

**IC 3 gate (Engineer, locked):**

> **(A)** Vision doc reflects ratified closure policy (snapshots A/B, family matrix, IC 1/2 semantics). **(B)** Catalog-bound propeller in BOM display shows `[sku]` with `sku_resolved=True`; motor/battery behavior unchanged. **Zero** readiness rollup / verdict / P2-1 / physics changes.

**Philosophy locks (inherit from closure arc):**

- **Documentation ≠ behavior change** — IC 3 policy sync must not alter `build_engineering_readiness` logic unless a bug is found outside this contract (stop and escalate).
- **Display-only fix for propeller** — `_bom_sku_resolved` / `format_bom_lines` only; no wiring `catalog_bound` into subsystem verdicts.
- **Do not weaken tests** — disclose any assertion change explicitly.

---

## 1. Problem / intent

### 1.1 Track A — Closure policy (documentation)

The investigation ratified **two target snapshots** for "assembly ready" semantics:

| Snapshot | Name | Catalog requirement |
|---|---|---|
| **A** | Freeform-tolerant v1 | All 9 subsystems PASS (or accepted WARNING); components may be honestly freeform; battery/motor/propeller **need not** be catalog-bound |
| **B** | Catalog-evidence-strong | Same rollup rules; motor + propeller + battery catalog-bound where library supports it; ESC/FC/sensors/frame remain freeform (no catalog exists) |

These decisions were implemented across IC 1/2 but **not yet synced** into `docs/ENGINEERING_READINESS_VISION.md` per that doc's §10 sync protocol. IC 3 closes the documentation gap so the arc has a single product-level contract for Project Closure.

**Also document (ratified, not new behavior):**

- S0→S1→S2 transition model (investigation §10): BOM completion and requirements closure are **orthogonal** levers.
- IC 1 ★3(b): explicit no-restrictions satisfies requirements.
- IC 2 ★7: battery catalog bind improves energy evidence but is **optional** for snapshot A readiness.
- IC 2: no `set_motor_component` after battery bind.
- G24, H5 ESC catalog, frame SKU catalog — explicitly deferred.

### 1.2 Track B — Propeller `sku_resolved` bug (display)

`_bom_sku_resolved` (`project_closure.py:204-228`) re-checks motor and battery SKUs via `has_motor` / `has_battery` but **omits** `has_propeller`:

```python
if family == "motor":
    return default_library.has_motor(sku)
if family == "battery":
    return default_library.has_battery(sku)
return False  # ← propeller falls through here
```

**Live effect:** bound propeller `hq_5045_bn` displays `✓ propellers: hq_5045_bn (SKU sin resolver)` even though the SKU resolves in `library/helices/_datos.json`.

**Fix (★6):**

```python
if family == "propeller":
    return default_library.has_propeller(sku)
```

**Non-effects (confirmed in investigation):** `sku_resolved` is BOM-display-only; does not affect gaps, subsystem verdicts, P2-1, or calc/sim.

---

## 2. Scope boxes

### 2.1 In scope

| ID | Deliverable |
|---|---|
| **Pol-1** | Bat-0 / Pol-0 trace: confirm `_bom_sku_resolved` line numbers; document in implementation report |
| **Pol-2** | `docs/ENGINEERING_READINESS_VISION.md` — new §11 (or equivalent) **Project Closure / Assembly Ready v1** with family matrix, snapshots A/B, IC 1/2 ratifications, S0→S1→S2, deferred items |
| **Pol-3** | `project_closure.py` — propeller branch in `_bom_sku_resolved`; update Impl D ★2 comment to mention propeller |
| **Pol-4** | Tests — propeller bound → `sku_resolved=True`, `[sku]` in `format_bom_lines`; regression: motor/battery/frankenstein scenarios unchanged |
| **Pol-5** | CLI probe `scripts/cli_probe_closure_policy_propeller_sku.py` — investigation §12 probes #6–#7 adapted |
| **Pol-6** | `docs/IMPLEMENTATION_TASKS.md` top section + `.jes/state/engineering_state.json` per vision sync protocol §10 steps 2–3 |

### 2.2 Out of scope (explicit)

- G24 DSE apply-by-index / scoring
- Changes to `build_engineering_readiness`, `_derive_overall`, gap builders, `ACCEPTED_WARNING_TYPES`
- Wiring `catalog_bound` / `sku_resolved` into subsystem verdicts
- P2-1 / `resolve_operating_point` / motor writer after battery bind (already ratified in IC 2 — do not touch)
- Battery/propeller catalog expansion, H5 ESC catalog, frame SKU catalog
- Iterate-wizard post-bind integration, Option B energy filter
- Version bump in `pyproject.toml` — Engineer call after arc closure
- `ARCHITECTURE.md` / `docs/system_map/*` — only after code lands (vision sync protocol step 4; optional follow-up)

---

## 3. Implementation slices

### Pol-1 — Trace (implementation report)

Document in report:

- `_bom_sku_resolved` current branches and the propeller omission
- Confirmation that `format_bom_lines` → `_bom_identity_suffix` is the only user-visible path affected
- `git diff --stat` must not include `engineering_readiness.py`, `library.py`, OP resolver, IC 1/2 source except comment-only if any

### Pol-2 — Vision doc sync (`docs/ENGINEERING_READINESS_VISION.md`)

Add section **§11 Project Closure — Assembly Ready v1** (title may vary; content must include):

1. **Rollup rule (as-implemented reference)** — pointer to `engineering_readiness.py` `_derive_overall`; 9 subsystems; zero HIGH gaps; accepted WARNING types unchanged (★8).
2. **Snapshots A / B** — condensed from investigation §9 (example `estado` blocks optional; criteria table required).
3. **Family policy matrix** — from investigation §7 / ★7 (motors, propellers, battery: catalog-strong optional; esc, frame, flight_controller, sensors: freeform only).
4. **Requirements semantics (IC 1)** — ★3(b) explicit none; numeric constraints → honest GAP-REQUIREMENTS-UNMET when unachievable.
5. **Energy / battery (IC 2)** — catalog bind = evidence-strong; not required for snapshot A; G27 hardened; no motor re-call after battery bind.
6. **S0→S1→S2** — investigation §10 one-paragraph summary.
7. **Deferred** — G24, H5, frame SKU, Conversation Engine.

Update doc header date/status line to note IC 3 policy sync (ERF-1/2 remain ✅).

**Do not** claim unimplemented behavior as shipped — distinguish "ratified product contract" from "code changed in IC 3".

### Pol-3 — Propeller resolve (`project_closure.py`)

- Add `if family == "propeller": return default_library.has_propeller(sku)` before final `return False`.
- Extend docstring comment: propeller branch added post-v0.3.0 propeller-bind UX (IC 3).
- **No other edits** in this file unless required for tests.

### Pol-4 — Tests

**Preferred:** extend `tests/test_impl_d_sku_bom.py` (same module as Impl D SKU tests).

Minimum new tests (names indicative):

1. `test_bound_propeller_entry_has_resolved_catalog_ref_and_quantity` — `bind_propeller_from_catalog("hq_5045_bn")` → `sku_resolved is True`, `format_bom_lines` contains `[hq_5045_bn]`, **no** `(SKU sin resolver)`.
2. `test_bound_propeller_sku_removed_from_library_resolves_false` — mirror motor Scenario C if feasible with monkeypatch or invalid sku after bind clear.
3. `test_motor_battery_sku_resolved_regression_unchanged` — smoke: existing motor/battery tests still pass (no weakened assertions).

Optional: `tests/test_closure_policy_docs.py` — lightweight import/check that vision doc contains key anchors (`Snapshot A`, `Snapshot B`, `freeform_ok`) if team wants doc drift guard; **not required** if Pol-2 is thorough.

**Zero weakened tests** in `test_impl_d_sku_bom.py` / `test_engineering_readiness_*`.

### Pol-5 — CLI probe (`scripts/cli_probe_closure_policy_propeller_sku.py`)

Deterministic probe; target **4/4** or **5/5 PASS**:

| Step | Action | Pass criterion |
|---|---|---|
| 1 | Build minimal state: motor + propeller catalog-bound (`hq_5045_bn`) | `build_component_bom` → propellers entry `sku_resolved is True` |
| 2 | `format_bom_lines` on same state | Line contains `[hq_5045_bn]`; no `(SKU sin resolver)` on propellers |
| 3 | Snapshot A shape (freeform battery, explicit-no requirements, other subsystems crafted PASS) | `build_engineering_readiness` → `ASSEMBLY READY` (reuse Fixture 2 pattern / IC 1 helper) |
| 4 | Snapshot B shape (motor + propeller + battery all bound, freeform esc/frame/FC/sensors) | Readiness summary shows `[sku]` on all three catalog families; propeller line not marked unresolved |
| 5 | (Optional) Load Fixture 1 propulsion-complete project if on disk | Propeller line shows `[sku]` not `(SKU sin resolver)` |

No wizard turns required if probe builds state programmatically (same discipline as other closure probes).

### Pol-6 — Queue / state sync

After implementation (before review):

- `docs/IMPLEMENTATION_TASKS.md` — mark IC 3 in progress → complete after review; IC 2 checkpoint line updated with `5581b51` / `checkpoint-battery-catalog-bind-ux`.
- `.jes/state/engineering_state.json` — `cycle_intent` → IC 3 implementation; update after PASS.

---

## 4. Files — expected touch set

| File | Change |
|---|---|
| `src/jarvis/core/project_closure.py` | Pol-3 only (`_bom_sku_resolved` + comment) |
| `docs/ENGINEERING_READINESS_VISION.md` | Pol-2 |
| `tests/test_impl_d_sku_bom.py` (or `tests/test_closure_policy_propeller_sku.py`) | Pol-4 |
| `scripts/cli_probe_closure_policy_propeller_sku.py` | Pol-5 (new) |
| `docs/IMPLEMENTATION_TASKS.md` | Pol-6 |
| `.jes/state/engineering_state.json` | Pol-6 |

**Must NOT change:**

- `src/jarvis/core/engineering_readiness.py` (rollup / verdicts)
- `library.py`, `resolve_operating_point`, `component_writers`, `catalog_bind.py`
- `orchestrator.py`, `battery_catalog_assist.py`, `semantic_intent_adapter.py` (IC 2)
- `state_schema.py`, `param_definition_session.py` (IC 1)
- G24 DSE modules
- `pyproject.toml` version

---

## 5. Regression anchors

Full suite must stay green. These files' **assertions** must remain valid (add tests, do not weaken):

- `tests/test_impl_d_sku_bom.py` — motor/battery frankenstein + Scenario C
- `tests/test_requirements_closure.py` — IC 1
- `tests/test_battery_catalog_bind_ux.py` — IC 2 incl. OP downgrade test
- `tests/test_propeller_catalog_bind_ux.py`, `tests/test_phase2_lookup_operating_point.py` — P2-1
- `tests/test_engineering_readiness_*` — rollup unchanged

---

## 6. Acceptance (Cursor review)

**PASS** if:

- Pol-1 trace in implementation report with file:line
- Vision doc §11 (or equivalent) contains snapshots A/B, family matrix, IC 1/2 ratifications, deferred list
- Propeller bound → `sku_resolved=True`, `[sku]` in BOM line; live bug from investigation §6.1 fixed
- Probe target met; new tests green; full suite green
- `git diff` confirms no engineering_readiness / OP / IC 1–2 logic changes
- No weakened tests without disclosure

**FAIL** if:

- Readiness rollup or gap logic changed without contract
- Propeller fix alters verdicts or P2-1 behavior
- Vision doc claims behavior not implemented or contradicts IC 1/2
- Fake PASS via invented SKUs or patched state that bypasses real predicates

---

## 7. Queue after IC 3

```text
IC 3 PASS + probe green
  ↓
Cursor: implementation review
  ↓
Engineer: optional checkpoint (e.g. checkpoint-closure-policy) + version bump decision
  ↓
Project Closure arc COMPLETE
```

**Suggested checkpoint name (Engineer optional):** `checkpoint-closure-policy`  
**Not in scope of this contract:** tag creation, push, `v0.3.x` bump.

---

**End of contract.**
