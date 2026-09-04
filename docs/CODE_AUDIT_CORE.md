# Jarvis — Auditoría de código del núcleo (3 septiembre 2026)

> **Petición:** directa del usuario ("los archivos core me preocupan, haz un informe muy muy detallado"), fuera del ciclo normal de Investigation Contract / Implementation Contract. No se editó ningún archivo de `src/` durante esta auditoría.
> **Autoritativo para:** patrones transversales, complejidad/arquitectura, métricas cuantitativas y recomendaciones de refactor. Los defectos puntuales fabricados a partir de esta auditoría están numerados como **Bug 80+** en [`docs/BUGS.md`](BUGS.md) (Fase O) — este documento es la fuente para todo lo que no encaja en el formato de un bug individual.
> **Cola:** [`docs/IMPLEMENTATION_TASKS.md`](IMPLEMENTATION_TASKS.md) — review de esta auditoría añadida en cola/prioridad.

## Método

Cinco investigaciones en paralelo, una por subsistema, cada una con lectura **completa** (no fragmentos) de sus archivos asignados, con instrucción explícita de verificar cada hipótesis con `grep`/tests antes de reportarla y de señalar cuando algo sospechoso resultaba intencional. Tras recibir los cinco informes, se verificaron personalmente en ejecución los 5 hallazgos de mayor impacto potencial — incluyendo reproducir el crash de división por cero con la secuencia de conversación real (Bug 80) y confirmar que no deja corrupción de estado persistente, un matiz que el sub-agente correspondiente no había capturado.

Alcance: **~24.017 líneas**, 47 archivos — todo `src/jarvis/core/` (19.817 líneas) más `actions/`, `adapters/cli/main.py`, `knowledge/library.py`, `domains/`, `schemas/` (~4.200 líneas).

Los hallazgos de severidad media/baja no llevaron verificación de ejecución independiente más allá de la que cada investigación ya documentó con grep — están bien fundamentados, no probados dos veces.

## Resumen ejecutivo

El tamaño de `orchestrator.py` (4.799 líneas) es un problema real, pero **no es el hallazgo más grave**. Los dos más graves:

1. **Crash 100% reproducible con input de usuario plausible** — "modifica el número de motores" → "0" → confirmar → `ZeroDivisionError` sin capturar, propagada hasta `orchestrator.handle_user_text`. Ver Bug 80.
2. **Fabricación de datos físicos desde texto no relacionado** — `resolve_material_alias("el frame absorbe bien las vibraciones")` declara `material="plástico"` (vía `"abs"` dentro de "absorbe"), con `confidence=0.9, source="declared"`. Ver Bug 81.

Distribución de severidad de los 41 hallazgos: **1 crítico · 14 altos · 17 medios · 9 bajos**.

Cuatro patrones se repiten en subsistemas auditados por investigaciones distintas, sin que unas supieran de las otras — eso hace más creíble que sean patrones reales del proyecto y no ruido de un solo lector.

## Patrones transversales

### A — "Doble verdad": el mirror físico se desincroniza del componente canónico

La misma familia de bug que motivó el hotfix N1 de Structure A (`set_frame_material` borraba el override de masa al actualizar solo la clase, corregido 2026-09-03). Esa corrección cerró **un** punto de entrada — quedan al menos cuatro más, en rutas que ese hotfix no toca:

| Instancia | Ubicación | Nota |
|---|---|---|
| Bug 82 | `actions/iterate.py:509` | Mutaciones de volumen/payload escriben `structure_mass_override_kg` directo, sin pasar por `set_frame_material` |
| Bug 83 | `system_architecture_catalog.py:241-256` | **Verificado.** `structure_mass_override_kg` no está en `COMPONENT_MIRRORED_PARAMS` — divergencia vía DSE |
| Bug 84 | `catalog_bind.py:234-311` | **Verificado.** `invalidate_diverged_catalog_refs` sin rama para `propellers` (ni `frame`) |
| Bug 85 | `component_writers.py:539-544` | `apply_components_delta` nunca lee `size_class_inch` del delta de frame |
| Bug 86 | `orchestrator.py:2324,2354,2381,2406` | 4× `except Exception: pass` puede perder el recálculo tras guardar el componente, sin avisar |

### B — Matching de texto por substring, sin límites de palabra (`\b`)

| Instancia | Ubicación | Nota |
|---|---|---|
| Bug 81 | `domains/materials.py:57-69` | **Verificado en ejecución.** Alias de 2-3 letras (`cf`, `alu`, `abs`) sin `\b` |
| Bug 87 | `domains/registry_selector.py:52-58` | `"par"` matchea dentro de "parámetros" — enruta mal el dominio del vehículo |
| Bug 88 | `adapters/cli/main.py:738-753` | `"uno"` matchea dentro de "ninguno" — selecciona proyecto #1 y toca disco |
| Bug 89 | `battery_catalog_assist.py:104-109` | Matching de SKU por substring puro, sin garantía estructural |

