# Investigation Contract — Project Closure / Assembly Ready (Physical Catalog)

**Project:** Jarvis  
**Date:** 2026-08-30  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output:** `.jes/artifacts/investigation_report_project_closure_assembly_ready.md`

**Status:** READY FOR CLAUDE

**Type:** Architecture + product investigation — define what **“assembly-ready closure”** means as a **deterministic readiness contract**, and recommend the **correct implementation sequence** (G27 / G26 / battery catalog UX / other) — **not** a mega-implementation plan.

**Checkpoint base:** tag **`v0.3.0`** / **`checkpoint-propeller-catalog-bind`** · commit `2efe1c2`

**Design authority (read-only):**
- [`docs/ENGINEERING_READINESS_VISION.md`](../../docs/ENGINEERING_READINESS_VISION.md) — to-be readiness language
- [`docs/PHYSICAL_COMPONENT_CATALOG_V1.md`](../../docs/PHYSICAL_COMPONENT_CATALOG_V1.md) — catalog families, `catalog_ref`, freeform policy
- [`docs/PRODUCT_SCOPE.md`](../../docs/PRODUCT_SCOPE.md) — when a project is “done”
- [`.jes/artifacts/design_erf1_readiness_foundation.md`](design_erf1_readiness_foundation.md) — as-is gap model (ERF-1)
- [`.jes/artifacts/design_erf2_dependency_hardening.md`](design_erf2_dependency_hardening.md) — electronics / electrical gaps (ERF-2)

**Prior findings (read, do not re-litigate without code trace):**
- [`.jes/artifacts/cli_finding_g26_restrictions_not_parsed.md`](cli_finding_g26_restrictions_not_parsed.md)
- [`.jes/artifacts/cli_finding_g27_battery_6s_parsed_as_6wh.md`](cli_finding_g27_battery_6s_parsed_as_6wh.md)
- [`.jes/artifacts/investigation_report_phase2_physical_propulsion.md`](investigation_report_phase2_physical_propulsion.md) — G26/G27 **not** Phase 2 calc prerequisites; catalog bind paths independent
- [`.jes/artifacts/investigation_report_impl_d_create_bom_sku.md`](investigation_report_impl_d_create_bom_sku.md) — BOM SKU ≠ ASSEMBLY READY while Requirements INCOMPLETE

**Prerequisites (CLOSED):**
- ERF-1 + ERF-2 (`checkpoint-erf2`)
- Catalog V1 Impl A–D + SKU BOM (`checkpoint-impl-d`)
- Phase 2 P2-1 lookup OP (`checkpoint-phase2-p2-1`)
- Propeller Catalog Bind UX (`checkpoint-propeller-catalog-bind` / `v0.3.0`)

**Engineer decision (2026-08-30) — locked framing:**

```text
Do NOT rank G24 / G26 / G27 as isolated next tickets.

Next arc = "Project Closure / Assembly Ready"
  ↓
This investigation determines:
  - what actually blocks ASSEMBLY READY today
  - what is G26 vs broader closure architecture
  - role of G27 + catalog battery in energy/calc
  - freeform vs catalog-required policy per family
  - recommended IC sequence (likely multiple cuts, not one)
```

**Do NOT implement closure fixes in this investigation.**  
**Do NOT invent catalog SKUs or fake PASS states to prove closure.**

**Workflow:** Investigate → report → Engineer ★ → Cursor IC(s) → Claude implements per cut → review → CLI walk → checkpoint. **No production fix in this contract.**

---

## 0. Context

### 0.1 Why investigate now (not implement)

After `v0.3.0`, Jarvis can complete **propulsion with catalog evidence**:

```text
motor catalog-bound → fallback OP
  → propeller help-choose → exact OP
  → calcular / simular coherent with 9.7086 N/motor
```

But the product goal has shifted:

```text
From: "physics calculates coherently"
To:   "design is sufficiently defined — components have evidence,
       physics passes, project is assembly-ready"
```

