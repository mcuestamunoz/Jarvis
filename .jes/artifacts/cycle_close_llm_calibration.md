# Cycle close — FASE_LLM / calibración routing

**Date:** 2026-08-05  
**Status:** CLOSED  
**Baseline tests at close:** 1369 passed

## Intent

Validar la capa LLM (interpret + semantic iterate) con ≥30 inputs reales, medir routing y corregir fricciones accionables.

## Evidence

- Session log: `.jes/artifacts/calibration_session.jsonl` (35 turns)
- Summary: `.jes/artifacts/calibration_summary.md`
- Path: `JarvisSessionManager.chat` (= MCP/CLI)

## Fixes shipped this cycle

| Finding | Fix |
|---|---|
| Sticky `ITERATE_INTERACTIVE` eats strong intents | Hard preempt + soft Bug 7 preserved |
| `optimiza para payload` / `mejora la estabilidad` → iterate | `EXPLORE_PATTERNS` + goal keywords for all DSE goals |
| `más chicha` → battery preseed @ conf 1.0 | Lexical grounding + drop invented `valor`; prompt guidance |
| Snapshot `mode` as str crashes prompt | Coerce `OrchestratorMode` on restore |

## Explicitly out of scope / deferred

- Analyze latency (~55–70 s) — product/infra, not routing
- Noisy `semantic_trace` on some analyze turns — cosmetic
- `autonomía` alone → calculate — minor; not blocking
- `CONFIDENCE_THRESHOLD` retune — deferred until more grounded preseeds
- Motor suggestions UX value — **next cycle**

## Verdict

FASE_LLM routing cycle **closed**. Deterministic gates (preempt, explore, grounding) cover the actionable misroutes from calibration. Residual items are non-blocking or belong to other cycles.
