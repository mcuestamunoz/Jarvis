# G25 — bare `sistema` → LLM leak

**Date:** 2026-08-21  
**Severity:** 🟡 product / routing  
**Status:** OPEN — registered during Impl C Engineer CLI walk  
**Category:** Intent / Continuity routing  
**Project evidence:** `autonomia-5540bda0ac16` — after `aplica la mejor` (G24), Engineer typed `sistema` to inspect components  
**Related:** [cli_finding_g24…](cli_finding_g24_dse_apply_only_top1_catalog_unselectable.md) (same session; distinct root)

---

## One-line

Bare phrase `sistema` is not a stable Continuity/view verb; the turn falls through to the **LLM** instead of a deterministic project/system view.

---

## Observed

```text
User > aplica la mejor   # abstract DSE #1 — catalog_ref cleared (G24)
User > sistema
Jarvis > … (LLM narration / analyze path — undesired)
```

Engineer intent: inspect design/components (equivalent to a system view or component summary).  
Actual: non-deterministic LLM path.

**Workaround used in the same walk:** `estado` / `qué motores tenemos` (deterministic).

---

## Expected

One of:

| Option | Behavior |
|---|---|
| **A** | `sistema` → deterministic render of system/components view (e.g. `views/sistema.md` content or equivalent Continuity block) — **0 LLM** |
| **B** | `sistema` → short honest refuse + CTA (`estado`, `qué motores tenemos`) — **0 LLM** |
| **C** | Document that `sistema` is **not** a product verb; never teach it in briefs |

Preferred: **A** if a system view already exists in the pipeline; else **B**.

---

## Why it matters

Full-project walks need a reliable way to inspect component identity (`catalog_ref`, frankenstein state after G24 apply) without burning an LLM turn or getting invented narration.

---

## Out of scope / not this bug

- G24 apply-only-`#1` (separate).  
- Missing `catalog_ref` after abstract apply (G5 correct; G24 steers user into it).  
- Impl D / BOM.

---

## Suggested follow-up

Small routing IC: add `sistema` (and likely ES synonyms) to intent patterns → `project_status` or dedicated view action. Do **not** block Impl D.

---

**End of finding.**
