# Guía de usuario — Jarvis por voz

> Esta guía es la ruta de operador para **usar** Jarvis con respuestas habladas: instalar un motor de voz **fuera** del paquete, apuntar dos variables de entorno, y sentarte a hablar con Jarvis desde la terminal — no solo lanzar una demo de fixture. Es una lista de comandos reales, no un resumen de arquitectura.
>
> Cada comando de aquí funciona tal cual está escrito — salvo los que necesitan Piper o whisper instalados, que te lo dirán con un error claro si faltan. Si alguno deja de funcionar, es un bug de esta guía, repórtalo.

---

## 1. Qué es y qué no es

**Qué es:** el mismo cerebro Skill-first que ya usas en `jarvis --chat`, alcanzado por un **canal** distinto. Un texto (el que tú escribes en el REPL de voz, o de un fixture, o de un audio transcrito fuera) entra etiquetado como `IntentSource.VOICE`, pasa por los **doce Skills** declarados, y la respuesta que normalmente se imprime se puede además **hablar** con un motor de voz externo.

Los doce Skills alcanzables por voz son exactamente los del chat: `explain <concepto>`, `estado`, `armar`, `desarmar`, `hold`, `land`, `go to`, `takeoff`, `return home` (`rtl`), `follow`, `patrol`, `charge`.

**Qué no es:**

- **No es un asistente de voz always-on.** No hay captura continua de micrófono, ni wake word, ni hilo de escucha de fondo. El micrófono solo se enciende cuando tú lo pides — escribiendo `hablar`/`habla` en `--chat --voice-speak` (§4.1, push-to-talk de un turno) o con `--voice-audio` para un archivo ya grabado (§5.3). Fuera de esos dos momentos exactos, Jarvis nunca escucha.
- **No es un motor de voz.** Jarvis no sintetiza ni transcribe audio. Llama a un **proceso externo** que tú instalas (Piper para hablar, whisper.cpp para transcribir). Ninguno de los dos es dependencia del paquete — `pyproject.toml` no tiene `piper` ni `whisper`, y nunca los tendrá por este camino.
- **El camino craft solo está en `--chat --voice-speak` (§4.1), no en `--voice` (§4.2).** `--voice` es Skill-first puro: si una frase no es uno de los doce Skills, ese canal no la cubre (eso es T40, con su propio contrato). `--chat --voice-speak` es el `--chat` completo de siempre — Continuity, wizards, fallthrough al LLM — con voz añadida encima, sin recortar la **pantalla**. La capa hablada (V7) extrae Continuity; no es un segundo cerebro.
- **No ejecuta vuelo.** `hold`, `takeoff`, `go to`… siguen respondiendo con la misma honestidad Safety que en el chat: `reject`/`disarmed` desarmado, `allow`/`not_implemented` armado. **Ningún dron real se mueve**, por voz igual que por texto. `armar` arma un latch de software, no un ESC.
- **No es un clon de la voz de la película.** El objetivo es *JARVIS-like* (grave, corto, sin teatro; por defecto español `es_ES` desde T49) con voces libres — no clonar a nadie. Ver [brief de producto](../.jes/artifacts/engineer_note_voice_tts_product_brief.md).

---

## 2. Instalar Piper (fuera del paquete)

Piper es un sintetizador local, gratuito y offline. Se instala **fuera** de este repo — en un venv aparte, con `pipx`, o descargando el binario de release.

Opción más simple (venv propio, no el de Jarvis):

```text
python3 -m venv ~/piper-venv
~/piper-venv/bin/pip install piper-tts
```

El ejecutable queda en `~/piper-venv/bin/piper`. Comprueba que responde:

```text
~/piper-venv/bin/piper --help
```

Después necesitas **un modelo de voz**. El brief fija como voz por defecto de demo **`es_ES-davefx-medium`** (español, masculino, grave — voz española leyendo español, T49). Los modelos viven en el repositorio de voces de Piper (`rhasspy/piper-voices` en Hugging Face), organizados por idioma: `es/es_ES/davefx/medium/`.

Cada voz son **dos archivos** que deben quedar **juntos en la misma carpeta**:

```text
es_ES-davefx-medium.onnx          ← el modelo
es_ES-davefx-medium.onnx.json     ← su config (Piper la busca al lado del .onnx)
```

Descárgalos a una carpeta tuya, por ejemplo `~/piper/`. Si bajas solo el `.onnx` y olvidas el `.json`, Piper falla — es el error más común de esta sección.

