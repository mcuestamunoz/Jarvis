# Engineer note — Mes de software hasta banco (2026-09-26)

**Author:** Cursor (captura de evaluación del Engineer)  
**Orden del Engineer (reafirmado 2026-09-26):** **primero acabar el software de control de vuelo.** Assistant / voz / casa / placement DC = **después**, parked. Silicon parked ([bench note](engineer_note_fase_c_bench_before_silicon_2026_09_24.md)).

**Tip tagged:** **`v0.5.35`**. D2 docs LANDED @ package `0.5.36` (review PASS WITH NOTES; awaiting Engineer spot-check + ★ ACCEPT). Esta nota **no** es un IC y **no** autoriza código.

---

## Lock (process)

```text
D2 ACCEPT  →  C36…C43 flight-control software (one front at a time)
Assistant / placement DC / voz / casa  →  PARKED until C43 CLOSED
C30 DFU / DShot wire / USART on-chip / live gyro  →  parked until bench
```

- Un frente a la vez. Esta cola es **orden**, no un Buy único.
- Standoff perímetro (Taller) **no** bloquea el mes: visor-break cuando el Engineer quiera, no AHORA.
- `craft ↔ flight_software` sigue **cero import** hasta el IC C43.
- Verbos HOLD/LAND/GO_TO en sim **≠** volar **≠** Safety execute en cobre.

---

## Hueco previo a los lazos

Sin una **planta 6-DoF de juguete** (cuerpo rígido + cuatro fuerzas de `step()` → nueva IMU + posición), los lazos de yaw/altitud/posición y el ejecutor son números que nadie “siente”. Por eso **C36 = planta sim** es el primer Buy tras D2.

**Planta sim ≠ volar ≠ 6-DoF realista de viento.** Es un integrador determinista para tests.

---

## Cola — software de control de vuelo (Mac · sin soldar)

Tras D2 ★ ACCEPT. Un IC por fila. **Esto es el foco hasta C43.**

| # | ★ (nombre tentativo) | Qué demuestra | Sigue siendo imposible |
|---|---|---|---|
| **C36** | `B1-fase-c-sim-6dof-plant` | Fuerzas de `step()` → IMU + pose (x,y,z, quat) en RAM | Volar, viento, inercia citada del MY5 |
| **C37** | `B1-fase-c-mag-yaw-rung` | Mag **simulada** + yaw con referencia (fusionar C7) | Magnetómetro en la placa |
| **C38** | `B1-fase-c-altitude-loop` | Baro/ToF **sim** + lazo de z → collective | Baro vivo |
| **C39** | `B1-fase-c-position-loop` | GPS / flujo **sim** + lazo xy → tilt; GO_TO a un punto ENU | GPS vivo, mapa de casa |
| **C40** | `B1-fase-c-autonomy-executor` | HOLD/LAND/GO_TO **mandan consignas** a `step()` en el sim | Execute en cobre |
| **C41** | `B1-fase-c-safety-sim-policy` | Allowlist alineada a lo que C40 **sí** puede comandar en sim | Safety execute |
| **C42** | `B1-fase-c-icm-register-client` | Cliente datasheet ICM42688P sobre `ScriptedSpi` | Chip SPI1, gyro live |
| **C43** | `B1-fase-c-craft-fs-bind` | Perfil de *este* quad lee identidad craft | Continuity manda el firmware |

---

## Parked (no AHORA)

| Qué | Hasta cuándo |
|---|---|
| Assistant / [DC placement](design_contract_assistant_placement_b0.md) | Después de **C43 CLOSED** |
| C30 desk DFU · DShot *wire* · USART on-chip · gyro SPI1 live | Banco |
| Standoff perímetro | Visor-break, no bloquea C36+ |

---

## Residuals (no cola · Engineer 2026-09-26)

Tras C39 ★ ACCEPT @ `v0.5.40`, review N1–N4 **no** abren Buy ni deuda del mes:

| Origen | Clasificación | Acción |
|---|---|---|
| C39 N1 (`nan` setpoint) | Higiene opcional | No cola. Arreglo oportunista si se toca `PositionController` |
| C39 N2 (z droop bajo tilt) | Acople físico de juguete | **No deuda.** C40+ no prometen z clavada durante GO_TO/tilt |
| C39 N3/N4 | Cosmético | Ignorar |

---

## Hoy

Tip tagged **`v0.5.40`** (C39 CLOSED). Siguiente: IC **C40** autonomy executor. Assistant PARKED hasta C43.
