# Implementation Contract — ERF-2 Investigation (Read-only)

**Type:** Investigation / Architecture design input — **zero `src/` changes**  
**Date:** 2026-08-18  
**Status:** READY FOR ENGINEER  
**Requester:** Engineer  
**Executor:** Cursor/JES  
**Checkpoint base:** tag **`checkpoint-erf1`** (`63c427b`)  
**Vision anchor:** [`docs/ENGINEERING_READINESS_VISION.md`](../../docs/ENGINEERING_READINESS_VISION.md) §ERF-2  
**Prior cycle:** [`.jes/artifacts/investigation_erf1_readiness_foundation.md`](investigation_erf1_readiness_foundation.md) · [`.jes/artifacts/implementation_report_erf1.md`](implementation_report_erf1.md)

**Primary question:**

> **"¿Cuál es el conjunto mínimo de comprobaciones deterministas motor↔ESC↔batería (y estados INCOMPATIBLE) que Jarvis puede afirmar reutilizando autoridades existentes, extendiendo ERF-1 sin solver eléctrico completo, segunda ProjectState, ni catálogo comercial Impl C?"**

---

## 1. Objective

Produce an ERF-2 investigation that defines the **smallest viable dependency / incompatibility layer** on top of ERF-1, sufficient for Engineer to decide ERF-2 design scope **before any implementation**.

ERF-2 must move Jarvis from *"sé qué falta"* (ERF-1) toward *"sé qué dependencias e incompatibilidades existen"* — starting with the **motor ↔ ESC ↔ battery** chain.

---

## 2. Scope

### In scope

1. Map **as-is** authorities for motor, ESC, battery, FC — inference, writers, BOM/arch, catalog, calc/sim.
2. Identify what ERF-1 already covers vs what is explicitly deferred to ERF-2.
3. Assess viability of **deterministic incompatibility checks** with evidence available today (declared props, SKU fields, calc bridges).
4. Propose minimum ERF-2 surface:
   - new gap types (stable IDs),
   - when to emit `INCOMPATIBLE` subsystem verdict,
   - explicit `depends_on` edges (if any),
   - whether to introduce `electronics` / `integration` subsystem lines or extend propulsion/energy only.
5. Map **ESC orphan status** (inferrable but not in `BLOCK_TO_COMPONENTS`, no catalog, no acquisition prompt).
6. Risks, non-goals, and suggested design slices (for a later Implementation Contract).
7. Acceptance probes (investigation-time only — no code).

### Out of scope

- Any `src/` implementation
- Full electrical solver (transients, wiring, connectors, geometric fit)
- Full ESC commercial catalog (H5) unless investigation proves it is **required** for MVP ERF-2
- Impl C SKU/procurement BOM
- System-level optimizer ("aplica la mejor")
- G17/G14/G13 CLI micro-fixes
- ERF-1 Slice 4b (unless investigation finds hard dependency)

---

## 3. Required inputs

| Artifact | Purpose |
|---|---|
| `docs/ENGINEERING_READINESS_VISION.md` | ERF-2 target semantics |
| `docs/system_map/*` (post C-107–C-110) | As-is authority flow |
| `.jes/artifacts/design_erf1_readiness_foundation.md` | ERF-1 locks + deferrals |
| `.jes/artifacts/implementation_report_erf1.md` | What shipped; Slice 4b deferred |
| `src/jarvis/core/engineering_readiness.py` | Extension point |
| `src/jarvis/domains/aerial.py` | ESC/battery/motor inference |
| `src/jarvis/core/system_architecture_catalog.py` | `BLOCK_TO_COMPONENTS` |
| `src/jarvis/knowledge/library.py` | Motor/battery specs; no ESC |
| `src/jarvis/core/calculation_engine.py` | KV×cells bridge |
| `src/jarvis/simulation/simulator.py` | What sim does **not** check |
| `docs/PHYSICAL_COMPONENT_CATALOG_V1.md` | H5 ESC deferred note |

---

## 4. Deliverable

**File:** `.jes/artifacts/investigation_erf2_dependency_hardening.md`

Must include:

1. Executive summary (viability of ERF-2 now vs blocked on catalog H5)
2. Answer to the central question
3. Authority map (as-is gaps: ESC orphan, INCOMPATIBLE unused, etc.)
4. Minimum viable electrical checks (predicates draft — not final contract)
5. Proposed gap catalog candidates (stable type IDs) with evidence requirements
6. Subsystem line strategy (`electronics` vs extend `propulsion`/`energy`)
7. `depends_on` model (explicit edges only — inherit ERF-1 discipline)
8. Risks and non-goals
9. Open questions for Engineer (before design doc)
10. Suggested implementation slices (for later contract)

---

## 5. Investigation constraints (inherit from ERF-1)

| Rule | Requirement |
|---|---|
| No second ProjectState | Readiness remains derived on read |
| No Continuity→Readiness circularity | Extend `engineering_readiness` only |
| No LLM gap inference | Every gap needs computed fact |
| Gap Registry central | New gaps compose; do not fork Continuity ranking in investigation |
| Stable gap type IDs | No `GAP-001` numbering |
| INCOMPATIBLE | Emit only when a deterministic checker says so — never narrative |

---

## 6. Success criteria (investigation)

Engineer can answer:

- Is ERF-2 implementable **without** ESC JSON catalog first?
- Which 3–6 gap types belong in ERF-2 MVP?
- Does ESC enter architecture/BOM in ERF-2 or stay optional?
- Is a new pure module (`electrical_compatibility.py` or similar) justified vs inline in `engineering_readiness`?

---

## 7. Workflow

```text
checkpoint-erf1 ✅
        ↓
ERF-2 INVESTIGATION (this contract) ← you are here
        ↓
Engineer review → PASS/FAIL
        ↓
design_erf2_dependency_hardening.md
        ↓
implementation_contract_erf2.md
        ↓
Claude implements
```

**Do not implement until Implementation Contract is approved.**

---

**End of investigation contract.**
