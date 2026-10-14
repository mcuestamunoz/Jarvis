# Guía de usuario — Jarvis por voz

> Esta guía es la ruta de operador para **usar** Jarvis con respuestas habladas: instalar un motor de voz **fuera** del paquete, apuntar unas pocas variables de entorno, y hablar con Jarvis — sin teclado — desde la terminal. Es una lista de comandos reales, no un resumen de arquitectura.
>
> Cada comando de aquí funciona tal cual está escrito — salvo los que necesitan Piper o whisper instalados, que te lo dirán con un error claro si faltan. Si alguno deja de funcionar, es un bug de esta guía, repórtalo.

---

## 1. Qué es y qué no es

Jarvis tiene **exactamente dos modos de uso diario** (V9, `0.8.0`):

| Modo | Comando | Entrada | Salida |
|---|---|---|---|
| **Chat** | `python -m jarvis.main --chat` | teclado | texto, en silencio |
| **Voz** | `python -m jarvis.main --voice-only` | micrófono | texto en pantalla **y** voz |

**Los dos son el mismo cerebro:** proyectos, Continuity, wizards, craft, los doce Skills y el fallthrough al LLM. `--voice-only` no es un canal recortado — todo lo que funciona en `--chat` funciona igual hablando. Solo cambia de dónde viene tu frase (el micrófono, transcrito) y que la respuesta además se oye.

Los doce Skills son los mismos en los dos modos: `explain <concepto>`, `estado`, `armar`, `desarmar`, `hold`, `land`, `go to`, `takeoff`, `return home` (`rtl`), `follow`, `patrol`, `charge`.

**Qué no es:**

- **No es always-on.** No hay wake word ni hilo de escucha de fondo. En `--voice-only` el micrófono se abre solo cuando Jarvis espera tu turno — nunca mientras Jarvis está hablando — y se cierra cuando dejas de hablar (~1 s de silencio) o, como máximo, a los `JARVIS_RECORD_SECONDS` (7 s por defecto). En `--chat` el micrófono no se toca jamás.
- **No es un motor de voz.** Jarvis no graba, sintetiza ni transcribe audio por sí mismo: llama a **procesos externos** que tú instalas (un grabador como ffmpeg/arecord, whisper.cpp para transcribir, Piper para hablar). Ninguno es dependencia del paquete — `pyproject.toml` no tiene `piper` ni `whisper`, y nunca los tendrá por este camino.
- **No ejecuta vuelo.** `hold`, `takeoff`, `go to`… responden con la misma honestidad Safety por voz que por texto: `reject`/`disarmed` desarmado, `allow`/`not_implemented` armado. **Ningún dron real se mueve.** `armar` arma un latch de software, no un ESC.
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

## 4. Usar Jarvis por voz — `--voice-only`

Con §3 configurado (para que Jarvis hable), añade la transcripción (whisper.cpp instalado fuera del paquete — ver §5.2) y la grabación:

```text
export JARVIS_WHISPER_MODEL="$HOME/whisper/ggml-base.bin"   # multilingüe, no .en.bin
export JARVIS_WHISPER_BIN="$HOME/whisper.cpp/build/bin/whisper-cli"
export JARVIS_STT_CMD="$PWD/scripts/voice/whisper_stt.sh {audio}"
./scripts/voice/whisper_stt.sh --check

export JARVIS_RECORD_CMD="$PWD/scripts/voice/record_turn.sh {output} {seconds}"
export JARVIS_RECORD_SECONDS=7          # opcional: máximo por turno, por defecto 7
export JARVIS_RECORD_SILENCE_SECONDS=1  # opcional: silencio que cierra el turno, por defecto 1 (0 = duración fija)
./scripts/voice/record_turn.sh --check

python -m jarvis.main --voice-only
```

Una sesión típica:

```text
Modo voz: tras cada respuesta el micrófono escucha hasta 7 s y corta tras ~1 s de silencio. Di 'salir' para terminar (o Ctrl-C dos veces seguidas).
Elige proyecto con el teclado; después, todo es por voz.
User > 1                                   ← único turno de teclado: el selector de proyecto
Jarvis >
  (el muro de Continuity completo en pantalla)   # el oído: extracto breve (§4.1)
Jarvis > Grabando (máx 7 s; corta con ~1 s de silencio)…   ← se imprime, nunca se dice
User > [voz] estado
Jarvis >
  (el muro completo otra vez)              # el oído: extracto breve
Jarvis > Grabando (máx 7 s; corta con ~1 s de silencio)…
User > [voz] completo                      # el oído: Continuity completa narrada
Jarvis > Grabando (máx 7 s; corta con ~1 s de silencio)…
User > [voz] salir
Jarvis > Sesión cerrada.
```

