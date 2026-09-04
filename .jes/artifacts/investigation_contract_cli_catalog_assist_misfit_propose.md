# Investigation Contract — CLI catalog-assist + misfit propose

**Project:** Jarvis  
**Date:** 2026-09-01  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_cli_catalog_assist_misfit_propose.md`

**Status:** READY FOR CLAUDE

**Type:** Product-path investigation. Trace why the happy-path catalog CLI cannot recover when a bound combo no longer fits, and which **one** first-IC tier is justified. **Not** new physics. **Not** a recommender subsystem. **Not** Catalog Foundation (ESC SKUs). **Not** an Implementation Contract.

**Checkpoint base:** tag **`v0.3.5`** / **`checkpoint-phase25-hover-energy`** · commit `fc46938`  
**Live tree:** Block Closure B-PROP-ENERGY is in product (do not revert; do not change its rollup).

**You are Claude Code.** This file is your work order. Cursor does not investigate and does not implement this slice. You write the report. Cursor reviews it. Engineer ★ on the recommended **first-IC tier** comes after that review. A later Implementation Contract (also written for you) is the only authorization to edit `src/`.

**Do not implement. Do not bump `pyproject.toml`. Do not weaken tests. Do not invent SKUs, watts, ESC η, or a Conversation Engine.**

---

## 0. Role split (do not invert)

```text
Cursor  → writes this contract (and later the IC)
Claude  → investigates, writes investigation_report_cli_catalog_assist_misfit_propose.md
Cursor  → investigation review
Engineer ★ → first-IC tier
Cursor  → writes IC
Claude  → implements from the IC only
```

**★ ratification (locked):** [engineer_ratification_cli_catalog_assist_misfit_propose.md](engineer_ratification_cli_catalog_assist_misfit_propose.md)

Optional seed notes (Cursor, **not** a report):  
[engineer_notes_cli_propose_on_misfit.md](engineer_notes_cli_propose_on_misfit.md)  
Walk: [engineer_cli_walk_block_closure_product_scope.md](engineer_cli_walk_block_closure_product_scope.md)

Treat notes as **hypotheses**. Verify or refute against code and the field fixture. If a note is wrong, say so with `file:line`.

Prior investigation that already named post-bind help and `bound_sku_underspec` (context, not proof you may skip tracing):  
[investigation_report_post_v034_block_closure.md](investigation_report_post_v034_block_closure.md) Gate E Path 2, Finding on `GAP-MOTOR-CATALOG-UNRESOLVED`.

---

## 1. Field fixture (input — inspect, do not mutate)

Live Engineer walk project (same slug/id as the walk):

```text
workspace/inspección-autonomía-mínima-5-minutos-eb61a0ed6fe2
```

If that directory is missing, say so and reconstruct the same bind graph from tests + library JSON + orchestrator traces. **Do not create or edit workspace files.**

Observed in chat (confirm in `state.json` / `latest_results` / BOM):

```text
objetivo: inspección, autonomía mínima 5 minutos
payload_kg: 0.5 · motor_count: 2 · architecture 4/4
motors catalog_ref: sunnysky_r2305_2500   (NOT sunnysky_r2205_2500)
propellers catalog_ref: gf_5045x3
battery catalog_ref: lipo_6s_10000mah (222.0 Wh) after earlier lipo_4s_1500mah
frame: PVC / structure_mass_override_kg 0.65 (iterate PVC 200g did not change mass — out of scope)
Propulsión (evidencia): legacy_estimate · ~7.5 N
sim: fail · thrust required ~30 N vs available 15 N · autonomy_min ~30.3 min
GAP-MOTOR-CATALOG-UNRESOLVED with SKU already bound
ayúdame a elegir (IDLE, post-bind) → reprinted estado
BLOQUE PROPULSIÓN/ENERGÍA: NO CERRADO
PROJECT STATUS: NOT ASSEMBLY READY
```

Earlier in the same walk (still relevant — 4S 1500 snapshot if still in history, else reconstruct):

```text
Create wizard D8 top-5 did not include sunnysky_r2205_2500
#1 was sunnysky_r2305_2500
Typed gf_5045x3 first → analyze CTA “este motor de catálogo no declara vatios” while list showed ~220W
lipo_4s_1500mah → autonomy L0 ~3.0 min vs 5 · thrust 15 vs ~16.35 N after PVC 650g
```

Gate A Combo A (library + tests, **not** the numbered offer): `sunnysky_r2205_2500` + `gf_5045x3` + `lipo_4s_1500mah` + freeform ESC. Engineer abandoned typing the hidden motor SKU. Do not recommend “document the SKU” as the product fix.

---

## 2. Product constraints (locked unless Engineer rewrites this contract)

| ID | Constraint |
|---|---|
| **C1** | **Spine = misfit propose.** The report’s primary question is: when the bound combo no longer fits, what can Jarvis honestly propose **with existing authorities**, and what requires a new search policy or DSE scope. |
| **C2** | **Three tiers.** Report must define, evidence, and recommend per §3.8. First IC **cannot** be Tier 3. |
| **C3** | **No silent G22 fallback.** Empty strict search stays empty unless you recommend a **named** second pass (Tier 2) with CLI copy that says filters were relaxed. |
| **C4** | Reuse `build_motor_catalog_suggestions` / `find_motors_for_requirements` — do not propose a second motor-ranking function. DSE already reuses G22 (`design_explorer._build_catalog_motor_candidates_for_goal`). |
| **C5** | No Conversation Engine, no Decision Engine, no new domain module, no `BLOCK_STATUS`, no ERF §11 / `_derive_overall` change, no Block Closure formula change, no catalog JSON expansion, no H5 ESC schema, no Option B, no Structure IC, no P26/P27-A, no HD lab. |
| **C6** | **G24-B `_score_candidate` stays frozen** unless you prove it **blocks the recommended first IC**. If you believe it blocks Tier 1 or 2, **stop** and say so — do not recommend unlocking it inside this investigation’s first IC. |
| **C7** | Watts CTA and GAP title are **hygiene**: recommend include/exclude in the first IC only if they share the same seams. They are not the spine. |

If evidence shows C2/C5 must break (e.g. even naming a replacement requires a new subsystem), **stop** and say so — do not expand scope yourself.

---

## 3. What you must investigate

### 3.1 Gate A — Walk fixture vs Combo A offer

- Confirm BOM SKUs and `bound_sku_underspec` evidence on the fixture.
- Trace D8 ranking at create (~4.7 N/motor, no battery): why `sunnysky_r2205_2500` is not in top 5; why `#1` is `sunnysky_r2305_2500`.
- Cite `MotorSpec.thrust_n` / `design_space` / sort key in `library.find_motors_for_requirements`.
- Question: is Combo A reachable from numbered pick **at all** on this create path, or only via verbatim SKU / test bind?

