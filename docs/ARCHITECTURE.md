# Jarvis Architecture

## Modelo conceptual del sistema

Jarvis transforma en tres pasos:

```text
Design intent (declarativo)
↓  component_resolver — bridge declarativo → físico
Physical parameters (computables)
↓  calculation_engine — modelo físico
Evaluation (simulación)
↓  simulator — evaluación de viabilidad
```

Este modelo es domain-agnostic: el mismo pipeline sirve para cualquier dominio físico.
Lo que cambia entre dominios es el vocabulario de `output_magnitude` y las reglas del `ComponentRuleRegistry`.
El núcleo (resolver, engine, simulator) no conoce el dominio.

## Visión General

Jarvis está estructurado como un motor de ingeniería por capas, no como un chatbot.

La idea central es separar claramente:

- interpretación de intención
- control del flujo
- memory ligera de decisiones explícitas
- mutación del diseño
- cálculo
- simulación
- sugerencias deterministas
- persistencia

Flujo conceptual actual:

```text
Arranque CLI
↓
_list_existing_projects → proyectos en disco
  ├─ ninguno → "Cuéntame qué quieres diseñar"
  └─ hay proyectos → mostrar lista + opción n/1/2...
       ├─ n → instrucción libre (loop normal)
  └─ 1..N / texto ordinal ("continuar", "el más reciente", "uno"...) → touch(state.json) + build_startup_context() [sin LLM]
       └─ Continuity (situation / evidence / next_useful_step) dentro del startup context
Input de usuario
  │
  ├─ sesión activa (CREATE_PROJECT_INTERACTIVE)
  │     └─ interactive_session.answer(session, input)          [sin LLM]
  │           └─ confirmado → create_project → SYSTEM_DEFINITION
  │
  ├─ sesión activa (SYSTEM_DEFINITION)
  │     └─ system_definition_session.answer(input)             [sin LLM]
  │           └─ completado → stubs + system_priority → bridge → DEFINE_MISSING_PARAMETERS
  │
  ├─ sesión activa (DEFINE_MISSING_PARAMETERS)                 [sin LLM]
  │     ├─ soft-interrupt project_status / analyze
  │     ├─ FN-013/014/015: re-prompt bloque activo / help-define pendiente
  │     ├─ FN-016: "atrás"/"volver" → cancel (no valor)
  │     ├─ descripción de componente (+ Brief FN-018; bare size FN-019 si aplica)
  │     └─ param_definition_session.answer / component path
  │           └─ al completar último bloque → clear → IDLE (FN-021)
  │
  ├─ sesión activa (ITERATE_INTERACTIVE)
  │     ├─ classify_input_intent → "information" / "hybrid" → _handle_analyze
  │     └─ classify_input_intent → "action" → iterate_interactive_session.answer
  │
  ├─ IDLE — Acquisition Target (FN-014/015): "definir/declarar <bloque|componente>"
  │     └─ resolve_acquisition_mention → DEFINE_MISSING / Brief          [sin LLM]
  │
  ├─ intent_resolver: project_status / GUIDANCE
  │     ("estado…", "siguiente paso", "ayúdame con el siguiente paso" FN-023…)
  │     └─ build_startup_context() + Continuity                          [sin LLM]
  │
  ├─ intent_resolver: explore_design_space ("optimiza para autonomía"…)
  │     └─ _handle_explore → DesignExplorer                              [sin LLM]
  │
  ├─ intent_resolver: apply_exploration_result ("aplica la mejor"…)
  │     └─ _handle_apply_exploration → calculate → simulate → save       [sin LLM]
  │
  ├─ IDLE — Engineering Intent (FN-022): intención sin valor numérico
  │     ("aumentar el empuje", …) → is_engineering_intention
  │     └─ format_goal_plan + CTA (0 LLM; DSE solo si luego exploran)
  │
  ├─ intent_resolver: acción clara (calcular, simular, iterate con valor…)
  │     └─ ActionRequest local                                           [sin LLM]
  │
  ├─ intent_resolver: analyze (pregunta, "qué pasa si"…)
  │     └─ LLM (puede anteponer format_goal_plan si detect_goal)         [LLM]
  │
  └─ intent_resolver: ambiguous / unknown
        └─ LLM → JSON → ActionRequest → Mutation / Calculation / Simulation
```

> **Autoridad:** el estado del proyecto / Continuity / Acquisition Target eligen el *siguiente objetivo de ingeniería*. El LLM interpreta lenguaje; no inventa el gap pendiente. Sin Conversation Engine. Step D (Guided Engineering ampliado) y Create→BOM: fuera de este mapa hasta aprobación explícita — ver `docs/PROJECT_CONTINUITY.md` e `IMPLEMENTATION_TASKS.md`.

## Capas Del Sistema

### 1. Contratos y schemas

Los contratos viven en `schemas/`.

- `action_schema.py`
  Define acciones, modos del orquestador, drafts temporales y parámetros estructurados.
- `state_schema.py`
  Define el estado persistente del proyecto, `design_properties` y el estado temporal de runtime.
  Campos clave de `ProjectState`:
  - `current_parameters: dict` — parámetros de entrada del usuario (payload, motores, restricciones, material como etiqueta).
  - `design_properties: DesignProperties` — propiedades estructurales del diseño. `structure.density` y `structure.volume` son la **fuente canónica** de las propiedades físicas del material; `_build_mutable_state` las lee aquí con fallback a `current_parameters` para compatibilidad con estado antiguo.
  - `parsed_constraints: dict[str, float]` — restricciones parseadas a tipo. Clave actual: `autonomy_min`. Poblado automáticamente en carga vía `@model_validator` que extrae minutos de la cadena libre `restrictions`. El simulador recibe `autonomy_threshold: float | None` — nunca el string crudo.
- `tool_schema.py`
  Define `ToolResult`, `CalculationBundle` y el contrato rico de simulación.

Esto evita lógica difusa y fuerza entradas y salidas explícitas.

### 2. Orquestación

El núcleo está en `core/orchestrator.py`.

Responsabilidades:

- recibir `ActionRequest`
- aceptar texto natural a través de la interfaz LLM
- detectar si hay sesión interactiva activa
- abrir `create_project_interactive` o `iterate_interactive`
- disparar acciones reales tras confirmación
- delegar en el router
- exponer planificación opcional mediante `build_plan(...)`

El mapeo `action -> handler` está en `core/action_router.py`.

#### Deuda técnica: dispersión de lógica de control

> **Estado: resuelto.** Ver `_handle_global_commands` a continuación.

En versiones anteriores, parte de la lógica de control global (escapes, shortcuts de arranque) estaba distribuida entre `main.py` y los session handlers. La regla de diseño aplicada: todo comando global vive en el orquestador, la CLI es un adaptador I/O puro.

#### `_handle_global_commands(user_input) → dict | None`

Primer check incondicional de `handle_user_text` — se ejecuta antes de cualquier modo de sesión, ingesta o intent resolver.

Maneja dos tipos de comandos:

- **Escape** (`cancelar`, `cancel`, `salir`, `abortar`, `abort`): llama a `state_manager.clear_runtime_session()` si hay sesión activa y devuelve `{status: "cancelled"}`. Si no hay sesión activa, devuelve `None` (el input cae al flujo normal — puede ser una pregunta válida).
- **Shortcut de creación** (`n`, `nuevo`, `nuevo proyecto`, `crear`): devuelve directamente `handle({action: create_project})` sin pasar por el LLM.

Los session handlers (`iterate_interactive_session`, `ParamDefinitionSession.answer`) mantienen su propio escape interno como fallback para callers directos (tests, tools). El orquestador coordina; los módulos internos siguen siendo coherentes por sí solos.

Orden de ejecución en `handle_user_text`:
```text
1. _handle_global_commands            ← comandos universales (escape, nuevo proyecto)
2. modo de sesión activo
   - CREATE_PROJECT_INTERACTIVE        ← delega a create_project wizard
   - ITERATE_INTERACTIVE               ← soft interrupt / classify / hard preempt / wizard
   - DEFINE_MISSING_PARAMETERS         ← soft-interrupt status; FN-013/015; nav-back FN-016;
                                         component description + Brief; param wizard
   - SYSTEM_DEFINITION                 ← system_definition_session
3. IDLE Acquisition Target (FN-014/015) ← mention gate / bare help-define → acquisition
4. intent resolver                    ← sin LLM (GUIDANCE/status antes que ANALYZE)
5. IDLE Engineering Intent (FN-022)   ← iterate|unknown + is_engineering_intention → goal_plan
6. acciones locales / explore / apply ← calculate, simulate, iterate-con-valor, DSE…
7. fallback LLM                       ← último recurso
```

Existe además una CLI mínima para validación humana real en `python -m jarvis.main --chat`.
Esa CLI usa Ollama local como cliente LLM real.
La integración actual usa dos modos:

- acciones estructuradas: `format=json`, `stream=false`
- `analyze`: texto natural (sin `format` en el payload)

### 2b. Human Layer Sprint v1 — capa conversacional

Módulos añadidos sobre el flujo base para hacer el sistema más comunicativo y orientado al usuario.

#### `intent_resolver.py` — `classify_input_intent(text)`
Clasificación ligera (sin LLM) de texto libre en tres categorías:
- `"information"`: preguntas, peticiones de estado, análisis → no mutan estado
- `"action"`: comandos de iteración, definición, cálculo → pueden mutar estado
- `"hybrid"`: combinación ambigua → tratado como `information` dentro de sesión activa

Uso principal: guardia en `ITERATE_INTERACTIVE` para evitar que preguntas informativas abran el wizard de iteración (Fix 1).

#### `main.py` — `WARNING_MESSAGES` / `_human_warning(code)`
Diccionario `WARNING_MESSAGES: dict[str, str]` que mapea códigos de warning del simulador (`low_margin`, `high_actuator_load`, `low_force_to_weight_ratio`, `autonomy_below_restriction`) a descripciones en español legibles por el usuario.

`_human_warning(code)` devuelve la descripción o el código sin cambios si no está en el diccionario.

#### `core/goal_planner.py` — Goal Planner híbrido
Detecta objetivos de diseño en lenguaje natural y genera planes estratégicos priorizados.

- `GOAL_STRATEGIES: dict[str, list[dict]]` — catálogo de estrategias por objetivo
- `detect_goal(text) → str | None` — keywords para `aumentar_payload`, `mejorar_autonomia`, `reducir_masa`, `mejorar_estabilidad` (incluye empuje/thrust → `mejorar_estabilidad`)
- `looks_like_numeric_mutate` / `is_engineering_intention` — FN-022: intención bare sin dígitos → `goal_key`; con valor numérico → cede a iterate
- `_prioritize_strategies(key, strategies, sim_context) → list[dict]` — reordena según `safety_margin_ratio` / warnings
- `format_goal_plan(key, sim_context) → str` — bloque determinista para el usuario
- `get_goal_context_for_llm(key) → str` — contexto inyectado al prompt LLM

**Dos usos:**
1. **IDLE Engineering Intent (FN-022):** gate en orquestador antes de iterate → `_handle_engineering_intent` → `format_goal_plan` + CTA a vocabulario DSE existente — **0 LLM**, sin auto-DSE.
2. **`_handle_analyze`:** si `detect_goal` → antepone `format_goal_plan` al análisis LLM.

Residual documentado: frases que ya matchean `EXPLORE_PATTERNS` (`mejorar estabilidad`…) siguen auto-DSE; no unificar en este mapa (ver `.jes/artifacts/residual_engineering_intent_plan_vs_explore.md`).

#### Acquisition Fluency + Continuity (FN-014…021, FN-023)

Módulos deterministas; el LLM no elige el siguiente target de adquisición.

| Módulo | Rol |
|---|---|
| `core/acquisition_target.py` | Autoridad de mención bloque∪componente; `COMPONENT_PROMPTS`; help-define / nav-back helpers |
| `core/acquisition_brief.py` | Brief fino (qué / qué sabe Jarvis / pregunta) reutilizado en open / re-prompt / help |
| `core/project_continuity.py` | `build_project_continuity` → situation / evidence / `next_useful_step` |
| `core/project_closure.py` | BOM + `classify_component` / `component_presence_tier` (FN-020: una clasificación para arch↔BOM↔Continuity) |
| `config.NAVIGATION_BACK_WORDS` | `atras`/`volver`/`vuelve` — solo wizards de adquisición (FN-016), no escape global |

Orquestador (IDLE / DEFINE_MISSING): gates FN-014…018, bare propeller vía `infer_component_for_key` (FN-019), clear a IDLE al cerrar arquitectura (FN-021). Detalle de field notes: `docs/PROJECT_CONTINUITY.md`.

### 3. Estado temporal vs persistente

Hay dos tipos de estado:

- estado temporal en memoria
- estado persistente en disco

#### Temporal

Lo mantiene `core/state_manager.py` mediante `runtime_state`.

Sirve para:

- modo actual del orquestador
- step actual
- drafts temporales

