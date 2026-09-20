# Guía de usuario — Montaje de un craft en Jarvis

> Jarvis se maneja de dos formas a la vez: **Continuity**, el chat de texto libre en español, y el **Board**, el visor 3D. Esta guía es una lista ordenada de comandos reales para llevar un proyecto desde vacío hasta un craft **montado de forma honesta** en el Board — no es un resumen de arquitectura ni un histórico de cambios.
>
> Cada comando de aquí funciona tal cual está escrito. Si alguno deja de funcionar, es un bug de esta guía, repórtalo.

---

## 1. Qué hace esta guía / qué no promete

**Objetivo:** llegar a un estado del Board donde la placa principal es una caja (citada o estimada), el stack de aviónica (FC, ESC, batería, sensores — los que tenga tu craft) está montado y colocado respecto a esa placa, los motores/hélices aparecen solos en sus estaciones, y puedes preguntar `parece un dron` o `relaciones` y saber exactamente qué es un dato real y qué es una aproximación.

**No promete:**

- **No es un cálculo de ingeniería completo.** "Montaje honesto en el Board" es un checklist de geometría declarada, no una validación estructural del proyecto.
- **No es CAD verificado.** Todo lo que ves en el Board es lo que tú **declaraste o citaste** — Jarvis nunca mide nada por su cuenta.
- **No reconoce nada visualmente.** `parece un dron` es un checklist sobre propiedades ya declaradas, no un vistazo al Board.
- **No inventa medidas.** Ni de catálogo, ni "típicas de esta clase", ni de fotos. Si falta un dato, Jarvis te lo dice y te deja elegir: citarlo (catálogo o medida real) o declarar una estimación **marcada como tal**.

Verás dos etiquetas todo el rato:

> 📐 **CITADO** — el número viene de una ficha de producto/catálogo, o lo mediste tú (`source=declared`).
>
> 🟡 **ESTIMADO (temporal)** — un número provisional que elegiste porque aún no tienes el dato real. Bloquea la verificación final hasta que lo sustituyas por uno real.

---

## 2. Cómo arrancar

```text
jarvis --chat
```

Abre el chat de texto libre. Si ya tienes proyectos, verás un menú:

```text
Proyectos existentes:
  1. mi-dron — objetivo…

Jarvis > ¿Qué quieres hacer?
  n  → crear nuevo proyecto
  1  → continuar con el proyecto más reciente
```

- Escribe **`n`** (o `nuevo`, `crear`) para empezar de cero, o el **número** de un proyecto existente para continuarlo.
- Si no hay proyectos todavía, escribe directamente lo que quieres diseñar (por ejemplo `quiero diseñar un dron de carreras`) — esto abre el asistente de creación de proyecto: responde sus preguntas de payload/restricciones/nivel de detalle y sigue.
- En paralelo, para ver el visor 3D:

```text
jarvis board
```

**En cualquier momento**, para orientarte sin activar ningún asistente:

```text
estado
```

**Qué deberías ver:** un resumen de bloques declarados/pendientes del proyecto activo. Nunca cambia nada por sí solo.

---

## 3. Arquitectura de misión (cámara / radio / VTX)

Al crear el proyecto, Jarvis ofrece una arquitectura base. Para un craft con payload de misión (vigilancia, FPV, telemetría…), añade los bloques que necesites:

```text
cámara
comunicación
vtx
listo
```

**Qué deberías ver:** bloques `perception` / `communication` / `video_link` añadidos. Tras `listo`, en `estado` aparecen stubs `cameras`, `radio_module` y `vtx`.

> 🟡 **VTX ≠ radio.** El radio (ELRS/Crossfire) es el enlace de **control** del craft; el VTX es el enlace de **vídeo** de la cámara FPV — son componentes separados, nunca el mismo. Si tu craft lleva cámara FPV, casi seguro necesitas nombrar también un VTX, aunque todavía no lo compres.

