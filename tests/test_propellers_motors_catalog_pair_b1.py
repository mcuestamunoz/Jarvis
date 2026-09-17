"""Propellers<->motors catalog-pair evidence B1 (`B1-propellers-motors-catalog-pair`).

Covers implementation_contract_propellers_motors_catalog_pair_b1.md §2:

  T1  Both catalog-bound + match_motor_propeller true -> catalog_pair_ok
  T2  Both bound + match false -> catalog_pair_mismatch
  T3  Motor or prop unbound / wrong family -> catalog_pair_unverifiable
  T4  motors<->frame_arm still uses station_reach_* (no regression)
  T5  screen_posed_envelope still child_not_box for disks -- unchanged
  T6  Copy asserts catalog-pair honesty; forbids cabe/alcance/hub/eje/VERIFIED fisico
  T7  When both bound, row outcome matches evaluate_electrical_compatibility(...).prop_motor
  T8  Full pytest green (checked at the repo level)
"""
from __future__ import annotations

from types import SimpleNamespace

from jarvis.core.electrical_compatibility import evaluate_electrical_compatibility
from jarvis.core.fit_relations_assist import assess_fit_relations, format_fit_relations_checklist
from jarvis.core.pose_envelope_screening import screen_posed_envelope
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, PropertyValue
from jarvis.workspace.spatial_board import _geometry_from_spec

# Known-compatible pair (5" motor band, 5.1" prop within +-1.0")
_MOTOR_SKU = "iflight_xing_e_pro_2207_2450"
_PROP_SKU_COMPATIBLE = "gemfan_hurricane_mck_51466_3_v2"
# Known-incompatible pair: a 10" propeller against the same 5"-band motor.
_PROP_SKU_MISMATCH = "apc_10x6_ep"


def _frame() -> ComponentSpec:
    return ComponentSpec(suggested_key="frame", completeness="high", properties={
        "configuration": PropertyValue(value="quad_x", unit=None, confidence=0.9, source="declared"),
        "wheelbase_mm": PropertyValue(value=225.0, unit="mm", confidence=0.95, source="declared"),
    })


def _arm() -> ComponentSpec:
    return ComponentSpec(suggested_key="frame_arm", completeness="high", properties={
        "length_mm": PropertyValue(value=80.0, unit="mm", confidence=0.9, source="declared"),
    })


def _motors(*, catalog_ref: CatalogRef | None = None) -> ComponentSpec:
    return ComponentSpec(
        suggested_key="motors", completeness="high", mounted_on="frame_arm", catalog_ref=catalog_ref,
        properties={
            "diameter_mm": PropertyValue(value=27.9, unit="mm", confidence=0.9, source="declared"),
            "height_mm": PropertyValue(value=31.7, unit="mm", confidence=0.9, source="declared"),
        },
    )


def _propellers(*, catalog_ref: CatalogRef | None = None) -> ComponentSpec:
    return ComponentSpec(
        suggested_key="propellers", completeness="high", mounted_on="motors", catalog_ref=catalog_ref,
        properties={"diameter_in": PropertyValue(value=5.1, unit="in", confidence=0.9, source="declared")},
    )


def _components(**overrides) -> dict[str, ComponentSpec]:
    base = {"frame": _frame(), "frame_arm": _arm(), "motors": _motors(), "propellers": _propellers()}
    base.update(overrides)
    return base


def _propellers_row(components):
    assessment = assess_fit_relations(components)
    return next(r for r in assessment.rows if r.child == "propellers")


# ── T1 ────────────────────────────────────────────────────────────────────


def test_t1_both_bound_compatible_is_catalog_pair_ok():
    components = _components(
        motors=_motors(catalog_ref=CatalogRef(family="motor", sku=_MOTOR_SKU)),
        propellers=_propellers(catalog_ref=CatalogRef(family="propeller", sku=_PROP_SKU_COMPATIBLE)),
    )
    row = _propellers_row(components)
    assert row.status == "catalog_pair_ok"


# ── T2 ────────────────────────────────────────────────────────────────────


def test_t2_both_bound_incompatible_is_catalog_pair_mismatch():
    components = _components(
        motors=_motors(catalog_ref=CatalogRef(family="motor", sku=_MOTOR_SKU)),
        propellers=_propellers(catalog_ref=CatalogRef(family="propeller", sku=_PROP_SKU_MISMATCH)),
    )
    row = _propellers_row(components)
    assert row.status == "catalog_pair_mismatch"


# ── T3 ────────────────────────────────────────────────────────────────────


def test_t3_unbound_motor_is_catalog_pair_unverifiable():
    components = _components(
        motors=_motors(catalog_ref=None),
        propellers=_propellers(catalog_ref=CatalogRef(family="propeller", sku=_PROP_SKU_COMPATIBLE)),
    )
    assert _propellers_row(components).status == "catalog_pair_unverifiable"


def test_t3_unbound_propeller_is_catalog_pair_unverifiable():
    components = _components(
        motors=_motors(catalog_ref=CatalogRef(family="motor", sku=_MOTOR_SKU)),
        propellers=_propellers(catalog_ref=None),
    )
    assert _propellers_row(components).status == "catalog_pair_unverifiable"


def test_t3_wrong_family_is_catalog_pair_unverifiable():
    components = _components(
        motors=_motors(catalog_ref=CatalogRef(family="motor", sku=_MOTOR_SKU)),
        propellers=_propellers(catalog_ref=CatalogRef(family="motor", sku=_MOTOR_SKU)),
    )
    assert _propellers_row(components).status == "catalog_pair_unverifiable"


