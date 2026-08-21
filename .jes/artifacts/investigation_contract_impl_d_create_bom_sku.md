# Investigation Contract — Impl D Create → BOM / SKU BOM

**Project:** Jarvis  
**Date:** 2026-08-21  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output:** `.jes/artifacts/investigation_report_impl_d_create_bom_sku.md`

**Status:** READY FOR CLAUDE

**Type:** Audit + design investigation — BOM / Create handoff must **consume SKU identity** (`catalog_ref`) so bound components become buildable line items, not only completeness buckets.

**Checkpoint base:** tag **`checkpoint-impl-c`** · commit `c99fec6`

**Design authority (read-only):**
- [`docs/PHYSICAL_COMPONENT_CATALOG_V1.md`](../../docs/PHYSICAL_COMPONENT_CATALOG_V1.md) — §6 Phase plan, exit criterion Impl D: *“Create/BOM consumes SKU identity (separate contract)”*
- [`docs/ENGINEERING_READINESS_VISION.md`](../../docs/ENGINEERING_READINESS_VISION.md) — Catalog/BOM Expansion (SKU-resolution tracking, BOM readiness)
- Existing BOM authority: `project_closure.build_component_bom` / `format_bom_lines` / ERF BOM gaps

**Prerequisites (CLOSED — do not re-open without cause):**
- **Impl A/B** — catalog schema + bind (`catalog_ref`)
- **Impl C** — catalog-aware DSE + thrust bridge (`checkpoint-impl-c`)
- **ERF-1/2** — readiness + BOM subsystem PASS when complete
- **G9-A** — bound-SKU-aware catalog gap honesty

**Explicitly queued debt — OUT OF SCOPE for this investigation (do not design fixes here):**
- **G24** — DSE apply only `#1` / catalog unselectable  
- **G25** — bare `sistema` → LLM  
- **G26** — restrictions/objective vs constraint (`autonomia=15`)  
- **G27** — `LiPo 6S…` → `6 Wh`  
- Real physics Phase 2 · H5 ESC catalog · Conversation Engine · Step D

**Workflow:** Investigate → report → Engineer ratifies ★ decisions → Cursor writes Implementation Contract → Claude implements. **No production fix in this contract.**

---

## 0. Context

### 0.1 Problem statement

After Impl A–C, a motor (and optionally battery) can carry durable identity:

```text
ComponentSpec.catalog_ref = { family, sku }
```

Continuity / ERF / DSE (catalog path) already *know* about bound SKUs in specialized surfaces.

**BOM does not yet “consume” that identity as a first-class procurement fact.**

Today `build_component_bom` produces light buckets:

```text
defined / incomplete / missing / declarative
```

Each entry exposes roughly: `key`, `name`, `completeness`, `missing_fields`, `component_type` — **no** `catalog_ref`, **no** quantity from `motor_count`, **no** resolved vs unresolved SKU status, **no** Create→BOM handoff narrative.

**Symptom (CLI walk `autonomia-5540bda0ac16`):** architecture 4/4, Catalog PASS, BOM PASS, hobbywing bound — user still has no deterministic “lista de piezas comprables” with SKU + qty. `estado` does not present a SKU BOM. Frankenstein post-G24 (`name=sunnysky`, `catalog_ref=None`) would still look like a named line item if BOM only reads `.name`.

**Impl D exit criterion (Design §6):**

> *Create/BOM consumes SKU identity (separate contract).*

### 0.2 Why now

Impl C closed the loop **SKU → physics → identity through catalog-native apply**. Engineer verdict: stop proving “Jarvis can hold a project”; next prove **BOM coherent from that project**. G24–G27 stay debt — must not expand this investigation into NL/requirements polish.

### 0.3 Ambiguity this investigation must resolve

“Create→BOM” has been used historically for **two** related ideas:

| Sense | Meaning |
|---|---|
| **A — SKU BOM surface** | BOM entries include `catalog_ref` / resolved SKU / qty / unresolved blockers |
| **B — Create handoff** | After `create_project` (or architecture close), Continuity/CTA steers user toward BOM completeness / SKU resolution |

