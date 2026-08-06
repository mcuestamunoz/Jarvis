---

## Diagnóstico

**Estado actual (17 abril 2026):**
- ✅ Refactor `iterate_domain.py` completado — 663 tests
- El sistema tiene **dos sistemas de dominio paralelos que no hablan entre sí**:

```text
Sistema A — componentes físicos (ya dinámico y extensible):
  ComponentRule → ComponentRuleRegistry → domains/aerial.py, domains/ground.py
  → registry_selector (routing por vehicle_type)
  → parameter_requirements.py (catálogo declarativo)

Sistema B — variables del wizard (aún hardcodeado):
  _VALID_VARIABLE_DOMAIN   (frozenset manual en iterate_domain.py)
  _PARAM_DISPLAY_ALIASES   (dict manual en mutation_engine.py)
  _VARIABLE_NORMALIZATION  (dict manual en iterate_domain.py)
  _classify_variable_type  (lógica de strings hardcodeada)
```

El Sistema A ya tiene la arquitectura correcta. El Sistema B es el objetivo de este refactor.

**Condición de activación:** el propeller pipeline (próxima feature) añade variables nuevas
(`propeller_diameter_in`, `propeller_rpm`). Sin el registro unificado, esas variables se
hardcodean **otra vez** en `_VALID_VARIABLE_DOMAIN` y `_PARAM_DISPLAY_ALIASES`.

---

## Veredicto: Ahora.

Alineado con FASE_LLM (objetivo siguiente del sistema):

> `Action Space = generado automáticamente desde código`

Para que el LLM reciba un Action Space estructurado necesita metadatos por variable (`type`,
`aliases`, `description`). Esos metadatos no existen en un frozenset de strings.

---

## Principio de migración

**Los símbolos públicos NO cambian de nombre ni de módulo.**

`_PARAM_DISPLAY_ALIASES`, `_VARIABLE_NORMALIZATION`, `_SEMANTIC_MUTATION_PARAMS`, etc.
siguen existiendo exactamente donde están. Pasan a ser **vistas computadas** del registro,
no fuentes hardcodeadas. Cero cambios en tests ni en imports externos.

---

## Scope del refactor

### Fase 1 — Extender `ParameterRequirement` (nuevos campos con defaults)

**Archivo:** `jarvis/core/parameter_requirements.py`

Primero, añadir `VariableType` como `str, Enum` — consistente con el estilo del codebase
(`ActionName`, `OrchestratorMode`, `IterationOperation`, etc. en `action_schema.py`):

```python
from enum import Enum

class VariableType(str, Enum):
    NUMERIC_DIRECT    = "numeric_direct"    # parámetro numérico settable directamente
    SEMANTIC_MUTATION = "semantic_mutation" # mutación conceptual (reducir/aumentar, no set-to-value)
    NUMERIC           = "numeric"           # genérico numérico (para variables derivadas)
    # futuro: CATEGORICAL, COMPONENT_DEFINE, STRUCTURAL, COMPUTED, LATENT
```

`VariableType` es la **naturaleza** de la variable. `is_derived` es la **política** (¿puedo
setearla?). Son ortogonales — `autonomia` es `NUMERIC` (naturaleza) + `is_derived=True`
(política: no settable directamente).

Luego extender el dataclass:

```python
@dataclass(frozen=True)
class ParameterRequirement:
    name: str
    label: str
    unit: str
    example: str
    keywords: tuple[str, ...]
    # --- NEW (todos con default → las 7 entradas existentes no cambian) ---
    variable_type: VariableType = VariableType.NUMERIC_DIRECT
    # naturaleza funcional de la variable (no política de uso)
    aliases: tuple[str, ...] = ()
    # user-facing display-name aliases → canonical key (reemplaza _PARAM_DISPLAY_ALIASES)
    concept_aliases: tuple[str, ...] = ()
    # concept words que resuelven A esta clave canónica (reemplaza _VARIABLE_NORMALIZATION)
    display_name: str | None = None
    # label humano para semantic_mutation en wizard (reemplaza _SEMANTIC_MUTATION_DISPLAY)
    is_derived: bool = False
    # True → variable no-settable directamente; se intercepta en step 1 del wizard
    derived_message: str | None = None
    # mensaje de redirección cuando el usuario intenta modificar esta variable
    description: str | None = None
    # consumido por build_action_space() para el LLM
```

