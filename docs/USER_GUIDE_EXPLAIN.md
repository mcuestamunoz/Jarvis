# Guía de usuario — `jarvis explain`

> `jarvis explain` es un **comando de terminal**, no el chat de Continuity (`jarvis --chat`) y no un asistente de voz. Consulta notas del vault conceptual `ontology/` y te muestra la cita — nunca inventa masa, potencia, empuje ni autonomía de tu craft. Esta guía es una lista de comandos reales, no un resumen de arquitectura.
>
> Cada comando de aquí funciona tal cual está escrito. Si alguno deja de funcionar, es un bug de esta guía, repórtalo.

---

## 1. Qué es y qué no es

**Qué es:** una consulta puntual, determinista, a las notas **`solid`** (revisadas) del vault `ontology/` — física, electrónica y robótica de por qué funcionan las cosas (C-rate, IMU, magnetómetro, navegación, bancos de empuje, etc.).

**Qué no es:**

- **No es Continuity.** No abre proyecto, no lee ni escribe tu `ProjectState`, no decide nada del craft.
- **No es el LLM.** No hay llamada a Ollama/OpenAI/Anthropic en este camino — es lectura de archivo + formateo, nada más.
- **No es un buscador.** No hay embeddings, ranking ni coincidencia difusa. O encuentra la nota exacta (por `id`, nombre o un alias conocido), o te dice honestamente que no la encontró.
- **No inventa datos de catálogo.** Cuando una nota declara qué no inventa (`never_invents`: masa, potencia, empuje, autonomía), `explain` te lo recuerda explícitamente — esos números siguen viniendo de `library/`/Continuity, nunca de esta nota.

---

## 2. Consulta directa

```text
jarvis explain c-rate-de-bateria
jarvis explain c-rate
```

Ambos comandos devuelven la misma nota — el segundo usa un alias corto. Funciona igual en la terminal y **dentro de `jarvis --chat`** (desde A7 — ver §7): la misma línea, escrita como tu siguiente turno del chat, responde sin pasar por el LLM. Salida:

```text
C-rate de batería  (id: c-rate-de-bateria)
Fuente: ontology/03_Ingenieria/Electrónica/C-rate de batería/C-rate de batería.md

[DEFINICION]
...

[INTUICION]
...

Citas: cited — Battery University BU-402 (C-rate); BU-105 (defs); ...

Honestidad: esta explicación no inventa mass_g, power_w, thrust_gf, autonomy_min —
esos valores deben venir de catálogo/Continuity, nunca de esta nota.
```

Puedes usar tres formas de consulta, en este orden de prioridad:

1. el `id` exacto de la nota (p. ej. `imu`, `c-rate-de-bateria`);
2. el nombre exacto de la nota (p. ej. `C-rate de batería`);
3. un alias corto conocido (p. ej. `c-rate`, `gyro`, `nav`, `banco`).

Si ninguno coincide, `explain` no inventa una nota parecida — termina con un mensaje honesto y código de salida 1:

```text
No solid ontology note for: motor-brushless
 (hint: use the note's id, its exact nombre, or a known alias such as 'c-rate')
```

---

## 3. Ver qué hay disponible: `--list`

```text
jarvis explain --list
```

Imprime **todas** las notas `solid` del vault (por `id`) y **todos** los alias conocidos, con su nota destino. Es la forma más rápida de descubrir qué puedes consultar sin adivinar nombres.

---

## 4. Consultar por rung/HD: `--rung`

```text
jarvis explain --rung C7
jarvis explain --rung HD-005
```

Algunas claves de producto (`C3`, `C7`, `C10`, `C39`, `C42` del flight software; `HD-001`, `HD-005` de Hardware Debt) tienen un pequeño mapa fijo hacia las notas del vault que las explican. `--rung` imprime esas notas (id + nombre) — **no** vuelca `[DEFINICION]`/`[INTUICION]` completas, para que la respuesta siga siendo escaneable. Para leer la nota completa, usa la consulta directa (§2) con el `id` que te muestre.

```text
$ jarvis explain --rung HD-005
HD-005 ->
  forma-medicion-banco-empuje  (Forma de medición en banco de empuje)
  punto-de-operacion-vs-capacidad-intrinseca  (Punto de operación vs capacidad intrínseca)
  motor-dc  (Motor DC)
```

Una clave desconocida (`--rung C999`) termina igual de honesto: sin mapear, código de salida 1, nunca una nota inventada.

`--list`, `--rung KEY` y la consulta directa son **mutuamente excluyentes** — no se pueden combinar en una sola llamada.

---

## 5. Honestidad — lo que `explain` nunca hace

