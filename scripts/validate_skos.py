"""Validate that every SKOS controlled-vocabulary file is well-formed Turtle and
that each concept carries at least a prefLabel and belongs to a scheme.

Run: python -m scripts.validate_skos
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from rdflib import Graph, Namespace, RDF
from rdflib.namespace import SKOS

ROOT = Path(__file__).resolve().parents[1]
VOCAB = ROOT / "vocabulary"


def _collect_concept_refs() -> list[str]:
    """Every conceptRef referenced across examples/*.json and examples/example.ttl.

    These are the payload anchors that must resolve to a real SKOS concept; a
    dangling reference means the closed-world instance points outside the value-space.
    """
    refs: list[str] = []
    from src.namespaces import ON as ct
    examples = ROOT / "examples"
    ttl = examples / "example.ttl"
    if ttl.exists():
        g = Graph()
        g.parse(ttl, format="turtle")
        refs.extend(str(o) for o in g.objects(None, ct.conceptRef))
    for path in sorted(examples.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))

        def walk(node):
            if isinstance(node, dict):
                v = node.get("concept_ref")
                if isinstance(v, str):
                    refs.append(v)
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(data)
    return refs


def main() -> int:
    errors: list[str] = []
    checked = 0
    for path in sorted(VOCAB.glob("*.ttl")):
        g = Graph()
        try:
            g.parse(path, format="turtle")
        except Exception as exc:  # rdflib raises a variety of parse errors
            errors.append(f"{path.name}: parse failed: {exc}")
            continue
        for concept in g.subjects(RDF.type, SKOS.Concept):
            checked += 1
            if (concept, SKOS.prefLabel, None) not in g:
                errors.append(f"{path.name}: concept {concept} missing skos:prefLabel")
            if (concept, SKOS.inScheme, None) not in g:
                errors.append(f"{path.name}: concept {concept} missing skos:inScheme")

    # concept_ref used in examples must resolve to a real concept (hard failure:
    # a bounded class pointing outside its vocabulary is a broken reference).
    from src import resolve_skos  # local: resolver loads vocab graphs lazily
    for ref in _collect_concept_refs():
        if not resolve_skos.concept_exists(ref):
            errors.append(f"unresolved concept_ref: {ref}")

    # Advisory (non-fatal): labels that normalise to more than one concept mark
    # where scheme-scoping or a human tie-break is required (e.g. material's
    # two distinct "硬质合金" branches). Listing, not failing, keeps the valid
    # multi-branch taxonomy intact while documenting the review surface.
    for term in resolve_skos.ambiguous_terms():
        print(f"(advisory) ambiguous normalization term '{term}' -> "
              f"{resolve_skos.resolve(term)}")

    if errors:
        print("\n".join(errors))
        print(f"FAIL: {len(errors)} issue(s), {checked} concepts checked")
        return 1
    print(f"PASS: {checked} SKOS concepts in {len(list(VOCAB.glob('*.ttl')))} files are well-formed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())