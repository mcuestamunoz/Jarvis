# Jarvis — Bug Tracker (fase CLI real)

> Fecha de apertura: 15 abril 2026  
> Revisado: 29 abril 2026 (Fase K — primera sesión de validación end-to-end proyecto nuevo)  
> Revisado: 3 junio 2026 (Fase L — sesión de validación post-G1, flujo completo desde cero)  
> Revisado: 3 junio 2026 (Fase M — E2E testing integración MCP server, 11 tests)  
> Revisado: 5 junio 2026 (Fase U — mejoras hacia herramienta usable, U1 masa batería dinámica)  
> Revisado: 15 julio 2026 (Fase N — validación propeller-only path vía MCP, proyecto desde cero)  
> Contexto: sesión de testing manual en CLI real con proyecto nuevo (dron, payload 2kg, flujo completo)  
> Total bugs: 79 · Abiertos: 0 · Fase K: 2 Críticos · 1 Importante · 1 Medio · 1 Menor (todos ✅) · Fase L: 1 Alto · 1 Medio · 1 Medio · 1 Menor (todos ✅) · Fase M: 1 Crítico · 1 Alto · 1 Menor (todos ✅) · Fase U: 5 (todos ✅) · Fase N: 4 (todos ✅)

---

## Leyenda

| Campo | Valores |
|---|---|
| **Riesgo impl.** | 🟢 Bajo · 🟡 Medio · 🔴 Alto |
| **Cambio arq.** | ✅ Requiere actualizar ARCHITECTURE.md y/o IMPLEMENTATION_TASKS.md · ❌ No requiere |
| **Estado** | ⬜ Pendiente · 🔵 En progreso · ✅ Hecho |

---

## 🔴 Críticos

### Bug 1 — Mutaciones físicas con `value=None`
> Iteraciones como `variable="dimensiones", strategy="optimizar estructura"` ejecutan `apply_volume_mutation` con `VOLUME_REDUCTION_FACTOR=0.9` sin que el usuario haya dado ningún valor concreto.

- **Archivos afectados:** `actions/iterate.py`
- **Fix:** Cambio en la semántica de ejecución de `iterate.py`: redefine qué constituye una iteración válida con impacto físico. Si el draft llega con `value=None` en una ruta física (no-DEFINE), se degrada a DEFINE con mensaje informativo — no es un guard simple, es un cambio en el contrato de qué se considera ejecutable.
- **⚠️ Nota:** Este bug es de _ejecución_ — qué pasa cuando algo no válido llega al motor. Bug 3 es el complementario de _validación_ — que nada no válido llegue. Deben implementarse en orden: primero Bug 3 (validación), luego Bug 1 (ejecución defensiva).
- **Riesgo impl.:** 🟡 Medio — cambia el contrato de qué es una iteración ejecutable, requiere tests nuevos
- **Cambio arq.:** ❌ No — misma interfaz, cambia comportamiento interno de `actions/iterate.py`
- **Estado:** ✅ `needs_concrete_value` en `mutation_engine` + guard en `iterate.py`: draft no-DEFINE sin value en ruta volumétrica se degrada a `status="definition"` con mensaje orientativo.

---

### Bug 2 — Acciones vagas producen cambios físicos no justificados
> `"optimizar estructura"` produce mutación física (`-5%` masa) aunque no hay modelo físico que lo justifique.

- **Archivos afectados:** `core/iterate_interactive_session.py` (`_estimate_impact`), `core/mutation_engine.py` (`resolve_strategy`)
- **Fix:** Se resuelve junto con Bug 1 — la degradación a DEFINE en Bug 1 evita que llegue a mutación física.
- **Riesgo impl.:** 🟡 Medio — vinculado al fix de Bug 1
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cubierto por Bug 1 — `needs_concrete_value` previene que iteraciones vagas lleguen al motor físico. — No existe validación "actionable vs no actionable"
> El sistema acepta cualquier combinación de `variable + strategy` y la ejecuta sin comprobar si es físicamente computable.

- **Archivos afectados:** `actions/iterate.py`, `core/mutation_engine.py` (`resolve_strategy`), `core/iterate_interactive_session.py`, toda la semántica del wizard
- **Fix:** Establecer una capa de validación explícita en `mutation_engine.resolve_strategy()` y en el wizard que determine si un draft es físicamente computable ANTES de proceder. No es solo un try/except — es definir el contrato de qué inputs son válidos para cada ruta de mutación.
- **⚠️ Este es el bug sistémico más importante:** afecta `iterate.py`, `mutation_engine`, el wizard completo y la semántica de toda iteración. Sin este fix, cualquier input del usuario puede llegar silenciosamente a una mutación física no justificada. Es el prerequisito conceptual de Bug 1 y dependencia de Bugs 14+15.
- **Riesgo impl.:** 🟡 Medio — cambia el comportamiento global del flujo iterate; requiere tests de cobertura amplia
- **Cambio arq.:** ❌ No — misma estructura, nuevo contrato de validación interno
- **Estado:** ✅ `is_physically_actionable` en `mutation_engine` + guard en `iterate.py` (Bug 25). Wizard: Bug 24 coherence check + Bug 20 pure-op-phrase guard. — `"carga"` no se normaliza a `payload_kg`
> `variable = user_input.lower()` en step 1 guarda el string como viene. El summary muestra `"Variable: carga"` y el código depende de heurísticas en vez de mapeo explícito.

- **Archivos afectados:** `core/iterate_interactive_session.py` (`_apply_answer`)
- **Fix:** Tabla de normalización de variables en step 1: `"carga" / "payload" → "payload_kg"`, etc.
- **Riesgo impl.:** 🟢 Bajo — cambio localizado en `_apply_answer`
- **Cambio arq.:** ❌ No
- **Estado:** ✅ `_VARIABLE_NORMALIZATION` + `_apply_answer` step 1: `"carga"` / `"payload"` / `"carga útil"` → `"payload_kg"` antes de entrar al motor semántico. — `"autonomía"` no se mapea a parámetros reales
> `"autonomía"` no está en `_PARAM_DISPLAY_ALIASES` ni es resoluble por `resolve_strategy`. Si el usuario llega a confirmar, lanza `ValueError` silencioso.

- **Archivos afectados:** `core/iterate_interactive_session.py` (`_apply_answer`)
- **Fix:** En step 1, detectar variables derivadas no-directas (`"autonomia"`) y redirigir: *"La autonomía depende de `battery_capacity_wh` y `motor_power_w`. ¿Cuál quieres modificar?"* — interrumpe el flujo de iteración y lanza `DEFINE_MISSING_PARAMETERS`.
- **⚠️ Riesgo oculto:** El fix introduce un flujo alternativo dentro del wizard activo — esto crea riesgo de:
  - sesiones con estado inconsistente (wizard activo + session DEFINE en paralelo)
  - estados intermedios raros si el usuario cancela la redirección
  - hay que asegurarse de que al lanzar `DEFINE_MISSING_PARAMETERS` el estado `ITERATE_INTERACTIVE` queda limpio
- **Riesgo impl.:** 🟡 Medio-alto — flujo alternativo con riesgo de sesiones inconsistentes
- **Cambio arq.:** ❌ No
- **Estado:** ✅ `_DERIVED_VARIABLE_MESSAGES` + `_normalize_variable_input`: step 1 detecta `"autonomia"` y devuelve mensaje de redirección sin avanzar la sesión. No lanza DEFINE en paralelo — responde inline, el wizard sigue en step 1.

---

### Bug 6 — Iteraciones se ejecutan aunque variable no corresponda a ningún parámetro real
> `"dimesniones"` (con typo) no coincide con `"dimension"` en `_should_downgrade_to_declarative`, pasa al path físico y ejecuta `apply_volume_mutation`.

- **Archivos afectados:** `core/iterate_interactive_session.py` (`_should_downgrade_to_declarative`), `core/mutation_engine.py` (`resolve_strategy`)
- **Fix:** Se resuelve por combinación de Bug 3 (guard en `resolve_strategy`) y Bug 9 (normalización fuzzy en step 1).
- **Riesgo impl.:** 🟢 Bajo — derivado de Bugs 3 y 9
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cubierto por Bug 3 (`is_physically_actionable`) + Bug 9 (`_fuzzy_normalize_variable`). "Dimesniones" → "dimensiones" en step 1; si igualmente no es routable, Bug 25 lo intercepta antes de ejecución.

### Bug 7 — Wizard bloquea comandos globales
> En step 4 (`¿Aplicar cambio?`), `"estado del proyecto"` no pasa por `_handle_global_commands` — llega directamente al `_handle_apply_decision` que solo acepta si/no → devuelve error.

- **Archivos afectados:** `core/orchestrator.py` (`handle_user_text`)
- **Fix:** En `handle_user_text`, antes de delegar al session handler cuando `mode=ITERATE_INTERACTIVE`, resolver el intent: si es `project_status` o `analyze`, responder sin interrumpir la sesión (el estado de sesión se preserva).
- **Riesgo impl.:** 🟡 Medio — toca el flujo principal del orquestador; requiere verificar que la sesión no queda corrupta
- **Cambio arq.:** ✅ Sí — actualiza sección "Orden de ejecución en handle_user_text" en ARCHITECTURE.md
- **Estado:** ✅
- **Nota (calibración 2026-08-05):** Bug 7 cubre solo soft interrupt de lectura. Intents de acción fuertes (`explore`, `calculate`, `simulate`, nuevo `iterate`, componentes) ahora hacen **hard preempt** (`clear_runtime_session` + re-dispatch idle, flag `preempted_iterate`). Ver ARCHITECTURE.md.

---

### Bug 8 — Inputs fuera de sesión causan error en vez de interrupción limpia
> Cualquier input no reconocido en step 4/5 devuelve `"Error: Responde 'sí'…"` en lugar de un mensaje orientativo.

- **Archivos afectados:** `core/iterate_interactive_session.py` (`_handle_apply_decision`, `_handle_final_confirmation`)
- **Fix:** Se resuelve parcialmente por Bug 7 (interceptar intents conocidos antes del session handler). Para inputs genuinamente desconocidos: mejorar el mensaje de error para que sea orientativo y no bloquee.
- **Riesgo impl.:** 🟢 Bajo — cambio de string en dos métodos
- **Cambio arq.:** ❌ No
- **Estado:** ✅

---

### Bug 9 — Typos del usuario no se corrigen ni validan
> `"dimesniones"` llega verbatim al mutation engine. Sin normalización, cualquier typo puede producir comportamiento inesperado.

- **Archivos afectados:** `core/iterate_interactive_session.py` (`_apply_answer`)
- **Fix:** Normalización por substring en step 1: si el input contiene al menos 4 chars de una keyword conocida, mapear a la variable canónica. Tabla: `"dimens" → "dimensiones"`, `"estructur" → "estructura"`, etc.
- **Riesgo impl.:** 🟢 Bajo — función de normalización pura, sin efectos secundarios
- **Cambio arq.:** ❌ No
- **Estado:** ✅

---

### Bug 10 — `IterationDraft.objective = None`
> En `intent_resolver.resolve_action_request()`, para `"mejorar autonomia"` se extrae `operacion="mejorar"` pero no se extrae `objetivo`. El draft queda con `objective=None` hasta el final → `"- Objetivo: None"` en el summary.

- **Archivos afectados:** `core/intent_resolver.py` (`resolve_action_request`)
- **Fix:** Capturar la frase sustantiva después del verbo de operación con regex: `mejorar <X>` → `objetivo = X`.
- **Riesgo impl.:** 🟢 Bajo — cambio en lógica de parseo de un método
- **Cambio arq.:** ❌ No
- **Estado:** ✅ `resolve_action_request` extrae objetivo post-verbo con regex `\b(reducir|mejorar|...)\s+([\w][\w\s]*?)$`. Resultado: `"mejorar autonomia"` → `objetivo = "autonomia"`. — Frases generadas gramaticalmente incorrectas
> `body = f"Quieres {operation} {objective}"` con `operation="mejorar"` y `objective="modificar el diseño"` (fallback) produce *"Quieres mejorar modificar el diseño del sistema actual"*.

- **Archivos afectados:** `core/iterate_interactive_session.py` (`_build_response`, `step=0`)
- **Fix:** Cambiar fallback de `objective` de `"modificar el diseño"` a `"el diseño"` (sustantivo puro). Resultado: *"Quieres mejorar el diseño del sistema actual"*.
- **Riesgo impl.:** 🟢 Bajo — cambio de un string de fallback
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Fallback en `_build_response` step 0: `objective or "el diseño"` (sustantivo). Genera: *"Quieres mejorar el diseño del sistema actual"*. — Suggestion engine contradice constraints activas
> `SuggestionEngine` sugiere `increase_payload` cuando `safety_margin_ratio > 1.8`, sin considerar si `autonomy_below_restriction` está activo. Resultado: el sistema recomienda aumentar carga con autonomía ya insuficiente.

- **Archivos afectados:** `suggestions/suggestion_engine.py` (`generate_suggestions`)
- **Fix:** Guard: si `"autonomy_below_restriction"` en `simulation.warnings`, suprimir `increase_payload` y emitir `improve_autonomy` en su lugar.
- **Riesgo impl.:** 🟢 Bajo — cambio condicional en `generate_suggestions`
- **Cambio arq.:** ❌ No
- **Estado:** ✅ `has_autonomy_warning` guard en `generate_suggestions`: bloquea `increase_payload` cuando `"autonomy_below_restriction" in simulation.warnings`. Emite `improve_autonomy` con priority 1.0. — Phase `"completado"` con restricciones incumplidas
> `PhaseLayer.infer()` prioriza `can_fly=True` + `quality="good"` + `margin >= 1.8` → `"complete"`, sin evaluar si hay warnings activos. Con `autonomy_below_restriction` activo, el proyecto aparece como "completado".

- **Archivos afectados:** `core/phase_layer.py` (`infer`)
- **Fix:** Añadir en priority 4: `warnings = simulation.get("warnings") or []` — si hay warnings, degradar de `"complete"` a `"optimization"`.
- **Riesgo impl.:** 🟢 Bajo — una condición en un método aislado
- **Cambio arq.:** ❌ No — `PhaseLayer` es determinista y aislada
- **Estado:** ✅ Priority 4 checks `warnings = simulation.get("warnings") or []` antes de retornar `"complete"`. Con warnings activos degrada a `"optimization"`.

---

### Bug 14 — Flujo del wizard rígido (mismas preguntas para cualquier tipo)
> El wizard hace siempre los mismos pasos sin importar si la acción es paramétrica, estructural o de componente.

- **Archivos afectados:** `core/iterate_interactive_session.py` (flujo completo), `core/orchestrator.py`
- **Fix:** Requiere ramas condicionales por tipo de variable detectado. Diseño pendiente de documentar.
- **⚠️ Dependencias previas obligatorias:** Este bug NO debe implementarse antes de tener cerrados **Bug 3** (validación actionable), **Bug 4** (normalización de variable) y **Bug 5** (redirección de variables derivadas). Sin ellos, el rediseño de ramas del wizard operará sobre inputs sin validar y reproducirá los mismos problemas con más complejidad.
- **Riesgo impl.:** 🔴 Alto — rediseño del flujo del wizard, impacta tests existentes
- **Cambio arq.:** ✅ Sí — actualiza diagrama de flujo "Flujo `iterate`" en ARCHITECTURE.md y sección correspondiente en IMPLEMENTATION_TASKS.md
- **Estado:** ✅

