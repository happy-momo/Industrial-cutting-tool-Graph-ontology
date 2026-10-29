# End-to-End Pilot `/pilot`

A small-batch proof that this architecture carries a real
"*standardize → validate → project → load Neo4j → query*" pipeline, reusing the
existing authority layers (OWL semantics / SKOS value-space / `field-registry`
validation contract / `ontology-neo4j.yaml` projection mapping). The module is
**additive and non-invasive** — it does not touch `src/`.

## Observed results (29 Oct 2026)

| Step | Outcome |
| --- | --- |
| `tests/test_pilot_catalog.py` | 2 passed — positive subgraph valid; negative fixture's 3 error classes rejected (dangling ref, cross-scheme ref, absent relation id) |
| `tests/test_pilot_project.py` | 2 passed — deterministic Cypher; relation types from mapping; unknown relation raises |
| Load into Neo4j 5-community (Docker, bolt://localhost:7689) | `LOADED: 12 nodes, 13 relationships`; idempotent re-load stays 12/13 |
| Representative queries | `ALL_QUERIES_PASS` (3/3): series-of-tools traversal, grade→material suitability, evidence-backed recommendation chain |

## Usage

```bash
pip install pyshacl            # if not already present (baseline regression)

# 1. Validate + project (offline, no DB needed)
python -m pytest tests/test_pilot_catalog.py tests/test_pilot_project.py -q

# 2. Start local Neo4j (uses host ports 7475/7689; 7474/7687 are reserved by
#    another project's Neo4j on this machine)
bash pilot/run_neo4j.sh

# 3. Load + query
python -m pilot.load_neo4j         # also runs the online relationship-invariant check
python -m pilot.query_neo4j        # representative queries (expect ALL_QUERIES_PASS)

# 4. Verify the online relationship rules (offline SHACL invariants on the graph)
python -m pilot.verify_neo4j_rules # expect ALL_RULES_PASS; non-zero exit on violations
```

## Files

- `toy-catalog.json` — positive self-contained subgraph (manufacturer → series →
  insert → type/method/grade → material → param → recommendation → evidence → document)
- `toy-catalog-bad.json` — negative fixtures: cross-scheme `concept_ref`, dangling
  `concept_ref`, relation referencing an absent id
- `validate_catalog.py` — entity checks via `src.validator.validate_entity`
  (+ `concept_ref` semantics) plus relationship definition / id-integrity checks
- `project_to_cypher.py` — deterministic Cypher (id constraints + node MERGE +
  relationship MATCH/MERGE), aligned to `ontology-neo4j.yaml`
- `run_neo4j.sh`, `load_neo4j.py`, `query_neo4j.py` — Docker + driver load/query
- `neo4j_rules.py`, `verify_neo4j_rules.py` — online relationship invariants
  mirroring the four SHACL rules in `shapes/relation-shapes.ttl`, run against the
  loaded graph (`python -m pilot.verify_neo4j_rules`). Also run on `load_neo4j.py`.

## Online relationship rules

The four relationship-level SHACL rules are mirrored as violation-detecting Cypher
queries that run against the loaded graph. Because Neo4j Community Cypher cannot
declare "this relationship must exist" as a constraint, the invariants are enforced
as checks (recorded, not rejecting); `verify_neo4j_rules.py` exits non-zero on any
violation for CI/audit use. Verified: clean 12/13 subgraph passes all 4; injected
violations (a recommendation without evidence, a mismatched feed unit) are detected
and cleanup restores a clean pass.

## Pilot data is not production data

All values are development fixtures for validating the toolchain; they carry no
product-geometry, performance, fit, or machining-safety meaning.