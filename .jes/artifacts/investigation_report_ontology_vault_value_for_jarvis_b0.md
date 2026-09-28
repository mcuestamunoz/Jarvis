# Investigation Report — Ontology vault value for Jarvis (`B0-ontology-vault-value-for-jarvis`)

**IC:** [`investigation_contract_ontology_vault_value_for_jarvis_b0.md`](investigation_contract_ontology_vault_value_for_jarvis_b0.md)
**Investigator:** Claude Code
**Date:** 2026-09-27
**Status:** Investigation only. **Tip stays `v0.5.44`.** Zero product code, zero `pyproject.toml` bump, no tag. Not claiming ACCEPT — that is Engineer's call after Cursor review.

---

## 0. Read this first — honesty summary

```text
ontology explains != catalog declares != Continuity decides != FS computes
structure inventory != quality grade of today's stubs
target note contract != today's note contract
recommending a seam != building it
```

This report inventories **shape** (folders, hub map, wikilink graph density) in `ontology/` as evidence of an intended taxonomy, not a verdict on today's note bodies. It models what a **complete** version of that same taxonomy would give six Jarvis surfaces, proposes SoT-respecting seams for each, defines an aspirational note-quality bar (built on a template the Engineer already planted, not invented from scratch), and ranks R0–R4 with one default path. **No file under `ontology/` was edited. No file under `src/` was created or edited. No package was created.**

---

## 1. Structure inventory (evidence only, not a grade)

### 1.1 Top-level bands

```text
ontology/
├── 00_Mapa/          3 notes  — hub map, template, roadmap sketch, concept registry
├── 01_Matematicas/   30 notes — Álgebra, Funciones, Trigonometría, Cálculo, Álgebra lineal, Ecuaciones diferenciales
├── 02_Fisica/        16 notes — Mecánica, Termodinámica, Mecánica de fluidos, Electromagnetismo
├── 03_Ingenieria/    20 notes — Aerodinámica, Control, Electrónica, Mecánica estructural, Sistemas
├── 04_Robotica/      19 notes — Sensores, Actuadores, Cinemática y dinámica, Control robótico, Percepción, Navegación y planificación
└── 05_Problemas/      0 notes — reserved band, empty directory (no files at all)
```

90 `.md` files total, verified via `find ontology -name "*.md"`. Every band folder itself follows a **folder-note pattern**: a topic directory (e.g. `01_Matematicas/Cálculo/`) holds a same-named hub note (`Cálculo.md`) plus subdirectories for each narrower concept (`Derivadas/`, `Integrales/`, …), each again holding its own same-named hub note and, where present, sibling leaf notes (e.g. `Cálculo/Derivadas/Derivada concepto.md` beside `Cálculo/Derivadas/Derivadas.md`). This nesting goes 2–3 levels deep consistently across all four content bands (`01`–`04`), matching the taxonomy `00_Mapa/Roadmap.md` itself lays out.

`05_Problemas` exists as a directory with zero files — read as a **reserved band** for future applied/worked-problem notes (the natural place a craft-facing worked example, e.g. "why C-rate honesty matters for this pack," would eventually live), not a defect.

### 1.2 Hub map

`00_Mapa/Ingenieria.md` is a single flat index linking the top concept of each of the four content bands under four headers (`## Matemáticas`, `## Física`, `## Ingeniería aplicada`, `## Robótica`), e.g.:

```markdown
## Robótica
- [[Sensores]]
- [[Actuadores]]
- [[Cinemática y dinámica]]
- [[Control robótico]]
- [[Percepción]]
- [[Navegación y planificación]]
```

