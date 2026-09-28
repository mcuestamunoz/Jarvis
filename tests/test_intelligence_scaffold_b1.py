"""Tests T1-T5 for `B1-intelligence-scaffold`.

Scaffold-only checks: the package imports, exists on disk, never
imports `jarvis.flight_software`/`jarvis.vehicle_profiles`, the README
states the honesty locks, and no source file in the package calls into
Continuity/orchestrator (`jarvis.core`).
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = REPO_ROOT / "src" / "jarvis" / "intelligence"

FORBIDDEN_IMPORT_ROOTS = ("jarvis.flight_software", "jarvis.vehicle_profiles")
CONTINUITY_IMPORT_ROOTS = ("jarvis.core",)


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


def _python_files() -> list[Path]:
    return sorted(PACKAGE_DIR.rglob("*.py"))


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


def test_t1_import_succeeds():
    import jarvis.intelligence

    assert jarvis.intelligence is not None


def test_t2_package_path_exists_on_disk():
    assert PACKAGE_DIR.is_dir()
    assert (PACKAGE_DIR / "__init__.py").is_file()


def test_t3_no_flight_software_or_vehicle_profiles_imports():
    for path in _python_files():
        imported = _imported_module_names(path)
        for module_name in imported:
            for forbidden in FORBIDDEN_IMPORT_ROOTS:
                assert not (
                    module_name == forbidden or module_name.startswith(forbidden + ".")
                ), f"{path.relative_to(REPO_ROOT)} imports forbidden module '{module_name}'"


def test_t4_readme_states_scaffold_not_retrieve():
    readme_path = PACKAGE_DIR / "README.md"
    assert readme_path.is_file()
    text = readme_path.read_text(encoding="utf-8").lower()
    assert "scaffold" in text
    assert "retrieve" in text
    assert "ontology" in text


def test_t5_no_continuity_or_orchestrator_calls():
    """No source file imports `jarvis.core` (Continuity/orchestrator) or
    actually calls a `submit_command`-named function. Mentioning these
    names in a docstring/README honesty lock (documenting what this
    package does *not* do) is fine — only real imports/calls count."""
    for path in _python_files():
        imported = _imported_module_names(path)
        for module_name in imported:
            for forbidden in CONTINUITY_IMPORT_ROOTS:
                assert not (
                    module_name == forbidden or module_name.startswith(forbidden + ".")
                ), f"{path.relative_to(REPO_ROOT)} imports Continuity/orchestrator module '{module_name}'"
        called = _called_names(path)
        assert "submit_command" not in called, (
            f"{path.relative_to(REPO_ROOT)} calls submit_command"
        )


def test_pyproject_version_is_0_6_1():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.6.1"' in text
