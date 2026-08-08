"""U5 — Validación de restricciones incremental.

Tests:
  - _parse_constraints extrae max_weight_kg de texto libre
  - _parse_constraints extrae autonomy_min + max_weight_kg simultáneamente
  - _parse_constraints compatible con proyectos sin restricción de peso (no rompe nada)
  - _check_constraint_violations vacío si no hay violación
  - _check_constraint_violations emite warning si peso supera máximo
  - _check_constraint_violations es no-op sin cálculo previo
  - warning se añade al mensaje del componente y status sigue siendo "ok" (no bloquea)
"""
from __future__ import annotations

import pytest

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.state_manager import OrchestratorMode
from jarvis.core.parameter_requirements import MISSING_COMPONENT_DEFINITION
from jarvis.schemas.state_schema import ProjectState, _parse_constraints


# ── _parse_constraints ─────────────────────────────────────────────────────────

def test_parse_constraints_extracts_max_weight() -> None:
    """'peso máximo 5kg' → max_weight_kg: 5.0"""
    result = _parse_constraints({"restrictions": "peso máximo 5kg"})
    assert result == {"max_weight_kg": 5.0}


def test_parse_constraints_max_weight_variants() -> None:
    """Variantes de escritura reconocidas (español / mixto)."""
    assert _parse_constraints({"restrictions": "masa máx: 3kg"})["max_weight_kg"] == 3.0
    assert _parse_constraints({"restrictions": "peso max 2.5kg"})["max_weight_kg"] == 2.5
    assert _parse_constraints({"restrictions": "peso máximo 10kg"})["max_weight_kg"] == 10.0


def test_parse_constraints_both_autonomy_and_weight() -> None:
    """Restricción mixta: autonomía + peso en el mismo string."""
    result = _parse_constraints({"restrictions": "vuelo mínimo 20 min, peso máximo 5kg"})
    assert result.get("autonomy_min") == 20.0
    assert result.get("max_weight_kg") == 5.0


def test_parse_constraints_autonomy_only_unchanged() -> None:
    """Proyectos sin restricción de peso no se ven afectados."""
    result = _parse_constraints({"restrictions": "vuelo mínimo 30 min"})
    assert result == {"autonomy_min": 30.0}
    assert "max_weight_kg" not in result


def test_parse_constraints_empty_restrictions() -> None:
    """Sin restrictions → dict vacío."""
    assert _parse_constraints({}) == {}
    assert _parse_constraints({"restrictions": None}) == {}


# ── FN-010: fallback determinista objective → parsed_constraints ──────────────

def test_parse_constraints_falls_back_to_objective_when_restrictions_absent() -> None:
    """Objetivo 'levantar 3,5kg con autonomía de 40min' + restrictions 'ninguno'
    → autonomy_min se deriva del objetivo (fallback per-key)."""
    result = _parse_constraints(
        {"restrictions": "ninguno"},
        objective="levantar 3,5kg con autonomía de 40min",
    )
    assert result.get("autonomy_min") == 40.0


def test_parse_constraints_restrictions_autonomy_wins_over_objective() -> None:
    """Una autonomía explícita en restrictions prevalece sobre la del objetivo."""
    result = _parse_constraints(
        {"restrictions": "vuelo mínimo 20 min"},
        objective="dron con autonomía de 40min",
    )
    assert result.get("autonomy_min") == 20.0


def test_parse_constraints_max_weight_falls_back_to_objective_independently() -> None:
    """El fallback es por clave: restrictions declara autonomía, max_weight_kg
    (ausente en restrictions) cae al objetivo sin pisar la autonomía explícita."""
    result = _parse_constraints(
        {"restrictions": "vuelo mínimo 20 min"},
        objective="dron con peso máximo 5kg",
    )
    assert result.get("autonomy_min") == 20.0
    assert result.get("max_weight_kg") == 5.0


def test_parse_constraints_no_constraints_anywhere_still_empty() -> None:
    """Sin patrones reconocibles en restrictions ni en objective → {} (sin falsos positivos)."""
    result = _parse_constraints(
        {"restrictions": "ninguna"},
        objective="dron de fotografía aérea urbana",
    )
    assert result == {}


def test_parse_constraints_none_objective_behaves_like_before() -> None:
    """objective=None (valor por defecto) no rompe el comportamiento previo."""
    assert _parse_constraints({"restrictions": "vuelo mínimo 30 min"}) == {"autonomy_min": 30.0}


