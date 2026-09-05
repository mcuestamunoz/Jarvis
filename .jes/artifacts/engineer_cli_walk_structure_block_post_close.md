# Engineer CLI Walk — Structure block post-close (2026-09-04)

**Authority:** Engineer manual walk  
**Context:** Structure block ★ CLOSED @ suite 2229 · fresh workspace  
**Project:** autonomía-de-10min · `9ada1a1b0cca`

## Verdict

**ACCEPT** for Structure close verification.

Honesty `PASS *`, frame catalog assist, and ASSEMBLY READY path behaved as designed. Parts-graph / G-N1 **not exercised** this walk (TBS pick has no seeded part children). No reopen of Structure MEASURE.

---

## What the walk verified

| Feature | Evidence | Result |
|---|---|---|
| Frame catalog assist | `ayúdame a elegir` → 4 SKUs → pick #4 TBS Source One V5 | **Pass** |
| Structure `PASS *` + footnote | Both `estado` dumps show asterisk + locked Structure footnote before Control | **Pass** |
| Control `PASS *` coexistence | Both footnotes present, Structure before Control | **Pass** |
| TBS without material → declarative BOM | `◇ frame: tbs_source_one_v5_5in […] (declarativo)` — seed has mass/class, **no** material | **Pass** (honest) |
| No fabricated part `└` lines on TBS | Seed has no arm/plate/cage/standoff materials for TBS | **Pass** |
| `catalog_bound` does not invent Structure PASS physics | PASS * still identity/LEVEL A disclaimer | **Pass** |
| ASSEMBLY READY reachable | After DSE apply + recalc/sim, overall ASSEMBLY READY | **Pass** (product path) |
| Prop/Energy weak-evidence rollup | `CERRADO — evidencia débil (no hay punto de operación de catálogo)` | **Pass** (honest) |

## Not exercised (still closed / debt)

| Feature | Why missed |
|---|---|
| Parts graph children / BOM `└` | Need Armattan (or free-text G-N1), not TBS |
| G-N1 root+parts free-text | Used catalog pick, not `"fibra …, 4 brazos…"` |
| Frame free-text config/wheelbase | Catalog path only |

Optional follow walk: pick Armattan Rooster **or** free-text root+parts — not required to keep Structure closed.

---

## Product observations (not Structure reopen)

1. **DSE → 3 motors on a 5″ quad frame catalog SKU** — autonomy goal met; Structure correctly does **not** cross-check arms↔motors. Situation says “Diseño validado” with low margin next-step — consistent with existing Continuity, not a new Structure lie.
2. **FC “ayúdame a elegir”** falls to free-text prompt (no FC catalog) — expected.
3. **ESC stays declarative** (`ESC 40A`) while ASSEMBLY READY — known declaration-complete vs physics pattern (same class as Control/Structure asterisks).
4. **First `estado`:** Requirements INCOMPLETE (autonomy unmet) + Structure/Control `PASS *` + NOT ASSEMBLY READY — correct gate.

---

## Recommendation

Keep Structure block **CLOSED**. Optional Engineer note only if you want a short Armattan/`└` smoke walk later; do not open MEASURE or re-litigate PASS meaning from this transcript.
