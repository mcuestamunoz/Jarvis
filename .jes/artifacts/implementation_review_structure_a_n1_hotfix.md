# Implementation Review — Structure A N1 hotfix

**Date:** 2026-09-03  
**Reviewer:** JES / Cursor  
**IC:** [implementation_contract_structure_a_n1_hotfix.md](implementation_contract_structure_a_n1_hotfix.md)  
**Report:** [implementation_report_structure_a_n1_hotfix.md](implementation_report_structure_a_n1_hotfix.md)  
**Implementer:** Claude Code

## Verdict

**PASS WITH NOTE**

The writer now mirrors `structure_mass_override_kg` from the merged frame
properties rather than from the partial-update argument. This closes the
reproduced dual truth: a size/material-only update preserves the frame's
declared mass in both the canonical component and calculation parameters.

The change is local to the writer plus the two test files authorized by §5.
Targeted tests pass (**38**) and the reviewer full suite passes (**2143**).

## Contract checklist

| Criterion | Result |
|---|---|
| Mirror from merged `props["mass_kg"]` | **Pass** |
| Partial size/material update preserves existing override | **Pass** |
| No merged mass genuinely present → override removed | **Pass** — unchanged writer branch |
| Walk `"pvc 5 pulgadas"` preserves 0.65 kg and total mass | **Pass** |
| Explicit `"pvc 200g"` path unchanged | **Pass** — parent regression remains green |
| `apply_components_delta` re-derive remains correct | **Pass** — reviewer probe normalized stale 9.99 → 0.45 |
| No gaps / Continuity / progress / rollup / parser edits | **Pass** |
| Lints | **Pass** — no diagnostics in the three files |
| Full suite | **Pass** — **2143** |

## Independent verification

- Writer-level size-only update preserves `structure_mass_override_kg=0.65`,
  component `mass_kg=0.65`, and writes `size_class_inch=5`.
- Material-only update preserves the pre-existing override.
- End-to-end iterate walk preserves `CalculationEngine.total_mass_kg`.
- `apply_components_delta(state, {})` re-derived a deliberately stale override
  from `9.99` to the component's declared `0.45`.

## Note

The implementation report says every caller shape has a regression test.
There is no dedicated automated test for the frame
`apply_components_delta(state, {})` normalization shape; the reviewer verified
it directly. This is a coverage wording issue, not a behavior defect, and the
full DA2 suite remains green. No follow-up is required for this hotfix.

## Closure

N1 is **closed**. The remaining parent-review notes N2–N6 are non-blocking and
are not part of this hotfix.
