# JES Principle — Acquisition as Guided Engineering

**Date ratified:** 2026-08-10  
**Status:** RATIFIED  
**Assessment:** `.jes/artifacts/assessment_report_acquisition_guidance.md`  
**Supersedes draft:** `principle_acquisition_guided_engineering_draft.md` (same content, now binding)

## Statement

Acquisition is not only a mechanism to fill missing parameters. It is the mechanism by which Jarvis guides the user from an engineering intention to a defensible system definition.

For each acquisition target, Jarvis should eventually:

1. Name what is being defined  
2. Explain what it is and why it matters for *this* project state  
3. Show options / what Jarvis already knows  
4. Ask clearly what it needs from the user (or offer assisted choice)  
5. Validate → apply → recalculate → explain consequence → next target  

The LLM may help explain or interpret ambiguous language. It must not choose the next engineering target.

## Sequence (binding for upcoming cuts)

```text
A. Principle (this document) — done
B. P0 Plumbing (FN-017) — done
C. Thin Acquisition Brief (FN-018) — done
C′. Completeness coherence Continuity↔BOM (FN-020) — done
C″. Bare propeller size (FN-019) — done
C‴. Create→BOM handoff — later
D. Larger Guided Engineering layer — only with explicit Engineer approval; no Conversation Engine by default
```

## Explicit non-goals until separately approved

- Conversation Engine / Decision Engine  
- Replacing Acquisition Target Authority  
- Skipping deterministic Core validation  
- Implementing D inside FN-018
