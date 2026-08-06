# FASE_LLM — Capa semántica del LLM

## Principio de diseño

El LLM actúa exclusivamente como **intérprete de lenguaje natural**. No calcula. No muta estado. No decide física. No reemplaza validaciones.

```text
Usuario (lenguaje libre)
↓
LLM — interpreta intención → JSON estructurado
↓
ActionPolicy — valida contra reglas de runtime
↓
SemanticIntentAdapter — valida variable contra PARAMETER_REQUIREMENTS
↓
Orquestador — routing por confidence → preseed o wizard normal
↓
iterate_interactive_session — wizard determinista
↓
mutation_engine / calculation_engine / simulator — ejecución física
```

El LLM nunca accede directamente a los motores. Todo pasa por las capas de validación.

---

## Dos modos de operación del LLM

### 1. Modo `interpret` — acción estructurada

Entrada: texto libre del usuario.
Salida: JSON estructurado validado contra `LLMActionRequest`.

Usado para: `create_project`, `iterate`, `calculate`, `simulate`, y cualquier entrada ambigua que el `intent_resolver` no clasifica localmente.

```json
{
  "action": "iterate",
  "project_id": null,
  "parameters": {
    "operacion": "increase",
    "variable": "battery_capacity_wh",
    "valor": 900,
    "confidence": 0.88
  },
  "mode": null,
  "raw_user_input": "quiero más autonomía"
}
```

### 2. Modo `analyze` — respuesta en texto natural

Entrada: pregunta técnica + contexto estructurado del proyecto.
Salida: texto natural en español.

Usado para: preguntas causales, comparaciones, estimaciones cualitativas.
El LLM recibe el razonamiento determinista como base; no puede contradecirlo.

---

## Pipeline `interpret` — detalle interno

### 1. `PromptBuilder`

Construye los mensajes `[system, ...history, user]` para el LLM.

**System prompt** incluye:
- Schema JSON obligatorio con todos los campos.
- Action Space: lista completa de variables modificables, generada automáticamente desde `PARAMETER_REQUIREMENTS` vía `build_action_space()`.
- Instrucciones de output para `iterate`: operación, variable canónica, valor opcional, confidence.
- Estado de sesión actual: `mode` y `step`.

**Operaciones válidas para iterate:** `increase | reduce | define | improve | optimize`

El Action Space se construye una vez al importar (`_ACTION_SPACE`), no en cada llamada. No hay lógica de dominio en el prompt — solo el vocabulario del registry.

### 2. `JarvisLLMInterface.interpret()`

1. Llama a `PromptBuilder.build_messages()`.
2. Llama a `OllamaClient.complete(messages, json_mode=True)`.
3. Parsea el JSON con `LLMResponseParser.parse()` (Pydantic strict).
4. Valida con `LLMResponseParser.validate_for_runtime()` → `ActionPolicy`.
5. Convierte a dict con `to_action_request()`.
6. Construye `semantic_trace` via `_build_semantic_trace()`.
7. Loguea el evento completo en `runtime/llm_logs/`.
8. Si cualquier paso lanza excepción → safe fallback: `{"action": "simulate", "parameters": {"error": "invalid_llm_output"}}`.

### 3. `ActionPolicy`

Valida reglas de runtime antes de que el output llegue al orquestador:

| Regla | Descripción |
|---|---|
| Acción permitida | Solo `create_project`, `iterate`, `calculate`, `simulate` |
| Sesión activa | Si hay sesión activa, la acción debe pertenecer al modo activo |
| Modo interactivo | Dentro de sesión activa, la acción requiere `mode=interactive` |
| Variable en registry | Cuando `action=iterate`, `parameters.variable` debe existir en `PARAMETER_REQUIREMENTS` — rechaza hallucinations antes del adapter |

Las variables **derivadas** pasan la policy: su rechazo corresponde al `SemanticIntentAdapter`, que genera un mensaje explicativo de redirección más rico.

### 4. `SemanticIntentAdapter`

Única puerta entre el output LLM y el wizard de iterate.

**Contrato de retorno:**

| Resultado | Condición | Acción del orquestador |
|---|---|---|
| `None` | `action != "iterate"` o `variable` ausente | No hace routing semántico |
| `AdaptRejection(reason="unknown_variable")` | Variable no encontrada en registry | Wizard desde paso 0, sin mensaje adicional |
| `AdaptRejection(reason="derived_variable")` | Variable existe pero `is_derived=True` | Wizard desde paso 0, muestra `redirect_message` (del registry) |
| `SemanticInterpretation(is_high_confidence=False)` | `confidence < 0.75` | Wizard desde paso 0 |
| `SemanticInterpretation(is_high_confidence=True)` | `confidence >= 0.75` | Wizard preseed en paso 2 |

**Resolución de variable en 4 pasos (más específico primero):**

