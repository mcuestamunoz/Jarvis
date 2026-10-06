"""Tests T1-T6 for `B1-assistant-voice-speak-sanitize` (T50).

A field note on live `--chat --voice-speak`/`--voice` use flagged that
the egress speaks visual-only decoration (rule lines, bullet/checkmark/
tree glyphs, trailing footnote asterisks) and the English-shaped token
`C-rate` badly. This Buy adds a pure, no-LLM `sanitize_for_speech`
function and wires it at the start of `speak_egress` (T38) — the single
seam every spoken egress already passes through, so it covers
`--chat --voice-speak` and `--voice`/`--voice-fixture`/`--voice-audio`
without touching `adapters/cli/main.py`. Layer 1 (everything `print`ed)
is untouched; only what travels on to the external TTS command changes.
"""

from __future__ import annotations

import inspect
import stat
from pathlib import Path

import pytest

from jarvis.adapters.voice.external_tts import TtsConfigError, speak_egress
from jarvis.adapters.voice.speak_sanitize import sanitize_for_speech


def test_t1_decoration_stripped_and_blank_lines_collapsed():
    text = (
        "Antes\n"
        "────────────\n"
        "  • Indicar un motor del catálogo\n"
        "✓ Arquitectura completa (4/4)\n"
        "   └ 2 motores declarados\n"
        "====\n"
        "____\n"
        "\n"
        "\n"
        "\n"
        "Despues"
    )
    result = sanitize_for_speech(text)

    assert "────" not in result
    assert "====" not in result
    assert "____" not in result
    assert "•" not in result
    assert "✓" not in result
    assert "└" not in result
    assert "Indicar un motor del catálogo" in result
    assert "Arquitectura completa (4/4)" in result
    assert "2 motores declarados" in result
    assert "\n\n\n" not in result, "runs of blank lines must collapse to one"
    assert "Antes" in result and "Despues" in result


def test_t1c_heavy_rule_and_tree_glyphs_stripped_but_dash_sign_kept():
    # Heavy box-drawing rule (━) and a tree-listing combo (├── / │) are
    # covered by the same two charsets as ─/•/✓/◇/└.
    assert sanitize_for_speech("Antes\n━━━━━━\nDespues") == "Antes\nDespues"
    assert sanitize_for_speech("├── sub-item") == "sub-item"
    assert sanitize_for_speech("│   └ 2 motores") == "2 motores"
    # A whole rule line of plain ASCII hyphens is decoration and drops —
    # but the leading-marker set never includes "-", so a line that
    # merely *starts* with a hyphen (a negative number, a markdown
    # dash-bullet) keeps its sign/character untouched.
    assert sanitize_for_speech("Antes\n------\nDespues") == "Antes\nDespues"
    assert sanitize_for_speech("-5kg margen") == "-5kg margen"
    assert sanitize_for_speech("- autonomía: 8.9 min") == "- autonomía: 8.9 min"


def test_t1b_trailing_footnote_asterisk_stripped_without_eating_glued_asterisks():
    # The real pattern: "{label:<14} {verdict} *" — a footnote marker
    # preceded by whitespace.
    assert sanitize_for_speech("Control        PASS *") == "Control        PASS"
    # A leading "* " footnote line is covered by the leading-decoration
    # rule (the asterisk is a bullet-style glyph at line start).
    assert (
        sanitize_for_speech("* Control: declaración — sin física de control")
        == "Control: declaración — sin física de control"
    )
    # An asterisk glued directly onto a word with no preceding space is
    # never touched — this sanitizer only strips the footnote-marker
    # shape, never an arbitrary trailing character.
    assert sanitize_for_speech("100%*") == "100%*"


