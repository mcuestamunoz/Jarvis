"""Tests T1-T7 for `B1-ontology-retrieve-r2`.

Exercises `jarvis.intelligence.ontology_retrieve` against the real
`ontology/` vault (no fixture copy) using the `c-rate-de-bateria` note
that the IC names explicitly.
"""

from __future__ import annotations

import ast
from pathlib import Path

from jarvis.intelligence.ontology_retrieve import (
    DEFAULT_ONTOLOGY_ROOT,
    retrieve_by_id,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = REPO_ROOT / "src" / "jarvis" / "intelligence"
NOTE_ID = "c-rate-de-bateria"
NOTE_PATH = (
    REPO_ROOT
    / "ontology"
    / "03_Ingenieria"
    / "Electrónica"
    / "C-rate de batería"
    / "C-rate de batería.md"
)


def _python_files() -> list[Path]:
    return sorted(PACKAGE_DIR.rglob("*.py"))


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


def _called_names(source_path: Path) -> set[str]:
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    return names


def test_t1_retrieve_by_id_returns_non_none_against_real_vault():
    assert DEFAULT_ONTOLOGY_ROOT == REPO_ROOT / "ontology"
    cite = retrieve_by_id(NOTE_ID)
    assert cite is not None


def test_t2_cite_has_definicion_path_and_solid_estado():
    cite = retrieve_by_id(NOTE_ID)
    assert cite is not None
    assert cite.definicion != ""
    assert "C-rate" in cite.definicion
    assert cite.path.startswith("ontology" + "/") or cite.path.startswith("ontology\\")
    assert cite.estado == "solid"
    assert cite.intuicion != ""


def test_t3_never_invents_is_non_empty_list_matching_frontmatter():
    cite = retrieve_by_id(NOTE_ID)
    assert cite is not None
    assert cite.never_invents == ["mass_g", "power_w", "thrust_gf", "autonomy_min"]


def test_t4_unknown_id_returns_none_no_raise():
    result = retrieve_by_id("this-id-does-not-exist-anywhere-in-the-vault")
    assert result is None


def test_t5_no_flight_software_or_vehicle_profiles_imports():
    forbidden = ("jarvis.flight_software", "jarvis.vehicle_profiles")
    for path in _python_files():
        imported = _imported_module_names(path)
        for module_name in imported:
            for forbidden_root in forbidden:
                assert not (
                    module_name == forbidden_root
                    or module_name.startswith(forbidden_root + ".")
                ), f"{path.relative_to(REPO_ROOT)} imports forbidden module '{module_name}'"


def test_t6_retrieve_does_not_write_target_note():
    before_mtime = NOTE_PATH.stat().st_mtime_ns
    before_text = NOTE_PATH.read_text(encoding="utf-8")

    cite = retrieve_by_id(NOTE_ID)
    assert cite is not None

    after_mtime = NOTE_PATH.stat().st_mtime_ns
    after_text = NOTE_PATH.read_text(encoding="utf-8")
    assert after_mtime == before_mtime
    assert after_text == before_text

    # No write API anywhere in the module source.
    module_source = (PACKAGE_DIR / "ontology_retrieve.py").read_text(encoding="utf-8")
    for forbidden_call in ("write_text", "open(", ".write(", "unlink", "os.remove"):
        assert forbidden_call not in module_source


def test_t7_no_continuity_submit_command_or_craft_state_write():
    for path in _python_files():
        imported = _imported_module_names(path)
        assert not any(
            module_name == "jarvis.core" or module_name.startswith("jarvis.core.")
            for module_name in imported
        ), f"{path.relative_to(REPO_ROOT)} imports jarvis.core (Continuity/orchestrator)"
        called = _called_names(path)
        assert "submit_command" not in called


def test_prior_scaffold_status_constant_untouched():
    import jarvis.intelligence as intelligence

    assert intelligence.SCAFFOLD_STATUS == "stub"
    assert intelligence.RETRIEVE_STATUS == "r2"


def test_pyproject_version_is_0_6_2():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.6.2"' in text