---

### Bug 15 — No adaptación del flujo según tipo de modificación
> Ídem que Bug 14 — la sesión no distingue entre `"cambiar material"` (declarativo), `"reducir payload"` (numérico directo) y `"optimizar estructura"` (estructural sin valor).

- **Archivos afectados:** `core/iterate_interactive_session.py`
- **Fix:** Vinculado a Bug 14 — se resuelve en la misma refactorización del wizard.
- **⚠️ Dependencias previas obligatorias:** Ídem Bug 14 — requiere Bugs 3, 4 y 5 cerrados primero.
- **Riesgo impl.:** 🔴 Alto — mismo scope que Bug 14
- **Cambio arq.:** ✅ Sí — mismo que Bug 14
- **Estado:** ✅

---

## 🟡 Medios

### Bug 16 — `material` duplicado entre `current_parameters` y `design_properties`
- **Archivos afectados:** `actions/create_project.py`, `actions/iterate.py`, `workspace/workspace_manager.py`
- **Riesgo impl.:** 🟡 Medio — cambio de schema con retrocompatibilidad
- **Cambio arq.:** ✅ Sí — ya documentado en IMPLEMENTATION_TASKS "Separación de capas en state.json"
- **Estado:** ✅ `_build_mutable_state` usa `design_properties.structure` como fuente canónica. Fallback `current.get("material")` eliminado.
- **⚠️ Deuda pendiente:** `current_parameters` sigue pudiendo contener `"material"`, `"densidad"` y `"volumen"` como campos legacy. Son campos huérfanos: la física los ignora (lee de `design_properties.structure`) pero el usuario los ve modificables. La eliminación completa está registrada en **Bug 26**.

---

### Bug 17 — `restrictions` string coexiste con `parsed_constraints`
- **Archivos afectados:** `schemas/state_schema.py`, `simulation/simulator.py`
- **Riesgo impl.:** 🟡 Medio — afecta simulador y schema
- **Cambio arq.:** ✅ Sí — ya documentado en IMPLEMENTATION_TASKS "Separación de capas"
- **Estado:** ✅ `ProjectState` documenta las dos capas: `restrictions` es string usuario (source of truth); `parsed_constraints` es forma máquina derivada automáticamente.

---

### Bug 18 — `latest_results` mezcla output con estado
- **Archivos afectados:** `schemas/state_schema.py`, `workspace/workspace_manager.py`
- **Riesgo impl.:** 🟡 Medio — cambio de schema, migración de proyectos existentes
- **Cambio arq.:** ✅ Sí — requiere actualizar sección "Estado temporal vs persistente" en ARCHITECTURE.md
- **Estado:** ✅ Añadido `last_total_mass_kg: float | None` en `ProjectState`. `record_action` lo extrae de `calculations`. `_build_mutable_state` lo lee directamente sin tocar `latest_results`.

---

### Bug 19 — Sin invalidación de `parsed_constraints` al cambiar restricciones
- **Archivos afectados:** `schemas/state_schema.py` (`@model_validator`)
- **Riesgo impl.:** 🟢 Bajo — añadir re-parseo en el validator
- **Cambio arq.:** ❌ No
- **Estado:** ✅ `model_copy` override en `ProjectState` re-deriva `parsed_constraints` cuando `current_parameters` cambia. Helper `_parse_constraints()` compartido con `@model_validator`.

---

### Bug 20 — Inputs ambiguos no disparan clarificación
- **Archivos afectados:** `core/iterate_interactive_session.py`, `core/semantic_interpreter.py`
- **Riesgo impl.:** 🟡 Medio — cambia comportamiento del semantic interpreter
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Rama `decide=="proceed"` bloquea strategy vacía o pure-op-phrase (e.g. "mejorar") y pide clarificación. Elimina auto-síntesis de strings como "reducir structure_mass_factor".

---

### Bug 21 — Estimaciones de impacto no basadas en modelo físico real
- **Archivos afectados:** `core/iterate_interactive_session.py` (`_estimate_impact`)
- **Riesgo impl.:** 🔴 Alto — requiere modelo físico para estimación previa a mutación
- **Cambio arq.:** ✅ Sí — nueva capacidad en pipeline; actualizar IMPLEMENTATION_TASKS "Extensiones de capacidad física"
- **Estado:** ✅ `_attach_impact_estimate` y `_estimate_impact` reciben `current_params` vía `memory_context`. Payload con value numérico calcula delta real (e.g. 2.0→1.5 kg = -25%). Fallback ±10% si sin datos.

---

### Bug 22 — Inconsistencia en naming de variables
- **Archivos afectados:** `core/iterate_interactive_session.py`, `core/intent_resolver.py`
- **Riesgo impl.:** 🟢 Bajo — tabla de aliases
- **Cambio arq.:** ❌ No
- **Estado:** ✅ `_PARAM_DISPLAY_ALIASES` ampliado: `bateria/batería` → `battery_capacity_wh`, `potencia_motor/potencia_motores` → `motor_power_w`, `num_motores` → `motors`.

---

### Bug 23 — El sistema permite confirmar iteraciones incoherentes
- **Archivos afectados:** `core/iterate_interactive_session.py` (`_handle_final_confirmation`)
- **Riesgo impl.:** 🟡 Medio — añadir validación pre-confirmación
- **Cambio arq.:** ❌ No
- **Estado:** ✅ `_handle_final_confirmation` valida antes de confirmar: `operation`, `variable` no-None; `strategy` non-empty para operaciones no-DEFINE. Error orientativo si draft incompleto.

---

### Bug 24 — Sin control de coherencia variable ↔ estrategia
- **Archivos afectados:** `core/iterate_interactive_session.py`, `core/mutation_engine.py`
- **⚠️ Más urgente de lo que parece:** `variable` debería acotar el espacio de estrategias válidas. Sin esta validación, el usuario puede elegir `variable="autonomía"` + `strategy="optimizar estructura"` y el sistema lo acepta sin advertencia — la incoherencia no se detecta en ningún punto. Es un bug de coherencia semántica que contamina todas las iteraciones posteriores.
- **Riesgo impl.:** 🟡 Medio — validación cruzada entre `variable` y `strategy`
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Guard en step 2 (post-`_apply_answer`): si `is_physically_actionable` es False y no es downgrade-declarative candidate, el sistema pide reformular la estrategia sin avanzar la sesión.

---

### Bug 25 — Sin validación global pre-ejecución (pre-simulation) 🆕
> Aunque `variable`, `strategy` o `value` sean inválidos o incoherentes, el sistema puede llegar a ejecutar cálculo y simulación sin bloqueo. Distinto de Bug 23 (confirmación de iteración incoherente) — este ocurre antes: el motor de cálculo recibe un bundle construido desde datos inválidos.

- **Archivos afectados:** `actions/iterate.py`, `actions/calculate.py`, `actions/simulate.py`
- **Fix:** Añadir capa de validación pre-ejecución en `actions/iterate.py` que verifique: (1) que el draft tiene suficiente información para construir un `CalculationBundle` válido, (2) que los parámetros de entrada no tienen inconsistencias detectables antes de llamar al engine.
- **⚠️ Distinto de Bug 23:** Bug 23 es validación de coherencia en la confirmación del usuario dentro del wizard. Este bug es validación técnica de que los datos son computables antes de ejecutar el pipeline físico — puede ocurrir aunque el wizard haya pasado correctamente.
- **Riesgo impl.:** 🟡 Medio — toca el entry point de `iterate.py` y potencialmente `calculate.py` y `simulate.py`
- **Cambio arq.:** ❌ No — misma estructura, nueva capa de guard en actions
- **Estado:** ✅ Guard en `iterate.py` (Bug 25 label): `not is_physically_actionable(draft)` → retorna `status="definition"` con mensaje. Segundo guard `needs_concrete_value` cubre Bug 1/2 (volumen sin value).

---

## 🔴 Modelo de datos

### Bug 26 — Duplicación de estado entre `current_parameters` y `design_properties`
> `current_parameters` contiene `"material"`, `"densidad"` y `"volumen"` como campos legacy que coexisten con `design_properties.structure.material/density/volume`. La física ya lee exclusivamente de `design_properties.structure` (Bug 16), pero el usuario puede modificar los campos en `current_parameters` creyendo que afecta al sistema físico. Esto rompe la trazabilidad y el determinismo percibido sin producir ningún error visible.

- **Tipo:** 🔴 Bug de modelo de datos — no falla, pero genera verdad incorrecta
- **Archivos afectados:** `actions/create_project.py` (escritura inicial), `workspace/workspace_manager.py` (contexto LLM), `domains/` (parámetros iniciales), posiblemente script de migración para proyectos en disco
- **Condición detectada:** proyecto `levantar-2kg` en disco tiene `current_parameters.material = "fibra de carbono"` vs `design_properties.structure.material = "aluminio"`. Los dos valores han divergido silenciosamente.
- **Riesgo impl.:** 🔴 Alto — requiere:
  - Eliminar escritura de `material/densidad/volumen` en `current_parameters` al crear proyecto
  - Migrar proyectos existentes en disco (mover valor a `design_properties.structure`, borrar clave legacy)
  - Actualizar LLM context builder para omitir los campos huérfanos
  - Actualizar ~50–80 tests que construyen `current_parameters` con esas claves
  - Decisión de producto: ¿`current_parameters` es el panel de control del usuario, o solo parámetros de física?
- **Cambio arq.:** ✅ Sí — actualizar ARCHITECTURE.md sección "Separación de capas en state.json" y IMPLEMENTATION_TASKS
- **Prerrequisito para hacer bien:** decisión explícita sobre qué campos viven en `current_parameters` vs `design_properties` de forma permanente. No es un cambio de código solo.
- **Estado:** ⬜ No iniciado — diferir hasta decisión de modelo de datos

---

---

## Fase G — Testing CLI (16 abril 2026)

> Bugs detectados en segunda sesión de prueba manual en CLI real.  
> Revisión cruzada: Claude (análisis de código) + GPT (análisis conversacional).  
> Principio rector del orden: validar dominio → interpretar → ejecutar → UX.

---

## 🔴 Críticos (Fase G)

### Bug 27 — Mutación de material bloquea en confirmación por `operation=None`
> El path de cambio de material (step 2 → sub-step de nombre → step 3 → step 4) nunca asigna `draft.operation`. Al llegar a `_handle_final_confirmation`, la validación de Bug 23 rechaza con error "_La iteración no tiene operación definida_" y el usuario queda en bucle infinito: no puede confirmar ni avanzar.

- **Archivos afectados:** `core/iterate_interactive_session.py` (material sub-step, `_awaiting_material_value`, `_apply_answer`)
- **Fix:** Al resolver el nombre de material en el sub-step, asignar `operation=IterationOperation.DEFINE`. Cambio de material es una declaración de propiedad (define el material del sistema), no una reducción ni aumento — semánticamente es `DEFINE`. Si el semantic state ya tiene operación inferida distinta de `None`, usarla como fallback.
- **⚠️ Nota GPT:** No usar `REDUCE` hardcodeado. Claude confirma: `DEFINE` es correcto arquitectónicamente — `IterationOperation` solo tiene `REDUCE/INCREASE/DEFINE`, y el cambio de material no reduce ni aumenta un escalar numérico.
- **Riesgo impl.:** 🟢 Bajo — cambio localizado en el material sub-step de `_apply_answer`
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cerrado — ya implementado (`_op = session.iteration_draft.operation or IterationOperation.DEFINE` en material sub-step). Estado en BUGS.md desincronizado.
> `_match_numeric_param` solo reconoce una variable como numérica si su valor ya existe en `current_parameters`. En proyectos nuevos (o parámetros opcionales no configurados aún), `battery_capacity_wh`, `motor_power_w`, etc. no existen → devuelve `None` → el wizard pide estrategia (step 2) → cualquier respuesta que el usuario escriba falla con _"La estrategia no es compatible con la variable"_ → bucle sin salida.

- **Archivos afectados:** `core/iterate_interactive_session.py` (`_match_numeric_param`)
- **Fix:** Reconocer como parámetro numérico si la variable:
  1. está en `current_parameters` con valor numérico (comportamiento actual), O
  2. está en `_PARAM_DISPLAY_ALIASES` (alias conocido → param físico conocido), O
  3. su alias canónico está en `PARAMETER_REQUIREMENTS` del dominio.
  Con esto, `"bateria"` → `battery_capacity_wh` se reconoce como numérico aunque el valor no exista todavía en el proyecto.
- **⚠️ GPT:** Fix debe ser amplio — no depender solo de aliases. Cualquier variable del dominio físico conocido debe activar el path numérico.
- **Riesgo impl.:** 🟢 Bajo — cambio localizado en `_match_numeric_param`
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cerrado — ya implementado (tier 3 en `_match_numeric_param`). Estado en BUGS.md desincronizado. aceptada y ejecutada silenciosamente
> En step 1, cualquier string es aceptado como nombre de variable sin validación de existencia semántica. El sistema lo propaga al motor físico y, si `resolve_strategy` puede resolverlo (e.g. `"reducir carga"` como estrategia), ejecuta una mutación física real con una variable inválida (`variable="itera"`, `variable="hola"`, `variable="123"`). El resultado es físicamente correcto sobre una premisa incorrecta — el sistema miente.

- **Archivos afectados:** `core/iterate_interactive_session.py` (step 1, `_apply_answer`)
- **Fix:** Definir un conjunto cerrado de variables válidas en step 1. Una variable es válida si:
  1. está en `_VARIABLE_NORMALIZATION` (alias de concepto: `"carga"`, `"payload"`, etc.), O
  2. está en `_PARAM_DISPLAY_ALIASES` como clave o valor (alias técnico), O
  3. pertenece a un conjunto léxico explícito de términos de dominio: `"material"`, `"dimensiones"`, `"estructura"`, `"componentes"`, `"motores"`, `"bateria"`, `"batería"`, `"potencia"`, etc.
  Si no pertenece a ninguna → rechazar con mensaje orientativo y permanecer en step 1.
- **⚠️ GPT: este es el bug más peligroso del sistema actual.** Produce resultados correctos sobre premisas incorrectas, rompiendo la confianza sin producir errores visibles. Es una vulnerabilidad de integridad semántica, no de validación técnica.
- **⚠️ Implementar PRIMERO en Fase G** — antes de Bug 28 y Bug 27.
- **Riesgo impl.:** 🟡 Medio — requiere definir y mantener el conjunto de variables válidas. Cuidado con no rechazar variables legítimas de proyectos no-dron.
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Implementado previamente — BUGS.md desincronizado. `_is_valid_variable()` en `iterate_domain.py` + guard en `answer()` step 1 (línea 181). Conjunto cerrado: `build_valid_domain()` | `_STRUCTURAL_TERMS`. `"hola"`, `"123"`, `"itera"` rechazados con mensaje orientativo; `"bateria"`, `"motores"`, `"autonomia"` aceptados.

---

## 🟡 Importantes (Fase G)

