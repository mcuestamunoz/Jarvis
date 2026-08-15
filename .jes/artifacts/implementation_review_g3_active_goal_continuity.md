# Informe de revisión — G3 Active Goal Continuity

**Proyecto:** Jarvis  
**Fecha:** 2026-08-14  
**Revisor:** Cursor (JES)  
**Tipo:** Implementation Review (código + contrato + integración de sistema)  

**Contrato:** `.jes/artifacts/implementation_contract_g3_active_goal_continuity.md`  
**Informe Claude:** `.jes/artifacts/implementation_report_g3_active_goal_continuity.md`  
**Diseño:** `.jes/artifacts/design_g3_active_goal_continuity.md` (CLOSED ★1–★4)  
**Base:** tag `checkpoint-g5-dse-component-sync`  

---

## 1. Veredicto

### **PASS WITH NOTES**

G3 cumple el contrato, cierra el finding CLI de continuidad, y queda bien integrado en el stack Goal Plan → Handoff → DSE sin contaminar F-1, H1–H4, G5 ni catálogo.

| Criterio | Resultado |
|---|---|
| ★1 — `optimiza payload` hereda plan reducir | ✅ |
| ★2 — otra dimensión override | ✅ |
| ★3 — no dual-fire plan vs explore | ✅ |
| ★4 — replace HandoffContext tras override | ✅ |
| H1 bare `explora opciones` intacto | ✅ |
| Suite completa | ✅ **1715 passed** (re-run revisor) |
| Scope (sin G6/G7/Impl C/H5) | ✅ |

---

## 2. Qué problema cerraba G3

Tras un Goal Plan activo, dos frases de exploración se comportaban distinto:

```text
Plan: reducir_payload

"explora opciones"   → DSE reducir     ✅  (H1)
"optimiza payload"   → DSE aumentar    ❌  (re-derive del texto)
```

Causa: `_handle_explore` solo consultaba el handoff cuando `goal_key is None`. Cualquier goal derivado del texto ganaba, aunque fuera undirected. F-1 hace que bare `"payload"` defaultee a `aumentar_payload` — correcto en aislamiento, pero invertía el plan activo.

Precedencia bloqueada en diseño:

```text
explicit new goal  >  active goal  >  inferred/default goal
```

---

## 3. Qué se implementó

### 3.1 Helper puro — `explore_continuity.resolve_explore_goal_with_handoff`

- Un solo punto de precedencia, testeable, sin I/O.
- Reutiliza `_direction_of` / `_normalize` de F-1 (sin NLP paralelo).
- Familias de dimensión mínimas (payload / mass / autonomy / stability).

**Aclaración de diseño aceptada:**  
`"optimiza payload"` y `"optimiza para aumentar el payload"` pueden colapsar al mismo `text_goal=aumentar_payload`. La distinción continuation vs override **debe** mirar la dirección en el texto crudo, no solo el enum del goal. La implementación lo hace bien y lo documenta.

### 3.2 Wiring — `orchestrator._handle_explore`

- Handoff se carga siempre (no solo si `goal_key is None`).
- Tres casos bien separados vía `using_handoff_goal`:

| Caso | Comportamiento |
|---|---|
| Bare explore / herencia G3 | Mismas reglas H1 de `dse_capability` (active / consumed) |
| Frase explícita que ya nombra el goal activo | Capability-neutral (FN-024 §4.2) — handoff intacto |
| Override explícito / otra dimensión | Explore independiente + ★4 replace |

### 3.3 ★4 — replace handoff

Tras override exitoso:

- Nuevo `HandoffContext` con `goal_key` / levers del goal explorado.
- `dse_capability="consumed"` (honesto: ese explore ya corrió).
- Un posterior `"explora opciones"` habla del **goal nuevo**, no del stale.

### 3.4 Archivos tocados

```text
src/jarvis/core/explore_continuity.py   (nuevo)
src/jarvis/core/orchestrator.py         (wiring)
tests/test_g3_active_goal_continuity.py (22 tests)
```

