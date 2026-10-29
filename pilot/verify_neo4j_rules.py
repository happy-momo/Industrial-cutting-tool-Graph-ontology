"""Run the online relationship rules against the loaded Neo4j graph.

Exit code: 0 if all rules pass; 1 if any violation is found (for CI/audit use).
"""
from __future__ import annotations
import sys

from neo4j import GraphDatabase

from pilot.neo4j_rules import run_rules, all_pass

URI = "bolt://localhost:7689"
AUTH = ("neo4j", "pilotsecret")


def main(argv: list[str] | None = None) -> int:
    _ = list(argv if argv is not None else sys.argv[1:])
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        results = run_rules(driver)
    ok = all_pass(results)
    for r in results:
        status = "PASS" if not r["violations"] else f"FAIL ({len(r['violations'])})"
        print(f"[{status}] {r['id']} {r['name']}  [shacl: {r['shacl_ref']}]")
        for v in r["violations"]:
            print(f"         violation: {v}")
    print("ALL_RULES_PASS" if ok else "RULE_VIOLATIONS")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())