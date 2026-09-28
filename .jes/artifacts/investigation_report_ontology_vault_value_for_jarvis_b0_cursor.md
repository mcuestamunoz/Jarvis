# Investigation Report — Ontology vault value for Jarvis (`B0-ontology-vault-value-for-jarvis`)

**IC:** [`investigation_contract_ontology_vault_value_for_jarvis_b0.md`](investigation_contract_ontology_vault_value_for_jarvis_b0.md)  
**Investigator:** **Cursor** (independent parallel run — Engineer asked for dual reports to compare with Claude)  
**Date:** 2026-09-27  
**Status:** **LANDED (investigation)** — awaiting Engineer compare + Cursor review of Claude’s twin · no product code · tip stays **`v0.5.44`**

**Twin:** Claude should write `investigation_report_ontology_vault_value_for_jarvis_b0.md` (no `_cursor` suffix). Compare both; do not treat this file as the sole review of record for Claude’s work.

---

## 0. Honesty first

```text
ontology explains ≠ library declares ≠ Continuity decides ≠ step() computes
rich vault (target) ≠ today’s stub bodies (out of scope to grade)
retrieve/cite ≠ Conversation Engine ≠ invent mass/W/autonomy
```

This report answers: **if `ontology/` were solid and rich, what would Jarvis gain, and how to wire it.**  
Structure of the live vault is used as **shape of intent**. Incomplete note bodies are **not** scored as a pass/fail of the Engineer.

---

## 1. Structure inventory (shape only)

| Band | `.md` notes (approx.) | Role in taxonomy |
|---|---|---|
| `00_Mapa/` | 3 (+ README) | Hub index (`Ingenieria.md`), roadmap outline, **Plantilla** for rich notes |
| `01_Matematicas/` | ~30 | Algebra → linear algebra → calculus → ODEs |
| `02_Fisica/` | ~16 | Mechanics, fluids, EM, thermo |
| `03_Ingenieria/` | ~20 | Systems, electronics, structures, aero, classical control |
| `04_Robotica/` | ~19 | Sensors, actuators, kin/dyn, robot control, perception, nav |
| `05_Problemas/` | empty dir | Reserved problem bank |
| Totals | **~90** `.md` | Wikilink edges observed **~356** (Obsidian-style `[[…]]`) |

**Hub map** (`00_Mapa/Ingenieria.md`): four layers — Matemáticas → Física → Ingeniería aplicada → Robótica — matching the folder bands. That is the intended ontology spine.

**Roadmap** (`00_Mapa/Roadmap.md`): hierarchical outline of the same tree (control, sensors, motors, localization, …). Acts as a **curriculum index**, not product SoT.

**Plantilla** (`00_Mapa/Plantilla.md`): already an aspirational note contract — frontmatter (`id`, `area`, `estado`, …) + sections DEFINICION / INTUICION / FUNDAMENTO / EJEMPLO / CONEXIONES / ERRORES / ESTADO. This is the seed of §5’s quality bar; Jarvis-specific fields are not there yet.

**Split from craft knowledge (locked, re-confirmed):**

| Path | Role |
|---|---|
| `ontology/` | Theory / conceptual graph (this vault) |
| `library/` | Craft catalog SoT (SKUs, cited dims) |
| `src/jarvis/knowledge/` | `ComponentLibrary` reader of `library/` only (`retriever.py` currently empty — name collision risk if reused for ontology) |

---

## 2. Value if the vault were rich (surfaces A–G)

For each: **gain** · **mechanism** · **risk if miswired** · **minimum Buy grain**.

### A · Craft Continuity / User Guide

| | |
|---|---|
| **Gain** | Status / assists can answer *why* (“por qué declarar masa / potencia / no convertir RF mW”) with a stable concept cite, not a one-off LLM essay. |
| **Mechanism** | Optional “explain” attachments: Continuity `next_useful_step` or CLI help → link to `ontology/…` note ids. User Guide §12 stays the command SoT; ontology is the *rationale* layer. |
| **Risk** | Continuity starts *choosing* engineering numbers from notes → SoT collapse. |
| **Grain** | Docs + optional read-only cite map (R3), after note contract (R1). |

