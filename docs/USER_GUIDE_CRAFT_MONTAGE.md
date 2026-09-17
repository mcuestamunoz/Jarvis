# Guía de usuario — Montaje de un craft en Jarvis

> **Para quién es esta guía:** el Engineer/power user que maneja Jarvis por **Continuity** (CLI de texto libre en español) y por el **Board** (visor 3D con Situar). No es una página de marketing ni un resumen de arquitectura — es una lista ordenada de **comandos reales** para llegar de un proyecto vacío (o a medias) hasta un craft **montado de forma honesta** en el Board.
>
> Cada frase de esta guía está tomada literalmente del código (parsers/regex de `src/jarvis/core/*_assist.py` y `orchestrator.py`) o de un smoke ya cerrado. Si una frase de aquí deja de funcionar, es un bug de esta guía — no una libertad de estilo.

---

## 1. Qué es esta guía / qué NO promete

**Monta:** llegar a un estado del Board donde: la placa principal es una caja (citada o `estimada`), el stack de aviónica (FC/ESC/batería/sensores, los que existan) está montado (`mounted_on`) y posado (`declared_box_pose`) respecto a esa placa, los motores/hélices aparecen en las estaciones del Visor X (o como cilindro si hay altura citada), y puedes preguntar `parece un dron` / `relaciones` y entender exactamente qué es honesto y qué no.

**NO promete:**

- **No es ASSEMBLY READY / ERF.** "Montaje honesto en Board" es un checklist de geometría declarada — no un cálculo de ingeniería completo del proyecto. `relaciones`/`fit` lo dice explícitamente en su propio pie de página.
- **No es CAD verificado.** Todo lo que ves en el Board es lo que se **declaró o citó** — nunca una medición física de Jarvis.
- **No es reconocimiento visual.** `parece un dron` es un checklist determinista sobre propiedades ya declaradas (caja de placa + stack posado/montado) — Jarvis nunca "mira" el Board y decide que parece un dron.
- **No inventa milímetros.** Ni de catálogo, ni de "typical class", ni de fotos. Cuando falta un dato, Jarvis te lo dice y te ofrece o bien citar (catálogo/medida real) o bien declarar una estimación **marcada como tal** (`estimated_temporary`).

Verás dos etiquetas todo el rato:

> 📐 **CITADO** — el número viene de una ficha de producto/catálogo, o lo mediste tú y lo declaraste como real (`source=declared`).
>
> 🟡 **ESTIMADO (temporal)** — un número provisional que TÚ elegiste porque todavía no tienes el dato real (`source=estimated_temporary`, confianza baja). Bloquea `cabe`/`declaro verificado` hasta que lo sustituyas.

---

## 2. Cómo arrancar

```text
jarvis --chat
```

Abre el CLI de texto libre. Si ya tienes proyectos, verás un menú:

```text
Proyectos existentes:
  1. mi-dron — objetivo…

Jarvis > ¿Qué quieres hacer?
  n  → crear nuevo proyecto
  1  → continuar con el proyecto más reciente
```

- Escribe **`n`** (o `nuevo`, `crear`) para empezar un proyecto nuevo, o el **número** de uno existente para continuarlo.
- Si no hay proyectos todavía, escribe directamente lo que quieres diseñar (por ejemplo `quiero diseñar un dron de carreras`) — esto abre el wizard de creación de proyecto (fuera del alcance de esta guía; responde sus preguntas de payload/restricciones/nivel de detalle y sigue).
- En paralelo, para ver el visor 3D:

```text
jarvis board
```

**En cualquier momento**, para orientarte sin abrir ningún wizard:

```text
estado
```
```text
resumen del proyecto
```

**Qué deberías ver:** un resumen de bloques declarados/pendientes del proyecto activo. Nunca muta nada.

---

## 2bis. Arquitectura de misión (cámara / radio)

Tras crear el proyecto, Jarvis ofrece arquitectura base (A/B/C). Para un craft de vigilancia (u otro con payload de misión):

```text
B
cámara
comunicación
listo
```

**Qué deberías ver:** bloques `perception` / `communication` **añadidos**. Tras `listo`, en `estado` aparecen stubs `cameras` y `radio_module`.

Bloques que **aún no** se pueden añadir (Jarvis se niega a propósito): `payload`, `brazo`, ruedas, gearbox — no hay regla de componente detrás.