Engineer CLI on a real workspace project (`crear-un-dron-de-autonomia-con-payload-1kg`) already shows the split:

| Surface | State after v0.3.0 walk |
|---|---|
| Physics / sim | PASS, good margin |
| Propulsion evidence | `exact_operating_point · 9.7086 N` |
| Propulsion subsystem | **PASS** |
| Catalog subsystem | **PASS** |
| Requirements | **INCOMPLETE** |
| Energy / Structure / Electronics / Control / BOM | **INCOMPLETE** |
| Overall | **NOT ASSEMBLY READY** |

Jumping straight into G27 or G26 fixes without a closure architecture risks optimizing local bugs while missing the **system definition of “ready”**.

### 0.2 Core product question

What must be true in `ProjectState` + readiness projection for Jarvis to honestly say:

```text
"Este diseño está suficientemente definido, sus componentes tienen evidencia,
 la física pasa y puedo considerarlo listo para ensamblaje."
```

### 0.3 Philosophy lock (★ — non-negotiable)

These rules must appear in the report and govern all recommendations:

| ★ | Rule |
|---|---|
| **★1** | **Do not invent components to obtain PASS.** If no ESC exists in catalog, ESC may be **declared manually** and remain honestly `catalog_bound=False`. Claiming *“✓ ESC real de catálogo”* requires a real, traceable catalog entry. |
| **★2** | **Physics may be provisional; evidence may not.** Freeform declare can support orientation/sim; catalog-bound claims require `catalog_ref` + library provenance. (Same discipline as P2-1.) |
| **★3** | **Readiness composes existing authorities** — `engineering_readiness.py` must not become a second physics engine or catalog reader. |
| **★4** | **ASSEMBLY READY is a rollup, not a single metric.** Investigate the full gap + subsystem graph, not only Requirements. |
| **★5** | **Separate “BOM complete” from “ASSEMBLY READY”.** Report must define both and the path between them. |

### 0.4 Explicit non-goals

- Implementing battery pick UX, G26 routing fix, or G27 parser fix  
- H5 ESC catalog / frame SKU catalog / Conversation Engine  
- G24 DSE apply-only-#1 (unless investigation proves closure **cannot** be designed without it — must argue with code)  
- Version bump  
- Changing P2-1 OP resolver rules or ★6 seed data  
- Weakening tests to force ASSEMBLY READY in fixtures  

---

## 1. What Claude must investigate

### 1.1 ASSEMBLY READY blocker inventory (mandatory)

Trace the **as-is** path from a real project state to `overall` in `build_engineering_readiness`.

| Step | File / symbol | Questions |
|---|---|---|
| Entry | `engineering_readiness.build_engineering_readiness` | Inputs only from `ProjectState` + authority helpers? |
| Gaps | `_build_gaps`, gap type registry | What gap types fire for a “typical” post-v0.3.0 drone project? |
| Subsystems | `_derive_subsystem_verdict`, `_EVIDENCE_BUILDERS` | Which of the 9 subsystems block today and **why**? |
| Rollup | `_derive_overall` | Exact PASS conditions; role of HIGH gaps vs INCOMPLETE subsystems |
| BOM | `project_closure.build_component_bom`, `classify_component` | When is BOM INCOMPLETE vs PASS? SKU-resolved vs stub? |
| Requirements | `state_schema._parse_constraints`, `_requirements_evidence` | What makes `requirements.defined` True/False? |

**Deliverable:** table — **Blocker → subsystem(s) → gap_id(s) → root cause → fix class** (routing / UX / catalog / policy / data).

Use at least **two fixtures**:

1. **Post-v0.3.0 propulsion-complete project** (motor + propeller bound, ESC/battery/frame stubs) — Engineer’s real workspace shape.  
2. **Historical “almost ready” project** if documented (e.g. `autonomia-5540bda0ac16` from G26/G27 findings) — compare blocker set.

### 1.2 G26 — what it really is (mandatory)

Do not treat “G26” as a label. Answer precisely:

| Question | Required answer |
|---|---|
| What is the bug? | File:line, write path vs read path |
| What subsystem/gap does it affect? | Requirements only, or also Continuity/DSE? |
| Does it affect calc/sim physics? | YES/NO with trace |
| Does it block ASSEMBLY READY alone? | YES/NO with example project state |
| Is it a **closure prerequisite** or **parallel polish**? | Argue from `_derive_overall`, not opinion |

Cross-check [`.jes/artifacts/cli_finding_g26_restrictions_not_parsed.md`](cli_finding_g26_restrictions_not_parsed.md).

**Deliverable:** G26 scope box — “fixes X, unblocks Y, does not fix Z”.

### 1.3 G27 — role in closure (mandatory)

| Question | Required answer |
|---|---|
| Root cause | Confirm `semantic_intent_adapter._parse_value` vs other paths |
| Catalog bind path | Does `bind_battery_from_catalog` bypass G27? Trace to `battery_capacity_wh` |
| Energy subsystem | When battery is catalog-bound, does `_energy_evidence` / energy PASS work today? |
| Autonomy calc | `calculate_autonomy_min` — what inputs; honest when Wh is wrong? |
| Closure role | Is G27 **required before** battery catalog UX, or **orthogonal** (UX uses pick, not free-text parse)? |

Cross-check [`.jes/artifacts/cli_finding_g27_battery_6s_parsed_as_6wh.md`](cli_finding_g27_battery_6s_parsed_as_6wh.md) and Phase 2 report §6.

**Deliverable:** verdict — **G27 in closure sequence: before / after / parallel to battery UX** with rationale.

### 1.4 Catalog battery participation in calc / energy (mandatory)

Trace the full chain for a **catalog-bound battery SKU** (use existing seed, e.g. from `library/baterias/_datos.json`):

```text
bind_battery_from_catalog(sku)
  → set_battery_component / writers
  → current_parameters["battery_capacity_wh"], battery_mass_kg
  → calculation_engine
  → autonomy_min
  → energy subsystem evidence
  → electrical_compatibility (discharge check)
  → readiness gaps
```

| Question | Required answer |
|---|---|
| Is bind API sufficient without UX? | Test-callable path today |
| Does mass use SKU or 150 Wh/kg heuristic? | When `catalog_ref` set vs cleared |
| Does `invalidate_diverged_catalog_refs` cover battery drift? | DSE / iterate interaction |
| What is missing for **live CLI** battery catalog pick? | Mirror G21/propeller pattern — list gaps only |
| Does exact OP / propulsion need battery voltage for energy closure? | Separate propulsion OP voltage from energy Wh |

**Deliverable:** energy closure checklist — what works today vs what an IC must add.

### 1.5 “Real component” definition in Jarvis (mandatory — policy)

Produce a **normative table** (as-is + recommended to-be for closure v1):

For each concept, state **where it lives today** and **what closure should require**:

| Concept | Investigate |
|---|---|
| `catalog_ref` (`family`, `sku`) | Schema, writers, BOM `[sku]` display |
| Physical properties on `ComponentSpec` | vs params mirror |
| Provenance / source | `PropertyValue.source`, `propulsion_resolution`, library `source_url` |
| Manufacturer / model | Optional fields in library — used anywhere? |
| `completeness` high/low | vs `classify_component` / BOM tier |
| `catalog_bound` in readiness | Per-subsystem evidence — sufficient for “real”? |
| Freeform declare | Valid for closure? For which families? |

**Deliverable:** definition box:

```text
"Componente real (catálogo)" = …
"Componente declarado (freeform)" = …
"Componente stub / incompleto" = …
```

Must respect ★1 — no pretending freeform is catalog.

### 1.6 Freeform vs catalog-required by family (mandatory)

For each component key in aerial architecture:

```text
motors, propellers, battery, esc, frame, flight_controller, sensors, …
```

