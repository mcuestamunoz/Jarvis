"""jarvis board — thin visor launcher. Does not start Vite in these tests."""
from __future__ import annotations

import sys
from pathlib import Path

from jarvis.adapters.cli.board import board_dir, launch_board, repo_root
from jarvis.adapters.cli.main import main


def test_board_dir_is_the_visor_app():
    package = board_dir()
    assert package == repo_root() / "ui" / "spatial-board"
    assert (package / "package.json").is_file()


def test_missing_visor_returns_one(tmp_path: Path, capsys):
    assert launch_board(root=tmp_path, open_browser=False) == 1
    assert "No encuentro el visor" in capsys.readouterr().err


def test_board_subcommand_calls_launcher(monkeypatch):
    called = {"n": 0}

    def fake_launch() -> int:
        called["n"] += 1
        return 0

    monkeypatch.setattr("jarvis.adapters.cli.board.launch_board", fake_launch)
    monkeypatch.setattr(sys, "argv", ["jarvis", "board"])
    try:
        main()
    except SystemExit as exc:
        assert exc.code == 0
    assert called["n"] == 1
