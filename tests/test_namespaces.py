"""Namespace single-source-of-truth: all artifacts share one base; swap is one place."""
from pathlib import Path

import rdflib
import yaml

from src import namespaces

ROOT = Path(__file__).resolve().parents[1]


def test_on_base_is_fragment_terminated():
    assert namespaces.ON_BASE.endswith("#")


def test_field_registry_namespace_matches():
    reg = yaml.safe_load((ROOT / "contract/field-registry.yaml").read_text("utf-8"))
    assert reg["namespace"] == namespaces.ON_BASE


def test_vocabulary_base_underscore_host():
    assert "vocabulary/" in namespaces.VOCAB_BASE
    assert namespaces.VOCAB_BASE.startswith("https://")


def test_generated_shapes_bind_same_ct():
    g = rdflib.Graph()
    g.parse(str(ROOT / "shapes/generated-shapes.ttl"), format="turtle")
    bound = {str(v) for _, v in g.namespaces()}
    assert namespaces.ON_BASE in bound