### Declarar identidad (sin inventar mm/g)

```text
cámara RunCam
```
```text
radio ELRS
```

**Qué deberías ver:** `Cameras registrado` / `Radio module registrado`; en `estado`, filas declarativas con el modelo. Completeness **medium** cuando la marca/protocolo está en el mapa interno (RunCam, Caddx, Foxeer, GoPro, Insta360 · ELRS, Crossfire, FrSky). Solo `cámara` / `radio` sin marca → low + pista.

> 🟡 **No es catálogo físico.** No hay `library/cameras` ni masa/cotas citadas todavía — identidad de misión (“qué llevo”), no caja en Board ni acoplamiento a energía.

Ver también: montaje honesto del craft en las secciones siguientes (placa → stack → Situar).

---

## 3. Identidad + catálogo

Cada familia (motor, hélice, batería, ESC, frame, controladora/FC, GPS/sensor) se puede **elegir de catálogo** (identidad citada, con L×W×H cuando la ficha las trae) o declarar en texto libre (identidad sin caja, salvo excepciones).

### 3.1 Pedir opciones de catálogo

```text
ayúdame a elegir
```

Jarvis lista SKUs citados de la familia que toque en ese momento (motor, hélice, batería, frame, ESC, o controladora/GPS si preguntaste por esos). Responde con el número de la lista, o escribe el modelo a mano.

**Qué deberías ver:** una lista numerada con L×W×H cuando la ficha las trae (📐 CITADO).

### 3.2 Cambiar una familia ya declarada

```text
cambiar esc
```

Reabre la lista de esa familia para volver a elegir. Funciona hoy para: **frame, motores, hélices, batería, esc**.

> 🟡 **Trampa conocida:** `cambiar controladora` / `cambiar gps` **no** reabre nada todavía — la identidad de FC/GPS solo se cambia re-declarando el modelo en texto libre (ver §3.3) o mediante `ayúdame a elegir` cuando el flujo la ofrezca. Ver inventario, §10.1.

### 3.3 Declarar identidad a mano (FC / GPS / cámara / radio)

```text
Pixhawk 4
```
```text
SpeedyBee F405 V4
```
```text
Holybro M10
```
```text
cámara RunCam
```
```text
radio ELRS
```

**Qué deberías ver:** si el modelo tiene ficha citada (Pixhawk 4, SpeedyBee F405 V4, Holybro M10 hoy), la tarjeta ya trae L×W×H 📐 CITADO. Un modelo reconocido pero sin ficha (por ejemplo `Skystars F4 V4`) se declara igual, pero sin caja — identidad sola. Cámara/radio: solo identidad (marca/protocolo → medium); **sin** caja ni masa — ver §2bis.

### 3.4 Refrescar una vinculación existente

```text
actualiza el esc
```

Vuelve a proyectar los físicos del SKU ya vinculado desde el catálogo actual (útil si el catálogo cambió). Funciona para: **esc, motores, batería, frame, hélices**. No existe todavía para FC/GPS (mismo motivo que §3.2).

---

## 4. Placa principal (citada o estimada) + disclosure

La placa (`frame_plate`) es la **raíz de ensamblaje** del craft. Todo lo demás se posa "respecto a" ella.

### 4.1 Si tienes una medida real o una cita

```text
declara frame_plate 120 x 55 x 2 mm
```

📐 **CITADO** — `source=declared`.

### 4.2 Si todavía no la mides (kits sin ficha de placa suelta)

```text
declara frame_plate estimada 120 x 55 mm
```

🟡 **ESTIMADO (temporal)** — la altura, si la omites, se rellena con el `thickness_mm` ya citado del frame si existe; si no, indícala también (`... estimada 120 x 55 x 2 mm`).

**Qué deberías ver:** Continuity confirma con "Declarado (ESTIMATED_TEMPORARY): ... — Jarvis no valida 'cabe' ni 'declaro verificado' con estas medidas." El Board muestra la placa como caja igualmente — con el disclosure visible en sus campos.

---

## 5. Sobres L×W×H del resto del stack

Con la placa lista, completa cajas para FC/ESC/batería/sensores.

### 5.1 Ya citadas por catálogo

Si vinculaste batería/ESC/FC/GPS de catálogo (§3) y la ficha trae L×W×H, **ya tienen caja** — no hace falta nada más.