#### Persistente

Lo guarda `state.json` dentro de cada proyecto.

Sirve para:

- parámetros actuales del sistema
- resultados más recientes
- historial
- memory mínima del proyecto
- iteración activa

Separación clave:

- el draft no toca disco
- el estado real solo cambia tras confirmación y ejecución

### 4. Workspace como fuente de verdad

Cada proyecto vive como un workspace en disco.

Ruta por defecto actual para proyectos:

- `Projects/Jarvis/workspace/` (vía `JARVIS_WORKSPACE_ROOT` o default relativo al paquete)

`jarvis/runtime/` queda reservado para artefactos internos como `llm_logs`.

Estructura:

```text
proyecto/
├── state.json                ← ÚNICA fuente de verdad
├── views/                    ← representaciones derivadas (read-only, generadas automáticamente)
│   ├── objetivo.md
│   ├── sistema.md            ← refleja system_defined + system_blocks + components
│   ├── estado_actual.md      ← parámetros actuales + última simulación
│   └── reasoning.md          ← último output de ReasoningLayer (tras iterate/simulate)
├── history/                  ← trazabilidad append-only
│   ├── events.jsonl          ← log de eventos del sistema (append-only, timestamp UTC)
│   ├── iterations/           ← iter_NNN.json (JSON estructurado: change + mutation + impact + calcs + sim)
│   ├── simulations/          ← sim_NNN.json (resultado de simulación standalone)
│   └── calculations/         ← calc_NNN.json (resultado de cálculo standalone)
└── meta/
    └── project_config.json

```

Reglas de oro:
- `state.json` nunca se reconstruye desde archivos — es la fuente
- las vistas (`views/`) son siempre derivadas, nunca editables manualmente
- `events.jsonl` es append-only — no editar, no borrar
- `history/` ≠ estado
- **`workspace_path` repair (5 ago 2026):** al cargar via `StateManager.load(state_path)`, si `workspace_path` falta o no coincide con el directorio real de `state.json` (proyectos migrados / path legacy), se reescribe al path actual y se persiste. Evita `PermissionError` al guardar historia/vistas.

Todo esto lo gestiona `workspace/workspace_manager.py` (+ repair en `core/state_manager.py`).
Las vistas se generan con las funciones de `workspace/render_views.py`.
`file_writer.append_jsonl()` garantiza el contrato append-only del log de eventos.

## Flujo `create_project`

### Inicio

Puede entrar de dos formas:

1. Acción directa con parámetros completos.
2. Modo interactivo `create_project_interactive`.

### Draft temporal

La sesión guiada vive en `core/interactive_session.py`.

Tronco común (siempre):

1. tipo de sistema — normalizado via `_normalize_vehicle_type()` (`VEHICLE_TYPE_ALIASES`)
2. objetivo
3. payload
4. restricciones
5. nivel de detalle — `conceptual` aplica defaults de `structure_mass_factor` / `safety_factor`; `detallado` los pregunta

Ramas por dominio (`VEHICLE_TYPE_ALIASES` → aéreo `dron`/`uav` o terrestre `robot`/`coche`/`rover`):

- **Aéreo:** número de motores → vía de fuerza (`empuje` → `per_motor_max_thrust_n` | `hélices` → `propeller_diameter_in` + `propeller_rpm` | `no sé` → sin valores ficticios)
- **Terrestre:** número de actuadores (campo `motors`) → vía (`torque` → `per_actuator_torque_nm` | `fuerza` → `max_force_per_actuator_n` | `no sé`)
- **Desconocido:** salta la rama y va a confirmación

Confirmación (step 90). Durante el wizard no se calcula, no se simula, no se crea workspace ni se persiste.

### Ejecución real

La acción real vive en `actions/create_project.py`.

Qué hace:

- crea workspace
- inicializa parámetros base
- ejecuta `calculation_engine`
- ejecuta simulación
- genera sugerencias no vinculantes basadas en el resultado
- guarda artefactos
- actualiza `state.json`

## Flujo `iterate`

### Inicio

Cuando entra `iterate`, el sistema:

1. resuelve el proyecto activo
2. carga `state.json`
3. abre sesión interactiva

### Draft temporal + estado semántico

La sesión guiada vive en `core/iterate_interactive_session.py`.
Las constantes de dominio y validadores puros (vocabulario del sistema, dominio cerrado de variables válidas, materiales conocidos, normalización y fuzzy matching) viven en `core/iterate_domain.py`. Tras el Domain Registry refactor, `iterate_domain.py` es una **capa de adaptación**: sus símbolos públicos (`_VARIABLE_NORMALIZATION`, `_SEMANTIC_MUTATION_PARAMS`, `_VALID_VARIABLE_DOMAIN`) son vistas computadas desde `parameter_requirements.py` — no fuentes hardcodeadas. `IteratePrompt` (dataclass de preguntas UX) permanece en el archivo de sesión por ser flujo conversacional, no dominio.

Cada input del usuario pasa por dos fases antes del routing:

1. **Seed desde draft**: los campos ya confirmados en `IterationDraft` se añaden al
   `SemanticState` como slots `confirmed` (confianza 1.0). Esto garantiza que el
   estado semántico siempre sabe lo que ya está resuelto.
2. **Enriquecimiento**: `semantic_interpreter.update()` extrae slots del nuevo input
   y los fusiona al estado sin borrar información previa.

Tras el enriquecimiento, `semantic_interpreter.decide()` determina la acción:

- `proceed` (confianza ≥ 0.75 en todos los slots requeridos) → avanzar al paso 3 (restricciones)
- `confirm` (slots presentes, confianza media) → avanzar al paso 3 con mensaje de confirmación
- `clarify` (slot ausente o confianza < 0.4) → preguntar solo el slot que falta
- forzado tras `MAX_CLARIFICATION_ROUNDS = 2` → avanzar con lo disponible

El paso 3 (restricciones) siempre se muestra — nunca se salta. El paso 4 (impacto) solo se alcanza desde el paso 3.

Los slots requeridos son `operation` y `variable`. Con ellos `mutation_engine` puede ejecutar.
Las restricciones son siempre preguntadas pero opcionales — si el usuario no responde (enter vacío), el sistema las registra como `"ninguna"` y avanza.

### Tipos de variable en el wizard (Bugs 14/15)

`IterateInteractiveSession._classify_variable_type(variable, current_params)` clasifica la variable del paso 1 en una de 7 categorías para seleccionar la pregunta correcta en paso 2.  
**Esta clasificación gobierna solo el texto de la pregunta (UX) — no la ejecución.** La decisión de si una mutación es físicamente ejecutable sigue siendo responsabilidad exclusiva de `mutation_engine.is_physically_actionable()` (Bug 3).

| Categoría | Condición | Pregunta paso 2 |
|---|---|---|
| `semantic_mutation` | `PARAMETER_REQUIREMENTS.get(variable).variable_type == VariableType.SEMANTIC_MUTATION` (ej: `payload_kg`) — verificado PRIMERO vía registro; estos params existen también en `current_parameters` numéricamente pero su mutación es conceptual (reducir/aumentar), nunca set-to-value | `"¿Cómo quieres modificar el payload? Indica valor concreto (ej: +10%, -0.5 kg)"` |
| `numeric_direct` | Clave numérica en `current_parameters` — seguro aquí porque `semantic_mutation` ya filtró el registro; además fires antes de `structural_*` para que `"factor_estructura"` no caiga en `structural_abstract` | `"¿Cuál es el nuevo valor de X? (actual: Y)"` |
| `material` | `"material"` en variable | Genérica (sub-flujo captura nombre explícito) |
| `structural_physical` | `"dimension"`, `"volum"`, `"geometr"` — cuantificable | Avisa que se necesita factor cuantitativo; sin él el cambio queda declarativo |
| `structural_abstract` | `"estructur"`, `"forma"`, `"topolog"` — siempre declarativo | Avisa que no hay impacto físico computable |
| `component_define` | `_is_supported_define_variable()` — abre sub-flujo de definición | Pregunta de componente/material |
| `unknown` | Fallback | Pregunta genérica |

El orden de prioridad **más específico primero** garantiza que variables como `"factor_estructura"` (que contiene `"estructur"`) resuelven correctamente a `numeric_direct` porque el param existe en `current_parameters`.

**Escape global del wizard:** en cualquier paso del flujo `ITERATE_INTERACTIVE`, el usuario puede escribir `cancelar`, `cancel`, `salir`, `abortar` o `abort`. `IterateInteractiveSession.answer()` lo detecta como primera comprobación (antes de cualquier procesamiento de step) y devuelve `{status: "cancelled"}`. El orquestador (`handle_user_text`) llama entonces a `state_manager.clear_runtime_session()` para restaurar el modo `NONE`. Esta comprobación es incondicional — no depende del step actual ni de si hay un conflicto activo.

**Preempción de intents fuertes (calibración 2026-08-05):** si el wizard está abierto y el input resuelve a un intent de acción fuerte (`explore_design_space`, `calculate`, `simulate`, `create_project`, `define_params`, `iterate`, `dismiss_suggestion`) o a una descripción de componente (probe con sesión idle; el guard Bug 64 sigue bloqueando el intercept directo), el orquestador cierra la sesión, re-despacha el turno como idle y prefija el mensaje con un aviso (`preempted_iterate: true`). Excepción: no se preemptan componentes cuando el wizard **posee** el input (`DEFINE` en step 2, o `motor_suggestions` activo) — así el flujo de sugerencias de motor / define-component no se aborta. Respuestas de paso del wizard (`sí`, nombres de variable, etc.) no hacen match y siguen el flujo normal. `project_status` / `analyze` siguen siendo soft interrupt (Bug 7).

`SemanticState` se serializa en el dict de respuesta de cada turno (clave `"semantic_state"`) y se restaura en `_session_from_response` del orquestador. Esto garantiza que `focus`, `entities` y `active_intent` sobreviven entre inputs del usuario dentro de la misma sesión interactiva.

`SemanticState` incluye tres campos de contexto de sesión más allá de los slots:

- `focus`: componente activo sobre el que se está trabajando (se hereda entre pasos)
- `entities`: lista de entidades mencionadas en la sesión (componentes, materiales)
- `active_intent`: intención semántica detectada (`modify_component`, `define_components`...)

### Sub-loop multi-entidad

Cuando el usuario menciona dos o más componentes a la vez en el paso 2 (`define`):

1. `semantic_interpreter.extract_entities()` detecta las entidades
2. El sistema pregunta por cuál empezar (o "todos" para registrar con detalle bajo)
3. Los componentes restantes se guardan en `pending_entities`
4. El sub-loop procesa cada uno antes de avanzar al paso 3

### Enriquecimiento cruzado de sesión

Cuando el usuario escribe `"completar especificación del motor"` tras una sesión anterior:

1. `ITERATE_PATTERNS` detecta `completar|especificar|enriquecer`
2. `resolve_action_request` extrae `enrich_component` de la frase (`"de/del X"`)
3. El orquestador carga `project_state.design_properties.components` y lo pasa como `known_components`
4. `iterate_interactive_session.start()` llama a `_seed_semantic_from_state` con esos componentes
   y establece `focus = enrich_component` en `SemanticState`
5. La sesión arranca en el paso 2 directamente con la pregunta enfocada en ese componente

Esto evita reiniciar la sesión desde el paso 0 y mantiene el contexto del componente parcialmente definido.

Campos del draft que se completan durante la sesión:

- objetivo
- variable
- operación (siempre `IterationOperation` enum, nunca raw string)
- estrategia
- valor declarativo si aplica
- impacto estimado
- confirmación final

### Impacto estimado

Antes de ejecutar se muestra una estimación preliminar.

Esto no modifica estado real.
Solo sirve para interacción guiada.

### Mutación real

Tras confirmación entra `core/mutation_engine.py`.

Responsabilidad:

- traducir `iteration_draft -> state_patch + impact`

No hace:

- cálculo físico
- simulación
- persistencia

Estrategias v0:

- material
- volumen
- payload

Tipos actuales de iteración:

- física: `reducir`, `aumentar`, `mejorar`, `optimizar`
- declarativa: `define`

## Snapshot de estado del proyecto

### `build_startup_context()`

Ubicación: `core/orchestrator.py`

Función pública del orquestador que construye un snapshot estructurado del estado actual del proyecto **sin invocar el LLM**. Es la única fuente de verdad para describir el estado del proyecto — tanto el display automático de arranque como las consultas on-demand usan este mismo builder.

```text
build_startup_context(workspace_path?) → dict
```

Flujo:
1. `state_manager.load_active_project()` — lee `state.json` fresco (sin caché)
2. `_build_analyze_context()` — construye contexto estructurado del proyecto
3. `reasoning_layer.build(context)` — extrae señales deterministas
4. Aplica jerarquía de status (prioridad estricta):
   - `blocking` — `signals["missing_physics_parameters"]` (dominio terrestre sin params de transmisión)
   - `warning`  — `signals["has_warnings"]` (simulación con warnings)
   - `nominal`  — `signals["has_simulation"]` (simulación válida sin warnings)
   - `no_data`  — ninguna simulación previa
