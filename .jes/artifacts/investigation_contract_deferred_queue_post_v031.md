# Investigation Contract — Deferred Queue Post-v0.3.1

**Project:** Jarvis  
**Date:** 2026-08-31  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output:** `.jes/artifacts/investigation_report_deferred_queue_post_v031.md`

**Status:** READY FOR CLAUDE

**Type:** Comparative architecture + product investigation — determine **which deferred candidate** should become the **next implementation arc** after `v0.3.1`, with evidence from code/tests on baseline **`checkpoint-next-engineering-block`**. **Not** an implementation plan. **Not** a version-bump decision until Engineer ratifies direction after ★.

**Checkpoint base:** tag **`v0.3.1`** / **`checkpoint-next-engineering-block`** · commit `30c9aec`

**Prior arc (CLOSED — do not re-open without regression proof):**

| Delivered @ v0.3.1 | Scope |
|---|---|
| **G24-A** | DSE apply-by-index — `aplica la N` / `#N`; `"aplica la mejor"` = `viable[0]` |
| **P2-2 bridge** | `motor_op_*` additive keys; `motor_power_w` = catalog rating; OP-first calc/electrical |

**Design authority (read-only — verify against code, do not treat as proof of pending work):**

- [`docs/PHYSICAL_PROPULSION_ENGINE_PHASE2.md`](../../docs/PHYSICAL_PROPULSION_ENGINE_PHASE2.md) — §12.2 Validation Case vision
- [`docs/PHYSICAL_COMPONENT_CATALOG_V1.md`](../../docs/PHYSICAL_COMPONENT_CATALOG_V1.md) — design lock 1A (ESC family)
- [`.jes/artifacts/phase2_star6_operating_point_validation_case.md`](phase2_star6_operating_point_validation_case.md) — approved OP dataset (P2-1 delivered)
- [`.jes/artifacts/cli_finding_g24_dse_apply_only_top1_catalog_unselectable.md`](cli_finding_g24_dse_apply_only_top1_catalog_unselectable.md) — G24-B/C options
- [`.jes/artifacts/investigation_report_next_engineering_block.md`](investigation_report_next_engineering_block.md) — prior H5 / G24 / P2-2 comparison (re-verify on v0.3.1)

**Engineer framing (2026-08-31) — locked:**

```text
v0.3.1 is the stable baseline. No code until comparative investigation + explicit ★.

Core question:
  Which intervention delivers the most engineering/product value NOW,
  and which has a real blocker or risk that justifies opening another IC?

Compare (do not pick by intuition):
  A  Validation Case   — real-world physics validation / honest deltas
  B  H5                — ESC catalog + bind (schema lock 1A)
  C  G24-B / G24-C     — DSE ranking tiebreak / honest explore CTA
  D  Frankenstein .name — stale motor name after G5 catalog_ref clear

G24-A and P2-2 bridge are DONE — investigate what each deferred item
still adds AFTER v0.3.1, not their pre-shipment rationale alone.
```

**Do NOT implement any candidate in this investigation.**  
**Do NOT bump `pyproject.toml` version.**  
**Do NOT weaken tests or fake PASS states.**

**Workflow:** Investigate → report + comparison matrix → Engineer ★ → version note → Cursor IC(s) → Claude implements → review → probe → checkpoint.

---

## 0. Context

### 0.1 Why investigate now

Next Engineering Block is **checkpointed** at `v0.3.1`. Four items were **explicitly deferred** with documented rationale. Opening any of them without re-comparison risks:

- wasting an IC on **symmetry-only** work (H5) when no live blocker exists;
- reopening **locked scoring** (G24-B) when G24-A may have closed the functional gap;
- duplicating **P2-1/P2-2** work under the “Validation Case” label;
- under-scoping **trust/display** debt (`.name`) or over-scoping it as a major arc.

This investigation re-evaluates the deferred queue **on the post-v0.3.1 codebase**.

### 0.2 Core product question

> **Which single deferred intervention has the best ratio of (real capability or trust gain) / (architectural risk + IC size), and is there a live blocker that makes deferral irresponsible?**

Secondary: micro-IC vs full arc — especially for **D (.name)**.

### 0.3 Methodology lock (★ — non-negotiable)

