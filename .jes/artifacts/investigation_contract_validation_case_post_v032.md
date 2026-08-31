# Investigation Contract — Validation Case Post-v0.3.2

**Project:** Jarvis  
**Date:** 2026-08-31  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output:** `.jes/artifacts/investigation_report_validation_case_post_v032.md`

**Status:** READY FOR CLAUDE

**Type:** Focused architecture + product investigation — determine **what Validation Case work remains** after P2-1/P2-2 and Deferred Queue C+D on baseline **`checkpoint-deferred-queue-cd` / `v0.3.2`**, and whether it justifies the **next implementation arc**. **Not** an implementation plan. **Not** a version-bump decision until Engineer ratifies direction after ★.

**Checkpoint base:** tag **`v0.3.2`** / **`checkpoint-deferred-queue-cd`** · commit `ca1659c`

**Prior arcs (CLOSED — do not re-open without regression proof on v0.3.2):**

| Delivered @ v0.3.2 | Scope |
|---|---|
| **P2-1** | `resolve_operating_point` — exact / fallback OP lookup from bound motor + prop + voltage |
| **P2-2** | `motor_op_*` bridge; `motor_power_w` = catalog rating; OP-first calc/electrical |
| **G24-A** | DSE apply-by-index |
| **G24C (IC C)** | Viable-slot reservation + honest explore CTA; `_score_candidate` zero diff |
| **G24D (IC D)** | Frankenstein `.name` clear on G5 motor divergence |

**Deferred queue status:** **CLOSED** @ `v0.3.2`. C and D delivered. Remaining frozen candidates: **H5**, **G24-B scoring rewrite**.

**Design authority (read-only — verify against code, do not treat as proof of pending work):**

- [`docs/PHYSICAL_PROPULSION_ENGINE_PHASE2.md`](../../docs/PHYSICAL_PROPULSION_ENGINE_PHASE2.md) — §12.2 Validation Case vision + §12.1 P2-1 delivered scope
- [`.jes/artifacts/phase2_star6_operating_point_validation_case.md`](phase2_star6_operating_point_validation_case.md) — ★6 approved OP dataset (P2-1 delivered)
- [`.jes/artifacts/investigation_report_deferred_queue_post_v031.md`](investigation_report_deferred_queue_post_v031.md) — prior Validation Case analysis @ v0.3.1 (re-verify delta on v0.3.2)
- [`.jes/artifacts/investigation_review_deferred_queue_post_v031.md`](investigation_review_deferred_queue_post_v031.md)

**Engineer framing (2026-08-31, post-checkpoint) — locked:**

```text
v0.3.2 is the stable baseline. No code until this investigation + explicit ★.

Core question:
  What Validation Case work is still open AFTER P2-1/P2-2 and C+D,
  and is it engineering-shaped (IC) or data-curation / documentation-shaped?

Primary candidate:  Validation Case (Phase 2 §12.2)
Still frozen:       H5 (ESC catalog) · G24-B (_score_candidate rewrite)
Discipline:         Do NOT implement immediately after this investigation.
```

**Do NOT implement any candidate in this investigation.**  
**Do NOT bump `pyproject.toml` version.**  
**Do NOT weaken tests or fake PASS states.**

**Workflow:** Investigate → report → Engineer ★ → (optional) IC contract → Claude implements → review → probe → checkpoint.

---

## 0. Context

### 0.1 Why investigate now

Deferred Queue C+D closed the last **demonstrated product gaps** (G24 catalog visibility, frankenstein identity). Engineer direction: **next arc candidate is Validation Case** — but the prior deferred-queue investigation (@ v0.3.1) found Validation Case is **mostly already shipped** as lookup + OP bridge + honest `estado` labels, with remaining work potentially **research/data-curation shaped**, not a classic engineering IC.

Before drafting any IC, this investigation must **re-trace on v0.3.2** and answer:

> Is there a bounded, IC-shaped Validation Case cut with real product value — or should Engineer commission data sourcing / documentation separately?

### 0.2 Core product question

> **What does "Validation Case" still mean in practice on v0.3.2, and what is the smallest honest next step that closes a real gap — without duplicating P2-1/P2-2 or reopening closed arcs?**

### 0.3 Methodology lock (★ — non-negotiable)