def test_project_creation_derives_autonomy_from_objective_fallback(tmp_path) -> None:
    """FN-010 criterio de aceptación: create_project con restrictions='ninguno' y un
    objetivo que menciona autonomía guarda parsed_constraints.autonomy_min == 40.0,
    y el valor sobrevive un save/reload de state.json."""
    orc = JarvisOrchestrator(workspace_root=tmp_path)
    orc.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "levantar 3,5kg con autonomía de 40min",
            "payload_kg": 3.5,
            "restrictions": "ninguno",
            "detail_level": "conceptual",
            "motors": 4,
            "per_motor_max_thrust_n": 15.0,
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })
    state = orc.state_manager.load_active_project(orc.workspace_manager)
    assert state.parsed_constraints.get("autonomy_min") == 40.0

    # Reload from disk (fresh StateManager) — the value must not depend on
    # in-memory state surviving the process.
    from pathlib import Path

    from jarvis.core.state_manager import StateManager
    reloaded = StateManager().load(Path(state.workspace_path) / "state.json")
    assert reloaded.parsed_constraints.get("autonomy_min") == 40.0

    # Existing consumers (simulator threshold) receive the value unchanged.
    assert state.parsed_constraints.get("autonomy_min") == reloaded.parsed_constraints.get("autonomy_min")


# ── _check_constraint_violations ──────────────────────────────────────────────

def _make_state_with_calc(*, max_weight_kg: float | None, total_mass_kg: float) -> ProjectState:
    """Construye un ProjectState mínimo con un cálculo registrado."""
    restrictions = f"peso máximo {max_weight_kg}kg" if max_weight_kg is not None else "ninguna"
    state = ProjectState(
        project_id="test",
        project_slug="test",
        objective="test",
        workspace_path="/tmp/test",
        current_parameters={"restrictions": restrictions},
        latest_results={"calculations": {"total_mass_kg": total_mass_kg}},
    )
    return state


def test_no_violation_when_within_limit() -> None:
    """Masa 1.5kg con límite 5kg → no hay violaciones."""
    from jarvis.core.orchestrator import JarvisOrchestrator
    orc = JarvisOrchestrator.__new__(JarvisOrchestrator)
    state = _make_state_with_calc(max_weight_kg=5.0, total_mass_kg=1.5)
    assert orc._check_constraint_violations(state) == []


def test_violation_when_mass_exceeds_max_weight() -> None:
    """Masa 6.2kg con límite 5kg → warning con valores concretos."""
    from jarvis.core.orchestrator import JarvisOrchestrator
    orc = JarvisOrchestrator.__new__(JarvisOrchestrator)
    state = _make_state_with_calc(max_weight_kg=5.0, total_mass_kg=6.2)
    violations = orc._check_constraint_violations(state)
    assert len(violations) == 1
    assert "6.20" in violations[0]
    assert "5.0" in violations[0]


def test_violation_skipped_without_calculation() -> None:
    """Sin latest_results no hay crash ni violaciones falsas."""
    from jarvis.core.orchestrator import JarvisOrchestrator
    orc = JarvisOrchestrator.__new__(JarvisOrchestrator)
    state = ProjectState(
        project_id="t", project_slug="t", objective="t", workspace_path="/tmp/t",
        current_parameters={"restrictions": "peso máximo 2kg"},
        latest_results={},
    )
    assert orc._check_constraint_violations(state) == []


def test_violation_skipped_when_no_constraints() -> None:
    """Sin parsed_constraints → no hay violaciones (no-op total)."""
    from jarvis.core.orchestrator import JarvisOrchestrator
    orc = JarvisOrchestrator.__new__(JarvisOrchestrator)
    state = _make_state_with_calc(max_weight_kg=None, total_mass_kg=99.0)
    assert orc._check_constraint_violations(state) == []


# ── Integración: warning inline en handle_user_text ───────────────────────────

class _NoLLM:
    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _setup_project_with_weight_constraint(tmp_path, max_weight_kg: float):
    """Crea un proyecto con restricción de peso y lo deja listo para definir frame."""
    orc = JarvisOrchestrator(workspace_root=tmp_path)
    orc.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "dron de prueba U5",
            "payload_kg": 1.0,
            "restrictions": f"peso máximo {max_weight_kg}kg",
            "detail_level": "conceptual",
            "motors": 4,
            "per_motor_max_thrust_n": 15.0,
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })
    # Forzar sesión en DEFINE_MISSING_PARAMETERS con bloque frame activo
    session = orc.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "pending_missing_params": ["frame"],
        "pending_define_missing": False,
    })
    orc.state_manager.set_runtime_session(updated)
    return orc


def test_no_warning_when_frame_within_constraint(tmp_path) -> None:
    """Frame de 0.3kg con límite 10kg → mensaje sin ⚠, status ok."""
    orc = _setup_project_with_weight_constraint(tmp_path, max_weight_kg=10.0)
    result = orc.handle_user_text("fibra de carbono 300g", _NoLLM())
    assert result["status"] == "ok"
    assert "⚠" not in (result.get("message") or "")


def test_warning_appended_when_frame_exceeds_max_weight(tmp_path) -> None:
    """Frame pesado (6kg) con límite 2kg → ⚠ aparece en message, status sigue 'ok'."""
    orc = _setup_project_with_weight_constraint(tmp_path, max_weight_kg=2.0)
    result = orc.handle_user_text("aluminio 6000g", _NoLLM())
    # El status nunca debe ser "error" por una violación de restricción — solo informativo
    assert result["status"] == "ok"
    assert "⚠" in (result.get("message") or ""), (
        f"Se esperaba ⚠ en el mensaje, pero fue: {result.get('message')!r}"
    )
