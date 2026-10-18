"""Tests T1-T4 for `B1-connect-plugs-real-data-map` (T33).

Docs-only Buy — no `src/` behavior change. Verifies the living SoT map
(`.jes/artifacts/engineer_note_connect_plugs_real_data_map.md`) exists,
carries the required A/B/C/D taxonomy legend and at least one markdown
table, and contains every seed `id` from the IC's §0b seed inventory
(extended ids this Buy's forensic pass added are a bonus, not required
here — this test locks the seed, not every extension).
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = REPO_ROOT / ".jes" / "artifacts" / "engineer_note_connect_plugs_real_data_map.md"

# IC §0b seed inventory — every id Cursor's forensic seed listed.
SEED_IDS = (
    "sd-go-to",
    "sim-tick-takeoff",
    "sim-tick-return-home",
    "sim-tick-follow",
    "sim-tick-patrol",
    "takeoff-altitude-params",
    "follow-target-params",
    "patrol-route-params",
    "sim-autonomy-z-m",
    "flight-caps-not-implemented",
    "ops-charge-not-implemented",
    "c4-execution-never-executed",
    "arm-latch-not-esc",
    "voice-intent-ingress",
    "radio-intent-live",
    "api-intent-ingress",
    "copper-esc-live-flight",
    "esc-gpio-sink",
    "dshot-wire",
    "gyro-spi1-live",
    "mcu-usart-on-chip",
    "c30-desk-dfu",
    "linux-crsf-baud",
    "live-elrs",
    "sim-sensor-hals",
    "hd-001",
    "hd-002",
    "hd-003",
    "hd-004",
    "hd-005",
    "a4-voice-world",
    "world-package",
    "go-to-metadata-plug-for-world",
)


def test_t1_sot_file_exists():
    assert MAP_PATH.exists(), f"missing SoT map: {MAP_PATH}"


def test_t2_taxonomy_legend_and_markdown_table_present():
    text = MAP_PATH.read_text(encoding="utf-8")
    for letter in ("A", "B", "C", "D"):
        assert f"**{letter}**" in text, f"taxonomy legend missing type {letter}"
    assert "| id | type | deferred | seam_today | connect_later | status | evidence |" in text


def test_t3_every_seed_id_present():
    text = MAP_PATH.read_text(encoding="utf-8")
    missing = [seed_id for seed_id in SEED_IDS if f"`{seed_id}`" not in text]
    assert not missing, f"seed ids missing from the map: {missing}"


def test_t4_no_tip_version_pins_in_suite():
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()
