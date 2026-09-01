"""DSE explore/apply vs motor_op_power_w dual-truth — closed.

Investigation: .jes/artifacts/investigation_report_dse_motor_op_dual_truth.md
Fix (Motor OP Voltage Coherence IC, ★1-★4 ratified):
  MOP-1 (library.py)            — resolve_operating_point no longer treats
                                   an unknown query voltage (voltage_v=None)
                                   as matching every exact row. An exact
                                   match now REQUIRES a known, compatible
                                   voltage.
  MOP-2 (component_writers.py)  — propulsion_resolution now carries
                                   voltage_validated/resolved_at_voltage_v
                                   provenance; set_battery_component
                                   conditionally re-calls set_motor_component
                                   ONLY when the stored resolution was never
                                   voltage-validated, or was validated at a
                                   voltage the new battery no longer matches
                                   (never unconditionally — an already
                                   voltage-validated, still-compatible exact
                                   match must never be re-triggered, per the
                                   locked P2-2/IC2 regression contract in
                                   test_battery_catalog_bind_ux.py).
  MOP-3 (design_explorer.py)    — explore()'s params-only baseline/grid use
                                   LIVE current_parameters directly instead
                                   of a re-normalized copy, so explore never
                                   promises a number "calcular" wouldn't
                                   already show for the same state.

Root cause (closed): a motor/propeller bound before any battery used to
lock in an exact_operating_point resolved with voltage_v=None (auto-matched
everything) — that resolution then survived un-revalidated indefinitely
once a real, possibly-incompatible battery was later bound (battery-only
binds deliberately never re-call set_motor_component, P2-2/IC2). MOP-1
closes the lock-in at the source; MOP-2 closes the "later battery bind
still never revalidates" gap without reopening P2-2/IC2's own protection
for an ALREADY-validated, compatible resolution.

CASE A and CASE B below now PASS — explore's baseline agrees with the live
calc, and applying explore's own top candidate delivers exactly what
explore promised, for the same fixture (motor/propeller bound before a
6S/22.2V battery) that used to reproduce the field-walk cliff
(8.325 min explore vs 7.7083 min live, before the fix).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.catalog_bind import bind_battery_from_catalog, bind_motor_from_catalog, bind_propeller_from_catalog
from jarvis.core.component_writers import set_battery_component, set_motor_component, set_propeller_component
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.knowledge.library import default_library


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


_MOTOR_SKU = "emax_rs2205s_2300"
_PROP_SKU = "hq_5045_bn"
_BATTERY_SKU = "lipo_6s_10000mah"  # 6S / 22.2V nominal


def _project_with_motor_bound_before_battery(tmp_path: Path) -> JarvisOrchestrator:
    """Mirrors the exact field-walk sequence that used to reproduce the bug
    (investigation §Evidence):

    1. Bind motor + propeller with NO battery bound yet (voltage_v=None at
       that moment) -> post-MOP-1, resolve_operating_point HONESTLY falls
       back (10.042 N, no OP-electrical fields) instead of locking in an
       unvalidated exact match.
    2. THEN bind a real 6S/22.2V battery via catalog -> MOP-2's conditional
       hook re-resolves (voltage_validated was False), confirming honestly
       against the real 22.2V pack (still fallback -- no curated row is
       anywhere near 22.2V for this motor+propeller).

    Live state after this setup is voltage-coherent throughout: no stale
    432W lock-in, motor_op_power_w correctly absent.
    """
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "dse motor op dual truth repro",
            "payload_kg": 1.0, "restrictions": "autonomia minima 15 min",
            "detail_level": "conceptual", "motors": 4,
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    prop_spec = bind_propeller_from_catalog(_PROP_SKU)
    ps = set_propeller_component(ps, prop_spec)

    m = default_library.get_motor(_MOTOR_SKU)
    motor_spec = bind_motor_from_catalog({
        "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
        "kv_rating": m.kv_rating, "weight_g": m.weight_g,
    })
    ps = set_motor_component(ps, motor_spec, m.max_watts)  # voltage_v=None -> honest fallback (MOP-1)

    battery_spec = bind_battery_from_catalog(_BATTERY_SKU)
    ps = set_battery_component(ps, battery_spec, battery_spec.properties["battery_capacity_wh"].value)
    # MOP-2: battery bind re-validates the never-voltage-validated resolution
    # above against the real 22.2V pack -- still honestly fallback.

    orch.workspace_manager.save_state(ps)
    return orch


def test_motor_bound_before_battery_resolves_honestly_not_stale_exact(tmp_path: Path):
    """Sanity precondition: the fixture that used to produce a stale,
    voltage-incoherent exact_operating_point (pre-fix) now produces a
    voltage-COHERENT fallback resolution throughout -- no lock-in ever
    happens, so there is nothing left to revalidate away."""
    import json

    orch = _project_with_motor_bound_before_battery(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    resolution = json.loads(ps.current_parameters["propulsion_resolution"])
    assert resolution["resolution_type"] == "fallback_operating_point"
    assert resolution["voltage_validated"] is True  # MOP-2 revalidated on battery bind
    assert resolution["resolved_at_voltage_v"] == pytest.approx(22.2)
    assert "motor_op_power_w" not in ps.current_parameters
    assert ps.current_parameters["battery_cell_count"] == 6  # 22.2V nominal


def test_case_a_explore_baseline_agrees_with_live_calc(tmp_path: Path):
    """CASE A (contract §3, now flipped to PASS): exploration.baseline_
    simulation.autonomy_min (explore's live-params baseline, MOP-3) must
    equal the live calc's autonomy_min for the same project state -- both
    read the same voltage-coherent motor OP now."""
    orch = _project_with_motor_bound_before_battery(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    live_calc = CalculationEngine().build(dict(ps.current_parameters))
    exploration = orch.design_explorer.explore(ps, "mejorar_autonomia")

    assert exploration.baseline_simulation.autonomy_min == pytest.approx(live_calc.autonomy_min), (
        f"explore baseline autonomy={exploration.baseline_simulation.autonomy_min} "
        f"!= live calc autonomy={live_calc.autonomy_min}"
    )


def test_case_b_apply_delivers_explore_promise(tmp_path: Path):
    """CASE B (contract §3, now flipped to PASS): applying explore's own
    top-scored candidate for mejorar_autonomia must produce exactly the
    autonomy explore's message promised for it."""
    orch = _project_with_motor_bound_before_battery(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    exploration = orch.design_explorer.explore(ps, "mejorar_autonomia")
    assert exploration.viable, "precondition: need at least one viable candidate"
    promised_autonomy = exploration.viable[0].simulation.autonomy_min
    assert promised_autonomy is not None, "precondition: candidate must have a real autonomy prediction"

    session = orch.state_manager.get_runtime_session()
    orch.state_manager.set_runtime_session(
        session.model_copy(update={"last_exploration_result": exploration})
    )
    llm = _RefuseLLM()
    result = orch.handle_user_text("aplica la mejor", llm)
    assert result["status"] == "ok"

    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    actual_autonomy = saved.latest_results["calculations"]["autonomy_min"]

    assert actual_autonomy == pytest.approx(promised_autonomy), (
        f"explore promised autonomy={promised_autonomy} for the applied candidate, "
        f"but post-apply calc shows autonomy={actual_autonomy}"
    )


# ── ★4 siblings — conditional revalidation gate itself (MOP-2) ─────────────


def test_motor_op_revalidated_on_battery_bind_when_voltage_was_unknown(tmp_path: Path):
    """★4 sibling: motor+propeller bound with NO voltage known at all ->
    binding a real (incompatible) battery afterward MUST revalidate the
    resolution against the real voltage, not leave it stamped
    voltage_validated=False forever."""
    import json

    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "star4 sibling revalidate",
            "payload_kg": 1.0, "restrictions": "no", "detail_level": "conceptual",
            "motors": 4, "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    prop_spec = bind_propeller_from_catalog(_PROP_SKU)
    ps = set_propeller_component(ps, prop_spec)
    m = default_library.get_motor(_MOTOR_SKU)
    motor_spec = bind_motor_from_catalog({
        "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
        "kv_rating": m.kv_rating, "weight_g": m.weight_g,
    })
    ps = set_motor_component(ps, motor_spec, m.max_watts)

    before = json.loads(ps.current_parameters["propulsion_resolution"])
    assert before["voltage_validated"] is False
    assert before["resolved_at_voltage_v"] is None

    battery_spec = bind_battery_from_catalog(_BATTERY_SKU)  # 6S / 22.2V
    ps = set_battery_component(ps, battery_spec, battery_spec.properties["battery_capacity_wh"].value)

    after = json.loads(ps.current_parameters["propulsion_resolution"])
    assert after["voltage_validated"] is True
    assert after["resolved_at_voltage_v"] == pytest.approx(22.2)
    assert "motor_op_power_w" not in ps.current_parameters  # honest: no exact row near 22.2V


def test_motor_op_unchanged_on_compatible_battery_bind_when_voltage_validated(tmp_path: Path):
    """★4 sibling / P2-2 lock preserved: once a resolution IS voltage-
    validated and the new battery bind's voltage is still compatible, the
    motor writer must NOT be re-triggered -- propulsion_resolution stays
    byte-identical. Uses a real ★6 exact row (sunnysky_r2205_2500 +
    gf_5045x3 @ 14.8V, OP-3) and two real 4S catalog SKUs (14.8V both) so
    the voltage genuinely matches within epsilon, not by synthetic tuning."""
    import json

    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "star4 sibling no-op",
            "payload_kg": 1.0, "restrictions": "no", "detail_level": "conceptual",
            "motors": 4, "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    prop_spec = bind_propeller_from_catalog("gf_5045x3")
    ps = set_propeller_component(ps, prop_spec)

    b1 = bind_battery_from_catalog("lipo_4s_10000mah")
    ps = set_battery_component(ps, b1, b1.properties["battery_capacity_wh"].value)

    m = default_library.get_motor("sunnysky_r2205_2500")
    motor_spec = bind_motor_from_catalog({
        "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
        "kv_rating": m.kv_rating, "weight_g": m.weight_g,
    })
    ps = set_motor_component(ps, motor_spec, m.max_watts)

    before = json.loads(ps.current_parameters["propulsion_resolution"])
    assert before["resolution_type"] == "exact_operating_point"
    assert before["voltage_validated"] is True
    assert before["resolved_at_voltage_v"] == pytest.approx(14.8)

    b2 = bind_battery_from_catalog("lipo_4s_5000mah")  # different SKU, same 4S/14.8V
    ps2 = set_battery_component(ps, b2, b2.properties["battery_capacity_wh"].value)

    after = json.loads(ps2.current_parameters["propulsion_resolution"])
    assert after == before, "compatible battery bind must not re-trigger motor OP revalidation"
    assert ps2.current_parameters["motor_op_power_w"] == pytest.approx(592.0)
    assert ps2.current_parameters["per_motor_max_thrust_n"] == pytest.approx(12.5525)
