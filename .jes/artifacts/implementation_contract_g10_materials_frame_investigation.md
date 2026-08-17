# Implementation Contract — G10 Material Catalog / Frame Acquisition  
# Investigation + Design

**Project:** Jarvis  
**Date:** 2026-08-15  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** READY FOR ENGINEER → send to Claude  

**Type:** **Investigation + Design only.** Zero intentional product `src/` changes. No FN. No G8/G9/R3/R4. No Impl C. No Continuity rewrite.

**Checkpoint base:** tag **`checkpoint-g3`** (`a3b72b8`)  

**Finding:** G10 in `.jes/artifacts/cli_findings_post_catalog_bind_v1.md`  

**Depends on:**  
- `library/materiales/_datos.json` (8 materials)  
- `src/jarvis/domains/aerial.py` — `MATERIAL_MAP`, `extract_frame_properties`, frame `ComponentRule` keywords  
- `src/jarvis/knowledge/library.py` — `get_material` / `list_materials` / `has_material`  
- `src/jarvis/core/orchestrator.py` — `_handle_component_description` (FN-019 force for propellers; frame path)  
- `src/jarvis/core/iterate_interactive_session.py` — material iterate path + `_extract_material_from_text`  
- `src/jarvis/core/mutation_engine.py` — density ratio via library  
- Catalog design: `docs/PHYSICAL_COMPONENT_CATALOG_V1.md` (§ materials = densities; alias bug deferred as “3A”)  
- Prior CLI evidence: Engineer session 2026-08-15 (`plastico`/`PVC` rejected; `fibra de carbono 450g` OK)

**Workflow:**  
Claude investigates + drafts design → writes artifacts under `.jes/artifacts/` → Engineer locks ★ → Cursor reviews → **later cut:** Implementation Contract for G10 code.  
**No commit/push unless Engineer asks.**

---

## 0. Why this cut

G3 CLI PASS proved Goal Plan → explore continuity. The same session exposed a **non-motor catalog** failure:

```text
Frame wizard open
User > plastico 390g     → re-prompt (example only)
User > PVC 390g          → re-prompt
User > fibra de carbono 450g → OK
```

Cursor already confirmed (probe, not yet a design):

| Layer | Fact |
|---|---|
| Library | 8 materials including `plástico`, `pvc` |
| Frame keywords | `carbon`/`carbono`/`aluminio` — **not** `plastico`/`pvc` |
| `MATERIAL_MAP` | has `plastico`; **missing `pvc`** |
| FN-019-style force | exists for propellers; **absent for frame** |
| List query | `"qué materiales tenemos…"` → LLM, not `list_materials()` |

Catalog v1 design already said materials stay density-only and deferred “alias micro-fix” as 3A. G10 is larger: **misalignment of authority layers** for a physical family that is not motors. Engineer wants this understood **before Impl C**, because it teaches how non-motor catalog entities should enter acquisition / state / iterate.

```text
checkpoint-g3 ✅
        │
        ▼
G10 INVESTIGATION + DESIGN  ← you are here
        │
        ▼
Engineer locks ★ on design
        │
        ▼
G10 Implementation Contract (later) → impl → CLI → checkpoint-g10
        │
        ▼
R3 → R4/G8 · G9 (later) → Impl C
```

---

## 1. Intent

Produce an evidence-first package that answers:

1. **Full map** of every material-related authority path (acquisition, iterate, mutation, create_project default, Continuity display).  
2. **Root cause(s)** of the CLI rejection of library materials — confirm / refine Cursor’s three-layer picture with citations.  
3. **Canonical identity problem:** library Spanish names (`fibra de carbono`) vs acquisition English tokens (`carbon_fiber`) vs iterate extractors — is this dual-truth? Where does `get_material` break?  
4. **Design options** for a minimal G10 fix that:
   - makes every library material declarable in the frame wizard;
   - does not invent a Conversation Engine;
   - leaves a clean pattern for future battery/prop acquisition (Impl C adjacent);
   - explicitly does **not** “fix Continuity G9” in this workstream.
5. A **Design note** ready for Engineer ★ lock (recommended option + rejected alternatives + out-of-scope).

---

## 2. Source-of-truth order (mandatory)

```text
1. Code
2. Tests
3. Runtime / CLI evidence (transcript + optional probes)
4. Architecture / Catalog v1 design docs
5. Continuity / JES findings / prior reviews
```

If docs and code disagree → record in the investigation report (and optionally propose a MISMATCHES M-xxx text). **Do not** change product code to “make the design true” in this cut.

