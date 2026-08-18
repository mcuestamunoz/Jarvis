# Implementation Contract — ERF-1 Investigation (Read-only)

**Type:** Investigation / Architecture design input — **zero `src/` changes**  
**Date:** 2026-08-18  
**Status:** READY FOR ENGINEER  
**Requester:** Engineer  
**Executor:** Cursor/JES  
**Vision anchor:** `docs/ENGINEERING_READINESS_VISION.md`  
**Primary question:**  
**"¿Cuál es la autoridad única y determinista que puede responder 'qué le falta a este proyecto para ser ensamblable' reutilizando autoridades existentes, sin segunda ProjectState ni duplicar Continuity/BOM/Simulation?"**

---

## 1. Objective

Produce an ERF-1 investigation that defines the smallest viable authority model for Engineering Readiness using existing system primitives.

The output must be sufficient for Engineer to decide ERF-1 design/contract scope **before any implementation**.

---

## 2. Scope

### In scope

1. Map existing authorities that already compute partial readiness:
   - architecture progress,
   - component/BOM completeness,
   - physical requirements,
   - simulation quality/status,
   - continuity ranking.
2. Propose one deterministic aggregation model (single authority surface) for readiness and gaps.
3. Define required data contract for:
   - readiness lines,
   - gap registry (`GAP-xxx`),
   - dependency ordering,
   - next-step handoff to continuity.
4. Define what ERF-1 explicitly does **not** solve yet (electrical solver, fit/cabling, full Impl C).
5. Produce acceptance probes (unit + CLI) for ERF-1 behavior only.

### Out of scope

- Any `src/` implementation
- Refactors to unrelated routing paths
- Full assembly solver
- Full catalog commercialization/BOM procurement engine

---

## 3. Required inputs

| Artifact | Purpose |
|---|---|
| `docs/ENGINEERING_READINESS_VISION.md` | Target semantics and boundaries |
| `docs/ARCHITECTURE.md` + `docs/system_map/*` | As-is authority and data flow |
| `.jes/artifacts/cli_findings_post_catalog_bind_v1.md` | Real continuity/catalog gaps |
| `.jes/artifacts/implementation_review_cli_polish.md` | Recent behavior and residuals |
| `src/jarvis/core/orchestrator.py` | Startup context, arch progress, routing surfaces |
| `src/jarvis/core/project_continuity.py` | Current next-step authority |
| `src/jarvis/core/project_closure.py` | BOM and requirements derivation |
| `src/jarvis/core/phase_layer.py` | Phase/readiness proxy |
| `src/jarvis/simulation/simulator.py` | Simulation authority output |

---

## 4. Deliverable

**File:** `.jes/artifacts/investigation_erf1_readiness_foundation.md`

Must include:

1. Executive summary (viability of ERF-1 now)
2. Authority map (current vs target, no duplicated truth)
3. Proposed single authority surface (readiness snapshot + gap registry)
4. Data contract draft for ERF-1
5. Dependency and prioritization rules
6. Risks and non-goals
7. Suggested implementation slices (for later contract)

---

## 5. Quality gates

| Gate | Criterion |
|---|---|
| G1 | No second state store proposed |
| G2 | No duplication of continuity/BOM/simulation computation logic |
| G3 | Every target field maps to existing deterministic evidence source |
| G4 | Clear ERF-1 boundary vs ERF-2 / Impl C |
| G5 | Includes concrete CLI/readout examples |
| G6 | Read-only investigation (no product behavior edits) |

---

## 6. Success criteria

Engineer can approve (or reject) a concrete ERF-1 design direction and then request a focused implementation contract without reopening architecture ambiguity.

