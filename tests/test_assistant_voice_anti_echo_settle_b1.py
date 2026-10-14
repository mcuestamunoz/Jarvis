"""Tests T1-T5 for `B1-assistant-voice-anti-echo-settle` (T57 / V12).

After Jarvis finishes speaking (or a mid-speech Ctrl-C prints `Habla
cancelada.`), `--voice-only` used to open the mic immediately, so the
tail of its own voice could bleed into the next take. T57 adds a short
fixed pause — `JARVIS_VOICE_SETTLE_SECONDS`, default 0.35; empty/0 =
none; negative/unparseable = default — after the print-only `Grabando`
cue and before the external recorder starts. Plain `time.sleep`: no
VAD, no audio package, `record_turn.sh` untouched. Ctrl-C during the
settle is handled exactly like Ctrl-C while recording (cancel this
take; a second consecutive one ends the session).

Mic/speaker-free: the T53 `_FakeVoice` RECORD/STT/TTS fakes (whose
shared fixture pins the settle to 0 — the tests below set it
explicitly), plus a sleep spy on `jarvis.adapters.cli.main.time` that
writes `SLEEP <s>` into the same event log the fake recorder writes
`REC` to, so ordering is observable.
"""

from __future__ import annotations

import signal
import types
import typing
from pathlib import Path

import jarvis.adapters.cli.main as main_module
import jarvis.workspace.workspace_manager as workspace_manager_module
from jarvis.capabilities.safety import AuthoritySource

REPO_ROOT = Path(__file__).resolve().parents[1]
GUIDE = REPO_ROOT / "docs" / "USER_GUIDE_VOICE.md"


def _setup(tmp_path: Path, monkeypatch, transcripts: list[str], *, settle: str | None, tts: bool = True):
    from tests.test_assistant_voice_only_loop_b1 import _FakeVoice

    monkeypatch.setattr(workspace_manager_module, "DEFAULT_WORKSPACE_ROOT", tmp_path / "workspace")

    def no_keyboard(prompt: str = "") -> str:
        raise AssertionError("voice-only must not read the keyboard without projects")

    monkeypatch.setattr("builtins.input", no_keyboard)
    fake = _FakeVoice(tmp_path, monkeypatch, transcripts, tts=tts)
    if settle is None:
        monkeypatch.delenv("JARVIS_VOICE_SETTLE_SECONDS", raising=False)
    else:
        monkeypatch.setenv("JARVIS_VOICE_SETTLE_SECONDS", settle)
    return fake


def _spy_sleep(monkeypatch, fake, *, raise_on: set[int] | None = None) -> list[float]:
    calls: list[float] = []

    def sleep(seconds: float) -> None:
        calls.append(seconds)
        with fake.events.open("a", encoding="utf-8") as log:
            log.write(f"SLEEP {seconds}\n")
        if raise_on and len(calls) in raise_on:
            raise KeyboardInterrupt

    monkeypatch.setattr(main_module, "time", types.SimpleNamespace(sleep=sleep))
    return calls


def _settle_precedes_every_record(fake, expected: float) -> None:
    lines = fake.event_lines()
    rec_indexes = [i for i, line in enumerate(lines) if line.startswith("REC ")]
    assert rec_indexes, "no recording happened"
    for i in rec_indexes:
        assert i > 0 and lines[i - 1] == f"SLEEP {expected}", f"REC at {i} not preceded by settle: {lines}"


def test_t1_default_settle_before_each_record_and_zero_or_empty_disables(tmp_path, monkeypatch, capsys):
    fake = _setup(tmp_path, monkeypatch, ["armar", "salir"], settle=None)
    calls = _spy_sleep(monkeypatch, fake)
    main_module.run_voice_only()
    assert calls == [0.35] * fake.record_count() and fake.record_count() >= 2
    _settle_precedes_every_record(fake, 0.35)
    out = capsys.readouterr().out
    assert "settle" not in out.lower() and "pausa" not in out.lower(), "cue stays about max/silence only"

    for value in ("0", ""):
        sub = tmp_path / f"disabled_{value or 'empty'}"
        sub.mkdir()
        fake = _setup(sub, monkeypatch, ["armar", "salir"], settle=value)
        calls = _spy_sleep(monkeypatch, fake)
        main_module.run_voice_only()
        assert calls == [], f"JARVIS_VOICE_SETTLE_SECONDS={value!r} must not pause"
        assert fake.record_count() >= 2
    capsys.readouterr()