**No tocados:** `goal_planner.py`, `intent_resolver.py`, H4, catalog, G5.

---

## 4. Regresión detectada durante la implementación (positiva)

La primera versión de `using_handoff_goal` trataba “resolved == handoff.goal_key” como herencia. Eso rompía un test FN-024 existente:

```text
Plan estabilidad activo
+ "optimiza para estabilidad"   (explícito, ya resuelve al mismo goal)
→ debía dejar dse_capability="active" (capability-neutral)
→ la wiring ingenua lo consumía
```

Se corrigió exigiendo que `text_goal != handoff.goal_key` **antes** de contar como herencia real. Sweep de regresiones limpio después.

Esto no es un defecto residual: es evidencia de integración cuidadosa con H1.

---

## 5. Tests ejecutados (revisor)

```text
tests/test_g3_active_goal_continuity.py
+ FN-024 / FN-025 / FN-026 / F-1
→ 106 passed

pytest -q (suite completa)
→ 1715 passed
```

Cobertura relevante: función pura (reglas 1–5), T1–T7 E2E, ★3 dual-fire, honestidad post-consumed, levers del handoff reemplazado.

---

## 6. Integración a nivel de sistema

El stack queda coherente:

```text
Intención / Goal Plan     (FN-022, F-1)
        ↓
HandoffContext            (C-105 / H1)
        ↓
Explore
  · bare "explora opciones"     → H1
  · undirected same-dimension   → G3 herencia
  · override / otra dimensión   → texto gana + ★4 replace
        ↓
DSE → apply               (G5 sync component)
        ↓
Iterate / H4 lever preseed (levers siguen el handoff actual)
```

| Capa | Impacto G3 |
|---|---|
| F-1 goal_planner | Ninguno (default bare payload intacto) |
| H1 capability | Preservado; herencia usa los mismos gates |
| H4 | Mejorado indirectamente (handoff replace trae levers correctos) |
| G5 / catálogo | Ninguno |
| G6 / G7 | Fuera de scope (correcto) |

**Riesgo “memoria que ignora al usuario”:** mitigado. Dirección explícita u otra dimensión siguen siendo override.

---

## 7. Notes (no bloquean el PASS)

1. **Frase T3 del contrato** (`"ahora aumenta el payload"`) no entra por explore: va a `engineering_intent` (★3). El override *dentro* de explore se prueba con `"optimiza para aumentar el payload"`. Aceptable; el CLI probe debe usar esa frase.

2. Continuaciones G3 tras `dse_capability=consumed` reciben el mismo mensaje honesto H1 (“Ya exploré opciones…”). Expansión correcta de honestidad.

3. Si F-1b añade direcciones a otras dimensiones, habrá que revisar si `_direction_of` basta para esas frases — mismo caveat que F-1.

---

## 8. CLI probe recomendado (Engineer)

```text
reducir payload
optimiza payload                         → minimizar/reducir  (NO maximizar)
optimiza para aumentar el payload      → maximizar
explora opciones                         → "Ya exploré… maximizar carga útil"
```

---

## 9. Estado del roadmap tras este informe

```text
✅ Catalog Impl A + Impl B
✅ F-1
✅ G5 (investigation + fix + CLI + checkpoint)
✅ G3 (design + implement + review PASS WITH NOTES)
📝 G6 / G7 registrados — sin implementar

Siguiente:
  CLI probe G3 (opcional)
        ↓
  checkpoint-g3
        ↓
  G1/G2 + H5 design
        ↓
  UX catálogo → Impl C
```

**No se recomienda Impl C todavía.** La capa de intención/continuidad sigue siendo el cuello de botella arquitectónico correcto antes de más SKUs.

---

## 10. Conclusión

G3 no es un parche de keywords: restaura la precedencia conversacional entre **plan activo** y **mensaje aislado**, en la capa correcta (explore + handoff), sin reescribir el goal planner ni abrir Conversation Engine.

**Listo para CLI de confirmación y checkpoint cuando el Engineer lo pida.**
