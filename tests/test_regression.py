"""Regression tests for the cutting-tool ontology toolchain.

The lightweight group (jsonschema + application validator) runs with only the
core dependencies. The RDF/OWL/SHACL route requires rdflib/pyshacl and is
skipped when those are not installed.
"""
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------
# 1. Lightweight group: JSON Schema + application cross-field validation
# --------------------------------------------------------------------------
def _examples():
    ex = ROOT / "examples"
    return {
        p.stem: json.loads(p.read_text(encoding="utf-8"))
        for p in ex.glob("*.json")
        if p.name not in {"RecommendationRecord.json", "document-anchored-tool-identifiers.json"}
    }


def _schemas():
    from src.validator import SCHEMAS
    return SCHEMAS


def test_positive_examples_validate_against_generated_schemas():
    schemas = _schemas()
    for cls, instance in _examples().items():
        v = Draft202012Validator(schemas[f"{cls}.schema.json"])
        errors = sorted(e.message for e in v.iter_errors(instance))
        assert not errors, f"{cls} should be valid: {errors}"


def test_negative_cutting_param_rejected():
    from src.validator import validate_entity
    bad = json.loads((ROOT / "tests" / "bad-cutting-param.json").read_text(encoding="utf-8"))
    errors = validate_entity("CuttingParam", bad)
    assert errors, "bad cutting-param (min>max, wrong feed unit) must be rejected"


def test_cross_field_unit_consistency():
    """feed_type must agree with feed_unit (P2 rule)."""
    from src.validator import validate_entity
    assert validate_entity("CuttingParam", {"id": "x", "name": "n", "feed_type": "fn", "feed_unit": "mm/tooth"})
    assert not validate_entity("CuttingParam", {"id": "x", "name": "n", "feed_type": "fn", "feed_unit": "mm/rev"})
    assert validate_entity("CuttingParam", {"id": "x", "name": "n", "feed_type": "vf", "feed_unit": "mm/rev"})
    # unit present without feed_type is allowed (unit itself is validated separately)


# --------------------------------------------------------------------------
# 2. Cross-layer generation consistency (skipped when rdflib/pyshacl absent)
# --------------------------------------------------------------------------
def test_generate_is_consistent_and_owf_aligns():
    """Regeneration must be deterministic and match the checked OWL classes."""
    pytest.importorskip("rdflib")
    pytest.importorskip("pyshacl")
    from src.verify_consistency import test_all
    # test_all writes reports/verification.json and asserts internal consistency.
    test_all()


def test_generated_artifacts_cover_registered_classes():
    pytest.importorskip("rdflib")
    from src.generate_constraints import generate, load
    reg, _map = load()
    summary = generate()
    classes = set(reg["classes"])
    assert summary["json_schemas"] == len(classes)

    shapes_text = (ROOT / "shapes" / "generated-shapes.ttl").read_text(encoding="utf-8")
    for cls in classes:
        assert f"ct:{cls}Shape" in shapes_text, f"{cls}Shape missing in SHACL shapes"

    community = (ROOT / "neo4j" / "community-constraints.cypher").read_text(encoding="utf-8")
    for cls in classes:
        assert f"(n:{cls})" in community, f"{cls} missing Neo4j uniqueness constraint"


# --------------------------------------------------------------------------
# 3. RDF / OWL / SKOS / SHACL route (skipped when optional deps absent)
# --------------------------------------------------------------------------
class TestRdfRoute:
    def test_owl_and_example_parse(self):
        pytest.importorskip("rdflib")
        from rdflib import Graph
        Graph().parse(ROOT / "ontology" / "cutting-tool.owl", format="xml")
        Graph().parse(ROOT / "examples" / "example.ttl", format="turtle")

    def test_skos_vocabularies_parse(self):
        pytest.importorskip("rdflib")
        import scripts.validate_skos as vs
        assert vs.main() == 0

    def test_shacl_relation_rule_enforces_evidence(self):
        pytest.importorskip("rdflib")
        pytest.importorskip("pyshacl")
        from rdflib import Graph, Literal, Namespace
        from rdflib.namespace import RDF
        from pyshacl import validate

        from src.namespaces import ON
        CT = ON
        shapes = Graph().parse(ROOT / "shapes" / "generated-shapes.ttl", format="turtle")
        ont = Graph().parse(ROOT / "ontology" / "cutting-tool.owl", format="xml")
        relation_shapes = Graph().parse(ROOT / "shapes" / "relation-shapes.ttl", format="turtle")
        combined = shapes + relation_shapes

        data = Graph()
        t = CT["rec-test"]
        data.add((t, RDF.type, CT.CuttingRecommendation))
        data.add((t, CT["id"], Literal("REC-X")))
        data.add((t, CT["name"], Literal("演示推荐")))
        data.add((t, CT["scopeType"], Literal("tool")))
        data.add((t, CT["status"], Literal("draft")))
        # no supportedBy -> must violate the evidence-traceability rule (P2)
        ok, report, _ = validate(data, shacl_graph=combined, ont_graph=ont, inference="rdfs")
        assert not ok, "recommendation without supportedBy must fail relation rule"