"""Document-anchored identifiers: cleaned into a contract-valid, projectable catalog."""
import json
from pathlib import Path

from pilot.validate_catalog import validate_catalog, load_mapping
from pilot.project_to_cypher import project_to_cypher

ROOT = Path(__file__).resolve().parents[1]


def _load():
    return json.loads((ROOT / "examples" / "document-anchored-tool-identifiers.json").read_text("utf-8"))


def test_sample_is_contract_valid():
    ok, errors = validate_catalog(_load())
    assert ok, f"sample must validate: {errors}"


def test_sample_has_provenance_chain():
    rels = {r["name"] for r in _load().get("relationships", [])}
    assert {"forTool", "supportedBy", "fromDocument"} <= rels


def test_sample_projects_deterministically():
    reg, mapping = load_mapping()
    data = _load()
    c1 = project_to_cypher(data, reg, mapping)
    c2 = project_to_cypher(data, reg, mapping)
    assert c1 == c2
    assert "CREATE CONSTRAINT" in c1
    assert ":SourceDocument" in c1 and ":Insert" in c1 and ":CuttingRecommendation" in c1