"""Tests T1-T6 for `B1-assistant-voice-brief-spanish` (T51).

After T50 closed decoration/`C-rate` noise, the Continuity **brief**
still spoke English engineering labels — `PROJECT STATUS: NOT ASSEMBLY
READY`, gap titles like `Autonomy target not met` (Field Note FN-017).
This Buy humanizes exactly two already-selected brief pieces to
Spanish — the project-status phrase and the top gap title — via a
finite, speak-only map in `brief_spoken_continuity`, plus absorbs the
T50-N1 "El tasa C" article mismatch and fixes the T50-N2 stale `en_GB`
docstring in `external_tts.py`. Same five brief fields/order as T45.
Screen (`render_startup_context`/the readiness block) keeps printing
the English strings verbatim — never touched by this Buy.
"""

from __future__ import annotations

import inspect

from jarvis.adapters.voice import brief_spoken_continuity, sanitize_for_speech


def _ctx(*, overall: str, gap_title: str | None = None) -> dict:
    ctx: dict = {
        "has_project": True,
        "continuity": {
            "situation": "Diseño en curso.",
            "next_useful_step": None,
            "next_useful_why": None,
        },
        "readiness": {"overall": overall, "prioritized_gaps": []},
    }
    if gap_title is not None:
        ctx["readiness"]["prioritized_gaps"] = [{"title": gap_title}]
    return ctx


def test_t1_assembly_ready_speaks_spanish_status_never_english():
    brief = brief_spoken_continuity(_ctx(overall="ASSEMBLY_READY"))
    assert "Estado del proyecto: listo para ensamblar" in brief
    assert "PROJECT STATUS" not in brief
    assert "ASSEMBLY READY" not in brief


def test_t2_not_ready_speaks_spanish_status_never_english():
    brief = brief_spoken_continuity(_ctx(overall="NOT_ASSEMBLY_READY"))
    assert "Estado del proyecto: no listo para ensamblar" in brief
    assert "PROJECT STATUS" not in brief
    assert "ASSEMBLY READY" not in brief


def test_t3_locked_gap_titles_map_to_spanish_unknown_passes_through():
    locked_map = {
        "Autonomy target not met": "Objetivo de autonomía no alcanzado",
        "Mass limit exceeded": "Límite de masa superado",
        "Parameters blocking simulation": "Parámetros bloquean la simulación",
        "Simulation not PASS": "Simulación no en PASS",
        "Architecture block incomplete": "Bloque de arquitectura incompleto",
    }
    for english_title, spanish_title in locked_map.items():
        brief = brief_spoken_continuity(_ctx(overall="NOT_ASSEMBLY_READY", gap_title=english_title))
        assert spanish_title in brief
        assert english_title not in brief

    # Unknown title: honesty over invented translation — spoken raw.
    unknown = "Some brand-new gap title never mapped"
    brief = brief_spoken_continuity(_ctx(overall="NOT_ASSEMBLY_READY", gap_title=unknown))
    assert unknown in brief


def test_t4_sanitize_glossary_never_produces_el_tasa_c():
    result = sanitize_for_speech("El C-rate de la batería")
    assert "la tasa C" in result
    assert "El tasa C" not in result
    assert "el tasa C" not in result

    result_lower = sanitize_for_speech("el c-rate importa mucho")
    assert "la tasa C" in result_lower
    assert "el tasa C" not in result_lower


def test_t5_rendered_wall_still_contains_english_project_status():
    """Layer 1 (print) is untouched — this test proves it against the
    real renderer, not just by grepping `spoken_continuity.py`'s own
    source for the absence of an import."""
    from jarvis.adapters.cli.main import _render_readiness_block

    readiness = {
        "overall": "NOT_ASSEMBLY_READY",
        "subsystems": {},
        "prioritized_gaps": [],
    }
    rendered = "\n".join(_render_readiness_block(readiness))
    assert "PROJECT STATUS: NOT ASSEMBLY READY" in rendered


def test_t6_version_no_speech_deps_tip_pin_and_run_chat_guard():
    from pathlib import Path

    from jarvis.adapters.cli.main import run_chat

    repo_root = Path(__file__).resolve().parents[1]
    pyproject_text = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    # No tip/package version pin here by policy — just confirm no new
    # speech dependency leaked in, same forbidden-list pattern every
    # sibling voice Buy's test uses.
    lowered = pyproject_text.lower()
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
        assert forbidden not in lowered, f"{forbidden!r} leaked into pyproject deps"

    source = inspect.getsource(run_chat)
    for forbidden_symbol in ("speak_egress", "JARVIS_TTS_CMD", "_voice_speak_fn", "TtsError"):
        assert forbidden_symbol not in source, f"run_chat must never reference {forbidden_symbol!r}"
