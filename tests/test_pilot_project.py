"""Projector determinism + mapping alignment."""
import json
from pathlib import Path

import pytest
import yaml

from pilot.project_to_cypher import project_to_cypher
from pilot.validate_catalog import load_mapping

ROOT = Path(__file__).resolve().parents[1]


def test_output_is_deterministic_and_well_formed():
    reg, mapping = load_mapping()
    data = json.loads((ROOT / "pilot" / "toy-catalog.json").read_text(encoding="utf-8"))
    c1 = project_to_cypher(data, reg, mapping)
    c2 = project_to_cypher(data, reg, mapping)
    assert c1 == c2  # deterministic
    assert "CREATE CONSTRAINT" in c1  # emit id-uniqueness constraints
    assert "IN_SERIES" in c1          # relationship type from mapping
    assert ":Insert" in c1 or ":Tool" in c1
    # every relationship name present must map to a real type
    mapping_rels = yaml.safe_load((ROOT / "mappings/ontology-neo4j.yaml").read_text("utf-8"))["relationships"]
    for rel in data["relationships"]:
        rel_upper = mapping_rels[rel["name"]]
        assert rel_upper in c1


def test_bad_fixture_raises_on_unknown_relation():
    reg, mapping = load_mapping()
    bad = json.loads((ROOT / "pilot" / "toy-catalog-bad.json").read_text(encoding="utf-8"))
    bad["relationships"].append({"source_type": "Tool", "source_id": "x",
                                 "name": "NOT_A_REL", "target_type": "ToolType", "target_id": "y"})
    with pytest.raises(KeyError):
        project_to_cypher(bad, reg, mapping)


def test_unmapped_entity_field_is_a_hard_error():
    reg, mapping = load_mapping()
    data = json.loads((ROOT / "pilot" / "toy-catalog.json").read_text(encoding="utf-8"))
    data["entities"].append({"type": "Manufacturer", "id": "M-X", "name": "x",
                             "not_in_mapping": 1})
    with pytest.raises(KeyError):
        project_to_cypher(data, reg, mapping)