También puedes añadir `payload` (bahía de carga), `manipulación` (brazo manipulador), `actuación` (ruedas) y `transmisión` (gearbox) — de momento solo como identidad (sin catálogo, sin mm/g/W ni ratios como física real: un ratio de gearbox como "5:1" se guarda como texto).

### 3.1 Declarar identidad (sin inventar medidas)

```text
cámara RunCam
```
```text
radio ELRS
```
```text
vtx HGLRC
```

**Qué deberías ver:** confirmación de registro; en `estado`, una fila con el modelo. Completeness **medium** cuando la marca/protocolo está reconocida (cámara: RunCam, Caddx, Foxeer, GoPro, Insta360 · radio: ELRS, Crossfire, FrSky · VTX: HGLRC). Solo `cámara` / `radio` / `vtx` sin marca → low, con una pista de qué falta.

> 🟡 Esto es identidad libre, sin caja en el Board. Para caja citada + masa de catálogo, ver la sección de catálogo (§4) — hay al menos un SKU real de catálogo para cámara (RunCam Phoenix 2) y para VTX (HGLRC Zeus 800).

### 3.2 Declarar masa de misión

Una vez declarada la identidad, puedes declarar su masa — la tuya o la de ficha, nunca inventada por Jarvis:

```text
cámara 28 g
```
```text
radio 3 g
```
```text
vtx 4.8 g
```

**Qué deberías ver:** confirmación con la masa de misión total en gramos y kg. Los gramos declarados **suman** al peso total del proyecto junto a `payload_kg`, batería y motores — nunca sustituyen `payload_kg`. Si `payload_kg` ya contaba esos mismos gramos, Jarvis avisa (no bloquea) para que reduzcas `payload_kg` a mano.

Sin identidad declarada primero, la masa se rechaza honestamente — Jarvis no crea la cámara/radio/VTX solo porque le diste un peso.

`estado` guía el siguiente hueco: identidad → masa → montaje → (si falta) autonomía objetivo → **potencia** de cámara/radio (declarada o catálogo Phoenix 1 W) → **VTX** (si hay cámara y aún no hay VTX) → revisar margen vs carga de misión.

### 3.3 Montar cámara/radio + autonomía objetivo

Con la identidad y la masa ya declaradas, Jarvis pide el montaje de la cámara/radio sobre la placa/frame — mismo mecanismo de §7, ahora también para carga de misión:

```text
cámara montada en la placa
```
```text
radio montado en el frame
```

> 🟡 Si hay **varias placas** declaradas, la frase genérica responde AMBIGUO — usa `montajes estándar` para ver la clave exacta.

Con los montajes resueltos, puede pedirse además una **autonomía objetivo** en minutos. No es un campo nuevo: se extrae del texto libre de `restricciones` cuando incluye algo parseable como "N min":

```text
restricciones: 8 min
```
```text
vuelo mínimo 8 min
```

**Qué deberías ver:** con montajes hechos y la autonomía objetivo presente, Jarvis pide la potencia de cámara/radio (ver abajo) antes de pasar a "revisar margen vs carga de misión" — o, si la autonomía calculada no llega al objetivo, el aviso honesto de margen ya existente. Nunca un vuelo "validado" inventado.

### 3.4 Declarar potencia de misión (consumo de cámara/radio)

Si declaras los vatios que consume la cámara o el radio, Jarvis los suma al consumo del modelo energético — la autonomía se recalcula con honestidad, sin inventar ficha ni certificar el vuelo:

```text
cámara 1 W
```
```text
radio 0.5 W
```

**Qué deberías ver:** confirmación con la potencia de misión total en vatios; la autonomía calculada (`calcular`/`simular`) baja en consecuencia — nunca sube. Sin identidad declarada primero, la potencia se rechaza honestamente, igual que la masa.

> 🟡 Jarvis nunca convierte una cita de corriente por su cuenta en tiempo real — esa aritmética solo existe cuando el propio Engineer ya la fijó como un campo `power_w` del catálogo (ver la RunCam Phoenix 2 en §4: 1 W calculado de su `200mA@5V` citado, verificado también contra `85mA@12V`). Cualquier otra cámara/marca sin ese campo se queda como texto de referencia hasta que tú declares el número. `estado` sigue guiando el siguiente hueco de la escalera: identidad → masa → montaje → autonomía objetivo → **potencia** → **VTX** → revisar margen vs carga de misión.

