# Pruebas manuales CLI — Jarvis

Checklist de validación end-to-end del sistema completo a través de `python -m jarvis.main --chat`.

**Estado:** ✅ Superado · ⚠️ Bug detectado · ❌ Fallo · ⬜ Pendiente

---

## Bloque 0 — Arranque y selección de proyecto

| # | Input / Acción | Qué esperar | Estado | Notas |
|---|----------------|-------------|--------|-------|
| 0.1 | Arrancar con múltiples proyectos | Lista numerada de proyectos | ✅ | |
| 0.2 | Seleccionar por número (`1`, `2`...) | Proyecto cargado + startup_context | ✅ | |
| 0.3 | Seleccionar por texto (`el último`, `continuar`) | Proyecto cargado | ✅ | carga `autonomia` correctamente |
| 0.4 | `n` / `nuevo` en selección inicial | Caer al loop normal → wizard creación | ✅ | wizard CREATE_PROJECT abre directamente |
| 0.5 | Arrancar sin proyectos | "No hay proyectos todavía. Cuéntame qué quieres diseñar." | ✅ | proyectos movidos a /tmp para el test |
| 0.6 | Arrancar con proyecto activo + `status=pass` | Startup context con ✓ Última simulación: OK | ✅ | |
| 0.7 | Arrancar con proyecto activo + parámetros faltantes | Startup context con ✗ Simulación incompleta + lista params | ✅ | wizard DEFINE_MISSING se abre automáticamente |
| 0.8 | Arrancar con proyecto activo + `status=warning` | Startup context con ⚠ Última simulación: WARNING | ✅ | fixture editado manualmente en state.json |

---

## Bloque 1 — Comandos globales (idle)

| # | Input | Qué esperar | Estado | Notas |
|---|-------|-------------|--------|-------|
| 1.1 | `help` | Mensaje de ayuda con ejemplos | ✅ | |
| 1.2 | Input vacío (Enter) | Silencio / ignorado | ✅ | |
| 1.3 | `exit` | "Sesión cerrada." | ✅ | |
| 1.4 | `quit` | "Sesión cerrada." | ✅ | |
| 1.5 | `cancelar` en idle | Mensaje "no hay operación activa" o similar | ✅ | |

---

## Bloque 2 — CREATE_PROJECT wizard

| # | Input | Qué esperar | Estado | Notas |
|---|-------|-------------|--------|-------|
| 2.1 | `quiero diseñar un dron` | Wizard de creación → pregunta nombre/objetivo | ✅ | |
| 2.2 | `nuevo proyecto` | Igual que 2.1 | ✅ | wizard CREATE_PROJECT desde idle |
| 2.3 | Responder nombre + objetivo | Wizard continúa → pregunta parámetros | ✅ | |
| 2.4 | Responder parámetros completos | Proyecto creado → cargado automáticamente | ✅ | |
| 2.5 | `cancelar` dentro del wizard | Wizard cerrado, sin proyecto creado | ✅ | |
| 2.6 | Crear proyecto aéreo (vehicle_type=dron) | Bridge automático → SYSTEM_DEFINITION | ✅ | |

---

## Bloque 3 — SYSTEM_DEFINITION wizard (aéreo)

| # | Input | Qué esperar | Estado | Notas |
|---|-------|-------------|--------|-------|
| 3.1 | Responder preguntas de arquitectura | Wizard secuencial | ✅ | Opción A → arquitectura base |
| 3.2 | Completar SYSTEM_DEFINITION | Bridge automático → DEFINE_MISSING_PARAMETERS si faltan params | ✅ | motors + per_motor_max_thrust_n |
| 3.3 | `cancelar` dentro de SYSTEM_DEFINITION | Wizard cerrado limpiamente | ✅ | Robot terrestre, cancel en selección A/B/C |

---

## Bloque 4 — project_status

| # | Input | Qué esperar | Estado | Notas |
|---|-------|-------------|--------|-------|
| 4.1 | `resumen` | Bloque estado proyecto (sin LLM) | ✅ | |
| 4.2 | `siguiente paso` | project_status + fase actualizada | ✅ | Bug 39 |
| 4.3 | `estado` | Igual que 4.1 | ✅ | Bug 53 cerrado — `r"\bestado\b"` en `STATUS_PATTERNS` |

---

## Bloque 5 — analyze (LLM)

| # | Input | Qué esperar | Estado | Notas |
|---|-------|-------------|--------|-------|
| 5.1 | `orientame` | Analyze LLM, sin prefijo | ✅ | Bug 47 |
| 5.2 | `ayudame` | Analyze LLM, sin prefijo | ✅ | Bug 47 |
| 5.3 | `dame opciones` | Analyze LLM, sin prefijo | ✅ | Bug 47 |
| 5.4 | `que deberia hacer` | Analyze LLM, sin prefijo | ✅ | Bug 47 |
| 5.5 | `como influye el material en el peso` | Analyze causal LLM + reasoning | ✅ | |
| 5.6 | Analyze dentro del wizard (Bug 7) | Status mostrado, wizard retoma | ✅ | Bug 7 |

---

## Bloque 6 — iterate wizard