| ★ | Rule |
|---|---|
| **★1** | **Code + tests first.** Every claim cites file:line or named test/probe on baseline `30c9aec` / tag `v0.3.1`. Vision docs and prior reports are **context only**. |
| **★2** | **No invented SKUs** — same discipline as Closure / ★6 dataset. |
| **★3** | **Four separate scope boxes** — Validation Case ≠ H5 ≠ G24-B/C ≠ `.name`. Do not collapse. |
| **★4** | **Do not reopen** Next Engineering Block (G24-A, P2-2 bridge), Project Closure, or P2-1 resolver matching without **new regression** reproduced on v0.3.1. |
| **★5** | **Recommend one primary direction** (+ optional secondary/micro-IC/deferred). No mega-IC mixing candidates. |
| **★6** | **Comparison matrix before recommendation** — qualitative cells only; no numeric priority scores. |
| **★7** | **Post-v0.3.1 delta** — each candidate section must state what is **already done** vs **still open** after G24-A + P2-2 bridge. |

### 0.4 Explicit non-goals

- Implementing any candidate  
- Version bump / tag creation  
- Re-doing G24-A or P2-2 bridge  
- Changing `resolve_operating_point` matching rules  
- Conversation Engine / Step D  
- Frame SKU catalog (unless investigation proves inseparable from H5 — unlikely)  
- Auto-refresh calc/sim after bind  
- Weakening tests  

---

## 1. What Claude must investigate

### 1.1 Baseline verification (mandatory first step)

On **`v0.3.1`** / `30c9aec`:

| Check | How |
|---|---|
| Full suite | `pytest tests/` — record pass count (expect **2013**) |
| Next-block probes | `cli_probe_g24_apply_by_index.py`, `cli_probe_p2_2_operating_point_bridge.py` — **6/6** each |
| Closure probes | `cli_probe_requirements_closure.py`, `cli_probe_battery_catalog_bind_ux.py`, `cli_probe_closure_policy_propeller_sku.py` |
| G24-A regression | apply-by-index + `"aplica la mejor"` = `viable[0]` smoke |
| P2-2 regression | `motor_power_w` vs `motor_op_*` on `emax_rs2205s_2300` + `hq_5045_bn` |

**Deliverable:** §Baseline — pass counts; STOP if baseline broken.

---

### 1.2 Candidate A — Real World Validation Case (Phase 2 §12.2)

**Scope box:**

Validation Case = **honest comparison** between Jarvis's resolved numbers (OP bridge, calc, electrical, thrust evidence) and **curated manufacturer/source data** for specific motor+prop+voltage combos — divergence report, probe, optional CLI/estado surface. **Not** re-implementing P2-1 seeds or P2-2 bridge (both shipped).

**Investigation tasks:**

| # | Question | Required answer |
|---|---|---|
| A1 | What is **already delivered** @ v0.3.1? | P2-1 seeds, ★6 dataset, `motor_op_*`, `propulsion_resolution`, probes — inventory with code refs |
| A2 | What does “Validation Case” mean **in code today**? | grep + read — any harness beyond tests? |
| A3 | **Still open** for a first IC cut? | Minimal slice: probe? report artifact? estado delta line? new SKUs? |
| A4 | **Live gap** | Is there a user-visible false confidence or missing “model vs source” honesty **today** after P2-2? |
| A5 | **Prerequisites** | Catalog bind, OP resolver, bridge — table |
| A6 | **Scope / risk** | IC size; touch surfaces; forbidden overlaps with P2-1 matcher |
| A7 | **Reusable fixtures** | `test_phase2_lookup_operating_point.py`, ★6 doc, existing probes |
| A8 | **Blockers** | Must H5, G24-B, or `.name` land first? |

**Code anchors:**

- `library/motores/_datos.json`, `library.py` — `operating_points[]` (read-only for this investigation)
- `component_writers.py` — `motor_op_*`, `propulsion_resolution`
- `adapters/cli/main.py` — propulsion + OP electrical lines
- `.jes/artifacts/phase2_star6_operating_point_validation_case.md`
- `tests/test_phase2_lookup_operating_point.py`

**Deliverable:** §Validation Case — post-v0.3.1 gap, first IC cut outline (bullets only).

---

### 1.3 Candidate B — H5 (ESC catalog + bind)

**Scope box:**

H5 = ESC as **catalog SKU** (`CatalogRef.family` += `"esc"`), library loader, bind path, optional pick UX. Freeform ESC + ERF-2 electrical checks **already work**.

**Investigation tasks:**