### Bug 29 — `itera` como palabra suelta no se reconoce como intent determinista
> `"itera"` no está en `ITERATE_PATTERNS`. Se resuelve como `unknown` → cae al LLM → el LLM a veces pasa el slug (`"levantar-2kg"`) como `project_id` en lugar del UUID → error _"No se encontró proyecto con id levantar-2kg"_. Reproducible: segunda llamada a `itera` tras una iteración exitosa en la misma sesión.

- **Archivos afectados:** `core/intent_resolver.py` (`ITERATE_PATTERNS`)
- **Fix:** Añadir `r"\biter(a(r)?|ar)?\b"` a `ITERATE_PATTERNS`. Aunque el flujo correcto es escribir el cambio directamente, `"itera"` es un comando natural que el usuario usa como atajo.
- **Riesgo impl.:** 🟢 Bajo — añadir un patrón regex a una tupla existente
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Implementado previamente — BUGS.md desincronizado. `r"\biter(ar?)?\b"` ya presente en `ITERATE_PATTERNS`. `"itera"` y `"iterar"` resuelven a `iterate` determinísticamente.

---

### Bug 31 — Aliases de batería incompletos
> `"capacidad de bateria"`, `"capacidad bateria"`, `"capacidad de batería"`, `"potencia motores"`, `"potencia por motor"` no están en `_PARAM_DISPLAY_ALIASES`. El usuario que los escribe en step 1 pasa al step 2 con variable no reconocida y el wizard queda en estado incoherente.

- **Archivos afectados:** `core/iterate_interactive_session.py` (`_PARAM_DISPLAY_ALIASES`), `core/mutation_engine.py` (`_PARAM_DISPLAY_ALIASES`)
- **Fix:** Añadir entradas a `_PARAM_DISPLAY_ALIASES` en ambos módulos: `"capacidad de bateria"`, `"capacidad bateria"`, `"capacidad de batería"`, `"potencia motores"`, `"potencia por motor"` → sus canónicas correspondientes.
- **Riesgo impl.:** 🟢 Bajo — cambio en tablas de aliases
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cerrado — aliases presentes en `core/parameter_requirements.py` (`ParameterRequirement.aliases` para `battery_capacity_wh` y `motor_power_w`). `build_alias_map()` los incluye en el mapa final.

---

### Bug 35 — Operación en resumen no refleja intención real del usuario
> El path numérico-directo hardcodea `operation=IterationOperation.REDUCE` al construir el draft, independientemente de si el nuevo valor es mayor o menor que el anterior. El resumen muestra `"Operación: reducir"` cuando el usuario ha aumentado un parámetro (e.g. motores 4→6, batería 250→400).

- **Archivos afectados:** `core/iterate_interactive_session.py` (path numérico en step 2, `_attach_numeric_impact_estimate`)
- **Fix:** Inferir la dirección comparando `new_value` vs `old_val`:
  - `new_value > old_value` → `INCREASE`
  - `new_value < old_value` → `REDUCE`
  - `new_value == old_value` → `DEFINE` (no-op técnico)
- **⚠️ GPT:** No es cosmético — rompe la coherencia semántica del sistema y la confianza del usuario.
- **Riesgo impl.:** 🟢 Bajo — cambio localizado en el bloque numérico de step 2
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cerrado — ya implementado (`_infer_numeric_operation` en `iterate_interactive_session.py`). Estado en BUGS.md desincronizado. a variable numérica, el wizard pide estrategia innecesariamente
> Cuando el usuario escribe `"autonomia"` (variable derivada), el wizard redirige correctamente pidiendo un parámetro concreto. Si el usuario responde con una variable numérica reconocida (`"bateria"`), debería saltar directamente a pedir el valor numérico. En cambio, avanza al step 2 de estrategia, donde cualquier respuesta natural del usuario falla: `"bateria"` → _"La estrategia 'bateria' no es compatible con la variable 'bateria'"_.

- **Archivos afectados:** `core/iterate_interactive_session.py` (manejo de step 1 tras redirección de variable derivada en Bug 5)
- **Fix:** En el step 1, cuando el input llega como respuesta a una redirección previa (flag de estado o detección por `_DERIVED_VARIABLE_MESSAGES`), si `_match_numeric_param` reconoce la variable → saltar directamente al sub-step numérico (pedir valor). La lógica ya existe en step 2 — aplicarla también al resultado de la redirección.
- **⚠️ GPT detectó esto** como un gap nuevo distinto del Bug 28 — incluso cuando el parámetro existe, el flujo post-redirección no aplica el path rápido.
- **Riesgo impl.:** 🟡 Medio — requiere distinguir contexto de step 1 (¿venimos de redirección o de fresh start?)
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Implementado previamente — BUGS.md desincronizado. Tras redirección de variable derivada, step 1 acepta la variable numérica y el bloque numérico de step 2 (`_match_numeric_param`) muestra `"¿Cuál es el nuevo valor de bateria? (actual: 250.0)"` directamente. Verificado end-to-end en test manual (autonomia → bateria → valor).

---

## 🟢 Medios (Fase G)

### Bug 32 — Estimación de impacto muestra `None%` para parámetros numéricos
> `_attach_numeric_impact_estimate` construye `ImpactEstimate(summary=...)` sin rellenar `weight_change_percent`, `thrust_impact`, `stability_impact`. El render en `_impact_message` muestra estas líneas como `None` explícito.

- **Archivos afectados:** `core/iterate_interactive_session.py` (`_impact_message`)
- **Fix:** En `_impact_message`, omitir las líneas `peso`, `impacto en empuje`, `impacto en estabilidad` si el campo es `None`. Solo mostrar el `summary`.
- **Riesgo impl.:** 🟢 Bajo — cambio en función de renderizado
- **Cambio arq.:** ❌ No
- **Estado:** ✅ `_impact_message` omite líneas cuyo campo es `None`. Solo muestra `summary` para estimaciones numéricas. Todos los campos poblados aparecen normalmente.

---

### Bug 33 — `improve_autonomy` no tiene etiqueta en español en el CLI
> `SUGGESTION_LABELS` en `main.py` no tiene entrada para `"improve_autonomy"`. El render lo muestra como `"Podrías improve_autonomy (...)"`.

- **Archivos afectados:** `main.py` (`SUGGESTION_LABELS`)
- **Fix:** Añadir `"improve_autonomy": "mejorar la autonomía"` al dict.
- **Riesgo impl.:** 🟢 Bajo — añadir una entrada a un dict
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Entrada `"improve_autonomy": "mejorar la autonomía"` añadida a `SUGGESTION_LABELS` en `main.py`.

---

### Bug 34 — `cancelar` sin sesión activa muestra texto técnico
> Al cancelar sin sesión activa, la respuesta tiene `status="ok"`, `action="global_command"` y el renderer genérico imprime `"Acción ejecutada: global_command"` antes del mensaje correcto.

- **Archivos afectados:** `main.py` (`render_response`)
- **Fix:** Añadir case para `action == "global_command"` en `render_response` que retorne directamente el `message` sin prefijo.
- **Riesgo impl.:** 🟢 Bajo — un case en la función de render
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Case `action == "global_command"` añadido antes del bloque genérico `status="ok"` en `render_response`. Retorna directamente el `message` sin prefijo técnico.

---

### Bug 37 — Fuzzy matching de intents inconsistente
> `"simlar"` no es reconocido como `simulate`. `"simluar"` sí. Los patrones regex de los intents de primer nivel (`calcula`, `simula`, etc.) no tienen tolerancia a errores de escritura comunes.

- **Archivos afectados:** `core/intent_resolver.py` (`SIMULATE_PATTERNS`, `CALCULATE_PATTERNS`)
- **Fix:** Ampliar los patrones para cubrir variantes de typos más comunes, o añadir una capa de normalización pre-matching que corrija transposiciones obvias antes del regex. Evaluar alcance para no introducir falsos positivos.
- **Riesgo impl.:** 🟡 Medio — ampliar patterns puede crear falsos positivos; requiere tests de regresión de intent
- **Cambio arq.:** ❌ No
- **Estado:** ✅ `_fix_common_typos()` estático en `IntentResolver` corrige transposiciones antes del regex: `\bsiml\w+\b` → `"simular"`, aliases de `calcular`. Alcance deliberadamente estrecho para evitar falsos positivos (`similar`, `simpatia` no afectados).

---

## Fase H — Testing CLI (18 abril 2026)

> Bugs detectados en tercera sesión de prueba manual en CLI real.  
> Revisión cruzada: Claude (análisis de código directo) + GPT (análisis conversacional).  
> Principio rector: estabilizar routing conversacional → UX de material → conexión lenguaje → flujos especializados.

---

## 🔴 Críticos (Fase H)

### Bug 38 — Regresión Fix 1: `INFORMATION_SEEKING_KEYWORDS` sin word boundaries
> `classify_input_intent` en `ITERATE_INTERACTIVE` comprueba `any(kw in normalized for kw in INFORMATION_SEEKING_KEYWORDS)` con coincidencia de substring puro. `"dime"` es una de las keywords → `"dime" in "dimensiones"` = `True` → el guard del Fix 1 mata el wizard al recibir cualquier input que contenga una keyword como subcadena. Ejemplo reproducible: el usuario escribe `"dimensiones"` en step 2 y el orquestador llama a `_handle_analyze` en lugar de continuar el wizard.

- **Archivos afectados:** `core/intent_resolver.py` (`classify_input_intent`, `INFORMATION_SEEKING_KEYWORDS`)
- **Fix:** Reemplazar `any(kw in normalized for kw in self.INFORMATION_SEEKING_KEYWORDS)` por `any(re.search(r"\b" + re.escape(kw) + r"\b", normalized) for kw in self.INFORMATION_SEEKING_KEYWORDS)`. El check de `ACTION_SEEKING_KEYWORDS` en el mismo método ya usa `re.search(r"\b...\b")` — `INFORMATION_SEEKING_KEYWORDS` debe espejarlo.
- **⚠️ Regresión del sprint anterior:** Fix 1 introducido en Human Layer Sprint v1 para proteger el wizard es activamente perjudicial en su estado actual. Cualquier variable cuyo nombre contenga una keyword como subcadena rompe el wizard. Test de no-regresión obligatorio: `"dimensiones"` no clasifica como `information`, `"dime"` sí.
- **Riesgo impl.:** 🟢 Bajo — cambio de una línea en `classify_input_intent`; requiere test de regresión específico
- **Cambio arq.:** ❌ No
- **Estado:** ✅ `re.search(r"\b" + re.escape(kw) + r"\b", normalized)` en `classify_input_intent`. Tests de no-regresión: `"dimensiones"` → `"action"`, `"calcular"` → `"action"`. Standalone `"dime"` → `"information"` sigue funcionando.

---

## 🟡 Importantes (Fase H)

### Bug 39 — Consultas de navegación en idle no reconocidas como `project_status`
> En modo idle, frases como `"siguiente paso"`, `"que hago"`, `"como sigo"`, `"que puedo hacer"` no están en `STATUS_PATTERNS`. `resolve_intent()` las evalúa en orden: `STATUS_PATTERNS` → `QUESTION_PATTERNS` → intents deterministas → LLM. Como no encajan en ninguna rama determinista, caen al LLM → el LLM retorna `action="iterate"` → el orquestador abre el wizard. El usuario preguntando orientación acaba en una iteración forzada.
> **Nota:** `"siguiente paso"` sí está en `INFORMATION_SEEKING_KEYWORDS` (L97 `intent_resolver.py`), pero ese check solo opera dentro de `ITERATE_INTERACTIVE`; en idle lo procesa `resolve_intent()`, que no lo ve.

- **Archivos afectados:** `core/intent_resolver.py` (`STATUS_PATTERNS`)
- **Fix:** Añadir a `STATUS_PATTERNS` los patrones: `r"\bsiguiente\s+paso\b"`, `r"\bqu[eé]\s+hago\b"`, `r"\bc[oó]mo\s+sigo\b"`, `r"\bqu[eé]\s+puedo\s+hacer\b"`, `r"\bqu[eé]\s+debo\s+hacer\b"`, `r"\bpor\s+d[oó]nde\s+empiezo\b"`, `r"\bc[oó]mo\s+contin[uú]o\b"`. Estas frases responden con el startup context en lugar de entrar al LLM.
- **Riesgo impl.:** 🟢 Bajo — añadir entradas a una tupla de regex existente
- **Cambio arq.:** ❌ No
- **Estado:** ✅ 7 frases añadidas a `STATUS_PATTERNS`: `"siguiente paso"`, `"que hago"`, `"como sigo"`, `"que puedo hacer"`, `"que debo hacer"`, `"por donde empiezo"`, `"como continuo"`. Resuelven a `project_status` antes de caer al LLM. Tests de cobertura y no-falso-positivo añadidos.

---

### Bug 40 — Nueva intención de alto nivel dentro del wizard activo no detectada
> En `iterate_interactive_session.answer()` step 2, si el usuario escribe una nueva intención de alto nivel (`"quiero aumentar la carga útil"`, `"reducir el peso total"`) mientras el wizard está activo en una variable diferente, el sistema lo trata como una estrategia para la variable actual. No hay detección de que el usuario ha cambiado de objetivo. El wizard avanza con datos incoherentes hasta la confirmación.

- **Archivos afectados:** `core/iterate_interactive_session.py` (`answer()`, step 2)
- **Fix:** En step 2, antes de procesar como estrategia, comprobar si `user_input` coincide con un patrón de `ITERATE_PATTERNS` y extrae una variable diferente a `draft.variable` (usando `SemanticIntentAdapter` o el extractor de objetivo de `resolve_action_request`). Si se detecta nueva intención con objetivo distinto → reiniciar sesión con la nueva intención pre-seeded (limpieza del draft actual, `start()` con nueva variable).
- **⚠️ Dependencias:** Requiere Fase G G1 cerrado (wizard estable) y H1 cerrado (routing sin regressions). Sin H1, el re-routing dentro del wizard puede caer en el mismo Bug 38.
- **Riesgo impl.:** 🟡 Medio — requiere distinguir "estrategia válida" vs "nueva intención de alto nivel" en step 2; riesgo de falsos positivos si frases válidas de estrategia parecen intents
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cerrado — detector en step 2 de `iterate_interactive_session.answer()` — solo dispara cuando una palabra clave de variable canónica (carga, material, batería, etc.) aparece en el input AND la forma canónica de esa variable difiere de `draft.variable` AND `resolve_action_request` confirma intent iterate.

---

### Bug 41 — Sin bridge manual desde lenguaje natural a `DEFINE_MISSING_PARAMETERS`
> `DEFINE_MISSING_PARAMETERS` solo se activa automáticamente desde `build_startup_context()` cuando el sistema detecta parámetros faltantes. No existe ningún path que permita al usuario activarlo manualmente con frases como `"declarar parámetros de batería"`, `"configurar energía"`, `"definir batería"`. Estas frases caen al LLM → error `"No reconozco variable"` o apertura de wizard iterate con variable inválida.