- Nunca completa `mass_g`, `power_w`, `thrust_gf` ni `autonomy_min` por su cuenta, aunque la nota los mencione conceptualmente — esos son siempre del catálogo (`library/`) o de Continuity.
- Nunca confirma que un sensor/sistema simulado (por ejemplo C37 magnetómetro sim, C39 posición) sea equivalente a hardware validado en vuelo — cuando la nota lo advierte, `explain` lo imprime tal cual, no lo suaviza.
- Nunca cierra un hueco de Hardware Debt (HD-004/HD-005) inventando una curva o un punto de operación — te dice qué notas explican el hueco, no te da el dato que falta.

---

## 6. Cheatsheet — una página de comandos

```text
# Consulta directa (id / nombre / alias)
jarvis explain c-rate-de-bateria
jarvis explain c-rate
jarvis explain imu
jarvis explain gyro
jarvis explain nav

# Descubrir qué hay
jarvis explain --list

# Puentes producto → vault
jarvis explain --rung C7
jarvis explain --rung C39
jarvis explain --rung HD-001
jarvis explain --rung HD-005
```

---

## 7. Conceptos en `estado` / Continuity (R3, extendido por A8)

Cuando estás en el chat de Continuity (`jarvis --chat`) y escribes `estado`, a veces verás un bloque opcional al final del resumen del proyecto:

```text
Siguiente paso: Declara empuje real por motor (≥ 4.8 N) o elige una pieza
   fuera de catálogo; Jarvis no inventará un SKU.
   Por qué: Necesitas empuje ≥ 4.8 N/motor; no tengo motor en catálogo. ...
Conceptos (ontology) — puedes escribirlo aquí mismo:
  - motores  →  jarvis explain motores
  - motor-dc  →  jarvis explain motor-dc
```

Estas líneas **no son parte de la decisión de Continuity** — son un garnish opcional. Continuity sigue decidiendo `situation`/`next_useful_step`/`next_useful_why` exactamente igual que antes; solo añade una etiqueta interna (`explain_topics`, un puñado de valores fijos como `motor`, `c_rate`, `operating_point`) cuando el paso que ya iba a mostrar toca un concepto con nota `solid` en el vault. Continuity **nunca lee `ontology/`** para decidir el paso — solo emite la etiqueta; la CLI es quien resuelve la etiqueta a una cita, con la misma función que usa `jarvis explain`.

Si no ves el bloque "Conceptos", es porque no hay ningún concepto sembrado relacionado con el paso actual — no es un error, y no bloquea nada.

**El bloque nunca muestra `[DEFINICION]`/`[INTUICION]` completas.** Solo el `id` y el comando exacto para leer la nota entera. Para el texto completo, siempre usa `jarvis explain <id>` (§2).

**Desde A7 (`B1-chat-explain-intercept`): puedes escribir ese comando ahí mismo, dentro del chat.** Escribe `jarvis explain motores` o simplemente `explain motores` como tu siguiente línea — Jarvis lo reconoce **antes** de llamar al modelo de lenguaje local, así que responde al instante y no dispara una interpretación LLM (evita el colapso bajo carga local y el "No se pudo interpretar la instrucción" cuando lo que querías era leer una nota). Solo funciona con la consulta directa (id/nombre/alias); `--list`/`--rung` siguen siendo solo de terminal — si los escribes en el chat, Jarvis te lo dice y te redirige, sin llamar al LLM tampoco.

*Nota interna (T0, `B1-assistant-explain-task`): desde dentro, esa línea de chat pasa por el Assistant (`jarvis.intelligence.assistant_task`) como un `Task` explícito, no por un segundo camino de resolución dentro del orquestador — mismo resultado visible, arquitectura más honesta. No cambia nada de lo que escribes ni de lo que ves.*

*Nota interna (T1, `B1-assistant-defer-continuity`): ese mismo Assistant reconoce, por separado, un segundo `Task` — `defer_to_continuity` — para frases de estado ya existentes como `estado` o `resumen`; ese Task se cumple con la Continuity de siempre (`_handle_project_status`), no con `jarvis explain`. Si una línea es explicativa (`explain …`), esa lectura **siempre gana** sobre cualquier lectura de estado para la misma línea.*

*Nota interna (T6, `B1-assistant-vehicle-hold-task`): el mismo Assistant reconoce un tercer `Task` — `request_hold` — para frases como `hold` o `mantener`. No es una nota de `ontology/` ni un resumen de Continuity: es el primer Task **vehicle**, y la respuesta siempre es un rechazo honesto de Safety (nunca "vuelo mantenido") — ningún dron real está conectado. `explain …` y las frases de `estado` siguen ganando primero sobre esa misma línea, en ese orden.*

*Nota interna (T7, `B1-assistant-vehicle-land-task`): mismo patrón, un cuarto `Task` — `request_land` — para frases como `land` o `aterrizar`. Misma respuesta honesta (nunca "aterrizó"). Orden de precedencia: `explain …` → `estado` → `hold` → `land`.*

