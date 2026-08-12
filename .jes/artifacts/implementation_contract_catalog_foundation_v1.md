# Implementation Contract — Physical Component Catalog v1 — Impl A (Foundation)

**Project:** Jarvis  
**Date:** 2026-08-12  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** DONE — PASS (review `.jes/artifacts/implementation_review_catalog_foundation_v1.md`; awaiting Engineer commit)  

**Type:** Infrastructure / domain foundation — Physical Component Catalog v1 **Impl A only**.  

**Design authority (mandatory):** [`docs/PHYSICAL_COMPONENT_CATALOG_V1.md`](../../docs/PHYSICAL_COMPONENT_CATALOG_V1.md) — **DESIGN CLOSED** (Engineer locks 1A–5A + A/B/C/D).  

**Prior artifacts:**  
- `.jes/artifacts/catalog_v1_connection_audit.md`  
- `.jes/artifacts/implementation_review_catalog_v1_audit.md` (PASS WITH NOTES)  

**Checkpoint base:** `v0.2.0` / `checkpoint-fn026-h4`  

**Explicitly deferred (do not implement):**  
Impl B (Bind write path, mass-in-calc, iterate discard fix) · Impl C (Catalog DSE) · Impl D (Create→BOM) · H5/C-081 · ESC/frame SKU catalogs · Continuity gap redesign · material ES/EN micro-fix (3A) · Conversation Engine / Step D  

**Workflow:** Claude implements + tests + report → Engineer forwards → Cursor reviews. **No commit/push unless Engineer asks.**

---

## 0. Intent

Establish the **Physical Catalog Foundation**:

```text
library/{motores,baterias,helices}/_datos.json
        ↓
ComponentLibrary  (single reader)
        ↓
typed records + deterministic get / find / match
        ↓
honest not-found / gap at API level
```

Plus the **schema placeholder** for identity:

```text
ComponentSpec.catalog_ref: { family, sku } | None
```

**Optional. Default `None`. No writer, assist pick, or Continuity path may populate it in this cut.**

This cut does **not** change calculation, simulation, DSE, Continuity ranking, or assisted-pick behavior beyond what is strictly required for the library API and schema to load/test.

---

## 1. Architectural authority (non-negotiable)

| Rule | Impl A implication |
|---|---|
| Catalog = identity + physical data authority | JSON + `ComponentLibrary` own SKU fields |
| Calc/sim read `current_parameters` only | **Zero** calc/sim behavior change |
| Bind is Impl B | **Do not** set `catalog_ref` from picks; **do not** project SKU → params |
| LLM never invents SKUs | No LLM in catalog load/match |
| Single JSON reader | Only `knowledge/library.py` (or thin helpers it owns) reads `_datos.json` |
| Honest gap | Missing SKU / no match → distinguishable empty / not-found — never fabricate |

---

## 2. IN SCOPE

### 2.1 Library layout

```text
library/
  motores/_datos.json      # enrich schema; preserve valid existing rows
  baterias/_datos.json     # NEW — seed ~8–15, LiPo-first
  helices/_datos.json      # NEW — seed ~10–20
  materiales/_datos.json   # unchanged (do not “fix” ES/EN aliases here)
```

### 2.2 Typed specs in `knowledge/library.py`

Extend (or add dataclasses) following existing `MotorSpec` / `MaterialSpec` style:

- **MotorSpec** — keep existing required fields; allow optional enrichment fields from Design §4.2 (`manufacturer`, `model`, `max_current_a`, voltages, `compatible_prop_ids`, `operating_points`, optional `source_url`). Existing motors must still load.
- **BatterySpec** — required: chemistry, energy_wh, mass (`mass_g` or `mass_kg` — pick one canonical and document), voltage identity (`cells` and/or `nominal_voltage`). Optional: capacity_mah, currents, c_rating, design_space, operating_points.
- **PropellerSpec** — required: diameter_in, pitch_in. Optional: mass_g, ct, cp, compatible_kv_band, tags, operating_points.

`operating_points`: optional lists; **no consumer code** in Impl A (no calc interpolation).

### 2.3 `ComponentLibrary` API

Extend the existing class — **do not** invent a second library architecture.

Minimum surface (names may follow project conventions if clearer):

```text
get_motor(id) / list_motors / has_motor
get_battery(id) / list_batteries / has_battery
get_propeller(id) / list_propellers / has_propeller

find_motors_for_requirements(...)     # EXISTING D8 — must not regress
find_batteries(...)                   # minimal deterministic filters OK (e.g. min energy_wh)
find_propellers(...)                  # e.g. by diameter_in

match_motor_propeller(motor_id, prop_id) -> bool
  # explicit compatible_prop_ids OR compatible_prop_inch / diameter rules only
```

Unknown id → deterministic not-found (exception or `None` — match existing `get_motor` style).

### 2.4 `CatalogRef` + `ComponentSpec.catalog_ref`

In `schemas/action_schema.py` (or adjacent schema module if project prefers):

```text
CatalogRef:
  family: Literal["motor", "battery", "propeller"]
  sku: str

ComponentSpec.catalog_ref: CatalogRef | None = None
```

- Additive; `extra="ignore"` / defaults must not break existing fixtures.  
- **No** production code path sets this field in Impl A.  
- Tests may construct `ComponentSpec(catalog_ref=...)` to prove round-trip serialization only.

### 2.5 Seed data quality

- Small curated seed (Design §10).  
- Prefer plausible manufacturer-like ids; do not invent dense thrust tables.  
- Motors: do not arbitrarily rewrite valid existing numeric rows; additive fields OK.  
- Batteries: every seed row has real `energy_wh` + mass + chemistry.  
- Propellers: every seed row has diameter_in + pitch_in.