> Si `davefx` te suena demasiado fino, el brief propone `es_ES-sharvard-medium` como alternativa antes de considerar cualquier servicio de pago. La voz original de demo, **`en_GB-alan-medium`** (inglés británico, grave), sigue totalmente soportada — es un cambio de variable, no de código — si prefieres oír un acento británico leyendo las respuestas en español; descárgala de `en/en_GB/alan/medium/` en el mismo repositorio de voces.

---

## 3. Configurar el entorno

Jarvis habla llamando al comando que le digas en `JARVIS_TTS_CMD`. Este repo trae un wrapper listo que recibe el texto por stdin y se encarga de Piper y del reproductor:

```text
export JARVIS_PIPER_MODEL="$HOME/piper/es_ES-davefx-medium.onnx"
export JARVIS_PIPER_BIN="$HOME/piper-venv/bin/piper"
export JARVIS_TTS_CMD="$PWD/scripts/voice/piper_tts.sh"
```

Comprueba la configuración **antes** de lanzar Jarvis — el wrapper tiene un modo de verificación que no habla nada:

```text
./scripts/voice/piper_tts.sh --check
```

Si todo está en su sitio:

```text
piper_tts.sh: ready (model=/Users/tu/piper/es_ES-davefx-medium.onnx, piper=/Users/tu/piper-venv/bin/piper)
```

Si falta algo, te dice exactamente qué y termina con código 1 — nunca silencia el fallo:

```text
piper_tts.sh: Piper voice model not found: /Users/tu/piper/es_ES-davefx-medium.onnx (download it outside this repo — see docs/USER_GUIDE_VOICE.md §2)
```

Variables que entiende el wrapper:

| Variable | Obligatoria | Qué hace |
|---|---|---|
| `JARVIS_PIPER_MODEL` | sí | Ruta al `.onnx` de la voz (con su `.onnx.json` al lado) |
| `JARVIS_PIPER_BIN` | no | Ejecutable de Piper (por defecto `piper` en el `PATH`) |
| `JARVIS_PIPER_ARGS` | no | Args extra para Piper (p. ej. `--length_scale 1.1` para hablar más despacio) |
| `JARVIS_VOICE_WAV_OUT` | no | Escribe el wav en esa ruta **en vez de** reproducirlo |
| `JARVIS_VOICE_PLAYER` | no | Reproductor de wav (por defecto autodetecta `afplay`/`aplay`/`paplay`) |

---

## 4. Usar Jarvis por voz (interactivo)

Con el entorno de §3 ya configurado, dos rutas para *usar* Jarvis con voz — elige según lo que quieras hacer. Ninguna de las dos es una demo: ambas son sesiones reales, y en ninguna Jarvis llama a `JARVIS_TTS_CMD` salvo que tú lo pidas explícitamente con la flag correspondiente.

### 4.1 Chat completo + voz (`--chat --voice-speak`) — para trabajar de verdad

Esto es **el `--chat` de siempre** — proyectos, Continuity, craft, fallthrough al LLM, exactamente el mismo cerebro — con cada respuesta de Jarvis también **hablada**, no solo impresa. A diferencia de `--voice` (§4.2), aquí no hay límite a los doce Skills: cualquier cosa que hoy funciona en `--chat` sigue funcionando igual, y además se oye.

```text
python -m jarvis.main --chat --voice-speak
```

Cada vez que verías `Jarvis > …`, también lo oyes — **salvo en el muro de Continuity**, donde la pantalla y el oído dicen cosas distintas a propósito (T45, `0.7.4`):

- **Pantalla = verdad completa, siempre.** Al cargar un proyecto, o al escribir `estado` (o cualquier otra frase que ya disparaba el muro), lo que *ves* es exactamente el mismo muro de siempre — Situación, Evidencia, ENGINEERING READINESS, TOP GAPS, todo. Esto no ha cambiado ni se recorta nunca.
- **Voz = extracto breve, por defecto.** Lo que *oyes* en ese mismo turno es un extracto determinista y corto: situación, siguiente paso (con el porqué humanizado), `PROJECT STATUS: ASSEMBLY READY` / `NOT ASSEMBLY READY`, y el título del gap principal — nada de Evidencia completa, tabla de Readiness, BOM, ni cierre de bloque. Sin LLM: son los mismos campos que ya existían, solo que no se leen todos en voz alta por defecto.
- **"Completo" es opt-in, por turno.** Si tu frase es una de estas (exacto, sin tilde, minúscula o mayúscula da igual): `completo`, `estado completo`, `dame detalles`, `dame detalles del proyecto`, `detalles del proyecto`, `cuentame todo`, `cuentame el proyecto`, `cuenta el proyecto`, `describe el proyecto`, `explica el proyecto` — Jarvis **oye** el muro entero ese turno, igual que ves en pantalla. No se queda "en modo completo": el siguiente `estado` vuelve a ser breve, a menos que también pidas `completo` otra vez.

