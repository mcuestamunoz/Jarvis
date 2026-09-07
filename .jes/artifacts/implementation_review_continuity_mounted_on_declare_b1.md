# Implementation Review — Continuity Declare `mounted_on` B1 (CLI / IDLE)

**Date:** 2026-09-07  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_continuity_mounted_on_declare_b1.md](implementation_contract_continuity_mounted_on_declare_b1.md)  
**Report:** [implementation_report_continuity_mounted_on_declare_b1.md](implementation_report_continuity_mounted_on_declare_b1.md)  
**Buy:** ★ Continuity declare — IDLE parse → existing writer · honest copy · no plate guessing

## Verdict

**PASS**

IC locks held. Thin deterministic assist + IDLE dispatch call `set_component_mounted_on` as-is; ambiguous bare “placa” lists candidates without write; copy stays declared-only; subject-as-own-target bug fixed and regression-tested. Suite **2380** (implementer); Cursor reconfirmed **16/16** new tests.

---

## Checklist

| Criterion | Result |
|---|---|
| Pure `mounted_on_declare_assist` (no LLM / no write) | **Pass** |
| Kinds SET / CLEAR / AMBIGUOUS_TARGET / NONE | **Pass** |
| Subject nouns §3.2; absent subject → orchestrator error | **Pass** |
| Target after first `en`; plate rule no guess on 2+ | **Pass** |
| IDLE dispatch after catalog-rebind, before FN-005 | **Pass** |
| Writer called as-is; ValueError surfaced | **Pass** |
| Copy: Declarado / eliminado — no ensamblado/cabe/verificado | **Pass** |
| Board projector smoke via existing `"montado en"` field | **Pass** |
| Tests T1–T9 (+ extras / regression) | **Pass** — 16 |
| Full suite | **2380** reported |
| No writer/schema/glyphs/ui/seeds/version change | **Pass** — `0.3.8` |

---

## Independent verification

| Check | Result |
|---|---|
| Diff scope | `mounted_on_declare_assist.py` (new) · `orchestrator.py` (+82) · test file (new) · report |
| `pytest tests/test_continuity_mounted_on_declare_b1.py` | **16 passed** |
| `component_writers` / `action_schema` / `spatial_board` / `ui/` / `pyproject` | **Unchanged** |
| Forbidden honesty tokens in success path | **Guarded by T7** |

---

## Notes

### N1 — Empty `AMBIGUOUS_TARGET` candidates

Unresolved target (mount-shaped phrase, no matching part) reuses `AMBIGUOUS_TARGET` with `candidates=()` and a distinct orchestrator message. Acceptable within the 4-kind table; no 5th kind required for B1.

### N2 — Subject-as-target regression

Restricting target search to text after the first `\ben\b` is the correct fix; covered by `test_exact_key_target_esc_montado_en_frame_plate`.

### N3 — Product reachability

Assembly espacial §3.5 gap closed: declare/clear from IDLE chat → Board. Pose mm / edges / fit remain later ★.

---

## Phase

Implementation **closed**. Continuity declare `mounted_on` B1 **PASS**. Await Engineer next focus.
