# Investigation Contract — Ontology spine lote-4 citation review (`B0-ontology-spine-lote4-citation-review`)

**Project:** Jarvis  
**Date:** 2026-09-28  
**Author:** JES / Cursor (Engineer Interface) — **investigation / review only**  
**Investigator:** **Claude Code** — ★ AUTHORIZED: **review now**  
**Reviewer:** Cursor against this contract · Engineer decides any content remediations  

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-28) — citation audit complete; remediations R1–R5 landed by Cursor  
**Parents:**
- Epoch **`0.6.x`**: [`docs/JARVIS_KNOWLEDGE_VISION.md`](../../docs/JARVIS_KNOWLEDGE_VISION.md)  
- Twin audits: [lote-1](investigation_contract_ontology_spine_lote1_citation_review_b0.md) · [lote-2](investigation_contract_ontology_spine_lote2_citation_review_b0.md) · [lote-3](investigation_contract_ontology_spine_lote3_citation_review_b0.md) (all ★ ACCEPT CLOSED)  
- Spine lote-4 **landed `solid`** (Engineer + GPT cite → Cursor land; commits `dc4d418`…`6ce81c4`):
  - [`ontology/04_Robotica/Actuadores/Actuadores.md`](../../ontology/04_Robotica/Actuadores/Actuadores.md)
  - [`ontology/04_Robotica/Actuadores/Motores/Motores.md`](../../ontology/04_Robotica/Actuadores/Motores/Motores.md)
  - [`ontology/04_Robotica/Actuadores/Motores/Motor%20DC/Motor%20DC.md`](../../ontology/04_Robotica/Actuadores/Motores/Motor%20DC/Motor%20DC.md)
  - [`ontology/02_Fisica/Electromagnetismo/Corriente%20y%20circuitos/Corriente%20y%20circuitos.md`](../../ontology/02_Fisica/Electromagnetismo/Corriente%20y%20circuitos/Corriente%20y%20circuitos.md)
  - [`ontology/03_Ingenieria/Electrónica/C-rate%20de%20batería/C-rate%20de%20batería.md`](../../ontology/03_Ingenieria/Electrónica/C-rate%20de%20batería/C-rate%20de%20batería.md)
  - [`ontology/03_Ingenieria/Electrónica/Punto%20de%20operación%20vs%20capacidad%20intrínseca/Punto%20de%20operación%20vs%20capacidad%20intrínseca.md`](../../ontology/03_Ingenieria/Electrónica/Punto%20de%20operación%20vs%20capacidad%20intrínseca/Punto%20de%20operación%20vs%20capacidad%20intrínseca.md)
- Tip remains **`v0.5.44`** until a separate 0.6 tag decision  
- Plantilla: Obsidian math = `$` / `$$` only

**Type:** **Investigation / citation-audit Contract** — same bar as lote-1/2/3: cited claims supported; URLs resolve; no invention; no catalog/FS SoT bleed. Heightened focus on **craft honesty**: ESC≠motor, command≠thrust, OP≠intrinsic, Kv≠thrust, RF≠DC, C-rate≠autonomy.  
**Package:** **do not bump** `pyproject.toml`. No git tag.  
**Not** Implementation · not editing `ontology/` · not re-auditing lote-1/2/3 · not RAG · not `src/` · not `library/`.

**Outputs (required):**
1. `.jes/artifacts/investigation_report_ontology_spine_lote4_citation_review_b0.md`
2. Per-note audit (Actuadores / Motores / Motor DC / Corriente y circuitos / C-rate / OP vs intrínseco)
3. URL matrix (reach + title match + claim support)
4. Invention / overclaim / SoT-bleed / honesty-theme findings
5. Verdict per note: **PASS** · **PASS WITH NOTES** · **FAIL**
6. Remediations for Cursor (or “none”) · explicit non-edits

