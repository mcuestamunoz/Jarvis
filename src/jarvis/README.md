# Jarvis

Jarvis es un motor de ingeniería asistida por IA orientado a flujos controlados, trazables y deterministas.

No está pensado como chatbot libre. Está pensado como sistema por capas:

1. El usuario decide.
2. El LLM interpreta.
3. El orquestador controla.
4. Las acciones ejecutan.
5. Los motores deterministas mutan, calculan y validan.
6. El workspace persiste todo.

## Estado actual

Jarvis ya permite:

- Crear proyectos de ingeniería con flujo guiado o directo
- Iterar diseños de forma controlada (iteraciones físicas y declarativas)
- Calcular y simular configuraciones físicas con trazabilidad completa
- Inferir componentes (motores, hélices, actuadores de tracción) y conectarlos al modelo físico
- Conectar componentes declarados al motor físico: `propeller_diameter_in` se deriva automáticamente del spec de hélice (D6)
- Proteger parámetros canónicos de componentes contra escritura directa del wizard (D4 — gatekeeper `COMPONENT_MIRRORED_PARAMS`)
- Solicitar proactivamente parámetros de hélice (`propeller_diameter_in`, `propeller_rpm`) en proyectos aéreos sin empuje declarado
- Mantener historial de iteraciones y memoria mínima de decisiones en disco
- Operar en modo multi-dominio (aéreo y terrestre) con un núcleo desacoplado
- Interpretar intención libre en lenguaje natural y enrutar al wizard correcto con preselección semántica
- Humanizar warnings del simulador (`low_margin`, `high_actuator_load`...) con `WARNING_MESSAGES` en español
- Detectar objetivos de diseño (`aumentar payload`, `mejorar autonomía`...) y responder con plan estratégico determinista priorizado por estado + análisis LLM contextual (goal planner híbrido)
- Guardar preguntas informativas dentro de `ITERATE_INTERACTIVE` del wizard de iteración mediante `classify_input_intent`
- Explorar automáticamente el espacio de diseño para un objetivo dado (`mejorar_autonomia`, `aumentar_payload`, `reducir_masa`, `mejorar_estabilidad`) sin mutar estado, evaluando tanto variaciones de parámetros como variaciones de componentes (DSE v1 + DA2)
- Aplicar el mejor candidato de la última exploración con trazabilidad completa, preservando componentes y parámetros derivados (DSE v1.1 + DA2)
Detalles técnicos internos del sistema en [ARCHITECTURE.md](ARCHITECTURE.md).

## Flujos disponibles

### `explore_design_space` (DSE v1)

Opera como búsqueda automática de configuraciones optimizadas. Solo lectura.

Entrada: texto libre con objetivo (`"optimiza para autonomía"`, `"encuentra la mejor configuración"`).

Resultado:

- detecta el objetivo (`mejorar_autonomia`, `aumentar_payload`, `reducir_masa`, `mejorar_estabilidad`)
- evalúa todas las variaciones del grid para ese objetivo
- calcula y simula cada candidato en memoria
- devuelve tabla de candidatos viables ordenados por score
- no muta `state.json`
- persiste `ExplorationResult` en sesión para el paso de apply

### `apply_exploration_result` (DSE v1.1 + DA2)

Aplica el mejor candidato de la última exploración al proyecto activo.

Entrada: `"aplica la mejor"`, `"aplica"`, `"usa esta configuración"`...

Resultado:

- lee `viable[0]` de la última exploración en sesión
- si el candidato es **component-driven** (DA2): aplica `apply_components_delta` → actualiza componentes + params derivados en un único paso atómico
- si el candidato es **params-only**: aplica delta de parámetros directamente
- recalcula y simula con los nuevos parámetros
- persiste con trazabilidad completa: `history/iterations/iter_NNN.json`, `history/events.jsonl`, vistas Markdown
- actualiza `state.json` (nueva iteración)
- avisa si el candidato no mejora la línea base

### `analyze`

Opera como consulta técnica de solo lectura sobre el estado actual.

Resultado:

- clasifica la intención como `analyze` en modo `idle`
- construye contexto estructurado mínimo (`objective`, `current_design`, `material`, `last_simulation`)
- responde en lenguaje natural usando LLM
- no muta `state.json`
- no ejecuta `mutation_engine`, `calculation_engine` ni `simulator`

