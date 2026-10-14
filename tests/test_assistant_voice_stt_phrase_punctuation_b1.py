"""Tests T1-T6 for `B1-assistant-voice-stt-phrase-punctuation` (T55 / V11).

whisper returns `Completo.` / `Estado.` / `¿Armar?`. Before T55 the
voice-only exit check already ignored that punctuation, but the FULL
phrase match (`spoken_continuity._normalize`) and the Skill-first phrase
matcher (`assistant_task._normalize_for_continuity_match`) were exact —
so `Completo.` spoke the brief instead of FULL, and `Estado.` missed the
Continuity wall. T55 strips the finite edge-punctuation set `.,;:!?¡¿`
(both ends — `¿completo?` needs the leading `¿` gone) after the existing
strip/casefold/NFKD steps. Phrase tables are unchanged and nothing is
fuzzy: `completos` still does not match `completo`.

Engineer-confirmed scope: `_normalize_for_continuity_match` is shared by
every Skill-first kind, so ARM/DISARM/HOLD/LAND/GO_TO/… also accept
STT punctuation now (T2 pins that explicitly). T55 also removes the dead
T47 push-to-talk helpers (`is_ptt_trigger`, `PTT_TRIGGER_PHRASES`).

Mic-free: string-level checks plus T53's `_FakeVoice` RECORD/STT/TTS.
"""

from __future__ import annotations

import inspect
import typing
from pathlib import Path

import jarvis.workspace.workspace_manager as workspace_manager_module
from jarvis.capabilities.intent import Task, TerminalIntentAdapter
from jarvis.capabilities.safety import AuthoritySource
from jarvis.config import CONTINUITY_DEFER_PHRASES
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.intelligence.assistant_task import (
    TASK_KIND_DEFER_TO_CONTINUITY,
    TASK_KIND_REQUEST_ARM_POLICY,
    TASK_KIND_REQUEST_HOLD,
    _normalize_for_continuity_match,
    parse_go_to_destination,
    try_defer_to_continuity_task,
    try_request_arm_policy_task,
    try_request_hold_task,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
GUIDE = REPO_ROOT / "docs" / "USER_GUIDE_VOICE.md"


def _isolate_workspace(monkeypatch, tmp_path: Path) -> Path:
    workspace_root = tmp_path / "workspace"
    monkeypatch.setattr(workspace_manager_module, "DEFAULT_WORKSPACE_ROOT", workspace_root)
    return workspace_root


def _seed_fat_project(workspace_root: Path) -> None:
    JarvisOrchestrator(workspace_root=workspace_root).handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "t55 punctuation fixture",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })


def _voice_only(tmp_path: Path, monkeypatch, transcripts: list[str], *, picker: str | None):
    from jarvis.adapters.cli.main import run_voice_only
    from tests.test_assistant_voice_only_loop_b1 import _FakeVoice

    fake = _FakeVoice(tmp_path, monkeypatch, transcripts)
    queue = [picker] if picker else []

    def keyboard(prompt: str = "") -> str:
        if not queue:
            raise AssertionError("keyboard only for the project picker")
        return queue.pop(0)

    monkeypatch.setattr("builtins.input", keyboard)
    run_voice_only()
    return fake


def test_t1_full_phrase_ignores_edge_punctuation_not_fuzzy():
    from jarvis.adapters.voice import is_full_continuity_request

    for raw in ("Completo.", "completo!", "¿completo?", "¡Completo!", "completo .", "Dame detalles.", "dame detalles..."):
        assert is_full_continuity_request(raw), raw
    for raw in ("completos", "completo ya", "muy completo", "detalles"):
        assert not is_full_continuity_request(raw), raw


def test_t2_defer_and_skill_matchers_ignore_edge_punctuation(tmp_path, monkeypatch, capsys):
    # Continuity defer: same Task as the bare phrase.
    for raw in ("Estado.", "estado?", "¿Estado?", "estado"):
        assert _normalize_for_continuity_match(raw) in CONTINUITY_DEFER_PHRASES, raw
        intent = TerminalIntentAdapter.parse(raw)
        task = try_defer_to_continuity_task(intent)
        assert isinstance(task, Task), raw
        assert intent.metadata.get("task_kind") == TASK_KIND_DEFER_TO_CONTINUITY
    assert try_defer_to_continuity_task(TerminalIntentAdapter.parse("estados")) is None

    # Engineer-confirmed widening: every Skill-first kind shares the normalize.
    intent = TerminalIntentAdapter.parse("Armar.")
    assert isinstance(try_request_arm_policy_task(intent), Task)
    assert intent.metadata.get("task_kind") == TASK_KIND_REQUEST_ARM_POLICY
    intent = TerminalIntentAdapter.parse("¿Hold?")
    assert isinstance(try_request_hold_task(intent), Task)
    assert intent.metadata.get("task_kind") == TASK_KIND_REQUEST_HOLD
    assert try_request_arm_policy_task(TerminalIntentAdapter.parse("armado.")) is None
    assert parse_go_to_destination("Go to 1 2.") == (1.0, 2.0)
    assert parse_go_to_destination("ir a 1.5 -2.5?") == (1.5, -2.5)

    # End to end: STT "Estado." reaches the Continuity wall, not the LLM.
    workspace_root = _isolate_workspace(monkeypatch, tmp_path)
    _seed_fat_project(workspace_root)
    fake = _voice_only(tmp_path, monkeypatch, ["Estado.", "Salir."], picker="1")
    out = capsys.readouterr().out
    assert "User > [voz] Estado." in out
    assert out.count("ENGINEERING READINESS") >= 2, "load wall + the 'Estado.' wall"
    assert sum("Estado del proyecto: no listo para ensamblar" in c for c in fake.captures()) >= 2


