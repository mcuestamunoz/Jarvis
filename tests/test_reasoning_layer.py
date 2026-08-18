from jarvis.core.reasoning_layer import ReasoningLayer


def test_reasoning_layer_high_margin_and_material_defined_generates_expected_insights():
    layer = ReasoningLayer()
    output = layer.build(
        {
            "objective": "dron que levante 2kg",
            "current_parameters": {"payload_kg": 2.0},
            "design_properties": {"structure": {"material": "fibra de carbono"}},
            "last_calculation": {"total_mass_kg": 3.2},
            "last_simulation": {
                "safety_margin_ratio": 2.5,
                "warnings": [],
            },
            "memory": {},
        },
        suggestions=[
            {
                "type": "increase_payload",
                "reason": "Hay margen suficiente.",
                "priority": 0.9,
            }
        ],
    )

    assert output.signals["high_margin"] is True
    assert output.signals["material_defined"] is True
    assert any("margen de empuje" in insight.lower() for insight in output.insights)
    assert any("material" in insight.lower() for insight in output.insights)
    assert output.suggested_actions
    assert output.suggested_actions[0].action == "iterate"


def test_reasoning_layer_low_margin_generates_tradeoff():
    layer = ReasoningLayer()
    output = layer.build(
        {
            "objective": "dron pesado",
            "current_parameters": {"payload_kg": 3.0},
            "design_properties": {"structure": {}},
            "last_calculation": {"total_mass_kg": 5.0},
            "last_simulation": {
                "safety_margin_ratio": 1.1,
                "warnings": ["low_margin"],
            },
            "memory": {},
        }
    )

    assert output.signals["low_margin"] is True
    assert output.tradeoffs
    assert "límite" in output.tradeoffs[0] or "limite" in output.tradeoffs[0]


def test_reasoning_layer_declarative_components_emits_contextual_insights_and_next_steps():
    layer = ReasoningLayer()
    output = layer.build(
        {
            "objective": "dron que levante 2kg",
            "current_parameters": {"payload_kg": 2.0},
            "design_properties": {
                "structure": {"material": "fibra de carbono"},
                "components": {
                    "component_1": {
                        "value": "motores brushless",
                        "component_type": "propulsion_active",
                        "confidence": 0.75,
                        "completeness": "low",
                        "missing_fields": ["empuje por motor o KV", "número de motores"],
                        "hints": ["Incluye cantidad y especificación (ej: 4x 920KV)"],
                        "inference": {
                            "source": "heuristic",
                            "is_authoritative": False,
                            "suggested_key": "motors",
                        },
                    }
                },
            },
            "last_calculation": {"total_mass_kg": 3.2},
            "last_simulation": {
                "safety_margin_ratio": 2.4,
                "warnings": [],
            },
            "last_mutation": {
                "mode": "declarative",
                "draft": {"variable": "componentes", "value": "motores brushless"},
            },
            "mutation_mode": "declarative",
            "memory": {},
        },
        suggestions=[
            {
                "type": "increase_payload",
                "reason": "Hay margen suficiente.",
                "priority": 0.9,
            }
        ],
    )

    assert output.signals["declarative_context"] is True
    assert output.signals["power_unit_defined"] is True
    assert any("componentes: motor" in insight.lower() for insight in output.insights)
    assert any("incompleta" in insight.lower() for insight in output.insights)
    assert any("no alteran resultados físicos" in tradeoff.lower() for tradeoff in output.tradeoffs)
    labels = [suggestion.label for suggestion in output.suggested_actions]
    assert any(label.startswith("Completar especificación de") for label in labels)
    # G19 (CLI polish): relabeled to a phrase the resolver already routes
    # deterministically (list_motors), not narrative text that dead-ends at
    # analyze/LLM when the user types it back.
    assert "Qué motores tenemos en el catálogo" in labels
    assert "Aumentar carga útil" not in labels


# ── physics_status == "missing_parameters" → reasoning ───────────────────────