### `create_project`

Puede ejecutarse:

- directamente con parámetros completos
- o en modo guiado paso a paso

Resultado:

- crea el workspace
- calcula
- simula
- guarda artefactos
- actualiza `state.json`
- devuelve sugerencias no vinculantes a partir de la simulación

### `iterate`

Funciona como flujo guiado sobre un proyecto existente.

Resultado:

- resuelve el proyecto activo
- recoge intención de iteración
- si la iteración es física: estima impacto, muta, aplica overrides de propulsión desde `component_resolver` si hay componentes elegibles, recalcula y simula
- si la iteración es declarativa (`define`): actualiza propiedades del diseño sin recalcular física
- persiste nueva iteración
- actualiza `state.json`
- devuelve sugerencias no vinculantes a partir de la simulación

**Escape del wizard de iteración:** en cualquier paso del flujo guiado, el usuario puede escribir `cancelar`, `cancel`, `salir` o `abortar` para abandonar la sesión sin aplicar cambios. El sistema limpia el modo `ITERATE_INTERACTIVE` y confirma la cancelación con un mensaje. El mismo escape está disponible en `DEFINE_MISSING_PARAMETERS`.

### `calculate`

Opera sobre un proyecto persistido.

Resultado:

- carga `state.json`
- recalcula usando `current_parameters`
- guarda resultado en `history/calculations/calc_NNN.json`
- regenera `views/estado_actual.md`
- actualiza historial sin crear iteración nueva

### `simulate`

Opera sobre un proyecto persistido.

Resultado:

- reutiliza cálculos persistidos o recalcula si faltan
- ejecuta simulación
- evalúa `safety_margin_ratio`, `thrust_to_weight_ratio` y `quality`
- guarda resultado en `history/simulations/sim_NNN.json`
- regenera `views/` (estado_actual + reasoning)
- actualiza historial sin crear iteración nueva
- devuelve sugerencias no vinculantes a partir de la simulación

## Estructura principal

- `core/`
  Núcleo del sistema, sesiones interactivas y motores.
- `core/component_writers.py`
  Funciones puras de escritura de componentes. Único punto de escritura por componente (frame, battery, motors, propellers, control). Incluye `apply_components_delta` — orquestador determinista de writers para DA2.
- `llm/`
  Interfaz LLM, prompt, policy y parser.
- `actions/`
  Flujos de alto nivel.
- `schemas/`
  Contratos de datos.
- `simulation/`
  Validación técnica.
- `workspace/`
  Persistencia y estructura en disco. `workspace_manager.py` gestiona state + history + events + views. `render_views.py` genera las vistas derivadas desde `state.json`. `file_writer.py` provee I/O atómico incluyendo `append_jsonl` para el log de eventos.

## Rutas por defecto

- proyectos: `Ingenieria/06_Proyectos/`
- logs LLM: `jarvis/runtime/llm_logs/`

## Ejemplo rápido

```
Usuario: quiero un dron que levante 2kg

Jarvis: [crea proyecto]
        - calcula configuración inicial (4 motores, 15N/motor)
        - simula: quality=acceptable, safety_margin=0.2
        - sugiere: aumentar empuje por motor para mejorar margen

Usuario: reduce el peso

Jarvis: [abre flujo de iteración]
        ¿Qué variable quieres reducir?

Usuario: estructura, usando fibra de carbono

Jarvis: Cambio: estructura → fibra de carbono
        Impacto estimado: -18% masa estructural
        ¿Confirmas?

Usuario: sí

Jarvis: [muta] [recalcula] [simula]
        Nueva calidad: good
        Guarda iteración 002
```

## Quickstart reproducible

Ejecuta estos pasos exactamente para levantar Jarvis desde cero:

```bash
cd /Users/marccuestamunoz/Desktop/Ingenieria/Ingenieria

# 1) Crear entorno
python3 -m venv .venv

# 2) Activar entorno
source .venv/bin/activate

# 3) Instalar dependencias del proyecto Jarvis
python -m pip install -r jarvis/requirements.txt

# 4) Ejecutar tests
python -m pytest jarvis/tests -q

# 5) Lanzar CLI
python -m jarvis.main --chat
```