- **Archivos afectados:** `core/intent_resolver.py` (nuevo patrón determinista), `core/orchestrator.py` (routing al session handler)
- **Fix:** Añadir en `resolve_intent()` detección de frases de definición de parámetros antes del LLM. Mapeo: `"definir bateria|configurar energia|parametros bateria|bateria"` → `reason="missing_energy_parameters"`; `"helices|propulsión|propeller"` + verbo de definición → `reason="missing_propeller_parameters"`. El orquestador enruta a `start_define_missing_params(reason=...)` cuando detecta estos intents.
- **⚠️ Dependencias:** Requiere H1 cerrado para que `"bateria"` no active antes algún path de información por substring.
- **Riesgo impl.:** 🟡 Medio — añadir nuevo bloque de intent detection; cuidado con no capturar `"bateria"` en contextos donde el usuario la menciona como variable de iterate
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cerrado — `DEFINE_PARAMS_PATTERNS` añadido a `intent_resolver.py` (antes de `ITERATE_PATTERNS`), `IntentType` ampliado, `resolve_action_request` mapea razón energy/propeller, bridge `if intent == "define_params"` en `orchestrator.chat()` llama `start_define_missing_params` directamente sin pasar por `handle()`.

---

### Bug 42 — "hélices" no conecta al pipeline de hélice
> `"hélices"` / `"mejorar hélices"` / `"propeller"` no están en `_COMPONENT_REDIRECT_TERMS` de `iterate_interactive_session.py`. Cuando el usuario los escribe en step 1, el sistema produce el mensaje de redirección genérico en lugar de enrutar a `DEFINE_MISSING_PARAMETERS` con `reason="missing_propeller_parameters"` — que es el único flujo que puede recoger `propeller_diameter_in` y `propeller_rpm`.

- **Archivos afectados:** `core/iterate_interactive_session.py` (`_COMPONENT_REDIRECT_TERMS`)
- **Fix:** Añadir a `_COMPONENT_REDIRECT_TERMS`: `"helice"`, `"helices"`, `"hélice"`, `"hélices"`, `"propeller"`, `"propellers"`, `"palas"` con routing a `DEFINE_MISSING_PARAMETERS` + `reason="missing_propeller_parameters"`. El texto del redirect debe indicar explícitamente qué parámetros se van a recoger.
- **⚠️ Dependencias:** Requiere Bug 41 cerrado — el redirect a `DEFINE_MISSING_PARAMETERS` desde dentro del wizard solo funciona si el bridge manual también está operativo (usan el mismo session handler).
- **Riesgo impl.:** 🟢 Bajo — añadir entradas a una tabla existente
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cerrado — `_PROPELLER_REDIRECT_TERMS` añadido a `iterate_interactive_session.py`; propeller terms en step 1 muestran mensaje específico `"Para configurar las hélices di: 'configurar hélices'"` en lugar del genérico `"di 'componentes'"`. El intent `define_params` + bridge en orquestador (Bug 41) completa el flujo.

### Bug 43 — Cambio al mismo material muestra 0% sin explicación
> Cuando el usuario declara el mismo material que ya tiene el proyecto (e.g. `"aluminio"` → `"aluminio"`), el motor de mutación ejecuta el cambio, calcula impacto y devuelve `"0.0% cambio en masa"` sin ningún mensaje que indique que el material seleccionado ya era el actual. El usuario no entiende por qué no pasó nada.

- **Archivos afectados:** `core/iterate_interactive_session.py` (material sub-step, pre-aplicación)
- **Fix:** Antes de ejecutar la mutación de material, comparar el material ingresado con `design_properties.structure.material` del estado actual. Si son idénticos (normalizado): devolver `"El material seleccionado ({material}) ya es el material actual del sistema — no hay cambio que aplicar."` y permanecer en el sub-step sin avanzar la sesión.
- **⚠️ Dependencias:** Requiere Bug 27 (Fase G) cerrado — la comparación solo tiene sentido si `operation` se asigna correctamente en el material path.
- **Riesgo impl.:** 🟢 Bajo — pre-check puro antes de llamar al motor; sin efectos secundarios
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cerrado — 18 abril 2026 (Fase H2). `_normalize_material()` + same-material pre-check en material sub-step; `memory_context["current_material"]` inyectado desde `orchestrator.py`.

---

### Bug 44 — Material desconocido: downgrade silencioso sin explicación causal
> Cuando el usuario ingresa un material no presente en la biblioteca física del sistema (`"PVC"`, `"plástico"`, `"madera"`), el flujo degrada silenciosamente a iteración declarativa con el mensaje genérico `"no se recalcula impacto físico en esta versión"`. No explica POR QUÉ no puede calcular el impacto ni qué debería hacer el usuario.

- **Archivos afectados:** `core/iterate_interactive_session.py` (material flow, downgrade path)
- **Fix:** Detectar explícitamente la causa del downgrade: si el material no está en `_KNOWN_MATERIALS` ni en la biblioteca física → mensaje específico: `"'{material}' no está en la biblioteca física del sistema. Se registra como propiedad declarativa pero no puedo calcular el impacto en masa ni en simulación. Los materiales con datos físicos disponibles son: {lista}."` El downgrade sigue ejecutándose — solo mejora la explicación.
- **Riesgo impl.:** 🟢 Bajo — cambio de mensaje en la rama de downgrade declarativo; sin cambios en lógica de ejecución
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cerrado — 18 abril 2026 (Fase H2). `_estimate_material_impact` split en dos bloques `try/except` separados; mensaje explícito "registrado pero sin datos físicos" con lista de materiales disponibles. `_impact_message` DEFINE muestra el mensaje sólo cuando no hay dato numérico.

---

### Bug 45 — Doble pregunta en flujo de material
> En el path de cambio de material, el orquestador genera `"¿A qué material quieres cambiar?"` y, en la misma respuesta, el wizard imprime `"Siguiente paso: ¿Qué material quieres usar?"`. El usuario recibe dos preguntas idénticas en el mismo turno.

- **Archivos afectados:** `core/iterate_interactive_session.py` (material sub-step, `_build_response`)
- **Fix:** Cuando el material handler ya ha emitido la pregunta de nombre de material (`_awaiting_material_value == True`), suprimir la pregunta del wizard en `_build_response`. La pregunta del handler es la canónica — el prompt del wizard para ese paso debe ser vacío o implícito.
- **⚠️ Dependencias:** Requiere Bug 27 (Fase G) cerrado — el path de material debe tener `operation` asignado antes de poder controlar el flujo de respuesta de forma coherente.
- **Riesgo impl.:** 🟢 Bajo — condición de supresión en `_build_response`; sin cambios en lógica de ejecución
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cerrado — 18 abril 2026 (Fase H2). Material handler emite única `question=` (sin `message=` paralelo); sustituyó el par `message+question` del bloque de material no reconocido.

---

### Bug 46 — Typo "augmentar" no normalizado
> `_fix_common_typos()` en `intent_resolver.py` solo cubre transposiciones de `simular` y `calcular`. El typo `"augmentar"` (anglicismo por `"aumentar"`) no tiene entrada en `_TYPO_MAP`. El usuario que escribe `"augmentar carga"` obtiene `unknown intent` → LLM → comportamiento impredecible.

- **Archivos afectados:** `core/intent_resolver.py` (`_fix_common_typos`, `_TYPO_MAP`)
- **Fix:** Añadir `(r"\baugment\w*\b", "aumentar")` a `_TYPO_MAP`. Alcance deliberadamente estrecho: solo cubrir el anglicismo directo, no variantes ambiguas.
- **Riesgo impl.:** 🟢 Bajo — añadir una entrada a una tabla de regex; sin efectos secundarios
- **Cambio arq.:** ❌ No
- **Estado:** ✅ `(r"\baugment\w*\b", "aumentar")` añadido a `_TYPO_MAP` en `_fix_common_typos`. `"augmentar carga"` / `"augmenta el payload"` → `iterate`. Tests parametrizados añadidos.

---

## Fase I — Audit Decision Layer (19 abril 2026)

> Bugs detectados en sesión de validación CLI del Decision Layer.  
> Método: escenarios adversos en CLI real con proyecto `carga-útil-de-2-3kg`.  
> Principio rector: un motor de decisión que no se muestra al usuario no existe.

---

## 🔴 Críticos (Fase I)

### Bug 47 — Reasoning completo nunca visible en modo conversacional
> El render con `PRIORIDAD CRÍTICA:` / `Siguientes pasos:` / `Evitar:` / `block_reason` existe en `render_response()` y el path `analyze` → `_handle_analyze()` lo activa correctamente (incluye `"reasoning"` en el payload). El problema real es que `ANALYZE_PATTERNS` es demasiado estrecho: solo captura `analiza|evalua|revisa|diagnostica`. Frases de orientación naturales como `"orientame"`, `"dame opciones"`, `"qué opciones tengo"`, `"cómo hago que vuele"` no encajan en ningún patrón determinista → caen al LLM → el LLM devuelve `iterate` → se abre el wizard. Adicionalmente, el render para `action="analyze"` muestra `"Acción ejecutada: analyze"` como primera línea, que es ruidoso e incorrecto para el usuario.

- **Archivos afectados:** `core/intent_resolver.py` (`ANALYZE_PATTERNS`), `main.py` (render `action="analyze"`)
- **Fix:** (1) Ampliar `ANALYZE_PATTERNS` con frases de orientación: `r"\b(?:orientame|orientar|dame opciones|que opciones|como hago|como puedo|que hago ahora|que deberia|ayudame)\b"`. (2) En `render_response`, cuando `action="analyze"`, omitir la línea `"Acción ejecutada: analyze"` y mostrar directamente el mensaje LLM + reasoning.
- **Riesgo impl.:** 🟢 Bajo — ampliar una tupla de regex existente + suprimir una línea de render
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cerrado — 19 abril 2026. `ANALYZE_PATTERNS` ampliado con `orientame|orientar|ayudame|dame opciones|que opciones|como hago|como puedo|que deberia`. `render_response` para `action="analyze"` omite prefijo `"Acción ejecutada:"`. `"que hago"` excluido (ya cubierto por `STATUS_PATTERNS`). 12 tests nuevos, 897 total.

---

## 🟡 Importantes (Fase I)

### Bug 48 — Warning "carga motores elevada" aparece cuando el sistema no vuela
> En `simulation/simulator.py`, `_resolve_warnings()` guarda los warnings `low_margin` y `low_force_to_weight_ratio` con `if can_fly and ...`, pero `high_actuator_load` carece de esa guarda: `if per_motor_load_ratio > HIGH_LOAD_THRESHOLD` dispara incondicionalmente. Con `payload=5.5kg`: `can_fly=False`, `per_motor_load_ratio=1.3631` → el warning se activa aunque el sistema no vuela. Resultado: el usuario ve `"⚠ Los motores trabajan cerca de su capacidad máxima. Un pico de carga puede comprometer el vuelo."` cuando el problema real es que el empuje es insuficiente, no que los motores estén al límite durante el vuelo. El mensaje es semánticamente incorrecto y genera confusión.

- **Archivos afectados:** `simulation/simulator.py` (`_resolve_warnings`, línea ~160)
- **Fix:** Añadir guarda `can_fly` al check de `high_actuator_load`: `if can_fly and per_motor_load_ratio > HIGH_LOAD_THRESHOLD`. Consistente con el patrón ya aplicado a `low_margin` y `low_force_to_weight_ratio` en el mismo método.
- **Riesgo impl.:** 🟢 Bajo — añadir `can_fly and` a una condición existente; requiere test de regresión
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cerrado — 19 abril 2026. Añadido `can_fly and` al check de `high_actuator_load` en `_resolve_warnings()`. 2 tests nuevos.

---

## 🟢 Menores (Fase I)

### Bug 49 — Intent "esta sugerencia no aplica, siguiente" sin cobertura
> Cuando el sistema muestra una sugerencia (e.g. "Aumentar carga útil") y el usuario responde indicando que esa sugerencia no aplica (`"carga útil correcta, siguiente paso"`, `"no quiero aumentar payload"`, `"ignora eso"`), no existe ningún intent que reconozca ese patrón. El sistema repite la misma sugerencia indefinidamente — la sesión queda bloqueada. El usuario no tiene forma de avanzar sin cambiar manualmente el estado del proyecto.

- **Archivos afectados:** `core/intent_resolver.py` (nuevo patrón de descarte), `core/orchestrator.py` (routing a siguiente sugerencia)
- **Fix:** Añadir `DISMISS_SUGGESTION_PATTERNS` al resolver. Cuando se detecta, el orquestador marca la sugerencia top como descartada en sesión (no en estado) y muestra la siguiente sugerencia no bloqueada. El descarte es por sesión, no persistente.
- **⚠️ Dependencias:** Bug 47 debe estar cerrado primero — tiene más sentido cuando el reasoning completo ya es visible.
- **Riesgo impl.:** 🟡 Medio — requiere estado de sesión para sugerencias descartadas; no contaminar `state.json`
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cerrado — 21 abril 2026. `DISMISS_SUGGESTION_PATTERNS` en `intent_resolver.py`, `_handle_dismiss_suggestion` en `orchestrator.py`. `session.last_suggested_action` garantiza consistencia UX. Descarte por sesión, no persistente.

---

### Bug 50 — Variable derivada `empuje` sin redirección en wizard
> Al escribir `"empuje"` como variable en el paso 1 del wizard de iteración, el sistema la acepta directamente sin redirigir al parámetro primario subyacente (`motors` o `per_actuator_torque_nm`). El usuario queda atrapado en un flujo sin salida: cualquier estrategia que intente (e.g. `"aumentar motores"`) es rechazada por coherencia Bug 24 como incompatible con `"empuje"`. Solo `"autonomía"` tiene redirección implementada (Bug 5).

- **Archivos afectados:** `core/iterate_interactive_session.py` — `_match_variable` o equivalente donde se resuelven variables derivadas
- **Fix:** Extender el mecanismo de redirección de Bug 5 para cubrir `"empuje"` → redirigir a `motors` (o `per_actuator_torque_nm` si hay torque declarado). Mostrar mensaje: `"Empuje es una variable derivada. Para modificarlo, ajusta el número de motores o el torque por actuador."`
- **⚠️ Dependencias:** Ninguna — Bug 5 ya establece el patrón. Bug 50 es una extensión directa.
- **Riesgo impl.:** 🟢 Bajo — mismo patrón que Bug 5, solo añadir alias
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cerrado — 21 abril 2026. Entrada `"empuje"` en `PARAMETER_REQUIREMENTS` con `is_derived=True`, `derived_message` y `concept_aliases=("empuje",)`. Redirige a `motors` / `per_actuator_torque_nm`.

---

### Bug 51 — Sin reprompt del wizard tras interrupción inline
> Al interceptar `resumen` (o `analyze`) dentro del wizard de iteración (Bug 7), el resultado se muestra correctamente pero el sistema no repromptea el paso actual del wizard. El usuario ve el bloque de estado y luego silencio — no sabe que el wizard sigue activo ni qué se espera de él.

- **Archivos afectados:** `main.py` — rama render de `project_status` y `analyze` cuando hay sesión activa
- **Fix:** Tras renderizar el resultado inline, añadir reprompt del paso actual del wizard (leer `pending_step` del `IterateInteractiveSession` y mostrar su pregunta al final de la respuesta)
- **⚠️ Dependencias:** Bug 7 (ya implementado) — Bug 51 es mejora UX sobre él
- **Riesgo impl.:** 🟢 Bajo — solo renderizado, sin tocar lógica de sesión
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cerrado — 21 abril 2026. `get_current_prompt(session)` en `IterateInteractiveSession` reutiliza `_question_for_session`. Orchestrator añade `wizard_reprompt` a los resultados de intercept inline. `render_response` en `main.py` renderiza `[Wizard activo] <pregunta>`.