| # | Input | Qué esperar | Estado | Notas |
|---|-------|-------------|--------|-------|
| 6.1 | `reduce el peso` | Wizard abierto | ✅ | |
| 6.2 | `itera` | Wizard directo con confirmación objetivo | ✅ | Bug 29 |
| 6.3 | `augmentar el peso` (typo) | Normalizado → wizard | ✅ | Bug 46 |
| 6.4 | Variable `material` → fibra de carbono | Ruta física, recalcula masa | ✅ | |
| 6.5 | Variable `estructura` → cambio declarativo | Ruta declarativa, sin recalcular | ✅ | |
| 6.6 | Variable `motores` + valor numérico | Ruta física, recalcula empuje | ✅ | Param ingestion + wizard (Bug 50 flow) |
| 6.7 | Variable `autonomía` | Redirect a batería/consumo | ✅ | Bug 5 OK |
| 6.8 | Variable `empuje` | Redirect a motors/torque (Bug 50) | ✅ | Bug 50 cerrado — `"empuje"` en `PARAMETER_REQUIREMENTS` con `is_derived=True`, redirige a motors/per_actuator_torque_nm |
| 6.9 | `cancelar` dentro wizard | Salida limpia a idle | ✅ | |
| 6.10 | project_status dentro wizard | Status mostrado, wizard retoma (sin reprompt) | ✅ | Bug 51 — sin reprompt |
| 6.11 | Flujo completo hasta confirmación | Iteración ejecutada, valores actualizados | ✅ | |

---

## Bloque 7 — calculate / simulate

| # | Input | Qué esperar | Estado | Notas |
|---|-------|-------------|--------|-------|
| 7.1 | `calcula` | Cálculo sin LLM, valores numéricos | ✅ | |
| 7.2 | `simula` | Simulación + safety_margin + sugerencias | ✅ | |
| 7.3 | `simula` con status=pass | Sin `high_actuator_load` warning | ✅ | Bug 48 |
| 7.4 | `simula` con quality=good (margen alto) | Sugerencias de aprovechar margen | ✅ | motors=4, safety_margin=2.83 |
| 7.5 | `simula` con parámetros faltantes | Error claro + qué falta | ✅ | params de energía no bloquean simulación física — se mencionan en reasoning |

---

## Bloque 8 — DEFINE_MISSING_PARAMETERS

| # | Input | Qué esperar | Estado | Notas |
|---|-------|-------------|--------|-------|
| 8.1 | `configurar helices` | Wizard secuencial: diámetro → rpm | ✅ | |
| 8.2 | `definir bateria` | Si ya definida: "No hay parámetros pendientes" | ✅ | |
| 8.3 | Flujo completo (2 params) → recalculo | Parámetros aplicados + nueva simulación | ✅ | |
| 8.4 | `cancelar` dentro del wizard | Salida limpia | ✅ | verificado múltiples veces en sesión |

---

## Bloque 9 — Rutas del motor de cálculo

| # | Escenario | Qué esperar | Estado | Notas |
|---|-----------|-------------|--------|-------|
| 9.1 | Torque → empuje (`per_actuator_torque_nm`) | `empuje_disponible` calculado | ✅ | Ruta principal |
| 9.2 | Hélice pura (`propeller_diameter_in` + `propeller_rpm`) | `calculate_thrust_from_propeller` activo | ✅ | Validado 15 julio 2026 (Fase N, vía MCP). Proyecto sin `per_motor_max_thrust_n`; empuje=38.24N desde 10"×7500rpm×4 motores (Ct=0.12). Reasoning confirma "empuje estimado desde hélice". |
| 9.3 | Fuerza directa (`per_motor_max_thrust_n`) | Bypass torque/hélice | ✅ | motors=4, per_motor_max_thrust_n=20 → empuje=80N |
| 9.4 | Aéreo sin empuje → `missing_propulsion_parameters` | Warning + solicitud proactiva | ✅ | Cubierto por `test_propeller_pipeline.py` (27 tests automáticos). Flujo CLI validado Fase N: el sistema pide proactivamente `propeller_diameter_in` y `propeller_rpm` cuando no hay thrust ni hélices. |
| 9.5 | Terrestre (torque + wheel + gear) | `traction_force_from_torque` | ✅ | trigger: `definir motores` (no `configurar transmision` — E1) |
| 9.6 | Terrestre sin transmisión completa | `missing_transmission_parameters` | ✅ | E1 — `configurar motor`/`definir transmision`/`parametros de torque` → wizard con pending=[per_actuator_torque_nm, motors, wheel_radius_m, gear_ratio]. Guard numérico OK. |

---

## Bloque 10 — Param ingestion (fuera del wizard)

| # | Input | Qué esperar | Estado | Notas |
|---|-------|-------------|--------|-------|
| 10.1 | `aumenta los motores a 6` | motors=6 aplicado, recalculo | ✅ | |
| 10.2 | `payload 4kg` | payload_kg=4 aplicado, recalculo | ✅ | |
| 10.3 | `cambia a 8 motores` | motors=8 aplicado, recalculo | ✅ | |

---