Si usas Ollama local, asegúrate de que el servidor esté activo y el modelo configurado exista.

## Entrada -> ruta -> efecto en estado

Tabla operativa del enrutado actual en modo `idle`:

| Entrada del usuario | Ruta interna | Efecto en `state.json` |
|---|---|---|
| Pregunta informativa en modo ITERATE_INTERACTIVE (ej: `cuáles son los warnings`) | `classify_input_intent="information"` → `_handle_analyze` | No muta estado |
| Pregunta causal (ej: `como influye el material`) | `intent=analyze` -> `orchestrator._handle_analyze` | No muta estado |
| Estado del proyecto (ej: `qué falta`, `resumen`) | `intent=project_status` -> `build_startup_context()` | No muta estado |
| Entrada ambigua (ej: `dron`) | `intent=ambiguous` -> `create_project_interactive` | No muta hasta confirmacion |
| Accion fuerte (ej: `reduce peso`) | `intent=iterate` -> flujo interactivo de iterate | Muta solo tras confirmacion |
| Accion fuerte + LLM (ej: `quiero más autonomía`) | LLM -> `ActionPolicy` -> `SemanticIntentAdapter` -> wizard preseed paso 2 (si confidence ≥ 0.75) | Muta solo tras confirmacion en wizard |
| Accion fuerte (ej: `calcula`) | `intent=calculate` -> `actions/calculate.py` | Actualiza historial y resultados |
| Accion fuerte (ej: `simula`) | `intent=simulate` -> `actions/simulate.py` | Actualiza historial y resultados || Exploración (ej: `optimiza para autonomía`) | `intent=explore_design_space` -> `_handle_explore` -> `DesignExplorer` | No muta estado |
| Aplicar explorac. (ej: `aplica la mejor`) | `intent=apply_exploration_result` -> `_handle_apply_exploration` | Muta estado, nueva iteración || Unknown (ej: `haz algo util con esto`) | fallback LLM -> parser/policy -> accion | Depende de la accion resultante |

Regla clave: accion fuerte tiene prioridad sobre `analyze` en prompts mixtos (`calcula como influye...`).

## Errores comunes

1. Ejecutar tests con `python archivo_test.py` en vez de usar `pytest`.
Ejecuta siempre:

```bash
cd /Users/marccuestamunoz/Desktop/Ingenieria/Ingenieria
.venv/bin/python -m pytest jarvis/tests/test_intent_resolver.py -q
```

2. Mezclar entornos virtuales de `Ingenieria/.venv` y `Ingenieria/Ingenieria/.venv`.
Usa un solo entorno para Jarvis: `Ingenieria/Ingenieria/.venv`.

3. Error `ModuleNotFoundError: jarvis` al ejecutar desde ruta incorrecta.
Ejecuta desde la raiz del proyecto interno: `Ingenieria/Ingenieria`.

4. Error de dependencias faltantes (ej: `pydantic`).
Reinstala dependencias en el `.venv` activo:

```bash
python -m pip install -r jarvis/requirements.txt
```

## Glosario minimo

- `ActionRequest`: solicitud ejecutable para el orquestador (`action`, `parameters`, `raw_user_input`).
- `RuntimeState`: estado temporal en memoria de la sesion interactiva.
- `ProjectState`: estado persistente del proyecto en `state.json`.
- `IterationDraft`: borrador de iteracion durante flujo guiado antes de confirmar.
- `design_properties`: propiedades declarativas del diseno (no fisica recalculada por defecto).
- `analyze`: consulta de solo lectura sin mutacion de estado ni ejecucion de motores.
- `ambiguous`: entrada insuficiente para accion directa; se redirige a flujo guiado.
- `unknown`: entrada no clasificada localmente; se usa fallback LLM.

## Uso conceptual

CLI mínima:

```bash
python -m jarvis.main --chat
```

Configuración actual de chat:

- runtime: Ollama local
- modelo por defecto: `qwen2.5:14b`
- endpoint por defecto: `http://localhost:11434/api/chat`
- formato: `json` para acciones estructuradas, texto natural para `analyze`
- stream: `false`
- variables opcionales:
  - `JARVIS_OLLAMA_BASE_URL`
  - `JARVIS_OLLAMA_CHAT_PATH`
  - `JARVIS_OLLAMA_MODEL`
  - `JARVIS_OLLAMA_FORMAT`
  - `JARVIS_OLLAMA_STREAM`
  - `JARVIS_OLLAMA_TEMPERATURE`
  - `JARVIS_OLLAMA_TIMEOUT_SECONDS`

