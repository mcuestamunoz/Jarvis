"""Manual CLI probe — Block Closure B-PROP-ENERGY.

Not a substitute for tests/test_block_closure_prop_energy.py (§6.1-6.4 of the
Implementation Contract). Run for human-readable confirmation of the locked
CLI copy and the battery SKU re-bind fix against the real orchestrator.

Usage: python scripts/cli_probe_block_closure_prop_energy.py
"""
from __future__ import annotations

import tempfile
from pathlib import Path


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _build_combo_a(tmp_root: Path, *, motor_count: int, payload_kg: float):
    from jarvis.core.catalog_bind import bind_battery_from_catalog, bind_motor_from_catalog, bind_propeller_from_catalog
    from jarvis.core.component_writers import set_battery_component, set_control_component, set_motor_component, set_propeller_component
    from jarvis.core.orchestrator import JarvisOrchestrator
    from jarvis.knowledge.library import default_library
    from jarvis.schemas.action_schema import ComponentSpec, PropertyValue

    orch = JarvisOrchestrator(workspace_root=tmp_root)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "block closure probe", "payload_kg": payload_kg,
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


def main() -> None:
    from jarvis.adapters.cli.main import render_startup_context
    from jarvis.core.project_closure import derive_prop_energy_block_closure

    print("=== 1) Gate A compatible (motor_count=2) — expect CERRADO / manufacturer_test ===")
    with tempfile.TemporaryDirectory() as tmp:
        orch = _build_combo_a(Path(tmp), motor_count=2, payload_kg=0.5)
        ps = orch.state_manager.load_active_project(orch.workspace_manager)
        print(derive_prop_energy_block_closure(ps))
        rendered = render_startup_context(orch.build_startup_context())
        for line in rendered.splitlines():
            if "BLOQUE PROPULSIÓN" in line:
                print(line)

    print("\n=== 2) Gate A incompatible (motor_count=4) — expect NO CERRADO / discharge ===")
    with tempfile.TemporaryDirectory() as tmp:
        orch = _build_combo_a(Path(tmp), motor_count=4, payload_kg=0.5)
        ps = orch.state_manager.load_active_project(orch.workspace_manager)
        print(derive_prop_energy_block_closure(ps))
        rendered = render_startup_context(orch.build_startup_context())
        for line in rendered.splitlines():
            if "BLOQUE PROPULSIÓN" in line:
                print(line)

    print("\n=== 3) Battery re-bind: 'definir bateria lipo_6s_10000mah' ===")
    with tempfile.TemporaryDirectory() as tmp:
        orch = _build_combo_a(Path(tmp), motor_count=2, payload_kg=0.5)
        llm = _RefuseLLM()
        orch.handle_user_text("definir bateria lipo_6s_10000mah", llm)
        ps = orch.state_manager.load_active_project(orch.workspace_manager)
        ref = ps.design_properties.components["battery"].catalog_ref
        print(f"catalog_ref={ref} battery_capacity_wh={ps.current_parameters.get('battery_capacity_wh')}")

    print("\n=== 4) Battery re-bind: 'cambia la bateria a lipo_6s_10000mah' ===")
    with tempfile.TemporaryDirectory() as tmp:
        orch = _build_combo_a(Path(tmp), motor_count=2, payload_kg=0.5)
        llm = _RefuseLLM()
        orch.handle_user_text("cambia la bateria a lipo_6s_10000mah", llm)
        ps = orch.state_manager.load_active_project(orch.workspace_manager)
        ref = ps.design_properties.components["battery"].catalog_ref
        print(f"catalog_ref={ref} battery_capacity_wh={ps.current_parameters.get('battery_capacity_wh')}")


if __name__ == "__main__":
    main()