### 3.2 Gate B — Post-bind `ayúdame a elegir`

Trace IDLE FN-005 chain:

- `orchestrator._try_start_assisted_motor_help`
- propeller then battery fallbacks
- `catalog_bound_motor_covers_power_w` short-circuit

Reproduce (read-only / unit, not workspace mutation): help-choose with `catalog_ref` set **and** `bound_sku_underspec`. Document the exact predicate that returns `None`.

Confirm or refute Gate E Path 2 (battery: `definir bateria` then help-choose). Is motor underspec the same shape?

### 3.3 Gate C — G22 filters on the **failed** combo

On the walk state (or an equivalent in-memory `ProjectState`):

Call `build_motor_catalog_suggestions` **as production does** (thrust + `derive_kv_prop_filters`).

Record:

1. `thrust_per_motor_needed_n`
2. `kv_hint`, `prop_inch`
3. the returned list (names + thrust) or empty

Then compute (in the report, not a new production function) what the **same** `find_motors_for_requirements` returns if KV and/or prop filters are dropped (thrust-only). Name SKUs. This is evidence for Tier 2, not an implementation.

State whether Tier 1 on this fixture is: **useful list** / **empty** / **list that still cannot lift**.

### 3.4 Gate D — Continuity + SuggestionEngine vs DSE

