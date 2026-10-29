"""Document-anchored identifiers: cleaned into a contract-valid, projectable catalog."""
import json
from pathlib import Path

from pilot.validate_catalog import validate_catalog, load_mapping
from pilot.project_to_cypher import project_to_cypher

import pytest
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]

URI = "bolt://localhost:7689"
AUTH = ("neo4j", "pilotsecret")


@pytest.fixture(scope="module")
def driver():
    try:
        d = GraphDatabase.driver(URI, auth=AUTH)
        d.verify_connectivity()
    except Exception:
        pytest.skip("Neo4j not reachable; online ingestion test skipped")
        return None
    yield d
    d.close()


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


def test_sample_loads_into_neo4j(driver):
    data = _load()
    ids = [e["id"] for e in data["entities"]]
    reg, mapping = load_mapping()
    cypher = project_to_cypher(data, reg, mapping)  # CREATE CONSTRAINT IF NOT EXISTS + MERGE
    with driver.session() as s:
        # Self-contained / idempotent: drop this sample's own ids first, so the load
        # is clean regardless of leftover or foreign nodes that share an id prefix.
        s.run("UNWIND $ids AS id MATCH (n {id: id}) DETACH DELETE n", ids=ids)
        for stmt in [x for x in cypher.split(";") if x.strip()]:
            s.run(stmt)
    with driver.session() as s:
        n = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        r = s.run("MATCH ()-[e]->() RETURN count(e) AS c").single()["c"]
    # 11 entities (incl. provenance) + 3 relationships, idempotently (MERGE), no growth.
    assert n >= 11 and r >= 3
    # re-load must not grow the graph (MERGE is idempotent)
    with driver.session() as s:
        for stmt in [x for x in cypher.split(";") if x.strip()]:
            s.run(stmt)
    with driver.session() as s:
        n2 = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        r2 = s.run("MATCH ()-[e]->() RETURN count(e) AS c").single()["c"]
    assert n2 == n and r2 == r