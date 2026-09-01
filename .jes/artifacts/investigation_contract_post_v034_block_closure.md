# Investigation Contract — Post-v0.3.4 Block Closure Capability

**Project:** Jarvis  
**Date:** 2026-09-01  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output:** `.jes/artifacts/investigation_report_post_v034_block_closure.md`

**Status:** READY FOR CLAUDE

**Type:** Architecture + product investigation — determine **which work blocks Jarvis can currently close end-to-end with explicit guarantees**, which **existing signals are sufficient** to support closure, and **what architectural/product contract is missing** where closure cannot yet be honestly claimed. **Not** an implementation plan. **Not** a decision to add a new subsystem.

**Checkpoint base:** tag **`v0.3.4`** / **`checkpoint-motor-op-voltage-coherence`** · commit `a563fe7`

**Prior arcs (CLOSED — do not re-open without regression proof on v0.3.4):**

| Delivered @ v0.3.4 | Scope |
|---|---|
| **Motor OP Voltage Coherence** | MOP-1 exact OP requires voltage; MOP-2 conditional battery re-resolve; MOP-3 DSE live-params baseline; MOP-4 explore honesty line |
| **Validation Case regression gate** | Probe + doc; ★6 narrative locked |
| **Project Closure IC 1–3** | Requirements; battery catalog UX + G27; propeller `sku_resolved` display |
| **P2-1 / P2-2** | `resolve_operating_point` + `motor_op_*` bridge |
| **G24-A/C/D** | Apply-by-index; viable CTA; frankenstein `.name` |
| **ERF-1 / ERF-2** | `engineering_readiness` + electrical gaps |

**Still frozen (hypotheses only — do not implement in this investigation):**

| ID | Topic |
|---|---|
| **H5** | ESC catalog / C-081 margin thread |
| **G24-B** | `_score_candidate` rewrite |
| **FN-R** | Acquisition/routing UX (field walk `autonomía-15-min`) |
| **Battery/ESC data curation** | Real-test data beyond spec sheets (★7) |
| **C-108 Slice 4b** | Full readiness → Continuity handoff |

**Design authority (read-only — context, not proof):**

- [`docs/ENGINEERING_READINESS_VISION.md`](../../docs/ENGINEERING_READINESS_VISION.md) — §11 Assembly Ready v1; Snapshot A/B
- [`docs/system_map/CONNECTIONS.md`](../../docs/system_map/CONNECTIONS.md) — C-081, C-108 partials
- [`.jes/artifacts/investigation_report_project_closure_assembly_ready.md`](investigation_report_project_closure_assembly_ready.md)
- [`.jes/artifacts/investigation_report_validation_case_post_v032.md`](investigation_report_validation_case_post_v032.md)
- [`.jes/artifacts/investigation_report_dse_motor_op_dual_truth.md`](investigation_report_dse_motor_op_dual_truth.md) — closed @ v0.3.4

**Engineer framing (2026-09-01, post-checkpoint) — locked:**

```text
v0.3.4 is the stable baseline. No code until this investigation + explicit ★.

Core question:
  Which work blocks can Jarvis close end-to-end with explicit guarantees today,
  and what contract (if any) is missing where closure cannot be honestly claimed?

Critical distinction (must not collapse):
  ASSEMBLY_READY  ≠  PROPULSION_ENERGY_STACK CLOSED
  (global rollup     vs   block-level closure)

Three layers (investigate separately):
  1) System can execute the flow
  2) System can demonstrate specific conditions hold
  3) System has an explicit contract allowing a block to be declared closed

Hypothesis to VERIFY (do not assume):
  Existing signals (components + readiness + electrical_compatibility +
  operating_point + simulation + BOM/provenance) may already suffice to DERIVE
  block closure — and the gap may be rollup semantics + UX only, not a new
  BLOCK_STATUS subsystem.

Parallel question (Gate F — see §2):
  Should Catalog Foundation (families, data schema, representative SKUs,
  evidence tiers, combo fixtures) be prioritized BEFORE or IN PARALLEL with
  block-closure conclusions? Investigation must decide with evidence, not assume.
```

