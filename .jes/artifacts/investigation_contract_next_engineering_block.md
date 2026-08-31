# Investigation Contract — Next Engineering Block (P2-2 vs G24 vs H5)

**Project:** Jarvis  
**Date:** 2026-08-31  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output:** `.jes/artifacts/investigation_report_next_engineering_block.md`

**Status:** READY FOR CLAUDE

**Type:** Comparative architecture + product investigation — determine **which candidate** (P2-2, G24, H5) should become the **next implementation arc**, with evidence from code/tests on baseline `73bd9fa`. **Not** an implementation plan. **Not** a version-bump decision (deferred until after Engineer ratifies direction).

**Checkpoint base:** tag **`checkpoint-closure-policy`** · commit `8728a85` · docs hygiene `73bd9fa`

**Design authority (read-only context — verify against code, do not treat as proof of pending work):**
- [`docs/PHYSICAL_PROPULSION_ENGINE_PHASE2.md`](../../docs/PHYSICAL_PROPULSION_ENGINE_PHASE2.md) — P2-1 delivered; §12.2+ vision
- [`docs/PHYSICAL_COMPONENT_CATALOG_V1.md`](../../docs/PHYSICAL_COMPONENT_CATALOG_V1.md) — design locks + §13 implementation status
- [`docs/ENGINEERING_READINESS_VISION.md`](../../docs/ENGINEERING_READINESS_VISION.md) §11 — Assembly Ready contract; deferred G24/H5
- [`docs/PROJECT_CONTINUITY.md`](../../docs/PROJECT_CONTINUITY.md) — Continuity authority (not readiness policy)
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) + [`docs/system_map/`](../../docs/system_map/README.md) — as-is

**Prior findings (read, re-verify in code — may be stale):**
- [`.jes/artifacts/cli_finding_g24_dse_apply_only_top1_catalog_unselectable.md`](cli_finding_g24_dse_apply_only_top1_catalog_unselectable.md)
- [`.jes/artifacts/investigation_report_phase2_physical_propulsion.md`](investigation_report_phase2_physical_propulsion.md) — P2-1 IC shape; P2-2 mentioned as future `resolve_operating_point` evolution
- [`.jes/artifacts/investigation_erf2_dependency_hardening.md`](investigation_erf2_dependency_hardening.md) — H5 ESC catalog deferred for ERF-2 MVP
- [`.jes/artifacts/implementation_report_impl_c_catalog_aware_dse.md`](implementation_report_impl_c_catalog_aware_dse.md) — G24 ranking residual context

**Prerequisites (CLOSED — do not re-open):**
- Project Closure arc IC 1–3 (`checkpoint-closure-policy`)
- Catalog V1 Impl A–D + live pick UX (motor / propeller / battery)
- P2-1 lookup OP (`checkpoint-phase2-p2-1`)
- ERF-1 + ERF-2

**Engineer decision (2026-08-31) — locked framing:**

```text
Do NOT assume P2-2 wins by default.

Next step = compare three candidates on baseline 73bd9fa:
  P2-2  — Phase 2 continuation (physics / OP / validation)
  G24   — DSE apply UX + catalog row selection
  H5    — ESC catalog + bind path

Investigation may conclude:
  "P2-2 is the next arc" OR "G24 first; P2-2 needs X" OR "H5 blocked until schema Y"
  — with code evidence, not priority intuition alone.

Version bump decision waits until Engineer ratifies the chosen direction.
```

**Do NOT implement any candidate in this investigation.**  
**Do NOT bump `pyproject.toml` version.**  
**Do NOT weaken tests or fake PASS states.**

**Workflow:** Investigate → report + comparison matrix → Engineer ★ → version decision → Cursor IC(s) → Claude implements → review → probe → checkpoint.

---

## 0. Context

### 0.1 Why investigate now (not implement)

Project Closure arc is **complete** and documented:

```text
IC 1 Requirements  →  IC 2 Battery/G27  →  IC 3 Policy/display
        ↓
checkpoint-closure-policy + ARCHITECTURE/system_map + design-doc hygiene
        ↓
73bd9fa — CLEAN BASELINE
```

Three credible next directions exist, each deferred **deliberately** during Closure:

| Candidate | One-line | Deferred because |
|---|---|---|
| **P2-2** | Continue Phase 2 physics beyond lookup OP | Closure arc had higher leverage; P2-1 was sufficient for propulsion evidence |
| **G24** | Apply catalog DSE row by index / honest apply CTA | Impl C validated generation; apply UX is separate product debt |
| **H5** | ESC as catalog SKU + bind | Schema + data work; freeform ESC sufficient for ERF-2 MVP |

