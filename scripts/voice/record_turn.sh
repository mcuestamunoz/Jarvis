#!/bin/sh
# Jarvis voice — external record wrapper (T47; default mic input of --voice-only since T53).
#
# Records a 16 kHz mono wav to the path given as the first argument, using
# ffmpeg (macOS avfoundation, or Linux pulse/alsa) or, failing that, arecord
# on Linux. The capture is capped at {seconds}. With ffmpeg it also stops
# early (T54, V10) once speech has been heard and then
# JARVIS_RECORD_SILENCE_SECONDS of continuous silence follow — detected by
# ffmpeg's own built-in `silencedetect` filter, watched from this script.
# If nobody speaks, there is no early cut: the capture runs to the cap. Point JARVIS_RECORD_CMD here with the
# required {output} placeholder (and the optional {seconds} one):
#
#   export JARVIS_RECORD_CMD="$PWD/scripts/voice/record_turn.sh {output} {seconds}"
#   python -m jarvis.main --voice-only
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
#   JARVIS_RECORD_SILENCE_SECONDS (optional) silence that ends a turn once
#                                     speech was heard, default: 1.0. Set to
#                                     0 (or empty) for a fixed-duration
#                                     capture (T53 behavior). arecord-only
#                                     hosts cannot detect silence and always
#                                     record the fixed duration (stderr note).
#   JARVIS_RECORD_SILENCE_NOISE   (optional) level below which audio counts
#                                     as silence, default: -35dB (raise to
#                                     e.g. -30dB in a noisy room)
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

# ── Silence window (printed %g-style): unset → 1; empty or 0 → fixed
# duration ("0"); negative/unparseable → 1. Same rules as Python's
# jarvis.adapters.voice.resolve_record_silence_seconds (which only prints
# the cue). ────────────────────────────────────────────────────────────────
silence_seconds() {
    if [ -z "${JARVIS_RECORD_SILENCE_SECONDS+set}" ]; then
        echo "1"
        return 0
    fi
    awk -v raw="$JARVIS_RECORD_SILENCE_SECONDS" 'BEGIN {
        if (raw ~ /^[ \t]*$/) { print "0"; exit }
        if (raw !~ /^[ \t]*[0-9]*\.?[0-9]+[ \t]*$/) { print "1"; exit }
        printf "%g\n", raw + 0
    }'
}

SILENCE="$(silence_seconds)"
NOISE="${JARVIS_RECORD_SILENCE_NOISE:--35dB}"

if [ "${1:-}" = "--check" ]; then
    TOOL="$(platform_tool)" || die "no recorder found (install ffmpeg, or arecord on Linux)"
    if [ "$SILENCE" = "0" ]; then
        CUT="off (fixed duration)"
    elif [ "$TOOL" = "arecord" ]; then
        CUT="unsupported with arecord (fixed duration) — install ffmpeg"
    else
        CUT="${SILENCE}s below $NOISE"
    fi
    echo "record_turn.sh: ready (tool=$TOOL, max seconds=${JARVIS_RECORD_SECONDS:-7}, silence cut=$CUT)"
    exit 0
fi

OUTPUT="${1:-}"
if [ -z "$OUTPUT" ]; then
    die "usage: record_turn.sh <output.wav> [seconds]  (wire it as JARVIS_RECORD_CMD=\"…/record_turn.sh {output} {seconds}\")"
fi
DURATION="${2:-${JARVIS_RECORD_SECONDS:-7}}"

TOOL="$(platform_tool)" || die "no recorder found (install ffmpeg, or arecord on Linux)"

# ── ffmpeg capture. Fixed duration when the silence cut is off; otherwise
# ffmpeg runs in the background with `silencedetect` and this script watches
# its log: `silence_end` means sound was heard; a `silence_start` after
# sound (or one stamped past the very start, i.e. speech came first) means
# SILENCE seconds of continuous silence have already elapsed → stop ffmpeg
# with SIGTERM, which it handles by finalizing the wav. `-t` stays the cap. ─
record_ffmpeg() {
    FORMAT="$1"
    DEVICE="$2"
    if [ "$SILENCE" = "0" ]; then
        ffmpeg -y -f "$FORMAT" -i "$DEVICE" -t "$DURATION" -ar 16000 -ac 1 "$OUTPUT"
        return $?
    fi

    WORKDIR="$(mktemp -d)"
    LOG_FIFO="$WORKDIR/ffmpeg.log"
    mkfifo "$LOG_FIFO"
    ffmpeg -nostdin -hide_banner -nostats -loglevel info -y -f "$FORMAT" -i "$DEVICE" -t "$DURATION" \
        -af "silencedetect=noise=$NOISE:d=$SILENCE" -ar 16000 -ac 1 "$OUTPUT" 2>"$LOG_FIFO" &
    FFMPEG_PID=$!
    # Ctrl-C reaches this script in the foreground; never leave ffmpeg
    # holding the mic behind it.
    trap 'kill -TERM "$FFMPEG_PID" 2>/dev/null; rm -rf "$WORKDIR"; exit 130' INT TERM

    HEARD=0
    CUT=0
    while IFS= read -r LINE; do
        case "$LINE" in
            *silence_end:*)
                HEARD=1
                ;;
            *silence_start:*)
                if [ "$CUT" = 0 ]; then
                    AT="${LINE##*silence_start: }"
                    AT="${AT%% *}"
                    if [ "$HEARD" = 1 ] || awk -v t="$AT" 'BEGIN { exit !(t + 0 > 0.05) }'; then
                        CUT=1
                        kill -TERM "$FFMPEG_PID" 2>/dev/null || true
                    fi
                fi
                ;;
            *Error*|*error*)
                echo "$LINE" >&2
                ;;
        esac
    done < "$LOG_FIFO"

    STATUS=0
    wait "$FFMPEG_PID" || STATUS=$?
    trap - INT TERM
    rm -rf "$WORKDIR"
    # ffmpeg exits non-zero when it was stopped by our SIGTERM — that is the
    # silence cut working, not a failure (the non-empty check below still
    # applies).
    if [ "$CUT" = 1 ]; then
        return 0
    fi
    return "$STATUS"
}

case "$TOOL" in
    ffmpeg-avfoundation)
        record_ffmpeg avfoundation "${JARVIS_RECORD_DEVICE:-:0}" \
            || die "ffmpeg (avfoundation) failed — check JARVIS_RECORD_DEVICE (default ':0', the system default mic)"
        ;;
    ffmpeg-pulse)
        record_ffmpeg pulse "${JARVIS_RECORD_DEVICE:-default}" \
            || die "ffmpeg (pulse) failed — check JARVIS_RECORD_DEVICE"
        ;;
    ffmpeg-alsa)
        record_ffmpeg alsa "${JARVIS_RECORD_DEVICE:-default}" \
            || die "ffmpeg (alsa) failed — check JARVIS_RECORD_DEVICE"
        ;;
    arecord)
        if [ "$SILENCE" != "0" ]; then
            echo "record_turn.sh: silence cut needs ffmpeg — arecord records the fixed $DURATION s" >&2
        fi
        arecord -d "$DURATION" -r 16000 -c 1 -f S16_LE "$OUTPUT" \
            || die "arecord failed"
        ;;
esac

if [ ! -s "$OUTPUT" ]; then
    die "recorder produced no audio at $OUTPUT — not reporting success"
fi
