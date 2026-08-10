# Architectural Assessment Contract — Acquisition as Guided Engineering

**Project:** Jarvis  
**Date:** 2026-08-08  
**Author:** JES / Cursor (Engineer Interface)  
**Assessor:** Claude Code  
**Reviewer:** Cursor  

**Status:** APPROVED FOR ASSESSMENT (not for implementation)  

**Type:** Distance / gap assessment — **no code changes**, no new subsystem, no FN cut.  
**Trigger:** Engineer observation after FN-014/015/016 + broken CLI session: Acquisition should teach and guide toward a defensible design, not only ask “¿Cuál es el valor de X?”.

---

## 1. Proposed principle (evaluate distance to this — do not build it)

Jarvis acquisition should behave as:

```text
Acquisition Target (deterministic, ProjectState)
        ↓
Knowledge / Guidance (structured, Core-owned facts + options)
        ↓
Question (what we need from the user now)
        ↓
User decision
        ↓
Validation
        ↓
Apply
        ↓
Recalculate
        ↓
Explain consequence
        ↓
Next target
```

**Example UX (illustrative, not a copy brief to implement):**

> Vamos a definir las hélices.  
> [qué son / por qué importan / qué necesita este diseño]  
> Opciones: indicar `10x4.5` · indicar set motor-hélice · decir “ayúdame a elegir”.  
> ¿Cómo quieres definirlas?

**Non-negotiables already in project identity:**

- LLM interprets language/intent; it does **not** decide which engineering target is next.
- ProjectState / acquisition authority remains source of truth.
- No Conversation Engine / Decision Engine unless Engineer explicitly approves later.

---

## 2. Your job (Claude Code)

Produce a written assessment answering: **how far are we from this approach today?**

Inspect code + recent contracts (FN-011…016), Continuity, param/component acquisition paths. **Do not implement.**

### Required sections in the report

1. **Current shape map** — What exists today for each stage of the pipeline above (Target → Guidance → Question → Decision → Validate → Apply → Recalc → Explain → Next). Label each: `present` / `partial` / `absent` / `wrong-place` (e.g. LLM doing Target selection).

2. **What FN-014/015/016 actually bought** — Precisely: routing fluency vs guidance depth. One paragraph each.

3. **Distance score** — For each pipeline stage, score `0–3` (0 = nothing useful, 3 = matches principle). Overall % or average. Justify in one line per stage.

4. **P0 plumbing vs principle** — Separate:
   - Bugs that break *any* UX (empty `pending_missing_params`, frame fallback, torque wizard on aerial, bare `10x4.5`, generic write).  
   - Gaps that are *missing Guidance* (explanation, options, “why”, consequence narrative).  
   Do not conflate them.

5. **Reuse inventory** — List existing assets that could feed Guidance without a new engine (e.g. `_COMPONENT_PROMPTS`, Continuity narrative, motor catalog / `offer_catalog_help`, param hints, architecture progress, Bug54 bridge, reasoning insights). Mark each: ready / needs thin adapter / wrong layer.

6. **Anti-patterns to avoid** — Concrete risks if we “build Guidance” carelessly (Conversation Engine drift, LLM as next-target decider, duplicating Continuity, rewriting 13 checkpoints).

7. **Recommended sequence** — Ordered options only (no implementing):
   - A) Plant principle in JES/ADR only; freeze new fluency FNs until P0 plumbing.  
   - B) Tiny P0 plumbing FN first (expected_keys + key-aware prompt), still no Guidance Engine.  
   - C) Thin “Acquisition Brief” template (deterministic strings per target) as Corte 4+.  
   - D) Larger Guidance subsystem (explicitly flag as architectural — needs Engineer approval).  
   Rank A–D for *this* moment; pick one primary recommendation.

8. **Verdict line** — One of:
   - `PRINCIPLE_NOW_PLUMBING_FIRST`
   - `PRINCIPLE_NOW_GUIDANCE_SLICE_NEXT`
   - `TOO_EARLY_FIX_ROUTING_ONLY`
   - `READY_FOR_GUIDANCE_SUBSYSTEM` (only if evidence is strong)

---

## 3. Out of scope

- Writing production code or tests  
- Redesigning Continuity formula  
- Changing physics / catalog matching  
- Implementing Conversation Engine  
- Deciding product priority propulsion-vs-battery (note as open product question if relevant)

---

## 4. Artifacts to read (minimum)

- `.jes/artifacts/implementation_contract_fn014.md` … `fn016.md` + cycle closes  
- `src/jarvis/core/acquisition_target.py`  
- `src/jarvis/core/orchestrator.py` (DEFINE_MISSING, `_handle_component_description`, Continuity/startup context)  
- `src/jarvis/core/param_definition_session.py` (`start` / `answer`)  
- `docs/PROJECT_CONTINUITY.md` (Acquisition / do-not Conversation Engine notes)  
- Plan: Acquisition Fluency Architecture  

Optional: live `runtime_snapshot.json` under the user’s project if present (empty `pending_missing_params` evidence).

---

## 5. Report format

Return markdown titled **Assessment Report — Acquisition Guided Engineering Distance**.  
Length target: tight (≈1–2 screens of substance + tables). No implementation plan disguised as assessment.

---

## 6. Cursor review criteria

- Separates plumbing bugs from Guidance ambition  
- Does not propose Conversation Engine by default  
- Recommendation is actionable for Engineer (plant principle? P0 FN? thin brief?)  
- Scores are evidence-backed  

**Verdict scale for the assessment itself:** PASS / PASS WITH NOTES / FAIL (incomplete / conflates layers)
