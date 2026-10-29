"""The catalog projector and the constraint generator must agree on every
id-uniqueness constraint (name AND class). A divergence = drift that would bite
at load time when one side's constraint name stops matching the other's intent."""
import json
import re
from pathlib import Path

from pilot.project_to_cypher import project_to_cypher
from pilot.validate_catalog import load_mapping

ROOT = Path(__file__).resolve().parents[1]
_RE = re.compile(r"CREATE CONSTRAINT (\S+) IF NOT EXISTS FOR \(n:([A-Za-z]+)\) REQUIRE n\.id IS UNIQUE;")


def _constraints_from(cypher: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in _RE.finditer(cypher)}


def test_projected_constraints_subset_of_written_file():
    reg, mapping = load_mapping()
    data = json.loads((ROOT / "pilot" / "toy-catalog.json").read_text("utf-8"))
    projected = _constraints_from(project_to_cypher(data, reg, mapping))
    written = _constraints_from((ROOT / "neo4j/community-constraints.cypher").read_text("utf-8"))
    assert set(projected.items()) <= set(written.items())


def test_projected_skips_recommendation_record_only():
    reg, mapping = load_mapping()
    data = json.loads((ROOT / "pilot" / "toy-catalog.json").read_text("utf-8"))
    projected = _constraints_from(project_to_cypher(data, reg, mapping))
    # RecommendationRecord is an aggregate view, not a graph entity -> no constraint
    assert "RecommendationRecord" not in projected.values()
    # ...but every real entity class is still covered (not skipped-all)
    assert "CuttingRecommendation" in projected.values()


def test_multiword_constraint_name_is_snake():
    reg, mapping = load_mapping()
    data = json.loads((ROOT / "pilot" / "toy-catalog.json").read_text("utf-8"))
    projected = _constraints_from(project_to_cypher(data, reg, mapping))
    assert projected["ct_cutting_recommendation_id"] == "CuttingRecommendation"