---

## 3. OUT OF SCOPE (hard)

Claude must **not**:

| Forbidden | Belongs to |
|---|---|
| Populate `catalog_ref` from assisted pick / DEFINE_MISSING / iterate | Impl B |
| Fix iterate discard of SKU name | Impl B |
| Motor mass → `calculation_engine` | Impl B (2A) |
| Battery SKU mass override of 150 Wh/kg | Impl B (4A) |
| Catalog-aware DSE / change `EXPLORATION_GRIDS` | Impl C |
| Create→BOM / SKU BOM | Impl D |
| Extend Continuity gaps to battery/prop | later UX / B |
| Generalize `motor_catalog_assist` into mega-module | 5A — leave as-is |
| Material ES/EN alias fix | separate micro-fix 3A |
| H5 / C-081 / ESC catalog | deferred |
| Second JSON reader in orchestrator/assist/calc | forever forbidden |
| Mandatory dense `operating_points` | overscope |
| Allocate final System Map `C-xxx` IDs into CONNECTIONS | Cursor later; optional brief “proposed edges” note in report only |

---

## 4. Backwards compatibility

Must remain green / behavior-unchanged:

- Existing motor load + `find_motors_by_kv` + `find_motors_for_requirements` (D8)  
- `motor_catalog_assist` + Continuity motor gap path (no intentional behavior change)  
- Calculation / simulation numeric behavior  
- FN-022…026 / H1–H4  
- Existing `ComponentSpec` construction in tests (new field defaults to `None`)

---

## 5. Tests (minimum)

New focused file(s), e.g. `tests/test_catalog_foundation_v1.py`:

1. Motors load; existing known SKU `get_motor` works.  
2. Motor D8-style `find_motors_for_requirements` smoke (regression).  
3. Enriched optional motor fields load when present; absent optionals OK.  
4. Batteries load; `get_battery` by id; required fields present on seed rows.  
5. Propellers load; `get_propeller`; diameter/pitch preserved.  
6. Unknown SKU → not-found deterministic.  
7. `match_motor_propeller` true for explicit/compatible pair; false for incompatible; no invented true.  
8. `ComponentSpec` round-trip with `catalog_ref=None` (default) and with a set `CatalogRef` (unit only).  
9. Grep/guard test or architectural assertion: no new `_datos.json` reads outside `knowledge/library.py`.  
10. Relevant existing library / motor assist / iterate regression subset green.  
11. Full suite green (or pre-existing failures explicitly named).

---

## 6. System Map / docs

- **Do not** invent registry IDs or flip connection statuses.  
- Optional: one short paragraph in the Implementation Report listing `PROPOSED-CAT-*` edges touched by Foundation (from audit) — Cursor will register later.  
- Do **not** rewrite `PHYSICAL_COMPONENT_CATALOG_V1.md` except if you find a factual contradiction — then stop and report, do not silently redefine locks.

---

## 7. Implementation Report (required)

Create:

`.jes/artifacts/implementation_report_catalog_foundation_v1.md`

```markdown
# Implementation Report — Catalog Foundation v1 (Impl A)

## Summary
## Existing architecture inspected
## Catalog schema (Motors / Batteries / Propellers)
## Canonical API
## ComponentSpec.catalog_ref (schema only — confirm writers untouched)
## Data seed (counts + LiPo-first note)
## Matching / gap behavior
## Files changed
## Tests run
## Regression results
## System Map impact (proposed only — no ID allocation)
## Blast radius
## Explicitly deferred (B/C/D, H5, material micro-fix, Continuity)
## Risks / limitations
```

---

## 8. Acceptance criteria (Cursor PASS requires)

1. Motors, batteries, propellers load via one `ComponentLibrary`.  
2. Typed get/list/find/match deterministic; honest not-found.  
3. Existing motor D8 / assist behavior does not regress.  
4. `catalog_ref` exists on `ComponentSpec`, default `None`.  
5. **No** production path sets `catalog_ref`.  
6. **No** calc / DSE / Continuity / Bind write-path changes.  
7. Foundation tests + full suite green.  
8. Report accurate; deferred list explicit.  
9. No second JSON reader.  
10. No commit/push unless Engineer asked.

---

## 9. Prompt to paste into Claude Code

> Execute Implementation Contract **Physical Component Catalog v1 — Impl A (Foundation)** from `.jes/artifacts/implementation_contract_catalog_foundation_v1.md`.
>
> Mandatory design authority: `docs/PHYSICAL_COMPONENT_CATALOG_V1.md` (DESIGN CLOSED — locks 1A–5A).
>
> Before coding, inspect: `src/jarvis/knowledge/library.py`, `library/motores/_datos.json`, `schemas/action_schema.py` (`ComponentSpec`), existing motor library/D8 tests.
>
> Implement **Foundation only**:
> - `library/baterias/_datos.json` + `library/helices/_datos.json` (+ enrich motors schema without breaking rows)
> - Extend `ComponentLibrary` (single reader) with battery/propeller loaders + get/find + `match_motor_propeller`
> - Add `CatalogRef` + optional `ComponentSpec.catalog_ref` (default None) — **do not populate it from any writer/pick path**
>
> Do **not** implement Bind, mass-in-calc, iterate discard fix, Catalog DSE, Create→BOM, H5, Continuity redesign, or material ES/EN fix.
>
> Do not create a second JSON reader. Do not let the LLM invent SKUs.
>
> Add Foundation tests; run regressions + full suite.
>
> Write `.jes/artifacts/implementation_report_catalog_foundation_v1.md`.
>
> **Do not commit or push.**
>
> Return the Implementation Report for Cursor review.

---

**End of contract.**
