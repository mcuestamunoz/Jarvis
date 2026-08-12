# Jarvis — Roadmap operativo

---

## 🔴 PRIORIDAD ACTUAL

> Fuente única de foco. No leer más allá de esta sección para saber qué hacer hoy.

> **H1–H4 cerrados (`v0.2.0` / `checkpoint-fn026-h4`). Mapa: 59 · 58🟢 · 0🔴 · 1🟡 (C-081).**  
> **PRIORIDAD AHORA:** Catalog Foundation **Impl A PASS** — commit cuando Engineer pida; luego IC **Impl B (Bind)**.  
> Review: [`.jes/artifacts/implementation_review_catalog_foundation_v1.md`](../.jes/artifacts/implementation_review_catalog_foundation_v1.md)  
> Design: [`PHYSICAL_COMPONENT_CATALOG_V1.md`](PHYSICAL_COMPONENT_CATALOG_V1.md) · Suite: **1616 passed**  
> **No Impl B sin contrato nuevo.** H5 / material micro-fix / Create→BOM siguen aparte.

### ✅ COMPLETADO — Catalog Foundation Impl A

> Contrato: [`.jes/artifacts/implementation_contract_catalog_foundation_v1.md`](../.jes/artifacts/implementation_contract_catalog_foundation_v1.md)  
> Informe / review: `.jes/artifacts/implementation_report_catalog_foundation_v1.md` · `implementation_review_catalog_foundation_v1.md` — **PASS**

**Entregó:** `BatterySpec`/`PropellerSpec` + loaders en `ComponentLibrary`; seeds `library/baterias` (10 LiPo) + `library/helices` (14); `CatalogRef` + `ComponentSpec.catalog_ref=None` (sin writers); `match_motor_propeller`; 25 tests; **1616** suite. Motores JSON / calc / DSE / Continuity / Bind **no** tocados.

**Siguiente:** commit Foundation (si Engineer pide) → IC Impl B (pick→`catalog_ref`, discard fix, masa SKU-bound).

### ✅ COMPLETADO — Catalog v1 Design CLOSED

> [`docs/PHYSICAL_COMPONENT_CATALOG_V1.md`](PHYSICAL_COMPONENT_CATALOG_V1.md) — Engineer 1A–5A + split A/B/C/D.

### ✅ COMPLETADO — Catalog v1 AUDIT (visión + conexiones)

> Contrato: [`.jes/artifacts/implementation_contract_catalog_v1_audit.md`](../.jes/artifacts/implementation_contract_catalog_v1_audit.md)  
> Informe: [`.jes/artifacts/catalog_v1_connection_audit.md`](../.jes/artifacts/catalog_v1_connection_audit.md)  
> Review: [`.jes/artifacts/implementation_review_catalog_v1_audit.md`](../.jes/artifacts/implementation_review_catalog_v1_audit.md) — PASS WITH NOTES  

**Hallazgo central:** pick de catálogo no persiste identidad SKU (`ComponentSpec` sin `catalog_ref`). Masa motor inerte; batería = heurística 150 Wh/kg. B antes de C es dependencia dura. Bug material ES/EN independiente.

### ✅ COMPLETADO — FN-026: H4 Plan lever → Iterate preseed (C-043)

> Contrato: [`.jes/artifacts/implementation_contract_fn026_h4_lever_iterate.md`](../.jes/artifacts/implementation_contract_fn026_h4_lever_iterate.md)  
> Diseño: mismo `HandoffContext.levers` / `iterate_capability` ([`HANDOFF_CONTEXT_DESIGN.md`](system_map/HANDOFF_CONTEXT_DESIGN.md))  
> Informe: [`.jes/artifacts/implementation_report_fn026.md`](../.jes/artifacts/implementation_report_fn026.md)

**Cierra:** C-043 🔴→🟢 — último RED del mapa. Nombrar un lever del plan activo (`"incrementa safety_factor"` tras `"ayudame a mejorar la estabilidad"`) ahora preseed `iteration_draft.variable` antes de que se abra el wizard — salta el paso 1 ("¿Qué quieres modificar?"). Nuevo helper puro `core/handoff_matching.py::match_plan_lever` (busca cada lever completo y sus tokens separados por `/` contra el texto del usuario, aceptando solo candidatos válidos vía `iterate_domain._is_valid_variable`; resuelve con la misma cadena `normalize_alias`/`_VARIABLE_NORMALIZATION`/`_fuzzy_normalize_variable` que ya usa `_apply_answer` en el paso 1 — sin vocabulario paralelo). Llamado desde `orchestrator._preseed_variable_from_handoff`, justo antes de despachar un `intent == "iterate"` — guardado por `handoff.project_id == project_state.project_id` y `handoff.iterate_capability == "active"`; nunca lee ni toca `dse_capability`.

**Plan:**
1. [x] `core/handoff_matching.py::match_plan_lever(user_input, handoff_context) -> str | None` — helper puro, reutiliza `iterate_domain`/`parameter_requirements`
2. [x] `orchestrator._preseed_variable_from_handoff` — no-op honesto sin contexto activo, proyecto distinto, o sin match; nunca sobrescribe un `variable` ya presente en `parameters`
3. [x] Wired en el dispatch de `intent in {"create_project","iterate","calculate","simulate"}` (solo rama `iterate`), antes de `self.handle(...)`
4. [x] Matching de lever compuesto (`"per_motor_max_thrust_n / motors"`) — token válido (`motors`) preseed, token derivado/no-settable (`total_power_w`) se descarta honestamente
5. [x] Tests: `test_fn026_lever_iterate_preseed.py` (T1–T8, 12 tests) + regresión FN-025 actualizada (`test_iterate_lever_preseed_now_implemented`, invierte el pin pre-FN-026) + regresión FN-022/023/024/025 (350 tests) + suite completa verde (1591 = 1579 + 12)
6. [x] Mapa actualizado: `CONNECTIONS.md` (C-043 🟢, rollup 58🟢/0🔴/1🟡), `AUTHORITY.md`, `FLOWS.md` (FLOW-004), `MISMATCHES.md` (H4 → implementado, H1–H4 todos cerrados), `DIAGRAMS.md`, canvas, `JARVIS_SYSTEM_MAP.md`, `01_runtime`/`04_engineering`/`05_iteration` — consistencia verificada programáticamente (0 diferencia simétrica de IDs entre `CONNECTIONS.md`/`DIAGRAMS.md`/canvas)

**No en este corte (confirmado, sin tocar):** H5/C-081, Create→BOM, refactor de dual dispatch. Polish opcional del contrato (marcar lever "reconciliado" tras aplicar la mutación) deliberadamente omitido — no requerido para cerrar C-043.

**Cola (histórica):** cerrada; siguiente decisión es del Engineer (H5 vs Create→BOM).

### ✅ COMPLETADO — Layer Connection Map (diseño) → System Map → H1–H4

> Artefacto histórico: [`.jes/artifacts/design_layer_connection_map.md`](../.jes/artifacts/design_layer_connection_map.md) (CLOSED / SUPERSEDED).  
> Autoridad viva: [`docs/system_map/`](system_map/README.md) · Handoff: [`HANDOFF_CONTEXT_DESIGN.md`](system_map/HANDOFF_CONTEXT_DESIGN.md)

**Entregó este plan de diseño:**
1. [x] Mapa de capas + fallos A–E + contratos H1–H5
2. [x] Cola reordenada: handoffs **antes** de Create→BOM
3. [x] FN-024 (H1+H2) acotado → contrato + delivery; luego FN-025/026

**Resultado:** A/B/C cerrados (FN-024/025/026). D = H5/C-081 deferred. Create→BOM sigue después del catálogo físico (ver PRIORIDAD ACTUAL).

### ✅ COMPLETADO — FN-025: H3 Help + Goal → Engineering Intent (C-025 / C-044)

> Contrato: [`.jes/artifacts/implementation_contract_fn025_h3_help_goal.md`](../.jes/artifacts/implementation_contract_fn025_h3_help_goal.md)  
> Diseño: mismo `HandoffContext` / C-105 ([`HANDOFF_CONTEXT_DESIGN.md`](system_map/HANDOFF_CONTEXT_DESIGN.md))  
> Informe / review: `.jes/artifacts/*fn025*` · Commit: `1442d44` · Tag: `checkpoint-fn025-h3`

**Cierra:** C-025 🔴→🟢 + C-044 🔴→🟢 (misma raíz, un solo fix). `"ayudame a mejorar la estabilidad"` → `_handle_engineering_intent` (mismo plan, mismo `handoff_context` vía C-105), 0 LLM. `intent_resolver.ANALYZE_PATTERNS` dividido en `ANALYZE_VERB_PATTERNS`/`ANALYZE_HELP_PATTERNS` (misma unión, sin cambio de comportamiento de `resolve_intent`); el gate vive en `orchestrator.py` (Opción A del contrato, no en `intent_resolver.py`).

**Plan:**
1. [x] `ANALYZE_PATTERNS` dividido en dos grupos nombrados (`intent_resolver.py`)
2. [x] Gate en `orchestrator.py`'s rama `intent == "analyze"`: si el match viene del grupo help (nunca el grupo de verbos reales) → `is_engineering_intention`; goal detectado → `_handle_engineering_intent`; sin goal → `_handle_project_status` (nunca LLM inventando un objetivo)
3. [x] FN-023 (`"ayúdame con el siguiente paso"`) intacto por construcción — GUIDANCE se comprueba antes que ANALYZE, nunca llega a esta rama
4. [x] Tests: `test_fn025_help_goal_intent.py` (T1–T8 + 2 regresiones, 10 tests) + regresión FN-005/011/013/014/015/016/020/021/022/023/024 (338 tests) + suite completa verde
5. [x] Mapa actualizado: `CONNECTIONS.md` (C-025/C-044 🟢, solo C-043 queda rojo), `AUTHORITY.md`, `FLOWS.md` (FLOW-002b), `MISMATCHES.md` (H3 implementado), `DIAGRAMS.md`, canvas, `01_runtime`/`02_intent`/`04_engineering`

**No en este corte (confirmado, sin tocar):** H4/C-043 (cerrado después en FN-026), H5/C-081, Create→BOM, refactor de dual dispatch.

**Cola (histórica):** cerrada en `checkpoint-fn025-h3`; siguiente fue FN-026 (ver arriba).

### ✅ COMPLETADO — FN-024: H1+H2 Handoff Context → Plan/DSE (C-042)

> Contrato: [`.jes/artifacts/implementation_contract_fn024_h1_h2_handoff_dse.md`](../.jes/artifacts/implementation_contract_fn024_h1_h2_handoff_dse.md)  
> Diseño: [`docs/system_map/HANDOFF_CONTEXT_DESIGN.md`](system_map/HANDOFF_CONTEXT_DESIGN.md) — **§5 CLOSED** (Hybrid Operation-Scoped Context)  
> Informe: [`.jes/artifacts/implementation_report_fn024.md`](../.jes/artifacts/implementation_report_fn024.md)  
> Commit checkpoint: `ff550f3`.

**Cierra:** C-042 🔴→🟢 + CTA honesty (H2, como consecuencia de H1, no un cambio de texto aparte). Nuevo `schemas.action_schema.HandoffContext` (runtime-only, nunca persistido, con guarda `project_id` en cada lectura) creado/reemplazado en cada `_handle_engineering_intent` exitoso; `"explora opciones"` a secas hace bind vía el contexto activo; un bind+explore exitoso consume **solo** la capability DSE — `goal_key`/`levers`/`iterate_capability` quedan intactos para un futuro H4.

**Plan:**
1. [x] `HandoffContext` en `schemas/action_schema.py` (campos mínimos del contrato) + campo `handoff_context` en `InteractiveSessionState`, excluido de `_PERSISTED_SESSION_FIELDS`
2. [x] `_handle_engineering_intent` crea/reemplaza el contexto (C-105); CTA sin cambios de texto (ya honesto por construcción)
3. [x] `_handle_explore` hace bind cuando `goal_key is None` (C-106) — guardado por `project_id` + `dse_capability=="active"`; consume solo la capability DSE tras un explore exitoso
4. [x] Segundo `"explora opciones"` tras consumir → mensaje determinista (0 LLM), no re-bind silencioso
5. [x] `"optimiza para X"` explícito sin cambios — contexto intacto (opción "más simple" del contrato §4.2)
6. [x] Tests: `test_fn024_handoff_context_dse.py` (T1–T9 + regresión FN-020/021/022/023, 11 tests) + suite completa verde
7. [x] Mapa actualizado: `CONNECTIONS.md` (57→59, C-042 🟢, C-105/C-106 nuevos), `DIAGRAMS.md`, canvas, `FLOWS.md` FLOW-003, `MISMATCHES.md` H1/H2 → implementado, `04_engineering`/`09_state` subsystem maps

**No en este corte (confirmado, sin tocar):** H3 (C-025/C-044, cerrado en FN-025), H4 (C-043, cerrado en FN-026 — `levers`/`iterate_capability` ya estaban listos para su consumidor), H5 (C-081, sigue deferred), Create→BOM, refactor de dual dispatch.

**Cola (histórica — ver FN-025 arriba):** checkpoint `ff550f3` cerrado; siguiente es FN-025.

### ✅ SYS-MAP-003 — verificación del mapa + inventario de higiene (documentación, sin cambios de código)

> Ejecutado en paralelo al trabajo de FN-024/diseño anterior. Re-verifica `docs/system_map/**` contra código actual (A1–A20, todos CONFIRMED) y audita `src/jarvis/` en busca de código muerto/residual/duplicado (16 hallazgos `HYG-xxx`, solo informe, sin limpieza).

**Entregables:**
- [`.jes/artifacts/implementation_report_sys_map_003.md`](../.jes/artifacts/implementation_report_sys_map_003.md) — resumen ejecutivo
- [`.jes/artifacts/sys_map_003_verification_matrix.md`](../.jes/artifacts/sys_map_003_verification_matrix.md) — A1–A22 completo
- [`.jes/artifacts/sys_map_003_hygiene_inventory.md`](../.jes/artifacts/sys_map_003_hygiene_inventory.md) — catálogo `HYG-001`…`HYG-016`, top ranking

**Correcciones al mapa (2, encontradas durante la re-verificación, ya aplicadas en `docs/system_map/**`):** `semantic_intent_adapter.py` estaba mal descrito en `10_llm/LLM_MAP.md` (M-003); `tools/materials.py`/`tools/math_utils.py`/`simulation/flight_model.py`/`simulation/energy_model.py` estaban listados como activos en SYS-MAP-002 pero son archivos vacíos sin ningún import (M-004) — 5 archivos vacíos más (`knowledge/loader.py`, `knowledge/parser.py`, `knowledge/retriever.py`, `utils/helpers.py`, `utils/validators.py`) nunca se habían reclamado como usados, catalogados en el inventario de higiene.

**No desbloquea FN-024** ni ningún RED (`C-042`/`C-025`/`C-044`/`C-043`). Sin cambios en `src/`. Suite completa: **1558 passed**, sin cambios.

**Higiene de seguimiento (opcional, no urgente):** lote mecánico sugerido — HYG-001 + HYG-003 + HYG-008…016 — ver inventario.

### ✅ HANDOFF CONTEXT — diseño (lifecycle cerrado)

> Hybrid Operation-Scoped Context aceptado 2026-08-10. Ver Decision log en el design doc.

### ✅ SYS-MAP-002 — System Map navegable (publicado)

> Árbol: [`docs/system_map/README.md`](system_map/README.md). **57** C-xxx canónicos (FN-024 añadirá C-105/C-106).

**Acquisition Fluency / FN-022 / FN-023:** cerradas.

---

### ✅ COMPLETADO — Sync docs: `ARCHITECTURE.md` ↔ stack FN-014…023

> El diagrama de flujo IDLE, el orden de `handle_user_text`, `goal_planner`, `project_status`/Continuity y DEFINE_MISSING no reflejaban Acquisition Fluency / Engineering Intent / next-step help.

**Plan:**
1. [x] Actualizar flujo conceptual + orden de despacho en `docs/ARCHITECTURE.md`
2. [x] Documentar módulos `acquisition_*`, Continuity/coherence, FN-022/023
3. [x] Alinear “cuándo NO interviene el LLM” y bullets de estado actual
4. [x] Sin Create→BOM, sin Step D, sin cambios de código

**Siguiente (histórico):** Create→BOM — **reordenado**; ver Layer Connection Map arriba.

### ✅ COMPLETADO — FN-023: ayuda genérica de "siguiente paso" → Continuity/`project_status`

> "ayúdame con el siguiente paso" resolvía `intent="analyze"` (`\bayudame\b` de `ANALYZE_PATTERNS` gana antes de que `_looks_like_status_query` llegue a ejecutarse) → LLM → podía inventar un gap no relacionado (p. ej. `battery_capacity_wh`) aunque Continuity ya conocía el target real pendiente.

