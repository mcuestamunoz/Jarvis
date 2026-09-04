"""Manual CLI probe — CLI catalog-assist T1 (misfit re-offer).

Not a substitute for tests/test_cli_catalog_assist_t1.py or the T1 cases in
tests/test_g21_g22_catalog_bind_ux.py / test_project_continuity.py /
test_engineering_readiness_gaps.py / test_energy_params.py. Run for
human-readable confirmation against the real orchestrator, tmp workspace only.

Usage: python scripts/cli_probe_cli_catalog_assist_t1.py
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


def _build(tmp_root: Path, *, motor_sku: str, motor_count: int = 2):
    from jarvis.core.catalog_bind import bind_battery_from_catalog, bind_motor_from_catalog, bind_propeller_from_catalog
    from jarvis.core.component_writers import set_battery_component, set_motor_component, set_propeller_component
    from jarvis.core.orchestrator import JarvisOrchestrator
    from jarvis.knowledge.library import default_library

    orch = JarvisOrchestrator(workspace_root=tmp_root)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "T1 catalog-assist probe", "payload_kg": 0.5,
            "restrictions": "no", "detail_level": "conceptual", "motors": motor_count,
            "structure_mass_factor": 0.6, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    ps = ps.model_copy(update={"current_parameters": {**ps.current_parameters, "motor_count": motor_count}})
    m = default_library.get_motor(motor_sku)
    motor_spec = bind_motor_from_catalog({
        "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
        "kv_rating": m.kv_rating, "weight_g": m.weight_g, "is_generic": m.is_generic,
    })
    ps = set_motor_component(ps, motor_spec, m.max_watts)
    ps = set_propeller_component(ps, bind_propeller_from_catalog("gf_5045x3"))
    battery_spec = bind_battery_from_catalog("lipo_6s_10000mah")
    ps = set_battery_component(ps, battery_spec, battery_spec.properties["battery_capacity_wh"].value)
    orch.workspace_manager.save_state(ps)

    llm = _RefuseLLM()
    orch.handle_user_text("calcular", llm)
    orch.handle_user_text("simular", llm)
    return orch


def main() -> None:
    from jarvis.adapters.cli.main import render_startup_context
    from jarvis.core.engineering_readiness import bound_motor_sku_is_underspec

    print("=== 1) Underspec bound motor (sunnysky_r2305_2500) — IDLE 'ayúdame a elegir' twice ===")
    with tempfile.TemporaryDirectory() as tmp:
        orch = _build(Path(tmp), motor_sku="sunnysky_r2305_2500", motor_count=2)
        ps = orch.state_manager.load_active_project(orch.workspace_manager)
        print("sim status:", ps.latest_results["simulation"]["status"])
        print("underspec:", bound_motor_sku_is_underspec(ps))
        llm = _RefuseLLM()
        r1 = orch.handle_user_text("ayúdame a elegir", llm)
        print("turn 1:", r1.get("message"))
        assert "Filtros relajados" in (r1.get("message") or "") or "Candidatos del catálogo" in (r1.get("message") or "")
        r2 = orch.handle_user_text("ayúdame a elegir", llm)
        print("turn 2 (must not be a stuck repeat of nothing):", r2.get("message"))
        rendered = render_startup_context(orch.build_startup_context())
        for line in rendered.splitlines():
            if "empuje" in line.lower() or "candidat" in line.lower() or "siguiente paso" in line.lower():
                print("estado:", line)

    print("\n=== 2) Covering bound motor (sunnysky_r2205_2500) — G21 must stay a noop ===")
    with tempfile.TemporaryDirectory() as tmp:
        orch = _build(Path(tmp), motor_sku="sunnysky_r2205_2500", motor_count=2)
        ps = orch.state_manager.load_active_project(orch.workspace_manager)
        print("underspec:", bound_motor_sku_is_underspec(ps))
        llm = _RefuseLLM()
        r = orch.handle_user_text("ayúdame a elegir", llm)
        print("result:", r.get("status"), r.get("action"), "-", r.get("message"))

    print("\n=== 3) Watts CTA: r2305 (220W) must not say 'no declara vatios' ===")
    from jarvis.core.reasoning_layer import ReasoningLayer
    layer = ReasoningLayer()
    context = {
        "last_simulation": {"energy_status": "missing_energy_parameters"},
        "current_parameters": {"battery_capacity_wh": 148.0},
        "design_properties": {
            "components": {"motors": {"catalog_ref": {"family": "motor", "sku": "sunnysky_r2305_2500"}}}
        },
    }
    output = layer.build(context)
    print("labels:", [s.label for s in output.suggested_actions])

    print("\n=== 4) Watts CTA: emax_rs2205s_2300 (no watts) must still say it ===")
    context["design_properties"]["components"]["motors"]["catalog_ref"]["sku"] = "emax_rs2205s_2300"
    output = layer.build(context)
    print("labels:", [s.label for s in output.suggested_actions])


if __name__ == "__main__":
    main()
