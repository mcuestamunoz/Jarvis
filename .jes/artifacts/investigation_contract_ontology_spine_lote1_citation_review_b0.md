# Investigation Contract — Ontology spine lote-1 citation review (`B0-ontology-spine-lote1-citation-review`)

**Project:** Jarvis  
**Date:** 2026-09-27  
**Author:** JES / Cursor (Engineer Interface) — **investigation / review only**  
**Investigator:** **Claude Code** — ★ AUTHORIZED: **review now**  
**Reviewer:** Cursor against this contract · Engineer decides any content remediations  

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-27) — citation audit complete; remediations R1/R2 landed by Cursor  
**Parents:**
- Epoch **`0.6.x`** knowledge vision: [`docs/JARVIS_KNOWLEDGE_VISION.md`](../../docs/JARVIS_KNOWLEDGE_VISION.md)  
- Spine lote-1 **landed `solid`** (Engineer-corrected + GPT cite pass → Cursor land):
  - [`ontology/01_Matematicas/Álgebra lineal/Vectores/Vectores.md`](../../ontology/01_Matematicas/Álgebra%20lineal/Vectores/Vectores.md)
  - [`ontology/02_Fisica/Mecánica/Dinámica/Dinámica.md`](../../ontology/02_Fisica/Mecánica/Dinámica/Dinámica.md)
  - [`ontology/03_Ingenieria/Control/Control%20clásico/Control%20clásico.md`](../../ontology/03_Ingenieria/Control/Control%20clásico/Control%20clásico.md)
- Tip remains **`v0.5.44`** until a separate 0.6 tag decision  
- Plantilla: [`ontology/00_Mapa/Plantilla.md`](../../ontology/00_Mapa/Plantilla.md)

**Type:** **Investigation / citation-audit Contract** — verify that every cited claim in lote-1 is supported by the listed references, that URLs resolve to the named works, and that the notes do **not** invent physical facts, catalog numbers, or FS gains.  
**Package:** **do not bump** `pyproject.toml`. No git tag.  
**Not** an Implementation Contract · not rewriting lote-2 · not RAG · not `src/` edits · not marking notes `solid`/`draft` yourself unless the report recommends a downgrade and Engineer ★ applies it via Cursor.

**Outputs (required):**
1. `.jes/artifacts/investigation_report_ontology_spine_lote1_citation_review_b0.md`
2. Per-note audit table (Vectores / Dinámica / Control clásico)
3. Per-reference reachability + fidelity check
4. Invention / overclaim / SoT-bleed findings (if any)
5. Verdict per note: **PASS** · **PASS WITH NOTES** · **FAIL** (with required remediations)
6. Explicit non-edits: what Claude did **not** change in `ontology/`

