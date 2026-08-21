"""Propeller Catalog Bind UX — Prop-1..Prop-7.

Live propeller catalog pick + bind (G21-class UX for propellers), so
Phase 2 P2-1 can reach exact_operating_point from real CLI turns without
test-only bind_propeller_from_catalog state patches.

★1: suggestion authority = match_motor_propeller filter, no SKU hardcode.
★4: motors/propellers help-choose gated on _wants_catalog_help (live
    incompleteness), not bare expected_keys membership — the starvation fix.
★5: propeller pick re-calls set_motor_component so resolve_operating_point
    re-runs with the now-bound propeller catalog_ref.
★6: scope A+B — component wizard + IDLE re-bind for freeform/unbound.
★7: no battery step needed to reach exact_operating_point for this dataset.
"""
from __future__ import annotations

import json
from pathlib import Path

from jarvis.core.catalog_bind import bind_motor_from_catalog
from jarvis.core.component_writers import set_motor_component
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import MISSING_COMPONENT_DEFINITION
from jarvis.core.propeller_catalog_assist import build_propeller_catalog_suggestions
from jarvis.core.state_manager import OrchestratorMode
from jarvis.knowledge.library import default_library


class _FakeLLM:
    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called for this path")

    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called for this path")


_CREATE_PARAMS = {
    "vehicle_type": "dron",
    "objective": "dron de prueba propeller catalog bind",
    "payload_kg": 1.0,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "structure_mass_factor": 0.5,
    "safety_factor": 1.2,
}

_OP_MOTOR_SKU = "emax_rs2205s_2300"  # P2-1 seed: OP-0/OP-1/OP-2
_OP_PROP_SKU = "hq_5045_bn"          # OP-1/OP-2 exact match


def _fresh(tmp_path) -> JarvisOrchestrator:
    o = JarvisOrchestrator(workspace_root=tmp_path)
    o.handle({"action": "create_project", "parameters": dict(_CREATE_PARAMS)})
    return o


def _open_component_wizard(o, pending_keys):
    session = o.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "pending_missing_params": pending_keys,
        "pending_define_missing": False,
    })
    o.state_manager.set_runtime_session(updated)


def _suggestion_for(sku: str):
    m = default_library.get_motor(sku)
    return {
        "idx": 1, "name": sku, "thrust_n": m.thrust_n, "kv_rating": m.kv_rating,
        "weight_g": m.weight_g, "max_watts": m.max_watts, "is_generic": m.is_generic,
    }


def _bind_op_motor(o: JarvisOrchestrator) -> None:
    ps = o.state_manager.load_active_project(o.workspace_manager)
    spec = bind_motor_from_catalog(_suggestion_for(_OP_MOTOR_SKU))
    ps = set_motor_component(ps, spec, default_library.get_motor(_OP_MOTOR_SKU).max_watts)
    o.workspace_manager.save_state(ps)


# ── 1. Component wizard help-choose after motors bound → propeller list ────


def test_propeller_component_wizard_help_choose_after_motors_bound(tmp_path: Path):
    o = _fresh(tmp_path)
    _bind_op_motor(o)
    _open_component_wizard(o, ["motors", "propellers"])

    result = o.handle_user_text("ayúdame a elegir", _FakeLLM())

    assert result.get("status") == "interactive"
    assert "Hélices del catálogo" in result.get("message", "")
    suggestions = result.get("propeller_suggestions") or []
    names = {s["name"] for s in suggestions}
    assert "hq_5045_bn" in names
    assert "gf_5045x3" in names
    session = o.state_manager.runtime_state.session
    assert session.propeller_suggestions == suggestions
    assert session.motor_suggestions == []  # cleared per §2/★4


# ── 2. Pick → catalog_ref + exact OP re-resolve ─────────────────────────────