Choosing wrong wastes a full IC arc. This investigation compares **leverage, prerequisites, scope, and live gaps** — not “what’s left on a backlog list”.

### 0.2 Core product question

> **Which single next block unlocks the most real Jarvis capability per unit of architectural risk?**

Secondary: does that choice imply **`0.3.x` vs `0.4.0`** (report may note implications; **decision is Engineer’s after ★**).

### 0.3 Methodology lock (★ — non-negotiable)

| ★ | Rule |
|---|---|
| **★1** | **Code + tests first.** Every “pending / done / broken” claim must cite file:line or a named test/probe on baseline `73bd9fa`. Vision docs are **context only**. |
| **★2** | **No invented SKUs** in recommendations — same discipline as Closure arc. |
| **★3** | **Do not conflate candidates.** G24 is DSE apply UX; P2-2 is physics/OP evolution; H5 is catalog/schema expansion. Report must keep three scope boxes. |
| **★4** | **Do not reopen Project Closure.** Requirements, battery UX, G27, §11 policy, propeller `sku_resolved` are closed unless investigation finds a **new regression** (must reproduce on baseline). |
| **★5** | **Recommend one primary direction** (+ optional secondary/deferred). No “do all three in one IC”. |
| **★6** | **Comparison matrix before recommendation** — evidence rows filled first; recommendation last. No arbitrary scoring. |

### 0.4 Explicit non-goals

- Implementing P2-2, G24, or H5 fixes  
- Version bump / tag creation  
- Conversation Engine / Step D  
- Frame SKU catalog (same class as H5 but **out of this comparison** unless investigation proves ESC and frame are inseparable — unlikely)  
- G26 / G27 (closed in IC 1/2)  
- Rewriting `ENGINEERING_READINESS_VISION.md` §11  
- Auto-refresh calc/sim after bind (separate debt)  
- Weakening tests  

---

## 1. What Claude must investigate

### 1.1 Baseline verification (mandatory first step)

Before candidate analysis, confirm baseline health on `73bd9fa`:

| Check | How |
|---|---|
| Full suite | `pytest tests/` — record pass count |
| Closure probes | `cli_probe_requirements_closure.py`, `cli_probe_battery_catalog_bind_ux.py`, `cli_probe_closure_policy_propeller_sku.py` — record PASS counts |
| P2-1 smoke | `tests/test_phase2_lookup_operating_point.py` — green |
| Impl C / G24 path | `tests/test_impl_c*` / DSE apply tests relevant to G24 — which scenarios exist vs CLI finding gap |

**Deliverable:** §Baseline — 5–10 lines: suite count, probe results, any surprise failure (STOP if baseline broken).

---

### 1.2 Candidate A — P2-2 (Phase 2 continuation)

**Scope box (investigation must define precisely — vision is broad):**

Vision doc (`PHYSICAL_PROPULSION_ENGINE_PHASE2.md`) marks P2-1 ✅ and leaves open:

- Real World Validation Case (§12.2)
- Power model electrical + mechanical (§7)
- Thrust from OP + validation chain (§8)
- Data provenance / confidence (§9)
- Model 2 evolution (§11)

**Investigation tasks:**

| # | Question | Required answer |
|---|---|---|
| A1 | What does “P2-2” mean **in code today**? | List symbols/files beyond `resolve_operating_point` / P2-1 bridge — grep + read |
| A2 | What is **already delivered** that P2-2 would build on? | P2-1 seeds, propulsion_resolution evidence, calc/sim inputs — trace |
| A3 | What is **conceptually open** per vision §4–11 vs **already partially present**? | Gap list with code refs |
| A4 | **Prerequisites satisfied?** | Catalog bind, OP lookup, electrical_compatibility — table |
| A5 | **New capability** if P2-2 ships first? | What user can do after that they cannot do on `73bd9fa` |
| A6 | **Scope / risk** | Likely IC count; touch surfaces (`library.py`, calc, sim, readiness?); forbidden overlaps |
| A7 | **Reusable fixtures/probes** | Which tests/probes extend vs net-new CLI walk |
| A8 | **Blockers** | Must anything else land first (G24? H5? data seeds?) |

**Code anchors (start trace, do not assume complete):**

