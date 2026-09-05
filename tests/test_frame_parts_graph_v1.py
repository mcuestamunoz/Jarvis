"""Structure B Parts Graph (Fase 1).

Covers implementation_contract_structure_b_parts_graph_fase1.md §3:
  - ComponentSpec.parent_key round-trip / default None
  - configuration / wheelbase_mm extraction (declared-only, never from
    motor_count)
  - part-type phrase extraction (locked keys, no fabricated stubs)
  - BOM N1: children never top-level peers, only display-only sub-lines
    under frame; orphaned parent_key never crashes/never becomes a peer
  - Structure PASS / evidence bits unchanged with vs without children
  - catalog bind: Armattan projects part children from seed; a TBS row
    with no part fields projects none
  - wheelbase_mm present on root after bind when seeded
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from jarvis.core.catalog_bind import bind_frame_from_catalog, frame_part_specs_from_catalog
from jarvis.core.component_writers import set_frame_material, upsert_frame_part
from jarvis.core.engineering_readiness import build_engineering_readiness
from jarvis.core.project_closure import build_component_bom, format_bom_lines
from jarvis.domains.aerial import (
    FRAME_ARM_KEY,
    FRAME_CAGE_KEY,
    FRAME_PLATE_KEY,
    FRAME_PLATE_MAX_SIBLINGS,
    FRAME_STANDOFF_KEY,
    extract_frame_part_properties,
    extract_frame_properties,
    frame_plate_key,
    is_frame_plate_key,
)
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue


def _design_properties(**kwargs):
    defaults = dict(components={}, system_blocks=[], system_priority=[])
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _project_state(**kwargs):
    defaults = dict(
        current_parameters={"vehicle_type": "dron"},
        parsed_constraints={},
        latest_results={"simulation": {}, "calculations": {}},
        design_properties=_design_properties(),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ── 1. Schema round-trip ─────────────────────────────────────────────────

def test_component_spec_parent_key_default_none():
    spec = ComponentSpec(suggested_key="frame")
    assert spec.parent_key is None


def test_component_spec_parent_key_round_trip():
    spec = ComponentSpec(suggested_key="frame_arm", parent_key="frame")
    dumped = spec.model_dump()
    restored = ComponentSpec(**dumped)
    assert restored.parent_key == "frame"


# ── 2. configuration / wheelbase_mm extraction ──────────────────────────

def test_extract_configuration_quad_x():
    props = extract_frame_properties("quad x, fibra de carbono")
    assert props["configuration"].value == "quad_x"


def test_extract_configuration_deadcat():
    props = extract_frame_properties("frame deadcat 7 pulgadas")
    assert props["configuration"].value == "deadcat"


def test_extract_configuration_unrecognized_absent():
    props = extract_frame_properties("fibra de carbono 450g")
    assert "configuration" not in props


def test_extract_configuration_never_from_motor_count():
    """motor_count is not even a parameter extract_frame_properties sees —
    confirms configuration cannot be derived from it structurally."""
    props = extract_frame_properties("4 motores")
    assert "configuration" not in props


def test_extract_wheelbase_mm_with_keyword():
    props = extract_frame_properties("wheelbase 230mm")
    assert props["wheelbase_mm"].value == pytest.approx(230.0)


def test_extract_wheelbase_mm_bare_number_absent():
    """A bare '230mm' with no wheelbase/motor-a-motor context must not be
    claimed — same discipline as size_class_inch's own bare-mm rule."""
    props = extract_frame_properties("carbono 230mm")
    assert "wheelbase_mm" not in props


# ── 3. part-type phrase extraction ──────────────────────────────────────

def test_extract_frame_part_arm_with_count_and_material():
    result = extract_frame_part_properties("4 brazos fibra de carbono")
    assert result is not None
    key, props = result
    assert key == FRAME_ARM_KEY
    assert props["count"].value == 4
    assert props["material"].value == "fibra de carbono"


def test_extract_frame_part_standoff_material_only():
    result = extract_frame_part_properties("standoffs aluminio")
    assert result == (FRAME_STANDOFF_KEY, {"material": result[1]["material"]})
    assert result[1]["material"].value == "aluminio"
    assert "count" not in result[1]


