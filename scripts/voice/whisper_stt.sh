#!/bin/sh
# Jarvis voice demo — external STT wrapper (T41, `B1-assistant-voice-demo-ready`).
#
# Takes an audio file path as its **only argument** and prints the transcript
# — and nothing else — on **stdout**. That is exactly the contract T37's
# `JARVIS_STT_CMD` seam expects, so point it here with an `{audio}`
# placeholder:
#
#   export JARVIS_WHISPER_MODEL="$HOME/whisper/ggml-base.en.bin"
#   export JARVIS_STT_CMD="$PWD/scripts/voice/whisper_stt.sh {audio}"
#   python -m jarvis.main --voice-audio /tmp/turn.wav --voice-speak
#
# Nothing here is a speech dependency of the Jarvis package: whisper.cpp is a
# separate binary + model the operator installs (see docs/USER_GUIDE_VOICE.md
# §5). This script never decodes audio itself. Diagnostics go to stderr so
# they can never be mistaken for a transcript; every missing piece exits
# non-zero rather than printing an empty "success".
#
# Env:
#   JARVIS_WHISPER_MODEL (required) path to a whisper.cpp .bin model
#   JARVIS_WHISPER_BIN   (optional) executable, default: whisper-cli
#                                   (older builds call it `main`)
#   JARVIS_WHISPER_ARGS  (optional) extra args appended to the call
#
# Flags:
#   --check   verify config + binaries and exit; transcribe nothing.

set -eu

WHISPER_BIN="${JARVIS_WHISPER_BIN:-whisper-cli}"
MODEL="${JARVIS_WHISPER_MODEL:-}"

die() {
    echo "whisper_stt.sh: $1" >&2
    exit 1
}

have() {
    command -v "$1" >/dev/null 2>&1
}

preflight() {
    if [ -z "$MODEL" ]; then
        die "JARVIS_WHISPER_MODEL is not set — point it at a whisper.cpp model (see docs/USER_GUIDE_VOICE.md §5)"
    fi
    if [ ! -f "$MODEL" ]; then
        die "whisper model not found: $MODEL (download it outside this repo — see docs/USER_GUIDE_VOICE.md §5)"
    fi
    if ! have "$WHISPER_BIN"; then
        die "whisper executable not found: $WHISPER_BIN (install whisper.cpp outside this repo, or set JARVIS_WHISPER_BIN — see docs/USER_GUIDE_VOICE.md §5)"
    fi
}

if [ "${1:-}" = "--check" ]; then
    preflight
    echo "whisper_stt.sh: ready (model=$MODEL, whisper=$WHISPER_BIN)" >&2
    exit 0
fi

AUDIO="${1:-}"
if [ -z "$AUDIO" ]; then
    die "usage: whisper_stt.sh <audio-path>  (wire it as JARVIS_STT_CMD=\"…/whisper_stt.sh {audio}\")"
fi
if [ ! -f "$AUDIO" ]; then
    die "audio file not found: $AUDIO"
fi

preflight

# `-nt` suppresses timestamps so stdout is the bare transcript. Diagnostics
# from whisper itself are routed to stderr — stdout stays transcript-only,
# which is what T37's `transcribe_audio_file` reads.
# shellcheck disable=SC2086 # JARVIS_WHISPER_ARGS is an intentional arg list
TRANSCRIPT="$("$WHISPER_BIN" -m "$MODEL" -f "$AUDIO" -nt ${JARVIS_WHISPER_ARGS:-} 2>/dev/null)" \
    || die "whisper failed (exit $?) — check JARVIS_WHISPER_ARGS against your whisper build's CLI"

# Collapse whitespace/newlines into one spoken line; refuse to report an
# empty transcript as success (T37 would reject it anyway — fail here with a
# clearer message).
TRANSCRIPT="$(printf '%s' "$TRANSCRIPT" | tr '\n' ' ' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/[[:space:]][[:space:]]*/ /g')"
if [ -z "$TRANSCRIPT" ]; then
    die "whisper produced an empty transcript for $AUDIO — not reporting success"
fi

printf '%s\n' "$TRANSCRIPT"
