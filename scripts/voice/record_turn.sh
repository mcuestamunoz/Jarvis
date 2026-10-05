#!/bin/sh
# Jarvis voice PTT — external record wrapper (T47, `B1-assistant-chat-voice-ptt`).
#
# Records a fixed-duration, 16 kHz mono wav to the path given as the first
# argument, using ffmpeg (macOS avfoundation, or Linux pulse/alsa) or,
# failing that, arecord on Linux. Point JARVIS_RECORD_CMD here with the
# required {output} placeholder (and the optional {seconds} one):
#
#   export JARVIS_RECORD_CMD="$PWD/scripts/voice/record_turn.sh {output} {seconds}"
#   python -m jarvis.main --chat --voice-speak
#   User > hablar
#
# Nothing here is a speech/audio dependency of the Jarvis package — ffmpeg
# or arecord are separate binaries the operator installs. This script never
# decodes or transcribes audio itself; it only captures raw PCM to a wav
# file for T37's existing JARVIS_STT_CMD seam to transcribe afterwards.
# Diagnostics go to stderr; every missing piece exits non-zero rather than
# silently producing an empty or missing file.
#
# Env:
#   JARVIS_RECORD_SECONDS (optional) capture duration, default: 7
#                                     (overridden by the {seconds} arg below
#                                     when the IC's JARVIS_RECORD_CMD passes one)
#   JARVIS_RECORD_DEVICE  (optional) input device — ffmpeg avfoundation
#                                     index on macOS (default ":0"), or the
#                                     pulse/alsa device name on Linux
#                                     (default "default")
#
# Usage:
#   record_turn.sh <output.wav> [seconds]
#   record_turn.sh --check

set -eu

die() {
    echo "record_turn.sh: $1" >&2
    exit 1
}

have() {
    command -v "$1" >/dev/null 2>&1
}

# ── Pick a recorder for this platform — never fail silently into a
# "recording" that never ran. ────────────────────────────────────────────────
platform_tool() {
    case "$(uname -s)" in
        Darwin)
            if have ffmpeg; then
                echo "ffmpeg-avfoundation"
                return 0
            fi
            ;;
        *)
            if have ffmpeg; then
                if have pactl || have pulseaudio; then
                    echo "ffmpeg-pulse"
                else
                    echo "ffmpeg-alsa"
                fi
                return 0
            fi
            if have arecord; then
                echo "arecord"
                return 0
            fi
            ;;
    esac
    return 1
}

if [ "${1:-}" = "--check" ]; then
    TOOL="$(platform_tool)" || die "no recorder found (install ffmpeg, or arecord on Linux)"
    echo "record_turn.sh: ready (tool=$TOOL, seconds=${JARVIS_RECORD_SECONDS:-7})"
    exit 0
fi

OUTPUT="${1:-}"
if [ -z "$OUTPUT" ]; then
    die "usage: record_turn.sh <output.wav> [seconds]  (wire it as JARVIS_RECORD_CMD=\"…/record_turn.sh {output} {seconds}\")"
fi
DURATION="${2:-${JARVIS_RECORD_SECONDS:-7}}"

TOOL="$(platform_tool)" || die "no recorder found (install ffmpeg, or arecord on Linux)"

case "$TOOL" in
    ffmpeg-avfoundation)
        DEVICE="${JARVIS_RECORD_DEVICE:-:0}"
        ffmpeg -y -f avfoundation -i "$DEVICE" -t "$DURATION" -ar 16000 -ac 1 "$OUTPUT" \
            || die "ffmpeg (avfoundation) failed — check JARVIS_RECORD_DEVICE (default ':0', the system default mic)"
        ;;
    ffmpeg-pulse)
        DEVICE="${JARVIS_RECORD_DEVICE:-default}"
        ffmpeg -y -f pulse -i "$DEVICE" -t "$DURATION" -ar 16000 -ac 1 "$OUTPUT" \
            || die "ffmpeg (pulse) failed — check JARVIS_RECORD_DEVICE"
        ;;
    ffmpeg-alsa)
        DEVICE="${JARVIS_RECORD_DEVICE:-default}"
        ffmpeg -y -f alsa -i "$DEVICE" -t "$DURATION" -ar 16000 -ac 1 "$OUTPUT" \
            || die "ffmpeg (alsa) failed — check JARVIS_RECORD_DEVICE"
        ;;
    arecord)
        arecord -d "$DURATION" -r 16000 -c 1 -f S16_LE "$OUTPUT" \
            || die "arecord failed"
        ;;
esac

if [ ! -s "$OUTPUT" ]; then
    die "recorder produced no audio at $OUTPUT — not reporting success"
fi