def test_extract_frame_part_cage():
    result = extract_frame_part_properties("jaula titanio")
    assert result is not None
    key, props = result
    assert key == FRAME_CAGE_KEY
    assert props["material"].value == "titanio"


def test_extract_frame_part_unrecognized_returns_none_never_a_stub():
    assert extract_frame_part_properties("algo irreconocible sin sentido") is None


# ── 4. BOM N1 — children never top-level peers ──────────────────────────

def _frame_with_parts_state(propeller_diameter_in=5.0):
    frame = ComponentSpec(
        suggested_key="frame", completeness="high", source="declared",
        properties={
            "mass_kg": PropertyValue(value=0.125),
            "material": PropertyValue(value="fibra de carbono"),
            "size_class_inch": PropertyValue(value=5.0, unit="in"),
        },
    )
    arm = ComponentSpec(
        suggested_key=FRAME_ARM_KEY, completeness="high", source="declared",
        properties={"material": PropertyValue(value="fibra de carbono")},
        parent_key="frame",
    )
    cage = ComponentSpec(
        suggested_key=FRAME_CAGE_KEY, completeness="high", source="declared",
        properties={"material": PropertyValue(value="titanio")},
        parent_key="frame",
    )
    return _project_state(
        current_parameters={"vehicle_type": "dron", "propeller_diameter_in": propeller_diameter_in},
        design_properties=_design_properties(
            components={"frame": frame, FRAME_ARM_KEY: arm, FRAME_CAGE_KEY: cage},
            system_blocks=["structure"], system_priority=["structure"],
        ),
    )


def test_bom_children_never_top_level_peers():
    state = _frame_with_parts_state()
    bom = build_component_bom(state)
    all_top_level_keys = (
        [e["key"] for e in bom["defined"]]
        + [e["key"] for e in bom["incomplete"]]
        + [e["key"] for e in bom["declarative"]]
        + list(bom["missing"])
    )
    assert FRAME_ARM_KEY not in all_top_level_keys
    assert FRAME_CAGE_KEY not in all_top_level_keys
    assert "frame" in [e["key"] for e in bom["defined"]]


def test_bom_lines_show_children_as_sublines_under_frame():
    state = _frame_with_parts_state()
    bom = build_component_bom(state)
    lines = format_bom_lines(bom, state)
    frame_idx = next(i for i, line in enumerate(lines) if line.startswith("✓ frame"))
    assert not any(line.startswith(f"✓ {FRAME_ARM_KEY}") for line in lines)
    assert not any(line.startswith(f"◇ {FRAME_ARM_KEY}") for line in lines)
    assert lines[frame_idx + 1] == "   └ arm — fibra de carbono"
    assert lines[frame_idx + 2] == "   └ cage — titanio"


def test_bom_sublines_absent_without_project_state():
    """Backward compatibility: omitting project_state keeps plain frame
    line only, same as before this IC."""
    state = _frame_with_parts_state()
    bom = build_component_bom(state)
    lines = format_bom_lines(bom)
    assert not any("└" in line for line in lines)


def test_bom_orphan_parent_key_no_crash_no_peer_line():
    """parent_key points at a key not present in components — must not
    crash and must not appear as a top-level peer."""
    orphan = ComponentSpec(
        suggested_key=FRAME_ARM_KEY, completeness="high", source="declared",
        properties={"material": PropertyValue(value="fibra de carbono")},
        parent_key="frame",
    )
    state = _project_state(
        design_properties=_design_properties(
            components={FRAME_ARM_KEY: orphan},
            system_blocks=["structure"], system_priority=["structure"],
        ),
    )
    bom = build_component_bom(state)
    lines = format_bom_lines(bom, state)
    assert FRAME_ARM_KEY not in [e["key"] for e in bom["defined"]]
    assert FRAME_ARM_KEY not in [e["key"] for e in bom["incomplete"]]
    assert FRAME_ARM_KEY not in [e["key"] for e in bom["declarative"]]
    assert not any(FRAME_ARM_KEY in line for line in lines)


