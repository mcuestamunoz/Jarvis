# Guía de usuario — Jarvis por voz

> Esta guía es la ruta de operador para **usar** Jarvis con respuestas habladas: instalar un motor de voz **fuera** del paquete, apuntar dos variables de entorno, y sentarte a hablar con Jarvis desde la terminal — no solo lanzar una demo de fixture. Es una lista de comandos reales, no un resumen de arquitectura.
>
> Cada comando de aquí funciona tal cual está escrito — salvo los que necesitan Piper o whisper instalados, que te lo dirán con un error claro si faltan. Si alguno deja de funcionar, es un bug de esta guía, repórtalo.

---

## 1. Qué es y qué no es

**Qué es:** el mismo cerebro Skill-first que ya usas en `jarvis --chat`, alcanzado por un **canal** distinto. Un texto (el que tú escribes en el REPL de voz, o de un fixture, o de un audio transcrito fuera) entra etiquetado como `IntentSource.VOICE`, pasa por los **doce Skills** declarados, y la respuesta que normalmente se imprime se puede además **hablar** con un motor de voz externo.

Los doce Skills alcanzables por voz son exactamente los del chat: `explain <concepto>`, `estado`, `armar`, `desarmar`, `hold`, `land`, `go to`, `takeoff`, `return home` (`rtl`), `follow`, `patrol`, `charge`.

**Qué no es:**

- **No es un asistente de voz always-on.** No hay captura continua de micrófono, ni wake word, ni hilo de escucha de fondo. Los dos REPLs interactivos (§4) siguen siendo **texto escrito por teclado** — lo que es nuevo es que, además de leer la respuesta, también la *oyes*; hablarle de verdad al micrófono es el camino opcional de un solo turno en §5.3.
- **No es un motor de voz.** Jarvis no sintetiza ni transcribe audio. Llama a un **proceso externo** que tú instalas (Piper para hablar, whisper.cpp para transcribir). Ninguno de los dos es dependencia del paquete — `pyproject.toml` no tiene `piper` ni `whisper`, y nunca los tendrá por este camino.
- **El camino craft solo está en `--chat --voice-speak` (§4.1), no en `--voice` (§4.2).** `--voice` es Skill-first puro: si una frase no es uno de los doce Skills, ese canal no la cubre (eso es T40, con su propio contrato). `--chat --voice-speak` es el `--chat` completo de siempre — Continuity, wizards, fallthrough al LLM — con voz añadida encima, sin recortar la **pantalla**. La capa hablada (V7) extrae Continuity; no es un segundo cerebro.
- **No ejecuta vuelo.** `hold`, `takeoff`, `go to`… siguen respondiendo con la misma honestidad Safety que en el chat: `reject`/`disarmed` desarmado, `allow`/`not_implemented` armado. **Ningún dron real se mueve**, por voz igual que por texto. `armar` arma un latch de software, no un ESC.
- **No es un clon de la voz de la película.** El objetivo es *JARVIS-like* (británico, grave, corto, sin teatro) con voces libres — no clonar a nadie. Ver [brief de producto](../.jes/artifacts/engineer_note_voice_tts_product_brief.md).

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

Después necesitas **un modelo de voz**. El brief fija como voz por defecto de demo **`en_GB-alan-medium`** (inglés británico, masculino, grave). Los modelos viven en el repositorio de voces de Piper (`rhasspy/piper-voices` en Hugging Face), organizados por idioma: `en/en_GB/alan/medium/`.

Cada voz son **dos archivos** que deben quedar **juntos en la misma carpeta**:

```text
en_GB-alan-medium.onnx          ← el modelo
en_GB-alan-medium.onnx.json     ← su config (Piper la busca al lado del .onnx)
```

Descárgalos a una carpeta tuya, por ejemplo `~/piper/`. Si bajas solo el `.onnx` y olvidas el `.json`, Piper falla — es el error más común de esta sección.

> Si `alan` te suena demasiado fino, el brief propone `en_GB-northern_english_male-medium` como alternativa antes de considerar cualquier servicio de pago.

---

## 3. Configurar el entorno

Jarvis habla llamando al comando que le digas en `JARVIS_TTS_CMD`. Este repo trae un wrapper listo que recibe el texto por stdin y se encarga de Piper y del reproductor:

```text
export JARVIS_PIPER_MODEL="$HOME/piper/en_GB-alan-medium.onnx"
export JARVIS_PIPER_BIN="$HOME/piper-venv/bin/piper"
export JARVIS_TTS_CMD="$PWD/scripts/voice/piper_tts.sh"
```

Comprueba la configuración **antes** de lanzar Jarvis — el wrapper tiene un modo de verificación que no habla nada:

```text
./scripts/voice/piper_tts.sh --check
```

Si todo está en su sitio:

```text
piper_tts.sh: ready (model=/Users/tu/piper/en_GB-alan-medium.onnx, piper=/Users/tu/piper-venv/bin/piper)
```

Si falta algo, te dice exactamente qué y termina con código 1 — nunca silencia el fallo:

```text
piper_tts.sh: Piper voice model not found: /Users/tu/piper/en_GB-alan-medium.onnx (download it outside this repo — see docs/USER_GUIDE_VOICE.md §2)
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

Cada vez que verías `Jarvis > …`, también lo oyes. **Hoy (T43, `0.7.3`) la voz lee el mismo texto que ves** — incluido el muro de Continuity al cargar un proyecto o al decir `estado`. Eso es honesto y, para Continuity, demasiado largo.

**Diseño V7 (T44-DC → T45 @ `0.7.4`):** la pantalla sigue siendo la verdad completa; la voz pasa a un extracto determinista (situación, siguiente paso, por qué, listo/no listo, top gap). `dame detalles` / `completo` leen el muro **ese turno**. Sin LLM. Hasta que T45 aterrice, el comportamiento real sigue siendo T43 (muro entero).

**`--chat` a solas (sin `--voice-speak`) sigue siendo exactamente como siempre: solo texto.** Jarvis nunca llama a `JARVIS_TTS_CMD` en ese caso, aunque esté configurado — hace falta pedir `--voice-speak` explícitamente.

**Si `JARVIS_TTS_CMD` falta o falla**, Jarvis lo dice e imprime `Jarvis > TTS no disponible: …`, y la conversación sigue — nunca se cae ni finge que habló.

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

Instala whisper.cpp fuera del paquete (su README oficial cubre tu plataforma) y descarga un modelo, por ejemplo `ggml-base.en.bin`. Igual que Piper: **nada de esto entra en `pyproject.toml`**.

```text
export JARVIS_WHISPER_MODEL="$HOME/whisper/ggml-base.en.bin"
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
- **No inventa datos de craft.** Es el mismo cerebro: `estado` sigue dando la Continuity real, y `explain` sigue citando la nota del vault sin rellenar masa/potencia/empuje por su cuenta.

---

## 7. Cheatsheet — una página

```text
# ── Preparar (una vez) ───────────────────────────────────────────────
python3 -m venv ~/piper-venv && ~/piper-venv/bin/pip install piper-tts
# descargar en_GB-alan-medium.onnx + .onnx.json a ~/piper/

export JARVIS_PIPER_MODEL="$HOME/piper/en_GB-alan-medium.onnx"
export JARVIS_PIPER_BIN="$HOME/piper-venv/bin/piper"
export JARVIS_TTS_CMD="$PWD/scripts/voice/piper_tts.sh"

# ── Comprobar antes de hablar ────────────────────────────────────────
./scripts/voice/piper_tts.sh --check

# ── Chat completo + voz (proyectos, Continuity, craft, LLM) ──────────
python -m jarvis.main --chat --voice-speak

# ── Solo Skills por voz (REPL ligero, sin craft/Continuity/LLM) ──────
python -m jarvis.main --voice

# ── Batch / fixture (CI, pruebas, grabar sin estar delante) ──────────
python -m jarvis.main --voice-fixture scripts/voice/fixtures/demo_skills.txt --voice-speak
python -m jarvis.main --voice-fixture scripts/voice/fixtures/demo_skills.txt   # solo texto

JARVIS_VOICE_WAV_OUT=/tmp/turno.wav \
  python -m jarvis.main --voice-fixture /tmp/una_linea.txt --voice-speak

# ── Un turno desde audio ya grabado ──────────────────────────────────
export JARVIS_WHISPER_MODEL="$HOME/whisper/ggml-base.en.bin"
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
- **Los Skills responden en español, la voz por defecto es `en_GB`.** El brief acepta esto para las primeras demos (acento británico leyendo español). Si molesta, el camino es una voz `es_ES` de Piper — mismo wrapper, solo cambia `JARVIS_PIPER_MODEL`; no hace falta tocar código.
- **`estado` y la Continuity completa son largos para hablarlos.** Hoy (T43) la voz lee exactamente el mismo texto que ves. El plan V7 ([cola](../.jes/artifacts/engineer_note_voice_phase_c_cola.md) · [DC](../.jes/artifacts/design_contract_assistant_chat_spoken_continuity_b0.md)) separa **verdad en pantalla** vs **extracto hablado**; T45 implementa eso. Hasta entonces no hay renderer "para voz": se oye el muro entero.
- **Ni `--voice` ni `--chat --voice-speak` son micrófono.** Ambos son REPLs de teclado que además hablan la respuesta — hablarle de verdad al micrófono es §5.3 (`--voice-audio`, un turno por invocación). Un modo always-on con wake word no está en voz v1 y necesitaría su propio contrato.
- **Craft/wizards solo en `--chat --voice-speak`.** `--voice` (§4.2) es Skill-first puro: si dices una frase que no es uno de los doce Skills, ese canal no la atiende (es T40). `--chat --voice-speak` (§4.1) es el chat completo — esa misma frase sí llega al camino craft/LLM, igual que en `--chat` sin voz.
- **El contexto no persiste entre invocaciones de `--voice-audio`.** Cada llamada a `--voice-audio` crea su propio orquestador y termina — el latch `armar` no sobrevive a la siguiente invocación. Dentro de una misma sesión `--voice` (§4) o de un `--voice-fixture` sí persiste turno a turno.