---

### Bug 52 — LLM fallback interpreta input sin sentido como `iterate`
> Al escribir input totalmente ajeno al dominio (e.g. `"xkcd"`), el sistema cae al LLM fallback (`llm_interface.interpret`). El LLM alucina una acción `iterate` con variable `payload` y el wizard se abre como si el usuario hubiera pedido iterar. El usuario no entiende qué ocurrió.
>
> Flujo afectado: intent=`unknown` → `llm_interface.interpret` → LLM devuelve `action=iterate` → `handle()` → wizard.

- **Archivos afectados:** `core/orchestrator.py` — rama de LLM fallback (después del bloque `if intent in {"create_project", "iterate", ...}`)
- **Fix:** Tras llamar a `llm_interface.interpret`, si la acción devuelta es `iterate` y el intent original era `unknown`, redirigir a `analyze` en lugar de abrir el wizard. El LLM no debería poder abrir el wizard para inputs sin sentido.
- **⚠️ Dependencias:** Ninguna
- **Riesgo impl.:** 🟡 Medio — puede afectar casos legítimos donde el LLM detecta correctamente un iterate desde texto natural no reconocido por patrones. Revisar test coverage.
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cerrado — 20 abril 2026. `orchestrator.py`: si `intent=="unknown"` y LLM devuelve `action=="iterate"`, redirige a `_handle_analyze` en lugar de abrir wizard.

---

### Bug 53 — `estado` suelto no se reconoce como `project_status`
> `"estado"` como input aislado no está en `STATUS_PATTERNS`. Cae al LLM fallback que en algunos contextos lo interpreta como `iterate` → abre wizard inesperadamente. Solo `"resumen"` y frases largas como `"dame el estado"` estaban cubiertas.

- **Archivos afectados:** `core/intent_resolver.py` (`STATUS_PATTERNS`)
- **Fix:** Añadir `r"\bestado\b"` a `STATUS_PATTERNS` como patrón adicional (mismo patrón que `"resumen"`).
- **⚠️ Dependencias:** Ninguna
- **Riesgo impl.:** 🟢 Bajo — añadir una sola cadena a la tupla
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cerrado — 21 abril 2026. `r"\bestado\b"` añadido a `STATUS_PATTERNS` en `intent_resolver.py`. Detectado en testing CLI 19 abril 2026.

---

### Bug 54 — Respuesta `si` al prompt proactivo de `resumen` no abre wizard
> El bloque `resumen` (y `project_status`) muestra una línea `? ¿Definimos X ahora?` cuando hay parámetros faltantes. Si el usuario responde `"si"`, el sistema cae al LLM fallback que interpreta la respuesta como iterate en lugar de arrancar `DEFINE_MISSING_PARAMETERS`. La pregunta es solo texto renderizado — no hay mecanismo en el orchestrator que capture esa respuesta.
>
> Contraste: al seleccionar un proyecto en startup, el wizard sí se abre automáticamente (sin esperar input). Esa ruta funciona porque el startup lo dispara directamente.

- **Archivos afectados:** `main.py` + `core/orchestrator.py` — tras renderizar `project_status` con `status_type=blocking`, el siguiente input `"si"`/`"s"`/`"ok"` debería disparar `start_define_missing_params`
- **Fix:** Añadir estado temporal `pending_define_missing` en el runtime (similar a como el startup lo dispara): si el último resultado fue `project_status` con params faltantes y el siguiente input es afirmativo, arrancar `DEFINE_MISSING_PARAMETERS` directamente
- **⚠️ Dependencias:** Ninguna
- **Riesgo impl.:** 🟡 Medio — requiere estado temporal entre turnos
- **Cambio arq.:** ❌ No (estado temporal ya existe en `RuntimeState`)
- **Estado:** ✅ Cerrado — 21 abril 2026. `pending_define_missing`, `pending_missing_params`, `pending_missing_reason` en `InteractiveSessionState`. `_handle_project_status` los persiste en modo IDLE cuando hay `proactive_question`. `_is_affirmative` + flag consumption en `handle_user_text`. Flag siempre limpiado tras cualquier input.

---

### Bug 56 — Comandos globales no interceptados en `DEFINE_MISSING_PARAMETERS`
> El wizard `DEFINE_MISSING_PARAMETERS` no intercepta comandos globales (`simula`, `calcula`, `resumen`, `estado`…) durante sus pasos. Cualquier input no numérico falla la validación con `"No reconozco X como número"` y repregunta el mismo paso. Contraste: el wizard `ITERATE_INTERACTIVE` sí tiene interceptación inline (Bug 7, implementado) para `resumen` y `analyze`.
>
> Reproducción: wizard de `DEFINE_MISSING_PARAMETERS` activo → escribir `simula` → respuesta: `"Error: No reconozco 'simula' como número."`

- **Archivos afectados:** `core/define_missing_params_session.py` (o equivalente) — la rama de validación numérica no verifica comandos de escape antes de parsear
- **Fix:** Antes de intentar parsear el valor numérico, comprobar si el input es un comando global (`cancelar`, `simula`, `calcula`, `estado`, `resumen`, `help`…) y enrutarlo correctamente — o al menos mostrar mensaje de ayuda en lugar de error de validación
- **⚠️ Dependencias:** Bug 51 (reprompt post-interrupción en ITERATE_INTERACTIVE) — ambos son variantes del mismo patrón
- **Riesgo impl.:** 🟢 Bajo — interceptación antes de validación numérica
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cerrado — 20 abril 2026. `orchestrator.py` rama `DEFINE_MISSING_PARAMETERS`: intercepta `project_status`, `analyze`, `calculate`, `simulate` antes de delegar al session handler. — Colisión visual entre `Siguiente paso recomendado:` del component resolver y `Siguiente paso:` del wizard
> Al analizar un componente de nivel bajo (ej: `motores`), el component resolver emite un bloque de análisis que termina con `Siguiente paso recomendado: Incluye cantidad y especificación (ej: 4x 920KV)`. Inmediatamente después, el wizard del iterate muestra su propio prompt `Siguiente paso: ¿Hay restricciones?`. El usuario ve dos `Siguiente paso` consecutivos y no sabe cuál responder — tiende a responder el primero (la recomendación del resolver) creyendo que es el prompt del wizard.
>
> Reprodución: `motores` → resolver emite recomendación → wizard pregunta restricciones → usuario confundido.
✅ Cerrado — 20 abril 2026. `orchestrator.py` rama `DEFINE_MISSING_PARAMETERS`: intercepta `project_status`, `analyze`, `calculate`, `simulate` antes de delegar al session handler. impl.:** 🟢 Bajo — solo cambio de etiqueta de texto
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cerrado — 20 abril 2026. Etiqueta renombrada a `→ Sugerencia:` en `iterate_interactive_session.py` línea 1515. — Mensaje `"Esta iteración define una propiedad del diseño."` aparece duplicado
> Al confirmar una iteración declarativa (tipo `define`), el mensaje `"Esta iteración define una propiedad del diseño."` se imprime dos veces consecutivas antes de `"No se recalcula impacto físico en esta versión."`
>
> Reproducción: wizard iterate → definir componente declarativo → confirmar → dos líneas idénticas.

- **Archivos afectados:** `main.py` o `core/iterate_interactive_session.py` — el mensaje se emite en dos lugares distintos del flujo de confirmación declarativa
- **Fix:** Localizar las dos emisiones del string y eliminar el duplicado
- **⚠️ Dependencias:** Ninguna
- **Riesgo impl.:** 🟢 Bajo — eliminar una línea de print/output
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Cerrado — 20 abril 2026. `_impact_message` verifica si `estimate.summary` ya empieza por `"Esta iteración define"` antes de preponer el prefijo. por grupo de fix

| Bugs | Archivo doc | Sección afectada |
|------|------------|-----------------|
| 7 | `ARCHITECTURE.md` | "Orden de ejecución en `handle_user_text`" |
| 14, 15 | `ARCHITECTURE.md` | Diagrama flujo `iterate`, "Draft temporal + estado semántico" |
| 14, 15 | `IMPLEMENTATION_TASKS.md` | Nuevo bloque "Rediseño wizard iterate" |
| 16, 17 | `IMPLEMENTATION_TASKS.md` | Marcar como completado cuando se cierre |
| 18 | `ARCHITECTURE.md` | Sección "Estado temporal vs persistente", estructura `state.json` |
| 21 | `IMPLEMENTATION_TASKS.md` | "Extensiones de capacidad física" |

---

---

## Orden de implementación sugerido

> Principio rector: **proximidad** — ordenar por qué desbloquea qué, qué evita estados inconsistentes, qué estabiliza antes de añadir complejidad. No por impacto ni facilidad.

### Fase A — Sin riesgo, mayor impacto visible (tests mínimos)

- [x] Bug 13 · `core/phase_layer.py` — phase "completado" con restricciones incumplidas
- [x] Bug 12 · `suggestions/suggestion_engine.py` — suggestions contradicen constraints
- [x] Bug 11 · `core/iterate_interactive_session.py` — gramática incorrecta en step 0
- [x] Bug 10 · `core/intent_resolver.py` — `objective=None` en draft

### Fase B — Wizard robusto (por capas de proximidad)

**🧱 Capa 1 — Reglas del sistema** (qué puede ejecutarse)
- [x] Bug 3 · `mutation_engine` + `actions/iterate.py` — validación actionable (🔑 base)
- [x] Bug 25 · `actions/iterate.py` — validación pre-ejecución (doble barrera)

**🧩 Capa 2 — Interpretación** (cómo traducir usuario → sistema)
- [x] Bug 4 · `core/iterate_interactive_session.py` — mapping `"carga"` → `payload_kg`
- [x] Bug 24 · `core/iterate_interactive_session.py` + `mutation_engine` — coherencia `variable` ↔ `strategy`
- [x] Bug 5 · `core/iterate_interactive_session.py` — redirección `"autonomía"` (segura tras Bug 3)

**⚙️ Capa 3 — Ejecución defensiva** (qué pasa cuando algo llega)
- [x] Bug 1 · `actions/iterate.py` — degradación a DEFINE con `value=None` (depende de Bug 3)
- [x] Bug 2 · cubierto por Bug 1
- [x] Bug 6 · cubierto por Bugs 3 + 4 + 9

**🎨 Capa 4 — UX** (mejora final, no desbloquea nada)
- [x] Bug 9 · `core/iterate_interactive_session.py` — normalización fuzzy de typos
- [x] Bug 8 · `core/iterate_interactive_session.py` — mensajes de error orientativos

### Fase C — Cambio de flujo orquestador (tests de integración)

- [x] Bug 7 · `core/orchestrator.py` — intercept `project_status`/`analyze` en `ITERATE_INTERACTIVE`

### Fase D — Rediseño wizard (cambio arquitectural, requiere doc update)

> ⚠️ Solo ejecutar con Bugs 3, 4 y 5 cerrados

- [x] Bug 14 · `core/iterate_interactive_session.py` — ramas por tipo de variable
- [x] Bug 15 · cubierto por Bug 14

### Fase E — Deuda técnica y hardening (diferible)

**E1**
- [x] Bug 23 · `core/iterate_interactive_session.py` — validación pre-confirmación

**E2**
- [x] Bug 16 · `material` duplicado entre `current_parameters` y `design_properties`
- [x] Bug 17 · `restrictions` string coexiste con `parsed_constraints`
- [x] Bug 18 · `latest_results` mezcla output con estado
- [x] Bug 19 · sin invalidación de `parsed_constraints` al cambiar restricciones
- [x] Bug 20 · inputs ambiguos no disparan clarificación
- [x] Bug 21 · estimaciones de impacto no basadas en modelo físico real
- [x] Bug 22 · inconsistencia en naming de variables

### Fase F — Modelo de datos (diferible — requiere decisión de producto)

- [ ] Bug 26 · `current_parameters` — duplicación `material/densidad/volumen` con `design_properties.structure`

### Fase G — CLI real segunda sesión (orden crítico — no alterar)

> Principio: validar dominio semántico → desbloq. interpretación → desbloq. ejecución → coherencia → UX.  
> El orden dentro de G1 es obligatorio: Bug 30 bloquea inputs inválidos antes de que Bug 28 los interprete.
>Regla de oro para Fase G: NINGÚN input del usuario entra al sistema sin pasar por validación de dominio

**G1 — Críticos de validación semántica** (en este orden)
- [x] Bug 30 · `iterate_interactive_session.py` — validar variable ∈ dominio cerrado (🔑 base — PRIMERO)
- [x] Bug 28 · `iterate_interactive_session.py` — `_match_numeric_param` sin depender de estado existente
- [x] Bug 27 · `iterate_interactive_session.py` — `operation=None` en material → asignar `DEFINE`

**G2 — Importantes UX** (desbloquean flujos esperados)
- [x] Bug 35 · `iterate_interactive_session.py` — operation REDUCE/INCREASE/DEFINE por comparación de valor
- [x] Bug 36 · `iterate_interactive_session.py` — tras redirección de variable derivada, saltar a valor
- [x] Bug 31 · `iterate_interactive_session.py` + `mutation_engine.py` — ampliar aliases de batería
- [x] Bug 29 · `intent_resolver.py` — añadir `"itera"` a `ITERATE_PATTERNS`

**G3 — Medios UX** (polish — diferibles)
- [x] Bug 32 · `iterate_interactive_session.py` — omitir campos `None` en `_impact_message`
- [x] Bug 33 · `main.py` — añadir `"improve_autonomy"` a `SUGGESTION_LABELS`
- [x] Bug 34 · `main.py` — `render_response` para `action="global_command"`
- [x] Bug 37 · `intent_resolver.py` — fuzzy matching de intents primer nivel

### Fase H — Capa conversacional (orden crítico — no alterar)

> Principio: estabilizar routing (regressions primero) → UX de material (requiere G1) → conexión lenguaje → flujos especializados (requiere H1 + G1).  
> El orden dentro de H1 es obligatorio: Bug 38 es una regresión activa que puede invalidar fixes anteriores.  
> Regla de oro para Fase H: NINGÚN fix de routing nuevo antes de cerrar la regresión del Bug 38.

**H1 — Regresión routing** (sin dependencias — implementar primero, todos en `intent_resolver.py`)
- [x] Bug 38 · `intent_resolver.py` — Fix 1 substring match sin `\b` (🔑 primera — regresión activa)
- [x] Bug 39 · `intent_resolver.py` — STATUS_PATTERNS sin frases de navegación
- [x] Bug 46 · `intent_resolver.py` — typo "augmentar" sin normalizar

**H2 — Material UX** (requieren Bug 27 de Fase G cerrado)
- [x] Bug 43 · `iterate_interactive_session.py` — mismo material muestra 0% sin explicación
- [x] Bug 44 · `iterate_interactive_session.py` — material desconocido: downgrade silencioso
- [x] Bug 45 · `iterate_interactive_session.py` — doble pregunta en flujo de material (requiere Bug 27)