# ── 5. Structure PASS / evidence bits unchanged with vs without children ──

def _fully_closed_pass_state(with_children: bool):
    frame = ComponentSpec(
        suggested_key="frame", completeness="high", source="declared",
        properties={
            "mass_kg": PropertyValue(value=0.4),
            "material": PropertyValue(value="fibra de carbono"),
            "size_class_inch": PropertyValue(value=10.0, unit="in"),
        },
    )
    components = {"frame": frame}
    if with_children:
        components[FRAME_ARM_KEY] = ComponentSpec(
            suggested_key=FRAME_ARM_KEY, completeness="high", source="declared",
            properties={"count": PropertyValue(value=4)}, parent_key="frame",
        )
        components[FRAME_PLATE_KEY] = ComponentSpec(
            suggested_key=FRAME_PLATE_KEY, completeness="high", source="declared",
            properties={"material": PropertyValue(value="fibra de carbono")}, parent_key="frame",
        )
    return _project_state(
        current_parameters={"vehicle_type": "dron", "propeller_diameter_in": 10.0},
        latest_results={
            "simulation": {"status": "pass", "can_fly": True, "quality": "good", "safety_margin_ratio": 1.5, "warnings": []},
            "calculations": {"total_mass_kg": 1.5},
        },
        design_properties=_design_properties(
            components=components,
            system_blocks=["structure"], system_priority=["structure"],
        ),
    )


def test_structure_pass_and_evidence_unchanged_with_vs_without_children():
    without = build_engineering_readiness(_fully_closed_pass_state(with_children=False))
    with_children = build_engineering_readiness(_fully_closed_pass_state(with_children=True))
    assert without.subsystems["structure"] == with_children.subsystems["structure"]
    assert without.overall == with_children.overall
    assert with_children.subsystems["structure"].verdict == "PASS"


# ── 6/7. Catalog bind — part projection + wheelbase on root ─────────────

def test_bind_frame_from_catalog_projects_wheelbase_and_configuration():
    spec = bind_frame_from_catalog("armattan_rooster_5in")
    assert spec.properties["wheelbase_mm"].value == pytest.approx(230.0)
    assert spec.properties["configuration"].value == "quad_x"


def test_frame_part_specs_from_catalog_armattan_has_arm_four_plates_cage_standoff():
    """Frame Assembly Physical Model B2, T3 — Armattan's curated 4-plate
    list projects 4 ordinal plate siblings (Main/LiPo/front/rear), each its
    own node, alongside arm/cage/standoff. Superseded by this IC:
    Armattan no longer has exactly 4 part children — it has 7 (arm + 4
    plates + cage + standoff)."""
    parts = frame_part_specs_from_catalog("armattan_rooster_5in")
    assert set(parts.keys()) == {
        FRAME_ARM_KEY, "frame_plate", "frame_plate_2", "frame_plate_3", "frame_plate_4",
        FRAME_CAGE_KEY, FRAME_STANDOFF_KEY,
    }
    assert parts[FRAME_ARM_KEY].properties["material"].value == "fibra de carbono"
    assert parts[FRAME_ARM_KEY].properties["thickness_mm"].value == pytest.approx(4.0)
    assert parts["frame_plate"].properties["label"].value == "Main Plate"
    assert parts["frame_plate"].properties["thickness_mm"].value == pytest.approx(4.0)
    assert parts["frame_plate"].properties["material"].value == "fibra de carbono"
    assert parts["frame_plate_2"].properties["label"].value == "Top (LiPo) plate"
    assert parts["frame_plate_2"].properties["thickness_mm"].value == pytest.approx(2.0)
    assert parts["frame_plate_3"].properties["label"].value == "Small front (top) plate"
    assert parts["frame_plate_3"].properties["thickness_mm"].value == pytest.approx(1.5)
    assert parts["frame_plate_4"].properties["label"].value == "Small rear (top) plate"
    assert parts["frame_plate_4"].properties["thickness_mm"].value == pytest.approx(1.5)
    assert parts[FRAME_CAGE_KEY].properties["material"].value == "titanio"
    assert parts[FRAME_STANDOFF_KEY].properties["material"].value == "aluminio"
    for spec in parts.values():
        assert spec.parent_key == "frame"
        assert spec.component_type == "structure_part"