5. Selecciona `active_variables` (máx 3) según status:
   - blocking → `["motor_count", "per_actuator_torque_nm", "payload_kg"]`
   - warning/nominal → `["payload_kg", "motor_count", "safety_margin_ratio"]`
   - no_data → `["payload_kg", "motor_count", "safety_factor"]`
6. Genera `suggested_action` desde el top `ReasoningSuggestion` + `hint` accionable

Estructura de retorno:
```python
{
    "has_project": True,
    "project_slug": str,
    "objective": str,
    "status_type": "blocking" | "warning" | "nominal" | "no_data",
    "status_reason": str | None,        # ej. "missing_transmission_parameters" | "missing_propulsion_parameters"
    "active_variables": dict[str, Any], # máx 3
    "suggested_action": {
        "label": str,
        "reason": str,
        "hint": str | None,             # ej. 'Puedes responder: "0.15 y 10"'
    } | None,
    "phase": str,                       # "definition" | "physical_validation" | "optimization" | "complete"
    "phase_description": str,
    "phase_confidence": float,
    "proactive_question": str | None,   # presente si hay parámetros bloqueantes ausentes
    "missing_params": list[str] | None, # parámetros que activan DEFINE_MISSING_PARAMETERS
    "param_definition_reason": str,     # reason code del trigger de parámetros
    # Arquitectura de sistema (None cuando system_defined=False)
    "architecture_progress": str | None,    # ej. "1/4"
    "next_architecture_block": str | None,  # clave del bloque pendiente
    "next_architecture_label": str | None,  # etiqueta humana del bloque
    "next_block_status": str | None,        # "not_started" | "in_progress"
}
```

### Startup display

Cuando el usuario selecciona un proyecto en la CLI (`run_chat()`), se llama `build_startup_context()` y el resultado se renderiza vía `render_startup_context()` (función pura en `main.py`, sin lógica) antes del primer turno.

Si el contexto incluye `proactive_question`, la CLI inicia automáticamente una sesión `DEFINE_MISSING_PARAMETERS`. Triggers (prioridad descendente):
1. Parámetros de transmisión ausentes (fase `definition` + `status_type=blocking`)
2. Parámetros de energía ausentes (`missing_energy_parameters` signal, cualquier fase)
3. Parámetros de hélice ausentes con hint (`propeller_status="missing_propeller_parameters"`)
4. Bloque de arquitectura composite `not_started` — Phase A: componentes; Phase B: parámetros numéricos
5. Bloque de arquitectura param-driven o component-driven pendiente

### Intent `project_status` (+ Continuity)

Cuando el usuario escribe frases como `"estado del proyecto"`, `"resumen"`, `"qué falta"`, `"siguiente paso"` o `"cómo va el proyecto"`, `IntentResolver` las clasifica como `project_status` (no `analyze`). El orquestador las atiende en `_handle_project_status()`, que delega en `build_startup_context()` — misma fuente de verdad, cero llamadas LLM. El contexto incluye `continuity` (`situation` / evidence / `next_useful_step`).

`STATUS_PATTERNS` vive separado de `QUESTION_PATTERNS`. `_looks_like_status_query()` se evalúa antes que `_looks_like_question()` cuando no hay strong-action previo.

**FN-023:** `"ayúdame con el siguiente paso"` (y variantes) iría a `analyze` por el `\bayudame\b` de `ANALYZE_PATTERNS`. Se corrige en `GUIDANCE_PATTERNS` (evaluados **antes** de ANALYZE en `_resolve_strong_action_intent`) → `project_status`. Continuity sigue siendo la única autoridad del siguiente paso; no hay recommender paralelo.

### Modo `DEFINE_MISSING_PARAMETERS`

Dos sub-modos bajo el mismo `OrchestratorMode.DEFINE_MISSING_PARAMETERS`, diferenciados por `param_definition_reason`:

**Sub-modo A — Component description** (`reason = MISSING_COMPONENT_DEFINITION`):  
Activado cuando el siguiente bloque de arquitectura es `component` o el siguiente bloque composite (Phase A) tiene componentes ausentes. La pregunta de apertura / re-prompt / help usa `acquisition_brief.build_acquisition_brief` + `acquisition_target.COMPONENT_PROMPTS` (no el genérico `¿Cuál es el valor de X?`). `_handle_component_description()` gestiona el input:
- `infer_components` y, si aplica, `infer_component_for_key` (FN-019: bare `"10x4.5"` con `propellers` en `expected_keys`)
- Rechazo de `generic_component` cuando hay `expected_keys` (FN-017)
- Routing por `suggested_key` → writers (`_set_motor_component`, `_set_propeller_component`, …)
- Cuando el bloque está completo → `_set_pending_next_block()`; si no hay siguiente bloque y el modo sigue DEFINE_MISSING → `clear_runtime_session()` → IDLE (FN-021)

**Sub-modo B — Param wizard numérico** (`reason ∈ {MISSING_PROPULSION_PARAMETERS, MISSING_ENERGY_PARAMETERS, MISSING_TRANSMISSION_PARAMETERS, MISSING_PROPELLER_PARAMETERS}`):  
Activado para blocks param-driven o composite Phase B (componentes ya completos, params ausentes).
1. `build_startup_context()` produce `proactive_question` + `missing_params` + `param_definition_reason`
2. La CLI inicia `JarvisOrchestrator.start_define_missing_params(missing_params, reason)`
3. Cada input pasa por `ParamDefinitionSession.answer()`:
   - Parseo semántico por keywords; fallback posicional
   - Acumula en `session.collected_params`
   - **Skip phrases** (`_SKIP_PHRASES`): si el usuario escribe `"no sé"`, `"omitir"`, `"skip"` u otras frases de deferimiento, el parámetro actual se omite (se elimina de `pending_param_definitions`) y se avanza al siguiente. Si todos los params han sido respondidos o omitidos, se llama a `apply_and_recalculate`. El param omitido no se escribe en `current_parameters` — queda como `None` hasta que el usuario lo defina posteriormente.
   - Cuando completo → `apply_and_recalculate()` → parchea `current_parameters` → recalcula → persiste

El campo `param_definition_reason` incluye: `"missing_transmission_parameters"`, `"missing_propulsion_parameters"`, `"missing_energy_parameters"`, `"missing_propeller_parameters"`, `"missing_component_definition"`.

Este flujo no toca `mutation_engine` ni `IterateInteractiveSession`.

**Escape global:** `cancelar` / `cancel` / `salir` / `abortar` → `clear_runtime_session()`.

**Navegación de adquisición (FN-016):** `atrás` / `volver` / `vuelve` (`NAVIGATION_BACK_WORDS`) cancelan el wizard de DEFINE_MISSING sin tratarse como valor numérico ni como escape global fuera de adquisición. Las claves de componente nunca reciben un float posicional.

### Bloque de arquitectura composite — Wizard de dos fases

Bloques composite (actualmente `energy` y `propulsion`) requieren AND-strict: `params_ok AND components_ok`. El wizard se orquesta vía `_set_pending_next_block()` y `build_startup_context()`:

```text
Phase A (not_started, componentes ausentes)
  build_startup_context → proactive_question + missing_params=["motors","propellers"]
  _set_pending_next_block → session.pending_missing_reason = MISSING_COMPONENT_DEFINITION
  → _handle_component_description procesa cada componente
  → cuando todos presentes → _set_pending_next_block → Phase B

Phase B (in_progress, componentes OK, params ausentes)
  build_startup_context → next_block_status="in_progress"
  _set_pending_next_block → session.pending_missing_reason = MISSING_PROPULSION_PARAMETERS
  → ParamDefinitionSession recoge motor_count + per_motor_max_thrust_n
  → apply_and_recalculate → bloque pasa a complete
```

`_block_progress_status(block, design_properties, params)` implementa la lógica AND-strict:
- `not_started`: ni params ni componentes definidos
- `in_progress`: uno de los dos satisfecho
- `complete`: ambos satisfechos

## Modo `SYSTEM_DEFINITION`

Transición de "intención" → "arquitectura de sistema estructurada". Se lanza automáticamente
tras confirmar `create_project`. Puebla `design_properties.components` con stubs declarados
antes de entrar en cálculo/iteración.

### Flujo

```text
create_project confirmado
↓
system_definition_session.start(vehicle_type, project_state)
  ├─ dominio conocido → step=0 (oferta A/B/C con bloques base del catálogo)
  └─ dominio desconocido → step=1 (modo B directo)

answer(user_input)
  step=0 → A (aceptar base) | B (añadir bloques) | C (saltar)
  step=1 → recoge bloques custom hasta "listo" | alias → bloque canónico | texto libre → registrado sin expandir
  → _apply_and_finish() → persiste stubs + system_priority, cierra sesión
  → bridge: priority[0] → get_param_reason_for_block() → ParamDefinitionSession.start()
```

### Catálogos de datos (sin imports de jarvis.schemas)

`core/system_architecture_catalog.py`:
- `SYSTEM_ARCHITECTURES` — bloques base + etiquetas por dominio (`dron`, `uav`, `robot`, `coche`, `rover`)
- `BLOCK_TYPE` — tipo de bloque: `"param"` | `"component"` | `"composite"`. Estado actual:
  - `"composite"`: `propulsion` (Fase 6: motors + propellers + params), `energy` (Fase 4: battery + motors + params)
  - `"component"`: `structure`, `control`
  - `"param"`: `actuation`, `transmission`
- `BLOCK_TO_COMPONENTS` — bloque → component keys (strings primitivos)
- `BLOCK_TO_PARAM_REASON` — bloque → reason code; entradas: `propulsion`, `actuation`, `energy`
- `COMPONENT_MIRRORED_PARAMS` — frozenset de params que son mirror de `components[*].properties`; solo escribibles via helpers (`battery_capacity_wh`, `motor_power_w`, `propeller_diameter_in`)
- `VEHICLE_TYPE_ALIASES` — normaliza aliases (`"drone"` → `"dron"`, `"quadcopter"` → `"dron"`, etc.)
- `BLOCK_ALIASES` — texto libre del usuario → bloque canónico (22 entradas)
- API pública: `get_domain_architecture()`, `blocks_to_component_keys()`, `normalize_block_alias()`, `get_param_reason_for_block()`, `get_block_type()`

`core/system_dependency_catalog.py`:
- `SYSTEM_DEPENDENCIES` — dependencias entre bloques por dominio
- Normalización via `VEHICLE_TYPE_ALIASES` — misma clave canónica que `system_architecture_catalog`
- API pública: `get_domain_dependencies(vehicle_type)`

### DependencyGraph y PriorityEngine

`core/system_dependency_graph.py`:
- `DependencyGraph` (frozen dataclass) — `dependencies: dict[str, list[str]]`
- `get_dependencies(block)`, `get_dependents(block)`
- `build_dependency_graph(vehicle_type, blocks)` — filtra el catálogo a los bloques presentes; bloques custom sin entrada en catálogo reciben `deps=[]`

`core/priority_engine.py`:
- `compute_priority_order(graph)` — DFS topológico
- Protección ante ciclos: `visited` + `visiting`; ciclos emiten `warnings.warn`, sin crash
- Output: lista ordenada de menos a más dependiente, p.ej. `["propulsion", "energy", "structure", "control"]`

El orden derivado reemplaza el antiguo `recommended_start` hardcodeado en el catálogo de arquitecturas. El campo `system_priority: list[str]` se persiste en `DesignProperties`.

### Reglas de prioridad (no-sobrescritura de componentes)

`source:       user(2) > inferred(1) > declared(0)`
`completeness: high(2) > medium(1)   > low(0)`

`_should_skip(existing)` → `True` si `source_rank > 0` OR `completeness_rank > 0`. Los stubs nuevos (`completeness=low, source=declared`) nunca sobreescriben componentes ya enriquecidos.

### Estado persistido

`DesignProperties` gana tres campos:
- `system_defined: bool` — flag de sesión completada
- `system_blocks: list[str]` — bloques elegidos (base + custom)
- `system_priority: list[str]` — orden topológico derivado del grafo

### Riesgos conocidos (deuda técnica)

1. `SYSTEM_DEPENDENCIES` es estático — no derivado de la física del proyecto
2. `compute_priority_order` ignora `payload`, `restrictions` y parámetros actuales — el orden es el mismo para todo proyecto del mismo dominio
3. `ReasoningLayer` no consume `system_priority` ni `DependencyGraph` — los insights causales ("no puedes mejorar autonomía sin tocar propulsión") están diferidos

## Sistema multi-dominio

### Principio de diseño

El sistema fue inicialmente diseñado para drones (dominio aéreo). La capa de componentes
estaba acoplada al vocabulario propulsivo (motores brushless, hélices, KV). La arquitectura
multi-dominio desacopla esa taxonomía del núcleo y la convierte en un artefacto intercambiable.

