# Implementation Contract — Physical Component Catalog v1 — Impl B (Bind)

**Project:** Jarvis  
**Date:** 2026-08-12  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** READY FOR ENGINEER → send to Claude  

**Type:** Product behavior — Catalog **Bind** (SKU → state → params → calc).  

**Design authority (mandatory):** [`docs/PHYSICAL_COMPONENT_CATALOG_V1.md`](../../docs/PHYSICAL_COMPONENT_CATALOG_V1.md) — DESIGN CLOSED (locks **1A, 2A, 4A** especially).  

**Checkpoint base:** tag `checkpoint-catalog-impl-a` · commit Foundation PASS  

**Depends on:** Impl A (`ComponentLibrary` 3 families, `ComponentSpec.catalog_ref` schema exists unused).  

**Explicitly deferred:** Impl C (Catalog DSE) · Impl D (Create→BOM) · H5/C-081 · ESC catalog · material ES/EN micro-fix · Continuity battery/prop gap redesign · Conversation Engine / Step D · mandatory `operating_points` consumers  

**Workflow:** Claude implements + tests + report → Engineer forwards → Cursor reviews → **CLI field probe (Engineer)** before commit. **No commit/push unless Engineer asks.**

---

## 0. Intent — the engineering chain

Impl A proved catalog **infrastructure**. Impl B must prove catalog **causality**:

```text
CATALOG SKU
    ↓ user confirm / assisted pick
ComponentSpec.catalog_ref = {family, sku}
    ↓ writers (MIRRORED PARAM CONTRACT)
current_parameters
    ├── motor mass (SKU-bound only)
    ├── battery mass + energy (SKU-bound only)
    └── thrust / kv / other projected props
    ↓
CalculationEngine → FeasibilitySimulator
```

**Unbound path must stay bit-compatible with today’s physics** (`catalog_ref is None` → legacy behavior).

Engineer’s three first-class requirements (non-negotiable):

1. **SKU must not disappear** after pick (fix today’s discard).  
2. **Continuous DSE / numeric diverge must not leave a lying SKU label** — clear `catalog_ref`.  
3. **Motor mass must demonstrate physical causality** (N motors × SKU mass → total_mass → weight → required thrust → margin).

---

## 1. Architectural authority

| Rule | Impl B |
|---|---|
| Catalog owns SKU physical fields | Read via `ComponentLibrary` only |
| Bind writes identity + projection | Only on **user-confirmed** catalog pick / DEFINE_MISSING catalog confirm |
| Calc still reads `current_parameters` | May **add** reading of mirrored mass params; must not import catalog in calc |
| LLM never invents / fuzzy-matches SKU | Forbidden |
| Unbound motors/batteries | Unchanged numeric behavior |

---

## 2. IN SCOPE

### 2.1 Identity write (both pick paths)

**A. Iterate assisted motor pick** — `iterate_interactive_session._handle_motor_suggestion_selection`  
Today: copies `thrust_n` + `weight_g` only; narrates SKU name.  
**Required:** set:

```text
catalog_ref = CatalogRef(family="motor", sku=<library key>)
```

plus project at least: `thrust_n`, `weight_g`, `kv_rating`, `power_w`/`max_watts` as available from the catalog suggestion / `MotorSpec` — same richness spirit as DEFINE_MISSING’s `_make_motor_spec_from_catalog`, **and** durable `catalog_ref` (not only `ComponentSpec.name`).

**B. DEFINE_MISSING catalog motor pick** — `_make_motor_spec_from_catalog`  
Today: richer props + `name=sku` but **no** `catalog_ref`.  
**Required:** set `catalog_ref` similarly. Prefer one shared helper (e.g. `bind_motor_from_catalog(sku|MotorSpec|suggestion) -> ComponentSpec`) used by both paths — avoid dual divergence.

**C. Battery catalog bind**  
If there is already a user-facing battery catalog pick path, wire it. If **none** exists yet, Impl B must still:

1. Provide a **deterministic bind helper** `bind_battery_from_catalog(sku) -> ComponentSpec` with `catalog_ref` + projected Wh/mass/cells, and  
2. Call it from the **smallest existing battery declaration/write path** that can accept a catalog SKU without inventing Continuity UX — OR expose bind only via a clear orchestrator/test-callable API used by tests.