- **El micrófono se abre solo.** Sin disparador escrito: graba cuando la sesión espera tu turno y otra vez **después** de que Jarvis termina de hablar — nunca encima de su propia voz.
- **Se cierra cuando dejas de hablar (T54, `0.8.1`).** Una vez que el grabador te ha oído, ~1 s seguido de silencio (`JARVIS_RECORD_SILENCE_SECONDS`) termina el turno; `JARVIS_RECORD_SECONDS` sigue siendo el máximo. Si no dices nada, espera hasta ese máximo (nunca corta una sala vacía antes de tiempo). Con `JARVIS_RECORD_SILENCE_SECONDS=0` vuelve la ventana fija (`Grabando 7 s…`). La detección la hace el grabador externo (`record_turn.sh`, con el filtro `silencedetect` que ya trae ffmpeg) — nada nuevo que instalar en Jarvis. En una sala ruidosa, sube el umbral: `JARVIS_RECORD_SILENCE_NOISE=-30dB` (por defecto `-35dB`). Con solo `arecord` (Linux sin ffmpeg) no hay corte por silencio: graba la ventana fija y lo avisa.
- **Teclado solo para elegir proyecto.** Si ya tienes proyectos, el primer turno (`n`, `1`, `2`…) se escribe; a partir de ahí todo entra por el micrófono. Sin proyectos, el micrófono se abre directamente.
- **Lo que se transcribe se ve** como `User > [voz] {transcripción}` y entra al mismo chat que si lo hubieras tecleado. El audio es efímero: un wav temporal que se borra al terminar el turno (nunca se guarda en `workspace/`).
- **Ctrl-C mientras Jarvis habla** corta la voz (`Habla cancelada.`, solo en pantalla) y el micrófono vuelve a abrirse — la sesión sigue (T56, `0.8.3`).
- **Para terminar:** di `salir` (o `exit`/`quit`). Ctrl-C mientras graba cancela **ese** turno (`Grabación cancelada.`) y el micrófono vuelve a abrirse; un segundo Ctrl-C seguido mientras graba cierra la sesión.

### 4.1 Lo que ves y lo que oyes

Cada vez que verías `Jarvis > …`, también lo oyes — **salvo en el muro de Continuity**, donde la pantalla y el oído dicen cosas distintas a propósito (T45, `0.7.4`):

- **Pantalla = verdad completa, siempre.** Al cargar un proyecto, o al decir `estado` (o cualquier otra frase que ya disparaba el muro), lo que *ves* es exactamente el mismo muro de siempre — Situación, Evidencia, ENGINEERING READINESS, TOP GAPS, todo. Esto no se recorta nunca.
- **Voz = extracto breve, por defecto, en español (T51, `0.7.8`).** Lo que *oyes* en ese mismo turno es un extracto determinista y corto: situación, siguiente paso (con el porqué humanizado), "Estado del proyecto: listo para ensamblar" / "no listo para ensamblar" (nunca el `PROJECT STATUS:` / `ASSEMBLY READY` en inglés de la pantalla), y el título del gap principal — traducido si es uno de los títulos del mapa fijo (p. ej. "Objetivo de autonomía no alcanzado"), o leído tal cual si no está mapeado (honestidad: nunca se inventa una traducción). Sin LLM: son los mismos campos que ya existían.
- **"Completo" es opt-in, por turno.** Si tu frase es una de estas (exacto, sin tilde, minúscula o mayúscula y la puntuación de los extremos dan igual): `completo`, `estado completo`, `dame detalles`, `dame detalles del proyecto`, `detalles del proyecto`, `cuentame todo`, `cuentame el proyecto`, `cuenta el proyecto`, `describe el proyecto`, `explica el proyecto` — oyes la Continuity completa narrada ese turno (T52, `0.7.9`, `full_spoken_continuity`): el extracto breve y, después, Evidencia (hasta 6), Huecos prioritarios (hasta 3, con título en español si está mapeado y "Siguiente: …" — nunca ids de gap, severidad ni dependencias), Arquitectura (progreso y siguiente bloque, o "Completa"), Requisitos físicos y "Bloque propulsión y energía: cerrado / no cerrado". **No** lee el muro de pantalla tal cual: BOM, la tabla de Readiness, Conceptos, los bloques de propulsión/hover/autonomía y el `PROJECT STATUS` en inglés se quedan solo en pantalla. No se queda "en modo completo": el siguiente `estado` vuelve a ser breve.

Cualquier otro turno (Skills, errores, wizards, `Acción ejecutada: …`) se oye **exactamente como se imprime** — la distinción breve/completo solo aplica al muro de Continuity.

### 4.2 Si algo falta o falla

