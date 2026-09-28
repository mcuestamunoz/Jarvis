# Investigation Contract — Ontology spine lote-5 citation review (`B0-ontology-spine-lote5-citation-review`)

**Project:** Jarvis  
**Date:** 2026-09-28  
**Author:** JES / Cursor (Engineer Interface) — **investigation / review only**  
**Investigator:** **Claude Code** — ★ AUTHORIZED: **review now**  
**Reviewer:** Cursor against this contract · Engineer decides any content remediations  

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-28) — citation audit complete; remediations R1–R2 landed by Cursor  
**Parents:**
- Epoch **`0.6.x`**: [`docs/JARVIS_KNOWLEDGE_VISION.md`](../../docs/JARVIS_KNOWLEDGE_VISION.md)  
- Twin audits: [lote-1](investigation_contract_ontology_spine_lote1_citation_review_b0.md) · [lote-2](investigation_contract_ontology_spine_lote2_citation_review_b0.md) · [lote-3](investigation_contract_ontology_spine_lote3_citation_review_b0.md) · [lote-4](investigation_contract_ontology_spine_lote4_citation_review_b0.md) (all ★ ACCEPT CLOSED)  
- Spine lote-5 **landed `solid`** (Engineer + GPT cite → Cursor land; commits `5b1703c` · `75ff061` · `335035d`/`d4f53cc`):
  - [`ontology/02_Fisica/Electromagnetismo/Magnetismo/Magnetismo.md`](../../ontology/02_Fisica/Electromagnetismo/Magnetismo/Magnetismo.md)
  - [`ontology/04_Robotica/Navegación%20y%20planificación/Navegación%20y%20planificación.md`](../../ontology/04_Robotica/Navegación%20y%20planificación/Navegación%20y%20planificación.md)
  - [`ontology/03_Ingenieria/Electrónica/Forma%20de%20medición%20en%20banco%20de%20empuje/Forma%20de%20medición%20en%20banco%20de%20empuje.md`](../../ontology/03_Ingenieria/Electrónica/Forma%20de%20medición%20en%20banco%20de%20empuje/Forma%20de%20medición%20en%20banco%20de%20empuje.md)
- Tip remains **`v0.5.44`** until a separate 0.6 tag decision  
- Plantilla: Obsidian math = `$` / `$$` only

**Type:** **Investigation / citation-audit Contract** — same bar as lote-1–4: cited claims supported; URLs resolve; no invention; no catalog/FS SoT bleed. Heightened focus on **nav/mag/bench honesty**: mag≠yaw true · mag≠geo north · C37 sim≠copper · estimation≠planning≠control · C39≠EKF/GPS · sim plant≠real nav · thrust-stand shape ≠ invented HD curve.  
**Package:** **do not bump** `pyproject.toml`. No git tag.  
**Not** Implementation · not editing `ontology/` · not re-auditing lote-1–4 · not RAG · not `src/` · not `library/`.

**Outputs (required):**
1. `.jes/artifacts/investigation_report_ontology_spine_lote5_citation_review_b0.md`
2. Per-note audit (Magnetismo / Navegación y planificación / Forma de medición en banco de empuje)
3. URL matrix (reach + title match + claim support)
4. Invention / overclaim / SoT-bleed / honesty-theme findings
5. Verdict per note: **PASS** · **PASS WITH NOTES** · **FAIL**
6. Remediations for Cursor (or “none”) · explicit non-edits

