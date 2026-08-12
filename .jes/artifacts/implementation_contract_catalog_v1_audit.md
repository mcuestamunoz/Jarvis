# Implementation Contract — Physical Component Catalog v1 AUDIT

**Project:** Jarvis  
**Date:** 2026-08-12  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** READY FOR ENGINEER → send to Claude  

**Type:** **Audit + design stress-test only.** No product code. No new JSON SKUs. No DSE/calc/orchestrator changes. No System Map status flips unless a **documentation mismatch** is proven (doc-only, listed explicitly).  

**Checkpoint base:** tag `v0.2.0` / `checkpoint-fn026-h4` · H1–H4 closed · System Map **59 · 58🟢 · 0🔴 · 1🟡 (C-081)**  

**Explicitly deferred (do not implement, do not “fix”):**  
H5 / C-081 · Create→BOM · Catalog-constrained DSE · Conversation Engine / Step D · dual-dispatch refactor · inventing 10k SKUs  

**Workflow:** Claude audits → writes **one** report under `.jes/artifacts/` → Engineer + Cursor review → **then** (later cut) Design note CLOSED + detailed Implementation Contract(s) for Catalog Foundation.  
**No commit/push unless Engineer asks.**

---

## 0. Why this cut (read carefully)

Handoffs Plan → DSE / Iterate are closed. The CLI field probe showed a **new frontier**:

> Jarvis iterates abstract parameters well, but Continuity already says things like:  
> *“no tengo un motor en el catálogo que cubra ese espacio.”*  
> The next leap is **physical / buildable configurations**, not more conversational FNs.

Before we write a fat implementation contract, we need Claude to:

1. **Stress-test the Engineer vision** (below) against the **real codebase** — what we are missing, over-scoping, or contradicting.  
2. **Audit every connection** (existing `C-xxx` + proposed new edges) that a Physical Catalog would touch.  
3. Leave a **connection map + risk register** so Cursor can draft a precise Design → Impl A/B/C/D sequence.

```text
v0.2.0 (H1–H4 done)
        │
        ▼
CATALOG-V1-AUDIT  ← you are here (report only)
        │
        ▼
Engineer + Cursor: Design note CLOSED
        │
        ▼
Implementation Contract(s) — Catalog Foundation → Bind → (later) DSE → BOM
```

---

## 1. Engineer vision (normative input — not yet a CLOSED design)

Treat the following as the **proposed product direction**. Your job is to validate, challenge, and map it — **not** to invent a parallel architecture.

### 1.1 Problem

Today engineering runs mostly on **abstract continuous parameters**:

```text
motor_count, per_motor_max_thrust_n, battery_capacity_wh, propeller_diameter_in, …
```

DSE explores synthetic grids (×1.5 thrust, 800 Wh, …).  
That proves the **architecture**. It does **not** answer:

> “What drone can I actually build with real parts?”

### 1.2 Target shift

```text
COMPONENTE ABSTRACTO  →  COMPONENTE FÍSICO REAL (SKU)
```

Catalog becomes a **constraint and identity layer**, eventually feeding:

```text
Catalog → bind/resolve → current_parameters → calc → sim → (later) DSE over buildable configs → BOM
```

### 1.3 Proposed v1 families (Engineer preference)

| In v1 design scope | Deferred |
|---|---|
| **Motors** (enrich existing ~20 SKUs) | ESC as full SKU family |
| **Batteries** (new) | Frames as SKU catalog |
| **Propellers** (new, with motor↔prop compat) | 10k-part dump |
| Materials densities (keep) | H5 Continuity rewrite |

### 1.4 Proposed fidelity (Engineer preference)

- Not only `KV` + single `thrust_n`.  
- Prefer ability to represent **operating data** over time, e.g.:

```text
Motor (+ Prop + Voltage) → RPM / thrust / current / power / efficiency
```

- Batteries: real energy + **mass** + voltage/cells + current limits (as available), not only “I want 800 Wh” with a 150 Wh/kg heuristic.  
- v1 may allow **optional** `operating_points[]`; empty tables → honest fallback to nominal point (do **not** invent curves).