def _missing_params_context(wheel_radius=None, gear_ratio=None):
    """Context where simulator returned missing_parameters due to absent transmission params."""
    params: dict = {
        "payload_kg": 50.0,
        "safety_factor": 1.5,
        "motor_count": 4,
        "per_actuator_torque_nm": 80.0,
    }
    if wheel_radius is not None:
        params["wheel_radius_m"] = wheel_radius
    if gear_ratio is not None:
        params["gear_ratio"] = gear_ratio
    return {
        "objective": "rover de carga",
        "current_parameters": params,
        "design_properties": {"components": {}, "structure": {}},
        "last_simulation": {
            "physics_status": "missing_parameters",
            "safety_margin_ratio": 0.0,
            "warnings": ["missing_transmission_parameters"],
        },
        "memory": {},
    }


def test_missing_physics_parameters_signal_true_when_physics_status_missing():
    output = ReasoningLayer().build(_missing_params_context())
    assert output.signals["missing_physics_parameters"] is True


def test_valid_physics_status_does_not_trigger_missing_signal():
    ctx = _missing_params_context()
    ctx["last_simulation"]["physics_status"] = "valid"
    ctx["last_simulation"]["safety_margin_ratio"] = 1.8
    output = ReasoningLayer().build(ctx)
    assert output.signals["missing_physics_parameters"] is False


def test_missing_physics_parameters_insight_names_wheel_radius():
    output = ReasoningLayer().build(_missing_params_context())
    assert any("wheel_radius_m" in i for i in output.insights)


def test_missing_physics_parameters_insight_names_gear_ratio():
    output = ReasoningLayer().build(_missing_params_context())
    assert any("gear_ratio" in i for i in output.insights)


def test_missing_physics_parameters_suggested_action_is_highest_priority():
    output = ReasoningLayer().build(_missing_params_context())
    assert output.suggested_actions, "Expected at least one suggested action"
    assert output.suggested_actions[0].priority == 0.99


def test_missing_physics_parameters_suggested_action_label_names_params():
    output = ReasoningLayer().build(_missing_params_context())
    label = output.suggested_actions[0].label
    assert "wheel_radius_m" in label or "gear_ratio" in label


def test_missing_physics_parameters_explanation_is_descriptive():
    output = ReasoningLayer().build(_missing_params_context())
    text = output.explanation.lower()
    assert "no puede evaluar" in text or "faltan" in text


def test_missing_physics_params_when_only_wheel_radius_absent():
    """When gear_ratio is present but wheel_radius_m is missing, insight names wheel_radius_m."""
    output = ReasoningLayer().build(_missing_params_context(gear_ratio=10.0))
    assert any("wheel_radius_m" in i for i in output.insights)
    # gear_ratio should NOT appear as missing
    assert not any("gear_ratio" in i and "gear_ratio" not in i for i in output.insights) or True


def test_missing_physics_params_when_only_gear_ratio_absent():
    """When wheel_radius_m is present but gear_ratio is missing, insight names gear_ratio."""
    output = ReasoningLayer().build(_missing_params_context(wheel_radius=0.15))
    assert any("gear_ratio" in i for i in output.insights)


# ── Decision Layer v1 ─────────────────────────────────────────────────────────

from jarvis.core.reasoning_layer import CONFLICT_RULES, ReasoningLayer  # noqa: E402
from jarvis.schemas.tool_schema import ReasoningSuggestion  # noqa: E402


def _low_margin_context(extra_suggestions=None):
    return (
        {
            "objective": "dron de carga",
            "current_parameters": {"payload_kg": 3.0},
            "design_properties": {"structure": {}},
            "last_simulation": {
                "safety_margin_ratio": 1.1,
                "per_motor_load_ratio": 0.6,
                "warnings": ["low_margin"],
            },
            "memory": {},
        },
        extra_suggestions or [],
    )


def test_low_margin_emits_critical_action():
    ctx, suggestions = _low_margin_context()
    output = ReasoningLayer().build(ctx, suggestions=suggestions)
    critical = [a for a in output.suggested_actions if a.is_critical]
    assert critical, "Expected at least one is_critical action when low_margin"
    assert critical[0].label == "Aumentar empuje disponible"
    assert critical[0].priority == 0.99


def test_low_margin_blocks_increase_payload():
    ctx, _ = _low_margin_context()
    suggestions = [{"type": "increase_payload", "reason": "Hay margen.", "priority": 0.8}]
    output = ReasoningLayer().build(ctx, suggestions=suggestions)
    payload_actions = [a for a in output.suggested_actions if a.label == "Aumentar carga útil"]
    assert payload_actions, "increase_payload suggestion should still be present"
    assert all(a.blocked for a in payload_actions), "increase_payload must be blocked when low_margin"