**Do NOT implement any candidate in this investigation.**  
**Do NOT bump `pyproject.toml` version.**  
**Do NOT weaken tests or fake PASS / CLOSED states.**  
**Do NOT pre-decide that a new `BLOCK_STATUS` enum or subsystem is required.**

**Workflow:** Investigate → report → Engineer ★ → (optional) IC contract(s) → implement → review → probe → checkpoint.

---

## 0. Intent

After Motor OP Voltage Coherence @ v0.3.4, Jarvis can **execute** a catalog-bound propulsion stack path (motor → propeller → battery → calc → sim → readiness rollup) with **honest** OP voltage coherence and electrical gap detection.

What is **not yet established**:

> Can Jarvis **declare a specific work block closed** — with explicit guarantees about compatibility, physics, traceability, and reproducible UX — or does it only reach **project-level `ASSEMBLY_READY`** without answering "have I finished working on this block?"

This investigation maps **block closure capability** against **existing architecture**. It may conclude that:

- (A) closure is already derivable from existing signals + a missing rollup/UX contract only; or  
- (B) catalog/data foundation must precede honest block closure; or  
- (C) specific frozen items (H5, FN-R, C-108, …) are **blocking** vs **enhancing** closure; or  
- (D) a new explicit block-closure authority is genuinely required.

The report must **not** assume (A)–(D) in advance.

---

## 1. Methodology lock (★ — non-negotiable)

| ★ | Rule |
|---|---|
| **★1** | **Code + tests + probes first.** Every claim cites `file:line`, named test, probe step, or artifact path on baseline `a563fe7` / tag `v0.3.4`. Vision docs and prior reports are **context only**. |
| **★2** | **No invented SKUs or fabricated closure.** Use only library rows that exist on baseline, or document fixture gaps explicitly. |
| **★3** | **Separate scope boxes** — Block closure ≠ Catalog Foundation ≠ H5 ≠ G24-B ≠ FN-R ≠ Motor OP. Do not collapse into one mega-IC recommendation. |
| **★4** | **Do not reopen** closed arcs (Motor OP, Closure IC 1–3, G24-A/C/D, P2-2 Option A) without **new regression** on v0.3.4. |
| **★5** | **Recommend ordered next steps** (+ explicit deferrals). No mega-IC. Distinguish **IC-shaped** vs **data-curation** vs **docs-only**. |
| **★6** | **Mandatory output table (§5)** — every cell must cite evidence. **`?` forbidden** — use `YES` / `NO` / `PARTIAL` + evidence pointer, or `N/A` with reason. |
| **★7** | **Do not infer closure from ASSEMBLY_READY alone.** Trace each guarantee separately. |
| **★8** | **Evidence strength taxonomy (Gate C)** — `manufacturer_test` ≠ `spec_sheet` ≠ `fallback` ≠ `derived` ≠ `declared/freeform`. Never upgrade strength by prose. |
| **★9** | **Catalog Foundation is a parallel hypothesis (Gate F).** Report must answer whether block-closure conclusions are **invalid or unstable** on current catalog size — not assume catalog expansion fixes closure. |

---

## 2. Investigation gates (must answer in report)

### Gate A — Existing closure capability

For a **reference case** (minimum):

```text
motor SKU (catalog-bound)
+ propeller SKU (catalog-bound)
+ battery SKU (catalog-bound)
+ ESC declared (freeform — no ESC catalog on baseline)
```

Determine whether this case can **actually** reach each step on v0.3.4, with **exact evidence at each hop**:

```text
catalog-bound
  → OP voltage coherent (MOP-1/2)
  → electrical_compatibility checks
  → calculation (autonomy / power coherent with OP)
  → simulation PASS (under declared conditions)
  → subsystem PASS (propulsion, energy, electronics, catalog, bom)
  → zero HIGH gaps
  → ASSEMBLY_READY
```

**Deliver:** step-by-step trace table (command or programmatic path + artifact). Include at least **one compatible** and **one intentionally incompatible** combo if library permits (e.g. discharge exceeded, prop-motor mismatch).