## Bloque 11 — Sugerencias y Bug 49

| # | Input | Qué esperar | Estado | Notas |
|---|-------|-------------|--------|-------|
| 11.1 | `simula` → ver bloque Sugerencias | Sugerencia listada correctamente | ✅ | |
| 11.2 | `esta sugerencia no aplica` | Intent dismiss_suggestion (Bug 49) | ✅ | Bug 49 cerrado — `DISMISS_SUGGESTION_PATTERNS` cubre esta frase |
| 11.3 | `siguiente sugerencia` | Intent dismiss_suggestion | ✅ | Bug 49 — intent=dismiss_suggestion. dismiss_noop=True cuando no hay sugerencia activa. |
| 11.4 | `ignora eso` | Intent dismiss_suggestion | ✅ | Bug 49 — intent=dismiss_suggestion confirmado. |

---

## Bloque 12 — Fallbacks y edge cases

| # | Input | Qué esperar | Estado | Notas |
|---|-------|-------------|--------|-------|
| 12.1 | `xkcd` (input sin sentido) | Analyze/LLM graceful, NO wizard | ✅ | Bug 52 cerrado — intent=unknown + LLM alucina iterate → redirige a analyze. Wizard nunca abre. |
| 12.2 | Input muy largo (>200 chars) | Sin crash | ✅ | analyze con respuesta técnica coherente |
| 12.3 | `siguiente pasosiguiente paso` (concatenado) | LLM fallback (no crash) | ✅ | No es bug |
| 12.4 | Input solo con números (`42`) | Sin crash, comportamiento razonable | ✅ | "No se pudo interpretar la intención" |

---

## Resumen de cobertura

| Bloque | Total | ✅ | ⚠️ | ❌ | ⬜ |
|--------|-------|----|----|----|----|
| 0 — Arranque | 8 | 3 | 0 | 0 | 5 |
| 1 — Globales | 5 | 5 | 0 | 0 | 0 |
| 2 — CREATE_PROJECT | 6 | 5 | 0 | 0 | 1 |
| 3 — SYSTEM_DEFINITION | 3 | 3 | 0 | 0 | 0 |
| 4 — project_status | 3 | 3 | 0 | 0 | 0 |
| 5 — analyze | 6 | 6 | 0 | 0 | 0 |
| 6 — iterate wizard | 11 | 11 | 0 | 0 | 0 |
| 7 — calculate/simulate | 5 | 4 | 0 | 0 | 1 |
| 8 — DEFINE_MISSING | 4 | 3 | 0 | 0 | 1 |
| 9 — Motor de cálculo | 6 | 6 | 0 | 0 | 0 |
| 10 — Param ingestion | 3 | 3 | 0 | 0 | 0 |
| 11 — Sugerencias | 4 | 4 | 0 | 0 | 0 |
| 12 — Edge cases | 4 | 4 | 0 | 0 | 0 |
| **Total** | **68** | **60** | **0** | **0** | **8** |

---

## Bugs descubiertos en testing

| Bug | Descripción | Estado |
|-----|-------------|--------|
| Bug 50 | Variable `empuje` sin redirección en wizard | ✅ Cerrado — 21 abril 2026 |
| Bug 51 | Sin reprompt del wizard tras interrupción inline | ✅ Cerrado — 21 abril 2026 |
| Bug 52 | LLM fallback interpreta input sin sentido como `iterate` | ✅ Cerrado — 21 abril 2026 |
| Bug 53 | `estado` suelto no resuelto como `project_status` | ✅ Cerrado — 21 abril 2026 |
| Bug 54 | Respuesta `si` al prompt proactivo de `resumen` no abre wizard | ✅ Cerrado — 21 abril 2026 |
| Bug 56 | Comandos globales (`simula`, `calcula`…) dentro de `DEFINE_MISSING_PARAMETERS` fallan con error numérico | ✅ Cerrado — 21 abril 2026 |
| Bug 76 | Vehicle type con descripción larga (`"dron de inspección"`) no activa arquitectura base de dron | ⬜ Pendiente — Fase N |
| Bug 77 | Wizard `DEFINE_MISSING` sin escape suave para param saltable (`per_motor_max_thrust_n`) | ⬜ Pendiente — Fase N |
| Bug 78 | Doble declaración de motor: segundo write no preserva `motor_count` → reasoning muestra gap | ⬜ Pendiente — Fase N |
| Bug 79 | DSE apply no comprueba `max_weight_kg` — violación de restricción sin warning | ⬜ Pendiente — Fase N |

---

## Extensiones incompletas encontradas en testing

Funcionalidad correcta para el dominio original (aéreo) pero no extendida al dominio terrestre al añadir esa ruta.

| # | Descripción | Archivo | Estado |
|---|-------------|---------|--------|
| E1 | `DEFINE_PARAMS_PATTERNS` solo cubre keywords aéreas (`bateria`, `energia`, `helice`). Faltan: `transmision`, `motor`, `torque`, `rueda`, `traccion` | `core/intent_resolver.py` | ✅ Cerrado — 21 abril 2026. Guard numérico añadido: inputs con valor pasan a `iterate`. |