*Nota interna (T8, `B1-assistant-vehicle-go-to-task`): mismo patrón, un quinto `Task` — `request_go_to` — para frases como `go to`, `ve a` o `navega`. Sin parseo de coordenadas: la propuesta siempre viaja sin destino real. Misma respuesta honesta (nunca "navegando"/"llegó"). Orden de precedencia: `explain …` → `estado` → `hold` → `land` → `go to`.*

*Nota interna (T9, `B1-assistant-vehicle-takeoff-task`): mismo patrón, un sexto `Task` — `request_takeoff` — para frases como `takeoff`, `despega` o `sube`. Misma respuesta honesta (nunca "en el aire"/"despegó").*

*Nota interna (T10, `B1-assistant-vehicle-return-home-task`, ★ ACCEPT CLOSED @ `v0.6.18`): séptimo `Task` — `request_return_home` — para `rtl`, `casa`, `volver a casa`, etc. Exact match only (no "volver al board"). Precedencia: `explain …` → `estado` → `armar`/`desarmar` → `hold` → `land` → `go to` → `takeoff` → `rtl`/`casa`. Cierra el set de mando básico.*

*Nota interna (T11, `B1-assistant-vehicle-arm-ux`, package `0.6.19`): `armar` / `desarmar` armán o desarman el latch de Safety del chat (software ArmedAllowlist), no el ESC ni los motores. Tras `armar`, `hold`/`land`/`go to` pueden pasar a allow/not_implemented; `takeoff`/`rtl`/`follow`/`patrol` siguen verb_not_allowed. Exact match only (no "arma el frame").*

*Nota interna (T12, `B1-assistant-vehicle-follow-task`, package `0.6.20`): `follow` / `sígueme` / `ven conmigo` → Task `request_follow` por el ArmedAllowlist compartido. Exact match only (no "sigue con el frame"). Sin parseo de persona/target. Tras `armar` → verb_not_allowed.*

*Nota interna (T13, `B1-assistant-vehicle-patrol-task`, package `0.6.21`): `patrol` / `patrulla` / `iniciar patrulla` → Task `request_patrol` por el ArmedAllowlist compartido. Exact match only (no "patrulla del catalogo"). Sin parseo de waypoint/ruta. Tras `armar` → verb_not_allowed. Último `AutonomyVerb` sin Task en el chat — cierra la cola vehicle.*

**Desde A8 (`B1-continuity-explain-topics-expand`): también verás `corriente-y-circuitos` cuando el proyecto ya tenga un punto de operación eléctrico (`motor_op_current_a`) resuelto** — el mismo dato que la línea "OP eléctrico" de `estado` ya muestra. Ejemplo real:

```text
Siguiente paso: Diseño en PASS — puedes iterar, explorar alternativas o documentar el cierre.
   Por qué: No hay gaps bloqueantes en BOM/catálogo.
Conceptos (ontology) — puedes escribirlo aquí mismo:
  - corriente-y-circuitos  →  jarvis explain corriente-y-circuitos
```

Este topic **no** aparece solo porque haya un gap de energía genérico o un motor en recuperación de vatios — necesita ese dato eléctrico concreto ya presente. Si no lo ves, Continuity todavía no tiene esa evidencia — no es un error.

---

## 8. Límites conocidos

- Cobertura parcial: solo las notas `solid` del spine (lotes 1–5) y los aliases/mapas sembrados hasta ahora — una consulta legítima puede no tener aún alias corto; usa `--list` para ver el `id` exacto.
- `--rung` solo mapea las claves sembradas explícitamente (`C3`, `C7`, `C10`, `C39`, `C42`, `HD-001`, `HD-005`) — ampliar la cobertura es un IC futuro, no una búsqueda automática.
- No hay canal conversacional todavía — cada consulta es una llamada de terminal independiente, sin memoria entre llamadas (esto también aplica dentro de `--chat`: cada `explain <id>` es una llamada aislada, sin historial).
- El bloque "Conceptos" en `estado`/Continuity solo cubre 5 etiquetas sembradas (`c_rate`, `operating_point`, `motor`, `current`, `thrust_stand`) y solo se activa cuando una señal concreta de Continuity ya existente coincide — no es una búsqueda ni una sugerencia generada por LLM.
- El intercepto de chat (A7) reconoce solo el prefijo exacto `jarvis explain ` o `explain ` (con espacio). No reconoce una hélice ni un id de ontología escrito a secas, ni frases como "explícame" — sigue el mismo camino que antes (LLM/wizard). `explain --list`/`explain --rung <KEY>` dentro del chat solo dan un redirect honesto a terminal, nunca ejecutan la búsqueda ahí mismo.