Crear proyecto:

```python
{
  "action": "create_project",
  "parameters": {}
}
```

Iterar diseño:

```python
{
  "action": "iterate",
  "parameters": {
    "objetivo": "peso",
    "operacion": "reducir"
  }
}
```

Planificar una secuencia:

```python
plan = orchestrator.build_plan("recalculate_and_simulate", {"project_id": "abc123"})
```

Regla de uso:

- acciones simples como `create_project`, `calculate`, `simulate` e `iterate` se ejecutan directamente con `handle(...)`
- el planner se reserva para objetivos compuestos como `create_and_simulate` o `recalculate_and_simulate`

---

## Guía de conversación CLI

Jarvis no es un chatbot libre. Cada frase activa una ruta interna determinista.
Esta sección agrupa todos los patrones reconocidos para que puedas hablar con fluidez.

> **Nota sobre diacríticos:** Jarvis normaliza el texto antes de procesarlo. Puedes escribir con o sin tildes — `autonomía` y `autonomia` son equivalentes.

---

### Crear un proyecto

| Lo que escribes | Lo que activa |
|---|---|
| `quiero diseñar un dron` | Flujo guiado de creación |
| `quiero crear un robot` | Flujo guiado de creación |
| `necesito hacer un drone` | Flujo guiado de creación |
| `crear proyecto` / `nuevo proyecto` | Flujo guiado de creación |
| `dron` / `drone` / `robot` | Entrada ambigua → pregunta de confirmación |

---

### Orientación y estado del proyecto

Usa estas frases en cualquier momento para saber dónde estás o qué hacer a continuación.

| Lo que escribes | Lo que activa |
|---|---|
| `estado del proyecto` / `estado actual` | Resumen del proyecto activo |
| `resumen` / `resumen del proyecto` | Resumen del proyecto activo |
| `qué falta` / `qué me falta` / `qué nos falta` | Campos o bloques pendientes |
| `siguiente paso` / `qué hago` / `cómo sigo` | Orientación sobre el paso siguiente |
| `qué puedo hacer` / `qué debo hacer` | Opciones disponibles en este punto |
| `por dónde empiezo` / `cómo continúo` | Orientación de inicio o reanudación |
| `guíame` / `guíame hasta completar` | Asistencia paso a paso |
| `ayúdame a completar` | Asistencia para terminar el proyecto |
| `cómo completo el proyecto` / `cómo termino el proyecto` | Pasos para cerrar el flujo |

**Navegación entre bloques** (dentro del wizard de creación o iteración):

| Lo que escribes | Efecto |
|---|---|
| `sigamos` / `sigamos con el siguiente` | Avanzar al siguiente bloque |
| `vamos con el siguiente` / `vamos con siguiente bloque` | Avanzar al siguiente bloque |
| `continúa` / `continuamos` | Avanzar al siguiente bloque |

---

### Preguntas y análisis

Usa estas frases para consultar el estado actual sin modificar nada.

| Lo que escribes | Ejemplo completo |
|---|---|
| `analiza` / `analizar` / `análisis` | `analiza el diseño actual` |
| `evalúa` / `revisa` / `informe` | `revisa los resultados de simulación` |
| `oriéntame` / `dame opciones` | `oriéntame sobre cómo mejorar` |
| `qué opciones` / `qué debería` | `qué debería cambiar primero` |
| `cómo` + tema | `cómo influye el material en el peso` |
| `por qué` + tema | `por qué el margen es bajo` |
| `explica` / `explícame` + tema | `explícame el warning de thrust` |
| `cuál es mejor` / `diferencia entre` | `cuál es mejor: 4 o 6 motores` |

> Estas frases no mutan `state.json`.

---

### Calcular y simular