def test_t3_neither_present_is_catalog_pair_unverifiable_never_silent_n_a_disk():
    components = _components(motors=_motors(), propellers=_propellers())
    row = _propellers_row(components)
    assert row.status == "catalog_pair_unverifiable"
    assert row.status != "n_a_disk"


# ── T4 ────────────────────────────────────────────────────────────────────


def test_t4_motors_frame_arm_still_uses_station_reach_unaffected():
    components = _components(
        motors=_motors(catalog_ref=CatalogRef(family="motor", sku=_MOTOR_SKU)),
        propellers=_propellers(catalog_ref=CatalogRef(family="propeller", sku=_PROP_SKU_COMPATIBLE)),
    )
    assessment = assess_fit_relations(components)
    motors_row = next(r for r in assessment.rows if r.child == "motors")
    assert motors_row.status == "station_reach_ok"


# ── T5 ────────────────────────────────────────────────────────────────────


def test_t5_screen_posed_envelope_unchanged_for_propellers():
    components = _components()
    screening = screen_posed_envelope(components["propellers"], components)
    assert screening.status == "no_pose"
    geometry = _geometry_from_spec(components["propellers"])
    assert geometry["shape"] == "disk"  # diameter_in alone, no hub_thickness_mm in this fixture


# ── T6 ────────────────────────────────────────────────────────────────────


def test_t6_copy_asserts_catalog_pair_honesty_and_forbidden_tokens():
    forbidden = ("cabe", "alcance", "hub", "eje", "clearance", "combo exacto de empuje", "VERIFIED")

    ok_components = _components(
        motors=_motors(catalog_ref=CatalogRef(family="motor", sku=_MOTOR_SKU)),
        propellers=_propellers(catalog_ref=CatalogRef(family="propeller", sku=_PROP_SKU_COMPATIBLE)),
    )
    ok_row = _propellers_row(ok_components)
    assert "emparejamiento de catálogo" in ok_row.reason
    for token in forbidden:
        assert token not in ok_row.reason

    mismatch_components = _components(
        motors=_motors(catalog_ref=CatalogRef(family="motor", sku=_MOTOR_SKU)),
        propellers=_propellers(catalog_ref=CatalogRef(family="propeller", sku=_PROP_SKU_MISMATCH)),
    )
    mismatch_row = _propellers_row(mismatch_components)
    assert "emparejamiento" in mismatch_row.reason
    for token in forbidden:
        assert token not in mismatch_row.reason

    unverifiable_row = _propellers_row(_components())
    assert "emparejamiento de catálogo" in unverifiable_row.reason
    for token in forbidden:
        assert token not in unverifiable_row.reason

    checklist_text = format_fit_relations_checklist(assess_fit_relations(ok_components))
    assert "emparejamiento de catálogo" in checklist_text
    propellers_line = next(line for line in checklist_text.splitlines() if "propellers" in line)
    for token in forbidden:
        assert token not in propellers_line


# ── T7 ────────────────────────────────────────────────────────────────────


def test_t7_row_outcome_matches_erf_prop_motor_check_ok():
    components = _components(
        motors=_motors(catalog_ref=CatalogRef(family="motor", sku=_MOTOR_SKU)),
        propellers=_propellers(catalog_ref=CatalogRef(family="propeller", sku=_PROP_SKU_COMPATIBLE)),
    )
    row_status = _propellers_row(components).status
    project_state = SimpleNamespace(
        design_properties=SimpleNamespace(components=components),
        current_parameters={},
        latest_results={},
    )
    erf_outcome = evaluate_electrical_compatibility(project_state).prop_motor
    assert erf_outcome == "compatible"
    assert row_status == "catalog_pair_ok"


def test_t7_row_outcome_matches_erf_prop_motor_check_mismatch():
    components = _components(
        motors=_motors(catalog_ref=CatalogRef(family="motor", sku=_MOTOR_SKU)),
        propellers=_propellers(catalog_ref=CatalogRef(family="propeller", sku=_PROP_SKU_MISMATCH)),
    )
    row_status = _propellers_row(components).status
    project_state = SimpleNamespace(
        design_properties=SimpleNamespace(components=components),
        current_parameters={},
        latest_results={},
    )
    erf_outcome = evaluate_electrical_compatibility(project_state).prop_motor
    assert erf_outcome == "mismatch"
    assert row_status == "catalog_pair_mismatch"


def test_t7_row_outcome_matches_erf_prop_motor_check_unverifiable():
    components = _components()
    row_status = _propellers_row(components).status
    project_state = SimpleNamespace(
        design_properties=SimpleNamespace(components=components),
        current_parameters={},
        latest_results={},
    )
    erf_outcome = evaluate_electrical_compatibility(project_state).prop_motor
    assert erf_outcome == "unverifiable"
    assert row_status == "catalog_pair_unverifiable"


def test_t7_no_human_attest_path_for_catalog_pair():
    """IC lock #8 — no attest exists for this evidence class: catalog_pair_ok
    is never `attested` and never offers a `suggest` phrase."""
    components = _components(
        motors=_motors(catalog_ref=CatalogRef(family="motor", sku=_MOTOR_SKU)),
        propellers=_propellers(catalog_ref=CatalogRef(family="propeller", sku=_PROP_SKU_COMPATIBLE)),
    )
    row = _propellers_row(components)
    assert row.status != "attested"
    assert row.suggest is None
