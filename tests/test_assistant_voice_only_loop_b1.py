"""Tests T1-T8 for `B1-assistant-voice-only-loop` (T53 / V9).

V9-DC collapses the product to exactly two daily modes: `--chat`
(keyboard, silent) and `--voice-only` (the same full chat brain, mic by
default, every reply spoken). No typed `hablar` trigger: the mic opens
when the session is ready for a user turn and again after each spoken
reply returns. The hybrid `--chat --voice-speak` and the Skills-only
interactive `--voice` REPL are retired with an honest pointer and a
non-zero exit; `--voice-fixture`/`--voice-audio` stay as batch/CI.

Isolation: `run_chat`/`run_voice_only` take no `workspace_root`, so —
like every sibling chat test — these monkeypatch the module-level
`DEFAULT_WORKSPACE_ROOT`. RECORD/STT/TTS are tiny shell scripts that
append to one shared event log, so ordering (record never overlaps
speak) is observable. No real mic, Piper, or whisper anywhere.
"""

from __future__ import annotations

import inspect
import re
import stat
import sys
import typing
from pathlib import Path

import pytest

import jarvis.workspace.workspace_manager as workspace_manager_module
from jarvis.capabilities.safety import AuthoritySource
from jarvis.core.orchestrator import JarvisOrchestrator

REPO_ROOT = Path(__file__).resolve().parents[1]
GUIDE = REPO_ROOT / "docs" / "USER_GUIDE_VOICE.md"
LIVING_MAP = REPO_ROOT / ".jes" / "artifacts" / "engineer_note_chat_spoken_continuity_map.md"


def _isolate_workspace(monkeypatch, tmp_path: Path) -> Path:
    workspace_root = tmp_path / "workspace"
    monkeypatch.setattr(workspace_manager_module, "DEFAULT_WORKSPACE_ROOT", workspace_root)
    return workspace_root


def _seed_fat_project(workspace_root: Path) -> None:
    JarvisOrchestrator(workspace_root=workspace_root).handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "t53 voice-only fixture",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })


def _write_script(tmp_path: Path, name: str, body: str) -> Path:
    script = tmp_path / name
    script.write_text(body, encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script


class _FakeVoice:
    """Fake RECORD/STT/TTS wired through the real env seams.

    - RECORD logs `REC <wav path>` and writes placeholder wav bytes.
    - STT pops the next queued transcript (falls back to `salir` when
      the queue runs dry, so a test can never spin forever).
    - TTS logs `TTS` and appends stdin to `spoken.log`.
    """

    def __init__(self, tmp_path: Path, monkeypatch, transcripts: list[str], *, tts: bool = True):
        self.events = tmp_path / "events.log"
        self.spoken = tmp_path / "spoken.log"
        self.queue = tmp_path / "stt_queue.txt"
        self.queue.write_text("".join(f"{line}\n" for line in transcripts), encoding="utf-8")
        record = _write_script(
            tmp_path,
            "fake_record.sh",
            f'#!/bin/sh\necho "REC $1" >> "{self.events}"\nprintf \'RIFF....WAVEfake\' > "$1"\n',
        )
        stt = _write_script(
            tmp_path,
            "fake_stt.sh",
            "#!/bin/sh\n"
            f'Q="{self.queue}"\n'
            'LINE=$(head -n 1 "$Q")\n'
            'tail -n +2 "$Q" > "$Q.tmp"; mv "$Q.tmp" "$Q"\n'
            'if [ -z "$LINE" ]; then LINE=salir; fi\n'
            'printf "%s\\n" "$LINE"\n',
        )
        monkeypatch.setenv("JARVIS_RECORD_CMD", f"{record} {{output}} {{seconds}}")
        monkeypatch.setenv("JARVIS_STT_CMD", f"{stt} {{audio}}")
        if tts:
            speak = _write_script(
                tmp_path,
                "fake_tts.sh",
                f'#!/bin/sh\necho "TTS" >> "{self.events}"\n'
                f'cat >> "{self.spoken}"\nprintf \'\\n---\\n\' >> "{self.spoken}"\n',
            )
            monkeypatch.setenv("JARVIS_TTS_CMD", str(speak))
        else:
            monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)

    def event_lines(self) -> list[str]:
        if not self.events.exists():
            return []
        return self.events.read_text(encoding="utf-8").splitlines()

    def record_count(self) -> int:
        return sum(line.startswith("REC ") for line in self.event_lines())

    def captures(self) -> list[str]:
        if not self.spoken.exists():
            return []
        return [c for c in self.spoken.read_text(encoding="utf-8").split("---\n") if c.strip()]


