# Investigation Contract — Ontology vault value for Jarvis (`B0-ontology-vault-value-for-jarvis`)

**Project:** Jarvis  
**Date:** 2026-09-27  
**Author:** JES / Cursor (Engineer Interface) — **investigation only**  
**Investigator:** **Claude Code** (Cursor does not implement) — ★ AUTHORIZED: **investigate now**  
**Reviewer:** Cursor against this contract · Engineer pick (seam + quality bar + next Buys)

**Status:** ★ **AUTHORIZED** (Engineer 2026-09-27 — IC passed to Claude = execute investigation)  
**Parents:**
- Tip **`v0.5.44`** — software-month C36–C43 ★ CLOSED ([C43](implementation_contract_fase_c_craft_fs_bind_b1.md))  
- Vault landed in monorepo: [`ontology/`](../../ontology/README.md) (commit that added the Obsidian graph; ≠ `src/jarvis/knowledge/`)  
- [DC-assistant-placement](design_contract_assistant_placement_b0.md) — **DISCUSS**; proposes future `intelligence/` retrieve; **no mkdir** this Buy  
- Craft SoT: Continuity / `library/` / Board — **unchanged**  
- Platform FS: `flight_software/` + `native/flight_control/` — **unchanged**  
- LLM boundary: interpret/narrate only; Continuity/cálculo = 0 LLM (`docs/system_map/10_llm/LLM_MAP.md` if present)

**Type:** **Investigation Contract** — map how a **well-planted, solid, rich** conceptual ontology (math → physics → engineering → robotics) would raise Jarvis quality, and what seams/Buys would unlock that. Use the **live folder tree and link skeleton** in `ontology/` as the **shape of intent**, not as a quality audit of incomplete note bodies.  
**Package:** **do not bump** `pyproject.toml`. No git tag.  
**Not** an Implementation Contract · not filling empty notes · not RAG shipping · not `src/jarvis/intelligence/` mkdir · not Conversation Engine · not mutating Continuity / `library/` / FS.

**Outputs (required):**
1. `.jes/artifacts/investigation_report_ontology_vault_value_for_jarvis_b0.md`  
2. Inventory of **structure only** (folders, hub map, wikilink graph shape) — cite paths under `ontology/`  
3. Value model: what a **complete** vault would give each Jarvis surface (see §3)  
4. Seam design: SoT boundaries (ontology ≠ catalog ≠ Continuity ≠ `step()`)  
5. Quality bar for “rich enough to trust” (template / required fields / cite rules) — **aspirational**, not a score of today’s stubs  
6. Ranked recommendations: park · enrich vault offline · B0/B1 retrieve under `intelligence/` · Continuity explain-links · NL→User-Guide grounding — **pick a default path** with stop conditions  
7. Explicit **non-goals** and forbidden claims

