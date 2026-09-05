"""Tests for Project Continuity (A') — Situation / Evidence / one next step."""
from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path

from jarvis.adapters.cli.main import render_startup_context
from jarvis.core.intent_resolver import IntentResolver
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.project_continuity import build_project_continuity


def _state(**kwargs):
    defaults = dict(
        latest_results={
            "simulation": {
                "status": "pass",
                "quality": "good",
                "safety_margin_ratio": 2.0,
                "can_fly": True,
                "warnings": [],
            },
            "calculations": {},
        },
        current_parameters={"motor_count": 4},
        design_properties=SimpleNamespace(components={}),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_situation_thrust_feasibility_only_when_autonomy_unmet():
    """CLI feasibility vs readiness semantics IC (§2.1): closed BOM + sim
    PASS + an autonomy constraint the calc could not evaluate must say
    "Comprobación de empuje... Candidato inicial", never "Diseño validado"
    — thrust feasibility PASS is not the same claim as the autonomy
    objective being demonstrated."""
    state = _state(
        latest_results={
            "simulation": {
                "status": "pass",
                "quality": "acceptable",
                "safety_margin_ratio": 1.28,
                "can_fly": True,
                "warnings": [],
                "energy_status": "missing_energy_parameters",
            },
            "calculations": {},
        },
    )
    cont = build_project_continuity(
        project_state=state,
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress="4/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={"autonomy_target_min": 5.0},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=None,
        motor_catalog_matches=[],
    )
    assert "PASS" in cont["situation"]
    assert "Comprobación de empuje" in cont["situation"]
    assert "Candidato inicial" in cont["situation"]
    assert "Diseño validado" not in cont["situation"]
    # §2.2: evidence line for the target must not go silent either.
    assert any("no calculada" in e.lower() for e in cont["evidence"])


def test_situation_still_diseno_validado_when_no_autonomy_constraint():
    """Same PASS + closed BOM shape, but no autonomy constraint at all ->
    the original "Diseño validado" wording is unchanged (§2.1's guard is
    scoped to the autonomy-constraint case only)."""
    cont = build_project_continuity(
        project_state=_state(),
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress="4/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=None,
        motor_catalog_matches=[],
    )
    assert "Diseño validado en simulación (PASS)" in cont["situation"]


def test_situation_thrust_feasibility_when_autonomy_calculated_below_target():
    """Feasibility delta 2026-09-02: closed BOM + sim PASS + autonomy
    calculated *below* the target (15 vs 5.0) must not say "Diseño validado".
    Same locked situation string as the uncalculated parent IC. Next step
    must not keep the architecture-complete / iterate CTA."""
    state = _state(
        latest_results={
            "simulation": {
                "status": "pass",
                "quality": "good",
                "safety_margin_ratio": 1.75,
                "can_fly": True,
                "warnings": ["autonomy_below_restriction"],
            },
            "calculations": {"autonomy_min": 5.0},
        },
    )
    cont = build_project_continuity(
        project_state=state,
        status_type="warning",
        status_reason="autonomy_below_restriction",
        phase="complete",
        architecture_progress="4/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question="Arquitectura completa (4/4) — puedes optimizar o simular.",
        suggested_action={"label": "Optimiza o itera el diseño.", "reason": "margen"},
        physical_requirements={
            "autonomy_target_min": 15.0,
            "current_autonomy_min": 5.0,
            "thrust_per_motor_needed_n": 4.30,
        },
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=None,
        motor_catalog_matches=[],
    )
    assert "Comprobación de empuje" in cont["situation"]
    assert "Candidato inicial" in cont["situation"]
    assert "Diseño validado" not in cont["situation"]
    assert "Revisa energía" in cont["next_useful_step"]
    assert "empuje ya es PASS" in cont["next_useful_step"]
    assert "Arquitectura completa" not in cont["next_useful_step"]
    assert "optimizar" not in cont["next_useful_step"]
    assert "puedes iterar" not in cont["next_useful_step"]
    assert "ayúdame a elegir" not in cont["next_useful_step"]
    assert cont["next_useful_why"] == "autonomy_below_restriction"
    assert any("15" in e and "5.0" in e for e in cont["evidence"])


def test_situation_still_diseno_validado_when_autonomy_meets_target():
    """Same PASS + closed BOM + autonomy constraint, but current meets the
    target → original "Diseño validado" wording (delta is below-target only)."""
    cont = build_project_continuity(
        project_state=_state(
            latest_results={
                "simulation": {
                    "status": "pass",
                    "quality": "good",
                    "safety_margin_ratio": 1.75,
                    "can_fly": True,
                    "warnings": [],
                },
                "calculations": {"autonomy_min": 16.0},
            },
        ),
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress="4/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={
            "autonomy_target_min": 15.0,
            "current_autonomy_min": 16.0,
        },
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=None,
        motor_catalog_matches=[],
    )
    assert "Diseño validado en simulación (PASS)" in cont["situation"]
    assert "Comprobación de empuje" not in cont["situation"]