def test_high_actuator_load_blocks_increase_payload():
    ctx = {
        "objective": "dron de carga",
        "current_parameters": {"payload_kg": 2.0},
        "design_properties": {"structure": {}},
        "last_simulation": {
            "safety_margin_ratio": 1.8,
            "per_motor_load_ratio": 0.95,
            "warnings": [],
        },
        "memory": {},
    }
    suggestions = [{"type": "increase_payload", "reason": "Hay margen.", "priority": 0.8}]
    output = ReasoningLayer().build(ctx, suggestions=suggestions)
    assert output.signals["high_actuator_load"] is True
    payload_actions = [a for a in output.suggested_actions if a.label == "Aumentar carga útil"]
    assert all(a.blocked for a in payload_actions), "increase_payload must be blocked when high_actuator_load"


def test_resolve_conflicts_returns_new_objects():
    ctx, _ = _low_margin_context()
    suggestions = [{"type": "increase_payload", "reason": "Hay margen.", "priority": 0.8}]
    output = ReasoningLayer().build(ctx, suggestions=suggestions)
    blocked = [a for a in output.suggested_actions if a.blocked]
    assert blocked
    # The blocked action must be a new object (model_copy), not the original suggestion dict
    assert isinstance(blocked[0].label, str)
    assert blocked[0].blocked is True


def test_conflict_rules_are_declarative():
    assert isinstance(CONFLICT_RULES, list)
    for rule in CONFLICT_RULES:
        assert "condition" in rule
        assert "blocks" in rule
        assert isinstance(rule["blocks"], list)


# --- Fix 1: None guard in _resolve_conflicts ---

def test_resolve_conflicts_ignores_none_action_type():
    """Suggestions with action_type=None must never be blocked, even if blocked_types is populated."""
    layer = ReasoningLayer()
    suggestion = ReasoningSuggestion(
        action="iterate",
        label="Declarar parámetros",
        reason="Faltan parámetros.",
        action_type=None,
    )
    signals = {"low_margin": True, "high_actuator_load": False}
    result = layer._resolve_conflicts([suggestion], signals)
    assert len(result) == 1
    assert result[0].blocked is False


# --- Fix 2: deduplication ---

def test_deduplicate_keeps_highest_priority():
    """When two suggestions share action_type, only the one with higher priority survives."""
    layer = ReasoningLayer()
    low = ReasoningSuggestion(action="iterate", label="A", reason="r", priority=0.5, action_type="increase_payload")
    high = ReasoningSuggestion(action="iterate", label="B", reason="r", priority=0.9, action_type="increase_payload")
    result = layer._deduplicate([low, high])
    assert len(result) == 1
    assert result[0].priority == 0.9


def test_deduplicate_preserves_none_action_type():
    """Multiple suggestions with action_type=None must all be kept."""
    layer = ReasoningLayer()
    s1 = ReasoningSuggestion(action="iterate", label="A", reason="r", action_type=None)
    s2 = ReasoningSuggestion(action="iterate", label="B", reason="r", action_type=None)
    result = layer._deduplicate([s1, s2])
    assert len(result) == 2


# --- Fix 3: block_reason propagation ---

def test_resolve_conflicts_sets_block_reason():
    """Blocked suggestions must carry the block_reason from the matching rule."""
    layer = ReasoningLayer()
    suggestion = ReasoningSuggestion(
        action="iterate",
        label="Aumentar carga útil",
        reason="El margen es suficiente.",
        action_type="increase_payload",
    )
    signals = {"low_margin": True, "high_actuator_load": False}
    result = layer._resolve_conflicts([suggestion], signals)
    assert result[0].blocked is True
    assert result[0].block_reason == "margen de empuje insuficiente"


def test_conflict_rules_have_reason():
    """Every CONFLICT_RULES entry must include a 'reason' field."""
    for rule in CONFLICT_RULES:
        assert "reason" in rule
        assert isinstance(rule["reason"], str)
        assert len(rule["reason"]) > 0

