import pytest

from jarvis.core.component_resolver import PropulsionOverride, resolve_propulsion_parameters


# ── Helpers ───────────────────────────────────────────────────────────────────

def _active(completeness="low", thrust_n=None, motor_count=None, name="motor", output_magnitude="thrust_n"):
    properties = {}
    if thrust_n is not None:
        properties["thrust_n"] = {"value": thrust_n, "unit": "N", "confidence": 1.0, "source": "declared"}
    if motor_count is not None:
        properties["motor_count"] = {"value": motor_count, "unit": None, "confidence": 1.0, "source": "declared"}
    return {
        "name": name,
        "component_type": "propulsion_active",
        "completeness": completeness,
        "properties": properties,
        "missing_fields": [],
        "hints": [],
        "source": "declared",
        "inference_confidence": 0.75,
        "suggested_key": None,
        "output_magnitude": output_magnitude,
    }


def _passive(completeness="low"):
    return {
        "name": "hélice",
        "component_type": "propulsion_passive",
        "completeness": completeness,
        "properties": {},
        "missing_fields": [],
        "hints": [],
        "source": "declared",
        "inference_confidence": 0.0,
        "suggested_key": None,
    }


# ── No components → no override ───────────────────────────────────────────────

def test_empty_components_returns_no_override():
    result = resolve_propulsion_parameters({})
    assert result.motors is None
    assert result.per_motor_max_thrust_n is None
    assert not result.has_any


# ── Only passive components (hélices) → no override ──────────────────────────

def test_only_passive_components_returns_no_override():
    result = resolve_propulsion_parameters({"helice_1": _passive("high"), "helice_2": _passive("medium")})
    assert not result.has_any


# ── Low completeness, no thrust_n → not eligible ─────────────────────────────

def test_low_completeness_without_thrust_not_eligible():
    result = resolve_propulsion_parameters({"motors": _active("low")})
    assert not result.has_any
    assert result.trace["reason"] == "no_eligible_components"
    assert len(result.trace["skipped"]) == 1


# ── Medium completeness → eligible for motor count ───────────────────────────

def test_medium_completeness_entry_yields_motor_count():
    result = resolve_propulsion_parameters({"motors": _active("medium")})
    assert result.motors == 1
    assert result.per_motor_max_thrust_n is None
    assert result.has_any


def test_high_completeness_entry_yields_motor_count():
    result = resolve_propulsion_parameters({"motors": _active("high")})
    assert result.motors == 1
    assert result.has_any


# ── Explicit thrust_n on low completeness → eligible ─────────────────────────

def test_low_completeness_with_explicit_thrust_is_eligible():
    result = resolve_propulsion_parameters({"m": _active("low", thrust_n=15.0)})
    assert result.motors == 1
    assert result.per_motor_max_thrust_n == 15.0
    assert result.has_any


# ── Full spec: motor_count + thrust_n ────────────────────────────────────────

def test_full_spec_with_motor_count_and_thrust():
    result = resolve_propulsion_parameters({"motors": _active("high", thrust_n=12.5, motor_count=4)})
    assert result.motors == 4
    assert result.per_motor_max_thrust_n == 12.5
    assert "properties.motor_count" in result.trace["motors"]["source"]
    assert "properties.thrust_n" in result.trace["per_motor_max_thrust_n"]["source"]


# ── motor_count takes priority over count of entries ─────────────────────────

def test_motor_count_property_takes_priority_over_entry_count():
    components = {
        "m1": _active("high", motor_count=4),
        "m2": _active("high"),
    }
    result = resolve_propulsion_parameters(components)
    # 2 eligible entries, but motor_count=4 on m1 takes priority
    assert result.motors == 4
    assert "properties.motor_count" in result.trace["motors"]["source"]


# ── Multiple eligible entries, count fallback ────────────────────────────────

def test_multiple_eligible_entries_counted_when_no_motor_count():
    components = {
        "m1": _active("medium"),
        "m2": _active("medium"),
        "m3": _active("medium"),
    }
    result = resolve_propulsion_parameters(components)
    assert result.motors == 3
    assert "count of eligible" in result.trace["motors"]["source"]


# ── Mix of eligible and ineligible ───────────────────────────────────────────

def test_only_eligible_entries_counted():
    components = {
        "good": _active("medium"),
        "bad": _active("low"),           # ineligible
        "passive": _passive("high"),      # wrong type
    }
    result = resolve_propulsion_parameters(components)
    assert result.motors == 1
    assert len(result.trace["skipped"]) == 1   # only the low-completeness active one


