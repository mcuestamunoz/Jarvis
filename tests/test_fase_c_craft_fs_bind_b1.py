"""Tests T1-T8 for `B1-fase-c-craft-fs-bind` (C43).

T7's own "suite green" half is a process gate covered by running it,
not asserted here. T8 (report honesty line) is covered by
`.jes/artifacts/implementation_report_fase_c_craft_fs_bind_b1.md`, not
by this file.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.knowledge.library import ComponentLibrary
from jarvis.vehicle_profiles import (
    BoundVehicleProfile,
    VehicleProfile,
    bind_profile_to_craft_identity,
    load_smoke_profile,
    load_this_quad_profile,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_t1_bind_to_fixture_catalog_sku_exposes_that_sku():
    profile = load_this_quad_profile()
    bound = bind_profile_to_craft_identity(profile, "hglrc_my5_5in")

    assert isinstance(bound, BoundVehicleProfile)
    assert bound.craft_sku == "hglrc_my5_5in"
    assert bound.craft_manufacturer == "HGLRC"
    assert bound.craft_model == "MY5"
    assert bound.craft_size_class_inch == pytest.approx(5.0)
    assert bound.profile.id == "this_quad"


def test_t1_direct_library_lookup_matches_the_catalog_row():
    """Cross-checks the bind against `ComponentLibrary` directly — the
    bind must mirror the catalog row verbatim, not a second copy of the
    same facts."""
    library = ComponentLibrary()
    frame = library.get_frame("hglrc_my5_5in")

    profile = load_this_quad_profile()
    bound = bind_profile_to_craft_identity(profile, "hglrc_my5_5in", library=library)

    assert bound.craft_sku == frame.name
    assert bound.craft_manufacturer == frame.manufacturer
    assert bound.craft_model == frame.model
    assert bound.craft_size_class_inch == frame.size_class_inch


def test_t2_unknown_sku_raises_documented_error_not_silent_success():
    profile = load_this_quad_profile()
    with pytest.raises(KeyError):
        bind_profile_to_craft_identity(profile, "not_a_real_sku_xyz")


def test_t3_unbound_smoke_profile_still_loads():
    profile = load_smoke_profile()
    assert isinstance(profile, VehicleProfile)
    assert profile.id == "smoke_quad_hal_imu"
    assert profile.rung == "hal_imu"


def test_t4_bind_does_not_write_library_or_workspace():
    library_dir = REPO_ROOT / "library"
    frames_path = library_dir / "frames" / "_datos.json"
    before_mtime = frames_path.stat().st_mtime
    before_text = frames_path.read_text(encoding="utf-8")

    profile = load_this_quad_profile()
    bind_profile_to_craft_identity(profile, "hglrc_my5_5in")

    assert frames_path.stat().st_mtime == before_mtime
    assert frames_path.read_text(encoding="utf-8") == before_text

    for py_file in (REPO_ROOT / "src" / "jarvis" / "vehicle_profiles").rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        assert ".write_text(" not in text, f"{py_file} unexpectedly writes a file"
        assert "open(" not in text, f"{py_file} unexpectedly calls open()"


def test_t5_craft_paths_still_do_not_import_flight_software():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    workspace_dir = REPO_ROOT / "src" / "jarvis" / "workspace"
    for directory in (core_dir, adapters_dir, workspace_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "jarvis.flight_software" not in text, f"{py_file} references jarvis.flight_software"
            assert "jarvis.vehicle_profiles" not in text, f"{py_file} references jarvis.vehicle_profiles"


def test_t6_bind_module_imports_only_the_craft_read_surface():
    """`vehicle_profiles.bind` may import `jarvis.knowledge.library` (a
    craft READ surface) — the disclosed, one-directional exception this
    Buy adds. It must not import anything under `core`/`adapters`, and
    must not import `capabilities`/`flight_software.autonomy` (Safety/
    autonomy stay untouched, IC §0 decision 7)."""
    import inspect

    from jarvis.vehicle_profiles import bind as bind_module

    source = inspect.getsource(bind_module)
    assert "from jarvis.knowledge.library import" in source
    assert "jarvis.core" not in source
    assert "jarvis.adapters" not in source
    assert "jarvis.capabilities" not in source
    assert "jarvis.flight_software.autonomy" not in source
    assert "submit_command" not in source
    assert "propose_command" not in source


def test_t7_pyproject_version_is_0_5_44():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.44"' in text


def test_t7_full_suite_process_gate_placeholder():
    """The full Python suite being green (and host `ctest` unchanged) is
    verified by running them, not asserted here — see the implementation
    report's own test-run transcript."""
    assert True