Cualquier otro turno (Skills, errores, wizards, `Acción ejecutada: …`) sigue hablando **exactamente lo que se imprime**, como en T43 — esta distinción breve/completo solo aplica al muro de Continuity.

**`--chat` a solas (sin `--voice-speak`) sigue siendo exactamente como siempre: solo texto.** Jarvis nunca llama a `JARVIS_TTS_CMD` en ese caso, aunque esté configurado — hace falta pedir `--voice-speak` explícitamente.

**Si `JARVIS_TTS_CMD` falta o falla**, Jarvis lo dice e imprime `Jarvis > TTS no disponible: …`, y la conversación sigue — nunca se cae ni finge que habló.

#### 4.1.1 Hablarle de verdad — `hablar` (push-to-talk, T47, `0.7.5`)

Todo lo de arriba sigue siendo teclado. Para hablarle de verdad **dentro de la misma sesión** de `--chat --voice-speak`, escribe exactamente `hablar` o `habla` en `User > `:

```text
python -m jarvis.main --chat --voice-speak
User > hablar
Jarvis > Grabando 7 s…
User > [voz] estado
Jarvis >
  (el muro de Continuity completo en pantalla)
                                  # el oído recibe el extracto breve de §4.1 (o el muro si dices "completo")
User > armar
  (el teclado sigue funcionando exactamente igual)
```

No es always-on: el micrófono se enciende **solo** tras escribir `hablar`/`habla`, graba una duración fija (`JARVIS_RECORD_SECONDS`, por defecto 7 s — no hay "pulsa Enter para terminar"), y se apaga. Jarvis no habla mientras grabas (el cue `Grabando…` se imprime, nunca se dice en voz alta — hablar encima del micrófono se oiría a sí mismo). Lo que se transcribe se ve como `User > [voz] {transcripción}` y entra a la **misma** sesión de chat — Continuity, craft, los doce Skills, las reglas de muro de §4.1 — exactamente como si lo hubieras tecleado. Si la transcripción es literalmente "hablar" o "habla", esa es la frase de ese turno — no se vuelve a grabar.

Variables (además de `JARVIS_TTS_CMD`/`JARVIS_STT_CMD` de más arriba):

```text
export JARVIS_RECORD_CMD="$PWD/scripts/voice/record_turn.sh {output} {seconds}"
export JARVIS_RECORD_SECONDS=7          # opcional, por defecto 7
```

Comprueba antes de hablar:

```text
./scripts/voice/record_turn.sh --check
```

**Si falta `JARVIS_RECORD_CMD`/`JARVIS_STT_CMD`, o la grabación/transcripción falla**, Jarvis lo dice (`Grabación no disponible: …` / `STT no disponible: …`) y la sesión sigue — nunca inventa una frase ni se cae. Ctrl-C durante la grabación cancela ese turno (`Grabación cancelada.`) sin cerrar la sesión.

**`hablar` solo existe con `--voice-speak`.** En `--chat` a solas es texto normal (sin Skill ni sentido especial); no se añade a la lista de frases de Continuity (`estado`, etc.) — es un disparador aparte. `--voice` (§4.2) no tiene `hablar`: sigue siendo únicamente el REPL de teclado Skills-only.

### 4.2 Solo Skills (`--voice`) — REPL ligero, sin craft/Continuity/LLM

Un canal más estrecho: el mismo cerebro Skill-first, pero **sin** proyectos/Continuity/craft — solo los doce Skills (§1). Útil para probar el canal de voz en aislamiento, sin arrastrar una sesión de proyecto completa.

```text
python -m jarvis.main --voice
```

Verás un prompt distinto al de `--chat`, y cada turno **además de imprimirse, se oye** (aquí no hace falta `--voice-speak`: `--voice` siempre habla):