| ★ | Rule |
|---|---|
| **★1** | **Code + tests first.** Every claim cites file:line or named test/probe on baseline `ca1659c` / tag `v0.3.2`. Vision docs and prior reports are **context only**. |
| **★2** | **No invented SKUs** — same discipline as ★6 dataset / Closure. |
| **★3** | **Separate scope boxes** — Validation Case ≠ H5 ≠ G24-B. Do not collapse. |
| **★4** | **Do not reopen** P2-1 matching rules, P2-2 Option A semantics, G24-A/C/D, or Closure without **new regression** on v0.3.2. |
| **★5** | **Recommend one primary direction** (+ explicit deferrals). No mega-IC. |
| **★6** | **Post-v0.3.2 delta** — state what C+D changed (if anything) for Validation Case analysis. |
| **★7** | **Distinguish IC-shaped vs data-curation vs docs-only** — do not label data sourcing as "implementation" without Engineer authority. |

### 0.4 Explicit non-goals

- Implementing any candidate  
- Version bump / tag creation  
- Re-doing P2-1, P2-2, G24-A/C/D  
- G24-B `_score_candidate` rewrite  
- H5 / ESC catalog / CatalogRef 1A expansion  
- Continuity catalog-gap UX polish  
- Conversation Engine  
- Weakening tests  

---

## 1. What Claude must investigate

### 1.1 Baseline verification (mandatory first step)

On **`v0.3.2`** / `ca1659c`:

| Check | How | Expected |
|---|---|---|
| Full suite | `pytest tests/` | **2028** passed |
| G24C probe | `cli_probe_g24_viable_selection_honest_cta.py` | **6/6** |
| G24D probe | `cli_probe_frankenstein_name_clear.py` | **5/5** |
| G24-A probe | `cli_probe_g24_apply_by_index.py` | **6/6** |
| P2-2 probe | `cli_probe_p2_2_operating_point_bridge.py` | **6/6** |
| Closure probes | `cli_probe_requirements_closure.py`, `cli_probe_battery_catalog_bind_ux.py`, `cli_probe_closure_policy_propeller_sku.py` | green |

**Deliverable:** §Baseline — pass counts; STOP if baseline broken.

---

### 1.2 Validation Case — deep trace (primary)

**Vision anchor:** [`PHYSICAL_PROPULSION_ENGINE_PHASE2.md`](../../docs/PHYSICAL_PROPULSION_ENGINE_PHASE2.md) §12.2 — `REAL DATA → JARVIS MODEL → CALCULATED RESULT → compare divergence`.

**Data anchor:** [`.jes/artifacts/phase2_star6_operating_point_validation_case.md`](phase2_star6_operating_point_validation_case.md) — OP-0/1/2/3 rows, URLs, locks.

| ID | Question | Method |
|---|---|---|
| V1 | What is **already delivered** in code for Validation Case? | Trace P2-1 seeds, `resolve_operating_point`, P2-2 bridge, `estado` evidence lines, relevant tests |
| V2 | Is there **any** `validation` harness in `src/` or tests beyond lookup? | `grep` + read |
| V3 | For **`exact_operating_point`**, is there numeric divergence to compute vs source? | Read `_resolved_from_op_row` / resolver path — lookup vs derivation |
| V4 | What **genuine divergences** exist today (e.g. rating vs OP, legacy vs exact)? | Live trace + tests; cite what's **already displayed** vs **missing** |
| V5 | Map §12.2 success criteria (items 1–14 in vision doc) — **done / partial / open** | Table with evidence |
| V6 | **Battery / ESC** domain: any curated real test data vs spec-sheet / freeform? | Library + electrical_compatibility + Closure probes |
| V7 | Does **G24C/D** change Validation Case calculus? | Expected: no — confirm |
| V8 | **IC-shaped options** (bullets only): | |
| | (a) Documentation artifact only (`.jes` comparison report citing live numbers) | |
| | (b) Probe / regression gate locking the ★6 story end-to-end | |
| | (c) `estado` / CLI surface — single "validation summary" line or section | |
| | (d) New sourced data (battery/ESC) — flag as **Engineer data curation**, not IC | |
| V9 | **Live gap** — false confidence, missing comparison, or user-visible hole? | Reproduce if claimed |
| V10 | **Scope / risk / touch surfaces** per option (a–d) | File list estimate |
| V11 | **Reusable fixtures** — existing tests/probes to extend? | Name them |

**Deliverable:** §Validation Case — post-v0.3.2 state; IC options with gates; live gap yes/no.

---

### 1.3 Frozen candidates — defer confirmation (lightweight)

Re-verify on v0.3.2 only — **no deep re-investigation** unless new regression found.