**Also trace:** what happens when combo is **incompatible** — does the system **honestly refuse closure** (INCOMPATIBLE / HIGH gap) or silently pass?

---

### Gate B — Meaning of "closed"

Answer:

> What does it mean, **technically**, for a work block to be **closed**?

Map current code concepts against this **proposed vocabulary** (report may refine labels, but must address each):

| Concept | Investigation must define using code evidence |
|---|---|
| **DECLARED** | Component/spec present with non-low completeness |
| **VALIDATED** | Physics/sim or explicit validation authority satisfied |
| **COMPATIBLE** | Electrical / prop-motor / discharge checks pass |
| **SIM_PASS** | Latest simulation viable under declared conditions |
| **READY** | Subsystem or project readiness verdict |
| **CLOSED** | Block-specific: user can stop working on this block with justified confidence |

**Required finding:** List every place two or more of these concepts are **currently conflated** (e.g. `ASSEMBLY_READY` used as if it meant propulsion stack closed). Cite code.

**Required finding:** Is **`ASSEMBLY_READY`** sufficient for any block-level closure claim today? **Yes/No + proof.**

---

### Gate C — Evidence strength

Classify what the reference case (Gate A) actually provides at each claim:

| Tier | Meaning (baseline) |
|---|---|
| `manufacturer_test` | Curated OP row / ★6-style sourced test data |
| `spec_sheet` | SKU fields (`c_rating`, `max_watts`, …) without test OP |
| `fallback` | `resolve_operating_point` fallback branch |
| `derived` | Heuristic / calc output (e.g. estimated mass) |
| `declared/freeform` | User text, no catalog_ref |

For each block-level claim the system **could** make (compatible, physically validated, procurement-ready), state **maximum honest tier** supported today.

**Explicit:** `fallback` ≠ `manufacturer_test`. `ASSEMBLY_READY` with Snapshot A freeform ≠ Snapshot B catalog-evidence-strong.

---

### Gate D — Preconditions for closure (blocking vs enhancing)

For each candidate, classify **BLOCKING** (honest block closure impossible without it) vs **ENHANCING** ( improves closure once block is otherwise closable) vs **UNRELATED**:

| Candidate | Question |
|---|---|
| ESC catalog (H5) | Required for propulsion/energy block closure, or only for electronics SKU traceability? |
| Battery real-test data curation | Required for "compatible" claim, or spec_sheet sufficient for MVP closure? |
| OP coverage density | Required for closure, or fallback-honest closure acceptable? |
| Viable combo pre-selection (G24-C territory) | Required for closure, or post-hoc detection sufficient? |
| FN-R routing UX | Blocks backend closure capability, or only UX path to reach it? |
| C-108 readiness → Continuity | Blocks closure verdict, or only next-step copy? |
| DSE ↔ component sync (G1) | Blocks declaring propulsion/energy closed after DSE apply? |
| C-081 sim margin → Continuity | Blocks any block closure, or Continuity polish only? |

**No default answers.** Each row needs evidence.

---

### Gate E — Closure UX

Assume Gate A demonstrates **sufficient backend evidence exists** for at least one reference case.

> Can a user **reproducibly reach** that closed state via CLI (deterministic path, no LLM)?

Trace minimum paths:

- Greenfield: create → arch → motor pick → prop pick → battery pick → calcular → estado  
- Re-open: gap fired (e.g. discharge exceeded) → is there a **deterministic re-bind / fix path**?  
- Architecture 4/4: `definir battery` / `definir propellers` — catalog re-bind or wizard-only? (FN-R1)

**Deliver:** UX closure matrix — backend-can-close vs user-can-reach-closure.

---

### Gate F — Catalog Foundation dependency (parallel hypothesis)

Answer with evidence:

> Should the next phase prioritize **Catalog Foundation** (family contracts, required fields per family, small representative SKU set, combo fixtures, evidence tiers) **before** declaring block-closure ICs?

Sub-questions:

