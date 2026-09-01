"""Physical Component Catalog v1 — Impl A (Foundation).

Design authority: docs/PHYSICAL_COMPONENT_CATALOG_V1.md (DESIGN CLOSED, locks 1A-5A).

Scope of this file: ComponentLibrary's new battery/propeller loaders + API,
motor enrichment fields, match_motor_propeller, and the ComponentSpec.catalog_ref
schema placeholder. Nothing here exercises a Bind write path — no production
code sets catalog_ref (Impl B territory); tests that construct one do so
directly, as a unit-only round-trip proof.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.knowledge.library import BatterySpec, ComponentLibrary, EscSpec, MotorSpec, PropellerSpec
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec

_LIB = ComponentLibrary()


# ── 1. Motors load; existing known SKU works (regression) ──────────────────

def test_get_motor_exact_name_still_works():
    spec = _LIB.get_motor("generic_920kv")
    assert isinstance(spec, MotorSpec)
    assert spec.kv_rating == 920
    assert spec.thrust_n == 10.0


# ── 2. D8-style find_motors_for_requirements smoke (regression) ────────────

def test_find_motors_for_requirements_still_works():
    results = _LIB.find_motors_for_requirements(min_thrust_n=20.0)
    assert results
    assert all(m.max_thrust_n >= 20.0 or m.thrust_n >= 20.0 for m in results)


# ── 3. Enriched optional motor fields ───────────────────────────────────────

def test_motor_optional_enrichment_fields_default_none():
    spec = _LIB.get_motor("generic_920kv")
    assert spec.manufacturer is None
    assert spec.model is None
    assert spec.compatible_prop_ids == ()
    assert spec.operating_points == ()
    assert spec.source_url is None
    assert spec.identity_status is None


def test_sunnysky_r2205_2500_verified_motor_identity():
    spec = _LIB.get_motor("sunnysky_r2205_2500")
    assert spec.identity_status == "verified"
    assert spec.manufacturer == "SunnySky"
    assert spec.part_number == "2205R25CW / 2205G25CW"
    assert spec.max_watts == pytest.approx(756.0)
    assert spec.max_current_a == pytest.approx(45.0)
    assert spec.voltage_min == pytest.approx(9.0)
    assert spec.voltage_max == pytest.approx(16.8)


def test_emax_rs2205s_2300_verified_motor_identity_no_nominal_power():
    spec = _LIB.get_motor("emax_rs2205s_2300")
    assert spec.identity_status == "verified"
    assert spec.part_number == "0101008001"
    assert spec.model == "RS2205 RaceSpec"
    assert spec.max_watts is None
    assert spec.max_current_a is None
    assert spec.voltage_min == pytest.approx(12.6)
    assert spec.voltage_max == pytest.approx(16.8)


def test_motor_optional_enrichment_fields_load_when_present(tmp_path: Path):
    (tmp_path / "motores").mkdir()
    (tmp_path / "materiales").mkdir()
    (tmp_path / "baterias").mkdir()
    (tmp_path / "helices").mkdir()
    (tmp_path / "motores" / "_datos.json").write_text(
        """{
          "custom_motor": {
            "thrust_n": 10.0, "kv_rating": 900, "weight_g": 60, "max_watts": 250,
            "compatible_prop_inch": [10],
            "manufacturer": "acme", "model": "X1", "max_current_a": 30.0,
            "voltage_min": 11.1, "voltage_max": 22.2,
            "compatible_prop_ids": ["apc_10x4_5"],
            "operating_points": [{"rpm": 8000, "thrust_n": 9.5}],
            "source_url": "https://example.com/x1"
          }
        }""",
        encoding="utf-8",
    )
    (tmp_path / "materiales" / "_datos.json").write_text("{}", encoding="utf-8")
    (tmp_path / "baterias" / "_datos.json").write_text("{}", encoding="utf-8")
    (tmp_path / "helices" / "_datos.json").write_text("{}", encoding="utf-8")
    lib = ComponentLibrary(library_root=tmp_path)
    spec = lib.get_motor("custom_motor")
    assert spec.manufacturer == "acme"
    assert spec.model == "X1"
    assert spec.max_current_a == 30.0
    assert spec.compatible_prop_ids == ("apc_10x4_5",)
    assert spec.operating_points == ({"rpm": 8000, "thrust_n": 9.5},)
    assert spec.source_url == "https://example.com/x1"


# ── 4. Batteries load; get_battery by id; required fields present ──────────

def test_batteries_load_and_get_by_id():
    spec = _LIB.get_battery("lipo_4s_5000mah")
    assert isinstance(spec, BatterySpec)
    assert spec.chemistry == "lipo"
    assert spec.energy_wh == 74.0
    assert spec.mass_g == 498.0
    assert spec.cells == 4


def test_lipo_4s_1500mah_cnhl_verified_identity():
    spec = _LIB.get_battery("lipo_4s_1500mah")
    assert spec.identity_status == "verified"
    assert spec.manufacturer == "CNHL"
    assert spec.part_number == "1501004BK"
    assert spec.mass_g == pytest.approx(183.0)
    assert spec.max_continuous_current_a == pytest.approx(150.0)
    assert spec.max_continuous_current_source == "derived_from_c_rating"


def test_lipo_4s_5000mah_spektrum_verified_identity():
    spec = _LIB.get_battery("lipo_4s_5000mah")
    assert spec.identity_status == "verified"
    assert spec.manufacturer == "Spektrum"
    assert spec.part_number == "SPMX50004S100HT"
    assert spec.c_rating == pytest.approx(100.0)
    assert spec.max_continuous_current_a == pytest.approx(500.0)
    assert spec.max_continuous_current_source == "derived_from_c_rating"


def test_lipo_6s_6000mah_gnb_verified_identity():
    spec = _LIB.get_battery("lipo_6s_6000mah")
    assert spec.identity_status == "verified"
    assert spec.manufacturer == "GNB"
    assert spec.pack_configuration == "6S2P"
    assert spec.mass_g == pytest.approx(793.0)
    assert spec.max_continuous_current_a == pytest.approx(600.0)


def test_all_seed_batteries_have_required_fields():
    for b in _LIB.list_batteries():
        assert b.chemistry
        assert b.energy_wh > 0
        assert b.mass_g > 0
        assert b.cells is not None or b.nominal_voltage is not None


def test_battery_unknown_raises_keyerror():
    with pytest.raises(KeyError, match="bateria_ficticia"):
        _LIB.get_battery("bateria_ficticia")


def test_has_battery():
    assert _LIB.has_battery("lipo_3s_2200mah") is True
    assert _LIB.has_battery("no_existe_xyz") is False


def test_find_batteries_min_energy_filter():
    results = _LIB.find_batteries(min_energy_wh=100.0)
    assert results
    assert all(b.energy_wh >= 100.0 for b in results)


def test_find_batteries_chemistry_filter():
    results = _LIB.find_batteries(chemistry="lipo")
    assert results
    assert all(b.chemistry == "lipo" for b in results)
    assert _LIB.find_batteries(chemistry="lifepo4") == []


def test_battery_missing_required_field_raises(tmp_path: Path):
    (tmp_path / "motores").mkdir()
    (tmp_path / "materiales").mkdir()
    (tmp_path / "baterias").mkdir()
    (tmp_path / "helices").mkdir()
    for name in ("motores", "materiales", "helices"):
        (tmp_path / name / "_datos.json").write_text("{}", encoding="utf-8")
    (tmp_path / "baterias" / "_datos.json").write_text(
        '{"broken": {"chemistry": "lipo", "energy_wh": 10.0}}', encoding="utf-8"
    )
    lib = ComponentLibrary(library_root=tmp_path)
    with pytest.raises(ValueError, match="mass_g"):
        lib.list_batteries()


def test_battery_missing_voltage_identity_raises(tmp_path: Path):
    (tmp_path / "motores").mkdir()
    (tmp_path / "materiales").mkdir()
    (tmp_path / "baterias").mkdir()
    (tmp_path / "helices").mkdir()
    for name in ("motores", "materiales", "helices"):
        (tmp_path / name / "_datos.json").write_text("{}", encoding="utf-8")
    (tmp_path / "baterias" / "_datos.json").write_text(
        '{"broken": {"chemistry": "lipo", "energy_wh": 10.0, "mass_g": 80}}', encoding="utf-8"
    )
    lib = ComponentLibrary(library_root=tmp_path)
    with pytest.raises(ValueError, match="voltaje"):
        lib.list_batteries()


# ── 5. Propellers load; get_propeller; diameter/pitch preserved ────────────

def test_propellers_load_and_get_by_id():
    spec = _LIB.get_propeller("apc_10x4_5")
    assert isinstance(spec, PropellerSpec)
    assert spec.diameter_in == 10.0
    assert spec.pitch_in == 4.5


def test_gf_5045x3_curated_identity_and_mass():
    spec = _LIB.get_propeller("gf_5045x3")
    assert spec.mass_g == pytest.approx(4.5)
    assert spec.manufacturer == "Gemfan"
    assert spec.model == "5045 3-Blade"
    assert spec.part_number == "PMAB5045-3"
    assert spec.source_url is not None


def test_hq_5045_bn_partially_verified_identity():
    spec = _LIB.get_propeller("hq_5045_bn")
    assert spec.identity_status == "partially_verified"
    assert spec.manufacturer == "HQProp"
    assert spec.model == "5045 BN"
    assert spec.mass_g is None


def test_gemfan_5045_hbn_verified_identity():
    spec = _LIB.get_propeller("gemfan_5045_hbn")
    assert spec.identity_status == "verified"
    assert spec.manufacturer == "Gemfan"
    assert spec.model == "5045 HBN"
    assert spec.mass_g is None


def test_all_seed_propellers_have_required_fields():
    for p in _LIB.list_propellers():
        assert p.diameter_in > 0
        assert p.pitch_in > 0


def test_propeller_unknown_raises_keyerror():
    with pytest.raises(KeyError, match="helice_ficticia"):
        _LIB.get_propeller("helice_ficticia")


def test_has_propeller():
    assert _LIB.has_propeller("gemfan_5030") is True
    assert _LIB.has_propeller("no_existe_xyz") is False


def test_find_propellers_by_diameter():
    results = _LIB.find_propellers(diameter_in=10.0, tolerance=1.0)
    names = [p.name for p in results]
    assert "apc_10x4_5" in names
    assert all(abs(p.diameter_in - 10.0) <= 1.0 for p in results)


def test_propeller_missing_required_field_raises(tmp_path: Path):
    (tmp_path / "motores").mkdir()
    (tmp_path / "materiales").mkdir()
    (tmp_path / "baterias").mkdir()
    (tmp_path / "helices").mkdir()
    for name in ("motores", "materiales", "baterias"):
        (tmp_path / name / "_datos.json").write_text("{}", encoding="utf-8")
    (tmp_path / "helices" / "_datos.json").write_text(
        '{"broken": {"diameter_in": 10.0}}', encoding="utf-8"
    )
    lib = ComponentLibrary(library_root=tmp_path)
    with pytest.raises(ValueError, match="pitch_in"):
        lib.list_propellers()


# ── 5b. ESCs load; get_esc by id; verified HOBBYWING seed ───────────────────

def test_escs_load_and_get_by_id():
    spec = _LIB.get_esc("hobbywing_xrotor_40a_6s")
    assert isinstance(spec, EscSpec)
    _assert_esc_hobbywing(spec)


def _assert_esc_hobbywing(spec: EscSpec) -> None:
    assert spec.identity_status == "verified"
    assert spec.manufacturer == "HOBBYWING"
    assert spec.model == "XRotor 40A 6S BLDC"
    assert spec.part_number == "30901001"
    assert spec.esc_topology == "individual"
    assert spec.channels == 1
    assert spec.continuous_current_a == pytest.approx(40.0)
    assert spec.burst_current_a == pytest.approx(60.0)
    assert spec.continuous_current_source == "manufacturer_spec"
    assert spec.cells_min == 2
    assert spec.cells_max == 6
    assert spec.mass_g == pytest.approx(26.0)


def test_has_esc():
    assert _LIB.has_esc("hobbywing_xrotor_40a_6s") is True
    assert _LIB.has_esc("no_existe_xyz") is False


def test_esc_missing_required_field_raises(tmp_path: Path):
    (tmp_path / "motores").mkdir()
    (tmp_path / "materiales").mkdir()
    (tmp_path / "baterias").mkdir()
    (tmp_path / "helices").mkdir()
    (tmp_path / "esc").mkdir()
    for name in ("motores", "materiales", "baterias", "helices"):
        (tmp_path / name / "_datos.json").write_text("{}", encoding="utf-8")
    (tmp_path / "esc" / "_datos.json").write_text(
        '{"broken": {"burst_current_a": 60}}', encoding="utf-8"
    )
    lib = ComponentLibrary(library_root=tmp_path)
    with pytest.raises(ValueError, match="continuous_current_a"):
        lib.list_escs()


def test_bind_esc_from_catalog_projects_continuous_current():
    from jarvis.core.catalog_bind import bind_esc_from_catalog

    spec = bind_esc_from_catalog("hobbywing_xrotor_40a_6s")
    assert spec.catalog_ref == CatalogRef(family="esc", sku="hobbywing_xrotor_40a_6s")
    assert spec.suggested_key == "esc"
    assert spec.properties["current_a"].value == pytest.approx(40.0)
    assert spec.properties["mass_g"].value == pytest.approx(26.0)


# ── 6. Unknown SKU → not-found deterministic (cross-family, no fabrication) ─

def test_unknown_sku_never_fabricated():
    assert _LIB.has_motor("phantom_motor_9000") is False
    assert _LIB.has_battery("phantom_battery_9000") is False
    assert _LIB.has_propeller("phantom_prop_9000") is False
    assert _LIB.has_esc("phantom_esc_9000") is False
    with pytest.raises(KeyError):
        _LIB.get_motor("phantom_motor_9000")
    with pytest.raises(KeyError):
        _LIB.get_battery("phantom_battery_9000")
    with pytest.raises(KeyError):
        _LIB.get_propeller("phantom_prop_9000")
    with pytest.raises(KeyError):
        _LIB.get_esc("phantom_esc_9000")


# ── 7. match_motor_propeller — explicit + fallback + honest False ──────────

def test_match_motor_propeller_diameter_fallback_true():
    # sunnysky_x2216_11.compatible_prop_inch == (10, 11); apc_10x4_5 diameter 10"
    assert _LIB.match_motor_propeller("sunnysky_x2216_11", "apc_10x4_5") is True


def test_match_motor_propeller_diameter_fallback_false_not_fabricated():
    # sunnysky_x2216_11 wants 10-11"; tmotor_22x6_7 is 22" — no match, no invented True
    assert _LIB.match_motor_propeller("sunnysky_x2216_11", "tmotor_22x6_7") is False


def test_match_motor_propeller_explicit_compatible_prop_ids(tmp_path: Path):
    (tmp_path / "motores").mkdir()
    (tmp_path / "materiales").mkdir()
    (tmp_path / "baterias").mkdir()
    (tmp_path / "helices").mkdir()
    (tmp_path / "motores" / "_datos.json").write_text(
        """{
          "explicit_motor": {
            "thrust_n": 10.0, "kv_rating": 900, "weight_g": 60, "max_watts": 250,
            "compatible_prop_inch": [99],
            "compatible_prop_ids": ["exact_prop"]
          }
        }""",
        encoding="utf-8",
    )
    (tmp_path / "helices" / "_datos.json").write_text(
        """{
          "exact_prop": {"diameter_in": 5.0, "pitch_in": 3.0},
          "other_prop": {"diameter_in": 5.0, "pitch_in": 3.0}
        }""",
        encoding="utf-8",
    )
    (tmp_path / "materiales" / "_datos.json").write_text("{}", encoding="utf-8")
    (tmp_path / "baterias" / "_datos.json").write_text("{}", encoding="utf-8")
    lib = ComponentLibrary(library_root=tmp_path)
    # Explicit id list wins even though compatible_prop_inch (99") would not match.
    assert lib.match_motor_propeller("explicit_motor", "exact_prop") is True
    # Same diameter/pitch, different id, not in the explicit list — no fabrication.
    assert lib.match_motor_propeller("explicit_motor", "other_prop") is False


# ── 8. ComponentSpec.catalog_ref round-trip (unit only, no production path) ─

def test_component_spec_catalog_ref_defaults_none():
    spec = ComponentSpec(name="motors", component_type="propulsion_active")
    assert spec.catalog_ref is None


def test_component_spec_catalog_ref_round_trip():
    spec = ComponentSpec(
        name="motors",
        component_type="propulsion_active",
        catalog_ref=CatalogRef(family="motor", sku="sunnysky_x2216_11"),
    )
    dumped = spec.model_dump()
    assert dumped["catalog_ref"] == {"family": "motor", "sku": "sunnysky_x2216_11"}
    restored = ComponentSpec.model_validate(dumped)
    assert restored.catalog_ref == CatalogRef(family="motor", sku="sunnysky_x2216_11")


# ── 9. Single JSON reader guard ─────────────────────────────────────────────

def test_single_json_reader_guard():
    """No file other than knowledge/library.py may construct a *_datos.json path.

    Matches the actual path-join idiom library.py uses (``self._root / "x" /
    "_datos.json"``) rather than a bare substring search, so prose mentions in
    docstrings/error messages (e.g. "revisa library/materiales/_datos.json")
    don't produce false positives.
    """
    import re

    _PATH_JOIN_RE = re.compile(r"""/\s*["']_datos\.json["']""")
    src_root = Path(__file__).resolve().parent.parent / "src" / "jarvis"
    offenders = []
    for path in src_root.rglob("*.py"):
        if path.name == "library.py" and path.parent.name == "knowledge":
            continue
        if _PATH_JOIN_RE.search(path.read_text(encoding="utf-8")):
            offenders.append(str(path.relative_to(src_root)))
    assert offenders == [], f"Second JSON reader found outside knowledge/library.py: {offenders}"
