import pytest

from jarvis.core.mutation_engine import MutationEngine, apply_mutation
from jarvis.schemas.action_schema import IterationDraft


def test_material_mutation_reduces_density_and_mass_deterministically():
    # aluminio (2700 kg/m³) → fibra de carbono (1600 kg/m³), structural_fraction=0.25
    # m_new = 3.2*0.75 + 3.2*0.25*(1600/2700) = 2.4 + 0.4741 = 2.8741
    state = {
        "masa_total": 3.2,
        "densidad": 2700.0,
        "material": "aluminio",
        "design_properties": {"structure": {"material": "aluminio", "structural_fraction": 0.25}},
    }
    draft = {
        "objective": "peso",
        "operation": "reducir",
        "strategy": "material",
        "value": "fibra de carbono",
    }

    new_state, impact = apply_mutation(state, draft)

    assert new_state["masa_total"] == 2.8741
    assert new_state["densidad"] == 1600.0
    assert new_state["material"] == "fibra de carbono"
    assert impact["masa_total"] == round((2.8741 - 3.2) / 3.2 * 100, 4)
    assert impact["densidad"] == round((1600 - 2700) / 2700 * 100, 4)


def test_volume_mutation_reduces_size_and_mass():
    engine = MutationEngine()
    state = {
        "masa_total": 5.0,
        "volumen": 10.0,
    }
    draft = {
        "objective": "peso",
        "operation": "reducir",
        "strategy": "optimizar estructura",
        "variable": "dimensiones",
    }

    new_state, impact = engine.apply_mutation(state, draft)

    assert new_state["volumen"] == 9.0
    assert new_state["masa_total"] == 4.5
    assert impact["volumen"] == -10.0
    assert impact["masa_total"] == -10.0


def test_payload_mutation_reduces_payload_and_updates_mass_partially():
    engine = MutationEngine()
    state = {
        "payload_kg": 2.0,
        "total_mass_kg": 3.2,
        "densidad": 1000.0,
    }
    draft = {
        "objective": "peso",
        "operation": "reducir",
        "strategy": "reducir carga",
        "variable": "payload",
    }

    new_state, impact = engine.apply_mutation(state, draft)

    assert new_state == {
        "payload_kg": 1.8,
        "total_mass_kg": 3.0,
    }
    assert impact == {
        "payload_kg": -10.0,
        "total_mass_kg": -6.25,
    }


def test_payload_mutation_can_increase_payload_and_updates_mass():
    engine = MutationEngine()
    state = {
        "payload_kg": 2.0,
        "total_mass_kg": 3.2,
        "densidad": 1000.0,
    }
    draft = {
        "objective": "carga",
        "operation": "aumentar",
        "strategy": "aumentar carga",
        "variable": "payload",
    }

    new_state, impact = engine.apply_mutation(state, draft)

    assert new_state == {
        "payload_kg": 2.2,
        "total_mass_kg": 3.4,
    }
    assert impact == {
        "payload_kg": 10.0,
        "total_mass_kg": 6.25,
    }


def test_default_weight_reduction_without_value_raises():
    """apply_material_mutation requires draft.value — no silent fallback."""
    engine = MutationEngine()
    state = {
        "masa_total": 3.2,
        "densidad": 2700.0,
        "material": "aluminio",
    }
    draft = {
        "objective": "peso",
        "operation": "reducir",
    }

    with pytest.raises(ValueError, match="draft.value"):
        engine.apply_mutation(state, draft)


def test_material_definition_mutation_updates_design_properties_only():
    engine = MutationEngine()
    state = {
        "design_properties": {
            "structure": {
                "material": None,
            }
        }
    }
    draft = {
        "objective": "material",
        "operation": "define",
        "variable": "material",
        "value": "fibra de carbono",
    }

    new_state, impact = engine.apply_mutation(state, draft)

    assert new_state == {
        "design_properties": {
            "structure": {
                "material": "fibra de carbono",
            }
        }
    }
    assert impact == {}