### 3.5 VTX: solo identidad + masa (nunca vatios desde mW de RF)

El VTX (enlace de vídeo) se declara y cataloga igual que la cámara — pero **no** tiene declaración de potencia en esta versión:

```text
vtx HGLRC
```
```text
vtx 4.8 g
```

**Qué deberías ver:** identidad + masa como con cámara/radio; la masa entra en el AUW igual que la de cámara/radio.

> 🟡 **RF mW ≠ consumo DC.** La ficha de un VTX cita su potencia de **radiofrecuencia** en milivatios (p. ej. "800 mW" del HGLRC Zeus 800) — eso describe la señal que emite la antena, no el consumo eléctrico real del circuito, que necesitaría un dato de corriente (mA) que la ficha no siempre da. Jarvis nunca convierte esos mW en vatios del modelo energético; no hay comando `vtx N W` todavía. Si más adelante hay un dato de corriente citado, esto podría añadirse en una versión futura.

---

## 4. Identidad + catálogo

Cada familia — motor, hélice, batería, ESC, frame, controladora (FC), GPS/sensor, cámara, VTX — se puede **elegir de catálogo** (identidad citada, con L×W×H y a veces masa/potencia) o declarar en **texto libre** (identidad sin caja).

### 4.1 Pedir opciones de catálogo

```text
ayúdame a elegir
```

Jarvis lista los SKUs citados de la familia que toque en ese momento. Si quieres una familia concreta, nómbrala:

```text
ayúdame a elegir cámara
```
```text
ayúdame a elegir vtx
```

Responde con el número de la lista, o escribe el modelo a mano.

**Qué deberías ver:** una lista numerada con L×W×H (y masa/potencia cuando aplica) para cada opción con ficha citada. La RunCam Phoenix 2, por ejemplo, trae 19×19×19 mm, 9 g y 1 W — ese vatiaje ya entra directo en el consumo de misión al elegirla, sin declararlo a mano. El HGLRC Zeus 800 trae 37×37×5 mm y 4.8 g (sin potencia — ver §3.5).

### 4.2 Cambiar una familia ya declarada

```text
cambiar esc
```
```text
cambiar cámara
```
```text
cambiar vtx
```

Reabre la lista de esa familia para volver a elegir. Funciona para las nueve familias catalogadas: **frame, motores, hélices, batería, ESC, controladora, GPS/sensor, cámara, VTX**.

### 4.3 Actualizar una vinculación existente

Un componente ya vinculado a catálogo puede volver a proyectar sus físicos desde la ficha actual, sin reelegir — útil si el catálogo cambió:

```text
actualiza el esc
```
```text
actualiza la cámara
```
```text
actualiza el vtx
```

Funciona para las mismas nueve familias. Si el componente todavía no está vinculado a catálogo (solo texto libre), Jarvis lo dice sin inventar nada que actualizar.

### 4.4 Declarar identidad a mano

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
```text
vtx HGLRC
```

**Qué deberías ver:** si el modelo tiene ficha citada, la tarjeta ya trae L×W×H (y masa/potencia, para cámara; L×W×H y masa, para VTX) 📐 CITADO. Un modelo reconocido pero sin ficha se declara igual, pero sin caja — solo identidad. Cámara/radio/VTX en texto libre: solo identidad (marca/protocolo → medium), sin caja, masa ni potencia — para eso, usa el catálogo (§4.1).

---

## 5. Placa principal (citada o estimada)

La placa (`frame_plate`) es la **raíz de ensamblaje** del craft. Todo lo demás se posa "respecto a" ella.

### 5.1 Si tienes una medida real o una cita

```text
declara frame_plate 120 x 55 x 2 mm
```

📐 CITADO — dato real.

### 5.2 Si todavía no la mides (kits sin ficha de placa suelta)

