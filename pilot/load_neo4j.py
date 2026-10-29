"""Load the toy catalog into a running Neo4j (Docker) via the neo4j driver."""
from __future__ import annotations

import json
from pathlib import Path

from neo4j import GraphDatabase

from pilot.project_to_cypher import project_to_cypher
from pilot.validate_catalog import load_mapping, validate_catalog

ROOT = Path(__file__).resolve().parents[1]
URI = "bolt://localhost:7689"
AUTH = ("neo4j", "pilotsecret")


def main(data_path: str = str(ROOT / "pilot/toy-catalog.json")) -> int:
    data = json.loads(Path(data_path).read_text(encoding="utf-8"))
    reg, mapping = load_mapping()
    ok, errors = validate_catalog(data)
    if not ok:
        print("\n".join(errors))
        return 1
    cypher = project_to_cypher(data, reg, mapping)
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        with driver.session() as s:
            for stmt in [l for l in cypher.splitlines() if l.strip() and not l.startswith("//")]:
                s.run(stmt)  # idempotent MERGE / CREATE CONSTRAINT IF NOT EXISTS
            nodes = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            rels = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
            print(f"LOADED: {nodes} nodes, {rels} relationships")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())