### 1.5 Proposed depth phasing (Engineer preference — challenge if wrong)

| Phase | Intent |
|---|---|
| **Design** | Authority + schema + connection map (after this audit) |
| **Impl A — Foundation** | `library/` + typed API + load/match/gap |
| **Impl B — Bind** | User-confirmed SKU → `ComponentSpec` + params; motor mass in calc; battery SKU mass/Wh |
| **Impl C — Catalog DSE** | Explore buildable SKU configs (mode or replacement of pure continuous grids) |
| **Impl D — Create→BOM / SKU BOM** | Consumer of catalog (after A/B stable) |

**Likely first code cut after design:** A (+ maybe thin B for motors only). Say so if A alone is incoherent.

### 1.6 Authority principles (must preserve)

| Rule | Meaning |
|---|---|
| Single JSON reader | Today: `knowledge/library.py` is the only reader of `library/**/_datos.json` — preserve or explicitly propose successor |
| Calc reads params | `calculation_engine` stays on `current_parameters` — catalog does not become a second physics truth |
| LLM never invents SKUs | Catalog rows are curated data; LLM may narrate, not fabricate motor specs |
| Honest gap | Pattern D8: if no SKU covers the requirement, say so — do not silently invent |
| No Conversation Engine | Routing stays deterministic |

---

## 2. Mandatory reading (before writing the report)

### Code / data

- `library/motores/_datos.json`, `library/materiales/_datos.json`
- `src/jarvis/knowledge/library.py` (`MotorSpec`, `MaterialSpec`, `find_motors_for_requirements`, D8)
- `src/jarvis/core/motor_catalog_assist.py`
- `src/jarvis/core/component_resolver.py`
- `src/jarvis/core/component_writers.py`
- `src/jarvis/core/calculation_engine.py` (thrust / battery mass / autonomy paths)
- `src/jarvis/core/design_explorer.py` (`EXPLORATION_GRIDS`, `COMPONENT_VARIATION_RULES`)
- `src/jarvis/core/project_closure.py` (BOM completeness — not SKU BOM)
- `src/jarvis/core/project_continuity.py` + orchestrator Continuity / `motor_catalog_gap` path
- `src/jarvis/domains/aerial.py` (declare extractors: motors, props, battery, ESC)
- `src/jarvis/core/system_architecture_catalog.py` (`COMPONENT_MIRRORED_PARAMS`, `BLOCK_TO_COMPONENTS`)
- `src/jarvis/schemas/action_schema.py` (`ComponentSpec`, `PropertyValue`)

### Docs / map

- `docs/system_map/README.md`, `CONNECTIONS.md`, `AUTHORITY.md`
- Subsystem maps likely touched: `04_engineering`, `05_iteration`, `06`/`07` if physics/sim, Continuity band, `10_llm` only as “must not invent SKUs”
- `docs/IMPLEMENTATION_TASKS.md` PRIORIDAD (Catalog v1)
- `README.md` v0.2 notes on thin library
- Debt **D8** (closed) references — do not reopen as “still KV-only” without checking code

### Field evidence

- Engineer CLI: Continuity `motor_catalog_gap` at ≥30 N/motor; DSE applying continuous thrust/Wh; autonomy apply → heavy battery mass → low_margin.

---

## 3. What you must produce

**Single report file:**

`.jes/artifacts/catalog_v1_connection_audit.md`

### Report structure (mandatory sections)

#### A. Vision stress-test

For each claim in §1, mark:

- **ALIGNED** — code can support this without architectural contradiction  
- **GAP** — missing piece; required for vision  
- **CONFLICT** — vision contradicts an existing authority or invariant  
- **OVERSCOPE** — too large for v1; split or defer  

Explicitly answer:

1. Are motors + batteries + propellers the right **minimum** v1 set? What breaks if ESC is deferred?  
2. Is “optional operating_points” enough, or does calc/DSE **require** tables to avoid lying?  
3. Is phasing A→B→C→D sound, or does Bind without Foundation (or DSE without Bind) create dual truths?  
4. Where does Create→BOM **actually** depend on catalog (edges), vs remaining a separate handoff?

