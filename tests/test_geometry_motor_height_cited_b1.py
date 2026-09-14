"""Motor height_mm 31.7 cited B1 (EMAX only, no cylinder).

Covers implementation_contract_geometry_motor_height_cited_b1.md §3–3.4:
  T1  emax_rs2205s_2300.height_mm == 31.7
  T2  sunnysky_r2205_2500.height_mm is None (different, unseeded fact)
  T3  sunnysky_r2305_2500.height_mm is None (live demo SKU, untouched)
  T4  emax_rs2205_2300.height_mm is None (sibling, unsourced)
  T5  bind_motor_from_catalog projects height_mm for the EMAX RS2205S
  T6  bind_motor_from_catalog does not project height_mm for SunnySky R2205
  T7  project_spatial_nodes: diameter_mm + height_mm resolves to a
      CYLINDER (Disk axial Visor B1, `B1-disk-axial-visor`, superseded
      this Buy's original "no cylinder" lock for cited axial dims) —
      never a box; height_mm still shows as a text field too
"""
from __future__ import annotations

import pytest

from jarvis.core.catalog_bind import bind_motor_from_catalog
from jarvis.core.motor_catalog_assist import motor_spec_to_suggestion
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes


def test_t1_emax_rs2205s_2300_height_mm_cited():
    motor = default_library.get_motor("emax_rs2205s_2300")
    assert motor.height_mm == pytest.approx(31.7)


def test_t2_sunnysky_r2205_2500_height_mm_none():
    motor = default_library.get_motor("sunnysky_r2205_2500")
    assert motor.height_mm is None


# Catalog sourced-only purge B1 redirect: sunnysky_r2305_2500 and
# emax_rs2205_2300 (both previously checked here) had no source_url and
# were deleted; sunnysky_r2205_2500 is a real, sourced KEEP sibling motor
# that also honestly omits height_mm (confirmed live).
def test_t3_sunnysky_r2205_2500_height_mm_none():
    motor = default_library.get_motor("sunnysky_r2205_2500")
    assert motor.height_mm is None


def test_t5_bind_projects_height_mm_for_emax_rs2205s_2300():
    motor = default_library.get_motor("emax_rs2205s_2300")
    suggestion = motor_spec_to_suggestion(motor)
    spec = bind_motor_from_catalog(suggestion)
    assert spec.properties["height_mm"].value == pytest.approx(31.7)
    assert spec.properties["height_mm"].unit == "mm"
    assert spec.properties["diameter_mm"].value == pytest.approx(27.9)


def test_t6_bind_sunnysky_r2205_has_no_height_mm_key():
    motor = default_library.get_motor("sunnysky_r2205_2500")
    suggestion = motor_spec_to_suggestion(motor)
    spec = bind_motor_from_catalog(suggestion)
    assert "height_mm" not in spec.properties


def test_t7_geometry_is_cylinder_when_diameter_and_height_mm_both_cited():
    """Disk axial Visor B1 (`B1-disk-axial-visor`) supersedes this Buy's
    own original "no cylinder" lock — Ø + a cited Motor `height_mm`
    together now emit a cylinder DTO, never a box. `height_mm` still
    shows as its own text field regardless (unchanged)."""
    motors = ComponentSpec(
        suggested_key="motors", completeness="high",
        properties={
            "diameter_mm": PropertyValue(value=27.9, unit="mm", source="declared"),
            "height_mm": PropertyValue(value=31.7, unit="mm", source="declared"),
        },
    )
    state = ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=DesignProperties(components={"motors": motors}),
    )
    nodes = project_spatial_nodes(state)
    node = next(n for n in nodes if n["id"] == "motors")
    assert node["geometry"] == {"shape": "cylinder", "diameter_mm": 27.9, "height_mm": 31.7}
    assert {"label": "height_mm", "value": "31.7 mm"} in node["fields"]