### C — Excepciones silenciadas de espectro total

| Instancia | Ubicación | Nota |
|---|---|---|
| Bug 86 | `orchestrator.py:2324,2354,2381,2406` | Ver patrón A |
| Bug 90 | `design_explorer.py:619-624, 648-651, 675-680` | 3 bucles de evaluación DSE descartan cualquier excepción como "candidato no viable" |

### D — Lógica duplicada sin fuente única

| Instancia | Ubicación | Nota |
|---|---|---|
| — | `orchestrator.py` — `_block_progress_status` | Ya conocido por el equipo (duplicado también en `engineering_readiness.py`) — no re-listado aquí |
| Bug 91 | `orchestrator.py` — motors/propellers/battery | Patrón "catalog help-choose/pick" triplicado casi literalmente |
| Bug 92 | `iterate_interactive_session.py:295-338` vs `424-452` | Extracción de "material+gramos+pulgadas" duplicada entre las dos ramas Gap-1 — motivo directo de que el hotfix N1 tuviera que tocar dos sitios |
| Bug 93 | `intent_resolver.py` / `semantic_interpreter.py` / `domains/aerial.py` | Al menos 3 tablas de sinónimos de material mantenidas a mano por separado |
| Bug 94 | `orchestrator.py` — 19 sitios | `try: load_active_project() except FileNotFoundError` reimplementado inline cuando existe `_safe_active_project()` en la misma clase; ≥5 son copias literales |

## `orchestrator.py` — foto cuantitativa

| Métrica | Valor |
|---|---|
| Líneas | 4.799 |
| Métodos | 86 |
| Método más grande | `_handle_user_text_inner`, 852-1458 (**606 líneas**, **74 ramas `if`/`elif`** de primer nivel, **2 recursiones** sin guarda de profundidad, líneas 1009 y 1194) |
| Otros métodos grandes | `_handle_component_description` 430 líneas · `build_startup_context` 346 líneas · `_handle_apply_exploration` 330 líneas · `_handle_explore` 229 líneas |
| Tags de parche en comentarios | **61** identificadores distintos (`FN-001`…`FN-026`, `Bug 7`…`Bug 79`, `G10`…`G26`, `★1`…`★4`, `R3a/R3b`) |
| Imports internos de `core/` | 17 en cabecera + ~15 adicionales dentro de funciones |

**Veredicto sobre el tamaño:** debería dividirse, no por dogma sino porque el tamaño ya produce el síntoma que motivó la pregunta original — un método de 606 líneas con recursión sin proteger y 4 bloques de manejo de error silencioso repetidos, sin consolidar en 61 parches sucesivos. Cualquier división requiere **ratificación explícita del Engineer** (`CLAUDE.md` lo exige para refactors estructurales grandes) — este documento propone la forma, no ejecuta nada:

- `wizard_dispatch` — sub-dispatchers por modo (`_dispatch_idle`, `_dispatch_iterate_interactive`, `_dispatch_define_missing`), cada uno mucho más corto y testeable en aislamiento.
- `component_acquisition` — `_handle_component_description`, `_apply_inferred_component_spec`, el trío catalog-pick colapsado en un helper genérico.
- `architecture_progress` — `_block_progress_status` y familia; ya vive casi aparte conceptualmente (tiene una copia paralela en `engineering_readiness.py`).
- `explore_dispatch` — `_handle_explore` + `_handle_apply_exploration` (559 líneas combinadas).
- El resto queda como fachada delgada: `handle`/`handle_user_text` delegando a los módulos anteriores.

## Archivos más grandes de `src/jarvis/core/`

| Archivo | Líneas | Nota |
|---|---:|---|
| `orchestrator.py` | 4.799 | ver arriba |
| `iterate_interactive_session.py` | 1.774 | `answer()`: 405 líneas de dispatch en cascada, ~15 comentarios "Bug N" incrustados |
| `engineering_readiness.py` | 1.284 | bien testeado, buen historial de regresión |
| `param_definition_session.py` | 1.173 | `answer()`: ~180 líneas, mismo patrón que iterate |
| `project_closure.py` | 764 | — |
| `design_explorer.py` | 706 | subsistema más limpio de los cinco auditados |
| `intent_resolver.py` | 686 | — |
| `reasoning_layer.py` | 628 | lee un campo eliminado desde Fase 3 (Bug 95) |
| `motor_catalog_assist.py` | 624 | — |
| `component_writers.py` | 561 | writers canónicos — foco del hotfix N1 y de varios bugs de esta fase |
| `parameter_requirements.py` | 535 | fuente única de verdad de requisitos |
| `project_continuity.py` | 501 | único módulo con ranking documentado explícitamente en su propio docstring |