- Continuity ranking: why sim-fail (rank 2) hides catalog next-step (rank 3) on this walk. `project_continuity.py` file:line.
- `SuggestionEngine.generate_suggestions`: types emitted after this sim fail; confirm no SKU.
- DSE: `_CATALOG_MOTOR_GOAL_KEYS` membership. Does `aumentar_empuje` / `mejorar_autonomia` / thrust language get catalog-motor candidates? FN-022 mapping of empuje → `mejorar_estabilidad` — does that path inject catalog motors, and would G22 still empty them?
- Question: can **Tier 3 later** be absorbed by DSE + G24-A apply-by-index **without** a new subsystem? Answer YES / NO / PARTIAL with seams. Do **not** design that IC.

### 3.5 Gate E — Watts CTA

Trace `catalog_bound_motor_covers_power_w` vs CLI/ReasoningLayer copy “este motor de catálogo no declara vatios”.

On `sunnysky_r2305_2500`: library `max_watts` vs predicate (SKU bound). Recommend: copy-only vs predicate split. Smallest file list for a future IC.

### 3.6 Gate F — GAP vocabulary

`GAP-MOTOR-CATALOG-UNRESOLVED` title vs `gap_evidence_fact` `bound_sku_underspec:{sku}` in `engineering_readiness._motor_catalog_gaps`.

Recommend: rename type (registry impact) vs title/copy only vs leave ID + fix Continuity/help-choose. Do not invent a tenth subsystem.

### 3.7 Frankenstein risk (Tier 2)

If thrust-only search would offer a motor incompatible with bound `gf_5045x3`, say so with SKUs. Recommendation: motor-only re-offer is honest **only if** CLI says propeller may need re-bind, or propeller is in the same offer (that second sentence is Tier 2+/3 — flag, do not merge into Tier 1).

### 3.8 Gate G — First-IC recommendation (mandatory)

Recommend **exactly one**:

| ID | First IC |
|---|---|
| **T1** | Tier 1 only: post-bind help-choose re-opens motor list; Continuity after sim-fail / underspec points at that list (or names 1–5 candidates already computed by G22); GAP title honesty; optional watts CTA if same seams. **No** filter relax. |
| **T1+2** | T1 plus a **named** G22 second pass (drop inherited KV and/or prop) **because** Gate C shows T1 empty/useless on the walk fixture. CLI must say filters were relaxed. Address frankenstein (prop) in the IC non-goals or a one-line warning — not a joint combo search. |
| **STOP** | Even T1 requires a new subsystem or unlocking G24-B / Foundation / Conversation Engine. No IC from this report. |

**Forbidden as first IC:** Tier 3 joint combo search; “just tell the user to type `sunnysky_r2205_2500`”; Catalog Foundation ESC SKUs; H5; Option B.

If you recommend T1+2, list the **exact** filter relax (drop KV only / drop prop only / drop both) with Gate C evidence.

### 3.9 Tests / probe sketch (for the future IC — not a patch)

Name existing tests that pin G22 empty, G21 bound-without-watts, G9-A underspec, FN-005 help-choose, Continuity rank, DSE catalog goals (`test_g21_g22_catalog_bind_ux.py`, `test_assisted_acquisition.py`, `test_project_continuity.py`, G24 / design_explorer tests).

Sketch **one** unit or CLI probe: architecture 4/4, bound `r2305` + `gf_5045x3` + heavy battery, `ayudame a elegir` must not reprint bare `estado` if you recommend T1.

---

## 4. Explicit non-goals

- Implementing any tier
- Expanding `library/motores/_datos.json` to force Combo A into top 5
- Unlocking G24-B scoring by default
- Joint motor+prop+battery recommender (Tier 3) as this investigation’s IC
- Frame iterate mass / Structure
- Changing Block Closure `derive_prop_energy_block_closure` / N1 discharge copy
- Inventing hover minutes or writing W into catalog

---

## 5. Done when your report contains

1. As-is path graph (help-choose / G22 / Continuity / suggestions / DSE catalog keys) with `file:line`.
2. Gate C table: filtered list vs thrust-only list on the walk (or equivalent) state.
3. Recommended **T1** / **T1+2** / **STOP** with a **future-IC file list** (not a patch).
4. Hygiene: watts CTA + GAP title — in or out of that IC.
5. Tier 3: YES/NO/PARTIAL “DSE can absorb later without a new subsystem” — one paragraph, not a design.
6. Sign off: **no `src/` or test files touched.**
