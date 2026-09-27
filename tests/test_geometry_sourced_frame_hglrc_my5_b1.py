"""#4g+ Sourced frame HGLRC MY5 B1 + 2026-09-24 caliper parts.

Retailer 225×200 stays root body_* only. Caliper bag seeds Top/Middle
plate L×W, one-arm L×W, and 8×30×Ø6 standoffs — never copied from body_*.
Bottom plate L×W still unknown. GEP/Rooster peers byte-stable on checked
fields.
"""
from __future__ import annotations

import pytest

from jarvis.core.catalog_bind import bind_frame_from_catalog, frame_part_specs_from_catalog
from jarvis.knowledge.library import default_library
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import _geometry_from_spec, project_spatial_nodes

_SKU = "hglrc_my5_5in"


def test_t1_new_sku_bag():
    spec = default_library.get_frame(_SKU)
    assert spec.wheelbase_mm == pytest.approx(225.0)
    assert spec.body_length_mm == pytest.approx(225.0)
    assert spec.body_width_mm == pytest.approx(200.0)
    assert spec.fc_esc_stack_length_mm == pytest.approx(46.0)
    assert spec.fc_esc_stack_width_mm == pytest.approx(46.0)
    assert spec.fc_esc_stack_height_mm == pytest.approx(18.0)
    assert spec.max_stack_height_mm is None
    assert spec.mass_g == pytest.approx(140.0)
    assert spec.size_class_inch == pytest.approx(5.0)
    assert spec.configuration == "quad_x"
    assert spec.arm_thickness_mm == pytest.approx(5.0)
    assert spec.arm_length_mm == pytest.approx(125.0)
    assert spec.arm_width_mm == pytest.approx(20.0)
    assert spec.plates is not None and len(spec.plates) == 3
    by_label = {p.label: (p.thickness_mm, p.length_mm, p.width_mm) for p in spec.plates}
    assert by_label["Top plate"][0] == pytest.approx(2.0)
    assert by_label["Top plate"][1] == pytest.approx(161.0)
    assert by_label["Top plate"][2] == pytest.approx(42.0)
    assert by_label["Middle plate"][0] == pytest.approx(3.0)
    assert by_label["Middle plate"][1] == pytest.approx(170.0)
    assert by_label["Middle plate"][2] == pytest.approx(45.0)
    assert by_label["Bottom plate"][0] == pytest.approx(2.0)
    assert by_label["Bottom plate"][1] is None
    assert by_label["Bottom plate"][2] is None
    assert spec.standoff_count == 8
    assert spec.standoffs is not None and len(spec.standoffs) == 1
    assert spec.standoffs[0].height_mm == pytest.approx(30.0)
    assert spec.standoffs[0].count == 8
    assert spec.standoffs[0].diameter_mm == pytest.approx(6.0)
    assert spec.manufacturer == "HGLRC"
    assert spec.model == "MY5"
    assert spec.identity_status == "verified"
    assert spec.source_url is not None and "rotorama.com" in spec.source_url


def test_t2_peers_unchanged():
    gep = default_library.get_frame("geprc_gep_racer_5in")
    assert gep.wheelbase_mm == pytest.approx(208.0)
    assert gep.mass_g == pytest.approx(78.0)
    assert gep.arm_length_mm is None
    assert gep.arm_width_mm is None
    assert gep.fc_esc_stack_length_mm is None
    rooster = default_library.get_frame("armattan_rooster_5in")
    assert rooster.wheelbase_mm == pytest.approx(230.0)
    assert rooster.mass_g == pytest.approx(125.0)
    assert rooster.body_length_mm is None
    assert rooster.body_width_mm is None
    assert rooster.arm_length_mm is None
    assert rooster.fc_esc_stack_height_mm is None