def _forbid_keyboard(monkeypatch):
    def no_keyboard(prompt: str = "") -> str:
        raise AssertionError("voice-only must not read the keyboard after startup")

    monkeypatch.setattr("builtins.input", no_keyboard)


def _keyboard_once(monkeypatch, line: str) -> list[str]:
    calls: list[str] = []

    def fake_input(prompt: str = "") -> str:
        if calls:
            raise AssertionError("voice-only read the keyboard more than once (picker only)")
        calls.append(prompt)
        return line

    monkeypatch.setattr("builtins.input", fake_input)
    return calls


def test_t1_voice_only_transcript_runs_full_chat_brain_and_speaks(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    fake = _FakeVoice(tmp_path, monkeypatch, ["armar", "salir"])
    _forbid_keyboard(monkeypatch)

    import jarvis.adapters.voice as voice_module

    def skills_only_forbidden(*_args, **_kwargs):
        raise AssertionError("voice-only must not route through Skills-only run_voice_turn")

    monkeypatch.setattr(voice_module, "run_voice_turn", skills_only_forbidden)
    from jarvis.adapters.cli.main import run_voice_only

    run_voice_only()

    out = capsys.readouterr().out
    assert "User > [voz] armar" in out
    assert "vehicle_arm_policy" in out
    assert "Sesión cerrada" in out
    captures = fake.captures()
    assert any("vehicle_arm_policy" in c or "ARMADA" in c for c in captures), "reply was not spoken"
    # "Grabando…" is a print-only cue — never spoken.
    assert not any("Grabando" in c for c in captures)


def test_t2_mic_reopens_after_each_spoken_reply_never_during_tts(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    fake = _FakeVoice(tmp_path, monkeypatch, ["armar", "salir"])
    _forbid_keyboard(monkeypatch)
    from jarvis.adapters.cli.main import run_voice_only

    run_voice_only()

    out = capsys.readouterr().out
    assert fake.record_count() >= 2
    assert out.count("Jarvis > Grabando 7 s…") == fake.record_count()
    events = [line.split()[0] for line in fake.event_lines()]
    first_rec, second_rec = [i for i, e in enumerate(events) if e == "REC"][:2]
    assert "TTS" in events[first_rec + 1 : second_rec], "second record must follow the spoken reply"

    # Ephemeral audio: every temp wav handed to RECORD is gone afterwards.
    wav_paths = [Path(line.split(" ", 1)[1]) for line in fake.event_lines() if line.startswith("REC ")]
    assert wav_paths and all(p.suffix == ".wav" for p in wav_paths)
    assert not any(p.exists() for p in wav_paths)
    assert not list((tmp_path / "workspace").rglob("*.wav"))


def test_t3_bare_chat_never_records_or_speaks(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    import jarvis.adapters.voice as voice_module

    def forbidden(*_args, **_kwargs):
        raise AssertionError("bare --chat must never record, transcribe, or speak")

    for name in ("record_audio_file", "transcribe_audio_file", "speak_egress"):
        monkeypatch.setattr(voice_module, name, forbidden)
    queue = ["armar", "hablar", "exit"]
    monkeypatch.setattr("builtins.input", lambda prompt="": queue.pop(0) if queue else "exit")
    from jarvis.adapters.cli.main import run_chat

    assert "speak_tts" not in inspect.signature(run_chat).parameters
    run_chat()

    out = capsys.readouterr().out
    assert "vehicle_arm_policy" in out
    assert "Grabando" not in out
    assert "[voz]" not in out
    assert "TTS no disponible" not in out
    from jarvis.adapters.cli.main import _run_chat_session

    for fn in (run_chat, _run_chat_session):
        assert "is_ptt_trigger" not in inspect.getsource(fn), "PTT intercept must be gone from chat"


def _run_main(monkeypatch, argv: list[str]):
    from jarvis.adapters.cli import main as main_module

    def no_session(*_args, **_kwargs):
        raise AssertionError("a retired mode must not open any chat/voice session")

    for name in ("run_chat", "run_voice_only", "run_demo", "run_voice_fixture", "run_voice_audio"):
        monkeypatch.setattr(main_module, name, no_session)
    monkeypatch.setattr(sys, "argv", ["jarvis", *argv])
    with pytest.raises(SystemExit) as exit_info:
        main_module.main()
    return exit_info.value.code


def test_t4_chat_voice_speak_hybrid_is_rejected_with_pointer(monkeypatch, capsys):
    assert _run_main(monkeypatch, ["--chat", "--voice-speak"]) == 2
    err = capsys.readouterr().err
    assert "--voice-only" in err

    assert _run_main(monkeypatch, ["--voice-speak"]) == 2
    assert "--voice-only" in capsys.readouterr().err

    assert _run_main(monkeypatch, ["--chat", "--voice-only"]) == 2


def test_t5_missing_config_is_honest_failures_reopen_mic_ctrl_c_cancels(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    _forbid_keyboard(monkeypatch)
    from jarvis.adapters.cli.main import run_voice_only

    # Missing RECORD config: honest, session ends cleanly (no endless retry).
    monkeypatch.delenv("JARVIS_RECORD_CMD", raising=False)
    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)
    run_voice_only()
    out = capsys.readouterr().out
    assert "Grabación no disponible" in out
    assert "Sesión cerrada" in out
    assert "[voz]" not in out

    # RECORD fine, missing STT config: honest, ends cleanly, wav cleaned up.
    fake = _FakeVoice(tmp_path, monkeypatch, [], tts=False)
    monkeypatch.delenv("JARVIS_STT_CMD", raising=False)
    run_voice_only()
    out = capsys.readouterr().out
    assert "STT no disponible" in out
    assert "Sesión cerrada" in out
    assert "[voz]" not in out
    assert not any(
        Path(line.split(" ", 1)[1]).exists() for line in fake.event_lines() if line.startswith("REC ")
    )

    # Failing STT process / Ctrl-C mid-record: that turn only; mic reopens.
    import jarvis.adapters.voice as voice_module

    fake = _FakeVoice(tmp_path, monkeypatch, ["armar", "salir."], tts=False)
    real_record = voice_module.record_audio_file
    calls = {"n": 0}

    def flaky_record(output_path, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise KeyboardInterrupt
        if calls["n"] == 2:
            raise voice_module.RecordProcessError("mic busy")
        return real_record(output_path, **kwargs)

    monkeypatch.setattr(voice_module, "record_audio_file", flaky_record)
    run_voice_only()
    out = capsys.readouterr().out
    assert "Grabación cancelada" in out
    assert "Grabación no disponible: mic busy" in out
    assert "User > [voz] armar" in out
    assert "TTS no disponible" in out  # missing TTS is honest, loop survived
    assert "User > [voz] salir." in out and "Sesión cerrada" in out

    # Two consecutive Ctrl-C while recording end the session.
    def always_interrupt(output_path, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(voice_module, "record_audio_file", always_interrupt)
    run_voice_only()
    out = capsys.readouterr().out
    assert out.count("Grabación cancelada") == 1
    assert "Sesión cerrada" in out


def test_t6_continuity_walls_print_full_speak_layer2_keyboard_only_for_picker(
    tmp_path, monkeypatch, capsys
):
    workspace_root = _isolate_workspace(monkeypatch, tmp_path)
    _seed_fat_project(workspace_root)
    fake = _FakeVoice(tmp_path, monkeypatch, ["estado", "completo", "salir"])
    keyboard_calls = _keyboard_once(monkeypatch, "1")
    from jarvis.adapters.cli.main import run_voice_only

    run_voice_only()

    out = capsys.readouterr().out
    assert len(keyboard_calls) == 1
    assert "Elige proyecto con el teclado" in out
    assert out.count("ENGINEERING READINESS") >= 3  # load + estado + completo: full wall on screen
    assert "User > [voz] estado" in out and "User > [voz] completo" in out

    captures = fake.captures()
    for capture in captures:
        for screen_only in ("ENGINEERING READINESS", "TOP GAPS", "PROJECT STATUS"):
            assert screen_only not in capture, f"spoke screen-only wall content: {screen_only!r}"
    assert sum("Estado del proyecto: no listo para ensamblar" in c for c in captures) >= 3
    full_captures = [c for c in captures if "Huecos prioritarios" in c]
    assert len(full_captures) == 1, "only the 'completo' turn speaks the narrated FULL extract"


def test_t7_voice_retired_fixture_kept_no_deps_tip_pin_esc(tmp_path, monkeypatch, capsys):
    from tests.test_fase_c_esc_pwm_stub_rung_b1 import _esc_fence_violations
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    assert _run_main(monkeypatch, ["--voice"]) == 2
    assert "--voice-only" in capsys.readouterr().err
    import jarvis.adapters.cli.main as main_module

    monkeypatch.undo()
    assert not hasattr(main_module, "run_voice_interactive")

    # Batch/CI fixture path still runs (Skills-only seam kept for CI).
    _isolate_workspace(monkeypatch, tmp_path)
    fixture = tmp_path / "turns.txt"
    fixture.write_text("armar\n", encoding="utf-8")
    main_module.run_voice_fixture(str(fixture))
    assert "vehicle_arm_policy" in capsys.readouterr().out

    test_no_pyproject_tip_version_pins_in_suite()
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
    for forbidden in (
        "piper",
        "whisper",
        "vosk",
        "speechrecognition",
        "pyttsx",
        "elevenlabs",
        "pyaudio",
        "sounddevice",
        "ffmpeg-python",
        "webrtcvad",
    ):
        assert forbidden not in pyproject_text, f"{forbidden!r} leaked into pyproject deps"
    for rel_path in (
        "src/jarvis/adapters/cli/main.py",
        "src/jarvis/adapters/voice/external_record.py",
        "src/jarvis/adapters/voice/external_stt.py",
        "src/jarvis/adapters/voice/external_tts.py",
    ):
        source = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        assert not _esc_fence_violations(source), f"{rel_path} forbidden ESC coupling"
    assert "voice" not in typing.get_args(AuthoritySource)

    # No second brain, no background thread, no VAD in the voice-only loop.
    loop_source = inspect.getsource(main_module._make_mic_line_reader) + inspect.getsource(
        main_module.run_voice_only
    )
    for forbidden in ("import threading", "Thread(", "run_voice_turn(", "webrtcvad"):
        assert forbidden not in loop_source, f"voice-only loop references {forbidden!r}"


def test_t8_guide_teaches_two_modes_only_and_map_updated():
    guide = GUIDE.read_text(encoding="utf-8")
    assert "--chat" in guide
    assert "--voice-only" in guide
    assert "--chat --voice-speak" not in guide
    assert "`hablar`" not in guide and "`habla`" not in guide
    assert "User > hablar" not in guide
    assert not re.search(r"--voice(?![-\w])", guide), "guide still teaches interactive --voice"

    living_map = LIVING_MAP.read_text(encoding="utf-8")
    assert "run_voice_only" in living_map
    assert "Modo voz:" in living_map
    assert "Grabación cancelada" in living_map