| Lo que escribes | Lo que activa |
|---|---|
| `calcula` / `calcular` | Recálculo con parámetros actuales |
| `recalcula` / `recalcular` | Ídem, forzando nuevo cálculo |
| `simula` / `simular` | Simulación física del diseño actual |
| `vuela` / `volar` | Simulación |
| `valida` / `validar` | Simulación |
| `comprueba` / `comprobar` | Simulación |

---

### Iterar el diseño

Usa estos verbos para modificar parámetros. Jarvis abre el wizard de iteración, pide confirmación y solo muta el estado si confirmas.

**Verbos que activan el wizard de iteración:**

`reduce` · `reducir` · `mejora` · `mejorar` · `optimiza` · `optimizar`  
`aumenta` · `aumentar` · `incrementa` · `incrementar` · `sube` · `subir`  
`cambia` · `cambiar` · `modifica` · `modificar` · `define` · `definir`  
`establece` · `establecer` · `usar` · `seleccionar`  
`completar` · `especificar` · `enriquecer` · `itera` · `iterar`

**Ejemplos:**

```
reduce el peso
mejora el margen de seguridad
cambia el material a fibra de carbono
aumenta la capacidad de batería
define estructura como aluminio 6061
```

**Definir parámetros específicos** (sin valor numérico — abre configurador):

```
definir batería
configurar hélice
parámetros de batería
parámetros de motor
```

> ⚠️ Si incluyes un valor numérico en la frase (`definir torque a 50 Nm`), Jarvis lo interpreta como iteración directa, no como configuración de parámetros.

**Salir del wizard sin guardar cambios:**

```
cancelar   cancel   salir   abortar
```

---

### Explorar el espacio de diseño

Jarvis evalúa todas las combinaciones posibles para un objetivo dado sin modificar el proyecto.

**Objetivos reconocidos:**

| Objetivo | Frases de ejemplo |
|---|---|
| Mejorar autonomía | `optimiza para autonomía`, `mejora la autonomía`, `maximiza la autonomía del dron`, `mejorar la eficiencia` |
| Aumentar carga útil | `optimiza para payload`, `optimiza para carga útil`, `carga útil`, `levantar más` |
| Reducir masa | `optimiza para masa`, `minimiza la masa`, `reducir el peso`, `aligerar`, `bajar peso` |
| Mejorar estabilidad | `mejora la estabilidad`, `maximiza el margen de seguridad`, `más estable`, `vuelo estable` |

**Patrones de exploración libre:**

```
optimiza la mejor configuración
busca la mejor opción
explora el espacio de diseño
encuentra la mejor configuración
cuál es la mejor opción
prueba todas las configuraciones
```

> La exploración no muta `state.json`. Guarda los resultados en sesión para el paso de aplicar.

---

### Aplicar el resultado de una exploración

Después de explorar, usa una de estas frases para aplicar el mejor candidato encontrado:

```
aplica
aplica la mejor
aplica la óptima
aplica el resultado
aplica la configuración
usa la mejor
usa esta configuración
quédate con esa
quédate con la mejor
guarda la configuración
```

---

### Descartar una sugerencia

Si Jarvis ofrece una sugerencia y no es relevante para tu caso:

```
no aplica
no quiero
no me interesa
no es relevante
ignora
descarta
siguiente sugerencia
omite eso
salta la sugerencia
eso no aplica
no es mi caso
```

---

### Resumen de prioridades de enrutado

Cuando una frase puede encajar en más de una categoría, Jarvis aplica este orden de prioridad (de mayor a menor):

1. Frases de orientación / navegación (`guíame`, `sigamos`, `continúa`)
2. Análisis explícito (`analiza`, `evalúa`, `revisa`)
3. Cálculo (`calcula`, `recalcula`)
4. Simulación (`simula`, `vuela`, `valida`)
5. Definir parámetros sin valor numérico (`definir batería`)
6. Descartar sugerencia (`no aplica`, `ignora`)
7. Aplicar exploración (`aplica la mejor`)
8. **Exploración de diseño** (`optimiza para autonomía`) ← antes de iterate
9. **Iteración** (`reduce`, `mejora`, `cambia`)
10. Crear proyecto (`quiero diseñar`)
11. Estado del proyecto (`estado`, `resumen`, `qué falta`)
12. Pregunta causal (`cómo`, `por qué`, `explica`)
13. Entrada ambigua → flujo guiado
14. Fallback LLM
