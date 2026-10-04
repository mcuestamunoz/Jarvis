# Guía de usuario — Jarvis por voz

> Esta guía es la ruta de operador para **usar** Jarvis con respuestas habladas: instalar un motor de voz **fuera** del paquete, apuntar dos variables de entorno, y lanzar un turno real. Es una lista de comandos reales, no un resumen de arquitectura.
>
> Cada comando de aquí funciona tal cual está escrito — salvo los que necesitan Piper o whisper instalados, que te lo dirán con un error claro si faltan. Si alguno deja de funcionar, es un bug de esta guía, repórtalo.

---

## 1. Qué es y qué no es

**Qué es:** el mismo cerebro Skill-first que ya usas en `jarvis --chat`, alcanzado por un **canal** distinto. Un texto (de un fixture, o de un audio transcrito fuera) entra etiquetado como `IntentSource.VOICE`, pasa por los **doce Skills** declarados, y la respuesta que normalmente se imprime se puede además **hablar** con un motor de voz externo.

Los doce Skills alcanzables por voz son exactamente los del chat: `explain <concepto>`, `estado`, `armar`, `desarmar`, `hold`, `land`, `go to`, `takeoff`, `return home` (`rtl`), `follow`, `patrol`, `charge`.

**Qué no es:**

- **No es un asistente de voz always-on.** No hay captura continua de micrófono, ni wake word, ni hilo de escucha. Cada turno lo lanzas tú con un comando.
- **No es un motor de voz.** Jarvis no sintetiza ni transcribe audio. Llama a un **proceso externo** que tú instalas (Piper para hablar, whisper.cpp para transcribir). Ninguno de los dos es dependencia del paquete — `pyproject.toml` no tiene `piper` ni `whisper`, y nunca los tendrá por este camino.
- **No es el camino craft.** Los asistentes de diseño (wizards de frame/motor/batería, Continuity completa, fallthrough al LLM) **no** están en voz v1. Si una frase no es uno de los doce Skills, este canal no la cubre todavía — eso es T40, con su propio contrato.
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

## 4. Primera demo: fixture + voz

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

Cada línea del fixture es un turno: Jarvis la trata como “esto es lo que dijo el operador”, la pasa por el Skill correspondiente, imprime la respuesta **y la habla**. Verás en pantalla lo mismo que oyes:

```text
Jarvis > Acción ejecutada: vehicle_hold
HOLD solicitado, pero no se ejecuta ningún vuelo real desde este chat todavía. Safety: allow (motivo: ). Ejecución: not_implemented. Simulación (no vuelo real, sin ESC/motores): tick en t=0.01s, colectivo=0.123.
```

Quita `--voice-speak` y es idéntico pero solo impreso — útil para comprobar las frases antes de encender el audio:

```text
python -m jarvis.main --voice-fixture scripts/voice/fixtures/demo_skills.txt
```

Tu propio fixture es un `.txt` con una frase por línea (las líneas en blanco se ignoran):

```text
printf 'estado\narmar\ntakeoff\n' > /tmp/mi_demo.txt
python -m jarvis.main --voice-fixture /tmp/mi_demo.txt --voice-speak
```

### Grabar la demo en vez de reproducirla

En una máquina sin audio (o para dejar un wav de muestra), `JARVIS_VOICE_WAV_OUT` escribe el archivo y no intenta reproducir nada. Ojo: con un fixture de varias líneas, **cada turno sobrescribe el anterior** — queda el último. Para un wav por turno, usa un fixture de una sola línea.

```text
JARVIS_VOICE_WAV_OUT=/tmp/turno.wav \
python -m jarvis.main --voice-fixture /tmp/una_linea.txt --voice-speak
```

---

## 5. (Opcional) Hablarle: micrófono → STT externo

Esto es la mitad de **entrada**: un archivo de audio se transcribe **fuera** de Jarvis, y el texto resultante entra por el mismo canal de voz. Jarvis no captura ni decodifica audio.

### 5.1 Instalar whisper.cpp (fuera del paquete)

whisper.cpp es local, gratuito y offline. Compílalo o instálalo fuera de este repo (su README oficial cubre tu plataforma) y descarga un modelo, por ejemplo `ggml-base.en.bin`. Igual que Piper: **nada de esto entra en `pyproject.toml`**.

### 5.2 Configurar

Este repo trae un wrapper que recibe la ruta del audio y escribe **solo la transcripción** en stdout — que es exactamente el contrato que espera `JARVIS_STT_CMD`:

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

Di “hold” al micrófono y deberías oír el rechazo honesto de Safety. Un turno por comando: no hay bucle de escucha.

---

## 6. Honestidad — lo que la voz nunca hace

- **Nunca mueve un dron.** Por voz, los siete verbos de vuelo dan exactamente el mismo resultado que por texto: `reject`/`disarmed` o `allow`/`not_implemented`. No hay ESC, ni motores, ni cobre en este camino.
- **`armar` por voz no arma hardware.** Arma el latch de software `ArmedAllowlist` del chat. El mensaje lo dice literalmente cada vez.
- **La voz no es una vía de autoridad.** No existe kill-switch por voz, ni override. `AuthoritySignal` no acepta `"voice"` como origen — es imposible por tipo, no por convención.
- **No finge que habló.** Si Piper falta, el modelo no está, o el reproductor falla, el wrapper termina con código distinto de cero y un mensaje en stderr. Jarvis lo recoge e imprime `TTS no disponible: …` — nunca un turno silencioso que parezca correcto.
- **No finge que entendió.** Si whisper falla o devuelve una transcripción vacía, el turno termina con `STT no disponible: …`. Jarvis **no** inventa una frase Skill ni cae de vuelta al fixture.
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

# ── Demo hablada ─────────────────────────────────────────────────────
python -m jarvis.main --voice-fixture scripts/voice/fixtures/demo_skills.txt --voice-speak

# ── Solo texto (sin audio) ───────────────────────────────────────────
python -m jarvis.main --voice-fixture scripts/voice/fixtures/demo_skills.txt

# ── Grabar wav en vez de reproducir ──────────────────────────────────
JARVIS_VOICE_WAV_OUT=/tmp/turno.wav \
  python -m jarvis.main --voice-fixture /tmp/una_linea.txt --voice-speak

# ── (Opcional) entrada por micrófono ─────────────────────────────────
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
- **`estado` es largo para hablarlo.** La Continuity completa son varias líneas con separadores y viñetas; suena denso leída en voz alta. Los otros once Skills son de una o dos frases y suenan bien. No hay renderer “para voz” todavía: la voz lee exactamente el mismo texto que ves.
- **Sin bucle de micrófono.** `--voice-audio` procesa **un** archivo por invocación. Un modo always-on con wake word no está en voz v1 y necesitaría su propio contrato.
- **Craft/wizards fuera.** Si dices una frase que no es uno de los doce Skills, este canal no la atiende (es T40). En el chat de texto esa misma frase sí llega al camino craft/LLM.
- **Un solo turno de contexto por invocación de audio.** `--voice-audio` crea su orquestador y termina; el latch `armar` no persiste entre invocaciones. Dentro de un `--voice-fixture` sí persiste entre líneas (por eso el fixture de ejemplo pone `armar` antes de `hold`).
