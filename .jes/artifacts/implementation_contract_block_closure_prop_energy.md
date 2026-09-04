# Implementation Contract — Block Closure B-PROP-ENERGY

**Project:** Jarvis  
**Date:** 2026-09-01  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** RATIFIED ★1–★6 (2026-09-01). **You are Claude Code.** Implement this file only. Cursor reviews; Cursor does not implement.

**Type:** Derivable rollup + CLI claim + battery re-bind fix. **Not** new physics. **Not** ERF §11 rewrite. **Not** a `BLOCK_STATUS` subsystem. **Not** Catalog Foundation / H5.

**Evidence:**
- [investigation_report_post_v034_block_closure.md](investigation_report_post_v034_block_closure.md)
- [investigation_review_post_v034_block_closure.md](investigation_review_post_v034_block_closure.md) — **PASS WITH NOTES**
- [engineer_ratification_block_closure_prop_energy.md](engineer_ratification_block_closure_prop_energy.md) — ★1–★6 locked

**Checkpoint base:** tag **`v0.3.5`** / `fc46938` plus current tree (P27-B / Option A / CLI feasibility semantics already shipped). Investigation citations are vs `v0.3.4`; do not revert later slices.

---

## 0. You (Claude)

- Edit only files listed in §5.
- Do **not** change `_derive_overall`, `ASSEMBLY_READY` / `NOT_ASSEMBLY_READY` conjunction, or the eight `validated = ctx.sim_status == "pass"` assignments in `engineering_readiness.py`.
- Do **not** add a `BLOCK_STATUS` enum, a tenth `SUBSYSTEM_KEYS` entry, or a new domain module.
- Do **not** change `resolve_operating_point`, HOLD rows, `fallback_only`, voltage epsilon, catalog JSON, P26 / P27-A, DSE scoring.
- Do **not** invent `motor_power_w`, hover watts, ESC η, pack R, minutes.
- Do **not** reopen CLI feasibility locked copy.
- Do **not** bump `pyproject.toml` unless the Engineer asks after review.
- Full suite green. Zero weakened tests. G27 battery tests stay green.

---

## 1. Intent

After a real Combo A walk (Gate A compatible), `estado` must answer **two different questions**:

```text
PROJECT STATUS: ASSEMBLY READY | NOT ASSEMBLY READY     # unchanged 9-way rollup
BLOQUE PROPULSIÓN/ENERGÍA: CERRADO | NO CERRADO …       # new, block-scoped
```

A project may be **block-closed** and **not** assembly-ready (frame/FC/structure HIGH or incomplete). That dual is the point of Finding B-3.

A project that is assembly-ready **must not** be the only way to learn the stack is closed.

Incompatible Gate A (`motor_count=4`, same SKUs, discharge exceeded): block **NO CERRADO**, overall **NOT ASSEMBLY READY**. Honest refuse. No silent pass.

---

## 2. Prerequisite — battery SKU re-bind (Gate E Path 3)

**Must land in this IC, before or with the rollup — not after.**

### Bug

On a project whose battery is **already catalog-bound**, these phrases (and equivalents that name a live library SKU) currently destroy `catalog_ref` and write a freeform Wh scraped from the SKU digits (G27-class `6` from `6s`):

```text
definir bateria lipo_6s_10000mah
cambia la bateria a lipo_6s_10000mah
```

Live path is `define_missing_params` / iterate numeric apply (`parse_floats_from_input` in `param_definition_session.py` ~1040). G27 hardened the **wizard / “LiPo 6S 10000mAh”** iterate path. This is a **distinct** path. Do not reopen G27; cover this path.

### Required behavior

If the user text contains a **live library battery SKU** (`ComponentLibrary.list_batteries()` / `get_battery` name, e.g. `lipo_6s_10000mah`):

1. Call existing `bind_battery_from_catalog(sku)` + `set_battery_component` (same chain as `_apply_component_battery_catalog_pick`).
2. Do **not** write `battery_capacity_wh` from `parse_floats_from_input` / `_make_battery_spec(n)`.
3. Result: `catalog_ref.family == "battery"`, `catalog_ref.sku` is the named SKU, Wh is catalog `energy_wh` (for `lipo_6s_10000mah` that is **not** 6.0).

Reuse `match_suggestion_by_input` / `list_batteries()` if that already matches SKU tokens. **No second binder.** **No new catalog family.**

Trace the live `handle_user_text` route (IDLE `define_params` vs `iterate` vs open `ParamDefinitionSession.answer`) and patch **that** seam. One intercept is enough if it runs before the float scrape.

Bare `"definir bateria"` (no SKU) keeps today’s wizard / catalog-offer behavior.

`"aumentar bateria a LiPo 6S 10000mAh"` (G27) must remain ~222 Wh, never 6.0.

---

## 3. Rollup — `derive_prop_energy_block_closure`

Add a **pure** function. Preferred home: `project_closure.py` (derivation over existing signals). Do **not** put new engineering physics in `adapters/cli/main.py`.

You may call `build_engineering_readiness` and `evaluate_electrical_compatibility` from it (already pure). Do not duplicate their arithmetic.

