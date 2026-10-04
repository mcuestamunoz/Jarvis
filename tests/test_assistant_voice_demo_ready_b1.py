"""Tests T1-T5 for `B1-assistant-voice-demo-ready` (T41).

Operator demo path for voice: a user guide plus external wrapper scripts
that let the Engineer actually **use** Jarvis with spoken replies. No new
`src/` seam — T35-T39's surface is reused as-is.

These tests never require Piper, whisper, a voice model, or a speaker to
be installed. The wrappers' honesty paths (missing config / missing
binary) are asserted directly, and their happy-path plumbing is proven
against a **stub** `piper` that mimics the real Piper 1.x CLI contract.
"""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GUIDE = REPO_ROOT / "docs" / "USER_GUIDE_VOICE.md"
VOICE_SCRIPTS = REPO_ROOT / "scripts" / "voice"
TTS_WRAPPER = VOICE_SCRIPTS / "piper_tts.sh"
STT_WRAPPER = VOICE_SCRIPTS / "whisper_stt.sh"
DEMO_FIXTURE = VOICE_SCRIPTS / "fixtures" / "demo_skills.txt"

# Phrases the demo fixture may legitimately use — every one is a declared
# Skill-first phrase (or a T32 prove-now GO_TO destination line).
_SKILL_PREFIXES = (
    "explain ",
    "estado",
    "armar",
    "desarmar",
    "hold",
    "land",
    "go to",
    "takeoff",
    "return home",
    "rtl",
    "follow",
    "patrol",
    "charge",
)


def _is_executable(path: Path) -> bool:
    return bool(path.stat().st_mode & stat.S_IXUSR)


def _run_wrapper(script: Path, *args: str, env: dict | None = None, stdin: str = ""):
    merged = dict(os.environ)
    # Never let an operator's real voice config leak into these tests.
    for leaky in (
        "JARVIS_PIPER_MODEL",
        "JARVIS_PIPER_BIN",
        "JARVIS_PIPER_ARGS",
        "JARVIS_VOICE_WAV_OUT",
        "JARVIS_VOICE_PLAYER",
        "JARVIS_WHISPER_MODEL",
        "JARVIS_WHISPER_BIN",
        "JARVIS_WHISPER_ARGS",
    ):
        merged.pop(leaky, None)
    if env:
        merged.update(env)
    return subprocess.run(
        [str(script), *args],
        input=stdin,
        capture_output=True,
        text=True,
        env=merged,
    )


def test_t1_user_guide_exists_with_env_names_and_sections():
    assert GUIDE.exists(), f"missing operator guide: {GUIDE}"
    text = GUIDE.read_text(encoding="utf-8")

    # Env / flag names the guide must actually teach.
    for token in (
        "JARVIS_TTS_CMD",
        "JARVIS_STT_CMD",
        "JARVIS_PIPER_MODEL",
        "--voice-speak",
        "--voice-fixture",
        "--voice-audio",
        "Piper",
        "en_GB-alan-medium",
    ):
        assert token in text, f"guide never mentions {token!r}"

    # Structure in the spirit of USER_GUIDE_EXPLAIN.md.
    for heading in (
        "## 1. Qué es y qué no es",
        "## 6. Honestidad",
        "## 7. Cheatsheet",
        "## 8. Límites conocidos",
    ):
        assert heading in text, f"guide missing section {heading!r}"

    # The guide must say the vendor binaries stay outside the package.
    assert "fuera del paquete" in text or "fuera de este repo" in text


def test_t2_wrapper_scripts_exist_executable_with_shebang():
    for script in (TTS_WRAPPER, STT_WRAPPER):
        assert script.exists(), f"missing wrapper: {script}"
        assert _is_executable(script), f"wrapper not executable: {script}"
        body = script.read_text(encoding="utf-8")
        assert body.startswith("#!"), f"wrapper missing shebang: {script}"

    tts_body = TTS_WRAPPER.read_text(encoding="utf-8")
    assert "JARVIS_PIPER_MODEL" in tts_body
    assert "Piper" in tts_body

    stt_body = STT_WRAPPER.read_text(encoding="utf-8")
    assert "JARVIS_WHISPER_MODEL" in stt_body