1. What families does Jarvis **conceptually** need today (motor, prop, battery, ESC, frame, FC, …)? Cite `system_architecture_catalog`, readiness subsystems, acquisition prompts — not wishlist.  
2. Per family: minimum fields for **calc**, **compatibility**, **readiness**, **DSE** — which exist vs missing in schema/library?  
3. How many SKUs per family are ** sufficient to exercise rules** (not "catalog the world")?  
4. Are current block-closure conclusions ** unstable** because catalog has ~22 motors / ~16 props / ~10 batteries — i.e. investigation conclusions would change materially with 5–10 more SKUs per family?  
5. Recommend: **Catalog Foundation investigation first** / **Block Closure first** / **parallel with explicit dependency edge** — one primary + rationale.

**Do not** recommend cataloging 100+ components. **Do** recommend minimum representative set if data gap is blocking.

---

## 3. Work blocks under review (mandatory table)

Investigator must evaluate **at minimum** these blocks:

| Block ID | Scope (investigation framing) |
|---|---|
| **B-REQ** | Requirements / mission constraints (IC 1) |
| **B-ARCH** | Architecture 4/4 declaration completeness |
| **B-PROP-ENERGY** | Motor + propeller + battery + ESC stack (primary reference case) |
| **B-BOM** | BOM / procurement identity / `sku_resolved` honesty (Impl D, G24D) |
| **B-DSE** | Explore/apply coherence for optimization block |
| **B-CONT** | Continuity next-step / risk thread (C-081, C-108) |

Report may add blocks if evidence supports (e.g. **B-ELEC** electronics-only), but not fewer.

---

## 4. Mandatory output table (§5 — no inference)

Report **must** include this table. Every cell: **`YES` / `NO` / `PARTIAL` / `N/A`** + evidence (test name, probe step, `file:line`, or "not attempted — reason").

| Block | Can close today? | Evidence tier reached | Physical guarantee | Traceability | UX closure | Missing contract |
|---|---|---|---|---|---|---|
| Requirements (B-REQ) | | | N/A | | | |
| Architecture (B-ARCH) | | | N/A | | | |
| Propulsion/Energy (B-PROP-ENERGY) | | | | | | |
| BOM/Procurement (B-BOM) | | | | | | |
| DSE (B-DSE) | | | N/A | | | |
| Continuity (B-CONT) | | | N/A | | | |

**Column definitions:**

- **Can close today?** — Honest block-level closure claim supportable on v0.3.4 (not ASSEMBLY_READY alone).  
- **Evidence tier reached** — Highest tier from Gate C actually achieved in reference trace.  
- **Physical guarantee** — Compatibility + sim coherence for physical blocks; N/A where not applicable.  
- **Traceability** — Catalog/provenance/BOM honesty for procurement-relevant blocks.  
- **UX closure** — User can reach closed state reproducibly via CLI.  
- **Missing contract** — One sentence: what authority/rollup/UX is absent (may be "none — derivable from X").

---

## 5. IN SCOPE

| # | Work |
|---|---|
| 1 | Baseline verification on `a563fe7` — suite count + relevant probes (P2-2, battery, DSE motor OP, closure, requirements) |
| 2 | Gate A–F traces with file:line citations |
| 3 | Gate A reference case — programmatic + optional CLI probe sketch (investigation may add `scripts/cli_probe_block_closure_capability.py` **only if** it clarifies Gate A/E — not required for PASS) |
| 4 | Mandatory output table (§4) fully populated |
| 5 | Concept map (Gate B) — DECLARED / VALIDATED / … vs current code symbols |
| 6 | Blocking vs enhancing matrix (Gate D) |
| 7 | Catalog Foundation dependency recommendation (Gate F) |
| 8 | **One primary recommended next arc** (+ ordered alternates + explicit deferrals) |
| 9 | Optional: draft outline for **separate** `investigation_contract_catalog_foundation.md` if Gate F recommends it — **outline only, not a second investigation report** |

---

## 6. OUT OF SCOPE