```text
Jarvis (voz) > Escribe una frase (p. ej. 'armar', 'hold', 'estado') — verás y oirás la respuesta. 'salir' o Ctrl-D para terminar.
You > armar
Jarvis > Acción ejecutada: vehicle_arm_policy
Política Safety del chat ARMADA (latch de software ArmedAllowlist). No es armado de ESC, motores ni del dron. HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME/FOLLOW/PATROL pueden pasar a allow/not_implemented (nunca ejecutado de verdad). Latch armed=True.
You > hold
Jarvis > Acción ejecutada: vehicle_hold
HOLD solicitado, pero no se ejecuta ningún vuelo real desde este chat todavía. Safety: allow (motivo: ). Ejecución: not_implemented. Simulación (no vuelo real, sin ESC/motores): tick en t=0.01s, colectivo=0.123.
You > salir
Jarvis > Sesión de voz cerrada.
```

El latch de `armar` persiste turno a turno dentro de la misma sesión — por eso `hold` ya sale `allow` en el segundo turno. Sales con `salir`, `quit`, `exit`, Ctrl-D (EOF), o Ctrl-C.

**Si `JARVIS_TTS_CMD` falta o falla**, Jarvis lo dice y sigue — nunca se cae ni finge que habló:

```text
You > hold
Jarvis > Acción ejecutada: vehicle_hold
HOLD solicitado, pero no se ejecuta ningún vuelo real desde este chat todavía. Safety: reject (motivo: disarmed). Ejecución: not_attempted.
Jarvis > TTS no disponible: no external TTS command configured (set JARVIS_TTS_CMD or pass command_template)
```

**`--chat` a solas sigue siendo solo texto, sin cambios.** `--voice` es un punto de entrada aparte — si no lo pides explícitamente, Jarvis nunca llama a `JARVIS_TTS_CMD`, aunque esté configurado.

---

## 5. Modo batch / fixture — para pruebas, CI, o grabar sin estar delante

§4 es la forma de **usar** Jarvis. Esto es para **automatizar**: correr las mismas frases sin escribir nada a mano (pruebas, demos grabadas, CI), o procesar un turno de audio ya grabado. Son los mismos Skills, el mismo `JARVIS_TTS_CMD` — solo cambia de dónde viene el texto.

### 5.1 Fixture de texto

El repo trae un fixture de ejemplo con unas pocas frases Skill:

```text
$ cat scripts/voice/fixtures/demo_skills.txt
estado
explain c-rate-de-bateria
armar
hold
go to 1.0 2.0
land
desarmar
charge
```

Lánzalo con voz:

```text
python -m jarvis.main --voice-fixture scripts/voice/fixtures/demo_skills.txt --voice-speak
```

Cada línea del fixture es un turno automático — sin teclear nada. Quita `--voice-speak` y es idéntico pero solo impreso:

```text
python -m jarvis.main --voice-fixture scripts/voice/fixtures/demo_skills.txt
```

Tu propio fixture es un `.txt` con una frase por línea (las líneas en blanco se ignoran):

```text
printf 'estado\narmar\ntakeoff\n' > /tmp/mi_demo.txt
python -m jarvis.main --voice-fixture /tmp/mi_demo.txt --voice-speak
```

**Grabar en vez de reproducir:** en una máquina sin audio, o para dejar un wav de muestra, `JARVIS_VOICE_WAV_OUT` escribe el archivo y no intenta reproducir nada. Con un fixture de varias líneas, cada turno sobrescribe el anterior — para un wav por turno, usa un fixture de una sola línea.

```text
JARVIS_VOICE_WAV_OUT=/tmp/turno.wav \
python -m jarvis.main --voice-fixture /tmp/una_linea.txt --voice-speak
```

### 5.2 Un turno desde un audio ya grabado

Esto es la mitad de **entrada**: un archivo de audio se transcribe **fuera** de Jarvis, y el texto resultante entra por el mismo canal. Jarvis no captura ni decodifica audio — y esto procesa **un** archivo por invocación, no un bucle de escucha (para eso usa §4, con el teclado).

Instala whisper.cpp fuera del paquete (su README oficial cubre tu plataforma) y descarga un modelo. Igual que Piper: **nada de esto entra en `pyproject.toml`**.

**Para `hablar`/PTT o cualquier audio en español, usa un modelo multilingüe** (p. ej. `ggml-base.bin`), no uno con sufijo `.en.bin` — esos son solo-inglés y transcriben mal el español (lo oyen como ruido o lo "traducen" a palabras inglesas parecidas). `ggml-base.en.bin` sigue siendo correcto si vas a hablarle en inglés.

```text
export JARVIS_WHISPER_MODEL="$HOME/whisper/ggml-base.bin"
export JARVIS_WHISPER_BIN="$HOME/whisper.cpp/build/bin/whisper-cli"
export JARVIS_STT_CMD="$PWD/scripts/voice/whisper_stt.sh {audio}"
```