### 5.2 Declarar a mano (batería, sensores, conectores, brazo, adaptador…)

```text
declara la bateria 80 x 34 x 22 mm
```
```text
declara el sensor 40 x 40 x 12 mm
```

**Nunca** acepta `frame` raíz, `motores`, `ESC`, `FC` ni `hélices` como sujeto — esas familias solo consiguen caja por catálogo (o, para el ESC, por la ruta estimada de abajo).

Para quitar un sobre declarado:

```text
quita el sobre de la bateria
```

### 5.3 ESC sin altura citada (híbrido: L×W citadas + H estimada)

Si el ESC ya tiene L×W citadas de catálogo pero la ficha no trae altura (caso real: Skystars KO50A II):

```text
declara el esc estimado 8 mm
```

🟡 **ESTIMADO (temporal)** — solo la altura; L×W/masa/corriente siguen 📐 CITADAS del catálogo, sin tocar. Bloquea `cabe`/`declaro verificado` para el ESC hasta que sustituyas H por un dato real (medido o de una ficha futura).

---

## 6. Montajes (`mounted_on`)

### 6.1 Ver qué falta

```text
montajes estándar
```

**Qué deberías ver:** una lista numerada de los montajes todavía no declarados (hélices→motores, motor→brazo, aviónica→placa/frame) con la frase exacta para confirmarlos.

### 6.2 Declarar uno

```text
el esc montado en frame_plate
```
```text
hélices montadas en los motores
```

> 🟡 **Trampa (multi-placa):** si el proyecto tiene varias placas (`frame_plate`, `frame_plate_2`, … — caso real de `10-min-autonomía`), la frase genérica `… montado en la placa` responde **AMBIGUOUS** y no escribe. Usa la clave (`frame_plate`) o la etiqueta de la lista (`top plate`). `montajes estándar` te da la frase lista para pegar.

Para quitarlo:

```text
quita el montaje del esc
```

---

## 7. Poses: Path F, layout pack, Situar

Con el stack montado, coloca cada caja respecto a la placa.

### 7.1 Camino recomendado — checklist automático (Path F)

```text
apilar en placa
```

**Qué deberías ver:** una lista con la frase de pose exacta para cada subject con caja pendiente de posar, centrada y a ras (`z = mitad de la placa + mitad de la caja`). Copia y pega la frase que te interese; nada se declara solo.

### 7.2 Pack curado de un kit conocido

```text
layout pack
```
o, si hay más de un pack registrado:
```text
aplicar layout hglrc_my5_flush_stack_b1
```

Lista pose **y** montaje juntos para un kit con un pack ya definido (hoy: `hglrc_my5_flush_stack_b1`, el mismo frame HGLRC MY5 que usan los proyectos de smoke).

### 7.3 Declarar una pose a mano

```text
declara el esc a 0 mm en x, 0 mm en y, 5.0 mm en z respecto a frame_plate
```

(El `z` concreto lo da Path F / el estado vivo del proyecto — en `10-min-autonomía` hoy es **5.0** mm para el ESC Skystars H=8; no copies un `z` de otro kit.)

Puedes combinar varios ejes en una sola frase. Para quitar la pose:

```text
quita la pose del esc
```

### 7.4 Situar — ajuste fino en el Board (residual)

En el Board (`jarvis board`), activa el botón **"Situar"** (pasa a "Situar: ON"). Con Situar activo:

- **Click** en una caja → la selecciona.
- **Arrastra** (la caja o el fondo) → mueve la caja seleccionada en el plano de pantalla actual.
- **Shift + arrastre** → bloquea el movimiento al eje de profundidad (Y declarado).
- **Alt + arrastre** → orbita la cámara (no mueve nada).
- **"Recentrar 3D"** → vuelve a centrar la escena si te alejaste.
- Si la caja no tiene origen de pose todavía, aparece un selector **"Origen para X:"** con un botón **"Fijar origen"** en vez de arrancar el arrastre.

Situar escribe con el **mismo writer** que la frase de §7.3 — es una forma alternativa de dar la misma pose, nunca un camino paralelo con reglas distintas.

---

## 8. Motores/hélices en el Visor X