**Checkpoint:** tip **`v0.5.44`** · report-only · lote-5 files read-only for Claude

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B0-ontology-spine-lote5-citation-review`** |
| 2 | Scope | **Only** the three lote-5 paths above (+ their `[REFERENCIAS]`) |
| 3 | No silent rewrites | Claude does **not** edit `ontology/`; propose patches in the report |
| 4 | Standard of “true” | Source supports claim. Fake §§, dead URLs, invented numbers = FINDING |
| 5 | SoT bleed | Flag prose authorizing SKU values (`mass_g`, `power_w`, `thrust_gf`, `autonomy_min`) or closing HD-004/005 with invented curves as physical truth from this note alone |
| 6 | Honesty bar (heightened) | Fail or FINDING if note collapses: mag↔yaw true · norte mag↔geo · C37 sim↔hw · estimación↔plan↔control · C39↔EKF/GPS · planta sim↔navegación real · resultado banco↔propiedad motor · T2 inventado |
| 7 | Math delimiters | `$` / `$$` is correct — do **not** FAIL for not using `\[...\]` |
| 8 | Forbidden report claims | “RAG-ready” · “Claude marks solid” · “Replace library with UIUC/NASA OPs” · inventing HD curves |

**Product sentence:**

```text
Verificar que las tres notas solid del spine lote-5 (Magnetismo,
Navegación, forma banco empuje) citan de verdad lo que afirman —
sin invención ni sangrado a catálogo/FS — y reportar PASS/FAIL
por nota.
```

---

## 1. Why this exists

Same workflow:

```text
Cursor draft → Engineer + GPT cite → Cursor land solid → Claude cite-audit
```

Lote-5 closes vision §8.1 #12: **Magnetismo (yaw/C37)**, **Navegación (C39 map)**, **HD-facing thrust-stand measurement shape**. Sources mix NOAA WMM/declination, Analog Devices mag/EKF notes, PX4 controllers/EKF2, Nav2 concepts, MIT Underactuated planning/estimation, UIUC Propeller Database, NASA Airvolt / thrust uncertainty, APC analytic data. Higher risk: dead Nav2/PX4/NOAA slugs, AD bot walls, overclaiming C39 as real nav stack, inventing stand curves for HD-005.

---

## 2. Locked stances

1. **Cite or do not claim.**  
2. **`never_invents` must hold** (no invented craft/SKU quantities; HD examples are conceptual gaps only).  
3. **Jarvis APLICACIONES may map C37/C38/C39/C40 as explain** — OK. Claiming those rungs validate copper/GPS/flight = FAIL.  
4. **Estimation / planning / control** remain distinct — flag collapses.  
5. **Do not re-audit lote-1–4** in this Buy.  
6. Network failure → **UNVERIFIED (network)** — do not invent PASS. Prefer a working mirror if a cited PDF/path 404s (same class as prior lotes; note Nav2 URL already once-corrected to `/concepts/` + rolling state-estimation path).

---

## 3. Audit procedure

### 3.1 Per note

Same as lote-1 §3.1: frontmatter · body vs REFERENCIAS · overclaim · SoT bleed · internal consistency · `estado: solid` / `formula_citation: cited…`.

### 3.2 Per URL

Fetch/verify every `[REFERENCIAS]` URL; match title/§; spot-check key claims. PDFs: title page + relevant sections (NASA NTRS; UIUC pubs; AD AN-1157).

### 3.3 Extra scans for lote-5

| Note | Extra focus |
|---|---|
| Magnetismo | Mag measures $\mathbf{B}$, not yaw; declination NOAA; hard/soft iron AD; $\operatorname{atan2}$ toy only; C37 sim ≠ copper ≠ WHO_AM_I validity |
| Navegación y planificación | Estimation ≠ planning ≠ control (Nav2/PX4); C39 = Jarvis map not EKF/GPS; observation ≠ true state; sim plant ≠ instrumented nav |
| Forma medición banco empuje | Measurement shape ≠ thrust value; variable set depends on static vs flow; T1/T2/estimado; UIUC $P=2\pi nQ$; no invented HD-004/005 curves; stand set ≠ motor intrinsic |

### 3.4 Invention scan

Invented `thrust_gf`, GPS accuracy, soft-iron matrices, autonomy_min, HD OP tables, fake NOAA/PX4/Nav2/UIUC/NASA section titles.

---

## 4. Report format

```text
0. Honesty summary
1. Scope + paths
2. Magnetismo — table + verdict
3. Navegación y planificación — table + verdict
4. Forma de medición en banco de empuje — table + verdict
5. Cross-cutting (SoT, mag/nav/bench honesty)
6. URL matrix
7. Remediations (Cursor-applicable)
8. Overall verdict + whether lote-5 may stay solid
9. Out of scope (lote-1–4, RAG, library, …)
```

---

## 5. Acceptance criteria

- [ ] Report at required path  
- [ ] All three notes + all REFERENCIAS URLs checked  
- [ ] Honesty-theme scan documented  
- [ ] Invention scan documented  
- [ ] Per-note verdict + remediations or “none”  
- [ ] No Claude edits under `ontology/`, `library/`, or `src/`  
- [ ] Tip still **`v0.5.44`** · no package bump  

---

## 6. Stop conditions

- Do not edit notes.  
- Do not style-rewrite.  
- Do not claim ACCEPT — Cursor review + Engineer.  
- Do not fold lote-1–4 into this report except one-line twin pointers.

---

## 7. Paste for Claude

```text
★ AUTHORIZED investigation — B0-ontology-spine-lote5-citation-review

IC: .jes/artifacts/investigation_contract_ontology_spine_lote5_citation_review_b0.md

Audit ONLY these three solid notes (read-only — do not edit ontology/):
- ontology/02_Fisica/Electromagnetismo/Magnetismo/Magnetismo.md
- ontology/04_Robotica/Navegación y planificación/Navegación y planificación.md
- ontology/03_Ingenieria/Electrónica/Forma de medición en banco de empuje/Forma de medición en banco de empuje.md

Job: verify every [REFERENCIAS] URL + body claims supported;
scan invention / SoT bleed / honesty collapses
(mag≠yaw true, mag≠geo north, C37 sim≠hw,
estimation≠planning≠control, C39≠EKF/GPS, sim≠real nav,
stand shape≠invented HD curve);
verdict PASS | PASS WITH NOTES | FAIL per note.
Write investigation_report_ontology_spine_lote5_citation_review_b0.md

Do NOT re-audit lote-1–4. Obsidian math $ / $$ is correct.
No src/, no library/, no pyproject bump, tip stays v0.5.44. No ACCEPT claim.
```