def test_t2_custom_negative_and_unparseable_values(monkeypatch, tmp_path, capsys):
    from jarvis.adapters.voice import (
        DEFAULT_VOICE_SETTLE_SECONDS,
        resolve_voice_settle_seconds,
    )

    assert DEFAULT_VOICE_SETTLE_SECONDS == 0.35
    for raw, expected in {None: 0.35, "": 0.0, "0": 0.0, "0.5": 0.5, "1": 1.0, "-1": 0.35, "abc": 0.35}.items():
        if raw is None:
            monkeypatch.delenv("JARVIS_VOICE_SETTLE_SECONDS", raising=False)
        else:
            monkeypatch.setenv("JARVIS_VOICE_SETTLE_SECONDS", raw)
        assert resolve_voice_settle_seconds() == expected, raw

    fake = _setup(tmp_path, monkeypatch, ["armar", "salir"], settle="0.5")
    calls = _spy_sleep(monkeypatch, fake)
    main_module.run_voice_only()
    assert calls and all(c == 0.5 for c in calls)
    _settle_precedes_every_record(fake, 0.5)
    capsys.readouterr()


def test_t3_settle_still_applies_after_mid_tts_cancel(tmp_path, monkeypatch, capsys):
    from tests.test_assistant_voice_cancel_mid_tts_b1 import _blocking_tts, _ctrl_c_when

    previous = signal.signal(signal.SIGINT, signal.default_int_handler)
    try:
        fake = _setup(tmp_path, monkeypatch, ["armar", "salir"], settle=None)
        monkeypatch.setenv("JARVIS_TTS_CMD", str(_blocking_tts(tmp_path, block_once=True)))
        _spy_sleep(monkeypatch, fake)
        _ctrl_c_when(tmp_path / "tts_started")
        main_module.run_voice_only()
    finally:
        signal.signal(signal.SIGINT, previous)

    out = capsys.readouterr().out
    assert "Jarvis > Habla cancelada." in out
    lines = [line.split()[0] for line in fake.event_lines()]
    cancelled_tts = lines.index("TTS")
    after = lines[cancelled_tts + 1 :]
    assert after[:2] == ["SLEEP", "REC"], f"next take after the cancel must settle first: {lines}"


def test_t4_ctrl_c_during_settle_and_t53_t54_behaviour_unchanged(tmp_path, monkeypatch, capsys):
    # Ctrl-C during the settle = cancel this take (not the session).
    fake = _setup(tmp_path, monkeypatch, ["armar", "salir"], settle=None, tts=False)
    _spy_sleep(monkeypatch, fake, raise_on={1})
    main_module.run_voice_only()
    out = capsys.readouterr().out
    assert "Grabación cancelada" in out
    assert "User > [voz] armar" in out and out.count("Sesión cerrada") == 1

    # Twice in a row (settle, then settle again) ends the session, like record cancels.
    sub = tmp_path / "double"
    sub.mkdir()
    fake = _setup(sub, monkeypatch, ["armar"], settle=None, tts=False)
    _spy_sleep(monkeypatch, fake, raise_on={1, 2})
    main_module.run_voice_only()
    out = capsys.readouterr().out
    assert out.count("Grabación cancelada") == 1
    assert "Sesión cerrada" in out and "[voz]" not in out
    assert fake.record_count() == 0

    # Bare --chat: no settle, no record.
    monkeypatch.setattr(workspace_manager_module, "DEFAULT_WORKSPACE_ROOT", tmp_path / "chat_ws")
    calls = _spy_sleep(monkeypatch, fake)
    queue = ["armar", "exit"]
    monkeypatch.setattr("builtins.input", lambda prompt="": queue.pop(0) if queue else "exit")
    main_module.run_chat()
    assert calls == []
    assert "Grabando" not in capsys.readouterr().out

    # Silence-cut cue untouched by the settle (T54).
    assert main_module._record_cue(7, 1.0) == "Grabando (máx 7 s; corta con ~1 s de silencio)…"
    assert main_module._record_cue(7, 0.0) == "Grabando 7 s…"


def test_t5_guide_deps_tip_pin_esc():
    guide = GUIDE.read_text(encoding="utf-8")
    assert "JARVIS_VOICE_SETTLE_SECONDS" in guide

    from tests.test_fase_c_esc_pwm_stub_rung_b1 import _esc_fence_violations
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
    for forbidden in (
        "piper", "whisper", "vosk", "speechrecognition", "pyttsx", "elevenlabs",
        "pyaudio", "sounddevice", "ffmpeg-python", "webrtcvad", "silero",
    ):
        assert forbidden not in pyproject_text, f"{forbidden!r} leaked into pyproject deps"
    for rel_path in ("src/jarvis/adapters/cli/main.py", "src/jarvis/adapters/voice/external_record.py"):
        source = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        assert not _esc_fence_violations(source), f"{rel_path} forbidden ESC coupling"
    assert "voice" not in typing.get_args(AuthoritySource)

    # record_turn.sh silence logic untouched by this Buy.
    script = (REPO_ROOT / "scripts" / "voice" / "record_turn.sh").read_text(encoding="utf-8")
    assert "SETTLE" not in script

