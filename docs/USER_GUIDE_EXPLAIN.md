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

Ambos comandos devuelven la misma nota — el segundo usa un alias corto. Salida:

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

## 7. Límites conocidos

- Cobertura parcial: solo las notas `solid` del spine (lotes 1–5) y los aliases/mapas sembrados hasta ahora — una consulta legítima puede no tener aún alias corto; usa `--list` para ver el `id` exacto.
- `--rung` solo mapea las claves sembradas explícitamente (`C3`, `C7`, `C10`, `C39`, `C42`, `HD-001`, `HD-005`) — ampliar la cobertura es un IC futuro, no una búsqueda automática.
- No hay canal conversacional todavía — cada consulta es una llamada de terminal independiente, sin memoria entre llamadas.