### B · Catalog / bind honesty

| | |
|---|---|
| **Gain** | Shared vocabulary for locks already in product: cited vs estimated, OP ≠ intrinsic thrust, RF mW ≠ DC W, estimated_temporary blocks attest. |
| **Mechanism** | Catalog / assist docs and error strings cite concept nodes (`Electrónica de potencia`, `Corriente y circuitos`, …) when refusing invent. |
| **Risk** | Ontology “formula” used to invent `power_w` for a SKU lacking citation. |
| **Grain** | Frontmatter `never_invents` + doc cites (R1); no catalog writer from vault. |

### C · Geometry / Board

| | |
|---|---|
| **Gain** | Engineer literacy: envelope ≠ CAD, AABB screening ≠ fit VERIFIED, cylinder glyph ≠ turned standoff. |
| **Mechanism** | USER_GUIDE / ARCHITECTURE honesty lines + Board tooltips → ontology nodes under Mecánica estructural / Aerodinámica (as *concepts*, not STEP). |
| **Risk** | Treating Board boxes as CAD because a note says “análisis estructural”. |
| **Grain** | Docs/teach only until a separate geometry Buy; ontology does not drive poses. |

### D · Platform FS (C36–C43 ladder)

| | |
|---|---|
| **Gain** | Human map from product names (complementary filter, PD attitude, ScriptedSpi, WHO_AM_I, Safety allow≠execute) → classical/robot control + sensors nodes. Onboarding and honesty docs get sharper. |
| **Mechanism** | Crosswalk table in docs or `ontology/00_Mapa/` (e.g. “Jarvis FS ↔ conceptos”) — **teach**, not import ontology into `native/`. |
| **Risk** | Rewriting controllers from textbook notes; claiming “PID from ontology = flying”. |
| **Grain** | Doc crosswalk Buy (tiny) after R1; never FS code from vault. |

### E · LLM

| | |
|---|---|
| **Gain** | NL → User Guide cheatsheet: LLM proposes Continuity phrases; ontology cites justify *why*, and hard gates still block inventing physics quantities. |
| **Mechanism** | Extend grounding beside `ActionPolicy` / semantic adapters: retrieve top-k notes by intent tags; attach cite paths; **never** let note text set `mass_g` / `power_w` / autonomy. |
| **Risk** | RAG as shadow calculator; Conversation Engine rebirth. |
| **Grain** | R4 only after R1 + hard `never_invents` tests; ActionPolicy remains supreme. |

### F · Future Assistant (`intelligence/`)

| | |
|---|---|
| **Gain** | Assistant asks “what is C-rate / what measurement unlocks autonomy?” → retrieve ontology; craft Continuity and FS stay separate. |
| **Mechanism** | Read-only retrieve/cite module under future `intelligence/` (Assistant DC placement). Vault path configurable → `ontology/`. |
| **Risk** | Stuffing ontology into `flight_software/` or `core/orchestrator`. |
| **Grain** | R2 after Assistant placement ★ + empty `intelligence/` scaffold IC. |

### G · HD-* / lab walls

| | |
|---|---|
| **Gain** | Notes state *what experiment* would unlock a claim (OP→consumo, ESC loss, …) without shipping fake curves. |
| **Mechanism** | HD-004 (etc.) docs link to ontology “measurement / operating point” concepts; vault section `never_invents: autonomy_min`. |
| **Risk** | “Theory complete ⇒ autonomy validated.” |
| **Grain** | Doc links only; HD-* stay lab-owned. |

---

## 3. SoT seams (normative)

```text
human
  → Continuity / IDLE / User Guide commands     (craft SoT mutations)
  → library/ via ComponentLibrary               (catalog SoT)
  → flight_software / native                    (vehicle compute)
  → ontology/                                   (explain / retrieve only)
  → LLM                                         (NL propose + narrate; gated)
  → intelligence/ (future)                      (tasking + retrieve; not FC)
```