Investigation must map **as-is** and recommend whether Impl D v1 is A-only, B-only, or A+thin-B — with explicit ★ for Engineer.

---

## 1. What Claude must investigate

### 1.1 As-is BOM pipeline audit (mandatory)

Trace every consumer of `build_component_bom` / `format_bom_lines` / BOM gaps.

| Step | File / symbol | Questions |
|---|---|---|
| BOM build | `project_closure.build_component_bom` | Exact entry schema; does it read `catalog_ref`? `motor_count`? |
| Classification | `classify_component` | Interaction with bound vs unbound motors |
| Format | `format_bom_lines` | What CLI/views show today |
| ERF | `engineering_readiness` BOM gaps / subsystem | What “BOM PASS” means without SKU |
| Continuity | `project_continuity` | How BOM incomplete drives `next_useful_step` |
| Views | `render_views` / CLI `estado` / startup context | Where BOM lines appear |
| Create | `actions/create_project.py` + post-create Continuity | Any Create→BOM handoff today? |

**Deliverable:** sequence diagram + table of BOM consumers + field-read matrix (`catalog_ref`, `name`, qty sources).

### 1.2 SKU identity gaps (data contract)

Enumerate concrete scenarios and honest BOM/UX for each:

| # | Scenario | BOM today | Expected for Impl D (propose) |
|---|---|---|---|
| A | Motors unbound, freeform name | ? | |
| B | Motors `catalog_ref` set, SKU in library | ? | line item with SKU + qty |
| C | `catalog_ref` set, SKU missing from library (G9-A D) | ? | |
| D | Frankenstein: `name=sku` but `catalog_ref=None` (post G24 apply) | ? | must not claim “bound SKU” |
| E | Battery freeform Wh only (no battery catalog_ref) | ? | |
| F | Battery `catalog_ref` set (if any path exists) | ? | |
| G | Propellers / ESC / FC — no catalog_ref by design today | ? | declared-only lines |
| H | `motor_count=6` with one motors ComponentSpec | ? | qty=6 vs qty=1 |

**Critical:** Scenario D must not be silently presented as a resolved SKU purchase line.

### 1.3 Quantity & line-item model

Investigate how quantity should be derived for v1:

- Motors: `properties.motor_count` / `current_parameters.motor_count`?
- Propellers: same as motor_count when aerial?
- ESC: 1 vs N (4-in-1 vs per-motor) — honest unknown vs invent?
- Battery / frame / FC / sensors: qty=1 default?

Propose a **minimal line-item schema** (fields only — no code), e.g.:

```text
{ key, display_name, catalog_ref?, sku_resolved: bool, quantity, status, missing_fields? }
```

### 1.4 Create→BOM handoff (sense B)

Audit post-create / post-architecture Continuity messages.

Answer:

1. Is there any existing “go to BOM” / procurement CTA?
2. What would a **thin** handoff look like without Conversation Engine?
3. Should Impl D v1 **defer** Continuity copy changes and only upgrade BOM data + formatting?

### 1.5 Relationship to ERF / ASSEMBLY READY

- Does SKU-unresolved motor (bound missing / underspec) already affect Catalog/BOM subsystems?
- Should Impl D add new gap types (e.g. `GAP-BOM-SKU-UNRESOLVED`) or reuse G9-A / existing BOM incomplete?
- **Do not** design G26 Requirements fixes here — only note interaction (“BOM SKU-complete ≠ ASSEMBLY READY while Requirements INCOMPLETE”).

### 1.6 Design options (mandatory — 2–3)

Propose options for Impl D v1 scope:

| Option | Scope | Pros | Cons |
|---|---|---|---|
| **A** | Extend `build_component_bom` entries with `catalog_ref` + qty + resolved flag; upgrade `format_bom_lines` / estado | Minimal; reuses authority | No Create handoff |
| **B** | A + Continuity CTA when architecture complete but SKU unresolved on propulsion | Better UX | Touches Continuity ranking |
| **C** | New `build_sku_bom` parallel to light BOM | Clear procurement list | Dual BOM risk — justify or reject |

