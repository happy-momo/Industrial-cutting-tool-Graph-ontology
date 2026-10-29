"""Relationship-level graph rules, the online (Neo4j) mirror of the offline SHACL
rules in shapes/relation-shapes.ttl. Each rule is an "violation-detection" query:
an empty result means the invariant holds.

Property / relationship names below use the projected naming from
mappings/ontology-neo4j.yaml (owl_properties camelCase; relationships->UPPER).
"""
from __future__ import annotations

from src.namespaces import VOCAB_BASE

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
# feed_type and feed_unit must describe the same feed semantics. The OR-chain is
# derived from the single-source pairing table so the offline validator and the
# online rule can never drift apart.
from src.feed_units import FEED_UNITS

_R4_OR = " OR\n".join(
    f"(p.feedType = '{ft}' AND p.feedUnit <> '{fu}')" for ft, fu in FEED_UNITS.items()
)
R4_FEED_UNIT = f"""
MATCH (p:CuttingParam)
WHERE {_R4_OR}
RETURN p.id AS id
"""

# R5 — node-level mirror of the vocabulary-binding invariant: every
# controlled class node must carry a conceptRef rooted at the project vocab base.
_VOCAB_BOUND = ("ToolType", "ProcessMethod", "MaterialClass")
R5_CONCEPT_REF = (
    "MATCH (n:" + "|".join(_VOCAB_BOUND) + ") "
    f"WHERE n.conceptRef IS NULL OR NOT n.conceptRef STARTS WITH '{VOCAB_BASE}' "
    "RETURN n.id AS id"
)

RULES: list[dict] = [
    {"id": "R1_evidence", "name": "recommendation needs supporting evidence",
     "shacl_ref": "RecommendationEvidenceShape", "cypher": R1_EVIDENCE},
    {"id": "R2_vc_range", "name": "recommended speed within [vcMin, vcMax]",
     "shacl_ref": "VcRecommendedRangeShape", "cypher": R2_VC_RANGE},
    {"id": "R3_mounting", "name": "insert fit requires a matched specification",
     "shacl_ref": "InsertFitsSpecShape", "cypher": R3_MOUNTING},
    {"id": "R4_feed_unit", "name": "feed_type and feed_unit agreement",
     "shacl_ref": "FeedUnitShape", "cypher": R4_FEED_UNIT},
    {"id": "R5_concept_ref", "name": "controlled-class concept must anchor in the vocabulary",
     "shacl_ref": "VocabularyBindingShape", "cypher": R5_CONCEPT_REF},
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