- **Falta `JARVIS_RECORD_CMD` o `JARVIS_STT_CMD`:** Jarvis lo dice una vez (`Grabación no disponible: …` / `STT no disponible: …`) y cierra la sesión — sin eso no puede oírte, y no se queda reintentando en bucle.
- **Una grabación o transcripción falla, o sale vacía:** lo dice (`Grabación no disponible: …` / `STT no disponible: …`) y el micrófono vuelve a abrirse. Nunca inventa una frase.
- **Falta o falla `JARVIS_TTS_CMD`:** imprime `TTS no disponible: …` y la conversación sigue en pantalla — nunca finge que habló.

### 4.3 `--chat` — el modo en silencio

`python -m jarvis.main --chat` es el mismo cerebro por teclado, solo texto: nunca graba ni llama a `JARVIS_TTS_CMD`, aunque esté configurado. Para hablar con Jarvis, el modo es `--voice-only` — no hay combinación "chat + voz". Las combinaciones retiradas de versiones anteriores responden con una línea que apunta a `--voice-only` y salen con código 2, sin abrir ninguna sesión.

---

## 5. Modo batch / fixture — para pruebas, CI, o grabar sin estar delante

§4 es la forma de **usar** Jarvis por voz. Esto **no** es un modo de uso diario: es para **automatizar** (pruebas, demos grabadas, CI) o procesar un turno de audio ya grabado. Ojo: estos dos caminos batch usan el canal Skill-first (`IntentSource.VOICE`, los doce Skills), no el chat completo. `--voice-speak` existe **solo** aquí, para que el batch además hable.

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

Esto es la mitad de **entrada**: un archivo de audio se transcribe **fuera** de Jarvis, y el texto resultante entra por el canal batch. Jarvis no captura ni decodifica audio — y esto procesa **un** archivo por invocación, no un bucle de escucha (para eso está `--voice-only`, §4). `JARVIS_STT_CMD` es el mismo que usa `--voice-only`.

Instala whisper.cpp fuera del paquete (su README oficial cubre tu plataforma) y descarga un modelo. Igual que Piper: **nada de esto entra en `pyproject.toml`**.

**Para `--voice-only` o cualquier audio en español, usa un modelo multilingüe** (p. ej. `ggml-base.bin`), no uno con sufijo `.en.bin` — esos son solo-inglés y transcriben mal el español (lo oyen como ruido o lo "traducen" a palabras inglesas parecidas). `ggml-base.en.bin` sigue siendo correcto si vas a hablarle en inglés.

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

Y pásalo por el canal batch — audio → transcripción → Skill → voz:

```text
python -m jarvis.main --voice-audio /tmp/turno.wav --voice-speak
```

Di “hold” al micrófono y deberías oír el rechazo honesto de Safety.

---

## 6. Honestidad — lo que la voz nunca hace

- **Nunca mueve un dron.** Por voz, los siete verbos de vuelo dan exactamente el mismo resultado que por texto: `reject`/`disarmed` o `allow`/`not_implemented`. No hay ESC, ni motores, ni cobre en este camino.
- **`armar` por voz no arma hardware.** Arma el latch de software `ArmedAllowlist` del chat. El mensaje lo dice literalmente cada vez.
- **La voz no es una vía de autoridad.** No existe kill-switch por voz, ni override. `AuthoritySignal` no acepta `"voice"` como origen — es imposible por tipo, no por convención.
- **No finge que habló.** Si Piper falta, el modelo no está, o el reproductor falla, el wrapper termina con código distinto de cero y un mensaje en stderr. Jarvis lo recoge e imprime `TTS no disponible: …` — nunca un turno silencioso que parezca correcto, ni en `--voice-only` ni en `--voice-fixture`/`--voice-audio`.
- **No finge que entendió.** Si whisper falla o devuelve una transcripción vacía, el turno termina con `STT no disponible: …`. Jarvis **no** inventa una frase.
- **No finge que grabó.** Si falta `JARVIS_RECORD_CMD`, o el wrapper de grabación falla, es `Grabación no disponible: …` — nunca una grabación silenciosa que parezca correcta. Ctrl-C durante la grabación es `Grabación cancelada.`, no un cierre de sesión (salvo el segundo seguido).
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

export JARVIS_WHISPER_MODEL="$HOME/whisper/ggml-base.bin"   # multilingüe, no .en.bin
export JARVIS_STT_CMD="$PWD/scripts/voice/whisper_stt.sh {audio}"

export JARVIS_RECORD_CMD="$PWD/scripts/voice/record_turn.sh {output} {seconds}"
export JARVIS_RECORD_SECONDS=7          # opcional: máximo por turno, por defecto 7
export JARVIS_RECORD_SILENCE_SECONDS=1  # opcional: corta tras ~1 s de silencio (0 = fijo)

# ── Comprobar antes de usar la voz ───────────────────────────────────
./scripts/voice/piper_tts.sh --check
./scripts/voice/whisper_stt.sh --check
./scripts/voice/record_turn.sh --check