# ── apply_to: parameters are not mutated ─────────────────────────────────────

def test_apply_to_does_not_mutate_original():
    params = {"motor_count": 4, "per_motor_max_thrust_n": 15.0, "payload_kg": 2.0}
    override = PropulsionOverride(motors=6, per_motor_max_thrust_n=20.0)
    updated = override.apply_to(params)
    assert params["motor_count"] == 4          # original unchanged
    assert updated["motor_count"] == 6
    assert updated["per_motor_max_thrust_n"] == 20.0
    assert updated["payload_kg"] == 2.0   # other params preserved


def test_apply_to_noop_when_no_override():
    params = {"motor_count": 4, "per_motor_max_thrust_n": 15.0}
    override = PropulsionOverride(motors=None, per_motor_max_thrust_n=None)
    updated = override.apply_to(params)
    assert updated == params


# ── Trace structure ───────────────────────────────────────────────────────────

def test_trace_contains_eligible_count_and_skipped():
    components = {
        "good": _active("high", thrust_n=10.0),
        "bad": _active("low"),
    }
    result = resolve_propulsion_parameters(components)
    assert result.trace["eligible_count"] == 1
    assert len(result.trace["skipped"]) == 1
    assert result.trace["motors"]["value"] == 1
    assert result.trace["per_motor_max_thrust_n"]["value"] == 10.0


def test_trace_indicates_unresolved_thrust_when_none():
    result = resolve_propulsion_parameters({"m": _active("medium")})
    assert result.trace["per_motor_max_thrust_n"]["value"] is None
    assert "not_resolved" in result.trace["per_motor_max_thrust_n"]["source"]


# ── output_magnitude: resolver respects declared magnitude  ──────────────────

def test_resolver_skips_force_when_output_magnitude_is_torque():
    """Ground component with torque_nm must not produce a per_motor_max_thrust_n override."""
    ground_component = {
        "name": "motor traccion",
        "component_type": "traction_active",
        "completeness": "high",
        "properties": {
            "torque_nm": {"value": 50.0, "unit": "Nm", "confidence": 0.9, "source": "declared"},
        },
        "missing_fields": [],
        "hints": [],
        "source": "declared",
        "inference_confidence": 0.75,
        "suggested_key": "wheel_actuators",
        "output_magnitude": "torque_nm",
    }
    result = resolve_propulsion_parameters({"actuator": ground_component})
    assert result.motors == 1           # count still resolved
    assert result.per_motor_max_thrust_n is None  # torque not converted to force
    assert "not_resolved" in result.trace["per_motor_max_thrust_n"]["source"]
    # eligible_for_count_only must identify this component explicitly
    count_only = result.trace["eligible_for_count_only"]
    assert len(count_only) == 1
    assert count_only[0]["key"] == "actuator"
    assert "torque_nm" in count_only[0]["reason"]
    # must NOT appear in skipped — it passed eligibility, it was counted
    assert "actuator" not in [x["key"] for x in result.trace["skipped"]]


def test_resolver_resolves_force_when_output_magnitude_is_thrust_n():
    """Aerial component with thrust_n and output_magnitude='thrust_n' must produce override."""
    result = resolve_propulsion_parameters({"m": _active("high", thrust_n=15.0)})
    assert result.per_motor_max_thrust_n == 15.0


def test_resolver_skips_force_when_output_magnitude_is_none():
    """Component with no output_magnitude must not produce a force override."""
    no_magnitude_component = {
        "name": "generic actuator",
        "component_type": "propulsion_active",
        "completeness": "high",
        "properties": {
            "thrust_n": {"value": 20.0, "unit": "N", "confidence": 0.9, "source": "declared"},
        },
        "missing_fields": [],
        "hints": [],
        "source": "declared",
        "inference_confidence": 0.5,
        "suggested_key": None,
        "output_magnitude": None,
    }
    result = resolve_propulsion_parameters({"m": no_magnitude_component})
    assert result.motors == 1
    assert result.per_motor_max_thrust_n is None
    # None magnitude also lands in eligible_for_count_only
    count_only = result.trace["eligible_for_count_only"]
    assert len(count_only) == 1
    assert count_only[0]["key"] == "m"
    # must NOT appear in skipped — it passed eligibility, it was counted
    assert "m" not in [x["key"] for x in result.trace["skipped"]]