```text
declara frame_plate estimada 120 x 55 mm
```

🟡 ESTIMADO (temporal) — la altura, si la omites, se rellena con el grosor ya citado del frame si existe; si no, indícala también (`... estimada 120 x 55 x 2 mm`).

**Qué deberías ver:** Jarvis confirma que quedó como estimación temporal y que no valida "cabe" ni "declaro verificado" con estas medidas. El Board muestra la placa igualmente, con el aviso visible.

---

## 6. Cajas del resto del stack

Con la placa lista, completa cajas para FC/ESC/batería/sensores.

### 6.1 Ya citadas por catálogo

Si vinculaste batería/ESC/FC/GPS/cámara de catálogo (§4) y la ficha trae L×W×H, ya tienen caja — no hace falta nada más.

### 6.2 Declarar a mano (batería, sensores, conectores, brazo, adaptador…)

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

### 6.3 ESC sin altura citada (L×W citadas + H estimada)

Si el ESC ya tiene L×W citadas de catálogo pero la ficha no trae altura:

```text
declara el esc estimado 8 mm
```

🟡 ESTIMADO (temporal) — solo la altura; L×W/masa/corriente siguen citadas del catálogo, sin tocar. Bloquea la verificación del ESC hasta que sustituyas la altura por un dato real.

---

## 7. Montajes (`mounted_on`)

### 7.1 Ver qué falta

```text
montajes estándar
```

**Qué deberías ver:** una lista numerada de los montajes todavía no declarados (hélices→motores, motor→brazo, aviónica→placa/frame) con la frase exacta para confirmarlos.

### 7.2 Declarar uno

```text
el esc montado en frame_plate
```
```text
hélices montadas en los motores
```

> 🟡 **Ojo con varias placas:** si el proyecto tiene más de una placa (`frame_plate`, `frame_plate_2`, …), la frase genérica "montado en la placa" responde AMBIGUO y no escribe nada. Usa la clave exacta o la etiqueta de la lista. `montajes estándar` te da la frase lista para copiar.

Para quitarlo:

```text
quita el montaje del esc
```

---

## 8. Poses: colocar cada caja en el espacio

Con el stack montado, coloca cada caja respecto a la placa.

### 8.1 Camino recomendado — checklist automático

```text
apilar en placa
```

**Qué deberías ver:** una lista con la frase de pose exacta para cada componente con caja pendiente de posar, centrada y a ras de la placa. Copia y pega la que te interese; nada se declara solo.

### 8.2 Pack curado de un kit conocido

```text
layout pack
```

o, si hay más de un pack registrado:

```text
aplicar layout hglrc_my5_flush_stack_b1
```

Aplica pose **y** montaje juntos para un kit con un pack ya definido (hoy: el frame HGLRC MY5).

### 8.3 Declarar una pose a mano

```text
declara el esc a 0 mm en x, 0 mm en y, 5.0 mm en z respecto a frame_plate
```

Puedes combinar varios ejes en una sola frase. Para quitar la pose:

```text
quita la pose del esc
```

### 8.4 El Board: Taller 3D, inspector y ajuste fino

Al abrir `jarvis board`, el Board arranca en la pestaña **Taller 3D**: el craft en 3D ocupa la pantalla, no una pared de tarjetas. La pestaña **Grafo** (arriba, junto a "Taller 3D") sigue disponible con las tarjetas de siempre — útil para ver todos los campos de golpe o los bordes de montaje entre piezas — pero ya no es lo primero que ves al abrir.

**Seleccionar una pieza:** haz click sobre una pieza en el 3D, o usa la tira de chips (una fila de botones con el id de cada pieza) que aparece siempre en el Taller — útil cuando dos piezas están apiladas y hacer click exacto es difícil.

**Inspector (columna derecha, Situar apagado):** al seleccionar, aparece un panel con:

- **Resumen** de la pieza: nombre, tipo, y unos pocos campos clave (montado en, masa, SKU…). Botón **"Ver todo"** para desplegar la ficha completa, igual de detallada que en Grafo.
- **Cadena hasta la placa** — la ruta de montaje declarada desde la pieza hasta la placa principal (`frame_plate`), un paso por vez (`esc → frame_plate`, `hélice → motor → brazo`…). Click en cualquier eslabón de la cadena para saltar a esa pieza. Si la pieza no tiene montaje declarado (o el montaje no llega hasta la placa), el panel lo dice honestamente en vez de inventar una ruta — nunca adivina por cercanía en el 3D.

Mientras hay una pieza seleccionada, el resto del craft se atenúa en el 3D (queda semitransparente) y la cadena seleccionada se ve a opacidad normal — así ubicas de un vistazo qué es la pieza y por dónde cuelga del chasis. Quita la selección (Escape, o click en el fondo) para recuperar la vista normal.

**Situar** (mismo botón de siempre) sigue para mover piezas a mano:

- **Click** en una caja → la selecciona.
- **Arrastra** (la caja o el fondo) → mueve la caja seleccionada en el plano de pantalla actual.
- **Shift + arrastre** → bloquea el movimiento al eje de profundidad.
- **Alt + arrastre** → orbita la cámara (no mueve nada).
- **"Recentrar 3D"** → vuelve a centrar la escena.
- Si la caja no tiene origen de pose todavía, aparece un selector de origen con un botón para fijarlo, en vez de arrancar el arrastre directamente.

Con Situar activo, el inspector se aparta — la tira de chips es la forma de elegir pieza mientras sitúas, para no competir por espacio con el 3D. Situar escribe con el mismo mecanismo que la frase de §8.3 — es solo una forma alternativa de dar la misma pose.

---

## 9. Motores/hélices en el visor

Este paso es **automático** — no hay frase que escribir. Si el frame ya tiene su configuración y separación entre motores citados, y el número de motores es válido (entre 2 y 16), el Board coloca motores/hélices solos en sus estaciones, y el brazo del frame se dibuja hacia cada motor usando su propia longitud declarada.

Si el motor o la hélice tienen además una altura/espesor citados, el sólido se dibuja como **cilindro** con esa profundidad — no un disco plano — automáticamente.

**Qué deberías ver:** los motores/hélices en cruz sobre el plano de la placa; cilindros con volumen si hay altura citada, discos planos si no.

---

## 10. Comprobar: `cabe`, `relaciones`, `declaro verificado`, `parece un dron`

### 10.1 Screening geométrico (nunca "verificado")

```text
cabe
```
```text
cabe el esc
```

**Qué deberías ver:** un texto de screening — "los sobres se solapan" / "no se solapan" / "no se compara (estimado)" / etc. Nunca dice "cabe" en sentido afirmativo ni "verificado".

### 10.2 Checklist de relaciones completo

```text
relaciones
```

**Qué deberías ver:** una lista de hasta 6 relaciones, siempre con el recordatorio de que esto no es una validación de ensamblaje completa:

| Relación | Qué mira Jarvis hoy |
|---|---|
| FC / ESC / batería / sensores → placa | Solape de cajas + pose (bloqueado si placa o hijo es 🟡 estimado) |
| motores → brazo | Alcance de estación (longitud del brazo vs radio de la cruz) |
| hélices → motores | Todavía no aplica — sin regla de alcance definida |

Estados típicos: bloqueada · lista para declarar verificado · ya declarada · no aplica.

### 10.3 Firmar como verificado

Solo cuando la fila está lista (caja en solape, o motores dentro del alcance):

```text
declaro verificado el esc
```
```text
declaro verificado el motor
```

Se rechaza si el screening no está OK — nunca en silencio. El sello es un juicio tuyo, no una medición de Jarvis. Para quitarlo:

```text
quita la verificación
```

> Los datos de catálogo o declarados son aproximados hasta que los midas físicamente; el sello no convierte un número estimado en una cita.

### 10.4 ¿Parece un dron?

```text
parece un dron
```

**Qué deberías ver:** "racimo" si falta la caja de placa o el stack no está montado/posado; "silueta estimada" si la placa (o algún hijo) sigue en estimación temporal; "silueta" sin más cuando todo lo anterior es 📐 citado.