| Column | Required |
|---|---|
| Catalog data exists? | library JSON yes/no |
| Bind helper exists? | `catalog_bind.py` |
| Pick UX exists? | CLI help-choose yes/no |
| Freeform declare path | infer / wizard |
| ERF `catalog_bound` checked? | which subsystem |
| **Recommend for closure v1** | `catalog_required` / `freeform_ok` / `stub_ok_for_physics_only` |

Explicitly address Engineer cases:

- ESC — no catalog → manual declare OK; catalog claim needs H5-scale work (out of closure v1?)  
- Frame — materials library ≠ frame SKU  
- FC / sensors — likely freeform-only for v1  

**Deliverable:** family policy matrix + ★ for Engineer ratification.

### 1.7 Minimum requirements per family (mandatory)

From `system_architecture_catalog`, `project_closure`, component writers, and ERF evidence builders:

What is the **minimum** `ComponentSpec` + params for each family to:

1. Stop being BOM INCOMPLETE  
2. Reach subsystem PASS (not merely stop showing gap)  
3. Contribute honestly to calc/sim  

**Deliverable:** per-family minimum spec table (fields, completeness, catalog_ref optional/required).

### 1.8 Existing catalog vs catalog expansion (mandatory)

Inventory `library/` today:

| Family | Entries | Bind API | Pick UX | OP / calc hooks |
|---|---|---|---|---|
| motores | ~22 | yes | yes | P2-1 OP |
| helices | ~16 | yes | yes | P2-1 OP |
| baterias | ~10 | yes | no | Wh / mass / discharge |
| materiales | ~8 | N/A | N/A | frame density |

Answer:

- What % of closure v1 can ship **without new SKUs**?  
- What families **require catalog expansion** before honest “catalog-bound” claims?  
- Is battery UX + G27/G26 fix enough for energy closure, or are new gap types needed?

### 1.9 Closed project — target `estado` / readiness shape (mandatory)

Describe **two** target snapshots (honest, achievable with recommended sequence):

**A — Assembly-ready (freeform-tolerant v1)**  
Physics PASS + BOM structurally complete + requirements parsed + key subsystems PASS; some components freeform without `catalog_ref`; no false catalog claims.

**B — Assembly-ready (catalog-evidence-strong)**  
Same as A but motors + propellers + battery catalog-bound where library supports; ESC/FC freeform labeled honestly.

For each, show exemplar:

```text
ENGINEERING READINESS (subsystem lines)
PROJECT STATUS: ASSEMBLY READY | NOT ASSEMBLY READY
Componentes / gaps (BOM section)
Propulsión (evidencia): …
```

### 1.10 Transition path (mandatory)

Explicit state machine:

```text
S0: PHYSICS PASS + BOM INCOMPLETE + NOT ASSEMBLY READY   ← typical mid-project
S1: PHYSICS PASS + BOM COMPLETE + NOT ASSEMBLY READY     ← what changes?
S2: PHYSICS PASS + BOM COMPLETE + ASSEMBLY READY         ← target
```

For each transition, list **minimal mutations** (not implementation — e.g. “bind battery SKU”, “fix parsed_constraints”, “declare ESC high completeness”).

Identify **which transitions are independent** vs **sequentially dependent**.

### 1.11 Recommended implementation sequence (mandatory — primary deliverable)

Do **not** assume `G27 → G26 → battery UX` is correct. Evaluate alternatives:

| Option | Sketch |
|---|---|
| **A** | G27 → G26 → battery catalog UX → closure policy tweaks |
| **B** | Battery catalog UX first (bypasses G27 for pick path) → G26 → freeform policy |
| **C** | Closure policy + BOM completeness first → then G26/G27 |
| **D** | Split: “Requirements closure” IC + “Energy catalog UX” IC + “Readiness rollup” IC |

Recommend **one sequence** with 2–4 **Implementation Contract cuts** (names only, no code). Each cut must:

- Have a testable CLI walk gate  
- Respect ★1–★5  
- Not exceed ~1 checkpoint worth of scope  

Address whether **G24** belongs in closure arc or stays deferred.

