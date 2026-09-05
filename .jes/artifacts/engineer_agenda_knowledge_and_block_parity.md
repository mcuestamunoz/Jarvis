# Engineer Agenda — Knowledge and block parity

**Date:** 2026-09-04  
**Authority:** Engineer (`Procede` phase transition)  
**Status:** ACTIVE AGENDA — not an Implementation Contract  
**★:** [engineer_ratification_phase_transition_knowledge_parity.md](engineer_ratification_phase_transition_knowledge_parity.md)

---

## 1. Phase statement

Propulsion / energy / Structure A (level A) / CLI fail-routing / block closure
for prop+energy have reached a level where walks expose **physics and claim
honesty**, not construction emptiness.

Other architecture blocks and claim surfaces are **behind** that bar. The next
phase raises them by answering knowledge questions — not by shipping another
convenience feature on the hot path.

---

## 2. Maturity bar (what “at the level of current” means)

A block/function is at parity with the current prop/energy loop when it has,
to a comparable degree:

| Axis | Meaning |
|---|---|
| **Know** | Explicit model or data authority (what variables exist, what they mean) |
| **Claim** | What Jarvis may say (PASS / incomplete / unverifiable / CERRADO) without overclaim |
| **Guide** | Continuity / acquisition can name the next missing fact without false loops |
| **Measure** | What would falsify or strengthen the claim (bench, OP, catalog row, declaration) |

Current hot stack approximately meets Know / Claim / Guide for thrust +
simplified hover energy + Structure A class screening. **Measure** is still
weak (legacy OP estimate, no C-rating, HD-* parked). That weakness is now a
**knowledge purchase** question, not a silent code invention.

---

## 3. Asymmetry map (as-is, for agenda only)

| Area | Relative maturity | Next question type |
|---|---|---|
| Propulsion (motors / props / thrust) | Highest in product | Knowledge: OP / catalog evidence strength — not more routing polish |
| Energy (Wh / nameplate W / autonomy L1) | High, honest limits visible | Knowledge: when may autonomy claims strengthen — lab or refuse |
| Structure A (mass + class) | Usable level A | Freeze CAD / fit; parity elsewhere first |
| Control (FC / sensors) | Declarative acquisition only | Know/Claim: what does “control complete” assert? |
| Electronics / ESC | Partial / declarative | Know/Claim vs H5 freeze |
| Catalog honesty (nominal vs design-space) | Deferred C-A1 | Product semantics — open only if Engineer names it as a knowledge decision, not default polish |
| DSE explore/apply | Honest refuse on nameplate W | Useful; not the center of the next phase |
| Core audit / orchestrator size | Debt logged | Not phase-default; investigate only with Engineer ★ |

---

## 4. Governing questions (Engineer picks one next)

Before any IC:

1. **Know** — Which block’s missing variables are blocking parity most?
2. **Claim** — Which current sentence over-claims (e.g. CERRADO with weak OP,
   ASSEMBLY READY with `risky` / `low_margin`)?
3. **Measure** — What measurement (or explicit refuse-to-measure) would change
   a claim without inventing physics?
4. **Buy** — Is the next purchase **code**, **catalog data**, **lab (HD-\*)**,
   or **investigation-only**?

Default stance: prefer investigation / product lock over implementation until
(4) is answered.

---

## 5. Candidate threads

**Chosen closed:** Claim hygiene under ASSEMBLY READY — **CLOSED** (suite **2160**).

**Chosen closed:** **Control parity B1** — **CLOSED** (suite **2164**).
[implementation_review_control_parity.md](implementation_review_control_parity.md).

**Phase status:** both planned knowledge/block-parity threads done. Awaiting
Engineer ★ to **close this phase** and name the next feature cycle.

Remaining (not ordered, not authorized until Engineer picks):

- **OP / propulsion evidence strength** / weak-OP Continuity wiring (N4 residual)
- **B2** declaration-only subsystems vs ASSEMBLY_READY (future ★)
- **Catalog honesty (C-A1)** — only as semantics decision
- **Hardware debt (HD-001 / HD-002)** — only with lab
- C-081 / C-108 map debt (not phase-default)

Frozen unless reopened: P26 / P27-A loaded autonomy, H5 ESC catalog, G24-B
scoring rewrite, CAD/FEA, Conversation Engine, broad `orchestrator.py` split.

Remaining (not ordered, not authorized until Engineer picks):

- **OP / propulsion evidence strength** / weak-OP Continuity wiring (N4 residual)
- **Catalog honesty (C-A1)** — only as semantics decision
- **Hardware debt (HD-001 / HD-002)** — only with lab

Frozen unless reopened: P26 / P27-A loaded autonomy, H5 ESC catalog, G24-B
scoring rewrite, CAD/FEA, Conversation Engine, broad `orchestrator.py` split.

---

## 6. Operating rule for Claude / JES

- No `src/` without a ratified IC named after an Engineer choice from §4–§5.
- No “small polish IC” on prop/energy/routing as the default next cycle.
- **Claim hygiene:** Investigation Contract is open — Claude writes the report;
  no IC until review + Engineer ★ on the claim matrix.
- Other §5 threads: JES may draft an Investigation Contract only after the
  Engineer picks them.

---

## 7. Success condition for this phase

Other blocks show the same property the walks just showed for prop/energy:

> Limits are visible and claims stay honest — even when the user cannot yet
> close the design.
