# Implementation Review — Structure B Parts Graph (Fase 1)

**Date:** 2026-09-04  
**Reviewer:** Cursor (JES) — independent code + test + seed spot-check  
**Contract:** [implementation_contract_structure_b_parts_graph.md](implementation_contract_structure_b_parts_graph.md)  
**Report:** [implementation_report_structure_b_parts_graph_fase1.md](implementation_report_structure_b_parts_graph_fase1.md)  
**Prerequisite:** Structure honesty **CLOSED** (suite 2200)  
**Baseline:** tag `v0.3.6`

## Verdict

**PASS WITH NOTES**

Fase 1 graph lands as specified: `parent_key`, locked `frame_*` keys, BOM N1
filter + `└` sub-lines, catalog projection for Armattan, wheelbase/configuration
on root, Structure PASS regression green. Suite **2223** confirmed locally.
Seed wheelbases spot-checked against cited pages (TBS 226, iFlight 285,
Armattan 230 + Ti/Al materials).

Ready for Engineer ★ to close Fase 1 or name follow-ons (free-text part UX).

---

## Checklist

| Criterion | Result |
|---|---|
| `ComponentSpec.parent_key` | **Pass** |
| Locked keys `frame_arm/plate/cage/standoff` | **Pass** |
| Config closed vocab; never from `motor_count` | **Pass** |
| Wheelbase keyword-gated (bare mm absent) | **Pass** |
| BOM N1 — no peer lines for children | **Pass** — both BOM loops skip `parent_key` |
| Orphan `parent_key` safe | **Pass** — tested |
| Structure PASS / evidence unchanged w/ children | **Pass** — regression test |
| `BLOCK_TO_COMPONENTS["structure"] == ["frame"]` | **Pass** |
| `engineering_readiness.py` untouched | **Pass** — empty diff |
| Seed sourced (no invented counts) | **Pass** — see N2 |
| Catalog assist upserts parts | **Pass** — UX tests |
| Full suite | **Pass** — **2223** |

---

## Independent verification

| Check | Result |
|---|---|
| `pytest tests/test_frame_parts_graph_v1.py` (+ bind UX / foundation / bind) | **100 passed** |
| `pytest -q` full | **2223 passed** |
| Armattan page (`armattanquads.com`) | 230mm @5in, Compressed X, Ti cage, Al standoffs, CF plate/arms — **confirmed** |
| TBS 5″ racedayquads | Wheelbase 226mm — **confirmed** |
| iFlight XL7 fpv24 | Wheelbase 285mm — **confirmed** |
| `titanio` / `aluminio` in materials lib | **Present** |

---

## Notes

### N1 — Free-text part wiring deferred (acknowledged)

IC §2.4 asked for smallest wiring of part extractors into the apply path.
Implementer shipped **catalog-assist upsert + tested API**, and explicitly
deferred live free-text wizard routing (needs `expected_keys` design). Root
`configuration`/`wheelbase_mm` extractors **are** on `extract_frame_properties`
(live frame free-text path). Residual is honest and scoped — not a silent
drop. Optional follow-on IC if Engineer wants chat-declared parts.

### N2 — Armattan counts left unset vs “Included” BOM on page

Report says no page states counts. Armattan’s **Included** section does list
`4x 4mm Arms` (and enumerated plates/standoffs). Leaving `arm_count` unset is
**conservative** (avoids config→count inference) and still sourced-honest for
materials/wheelbase. Optional later seed enrichment from the Included list —
not a FAIL.

### N3 — `compressed-x` alias missing in free-text map

Catalog seed maps Compressed-X → `quad_x` explicitly. `CONFIGURATION_MAP` has
no `compressed-x` / `compressed x` alias for free text. Low risk (catalog path
covers Armattan). Optional alias add.

### N4 — Diverge leaves children

IC allowed “leave children” as the simpler choice. No auto-clear of
`frame_*` when frame `catalog_ref` clears — acceptable; document in residual
if frankenstein-with-orphans ever matters.

### N5 — Report filename vs contract

Report links `…_parts_graph_fase1.md` contract; actual IC is
`implementation_contract_structure_b_parts_graph.md`. Cosmetic.

---

## Next

Engineer ★: close Structure B Fase 1, and/or open free-text part-wiring /
Armattan count seed follow-ons. MEASURE / PASS widen still out.