El `{audio}` es obligatorio: Jarvis lo sustituye por la ruta del archivo en cada turno. Verifica igual que con Piper:

```text
./scripts/voice/whisper_stt.sh --check
```

### 5.3 Grabar un turno y lanzarlo

La captura de micrófono es un comando de tu sistema, **no** parte de Jarvis. Graba 5 segundos a 16 kHz mono (lo que whisper espera):

```text
# macOS / Linux con ffmpeg (-f avfoundation en macOS, -f alsa en Linux)
ffmpeg -f avfoundation -i ":0" -t 5 -ar 16000 -ac 1 -y /tmp/turno.wav

# Linux con alsa-utils
arecord -d 5 -r 16000 -c 1 -f S16_LE /tmp/turno.wav
```

Y pásalo por el canal completo — audio → transcripción → Skill → voz:

```text
python -m jarvis.main --voice-audio /tmp/turno.wav --voice-speak
```

Di “hold” al micrófono y deberías oír el rechazo honesto de Safety.

---

## 6. Honestidad — lo que la voz nunca hace

- **Nunca mueve un dron.** Por voz, los siete verbos de vuelo dan exactamente el mismo resultado que por texto: `reject`/`disarmed` o `allow`/`not_implemented`. No hay ESC, ni motores, ni cobre en este camino.
- **`armar` por voz no arma hardware.** Arma el latch de software `ArmedAllowlist` del chat. El mensaje lo dice literalmente cada vez.
- **La voz no es una vía de autoridad.** No existe kill-switch por voz, ni override. `AuthoritySignal` no acepta `"voice"` como origen — es imposible por tipo, no por convención.
- **No finge que habló.** Si Piper falta, el modelo no está, o el reproductor falla, el wrapper termina con código distinto de cero y un mensaje en stderr. Jarvis lo recoge e imprime `TTS no disponible: …` — nunca un turno silencioso que parezca correcto, ni en `--voice` ni en `--voice-fixture`/`--voice-audio`.
- **No finge que entendió.** Si whisper falla o devuelve una transcripción vacía, el turno termina con `STT no disponible: …`. Jarvis **no** inventa una frase Skill.
- **No finge que grabó.** Si falta `JARVIS_RECORD_CMD`, o el wrapper de grabación falla, `hablar` termina con `Grabación no disponible: …` — nunca una grabación silenciosa que parezca correcta. Ctrl-C durante la grabación es `Grabación cancelada.`, no un cierre de sesión.
- **No inventa datos de craft.** Es el mismo cerebro: `estado` sigue dando la Continuity real, y `explain` sigue citando la nota del vault sin rellenar masa/potencia/empuje por su cuenta.

---

## 7. Cheatsheet — una página

```text
# ── Preparar (una vez) ───────────────────────────────────────────────
python3 -m venv ~/piper-venv && ~/piper-venv/bin/pip install piper-tts
# descargar es_ES-davefx-medium.onnx + .onnx.json a ~/piper/
# (alt: es_ES-sharvard-medium · legacy: en_GB-alan-medium)

export JARVIS_PIPER_MODEL="$HOME/piper/es_ES-davefx-medium.onnx"
export JARVIS_PIPER_BIN="$HOME/piper-venv/bin/piper"
export JARVIS_TTS_CMD="$PWD/scripts/voice/piper_tts.sh"

# ── Comprobar antes de hablar ────────────────────────────────────────
./scripts/voice/piper_tts.sh --check

# ── Chat completo + voz (proyectos, Continuity, craft, LLM) ──────────
python -m jarvis.main --chat --voice-speak

# ── Hablarle de verdad dentro de esa misma sesión (push-to-talk) ─────
export JARVIS_RECORD_CMD="$PWD/scripts/voice/record_turn.sh {output} {seconds}"
export JARVIS_RECORD_SECONDS=7          # opcional, por defecto 7
./scripts/voice/record_turn.sh --check
#   User > hablar     (o: habla)

# ── Solo Skills por voz (REPL ligero, sin craft/Continuity/LLM) ──────
python -m jarvis.main --voice

# ── Batch / fixture (CI, pruebas, grabar sin estar delante) ──────────
python -m jarvis.main --voice-fixture scripts/voice/fixtures/demo_skills.txt --voice-speak
python -m jarvis.main --voice-fixture scripts/voice/fixtures/demo_skills.txt   # solo texto

JARVIS_VOICE_WAV_OUT=/tmp/turno.wav \
  python -m jarvis.main --voice-fixture /tmp/una_linea.txt --voice-speak

# ── Un turno desde audio ya grabado ──────────────────────────────────
export JARVIS_WHISPER_MODEL="$HOME/whisper/ggml-base.bin"   # multilingüe, no .en.bin
export JARVIS_STT_CMD="$PWD/scripts/voice/whisper_stt.sh {audio}"
./scripts/voice/whisper_stt.sh --check
arecord -d 5 -r 16000 -c 1 -f S16_LE /tmp/turno.wav
python -m jarvis.main --voice-audio /tmp/turno.wav --voice-speak

# ── El chat de siempre, intacto ──────────────────────────────────────
python -m jarvis.main --chat
```

