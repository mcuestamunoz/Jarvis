# Investigation Contract — Ontology spine lote-2 citation review (`B0-ontology-spine-lote2-citation-review`)

**Project:** Jarvis  
**Date:** 2026-09-27  
**Author:** JES / Cursor (Engineer Interface) — **investigation / review only**  
**Investigator:** **Claude Code** — ★ AUTHORIZED: **review now**  
**Reviewer:** Cursor against this contract · Engineer decides any content remediations  

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-27) — citation audit complete; remediations R1–R3 landed by Cursor  
**Parents:**
- Epoch **`0.6.x`**: [`docs/JARVIS_KNOWLEDGE_VISION.md`](../../docs/JARVIS_KNOWLEDGE_VISION.md)  
- Twin audit (lote-1): [`investigation_contract_ontology_spine_lote1_citation_review_b0.md`](investigation_contract_ontology_spine_lote1_citation_review_b0.md)  
- Spine lote-2 **landed `solid`** (Engineer + GPT cite → Cursor land):
  - [`ontology/02_Fisica/Mecánica/Momento y rotación/Momento y rotación.md`](../../ontology/02_Fisica/Mecánica/Momento%20y%20rotación/Momento%20y%20rotación.md)
  - [`ontology/04_Robotica/Control robótico/Control robótico.md`](../../ontology/04_Robotica/Control%20robótico/Control%20robótico.md)
  - [`ontology/04_Robotica/Sensores/Sensores de movimiento/Sensores de movimiento.md`](../../ontology/04_Robotica/Sensores/Sensores%20de%20movimiento/Sensores%20de%20movimiento.md)
- Tip remains **`v0.5.44`** until a separate 0.6 tag decision  
- Plantilla: [`ontology/00_Mapa/Plantilla.md`](../../ontology/00_Mapa/Plantilla.md) — Obsidian math = `$` / `$$` only

**Type:** **Investigation / citation-audit Contract** — same bar as lote-1: every cited claim supported by listed refs; URLs resolve; no invention; no catalog/FS SoT bleed.  
**Package:** **do not bump** `pyproject.toml`. No git tag.  
**Not** Implementation · not editing `ontology/` · not re-auditing lote-1 · not RAG · not `src/`.

**Outputs (required):**
1. `.jes/artifacts/investigation_report_ontology_spine_lote2_citation_review_b0.md`
2. Per-note audit (Momento y rotación / Control robótico / Sensores de movimiento)
3. URL matrix (reach + title match + claim support)
4. Invention / overclaim / SoT-bleed findings
5. Verdict per note: **PASS** · **PASS WITH NOTES** · **FAIL**
6. Remediations for Cursor (or “none”) · explicit non-edits