**Checkpoint:** tip **`v0.5.44`** · report-only · lote-4 files read-only for Claude

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B0-ontology-spine-lote4-citation-review`** |
| 2 | Scope | **Only** the six lote-4 paths above (+ their `[REFERENCIAS]`) |
| 3 | No silent rewrites | Claude does **not** edit `ontology/`; propose patches in the report |
| 4 | Standard of “true” | Source supports claim. Fake §§, dead URLs, invented numbers = FINDING |
| 5 | SoT bleed | Flag prose authorizing SKU values (`mass_g`, `power_w`, `thrust_gf`, `autonomy_min`, current/W of a named pack) as physical truth from this note alone |
| 6 | Honesty bar (heightened) | Fail or FINDING if note collapses: ESC↔motor · comando↔fuerza/thrust · OP↔propiedad intrínseca · Kv/`k_n`↔thrust · potencia RF↔consumo DC · C-rate↔autonomía · W↔Wh |
| 7 | Math delimiters | `$` / `$$` is correct — do **not** FAIL for not using `\[...\]` |
| 8 | Forbidden report claims | “RAG-ready” · “Claude marks solid” · “Replace library with TI/maxon/BU” · inventing SKU OP tables |

**Product sentence:**

```text
Verificar que las seis notas solid del spine lote-4 (actuadores,
motores, corriente, C-rate, OP) citan de verdad lo que afirman —
sin invención ni sangrado a catálogo/FS — y reportar PASS/FAIL
por nota.
```

---

## 1. Why this exists

Same workflow:

```text
Cursor draft → Engineer + GPT cite → Cursor land solid → Claude cite-audit
```

Lote-4 is the **craft/catalog honesty** spine: actuation chain, motor–ESC–prop, electrical fundamentals, battery C-rate, and OP vs component specs. Sources mix MIT OCW/manipulation, TI drone ESC (slyt692 / TIDA / tiducf1), PX4 allocation, OpenStax, Battery University, maxon constants. Higher risk: treating catalog toy numbers as measured OPs, dead TI/maxon PDF paths, over-reading Ohm/`P=I²R`, inventing Ah→A continuous limits.

---

## 2. Locked stances

1. **Cite or do not claim.**  
2. **`never_invents` must hold** (no invented craft quantities; examples like `4 Ah` / `1C → 4 A` are OK only as **illustrative arithmetic**, not as a SKU claim).  
3. **Jarvis APLICACIONES may map FS/craft/catalog as explain** — OK. Claiming ontology authorizes library numbers or FS gains as physical truth = FAIL.  
4. **Command / allocation / ESC / motor / hélice / thrust** remain distinct layers — flag any paragraph that collapses them into a deterministic chain without model.  
5. **Do not re-audit lote-1/2/3** in this Buy.  
6. Network failure → **UNVERIFIED (network)** — do not invent PASS. Prefer a working mirror if a cited PDF 404s (same class as lote-2/3 datasheet FINDINGs).

---

## 3. Audit procedure

### 3.1 Per note

Same as lote-1 §3.1: frontmatter · body vs REFERENCIAS · overclaim · SoT bleed · internal consistency · `estado: solid` / `formula_citation: cited…`.

### 3.2 Per URL

Fetch/verify every `[REFERENCIAS]` URL; match title/§/tool ID; spot-check key claims. PDFs: title page + relevant sections (TI slyt692 / tiducf1; maxon constants PDF).

### 3.3 Extra scans for lote-4

| Note | Extra focus |
|---|---|
| Actuadores | Command ≠ physical force; allocation (`u=Pm`) ≠ plant dynamics; actuator may be ESC+motor+hélice; PX4 `ActuatorMotors` = normalised setpoint; saturation / input constraints |
| Motores | Motor ≠ full actuator when transmission exists; ESC ≠ motor; `τ=Kt I` scope + transmission caveat; thrust ≠ intrinsic motor property; TI FC→ESC→motor architecture |
| Motor DC | Brushed vs BLDC scoped correctly; Kv/`k_n` ≠ thrust; no invented SKU W/A/RPM |
| Corriente y circuitos | `I=dQ/dt`; Ohm not universal; `P=VI` vs `P=I²R` / `V²/R` only for ohmic; W ≠ Wh; RF ≠ DC input; losses along battery→ESC→motor |
| C-rate de batería | `C_rate = I/Q`; continuous vs peak; do not invent C from capacity alone; coulomb (C) ≠ C-rate; capacity depends on discharge conditions (BU-402/904) |
| OP vs intrínseco | Spec/`k_n`/`k_M` ≠ OP thrust; OP must keep conditions; no invented performance curves; maxon formulas scoped as motor constants |

### 3.4 Invention scan

Invented Kv, thrust_gf, current_a, power_w, autonomy_min, Ah continuous limits, fake OpenStax/TI/PX4/BU/maxon section numbers, universal “all motors have X”, OP tables without source.

---

## 4. Report format

```text
0. Honesty summary
1. Scope + paths
2. Actuadores — table + verdict
3. Motores — table + verdict
4. Motor DC — table + verdict
5. Corriente y circuitos — table + verdict
6. C-rate de batería — table + verdict
7. OP vs capacidad intrínseca — table + verdict
8. Cross-cutting (SoT, honesty themes, ESC≠motor, OP≠intrinsic)
9. URL matrix
10. Remediations (Cursor-applicable)
11. Overall verdict + whether lote-4 may stay solid
12. Out of scope (lote-1/2/3, RAG, library edits, …)
```

---

## 5. Acceptance criteria

- [ ] Report at required path  
- [ ] All six notes + all REFERENCIAS URLs checked  
- [ ] Honesty-theme scan documented (ESC/motor/OP/Kv/RF/C-rate)  
- [ ] Invention scan documented  
- [ ] Per-note verdict + remediations or “none”  
- [ ] No Claude edits under `ontology/`, `library/`, or `src/`  
- [ ] Tip still **`v0.5.44`** · no package bump  

---

## 6. Stop conditions

- Do not edit notes.  
- Do not style-rewrite.  
- Do not claim ACCEPT — Cursor review + Engineer.  
- Do not fold lote-1/2/3 into this report except one-line twin pointers.

---

## 7. Paste for Claude

```text
★ AUTHORIZED investigation — B0-ontology-spine-lote4-citation-review

IC: .jes/artifacts/investigation_contract_ontology_spine_lote4_citation_review_b0.md

Audit ONLY these six solid notes (read-only — do not edit ontology/):
- ontology/04_Robotica/Actuadores/Actuadores.md
- ontology/04_Robotica/Actuadores/Motores/Motores.md
- ontology/04_Robotica/Actuadores/Motores/Motor DC/Motor DC.md
- ontology/02_Fisica/Electromagnetismo/Corriente y circuitos/Corriente y circuitos.md
- ontology/03_Ingenieria/Electrónica/C-rate de batería/C-rate de batería.md
- ontology/03_Ingenieria/Electrónica/Punto de operación vs capacidad intrínseca/Punto de operación vs capacidad intrínseca.md

Job: verify every [REFERENCIAS] URL + body claims supported;
scan invention / SoT bleed / craft-honesty collapses
(ESC≠motor, command≠thrust, OP≠intrinsic, Kv≠thrust, RF≠DC, C-rate≠autonomy);
verdict PASS | PASS WITH NOTES | FAIL per note.
Write investigation_report_ontology_spine_lote4_citation_review_b0.md

Do NOT re-audit lote-1/2/3. Obsidian math $ / $$ is correct.
No src/, no library/, no pyproject bump, tip stays v0.5.44. No ACCEPT claim.
```