---

## 11. Ejemplo completo, de principio a fin

Ejemplo real: frame HGLRC MY5 5", motores iFlight XING-E Pro, hélices Gemfan Hurricane MCK 51466-3 V2, ESC Skystars KO50A II, batería Tattu 2300mAh 4S, controladora SpeedyBee F405 V4, GPS Holybro M10.

```text
jarvis --chat
> continuar con mi-dron                  # o "n" si empiezas de cero

ayúdame a elegir                         # motor → iFlight XING-E Pro 2207 2450KV
ayúdame a elegir                         # hélice → Gemfan Hurricane MCK 51466-3 V2
ayúdame a elegir                         # batería → Tattu 2300mAh 4S 75C XT60
ayúdame a elegir                         # ESC → Skystars KO50A II BLS
SpeedyBee F405 V4                        # controladora (identidad + caja citada)
Holybro M10                              # GPS (identidad + caja citada)

declara frame_plate estimada 120 x 55 mm # 🟡 kit sin ficha de placa suelta
declara el esc estimado 8 mm             # 🟡 Skystars sin altura citada (L×W sí)

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

relaciones                               # stack placa bloqueado por estimados (esperado);
                                          # motores→brazo puede estar ya listo
declaro verificado el motor              # si la fila de motores está en alcance OK
parece un dron                           # → silueta estimada
```

**Qué deberías ver al final:** el Board muestra la placa, el stack completo montado y posado, motores/hélices en cruz sobre sus 4 estaciones, y `parece un dron` responde "silueta estimada" — honesto sobre que la placa y el ESC llevan medidas provisionales. El día que midas la placa real o llegue una ficha con la altura del Skystars, sustituye esos dos `declara ... estimad[ao] ...` por la medida real y desaparece el aviso.

---

## 12. Cheatsheet — una página de comandos

```text
# Arranque
jarvis --chat
jarvis board
estado

# Catálogo (motor, hélice, batería, ESC, frame, controladora, GPS, cámara, VTX)
ayúdame a elegir
cambiar esc
actualiza el esc

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

# Misión (cámara / radio / VTX)
ayúdame a elegir cámara                 # Phoenix 2 → 19³ mm, 9 g, 1 W (catálogo)
cámara RunCam                           # texto libre: sin caja/masa/W
cámara 28 g
cámara montada en la placa
restricciones: 8 min
cámara 1 W                              # solo si no vino del catálogo / radio
ayúdame a elegir vtx                    # Zeus 800 → 37×37×5 mm, 4.8 g (catálogo)
vtx HGLRC                               # texto libre: sin caja/masa
vtx 4.8 g                               # sin declaración de potencia (RF mW ≠ W)
```

---

## 13. Límites conocidos

- La medida "de verdad" de la placa (sin catálogo propio) no existe todavía — usa la ruta estimada (§5.2); el stack completo sigue bloqueado para `declaro verificado` mientras la placa sea 🟡.
- Colocar una pose usando un motor o una hélice como origen no está soportado.
- Un rebind a un SKU sin un dato que el anterior sí tenía nunca deja ese dato viejo mal etiquetado — actualizar el mismo SKU preserva lo que declaraste a mano (p. ej. una altura estimada) sin tocarlo.
- Hélices → motores no tiene todavía una regla de alcance/solape propia (motores → brazo sí la tiene). El screening `cabe` sigue siendo solo de cajas.
- `layout pack` sin nombre solo funciona mientras exista exactamente un pack registrado.
- Las medidas de catálogo son aproximadas hasta que las midas físicamente tú mismo.
- El VTX todavía no tiene montaje/pose gestionado por Continuity (solo cámara/radio) — puedes montarlo/posarlo a mano como cualquier otra caja (§7/§8) mientras eso no se añada.
- El VTX no tiene declaración de potencia — su ficha cita vatiaje de radiofrecuencia (mW), una magnitud distinta del consumo eléctrico que suma el modelo energético; no hay número honesto que proyectar todavía.