Principio rector: **"primero cambias el significado, luego cambias el nombre"**. Todos los
renames destructivos están diferidos hasta que un caller real genere confusión semántica.
Mientras tanto se usan aliases y frozensets.

### ComponentRule y ComponentRuleRegistry

Ubicación: `core/component_rules.py`

Contratos de comportamiento (Protocols, `runtime_checkable`):

- `PropertyExtractor(normalized: dict) → dict` — extrae propiedades de un componente normalizado
- `CompletenessEvaluator(props: dict) → tuple[str, list[str]]` — devuelve `(nivel, campos_faltantes)`

`ComponentRule` (frozen dataclass):

- `keywords: frozenset[str]` — palabras clave que identifican este tipo de componente
- `component_type: str` — tipo semántico (`"propulsion_active"`, `"traction_active"`, etc.)

`_COMPONENT_PROMPTS: dict[str, str]` — prompts UX por component key (`"frame"`, `"battery"`, `"motors"`, `"propellers"`, `"flight_controller"`, `"sensors"`). Usados en `_component_prompt_for_first_missing()` para guiar al usuario.

`_BLOCK_COMPONENT_HINTS: dict[str, str]` — hints de Phase A por bloque composite/component, usados en `build_startup_context()` para el `proactive_question` inicial. Entradas: `"structure"`, `"control"`, `"energy"`, `"propulsion"`.
- `suggested_key: str` — clave sugerida para el componente
- `inference_confidence: float` — confianza base del match
- `property_extractor: PropertyExtractor | None`
- `completeness_evaluator: CompletenessEvaluator | None`
- `missing_field_hints: list[str]` — preguntas de completeness
- `extra_hints: list[str]` — preguntas adicionales opcionales
- `output_magnitude: str | None` — clave de la propiedad que representa la magnitud física de salida del componente (ej. `"thrust_n"` para motor aéreo, `"torque_nm"` para motor de tracción). El resolver la usa para parametrizar elegibilidad y resolución de fuerza sin hardcodear nombres de dominio.
- `matches(normalized: dict, name_lc: str) → bool` — matching por keywords

`ComponentRuleRegistry`:

- lista ordenada de `ComponentRule`
- `first-match-wins`
- `register(rule)`, `match(normalized, name_lc) → ComponentRule | None`

### Dominio aéreo

Ubicación: `domains/aerial.py`

Tres reglas registradas en `aerial_registry = ComponentRuleRegistry([propeller_rule, motor_rule, esc_rule])`:

| Tipo | `component_type` | `suggested_key` | Propiedades extraídas |
|---|---|---|---|
| Motor brushless | `propulsion_active` | `motors` | `kv`, `thrust_n`, `motor_count`, `watts` |
| Hélice | `propulsion_passive` | `propellers` | `diameter_in`, `pitch_in`, `count` |
| ESC | `esc` | `esc` | `current_a` |

`_set_propeller_component(project_state, spec)` — extraído a `core/component_writers.py` (D6). Escribe en `components["propellers"]` y hace el bridge físico: lee `spec.properties["diameter_in"]` y escribe `current_parameters["propeller_diameter_in"]` (o elimina la clave si el valor es `None`). El engine recibe `propeller_diameter_in` como parámetro normal.

Extractores usan regex sobre el nombre normalizado del componente (sin LLM).

Campo `output_magnitude`: motor brushless → `"thrust_n"` · hélice y ESC → `None`.

### Dominio terrestre

Ubicación: `domains/ground.py`

Dos reglas registradas en `ground_registry = ComponentRuleRegistry([traction_active_rule, rolling_passive_rule])`:

| Tipo | `component_type` | Propiedades extraídas |
|---|---|---|
| Motor de tracción | `traction_active` | `motor_count`, `torque_nm`, `rpm` |
| Rueda pasiva | `rolling_passive` | `wheel_count` |

Campo `output_magnitude`: motor de tracción → `"torque_nm"` · rueda pasiva → `None`.

Decisión de diseño: `torque_nm` se extrae en el resolver pero la conversión a fuerza ocurre
en el engine. El resolver inyecta `per_actuator_torque_nm` via `apply_to` al dict de parámetros.
El engine lee `per_actuator_torque_nm + wheel_radius_m + gear_ratio` de `current_parameters`, que
el usuario debe declarar explícitamente (sin fallback implícito). Si faltan, el engine registra
`missing_transmission_parameters` en `tool_results` y devuelve `available_total_thrust_n = None`.

Para vehículos aéreos sin ninguna ruta de fuerza (sin thrust declarado, sin torque, sin geometría de hélice), el engine registra `missing_propulsion_parameters` con los parámetros `["motor_count", "per_motor_max_thrust_n"]`. La decisión de dominio está centralizada en `AERIAL_VEHICLE_TYPES` (frozenset en `calculation_engine.py`) — un único punto de decisión sin lógica duplicada downstream.

### Routing de dominio (registry_selector)

Ubicación: `domains/registry_selector.py`

```python
def get_registry(vehicle_type: str | None = None, text: str | None = None) → ComponentRuleRegistry
```

Tres niveles de prioridad:

1. **vehicle_type explícito** — si está en `_VEHICLE_TYPE_MAP` determina el dominio de forma
   determinísta, sin importar el contenido del texto. **Anula completamente la heurística.**
2. **Heurística de texto** — cuenta hits de keywords en `_AERIAL_KEYWORDS` y `_GROUND_KEYWORDS`
   sobre el texto normalizado; gana el dominio con más hits (sin ties)
3. **Default** — `aerial_registry` (compatibilidad hacia atrás)

`_VEHICLE_TYPE_MAP` incluye: `drone/dron/uav/quadcopter/multirotor` → aéreo;
`rover/car/coche/vehicle/ground/robot/ugv` → terrestre.

Hooks de integración:

- `mutation_engine.py` lee `state.get("vehicle_type")` y pasa el registro correcto a `infer_component`
- `IterateInteractiveSession._registry_for_session(session, text)` — helper que lee
  `session.memory_context.get("vehicle_type")` y llama a `get_registry`; todos los call sites
  de `infer_component` en `iterate_interactive_session.py` usan este helper (5 sitios)

Persistencia de `vehicle_type` — dos gaps cerrados para garantizar que el tipo de dominio
llega correctamente a ambos hooks:

- `actions/iterate.py` → `_build_mutable_state`: incluye `"vehicle_type"` en el dict
  mutable para que `mutation_engine` lo lea directamente
- `core/orchestrator.py` → seed de `iterate_interactive_session.start()`: `memory_context`
  incluye `vehicle_type` de `current_parameters` además de `ProjectMemory`

### Component inference (dispatcher)

Ubicación: `core/component_inference.py`

Dispatcher puro (~60 líneas). El registro se inyecta en cada llamada:

```python
infer_component(raw_name, raw_value=None, registry: ComponentRuleRegistry | None = None)
```

- `registry=None` usa `_DEFAULT_REGISTRY = aerial_registry` (compatibilidad hacia atrás)
- Fallback genérico cuando ninguna regla coincide: `suggested_key="generic_component"`, `confidence=0.4`
- Propaga `rule.output_magnitude` al `ComponentSpec` resultante; `None` si no hay regla coincidente o si la regla no define magnitud

### Component resolver (puente declarativo → físico)

Ubicación: `core/component_resolver.py`

**Es el único componente que traduce intención declarativa en parámetros físicos utilizables por el motor de cálculo.** Sin él, todo lo declarado en `design_properties.components` es invisible para la física.

Función:

- convertir `design_properties.components` en overrides efímeros de parámetros de actuadores
- actuar como puente entre el mundo declarativo (ComponentSpec) y el modelo físico (CalculationBundle)

**Los overrides son estrictamente efímeros**: se calculan en RAM, se aplican una vez antes
de `calculation_engine.build()` y nunca se persisten en `state.json`.

Cambios de la arquitectura multi-dominio:

- `_ACTIVE_ACTUATOR_TYPES = frozenset({"propulsion_active", "traction_active"})` — reemplaza
  la constante `"propulsion_active"` para soportar ambos dominios sin cambio destructivo
- `PhysicalOverride` — clase principal; `PropulsionOverride = PhysicalOverride` como alias
- `resolve_physical_parameters` — función principal; `resolve_propulsion_parameters` como alias

`PhysicalOverride` mantiene los campos originales (`motors`, `per_motor_max_thrust_n`, `per_actuator_torque_nm`) para
compatibilidad, y expone aliases genéricos como propiedades:

```python
@property def actuator_count(self) → int | None: return self.motors
@property def max_force_per_actuator_n(self) → float | None: return self.per_motor_max_thrust_n
```

Campo `per_actuator_torque_nm: float | None = None` — se extrae del componente cuando `output_magnitude == "torque_nm"` y el valor está declarado con `source="declared"`. Se inyecta al dict de parámetros via `apply_to`, donde el engine lo toma para la conversión.

Regla de elegibilidad de un componente:

- `component_type in _ACTIVE_ACTUATOR_TYPES`, Y
- `completeness in ("medium", "high")` O la propiedad identificada por `output_magnitude` declarada con `source="declared"`
- Componentes con `completeness="low"` y sin valor declarado explícito son ignorados

Resolución de `motors` / `actuator_count`:

1. `properties["motor_count"].value` si existe explícitamente
2. Conteo de entries elegibles como fallback

Resolución de `per_motor_max_thrust_n` / `max_force_per_actuator_n`:

- Solo cuando `output_magnitude == "thrust_n"` — fuerza lineal directa (dominio aéreo)
- Lee `properties["thrust_n"].value` con `source="declared"`
- Otros `output_magnitude` (ej. `"torque_nm"`) producen conteo de actuadores pero no override de fuerza
- Sin heurísticas de texto — si no está declarado con `source="declared"`, no se aplica override

Principio rector: **el resolver extrae, el engine interpreta**. La conversión de magnitudes (torque → fuerza, etc.) no es responsabilidad del resolver.

Trazabilidad — cuatro estados semánticos del resolver, mutuamente excluyentes:

```text
skipped              → no pasó elegibilidad (completeness bajo, sin declaración explícita)
count_only           → elegible y contado en motors, output_magnitude sin valor declarado o magnitud no conocida
missing_parameters   → elegible, contado, torque extraído y pasado al engine — conversión pendiente de parámetros externos
force_resolved       → fuerza extraída de properties["thrust_n"] con source="declared"
```

El trace incluye:
- `force_resolution_status` — estado global (máximo rango entre todos los entries elegibles)
- `force_resolution_detail` — lista con una entrada por componente elegible (`key` + `force_resolution_status` + `reason`)
  - `reason` valores: `missing_transmission_parameters` | `thrust_n_declared` | `thrust_n_not_declared` | `output_magnitude=<magnitud>`
- `eligible_for_count_only` — lista original con `reason` y `torque_nm_extracted` si aplica
- `skipped` — componentes descartados antes de elegibilidad

Rango de precedencia: `force_resolved (3) > missing_parameters (2) > count_only (1)`

- `skipped` — componente descartado en elegibilidad (completeness bajo, sin declaración)
- `eligible_for_count_only` — componente elegible y contado en `motors`, pero `output_magnitude` no soporta conversión directa a fuerza; cuando `output_magnitude == "torque_nm"` y el valor está declarado, se añade `torque_nm_extracted` a la entrada; el valor extraído se propaga a `PhysicalOverride.per_actuator_torque_nm`. En `force_resolution_detail` estos componentes aparecen como `missing_parameters`.
- fuerza resuelta — `per_motor_max_thrust_n` extraído de `properties["thrust_n"]`. En `force_resolution_detail` aparecen como `force_resolved`.

### Remap API → params internos (`workspace_manager.py`)

La API pública (`CreateProjectParams`) usa `motors: int | None` como nombre del campo (convención de la acción `create_project`). Al crear el workspace, `workspace_manager.create_project()` hace el remap:

```python
if "motors" in _params_dict:
    _params_dict["motor_count"] = _params_dict.pop("motors")
```

Esto ocurre **una sola vez en la frontera de entrada**. Todo el código downstream usa `motor_count`. La key `components["motors"]` (ComponentSpec) no se toca — son objetos y namespaces distintos.

### Recálculo

El recálculo vive en `core/calculation_engine.py`.

API dual-vocabulario:

- Acepta `actuator_count` o `motor_count` (el primero tiene precedencia). `motor_count` es el key canónico interno desde Fase 6 — el remap de `motors` → `motor_count` ocurre en `workspace_manager.create_project()`.
- Acepta `max_force_per_actuator_n` o `per_motor_max_thrust_n` (el primero tiene precedencia)

Esto permite usar el mismo motor de cálculo desde dominios aéreo y terrestre sin cambio destructivo.

Resolución de `per_motor_max_thrust_n` / `max_force_per_actuator_n`:

- **Ruta aérea** (prioridad): si `max_force_per_actuator_n` o `per_motor_max_thrust_n` están en `parameters` → fuerza directa
- **Ruta terrestre**: si `per_actuator_torque_nm` + `wheel_radius_m` + `gear_ratio` están en `parameters` → llama `calculate_traction_force_from_torque` → fuerza de tracción
- **Ruta incompleta (terrestre)**: `per_actuator_torque_nm` presente pero faltan parámetros de transmisión → registra `ToolResult(tool_name="missing_transmission_parameters")` en `tool_results`; `available_total_thrust_n = None`
- **Ruta hélice**: sin fuerza directa ni torque → acepta `propeller_diameter_in` (alias en pulgadas, se convierte `× 0.0254 → propeller_diameter_m`) o `propeller_diameter_m` (canónico interno) + `propeller_rpm` → llama `calculate_thrust_from_propeller`
- **Ruta incompleta (aéreo, hint presente)**: vehicle_type aéreo + algún param de `_PROPELLER_HINT_PARAMS` (`propeller_diameter_m`, `propeller_diameter_in`, `propeller_rpm`) presente pero incompleto → registra `ToolResult(tool_name="missing_propeller_parameters")`; `available_total_thrust_n = None`
- **Ruta incompleta (aéreo, sin hint)**: vehicle_type aéreo sin ningún dato de hélice → registra `ToolResult(tool_name="missing_propulsion_parameters")`; `available_total_thrust_n = None`
- Sin heurísticas de texto — si no está declarado con `source="declared"`, no se aplica override

`_PROPELLER_HINT_PARAMS: frozenset = {"propeller_diameter_m", "propeller_diameter_in", "propeller_rpm"}` — detecta si el usuario inició la ruta hélice aunque incompleta. Determina qué reason code se emite (específico vs. genérico). Un único punto de decisión sin lógica duplicada downstream.

`available_total_thrust_n` es `float | None` — puede ser `None` en dominio terrestre con parámetros de transmisión ausentes.

### Simulación

La validación vive en `simulation/simulator.py`.

Clase principal: `FeasibilitySimulator` (renombrada de `FlightSimulator`).
`FlightSimulator = FeasibilitySimulator` como alias de compatibilidad.

En la versión actual:

- compara fuerza disponible frente a requerida
- calcula `safety_margin_ratio`
- calcula `thrust_to_weight_ratio` (alias `force_to_weight_ratio` en schema)
- calcula `per_motor_load_ratio`
- deriva `quality = fail | risky | acceptable | good`
- emite `warnings` deterministas
- cuando `available_total_thrust_n is None` → rama `missing_parameters`: devuelve `SimulationResult` estructurado con `physics_status="missing_parameters"`, `quality="fail"`, warning con el **reason code emitido por el engine** (leído de `tool_results`), sin crash

`SimulationResult.physics_status: Literal["valid", "missing_parameters"]` — siempre presente, valor por defecto `"valid"`. Permite a UX y tests distinguir si la física fue evaluable o no.

`SimulationResult.propeller_status: Literal["valid", "missing_propeller_parameters"]` — campo **independiente** de `physics_status`. Se deriva exclusivamente de `tool_results`: si algún `ToolResult.tool_name == "missing_propeller_parameters"` → `propeller_status="missing_propeller_parameters"`, en cualquier otro caso `"valid"`. No entra en `warnings`. Patrón simétrico a `energy_status`.

`physics_status` fluye a la capa de razonamiento vía `simulation.model_dump()["physics_status"]` en `last_simulation`. `ReasoningLayer._extract_signals` lo convierte en la señal `missing_physics_parameters`, **con exclusión mutua**: si `propeller_status == "missing_propeller_parameters"`, la señal `missing_physics_parameters` se suprime y en su lugar se activa `missing_propeller_parameters`. El usuario recibe el mensaje específico, nunca dos mensajes solapados.

Cuando la señal `missing_propeller_parameters` es `True`:
- `_build_insights`: genera insight específico de hélice (nombrando `propeller_diameter_in` y `propeller_rpm`)
- `_build_tradeoffs`: añade tradeoff con nota sobre modelo Ct≈0.12
- `_build_suggested_actions`: devuelve acción de prioridad 0.99 (`Declarar propeller_diameter_in y propeller_rpm`) **antes** del bloque de física genérica

Cuando la señal `missing_physics_parameters` es `True` (propeller_status no activo):
- `_build_insights`: genera insight nombrando los params ausentes leídos desde `current_parameters`
- `_build_tradeoffs`: añade tradeoff sobre la imposibilidad de evaluar viabilidad
- `_build_suggested_actions`: devuelve acción de prioridad 0.99 (`Declarar <params>`) antes que cualquier otra ruta
- `_build_explanation`: usa rama específica ("El sistema no puede evaluar la viabilidad física…")

La lista de parámetros requeridos se deriva de `core/parameter_requirements.py`: un catálogo declarativo `reason_code → [params]` con labels, hints y keywords. Entradas actuales: `missing_transmission_parameters`, `missing_propulsion_parameters`, `missing_energy_parameters`, `missing_propeller_parameters`. El helper `_get_missing_force_reason(context)` lee el reason code de `simulation.warnings` — fuente única emitida por el engine — y lo usa para lookups del catálogo. Añadir un nuevo dominio de conversión (ej. hidráulico) solo requiere una nueva entrada en el catálogo.

`SimulationAnalysis.available_thrust_n` es `float | None` para acomodar el caso de parámetros ausentes.

Códigos de warning genéricos:

- `"low_force_to_weight_ratio"` (antes `"low_thrust_to_weight_ratio"`)
- `"high_actuator_load"` (antes `"high_motor_load"`)

### Abstracción de magnitudes físicas

`output_magnitude` es la abstracción que permite al sistema operar sobre diferentes dominios
sin conocer sus unidades específicas. Es el contrato entre el mundo declarativo y el físico.

Ejemplos actuales:

| `output_magnitude` | Dominio | Componente |
|---|---|---|
| `"thrust_n"` | aéreo | motor brushless |
| `"torque_nm"` | terrestre | motor de tracción |
| `None` | genérico | hélice, ESC, rueda pasiva |

El resolver utiliza esta clave para:
1. decidir elegibilidad de forma paramétrica (sin hardcodear nombres)
2. extraer el valor correcto de `properties`
3. decidir si puede producir un override de fuerza o solo conteo

Cuando se añada un nuevo dominio, solo hace falta definir un nuevo valor de `output_magnitude`
en la regla correspondiente — sin modificar el resolver.

### Limitaciones actuales del modelo físico

- El motor de cálculo soporta torque → fuerza, pero requiere `wheel_radius_m` + `gear_ratio` declarados explícitamente en `current_parameters`. Sin estos, `available_total_thrust_n` queda `None`.
- Modelo energético parcial: `calculate_autonomy_min(battery_capacity_wh, total_power_w)` calcula autonomía en minutos (`(wh/w)×60`). `energy_status: EnergyStatus` y `autonomy_min: float | None` son campos independientes en `SimulationResult` — no entran en `warnings` para preservar la jerarquía `status_type`. Sin curva de descarga ni modelo de C-rating.
- No existe acoplamiento componente auxiliar ↔ actuador: hélice (aéreo) y transmisión (terrestre) no se modelan todavía como parámetros físicos derivados.

El sistema soporta múltiples magnitudes vía `output_magnitude`. Para aéreo: conversión completa.
Para terrestre: conversión posible con parámetros de transmisión declarados.

### Herramientas de mecánica genérica

Ubicación: `tools/mechanics.py`

Funciones canónicas:

- `calculate_required_force(weight_n, safety_factor)` → `required_force_n`
- `calculate_force_per_actuator(required_force_n, actuator_count)` → `force_per_actuator_required_n`
- `calculate_traction_force_from_torque(torque_nm, wheel_radius_m, gear_ratio)` → `traction_force_n`
  Fórmula: `F = (torque_nm × gear_ratio) / wheel_radius_m`

Aliases semánticos aéreos (sin lógica propia — delegan a las canónicas):

- `calculate_required_thrust` → alias de `calculate_required_force`
- `calculate_thrust_per_motor` → alias de `calculate_force_per_actuator`

### Herramientas de electricidad / energía

Ubicación: `tools/electricity.py`

Funciones:

- `calculate_autonomy_min(battery_capacity_wh, total_power_w)` → `autonomy_min` (minutos)
  Fórmula: `t = (wh / w) × 60`

### Herramientas de aerodinámica

Ubicación: `tools/aerodynamics.py`

Funciones:

- `calculate_thrust_from_propeller(diameter_m, rpm, ct=0.12, air_density=1.225)` → `thrust_n` (N)
  Fórmula: `T = Ct · ρ · n² · D⁴` donde `n = rpm / 60`
  Modelo simplificado — Nivel 1. Coeficiente `Ct` típico para UAV: 0.12.
  El parámetro `ct` puede sobreescribirse vía `propeller_ct` en `parameters`.

Parámetros del proyecto que activan la ruta de inferencia en `calculation_engine`:

| Parámetro              | Tipo    | Descripción                                        |
|------------------------|---------|-----------------------------------------------------|
| `propeller_diameter_m` | float   | Diámetro de hélice en metros (canónico interno)    |
| `propeller_diameter_in`| float   | Diámetro de hélice en pulgadas (alias de entrada, convertido `× 0.0254`) |
| `propeller_rpm`        | float   | RPM del motor                                      |
| `propeller_ct`       | float   | Ct personalizado (opcional, def. 0.12)   |
| `air_density_kg_m3`  | float   | Densidad del aire (opcional, def. 1.225) |

Prioridad de resolución de `per_motor_max_thrust_n` en el motor de cálculo:

1. Declarado directo (`per_motor_max_thrust_n` / `max_force_per_actuator_n`)
2. Torque → tracción (`per_actuator_torque_nm` + conversión)
3. **Inferencia aerodinámica** (`propeller_diameter_m` + `propeller_rpm` → `calculate_thrust_from_propeller`)

El campo `SimulationResult.propeller_thrust_inferred: bool` indica si el empuje fue estimado
desde la hélice. El `ReasoningLayer` lee este campo y emite insight + tradeoff específicos.

### Aliases genéricos en schemas

Ubicación: `schemas/tool_schema.py`

`CalculationBundle` expone propiedades genéricas sobre los campos originales:

```python
@property def actuator_count(self) → int: return self.motors
@property def required_force_n(self) → float: return self.required_thrust_n
@property def available_total_force_n(self) → float: return self.available_total_thrust_n
@property def force_per_actuator_required_n(self) → float: return self.thrust_per_motor_required_n
```

`SimulationResult` expone:

```python
@property def constraints_satisfied(self) → bool: return self.can_fly
@property def force_to_weight_ratio(self) → float: return self.thrust_to_weight_ratio
```

Principio: los campos originales nunca se eliminan; los aliases permiten que código nuevo
use vocabulario neutro sin romper código existente.

### Persistencia

### Mirrored Param Contract

> **Regla estructural activa — no diferible.**

Todo writer que gestione un componente físico tiene la obligación de escribir en **dos lugares simultáneamente**:

| Capa | Dónde | Por qué |
|------|-------|---------|
| Canónica | `design_properties.components[key]` | Fuente única de verdad del componente |
| Bridge físico | `current_parameters[param]` | Mirror para que `calculation_engine` consuma el valor |

Si la capa bridge falta, el engine calcula con datos desactualizados **sin lanzar ningún error** (fallo silencioso).

**Flujo garantizado:**

```
ComponentSpec → writer → current_parameters → calculation_engine
                  └───→ design_properties.components
```

**Params mirrored actuales** (`COMPONENT_MIRRORED_PARAMS` en `system_architecture_catalog.py`):

| Param | Writer | Key en components |
|-------|--------|-------------------|
| `battery_capacity_wh` | `set_battery_component` | `components["battery"]` |
| `motor_power_w` | `set_motor_component` | `components["motors"]` |
| `propeller_diameter_in` | `set_propeller_component` | `components["propellers"]` |

**Checklist para añadir un nuevo mirrored param:**

1. Añadir la clave a `COMPONENT_MIRRORED_PARAMS`
2. Crear (o extender) su writer en `component_writers.py` cumpliendo ambas capas
3. Añadir spec builder `_make_*_spec` en `param_definition_session.py`
4. Añadir rama en el bloque `if blocked:` de `apply_and_recalculate`
5. Añadir test `test_mirrored_param_contract_*` en `test_d4_param_gatekeeper.py` verificando `(1)` y `(2)`

**Enforcement:** `test_d4_param_gatekeeper.py::TestParamGatekeeper` — tres tests nombrados `test_mirrored_param_contract_*` verifican que tras `save_state` tanto `design_properties.components[key]` como `current_parameters[param]` contienen el valor declarado.

---

### Component writers

Ubicación: `core/component_writers.py`

Funciones puras extraídas de `JarvisOrchestrator` para eliminar el import circular `orchestrator → design_explorer → orchestrator` (prerequisito DA2).

