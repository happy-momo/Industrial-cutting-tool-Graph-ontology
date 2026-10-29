"""Rule definitions mirror the four relationship-level SHACL rules in
shapes/relation-shapes.ttl, expressed as violation-detecting Cypher."""
from neo4j import GraphDatabase
import pytest

from pilot.neo4j_rules import RULES


def test_four_rules_defined_matching_shacl():
    assert len(RULES) == 4
    ids = {r["id"] for r in RULES}
    assert ids == {"R1_evidence", "R2_vc_range", "R3_mounting", "R4_feed_unit"}


def test_each_rule_is_a_query_with_shacl_trace():
    for r in RULES:
        assert "MATCH" in r["cypher"]          # every rule is a real query
        assert r["shacl_ref"]                  # names the source SHACL rule
        assert r["name"]


def test_rule_property_names_use_projected_naming():
    """R2/R4 must reference camelCase projected properties, not raw JSON field names."""
    from pilot.neo4j_rules import RULES
    by_id = {r["id"]: r["cypher"] for r in RULES}
    assert "vcMin" in by_id["R2_vc_range"] and "vcRecommended" in by_id["R2_vc_range"]
    assert "feedType" in by_id["R4_feed_unit"] and "feedUnit" in by_id["R4_feed_unit"]
    assert "vc_min" not in by_id["R2_vc_range"]  # no raw snake_case names


def test_rule_relationship_types_use_mapping_uppercase():
    """Relationship types must match mappings/ontology-neo4j.yaml (UPPER)."""
    from pilot.neo4j_rules import RULES
    by_id = {r["id"]: r["cypher"] for r in RULES}
    assert "SUPPORTED_BY" in by_id["R1_evidence"]
    assert "FITS_WITH" in by_id["R3_mounting"]
    assert "CONFORMS_TO" in by_id["R3_mounting"] and "ACCEPTS_SPEC" in by_id["R3_mounting"]


# ---------------------------------------------------------------------------
# On-graph integration (requires the running pilot Neo4j at bolt://localhost:7689;
# skipped when the server is not reachable so DB-less CI stays green).
# ---------------------------------------------------------------------------
URI = "bolt://localhost:7689"
AUTH = ("neo4j", "pilotsecret")


@pytest.fixture(scope="module")
def driver():
    try:
        d = GraphDatabase.driver(URI, auth=AUTH)
        d.verify_connectivity()
    except Exception:
        pytest.skip("Neo4j not reachable; online rule tests skipped")
        return None
    yield d
    d.close()


def _eval_from(driver, cypher):
    with driver.session() as s:
        return [dict(x) for x in s.run(cypher)]


def _rules_by_id():
    return {r["id"]: r["cypher"] for r in RULES}


def test_clean_graph_satisfies_all_rules(driver):
    for rid, cypher in _rules_by_id().items():
        assert _eval_from(driver, cypher) == [], f"{rid} violated on clean graph"


def test_injected_violations_are_detected(driver):
    with driver.session() as s:
        # R1: a CuttingRecommendation without any SUPPORTED_BY
        s.run("MERGE (r:CuttingRecommendation {id:'BAD-NO-EVIDENCE', name:'n'})")
        # R4: a CuttingParam with feed_type='fn' but feed_unit='mm/tooth'
        s.run("MERGE (p:CuttingParam {id:'BAD-FEED', name:'n', feedType:'fn', feedUnit:'mm/tooth'})")
    rules = _rules_by_id()
    r1 = {h["id"] for h in _eval_from(driver, rules["R1_evidence"])}
    r4 = {h["id"] for h in _eval_from(driver, rules["R4_feed_unit"])}
    assert "BAD-NO-EVIDENCE" in r1
    assert "BAD-FEED" in r4
    # cleanup so the graph stays clean for the other test and later runs
    with driver.session() as s:
        s.run("MATCH (n {id:'BAD-NO-EVIDENCE'}) DETACH DELETE n")
        s.run("MATCH (n {id:'BAD-FEED'}) DETACH DELETE n")


def test_injected_violations_cleanup_restores_pass(driver):
    """After test_injected_violations_are_detected cleans up, clean graph passes again."""
    for rid, cypher in _rules_by_id().items():
        assert _eval_from(driver, cypher) == [], f"{rid} still violated after cleanup"