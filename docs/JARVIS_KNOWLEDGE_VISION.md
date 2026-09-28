# Jarvis — Knowledge Vision (`ontology/` explain layer)

**Status:** Directional — not implementation authority  
**Type:** Vision / To-be (+ as-is placement locks)  
**Date:** 2026-09-27  
**Epoch:** **`v0.6.0` TAGGED** (ontology explain branch CLOSED) · bloque **`0.5` CLOSED** @ historical **`v0.5.44`** · next product slice Assistant **`0.6.1+`**  
**Investigation SoT:** [B0 review](../.jes/artifacts/investigation_review_ontology_vault_value_for_jarvis_b0.md) · [Claude report](../.jes/artifacts/investigation_report_ontology_vault_value_for_jarvis_b0.md)

---

## 1) Purpose

Name the **conceptual knowledge** role in Jarvis so that enrichment of `ontology/` and any future retrieve/cite Buys stay on the correct side of the SoT fences.

This document is **not** an Implementation Contract. It does **not** authorize `src/` changes, RAG, or Assistant code. Only Engineer-★ ICs move behavior into product packages; only validated as-is facts move into [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## 2) Document boundaries (anti-drift)

| Truth | Where |
|---|---|
| As-is architecture | [`ARCHITECTURE.md`](ARCHITECTURE.md) · [`system_map/`](system_map/README.md) |
| Execution queue | [`IMPLEMENTATION_TASKS.md`](IMPLEMENTATION_TASKS.md) |
| Platform / skills to-be | [`PLATFORM_CAPABILITY_VISION.md`](PLATFORM_CAPABILITY_VISION.md) |
| Engineering readiness to-be | [`ENGINEERING_READINESS_VISION.md`](ENGINEERING_READINESS_VISION.md) |
| **Knowledge / explain to-be (this file)** | [`JARVIS_KNOWLEDGE_VISION.md`](JARVIS_KNOWLEDGE_VISION.md) |
| Live vault (notes) | [`ontology/`](../ontology/README.md) |
| Craft catalog SoT | `library/` via `src/jarvis/knowledge/` (`ComponentLibrary` only) |

**Name lock:** do **not** merge `ontology/` into `src/jarvis/knowledge/`. That package name already means catalog reader. Future retrieve lives under future `intelligence/` (gated by Assistant placement ★), never as a silent reuse of empty `knowledge/retriever.py`.

---

## 3) Core discovery

Jarvis already has four hard roles:

```text
Continuity / core     DECIDES next craft step
library/              DECLARES cited physical facts (SKU)
flight_software/      COMPUTES vehicle behavior (sim / native)
LLM + ActionPolicy    NARRA / propone (4 verbs; no invent physics)
```

What was missing — and what epoch **`0.6.x`** opens — is a fifth role:

```text
ontology/             EXPLAINS concepts (prose + wikilinks)
```

A rich vault is **reusable “why” memory**: C-rate, OP ≠ intrinsic thrust, complementary filter, WHO_AM_I as a concept — cited by docs, humans, and (later) Assistant/LLM grounding. It never replaces catalog numbers, Continuity decisions, or `step()`.

---

## 4) As-is placement (2026-09-27)

- Vault at repo root: `ontology/` (Obsidian open-folder). ~90 notes; wikilink graph already denser than materialized bodies (“shape of intent”).
- `grep -rl ontology src/jarvis/` → empty. Product code does not read the vault today.
- `ontology/README.md` states the split from catalog / Continuity / FS / LLM invent.

---

## 5) Surfaces that gain if the vault is rich (summary)

| Surface | Gain (if rich) | Product grain (later) |
|---|---|---|
| A Craft / Continuity explain | Stable *why* beside status text | Optional cite links (careful IC) |
| B Catalog honesty | Shared vocabulary for locks (OP, RF≠DC, cited vs estimated) | Docs crosswalk; never write catalog from notes |
| C Geometry / Board | Literacy: envelope ≠ CAD, AABB ≠ fit | Docs/teach only |
| D Platform FS ladder | Human map C6–C43 ↔ classical/robot concepts | Docs crosswalk table; never FS imports |
| E LLM | Quote/cite beside `goal_context` pattern | Additive grounding IC; ActionPolicy unchanged |
| F Assistant | Retrieve “what is C-rate?” vs catalog “this pack’s C-rate” | R2 after Assistant DC ★ |
| G HD-* / lab | Shape of the missing experiment, no fake curves | Doc links only |

Full gain/mechanism/risk/grain: Claude B0 report §2.

---

## 6) SoT seams (normative)

```text
ontology/          EXPLAINS
   → docs/         cite (crosswalks, User Guide, HD-*)
   → intelligence/ retrieve/cite (future, gated)
   → llm/          narrate with cites (future IC; quote never decide)
   ✗ Continuity    does not read ontology to decide
   ✗ library/      does not read ontology; notes never restate SKU numbers
   ✗ flight_software / native/  never read ontology
```

**Forbidden claims:** ontology replaces catalog · LLM invents mass/W from notes · vault drives `step()` · vault is production RAG-ready today.

---

## 7) Default path (epoch `0.6.x`)

| Step | What | Tag / code |
|---|---|---|
| **R1** | Vault hygiene + spine offline | **DONE** @ **`v0.6.0`** |
| Docs crosswalks | FS / HD / geometry teach tables | **DONE** @ **`v0.6.0`** ([`ONTOLOGY_CROSSWALKS.md`](ONTOLOGY_CROSSWALKS.md)) |
| Branch **(a)** | Assistant DC ★ → `intelligence/` → R2 → terminal | **DONE** @ **`v0.6.1`**–**`v0.6.4`** — A0–A5 ★ CLOSED (scaffold, retrieve, `jarvis explain`, alias/FS/HD maps) |
| Branch **(b)** | R3 Continuity cite | **Delivered @ package `0.6.5`** ([report](../.jes/artifacts/implementation_report_continuity_explain_cite_r3_b1.md)) — Continuity emits finite `explain_topics`, CLI resolves optional Conceptos; vault still never decides the craft step. Awaiting Cursor review + Engineer ★ ACCEPT. R4 LLM cite: **Later** |
| **R0** | Park product coupling; enrich vault only | Always available fallback |

**Versioning:** tip **`v0.6.0`** closes ontology explain. Assistant Buys tag on **`0.6.1+`**. Bloque `0.5` tip remains historical **`v0.5.44`**.

---

## 8) Spine enrichment protocol (offline — how we fill)

Goal: make a **vertical spine** retrieve-ready for craft + FS explain, without grading the whole vault or inventing catalog numbers.

### 8.1 Scope

~12 concept nodes (hubs + critical dangling leaves), not all ~90 notes and not all ~270 dangling targets.

**Spine order (fill top → down, then leaves):**

1. Álgebra lineal / Vectores  
2. Dinámica (Mecánica)  
3. Momento y rotación  
4. Control clásico  
5. Control robótico / control de movimiento  
6. Sensores de movimiento (hub)  
7. **IMU** · **Giroscopio** · Acelerómetro (materialize dangling)  
8. Actuadores / Motores hub · **Motor DC** (if still dangling)  
9. Corriente y circuitos / electrónica de potencia  
10. Operating point vs intrinsic capability (concept note — no SKU watts)  
11. C-rate / batería (concept — no pack Wh invented)  
12. Magnetismo (yaw) · Navegación (C39 map) · HD-facing “thrust-stand measurement shape”

Exact paths follow live `ontology/` folders; create leaf notes where wikilinks already point.

### 8.2 Per-note contract (extend Plantilla — do not fork a second template)

Frontmatter target:

```yaml
id: <slug>
nombre: <concepto>
area: <banda>
subarea: <…>
nivel: <…>
estado: stub | draft | solid   # consolidate with body [ESTADO] over time
jarvis_relevance: [craft | catalog | fs | assistant | none]  # multi-ok
never_invents: [mass_g, power_w, thrust_gf, autonomy_min, …]  # when relevant
formula_citation: <textbook/section or "toy/example only">     # if any equation
tags: []
```

Body: keep existing sections. Prefer substance in:

- `[DEFINICION]` — one crisp paragraph  
- `[INTUICION]` — engineer-facing picture  
- `[CONEXIONES]` — wikilinks along the spine + to Jarvis surfaces in prose (“used when explaining C7 attitude”)  
- `[ERRORES]` — honesty traps (OP≠intrinsic, RF mW≠DC W, envelope≠CAD, …)  
- `[APLICACIONES]` — *where Jarvis cites this*, not SKU values  
- Fórmulas only with `formula_citation` or marked toy/example  

**Done for a spine node (`estado: solid`):** DEFINICION + INTUICION + CONEXIONES filled; `jarvis_relevance` set; if any number/formula → citation or explicit toy; `never_invents` listed when the concept touches craft/FS quantities; no restated `library/` SKU row.

### 8.3 What we deliberately do *not* do while enriching

- Invent thrust/Kv/Wh for a real SKU  
- Copy Continuity decision rules into notes  
- Paste controller gains from `flight_software/` as “truth” (disclose toy if mentioned)  
- Build RAG / touch `src/` from Obsidian editing  
- Grade non-spine stubs as failures — incompleteness outside the spine stays accepted

### 8.4 Cadence

Engineer (or offline session) fills notes in Obsidian against this protocol.  
Cursor/Claude may: propose note outlines, suggest wikilinks, draft R1 Plantilla IC, draft docs crosswalks.  
Product code waits on named ICs (R2/R3/R4).

---

## 9) When ARCHITECTURE / system_map get updates

| Event | Doc action |
|---|---|
| This vision + vault placement | Pointer in `ARCHITECTURE.md` header + short as-is note (ontology exists; no runtime read) |
| R1 Plantilla fields land | Mention under knowledge pointer; still no runtime |
| Docs crosswalk FS↔ontology | [`ONTOLOGY_CROSSWALKS.md`](ONTOLOGY_CROSSWALKS.md) · pointer in ARCHITECTURE knowledge § + native README |
| R2/R3/R4 ★ ACCEPT | Move **implemented** seams into `ARCHITECTURE.md` + `system_map` (not before) |

---

## 10) Non-goals

- Conversation Engine / Decision Engine rebirth  
- Ontology as second catalog  
- Merging vault into `knowledge/` package  
- Claiming the vault is solid end-to-end today
