"""Tests T1-T6 for `B1-assistant-chat-spoken-continuity` (T45).

T43 made `--chat --voice-speak` speak every printed `Jarvis > …` string
verbatim — including the full Continuity wall on project load and on
`estado`. T44-inv mapped the wall's fields; T44-DC locked a two-layer
plan: Layer 1 (print) stays the full wall, untouched; Layer 2 (speak)
becomes a deterministic brief extract on wall turns only, unless the
user's line is one of the locked FULL phrases, in which case the wall
itself is spoken that turn only (no session latch). No LLM anywhere in
this layer.

Isolation note: same pattern as `test_assistant_chat_voice_speak_b1.py`
— `run_chat()` takes no `workspace_root`, so these tests monkeypatch the
module-level `DEFAULT_WORKSPACE_ROOT` that `WorkspaceManager.__init__`
reads. A "fat" project (one with a blocking/incomplete Continuity state)
is seeded directly via `JarvisOrchestrator.handle({"action":
"create_project", ...})`, bypassing the interactive wizard, so its
`render_startup_context` wall actually contains an ENGINEERING READINESS
block and TOP GAPS to distinguish "wall" from "brief" unambiguously. The
fake TTS is a tiny shell script that records what it received — the
same pattern every prior voice test file uses. No Piper/whisper/
speaker/mic is ever required.
"""

from __future__ import annotations

import stat
import typing
from pathlib import Path

import jarvis.workspace.workspace_manager as workspace_manager_module
from jarvis.capabilities.safety import AuthoritySource
from jarvis.core.orchestrator import JarvisOrchestrator


def _isolate_workspace(monkeypatch, tmp_path: Path) -> Path:
    workspace_root = tmp_path / "workspace"
    monkeypatch.setattr(workspace_manager_module, "DEFAULT_WORKSPACE_ROOT", workspace_root)
    return workspace_root


def _seed_fat_project(workspace_root: Path) -> None:
    """A project with a blocking/incomplete Continuity state — its
    `render_startup_context` wall includes an ENGINEERING READINESS
    block, TOP GAPS, and a block-closure line, which the brief extract
    must never leak."""
    seed = JarvisOrchestrator(workspace_root=workspace_root)
    seed.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "t45 spoken continuity fixture",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })


def _write_fake_tts_script(tmp_path: Path, received_path: Path) -> Path:
    script = tmp_path / "fake_tts.sh"
    script.write_text(
        f"#!/bin/sh\ncat >> {received_path}\nprintf '\\n---\\n' >> {received_path}\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script


def _feed_lines(monkeypatch, lines: list[str]):
    queue = list(lines)

    def fake_input(prompt: str = "") -> str:
        if not queue:
            raise EOFError
        return queue.pop(0)

    monkeypatch.setattr("builtins.input", fake_input)


_WALL_MARKERS = ("ENGINEERING READINESS", "Componentes / gaps", "Evidencia:")


def test_t1_brief_spoken_continuity_excludes_wall_detail():
    from jarvis.adapters.voice import brief_spoken_continuity

    fat_ctx = {
        "has_project": True,
        "continuity": {
            "situation": "Diseño bloqueado: faltan parámetros físicos para simular con rigor.",
            "next_useful_step": "¿Definimos motor_count y per_motor_max_thrust_n ahora?",
            "next_useful_why": "missing_propulsion_parameters",
            "evidence": ["Simulación: fail — calidad fail — margen 0.00"],
            "explain_topics": ["c-rate"],
        },
        "component_bom_lines": ["Motor: definido", "Bateria: GAP"],
        "physical_requirements_lines": ["Requisito: >= 1 N/motor"],
        "readiness": {
            "overall": "NOT_ASSEMBLY_READY",
            "subsystems": {"requirements": {"verdict": "INCOMPLETE"}},
            "prioritized_gaps": [
                {
                    "gap_id": "GAP-SIM-NOT-PASS",
                    "title": "Simulation not PASS",
                    "severity": "HIGH",
                    "blocks": ["requirements"],
                    "depends_on": [],
                    "recommended_next_step": {"action": "fix_simulation_blocker"},
                },
            ],
        },
        "prop_energy_block_closure": {"status": "not_closed", "facts": {}},
    }

    brief = brief_spoken_continuity(fat_ctx)

    assert "Diseño bloqueado" in brief
    assert "¿Definimos motor_count" in brief
    # T51 (`B1-assistant-voice-brief-spanish`): the brief speaks Spanish
    # status/gap-title phrases; the English readiness strings stay
    # screen-only (print side, unchanged, tested separately).
    assert "Estado del proyecto: no listo para ensamblar" in brief
    assert "PROJECT STATUS" not in brief
    assert "Simulación no en PASS" in brief
    for marker in _WALL_MARKERS:
        assert marker not in brief, f"brief leaked wall-only content: {marker!r}"
    assert "BLOQUE PROPULSIÓN" not in brief


def test_t2_chat_wall_prints_full_but_speaks_brief(tmp_path, monkeypatch, capsys):
    workspace_root = _isolate_workspace(monkeypatch, tmp_path)
    _seed_fat_project(workspace_root)
    from jarvis.adapters.cli.main import run_chat

    received = tmp_path / "received.log"
    script = _write_fake_tts_script(tmp_path, received)
    monkeypatch.setenv("JARVIS_TTS_CMD", str(script))
    _feed_lines(monkeypatch, ["1", "estado", "exit"])

    run_chat(speak_tts=True)

    out = capsys.readouterr().out
    for marker in _WALL_MARKERS[:1]:  # ENGINEERING READINESS must be on screen
        assert marker in out, "print side must still show the full wall"
    assert "TOP GAPS" in out

    # The turn sequence also opens the auto-define wizard (a non-wall,
    # speak-as-printed turn) between the two wall turns — assert on
    # content, not a fixed capture index, so this test doesn't depend on
    # exactly how many non-wall turns happen to land in between.
    captures = [c for c in received.read_text(encoding="utf-8").split("---\n") if c.strip()]
    assert len(captures) >= 2
    for capture in captures:
        for marker in _WALL_MARKERS:
            assert marker not in capture, f"TTS received wall-only content: {marker!r}"
    # T51: the brief now speaks Spanish ("Estado del proyecto: ...")
    # instead of the English "PROJECT STATUS: ..." line.
    assert any("Estado del proyecto: no listo para ensamblar" in c for c in captures), (
        "at least one wall turn (project-load or estado) must have spoken the brief"
    )
    assert sum("Estado del proyecto: no listo para ensamblar" in c for c in captures) >= 2, (
        "both wall turns (project-load and estado) must have spoken the brief"
    )


def test_t3_full_phrase_speaks_the_wall_verbatim(tmp_path, monkeypatch, capsys):
    workspace_root = _isolate_workspace(monkeypatch, tmp_path)
    _seed_fat_project(workspace_root)
    from jarvis.adapters.cli.main import run_chat

    received = tmp_path / "received.log"
    script = _write_fake_tts_script(tmp_path, received)
    monkeypatch.setenv("JARVIS_TTS_CMD", str(script))
    _feed_lines(monkeypatch, ["1", "completo", "exit"])

    run_chat(speak_tts=True)

    out = capsys.readouterr().out
    assert "ENGINEERING READINESS" in out  # print side unaffected either way

    captures = [c for c in received.read_text(encoding="utf-8").split("---\n") if c.strip()]
    # Exactly one capture (the "completo" turn) carries the full wall;
    # the project-load turn and any wizard-opener stay brief/short.
    full_captures = [c for c in captures if "ENGINEERING READINESS" in c]
    assert len(full_captures) == 1, f"expected exactly one full-wall capture, got {len(full_captures)}"
    assert "TOP GAPS" in full_captures[0]


def test_t3b_full_phrase_dame_detalles_also_speaks_the_wall(tmp_path, monkeypatch):
    workspace_root = _isolate_workspace(monkeypatch, tmp_path)
    _seed_fat_project(workspace_root)
    from jarvis.adapters.cli.main import run_chat

    received = tmp_path / "received.log"
    script = _write_fake_tts_script(tmp_path, received)
    monkeypatch.setenv("JARVIS_TTS_CMD", str(script))
    _feed_lines(monkeypatch, ["1", "dame detalles", "exit"])

    run_chat(speak_tts=True)

    captures = [c for c in received.read_text(encoding="utf-8").split("---\n") if c.strip()]
    full_captures = [c for c in captures if "ENGINEERING READINESS" in c]
    assert len(full_captures) == 1, f"expected exactly one full-wall capture, got {len(full_captures)}"


def test_t4_short_skill_turn_still_speaks_as_printed_and_bare_chat_is_silent(
    tmp_path, monkeypatch, capsys
):
    workspace_root = _isolate_workspace(monkeypatch, tmp_path)
    from jarvis.adapters.cli.main import run_chat

    received = tmp_path / "received.log"
    script = _write_fake_tts_script(tmp_path, received)
    monkeypatch.setenv("JARVIS_TTS_CMD", str(script))
    _feed_lines(monkeypatch, ["armar", "exit"])

    run_chat(speak_tts=True)

    out = capsys.readouterr().out
    assert "vehicle_arm_policy" in out
    captures = [c for c in received.read_text(encoding="utf-8").split("---\n") if c.strip()]
    assert len(captures) >= 1
    assert any("vehicle_arm_policy" in c or "ARMADA" in c for c in captures)

    # Bare --chat (default speak_tts=False): same two turns, no TTS call at all.
    received.unlink()
    monkeypatch.setattr(workspace_manager_module, "DEFAULT_WORKSPACE_ROOT", workspace_root.parent / "ws2")
    _feed_lines(monkeypatch, ["armar", "exit"])
    run_chat()
    assert not received.exists(), "bare --chat must never invoke JARVIS_TTS_CMD"


def test_t5_missing_tts_config_is_honest_and_wall_turn_survives(tmp_path, monkeypatch, capsys):
    workspace_root = _isolate_workspace(monkeypatch, tmp_path)
    _seed_fat_project(workspace_root)
    from jarvis.adapters.cli.main import run_chat

    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)
    _feed_lines(monkeypatch, ["1", "estado", "completo", "exit"])

    run_chat(speak_tts=True)

    out = capsys.readouterr().out
    assert out.count("TTS no disponible") >= 3
    assert "ENGINEERING READINESS" in out
    assert "Sesión cerrada" in out