### 3.1 Return shape (plain dict or dataclass — not a new subsystem)

```text
block_id: "B-PROP-ENERGY"
status: "closed" | "not_closed"
evidence_tier: "manufacturer_test" | "fallback" | "legacy_estimate" | "none"
reasons: list[str]     # empty iff closed; short machine-stable tokens ok
facts: dict            # the inputs you actually used (verdicts + check outcomes + sim_status)
```

### 3.2 `closed` iff all of:

| # | Condition |
|---|---|
| 1 | `subsystems["propulsion"].verdict == "PASS"` |
| 2 | `subsystems["energy"].verdict == "PASS"` |
| 3 | `subsystems["electronics"].verdict == "PASS"` |
| 4 | `electrical_compatibility.battery_discharge == "within_limit"` |
| 5 | `electrical_compatibility.esc_vs_motor == "compatible"` |
| 6 | `electrical_compatibility.prop_motor == "compatible"` |
| 7 | `electrical_compatibility.esc_presence == "defined"` (freeform ESC **allowed** — ★3 / Gate D #1) |
| 8 | latest `simulation.status == "pass"` |
| 9 | `motors`, `propellers`, `battery` each have `catalog_ref` with the right family |

**Forbidden as ESC proof:** `subsystems["electronics"].evidence.validated` (Finding B-2 — that flag is global sim PASS). You may read it for diagnostics; it must not be sufficient for `closed`.

ESC `sku_resolved` is **not** required (no ESC catalog).

### 3.3 `evidence_tier` (★6)

Read existing propulsion resolution (`resolution_type` / `source_type` already on startup context / project — same fields CLI feasibility uses). Do not call the resolver with new voltage rules.

| Resolution | `evidence_tier` |
|---|---|
| `exact_operating_point` and `source_type == "manufacturer_test"` | `manufacturer_test` |
| `fallback_operating_point` | `fallback` |
| other / missing | `legacy_estimate` or `none` as honest |

`status == "closed"` **is allowed** at `fallback`. Copy must not say manufacturer_test in that case.

If checks fail, `status` is `not_closed` even if the OP is `manufacturer_test`.

### 3.4 Wire-up

`build_startup_context` already builds readiness. Attach the dict on the same context (e.g. `ctx["prop_energy_block_closure"]`). Do not persist a new file in the workspace unless an existing snapshot already stores readiness (prefer ephemeral ctx only).

---

## 4. Locked CLI copy — `adapters/cli/main.py`

Render **one** block line in `estado` / `render_startup_context`, **near** `_render_readiness_block`, **after** the nine subsystem lines, **not** replacing `PROJECT STATUS`.

### Closed + manufacturer_test

```text
BLOQUE PROPULSIÓN/ENERGÍA: CERRADO — evidencia manufacturer_test (punto de operación coincidente)
```

### Closed + fallback

```text
BLOQUE PROPULSIÓN/ENERGÍA: CERRADO — evidencia fallback (combo exacto no usable; no es manufacturer_test)
```

### Closed + legacy / none (if 3.2 can still hold)

```text
BLOQUE PROPULSIÓN/ENERGÍA: CERRADO — evidencia débil (no hay punto de operación de catálogo)
```

Use this only if 3.2 is actually true. If it cannot be true without an OP, then `not_closed` instead — do not freelance a fake closed.

### Not closed — discharge (Gate A incompatible)

```text
BLOQUE PROPULSIÓN/ENERGÍA: NO CERRADO — descarga de batería excedida
```

### Not closed — other

```text
BLOQUE PROPULSIÓN/ENERGÍA: NO CERRADO — el stack de propulsión/energía no está cerrado
```

You may append a short fact from `reasons` (one clause). **Forbidden phrases:** `ASSEMBLY READY` as a synonym of this line, `Diseño validado`, `autonomía real`, `fuera del rango del dataset`, inventing minutes.

Continuity situation strings from the CLI feasibility IC stay as they are. Do not retcon them into this rollup.

---

## 5. Files

| File | Role |
|---|---|
| `src/jarvis/core/project_closure.py` | `derive_prop_energy_block_closure` |
| `src/jarvis/core/orchestrator.py` | Attach derivation on startup context; IDLE intercept for battery SKU if that is the live path |
| `src/jarvis/core/param_definition_session.py` | SKU bind **before** `parse_floats_from_input` when that is the live path |
| `src/jarvis/core/battery_catalog_assist.py` | Optional: SKU token match helper reused by the intercept — not a new catalog |
| `src/jarvis/core/intent_resolver.py` | Only if the numeric DEFINE_PARAMS guard is part of the live bug; do not loosen `"definir torque a 50 Nm"` → iterate |
| `src/jarvis/actions/iterate.py` | Only if the live phrase is IterateAction apply; then bind SKU instead of float-scrape **for battery SKU tokens only** |
| `src/jarvis/adapters/cli/main.py` | Locked line in `estado` |
| `tests/test_block_closure_prop_energy.py` | **New** — Gate A compatible / incompatible / dual vs `ASSEMBLY_READY` / battery re-bind |
| `tests/test_battery_catalog_bind_ux.py` | Must stay green (G27) |
| `scripts/cli_probe_block_closure_prop_energy.py` | Gate A + `estado` line + re-bind phrase |
| `docs/IMPLEMENTATION_TASKS.md` | In progress / done when you finish |
| `.jes/state/engineering_state.json` | Sync |

**Not touched:** `engineering_readiness.py` verdict/`_derive_overall`/`validated=` copies, `electrical_compatibility.py` formulas, `library/` JSON, `design_explorer.py`, `resolve_operating_point*`.

If attaching the dict is mechanically easier as an **optional field** on `EngineeringReadinessResult` with a default of `None` and `_derive_overall` ignored, **stop and ask** — that is a core-contract change this IC did not authorize. Prefer ctx-only.

---

## 6. Tests (mandatory)

### 6.1 Gate A compatible → block closed, tier manufacturer_test

Drive the **real orchestrator** (no LLM, no hand-built `simulation.status`):

```text
sunnysky_r2205_2500 + gf_5045x3 + lipo_4s_1500mah + freeform ESC 60A
motor_count=2
calcular + simular
```

Assert:

- `derive_prop_energy_block_closure(...)["status"] == "closed"`
- `evidence_tier == "manufacturer_test"`
- rendered `estado` contains the locked manufacturer_test closed line
- rendered `estado` still has `PROJECT STATUS:` from `_derive_overall` (value whatever the 9-way says — do not force it)

### 6.2 Dual: block closed ≠ assembly-ready

Same propulsion/energy/electronics stack as 6.1 but **omit** frame and/or flight controller so overall is `NOT_ASSEMBLY_READY` if that is what the 9-way already does.

Assert: block `closed` **and** `overall == "NOT_ASSEMBLY_READY"`. If omitting frame still yields `ASSEMBLY_READY` in this codebase, assert the dual on another honest incomplete subsystem (structure/control) — do not fake a HIGH gap.

### 6.3 Gate A incompatible → not closed

Same SKUs, `motor_count=4` (discharge exceeded, `i_total` 160 vs limit 150).

Assert:

- sim may still `pass` (thrust) — do not “fix” that
- block `status == "not_closed"`
- copy contains `descarga de batería excedida`
- overall `NOT_ASSEMBLY_READY`

### 6.4 Battery re-bind

Start from a catalog-bound 4S (`lipo_4s_1500mah` or `lipo_4s_10000mah`). `handle_user_text` with RefuseLLM:

```text
definir bateria lipo_6s_10000mah
```

and a second case:

```text
cambia la bateria a lipo_6s_10000mah
```

Assert: `catalog_ref.sku == "lipo_6s_10000mah"`, `battery_capacity_wh` is catalog energy (**≠ 6.0**).

### 6.5 G27 unchanged

Existing `tests/test_battery_catalog_bind_ux.py` green.

### 6.6 Unbound / incomplete stack is not closed

Motor catalog-bound without propeller `catalog_ref` (or missing electrical checks) → `not_closed`. Do not declare closed on CLI feasibility’s emax+HQ fixture if `prop_motor` is not `compatible` or energy is not PASS-for-the-right-reasons — **follow 3.2 literally**. If that fixture is `not_closed`, that is correct (CLI IC already covers its claim language).

Optional probe: `scripts/cli_probe_block_closure_prop_energy.py` (compatible, incompatible, re-bind, dual). Not a substitute for 6.1–6.4.

---

## 7. Non-goals

```text
engineering_readiness._derive_overall / ASSEMBLY_READY formula
rewriting SubsystemEvidence.validated (Finding B-2 field itself)
BLOCK_STATUS enum / tenth subsystem
H5 ESC catalog / EscSpec / sku_resolved on ESC
Catalog Foundation / extra motor-prop-battery SKUs
Gate E Path 4 frankenstein on define_missing_params thrust mutation
GAP-MOTOR-CATALOG-UNRESOLVED rename
C-081 / C-108 / G24-B / Option B ERF energy evidence
P26 / P27-A / HD-001/002/003
CLI feasibility locked strings
Invented motor_power_w / hover minutes
Persisted fidelity ladder
```

---

## 8. Acceptance (reviewer)

- 6.1–6.5 green on reviewer re-run.
- `git` / inspection: no `_derive_overall` change; no new subsystem key.
- Combo A L1 / Option A ESTIMATIVO / CLI feasibility tests still green.
- No version bump, no checkpoint.

---

## 9. After you finish

Write `implementation_report_block_closure_prop_energy.md` (files, tests run, `ASSEMBLY_READY` unchanged, re-bind not 6.0 Wh). Cursor reviews against **this** IC.

**After a PASS review — Engineer CLI walk (required, not optional).**  
Tests/probe close the *contract*. They do not close the *product*. Jarvis is one interconnected surface (Continuity + ERF `ASSEMBLY_READY` + this block line + catalog bind + `calcular`/`simular`). The last “optional” walk is what found CLI feasibility. Do a Combo A / `PRODUCT_SCOPE.md` walk on the live CLI before calling this arc done. If that walk lies, that is the next investigation — not a silent stop.