**One option must be minimal; one must be most correct long-term.** Investigator recommendation required.

### 1.7 Out-of-family policy

Confirm v1 families:

- **In:** motors (required), battery **if** `catalog_ref` present  
- **Out:** propeller/ESC/frame/FC SKU catalogs (no Impl B bind for most) — declared lines only  
- Battery catalog pick UX (Impl C C3) — still deferred; BOM only *displays* identity if already bound

### 1.8 Test inventory + CLI probe sketch

List tests touching BOM / classify_component / ERF BOM / Continuity incomplete.

Propose future IC probes (do not implement):

```text
1) Bind motor SKU → estado/BOM shows sku + quantity
2) Unbound freeform motor → BOM does not claim catalog resolved
3) Post-G24 frankenstein (name set, catalog_ref None) → BOM honest (unresolved)
4) Architecture 4/4 + bound motor → BOM PASS still; SKU line visible
5) Regression: existing GAP-BOM-INCOMPLETE-* behavior unchanged for missing keys
```

### 1.9 Slice recommendation

Ordered slices for future IC (bullets only):

| Slice | Intent |
|---|---|
| D1 | BOM entry schema + catalog_ref/qty/resolved |
| D2 | format_bom_lines + estado/startup surfacing |
| D3 | Optional Continuity CTA (if ★ chooses B) |
| D4 | Tests + CLI probe |
| D5 | Docs / System Map edges (Cursor later) |

---

## 2. Scope boundaries

### In scope

- Full audit §1.1–1.9  
- Scenario matrix + line-item schema proposal  
- 2–3 design options + ★ decisions for Engineer  
- Explicit non-goals list (G24–G27, Phase 2, H5, Step D)

### Out of scope (do not implement)

- Any `src/` changes  
- Any new tests (investigation only)  
- Fixing G24–G27  
- Battery/propeller catalog pick UX  
- Phase 2 propulsion physics  
- Procurement vendor URLs / pricing  
- Conversation Engine / Step D  
- New architectural subsystem (no parallel “BOM Engine”)

---

## 3. Output format

Single artifact: `.jes/artifacts/investigation_report_impl_d_create_bom_sku.md`

Required sections:

1. Executive summary (≤15 lines)  
2. As-is BOM pipeline audit + consumer table  
3. Field-read matrix (`catalog_ref`, name, qty, …)  
4. Scenario matrix A–H with recommended UX  
5. Line-item schema proposal  
6. Create handoff (sense B) recommendation  
7. ERF / ASSEMBLY READY interaction notes  
8. Design options (2–3) + trade-offs  
9. Test inventory + CLI probe sketch  
10. Recommended approach  
11. ★ Decisions for Engineer (numbered)  
12. Suggested Implementation Contract outline (slices only)

---

## 4. Hard constraints for any future IC

- **ProjectState remains source of truth** — BOM is a pure projection.  
- **LLM never invents SKUs or quantities.**  
- **No second JSON catalog reader** — only `ComponentLibrary` / existing bind.  
- **Never present `catalog_ref=None` as a resolved purchasable SKU** (Scenario D).  
- **Prefer extending `build_component_bom`** over a parallel BOM authority unless investigation proves necessity.  
- **G24–G27 remain untouched** in Impl D implementation.  
- **Zero weakened tests.**

---

## 5. Acceptance (Cursor investigation review)

**PASS** if report answers §1, includes ≥2 options, scenario D handled honestly, and delivers actionable ★ + slices.  
**FAIL** if collapses into G26/G24 fixes, invents Conversation Engine, or proposes dual BOM without strong justification.

---

## 6. Queue after investigation

```text
Investigation PASS
        ↓
Engineer ratifies ★1–★N
        ↓
Cursor: implementation_contract_impl_d_create_bom_sku.md
        ↓
Claude implements → Cursor review → CLI → checkpoint-impl-d
```

---

**End of contract.**
