"""Tests T1-T7 for `B1-assistant-voice-full-spoken` (T52).

Field Note FN-017: asking `completo` (a locked FULL phrase) spoke the
printed Continuity wall verbatim — OCR-style speech of the readiness
table, gap ids, BOM lines and English labels. This Buy changes only the
FULL **speak** payload: `spoken_text_for_wall` now returns
`full_spoken_continuity(ctx)` — the T51 brief (unchanged) plus a narrated
body (A evidence · B top-3 gaps · C architecture · D physical
requirements · E propulsion/energy block state), each section omitted
when empty. The printed wall (Layer 1) is untouched; BOM, the subsystem
table, Conceptos, propulsion/hover/endurance detail and the English
`PROJECT STATUS` line stay screen-only even on FULL. No LLM.
"""

from __future__ import annotations

import inspect
import re
import stat
import typing
from pathlib import Path

import jarvis.workspace.workspace_manager as workspace_manager_module
from jarvis.adapters.voice import (
    brief_spoken_continuity,
    full_spoken_continuity,
    spoken_text_for_wall,
)
from jarvis.capabilities.safety import AuthoritySource
from jarvis.core.orchestrator import JarvisOrchestrator


def _fat_ctx() -> dict:
    return {
        "has_project": True,
        "project_slug": "t52-fixture",
        "continuity": {
            "situation": "Diseño bloqueado: faltan parámetros físicos para simular con rigor.",
            "next_useful_step": "¿Definimos motor_count ahora?",
            "next_useful_why": None,
            "evidence": [f"Evidencia número {i}" for i in range(1, 9)],
            "explain_topics": ["c-rate"],
        },
        "component_bom_lines": ["Motor: definido SKU-BOM-123", "Bateria: GAP"],
        "physical_requirements_lines": ["Empuje requerido: 17.66 N", "Masa actual: 1.5 kg"],
        "architecture_progress": "3/7",
        "next_architecture_label": "Propulsión",
        "next_block_status": "in_progress",
        "propulsion_resolution": {
            "resolution_type": "fallback_operating_point",
            "source_type": "manufacturer_test",
            "thrust_n": 9.5,
        },
        "hover_energy": {"source_type": "unverifiable", "power_w": None},
        "readiness": {
            "overall": "NOT_ASSEMBLY_READY",
            "subsystems": {"requirements": {"verdict": "INCOMPLETE"}},
            "prioritized_gaps": [
                {
                    "gap_id": "GAP-SIM-NOT-PASS",
                    "title": "Simulation not PASS",
                    "severity": "HIGH",
                    "blocks": ["requirements"],
                    "depends_on": ["GAP-PARAMS"],
                    "recommended_next_step": {"action": "fix_simulation_blocker"},
                },
                {
                    "gap_id": "GAP-ARCH",
                    "title": "Architecture block incomplete",
                    "severity": "MEDIUM",
                    "blocks": ["structure"],
                    "depends_on": [],
                    "recommended_next_step": {"action": "continue_architecture_block"},
                },
                {
                    "gap_id": "GAP-NEW",
                    "title": "Brand-new unmapped gap",
                    "severity": "LOW",
                    "blocks": [],
                    "depends_on": [],
                    "recommended_next_step": {},
                },
                {
                    "gap_id": "GAP-FOURTH",
                    "title": "Mass limit exceeded",
                    "severity": "LOW",
                    "blocks": [],
                    "depends_on": [],
                    "recommended_next_step": {"action": "fourth_action"},
                },
            ],
        },
        "prop_energy_block_closure": {"status": "not_closed", "facts": {}},
    }


def test_t1_full_speaks_brief_head_spanish_status_never_english():
    ctx = _fat_ctx()
    full = spoken_text_for_wall("completo", "irrelevant printed wall", ctx)

    assert full == full_spoken_continuity(ctx)
    assert full.startswith(brief_spoken_continuity(ctx) + "\n")
    assert "Estado del proyecto: no listo para ensamblar" in full
    assert "PROJECT STATUS" not in full
    assert "ASSEMBLY READY" not in full
    # Locked body order after the brief head (T52-DC A-E).
    order = [
        "Evidencia:",
        "Huecos prioritarios:",
        "Arquitectura 3/7.",
        "Requisitos físicos:",
        "Bloque propulsión y energía:",
    ]
    positions = [full.index(marker) for marker in order]
    assert positions == sorted(positions), f"body sections out of order: {positions}"


