# Implementation Contract — CLI Polish Audit (Investigation only)

**Type:** Investigation / Audit — **zero `src/` changes**  
**Date:** 2026-08-17  
**Requester:** Engineer  
**Executor:** Claude (JES investigation agent)  
**Work plan:** [work_plan_cli_polish_audit.md](work_plan_cli_polish_audit.md)  
**Findings register:** [cli_findings_post_catalog_bind_v1.md](cli_findings_post_catalog_bind_v1.md)  
**Base commit:** `1b4769f`

---

## 1. Objective

Produce a **complete, detailed audit report** of all open CLI polish gaps discovered during the Continuity + G10 CLI walk (`continuity-bom`, 2026-08-17). The report must be sufficient for Engineer to author a **clean, ordered Implementation Contract** without further code archaeology.

---

## 2. Scope

### In scope — audit these findings

| ID | Priority |
|---|---|
| G9-B | 🔴 |
| G9-A | 🟡 (relationship to G9-B) |
| G16-A, G16-B | 🟡/🔴 |
| G17 | 🔴 |
| G18 | 🔴 |
| G19 | 🔴 |
| G12 / FN-013 | 🟡 |
| G13 | 🟡 (include defer recommendation) |
| G11, G8, G7 | 🟡 (cross-reference only; note R3 overlap) |

### In scope — cross-cutting analysis

1. **Three authorities:** physics (calc/sim) vs catalog (SKU matcher) vs Continuity (next_step CTA).
2. **Intent routing map:** IDLE vs DEFINE_MISSING vs iterate vs analyze — where each finding fires.
3. **G10 ★8 parity:** `list_materials` pattern as template for `list_motors`.
4. **DSE discoverability:** `declarar empuje` → `explora opciones` path vs Continuity CTA.
5. **Regression guards:** G14, G15, G10 force-frame must not regress.

### Out of scope

- Implementing fixes
- New architectural subsystems (Decision Engine, Conversation Engine)
- Library JSON changes (`library/motores/*.json`)
- Impl C full catalog architecture
- Thrust gate (★7 — rejected in Continuity design)

---

## 3. Required inputs (read before writing)

| Artifact | Purpose |
|---|---|
| `cli_findings_post_catalog_bind_v1.md` | Finding IDs + CLI transcripts |
| `work_plan_cli_polish_audit.md` | Phase plan + acceptance probes |
| `design_continuity_hardening.md` | ★1–★7 locks |
| `design_g10_materials_frame.md` | ★1–★8 locks |
| `implementation_report_continuity_hardening.md` | What was implemented |
| `implementation_report_g10_materials_frame.md` | What was implemented |
| `src/jarvis/core/project_continuity.py` | G9-B CTA logic |
| `src/jarvis/core/orchestrator.py` | catalog_gap, soft-interrupts, force-* |
| `src/jarvis/core/intent_resolver.py` | E1, LIST_MATERIALS, analyze routing |
| `src/jarvis/core/motor_catalog_assist.py` | list-motors, filtered max |
| `src/jarvis/core/reasoning_layer.py` | suggestion wiring |
| `src/jarvis/core/param_definition_session.py` | FN-013 reprompt path |
| `tests/test_continuity_hardening.py` | Existing regression tests |
| `tests/test_g10_materials_frame.py` | G10 regression tests |

Optional CLI evidence: `workspace/continuity-bom-fa9f25c1d2a2/state.json` (if present).

---

## 4. Deliverable

**File:** `.jes/artifacts/investigation_cli_polish_audit.md`

### Required sections

#### 4.1 Executive summary
- Verdict: ready for impl / needs design decisions / blocked
- Recommended slice count and order
- Estimated risk per slice

#### 4.2 Per-finding analysis (one subsection each)

For **each** finding G9-B, G9-A, G16, G17, G18, G19, G12-FN013, G13:

```text
- Symptom (CLI transcript)
- Code path (file:line references)
- Root cause (single sentence)
- Why current Continuity/G10/Continuity-hardening didn't fix it
- Proposed fix (behavior, not code dump)
- Blast radius / regression risk
- Test probes (unit + CLI)
- Defer? (yes/no + reason)
```

#### 4.3 Authority diagram

Mermaid or ASCII showing how physics, catalog matcher, and Continuity CTA interact — especially the G9-B case (PASS + margin 9.1 + catalog_gap).

#### 4.4 Proposed implementation slices

Table:

| Slice | Findings | Files (estimate) | Tests | Depends on |
|---|---|---|---|---|

Must include explicit **non-goals** per slice.

#### 4.5 Continuity CTA policy proposal

Single policy document section answering:

- When should `motor_catalog_gap` appear as next_step?
- When should it be suppressed or demoted to evidence-only?
- What CTA text when declared thrust >> required thrust and sim PASS?
- How to connect to DSE (`explora opciones`) and list-motors?

#### 4.6 CLI acceptance matrix

Expand work plan §8 with expected vs failure signals.

#### 4.7 Open questions for Engineer

List decisions that audit cannot resolve without product input.

---

## 5. Quality gates

| Gate | Criterion |
|---|---|
| G1 | Every Tier-1 finding has file:line evidence |
| G2 | G9-B two-layer problem explained with user's numbers (19.777 N / 180 N / 3.3 N / 30 N) |
| G3 | G19 documents both dead-end AND hidden DSE path |
| G4 | No fix proposed that violates Continuity ★1–★7 or G10 ★1–★8 |
| G5 | Slice ordering has explicit dependencies |
| G6 | Test matrix covers G14/G15/G10 regression |
| G7 | Zero `src/` edits in audit phase |

---

## 6. Constraints

- **Read-only** on `src/` — investigation only
- Do not patch G10 materials to paper over routing gaps
- Do not collapse G11/G8/G12 into one vague "routing" finding — keep IDs
- Distinguish **bug** vs **known limit** vs **expected behavior**
- Spanish CLI examples where citing user transcripts

---

## 7. Success criteria

Engineer can take `investigation_cli_polish_audit.md` and write `implementation_contract_cli_polish.md` in one session without re-reading orchestrator.py.

---

## 8. After audit (not part of this contract)

```text
investigation_cli_polish_audit.md
        ↓ Engineer review
design_cli_polish.md (optional, if slices need ★ locks)
        ↓
implementation_contract_cli_polish.md
        ↓
Cursor implementation + review + CLI re-walk + checkpoint
```
