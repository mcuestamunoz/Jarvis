# Implementation Review — Structure A (masa + compatibilidad de clase)

**Date:** 2026-09-03  
**Reviewer:** JES / Cursor  
**IC:** [implementation_contract_structure_a.md](implementation_contract_structure_a.md)  
**★:** [engineer_ratification_structure_a.md](engineer_ratification_structure_a.md) — Engineer `ratifico` (2026-09-03)  
**Physics lock:** CLASS COMPATIBILITY LEVEL A, not geometric fit  
**Report:** [implementation_report_structure_a.md](implementation_report_structure_a.md)  
**Implementer:** Claude Code

## Verdict

**PASS WITH NOTES**

§2.1 walk leak is fixed at the confirmed seam (`iterate_interactive_session.py`, both call sites) and routed through `set_frame_material`. §2.2 class screening uses the shared predicate, both `_block_progress_status` copies, two MEDIUM gaps (`blocks=["structure"]` only), Continuity locked Spanish copy, no HIGH, `_derive_overall` untouched. Thrust is not a function of `size_class_inch`. Forbidden product copy (`cabe` / VERIFIED / “does not fit”) is absent from titles and Continuity strings.

Reviewer re-ran adjacent tests (**130 passed**) and the full suite (**2140 passed**). Notes are hygiene / residual writer semantics, not a re-implement.

---

## Contract checklist

| Criterion | Result |
|---|---|
| §2.1 iterate `PVC 200g` → override `0.2` + frame `mass_kg` | **Pass** — both wizard call sites (`test_walk_pvc_200g_*`) |
| §2.1 parse full text *before* truncating; `set_frame_material` on DEFINE path | **Pass** — `extract_frame_properties` + `component_patch["frame"]` + iterate writer + recalc |
| §2.1 do not fix only `apply_material_definition` | **Pass** — `mutation_engine.py` unchanged (correct) |
| §2.1 acquisition `"carbono 450g"` still 0.45 | **Pass** |
| §2.1 material-only `"pvc"` does not invent mass; no “PVC has no density” test | **Pass** |
| §2.2 `size_class_inch` extracted; no mm→class; no copy from \(D\) | **Pass** — `extract_frame_properties`; `"pvc 200g"` / `"frame 5 pulgadas"` / `"250mm"` unit tests |
| §2.2 writer optional class; `_frame_completeness` still mass+material | **Pass** — completeness stays `"high"` without class |
| §2.2 one `propeller_diameter_in` helper (property → param → bound SKU) | **Pass** — `project_closure.py:114-159` |
| §2.2 `frame_class_compatibility_state` (not fit/misfit names) | **Pass** — four states as locked |
| Dual `_block_progress_status` AND-condition | **Pass** — orchestrator `:2001-2006` and ERF `:423-425` via `frame_size_blocks_structure_complete` |
| Gaps MEDIUM, `blocks=["structure"]`, not in `_INCOMPATIBLE_CLASS_GAP_TYPES` | **Pass** |
| `_derive_overall` unchanged; incomplete → `NOT_ASSEMBLY_READY` | **Pass** — function body identical; dedicated MEDIUM-only test |
| Continuity locked Spanish copy; short English `Gap.title` | **Pass** (copy in code) — **Note 3:** no test asserts the Spanish sentences |
| Frame prompt mentions pulgadas when \(D\) known | **Pass** — orchestrator conditional; static `COMPONENT_PROMPTS` default unchanged |
| No class → thrust / OP / G22 / \(D^4\) | **Pass** — `calculation_engine.py` / `aerodynamics.py` / `library.py` / G22 filters not edited; identical-thrust test |
| Forbidden copy | **Pass** — product strings; comments only *forbid* those words |
| §5 files; no CAD / HIGH / +0.25 | **Pass** |
| Mandatory tests | **Pass** — `tests/test_structure_a.py` 11; gaps +4; frame +1 |
| Six fixture updates | **Pass** — compatible class added; assertions not weakened (spot-check G9-B fixture) |
| Suite | **Pass** — reviewer **2140** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| Walk path both call sites write 0.2 kg | **Confirmed** — `tests/test_structure_a.py` |
| 7 in / 5 in class → `GAP-FRAME-PROP-SIZE`, structure not complete, thrust identical | **Confirmed** |
| 5 in / no class → `GAP-FRAME-SIZE-MISSING`, class not copied | **Confirmed** |
| 5 in / 5 in class → no frame-class gaps, structure complete | **Confirmed** |
| No propeller → structure complete | **Confirmed** |
| MEDIUM-only flips `overall` to `NOT_ASSEMBLY_READY` | **Confirmed** — `test_gap_frame_prop_size_flips_overall_not_assembly_ready_via_medium_only` |
| Gap titles | **Confirmed** — `"Frame size class missing"` / `"Propeller diameter exceeds declared frame class"` |
| Continuity copy matches IC (missing + incompatible) | **Confirmed in** `project_continuity.py:142-158` |
| Rank before generic architecture pending | **Confirmed** — `:457` before `:459` |
| `_INCOMPATIBLE_CLASS_GAP_TYPES` still ESC / discharge / motor↔prop only | **Confirmed** |
| `5"` / `5 in` / `5 pulgadas` parse; `250mm` ignored | **Confirmed** (extractor probe + unit test) |
| Full suite | **2140 passed** (reviewer) |