def test_plate_multiplicity_never_merges_equal_thickness_siblings():
    """N3 lock, T5 — TBS 5in's Top (2mm) and Middle (2mm) share a thickness
    value but must remain two distinct nodes, never merged/deduped by
    value."""
    parts = frame_part_specs_from_catalog("tbs_source_one_v5_5in")
    assert parts["frame_plate"].properties["label"].value == "Top"
    assert parts["frame_plate_2"].properties["label"].value == "Middle"
    assert parts["frame_plate"].properties["thickness_mm"].value == pytest.approx(2.0)
    assert parts["frame_plate_2"].properties["thickness_mm"].value == pytest.approx(2.0)
    assert parts["frame_plate"] is not parts["frame_plate_2"]
    assert parts["frame_plate_3"].properties["label"].value == "Bottom"
    assert parts["frame_plate_3"].properties["thickness_mm"].value == pytest.approx(2.5)


def test_frame_plate_key_helpers_locked_bound():
    """N7 lock — exactly frame_plate..frame_plate_8 (8 max), nothing else
    recognized as a plate-family key."""
    assert FRAME_PLATE_MAX_SIBLINGS == 8
    assert frame_plate_key(0) == "frame_plate"
    assert frame_plate_key(1) == "frame_plate_2"
    assert frame_plate_key(7) == "frame_plate_8"
    for i in range(8):
        assert is_frame_plate_key(frame_plate_key(i))
    assert not is_frame_plate_key("frame_plate_9")
    assert not is_frame_plate_key("frame_plate_top")
    assert not is_frame_plate_key("frame_arm")


def test_bom_thickness_only_arm_still_renders_subline():
    """T5 — thickness-only frame_arm (no count/material) still renders a
    BOM sub-line under frame."""
    frame = ComponentSpec(
        suggested_key="frame", completeness="medium", source="declared",
        properties={
            "mass_kg": PropertyValue(value=0.1235),
            "size_class_inch": PropertyValue(value=5.0, unit="in"),
        },
    )
    arm = ComponentSpec(
        suggested_key=FRAME_ARM_KEY, completeness="low", source="declared",
        properties={"thickness_mm": PropertyValue(value=6.0, unit="mm")},
        parent_key="frame",
    )
    state = _project_state(
        current_parameters={"vehicle_type": "dron", "propeller_diameter_in": 5.0},
        design_properties=_design_properties(
            components={"frame": frame, FRAME_ARM_KEY: arm},
            system_blocks=["structure"], system_priority=["structure"],
        ),
    )
    bom = build_component_bom(state)
    lines = format_bom_lines(bom, state)
    assert "   └ arm — 6mm" in lines


def test_bom_thickness_and_material_and_count_all_render():
    """Combined shape from the IC example:
    '   └ arm ×4 — fibra de carbono, 4mm'."""
    frame = ComponentSpec(
        suggested_key="frame", completeness="high", source="declared",
        properties={
            "mass_kg": PropertyValue(value=0.125),
            "material": PropertyValue(value="fibra de carbono"),
            "size_class_inch": PropertyValue(value=5.0, unit="in"),
        },
    )
    arm = ComponentSpec(
        suggested_key=FRAME_ARM_KEY, completeness="high", source="declared",
        properties={
            "count": PropertyValue(value=4),
            "material": PropertyValue(value="fibra de carbono"),
            "thickness_mm": PropertyValue(value=4.0, unit="mm"),
        },
        parent_key="frame",
    )
    state = _project_state(
        current_parameters={"vehicle_type": "dron", "propeller_diameter_in": 5.0},
        design_properties=_design_properties(
            components={"frame": frame, FRAME_ARM_KEY: arm},
            system_blocks=["structure"], system_priority=["structure"],
        ),
    )
    bom = build_component_bom(state)
    lines = format_bom_lines(bom, state)
    assert "   └ arm ×4 — fibra de carbono, 4mm" in lines