def test_t3_bind_projects_caliper_children_not_body_onto_plates():
    bound = bind_frame_from_catalog(_SKU)
    assert bound.properties["wheelbase_mm"].value == pytest.approx(225.0)
    assert bound.properties["body_length_mm"].value == pytest.approx(225.0)
    assert bound.properties["body_width_mm"].value == pytest.approx(200.0)
    assert bound.properties["fc_esc_stack_length_mm"].value == pytest.approx(46.0)
    assert bound.properties["fc_esc_stack_width_mm"].value == pytest.approx(46.0)
    assert bound.properties["fc_esc_stack_height_mm"].value == pytest.approx(18.0)
    assert bound.properties["mass_kg"].value == pytest.approx(0.140)
    assert bound.catalog_ref.sku == _SKU
    assert "length_mm" not in bound.properties
    assert "width_mm" not in bound.properties
    assert "height_mm" not in bound.properties
    assert _geometry_from_spec(bound) is None

    parts = frame_part_specs_from_catalog(_SKU)
    assert set(parts) == {
        "frame_arm", "frame_plate", "frame_plate_2", "frame_plate_3", "frame_standoff",
    }
    for part_spec in parts.values():
        assert part_spec.parent_key == "frame"

    top = parts["frame_plate"]
    assert top.properties["label"].value == "Top plate"
    assert top.properties["thickness_mm"].value == pytest.approx(2.0)
    assert top.properties["length_mm"].value == pytest.approx(161.0)
    assert top.properties["width_mm"].value == pytest.approx(42.0)
    assert top.properties["height_mm"].value == pytest.approx(2.0)
    assert top.properties["length_mm"].value != pytest.approx(225.0)
    assert top.properties["width_mm"].value != pytest.approx(200.0)

    mid = parts["frame_plate_2"]
    assert mid.properties["label"].value == "Middle plate"
    assert mid.properties["length_mm"].value == pytest.approx(170.0)
    assert mid.properties["width_mm"].value == pytest.approx(45.0)
    assert mid.properties["height_mm"].value == pytest.approx(3.0)

    bot = parts["frame_plate_3"]
    assert bot.properties["label"].value == "Bottom plate"
    assert bot.properties["thickness_mm"].value == pytest.approx(2.0)
    assert "length_mm" not in bot.properties
    assert "width_mm" not in bot.properties
    assert "height_mm" not in bot.properties

    arm = parts["frame_arm"]
    assert arm.properties["thickness_mm"].value == pytest.approx(5.0)
    assert arm.properties["length_mm"].value == pytest.approx(125.0)
    assert arm.properties["width_mm"].value == pytest.approx(20.0)
    assert arm.properties["height_mm"].value == pytest.approx(5.0)

    standoff = parts["frame_standoff"]
    assert standoff.properties["count"].value == 8
    assert standoff.properties["height_mm"].value == pytest.approx(30.0)
    assert standoff.properties["diameter_mm"].value == pytest.approx(6.0)
    assert "length_mm" not in standoff.properties


def test_t4_glyphs_from_projected_parts():
    parts = frame_part_specs_from_catalog(_SKU)
    assert _geometry_from_spec(parts["frame_plate"]) == {
        "shape": "box", "length_mm": 161.0, "width_mm": 42.0, "height_mm": 2.0,
    }
    assert _geometry_from_spec(parts["frame_plate_2"]) == {
        "shape": "box", "length_mm": 170.0, "width_mm": 45.0, "height_mm": 3.0,
    }
    assert _geometry_from_spec(parts["frame_plate_3"]) is None
    assert _geometry_from_spec(parts["frame_arm"]) == {
        "shape": "box", "length_mm": 125.0, "width_mm": 20.0, "height_mm": 5.0,
    }
    assert _geometry_from_spec(parts["frame_standoff"]) == {
        "shape": "cylinder", "diameter_mm": 6.0, "height_mm": 30.0,
    }


def test_t5_graph_lists_my5_parts_as_children():
    components = {"frame": bind_frame_from_catalog(_SKU)}
    components.update(frame_part_specs_from_catalog(_SKU))
    state = ProjectState(
        project_id="my5-caliper",
        project_slug="my5-caliper",
        objective="my5 caliper graph",
        workspace_path="/tmp/my5-caliper",
        design_properties=DesignProperties(
            components=components,
            system_blocks=["structure"],
        ),
    )
    nodes = {n["id"]: n for n in project_spatial_nodes(state)}
    assert nodes["frame"]["kind"] == "component"
    for key in ("frame_arm", "frame_plate", "frame_plate_2", "frame_plate_3", "frame_standoff"):
        assert key in nodes, f"{key} missing from graph"
        assert nodes[key]["kind"] == "part"
    assert nodes["frame_plate"]["geometry"]["length_mm"] == pytest.approx(161.0)
    assert nodes["frame_standoff"]["geometry"]["shape"] == "cylinder"
    assert nodes["frame_standoff"]["solidCopies"] == 8
    standoff_pts = {
        (o["xMm"], o["yMm"]) for o in nodes["frame_standoff"]["solidCopyOffsetsMm"]
    }
    assert standoff_pts == {
        (77.5, 18.0), (77.5, -18.0), (-77.5, -18.0), (-77.5, 18.0),
        (77.5, 0.0), (-77.5, 0.0), (0.0, 18.0), (0.0, -18.0),
    }
    assert all(o["zMm"] == 0.0 for o in nodes["frame_standoff"]["solidCopyOffsetsMm"])
    frame_labels = {f["label"] for f in nodes["frame"]["fields"]}
    assert "body_length_mm" in frame_labels
    assert "body_width_mm" in frame_labels
    assert "fc_esc_stack_length_mm" in frame_labels
    assert "fc_esc_stack_height_mm" in frame_labels
    assert "geometry" not in nodes["frame"]
    for key in ("frame_arm", "frame_plate", "frame_plate_2", "frame_plate_3", "frame_standoff"):
        child_labels = {f["label"] for f in nodes[key]["fields"]}
        assert "fc_esc_stack_length_mm" not in child_labels
        assert "body_length_mm" not in child_labels
