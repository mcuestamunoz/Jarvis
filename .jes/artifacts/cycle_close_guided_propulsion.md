# Cycle close — Guided Propulsion Acquisition (FN-010 / FN-008 / FN-009)

**Date:** 2026-08-08  
**Status:** CLOSED  
**Baseline tests at close:** 1449 passed (suite reported; smoke E2E OK for the three cuts together)  
**Review:** PASS

## Intent

Cerrar tres field notes de create/propulsión guiada:

1. No perder constraints de misión cuando `restrictions` es placeholder.
2. No exigir parámetros internos (`structure_mass_factor` / `safety_factor`) al crear en nivel detallado.
3. Conectar empuje pendiente a assisted acquisition / catálogo sin inventar física.

## Cuts

### Corte 1 — FN-010

- `parsed_constraints` deriva de `restrictions` y, por clave ausente, del `objective` (mismas regex).
- Restricción explícita siempre gana.
- Caso field note: `autonomy_min == 40.0` persistido tras reload.

### Corte 2 — FN-008

- Al elegir conceptual/detallado se aplican `0.6` y `1.2` y se salta a la rama de dominio.
- Resumen humanizado; steps 5/6 eliminados; sin “Enter para default”.
- Hipótesis editables después vía iterate.

### Corte 3 — FN-009

- `per_motor_max_thrust_n` en assisted acquisition.
- Pick de catálogo resuelve thrust + potencia de forma coherente; preserva `motor_count`; un recalc.
- Gap honesto sin inventar SKU.
- IDLE prioriza propulsión sobre energía.
- Continuity marca requisito provisional hasta declarar batería.
- Follow-up: copy N vs W en `_offer_catalog_help`.

## Explicitly out of scope / deferred

- Copy debt no bloqueante en `_answer_assisted_motor` (errores aún hablan de W con pending thrust).
- Extender el patrón a batería/hélices.
- Refactor / higiene grande de `orchestrator.py`.

## Verdict

Guided Propulsion Acquisition **closed**. Los tres cortes están hechos, revisados PASS y coherentes entre sí. Deuda restante es copy en paths de error, no comportamiento físico.
