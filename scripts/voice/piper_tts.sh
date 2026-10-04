#!/bin/sh
# Jarvis voice demo — Piper TTS wrapper (T41, `B1-assistant-voice-demo-ready`).
#
# Reads the egress text Jarvis produced on **stdin** and speaks it (or writes
# a wav) via a **Piper installed outside this repo**. Point `JARVIS_TTS_CMD`
# at this script:
#
#   export JARVIS_PIPER_MODEL="$HOME/piper/en_GB-alan-medium.onnx"
#   export JARVIS_TTS_CMD="$PWD/scripts/voice/piper_tts.sh"
#   python -m jarvis.main --voice-fixture scripts/voice/fixtures/demo_skills.txt --voice-speak
#
# Nothing here is a speech dependency of the Jarvis package: Piper is a
# separate binary + voice model the operator installs (see
# docs/USER_GUIDE_VOICE.md). This script never synthesizes audio itself and
# never claims success it did not get — every missing piece exits non-zero
# with a message on stderr.
#
# Env:
#   JARVIS_PIPER_MODEL   (required) path to a Piper .onnx voice model
#   JARVIS_PIPER_BIN     (optional) Piper executable, default: piper
#   JARVIS_PIPER_ARGS    (optional) extra args appended to the Piper call
#   JARVIS_VOICE_WAV_OUT (optional) write wav here instead of playing it
#   JARVIS_VOICE_PLAYER  (optional) wav player, default: autodetect
#                                   (afplay / aplay / paplay)
#
# Flags:
#   --check   verify config + binaries and exit; speak nothing.
#             Exit 0 = ready to speak. Non-zero = what is missing, on stderr.

set -eu

PIPER_BIN="${JARVIS_PIPER_BIN:-piper}"
MODEL="${JARVIS_PIPER_MODEL:-}"

die() {
    echo "piper_tts.sh: $1" >&2
    exit 1
}

have() {
    command -v "$1" >/dev/null 2>&1
}

# ── Config / binary preflight (shared by --check and the real path) ──────────
preflight() {
    if [ -z "$MODEL" ]; then
        die "JARVIS_PIPER_MODEL is not set — point it at a Piper .onnx voice model (see docs/USER_GUIDE_VOICE.md §2)"
    fi
    if [ ! -f "$MODEL" ]; then
        die "Piper voice model not found: $MODEL (download it outside this repo — see docs/USER_GUIDE_VOICE.md §2)"
    fi
    if ! have "$PIPER_BIN"; then
        die "Piper executable not found: $PIPER_BIN (install Piper outside this repo, or set JARVIS_PIPER_BIN — see docs/USER_GUIDE_VOICE.md §2)"
    fi
}

resolve_player() {
    if [ -n "${JARVIS_VOICE_PLAYER:-}" ]; then
        if ! have "${JARVIS_VOICE_PLAYER}"; then
            die "JARVIS_VOICE_PLAYER not found: ${JARVIS_VOICE_PLAYER}"
        fi
        echo "${JARVIS_VOICE_PLAYER}"
        return 0
    fi
    for candidate in afplay aplay paplay; do
        if have "$candidate"; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

if [ "${1:-}" = "--check" ]; then
    preflight
    if [ -z "${JARVIS_VOICE_WAV_OUT:-}" ] && ! resolve_player >/dev/null; then
        die "no wav player found (tried afplay/aplay/paplay) — install one, set JARVIS_VOICE_PLAYER, or set JARVIS_VOICE_WAV_OUT to write a file instead"
    fi
    echo "piper_tts.sh: ready (model=$MODEL, piper=$PIPER_BIN)"
    exit 0
fi

preflight

TEXT="$(cat)"
if [ -z "$(printf '%s' "$TEXT" | tr -d '[:space:]')" ]; then
    die "empty text on stdin — nothing to speak"
fi

# ── Synthesize ──────────────────────────────────────────────────────────────
# `JARVIS_VOICE_WAV_OUT` set -> keep the wav, do not play (useful for a demo
# recording, or on a box with no audio device). Otherwise synthesize to a
# temp wav, play it, and clean up.
if [ -n "${JARVIS_VOICE_WAV_OUT:-}" ]; then
    WAV="$JARVIS_VOICE_WAV_OUT"
    CLEANUP=""
else
    # GNU mktemp requires ≥3 trailing X's at the end of the template.
    # Create the empty tempfile, then use a sibling `.wav` path (and remove
    # the empty placeholder) so Piper writes a real RIFF file.
    _tmp="$(mktemp "${TMPDIR:-/tmp}/jarvis_voice.XXXXXX")"
    WAV="${_tmp}.wav"
    rm -f "$_tmp"
    CLEANUP="$WAV"
fi

cleanup() {
    [ -n "$CLEANUP" ] && rm -f "$CLEANUP" || true
}
trap cleanup EXIT

# shellcheck disable=SC2086 # JARVIS_PIPER_ARGS is an intentional arg list
printf '%s\n' "$TEXT" | "$PIPER_BIN" --model "$MODEL" --output_file "$WAV" ${JARVIS_PIPER_ARGS:-} >&2 \
    || die "Piper failed (exit $?) — check JARVIS_PIPER_MODEL / JARVIS_PIPER_ARGS against your Piper build's CLI"

if [ ! -s "$WAV" ]; then
    die "Piper produced no audio at $WAV — not reporting success"
fi

if [ -n "${JARVIS_VOICE_WAV_OUT:-}" ]; then
    exit 0
fi

PLAYER="$(resolve_player)" || die "no wav player found (tried afplay/aplay/paplay) — install one, set JARVIS_VOICE_PLAYER, or set JARVIS_VOICE_WAV_OUT"
"$PLAYER" "$WAV" >/dev/null 2>&1 || die "wav player '$PLAYER' failed on $WAV"