def test_trace_eligible_for_count_only_empty_when_thrust_n():
    """Aerial component with output_magnitude=thrust_n must NOT appear in eligible_for_count_only."""
    result = resolve_propulsion_parameters({"m": _active("high", thrust_n=15.0)})
    assert result.trace["eligible_for_count_only"] == []


def test_trace_eligible_for_count_only_present_on_normal_no_force_path():
    """Component with medium completeness but no force value: not in eligible_for_count_only
    (it has thrust_n output_magnitude but value is None), so force stays null but count_only is empty."""
    result = resolve_propulsion_parameters({"m": _active("medium")})
    assert result.trace["eligible_for_count_only"] == []
    assert result.trace["per_motor_max_thrust_n"]["value"] is None


# ── per_actuator_torque_nm: resolver extracts declared torque value ───────────

def _traction(completeness="high", torque_nm=None, motor_count=None, name="motor_traccion"):
    properties = {}
    if torque_nm is not None:
        properties["torque_nm"] = {"value": torque_nm, "unit": "Nm", "confidence": 1.0, "source": "declared"}
    if motor_count is not None:
        properties["motor_count"] = {"value": motor_count, "unit": None, "confidence": 1.0, "source": "declared"}
    return {
        "name": name,
        "component_type": "traction_active",
        "completeness": completeness,
        "properties": properties,
        "missing_fields": [],
        "hints": [],
        "source": "declared",
        "inference_confidence": 0.75,
        "suggested_key": None,
        "output_magnitude": "torque_nm",
    }


def test_resolver_extracts_torque_nm_into_physical_override():
    """Declared torque_nm on traction_active → PhysicalOverride.per_actuator_torque_nm set."""
    result = resolve_propulsion_parameters({"w1": _traction(torque_nm=50.0)})
    assert result.per_actuator_torque_nm == 50.0
    assert result.motors == 1
    assert result.per_motor_max_thrust_n is None  # resolver does not convert
    assert result.has_any


def test_resolver_torque_nm_appears_in_eligible_for_count_only_with_extracted_value():
    """torque_nm entry must land in eligible_for_count_only with extraction noted."""
    result = resolve_propulsion_parameters({"w1": _traction(torque_nm=80.0)})
    count_only = result.trace["eligible_for_count_only"]
    assert len(count_only) == 1
    assert count_only[0]["key"] == "w1"
    assert count_only[0].get("torque_nm_extracted") == 80.0
    # must NOT be in skipped
    assert "w1" not in [x["key"] for x in result.trace["skipped"]]


def test_resolver_trace_per_actuator_torque_nm_when_extracted():
    result = resolve_propulsion_parameters({"w1": _traction(torque_nm=120.0)})
    torque_trace = result.trace["per_actuator_torque_nm"]
    assert torque_trace["value"] == 120.0
    assert "properties.torque_nm" in torque_trace["source"]


def test_resolver_torque_nm_not_extracted_when_no_value():
    """traction_active without declared torque: per_actuator_torque_nm remains None."""
    entry = _traction(completeness="high")  # no torque_nm property
    result = resolve_propulsion_parameters({"w1": entry})
    assert result.per_actuator_torque_nm is None
    assert result.trace["per_actuator_torque_nm"]["value"] is None
    assert result.trace["per_actuator_torque_nm"]["source"] == "not_extracted"


def test_resolver_apply_to_injects_per_actuator_torque_nm():
    """apply_to must write per_actuator_torque_nm into parameters dict."""
    result = resolve_propulsion_parameters({"w1": _traction(torque_nm=60.0)})
    params = {"payload_kg": 5.0, "safety_factor": 1.2, "vehicle_type": "ground"}
    updated = result.apply_to(params)
    assert updated["per_actuator_torque_nm"] == 60.0
    assert updated["motor_count"] == 1
    # original not mutated
    assert "per_actuator_torque_nm" not in params


def test_resolver_first_declared_torque_wins_with_multiple_wheels():
    """When multiple torque_nm entries, only the first extracted value is used."""
    components = {
        "w1": _traction(torque_nm=50.0, name="w1"),
        "w2": _traction(torque_nm=80.0, name="w2"),
    }
    result = resolve_propulsion_parameters(components)
    # motors = 2 (count of eligible), per_actuator_torque_nm = first extracted
    assert result.motors == 2
    assert result.per_actuator_torque_nm == 50.0