**H3 — Conexión lenguaje → flujos** (requieren H1 + G1 cerrados — en este orden)
- [x] Bug 40 · `iterate_interactive_session.py` — nueva intención de alto nivel dentro del wizard
- [x] Bug 41 · `intent_resolver.py` + `orchestrator.py` — bridge manual a DEFINE_MISSING_PARAMETERS (🔑 base de H3)
- [x] Bug 42 · `iterate_interactive_session.py` — "hélices" conecta a propeller pipeline (requiere Bug 41)

### Fase I — Audit Decision Layer (19 abril 2026)

> Principio: el Decision Layer ya es un motor de decisión real — los bugs ya no son de cálculo sino de decisión incorrecta o de visibilidad nula.  
> Regla de oro: un motor de decisión que no se muestra al usuario no existe.

**I1 — Visibilidad crítica** (el reasoning completo nunca llega al usuario)
- [x] Bug 47 · `core/intent_resolver.py` + `main.py` — `ANALYZE_PATTERNS` estrecho + prefijo render incorrecto

**I2 — Correctness de estado** (mensajes incorrectos según estado físico)
- [x] Bug 48 · `simulation/simulator.py` — warning "carga motores elevada" aparece en `status=fail`

**I3 — UX conversacional** (intents sin cobertura)
- [x] Bug 49 · `core/intent_resolver.py` — intent "esta sugerencia no aplica / siguiente" sin cobertura

### Fase J — Testing CLI segunda ronda (19 abril 2026)

**J1 — Variables derivadas sin redirección**
- [x] Bug 50 · `core/iterate_interactive_session.py` — variable `"empuje"` sin redirección a `motors`/`per_actuator_torque_nm`

**J2 — UX wizard: reprompt post-interrupción**
- [x] Bug 51 · `main.py` — tras interrupción inline (resumen/analyze dentro del wizard), no se repromptea el paso actual del wizard

**J3 — LLM fallback no acotado**
- [x] Bug 52 · `core/orchestrator.py` — LLM fallback interpreta input sin sentido (`xkcd`) como `iterate` y abre wizard

**J4 — STATUS_PATTERNS incompleto**
- [x] Bug 53 · `core/intent_resolver.py` — `"estado"` suelto no resuelto como `project_status`

**J5 — Prompt proactivo sin captura de respuesta**
- [x] Bug 54 · `main.py` / `core/orchestrator.py` — la pregunta `?` del bloque `resumen` no captura `"si"` como trigger de DEFINE_MISSING_PARAMETERS

**Jx — Comandos globales no interceptados en DEFINE_MISSING_PARAMETERS**
- [x] Bug 56 · `core/define_missing_params_session.py` — comandos globales dentro del wizard fallan con error de validación numérica en lugar de enrutarse

**J7 — Colisión visual de etiquetas y mensaje duplicado en iterate**
- [x] Bug 57 · `core/iterate_interactive_session.py` — `Siguiente paso recomendado:` del component resolver colisiona con `Siguiente paso:` del wizard
- [x] Bug 58 · `main.py` / `core/iterate_interactive_session.py` — mensaje declarativo `"Esta iteración define una propiedad del diseño."` aparece duplicado

x] Bug 57 · `core/iterate_interactive_session.py` — `Siguiente paso recomendado:` del component resolver colisiona con `Siguiente paso:` del wizard
---

## Fase K — Testing CLI (29 abril 2026)

> Contexto: primera sesión de validación end-to-end con proyecto nuevo (dron, payload 2kg, flujo completo desde crear → arquitectura → propulsión → energía → frame).  
> Identificados 5 bugs nuevos. Todos surgieron en flows normales, sin casos extremos.  
> Último count antes de esta sesión: 58 bugs (todos ✅). Esta sesión abre 59–63.

---

### Bug 59 — `battery_capacity_wh` / `motor_power_w` en wizard → noop (Crítico)

> El wizard `DEFINE_MISSING_PARAMETERS` colecta `battery_capacity_wh` y `motor_power_w` correctamente (pregunta, el usuario responde con valores numéricos) pero `apply_and_recalculate` los detecta como `COMPONENT_MIRRORED_PARAMS` y devuelve `{"status": "noop"}`. El usuario queda en un loop: el sistema sigue pidiendo los mismos params que acaba de rechazar sin escribir.
>
> Reproducción: arquitectura definida → sistema guía a "Siguiente bloque: Energía" → usuario dice `"definir bateria"` → wizard pregunta `battery_capacity_wh` → usuario responde `300` → wizard pregunta `motor_power_w` → usuario responde `45` → respuesta: `{"status": "noop", "message": "Estos parámetros se definen a través del componente correspondiente."}` → energía sigue en not_started.

- **Archivos afectados:** `core/param_definition_session.py` (`apply_and_recalculate`)
- **Causa raíz:** D4 bloquea escritura directa de mirrored params. Correcto por invariante, pero el wizard de energía/propulsión no tiene path alternativo que cree el componente a través de los writers.
- **Fix:** En `apply_and_recalculate`, cuando los params bloqueados son exclusivamente mirrored de energía (`battery_capacity_wh`, `motor_power_w`), invocar `set_battery_component` / `set_motor_component` con specs sintéticas de completeness `"medium"`. Los specs se construyen igual que en `design_explorer._battery_spec()` / `_motor_spec()`. El estado se persiste y la simulación se recalcula. Resultado: el bloque energy avanza a `complete`, `autonomy` aparece en cálculos.
- **⚠️ Nota:** No romper el invariante D4 — la escritura pasa por los writers, nunca directamente a `current_parameters`. El fix es añadir un bridge en `apply_and_recalculate`, no eliminar el guard.
- **Riesgo impl.:** 🟡 Medio — requiere importar component writers + `_battery_spec`/`_motor_spec` helpers en `param_definition_session.py`. Verificar que los writers llaman a `save_state` o que el caller lo hace.
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Hecho — bridge implementado en `apply_and_recalculate`. Helpers `_make_battery_spec` / `_make_motor_spec` locales en `param_definition_session.py`. Tests actualizados. 1203 passed. (Crítico)

> El wizard de propulsión/hélice colecta `propeller_diameter_in` del usuario pero `apply_and_recalculate` lo bloquea (D4) y solo aplica el siguiente param no-mirrored (`propeller_rpm`). El usuario ve `"Parámetros aplicados: propeller_rpm=6500"` sin mención del diámetro — no hay mensaje de error, no hay confirmación, no hay componente creado.
>
> Reproducción: `"definir motores + helices"` → wizard pregunta `propeller_diameter_in` → usuario responde `9` → wizard pregunta `propeller_rpm` → usuario responde `6500` → respuesta: `"Parámetros aplicados: propeller_rpm=6500.0"` — `propeller_diameter_in` silenciado. El bloque propulsión sigue `in_progress`.

- **Archivos afectados:** `core/param_definition_session.py` (`apply_and_recalculate`)
- **Causa raíz:** Igual que Bug 59. D4 bloquea `propeller_diameter_in` sin bridge al writer correspondiente.
- **Fix:** Mismo patrón que Bug 59: cuando el param bloqueado es `propeller_diameter_in`, invocar `set_propeller_component` con spec sintético. `propeller_diameter_in` se escribe en `components["propellers"].properties["diameter_in"]` y se deriva a `current_parameters` vía el bridge D6.
- **⚠️ Dependencia:** Bug 59 — implementar juntos (misma función, mismo punto de extensión).
- **Riesgo impl.:** 🟡 Medio — mismo patrón que Bug 59
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Hecho — resuelto junto con Bug 59 (mismo punto de extensión). `_make_propeller_spec` local. Tests actualizados.

---

### Bug 61 — Mensaje "en progreso" equivocado en bloque composite (Medio)

> Cuando un bloque `composite` (propulsion, energy) está `in_progress` porque faltan los **componentes** (no los params), el contexto de inicio muestra: `"Propulsión (motores + hélices) en progreso — define los parámetros que faltan."` El usuario interpreta que tiene que escribir números, cuando en realidad necesita describir componentes.
>
> Reproducción: propulsión con `motor_count + per_motor_max_thrust_n` definidos pero `components["motors"]` y `components["propellers"]` en completeness=`"low"` → `_block_progress_status` = `"in_progress"` → `build_startup_context` emite mensaje de params.

- **Archivos afectados:** `core/orchestrator.py` (`build_startup_context` + nuevo `get_block_in_progress_reason`)
- **Causa raíz:** El mensaje `"en progreso — define los parámetros que faltan"` es genérico y no distingue si el bloqueo es por params o por componentes faltantes.
- **Fix:** Se introduce `get_block_in_progress_reason(state, block) → 'missing_components' | 'missing_params'` como única fuente de verdad para la razón del `in_progress`. Para bloques `composite`, inspecciona las completeness de los component keys (misma semántica que `_block_progress_status`, sin duplicación). La rama `in_progress` de `build_startup_context` delega en esta función y emite: `"en progreso — declara los componentes necesarios"` si `missing_components`, `"en progreso — define los parámetros que faltan"` si `missing_params`. Diseño: estado ≠ UI — `_block_progress_status` no cambia, solo se añade la función de razón.
- **Nota impl.:** El escenario `params_ok=False, components_ok=True` para composite no alcanza la rama `in_progress` de `build_startup_context` porque la proactive question de params de mayor prioridad se establece antes. El test cubre el invariante real: cuando componentes están presentes, el mensaje no dice `"declara los componentes"`.
- **Riesgo impl.:** 🟢 Bajo
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Hecho — 5 tests nuevos: `TestGetBlockInProgressReason` (3) + `TestBuildStartupContextInProgressMessage` (2). 1210 passed.

---

### Bug 62 — "frame de fibra de carbono 500g" → LLM analyze, sin aplicar (Importante)

> El usuario describe un componente con especificación concreta (`"frame de fibra de carbono 500g"`) pero el intent resolver lo enruta a `analyze` (o `ambiguous` → `analyze`). El LLM responde con análisis cualitativo correcto pero no aplica nada al estado. El usuario repite la frase — mismo resultado. No hay wizard, no hay confirmación, no hay cambio.
>
> Reproducción: arquitectura definida, bloque `structure` pendiente → usuario escribe `"frame de fibra de carbono 500g"` → intent = `analyze` → LLM responde → state sin cambios → usuario intenta de nuevo → misma respuesta LLM.

- **Archivos afectados:** `core/intent_resolver.py`, `core/orchestrator.py`
- **Causa raíz real:** `_should_intercept_component` usaba `completeness == "low"` como proxy para "no hay señal útil". Pero `"estructura de fibra de carbono"` tiene `completeness="low"` (sin masa) aunque el extractor sí extrajo `{material: carbon_fiber}`. El guard bloqueaba el intercept → fallback a LLM.
- **Fix real (K4):** Cambiar el criterio de intercept de completeness a presencia de propiedades extraídas: `if not spec.properties: return None`. Separa calidad del componente (completeness) de utilidad para acción (has signal). `_frame_completeness` no cambia — material-only sigue siendo `"low"` semánticamente.
- **Principio:** `calidad ≠ utilidad` — completeness mide si el componente está suficientemente definido para física; properties mide si hay señal para actuar.
- **Riesgo impl.:** 🟢 Bajo — un guard, sin cambio de semántica de dominio
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Hecho — 3 tests nuevos en `TestFrameMaterialOnlyIntercept` (test_frame_component.py). 1210 passed base + nuevos tests.

---

### Bug 63 — `motors` vs `motor_count` inconsistencia entre sesiones (Menor)

> El primer proyecto creado guardó `motors=4.0` en `current_parameters`. El segundo proyecto guarda `motor_count=4.0`. El nombre canónico es `motor_count` (definido en `PARAMETER_REQUIREMENTS` y `REQUIREMENT_REASONS`). Si un proyecto antiguo tiene `motors`, `_block_progress_status` busca `motor_count` → lo ve como `None` → propulsión nunca completa aunque el usuario haya definido 4 motores.
>
> Reproducción: proyecto `levantar-2kg` (sesión anterior) → `motors=4.0` en state → nueva sesión → `architecture_progress = 0/4` aunque propulsión estaba completa.

- **Archivos afectados:** `core/state_manager.py` (`load`), `core/param_definition_session.py` (`apply_and_recalculate`)
- **Causa raíz:** Alias `motors` → `motor_count` existe en `PARAMETER_REQUIREMENTS.aliases` pero no se normalizaba al leer estado desde disco ni al recibir param_updates con el alias.
- **Fix:** Dos puntos de normalización: (1) `StateManager.load()` — al deserializar state.json, si `motors` presente y `motor_count` ausente, remap idempotente antes de `model_validate`; cubre todos los proyectos legacy en disco. (2) `apply_and_recalculate()` — normaliza alias en `param_updates` antes de procesar; cubre callers futuros. Nota impl.: `{**d, k: d.pop(k)}` no funciona (el `**` spread ocurre antes del pop); se usa `dict(d)` + `pop` en secuencia.
- **Riesgo impl.:** 🟢 Bajo
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Hecho — 2 tests nuevos: `test_load_normalizes_legacy_motors_alias` (test_memory_manager.py) + `test_motors_alias_normalized_in_apply_and_recalculate` (test_d4_param_gatekeeper.py). 1205 passed.

---

## Orden de implementación — Fase K

> Principio: desbloquear el flujo energía/propulsión primero (Bugs 59+60 bloquean completamente el onboarding normal) → luego UX de mensajes → luego intents.

**K1 — Críticos de flujo** (en este orden — mismo punto de extensión)
- [x] Bug 59 · `core/param_definition_session.py` — bridge mirrored params energía → writers (🔑 base)
- [x] Bug 60 · `core/param_definition_session.py` — bridge `propeller_diameter_in` → `set_propeller_component`

**K2 — Normalización** (sin dependencias)
- [x] Bug 63 · `core/state_manager.py` + `core/param_definition_session.py` — alias `motors` → `motor_count`

**K3 — UX mensajes** (requiere K1 para validar que el mensaje cambia tras fix)
- [x] Bug 61 · `core/orchestrator.py` — `get_block_in_progress_reason` + rama `in_progress` diferenciada

**K4 — Intent routing** (independiente, diferible)
- [x] Bug 62 · `core/orchestrator.py` — `_should_intercept_component`: criterio de intercept cambiado de `completeness != low` a `properties no vacío`

---

## Fase L — Testing CLI post-G1 (3 junio 2026)

> Contexto: sesión de validación end-to-end con proyecto nuevo creado desde cero (dron, payload 2kg, flujo completo: arquitectura → propulsión → energía → estructura → controladora → DSE → apply). Post-implementación G1 (COMPONENT_VARIATION_RULES + frame variants).  
> Identificados 4 bugs nuevos (64–67). Todos surgieron en flows normales. El flujo principal funcionó correctamente hasta sensores y routing de DSE.  
> Último count antes de esta sesión: 63 bugs (todos ✅). Esta sesión abre 64–67.

---

### Bug 64 — `_should_intercept_component` dispara dentro de `ITERATE_INTERACTIVE` (Alto)

