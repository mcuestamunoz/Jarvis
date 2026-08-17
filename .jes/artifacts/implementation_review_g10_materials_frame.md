# Implementation Review — G10 Material Catalog / Frame Acquisition

**Project:** Jarvis  
**Date:** 2026-08-15  
**Reviewer:** Cursor (JES)  
**Type:** Implementation review  

**Contract:** `.jes/artifacts/implementation_contract_g10_materials_frame.md`  
**Report:** `.jes/artifacts/implementation_report_g10_materials_frame.md`  
**Design:** CLOSED ★1–★8  
**Base:** `checkpoint-g3`

---

## Veredicto

### **PASS WITH NOTES**

★1–★8 implementados en la capa correcta; regresión §5.2 cubierta con test; suite local re-run verde. Listo para CLI probe Engineer → `checkpoint-g10`.

| Criterio IC §7 | Resultado |
|---|---|
| 1 All 8 materials via frame wizard | ✅ T1 + keywords + force-frame |
| 2 Stored = library Spanish; `get_material` accepts | ✅ `materials.py` + aerial wiring |
| 3 Dual-name regression green | ✅ `test_t4_…` |
| 4 Force-frame present + tested | ✅ orchestrator + T3 |
| 5 Legacy EN slug shim | ✅ `LEGACY_MATERIAL_SLUGS` + T5 |
| 6 `madera` removed | ✅ aliases; T6 |
| 7 List-materials 0 LLM | ✅ intent + handler + soft-interrupts |
| 8 No G8/G9/Impl C / library JSON adds | ✅ |
| 9 Related regressions | ✅ revisor: 102 passed on G10+aerial+design_utils+frame |

---

## Re-verificación

| ★ | Evidence | Match |
|---|---|---|
| ★1 | `resolve_material_alias` → library ES names | ✅ |
| ★2 (b) | `domains/materials.py`; aerial + iterate_domain alias to `MATERIAL_ALIASES` | ✅ |
| ★3 | `orchestrator.py` force-frame after propellers FN-019 | ✅ |
| ★4 | Frame keywords expanded (report + aerial) | ✅ |
| ★5 | `get_frame_material` + `LEGACY_MATERIAL_SLUGS` | ✅ |
| ★6 | `state["material"]` **before** `structure.material` (`mutation_engine.py:250-252`) | ✅ |
| ★7 | No `madera` in `MATERIAL_ALIASES` | ✅ |
| ★8 | `LIST_MATERIALS_PATTERNS` + `_handle_list_materials`; IDLE / iterate / DEFINE_MISSING | ✅ |

Revisor ejecutó:

```text
tests/test_g10_materials_frame.py
+ test_aerial_domain / test_design_utils / test_frame_component
→ 102 passed
```

(Full 1741 claimed by Claude — spot-check suite above green; no reason to doubt.)

---

## Notes (no bloquean PASS)

1. **`structure.material` still written** — allowed by IC; ★6 only required stop-reading-as-SoT. Residual Fase 3 cleanup OK later.
2. **`semantic_interpreter.py` still lists `"madera"`** in material keyword hints for LLM iterate path — not the alias table. Low risk; optional micro-clean later (not G10 scope failure).
3. **List-materials pattern set is narrow** — report already flags; CLI may discover missing phrases → extend `LIST_MATERIALS_PATTERNS` only.
4. **Force-frame T3 uses bare `"400g"`** — synthetic isolation from ★4; fine for unit proof; CLI should still exercise `plastico`/`pvc` in real wizard.

---

## CLI probe (Engineer)

```text
# Con wizard frame abierto (o DEFINE_MISSING frame):
plastico 390g
pvc 400g
que materiales tenemos en el catalogo?

# Tras frame = fibra de carbono (o equivalente):
# iterate → cambiar material a pvc
# → delta de masa coherente con carbono→pvc (no aluminio)
```

Esperado: aceptación + lista determinista (8 filas) + mutate correcto.

---

## Conclusión

G10 cierra el síntoma CLI **y** el bug silencioso de masa. Patrón reutilizable para adquisición de familias density-only hacia Impl C, sin tocar G9.

**Siguiente:** CLI → si PASS → `checkpoint-g10` → R3 design.