**Forbidden edges:**
- ontology → write `library/` or workspace  
- ontology → set Safety allow / `step()` setpoints  
- LLM → numeric craft fields sourced only from ontology prose  
- merge vault into `src/jarvis/knowledge/` (name already means catalog)

**Name collision note:** `src/jarvis/knowledge/retriever.py` is empty today. A future ontology retriever must **not** silently occupy that file for theory RAG — prefer `intelligence/ontology_retrieve` (or rename catalog package later under its own IC).

---

## 4. Aspirational quality bar (“rich enough”)

Extend existing `Plantilla.md` rather than invent a parallel template:

```text
# frontmatter (target)
id: slug
nombre: …
area / subarea
estado: stub | draft | solid
jarvis_relevance: [craft | catalog | fs | assistant | none]  # multi-ok
never_invents: [mass_g, power_w, autonomy_min, thrust_gf, …]
formula_citation: …   # required if any equation claimed as numeric truth
```

**“Rich enough for retrieve” (minimum bar, target):**  
A **vertical spine** solid from Matemáticas (álgebra lineal / EDO) → Control → Control robótico / Sensores de movimiento, plus Electrónica (corriente/potencia) and one HD-facing note that states the lab wall — each with DEFINICION + CONEXIONES + `never_invents` + `estado: solid`. Lateral stubs may remain.

This is a **fill target for offline enrichment**, not a grade of the current tree.

---

## 5. Ranked options (R0–R4)

| Rank | Option | Verdict |
|---|---|---|
| **1 (default)** | **R1** — Vault hygiene offline: apply Plantilla + Jarvis frontmatter on the spine; Engineer fills; still no product code | Best leverage / risk ratio now |
| **2** | **R2** — After Assistant placement ★ + tiny `intelligence/` scaffold: read-only search/cite over `ontology/` | Real product seam; needs placement lock first |
| **3** | **R0** — Park product integration; enrich vault with zero Jarvis coupling | Safe if attention is elsewhere; leaves value on the table |
| **4** | **R3** — Continuity optional explain-cites | Useful but easy to over-couple; do after R1, thin IC |
| **5** | **R4** — LLM grounding with ontology cites | Highest misuse risk; only after R1 + automated `never_invents` tests |

**Default path:**

```text
R1 (offline spine + Plantilla/Jarvis fields)
  → Engineer ★ Assistant placement DC (if not already)
  → IC: intelligence/ empty scaffold
  → R2 retrieve/cite read-only
  → optional thin R3 / later R4
STOP: no R4 before R1; no merge into src/jarvis/knowledge/; no FS code from notes
```

---

## 6. What a rich vault would *not* replace

- Catalog SKUs or caliper bags  
- Continuity next-step logic  
- HD-004 measurement campaign  
- CAD / Board fit VERIFIED  
- C42 WHO_AM_I on copper / SPI1 live  

Those stay their own SoTs and parks.

---

## 7. Self-check vs IC §7

| Gate | Result |
|---|---|
| §3 surfaces A–G | Covered |
| Structure inventory | Covered (§1) — counts are descriptive of shape |
| SoT seams | Covered (§3) |
| Aspirational quality bar | Covered (§4) — builds on Plantilla |
| Ranked R0–R4 + default | Covered (§5) — **default R1 → R2** |
| No product code | Confirmed |
| Did not grade stubs as Engineer fail | Confirmed — incompleteness noted only as “not the question” |
| Forbidden claims absent | Confirmed |

---

## 8. Ask of Engineer (compare with Claude)

1. Read Claude’s report beside this one.  
2. ACCEPT investigation when both reviewed (or ACCEPT one path).  
3. If default stands: start **R1 offline** (no IC required for personal note fill); next product IC only when ready for **R2** after Assistant placement ★.

**Cursor does not ★ ACCEPT this investigation alone** — Engineer compares twins first.