Este paso es **automático** — no hay frase que escribir. Si el frame ya tiene `configuration: quad_x` + `wheelbase_mm` citados, y `motors.motor_count` es un número entero entre 2 y 16, el Board ya coloca motores/hélices en las 4 estaciones del Visor X, y `frame_arm` (con `motor_count == 4`) se dibuja como diagonal hacia cada motor usando su propia longitud declarada.

Si el motor o la hélice tienen **además** una altura/espesor citados (`height_mm` de motor, `hub_thickness_mm` de hélice), el sólido se dibuja como **cilindro** con esa profundidad — no un disco plano — automáticamente, sin ningún comando adicional.

**Qué deberías ver:** 4 motores/hélices en cruz sobre el plano de la placa; cilindros con volumen si hay altura citada, discos planos si no.

---

## 9. Comprobar: `cabe`, `relaciones`, `declaro verificado`, `parece un dron`

### 9.1 Screening geométrico (nunca "verificado")

```text
cabe
```
```text
cabe el esc
```

**Qué deberías ver:** un texto de screening AABB — "los sobres se solapan" / "no se solapan" / "no se compara (ESTIMATED_TEMPORARY)" / etc. Nunca dice "cabe" en sentido afirmativo ni "VERIFIED".

### 9.2 Checklist de relaciones completo

```text
relaciones
```

**Qué deberías ver:** una lista de hasta 6 relaciones con pie *"esto no es ASSEMBLY READY…"*:

| Relación | Qué mira Jarvis hoy |
|---|---|
| FC / ESC / batería / sensores → `frame_plate` | Screening AABB de cajas + pose (bloqueado si placa/hijo es 🟡 estimado) |
| **motores → `frame_arm`** | **Alcance de estación** (L del brazo vs radio quad-X del wheelbase) — no es AABB de disco |
| hélices → motores | Sigue **n/a disco** (aún no hay regla de alcance/axial) |

Estados típicos: bloqueada · lista para declarar verificado (`→`) · ya declarada (`✓`) · n/a · alcance over/insufficient/estimated.

### 9.3 Firmar como verificado

Solo cuando la fila está **lista** (caja en solape, o motores en `station_reach_ok`):

```text
declaro verificado el esc
```
```text
declaro verificado el motor
```

Se **niega** si no hay screening OK — nunca en silencio. El sello es juicio del Engineer, no “Jarvis midió el ensamblaje”. Para quitarlo:

```text
quita la verificación
```

> 📐 / 🟡: dims de catálogo o declaradas son **aproximadas** hasta medida física; el sello no convierte un número estimado en cita.

### 9.4 ¿Parece un dron?

```text
parece un dron
```

**Qué deberías ver:** `racimo (A)` si falta la caja de placa o el stack no está montado/posado; `silueta estimada (B*)` si la placa (o algún hijo) es `estimated_temporary`; `silueta (B)` sin asterisco cuando todo lo anterior es 📐 citado.

---

## 10. Ejemplo completo, de principio a fin