| # | Question | Required answer |
|---|---|---|
| B1 | ESC **as-is** @ v0.3.1 | Acquisition, writers, readiness, electrical — trace |
| B2 | **Live blocker** | Any fixture/gap fails because ESC lacks catalog? YES/NO + evidence |
| B3 | Schema delta | `action_schema.py` CatalogRef 1A reopening — exact changes |
| B4 | Data / UX delta | Minimum honest seed; mirror battery IC 2? |
| B5 | **Post-v0.3.1** | Did P2-2 bridge or G24-A change urgency? |
| B6 | Scope / risk | vs prior investigation — still defer? |
| B7 | Version-milestone note | `0.3.x` vs `0.4.0` shape (recommendation only) |

**Code anchors:** prior §1.4 in [investigation_report_next_engineering_block.md](investigation_report_next_engineering_block.md) — **re-verify**, do not cite from memory.

**Deliverable:** §H5 — blocker verdict, schema cost, honest “why now / why later”.

---

### 1.4 Candidate C — G24-B / G24-C (DSE ranking + explore CTA)

**Scope box:**

**G24-A is CLOSED.** This candidate is **only**:

- **G24-B** — ranking tiebreak / catalog preference in `_score_candidate` (touches Impl C ★6 lock)
- **G24-C** — honest explore CTA when `#1` is abstract and catalog rows exist

**Not** apply-by-index (done).

**Investigation tasks:**

| # | Question | Required answer |
|---|---|---|
| C1 | **Post-G24-A user journeys** | Reproduce: bound motor + explore — can user reach catalog SKU via `aplica la N` when in `.viable`? when **not** in `.viable`? |
| C2 | **Residual pain** | What problem remains after G24-A? Quantify frequency (code paths, not guess) |
| C3 | G24-B effort/risk | `_score_candidate` / ★6 unlock — what Engineer ★ would be required? |
| C4 | G24-C alone | Is CTA without B sufficient for honesty? Dependency on catalog in `.viable`? |
| C5 | **Impact on Closure / readiness** | Still non-blocker? |
| C6 | **vs Validation Case / H5 / .name** | Relative leverage argument with evidence |

**Code anchors:**

- `design_explorer.py` — `_score_candidate`, explore message (`orchestrator._handle_explore`)
- `tests/test_g24_apply_by_index.py`, `cli_probe_g24_apply_by_index.py`
- `cli_finding_g24_dse_apply_only_top1_catalog_unselectable.md` — Options B/C

**Deliverable:** §G24-B/C — two-layer residual (ranking vs copy); recommend B, C, both, or **defer** with post-G24-A rationale.

---

### 1.5 Candidate D — Frankenstein `.name` (G5 identity display)

**Scope box:**

After G5 `invalidate_diverged_catalog_refs` clears `catalog_ref`, motor **`ComponentSpec.name`** may remain a stale SKU string while params/thrust diverge — trust/display debt. **Not** changing G5 invalidate semantics (correct when params diverge); question is **honest labeling** after divergence or on `estado`/BOM.

**Investigation tasks:**

