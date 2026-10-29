"""Relationship-level graph rules, the online (Neo4j) mirror of the offline SHACL
rules in shapes/relation-shapes.ttl. Each rule is an "violation-detection" query:
an empty result means the invariant holds.

Property / relationship names below use the projected naming from
mappings/ontology-neo4j.yaml (owl_properties camelCase; relationships->UPPER).
"""
from __future__ import annotations

# R1 — evidence traceability (shapes/relation-shapes.ttl RecommendationEvidenceShape):
# every CuttingRecommendation must be linked to at least one SourceEvidence.
R1_EVIDENCE = """
MATCH (r:CuttingRecommendation)
WHERE NOT EXISTS { MATCH (r)-[:SUPPORTED_BY]->(:SourceEvidence) }
RETURN r.id AS id
"""

# R2 — recommended speed in range (shapes/relation-shapes.ttl VcRecommendedRangeShape):
# vcRecommended must lie within [vcMin, vcMax] when all three are present.
R2_VC_RANGE = """
MATCH (p:CuttingParam)
WHERE p.vcRecommended IS NOT NULL AND p.vcMin IS NOT NULL AND p.vcMax IS NOT NULL
  AND (p.vcRecommended < p.vcMin OR p.vcRecommended > p.vcMax)
RETURN p.id AS id
"""

# R3 — mounting contract (shapes/relation-shapes.ttl InsertFitsSpecShape): if an
# Insert fitsWith a Holder, some InsertSpecification must be conformed to by the
# insert AND accepted by that holder. Mirrors targetSubjectsOf ct:fitsWith (no
# fitsWith edge -> nothing to check -> empty result).
R3_MOUNTING = """
MATCH (i:Insert)-[:FITS_WITH]->(h:Holder)
WHERE NOT EXISTS {
    MATCH (i)-[:CONFORMS_TO]->(:InsertSpecification)<-[:ACCEPTS_SPEC]-(h)
}
RETURN i.id AS id, h.id AS holder
"""

# R4 — feed-unit consistency (shapes/relation-shapes.ttl FeedUnitShape):
# feed_type and feed_unit must describe the same feed semantics.
R4_FEED_UNIT = """
MATCH (p:CuttingParam)
WHERE (p.feedType = 'fn' AND p.feedUnit <> 'mm/rev')
   OR (p.feedType = 'fz' AND p.feedUnit <> 'mm/tooth')
   OR (p.feedType = 'vf' AND p.feedUnit <> 'mm/min')
RETURN p.id AS id
"""

RULES: list[dict] = [
    {"id": "R1_evidence", "name": "recommendation needs supporting evidence",
     "shacl_ref": "RecommendationEvidenceShape", "cypher": R1_EVIDENCE},
    {"id": "R2_vc_range", "name": "recommended speed within [vcMin, vcMax]",
     "shacl_ref": "VcRecommendedRangeShape", "cypher": R2_VC_RANGE},
    {"id": "R3_mounting", "name": "insert fit requires a matched specification",
     "shacl_ref": "InsertFitsSpecShape", "cypher": R3_MOUNTING},
    {"id": "R4_feed_unit", "name": "feed_type and feed_unit agreement",
     "shacl_ref": "FeedUnitShape", "cypher": R4_FEED_UNIT},
]


def eval_rule(driver, cypher: str) -> list[dict]:
    """Run a single violation-detection query; return each violation row dict."""
    with driver.session() as s:
        return [dict(r) for r in s.run(cypher)]


def run_rules(driver) -> list[dict]:
    """Run every rule; each result carries id/name/shacl_ref and any violations."""
    return [{**{"id": r["id"], "name": r["name"], "shacl_ref": r["shacl_ref"]},
             "violations": eval_rule(driver, r["cypher"])} for r in RULES]


def all_pass(results: list[dict]) -> bool:
    return all(not r["violations"] for r in results)