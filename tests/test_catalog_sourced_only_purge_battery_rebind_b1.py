"""Catalog sourced-only purge + battery rebind P0.

implementation_contract_catalog_sourced_only_purge_battery_rebind_b1.md

★1-★2: every buyable product seed (baterias/motores/helices/frames/esc/
kit_hardware) keeps only rows with a real, non-empty source_url — a
guardrail so the catalog can never silently re-grow an anonymous/unsourced
row. library/materiales is explicitly out of scope (★3 — material types,
not buyable SKUs).

★4/Bat-list/Bat-sku/Bat-help: after the purge, the battery assist lists
ALL remaining batteries (no hard limit that could truncate again), and a
"cambiar bateria" REBIND session (battery already catalog-bound) accepts
both a free-text SKU (even embedded in a sentence) and a bare "ayúdame a
elegir" re-offer — both landed as real bugs during this cycle's own
implementation, fixed in component_writers.py/orchestrator.py, verified
here.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.battery_catalog_assist import build_battery_catalog_suggestions
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.knowledge.library import ComponentLibrary, default_library
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, PropertyValue


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


# ── ★1/★2: sourced-only gate ─────────────────────────────────────────────


@pytest.mark.parametrize("family,lister", [
    ("baterias", "list_batteries"),
    ("motores", "list_motors"),
    ("helices", "list_propellers"),
    ("frames", "list_frames"),
    ("esc", "list_escs"),
    ("kit_hardware", "list_kit_hardware"),
])
def test_every_product_seed_row_has_source_url(family, lister):
    """★1/★2 guardrail: no buyable product family may silently re-grow an
    anonymous/unsourced row. library/materiales is deliberately excluded
    (★3 — material types, not buyable SKUs)."""
    rows = getattr(default_library, lister)()
    assert rows, f"{family} catalog is empty — nothing to gate"
    unsourced = [r.name for r in rows if not getattr(r, "source_url", None)]
    assert not unsourced, f"{family} rows with no source_url: {unsourced}"


def test_purged_skus_are_actually_gone():
    """Direct confirmation of the DROP list — never re-seeded under the
    same name (§8 done-when #1)."""
    dropped_batteries = {
        "lipo_2s_850mah", "lipo_3s_1300mah", "lipo_3s_2200mah",
        "lipo_4s_10000mah", "lipo_6s_10000mah", "lipo_6s_22000mah", "lipo_12s_16000mah",
    }
    dropped_motors = {
        "sunnysky_x2216_11", "t-motor_mn3110_700", "emax_rs2205_2300",
        "sunnysky_x2212_980", "t-motor_mn4014_400", "generic_920kv",
        "brotherhobby_avenger_2500", "t-motor_f80_2400", "sunnysky_v4006_740",
        "t-motor_mn5008_340", "emax_eco_ii_2207_1700", "hobbywing_xrotor_2207_2450",
        "t-motor_antigravity_mn4006_380", "sunnysky_r2305_2500", "generic_1500kv",
        "generic_700kv", "t-motor_u8_170", "sunnysky_x2820_900", "emax_mt2216_810",
        "brotherhobby_returner_r5_2700",
    }
    dropped_props = {
        "gemfan_5030", "gemfan_6040", "apc_8x4_5", "apc_10x4_5", "apc_11x5_5",
        "tmotor_12x4", "tmotor_13x4_4", "tmotor_15x5", "tmotor_16x5_4",
        "tmotor_17x5_8", "tmotor_18x6_1", "tmotor_22x6_7", "tmotor_24x7_2",
    }
    battery_names = {b.name for b in default_library.list_batteries()}
    motor_names = {m.name for m in default_library.list_motors()}
    prop_names = {p.name for p in default_library.list_propellers()}
    assert not (dropped_batteries & battery_names)
    assert not (dropped_motors & motor_names)
    assert not (dropped_props & prop_names)


def test_keep_rows_survive_untouched():
    """KEEP rows are unchanged in physics — spot-check a few real numbers."""
    tattu = default_library.get_battery("tattu_2300mah_4s_75c_xt60")
    assert tattu.energy_wh == pytest.approx(34.04)
    assert tattu.cells == 4
    emax = default_library.get_motor("emax_rs2205s_2300")
    assert emax.thrust_n == pytest.approx(10.042)
    assert emax.max_watts is None


def test_materiales_out_of_scope_unaffected():
    """★3: library/materiales is a different taxonomy (material types, not
    buyable SKUs) — this Buy never touches it."""
    materials = default_library.list_materials()
    assert materials, "materiales catalog must be untouched by this Buy"


# ── ★4/Bat-list: no hard truncation ──────────────────────────────────────


def test_battery_list_includes_tattu_and_gens_ace_no_truncation():
    suggestions = build_battery_catalog_suggestions(None)
    names = {s["name"] for s in suggestions}
    assert "tattu_2300mah_4s_75c_xt60" in names
    assert "gens_ace_2200mah_3s_35c_gtech" in names
    # Every remaining KEEP battery appears — no hard limit truncates them.
    assert len(suggestions) == len(default_library.list_batteries())


def test_battery_list_limit_still_overridable():
    """`limit` stays an available override (opt-in narrower slice), just
    no longer a silent default truncation."""
    suggestions = build_battery_catalog_suggestions(None, limit=1)
    assert len(suggestions) == 1


# ── ★4/Bat-sku/Bat-help: rebind session on an already-bound battery ──────


def _rebind_project(tmp_path: Path, *, bound_sku: str = "lipo_4s_5000mah") -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "battery rebind b1",
            "payload_kg": 1.0, "restrictions": "ninguna", "detail_level": "conceptual",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    battery = ComponentSpec(
        suggested_key="battery", completeness="high",
        catalog_ref=CatalogRef(family="battery", sku=bound_sku),
        properties={"battery_capacity_wh": PropertyValue(value=74.0, unit="Wh", confidence=0.9, source="declared")},
    )
    updated_dp = ps.design_properties.model_copy(
        update={"components": {**ps.design_properties.components, "battery": battery}}
    )
    ps = ps.model_copy(update={"design_properties": updated_dp})
    orch.workspace_manager.save_state(ps)
    return orch


def test_cambiar_bateria_lists_all_keep_batteries_including_tattu(tmp_path: Path):
    orch = _rebind_project(tmp_path)
    result = orch.handle_user_text("cambiar bateria", _RefuseLLM())
    names = {s["name"] for s in result.get("battery_suggestions") or []}
    assert "tattu_2300mah_4s_75c_xt60" in names


def test_battery_rebind_free_text_sku_embedded_in_sentence_binds(tmp_path: Path):
    """Bat-sku: a live SKU embedded anywhere in free text (not just a bare/
    near-exact match against the offered list) binds directly."""
    orch = _rebind_project(tmp_path)
    orch.handle_user_text("cambiar bateria", _RefuseLLM())
    result = orch.handle_user_text("quiero la tattu_2300mah_4s_75c_xt60 por favor", _RefuseLLM())
    assert result["status"] == "ok"
    assert "tattu_2300mah_4s_75c_xt60" in result["message"]

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    battery = ps.design_properties.components["battery"]
    assert battery.catalog_ref == CatalogRef(family="battery", sku="tattu_2300mah_4s_75c_xt60")


def test_battery_rebind_bare_sku_binds_without_prior_offer(tmp_path: Path):
    """Bat-sku also fires on the very first turn after "cambiar bateria",
    before any numbered list has even been re-requested."""
    orch = _rebind_project(tmp_path)
    orch.handle_user_text("cambiar bateria", _RefuseLLM())
    result = orch.handle_user_text("tattu_2300mah_4s_75c_xt60", _RefuseLLM())
    assert result["status"] == "ok"

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.design_properties.components["battery"].catalog_ref.sku == "tattu_2300mah_4s_75c_xt60"


def test_battery_rebind_help_choose_reoffers_list_not_generic_brief(tmp_path: Path):
    """Bat-help: G18-style fix — "ayúdame a elegir" after "cambiar bateria"
    (battery already catalog-bound) must re-show the numbered list, never
    loop back to a generic "Vamos a definir la batería..." Brief."""
    orch = _rebind_project(tmp_path)
    orch.handle_user_text("cambiar bateria", _RefuseLLM())
    result = orch.handle_user_text("ayudame a elegir", _RefuseLLM())
    assert result["status"] == "interactive"
    assert "tattu_2300mah_4s_75c_xt60" in result["message"]
    assert "Vamos a definir la batería" not in result["message"]


def test_battery_rebind_help_choose_then_number_pick_binds(tmp_path: Path):
    orch = _rebind_project(tmp_path)
    orch.handle_user_text("cambiar bateria", _RefuseLLM())
    offer = orch.handle_user_text("ayudame a elegir", _RefuseLLM())
    idx = next(
        s["idx"] for s in offer["battery_suggestions"]
        if s["name"] == "tattu_2300mah_4s_75c_xt60"
    )
    pick = orch.handle_user_text(str(idx), _RefuseLLM())
    assert pick["status"] == "ok"

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.design_properties.components["battery"].catalog_ref.sku == "tattu_2300mah_4s_75c_xt60"


def test_battery_rebind_never_writes_without_explicit_pick(tmp_path: Path):
    """Suggest-only discipline: merely opening the list must never mutate
    the on-disk catalog_ref."""
    orch = _rebind_project(tmp_path)
    orch.handle_user_text("cambiar bateria", _RefuseLLM())
    orch.handle_user_text("ayudame a elegir", _RefuseLLM())

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.design_properties.components["battery"].catalog_ref.sku == "lipo_4s_5000mah"