| # | Question | Required answer |
|---|---|---|
| D1 | Reproduce @ v0.3.1 | Steps: bound motor → explore → `aplica la mejor` (abstract #1) OR iterate divergence — disk/`estado` shape |
| D2 | Trace | `invalidate_diverged_catalog_refs` — what fields mutate; who reads `.name` |
| D3 | **Impact** | `estado`, BOM (`format_bom_lines`), readiness, Continuity — misleading where? |
| D4 | **G24-A interaction** | Does apply-by-index **reduce** incidence vs `"aplica la mejor"` path? |
| D5 | Fix options | Clear/rename `.name`; generic label; estado disclaimer; sync from params — effort table |
| D6 | **Micro-IC?** | Smallest safe cut vs coupling with G5 semantic change |
| D7 | **Live blocker** | ASSEMBLY READY / gap / trust break severity |

**Code anchors:**

- `catalog_bind.py` — `invalidate_diverged_catalog_refs`
- `component_sync.py`, `project_closure.py`, `adapters/cli/main.py`
- G24 finding post-apply disk check (stale `name`)

**Deliverable:** §Frankenstein `.name` — gap class (display vs data model); micro-IC outline if warranted.

---

### 1.6 Cross-candidate comparison matrix (mandatory)

Fill **after** §1.2–1.5. Qualitative cells only.

| Criterion | A Validation Case | B H5 ESC | C G24-B/C | D `.name` |
|---|---|---|---|---|
| Gap live on v0.3.1 (repro) | | | | |
| Live blocker (readiness/gap) | | | | |
| Trust / product value | | | | |
| Post-v0.3.1 incremental value | | | | |
| Prerequisites satisfied | | | | |
| Implementation scope | Short / Medium / Large | | | |
| Architectural risk | | | | |
| Touches locked contracts (★6, 1A, G5) | | | | |
| Unlocks downstream work | | | | |
| Test/probe gate clarity | | | | |
| Version-milestone fit (note only) | | | | |

**Deliverable:** §Comparison matrix + 1 paragraph interpreting tradeoffs (no winner until §1.7).

---

### 1.7 Recommendation (mandatory)

| Field | Required |
|---|---|
| **Primary next block** | One of A / B / C / D — or explicit “investigate further X first” |
| **Rationale** | 5–10 lines tied to matrix; **post-v0.3.1** delta |
| **Secondary / micro-IC** | Optional parallel small cut (e.g. D as micro-IC after primary) |
| **Deferred** | Explicit deferrals with prerequisite if “X before Y” |
| **Suggested IC sequence** | 1–2 cuts max; names + gates (bullets, no code) |
| **Version note** | `0.3.x` patch vs `0.4.0` milestone — recommendation only |
| **Out of scope for first IC** | What must NOT leak in |

**Allowed conclusions (examples — pick one):**

```text
"Validation Case first — closes physics honesty loop after P2-2 bridge."
"H5 defer — still no live blocker; 1A reopening not justified yet."
"G24-C only (copy) — B still deferred; ranking lock intact."
"D micro-IC first — smallest trust fix; Validation Case second."
"Validation Case + D micro-IC in one checkpoint window" — only if investigation
  proves independence and Engineer-scale discipline; default is one primary.
```

---

### 1.8 ★ Decisions for Engineer (mandatory)

| ★ | Topic |
|---|---|
| **★1** | Primary next block (ratify recommendation or override) |
| **★2** | Validation Case first-cut scope (probe-only vs estado surface vs dataset expansion) |
| **★3** | G24-B vs G24-C vs defer (post-G24-A) |
| **★4** | H5: defer vs Engineer ratification of 1A reopening |
| **★5** | `.name` debt: micro-IC now vs bundle with another cut vs defer |
| **★6** | Version bump timing relative to chosen IC |

---

## 2. Report structure

`.jes/artifacts/investigation_report_deferred_queue_post_v031.md` must include:

1. Executive summary (≤10 lines)  
2. Baseline verification (§1.1)  
3. Validation Case findings (§1.2)  
4. H5 findings (§1.3)  
5. G24-B/C findings (§1.4)  
6. Frankenstein `.name` findings (§1.5)  
7. Comparison matrix (§1.6)  
8. Recommendation (§1.7)  
9. ★ Decisions for Engineer (§1.8)  
10. Suggested IC outline(s) — bullets only  
11. CLI probe sketch(es) for recommended path  
12. Explicit “do not implement yet” queue  

---

## 3. Hard constraints for future ICs (inherit)

- LLM never invents SKUs  
- `motor_power_w` = catalog rating; OP electrical = `motor_op_*` (Option A — frozen @ v0.3.1)  
- G24-A apply-by-index frozen — do not regress  
- Do not break Closure / v0.3.1 probes without disclosure  
- One arc at a time — no mega-IC  
- G24-B touches `_score_candidate` only with explicit new Engineer ★ unlocking Impl C ★6  
- H5 touches `CatalogRef` 1A only with explicit Engineer ★  

---

## 4. Acceptance (Cursor review)

**PASS** if report:

- Verifies baseline on `v0.3.1`  
- Answers every §1.2–1.5 question with code traces  
- States **post-v0.3.1 delta** per candidate (★7)  
- Fills matrix before recommendation  
- Recommends **one** primary block (+ optional micro-IC)  
- Includes ★ decisions + IC cut outlines  
- Does not implement or bump version  

**FAIL** if report:

- Relies on pre-v0.3.1 conclusions without re-verification  
- Treats Validation Case as “add OP seeds” (already shipped in P2-1)  
- Reopens G24-A or P2-2 bridge without regression proof  
- Collapses G24-B and G24-C with G24-A  
- Uses numeric priority scores without evidence  

---

## 5. Queue after investigation

```text
Investigation PASS
  ↓
Engineer ★ (primary + micro-IC + version note)
  ↓
Cursor: implementation_contract(s)
  ↓
Claude implements → review → probe → checkpoint
```

---

**End of contract.**
