"""Policy guard — tests must not pin exact ``pyproject.toml`` package version.

Engineer (2026-10-01): retire historical tip pins; going forward do not
assert live tip / package version from the suite. Version lives in
``pyproject.toml`` + git tags; behavioral tests cover product truth.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_TESTS = Path(__file__).resolve().parent

# Exact tip-version pin shapes that historically red-lined the suite.
_PIN_PATTERNS = (
    re.compile(r"""assert\s+['\"]version\s*=\s*\"[0-9.]+\"\s*in\s+\w+"""),
    re.compile(r"""assert\s+match\.group\(1\)\s*==\s*['\"][0-9.]+['\"]"""),
    re.compile(r"""def\s+test_\w*pyproject_version_is_\w+\s*\("""),
    re.compile(r"""def\s+test_\w*package_checkpoint_version\s*\("""),
)


def test_no_pyproject_tip_version_pins_in_suite():
    offenders: list[str] = []
    for path in sorted(_TESTS.glob("test_*.py")):
        if path.name == Path(__file__).name:
            continue
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            for pat in _PIN_PATTERNS:
                if pat.search(line):
                    offenders.append(f"{path.name}:{i}: {line.strip()}")
                    break
    assert not offenders, (
        "Tip-version pins are forbidden after suite-tip-pin-cleanup. "
        "Remove the assert / test; do not bump the expected version.\n"
        + "\n".join(offenders)
    )
