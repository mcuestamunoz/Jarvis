"""Tests T1-T6 for `B1-assistant-voice-silence-cut` (T54 / V10).

T53's `--voice-only` recorded a fixed `JARVIS_RECORD_SECONDS` window.
V10 ends the turn early once the user stops talking: after speech has
been heard, `JARVIS_RECORD_SILENCE_SECONDS` (default 1.0) of continuous
silence stops the capture; `JARVIS_RECORD_SECONDS` stays the hard cap;
with no speech at all the capture runs to the cap; `0` (or empty) means
fixed duration. The cut lives in the **external** recorder
(`scripts/voice/record_turn.sh`, ffmpeg's built-in `silencedetect`
filter) — `record_audio_file` is unchanged and no audio package enters
`pyproject.toml`. Python only resolves the env to print an honest,
never-spoken cue.

Mic-free: T1-T3 run the **real** `record_turn.sh` against a fake
`ffmpeg` placed first on `PATH` that logs its argv, emits
`silencedetect`-style log lines per scenario, honours `-t`, and on
SIGTERM finalizes the output and exits non-zero — exactly what the
script's watcher relies on. T2b repeats the early-cut check against the
real ffmpeg with a synthetic real-time `lavfi` source (skipped when
ffmpeg is not installed).
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import time
import typing
from pathlib import Path

import pytest

import jarvis.workspace.workspace_manager as workspace_manager_module
from jarvis.capabilities.safety import AuthoritySource

REPO_ROOT = Path(__file__).resolve().parents[1]
RECORD_WRAPPER = REPO_ROOT / "scripts" / "voice" / "record_turn.sh"
GUIDE = REPO_ROOT / "docs" / "USER_GUIDE_VOICE.md"

# Fake ffmpeg: argv logged to $FAKE_FFMPEG_ARGS; scenario from
# $FAKE_FFMPEG_SCENARIO. Writes placeholder wav bytes on normal end or
# SIGTERM (exit 255 on SIGTERM, like ffmpeg).
_FAKE_FFMPEG = r"""#!/bin/sh
echo "$*" >> "$FAKE_FFMPEG_ARGS"
CAP=7
PREV=""
for ARG in "$@"; do
    if [ "$PREV" = "-t" ]; then CAP="$ARG"; fi
    PREV="$ARG"
    OUT="$ARG"
done
SLEEP_PID=""
finish() {
    [ -n "$SLEEP_PID" ] && kill "$SLEEP_PID" 2>/dev/null
    printf 'RIFF....WAVEfake' > "$OUT"
    exit "$1"
}
trap 'finish 255' TERM
emit() { echo "[silencedetect @ 0x1] $1" >&2; }
case "$*" in
    *silencedetect*) SCENARIO="${FAKE_FFMPEG_SCENARIO:-speech_then_silence}" ;;
    *) SCENARIO=fixed ;;
esac
case "$SCENARIO" in
    speech_then_silence)
        emit "silence_start: 0"
        sleep 0.2
        emit "silence_end: 0.3 | silence_duration: 0.3"
        sleep 0.3
        emit "silence_start: 0.9"
        ;;
    speech_first)
        sleep 0.3
        emit "silence_start: 0.6"
        ;;
    silent_room)
        emit "silence_start: 0"
        ;;
    speech_forever)
        emit "silence_start: 0"
        sleep 0.1
        emit "silence_end: 0.1 | silence_duration: 0.1"
        ;;