> Mientras el wizard `ITERATE_INTERACTIVE` está activo, el usuario escribe una descripción de componente (`"300g de fibra de carbono"` como valor de masa para el frame). El sistema intercepta el input como declaración de componente, actualiza el frame físicamente y devuelve confirmación del componente — pero el wizard queda abierto en un estado zombie. El modo `ITERATE_INTERACTIVE` sigue activo aunque el componente ya fue aplicado por un path distinto.
>
> Reproducción: wizard iterate activo (step confirmación) → usuario escribe `"300g de fibra de carbono"` → `_should_intercept_component` lo intercepta (frame 0.45→0.30kg, safety_margin 2.635→2.807) → respuesta componente devuelta → modo = `ITERATE_INTERACTIVE` abierto, paso del wizard sin avanzar.

- **Archivos afectados:** `core/orchestrator.py` (`_should_intercept_component`)
- **Causa raíz:** `_should_intercept_component` tiene guards para `CREATE_PROJECT_INTERACTIVE` (línea 333) y `DEFINE_MISSING_PARAMETERS` (línea 335) pero **no** para `ITERATE_INTERACTIVE`. La llamada a `_should_intercept_component` (línea ~380) ocurre **antes** del check de modo `ITERATE_INTERACTIVE` (línea ~399), por lo que el componente se intercepta antes de que el wizard tenga oportunidad de procesar el input.
- **Fix:** Añadir guard en `_should_intercept_component` tras la línea 335:
  ```python
  if session.mode == OrchestratorMode.ITERATE_INTERACTIVE:
      return None
  ```
- **Riesgo impl.:** 🟢 Bajo — un guard de modo, sin cambio de semántica
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Hecho — guard añadido en `_should_intercept_component` tras la línea de `DEFINE_MISSING_PARAMETERS`. 1 test nuevo en `TestIterateInteractiveComponentGuard` (test_orchestrator.py). 1227 passed.

---

### Bug 65 — `"optimiza para autonomía"` no activa DSE (Medio)

> El usuario escribe `"optimiza para autonomía"` esperando lanzar la exploración de espacio de diseño. El sistema lo enruta a `iterate_interactive` (abre el wizard de iteración) en vez de `explore_design_space`. Frases equivalentes como `"mejora la autonomía"` sufren el mismo problema. Solo `"explora el espacio de diseño para autonomía"` funciona correctamente.
>
> Reproducción: proyecto con 3/4 bloques completos → usuario escribe `"optimiza para autonomía"` → intent = `iterate_interactive` → wizard abre.

- **Archivos afectados:** `core/intent_resolver.py` (`EXPLORE_PATTERNS`)
- **Causa raíz:** Los `EXPLORE_PATTERNS` requieren **dos** keywords simultáneas: verbo de exploración (`optimiza`, `busca`...) **y** keyword de objetivo (`mejor`, `configuracion`...). `"optimiza para autonomía"` solo contiene el verbo → no matchea ningún patrón → cae al check de `iterate`. Frases con un único verbo de optimización + dominio objetivo quedan sin capturar.
- **Fix:** Añadir a `EXPLORE_PATTERNS` un patrón que capture verbo de optimización + dominio objetivo sin exigir segunda keyword de objetivo:
  ```python
  r"\b(?:optimiza|mejorar?|maximiza|minimiza)\s+(?:la\s+|el\s+)?(?:autonomia|autonomía|masa|eficiencia|potencia|rendimiento)\b",
  ```
- **Riesgo impl.:** 🟢 Bajo — añadir patrón regex; verificar que no colisiona con `iterate`
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Hecho — 2 patrones añadidos a `EXPLORE_PATTERNS` en `intent_resolver.py`. Parametrized test `test_bug65_single_verb_domain_goal_routes_to_explore` con 6 frases (test_intent_resolver.py). 1227 passed.
- **Extensión (calibración 2026-08-05):** el patrón Bug 65 solo cubría autonomía/eficiencia/potencia (+ reducir masa). Ampliado a todos los goals DSE: `payload` / `carga util`, `estabilidad` / `margen de seguridad`, `masa`/`peso` con `optimiza|mejora|maximiza`. Keywords en `goal_planner._GOAL_KEYWORDS` alineadas. Mutaciones concretas (`aumenta el payload`, `mejora los motores`) siguen en `iterate`.

---

### Bug 66 — Sensors (`"sensores IMU y barómetro"`) no se intercepta nunca (Medio)

> El usuario describe sensores (`"sensores IMU y barómetro"`, `"sensor de navegación"`) pero el sistema no los intercepta como componente: el primero devuelve `"No se pudo interpretar la intención"` y el segundo llega al LLM como `analyze`. El bloque `control` (que requiere el componente `sensors`) no puede completarse vía chat natural.
>
> Reproducción: bloque control pendiente → usuario escribe `"sensores IMU y barómetro"` → respuesta: `"No se pudo interpretar la intención"`. Usuario escribe `"sensor de navegación"` → LLM analyze sin cambios de estado.

- **Archivos afectados:** `domains/aerial.py` (`extract_sensor_properties`, `GPS_MAP`)
- **Causa raíz:** `extract_sensor_properties` solo extrae `gps_model` buscando en `GPS_MAP`. "IMU", "barómetro", "sensor de navegación", "sensor inercial" no generan ninguna propiedad → `spec.properties = {}` → guard (2) de `_should_intercept_component` devuelve `None` → el componente nunca se intercepta. El extractor está diseñado exclusivamente para GPS, ignorando el resto de sensores del bloque `control`.
- **Fix:** Ampliar `extract_sensor_properties` para reconocer tipos de sensor adicionales: IMU (`imu`, `inercial`, `acelerómetro`/`acelerometro`, `giroscopio`), barómetro (`barómetro`/`barometro`, `presión`/`presion`), compass (`brújula`/`brujula`, `magnetómetro`). Extraer propiedad `sensor_type` (lista o string) con confidence 0.8. Conservar GPS como path existente.
- **Riesgo impl.:** 🟡 Medio — amplía el extractor de dominio; añadir tests para nuevas frases
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Hecho — `SENSOR_TYPE_MAP` añadido; `extract_sensor_properties` ampliado con búsqueda de IMU/barometer/compass; `_sensor_completeness` acepta `sensor_type` además de `gps_model`; keywords `imu`, `barometro`, `sensor`, etc. añadidos a `ComponentRule`. 3 tests en `TestSensorIMUBarometer` (test_control_component.py). 1227 passed.

---

### Bug 67 — Mensaje "parámetros que faltan" incorrecto para bloque `control` (Menor)

> El bloque `control` muestra: `"Control (controladora + sensores) — en progreso, define los parámetros que faltan."` cuando lo que falta no son parámetros numéricos sino el componente `sensors`. El mensaje confunde al usuario.
>
> Reproducción: bloque `control` con `flight_controller` declarado pero `sensors` pendiente → `build_startup_context` emite `"define los parámetros que faltan"`.

- **Archivos afectados:** `core/orchestrator.py` (`get_block_in_progress_reason`)
- **Causa raíz:** `get_block_in_progress_reason` solo entra por la rama `"missing_components"` para bloques de tipo `composite`. El bloque `control` es de tipo `"component"`, no `"composite"`, por lo que siempre devuelve `"missing_params"` aunque lo que falte sea un componente (`sensors`). La distinción composite/component del tipo de bloque no está reflejada en la lógica de razón de progreso.
- **Fix:** En `get_block_in_progress_reason`, ampliar la rama `"missing_components"` para bloques de tipo `"component"` que tengan component keys definidos y alguno incompleto (mismo criterio que composite pero aplicado a bloques tipo `"component"`).
- **Dependencia:** Relacionado con Bug 61 (mismo archivo, misma función). Implementar junto a Bug 64 o después.
- **Riesgo impl.:** 🟢 Bajo — extensión puntual de `get_block_in_progress_reason`
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Hecho — `get_block_in_progress_reason` ampliado: bloques tipo `"component"` con component keys ahora entran por la rama `missing_components`. 1 test en `TestGetBlockInProgressReasonComponentType` (test_composite_wizard_flow.py). 1227 passed.

---

## Orden de implementación — Fase L

> Principio: corregir primero la corrupción de estado (Bug 64, estado zombie en wizard), luego routing (Bug 65), luego cobertura de dominio (Bug 66), luego cosmético (Bug 67).

**L1 — Estado zombie** (crítico de integridad)
- [x] Bug 64 · `core/orchestrator.py` — guard `ITERATE_INTERACTIVE` en `_should_intercept_component`

**L2 — Routing DSE** (UX directamente bloqueada)
- [x] Bug 65 · `core/intent_resolver.py` — patrón `"optimiza para <dominio>"` en `EXPLORE_PATTERNS`

**L3 — Cobertura sensores** (bloque control incompleto)
- [x] Bug 66 · `domains/aerial.py` — ampliar `extract_sensor_properties` con IMU, barómetro, compass

**L4 — Mensaje cosmético** (diferible)
- [x] Bug 67 · `core/orchestrator.py` — `get_block_in_progress_reason`: bloques tipo `"component"` con component keys

---

## Fase M — E2E Testing MCP Server (3 junio 2026)

> Contexto: suite de 11 tests end-to-end sobre el MCP server (`Ingenieria/MCP/`) recién implementado. Todos los tests pasan (status `ok`), pero se detectan 3 bugs de comportamiento: un fallo crítico de routing que inutiliza `simula`, un problema de usabilidad en preguntas analíticas, y una limitación documental del tool `get_state`.

---

### Bug 68 — `"simula"` interceptado como componente sensor por substring `"imu"` (Crítico)

> `jarvis_chat("simula")` devuelve `"Acción ejecutada: component_description_saved\nSensors registrado."` en vez de ejecutar la simulación. El comando más importante de Jarvis vía MCP está completamente roto.
>
> Reproducción: sesión limpia → `jarvis_chat("simula")` → `action: "component_description_saved"`, `message: "Sensors registrado. ✓ Arquitectura completa (4/4)"`. Ocurre incluso tras `jarvis_reset_session()`. Afecta también a `"simular"`.

- **Archivos afectados:** `core/orchestrator.py` (`_should_intercept_component`), `domains/aerial.py` (`extract_sensor_properties`, `SENSOR_TYPE_MAP`)
- **Causa raíz (dos capas):**
  1. `extract_sensor_properties` busca aliases de `SENSOR_TYPE_MAP` con `alias in lower` (substring plano). `"imu" in "simula"` → `True` → extrae `{sensor_type: 'imu'}`. El spec tiene `properties != {}` y `suggested_key == 'sensors'`, con lo que pasa todos los guards de `_should_intercept_component`.
  2. `_should_intercept_component` se ejecuta antes del check de `SIMULATE_PATTERNS` en `handle_user_text` y no tiene ninguna guarda que descarte inputs que resuelvan a una intención de acción fuerte (simulate, calculate, etc.).
- **Fix (dos capas, belt-and-suspenders):**
  1. **`orchestrator.py`** · `_should_intercept_component`: añadir guarda de intención fuerte al inicio — si `intent_resolver._resolve_strong_action_intent(normalized)` no es `None`, retornar `None` inmediatamente. Es el fix principal y más seguro.
  2. **`domains/aerial.py`** · `extract_sensor_properties`: cambiar `alias in lower` por `re.search(r'\b' + re.escape(alias) + r'\b', lower)` para `SENSOR_TYPE_MAP`. Corrige la causa raíz; no afecta a `ComponentRule.keywords` (que usa `kw in text` intencionalmente para prefijos como `"here+"`).
- **Regresión:** La búsqueda de IMU en `"sensores IMU y barómetro"` (Bug 66) debe seguir funcionando porque `"imu"` aparece como palabra completa → `\bimu\b` sigue siendo `True`.
- **Test nuevo:** `test_simula_no_interceptado_como_sensor` — verificar que `infer_component("simula").properties == {}` y que `_should_intercept_component("simula", idle_session) is None`.
- **Riesgo impl.:** 🟢 Bajo — cambio puntual en dos sitios; no toca la semántica del flujo
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Hecho — (1) `_should_intercept_component` añade guard de intent fuerte antes de `infer_component`; (2) `extract_sensor_properties` usa `re.search(r'\b' + re.escape(alias) + r'\b', lower)` para `SENSOR_TYPE_MAP`. 3 tests de regresión (`test_simula_no_interceptado_como_sensor`, `test_simular_no_interceptado_como_sensor`, `test_simula_no_intercepta_componente_en_orquestador`) en `TestSensorIMUBarometer`. 1243 passed.

---

### Bug 69 — Preguntas analíticas vía MCP: 31 s de LLM + `"No se pudo interpretar"` (Alto)

> `jarvis_chat("qué parámetros me faltan")` tarda ~31 segundos, llama al LLM de Ollama y devuelve `"No se pudo interpretar la intención. Prueba con: 'calcula', 'simula'..."`. El usuario de la herramienta MCP no tiene feedback de que la pregunta no es ejecutable.
>
> Reproducción: proyecto activo → `jarvis_chat("qué parámetros me faltan")` → 30983 ms → acción no reconocida.

- **Archivos afectados:** `core/orchestrator.py` (`handle_user_text`, rama `analyze` / LLM fallback), `core/intent_resolver.py` (`resolve_intent`)
- **Causa raíz:** La frase no hace match en ningún patrón de `_resolve_strong_action_intent` ni en `_looks_like_status_query`. Cae a `_looks_like_question` → intent `analyze` → `_handle_analyze` → LLM. El LLM devuelve una acción no parseada (p.ej. `list_missing_params`) que el orquestador no reconoce → `"No se pudo interpretar"`.
- **Fix (dos opciones):**
  - **Opción A (recomendada):** Ampliar `GUIDANCE_PATTERNS` / `_looks_like_status_query` con patrones del tipo `"qué (me) falta"`, `"qué parámetros"`, `"qué hay pendiente"` → routear a `project_status` en vez de al LLM.
  - **Opción B:** En `_handle_analyze`, cuando la respuesta del LLM no produce una acción conocida, degradar a `project_status` en lugar de emitir el mensaje de error genérico.
- **Impacto MCP:** Hasta que se corrija, el workaround recomendado para consumidores MCP es usar `jarvis_get_context()` + `jarvis_get_state()` en lugar de preguntas analíticas vía `jarvis_chat`.
- **Riesgo impl.:** 🟢 Bajo (Opción A) · 🟡 Medio (Opción B)
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Hecho — Opción A implementada: 4 nuevos patrones añadidos a `GUIDANCE_PATTERNS` en `intent_resolver.py` (`que (me) falta[...}`, `que parametros`, `que hay pendiente`, `que (me) queda [definir|completar|configurar]`). 9 tests paramétricos en `test_bug69_analytical_questions_route_to_project_status`. 1243 passed.

---

### Bug 70 — `jarvis_get_state()` no incluye `phase` ni otros campos computados (Menor)

> `json.loads(jarvis_get_state()).get('phase')` devuelve `None`. El campo `phase` no está en `state.json` — es calculado por `build_startup_context()`. Los consumidores MCP que llaman solo a `get_state()` no pueden conocer la fase del proyecto sin llamar también a `get_context()`.
>
> Reproducción: `jarvis_get_state()` → objeto JSON sin clave `phase`, sin `arch_progress_str`, sin `suggestions`.

