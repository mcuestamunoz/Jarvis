
---

## Diagnóstico

**Estado actual (16 abril 2026):**
- ✅ G1 completado — Bugs 30, 28, 27 — 640 tests
- ✅ G2 completado — Bugs 35, 36, 31, 29 — 654 tests
- ✅ G3 completado — Bugs 32, 34, 33, 37 — 663 tests
- `iterate_interactive_session.py` tiene **1659 líneas**; las primeras 177 son constantes de dominio y helpers puros completamente desacoplados del estado de sesión
- Próxima feature: propeller pipeline → toca `tools/`, `calculation_engine`, `parameter_requirements.py` — **no toca este archivo**

---

## Veredicto: Ahora.

G3 completado. Comportamiento 100 % estabilizado. Los 663 tests son la red de seguridad.
El refactor es un movimiento mecánico: constantes y funciones puras que **no tienen acceso a `self`** entran en un módulo propio. Cero lógica cambia.

---

## Scope del refactor

**Extraer → `jarvis/core/iterate_domain.py`** (nuevo archivo)

Todo lo que precede a `class IterateInteractiveSession` en el archivo actual (líneas 28–177), **excepto `IteratePrompt`** (ver abajo):

| Símbolo | Tipo |
|---|---|
| `_VARIABLE_NORMALIZATION` | dict |
| `_SEMANTIC_MUTATION_PARAMS` | frozenset |
| `_SEMANTIC_MUTATION_DISPLAY` | dict |
| `_DERIVED_VARIABLE_MESSAGES` | dict |
| `_normalize_variable_input()` | función pura |
| `_VARIABLE_FUZZY_PAIRS` | list |
| `_fuzzy_normalize_variable()` | función pura |
| `_VALID_VARIABLE_DOMAIN` | frozenset |
| `_NORMALIZED_PARAM_ALIAS_KEYS` | frozenset |
| `_is_valid_variable()` | función pura |
| `_KNOWN_MATERIALS` | dict |

`iterate_domain.py` solo necesita:
```python
from __future__ import annotations
import unicodedata
from jarvis.core.mutation_engine import _PARAM_DISPLAY_ALIASES
```

`IteratePrompt` (dataclass de preguntas UX) **no se mueve** — permanece en `iterate_interactive_session.py`. Es flujo conversacional, no dominio.

**`iterate_interactive_session.py` después del refactor:**
- Se eliminan las líneas 28–177 (constantes de dominio y validators)
- Se añade un import explícito desde el nuevo módulo:
```python
from jarvis.core.iterate_domain import (
    _VARIABLE_NORMALIZATION,
    _SEMANTIC_MUTATION_PARAMS,
    _SEMANTIC_MUTATION_DISPLAY,
    _DERIVED_VARIABLE_MESSAGES,
    _normalize_variable_input,
    _fuzzy_normalize_variable,
    _is_valid_variable,
    _KNOWN_MATERIALS,
)
```
`IteratePrompt` se define directamente en `iterate_interactive_session.py` (es UX/flujo, no dominio).
`_VALID_VARIABLE_DOMAIN` y `_NORMALIZED_PARAM_ALIAS_KEYS` **no se re-exportan** — son detalles internos de `_is_valid_variable` dentro de `iterate_domain.py`.

El archivo pasa de **1659 a 1517 líneas**.

**Quedan en `IterateInteractiveSession`** (tightly coupled al estado de sesión):
- `answer()`, `start()`, `_handle_*`
- `_match_numeric_param()` — lee `current_params` del estado
- `_classify_variable_type()` — routing de flujo
- `_estimate_*`, `_impact_message`, `_question_for_session` — usan `self._library` y estado del draft

---

## Plan de ejecución

```
✅ G2 (Bugs 35, 36, 31, 29)
✅ G3 (Bugs 32, 34, 33, 37)
✅ Refactor: extraer iterate_domain.py
   Post-refactor → Propeller pipeline
```

### Estado final

1. ✅ `jarvis/core/iterate_domain.py` creado con 11 símbolos
2. ✅ Líneas de constantes/validators eliminadas de `iterate_interactive_session.py`
3. ✅ Import desde `iterate_domain` añadido
4. ✅ `IteratePrompt` devuelto a `iterate_interactive_session.py` (es flujo UX)
5. ✅ 663/663 tests sin regresiones