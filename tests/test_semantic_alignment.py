"""Semantic-alignment regression tests.

These assert that the controlled SKOS vocabularies are the enforceable value-space
for the closed-world classes (ToolType / ProcessMethod / MaterialClass): the
resolve_skos layer maps manufacturer synonyms to canonical concept URIs, and the
application validator rejects any concept_ref that falls outside the bound scheme.

The resolve/validate cases require rdflib; the generated-schema assertions run on
pure jsonschema alone.
"""
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]

from src.namespaces import ON, VOCAB_BASE

VOCAB_T = VOCAB_BASE + "tool#"
VOCAB_P = VOCAB_BASE + "process#"
VOCAB_M = VOCAB_BASE + "material#"


# --------------------------------------------------------------------------
# Vocabulary resolution (needs rdflib)
# --------------------------------------------------------------------------
def test_resolve_skos_loads_taxonomy():
    pytest.importorskip("rdflib")
    from src import resolve_skos
    assert "tool" in resolve_skos.schemes()
    assert {"prefLabels", "altLabels", "contains"} <= set(resolve_skos.load_taxonomy()[VOCAB_T + "solid-milling"])


def test_resolve_canonical_preflabel():
    pytest.importorskip("rdflib")
    from src import resolve_skos
    assert resolve_skos.resolve("整体铣刀", "tool") == [VOCAB_T + "solid-milling"]


def test_resolve_manufacturer_alias_scopes_to_canonical():
    """Sandvik's '整体硬质合金铣刀' normalises to the canonical solid-milling concept
    when scoped to the tool vocabulary (the ambiguity resolver is scheme-aware)."""
    pytest.importorskip("rdflib")
    from src import resolve_skos
    assert resolve_skos.resolve("整体硬质合金铣刀", "tool") == [VOCAB_T + "solid-milling"]


def test_resolve_iso_turning_alias():
    """Seco's 'ISO车削' maps to the canonical turning concept."""
    pytest.importorskip("rdflib")
    from src import resolve_skos
    assert resolve_skos.resolve("ISO车削", "process") == [VOCAB_P + "turning"]


def test_resolve_returns_ambiguity_not_guess():
    """'钻削' names both hole-making and milling; auto-normalisation must surface
    both rather than silently pick one."""
    pytest.importorskip("rdflib")
    from src import resolve_skos
    hits = resolve_skos.resolve("钻削", "process")
    assert {VOCAB_P + "milling", VOCAB_P + "hole-making"} <= set(hits)


def test_scheme_membership_boundary():
    pytest.importorskip("rdflib")
    from src import resolve_skos
    assert resolve_skos.concept_in_scheme(VOCAB_T + "solid-milling", "tool")
    assert not resolve_skos.concept_in_scheme(VOCAB_T + "solid-milling", "process")


def test_advisory_ambiguity_surface_reported():
    """Known cross-branch duplicate (material '硬质合金') must appear on the
    human-review surface."""
    pytest.importorskip("rdflib")
    from src import resolve_skos
    assert "硬质合金" in resolve_skos.ambiguous_terms()


# --------------------------------------------------------------------------
# Application validator enforcement (needs rdflib + jsonschema)
# --------------------------------------------------------------------------
def test_validator_rejects_dangling_concept_ref():
    pytest.importorskip("rdflib")
    from src.validator import validate_entity
    errs = validate_entity("ToolType", {
        "id": "T-BAD", "name": "n", "concept_ref": VOCAB_T + "does-not-exist",
    })
    assert errs, "a concept_ref outside the vocabulary must be rejected"


def test_validator_rejects_cross_scheme_concept_ref():
    pytest.importorskip("rdflib")
    from src.validator import validate_entity
    errs = validate_entity("ToolType", {
        "id": "T-BAD", "name": "n", "concept_ref": VOCAB_P + "turning",
    })
    assert errs, "a process concept must not satisfy a ToolType concept_ref"


def test_validator_accepts_valid_concept_ref():
    pytest.importorskip("rdflib")
    from src.validator import validate_entity
    assert not validate_entity("ToolType", {
        "id": "T-OK", "name": "n", "concept_ref": VOCAB_T + "turning-insert",
    })
    assert not validate_entity("MaterialClass", {
        "id": "M-OK", "name": "n", "iso_code": "P", "concept_ref": VOCAB_M + "P",
    })


# --------------------------------------------------------------------------
# Generated schema carries the vocabulary binding (pure jsonschema)
# --------------------------------------------------------------------------
def test_generated_tool_type_schema_requires_concept_ref():
    schema = json.loads((ROOT / "schemas" / "ToolType.schema.json").read_text(encoding="utf-8"))
    assert "concept_ref" in schema["required"]
    assert "pattern" in schema["properties"]["concept_ref"]
    assert "tool" in schema["properties"]["concept_ref"]["pattern"]
    # required reference: instance without concept_ref fails schema validation
    v = Draft202012Validator(schema)
    assert not v.is_valid({"id": "T", "name": "n"})


def test_generated_material_class_schema_requires_concept_ref():
    schema = json.loads((ROOT / "schemas" / "MaterialClass.schema.json").read_text(encoding="utf-8"))
    assert "concept_ref" in schema["required"]
    v = Draft202012Validator(schema)
    assert not v.is_valid({"id": "M", "name": "n", "iso_code": "P"})
    assert v.is_valid({"id": "M", "name": "n", "iso_code": "P", "concept_ref": VOCAB_M + "P"})