def test_structure_pass_and_evidence_unchanged_with_vs_without_arm_thickness():
    """T6 twin — Structure ERF / _frame_completeness / _structure_evidence
    identical with vs without frame_arm.thickness_mm present."""

    def _state(with_thickness: bool):
        arm_props = {"count": PropertyValue(value=4)}
        if with_thickness:
            arm_props["thickness_mm"] = PropertyValue(value=6.0, unit="mm")
        frame = ComponentSpec(
            suggested_key="frame", completeness="high", source="declared",
            properties={
                "mass_kg": PropertyValue(value=0.4),
                "material": PropertyValue(value="fibra de carbono"),
                "size_class_inch": PropertyValue(value=10.0, unit="in"),
            },
        )
        arm = ComponentSpec(
            suggested_key=FRAME_ARM_KEY, completeness="high", source="declared",
            properties=arm_props, parent_key="frame",
        )
        return _project_state(
            current_parameters={"vehicle_type": "dron", "propeller_diameter_in": 10.0},
            latest_results={
                "simulation": {"status": "pass", "can_fly": True, "quality": "good", "safety_margin_ratio": 1.5, "warnings": []},
                "calculations": {"total_mass_kg": 1.5},
            },
            design_properties=_design_properties(
                components={"frame": frame, FRAME_ARM_KEY: arm},
                system_blocks=["structure"], system_priority=["structure"],
            ),
        )

    without = build_engineering_readiness(_state(with_thickness=False))
    with_thickness = build_engineering_readiness(_state(with_thickness=True))
    assert without.subsystems["structure"] == with_thickness.subsystems["structure"]
    assert without.overall == with_thickness.overall
    assert with_thickness.subsystems["structure"].verdict == "PASS"


def test_frame_part_specs_from_catalog_tbs_5in_arm_and_three_plates_no_cage_standoff():
    """Frame Assembly Physical Model B2, T2 — TBS 5in has a sourced
    arm_thickness_mm (arms B2) *and* a curated 3-plate list (Top/Middle/
    Bottom); still no cage/standoff (never stated on its page). Supersedes
    the pre-this-IC "arm-thickness-only" shape."""
    parts = frame_part_specs_from_catalog("tbs_source_one_v5_5in")
    assert set(parts.keys()) == {FRAME_ARM_KEY, "frame_plate", "frame_plate_2", "frame_plate_3"}
    assert parts[FRAME_ARM_KEY].properties["thickness_mm"].value == pytest.approx(6.0)
    assert "material" not in parts[FRAME_ARM_KEY].properties
    assert "count" not in parts[FRAME_ARM_KEY].properties
    assert parts["frame_plate"].properties["label"].value == "Top"
    assert parts["frame_plate"].properties["thickness_mm"].value == pytest.approx(2.0)
    assert parts["frame_plate_2"].properties["label"].value == "Middle"
    assert parts["frame_plate_3"].properties["label"].value == "Bottom"
    assert parts["frame_plate_3"].properties["thickness_mm"].value == pytest.approx(2.5)
    assert FRAME_CAGE_KEY not in parts
    assert FRAME_STANDOFF_KEY not in parts


def test_upsert_frame_part_merges_and_sets_parent_key(tmp_path):
    from jarvis.core.orchestrator import JarvisOrchestrator

    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "test", "payload_kg": 1.0,
            "restrictions": "ninguna", "detail_level": "conceptual",
            "motors": 4, "per_motor_max_thrust_n": 12.0,
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    ps = set_frame_material(ps, 0.4, "fibra de carbono", 5.0)
    ps = upsert_frame_part(ps, FRAME_ARM_KEY, {"count": PropertyValue(value=4)})
    arm = ps.design_properties.components[FRAME_ARM_KEY]
    assert arm.parent_key == "frame"
    assert arm.properties["count"].value == 4
    assert arm.completeness == "high"


# ── Frame Assembly Physical Model B2 — N2 precedence, BOM, twin ─────────────

