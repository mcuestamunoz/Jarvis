"""ERF-2 Slice 2 — ESC in architecture (★5).

Covers .jes/artifacts/implementation_contract_erf2.md §9 Slice 2:
  - esc added to BLOCK_TO_COMPONENTS["propulsion"]
  - build_component_bom lists esc in 'missing' when architecture expects it
    and no esc component is declared
"""
from __future__ import annotations

from types import SimpleNamespace

from jarvis.core.project_closure import build_component_bom
from jarvis.core.system_architecture_catalog import BLOCK_TO_COMPONENTS
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue


def test_esc_is_part_of_propulsion_block_components():
    keys = BLOCK_TO_COMPONENTS.get("propulsion", [])
    assert "esc" in keys
    assert "motors" in keys
    assert "propellers" in keys


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


def test_bom_lists_esc_missing():
    motors = ComponentSpec(
        suggested_key="motors", completeness="high", source="declared",
        properties={"motor_count": PropertyValue(value=4)},
    )
    propellers = ComponentSpec(
        suggested_key="propellers", completeness="high", source="declared",
        properties={"diameter_in": PropertyValue(value=10.0)},
    )
    state = _project_state(
        design_properties=_design_properties(
            components={"motors": motors, "propellers": propellers},
            system_blocks=["propulsion"],
        ),
    )
    bom = build_component_bom(state)
    assert "esc" in bom["missing"]


def test_bom_does_not_list_esc_missing_when_declared():
    motors = ComponentSpec(
        suggested_key="motors", completeness="high", source="declared",
        properties={"motor_count": PropertyValue(value=4)},
    )
    propellers = ComponentSpec(
        suggested_key="propellers", completeness="high", source="declared",
        properties={"diameter_in": PropertyValue(value=10.0)},
    )
    esc = ComponentSpec(
        suggested_key="esc", completeness="high", source="declared",
        properties={"current_a": PropertyValue(value=30.0)},
    )
    state = _project_state(
        design_properties=_design_properties(
            components={"motors": motors, "propellers": propellers, "esc": esc},
            system_blocks=["propulsion"],
        ),
    )
    bom = build_component_bom(state)
    assert "esc" not in bom["missing"]
    assert "esc" not in [e["key"] for e in bom["incomplete"]]