def test_t2_evidence_capped_at_six_and_header_omitted_when_empty():
    ctx = _fat_ctx()
    full = full_spoken_continuity(ctx)
    assert "Evidencia:" in full
    for i in range(1, 7):
        assert f"Evidencia número {i}" in full
    assert "Evidencia número 7" not in full
    assert "Evidencia número 8" not in full

    ctx["continuity"]["evidence"] = []
    assert "Evidencia:" not in full_spoken_continuity(ctx)

    # Every A-E section empty -> FULL is the brief head alone; no project -> "".
    minimal = {
        "has_project": True,
        "continuity": {"situation": "Diseño en curso."},
        "readiness": {"overall": "ASSEMBLY_READY", "prioritized_gaps": []},
    }
    assert full_spoken_continuity(minimal) == brief_spoken_continuity(minimal)
    assert full_spoken_continuity(None) == ""
    assert full_spoken_continuity({"has_project": False}) == ""


def test_t3_gaps_top3_spanish_titles_action_only_never_ids():
    ctx = _fat_ctx()
    ctx["readiness"]["prioritized_gaps"][0]["title"] = "Autonomy target not met"
    full = full_spoken_continuity(ctx)
    body = full.split("Huecos prioritarios:", 1)[1]

    assert "Objetivo de autonomía no alcanzado" in body
    assert "Bloque de arquitectura incompleto" in body
    assert "Brand-new unmapped gap" in body  # unknown title: honest passthrough
    assert "Siguiente: resolver el bloqueo de simulación" in body
    assert "Siguiente: continuar el bloque de arquitectura" in body
    assert "fix_simulation_blocker" not in full
    assert "continue_architecture_block" not in full
    # Fourth gap is beyond the top-3 cap.
    assert "Límite de masa superado" not in full
    assert "fourth_action" not in full
    # Never gap_id / depends_on / severity / blocks.
    assert "GAP-" not in full
    for forbidden in (
        "depends_on",
        "HIGH",
        "MEDIUM",
        "LOW",
        "blocks:",
        "Autonomy target not met",
        "Architecture block incomplete",
    ):
        assert forbidden not in full, f"FULL spoke screen-only gap detail: {forbidden!r}"


def test_t4_full_differs_from_printed_wall_and_estado_stays_brief():
    from jarvis.adapters.cli.main import render_startup_context

    ctx = _fat_ctx()
    printed_wall = render_startup_context(ctx)
    assert len(printed_wall.splitlines()) > 10  # a long Continuity print

    assert spoken_text_for_wall("completo", printed_wall, ctx) != printed_wall
    assert spoken_text_for_wall("dame detalles", printed_wall, ctx) == full_spoken_continuity(ctx)
    assert spoken_text_for_wall("estado", printed_wall, ctx) == brief_spoken_continuity(ctx)
    assert "Huecos prioritarios:" not in spoken_text_for_wall("estado", printed_wall, ctx)


def test_t5_screen_only_fence_and_print_still_shows_it():
    from jarvis.adapters.cli.main import _render_readiness_block, render_startup_context

    ctx = _fat_ctx()
    ctx["readiness"]["subsystems"] = {
        "requirements": {"verdict": "INCOMPLETE"},
        "control": {"verdict": "PASS"},
    }
    full = spoken_text_for_wall("completo", render_startup_context(ctx), ctx)
    for screen_only in (
        "ENGINEERING READINESS",
        "TOP GAPS",
        "PROJECT STATUS",
        "Componentes / gaps",
        "Motor: definido SKU-BOM-123",
        "SKU-BOM-123",
        "Bateria: GAP",
        "Conceptos",
        "Propulsión (evidencia)",
        "fallback_operating_point",
        "BLOQUE PROPULSIÓN/ENERGÍA",
        "INCOMPLETE",
        "─",
    ):
        assert screen_only not in full, f"FULL spoke screen-only content: {screen_only!r}"
    assert not re.search(r"^\S+\s+PASS\b", full, flags=re.M), "subsystem PASS table row leaked"

    # Layer 1 untouched: the real renderers still print the screen truth.
    printed_wall = render_startup_context(ctx)
    assert "Componentes / gaps:" in printed_wall
    assert "SKU-BOM-123" in printed_wall
    readiness_block = "\n".join(_render_readiness_block(ctx["readiness"]))
    assert "PROJECT STATUS: NOT ASSEMBLY READY" in readiness_block