def test_t2_c_rate_glossary_case_insensitive_word_bounded():
    # T51 (B1-assistant-voice-brief-spanish) lock 5 / T50-N1: the
    # glossary resolves to "la tasa C" in every case and absorbs a
    # preceding El/La article so the result is never "El tasa C".
    assert sanitize_for_speech("El C-rate de la batería es 10") == "la tasa C de la batería es 10"
    assert sanitize_for_speech("el c-rate importa") == "la tasa C importa"
    assert sanitize_for_speech("La c-rate es alta") == "la tasa C es alta"
    assert sanitize_for_speech("C-RATE alto") == "la tasa C alto"
    assert "El tasa C" not in sanitize_for_speech("El C-rate de la batería")
    assert "el tasa C" not in sanitize_for_speech("el c-rate importa")
    # Word-bounded — never matches inside a longer token.
    assert "tasa C" not in sanitize_for_speech("recalcular")


def test_t3_project_status_pass_and_gap_titles_untouched():
    """Locked scope: this Buy is a decoration/glossary cleanup only —
    it must never rewrite PROJECT STATUS/PASS/gap-title wording. That
    is explicitly a later Buy's job (T51/T52), not T50's."""
    wall_fragment = (
        "PROJECT STATUS: ASSEMBLY READY\n"
        "\n"
        "TOP GAPS\n"
        "\n"
        "GAP-001\n"
        "  Battery capacity below mission requirement\n"
        "  HIGH — blocks: endurance\n"
    )
    result = sanitize_for_speech(wall_fragment)
    assert "PROJECT STATUS: ASSEMBLY READY" in result
    assert "TOP GAPS" in result
    assert "GAP-001" in result
    assert "Battery capacity below mission requirement" in result
    assert "HIGH — blocks: endurance" in result


def test_t4_empty_or_decoration_only_sanitizes_to_empty_string():
    assert sanitize_for_speech("") == ""
    assert sanitize_for_speech("   \n  \n   ") == ""
    assert sanitize_for_speech("────\n• \n✓\n") == ""


def test_t4b_speak_egress_is_a_silent_noop_when_sanitized_text_is_empty(monkeypatch):
    # No JARVIS_TTS_CMD configured at all — if sanitize_for_speech did
    # not short-circuit, this would raise TtsConfigError. It must not:
    # there is nothing to say, so there is nothing to misconfigure.
    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)
    speak_egress("────\n• \n")  # no exception
    speak_egress("")  # no exception

    # Sanity check the config error still fires for real, non-empty text.
    with pytest.raises(TtsConfigError):
        speak_egress("texto real")


def test_t5_speak_egress_wiring_sends_sanitized_text_to_the_external_command(tmp_path: Path):
    received_path = tmp_path / "received.log"
    script = tmp_path / "fake_tts.sh"
    script.write_text(f"#!/bin/sh\ncat >> {received_path}\n", encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)

    decorated = "  • Indicar motor\n✓ Listo\nEl C-rate importa\n────\n"
    speak_egress(decorated, command_template=str(script))

    received = received_path.read_text(encoding="utf-8")
    assert received == sanitize_for_speech(decorated)
    assert "•" not in received
    assert "✓" not in received
    assert "────" not in received
    assert "tasa C" in received
    assert "C-rate" not in received


def test_t6_run_chat_and_layer_1_renderers_never_reference_the_sanitizer():
    """T42's structural guard stays green, and Layer 1 (print) is
    provably untouched: `run_chat` and every print-side renderer this
    Buy was told to prefer not editing never import or name the speak
    sanitizer."""
    from jarvis.adapters.cli.main import render_response, render_startup_context, run_chat
    from jarvis.adapters.voice.spoken_continuity import spoken_text_for_wall

    run_chat_source = inspect.getsource(run_chat)
    for forbidden in ("speak_egress", "JARVIS_TTS_CMD", "_voice_speak_fn", "TtsError"):
        assert forbidden not in run_chat_source, f"run_chat must never reference {forbidden!r}"
    assert "speak_sanitize" not in run_chat_source
    assert "sanitize_for_speech" not in run_chat_source

    for renderer in (render_response, render_startup_context, spoken_text_for_wall):
        source = inspect.getsource(renderer)
        assert "speak_sanitize" not in source
        assert "sanitize_for_speech" not in source
