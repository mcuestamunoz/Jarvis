"""Disk axial Visor from cited dims B1 (`B1-disk-axial-visor`).

Covers implementation_contract_geometry_disk_axial_visor_b1.md §2:
  C1  Motors {diameter_mm, height_mm} -> cylinder
  C2  Motors {diameter_mm} only -> still disk
  C3  Motors {diameter_mm, height_mm, stator_height_mm} -> cylinder H is
      height_mm, never stator_height_mm
  C4  Propellers {diameter_in, hub_thickness_mm} -> cylinder; height_mm ==
      hub_thickness_mm; diameter_mm == diameter_in * 25.4
  C5  Propellers diameter only (no hub_thickness_mm) -> flat disk
  C6  Full L×W×H still wins as box even with diameter also present
  C7  screen_posed_envelope on a cylinder child -> child_not_box (no AABB
      invented for a cylinder)
  T   Full pytest green; package 0.4.1 (checked at the repo level)

Plus a census of live-bound catalog SKUs that become cylinders vs. stay
disks under the new rule (no new catalog numbers this Buy).
"""
from __future__ import annotations

import pytest

from jarvis.core.catalog_bind import bind_motor_from_catalog, bind_propeller_from_catalog
from jarvis.core.motor_catalog_assist import motor_spec_to_suggestion
from jarvis.core.pose_envelope_screening import screen_posed_envelope
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import ComponentSpec, DeclaredBoxPose, PropertyValue
from jarvis.workspace.spatial_board import _geometry_from_spec


def _spec(properties: dict) -> ComponentSpec:
    return ComponentSpec(suggested_key="x", completeness="high", properties=properties)


# ── C1: motors diameter + height_mm -> cylinder ──────────────────────────


def test_c1_motor_diameter_and_height_mm_yields_cylinder():
    spec = _spec({
        "diameter_mm": PropertyValue(value=28.5, unit="mm", source="declared"),
        "height_mm": PropertyValue(value=33.1, unit="mm", source="declared"),
    })
    assert _geometry_from_spec(spec) == {"shape": "cylinder", "diameter_mm": 28.5, "height_mm": 33.1}


# ── C2: motors diameter only -> disk ─────────────────────────────────────


def test_c2_motor_diameter_only_still_disk():
    spec = _spec({"diameter_mm": PropertyValue(value=27.9, unit="mm", source="declared")})
    assert _geometry_from_spec(spec) == {"shape": "disk", "diameter_mm": 27.9}


# ── C3: stator_height_mm never substitutes for cylinder H ────────────────


def test_c3_stator_height_mm_never_used_as_cylinder_height():
    spec = _spec({
        "diameter_mm": PropertyValue(value=28.5, unit="mm", source="declared"),
        "height_mm": PropertyValue(value=33.1, unit="mm", source="declared"),
        "stator_height_mm": PropertyValue(value=7.0, unit="mm", source="declared"),
    })
    geometry = _geometry_from_spec(spec)
    assert geometry["shape"] == "cylinder"
    assert geometry["height_mm"] == pytest.approx(33.1)
    assert geometry["height_mm"] != pytest.approx(7.0)


def test_c3_stator_height_mm_alone_never_creates_geometry():
    """stator_diameter_mm/stator_height_mm are never a diameter or axial
    path on their own — a motor citing ONLY those (no diameter_mm, no
    height_mm) still gets no geometry at all, same as before this Buy."""
    spec = _spec({
        "stator_diameter_mm": PropertyValue(value=22.0, unit="mm", source="declared"),
        "stator_height_mm": PropertyValue(value=7.0, unit="mm", source="declared"),
    })
    assert _geometry_from_spec(spec) is None


# ── C4: propellers diameter_in + hub_thickness_mm -> cylinder ───────────


def test_c4_propeller_diameter_in_and_hub_thickness_yields_cylinder():
    spec = _spec({
        "diameter_in": PropertyValue(value=5.189, unit="in", source="declared"),
        "hub_thickness_mm": PropertyValue(value=6.8, unit="mm", source="declared"),
    })
    geometry = _geometry_from_spec(spec)
    assert geometry["shape"] == "cylinder"
    assert geometry["height_mm"] == pytest.approx(6.8)
    assert geometry["diameter_mm"] == pytest.approx(5.189 * 25.4)


# ── C5: propellers diameter only (no hub_thickness) -> disk ─────────────


def test_c5_propeller_diameter_only_no_hub_thickness_stays_disk():
    spec = _spec({"diameter_in": PropertyValue(value=5.0, unit="in", source="declared")})
    geometry = _geometry_from_spec(spec)
    assert geometry["shape"] == "disk"
    assert geometry["diameter_mm"] == pytest.approx(127.0)


def test_c5_hub_thickness_alone_without_diameter_yields_no_geometry():
    """Axial fact alone, no diameter at all -> None (never invent Ø)."""
    spec = _spec({"hub_thickness_mm": PropertyValue(value=6.8, unit="mm", source="declared")})
    assert _geometry_from_spec(spec) is None


# ── C6: full L×W×H still wins as box even with diameter present ─────────


def test_c6_box_wins_over_diameter_and_axial_when_full_lwh_present():
    spec = _spec({
        "length_mm": PropertyValue(value=44.0, unit="mm", source="declared"),
        "width_mm": PropertyValue(value=84.0, unit="mm", source="declared"),
        "height_mm": PropertyValue(value=12.0, unit="mm", source="declared"),
        "diameter_mm": PropertyValue(value=30.5, unit="mm", source="declared"),
    })
    geometry = _geometry_from_spec(spec)
    assert geometry == {
        "shape": "box", "length_mm": 44.0, "width_mm": 84.0, "height_mm": 12.0,
    }