---

## Notes (non-blocking — do not re-implement)

### Note 1 — `set_frame_material(..., mass_kg=None)` still pops the override — **REPRODUCED**

Reviewer probe (tmp project, frame 0.65 kg + fibra de carbono, iterate `cambiar material` → `"pvc 5 pulgadas"`):

```text
structure_mass_override_kg   0.65 → None        (borrado en silencio)
components["frame"].mass_kg  0.65 → 0.65        (intacto)
calc total_mass_kg           1.65 → 1.60        (vuelve al factor)
```

Dual truth: el componente canónico sigue declarando 0.65 kg mientras el mirror de params desaparece y la física cae al `structure_mass_factor`. Misma clase de deshonestidad que este IC vino a cerrar, en la dirección opuesta (borrar masa declarada en vez de ignorarla).

Causa: el writer espeja el **argumento**, no el componente ya fusionado. `None` significa dos cosas distintas según el caller:

| Caller | Significado de `mass_kg=None` |
|---|---|
| `actions/iterate.py:363` (nuevo), `orchestrator._apply_inferred_component_spec` | “esta frase no menciona masa” — parcial |
| `component_writers.py:533-538` (`apply_components_delta` re-derive) | “el componente no tiene masa” — total |

El `pop` es **pre-existente**; Structure A añadió el trigger de iterate. Ningún test fija el `pop` (`grep` de `set_frame_material(..., None`: solo casos `material=None`).

Fix propuesto (writer, local): espejar desde los props fusionados — override = `props["mass_kg"]` si existe, `pop` si no. Mantiene el invariante `override == componente.mass_kg` y deja el caller de normalización idéntico (ahí `spec` es el propio componente existente).

### Note 2 — `get_block_in_progress_reason` does not know class screening

If structure is `in_progress` solely because class is `missing`/`class_incompatible`, components are already non-stub, so the reason helper returns `"missing_params"`. Continuity (when `readiness` is passed) still carries the locked class sentence. Do not fold class into that helper in a drive-by.

### Note 3 — Continuity Spanish copy is untested

IC asked the misfit/missing tests to cover copy. Implementation asserts gap **title** (no cabe / verificado / “does not fit”) but never `next_useful_step`. The locked paragraphs are in `_frame_class_next_step`. Compatible PASS has no user-visible class line (absence of gaps) — acceptable.

### Note 4 — Extra `_safe_active_project()` on the frame prompt

Disclosed in the report. Same pattern as other orchestrator lookups. Static `COMPONENT_PROMPTS["frame"]` unchanged when \(D\) is unknown.

### Note 5 — Test names still say `misfit`

`test_misfit_7in_prop_5in_class_…` is internal. Product copy does not say misfit. Ignore.

### Note 6 — Six fixtures

Each added a **compatible** `size_class_inch` matching an incidental propeller diameter. Spot-check: G9-B continuity fixture is catalog-demotion, not structure. `test_cli_stale_energy_recalc.py` documents gemfan 5 in → class 5. No assertion dropped.

---

## Frozen honored

No CAD/FEA. No invented density. No `size_class_inch` in CalculationEngine. No `+0.25`. No mm→class. No copy class from prop. No HIGH / `_derive_overall` edit / `_INCOMPATIBLE_CLASS_GAP_TYPES` membership. No control/sensor/ESC catalog. No DSE scoring. Engineer `workspace/` not used as a test fixture.

---

## Next

Structure A is **closed** at the code+review layer. Optional Engineer CLI walk on `autonomia-15min` (`PVC 200g`, then class vs \(D\)). Do not start the next IC until Engineer names it. Hardware HD-* stays parked.