def test_t3_payloads_unchanged_full_narrated_brief_brief(tmp_path, monkeypatch, capsys):
    workspace_root = _isolate_workspace(monkeypatch, tmp_path)
    _seed_fat_project(workspace_root)

    fake = _voice_only(tmp_path, monkeypatch, ["Completo.", "estado?", "salir"], picker="1")

    out = capsys.readouterr().out
    assert out.count("ENGINEERING READINESS") >= 3  # screen: full wall every time (Layer 1)
    captures = fake.captures()
    full = [c for c in captures if "Huecos prioritarios" in c]
    assert len(full) == 1, "'Completo.' speaks the narrated FULL extract exactly once"
    for capture in captures:
        for screen_only in ("ENGINEERING READINESS", "TOP GAPS", "PROJECT STATUS"):
            assert screen_only not in capture
    # load + "estado?" stay brief (no FULL body)
    assert sum("Estado del proyecto" in c and "Huecos prioritarios" not in c for c in captures) >= 2


def test_t4_voice_only_exit_still_punctuation_tolerant_and_chat_silent(tmp_path, monkeypatch, capsys):
    from jarvis.adapters.cli.main import _is_voice_only_exit, run_chat

    for raw in ("Salir.", "salir!", "¿Salir?", "EXIT", "quit."):
        assert _is_voice_only_exit(raw), raw
    assert not _is_voice_only_exit("salirme")

    _isolate_workspace(monkeypatch, tmp_path)
    _voice_only(tmp_path, monkeypatch, ["salir!"], picker=None)
    assert "Sesión cerrada" in capsys.readouterr().out

    import jarvis.adapters.voice as voice_module

    def forbidden(*_args, **_kwargs):
        raise AssertionError("bare --chat must never record or speak")

    for name in ("record_audio_file", "transcribe_audio_file", "speak_egress"):
        monkeypatch.setattr(voice_module, name, forbidden)
    queue = ["Estado.", "exit"]
    monkeypatch.setattr("builtins.input", lambda prompt="": queue.pop(0) if queue else "exit")
    run_chat()
    out = capsys.readouterr().out
    assert "Grabando" not in out and "[voz]" not in out


def test_t5_dead_ptt_helpers_gone_and_no_hablar_intercept():
    import jarvis.adapters.voice as voice_module
    import jarvis.adapters.voice.external_record as external_record
    from jarvis.adapters.cli.main import _run_chat_session, run_chat

    for name in ("is_ptt_trigger", "PTT_TRIGGER_PHRASES"):
        assert not hasattr(voice_module, name), name
        assert name not in voice_module.__all__, name
        assert not hasattr(external_record, name), name
    for fn in (run_chat, _run_chat_session):
        source = inspect.getsource(fn)
        assert "is_ptt_trigger" not in source
        assert '"hablar"' not in source


def test_t6_guide_deps_tip_pin_esc():
    guide = GUIDE.read_text(encoding="utf-8")
    assert "puntuación" in guide and "Completo." in guide

    from tests.test_fase_c_esc_pwm_stub_rung_b1 import _esc_fence_violations
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
    for forbidden in (
        "piper", "whisper", "vosk", "speechrecognition", "pyttsx", "elevenlabs",
        "pyaudio", "sounddevice", "ffmpeg-python", "webrtcvad", "rapidfuzz", "fuzzywuzzy",
    ):
        assert forbidden not in pyproject_text, f"{forbidden!r} leaked into pyproject deps"
    for rel_path in (
        "src/jarvis/adapters/voice/spoken_continuity.py",
        "src/jarvis/adapters/voice/external_record.py",
        "src/jarvis/intelligence/assistant_task.py",
    ):
        source = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        assert not _esc_fence_violations(source), f"{rel_path} forbidden ESC coupling"
    assert "voice" not in typing.get_args(AuthoritySource)