- `src/jarvis/core/resolve_operating_point.py` (or equivalent module path — verify)
- `src/jarvis/core/component_writers.py` — propulsion bridge
- `src/jarvis/core/calculation_engine.py` — thrust / power paths
- `library/` operating point seed data
- `tests/test_phase2_lookup_operating_point.py`

**Deliverable:** §P2-2 — scope box, prerequisite table, capability delta, recommended **first IC cut outline** (bullets only, no code).

---

### 1.3 Candidate B — G24 (DSE apply / catalog row selection)

**Scope box:**

G24 = user sees catalog motor in DSE top-N but **`aplica la mejor` applies `viable[0]` only** — often params-only — G5 clears `catalog_ref`. Ranking residual (abstract thrust beats SKU) is a **separate layer** per finding doc.

**Investigation tasks:**

| # | Question | Required answer |
|---|---|---|
| B1 | Reproduce on baseline | Can CLI finding be reproduced with workspace fixture or test harness? YES/NO + steps |
| B2 | Apply path today | Trace `orchestrator._handle_apply_exploration`, `viable[0]`, intent patterns for apply |
| B3 | Generation path | What Impl C **does** deliver — catalog rows in `viable[]` — file:line |
| B4 | Ranking layer | Trace `design_explorer._score_candidate` / grids — why abstract wins when thrust declared |
| B5 | G5 interaction | When apply #1 clears identity — exact call order; frankenstein `.name` behavior |
| B6 | **Gap class** | UX debt vs structural capability — argue with user journey |
| B7 | Fix options | Map G24-A/B/C from finding to effort/risk (apply-by-index, ranking tiebreak, honest CTA) |
| B8 | **Impact on Closure / readiness** | Does G24 block ASSEMBLY READY? (Closure investigation said no — re-verify) |
| B9 | Existing test coverage | Which tests **miss** the Engineer CLI path; what probe would gate an IC |

**Code anchors:**

- `src/jarvis/core/orchestrator.py` — `_handle_apply_exploration` (~3534+)
- `src/jarvis/core/design_explorer.py` — scoring, `EXPLORATION_GRIDS`
- `src/jarvis/core/catalog_bind.py` — `invalidate_diverged_catalog_refs`
- `src/jarvis/core/intent_resolver.py` — apply patterns
- `tests/test_impl_c*`, `tests/test_g5_*`, `tests/test_da2_*`

**Deliverable:** §G24 — two-layer root cause (apply vs ranking), fix-option table, recommended **first cut** (likely G24-A), probe sketch.

---

### 1.4 Candidate C — H5 (ESC catalog + bind)

**Scope box:**

H5 = ESC as **catalog SKU** with bind path. Today: `CatalogRef.family` is `Literal["motor","battery","propeller"]` only; ESC is **freeform_ok** per §11; ERF-2 uses declared `current_a` + `electrical_compatibility`.

**Investigation tasks:**

| # | Question | Required answer |
|---|---|---|
| C1 | ESC **as-is** | Acquisition, writers, readiness, electrical checks — trace freeform path |
| C2 | What **works without** ESC catalog | Which gaps/verdicts are satisfiable today |
| C3 | Schema delta | Exact changes to `CatalogRef`, `catalog_bind`, library layout for `"esc"` |
| C4 | Data delta | New `library/esc/` or equivalent — minimum honest seed count |
| C5 | UX delta | Mirror motor/propeller/battery pick? FN-ESC out-of-scope save interaction |
| C6 | **Live blocker** | Does any fixture fail ASSEMBLY READY **because** ESC lacks catalog? YES/NO |
| C7 | **Capability unlocked** | What becomes possible vs better evidence only |
| C8 | Scope vs H5 investigations | Compare to ERF-2 investigation deferral — still valid? |
| C9 | Dependency | Does H5 require G24 or P2-2 first? |

**Code anchors:**

- `src/jarvis/schemas/action_schema.py` — `CatalogRef`
- `src/jarvis/core/electrical_compatibility.py`
- `src/jarvis/core/acquisition_target.py` — ESC aliases / FN-ESC
- `src/jarvis/knowledge/library.py` — family loaders pattern
- `tests/test_fn_esc_acquisition.py`, `tests/test_electrical_compatibility.py`

**Deliverable:** §H5 — schema/data/UX delta table, blocker verdict, honest “why now / why later”.

---

### 1.5 Cross-candidate comparison matrix (mandatory)