---

## 3. Out of scope (hard)

| Forbidden now |
|---|
| Any product `src/` / `library/` JSON edits |
| Implementing force-frame, expanding MATERIAL_MAP, or list-materials intent |
| G8 / R3 / R4 / G9 Continuity honesty fix |
| Catalog Impl C, battery/prop SKU UX, BOM |
| Conversation Engine / Step D / dual-dispatch refactor |
| Expanding materials SKU catalog into “frame SKUs” (deferred by Catalog v1) |
| Weakening tests |
| Commit / push unless Engineer asks |

**Allowed doc-only (optional, prefer report-first):**  
- Clarifying notes inside the design artifact.  
- Do **not** rewrite `PHYSICAL_COMPONENT_CATALOG_V1.md` unless Engineer later absorbs the CLOSED design.

---

## 4. Part A — Investigation checklist

Claude must verify against code (file + symbol; line numbers preferred). Status per item: `CONFIRMED` | `REFINED` | `NEW FINDING` | `NEEDS ENGINEER`.

### 4.1 Library surface

| # | Check |
|---|---|
| A1 | Exact contents of `library/materiales/_datos.json` (names + densities) |
| A2 | `_normalize_name` behavior (accents: `plastico` vs `plástico`) |
| A3 | `get_material` / `list_materials` / `has_material` callers across `src/jarvis/` |
| A4 | Which callers pass Spanish library names vs English acquisition tokens? |

### 4.2 Acquisition / frame path

| # | Check |
|---|---|
| A5 | Frame `ComponentRule` keywords — complete list; why `plastico` misses |
| A6 | `MATERIAL_MAP` vs library — full gap table (alias present / absent / canonical stored) |
| A7 | `extract_frame_properties("plastico 390g")` vs `infer_component` vs `infer_component_for_key(..., "frame")` |
| A8 | `_handle_component_description` when `expected_keys == ["frame"]`: prove generic reject + re-prompt (mirror FN-019 propeller force — cite propeller branch and absence for frame) |
| A9 | What canonical string is written by `set_frame_material` for carbono / plástico / aluminio? |

### 4.3 Iterate / mutation path

| # | Check |
|---|---|
| A10 | `_extract_material_from_text` vocabulary vs `MATERIAL_MAP` vs library |
| A11 | `mutation_engine.apply_material_mutation` — does it require library names? Failure mode if state holds `carbon_fiber`? |
| A12 | Create-project default material (`aluminio`) — consistent? |

### 4.4 Query / Continuity

| # | Check |
|---|---|
| A13 | Is there **any** deterministic path that lists materials to the user? (intent, help, acquisition brief) |
| A14 | What does Continuity / startup context show as “material estructural”? |
| A15 | Confirm G10 ≠ G9 (no shared symbols that would force a joint fix) |

### 4.5 Mandatory probes (diagnostic only — PreferLLM refuse / scratchpad OK)

| # | Probe | Intent |
|---|---|---|
| P1 | `list_materials()` names | Ground truth library |
| P2 | For each library name: `extract_frame_properties(f"{name} 400g")` + `infer_component` + `infer_component_for_key(..., "frame")` | Coverage matrix |
| P3 | Forced DEFINE_MISSING frame session + `"plastico 390g"` / `"pvc 390g"` / `"fibra de carbono 450g"` | Reproduce CLI |
| P4 | If state has `material=carbon_fiber`, call `get_material` / iterate material change | Dual-name hazard |
| P5 | `"qué materiales tenemos en el catálogo?"` via orchestrator (RefuseLLM) | Prove LLM fallback |

Report raw matrices in the investigation artifact.

---

## 5. Part B — Design (draft for Engineer ★ lock)

### 5.1 Engineer preferences (stress-test — not yet CLOSED)

Treat as preferences to validate or challenge:

1. **Library is the vocabulary authority** for which materials exist (`list_materials` / JSON). Acquisition aliases must cover **every** library entry (plus reasonable ES/EN variants).  
2. Prefer **one canonical stored identity** (decide: library Spanish key **or** stable slug). Dual-truth `carbon_fiber` in state vs `fibra de carbono` in library is a liability — design must pick a resolution.  
3. When frame wizard is open (`expected_keys` includes `frame`), reuse the **FN-019 pattern**: if inference is generic, force `infer_component_for_key(..., "frame")` — do not invent a second parser.  
4. Optional but valued: deterministic **list materials** help when user asks what is available (0 LLM) — keep narrow (materials family only), not a general “catalog browser”.  
5. Do **not** expand into frame SKU catalogs or Impl C. Densities-only role from Catalog v1 stays.  
6. Do **not** fold G9 Continuity motor-gap honesty into G10.