**Impacto:** cero. Todos los campos nuevos tienen default. Las 7 entradas existentes no se tocan.

> **Ajuste 2 diferido:** separar metadata LLM (`reasoning_hints`, `embedding_keywords`) de
> metadata runtime es correcto pero prematuro — no hay consumidor LLM todavía. Se activa
> cuando `build_action_space()` tenga un caller real en FASE_LLM.

---

### Fase 2 — Nuevas entradas en `PARAMETER_REQUIREMENTS`

**5 entradas nuevas** que trasladan contenido hardcodeado de `iterate_domain.py` y
`mutation_engine.py` al catálogo:

| Canonical key | `variable_type` | `is_derived` | Qué migra |
|---|---|---|---|
| `structure_mass_factor` | `NUMERIC_DIRECT` | `False` | `aliases=("factor_estructura",)` desde `_PARAM_DISPLAY_ALIASES` |
| `safety_factor` | `NUMERIC_DIRECT` | `False` | `aliases=("factor_seguridad",)` desde `_PARAM_DISPLAY_ALIASES` |
| `payload_kg` | `SEMANTIC_MUTATION` | `False` | `concept_aliases=("carga","payload","carga util","carga útil")`, `display_name="el payload (carga útil)"` |
| `autonomia` | `NUMERIC` | `True` | `derived_message="La autonomía es un resultado derivado..."` |
| `propeller_diameter_in` | `NUMERIC_DIRECT` | `False` | Preparado para propeller pipeline |

> **Nota clave:** `autonomia` usa `variable_type=NUMERIC` (naturaleza: es un número)
> + `is_derived=True` (política: el wizard intercepta en step 1 antes de entrar a
> `_classify_variable_type`). Esto respeta la separación real del código — `_DERIVED_VARIABLE_MESSAGES`
> se consume en step 1, `_classify_variable_type` se invoca en step 2. Son capas distintas.

**Beneficio inmediato:** añadir variables del propeller pipeline no requiere tocar
`iterate_domain.py` ni `mutation_engine.py` — solo añadir una entrada aquí.

---

### Fase 3 — Nuevos helpers en `parameter_requirements.py`

```python
def build_alias_map() -> dict[str, str]:
    """alias → canonical. Reemplaza _PARAM_DISPLAY_ALIASES como fuente."""

def build_normalization_map() -> dict[str, str]:
    """concept_alias → canonical. Reemplaza _VARIABLE_NORMALIZATION como fuente."""

def build_semantic_params() -> frozenset[str]:
    """Claves canónicas con variable_type=VariableType.SEMANTIC_MUTATION."""

def build_valid_domain() -> frozenset[str]:
    """Todos los names + aliases + concept_aliases + derived names del registro."""

def get_derived_message(var_normalised: str) -> str | None:
    """Mensaje de redirección para variables derivadas. Reemplaza _DERIVED_VARIABLE_MESSAGES."""

def get_display_name(canonical: str) -> str | None:
    """Label humano para semantic_mutation. Reemplaza _SEMANTIC_MUTATION_DISPLAY."""

def build_action_space() -> dict:
    """Dict consumible por LLM: {canonical: {type, description, aliases, ...}}"""

def validate_registry() -> None:
    """
    Comprueba integridad del registro en tiempo de carga. Lanza ValueError si:
    - canonical keys repetidas
    - aliases duplicados entre entradas
    - is_derived=True sin derived_message
    - variable_type=SEMANTIC_MUTATION sin display_name
    - entries sin description
    """
```

> **Política de normalización de aliases:** los builder functions (`build_alias_map`,
> `build_normalization_map`) aplican `_normalize_alias()` a todas las keys que emiten:
> lowercase + strip diacritics + strip. Esto permite escribir las entradas del registro con
> texto natural (con tildes: `"batería"`) y garantiza que las keys del dict resultante sean
> siempre normalizadas (`"bateria"`), evitando duplicados invisibles. El mismo normalizador
> ya existe en `iterate_domain._normalize_variable_input()` — se mueve/reusar desde ahí.

