"""Pilot catalog validator: entity + relationship-level checks."""
import json
from pathlib import Path

from pilot.validate_catalog import validate_catalog

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str) -> dict:
    return json.loads((ROOT / "pilot" / name).read_text(encoding="utf-8"))


def test_positive_fixture_fully_valid():
    ok, errors = validate_catalog(_load("toy-catalog.json"))
    assert ok, f"positive fixture must validate: {errors}"


def test_bad_fixture_rejected():
    ok, errors = validate_catalog(_load("toy-catalog-bad.json"))
    assert not ok
    msg = "\n".join(errors)
    assert "does-not-exist" in msg or "not a concept" in msg          # dangling ref
    assert "process" in msg                                            # cross-scheme ref
    assert "NO-SUCH-ID" in msg                                         # dangling relation source