def test_situation_margin_weak_never_says_diseno_validado():
    """Claim hygiene under ASSEMBLY READY IC §2.1: PASS + quality=risky +
    an active low_margin warning must not say "Diseño validado" — it must
    use the locked margin-weak sentence instead. Evidence keeps naming
    quality/margin (unchanged); next step stays the warning-branch
    correction (status_type="warning", as orchestrator actually derives it
    for a non-empty warnings list)."""
    cont = build_project_continuity(
        project_state=_state(
            latest_results={
                "simulation": {
                    "status": "pass",
                    "quality": "risky",
                    "safety_margin_ratio": 1.05,
                    "can_fly": True,
                    "warnings": ["low_margin"],
                },
                "calculations": {},
            },
        ),
        status_type="warning",
        status_reason="low_margin",
        phase="complete",
        architecture_progress="4/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=None,
        motor_catalog_matches=[],
    )
    assert "Diseño validado" not in cont["situation"]
    assert "Margen ajustado" in cont["situation"]
    assert "PASS" in cont["situation"]
    assert any("risky" in e.lower() and "1.05" in e for e in cont["evidence"])
    assert "Corrige la causa del warning" in cont["next_useful_step"]
    assert cont["next_useful_why"] == "low_margin"


def test_situation_high_actuator_load_never_says_diseno_validado():
    """Same guard, different margin/load warning code (high_actuator_load) —
    quality can still be "acceptable"; the warning alone is enough."""
    cont = build_project_continuity(
        project_state=_state(
            latest_results={
                "simulation": {
                    "status": "pass",
                    "quality": "acceptable",
                    "safety_margin_ratio": 1.2,
                    "can_fly": True,
                    "warnings": ["high_actuator_load"],
                },
                "calculations": {},
            },
        ),
        status_type="warning",
        status_reason="high_actuator_load",
        phase="complete",
        architecture_progress="4/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=None,
        motor_catalog_matches=[],
    )
    assert "Diseño validado" not in cont["situation"]
    assert "Margen ajustado" in cont["situation"]


def test_situation_diseno_validado_unchanged_for_pass_good_no_warnings():
    """Regression guard: PASS + quality=good + no warnings keeps the
    original "Diseño validado" sentence — the §2.1 gate must not fire on
    the honest case."""
    cont = build_project_continuity(
        project_state=_state(),
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress="4/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=None,
        motor_catalog_matches=[],
    )
    assert "Diseño validado en simulación (PASS)" in cont["situation"]
    assert "Margen ajustado" not in cont["situation"]


