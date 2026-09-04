"""CLI feasibility vs readiness semantics IC — end-to-end field-fixture unit.

Reproduces workspace/autonomía-de-5min-c09442c25db0 via the real orchestrator
(no LLM): emax_rs2205s_2300 (catalog-bound, no nameplate max_watts) +
hq_5045_bn propeller (catalog-bound) + a 4S battery + an autonomy_min=5.0
constraint. Thrust feasibility PASSes; the energy model cannot run
(motor_power_w absent, honestly). Asserts the claim-language fixes from
investigation_report_cli_feasibility_semantics.md §2-§5 hold together on
one real state, not just in isolated unit fixtures.

investigation_report_cli_feasibility_semantics.md ·
implementation_contract_cli_feasibility_semantics.md
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _field_fixture_state(tmp_root: Path):
    from jarvis.core.catalog_bind import bind_battery_from_catalog, bind_motor_from_catalog, bind_propeller_from_catalog
    from jarvis.core.component_writers import set_battery_component, set_motor_component, set_propeller_component
    from jarvis.core.orchestrator import JarvisOrchestrator
    from jarvis.knowledge.library import default_library

    orch = JarvisOrchestrator(workspace_root=tmp_root)
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
    assert m.max_watts is None, "fixture assumes this SKU has no nameplate wattage"
    motor_spec = bind_motor_from_catalog({
        "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
        "kv_rating": m.kv_rating, "weight_g": m.weight_g, "is_generic": m.is_generic,
    })
    ps = set_motor_component(ps, motor_spec, m.max_watts)

    battery_spec = bind_battery_from_catalog("lipo_4s_10000mah")
    ps = set_battery_component(
        ps, battery_spec, battery_spec.properties["battery_capacity_wh"].value
    )

    # Real user objective: an autonomy constraint the energy model cannot
    # currently evaluate — the exact shape the field fixture had.
    ps = ps.model_copy(update={"parsed_constraints": {"autonomy_min": 5.0}})
    orch.workspace_manager.save_state(ps)
    return orch


def test_field_fixture_claim_language():
    from jarvis.adapters.cli.main import render_response, render_startup_context

    with tempfile.TemporaryDirectory(prefix="jarvis-test-cli-feasibility-") as tmp:
        orch = _field_fixture_state(Path(tmp))
        llm = _RefuseLLM()

        calc_result = orch.handle_user_text("calcular", llm)
        assert calc_result["status"] == "ok"
        assert calc_result["calculations"]["autonomy_min"] is None  # physics unchanged
        calc_rendered = render_response(calc_result)
        # (c) named negative, not silent, not a fake minute.
        assert "autonomía=no calculada" in calc_rendered
        assert "autonomía real" not in calc_rendered.lower()

        sim_result = orch.handle_user_text("simular", llm)
        assert sim_result["status"] == "ok"
        assert sim_result["simulation"]["status"] == "pass"  # thrust feasibility unchanged
        assert sim_result["simulation"]["autonomy_min"] is None
        sim_rendered = render_response(sim_result)
        assert "autonomía=no calculada" in sim_rendered

        ctx = orch.build_startup_context()
        estado_rendered = render_startup_context(ctx)

        # (a) next step / CTA does not ask the user to invent motor_power_w.
        assert "Declarar motor_power_w" not in estado_rendered
        assert ctx.get("proactive_question") is None or "motor_power_w" not in ctx["proactive_question"]

        # (b) situation is thrust-feasibility-scoped, not an autonomy claim.
        continuity = ctx.get("continuity") or {}
        assert "Diseño validado en simulación (PASS)" not in continuity.get("situation", "")
        assert "Comprobación de empuje" in continuity.get("situation", "")

        # (d) fallback suffix reflects BOM identity (propeller IS catalog-bound).
        assert "(sin hélice de catálogo)" not in estado_rendered
        assert "fallback de fabricante" in estado_rendered

        # ERF / ASSEMBLY_READY untouched by this IC (§4 non-goal) — ancillary
        # sanity check, not a new claim this test is asserting ownership of.
        readiness = ctx.get("readiness") or {}
        subsystems = readiness.get("subsystems") or {}
        energy = subsystems.get("energy") or {}
        assert energy.get("verdict") == "PASS"
