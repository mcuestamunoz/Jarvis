"""ERF-1 Slice 4 — Continuity handoff.

Covers .jes/artifacts/implementation_contract_erf1.md §7 Slice 4:
  - build_project_continuity accepts readiness as a NEW optional kw-only param
  - next_useful_step/why for the catalog-gap ranking now derive from
    readiness.top_gap / readiness.subsystems["catalog"]
  - G9-B demotion narration preserved when top gap is the demoted catalog gap
  - byte-identical legacy behavior when readiness is omitted
"""
from __future__ import annotations

from types import SimpleNamespace

from jarvis.core.engineering_readiness import build_engineering_readiness
from jarvis.core.project_continuity import build_project_continuity
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


def _motor_spec(kv=None):
    props = {}
    if kv is not None:
        props["kv_rating"] = PropertyValue(value=kv, unit="KV")
    return ComponentSpec(
        component_type="propulsion_active",
        suggested_key="motors",
        completeness="high",
        properties=props,
        source="declared",
    )


def _catalog_gap_state():
    """A' continuity-bom style fixture: sim PASS, declared thrust covers the
    floor, 2400KV+10in has zero catalog matches -> genuine G9-B demotion.

    Frame declares a compatible size_class_inch (Structure A,
    implementation_contract_structure_a.md §2.2) so the unrelated
    class-compatibility rank never fires here — this fixture is about G9-B
    catalog demotion, not structure.
    """
    return _project_state(
        current_parameters={
            "vehicle_type": "dron",
            "per_motor_max_thrust_n": 30.0,
            "motor_count": 6,
            "propeller_diameter_in": 10.0,
        },
        latest_results={
            "simulation": {"status": "pass", "safety_margin_ratio": 9.1},
            "calculations": {"required_thrust_n": 19.8, "total_mass_kg": 1.5},
        },
        design_properties=_design_properties(components={
            "motors": _motor_spec(kv=2400),
            "frame": ComponentSpec(
                component_type="structure",
                suggested_key="frame",
                completeness="high",
                properties={"size_class_inch": PropertyValue(value=10.0, unit="in")},
                source="declared",
            ),
        }),
    )


def _build_continuity_args(project_state, motor_catalog_gap, readiness=None):
    from jarvis.core.project_closure import build_component_bom, derive_physical_requirements

    req = derive_physical_requirements(project_state)
    bom = build_component_bom(project_state)
    sim = (project_state.latest_results or {}).get("simulation") or {}
    return dict(
        project_state=project_state,
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress=None,
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements=req,
        component_bom=bom,
        energy_model_note=None,
        motor_catalog_gap=motor_catalog_gap,
        motor_catalog_matches=[],
        readiness=readiness,
    )


def test_continuity_uses_readiness_top_gap():
    """A mock/real readiness whose top_gap is the (non-demoted) motor catalog
    gap drives the same 'Declara empuje' branch as the legacy computation."""
    state = _project_state(
        current_parameters={
            "vehicle_type": "dron",
            "per_motor_max_thrust_n": 2.0,
            "motor_count": 6,
            "propeller_diameter_in": 10.0,
        },
        latest_results={
            "simulation": {"status": "pass", "safety_margin_ratio": 1.0},
            "calculations": {"required_thrust_n": 19.8, "total_mass_kg": 1.5},
        },
        design_properties=_design_properties(components={"motors": _motor_spec(kv=2400)}),
    )
    readiness = build_engineering_readiness(state)
    assert readiness.top_gap is not None
    assert readiness.top_gap.gap_type == "GAP-MOTOR-CATALOG-UNRESOLVED"

    gap_msg = "Necesitas empuje ≥ 3.3 N/motor; no tengo un motor en el catálogo."
    cont = build_project_continuity(**_build_continuity_args(state, gap_msg, readiness=readiness))
    assert "Declara empuje" in cont["next_useful_step"]


def test_continuity_g9b_regression():
    """G9-B: PASS + declared thrust covers floor -> demoted, via readiness."""
    state = _catalog_gap_state()
    readiness = build_engineering_readiness(state)
    assert readiness.subsystems["catalog"].warning_type == "CATALOG-GAP-DEMOTED-POST-PASS"

    gap_msg = "Necesitas empuje ≥ 3.3 N/motor; no tengo un motor en el catálogo."
    cont = build_project_continuity(**_build_continuity_args(state, gap_msg, readiness=readiness))
    assert "Declara empuje" not in cont["next_useful_step"]
    assert "qué motores" in cont["next_useful_why"].lower()
    assert "explora opciones" in cont["next_useful_why"].lower()


def test_continuity_legacy_path_unchanged_without_readiness():
    """Omitting readiness must reproduce byte-identical output to passing it
    explicitly for the same fixture — the legacy computation and the
    readiness-derived one must agree for every currently-shipped scenario."""
    state = _catalog_gap_state()
    readiness = build_engineering_readiness(state)
    gap_msg = "Necesitas empuje ≥ 3.3 N/motor; no tengo un motor en el catálogo."

    with_readiness = build_project_continuity(
        **_build_continuity_args(state, gap_msg, readiness=readiness)
    )
    without_readiness = build_project_continuity(
        **_build_continuity_args(state, gap_msg, readiness=None)
    )
    assert with_readiness == without_readiness


def test_continuity_readiness_param_defaults_to_none():
    import inspect

    sig = inspect.signature(build_project_continuity)
    assert sig.parameters["readiness"].default is None
    assert sig.parameters["readiness"].kind == inspect.Parameter.KEYWORD_ONLY