def test_t3_demo_fixture_has_at_least_three_skill_lines():
    assert DEMO_FIXTURE.exists(), f"missing demo fixture: {DEMO_FIXTURE}"
    lines = [
        line.strip()
        for line in DEMO_FIXTURE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(lines) >= 3, f"demo fixture needs >= 3 non-empty lines, got {len(lines)}"
    for line in lines:
        assert line.startswith(_SKILL_PREFIXES), (
            f"fixture line {line!r} is not a declared Skill-first phrase"
        )


def test_t3b_demo_fixture_runs_through_the_voice_loop(tmp_path: Path):
    """The checked-in fixture must actually drive real Skill turns — a
    stale phrase would otherwise sit in the repo looking valid."""
    from jarvis.adapters.voice import FixtureSttSource, run_voice
    from jarvis.core.orchestrator import JarvisOrchestrator

    class _ExplodingLLMInterface:
        def interpret(self, *args, **kwargs):
            raise AssertionError("llm must not be called for a Skill-first phrase")

        def analyze(self, *args, **kwargs):
            raise AssertionError("llm must not be called for a Skill-first phrase")

        def complete(self, *args, **kwargs):
            raise AssertionError("llm must not be called for a Skill-first phrase")

    orch = JarvisOrchestrator(workspace_root=tmp_path)
    turns = run_voice(orch, _ExplodingLLMInterface(), FixtureSttSource.from_path(DEMO_FIXTURE))

    assert len(turns) >= 3
    for text, result, egress in turns:
        assert result.get("action"), f"{text!r} produced no action"
        assert egress, f"{text!r} produced empty egress"


def test_t4_no_speech_deps_tip_pin_and_esc_fences_green():
    from tests.test_fase_c_esc_pwm_stub_rung_b1 import _esc_fence_violations
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()

    # No speech vendor may become a package dependency via this Buy.
    # (The package version itself is deliberately NOT asserted here: that
    # exact shape is one of T17's own forbidden tip-pin patterns.)
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
    for forbidden in (
        "piper",
        "whisper",
        "vosk",
        "speechrecognition",
        "pyttsx",
        "elevenlabs",
        "pyaudio",
    ):
        assert forbidden not in pyproject_text, f"{forbidden!r} leaked into pyproject deps"

    # Voice adapters stay untouched by this Buy; fences still green.
    for rel_path in (
        "src/jarvis/core/orchestrator.py",
        "src/jarvis/adapters/voice/fixture_loop.py",
        "src/jarvis/adapters/voice/external_stt.py",
        "src/jarvis/adapters/voice/external_tts.py",
        "src/jarvis/adapters/cli/main.py",
    ):
        source = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        violations = _esc_fence_violations(source)
        assert not violations, f"{rel_path} forbidden ESC coupling: {violations}"


def test_t5_wrappers_fail_clearly_without_config_or_binary(tmp_path: Path):
    """No silent success: every missing piece is a non-zero exit with a
    message on stderr. Requires no Piper, no whisper, no speaker."""
    # TTS: no model configured at all.
    done = _run_wrapper(TTS_WRAPPER, stdin="hola")
    assert done.returncode != 0
    assert "JARVIS_PIPER_MODEL" in done.stderr

    # TTS: --check is a config probe that speaks nothing and still fails loudly.
    done = _run_wrapper(TTS_WRAPPER, "--check")
    assert done.returncode != 0
    assert "JARVIS_PIPER_MODEL" in done.stderr

    # TTS: model path that does not exist.
    done = _run_wrapper(
        TTS_WRAPPER, env={"JARVIS_PIPER_MODEL": str(tmp_path / "nope.onnx")}, stdin="hola"
    )
    assert done.returncode != 0
    assert "not found" in done.stderr

    # TTS: model present but Piper binary missing.
    model = tmp_path / "voice.onnx"
    model.write_bytes(b"")
    done = _run_wrapper(
        TTS_WRAPPER,
        env={
            "JARVIS_PIPER_MODEL": str(model),
            "JARVIS_PIPER_BIN": "definitely_not_piper_xyz",
        },
        stdin="hola",
    )
    assert done.returncode != 0
    assert "not found" in done.stderr

    # STT: a missing audio argument is reported before anything else.
    done = _run_wrapper(STT_WRAPPER, str(tmp_path / "absent.wav"))
    assert done.returncode != 0
    assert "audio file not found" in done.stderr

    # STT: audio present, but no model configured.
    audio = tmp_path / "turn.wav"
    audio.write_bytes(b"")
    done = _run_wrapper(STT_WRAPPER, str(audio))
    assert done.returncode != 0
    assert "JARVIS_WHISPER_MODEL" in done.stderr

    # STT: no audio argument at all.
    whisper_model = tmp_path / "model.bin"
    whisper_model.write_bytes(b"")
    done = _run_wrapper(STT_WRAPPER, env={"JARVIS_WHISPER_MODEL": str(whisper_model)})
    assert done.returncode != 0
    assert "usage" in done.stderr


def test_t5b_tts_wrapper_plumbing_against_a_stub_piper(tmp_path: Path):
    """Prove the wrapper's real contract — egress text arrives on the
    synthesizer's stdin intact, and a wav is produced — without needing
    Piper installed. The stub mimics Piper 1.x's `--model/--output_file`
    CLI; it is not a claim that a specific Piper build was exercised."""
    received = tmp_path / "received.txt"
    stub = tmp_path / "piper"
    stub.write_text(
        "#!/bin/sh\n"
        'OUT=""\n'
        'while [ $# -gt 0 ]; do case "$1" in --output_file) OUT="$2"; shift 2;; *) shift;; esac; done\n'
        f'cat > "{received}"\n'
        'printf "RIFF....WAVEfake" > "$OUT"\n',
        encoding="utf-8",
    )
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)

    model = tmp_path / "voice.onnx"
    model.write_bytes(b"")
    wav_out = tmp_path / "spoken.wav"

    spoken = 'HOLD solicitado — con "comillas" y espacios.'
    done = _run_wrapper(
        TTS_WRAPPER,
        env={
            "JARVIS_PIPER_MODEL": str(model),
            "JARVIS_PIPER_BIN": str(stub),
            "JARVIS_VOICE_WAV_OUT": str(wav_out),
        },
        stdin=spoken,
    )

    assert done.returncode == 0, f"wrapper failed: {done.stderr}"
    assert received.read_text(encoding="utf-8").strip() == spoken
    assert wav_out.exists() and wav_out.stat().st_size > 0

    # A synthesizer that exits 0 but writes no audio must NOT be reported
    # as success.
    silent_stub = tmp_path / "piper_silent"
    silent_stub.write_text(
        "#!/bin/sh\n"
        'OUT=""\n'
        'while [ $# -gt 0 ]; do case "$1" in --output_file) OUT="$2"; shift 2;; *) shift;; esac; done\n'
        "cat > /dev/null\n"
        ': > "$OUT"\n',
        encoding="utf-8",
    )
    silent_stub.chmod(silent_stub.stat().st_mode | stat.S_IEXEC)
    done = _run_wrapper(
        TTS_WRAPPER,
        env={
            "JARVIS_PIPER_MODEL": str(model),
            "JARVIS_PIPER_BIN": str(silent_stub),
            "JARVIS_VOICE_WAV_OUT": str(tmp_path / "empty.wav"),
        },
        stdin="hola",
    )
    assert done.returncode != 0
    assert "no audio" in done.stderr