# ── force_resolution_status: unified audit trace ──────────────────────────────

def test_force_resolution_status_force_resolved_for_aerial():
    """Aerial motor with declared thrust_n → overall status force_resolved."""
    result = resolve_propulsion_parameters({"m": _active("high", thrust_n=15.0)})
    assert result.trace["force_resolution_status"] == "force_resolved"


def test_force_resolution_status_missing_parameters_for_torque_with_value():
    """Traction motor with declared torque_nm → overall status missing_parameters (engine will convert)."""
    result = resolve_propulsion_parameters({"w1": _traction(torque_nm=50.0)})
    assert result.trace["force_resolution_status"] == "missing_parameters"


def test_force_resolution_status_count_only_for_torque_without_value():
    """Traction motor without declared torque → overall status count_only."""
    result = resolve_propulsion_parameters({"w1": _traction()})
    assert result.trace["force_resolution_status"] == "count_only"


def test_force_resolution_status_count_only_for_unknown_magnitude():
    """Component with None output_magnitude → count_only."""
    no_magnitude = {
        "name": "generic",
        "component_type": "propulsion_active",
        "completeness": "high",
        "properties": {},
        "missing_fields": [],
        "hints": [],
        "source": "declared",
        "inference_confidence": 0.5,
        "suggested_key": None,
        "output_magnitude": None,
    }
    result = resolve_propulsion_parameters({"m": no_magnitude})
    assert result.trace["force_resolution_status"] == "count_only"


def test_force_resolution_detail_has_one_entry_per_eligible_component():
    """force_resolution_detail must list every eligible component exactly once."""
    components = {
        "m1": _active("high", thrust_n=15.0),
        "m2": _active("medium"),
    }
    result = resolve_propulsion_parameters(components)
    detail = result.trace["force_resolution_detail"]
    assert len(detail) == 2
    keys = {e["key"] for e in detail}
    assert keys == {"m1", "m2"}


def test_force_resolution_detail_statuses_match():
    """force_resolved entry exists for the component with declared thrust."""
    components = {
        "m1": _active("high", thrust_n=15.0),
        "m2": _active("medium"),
    }
    result = resolve_propulsion_parameters(components)
    detail = {e["key"]: e["force_resolution_status"] for e in result.trace["force_resolution_detail"]}
    assert detail["m1"] == "force_resolved"
    assert detail["m2"] == "count_only"


def test_force_resolution_takes_highest_rank_across_entries():
    """Mixed: one count_only + one force_resolved → overall is force_resolved."""
    components = {
        "m1": _active("high", thrust_n=20.0),
        "m2": _traction(torque_nm=50.0, name="w"),
    }
    result = resolve_propulsion_parameters(components)
    # m1 is force_resolved (rank 3), w is missing_parameters (rank 2) — force_resolved wins
    assert result.trace["force_resolution_status"] == "force_resolved"


# ── force_resolution_detail: reason field ─────────────────────────────────────

def test_force_resolution_detail_missing_parameters_has_transmission_reason():
    """Traction motor with torque_nm → detail entry reason == missing_transmission_parameters."""
    result = resolve_propulsion_parameters({"w1": _traction(torque_nm=50.0)})
    detail = {e["key"]: e for e in result.trace["force_resolution_detail"]}
    assert detail["w1"]["reason"] == "missing_transmission_parameters"


def test_force_resolution_detail_force_resolved_has_thrust_declared_reason():
    """Aerial motor with thrust_n declared → detail entry reason == thrust_n_declared."""
    result = resolve_propulsion_parameters({"m": _active("high", thrust_n=15.0)})
    d = result.trace["force_resolution_detail"][0]
    assert d["reason"] == "thrust_n_declared"


def test_force_resolution_detail_count_only_thrust_has_not_declared_reason():
    """Active motor without thrust_n value → detail entry reason == thrust_n_not_declared."""
    result = resolve_propulsion_parameters({"m": _active("medium")})
    d = result.trace["force_resolution_detail"][0]
    assert d["reason"] == "thrust_n_not_declared"


def test_force_resolution_detail_count_only_other_magnitude_has_output_magnitude_reason():
    """Active motor with non-thrust_n output_magnitude → detail reason starts with 'output_magnitude='."""
    comp = _active("medium", output_magnitude="power_w")
    result = resolve_propulsion_parameters({"m": comp})
    d = result.trace["force_resolution_detail"][0]
    assert d["reason"].startswith("output_magnitude=")