Cada función es el único punto de escritura para su componente — recibe `ProjectState` y devuelve un `ProjectState` nuevo sin persistir.

| Función | Escribe en |
|---|---|
| `set_frame_material(state, mass_kg, material)` | `components["frame"]` + `current_parameters["structure_mass_override_kg"]` |
| `set_battery_component(state, spec, capacity_wh)` | `components["battery"]` + `current_parameters["battery_capacity_wh"]` |
| `set_motor_component(state, spec, power_w)` | `components["motors"]` + `current_parameters["motor_power_w"]` — preserva `motor_count` de la declaración anterior si el nuevo spec no lo incluye (Bug 78: doble write de motores no pierde el conteo) |
| `set_propeller_component(state, spec)` | `components["propellers"]` + `current_parameters["propeller_diameter_in"]` (D6 bridge) |
| `set_control_component(state, spec)` | `components[key]` genérico (sin params derivados) |
| `apply_components_delta(state, components_delta)` | Orquesta todos los writers en `_APPLY_ORDER` (DA2) |

**`apply_components_delta(project_state, components_delta) → ProjectState`** (DA2):
- `_APPLY_ORDER = ("frame", "battery", "motors", "propellers")` — orden determinista independiente del dict de entrada
- Para cada clave en `_APPLY_ORDER`: usa el spec del delta si existe; si no, re-aplica el componente existente en `design_properties.components` (normalización de baseline)
- Claves fuera de `_APPLY_ORDER` (flight_controller, sensores…) → `set_control_component`
- Con delta vacío `{}`: re-deriva todos los params desde componentes existentes — normalización de baseline
- Acceso defensivo a `design_properties` vía `getattr` para compatibilidad con `SimpleNamespace` de tests legacy
- Pura: no persiste ni dispara efectos secundarios

La acción real de `iterate` vive en `actions/iterate.py`.

Pipeline:

1. cargar proyecto real
2. construir estado mutable base (`_build_mutable_state` — lee `design_properties.structure` como fuente canónica, fallback a `current_parameters` para retrocompat)
3. aplicar mutación
4. si la iteración es física:
   - `_apply_mutation_to_parameters` — actualiza `current_parameters` (payload, material como etiqueta, overrides numéricos)
   - `_apply_design_property_mutation` — actualiza `design_properties.structure` con `density`/`volume` del mutated_state
   - aplicar overrides efímeros de propulsión desde `component_resolver` (si hay componentes elegibles)
   - recalcular con los parámetros resultantes
   - simular con `autonomy_threshold` desde `parsed_constraints`
5. si la iteración es declarativa: `_apply_design_property_mutation` únicamente y omitir cálculo/simulación
6. persistir estado con `design_properties` actualizado (ambos flujos)
7. generar sugerencias si hay contexto físico disponible
8. persistir artefactos
9. actualizar `state.json`
10. registrar historial

## Design Space Explorer (DSE)

Ubicación: `core/design_explorer.py`

### Visión general

El DSE explora automáticamente un conjunto de configuraciones alternativas a partir del estado actual del proyecto y un objetivo declarado. Es una operación 100% en memoria: no escribe en disco, no llama a `record_action` ni muta `state.json`.

Entradas: `project_state` + `goal_key` → Salida: `ExplorationResult`

### Objetivos soportados

| `goal_key` | Descripción | Score function |
|---|---|---|
| `mejorar_autonomia` | Maximizar autonomía de vuelo | `sim.autonomy_min` |
| `aumentar_payload` | Maximizar carga útil viable | `sim.safety_margin_ratio × calc.payload_kg` |
| `reducir_masa` | Minimizar masa total | `-calc.total_mass_kg` |
| `mejorar_estabilidad` | Maximizar margen de seguridad | `sim.safety_margin_ratio` |

### Grids de exploración

Hay dos tipos de grids, ambos evaluados en `explore()` y mezclados en el ranking final:

**`EXPLORATION_GRIDS`** — variaciones de `current_parameters` expresadas como deltas:
- `{param}_factor` → multiplica el valor actual por el factor
- `{param}_delta` → suma un entero al valor actual (para conteos discretos como `motor_count`)
- `{param}_value` → fija un valor absoluto

**`COMPONENT_VARIATION_RULES`** (G1) — tabla declarativa de variaciones de componentes. Cada regla define `component_key`, `component_type`, `property_name`, `unit` y `values`. `_build_component_candidates_for_goal(goal_key)` genera los `dict[component_key, ComponentSpec]` a partir de esta tabla — sin lógica de dominio en el generador.

Reglas actuales:

| Goal | Componente | Propiedad | Valores |
|---|---|---|---|
| `mejorar_autonomia` | `battery` | `battery_capacity_wh` | 300 / 500 / 800 / 1200 Wh |
| `aumentar_payload` | `motors` | `power_w` | 150 / 200 / 300 / 400 W |
| `reducir_masa` | `frame` | `mass_kg` | 0.280 / 0.350 / 0.450 kg |
| `mejorar_estabilidad` | `frame` | `mass_kg` | 0.500 / 0.700 kg |

Añadir un nuevo componente (rueda, depósito, brazo...) solo requiere una nueva entrada en `COMPONENT_VARIATION_RULES` — no se toca `_build_component_candidates_for_goal` ni `explore()`.

### `_apply_delta(base_params, delta) → dict | None`

Aplica un delta sobre `base_params` y devuelve un nuevo dict. Devuelve `None` si algún parámetro referenciado no existe en `base_params` — el candidato se omite sin error. Filtra `COMPONENT_MIRRORED_PARAMS` antes de aplicar: esos params solo llegan via `components_delta`.

### `_score_candidate(sim, calc, goal_key) → float`

Escalar de scoring. Mayor = mejor para todos los goals. Para `reducir_masa` se niega `total_mass_kg` para que el sort descendente funcione.

### `DesignExplorer.explore(project_state, goal_key) → ExplorationResult`

Flujo (DA2):
1. **Baseline normalizado**: `apply_components_delta(project_state, {})` re-deriva `current_parameters` desde los componentes existentes antes de calcular el baseline. Garantiza comparabilidad entre baseline y candidatos component-driven.
2. **Bucle params** (`EXPLORATION_GRIDS`): aplica `_apply_delta` → `_evaluate(params)` → `ExplorationCandidate(components_delta={})`
3. **Bucle componentes** (`COMPONENT_VARIATION_RULES`): `_build_component_candidates_for_goal(goal_key)` genera los deltas → aplica `apply_components_delta(normalized_state, comp_delta)` → extrae `current_parameters` → `_evaluate(params)` → `ExplorationCandidate(params_delta={})`
4. Candidatos con `_apply_delta = None`, `comp_delta` vacío, o que lanzan excepción se omiten
5. Candidatos `can_fly=True` van a `viable`; todos van a `candidates`
6. `viable.sort(key=score, reverse=True)` → top `MAX_VIABLE = 5`

**Cache**: `_evaluate(params)` usa `frozenset(params.items())` como clave — evita recalcular combinaciones idénticas entre ambos bucles dentro de una misma llamada a `explore()`.

### Helpers de spec y builder genérico

`_build_component_spec(component_key, component_type, property_name, unit, value) → ComponentSpec` — constructor genérico domain-agnostic. Produce specs con `completeness="medium"` y `source="declared"` — elegibles por `apply_components_delta`.

`_battery_spec(wh)`, `_motor_spec(w)`, `_frame_spec(kg)` — wrappers de conveniencia sobre `_build_component_spec`, usados directamente en tests de fixture.

### Schemas

- `ExplorationCandidate` — `params_delta`, `components_delta` (DA2), `generation_metadata` (reservado v2), `calculations`, `simulation`, `score`, `label`, `improvement`
- `ExplorationResult` — `goal_key`, `goal_label`, `baseline_score`, `baseline_calculations`, `baseline_simulation`, `candidates`, `viable`

### Labels

- `_build_label(delta, applied)` — label para candidatos params-driven: `"batería (Wh)=800"`
- `_build_label_components(components_delta)` (DA2) — label para candidatos component-driven: `"battery: battery_capacity_wh=800.0"`

### Intent routing (DSE v1)

`IntentResolver.EXPLORE_PATTERNS` — expresiones regulares que detectan solicitudes de exploración. Evaluadas **antes** de `ITERATE_PATTERNS` para evitar falso routing al wizard de iteración.

`resolve_explore_goal(text) → str | None` — detecta el `goal_key` del texto libre. Devuelve `None` si no se reconoce objetivo; el orquestador cae a `_handle_analyze`.

`_handle_explore` en el orquestador:
1. Carga `project_state` (FileNotFoundError → `_handle_analyze`)
2. Valida `goal_key` en `EXPLORATION_GRIDS` (None o ausente → `_handle_analyze`)
3. Llama `DesignExplorer.explore()`
4. Construye mensaje con tabla de candidatos viables
5. **Persiste `ExplorationResult` en `session.last_exploration_result`** (DSE v1.1)

### Apply (DSE v1.1 / DA2)

Cierra el loop: permite al usuario decir «aplica la mejor» tras una exploración para escribir `viable[0]` en el proyecto.

`IntentResolver.APPLY_PATTERNS` — detectado **antes** que `EXPLORE_PATTERNS` para que «aplica la mejor» no caiga en `explore_design_space`.

`_handle_apply_exploration` en el orquestador (con rama DA2):
1. Lee `session.last_exploration_result` (None → error)
2. Verifica `exploration.viable` no vacío
3. Carga `project_state` (FileNotFoundError → error)
4. `best = exploration.viable[0]` (mayor score)
5. **Rama `best.components_delta` no vacío** (DA2): `apply_components_delta(project_state, best.components_delta)` → `updated_project`; `canonical_params = dict(updated_project.current_parameters)`; `base_state_for_save = updated_project` (preserva componentes actualizados)
6. **Rama params-only** (original): `_apply_delta(base_params, best.params_delta)` → `canonical_params` (None → error + instrucción manual); `base_state_for_save = project_state`
7. `calculation_engine.build(canonical_params)` → `calculations`
8. `simulator.evaluate(calculations, autonomy_threshold)` → `simulation`
9. `workspace_manager.save_iteration_snapshot(...)` — `history/iterations/iter_NNN.json`
10. `state_manager.record_action(...)` sobre `base_state_for_save.model_copy(update={"current_parameters": canonical_params})` + `workspace_manager.save_state()` — `state.json` actualizado
11. `workspace_manager.append_event("dse_apply", ...)` — `history/events.jsonl`
12. `workspace_manager.render_views(...)` — vistas Markdown regeneradas
13. Mensaje con params cambiados + resultados reales; aviso si `best.score <= baseline_score`; `⚠` warning inline si `_check_constraint_violations` detecta que la nueva masa total viola `max_weight_kg` (mismo patrón U5 — informativo, nunca bloquea).

**Garantía DA2:** cuando el candidato es component-driven, `base_state_for_save` ya tiene `design_properties.components` actualizado → se persiste tanto el componente como los params derivados en un único `record_action`.

**Garantías de trazabilidad:** el apply sigue los mismos 5 pasos de persistencia que una iteración física (`save_iteration_snapshot → record_action → save_state → append_event → render_views`). El audit trail queda completo.

**`session.last_exploration_result: Any | None`** — campo en `InteractiveSessionState` (`Any` para evitar ciclo de importación `action_schema → design_explorer → calculation_engine`). Se escribe en `_handle_explore` y se lee en `_handle_apply_exploration`. No se persiste en `state.json` — es temporal de sesión.

## Flujo `calculate`

La acción real vive en `actions/calculate.py`.

Pipeline:

1. resolver proyecto activo
2. cargar `state.json`
3. recalcular usando `current_parameters`
4. guardar snapshot en `history/calculations/calc_NNN.json`
5. registrar evento en `history/events.jsonl`
6. renderizar vistas en `views/`
7. actualizar historial sin crear nueva iteración

## Flujo `simulate`

La acción real vive en `actions/simulate.py`.

Pipeline:

1. resolver proyecto activo
2. reutilizar cálculos persistidos o recalcular si faltan
3. ejecutar simulación
4. generar sugerencias no vinculantes
5. guardar snapshot en `history/simulations/sim_NNN.json`
6. registrar evento en `history/events.jsonl`
7. renderizar vistas en `views/`
8. actualizar historial sin crear nueva iteración

## Motores del sistema

### Mutation engine

Ubicación: `core/mutation_engine.py`

Función:

- convertir intención de alto nivel en cambios de variables base
- convertir definiciones declarativas en parches sobre `design_properties`

No debe:

- calcular física
- simular
- escribir en disco

### Calculation engine

Ubicación: `core/calculation_engine.py`

Función:

- recalcular dependencias técnicas a partir de variables base

### Planner v0

Ubicación: `core/planner.py`

Función:

- generar planes compuestos a nivel de acción
- validar coherencia mínima del plan
- no expandir pipelines internos como `iterate`

Regla de uso:

- acciones simples se ejecutan directamente por el orquestador
- el planner solo se usa para objetivos compuestos

Casos soportados:

- `create_and_simulate`
- `recalculate_and_simulate`
- `iterate_and_validate`

### Historial conversacional

Ubicación: campo `conversation_history` en `RuntimeState` (solo RAM, no persiste).

Función:

- guardar los últimos N intercambios usuario/asistente de la sesión actual
- inyectarlos como mensajes anteriores en el payload del LLM (rutas `analyze` y fallback `unknown`)
- permitir que el LLM resuelva referencias contextuales (`"mi próximo cambio"`, `"el mismo material"`, etc.)

Reglas:

- máximo configurable: `MAX_HISTORY_TURNS = 6` (3 intercambios)
- nunca entra en `mutation_engine`, `calculation_engine` ni `simulator`
- no entra en sesiones interactivas (`ITERATE_INTERACTIVE`, `CREATE_PROJECT_INTERACTIVE`) — usan contexto estructurado propio
- se limpia al cargar un proyecto nuevo desde la CLI

### Memory v0

Ubicación:

- `memory/memory_manager.py`
- `state.json`

Función:

- guardar resoluciones explícitas de conflicto
- guardar preferencias binarias explícitas derivadas de esas resoluciones
- reutilizar esa información solo en mensajes de interacción

No debe:

- decidir por el usuario
- modificar motores
- introducir lógica implícita

### Simulator

Ubicación: `simulation/simulator.py`

Función:

- validar la viabilidad técnica y la calidad básica de la configuración

API: `evaluate(calculations: CalculationBundle, autonomy_threshold: float | None = None) → SimulationResult`

El simulador no parsea strings. Las restricciones llegan como `float | None` (leer desde `project_state.parsed_constraints`). El warning `autonomy_below_restriction` se emite cuando `autonomy_min < autonomy_threshold`.

### Suggestion engine v0

Ubicación: `suggestions/suggestion_engine.py`

Función:

- leer cálculos y simulación ya generados
- proponer opciones posibles de mejora
- no modificar estado
- no ejecutar iteraciones
- no usar LLM

## Acciones actuales

### Implementadas

- `create_project`
- `calculate`
- `simulate`
- `iterate`

## Estado actual del sistema

Implementado:

- workspace persistente
- `state.json`
- `create_project` directo
- `create_project_interactive`
- `calculate`
- `simulate`
- `iterate_interactive`
- ejecución real de `iterate`
- `mutation_engine`
- `calculation_engine`
- `planner` v0
- planner solo para secuencias compuestas
- LLM interface validada
- `FeasibilitySimulator` v1+ con métricas y warnings genéricos (`FlightSimulator` como alias)
- `suggestion_engine` v0 con sugerencias no vinculantes
- `design_properties` tipadas y persistidas en `state.json`
- `memory` v0 mínima en `state.json`
- CLI mínima de terminal para prueba real conectada a Ollama
- historial por iteraciones
- `SemanticState` + `SemanticInterpreter` — interpretación acumulativa slot-driven
- flujo `decide()` en iterate: proceed / confirm / clarify con límite de clarificación
- bienvenida contextual en CLI con selección de proyecto existente
- **arquitectura multi-dominio** — `ComponentRule` + `ComponentRuleRegistry` + Protocols
- dominio aéreo: `domains/aerial.py` — motores brushless, hélices, ESC con extractores regex
- dominio terrestre: `domains/ground.py` — motores de tracción, ruedas pasivas, torque/rpm
- `domains/registry_selector.py` — routing híbrido (vehicle_type + heurística de texto + default aéreo)
- `component_inference.py` refactorizado como dispatcher con registro inyectable
- `component_resolver.py` — `PhysicalOverride` genérico + `_ACTIVE_ACTUATOR_TYPES` frozenset + `reason` field en `force_resolution_detail`
- `calculation_engine.py` — vocabulario dual (`actuator_count|motors`, `max_force_per_actuator_n|per_motor_max_thrust_n`)
- `tools/mechanics.py` — funciones genéricas `calculate_required_force` / `calculate_force_per_actuator`
- aliases genéricos en `schemas/tool_schema.py` (`actuator_count`, `constraints_satisfied`, `force_to_weight_ratio`)
- `component_inference` — inferencia determinista de tipo de componente
- componentes unificados como fuente única de verdad en `design_properties.components`
- `component_resolver` — puente determinista declarativo → físico (overrides efímeros de propulsión)
- `PhysicalOverride.per_actuator_torque_nm` — extracción de torque declarado; `apply_to` lo inyecta en `current_parameters`; engine convierte con `wheel_radius_m` + `gear_ratio`
- `tools/mechanics.py` — `calculate_traction_force_from_torque` — dominio terrestre completo
- `calculation_engine.py` — ruta terrestre: `torque → force`; ruta aerial (prioridad); ruta hélice (tercer nivel, acepta `propeller_diameter_in` alias con conversión `×0.0254`); `_PROPELLER_HINT_PARAMS` frozenset para intent detection; tres ramas de razón mutuamente excluyentes: `missing_propeller_parameters` (aéreo + hint), `missing_propulsion_parameters` (aéreo sin hint), `missing_transmission_parameters` (terrestre)
- `parameter_requirements.py` — catálogo declarativo único para `reason_code → parámetros → labels/hints/keywords` (entradas `missing_transmission_parameters`, `missing_propulsion_parameters`, `missing_energy_parameters`, `missing_propeller_parameters`); `MISSING_FORCE_REASONS` frozenset incluye `missing_propeller_parameters`
- `schemas/tool_schema.py` — `PropellerStatus = Literal["valid", "missing_propeller_parameters"]`; `propeller_status: PropellerStatus = "valid"` en `SimulationResult` (campo independiente, patrón simétrico a `energy_status`)
- `simulation/simulator.py` — `propeller_status` derivado exclusivamente de `tool_results`; no altera `physics_status` ni `warnings`
- `reasoning_layer.py` — señal `missing_propeller_parameters` con exclusión mutua (`missing_physics_parameters` suprimida cuando `missing_propeller_parameters` activa); insight + tradeoff + suggested action (priority 0.99) específicos de hélice; cero hardcoding de dominio downstream
- `phase_layer.py` — `PhaseLayer.infer(signals, simulation)`: 4 fases deterministas (`definition`, `physical_validation`, `optimization`, `complete`); reglas en prioridad estricta; reutiliza `HIGH_MARGIN_THRESHOLD` de `reasoning_layer`
- `build_startup_context()` — snapshot operativo sin LLM; jerarquía 4 niveles; `active_variables` y `suggested_action` con hint; `phase`/`phase_description`/`phase_confidence`; `proactive_question` + `missing_params` cuando blocking
- `OrchestratorMode.DEFINE_MISSING_PARAMETERS` — sesión ligera para recolección de parámetros numéricos + recalculo directo; sin LLM; sin `iterate_interactive`; `param_definition_reason` identifica el origen; `ParamDefinitionSession` usa `parameter_requirements.py` para parseo semántico con fallback posicional
- `IntentResolver` — `project_status` intent; `STATUS_PATTERNS` + `GUIDANCE_PATTERNS` (FN-023 next-step help) antes de `ANALYZE`; consultas de estado/orientación no entran por `analyze`
- **Acquisition Fluency + Continuity (FN-014…023)** — `acquisition_target` / `acquisition_brief` / `project_continuity` / `classify_component`; IDLE Engineering Intent (`is_engineering_intention` → `goal_plan`); session hygiene a IDLE (FN-021). Field notes: `PROJECT_CONTINUITY.md`. Create→BOM y Step D: aún no en este mapa.
- `knowledge/library.py` — capa de biblioteca determinista (no RAG): `ComponentLibrary` carga catálogos JSON de materiales y motores desde `library/`. Lookups exactos (`get_material`, `get_motor`), sugerencia por KV (`find_motors_by_kv`) y por **espacio de diseño** (`find_motors_for_requirements`: empuje/KV/hélice). Cada entrada declara la región que cubre (`design_space`). Sin match → hueco honesto, nunca inventar SKU.
- `tools/mechanics.py` — `calculate_autonomy_min(battery_capacity_wh, total_power_w)` — dominio energético; fórmula `(wh/w)×60`
- `tools/electricity.py` — `calculate_autonomy_min` — movida desde `mechanics.py` a su dominio correcto (energía/electricidad)
- `schemas/tool_schema.py` — `EnergyStatus` type; `energy_status` + `autonomy_min` en `SimulationResult`; `autonomy_min: float | None` en `CalculationBundle`
- `calculation_engine.py` — bloque energético: traza `missing_energy_parameters` cuando faltan params; calcula `autonomy_min` cuando ambos presentes
- `simulation/simulator.py` — `energy_status` derivado del trace; campo independiente (no entra en `warnings`)
- `reasoning_layer.py` — señal `missing_energy_parameters`; insight + tradeoff + suggested action para energía; `_detect_missing_energy_params`; prioridad: `missing_physics_parameters` > `declarative_context` > `missing_energy_parameters`
- `parameter_requirements.py` — metadata de `battery_capacity_wh` y `motor_power_w`; proactive question de energía sin restricción de fase
- `main.py` — `render_startup_context`: warning de batería cuando `missing_energy_parameters` activo
- **FASE_LLM — intérprete semántico de iterate**: `SemanticIntentAdapter` (resolución de variable en 4 pasos: canonical → normalizado → alias → concepto; `AdaptRejection` para derivadas y desconocidas; `_parse_value` sanitiza unidades; `CONFIDENCE_THRESHOLD = 0.75`); `ActionPolicy._validate_iterate_variable` rechaza variables ausentes del registry antes del adapter; `orchestrator._semantic_preseed` routing confidence-based (≥ 0.75 → wizard paso 2, variable derivada → paso 0 + mensaje del registry, demás → paso 0 normal); `llm_client._build_semantic_trace` loguea `{variable, confidence, routing}` por cada evento iterate
- `conversation_history` en `RuntimeState` — `ConversationTurn`, máx 6 turnos; inyectado en `analyze` y fallback LLM; no persiste en disco; se limpia al cargar proyecto nuevo
- `SystemDefinitionSession` — transición de "parámetros sueltos" → "arquitectura estructurada"; lanzado post-`create_project`; catálogos de datos puros (`system_architecture_catalog.py`, `system_dependency_catalog.py`); `DependencyGraph` + `PriorityEngine` DFS topológico; `system_priority: list[str]` persistido en `DesignProperties`; bridge automático `SYSTEM_DEFINITION → DEFINE_MISSING_PARAMETERS`
- **Pipeline hélice activo (Fase 2)**: `PropellerStatus` en `SimulationResult`; conversión `propeller_diameter_in × 0.0254`; `_PROPELLER_HINT_PARAMS` intent detection; exclusión mutua en reasoning; proactive collection en `build_startup_context()`; `MISSING_FORCE_REASONS` ampliado; 27 tests en `test_propeller_pipeline.py`
- **Design Space Explorer (DSE v1)**: `core/design_explorer.py`; `DesignExplorer.explore()`; 4 objetivos (`mejorar_autonomia`, `aumentar_payload`, `reducir_masa`, `mejorar_estabilidad`); `EXPLORATION_GRIDS` con deltas `_factor`/`_delta`/`_value`; scoring por goal; `ExplorationCandidate` + `ExplorationResult` Pydantic; operación 100% en memoria sin mutación de estado; `EXPLORE_PATTERNS` antes que `ITERATE_PATTERNS` en `IntentResolver`; `resolve_explore_goal()` para detección de objetivo en lenguaje natural
- **Design Space Explorer (DSE v1.1)** — apply: `APPLY_PATTERNS` antes que `EXPLORE_PATTERNS`; `session.last_exploration_result: Any | None` en `InteractiveSessionState`; `_handle_apply_exploration()` aplica `viable[0]` con pipeline completo de persistencia (`save_iteration_snapshot → record_action → save_state → append_event → render_views`); aviso si `best.score <= baseline_score`; edge cases cubiertos (sin exploración, viable vacío, sin proyecto, `_apply_delta` None)
- **D6 — propellers physics bridge**: `set_propeller_component()` escribe `propeller_diameter_in` en `current_parameters` desde `spec.properties["diameter_in"]`; key añadida a `COMPONENT_MIRRORED_PARAMS`; 3 tests en `TestPropellersPhysicsBridge` (`test_propulsion_composite_wizard_flow.py`)
- **D4 — mirrored param bridge**: `ParamDefinitionSession.apply_and_recalculate()` intercepta `COMPONENT_MIRRORED_PARAMS` y los enruta a través de los component writers (battery/motor/propeller) en vez de escribirlos directamente — ver **Mirrored Param Contract**; `try_ingest()` ignora mirrored params en `missing_params`; `_apply_delta()` en `design_explorer.py` filtra mirrored params del delta antes de aplicar; 5 tests en `TestParamGatekeeper` (`test_d4_param_gatekeeper.py`) — 3 de ellos nombrados `test_mirrored_param_contract_*` como enforcement del contrato
- **DA2 — components_delta en DSE**: `core/component_writers.py` con 6 writers + `apply_components_delta()` (orden `_APPLY_ORDER`, baseline normalization, defensivo a SimpleNamespace); `ExplorationCandidate.components_delta` + `generation_metadata`; `_build_label_components`; `explore()` con baseline normalizado + cache param-hash + bucle componentes paralelo al bucle params; `_handle_apply_exploration` ramifica en `best.components_delta` → `apply_components_delta` → `base_state_for_save = updated_project`; 11 tests en `test_da2_components_delta.py`
- **G1 — COMPONENT_VARIATION_RULES**: tabla declarativa de variaciones de componentes reemplaza `COMPONENT_GRIDS`; `_build_component_spec` (builder genérico domain-agnostic); `_build_component_candidates_for_goal` (generador sin lógica de dominio); `_battery_spec`/`_motor_spec`/`_frame_spec` como wrappers de conveniencia para tests; `reducir_masa` + `mejorar_estabilidad` añaden variaciones de frame (0.280–0.700 kg); 3 nuevos tests en `TestFrameComponentGrid` en `test_da2_components_delta.py`; 1216 tests passing
- **Fase 4 (energy composite)**: `BLOCK_TYPE["energy"] = "composite"`; `_set_battery_component()` + `_set_motor_component()` como únicos puntos de escritura; `COMPONENT_MIRRORED_PARAMS` frozenset; `_block_progress_status` rama composite AND-strict; `_set_pending_next_block` Phase A/B; `build_startup_context` composite hint; DA-MOTORS-2 documentada
- **Fase 5 (wizard dinámico composite)**: `_set_pending_next_block` rama composite genérica; supresión de `missing_energy_parameters` en Phase A; `_BLOCK_COMPONENT_HINTS["energy"]` Phase A hint
- **Fase 6 (propulsion composite)**: `BLOCK_TYPE["propulsion"] = "composite"` (motors + propellers + params); DA-MOTORS-3 resuelto (`workspace_manager` remap `motors` → `motor_count`); `_set_propeller_component()` + routing en `_handle_component_description`; `_COMPONENT_PROMPTS["propellers"]` + `_BLOCK_COMPONENT_HINTS["propulsion"]`; `motor_count` key canónico en `parameter_requirements.py` con aliases `("motores", "num_motores", "motors")`; `calculation_engine` lee `motor_count` (con fallback `actuator_count`); DA-MOTORS-2 implementada (Opción B: componente compartido)
- **1216 tests passing** (sin regresiones)

