"""Shared Neo4j (Community) id-uniqueness constraint emission.

Both the constraint generator (src/generate_constraints.py) and the catalog
projector (pilot/project_to_cypher.py) emit `n.id IS UNIQUE` per entity class.
Keeping a single builder here guarantees identical constraint NAMES and text
across the two outputs — previously they diverged (generator used
`ct_cutting_recommendation_id`, projector used `ct_cuttingrecommendation_id`).
"""
import re


def constraint_name(cls: str) -> str:
    return 'ct_' + re.sub(r'(?<!^)(?=[A-Z])', '_', cls).lower() + '_id'


def community_constraints(classes: list[str]) -> list[str]:
    return [
        f"CREATE CONSTRAINT {constraint_name(cls)} IF NOT EXISTS "
        f"FOR (n:{cls}) REQUIRE n.id IS UNIQUE;"
        for cls in classes
    ]