- Implementing block closure, `BLOCK_STATUS`, catalog expansion, H5, G24-B, FN-R fixes  
- Version bump / checkpoint / tag  
- Reopening Motor OP, P2-2 semantics, Closure IC 1–3, G24-A/C/D without new regression  
- Mega-catalog data entry (hundreds of SKUs)  
- Conversation Engine / Step D  
- Weakening tests or marking blocks CLOSED without evidence  
- Assuming Catalog Foundation **must** precede Block Closure IC — that is Gate F output  

---

## 7. Deliverables

1. **Investigation report** — `.jes/artifacts/investigation_report_post_v034_block_closure.md`  
   - Executive summary (≤15 lines)  
   - Gates A–F answered  
   - Mandatory table (§4)  
   - Primary recommendation + ★ ratification questions for Engineer  
2. **Baseline table** — suite + probe results on `a563fe7`  
3. **Optional repro** — programmatic trace test e.g. `tests/test_block_closure_capability_investigation.py` (xfail/skip allowed **only** for documenting "cannot reach step X" — must explain)  
4. **Optional probe** — `scripts/cli_probe_block_closure_capability.py` if CLI path is material to Gate E  

**No production fix in this contract.**

---

## 8. Acceptance (Cursor review)

| Verdict | Criteria |
|---|---|
| **PASS** | All gates answered; mandatory table fully evidenced (no `?`); ASSEMBLY_READY vs block-closed distinction explicit; one bounded primary recommendation; Gate F answered |
| **PASS WITH NOTES** | Gate E UX trace incomplete but A–D + table solid for B-PROP-ENERGY |
| **FAIL** | Table cells filled by inference; conflates ASSEMBLY_READY with block closure; pre-decides new subsystem without verifying derivability; implements fixes |

---

## 9. Suggested investigation order

```text
1. Baseline verify (suite + probes @ v0.3.4)
2. Gate B — vocabulary / conflation map (read codebase first)
3. Gate A — reference case trace (compatible + incompatible)
4. Gate C — evidence tiers on reference case
5. Gate D — blocking vs enhancing matrix
6. Gate E — UX paths on same cases
7. Gate F — catalog size / schema / fixture stability
8. Fill mandatory table (§4)
9. Primary recommendation + Engineer ★ questions
```

---

## 10. Engineer ★ questions (report must surface — do not answer without evidence)

| ★ | Question |
|---|---|
| **★1** | Is block-level closure **derivable** from existing signals + rollup/UX contract, or is a new authority required? |
| **★2** | Is **B-PROP-ENERGY** closable today at Snapshot B evidence tier with honest COMPATIBLE + SIM_PASS claims? |
| **★3** | Which Gate D items are **blocking** vs **enhancing** for B-PROP-ENERGY? |
| **★4** | Next arc priority: **Block Closure IC** / **Catalog Foundation investigation** / **FN-R** / **H5** / **C-108** — one primary, others deferred. |
| **★5** | If Catalog Foundation goes first: minimum SKU count per family and minimum combo fixtures — propose numbers with rationale. |
| **★6** | Accept **fallback-honest** closure for propulsion OP where no manufacturer_test row exists, or require evidence upgrade before "closed"? |

---

## 11. Relationship to parallel Catalog Foundation track

This contract **does not replace** a potential future:

```text
investigation_contract_catalog_foundation.md
```

If Gate F recommends Catalog Foundation first, the block-closure report should:

- State **exactly which §4 table cells** would change after a bounded catalog expansion  
- **Not** assume expansion automatically enables closure (UX/rollup may still be the gap)

Both investigations may run **in parallel** if Engineer approves — but **one primary sequencing recommendation** is required in the block-closure report.

---

## 12. Post-investigation workflow (not part of this contract)

```text
v0.3.4 ✅
      ↓
Block Closure Investigation (this contract)
      ↓
Engineer ★
      ↓
Optional: Catalog Foundation Investigation (separate contract if ★4/★5 say so)
      ↓
IC(s) — bounded; no mega-IC
      ↓
checkpoint
```

Frozen until ★: H5 · G24-B · FN-R implementation · battery/ESC bulk curation.
