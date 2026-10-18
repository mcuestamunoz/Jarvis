"""Tests T1-T6 for `B1-explain-maps-expand`.

Exercises the expanded `EXPLAIN_ALIASES`, the new `explain_maps`
FS/HD tables, and the `--list`/`--rung` CLI paths, all against the
real `ontology/` vault.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

from jarvis.intelligence.explain import (
    resolve_explain_query,
    run_explain_list_cli,
    run_explain_rung_cli,
)
from jarvis.intelligence.explain_aliases import EXPLAIN_ALIASES
from jarvis.intelligence.explain_maps import (
    FS_EXPLAIN_MAP,
    HD_EXPLAIN_MAP,
    ids_for_rung,
)
from jarvis.intelligence.ontology_retrieve import list_solid_ids

REPO_ROOT = Path(__file__).resolve().parents[1]
NEW_MODULE_PATHS = [
    REPO_ROOT / "src" / "jarvis" / "intelligence" / "explain_maps.py",
    REPO_ROOT / "src" / "jarvis" / "intelligence" / "explain_aliases.py",
]


def _imported_module_names(source_path: Path) -> set[str]:
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_t1_alias_imu_and_gyro_resolve_to_solid_cites():
    assert EXPLAIN_ALIASES["imu"] == "imu"
    assert EXPLAIN_ALIASES["gyro"] == "giroscopio"

    imu_cite = resolve_explain_query("imu")
    gyro_cite = resolve_explain_query("gyro")
    assert imu_cite is not None
    assert gyro_cite is not None
    assert imu_cite.id == "imu"
    assert gyro_cite.id == "giroscopio"
    assert imu_cite.estado == "solid"
    assert gyro_cite.estado == "solid"


def test_t2_ids_for_rung_c7_contains_imu_and_giroscopio():
    ids = ids_for_rung("C7")
    assert ids is not None
    assert "imu" in ids
    assert "giroscopio" in ids
    # Case-normalized lookup.
    assert ids_for_rung("c7") == ids


def test_t3_ids_for_rung_hd_001_contains_c_rate():
    ids = ids_for_rung("HD-001")
    assert ids is not None
    assert "c-rate-de-bateria" in ids
    assert ids_for_rung("hd-001") == ids


def test_t4_unknown_rung_is_a_miss():
    assert ids_for_rung("C999") is None
    assert ids_for_rung("HD-999") is None
    assert ids_for_rung("not-a-key") is None

    exit_code = run_explain_rung_cli("not-a-key")
    assert exit_code == 1


def test_t5_list_mentions_c_rate_and_an_alias(capsys):
    exit_code = run_explain_list_cli()
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "c-rate-de-bateria" in captured.out
    assert "c-rate -> c-rate-de-bateria" in captured.out

    # Also confirm the printed id list matches the real solid-id scan.
    solid_ids = list_solid_ids()
    assert "c-rate-de-bateria" in solid_ids
    for solid_id in solid_ids:
        assert solid_id in captured.out


def test_t6_no_continuity_llm_imports_and_no_ontology_write():
    forbidden_modules = ("jarvis.core",)
    forbidden_llm_substrings = ("llm", "ollama", "openai", "anthropic")
    for path in NEW_MODULE_PATHS:
        imported = _imported_module_names(path)
        for module_name in imported:
            for forbidden in forbidden_modules:
                assert not (
                    module_name == forbidden or module_name.startswith(forbidden + ".")
                ), f"{path.name} imports {module_name}"
            lowered = module_name.lower()
            for token in forbidden_llm_substrings:
                assert token not in lowered, f"{path.name} imports '{module_name}'"

        source = path.read_text(encoding="utf-8")
        for forbidden_call in ("write_text", "open(", ".write(", "unlink", "os.remove"):
            assert forbidden_call not in source, f"{path.name} contains '{forbidden_call}'"

    # Every id referenced by the new maps/aliases must actually be a
    # real solid vault id today (no invented/aspirational ids shipped).
    solid_ids = set(list_solid_ids())
    for id_list in list(FS_EXPLAIN_MAP.values()) + list(HD_EXPLAIN_MAP.values()):
        for note_id in id_list:
            assert note_id in solid_ids, f"{note_id} is not a solid vault id"
    for target_id in EXPLAIN_ALIASES.values():
        assert target_id in solid_ids, f"{target_id} is not a solid vault id"


def test_query_path_unchanged_for_a3_seed():
    cite = resolve_explain_query("c-rate")
    assert cite is not None
    assert cite.id == "c-rate-de-bateria"


def test_cli_argv_list_and_rung_smoke():
    env = {"PYTHONPATH": str(REPO_ROOT / "src")}

    list_result = subprocess.run(
        [sys.executable, "-m", "jarvis.main", "explain", "--list"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert list_result.returncode == 0
    assert "c-rate-de-bateria" in list_result.stdout

    rung_result = subprocess.run(
        [sys.executable, "-m", "jarvis.main", "explain", "--rung", "C7"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert rung_result.returncode == 0
    assert "imu" in rung_result.stdout

    mutually_exclusive = subprocess.run(
        [sys.executable, "-m", "jarvis.main", "explain", "c-rate", "--list"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert mutually_exclusive.returncode != 0