Este es el recorrido real del proyecto de smoke `10-min-autonomía` (frame HGLRC MY5 5", motores iFlight XING-E Pro, hélices Gemfan Hurricane MCK 51466-3 V2, ESC Skystars KO50A II, batería Tattu 2300mAh 4S, controladora SpeedyBee F405 V4, GPS Holybro M10). No son nombres de ejemplo inventados — es exactamente lo que hay hoy en ese proyecto, verificable en `workspace/`.

```text
jarvis --chat
> continuar con 10-min-autonomía        # o "n" si empiezas de cero

ayúdame a elegir                         # motor → iFlight XING-E Pro 2207 2450KV
ayúdame a elegir                         # hélice → Gemfan Hurricane MCK 51466-3 V2
ayúdame a elegir                         # batería → Tattu 2300mAh 4S 75C XT60
ayúdame a elegir                         # ESC → Skystars KO50A II BLS
SpeedyBee F405 V4                        # controladora (identidad + caja citada)
Holybro M10                              # GPS (identidad + caja citada)

declara frame_plate estimada 120 x 55 mm # 🟡 kit sin ficha de placa suelta
declara el esc estimado 8 mm             # 🟡 Skystars sin H citada (L×W sí)

montajes estándar                        # lista lo que falta montar (usa esas frases)
el esc montado en frame_plate            # no "la placa" si hay varias placas
la controladora montada en frame_plate
la bateria montada en frame_plate
el sensor montado en frame_plate
hélices montadas en los motores
motor montado en el brazo

apilar en placa                          # checklist de poses centradas
declara el esc a 0 mm en x, 0 mm en y, 5.0 mm en z respecto a frame_plate
declara la controladora a 0 mm en x, 0 mm en y, 4.9 mm en z respecto a frame_plate
declara la bateria a 0 mm en x, 0 mm en y, 15.5 mm en z respecto a frame_plate
declara el sensor a 0 mm en x, 0 mm en y, 8.2 mm en z respecto a frame_plate

relaciones                               # stack placa bloqueado por estimated_dims (esperado);
                                         # motors→frame_arm puede estar → listo (alcance)
declaro verificado el motor              # si la fila motors está en alcance OK
parece un dron                           # → silueta estimada (B*)
```

**Qué deberías ver al final:** el Board muestra la placa, el stack completo montado y posado, motores/hélices en cruz sobre las 4 estaciones (motores como cilindro Ø28.5×H33.1, hélices como cilindro Ø~131.8×H6.8 de espesor de hub), y `parece un dron` responde `silueta estimada (B*)` — honesto sobre que la placa y el ESC llevan medidas 🟡 provisionales. El día que midas la placa real o llegue una ficha con la altura del Skystars, sustituye esos dos `declara ... estimad[ao] ...` por la medida real y el `*` desaparece.

## 11. Cheatsheet — una página de comandos

```text
# Arranque
jarvis --chat
jarvis board
estado

# Catálogo
ayúdame a elegir
cambiar esc                       # también: motor, helice, bateria, frame
actualiza el esc                  # también: motor, bateria, frame, helice

# Placa
declara frame_plate 120 x 55 x 2 mm            # citada
declara frame_plate estimada 120 x 55 mm       # estimada

# Sobres
declara la bateria 80 x 34 x 22 mm
declara el sensor 40 x 40 x 12 mm
declara el esc estimado 8 mm                   # solo si L×W ya citadas
quita el sobre de la bateria

# Montajes
montajes estándar
el esc montado en frame_plate
quita el montaje del esc

# Poses
apilar en placa
layout pack
declara el esc a 0 mm en x, 0 mm en y, 5.0 mm en z respecto a frame_plate
quita la pose del esc

# Comprobación
cabe
relaciones
declaro verificado el esc              # caja en solape
declaro verificado el motor            # alcance de estación OK
quita la verificación
parece un dron
```

---

## 12. Apéndice — energía/simulación y límites conocidos

### 12.1 Fuera del spine de montaje

`calcular` / `simular` recalculan la física del proyecto (energía, empuje, autonomía) — útiles en cualquier momento, pero orientados al Requirements/ERF del proyecto, no al montaje del Board. No se detallan aquí; pregunta `estado` para ver dónde está el proyecto.

### 12.2 Limitaciones conocidas (deuda con nombre, no bugs escondidos)

- **`B1-plate-box`** (medida/citada de placa "de verdad") sigue en **await bag** — usa la ruta estimada (§4.2); el stack FC/ESC/batería/sensores→placa sigue bloqueado para `declaro verificado` mientras la placa sea 🟡.
- **Path N** (motor/hélice como origen de pose) es **imposible por esquema** — HOLD; no reabrir.
- **`cambiar controladora` / `cambiar gps`** no reabren el picker todavía (§3.2) — deuda conocida.
- **`actualiza el fc` / `actualiza el gps`** no existen todavía, mismo motivo.
- **Rebind ESC** a un SKU sin un dato que el anterior sí tenía puede dejar ese dato viejo como `declared` — deuda `bind_esc_from_catalog`.
- **Motores → brazo:** sí hay **alcance de estación** + `declaro verificado el motor` (§9). **Hélices → motores** sigue n/a (Buy aparte). AABB `cabe` sigue siendo solo cajas.
- **`layout pack` (sin nombre)** solo funciona mientras exista exactamente un pack registrado.
- Dims de catálogo = **aproximadas** hasta medida física ([lock](../.jes/artifacts/engineer_note_geometry_approx_until_verified.md)).

---

*Fuente de verdad de esta guía: `.jes/artifacts/inventory_user_facing_commands_craft_montage_b0.md` (Phase 0, evidencia por fila). Si una frase de aquí deja de aparecer en ese inventario, esta guía está desactualizada — repórtalo.*