# ── Los dos modos ────────────────────────────────────────────────────
python -m jarvis.main --chat            # teclado, en silencio
python -m jarvis.main --voice-only      # micrófono + voz; di "salir" para terminar

# ── Batch / CI (no son modos de uso diario) ──────────────────────────
python -m jarvis.main --voice-fixture scripts/voice/fixtures/demo_skills.txt --voice-speak
python -m jarvis.main --voice-fixture scripts/voice/fixtures/demo_skills.txt   # solo texto

JARVIS_VOICE_WAV_OUT=/tmp/turno.wav \
  python -m jarvis.main --voice-fixture /tmp/una_linea.txt --voice-speak

arecord -d 5 -r 16000 -c 1 -f S16_LE /tmp/turno.wav
python -m jarvis.main --voice-audio /tmp/turno.wav --voice-speak
```

---

## 8. Límites conocidos y problemas típicos

- **Las flags de Piper cambian entre builds.** El wrapper llama `piper --model M --output_file W` (forma de Piper 1.x). Si tu build usa otras, pásalas con `JARVIS_PIPER_ARGS` o ajusta el wrapper — el error de Piper se propaga tal cual a stderr, no se enmascara.
- **Falta el `.onnx.json`.** Es el fallo nº 1 al instalar una voz. Piper no lo pide por flag: lo busca al lado del `.onnx`.
- **La voz por defecto ya es `es_ES` (T49, `0.7.6`).** Los Skills responden en español y, desde T49, la voz de demo por defecto (`es_ES-davefx-medium`) también es española — cierra el desajuste que el brief aceptaba como compromiso de las primeras demos (acento británico leyendo español). Si prefieres ese acento británico, sigue disponible: `en_GB-alan-medium` vía el mismo `JARVIS_PIPER_MODEL`, sin tocar código.
- **`estado` y la Continuity completa son largos para hablarlos — por eso el oído recibe el extracto breve por defecto (T45, `0.7.4`).** La pantalla sigue mostrando el muro completo; pide `completo`/`dame detalles` ese turno para oír la versión completa narrada, nunca el muro leído tal cual (T52). Fuera del muro de Continuity (Skills, errores, wizards) se oye exactamente lo que se imprime.
- **El corte por silencio es por nivel, no por voz.** El grabador corta tras ~1 s por debajo de `JARVIS_RECORD_SILENCE_NOISE` (`-35dB`) después de haber oído algo: un ruido fuerte cuenta como "hablar", y una pausa larga a mitad de frase cierra el turno. Ajusta `JARVIS_RECORD_SILENCE_SECONDS` (p. ej. `1.5`) o el umbral; con `0` vuelves a la ventana fija. Si hablas más que `JARVIS_RECORD_SECONDS`, se corta en el máximo. Sin doble Enter.
- **La puntuación que añade whisper no cuenta (T55, `0.8.2`).** `Completo.`, `¿Completo?` o `Estado.` valen igual que `completo`/`estado`: los signos `.,;:!?¡¿` al principio o al final se ignoran al comparar frases de Continuity, `completo`/FULL y los Skills (`Armar.`, `Hold!`, `Go to 1 2.`). Solo eso — no hay coincidencia aproximada ni frases nuevas.
- **La transcripción decide.** Si whisper oye mal (p. ej. "completo" con otra palabra delante, o "completos"), ese turno no es FULL — la regla de §4.1 compara la frase exacta, solo sin la puntuación de los extremos. El eco `User > [voz] …` te deja ver qué entendió.
- **El contexto no persiste entre invocaciones de `--voice-audio`.** Cada llamada crea su propio orquestador y termina — el latch `armar` no sobrevive a la siguiente invocación. Dentro de una sesión `--voice-only` o de un `--voice-fixture` sí persiste turno a turno.
- **Lo que se oye limpia la decoración visual antes de hablar (T50, `0.7.7`).** Líneas de regla (`────`, `━━━━`, `----`, `====`, `____`), viñetas/checks/árbol al inicio de línea (`•`, `*`, `✓`, `◇`, `└`, `├`, `│`, `─`, `━`) y el asterisco de nota al pie (`PASS *`) se quitan solo en el camino hablado — la **pantalla** sigue mostrando exactamente lo mismo que siempre, sin recortes. También se aplica un único término de glosario: `C-rate`/`c-rate` se dice como "la tasa C" (el artículo `El`/`La` que lo precede se absorbe en la misma sustitución — nunca sale "El tasa C", T51 `0.7.8`). En la pantalla, `PROJECT STATUS`/`PASS`/los títulos de gap siguen en inglés tal cual; lo que se oye (breve y, desde T52 `0.7.9`, también FULL narrado) los dice en español (§4.1). Si tras limpiar no queda nada que decir, Jarvis no dice nada ese turno — nunca rellena con voz inventada.