| ID | Candidate | Confirm |
|---|---|---|
| F1 | **H5 (ESC catalog)** | Still no live blocker? Still requires 1A reopening? C+D unchanged calculus? |
| F2 | **G24-B (scoring rewrite)** | Still frozen after G24C slot reservation? Any new evidence that ranking rewrite is needed? |

**Deliverable:** §Frozen candidates — one paragraph each; defer unless new blocker.

---

### 1.4 Comparison matrix (mandatory)

Qualitative only — no numeric scores.

| Criterion | Validation Case (next?) | H5 ESC | G24-B |
|---|---|---|---|
| Live gap on v0.3.2 | | | |
| Post-C+D incremental value | | | |
| IC-shaped vs research/data | | | |
| Architectural risk | | | |
| Touch surface size | | | |
| Independent of closed arcs | | | |
| Test/probe gate clarity | | | |

**Deliverable:** §Matrix + interpretation paragraph.

---

### 1.5 Recommendation (mandatory)

| Field | Required |
|---|---|
| **Primary next block** | Validation Case variant (a/b/c), defer entirely, or "Engineer data commission first" |
| **Rationale** | 5–10 lines tied to matrix; **post-v0.3.2** delta |
| **Deferred** | H5, G24-B — explicit unless new blocker |
| **Suggested IC sequence** | 0–2 cuts max; names + acceptance gates (bullets, no code) |
| **Version note** | `0.3.x` patch vs `0.4.0` — recommendation only |
| **Out of scope for first IC** | What must NOT leak in |

**Allowed conclusions (examples — pick one):**

```text
"Validation Case IC — probe-only gate locking ★6 end-to-end narrative."
"Validation Case IC — estado validation summary surface (no new resolver logic)."
"Defer Validation Case IC — commission Engineer battery/ESC data sourcing first."
"Documentation-only — .jes comparison artifact, no src/ touch."
"Still defer H5 and G24-B — no new blockers on v0.3.2."
```

---

### 1.6 ★ Decisions for Engineer (mandatory)

| ★ | Topic |
|---|---|
| **★1** | Primary next block — ratify recommendation or override |
| **★2** | Validation Case first-cut scope: (a) docs · (b) probe · (c) estado surface · (d) data curation · defer |
| **★3** | If (d): Engineer commissions new sourced data before any IC? |
| **★4** | H5: continue defer vs explicit 1A reopening |
| **★5** | G24-B: continue freeze vs revisit |
| **★6** | Version bump timing relative to chosen IC |

---

## 2. Report structure

`.jes/artifacts/investigation_report_validation_case_post_v032.md` must include:

1. Executive summary (≤10 lines)  
2. Baseline verification (§1.1)  
3. Validation Case findings (§1.2) — including §12.2 criteria map  
4. Frozen candidates confirmation (§1.3)  
5. Comparison matrix (§1.4)  
6. Recommendation (§1.5)  
7. ★ Decisions for Engineer (§1.6)  
8. Suggested IC outline(s) — bullets only, if any  
9. CLI probe sketch for recommended path — if any  
10. Explicit "do not implement yet" queue  

---

## 3. Hard constraints for future ICs (inherit)

- LLM never invents SKUs  
- `motor_power_w` = catalog rating; OP electrical = `motor_op_*` (Option A — frozen)  
- G24-A/C/D frozen — do not regress  
- `_score_candidate` zero diff unless explicit new Engineer ★ unlocking G24-B  
- `resolve_operating_point` matching rules frozen unless explicit new ★  
- H5 touches `CatalogRef` 1A only with explicit Engineer ★  
- One arc at a time — no mega-IC  
- Do not break v0.3.2 probes without disclosure  

---

## 4. Acceptance (Cursor review)

**PASS** if report:

- Baselines v0.3.2 with recorded pass counts  
- Answers V1–V11 with code citations or named tests  
- Distinguishes IC-shaped vs data-curation vs docs-only honestly  
- Matrix + recommendation present  
- ★ table complete  
- Does not implement or bump version  

**FAIL** if:

- Treats "add OP seeds" as open work (P2-1 shipped)  
- Collapses Validation Case into H5 or G24-B  
- Reopens C+D without regression proof  
- Recommends mega-IC  

---

## 5. Queue after investigation

```text
Investigation PASS + Engineer ★
  ↓
Optional IC contract (if ★2 selects IC-shaped cut)
  ↓
Implement → review → probe → checkpoint → 0.3.x or 0.4.0 per ★6
```

If ★2 = defer or docs-only → no IC until Engineer re-queues.

---

**End of contract.**