def test_t6_no_tip_pins_no_speech_deps_esc_fence_green_guide_and_map_updated():
    from tests.test_fase_c_esc_pwm_stub_rung_b1 import _esc_fence_violations
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()

    repo_root = Path(__file__).resolve().parents[1]
    pyproject_text = (repo_root / "pyproject.toml").read_text(encoding="utf-8").lower()
    for forbidden in ("piper", "whisper", "vosk", "speechrecognition", "pyttsx", "elevenlabs", "pyaudio"):
        assert forbidden not in pyproject_text, f"{forbidden!r} leaked into pyproject deps"

    for rel_path in (
        "src/jarvis/core/orchestrator.py",
        "src/jarvis/adapters/voice/fixture_loop.py",
        "src/jarvis/adapters/voice/external_stt.py",
        "src/jarvis/adapters/voice/external_tts.py",
        "src/jarvis/adapters/voice/spoken_continuity.py",
        "src/jarvis/adapters/cli/main.py",
    ):
        source = (repo_root / rel_path).read_text(encoding="utf-8")
        violations = _esc_fence_violations(source)
        assert not violations, f"{rel_path} forbidden ESC coupling: {violations}"

    assert "voice" not in typing.get_args(AuthoritySource)

    guide = (repo_root / "docs" / "USER_GUIDE_VOICE.md").read_text(encoding="utf-8")
    assert "completo" in guide
    assert "dame detalles" in guide

    living_map = repo_root / ".jes" / "artifacts" / "engineer_note_chat_spoken_continuity_map.md"
    assert living_map.exists()
