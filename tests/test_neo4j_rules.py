"""Rule definitions mirror the four relationship-level SHACL rules in
shapes/relation-shapes.ttl, expressed as violation-detecting Cypher."""
from neo4j import GraphDatabase
import pytest

from pilot.neo4j_rules import RULES


def test_five_rules_defined_matching_shacl():
    assert len(RULES) == 5
    ids = {r["id"] for r in RULES}
    assert ids == {"R1_evidence", "R2_vc_range", "R3_mounting", "R4_feed_unit", "R5_concept_ref"}


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


def test_r5_uses_vocab_base_not_raw_literal():
    from pilot.neo4j_rules import R5_CONCEPT_REF
    from src.namespaces import VOCAB_BASE
    assert VOCAB_BASE in R5_CONCEPT_REF
    remaining = R5_CONCEPT_REF.replace(VOCAB_BASE, "")
    assert "example.org/cutting-tool/vocabulary/" not in remaining


def test_r5_covers_every_bound_class():
    from pilot.neo4j_rules import _VOCAB_BOUND
    assert _VOCAB_BOUND == ("ToolType", "ProcessMethod", "MaterialClass")


def test_r4_feed_units_are_single_source_with_validator():
    from pilot.neo4j_rules import R4_FEED_UNIT, _R4_OR
    from src.feed_units import FEED_UNITS
    assert _R4_OR
    for ft, fu in FEED_UNITS.items():
        clause = f"(p.feedType = '{ft}' AND p.feedUnit <> '{fu}')"
        assert clause in R4_FEED_UNIT
    assert FEED_UNITS == {'fn': 'mm/rev', 'fz': 'mm/tooth', 'vf': 'mm/min'}


def test_offline_validator_and_online_r4_share_the_table():
    from src.validator import _FEED_UNITS
    from src.feed_units import FEED_UNITS
    assert _FEED_UNITS == FEED_UNITS


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
        # R2: vcRecommended outside [vcMin, vcMax]
        s.run("MERGE (p:CuttingParam {id:'BAD-VC', name:'n', vcRecommended: 900, vcMin: 100, vcMax: 200})")
        # R3: an Insert FITS_WITH a Holder but no matched InsertSpecification
        s.run("MERGE (i:Insert {id:'BAD-FIT', name:'i'}) "
              "MERGE (h:Holder {id:'BAD-HOLDER', name:'h'}) "
              "MERGE (i)-[:FITS_WITH]->(h)")
        # R5: a bound class node with a dangling / absent conceptRef
        s.run("MERGE (n:ToolType {id:'BAD-REF', name:'n', conceptRef:'http://garbage/not-vocab'})")
    rules = _rules_by_id()
    r1 = {h["id"] for h in _eval_from(driver, rules["R1_evidence"])}
    r4 = {h["id"] for h in _eval_from(driver, rules["R4_feed_unit"])}
    r2 = {h["id"] for h in _eval_from(driver, rules["R2_vc_range"])}
    r3 = {h["id"] for h in _eval_from(driver, rules["R3_mounting"])}
    r5 = {h["id"] for h in _eval_from(driver, rules["R5_concept_ref"])}
    assert "BAD-NO-EVIDENCE" in r1
    assert "BAD-FEED" in r4
    assert "BAD-VC" in r2
    assert "BAD-FIT" in r3
    assert "BAD-REF" in r5
    # cleanup so the graph stays clean for the other test and later runs
    with driver.session() as s:
        s.run("MATCH (n {id:'BAD-NO-EVIDENCE'}) DETACH DELETE n")
        s.run("MATCH (n {id:'BAD-FEED'}) DETACH DELETE n")
        s.run("MATCH (n {id:'BAD-VC'}) DETACH DELETE n")
        s.run("MATCH (n {id:'BAD-FIT'}) DETACH DELETE n")
        s.run("MATCH (n {id:'BAD-HOLDER'}) DETACH DELETE n")
        s.run("MATCH (n {id:'BAD-REF'}) DETACH DELETE n")


def test_injected_violations_cleanup_restores_pass(driver):
    """After test_injected_violations_are_detected cleans up, clean graph passes again."""
    for rid, cypher in _rules_by_id().items():
        assert _eval_from(driver, cypher) == [], f"{rid} still violated after cleanup"