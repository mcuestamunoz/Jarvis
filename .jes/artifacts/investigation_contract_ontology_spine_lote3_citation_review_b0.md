# Investigation Contract — Ontology spine lote-3 citation review (`B0-ontology-spine-lote3-citation-review`)

**Project:** Jarvis  
**Date:** 2026-09-28  
**Author:** JES / Cursor (Engineer Interface) — **investigation / review only**  
**Investigator:** **Claude Code** — ★ AUTHORIZED: **review now**  
**Reviewer:** Cursor against this contract · Engineer decides any content remediations  

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-28) — citation audit complete; remediations R1–R3 landed by Cursor  
**Parents:**
- Epoch **`0.6.x`**: [`docs/JARVIS_KNOWLEDGE_VISION.md`](../../docs/JARVIS_KNOWLEDGE_VISION.md)  
- Twin audits: [lote-1](investigation_contract_ontology_spine_lote1_citation_review_b0.md) · [lote-2](investigation_contract_ontology_spine_lote2_citation_review_b0.md) (both ★ ACCEPT CLOSED)  
- Spine lote-3 **landed `solid`** (Engineer + GPT cite → Cursor land):
  - [`ontology/04_Robotica/Sensores/Sensores de movimiento/Acelerómetro/Acelerómetro.md`](../../ontology/04_Robotica/Sensores/Sensores%20de%20movimiento/Acelerómetro/Acelerómetro.md)
  - [`ontology/04_Robotica/Sensores/Sensores de movimiento/Giroscopio/Giroscopio.md`](../../ontology/04_Robotica/Sensores/Sensores%20de%20movimiento/Giroscopio/Giroscopio.md)
  - [`ontology/04_Robotica/Sensores/Sensores de movimiento/IMU/IMU.md`](../../ontology/04_Robotica/Sensores/Sensores%20de%20movimiento/IMU/IMU.md)
- Tip remains **`v0.5.44`** until a separate 0.6 tag decision  
- Plantilla: Obsidian math = `$` / `$$` only

**Type:** **Investigation / citation-audit Contract** — same bar as lote-1/2: cited claims supported; URLs resolve; no invention; no catalog/FS SoT bleed; ICM-42688-P specifics match datasheet.  
**Package:** **do not bump** `pyproject.toml`. No git tag.  
**Not** Implementation · not editing `ontology/` · not re-auditing lote-1/2 · not RAG · not `src/`.

**Outputs (required):**
1. `.jes/artifacts/investigation_report_ontology_spine_lote3_citation_review_b0.md`
2. Per-note audit (Acelerómetro / Giroscopio / IMU)
3. URL matrix (reach + title match + claim support)
4. Invention / overclaim / SoT-bleed / datasheet-fidelity findings
5. Verdict per note: **PASS** · **PASS WITH NOTES** · **FAIL**
6. Remediations for Cursor (or “none”) · explicit non-edits

