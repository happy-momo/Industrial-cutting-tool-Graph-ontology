"""Rule definitions mirror the four relationship-level SHACL rules in
shapes/relation-shapes.ttl, expressed as violation-detecting Cypher."""
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