Fill **after** §1.2–1.4. Use qualitative cells (Short / Medium / Large / None / Yes / No / Partial) — **not** numeric scores.

| Criterion | P2-2 | G24 | H5 |
|---|---|---|---|
| Gap live (repro on baseline) | | | |
| New user-visible capability | | | |
| Prerequisites satisfied | | | |
| Leverage (unlock downstream work) | | | |
| Implementation scope | | | |
| Architectural risk | | | |
| Continuity with P2-1 / Closure / Impl C | | | |
| Product value (Engineer-facing) | | | |
| Test/probe gate clarity | | | |
| Version-milestone fit (note only) | | | |

**Deliverable:** §Comparison matrix — complete table + 1 paragraph interpreting tradeoffs (no winner until §1.6).

---

### 1.6 Recommendation (mandatory)

| Field | Required |
|---|---|
| **Primary next block** | P2-2 **or** G24 **or** H5 — one only |
| **Rationale** | 5–10 lines tied to matrix rows |
| **Deferred candidates** | What waits; **explicit prerequisite** if “X before Y” |
| **Suggested investigation → IC sequence** | 1–3 cuts max; names + gates (bullets, no code) |
| **Version note** | Whether primary block suggests `0.3.x` patch vs `0.4.0` milestone — **recommendation only, not a bump** |
| **Out of scope for first IC** | What must NOT leak into the first contract |

**Allowed conclusions (examples — investigation must pick one):**

```text
"P2-2 first — G24/H5 wait; Real World Validation Case is the highest physics leverage."
"G24-A first — P2-2 unchanged; catalog DSE product path is broken for bound motors today."
"H5 defer — no live blocker; schema cost high; G24 or P2-2 better ROI."
"G24 before P2-2 — OP validation meaningless if user cannot preserve SKU through explore/apply."
```

---

### 1.7 ★ Decisions for Engineer (mandatory)

Number ★1…★N. Each: decision + investigation recommendation + “no recommendation” only when genuinely ambiguous.

**Minimum ★ topics:**

| ★ | Topic |
|---|---|
| **★1** | Primary next block (ratify investigation recommendation or override) |
| **★2** | G24: apply-by-index vs ranking tiebreak vs CTA-only — if G24 wins |
| **★3** | P2-2: first cut scope — Real World Validation vs power model vs other |
| **★4** | H5: defer vs start schema-only spike vs full catalog slice |
| **★5** | Version bump timing relative to chosen IC (after IC PASS vs with checkpoint) |

---

## 2. Report structure

`.jes/artifacts/investigation_report_next_engineering_block.md` must include:

1. Executive summary (≤10 lines)  
2. Baseline verification (§1.1)  
3. P2-2 findings (§1.2)  
4. G24 findings (§1.3)  
5. H5 findings (§1.4)  
6. Comparison matrix (§1.5)  
7. Recommendation (§1.6)  
8. ★ Decisions for Engineer (§1.7)  
9. Suggested IC outline(s) — bullets only  
10. CLI probe sketch(es) for recommended path  
11. Explicit “do not implement yet” queue  

---

## 3. Hard constraints for future ICs (inherit)

- LLM never invents SKUs  
- Reuse `catalog_bind` / existing assist patterns — no parallel binders  
- `ProjectState` remains SoT; readiness is projection only  
- Do not break Closure regressions (1976 suite anchors)  
- Do not break P2-1 propulsion path (exact/fallback OP)  
- Zero weakened tests — disclose assertion changes  
- One arc at a time — no mega-IC mixing P2-2 + G24 + H5  

---

## 4. Acceptance (Cursor review)

**PASS** if report:

- Verifies baseline on `73bd9fa` (suite + relevant probes)  
- Answers every §1.2–1.4 question with code traces  
- Fills comparison matrix before recommendation  
- Recommends **one** primary block with explicit deferrals  
- Includes ★ decisions + 1–3 IC cut outlines  
- Does not implement or bump version  

**FAIL** if report:

- Relies on stale docs without code verification  
- Recommends multiple blocks in one IC without justification  
- Reopens Project Closure without regression proof  
- Uses numeric priority scores without evidence  
- Collapses G24 ranking and apply layers  

---

## 5. Queue after investigation

```text
Investigation PASS
  ↓
Engineer ★ (primary block + version timing)
  ↓
Version decision (optional tag)
  ↓
Cursor: implementation_contract(s) for chosen block
  ↓
Claude implements → review → probe → checkpoint
```

---

**End of contract.**