def test_t5c_stt_wrapper_prints_bare_transcript_on_stdout(tmp_path: Path):
    """T37's seam reads stdout as the transcript — so the wrapper must put
    the transcript there and nothing else, with engine noise on stderr."""
    stub = tmp_path / "whisper-cli"
    stub.write_text(
        "#!/bin/sh\n"
        'echo "whisper_init: loading model (noise that must not reach stdout)" >&2\n'
        "printf '\\n  hold  \\n'\n",
        encoding="utf-8",
    )
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)

    model = tmp_path / "model.bin"
    model.write_bytes(b"")
    audio = tmp_path / "turn.wav"
    audio.write_bytes(b"")

    done = _run_wrapper(
        STT_WRAPPER,
        str(audio),
        env={"JARVIS_WHISPER_MODEL": str(model), "JARVIS_WHISPER_BIN": str(stub)},
    )
    assert done.returncode == 0, f"wrapper failed: {done.stderr}"
    assert done.stdout.strip() == "hold"
    assert "noise" not in done.stdout

    # An empty transcript is a failure, never an empty "success".
    silent = tmp_path / "whisper_silent"
    silent.write_text("#!/bin/sh\nprintf '\\n   \\n'\n", encoding="utf-8")
    silent.chmod(silent.stat().st_mode | stat.S_IEXEC)
    done = _run_wrapper(
        STT_WRAPPER,
        str(audio),
        env={"JARVIS_WHISPER_MODEL": str(model), "JARVIS_WHISPER_BIN": str(silent)},
    )
    assert done.returncode != 0
    assert "empty transcript" in done.stderr
