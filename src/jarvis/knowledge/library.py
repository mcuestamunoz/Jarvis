"""
jarvis.knowledge.library
========================
Deterministic access to the component/material library stored under
library/.

This module is the ONLY place that reads _datos.json files.
All callers (mutation_engine, iterate_interactive_session, create_project)
must use ComponentLibrary – never read JSON directly.
"""
from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

# Root of the knowledge base relative to this file:
# src/jarvis/knowledge/ → ../../../../library/
_LIBRARY_ROOT = Path(__file__).resolve().parent.parent.parent.parent / "library"


def _normalize_name(name: str) -> str:
    """Lowercase and strip diacritics so 'plastico' matches 'plástico'."""
    nfd = unicodedata.normalize("NFD", name.strip().lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


@dataclass(frozen=True)
class MaterialSpec:
    name: str
    density_kg_m3: float


@dataclass(frozen=True)
class MotorSpec:
    name: str
    thrust_n: float
    kv_rating: int
    weight_g: float
    max_watts: float
    compatible_prop_inch: tuple[int, ...]


class ComponentLibrary:
    """Read-only access to the physical component/material database."""

    def __init__(self, library_root: Path | None = None) -> None:
        self._root = library_root or _LIBRARY_ROOT
        self._materials: dict[str, MaterialSpec] | None = None
        self._motors: dict[str, MotorSpec] | None = None

    # ── Materials ────────────────────────────────────────────────────────────

    def _load_materials(self) -> dict[str, MaterialSpec]:
        if self._materials is not None:
            return self._materials
        path = self._root / "materiales" / "_datos.json"
        if not path.exists():
            raise FileNotFoundError(
                f"Biblioteca de materiales no encontrada: {path}"
            )
        raw: dict[str, dict] = json.loads(path.read_text(encoding="utf-8"))
        self._materials = {
            _normalize_name(name): MaterialSpec(name=name, density_kg_m3=float(data["density_kg_m3"]))
            for name, data in raw.items()
        }
        return self._materials

    def get_material(self, name: str) -> MaterialSpec:
        """Return MaterialSpec for *name*.

        Raises KeyError with a clear message if the material is not in the
        library.  Callers that require graceful degradation should catch
        KeyError and show a user-friendly message.
        """
        canonical = _normalize_name(name)
        materials = self._load_materials()
        if canonical not in materials:
            available = ", ".join(sorted(materials))
            raise KeyError(
                f"Material '{name}' no está en la biblioteca. "
                f"Disponibles: {available}"
            )
        return materials[canonical]

    def list_materials(self) -> list[MaterialSpec]:
        """Return all known materials sorted by name."""
        return sorted(self._load_materials().values(), key=lambda m: m.name)

    def has_material(self, name: str) -> bool:
        """Return True if *name* is in the library (no exception)."""
        try:
            self.get_material(name)
            return True
        except KeyError:
            return False

    # ── Motors ─────────────────────────────────────────────────────────────

    def _load_motors(self) -> dict[str, MotorSpec]:
        if self._motors is not None:
            return self._motors
        path = self._root / "motores" / "_datos.json"
        if not path.exists():
            raise FileNotFoundError(f"Biblioteca de motores no encontrada: {path}")
        raw: dict[str, dict] = json.loads(path.read_text(encoding="utf-8"))
        self._motors = {
            _normalize_name(name): MotorSpec(
                name=name,
                thrust_n=float(data["thrust_n"]),
                kv_rating=int(data["kv_rating"]),
                weight_g=float(data["weight_g"]),
                max_watts=float(data["max_watts"]),
                compatible_prop_inch=tuple(data["compatible_prop_inch"]),
            )
            for name, data in raw.items()
        }
        return self._motors

    def get_motor(self, name: str) -> MotorSpec:
        """Return exact motor by name. KeyError if not found."""
        canonical = _normalize_name(name)
        motors = self._load_motors()
        if canonical not in motors:
            available = ", ".join(sorted(motors))
            raise KeyError(
                f"Motor '{name}' no está en la biblioteca. Disponibles: {available}"
            )
        return motors[canonical]

    def list_motors(self) -> list[MotorSpec]:
        """Return all motors sorted by name."""
        return sorted(self._load_motors().values(), key=lambda m: m.name)

    def find_motors_by_kv(self, kv: int, tolerance: int = 150) -> list[MotorSpec]:
        """Return motors whose kv_rating is within *tolerance* of *kv*.

        IMPORTANT: for suggestion-only — never auto-apply thrust from this result.
        """
        return [
            m for m in self._load_motors().values()
            if abs(m.kv_rating - kv) <= tolerance
        ]

    def has_motor(self, name: str) -> bool:
        """Return True if *name* is in the motor library (no exception)."""
        try:
            self.get_motor(name)
            return True
        except KeyError:
            return False


# Shared singleton — safe for single-process use (tests override via constructor)
default_library = ComponentLibrary()
