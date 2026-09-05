"""Launch the spatial board visor. No engineering logic."""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

BOARD_HOST = "127.0.0.1"
BOARD_PORT = 5173
BOARD_URL = f"http://{BOARD_HOST}:{BOARD_PORT}/"


def repo_root() -> Path:
    # src/jarvis/adapters/cli/board.py → repo
    return Path(__file__).resolve().parents[4]


def board_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "ui" / "spatial-board"


def is_board_up(host: str = BOARD_HOST, port: int = BOARD_PORT) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.3):
            return True
    except OSError:
        return False


def launch_board(*, root: Path | None = None, open_browser: bool = True) -> int:
    directory = board_dir(root)
    if not (directory / "package.json").is_file():
        print(f"Jarvis > No encuentro el visor en {directory}", file=sys.stderr)
        return 1

    if is_board_up():
        print(f"Jarvis > Pizarra ya en marcha → {BOARD_URL}")
        if open_browser:
            webbrowser.open(BOARD_URL)
        return 0

    npm = shutil.which("npm")
    if not npm:
        print("Jarvis > npm no está en el PATH.", file=sys.stderr)
        return 1

    if not (directory / "node_modules").is_dir():
        print("Jarvis > Instalando dependencias del visor…")
        installed = subprocess.run([npm, "install"], cwd=directory)
        if installed.returncode != 0:
            return installed.returncode

    print(f"Jarvis > Pizarra → {BOARD_URL}")
    print("Jarvis > Ctrl+C para cerrar.")
    proc = subprocess.Popen(
        [npm, "run", "dev", "--", "--host", BOARD_HOST, "--port", str(BOARD_PORT)],
        cwd=directory,
        env=os.environ.copy(),
    )
    if not _wait_for_port(proc):
        if proc.poll() is None:
            proc.terminate()
        print("Jarvis > El visor no arrancó en el puerto 5173.", file=sys.stderr)
        return 1
    if open_browser:
        webbrowser.open(BOARD_URL)
    try:
        return int(proc.wait())
    except KeyboardInterrupt:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        return 0


def _wait_for_port(proc: subprocess.Popen[bytes], timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            return False
        if is_board_up():
            return True
        time.sleep(0.15)
    return False