#### B. Connection audit (the core deliverable)

Build a table of **every directed connection** involved in Catalog v1 — both:

1. **Existing `C-xxx`** from `CONNECTIONS.md` that Catalog will read/write/alter semantics of, and  
2. **Proposed new edges** (`C-1xx` candidates or labeled `PROPOSED-CAT-0xx` if ID allocation is unclear) that do **not** exist yet.

For each row:

| Field | Content |
|---|---|
| ID | `C-xxx` or `PROPOSED-…` |
| From → To | modules/layers |
| Today | what actually happens (evidence: file + function) |
| Catalog impact | none / read / write / replace / constrain |
| Risk if we add Catalog | dual truth, silent apply, stale Continuity, mass ignored, … |
| Needed before Impl A/B/C/D? | which phase |

Minimum areas to cover (add more if you find them):

```text
library JSON → ComponentLibrary API
ComponentLibrary → motor_catalog_assist / Continuity gap
assisted pick → ComponentSpec
ComponentSpec → component_writers → current_parameters
component_resolver → per_motor_max_thrust_n
calculation_engine ← params (thrust, battery mass, motor mass?)
design_explorer grids ↔ catalog (today: none)
declare/NL aerial extractors ↔ catalog (today: mostly bypass)
iterate / define_missing assisted motor path
materials library ↔ frame MATERIAL_MAP aliases
project_closure BOM vs future SKU BOM
DSE apply → state → Continuity re-read catalog gap
LLM analyze/interpret  (must remain non-authority for SKUs)
Create wizard params ↔ components (Create→BOM debt)
```

Also produce a **mermaid** diagram: Catalog-centric data flow **as-is** and a second diagram **proposed** for after Impl B (no code).

#### C. Dual-truth / authority hazards

List every place where Catalog v1 could create **two sources of truth**, e.g.:

- SKU thrust vs `per_motor_max_thrust_n` after DSE continuous apply  
- Battery SKU mass vs `estimate_battery_mass_kg(150 Wh/kg)`  
- Prop diameter in create params vs undeclared `propellers` component  
- Generic motors (`is_generic`) vs “real” SKUs in matching  

For each: recommend **one** authority rule (keep / bind-on-confirm / invalidate / forbid silent overwrite).

#### D. System Map impact estimate

- Which subsystem maps need updates when Catalog ships?  
- Estimated new `C-xxx` count (range), without assigning final IDs unless obvious.  
- Confirm **C-081 / H5** stays orthogonal (or note coupling if Continuity catalog-gap text is the only “risk thread” today).

#### E. Recommended Design CLOSED outline (draft only)

Propose the outline Cursor should write next in `docs/PHYSICAL_COMPONENT_CATALOG_V1.md`:

- Authority table  
- Schemas (motor / battery / prop) — fields **required vs optional**  
- Non-goals  
- Phase gates A/B/C/D with **exit criteria**  
- Open questions that **only the Engineer** can answer (max 5, sharp)

#### F. Explicit “we might be missing”

Free-form but concrete: physics model limits (Ct fixed, no ESC current bridge, motor weight unused, …), naming collisions (`system_architecture_catalog` vs physical catalog), test gaps, seed-data quality, i18n material names, etc.

#### G. Recommended scope for **Impl A — Catalog Foundation** (mandatory)

Cursor has a draft Foundation IC in mind (motors + batteries + propellers JSON + typed `ComponentLibrary` API + match/gap; **no** Bind, **no** DSE, **no** Create→BOM, **no** H5, **no** Continuity redesign).

Your job in this section: **confirm or correct that scope** against the codebase.

Produce a table:

| Item | Verdict | Why (file/evidence) |
|---|---|---|
| Enrich motors schema + keep D8 matching | IN A / OUT / SPLIT | … |
| New `library/baterias/_datos.json` + API | IN A / OUT / SPLIT | … |
| New `library/helices/_datos.json` + API | IN A / OUT / SPLIT | … |
| `match_motor_propeller` (IDs / inches only) | IN A / OUT / SPLIT | … |
| Extend Continuity gaps to battery/prop | IN A / OUT / SPLIT | … |
| Motor/battery mass into `calculation_engine` | IN A / OUT / SPLIT | … |
| Assisted pick → ComponentSpec (existing motor path) | IN A / OUT / SPLIT | … |
| Full Catalog Bind pipeline | IN A / OUT / SPLIT | … |
| Catalog-aware DSE | IN A / OUT / SPLIT | … |
| ESC / frame SKU families | IN A / OUT / SPLIT | … |
| Mandatory dense `operating_points` | IN A / OUT / SPLIT | … |
| Optional `operating_points[]` on schema only | IN A / OUT / SPLIT | … |

End section G with **one paragraph**: “Impl A should be …” (≤120 words) — the scope Cursor should lock into the Foundation IC after Design CLOSED.

---

## 4. Hard constraints

| Allowed | Forbidden |
|---|---|
| Read code/tests/docs | Modify `src/**` product behavior |
| Write the audit report | Add/edit `library/**/_datos.json` SKUs |
| Doc-only map typo fixes **only if** proven wrong and listed in report appendix | “Quick win” Bind / DSE / calc changes |
| Propose `PROPOSED-CAT-*` edges | Allocate final `C-xxx` IDs into `CONNECTIONS.md` without Cursor |
| Challenge Engineer vision with evidence | Expand scope to Conversation Engine / Step D / H5 implementation |

If you find a critical doc lie in the System Map about catalog/D8, you may fix **that one sentence** and list it under “Doc fixes applied”; prefer reporting over editing when unsure.

---

## 5. Acceptance criteria (for this audit cut)

- [ ] Report path exists: `.jes/artifacts/catalog_v1_connection_audit.md`  
- [ ] Section A marks each vision claim ALIGNED/GAP/CONFLICT/OVERSCOPE  
- [ ] Section B has a connection table covering all minimum areas + mermaid as-is + proposed  
- [ ] Section C lists dual-truth hazards with one authority recommendation each  
- [ ] Section D estimates System Map impact; H5 coupling called out  
- [ ] Section E gives a Design doc outline + ≤5 Engineer-only questions  
- [ ] Section F lists concrete misses  
- [ ] Section G recommends Impl A IN/OUT scope with evidence  
- [ ] **Zero** intentional product code changes  
- [ ] Full test suite still green if you touched nothing (no need to run if zero `src/` edits; if you edited docs only, note that)

---

## 6. Out of scope reminders

- Do **not** draft the full Implementation Contract for Impl A in this cut (section G scope table + section E outline are enough).  
- Do **not** start coding Catalog Foundation.  
- Do **not** reopen H1–H4.  
- Do **not** treat Create→BOM as the first catalog FN.

---

## 7. Handoff back to Cursor / Engineer

When the report is ready, Engineer forwards to Cursor. Cursor will:

1. Review the audit (PASS / PASS WITH NOTES / FAIL).  
2. Write `docs/PHYSICAL_COMPONENT_CATALOG_V1.md` (Design) incorporating accepted findings.  
3. Only then emit **Implementation Contract — Catalog Foundation (Impl A)** with file-level edits and tests — scope locked from section G.

---

## 8. Prompt to paste into Claude Code

> Execute Implementation Contract **Physical Component Catalog v1 AUDIT** from `.jes/artifacts/implementation_contract_catalog_v1_audit.md`.
>
> This is an **audit only** — zero product code, zero new SKUs, zero DSE/calc/Bind.
>
> Read the mandatory paths in §2 of the contract (library, `ComponentLibrary`, D8 assist, resolver, writers, calc, DSE, Continuity, aerial declare, System Map).
>
> Produce **one** report: `.jes/artifacts/catalog_v1_connection_audit.md` with sections **A–G** exactly as specified (vision stress-test, connection audit + mermaid, dual-truth hazards, System Map impact, Design outline, misses, **Impl A scope recommendation**).
>
> Challenge the Engineer vision where the codebase contradicts it. Do not invent a parallel architecture.
>
> **Do not commit or push.**
>
> Return the path of the report when done.

---

**End of contract.** Claude: audit connections and stress-test the vision; do not build the catalog yet.