### 1.12 Regression / CLI probe sketch (mandatory)

Future probes for closure arc (bullets only):

```text
1) Post-v0.3.0 project: list blockers → fix class per blocker
2) Bind battery from catalog (API or future UX) → energy evidence → calc autonomy
3) Fix/replay G26 scenario → Requirements PASS
4) G27 scenario → either refused or correct Wh — never 6 Wh
5) Declare ESC freeform → electronics INCOMPLETE→PASS? honest catalog_bound
6) Full walk to ASSEMBLY READY (freeform-tolerant v1) — no invented SKUs
```

---

## 2. Scope boundaries

### In scope

- Full audit §1.1–1.12  
- Blocker inventory from real + documented fixtures  
- G26/G27 scoped precisely for closure (not generic debt essay)  
- Battery catalog → calc/energy chain trace  
- Freeform vs catalog policy matrix  
- “Real component” definition  
- Target closed-project shape + transition path  
- Recommended IC sequence (multiple cuts)  
- ★ decisions for Engineer  

### Out of scope

- Any `src/` / test changes  
- New library JSON rows (unless reporting “expansion needed” as finding)  
- Implementing pick UX or G26/G27 fixes  
- H5 ESC catalog / frame SKU catalog  
- Conversation Engine / Step D  
- Changing `_derive_overall` semantics without explicit ★ proposal  

---

## 3. Output format

`.jes/artifacts/investigation_report_project_closure_assembly_ready.md`

Required sections:

1. **Executive summary** — blocker count, recommended sequence in 5 lines  
2. **ASSEMBLY READY blocker inventory** (§1.1)  
3. **G26 scope box** (§1.2)  
4. **G27 role in closure** (§1.3)  
5. **Catalog battery → calc/energy chain** (§1.4)  
6. **“Real component” definitions** (§1.5)  
7. **Freeform vs catalog policy matrix** (§1.6)  
8. **Minimum requirements per family** (§1.7)  
9. **Existing catalog vs expansion** (§1.8)  
10. **Target closed-project snapshots A / B** (§1.9)  
11. **Transition S0 → S1 → S2** (§1.10)  
12. **Sequence options + recommendation** (§1.11)  
13. **CLI probe sketch** (§1.12)  
14. **★ Decisions for Engineer** (numbered, ratify/reject)  
15. **Suggested IC outline** — 2–4 cuts with gates  

---

## 4. Hard constraints for future ICs

- **LLM never invents SKUs** — lists from `ComponentLibrary` only.  
- **Reuse `catalog_bind` helpers** — no parallel binders.  
- **`ProjectState` remains SoT**; readiness is projection only.  
- **Do not wire fake `catalog_ref`** to satisfy BOM/readiness tests.  
- **Do not break v0.3.0 propulsion path** (motor + propeller bind → exact OP).  
- **Zero weakened tests** — disclose any assertion changes explicitly.  
- **Separate ICs** if sequence recommends >1 cut — no mega-IC.  

---

## 5. Acceptance (Cursor review)

**PASS** if report:

- Answers every §1 subsection with code traces (file:line where factual)  
- Uses ≥2 project fixtures  
- Separates G26 vs G27 vs battery UX vs BOM vs rollup policy  
- Delivers family policy matrix + S0/S1/S2 transition  
- Proposes ≥2 sequence options with explicit recommendation  
- Includes ★ decisions + 2–4 IC cut outlines  

**FAIL** if report:

- Collapses closure into “fix G26 and done” without subsystem audit  
- Proposes inventing ESC/frame catalog entries to force PASS  
- Implements fixes or weakens acceptance criteria  
- Ignores `_derive_overall` / gap registry authority  

---

## 6. Queue after investigation

```text
Investigation PASS
  ↓
Engineer ★ (sequence + family policy)
  ↓
Cursor: implementation_contract(s) — one per cut
  ↓
Claude implements → review → CLI walk → checkpoint(s)
  ↓
Optional version bump — Engineer call only
```

---

**End of contract.**