Pendiente:

- D7: frases mixtas multi-componente (`"motores + hélices"` en un mensaje)
- más tools de ingeniería
- memoria de patrones de usuario ("palas" → "propellers")

### Deuda técnica documentada (no bloqueante — diferida a v2)

Los siguientes puntos están documentados y acotados. No requieren acción en v1.

**DT-1 — Separación semántica de `apply_components_delta`**
Ubicación: `core/component_writers.py`
La función actualmente cumple dos responsabilidades distintas: (a) aplicar un delta de componentes y (b) normalizar el estado re-derivando params desde componentes existentes cuando el delta es `{}`. Un caller futuro que pase `{}` esperando no-op obtendrá un recálculo completo. Refactor seguro cuando aparezca un segundo caller con expectativa distinta:
```python
normalize_state_from_components(state) -> ProjectState   # solo re-deriva
apply_components_delta(state, delta) -> ProjectState      # solo aplica delta
```

**DT-2 — Cache por hash de params en `_evaluate` (DSE)**
Ubicación: `core/design_explorer.py`, función `_evaluate` dentro de `explore()`
El cache usa `frozenset(params.items())` como clave. Es una aproximación: si dos `ComponentSpec` distintos derivan los mismos `current_parameters` (ej. motor A + hélice X = motor B + hélice Y = 10N de thrust), producirán la misma clave y el segundo candidato reutilizará el resultado del primero sin saberlo. Impacto actual: bajo (grids con valores muy distintos entre sí). Solución futura: incluir identidad de componentes en la clave de cache.

**DT-3 — `COMPONENT_VARIATION_RULES` estáticos (ciegos al estado)**
Ubicación: `core/design_explorer.py`
Las reglas actuales son valores fijos. No dependen del estado del proyecto: un dron de 200g probará baterías de 1200Wh igual que uno de 2kg. Esto hace la exploración sistemática pero no inteligente. El salto a reglas adaptativas requiere heurísticas de dominio o un `ComponentGenerator` que genere valores en función del estado actual.

## Papel del LLM

El LLM está integrado como interfaz validada y pluggable. No ejecuta física, no muta estado, no accede directamente a los motores. Interviene en dos casos.

### Cuándo interviene

**Routing de intent desconocido o ambiguo (`interpret`)**

Cuando `intent_resolver` no puede clasificar el input localmente, lo pasa al LLM. El LLM devuelve JSON estricto (`LLMActionRequest`) que pasa por `response_parser` + `ActionPolicy` + `SemanticIntentAdapter` antes de convertirse en acción.

Cuando el intent es `"ambiguous"` (keywords de dominio como `"dron"`, `"robot"`): si **no hay proyecto activo** → wizard `create_project_interactive` sin LLM; si **hay proyecto activo** → `analyze` con contexto del proyecto.

**Análisis y preguntas abiertas (`analyze`)**

Cuando el input parece una pregunta causal (`"qué pasa si"`, `"explica"`, `"influye"`...), `intent_resolver` lo clasifica como `"analyze"` y el LLM produce texto natural con el contexto del proyecto como base. No se ejecuta ningún motor.

### Routing semántico para `iterate` (FASE_LLM)

Cuando el LLM propone `action=iterate`, el output pasa por tres capas en secuencia antes de abrir el wizard:

```text
ActionPolicy._validate_iterate_variable
    → rechaza variables ausentes del registry (hallucinations) antes del adapter

SemanticIntentAdapter.adapt()
    → None: variable ausente → wizard paso 0
    → AdaptRejection("derived_variable"): variable no settable → wizard paso 0 + mensaje del registry
    → AdaptRejection("unknown_variable"): no llegará aquí (ya rechazado por ActionPolicy)
    → SemanticInterpretation(is_high_confidence=False): confidence < 0.75 → wizard paso 0
    → SemanticInterpretation(is_high_confidence=True): confidence ≥ 0.75 → wizard preseed paso 2

Reglas adicionales del adapter (calibración 2026-08-05):
- Si `raw_user_input` no contiene un token de anclaje de la variable propuesta (clave, alias o concept_alias, longitud ≥ 4), el confidence se cap a `< 0.75` aunque el LLM diga `1.0` (ej. `"más chicha"` → `battery_capacity_wh`).
- Si el usuario no escribió ningún número, el `valor` inventado por el LLM se descarta (`None`).

orchestrator._semantic_preseed()
    → traduce el resultado del adapter a parámetros de seed para iterate_interactive_session.start()
```

El wizard determinista (`iterate_interactive_session`) se abre siempre: la diferencia es si empieza en paso 0 o en paso 2 con los campos pre-rellenados. Los motores nunca reciben output LLM sin pasar por la validación del wizard.

**Logging de cada evento LLM (`interpret`):**

```json
{
  "prompt_version": "...",
  "user_input": "...",
  "llm_raw_output": "...",
  "parsed_output": {...},
  "semantic_trace": {"variable": "...", "confidence": 0.88, "routing": "preseed_step2"},
  "error": null
}
```

`routing` values: `preseed_step2 | fallback_wizard | rejected_derived | rejected_unknown | n/a`

### Cuándo NO interviene

- Selección inicial de proyecto por número (`1`, `2`...) — `main.py` lee `state.json` directamente
- Proyecto seleccionado → startup display — `build_startup_context()` es determinista
- **Consulta de estado / Continuity** (`"estado del proyecto"`, `"resumen"`, `"qué falta"`, `"siguiente paso"`, `"ayúdame con el siguiente paso"`…) — `project_status` → `build_startup_context()` sin LLM
- **Acquisition Target / Brief** (declarar bloque∪componente, help-define, nav-back) — orquestador + `acquisition_*` sin LLM
- **Engineering Intent** (intención bare sin valor) — `goal_plan` determinista (FN-022); no abre iterate
- Sesión interactiva activa — session handler (salvo soft-interrupt status/analyze)
- Intent claro (`calcular`, `simular`, iterate **con valor**, explore/apply…) — `ActionRequest` / DSE local
- Todos los pasos dentro de `create_project_interactive` e `iterate_interactive`
- Extracción de slots en `semantic_interpreter` — determinista por reglas

### Restricciones permanentes

- No calcula física.
- No simula.
- No persiste estado.
- No controla el flujo de sesión.
- El registry (`PARAMETER_REQUIREMENTS`) es el único árbitro de variables modificables.

La frontera LLM incluye: safe fallback para salidas inválidas, logging estructurado en `jarvis/runtime/llm_logs/`, versionado de prompt.



## SemanticState y SemanticInterpreter

### Propósito

Reemplazar el parsing rígido por keyword-rules con un estado acumulativo que
construye significado progresivamente a lo largo de la sesión.

Antes: cada input debía ser un comando válido completo.
Ahora: cada input aporta información parcial que se acumula.

### SemanticState

Ubicación: `schemas/semantic_schema.py`

**Runtime-only. Nunca se persiste en `state.json`.**

Campos clave:

```python
slots: dict[str, SlotValue]    # operation, variable, value, objective, restrictions
missing_slots: list[str]       # slots requeridos aún no resueltos
alternatives: list[str]        # interpretaciones posibles cuando hay ambigüedad
history: list[str]             # todos los inputs de la sesión
clarification_round: int       # rondas de clarificación ya usadas
forced: bool                   # True si se avanzó forzado por MAX_CLARIFICATION_ROUNDS
```

Cada `SlotValue` tiene:
- `value`: el valor extraído (o `None`)
- `confidence`: 0.0–1.0
- `source`: `"inferred"` | `"explicit"` | `"confirmed"`

Los slots con `source="confirmed"` nunca se sobreescriben.

### SemanticInterpreter

Ubicación: `core/semantic_interpreter.py`

Tres funciones públicas:

| Función | Entrada | Salida |
|---|---|---|
| `update(state, input)` | estado actual + nuevo input | estado enriquecido (nunca menos completo) |
| `decide(state)` | estado actual | `"proceed"` \| `"confirm"` \| `"clarify"` |
| `to_draft_patch(state)` | estado actual | dict compatible con `IterationDraft` |

Política de confianza en `decide()`:

| Condición | Decisión |
|---|---|
| todos los slots requeridos con confianza ≥ 0.75 | `proceed` |
| todos presentes, alguno entre 0.4–0.75 | `confirm` |
| algún slot ausente o confianza < 0.4 | `clarify` |
| `clarification_round >= 2` (forzado) | `proceed` |

`to_draft_patch` garantiza que `operation` siempre es `IterationOperation` enum o `None`.
Nunca emite un raw string — esto elimina el crash histórico de Pydantic.

### Integración en la sesión

En `iterate_interactive_session.answer()`:

1. `_seed_semantic_from_draft()` — añade campos confirmados del draft como slots `confirmed`
2. `sem.update()` — enriquece con el nuevo input
3. Routing por step (conflicto, definición, etc.)
4. En step 2: `sem.decide()` determina si proceder, confirmar o clarificar
5. `_operation_from_semantic()` — extrae operation del estado semántico, nunca raw string

## Principios de diseño

- Determinismo: mismo input, misma salida.
- Separación total de capas.
- Trazabilidad: nada importante se pierde.
- Escalabilidad: nuevas estrategias y dominios deben poder añadirse sin romper el núcleo.

## Uso conceptual

### Crear proyecto

```python
{
  "action": "create_project",
  "parameters": {}
}
```

o:

```python
{
  "action": "create_project",
  "parameters": {
    "vehicle_type": "dron",
    "objective": "dron que levante 2kg",
    "payload_kg": 2.0,
    "restrictions": "sin restricciones adicionales",
    "detail_level": "conceptual",
    "motors": 4,
    "per_motor_max_thrust_n": 15.0,
    "structure_mass_factor": 0.6,
    "safety_factor": 1.2
  }
}
```

### Iterar proyecto

```python
{
  "action": "iterate",
  "parameters": {
    "objetivo": "peso",
    "operacion": "reducir"
  }
}
```

Después el sistema abre el flujo guiado, pide confirmación y ejecuta la iteración real.

### Recalcular proyecto

```python
{
  "action": "calculate",
  "parameters": {
    "project_id": "abc123"
  }
}
```

### Simular proyecto

```python
{
  "action": "simulate",
  "parameters": {
    "project_id": "abc123"
  }
}
```

### Generar plan

```python
plan = orchestrator.build_plan("recalculate_and_simulate", {"project_id": "abc123"})
```