**Plan:**
1. [x] Tres patrones nuevos en `GUIDANCE_PATTERNS` (`intent_resolver.py`, chequeados antes que `ANALYZE_PATTERNS`) — "ayúdame con el siguiente paso"/"ayúdame con el siguiente"/"ayúdame a seguir" → `intent="project_status"`
2. [x] **Sin cambios en `orchestrator.py`** — el despacho `if intent == "project_status"` (cola IDLE) y el soft-interrupt ya existente dentro de `DEFINE_MISSING_PARAMETERS` (Bug 56) ya reutilizan `_handle_project_status()`/Continuity automáticamente en cuanto `resolve_intent` devuelve el valor correcto
3. [x] Genérico: probado con dos gaps reales distintos (propulsión/hélices vs estructura/frame) — cada uno refleja su propio `next_architecture_label`/`next_useful_step`, nunca batería inventada
4. [x] Tests: `test_fn023_next_step_help.py` (8) + regresión FN-005/011/013/014/015/016/017/018/019/020/021/022 + orchestrator/main_cli (185) verdes

**Siguiente:** Create→BOM handoff. Consistencia plan-first vs auto-DSE (residual de FN-022, opcional). Step D sigue bloqueado.

### ✅ COMPLETADO — FN-022: Engineering Intent → plan de estrategia determinista

> Una intención de ingeniería sin valor concreto ("Aumentar el empuje", "más thrust") resolvía `intent="iterate"` (verbo `aumentar`/`subir` capturado antes de cualquier capa de goal) y abría el wizard de iterate, o caía al LLM — en vez del plan estratégico determinista que ya vive en `goal_planner.GOAL_STRATEGIES`/`format_goal_plan`.

**Plan:**
1. [x] `goal_planner._GOAL_KEYWORDS` ampliado para **los 4 goals** (no solo empuje) — payload/autonomía/masa también rellenados; empuje/thrust/margen añadidos bajo `mejorar_estabilidad` (mapping primario documentado: esa goal ya lidera con la palanca de thrust/margen)
2. [x] Nuevo `goal_planner.is_engineering_intention(text) -> goal_key | None` — `detect_goal` + guarda conservadora `looks_like_numeric_mutate` (cualquier dígito ⇒ deja el turno a iterate)
3. [x] Nueva puerta IDLE en `orchestrator.py`: `intent in ("iterate", "unknown")` con goal detectado → `_handle_engineering_intent(goal_key)` (reutiliza `format_goal_plan` + el mismo `sim_context` que ya usa `_handle_analyze`, 0 LLM), insertada justo antes del despacho de iterate existente — todas las rutas más específicas (`project_status`/`analyze`/`define_params`/`dismiss_suggestion`/`explore_design_space`/`apply_exploration_result`) quedan intactas
4. [x] Tests: `test_fn022_engineering_intent.py` (9) + `test_goal_planner.py` (8 nuevos) + regresión FN-011..021/orchestrator/iterate/reasoning_layer (283) verdes
5. [x] **Ajuste dentro de este mismo corte**: una aserción propia de FN-021 (`"Aumentar el empuje"` → `iterate_interactive`) se actualizó para aceptar el resultado ahora mejor (`engineering_intent`) — la propiedad que FN-021 realmente protege (sin component prompt obsoleto) se mantiene intacta

**Siguiente:** ayuda genérica al siguiente paso → Continuity, Create→BOM handoff. Step D sigue bloqueado.

### ✅ COMPLETADO — FN-021: higiene de sesión — arquitectura completa vuelve a IDLE

> Al completar adquisición, cuando `_next_pending_block()` es `None` (nada más que adquirir, para **cualquier** bloque), `_set_pending_next_block()` hacía `return` sin más — dejando `mode=DEFINE_MISSING_PARAMETERS` con `pending_missing_params`/`param_definition_reason` obsoletos. El siguiente turno, sea cual sea su intención real, se respondía con un `component_description_prompt` residual. Sonda de campo: "Aumentar el empuje" tras arquitectura 4/4 seguía pidiendo la controladora de vuelo.

**Plan:**
1. [x] `_set_pending_next_block()`: cuando `pending is None` **y** la sesión sigue en `DEFINE_MISSING_PARAMETERS`, llama a `state_manager.clear_runtime_session()` (existente, sin inventar un segundo clearer) en vez de retornar en silencio. Gateado por modo, no por bloque/clave — genérico
2. [x] Camino de parámetros numéricos (`ParamDefinitionSession.answer()`) ya se autolimpiaba en su propia finalización — el bug era específico del camino de finalización de `_handle_component_description`, que nunca limpiaba por sí mismo
3. [x] Encadenamiento a bloque no-final sin cambios (código de esa rama no tocado)
4. [x] Tests: `test_fn021_session_hygiene.py` (4) — prueba primaria con fixture mínima de un solo bloque (genérica, sin ramas por tipo de bloque/clave) + sonda de campo (control/"Aumentar el empuje") como test adicional, no como diseño

**Siguiente:** Engineering Intent → goal_planner/DSE (contrato aparte), "ayúdame con el siguiente paso" → Continuity, Create→BOM handoff. Step D sigue bloqueado.

### ✅ COMPLETADO — FN-019: hélice sin palabra clave ("10x4.5" a secas)

> Bloqueo de campo: con `propellers` pendiente, el Brief/`COMPONENT_PROMPTS` anuncian `'10x4.5'` como ejemplo, pero sin la palabra "hélices" nunca disparaba la regla de `aerial_registry` (gateada por keyword) → `generic_component` → FN-017/018 rechazan correctamente la escritura y repiten el mismo Brief → el usuario queda en bucle con su propio ejemplo anunciado.

**Plan:**
1. [x] Nuevo `component_inference.py::infer_component_for_key(raw_name, suggested_key, ...)` — fuerza la inferencia contra la regla de una clave concreta (mismo `extract_propeller_properties`/`_propeller_completeness`, sin regex nueva), sin pasar por el match de keywords
2. [x] Refactor de `infer_component` para compartir la construcción del spec vía `_spec_from_rule` (sin duplicar)
3. [x] Wiring en `orchestrator._handle_component_description`, gateado estrictamente: solo dispara si `"propellers" in expected_keys` **y** todos los specs que encontró `infer_components` siguen siendo `generic_component` — nunca sustituye un match real de otro componente
4. [x] Tests: `test_fn019_bare_propeller_size.py` (7, A–G) + regresión FN-011/013/014/015/016/017/018/020 (100 tests) verdes

**Siguiente:** Create → BOM handoff queda para un contrato posterior. Step D sigue bloqueado hasta autorización del Engineer.

### ✅ COMPLETADO — FN-020: coherencia de completitud (arquitectura ↔ BOM ↔ Continuity)

> Dos umbrales de completitud contradictorios sobre el mismo `ComponentSpec`: `_block_progress_status` trataba cualquier `completeness` no-`low` como presente (arquitectura 4/4), mientras `build_component_bom` metía cualquier `medium` en `incomplete` sin condición — Continuity podía decir "aún tiene gaps de componentes" en el mismo turno que "Arquitectura: 4/4". Caso real: `construir-dron-6ac77f21daf5` (battery/sensors en `medium` con propiedades medibles reales).

**Plan:**
1. [x] Nuevo `project_closure.py::classify_component(key, spec, project_state) -> missing/stub/declared/defined` — clasificador único, sobre `component_presence_tier(spec) -> stub/present` (primitiva compartida) y `_measurable_and_missing_fields` (reutiliza `_MEASURABLE` + la regla motor_count-en-current_parameters existente, sin fork)
2. [x] `build_component_bom` enruta sus 4 buckets (forma sin cambios: `defined`/`incomplete`/`missing`/`declarative`) vía el clasificador — `incomplete` ahora es solo `stub` real, nunca `medium`-pero-medible (eso cae en `declarative`)
3. [x] `orchestrator._component_is_low` — wrapper delgado sobre `component_presence_tier`, comportamiento sin cambios (sigue siendo exactamente `completeness == "low"`)
4. [x] `project_continuity.py` — **sin cambios de código**: su lógica de situación/evidencia/next-step ya trataba `incomplete`/`missing` (nunca `declarative`) como señal fuerte de gap; verificado con traza real del caso `construir-dron` que el resultado ya es coherente una vez arreglada la clasificación en el BOM
5. [x] **Hallazgo corregido dentro de este mismo corte, documentado explícitamente** (no en la lista de archivos permitidos del contrato): `tests/test_project_closure_v1.py::test_bom_kv_motor_is_incomplete_not_declarative` fijaba exactamente la contradicción que este corte elimina — renombrado a `test_bom_kv_motor_is_declared_not_stub` y actualizado, mismo precedente que FN-016/017
6. [x] Tests: `test_fn020_completeness_coherence.py` (6) + `test_project_closure_v1.py`/`test_project_continuity.py`/`test_project_coherence.py`/`test_architecture_progress.py` (67) verdes

**Siguiente:** FN-019 (bare `10x4.5`) es el siguiente en cola. Create → BOM handoff y Step D siguen bloqueados/diferidos.

### ✅ COMPLETADO — FN-018: Thin Acquisition Brief + armonización de preguntas de componente

> Step C de "Acquisition Guided Engineering". C0 (obligatorio): ningún camino que pregunta por una clave de componente pendiente debe usar `_question_for_param` genérico — el único que quedaba (`_try_reprompt_active_block_declaration`, re-prompt de FN-013) ahora usa el mismo builder. C1: abrir/re-preguntar/ayudar sobre un target de definición de componente muestra un Brief corto y determinista (qué definimos / qué sabe Jarvis / por qué importa / qué necesita de mí), sin LLM, sin nueva subsistema de diálogo.

**Plan:**
1. [x] Nuevo `core/acquisition_brief.py::build_acquisition_brief(key, project_state) -> {message, question}` — blurb estático + hecho determinista de componentes hermanos ya declarados (`BLOCK_TO_COMPONENTS`) + línea "why" opcional (reutiliza `derive_physical_requirements`, sin cálculo nuevo) para `propellers`/`motors`/`battery`/`frame`; degrada a solo `COMPONENT_PROMPTS[key]` para cualquier otra clave (igual que FN-017)
2. [x] `ParamDefinitionSession.start()` — pregunta de apertura de Fase A usa el Brief cuando existe
3. [x] `_try_reprompt_active_block_declaration` (FN-013) — **fix C0**: deja de llamar `_question_for_param` sin condición para claves de componente
4. [x] `_help_current_pending_acquisition` (FN-015) — usa el mismo builder en vez del hint plano de `_COMPONENT_PROMPTS`
5. [x] `_handle_component_description`, rama `elif expected_keys` (baja completitud) — usa el builder; la rama propia de frame (material/masa) queda intacta
6. [x] Tests: `test_fn018_acquisition_brief.py` (8) + regresión FN-011/013/014/015/016/017 (61) verdes

**Siguiente:** Step D (subsistema de Guided Engineering) sigue bloqueado hasta autorización explícita del Engineer. Bare `"10x4.5"` sin keyword "hélices" sigue diferido.

### ✅ COMPLETADO — FN-017: plumbing de adquisición de componentes

> Corrige la capa de UX/routing que se apoya sobre el dispatch ya corregido (FN-011–016): `pending_missing_params` coherente en un wizard vivo, follow-up de baja completitud consciente de la clave pendiente (no siempre "material y masa"), ninguna escritura silenciosa de `generic_component`, pregunta de apertura concreta por componente, y `"declarar motores"` en IDLE (motores hechos, hélices pendiente) continúa el bloque de propulsión en vez de caer en el wizard de par de transmisión terrestre.

**Plan:**
1. [x] `ParamDefinitionSession.start()` — puebla `pending_missing_params`/`pending_missing_reason` desde la misma lista cuando `reason == MISSING_COMPONENT_DEFINITION` (aditivo, no toca otros callers de Bug54)
2. [x] `_handle_component_description` — fallback defensivo lee `pending_param_definitions` si `pending_missing_params` viniera vacío
3. [x] Rama de baja completitud consciente de la clave: frame conserva su probe fino (material/masa), el resto usa `acquisition_target.COMPONENT_PROMPTS[expected_keys[0]]`
4. [x] `processable` filtra coincidencias `generic_component` cuando hay `expected_keys` — cae al re-prompt dirigido en vez de escribir
5. [x] `COMPONENT_PROMPTS` movido de `orchestrator._COMPONENT_PROMPTS` a `acquisition_target.py` (fuente única, sin import circular) — `start()` la usa como pregunta de apertura para wizards de definición de componente
6. [x] Nuevo `orchestrator._continue_block_acquisition()` (dedup del tail Bug54/FN-011/FN-013) — `_try_start_acquisition_from_mention` lo llama cuando el mention resuelve al bloque correcto pero a un componente ya satisfecho, continuando el hueco real del bloque en vez de caer a `define_params`/`intent_resolver`. Sin cambios en `intent_resolver.py`
7. [x] Tests: `test_fn017_component_acquisition_plumbing.py` (10) + regresión FN-011/013/014/015/016 (43) verdes

**Siguiente:** Corte 4 (copy de `¿Cuál es el valor de X?` restante) y wrong-block-while-wizard LLM leak siguen como residuales conocidos, no corregidos aquí. Bare `"10x4.5"` sin keyword "hélices" sigue sin reconocerse en el registro aéreo — preexistente, diferido.

### ✅ COMPLETADO — FN-016: navegación y seguridad de parseo en adquisición

> `DEFINE_MISSING` (Fase A o B): `"atrás"/"volver"/"vuelve"` cancela limpio (0 LLM, sin escribir valor) en vez de caer en "No reconozco ... como valor". Una clave de componente (`propellers`/`motors`/`battery`/…) nunca recibe un float posicional como si fuera un parámetro numérico.

**Plan:**
1. [x] `config.NAVIGATION_BACK_WORDS` + `acquisition_target.is_navigation_back_phrase` — exact-match, deliberadamente NO añadido a `ESCAPE_WORDS` global
2. [x] `param_definition_session._ACQUISITION_COMPONENT_KEYS` (fuente única: `BLOCK_TO_COMPONENTS`) — guard antes del parseo posicional en `answer()`, y en el bucle `zip` (defensa en profundidad para claves no-primeras)
3. [x] Wiring en `DEFINE_MISSING` (orchestrator, antes del intercept de componentes) y dentro de `ParamDefinitionSession.answer` (fallback para callers directos)
4. [x] **Hallazgo durante implementación, corregido dentro de este mismo corte** (justificado por el propio criterio D del contrato): el intercept `UX-C` comprobaba `pending_missing_reason`, campo que `ParamDefinitionSession.start()` nunca traslada a la sesión ya abierta — una descripción real de componente tras abrir el wizard (por Bug54, FN-011, FN-013 o FN-014) nunca llegaba a `_handle_component_description` y corrompía silenciosamente `current_parameters["propellers"]=10.0`. Fix aditivo (OR con `param_definition_reason`), sin quitar el check original
5. [x] Tests: `test_fn016_navigation_parse_safety.py` (11) + regresión FN-011/013/014/015 verdes

**Siguiente:** Corte 4 (copy de `¿Cuál es el valor de X?`) — solo si sigue doliendo tras este corte. Wrong-block-while-wizard LLM leak sigue como residual conocido, no corregido aquí.

### ✅ COMPLETADO — FN-015: ayuda genérica al pendiente ("ayúdame a definir")

> `DEFINE_MISSING` (y IDLE con hueco conocido): `"ayúdame a definir"` / `"ayúdame a definir el valor"` sin nombrar bloque/componente → ayuda determinista para `pending[0]` real (nunca energía/batería si lo pendiente es propulsión). 0 LLM, sesión no se reinicia.

**Plan:**
1. [x] `acquisition_target.is_help_define_pending_phrase` — excluye help-choose (FN-005) y targets nombrados vía bloque (FN-011/013/014); reutiliza el mismo verbo de adquisición, sin duplicar vocabulario
2. [x] `orchestrator._help_current_pending_acquisition` — rama por `pending[0]`: catálogo asistido (FN-005) / hint de `_COMPONENT_PROMPTS` / re-pregunta genérica; sin mutar `collected_params`
3. [x] Wiring en `DEFINE_MISSING` (tras FN-013, antes de analyze→LLM) y en IDLE (abre el bridge de Bug54/FN-011/014 y devuelve la ayuda en el mismo turno)
4. [x] Tests: `test_fn015_pending_help.py` (9) + regresión FN-005/011/013/014 verdes

**Siguiente:** FN-016 (navegación `atrás` / parse safety) — próximo contrato, no incluido aquí.

### ✅ COMPLETADO — FN-014: Acquisition Target Authority (gate IDLE unificado)

> IDLE: `definir/declarar/completar + bloque **o componente** activo` (p.ej. `"definir propellers"`) abre adquisición determinista — antes caía en ITERATE_INTERACTIVE porque `propellers` no es un alias de bloque. Mismo bridge que FN-011/Bug54, sin duplicar lógica.

**Plan:**
1. [x] `core/acquisition_target.py` — `resolve_acquisition_mention` (bloque ∪ componente, con verbo de adquisición reutilizado de `IntentResolver.DECLARE_BLOCK_VERB_PATTERNS`) + `is_mention_on_active_gap`
2. [x] `orchestrator._try_start_acquisition_from_mention` sustituye el call site IDLE de FN-011 (superset estricto); `_try_declare_active_block_help` (FN-011) queda como wrapper delgado
3. [x] Bloque equivocado (`definir batería` con propulsión activa) → mensaje determinista, sin saltar de bloque, 0 LLM
4. [x] Tests: `test_fn014_acquisition_target_idle.py` (11) + regresión FN-011 (7) + FN-013 (5) verdes