---

## 8. Límites conocidos y problemas típicos

- **Las flags de Piper cambian entre builds.** El wrapper llama `piper --model M --output_file W` (forma de Piper 1.x). Si tu build usa otras, pásalas con `JARVIS_PIPER_ARGS` o ajusta el wrapper — el error de Piper se propaga tal cual a stderr, no se enmascara.
- **Falta el `.onnx.json`.** Es el fallo nº 1 al instalar una voz. Piper no lo pide por flag: lo busca al lado del `.onnx`.
- **La voz por defecto ya es `es_ES` (T49, `0.7.6`).** Los Skills responden en español y, desde T49, la voz de demo por defecto (`es_ES-davefx-medium`) también es española — cierra el desajuste que el brief aceptaba como compromiso de las primeras demos (acento británico leyendo español). Si prefieres ese acento británico, sigue disponible: `en_GB-alan-medium` vía el mismo `JARVIS_PIPER_MODEL`, sin tocar código.
- **`estado` y la Continuity completa son largos para hablarlos — por eso `--chat --voice-speak` ya no los lee enteros por defecto (T45, `0.7.4`).** Al cargar un proyecto o escribir `estado`, la pantalla sigue mostrando el muro completo; el oído recibe el extracto breve de §4.1 salvo que pidas `completo`/`dame detalles` ese turno. Fuera del muro de Continuity (Skills, errores, wizards) no hay renderer "para voz" todavía: se oye exactamente lo que se imprime, igual que en T43.
- **`--voice` sigue siendo solo teclado.** Es un REPL que además habla la respuesta, pero no escucha — hablarle de verdad al micrófono ahí no existe (sin `hablar`/T47 en este canal). En `--chat --voice-speak` sí puedes hablarle de verdad con `hablar`/`habla` (§4.1.1, push-to-talk de un turno fijo, no always-on) o, para un archivo ya grabado, con `--voice-audio` (§5.3). Un modo always-on con wake word no está en voz v1 y necesitaría su propio contrato.
- **El PTT de `hablar` es de duración fija, no "pulsa para terminar".** Graba exactamente `JARVIS_RECORD_SECONDS` segundos (7 por defecto) y para sola — no hay doble Enter ni detección de silencio. Si hablas más corto o más largo, igual se transcribe lo que haya en esa ventana.
- **Craft/wizards solo en `--chat --voice-speak`.** `--voice` (§4.2) es Skill-first puro: si dices una frase que no es uno de los doce Skills, ese canal no la atiende (es T40). `--chat --voice-speak` (§4.1) es el chat completo — esa misma frase sí llega al camino craft/LLM, igual que en `--chat` sin voz.
- **El contexto no persiste entre invocaciones de `--voice-audio`.** Cada llamada a `--voice-audio` crea su propio orquestador y termina — el latch `armar` no sobrevive a la siguiente invocación. Dentro de una misma sesión `--voice` (§4) o de un `--voice-fixture` sí persiste turno a turno.
- **Lo que se oye limpia la decoración visual antes de hablar (T50, `0.7.7`).** Líneas de regla (`────`, `━━━━`, `----`, `====`, `____`), viñetas/checks/árbol al inicio de línea (`•`, `*`, `✓`, `◇`, `└`, `├`, `│`, `─`, `━`) y el asterisco de nota al pie (`PASS *`) se quitan solo en el camino hablado — la **pantalla** sigue mostrando exactamente lo mismo que siempre, sin recortes. También se aplica un único término de glosario: `C-rate`/`c-rate` se dice como "tasa C". No se reescribe `PROJECT STATUS`, `PASS` ni los títulos de gap — eso queda para una Buy futura (T51/T52). Si tras limpiar no queda nada que decir, Jarvis no dice nada ese turno — nunca rellena con voz inventada.
