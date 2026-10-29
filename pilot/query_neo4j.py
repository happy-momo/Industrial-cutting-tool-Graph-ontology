"""Representative queries against the loaded toy graph. Ends non-zero if any fails."""
from __future__ import annotations

from neo4j import GraphDatabase

URI = "bolt://localhost:7689"
AUTH = ("neo4j", "pilotsecret")


def query(driver, cypher: str, **params):
    with driver.session() as s:
        return list(s.run(cypher, **params))


def main() -> int:
    checks = []
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        # Q1 series-of-tools (catalog traversal, tool under a product series)
        r1 = query(driver, "MATCH (t:Tool)-[:IN_SERIES]->(s:ProductSeries {id:$sid}) RETURN t.id",
                   sid="S-CNT")
        checks.append(("series tools", r1, len(r1) >= 1))
        # Q2 grade-to-material applicability
        r2 = query(driver, "MATCH (g:ToolGrade)-[:SUITABLE_FOR]->(m:MaterialClass {id:$mid}) RETURN g.id",
                   mid="MC-P")
        checks.append(("grade->material suitability", r2, len(r2) >= 1))
        # Q3 evidence-backed recommendation (traceability chain)
        r3 = query(driver, """MATCH (r:CuttingRecommendation)-[:FOR_GRADE]->(g:ToolGrade)
                              MATCH (r)-[:SUPPORTED_BY]->(e:SourceEvidence)-[:FROM_DOCUMENT]->(d:SourceDocument)
                              RETURN r.id, g.id, d.documentName""")
        checks.append(("evidence-backed recommendation", r3, len(r3) >= 1))

    ok = all(ok for _, _, ok in checks)
    for name, rows, passed in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}: {rows}")
    print("ALL_QUERIES_PASS" if ok else "QUERY_FAILURE")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())