**Siguiente:** FN-015 (`ayúdame a definir` sin bloque, dentro de DEFINE_MISSING) y FN-016 (`atrás`/navegación) — próximos contratos, no incluidos aquí.

### ✅ COMPLETADO — FN-013: declare block dentro de DEFINE_MISSING

> En adquisición activa, `definir/declarar/completar + bloque activo` re-pregunta el pendiente (0 LLM), sin reiniciar sesión ni saltar de bloque.

**Plan:**
1. [x] Intercept en rama `DEFINE_MISSING` antes de analyze/valor
2. [x] Solo si bloque nombrado == `_next_pending_block`
3. [x] Re-prompt; preservar `collected_params` / `pending`
4. [x] Tests field-note + wrong-block + valor numérico

**Siguiente:** field notes CLI; copy genérico de component keys solo si duele.

### ✅ COMPLETADO — FN-012: snapshot wizard sin draft → IDLE

> Reabrir proyecto no debe restaurar `create_project_interactive` / `iterate_interactive` sin draft (error “No hay una sesión interactiva activa”).

**Plan:**
1. [x] `restore_from_snapshot` demota draftless wizards a IDLE
2. [x] `session_to_snapshot` no re-persiste esos modos
3. [x] Tests U4 + reopen orchestrator

**Siguiente:** field notes CLI; diferidos FN-011 solo si duelen.

### ✅ COMPLETADO — FN-011: declare active block sin LLM

> `"ayúdame a declarar propulsión"` en IDLE no debe despertar al LLM si el bloque nombrado es el próximo pendiente. Contrato Continuity: [PROJECT_CONTINUITY.md](PROJECT_CONTINUITY.md).

**Plan:**
1. [x] Detectar verbo declarar/completar/definir/configurar/especificar + bloque vía `normalize_block_alias`
2. [x] Solo actuar si `_next_pending_block` == bloque nombrado
3. [x] Reutilizar bridge Bug 54 (`_set_pending_next_block` + `start_define_missing_params`)
4. [x] Tests A–D + smoke CLI 0 LLM; suite 1456

**Diferido (no bloqueante):**
1. [ ] Mismo leak dentro de `DEFINE_MISSING_PARAMETERS` activo (re-prompt sin reset de `collected_params`)
2. [ ] Copy genérico preexistente: primera pregunta component-driven (`¿Cuál es el valor de motors?`)

**Siguiente:** field notes CLI; diferidos arriba solo si duelen.

### ✅ COMPLETADO — Guided Propulsion Acquisition (FN-010 / FN-008 / FN-009)

> Conservar constraints de misión, crear con hipótesis 0.6/1.2 sin preguntas internas, y conectar thrust pendiente al catálogo asistido. Contrato Continuity: [PROJECT_CONTINUITY.md](PROJECT_CONTINUITY.md).

**Plan:**
1. [x] FN-010 — fallback determinista `objective` → `parsed_constraints` (per-key; restrictions prevalece)
2. [x] FN-008 — `detallado` aplica hipótesis 0.6/1.2 automáticamente; resumen humanizado
3. [x] FN-009 — `per_motor_max_thrust_n` en assisted acquisition; IDLE prioriza propulsión; gap honesto
4. [x] Follow-up copy — `_offer_catalog_help` / `format_motor_catalog_suggestions` hablan de N vs W según pending

**Deuda pendiente (copy, no bloqueante — `_answer_assisted_motor`):**
1. [ ] Error “modelo no encontrado”: sigue diciendo *“indica W (ej: 350)”* aunque el pendiente sea `per_motor_max_thrust_n`.
2. [ ] Error “valor no reconocido”: sigue diciendo *“como potencia en W”* aunque el pendiente sea empuje.

**Siguiente:** seguir field notes en CLI; cortar la deuda de copy arriba si duele; extender el patrón a batería/hélices solo si duele.

### ✅ COMPLETADO — Assisted Acquisition + hygiene (FN-005/FN-006/FN-007)

> Cuando falta potencia/motor, no exigir `motor_power_w` crudo ni caer en analyze. Contrato Continuity: [PROJECT_CONTINUITY.md](PROJECT_CONTINUITY.md).

**Principio:** pregunta humana + 3 vías (modelo / W / catálogo) → D8 → escritura determinista + Coherence.
**No** Conversation Engine.

**Plan:**
1. [x] P0 — `param_question` humana (sin clave como héroe)
2. [x] P1 — `ayúdame a elegir` en wizard DEFINE → picker
3. [x] P2 — helper compartido `motor_catalog_assist` + apply watts/thrust
4. [x] P3 — menú 3 vías (+ candidatos inline) al preguntar potencia
5. [x] P4 — Continuity next alineado con adquisición asistida
6. [x] P5 — docs FN-005 + tests
7. [x] FN-006 — higiene localizada: `_answer_assisted_motor`, `offer_catalog_help`, `MotorSuggestion` y formatter compartido
8. [x] FN-007 — pick de catálogo preserva `motor_count` y sustituye thrust obsoleto mediante el resolver existente

**Review FN-006:** PASS WITH NOTES; sin cambios funcionales ni scope creep.
**Review FN-007:** PASS WITH NOTES; corrección física validada con 49 tests focalizados y 1431 tests de suite.

**MINOR registrados (no bloqueantes):**
1. [ ] Propagar `MotorSuggestion` a `_question_for_param(..., suggestions=...)`.
2. [ ] Desacoplar el test público de la existencia de `_offer_catalog_help`.

### ✅ COMPLETADO — Project Coherence (después de A')

> El proyecto no puede desaparecer tras el primer turno. Contrato: [PROJECT_CONTINUITY.md](PROJECT_CONTINUITY.md).

**Principio:** Project-first responses + Regla de Continuidad (qué cambió / estado ahora / siguiente decisión).
**Método:** field notes en CLI — cada vez que “parece una operación, no Jarvis”. No Conversation Engine todavía.