`00_Mapa/Roadmap.md` is a plain-text outline (no wikilinks) of the intended full tree — every subtopic name in every band, several levels deep — evidently written **before** the folders/notes existed, since it still names a few subtopics with slightly different labels than the eventual folder names (e.g. Roadmap's "EDO primer orden" vs the actual folder `EDO de primer orden`). This is the clearest single artifact of **intent preceding content**.

`00_Mapa/conceptos.json` is a flat JSON array of 94 `{concepto, area, subarea}` records — a concept registry at a **finer grain** than the 90 materialized notes (e.g. `Número natural`/`Número entero`/`Número racional` are three distinct registry entries that would fold into fewer, richer notes, or split further — investigator does not resolve which). Read as a seed list for future note creation, not a duplicate SoT.

`00_Mapa/Plantilla.md` is an existing note **template** (not a note itself) — see §4, this is directly reusable evidence for the "quality bar" output the IC asks for, rather than something this report needs to invent from nothing.

### 1.3 Wikilink graph shape (density, not prose quality)

Measured directly (script run against the checked-in files, not against note content quality):

```text
Total notes:                90
Total [[wikilink]] occurrences:   363
Unique wikilink targets:          352
Targets that resolve to an existing note: 82
Targets with no note yet ("dangling"):    270  (~77% of unique targets)
```

Sample of dangling targets (concepts referenced by existing notes but with no note of their own yet): `Acelerómetro`, `Actuador`, `Campo eléctrico`, `Capacitor`, `Cinemática directa`, `Cinemática inversa`, `Coeficiente de arrastre`, `IMU`, `Giroscopio`, `Motor DC`, `Encoder`.

Read this as the **shape of intent** the IC names explicitly: the graph's edges already reach ~4x further than its materialized nodes. A rich vault is not "write 90 better notes" — it is "resolve ~270 more nodes the graph already expects to exist." Two concrete examples directly adjacent to this session's own C36–C42 work: `[[IMU]]` and `[[Giroscopio]]` are both linked from `04_Robotica/Sensores/Sensores de movimiento/Sensores de movimiento.md` (alongside `[[Acelerómetro]]`, `[[Encoder]]`, `[[Velocidad angular]]`) but neither has a note yet — exactly the concept pair `sim_altitude_hal.py`/`icm42688p.hpp` sit next to on the platform side.

### 1.4 Explicit split from `src/jarvis/knowledge/` and `library/`

Already stated, correctly, in `ontology/README.md` (not written by this investigation — quoted verbatim):

> **What this is not:** Not the craft catalog (`library/` + `src/jarvis/knowledge/` / `ComponentLibrary`) · Not Continuity project state · Not flight-software truth (`step()`, Safety, WHO_AM_I, …) · Not permission for the LLM to invent masses, watts, or autonomy.

Verified independently, not just quoted: `grep -rl "ontology" src/jarvis/` returns nothing — no file under `src/` imports, reads, or references `ontology/` today. `src/jarvis/knowledge/library.py` (`ComponentLibrary`) reads exclusively from `library/*/​_datos.json` (frame/motor/battery/etc. catalog rows with `source_url`/`identity_status` citation fields) — a structurally different content shape (numeric, cited, SKU-keyed) from `ontology/`'s prose-and-wikilink concept notes. The two trees do not currently touch, and this report does not recommend merging them (IC §0 decision 5, Locked stance 1).

---

## 2. Value model — what a *complete* vault gives each surface

For each surface: **gain if rich** → **mechanism** → **risk if miswired** → **minimum Buy grain**.

### A · Craft Continuity / User Guide

- **Gain:** when Continuity's own status text says "declare `battery_capacity_wh` honestly" or explains why C-rate matters, it can point at a *why*, not just a *what* — a concept explanation the Engineer (or a future user) can actually read, instead of a one-line status string repeated project after project.
- **Mechanism:** an **optional, read-only citation** attached to existing Continuity status/explain text — e.g. a status string gains a trailing `(ver: [[Corriente y circuitos]])`-shaped pointer, resolved and rendered by whatever surface displays that text (CLI/MCP), never computed from or altered by the ontology note's content.
- **Risk if miswired:** if a Continuity decision (which field is required next, what C-rate is "honest") ever became *conditional* on ontology note content, Continuity would silently gain a second, unreviewed source of truth for decisions that must stay in `core/`'s own deterministic logic. This is the single highest-risk seam in this list because Continuity is the most decision-heavy surface — mitigated only by keeping the link one-way and cosmetic.
- **Minimum Buy grain:** a docs-only pass (no `src/` change) adding a handful of citation pointers into existing `docs/USER_GUIDE_CRAFT_MONTAGE.md`-style prose, proving the pattern reads well, before any code touches it.

### B · Catalog / bind honesty

- **Gain:** "cited vs estimated," "motor OP ≠ intrinsic thrust," "RF mW ≠ DC W" are exactly the kind of standing confusions this session's own catalog work (HD-005, the XING-E motor OP debate) keeps re-explaining from scratch in report prose. A rich `03_Ingenieria/Electrónica`/`02_Fisica/Electromagnetismo` subtree could hold the canonical explanation once.
- **Mechanism:** a docs crosswalk (Markdown table, not code) mapping catalog honesty terms (`identity_status`, `source_url`, "OP vs intrinsic") to ontology concept nodes — read by a human (Engineer, future contributor), not by `ComponentLibrary` at runtime. `ComponentLibrary` itself never reads `ontology/`.
- **Risk if miswired:** a note claiming a *specific number* ("this motor's Kv is...") would collide with `library/`'s own `source_url`-cited row for the same fact, creating exactly the two-SoT problem `library/`'s own docs already guard against. Ontology notes must stay at the *concept* level (what is a C-rate, what does "OP" mean) and never restate a catalog row's own cited numeric value.
- **Minimum Buy grain:** one glossary-shaped doc (or a `03_Ingenieria`/`02_Fisica` note pair) explaining "operating point vs intrinsic capability" in general engineering terms, cross-linked from — never embedded into — the existing HD-005/XING-E report prose.

### C · Geometry / Board

- **Gain:** "envelope ≠ CAD," "AABB ≠ fit" are concepts this session's own Taller CSS work (cuboid/cylinder face centering) already had to explain by hand in every implementation report. A `03_Ingenieria/Mecánica estructural` or a new geometry-adjacent note could hold that once, for onboarding/docs, not for the geometry code itself.
- **Mechanism:** doc-only cross-reference from `docs/ARCHITECTURE.md`'s own Board/Taller sections to an ontology concept — literacy for the Engineer and future contributors reading docs, never a runtime dependency of `Solid3D.tsx`/`spatial_board.py`.
- **Risk if miswired:** near-zero for this surface specifically, *provided* the link stays doc-to-doc. The only failure mode would be treating an ontology note as an authority on an actual geometric tolerance/fit number, which nothing in this repo's geometry pipeline currently reads from anywhere but `library/` fixture data.
- **Minimum Buy grain:** a single new cross-reference line in `docs/ARCHITECTURE.md`'s existing Taller/Board section pointing at the relevant (even if currently thin) ontology concept — no code.

### D · Platform FS (C36–C43 ladder) — human-readable map

- **Gain:** this session's own flight-software ladder (filter → estimator → PD controller → mixer → SPI → WHO_AM_I) is dense, cumulative, and currently explained only in scattered `implementation_report_*.md`/`native/flight_control/README.md` prose. A stable ontology cross-reference would let a newcomer (or the Engineer six months from now) go "attitude estimator" → `[[Cinemática robótica]]`/`[[Control robótico]]` → the textbook concept, instead of re-deriving it from a Buy report.
- **Mechanism:** a **docs-only crosswalk table** (illustrative, not built this Buy):

  | FS module | Ontology node (existing or dangling) |
  |---|---|
  | `filter.py` (C6, IMU low-pass) | `04_Robotica/Sensores/Sensores de movimiento` → `[[IMU]]` (dangling) |
  | `attitude.py` (C7, complementary filter) | `[[Cinemática robótica]]` (dangling), `01_Matematicas` trig/vector notes (exist) |
  | `controller.py` (C8, PD law) | `03_Ingenieria/Control/Control clásico` (exists) |
  | `mixer.py`/`esc.py` (C9/C10) | `04_Robotica/Actuadores/Motores` (exists as hub, links `[[Motor DC]]` dangling) |
  | `plant.py` (C36, 6-DoF) | `02_Fisica/Mecánica/Dinámica`, `Momento y rotación` (exist) |
  | `mag.py`/`altitude_controller.py` (C37/C38) | `02_Fisica/Electromagnetismo/Magnetismo` (exists), `Control clásico` |
  | `sim_position_hal.py`/`position_controller.py` (C39) | `04_Robotica/Navegación y planificación` (exists) |
  | `icm42688p.hpp` (C42, WHO_AM_I) | `04_Robotica/Sensores` → `[[IMU]]` (dangling) |

  This table itself is the kind of artifact a future Buy would produce — **docs/teach, never a code merge** (IC §3.D's own phrasing), living in `docs/` or `native/flight_control/README.md`, not imported by any module.
- **Risk if miswired:** if any FS module ever imported `ontology/` to decide behavior (e.g. reading a "typical Kp value" from a control-theory note instead of the module's own documented, tested default), that would directly violate this session's own established discipline (every gain/constant in `flight_control/` is a disclosed, tested, toy default — never sourced from a prose note). Locked stance 3 ("cite or do not claim physical numbers") applies with full force here.
- **Minimum Buy grain:** the crosswalk table above, added to an existing doc, zero new files, zero code.

### E · LLM (NL → Continuity grounding)

- **Gain:** `src/jarvis/llm/llm_client.py`'s own `analyze(...)` already accepts `goal_context` as **read-only reference material the LLM may quote from, never as something it decides** (verified — `docs/system_map/10_llm/LLM_MAP.md`'s own wording). A rich ontology gives that same narrator a second, richer body of quotable reference material for narration/explanation turns — never for the 4-verb `ActionPolicy`-gated decision path (`CREATE_PROJECT`/`ITERATE`/`CALCULATE`/`SIMULATE`).
- **Mechanism:** an optional citation attached to an `analyze(...)` response (e.g. "see `[[Control clásico]]` for why this gain matters") — additive text, never a new field `ActionPolicy.validate` inspects or gates on. `ActionPolicy.ALLOWED_ACTIONS` (the closed 4-member set) is structurally unaffected by anything this surface could add.
- **Risk if miswired:** the IC's own explicit forbidden claim — "LLM may invent mass/W from notes" — is the exact failure mode to guard against. An ontology note is prose; if a narrator ever paraphrased a note's example number as if it were a catalog fact, that is indistinguishable from hallucination dressed as citation. Any grounding surface must **quote/link**, never **compute from**, an ontology note.
- **Minimum Buy grain**: none yet — this is the surface most worth a small B1 investigation of its own (see R4) rather than a docs-only pass, since it touches live code (`llm_client.py`), even if additively.

### F · Future Assistant (`intelligence/`)

- **Gain:** the Assistant DC (`design_contract_assistant_placement_b0.md`, still **DISCUSS**) already names `intelligence/` as the future home for a retrieve/cite layer sitting *above* Intent, never inside `flight_control`. A rich ontology is exactly the corpus that layer would retrieve against — concept explanations an Assistant could answer "what is a C-rate" from, distinct from "what is *this* battery's C-rate" (still `library/`'s own job).
- **Mechanism:** (future, gated) a read-only retrieve/search+cite function under `intelligence/`, called by an Assistant task, returning note excerpts + wikilink paths — never a write path, never a decision path, never a PWM/mixer reference (IC §3.F's own explicit "never PWM/mixer").
- **Risk if miswired:** building this before the Assistant DC itself is ★ would create exactly the kind of premature-placement problem the DC's own §5 warns about — "zero directories" until a dedicated IC exists. This report does **not** recommend starting this now (see §6, R2's own stop condition).
- **Minimum Buy grain:** none this Buy. A future, separate IC, explicitly gated behind the Assistant DC's own ★.

### G · HD-* / lab walls

- **Gain:** HD-005 (the XING-E + Hurricane MCK 51466-3 + 4S thrust-stand gap) is a live example of exactly what this surface asks for — an ontology note on `03_Ingenieria/Aerodinámica`/propeller pitch/thrust concepts could state *what a thrust-stand measurement would need to show* (pitch, RPM, current, voltage — the concepts, not invented numbers) to close that debt, without ever fabricating the missing curve itself.
- **Mechanism:** a doc cross-reference from the HD-005 entry in `docs/HARDWARE_DEBT.md` to the relevant aerodynamics concept note — explaining the *shape* of the needed measurement, read by whoever picks up the bag/bench task.
- **Risk if miswired:** the obvious failure is a note that estimates or implies a specific thrust/RPM/efficiency number for the real combo — that is precisely "faking the curve," forbidden by both this IC and HD-005's own existing lock ("Nunca... fingir match").
- **Minimum Buy grain:** one cross-reference line in `docs/HARDWARE_DEBT.md`'s existing HD-005 entry — no code, no invented numbers.

---

## 3. Seam design — SoT boundaries

Four roles, never collapsed (Locked stance 1, restated with the actual module names this repo already has):

```text
ontology/                         EXPLAINS (concepts, prose, wikilinks)
   |  read-only, doc-to-doc or cite-only
   v
docs/ (Continuity prose, reports, READMEs)     — surfaces A, C, D, G (this Buy's own minimum grains)
   |
   |  (future, gated behind a separate ★ IC)
   v
intelligence/  [NOT ON DISK]        RETRIEVES/CITES  — surface F
   |  attaches citations only, never decides
   v
src/jarvis/llm/ (interpret/analyze)          — surface E
   |
   X  ActionPolicy's closed 4-verb set is UNCHANGED by anything on this diagram
   v
src/jarvis/core/ (Continuity)                DECIDES next craft step
   |
   X  never reads ontology/ to decide; never writes ontology/
   v
library/ + src/jarvis/knowledge/ (ComponentLibrary)   DECLARES catalog facts (cited)
   |
   X  never reads ontology/; ontology/ never restates a cited numeric row
   v
flight_software/ + native/flight_control/    COMPUTES vehicle behavior (sim)
   |
   X  never reads ontology/; every gain/constant stays a disclosed, tested default
```

**Explicit boundary statements** (each independently checkable, none require new tooling to verify — the same `grep`/`git diff --stat` style this session already uses for every C-Buy's own freeze checks):

1. `grep -rl "ontology" src/jarvis/` → today, empty. Any future Buy touching surfaces A/C/D/G should keep this empty for `core/`, `knowledge/`, `flight_software/`, and `native/` — only a future, explicitly-scoped `intelligence/` (surface F, not this Buy) or `llm/` (surface E, its own future Buy) would legitimately add a reference, and even then read-only.
2. `library/*/_datos.json` rows keep their own `source_url`/`identity_status` citation fields — ontology notes never substitute for or override those; a note may *explain* what "identity_status: verified" means, never assert a value for a specific SKU.
3. `ActionPolicy.ALLOWED_ACTIONS` (the closed 4-verb set) is not touched by any surface in this report — grounding/citation is additive text on top of an already-validated action, never a new action, never a new field the policy gates on.
4. No file under `ontology/` gains a write-back path from any other tree — the seam is FS/docs/LLM **reading** ontology, never the reverse, and never ontology being written by product code (only the Engineer's own Obsidian editing).

---

## 4. Quality bar for a *future* rich vault (aspirational — target, not a grade of today)

The Engineer has already planted a template — `00_Mapa/Plantilla.md` — rather than this investigation inventing one from nothing. Quoted (trimmed) for reference:

```yaml
---
id: {{concepto_slug}}
nombre: {{concepto}}
area: {{area}}
subarea: {{subarea}}
nivel: {{nivel}}
estado: draft
tags: []
---
```
followed by body sections `[DEFINICION]` `[INTUICION]` `[FUNDAMENTO]` `[EJEMPLO]` `[PROCEDIMIENTO]` `[USO_PROBLEMAS]` `[APLICACIONES]` `[CONEXIONES]` `[ERRORES]` `[NOTAS]` `[ESTADO]` (with `comprensión`/`revisión` sub-fields).

This is a strong starting shape — richer, in fact, than the IC §5 example. Two structural gaps, relative to what surfaces B/D/E/G above actually need, are worth naming as a **target refinement**, not a rewrite of the existing template:

- **No `jarvis_relevance` field.** The existing frontmatter has no way to say "this concept feeds craft/catalog/FS/assistant explanations" vs "pure math with no Jarvis-facing use yet." Without it, a future retrieve layer (surface F) has no cheap way to prioritize which of ~350 eventual nodes are worth indexing first.
- **No `citation`/`never_invents` field for formula-bearing notes.** `Derivada concepto.md`'s own `## Fórmulas` section (currently empty) is exactly where Locked stance 3 ("cite or do not claim physical numbers") needs an explicit anchor — a physics/engineering note stating a formula should say where it comes from (textbook/section) the same way `library/` rows carry `source_url`, and should be able to declare a `never_invents: [thrust_n, mass_g, ...]` list the same shape this session's own `flight_software/` docstrings already use in prose ("toy tuning constant, never sourced from real hardware").
- **`estado: draft` (frontmatter) vs `[ESTADO]` (body section, `comprensión`/`revisión`) look like two overlapping status concepts.** A target contract should either fold these into one status axis (e.g. `status: stub | draft | solid` at the frontmatter level, matching the IC's own §5 suggestion) or explicitly document why both exist — this is a shape observation for whoever owns the vault template next, not a defect grade of any individual note.

**Target definition of "rich enough to trust" (aspirational, per IC §5):** a path is retrieve-ready when every node on it (a) resolves to an actual note (not dangling), (b) carries `jarvis_relevance` naming which surface(s) above would use it, (c) any formula/number in it carries a citation or is explicitly marked a toy/example, and (d) `estado`/`status` is `solid`, not `stub`/`draft`. Example target path this report calls out as directly relevant to surface D: `Matemáticas → Álgebra lineal → Vectores` → `Física → Mecánica → Dinámica` → `Ingeniería → Control → Control clásico` → `Robótica → Control robótico → Control de movimiento` — the exact chain this session's own C7/C8/C36 attitude+PD-controller work already narrates by hand in every report. This is a **target**, not a claim that this path is solid today (it is not — most of its nodes are hub notes with only child wikilinks, no filled body).

---

## 5. Ranked recommendations (R0–R4)

| Rank | Option | Grain | Why this rank |
|---|---|---|---|
| **R0** | Park ontology integration; Engineer enriches vault offline only | Zero Buys | Always available, zero risk, but leaves all six surfaces' gains unrealized. Correct **fallback**, not a plan. |
| **R1** | Vault hygiene IC later (templates/frontmatter refinement per §4) — still no product code | One small IC, `ontology/` only | Cheapest way to close the two template gaps in §4 (`jarvis_relevance`, `citation`/`never_invents`) before anything reads the vault programmatically. Entirely reversible, zero product-code risk. |
| **R2** | Tiny retrieve stub under future `intelligence/` (read-only search/cite) after Assistant placement ★ | One Buy, gated | Real value (surface F) but explicitly blocked on a DC that is still DISCUSS — building this now would repeat the exact premature-placement mistake the Assistant DC's own §5 already names and forbids. |
| **R3** | Continuity "explain" links (optional citations in status text) — no mutation | One small IC, `core/` prose only | Real, visible value (surface A) but touches the single highest-decision-density surface in the whole system; needs its own careful IC even though the change itself is small (append-only text). |
| **R4** | LLM grounding: adapter may attach ontology cites to NL→User-Guide proposals; `ActionPolicy` still hard-gates | One small IC, `llm/` additive only | Real value (surface E), and the seam is unusually clean because `goal_context`'s own existing "quote, never decide" pattern is a precedent already proven safe in this exact module — but it is still a change to live, tested code (`llm_client.py`/`analyze`), so it should not be first. |

**Default recommendation: R1 first, docs-only crosswalks second, then reassess.**

Concretely, in order:

1. **R1** (vault hygiene IC) — closes the §4 template gaps. Small, reversible, zero product-code risk, and it is the prerequisite every other option benefits from (a `jarvis_relevance`-tagged, citation-anchored vault is what makes R2/R3/R4 safe to build against later).
2. In parallel with or right after R1, the **docs-only crosswalk grains** named in §2 (surfaces A/C/D/G's own "minimum Buy grain" rows) — these are not even full ICs, just doc edits, and they are the cheapest possible proof that the seam reads well before any code touches it.
3. Only after R1 has landed and at least one docs crosswalk has been used in practice: pick between **R3** (Continuity explain-links) and **R4** (LLM grounding) based on which surface the Engineer actually wants next — both are small, single-purpose ICs, neither depends on the other.
4. **R2** stays explicitly blocked until the Assistant placement DC itself is ★ — do not start it before that, regardless of how R1/R3/R4 go.

**Stop conditions (explicit):**

- Do **not** start R2 before the Assistant DC (`design_contract_assistant_placement_b0.md`) is ★ — its own §5 already locks "zero directories" until a dedicated IC exists.
- Do **not** start R3 or R4 before R1's template gaps (`jarvis_relevance`, `citation`) are closed — grounding against an un-tagged, uncited vault means the first real consumer has to re-derive exactly the fields R1 would have added.
- Do **not**, at any rank, let a note's formula/example number be quoted by `core/` or `llm/` as if it were a `library/`-cited fact — every citation surface (R3/R4) must render ontology content as attributed prose, never as a resolved numeric value a caller could mistake for catalog data.
- If any future IC for R2/R3/R4 proposes writing to `ontology/` from product code, or reading `ontology/` from inside `flight_software/`/`native/flight_control/`/`ComponentLibrary`, that proposal fails this report's own seam design (§3) and should be rejected at IC-draft stage, not caught in review.

---

## 6. Non-goals and forbidden claims (explicit, per IC §0.8)

This report does **not** claim, and no future Buy following its default path should claim:

- "Ontology replaces catalog" — `library/`'s own cited rows remain the only SoT for craft physical facts.
- "LLM may invent mass/W from notes" — every grounding seam in §2/§3 is quote-only, never compute-from.
- "Vault drives `step()`" — `flight_software/`/`native/flight_control/` are untouched by every recommendation in §5.
- "We audited note quality and failed the Engineer" — §1's inventory is structural (counts, paths, link density), not a pass/fail grade of any note's prose; the Engineer's own stated position ("many notes are incomplete") is treated as a known, accepted state of a graph still being planted, not a finding.
- "The vault is production RAG-ready today" — §4's quality bar is explicitly aspirational; the one worked example path named there is called out as *not* solid yet.

---

## 7. Acceptance self-check vs IC §7

- Covers §3 surfaces (A–G): ✅ §2, gain/mechanism/risk/minimum-Buy-grain for each.
- Structure inventory: ✅ §1, paths + counts + wikilink density, no content grading.
- SoT seams: ✅ §3, four-role diagram + four checkable boundary statements.
- Aspirational quality bar: ✅ §4, built on the Engineer's own existing `Plantilla.md`, two gaps named as target refinements, one target path named and explicitly disclosed as not-yet-solid.
- Ranked R0–R4 with a default: ✅ §5, default = R1 → docs crosswalks → R3/R4 → R2 last (gated).
- Forbidden claims absent: ✅ §6, explicit negative list.
- No product code: ✅ confirmed — `git status --short` (below) shows only this report and no other change.

```text
$ git status --short -- ontology/ src/ pyproject.toml
(empty)
$ git status --short -- .jes/artifacts/investigation_report_ontology_vault_value_for_jarvis_b0.md
?? .jes/artifacts/investigation_report_ontology_vault_value_for_jarvis_b0.md
```

Tip remains `v0.5.44` — no version bump, no tag, confirmed via `git tag -l | sort -V | tail -1` = `v0.5.44`.