## Subsistemas auditados y qué se encontró en cada uno

| Subsistema | Archivos | Líneas | Hallazgo principal |
|---|---|---:|---|
| `orchestrator.py` | 1 | 4.799 | Dispatcher central de 606 líneas / 74 ramas; 4× `except` silencioso |
| Sesiones/wizards | `iterate_interactive_session.py`, `mutation_engine.py`, `actions/iterate.py`, `param_definition_session.py`, `system_definition_session.py`, `interactive_session.py`, `iterate_domain.py` | 4.923 | Masa de frame divergente en mutaciones físicas (patrón A); sweep ESTIMATIVO perdido en 7+ rutas |
| Readiness/closure/writers | `engineering_readiness.py`, `project_closure.py`, `project_continuity.py`, `calculation_engine.py`, `electrical_compatibility.py`, `system_architecture_catalog.py`, `component_writers.py`, `component_sync.py`, `catalog_bind.py` | 4.649 | `ZeroDivisionError` reproducido (Bug 80); mirrored-param y divergencia de catálogo sin cubrir para frame/hélices |
| Catálogo/DSE/inferencia | `design_explorer.py`, `motor_catalog_assist.py`, `battery_catalog_assist.py`, `propeller_catalog_assist.py`, `component_resolver.py`, `component_inference.py`, `component_rules.py`, `knowledge/library.py`, `acquisition_target.py`, `acquisition_brief.py` | 3.548 | Subsistema más limpio; único bug crítico encontrado ya es código muerto hoy |
| Intención/razonamiento/CLI | `intent_resolver.py`, `semantic_interpreter.py`, `reasoning_layer.py`, `goal_planner.py`, `parameter_requirements.py`, `adapters/cli/main.py`, `domains/aerial.py`, `domains/ground.py`, `domains/materials.py`, `domains/registry_selector.py` | 5.128 | El bug crítico del informe (Bug 81) y la mayoría de instancias del patrón B |

## Recomendaciones priorizadas

Ninguna se implementa sin ratificación explícita — son candidatas a Investigation Contract / Implementation Contract bajo el mismo protocolo que ya usa el proyecto.

1. **Blindar `calculate_force_per_actuator` contra división por cero** (Bug 80) — la corrección más barata y de mayor impacto: un guard de `actuator_count ≥ 1` en `tools/mechanics.py:50`, o validación en el punto de entrada del wizard numérico.
2. **Acotar `resolve_material_alias` con límites de palabra** (Bug 81) — añadir `\b` a los alias cortos en `domains/materials.py`; mismo arreglo aplicable de una vez a las otras 3 instancias del patrón B.
3. **Extender el "Mirrored Param Contract" a `structure_mass_override_kg` y a las hélices** (Bugs 83, 84) — cierra las dos instancias más peligrosas del patrón A con el mismo aparato que ya existe y funciona para motor/batería.
4. **Investigación dedicada: por qué el sweep ESTIMATIVO se pierde en 7+ rutas de recálculo** — incluye la ruta más transitada de la app (`apply_and_recalculate` del wizard de parámetros) y la creación de proyecto. Misma categoría de honestidad de producto que Option A y Structure A ya cerraron en otros flujos.
5. **Dividir `orchestrator.py`** — como investigación de arquitectura, no como refactor exprés (ver forma propuesta arriba).
6. **Pasada dedicada al patrón B** — grep sistemático de `" in normalized"` / `" in lower"` en `core/` y `domains/`; 4 instancias confirmadas sugieren que hay más sin encontrar.

## Qué resultó intencional (verificado, no reportado como bug)

- `_apply_delta` no filtra `battery_capacity_wh_factor`/`motor_power_w_factor` pese a que `COMPONENT_MIRRORED_PARAMS` los lista sin sufijo — confirmado intencional vía `tests/test_battery_component.py::test_criterio_dse_gap_documented`.
- `resolve_operating_point_at_thrust` (`library.py:899-990`) — interpolación acotada revisada a fondo, sin forma de disparar `ZeroDivisionError` ni interpolación incorrecta. Código de alta calidad.
- Resolución "primero que gana" en `component_resolver.py` — parece frágil pero está marcada explícitamente como decisión deliberada, y Python garantiza orden de inserción en dicts.
- Zona sin señal entre `low_margin` (&lt;1.2) y `high_margin` (≥1.5) en `reasoning_layer.py` — diseño intencional.
- `ANALYZE_HELP_PATTERNS`/"ayúdame a elegir" ya tiene mitigación documentada en `orchestrator.py:1080` — listado como fragilidad de mantenimiento en Bug 96, no como bug activo.
