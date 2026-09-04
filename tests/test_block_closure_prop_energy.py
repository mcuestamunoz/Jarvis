"""Block Closure B-PROP-ENERGY — derivable rollup + battery SKU re-bind.

investigation_report_post_v034_block_closure.md ·
implementation_contract_block_closure_prop_energy.md

Drives the real orchestrator (no LLM, no hand-built simulation.status) for
every Gate A trace — matching the investigation's own methodology. Combo A:
sunnysky_r2205_2500 + gf_5045x3 + lipo_4s_1500mah + freeform ESC 60A.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from jarvis.core.project_closure import derive_prop_energy_block_closure
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _build_combo_a(tmp_root: Path, *, motor_count: int, payload_kg: float, bind_esc: bool = True):
    from jarvis.core.catalog_bind import bind_battery_from_catalog, bind_motor_from_catalog, bind_propeller_from_catalog
    from jarvis.core.component_writers import set_battery_component, set_control_component, set_motor_component, set_propeller_component
    from jarvis.core.orchestrator import JarvisOrchestrator
    from jarvis.knowledge.library import default_library

    orch = JarvisOrchestrator(workspace_root=tmp_root)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "block closure combo A", "payload_kg": payload_kg,
            "restrictions": "no", "detail_level": "conceptual", "motors": motor_count,
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    ps = ps.model_copy(update={"current_parameters": {**ps.current_parameters, "motor_count": motor_count}})
    ps = set_propeller_component(ps, bind_propeller_from_catalog("gf_5045x3"))
    m = default_library.get_motor("sunnysky_r2205_2500")
    motor_spec = bind_motor_from_catalog({
        "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
        "kv_rating": m.kv_rating, "weight_g": m.weight_g, "is_generic": m.is_generic,
    })
    ps = set_motor_component(ps, motor_spec, m.max_watts)
    battery_spec = bind_battery_from_catalog("lipo_4s_1500mah")
    ps = set_battery_component(ps, battery_spec, battery_spec.properties["battery_capacity_wh"].value)
    if bind_esc:
        esc_spec = ComponentSpec(
            name="esc 60a", suggested_key="esc", component_type="power_electronics",
            completeness="high", properties={"current_a": PropertyValue(value=60.0, unit="A", confidence=0.8, source="declared")},
        )
        ps = set_control_component(ps, esc_spec)
    orch.workspace_manager.save_state(ps)

    llm = _RefuseLLM()
    orch.handle_user_text("calcular", llm)
    orch.handle_user_text("simular", llm)
    return orch


def test_gate_a_compatible_block_closed_manufacturer_test():
    with tempfile.TemporaryDirectory() as tmp:
        orch = _build_combo_a(Path(tmp), motor_count=2, payload_kg=0.5)
        ps = orch.state_manager.load_active_project(orch.workspace_manager)

        assert ps.latest_results["simulation"]["status"] == "pass"
        result = derive_prop_energy_block_closure(ps)
        assert result["status"] == "closed"
        assert result["evidence_tier"] == "manufacturer_test"
        assert result["reasons"] == []
        assert result["block_id"] == "B-PROP-ENERGY"

        from jarvis.adapters.cli.main import render_startup_context
        rendered = render_startup_context(orch.build_startup_context())
        assert (
            "BLOQUE PROPULSIÓN/ENERGÍA: CERRADO — evidencia manufacturer_test "
            "(punto de operación coincidente)"
        ) in rendered
        assert "PROJECT STATUS:" in rendered


def test_dual_block_closed_not_assembly_ready():
    """Same propulsion/energy/electronics stack as the compatible case, but
    frame/flight_controller/sensors were never declared — overall must be
    NOT_ASSEMBLY_READY while the block is still closed (Finding B-3: the
    two questions are independent, this is the point, not a bug)."""
    with tempfile.TemporaryDirectory() as tmp:
        orch = _build_combo_a(Path(tmp), motor_count=2, payload_kg=0.5)
        ps = orch.state_manager.load_active_project(orch.workspace_manager)

        result = derive_prop_energy_block_closure(ps)
        assert result["status"] == "closed"

        from jarvis.core.engineering_readiness import build_engineering_readiness
        readiness = build_engineering_readiness(ps)
        assert readiness.overall == "NOT_ASSEMBLY_READY"


def test_gate_a_incompatible_battery_discharge_not_closed():
    with tempfile.TemporaryDirectory() as tmp:
        orch = _build_combo_a(Path(tmp), motor_count=4, payload_kg=0.5)
        ps = orch.state_manager.load_active_project(orch.workspace_manager)

        # Thrust feasibility is untouched by this IC — do not "fix" it.
        assert ps.latest_results["simulation"]["status"] == "pass"

        result = derive_prop_energy_block_closure(ps)
        assert result["status"] == "not_closed"
        assert "battery_discharge_exceeded" in result["reasons"]
        assert result["facts"]["battery_discharge"] == "exceeded"

        from jarvis.adapters.cli.main import render_startup_context
        rendered = render_startup_context(orch.build_startup_context())
        assert "BLOQUE PROPULSIÓN/ENERGÍA: NO CERRADO — descarga de batería excedida" in rendered

        from jarvis.core.engineering_readiness import build_engineering_readiness
        readiness = build_engineering_readiness(ps)
        assert readiness.overall == "NOT_ASSEMBLY_READY"


def test_unverifiable_discharge_does_not_claim_exceeded():
    """N1 (implementation_review_block_closure_prop_energy.md): CLI
    feasibility fixture emax_rs2205s_2300 + hq_5045_bn + lipo_4s_10000mah,
    no ESC declared -> battery_discharge is unverifiable, NOT exceeded.
    The locked 'descarga de batería excedida' sentence is a specific claim
    and must not be printed for a merely-unverifiable discharge (same class
    of lie as the old 'sin hélice de catálogo' bug)."""
    with tempfile.TemporaryDirectory() as tmp:
        from jarvis.core.catalog_bind import bind_battery_from_catalog, bind_motor_from_catalog, bind_propeller_from_catalog
        from jarvis.core.component_writers import set_battery_component, set_motor_component, set_propeller_component
        from jarvis.core.orchestrator import JarvisOrchestrator
        from jarvis.knowledge.library import default_library

        orch = JarvisOrchestrator(workspace_root=Path(tmp))
        orch.handle({
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron", "objective": "autonomía de 5 min", "payload_kg": 1.0,
                "restrictions": "no", "detail_level": "conceptual", "motors": 4,
                "structure_mass_factor": 0.6, "safety_factor": 1.2,
            },
        })
        ps = orch.state_manager.load_active_project(orch.workspace_manager)

        prop_spec = bind_propeller_from_catalog("hq_5045_bn")
        ps = set_propeller_component(ps, prop_spec)

        m = default_library.get_motor("emax_rs2205s_2300")
        motor_spec = bind_motor_from_catalog({
            "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
            "kv_rating": m.kv_rating, "weight_g": m.weight_g, "is_generic": m.is_generic,
        })
        ps = set_motor_component(ps, motor_spec, m.max_watts)

        battery_spec = bind_battery_from_catalog("lipo_4s_10000mah")
        ps = set_battery_component(ps, battery_spec, battery_spec.properties["battery_capacity_wh"].value)
        ps = ps.model_copy(update={"parsed_constraints": {"autonomy_min": 5.0}})
        orch.workspace_manager.save_state(ps)

        llm = _RefuseLLM()
        orch.handle_user_text("calcular", llm)
        orch.handle_user_text("simular", llm)
        ps = orch.state_manager.load_active_project(orch.workspace_manager)

        result = derive_prop_energy_block_closure(ps)
        assert result["status"] == "not_closed"
        assert result["facts"]["battery_discharge"] != "exceeded"

        from jarvis.adapters.cli.main import render_startup_context
        rendered = render_startup_context(orch.build_startup_context())
        assert "descarga de batería excedida" not in rendered
        assert (
            "BLOQUE PROPULSIÓN/ENERGÍA: NO CERRADO — el stack de propulsión/energía "
            "no está cerrado"
        ) in rendered


def test_unbound_propeller_is_not_closed():
    """Motor catalog-bound, propeller freeform (no catalog_ref) -> not_closed
    on the catalog-identity condition (§3.2 #9), independent of whatever the
    electrical checks say."""
    with tempfile.TemporaryDirectory() as tmp:
        from jarvis.core.catalog_bind import bind_battery_from_catalog, bind_motor_from_catalog
        from jarvis.core.component_writers import set_battery_component, set_motor_component
        from jarvis.core.orchestrator import JarvisOrchestrator
        from jarvis.knowledge.library import default_library

        orch = JarvisOrchestrator(workspace_root=Path(tmp))
        orch.handle({
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron", "objective": "unbound propeller", "payload_kg": 0.5,
                "restrictions": "no", "detail_level": "conceptual", "motors": 2,
                "structure_mass_factor": 0.5, "safety_factor": 1.2,
            },
        })
        ps = orch.state_manager.load_active_project(orch.workspace_manager)
        ps = ps.model_copy(update={"current_parameters": {**ps.current_parameters, "motor_count": 2}})
        m = default_library.get_motor("sunnysky_r2205_2500")
        motor_spec = bind_motor_from_catalog({
            "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
            "kv_rating": m.kv_rating, "weight_g": m.weight_g, "is_generic": m.is_generic,
        })
        ps = set_motor_component(ps, motor_spec, m.max_watts)
        battery_spec = bind_battery_from_catalog("lipo_4s_1500mah")
        ps = set_battery_component(ps, battery_spec, battery_spec.properties["battery_capacity_wh"].value)
        orch.workspace_manager.save_state(ps)

        result = derive_prop_energy_block_closure(ps)
        assert result["status"] == "not_closed"
        assert "propellers_not_catalog_bound" in result["reasons"]


def test_battery_rebind_definir_bateria():
    with tempfile.TemporaryDirectory() as tmp:
        orch = _build_combo_a(Path(tmp), motor_count=2, payload_kg=0.5, bind_esc=False)
        llm = _RefuseLLM()
        result = orch.handle_user_text("definir bateria lipo_6s_10000mah", llm)
        assert result["status"] == "ok"

        ps = orch.state_manager.load_active_project(orch.workspace_manager)
        ref = ps.design_properties.components["battery"].catalog_ref
        assert ref is not None
        assert ref.family == "battery"
        assert ref.sku == "lipo_6s_10000mah"
        assert ps.current_parameters["battery_capacity_wh"] == pytest.approx(222.0)
        assert ps.current_parameters["battery_capacity_wh"] != 6.0


def test_battery_rebind_cambia_la_bateria_a():
    with tempfile.TemporaryDirectory() as tmp:
        orch = _build_combo_a(Path(tmp), motor_count=2, payload_kg=0.5, bind_esc=False)
        llm = _RefuseLLM()
        result = orch.handle_user_text("cambia la bateria a lipo_6s_10000mah", llm)
        assert result["status"] == "ok"

        ps = orch.state_manager.load_active_project(orch.workspace_manager)
        ref = ps.design_properties.components["battery"].catalog_ref
        assert ref is not None
        assert ref.family == "battery"
        assert ref.sku == "lipo_6s_10000mah"
        assert ps.current_parameters["battery_capacity_wh"] == pytest.approx(222.0)
        assert ps.current_parameters["battery_capacity_wh"] != 6.0


def test_bare_definir_bateria_keeps_wizard_behavior():
    """No SKU named -> today's wizard/catalog-offer behavior, unaffected by
    the SKU-detection intercept (it never matches without a real SKU token)."""
    with tempfile.TemporaryDirectory() as tmp:
        orch = _build_combo_a(Path(tmp), motor_count=2, payload_kg=0.5, bind_esc=False)
        llm = _RefuseLLM()
        result = orch.handle_user_text("definir bateria", llm)
        assert result["status"] in ("ok", "interactive")
        ps = orch.state_manager.load_active_project(orch.workspace_manager)
        # Existing catalog-bound battery must survive an SKU-less mention.
        assert ps.design_properties.components["battery"].catalog_ref is not None