**Checkpoint:** tip stays **`v0.5.44`** · zero product code · suite untouched · report only

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B0-ontology-vault-value-for-jarvis`** — investigation of **value + seams**, not note grading |
| 2 | Incomplete notes | Engineer states many concepts are incomplete. **Do not** score completeness, fill stubs, or rewrite the vault. Treat thin notes as **placeholders for a future rich graph**. |
| 3 | What this Buy demonstrates | Un grafo conceptual bien planteado puede subir calidad de explicación, grounding y Assistant — **sin** convertirse en SoT de craft ni de firmware. **Human:** “si el vault estuviera rico, ¿qué ganaría Jarvis — y dónde se enchufa sin romper Continuity?” |
| 4 | Shape vs content | May describe the **taxonomy** (`00_Mapa`…`04_Robotica`, hubs Ingeniería/Conocimiento) as the intended ontology. Must **not** conclude “vault is weak → abandon” from empty bodies. |
| 5 | Placement | Vault stays at repo-root **`ontology/`**. Never merge into `src/jarvis/knowledge/` (catalog reader). Future retrieve belongs under **`intelligence/`** (per Assistant DC), not under `core/orchestrator` or `flight_software/`. |
| 6 | No code this Buy | No new packages · no indexer · no pytest that parses the vault as product · no Continuity edits |
| 7 | One front | Do **not** fold Assistant scaffold ★, VoiceIntentAdapter, house `world/`, silicon, CAD, HD-* lab |
| 8 | Forbidden claims | “Ontology replaces catalog” · “LLM may invent mass/W from notes” · “vault drives `step()`” · “we audited note quality and failed the Engineer” |

**Product sentence:**

```text
Investigar qué valor daría a Jarvis un ontology/ rico y bien
planteado — y cómo engancharlo — sin juzgar los stubs actuales
ni escribir código.
```

**Defaults locked by Cursor:**
- Investigation report only  
- Structure = evidence of intent; content completeness = out of scope  
- Recommend seams aligned with Assistant DC  

---

## 1. Why this exists

Shipped today (tip `v0.5.44`):

```text
ontology/          Obsidian vault — theory graph (math → robotics)
library/           Craft catalog SoT (SKUs, cited dims)
src/jarvis/knowledge/   ComponentLibrary reader of library/ ONLY
src/jarvis/core/   Continuity / Engineer craft path
src/jarvis/llm/    Narrow interpret + narrate
flight_software/ + native/   Vehicle scaffold (not ontology)
```

Wrong answers:

```text
· Grade every .md and declare the vault “not ready”
· Fill incomplete notes in this Buy
· Put ontology under src/jarvis/knowledge/
· Let LLM invent thrust/autonomy from a physics note
· Build RAG + Conversation Engine in one leap
```

Right question:

> If `ontology/` were **solid and rich** (same taxonomy, filled and cross-linked), **what concrete quality gains** would Jarvis get on craft Continuity, catalog honesty, platform FS literacy, Assistant, and LLM grounding — and what is the **smallest honest seam** to start, without violating SoT locks?

---

## 2. Locked stances

1. **Ontology explains; catalog declares; Continuity decides next craft step; FS computes vehicle.** Four roles — do not collapse.  
2. **Incomplete ≠ worthless skeleton.** Report value of the *target* graph.  
3. **Cite or do not claim physical numbers.** Theory notes never override `library/` or HD-* walls.  
4. **No Conversation Engine.** Retrieve/cite ≠ new orchestrator.  
5. **Assistant DC still DISCUSS.** This B0 may recommend a later IC for retrieve; it does **not** ★ `intelligence/` mkdir.  
6. **Fail closed on mutation:** any recommended path that writes craft workspace or `library/` from ontology = reject.

---

## 3. Value surfaces the report must cover

For each surface, answer: **gain if vault were rich** · **mechanism** · **risk if miswired** · **minimum Buy grain**.

| Surface | Prompt |
|---|---|
| A · Craft Continuity / User Guide | Explain *why* a step exists (e.g. declare mass, C-rate honesty) with links to concepts — without inventing values |
| B · Catalog / bind honesty | Ground “cited vs estimated”, motor OP ≠ intrinsic thrust, RF mW ≠ DC W — concept citations |
| C · Geometry / Board | Envelope ≠ CAD; AABB ≠ fit — conceptual literacy for Engineer + docs |
| D · Platform FS (C36–C43 ladder) | Human-readable map: PID / attitude / SPI / WHO_AM_I ↔ ontology nodes — **docs/teach**, not code merge |
| E · LLM | NL → Continuity cheatsheet grounding; refuse inventing physics numbers; optional cite-back to notes |
| F · Future Assistant (`intelligence/`) | Retrieve/cite layer; tasks that *ask* ontology; never PWM/mixer |
| G · HD-* / lab walls | Ontology states *what measurement would unlock* — does not fake the curve |

---

## 4. Structure evidence (allowed)

Report **must** inventory (paths + counts OK):

- Top-level bands: `00_Mapa` … `04_Robotica` (+ `05_Problemas` if relevant)  
- Hub map note(s) under `00_Mapa/`  
- Wikilink style (e.g. `[[Control]]`) as graph edges — qualitative density, not a quality score of prose  
- Explicit split from `src/jarvis/knowledge/` and `library/`

Report **must not**:

- Rank notes as “empty / bad / incomplete” as a pass/fail of the Engineer  
- Propose rewriting hundreds of stubs in this Buy  
- Claim the current vault is already “production RAG ready”

---

## 5. Quality bar for a *future* rich vault (aspirational)

Define a **target note contract** (example fields — investigator may refine):

```text
concept_id / title
definition (short)
relations (wikilinks up/down/lateral)
jarvis_relevance (craft | catalog | FS | assistant | none)
never_invents (list: mass_g, power_w, autonomy_min, …)
citation / textbook section when claiming formulas
status: stub | draft | solid
```

State what “rich enough for retrieve” means (e.g. solid on path Matemáticas→Control→Control robótico for craft energy/control explanations) — **as a target**, not a grade of today.

---

## 6. Recommendations the report must pick among

At least evaluate and **rank**:

| Option | Grain |
|---|---|
| R0 | Park ontology integration; Engineer enriches vault offline only |
| R1 | Vault hygiene IC later (templates/frontmatter) — still no product code |
| R2 | Tiny retrieve stub under future `intelligence/` (read-only search/cite) after Assistant placement ★ |
| R3 | Continuity “explain” links (optional citations in status text) — careful, no mutation |
| R4 | LLM grounding: adapter may attach ontology cites to NL→User-Guide proposals; ActionPolicy still hard-gates |

**Default recommendation required:** one primary path + stop conditions (“do not start R4 before R1”, etc.).

---

## 7. Acceptance (investigation)

**PASS when:** report covers §3 surfaces · structure inventory · SoT seams · aspirational quality bar · ranked R0–R4 with a default · forbidden claims absent · no product code.  
**FAIL if:** grades incomplete notes as the verdict · proposes merging into `src/jarvis/knowledge/` · proposes LLM invent numbers from notes · implements retrieve/code in this Buy.

---

## 8. Handoff

```text
Engineer → ★ AUTHORIZED (this B0 — Claude investigates now)
Claude   → investigation_report_ontology_vault_value_for_jarvis_b0.md
Cursor   → independent review of report
Engineer → ACCEPT investigation · pick next Buy (or park)
```

---

## 9. Engineer ★ checklist

- [x] ★ this investigation IC — 2026-09-27 (passed to Claude = execute)  
- [ ] After report: Cursor review · Engineer ACCEPT · choose R*  
- [ ] No `intelligence/` mkdir until a separate IC is ★  