---

### Fase 4 — `mutation_engine.py`: `_PARAM_DISPLAY_ALIASES` → vista computada

```python
# Antes (hardcoded):
_PARAM_DISPLAY_ALIASES: dict[str, str] = {
    "factor_estructura": "structure_mass_factor",
    ...
}

# Después (computed, mismo símbolo, cero impacto en consumidores):
from jarvis.core.parameter_requirements import build_alias_map
_PARAM_DISPLAY_ALIASES: dict[str, str] = build_alias_map()
```

Los 3 tests que importan `_PARAM_DISPLAY_ALIASES` desde `mutation_engine` siguen funcionando sin cambios.

---

### Fase 5 — `_classify_variable_type`: leer `variable_type` del registro

> Adelantada antes de la migración de `iterate_domain.py` para validar el registro con
> comportamiento real antes de la migración masiva.

```python
def _classify_variable_type(self, variable: str, current_params: dict) -> str:
    # 1. Consultar registro primero (cubre semantic_mutation)
    req = PARAMETER_REQUIREMENTS.get(variable)
    if req and req.variable_type == VariableType.SEMANTIC_MUTATION:
        return "semantic_mutation"
    # Nota: is_derived NO se consulta aquí — las variables derivadas
    # se interceptan en step 1 (antes de que este método se invoque en step 2).
    # 2. numeric_direct — igual que ahora (depende de current_params en runtime)
    if self._match_numeric_param(variable, current_params) is not None:
        return "numeric_direct"
    # 3–7. el resto igual (material, structural_physical, etc.)
    ...
```

`_classify_variable_type` sigue siendo un método de instancia porque el caso `numeric_direct`
necesita `current_params` en runtime. Eso no cambia.

---

### Fase 6 — `iterate_domain.py`: dicts hardcodeados → vistas computadas

```python
# Antes (hardcoded):
_VARIABLE_NORMALIZATION = {"carga": "payload_kg", ...}

# Después (computed, mismo símbolo):
from jarvis.core.parameter_requirements import (
    build_normalization_map, build_semantic_params, build_valid_domain,
    get_derived_message, get_display_name,
)

_VARIABLE_NORMALIZATION  = build_normalization_map()
_SEMANTIC_MUTATION_PARAMS = build_semantic_params()
_VALID_VARIABLE_DOMAIN   = build_valid_domain() | _STRUCTURAL_TERMS
# _STRUCTURAL_TERMS = frozenset({"material","dimensiones","dimension","estructura",...})
# Estos NO son params del sistema → no entran al registro → constante local en iterate_domain.py
```

`iterate_domain.py` pasa a ser una **capa de adaptación** entre el registro y el wizard,
no una fuente de verdad.

---

## Impacto en tests

| Fase | Tests afectados | Cambio en tests |
|---|---|---|
| 1 | 0 | Campos con defaults + VariableType Enum, nada rompe |
| 2 | 0 | Entradas nuevas, no se tocan las existentes |
| 3 | 0 | Helpers nuevos, nadie los usa aún |
| 4 | 0 | `_PARAM_DISPLAY_ALIASES` mismo símbolo, mismos valores |
| 5 | 0 | Comportamiento de routing idéntico (`is_derived` no entra aquí) |
| 6 | 0 | Símbolos de `iterate_domain` idénticos, mismos valores |

**Objetivo: 663/663 verificado tras cada fase.**

---

## Orden de ejecución

```
✅ Refactor iterate_domain.py         (completado)
→  Fase 1: extender ParameterRequirement + VariableType Enum  [pytest: 663]
→  Fase 2: 5 entradas nuevas                                   [pytest: 663]
→  Fase 3: helpers build_*                                     [pytest: 663]
→  Fase 4: mutation_engine computado                           [pytest: 663]
→  Fase 5: _classify_variable_type usa registro (1er consumer) [pytest: 663]
→  Fase 6: iterate_domain dicts computados (migración masiva)  [pytest: 663]
   Post-refactor → build_action_space() → FASE_LLM
```