def test_situation_frame_class_gap_never_says_diseno_validado():
    """Structure Foundations IC §2.2: PASS + a live GAP-FRAME-SIZE-MISSING
    on ``readiness`` must not say "Diseño validado" — even when
    ``architecture_progress`` is omitted (the gate reads the Gap Registry
    directly, not the architecture-progress string)."""
    readiness = SimpleNamespace(
        gaps=[SimpleNamespace(gap_type="GAP-FRAME-SIZE-MISSING")],
        top_gap=None,
        subsystems={},
        motor_catalog_gap_fact=None,
    )
    state = _state(
        current_parameters={"motor_count": 4, "propeller_diameter_in": 10.0},
    )
    cont = build_project_continuity(
        project_state=state,
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress=None,
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=None,
        motor_catalog_matches=[],
        readiness=readiness,
    )
    assert "Diseño validado" not in cont["situation"]
    assert cont["situation"] == (
        "Comprobación de empuje: PASS. Compatibilidad de clase (nivel A) pendiente."
    )


def test_situation_frame_prop_size_gap_uses_same_locked_sentence():
    readiness = SimpleNamespace(
        gaps=[SimpleNamespace(gap_type="GAP-FRAME-PROP-SIZE")],
        top_gap=None,
        subsystems={},
        motor_catalog_gap_fact=None,
    )
    frame = SimpleNamespace(properties={"size_class_inch": SimpleNamespace(value=5.0)})
    state = _state(
        current_parameters={"motor_count": 4, "propeller_diameter_in": 10.0},
        design_properties=SimpleNamespace(components={"frame": frame}),
    )
    cont = build_project_continuity(
        project_state=state,
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress=None,
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=None,
        motor_catalog_matches=[],
        readiness=readiness,
    )
    assert cont["situation"] == (
        "Comprobación de empuje: PASS. Compatibilidad de clase (nivel A) pendiente."
    )


def test_situation_diseno_validado_unchanged_when_readiness_has_no_frame_gap():
    """Regression guard: a readiness object with unrelated gaps (or none)
    must not trip the new gate."""
    readiness = SimpleNamespace(gaps=[], top_gap=None, subsystems={}, motor_catalog_gap_fact=None)
    cont = build_project_continuity(
        project_state=_state(),
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress="4/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=None,
        motor_catalog_matches=[],
        readiness=readiness,
    )
    assert "Diseño validado en simulación (PASS)" in cont["situation"]


def test_continuity_catalog_gap_beats_optimization_suggestion():
    cont = build_project_continuity(
        project_state=_state(),
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress="3/4",
        next_architecture_label="Propulsión",
        next_block_status="in_progress",
        proactive_question="Propulsión en progreso",
        suggested_action={
            "label": "Aumentar carga útil",
            "reason": "Hay margen de empuje",
        },
        physical_requirements={"thrust_per_motor_needed_n": 4.76},
        component_bom={
            "defined": [],
            "incomplete": [{"key": "propellers", "missing_fields": []}],
            "missing": [],
            "declarative": [],
        },
        energy_model_note=None,
        motor_catalog_gap="Necesitas empuje ≥ 4.8 N/motor; no tengo motor en catálogo.",
        motor_catalog_matches=[],
    )
    assert "PASS" in cont["situation"] or "gaps" in cont["situation"].lower() or "PASS" in cont["situation"]
    assert cont["next_useful_step"]
    assert "Aumentar carga útil" not in cont["next_useful_step"]
    assert "empuje" in cont["next_useful_step"].lower() or "catálogo" in cont["next_useful_why"].lower()


def test_continuity_incomplete_bom_without_catalog_gap():
    cont = build_project_continuity(
        project_state=_state(),
        status_type="nominal",
        status_reason=None,
        phase="definition",
        architecture_progress="2/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action={"label": "Aumentar carga útil", "reason": "margen"},
        physical_requirements={},
        component_bom={
            "defined": [],
            "incomplete": [{"key": "battery", "missing_fields": ["Wh"]}],
            "missing": [],
            "declarative": [],
        },
        energy_model_note=None,
        motor_catalog_gap=None,
    )
    assert "battery" in cont["next_useful_step"].lower()
    assert "Aumentar carga útil" not in cont["next_useful_step"]