Prefer: if no CLI pick exists for batteries, implement helper + unit/integration tests that apply bind through `set_battery_component`; do **not** invent a Conversation Engine. Document in report which battery entry point was wired (or “helper + tests only”).

**D. Propeller bind**  
Same rule as battery: helper + wire if an existing pick exists; otherwise helper + tests. Propeller mass in calc is **optional** in B if not already mirrored — do not block B on prop mass if motors+batteries prove the chain. If prop mass is easy via a new mirrored param and SKU-bound gate, include it; else defer with explicit note.

### 2.2 Writers / mirrored params

Extend MIRRORED PARAM CONTRACT as needed:

- When motors are SKU-bound: ensure `weight_g` (or fleet mass) is available for calc.  
  Recommended mirrored param: `motor_mass_kg` = `(weight_g/1000) * motor_count` when `catalog_ref.family=="motor"`, cleared/not written when unbound.  
- When battery is SKU-bound: `battery_capacity_wh` from SKU `energy_wh`; `battery_mass_kg` from SKU `mass_g/1000` — **override** `estimate_battery_mass_kg(150 Wh/kg)`.  
- When unbound: keep today’s `estimate_battery_mass_kg` path.

Do not break MIRRORED PARAM discipline (writers remain the sole write points).

### 2.3 CalculationEngine — SKU-bound mass causality

Today: `total_mass = payload + structure + battery_mass_kg` (no motor mass).

**Required:**

```text
if motor_mass_kg present in parameters (written only for SKU-bound motors):
    include in total_mass
else:
    identical to today (no motor mass)
```

Demonstrate in tests:

```text
4 × motor SKU (known weight_g)
  → +4*(weight_g/1000) kg
  → higher total_mass_kg
  → higher weight_n
  → higher required_thrust_n
  → lower safety_margin (all else equal)
```

Unbound motor project fixtures must keep **unchanged** expected mass/thrust/margin numbers.

### 2.4 Dual-truth: clear `catalog_ref` on diverge

When a continuous / free-numeric mutation changes a SKU-projected physical number away from the catalog value (especially `per_motor_max_thrust_n` / component `thrust_n` after DSE apply or iterate set), **clear `catalog_ref`** on that component (and stop treating mass as SKU-authoritative if the bind contract ties mass to identity).

Minimum covered paths:

1. DSE `apply` that scales/changes thrust (or motor-related mirrored params) on a previously SKU-bound motor component.  
2. Iterate / mutation that sets a new explicit thrust (or equivalent) different from catalog `thrust_n`.

Rule (Design §8): **forbid silent overwrite** — never keep `catalog_ref` pointing at SKU X while numbers no longer match X.

Battery: if user/DSE changes `battery_capacity_wh` away from bound SKU energy, clear battery `catalog_ref` and revert mass derivation to heuristic unless a new bind occurs.

Exact equality tolerance: document a small float epsilon if needed; do not “almost match” with fuzzy SKU retention.

### 2.5 Persistence

`catalog_ref` must survive save/load of project state (round-trip `ProjectState` / workspace save). Add a test.

### 2.6 BOM / Continuity (minimal)

Light touch only: where BOM or Continuity already lists components, prefer showing SKU when `catalog_ref` is set (e.g. evidence line or component label). **Do not** redesign Continuity ranking or implement H5. Skip Continuity text changes if they require non-trivial UX redesign — then note “deferred labeling” in report; identity persistence + calc causality remain mandatory.

---

## 3. OUT OF SCOPE (hard)

| Forbidden | Why |
|---|---|
| Catalog-aware DSE candidate generation | Impl C |
| Create→BOM / SKU BOM architecture | Impl D |
| H5 / C-081 | deferred |
| Material ES/EN fix | separate micro-fix |
| Silent NL→SKU fuzzy match | authority |
| Populating `catalog_ref` without user confirm / explicit bind API | authority |
| Changing unbound project physics | lock 2A |
| Second JSON reader | forever |
| Mandatory operating_points interpolation | later |

---

## 4. Tests (minimum)

### Identity

