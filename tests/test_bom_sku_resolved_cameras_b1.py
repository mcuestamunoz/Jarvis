"""B1-bom-sku-resolved-cameras — display-only sku_resolved for cameras/FC/sensors.

Bound Phoenix 2 must show ``[runcam_phoenix_2]``, not ``(SKU sin resolver)``.
"""

from __future__ import annotations

from types import SimpleNamespace

from jarvis.core.catalog_bind import bind_camera_from_catalog
from jarvis.core.project_closure import (
    _bom_identity_suffix,
    _bom_sku_resolved,
    build_component_bom,
    format_bom_lines,
)
from jarvis.schemas.action_schema import ComponentSpec


def _state_with_cameras(spec: ComponentSpec):
    return SimpleNamespace(
        parsed_constraints={},
        latest_results={},
        current_parameters={},
        design_properties=SimpleNamespace(
            components={"cameras": spec},
            system_blocks=["perception"],
            system_defined=True,
            system_priority=["perception"],
        ),
    )


def test_t1_bound_phoenix_sku_resolved_true():
    assert _bom_sku_resolved({"family": "cameras", "sku": "runcam_phoenix_2"}) is True


def test_t2_bom_suffix_shows_bracket_sku_not_sin_resolver():
    """B1-catalog-camera-power-w (2026-09-18) note: a fresh Phoenix 2 bind
    now carries a catalog-cited ``power_w`` — which is in project_closure's
    own ``_MEASURABLE`` set — so ``classify_component`` promotes it from
    ``"declared"`` to ``"defined"`` (completeness=high + measurable + no
    missing_fields = a strict close). This test's own concern (the SKU
    suffix formatting) is bucket-independent, so it looks the entry up
    across every bucket rather than assuming ``"declarative"``."""
    bound = bind_camera_from_catalog("runcam_phoenix_2")
    bom = build_component_bom(_state_with_cameras(bound))
    cameras = next(
        e for e in bom["defined"] + bom["declarative"] + bom["incomplete"]
        if e["key"] == "cameras"
    )
    assert cameras["sku_resolved"] is True
    assert cameras["catalog_ref"]["sku"] == "runcam_phoenix_2"
    suffix = _bom_identity_suffix(cameras)
    assert suffix == " [runcam_phoenix_2]"
    assert "SKU sin resolver" not in suffix
    lines = format_bom_lines(bom)
    camera_line = next(ln for ln in lines if "runcam_phoenix_2" in ln)
    assert "SKU sin resolver" not in camera_line
    assert "[runcam_phoenix_2]" in camera_line


def test_t3_unknown_camera_sku_unresolved():
    assert _bom_sku_resolved({"family": "cameras", "sku": "phantom_cam_9000"}) is False
    entry = {
        "catalog_ref": {"family": "cameras", "sku": "phantom_cam_9000"},
        "sku_resolved": False,
    }
    assert _bom_identity_suffix(entry) == " (SKU sin resolver)"


def test_t4_no_catalog_ref_no_sku_suffix():
    free = ComponentSpec(
        name="cámara RunCam",
        component_type="perception",
        suggested_key="cameras",
        completeness="medium",
        source="declared",
        properties={},
        catalog_ref=None,
    )
    bom = build_component_bom(_state_with_cameras(free))
    cameras = next(e for e in bom["declarative"] if e["key"] == "cameras")
    assert cameras["catalog_ref"] is None
    assert cameras["sku_resolved"] is False
    assert _bom_identity_suffix(cameras) == ""


def test_t5_fc_and_sensors_resolve_when_live():
    assert _bom_sku_resolved(
        {"family": "flight_controller", "sku": "speedybee_f405_v4"}
    ) is True
    assert _bom_sku_resolved(
        {"family": "sensors", "sku": "holybro_m10"}
    ) is True
    assert _bom_sku_resolved(
        {"family": "flight_controller", "sku": "missing_fc"}
    ) is False
    assert _bom_sku_resolved(
        {"family": "motor", "sku": "iflight_xing_e_pro_2207_2450"}
    ) is True


def test_t5_package_checkpoint():
    from pathlib import Path

    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.4.3"' in text