# ── C7: screening still refuses a cylinder child (no AABB invented) ─────


def test_c7_screening_refuses_cylinder_child_as_not_box():
    fc = _spec({
        "length_mm": PropertyValue(value=44.0, unit="mm", source="declared"),
        "width_mm": PropertyValue(value=84.0, unit="mm", source="declared"),
        "height_mm": PropertyValue(value=12.0, unit="mm", source="declared"),
    })
    motors = _spec({
        "diameter_mm": PropertyValue(value=28.5, unit="mm", source="declared"),
        "height_mm": PropertyValue(value=33.1, unit="mm", source="declared"),
    }).model_copy(update={
        "declared_box_pose": DeclaredBoxPose(origin_key="flight_controller", x_mm=1.0, y_mm=1.0, z_mm=1.0),
    })
    components = {"flight_controller": fc, "motors": motors}
    screening = screen_posed_envelope(motors, components)
    assert screening.status == "child_not_box"


def test_c7_screening_refuses_cylinder_as_pose_origin_too():
    """A cylinder is equally refused as an ORIGIN (never just as a
    child) — origin_unusable, same as a disk always was."""
    motors = _spec({
        "diameter_mm": PropertyValue(value=28.5, unit="mm", source="declared"),
        "height_mm": PropertyValue(value=33.1, unit="mm", source="declared"),
    })
    esc = _spec({
        "length_mm": PropertyValue(value=45.6, unit="mm", source="declared"),
        "width_mm": PropertyValue(value=44.0, unit="mm", source="declared"),
        "height_mm": PropertyValue(value=8.0, unit="mm", source="declared"),
    }).model_copy(update={
        "declared_box_pose": DeclaredBoxPose(origin_key="motors", x_mm=0.0, y_mm=0.0, z_mm=0.0),
    })
    components = {"motors": motors, "esc": esc}
    screening = screen_posed_envelope(esc, components)
    assert screening.status == "origin_unusable"


# ── Census: which live-bound catalog SKUs become cylinders vs stay disks ──
# (no new catalog numbers this Buy — only consuming seeds already present)


def test_census_iflight_xing_e_pro_becomes_cylinder():
    suggestion = motor_spec_to_suggestion(default_library.get_motor("iflight_xing_e_pro_2207_2450"))
    bound = bind_motor_from_catalog(suggestion)
    geometry = _geometry_from_spec(bound)
    assert geometry == {"shape": "cylinder", "diameter_mm": pytest.approx(28.5), "height_mm": pytest.approx(33.1)}


def test_census_emax_rs2205s_2300_becomes_cylinder():
    suggestion = motor_spec_to_suggestion(default_library.get_motor("emax_rs2205s_2300"))
    bound = bind_motor_from_catalog(suggestion)
    geometry = _geometry_from_spec(bound)
    assert geometry["shape"] == "cylinder"
    assert geometry["height_mm"] == pytest.approx(31.7)


def test_census_sunnysky_r2205_2500_stays_disk_no_height_mm_cited():
    suggestion = motor_spec_to_suggestion(default_library.get_motor("sunnysky_r2205_2500"))
    bound = bind_motor_from_catalog(suggestion)
    geometry = _geometry_from_spec(bound)
    assert geometry["shape"] == "disk"


def test_census_gemfan_hurricane_mck_51466_becomes_cylinder():
    bound = bind_propeller_from_catalog("gemfan_hurricane_mck_51466_3_v2")
    geometry = _geometry_from_spec(bound)
    assert geometry["shape"] == "cylinder"
    assert geometry["height_mm"] == pytest.approx(6.8)


def test_census_gf_5045x3_becomes_cylinder_hub_thickness_9_5():
    """gf_5045x3 cites hub_thickness_mm=9.5 too — also flips to cylinder,
    not just the newest SKU (no cherry-picking which cited row honors the
    new rule)."""
    bound = bind_propeller_from_catalog("gf_5045x3")
    geometry = _geometry_from_spec(bound)
    assert geometry["shape"] == "cylinder"
    assert geometry["height_mm"] == pytest.approx(9.5)


def test_census_dal_7040_becomes_cylinder_hub_thickness_7_0():
    bound = bind_propeller_from_catalog("dal_7040")
    geometry = _geometry_from_spec(bound)
    assert geometry["shape"] == "cylinder"
    assert geometry["height_mm"] == pytest.approx(7.0)


def test_census_apc_10x6_ep_becomes_cylinder_hub_thickness_9_9():
    """apc_10x6_ep cites both hub_diameter_mm AND hub_thickness_mm=9.9 —
    also flips to cylinder; hub_diameter_mm itself is never read as an
    axial fact (only hub_thickness_mm is)."""
    bound = bind_propeller_from_catalog("apc_10x6_ep")
    geometry = _geometry_from_spec(bound)
    assert geometry["shape"] == "cylinder"
    assert geometry["height_mm"] == pytest.approx(9.9)


def test_census_hq_5045_bn_stays_disk_no_hub_thickness_cited():
    """hq_5045_bn cites no hub bag at all (partially_verified) — stays a
    flat disk, the honest fallback."""
    bound = bind_propeller_from_catalog("hq_5045_bn")
    geometry = _geometry_from_spec(bound)
    assert geometry["shape"] == "disk"


def test_no_new_catalog_seeds_added_this_buy():
    """This Buy consumes existing seeds only — `library/motores/_datos.json`
    and `library/helices/_datos.json` are untouched on disk (verified via
    git, not just re-parsed)."""
    import subprocess
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "status", "--short", "--", "library/motores/_datos.json", "library/helices/_datos.json"],
        cwd=repo_root, capture_output=True, text=True, check=True,
    )
    assert result.stdout.strip() == ""