1. Iterate motor catalog pick → `components["motors"].catalog_ref.sku` set and persists after confirm path used in session.  
2. DEFINE_MISSING catalog pick → `catalog_ref` set.  
3. Save/load project → `catalog_ref` survives.  
4. Regression: unbound declare path → `catalog_ref is None`.

### Mass causality (motors)

5. Bind known motor SKU with `weight_g=W`, `motor_count=N` → `total_mass` increases by ~`N*W/1000` vs identical unbound baseline.  
6. Unbound motor fixture mass/thrust expectations **unchanged**.

### Battery

7. Bind battery SKU → `battery_capacity_wh` and `battery_mass_kg` match SKU (not 150 Wh/kg heuristic).  
8. Unbound battery → still heuristic mass from Wh.

### Dual-truth / invalidate

9. SKU-bound motor + DSE/apply or numeric thrust change away from catalog → `catalog_ref is None` afterward.  
10. After clear, motor mass must not keep claiming SKU authority (mass mirror cleared or falls back per chosen rule — document and test).

### Regressions

11. FN-022…026 / H1–H4 subset green.  
12. Existing library Foundation tests green.  
13. Full suite green (or pre-existing failures named).

---

## 5. CLI field probe (Engineer — after Cursor PASS)

Not Claude’s job to run interactive CLI, but report must list the intended probe for Engineer:

```text
1) Closed architecture project
2) Assisted / DEFINE_MISSING catalog motor pick (or documented bind entry)
3) estado / inspect → catalog_ref present (or Continuity/BOM shows SKU)
4) calculate/simulate → mass/margin moved vs pre-bind baseline
5) explora / apply continuous thrust change → catalog_ref cleared (no lying SKU)
```

Cursor review may be **PASS WITH NOTES** until Engineer confirms CLI probe; coding acceptance still requires automated tests green.

---

## 6. Implementation Report (required)

`.jes/artifacts/implementation_report_catalog_bind_v1.md`

```markdown
# Implementation Report — Catalog Bind v1 (Impl B)

## Summary
## Bind entry points wired (iterate / DEFINE_MISSING / battery / prop)
## Shared bind helper(s)
## Writers / mirrored params
## CalculationEngine mass causality
## catalog_ref invalidation rules + call sites
## Persistence
## BOM/Continuity touch (or deferred)
## Files changed
## Tests run
## Regression results
## CLI probe script for Engineer
## Explicitly deferred (C/D/H5/material)
## Risks
```

---

## 7. Acceptance criteria (Cursor PASS)

1. SKU identity persists via `catalog_ref` on motor catalog picks (iterate + DEFINE_MISSING).  
2. Unbound physics unchanged.  
3. SKU-bound motor mass affects total_mass → thrust/margin chain (tested).  
4. SKU-bound battery mass/energy overrides heuristic (tested).  
5. Diverge clears `catalog_ref` (tested).  
6. No Catalog DSE / Create→BOM / H5 / material fix.  
7. Single JSON reader preserved.  
8. Full suite green.  
9. Report complete + CLI probe listed.

---

## 8. Prompt to paste into Claude Code

> Execute Implementation Contract **Physical Component Catalog v1 — Impl B (Bind)** from `.jes/artifacts/implementation_contract_catalog_bind_v1.md`.
>
> Design authority: `docs/PHYSICAL_COMPONENT_CATALOG_V1.md` (CLOSED). Base: `checkpoint-catalog-impl-a`.
>
> Implement **Bind only**:
> - Catalog picks must set `ComponentSpec.catalog_ref` (fix iterate discard; align DEFINE_MISSING).
> - Writers mirror motor mass (SKU-bound only) and battery mass/energy from SKU (SKU-bound only).
> - CalculationEngine includes motor mass when mirrored param present; unbound behavior unchanged.
> - Clear `catalog_ref` when continuous/numeric changes diverge from SKU (no lying labels).
>
> Prefer a shared bind helper for motor paths. Battery/prop: helper + wire or helper+tests per contract.
>
> Do **not** implement Catalog DSE, Create→BOM, H5, material ES/EN fix, or second JSON reader.
>
> Add tests for identity persistence, mass causality, unbound regression, and invalidation.
> Write `.jes/artifacts/implementation_report_catalog_bind_v1.md` including the Engineer CLI probe script.
>
> **Do not commit or push.**

---

**End of contract.**