> **Rationale del orden Fase 5 antes de Fase 6:** `_classify_variable_type` es el primer
> consumidor real del registry. Validar que el routing es correcto con el registro antes
> de migrar todos los dicts de `iterate_domain.py` reduce el riesgo de introducir errores
> silenciosos en la migración masiva.

---

## Lo que desbloquea

Tras las 6 fases, `build_action_space()` produce el Action Space para el LLM:

```python
build_action_space()
# {
#   "payload_kg": {
#       "type": "semantic_mutation",
#       "settable": True,
#       "description": "Carga útil del sistema",
#       "aliases": ["carga", "payload", "carga util", "carga util"],  # ya normalizadas
#       "display_name": "el payload (carga útil)"
#   },
#   "battery_capacity_wh": {
#       "type": "numeric_direct",
#       "settable": True,
#       "description": "Capacidad de batería",
#       "aliases": ["bateria", "bateria", "capacidad_bateria", ...],   # ya normalizadas
#   },
#   "autonomia": {
#       "type": "numeric",        # naturaleza (VariableType)
#       "derived": True,          # política (is_derived)
#       "settable": False,
#       "message": "La autonomía es un resultado derivado..."
#   },
#   ...
# }
```

> **Nota:** `settable = not is_derived`. El LLM recibe naturaleza (`type`) y política
> (`derived`, `settable`) como campos separados — coherente con el modelo ortogonal
> establecido en Fase 1.

Este dict se inyecta directamente en el prompt del LLM sin procesar código Python.

---

## Nota sobre términos estructurales

`_STRUCTURAL_TERMS` (`material`, `dimensiones`, `dimension`, `estructura`, `componentes`,
`componente`, `potencia`, `empuje`) **no entran al registro** porque no son parámetros de
sistema — son términos léxicos del wizard que activan ramas declarativas. Permanecen como
constante local en `iterate_domain.py`.

---

## Checklist de implementación

> Marcar cada ítem al completar. Verificar 663/663 tras cada fase antes de continuar.

### ✅ Pre-refactor
- [x] Baseline: `pytest` → 663/663 antes de empezar

### Fase 1 — Extender `ParameterRequirement` ✅
- [x] Añadir `VariableType(str, Enum)` en `parameter_requirements.py`
- [x] Añadir nuevos campos al dataclass (`variable_type`, `aliases`, `concept_aliases`, `display_name`, `is_derived`, `derived_message`, `description`)
- [x] Verificar: `pytest` → 663/663

### Fase 2 — Nuevas entradas en `PARAMETER_REQUIREMENTS` ✅
- [x] Añadir entrada `structure_mass_factor` con `aliases=("factor_estructura",)`
- [x] Añadir entrada `safety_factor` con `aliases=("factor_seguridad",)`
- [x] Añadir entrada `payload_kg` con `variable_type=SEMANTIC_MUTATION`, `concept_aliases`, `display_name`
- [x] Añadir entrada `autonomia` con `variable_type=NUMERIC`, `is_derived=True`, `derived_message`
- [x] Añadir entrada `propeller_diameter_in` (placeholder)
- [x] Corrección: añadir `aliases` a 4 entradas existentes (`battery_capacity_wh`, `motor_power_w`, `motors`, `per_motor_max_thrust_n`) — necesario para que `build_alias_map()` en Fase 4 produzca los 18 valores idénticos al dict hardcodeado actual
- [x] Verificar: `pytest` → 663/663

### Fase 3 — Helpers en `parameter_requirements.py` ✅
- [x] Definir `_normalize_alias()` (lowercase + strip diacritics + strip — reusar lógica de `iterate_domain._normalize_variable_input`)
- [x] Implementar `build_alias_map()` (aplica `_normalize_alias` a keys) — verificado igual a `_PARAM_DISPLAY_ALIASES` normalizado
- [x] Implementar `build_normalization_map()` (aplica `_normalize_alias` a keys) — verificado igual a `_VARIABLE_NORMALIZATION` normalizado
- [x] Implementar `build_semantic_params()` — verificado igual a `_SEMANTIC_MUTATION_PARAMS`
- [x] Implementar `build_valid_domain()`
- [x] Implementar `get_derived_message()` — verificado igual a `_DERIVED_VARIABLE_MESSAGES`
- [x] Implementar `get_display_name()` — verificado igual a `_SEMANTIC_MUTATION_DISPLAY`
- [x] Implementar `build_action_space()` (output: `type` + `derived` + `settable` separados)
- [x] Implementar `validate_registry()` — detectó y corrigió duplicados de aliases en Fase 2 (forma esperada: `validate_registry` funciona en tiempo de carga)
- [x] Llamar `validate_registry()` al nivel de módulo tras definir `PARAMETER_REQUIREMENTS`
- [x] Verificar: `pytest` → 663/663