def test_n2_plates_present_ignores_legacy_scalar_material_and_count(tmp_path):
    """N2 lock, T4 — when a seed row sets BOTH the legacy plate_material/
    plate_count scalars AND a curated plates list, projection reads ONLY
    from plates; the scalars never leak in as a fifth/conflicting path."""
    from jarvis.knowledge.library import ComponentLibrary

    (tmp_path / "frames").mkdir()
    (tmp_path / "frames" / "_datos.json").write_text(
        """
        {"synthetic_frame": {
            "mass_g": 100, "size_class_inch": 5,
            "plate_material": "legacy-should-be-ignored",
            "plate_count": 99,
            "plates": [{"label": "Only", "thickness_mm": 3.0, "material": "fibra de carbono"}]
        }}
        """,
        encoding="utf-8",
    )
    lib = ComponentLibrary(library_root=tmp_path)
    parts = frame_part_specs_from_catalog("synthetic_frame", library=lib)
    assert set(k for k in parts if is_frame_plate_key(k)) == {"frame_plate"}
    plate = parts["frame_plate"]
    assert plate.properties["label"].value == "Only"
    assert plate.properties["material"].value == "fibra de carbono"
    assert "count" not in plate.properties
    assert plate.properties["material"].value != "legacy-should-be-ignored"


def test_bom_renders_distinct_labeled_plate_lines_in_ordinal_order():
    """T6 — BOM renders one └ plate line per curated plate sibling, in
    ordinal order, each showing its own label + thickness."""
    frame = ComponentSpec(
        suggested_key="frame", completeness="high", source="declared",
        properties={
            "mass_kg": PropertyValue(value=0.1235),
            "size_class_inch": PropertyValue(value=5.0, unit="in"),
        },
    )
    components = {"frame": frame}
    for spec in frame_part_specs_from_catalog("tbs_source_one_v5_5in").values():
        components[spec.suggested_key] = spec
    state = _project_state(
        current_parameters={"vehicle_type": "dron", "propeller_diameter_in": 5.0},
        design_properties=_design_properties(
            components=components, system_blocks=["structure"], system_priority=["structure"],
        ),
    )
    bom = build_component_bom(state)
    lines = format_bom_lines(bom, state)
    frame_idx = next(i for i, line in enumerate(lines) if line.startswith("✓ frame"))
    plate_lines = lines[frame_idx + 2 : frame_idx + 5]
    assert plate_lines == [
        "   └ plate — Top, 2mm",
        "   └ plate — Middle, 2mm",
        "   └ plate — Bottom, 2.5mm",
    ]


def test_structure_pass_and_evidence_unchanged_with_vs_without_plate_siblings():
    """T7 twin — Structure ERF / _frame_completeness / _structure_evidence
    identical with vs without curated plate siblings present."""

    def _state(with_plates: bool):
        components = {
            "frame": ComponentSpec(
                suggested_key="frame", completeness="high", source="declared",
                properties={
                    "mass_kg": PropertyValue(value=0.4),
                    "material": PropertyValue(value="fibra de carbono"),
                    "size_class_inch": PropertyValue(value=10.0, unit="in"),
                },
            ),
        }
        if with_plates:
            for spec in frame_part_specs_from_catalog("armattan_rooster_5in").values():
                components[spec.suggested_key] = spec
        return _project_state(
            current_parameters={"vehicle_type": "dron", "propeller_diameter_in": 10.0},
            latest_results={
                "simulation": {"status": "pass", "can_fly": True, "quality": "good", "safety_margin_ratio": 1.5, "warnings": []},
                "calculations": {"total_mass_kg": 1.5},
            },
            design_properties=_design_properties(
                components=components, system_blocks=["structure"], system_priority=["structure"],
            ),
        )

    without = build_engineering_readiness(_state(with_plates=False))
    with_plates = build_engineering_readiness(_state(with_plates=True))
    assert without.subsystems["structure"] == with_plates.subsystems["structure"]
    assert without.overall == with_plates.overall
    assert with_plates.subsystems["structure"].verdict == "PASS"