def test_propeller_pick_sets_catalog_ref_and_reresolves_exact_op(tmp_path: Path):
    o = _fresh(tmp_path)
    _bind_op_motor(o)
    _open_component_wizard(o, ["motors", "propellers"])
    listed = o.handle_user_text("ayúdame a elegir", _FakeLLM())
    suggestions = listed["propeller_suggestions"]
    idx = next(s["idx"] for s in suggestions if s["name"] == _OP_PROP_SKU)

    result = o.handle_user_text(str(idx), _FakeLLM())

    assert result.get("status") == "ok"
    assert result.get("action") == "component_description_saved"
    project = o.state_manager.load_active_project(o.workspace_manager)
    propellers = project.design_properties.components["propellers"]
    assert propellers.catalog_ref is not None
    assert propellers.catalog_ref.family == "propeller"
    assert propellers.catalog_ref.sku == _OP_PROP_SKU

    # ★5/★7: no battery step — propeller bind alone re-resolves exact OP.
    raw = project.current_parameters.get("propulsion_resolution")
    assert raw is not None
    resolution = json.loads(raw)
    assert resolution["resolution_type"] == "exact_operating_point"
    assert resolution["selection_reason"] == "v1_max_thrust"
    assert project.current_parameters["per_motor_max_thrust_n"] == 9.7086

    session = o.state_manager.runtime_state.session
    assert session.propeller_suggestions == []


# ── 3. IDLE freeform unbound propeller → picker ─────────────────────────────


def test_propeller_idle_help_choose_when_freeform_unbound(tmp_path: Path):
    o = _fresh(tmp_path)
    _bind_op_motor(o)
    # Freeform propeller declare — no catalog_ref.
    o.handle_user_text("hélices 5x4.5", _FakeLLM())
    project = o.state_manager.load_active_project(o.workspace_manager)
    propellers = project.design_properties.components.get("propellers")
    assert propellers is not None and propellers.catalog_ref is None

    result = o.handle_user_text("ayúdame a elegir", _FakeLLM())

    assert result.get("status") == "interactive"
    assert "Hélices del catálogo" in result.get("message", "")
    session = o.state_manager.runtime_state.session
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert session.pending_missing_params == ["propellers"]


# ── 4. IDLE no-op when propeller catalog_ref already set ───────────────────


def test_propeller_idle_help_choose_noop_when_catalog_ref_set(tmp_path: Path):
    o = _fresh(tmp_path)
    _bind_op_motor(o)
    _open_component_wizard(o, ["motors", "propellers"])
    listed = o.handle_user_text("ayúdame a elegir", _FakeLLM())
    idx = next(s["idx"] for s in listed["propeller_suggestions"] if s["name"] == _OP_PROP_SKU)
    o.handle_user_text(str(idx), _FakeLLM())

    result = o.handle_user_text("ayúdame a elegir", _FakeLLM())

    session = o.state_manager.runtime_state.session
    assert not (
        session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
        and session.pending_missing_params == ["propellers"]
    )


# ── 5. Both incomplete → motors list wins (priority precedent unchanged) ───


def test_motors_help_choose_wins_when_both_incomplete(tmp_path: Path):
    o = _fresh(tmp_path)
    _open_component_wizard(o, ["motors", "propellers"])

    result = o.handle_user_text("ayúdame a elegir", _FakeLLM())

    assert "motor_suggestions" in result
    assert result.get("motor_suggestions")
    session = o.state_manager.runtime_state.session
    assert session.motor_suggestions
    assert session.propeller_suggestions == []


# ── 6. Freeform hélices never yields exact_operating_point ─────────────────


def test_freeform_propeller_never_produces_false_exact_op(tmp_path: Path):
    o = _fresh(tmp_path)
    _bind_op_motor(o)
    project = o.state_manager.load_active_project(o.workspace_manager)
    raw_before = project.current_parameters.get("propulsion_resolution")
    assert json.loads(raw_before)["resolution_type"] == "fallback_operating_point"

    o.handle_user_text("hélices 5x4.5", _FakeLLM())

    project2 = o.state_manager.load_active_project(o.workspace_manager)
    propellers = project2.design_properties.components.get("propellers")
    assert propellers.catalog_ref is None
    raw_after = project2.current_parameters.get("propulsion_resolution")
    # set_propeller_component does not call resolve_operating_point at all —
    # the prior motor-bind resolution is left exactly as it was.
    assert json.loads(raw_after)["resolution_type"] == "fallback_operating_point"


# ── 7. No motor bound → empty suggestions / honest message ─────────────────


def test_no_motor_bound_yields_empty_suggestions_not_full_dump():
    suggestions = build_propeller_catalog_suggestions(None)
    assert suggestions == []


def test_propeller_component_wizard_help_choose_before_motors_bound_is_honest(tmp_path: Path):
    o = _fresh(tmp_path)
    _open_component_wizard(o, ["propellers"])

    result = o.handle_user_text("ayúdame a elegir", _FakeLLM())

    assert result.get("status") == "interactive"
    assert "Primero elige un motor" in result.get("message", "")
    assert result.get("propeller_suggestions") == []
