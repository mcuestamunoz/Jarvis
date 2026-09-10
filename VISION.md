# Jarvis — Visión

**v0.1 · prototipo funcional · 2026**

Jarvis demuestra que un **motor de ingeniería determinista** puede diseñar y validar sistemas físicos con **lenguaje natural asistido por IA** — sin que el modelo invente la física.

## Qué es

Un asistente de diseño de ingeniería (primero aéreo: drones y vehículos relacionados) que:

- entiende objetivos y restricciones en castellano,
- mantiene un estado de proyecto trazable,
- calcula y simula con reglas explícitas,
- propone cambios que el ingeniero confirma.

La IA interpreta y sugiere. **Los motores de cálculo y simulación deciden qué es físicamente coherente.**

## Qué no es

No es CAD, ni FEM, ni un marketplace de piezas, ni un chatbot que “opina” de ingeniería.  
No sustituye el criterio del ingeniero: lo acelera y lo documenta.

## Principio

```text
Requisitos e intención humana
        ↓
Interpretación (reglas + IA cuando hace falta)
        ↓
Física determinista (cálculo / simulación / mutación)
        ↓
Estado y historial auditables
```

El conocimiento de ingeniería debe permanecer **estable y comprobable**.  
El conocimiento de mercado (catálogos, proveedores) puede evolucionar aparte.

## Para qué existe v0.1

Probar, en uso real, que ese contrato aguanta: crear un sistema, definirlo por componentes, calcular, simular, iterar y explorar alternativas — con un núcleo en el que se puede confiar.

## Hacia v1 usable

Cerrar un proyecto aéreo con *pass + requisitos + gaps/BOM*, sin ambigüedad. Detalle: [PRODUCT_SCOPE.md](PRODUCT_SCOPE.md).

## Project Continuity → Project Coherence

Jarvis no acompaña “fases”. El **proyecto** es el protagonista:

- Al **reabrir**: situación / evidencia / un siguiente paso útil (A').
- En **toda** la conversación: las operaciones no sustituyen al proyecto — **Project Coherence**. Tras cada operación relevante debe quedar claro qué cambió, cómo está el proyecto ahora y cuál es la siguiente decisión útil.

Regla y field notes: [docs/PROJECT_CONTINUITY.md](docs/PROJECT_CONTINUITY.md).
No construir aún un “Conversation Engine”: descubrir con uso real en CLI.

## Continuity spatial assembly (*situar el mapa*) — v0.4

En el Board 3D, Jarvis sitúa **cajas declaradas** (o citadas) en un marco en milímetros: envelope + pose + copias de visor (p. ej. 4 motores / 4 brazos) **sin** que el LLM invente cotas y **sin** partir el BOM en N piezas falsas.

Contrato de producto: [`.jes/artifacts/engineer_lock_continuity_spatial_assembly_feature.md`](.jes/artifacts/engineer_lock_continuity_spatial_assembly_feature.md).  
Siguiente dirección de UX: arrastrar/ampliar en el Board escribiendo a los **mismos** writers ([nota](.jes/artifacts/engineer_note_board_drag_place_concept.md)).

Si dentro de cinco años lees esto, la pregunta sigue siendo la misma:  
**¿Jarvis sigue siendo el lugar donde la física no se negocia?**