### Fase 4 — `mutation_engine.py` computado ✅
- [x] Reemplazar `_PARAM_DISPLAY_ALIASES` hardcodeado → `build_alias_map()`
- [x] Actualizar `_is_numeric_param_mutation` y `apply_numeric_param_mutation`: `.lower()` → `_normalize_alias()` en los consumption sites (necesario porque el dict ahora tiene keys normalizadas)
- [x] Extraer set de `_is_numeric_param_mutation` a `_NUMERIC_PARAM_KEYS` constante de módulo
- [x] `resolve_strategy`: `.lower()` → `normalize_alias()` en todos los campos de texto (cierra gap diacrítico en routing)
- [x] Renombrar `_normalize_alias` → `normalize_alias` (público — múltiples importadores en Fase 6)
- [x] Añadir test CROSS-1: `normalize_alias` ↔ `_normalize_variable_input` producen output idéntico
- [x] Actualizar 2 tests (Bug 22, Bug 31) al nuevo contrato: keys normalizadas en el dict
- [x] Verificar: `pytest` → 664/664

### Fase 5 — `_classify_variable_type` usa registro ✅
- [x] Importar `PARAMETER_REQUIREMENTS`, `VariableType` en `iterate_interactive_session.py`
- [x] Consultar `PARAMETER_REQUIREMENTS.get(variable).variable_type` primero en `_classify_variable_type`
- [x] Mantener fallback a `_SEMANTIC_MUTATION_PARAMS` para entries no migradas (eliminado en Fase 6)
- [x] Confirmar que `is_derived` NO se consulta aquí (interceptado en step 1, antes de este método)
- [x] Verificar: `pytest` → 664/664

### Fase 6 — `iterate_domain.py` dicts computados ✅
- [x] `_VARIABLE_NORMALIZATION` → `build_normalization_map()`
- [x] `_SEMANTIC_MUTATION_PARAMS` → `build_semantic_params()`
- [x] `_SEMANTIC_MUTATION_DISPLAY` → eliminado; callsite usa `get_display_name(_var) or _var`
- [x] `_DERIVED_VARIABLE_MESSAGES` → eliminado; callsite usa `get_derived_message(normalize_alias(normalized))`
- [x] `_VALID_VARIABLE_DOMAIN` → `build_valid_domain() | _STRUCTURAL_TERMS`
- [x] `_STRUCTURAL_TERMS` añadido como constante local (`material`, `dimensiones`, `componentes`, etc.)
- [x] Eliminar NOTE comment sobre dependency en `mutation_engine._PARAM_DISPLAY_ALIASES`
- [x] Eliminar TODO comment sobre `_VALID_VARIABLE_DOMAIN` derivado del registro
- [x] Eliminar `_NORMALIZED_PARAM_ALIAS_KEYS` y tier 4 de `_is_valid_variable` (redundante — `_VALID_VARIABLE_DOMAIN` lo cubre)
- [x] Eliminar fallback a `_SEMANTIC_MUTATION_PARAMS` en `_classify_variable_type` (registro es fuente única)
- [x] `_update_draft_for_step`: `user_input.lower()` → `normalize_alias(user_input)` (keys del dict ahora normalizadas)
- [x] `_normalize_variable_input` eliminado del import en `iterate_interactive_session.py` (reemplazado por `normalize_alias`)
- [x] Verificar: `pytest` → 664/664

### Post-refactor
- [x] Confirmar que `build_action_space()` produce output correcto para FASE_LLM
- [x] Actualizar `ARCHITECTURE.md` (iterate_domain → capa de adaptación)
- [x] Actualizar `IMPLEMENTATION_TASKS.md` (Domain Registry entry)
