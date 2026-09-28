# Investigation Review — Ontology vault value for Jarvis (`B0-ontology-vault-value-for-jarvis`)

**IC:** [`investigation_contract_ontology_vault_value_for_jarvis_b0.md`](investigation_contract_ontology_vault_value_for_jarvis_b0.md)  
**Claude report:** [`investigation_report_ontology_vault_value_for_jarvis_b0.md`](investigation_report_ontology_vault_value_for_jarvis_b0.md)  
**Cursor twin report:** [`investigation_report_ontology_vault_value_for_jarvis_b0_cursor.md`](investigation_report_ontology_vault_value_for_jarvis_b0_cursor.md)  
**Reviewer:** Cursor (independent — not Claude self-PASS)  
**Date:** 2026-09-27  

**Verdict on Claude report:** **PASS** — ready for Engineer ★ ACCEPT of the **investigation** (not a product Buy). Tip stays **`v0.5.44`**.

---

## 0. Scope check (IC)

| Gate | Claude | Cursor twin |
|---|---|---|
| Structure inventory, not stub grading | **Pass** | **Pass** |
| Surfaces A–G with gain/mechanism/risk/grain | **Pass** | **Pass** |
| SoT seams (ontology ≠ catalog ≠ Continuity ≠ FS) | **Pass** | **Pass** |
| Aspirational quality bar on Plantilla | **Pass** | **Pass** |
| Ranked R0–R4 + default + stops | **Pass** | **Pass** |
| No product code / no version bump | **Pass** (confirmed dirty tree: report only + prior ontology README/workspace) | same |
| Forbidden claims absent | **Pass** | **Pass** |

---

## 1. Where the two reports **agree** (high confidence)

1. **Four-role SoT** — ontology explains; Continuity decides; catalog declares; FS computes. Never collapse.  
2. **Plantilla.md is the right seed** — add `jarvis_relevance` + citation/`never_invents`; don’t invent a parallel template.  
3. **Default first step = R1** (vault hygiene / template fields) before programmatic consumers.  
4. **R2 (`intelligence/` retrieve) blocked** until Assistant DC is ★.  
5. **No merge** into `src/jarvis/knowledge/`.  
6. **LLM must quote/cite, never compute numbers** from notes (`ActionPolicy` stays closed).  
7. **Docs crosswalks** (FS ladder, HD-*, geometry honesty) are cheap proofs of the seam.

---

## 2. Where they **differ** (Engineer pick)

| Topic | Claude | Cursor twin | Reviewer note |
|---|---|---|---|
| **Graph evidence** | Stronger: 363 links, **~77% dangling** (~270 missing notes); names `[[IMU]]`/`[[Giroscopio]]` next to C6/C42 | Weaker counts (~356 edges); less dangling analysis | Prefer Claude’s dangling metric as the “shape of intent” proof |
| **Extra artifacts** | Inventories `conceptos.json` (94 registry rows) | Mentions Plantilla/Roadmap; skips conceptos.json | Claude win — registry is part of the skeleton |
| **Order after R1** | Docs crosswalks → **R3/R4** → **R2 last** | **R2 next** (after Assistant ★) → optional R3/R4 | **Real fork.** If next product focus is Assistant, Cursor order is tighter. If next focus is craft explain/LLM, Claude order is tighter. |
| **R3 risk** | Flags Continuity as highest-decision-density (careful IC) | Same risk, slightly less emphasis | Agree with Claude’s caution on R3 |
| **Name collision** | Silent | Flags empty `src/jarvis/knowledge/retriever.py` | Keep Cursor note: future ontology retrieve ≠ that file |

**Synthesized default (reviewer recommendation to Engineer):**

```text
R1 (Plantilla + jarvis_relevance + never_invents/citation)
  → thin docs crosswalks (FS table Claude §2.D + HD/geometry cites)   [no src/]
  → THEN branch:
       (a) Assistant path: ★ DC placement → intelligence scaffold → R2
       (b) Craft/LLM path: thin R4 (goal_context cite) and/or careful R3
STOP: no R2 before Assistant DC ★ · no R3/R4 before R1 · no FS/library reads of ontology
```

---

## 3. Claude-only highlights worth keeping

- Dangling-wikilink quantification as primary “intent ≫ content” evidence.  
- Concrete FS↔ontology crosswalk table (filter/attitude/PD/mixer/plant/SPI).  
- `goal_context` “quote, never decide” as proven precedent for surface E.  
- Explicit stop: do not start R3/R4 before R1 template gaps closed.

---

## 4. Residual notes (not FAIL)

| # | Note | ¿Deuda? |
|---|---|---|
| N1 | `ontology/README.md` + `.obsidian/workspace.json` dirty on disk — pre-existing / Obsidian; not Claude product edits. Fold into a hygiene commit when convenient. | No |
| N2 | Engineer still chooses branch (a) Assistant-first vs (b) craft-explain-first after R1. | Decision, not defect |

---

## 5. Reviewer ask of Engineer

1. ★ **ACCEPT investigation** (both reports + this review as compare pack).  
2. Pick synthesized default or amend order (Assistant-first vs LLM/Continuity-first).  
3. Next product work is **not** automatic — R1 can be offline Obsidian work or a tiny vault-hygiene IC; R2 waits on Assistant DC ★.

No tag · tip **`v0.5.44`**.