1. Clave canónica directa (`battery_capacity_wh`).
2. Clave canónica normalizada (sin tildes, minúsculas).
3. Display alias map (`"batería"` → `battery_capacity_wh`).
4. Concept alias map (`"carga"` → `payload_kg`).

**Sanitización de valor (`_parse_value`):**
- `int` / `float` → `str(raw)`
- String con número → extrae primer número (`"800 Wh"` → `"800"`)
- String sin número (`"mucho"`) → `None` (el wizard pregunta en paso 2)
- `None` → `None`

### 5. Routing semántico en el orquestador (`_semantic_preseed`)

```text
SemanticInterpretation + is_high_confidence=True
    → preseed: {operacion, variable, [valor], seed_step=2}
    → wizard abre directo en paso 2 (saltar paso 1)

AdaptRejection(reason="derived_variable")
    → preseed: {derived_redirect_message}
    → wizard abre en paso 0, muestra mensaje antes de la pregunta objetivo

AdaptRejection(reason="unknown_variable") | confidence < 0.75 | None
    → preseed: {}
    → wizard abre en paso 0 normal
```

### 6. Logging estructurado

Cada llamada a `interpret()` loguea en `runtime/llm_logs/`:

```json
{
  "prompt_version": "v1.2",
  "user_input": "quiero más autonomía",
  "messages": [...],
  "llm_raw_output": "{...}",
  "parsed_output": {"action": "iterate", ...},
  "semantic_trace": {
    "variable": "battery_capacity_wh",
    "confidence": 0.88,
    "routing": "preseed_step2"
  },
  "error": null
}
```

**Valores de `routing`:** `preseed_step2` | `fallback_wizard` | `rejected_derived` | `rejected_unknown` | `n/a`

El log es idéntico en éxito y en error (con `error: null` / `error: "mensaje"`). Los campos `parsed_output` y `semantic_trace` son `null` en el bloque de error.

---

## Pipeline `analyze` — detalle interno

1. `PromptBuilder.build_analysis_messages()` construye mensajes con:
   - Contexto estructurado mínimo del proyecto.
   - Razonamiento determinista (si disponible).
   - Historial conversacional (máx. 6 turnos).
   - Prefill `"En resumen,"` para forzar continuación en español.
2. `OllamaClient.complete(messages, json_mode=False)` — sin `format=json`.
3. Texto retornado directamente al usuario, sin parseado.
4. No muta ningún estado. No invoca motores.

---

## Observabilidad

### Logs

Los logs LLM en `runtime/llm_logs/` permiten analizar:
- Ratio de outputs válidos vs fallback.
- Distribución de routing (`preseed_step2` vs `fallback_wizard` vs `rejected_*`).
- Variables más frecuentes y su confidence media.
- Evolución del comportamiento del modelo tras cambios de prompt.

### Indicadores de calidad v1

Antes de iterar sobre prompts o thresholds, validar con inputs reales:

1. `"quiero más autonomía"` → `battery_capacity_wh`, confidence ≥ 0.75, `routing=preseed_step2`.
2. `"pon batería a 800 Wh"` → variable + valor=800, skip paso 1.
3. `"turbocompresor"` → `AdaptRejection(unknown_variable)` → wizard paso 0.
4. `"autonomía"` → `AdaptRejection(derived_variable)` → wizard paso 0 con mensaje del registry.
5. Entrada ambigua → `confidence < 0.75` → wizard paso 0 normal.

---

## Extensiones diseñadas (no implementadas)

El sistema está diseñado para crecer en estas direcciones sin cambios en los motores deterministas:

### Sugerencias proactivas (Nivel 2)

Con el estado del proyecto disponible en el contexto, el LLM puede inferir acciones que el usuario no pidió:

```json
{
  "suggestions": [
    {
      "action": {"operation": "increase", "variable": "payload_kg", "value": 2.2},
      "reason": "Hay margen de empuje alto sin warnings activos"
    }
  ]
}
```

El sistema pasa de reactivo a proactivo. El resultado pasa por el mismo pipeline de validación.

### Embeddings semánticos

Cuando el registry crezca significativamente, los alias estáticos se pueden complementar con búsqueda por similaridad semántica. Los embeddings asisten la resolución de variable; las reglas deterministas siguen siendo el árbitro final.

### Memoria conversacional extendida

El historial actual (6 turnos, sin persistencia) puede extenderse con memoria persistente de sesión y preferencias explícitas del usuario, aprovechando la estructura `memory` de `state.json`.

---

## Reglas de diseño permanentes

```text
LLM propone → ActionPolicy valida → SemanticIntentAdapter filtra → Orquestador enruta → Motores ejecutan
```

- El LLM nunca ejecuta cálculos.
- El LLM nunca muta `state.json`.
- El LLM nunca accede a `mutation_engine`, `calculation_engine` ni `simulator`.
- El registry (`PARAMETER_REQUIREMENTS`) es el único árbitro de qué variables son modificables.
- Los motores deterministas son intocables desde la capa LLM.