**Checkpoint:** tip stays **`v0.5.44`** · zero product code · lote-1 files read-only for Claude unless Engineer later asks Cursor to apply remediations

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B0-ontology-spine-lote1-citation-review`** — audit cites + truthfulness of lote-1 solids |
| 2 | Parallel work | Cursor + Engineer continue **lote-2** drafts while this runs — do not block on lote-2; do not audit lote-2 in this Buy |
| 3 | Scope files | **Only** the three lote-1 paths listed above (+ their `[REFERENCIAS]` URLs) |
| 4 | No silent rewrites | Claude **must not** edit `ontology/` in this Buy. Report proposed patches as markdown diffs / bullet remediations for Cursor to land after Engineer ★ |
| 5 | Standard of “true” | A claim is OK if the cited source **supports** it (same meaning). Minor phrasing differences OK. Contradictions, fabricated §§, dead URLs, or invented numbers = FINDING |
| 6 | SoT bleed | Flag any prose that could be read as authorizing catalog SKU values, Continuity decisions, or FS gains as physical truth |
| 7 | Forbidden claims in the report | “Vault is production RAG-ready” · “Claude solidifies notes” · “Replace library with OpenStax” |

**Product sentence:**

```text
Verificar que las tres notas solid del spine lote-1 citan de verdad
lo que afirman — sin invención ni sangrado a catálogo/FS — y
reportar PASS/FAIL por nota.
```

---

## 1. Why this exists

Workflow locked by Engineer:

```text
Cursor draft → Engineer + GPT cite pass → Cursor land solid
→ Claude independent citation audit (this Buy)
→ remediations via Cursor if FAIL / NOTES
```

Lote-1 claims OpenStax, NASA NTRS/TM, MIT notes, UMich CTMS, Control Guru. Before the spine grows, we need an independent check that those cites are real and that the note bodies do not overclaim.

---

## 2. Locked stances

1. **Cite or do not claim.** Formulas and strong factual statements need a listed reference that actually contains them (or an explicitly weaker “standard definition” backed by the same sources).  
2. **`never_invents` must hold.** No `mass_g` / `power_w` / `thrust_gf` / `autonomy_min` values; no SKU rows; no “use these Kp/Kd on the craft”.  
3. **Jarvis APLICACIONES may name C7/C8/C36… as *explain map*** — that is OK. Claiming those Buys *validate* physics from the note = FAIL.  
4. **Dead or mismatched URL** = FINDING (severity by whether an alternate stable URL exists).  
5. **Do not expand scope** to lote-2, Plantilla-only, or the whole vault.  
6. **Math delimiters:** notes use Obsidian-native `$...$` / `$$...$$`. That is intentional. Do **not** FAIL a note for not using LaTeX `\(...\)` / `\[...\]`.

---

## 3. Audit procedure (required)

### 3.1 Per note

For each of the three files:

| Check | How |
|---|---|
| Frontmatter | `estado: solid`, `formula_citation` present, `never_invents` present, `jarvis_relevance` sensible |
| Body vs REFERENCIAS | Every strong formula / named theorem / quantitative relation in FUNDAMENTO/DEFINICION is covered by at least one entry in `[REFERENCIAS]` (or explicitly marked as definitional restatement of those sources) |
| Overclaim | No universal guarantees that the sources do not make (e.g. “PID always stable”, “integral always kills steady-state error”) |
| SoT bleed | APLICACIONES/ERRORES/NOTAS respect catalog/FS/Safety fences |
| Internal consistency | DEFINICION ↔ FUNDAMENTO ↔ ERRORES do not contradict |

### 3.2 Per reference URL

For **every** URL in each note’s `[REFERENCIAS]`:

1. Fetch or otherwise verify the URL is reachable (HTTP 200 or equivalent stable redirect to the named work).  
2. Confirm the title / § / TM number in the bullet matches the landed page.  
3. Spot-check that the **key claims** attributed to that source appear there (quote or paraphrase with section pointer in the report).  
4. If a PDF (NASA/MIT): check title page / abstract / relevant section headers — not every page.

### 3.3 Invention scan (explicit)

Search each note body for:

- Numeric physical parameters presented as facts without cite (masses, watts, thrusts, Kp/Ki/Kd numeric values for a vehicle)  
- Assertions that contradict OpenStax/CTMS standard statements  
- Fake section numbers (e.g. § that does not exist in the named OpenStax page)

---

## 4. Report format (mandatory sections)

```text
0. Honesty summary
1. Scope + files hashed/paths
2. Vectores — audit table + verdict
3. Dinámica — audit table + verdict
4. Control clásico — audit table + verdict
5. Cross-cutting findings (SoT bleed, template drift)
6. URL matrix (note × URL × reach × match × claim-support)
7. Recommended remediations (ordered; Cursor-applicable patches only)
8. Overall verdict + whether lote-1 may stay solid
9. Non-goals / what was not audited (lote-2, RAG, …)
```

Each note verdict:

| Verdict | Meaning |
|---|---|
| **PASS** | Cites OK; no invention; SoT clean — keep `solid` |
| **PASS WITH NOTES** | Keep `solid` but Cursor should apply small wording/URL fixes |
| **FAIL** | Material invention, dead critical cite, or SoT bleed — recommend downgrade to `draft` until fixed |

---

## 5. Acceptance criteria (investigation)

- [ ] Report path written  
- [ ] All three notes audited  
- [ ] All REFERENCIAS URLs checked  
- [ ] Invention scan documented (even if empty)  
- [ ] Per-note verdict present  
- [ ] Remediations list actionable for Cursor (or “none”)  
- [ ] `git status` shows **no** Claude edits under `ontology/` or `src/` (report-only)  
- [ ] Tip still **`v0.5.44`** · no package bump  

---

## 6. Stop conditions

- Do **not** start auditing lote-2 in this Buy.  
- Do **not** “improve” prose for style — only truth/cite/SoT issues.  
- Do **not** claim ACCEPT of the investigation — that is Cursor review + Engineer.  
- If network cannot reach a URL, mark **UNVERIFIED (network)** and say what would be needed offline — do not invent that the cite is fine.

---

## 7. Paste for Claude (short)

```text
★ AUTHORIZED investigation — B0-ontology-spine-lote1-citation-review

IC: .jes/artifacts/investigation_contract_ontology_spine_lote1_citation_review_b0.md

Audit ONLY these three solid notes (read-only — do not edit ontology/):
- ontology/01_Matematicas/Álgebra lineal/Vectores/Vectores.md
- ontology/02_Fisica/Mecánica/Dinámica/Dinámica.md
- ontology/03_Ingenieria/Control/Control clásico/Control clásico.md

Job: verify every [REFERENCIAS] URL + that body claims are supported;
scan for invention / catalog-FS SoT bleed; verdict PASS | PASS WITH NOTES | FAIL
per note. Write investigation_report_ontology_spine_lote1_citation_review_b0.md

Parallel: Cursor+Engineer do lote-2 drafts — out of your scope.
No src/, no pyproject bump, tip stays v0.5.44. No ACCEPT claim.
```