def test_continuity_sim_fail_underspec_names_candidates():
    """T1 (implementation_contract_cli_catalog_assist_t1.md §2.4/§3): rank 2
    (sim warning/fail) stays first, but when the bound motor SKU is
    underspec its copy names the G22 candidates instead of only the
    generic "no es PASS" — and never claims sim PASS or bloque CERRADO."""
    cont = build_project_continuity(
        project_state=_state(
            latest_results={
                "simulation": {"status": "fail", "quality": "fail", "warnings": []},
                "calculations": {},
            }
        ),
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress="4/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={"thrust_per_motor_needed_n": 15.04},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=(
            "El motor vinculado (sunnysky_r2305_2500) ya no cubre el hueco de diseño "
            "(empuje ≥ 15.0 N/motor, ~2500KV, hélice ~5\")."
        ),
        motor_catalog_matches=[{"name": "sunnysky_r2205_2500", "thrust_n": 12.5525}],
    )
    assert "ayúdame a elegir" in cont["next_useful_step"]
    assert "sunnysky_r2205_2500" in cont["next_useful_step"]
    # Locked disclaimer, not a claim of achieved PASS/CERRADO.
    assert "no garantiza sim PASS" in cont["next_useful_step"]
    assert "CERRADO" not in cont["next_useful_step"]
    assert "sunnysky_r2305_2500" in cont["next_useful_why"]


def test_continuity_sim_fail_without_underspec_unchanged():
    """Sim fail with no underspec evidence, thrust itself genuinely fine
    (can_fly=True — every real simulation result sets this; explicit here
    per implementation_contract_cli_fail_routing_coherence.md §2.4, which
    only replaces this generic fallback when can_fly is NOT True) keeps
    today's generic copy — T1 only specializes the underspec case, nothing
    else in rank 2 for this shape."""
    cont = build_project_continuity(
        project_state=_state(
            latest_results={
                "simulation": {
                    "status": "fail", "quality": "fail", "can_fly": True,
                    "warnings": ["margen bajo"],
                },
                "calculations": {},
            }
        ),
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress="4/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=None,
    )
    assert "Corrige la causa" in cont["next_useful_step"]
    assert "ayúdame a elegir" not in cont["next_useful_step"]


def test_render_leads_with_continuity_block():
    text = render_startup_context({
        "has_project": True,
        "project_slug": "demo",
        "objective": "inspección",
        "phase": "complete",
        "status_type": "nominal",
        "continuity": {
            "situation": "Diseño validado en simulación (PASS).",
            "evidence": ["Simulación: pass — calidad good"],
            "next_useful_step": "Declara empuje real por motor.",
            "next_useful_why": "Hueco de catálogo",
        },
        "suggested_action": {"label": "Aumentar carga útil", "reason": "margen"},
        "component_bom_lines": ["… propellers: incompleto"],
    })
    assert "Situación:" in text
    assert "Evidencia:" in text
    assert "Siguiente paso:" in text
    assert "Declara empuje" in text
    # Competing optimization hint must not appear when continuity chose another next
    assert "Aumentar carga útil" not in text


def test_continuity_phrases_resolve_to_project_status():
    r = IntentResolver()
    for phrase in ("dónde estoy", "y ahora", "qué sigue", "por qué no puedo comprar aún"):
        assert r.resolve_intent(phrase) == "project_status", phrase


def test_build_startup_context_includes_continuity(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    # Minimal create via handle create path is heavy; use existing workspace if present
    ws = Path(
        "workspace/inspección-de-puentes-con-cámara-de-0-5kg-autonomía-mínima-20-minutos-9656971237a1"
    )
    if not ws.exists():
        return
    ctx = orch.build_startup_context(workspace_path=str(ws))
    assert ctx.get("has_project")
    cont = ctx.get("continuity") or {}
    assert cont.get("situation")
    assert cont.get("evidence")
    assert cont.get("next_useful_step")
    # Catalog gap on this project should win over payload optimization
    assert "Aumentar carga útil" not in cont["next_useful_step"]