**Checkpoint:** tip **`v0.5.44`** · report-only · lote-2 files read-only for Claude

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B0-ontology-spine-lote2-citation-review`** |
| 2 | Scope | **Only** the three lote-2 paths above (+ their `[REFERENCIAS]`) |
| 3 | No silent rewrites | Claude does **not** edit `ontology/`; propose patches in the report |
| 4 | Standard of “true” | Source supports claim (same meaning). Fake §§, dead URLs, invented numbers = FINDING |
| 5 | SoT bleed | Flag prose that authorizes SKU values, Continuity decisions, or FS gains as physical truth |
| 6 | Datasheet claims | For ICM-42688-P / sensor specifics: claim must match TDK datasheet (or be clearly generic). Invented registers/ODR/noise = FAIL |
| 7 | Math delimiters | `$` / `$$` is correct Obsidian — do **not** FAIL for not using `\[...\]` |
| 8 | Forbidden report claims | “RAG-ready” · “Claude marks solid” · “Replace library with ETH/NASA” |

**Product sentence:**

```text
Verificar que las tres notas solid del spine lote-2 citan de verdad
lo que afirman — sin invención ni sangrado a catálogo/FS — y
reportar PASS/FAIL por nota.
```

---

## 1. Why this exists

Same workflow as lote-1:

```text
Cursor draft → Engineer + GPT cite → Cursor land solid → Claude cite-audit
```

Lote-2 mixes OpenStax/MIT mechanics, ETH quadrotor control PDFs, NASA allocation/hierarchy, Analog Devices MEMS, and TDK ICM-42688-P. Higher risk of overclaim on datasheet/SPI and of treating sim ladder (C6–C42) as hardware validation — audit must catch that.

---

## 2. Locked stances

1. **Cite or do not claim.**  
2. **`never_invents` must hold.**  
3. **Jarvis APLICACIONES may map C7/C8/C36… as explain** — OK. Claiming those Buys validate physics/hardware = FAIL.  
4. **WHO_AM_I / ScriptedSpi / sim IMU ≠ copper / ≠ calibration / ≠ flight** — notes already state this; flag if any paragraph weakens it.  
5. **Do not audit lote-1** in this Buy (separate IC/report).  
6. Network failure on a URL → **UNVERIFIED (network)** — do not invent PASS.

---

## 3. Audit procedure

### 3.1 Per note

Same checks as lote-1 IC §3.1: frontmatter · body vs REFERENCIAS · overclaim · SoT bleed · internal consistency.

### 3.2 Per URL

Fetch/verify every `[REFERENCIAS]` URL; match title/§/TM; spot-check key claims (quote or paraphrase + pointer in report). PDFs: title/abstract/relevant headers.

### 3.3 Extra scans for lote-2

| Note | Extra focus |
|---|---|
| Momento y rotación | \(\tau=I\alpha\) scope (fixed axis vs 3D Euler); no invented \(I_{xx}\) |
| Control robótico | Cascade claims vs ETH PDFs; allocation ≠ plant; sim ≠ flight |
| Sensores de movimiento | Specific accel vs linear accel; 6-axis ≠ mag; ICM-42688-P only from TDK DS; C42 ≠ live SPI1 |

### 3.4 Invention scan

Numeric sensor params, thrusts, inertias, gains, fake datasheet fields, fake OpenStax/ETH section numbers.

---

## 4. Report format

```text
0. Honesty summary
1. Scope + paths
2. Momento y rotación — table + verdict
3. Control robótico — table + verdict
4. Sensores de movimiento — table + verdict
5. Cross-cutting (SoT, sim≠hw)
6. URL matrix
7. Remediations (Cursor-applicable)
8. Overall verdict + whether lote-2 may stay solid
9. Out of scope (lote-1, RAG, …)
```

---

## 5. Acceptance criteria

- [ ] Report written at required path  
- [ ] All three notes + all REFERENCIAS URLs checked  
- [ ] Invention scan documented  
- [ ] Per-note verdict  
- [ ] Remediations actionable or “none”  
- [ ] No Claude edits under `ontology/` or `src/`  
- [ ] Tip still **`v0.5.44`** · no package bump  

---

## 6. Stop conditions

- Do not edit notes.  
- Do not style-rewrite.  
- Do not claim ACCEPT — Cursor review + Engineer.  
- Do not fold lote-1 findings into this report except a one-line “see twin IC” if needed.

---

## 7. Paste for Claude

```text
★ AUTHORIZED investigation — B0-ontology-spine-lote2-citation-review

IC: .jes/artifacts/investigation_contract_ontology_spine_lote2_citation_review_b0.md

Audit ONLY these three solid notes (read-only — do not edit ontology/):
- ontology/02_Fisica/Mecánica/Momento y rotación/Momento y rotación.md
- ontology/04_Robotica/Control robótico/Control robótico.md
- ontology/04_Robotica/Sensores/Sensores de movimiento/Sensores de movimiento.md

Job: verify every [REFERENCIAS] URL + body claims supported;
scan invention / catalog-FS SoT bleed / sim≠hardware overclaim;
verdict PASS | PASS WITH NOTES | FAIL per note.
Write investigation_report_ontology_spine_lote2_citation_review_b0.md

Do NOT re-audit lote-1 (separate IC). Obsidian math $ / $$ is correct.
No src/, no pyproject bump, tip stays v0.5.44. No ACCEPT claim.
```
