"""Project a validated catalog to Neo4j Cypher (nodes + relationships), deterministically.

Emits:
  1. id-uniqueness constraints for every entity class (mirrors neo4j/community-constraints.cypher).
  2. One MERGE per entity, using the mapped multi-label set + scalar properties.
  3. One MATCH/MERGE per relationship, using the mapped relationship type.
All output is sorted by (type, id) / relation key so regeneration is byte-stable.
"""
from __future__ import annotations


def _esc(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'") + "'"


def project_to_cypher(data: dict, reg: dict, mapping: dict) -> str:
    labels = mapping["labels"]            # class -> [label, label, ...]
    rel_types = mapping["relationships"]  # rel name -> RELATION_TYPE
    nm = mapping["owl_properties"]

    out: list[str] = []
    out.append("// constraint on entity id (Neo4j 5+ Community)")
    for cls in sorted(reg["classes"]):
        if cls == "RecommendationRecord":
            continue
        out.append(f"CREATE CONSTRAINT ct_{cls.lower()}_id IF NOT EXISTS FOR (n:{cls}) REQUIRE n.id IS UNIQUE;")

    # --- nodes ---
    for ent in sorted(data["entities"], key=lambda e: (e["type"], e["id"])):
        cls = ent["type"]
        lbl = ":".join(labels.get(cls, [cls]))
        props = {k: v for k, v in ent.items() if k not in ("type", "id")}
        cypher_props = ", ".join(f"{nm[k]}: {_esc(v)}" for k, v in sorted(props.items()))
        out.append(f"MERGE (n:{lbl} {{id: {_esc(ent['id'])}}}) SET n += {{{cypher_props}}};")

    # --- relationships ---
    for rel in sorted(data["relationships"], key=lambda r: (r["name"], r["source_id"], r["target_id"])):
        rtype = rel_types[rel["name"]]  # KeyError -> unknown relation (used by bad fixture)
        s_lbl = labels.get(rel["source_type"], [rel["source_type"]])[-1]
        t_lbl = labels.get(rel["target_type"], [rel["target_type"]])[-1]
        out.append(
            f"MATCH (a:{s_lbl} {{id: {_esc(rel['source_id'])}}}) "
            f"MATCH (b:{t_lbl} {{id: {_esc(rel['target_id'])}}}) "
            f"MERGE (a)-[:{rtype}]->(b);"
        )
    return "\n".join(out) + "\n"