def test_power_unit_definition_mutation_updates_components_power_unit():
    engine = MutationEngine()
    state = {
        "design_properties": {
            "structure": {
                "material": "aluminio",
            }
        }
    }
    draft = {
        "objective": "sistema de potencia",
        "operation": "define",
        "variable": "componentes",
        "strategy": "definir componentes para la unidad de potencia",
        "value": "motores brushless + esc 30a",
        "restrictions": "no cambiar tamaño",
    }

    new_state, impact = engine.apply_mutation(state, draft)

    component = new_state["design_properties"]["components"]["component_1"]
    assert component["component_type"] == "propulsion_active"
    # "motores brushless + esc 30a" has no extractable KV/thrust_n/motor_count → low
    assert component["completeness"] == "low"
    assert component["inference_confidence"] == 0.75
    assert "empuje por motor, KV o potencia (W)" in component["missing_fields"]
    assert "número de motores" in component["missing_fields"]
    assert component["suggested_key"] == "motors"
    assert impact == {}


def test_power_unit_definition_requires_explicit_value():
    engine = MutationEngine()
    state = {
        "design_properties": {
            "structure": {
                "material": "aluminio",
            }
        }
    }
    draft = {
        "objective": "sistema de potencia",
        "operation": "define",
        "variable": "componentes",
        "strategy": "definir componentes para la unidad de potencia",
    }

    with pytest.raises(ValueError, match="valor explícito"):
        engine.apply_mutation(state, draft)


def test_mutation_engine_generic_define_returns_empty_patch():
    """Generic DEFINE (not material, not power_unit) must return ({}, {}) without raising."""
    engine = MutationEngine()
    state = {
        "design_properties": {
            "structure": {"material": "aluminio"}
        }
    }
    draft = {
        "objective": "optimizar estructura",
        "operation": "define",
        "variable": "estructura",
        "strategy": "optimizar topología del chasis",
    }
    state_patch, impact = engine.apply_mutation(state, draft)
    assert state_patch == {}, "generic DEFINE must produce empty state patch"
    assert impact == {}, "generic DEFINE must produce empty impact"


# ── is_physically_actionable ──────────────────────────────────────────────────

def test_is_physically_actionable_true_for_material_strategy():
    engine = MutationEngine()
    draft = IterationDraft.model_validate({"objective": "peso", "operation": "reducir", "strategy": "material", "value": "fibra de carbono"})
    assert engine.is_physically_actionable(draft) is True


def test_is_physically_actionable_true_for_volumen_strategy():
    engine = MutationEngine()
    draft = IterationDraft.model_validate({"operation": "reducir", "variable": "dimensiones", "strategy": "optimizar estructura"})
    assert engine.is_physically_actionable(draft) is True


def test_is_physically_actionable_true_for_payload_strategy():
    engine = MutationEngine()
    draft = IterationDraft.model_validate({"operation": "reducir", "variable": "payload", "strategy": "reducir carga"})
    assert engine.is_physically_actionable(draft) is True


def test_is_physically_actionable_false_for_unresolvable_draft():
    """Draft with no recognizable variable/strategy → not actionable."""
    engine = MutationEngine()
    draft = IterationDraft.model_validate({"operation": "mejorar", "variable": "autonomia", "strategy": "mejorar autonomia"})
    assert engine.is_physically_actionable(draft) is False


def test_is_physically_actionable_false_for_define_operation():
    """DEFINE is declarative, not physical — always False."""
    engine = MutationEngine()
    draft = IterationDraft.model_validate({"operation": "define", "variable": "material", "value": "fibra de carbono"})
    assert engine.is_physically_actionable(draft) is False


def test_is_physically_actionable_false_when_no_strategy_no_variable():
    """Empty draft with only an objective not matching any keyword → not actionable."""
    engine = MutationEngine()
    draft = IterationDraft.model_validate({"operation": "mejorar", "objective": "eficiencia"})
    assert engine.is_physically_actionable(draft) is False


def test_is_physically_actionable_true_for_numeric_param_with_value():
    """Numeric alias (motores) + explicit value → actionable via the numeric path, NOT resolve_strategy."""
    engine = MutationEngine()
    draft = IterationDraft.model_validate({"operation": "reducir", "variable": "motores", "value": "6"})
    assert engine.is_physically_actionable(draft) is True


def test_is_physically_actionable_false_for_numeric_param_without_value():
    """Numeric alias without a value → _is_numeric_param_mutation is False → not actionable."""
    engine = MutationEngine()
    draft = IterationDraft.model_validate({"operation": "reducir", "variable": "motores"})
    assert engine.is_physically_actionable(draft) is False