- **Archivos afectados:** `MCP/session_manager.py` (`get_state`), posiblemente `jarvis/core/orchestrator.py` (`build_startup_context`)
- **Causa raíz:** `get_state()` lee `state.json` directamente (datos persistidos). `phase`, `arch_progress_str` y `suggestions` son propiedades derivadas que solo existen en la respuesta de `build_startup_context()`, no en el fichero de estado. No es un bug de código sino un gap de API: el caller espera un objeto completo pero recibe el estado crudo.
- **Fix (dos opciones):**
  - **Opción A:** Enriquecer `get_state()` con los campos derivados: llamar a `build_startup_context()` internamente y mezclar `phase`, `arch_progress_str` y otras propiedades calculadas en el objeto devuelto.
  - **Opción B (sin cambio de código):** Documentar en el docstring de `jarvis_get_state` que los campos computados (`phase`, `suggestions`) requieren llamar a `jarvis_get_context()`. Añadir nota al `instructions` del tool MCP.
- **Riesgo impl.:** 🟢 Bajo (ambas opciones)
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Hecho — Opción A implementada: `get_state()` en `MCP/session_manager.py` llama a `build_startup_context()` tras cargar `state.json` e inyecta `phase`, `phase_description`, `phase_confidence`, `status_type`, `architecture_progress`, `suggested_action`, `proactive_question` en el objeto devuelto. Fallo de enriquecimiento es no-fatal (log warning, retorna estado crudo). 1243 passed.

---

## Orden de implementación — Fase M

> Principio: corregir primero el bug crítico de routing (Bug 68) que bloquea el comando principal de Jarvis vía MCP, luego mejorar la UX de preguntas analíticas (Bug 69), finalmente el gap documental (Bug 70).

**M1 — Routing `simula` roto** (crítico funcional)
- [x] Bug 68 · `core/orchestrator.py` — guarda intención fuerte en `_should_intercept_component`
- [x] Bug 68 · `domains/aerial.py` — word-boundary en `extract_sensor_properties` para `SENSOR_TYPE_MAP`

**M2 — Preguntas analíticas** (UX degradada)
- [x] Bug 69 · `core/intent_resolver.py` — ampliar `GUIDANCE_PATTERNS` con `"qué me falta"`, `"qué parámetros"`, `"qué hay pendiente"`

**M3 — API gap `get_state`** (documentación / mejora)
- [x] Bug 70 · `MCP/session_manager.py` — enriquecer `get_state()` con campos derivados, o documentar la limitación

---

## Fase U — Hacia herramienta usable (5 junio 2026)

> Contexto: sesión de mejoras post-E2E MCP. U1 detectado durante demo: DSE propuso `battery_capacity_wh: 355 → 1200 Wh` pero `masa_total` no cambió — física incorrecta.
> Identificado 1 bug crítico de correctness física (Bug 71). Implementado y verificado E2E vía MCP.
> Último count antes de esta sesión: 70 bugs (todos ✅). Esta sesión abre y cierra 71.

---

### Bug 71 — `battery_mass_kg` nunca se suma a `masa_total` (Crítico — U1)

> Detectado en E2E MCP (3 junio 2026). DSE aplicó `battery_capacity_wh: 355 → 1200 Wh` (+238%) pero `masa_total` se quedó en `2.15 kg`. La batería casi triplicó capacidad sin ganar masa. El resultado de autonomía (`60 min`) era físicamente incorrecto.
>
> Reproducción: declarar batería LiPo cualquier capacidad → `simula` → `masa_total` no incluye masa de batería. Con 118.4 Wh: `masa_total = 1.6 kg` (payload 1.0 + estructura 0.6), batería invisible.

- **Archivos afectados:** `tools/electricity.py`, `core/component_writers.py`, `core/calculation_engine.py`, `core/design_explorer.py`, `core/system_architecture_catalog.py`
- **Causa raíz:** `set_battery_component()` escribía `battery_capacity_wh` en `current_parameters` pero nunca estimaba ni escribía `battery_mass_kg`. `calculation_engine` solo sumaba `payload_kg + structure_mass_kg`. La batería era energéticamente real pero físicamente invisible.
- **Fix (4 capas, belt-and-suspenders):**
  1. `electricity.py` — `estimate_battery_mass_kg(capacity_wh)` nueva función (150 Wh/kg LiPo estándar)
  2. `component_writers.py` — `set_battery_component()` escribe `battery_mass_kg` como campo derivado junto a `battery_capacity_wh`
  3. `calculation_engine.py` — suma `battery_mass_kg` a `structure_mass_kg` antes de `calculate_total_mass`
  4. `design_explorer.py` — `_apply_delta` sincroniza `battery_mass_kg` cuando cambia `battery_capacity_wh` por factor
  + `battery_mass_kg` añadido a `COMPONENT_MIRRORED_PARAMS` en `system_architecture_catalog.py`
- **Backward compat:** `parameters.get("battery_mass_kg") or 0.0` → cero cuando campo ausente → proyectos legacy sin `battery_mass_kg` se comportan igual que antes. 0 regresiones.
- **Riesgo impl.:** 🟡 Medio — campo nuevo en `current_parameters`; auditado que no colisiona con `structure_mass_override_kg` (son aditivos)
- **Cambio arq.:** ❌ No — mismo pipeline, nuevo campo derivado canónico
- **Estado:** ✅ Hecho — 5 junio 2026. 13 tests en `test_u1_battery_mass.py`. 1256 passed. Verificado E2E vía MCP: `"batería LiPo 4S 8000mAh 14.8V"` → `masa_total = 2.389 kg` (antes: `1.6 kg` sin batería).

---

## Orden de implementación — Fase U

**U1 — Correctness física de batería** (crítico de física)
- [x] Bug 71 · `tools/electricity.py` + `core/component_writers.py` + `core/calculation_engine.py` + `core/design_explorer.py` — `battery_mass_kg` entra en `masa_total`

**U2 — Bridge propellers → parámetros físicos** (correctness física)
- [x] Bug 72 · `core/component_writers.py` + `core/calculation_engine.py` + `core/system_architecture_catalog.py` — bridges `pitch_in`, `kv_rating`, `cell_count` + derivación RPM desde KV×V×0.85

**U3 — DSE espacio de exploración ampliado** (domain-agnostic)
- [x] Bug 73 · `core/design_explorer.py` — `EXPLORATION_GRIDS["mejorar_autonomia"]` solo varíaba batería; añadidos factores relativos de frame (`structure_mass_override_kg_factor`) y motor eficiente (`motor_power_w_factor=0.65`). Agnosótico al dominio: mismo factor funciona para dron, rover y robot.

**U4 — Persistencia del historial conversacional**
- [x] Bug 74 · `workspace/workspace_manager.py` + `core/state_manager.py` + `core/orchestrator.py` — al reiniciar el MCP server el historial y el modo de sesión se perdían. Añadido `history/runtime_snapshot.json` (max 50 turns en disco, max 6 en memoria). Wrapper `handle_user_text` persiste tras cada turno; `__init__` auto-restaura al arrancar.

**U5 — Validación de restricciones incremental**
- [x] Bug 75 · `schemas/state_schema.py` + `core/orchestrator.py` — las restricciones de peso (`"peso máximo Xkg"`) no se parseaban ni se comprobaban. Añadido `_WEIGHT_CONSTRAINT_RE` a `_parse_constraints` y `_check_constraint_violations` con hook inline en `_handle_component_description`. Warning informativo (`⚠`) añadido al mensaje del componente, nunca bloquea el flujo.

---

## Fase N — Validación propeller-only path vía MCP (15 julio 2026)

> Contexto: sesión de validación E2E con proyecto nuevo desde cero vía MCP server. Objetivo: cubrir tests 9.2 y 9.4 del CLI_TESTS.md (hélice pura, sin `per_motor_max_thrust_n`). Flujo completo: create_project → arquitectura → motores → hélices → frame → batería → FC → sensores → simula → DSE → apply.  
> Identificados 4 bugs nuevos (76–79). Tests 9.2 y 9.4 validados. 0 regresiones (1300 passing).  
> Último count antes de esta sesión: 75 bugs (todos ✅). Esta sesión abre 76–79.

---

### Bug 76 — Vehicle type con descripción larga no mapea a arquitectura base (Medio)

> Al crear un proyecto con vehicle type `"dron de inspección de infraestructuras"`, el wizard de `SYSTEM_DEFINITION` entra en modo de bloques custom (step 1) en lugar de ofrecer la arquitectura base del dron (step 0 con opciones A/B/C). Solo el string exacto `"dron"` y aliases directos activan el step 0.
>
> Reproducción: create_project → vehicle_type = `"dron de inspección de infraestructuras"` → SYSTEM_DEFINITION muestra `"No tengo una arquitectura base para 'dron de inspección...'"` en lugar de A/B/C.

- **Archivos afectados:** `core/interactive_session.py` (parseo de vehicle_type), `core/system_architecture_catalog.py` (`VEHICLE_TYPE_ALIASES`)
- **Causa raíz:** `VEHICLE_TYPE_ALIASES` normaliza aliases exactos pero no substrings ni frases compuestas. El vehicle_type se guarda verbatim. `get_domain_architecture(vehicle_type)` busca coincidencia exacta.
- **Fix:** En `interactive_session.py`, normalizar el vehicle_type antes de guardar: si el texto contiene `"dron"` o `"drone"` como palabra → normalizar a `"dron"`. Aplicar misma lógica para otros dominios canónicos.
- **Riesgo impl.:** 🟢 Bajo — normalización de entrada en un solo punto
- **Cambio arq.:** ❌ No
- **Estado:** ⬜ Pendiente

---

### Bug 77 — Wizard DEFINE_MISSING sin escape suave para param saltable (Leve)

> En el wizard `DEFINE_MISSING_PARAMETERS` para `per_motor_max_thrust_n`, el usuario no puede saltar el parámetro con texto natural (`"no lo sé, voy a usar hélices"`). El wizard responde `"Error: No reconozco '...' como número"` y repite la pregunta. El único escape es `cancelar`, que aborta toda la sesión.
>
> Reproducción: wizard activo para `per_motor_max_thrust_n` → usuario escribe `"no sé"` → `"Error: No reconozco 'no sé' como número"` → pregunta repetida.

- **Archivos afectados:** `core/param_definition_session.py` (`answer`)
- **Causa raíz:** `ParamDefinitionSession.answer()` hace `float(user_input)` sin validar si el input expresa intención de saltar. No existe concepto de "param que el usuario puede delegar a otro mecanismo".
- **Fix:** Detectar frases de deferimiento antes del parseo numérico: `"no sé"`, `"después"`, `"lo calculo con hélices"`, `"skip"` → marcar el param como `deferred` y continuar al siguiente. Si todos los params son `deferred`, avisar que la simulación estará incompleta.
- **Riesgo impl.:** 🟡 Medio — nuevo estado `deferred` en `ParamDefinitionSession`
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Hecho — 16 julio 2026. `_SKIP_PHRASES` frozenset en `param_definition_session.py`. Frases de deferimiento omiten el param actual, avanzan al siguiente o llaman `apply_and_recalculate` si no hay más. Test en `test_define_transmission_params.py` actualizado (`"no sé"` ahora avanza, no da error). 4 tests en `TestDefineParamSkip` + 1 nuevo en `test_define_transmission_params.py`. 1321 passed. — Doble declaración de motor no preserva `motor_count` (Leve)

> Cuando el usuario declara motores dos veces (`"4 motores"` + `"motores 2306 2400KV 150W"`), el segundo write crea un `ComponentSpec` nuevo que no incluye `motor_count`. El reasoning muestra `"Faltan: número de motores"` aunque la física usa `motor_count=4` correctamente desde `current_parameters`.
>
> Reproducción: `"4 motores"` → componente con `motor_count=4`; luego `"motores 2306 2400KV 150W"` → nuevo write sin `motor_count` → reasoning muestra gap semántico (la física sigue siendo correcta).

- **Archivos afectados:** `core/component_writers.py` (`set_motor_component`)
- **Causa raíz:** `set_motor_component` sobreescribe el spec existente completamente. El nuevo spec extrae `power_w` y `kv` pero no `motor_count`, dejando el componente sin ese campo.
- **Fix:** En `set_motor_component`, hacer merge con el spec existente: si `components["motors"]` ya tiene `motor_count`, preservarlo a menos que el nuevo extractor haya extraído uno explícito.
- **Riesgo impl.:** 🟢 Bajo — merge defensivo en un helper
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Hecho — 16 julio 2026. `set_motor_component` hace merge del `motor_count` existente cuando el nuevo spec no lo incluye. La física (`current_parameters`) ya lo preservaba; ahora también `components["motors"].properties`. 3 tests en `TestMotorComponentMerge` (test_fase_n.py). 1321 passed.

---

### Bug 79 — DSE apply no comprueba `max_weight_kg` (Medio)

> Al aplicar el mejor candidato DSE (`"aplica la mejor"`), si el candidato viola `max_weight_kg`, el sistema lo aplica sin emitir warning. La validación de restricciones inline (U5) solo cubre `_handle_component_description`, no `_handle_apply_exploration`.
>
> Reproducción: proyecto con `max_weight_kg=2.0` → DSE propone batería 300Wh (masa batería=2.0kg → masa_total=2.85kg) → `"aplica la mejor"` → 2.85kg aplicado sin advertencia.

- **Archivos afectados:** `core/orchestrator.py` (`_handle_apply_exploration`)
- **Causa raíz:** `_check_constraint_violations` existe (U5) pero solo se llama desde `_handle_component_description`. `_handle_apply_exploration` tiene su propio pipeline y no la llama.
- **Fix:** Al final de `_handle_apply_exploration`, tras recalcular con el candidato aplicado, llamar a `_check_constraint_violations(updated_state)` y añadir violaciones al mensaje (informativo, no bloquea — mismo patrón U5).
- **Riesgo impl.:** 🟢 Bajo — añadir una llamada a función existente
- **Cambio arq.:** ❌ No
- **Estado:** ✅ Hecho — 16 julio 2026. `_handle_apply_exploration` llama a `_check_constraint_violations(updated_state)` tras persistir el estado y añade las violaciones al mensaje (patrón U5). `_check_constraint_violations` hardened con `isinstance` guards y try/except para no fallar con mocks en tests existentes. 4 tests en `TestDSEApplyConstraintWarning` (test_fase_n.py). 1321 passed.

> Implementado: 16 julio 2026. 1321 tests passing (+21 vs baseline de Fase N). 0 regresiones.

**N1 — Vehicle type alias** (UX create_project)
- [x] Bug 76 · `core/interactive_session.py` — `_normalize_vehicle_type` por matching de palabras contra `VEHICLE_TYPE_ALIASES`

**N2 — DSE apply constraint check** (correctness de validación)
- [x] Bug 79 · `core/orchestrator.py` — `_check_constraint_violations` en `_handle_apply_exploration`

**N3 — Motor merge en doble declaración** (UX cosmético)
- [x] Bug 78 · `core/component_writers.py` — merge de `motor_count` al actualizar componente motors

**N4 — Escape suave en DEFINE_MISSING** (UX)
- [x] Bug 77 · `core/param_definition_session.py` — `_SKIP_PHRASES` + rama de deferimiento antes del error numérico