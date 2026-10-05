"""Tests T1-T4 for `B1-assistant-voice-tts-spanish` (T49).

T48-inv Q8 found the shipped default demo TTS voice (`en_GB-alan-medium`)
mismatched against every Skill/Continuity/chat reply, which is Spanish
prose. This Buy flips the *documentation default* only — the T38 Piper
seam (`scripts/voice/piper_tts.sh`) was already fully model-agnostic via
`JARVIS_PIPER_MODEL`, so there is no `src/jarvis` change here. These
tests assert the new default appears in the brief/guide/script comment,
that `en_GB-alan-medium` is still documented as a legacy/optional voice
(not deleted), and that no speech dependency or tip-pinned voice-model
file was added anywhere in the repo.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BRIEF = REPO_ROOT / ".jes" / "artifacts" / "engineer_note_voice_tts_product_brief.md"
GUIDE = REPO_ROOT / "docs" / "USER_GUIDE_VOICE.md"
PIPER_SCRIPT = REPO_ROOT / "scripts" / "voice" / "piper_tts.sh"
PYPROJECT = REPO_ROOT / "pyproject.toml"


def test_t1_brief_defaults_to_spanish_davefx_with_legacy_en_gb():
    text = BRIEF.read_text(encoding="utf-8")
    assert "es_ES-davefx-medium" in text
    assert "es_ES-sharvard-medium" in text
    # en_GB stays documented, but demoted — never deleted from the brief.
    assert "en_GB-alan-medium" in text
    assert "legacy" in text.lower()


def test_t2_guide_sections_default_to_davefx_es_es():
    text = GUIDE.read_text(encoding="utf-8")

    # Section 2 (install) and section 3 (env config) both reference the
    # Spanish default path, not just a passing mention.
    assert "es_ES-davefx-medium.onnx" in text
    assert "es/es_ES/davefx/medium/" in text
    assert 'JARVIS_PIPER_MODEL="$HOME/piper/es_ES-davefx-medium.onnx"' in text

    # Cheatsheet (section 7) also defaults to davefx.
    cheatsheet_start = text.index("Cheatsheet")
    cheatsheet = text[cheatsheet_start : cheatsheet_start + 2000]
    assert "es_ES-davefx-medium" in cheatsheet

    # en_GB-alan-medium still named, but as the documented legacy choice,
    # not as *the* default install example anymore.
    assert "en_GB-alan-medium" in text
    assert "legacy" in text.lower() or "original" in text.lower()

    # Whisper STT example for Spanish hablar/PTT prefers a multilingual
    # model over the English-only ggml-base.en.bin.
    assert "ggml-base.bin" in text


def test_t3_piper_script_body_still_model_agnostic():
    text = PIPER_SCRIPT.read_text(encoding="utf-8")

    # Comment header may name the new Spanish default example.
    assert "es_ES-davefx-medium" in text

    # The executable body (non-comment lines) must still read the model
    # path from the environment, never a hardcoded voice-model filename
    # (the body may still mention ".onnx" generically, e.g. in an error
    # message telling the operator what kind of file to point at).
    body_lines = [line for line in text.splitlines() if not line.strip().startswith("#")]
    body = "\n".join(body_lines)
    assert "JARVIS_PIPER_MODEL" in body
    for hardcoded_voice in ("davefx", "sharvard", "alan-medium", "northern_english_male"):
        assert hardcoded_voice not in body, f"piper_tts.sh body must never hardcode voice {hardcoded_voice!r}"


def test_t4_no_speech_deps_or_tip_pinned_models():
    # No tip/package version pin here by policy (see
    # test_suite_no_tip_version_pins_b1.py) — the version lives in
    # pyproject.toml + git tags, not in an assertion that would need
    # bumping every time a sibling Buy opens the next package version.
    pyproject_text = PYPROJECT.read_text(encoding="utf-8")

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

    # No tip-pinned voice-model binary anywhere in the repo (excluding .git).
    found = subprocess.run(
        ["find", str(REPO_ROOT), "-name", "*.onnx", "-not", "-path", "*/.git/*"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert found.stdout.strip() == "", f"unexpected .onnx file(s) committed: {found.stdout}"
