# Deuda técnica dependiente de hardware

Registro vivo de **física que Jarvis no inventa**. Cada ítem necesita **T1** (curva del fabricante para ese SKU) o **T2** (banco instrumentado sobre el SKU o un sustituto **declarado**). No son bugs de software y **no bloquean** el resto de Jarvis.

**Cola:** HD-* **nunca** es 🔴 PRIORIDAD ACTUAL en `IMPLEMENTATION_TASKS.md`. Engineer (2026-09-03): no hay equipo, banco ni herramientas de laboratorio; no hay campaña T1/T2. Aparcar OPEN está bien. Los agentes **no** proponen HD-* como “siguiente” al cerrar un IC de producto.

**Dueño:** Engineer (laboratorio / datasheet), cuando exista. Los agentes no rellenan números.  
**Si algún día llegan datos:** apéndice JES → investigation delta → Engineer ★ **explícita** → Implementation Contract → campo sibling. **No** editar catálogo JSON ni `src/` hasta ese IC.  
**Estado permitido:** dejar un ítem OPEN. L1 permanece `hover_energy_autonomy_min` ≈ 1.32 min (Combo A).

**No es este registro:** visibilidad ESTIMATIVO en chat (Opción A) — **cerrada**, no lab.

---

## Cómo añadir un ítem

1. Asignar el siguiente id `HD-xxx`.
2. Nombrar SKU, magnitud que falta, T1 vs T2, y qué desbloquearía un IC.
3. Enlazar investigación / DAC.
4. Estado: `OPEN` | `DATOS EN MANO` | `CERRADO (IC)` | `WONT` (Engineer aparcado).

No añadir filas genéricas de “LiPo típico” o “η típica de ESC”.

---

## HD-001 — Derating C-rate de batería (M3)

| Campo | Valor |
|---|---|
| **Estado** | **OPEN** |
| **SKU** | `lipo_4s_1500mah` (CNHL Black Series, `1501004BK`) |
| **Falta** | Tabla `{C-rate → fracción de capacidad usable}` + cutoff + temperatura (o ambiente declarado) |
| **Por qué** | Hover Combo A ≈ **45 C** (`68 A / 1.5 Ah`). Los 22.2 Wh de placa no son energía usable a ese C. Mayor palanca que sigue compatible con `PHASE26_P_BATTERY_BOUNDARY`. |
| **T1** | Curva de descarga del fabricante para **esta pieza**. Búsqueda day-0 (2026-09-01): solo listings; pack a menudo marcado discontinued. |
| **T2** | Pack (o sustituto 4S ~1500 mAh ≥100 C **declarado**) + carga electrónica. **≥3** descargas a corriente constante: ~1 C, ~10–20 C, **~40–50 C**. Mismo cutoff en todas las filas. Log V, I, t → Ah (y Wh si se registra). Clase ~68 A / ~1 kW; riesgo de incendio LiPo — sin procedimiento improvisado. |
| **No cierra** | ESC `P_battery`, OCV/R/sag validado (V(t) puede ser *subproducto*, no el entregable M3) |
| **Complejidad** | Media. Solo batería — sin airframe. Más seguro que girar una hélice; sigue sin ser un trabajo de cargador hobby a 45 C. |
| **Desbloquea** | Campo sibling de energía usable (nombre en el IC). **No** relabela L1. |
| **Spec** | [data_acquisition_contract_phase27_m3_crate_derating.md](../.jes/artifacts/data_acquisition_contract_phase27_m3_crate_derating.md) |
| **Boundary** | `PHASE27_LOADED_BATTERY_BOUNDARY` (solo el slice M3) |

---

## HD-002 — Pérdida aislada de ESC (`P_motor_input` → `P_battery`)

| Campo | Valor |
|---|---|
| **Estado** | **OPEN** |
| **SKU** | `hobbywing_xrotor_40a_6s` |
| **Falta** | η sourced o `P_loss(I)` a **≥2** corrientes en el rango Combo A (~8–40 A) |
| **Por qué** | El catálogo tiene identidad / corriente / masa solamente. Página oficial: sin η numérica. Un paper η=96 % movería la autonomía Combo A **~−4 %** (1.32 → ~1.27 min). El “≥90 %” académico **no** es este SKU. |
| **T1** | Improbable (ya buscado). |
| **T2** | **ESC aislado** (p. ej. dos vatímetros): `P_pack` y `P_motor_input` en el mismo instante. **No** un blob de eficiencia motor+ESC de thrust-stand (Phase 2.6 rechazó esa clase). |
| **No cierra** | Wh usable de batería, sag, SKUs ESC extra (H5) |
| **Complejidad** | Mayor que HD-001: ESC + motor + doble medición de potencia; hélice girando o dummy load. |
| **Desbloquea** | Reabrir P26-D/E → campo sibling de energía de sistema. **No** relabela L1. |
| **Spec** | Gate H en [investigation_report_phase26_esc_system_losses.md](../.jes/artifacts/investigation_report_phase26_esc_system_losses.md) — DAC completo aún no redactado |
| **Boundary** | `PHASE26_P_BATTERY_BOUNDARY` |

---

## HD-003 — Sag / OCV / `R_internal` bajo carga (aparcado)

| Campo | Valor |
|---|---|
| **Estado** | **OPEN** (aparcado — **no** es la misma campaña que HD-001) |
| **SKU** | El mismo pack Combo A |
| **Falta** | T1/T2 OCV(SOC) y/o `R_internal` (o circuito equivalente) de **este** pack |
| **Por qué** | `V_loaded` / Wh usable validados bajo sag. L2 P27-B es **solo estimativo** (sweep del caller). |
| **Nota** | Un T2 de HD-001 bien logueado (`V(t)`, `I(t)`) puede *alimentar* un delta de sag posterior. No valida M1/M2 por sí solo. I2 (`I = P_motor / V`) sigue prohibido. |
| **Desbloquea** | Sibling de autonomía bajo carga tras investigation + ★ + IC |
| **Boundary** | `PHASE27_LOADED_BATTERY_BOUNDARY` |

---

## Más adelante (no abierto)

Validación de vuelo / vehículo completo. Necesita los ítems de arriba (o etiquetas honestas de que siguen faltando). No mezclar en HD-001/002.

---

## Después de una medición

```text
laboratorio o datasheet
  → apéndice en .jes/artifacts/ (markdown + números)
  → investigation delta (un id HD)
  → Engineer ★
  → Implementation Contract
  → campo sibling + provenance
```

**Prohibido:** T3/T4 en `library/` o en `calculate_autonomy_min`.