**Checkpoint:** tip **`v0.5.44`** · report-only · lote-3 files read-only for Claude

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B0-ontology-spine-lote3-citation-review`** |
| 2 | Scope | **Only** the three lote-3 paths above (+ their `[REFERENCIAS]`) |
| 3 | No silent rewrites | Claude does **not** edit `ontology/`; propose patches in the report |
| 4 | Standard of “true” | Source supports claim. Fake §§, dead URLs, invented numbers = FINDING |
| 5 | SoT bleed | Flag prose authorizing SKU values, Continuity decisions, or FS gains as physical truth |
| 6 | Datasheet bar (heightened) | ICM-42688-P ranges (accel g / gyro dps), interfaces (I3C/I²C/SPI), and any numeric noise/ODR claims must match TDK DS-000347 (or product page if only qualitative). Prefer verifying against a **working** datasheet mirror if a cited PDF path 404s (same class as lote-2 F3) |
| 7 | Math delimiters | `$` / `$$` is correct — do **not** FAIL for not using `\[...\]` |
| 8 | Forbidden report claims | “RAG-ready” · “Claude marks solid” · “Replace library with TDK/NASA” |

**Product sentence:**

```text
Verificar que las tres notas solid del spine lote-3 (Acelerómetro,
Giroscopio, IMU) citan de verdad lo que afirman — sin invención ni
sangrado a catálogo/FS — y reportar PASS/FAIL por nota.
```

---

## 1. Why this exists

Same workflow:

```text
Cursor draft → Engineer + GPT cite → Cursor land solid → Claude cite-audit
```

Lote-3 materializes the dangling `[[IMU]]` / `[[Giroscopio]]` / `[[Acelerómetro]]` leaves next to the already-audited [[Sensores de movimiento]] hub. Higher risk: device-specific ICM ranges, Analog Devices timeouts, NASA TM title placeholders, stale datasheet PDF paths.

---

## 2. Locked stances

1. **Cite or do not claim.**  
2. **`never_invents` must hold** (no invented craft quantities; SKU params only if datasheet-backed and scoped as device-specific).  
3. **Jarvis C6/C7/C42 explain-map OK** — claiming sim/SPI validates copper/flight = FAIL.  
4. **WHO_AM_I / ScriptedSpi ≠ calibration ≠ flight** — flag if weakened.  
5. **6-axis IMU ≠ necessarily magnetometer / ≠ AHRS** — confirm notes keep this.  
6. **Do not re-audit lote-1/2** in this Buy.  
7. Network failure → **UNVERIFIED (network)** — do not invent PASS.

---

## 3. Audit procedure

### 3.1 Per note

Same as lote-1 §3.1: frontmatter · body vs REFERENCIAS · overclaim · SoT bleed · internal consistency.

### 3.2 Per URL

Fetch/verify every `[REFERENCIAS]` URL; match title/§/TM; spot-check key claims. PDFs: title page + relevant sections.

### 3.3 Extra scans for lote-3

| Note | Extra focus |
|---|---|
| Acelerómetro | Specific force vs linear accel; inclinometer-only-when-static; ICM accel ±2/4/8/16 g scoped as device-specific |
| Giroscopio | ω not absolute angle; bias→drift; ARW; ICM gyro dps ranges scoped as device-specific |
| IMU | 6-axis = accel+gyro; mag optional; IMU≠estimator≠true attitude; NASA-TM-20250008926 **actual PDF title**; datasheet path live or flagged with working alternate |

### 3.4 Invention scan

Fake WHO_AM_I, ODR, noise densities, registers, universal “all IMUs have X”, invented g/dps for non-cited devices.

---

## 4. Report format

```text
0. Honesty summary
1. Scope + paths
2. Acelerómetro — table + verdict
3. Giroscopio — table + verdict
4. IMU — table + verdict
5. Cross-cutting (SoT, sim≠hw, datasheet)
6. URL matrix
7. Remediations (Cursor-applicable)
8. Overall verdict + whether lote-3 may stay solid
9. Out of scope (lote-1/2, RAG, …)
```

---

## 5. Acceptance criteria

- [ ] Report at required path  
- [ ] All three notes + all REFERENCIAS URLs checked  
- [ ] ICM claims checked against datasheet text (or FINDING if unreachable)  
- [ ] Invention scan documented  
- [ ] Per-note verdict + remediations or “none”  
- [ ] No Claude edits under `ontology/` or `src/`  
- [ ] Tip still **`v0.5.44`** · no package bump  

---

## 6. Stop conditions

- Do not edit notes.  
- Do not style-rewrite.  
- Do not claim ACCEPT — Cursor review + Engineer.  
- Do not fold lote-1/2 into this report except one-line twin pointers.

---

## 7. Paste for Claude

```text
★ AUTHORIZED investigation — B0-ontology-spine-lote3-citation-review

IC: .jes/artifacts/investigation_contract_ontology_spine_lote3_citation_review_b0.md

Audit ONLY these three solid notes (read-only — do not edit ontology/):
- ontology/04_Robotica/Sensores/Sensores de movimiento/Acelerómetro/Acelerómetro.md
- ontology/04_Robotica/Sensores/Sensores de movimiento/Giroscopio/Giroscopio.md
- ontology/04_Robotica/Sensores/Sensores de movimiento/IMU/IMU.md

Job: verify every [REFERENCIAS] URL + body claims supported;
ICM-42688-P numeric/interface claims vs datasheet;
scan invention / SoT bleed / sim≠hardware;
verdict PASS | PASS WITH NOTES | FAIL per note.
Write investigation_report_ontology_spine_lote3_citation_review_b0.md

Do NOT re-audit lote-1/2. Obsidian math $ / $$ is correct.
No src/, no pyproject bump, tip stays v0.5.44. No ACCEPT claim.
```