def test_t6_architecture_and_block_closure_templates():
    ctx = _fat_ctx()
    assert "Arquitectura 3/7. Siguiente bloque: Propulsión en progreso" in full_spoken_continuity(ctx)

    ctx["next_block_status"] = "pending"
    full = full_spoken_continuity(ctx)
    assert "Arquitectura 3/7. Siguiente bloque: Propulsión" in full
    assert "en progreso" not in full

    ctx["next_architecture_label"] = None
    ctx["architecture_progress"] = "7/7"
    assert "Arquitectura 7/7. Completa." in full_spoken_continuity(ctx)

    ctx["architecture_progress"] = None
    assert "Arquitectura" not in full_spoken_continuity(ctx)

    assert "Bloque propulsión y energía: no cerrado." in full_spoken_continuity(ctx)
    ctx["prop_energy_block_closure"] = {"status": "closed", "evidence_tier": "manufacturer_test"}
    full = full_spoken_continuity(ctx)
    assert "Bloque propulsión y energía: cerrado." in full
    assert "manufacturer_test" not in full

    ctx["prop_energy_block_closure"] = None
    assert "Bloque propulsión" not in full_spoken_continuity(ctx)

    # T52-N1: unknown action codes pass through raw (honesty).
    ctx["readiness"]["prioritized_gaps"] = [{
        "title": "Brand-new unmapped gap",
        "recommended_next_step": {"action": "some_unknown_action"},
    }]
    assert "Siguiente: some_unknown_action" in full_spoken_continuity(ctx)


def _write_fake_tts_script(tmp_path: Path, received_path: Path) -> Path:
    script = tmp_path / "fake_tts.sh"
    script.write_text(
        f"#!/bin/sh\ncat >> {received_path}\nprintf '\\n---\\n' >> {received_path}\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script


def test_t7_run_chat_completo_prints_wall_speaks_narrated_full_and_guards(
    tmp_path, monkeypatch, capsys
):
    workspace_root = tmp_path / "workspace"
    monkeypatch.setattr(workspace_manager_module, "DEFAULT_WORKSPACE_ROOT", workspace_root)
    JarvisOrchestrator(workspace_root=workspace_root).handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "t52 full spoken fixture",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })
    from jarvis.adapters.cli.main import run_chat

    received = tmp_path / "received.log"
    monkeypatch.setenv("JARVIS_TTS_CMD", str(_write_fake_tts_script(tmp_path, received)))
    queue = ["1", "completo", "exit"]
    monkeypatch.setattr("builtins.input", lambda prompt="": queue.pop(0) if queue else (_ for _ in ()).throw(EOFError))

    run_chat(speak_tts=True)

    out = capsys.readouterr().out
    assert "ENGINEERING READINESS" in out
    assert "TOP GAPS" in out

    captures = [c for c in received.read_text(encoding="utf-8").split("---\n") if c.strip()]
    full_captures = [c for c in captures if "Huecos prioritarios" in c]
    assert len(full_captures) == 1
    assert "Estado del proyecto: no listo para ensamblar" in full_captures[0]
    assert "Bloque propulsión y energía" in full_captures[0]
    for capture in captures:
        for screen_only in ("ENGINEERING READINESS", "TOP GAPS", "PROJECT STATUS", "depends_on"):
            assert screen_only not in capture

    # Guards: tip-pin policy, ESC fence, no speech deps, no LLM in the
    # extractor, run_chat TTS source guard, run_chat untouched by this Buy.
    from tests.test_fase_c_esc_pwm_stub_rung_b1 import _esc_fence_violations
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()

    repo_root = Path(__file__).resolve().parents[1]
    pyproject_text = (repo_root / "pyproject.toml").read_text(encoding="utf-8").lower()
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
    ):
        assert forbidden not in pyproject_text, f"{forbidden!r} leaked into pyproject deps"
    for rel_path in (
        "src/jarvis/adapters/voice/spoken_continuity.py",
        "src/jarvis/adapters/cli/main.py",
    ):
        source = (repo_root / rel_path).read_text(encoding="utf-8")
        assert not _esc_fence_violations(source), f"{rel_path} forbidden ESC coupling"
    assert "voice" not in typing.get_args(AuthoritySource)

    import jarvis.adapters.voice.spoken_continuity as spoken_continuity_module

    source = inspect.getsource(spoken_continuity_module).lower()
    for forbidden in ("anthropic", "openai", "llm_client", "import requests"):
        assert forbidden not in source
    run_chat_source = inspect.getsource(run_chat)
    for forbidden_symbol in ("speak_egress", "JARVIS_TTS_CMD", "_voice_speak_fn", "TtsError"):
        assert forbidden_symbol not in run_chat_source, f"run_chat must never reference {forbidden_symbol!r}"
    assert "full_spoken_continuity" not in run_chat_source
    assert "spoken_text_for_wall(user_input, startup_block, startup_ctx)" in run_chat_source

    guide = (repo_root / "docs" / "USER_GUIDE_VOICE.md").read_text(encoding="utf-8")
    assert "full_spoken_continuity" in guide
    assert "narrada" in guide
    living_map = (
        repo_root / ".jes" / "artifacts" / "engineer_note_chat_spoken_continuity_map.md"
    ).read_text(encoding="utf-8")
    assert "full_spoken_continuity" in living_map
