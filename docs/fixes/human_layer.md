Ambos análisis apuntan a lo mismo: el núcleo físico está sólido, el cuello de botella es la capa conversacional. Aquí está mi síntesis y el plan de fixes.

---

## Diagnóstico consolidado

| # | Bug / Gap | Severidad | Fuente |
|---|---|---|---|
| 1 | Preguntas informativas abren wizard de iterate | Crítica | Ambos |
| 2 | Warnings en código interno, no en lenguaje humano | Alta | GPT |
| 3 | Error de variable desconocida no guía al camino correcto | Media | Ambos |
| 4 | Componente declarativo no da feedback de "qué falta para activarlo" | Media | GPT |
| 5 | "mejorar carga útil" no genera opciones estratégicas | Media | GPT |

---

## Plan de fixes — Human Layer Sprint v1

### Fix 1 — Preguntas informativas siempre → `analyze` (crítico)

**Problema exacto:** tras un iterate completado, el LLM preseed mantiene contexto de variable. Cuando llega `"dime cuales son los warnings"`, el routing detecta preseed activo y abre wizard en lugar de ir a `analyze`.

**Cambio propuesto:**
Clasificar cada input en una de dos clases por intención semántica (no solo regex literal), antes de evaluar preseed LLM:

- **INFORMATION_SEEKING** — keywords: `qué`, `por qué`, `cuáles`, `explica`, `dime`, `estado`, `warnings`, `fallo`, `significa`, `cómo va`
- **ACTION_SEEKING** — keywords: `cambia`, `reduce`, `aumenta`, `mejora`, `optimiza`, `define`, `añade`, `pon`

Reglas de routing:
- Solo `INFORMATION_SEEKING` → `analyze` incondicional, sin importar sesión activa ni preseed.
- Solo `ACTION_SEEKING` → continúa flujo normal (preseed si aplica).
- Mezcla de ambas (ej: `"quiero mejorar autonomía, qué recomiendas"`) → prioridad híbrida → `analyze`.

La función `_classify_input_intent(text) -> Literal["information", "action", "hybrid"]` vive en `orchestrator.py` y se llama como primer guard en `handle_user_text`, antes de cualquier evaluación LLM.

**Archivos:** `core/orchestrator.py` (~15 líneas)

---

### Fix 2 — Warnings en lenguaje humano (alta)

**Problema exacto:** `low_margin`, `high_actuator_load`, `low_force_to_weight_ratio` se muestran como códigos internos.

**Cambio propuesto:**
- Añadir `WARNING_MESSAGES: dict[str, str]` en `main.py` o en un módulo `utils/display.py`:
  ```
  low_margin → "Margen de seguridad ajustado — el sistema opera cerca del límite. Riesgo ante variaciones de carga o viento."
  high_actuator_load → "Los motores trabajan cerca de su capacidad máxima. Un pico de carga puede comprometer el vuelo."
  low_force_to_weight_ratio → "La relación empuje/peso es baja. El sistema tiene poca reserva para maniobras o peso extra."
  ```
- En el display de simulación en `main.py`, reemplazar el `warnings=` raw por las descripciones.

**Archivos:** `main.py` + opcional `utils/display.py` (~20 líneas)

---

### Fix 3 — Error de variable desconocida guía al usuario (media)

**Problema exacto:** `"Error: No reconozco 'helices' como variable modificable."` no dice cómo proceder.

**Cambio propuesto:**
- Después del mensaje de error, añadir: `"Para definir componentes físicos (hélices, motores, batería, sensores), di 'componentes'."`
- Opcionalmente, si el término desconocido tiene similitud semántica con algún alias del registry (ej: "helices" ≈ "componentes" → `propulsion_passive`), sugerirlo directamente.

**Archivos:** `core/iterate_interactive_session.py` (~3 líneas)

---

### Fix 4 — Componente declarativo informa qué falta para activarlo (media)

**Problema exacto:** tras definir `hélice 9.8x4.2`, el sistema dice "sin impacto físico en esta versión" y el usuario queda sin camino claro.

**Cambio propuesto:**
- Cuando `operation == DEFINE` y el componente es `propulsion_passive` → añadir al output:
  ```
  "Para conectar esta hélice al modelo físico, necesito:
  - propeller_diameter_in (ej: 9.8)
  - propeller_rpm (ej: 8000)
  Di 'definir parámetros de hélice' cuando estés listo."
  ```
- Usar `PARAMETER_REQUIREMENTS["missing_propeller_parameters"]` como fuente de los parámetros a listar (no hardcodear).

**Archivos:** `actions/iterate.py` o el formateador de output en `main.py` (~10 líneas)

---

### Fix 5 — Goal planner básico: objetivo → opciones estratégicas (media, nuevo)

**Problema exacto:** `"mejorar carga útil"` devuelve analyze genérico en lugar de opciones concretas accionables.

**Cambio propuesto:**
- Añadir `GOAL_STRATEGIES: dict[str, list[dict]]` en `core/reasoning_layer.py`:
  ```python
  "aumentar_payload": [
      {"acción": "Aumentar empuje disponible", "cómo": "Más motores o motores de mayor empuje"},
      {"acción": "Reducir masa estructural", "cómo": "Cambiar material o reducir factor estructura"},
      {"acción": "Optimizar hélices", "cómo": "Hélices de mayor diámetro generan más thrust por W"},
  ]
  ```
- Cuando el intent es `analyze` Y el texto contiene objetivo de mejora (`"mejorar X"`, `"cómo aumentar X"`, `"qué hago con X"`), inyectar `GOAL_STRATEGIES` en el contexto del LLM en lugar de solo pasar el estado.
- El LLM usa ese contexto para generar la respuesta → no es determinista puro, pero sí guiado.

**Archivos:** `core/reasoning_layer.py` + `llm/prompt_builder.py` (~30 líneas)

---

## Orden de implementación propuesto

1. **Fix 1** — routing (desbloquea todo lo demás, es el más urgente)
2. **Fix 2** — warnings en humano (impacto alto, esfuerzo bajo)
3. **Fix 3** — error guidance (5 minutos de trabajo)
4. **Fix 4** — declarative feedback (necesita Fase 2 para el camino completo, pero el mensaje ya se puede añadir ahora)
5. **Fix 5** — goal planner (más complejo, sesión separada)

---