esac
# The timer must not inherit stderr (the script's log FIFO), or the
# watcher would only see EOF when the timer ends.
sleep "$CAP" >/dev/null 2>&1 &
SLEEP_PID=$!
wait "$SLEEP_PID"
SLEEP_PID=""
finish 0
"""


def _write_script(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


def _fake_ffmpeg_env(tmp_path: Path, *, scenario: str | None = None, silence: str | None = None) -> dict:
    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir(exist_ok=True)
    _write_script(bin_dir / "ffmpeg", _FAKE_FFMPEG)
    env = {k: v for k, v in os.environ.items() if not k.startswith("JARVIS_RECORD_")}
    env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
    env["FAKE_FFMPEG_ARGS"] = str(tmp_path / "ffmpeg_args.log")
    if scenario is not None:
        env["FAKE_FFMPEG_SCENARIO"] = scenario
    if silence is not None:
        env["JARVIS_RECORD_SILENCE_SECONDS"] = silence
    return env


def _record(tmp_path: Path, env: dict, seconds: int) -> tuple[subprocess.CompletedProcess, float, Path]:
    output = tmp_path / "turn.wav"
    output.unlink(missing_ok=True)
    start = time.monotonic()
    done = subprocess.run(
        [str(RECORD_WRAPPER), str(output), str(seconds)],
        capture_output=True,
        text=True,
        env=env,
        timeout=seconds + 10,
    )
    return done, time.monotonic() - start, output


def _ffmpeg_args(tmp_path: Path) -> str:
    return (tmp_path / "ffmpeg_args.log").read_text(encoding="utf-8")


def _isolate_workspace(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(workspace_manager_module, "DEFAULT_WORKSPACE_ROOT", tmp_path / "workspace")


def _forbid_keyboard(monkeypatch) -> None:
    def no_keyboard(prompt: str = "") -> str:
        raise AssertionError("voice-only must not read the keyboard without projects")

    monkeypatch.setattr("builtins.input", no_keyboard)


def _wire_voice_only_through_real_wrapper(tmp_path: Path, monkeypatch, env: dict, transcripts: list[str]) -> None:
    """`run_voice_only` → real `record_turn.sh` (fake ffmpeg on PATH) →
    queue-driven fake STT; TTS unset (honest `TTS no disponible`)."""
    for key in ("PATH", "FAKE_FFMPEG_ARGS", "FAKE_FFMPEG_SCENARIO", "JARVIS_RECORD_SILENCE_SECONDS"):
        if key in env:
            monkeypatch.setenv(key, env[key])
        else:
            monkeypatch.delenv(key, raising=False)
    queue = tmp_path / "stt_queue.txt"
    queue.write_text("".join(f"{line}\n" for line in transcripts), encoding="utf-8")
    stt = _write_script(
        tmp_path / "queue_stt.sh",
        "#!/bin/sh\n"
        f'Q="{queue}"\n'
        'if [ ! -s "$Q" ]; then echo salir; exit 0; fi\n'
        'head -n 1 "$Q"\n'
        'tail -n +2 "$Q" > "$Q.tmp"; mv "$Q.tmp" "$Q"\n',
    )
    monkeypatch.setenv("JARVIS_RECORD_CMD", f"{RECORD_WRAPPER} {{output}} {{seconds}}")
    monkeypatch.setenv("JARVIS_RECORD_SECONDS", "3")
    monkeypatch.setenv("JARVIS_STT_CMD", f"{stt} {{audio}}")
    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)


def test_t1_silence_zero_is_fixed_duration_and_t53_loop_unchanged(tmp_path, monkeypatch, capsys):
    env = _fake_ffmpeg_env(tmp_path, silence="0")
    done, elapsed, output = _record(tmp_path, env, seconds=1)
    assert done.returncode == 0, done.stderr
    assert output.stat().st_size > 0
    assert "silencedetect" not in _ffmpeg_args(tmp_path)
    assert "-t 1" in _ffmpeg_args(tmp_path)
    assert elapsed >= 0.9, "fixed mode must record the whole window"

    # Empty value is also fixed-only.
    env = _fake_ffmpeg_env(tmp_path, silence="")
    (tmp_path / "ffmpeg_args.log").unlink()
    done, _, _ = _record(tmp_path, env, seconds=1)
    assert done.returncode == 0 and "silencedetect" not in _ffmpeg_args(tmp_path)

    # T53 voice-only loop with S=0: fixed cue, armar → salir.
    _isolate_workspace(monkeypatch, tmp_path)
    _forbid_keyboard(monkeypatch)
    from jarvis.adapters.cli.main import run_voice_only
    from tests.test_assistant_voice_only_loop_b1 import _FakeVoice

    fake = _FakeVoice(tmp_path, monkeypatch, ["armar", "salir"])
    monkeypatch.setenv("JARVIS_RECORD_SILENCE_SECONDS", "0")
    run_voice_only()
    out = capsys.readouterr().out
    assert out.count("Jarvis > Grabando 7 s…") == fake.record_count() >= 2
    assert "corta con" not in out
    assert "User > [voz] armar" in out and "vehicle_arm_policy" in out
    assert not any("Grabando" in c for c in fake.captures())


def test_t2_silence_cut_stops_early_with_wav_and_voice_only_continues(tmp_path, monkeypatch, capsys):
    for scenario in ("speech_then_silence", "speech_first"):
        env = _fake_ffmpeg_env(tmp_path, scenario=scenario, silence="1.0")
        done, elapsed, output = _record(tmp_path, env, seconds=5)
        assert done.returncode == 0, f"{scenario}: {done.stderr}"
        assert output.exists() and output.stat().st_size > 0, f"{scenario}: no wav after silence cut"
        assert elapsed < 3, f"{scenario}: expected an early stop, took {elapsed:.2f}s of a 5 s cap"
    args = _ffmpeg_args(tmp_path)
    assert "silencedetect=noise=-35dB:d=1 " in args
    assert "-t 5" in args

    # Default (env unset) is silence mode too.
    env = _fake_ffmpeg_env(tmp_path, scenario="speech_first")
    (tmp_path / "ffmpeg_args.log").unlink()
    done, elapsed, _ = _record(tmp_path, env, seconds=5)
    assert done.returncode == 0 and elapsed < 3
    assert "silencedetect" in _ffmpeg_args(tmp_path)

    # Voice-only end-to-end through the real wrapper: early cut → STT → brain.
    _isolate_workspace(monkeypatch, tmp_path)
    _forbid_keyboard(monkeypatch)
    env = _fake_ffmpeg_env(tmp_path, scenario="speech_then_silence")
    _wire_voice_only_through_real_wrapper(tmp_path, monkeypatch, env, ["armar", "salir"])
    from jarvis.adapters.cli.main import run_voice_only

    start = time.monotonic()
    run_voice_only()
    elapsed = time.monotonic() - start
    out = capsys.readouterr().out
    assert "Jarvis > Grabando (máx 3 s; corta con ~1 s de silencio)…" in out
    assert "User > [voz] armar" in out and "vehicle_arm_policy" in out
    assert "Grabación no disponible" not in out
    assert elapsed < 2 * 3, "two silence-cut turns must finish well before two full 3 s windows"


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="real ffmpeg not installed")
def test_t2b_real_ffmpeg_silencedetect_cut_on_synthetic_source(tmp_path):
    """Same early cut, real ffmpeg: a shim swaps the mic input for a
    real-time lavfi source (0.8 s tone, then silence)."""
    real_ffmpeg = shutil.which("ffmpeg")
    bin_dir = tmp_path / "shimbin"
    bin_dir.mkdir()
    _write_script(
        bin_dir / "ffmpeg",
        "#!/bin/sh\n"
        "NEW=''\n"
        'while [ $# -gt 0 ]; do\n'
        '  case "$1" in\n'
        '    -f) shift 4; NEW="$NEW -re -f lavfi -i sine=frequency=440:duration=0.8,apad"; continue ;;\n'
        "  esac\n"
        '  NEW="$NEW \'$1\'"; shift\n'
        "done\n"
        f'eval exec "{real_ffmpeg}" $NEW\n',
    )
    env = {k: v for k, v in os.environ.items() if not k.startswith("JARVIS_RECORD_")}
    env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
    env["JARVIS_RECORD_SILENCE_SECONDS"] = "0.5"
    done, elapsed, output = _record(tmp_path, env, seconds=6)
    assert done.returncode == 0, done.stderr
    assert output.stat().st_size > 44, "wav must hold audio, not just a header"
    assert elapsed < 4, f"real silencedetect should cut ~1.3 s in, took {elapsed:.2f}s"


def test_t3_max_cap_enforced_even_in_silence_mode(tmp_path):
    # Speech that never stops: no silence_start after sound → runs to the cap.
    env = _fake_ffmpeg_env(tmp_path, scenario="speech_forever", silence="1.0")
    done, elapsed, output = _record(tmp_path, env, seconds=1)
    assert done.returncode == 0, done.stderr
    assert output.stat().st_size > 0
    assert 0.9 <= elapsed < 4
    assert "-t 1" in _ffmpeg_args(tmp_path)

    # Silent room (no speech ever): no early "empty room" cut — waits for the cap.
    env = _fake_ffmpeg_env(tmp_path, scenario="silent_room", silence="1.0")
    done, elapsed, output = _record(tmp_path, env, seconds=2)
    assert done.returncode == 0, done.stderr
    assert output.stat().st_size > 0
    assert elapsed >= 1.9, f"no-speech window must run to the cap, stopped at {elapsed:.2f}s"


def test_t4_bare_chat_never_records_and_missing_record_config_still_ends(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    import jarvis.adapters.voice as voice_module

    def forbidden(*_args, **_kwargs):
        raise AssertionError("bare --chat must never record")

    monkeypatch.setattr(voice_module, "record_audio_file", forbidden)
    queue = ["armar", "exit"]
    monkeypatch.setattr("builtins.input", lambda prompt="": queue.pop(0) if queue else "exit")
    from jarvis.adapters.cli.main import run_chat, run_voice_only

    run_chat()
    out = capsys.readouterr().out
    assert "Grabando" not in out and "vehicle_arm_policy" in out

    monkeypatch.undo()
    _isolate_workspace(monkeypatch, tmp_path)
    _forbid_keyboard(monkeypatch)
    monkeypatch.delenv("JARVIS_RECORD_CMD", raising=False)
    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)
    run_voice_only()
    out = capsys.readouterr().out
    assert "Grabación no disponible" in out
    assert "Sesión cerrada" in out


def test_t5_env_rules_match_script_guide_deps_tip_pin_esc(monkeypatch):
    from jarvis.adapters.cli.main import _record_cue
    from jarvis.adapters.voice import resolve_record_silence_seconds

    # Python resolver and the script's own --check agree on every rule.
    cases = {None: 1.0, "": 0.0, "0": 0.0, "1.5": 1.5, "abc": 1.0, "-2": 1.0}
    for raw, expected in cases.items():
        if raw is None:
            monkeypatch.delenv("JARVIS_RECORD_SILENCE_SECONDS", raising=False)
        else:
            monkeypatch.setenv("JARVIS_RECORD_SILENCE_SECONDS", raw)
        assert resolve_record_silence_seconds() == expected, raw
        if shutil.which("ffmpeg") is not None:
            check = subprocess.run(
                [str(RECORD_WRAPPER), "--check"], capture_output=True, text=True, env=dict(os.environ)
            ).stdout
            if expected == 0:
                assert "silence cut=off" in check, (raw, check)
            else:
                assert f"silence cut={expected:g}s" in check, (raw, check)

    assert _record_cue(7, 0.0) == "Grabando 7 s…"
    assert _record_cue(7, 1.0) == "Grabando (máx 7 s; corta con ~1 s de silencio)…"
    assert _record_cue(5, 1.5) == "Grabando (máx 5 s; corta con ~1.5 s de silencio)…"

    guide = GUIDE.read_text(encoding="utf-8")
    for token in ("JARVIS_RECORD_SILENCE_SECONDS", "JARVIS_RECORD_SECONDS", "silencedetect"):
        assert token in guide, f"guide never mentions {token!r}"

    from tests.test_fase_c_esc_pwm_stub_rung_b1 import _esc_fence_violations
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
    for forbidden in (
        "piper", "whisper", "vosk", "speechrecognition", "pyttsx", "elevenlabs",
        "pyaudio", "sounddevice", "ffmpeg-python", "webrtcvad", "silero", "pydub", "numpy-audio",
    ):
        assert forbidden not in pyproject_text, f"{forbidden!r} leaked into pyproject deps"
    for rel_path in ("src/jarvis/adapters/cli/main.py", "src/jarvis/adapters/voice/external_record.py"):
        source = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        assert not _esc_fence_violations(source), f"{rel_path} forbidden ESC coupling"
    assert "voice" not in typing.get_args(AuthoritySource)
    assert RECORD_WRAPPER.stat().st_mode & stat.S_IXUSR


def test_t6_default_silence_mode_keeps_t53_voice_only_fakes_working(tmp_path, monkeypatch, capsys):
    """Fakes that ignore the silence env (every T53 test) still work
    under the default S=1.0; the cue switches to the silence style and
    is still never spoken."""
    _isolate_workspace(monkeypatch, tmp_path)
    _forbid_keyboard(monkeypatch)
    from jarvis.adapters.cli.main import run_voice_only
    from tests.test_assistant_voice_only_loop_b1 import _FakeVoice

    fake = _FakeVoice(tmp_path, monkeypatch, ["armar", "salir"])
    monkeypatch.delenv("JARVIS_RECORD_SILENCE_SECONDS", raising=False)
    run_voice_only()
    out = capsys.readouterr().out
    assert out.count("Jarvis > Grabando (máx 7 s; corta con ~1 s de silencio)…") == fake.record_count() >= 2
    assert "vehicle_arm_policy" in out and "Sesión cerrada" in out
    assert not any("Grabando" in c or "silencio" in c for c in fake.captures())