**Hecho (A' + thin fixes FN-001…004):**
1. [x] Experimento reopen + docs + `continuity` en startup/status
2. [x] FN-001 — no auto-define al cargar si missing vacío / Continuity basta
3. [x] FN-002/003 — detalles/estado → narrativa Continuity-first (`project_status`)
4. [x] Evidencia — no gap “número de motores” si `motor_count` en params
5. [x] FN-004 — confirmación estructural al sustituir `motor_count`
6. [x] P4 — footer Continuity tras iterate/define/calc/sim ok

### ✅ COMPLETADO — Project Continuity (A')

> Objetivo: hilo al reabrir (situación / evidencia / un siguiente paso). Contrato: [PROJECT_CONTINUITY.md](PROJECT_CONTINUITY.md).

**Plan:**
1. [x] Experimento 1h sobre workspace — confirmado: faltaba continuidad, no ArduPilot
2. [x] Documentar contrato A' (`PROJECT_CONTINUITY.md` + VISION + PRODUCT_SCOPE)
3. [x] Unificar superficie status/startup (`continuity` en `build_startup_context` + CLI)

### ✅ COMPLETADO — v1 usable (cierre de proyecto aéreo)

> Criterio en [PRODUCT_SCOPE.md](../PRODUCT_SCOPE.md).

**Done de producto (diseño):** simulación `pass` (o fallo claro) + requisitos físicos explícitos + BOM/gaps + huecos de catálogo honestos. Aéreo-first.

**Plan:**
1. [x] P0 — Documentar criterio v1 (`PRODUCT_SCOPE.md` + esta prioridad)
2. [x] P1 — Requisitos físicos derivados + D8 catálogo por espacio de diseño + BOM/gaps + honestidad energética
3. [x] P2 — D7 multi-componente + lista proyectos CLI + hint D5
4. [x] P3 — D1 `design_properties` en iteraciones; G2/G4 solo si duele

---

### ✅ COMPLETADO — Fase 2: Structure como física real

> Implementado y validado el 22 de abril de 2026. 1040 tests passing (+155 vs baseline). 0 regresiones.

**Objetivo cumplido:** `"carbono 450g"` → afecta masa → afecta simulación. Estructura es física real.

**Implementado:**
1. `[x]` **UX-C** — intercept `MISSING_COMPONENT_DEFINITION` en `process_user_input`
2. `[x]` **UX-A** — `_set_pending_next_block()` en `orchestrator.py`
3. `[x]` **UX-B** — `GUIDANCE_PATTERNS` + `STATUS_PATTERNS` extendidos en `intent_resolver.py`
4. `[x]` `MATERIAL_MAP` + `extract_frame_properties` + `_frame_completeness` + `ComponentRule frame` en `aerial.py`
5. `[x]` `MISSING_COMPONENT_DEFINITION` en `parameter_requirements.py`
6. `[x]` `_set_frame_material()` helper en `orchestrator.py`
7. `[x]` `build_startup_context` rama component-driven
8. `[x]` `_handle_component_description()` en `orchestrator.py`
9. `[x]` 20 tests en `test_fase2_uxc.py` + 9 tests en `test_aerial_domain.py` (frame) + 7 tests en `test_intent_resolver.py` (UX-B)

→ Spec completo en [🔵 Fase 2](#fase-2--structure-como-física-real-ahora)

**Criterio de finalización — VERIFICADO:**
- ✅ El usuario puede definir el frame en lenguaje natural (ej: `"carbono 450g"`)
- ✅ Guardado en `components["frame"].properties`, `design_properties.structure.material` (mirror) y `current_parameters["structure_mass_override_kg"]`
- ✅ La masa total cambia respecto al cálculo con factor (`test_criterio_total_mass_changes_vs_factor`)
- ✅ `_block_progress_status("structure") == "complete"` (`test_criterio_block_progress_complete_after_frame`)
- ✅ El flujo CLI no entra en LLM ni en wizard incorrecto (`test_criterio_no_llm_called_in_component_flow`)

---

### ✅ COMPLETADO — Fase 2.5: Control (ComponentRule mínimo)

> Implementado y validado el 22 de abril de 2026. 1075 tests passing (+35 vs Fase 2). 0 regresiones.

**Objetivo cumplido:** `"Pixhawk 4"` → `components["flight_controller"]`, `"GPS M9N"` → `components["sensors"]`. Bloque `control` completo sin LLM.

- `[x]` `FLIGHT_CONTROLLER_MAP` + `GPS_MAP` en `aerial.py`
- `[x]` `extract_flight_controller_properties` + `extract_sensor_properties`
- `[x]` `_flight_controller_completeness` + `_sensor_completeness`
- `[x]` `ComponentRule flight_controller` + `ComponentRule sensors` en `aerial_registry` (7 reglas total)
- `[x]` `_set_control_component()` helper en `orchestrator.py`
- `[x]` `_component_prompt_for_first_missing()` + dispatch por `suggested_key` en `_handle_component_description`
- `[x]` Bug fix: input wrong-block (FC cuando bloque activo es structure) → redirect contextual, no write
- `[x]` `build_startup_context` proactive question contextual por bloque (`_BLOCK_COMPONENT_HINTS`)
- `[x]` 35 tests en `test_fase25_control.py`

**Criterio de finalización — VERIFICADO:**
- ✅ `"Pixhawk 4"` → `components["flight_controller"].completeness != "low"`
- ✅ `"GPS M9N"` → `components["sensors"].completeness != "low"`
- ✅ Input FC con bloque structure activo → frame NO escrito (`test_criterio_no_cross_write_to_frame`)
- ✅ LLM no llamado en ningún paso del flujo de control
- ✅ `_block_progress_status("control") == "complete"` tras FC + GPS

→ Spec completo en [🔵 Fase 2.5](#fase-25--control-componentrule-mínimo-siguiente)

---

### ✅ COMPLETADO — Fase 2.6: Battery como componente mínimo

> Implementado y validado el 22 de abril de 2026. 1095 tests passing (+20 vs Fase 2.5). 0 regresiones.

**Objetivo cumplido:** `"6S 5000mAh"` → `components["battery"]` + `current_parameters["battery_capacity_wh"]`. Patrón físico completo validado. G1 (DSE gap) documentado como test.

- `[x]` `extract_battery_properties`: mAh→Wh cell-aware (3.7V/celda, confidence=0.9 con celdas, 0.5 sin)
- `[x]` `_set_battery_component()` — write atómico: `components["battery"]` + `current_parameters["battery_capacity_wh"]`
- `[x]` Dispatch `battery` en `_handle_component_description`
- `[x]` Intercept `component intent > param wizard`: "bateria 5000mAh" durante wizard numérico → interceptado, no error de parse
- `[x]` 20 tests en `test_fase26_battery.py`

**Criterio de finalización — VERIFICADO:**
- ✅ `components["battery"].properties["battery_capacity_wh"].value == current_parameters["battery_capacity_wh"]` (coherencia invariante)
- ✅ Battery input con bloque structure activo → frame NO escrito
- ✅ LLM no llamado en ningún paso
- ✅ `_block_progress_status("energy")`: `not_started` → `in_progress` tras `_set_battery_component`
- ✅ G1 gap documentado: DSE `_apply_delta` cambia `current_parameters` pero no `components["battery"]` (`test_criterio_dse_gap_documented`)

**Patrón validado completo:**
```
structure → componente físico ✔ (masa → física real)
control   → componente UX    ✔ (sin física)
battery   → componente físico + bridge params ✔ (autonomía cambia)
```

→ Spec en [🔵 Fase 2.6](#fase-26--battery-mínima)

---

### ✅ COMPLETADO — Fase 2.6.1: Intercepción global de componentes

> Implementado y validado el 23 de abril de 2026. 1102 tests passing (+7 vs Fase 2.6). 0 regresiones.

**Objetivo cumplido:** La detección de componentes NO depende del modo del orquestador. Regla arquitectónica: *el routing se basa en el tipo de input, no en el modo.*

**Bug corregido:** `"batería LiPo 6S 5000mAh"` en modo idle → el wizard numérico capturaba `"6"` de `"6S"` → `battery_capacity_wh = 6.0 Wh` en lugar de `111.0 Wh`.

- `[x]` `_is_pure_numeric(text)` — guarda: `"500"`, `"1.2"` nunca llegan al intercept global
- `[x]` `_should_intercept_component(text, session)` — 6 guardas ordenadas (actualizado en Fase K / Bug 62):
  1. `suggested_key != 'generic_component'` — regla de dominio real
  2. `not spec.properties` — propiedades extraídas presentes; si el extractor no sacó nada → no hay señal → no interceptar (**calidad ≠ utilidad**: `completeness` mide calidad del componente; `properties` mide si hay señal para actuar)
  3. not interrogative phrase — `"que/qué/cual/cuál/¿"` al inicio → pregunta comparativa → LLM
  4. `not _is_pure_numeric(text)` — numérico puro → wizard numérico
  5. `mode NOT IN [CREATE_PROJECT_INTERACTIVE, DEFINE_MISSING_PARAMETERS]` — wizards propios
  6. Battery-specific: al menos un keyword de energía (`mah`, `wh`, `v`, `s`)
- `[x]` Bloque `# Global component intercept` colocado ANTES del routing de modos, DESPUÉS del `pending_define_missing` block
- `[x]` Invariante arquitectónica: `DEFINE_MISSING_PARAMETERS` excluido del intercept global (tiene su propio intercept per-reason)
- `[x]` 7 tests en `test_fase26_battery.py` (Fase 2.6.1 block)

**Criterio de finalización — VERIFICADO:**
- ✅ `"batería LiPo 6S 5000mAh"` en idle → `111.0 Wh` (no `6.0 Wh`)
- ✅ `"carbono 450g"` en idle → interceptado como frame
- ✅ `"500"` en idle → NO interceptado (llega a wizard numérico)
- ✅ `"lipo"` en idle → NO interceptado (`properties={}` — extractor no sacó nada)
- ✅ `"bateria 5000"` sin unidades → NO interceptado (battery units guard)
- ✅ En `DEFINE_MISSING_PARAMETERS`: `_should_intercept_component` retorna `None` → wizard propio actúa
- ✅ Intercept wizard numérico (`DEFINE_MISSING_PARAMETERS`) conserva su propio intercept de batería
- ✅ `"estructura de fibra de carbono"` en idle → interceptado (material extraído aunque `completeness=low`) ← **Fase K / Bug 62**
- ✅ `"que material es mejor aluminio o fibra"` → NO interceptado (frase interrogativa → LLM) ← **Fase K / Bug 62**

→ Spec en [🔵 Fase 2.6.1](#fase-261--intercepción-global-de-componentes)

---

### ✅ COMPLETADO — Fase 3: Single Read Point

> Implementado y validado el 23 de abril de 2026. 1117 tests passing (+15 vs Fase 2.6.1). 0 regresiones.

**Objetivo cumplido:** `components` es ahora fuente única de verdad tanto para escritura como para lectura. El mirror legacy (`structure.material`) ha sido eliminado.

- `[x]` `jarvis/utils/design_utils.py` — módulo nuevo con 3 getters canónicos:
  - `get_frame_material(dp)` → `str` (fallback: `"aluminio"`)
  - `get_frame_mass_kg(dp)` → `float | None`
  - `get_battery_capacity_wh(dp)` → `float | None`
- `[x]` `actions/iterate.py:339` — migrado de `structure.material or "aluminio"` a `get_frame_material(design_properties)`
- `[x]` Mirror legacy eliminado en `_set_frame_material` — helper ahora escribe en 2 lugares (components + params), no 3
- `[x]` TODO eliminado de `orchestrator.py`
- `[x]` 15 tests en `test_fase3_single_read.py`
- `[x]` 3 tests de Fase 2 actualizados para reflejar el nuevo contrato (sin mirror)

**Criterio de finalización — VERIFICADO:**
- ✅ `components["frame"].material = "carbon_fiber"` + `structure.material = "aluminio"` → `get_frame_material()` retorna `"carbon_fiber"` (components gana)
- ✅ `_build_mutable_state` usa getter — sin lectura directa de mirror
- ✅ Auditoría grep: cero lecturas de `structure.material` en paths físicos
- ✅ 0 regresiones en 1117 tests

→ Spec en [🔵 Fase 3](#fase-3--single-read-point-objetivo-principal)

---

### ✅ DA1 RESUELTA — `motors` = component-driven (23 abril 2026)

`propulsion` será `"composite"` en Fase 4. `motor_power_w` pasará a mirror de `components["motors"].properties`. Prerrequisito cumplido para Fase 4.

→ Detalle en [🟠 DA1](#da1--motors-es-param-driven-o-component-driven)

---

---

## 🚀 FASE U — Hacia herramienta usable (3 junio 2026)

> Prioridad: convertir el prototipo funcional en una herramienta que da resultados físicamente creíbles.
> Condición de activación: Fases 2–6 + K + M completadas. MCP E2E verificado. 1243 tests passing.
> Secuencia: U1 → U2 → U3 → U4 → U5. Cada ítem es independiente salvo que se indique.

---

### ✅ U1 — Masa de batería dinámica — COMPLETADO (5 junio 2026, 1256 tests)

**Problema detectado en E2E (3 junio 2026):** el DSE aplicó `battery_capacity_wh: 355 → 1200 Wh` (+238%) pero `masa_total` quedó en `2.15 kg`. La batería casi triplicó su capacidad sin ganar un gramo. El resultado de autonomía (`60 min`) es físicamente incorrecto porque el cálculo se hizo con masa irreal.

**Causa raíz:** `_set_battery_component()` y `DSE._apply_delta` escriben `battery_capacity_wh` en `current_parameters` pero nunca estiman ni actualizan la masa de la batería.

**Solución:**

```python
# jarvis/tools/electricity.py  — función nueva
LIPO_ENERGY_DENSITY_WH_KG = 150.0  # Wh/kg — LiPo estándar (rango real: 120–200)

def estimate_battery_mass_kg(capacity_wh: float) -> float:
    """Estimación de masa de batería a partir de capacidad y densidad energética LiPo."""
    return round(capacity_wh / LIPO_ENERGY_DENSITY_WH_KG, 3)
```

```python
# jarvis/core/orchestrator.py — _set_battery_component()
# Añadir al final del helper, junto al write de battery_capacity_wh:
estimated_mass = estimate_battery_mass_kg(capacity_wh)
new_params["battery_mass_kg"] = estimated_mass
```

```python
# jarvis/core/calculation_engine.py — build()
# Leer battery_mass_kg si está disponible y sumarlo a masa_total en lugar del factor fijo
battery_mass = parameters.get("battery_mass_kg", 0.0)
```

```python
# jarvis/actions/iterate.py (DSE _apply_delta) — sincronizar masa al aplicar delta de Wh
if "battery_capacity_wh" in candidate.params_delta:
    new_params["battery_mass_kg"] = estimate_battery_mass_kg(
        candidate.params_delta["battery_capacity_wh"]
    )
```

**Criterio de finalización:**
- `_set_battery_component("LiPo 355 Wh")` → `battery_mass_kg ≈ 2.37 kg` en `current_parameters`
- `_set_battery_component("LiPo 1200 Wh")` → `battery_mass_kg ≈ 8.0 kg` en `current_parameters`
- `masa_total` sube al aplicar DSE con batería mayor
- DSE que propone `1200 Wh` también recalcula masa → autonomía resultante es realista (no 60 min con 2.15 kg)
- 0 regresiones en tests de Fase 2.6

**Tests nuevos (≥ 5):**
- `test_battery_mass_estimated_on_set_component` — `355 Wh → 2.37 kg`
- `test_battery_mass_updates_total_mass` — `masa_total` cambia al cambiar batería
- `test_dse_apply_delta_syncs_battery_mass` — delta de Wh → delta de masa
- `test_autonomy_realistic_after_large_battery` — 1200 Wh con masa real → autonomía ≤ 40 min (no 60)
- `test_estimate_battery_mass_kg_boundary` — 0 Wh → 0 kg, 100 Wh → 0.667 kg

**Riesgo:** `battery_mass_kg` es nuevo campo en `current_parameters` → auditar que `calculation_engine` no lo confunda con `structure_mass_override_kg`. Son aditivos, no alternativos.

---

### ✅ U2 — Bridge propellers → parámetros físicos (D6) — COMPLETADO (5 junio 2026, 1267 tests)

**Problema:** el usuario declara `"6 hélices 15x5 pulgadas"` y el componente se guarda en `components["propellers"]`, pero `propeller_diameter_in` NO se escribía en `current_parameters`. El motor de cálculo no tenía datos de hélice → empuje por hélice no calculado → sistema caía al fallback `per_motor_max_thrust_n` declarado.

**Solución:** `_set_propeller_component()` debe actuar como bridge (análogo a `_set_motor_component` → `motor_power_w`):

```python
# jarvis/core/orchestrator.py — _set_propeller_component()
# Extraer diameter_in y pitch del ComponentSpec y escribir en current_parameters:
if "diameter_in" in spec.properties:
    new_params["propeller_diameter_in"] = float(spec.properties["diameter_in"].value)
if "pitch_in" in spec.properties:
    new_params["propeller_pitch_in"] = float(spec.properties["pitch_in"].value)
```

**Prerrequisito:** `extract_propeller_properties` en `aerial.py` debe extraer `diameter_in` y `pitch_in` del texto libre. Hoy extrae `diameter_in` pero no siempre escribe en `current_parameters`.

**Criterio de finalización:**
- `"6 hélices 15x5"` → `current_parameters["propeller_diameter_in"] = 15.0`
- `calculation_engine` usa `propeller_diameter_in` en empuje por hélice (ruta hélice activa)
- `propeller_status` en `SimulationResult` pasa de `"missing_propeller_parameters"` a `"valid"`
- La simulación muestra `propeller_thrust_inferred = True` en reasoning

**Tests nuevos (≥ 4):**
- `test_set_propeller_bridges_diameter_to_params`
- `test_set_propeller_bridges_pitch_to_params`
- `test_propeller_status_valid_after_component_set`
- `test_engine_uses_propeller_params_when_available`

---

### ✅ U3 — DSE espacio de exploración ampliado (domain-agnostic) — COMPLETADO (9 junio 2026, 1278 tests)

**Problema:** el DSE para `mejorar_autonomia` solo variaba `battery_capacity_wh` y `motor_count`. No exploraba:
- Reducción de masa del frame (menos peso total → más autonomía con la misma batería)
- Motores más eficientes a bajo consumo

**Decisión de diseño (9 junio 2026):** usar **factores relativos** en `EXPLORATION_GRIDS`, no valores absolutos en `COMPONENT_VARIATION_RULES`. Razón: un factor `0.75` sobre `structure_mass_override_kg` funciona igual para un dron de 300g de frame, un rover de 3kg, o un brazo robótico de 1kg. Un valor absoluto como `[0.280, 0.350, 0.450]` solo es válido para drones — viola la arquitectura multi-dominio de Jarvis.

**Solución:** añadir entradas a `EXPLORATION_GRIDS["mejorar_autonomia"]` en `design_explorer.py`:

```python
# U3: Estructura más ligera — domain-agnostic
{"structure_mass_override_kg_factor": 0.6},
{"structure_mass_override_kg_factor": 0.75},
{"structure_mass_override_kg_factor": 0.6, "battery_capacity_wh_factor": 1.5},
# U3: Motores más eficientes (menor consumo por actuador)
{"motor_power_w_factor": 0.65},
{"motor_power_w_factor": 0.65, "structure_mass_override_kg_factor": 0.75},
```

Si `structure_mass_override_kg` no existe en `current_parameters`, `_apply_delta` devuelve `None` y el candidato se omite automáticamente — sin errores, sin defaults inventados. Mismo comportamiento para cualquier dominio.

**Prerrequisito:** U1 (masa dinámica de batería) — completado. Sin U1, candidatos de batería grande tenían score inflado.

**Criterio de finalización:**
- DSE para `autonomía` genera candidatos de frame ligero y motores eficientes, no solo batería grande
- Candidatos de frame aplican para dron y para ground vehicle igualmente
- Si el proyecto no tiene `structure_mass_override_kg` declarado, los candidatos de frame se omiten (no fallan)
- 0 regresiones en `test_da2_components_delta.py`

**Tests nuevos (≥ 3):**
- `test_dse_autonomia_explores_frame_mass` — candidatos con `structure_mass_override_kg_factor` generados
- `test_dse_autonomia_explores_motor_power_factor` — candidatos con `motor_power_w_factor=0.65` generados
- `test_dse_frame_candidate_skipped_when_no_override` — sin `structure_mass_override_kg` en params → candidato omitido (no error)

**Tests nuevos (≥ 3):**
- `test_dse_autonomia_explores_frame_mass`
- `test_dse_autonomia_explores_motor_power`
- `test_dse_top_candidate_considers_total_mass`

---

### ✅ U4 — Persistencia del historial conversacional — COMPLETADO (9 junio 2026, 1289 tests)

**Problema:** al reiniciar el MCP server (p.ej. tras un crash o redeploy), el historial de mensajes del wizard se pierde. El usuario pierde el contexto de la conversación aunque el proyecto siga en disco.

Impacto: si el wizard está a mitad de un bloque (`DEFINE_MISSING_PARAMETERS`), el reinicio lo resetea a `idle` → el usuario no sabe que puede continuar con `"sigamos"`.

**Solución:** persistir el historial de mensajes en `state.json` o en un archivo separado:

```python
# jarvis/workspace/workspace_manager.py
# Añadir campo "conversation_history": list[dict] al save/load de state.json
# Máximo: últimos 50 mensajes (evitar crecimiento ilimitado)

def save_conversation_history(self, project_id: str, history: list[dict]) -> None: ...
def load_conversation_history(self, project_id: str) -> list[dict]: ...
```

```python
# jarvis/core/orchestrator.py
# En handle_user_text: append al historial tras cada turno
# En __init__: cargar historial desde workspace si hay proyecto activo
```

**Criterio de finalización:**
- Reiniciar `JarvisSessionManager` con proyecto activo → historial restaurado
- El wizard retoma el estado correcto (modo, bloque activo) desde `state.json`
- Historial truncado a 50 mensajes — no crece ilimitadamente

**Tests nuevos (≥ 3):**
- `test_conversation_history_persisted_on_save`
- `test_conversation_history_restored_on_load`
- `test_conversation_history_truncated_at_max`

---

### ✅ U5 — Validación de restricciones incremental — COMPLETADO (9 junio 2026, 1300 tests)

**Problema:** las restricciones declaradas en `create_project` (p.ej. `"peso máximo 5kg"`) solo se verifican cuando el usuario ejecuta `simula`. Durante la definición de componentes, el sistema no avisa si un componente declarado ya viola la restricción.

Resultado: el usuario completa el wizard de 4 bloques y al simular descubre que viola el peso → debe iterar hacia atrás.

**Solución:** al final de `_handle_component_description` (tras recalcular), verificar restricciones activas y emitir warning inline si alguna se viola:

```python
# jarvis/core/orchestrator.py — _handle_component_description()
# Tras _recalculate():
violations = _check_constraint_violations(updated_state)
if violations:
    response_text += f"\n⚠ {'; '.join(violations)}"
```

```python
# jarvis/core/orchestrator.py — función nueva
def _check_constraint_violations(state: ProjectState) -> list[str]:
    """Verifica restricciones activas contra el estado actual. Solo restricciones numéricas parseadas."""
    violations = []
    constraints = state.design_properties.parsed_constraints or {}
    calc = state.last_calculation
    if not calc:
        return violations
    if "max_weight_kg" in constraints and calc.total_mass_kg > constraints["max_weight_kg"]:
        violations.append(f"peso {calc.total_mass_kg:.2f} kg supera máximo {constraints['max_weight_kg']} kg")
    return violations
```

**Criterio de finalización:**
- Declarar un frame de 4 kg con restricción `peso máximo 5kg` no genera warning
- Declarar un frame de 6 kg con restricción `peso máximo 5kg` → warning inline inmediato
- Warning no bloquea el flujo — es informativo
- `simula` sigue siendo el punto de validación completa

**Tests nuevos (≥ 4):**
- `test_no_warning_when_within_constraints`
- `test_weight_warning_when_frame_exceeds_max`
- `test_constraint_check_skipped_without_calculation`
- `test_warning_appended_inline_not_blocking`

---

### Criterio de "herramienta usable" (Fase U completa)

| Requisito | Cubierto por |
|---|---|
| Masa total coherente con componentes reales | U1 |
| Hélices declaradas tienen efecto físico | U2 |
| DSE explora el espacio de diseño real, no solo batería | U3 |
| Reiniciar el server no pierde el contexto | U4 |
| El usuario sabe en tiempo real si viola restricciones | U5 |

**Dependencias entre ítems:**
- U1 es prerrequisito blando de U3 (sin masa dinámica, DSE da scores inflados)
- U2 es independiente
- U4 es independiente
- U5 requiere que `parsed_constraints` esté disponible (ya implementado desde Fase 2 hardening)

---

## 🔍 VALIDACIÓN MANUAL PENDIENTE

> No se puede resolver en código. Requiere uso humano.

### Cierre dominio aéreo — validación CLI (hélice activa)

**✅ VALIDADO — 15 julio 2026 (Fase N, vía MCP server).**

- [x] Crear un proyecto de dron sin `per_motor_max_thrust_n` desde CLI real.
- [x] Verificar que el sistema solicita proactivamente `propeller_diameter_in` y `propeller_rpm` (vía `configurar hélices`).
- [x] Verificar que la simulación con datos de hélice produce resultado coherente: empuje=38.24N desde 10"×7500rpm×4 motores (Ct=0.12), `safety_margin=2.83`, `status=pass`.
- [x] Registrar qué preguntas sobran, qué falta, dónde se rompe la UX → 4 bugs detectados (76–79), ver BUGS.md Fase N.

**Condición para rediseño de `create_project` por ramas:** cumplida. Datos de sesión disponibles en BUGS.md Fase N.

### Validación con uso real — routing LLM

> **Ciclo CERRADO 2026-08-05.** Cierre: `.jes/artifacts/cycle_close_llm_calibration.md`. Evidencia: `.jes/artifacts/calibration_summary.md`.

- [x] Validar FASE_LLM con ≥30 inputs reales. Analizar `runtime/llm_logs/` y medir distribución de routing (`preseed_step2` / `fallback_wizard` / `rejected_*`). → calibración 2026-08-05 (`.jes/artifacts/calibration_summary.md`).
- [x] Ajustar `prompt_builder` / umbral de confianza si slang vago preseed-ea variables (`más chicha` → `battery_capacity_wh` conf 1.0). → grounding léxico en `SemanticIntentAdapter` + instrucciones de prompt (2026-08-05).
- [x] Validar precedencia `acción fuerte > analyze` en prompts mixtos (ej: "calcula cómo influye...").
- [x] **Preempción sticky iterate** (2026-08-05): dentro de `ITERATE_INTERACTIVE`, intents fuertes + componentes abortan el wizard y re-despachan idle; status/analyze siguen soft (Bug 7). Tests: `TestIterateWizardPreemption`.
- [x] Ajustar `EXPLORE_PATTERNS` para frases tipo `optimiza para payload` / `mejora la estabilidad` (2026-08-05): dominios DSE completos + keywords goal (`margen`, `para masa/peso`).

### ✅ COMPLETADO — sugerencias de motor (validación UX)

- [x] Validar con uso real si las sugerencias de motor aportan valor o generan ruido. → **valor en hits de catálogo**; field note `.jes/artifacts/field_note_2026-08-05_motor_suggestions.md`. Fix: preempt no aborta DEFINE@step2; aviso si KV sin match en biblioteca.

---

## 🧠 ESTADO ACTUAL DEL SISTEMA

- **1321 tests passing** sin regresiones (baseline 885, +155 Fase 2, +35 Fase 2.5, +20 Fase 2.6, +7 Fase 2.6.1, +15 Fase 3, +96 Fases 4–6+K, +14 Fase L+M, +87 Fase U, +21 Fase N). Verificado 16 julio 2026.
- **1331 tests passing** tras rediseño `create_project` por ramas (5 agosto 2026, +11).
- **1337 tests passing** tras repair de `workspace_path` en carga (5 agosto 2026, +6). Proyectos con path legacy se reparan al `StateManager.load`.
- **1346 tests passing** tras preempción de intents fuertes en `ITERATE_INTERACTIVE` (5 agosto 2026, +9). Sticky wizard ya no come explore/calculate/simulate/components/nuevo iterate.
- **1364 tests passing** tras ampliar `EXPLORE_PATTERNS` a payload/estabilidad/masa vía optimiza|mejora (5 agosto 2026, +18).
- **1371 tests passing** tras validación sugerencias de motor + fix preempt DEFINE + nota catálogo vacío (5 agosto 2026, +2).

- `create_project`, `calculate`, `simulate` e `iterate` funcionan end-to-end.
- La capa LLM está integrada como interfaz segura, validada y con logging completo.
- El intérprete semántico de iterate (FASE_LLM) está implementado, testeado y **calibrado con uso real** (2026-08-05). Ciclo LLM cerrado.
- La arquitectura multi-dominio está operativa: domains `aerial` y `ground`, `registry_selector` con routing híbrido.
- El sistema solicita proactivamente parámetros físicos faltantes sin LLM (`DEFINE_MISSING_PARAMETERS`), incluyendo hélice (`propeller_diameter_in`, `propeller_rpm`) para proyectos aéreos.
- Pipeline hélice activo: `propeller_status` en `SimulationResult`, exclusión mutua en reasoning, colección proactiva en orchestrator. **Validado E2E en Fase N (15 julio 2026).**
- `PhaseLayer` clasifica el proyecto en 4 fases deterministas y lo muestra en el startup context.
- `SystemDefinitionSession` puebla la arquitectura del sistema con stubs antes de calcular, con orden derivado del grafo de dependencias.
- `state.json` tiene contratos de responsabilidad claros por campo. Sin valores ficticios, sin parseo de strings en capas de cálculo.
- Capa conversacional (Human Layer Sprint v1) completa: routing semántico, frases de navegación, re-intent detector, bridge a `DEFINE_MISSING_PARAMETERS`, redirects por componente, validaciones de material.
- Decision Layer v1 completo: pipeline único `_collect_suggested_actions` → `_deduplicate` → `_resolve_conflicts` → `sorted()`. `CONFLICT_RULES` declarativas. Render jerárquico.
- DSE v1 implementado: exploración en memoria, scoring por objetivo, top-5 viables, sin modificar estado.
- **Fase 2 + 3 (Structure como física real + Single Read Point):** `"carbono 450g"` → masa real en `calculation_engine`. Frame se persiste en 2 lugares: `components["frame"].properties` (canónico) y `current_parameters["structure_mass_override_kg"]` (bypass física). Mirror `design_properties.structure.material` eliminado en Fase 3. Flujo sin LLM garantizado.
- **Fase K (validación end-to-end, 29 abril 2026):** bugs de flujo real corregidos — bridge mirrored params (K1), alias `motors→motor_count` (K2), mensaje `in_progress` diferenciado (K3), intercept por presencia de propiedades en lugar de completeness (K4 — `calidad ≠ utilidad`).
- **Fase U completada (9 junio 2026):** masa de batería dinámica (U1), bridge propellers→params físicos (U2), DSE exploración ampliada domain-agnostic (U3), persistencia historial conversacional (U4), validación restricciones incremental (U5).
- **Fase N (15–16 julio 2026):** validación CLI propeller-only path E2E — `calculate_thrust_from_propeller` activo sin `per_motor_max_thrust_n`. 4 bugs detectados y corregidos (76–79): vehicle type alias en create_project, escape suave wizard DEFINE_MISSING, merge motor_count en doble write, DSE apply sin constraint check. **1321 tests passing.**

**Limitaciones conocidas:**
- Modelo energético parcial: `(wh/w)×60` — sin curva de descarga ni C-rating.
- `DependencyGraph` estático: mismo orden para todo proyecto del mismo dominio.
- Routing LLM: calibración real 2026-08-05 + grounding léxico; `CONFIDENCE_THRESHOLD = 0.75` retenido (retune opcional con más preseeds grounded).
- Biblioteca de motores: matching por KV, no por espacio de diseño — **D8**.

---

## 🟡 SYSTEM GAPS

> Puntos donde el sistema **ya se rompe** o queda incompleto con uso real. No son futuro — son presente.

### G1 — DSE ignora `components.properties`

~~El DSE actual solo varía `current_parameters`.~~ ✅ **RESUELTO (3 junio 2026)**

**DA2** implementó `ExplorationCandidate.components_delta`, `COMPONENT_GRIDS` (battery + motors) y el loop de componentes en `explore()`.

**G1** completa el cierre: `COMPONENT_GRIDS` reemplazado por `COMPONENT_VARIATION_RULES` (tabla declarativa) + `_build_component_spec` (builder genérico) + `_build_component_candidates_for_goal` (generador sin lógica de dominio). Frame añadido a los grids: `reducir_masa` (0.280 / 0.350 / 0.450 kg) y `mejorar_estabilidad` (0.500 / 0.700 kg).

**Propiedad de extensibilidad:** añadir variación de cualquier componente (rueda, brazo, sensor, depósito) solo requiere añadir una entrada a `COMPONENT_VARIATION_RULES` — sin cambios en `_build_component_candidates_for_goal` ni en `explore()`.

3 nuevos tests en `TestFrameComponentGrid` en `test_da2_components_delta.py`.

---

### G2 — `_block_progress_status` no soporta composite

~~La rama `"composite"` no existe.~~ ✅ **RESUELTO en G2 (23 abril 2026)** — `BLOCK_TYPE`, `get_block_type()` y rama `"composite"` implementados. 18 tests en `test_block_progress.py`.

**Decisión de semántica pendiente para Fase 4 (DA3):** La implementación actual usa AND estricto:
`composite = params_ok AND components_ok`. Cuando `param_reason=None`, `params_ok=True` trivialmente,
lo que hace que bloques component-only parezcan más avanzados (`in_progress` con 1 componente aunque falten params).
En Fase 4 decidir si mantener AND estricto o AND semántico (peso por bloque). **No urgente — anotar para Fase 4.**

**Cuándo se vuelve crítico:** inicio de Fase 4.

---

### G3 — `_set_pending_next_block` sin guard de doble trigger

Si dos handlers distintos llaman a `_set_pending_next_block` en el mismo ciclo (ej: `_handle_component_description` + otro handler futuro), el bloque activo puede avanzar dos veces produciendo estado inconsistente.

**Deuda técnica leve — no urgente.** Solución cuando aparezca un segundo call site:
```python
# Opción A: guard de sesión
if not session.pending_define_missing:
    self._set_pending_next_block()

# Opción B: parámetro force
def _set_pending_next_block(self, force: bool = False): ...
```

**Cuándo se vuelve crítico:** al añadir un segundo handler que gestione bloques component-driven (ej: control en Fase 2.5 si usa su propio handler).

---

### G4 — `completeness="medium"` como criterio de "block complete" — deuda controlada

En Fase 2, un frame con solo masa (`completeness="medium"`) marca `structure` como `"complete"`. Correcto para Fase 2 (el override de masa es suficiente para la física).

En Fase 3 se añaden `arm_length_m` y `stiffness` al frame. Si `_frame_completeness` no actualiza su criterio, un frame con solo masa seguirá siendo "complete" aunque le falten los campos estructurales avanzados.

**Regla para Fase 3:** redefinir completeness levels:
```
Fase 2: medium = mass_kg presente → suficiente para física básica
Fase 3: medium = mass_kg + material, high = mass_kg + material + arm_length_m
```
`_block_progress_status` usa `completeness != "low"` como criterio — esto también necesita revisión en Fase 3.

---

## 🟠 DECISIONES ABIERTAS

> Decisiones sin tomar que bloquean diseño posterior. Resolver solo cuando llegue su fase.

### DA1 — ¿`motors` es param-driven o component-driven?

**✅ RESUELTA — 23 abril 2026: `motors` = component-driven**

**Rationale:**
- Coherencia con Fase 2–3: frame, battery y control ya son component-driven. Volver a param rompe el patrón establecido.
- Permite energy como sistema físico real: `battery + motors` → composite con semántica de ingeniería.
- Habilita DSE sobre componentes de propulsión (trade-offs `"T-Motor MN3510 vs alternativa"`).
- Evita arquitectura híbrida param/component en el bloque energy.

**Impacto arquitectónico:**
- `BLOCK_TYPE["propulsion"]` pasa a `"composite"` en Fase 4.
- `motor_power_w` en `current_parameters` se convierte en mirror de `components["motors"].properties["power_w"]`.
- Requiere: `ComponentRule motors` + extractor `extract_motor_properties` + helper `_set_motor_component`.
- `_block_progress_status("propulsion")` usará rama `"composite"` (prerrequisito: G2).

**Lo que NO se hace aquí:** no se implementa extractor, wizard ni helper hasta Fase 4. Esta entrada solo congela la dirección arquitectónica.

~~`BLOCK_TYPE["propulsion"] = "param"` es provisional. Si `motors` migra a component-driven, `propulsion` pasa a `"composite"` y el wizard necesita rediseño completo.~~

~~**Cuándo decidir:** antes de iniciar Fase 4. No antes.~~

---

### DA-MOTORS-2 — Componente `motors` en múltiples bloques: ownership vs. dependencia

**Documentada: 23 abril 2026. Activar en Fase 6 ANTES de migrar `propulsion` a `"composite"`.**

**Contexto:** `motors` aparece como component_key en tres bloques: `propulsion`, `energy` y `actuation`. Hoy inocuo porque solo `energy` es `"composite"`. Cuando `propulsion` migre a `"composite"` (Fase 6), ambos bloques evaluarán `motors` como criterio de completitud.

**Insight clave:** `motors` no es duplicación incorrecta — es intersección de dominios físicos:
- `propulsion` → motors como generador de empuje (`thrust_n`, `kv_rating`)
- `energy` → motors como consumidor de energía (`power_w`)

El mismo objeto físico participa en dos sistemas. Esto es correcto por diseño.

**Opciones evaluadas:**

| Opción | Descripción | Veredicto |
|---|---|---|
| **A — Ownership** | `propulsion` posee `motors`; `energy` delega en `propulsion` | ✗ Introduce acoplamiento entre bloques, rompe independencia de evaluación, requiere lógica de delegación |
| **B — Dependencia compartida** | `motors` es recurso compartido; ambos bloques lo evalúan independientemente | ✔ Simple, consistente, escalable |

**Decisión: Opción B.**

Un componente definido satisface simultáneamente todos los bloques que lo referencian. No hay propietario — hay vistas funcionales. Esto está formalizado como SYSTEM RULE en `system_architecture_catalog.py`.

---

**✅ RESUELTO — Definición formal de `propulsion_complete` (24 abril 2026)**

`BLOCK_TO_COMPONENTS["propulsion"] = ["motors", "propellers"]` se **mantiene** (no se reduce a `["propellers"]`).

```
propulsion_complete =
    params_ok:      current_parameters["motors"] (count) + "per_motor_max_thrust_n" definidos
    AND motors_ok:     components["motors"].completeness != "low"  ← shared con energy
    AND propellers_ok: components["propellers"].completeness != "low" ← exclusivo de propulsion
```

**Riesgo de doble completitud — ANALIZADO Y DESCARTADO:**

La preocupación era que definir `motors` completara simultáneamente `energy` y `propulsion`, saltando pasos.

Análisis con Option B (shared dependency) + composite AND-estricto:

| Acción del usuario | energy | propulsion |
|---|---|---|
| Define motors | in_progress (falta battery) | in_progress (faltan propellers) |
| Define motors + battery | complete | in_progress (faltan propellers) |
| Define motors + propellers | in_progress (falta battery) | in_progress (faltan params count/thrust) |
| Define motors + propellers + params + battery | complete | complete |

→ No existe escenario donde motors solo complete propulsion. Propellers siempre se requieren — el wizard los pedirá.
→ El riesgo de "saltar pasos" no existe con este diseño. La SYSTEM RULE es correcta.

**Pasos de implementación en Fase 6:**
1. `BLOCK_TYPE["propulsion"] = "composite"` (ya confirmada componentes: `["motors", "propellers"]`)
2. `ComponentRule propellers` + extractor en `aerial.py` (aun no existe)
3. Resolver DA-MOTORS-3 (renombrar `current_parameters["motors"]` → `"motor_count"`) antes de este cambio
4. Verificar que `_block_progress_status("propulsion")` con composite AND-estricto no salta propellers
5. Documentar como DA-MOTORS-2 resuelto

---

### DA-MOTORS-3 — Naming collision: `current_parameters["motors"]` vs `components["motors"]`

**Documentada: 23 abril 2026. Resolver en Fase 6 ANTES de migrar `propulsion` a `"composite"`.**

**El conflicto:**

| Clave | Tipo | Semántica |
|---|---|---|
| `current_parameters["motors"]` | `int` | Número de motores — input al cálculo de empuje total |
| `components["motors"]` | `ComponentSpec` | Especificación física del motor (KV, potencia, modelo) |

Ambas claves se llaman `"motors"` pero son objetos completamente distintos en espacios distintos.

**Por qué no rompe hoy:** `current_parameters` y `design_properties.components` son dicts separados — no hay colisión en tiempo de ejecución. El `calculation_engine` lee `current_parameters["motors"]` (int) y la lógica de bloques lee `design_properties.components["motors"]` (ComponentSpec).

**Por qué romperá en Fase 6:** cuando `propulsion` migre a `"composite"`, `_block_progress_status` evaluará `components["motors"].completeness`. Si en algún punto la lógica intenta derivar el conteo de motores desde el componente (`component.properties["motor_count"]`) y escribirlo en `current_parameters["motors"]`, hay riesgo de confusión semántica + bugs silenciosos.

**Opciones:**

| Opción | Cambio | Impacto |
|---|---|---|
| A — Renombrar param | `current_parameters["motors"]` → `current_parameters["motor_count"]` | Cambio rompedor: audit de todos los readers en calculation engine, requirements, suggestions |
| B — Derivar count desde componente | `motor_count = components["motors"].properties["motor_count"].value` → escribe en `current_parameters["motors"]` | Nuevo bridge; requiere que `extract_motor_properties` capture siempre `motor_count` |
| C — Mantener separados explícitamente | Documentar que son espacios distintos; no intentar derivar uno del otro | Más simple, pero deja la ambigüedad de naming |

**Recomendación: Opción A** — renombrar `current_parameters["motors"]` → `current_parameters["motor_count"]` en Fase 6 antes de implementar propulsion composite. Registrar como DA-MOTORS-3 resuelto en ese momento.

---

### DA2 — DSE v2: contrato para variar `components.properties`

El DSE actual solo varía `current_parameters`. Contrato ya definido, pendiente de implementación:

```python
ExplorationCandidate v2:
    params_delta: dict[str, Any]        # ya existe
    components_delta: dict[str, dict]   # NUEVO
    # Ejemplo: {"frame": {"mass_kg": 0.4, "material": "carbon_fiber"}}
```

El explorador aplica `components_delta` via el helper de escritura único (`_set_frame_material()`, etc.) — nunca escribe directamente en `components.properties`.

**Implementar cuando:** Fase 2 validada. No requiere más diseño.

---

## 🔵 EJECUCIÓN POR FASES

### Fase 2 — Structure como física real ✅ COMPLETADA

> Implementada: 22 abril 2026. 1040 tests passing. 0 regresiones.
> Condición de activación confirmada: bloque structure bloqueado en prueba manual — documentado 22 abril 2026.

**Contexto:** "estructura" es actualmente decorativa — no afecta cálculos. Para ser ingeniería real, la masa del frame debe entrar en `calculation_engine.build()` y reducir empuje requerido + mejorar autonomía.

---

#### Bugs UX bloqueantes — IMPLEMENTADOS

- [x] **UX-C** — `MISSING_COMPONENT_DEFINITION` + `_handle_component_description` en orchestrator. Input `"frame de fibra de carbono 500g"` → persiste directamente, sin LLM.
- [x] **UX-A** — `_set_pending_next_block()` en `orchestrator.py`. `si` tras propulsion completo → carga `DEFINE_MISSING_PARAMETERS` del siguiente bloque automáticamente.
- [x] **UX-B** — `GUIDANCE_PATTERNS` + `STATUS_PATTERNS` extendidos: `"sigamos"`, `"vamos con el siguiente"`, `"continua"`, `"continuamos"`, `"siguiente bloque"` → `project_status` sin LLM.

**Tests UX bugs:**
- [x] `test_si_with_component_reason_returns_description_prompt`
- [x] `test_pending_next_block_set_after_propulsion_complete`
- [x] 7 tests parametrizados `test_uxb_navigation_phrases_resolve_to_project_status` en `test_intent_resolver.py`

---

#### Modelo de datos — fuentes de verdad (crítico)

| Campo | Rol | Quién lo escribe | Quién lo lee |
|---|---|---|---|
| `components["frame"].properties["material"]` | **CANÓNICO** — nueva fuente de verdad | `_set_frame_material()` | futuro `_build_mutable_state` |
| `design_properties.structure.material` | **MIRROR LEGACY** — derivado | `_set_frame_material()` (sync) | `_build_mutable_state` en `iterate.py` (hoy) |
| `components["frame"].properties["mass_kg"]` | **CANÓNICO** — nueva fuente de verdad | `_set_frame_material()` | orquestador al calcular override |
| `current_parameters["structure_mass_override_kg"]` | **BYPASS física** — mecanismo existente | orquestador (deriva de mass_kg) | `calculation_engine.build()` |

**Regla absoluta:** siempre escribir via el helper `_set_frame_material()` — nunca directamente en ambos sitios por separado.

**TODO explícito en código:**
```python
# TODO: remove structure.material mirror when _build_mutable_state migrates to
#       read from components["frame"].properties["material"] directly (Fase 3).
```

---

#### Principios de implementación

- Sin nuevos campos de schema.
- `structure_mass_override_kg` en `current_parameters` es el mecanismo de inyección ya existente — reutilizar.
- Un único punto de escritura: `_set_frame_material(project_state, mass_kg, material)`.
- Lectura actual en `_build_mutable_state`: sigue siendo `design_properties.structure.material` (no cambiar todavía — Fase 3).

**Variables mínimas de Fase 2:**
```python
Frame:
    material: "carbon_fiber" | "aluminum" | "plastic"  # → components["frame"].properties + structure.material (mirror)
    mass_kg:  float                                     # → components["frame"].properties + current_parameters["structure_mass_override_kg"]
```
Variables diferidas a Fase 3: `arm_length_m`, `stiffness`, `structural_fraction`.

---

#### Cambios de código — IMPLEMENTADOS

**`jarvis/domains/aerial.py`**

- [x] `MATERIAL_MAP: dict[str, str]` — normalización: `"carbono" | "fibra de carbono" → "carbon_fiber"`, `"aluminio" → "aluminum"`, `"plastico" | "abs" → "plastic"`. Algoritmo longest-match para evitar falsos positivos.
- [x] `extract_frame_properties(normalized: str) → dict[str, PropertyValue]` — masa con word boundary (`\b`) para evitar falsa extracción de `"4000mah"`. Kg tiene prioridad sobre gramos.
- [x] `_frame_completeness(props) → tuple[str, list[str]]` — `"low"` (vacío o solo material), `"medium"` (mass_kg presente), `"high"` (mass_kg + material).
- [x] `ComponentRule` para `frame` añadida a `aerial_registry` (5 reglas total): keywords `("frame", "chasis", "estructura", "armazón", "carbon", "carbono", "aluminio")`.

**`jarvis/core/parameter_requirements.py`**

- [x] `MISSING_COMPONENT_DEFINITION = "missing_component_definition"` — constante para identificar bloques component-driven en `pending_missing_reason`. No es un nuevo `RequirementReason`.

**`jarvis/core/orchestrator.py` — helper `_set_frame_material` (único punto de escritura)**

- [x] Implementado. Escribe en 3 lugares de forma atómica. Usa `model_copy` (Pydantic v2) — no muta el estado original. Guard: `material=None` preserva el mirror legacy en lugar de sobreescribir con `None`.

**`jarvis/core/orchestrator.py` — `build_startup_context`**

- [x] Rama component-driven: cuando `get_param_reason_for_block` devuelve `None`, `proactive_question` incluye ejemplo. `param_definition_reason = MISSING_COMPONENT_DEFINITION`, `missing_params = component_keys`.

**`jarvis/core/orchestrator.py` — `process_user_input` en modo `DEFINE_MISSING_PARAMETERS`**

- [x] Intercept implementado ANTES de `param_definition_session.answer()`: `pending_missing_reason == MISSING_COMPONENT_DEFINITION` → `_handle_component_description(user_input, current_session)`.

**`jarvis/core/orchestrator.py` — nuevo método `_handle_component_description`**

- [x] Implementado con lógica completa:
  - Afirmativo → prompt contextual con ejemplo
  - Descriptivo + completeness ≥ medium → `_set_frame_material` → recalcula → guarda → `_set_pending_next_block` → `_append_arch_progress_hint` → `ok`
  - Descriptivo + completeness low → follow-up dirigido: masa-falta / material-falta / ambos-faltan
  - No hay proyecto activo → `status: error` (no crash)
  - LLM nunca se llama en ningún paso del flujo (`test_criterio_no_llm_called_in_component_flow`)

---

#### Tests nuevos — TODOS IMPLEMENTADOS (36 tests en total)

**`jarvis/tests/test_aerial_domain.py` (+9 tests frame):**
- [x] `test_extract_frame_mass_grams` — "500g" → `mass_kg=0.5`
- [x] `test_extract_frame_mass_kg` — "0.45 kg" → `mass_kg=0.45`
- [x] `test_extract_frame_mass_with_material` — "fibra de carbono 450g" → `mass_kg=0.45`, `material="carbon_fiber"`
- [x] `test_extract_frame_material_only` — "aluminio" → `material="aluminum"`, sin mass_kg
- [x] `test_frame_completeness_low_empty` — sin props → `"low"`
- [x] `test_frame_completeness_medium_with_mass` — mass_kg presente → `"medium"`
- [x] `test_frame_completeness_high_with_mass_and_material` — ambos → `"high"`
- [x] `test_aerial_registry_matches_frame_keyword` — "frame" → `component_type="structure"`
- [x] `test_aerial_registry_matches_carbon_keyword` — "carbono" → `component_type="structure"`

**`jarvis/tests/test_intent_resolver.py` (+7 tests UX-B):**
- [x] `test_uxb_navigation_phrases_resolve_to_project_status` (parametrizado × 7)

**`jarvis/tests/test_fase2_uxc.py` (20 tests total):**
- [x] `test_missing_component_definition_constant_exists`
- [x] `test_si_with_component_reason_returns_description_prompt`
- [x] `test_pending_next_block_set_after_propulsion_complete`
- [x] `test_set_pending_next_block_component_driven_sets_missing_component_definition`
- [x] `test_set_pending_next_block_noop_when_system_not_defined`
- [x] `test_set_frame_material_writes_all_three_locations`
- [x] `test_set_frame_material_mass_only_no_material_key`
- [x] `test_set_frame_material_completeness_high_when_both`
- [x] `test_set_frame_material_does_not_mutate_original`
- [x] `test_physics_uses_frame_mass_when_available`
- [x] `test_component_description_saves_frame_and_recalculates`
- [x] `test_component_description_updates_structure_material`
- [x] `test_si_after_structure_hint_returns_frame_example`
- [x] `test_vague_component_description_stays_interactive`
- [x] `test_structure_block_complete_after_frame_medium`
- [x] `test_proactive_question_for_structure_includes_example`
- [x] `test_criterio_frame_in_natural_language_saved_correctly` *(CRITERIO 1+2)*
- [x] `test_criterio_total_mass_changes_vs_factor` *(CRITERIO 3)*
- [x] `test_criterio_block_progress_complete_after_frame` *(CRITERIO 4)*
- [x] `test_criterio_no_llm_called_in_component_flow` *(CRITERIO 5)*

---

#### Desajustes conocidos en datos en disco (verificados en `state.json`)

> Verificación realizada sobre el proyecto `dron-con-peso-de-2kg-2b61eb3f9a28`. No son bloqueadores de Fase 2.

**D1 — `iter_N.json` no persistía `design_properties` → ✅ Cerrado 2026-08-06**

Los snapshots de iteración (`iterate`, `iterate_declarative`, `params_defined`, `dse_apply`, `create_project`) incluyen `design_properties` + `current_parameters` para rollback auditable.

**D2 — `structure.material: "aluminio"` es un default del schema, no un valor declarado por el usuario**

Este valor proviene del default de `StructureProperties`, no de ninguna acción del usuario. Cuando `_build_mutable_state` lo lee, lo interpreta como si el usuario hubiera elegido aluminio.

**Regla para Fase 3:** antes de migrar la lectura a `components["frame"].properties["material"]`, verificar que `completeness != "low"`. El fallback de último recurso debe ser `"aluminio"` explícito, no el mirror de `structure.material`.

---

#### Lo que no cambia

- `calculation_engine.build()` — sin modificar. El override llega via `current_parameters`.
- `structure_mass_factor` — sigue activo como fallback cuando no hay frame definido.
- `_build_mutable_state` en `iterate.py` — sigue leyendo `design_properties.structure.material` (el mirror garantiza compatibilidad).
- Bloques param-driven (propulsion, energy) — sin tocar.
- Schema — sin campos nuevos.

---

### Fase 2.5 — Control (ComponentRule mínimo) (AHORA)

> Implementar inmediatamente después de Fase 2 validada. Solo UX — cero impacto en cálculo.

**Objetivo:** `"Pixhawk 4 + GPS M9N"` → componente guardado. Sin esto el cuarto bloque del dron cae al LLM y la promesa de "te guío hasta completar" se rompe.

**`jarvis/domains/aerial.py`**
- [ ] `FLIGHT_CONTROLLER_MAP` + `GPS_MAP` — normalización de texto a canónico
- [ ] `extract_flight_controller_properties(normalized) → dict[str, PropertyValue]`
- [ ] `extract_sensor_properties(normalized) → dict[str, PropertyValue]`
- [ ] `_flight_controller_completeness` + `_sensor_completeness`
- [ ] `ComponentRule` para `flight_controller` en `aerial_registry`
- [ ] `ComponentRule` para `sensors` en `aerial_registry`

**Tests:**
- [ ] `test_extract_fc_pixhawk4`, `test_extract_fc_unknown`
- [ ] `test_extract_sensors_gps_only`, `test_extract_sensors_gps_and_imu`
- [ ] `test_control_block_complete_after_both_components`
- [ ] `test_control_block_in_progress_with_only_fc`
- [ ] `test_aerial_registry_matches_pixhawk_keyword`, `test_aerial_registry_matches_gps_keyword`

---

### Fase 3 — Single Read Point (Objetivo principal)

**Condición de activación: Fase 2 + 2.5 + 2.6 + 2.6.1 implementadas y validadas.**

**Objetivo:** Convertir `components` en fuente única de verdad tanto para escritura como para lectura, introduciendo una capa de acceso canónica (getters) antes de eliminar cualquier mirror legacy.

El sistema ya tiene Single Write Point ✅ (`_set_frame_material`, `_set_battery_component`).
Lo que falta: Single Read Point ❌ — múltiples callers pueden leer de sitios distintos.

#### Inventario real de sitios de lectura (estado actual)

**`structure.material` — sitios activos:**
| Sitio | Tipo | Migrar en Fase 3 |
|---|---|---|
| `actions/iterate.py:339` | **FÍSICA** — alimenta `_build_mutable_state` | ✅ sí |
| `orchestrator.py:204` | Display (startup context) | cosmético — opcional |
| `orchestrator.py:1568` | Display | cosmético — opcional |

**`battery_capacity_wh` — sitios activos:**
| Sitio | Lee desde | Estado |
|---|---|---|
| `calculation_engine.py:144` | `current_parameters` | ✅ limpio — no necesita migración |
| `design_explorer.py` | `current_parameters` | ✅ limpio (G1 gap documentado aparte) |

> `simulator`, `reasoning_layer` y `design_explorer` no leen directamente de `components` — leen de `current_parameters` → `CalculationResult`. La cadena es clean. El único sitio de divergencia activo que necesita migración es `iterate.py:339`.

#### Secuencia de implementación (5 commits)

**Commit 1 — Crear capa de lectura canónica en `design_utils.py`**

No condicional. Debe existir antes de migrar ningún caller. En `jarvis/utils/design_utils.py` (no en `orchestrator.py` — problema de dependencia de módulos).

```python
def get_frame_material(design_properties) -> str:
    """Lectura canónica de material del frame. Único punto de lectura."""
    frame = design_properties.components.get("frame")
    if frame and frame.completeness != "low" and "material" in frame.properties:
        return frame.properties["material"].value or "aluminio"
    return "aluminio"  # fallback explícito — nunca leer structure.material (default silencioso)

def get_frame_mass_kg(design_properties) -> float | None:
    """Lectura canónica de masa del frame."""
    frame = design_properties.components.get("frame")
    if frame and frame.completeness != "low" and "mass_kg" in frame.properties:
        return float(frame.properties["mass_kg"].value)
    return None

def get_battery_capacity_wh(design_properties) -> float | None:
    """Lectura canónica de capacidad de batería."""
    battery = design_properties.components.get("battery")
    if battery and battery.completeness != "low" and "battery_capacity_wh" in battery.properties:
        return float(battery.properties["battery_capacity_wh"].value)
    return None
```

**Commit 2 — Migrar todas las lecturas físicas al getter**

Mínimo obligatorio (los cosmético en orchestrator.py son opcionales):

```python
# actions/iterate.py:339 — CRÍTICO (física real)
# Antes:
material = structure.material or "aluminio"
# Después:
from jarvis.utils.design_utils import get_frame_material
material = get_frame_material(design_properties)
```

**Commit 3 — Tests de coherencia de lectura (definición de Fase 3 correcta)**

Test clave — si pasa, Single Read Point está implementado:

```python
def test_getter_wins_over_mirror_when_inconsistent():
    """components["frame"].material gana sobre structure.material cuando divergen."""
    # Simular inconsistencia: components dice carbon, mirror dice aluminio
    dp = build_design_properties_with_frame(material="carbon_fiber")
    dp_inconsistent = dp.model_copy(
        update={"structure": dp.structure.model_copy(update={"material": "aluminio"})}
    )
    assert get_frame_material(dp_inconsistent) == "carbon_fiber"  # components gana
```

**Commit 4 — Auditoría y validación sistema completo**

Verificar con grep que no quedan lecturas de `structure.material` en paths de física (no display):
```bash
grep -rn "structure\.material" jarvis/ --include="*.py" | grep -v "test_\|docs/\|#"
```
Expected: solo orchestrator display (líneas 204, 1568) y la escritura del mirror (línea 795). Si aparece cualquier otra línea en path de física → migrar antes de continuar.

**Commit 5 — Eliminar mirror (solo después de Commits 1-4 validados)**

Eliminar el bloque `# Mirror legacy: structure.material` en `_set_frame_material` y el TODO. El campo `design_properties.structure.material` puede mantenerse en schema por compatibilidad de `state.json` en disco, pero ya no se escribe ni se lee en lógica nueva.

> ⚠️ **Regla:** El mirror protege lecturas legacy no detectadas. No eliminar hasta que el Commit 4 confirme que no quedan readers en paths físicos.

#### Variables adicionales Fase 3 (estructura avanzada):
```python
Frame:
    arm_length_m: float  # → momento de inercia (proxy de estabilidad)
    stiffness: "low" | "medium" | "high"  # cualitativo
```

Desbloquea: DSE sobre estructura, trade-offs reales en `ReasoningLayer`, sugerencias inteligentes.

---

### Fase 4 — Energy como componentes ✅ COMPLETADA

> Implementada: 23 abril 2026. 1165 tests passing (+27 vs Fase 3). 0 regresiones.

**Objetivo cumplido:** battery y motors son componentes físicos reales. Energy block es `"composite"`: requiere AMBOS `components["battery"]` y `components["motors"]` con completeness > "low", más los params mirror en `current_parameters`.

**Implementado:**
1. `[x]` `extract_motor_properties` extendido + `_motor_completeness` en `aerial.py`
2. `[x]` `_set_motor_component()` helper en `orchestrator.py` (único punto de escritura)
3. `[x]` `BLOCK_TYPE["energy"] = "composite"` + `BLOCK_TO_COMPONENTS["energy"] = ["battery", "motors"]`
4. `[x]` `get_motor_power_w()` getter en `design_utils.py` (Single Read Point completo)
5. `[x]` Dispatch `motors` en `_handle_component_description` (orchestrator)
6. `[x]` 27 tests en `test_motor_component.py` (extractor, completeness, setter, getter, composite backward-compat, end-to-end dispatch)
7. `[x]` `COMPONENT_MIRRORED_PARAMS` frozenset en `system_architecture_catalog.py` (invariante formal)
8. `[x]` DA-MOTORS-2 documentada + SYSTEM RULE en catálogo

**Audit `motor_power_w` write sites — VERIFICADO (23 abril 2026):**
```bash
grep -rn "motor_power_w" jarvis/ --include="*.py"
```
- ✅ `orchestrator.py:920/922` — único write, dentro de `_set_motor_component()` ← correcto
- ✅ `calculation_engine.py:145` — solo lectura (`parameters.get(...)`) ← correcto
- ✅ `design_explorer.py:54-55` — usa `motor_power_w_factor`, concepto distinto ← OK
- ⚠️ **Bypass latente documentado como D4** — ver sección Deuda Técnica

**Modelo de fuentes de verdad — IMPLEMENTADO:**

| Campo | Rol | Helper |
|---|---|---|
| `components["battery"].properties["battery_capacity_wh"]` | **CANÓNICO** | `_set_battery_component()` |
| `current_parameters["battery_capacity_wh"]` | **MIRROR** | escrito por mismo helper |
| `components["motors"].properties["power_w"]` | **CANÓNICO** | `_set_motor_component()` |
| `current_parameters["motor_power_w"]` | **MIRROR** | escrito por mismo helper |

---

### Fase 6 — Propulsion como bloque composite ✅ COMPLETADA

> Implementada: 27 abril 2026. 1184 tests passing (+11 vs Fase 5). 0 regresiones.

**Objetivos cumplidos:**
- DA-MOTORS-3 resuelto: `current_parameters["motors"]` → `"motor_count"` (remap en `workspace_manager.py`)
- DA-MOTORS-2 mitigado: `components["motors"]` (component key) separado de `"motor_count"` (param key)
- `BLOCK_TYPE["propulsion"] = "composite"` con componentes `["motors", "propellers"]`
- Wizard Phase A (define motors + propellers) / Phase B (define motor_count + per_motor_max_thrust_n)
- `_set_propeller_component()` — dispatcher para descripciones de hélices
- `_BLOCK_COMPONENT_HINTS["propulsion"]` — hint UX Phase A
- `parameter_requirements.py`: `motor_count` con aliases `("motores", "num_motores", "motors")`
- `calculation_engine.py`: `motors = parameters.get("actuator_count") or parameters.get("motor_count")`

**Tests añadidos (+11):**
1. `test_propulsion_block_type_is_composite`
2. `test_propulsion_components_are_motors_and_propellers`
3. `TestSetPendingNextBlockPropulsionComposite` (4 tests)
4. `TestPropellersDispatcher` (2 tests)
5. `TestBuildStartupContextPropulsion` (3 tests)
6. `TestPropulsionCompletesAfterBothComponents` (1 test)

**DA resueltos:**
- DA-MOTORS-3 ✅ (`motor_count` en params, `motors` en API/components)
- DA-MOTORS-2 ✅ mitigado (ownership via remap + naming separation)

---

### Fase 5 — Wizard dinámico para bloques composite

> Implementada: 24 abril 2026. 1173 tests passing (+8 vs Fase 4). 0 regresiones.

1. [x] `_set_pending_next_block`: rama `composite` con Phase A (componentes) / Phase B (params)
2. [x] Suprimir señal `missing_energy_parameters` en Phase A (composite con componentes ausentes)
3. [x] `build_startup_context`: rama `composite` con hint correcto por fase
4. [x] `_BLOCK_COMPONENT_HINTS["energy"]` añadido para Phase A hint
5. [x] `test_composite_wizard_flow.py` (8 tests: 4 × `_set_pending_next_block` + 4 × `build_startup_context`)
6. [x] `test_frame_component.py` línea 122 actualizada (MISSING_ENERGY_PARAMETERS → MISSING_COMPONENT_DEFINITION)
7. [x] `test_control_component.py::test_criterio_control_complete_advances_to_next_block` actualizado (energy composite Phase A es el comportamiento correcto)

**Fuera de scope Fase 5 (→ Fase 6):**
- `propulsion → "composite"`: bloqueado por DA-MOTORS-3 (naming collision) + DA-MOTORS-2 (ownership vs dependencia)
- `set_param()` gatekeeper para `COMPONENT_MIRRORED_PARAMS` (D4)

---

### Fase K — Validación end-to-end y correcciones de flujo real ✅ COMPLETADA

> Implementada: 29 abril 2026. 1213 tests passing. 0 regresiones.
> Contexto: primera sesión de validación end-to-end con proyecto nuevo real (dron, payload 2kg, flujo CLI completo).

**Objetivo cumplido:** Desbloquear el flujo completo de onboarding — energía, propulsión y frame definibles sin bloqueos ni LLM innecesario. Correcciones de Bugs 59–62 detectados en CLI real.

**K1 — Bridge de params mirrored (Bugs 59+60)**
- `[x]` `core/param_definition_session.py` — `apply_and_recalculate()`: bridge `battery_capacity_wh`, `motor_power_w`, `propeller_diameter_in` → writers de componentes. Sin este fix, los valores se guardaban en `current_parameters` pero no en `components[*].properties` → coherencia invariante rota.

**K2 — Normalización alias `motors → motor_count` (Bug 63)**
- `[x]` `core/state_manager.py` — `load()`: remap idempotente `motors → motor_count` al deserializar `state.json`. Cubre proyectos legacy en disco.
- `[x]` `core/param_definition_session.py` — `apply_and_recalculate()`: normalización en entrada. Cubre callers futuros.
- Nota impl.: `{**d, k: d.pop(k)}` no funciona (el `**` spread ocurre antes del pop); se usa `dict(d)` + `pop` en secuencia.
- 2 tests: `test_load_normalizes_legacy_motors_alias` + `test_motors_alias_normalized_in_apply_and_recalculate`

**K3 — Mensaje `in_progress` diferenciado por tipo de bloque (Bug 61)**
- `[x]` `core/orchestrator.py` — nuevo `_component_is_low(component)`: fuente única de verdad para el umbral de completeness. Reemplaza 3 ocurrencias inline de `(component.completeness or "low") == "low"`.
- `[x]` `core/orchestrator.py` — nuevo `get_block_in_progress_reason(state, block) → "missing_components" | "missing_params"`: fuente única de verdad para la causa de `in_progress` en bloques composite.
- `[x]` `core/orchestrator.py` — `build_startup_context`: rama `in_progress` diferenciada. Composite con componentes ausentes → `"declara los componentes necesarios"`. Resto → `"define los parámetros que faltan"`.
- 5 tests en `test_composite_wizard_flow.py` (3 × `TestGetBlockInProgressReason` + 2 × `TestBuildStartupContextInProgressMessage`)

**K4 — Intercept por presencia de propiedades, no completeness (Bug 62)**
- `[x]` `core/orchestrator.py` — `_should_intercept_component`: guard 2 cambiado de `completeness != "low"` → `not spec.properties`. Guard 3 nuevo: frases interrogativas (`que/qué/cual/cuál/¿`) → LLM.
- **Principio arquitectónico establecido:** `calidad ≠ utilidad` — `completeness` mide si el componente es físicamente suficiente; `properties` mide si hay señal para actuar. Las decisiones del sistema no deben depender de etiquetas de calidad.
- `_frame_completeness` no cambiada — material-only sigue siendo `"low"` semánticamente (correcto).
- 3 tests en `TestFrameMaterialOnlyIntercept` (test_frame_component.py)

---

## 🧱 TIPOS DE BLOQUE

> Prerrequisito de Fase 4. Implementado en Fases 4 y 6. Estado actualizado a 3 junio 2026.

### Estado actual (implementado)

| Bloque | Tipo actual | Implementado en |
|---|---|---|
| `propulsion` | `"composite"` — motors + propellers | ✅ Fase 6 |
| `actuation` | `"param"` | — |
| `energy` | `"composite"` — battery + motors | ✅ Fase 4 |
| `structure` | `"component"` | — |
| `control` | `"component"` | — |
| `transmission` | `"param"` | — |
| `perception` | `"component"` | — |
| `communication` | `"component"` | — |

### Estado real en `system_architecture_catalog.py`

```python
BLOCK_TYPE: dict[str, str] = {
    "propulsion":    "composite",   # Fase 6: motors (component) + propellers (component) + params
    "actuation":     "param",
    "energy":        "composite",   # Fase 4: battery (component) + param_reason coherente
    "structure":     "component",
    "control":       "component",
    "transmission":  "param",
    "perception":    "component",
    "communication": "component",
}
```

**Regla:** `BLOCK_REQUIREMENTS` **no se crea**. Sería una tercera fuente de verdad que duplica `BLOCK_TO_PARAM_REASON` + `BLOCK_TO_COMPONENTS`.

### Fallback obligatorio

```python
block_type = BLOCK_TYPE.get(block, "component")  # fallback: component-driven
```

Sin fallback: bloque custom → `None` → ninguna rama en `_block_progress_status` → retorno implícito `None` → crash silencioso en `_next_pending_block`.

### Rama composite en `_block_progress_status`

```python
elif block_type == "composite":
    param_reason = get_param_reason_for_block(block)
    params_ok = ...  # igual que branch param
    component_keys = BLOCK_TO_COMPONENTS.get(block, [])
    components_ok = all(
        k in components and components[k].completeness != "low"
        for k in component_keys
    )
    if not params_ok and not components_ok:
        return "not_started"
    if params_ok and components_ok:
        return "complete"
    return "in_progress"
```

---

## 🔮 EVOLUCIÓN DIFERIDA

> Condición de activación explícita por ítem. No implementar hasta que la condición esté documentada.

### Rediseño `create_project` por ramas

**Condición: datos reales de validación CLI documentados.** ✅ Cumplida (Fase N).  
**Implementado: 5 agosto 2026.** 1331 tests passing (+11).

- [x] `CreateProjectInteractiveSession` con ramas por `vehicle_type`. Tronco siempre: `vehicle_type`, `objective`, `payload_kg`, `restrictions`, `detail_level`.
- [x] Rama aérea: preguntar `motors`, luego bifurcar (empuje declarado / hélices / no sé aún).
- [x] Rama terrestre: preguntar `actuator_count` (campo `motors` en draft), luego bifurcar (torque / fuerza directa / no sé aún).
- [x] `structure_mass_factor` y `safety_factor` mantienen defaults — no preguntar salvo `detail_level=detallado`.

→ Tests: `tests/test_create_project_branches.py`. Steps: tronco 0–4, detallado 5–6, aéreo 10–14, terrestre 20–23, confirmación 90.

### Evolución de arquitectura

**Condición: caller real genera confusión semántica documentada.**

- [ ] Renames destructivos diferidos: `can_fly → constraints_satisfied`, `motors → actuators`, `vehicle_type → system_type`.
- [ ] Planner v1 con más tipos de secuencias y validaciones.
- [ ] `ReasoningLayer` + `DependencyGraph`: insights causales requieren canal de señales estructurales.
- [ ] `next_underdefined_block(state)` en `PriorityEngine`: orden dinámico según parámetros actuales.

### Extensiones de conocimiento

- [ ] Integrar knowledge/RAG para contexto técnico en `analyze`.
- [ ] Ampliar tipos de conflicto y hints de memory.
- [ ] Memoria de patrones de usuario ("palas" → "propellers").

### Extensiones de capacidad física

- [ ] Modelo físico de hélice nivel 2 (Ct variable, curva de empuje).
- [ ] Modelo energético con curva de descarga y C-rating.
- [ ] Más tools de ingeniería reutilizables en `tools/`.

---

## 🧨 DEUDA TÉCNICA

> Latente, no urgente. No diseñar antes de la fase indicada.

| ID | Problema | Bloqueante en |
|---|---|---|
| D1 | `iter_N.json` no persiste `design_properties` — rollback borra frame sin reflejo en historial | **Cerrada 2026-08-06** — snapshots incluyen `design_properties` + `current_parameters` |
| D2 | `structure.material = "aluminio"` es default silencioso del schema — `_build_mutable_state` lo lee como declarado | Fase 3 (migración de lectura) |
| ~~D3~~ | ~~módulo `design_utils.py` no existe~~ → **✅ Cerrado** — `jarvis/utils/design_utils.py` existe (`get_frame_material`, etc.). Revisado 2026-08-06. | — |
| ~~D4~~ | ~~Bypass de mirrors via signal de params~~ → **✅ Cerrado** — gatekeeper `COMPONENT_MIRRORED_PARAMS` en `param_definition_session` + writers; tests `test_d4_param_gatekeeper.py`. Revisado 2026-08-06. | — |
| ~~D5~~ | ~~Avance silencioso de bloque composite~~ → **Mitigada 2026-08-06** — hint `✓ Bloque completado` al pasar a complete | — |
| ~~D6~~ | ~~Dualidad física de `propellers` sin bridge~~ → **✅ Cerrado (U2)** — `set_propeller_component()` puentea `propeller_diameter_in` (+ pitch) a `current_parameters`; tests `test_u2_propeller_bridge.py`. Revisado 2026-08-06. | — |
| ~~D7~~ | ~~Frases mixtas first-match-wins~~ → **Cerrada 2026-08-06** — `infer_components` + loop en handler | — |
| ~~D8~~ | ~~Catálogo motores solo por KV~~ → **Cerrada 2026-08-06** — `design_space` + `find_motors_for_requirements` + hueco honesto | — |

---

## ⚪ FUTURO (SIN DISEÑAR)

> Solo registro de existencia. No implementar, no diseñar hasta que un caso de uso real lo justifique.

- `perception` → `cameras`, `lidar` — sin ComponentRule, sin physics
- `communication` → `radio_module` — sin ComponentRule
- `manipulation` → `arm` — sin ComponentRule
- `payload` → `payload_bay` — sin ComponentRule
- `actuation` / `transmission` — parcialmente cubiertos por wizard param-driven terrestre; sin component spec

---

## 🧠 REGLA MAESTRA DEL SISTEMA

```text
LLM propone → ActionPolicy valida → SemanticIntentAdapter filtra → Orquestador enruta → Motores ejecutan
```

- LLM → interfaz semántica, nunca ejecutor.
- Orquestador → control de flujo.
- Engines → ejecución técnica determinista.
- Registry (`PARAMETER_REQUIREMENTS`) → árbitro único de variables modificables.
- Acciones simples → ejecución directa. Objetivos compuestos → planner.

---

## ✅ COMPLETADO

### Núcleo del sistema

- [x] Definir contratos estructurados para acciones, estado y resultados.
- [x] Implementar `action_router` y `orchestrator`.
- [x] Implementar `state_manager` con estado temporal de runtime y estado persistente de proyecto.
- [x] **Workspace v2 — separación estado / historia / vistas**: `views/`, `history/iterations/`, `history/simulations/`, `history/calculations/`, `history/events.jsonl` y `meta/`. `state.json` es la única fuente de verdad. Vistas regeneradas automáticamente tras cada acción. Log `events.jsonl` append-only. Iteraciones en JSON estructurado (change + mutation + impact + calculations + simulation). Ver `workspace/workspace_manager.py` y `workspace/render_views.py`.
- [x] **Hardening de `state.json`** — separación de responsabilidades por campo:
  - `current_parameters` = inputs del usuario al motor de cálculo; no incluye propiedades físicas derivadas ni slugs.
  - `design_properties.structure` = fuente canónica de `material`, `density`, `volume`. `_build_mutable_state` lee aquí con fallback a `current_parameters` para retrocompat.
  - `parsed_constraints: dict[str, float]` — restricciones parseadas a tipo fuerte via `@model_validator`. El simulador recibe `float | None`, nunca texto libre.
  - `project_slug` excluido de `current_parameters` via `_PARAMS_NOT_CALC_INPUTS`.

### Motores deterministas

- [x] Implementar tools base para masa, peso y empuje.
- [x] Implementar `calculation_engine` reutilizable.
- [x] Implementar `mutation_engine` determinista para iteraciones.
- [x] Implementar `simulator v1+` con `safety_margin_ratio`, `thrust_to_weight_ratio`, `per_motor_load_ratio`, `quality = fail | risky | acceptable | good`, `warnings` deterministas, `physics_status: Literal["valid", "missing_parameters"]`, `energy_status`, `propeller_status: Literal["valid", "missing_propeller_parameters"]` y `propeller_thrust_inferred`.
- [x] Implementar `suggestion_engine` v0 determinista y de solo lectura.
- [x] **Dominio energético**: `calculate_autonomy_min(battery_capacity_wh, total_power_w)` en `tools/electricity.py`. `energy_status` + `autonomy_min` en `SimulationResult`. Engine traza `missing_energy_parameters` si faltan parámetros.
- [x] **Dominio aerodinámica** — inferencia de thrust desde hélice: `calculate_thrust_from_propeller(diameter_m, rpm, ct=0.12)` en `tools/aerodynamics.py`. Tercera ruta de resolución del engine (prioridad: declarado > torque > hélice). Señal `propeller_thrust_inferred` en reasoning.
- [x] **Dominio terrestre** — `torque → force`: `calculate_traction_force_from_torque(torque_nm, wheel_radius_m, gear_ratio)` en `tools/mechanics.py`. Ruta terrestre completa. Sin conversión posible → `missing_transmission_parameters` en trace sin excepción.
- [x] **`physics_status` expuesto a reasoning**: cuando `physics_status == "missing_parameters"`, `ReasoningLayer` genera insight + tradeoff + suggested action con los parámetros concretos ausentes. Helper `_detect_missing_physics_params` lee `current_parameters`.
- [x] **`parameter_requirements.py`**: catálogo declarativo único que mapea `reason_code → parámetros → labels/hints/keywords`. Consumido por `ReasoningLayer`, `ParamDefinitionSession`, `main.py` y `simulator.py`. Incluye `MISSING_PROPELLER_PARAMETERS`, entrada `propeller_rpm` con keywords y `REQUIREMENT_REASONS["missing_propeller_parameters"]`. Añadir un nuevo dominio de conversión = extender el catálogo, no duplicar lógica.

### Acciones

- [x] Implementar `create_project` (directo e interactivo).
- [x] Implementar `calculate` sobre proyecto persistido.
- [x] Implementar `simulate` sobre proyecto persistido.
- [x] Implementar `iterate` con mutación, recálculo, simulación y persistencia.
- [x] Soportar iteraciones declarativas `define` para propiedades de diseño sin recálculo físico.
- [x] **`create_project` sin valores ficticios**: `per_motor_max_thrust_n` y `motors` opcionales en `CreateProjectParams`. `build_execution_payload()` sin defaults inventados — pasa `None` si el usuario no lo declaró.

### Flujos interactivos

- [x] Implementar `create_project_interactive` con `project_draft` temporal.
- [x] Implementar `iterate_interactive` con `iteration_draft` temporal.
- [x] Exigir confirmación antes de ejecutar cambios reales.
- [x] **`_handle_global_commands`**: primer check incondicional en `handle_user_text`. Comandos `cancelar/cancel/salir/abortar` → limpia sesión activa. Comandos `n/nuevo` → `create_project` sin LLM. La CLI es un adaptador I/O puro.

### Wizard iterate — integridad de inputs

- [x] **Gap 1 — Material explícito**: cuando `variable=material` y la estrategia no contiene un nombre conocido, la sesión pregunta explícitamente. `draft.value` queda con el nombre canónico (`_KNOWN_MATERIALS`, `_extract_material_from_text`, `_awaiting_material_value`).
- [x] **Gap 2 — Downgrade estructural**: iteraciones con variable estructural sin valor concreto se degradan a `DEFINE` con mensaje explicativo (`_should_downgrade_to_declarative`). `mutation_engine` DEFINE genérico devuelve `({}, {})` en lugar de `raise ValueError`.
- [x] **Gap 3 — Parámetros numéricos directos**: cuando la variable es un parámetro numérico en `current_parameters` (`factor_estructura`, `motors`, `safety_factor`...), el wizard pregunta directamente el nuevo valor sin pasos intermedios. Detección dinámica via `_match_numeric_param`. `apply_numeric_param_mutation` en `mutation_engine`. Elimina `structure_mass_override_kg` si se toca `structure_mass_factor`.
- [x] **Clasificación de tipo de variable** (`_classify_variable_type`): 7 categorías (`semantic_mutation`, `numeric_direct`, `material`, `structural_physical`, `structural_abstract`, `component_define`, `unknown`). Gobierna el texto de la pregunta en paso 2 — no la ejecución. La gate física sigue siendo `mutation_engine.is_physically_actionable()`.
- [x] **Sub-loop `pending_entities`**: cuando el usuario menciona varios componentes a la vez, el sistema pregunta por cuál empezar y procesa los restantes en el sub-loop.
- [x] **Enriquecimiento cruzado de sesión**: `"completar especificación del motor"` extrae `enrich_component`, carga `known_components` desde `design_properties` y arranca el wizard en paso 2 con focus preseeded.

### Bridge declarativo → físico

- [x] **`component_resolver` operativo**: overrides efímeros `motors` y `per_motor_max_thrust_n` aplicados antes de `calculation_engine.build()`. Trazabilidad en `propulsion_override_trace`. Sin persistencia, sin heurísticas de texto.
- [x] **Resolver multi-magnitud** (`output_magnitude`): elegibilidad y resolución de fuerza parametrizadas. `thrust_n` para aéreo, `torque_nm` para terrestre.
- [x] **Trace completo del resolver**: tres categorías excluyentes — `force_resolved` / `missing_parameters` / `count_only`. `force_resolution_detail` incluye campo `reason` por componente.
- [x] **Arquitectura multi-dominio**: `ComponentRuleRegistry`, `domains/aerial`, `domains/ground`, `registry_selector` con routing 3 niveles (vehicle_type → heurística texto → default aéreo). Hooks en `mutation_engine` e `iterate_interactive_session`.
- [x] **Persistencia de dominio** (`vehicle_type`): gaps en `actions/iterate.py` y `orchestrator.py` cerrados.
- [x] **Biblioteca de motores** (`knowledge/library.py`): `ComponentLibrary`, `MotorSpec`, selección interactiva — modelo exacto → datos directos; KV genérico → sugerencia, nunca auto-apply.

### Arquitectura del sistema — definición contextual

- [x] **`SystemDefinitionSession`**: transición de "parámetros sueltos" → "arquitectura estructurada". Se lanza post-`create_project`. Puebla `design_properties.components` con stubs declarados antes de cálculo/iteración. Step 0 (opciones A/B/C) y step 1 (modo B personalizado). Merge seguro con prioridad `source: user > inferred > declared` y `completeness: high > medium > low`.
- [x] **`system_architecture_catalog.py`**: módulo de datos puros. `SYSTEM_ARCHITECTURES`, `BLOCK_TO_COMPONENTS`, `BLOCK_ALIASES`, `BLOCK_TO_PARAM_REASON`. Bridge paramétrico basado en `BLOCK_TO_PARAM_REASON`, no en heurística de nombres.
- [x] **`DependencyGraph` + `PriorityEngine`**: `system_dependency_catalog.py` por dominio (`dron`, `uav`, `robot`, `coche`, `rover`). `build_dependency_graph(vehicle_type, blocks)`. `compute_priority_order(graph)` — DFS topológico con detección de ciclos sin crash. `system_priority: list[str]` persistido en `DesignProperties`.
- [x] Estado persistido: `design_properties.system_defined: bool`, `system_blocks: list[str]`, `system_priority: list[str]`.
- [x] Bridge automático `SYSTEM_DEFINITION → DEFINE_MISSING_PARAMETERS` en orquestador.

### Capa LLM e intérprete semántico

- [x] Schema fuerte `LLMActionRequest` + `response_parser` con validación Pydantic strict.
- [x] `ActionPolicy` centraliza reglas de runtime (acciones permitidas, sesión activa, modo interactivo, variable en registry).
- [x] `PromptBuilder` con system prompt que inyecta `build_action_space()` completo. Operaciones documentadas: `increase | reduce | define | improve | optimize`. Action Space construido una vez al importar.
- [x] `JarvisLLMInterface` pluggable con `OllamaClient`. Doble modo: `json_mode=True` para acciones, `json_mode=False` para `analyze`.
- [x] Safe fallback para salidas inválidas. Logging estructurado en `runtime/llm_logs/` con schema idéntico en éxito y error. Versionado de prompt.
- [x] Intent resolver híbrido con intents `analyze`, `ambiguous`, `project_status` y precedencia por intención fuerte (`acción fuerte > analyze`).
- [x] **`SemanticIntentAdapter`**: única puerta entre output LLM y wizard iterate. Resolución de variable en 4 pasos (canonical → normalizado → alias → concepto). `AdaptRejection` para variables derivadas (con `redirect_message` del registry) y desconocidas. `_parse_value()` sanitiza strings con unidades (`"800 Wh"` → `"800"`, `"mucho"` → `None`). Threshold: `CONFIDENCE_THRESHOLD = 0.75`.
- [x] **`ActionPolicy._validate_iterate_variable`**: rechaza variables ausentes del registry antes del adapter. Variables derivadas pasan — el adapter genera mensaje rico.
- [x] **`orchestrator._semantic_preseed`**: confidence ≥ 0.75 → wizard preseed paso 2; variable derivada → `derived_redirect_message` en paso 0; demás → wizard normal paso 0.
- [x] **`llm_client._build_semantic_trace`**: loguea `{variable, confidence, routing}` por cada evento iterate. Routing values: `preseed_step2 | fallback_wizard | rejected_derived | rejected_unknown | n/a`.
- [x] Historial conversacional ligero (`ConversationTurn`, máx 6 turnos) inyectado en `analyze` y fallback LLM. No persiste en disco. Se limpia al cargar proyecto nuevo.

### Reasoning v0

- [x] `ReasoningOutput` + `ReasoningSuggestion` como contrato estructurado.
- [x] `core/reasoning_layer.py` determinista: señales → insights/tradeoffs → explicación/siguientes pasos. Señales: `missing_physics_parameters` (suprimida por `missing_propeller_parameters`), `declarative_context`, `missing_energy_parameters`, `propeller_thrust_inferred`, `missing_propeller_parameters`.
- [x] Integrado en `analyze`, `simulate` e `iterate` sin modificar motores.

### UX e interacción

- [x] **`build_startup_context()`**: snapshot operativo sin LLM. Jerarquía 4 niveles (`blocking → warning → nominal → no_data`). `active_variables` (máx 3), `suggested_action` + hint, `phase`/`phase_description`/`phase_confidence`, `proactive_question` + `missing_params` cuando blocking. Única fuente de verdad — startup display y consultas on-demand usan el mismo builder.
- [x] **`PhaseLayer`**: 4 fases deterministas (`definition`, `physical_validation`, `optimization`, `complete`). Reglas en prioridad estricta. Reutiliza `HIGH_MARGIN_THRESHOLD` de `reasoning_layer`.
- [x] **`project_status` intent**: `STATUS_PATTERNS` separado. Se evalúa antes que `_looks_like_question()` — consultas de estado nunca entran por `analyze`.
- [x] **`DEFINE_MISSING_PARAMETERS`**: modo de recolección proactiva de parámetros numéricos sin LLM. `ParamDefinitionSession` con parser semántico (keywords en `parameter_requirements.py`) + fallback posicional. `param_definition_reason` identifica el origen (`missing_transmission_parameters`, `missing_energy_parameters`, `missing_propulsion_parameters`, `missing_propeller_parameters`).
- [x] Selección de proyecto en CLI acepta texto natural (`"continuar"`, `"el más reciente"`, ordinales escritos) además de dígito.
- [x] CLI mínima `python -m jarvis.main --chat` conectada a Ollama.

### Domain Registry

- [x] **`parameter_requirements.py`** como fuente única de verdad del dominio del wizard: `VariableType` enum (`NUMERIC_DIRECT`, `SEMANTIC_MUTATION`, `NUMERIC`), `ParameterRequirement` con `variable_type`, `aliases`, `concept_aliases`, `display_name`, `is_derived`, `derived_message`, `description`. 8 helpers `build_*`/`get_*`/`normalize_alias`/`validate_registry`. `build_action_space()` listo. `iterate_domain.py` como capa de adaptación (vistas computadas desde el registry).

### Planner v0

- [x] Planner para secuencias cerradas: `create_and_simulate`, `recalculate_and_simulate`, `iterate_and_validate`. Acciones simples se ejecutan directamente desde el orquestador.

### Testing y documentación

- [x] Tests de tools, simulación, `create_project`, wizard interactivo, parser/policy LLM, planner, reasoning, multi-dominio, energía, aerodinámica y pipeline hélice (27 tests en `test_propeller_pipeline.py`).
- [x] Tests de clasificación realista y precedencia (`analyze` vs acciones fuertes). Tests de no-regresión.
- [x] Tests de `SemanticIntentAdapter` (46), `PromptBuilder` action space (8), `ActionPolicy` variable validation (5).
- [x] `README.md` y `ARCHITECTURE.md` alineados con el flujo real. Quickstart reproducible. Tabla entrada→ruta→efecto con routing semántico LLM.

### Dominio aéreo — pipeline hélice activo (Fase 2)

- [x] **Conversión de unidades en engine**: `propeller_diameter_in × 0.0254 → propeller_diameter_m`. `propeller_diameter_m` es el canónico interno; `propeller_diameter_in` es alias de entrada. `_PROPELLER_HINT_PARAMS` frozenset para detección de intent.
- [x] **Intent detection para `missing_propeller_parameters`**: aéreo + hint presente → `missing_propeller_parameters`; aéreo sin hint → `missing_propulsion_parameters`; terrestre → `missing_transmission_parameters`. Tres ramas mutuamente excluyentes en engine.
- [x] **`PropellerStatus` + `propeller_status` en `SimulationResult`**: campo independiente derivado exclusivamente de `tool_results`. No altera `physics_status` ni `warnings`. Patrón simétrico a `energy_status`.
- [x] **`reasoning_layer` — exclusión mutua**: `missing_propeller_parameters` activa → `missing_physics_parameters` suprimida. El usuario ve exactamente qué falta, no un mensaje genérico. `ReasoningSuggestion` con priority 0.99 precede al bloque de física.
- [x] **Proactive collection en orchestrator**: `build_startup_context()` detecta `propeller_status="missing_propeller_parameters"` y emite `proactive_question` con `param_definition_reason=MISSING_PROPELLER_PARAMETERS`.
- [x] **`MISSING_FORCE_REASONS`** ampliado con `MISSING_PROPELLER_PARAMETERS`.
- [x] Tests: `test_propeller_pipeline.py` — 27 tests (conversión, intent detection, simulator, reasoning, orchestrator).

### Human Layer Sprint v1 — capa conversacional

- [x] **Fix 1 — Routing semántico por intención**: `classify_input_intent(text) → "information" | "action" | "hybrid"` en `intent_resolver.py`. Dentro de `ITERATE_INTERACTIVE`, inputs `information` o `hybrid` → `_handle_analyze` incondicional antes del wizard. Elimina el bug donde preguntas informativas abrían el wizard de iteración.
- [x] **Fix 2 — Warnings en lenguaje humano**: `WARNING_MESSAGES: dict[str, str]` en `main.py`. `_human_warning(code)` traduce `low_margin`, `high_actuator_load`, `low_force_to_weight_ratio`, `autonomy_below_restriction` a descripciones en español.
- [x] **Fix 3 — Error de variable desconocida guía al usuario**: cuando el término desconocido coincide con `_COMPONENT_REDIRECT_TERMS`, el mensaje de error añade `" Para definir componentes físicos (hélices, motores, batería, sensores), di 'componentes'."` automáticamente.
- [x] **Fix 4 — DEFINE propulsion_passive informa qué falta**: `_propulsion_passive_hint(draft, current_parameters)` en `actions/iterate.py`. Cuando la iteración es DEFINE + componente `propulsion_passive`, añade `next_step_hint` con los parámetros faltantes del catálogo (`propeller_diameter_in`, `propeller_rpm`) y cómo activarlos. Supresión automática si los parámetros ya están definidos.
- [x] **Fix 5 — Goal Planner híbrido**: `core/goal_planner.py` con `GOAL_STRATEGIES`, `detect_goal(text)`, `_prioritize_strategies(key, strategies, sim_context)`, `format_goal_plan(key, sim_context)`, `get_goal_context_for_llm(key)`. Cuando se detecta un objetivo (`aumentar_payload`, `mejorar_autonomia`, `reducir_masa`, `mejorar_estabilidad`), `_handle_analyze` construye un bloque determinista priorizado por `safety_margin_ratio` + análisis LLM contextual separados por `"─── Evaluación contextual ───"`.
- [x] Tests: `test_goal_planner.py` — 31 tests (detección, plan format, priorización, inyección LLM).

### Decision Layer v1 — Priorización dinámica

- [x] **`blocked` e `is_critical` en schema**: `blocked: bool = False` e `is_critical: bool = False` añadidos a `ReasoningSuggestion` en `schemas/tool_schema.py`. Convierte el schema de "sugerencias" a "decisiones estructuradas".
- [x] **Acciones críticas para `low_margin`**: rama `low_margin` en `_build_suggested_actions` emite `ReasoningSuggestion(is_critical=True, priority=0.99)` con label `"Aumentar empuje disponible"`. Deduplicación si `increase_thrust` ya estaba en la lista.
- [x] **Señal `high_actuator_load`**: `_extract_signals` lee `per_motor_load_ratio` de `last_simulation`; activa cuando ≥ `HIGH_ACTUATOR_LOAD_THRESHOLD = 0.9`. `increase_thrust` del `SuggestionEngine` se marca `is_critical=True` cuando la señal es verdadera.
- [x] **`CONFLICT_RULES` + `_resolve_conflicts`**: tabla declarativa a nivel de módulo con 2 reglas (`low_margin`, `high_actuator_load` bloquean `increase_payload`). `_resolve_conflicts` retorna nuevos objetos vía `model_copy()`, sin mutar en sitio. `_ACTION_TYPE_TO_LABEL` como tabla de traducción type → label para el matching.
- [x] **Render jerárquico en `main.py`**: `render_response()` separa en 3 secciones: `PRIORIDAD CRÍTICA: →`, `Siguientes pasos: -`, `Evitar: ✗`.
- [x] **Fix: `build_startup_context` salta acciones bloqueadas**: `orchestrator.py` usaba `suggested_actions[0]` directamente; ahora usa `next(a for a in ... if not a.blocked)` para no surfacear una acción marcada como `Evitar` en el startup context.
- [x] Tests: 5 nuevos en `test_reasoning_layer.py` — 880 tests passing.

### Design Space Explorer (DSE) — v1

- [x] **`jarvis/core/design_explorer.py`**: `ExplorationCandidate`, `ExplorationResult`, `EXPLORATION_GRIDS`, `_score_candidate(sim, goal_key)`, `DesignExplorer.explore()` — 100% en memoria, sin I/O, usa `calculation_engine.build()` + `FeasibilitySimulator.evaluate()`. Filtra candidatos `can_fly=False`, top-5 viables.
- [x] **`jarvis/core/intent_resolver.py`** — `EXPLORE_PATTERNS` + `resolve_explore_intent(text) → goal_key | None`.
- [x] **`jarvis/core/orchestrator.py`** — routing `intent == "explore_design_space"` → `_handle_explore`.
- [x] Tests en `test_design_explorer.py`: grids, scoring, exploración pura, ranking, filtrado de infeasibles. Tests de integración: mock de engines, verificar que `state` no muta.

**Métricas de ranking:**

| Goal | Métrica principal | Dirección |
|---|---|---|
| `mejorar_autonomia` | `autonomy_min` | maximizar |
| `aumentar_payload` | `safety_margin_ratio × payload_kg` | maximizar |
| `reducir_masa` | `total_mass_kg` | minimizar |
| `mejorar_estabilidad` | `safety_margin_ratio` | maximizar |

---