### 5.2 Options Claude must compare

At minimum evaluate:

| Option | Sketch |
|---|---|
| **O1 — Alias + force-frame only** | Expand keywords/`MATERIAL_MAP` to library; add FN-019-style force for frame; leave stored canonical as today |
| **O2 — Library-canonical** | Store library names in `ComponentSpec`; map aliases → library keys; migrate/normalize English tokens |
| **O3 — Slug-canonical** | Introduce stable slugs (`carbon_fiber`, `pvc`, …) in JSON + acquisition; library display names separate |
| **O4 — List-only + aliases** | Deterministic list intent + alias fix; skip force-frame if aliases alone suffice (argue with P2/P3) |

Recommend **one** primary option (+ optional small add-ons). Reject others with one-line reasons.

### 5.3 Design must specify (for later Implementation Contract)

- Canonical identity rule (what string lands in `components["frame"].properties["material"]`).  
- Alias ownership module (single source — no third copy in iterate if avoidable).  
- Force-frame: yes/no + exact mirror of FN-019 gates.  
- List-materials: yes/no + intent surface + authority (`list_materials` only).  
- Test plan sketch (acquisition matrix + iterate/mutation dual-name).  
- Explicit non-goals (G9, Impl C, frame SKUs).  
- Blast radius (files likely touched in impl cut).

### 5.4 Catalog v1 / Impl C implications (one section)

Answer briefly:

> What pattern does G10 establish that battery/prop acquisition should copy later — and what must **not** be generalized yet?

---

## 6. Deliverables (required)

### 6.1 Investigation report (mandatory)

**Path:** `.jes/artifacts/investigation_g10_materials_frame.md`

Must include:

1. Executive verdict (≤10 lines)  
2. Layer map (library ↔ MATERIAL_MAP ↔ keywords ↔ writers ↔ iterate/mutation)  
3. CLI root-cause reconstruction (turn path for `plastico 390g`)  
4. Coverage matrix (P2)  
5. Dual-name / canonical hazard (A4/A9/A11/P4)  
6. G10 vs G9 / Design 3A boundary  
7. Risks for a naive alias-only patch  

### 6.2 Design note (mandatory)

**Path:** `.jes/artifacts/design_g10_materials_frame.md`

Must include:

1. Status line: `OPEN — awaiting Engineer ★ lock`  
2. Recommended option (O1–O4 or refined hybrid)  
3. ★ decisions to lock (numbered, Engineer can ★ each)  
4. Rejected alternatives  
5. Implementation blast radius + test sketch  
6. Out of scope  
7. Relation to Catalog v1 § materials / “3A”  

Do **not** mark CLOSED yourself — Engineer locks ★.

### 6.3 Explicit non-deliverables

- No Implementation Contract for code (that is the **next** cut after ★)  
- No `src/` changes  
- No checkpoint tag  

---

## 7. Pass criteria (Cursor review)

| # | Criterion |
|---|---|
| 1 | CLI `plastico`/`pvc` failure explained with code citations |
| 2 | Coverage matrix covers all library materials |
| 3 | Canonical dual-name hazard proven or refuted with probes |
| 4 | FN-019 propeller force vs frame absence cited |
| 5 | Design recommends one option + ★ list for Engineer |
| 6 | G9 / Impl C / R3 explicitly out of scope in design |
| 7 | Zero product code changes |
| 8 | Catalog v1 implications section present |

**Grades:** PASS / PASS WITH NOTES / FAIL.

---

## 8. Suggested Claude working order

```text
1. Read this contract + G10 finding + Catalog v1 materials paragraph
2. Map A1–A15 with citations
3. Run probes P1–P5
4. Write investigation_g10_materials_frame.md
5. Draft design_g10_materials_frame.md (OPEN)
6. STOP — do not implement
```

---

## 9. Handoff back to Engineer

Closing message must contain:

```text
VERDICT: <one sentence on root cause>
INVESTIGATION: .jes/artifacts/investigation_g10_materials_frame.md
DESIGN: .jes/artifacts/design_g10_materials_frame.md (OPEN — ★ pending)
RECOMMENDED OPTION: <O1|O2|O3|O4|hybrid>
NEXT: Engineer ★ lock → G10 Implementation Contract
CODE CHANGES: none
```
